# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.ta1394.general import AvcGeneral
from hinawa_utils.ta1394.general import AvcConnection
from hinawa_utils.ta1394.ccm import AvcCcm

from hinawa_utils.bebob.bebob_unit import BebobUnit
from hinawa_utils.bebob.extensions import BcoPlugInfo
from hinawa_utils.bebob.extensions import BcoSubunitInfo
from hinawa_utils.bebob.extensions import BcoStreamFormatInfo

__all__ = ['PlugParser']


class PlugParser():
    @classmethod
    def parse_unit_info(cls, fcp):
        return AvcGeneral.get_unit_info(fcp)

    @classmethod
    def parse_unit_plugs(cls, fcp):
        unit_plugs = {}
        info = AvcConnection.get_unit_plug_info(fcp)
        for type, params in info.items():
            if type not in unit_plugs:
                unit_plugs[type] = {}
                unit_plugs[type]['output'] = {}
                unit_plugs[type]['input'] = {}
            for dir, num in params.items():
                for i in range(num + 1):
                    try:
                        plug = cls.parse_unit_plug(fcp, dir, type, i)
                        unit_plugs[type][dir][i] = plug
                    except Exception:
                        continue
        return unit_plugs

    @classmethod
    def parse_unit_plug(cls, fcp, dir, type, num):
        plug = {}
        addr = BcoPlugInfo.get_unit_addr(dir, type, num)
        plug['type'] = BcoPlugInfo.get_plug_type(fcp, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(fcp, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(fcp, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(fcp, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] == 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(fcp, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(
                    fcp, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = []
        plug['outputs'] = []
        if dir == 'output':
            plug['input'] = BcoPlugInfo.get_plug_input(fcp, addr)
        else:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(fcp, addr)
        return plug

    @classmethod
    def parse_subunit_plugs(cls, fcp):
        subunit_plugs = {}
        for page in range(AvcGeneral.MAXIMUM_SUBUNIT_PAGE + 1):
            try:
                subunits = AvcGeneral.get_subunit_info(fcp, page)
            except Exception:
                break

            for entry in subunits:
                type = entry['type']
                maximum_id = entry['maximum-id']
                if type not in subunit_plugs:
                    subunit_plugs[type] = {}
                for id in range(maximum_id + 1):
                    if id not in subunit_plugs[type]:
                        subunit_plugs[type][id] = {}
                        subunit_plugs[type][id]['output'] = {}
                        subunit_plugs[type][id]['input'] = {}

                info = AvcConnection.get_subunit_plug_info(fcp, type, 0)
                for dir, num in info.items():
                    for i in range(num):
                        plug = cls.parse_subunit_plug(fcp, dir, type, 0, i)
                        subunit_plugs[type][id][dir][i] = plug
        return subunit_plugs

    @classmethod
    def parse_subunit_plug(cls, fcp, dir, type, id, num):
        plug = {}
        addr = BcoPlugInfo.get_subunit_addr(dir, type, id, num)
        plug['type'] = BcoPlugInfo.get_plug_type(fcp, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(fcp, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(fcp, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(fcp, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] == 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(fcp, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(
                    fcp, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = {}
        plug['outputs'] = []
        # Music subunits have counter direction.
        try:
            plug['input'] = BcoPlugInfo.get_plug_input(fcp, addr)
        except Exception:
            pass
        try:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(fcp, addr)
        except Exception:
            pass
        return plug

    @classmethod
    def parse_function_block_plugs(cls, fcp, subunit_plugs):
        subunits = {}
        for subunit_type, subunit_type_plugs in subunit_plugs.items():
            if subunit_type not in subunits:
                subunits[subunit_type] = {}

            for subunit_id in subunit_type_plugs.keys():
                fbs = {}

                entries = []
                for page in range(0xff):
                    elems = BcoSubunitInfo.get_subunit_fb_info(fcp,
                                                               subunit_type, subunit_id, page, 0xff)
                    if len(elems) == 0:
                        break
                    entries.extend(elems)

                for entry in entries:
                    fb_type = entry['type']
                    if fb_type not in fbs:
                        fbs[fb_type] = {}
                    fb_id = entry['id']

                    fb = {}
                    fb['purpose'] = entry['purpose']
                    fb['outputs'] = {}
                    fb['inputs'] = {}
                    for i in range(entry['inputs']):
                        plug = cls.parse_fb_plug(fcp, 'input', subunit_type, subunit_id, fb_type, fb_id, i)
                        fb['inputs'][i] = plug
                    for i in range(entry['outputs']):
                        plug = cls.parse_fb_plug(fcp, 'output', subunit_type, subunit_id, fb_type, fb_id, i)
                        fb['outputs'][i] = plug

                    fbs[fb_type][fb_id] = fb

                subunits[subunit_type][subunit_id] = fbs

        return subunits

    @classmethod
    def parse_fb_plug(cls, fcp, dir, subunit_type, subunit_id, fb_type, fb_id, num):
        plug = {}
        addr = BcoPlugInfo.get_function_block_addr(dir, subunit_type,
                                                   subunit_id, fb_type, fb_id, num)
        plug['type'] = BcoPlugInfo.get_plug_type(fcp, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(fcp, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(fcp, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(fcp, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] == 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(fcp, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(
                    fcp, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = {}
        plug['outputs'] = []
        # Music subunits have counter direction.
        try:
            plug['input'] = BcoPlugInfo.get_plug_input(fcp, addr)
        except Exception:
            pass
        try:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(fcp, addr)
        except Exception:
            pass
        return plug

    @classmethod
    def parse_signal_destination(cls, fcp, subunit_plugs):
        dst = []
        for subunit_id, subunit_id_plugs in subunit_plugs['music'].items():
            for i, plug in subunit_id_plugs['input'].items():
                if plug['type'] == 'Sync':
                    dst = AvcCcm.get_subunit_signal_addr('music', 0, i)
        return dst

    @classmethod
    def parse_signal_sources(cls, fcp, unit_plugs, subunit_plugs, signal_destination):
        srcs = []
        candidates = []
        # This is internal clock source.
        for subunit_id, subunit_id_plugs in subunit_plugs['music'].items():
            for i, plug in subunit_id_plugs['output'].items():
                if plug['type'] == 'Sync':
                    addr = AvcCcm.get_subunit_signal_addr('music', 0, i)
                    candidates.append((addr, plug))
        # External source is available.
        for i, plug in unit_plugs['external']['input'].items():
            if plug['type'] in ('Sync', 'Digital', 'Clock'):
                addr = AvcCcm.get_unit_signal_addr('external', i)
                candidates.append((addr, plug))
        # SYT-match is available, but not practical.
        for i, plug in unit_plugs['isoc']['input'].items():
            if plug['type'] == 'Sync':
                addr = AvcCcm.get_unit_signal_addr('isoc', i)
                candidates.append((addr, plug))
        # BeBoBv3 has.
        # Inquire these are able to connect to destination.
        for params in candidates:
            addr = params[0]
            plug = params[1]
            try:
                AvcCcm.ask_signal_source(fcp, addr, signal_destination)
            except Exception:
                continue
            srcs.append(params)
        return srcs

    @classmethod
    def parse_stream_formats(cls, fcp, unit_plugs):
        hoge = {}
        for type, dir_plugs in unit_plugs.items():
            if type == 'async':
                continue
            hoge[type] = {}
            for dir, plugs in dir_plugs.items():
                hoge[type][dir] = {}
                for i, plug in plugs.items():
                    addr = BcoPlugInfo.get_unit_addr(dir, type, i)
                    try:
                        fmts = BcoStreamFormatInfo.get_entry_list(fcp,
                                                                  addr)
                        hoge[type][dir][i] = fmts
                    except Exception:
                        continue
        return hoge

    @classmethod
    def get_unit_plug_list(cls, fcp):
        plugs = {}
        seqid = 0

        units = AvcConnection.get_unit_plug_info(fcp)
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

    @classmethod
    def get_subunit_plug_info(cls, fcp):
        subunits = {}
        for page in range(AvcGeneral.MAXIMUM_SUBUNIT_PAGE + 1):
            try:
                info = AvcGeneral.get_subunit_info(fcp, page)
            except Exception:
                break

            for entry in info:
                subunit_type = entry['type']
                maximum_id = entry['maximum-id']

                for subunit_id in range(maximum_id + 1):
                    try:
                        data = AvcConnection.get_subunit_plug_info(fcp,
                                                    subunit_type, subunit_id)
                    except Exception:
                        continue

                    id = (subunit_type, subunit_id)
                    if id not in subunits:
                        subunits[id] = {}
                    for direction, count in data.items():
                        subunits[id][direction] = count

        return subunits

    @classmethod
    def get_subunit_plug_list(cls, fcp):
        plugs = {}
        seqid = 0

        subunits = cls.get_subunit_plug_info(fcp)
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

    @classmethod
    def get_avail_connections(cls, fcp, unit_plug_list, subunit_plug_list):
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
                curr_src_info = AvcCcm.get_signal_source(fcp, dst_addr)
            except Exception:
                curr_src_info = None

            for src_seqid, src_addr in src_candidates.items():
                try:
                    AvcCcm.ask_signal_source(fcp, src_addr, dst_addr)
                except Exception:
                    continue

                if dst_seqid not in avail:
                    avail[dst_seqid] = []

                src_info = AvcCcm.parse_signal_addr(src_addr)
                avail[dst_seqid].append((src_seqid, src_info == curr_src_info))

        return avail

    @classmethod
    def get_plug_spec(cls, fcp, info):
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
            'name': BcoPlugInfo.get_plug_name(fcp, addr),
            'type': BcoPlugInfo.get_plug_type(fcp, addr),
        }

        if info['dir'] == 'input':
            spec['input'] = BcoPlugInfo.get_plug_input(fcp, addr),
        else:
            spec['outputs'] = BcoPlugInfo.get_plug_outputs(fcp, addr),

        return spec

        if info['mode'] == 'unit':
            spec['clusters'] = []
            clusters = BcoPlugInfo.get_plug_clusters(fcp, addr)

            for i, cluster in enumerate(clusters):
                mapping = []
                name = BcoPlugInfo.get_plug_cluster_info(fcp, addr, i + 1)
                for info in cluster:
                    idx, pos = info
                    ch_name = BcoPlugInfo.get_plug_ch_name(fcp, addr, idx)
                    mapping.append(ch_name)
                entry = {
                    'name': name,
                    'channels': mapping,
                }
                spec['clusters'].append(entry)

        return spec
