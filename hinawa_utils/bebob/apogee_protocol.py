# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from struct import pack
from enum import Enum

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from hinawa_utils.ta1394.general import AvcGeneral

__all__ = ['HwCmd', 'DisplayCmd', 'OptIfaceCmd', 'MicCmd', 'InputCmd',
           'OutputCmd', 'MixerCmd', 'RouteCmd', 'KnobCmd', 'SpdifResampleCmd']


class VendorCmd(Enum):
    INPUT_LIMIT = 0xe4
    MIC_POWER = 0xe5
    IO_ATTR = 0xe8
    IO_ROUTING = 0xef
    HW = 0xeb
    HP_SRC = 0xab
    MIXER_SRC1 = 0xb0
    MIXER_SRC2 = 0xb1
    MIXER_SRC3 = 0xb2
    MIXER_SRC4 = 0xb3
    OPT_IFACE_MODE = 0xf1
    DOWNGRADE = 0xf2
    SPDIF_RESAMPLE = 0xf3
    MIC_POLARITY = 0xf5
    KNOB_VALUE = 0xf6
    HW_STATUS = 0xff


class HwCmdOp(Enum):
    STREAM_MODE = 0x06
    DISPLAY_ILLUMINATE = 0x08
    DISPLAY_MODE = 0x09
    DISPLAY_TARGET = 0x0a
    DISPLAY_OVERHOLD = 0x0e
    METER_RESET = 0x0f
    CD_MODE = 0xf5


class ApogeeProtocol():
    __OUI = (0x00, 0x03, 0xdb)

    @classmethod
    def command_set(cls, fcp: Hinawa.FwFcp, cmd: VendorCmd, args: bytearray):
        data = bytearray()
        data.append(cmd.value)

        if len(args) > 0:
            data.extend(args)

        # At least, 6 bytes should be required to align to 3 quadlets.
        # Unless, target unit is freezed.
        if len(data) < 6:
            for i in range(6 - len(data)):
                data.append(0x00)

        resps = AvcGeneral.set_vendor_dependent(fcp, cls.__OUI, data)
        if resps[0] != data[0]:
            raise OSError('Unexpected value for vendor-dependent command.')

        return resps[1:]


class HwCmd():
    __NAME = 'hw'

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
    def create_cache(cls, cache: dict):
        cache[cls.__NAME] = {
            'cd':       False,
            '16bit':    'none',
        }

    @classmethod
    def get_stream_mode_labels(cls):
        return list(cls.__STREAM_MODES.keys())

    @classmethod
    def set_stream_mode(cls, fcp: Hinawa.FwFcp, mode: str):
        if mode not in cls.__STREAM_MODES:
            raise ValueError('Invalid argument for mode of stream.')
        args = bytearray(2)
        args[0] = HwCmdOp.STREAM_MODE.value
        args[1] = cls.__STREAM_MODES[mode]
        ApogeeProtocol.command_set(fcp, VendorCmd.HW, args)

    @classmethod
    def set_cd_mode(cls, cache: dict, fcp: Hinawa.FwFcp, enable: bool):
        if not isinstance(enable, bool):
            raise ValueError('Invalid argument for mode of cd.')
        val = 0x01 if enable else 0x00

        args = bytearray(2)
        args[0] = HwCmdOp.CD_MODE.value
        args[1] = val
        ApogeeProtocol.command_set(fcp, VendorCmd.HW, args)
        cache[cls.__NAME]['cd'] = enable

    @classmethod
    def get_cd_mode(cls, cache: dict):
        return cache[cls.__NAME]['cd']

    @classmethod
    def get_16bit_mode_labels(cls):
        return list(cls.__DOWNGRADE_TARGETS.keys())

    @classmethod
    def set_16bit_mode(cls, cache: dict, fcp: Hinawa.FwFcp, target: str):
        if target not in cls.__DOWNGRADE_TARGETS:
            raise ValueError('Invalid argument for target of 16bit mode.')
        args = bytearray(1)
        args[0] = cls.__DOWNGRADE_TARGETS[target]
        ApogeeProtocol.command_set(fcp, VendorCmd.DOWNGRADE, args)
        cache[cls.__NAME]['16bit'] = target

    @classmethod
    def get_16bit_mode(cls, cache: dict):
        return cache[cls.__NAME]['16bit']


