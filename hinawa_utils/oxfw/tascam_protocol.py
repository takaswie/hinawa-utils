# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto

from enum import Enum

import gi
gi.require_version('Hinawa', '4.0')
from gi.repository import Hinawa

from hinawa_utils.ta1394.general import AvcGeneral


class VendorCmd(Enum):
    DISPLAY_MODE = 0x10
    CONTROL_MODE = 0x11
    INPUT_MODE = 0x12
    FIRMWARE_VER = 0x13


class TascamProtocol():
    __OUI = (0x00, 0x02, 0x2e)      # TEAC Corporation.

    __PREFIX = (0x46, 0x49, 0x31)   # FI1

    __PARAMS = {
        VendorCmd.DISPLAY_MODE: {
            'always-off':           0x00,
            'always-on':            0x01,
            'breathe':              0x02,
            'metronome':            0x03,
            'MIDI-clock-rotate':    0x04,
            'MIDI-clock-flash':     0x05,
            'jog-slow-rotate':      0x06,
            'jog-track':            0x07,
        },
        VendorCmd.CONTROL_MODE: {
            'native':               0x00,
            'mackie-HUI-emulation': 0x01,
        },
        VendorCmd.INPUT_MODE: {
            'stereo':   0x00,
            'monaural': 0x01,
        },
    }

    @classmethod
    def __command_set(cls, fcp, cmd, key, name):
        if key not in cls.__PARAMS[cmd]:
            raise ValueError('Invalid argument for {0}.'.format(name))
        data = bytearray()
        data.extend(cls.__PREFIX)
        data.append(cmd.value)
        data.append(cls.__PARAMS[cmd][key])
        try:
            AvcGeneral.set_vendor_dependent(fcp, cls.__OUI, data)
            # The response frame includes wrong __OUI and __PREFIX.
        except Exception as e:
            # The response code is 0x0c, against control requect (0x00).
            if str(e) != 'Unknown status':
                raise e

    @classmethod
    def __command_get(cls, fcp, cmd, name):
        data = bytearray()
        data.extend(cls.__PREFIX)
        data.append(cmd.value)
        data.append(0xff)
        resp = AvcGeneral.get_vendor_dependent(fcp, cls.__OUI, data)
        # The response frame includes wrong __OUI and __PREFIX.
        for key, val in cls.__PARAMS[cmd].items():
            if val == resp[4]:
                return key
        raise OSError('Invalid argument for {0}.'.format(name))

    @classmethod
    def get_display_mode_labels(cls):
        return list(cls.__PARAMS[VendorCmd.DISPLAY_MODE].keys())

    @classmethod
    def set_display_mode(cls, fcp: Hinawa.FwFcp, mode: str):
        cls.__command_set(fcp, VendorCmd.DISPLAY_MODE, mode,
                          'mode of display')

    @classmethod
    def get_display_mode(cls, fcp: Hinawa.FwFcp):
        return cls.__command_get(fcp, VendorCmd.DISPLAY_MODE,
                                 'mode of display')

    @classmethod
    def get_control_mode_labels(cls):
        return list(cls.__PARAMS[VendorCmd.CONTROL_MODE].keys())

    @classmethod
    def set_control_mode(cls, fcp: Hinawa.FwFcp, mode: str):
        cls.__command_set(fcp, VendorCmd.CONTROL_MODE, mode,
                          'mode of control')

    @classmethod
    def get_control_mode(cls, fcp: Hinawa.FwFcp):
        return cls.__command_get(fcp, VendorCmd.CONTROL_MODE,
                                 'mode of control')

    @classmethod
    def get_input_mode_labels(cls):
        return list(cls.__PARAMS[VendorCmd.INPUT_MODE].keys())

    @classmethod
    def set_input_mode(cls, fcp: Hinawa.FwFcp, mode: str):
        cls.__command_set(fcp, VendorCmd.INPUT_MODE, mode,
                          'mode of input')

    @classmethod
    def get_input_mode(cls, fcp: Hinawa.FwFcp):
        return cls.__command_get(fcp, VendorCmd.INPUT_MODE,
                                 'mode of input')

    @classmethod
    def get_firmware_version(cls, fcp: Hinawa.FwFcp):
        data = bytearray()
        data.extend(cls.__PREFIX)
        data.append(VendorCmd.FIRMWARE_VER.value)
        data.append(0xff)
        resp = AvcGeneral.get_vendor_dependent(fcp, cls.__OUI, data)
        # The response frame includes wrong __OUI and __PREFIX.
        return resp[4]
