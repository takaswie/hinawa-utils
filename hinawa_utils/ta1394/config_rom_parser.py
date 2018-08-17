# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.ieee1394.config_rom_parser import Ieee1394ConfigRomParser

__all__ = ['Ta1394ConfigRomParser']

# TA Document 1999027 Configuration ROM for AV/C Devices 1.0
# http://1394ta.org/specifications/
class Ta1394ConfigRomParser(Ieee1394ConfigRomParser):
    OUI_1394TA  = 0x00a02d
    VERSION_AVC = 0x010001

    def parse_rom(self, data):
        entries = super().parse_rom(data)
        return self._parse_entries(entries['root-directory'])

    def _parse_entries(self, entries):
        # Recommended layout.
        FIELDS = (
            ('VENDOR',              'vendor-id'),
            ('DESCRIPTOR',          'vendor-name'),
            ('MODEL',               'model-id'),
            ('DESCRIPTOR',          'model-name'),
            ('NODE_CAPABILITIES',   'node-capabilities'),
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
                if (entry[0][0] != 'SPECIFIER_ID' or
                    entry[1][0] != 'VERSION' or
                    entry[2] != ['MODEL',      info['model-id']] or
                    entry[3][0] != 'DESCRIPTOR'):
                    raise ValueError('Invalid data of config ROM.')
                info['spec-id'] = entry[0][1]
                info['spec-version'] = entry[1][1]
            else:
                info[alt] = entry[1]

        return info
