from ta1394.general import AvcGeneral

class AvcCcm():
    plug_mode = ('unit', 'subunit')
    plug_unit_type = ('isoc', 'external')

    @staticmethod
    def get_unit_signal_addr(type, plug):
        if AvcCcm.plug_unit_type.count(type) == 0:
            raise ValueError('Invalid argument for plug unit type')
        if plug >= 30:
            raise ValueError('Invalid argument for plug number')
        addr = bytearray()
        addr.append(0xff)
        if type == 'isoc':
            addr.append(plug)
        else:
            addr.append(0x80 + plug)
        return addr

    @staticmethod
    def get_subunit_signal_addr(type, id, plug):
        if AvcGeneral.subunit_types.count(type) == 0:
            raise ValueError('Invalid argument for subunit type')
        if plug >= 30:
            raise ValueError('Invalid argument for plug number')
        addr = bytearray()
        addr.append((AvcGeneral.subunit_types.index(type) << 3) | id)
        addr.append(plug)
        return addr

    @staticmethod
    def parse_signal_addr(addr):
        info = {}
        data = {}
        if addr[0] == 0xff:
            info['mode'] = 'unit'
            if addr[1] & 0x80:
                data['type'] = 'external'
                data['plug'] = addr[1] - 0x80
            else:
                data['type'] = 'isoc'
                data['plug'] = addr[1]
        else:
            info['mode'] = 'subunit'
            data['type'] = AvcGeneral.subunit_types[addr[0] >> 3]
            data['id'] = addr[0] & 0x07
            data['plug'] = addr[1]
        info['data'] = data
        return info

    @staticmethod
    def set_signal_source(fcp, src, dst):
        args = bytearray()
        args.append(0x00)
        args.append(0xff)
        args.append(0x1a)
        args.append(0x0f)
        args.append(src[0])
        args.append(src[1])
        args.append(dst[0])
        args.append(dst[1])
        return AvcGeneral.command_control(fcp, args)

    @staticmethod
    def get_signal_source(fcp, dst):
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x1a)
        args.append(0xff)
        args.append(0xff)
        args.append(0xfe)
        args.append(dst[0])
        args.append(dst[1])
        params = AvcGeneral.command_status(fcp, args)
        return AvcCcm.parse_signal_addr(params[6:])

    @staticmethod
    def ask_signal_source(fcp, src, dst):
        args = bytearray()
        args.append(0x02)
        args.append(0xff)
        args.append(0x1a)
        args.append(0xff)
        args.append(src[0])
        args.append(src[1])
        args.append(dst[0])
        args.append(dst[1])
        AvcGeneral.command_inquire(fcp, args)
