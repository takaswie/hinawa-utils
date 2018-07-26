from ieee1394.config_rom_parser import Ieee1394ConfigRomParser

__all__ = ['TscmConfigRomParser']

class TscmConfigRomParser(Ieee1394ConfigRomParser):
    _OUI = 0x00022e

    def __init__(self):
        super().__init__()
        self.add_spec_dep_handle(self._OUI, 0x800004, self._handle_teac_keys)

    def _handle_teac_keys(self, key_id, type_name, data):
        if key_id == 0x02 and type_name == 'LEAF':
            content = data[8:].decode('US-ASCII') + '\0'
            return ['MODEL_NAME', content[:content.find('\0')]]
        return None

    def parse_rom(self, data):
        entries = super().parse_rom(data)
        return self._parse_entries(entries['root-directory'])

    def _parse_entries(self, entries):
        # Typical layout.
        FIELDS = (
            ('VENDOR',              'vendor-id'),
            ('NODE_CAPABILITIES',   'node-capabilities'),
            ('EUI_64',              'guid'),
            ('UNIT',                None),
        )
        info = {}

        for i, field in enumerate(FIELDS):
            entry = entries[i]
            name, alt = field
            if entry[0] != name:
                raise OSError('Invalid format of config ROM.')
            if name == 'UNIT':
                # Check unit.
                entry = entry[1]
                if (entry[0] != ['SPECIFIER_ID', self._OUI] or
                    entry[1][0] != 'VERSION' or
                    entry[2][0] != 'DEPENDENT_INFO'):
                    raise ValueError('Invalid data in unit directory.')
                info['model-version'] = entry[1][1]

                entry = entry[2][1]
                if (entry[0][0] != 'DESCRIPTOR' or
                    entry[1][0] != 'MODEL_NAME'):
                    raise ValueError('Invalid data in dependent info directory.')
                info['vendor-name'] = entry[0][1]
                info['model-name'] = entry[1][1]
            else:
                info[alt] = entry[1]

        return info
