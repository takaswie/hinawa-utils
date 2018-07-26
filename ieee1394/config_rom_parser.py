from struct import unpack

from ieee1212.config_rom_lexer import Ieee1212ConfigRomLexer
from ieee1212.root_directory_parser import Ieee1212RootDirectoryParser

__all__ = ['Ieee1394ConfigRomParser']

class Ieee1394ConfigRomParser(Ieee1212RootDirectoryParser):
    _NAME = '1394'

    def __init__(self):
        super().__init__()

    def _parse_ieee1394_bus_info(self, data):
        info = {}

        name = data[0:4].decode('US-ASCII')
        if name != self._NAME:
            raise ValueError('Invalid data for Configuration ROM in IEEE 1394.')

        info['name'] = name
        info['imc'] = bool(data[4] & 0x80)
        info['cmc'] = bool(data[4] & 0x40)
        info['isc'] = bool(data[4] & 0x20)
        info['bmc'] = bool(data[4] & 0x10)
        info['pmc'] = bool(data[4] & 0x00)
        info['cyc_clk_acc'] = data[5]
        info['max_rec'] = data[6] >> 4
        info['max_ROM'] = data[6] & 0x03
        info['generation'] = data[7] >> 4
        info['r'] = bool(data[7] & 0x08)
        info['link_spd'] = data[7] & 0x07
        info['node_vendor_ID'] = (unpack('>H', data[8:10])[0] << 8) | data[10]
        info['chip_ID'] = (data[11] << 32) | unpack('>I', data[12:16])[0]

        return info

    def _handle_bus_dep_keys(key_id, type, data):
        pass

    def parse_rom(self, data):
        info = {}

        entries = Ieee1212ConfigRomLexer.detect_entries(data)

        bus_info = entries['bus-info']
        info['bus-info'] = self._parse_ieee1394_bus_info(bus_info)

        self.add_bus_dep_handle(self._NAME, self._handle_bus_dep_keys)
        root = entries['root-directory']
        info['root-directory'] = self.parse_root_directory(self._NAME, root)

        return info
