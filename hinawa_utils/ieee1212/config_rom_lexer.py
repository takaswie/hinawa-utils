# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from struct import unpack
from enum import Enum

__all__ = ['Ieee1212ConfigRomLexer']


class EntryType(Enum):
    IMMEDIATE = 0x00
    CSR_OFFSET = 0x01
    LEAF = 0x02
    DIRECTORY = 0x03

    @classmethod
    def check_value(cls, value):
        return value in (item.value for item in cls)

    def __repr__(self):
        return "'" + self.name + "'"


class Ieee1212ConfigRomLexer():
    @classmethod
    def detect_entries(cls, data):
        entries = {}

        bus_info_length = cls._detect_bus_info_length(data)
        entries['bus-info'] = data[4:4 + bus_info_length]
        data = data[4 + bus_info_length:]

        entries['root-directory'] = cls._detect_directory_entries(data)

        return entries

    @classmethod
    def _detect_bus_info_length(cls, data):
        bus_info_quadlet_count = data[0]
        crc_quadlet_count = data[1]
        crc = unpack('>H', data[2:4])[0]
        return bus_info_quadlet_count * 4

    @classmethod
    def _detect_leaf_length(cls, data):
        quadlet_count = unpack('>H', data[0:2])[0]
        crc = unpack('>H', data[2:4])[0]
        return quadlet_count * 4

    @classmethod
    def _detect_directory_length(cls, data):
        quadlet_count = unpack('>H', data[0:2])[0]
        crc = unpack('>H', data[2:4])[0]
        return quadlet_count * 4

    @classmethod
    def _detect_immediate(cls, key, value, data):
        return value

    @classmethod
    def _detect_csr_offset(cls, key, value, data):
        return 0xfffff0000000 + value * 4

    @classmethod
    def _detect_leaf(cls, key, value, data):
        offset = value * 4
        data = data[offset:]
        length = cls._detect_leaf_length(data)
        return data[4:4 + length]

    @classmethod
    def _detect_directory(cls, key, value, data):
        data = data[value * 4:]
        return cls._detect_directory_entries(data)

    @classmethod
    def _detect_directory_entries(cls, data):
        #
        # Table 7 - Directory entry types
        #
        TYPE_HANDLES = {
            EntryType.IMMEDIATE:   cls._detect_immediate,
            EntryType.CSR_OFFSET:  cls._detect_csr_offset,
            EntryType.LEAF:        cls._detect_leaf,
            EntryType.DIRECTORY:   cls._detect_directory,
        }
        entries = []

        length = cls._detect_directory_length(data)
        data = data[4:]

        while length > 0:
            type_id = data[0] >> 6
            key_id = data[0] & 0x3f
            value = (data[1] << 16) | (data[2] << 8) | data[3]

            if not EntryType.check_value(type_id):
                raise ValueError('Type {0} is not defined.'.format(type_id))
            type = EntryType(type_id)

            entry = [(key_id, type), TYPE_HANDLES[type](key_id, value, data)]
            entries.append(entry)

            data = data[4:]
            length -= 4

        return entries
