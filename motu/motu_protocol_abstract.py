from abc import ABCMeta, abstractmethod

__all__ = ['MotuProtocolAbstract']

class MotuProtocolAbstract(metaclass=ABCMeta):
    BASE_ADDR = 0xfffff0000000

    SUPPORTED_SAMPLING_RATES_X1 = (44100, 48000)
    SUPPORTED_SAMPLING_RATES_X2 = (44100, 48000, 88200, 96000)
    SUPPORTED_SAMPLING_RATES_X4 = (44100, 48000, 88200, 96000, 176400, 192000)
    SUPPORTED_OPT_IFACE_MODES = ('None', 'S/PDIF', 'ADAT')
    SUPPORTED_OPT_IFACE_DIRECTIONS = ('in', 'out')
    SUPPORTED_OPT_IFACE_INDEXES = ('A', 'B')

    CLOCK_INTERNAL        = 'Internal'
    CLOCK_ADAT_ON_DSUB    = 'ADAT on Dsub-9pin interface'
    CLOCK_ADAT_ON_OPT     = 'ADAT on optical interface'
    CLOCK_ADAT_ON_OPT_A   = 'ADAT on optical interface A'
    CLOCK_ADAT_ON_OPT_B   = 'ADAT on optical interface B'
    CLOCK_SPDIF_ON_COAX   = 'S/PDIF on coaxial interface'
    CLOCK_SPDIF_ON_OPT    = 'S/PDIF on optical interface'
    CLOCK_SPDIF_ON_OPT_A  = 'S/PDIF on optical interface A'
    CLOCK_SPDIF_ON_OPT_B  = 'S/PDIF on optical interface B'
    CLOCK_AESEBU_XLR      = 'AES/EBU on XLR interface'
    CLOCK_WORD_ON_BNC     = 'Word clock on BNC interface'

    def __init__(self, unit, debug):
        self._unit = unit
        self._debug = bool(debug)

    def read(self, offset, count):
        addr = self.BASE_ADDR + offset
        quads = self._unit.read_transact(addr, count)
        if self._debug:
            print('    read: {0:012x}:'.format(addr))
            for i, quad in enumerate(quads):
                print('        {0:04x}: {1:08x}'.format(offset + i * 4, quad))
        return quads

    def write(self, offset, quads):
        addr = self.BASE_ADDR + offset
        if self._debug:
            print('    write: {0:012x}:'.format(addr))
            for i, quad in enumerate(quads):
                print('        {0:04x}: {1:08x}'.format(offset + i * 4, quad))

        self._unit.write_transact(addr, quads)

    @abstractmethod
    def get_supported_sampling_rates(self):
        pass
    @abstractmethod
    def get_sampling_rate(self):
        pass
    @abstractmethod
    def set_sampling_rate(self, rate):
        pass

    @abstractmethod
    def get_supported_clock_sources(self):
        pass
    @abstractmethod
    def get_clock_source(self):
        pass
    @abstractmethod
    def set_clock_source(self, source):
        pass

    def get_supported_opt_iface_modes(self):
        return self.SUPPORTED_OPT_IFACE_MODES
    def get_supported_opt_iface_directions(self):
        return self.SUPPORTED_OPT_IFACE_DIRECTIONS
    @abstractmethod
    def get_supported_opt_iface_indexes(self):
        pass
    @abstractmethod
    def get_opt_iface_mode(self, direction, index):
        pass
    @abstractmethod
    def set_opt_iface_mode(self, direction, index, mode):
        pass
