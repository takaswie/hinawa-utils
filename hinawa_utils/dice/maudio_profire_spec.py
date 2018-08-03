# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.dice.tcat_tcd22xx_spec import TcatTcd22xxSpec

__all__ = ['MaudioProfireSpec']

class MaudioProfireSpec(TcatTcd22xxSpec):
    MODELS = (
        (0x000d6c, 0x000010),   # Profire 2626
        (0x000d6c, 0x000011),   # Profire 610
    )

    _INPUTS = (
        (
            ('Analog',   'ins0',    8),
            ('ADAT-A',   'adat',    8),
            ('ADAT-B',   'adat',    8),
            ('S/PDIF',   'aes',     2),
        ),
        (
            ('Analog',   'ins0',    4),
            ('S/PDIF',   'aes',     2),
        ),
    )

    _OUTPUTS = (
        (
            ('Analog',   'ins0',    8),
            ('ADAT-A',   'adat',    8),
            ('ADAT-B',   'adat',    8),
            ('S/PDIF',   'aes',     2),
        ),
        (
            ('Analog',   'ins0',    8),
            ('S/PDIF',   'aes',     2),
        ),
    )

    _FIXED = (
        {},
        {
            0: ('src',  'ins0', 0),
            1: ('src',  'ins0', 1),
        },
    )