class DisplayCmd():
    __NAME = 'display'

    __TARGETS = {
        'output':   0x00,
        'input':    0x01,
    }

    @classmethod
    def create_cache(cls, cache: dict):
        cache[cls.__NAME] = {
            'illuminate': False,
            'mode': False,
            'target': 'output',
            'overhold': False,
        }

    @classmethod
    def get_target_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def __command_set(cls, fcp, op, val):
        args = bytearray(2)
        args[0] = op.value
        args[1] = val
        return ApogeeProtocol.command_set(fcp, VendorCmd.HW, args)

    @classmethod
    def set_illuminate(cls, cache: dict, fcp: Hinawa.FwFcp, enable: bool):
        if not isinstance(enable, bool):
            raise ValueError('Invalid argument for illuminate of display.')
        val = 0x01 if enable else 0x00
        cls.__command_set(fcp, HwCmdOp.DISPLAY_ILLUMINATE, val)
        cache[cls.__NAME]['illuminate'] = enable

    @classmethod
    def get_illuminate(cls, cache: dict):
        return cache[cls.__NAME]['illuminate']

    @classmethod
    def set_mode(cls, cache: dict, fcp: Hinawa.FwFcp, enable: bool):
        if not isinstance(enable, bool):
            raise ValueError('Invalid argument for mode of display.')
        val = 0x01 if enable else 0x00
        cls.__command_set(fcp, HwCmdOp.DISPLAY_MODE, val)
        cache[cls.__NAME]['mode'] = enable

    @classmethod
    def get_mode(cls, cache: dict):
        return cache[cls.__NAME]['mode']

    @classmethod
    def set_target(cls, cache: dict, fcp: Hinawa.FwFcp, target: str):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for target of display.')
        val = cls.__TARGETS[target]
        cls.__command_set(fcp, HwCmdOp.DISPLAY_TARGET, val)
        cache[cls.__NAME]['target'] = target

    @classmethod
    def get_target(cls, cache: dict):
        return cache[cls.__NAME]['target']

    @classmethod
    def set_overhold(cls, cache: dict, fcp: Hinawa.FwFcp, enable: bool):
        if not isinstance(enable, bool):
            raise ValueError('Invalid argument for overhold of display.')
        val = 0x01 if enable else 0x00
        cls.__command_set(fcp, HwCmdOp.DISPLAY_OVERHOLD, val)
        cache[cls.__NAME]['overhold'] = enable

    @classmethod
    def get_overhold(cls, cache: dict):
        return cache[cls.__NAME]['overhold']

    @classmethod
    def reset_meter(cls, fcp: Hinawa.FwFcp):
        cls.__command_set(fcp, HwCmdOp.METER_RESET, 0x00)


class OptIfaceCmd():
    __NAME = 'opt-iface'

    __TARGETS = {
        'output':   0x00,
        'input':    0x00,
    }
    __MODES = {
        'S/PDIF':       0x00,
        'ADAT/SMUX':    0x01,
    }

    @classmethod
    def create_cache(cls, cache: dict):
        cache[cls.__NAME] = {}
        for target in cls.__TARGETS:
            cache[cls.__NAME][target] = 'S/PDIF'

    @classmethod
    def get_target_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def get_mode_labels(cls):
        return list(cls.__MODES.keys())

    @classmethod
    def set_mode(cls, cache: dict, fcp: Hinawa.FwFcp, target: str, mode: str):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for target of optical iface.')
        if mode not in cls.__MODES:
            raise ValueError('Invalid argument for mode of optical iface.')
        args = bytearray(2)
        args[0] = cls.__TARGETS[target]
        args[1] = cls.__MODES[mode]
        ApogeeProtocol.command_set(fcp, VendorCmd.OPT_IFACE_MODE, args)
        cache[cls.__NAME][target] = mode

    @classmethod
    def get_mode(cls, cache: dict, target: str):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for optical iface.')
        return cache[cls.__NAME][target]


