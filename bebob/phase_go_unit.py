from bebob.bebob_unit import BebobUnit

from bebob.phase_go_protocol_coax import PhaseGoProtocolCoax
from bebob.phase_go_protocol_opt import PhaseGoProtocolOpt

__all__ = ['PhaseGoUnit']

class PhaseGoUnit(BebobUnit):
    _SUPPORTED_MODELS = (
        # VendorID, ModelID, ProtocolClass
        (0x000aac, 0x000004, PhaseGoProtocolCoax),  # Terratec PHASE 24 FW
        (0x000aac, 0x000007, PhaseGoProtocolOpt),   # Terratec PHASE X24 FW
        (0x00a0de, 0x10000b, PhaseGoProtocolCoax),  # Yamaha Go44
        (0x00a0de, 0x10000c, PhaseGoProtocolOpt),   # Yamaha Go46
    )

    def __init__(self, path):
        super().__init__(path)
        for quad in self.get_config_rom():
            # Vendor ID
            if quad >> 24 == 0x03:
                vendor_id = quad & 0x00ffffff
            # Model ID
            if quad >> 24 == 0x17:
                model_id = quad & 0x00ffffff

        for entry in self._SUPPORTED_MODELS:
            if entry[0] == vendor_id and entry[1] == model_id:
                self.protocol = entry[2](self.fcp)
                break
        else:
            raise OSError('Not supported.')
