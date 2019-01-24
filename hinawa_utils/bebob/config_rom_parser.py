# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.ieee1394.config_rom_parser import Ieee1394ConfigRomParser

__all__ = ['BebobConfigRomParser']


class BebobConfigRomParser(Ieee1394ConfigRomParser):
    def parse_rom(self, data):
        entries = super().parse_rom(data)
        return self.__parse_entries(entries['root-directory'])

    def __parse_entries(self, entries):
        # Typical layout.
        FIELDS = (
            ('HARDWARE_VERSION',    'hardware-version'),
            ('NODE_CAPABILITIES',   'node-capabilities'),
            ('VENDOR',              'vendor-id'),
            ('DESCRIPTOR',          'vendor-name'),
            ('MODEL',               'model-id'),
            ('DESCRIPTOR',          'model-name'),
            # There are entries of VERSION, UNIT and VENDOR_DEPENDENT keys, but
            # model-specific.
        )
        info = {}

        for i, entry in enumerate(entries):
            if i < len(FIELDS):
                name, alt = FIELDS[i]
                if entry[0] != name:
                    raise OSError('Invalid format of config ROM.')
                info[alt] = entry[1]
            elif entry[0] == 'VERSION':
                info['version'] = entry[1]
            elif entry[0] == 'UNIT':
                items = entry[1]
                # Check unit.
                if (items[0] != ['SPECIFIER_ID', 0x00a02d] or
                        items[1][0] != 'VERSION' or
                        items[2] != ['MODEL', info['model-id']] or
                        items[3] != ['DESCRIPTOR', info['model-name']]):
                    raise ValueError('Invalid data of unit directory.')
                info['unit-version'] = items[1][1]
            elif entry[0] == 'DEPENDENT_INFO':
                items = entry[1]
                if (items[0][0] != 'SPECIFIER_ID' or
                        items[1][0] != 'VERSION' or
                        items[2][0][0] != 0x3a or
                        items[3][0][0] != 0x3b or
                        items[4][0][0] != 0x3c or
                        items[5][0][0] != 0x3d):
                    raise ValueError('Invalid data of dependent information.')
                info['addrs'] = [
                    (items[2][1] << 32) + items[3][1],
                    (items[4][1] << 32) + items[5][1],
                ]

        return info
