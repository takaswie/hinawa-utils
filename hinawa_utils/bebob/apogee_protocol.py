# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from struct import pack
from enum import Enum

__all__ = ['HwCmd', 'DisplayCmd', 'OptIfaceCmd', 'MicCmd', 'InputCmd',
           'OutputCmd', 'MixerCmd', 'RouteCmd', 'StatusCmd', 'KnobCmd',
           'SpdifResampleCmd']


class VendorCmd(Enum):
    INPUT_LIMIT     = 0xe4
    MIC_POWER       = 0xe5
    IO_ATTR         = 0xe8
    IO_ROUTING      = 0xef
    HW              = 0xeb
    HP_SRC          = 0xab
    MIXER_SRC1      = 0xb0
    MIXER_SRC2      = 0xb1
    MIXER_SRC3      = 0xb2
    MIXER_SRC4      = 0xb3
    OPT_IFACE_MODE  = 0xf1
    DOWNGRADE       = 0xf2
    SPDIF_RESAMPLE  = 0xf3
    MIC_POLARITY    = 0xf5
    KNOB_VALUE      = 0xf6
    HW_STATUS       = 0xff


class HwCmdOp(Enum):
    STREAM_MODE         = 0x06
    DISPLAY_ILLUMINATE  = 0x08
    DISPLAY_MODE        = 0x09
    DISPLAY_TARGET      = 0x0a
    DISPLAY_OVERHOLD    = 0x0e
    METER_RESET         = 0x0f
    CD_MODE             = 0xf5


class HwCmd():
    __STREAM_MODES = {
        '16x16':    0x00,
        '10x10':    0x01,
        '8x8':      0x02,
    }

    __DOWNGRADE_TARGETS = {
        'none':                 0x00,
        'analog-in-1/2':        0x01,
        'analog-in-3/4':        0x02,
        'analog-in-5/6':        0x03,
        'analog-in-7/8':        0x04,
        'spdif-opt-in-1/2':     0x05,
        'spdif-coax-in-1/2':    0x09,
        'spdif-coax-out-1/2':   0x0a,
        'spdif-opt-out-1/2':    0x0b,
    }

    @classmethod
    def create_cache(cls):
        cache = {
            'cd':       False,
            '16bit':    'none',
        }
        return cache

    @classmethod
    def get_stream_mode_labels(cls):
        return list(cls.__STREAM_MODES.keys())

    @classmethod
    def __build_args(cls, op, val):
        args = bytearray()
        args.append(VendorCmd.HW.value)
        args.append(op.value)
        args.append(val)
        return args

    @classmethod
    def build_stream_mode(cls, mode):
        if mode not in cls.__STREAM_MODES:
            raise ValueError('Invalid argument for mode of stream.')
        val = cls.__STREAM_MODES[mode]
        return cls.__build_args(HwCmdOp.STREAM_MODE, val)

    @classmethod
    def build_cd_mode(cls, enable):
        if not isinstance(enable, bool):
            raise ValueError('Invalid argument for mode of cd.')
        val = 0x01 if enable else 0x00
        return cls.__build_args(HwCmdOp.CD_MODE, val)

    @classmethod
    def get_16bit_mode_labels(cls):
        return list(cls.__DOWNGRADE_TARGETS.keys())
    @classmethod
    def build_16bit_mode(cls, target):
        if target not in cls.__DOWNGRADE_TARGETS:
            raise ValueError('Invalid argument for target of 16bit mode.')
        args = bytearray()
        args.append(VendorCmd.DOWNGRADE.value)
        args.append(cls.__DOWNGRADE_TARGETS[target])
        return args


class DisplayCmd():
    __TARGETS = {
        'output':   0x00,
        'input':    0x01,
    }

    @classmethod
    def create_cache(cls):
        cache = {
            'illuminate': False,
            'mode': False,
            'target': 'output',
            'overhold': False,
        }
        return cache

    @classmethod
    def get_target_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def __build_args(cls, op, val):
        args = bytearray()
        args.append(VendorCmd.HW.value)
        args.append(op.value)
        args.append(val)
        return args

    @classmethod
    def build_illuminate(cls, enable):
        if not isinstance(enable, bool):
            raise ValueError('Invalid argument for illuminate of display.')
        val = 0x01 if enable else 0x00
        return cls.__build_args(HwCmdOp.DISPLAY_ILLUMINATE, val)

    @classmethod
    def build_mode(cls, enable):
        if not isinstance(enable, bool):
            raise ValueError('Invalid argument for mode of display.')
        val = 0x01 if enable else 0x00
        return cls.__build_args(HwCmdOp.DISPLAY_MODE, val)

    @classmethod
    def build_target(cls, target):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for target of display.')
        val = cls.__TARGETS[target]
        return cls.__build_args(HwCmdOp.DISPLAY_TARGET, val)

    @classmethod
    def build_overhold(cls, enable):
        if not isinstance(enable, bool):
            raise ValueError('Invalid argument for overhold of display.')
        val = 0x01 if enable else 0x00
        return cls.__build_args(HwCmdOp.DISPLAY_OVERHOLD, val)

    @classmethod
    def build_meter_reset(cls):
        return cls.__build_args(HwCmdOp.METER_RESET, 0x00)


