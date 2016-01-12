#!/usr/bin/env python3

from gi.repository import Hinawa

from ta1394.audio import AvcAudio

import sys
import time
from math import log10

argv = sys.argv
argc = len(argv)

if argc < 2:
	print('help')

card = argv[1]

class BebobMaudio(Hinawa.SndUnit):
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

    def __init__(self, card):
        super().__init__()
        self.open('/dev/snd/hwC{0}D0'.format(card))
        self.listen()

    # 0x0000ffff - 0x7fffffff
    # db = 20 * log10(vol / 0x80000000)
    # vol = 0, then db = -144.0
    #
    # fw410: 19
    # audiophile: 15
    def get_metering(self):
        return self.read_transact(0xffc700600000, 15)

unit = BebobMaudio(card)

for i in range(1, 8):
    try:
        print(i, AvcAudio.get_selector_state(unit, 0, 'current', i))
    except Exception as e:
        print(e)

for i in range(1, 16):
    try:
        print(i, AvcAudio.get_feature_mute_state(unit, 0, 'current', i, 0))
    except Exception as e:
        print(e)

for i in range(1, 16):
    try:
        print(i, AvcAudio.get_feature_volume_state(unit, 0, 'current', i, 0))
    except Exception as e:
        print(e)

for i in range(1, 16):
    try:
        print(i, AvcAudio.get_feature_lr_state(unit, 0, 'current', i, 0))
    except Exception as e:
        print(e)

print('{0:04x}'.format(AvcAudio.get_processing_mixer_state(unit, 0, 'current', 1, 3, 1, 1)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_state(unit, 0, 'current', 1, 3, 2, 2)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_state(unit, 0, 'current', 1, 4, 1, 1)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_state(unit, 0, 'current', 1, 4, 2, 2)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_state(unit, 0, 'current', 1, 0, 1, 1)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_state(unit, 0, 'current', 1, 0, 2, 2)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_state(unit, 0, 'current', 1, 2, 1, 1)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_state(unit, 0, 'current', 1, 2, 2, 2)))

print(AvcAudio.get_processing_mixer_state_all(unit, 0, 'current', 1, 2))
print(AvcAudio.get_processing_mixer_state_all(unit, 0, 'minimum', 1, 2))
print(AvcAudio.get_processing_mixer_state_all(unit, 0, 'maximum', 1, 2))
print(AvcAudio.get_processing_mixer_state_all(unit, 0, 'resolution', 1, 2))
print(AvcAudio.get_processing_mixer_state_all(unit, 0, 'default', 1, 2))

for i in range(0, 100):
    meters = unit.get_metering()
    for i in range(len(unit.hoge)):
        vol = meters[i]
        if vol == 0:
            db = -144
        else:
            db = int(20 * log10(vol / 0x80000000))
        print('{0: >15}: {1: >8}'.format(unit.hoge[i], db))
    print('{0:08x}'.format(meters[-1]))
    time.sleep(0.2)
