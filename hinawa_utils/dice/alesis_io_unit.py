# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from struct import pack, unpack
from math import log10, pow

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from hinawa_utils.dice.dice_unit import DiceUnit

__all__ = ['AlesisIoUnit']

class AlesisIoUnit(DiceUnit):
    __OUI_ALESIS = 0x000595

    __SPECS = {
        'iO|14': {
            'analog-in': 4,
            'has_adat_b': False,
        },
        'iO|26': {
            'analog-in': 8,
            'has_adat_b': True,
        },
    }

    __BASE_OFFSET = 0x00200000

    '''
    Map of offset for mixer sources.
              Mixer-1 Mixer-2 Mixer-3 Mixer-4 Mixer-5 Mixer-6 Mixer-7 Mixer-8
    Analog-1:    0038    00b8    0138    01b8    0238    02b8    0338    03b8
    ...
    Analog-8:    0054    00d4    0154    01d4    0254    02d4    0354    03b4
    Stream-1:    0058    00d8    0158    01d8    0258    02d8    0358    03b8
    ...
    Stream-8:    0074    00f4    0174    01f4    0274    02f4    0374    03f4
    ADAT-A-1:    0078    00f8    0178    01f8    0278    02f8    0378    03f8
    ...
    ADAT-A-8:    0094    0114    0194    0214    0294    0314    0394    0414
    ADAT-B-1:    0098    0118    0198    0218    0298    0318    0398    0418
    ...
    ADAT-B-8:    00b4    0134    01b4    0234    02b4    0334    03b4    0434

    Map of offset for mixer outputs.
    Mixer-1:    0438
    ...
    Mixer-8:    043c
    '''

    __MIXER_SRC_MUTE_OFFSETS = {
        'Mixer-1/2': 0x0458,
        'Mixer-3/4': 0x045c,
        'Mixer-5/6': 0x0460,
        'Mixer-7/8': 0x0464,
    }
    __MIXER_OUT_MUTE_OFFSETS = 0x0468
    __MIXER_SRC_LINK_OFFSET = {
        'Mixer-1/2': 0x047c,
        'Mixer-3/4': 0x0450,
        'Mixer-5/6': 0x0454,
        'Mixer-7/8': 0x0458,
    }
    __METER_OFFSET = 0x4c0
    __MIXER_OUT_LEVEL_OFFSET = 0x0564
    __MIXER_23_24_SWITCH = 0x0568
    __SPDIF_OUT_SRC_OFFSET = 0x056c
    __HP34_OUT_SRC_OFFSET = 0x0570
    __MIX_BLEND_OFFSET = 0x0574     # 0x0000 - 0x0100
    __MAIN_LEVEL_OFFSET = 0x0578    # 0x0000 - 0x0100

    __MAX_COEFF = 0x007fffff

    __MIXER_SRC_LABELS = (
        'Analog-1/2',
        'Analog-3/4',
        'Analog-5/6',
        'Analog-7/8',
        'Stream-1/2',
        'Stream-3/4',
        'Stream-5/6',
        'Stream-7/8',
        'ADAT-A-1/2',
        'ADAT-A-3/4',
        'ADAT-A-5/6',
        'ADAT-A-7/8',
        'ADAT-B-1/2',
        'ADAT-B-3/4',
        'ADAT-B-5/6',
        'ADAT-B-7/8',
    )

    __MIXER_LABELS = (
        'Mixer-1/2',
        'Mixer-3/4',
        'Mixer-5/6',
        'Mixer-7/8',
    )

    __LEVEL_LABELS = (
        '-10',
        '+4',
    )

    def __init__(self, fullpath):
        super().__init__(fullpath)

        if self.vendor_id != self.__OUI_ALESIS:
            raise ValueError('Unsupported model.')

        tx_params = self.get_tx_params()
        if tx_params[0]['pcm'] in (4, 6):
            self.name = 'iO|14'
        else:
            self.name = 'iO|26'
        self.__specs = self.__SPECS[self.name]

        # Ensure 23/24 ports of mixer source receive signal from S/PDIF-1/2 if
        # it has no optical interface for ADAT-B.
        if not self.__specs['has_adat_b']:
            data = bytearray(4)
            self.__write_data(self.__MIXER_23_24_SWITCH, data)

    def __write_data(self, offset, data):
        req = Hinawa.FwReq()
        offset += self.__BASE_OFFSET
        self._protocol.write_transactions(req, offset, data)

    def __read_data(self, offset, length):
        req = Hinawa.FwReq()
        offset += self.__BASE_OFFSET
        return self._protocol.read_transactions(req, offset, length)

    def get_mixer_labels(self):
        return self.__MIXER_LABELS

    def get_mixer_src_labels(self):
        labels = []
        for ch in range(1, self.__specs['analog-in'], 2):
            labels.append('Analog-{0}/{1}'.format(ch, ch + 1))
        # MEMO: Any source from stream input receives no influences from
        # out-volume/mute.
        #for ch in range(1, 8, 2):
        #    labels.append('Stream-{0}/{1}'.format(ch, ch + 1))
        if not self.__specs['has_adat_b']:
            for ch in range(1, 8, 2):
                labels.append('ADAT-{0}/{1}'.format(ch, ch + 1))
            labels.append('S/PDIF-1/2')
        else:
            for ch in range(1, 8, 2):
                labels.append('ADAT-A-{0}/{1}'.format(ch, ch + 1))
            for ch in range(1, 6, 2):
                labels.append('ADAT-B-{0}/{1}'.format(ch, ch + 1))
            data = self.__read_data(self.__MIXER_23_24_SWITCH, 4)
            val = unpack('>I', data)[0]
            if val > 0:
                labels.append('ADAT-B-7/8')
            else:
                labels.append('S/PDIF-1/2')
        return labels

    def __calculate_mixer_src_gain_offsets(self, dst, src, src_ch):
        if dst not in self.__MIXER_LABELS:
            raise ValueError('Invalid argument for mixer.')
        if src not in self.get_mixer_src_labels():
            raise ValueError('Invalid argument for input of mixer.')
        if src_ch not in (0, 1):
            raise ValueError('Invalid argument for channel of stereo pair.')

        # iO14 has one optical interface for ADAT.
        if (src.find('ADAT-') == 0 and
                (src.find('ADAT-A-') != 0 or src.find('ADAT-B-') != 0)):
            src = 'ADAT-A-' + src[5:]
        # S/PDIF signal shares destination port with ADAT-B signal.
        if src == 'S/PDIF-1/2':
            src = 'ADAT-B-7/8'

        offset = (self.__MIXER_SRC_LABELS.index(src) * 2 + src_ch) * 4

        offsets = [
            offset + 0x0038 + (self.__MIXER_LABELS.index(dst) * 2) * 0x0080,
            offset + 0x0038 + (self.__MIXER_LABELS.index(dst) * 2 + 1) * 0x0080,
        ]

        return offsets

    def __write_src_pair_values(self, dst, src, src_ch, vals):
        offsets = self.__calculate_mixer_src_gain_offsets(dst, src, src_ch)
        for i, offset in enumerate(offsets):
            data = pack('>I', vals[i])
            self.__write_data(offset, data)

    def __read_src_pair_values(self, dst, src, src_ch):
        vals = [0, 0]
        offsets = self.__calculate_mixer_src_gain_offsets(dst, src, src_ch)
        for i, offset in enumerate(offsets):
            data = self.__read_data(offset, 4)
            vals[i] = unpack('>I', data)[0]
        # normalize.
        total = sum(vals)
        if total > self.__MAX_COEFF:
            vals[0] = int(vals[0] * self.__MAX_COEFF / total)
            vals[1] = int(vals[1] * self.__MAX_COEFF / total)
        return vals

    # -60..0dB
    def __parse_val_to_db(self, val):
        return float(-60.0 + val * 60 / self.__MAX_COEFF)

    def __build_val_from_db(self, db):
        if db > 0:
            raise ValueError('Invalid argument for dB value.')
        return int((db + 60.0) * self.__MAX_COEFF / 60)

    def set_mixer_src_gain(self, dst, src, src_ch, db):
        if src_ch not in (0, 1):
            raise ValueError('Invalid argument for channel of stereo pair.')
        vals = self.__read_src_pair_values(dst, src, src_ch)
        total = sum(vals)
        val = self.__build_val_from_db(db)
        if total == 0:
            vals[src_ch] = val
            vals[(src_ch + 1) % 2] = 0
        else:
            vals[0] = vals[0] * val // total
            vals[1] = vals[1] * val // total
        self.__write_src_pair_values(dst, src, src_ch, vals)

    def get_mixer_src_gain(self, dst, src, src_ch):
        if src_ch not in (0, 1):
            raise ValueError('Invalid argument for channel of stereo pair.')
        vals = self.__read_src_pair_values(dst, src, src_ch)
        db = self.__parse_val_to_db(sum(vals))
        return db

    def set_mixer_src_balance(self, dst, src, src_ch, balance):
        vals = self.__read_src_pair_values(dst, src, src_ch)
        total = sum(vals)
        vals[0] = int(total * (100 - balance) // 100)
        vals[1] = total - vals[0]
        self.__write_src_pair_values(dst, src, src_ch, vals)

    def get_mixer_src_balance(self, dst, src, src_ch):
        vals = self.__read_src_pair_values(dst, src, src_ch)
        total = sum(vals)
        if total == 0:
            balance = src_ch * 100.0
        else:
            balance = float(100 * vals[1] // sum(vals))
        return balance

    def set_mixer_src_link(self, dst, src, link):
        if dst not in self.__MIXER_SRC_LINK_OFFSET:
            raise ValueError('Invalid argument for mixer.')
        srcs = self.get_mixer_src_labels()
        if src not in srcs:
            raise ValueError('Invalid argument for source of mixer.')
        data = self.__read_data(self.__MIXER_SRC_LINK_OFFSET[dst], 4)
        val = unpack('>I', data)[0]
        pos = srcs.index(src)
        if link:
            val |= 1 << pos
        else:
            val &= ~(1 << pos)
        data = pack('>I', val)
        self.__write_data(self.__MIXER_SRC_LINK_OFFSET[dst], data)

    def get_mixer_src_link(self, dst, src):
        if dst not in self.__MIXER_SRC_LINK_OFFSET:
            raise ValueError('Invalid argument for mixer.')
        srcs = self.get_mixer_src_labels()
        if src not in srcs:
            raise ValueError('Invalid argument for source of mixer.')
        data = self.__read_data(self.__MIXER_SRC_LINK_OFFSET[dst], 4)
        val = unpack('>I', data)[0]
        pos = srcs.index(src)
        return bool(val & (1 << pos))

    def set_mixer_src_mute(self, dst, src, src_ch, mute):
        if dst not in self.__MIXER_LABELS:
            raise ValueError('Invalid argument for mixer.')
        labels = self.get_mixer_src_labels()
        if src not in labels:
            raise ValueError('Invalid argument for input of mixer.')
        if src_ch not in (0, 1):
            raise ValueError('Invalid argument for channel of stereo pair.')
        offset = self.__MIXER_SRC_MUTE_OFFSETS[dst]
        data = self.__read_data(offset, 4)
        val = unpack('>I', data)[0]
        index = labels.index(src) + src_ch
        if mute:
            val |= (1 << index)
        else:
            val &= ~(1 << index)
        data = pack('>I', val)
        self.__write_data(offset, data)

    def get_mixer_src_mute(self, dst, src, src_ch):
        if dst not in self.__MIXER_LABELS:
            raise ValueError('Invalid argument for mixer.')
        labels = self.get_mixer_src_labels()
        if src not in labels:
            raise ValueError('Invalid argument for input of mixer.')
        if src_ch not in (0, 1):
            raise ValueError('Invalid argument for channel of stereo pair.')
        offset = self.__MIXER_SRC_MUTE_OFFSETS[dst]
        data = self.__read_data(offset, 4)
        val = unpack('>I', data)[0]
        index = labels.index(src) + src_ch
        return bool(val & (1 << index))

    def set_mixer_spdif_src(self, enable):
        if enable:
            val = 0
        else:
            val = 1
        data = pack('>I', val)
        self.__write_data(self.__MIXER_23_24_SWITCH, data)

    def get_mixer_spdif_src(self):
        data = self.__read_data(self.__MIXER_23_24_SWITCH, 4)
        val = unpack('>I', data)[0]
        return bool(val == 0)

    def get_level_labels(self):
        return self.__LEVEL_LABELS

    def __calculate_mixer_out_offset(self, target, ch):
        if target not in self.__MIXER_LABELS:
            raise ValueError('Invalid argument for mixer out')
        if ch not in (0, 1):
            raise ValueError('Invalid argument for channel in stereo pair')
        offset = 0x0438 + (self.__MIXER_LABELS.index(target) * 2 + ch) * 4
        return offset

    def set_mixer_out_volume(self, target, ch, db):
        offset = self.__calculate_mixer_out_offset(target, ch)
        val = self.__build_val_from_db(db)
        data = pack('>I', val)
        self.__write_data(offset, data)

    def get_mixer_out_volume(self, target, ch):
        offset = self.__calculate_mixer_out_offset(target, ch)
        data = self.__read_data(offset, 4)
        val = unpack('>I', data)[0]
        return self.__parse_val_to_db(val)

    def set_mixer_out_level(self, target, ch, level):
        if target not in self.__MIXER_LABELS:
            raise ValueError('Invalid argument for mixer out')
        if ch not in (0, 1):
            raise ValueError('Invalid argument for channel in pair')
        if level not in self.__LEVEL_LABELS:
            raise ValueError('Invalid argument for output level')
        data = self.__read_data(self.__MIXER_OUT_LEVEL_OFFSET, 4)
        val = unpack('>I', data)[0]

        pos = self.__MIXER_LABELS.index(target) * 2 + ch
        val &= ~(1 << pos)
        val |= self.__LEVEL_LABELS.index(level) << pos

        data = pack('>I', val)
        self.__write_data(self.__MIXER_OUT_LEVEL_OFFSET, data)

    def get_mixer_out_level(self, target, ch):
        if target not in self.__MIXER_LABELS:
            raise ValueError('Invalid argument for mixer out')
        if ch not in (0, 1):
            raise ValueError('Invalid argument for channel in pair')
        data = self.__read_data(self.__MIXER_OUT_LEVEL_OFFSET, 4)
        val = unpack('>I', data)[0]

        pos = self.__MIXER_LABELS.index(target) * 2 + ch
        if val & (1 << pos):
            index = 1
        else:
            index = 0

        return self.__LEVEL_LABELS[index]

    def set_mixer_out_mute(self, target, ch, mute):
        if target not in self.__MIXER_LABELS:
            raise ValueError('Invalid argument for mixer out')
        if ch not in (0, 1):
            raise ValueError('Invalid argument for channel in pair')
        data = self.__read_data(self.__MIXER_OUT_MUTE_OFFSETS, 4)
        val = unpack('>I', data)[0]

        pos = self.__MIXER_LABELS.index(target) * 2 + ch
        if mute:
            val |= 1 << pos
        else:
            val &= ~(1 << pos)
        data = pack('>I', val)
        self.__write_data(self.__MIXER_OUT_MUTE_OFFSETS, data)

    def get_mixer_out_mute(self, target, ch):
        if target not in self.__MIXER_LABELS:
            raise ValueError('Invalid argument for mixer out')
        if ch not in (0, 1):
            raise ValueError('Invalid argument for channel in pair')
        data = self.__read_data(self.__MIXER_OUT_MUTE_OFFSETS, 4)
        val = unpack('>I', data)[0]

        pos = self.__MIXER_LABELS.index(target) * 2 + ch
        return bool(val & (1 << pos))

    def get_output_labels(self):
        labels = []
        for ch in range(1, self.__specs['analog-in'], 2):
            labels.append('Analog-{0}/{1}'.format(ch, ch + 1))
        labels.append('Headphone-1/2')
        labels.append('Headphone-3/4')
        labels.append('S/PDIF-1/2')
        return labels

    def get_output_src_labels(self, target):
        labels = []
        if target.find('Analog-') == 0:
            labels.append('Mixer-' + target[7:])
        elif target == 'Headphone-1/2':
            labels.append('Mixer-1/2')
        else:
            labels.extend(self.__MIXER_LABELS)
        return labels

    def set_output_src(self, target, src):
        if target not in self.get_output_labels():
            raise ValueError('Invalid argument for output.')
        srcs = self.get_output_src_labels(target)
        if src not in srcs:
            raise ValueError('Invalid argument for source of output.')
        if len(srcs) == 1:
            return
        if target == 'Headphone-3/4':
            offset = self.__HP34_OUT_SRC_OFFSET
        elif target == 'S/PDIF-1/2':
            offset = self.__SPDIF_OUT_SRC_OFFSET
        else:
            return
        val = srcs.index(src)
        data = pack('>I', val)
        self.__write_data(offset, data)

    def get_output_src(self, target):
        if target not in self.get_output_labels():
            raise ValueError('Invalid argument for output.')
        srcs = self.get_output_src_labels(target)
        if len(srcs) == 1:
            return srcs[0]
        if target == 'Headphone-3/4':
            offset = self.__HP34_OUT_SRC_OFFSET
        elif target == 'S/PDIF-1/2':
            offset = self.__SPDIF_OUT_SRC_OFFSET
        else:
            return None
        data = self.__read_data(offset, 4)
        val = unpack('>I', data)[0]
        return srcs[val]

    def get_meter_labels(self):
        labels = []
        for ch in range(1, 9):
            labels.append('Analog-{0}'.format(ch))
        for ch in range(1, 9):
            labels.append('Stream-{0}'.format(ch))
        if not self.__specs['has_adat_b']:
            for ch in range(1, 9):
                labels.append('ADAT-{0}'.format(ch))
            for ch in range(1, 3):
                labels.append('S/PDIF-{0}'.format(ch))
        else:
            for ch in range(1, 9):
                labels.append('ADAT-A-{0}'.format(ch))
            for ch in range(1, 7):
                labels.append('ADAT-B-{0}'.format(ch))
            data = self.__read_data(self.__MIXER_23_24_SWITCH, 4)
            val = unpack('>I', data)[0]
            if val:
                labels.append('ADAT-B-7/8')
            else:
                labels.append('S/PDIF-1/2')
        for ch in range(1, 9):
            labels.append('Mixer-{0}'.format(ch))
        return labels

    def get_meters(self):
        meters = []
        data = self.__read_data(self.__METER_OFFSET, 160)
        vals = unpack('>40I', data)
        meters.extend(vals[0:24])
        if self.__specs['has_adat_b']:
            meters.extend(vals[25:30])
        meters.extend(vals[30:])
        for i, meter in enumerate(meters):
            meters[i] = self.__parse_val_to_db(meter)
        return meters

    def get_mix_blend_ratio(self):
        data = self.__read_data(self.__MIX_BLEND_OFFSET, 4)
        val = unpack('>I', data)[0]
        return val / 0x100

    def get_main_level_ratio(self):
        data = self.__read_data(self.__MAIN_LEVEL_OFFSET, 4)
        val = unpack('>I', data)[0]
        return val / 0x100
