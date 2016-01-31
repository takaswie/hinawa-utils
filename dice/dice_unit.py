import re
from array import array

from gi.repository import Hinawa

class DiceUnit(Hinawa.SndDice):
    def __init__(self, path):
        super().__init__()
        self.open(path)
        if self.get_property('type') != 1:
            raise ValueError('The character device is not for Dice unit')
        self.listen()
        self._addrs = self._parse_address_space()
        self.supported_sampling_rates = []
        self.supported_clock_sources = []
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
        return {
            'global':   {'addr': data[0] * 4 + 0xffffe0000000, 'size': data[1]},
            'tx':       {'addr': data[2] * 4 + 0xffffe0000000, 'size': data[3]},
            'rx':       {'addr': data[4] * 4 + 0xffffe0000000, 'size': data[5]},
            'extended': {'addr': data[6] * 4 + 0xffffe0000000, 'size': data[7]},
            'reserved': {'addr': data[8] * 4 + 0xffffe0000000, 'size': data[9]},
        }

    def write_global(self, offset, data):
        addr = self._addrs['global']['addr'] + offset
        self.write_transact(addr, data)
    def read_global(self, offset, quads):
        addr = self._addrs['global']['addr'] + offset
        return self.read_transact(addr, quads)

    def read_tx(self, offset, quads):
        addr = self._addrs['tx']['addr'] + offset
        return self.read_transact(addr, quads)
    def read_rx(self, offset, quads):
        addr = self._addrs['rx']['addr'] + offset
        return self.read_transact(addr, quads)
    def read_extended(self, offset, quads):
        addr = self._addrs['extended']['addr'] + offset
        return self.read_transact(addr, quads)

    def read_owner_addr(self):
        data = self.read_global(0x00, 2)
        return (data[0] << 32) | data[1]

    def read_enabled(self):
        data = self.read_global(0x50, 1)
        return data[0] == 1

    _sampling_rates = (32000, 44100, 48000, 88200, 96000, 176400, 192000)
    _clock_sources = []
    def read_clock_status(self):
        status = {}
        data = self.read_global(0x54, 1)
        status['locked'] = data[0] & 0x00000001
        index = (data[0] >> 8) & 0xff
        if index >= len(self._sampling_rates):
            raise OSError('Unexpected value for sampling rate.')
        status['nominal'] = self._sampling_rates[index]
        return status

    def read_clock_detection(self):
        # TODO: ?
        labels = (
            'aes1', 'aes2', 'aes3', 'aes4',
            'adat', 'tdif',
            'arx1', 'arx2', 'arx3', 'arx4',
            'word-clock'
        )
        detection = {}
        data = self.read_global(0x58, 1)
        detection['locked'] = []
        detection['slip'] = []
        for i, label in enumerate(labels):
            if data[0] & (1 << i):
                detection['locked'].append(label)
            if data[0] & (1 << (i + 16)):
                detection['slip'].append(label)
        return detection

    def read_measured_rate(self):
        data = self.read_global(0x5c, 1)
        return data[0]

    def read_dice_version(self):
        data = self.read_global(0x60, 1)
        return '{0}.{1}.{2}.{3}'.format((data[0] >> 24) & 0xff,
                                        (data[0] >> 16) & 0xff,
                                        (data[0] >>  8) & 0xff,
                                        (data[0] >>  0) & 0xff)

    def _parse_clock_source_labels(self):
        byte_literal = bytearray()
        data = self.read_global(0x68, 256//4)
        for i, datum in enumerate(data):
            byte_literal.append((datum >>  0) & 0xff)
            byte_literal.append((datum >>  8) & 0xff)
            byte_literal.append((datum >> 16) & 0xff)
            byte_literal.append((datum >> 24) & 0xff)
        string_literal = byte_literal.decode('utf-8').replace(' ', '-')
        labels = string_literal.split('\\')
        del labels[-1]  # drop members with multiple 0x00.
        del labels[-1]  # drop member with ''
        return labels

    def _parse_clock_caps(self):
        data = self.read_global(0x64, 1)
        for i, rate in enumerate(self._sampling_rates):
            if data[0] & (1 << i):
                self.supported_sampling_rates.append(rate)
        self._clock_sources = self._parse_clock_source_labels()
        for i, src in enumerate(self._clock_sources):
            if data[0] & (1 << (i + 16)) and src != 'Unused':
                self.supported_clock_sources.append(src)

    def get_latest_notification(self):
        return self.read_global(0x08, 1)[0]

    def set_clock_source(self, source):
        if source not in self.supported_clock_sources:
            raise ValueError('Invalid argument for clock source.')
        data = self.read_global(0x4c, 1)
        if data[0] & 0x000000ff != self._clock_sources.index(source):
            data[0] = (data[0] & 0xffffff00) | (self._clock-source.index(source))
            addr = self._addrs['global']['addr'] + 0x4c
            self.transact(addr, data, 0x00000020)
    def get_clock_source(self):
        data = self.read_global(0x4c, 1)
        index = data[0] & 0x000000ff
        if index >= len(self._clock_sources):
            raise OSError('Unexpected return value for clock source.')
        return self._clock_sources[index]

    def set_sampling_rate(self, rate):
        if rate not in self.supported_sampling_rates:
            raise ValueError('Invalid argument for sampling rate.')
        data = self.read_global(0x4c, 1)
        if ((data[0] & 0x0000ff00) >> 8) != self._sampling_rates.index(rate):
            data[0] = (data[0] & 0xffff00ff) | \
                                        (self._sampling_rates.index(rate) << 8)
            addr = self._addrs['global']['addr'] + 0x4c
            self.transact(addr, data, 0x00000020)
    def get_sampling_rate(self):
        data = self.read_global(0x4c, 1)
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
        for i, b in enumerate(byte_literal):
            data[i // 4] = data[i // 4] | (b << ((i % 4) * 8))
        self.write_global(0x0c, data)
    def get_nickname(self):
        data = self.read_global(0x0c, 64 // 4)
        byte_literal = bytearray()
        for i, quad in enumerate(data):
            byte_literal.append((data[i] >>  0) & 0xff)
            byte_literal.append((data[i] >>  8) & 0xff)
            byte_literal.append((data[i] >> 16) & 0xff)
            byte_literal.append((data[i] >> 24) & 0xff)
        return byte_literal.decode('utf-8')

    def _parse_stream_names(self, quads):
        names = []
        byte_literal = bytearray()
        for i, quad in enumerate(quads):
            byte_literal.append((quad >>  0) & 0xff)
            byte_literal.append((quad >>  8) & 0xff)
            byte_literal.append((quad >> 16) & 0xff)
            byte_literal.append((quad >> 24) & 0xff)
        names_literal = byte_literal.decode('utf-8')
        names = names_literal.split('\\')
        del names[-1]
        del names[-1]
        return names

    def get_tx_params(self):
        params = []
        data = self.read_tx(0x00, 1)
        count = data[0]
        offset = 0
        for i in range(count):
            data = self.read_tx(offset + 0x04, 1)
            size = data[0]
            data = self.read_tx(offset + 0x08, size)
            stream = {'iso-channel':  data[0],
                      'pcm':          data[1],
                      'midi':         data[2],
                      'speed':        data[3],
                      'formation':    self._parse_stream_names(data[4:-3]),
                      'iec60958':     {'caps':      data[-2],
                                       'enable':    data[-1]}}
            offset = size
            params.append(stream)
        return params

    def get_rx_params(self):
        params = []
        data = self.read_rx(0x00, 1)
        count = data[0]
        offset = 0
        for i in range(count):
            data = self.read_rx(offset + 0x04, 1)
            size = data[0]
            data = self.read_rx(offset + 0x08, size)
            stream = {'iso-channel': data[0],
                      'start':       data[1],
                      'pcm':         data[2],
                      'midi':        data[3],
                      'formation':   self._parse_stream_names(data[4:-3]),
                      'iec60958':    {'caps':       data[-2],
                                      'enable':     data[-1]}}
            params.append(stream)
        return params

    def get_sync_info(self):
        info = {}
        if self._addrs['extended']['size'] == 0:
            return info
        data = self.read_extended(0, self._addrs['extended']['size'])
        index = data[0] & 0xff
        if index >= len(self._clock_sources):
            raise ValueError('Unexpected value for clock source.')
        info['clock-source'] = self._clock_sources[index]
        info['locked'] = data[1] & 0xff
        index = data[2] & 0xff
        if index >= len(self._sampling_rates):
            raise ValueError('Unexpected value for sampling rate.')
        info['sampling-rate'] = self._sampling_rates[index]
        info['adat'] = {'data-bits': data[3] & 0x0f,
                        'no-data': (data[3] >> 4) & 0x01}
        return info
