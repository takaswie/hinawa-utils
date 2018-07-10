from struct import unpack

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

        vendor_id = -1
        model_id = -1
        data = self.get_config_rom()
        quad_count = len(data) // 4
        for i in range(quad_count):
            quad = unpack('>I', data[:4])[0]
            if quad >> 24 == 0x03:
                vendor_id = quad & 0x00ffffff
            if quad >> 24 == 0x17:
                model_id = quad & 0x00ffffff
                break
            data = data[4:]
        if vendor_id < 0 or model_id < 0:
            raise OSError('Invalid design of config rom.')

        for entry in self._SUPPORTED_MODELS:
            if entry[0] == vendor_id and entry[1] == model_id:
                self.protocol = entry[2](self.fcp)
                break
        else:
            raise OSError('Not supported.')
