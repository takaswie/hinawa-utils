# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

__all__ = ['AvcGeneral', 'AvcConnection']

class AvcGeneral():
    SUBUNIT_TYPES = ('monitor', 'audio', 'printer', 'disc',
                     'tape-recorder-player', 'tuner', 'ca', 'camera',
                     'reserved', 'panel', 'bulletin-board', 'camera storate',
                     'music')

    @classmethod
    def command_control(cls, fcp, cmd):
        if not isinstance(fcp, Hinawa.FwFcp):
            raise ValueError('Invalid argument for FwFcp')
        if cmd[0] != 0x00:
            raise ValueError('Invalid command code for control')
        params = fcp.transact(cmd)
        if   params[0] == 0x08:
            raise OSError('Not implemented')
        elif params[0] == 0x0a:
            raise OSError('Rejected')
        elif params[0] != 0x09:
            raise OSError('Unknown status')
        return params

    @classmethod
    def command_status(cls, fcp, cmd):
        if not isinstance(fcp, Hinawa.FwFcp):
            raise ValueError('Invalid argument for FwFcp')
        if cmd[0] != 0x01:
            raise ValueError('Invalid command code for status')
        params = fcp.transact(cmd)
        if   params[0] == 0x08:
            raise OSError('Not implemented')
        elif params[0] == 0x0a:
            raise OSError('Rejected')
        elif params[0] == 0x0b:
            raise OSError('In transition')
        elif params[0] != 0x0c:
            raise OSError('Unknown status')
        return params

    @classmethod
    def command_inquire(cls, fcp, cmd):
        if not isinstance(fcp, Hinawa.FwFcp):
            raise ValueError('Invalid argument for FwFcp')
        if cmd[0] != 0x02:
            raise ValueError('Invalid command code for inquire')
        params = fcp.transact(cmd)
        if   params[0] == 0x08:
            raise OSError('Not Implemented')
        elif params[0] != 0x0c:
            raise OSError('Unknown status')

    @classmethod
    def get_unit_info(cls, fcp):
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x30)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        params = cls.command_status(fcp, args)
        info = {}
        info['unit-type'] = params[4] >> 3
        info['unit'] = params[4] & 0x07
        info['company-id'] = (params[5], params[6], params[7])
        return info

    @classmethod
    def get_subunit_info(cls, fcp, page):
        if page > 7:
            raise ValueError('Invalid argument for page number')
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x31)
        args.append(page << 4 | 0x07)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        params = cls.command_status(fcp, args)
        info = {}
        info['subunit-type'] = cls.SUBUNIT_TYPES[params[4] >> 3]
        info['maximum-id'] = params[4] & 0x07
        # ignoring extended_subunit_type and extended_subunit_ID
        return info

    @classmethod
    def set_vendor_dependent(cls, fcp, company_ids, deps):
        if len(company_ids) != 3:
            raise ValueError('Invalid array for company ID')
        if len(deps) == 0:
            raise ValueError('Invalid data for vendor dependent field')
        args = bytearray()
        args.append(0x00)   # Control
        args.append(0xff)   # Unit
        args.append(0x00)   # Vendor dependent command
        for b in company_ids:
            args.append(b)
        for b in deps:
            args.append(b)
        cls.command_control(fcp, args)

    @classmethod
    def get_vendor_dependent(cls, fcp, company_ids, deps):
        if len(company_ids) != 3:
            raise ValueError('Invalid array for company ID')
        if len(deps) == 0:
            raise ValueError('Invalid data for vendor dependent field')
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x00)
        for b in company_ids:
            args.append(b)
        for b in deps:
            args.append(b)
        params = cls.command_status(fcp, args)
        return params[6:]

class AvcConnection():
    plug_direction = ('output', 'input')
    sampling_rates = (32000, 44100, 48000, 88200, 96000, 176400, 192000)

    @classmethod
    def get_unit_plug_info(cls, fcp):
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x02)   # Plug info
        args.append(0x00)   # Serial Bus Isochronous and External Plug
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(fcp, args)
        return {'isoc': {
                    'input':    params[4],
                    'output':   params[5]},
                'external': {
                    'input':    params[6],
                    'output':   params[7]}}

    @classmethod
    def get_subunit_plug_info(cls, fcp, subunit_type, subunit_id):
        if subunit_type not in AvcGeneral.SUBUNIT_TYPES:
            raise ValueError('Invalid argument for subunit type')
        if subunit_id > 7:
            raise ValueError('Invalid argument for subunit id')
        args = bytearray()
        args.append(0x01)
        args.append((AvcGeneral.SUBUNIT_TYPES.index(subunit_type) << 3) | subunit_id)
        args.append(0x02)
        args.append(0x00)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(fcp, args)
        # Consider that destination is input and source is output.
        return {'input': params[4], 'output': params[5]}

    @classmethod
    def set_plug_signal_format(cls, fcp, direction, plug, rate):
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        if direction not in AvcConnection.plug_direction:
            raise ValueError('Invalid argument for plug direction')
        if rate not in AvcConnection.sampling_rates:
            raise ValueError('Invalid argument for sampling rate')
        args = bytearray()
        args.append(0x00)
        args.append(0xff)
        args.append(0x18 + AvcConnection.plug_direction.index(direction))
        args.append(plug)
        args.append(0x90)
        args.append(AvcConnection.sampling_rates.index(rate))
        args.append(0xff)
        args.append(0xff)
        AvcGeneral.command_control(fcp, args)

    @classmethod
    def get_plug_signal_format(cls, fcp, direction, plug):
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        if direction not in AvcConnection.plug_direction:
            raise ValueError('Invalid argument for plug direction')
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x18 + AvcConnection.plug_direction.index(direction))
        args.append(plug)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(fcp, args)
        param = params[5] & 0x07
        if param > len(AvcConnection.sampling_rates):
            raise OSError
        return AvcConnection.sampling_rates[param]

    @classmethod
    def ask_plug_signal_format(cls, fcp, direction, plug, rate):
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        if direction not in AvcConnection.plug_direction:
            raise ValueError('Invalid argument for plug direction')
        if rate not in AvcConnection.sampling_rates:
            raise ValueError('Invalid argument for sampling rate')
        args = bytearray()
        args.append(0x02)
        args.append(0xff)
        args.append(0x18 + AvcConnection.plug_direction.index(direction))
        args.append(plug)
        args.append(0x90)
        args.append(AvcConnection.sampling_rates.index(rate))
        args.append(0xff)
        args.append(0xff)
        try:
            AvcGeneral.command_inquire(fcp, args)
        except OSError:
            return False
        return True
