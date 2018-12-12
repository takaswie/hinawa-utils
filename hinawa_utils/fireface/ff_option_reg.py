# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.fireface.ff_status_reg import FFClkLabels

__all__ = ['FFOptionReg']

class FFOptionReg():
    __MULTIPLE_OPTION_MASKS = {
        'line-in': {
            'lo-gain':      (0x00000008, 0x00000000, 0x00000000),
            '-10dB':        (0x00000020, 0x00000002, 0x00000000),
            '+4dB':         (0x00000010, 0x00000003, 0x00000000),
        },
        'line-out': {
            '-10dB':        (0x00001000, 0x00000008, 0x00000000),
            '+4dB':         (0x00000800, 0x00000018, 0x00000000),
            'hi-gain':      (0x00000400, 0x00000010, 0x00000000),
        },
        'primary-clk-src': {
            FFClkLabels.ADAT1.value:    (0x00000000, 0x00000000, 0x00000000),
            FFClkLabels.ADAT2.value:    (0x00000000, 0x00000000, 0x00000400),
            FFClkLabels.SPDIF.value:    (0x00000000, 0x00000000, 0x00000c00),
            FFClkLabels.WDCLK.value:    (0x00000000, 0x00000000, 0x00001400),
        },
    }

    # bit flags for boolean value.
    __SINGLE_OPTION_MASKS = {
        'auto-sync': {
            'internal':     (0x00000000, 0x00000000, 0x00000001),
            'base-441':     (0x00000000, 0x00000000, 0x00000002),
            'base-480':     (0x00000000, 0x00000000, 0x00000004),
            'double':       (0x00000000, 0x00000000, 0x00000008),
            'quadruple':    (0x00000000, 0x00000000, 0x00000010),
        },
        'front-input': {
            'in-1':         (0x00000000, 0x00000800, 0x00000000),
            'in-7':         (0x00000000, 0x00000020, 0x00000000),
            'in-8':         (0x00000000, 0x00000080, 0x00000000),
        },
        'rear-input': {
            'in-1':         (0x00000000, 0x00000004, 0x00000000),
            'in-7':         (0x00000000, 0x00000040, 0x00000000),
            'in-8':         (0x00000000, 0x00000100, 0x00000000),
        },
        'phantom-power': {
            'mic-7':        (0x00000001, 0x00000000, 0x00000000),
            'mic-8':        (0x00000080, 0x00000000, 0x00000000),
            'mic-9':        (0x00000002, 0x00000000, 0x00000000),
            'mic-10':       (0x00000100, 0x00000000, 0x00000000),
        },
        'spdif-in': {
            'optical':      (0x00000000, 0x00000000, 0x00000200),
            'track-maker':  (0x00000000, 0x00000000, 0x40000000),
        },
        'spdif-out': {
            'professional': (0x00000000, 0x00000000, 0x00000020),
            'emphasis':     (0x00000000, 0x00000000, 0x00000040),
            'non-audio':    (0x00000000, 0x00000000, 0x00000080),
            'optical':      (0x00000000, 0x00000000, 0x00000100),
        },
        'instruments': {
            'drive':        (0x00000200, 0x00000200, 0x00000000),
            'limit':        (0x00000000, 0x00000000, 0x00010000),
            'speaker-emu':  (0x00000004, 0x00000000, 0x00000000),
        },
        'wdclk-out': {
            'single-speed': (0x00000000, 0x00000000, 0x00004000),
        },
        'midi-low-addr': {
            '0x00000000':   (0x00000000, 0x00000000, 0x04000000),
            '0x00000080':   (0x00000000, 0x00000000, 0x08000000),
            '0x00000100':   (0x00000000, 0x00000000, 0x10000000),
            '0x00000180':   (0x00000000, 0x00000000, 0x20000000),
        },
        'in-error': {
            'continue':     (0x00000000, 0x00000000, 0x80000000),
        }
    }

    # Helper functions for multiple value options.
    @classmethod
    def get_multiple_option_labels(cls):
        return cls.__MULTIPLE_OPTION_MASKS.keys()
    @classmethod
    def get_multiple_option_value_labels(cls, target):
        if target not in cls.__MULTIPLE_OPTION_MASKS:
            raise ValueError('Invalid argument for multi option.')
        return cls.__MULTIPLE_OPTION_MASKS[target].keys()
    @classmethod
    def build_multiple_option(cls, quads, target, val):
        if target not in cls.__MULTIPLE_OPTION_MASKS:
            raise ValueError('Invalid argument for multi option.')
        if val not in cls.__MULTIPLE_OPTION_MASKS[target]:
            raise ValueError('Invalid argument for value of multi option.')
        elems = cls.__MULTIPLE_OPTION_MASKS[target]
        for name, flags in elems.items():
            for i, flag in enumerate(flags):
                quads[i] &= ~flag
        for i, flag in enumerate(elems[val]):
            quads[i] |= flag
        return quads
    @classmethod
    def parse_multiple_option(cls, quads, target):
        if target not in cls.__MULTIPLE_OPTION_MASKS:
            raise ValueError('Invalid argument for multi option.')
        elems = cls.__MULTIPLE_OPTION_MASKS[target]
        masks = [0x00] * 3
        for name, flags in elems.items():
            for i, flag in enumerate(flags):
                masks[i] |= flag
        for val, flags in elems.items():
            for i, flag in enumerate(flags):
                if quads[i] & masks[i] != flag:
                    break
            else:
                return val
        raise OSError('Unexpected state of bit flags.')

    # Helper functions to handle boolen options.
    @classmethod
    def get_single_option_labels(cls):
        return cls.__SINGLE_OPTION_MASKS.keys()
    @classmethod
    def get_single_option_item_labels(cls, target):
        if target not in cls.__SINGLE_OPTION_MASKS:
            raise ValueError('Invalid argument for bool option.')
        return cls.__SINGLE_OPTION_MASKS[target].keys()
    @classmethod
    def build_single_option(cls, quads, target, item, enable):
        if target not in cls.__SINGLE_OPTION_MASKS:
            raise ValueError('Invalid argument for bool option.')
        if item not in cls.__SINGLE_OPTION_MASKS[target]:
            raise ValueError('Invalid argument for item of bool option.')
        masks = cls.__SINGLE_OPTION_MASKS[target][item]
        for i, mask in enumerate(masks):
            quads[i] &= ~mask
            if enable:
                quads[i] |= mask
        return quads
    @classmethod
    def parse_single_option(cls, quads, target, item):
        if target not in cls.__SINGLE_OPTION_MASKS:
            raise ValueError('Invalid argument for bool option.')
        if item not in cls.__SINGLE_OPTION_MASKS[target]:
            raise ValueError('Invalid argument for item of bool option.')
        masks = cls.__SINGLE_OPTION_MASKS[target][item]
        for i, mask in enumerate(masks):
            if quads[i] & mask != mask:
                return False
        return True
