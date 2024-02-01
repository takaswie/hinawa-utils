# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from threading import Thread
from math import log10
from struct import pack, unpack
from pathlib import Path

import gi
gi.require_version('GLib', '2.0')
gi.require_version('Hinawa', '3.0')
gi.require_version('Hitaki', '0.0')
from gi.repository import GLib, Hinawa, Hitaki

from hinawa_utils.fireface.ff_config_rom_parser import FFConfigRomParser
from hinawa_utils.fireface.ff_option_reg import FFOptionReg
from hinawa_utils.fireface.ff_status_reg import FFStatusReg, FFClkLabels
from hinawa_utils.fireface.ff_mixer_reg import FFMixerRegs
from hinawa_utils.fireface.ff_out_reg import FFOutRegs

__all__ = ['FFUnit']


class FFUnit(Hitaki.SndUnit):
    __MODELS = {
        0x000001:   'Fireface800',
        0x000002:   'Fireface400',
    }
    __REGS = {
        # model_id: (option offset, mixer offset, out offset)
        0x000001:   (0x0000fc88f014, 0x000080080000, 0x000080081f80),
        0x000002:   (0x00008010051c, 0x000080080000, 0x000080080f80),
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
            'analog':   8,
            'spdif':    2,
            'adat':     8,
            'stream':   18,
            'avail':    18,
        },
    }

    __MUTE_VAL = 0x00000000
    __ZERO_VAL = 0x00008000
    __MIN_VAL = 0x00000001
    __MAX_VAL = 0x00010000

    def __init__(self, path):
        super().__init__()
        self.open(path, 0)

        ctx = GLib.MainContext.new()
        _, src = self.create_source()
        src.attach(ctx)
        self.__unit_dispatcher = GLib.MainLoop.new(ctx, False)
        self.__unit_th = Thread(target=lambda d: d.run(), args=(self.__unit_dispatcher, ))
        self.__unit_th.start()

        fw_node_path = '/dev/{}'.format(self.get_property('node-device'))
        self.__node = Hinawa.FwNode.new()
        self.__node.open(fw_node_path)
        ctx = GLib.MainContext.new()
        src = self.__node.create_source()
        src.attach(ctx)
        self.__node_dispatcher = GLib.MainLoop.new(ctx, False)
        self.__node_th = Thread(target=lambda d: d.run(), args=(self.__node_dispatcher, ))
        self.__node_th.start()

        parser = FFConfigRomParser()
        info = parser.parse_rom(self.get_node().get_config_rom())
        if info['model_id'] not in self.__MODELS:
            raise OSError('Unsupported model.')

        self.__name = self.__MODELS[info['model_id']]
        self.__regs = self.__REGS[info['model_id']]
        self.__spec = self.__SPECS[info['model_id']]

        guid = self.get_property('guid')
        self._path = Path('/tmp/hinawa-{0:08x}'.format(guid))

        if self._path.exists() and self._path.is_file():
            self.__read_cache_from_file()
        else:
            self.__option_cache = self.__create_option_initial_cache()
            self.__mixer_cache = self.__create_mixer_initial_cache()
            self.__out_cache = self.__create_out_initial_cache()
            self.__load_settings()
            self.__write_cache_to_file()

        self.__load_option_settings()

    def release(self):
        self.__unit_dispatcher.quit()
        self.__node_dispatcher.quit()
        self.__unit_th.join()
        self.__node_th.join()

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.release()

    def get_node(self):
        return self.__node

    def __read_cache_from_file(self):
        self.__option_cache = []
        self.__mixer_cache = []
        self.__out_cache = []
        with self._path.open(mode='r') as f:
            for i, line in enumerate(f):
                line = line.strip()
                tokens = line.split(' ')
                reg_type = tokens[0]
                reg_val = int(tokens[1], 16)
                if reg_type == 'option':
                    self.__option_cache.append(reg_val)
                elif reg_type == 'mixer':
                    self.__mixer_cache.append(reg_val)
                elif reg_type == 'out':
                    self.__out_cache.append(reg_val)

    def __write_cache_to_file(self):
        with self._path.open(mode='w+') as f:
            for frame in self.__option_cache:
                f.write('option {0:08x}\n'.format(frame))
            for frame in self.__mixer_cache:
                f.write('mixer {0:08x}\n'.format(frame))
            for frame in self.__out_cache:
                f.write('out {0:08x}\n'.format(frame))

    def __load_settings(self):
        self.__load_option_settings()
        for target in self.get_mixer_labels():
            for src in self.get_mixer_src_labels():
                db = self.get_mixer_src(target, src)
                self.set_mixer_src(target, src, db)
        for target in self.get_out_labels():
            db = self.get_out_volume(target)
            self.set_out_volume(target, db)

    def get_model_name(self):
        return self.__name

    #
    # Configuration for options.
    #
    def __create_option_initial_cache(self):
        cache = [0x00] * 3
        self.__create_multiple_option_initial_cache(cache)
        self.__create_single_option_initial_cache(cache)
        return cache

    def __load_option_settings(self):
        # Assist ALSA fireface driver to handle MIDI messages from Fireface 400.
        if self.__name == 'Fireface400':
            FFOptionReg.build_single_option(self.__option_cache,
                                            'midi-low-addr', '0x00000000', True)
        req = Hinawa.FwReq()
        frames = pack('<3I', *self.__option_cache)
        req.transaction(self.get_node(), Hinawa.FwTcode.WRITE_BLOCK_REQUEST,
                        self.__regs[0], len(frames), frames)

    def __create_multiple_option_initial_cache(self, cache):
        default_params = {
            'line-in':          '-10dB',
            'line-out':         '-10dB',
            'primary-clk-src':  FFClkLabels.SPDIF.value,
        }
        for target, value in default_params.items():
            FFOptionReg.build_multiple_option(cache, target, value)

    def get_multiple_option_labels(self):
        return FFOptionReg.get_multiple_option_labels()

    def get_multiple_option_value_labels(self, target):
        return FFOptionReg.get_multiple_option_value_labels(target)

    def set_multiple_option(self, target, val):
        FFOptionReg.build_multiple_option(self.__option_cache, target, val)
        self.__write_cache_to_file()
        self.__load_option_settings()

    def get_multiple_option(self, target):
        return FFOptionReg.parse_multiple_option(self.__option_cache, target)

    def __create_single_option_initial_cache(self, cache):
        default_params = {
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
        for target, params in default_params.items():
            for item, enable in params.items():
                FFOptionReg.build_single_option(cache, target, item, enable)

    def get_single_option_labels(self):
        return FFOptionReg.get_single_option_labels()

    def get_single_option_item_labels(self, target):
        return FFOptionReg.get_single_option_item_labels(target)

    def set_single_option(self, target, item, enable):
        FFOptionReg.build_single_option(self.__option_cache, target, item,
                                        enable)
        self.__write_cache_to_file()
        self.__load_option_settings()

    def get_single_option(self, target, item):
        return FFOptionReg.parse_single_option(self.__option_cache, target,
                                               item)

    def get_sync_status(self):
        req = Hinawa.FwReq()
        frames = bytearray(8)
        frames = req.transaction(self.get_node(),
                    Hinawa.FwTcode.READ_BLOCK_REQUEST,
                    0x0000801c0000, 8, frames)
        quads = unpack('<2I', frames)

        return FFStatusReg.parse(quads)

    #
    # Configuration for internal multiplexer.
    #
    def __create_mixer_initial_cache(self):
        targets = self.get_mixer_labels()
        srcs = self.get_mixer_src_labels()
        cache = [0x00] * (len(targets) * 2 * self.__spec['avail'])
        for i, target in enumerate(targets):
            for src in srcs:
                # Supply diagonal stream sources to each mixers.
                if src != 'stream-{0}'.format(i + 1):
                    val = self.__MUTE_VAL
                else:
                    val = self.__ZERO_VAL
                offset = FFMixerRegs.calculate_src_offset(self.__spec, target,
                                                          src)
                cache[offset // 4] = val
        return cache

    def get_mixer_labels(self):
        return FFMixerRegs.get_mixer_labels(self.__spec)

    def get_mixer_src_labels(self):
        return FFMixerRegs.get_mixer_src_labels(self.__spec)

    def get_mixer_mute_db(self):
        return self.get_db_mute()

    def get_mixer_min_db(self):
        return self.get_db_min()

    def get_mixer_max_db(self):
        return self.get_db_max()

    def set_mixer_src(self, target, src, db):
        offset = FFMixerRegs.calculate_src_offset(self.__spec, target, src)
        val = self.__build_val_from_db(db)
        data = pack('<I', val)
        req = Hinawa.FwReq()
        req.transaction(self.get_node(), Hinawa.FwTcode.WRITE_BLOCK_REQUEST,
                        self.__regs[1] + offset, len(data), data)
        self.__mixer_cache[offset // 4] = val
        self.__write_cache_to_file()

    def get_mixer_src(self, target, src):
        offset = FFMixerRegs.calculate_src_offset(self.__spec, target, src)
        return self.__parse_val_to_db(self.__mixer_cache[offset // 4])

    #
    # Configuration for output.
    #
    def __create_out_initial_cache(self):
        targets = FFOutRegs.get_out_labels(self.__spec)
        cache = [0x00] * len(targets)
        for target in targets:
            offset = FFOutRegs.calculate_out_offset(self.__spec, target)
            cache[offset // 4] = self.__ZERO_VAL
        return cache

    def get_out_labels(self):
        return FFOutRegs.get_out_labels(self.__spec)

    def set_out_volume(self, target, db):
        if db > self.get_db_max():
            raise ValueError('Invalid argument for db.')
        offset = FFOutRegs.calculate_out_offset(self.__spec, target)
        val = self.__build_val_from_db(db)
        data = pack('<I', val)
        req = Hinawa.FwReq()
        req.transaction(self.get_node(), Hinawa.FwTcode.WRITE_BLOCK_REQUEST,
                        self.__regs[2] + offset, len(data), data)
        self.__out_cache[offset // 4] = val

    def get_out_volume(self, target):
        offset = FFOutRegs.calculate_out_offset(self.__spec, target)
        return self.__parse_val_to_db(self.__out_cache[offset // 4])

    #
    # Helper methods.
    #
    @staticmethod
    def __build_val_from_db(db: float):
        return int(0x8000 * pow(10, db / 20))

    @staticmethod
    def __parse_val_to_db(val: int):
        if val == 0:
            return float('-inf')
        return 20 * log10(val / 0x8000)

    @classmethod
    def get_db_mute(cls):
        return cls.__parse_val_to_db(cls.__MUTE_VAL)

    @classmethod
    def get_db_zero(cls):
        return cls.__parse_val_to_db(cls.__ZERO_VAL)

    @classmethod
    def get_db_min(cls):
        return cls.__parse_val_to_db(cls.__MIN_VAL)

    @classmethod
    def get_db_max(cls):
        return cls.__parse_val_to_db(cls.__MAX_VAL)
