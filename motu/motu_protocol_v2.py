# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from motu.motu_protocol_abstract import MotuProtocolAbstract

__all__ = ['MotuProtocolV2']

class MotuProtocolV2(MotuProtocolAbstract):
    # direction/index/mask/shift
    OPT_IFACE_MODE_ATTRS = {
        'in':   (2, 0x03, 0),
        'out':  (2, 0x0c, 2),
    }

    PACKET_SIZE_ATTRS = {
        'in':   (3, 0x80, 7),
        'out':  (3, 0x40, 6),
    }

    def get_supported_sampling_rates(self):
        if self._unit.name in ('828mk2', ):
            return self.SUPPORTED_SAMPLING_RATES_X2
        if self._unit.name in ('Traveler', ):
            return self.SUPPORTED_SAMPLING_RATES_X4

    def get_sampling_rate(self):
        frames = self.read(0x0b14, 4)
        val = (frames[3] & 0x38) >> 3
        return self.SUPPORTED_SAMPLING_RATES_X4[val]

    def set_sampling_rate(self, rate):
        frames = self.read(0x0b14, 4)
        frames[3]  &= ~0x00000038
        frames[3] |= self.SUPPORTED_SAMPLING_RATES_X4.index(rate) << 3
        self.write(0x0b14, frames)

    def get_supported_clock_sources(self):
        sources = [
            self.CLOCK_INTERNAL,
            self.CLOCK_WORD_ON_BNC,
            self.CLOCK_SPDIF_ON_COAX,
            self.CLOCK_ADAT_ON_DSUB,
        ]
        mode = self.get_opt_iface_mode('in', 'A')
        if mode == 'S/PDIF':
            sources.append(self.CLOCK_SPDIF_ON_OPT)
        else:
            sources.append(self.CLOCK_ADAT_ON_OPT)

        return sources

    def get_clock_source(self):
        frames = self.read(0x0b14, 4)

        val = frames[3] & 0x07
        if val == 0:
            return self.CLOCK_INTERNAL
        elif val == 1:
            return self.CLOCK_ADAT_ON_OPT
        elif val == 4:
            return self.CLOCK_WORD_ON_BNC
        elif val == 5:
            return self.CLOCK_ADAT_ON_DSUB
        elif val == 2:
            mode = self.get_opt_iface_mode('in', 'A')
            if mode == 'S/PDIF':
                return self.CLOCK_ADAT_ON_OPT
            else:
                return self.CLOCK_SPDIF_ON_COAX

    def set_clock_source(self, source):
        frames = self.read(0x0b14, 4)

        frames[3] &= ~0x07
        if source == self.CLOCK_ADAT_ON_OPT:
            frames[3] |= 0x01
        elif source == self.CLOCK_WORD_ON_BNC:
            frames[3] |= 0x04
        elif source == self.CLOCK_ADAT_ON_DSUB:
            frames[3] |= 0x05
        elif source in (self.CLOCK_SPDIF_ON_OPT, self.CLOCK_SPDIF_ON_COAX):
            mode = self.get_opt_iface_mode('in', 'A')
            if source == self.CLOCK_SPDIF_ON_OPT and mode != 'S/PDIF':
                raise ValueError('This mode is currently unavailable.')
            frames[3] |= 0x02

        self.write(0x0b14, frames)

    def get_supported_opt_iface_indexes(self):
        if self._unit.name == '828mk2':
            return self.SUPPORTED_OPT_IFACE_INDEXES[0:1]
        else:
            return self.SUPPORTED_OPT_IFACE_INDEXES

    def get_opt_iface_mode(self, direction, index):
        frames = self.read(0x0c04, 4)

        pos, mask, shift = self.OPT_IFACE_MODE_ATTRS[direction]
        val = (frames[pos] & mask) >> shift
        if val >= len(self.SUPPORTED_OPT_IFACE_MODES):
            raise OSError('Unexpected value for opt iface mode.')

        if val == 1:
            val = 2
        elif val == 2:
            val = 1
        return self.SUPPORTED_OPT_IFACE_MODES[val]

    def set_opt_iface_mode(self, direction, index, mode):
        frames = self.read(0x0c04, 4)

        idx = self.SUPPORTED_OPT_IFACE_MODES.index(mode)
        if idx == 1:
            idx = 2
        elif idx == 2:
            idx = 1

        pos, mask, shift = self.OPT_IFACE_MODE_ATTRS[direction]
        frames[pos] &= ~mask
        frames[pos] |= idx << shift

        self.write(0x0c04, frames)

        pos, mask, shift = self.PACKET_SIZE_ATTRS[direction]
        frames = self.read(0x0b10, 4)
        frames[pos] &= ~mask
        if mode != 'ADAT':
            frames[pos] |= 1 << shift

        self.write(0x0b10, frames)
