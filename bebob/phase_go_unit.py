from struct import unpack

from bebob.bebob_unit import BebobUnit

from bebob.phase_go_protocol_coax import PhaseGoProtocolCoax
from bebob.phase_go_protocol_opt import PhaseGoProtocolOpt

__all__ = ['PhaseGoUnit']

class PhaseGoUnit(BebobUnit):
    _SUPPORTED_MODELS = {
        # (VendorID, ModelID): ProtocolClass
        (0x000aac, 0x000004):   PhaseGoProtocolCoax,    # Terratec PHASE 24 FW
        (0x000aac, 0x000007):   PhaseGoProtocolOpt,     # Terratec PHASE X24 FW
        (0x00a0de, 0x10000b):   PhaseGoProtocolCoax,    # Yamaha Go44
        (0x00a0de, 0x10000c):   PhaseGoProtocolOpt,     # Yamaha Go46
    }

    def __init__(self, path):
        super().__init__(path)

        key = (self.vendor_id, self.model_id)
        if key not in self._SUPPORTED_MODELS:
            raise OSError('Not supported.')
        self.protocol = self._SUPPORTED_MODELS[key]
