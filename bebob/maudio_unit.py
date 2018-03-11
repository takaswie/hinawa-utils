from bebob.bebob_unit import BebobUnit

from bebob.maudio_protocol_normal import MaudioProtocolNormal
from bebob.maudio_protocol_fw410 import MaudioProtocolFw410
from bebob.maudio_protocol_audiophile import MaudioProtocolAudiophile
from bebob.maudio_protocol_special import MaudioProtocolSpecial

__all__ = ['MaudioUnit']

class MaudioUnit(BebobUnit):
    _SUPPORTED_MODELS = (
        # VendorID, ModelID, ModelName, Protocol
        (0x000d6c, 0x00000a, MaudioProtocolNormal),  # Ozonic
        (0x000d6c, 0x010062, MaudioProtocolNormal),  # Firewire Solo
        (0x000d6c, 0x010060, MaudioProtocolAudiophile), # Firewire Audiophile
        (0x000d6c, 0x010081, MaudioProtocolNormal),  # NRV10
        (0x000d6c, 0x0100a1, MaudioProtocolNormal),  # Profire Lightbridge
        (0x0007f5, 0x010046, MaudioProtocolFw410),   # Firewire 410
        (0x000d6c, 0x010071, MaudioProtocolSpecial), # Firewire 1814
        (0x000d6c, 0x010091, MaudioProtocolSpecial), # ProjectMix I/O
    )

    def __init__(self, path):
        super().__init__(path)
        vendor_id = -1
        model_id = -1
        for quad in self.get_config_rom():
            if quad >> 24 == 0x03:
                vendor_id = quad & 0x00ffffff
            if quad >> 24 == 0x17:
                model_id = quad & 0x00ffffff
        if vendor_id < 0 or model_id < 0:
            raise OSError('Invalid design of config rom.')
        for entry in self._SUPPORTED_MODELS:
            if entry[0] == vendor_id and entry[1] == model_id:
                self.protocol = entry[2](self, False, model_id)
                break
        else:
            raise OSError('Not supported.')
