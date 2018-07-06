from re import match
from struct import unpack

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

__all__ = ['TscmUnit']

class TscmUnit(Hinawa.SndUnit):
    _BASE_ADDR = 0xffff00000000

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

    def read_quadlet(self, offset):
        req = Hinawa.FwReq()
        return req.read(self, self._BASE_ADDR + offset, 4)

    def write_quadlet(self, offset, frames):
        req = Hinawa.FwReq()
        return req.write(self, self._BASE_ADDR + offset, frames)

    def get_firmware_versions(self):
        info = {}
        frames = self.read_quadlet(0x0000)
        info['Register'] = unpack('>I', frames)[0]
        frames = self.read_quadlet(0x0004)
        info['FPGA'] = unpack('>I', frames)[0]
        frames = self.read_quadlet(0x0008)
        info['ARM'] = unpack('>I', frames)[0]
        frames = self.read_quadlet(0x000c)
        info['HW'] = unpack('>I', frames)[0]
        return info

    def set_clock_source(self, src):
        if src not in self.supported_clock_sources:
            raise ValueError('Invalid argument for clock source: {0}'.format(src))
        src = self.supported_clock_sources.index(src) + 1
        frames = self.read_quadlet(0x0228)
        frames = bytearray(frames)
        frames[0] = 0
        frames[1] = 0
        frames[3] = src
        self.write_quadlet(0x0228, frames)
    def get_clock_source(self):
        frames = self.read_quadlet(0x0228)
        index = frames[3] - 1
        if index < 0 or index >= len(self.supported_clock_sources):
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
        frames = self.read_quadlet(0x0228)
        frames = bytearray(frames)
        frames[3] = flag
        self.write_quadlet(0x0228, frames)
    def get_sampling_rate(self):
        frames = self.read_quadlet(0x0228)
        if (frames[1] & 0x0f) == 0x01:
            rate = 44100
        elif (frames[1] & 0x0f) == 0x02:
            rate = 48000
        else:
            raise OSError('Unexpected value for sampling rate.')
        if (frames[1] & 0xf0) == 0x80:
            rate *= 2
        elif (frames[1] & 0xf0) != 0x00:
            raise OSError('Unexpected value for sampling rate.')
        return rate

    def set_master_fader(self, mode):
        frames = bytearray(4)
        if mode:
            frames[2] = 0x40
        else:
            frames[1] = 0x40
        self.write_quadlet(0x022c, frames)
    def get_master_fader(self):
        frames = self.read_quadlet(0x022c)
        return bool(frames[3] & 0x40)

    def set_coaxial_source(self, source):
        frames = bytearray(4)
        if source not in self.supported_coax_sources:
            raise ValueError('Invalid argument for coaxial source.')
        if self.supported_coax_sources.index(source) == 0:
            frames[1] = 0x02
        else:
            frames[2] = 0x02
        self.write_quadlet(0x022c, frames)
    def get_coaxial_source(self):
        frames = self.read_quadlet(0x022c)
        index = frames[3] & 0x02 > 0
        return self.supported_coax_sources[index]

    def bright_led(self, position, state):
        if state not in self.supported_led_status:
            raise ValueError('Invalid argument for LED state.')
        frames = bytearray(4)
        frames[3] = position
        if self.supported_led_status.index(state) == 1:
            frames[1] = 0x01
        self.write_quadlet(0x0404, frames)