class MicCmd():
    __NAME = 'mic'

    __TARGETS = {
        'mic-1':    0x00,
        'mic-2':    0x01,
        'mic-3':    0x02,
        'mic-4':    0x03,
    }

    @classmethod
    def create_cache(cls, cache: dict):
        cache[cls.__NAME] = {}
        for item in ('power', 'polarity'):
            cache[cls.__NAME][item] = {}
            for target in cls.__TARGETS:
                cache[cls.__NAME][item][target] = False

    @classmethod
    def __command_set(cls, fcp, cmd, target, val):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for mic.')
        args = bytearray(2)
        args[0] = cls.__TARGETS[target]
        args[1] = val
        ApogeeProtocol.command_set(fcp, cmd, args)

    @classmethod
    def get_mic_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def set_power(cls, cache: dict, fcp: Hinawa.FwFcp, target: str, enable: bool):
        val = 0x01 if enable else 0x00
        cls.__command_set(fcp, VendorCmd.MIC_POWER, target, val)
        cache[cls.__NAME]['power'][target] = enable

    @classmethod
    def get_power(cls, cache: dict, target: str):
        if target not in MicCmd.get_mic_labels():
            raise ValueError('Invalid argument for mic.')
        return cache[cls.__NAME]['power'][target]

    @classmethod
    def set_polarity(cls, cache: dict, fcp: Hinawa.FwFcp, target: str,
                     invert: bool):
        val = 0x01 if invert else 0x00
        cls.__command_set(fcp, VendorCmd.MIC_POLARITY, target, val)
        cache[cls.__NAME]['polarity'][target] = invert

    @classmethod
    def get_polarity(cls, cache: dict, target: str):
        if target not in MicCmd.get_mic_labels():
            raise ValueError('Invalid argument for mic.')
        return cache[cls.__NAME]['polarity'][target]


class InputCmd():
    __NAME = 'input'

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
    def create_cache(cls, cache: dict):
        cache[cls.__NAME] = {
            'soft-limit': {},
            'attr': {},
        }
        for target in cls.__TARGETS:
            cache[cls.__NAME]['soft-limit'][target] = False
            cache[cls.__NAME]['attr'][target] = '-10dB'

    @classmethod
    def get_in_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def get_attr_labels(cls):
        return list(cls.__ATTRS.keys())

    @classmethod
    def set_soft_limit(cls, cache: dict, fcp: Hinawa.FwFcp, target, enable):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for line input.')
        val = 0x01 if enable else 0x00

        args = bytearray(2)
        args[0] = cls.__TARGETS[target]
        args[1] = val
        ApogeeProtocol.command_set(fcp, VendorCmd.INPUT_LIMIT, args)
        cache[cls.__NAME]['soft-limit'][target] = enable

    @classmethod
    def get_soft_limit(cls, cache: dict, target: str):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for line input.')
        return cache[cls.__NAME]['soft-limit'][target]

    @classmethod
    def set_attr(cls, cache: dict, fcp: Hinawa.FwFcp, target: str, attr: str):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for line input.')
        if attr not in cls.__ATTRS:
            raise ValueError('Invalid argument for in attenuation.')

        args = bytearray(3)
        args[0] = cls.__TARGETS[target]
        args[1] = 0x01  # input.
        args[2] = cls.__ATTRS[attr]
        ApogeeProtocol.command_set(fcp, VendorCmd.IO_ATTR, args)
        cache[cls.__NAME]['attr'][target] = attr

    @classmethod
    def get_attr(cls, cache: dict, target: str):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for line input.')
        return cache[cls.__NAME]['attr'][target]


class OutputCmd():
    __NAME = 'output'

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
    def create_cache(cls, cache: dict):
        cache[cls.__NAME] = {
            'attr': {},
        }
        for target in cls.__TARGETS:
            cache[cls.__NAME]['attr'][target] = '-10dB'

    @classmethod
    def get_target_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def get_attr_labels(cls):
        return list(cls.__ATTRS.keys())

    @classmethod
    def set_attr(cls, cache: dict, fcp: Hinawa.FwFcp, target: str, attr: str):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for line output.')
        if attr not in cls.__ATTRS:
            raise ValueError('Invalid argument for out attenuation.')

        args = bytearray(3)
        args[0] = cls.__TARGETS[target]
        args[1] = 0x00    # output.
        args[2] = cls.__ATTRS[attr]
        ApogeeProtocol.command_set(fcp, VendorCmd.IO_ATTR, args)
        cache[cls.__NAME]['attr'][target] = attr

    @classmethod
    def get_attr(cls, cache: dict, target):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for line output.')
        return cache[cls.__NAME]['attr'][target]


