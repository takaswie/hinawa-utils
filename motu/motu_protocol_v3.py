from motu.motu_protocol_abstract import MotuProtocolAbstract

__all__ = ['MotuProtocolV3']

class MotuProtocolV3(MotuProtocolAbstract):
    def get_supported_sampling_rates(self):
        return self.SUPPORTED_SAMPLING_RATES_X4

    def get_sampling_rate(self):
        quads = self.read(0x0b14, 1)
        val = (quads[0] & 0x0000ff00) >> 8
        return self.SUPPORTED_SAMPLING_RATES_X4[val]

    def set_sampling_rate(self, rate):
        quads = self.read(0x0b14, 1)
        quads[0] &= ~0x0000ff00
        quads[0] |= self.SUPPORTED_SAMPLING_RATES_X4.index(rate) << 8
        self.write(0x0b14, quads)

    def get_supported_clock_sources(self):
        sources = [
            self.CLOCK_INTERNAL,
            self.CLOCK_WORD_ON_BNC,
        ]

        flag = False
        mode = self.get_opt_iface_mode('in', 'A')
        if mode == 'ADAT':
            sources.append(self.CLOCK_ADAT_ON_OPT_A)
            flag = True
        elif mode == 'S/PDIF':
            sources.append(self.CLOCK_SPDIF_ON_OPT_A)

        mode = self.get_opt_iface_mode('in', 'B')
        if mode == 'ADAT':
            sources.append(self.CLOCK_ADAT_ON_OPT_B)
            flag = True
        elif mode == 'S/PDIF':
            sources.append(self.CLOCK_SPDIF_ON_OPT_B)

        if not flag:
            sources.append(self.CLOCK_SPDIF_ON_COAX)

        return sources

    def get_clock_source(self):
        quads = self.read(0x0b14, 1)

        # TODO:
        val = quads[0] & 0x000000ff
        if val == 0x00:
            return self.CLOCK_INTERNAL

    def set_clock_source(self, source):
        quads = self.read(0x0b14, 1)

        # TODO:
        quads[0] &= ~0x0000000f
        if source == self.CLOCK_INTERNAL:
            pass

        self.write(0x0b14, quads)

    # kind/direction/index/mask/shift
    OPT_IFACE_MODE_ATTRS = {
        'enabled': {
            'in': {
                'A': (0x00000001, 0),
                'B': (0x00000002, 1),
            },
            'out': {
                'A': (0x00000100, 8),
                'B': (0x00000200, 9),
            }
        },
        'no-adat': {
            'in': {
                'A': (0x00010000, 16),
                'B': (0x00100000, 20),
            },
            'out': {
                'A': (0x00040000, 18),
                'B': (0x00400000, 22),
            }
        },
    }

    def get_supported_opt_iface_indexes(self):
        return self.SUPPORTED_OPT_IFACE_INDEXES

    def get_opt_iface_mode(self, direction, index):
        quads = self.read(0x0c94, 1)

        mask, shift = self.OPT_IFACE_MODE_ATTRS['enabled'][direction][index]
        if (quads[0] & mask) >> shift:
            # Enabled.
            mask, shift = self.OPT_IFACE_MODE_ATTRS['no-adat'][direction][index]
            if (quads[0] & mask) >> shift:
                # S/PDIF
                idx = 1
            else:
                idx = 2
        else:
            # Disabled.
            idx = 0

        return self.SUPPORTED_OPT_IFACE_MODES[idx]

    def set_opt_iface_mode(self, direction, index, mode):
        idx = self.SUPPORTED_OPT_IFACE_MODES.index(mode)
        quads = self.read(0x0c94, 1)

        mask, shift = self.OPT_IFACE_MODE_ATTRS['enabled'][direction][index]
        quads[0] &= ~mask
        if idx > 0:
            # Enabled.
            quads[0] |= mask

            mask, shift = self.OPT_IFACE_MODE_ATTRS['no-adat'][direction][index]
            quads[0] &= ~mask
            if idx == 1:
                # S/PDIF.
                quads[0] |= mask

        self.write(0x0c94, quads)
