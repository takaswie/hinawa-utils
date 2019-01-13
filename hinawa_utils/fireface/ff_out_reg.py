# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2019 Takashi Sakamoto


class FFOutRegs():
    @classmethod
    def get_out_labels(cls, spec: dict):
        labels = []
        for i in range(spec['analog']):
            labels.append('analog-{0}'.format(i + 1))
        for i in range(spec['spdif']):
            labels.append('spdif-{0}'.format(i + 1))
        for i in range(spec['adat']):
            labels.append('adat-{0}'.format(i + 1))
        return labels

    @classmethod
    def calculate_out_offset(cls, spec: dict, target):
        targets = cls.get_out_labels(spec)
        return targets.index(target) * 4
