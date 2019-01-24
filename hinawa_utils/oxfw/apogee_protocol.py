# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto

from enum import Enum
from struct import pack, unpack

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from hinawa_utils.ta1394.general import AvcGeneral

__all__ = ['MicCmd', 'InputCmd', 'OutputCmd', 'MixerCmd', 'DisplayCmd',
           'KnobCmd']


class VendorCmd(Enum):
    MIC_POLARITY = 0x00
    IN_LEVEL = 0x01
    IN_ATTR = 0x02
    MIC_POWER = 0x03
    OUT_ATTR = 0x04
    IN_GAIN = 0x05
    HW_STATUS = 0x07
    # Unknown: 0x08
    OUT_MUTE = 0x09
    IN_SRC = 0x0c
    MIXER_SRC = 0x10
    OUT_SRC = 0x11
    DISPLAY_OVERHOLD = 0x13
    DISPLAY_CLEAR = 0x14
    OUT_VOLUME = 0x15
    # Out mute is engaged for speaker: 0x16
    # Out mute is engaged for headphone: 0x17
    # Out mute is not engaged for speaker: 0x18
    # Out mute is not engaged for headphone: 0x19
    DISPLAY_TARGET = 0x1b
    IN_CLICKLESS = 0x1e
    DISPLAY_FOLLOW = 0x22


class ApogeeProtocol():
    __OUI = (0x00, 0x03, 0xdb)

    @classmethod
    def __command_req(cls, fcp, cmd, args, func_name):
        funcs = {
            'set':  AvcGeneral.set_vendor_dependent,
            'get':  AvcGeneral.get_vendor_dependent,
        }

        data = bytearray(4)
        data[0] = 0x50    # P
        data[1] = 0x43    # C
        data[2] = 0x4d    # M
        data[3] = cmd.value
        if args:
            data += args

        if len(data) < 10:
            for i in range(10 - len(data)):
                data.append(0x00)

        resp = funcs[func_name](fcp, cls.__OUI, data)
        if resp[0:4] != data[0:4]:
            raise ValueError('Unexpected response against request.')

        return resp[4:]

    @classmethod
    def command_set(cls, fcp: Hinawa.FwFcp, cmd: VendorCmd, args: bytearray):
        return cls.__command_req(fcp, cmd, args, 'set')

    @classmethod
    def command_get(cls, fcp: Hinawa.FwFcp, cmd: VendorCmd, args: bytearray):
        return cls.__command_req(fcp, cmd, args, 'get')


class MicCmd():
    __TARGETS = {
        'mic-1':    0x00,
        'mic-2':    0x01,
    }

    __PARAMS = {
        True:   0x60,
        False:  0x70,
    }

    @classmethod
    def get_mic_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def __command_set(cls, fcp, cmd, target, params, val):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for mic.')
        if val not in params:
            raise ValueError('Invalid ardument for mic command.')
        args = bytearray(3)
        args[0] = 0x80
        args[1] = cls.__TARGETS[target]
        args[2] = params[val]
        ApogeeProtocol.command_set(fcp, cmd, args)

    @classmethod
    def __command_get(cls, fcp, cmd, target, params):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for mic.')
        args = bytearray(3)
        args[0] = 0x80
        args[1] = cls.__TARGETS[target]
        args[2] = 0xff
        resp = ApogeeProtocol.command_get(fcp, cmd, args)
        for key, val in params.items():
            if resp[2] == val:
                return key
        raise OSError('Unexpected response for mic command.')

    @classmethod
    def set_polarity(cls, fcp: Hinawa.FwFcp, target: str, enable: bool):
        cls.__command_set(fcp, VendorCmd.MIC_POLARITY, target,
                          cls.__PARAMS, enable)

    @classmethod
    def get_polarity(cls, fcp: Hinawa.FwFcp, target: str):
        return cls.__command_get(fcp, VendorCmd.MIC_POWER, target,
                                 cls.__PARAMS)

    @classmethod
    def set_power(cls, fcp: Hinawa.FwFcp, target: str, enable: bool):
        cls.__command_set(fcp, VendorCmd.MIC_POLARITY, target,
                          cls.__PARAMS, enable)

    @classmethod
    def get_power(cls, fcp: Hinawa.FwFcp, target: str):
        return cls.__command_get(fcp, VendorCmd.MIC_POWER, target,
                                 cls.__PARAMS)