class OptIfaceCmd():
    __TARGETS = {
        'output':   0x00,
        'input':    0x00,
    }
    __MODES = {
        'S/PDIF':       0x00,
        'ADAT/SMUX':    0x01,
    }

    @classmethod
    def create_cache(cls):
        cache = {}
        for target in cls.__TARGETS:
            cache[target] = 'S/PDIF'
        return cache

    @classmethod
    def get_target_labels(cls):
        return list(cls.__TARGETS.keys())
    @classmethod
    def get_mode_labels(cls):
        return list(cls.__MODES.keys())
    @classmethod
    def build_opt_iface(cls, target, mode):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for target of optical iface.')
        if mode not in cls.__MODES:
            raise ValueError('Invalid argument for mode of optical iface.')
        args = bytearray()
        args.append(VendorCmd.OPT_IFACE_MODE.value)
        args.append(cls.__TARGETS[target])
        args.append(cls.__MODES[mode])
        return args


class MicCmd():
    __TARGETS = {
        'mic-1':    0x00,
        'mic-2':    0x01,
        'mic-3':    0x02,
        'mic-4':    0x03,
    }

    @classmethod
    def create_cache(cls):
        cache = {}
        for item in ('power', 'polarity'):
            cache[item] = {}
            for target in cls.__TARGETS:
                cache[item][target] = False
        return cache

    @classmethod
    def __build_args(cls, cmd, target, val):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for mic.')
        args = bytearray()
        args.append(cmd.value)
        args.append(cls.__TARGETS[target])
        args.append(val)
        return args

    @classmethod
    def get_mic_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def build_power(cls, target, enable):
        val = 0x01 if enable else 0x00
        return cls.__build_args(VendorCmd.MIC_POWER, target, val)

    @classmethod
    def build_polarity(cls, target, invert):
        val = 0x01 if invert else 0x00
        return cls.__build_args(VendorCmd.MIC_POLARITY, target, val)


class InputCmd():
    __TARGETS = {
        'analog-1': 0x00,
        'analog-2': 0x01,
        'analog-3': 0x02,
        'analog-4': 0x03,
        'analog-5': 0x04,
        'analog-6': 0x05,
        'analog-7': 0x06,
        'analog-8': 0x07,
    }

    __ATTRS = {
        '+4dB':     0x00,
        '-10dB':    0x01,
    }

    @classmethod
    def create_cache(cls):
        cache = {}
        cache['soft-limit'] = {}
        cache['attr'] = {}
        for target in cls.__TARGETS:
            cache['soft-limit'][target] = False
            cache['attr'][target] = '-10dB'
        return cache

    @classmethod
    def get_in_labels(cls):
        return list(cls.__TARGETS.keys())
    @classmethod
    def get_attr_labels(cls):
        return list(cls.__ATTRS.keys())
    @classmethod
    def build_soft_limit(cls, target, enable):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for line input.')
        val = 0x01 if enable else 0x00

        args = bytearray()
        args.append(VendorCmd.INPUT_LIMIT.value)
        args.append(cls.__TARGETS[target])
        args.append(val)
        return args

    @classmethod
    def build_attr(cls, target, attr):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for line input.')
        if attr not in cls.__ATTRS:
            raise ValueError('Invalid argument for in attenuation.')

        args = bytearray()
        args.append(VendorCmd.IO_ATTR.value)
        args.append(cls.__TARGETS[target])
        args.append(0x01)   # input.
        args.append(cls.__ATTRS[attr])
        return args


