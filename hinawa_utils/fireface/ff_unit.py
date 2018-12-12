# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from struct import pack, unpack
from pathlib import Path

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from hinawa_utils.fireface.ff_config_rom_parser import FFConfigRomParser
from hinawa_utils.fireface.ff_option_reg import FFOptionReg
from hinawa_utils.fireface.ff_status_reg import FFStatusReg, FFClkLabels

__all__ = ['FFUnit']

class FFUnit(Hinawa.SndUnit):
    _MODELS = {
        0x000001:   ('Fireface800', (0x0000fc88f014, )),
        0x000002:   ('Fireface400', (0x00008010051c, )),
    }

    def __init__(self, path):
        super().__init__()
        self.open(path)
        self.listen()

        parser = FFConfigRomParser()
        info = parser.parse_rom(self.get_config_rom())
        if info['model_id'] not in self._MODELS:
            raise OSError('Unsupported model.')

        self.__name, self.__regs = self._MODELS[info['model_id']]

        guid = self.get_property('guid')
        self._path = Path('/tmp/hinawa-{0:08x}'.format(guid))

        self.__cache = [0x00] * 3
        if self._path.exists() and self._path.is_file():
            self.__load_cache()
        else:
            # Default values.
            single_options = {
                'auto-sync': {
                    'internal':     True,   'base-441':     True,
                    'base-480':     True,   'double':       True,
                    'quadruple':    True,
                },
                'front-input': {
                    'in-1':         False,  'in-7':         False,
                    'in-8':         False,
                },
                'rear-input': {
                    'in-1':         True,   'in-7':         True,
                    'in-8':         True,
                },
                'phantom-power': {
                    'mic-7':        False,  'mic-8':        False,
                    'mic-9':        False,  'mic-10':       False,
                },
                'spdif-in': {
                    'optical':      False,  'track-maker':  False,
                },
                'spdif-out': {
                    'professional': False,  'emphasis':     False,
                    'non-audio':    False,  'optical':      False,
                },
                'instruments': {
                    'drive':        False,  'limit':        True,
                    'speaker-emu':  False,
                },
                'wdclk-out': {
                    'single-speed': True,
                },
                'in-error': {
                    'continue':     True,
                },
            }
            multiple_options = {
                'line-in':          '-10dB',
                'line-out':         '-10dB',
                'primary-clk-src':  FFClkLabels.SPDIF.value,
            }
            for target, opts in single_options.items():
                for item, enable in opts.items():
                    FFOptionReg.build_single_option(self.__cache, target, item, enable)
            for target, value in multiple_options.items():
                FFOptionReg.build_multiple_option(self.__cache, target, value)

            self.__save_cache()

        # Assist ALSA fireface driver to handle MIDI messages from Fireface 400.
        if self.__name == 'Fireface400':
            FFOptionReg.build_single_option(self.__cache, 'miti-low',
                                            '0x00000000', True)

        self.__write_flags()

    def __load_cache(self):
        with self._path.open(mode='r') as f:
            for i, line in enumerate(f):
                self.__cache[i] = int(line.strip(), base=16)

    def __save_cache(self):
        with self._path.open(mode='w+') as f:
            for frame in self.__cache:
                f.write('{0:08x}\n'.format(frame))

    def __write_flags(self):
        req = Hinawa.FwReq()
        frames = pack('<3I', *self.__cache)
        req.write(self, self.__regs[0], frames)

    def get_model_name(self):
        return self.__name

    def get_multiple_option_labels(self):
        return FFOptionReg.get_multiple_option_labels()
    def get_multiple_option_value_labels(self, target):
        return FFOptionReg.get_multiple_option_value_labels(target)
    def set_multiple_option(self, target, val):
        self.__cache = FFOptionReg.build_multiple_option(self.__cache, target, val)
        self.__save_cache()
        self.__write_flags()
    def get_multiple_option(self, target):
        return FFOptionReg.parse_multiple_option(self.__cache, target)

    def get_single_option_labels(self):
        return FFOptionReg.get_single_option_labels()
    def get_single_option_item_labels(self, target):
        return FFOptionReg.get_single_option_item_labels(target)
    def set_single_option(self, target, item, enable):
        self.__cache = FFOptionReg.build_single_option(self.__cache, target, item, enable)
        self.__save_cache()
        self.__write_flags()
    def get_single_option(self, target, item):
        return FFOptionReg.parse_single_option(self.__cache, target, item)

    def get_sync_status(self):
        req = Hinawa.FwReq()
        frames = req.read(self, 0x0000801c0000, 8)
        quads = unpack('<2I', frames)

        return FFStatusReg.parse(quads)
