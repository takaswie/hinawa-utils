from motu.motu_protocol_abstract import MotuProtocolAbstract

__all__ = ['MotuProtocolV2']

class MotuProtocolV2(MotuProtocolAbstract):
    # direction/index/mask/shift
    OPT_IFACE_MODE_ATTRS = {
        'in':   (0x00000300, 8),
        'out':  (0x00000c00, 10),
    }

    PACKET_SIZE_ATTRS = {
        'in':   (0x00000080, 7),
        'out':  (0x00000040, 6),
    }

    def get_supported_sampling_rates(self):
        if self._unit.name == '828mk2':
            return self.SUPPORTED_SAMPLING_RATES_X2

    def get_sampling_rate(self):
        quads = self.read(0x0b14, 1)
        val = (quads[0] & 0x00000038) >> 3
        return self.SUPPORTED_SAMPLING_RATES_X4[val]

    def set_sampling_rate(self, rate):
        quads = self.read(0x0b14, 1)
        quads[0] &= ~0x00000038
        quads[0] |= self.SUPPORTED_SAMPLING_RATES_X4.index(rate) << 3
        self.write(0x0b14, quads)

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
        quads = self.read(0x0b14, 1)

        val = quads[0] & 0x00000007
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
        quads = self.read(0x0b14, 1)

        quads[0] &= ~0x00000007
        if source == self.CLOCK_ADAT_ON_OPT:
            quads[0] |= 0x01
        elif source == self.CLOCK_WORD_ON_BNC:
            quads[0] |= 0x04
        elif source == self.CLOCK_ADAT_ON_DSUB:
            quads[0] |= 0x05
        elif source in (self.CLOCK_SPDIF_ON_OPT, self.CLOCK_SPDIF_ON_COAX):
            mode = self.get_opt_iface_mode('in', 'A')
            if source == self.CLOCK_SPDIF_ON_OPT and mode != 'S/PDIF':
                raise ValueError('This mode is currently unavailable.')
            quads[0] |= 0x02

        self.write(0x0b14, quads)

    def get_supported_opt_iface_indexes(self):
        if self._unit.name == '828mk2':
            return self.SUPPORTED_OPT_IFACE_INDEXES[0:1]
        else:
            return self.SUPPORTED_OPT_IFACE_INDEXES

    def get_opt_iface_mode(self, direction, index):
        quads = self.read(0x0c04, 1)

        mask, shift = self.OPT_IFACE_MODE_ATTRS[direction]
        val = (quads[0] & mask) >> shift
        if val >= len(self.SUPPORTED_OPT_IFACE_MODES):
            raise OSError('Unexpected value for opt iface mode.')

        if val == 1:
            val = 2
        elif val == 2:
            val = 1
        return self.SUPPORTED_OPT_IFACE_MODES[val]

    def set_opt_iface_mode(self, direction, index, mode):
        quads = self.read(0x0c04, 1)

        idx = self.SUPPORTED_OPT_IFACE_MODES.index(mode)
        if idx == 1:
            idx = 2
        elif idx == 2:
            idx = 1

        mask, shift = self.OPT_IFACE_MODE_ATTRS[direction]
        quads[0] &= ~mask
        quads[0] |= idx << shift

        self.write(0x0c04, quads)

        mask, shift = self.PACKET_SIZE_ATTRS[direction]
        quads = self.read(0x0b10, 1)
        quads[0] &= ~mask
        if mode != 'ADAT':
            quads[0] |= 1 << shift

        self.write(0x0b10, quads)