class OutputCmd():
    __TARGETS = {
        'analog-1': 0x00,
        'analog-2': 0x01,
        'analog-3': 0x02,
        'analog-4': 0x03,
        'analog-5': 0x04,
        'analog-6': 0x05,
        'analog-7': 0x06,
        'analog-8': 0x07,
    }

    __ATTRS = {
        '+4dB':     0x00,
        '-10dB':    0x01,
    }

    @classmethod
    def create_cache(cls):
        cache = {}
        cache['attr'] = {}
        for target in cls.__TARGETS:
            cache['attr'][target] = '-10dB'
        return cache

    @classmethod
    def get_target_labels(cls):
        return list(cls.__TARGETS.keys())
    @classmethod
    def get_attr_labels(cls):
        return list(cls.__ATTRS.keys())
    @classmethod
    def build_attr(cls, target, attr):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for line output.')
        if attr not in cls.__ATTRS:
            raise ValueError('Invalid argument for out attenuation.')

        args = bytearray()
        args.append(VendorCmd.IO_ATTR.value)
        args.append(cls.__TARGETS[target])
        args.append(0x00)    # output.
        args.append(cls.__ATTRS[attr])
        return args


class MixerCmd():
    __TARGETS = {
        'mixer-1/2':    0x00,
        'mixer-3/4':    0x01,
    }

    __SRCS = {
        VendorCmd.MIXER_SRC1: (
            'analog-1', 'analog-2',
            'analog-3', 'analog-4',
            'analog-5', 'analog-6',
            'analog-7', 'analog-8',
            'stream-1',
        ),
        VendorCmd.MIXER_SRC2: (
            'stream-2', 'stream-3',
            'stream-4', 'stream-5',
            'stream-6', 'stream-7',
            'stream-8', 'stream-9',
            'stream-10',
        ),
        VendorCmd.MIXER_SRC3: (
            'stream-11', 'stream-12',
            'stream-13', 'stream-14',
            'stream-15', 'stream-16',
            'stream-17', 'stream-18',
            'adat-1',
        ),
        VendorCmd.MIXER_SRC4: (
            'adat-2', 'adat-3',
            'adat-4', 'adat-5',
            'adat-6', 'adat-7',
            'adat-8', 'spdif-1',
            'spdif-2',
        ),
    }

    @classmethod
    def create_cache(cls):
        cache = {}
        for target in cls.__TARGETS:
            right = True
            cache[target] = {}
            for cmd, srcs in cls.__SRCS.items():
                for src in srcs:
                    db = 0.0
                    balance = 100.0 if right else 0.0
                    cache[target][src] = [db, balance]
                    right = not right
        return cache

    @classmethod
    def get_target_labels(cls):
        return list(cls.__TARGETS.keys())
    @classmethod
    def get_mixer_src_labels(cls):
        srcs = []
        for cmd, sources in cls.__SRCS.items():
            srcs.extend(sources)
        return srcs
    @classmethod
    def build_src_gain(cls, cache, target, src, db, balance):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for mixer.')
        if db < -48 or db > 0:
            raise ValueError('Invalid argument for db of source.')
        if balance < 0 or 100 < balance:
            raise ValueError('Invalid argument for balance of source.')

        for cmd, srcs in cls.__SRCS.items():
            if src in srcs:
                break
        else:
            raise ValueError('Invalid argument for source of mixer.')
        data = (db, balance)

        for s in srcs:
            if s not in cache[target]:
                raise ValueError('Invalid argument for status cache.')

        args = bytearray()
        args.append(cmd.value)
        args.append(cls.__TARGETS[target])
        for s in srcs:
            if s == src:
                db, balance = data
            else:
                db, balance = cache[target][s]
            val = int(0xffff * (1 + db / 48))
            right = int(val * balance / 100)
            left = val - right
            args.extend(pack('<H', left))
            args.extend(pack('<H', right))

        return args


