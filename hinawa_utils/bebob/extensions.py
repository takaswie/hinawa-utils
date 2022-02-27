# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.ta1394.general import AvcGeneral
from hinawa_utils.ta1394.streamformat import AvcStreamFormatInfo

import time

__all__ = ['BcoPlugInfo', 'BcoSubunitInfo', 'BcoVendorDependent',
           'BcoStreamFormatInfo']


class BcoPlugInfo():
    ADDR_DIR = ('input', 'output')
    ADDR_MODE = ('unit', 'subunit', 'function-block')
    ADDR_UNIT_TYPE = ('isoc', 'external', 'async')

    PLUG_TYPE = ('IsoStream', 'AsyncStream', 'MIDI', 'Sync', 'Analog',
                 'Digital', 'Clock')
    CH_LOCATION = ('N/A', 'left-front', 'right-front', 'center', 'subwoofer',
                   'left-surround', 'right-surround', 'left-of-center',
                   'right-of-center', 'surround', 'side-left', 'side-right',
                   'top', 'buttom', 'left-front-effect', 'right-front-effect',
                   'no-position')
    PORT_TYPE = ('speaker', 'headphone', 'microphone', 'line', 'spdif',
                 'adat', 'tdif', 'madi', 'analog', 'digital', 'MIDI', 'no-type')

    @classmethod
    def get_unit_addr(cls, addr_dir, addr_unit_type, plug):
        if addr_dir not in cls.ADDR_DIR:
            raise ValueError('Invalid argument for address direction')
        if addr_unit_type not in cls.ADDR_UNIT_TYPE:
            raise ValueError('Invalid argument for address unit type')
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        addr = bytearray()
        addr.append(cls.ADDR_DIR.index(addr_dir))
        addr.append(cls.ADDR_MODE.index('unit'))
        addr.append(cls.ADDR_UNIT_TYPE.index(addr_unit_type))
        addr.append(plug)
        addr.append(0xff)
        # For my purpose.
        addr.append(0xff)
        return addr

    @classmethod
    def get_subunit_addr(cls, addr_dir, subunit_type, subunit_id, plug):
        if addr_dir not in cls.ADDR_DIR:
            raise ValueError('Invalid argument for address direction')
        if subunit_type not in AvcGeneral.SUBUNIT_TYPES:
            raise ValueError('Invalid argument for address subunit type')
        if subunit_id > 7:
            raise ValueError('Invalid argument for address subunit id')
        if plug > 255:
            raise ValueError('Invalid argument for address plug number')
        addr = bytearray()
        addr.append(cls.ADDR_DIR.index(addr_dir))
        addr.append(cls.ADDR_MODE.index('subunit'))
        addr.append(plug)
        addr.append(0xff)
        addr.append(0xff)
        # For my purpose.
        addr.append((AvcGeneral.SUBUNIT_TYPES.index(subunit_type) << 3) |
                    subunit_id)
        return addr

    @classmethod
    def get_function_block_addr(cls, addr_dir, subunit_type, subunit_id,
                                fb_type, fb_id, plug):
        if addr_dir not in cls.ADDR_DIR:
            raise ValueError('Invalid argument for address direction')
        if subunit_type not in AvcGeneral.SUBUNIT_TYPES:
            raise ValueError('Invalid argument for address subunit type')
        if subunit_id > 7:
            raise ValueError('Invalid argument for address subunit id')
        addr = bytearray()
        addr.append(cls.ADDR_DIR.index(addr_dir))
        addr.append(cls.ADDR_MODE.index('function-block'))
        addr.append(fb_type)
        addr.append(fb_id)
        addr.append(plug)
        # For my purpose.
        addr.append((AvcGeneral.SUBUNIT_TYPES.index(subunit_type) << 3) |
                    subunit_id)
        return addr

    @classmethod
    def build_plug_info(cls, info):
        addr = bytearray()
        if info['dir'] not in cls.ADDR_DIR:
            raise ValueError('Invalid address direction')
        addr.append(cls.ADDR_DIR.index(info['dir']))
        if info['mode'] not in cls.ADDR_MODE:
            raise ValueError('Invalid address mode')
        addr.append(cls.ADDR_MODE.index(info['mode']))
        data = info['data']
        if info['mode'] == 'unit':
            if data['unit-type'] not in cls.ADDR_UNIT_TYPE:
                raise ValueError('Invalid address unit type')
            addr.append(cls.ADDR_UNIT_TYPE.index(data['unit-type']))
            addr.append(data['plug'])
            addr.append(0xff)
            addr.append(0xff)
            addr.append(0xff)
        else:
            if data['subunit-type'] not in AvcGeneral.SUBUNIT_TYPES:
                raise ValueError('Invalid address subunit type')
            addr.append(AvcGeneral.SUBUNIT_TYPES.index(data['subunit-type']))
            addr.append(data['subunit-id'])
            addr.append(0xff)
            addr.append(0xff)
            if info['mode'] == 'function-block':
                addr.append(data['function-block-type'])
                addr.append(data['function-block-id'])
                addr.append(data['plug'])
        return addr

    @classmethod
    def parse_plug_addr(cls, addr):
        info = {}
        if addr[0] == 0xff:
            return info
        if addr[0] >= len(cls.ADDR_DIR):
            raise OSError('Unexpected address direction')
        info['dir'] = cls.ADDR_DIR[addr[0]]
        if addr[1] >= len(cls.ADDR_MODE):
            raise OSError('Unexpected address mode in response')
        info['mode'] = cls.ADDR_MODE[addr[1]]
        data = {}
        if info['mode'] == 'unit':
            if addr[2] >= len(cls.ADDR_UNIT_TYPE):
                raise OSError('Unexpected address unit type in response')
            data['unit-type'] = cls.ADDR_UNIT_TYPE[addr[2]]
            data['plug'] = addr[3]
        else:
            if addr[2] >= len(AvcGeneral.SUBUNIT_TYPES):
                raise OSError('Unexpected address subunit type in response')
            data['subunit-type'] = AvcGeneral.SUBUNIT_TYPES[addr[2]]
            data['subunit-id'] = addr[3]
            if info['mode'] == 'subunit':
                data['plug'] = addr[4]
            if info['mode'] == 'function-block':
                data['function-block-type'] = addr[4]
                data['function-block-id'] = addr[5]
                data['plug'] = addr[6]
        info['data'] = data
        return info

    @classmethod
    def get_plug_type(cls, fcp, addr):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x00)   # Info type is 'type'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(fcp, args)
        if params[10] > len(cls.PLUG_TYPE):
            raise OSError('Unexpected value in response')
        return cls.PLUG_TYPE[params[10]]

    @classmethod
    def get_plug_name(cls, fcp, addr):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x01)   # Info type is 'name'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(fcp, args)
        length = params[10]
        if length == 0:
            return ""
        return params[11:11 + length].decode()

    @classmethod
    def get_plug_channels(cls, fcp, addr):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x02)   # Info type is 'the number of channels'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(fcp, args)
        return params[10]

    @classmethod
    def get_plug_ch_name(cls, fcp, addr, pos):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x04)   # Info type is 'channel position name'
        args.append(pos)
        args.append(0xff)
        params = AvcGeneral.command_status(fcp, args)
        length = params[11]
        return params[12:12 + length].decode()

    @classmethod
    def get_plug_clusters(cls, fcp, addr):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x03)   # Info type is 'channel position data'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(fcp, args)
        data = params[10:]
        pos = 0
        clusters = [[] for i in range(data[pos])]
        pos += 1
        for cls in range(len(clusters)):
            num = data[pos]
            pos += 1
            if num == 0:
                break

            clusters[cls] = [[0, 0] for j in range(num)]
            for e in range(len(clusters[cls])):
                clusters[cls][e][0] = data[pos]
                clusters[cls][e][1] = data[pos + 1]
                pos += 2
        return clusters

    @classmethod
    def get_plug_cluster_info(cls, fcp, addr, cluster):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x07)   # Info type is 'cluster info'
        args.append(cluster)
        args.append(0xff)
        params = AvcGeneral.command_status(fcp, args)
        length = params[12]
        return params[13:13 + length].decode()

    @classmethod
    def get_plug_input(cls, fcp, addr):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x05)   # Info type is 'input data'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(fcp, args)
        return cls.parse_plug_addr(params[10:])

    @classmethod
    def get_plug_outputs(cls, fcp, addr):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x06)   # Info type is 'output data'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(fcp, args)
        info = []
        plugs = params[10]
        if plugs != 0xff:
            for i in range(plugs):
                addr = cls.parse_plug_addr(params[11 + i * 7:])
                info.append(addr)
        return info


