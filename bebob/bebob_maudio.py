#!/usr/bin/env python3

import sys

from bebob.bebob_unit import BebobUnit

from ta1394.general import AvcGeneral
from ta1394.audio import AvcAudio

import re

class BebobMaudio(BebobUnit):
    _labels = (
        {'inputs':  ('Analog 1/2', 'Digital 1/2',
                     'Stream 1/2', 'Stream 3/4', 'Stream 5/6', 'Stream 7/8',
                     'Stream 9/10'),
         'outputs': ('Analog 1/2', 'Analog 3/4', 'Analog 5/6', 'Analog 7/8',
                     'Digital 1/2'),
         'mixers':  ('Mixer 1/2', 'Mixer 3/4', 'Mixer 5/6', 'Mixer 7/8',
                     'Mixer 9/10'),
         'meters':  ('Analog in 1', 'Analog in 2',
                     'Digital in 1', 'Digital in 2',
                     'Analog out 1', 'Analog out 2',
                     'Analog out 3', 'Analog out 4',
                     'Analog out 5', 'Analog out 6',
                     'Analog out 7', 'Analog out 8',
                     'Digital out 1', 'Digital out 2',
                     'Headphone out 1', 'Headphone out 2')},
        {'inputs':  ('Analog 1/2', 'Analog 3/4', 'Analog 5/6', 'Analog 7/8',
                     'Stream 1/2', 'Stream 3/4',
                     'ADAT 1/2', 'ADAT 3/4', 'ADAT 5/6', 'ADAT 7/8',
                     'S/PDIF 1/2'),
         'outputs': ('Analog 1/2', 'Analog 3/4'),
         'mixers':  ('Mixer 1/2', 'Mixer 3/4'),
         'meters':  ('Analog in 1', 'Analog in 2',
                     'Analog in 3', 'Analog in 4',
                     'Analog in 5', 'Analog in 6',
                     'Analog in 7', 'Analog in 8',
                     'S/PDIF in 1', 'S/PDIF in 2',
                     'ADAT in 1', 'ADAT in 2', 'ADAT in 3', 'ADAT in 4',
                     'Analog out 1', 'Analog out 2',
                     'Analog out 3', 'Analog out 4',
                     'S/PDIF out 1', 'S/PDIF out 2',
                     'ADAT out 1', 'ADAT out 2', 'ADAT out 3', 'ADAT out 4',
                    )},
    )

    # = _labels['inputs']
    _inputs = (
        (( 3, (1, 2)), ( 4, (1, 2)),
         ( 1, (1, 2)), ( 1, (3, 4)), ( 1, (5, 6)), ( 1, (7, 8)), ( 2, (1, 2))),
        (( 1, (1, 2)), ( 2, (1, 2)), ( 3, (1, 2)), ( 4, (1, 2)),
         (10, (1, 2)), (11, (1, 2)),
         ( 5, (1, 2)),
         ( 6, (1, 2)), ( 7, (1, 2)), ( 8, (1, 2)), ( 9, (1, 2))),
    )

    # = _labels['inputs']
    _aux_sources = (
        (( 7, (1, 2)), ( 8, (1, 2)), ( 9, (1, 2)), ( 6, (1, 2)),
         ( 5, (1, 2)), ( 5, (3, 4)), ( 5, (5, 6)), ( 5, (7, 8))),
        ((19, (1, 2)), (20, (1, 2)), (21, (1, 2)), (22, (1, 2)),
         (17, (1, 2)), (18, (1, 2)),
         (23, (1, 2)),
         (24, (1, 2)), (25, (1, 2)), (26, (1, 2)), (27, (1, 2))),
    )

    _aux_output = (
         9,
        13,
    )

    # = _labels['inputs']
    _mixer_sources = (
        (( 2, (1, 2)), ( 3, (1, 2)),
         ( 0, (1, 2)), ( 0, (3, 4)), ( 0, (5, 6)), ( 0, (7, 8)),
         ( 1, (1, 2))),
        (( 1, (1, 2)), ( 1, (3, 4)), ( 1, (5, 6)), ( 1, (7, 8)),
         ( 2, (1, 2)), ( 2, (3, 4)),
         ( 3, (1, 2)),
         ( 4, (1, 2)), ( 4, (3, 4)), ( 4, (5, 6)), ( 4, (7, 8))),
    )

    # = _labels['outputs']
    _mixer_sinks = (
        (( 1, (1, 2)), ( 1, (3, 4)), ( 1, (5, 6)), ( 1, (7, 8)), ( 1, (9, 10))),
        (( 1, (1, 2)), ( 2, (1, 2))),
    )

    # = _labels['outputs']
    _output_sources = (
        (( 2, (1, 2)), ( 3, (1, 2)), ( 4, (1, 2)), ( 5, (1, 2)), ( 6, (1, 2))),
        (( 3, (1, 2)), ( 4, (1, 2))),
    )

    # = _labels['outputs']
    _outputs = (
        ((10, (1, 2)), (11, (1, 2)), (12, (1, 2)), (13, (1, 2)), (14, (1, 2))),
        ((12, (1, 2)), (13, (1, 2))),
    )

    _hp_sources = (
        (( 7, (2, 3, 4, 5, 6, 7))),
        (( 1, (1, 2, 4)), ( 2, (1, 2, 4))),
    )

    _hp_outs = (
        ((15, (1, 2)), ),
        ((15, (1, 2)), (16, (1, 2))),
    )

    _meters = (76, 84, )

    def __init__(self, path):
        super().__init__(path)
        self._id = 0
        info = AvcGeneral.get_unit_info(self.fcp)
        self._company_ids = info['company-id']

    def _refer_fb_data(self, targets, index, ch):
        if index > len(targets):
            raise ValueError('Invalid argument for function block index')
        if ch > len(targets[index][1]):
            raise ValueError('Invalid argument for channel number')
        fb = targets[index][0]
        ch = targets[index][1][0]
        return (fb, ch)

    def _set_mute(self, targets, index, ch, value):
        fb, ch = self._refer_fb_data(targets, index, ch)
        AvcAudio.set_feature_mute_state(self.fcp, 0, 'current', fb, ch, value)
    def _get_mute(self, targets, index, ch):
        fb, ch = self._refer_fb_data(targets, index, ch)
        return AvcAudio.get_feature_mute_state(self.fcp, 0, 'current', fb, ch)

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

    def set_input_mute(self, target, ch, value):
        index = self._refer_input_data(target)
        self._set_mute(self._inputs[self._id], index, ch, value)
    def get_input_mute(self, target, ch):
        index = self._refer_input_data(target)
        return self._get_mute(self._inputs[self._id], index, ch)

    def set_input_volume(self, target, ch, value):
        index = self._refer_input_data(target)
        self._set_volume(self._inputs[self._id], index, ch, value)
    def get_input_volume(self, target, ch):
        index = self._refer_input_data(target)
        return self._get_volume(self._inputs[self._id], index, ch)


    def get_aux_source_labels(self):
        return self._labels[self._id]['inputs']

    def set_aux_source_mute(self, target, ch, value):
        index = self._refer_input_data(target)
        self._set_mute(self._aux_sources[self._id], index, ch, value)
    def get_aux_source_mute(self, target, ch):
        index = self._refer_input_data(target)
        return self._get_mute(self._aux_sources[self._id], index, ch)

    def set_aux_source_volume(self, target, ch, value):
        index = self._refer_input_data(target)
        self._set_volume(self._aux_sources[self._id], index, ch, value)
    def get_aux_source_volume(self, target, ch):
        index = self._refer_input_data(target)
        return self._get_volume(self._aux_sources[self._id], index, ch)


    def set_aux_master_mute(self, ch, value):
        if ch > 2:
            raise ValueError('Invalid argument for master channel')
        fb = self._aux_output[self._id]
        AvcAudio.set_feature_mute_state(self.fcp, 0, 'current', fb, ch, value)
    def get_aux_master_mute(self, ch):
        if ch > 2:
            raise ValueError('Invalid argument for master channel')
        fb = self._aux_output[self._id]
        return AvcAudio.get_feature_mute_state(self.fcp, 0, 'current', fb, ch)

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

    def set_output_mute(self, target, ch, value):
        index = self._refer_out_data(target)
        self._set_mute(self._outputs[self._id], index, ch, value)
    def get_output_mute(self, target, ch):
        index = self._refer_out_data(target)
        return self._get_mute(self._outputs[self._id], index, ch)

    def set_output_volume(self, target, ch):
        index = self._refer_out_data(target)
        self._set_volume(self._outputs[self._id], index, ch, value)
    def get_output_volume(self, target, ch):
        index = self._refer_out_data(target)
        return self._get_volume(self._outputs[self._id], index, ch)


    def get_output_source_labels(self, target):
        index = self._refer_out_data(target)
        labels = []
        labels.append(self._labels[self._id]['mixers'][index] + ' out')
        labels.append("Aux 1/2 out")
        return labels

    def set_output_source(self, target, source):
        index = self._refer_out_data(target)
        if source in self._labels[self._id]['mixers']:
            ch = 0
        elif source.find('Aux'):
            ch = 1
        else:
            raise ValueError('Invalid argument for output target')
        fb = self._output_sources[self._id][index][0]
        value = self._output_sources[self.id][index][1][ch]
        AvcAudio.set_selector_state(self.fcp, 0, 'current', fb, value)

    def get_output_source(self, target):
        index = self._refer_out_data(target)
        fb = self._output_sources[self._id][index][0]
        value = AvcAudio.get_selector_state(self.fcp, 0, 'current', fb)
        if self._output_sources[index][1].index(value) == 0:
            return self._labels[self._id]['mixers'][index]
        return 'Aux 1/2 out'


    def get_headphone_labels(self):
        labels = []
        for i in range(len(self._hp_outs[self._id])):
            labels.append('Headphone {0}/{1}'.format(i * 2 + 1, i * 2 + 2))
        return labels

    _hp_expr = re.compile('^Headphone ([0-9]*)/([0-9]*)$')

    def _refer_hp_data(self, target):
        matches = self._hp_expr.match(target)
        if not matches:
            raise ValueError('Invalid argument for headphone')
        left = int(matches.group(1)) // 2
        right = int(matches.group(2)) // 2
        if right != left + 1:
            raise ValueError('Invalid argument for headphone')
        return left

    def set_headphone_mute(self, target, ch, value):
        index = self._refer_hp_data(target)
        self._set_mute(self._hp_outs[self._id], index, ch, value)
    def get_headphone_mute(self, target, ch):
        index = self._refer_hp_data(target)
        return self._get_mute(self._hp_outs[self._id], index, ch)

    def set_headphone_volume(self, target, ch, value):
        index = self._refer_hp_data(target)
        self._set_volume(self._hp_outs[self._id], index, ch, value)
    def get_headphone_volume(self, target, ch):
        index = self._refer_hp_data(target)
        return self._get_volume(self._hp_outs[self._id], index, ch)


    def get_headphone_source_labels(self, target):
        index = self._refer_out_data(target)
        labels = []
        for mixer in self._labels[self._id]['mixers']:
            labels.append(mixer + ' out')
        labels.append("Aux 1/2 out")
        return labels

    def set_headphone_source(self, target, source):
        index = self._refer_out_data(target)
        if source in self._labels[self._id]['mixers']:
            ch = self._labels[self._id]['mixers'].index(source)
        elif source.find('Aux'):
            ch = len(self._labels[self._id]['mixers'])
        else:
            raise ValueError('Invalid argument for output target')
        fb = self._hp_sources[self._id][index][0]
        value = self._hp_sources[self.id][index][1][ch]
        AvcAudio.set_selector_state(self.fcp, 0, 'current', fb, value)

    def get_headphone_source(self, target):
        index = self._refer_out_data(target)
        fb = self._hp_sources[self._id][index][0]
        value = AvcAudio.get_selector_state(self.fcp, 0, 'current', fb)
        ch = self._hp_sources[index][1].index(value)
        if ch < len(self._labels[self._id]['mixers']):
            return self._labels[self._id]['mixers'][ch]
        return 'Aux 1/2 out'

    def get_meter_labels(self):
        return self._labels[self._id]['meters']

    # 0x0000ffff - 0x7fffffff
    # db = 20 * log10(vol / 0x80000000)
    # vol = 0, then db = -144.0
    #
    # fw410: 19
    # audiophile: 15
    def get_meters(self):
        length = self._meters[self._id]
        return self.read_transact(0xffc700600000, length)