class RouteCmd():
    __PORTS = {
        # From external interfaces.
        'analog-1':     0x00,
        'analog-2':     0x01,
        'analog-3':     0x02,
        'analog-4':     0x03,
        'analog-5':     0x04,
        'analog-6':     0x05,
        'analog-7':     0x06,
        'analog-8':     0x07,
        # For host computer.
        'stream-1':     0x08,
        'stream-2':     0x09,
        'stream-3':     0x0a,
        'stream-4':     0x0b,
        'stream-5':     0x0c,
        'stream-6':     0x0d,
        'stream-7':     0x0e,
        'stream-8':     0x0f,
        'stream-9':     0x10,
        'stream-10':    0x11,
        'stream-11':    0x12,
        'stream-12':    0x13,
        'stream-13':    0x14,
        'stream-14':    0x15,
        'stream-15':    0x16,
        'stream-16':    0x17,
        'stream-17':    0x18,
        'stream-18':    0x19,
        # From external interfaces.
        'spdif-1':      0x1a,
        'spdif-2':      0x1b,
        'adat-1':       0x1c,
        'adat-2':       0x1d,
        'adat-3':       0x1e,
        'adat-4':       0x1f,
        'adat-5':       0x20,
        'adat-6':       0x21,
        'adat-7':       0x22,
        'adat-8':       0x23,
        # From internal multiplexers.
        'mixer-1':      0x24,
        'mixer-2':      0x25,
        'mixer-3':      0x26,
        'mixer-4':      0x27,
    }

    __OUT_TARGETS = (
        'analog-1', 'analog-2', 'analog-3', 'analog-4',
        'analog-5', 'analog-6', 'analog-7', 'analog-8',
        'spdif-1', 'spdif-2',
        'adat-1', 'adat-2', 'adat-3', 'adat-4',
        'adat-5', 'adat-6', 'adat-7', 'adat-8',
    )

    __OUT_SRCS = (
        'analog-1', 'analog-2', 'analog-3', 'analog-4',
        'analog-5', 'analog-6', 'analog-7', 'analog-8',
        'stream-1', 'stream-2', 'stream-3', 'stream-4',
        'stream-5', 'stream-6', 'stream-7', 'stream-8',
        'stream-9', 'stream-10', 'stream-11', 'stream-12',
        'stream-13', 'stream-14', 'stream-15', 'stream-16',
        'stream-17', 'stream-18',
        'spdif-1', 'spdif-2',
        'adat-1', 'adat-2', 'adat-3', 'adat-4',
        'adat-5', 'adat-6', 'adat-7', 'adat-8',
        'mixer-1', 'mixer-2',
        'mixer-3', 'mixer-4',
    )

    __CAP_TARGETS = (
        'stream-1', 'stream-2', 'stream-3', 'stream-4',
        'stream-5', 'stream-6', 'stream-7', 'stream-8',
        'stream-9', 'stream-10', 'stream-11', 'stream-12',
        'stream-13', 'stream-14', 'stream-15', 'stream-16',
        'stream-17', 'stream-18',
    )

    __CAP_SRCS = (
        'analog-1', 'analog-2', 'analog-3', 'analog-4',
        'analog-5', 'analog-6', 'analog-7', 'analog-8',
        'spdif-1', 'spdif-2',
        'adat-1', 'adat-2', 'adat-3', 'adat-4',
        'adat-5', 'adat-6', 'adat-7', 'adat-8',
    )

    __HP_TARGETS = {
        'hp-1': 0x01,
        'hp-2': 0x00,
    }

    __HP_SRCS = {
        'analog-1/2':   0x01,
        'analog-3/4':   0x03,
        'analog-5/6':   0x05,
        'analog-7/8':   0x07,
        'spdif-1/2':    0x09,
        'none':         0xff,
    }

    @classmethod
    def create_cache(cls):
        cache = {}
        cache['out'] = {}
        cache['cap'] = {}
        cache['hp'] = {}
        for i, target in enumerate(cls.__OUT_TARGETS):
            src = cls.__OUT_SRCS[i + 8]
            cache['out'][target] = src
        for i, target in enumerate(cls.__CAP_TARGETS):
            src = cls.__CAP_SRCS[i]
            cache['cap'][target] = src
        for i, target in enumerate(cls.__HP_TARGETS):
            src = list(cls.__HP_SRCS.keys())[i]
            cache['hp'][target] = src
        return cache

    @classmethod
    def __build_args(cls, dst, src):
        args = bytearray()
        args.append(VendorCmd.IO_ROUTING.value)
        args.append(cls.__PORTS[dst])
        args.append(cls.__PORTS[src])
        return args

    @classmethod
    def get_out_labels(cls):
        return cls.__OUT_TARGETS
    @classmethod
    def get_out_src_labels(cls):
        return cls.__OUT_SRCS
    @classmethod
    def build_out_src(cls, target, src):
        if target not in cls.__OUT_TARGETS:
            raise ValueError('Invalid argument for output.')
        if src not in cls.__OUT_SRCS:
            raise ValueError('Invalid argument for source of output.')
        return cls.__build_args(target, src)

    @classmethod
    def get_cap_labels(cls):
        return cls.__CAP_TARGETS
    @classmethod
    def get_cap_src_labels(cls):
        return cls.__CAP_SRCS
    @classmethod
    def build_cap_src(cls, target, src):
        if target not in cls.__CAP_TARGETS:
            raise ValueError('Invalid argument for capture.')
        if src not in cls.__CAP_SRCS:
            raise ValueError('Invalid argument for source of capture.')
        return cls.__build_args(target, src)

    @classmethod
    def get_hp_labels(cls):
        return list(cls.__HP_TARGETS.keys())
    @classmethod
    def get_hp_src_labels(cls):
        return list(cls.__HP_SRCS.keys())
    @classmethod
    def build_hp_src(cls, target, src):
        if target not in cls.__HP_TARGETS:
            raise ValueError('Invalid argument for heaphone.')
        if src not in cls.__HP_SRCS:
            raise ValueError('Invalid argument for source of headphone.')
        args = bytearray()
        args.append(VendorCmd.HP_SRC.value)
        args.append(cls.__HP_TARGETS[target])
        args.append(cls.__HP_SRCS[src])
        return args


