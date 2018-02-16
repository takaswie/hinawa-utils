from re import match
from struct import unpack

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

__all__ = ['BebobUnit']

class BebobUnit(Hinawa.SndUnit):
    REG_INFO = 0xffffc8020000

    def __init__(self, path):
        if match('/dev/snd/hwC[0-9]*D0', path):
            super().__init__()
            self.open(path)
            if self.get_property('type') != 3:
                raise ValueError('The character device is not for BeBoB unit')
            self._on_juju = False,
            self.listen()
        elif match('/dev/fw[0-9]*', path):
            # Just using parent class.
            super(Hinawa.FwUnit, self).__init__()
            Hinawa.FwUnit.open(self, path)
            Hinawa.FwUnit.listen(self)
            self._on_juju = True
        else:
            raise ValueError('Invalid argument for character device')
        self.fcp = Hinawa.FwFcp()
        self.fcp.listen(self)
        self.firmware_info = self._get_firmware_info()

    def _get_firmware_info(self):
        def _get_string_literal(params):
            if 0x00 in params:
                return '00000000'
            return params.decode('US-ASCII')
        def _get_time_literal(params):
            if 0x00 in params:
                return '000000'
            return params.decode('US-ASCII')

        req = Hinawa.FwReq()
        params = req.read(self, BebobUnit.REG_INFO, 104)

        info = {}
        info['manufacturer']        = _get_string_literal(params[0:8])
        info['protocol-version']    = unpack('<I', params[8:12])[0]
        info['guid']                = (unpack('<Q', params[12:20])[0] << 32) | \
                                      unpack('<I', params[20:24])[0]
        info['model-id']            = unpack('<I', params[24:28])[0]
        info['model-revision']      = unpack('<I', params[28:32])[0]
        info['software'] = {
            'build-date':   _get_string_literal(params[32:40]),
            'build-time':   _get_time_literal(params[40:46]),
            'id':           unpack('<I', params[48:52])[0],
            'version':      unpack('<I', params[52:56])[0],
            'base-address': unpack('<I', params[56:60])[0],
            'max-size':     unpack('<I', params[60:64])[0],
        }
        info['bootloader'] = {
            'build-date':   _get_string_literal(params[64:72]),
            'build-time':   _get_time_literal(params[72:80]),
        }
        info['debugger'] = {
            'build-date':   _get_string_literal(params[80:88]),
            'build-time':   _get_string_literal(params[88:96]),
            'id':           unpack('<I', params[96:100])[0],
            'version':      unpack('<I', params[100:104])[0],
        }

        return info
