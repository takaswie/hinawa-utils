# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto

from hinawa_utils.oxfw.oxfw_unit import OxfwUnit

from hinawa_utils.oxfw.apogee_protocol import (
    MicCmd, InputCmd, OutputCmd, MixerCmd, DisplayCmd, KnobCmd,
)

__all__ = ['ApogeeDuetUnit']


class ApogeeDuetUnit(OxfwUnit):
    def __init__(self, path):
        super().__init__(path)

        if (self.vendor_name != 'Apogee Electronics' or
                self.model_name != 'Duet'):
            raise ValueError('Unsupported model: {0}, {1}'.format(
                                            self.vendor_name, self.model_name))

    #
    # Mic configurations.
    #
    def get_mic_labels(self):
        return MicCmd.get_mic_labels()

    def set_mic_polarity(self, target: str, enable: bool):
        MicCmd.set_polarity(self.fcp, target, enable)

    def get_mic_polarity(self, target: str):
        return MicCmd.get_polarity(self.fcp, target)

    def set_mic_power(self, target: str, enable: bool):
        MicCmd.set_power(self.fcp, target, enable)

    def get_mic_power(self, target: str):
        return MicCmd.get_power(self.fcp, target)

    #
    # Input configurations.
    #
    def get_in_labels(self):
        return InputCmd.get_target_labels()

    def get_in_level_labels(self):
        return InputCmd.get_level_labels()

    def set_in_level(self, target, level):
        InputCmd.set_level(self.fcp, target, level)

    def get_in_level(self, target):
        return InputCmd.get_level(self.fcp, target)

    def get_in_attr_labels(self):
        return InputCmd.get_attr_labels()

    def set_in_attr(self, target, attr):
        InputCmd.set_attr(self.fcp, target, attr)

    def get_in_attr(self, target):
        return InputCmd.get_attr(self.fcp, target)

    def get_in_src_labels(self):
        return InputCmd.get_src_labels()

    def set_in_src(self, target, src):
        InputCmd.set_src(self.fcp, target, src)

    def get_in_src(self, target):
        return InputCmd.get_src(self.fcp, target)

    def set_in_gain(self, target: str, db: float):
        InputCmd.set_gain(self.fcp, target, db)

    def get_in_gain(self, target: str):
        return InputCmd.get_gain(self.fcp, target)

    def set_in_clickless(self, enable):
        InputCmd.set_clickless(self.fcp, enable)

    def get_in_clickless(self):
        return InputCmd.get_clickless(self.fcp)

    def get_input_meters(self):
        return InputCmd.get_meters(self)

    #
    # Output configurations.
    #
    def get_out_attr_labels(self):
        return OutputCmd.get_attr_labels()

    def set_out_attr(self, attr: str):
        OutputCmd.set_attr(self.fcp, attr)

    def get_out_attr(self):
        return OutputCmd.get_attr(self.fcp)

    def set_out_mute(self, enable: bool):
        OutputCmd.set_mute(self.fcp, enable)

    def get_out_mute(self):
        return OutputCmd.get_mute(self.fcp)

    def set_out_volume(self, db: float):
        OutputCmd.set_volume(self.fcp, db)

    def get_out_volume(self):
        return OutputCmd.get_volume(self.fcp)

    #
    # Route configurations.
    #
    def get_out_src_labels(self):
        return OutputCmd.get_out_src_labels()

    def set_out_src(self, src: str):
        OutputCmd.set_out_src(self.fcp, src)

    def get_out_src(self):
        return OutputCmd.get_out_src(self.fcp)

    #
    # Mixer configurations.
    #
    def get_mixer_src_labels(self):
        return MixerCmd.get_mixer_src_labels()

    def set_mixer_src(self, src, ch, db):
        MixerCmd.set_src_gain(self.fcp, src, ch, db)

    def get_mixer_src(self, src, ch):
        return MixerCmd.get_src_gain(self.fcp, src, ch)

    def get_mixer_meters(self):
        return MixerCmd.get_meters(self)

    #
    # Hardware configurations.
    #
    def get_display_target_labels(self):
        return DisplayCmd.get_target_labels()

    def set_display_target(self, target):
        DisplayCmd.set_target(self.fcp, target)

    def get_display_target(self):
        return DisplayCmd.get_target(self.fcp)

    def get_display_overhold_labels(self):
        return DisplayCmd.get_overhold_labels()

    def set_display_overhold(self, target):
        DisplayCmd.set_overhold(self.fcp, target)

    def get_display_overhold(self):
        return DisplayCmd.get_overhold(self.fcp)

    def set_display_follow(self, enable):
        DisplayCmd.set_follow(self.fcp, enable)

    def get_display_follow(self):
        return DisplayCmd.get_follow(self.fcp)

    def clear_display(self):
        DisplayCmd.reset_meters(self.fcp)

    #
    # Knob states.
    #
    def get_knob_states(self):
        return KnobCmd.get_states(self.fcp)
