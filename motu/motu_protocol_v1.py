from motu.motu_protocol_abstract import MotuProtocolAbstract

__all__ = ['MotuProtocolV1']

class MotuProtocolV1(MotuProtocolAbstract):
    SUPPORTED_MODELS = ('828', '896')

    # direction/mask/shift
    OPT_IFACE_MODE_ATTRS = {
        'in':   ((0x00008000, 15), (0x00000080, 7)),
        'out':  ((0x00004000, 14), (0x00000040, 6))
    }

    PACKET_SIZE_ATTRS = {
        'in':   (0x00000080, 7),
        'out':  (0x00000040, 6),
    }

    def get_supported_sampling_rates(self):
        if self._unit.name == '828':
            return self.SUPPORTED_SAMPLING_RATES_X1
        elif self._unit.name == '896':
            return self.SUPPORTED_SAMPLING_RATES_X2

    def get_sampling_rate(self):
        quads = self.read(0x0b00, 1)
        if quads[0] & 0x00000004:
            rate = 48000
        else:
            rate = 44100
        if quads[0] & 0x00000008:
            rate * 2
        return rate

    def set_sampling_rate(self, rate):
        quads = self.read(0x0b00, 1)
        quads[0] &= ~0x0000000c
        if rate % 48000 == 0:
            quads[0] |= 0x00000004
        if rate > 48000:
            quads[0] |= 0x00000008
        self.write(0x0b00, quads)

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
        quads = self.read(0x0b00, 1)

        if quads[0] & 0x00000001:
            if quads[0] & 0x00000020:
                return self.CLOCK_ADAT_ON_OPT
            else:
                return self.CLOCK_ADAT_ON_DSUB
        elif quads[0] & 0x00000002:
            if quads[0] & 0x00008000:
                return self.CLOCK_SPDIF_ON_OPT
            else:
                return self.CLOCK_SPDIF_ON_COAX
        else:
            return self.CLOCK_INTERNAL

    def set_clock_source(self, source):
        quads = self.read(0x0b00, 1)
        quads[0] &= ~0x00008023

        if source != self.CLOCK_ADAT_ON_DSUB:
            quads[0] |= 0x00000020

        if source in (self.CLOCK_ADAT_ON_DSUB, self.CLOCK_ADAT_ON_OPT):
            quads[0] |= 0x00000001
        elif source == self.CLOCK_SPDIF_ON_OPT:
            quads[0] |= 0x00000002
        elif source == self.CLOCK_SPDIF_ON_COAX:
            if quads[0] & 0x00008000:
                raise ValueError('This mode is currently unavailable.')
            quads[0] |= 0x00008002
        elif source == self.CLOCK_WORD_ON_BNC:
            quads[0] |= 0x00000010

        self.write(0x0b00, quads)

    def get_supported_opt_iface_indexes(self):
        return self.SUPPORTED_OPT_IFACE_INDEXES[0:1]

    def get_opt_iface_mode(self, direction, index):
        quads = self.read(0x0b00, 1)

        mask, shift = self.OPT_IFACE_MODE_ATTRS[direction][0]
        if quads[0] & mask:
            return self.SUPPORTED_OPT_IFACE_MODES[1]
        else:
            # Need to check the size of data block, sigh...
            quads = self.read(0x0b10, 1)

            mask, shift = self.OPT_IFACE_MODE_ATTRS[direction][1]
            if quads[0] & mask:
                return self.SUPPORTED_OPT_IFACE_MODES[0]
            else:
                return self.SUPPORTED_OPT_IFACE_MODES[2]

    def set_opt_iface_mode(self, direction, index, mode):
        quads = self.read(0x0b00, 1)
        quads[0] &= 0xc0000000

        mask, shift = self.OPT_IFACE_MODE_ATTRS[direction][0]
        if self.SUPPORTED_OPT_IFACE_MODES.index(mode) == 1:
            quads[0] |= 1 << shift

        self.write(0x0b00, quads)

        mask, shift = self.PACKET_SIZE_ATTRS[direction]
        quads = self.read(0x0b10, 1)
        quads[0] &= ~mask
        if mode != 'ADAT':
            quads[0] |= 1 << shift

        self.write(0x0b10, quads)
