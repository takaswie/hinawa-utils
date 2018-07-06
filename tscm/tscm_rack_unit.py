from struct import pack,unpack

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from tscm.tscm_unit import TscmUnit

__all__ = ['TscmRackUnit']

class TscmRackUnit(TscmUnit):
    _OFFSET_CH_CTL = 0x0408

    _CH_LABELS = (
        'Analog-1', 'Analog-2', 'Analog-3', 'Analog-4',
        'Analog-5', 'Analog-6', 'Analog-7', 'Analog-8',
        'ADAT-1', 'ADAT-2', 'ADAT-3', 'ADAT-4',
        'ADAT-5', 'ADAT-6', 'ADAT-7', 'ADAT-8',
        'S/PDIF-1', 'S/PDIF-2',
    )
    _CH_FRAME_SIZE = 4

    def __init__(self, path):
        super().__init__(path)

        # For permanent cache.
        guid = self.get_property('guid')
        self._filepath = '/tmp/hinawa-{0:08x}'.format(guid)

        # For process local cache.
        self._cache = bytearray(len(self._CH_LABELS) * self._CH_FRAME_SIZE)

        # Sync these caches.
        self._load_cache()
        self._write_cache()

    def _load_cache(self):
        try:
            with open(self._filepath, 'r') as f:
                for i, line in enumerate(f):
                    self._cache[i] = int(line.strip(), base=16)
        except Exception as e:
            # This is initial values.
            for i in range(len(self._CH_LABELS)):
                pos = i * self._CH_FRAME_SIZE
                self._cache[pos] = i
                if i % 2 == 0:
                    self._cache[pos + 1] = 0x00
                else:
                    self._cache[pos + 1] = 0xff
                self._cache[pos + 2] = 0x7f
                self._cache[pos + 3] = 0xff
        finally:
            for i in range(len(self._CH_LABELS)):
                pos = i * self._CH_FRAME_SIZE
                self.write_quadlet(0x0408, self._cache[pos:pos + 4])

    def _write_cache(self):
        with open(self._filepath, 'w+') as fd:
            for i, frame in enumerate(self._cache):
                fd.write('{0:02x}\n'.format(frame))

    def _write_frames(self, frames):
        # Write to the unit.
        self.write_quadlet(self._OFFSET_CH_CTL, frames)

        # Refresh process cache.
        ch = frames[0] & 0x7f
        for i, frame in enumerate(frames):
            pos = ch * self._CH_FRAME_SIZE
            self._cache[pos + i] = frame

        # Refresh permanent cache.
        self._write_cache()

    def _get_frames(self, ch):
        if ch not in self._CH_LABELS:
            raise ValueError('Invalid argument for channel label: {0}'.format(ch))
        pos = self._CH_LABELS.index(ch) * self._CH_FRAME_SIZE
        return self._cache[pos:pos + self._CH_FRAME_SIZE]

    def get_channel_labels(self):
        return self._CH_LABELS

    def set_mute(self, ch, state):
        frames = self._get_frames(ch)
        if state:
            frames[0] |= 0x80
        else:
            frames[0] &= ~0x80
        self._write_frames(frames)
    def get_mute(self, ch):
        frames = self._get_frames(ch)
        return bool(frames[0] & 0x80)

    def set_balance(self, ch, balance):
        if balance < 0 or balance > 99:
            raise ValueError('Invalid argument for LR Balance: {0}'.format(balance))
        frames = self._get_frames(ch)
        frames[1] = balance * 0xff // 99
        self._write_frames(frames)
    def get_balance(self, ch):
        frames = self._get_frames(ch)
        return frames[1] * 99 // 0xff

    def set_gain(self, ch, gain):
        if gain < 0 or gain > 99:
            raise ValueError('Invalid argument for gain: {0}'.format(gain))
        frames = self._get_frames(ch)
        gain = int(gain * 0x7fff // 99)
        data = pack('>H', gain)
        frames[2] = data[0]
        frames[3] = data[1]
        self._write_frames(frames)
    def get_gain(self, ch):
        frames = self._get_frames(ch)
        return unpack('>H', frames[2:4])[0] * 99 // 0x7fff
