from struct import unpack
from time import sleep

from dice.tcat_protocol_general import TcatProtocolGeneral

__all__ = ['ExtCtlSpace', 'ExtCapsSpace', 'ExtCmdSpace']

# '3.1 External control private space'
class ExtCtlSpace():
    _EXT_OFFSET = 0x00200000

    _SECTIONS = {
        'caps':                 0x00,
        'cmd':                  0x08,
        'mixer':                0x10,
        'peak':                 0x18,
        'new-router':           0x20,
        'new-stream-config':    0x28,
        'current-config':       0x30,
        'standalone-config':    0x38,
        'application':          0x40,
    }

    @classmethod
    def write_section(cls, protocol, req, section, offset, data):
        if section not in cls._SECTIONS:
            raise ValueError('Invalid name of section: {0}'.format(section))
        offset += cls._EXT_OFFSET + protocol._ext_layout[section]['offset']
        return protocol._write_transactions(req, offset, data)

    @classmethod
    def read_section(cls, protocol, req, section, offset, length):
        if section not in cls._SECTIONS:
            raise ValueError('Invalid name of section: {0}'.format(section))
        offset += cls._EXT_OFFSET + protocol._ext_layout[section]['offset']
        return protocol._read_transactions(req, offset, length)

    @classmethod
    def detect_layout(cls, protocol, req):
        layout = {}

        data = protocol._read_transactions(req, cls._EXT_OFFSET,
                                           len(cls._SECTIONS) * 8)
        for name, offset in cls._SECTIONS.items():
            layout[name] = {
                'offset': unpack('>I', data[offset    : offset + 4])[0] * 4,
                'length': unpack('>I', data[offset + 4: offset + 8])[0] * 4,
            }

        protocol._ext_layout = layout
        return layout

# '3.2 Capability space'
class ExtCapsSpace():
    _OFFSET_ROUTER_CAPS     = 0x00
    _OFFSET_MIXER_CAPS      = 0x04
    _OFFSET_GENERAL_CAPS    = 0x08
    _OFFSET_RESERVED_CAPS   = 0x0c

    _ASIC_TYPES = {
        0x00: 'DICE-II',
        0x01: 'TCD-2210',
        0x02: 'TCD-2220',
        0x03: 'Unknown',
    }

    @classmethod
    def _parse_router_caps(cls, data):
        caps = {}

        data = data[cls._OFFSET_ROUTER_CAPS:]
        caps['is-exposed']  = bool(data[3] & 0x01)
        caps['is-readonly'] = bool(data[3] & 0x02)
        caps['is-storable'] = bool(data[3] & 0x04)
        caps['maximum-routes']  = unpack('>H', data[0:2])[0]

        return caps

    @classmethod
    def _parse_mixer_caps(cls, data):
        caps = {}

        data = data[cls._OFFSET_MIXER_CAPS:]
        caps['is-exposed']          = bool(data[3] & 0x01)
        caps['is-readonly']         = bool(data[3] & 0x02)
        caps['is-storable']         = bool(data[3] & 0x04)
        caps['input-device-id']     = (data[3] & 0xf0) >> 4
        caps['output-device-id']    = data[2] & 0x0f
        caps['input-channels']      = data[1]
        caps['output-channels']     = data[0]
        return caps

    @classmethod
    def _parse_general_caps(cls, data):
        caps = {}

        data = data[cls._OFFSET_GENERAL_CAPS:]
        caps['dynamic-stream-conf'] = bool(data[3] & 0x01)
        caps['storage-available']   = bool(data[3] & 0x02)
        caps['peak-available']      = bool(data[3] & 0x04)
        caps['maximum-tx-streams']  = (data[3] & 0xf0) >> 4
        caps['maximum-rx-streams']  = data[2] & 0x0f
        caps['storable-stream-conf']= bool(data[2] & 0x10)
        asic_type = data[1]
        if asic_type < len(cls._ASIC_TYPES) - 1:
            caps['asic-type'] = cls._ASIC_TYPES[asic_type]
        else:
            caps['asic-type'] = cls._ASIC_TYPES[-1]
        return caps

    @classmethod
    def detect_caps(cls, protocol, req):
        caps = {}

        length = protocol._ext_layout['caps']['length']
        data = ExtCtlSpace.read_section(protocol, req, 'caps', 0, length)

        caps['router']  = cls._parse_router_caps(data)
        caps['mixer']   = cls._parse_mixer_caps(data)
        caps['general'] = cls._parse_general_caps(data)
        caps['reserved'] = data[cls._OFFSET_RESERVED_CAPS:]

        protocol._ext_caps = caps

        return caps

# '3.3 Command space'
class ExtCmdSpace():
    _OFFSET_OPCODE = 0x0000
    _OFFSET_RETURN = 0x0004

    _EXECUTE_FLAG = 0x80

    _RETURN_SUCCESS = 0x00
    _RETURN_FAILURE = 0x01

    _OP_CODES = (
        'noop',
        'load-from-router',
        'load-from-stream-config',
        'load-from-router-stream-config',
        'load-from-storage',
        'load-to-storage',
    )

    _RATE_MODES = {
        'low':      0x01,
        'middle':   0x02,
        'high':     0x04,
    }

    @classmethod
    def initiate(cls, protocol, req, cmd, mode):
        if cmd not in cls._OP_CODES:
            raise ValueError('Invalid argument for command')
        if mode not in cls._RATE_MODES:
            raise ValueError('Invalid argument for rate mode')

        # Check feature capabilities.
        if ((cmd.find('router') > 0 and
                protocol._ext_caps['router']['is-readonly']) or
            (cmd.find('stream-config') > 0 and
                not protocol._ext_caps['general']['dynamic-stream-conf']) or
            (cmd in ('load-from-storage', 'load-to-storage' ) and
                not protocol._ext_caps['general']['storage-available'])):
            raise RuntimeError('This feature is not available.')

        data = bytearray(4)
        data[0] = cls._EXECUTE_FLAG
        data[1] = cls._RATE_MODES[mode]
        data[3] = cls._OP_CODES.index(cmd)

        ExtCtlSpace.write_section(protocol, req, 'cmd', cls._OFFSET_OPCODE, data)

        # Completion is notified as clearing of bit flags in the register.
        count = 10
        while count > 0:
            data = ExtCtlSpace.read_section(protocol, req, 'cmd',
                                            cls._OFFSET_OPCODE, 4)
            if not (data[0] & cls._EXECUTE_FLAG):
                break
            count -= 1
            sleep(0.2)
        else:
            raise IOError('Timeout of command initiation.')

        data = ExtCtlSpace.read_section(protocol, req, 'cmd',
                                        cls._OFFSET_RETURN, 4)
        if data[3] != cls._RETURN_SUCCESS:
            raise IOError('Fail to execute requested operation.')
