# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from enum import Enum

__all__ = ['FFClkLabels', 'FFStatusReg']

class FFClkLabels(Enum):
    ADAT1   = 'ADAT1'
    ADAT2   = 'ADAT2'
    SPDIF   = 'S/PDIF'
    WDCLK   = 'Word-clock'
    LTO     = 'LTO'
    TCO     = 'TCO'

class FFStatusReg():
    __SINGLE_STATUS_MASKS = {
        'spdif-rate': {
            32000:              (0x00004000, 0x00000000),
            44100:              (0x00008000, 0x00000000),
            48000:              (0x0000c000, 0x00000000),
            64000:              (0x00010000, 0x00000000),
            88200:              (0x00014000, 0x00000000),
            96000:              (0x00018000, 0x00000000),
            128000:             (0x0001c000, 0x00000000),
            176400:             (0x00020000, 0x00000000),
            192000:             (0x00024000, 0x00000000),
        },
        'referred-rate': {
            32000:              (0x02000000, 0x00000000),
            44100:              (0x04000000, 0x00000000),
            48000:              (0x06000000, 0x00000000),
            64000:              (0x08000000, 0x00000000),
            88200:              (0x0a000000, 0x00000000),
            96000:              (0x0c000000, 0x00000000),
            128000:             (0x0e000000, 0x00000000),
            176400:             (0x10000000, 0x00000000),
            192000:             (0x12000000, 0x00000000),
        },
        'base-freq': {
            '44100':            (0x00000000, 0x00000000),
            '32000':            (0x00000000, 0x00000002),
            '48000':            (0x00000000, 0x00000006),
        },
        'multiplier': {
            'single':           (0x00000000, 0x00000000),
            'double':           (0x00000000, 0x00000008),
            'quadruple':        (0x00000000, 0x00000010),
        },
        'sync-mode': {
            'internal':         (0x00000000, 0x00000001),
        },
        'referred': {
            FFClkLabels.ADAT1.value:    (0x00000000, 0x00000000),
            FFClkLabels.ADAT2.value:    (0x00400000, 0x00000000),
            FFClkLabels.SPDIF.value:    (0x00c00000, 0x00000000),
            FFClkLabels.WDCLK.value:    (0x01000000, 0x00000000),
            FFClkLabels.TCO.value:      (0x01400000, 0x00000000),
        },
    }

    __MULTIPLE_STATUS_MASKS = {
        'synchronized': {
            FFClkLabels.ADAT1.value:    (0x00001000, 0x00000000),
            FFClkLabels.ADAT2.value:    (0x00002000, 0x00000000),
            FFClkLabels.SPDIF.value:    (0x00040000, 0x00000000),
            FFClkLabels.WDCLK.value:    (0x20000000, 0x00000000),
            FFClkLabels.TCO.value:      (0x00000000, 0x00400000),
        },
        'locked': {
            FFClkLabels.ADAT1.value:    (0x00000400, 0x00000000),
            FFClkLabels.ADAT2.value:    (0x00000800, 0x00000000),
            FFClkLabels.SPDIF.value:    (0x00080000, 0x00000000),
            FFClkLabels.WDCLK.value:    (0x40000000, 0x00000000),
            FFClkLabels.TCO.value:      (0x00000000, 0x00800000),
        },
    }

    @classmethod
    def parse(cls, quads):
        status = {}

        for target, elems in cls.__SINGLE_STATUS_MASKS.items():
            masks = [0x00] * 2
            for name, flags in elems.items():
                for i, flag in enumerate(flags):
                    masks[i] |= flag
            for name, flags in elems.items():
                for i, flag in enumerate(flags):
                    if quads[i] & masks[i] != flag:
                        break
                else:
                    status[target] = name

        for target, elems in cls.__MULTIPLE_STATUS_MASKS.items():
            status[target] = {}
            for name, flags in elems.items():
                for i, flag in enumerate(flags):
                    if quads[i] & flag != flag:
                        status[target][name] = False
                        break
                else:
                    status[target][name] = True

        return status