class InputCmd():
    __ADDR_IN_METERS = 0xfffff0080004

    __TARGETS = {
        'analog-1': 0x00,
        'analog-2': 0x01,
    }

    __ATTRS = {
        '+4dB':     0x60,
        '-10dB':    0x70,
    }

    __CLICKLESS = {
        True:   0x60,
        False:  0x70,
    }

    __LEVELS = {
        'line':         0x60,
        'instrument':   0x70,
    }

    __SRCS = {
        'mic':  0x60,
        'line': 0x70,
    }

    @classmethod
    def get_target_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def get_attr_labels(cls):
        return list(cls.__ATTRS.keys())

    @classmethod
    def __command_set(cls, fcp, cmd, target, params, key):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for input.')
        if key not in params:
            raise ValueError('Invalid argument for input command.')
        args = bytearray(3)
        args[0] = 0x80
        args[1] = cls.__TARGETS[target]
        args[2] = params[key]
        ApogeeProtocol.command_set(fcp, cmd, args)

    @classmethod
    def __command_get(cls, fcp, cmd, target, params):
        if target not in cls.__TARGETS:
            raise ValueError('Invalid argument for input.')
        args = bytearray(3)
        args[0] = 0x80
        args[1] = cls.__TARGETS[target]
        args[2] = 0xff
        resp = ApogeeProtocol.command_get(fcp, cmd, args)
        for key, val in params.items():
            if val == resp[2]:
                return key
        raise OSError('Unexpected response for input command.')

    @classmethod
    def set_attr(cls, fcp: Hinawa.FwFcp, target: str, attr: str):
        cls.__command_set(fcp, VendorCmd.IN_ATTR, target, cls.__ATTRS, attr)

    @classmethod
    def get_attr(cls, fcp: Hinawa.FwFcp, target: str):
        return cls.__command_get(fcp, VendorCmd.IN_ATTR, target, cls.__ATTRS)

    @classmethod
    def get_level_labels(cls):
        return list(cls.__LEVELS.keys())

    @classmethod
    def set_level(cls, fcp: Hinawa.FwFcp, target: str, level: str):
        cls.__command_set(fcp, VendorCmd.IN_LEVEL, target, cls.__LEVELS, level)

    @classmethod
    def get_level(cls, fcp: Hinawa.FwFcp, target: str):
        return cls.__command_get(fcp, VendorCmd.IN_LEVEL, target, cls.__LEVELS)

    @classmethod
    def get_src_labels(cls):
        return list(cls.__SRCS.keys())

    @classmethod
    def set_src(cls, fcp: Hinawa.FwFcp, target: str, src: str):
        cls.__command_set(fcp, VendorCmd.IN_SRC, target, cls.__SRCS, src)

    @classmethod
    def get_src(cls, fcp: Hinawa.FwFcp, target: str):
        return cls.__command_get(fcp, VendorCmd.IN_SRC, target, cls.__SRCS)

    @classmethod
    def set_clickless(cls, fcp: Hinawa.FwFcp, enable: bool):
        args = bytearray(3)
        args[0] = 0x80
        args[1] = 0x00
        args[2] = cls.__CLICKLESS[enable]
        ApogeeProtocol.command_set(fcp, VendorCmd.IN_CLICKLESS, args)

    @classmethod
    def get_clickless(cls, fcp: Hinawa.FwFcp):
        args = bytearray(3)
        args[0] = 0x80
        args[1] = 0x00
        args[2] = 0xff
        resp = ApogeeProtocol.command_get(fcp, VendorCmd.IN_CLICKLESS, args)
        for key, val in cls.__CLICKLESS.items():
            if val == resp[2]:
                return key
        raise OSError('Unexpected response for clickless operation.')

    @classmethod
    def set_gain(cls, fcp: Hinawa.FwFcp, target: str, db: float):
        args = bytearray(3)
        args[0] = 0x80
        args[1] = cls.__TARGETS[target]
        args[2] = int(db * 0x4f / 75)
        ApogeeProtocol.command_set(fcp, VendorCmd.IN_GAIN, args)

    @classmethod
    def get_gain(cls, fcp: Hinawa.FwFcp, target: str):
        args = bytearray(3)
        args[0] = 0x80
        args[1] = cls.__TARGETS[target]
        args[2] = 0xff
        # TODO: this doesn't work.
        resp = ApogeeProtocol.command_get(fcp, VendorCmd.IN_GAIN, args)
        return float(resp[2] * 75 / 0x4f)

    @classmethod
    def get_meters(cls, unit: Hinawa.FwUnit):
        req = Hinawa.FwReq()
        frames = req.read(unit, cls.__ADDR_IN_METERS, 8)
        vals = unpack('>2I', frames)
        meters = {
            'analog-1': vals[0],
            'alaong-2': vals[1],
        }
        return meters


