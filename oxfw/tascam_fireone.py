from gi.repository import Hinawa

from oxfw.oxfw_unit import OxfwUnit

from ta1394.general import AvcGeneral

class TascamFireone(OxfwUnit):
    # Available parameters
    display_modes = ('always-off', 'always-on', 'breathe', 'metronome',
                     'MIDI-clock-rotate', 'MIDI-clock-flash', 'jog-slow-rotate',
                     'jog-track')
    control_modes = ('native', 'mackie-HUI-emulation')
    input_modes = ('stereo', 'monaural')

    def __init__(self, path):
        super().__init__(path)
        unit_info = AvcGeneral.get_unit_info(self.fcp)
        self.company_ids = unit_info['company-id']

    def command_set_param(self, cmd, param):
        deps = bytearray()
        deps.append(0x46)
        deps.append(0x49)
        deps.append(0x31)
        deps.append(cmd)
        deps.append(param)
        try:
            AvcGeneral.set_vendor_dependent(self.fcp, self.company_ids, deps)
        except Exception as e:
            if str(e) != 'Unknown status':
                raise e

    def command_get_param(self, cmd):
        deps = bytearray()
        deps.append(0x46)
        deps.append(0x49)
        deps.append(0x31)
        deps.append(cmd)
        deps.append(0xff)
        params = AvcGeneral.get_vendor_dependent(self.fcp, self.company_ids,
                                                 deps)
        return params[4]

    def display_set_mode(self, arg):
        if self.display_modes.count(arg) == 0:
            raise ValueError('Invalid argument for display mode')
        self.command_set_param(0x10, self.display_modes.index(arg))

    def display_get_mode(self):
        param = self.command_get_param(0x10)
        if param >= len(self.display_modes):
            raise OSError('Unexpected value in FCP response')
        return self.display_modes[param]

    def control_set_mode(self, arg):
        if self.control_modes.count(arg) == 0:
            raise ValueError('Invalid argument for control mode')
        self.command_set_param(0x11, self.control_modes.index(arg))
            
    def control_get_mode(self):
        param = self.command_get_param(0x11)
        if param >= len(self.control_modes):
            raise OSError('Unexpected value in FCP response')
        return self.control_modes[param]

    def input_set_mode(self, arg):
        if self.input_modes.count(arg) == 0:
            raise ValueError('Invalid argument for input mode')
        self.command_set_param(0x12, self.input_modes.index(arg))

    def input_get_mode(self):
        param = self.command_get_param(0x12)
        if param >= len(self.input_modes):
            raise OSError('Unexpected value in FCP response')
        return self.input_modes[param]

    def firmware_get_version(self):
        return self.command_get_param(0x13)
