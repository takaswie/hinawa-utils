#!/usr/bin/env python3

import sys

from echoaudio.eft import Fireworks

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

for key in unit.supported_features:
    print(key, unit.supported_features[key])

for key in unit.supported_clock_sources:
    print(key, unit.supported_clock_sources[key])

for key in unit.supported_sampling_rates:
    print(key, unit.supported_sampling_rates[key])

for key in unit.firmware_versions:
    print(key, unit.firmware_versions[key])

for kind in unit.phys_outputs:
    print(kind)

for kind in unit.phys_inputs:
    print(kind)

for channel in range(len(unit.phys_outputs)):
    print('Phys output: {0}'.format(channel))
    try:
        print(unit.phys_output_get_param('gain', channel))
        print(unit.phys_output_get_param('mute', channel))
        print(unit.phys_output_get_param('nominal', channel))
    except Exception as e:
        print(e)

for channel in range(unit.mixer_playback_channels):
    print('Mixer playback {0}'.format(channel))
    try:
        print(unit.playback_get_param('gain', channel))
        print(unit.playback_get_param('mute', channel))
        print(unit.playback_get_param('solo', channel))
    except Exception as e:
        print(e)

for input in range(len(unit.phys_inputs)):
   for output in range(len(unit.phys_outputs)):
       print('Monitoring from {0} to {1}'.format(input, output))
       try:
           print(unit.monitor_get_param('gain', input, output))
           print(unit.monitor_get_param('mute', input, output))
           print(unit.monitor_get_param('solo', input, output))
           print(unit.monitor_get_param('pan', input, output))
       except Exception as e:
           print(e)

print(unit.ioconf_get_stream_mapping())
print(unit.hwctl_get_clock())
print(unit.hwctl_get_box_states())

offset = unit.flash_get_session_offset()
print(unit.flash_read_block(offset, 1))

unit.unlisten()

sys.exit()
