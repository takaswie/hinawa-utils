from struct import unpack

__all__ = ['Ieee1212ConfigRom']

class Ieee1212ConfigRom():
    def __init__(self, bus_name, bus_info_parser, bus_entry_defs,
                 spec_entry_defs, vendor_entry_defs):
        self._bus_name = bus_name
        self._bus_info_parser = bus_info_parser
        self._bus_entry_defs = bus_entry_defs
        self._spec_entry_defs = spec_entry_defs
        self._vendor_entry_defs = vendor_entry_defs

    def get_bus_info(self, rom):
        bus_info_length = self._check_bus_info_length(rom)
        bus_info = rom[4:4 + bus_info_length]
        return self._parse_bus_info(bus_info)

    def get_root_directory(self, rom):
        bus_info_length = self._check_bus_info_length(rom)
        root = rom[4 + bus_info_length:]
        return self._parse_root_directory(root)

    def _check_bus_info_length(self, rom):
        bus_info_length = rom[0]
        crc_length = rom[1]
        crc = unpack('>H', rom[2:4])[0]
        return bus_info_length * 4

    def _parse_bus_info(self, rom):
        info = {}

        bus_name = rom[0:4].decode('US-ASCII')
        if bus_name != self._bus_name:
            raise OSError('Bus {0} is not supported'.format(bus_name))
        info = self._bus_info_parser(rom)
        info['name'] = bus_name

        return info

    def _check_descriptor_length(self, rom):
        descriptor_length = unpack('>H', rom[0:2])[0]
        crc = unpack('>H', rom[2:4])[0]
        return descriptor_length * 4

    #
    # IEEE 1212, 7.5.4.1 Textual descriptors
    #
    def _parse_textual_descriptor(self, rom):
        WIDTH_DEFINITIONS = {
            0x00:   'Fixed one-byte characters',
            0x01:   'Fixed two-byte characters',
            0x02:   'Fixed four-byte characters',
            # 0x03-07: reserved
            0x08:   'Not to be used',
            0x09:   'Variable width characters up to a two byte maximum',
            0x0a:   'Variable width characters up to a four byte maximum',
            # 0x0b-0f: reserved
        }

        width = rom[0] >> 4
        character_set = ((rom[0] & 0x0f) << 8) |rom[1]
        language = unpack('>H', rom[2:4])[0]

        if width not in WIDTH_DEFINITIONS or width != 0x00:
            raise OSError('Width {0} is not supported.'.format(width))

        # character_set == IANA MIBenum
        if character_set != 0:
            return OSError('Character set {0} is not supported.'.format(
                                                                character_set))

        # At present, 'US-ASCII' is supported only.
        if language & 0x8000 or language > 0:
            raise OSError('Language {0} is not supported.'.format(language))

        content = rom[4:].decode('US-ASCII') + '\0'
        return content[:content.find('\0')]

    #
    # IEEE 1212, 7.5.4.2 Icon descriptor
    #
    def _parse_icon_descriptor(self, rom):
        raise OSError('Icon descriptor is not supported.')

    #
    # IEEE 1212, 7.5.4 Descriptors
    #
    def _parse_descriptor_leaf(self, rom):
        TYPE_PARSERS = {
                0x00: ('textual',   self._parse_textual_descriptor),
                0x01: ('icon',      self._parse_icon_descriptor),
        }
        descriptor_length = self._check_descriptor_length(rom)

        rom = rom[4:4 + descriptor_length]
        descriptor_type = rom[0]
        specifier_id = (rom[1] << 16) | (rom[2] << 8) | rom[3]

        if specifier_id != 0x00:
            raise OSError('Specifier ID {0} is not supported.'.format(
                                                            specifier_id))

        if descriptor_type not in TYPE_PARSERS:
            raise OSError('Descritpor type {0} is not supported.'.format(
                                                            descriptor_type))

        rom = rom[4:]
        return TYPE_PARSERS[descriptor_type][1](rom)

    #
    # IEEE 1212, 7.7.8 EUI_64 entry
    #
    def _parse_eui_64_leaf(self, rom):
        rom = rom[4:]
        return (unpack('<I', rom[0:4])[0] << 32) | unpack('<I', rom[4:8])[0]

    #
    # IEEE 1212, 7.7.13 Unit_Location entry
    #
    def _parse_unit_location_leaf(self, rom):
        info = {}
        rom = rom[4:]
        info['base-address'] = (unpack('<I', rom[0:4])[0] << 32) | \
                               unpack('<I', rom[4:8])[0]
        rom = rom[4:]
        info['upper-bound'] = (unpack('<I', rom[0:4])[0] << 32) | \
                              unpack('<I', rom[4:8])[0]
        return info

    def _parse_immediate(self, key, value, rom):
        return value

    def _parse_csr_offset(self, key, value, rom):
        return 0xfffff0000000 + value * 4

    def _parse_leaf(self, key, value, rom):
        LEAF_PARSERS = {
                0x01:   self._parse_descriptor_leaf,
                0x02:   None,
                0x03:   None,
                0x07:   None,
                0x0d:   self._parse_eui_64_leaf,
                0x15:   self._parse_unit_location_leaf,
                0x19:   None,
                0x1b:   None,
                0x1e:   None,
                0x1f:   None,
        }
        if key not in LEAF_PARSERS:
            raise OSError('Key {0} is not supported.'.format(key))

        rom = rom[value * 4:]
        return LEAF_PARSERS[key](rom)

    #
    # IEEE 1212, 7.6.2 Instance directories
    # IEEE 1212, 7.6.3 Unit directories
    # IEEE 1212, 7.6.4 Feature directories
    #
    def _parse_directory(self, key, value, rom):
        rom = rom[value * 4:]
        directory_length = self._check_directory_length(rom)
        return self._parse_directory_entries(directory_length, rom)

    def _parse_directory_entries(self, directory_length, rom):
        #
        # IEEE 1212, Table 7 - Directory entry types
        #
        TYPE_PARSERS = {
                0x00: ('immediate',     self._parse_immediate),
                0x01: ('csr-offsset',   self._parse_csr_offset),
                0x02: ('leaf',          self._parse_leaf),
                0x03: ('directory',     self._parse_directory),
        }
        #
        # IEEE 1212, Table 16 - Key definitions
        #
        KEY_DEFS = {
            # key:  (name, available types of parser)
            0x01:   ('descriptor',                  (0x02, 0x03)),
            0x02:   ('bus-dependent-info',          (0x00, 0x02, 0x03)),
            0x03:   ('vendor',                      (0x00, 0x02, 0x03)),
            0x04:   ('hardware-version',            (0x00, )),
            # 0x05-06: reserved.
            0x07:   ('module',                      (0x02, 0x03)),
            # 0x08-0b: reserved.
            0x0c:   ('node-capabilities',           (0x00, )),
            0x0d:   ('eui-64',                      (0x02, )),
            # 0x0e-10: reserved.
            0x11:   ('unit',                        (0x03, )),
            0x12:   ('specifier-id',                (0x00, )),
            0x13:   ('version',                     (0x00, )),
            0x14:   ('dependent-info',              (0x00, 0x01, 0x02, 0x03)),
            0x15:   ('unit-location',               (0x02, )),
            0x17:   ('model',                       (0x00, )),
            0x18:   ('instance',                    (0x03, )),
            0x19:   ('keyword',                     (0x02, )),
            0x1a:   ('feature',                     (0x03, )),
            0x1b:   ('extended-rom',                (0x02, )),
            0x1c:   ('extended-key-specifier-id',   (0x00, )),
            0x1d:   ('extended-key',                (0x00, )),
            0x1e:   ('extended-data',               (0x00, 0x01, 0x02, 0x03)),
            0x1f:   ('modifiable-descriptor',       (0x02, )),
            0x20:   ('directory-id',                (0x00, )),
            # 0x21-2f: reserved.
            # 0x30-37: by bus standard.
            # 0x38-3f: by directory specifier.
        }
        length = 0
        entries = []

        rom = rom[4:]
        while length < directory_length:
            type = rom[0] >> 6
            key = rom[0] & 0x3f
            value = (rom[1] << 16) | (rom[2] << 8) | rom[3]

            if type not in TYPE_PARSERS:
                raise OSError('Type {0} is not supported.'.format(type))
            type_name = TYPE_PARSERS[type][0]
            type_parser = TYPE_PARSERS[type][1]

            definition = None
            if self._vendor_entry_defs and key in self._vendor_entry_defs:
                definition = self._vendor_entry_defs[key]
            elif 0x30 <= key and key <= 0x37 and \
                 self._bus_entry_defs and key in self._bus_entry_defs:
                definition = self._bus_entry_defs[key]
            elif 0x38 <= key and key <= 0x3f and \
                 self._spec_entry_defs and key in self._spec_entry_defs:
                definition = self._spec_entry_defs[key]
            elif key in KEY_DEFS:
                definition = KEY_DEFS[key]

            if definition and type in definition[1]:
                if definition[0] != 'descriptor':
                    key_name = definition[0]
            else:
                key_name = '0x{0:x}'.format(key)

            entry = [key_name, type_name, type_parser(key, value, rom)]
            entries.append(entry)

            rom = rom[4:]
            length += 4

        return entries

    def _check_directory_length(self, rom):
        length = unpack('>H', rom[0:2])[0]
        crc = unpack('>H', rom[2:4])[0]
        return length * 4

    #
    # IEEE 1212, 7.6.1 Root directory
    #
    def _parse_root_directory(self, rom):
        directory_length = self._check_directory_length(rom)
        #
        return self._parse_directory_entries(directory_length, rom)
