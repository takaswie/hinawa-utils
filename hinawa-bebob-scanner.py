#!/usr/bin/env python3

from bridgeco.bebobnormal import BebobNormal

import sys
import json

argv = sys.argv
argc = len(argv)

if argc < 2:
    print('help')

path = '/dev/fw{0}'.format(argv[1])
unit = BebobNormal(path)

info = {
    'unit': unit.unit_plugs,
    'subunit': unit.subunit_plugs,
    'function-block': unit.function_block_plugs,
}

literal = json.dumps(info)
info = json.loads(literal)
print(info)

for type, dir_plugs in unit.unit_plugs.items():
    for dir, plugs in dir_plugs.items():
        for i, plug in enumerate(plugs):
            print(type, dir, i, plug['name'])

for type, dir_plugs in unit.subunit_plugs.items():
    for dir, plugs in dir_plugs.items():
        for i, plugs in enumerate(plugs):
            print(type, dir, i, plug['name'])

for type, fb_type_plugs in unit.function_block_plugs.items():
    for fb_type, fb_id_plugs in fb_type_plugs.items():
        for fb_id, dir_plugs in enumerate(fb_id_plugs):
            for dir, plugs in dir_plugs.items():
                for i, plug in enumerate(plugs):
                    print(type, fb_type, fb_id + 1, dir, i, plug['name'])

print(unit.signal_destination)

for name, addr in unit.signal_sources.items():
    print(name, addr)

sys.exit()

