# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.ieee1394.config_rom_parser import Ieee1394ConfigRomParser

__all__ = ['FFConfigRomParser']

class FFConfigRomParser(Ieee1394ConfigRomParser):
    def parse_rom(self, data):
        entries = super().parse_rom(data)
        return self.__parse_entries(entries['root-directory'])

    def __parse_entries(self, entries):
        info = {}

        if (entries[0] != ['VENDOR', 0x000a35] or
                entries[1][0] != 'NODE_CAPABILITIES' or
                entries[2][0] != 'EUI_64' or
                entries[3][0] != 'UNIT'):
            raise OSError('Invalid format of config ROM.')

        unit_entries = entries[3][1]
        if (unit_entries[0] != ['SPECIFIER_ID', 0x000a35] or
                unit_entries[1][0] != 'VERSION' or
                unit_entries[2] != ['MODEL', 0x101800]):
            raise OSError('Invalid data of config ROM.')

        info['model_id'] = unit_entries[1][1]

        return info
