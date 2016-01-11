from gi.repository import Hinawa

from ta1394.general import AvcGeneral
from ta1394.general import AvcConnection
from ta1394.streamformat import AvcStreamFormat
from ta1394.audio import AvcAudio
from ta1394.ccm import AvcCcm

from bridgeco.extensions import BcoPlugInfo
from bridgeco.extensions import BcoSubunitInfo
from bridgeco.extensions import BcoVendorDependent

class BebobNormal(Hinawa.SndUnit):
    unit_info = {}
    unit_plugs = {}
    subunit_plugs = {}

    def __init__(self, card):
        super().__init__()
        self.open('/dev/snd/hwC{0}D0'.format(card))
        self.listen()

        self.unit_info = self._parse_unit_info()
        self.unit_plugs = self._parse_unit_plugs()
        self.subunit_plugs = self._parse_subunit_plugs()
        self.function_block_plugs = self._parse_function_block_plugs()

        self.signal_destination = self._parse_signal_destination()
        self.signal_sources = self._parse_signal_sources()

        self._parse_processing_fbs()

    def _parse_unit_info(self):
        return AvcGeneral.get_unit_info(self) 

    def _parse_unit_plugs(self):
        unit_plugs = {}
        info = AvcConnection.get_unit_plug_info(self)
        for type, params in info.items():
            if type not in unit_plugs:
                unit_plugs[type] = {}
            for dir, num in params.items():
                if dir not in unit_plugs[type]:
                    unit_plugs[type][dir] = []
                for i in range(num):
                    plug = self._parse_unit_plug(dir, type, i)
                    unit_plugs[type][dir].append(plug)
        return unit_plugs

    def _parse_unit_plug(self, dir, type, num):
        plug = {}
        addr = BcoPlugInfo.get_unit_addr(dir, type, num)
        plug['type'] = BcoPlugInfo.get_plug_type(self, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(self, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(self, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(self, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] is 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(self, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(self, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = []
        plug['outputs'] = []
        if dir == 'output':
            plug['input'] = BcoPlugInfo.get_plug_input(self, addr)
        else:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(self, addr)
        return plug

    def _parse_subunit_plugs(self):
        subunit_plugs = {}
        subunits = BcoSubunitInfo.get_subunits(self)
        for subunit in subunits:
            type = subunit['type']
            id = subunit['id']
            if type not in subunit_plugs:
                subunit_plugs[type] = []
            if id >= len(subunit_plugs[type]):
                subunit_plugs[type].append({})
            info = AvcConnection.get_subunit_plug_info(self, type, id)
            for dir, num in info.items():
                if dir not in subunit_plugs[type][id]:
                    subunit_plugs[type][id][dir] = []
                for i in range(num):
                    plug = self._parse_subunit_plug(dir, type, id, i)
                    subunit_plugs[type][id][dir].append(plug)
        return subunit_plugs

    def _parse_subunit_plug(self, dir, type, id, num):
        plug = {}
        addr = BcoPlugInfo.get_subunit_addr(dir, type, id, num)
        plug['type'] = BcoPlugInfo.get_plug_type(self, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(self, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(self, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(self, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] is 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(self, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(self, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = {}
        plug['outputs'] = []
        # Music subunits have counter direction.
        try:
            plug['input'] = BcoPlugInfo.get_plug_input(self, addr)
        except:
            pass
        try:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(self, addr)
        except:
            pass
        return plug

    def _parse_function_block_plugs(self):
        fbs = {}
        subunits = BcoSubunitInfo.get_subunits(self)
        for subunit in subunits:
            type = subunit['type']
            id = subunit['id']
            if type not in fbs:
                fbs[type] = []
            if id >= len(fbs[type]):
                fbs[type].append({})
            entries = []
            for i in range(0xff):
                try:
                    entries.extend(BcoSubunitInfo.get_subunit_fb_info(self, type, id, i, 0xff))
                except:
                    break
            fb_counts = {}
            for entry in entries:
                if entry['fb-type'] not in fb_counts:
                    fb_counts[entry['fb-type']] = 0
                fb_counts[entry['fb-type']] += 1
            for entry in entries:
                fb_type = entry['fb-type']
                if fb_type is not fbs[type][id]:
                    fbs[type][id][fb_type] = [{} for i in range(fb_counts[fb_type])]
                fb_id = entry['fb-id'] - 1
                for j in range(entry['inputs']):
                    if 'input' not in fbs[type][id][fb_type][fb_id]:
                        fbs[type][id][fb_type][fb_id]['input'] = []
                    plug = self._parse_fb_plug('input', type, id,
                                        entry['fb-type'], entry['fb-id'], j)
                    fbs[type][id][fb_type][fb_id]['input'].append(plug)
                for j in range(entry['outputs']):
                    if 'output' not in fbs[type][id][fb_type]:
                        fbs[type][id][fb_type][fb_id]['output'] = []
                    plug = self._parse_fb_plug('output', type, id,
                                        entry['fb-type'], entry['fb-id'], j)
                    fbs[type][id][fb_type][fb_id]['output'].append(plug)
        return fbs

    def _parse_fb_plug(self, dir, subunit_type, subunit_id, fb_type, fb_id,
                       num):
        plug = {}
        addr = BcoPlugInfo.get_function_block_addr(dir, subunit_type,
                                            subunit_id, fb_type, fb_id, num)
        plug['type'] = BcoPlugInfo.get_plug_type(self, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(self, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(self, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(self, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] is 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(self, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(self, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = {}
        plug['outputs'] = []
        # Music subunits have counter direction.
        try:
            plug['input'] = BcoPlugInfo.get_plug_input(self, addr)
        except:
            pass
        try:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(self, addr)
        except:
            pass
        return plug

    def _parse_signal_destination(self):
        dst = []
        for id, id_plugs in enumerate(self.subunit_plugs['music']):
            for i, plug in enumerate(id_plugs['input']):
                if plug['type'] == 'Sync':
                    dst = AvcCcm.get_subunit_signal_addr('music', id, i)
        return dst

    def _parse_signal_sources(self):
        srcs = {}
        candidates = {}
        # This is internal clock source.
        for id, id_plugs in enumerate(self.subunit_plugs['music']):
            for i, plug in enumerate(id_plugs['output']):
                if plug['type'] == 'Sync':
                    addr = AvcCcm.get_subunit_signal_addr('music', id, i)
                    candidates[plug['name']] = addr
        # External source is available.
        for i, plug in enumerate(self.unit_plugs['external']['input']):
            if plug['type'] == 'Sync' or plug['type'] == 'Digital':
                addr = AvcCcm.get_unit_signal_addr('external', i)
                candidates[plug['name']] = addr
        # SYT-match is available, but not practical.
        for i, plug in enumerate(self.unit_plugs['isoc']['input']):
            if plug['type'] == 'Sync':
                addr = AvcCcm.get_unit_signal_addr('isoc', i)
                candidates[plug['name']] = addr
        # Inquire these are able to connect to destination.
        for key, src in candidates.items():
            try:
                AvcCcm.ask_signal_source(self, src, self.signal_destination)
            except:
                continue
            srcs[key] = src
        return srcs

    def set_clock_source(self, name):
        if name not in self.signal_sources:
            raise ValueError('Invalid argument for signal source label')
        src = self.signal_sources[name]
        dst = self.signal_destination
        AvcCcm.set_signal_source(self, src, dst)

    def get_clock_source(self):
        status = {}
        current = AvcCcm.get_signal_source(self, self.signal_destination)
        for key, addr in self.signal_sources.items():
            if AvcCcm.parse_signal_addr(addr) == current:
                status[key] = True
            else:
                status[key] = False
        return status

    def _parse_processing_fbs(self):
        for type, type_plugs in self.function_block_plugs.items():
            for id, id_plugs in enumerate(type_plugs):
                for fb_type, fb_type_plugs in id_plugs.items():
                    for index, fb_plugs in enumerate(fb_type_plugs):
                        for dir, dir_plugs in fb_plugs.items():
                            for i, plugs in enumerate(dir_plugs):
                                print(type, id, fb_type, index, dir, i)
