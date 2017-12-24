import gi
gi.require_version('Hinawa', '1.0')
from gi.repository import Hinawa

import re
from array import array

__all__ = ['TscmUnit']

class TscmUnit(Hinawa.SndUnit):
    supported_sampling_rates = (44100, 48000, 88200, 96000)
    supported_clock_sources = ('Internal', 'Word-clock', 'S/PDIF', 'ADAT')
    supported_coax_sources = ('S/PDIF-1/2', 'Analog-1/2')
    supported_led_status = ('off', 'on')

    def __init__(self, path):
        if re.match('/dev/snd/hwC[0-9]*D0', path):
            super().__init__()
            self.open(path)
            if self.get_property('type') != 6:
                raise ValueError('The character device is not for Tascam unit')
            self.listen()
        elif re.match('/dev/fw[0-9]*', path):
            # Just using parent class.
            super(Hinawa.FwUnit, self).__init__()
            Hinawa.FwUnit.open(self, path)
            Hinawa.FwUnit.listen(self)
        else:
            raise ValueError('Invalid argument for character device')

    def _get_array(self):
        # The width with 'L' parameter is depending on environment.
        arr = array('L')
        if arr.itemsize is not 4:
            arr = array('I')
            if arr.itemsize is not 4:
                raise RuntimeError('Platform has no representation \
                                    equivalent to quadlet.')
        return arr

    def _read_transaction(self, addr, quads):
        req = Hinawa.FwReq()
        return req.read(self, addr, quads)

    def _write_transaction(self, addr, data):
        req = Hinawa.FwReq()
        return req.write(self, addr, data)

    def get_firmware_versions(self):
        info = {}
        data = self._read_transaction(0xffff00000000, 1)
        info['Register'] = data[0]
        data = self._read_transaction(0xffff00000004, 1)
        info['FPGA'] = data[0]
        data = self._read_transaction(0xffff00000008, 1)
        info['ARM'] = data[0]
        data = self._read_transaction(0xffff0000000c, 1)
        info['HW'] = data[0]
        return info

    def set_clock_source(self, source):
        if source not in self.supported_clock_sources:
            raise ValueError('Invalid argument for clock source.')
        src = self.supported_clock_sources.index(source) + 1
        data = self._read_transaction(0xffff00000228, 1)
        data[0] = (data[0] & 0x0000ff00) | src
        self._write_transaction(0xffff00000228, data)
    def get_clock_source(self):
        data = self._read_transaction(0xffff00000228, 1)
        index = ((data[0] & 0x00ff0000) >> 16) - 1
        if index >= len(self.supported_clock_sources):
            raise OSError('Unexpected value for clock source.')
        return self.supported_clock_sources[index]

    def set_sampling_rate(self, rate):
        if rate not in self.supported_sampling_rates:
            raise ValueError('Invalid argument for sampling rate.')
        if rate == 44100:
            flag = 0x01
        elif rate == 48000:
            flag = 0x02
        elif rate == 88200:
            flag = 0x81
        elif rate == 96000:
            flag = 0x82
        data = self._read_transaction(0xffff00000228, 1)
        data[0] = (data[0] & 0x000000ff) | (flag << 8)
        self._write_transaction(0xffff00000228, data)
    def get_sampling_rate(self):
        data = self._read_transaction(0xffff00000228, 1)
        value = (data[0] & 0xff000000) >> 24
        if (value & 0x0f) == 0x01:
            rate = 44100
        elif (value & 0x0f) == 0x02:
            rate = 48000
        else:
            raise OSError('Unexpected value for sampling rate.')
        if (value & 0xf0) == 0x80:
            rate *= 2
        elif (value & 0xf0) != 0x00:
            print(value)
            raise OSError('Unexpected value for sampling rate.')
        return rate

    def set_master_fader(self, mode):
        data = self._get_array()
        if mode > 0:
            data.append(0x00004000)
        else:
            data.append(0x00400000)
        self._write_transaction(0xffff0000022c, data)
    def get_master_fader(self):
        data = self._read_transaction(0xffff0000022c, 1)
        if data[0] & 0x00000040:
            return True
        else:
            return False

    def set_coaxial_source(self, source):
        data = self._get_array()
        if source not in self.supported_coax_sources:
            raise ValueError('Invalid argument for coaxial source.')
        if self.supported_coax_sources.index(source) == 0:
            data.append(0x00020000)
        else:
            data.append(0x00000200)
        self._write_transaction(0xffff0000022c, data)
    def get_coaxial_source(self):
        data = self._read_transaction(0xffff0000022c, 1)
        index = data[0] & 0x00000002 > 0
        return self.supported_coax_sources[index]

    def bright_led(self, position, state):
        if state not in self.supported_led_status:
            raise ValueError('Invalid argument for LED state.')
        data = self._get_array()
        if self.supported_led_status.index(state) == 0:
            data.append(position)
        else:
            data.append(0x00010000 | position)
        self._write_transaction(0xffff00000404, data)
