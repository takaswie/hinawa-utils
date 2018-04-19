from struct import pack, unpack
from array import array

__all__ = ['TcatProtocolGeneral']

class TcatProtocolGeneral():
    _BASE_ADDR = 0xffffe0000000
    _MAXIMUM_TRX_LENGTH = 512
    RATE_BITS = {
        0x00:   32000,
        0x01:   44100,
        0x02:   48000,
        0x03:   88200,
        0x04:   96000,
        0x05:   176400,
        0x06:   192000,
    }
    _EXT_RATE_BITS = {
        0x07:   48000,
        0x08:   96000,
        0x09:   192000,
    }
    CLOCK_BITS = {
        0x00:   'aes1',
        0x01:   'aes2',
        0x02:   'aes3',
        0x03:   'aes4',
        0x04:   'aes-any',
        0x05:   'adat',
        0x06:   'tdif',
        0x07:   'word-clock',
        0x08:   'arx1',
        0x09:   'arx2',
        0x0a:   'arx3',
        0x0b:   'arx4',
        0x0c:   'internal',
    }

    def __init__(self, unit, req):
        self._unit = unit

        self._general_layout = self._detect_address_space(req)
        self._version = self._parse_dice_version(req)
        self._clock_source_labels = self._parse_clock_source_names(req)
        self._sampling_rates, self._clock_sources = self._parse_clock_caps(req)

    def _write_transactions(self, req, offset, data):
        quads = array('I')

        addr = self._BASE_ADDR + offset

        for i in range(0, len(data), 4):
            quads.append(unpack('>I', data[i:i + 4])[0])

        while len(quads) > 0:
            quad_count = len(quads)
            if quad_count >= self._MAXIMUM_TRX_LENGTH // 4:
                quad_count = self._MAXIMUM_TRX_LENGTH // 4
            req.write(self._unit, addr, quads[0:quad_count])
            quads = quads[quad_count:]
            addr += quad_count * 4

    def _read_transactions(self, req, offset, length):
        data = bytearray()

        addr = self._BASE_ADDR + offset

        while len(data) < length:
            quad_count = (length - len(data)) // 4
            if quad_count >= self._MAXIMUM_TRX_LENGTH // 4:
                quad_count = self._MAXIMUM_TRX_LENGTH // 4
            quads = req.read(self._unit, addr, quad_count)
            for quad in quads:
                data.extend(pack('>I', quad))
            addr += quad_count * 4

        return data

    def _read_section_offset(self, req, section, offset, length):
        offset += self._general_layout[section]['offset']
        return self._read_transactions(req, offset, length)

    def _write_section_offset(self, req, section, offset, data):
        offset += self._general_layout[section]['offset']
        self._write_transactions(req, offset, data)

    def _detect_address_space(self, req):
        PARAMS = (
            ('global',  40, 0x60),
            ('tx',      40, 0x18),
            ('rx',      40, 0x18),
            ('external', 0, 0),
            ('reserved', 0, 0),
        )
        layout = {}

        data = self._read_transactions(req, 0, len(PARAMS) * 8)
        for i, param in enumerate(PARAMS):
            offset = unpack('>I', data[0:4])[0] * 4
            count = unpack('>I', data[4:8])[0] * 4
            data = data[8:]
            if offset >= param[1] or count >= param[2]:
                layout[param[0]] = {
                    'offset':   offset,
                    'length':   count,
                }
        return layout

    def _parse_string_bytes(self, data):
        letters = bytearray()

        for i in range(0, len(data), 4):
            letters.extend(list(reversed(data[0:4])))
            data = data[4:]

        return letters.decode('utf-8').rstrip('\0')

    # GLOBAL_OWNER: global:0x00
    def read_owner_addr(self, req):
        data = self._read_section_offset(req, 'global', 0x00, 8)
        return (unpack('>I', data[0:4])[0] << 32) | unpack('>I', data[4:8])[0]

    # GLOBAL_NOTIFICATION: global:0x08
    def read_latest_notification(self, req):
        data = self._read_section_offset(req, 'global', 0x08, 4)
        return unpack('>I', data)[0]

    # GLOBAL_NICKNAME: global:0x0c
    def write_nickname(self, req, name):
        letters = bytearray(name.encode('utf-8'))
        if len(letters) > 63:
            raise ValueError('The length of name should be within 63 bytes.')
        for i in range(64 - len(letters)):
            letters.append(0x00)

        data = bytearray()
        for i in range(0, len(letters), 4):
            data.extend(list(reversed(letters[0:4])))
            letters = letters[4:]

        self._write_section_offset(req, 'global', 0x0c, data)

    def read_nickname(self, req):
        data = self._read_section_offset(req, 'global', 0x0c, 64)
        return self._parse_string_bytes(data).rstrip()

    def _clock_select_transaction(self, data):
        quads = array('I')
        quads.append(unpack('>I', data)[0])
        offset = self._general_layout['global']['offset'] + 0x4c
        self._unit.transact(self._BASE_ADDR + offset, quads, 0x00000020)

    # GLOBAL_CLOCK_SELECT: global:004c
    def get_supported_clock_sources(self):
        return self._clock_sources

    def write_clock_source(self, req, source):
        if source not in self._clock_sources:
            raise ValueError('Invalid argument for clock source.')
        val = {v: k for k, v in self.CLOCK_BITS.items()}[source]

        data = self._read_section_offset(req, 'global', 0x4c, 4)
        if data[3] != val:
            data[3] = val
            self._clock_select_transaction(data)

    def read_clock_source(self, req):
        data = self._read_section_offset(req, 'global', 0x4c, 4)
        val = data[3]
        if (val not in self.CLOCK_BITS or
                self._clock_source_labels[val] == 'Unused'):
            raise OSError('Unexpected return value for clock source.')

        return self.CLOCK_BITS[val]

    def get_supported_sampling_rates(self):
        return self._sampling_rates

    def write_sampling_rate(self, req, rate):
        for index, val in self.RATE_BITS.items():
            if rate == val:
                break
        else:
            for index, val in self._EXT_RATE_BITS.items():
                if rate < val:
                    break
            else:
                raise ValueError('Invalid argument for sampling rate.')

        data = self._read_section_offset(req, 'global', 0x4c, 4)
        if data[2] != index:
            data[2] = index
            self._clock_select_transaction(data)

    def read_sampling_rate(self, req):
        data = self._read_section_offset(req, 'global', 0x4c, 4)
        index = data[2]
        if index in self.RATE_BITS:
            return self.RATE_BITS[index]
        if index in self._EXT_RATE_BITS:
            return self._EXT_RATE_BITS[index]

        raise OSError('Unexpected return value for sampling rate.')

    # GLOBAL_ENABLE: global:0x50
    def read_enabled(self, req):
        data = self._read_section_offset(req, 'global', 0x50, 4)
        return bool(unpack('>I', data))

    # GLOBAL_STATUS: global:0x54
    def read_clock_status(self, req):
        status = {}

        data = self._read_section_offset(req, 'global', 0x54, 4)
        status['locked'] = bool(data[3])
        status['rate'] = self.RATE_BITS[data[2]]

        return status

    # GLOBAL_EXTENDED_STATUS: global 0x58
    def read_external_clock_states(self, req):
        CLOCK_BITS = {
            0x0001: 'aes1',
            0x0002: 'aes2',
            0x0004: 'aes3',
            0x0008: 'aes4',
            0x0010: 'adat',
            0x0020: 'tdif',
            0x0040: 'arx1',
            0x0080: 'arx2',
            0x0100: 'arx3',
            0x0200: 'arx4',
            0x0400: 'word-clock',
        }
        status = {
            'locked':   [],
            'slipped':  [],
        }

        data = self._read_section_offset(req, 'global', 0x58, 4)

        slipped_mask = unpack('>H', data[0:2])[0]
        locked_mask = unpack('>H', data[2:4])[0]
        for bit, clk in CLOCK_BITS.items():
            if bit & slipped_mask:
                status['slipped'].append(clk)
            if bit & locked_mask:
                status['locked'].append(clk)
        return status

    # GLOBAL_SAMPLE_RATE: global:0x5c
    def read_measured_sampling_rate(self, req):
        data = self._read_section_offset(req, 'global', 0x5c, 4)
        return unpack('>I', data)[0]

    # GLOBAL_VERSION: global:0x60
    def _parse_dice_version(self, req):
        if self._general_layout['global']['length'] < 0x64:
            return '1.0.2'
        data = self._read_section_offset(req, 'global', 0x60, 4)
        return '{0}.{1}.{2}.{3}'.format(data[0], data[1], data[2], data[3])

    def get_dice_version(self):
        return self._version

    # GLOBAL_CLOCK_CAPABILITIES: global:0x64
    def _parse_clock_caps(self, req):
        rates = []
        clks = []

        if self._version == '1.0.2':
            return [44100, 48000], ['arx1', 'internal']

        data = self._read_section_offset(req, 'global', 0x64, 4)

        flags = unpack('>H', data[0:2])[0]
        for index, name in self.CLOCK_BITS.items():
            label = self._clock_source_labels[index]
            if (1 << index) & flags and label != 'Unused':
                clks.append(name)

        flags = unpack('>H', data[2:4])[0]
        for index, rate in self.RATE_BITS.items():
            if (1 << index) & flags:
                rates.append(rate)

        return rates, clks

    # GLOBAL_CLOCK_SOURCE_NAMES: global:0x68
    def _parse_clock_source_names(self, req):
        if self._version == '1.0.2':
            names = []
            for key, name in self.CLOCK_BITS.items():
                if name == 'arx1':
                    names.append('Firewire')
                elif name == 'internal':
                    names.append('Internal')
                else:
                    names.append('Unused')
            return names
        data = self._read_section_offset(req, 'global', 0x68, 256)
        return self._parse_string_bytes(data).split('\\')[0:-2]

    def get_clock_source_names(self):
        return self._clock_source_labels

    # TX stream settings.
    def read_tx_params(self, req):
        params = []
        data = self._read_section_offset(req, 'tx', 0x00, 8)
        count = unpack('>I', data[0:4])[0]
        length = unpack('>I', data[4:8])[0] * 4
        for i in range(count):
            offset = 0x08 + length * i
            data = self._read_section_offset(req, 'tx', offset, length)
            pcm_count = unpack('>I', data[4:8])[0]
            pcm_formation = self._parse_string_bytes(data[16:272])
            pcm_formation = pcm_formation.split('\\')[0:pcm_count]
            stream = {
                'iso-channel': unpack('>I', data[0:4])[0],
                'pcm':         pcm_count,
                'midi':        unpack('>I', data[8:12])[0],
                'speed':       unpack('>I', data[12:16])[0],
                'formation':   pcm_formation,
            }
            if length >= 280:
                stream['iec60958'] = {
                    'caps':    unpack('>I', data[272:276])[0],
                    'enable':  unpack('>I', data[276:280])[0],
                }
            params.append(stream)
        return params

    # RX stream settings.
    def read_rx_params(self, req):
        params = []
        data = self._read_section_offset(req, 'rx', 0x00, 8)
        count = unpack('>I', data[0:4])[0]
        length = unpack('>I', data[4:8])[0] * 4
        for i in range(count):
            offset = 0x08 + length * i
            data = self._read_section_offset(req, 'rx', offset, length)
            pcm_count = unpack('>I', data[8:12])[0]
            pcm_formation = self._parse_string_bytes(data[16:272])
            pcm_formation = pcm_formation.split('\\')[0:pcm_count]
            stream = {
                'iso-channel':  unpack('>I', data[0:4])[0],
                'start':        unpack('>I', data[4:8])[0],
                'pcm':          pcm_count,
                'midi':         unpack('>I', data[12:16])[0],
                'formation':    pcm_formation,
            }
            if length >= 280:
                stream['iec60958'] = {
                    'caps':    unpack('>I', data[272:276])[0],
                    'enable':  unpack('>I', data[276:280])[0],
                }
            params.append(stream)
        return params

    # External synchronization status.
    def read_external_sync_clock_source(self, req):
        if ('external' not in self._general_layout or
                self._general_layout['external']['length'] == 0):
            return ''
        data = self._read_section_offset(req, 'external', 0x00, 4)
        val = unpack('>I', data)[0]
        if (val not in self.CLOCK_BITS or
                self._clock_source_labels[val] == 'Unused'):
            raise OSError('Unexpected return value for clock source.')
        return self.CLOCK_BITS[val]

    def read_external_sync_locked(self, req):
        if ('external' not in self._general_layout or
                self._general_layout['external']['length'] == 0):
            return ''
        data = self._read_section_offset(req, 'external', 0x04, 4)
        val = unpack('>I', data)[0]
        return bool(val)

    def read_external_sync_rate(self, req):
        if ('external' not in self._general_layout or
                self._general_layout['external']['length'] == 0):
            return ''
        data = self._read_section_offset(req, 'external', 0x08, 4)
        val = unpack('>I', data)[0]
        if val not in self.RATE_BITS:
            raise OSError('Unexpected return value for sampling rate.')
        return self.RATE_BITS[val]

    def read_external_sync_adat_status(self, req):
        if ('external' not in self._general_layout or
                self._general_layout['external']['length'] == 0):
            return ''
        data = self._read_section_offset(req, 'external', 0x0c, 4)
        if not data[3] & 0x10:
            return 0
        return data[3] & 0xf
