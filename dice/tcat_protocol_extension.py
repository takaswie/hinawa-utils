from struct import unpack

from dice.tcat_protocol_general import TcatProtocolGeneral

__all__ = ['ExtCtlSpace']

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
