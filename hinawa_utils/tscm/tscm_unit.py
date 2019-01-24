# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from re import match
from struct import pack, unpack
from math import log10, pow

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from hinawa_utils.tscm.config_rom_parser import TscmConfigRomParser

__all__ = ['TscmUnit']


class TscmUnit(Hinawa.SndUnit):
    _BASE_ADDR = 0xffff00000000

    supported_sampling_rates = (44100, 48000, 88200, 96000)
    supported_clock_sources = ('Internal', 'Word-clock', 'S/PDIF', 'ADAT')
    supported_coax_sources = ('S/PDIF-1/2', 'Analog-1/2')
    supported_led_status = ('off', 'on')

    __SPECS = {
        'FW-1082': {
            'stream-in-ana-chs':    2,
            'has-opt-iface':        False,
        },
        'FW-1804': {
            'stream-in-ana-chs':    2,
            'has-opt-iface':        True,
        },
        'FW-1884': {
            'stream-in-ana-chs':    8,
            'has-opt-iface':        True,
        },
    }

    __MAX_THRESHOLD = 0x7fff

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

        parser = TscmConfigRomParser()
        info = parser.parse_rom(self.get_config_rom())
        self.model_name = info['model-name']
        self.__specs = self.__SPECS[self.model_name]

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
            raise ValueError(
                'Invalid argument for clock source: {0}'.format(src))
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

    def __set_flag(self, flag, mask):
        data = self.read_quadlet(0x022c)
        flags = data[3]
        data = bytearray(4)
        data[1] = (flags & ~flag) & mask    # removed bits.
        data[2] = (~flags & flag) & mask    # added bits.
        self.write_quadlet(0x022c, data)

    def get_stream_spdif_in_src_labels(self):
        labels = []
        labels.append('coax-iface')
        labels.append('opt-iface')
        return labels

    def set_stream_spdif_in_src(self, src):
        labels = self.get_stream_spdif_in_src_labels()
        if src not in labels:
            raise ValueError('Invalid argumen for source of stream spdif in.')
        flag = labels.index(src)
        self.__set_flag(flag, 0x01)

    def get_stream_spdif_in_src(self):
        labels = self.get_stream_spdif_in_src_labels()
        data = self.read_quadlet(0x022c)
        index = data[3] & 0x01
        return labels[index]

    def get_coax_out_src_labels(self):
        labels = []
        ana_ch = self.__specs['stream-in-ana-chs']
        labels.append('stream-in-{0}/{1}'.format(ana_ch + 1, ana_ch + 2))
        labels.append('analog-out-1/2')
        return labels

    def set_coax_out_src(self, src):
        labels = self.get_coax_out_src_labels()
        if src not in labels:
            raise ValueError('Invalid argument for source of coax out iface.')
        flag = labels.index(src) << 1
        self.__set_flag(flag, 0x02)

    def get_coax_out_src(self):
        labels = self.get_coax_out_src_labels()
        data = self.read_quadlet(0x022c)
        index = (data[3] & 0x02) >> 1
        return labels[index]

    def get_opt_out_src_labels(self):
        labels = []
        if self.__specs['has-opt-iface']:
            ana_ch = self.__specs['stream-in-ana-chs']

            label = 'stream-in-{0}:{1}'.format(ana_ch + 1, ana_ch + 9)
            labels.append(label)

            label = 'stream-in-{0}/{1}'.format(ana_ch + 10, ana_ch + 11)
            labels.append(label)

            labels.append('analog-in-1:8')
            if ana_ch > 2:
                labels.append('analog-out-1:8')

        return labels

    def set_opt_out_src(self, src):
        labels = self.get_opt_out_src_labels()
        if src not in labels:
            print('Invalid argument for source of opt out iface.')
        flag = labels.index(src) << 2
        if flag == 0x0c:
            flag = 0x88
        self.__set_flag(flag, 0x8c)

    def get_opt_out_src(self):
        labels = self.get_opt_out_src_labels()
        data = self.read_quadlet(0x022c)
        index = (data[3] & 0x0c) >> 2
        if data[3] & 0x80:
            index += 1
        print(index)
        return labels[index]

    def set_input_threshold(self, level):
        data = self.read_quadlet(0x0230)
        data = bytearray(data)
        if level == float('-inf'):
            val = 0x0000
        else:
            val = int(self.__MAX_THRESHOLD * pow(10, level / 20))
        chunks = pack('>H', val)
        data[0] = chunks[0]
        data[1] = chunks[1]
        self.write_quadlet(0x0230, data)

    def get_input_threshold(self):
        data = self.read_quadlet(0x0230)
        val = unpack('>H', data[0:2])[0]
        if val == 0x0000:
            return float('-inf')
        return 20 * log10(val / self.__MAX_THRESHOLD)