class MixerCmd():
    __NAME = 'mixer'

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
    def create_cache(cls, cache: dict):
        cache[cls.__NAME] = {}
        for target in cls.__TARGETS:
            right = True
            cache[cls.__NAME][target] = {}
            for cmd, srcs in cls.__SRCS.items():
                for src in srcs:
                    db = 0.0
                    balance = 100.0 if right else 0.0
                    cache[cls.__NAME][target][src] = [db, balance]
                    right = not right

    @classmethod
    def get_target_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def get_src_labels(cls):
        srcs = []
        for cmd, sources in cls.__SRCS.items():
            srcs.extend(sources)
        return srcs

    @classmethod
    def set_src_gain(cls, cache: dict, fcp: Hinawa.FwFcp, target: str, src: str,
                     db: float, balance: float):
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
            if s not in cache[cls.__NAME][target]:
                raise ValueError('Invalid argument for status cache.')

        args = bytearray()
        args.append(cmd.value)
        args.append(cls.__TARGETS[target])
        for s in srcs:
            if s == src:
                db, balance = data
            else:
                db, balance = cache[cls.__NAME][target][s]
            val = int(0xffff * (1 + db / 48))
            right = int(val * balance / 100)
            left = val - right
            args.extend(pack('<H', left))
            args.extend(pack('<H', right))

        ApogeeProtocol.command_set(fcp, cmd, args)
        cache[cls.__NAME][target][src] = data

    @classmethod
    def get_src_gain(cls, cache: dict, target: str, src: str):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for mixer.')
        for cmd, srcs in cls.__SRCS.items():
            if src in srcs:
                break
        else:
            raise ValueError('Invalid argument for source of mixer.')
        return list(cache[cls.__NAME][target][src])


class RouteCmd():
    __NAME = 'route'

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
    def create_cache(cls, cache: dict):
        cache[cls.__NAME] = {
            'out':  {},
            'cap':  {},
            'hp':   {},
        }
        for i, target in enumerate(cls.__OUT_TARGETS):
            src = cls.__OUT_SRCS[i + 8]
            cache[cls.__NAME]['out'][target] = src
        for i, target in enumerate(cls.__CAP_TARGETS):
            src = cls.__CAP_SRCS[i]
            cache[cls.__NAME]['cap'][target] = src
        for i, target in enumerate(cls.__HP_TARGETS):
            src = list(cls.__HP_SRCS.keys())[i]
            cache[cls.__NAME]['hp'][target] = src

    @classmethod
    def __command_set(cls, fcp, dst, src):
        args = bytearray(2)
        args[0] = cls.__PORTS[dst]
        args[1] = cls.__PORTS[src]
        ApogeeProtocol.command_set(fcp, VendorCmd.IO_ROUTING, args)

    @classmethod
    def get_out_labels(cls):
        return cls.__OUT_TARGETS

    @classmethod
    def get_out_src_labels(cls):
        return cls.__OUT_SRCS

    @classmethod
    def set_out_src(cls, cache: dict, fcp: Hinawa.FwFcp, target: str, src: str):
        if target not in cls.__OUT_TARGETS:
            raise ValueError('Invalid argument for output.')
        if src not in cls.__OUT_SRCS:
            raise ValueError('Invalid argument for source of output.')
        cls.__command_set(fcp, target, src)
        cache[cls.__NAME]['out'][target] = src

    @classmethod
    def get_out_src(cls, cache: dict, target: str):
        if target not in cls.__OUT_TARGETS:
            raise ValueError('Invalid argument for output.')
        return cache[cls.__NAME]['out'][target]

    @classmethod
    def get_cap_labels(cls):
        return cls.__CAP_TARGETS

    @classmethod
    def get_cap_src_labels(cls):
        return cls.__CAP_SRCS

    @classmethod
    def set_cap_src(cls, cache: dict, fcp: Hinawa.FwFcp, target: str, src: str):
        if target not in cls.__CAP_TARGETS:
            raise ValueError('Invalid argument for capture.')
        if src not in cls.__CAP_SRCS:
            raise ValueError('Invalid argument for source of capture.')
        cls.__command_set(fcp, target, src)
        cache[cls.__NAME]['cap'][target] = src

    @classmethod
    def get_cap_src(cls, cache: dict, target: str):
        if target not in RouteCmd.get_cap_labels():
            raise ValueError('Invalid argument for capture.')
        return cache[cls.__NAME]['cap'][target]

    @classmethod
    def get_hp_labels(cls):
        return list(cls.__HP_TARGETS.keys())

    @classmethod
    def get_hp_src_labels(cls):
        return list(cls.__HP_SRCS.keys())

    @classmethod
    def set_hp_src(cls, cache: dict, fcp: Hinawa.FwFcp, target: str, src: str):
        if target not in cls.__HP_TARGETS:
            raise ValueError('Invalid argument for heaphone.')
        if src not in cls.__HP_SRCS:
            raise ValueError('Invalid argument for source of headphone.')
        args = bytearray(2)
        args[0] = cls.__HP_TARGETS[target]
        args[1] = cls.__HP_SRCS[src]
        ApogeeProtocol.command_set(fcp, VendorCmd.HP_SRC, args)
        cache[cls.__NAME]['hp'][target] = src

    @classmethod
    def get_hp_src(cls, cache: dict, target: str):
        if target not in cls.__HP_TARGETS:
            raise ValueError('Invalid argument for heaphone.')
        return cache[cls.__NAME]['hp'][target]


