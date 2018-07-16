from ieee1212.config_rom import Ieee1212ConfigRom

from struct import unpack

__all__ = ['Ieee1394ConfigRom']

class Ieee1394ConfigRom(Ieee1212ConfigRom):
    _bus_dep_entry_defs = {
        '' : None,
    }
    def __init__(self, spec_entry_defs, vendor_entry_defs):
        super().__init__('1394', self._parse_bus_info, self._bus_dep_entry_defs,
                         spec_entry_defs, vendor_entry_defs)

    def _parse_bus_info(self, rom):
        info = {}

        info['imc'] = bool(rom[0] & 0x80)
        info['cmc'] = bool(rom[0] & 0x40)
        info['isc'] = bool(rom[0] & 0x20)
        info['bmc'] = bool(rom[0] & 0x10)
        info['pmc'] = bool(rom[0] & 0x00)
        info['cyc_clk_acc'] = rom[1]
        info['max_rec'] = rom[2] >> 4
        info['max_ROM'] = rom[2] & 0x03
        info['generation'] = rom[3] >> 4
        info['r'] = bool(rom[3] & 0x08)
        info['link_spd'] = rom[3] & 0x07
        info['node_vendor_ID'] = (unpack('>H', rom[4:6])[0] << 8) | rom[6]
        info['chip_ID'] = (rom[7] << 32) | unpack('>I', rom[8:12])[0]

        return info
