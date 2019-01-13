# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto


class FFMixerRegs():
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
    def calculate_src_offset(cls, spec: dict, dst: str, src: str):
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
