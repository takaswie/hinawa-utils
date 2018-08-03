# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from struct import pack, unpack

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from hinawa_utils.bebob.bebob_unit import BebobUnit
from hinawa_utils.ta1394.audio import AvcAudio
from hinawa_utils.ta1394.general import AvcConnection

__all__ = ['FocusriteSaffireproIoUnit']

class FocusriteSaffireproIoUnit(BebobUnit):
    _BASE_ADDR = 0x000100000000

    _INPUTS = (
        'Analog-1/2',
        'Analog-3/4',
        'Analog-5/6',
        'Analog-7/8',
        'S/PDIF-1/2',
        'ADAT-1/2',
        'ADAT-3/4',
        'ADAT-5/6',
        'ADAT-7/8',
        'ADAT-9/10',
        'ADAT-11/12',
        'ADAT-13/14',
        'ADAT-15/16',
    )

    _OUTPUTS = (
        'Analog-1/2',
        'Analog-3/4',
        'Analog-5/6',
        'Analog-7/8',
        'S/PDIF-1/2',
    )

    _MIXER_INPUT_OFFSETS = {
        # input pair    offset
        'Analog-1/2':   0x00,
        'Analog-3/4':   0x10,
        'Analog-5/6':   0x20,
        'Analog-7/8':   0x30,
        'S/PDIF-1/2':   0x40,
        'ADAT-1/2':     0x50,
        'ADAT-3/4':     0x60,
        'ADAT-5/6':     0x70,
        'ADAT-7/8':     0x80,
        'ADAT-9/10':    0x90,
        'ADAT-11/12':   0xa0,
        'ADAT-13/14':   0xb0,
        'ADAT-15/16':   0xc0,
    }

    _OUTPUT_SRC_OFFSETS = {
        # output pair   offset  pair_count
        'Analog-1/2':   (0xd0,  2),
        'Analog-3/4':   (0xe0,  3),
        'Analog-5/6':   (0xf8,  3),
        'Analog-7/8':   (0x110, 3),
        'S/PDIF-1/2':   (0x128, 3),
    }

    _OUTPUT_PARAMS_OFFSETS = {
        # output pair   offset
        'Analog-1/2':   0x140,
        'Analog-3/4':   0x144,
        'Analog-5/6':   0x148,
        'Analog-7/8':   0x14c,
    }

    _RATE_MODES = {
        'low':      ( 44100,  48000),
        'middle':   ( 88200,  96000),
        'high':     (176400, 192000),
    }

    _RATE_BITS = {
        44100:  1,
        48000:  2,
        88200:  3,
        96000:  4,
        176400: 5,
        192000: 6,
    }

    _CLOCK_BITS = {
        'Internal':     0,
        'S/PDIF':       2,
        'ADAT1':        3,
        'ADAT2':        4,
        'Word-clock':   5,
    }

    _IO10_CAPS = {
        'rate-modes':   ('low', 'middle'),
        'clocks':       ('Internal', 'S/PDIF'),
    }

    _IO26_CAPS = {
        'rate-modes':   ('low', 'middle', 'high'),
        'clocks':       ('Internal', 'S/PDIF', 'ADAT1', 'ADAT2', 'Word-clock'),
    }

    def __init__(self, path):
        CAPS = {
            0x000006: self._IO10_CAPS,
            0x000003: self._IO26_CAPS,
        }
        super().__init__(path)
        if self.model_id not in CAPS:
            raise OSError('Unsupported unit.')
        self._caps = CAPS[self.model_id]

    def _write_quads(self, offset, quads):
        frames = []
        count = len(quads)
        for i in range(count):
            frames.extend(pack('>I', quads[0]))
            quads = quads[1:]
        req = Hinawa.FwReq()
        req.write(self, self._BASE_ADDR + offset, frames)

    def _read_quads(self, offset, count):
        quads = []
        req = Hinawa.FwReq()
        size = count * 4
        frames = req.read(self, self._BASE_ADDR + offset, size)
        for i in range(count):
            quads.append(unpack('>I', frames[0:4])[0])
            frames = frames[4:]
        return quads

    def get_mixer_input_labels(self):
        return self._INPUTS
    def set_mixer_input_balance(self, target, ch, balance):
        if target not in self._INPUTS:
            raise ValueError('Invalid value for input target.')
        offset = self._MIXER_INPUT_OFFSETS[target]
        quads = self._read_quads(offset, 4)
        pos = ch - 1
        total = quads[pos] + quads[pos + 2]
        quads[pos] = int(total * balance // 100)
        quads[pos + 2] = int(total * (100 - balance) // 100)
        self._write_quads(offset, quads)
    def get_mixer_input_balance(self, target, ch):
        if target not in self._INPUTS:
            raise ValueError('Invalid value for input target.')
        offset = self._MIXER_INPUT_OFFSETS[target]
        quads = self._read_quads(offset, 4)
        pos = ch - 1
        total = quads[pos] + quads[pos + 2]
        return quads[pos] * 100 // total
    def set_mixer_input_gain(self, target, ch, db):
        if target not in self._INPUTS:
            raise ValueError('Invalid value for input target.')
        offset = self._MIXER_INPUT_OFFSETS[target]
        quads = self._read_quads(offset, 4)
        pos = ch - 1
        total = quads[pos] + quads[pos + 2]
        data = AvcAudio.build_data_from_db(db)
        value = unpack('>H', data)[0]
        quads[pos] = int(value * quads[pos] // total)
        quads[pos + 2] = int(value * quads[pos + 2] // total)
        self._write_quads(offset, quads)
    def get_mixer_input_gain(self, target, ch):
        if target not in self._INPUTS:
            raise ValueError('Invalid value for input target.')
        offset = self._MIXER_INPUT_OFFSETS[target]
        quads = self._read_quads(offset, 4)
        pos = ch - 1
        total = quads[pos] + quads[pos + 2]
        data = pack('>H', total)
        return AvcAudio.parse_data_to_db(data)

    def get_output_destination_labels(self):
        return self._OUTPUTS
    def get_output_source_labels(self, target):
        labels = []
        labels.append('Stream-1/2')
        if target != 'Analog-1/2':
            labels.append(target.replace('Analog-', 'Stream-'))
        labels.append('Mixer-1/2')
        return labels
    def set_output_source(self, target, source):
        if target not in self._OUTPUTS:
            raise ValueError('Invalid value for output target.')
        labels = self.get_output_source_labels(target)
        if source not in labels:
            raise ValueError('Invalid value for target source.')
        offset, pair_count = self._OUTPUT_SRC_OFFSETS[target]
        quads = []
        for i in range(pair_count * 2):
            quads.append(0x00000000)
        quads[labels.index(source)] = 0x00007fff
        quads[len(labels) + labels.index(source)] = 0x00007fff
        self._write_quads(offset, quads)
    def get_output_source(self, target):
        if target not in self._OUTPUTS:
            raise ValueError('Invalid value for output target.')
        labels = self.get_output_source_labels(target)
        offset, pair_count = self._OUTPUT_SRC_OFFSETS[target]
        quads = self._read_quads(offset, pair_count * 2)
        for i in range(pair_count):
            if quads[i] > 0 and quads[pair_count + i] > 0:
                return labels[i]
        return None

    def get_output_labels(self):
        return list(self._OUTPUT_PARAMS_OFFSETS.keys())
    def _write_output_quad(self, target, quads):
        if target not in self._OUTPUT_PARAMS_OFFSETS:
            raise ValueError('Invalid value for output target.')
        offset = self._OUTPUT_PARAMS_OFFSETS[target]
        self._write_quads(offset, quads)
    def _read_output_quad(self, target):
        if target not in self._OUTPUT_PARAMS_OFFSETS:
            raise ValueError('Invalid value for output target.')
        offset = self._OUTPUT_PARAMS_OFFSETS[target]
        return self._read_quads(offset, 1)
    def set_output_volume(self, target, db):
        quads = self._read_output_quad(target)
        data = AvcAudio.build_data_from_db(db)
        quads[0] &= ~0x0000ffff
        quads[0] |= unpack('>H', data)[0]
        self._write_output_quad(target, quads)
    def get_output_volume(self, target):
        quads = self._read_output_quad(target)
        data = pack('>I', quads[0])
        return AvcAudio.parse_data_to_db(data[2:])
    def set_output_mute(self, target, enable):
        quads = self._read_output_quad(target)
        if enable:
            quads[0] |= 1 << 24
        else:
            quads[0] &= ~(1 << 24)
        self._write_output_quad(target, quads)
    def get_output_mute(self, target):
        quads = self._read_output_quad(target)
        return bool(quads[0] & (1 << 24))
    def set_output_hwctl(self, target, enable):
        quads = self._read_output_quad(target)
        if enable:
            quads[0] |= 1 << 26
        else:
            quads[0] &= ~(1 << 26)
        self._write_output_quad(target, quads)
    def get_output_hwctl(self, target):
        quads = self._read_output_quad(target)
        return bool(quads[0] & (1 << 26))
    def set_output_pad(self, target, enable):
        quads = self._read_output_quad(target)
        if enable:
            quads[0] |= 1 << 27
        else:
            quads[0] &= ~(1 << 27)
        self._write_output_quad(target, quads)
    def get_output_pad(self, target):
        quads = self._read_output_quad(target)
        return bool(quads[0] & (1 << 27))
    def set_output_dim(self, target, enable):
        quads = self._read_output_quad(target)
        if enable:
            quads[0] |= 1 << 28
        else:
            quads[0] &= ~(1 << 28)
        self._write_output_quad(target, quads)
    def get_output_dim(self, target):
        quads = self._read_output_quad(target)
        return bool(quads[0] & (1 << 28))

    def get_supported_rate_modes(self):
        return self._caps['rate-modes']
    def set_rate_mode(self, mode):
        if self.get_property('streaming'):
            raise OSError('Packet streaming starts')
        if mode not in self._caps['rate-modes']:
            raise ValueError('Invalid argument for frequency mode.')
        quads = []
        quads.append(self._RATE_BITS[self._RATE_MODES[mode][0]])
        # This corresponds to bus reset and the unit disappears from the bus,
        # then appears with a set mode.
        self._write_quads(0x150, quads)
    def get_rate_mode(self):
        rate = AvcConnection.get_plug_signal_format(self.fcp, 'input', 0)
        for mode, rates in self._RATE_MODES.items():
            if rate in rates and mode in self._caps['rate-modes']:
                break
        else:
            raise OSError('Invalid state for sampling rate.')
        return mode

    def get_supported_sampling_rates(self):
        rate = AvcConnection.get_plug_signal_format(self.fcp, 'input', 0)
        for mode, rates in self._RATE_MODES.items():
            if rate in rates and mode in self._caps['rate-modes']:
                break
        else:
            raise OSError('Invalid state for sampling rate.')
        return rates
    def set_sampling_rate(self, rate):
        if self.get_property('streaming'):
            raise OSError('Packet streaming starts')
        curr_rate = AvcConnection.get_plug_signal_format(self.fcp, 'input', 0)
        for mode, rates in self._RATE_MODES.items():
            if curr_rate in rates:
                break
        else:
            raise OSError('Invalid state for sampling rate.')
        if rate not in rates:
            raise ValueError('Invalid argument for sampling rate.')
        AvcConnection.set_plug_signal_format(self.fcp, 'input', 0, rate)
        AvcConnection.set_plug_signal_format(self.fcp, 'output', 0, rate)
    def get_sampling_rate(self):
        in_rate = AvcConnection.get_plug_signal_format(self.fcp, 'input', 0)
        out_rate = AvcConnection.get_plug_signal_format(self.fcp, 'output', 0)
        if in_rate != out_rate:
            raise OSError('Sampling rate mismatch: ', in_rate, out_rate)
        return in_rate

    def get_supported_clock_sources(self):
        return self._caps['clocks']
    def set_clock_source(self, source):
        if self.get_property('streaming'):
            raise OSError('Packet streaming starts')
        if source not in self._caps['clocks']:
            raise ValueError('Invalid argument for clock source.')
        quads = []
        quads.append(self._CLOCK_BITS[source])
        self._write_quads(0x0174, quads)
    def get_clock_source(self):
        quads = self._read_quads(0x0174, 1)
        quads[0] & 0xff
        for key, val in self._CLOCK_BITS.items():
            if val == quads[0] & 0xff:
                break
        else:
            raise OSError('Invalid state of clock source.')
        return key
