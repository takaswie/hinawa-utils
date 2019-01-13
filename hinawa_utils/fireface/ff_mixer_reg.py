# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto

from math import log10


class FFMixerRegs():
    __MUTE_VAL = 0x00000000
    __MIN_VAL = 0x00000001
    __ZERO_VAL = 0x00008000
    __MAX_VAL = 0x00010000

    @classmethod
    def create_initial_cache(cls, spec):
        cache = []
        dsts =  spec['analog']
        dsts += spec['spdif']
        dsts += spec['adat']
        avail = spec['avail']
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
    def __generate_labels(cls, spec, category):
        labels = []
        for i in range(spec[category]):
            labels.append('{0}-{1}'.format(category, i + 1))
        return labels

    @classmethod
    def get_mixer_labels(cls, spec: dict):
        labels = cls.__generate_labels(spec, 'analog')
        labels += cls.__generate_labels(spec, 'spdif')
        labels += cls.__generate_labels(spec, 'adat')
        return labels

    @classmethod
    def get_mixer_src_labels(cls, spec: dict):
        labels = cls.__generate_labels(spec, 'analog')
        labels += cls.__generate_labels(spec, 'spdif')
        labels += cls.__generate_labels(spec, 'adat')
        labels += cls.__generate_labels(spec, 'stream')
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
    def calculate_offset(cls, spec: dict, dst: str, src: str):
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

        dsts = cls.get_mixer_labels(spec)
        srcs = cls.get_mixer_src_labels(spec)
        if dst not in dsts:
            raise ValueError('Invalid argument for destination of mixer.')
        if src not in srcs:
            raise ValueError('Invalid argument for source of mixer.')

        offset = dsts.index(dst) * spec['avail'] * 2 * 4

        if src.find('stream-') == 0:
            offset += spec['avail'] * 4
            srcs = cls.__generate_labels(spec, 'stream')

        return offset + srcs.index(src) * 4
