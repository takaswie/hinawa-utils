# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from struct import pack, unpack
from math import pow, log10

from hinawa_utils.dg00x.dg00x_unit import Dg00xUnit

__all__ = ['Dg003Unit']


class Dg003Unit(Dg00xUnit):
    __OFFSET_MIXER_SRC = 0x0300
    __MAX_COEFF = 0x1fffffff

    def __init__(self, path):
        super().__init__(path)

    def set_mixer_status(self, enabled):
        data = bytearray(4)
        data[3] = 0x01 if enabled else 0x00
        self._write_transaction(0x0124, data)

    def get_mixer_status(self):
        data = self._read_transaction(0x0124, 4)
        return bool(data[3])

    def get_mixer_src_labels(self):
        labels = []
        for ch in range(1, 9, 2):
            labels.append('Analog-{0}/{1}'.format(ch, ch + 1))
        for ch in range(1, 3, 2):
            labels.append('S/PDIF-{0}/{1}'.format(ch, ch + 1))
        for ch in range(1, 8, 2):
            labels.append('ADAT-{0}/{1}'.format(ch, ch + 1))
        return labels

    def __write_src_pair(self, pair):
        for elem in pair:
            offset = elem[0]
            data = pack('>I', elem[1])
            self._write_transaction(offset, data)

    def __read_src_pair(self, src, ch):
        pair = []

        labels = self.get_mixer_src_labels()
        if src not in labels:
            raise ValueError('Invalid argument for source of mixer.')

        for offset in (0x08 * ch, 0x08 * ch + 0x04):
            offset += self.__OFFSET_MIXER_SRC + labels.index(src) * 0x10
            data = self._read_transaction(offset, 4)
            pair.append([offset, unpack('>I', data)[0]])

        return pair

    def __parse_val_to_db(self, val):
        if val == 0:
            return float('-inf')
        return 20 * log10(val / self.__MAX_COEFF)

    def __build_val_from_db(self, db):
        if db == float('-inf'):
            return 0
        return int(self.__MAX_COEFF * pow(10, db / 20))

    def set_mixer_src_balance(self, src, ch, balance):
        pair = self.__read_src_pair(src, ch)
        total = pair[0][1] + pair[1][1]

        if total >= self.__MAX_COEFF:
            total = self.__MAX_COEFF
        left_ratio = 100 - balance
        right_ratio = balance

        if balance == float('-inf'):
            total = 0
        pair[0][1] = int(total * left_ratio / 100)
        pair[1][1] = int(total * right_ratio / 100)
        self.__write_src_pair(pair)

    def get_mixer_src_balance(self, src, ch):
        pair = self.__read_src_pair(src, ch)
        total = pair[0][1] + pair[1][1]
        if total == 0:
            return float('-inf')
        return 100 * pair[1][1] / total

    def set_mixer_src_gain(self, src, ch, db):
        pair = self.__read_src_pair(src, ch)
        val = self.__build_val_from_db(db)

        # Calculate ratio between left and right.
        total = pair[0][1] + pair[1][1]
        if total == 0:
            if pair[0][0] % 0x10 == 0x08:
                # Even channel.
                ratio_left = 0
                ratio_right = 1
            else:
                # Odd channel.
                ratio_left = 1
                ratio_right = 0
        else:
            ratio_left = pair[0][1] / total
            ratio_right = 1 - ratio_left

        pair[0][1] = int(val * ratio_left)
        pair[1][1] = int(val * ratio_right)
        self.__write_src_pair(pair)

    def get_mixer_src_gain(self, src, ch):
        pair = self.__read_src_pair(src, ch)
        total = pair[0][1] + pair[1][1]
        if total == 0:
            return float('-inf')
        return self.__parse_val_to_db(total)
