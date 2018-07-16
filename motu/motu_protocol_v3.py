from motu.motu_protocol_abstract import MotuProtocolAbstract

__all__ = ['MotuProtocolV3']

class MotuProtocolV3(MotuProtocolAbstract):
    def get_supported_sampling_rates(self):
        return self.SUPPORTED_SAMPLING_RATES_X4

    def get_sampling_rate(self):
        frames = self.read(0x0b14, 4)
        val = frames[2]
        return self.SUPPORTED_SAMPLING_RATES_X4[val]

    def set_sampling_rate(self, rate):
        frames = self.read(0x0b14, 4)
        frames[2] = self.SUPPORTED_SAMPLING_RATES_X4.index(rate)
        self.write(0x0b14, frames)

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
        frames = self.read(0x0b14, 4)

        # TODO:
        if frames[3] == 0x00:
            return self.CLOCK_INTERNAL

    def set_clock_source(self, source):
        frames = self.read(0x0b14, 4)

        # TODO:
        frames[3] &= ~0x0f
        if source == self.CLOCK_INTERNAL:
            pass

        self.write(0x0b14, frames)

    # kind/direction/index/mask/shift
    OPT_IFACE_MODE_ATTRS = {
        'enabled': {
            'in': {
                # label: (pos, shift)
                'A': (3, 0),
                'B': (3, 1),
            },
            'out': {
                'A': (2, 0),
                'B': (2, 1),
            }
        },
        'no-adat': {
            'in': {
                'A': (1, 0),
                'B': (1, 4),
            },
            'out': {
                'A': (1, 2),
                'B': (1, 6),
            }
        },
    }

    def get_supported_opt_iface_indexes(self):
        return self.SUPPORTED_OPT_IFACE_INDEXES

    def get_opt_iface_mode(self, direction, index):
        frames = self.read(0x0c94, 4)

        pos, shift = self.OPT_IFACE_MODE_ATTRS['enabled'][direction][index]
        if frames[pos] & (1 << shift):
            # Enabled.
            pos, shift = self.OPT_IFACE_MODE_ATTRS['no-adat'][direction][index]
            if frames[pos] & (1 << shift):
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
        frames = self.read(0x0c94, 4)

        pos, shift = self.OPT_IFACE_MODE_ATTRS['enabled'][direction][index]
        frames[pos] & ~(1 << shift)
        if idx > 0:
            # Enabled.
            frames[pos] |= 1 << shift

            pos, shift = self.OPT_IFACE_MODE_ATTRS['no-adat'][direction][index]
            frames[pos] &= ~(1 << shift)
            if idx == 1:
                # S/PDIF.
                frames[pos] |= 1 << shift

        self.write(0x0c94, frames)
