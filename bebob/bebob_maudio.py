#!/usr/bin/env python3

import sys

from bebob.bebob_unit import BebobUnit

class BebobMaudio(BebobUnit):
    meter_labels = ('Analog in 1', 'Analog in 2',
                    'Digital in 1', 'Digital in 2',
                    'Analog out 1', 'Analog out 2',
                    'Analog out 3', 'Analog out 4',
                    'Analog out 5', 'Analog out 6',
                    'Analog out 7', 'Analog out 8',
                    'Digital out 1', 'Digital out 2',
                    'HP out 1', 'HP out 2',
                    'AUX out 1', 'AUX out 2')

    hoge = ('Analog in 1', 'Analog in 2',
     'Digital in 1', 'Digital in 2',
     'Stream in 1', 'Stream in 2', 'Stream in 3', 'Stream in 4',
     'Analog out 1', 'Analog out 2',
     'Digital out 1', 'Digital out 2')

    def __init__(self, path):
        super().__init__(path)

    # 0x0000ffff - 0x7fffffff
    # db = 20 * log10(vol / 0x80000000)
    # vol = 0, then db = -144.0
    #
    # fw410: 19
    # audiophile: 15
    def get_metering(self):
        return self.read_transact(0xffc700600000, 15)
