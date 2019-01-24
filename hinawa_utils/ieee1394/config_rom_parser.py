# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from struct import unpack

from hinawa_utils.ieee1212.config_rom_lexer import Ieee1212ConfigRomLexer
from hinawa_utils.ieee1212.root_directory_parser import Ieee1212RootDirectoryParser

__all__ = ['Ieee1394ConfigRomParser']


class Ieee1394ConfigRomParser(Ieee1212RootDirectoryParser):
    _NAME = '1394'

    __BUS_CAPABILITIES_1995 = {
        'imc':  7,  # the node is IRM capable.
        'cmc':  6,  # the node is cycle master capable.
        'isc':  5,  # the node supports isochronous operations.
        'bmc':  4,  # the node is bus namager capable.
    }

    # added by IEEE 1394:2008
    __BUS_CAPABILITIES_2008 = {
        'pmc':  3,  # the node is power manager capable.
        'adj':  2,  # the node is compliant to IEEE 1394.1:2004.
    }

    # IEEE 1394:1995 refers to ISO/IEC 13213:1994 (ANSI/IEEE Std 1212:1994).
    __NODE_CAPABILITIES = {
        'misc': {
            'spt':  15,  # The SPLIT_TIMEOUT register is implemented.
            'ms':  14,  # The messages-passing registers are implemented.
            'int':  13,  # The INTERRUPT_TARGET and INTERRUPT_MASK registers are
                        # implemented.
        },
        'testing': {
            'ext':  12,  # The ARGUMENT registers are implemented.
            'bas':  11,  # Node implements TEST_START&TEST_STATUS registers and
            # testing state.
        },
        'addressing': {
            'prv':  10,  # The node implements the private space.
            '64':   9,  # The node uses 64-bit aaddressing (otherwise 32-bit
                        # addressing).
            'fix':  8,  # The node uses the fixed addressing scheme (otherwise
                        # extended addressing).
        },
        'state': {
            'lst':  7,  # The STATE_BITS.lost bit is implemented.
            'drq':  6,  # The STATE_BITS.dreq bit is implemented.
            'elo':  4,  # The STATE_BITS.elog bit and the ERROR_LOG registers
                        # are implementd.
            'atn':  3,  # The STATE_BITS.atn bit is implemented.
            'off':  2,  # The STATE_BITS.off bit is implemented.
            'ded':  1,  # The node supports the dead state.
            'init': 0,  # The node supports the initializing state.
        },
    }

    def __init__(self):
        super().__init__()

    def _parse_ieee1394_bus_info(self, data):
        info = {}

        name = data[0:4].decode('US-ASCII')
        if name != self._NAME:
            raise ValueError(
                'Invalid data for Configuration ROM in IEEE 1394.')

        info['name'] = name

        for name, shift in self.__BUS_CAPABILITIES_1995.items():
            info[name] = bool(data[4] & (1 << shift))

        info['cyc_clk_acc'] = data[5]

        val = data[6] >> 4
        info['max_rec'] = 0 if val == 0 else pow(2, val + 1)

        # reserved fields in IEEE 1394:1995
        if data[4] & 0x0f or data[6] & 0x04 or data[7]:
            # IEEE 1394:2008
            for name, shift in self.__BUS_CAPABILITIES_2008.items():
                info[name] = bool(data[4] & (1 << shift))
            info['max_ROM'] = data[6] & 0x03
            info['generation'] = data[7] >> 4
            info['link_spd'] = data[7] & 0x07

        info['node_vendor_ID'] = (unpack('>H', data[8:10])[0] << 8) | data[10]
        info['chip_ID'] = (data[11] << 32) | unpack('>I', data[12:16])[0]

        return info

    def _handle_bus_dep_keys(self, key_name, type_name, data):
        if key_name == 'NODE_CAPABILITIES' and type_name == 'IMMEDIATE':
            info = {}
            for kind, elems in self.__NODE_CAPABILITIES.items():
                if kind not in info:
                    info[kind] = {}
                for name, shift in elems.items():
                    info[kind][name] = bool(data & (1 << shift))
            return info
        return None

    def parse_rom(self, data):
        info = {}

        entries = Ieee1212ConfigRomLexer.detect_entries(data)

        bus_info = entries['bus-info']
        info['bus-info'] = self._parse_ieee1394_bus_info(bus_info)

        self.add_bus_dep_handle(self._NAME, self._handle_bus_dep_keys)
        root = entries['root-directory']
        info['root-directory'] = self.parse_root_directory(self._NAME, root)

        return info
