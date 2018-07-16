from ieee1394.config_rom import Ieee1394ConfigRom

__all__ = ['EfwConfigRom']

class EfwConfigRom(Ieee1394ConfigRom):
    _ECHOAUDIO_ENTRY_DEFS = {
        0x08: ('ECHOAUDIO-ENTRY', (0x00, )),
    };

    def __init__(self):
        super().__init__(None, self._ECHOAUDIO_ENTRY_DEFS)

    def _handle_oui(self, info, value):
        _OUI_COMPANIES = {
            0x000ff2: 'Loud Technologies Inc.',
            0x001486: 'Echo Digital Audio Corporation',
        }
        if value in _OUI_COMPANIES:
            info['manufacturer'] = _OUI_COMPANIES[value]

    def _handle_unit(self, info, entries):
        # 4 entries in this unit.
        for entry in entries:
            key, type, value = entry
            if key == 'specifier-id':
                if type != 'immediate' or value != 0x00a02d:
                    raise OSError('Unsupported value for specifier-id: {0}'.format(value))
            elif key == 'version':
                if type != 'immediate' or value != 0x010000:
                    raise OSError('Unsupported value for version: {0}'.format(value))
            elif key == 'model':
                if (type == 'immediate' and value != info['model-id'] or
                    type == 'leaf' and value != info['model-name']):
                    raise OSError('Unsupported value for model: {0}'.format(value))
            else:
                raise OSError('Unsupported entry: {0},{1}'.format(name, type))

    def parse_root_directory(self, rom):
        PARSERS = (
            ('vendor', 'immediate', 'vendor-id', None),
            ('vendor', 'leaf', 'vendor-name', None),
            ('model', 'immediate', 'model-id', None),
            ('model', 'leaf', 'model-name', None),
            ('node-capabilities', 'immediate', 'node-capabilities', None),
            ('eui-64', 'immediate', 'eui-64', None),
            ('unit', 'directory', None, self._handle_unit),
            ('ECHOAUDIO-ENTRY', 'immediate', None, self._handle_oui),
        )
        info = {}

        entries = self.get_root_directory(rom)
        for entry in entries:
            for parser in PARSERS:
                key, type, label, handler = parser
                if entry[0] == key and entry[1] == type:
                    if label:
                        info[label] = entry[2]
                    else:
                        handler(info, entry[2])

        return info
