# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from ieee1394.config_rom_parser import Ieee1394ConfigRomParser

__all__ = ['EfwConfigRomParser']

class EfwConfigRomParser(Ieee1394ConfigRomParser):
    _OUI_ECHO = 0x001486
    _MANUFACTURER_OUI = {
        0x000ff2:   'Loud Technologies Inc.',
        _OUI_ECHO:  'Echo Digital Audio Corporation',
    }

    def __init__(self):
        super().__init__()
        self.add_vendor_dep_handle(self._OUI_ECHO, self._handle_echoaudio_keys)

    def _handle_echoaudio_keys(self, key_id, type_name, data):
        if key_id != 0x08 or type_name != 'IMMEDIATE':
            return None
        if data in self._MANUFACTURER_OUI:
            name = self._MANUFACTURER_OUI[data]
        else:
            name = data
        return ['MANUFACTURER', name]

    def parse_rom(self, data):
        entries = super().parse_rom(data)
        return self._parse_entries(entries['root-directory'])

    def _parse_entries(self, entries):
        # Typical layout.
        FIELDS = (
            ('VENDOR',              'vendor-id'),
            ('DESCRIPTOR',          'vendor-name'),
            ('MODEL',               'model-id'),
            ('DESCRIPTOR',          'model-name'),
            ('NODE_CAPABILITIES',   'node-capabilities'),
            ('EUI_64',              'guid'),
            ('UNIT',                None),
            ('MANUFACTURER',        'manufacturer'),
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
                    entry[1] != ['VERSION',      0x010000] or
                    entry[2] != ['MODEL',        info['model-id']] or
                    entry[3] != ['DESCRIPTOR',   info['model-name']]):
                    raise ValueError('Invalid data of config ROM.')
            else:
                info[alt] = entry[1]

        return info
