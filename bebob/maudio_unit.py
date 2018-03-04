from bebob.bebob_unit import BebobUnit

from bebob.maudio_protocol_abstract import MaudioProtocolAbstract

__all__ = ['MaudioUnit']

class MaudioUnit(BebobUnit):
    _SUPPORTED_MODELS = (
        # VendorID, ModelID, ModelName, Protocol
        (0x000000, 0x000000, MaudioProtocolAbstract),
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
