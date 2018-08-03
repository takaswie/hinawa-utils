# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from struct import unpack

from hinawa_utils.bebob.bebob_unit import BebobUnit

from hinawa_utils.bebob.maudio_protocol_normal import MaudioProtocolNormal
from hinawa_utils.bebob.maudio_protocol_fw410 import MaudioProtocolFw410
from hinawa_utils.bebob.maudio_protocol_audiophile import MaudioProtocolAudiophile
from hinawa_utils.bebob.maudio_protocol_special import MaudioProtocolSpecial

__all__ = ['MaudioUnit']

class MaudioUnit(BebobUnit):
    _SUPPORTED_MODELS = {
        # (VendorID, ModelID): Protocol
        (0x000d6c, 0x00000a): MaudioProtocolNormal,     # Ozonic
        (0x000d6c, 0x010062): MaudioProtocolNormal,     # Firewire Solo
        (0x000d6c, 0x010060): MaudioProtocolAudiophile, # Firewire Audiophile
        (0x000d6c, 0x010081): MaudioProtocolNormal,     # NRV10
        (0x000d6c, 0x0100a1): MaudioProtocolNormal,     # Profire Lightbridge
        (0x0007f5, 0x010046): MaudioProtocolFw410,      # Firewire 410
        (0x000d6c, 0x010071): MaudioProtocolSpecial,    # Firewire 1814
        (0x000d6c, 0x010091): MaudioProtocolSpecial,    # ProjectMix I/O
    }

    def __init__(self, path):
        super().__init__(path)

        key = (self.vendor_id, self.model_id)
        if key not in self._SUPPORTED_MODELS:
            raise OSError('Not supported.')
        self.protocol = self._SUPPORTED_MODELS[key](self, False)
