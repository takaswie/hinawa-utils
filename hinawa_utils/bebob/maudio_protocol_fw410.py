# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.bebob.maudio_protocol_normal import MaudioProtocolNormal

from hinawa_utils.ta1394.general import AvcConnection
from hinawa_utils.ta1394.ccm import AvcCcm
from hinawa_utils.ta1394.audio import AvcAudio

__all__ = ['MaudioProtocolNormal']

class MaudioProtocolFw410(MaudioProtocolNormal):
    _SELECTOR_FB        = 0x07
    _PROCESSING_OUT_FB  = 0x07
    _PROCESSING_IN_FB   = 0x00
    _PROCESSING_OUT_CH  = 0x01

    def set_headphone_source(self, target, source):
        if target not in self.get_headphone_labels():
            raise ValueError('Invalid argument for headphone')
        if source not in self.get_headphone_source_labels(target):
            raise ValueError('Invalid argument for headphone source')

        if source == 'aux-1/2':
            value = 0x01
        else:
            value = 0x00
        AvcAudio.set_selector_state(self._unit.fcp, 0, 'current',
                                    self._SELECTOR_FB, value)

        if source != 'aux-1/2':
            for i, elems in enumerate(self._mixers):
                if self._labels['mixers'][i] == source:
                    data = (0x00, 0x00)
                else:
                    data = (0x80, 0x00)

                in_ch = elems[1][0]
                AvcAudio.set_processing_mixer_state(self._unit.fcp, 0,
                            'current', self._PROCESSING_OUT_FB,
                            self._PROCESSING_IN_FB, in_ch,
                            self._PROCESSING_OUT_CH, data)

    def get_headphone_source(self, target):
        if target not in self.get_headphone_labels():
            raise ValueError('Invalid argument for headphone')

        state = AvcAudio.get_selector_state(self._unit.fcp, 0, 'current',
                                            self._SELECTOR_FB)
        if state == 0x01:
            return 'aux-1/2'
        elif state == 0x00:
            for i, elems in enumerate(self._mixers):
                in_ch = elems[1][0]
                data = AvcAudio.get_processing_mixer_state(self._unit.fcp, 0,
                            'current',
                            self._PROCESSING_OUT_FB, self._PROCESSING_IN_FB,
                            in_ch, self._PROCESSING_OUT_CH)
                print(data)
                if data[0] == 0x00 and data[1] == 0x00:
                    return self._labels['mixers'][i]

        # No sources are set. For convenience, set 'mixer-1/2'.
        self.set_headphone_source('headphone-1/2', 'mixer-1/2')
        return 'mixer-1/2'
