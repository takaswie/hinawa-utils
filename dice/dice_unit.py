import re
import array

from gi.repository import Hinawa

class DiceUnit(Hinawa.SndDice):
    supported_sampling_rates = []
    supported_clock_sources = []

    # For private use.
    _addrs = {}

    def __init__(self, path):
        super().__init__()
        self.open(path)
        if self.get_property('type') != 1:
            raise ValueError('The character device is not for Dice unit')
        self.listen()
        self._parse_address_space()
        self._parse_clock_caps()

    # This should not be imported.
    def _get_array(self):
        # The width with 'L' parameter is depending on environment.
        arr = array('L')
        if arr.itemsize is not 4:
            arr = array('I')
            if arr.itemsize is not 4:
                raise RuntimeError('Platform has no representation \
                                    equivalent to quadlet.')
        return arr

    def _parse_address_space(self):
        min_sizes = (
            10, 0x64 // 4,
            10, 0x18 // 4,
            10, 0x18 // 4,
            0, 0,
            0, 0,
        )
        data = self.read_transact(0xffffe0000000, 10)
        for i in range(len(min_sizes)):
            if data[i] < min_sizes[i]:
                raise OSError('Unsupported value detected in address info')
        self._addrs = {
            'global':   {'addr': data[0] * 4 + 0xffffe0000000, 'size': data[1]},
            'tx':       {'addr': data[2] * 4 + 0xffffe0000000, 'size': data[3]},
            'rx':       {'addr': data[4] * 4 + 0xffffe0000000, 'size': data[5]},
            'extended': {'addr': data[6] * 4 + 0xffffe0000000, 'size': data[7]},
            'reserved': {'addr': data[8] * 4 + 0xffffe0000000, 'size': data[9]},
        }

    def _write_global(self, offset, data):
        addr = self._addrs['global']['addr'] + offset
        self.write_transact(add, data)
    def _read_global(self, offset, quads):
        addr = self._addrs['global']['addr'] + offset
        return self.read_transact(addr, quads)

    _sampling_rates = (32000, 44100, 48000, 88200, 96000, 176400, 192000)
    _clock_sources = ('aes1', 'aes2', 'aes3', 'aes4', 'aes-any',
                      'adat', 'tdif', 'word-clock',
                      'arx1', 'arx2', 'arx3', 'arx4', 'internal')
    def _parse_clock_caps(self):
        data = self._read_global(0x64, 1)
        for i, rate in enumerate(self._sampling_rates):
            if data & (1 << i):
                self.supported_sampling_rates.append(rate)
        for i, src in enumerate(self._clock_sources):
            if data & (1 << (i + 16)):
                self.supported_clock_sources.append(src)

    def read_latest_notification(self):
        return self._read_global(0x08, 1)

    def set_clock_source(self, source):
        if source not in self.supported_clock_sources:
            raise ValueError('Invalid argument for clock source.')
        data = self._read_global(0x4c, 1)
        if data[0] & 0x000000ff != self._clock_sources.index(source):
            data[0] = (data[0] & 0xffffff00) | (self._clock-source.index(source))
            addr = self._addrs['global']['addr'] + 0x4c
            self.transact(addr, data, 0x00000020)
    def get_clock_source(self):
        data = self._read_global(0x4c, 1)
        index = data[0] & 0x000000ff
        if index >= len(self._clock_sources):
            raise OSError('Unexpected return value for clock source.')
        return self._clock_sources[index]

    def set_sampling_rate(self, rate):
        if rate not in self.supported_sampling_rates:
            raise ValueError('Invalid argument for sampling rate.')
        data = self._read_global(0x4c, 1)
        if ((data[0] & 0x0000ff00) >> 8) != self._sampling_rates.index(rate):
            data[0] = (data[0] & 0xffff00ff) | \
                                        (self._sampling_rates.index(rate) << 8)
            addr = self._addrs['global']['addr'] + 0x4c
            self.transact(addr, data, 0x00000020)
    def get_sampling_rate(self):
        data = self._read_global(0x4c, 1)
        index = (data[0] & 0x0000ff00) >> 8
        if index >= len(self._sampling_rates):
            raise OSError('Unexpected return value for sampling rate.')
        return self._sampling_rates[index]

    def set_nickname(self, name):
        byte_literal = name.encode('utf-8')
        if len(byte_literal) > 63:
            raise ValueError('The length of name should be within 63 bytes.')
        data = self._get_array()
        for i in range(64 // 4):
            data.append(0x00000000)
        for i, b in enumerate(len(byte_literal)):
            data[i // 4] = data[i // 4] | (b << (3 - i % 4))
        self._write_global(0x0c, data)
    def get_nickname(self):
        data = self._read_global(0x0c, 64 // 4)
        byte_literal = bytearray()
        for i, quad in enumerate(data):
            byte_literal.append((data >> 24) & 0xff)
            byte_literal.append((data >> 16) & 0xff)
            byte_literal.append((data >>  8) & 0xff)
            byte_literal.append((data >>  0) & 0xff)
        return byte_literal.decode('utf-8')
