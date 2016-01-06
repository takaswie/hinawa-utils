#!/usr/bin/env python3

import sys

from gi.repository import Hinawa
from ta1394.general import AvcGeneral
from ta1394.general import AvcConnection
from ta1394.streamformat import AvcStreamFormat

argv = sys.argv
argc = len(argv)

if argc < 2:
	print('help')

card = argv[1]

class Fireone(Hinawa.SndUnit):
    # Available parameters
    display_modes = ('always-off', 'always-on', 'breathe', 'metronome',
                     'MIDI-clock-rotate', 'MIDI-clock-flash', 'jog-slow-rotate',
                     'jog-track')
    control_modes = ('native', 'Mackie HUI emulation')
    input_modes = ('stereo', 'monoral')
    supported_sampling_rates = (32000, 44100, 48000, 88200, 96000)

    # For AV/C vendor dependent command
    company_ids = bytes([0x00, 0x02, 0x2e])

    def __init__(self, card):
        super().__init__()
        self.open('/dev/snd/hwC{0}D0'.format(card))
        self.listen()

    def command_set_param(self, cmd, param):
        deps = bytearray()
        deps.append(0x46)
        deps.append(0x49)
        deps.append(0x31)
        deps.append(cmd)
        deps.append(param)
        AvcGeneral.set_vendor_dependent(unit, self.company_ids, deps)

    def command_get_param(self, cmd):
        deps = bytearray()
        deps.append(0x46)
        deps.append(0x49)
        deps.append(0x31)
        deps.append(cmd)
        deps.append(0xff)
        params = AvcGeneral.get_vendor_dependent(unit, self.company_ids, deps)
        return params[4]

    def display_set_mode(self, arg):
        if self.display_modes.count(arg) == 0:
            raise ValueError('Invalid argument for display mode')
        self.command_set_param(0x10, self.display_modes.index(arg))

    def display_get_mode(self):
        param = self.command_get_param(0x10)
        if param >= len(self.display_modes):
            raise IOError
        return self.display_modes[param]

    def control_set_mode(self, arg):
        if self.control_modes.count(arg) == 0:
            raise ValueError('Invalid argument for control mode')
        self.command_set_param(0x11, self.control_modes.index(arg))
            
    def control_get_mode(self):
        param = self.command_get_param(0x11)
        if param >= len(self.control_modes):
            raise IOError
        return self.control_modes[param]

    def input_set_mode(self, arg):
        if self.input_modes.count(arg) == 0:
            raise ValueError('Invalid argument for input mode')
        self.command_set_param(0x12, self.input_modes.index(arg))

    def input_get_mode(self):
        param = self.command_get_param(0x12)
        if param >= len(self.input_modes):
            raise IOError
        return self.input_modes[param]

    def firmware_get_version(self):
        return self.command_get_param(0x13)

unit = Fireone(card)
"""
print(unit.display_get_mode())
print(unit.control_get_mode())
print(unit.input_get_mode())
print(unit.firmware_get_version())

for rate in AvcGeneral.sampling_rates:
    if AvcGeneral.ask_plug_signal_format(unit, 'input',  0, rate):
        print(rate)
    if AvcGeneral.ask_plug_signal_format(unit, 'output', 0, rate):
        print(rate)
"""
print(AvcStreamFormat.get_format(unit, 'input', 0))
