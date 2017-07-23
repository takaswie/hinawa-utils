from ta1394.general import AvcGeneral
from ta1394.general import AvcConnection
from ta1394.ccm import AvcCcm

from bebob.bebob_unit import BebobUnit
from bebob.extensions import BcoPlugInfo
from bebob.extensions import BcoSubunitInfo
from bebob.extensions import BcoStreamFormatInfo

__all__ = ['PlugParser']

class PlugParser(BebobUnit):
    def __init__(self, path):
        super().__init__(path)

        self.unit_info = self._parse_unit_info()
        self.unit_plugs = self._parse_unit_plugs()

        self.subunit_plugs = self._parse_subunit_plugs()

        self.function_block_plugs = self._parse_function_block_plugs()

        self.stream_formats = self._parse_stream_formats()

        self.signal_destination = self._parse_signal_destination()
        self.signal_sources = self._parse_signal_sources()

    def _parse_unit_info(self):
        return AvcGeneral.get_unit_info(self.fcp) 

    def _parse_unit_plugs(self):
        unit_plugs = {}
        info = AvcConnection.get_unit_plug_info(self.fcp)
        for type, params in info.items():
            if type not in unit_plugs:
                unit_plugs[type] = {}
                unit_plugs[type]['output'] = {}
                unit_plugs[type]['input'] = {}
            for dir, num in params.items():
                for i in range(num + 1):
                    try:
                        plug = self._parse_unit_plug(dir, type, i)
                        unit_plugs[type][dir][i] = plug
                    except:
                        continue
        return unit_plugs

    def _parse_unit_plug(self, dir, type, num):
        plug = {}
        addr = BcoPlugInfo.get_unit_addr(dir, type, num)
        plug['type'] = BcoPlugInfo.get_plug_type(self.fcp, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(self.fcp, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(self.fcp, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(self.fcp, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] is 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(self.fcp, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(self.fcp, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = []
        plug['outputs'] = []
        if dir == 'output':
            plug['input'] = BcoPlugInfo.get_plug_input(self.fcp, addr)
        else:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(self.fcp, addr)
        return plug

    def _parse_subunit_plugs(self):
        subunit_plugs = {}
        subunits = BcoSubunitInfo.get_subunits(self.fcp)
        for subunit in subunits:
            type = subunit['type']
            id = subunit['id']
            if type not in subunit_plugs:
                subunit_plugs[type] = {}
            if id not in subunit_plugs[type]:
                subunit_plugs[type][id] = {}
                subunit_plugs[type][id]['output'] = {}
                subunit_plugs[type][id]['input'] = {}

            info = AvcConnection.get_subunit_plug_info(self.fcp, type, 0)
            for dir, num in info.items():
                for i in range(num):
                    plug = self._parse_subunit_plug(dir, type, 0, i)
                    subunit_plugs[type][id][dir][i] = plug
        return subunit_plugs

    def _parse_subunit_plug(self, dir, type, id, num):
        plug = {}
        addr = BcoPlugInfo.get_subunit_addr(dir, type, id, num)
        plug['type'] = BcoPlugInfo.get_plug_type(self.fcp, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(self.fcp, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(self.fcp, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(self.fcp, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] == 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(self.fcp, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(self.fcp, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = {}
        plug['outputs'] = []
        # Music subunits have counter direction.
        try:
            plug['input'] = BcoPlugInfo.get_plug_input(self.fcp, addr)
        except:
            pass
        try:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(self.fcp, addr)
        except:
            pass
        return plug

    def _parse_function_block_plugs(self):
        subunits = {}
        for subunit_type, subunit_type_plugs in self.subunit_plugs.items():
            if subunit_type not in subunits:
                subunits[subunit_type] = {}

            for subunit_id in subunit_type_plugs.keys():
                fbs = {}

                entries = []
                for i in range(0xff):
                    try:
                        entries.extend(BcoSubunitInfo.get_subunit_fb_info(
                                self.fcp, subunit_type, subunit_id, i, 0xff))
                    except:
                        break

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
                        plug = self._parse_fb_plug('input', subunit_type,
                                                subunit_id, fb_type, fb_id, i)
                        fb['inputs'][i] = plug
                    for i in range(entry['outputs']):
                        plug = self._parse_fb_plug('output', subunit_type,
                                                subunit_id, fb_type, fb_id, i)
                        fb['outputs'][i] = plug

                    fbs[fb_type][fb_id] = fb

                subunits[subunit_type][subunit_id] = fbs

        return subunits

    def _parse_fb_plug(self, dir, subunit_type, subunit_id, fb_type, fb_id,
                       num):
        plug = {}
        addr = BcoPlugInfo.get_function_block_addr(dir, subunit_type,
                                            subunit_id, fb_type, fb_id, num)
        plug['type'] = BcoPlugInfo.get_plug_type(self.fcp, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(self.fcp, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(self.fcp, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(self.fcp, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] is 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(self.fcp, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(self.fcp, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = {}
        plug['outputs'] = []
        # Music subunits have counter direction.
        try:
            plug['input'] = BcoPlugInfo.get_plug_input(self.fcp, addr)
        except:
            pass
        try:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(self.fcp, addr)
        except:
            pass
        return plug

    def _parse_signal_destination(self):
        dst = []
        for subunit_id, subunit_id_plugs in self.subunit_plugs['music'].items():
            for i, plug in subunit_id_plugs['input'].items():
                if plug['type'] == 'Sync':
                    dst = AvcCcm.get_subunit_signal_addr('music', 0, i)
        return dst

    def _parse_signal_sources(self):
        srcs = []
        candidates = []
        # This is internal clock source.
        for subunit_id, subunit_id_plugs in self.subunit_plugs['music'].items():
            for i, plug in subunit_id_plugs['output'].items():
                if plug['type'] == 'Sync':
                    addr = AvcCcm.get_subunit_signal_addr('music', 0, i)
                    candidates.append((addr, plug))
        # External source is available.
        for i, plug in self.unit_plugs['external']['input'].items():
            if plug['type'] in ('Sync', 'Digital', 'Clock'):
                addr = AvcCcm.get_unit_signal_addr('external', i)
                candidates.append((addr, plug))
        # SYT-match is available, but not practical.
        for i, plug in self.unit_plugs['isoc']['input'].items():
            if plug['type'] == 'Sync':
                addr = AvcCcm.get_unit_signal_addr('isoc', i)
                candidates.append((addr, plug))
        # BeBoBv3 has.
        # Inquire these are able to connect to destination.
        for params in candidates:
            addr = params[0]
            plug = params[1]
            try:
                AvcCcm.ask_signal_source(self.fcp, addr,
                                         self.signal_destination)
            except:
                continue
            srcs.append(params)
        return srcs

    def _parse_stream_formats(self):
        hoge = {}
        for type, dir_plugs in self.unit_plugs.items():
            if type == 'async':
                continue
            hoge[type] = {}
            for dir, plugs in dir_plugs.items():
                hoge[type][dir] = {}
                for i, plug in plugs.items():
                    addr = BcoPlugInfo.get_unit_addr(dir, type, i)
                    try:
                        fmts = BcoStreamFormatInfo.get_entry_list(self.fcp,
                                                                  addr)
                        hoge[type][dir][i] = fmts
                    except:
                        continue
        return hoge
