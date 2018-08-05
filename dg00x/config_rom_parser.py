# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from struct import unpack

from ieee1394.config_rom_parser import Ieee1394ConfigRomParser

__all__ = ['Dg00xConfigRomParser']

class Dg00xConfigRomParser(Ieee1394ConfigRomParser):
    _OUI_MICROSOFT = 0x0050f2

    def __init__(self):
        super().__init__()
        self.add_vendor_dep_handle(self._OUI_MICROSOFT,
                                   self._handle_microsoft_keys)

    def _handle_microsoft_keys(self, key_id, type_name, data):
        if key_id == 0x01 and type_name == 'LEAF':
            width = data[0] >> 4
            character_set = ((data[0] & 0x0f) << 8) | data[1]
            language = unpack('>H', data[2:4])[0]

            if width != 0x00:
                raise OSError('Width {0} is not supported.'.format(width))

            if character_set != 0x00 or language != 0x00:
                raise ValueError('Invalid data in descriptor leaf.')

            content = data[4:].decode('US-ASCII') + '\0'
            return content[:content.find('\0')]

        return None

    def parse_rom(self, data):
        entries = super().parse_rom(data)
        return self._parse_entries(entries['root-directory'])

    def _parse_entries(self, entries):
        # Typical layout.
        FIELDS = (
            ('NODE_CAPABILITIES',   'node-capabilities'),
            ('HARDWARE_VERSION', 'hardware-version'),
            ('VENDOR', 'vendor-id'),
            ('DESCRIPTOR', 'vendor-name'),
            ('UNIT', None),
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
                    entry[2][0] != 'MODEL' or
                    entry[3][0] != 'DESCRIPTOR'):
                    raise ValueError('Invalid data in unit directory.')
                info['model-revision'] = entry[0][1]
                info['model-version'] = entry[1][1]
                info['model-id'] = entry[2][1]
                info['model-name'] = entry[3][1]
            else:
                info[alt] = entry[1]

        return info
