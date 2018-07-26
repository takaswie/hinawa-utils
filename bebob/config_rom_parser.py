from ieee1394.config_rom_parser import Ieee1394ConfigRomParser

__all__ = ['BebobConfigRomParser']

class BebobConfigRomParser(Ieee1394ConfigRomParser):
    def parse_rom(self, data):
        entries = super().parse_rom(data)
        return self._parse_entries(entries['root-directory'])

    def _parse_entries(self, entries):
        # Typical layout.
        FIELDS = (
            ('HARDWARE_VERSION',    'hardware-version'),
            ('NODE_CAPABILITIES',   'node-capabilities'),
            ('VENDOR',              'vendor-id'),
            ('DESCRIPTOR',          'vendor-name'),
            ('MODEL',               'model-id'),
            ('DESCRIPTOR',          'model-name'),
            ('VERSION',             'version'),
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
                if (entry[0] != ['SPECIFIER_ID', 0x00a02d] or
                    entry[1][0] != 'VERSION' or
                    entry[2] != ['MODEL', info['model-id']] or
                    entry[3] != ['DESCRIPTOR', info['model-name']]):
                    raise ValueError('Invalid data of unit directory.')
                info['unit-version'] = entry[1][1]
            else:
                info[alt] = entry[1]

        # All of units for BeBoB protocol don't have this directory.
        if entries[-1][0] == 'DEPENDENT_INFO':
            entries = entries[-1][1]
            if (entries[0][0] != 'SPECIFIER_ID' or
                entries[1][0] != 'VERSION' or
                entries[2][0][0] != 0x3a or
                entries[3][0][0] != 0x3b or
                entries[4][0][0] != 0x3c or
                entries[5][0][0] != 0x3d):
                raise ValueError('Invalid data of dependent information.')
            info['addrs'] = [
                (entries[2][1] << 32) + entries[3][1],
                (entries[4][1] << 32) + entries[5][1],
            ]

        return info
