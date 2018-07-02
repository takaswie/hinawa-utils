from re import match
from struct import unpack

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

__all__ = ['TscmUnit']

class TscmUnit(Hinawa.SndUnit):
    supported_sampling_rates = (44100, 48000, 88200, 96000)
    supported_clock_sources = ('Internal', 'Word-clock', 'S/PDIF', 'ADAT')
    supported_coax_sources = ('S/PDIF-1/2', 'Analog-1/2')
    supported_led_status = ('off', 'on')

    def __init__(self, path):
        if match('/dev/snd/hwC[0-9]*D0', path):
            super().__init__()
            self.open(path)
            if self.get_property('type') != 6:
                raise ValueError('The character device is not for Tascam unit')
            self.listen()
        elif match('/dev/fw[0-9]*', path):
            # Just using parent class.
            super(Hinawa.FwUnit, self).__init__()
            Hinawa.FwUnit.open(self, path)
            Hinawa.FwUnit.listen(self)
        else:
            raise ValueError('Invalid argument for character device')

    def get_firmware_versions(self):
        info = {}
        req = Hinawa.FwReq()
        data = req.read(self, 0xffff00000000, 4)
        info['Register'] = unpack('>I', data)[0]
        data = req.read(self, 0xffff00000004, 4)
        info['FPGA'] = unpack('>I', data)[0]
        data = req.read(self, 0xffff00000008, 4)
        info['ARM'] = unpack('>I', data)[0]
        data = req.read(self, 0xffff0000000c, 4)
        info['HW'] = unpack('>I', data)[0]
        return info

    def set_clock_source(self, source):
        if source not in self.supported_clock_sources:
            raise ValueError('Invalid argument for clock source.')
        src = self.supported_clock_sources.index(source) + 1
        req = Hinawa.FwReq()
        data = req.read(self, 0xffff00000228, 4)
        data = bytearray(data)
        data[0] = 0
        data[1] = 0
        data[3] = src
        req.write(self, 0xffff00000228, data)
    def get_clock_source(self):
        req = Hinawa.FwReq()
        data = req.read(self, 0xffff00000228, 4)
        index = data[1] - 1
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
        req = Hinawa.FwReq()
        data = req.read(self, 0xffff00000228, 4)
        data = bytearray(data)
        data[3] = flag
        req.write(self, 0xffff00000228, data)
    def get_sampling_rate(self):
        req = Hinawa.FwReq()
        data = req.read(self, 0xffff00000228, 4)
        if (data[1] & 0x0f) == 0x01:
            rate = 44100
        elif (data[1] & 0x0f) == 0x02:
            rate = 48000
        else:
            raise OSError('Unexpected value for sampling rate.')
        if (data[1] & 0xf0) == 0x80:
            rate *= 2
        elif (data[1] & 0xf0) != 0x00:
            raise OSError('Unexpected value for sampling rate.')
        return rate

    def set_master_fader(self, mode):
        data = bytearray(4)
        if mode:
            data[2] = 0x40
        else:
            data[1] = 0x40
        req = Hinawa.FwReq()
        req.write(self, 0xffff0000022c, data)
    def get_master_fader(self):
        req = Hinawa.FwReq()
        data = req.read(self, 0xffff0000022c, 4)
        return bool(data[3] & 0x40)

    def set_coaxial_source(self, source):
        data = bytearray(4)
        if source not in self.supported_coax_sources:
            raise ValueError('Invalid argument for coaxial source.')
        if self.supported_coax_sources.index(source) == 0:
            data[1] = 0x02
        else:
            data[2] = 0x02
        req = Hinawa.FwReq()
        req.write(self, 0xffff0000022c, data)
    def get_coaxial_source(self):
        req = Hinawa.FwReq()
        data = req.read(self, 0xffff0000022c, 4)
        index = data[3] & 0x02 > 0
        return self.supported_coax_sources[index]

    def bright_led(self, position, state):
        if state not in self.supported_led_status:
            raise ValueError('Invalid argument for LED state.')
        data = bytearray(4)
        data[3] = position
        if self.supported_led_status.index(state) == 1:
            data[1] = 0x01
        req = Hinawa.FwReq()
        req.write(self, 0xffff00000404, data)
