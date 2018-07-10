from struct import pack, unpack

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from bebob.bebob_unit import BebobUnit
from ta1394.audio import AvcAudio

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
        'Analog-9/10',
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
        'Analog-9/10':  (0x128, 3),
    }

    _OUTPUT_PARAMS_OFFSETS = {
        # output pair   offset
        'Analog-1/2':   0x140,
        'Analog-3/4':   0x144,
        'Analog-5/6':   0x148,
        'Analog-7/8':   0x14c,
        'Analog-9/10':  0x150,  # TODO: ?
    }

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

    def get_output_labels(self):
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

    def set_output_volume(self, target, db):
        if target not in self._OUTPUTS:
            raise ValueError('Invalid value for output target.')
        offset = self._OUTPUT_PARAMS_OFFSETS[target]
        quads = self._read_quads(offset, 1)
        data = AvcAudio.build_data_from_db(db)
        quads[0] &= ~0x0000ffff
        quads[0] |= unpack('>H', data)[0]
        self._write_quads(offset, quads)

    def get_output_volume(self, target):
        if target not in self._OUTPUTS:
            raise ValueError('Invalid value for output target.')
        offset = self._OUTPUT_PARAMS_OFFSETS[target]
        quads = self._read_quads(offset, 1)
        data = pack('>I', quads[0])
        return AvcAudio.parse_data_to_db(data[2:])
