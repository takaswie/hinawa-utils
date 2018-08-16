# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.bebob.phase_go_protocol_abstract import PhaseGoProtocolAbstract

from hinawa_utils.ta1394.audio import AvcAudio

__all__ = ['PhaseGoProtocolOpt']

class PhaseGoProtocolOpt(PhaseGoProtocolAbstract):
    __MIXER_OUTPUT_FB = 2
    __OUTPUT_LABELS = {
        'analog-1/2':       1,
        'analog-3/4':       2,
        'digital-1/2':      3,
    }

    __ANALOG_OUTPUT_TARGETS = ('analog-1/2', 'analog-3/4')
    __ANALOG_OUTPUT_FB = 1

    def __init__(self, fcp):
        super().__init__(fcp, self.__MIXER_OUTPUT_FB, self.__OUTPUT_LABELS)

    def get_analog_output_labels(self):
        return self.__ANALOG_OUTPUT_TARGETS

    def __check_analog_output_channel(self, target, ch):
        if target not in self.__ANALOG_OUTPUT_TARGETS:
            raise ValueError('Invalid argument for stereo pair')
        if ch not in (1, 2):
            raise ValueError('Invalid argument for channel number')
        return self.__ANALOG_OUTPUT_FB, ch

    def set_analog_output_volume(self, target, ch, db):
        fb, ch = self.__check_analog_output_channel(target, ch)
        data = AvcAudio.build_data_from_db(db)
        AvcAudio.set_feature_volume_state(self.fcp, 0, 'current', fb, ch,
                                          data)

    def get_analog_output_volume(self, target, ch):
        fb, ch = self.__check_analog_output_channel(target, ch)
        data = AvcAudio.get_feature_volume_state(self.fcp, 0, 'current', fb,
                                                 ch)
        return AvcAudio.parse_data_to_db(data)

    def set_analog_output_mute(self, target, ch, enable):
        fb, ch = self.__check_analog_output_channel(target, ch)
        AvcAudio.set_feature_mute_state(self.fcp, 0, 'current', fb, ch,
                                        enable)

    def get_analog_output_mute(self, target, ch):
        fb, ch = self.__check_analog_output_channel(target, ch)
        return AvcAudio.get_feature_mute_state(self.fcp, 0, 'current', fb, ch)