class BcoSubunitInfo():
    FB_PURPOSE = {
        0x00: 'input-gain',
        0x01: 'output-volume',
        0xff: 'nothing-special'
    }

    @classmethod
    def get_subunit_fb_info(cls, fcp, subunit_type, subunit_id, page, fb_type):
        if subunit_type not in AvcGeneral.SUBUNIT_TYPES:
            raise ValueError('Invalid argument for subunit type')
        if subunit_id > 7:
            raise ValueError('Invalid argument for subunit id')
        args = bytearray(0xff for i in range(30))
        args[0] = 0x01
        args[1] = (AvcGeneral.SUBUNIT_TYPES.index(
            subunit_type) << 3) | subunit_id
        args[2] = 0x31
        args[3] = page
        args[4] = 0xff
        try:
            params = AvcGeneral.command_status(fcp, args)
        except Exception as e:
            if str(e) == 'Not implemented':
                return []
            raise
        entries = []
        for i in range(5):
            if params[5 + 5 * i] == 0xff:
                continue
            entry = {}
            entry['type'] = params[5 + 5 * i]
            entry['id'] = params[6 + 5 * i]
            entry['purpose'] = cls.FB_PURPOSE[params[7 + 5 * i]]
            entry['inputs'] = params[8 + 5 * i]
            entry['outputs'] = params[9 + 5 * i]
            entries.append(entry)
        return entries


