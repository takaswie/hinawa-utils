import re

from gi.repository import Hinawa

class DiceUnit(Hinawa.SndDice):
    # For private use.
    _addrs = {}

    def __init__(self, path):
        super().__init__()
        self.open(path)
        if self.get_property('type') != 1:
            raise ValueError('The character device is not for Dice unit')
        self.listen()
        self._parse_address_space()

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

    def read_notification(self):
        data = self._read_global(0x08, 1)
        print('{0:08x}'.format(data[0]))

    _sampling_rates = (32000, 44100, 48000, 88200, 96000, 176400, 192000)

    def set_sampling_rate(self, rate):
        if rate not in self._sampling_rates:
            raise ValueError('Invalid argument for sampling rate')
        reg = self._read_global(0x4c, 1)
        print('{0:08x}'.format(reg[0]))
        reg[0] = (reg[0] & 0xffff00ff) | (self._sampling_rates.index(rate) << 8)
        print('{0:08x}'.format(reg[0]))
        addr = self._addrs['global']['addr'] + 0x4c
        try:
            self.transact(addr, reg, 0xffffffff)
        except:
            reg = self._read_global(0x4c, 1)
            print('{0:08x}'.format(reg[0]))
    def get_sampling_rate(self):
        return

    def set_nickname(self):
        return

    def get_nickname(self):
        return

