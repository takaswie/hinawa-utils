from gi.repository import Hinawa

class AvcGeneral():
    plug_direction = ('output', 'input')
    subunit_types = ('monitor', 'audio', 'printer', 'disc',
                     'tape-recorder-player', 'tuner', 'ca', 'camera',
                     'reserved', 'panel', 'bulletin-board', 'camera storate',
                     'music')

    @staticmethod
    def command_control(unit, cmd):
        if isinstance(unit, Hinawa.SndUnit):
            params = unit.fcp_transact(cmd)
        elif isinstance(unit, Hinawa.FwFcp):
            params = unit.transact(cmd)
        else:
            raise ValueError('Invalid argument for SndUnit')
        if   params[0] == 0x08:
            raise IOError('Not implemented')
        elif params[0] == 0x0a:
            raise IOError('Rejected')
        elif params[0] != 0x09:
            raise IOError('Unknown status')
        return params

    @staticmethod
    def command_status(unit, cmd):
        if isinstance(unit, Hinawa.SndUnit):
            params = unit.fcp_transact(cmd)
        elif isinstance(unit, Hinawa.FwFcp):
            params = unit.transact(cmd)
        else:
            raise ValueError('Invalid argument for SndUnit')
        if   params[0] == 0x08:
            raise IOError('Not implemented')
        elif params[0] == 0x0a:
            raise IOError('Rejected')
        elif params[0] == 0x0b:
            raise IOError('In transition')
        elif params[0] != 0x0c:
            raise IOError('Unknown status')
        return params

    @staticmethod
    def command_inquire(unit, cmd):
        if isinstance(unit, Hinawa.SndUnit):
            params = unit.fcp_transact(cmd)
        elif isinstance(unit, Hinawa.FwFcp):
            params = unit.transact(cmd)
        else:
            raise ValueError('Invalid argument for SndUnit')
        if   params[0] == 0x08:
            raise IOError('Not Implemented')
        elif params[0] != 0x0c:
            raise IOError('Unknown status')

    @staticmethod
    def get_unit_info(unit):
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x30)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        info = {}
        info['unit-type'] = params[4] >> 3
        info['unit'] = params[4] & 0x07
        info['company-id'] = (params[5], params[6], params[7])
        return info

    @staticmethod
    def get_subunit_info(unit, page):
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
        params = AvcGeneral.command_status(unit, args)
        info = {}
        info['subunit-type'] = AvcGeneral.subunit_types[params[4] >> 3]
        info['maximum-id'] = params[4] & 0x07
        # ignoring extended_subunit_type and extended_subunit_ID
        return info

    @staticmethod
    def set_vendor_dependent(unit, company_ids, deps):
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
        AvcGeneral.command_control(unit, args)

    @staticmethod
    def get_vendor_dependent(unit, company_ids, deps):
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
        params = AvcGeneral.command_status(unit, args)
        return params[6:]

class AvcConnection():
    sampling_rates = (32000, 44100, 48000, 88200, 96000, 176400, 192000)

    @staticmethod
    def get_unit_plug_info(unit):
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x02)   # Plug info
        args.append(0x00)   # Serial Bus Isochronous and External Plug
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        return {'isoc': {
                    'input':    params[4],
                    'output':   params[5]},
                'external': {
                    'input':    params[6],
                    'output':   params[7]}}

    @staticmethod
    def get_subunit_plug_info(unit, subunit_type, subunit_id):
        if AvcGeneral.subunit_types.count(subunit_type) == 0:
            raise ValueError('Invalid argument for subunit type')
        if subunit_id > 7:
            raise ValueError('Invalid argument for subunit id')
        args = bytearray()
        args.append(0x01)
        args.append((AvcGeneral.subunit_types.index(subunit_type) << 3) | subunit_id)
        args.append(0x02)
        args.append(0x00)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        # Consider that destination is input and source is output.
        return {'input': params[4], 'output': params[5]}

    @staticmethod
    def set_plug_signal_format(unit, direction, plug, rate):
        if unit.get_property('streaming') is True:
            raise RuntimeError('Packet streaming is running')
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        if AvcGeneral.plug_direction.count(direction) == 0:
            raise ValueError('Invalid argument for plug direction')
        if AvcConnection.sampling_rates.count(rate) == 0:
            raise ValueError('Invalid argument for sampling rate')
        args = bytearray()
        args.append(0x00)
        args.append(0xff)
        args.append(0x18 + AvcGeneral.plug_direction.index(direction))
        args.append(plug)
        args.append(0x90)
        args.append(AvcGeneral.sampling_rates.index(rate))
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_control(unit, args)

    @staticmethod
    def get_plug_signal_format(unit, direction, plug):
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        if AvcGeneral.plug_direction.count(direction) == 0:
            raise ValueError('Invalid argument for plug direction')
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x18 + AvcGeneral.plug_direction.index(direction))
        args.append(plug)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        param = params[5] & 0x03
        if param > len(AvcConnection.sampling_rates):
            raise IOError
        return AvcConnection.sampling_rates[param]

    @staticmethod
    def ask_plug_signal_format(unit, direction, plug, rate): 
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        if AvcGeneral.plug_direction.count(direction) == 0:
            raise ValueError('Invalid argument for plug direction')
        if AvcConnection.sampling_rates.count(rate) == 0:
            raise ValueError('Invalid argument for sampling rate')
        args = bytearray()
        args.append(0x02)
        args.append(0xff)
        args.append(0x18 + AvcGeneral.plug_direction.index(direction))
        args.append(plug)
        args.append(0x90)
        args.append(AvcConnection.sampling_rates.index(rate))
        args.append(0xff)
        args.append(0xff)
        try:
            AvcGeneral.command_inquire(unit, args)
        except IOError:
            return False
        return True
