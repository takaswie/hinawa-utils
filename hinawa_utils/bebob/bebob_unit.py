# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from threading import Thread
from struct import unpack

import gi
gi.require_version('GLib', '2.0')
gi.require_version('Hinawa', '2.0')
from gi.repository import GLib, Hinawa

from hinawa_utils.ta1394.general import AvcGeneral, AvcConnection
from hinawa_utils.ta1394.ccm import AvcCcm

from hinawa_utils.bebob.config_rom_parser import BebobConfigRomParser
from hinawa_utils.bebob.extensions import BcoPlugInfo

__all__ = ['BebobUnit']


class BebobUnit(Hinawa.SndUnit):
    REG_INFO = 0xffffc8020000

    def __init__(self, path):
        super().__init__()
        self.open(path)
        if self.get_property('type') != 3:
            raise ValueError('The character device is not for BeBoB unit')

        ctx = GLib.MainContext.new()
        self.create_source().attach(ctx)
        self.__unit_dispatcher = GLib.MainLoop.new(ctx, False)
        self.__unit_th = Thread(target=lambda d: d.run(), args=(self.__unit_dispatcher, ))
        self.__unit_th.start()

        node = self.get_node()
        ctx = GLib.MainContext.new()
        node.create_source().attach(ctx)
        self.__node_dispatcher = GLib.MainLoop.new(ctx, False)
        self.__node_th = Thread(target=lambda d: d.run(), args=(self.__node_dispatcher, ))
        self.__node_th.start()

        parser = BebobConfigRomParser()
        info = parser.parse_rom(self.get_config_rom())
        self.vendor_id = info['vendor-id']
        self.model_id = info['model-id']

        self.fcp = Hinawa.FwFcp()
        self.fcp.bind(self.get_node())
        self.firmware_info = self._get_firmware_info()

    def release(self):
        self.fcp.unbind()
        self.__unit_dispatcher.quit()
        self.__node_dispatcher.quit()
        self.__unit_th.join()
        self.__node_th.join()

    def _get_firmware_info(self):
        def _get_string_literal(params):
            if 0x00 in params:
                return '00000000'
            return params.decode('US-ASCII')

        def _get_time_literal(params):
            if 0x00 in params:
                return '000000'
            return params.decode('US-ASCII')

        req = Hinawa.FwReq()
        params = req.read(self, BebobUnit.REG_INFO, 104)

        info = {}
        info['manufacturer'] = _get_string_literal(params[0:8])
        info['protocol-version'] = unpack('<I', params[8:12])[0]
        info['guid'] = (unpack('<Q', params[12:20])[0] << 32) | \
            unpack('<I', params[20:24])[0]
        info['model-id'] = unpack('<I', params[24:28])[0]
        info['model-revision'] = unpack('<I', params[28:32])[0]
        info['software'] = {
            'build-date':   _get_string_literal(params[32:40]),
            'build-time':   _get_time_literal(params[40:46]),
            'id':           unpack('<I', params[48:52])[0],
            'version':      unpack('<I', params[52:56])[0],
            'base-address': unpack('<I', params[56:60])[0],
            'max-size':     unpack('<I', params[60:64])[0],
        }
        info['bootloader'] = {
            'build-date':   _get_string_literal(params[64:72]),
            'build-time':   _get_time_literal(params[72:80]),
        }
        info['debugger'] = {
            'build-date':   _get_string_literal(params[80:88]),
            'build-time':   _get_string_literal(params[88:96]),
            'id':           unpack('<I', params[96:100])[0],
            'version':      unpack('<I', params[100:104])[0],
        }

        return info

    def get_unit_plug_list(self):
        plugs = {}
        seqid = 0

        units = AvcConnection.get_unit_plug_info(self.fcp)
        for type, data in units.items():
            for direction, count in data.items():
                for plug_id in range(count):
                    # Use the same format as Plug Input/Output Specific Data
                    # to keep enough informaton.
                    plug_info = {
                        'dir': direction,
                        'mode': 'unit',
                        'data': {
                            'unit-type': type,
                            'plug': plug_id,
                        },
                    }
                    plugs['unit_{0}'.format(seqid)] = plug_info
                    seqid += 1

        return plugs

    def _get_subunit_plug_info(self):
        subunits = {}
        for page in range(AvcGeneral.MAXIMUM_SUBUNIT_PAGE + 1):
            try:
                info = AvcGeneral.get_subunit_info(self.fcp, page)
            except:
                break

            for entry in info:
                subunit_type = entry['type']
                maximum_id = entry['maximum-id']

                for subunit_id in range(maximum_id + 1):
                    try:
                        data = AvcConnection.get_subunit_plug_info(self.fcp,
                                                    subunit_type, subunit_id)
                    except:
                        continue

                    id = (subunit_type, subunit_id)
                    if id not in subunits:
                        subunits[id] = {}
                    for direction, count in data.items():
                        subunits[id][direction] = count

        return subunits

    def get_subunit_plug_list(self):
        plugs = {}
        seqid = 0

        subunits = self._get_subunit_plug_info()
        for id, data in subunits.items():
            for direction, count in data.items():
                for plug_id in range(count):
                    # Use the same format as Plug Input/Output Specific Data
                    # to keep enough informaton.
                    plug_info = {
                        'dir': direction,
                        'mode': 'subunit',
                        'data': {
                            'subunit-type': id[0],
                            'subunit-id': id[1],
                            'plug': plug_id,
                        },
                    }
                    plugs['subunit_{0}'.format(seqid)] = plug_info
                    seqid += 1

        return plugs

    def get_avail_connections(self, unit_plug_list, subunit_plug_list):
        src_candidates = {}
        dst_candidates = {}
        avail = {}

        for seqid, info in unit_plug_list.items():
            data = info['data']
            addr = AvcCcm.get_unit_signal_addr(data['unit-type'], data['plug'])
            if info['dir'] == 'output':
                target = dst_candidates
            else:
                target = src_candidates
            target[seqid] = addr

        for seqid, info in subunit_plug_list.items():
            data = info['data']
            addr = AvcCcm.get_subunit_signal_addr(data['subunit-type'],
                                            data['subunit-id'], data['plug'])
            # Inverse direction against plugs of unit.
            if info['dir'] == 'output':
                target = src_candidates
            else:
                target = dst_candidates
            target[seqid] = addr

        for dst_seqid, dst_addr in dst_candidates.items():
            try:
                curr_src_info = AvcCcm.get_signal_source(self.fcp, dst_addr)
            except:
                curr_src_info = None

            for src_seqid, src_addr in src_candidates.items():
                try:
                    AvcCcm.ask_signal_source(self.fcp, src_addr, dst_addr)
                except:
                    continue

                if dst_seqid not in avail:
                    avail[dst_seqid] = []

                src_info = AvcCcm.parse_signal_addr(src_addr)
                avail[dst_seqid].append((src_seqid, src_info == curr_src_info))

        return avail

    def get_plug_spec(self, info):
        data = info['data']
        if info['mode'] == 'unit':
            addr = BcoPlugInfo.get_unit_addr(info['dir'],
                                             data['unit-type'], data['plug'])
        elif info['mode'] == 'subunit':
            addr = BcoPlugInfo.get_subunit_addr(info['dir'],
                    data['subunit-type'], data['subunit-id'], data['plug'])
        else:
            raise ValueError('Invalid mode of plug info.')

        spec = {
            'name': BcoPlugInfo.get_plug_name(self.fcp, addr),
            'type': BcoPlugInfo.get_plug_type(self.fcp, addr),
        }

        if info['dir'] == 'input':
            spec['input'] = BcoPlugInfo.get_plug_input(self.fcp, addr),
        else:
            spec['outputs'] = BcoPlugInfo.get_plug_outputs(self.fcp, addr),

        return spec

        if info['mode'] == 'unit':
            spec['clusters'] = []
            clusters = BcoPlugInfo.get_plug_clusters(self.fcp, addr)

            for i, cluster in enumerate(clusters):
                mapping = []
                name = BcoPlugInfo.get_plug_cluster_info(self.fcp, addr, i + 1)
                for info in cluster:
                    idx, pos = info
                    ch_name = BcoPlugInfo.get_plug_ch_name(self.fcp, addr, idx)
                    mapping.append(ch_name)
                entry = {
                    'name': name,
                    'channels': mapping,
                }
                spec['clusters'].append(entry)

        return spec
