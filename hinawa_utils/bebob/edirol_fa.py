# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from hinawa_utils.bebob.bebob_unit import BebobUnit
from hinawa_utils.ta1394.audio import AvcAudio

__all__ = ['EdirolFaUnit']


class EdirolFaUnit(BebobUnit):
    _FBS = {
        # Edirol FA-66.
        (0x0040ab, 0x010049): (
            'analog-in-1/2',
            'analog-in-3/4',
            'digital-in-1/2',
        ),
        # Edirol FA-101.
        (0x0040ab, 0x010048): (
            'analog-in-1/2',
            'analog-in-3/4',
            'analog-in-5/6',
            'analog-in-7/8',
            'digital-in-1/2',
        ),
    }

    def __init__(self, path):
        super().__init__(path)
        if (self.vendor_id, self.model_id) not in self._FBS:
            raise OSError('Not supported.')
        self._fbs = self._FBS[(self.vendor_id, self.model_id)]

    def get_mixer_input_labels(self):
        return self._fbs

    def set_mixer_input_gain(self, target, ch, gain):
        if target not in self._fbs:
            raise ValueError('Invalid argument for input.')
        fb = self._fbs.index(target) + 1
        data = AvcAudio.build_data_from_db(gain)
        AvcAudio.set_feature_volume_state(self.fcp, 0, 'current', fb, ch, data)

    def get_mixer_input_gain(self, target, ch):
        if target not in self._fbs:
            raise ValueError('Invalid argument for input.')
        fb = self._fbs.index(target) + 1
        data = AvcAudio.get_feature_volume_state(
            self.fcp, 0, 'current', fb, ch)
        return AvcAudio.parse_data_to_db(data)

    def set_mixer_input_balance(self, target, ch, balance):
        if target not in self._fbs:
            raise ValueError('Invalid argument for input.')
        fb = self._fbs.index(target) + 1
        data = AvcAudio.build_data_from_db(balance)
        AvcAudio.set_feature_lr_state(self.fcp, 0, 'current', fb, ch, data)

    def get_mixer_input_balance(self, target, ch):
        if target not in self._fbs:
            raise ValueError('Invalid argument for input.')
        fb = self._fbs.index(target) + 1
        data = AvcAudio.get_feature_lr_state(self.fcp, 0, 'current', fb, ch)
        return AvcAudio.parse_data_to_db(data)
