#!/usr/bin/env python3

import sys

from gi.repository import Hinawa

from ta1394.general import AvcGeneral
from ta1394.general import AvcConnection
from ta1394.streamformat import AvcStreamFormat
from ta1394.audio import AvcAudio
from bridgeco.extendedpluginfo import ExtendedPlugInfo

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
        print(i, AvcAudio.get_selector_param(unit, 0, 'current', i))
    except Exception as e:
        print(e)

for i in range(1, 16):
    try:
        print(i, AvcAudio.get_feature_mute_param(unit, 0, 'current', i, 0))
    except Exception as e:
        print(e)

for i in range(1, 16):
    try:
        print(i, AvcAudio.get_feature_volume_param(unit, 0, 'current', i, 0))
    except Exception as e:
        print(e)

for i in range(1, 16):
    try:
        print(i, AvcAudio.get_feature_lr_param(unit, 0, 'current', i, 0))
    except Exception as e:
        print(e)

print('{0:04x}'.format(AvcAudio.get_processing_mixer_param(unit, 0, 'current', 1, 3, 1, 1)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_param(unit, 0, 'current', 1, 3, 2, 2)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_param(unit, 0, 'current', 1, 4, 1, 1)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_param(unit, 0, 'current', 1, 4, 2, 2)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_param(unit, 0, 'current', 1, 0, 1, 1)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_param(unit, 0, 'current', 1, 0, 2, 2)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_param(unit, 0, 'current', 1, 2, 1, 1)))
print('{0:04x}'.format(AvcAudio.get_processing_mixer_param(unit, 0, 'current', 1, 2, 2, 2)))

print(AvcGeneral.get_unit_info(unit))
print(AvcGeneral.get_subunit_info(unit, 0))
plugs = AvcConnection.get_plug_info(unit)
print(plugs)

for key,count in plugs.items():
    if   key == 'isoc-input':
        type = 'isoc'
        dir = 'input'
    elif key == 'isoc-output':
        type = 'isoc'
        dir = 'output'
    elif key == 'external-input':
        type = 'external'
        dir = 'input'
    elif key == 'external-output':
        type = 'external'
        dir = 'output'
    else:
        print(key)
        break

    for plug in range(count):
        print('{0} {1} {2}'.format(type, dir, plug))
        addr = ExtendedPlugInfo.get_unit_addr(dir, type, plug)

        plug_type = ExtendedPlugInfo.get_plug_type(unit, addr)
        plug_name = ExtendedPlugInfo.get_plug_name(unit, addr)
        chs = ExtendedPlugInfo.get_plug_channels(unit, addr)

        print('    type: {0}'.format(plug_type))
        print('    name: {0}'.format(plug_name))
        for ch in range(chs):
            ch_name = ExtendedPlugInfo.get_plug_ch_name(unit, addr, ch + 1)
            print('    ch: {0}'.format(ch_name))

        if plug_type == 'IsoStream':
            clusters = ExtendedPlugInfo.get_plug_clusters(unit, addr)
            for i in range(len(clusters)):
                info = ExtendedPlugInfo.get_plug_cluster_info(unit, addr, i + 1)
                print('    cls: {0}'.format(info))

        if dir is 'output':
            input = ExtendedPlugInfo.get_plug_input(unit, addr)
            print('    input:')
            for key,value in input.items():
                print('        {0}: {1}'.format(key, value))
            ExtendedPlugInfo.build_plug_info(input)
        else:
            outputs = ExtendedPlugInfo.get_plug_outputs(unit, addr)
            for output in outputs:
                print('    output:')
                for key,value in output.items():
                    print('       {0}: {1}'.format(key, value))
                ExtendedPlugInfo.build_plug_info(output)

sys.exit()

import time

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
    time.sleep(1)
