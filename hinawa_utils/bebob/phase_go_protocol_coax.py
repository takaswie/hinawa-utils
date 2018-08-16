# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.bebob.phase_go_protocol_abstract import PhaseGoProtocolAbstract

from hinawa_utils.ta1394.audio import AvcAudio

__all__ = ['PhaseGoProtocolCoax']

class PhaseGoProtocolCoax(PhaseGoProtocolAbstract):
    __MIXER_OUTPUT_FB = 1
    __OUTPUT_LABELS = {
        'analog-1/2':       1,
        'headphone-1/2':    2,
        'digital-1/2':      3,
    }

    __ANALOG_INPUT_LEVELS = {
        'low':      bytearray((0xf4, 0x00)),
        'middle':   bytearray((0xfd, 0x00)),
        'high':     bytearray((0x00, 0x00)),
    }
    __ANALOG_INPUT_FB = 2
    __ANALOG_INPUT_FB_PN = 0

    def __init__(self, fcp):
        super().__init__(fcp, self.__MIXER_OUTPUT_FB, self.__OUTPUT_LABELS)

    def get_analog_input_level_labels(self):
        return list(self.__ANALOG_INPUT_LEVELS.keys())

    def set_analog_input_level(self, level):
        if level not in self.__ANALOG_INPUT_LEVELS:
            raise ValueError('Invalid argument for input level.')
        data = self.__ANALOG_INPUT_LEVELS[level]
        AvcAudio.set_feature_volume_state(self.fcp, 0, 'current',
                                self.__ANALOG_INPUT_FB,
                                self.__ANALOG_INPUT_FB_PN, data)

    def get_analog_input_level(self):
        result = AvcAudio.get_feature_volume_state(self.fcp, 0, 'current',
                            self.__ANALOG_INPUT_FB, self.__ANALOG_INPUT_FB_PN)
        for name, data in self.__ANALOG_INPUT_LEVELS.items():
            if data == result:
                return name
        else:
            raise OSError('Unexpected data for input level')