class BcoVendorDependent():
    SUPPORTED_SPEC = ('con', 'pro')
    ADDR_DIR = ('input', 'output')

    # For IEC 60958-1, a.k.a. 'concumer' or 'S/PDIF'
    SUPPORTED_CON_STATUS = {
        # name, the number of values
        'consumerUse':             1,
        'linearPCM':               1,
        'copyRight':               1,
        'additionalFormatInfo':    1,
        'channelStatusMode':       1,
        'categoryCode':            1,
        'sourceNumber':            1,
        'channelNumber':           1,
        'samplingFrequency':       1,
        'clkAccuracy':             1,
        'maxWordLength':           1,
        'sampleWordLength':        1,
    }

    # For IEC 60958-3, a.k.a 'professional' or 'AES'
    SUPPORTED_PRO_STATUS = {
        # name, the number of values
        'profesionalUse':          1,
        'linearPCM':               1,
        'audioSignalEmphasis':     1,
        'srcSampleFreqLock':       1,
        'samplingFrequency':       1,
        'channelMode':             1,
        'userBitManagement':       1,
        'auxSampleBitsUse':        1,
        'sourceWordLength':        1,
        'multiChannelDesc':        1,
        'referenceSignal':         1,
        'refSigSamplFreq':         1,
        'scalingFlag':             1,
        'channelOriginData':       4,
        'channelDestData':         4,
        'localSampleAddrCode':     4,
        'timeOfDaySampleAddrCode': 4,
        'reliabilityFlags':        1,
        'cyclicRedundancyCheck':   1,
    }

    __CON_SUBCMDS = {
        'consumerUse':             0x00,
        'linearPCM':               0x01,
        'copyRight':               0x02,
        'additionalFormatInfo':    0x03,
        'channelStatusMode':       0x04,
        'categoryCode':            0x05,
        'sourceNumber':            0x06,
        'channelNumber':           0x07,
        'samplingFrequency':       0x08,
        'clkAccuracy':             0x09,
        'maxWordLength':           0x0a,
        'sampleWordLength':        0x0b,
    }

    __PRO_SUBCMDS = {
        'profesionalUse':          0x00,
        'linearPCM':               0x01,
        'audioSignalEmphasis':     0x02,
        'srcSampleFreqLock':       0x03,
        'samplingFrequency':       0x04,
        'channelMode':             0x05,
        'userBitManagement':       0x06,
        'auxSampleBitsUse':        0x07,
        'sourceWordLength':        0x08,
        'multiChannelDesc':        0x09,
        'referenceSignal':         0x0a,
        'refSigSamplFreq':         0x0b,
        'scalingFlag':             0x0c,
        'channelOriginData':       0x0d,
        'channelDestData':         0x0e,
        'localSampleAddrCode':     0x0f,
        'timeOfDaySampleAddrCode': 0x10,
        'reliabilityFlags':        0x11,
        'cyclicRedundancyCheck':   0x12,
    }

    @classmethod
    def set_digital_channel_status(cls, fcp, spec, name, values):
        if spec == 'con':
            attrs = cls.SUPPORTED_CON_STATUS
            subcmds = cls.__CON_SUBCMDS
        elif spec == 'pro':
            attrs = cls.SUPPORTED_PRO_STATUS
            subcmds = cls.__PRO_SUBCMDS
        else:
            raise ValueError('Invalid argument for specification name')
        if name not in attrs:
            raise ValueError('Invalid argument for attribute name')
        if attrs[name] != 1:
            if type(values) != 'list' or len(values) != attrs[name]:
                raise ValueError('Invalid argument for attribute value length')
        args = bytearray(0xff for i in range(10))
        args[0] = 0x00
        args[1] = 0xff
        args[2] = 0x00
        args[3] = cls.SUPPORTED_SPEC.index(spec)
        args[4] = subcmds[name]
        args[5] = attrs[name]
        if attrs[name] == 1:
            args[6] = values
        else:
            for i in range(len(values)):
                args[6 + i] = values[i]
        AvcGeneral.command_control(fcp, args)

    @classmethod
    def get_digital_channel_status(cls, fcp, spec, name):
        if spec == 'con':
            attrs = cls.SUPPORTED_CON_STATUS
            subcmds = cls.__CON_SUBCMDS
        elif spec == 'pro':
            attrs = cls.SUPPORTED_PRO_STATUS
            subcmds = cls.__PRO_SUBCMDS
        else:
            raise ValueError('Invalid argument for specification name')
        if name not in attrs:
            raise ValueError('Invalid argument for attribute name')
        args = bytearray(0xff for i in range(10))
        args[0] = 0x01
        args[1] = 0xff
        args[2] = 0x00
        args[3] = cls.SUPPORTED_SPEC.index(spec)
        args[4] = subcmds[name]
        args[5] = attrs[name]
        params = AvcGeneral.command_status(fcp, args)
        return params[6:6 + attrs[name]]

    @classmethod
    def get_stream_detection(cls, fcp, company_ids, dir, ext_plug):
        if dir not in cls.ADDR_DIR:
            raise ValueError('Invalid argument for address direction')
        if ext_plug >= 255:
            raise ValueError('Invalid argument for external plug number')
        args = bytearray()
        args.append(0x00)
        args.append(cls.ADDR_DIR.index(dir))
        args.append(ext_plug)
        args.append(0xff)
        params = AvcGeneral.get_vendor_dependent(fcp, company_ids, args)
        if params[0] != args[0] or params[1] != args[1] or params[2] != args[2]:
            raise OSError('Unexpected value in response')
        if params[3] == 0x00:
            return False
        return True


