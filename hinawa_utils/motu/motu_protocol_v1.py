# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.motu.motu_protocol_abstract import MotuProtocolAbstract

__all__ = ['MotuProtocolV1']

class MotuProtocolV1(MotuProtocolAbstract):
    SUPPORTED_MODELS = ('828', '896')

    # direction/mask/shift
    OPT_IFACE_MODE_ATTRS = {
        'in':   ((2, 0x80, 3), (3, 0x80, 3)),
        'out':  ((2, 0x40, 2), (3, 0x40, 2))
    }

    PACKET_SIZE_ATTRS = {
        'in':   (3, 0x80, 3),
        'out':  (3, 0x40, 2),
    }

    def get_supported_sampling_rates(self):
        if self._unit.name == '828':
            return self.SUPPORTED_SAMPLING_RATES_X1
        elif self._unit.name == '896':
            return self.SUPPORTED_SAMPLING_RATES_X2

    def get_sampling_rate(self):
        frames = self.read(0x0b00, 4)
        if frames[3] & 0x04:
            rate = 48000
        else:
            rate = 44100
        if frames[3] & 0x08:
            rate * 2
        return rate

    def set_sampling_rate(self, rate):
        frames = self.read(0x0b00, 4)
        frames[0] &= ~0x0c
        if rate % 48000 == 0:
            frames[3] |= 0x04
        if rate > 48000:
            frames[3] |= 0x08
        self.write(0x0b00, frames)

    def get_supported_clock_sources(self):
        sources = [
            self.CLOCK_INTERNAL,
            self.CLOCK_ADAT_ON_DSUB,
        ]
        if self.get_opt_iface_mode('in', 'A') == 'S/PDIF':
            sources.append(self.CLOCK_SPDIF_ON_OPT)
        else:
            sources.append(self.CLOCK_ADAT_ON_OPT)
            sources.append(self.CLOCK_SPDIF_ON_COAX)

        if self._unit.name == '896':
            sources.append(self.CLOCK_WORD_ON_BNC)

        return sources

    def get_clock_source(self):
        frames = self.read(0x0b00, 4)

        if frames[3] & 0x01:
            if frames[3] & 0x20:
                return self.CLOCK_ADAT_ON_OPT
            else:
                return self.CLOCK_ADAT_ON_DSUB
        elif frames[3] & 0x02:
            if frames[2] & 0x80:
                return self.CLOCK_SPDIF_ON_OPT
            else:
                return self.CLOCK_SPDIF_ON_COAX
        else:
            return self.CLOCK_INTERNAL

    def set_clock_source(self, source):
        frames = self.read(0x0b00, 4)
        frames[2] &= ~0x80
        frames[3] &= ~0x23

        if source != self.CLOCK_ADAT_ON_DSUB:
            frames[3] |= 0x20

        if source in (self.CLOCK_ADAT_ON_DSUB, self.CLOCK_ADAT_ON_OPT):
            frames[3] |= 0x01
        elif source == self.CLOCK_SPDIF_ON_OPT:
            frames[3] |= 0x02
        elif source == self.CLOCK_SPDIF_ON_COAX:
            if frames[2] & 0x80:
                raise ValueError('This mode is currently unavailable.')
            frames[2] |= 0x80
            frames[3] |= 0x02
        elif source == self.CLOCK_WORD_ON_BNC:
            frames[3] |= 0x10

        self.write(0x0b00, frames)

    def get_supported_opt_iface_indexes(self):
        return self.SUPPORTED_OPT_IFACE_INDEXES[0:1]

    def get_opt_iface_mode(self, direction, index):
        frames = self.read(0x0b00, 4)

        pos, mask, shift = self.OPT_IFACE_MODE_ATTRS[direction][0]
        if frames[pos] & mask:
            return self.SUPPORTED_OPT_IFACE_MODES[1]
        else:
            # Need to check the size of data block, sigh...
            frames = self.read(0x0b10, 4)

            pos, mask, shift = self.OPT_IFACE_MODE_ATTRS[direction][1]
            if frames[pos] & mask:
                return self.SUPPORTED_OPT_IFACE_MODES[0]
            else:
                return self.SUPPORTED_OPT_IFACE_MODES[2]

    def set_opt_iface_mode(self, direction, index, mode):
        frames = self.read(0x0b00, 4)
        frames[0] &= 0xc0

        pos, mask, shift = self.OPT_IFACE_MODE_ATTRS[direction][0]
        if self.SUPPORTED_OPT_IFACE_MODES.index(mode) == 1:
            frames[pos] |= 1 << shift

        self.write(0x0b00, frames)

        pos, mask, shift = self.PACKET_SIZE_ATTRS[direction]
        frames = self.read(0x0b10, 4)
        frames[pos] &= ~mask
        if mode != 'ADAT':
            frames[pos] |= 1 << shift

        self.write(0x0b10, frames)