class KnobCmd():
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
        'hp-1/2':   (6, 0x02),
        'hp-3/4':   (5, 0x04),
    }

    __TARGETS = {
        'main':     0x00,
        'hp-1/2':   0x01,
        'hp-3/4':   0x02,
    }

    __DB_MIN = -127.0
    __DB_MAX = 0.0

    @classmethod
    def __parse_val_from_db(cls, db):
        if db < cls.__DB_MIN or db > cls.__DB_MAX:
            raise ValueError('Invalid argument for dB.')
        return int(-db)

    @staticmethod
    def __build_val_to_db(val):
        if val > 256:
            raise ValueError('Invalid argument for linear value.')
        if val > 0x7f:
            db = (0xff - val)
        else:
            db = -val
        return float(db)

    @classmethod
    def get_knob_out_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def set_out_vol(cls, fcp: Hinawa.FwFcp, target: str, db: float):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for output.')
        val = cls.__parse_val_from_db(db)

        args = bytearray(2)
        args[0] = cls.__TARGETS[target]
        args[1] = val
        ApogeeProtocol.command_set(fcp, VendorCmd.KNOB_VALUE, args)

    @classmethod
    def get_states(cls, fcp: Hinawa.FwFcp):
        args = bytearray(1)
        args[0] = 0x01
        resp = ApogeeProtocol.command_set(fcp, VendorCmd.HW_STATUS, args)

        status = {}
        for label, params in cls.__IN_KNOBS.items():
            val_pos, sel_val, peak_pos = params
            db = cls.__build_val_to_db(resp[val_pos])
            status[label] = (db, bool(resp[peak_pos] > 0x00))
            if resp[4] & 0x18 == sel_val:
                status['in-knob'] = (label, resp[8])
        for label, params in cls.__OUT_KNOBS.items():
            val_pos, sel_mask = params
            db = cls.__build_val_to_db(resp[val_pos])
            status[label] = db
            if resp[4] & sel_mask:
                status['out-knob'] = (label, resp[9])
        return status


class SpdifResampleCmd():
    __NAME = 'spdif-resample'

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
    def create_cache(cls, cache: dict):
        cache[cls.__NAME] = (False, 'optical', 'output', 44100)

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
    def set_params(cls, cache: dict, fcp: Hinawa.FwFcp, enable: bool, iface: str,
                   direction: str, rate: int):
        if not isinstance(enable, bool):
            raise ValueError('Invalid argument for state.')
        if iface not in cls.__IFACES:
            raise ValueError('Invalid argument for iface.')
        if direction not in cls.__DIRECTIONS:
            raise ValueError('Invalid argument for direction.')
        if rate not in cls.__RATES:
            raise ValueError('Invalid argument for rate.')
        args = bytearray(4)
        args[0] = 0x01 if enable else 0x00
        args[1] = cls.__IFACES[iface]
        args[2] = cls.__DIRECTIONS[direction]
        args[3] = cls.__RATES[rate]
        ApogeeProtocol.command_set(fcp, VendorCmd.SPDIF_RESAMPLE, args)
        cache[cls.__NAME] = (enable, iface, direction, rate)

    @classmethod
    def get_params(cls, cache: dict):
        return list(cache[cls.__NAME])