class OutputCmd():
    __ATTRS = {
        'instrument':   0x60,
        '-10dB':        0x70,
    }

    __MUTES = {
        False:  0x60,
        True:   0x70,
    }

    __SRCS = {
        'stream-1/2':   0x60,
        'mixer-1/2':    0x70,
    }

    @classmethod
    def get_attr_labels(cls):
        return list(cls.__ATTRS.keys())

    @classmethod
    def __command_set(cls, fcp, cmd, params, key):
        if key not in params:
            raise ValueError('Invalid argument for output command.')
        args = bytearray(3)
        args[0] = 0x80
        args[1] = 0x80
        args[2] = params[key]
        ApogeeProtocol.command_set(fcp, cmd, args)

    @classmethod
    def __command_get(cls, fcp, cmd, params):
        args = bytearray(3)
        args[0] = 0x80
        args[1] = 0x80
        args[2] = 0xff
        resp = ApogeeProtocol.command_get(fcp, cmd, args)
        for key, val in params.items():
            if resp[2] == val:
                return key
        raise OSError('Unexpected response to output command.')

    @classmethod
    def set_attr(cls, fcp: Hinawa.FwFcp, attr: str):
        cls.__command_set(fcp, VendorCmd.OUT_ATTR, cls.__ATTRS,
                          attr)

    @classmethod
    def get_attr(cls, fcp: Hinawa.FwFcp):
        return cls.__command_get(fcp, VendorCmd.OUT_ATTR, cls.__ATTRS)

    @classmethod
    def set_mute(cls, fcp: Hinawa.FwFcp, enable: bool):
        cls.__command_set(fcp, VendorCmd.OUT_MUTE, cls.__MUTES, enable)

    @classmethod
    def get_mute(cls, fcp: Hinawa.FwFcp):
        return cls.__command_get(fcp, VendorCmd.OUT_MUTE, cls.__MUTES)

    @classmethod
    def get_out_src_labels(cls):
        return list(cls.__SRCS.keys())

    @classmethod
    def set_out_src(cls, fcp: Hinawa.FwFcp, src: str):
        cls.__command_set(fcp, VendorCmd.OUT_SRC, cls.__SRCS, src)

    @classmethod
    def get_out_src(cls, fcp: Hinawa.FwFcp):
        return cls.__command_get(fcp, VendorCmd.OUT_SRC, cls.__SRCS)

    @classmethod
    def set_volume(cls, fcp: Hinawa.FwFcp, db: float):
        val = int(-db * 0x64 / 48)
        args = bytearray(3)
        args[0] = 0x80
        args[1] = 0x80
        args[2] = val
        ApogeeProtocol.command_set(fcp, VendorCmd.OUT_VOLUME, args)

    @classmethod
    def get_volume(cls, fcp: Hinawa.FwFcp):
        args = bytearray(3)
        args[0] = 0x80
        args[1] = 0x80
        args[2] = 0xff
        resp = ApogeeProtocol.command_get(fcp, VendorCmd.OUT_VOLUME, args)
        return float(resp[2] * -48 / 0x64)


