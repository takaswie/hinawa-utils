from gi.repository import Hinawa

class AvcGeneral():
    plug_direction = ('output', 'input')
    sampling_rates = (32000, 44100, 48000, 88200, 96000, 176400, 192000)

    @staticmethod
    def command_control(unit, cmd):
        if isinstance(unit, Hinawa.SndUnit) is False:
            raise ValueError('Invalid argument for SndUnit')
        params = unit.fcp_transact(cmd)
        if   params[0] == 0x08:
            raise IOError('Not implemented')
        elif params[0] == 0x0a:
            raise IOError('Rejected')
        elif params[0] != 0x09:
            raise IOError('Unknown status')
        return params

    @staticmethod
    def command_status(unit, cmd):
        if isinstance(unit, Hinawa.SndUnit) is False:
            raise ValueError('Invalid argument for SndUnit')
        params = unit.fcp_transact(cmd)
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
        if isinstance(unit, Hinawa.SndUnit) is False:
            raise ValueError('Invalid argument for SndUnit')
        params = unit.fcp_transact(cmd)
        if   params[0] == 0x08:
            raise IOError('Not Implemented')
        elif params[0] != 0x0c:
            raise IOError('Unknown status')

    @staticmethod
    def set_plug_signal_format(unit, direction, plug, rate):
        if unit.get_property('streaming') is True:
            raise RuntimeError('Packet streaming is running')
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        if unit.plug_direction.count(direction) == 0:
            raise ValueError('Invalid argument for plug direction')
        if unit.sampling_rates.count(rate) == 0:
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
        if param > len(AvcGeneral.sampling_rates):
            raise IOError
        return AvcGeneral.sampling_rates[param]

    @staticmethod
    def ask_plug_signal_format(unit, direction, plug, rate): 
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        if AvcGeneral.plug_direction.count(direction) == 0:
            raise ValueError('Invalid argument for plug direction')
        if AvcGeneral.sampling_rates.count(rate) == 0:
            raise ValueError('Invalid argument for sampling rate')
        args = bytearray()
        args.append(0x02)
        args.append(0xff)
        args.append(0x18 + AvcGeneral.plug_direction.index(direction))
        args.append(plug)
        args.append(0x90)
        args.append(AvcGeneral.sampling_rates.index(rate))
        args.append(0xff)
        args.append(0xff)
        try:
            AvcGeneral.command_inquire(unit, args)
        except IOError:
            return False
        return True

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
        rest = 4 - len(args) % 4
        for i in range(rest):
            args.append(0xff)
        AvcGeneral.command_control(unit, args)

    @staticmethod
    def get_vendor_dependent(unit, company_ids, deps):
        if len(company_ids) != 3:
            raise ValueError('Invalid array for company ID')
        if len(deps) == 0:
            raise ValueError('Invalid data for vendor dependent field')
        args = bytearray()
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x00)
        for b in company_ids:
            args.append(b)
        for b in deps:
            args.append(b)
        rest = 4 - len(args) % 4
        for i in range(rest):
            args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        return params[6:len(params)]
