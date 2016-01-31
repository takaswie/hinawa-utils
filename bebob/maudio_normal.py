#!/usr/bin/env python3

from bebob.bebob_unit import BebobUnit

from ta1394.general import AvcGeneral
from ta1394.general import AvcConnection
from ta1394.ccm import AvcCcm
from ta1394.audio import AvcAudio

import re
from math import log10

class MaudioNormal(BebobUnit):
    _ids = {
        0x00000a: (0, "Ozonic"),
        0x010062: (1, "Firewire Solo"),
        0x010060: (2, "Firewire Audiophile"),
        0x010046: (3, "Firewire 410"),
        # Need information.
        #   NRV10
        #   ProFire Lightbridge
    }

    _labels = (
        {'inputs':  ('analog-1/2', 'analog-3/4', 'stream-1/2', 'stream-3/4'),
         'outputs': ('analog-1/2', 'analog-3/4'),
         'mixers':  ('mixer-1/2', 'mixer-3/4'),
         'meters':  ('analog-in-1', 'analog-in-2',
                     'analog-in-3', 'analog-in-4',
                     'stream-in-1', 'stream-in-2',
                     'stream-in-3', 'stream-in-4',
                     'analog-out-1', 'analog-out-2',
                     'analog-out-3', 'analog-out-4')},
        {'inputs':  ('analog-1/2', 'digital-1/2', 'stream-1/2', 'stream-3/4'),
         'outputs': ('analog-1/2', 'digital-1/2'),
         'mixers':  ('mixer-1/2', 'mixer-3/4'),
         'meters':  ('analog-in-1', 'analog-in-2',
                     'digital-in-1', 'digital-in-2',
                     'stream-in-1', 'stream-in-2',
                     'stream-in-3', 'stream-in-4',
                     'analog-out-1', 'analog-out-2',
                     'digital-out-1', 'digital-out-2')},
        {'inputs':  ('analog-1/2', 'digital-1/2',
                     'stream-1/2', 'stream-3/4', 'stream-5/6'),
         'outputs': ('analog-1/2', 'analog-3/4', 'digital-1/2'),
         'mixers':  ('mixer-1/2', 'mixer-3/4', 'mixer-5/6'),
         'meters':  ('analog-in-1', 'analog-in-2',
                     'digital-in-1', 'digital-in-2',
                     'analog-out-1', 'analog-out-2',
                     'analog-out-3', 'analog-out-4',
                     'digital-out-1', 'digital-out-2',
                     'headphone-out-1', 'headphone-out-2',
                     'aux-out-1', 'aux-out-2')},
        {'inputs':  ('analog-1/2', 'digital-1/2',
                     'stream-1/2', 'stream-3/4', 'stream-5/6', 'stream-7/8',
                     'stream-9/10'),
         'outputs': ('analog-1/2', 'analog-3/4', 'analog-5/6', 'analog-7/8',
                     'digital-1/2'),
         'mixers':  ('mixer-1/2', 'mixer-3/4', 'mixer-5/6', 'mixer-7/8',
                     'mixer-9/10'),
         'meters':  ('analog-in-1', 'analog-in-2',
                     'digital-in-1', 'digital-in-2',
                     'analog-out-1', 'analog-out-2',
                     'analog-out-3', 'analog-out-4',
                     'analog-out-5', 'analog-out-6',
                     'analog-out-7', 'analog-out-8',
                     'digital-out-1', 'digital-out-2',
                     'headphone-out-1', 'headphone-out-2',
                     'headphone-out-3', 'headphone-out-4')},
    )

    # = _labels['inputs']
    _inputs = (
        (( 3, (1, 2)), ( 4, (1, 2)), ( 1, (1, 2)), ( 2, (1, 2))),
        (( 1, (1, 2)), ( 2, (1, 2)), ( 4, (1, 2)), ( 3, (1, 2))),
        (( 4, (1, 2)), ( 5, (1, 2)), ( 1, (1, 2)), ( 2, (1, 2)), ( 3, (1, 2))),
        (( 3, (1, 2)), ( 4, (1, 2)),
         ( 2, (1, 2)), ( 1, (1, 2)), ( 1, (3, 4)), ( 1, (5, 6)), ( 1, (7, 8))),
    )

    # = _labels['inputs']
    _aux_inputs = (
        (),
        (),
        (( 9, (1, 2)), (10, (1, 2)), ( 6, (1, 2)), ( 7, (1, 2)), ( 8, (1, 2))),
        (( 7, (1, 2)), ( 8, (1, 2)), ( 9, (1, 2)), ( 6, (1, 2)),
         ( 5, (1, 2)), ( 5, (3, 4)), ( 5, (5, 6)), ( 5, (7, 8))),
    )

    _aux_output = (
        None,
        None,
        11,
         9,
    )

    # = _labels['inputs']
    _mixer_sources = (
        (( 2, (1, 2)), ( 3, (1, 2)), ( 0, (1, 2)), ( 1, (1, 2))),
        (( 0, (1, 2)), ( 1, (1, 2)), ( 3, (1, 2)), ( 2, (1, 2))),
        (( 3, (1, 2)), ( 4, (1, 2)), ( 0, (1, 2)), ( 1, (1, 2)), ( 2, (1, 2))),
        (( 2, (1, 2)), ( 3, (1, 2)),
         ( 1, (1, 2)), ( 0, (1, 2)), ( 0, (3, 4)), ( 0, (5, 6)),
         ( 0, (7, 8))),
    )

    # = _labels['outputs']
    _mixer_sinks = (
        (( 1, (1, 2)), ( 1, (1, 2))),
        (( 1, (1, 2)), ( 1, (3, 4))),
        (( 1, (1, 2)), ( 2, (1, 2)), ( 3, (1, 2)), ( 4, (1, 2))),
        (( 1, (1, 2)), ( 1, (3, 4)), ( 1, (5, 6)), ( 1, (7, 8)), ( 1, (9, 10))),
    )

    # = _labels['outputs']
    _output_sources = (
        (),
        (),
        ( 1, 2, 3),
        ( 2, 3, 4, 5, 6),
    )

    # = _labels['outputs']
    _outputs = (
        (( 5, (1, 2)), ( 6, (1, 2))),
        (( 2, (1, 2)), ( 3, (1, 2))),
        ((12, (1, 2)), (13, (1, 2)), (14, (1, 2))),
        ((10, (1, 2)), (11, (1, 2)), (12, (1, 2)), (13, (1, 2)), (14, (1, 2))),
    )

    _hp_sources = (
        (),
        (),
        (( 4, (0, 1, 2, 3)), ),
        (( 7, (2, 3, 4, 5, 6, 7)), ),
    )

    _hp_outs = (
        (),
        (),
        ((16, (1, 2)), ),
        ((15, (1, 2)), ),
    )

    _meters = (
        48 // 4,
        52 // 4,
        60 // 4,
        76 // 4,
    )

    _clocks = (
        {},
        {'Internal':    AvcCcm.get_subunit_signal_addr('music', 0, 1),
         'S/PDIF':      AvcCcm.get_unit_signal_addr('external', 1)},
        {'Internal':    AvcCcm.get_subunit_signal_addr('music', 0, 1),
         'S/PDIF':      AvcCcm.get_unit_signal_addr('external', 2)},
        {'Internal':    AvcCcm.get_subunit_signal_addr('music', 0, 1),
         'S/PDIF':      AvcCcm.get_unit_signal_addr('external', 2),
         'ADAT':        AvcCcm.get_unit_signal_addr('external', 3)},
    )

    def get_clock_source_labels(self):
        return self._clocks[self._id].keys()
    def set_clock_source(self, src):
        dst = AvcCcm.get_subunit_signal_addr('music', 0, 1)
        addr = self._clocks[self._id][src]
        AvcCcm.set_signal_source(self.fcp, addr, dst)
    def get_clock_source(self):
        dst = AvcCcm.get_subunit_signal_addr('music', 0, 1)
        curr = AvcCcm.get_signal_source(self.fcp, dst)
        for name, addr in self._clocks[self._id].items():
            if AvcCcm.compare_addrs(curr, AvcCcm.parse_signal_addr(addr)):
                return name

    def __init__(self, path):
        super().__init__(path)
        model_id = -1
        for quad in self.get_config_rom():
            if quad >> 24 == 0x17:
                model_id = quad & 0x00ffffff
                self._id = self._ids[model_id][0]
                info = AvcGeneral.get_unit_info(self.fcp)
                self._company_ids = info['company-id']
        if model_id < 0:
            raise OSError('Not supported')

    def _refer_fb_data(self, targets, index, ch):
        if index >= len(targets):
            raise ValueError('Invalid argument for function block index')
        if ch >= len(targets[index][1]):
            raise ValueError('Invalid argument for channel number')
        fb = targets[index][0]
        ch = targets[index][1][ch]
        return (fb, ch)

    def _set_volume(self, targets, index, ch, value):
        fb, ch = self._refer_fb_data(targets, index, ch)
        AvcAudio.set_feature_volume_state(self.fcp, 0, 'current', fb, ch, value)
    def _get_volume(self, targets, index, ch):
        fb, ch = self._refer_fb_data(targets, index, ch)
        return AvcAudio.get_feature_volume_state(self.fcp, 0, 'current', fb, ch)


    def get_input_labels(self):
        return self._labels[self._id]['inputs']

    def _refer_input_data(self, target):
        if target not in self._labels[self._id]['inputs']:
            raise ValueError('Invalid argument for input')
        return self._labels[self._id]['inputs'].index(target)

    def set_input_volume(self, target, ch, value):
        index = self._refer_input_data(target)
        self._set_volume(self._inputs[self._id], index, ch, value)
    def get_input_volume(self, target, ch):
        index = self._refer_input_data(target)
        return self._get_volume(self._inputs[self._id], index, ch)


    def get_aux_input_labels(self):
        if not self._aux_output[self._id]:
            return ()
        return self._labels[self._id]['inputs']

    def set_aux_input_volume(self, target, ch, value):
        index = self._refer_input_data(target)
        self._set_volume(self._aux_inputs[self._id], index, ch, value)
    def get_aux_input_volume(self, target, ch):
        index = self._refer_input_data(target)
        return self._get_volume(self._aux_inputs[self._id], index, ch)


    def set_aux_master_volume(self, ch, value):
        if ch > 2:
            raise ValueError('Invalid argument for master channel')
        fb = self._aux_output[self._id]
        AvcAudio.set_feature_volume_state(self.fcp, 0, 'current', fb, ch, value)

    def get_aux_master_volume(self, ch):
        if ch > 2:
            raise ValueError('Invalid argument for master channel')
        fb = self._aux_output[self._id]
        return AvcAudio.get_feature_volume_state(self.fcp, 0, 'current', fb, ch)


    def get_mixer_source_labels(self):
        return self._labels[self._id]['inputs']
    def get_mixer_sink_labels(self):
        return self._labels[self._id]['mixers']

    def _refer_mixer_data(self, source, sink):
        if source not in self._labels[self._id]['inputs']:
            raise ValueError('Invalid argument for mixer input')
        if sink not in self._labels[self._id]['mixers']:
            raise ValueError('Invalid argument for mixer output')
        input = self._labels[self._id]['inputs'].index(source)
        in_fb = self._mixer_sources[self._id][input][0]
        in_ch = self._mixer_sources[self._id][input][1][0]   # Use left channel.
        output = self._labels[self._id]['mixers'].index(sink)
        out_fb = self._mixer_sinks[self._id][output][0]
        out_ch = self._mixer_sinks[self._id][output][1][0]  # Use left channel.
        return (in_fb, in_ch, out_fb, out_ch)

    def set_mixer_routing(self, source, sink, value):
        in_fb, in_ch, out_fb, out_ch = self._refer_mixer_data(source, sink)
        AvcAudio.set_processing_mixer_state(self.fcp, 0, 'current',
                                            out_fb, in_fb, in_ch, out_ch, value)
    def get_mixer_routing(self, source, sink):
        in_fb, in_ch, out_fb, out_ch = self._refer_mixer_data(source, sink)
        return AvcAudio.get_processing_mixer_state(self.fcp, 0, 'current',
                                            out_fb, in_fb, in_ch, out_ch)

    def get_output_labels(self):
        return self._labels[self._id]['outputs']

    def _refer_out_data(self, target):
        if target not in self._labels[self._id]['outputs']:
            raise ValueError('Invalid argument for output')
        return self._labels[self._id]['outputs'].index(target)

    def set_output_volume(self, target, ch, value):
        index = self._refer_out_data(target)
        self._set_volume(self._outputs[self._id], index, ch, value)
    def get_output_volume(self, target, ch):
        index = self._refer_out_data(target)
        return self._get_volume(self._outputs[self._id], index, ch)


    def get_output_source_labels(self, target):
        index = self._refer_out_data(target)
        labels = []
        labels.append(self._labels[self._id]['mixers'][index])
        if self._aux_output[self._id]:
            labels.append("aux-1/2")
        return labels

    def set_output_source(self, target, source):
        index = self._refer_out_data(target)
        if source in self._labels[self._id]['mixers'][index]:
            value = 0
        elif source.find('aux') == 0:
            value = 1
        else:
            raise ValueError('Invalid argument for output target')
        fb = self._output_sources[self._id][index]
        AvcAudio.set_selector_state(self.fcp, 0, 'current', fb, value)

    def get_output_source(self, target):
        index = self._refer_out_data(target)
        fb = self._output_sources[self._id][index]
        value = AvcAudio.get_selector_state(self.fcp, 0, 'current', fb)
        if value == 1 and self._aux_output[self._id]:
            return 'aux-1/2'
        return self._labels[self._id]['mixers'][index]


    def get_headphone_labels(self):
        labels = []
        for i in range(len(self._hp_outs[self._id])):
            labels.append('headphone-{0}/{1}'.format(i * 2 + 1, i * 2 + 2))
        return labels

    _hp_expr = re.compile('^headphone-([0-9]*)/([0-9]*)$')

    def _refer_hp_data(self, target):
        matches = self._hp_expr.match(target)
        if not matches:
            raise ValueError('Invalid argument for headphone')
        left = int(matches.group(1)) // 2
        right = int(matches.group(2)) // 2
        if right != left + 1:
            raise ValueError('Invalid argument for headphone')
        return left

    def set_headphone_volume(self, target, ch, value):
        index = self._refer_hp_data(target)
        self._set_volume(self._hp_outs[self._id], index, ch, value)
    def get_headphone_volume(self, target, ch):
        index = self._refer_hp_data(target)
        return self._get_volume(self._hp_outs[self._id], index, ch)


    def get_headphone_source_labels(self):
        labels = []
        if len(self._hp_sources[self._id]) > 0:
            for mixer in self._labels[self._id]['mixers']:
                labels.append(mixer)
            if self._aux_output[self._id]:
                labels.append("aux-1/2")
        return labels

    def set_headphone_source(self, target, source):
        index = self._refer_hp_data(target)
        if source in self._labels[self._id]['mixers']:
            ch = self._labels[self._id]['mixers'].index(source)
        elif source.find('aux') == 0:
            ch = len(self._labels[self._id]['mixers'])
        else:
            raise ValueError('Invalid argument for output target')
        fb = self._hp_sources[self._id][index][0]
        value = self._hp_sources[self._id][index][1][ch]
        AvcAudio.set_selector_state(self.fcp, 0, 'current', fb, value)

    def get_headphone_source(self, target):
        index = self._refer_hp_data(target)
        fb = self._hp_sources[self._id][index][0]
        value = AvcAudio.get_selector_state(self.fcp, 0, 'current', fb)
        ch = self._hp_sources[self._id][index][1][value]
        if ch < len(self._labels[self._id]['mixers']):
            return self._labels[self._id]['mixers'][ch]
        return 'aux-1/2'

    def get_meter_labels(self):
        return self._labels[self._id]['meters']

    # 0x0000ffff - 0x7fffffff
    # db = 20 * log10(vol / 0x80000000)
    # vol = 0, then db = -144.0
    # may differs analog-in and the others.
    def get_meters(self):
        labels = self._labels[self._id]['meters']
        meters = {}
        current = self.read_transact(0xffc700600000, self._meters[self._id])
        for i, name in enumerate(labels):
            meters[name] = current[i]
        if len(current) > len(labels):
            misc = current[len(labels)]
            meters['switch-0'] = (misc >> 24) & 0x0f
            meters['switch-1'] = (misc >> 28) & 0x0f
            meters['rotery-0'] = (misc >> 16) & 0x0f
            meters['rotery-1'] = (misc >> 20) & 0x0f
            meters['rotery-2'] = 0
            meters['rate']     = AvcConnection.sampling_rates[(misc >> 8) & 0xff]
            meters['sync']     = (misc >> 0) & 0x0f
        return meters