class BcoStreamFormatInfo():
    format_types = ('Compound', 'Sync')
    data_types = ('IEC60958-3',     # 0x00
                  'IEC61937-3',
                  'IEC61937-4',
                  'IEC61937-5',
                  'IEC61937-6',
                  'IEC61937-7',
                  'multi-bit-linear-audio-raw',
                  'multi-bit-linear-audio-DVD-audio',
                  'one-bit-audio-plain-raw',
                  'one-bit-audio-plain-SACD',
                  'one-bit-audio-encoded-raw',
                  'one-bit-audio-encoded-SACD',
                  'high-precision-multi-bit-linear-audio',
                  'MIDI-conformant',
                  'sync-stream',    # 0x40
                  'do-not-care',    # 0xff
                  'reserved')       # the others

    @classmethod
    def get_entry_list(cls, fcp, addr):
        fmts = []
        for i in range(0xff):
            # DM1500 tends to cause timeout.
            time.sleep(0.1)
            try:
                args = bytearray()
                args.append(0x01)
                args.append(addr[5])
                args.append(0x2f)   # Bco stream format support
                args.append(0xc1)   # List request
                args.append(addr[0])
                args.append(addr[1])
                args.append(addr[2])
                args.append(addr[3])
                args.append(addr[4])
                args.append(0xff)
                args.append(i)
                args.append(0xff)
                params = AvcGeneral.command_status(fcp, args)
                fmts.append(cls._parse_format(params[11:]))
            except OSError as e:
                if str(e) != 'Rejected':
                    raise
                else:
                    break
        return fmts

    # Two types of sync stream: 0x90/0x00/0x40 and 0x90/0x40 with 'sync-stream'
    @classmethod
    def _parse_format(cls, params):
        fmt = {}
        # Sync stream with stereo raw audio
        if params[0] == 0x90 and params[1] == 0x00 and params[2] == 0x40:
            ctl = params[4] & 0x01
            rate = params[4] >> 8
            fmt['type'] = 'Sync'
            fmt['rate-control'] = AvcStreamFormatInfo.RATE_CONTROLS[ctl]
            fmt['sampling-rate'] = AvcStreamFormatInfo.SAMPLING_RATES[rate]
            fmt['formation'] = ['multi-bit-linear-audio-raw']
            return fmt
        if params[0] != 0x90 or params[1] != 0x40:
            raise RuntimeError('Unsupported format')
        fmt['type'] = 'Compound'
        fmt['sampling-rate'] = AvcStreamFormatInfo.SAMPLING_RATES[params[2]]
        ctl = params[3] & 0x3
        fmt['rate-control'] = AvcStreamFormatInfo.RATE_CONTROLS[ctl]
        formation = []
        for i in range(params[4]):
            for c in range(params[5 + i * 2]):
                type = params[5 + i * 2 + 1]
                if type <= 0x0f:
                    formation.append(cls.data_types[type])
                elif type == 0x40:
                    formation.append('sync-stream')
                elif type == 0xff:
                    formation.append('do-not-care')
                else:
                    formation.append('reserved')
        fmt['formation'] = formation
        return fmt
