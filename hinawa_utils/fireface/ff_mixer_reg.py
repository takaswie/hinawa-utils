# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto

from math import log10


class FFMixerRegs():
    __SPECS = {
        'Fireface400':  {
            'analog':   10,
            'spdif':    2,
            'adat':     8,
            'stream':   18,
            'avail':    18,
        },
        'Fireface800':  {
            'analog':   10,
            'spdif':    2,
            'adat':     16,
            'stream':   28,
            'avail':    32,
        },
    }

    __MUTE_VAL = 0x00000000
    __MIN_VAL = 0x00000001
    __ZERO_VAL = 0x00008000
    __MAX_VAL = 0x00010000

    @classmethod
    def create_initial_cache(cls, name):
        cache = []
        dsts = cls.__SPECS[name]['analog']
        dsts += cls.__SPECS[name]['spdif']
        dsts += cls.__SPECS[name]['adat']
        avail = cls.__SPECS[name]['avail']
        for i in range(dsts):
            for j in range(avail):
                cache.append(cls.__MUTE_VAL)
            for j in range(avail):
                if i != j:
                    val = cls.__MUTE_VAL
                else:
                    # Supply diagonal stream sources for mixers.
                    val = cls.__ZERO_VAL
                cache.append(val)
        return cache

    @classmethod
    def __generate_labels(cls, name, category):
        labels = []
        for i in range(cls.__SPECS[name][category]):
            labels.append('{0}-{1}'.format(category, i + 1))
        return labels

    @classmethod
    def get_mixer_labels(cls, name: str):
        labels = cls.__generate_labels(name, 'analog')
        labels[-2] = 'hp-1'
        labels[-1] = 'hp-2'
        labels += cls.__generate_labels(name, 'spdif')
        labels += cls.__generate_labels(name, 'adat')
        return labels

    @classmethod
    def get_mixer_src_labels(cls, name: str):
        labels = cls.__generate_labels(name, 'analog')
        labels += cls.__generate_labels(name, 'spdif')
        labels += cls.__generate_labels(name, 'adat')
        labels += cls.__generate_labels(name, 'stream')
        return labels

    @classmethod
    def build_val_from_db(cls, db: float):
        return int(0x8000 * pow(10, db / 20))

    @classmethod
    def parse_val_to_db(cls, val: int):
        if val == 0:
            return float('-inf')
        return 20 * log10(val / 0x8000)

    @classmethod
    def get_mute_db(cls):
        return cls.parse_val_to_db(cls.__MUTE_VAL)

    @classmethod
    def get_min_db(cls):
        return cls.parse_val_to_db(cls.__MIN_VAL)

    @classmethod
    def get_max_db(cls):
        return cls.parse_val_to_db(cls.__MAX_VAL)

    @classmethod
    def calculate_offset(cls, name: str, dst: str, src: str):
        """
        Register layout.
             =+=========+=
              | inputs  | <= avail
        dst-0 +---------+
              | streams | <= avail
             =+=========+=
              | inputs  |
        dst-1 +---------+
              | streams |
             =+=========+=
        ...
             =+=========+=
              | inputs  |
        dst-n +---------+
              | streams |
             =+=========+=
        """

        dsts = cls.get_mixer_labels(name)
        srcs = cls.get_mixer_src_labels(name)
        if dst not in dsts:
            raise ValueError('Invalid argument for destination of mixer.')
        if src not in srcs:
            raise ValueError('Invalid argument for source of mixer.')

        offset = dsts.index(dst) * cls.__SPECS[name]['avail'] * 2 * 4

        if src.find('stream-') == 0:
            offset += cls.__SPECS[name]['avail'] * 4
            srcs = cls.__generate_labels(name, 'stream')

        return offset + srcs.index(src) * 4
