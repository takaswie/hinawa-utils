from ieee1394.config_rom_parser import Ieee1394ConfigRomParser

__all__ = ['MotuConfigRomParser']

class MotuConfigRomParser(Ieee1394ConfigRomParser):
    def parse_rom(self, data):
        entries = super().parse_rom(data)
        return self._parse_entries(entries['root-directory'])

    def _parse_entries(self, entries):
        FIELDS = (
            ('VENDOR',              'vendor-id'),
            ('NODE_CAPABILITIES',   'node-capabilities'),
            ('UNIT',                None),
            ('EUI_64',              'guid'),
        )
        info = {}

        for i, field in enumerate(FIELDS):
            entry = entries[i]
            name, alt = field
            if entry[0] != name:
                raise OSError('Invalid format of config ROM.')
            if name == 'UNIT':
                entry = entry[1]
                if (entry[0] != ['SPECIFIER_ID', 0x0001f2] or
                    entry[1][0] != 'VERSION' or
                    entry[2][0] != 'MODEL'):
                    raise ValueError('Invalid data of unit directory.')
                info['version'] = entry[1][1]
                info['model-id'] = entry[2][1]
            else:
                info[alt] = entry[1]

        return info
