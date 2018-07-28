from dice.tcat_tcd22xx_spec import TcatTcd22xxSpec

__all__ = ['FocusriteSaffireproSpec']

class FocusriteSaffireproSpec(TcatTcd22xxSpec):
    MODELS = (
        (0x00130e, 0x000007),   # Saffire Pro 24
        (0x00130e, 0x000008),   # Saffire Pro 24 DSP
        (0x00130e, 0x000009),   # Saffire Pro 14
        (0x00130e, 0x000012),   # Saffire Pro 26
        (0x00130e, 0x000006),   # Saffire 56
        (0x00130e, 0x000005),   # Saffire Pro 40
        (0x00130e, 0x000013),   # Saffire Pro 40 (variant1)
        (0x00130e, 0x0000de),   # Saffire Pro 40 (variant2)
    )

    _INPUTS = (
        (
            ('Analog',  'ins0', 4),
            ('S/PDIF',  'aes',  2),
            ('ADAT',    'adat', 8),
        ),
        (
            ('Analog',  'ins0', 4),
            ('S/PDIF',  'aes',  2),
            ('ADAT',    'adat', 8),
        ),
        (
            ('Analog',  'ins0', 4),
            ('S/PDIF',  'aes',  2),
        ),
        (
            ('Analog',      'ins0', 6),
            ('S/PDIF-coax', 'aes',  2),
            ('S/PDIF-opt',  'aes',  2),
            ('ADAT',        'adat', 8),
        ),
        (),
        (),
        (),
    )

    _OUTPUTS = (
        (
            ('Analog',  'ins0', 6),
            ('S/PDIF',  'aes',  2),
        ),
        (
            ('Analog',  'ins0', 6),
            ('S/PDIF',  'aes',  2),
        ),
        (
            ('Analog',  'ins0', 4),
            ('S/PDIF',  'aes',  2),
        ),
        (
            ('Analog',  'ins0', 6),
            ('S/PDIF',  'aes',  2),
        ),
        (),
        (),
        (),
    )

    _FIXED = (
        {},
        {},
        {},
        {
            0: ('src', 'ins0', 0),
            1: ('src', 'ins0', 1),
            2: ('src', 'ins0', 2),
            3: ('src', 'ins0', 3),
            4: ('src', 'ins0', 4),
            5: ('src', 'ins0', 5),
        },
        {},
        {},
        {},
    )
