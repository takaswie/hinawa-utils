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
from hinawa_utils.fireface.ff_mixer_reg import FFMixerRegs

__all__ = ['FFUnit']

class FFUnit(Hinawa.SndUnit):
    __MODELS = {
        0x000001:   'Fireface800',
        0x000002:   'Fireface400',
    }
    __REGS = {
        # model_id: (option offset, mixer offset)
        0x000001:   (0x0000fc88f014, 0x000080080000),
        0x000002:   (0x00008010051c, 0x000080080000),
    }
    __SPECS = {
        0x000001: {
            'analog':   10,
            'spdif':    2,
            'adat':     16,
            'stream':   28,
            'avail':    32,
        },
        0x000002: {
            'analog':   10,
            'spdif':    2,
            'adat':     8,
            'stream':   18,
            'avail':    18,
        },
    }

    def __init__(self, path):
        super().__init__()
        self.open(path)
        self.listen()

        parser = FFConfigRomParser()
        info = parser.parse_rom(self.get_config_rom())
        if info['model_id'] not in self.__MODELS:
            raise OSError('Unsupported model.')

        self.__name = self.__MODELS[info['model_id']]
        self.__regs = self.__REGS[info['model_id']]
        self.__spec = self.__SPECS[info['model_id']]

        guid = self.get_property('guid')
        self._path = Path('/tmp/hinawa-{0:08x}'.format(guid))

        if self._path.exists() and self._path.is_file():
            self.__load_cache()
        else:
            self.__option_cache = FFOptionReg.create_initial_cache(self.__name)
            self.__mixer_cache = FFMixerRegs.create_initial_cache(self.__spec)
            self.__save_cache()
            self.__set_mixers()

        self.__set_options()

    def __load_cache(self):
        self.__option_cache = [0x00] * 3
        self.__mixer_cache = []
        with self._path.open(mode='r') as f:
            for i, line in enumerate(f):
                val = int(line.strip(), base=16)
                if i < len(self.__option_cache):
                    self.__option_cache[i] = val
                else:
                    self.__mixer_cache.append(val)

    def __save_cache(self):
        with self._path.open(mode='w+') as f:
            for frame in self.__option_cache:
                f.write('{0:08x}\n'.format(frame))
            for frame in self.__mixer_cache:
                f.write('{0:08x}\n'.format(frame))

    def __set_options(self):
        req = Hinawa.FwReq()
        frames = pack('<3I', *self.__option_cache)
        req.write(self, self.__regs[0], frames)

    def __set_mixers(self):
        req = Hinawa.FwReq()
        targets = FFMixerRegs.get_mixer_labels(self.__spec)
        srcs = FFMixerRegs.get_mixer_src_labels(self.__spec)
        for target in targets:
            for src in srcs:
                db = self.get_mixer_src(target, src)
                self.set_mixer_src(target, src, db)

    def get_model_name(self):
        return self.__name

    def get_multiple_option_labels(self):
        return FFOptionReg.get_multiple_option_labels()
    def get_multiple_option_value_labels(self, target):
        return FFOptionReg.get_multiple_option_value_labels(target)
    def set_multiple_option(self, target, val):
        FFOptionReg.build_multiple_option(self.__option_cache, target, val)
        self.__save_cache()
        self.__set_options()
    def get_multiple_option(self, target):
        return FFOptionReg.parse_multiple_option(self.__option_cache, target)

    def get_single_option_labels(self):
        return FFOptionReg.get_single_option_labels()
    def get_single_option_item_labels(self, target):
        return FFOptionReg.get_single_option_item_labels(target)
    def set_single_option(self, target, item, enable):
        FFOptionReg.build_single_option(self.__option_cache, target, item,
                                        enable)
        self.__save_cache()
        self.__set_options()
    def get_single_option(self, target, item):
        return FFOptionReg.parse_single_option(self.__option_cache, target,
                                               item)

    def get_sync_status(self):
        req = Hinawa.FwReq()
        frames = req.read(self, 0x0000801c0000, 8)
        quads = unpack('<2I', frames)

        return FFStatusReg.parse(quads)

    def get_mixer_labels(self):
        return FFMixerRegs.get_mixer_labels(self.__spec)

    def get_mixer_src_labels(self):
        return FFMixerRegs.get_mixer_src_labels(self.__spec)

    def get_mixer_mute_db(self):
        return FFMixerRegs.get_mute_db()

    def get_mixer_min_db(self):
        return FFMixerRegs.get_min_db()

    def get_mixer_max_db(self):
        return FFMixerRegs.get_max_db()

    def set_mixer_src(self, target, src, db):
        offset = FFMixerRegs.calculate_offset(self.__spec, target, src)
        val = FFMixerRegs.build_val_from_db(db)
        data = pack('<I', val)
        req = Hinawa.FwReq()
        req.write(self, self.__regs[1] + offset, data)
        self.__mixer_cache[offset // 4] = val
        self.__save_cache()

    def get_mixer_src(self, target, src):
        offset = FFMixerRegs.calculate_offset(self.__spec, target, src)
        return FFMixerRegs.parse_val_to_db(self.__mixer_cache[offset // 4])