class MixerCmd():
    __ADDR_SRC_LEVELS = 0xfffff0080404

    __SRCS = {
        'stream-1': 0x00,
        'stream-2': 0x01,
        'analog-1': 0x10,
        'analog-2': 0x11,
    }

    @classmethod
    def __build_args(cls, src, ch):
        if src not in cls.__SRCS:
            raise ValueError('Invalid argument for source of mixer.')
        if ch not in (0, 1):
            raise ValueError('Invalid argument for channel of mixer.')
        args = bytearray()
        args.append(cls.__SRCS[src])
        args.append(ch)
        return args

    @classmethod
    def get_mixer_src_labels(cls):
        return list(cls.__SRCS.keys())

    @classmethod
    def set_src_gain(cls, fcp: Hinawa.FwFcp, src: str, ch: int, db: float):
        args = cls.__build_args(src, ch)

        val = int((db + 48) * 0x3fff / 48)
        vals = pack('>H', val)
        args.extend(vals)
        ApogeeProtocol.command_set(fcp, VendorCmd.MIXER_SRC, args)

    @classmethod
    def get_src_gain(cls, fcp: Hinawa.FwFcp, src: str, ch: int):
        args = cls.__build_args(src, ch)
        args.append(0xff)
        args.append(0xff)
        resp = ApogeeProtocol.command_get(fcp, VendorCmd.MIXER_SRC, args)
        val = unpack('>H', resp[2:4])[0]
        return float(48 * val / 0x3fff - 48)

    @classmethod
    def get_meters(cls, unit: Hinawa.FwUnit):
        req = Hinawa.FwReq()
        frames = req.read(unit, cls.__ADDR_SRC_LEVELS, 16)
        vals = unpack('>4I', frames)
        meters = {
            'stream-1': vals[0],
            'stream-2': vals[1],
            'analog-1': vals[2],
            'alaong-2': vals[3],
        }
        return meters


class DisplayCmd():
    __TARGETS = {
        'output':   0x60,
        'input':    0x70,
    }

    __OVERHOLDS = {
        'infinite': 0x60,
        '2sec':     0x70,
    }

    __FOLLOWS = {
        False:   0x60,
        True:    0x70,
    }

    @classmethod
    def __command_set(cls, fcp, cmd, params, key):
        if key not in params:
            raise ValueError('Invalid argument for display command.')
        args = bytearray(3)
        args[0] = 0x80
        args[1] = 0x00
        args[2] = params[key]
        ApogeeProtocol.command_set(fcp, cmd, args)

    @classmethod
    def __command_get(cls, fcp, cmd, params):
        args = bytearray(3)
        args[0] = 0x80
        args[1] = 0x00
        args[2] = 0xff
        resp = ApogeeProtocol.command_get(fcp, cmd, args)
        for key, val in params.items():
            if resp[2] == val:
                return key
        raise OSError('Unexpected response for display command.')

    @classmethod
    def get_target_labels(cls):
        return list(cls.__TARGETS.keys())

    @classmethod
    def set_target(cls, fcp: Hinawa.FwFcp, target: str):
        cls.__command_set(fcp, VendorCmd.DISPLAY_TARGET, cls.__TARGETS, target)

    @classmethod
    def get_target(cls, fcp: Hinawa.FwFcp):
        return cls.__command_get(fcp, VendorCmd.DISPLAY_TARGET, cls.__TARGETS)

    @classmethod
    def get_overhold_labels(cls):
        return list(cls.__OVERHOLDS.keys())

    @classmethod
    def set_overhold(cls, fcp: Hinawa.FwFcp, overhold: str):
        cls.__command_set(fcp, VendorCmd.DISPLAY_OVERHOLD, cls.__OVERHOLDS,
                          overhold)

    @classmethod
    def get_overhold(cls, fcp: Hinawa.FwFcp):
        return cls.__command_get(fcp, VendorCmd.DISPLAY_OVERHOLD,
                                 cls.__OVERHOLDS)

    @classmethod
    def set_follow(cls, fcp: Hinawa.FwFcp, enable: bool):
        cls.__command_set(fcp, VendorCmd.DISPLAY_FOLLOW, cls.__FOLLOWS, enable)

    @classmethod
    def get_follow(cls, fcp: Hinawa.FwFcp):
        return cls.__command_get(fcp, VendorCmd.DISPLAY_FOLLOW, cls.__FOLLOWS)

    @classmethod
    def reset_meters(cls, fcp: Hinawa.FwFcp):
        cls.__command_set(fcp, VendorCmd.DISPLAY_CLEAR, {True: 0x70}, True)


class KnobCmd():
    __KNOBS = {
        # label: (selected, val_pos)
        'OUT':  (0x00, 5),
        'IN-1': (0x01, 6),
        'IN-2': (0x02, 7),
    }

    @classmethod
    def get_states(cls, fcp: Hinawa.FwFcp):
        args = bytearray()
        args.append(VendorCmd.HW_STATUS.value)
        resp = ApogeeProtocol.command_get(fcp, VendorCmd.HW_STATUS, None)
        states = {}
        for label, params in cls.__KNOBS.items():
            selected, val_pos = params
            states[label] = resp[val_pos]
            if selected == resp[3]:
                states['knob'] = label
        states['mute'] = bool(resp[2] > 0)
        return states