class StatusCmd():
    __IN_KNOBS = {
        # name: (value-pos, selected-value, peak-pos)
        # 0x7f - 0x00
        'mic-1':    (0, 0x00, 12),
        'mic-2':    (1, 0x08, 13),
        'mic-3':    (2, 0x10, 14),
        'mic-4':    (3, 0x18, 15),
    }
    __OUT_KNOBS = {
        # name: (value-pos, selected-mask)
        # 0x7f - 0x00
        'main':     (7, 0x01),
        'hp-1':     (6, 0x02),
        'hp-2':     (5, 0x04),
    }

    @staticmethod
    def __build_db_from_val(val):
        if val > 256:
            raise ValueError('Invalid argument for linear value.')
        if val > 0x7f:
            db = (0xff - val)
        else:
            db = -val
        return float(db)

    @classmethod
    def build_status(cls):
        args = bytearray()
        args.append(VendorCmd.HW_STATUS.value)
        args.append(0x01)
        return args

    @classmethod
    def parse_params(cls, resps):
        status = {}
        for label, params in cls.__IN_KNOBS.items():
            val_pos, sel_val, peak_pos = params
            db = cls.__build_db_from_val(resps[val_pos])
            status[label] = (db, bool(resps[peak_pos] > 0x00))
            if resps[4] & 0x18 == sel_val:
                status['in-knob'] = (label, resps[8])
        for label, params in cls.__OUT_KNOBS.items():
            val_pos, sel_mask = params
            db = cls.__build_db_from_val(resps[val_pos])
            status[label] = db
            if resps[4] & sel_mask:
                status['out-knob'] = (label, resps[9])
        return status


class KnobCmd():
    __TARGETS = {
        'main': 0x00,
        'hp-1': 0x01,
        'hp-2': 0x02,
    }

    __DB_MIN = -127.0
    __DB_MAX = 0.0

    @classmethod
    def __parse_val_from_db(cls, db):
        if db < cls.__DB_MIN or db > cls.__DB_MAX:
            raise ValueError('Invalid argument for dB.')
        return int(-db)

    @classmethod
    def get_knob_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def build_vol(cls, target, db):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for output.')
        val = cls.__parse_val_from_db(db)

        args = bytearray()
        args.append(VendorCmd.KNOB_VALUE.value)
        args.append(cls.__TARGETS[target])
        args.append(val)
        return args


class SpdifResampleCmd():
    __IFACES = {
        'optical':  0x00,
        'coaxial':  0x01,
    }
    __DIRECTIONS = {
        'output':   0x00,
        'input':    0x01,
    }
    __RATES = {
        44100:  0x01,
        48000:  0x02,
        88200:  0x04,
        96000:  0x08,
        176400: 0x10,
        192000: 0x20,
    }

    @classmethod
    def create_cache(cls):
        cache = {
            'state':        False,
            'iface':        'optical',
            'direction':    'output',
            'rate':         44100,
        }
        return cache

    @classmethod
    def get_iface_labels(cls):
        return list(cls.__IFACES.keys())
    @classmethod
    def get_direction_labels(cls):
        return list(cls.__DIRECTIONS.keys())
    @classmethod
    def get_rate_labels(cls):
        return list(cls.__RATES.keys())
    @classmethod
    def build_args(cls, enable, iface, direction, rate):
        if not isinstance(enable, bool):
            raise ValueError('Invalid argument for state.')
        if iface not in cls.__IFACES:
            raise ValueError('Invalid argument for iface.')
        if direction not in cls.__DIRECTIONS:
            raise ValueError('Invalid argument for direction.')
        if rate not in cls.__RATES:
            raise ValueError('Invalid argument for rate.')
        args = bytearray(5)
        args[0] = VendorCmd.SPDIF_RESAMPLE.value
        args[1] = 0x01 if enable else 0x00
        args[2] = cls.__IFACES[iface]
        args[3] = cls.__DIRECTIONS[direction]
        args[4] = cls.__RATES[rate]
        return args
