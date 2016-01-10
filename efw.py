#!/usr/bin/env python3

import sys
from echoaudio.fireworks import Fireworks

argv = sys.argv
argc = len(argv)

if argc < 2:
    print('help')

card = argv[1]

try:
    unit = Fireworks(card)
except Exception as e:
    print(e)
    sys.exit()

info = unit.info
print(info)
print(unit.get_metering())

print(unit.get_box_states())

for ch in range(len(info['phys-outputs'])):
    print(unit.get_phys_out_gain(ch))
    print(unit.get_phys_out_mute(ch))
    print(unit.get_phys_out_nominal(ch))

for ch in range(len(info['phys-inputs'])):
    print(unit.get_phys_in_nominal(ch))

for ch in range(info['playback-channels']):
    print(unit.get_playback_gain(ch))
    print(unit.get_playback_mute(ch))
    print(unit.get_playback_solo(ch))

for in_ch in range(info['capture-channels']):
    for out_ch in range(info['playback-channels']):
        print(unit.get_monitor_gain(in_ch, out_ch))
        print(unit.get_monitor_mute(in_ch, out_ch))
        print(unit.get_monitor_solo(in_ch, out_ch))
        print(unit.get_monitor_pan(in_ch, out_ch))

if info['features']['control-room-mirroring']:
    print(unit.get_control_room_mirroring())
if info['features']['aesebu-xlr'] or info['features']['spdif-coax'] or \
   info['features']['spdif-opt'] or info['features']['adat-opt']:
    print(unit.get_digital_input_mode())
if info['features']['phantom-powering']:
    print(unit.get_phantom_powering())
if info['features']['rx-mapping'] or info['features']['tx-mapping']:
    print(unit.get_stream_mapping())
