from ta1394.general import AvcGeneral

class ExtendedPlugInfo():
    addr_dir  = ('input', 'output')
    addr_mode = ('unit', 'subunit', 'function-block')
    addr_unit_type = ('isoc', 'external', 'async')

    plug_type = ('IsoStream', 'AsyncStream', 'MIDI', 'Sync', 'Analog',
                 'Digital')
    ch_location = ('N/A', 'left-front', 'right-front', 'center', 'subwoofer',
                   'left-surround', 'right-surround', 'left-of-center',
                   'right-of-center', 'surround', 'side-left', 'side-right',
                   'top', 'buttom', 'left-front-effect', 'right-front-effect',
                   'no-position')
    port_type = ('speaker', 'headphone', 'microphone', 'line', 'spdif',
                 'adat', 'tdif', 'madi', 'analog', 'digital', 'MIDI', 'no-type')

    @staticmethod
    def get_unit_addr(addr_dir, addr_unit_type, plug):
        if ExtendedPlugInfo.addr_dir.count(addr_dir) == 0:
            raise ValueError('Invalid argument for address direction')
        if ExtendedPlugInfo.addr_unit_type.count(addr_unit_type) == 0:
            raise ValueError('Invalid argumetn for address unit type')
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        addr = bytearray()
        addr.append(ExtendedPlugInfo.addr_dir.index(addr_dir))
        addr.append(ExtendedPlugInfo.addr_mode.index('unit'))
        addr.append(ExtendedPlugInfo.addr_unit_type.index(addr_unit_type))
        addr.append(plug)
        addr.append(0xff)
        return addr

    @staticmethod
    def get_subunit_addr(addr_dir, subunit_type, subunit_id, plug):
        if ExtendedPlugInfo.addr_dir.count(addr_dir) == 0:
            raise ValueError('Invalid argument for address direction')
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        addr = bytearray()
        addr.append(ExtendedPlugInfo.addr_dir.index(addr_dir))
        addr.append(ExtendedPlugInfo.addr_mode.index('subunit'))
        addr.append(subunit_id)
        addr.append(plug)
        addr.append(0xff)
        return addr

    @staticmethod
    def get_function_block_addr(addr_dir, fb_type, fb_id, plug):
        if ExtendedPlugInfo.addr_dir.count(addr_dir) == 0:
            raise ValueError('Invalid argument for address direction')
        addr = bytearray()
        addr.append(ExtendedPlugInfo.addr_dir.index(addr_dir))
        addr.append(ExtendedPlugInfo.addr_mode.index('function-block'))
        addr.append(fb_type)
        addr.append(fb_id)
        addr.append(plug)
        return addr

    @staticmethod
    def build_plug_info(info):
        addr = bytearray()
        if ExtendedPlugInfo.addr_dir.count(info['dir']) == 0:
            raise ValueError('Invalid address direction')
        addr.append(ExtendedPlugInfo.addr_dir.index(info['dir']))
        if ExtendedPlugInfo.addr_mode.count(info['mode']) == 0:
            raise ValueError('Invalid address mode')
        addr.append(ExtendedPlugInfo.addr_mode.index(info['mode']))
        data = info['data']
        if info['mode'] == 'unit':
            if ExtendedPlugInfo.addr_unit_type.count(data['unit-type']) == 0:
                raise ValueError('Invalid address unit type')
            addr.append(ExtendedPlugInfo.addr_unit_type.index(data['unit-type']))
            addr.append(data['plug'])
            addr.append(0xff)
            addr.append(0xff)
            addr.append(0xff)
        else:
            if AvcGeneral.subunit_types.count(data['subunit-type']) == 0:
                raise ValueError('Invalid address subunit type')
            addr.append(AvcGeneral.subunit_types.index(data['subunit-type']))
            addr.append(data['subunit-id'])
            addr.append(0xff)
            addr.append(0xff)
            if info['mode'] is 'function-block':
                addr.append(data['function-block-type'])
                addr.append(data['function-block-id'])
                addr.append(data['plug'])
        return addr

    @staticmethod
    def parse_plug_addr(addr):
        info = {}
        if addr[0] == 0xff:
            return info
        if addr[0] >= len(ExtendedPlugInfo.addr_dir):
            raise IOError('Unexpected address direction')
        info['dir'] = ExtendedPlugInfo.addr_dir[addr[0]]
        if addr[1] >= len(ExtendedPlugInfo.addr_mode):
            raise IOError('Unexpected address mode in response')
        info['mode'] = ExtendedPlugInfo.addr_mode[addr[1]]
        data = {}
        if info['mode'] == 'unit':
            if addr[2] >= len(ExtendedPlugInfo.addr_unit_type):
                raise IOError('Unexpected address unit type in response')
            data['unit-type'] = ExtendedPlugInfo.addr_unit_type[addr[2]]
            data['plug'] = addr[3]
        else:
            if addr[2] >= len(AvcGeneral.subunit_types):
                raise IOError('Unexpected address subunit type in response')
            data['subunit-type'] = AvcGeneral.subunit_types[addr[2]]
            data['subunit-id'] = addr[3]
            if info['mode'] == 'subunit':
                data['plug'] = addr[4]
            if info['mode'] == 'function-block':
                data['function-block-type'] = addr[2]
                data['function-block-id'] = addr[3]
                data['plug'] = addr[4]
        info['data'] = data
        return info

    @staticmethod
    def get_plug_type(unit, addr):
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Extended plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x00)   # Info type is 'type'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        if params[10] > len(ExtendedPlugInfo.plug_type):
            raise IOError('Unexpected value in response')
        return ExtendedPlugInfo.plug_type[params[10]]

    @staticmethod
    def get_plug_name(unit, addr):
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Extended plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x01)   # Info type is 'name'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        length = params[10]
        if length == 0:
            return ""
        return params[11:11 + length].decode()

    @staticmethod
    def get_plug_channels(unit, addr):
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Extended plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x02)   # Info type is 'the number of channels'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        return params[10]

    @staticmethod
    def get_plug_ch_name(unit, addr, pos):
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Extended plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x04)   # Info type is 'channel position name'
        args.append(pos)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        length = params[11]
        return params[12:12+length].decode()

    @staticmethod
    def get_plug_clusters(unit, addr):
        if addr[1] != ExtendedPlugInfo.addr_mode.index('unit') or \
           addr[2] != ExtendedPlugInfo.addr_unit_type.index('isoc'):
            raise ValueError('Isochronous unit plugs just support this')
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Extended plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x03)   # Info type is 'channel position data'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        data = params[10:]
        pos = 0
        clusters = [[] for i in range(data[pos])]
        pos += 1
        for cls in range(len(clusters)):
            num = data[pos]
            pos += 1
            if num == 0:
                break;

            clusters[cls] = [[0, 0] for j in range(num)]
            for e in range(len(clusters[cls])):
                clusters[cls][e][0] = data[pos];
                clusters[cls][e][1] = data[pos + 1];
                pos += 2
        return clusters

    @staticmethod
    def get_plug_cluster_info(unit, addr, cls):
        if addr[1] != ExtendedPlugInfo.addr_mode.index('unit') or \
           addr[2] != ExtendedPlugInfo.addr_unit_type.index('isoc'):
            raise ValueError('Isochronous unit plugs just support this')
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Extended plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x07)   # Info type is 'cluster info'
        args.append(cls)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        length = params[12]
        return params[13:13+length].decode()

    @staticmethod
    def get_plug_input(unit, addr):
        if ExtendedPlugInfo.addr_dir[addr[0]] == 'input':
            raise ValueError('Invalid argument. Output plug is just supported')
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Extended plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x05)   # Info type is 'input data'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        return ExtendedPlugInfo.parse_plug_addr(params[10:])

    @staticmethod
    def get_plug_outputs(unit, addr):
        if ExtendedPlugInfo.addr_dir[addr[0]] == 'output':
            raise ValueError('Invalid argument. Input plug is just supported')
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Extended plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x06)   # Info type is 'output data'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        info = []
        plugs = params[10]
        if plugs != 0xff:
            for i in range(plugs):
                data = params[11:11 + i * 7]
                info.append(ExtendedPlugInfo.parse_plug_addr(addr))
        return info
