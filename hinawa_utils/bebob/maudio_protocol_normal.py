# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from re import match
from struct import unpack

import gi
gi.require_version('Hinawa', '4.0')
from gi.repository import Hinawa

from hinawa_utils.bebob.maudio_protocol_abstract import MaudioProtocolAbstract

from hinawa_utils.ta1394.general import AvcConnection
from hinawa_utils.ta1394.ccm import AvcCcm
from hinawa_utils.ta1394.audio import AvcAudio

__all__ = ['MaudioProtocolNormal']


class MaudioProtocolNormal(MaudioProtocolAbstract):
    __IDS = (
        0x00000a,    # Ozonic
        0x010062,    # Firewire Solo
        0x010060,    # Firewire Audiophile
        0x010046,    # Firewire 410
        # Need information.
        #   NRV10
        #   ProFire Lightbridge
    )

    __LABELS = (
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
                     'aux-out-1', 'aux-out-2')},
    )

    # = __LABELS['inputs']
    __INPUTS = (
        ((3, (1, 2)), (4, (1, 2)), (1, (1, 2)), (2, (1, 2))),
        ((1, (1, 2)), (2, (1, 2)), (4, (1, 2)), (3, (1, 2))),
        ((4, (1, 2)), (5, (1, 2)), (1, (1, 2)), (2, (1, 2)), (3, (1, 2))),
        ((3, (1, 2)), (4, (1, 2)),
         (2, (1, 2)), (1, (1, 2)), (1, (3, 4)), (1, (5, 6)), (1, (7, 8))),
    )

    # = __LABELS['inputs']
    __AUX__INPUTS = (
        (),
        (),
        ((9, (1, 2)), (10, (1, 2)), (6, (1, 2)), (7, (1, 2)), (8, (1, 2))),
        ((7, (1, 2)), (8, (1, 2)), (9, (1, 2)), (6, (1, 2)),
         (5, (1, 2)), (5, (3, 4)), (5, (5, 6)), (5, (7, 8))),
    )

    __AUX_OUTPUT = (
        None,
        None,
        11,
        9,
    )

    # = __LABELS['inputs']
    __MIXER_SOURCES = (
        ((2, (1, 2)), (3, (1, 2)), (0, (1, 2)), (1, (1, 2))),
        ((0, (1, 2)), (1, (1, 2)), (3, (1, 2)), (2, (1, 2))),
        ((3, (1, 2)), (4, (1, 2)), (0, (1, 2)), (1, (1, 2)), (2, (1, 2))),
        ((2, (1, 2)), (3, (1, 2)),
         (1, (1, 2)), (0, (1, 2)), (0, (3, 4)), (0, (5, 6)),
         (0, (7, 8))),
    )

    # = __LABELS['mixers']
    __MIXERS = (
        ((1, (1, 2)), (1, (1, 2))),
        ((1, (1, 2)), (1, (3, 4))),
        ((1, (1, 2)), (2, (1, 2)), (3, (1, 2))),
        ((1, (1, 2)), (1, (3, 4)), (1, (5, 6)), (1, (7, 8)), (1, (9, 10))),
    )

    # = __LABELS['outputs']
    __OUTPUT_SOURCES = (
        (),
        (),
        (1, 2, 3),
        (2, 3, 4, 5, 6),
    )

    # = __LABELS['outputs']
    __OUTPUTS = (
        (),
        (),
        ((12, (1, 2)), (13, (1, 2)), (14, (1, 2))),
        ((10, (1, 2)), (11, (1, 2)), (12, (1, 2)), (13, (1, 2)), (14, (1, 2))),
    )

    __HP_SOURCES = (
        (),
        (),
        ((4, (0, 1, 2, 3)), ),
        ((7, (2, 3, 4, 5, 6, 7)), ),
    )

    __HP_OUTS = (
        (),
        (),
        ((15, (1, 2)), ),
        ((15, (1, 2)), ),
    )

    __METERS = (
        48,
        52,
        60,
        76,
    )

    __CLOCKS = (
        {},
        {'Internal':    AvcCcm.get_subunit_signal_addr('music', 0, 1),
         'S/PDIF':      AvcCcm.get_unit_signal_addr('external', 1)},
        {'Internal':    AvcCcm.get_subunit_signal_addr('music', 0, 1),
         'S/PDIF':      AvcCcm.get_unit_signal_addr('external', 2)},
        {'Internal':    AvcCcm.get_subunit_signal_addr('music', 0, 1),
         'S/PDIF':      AvcCcm.get_unit_signal_addr('external', 2),
         'ADAT':        AvcCcm.get_unit_signal_addr('external', 3)},
    )

    def __init__(self, unit, debug):
        if unit.model_id not in self.__IDS:
            raise OSError('Not supported')

        super().__init__(unit, debug)

        index = self.__IDS.index(unit.model_id)
        self.labels = self.__LABELS[index]
        self.mixers = self.__MIXERS[index]
        self.__inputs = self.__INPUTS[index]
        self.__aux_inputs = self.__AUX__INPUTS[index]
        self.__aux_output = self.__AUX_OUTPUT[index]
        self.__mixer_sources = self.__MIXER_SOURCES[index]
        self.__output_sources = self.__OUTPUT_SOURCES[index]
        self.__outputs = self.__OUTPUTS[index]
        self.__hp_sources = self.__HP_SOURCES[index]
        self.__hp_outs = self.__HP_OUTS[index]
        self.__meters = self.__METERS[index]
        self.__clocks = self.__CLOCKS[index]

    def _refer_fb_data(self, targets, index, ch):
        if index >= len(targets):
            raise ValueError('Invalid argument for function block index')
        if ch >= len(targets[index][1]):
            raise ValueError('Invalid argument for channel number')
        fb = targets[index][0]
        ch = targets[index][1][ch]
        return (fb, ch)

    def _set_volume(self, targets, index, ch, db):
        fb, ch = self._refer_fb_data(targets, index, ch)
        data = AvcAudio.build_data_from_db(db)
        AvcAudio.set_feature_volume_state(self.unit.fcp, 0, 'current', fb, ch,
                                          data)

    def _get_volume(self, targets, index, ch):
        fb, ch = self._refer_fb_data(targets, index, ch)
        data = AvcAudio.get_feature_volume_state(self.unit.fcp, 0, 'current',
                                                 fb, ch)
        return AvcAudio.parse_data_to_db(data)

    def get_input_labels(self):
        return self.labels['inputs']

    def _refer_input_data(self, target):
        if target not in self.labels['inputs']:
            raise ValueError('Invalid argument for input')
        return self.labels['inputs'].index(target)

    def set_input_gain(self, target, ch, db):
        index = self._refer_input_data(target)
        self._set_volume(self.__inputs, index, ch, db)

    def get_input_gain(self, target, ch):
        index = self._refer_input_data(target)
        return self._get_volume(self.__inputs, index, ch)

    def get_input_balance_labels(self):
        labels = []
        for label in self.labels['inputs']:
            if label.find('stream-') == 0:
                continue
            labels.append(label)
        return labels

    def set_input_balance(self, target, ch, balance):
        index = self._refer_input_data(target)
        fb, ch = self._refer_fb_data(self.__inputs, index, ch)
        data = AvcAudio.build_data_from_db(balance)
        AvcAudio.set_feature_lr_state(self.unit.fcp, 0, 'current', fb, ch,
                                      data)

    def get_input_balance(self, target, ch):
        index = self._refer_input_data(target)
        fb, ch = self._refer_fb_data(self.__inputs, index, ch)
        data = AvcAudio.get_feature_lr_state(self.unit.fcp, 0, 'current',
                                             fb, ch)
        return AvcAudio.parse_data_to_db(data)

    def get_output_labels(self):
        if len(self.__outputs) == 0:
            return ()
        return self.labels['outputs']

    def _refer_out_data(self, target):
        if target not in self.labels['outputs']:
            raise ValueError('Invalid argument for output')
        return self.labels['outputs'].index(target)

    def set_output_volume(self, target, ch, db):
        index = self._refer_out_data(target)
        self._set_volume(self.__outputs, index, ch, db)

    def get_output_volume(self, target, ch):
        index = self._refer_out_data(target)
        return self._get_volume(self.__outputs, index, ch)

    def set_aux_volume(self, ch, db):
        if ch > 2:
            raise ValueError('Invalid argument for master channel')
        fb = self.__aux_output
        data = AvcAudio.build_data_from_db(db)
        AvcAudio.set_feature_volume_state(self.unit.fcp, 0, 'current', fb, ch,
                                          data)

    def get_aux_volume(self, ch):
        if ch > 2:
            raise ValueError('Invalid argument for master channel')
        fb = self.__aux_output
        data = AvcAudio.get_feature_volume_state(self.unit.fcp, 0, 'current',
                                                 fb, ch)
        return AvcAudio.parse_data_to_db(data)

    def set_aux_balance(self, ch, balance):
        if ch > 2:
            raise ValueError('Invalid argument for master channel')
        fb = self.__aux_output
        data = AvcAudio.build_data_from_db(balance)
        ch += 1
        AvcAudio.set_feature_lr_state(self.unit.fcp, 0, 'current', fb, ch,
                                      data)

    def get_aux_balance(self, ch):
        if ch > 2:
            raise ValueError('Invalid argument for master channel')
        fb = self.__aux_output
        ch += 1
        data = AvcAudio.get_feature_lr_state(self.unit.fcp, 0, 'current',
                                             fb, ch)
        return AvcAudio.parse_data_to_db(data)

    def get_headphone_labels(self):
        labels = []
        for i in range(len(self.__hp_outs)):
            labels.append('headphone-{0}/{1}'.format(i * 2 + 1, i * 2 + 2))
        return labels

    def _refer_hp_data(self, target):
        matches = match('^headphone-([0-9]*)/([0-9]*)$', target)
        if not matches:
            raise ValueError('Invalid argument for headphone')
        left = int(matches.group(1)) // 2
        right = int(matches.group(2)) // 2
        if right != left + 1:
            raise ValueError('Invalid argument for headphone')
        return left

    def set_headphone_volume(self, target, ch, db):
        index = self._refer_hp_data(target)
        self._set_volume(self.__hp_outs, index, ch, db)

    def get_headphone_volume(self, target, ch):
        index = self._refer_hp_data(target)
        return self._get_volume(self.__hp_outs, index, ch)

    def get_aux_input_labels(self):
        if not self.__aux_output:
            return ()
        return self.labels['inputs']

    def set_aux_input(self, target, ch, db):
        index = self._refer_input_data(target)
        self._set_volume(self.__aux_inputs, index, ch, db)

    def get_aux_input(self, target, ch):
        index = self._refer_input_data(target)
        return self._get_volume(self.__aux_inputs, index, ch)

    def get_mixer_labels(self):
        return self.labels['mixers']

    def get_mixer_source_labels(self):
        return self.labels['inputs']

    def _refer_mixer_data(self, target, source):
        if source not in self.labels['inputs']:
            raise ValueError('Invalid argument for mixer input')
        if target not in self.labels['mixers']:
            raise ValueError('Invalid argument for mixer output')
        input = self.labels['inputs'].index(source)
        in_fb = self.__mixer_sources[input][0]
        in_ch = self.__mixer_sources[input][1][0]   # Use left channel.
        mixer = self.labels['mixers'].index(target)
        out_fb = self.mixers[mixer][0]
        out_ch = self.mixers[mixer][1][0]  # Use left channel.
        return (in_fb, in_ch, out_fb, out_ch)

    def set_mixer_routing(self, target, source, enable):
        in_fb, in_ch, out_fb, out_ch = self._refer_mixer_data(target, source)
        if enable:
            data = (0x00, 0x00)
        else:
            data = (0x80, 0x00)
        AvcAudio.set_processing_mixer_state(self.unit.fcp, 0, 'current',
                                            out_fb, in_fb, in_ch, out_ch, data)

    def get_mixer_routing(self, target, source):
        in_fb, in_ch, out_fb, out_ch = self._refer_mixer_data(target, source)
        data = AvcAudio.get_processing_mixer_state(self.unit.fcp, 0, 'current',
                                                   out_fb, in_fb, in_ch, out_ch)
        return data[0] == 0x00 and data[1] == 0x00

    def get_headphone_source_labels(self, target):
        labels = []
        if len(self.__hp_sources) > 0:
            for mixer in self.labels['mixers']:
                labels.append(mixer)
            if self.__aux_output:
                labels.append("aux-1/2")
        return labels

    def set_headphone_source(self, target, source):
        index = self._refer_hp_data(target)
        if source in self.labels['mixers']:
            ch = self.labels['mixers'].index(source)
        elif source.find('aux') == 0:
            ch = len(self.labels['mixers'])
        else:
            raise ValueError('Invalid argument for output target')
        fb = self.__hp_sources[index][0]
        value = self.__hp_sources[index][1][ch]
        AvcAudio.set_selector_state(self.unit.fcp, 0, 'current', fb, value)

    def get_headphone_source(self, target):
        index = self._refer_hp_data(target)
        fb = self.__hp_sources[index][0]
        value = AvcAudio.get_selector_state(self.unit.fcp, 0, 'current', fb)
        ch = self.__hp_sources[index][1][value]
        if ch < len(self.labels['mixers']):
            return self.labels['mixers'][ch]
        return 'aux-1/2'

    def get_output_source_labels(self, target):
        index = self._refer_out_data(target)
        labels = []
        labels.append(self.labels['mixers'][index])
        if self.__aux_output:
            labels.append("aux-1/2")
        return labels

    def set_output_source(self, target, source):
        index = self._refer_out_data(target)
        if source in self.labels['mixers'][index]:
            value = 0
        elif source.find('aux') == 0:
            value = 1
        else:
            raise ValueError('Invalid argument for output target')
        fb = self.__output_sources[index]
        AvcAudio.set_selector_state(self.unit.fcp, 0, 'current', fb, value)

    def get_output_source(self, target):
        index = self._refer_out_data(target)
        fb = self.__output_sources[index]
        value = AvcAudio.get_selector_state(self.unit.fcp, 0, 'current', fb)
        if value == 1 and self.__aux_output:
            return 'aux-1/2'
        return self.labels['mixers'][index]

    # 0x0000ffff - 0x7fffffff
    # db = 20 * log10(vol / 0x80000000)
    # vol = 0, then db = -144.0
    # may differs analog-in and the others.
    def get_meters(self):
        labels = self.labels['meters']
        meters = {}
        req = Hinawa.FwReq.new()
        frames = [0] * 256
        _, data = req.transaction(self.unit.get_node(),
                                  Hinawa.FwTcode.READ_BLOCK_REQUEST,
                                  self._ADDR_FOR_METERING, self.__meters,
                                  frames, 100)
        for i, name in enumerate(labels):
            meters[name] = unpack('>I', data[i * 4:(i + 1) * 4])[0]
        if len(data) > len(labels) * 4:
            meters['rotery-0'] = data[-3] & 0x0f
            meters['rotery-1'] = (data[-3] & 0xf0) >> 4
            meters['rotery-2'] = 0
            meters['switch-0'] = (data[-4] & 0xf0) >> 4
            meters['switch-1'] = data[-4] & 0x0f
            meters['rate'] = AvcConnection.SAMPLING_RATES[data[-2]]
            meters['sync'] = data[-1] & 0x0f
        return meters

    def get_clock_source_labels(self):
        return self.__clocks.keys()

    def set_clock_source(self, src):
        if self.unit.get_property('is-locked'):
            raise ValueError('Packet is-locked already runs.')
        dst = AvcCcm.get_subunit_signal_addr('music', 0, 1)
        addr = self.__clocks[src]
        AvcCcm.set_signal_source(self.unit.fcp, addr, dst)

    def get_clock_source(self):
        dst = AvcCcm.get_subunit_signal_addr('music', 0, 1)
        curr = AvcCcm.get_signal_source(self.unit.fcp, dst)
        for name, addr in self.__clocks.items():
            if AvcCcm.compare_addrs(curr, AvcCcm.parse_signal_addr(addr)):
                return name

    def get_sampling_rate(self):
        in_rate = AvcConnection.get_plug_signal_format(self.unit.fcp, 'input',
                                                       0)
        out_rate = AvcConnection.get_plug_signal_format(self.unit.fcp,
                                                        'output', 0)
        if in_rate != out_rate:
            raise OSError('Unexpected state of the unit: {0}!={1}'.format(
                in_rate, out_rate))
        return in_rate
