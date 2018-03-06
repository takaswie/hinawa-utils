from re import match
import gi

gi.require_version('Hinawa', '1.0')
from gi.repository import Hinawa

from bebob.bebob_unit import BebobUnit

from bebob.maudio_protocol_abstract import MaudioProtocolAbstract

from ta1394.general import AvcConnection
from ta1394.ccm import AvcCcm
from ta1394.audio import AvcAudio

__all__ = ['MaudioProtocolNormal']

class MaudioProtocolNormal(MaudioProtocolAbstract):
    _IDS = (
        0x00000a,    # Ozonic
        0x010062,    # Firewire Solo
        0x010060,    # Firewire Audiophile
        0x010046,    # Firewire 410
        # Need information.
        #   NRV10
        #   ProFire Lightbridge
    )

    _LABELS = (
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

    # = _LABELS['inputs']
    _INPUTS = (
        (( 3, (1, 2)), ( 4, (1, 2)), ( 1, (1, 2)), ( 2, (1, 2))),
        (( 1, (1, 2)), ( 2, (1, 2)), ( 4, (1, 2)), ( 3, (1, 2))),
        (( 4, (1, 2)), ( 5, (1, 2)), ( 1, (1, 2)), ( 2, (1, 2)), ( 3, (1, 2))),
        (( 3, (1, 2)), ( 4, (1, 2)),
         ( 2, (1, 2)), ( 1, (1, 2)), ( 1, (3, 4)), ( 1, (5, 6)), ( 1, (7, 8))),
    )

    # = _LABELS['inputs']
    _AUX_INPUTS = (
        (),
        (),
        (( 9, (1, 2)), (10, (1, 2)), ( 6, (1, 2)), ( 7, (1, 2)), ( 8, (1, 2))),
        (( 7, (1, 2)), ( 8, (1, 2)), ( 9, (1, 2)), ( 6, (1, 2)),
         ( 5, (1, 2)), ( 5, (3, 4)), ( 5, (5, 6)), ( 5, (7, 8))),
    )

    _AUX_OUTPUT = (
        None,
        None,
        11,
         9,
    )

    # = _LABELS['inputs']
    _MIXER_SOURCES = (
        (( 2, (1, 2)), ( 3, (1, 2)), ( 0, (1, 2)), ( 1, (1, 2))),
        (( 0, (1, 2)), ( 1, (1, 2)), ( 3, (1, 2)), ( 2, (1, 2))),
        (( 3, (1, 2)), ( 4, (1, 2)), ( 0, (1, 2)), ( 1, (1, 2)), ( 2, (1, 2))),
        (( 2, (1, 2)), ( 3, (1, 2)),
         ( 1, (1, 2)), ( 0, (1, 2)), ( 0, (3, 4)), ( 0, (5, 6)),
         ( 0, (7, 8))),
    )

    # = _LABELS['mixers']
    _MIXERS = (
        (( 1, (1, 2)), ( 1, (1, 2))),
        (( 1, (1, 2)), ( 1, (3, 4))),
        (( 1, (1, 2)), ( 2, (1, 2)), ( 3, (1, 2))),
        (( 1, (1, 2)), ( 1, (3, 4)), ( 1, (5, 6)), ( 1, (7, 8)), ( 1, (9, 10))),
    )

    # = _LABELS['outputs']
    _OUTPUT_SOURCES = (
        (),
        (),
        ( 1, 2, 3),
        ( 2, 3, 4, 5, 6),
    )

    # = _LABELS['outputs']
    _OUTPUTS = (
        (),
        (),
        ((12, (1, 2)), (13, (1, 2)), (14, (1, 2))),
        ((10, (1, 2)), (11, (1, 2)), (12, (1, 2)), (13, (1, 2)), (14, (1, 2))),
    )

    _HP_SOURCES = (
        (),
        (),
        (( 4, (0, 1, 2, 3)), ),
        (( 7, (2, 3, 4, 5, 6, 7)), ),
    )

    _HP_OUTS = (
        (),
        (),
        ((15, (1, 2)), ),
        ((15, (1, 2)), ),
    )

    _METERS = (
        48 // 4,
        52 // 4,
        60 // 4,
        76 // 4,
    )

    _CLOCKS = (
        {},
        {'Internal':    AvcCcm.get_subunit_signal_addr('music', 0, 1),
         'S/PDIF':      AvcCcm.get_unit_signal_addr('external', 1)},
        {'Internal':    AvcCcm.get_subunit_signal_addr('music', 0, 1),
         'S/PDIF':      AvcCcm.get_unit_signal_addr('external', 2)},
        {'Internal':    AvcCcm.get_subunit_signal_addr('music', 0, 1),
         'S/PDIF':      AvcCcm.get_unit_signal_addr('external', 2),
         'ADAT':        AvcCcm.get_unit_signal_addr('external', 3)},
    )

    def __init__(self, unit, debug, model_id):
        super().__init__(unit, debug)
        if model_id not in self._IDS:
            raise OSError('Not supported')
        index = self._IDS.index(model_id)
        self._labels = self._LABELS[index]
        self._inputs = self._INPUTS[index]
        self._aux_inputs = self._AUX_INPUTS[index]
        self._aux_output = self._AUX_OUTPUT[index]
        self._mixer_sources = self._MIXER_SOURCES[index]
        self._mixers = self._MIXERS[index]
        self._output_sources = self._OUTPUT_SOURCES[index]
        self._outputs = self._OUTPUTS[index]
        self._hp_sources = self._HP_SOURCES[index]
        self._hp_outs = self._HP_OUTS[index]
        self._meters = self._METERS[index]
        self._clocks = self._CLOCKS[index]

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
        AvcAudio.set_feature_volume_state(self._unit.fcp, 0, 'current', fb, ch,
                                          data)
    def _get_volume(self, targets, index, ch):
        fb, ch = self._refer_fb_data(targets, index, ch)
        data = AvcAudio.get_feature_volume_state(self._unit.fcp, 0, 'current',
                                                 fb, ch)
        return AvcAudio.parse_data_to_db(data)

    def get_input_labels(self):
        return self._labels['inputs']
    def _refer_input_data(self, target):
        if target not in self._labels['inputs']:
            raise ValueError('Invalid argument for input')
        return self._labels['inputs'].index(target)
    def set_input_gain(self, target, ch, db):
        index = self._refer_input_data(target)
        self._set_volume(self._inputs, index, ch, db)
    def get_input_gain(self, target, ch):
        index = self._refer_input_data(target)
        return self._get_volume(self._inputs, index, ch)

    def get_output_labels(self):
        if len(self._outputs) == 0:
            return ()
        return self._labels['outputs']
    def _refer_out_data(self, target):
        if target not in self._labels['outputs']:
            raise ValueError('Invalid argument for output')
        return self._labels['outputs'].index(target)
    def set_output_volume(self, target, ch, db):
        index = self._refer_out_data(target)
        self._set_volume(self._outputs, index, ch, db)
    def get_output_volume(self, target, ch):
        index = self._refer_out_data(target)
        return self._get_volume(self._outputs, index, ch)

    def set_aux_volume(self, ch, db):
        if ch > 2:
            raise ValueError('Invalid argument for master channel')
        fb = self._aux_output
        data = AvcAudio.build_data_from_db(db)
        AvcAudio.set_feature_volume_state(self._unit.fcp, 0, 'current', fb, ch,
                                          data)
    def get_aux_volume(self, ch):
        if ch > 2:
            raise ValueError('Invalid argument for master channel')
        fb = self._aux_output
        data = AvcAudio.get_feature_volume_state(self._unit.fcp, 0, 'current',
                                                 fb, ch)
        return AvcAudio.parse_data_to_db(data)

    def get_headphone_labels(self):
        labels = []
        for i in range(len(self._hp_outs)):
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
        self._set_volume(self._hp_outs, index, ch, db)
    def get_headphone_volume(self, target, ch):
        index = self._refer_hp_data(target)
        return self._get_volume(self._hp_outs, index, ch)

    def get_aux_input_labels(self):
        if not self._aux_output:
            return ()
        return self._labels['inputs']
    def set_aux_input(self, target, ch, db):
        index = self._refer_input_data(target)
        self._set_volume(self._aux_inputs, index, ch, db)
    def get_aux_input(self, target, ch):
        index = self._refer_input_data(target)
        return self._get_volume(self._aux_inputs, index, ch)

    def get_mixer_labels(self):
        return self._labels['mixers']
    def get_mixer_source_labels(self):
        return self._labels['inputs']
    def _refer_mixer_data(self, target, source):
        if source not in self._labels['inputs']:
            raise ValueError('Invalid argument for mixer input')
        if target not in self._labels['mixers']:
            raise ValueError('Invalid argument for mixer output')
        input = self._labels['inputs'].index(source)
        in_fb = self._mixer_sources[input][0]
        in_ch = self._mixer_sources[input][1][0]   # Use left channel.
        mixer = self._labels['mixers'].index(target)
        out_fb = self._mixers[mixer][0]
        out_ch = self._mixers[mixer][1][0]  # Use left channel.
        return (in_fb, in_ch, out_fb, out_ch)
    def set_mixer_routing(self, target, source, enable):
        in_fb, in_ch, out_fb, out_ch = self._refer_mixer_data(target, source)
        if enable:
            data = (0x00, 0x00)
        else:
            data = (0x80, 0x00)
        AvcAudio.set_processing_mixer_state(self._unit.fcp, 0, 'current',
                                            out_fb, in_fb, in_ch, out_ch, data)
    def get_mixer_routing(self, target, source):
        in_fb, in_ch, out_fb, out_ch = self._refer_mixer_data(target, source)
        data = AvcAudio.get_processing_mixer_state(self._unit.fcp, 0, 'current',
                                                   out_fb, in_fb, in_ch, out_ch)
        return data[0] == 0x00 and data[1] == 0x00

    def get_headphone_source_labels(self, target):
        labels = []
        if len(self._hp_sources) > 0:
            for mixer in self._labels['mixers']:
                labels.append(mixer)
            if self._aux_output:
                labels.append("aux-1/2")
        return labels
    def set_headphone_source(self, target, source):
        index = self._refer_hp_data(target)
        if source in self._labels['mixers']:
            ch = self._labels['mixers'].index(source)
        elif source.find('aux') == 0:
            ch = len(self._labels['mixers'])
        else:
            raise ValueError('Invalid argument for output target')
        fb = self._hp_sources[index][0]
        value = self._hp_sources[index][1][ch]
        AvcAudio.set_selector_state(self._unit.fcp, 0, 'current', fb, value)
    def get_headphone_source(self, target):
        index = self._refer_hp_data(target)
        fb = self._hp_sources[index][0]
        value = AvcAudio.get_selector_state(self._unit.fcp, 0, 'current', fb)
        ch = self._hp_sources[index][1][value]
        if ch < len(self._labels['mixers']):
            return self._labels['mixers'][ch]
        return 'aux-1/2'

    def get_output_source_labels(self, target):
        index = self._refer_out_data(target)
        labels = []
        labels.append(self._labels['mixers'][index])
        if self._aux_output:
            labels.append("aux-1/2")
        return labels
    def set_output_source(self, target, source):
        index = self._refer_out_data(target)
        if source in self._labels['mixers'][index]:
            value = 0
        elif source.find('aux') == 0:
            value = 1
        else:
            raise ValueError('Invalid argument for output target')
        fb = self._output_sources[index]
        AvcAudio.set_selector_state(self._unit.fcp, 0, 'current', fb, value)
    def get_output_source(self, target):
        index = self._refer_out_data(target)
        fb = self._output_sources[index]
        value = AvcAudio.get_selector_state(self._unit.fcp, 0, 'current', fb)
        if value == 1 and self._aux_output:
            return 'aux-1/2'
        return self._labels['mixers'][index]

    # 0x0000ffff - 0x7fffffff
    # db = 20 * log10(vol / 0x80000000)
    # vol = 0, then db = -144.0
    # may differs analog-in and the others.
    def get_meters(self):
        labels = self._labels['meters']
        meters = {}
        req = Hinawa.FwReq()
        current = req.read(self._unit, 0xffc700600000, self._meters)
        for i, name in enumerate(labels):
            meters[name] = current[i]
        if len(current) > len(labels):
            misc = current[len(labels)]
            # From Audiophile, several bits stand by one operation.
            meters['switch-0'] = 0
            meters['switch-1'] = 0
            meters['rotery-0'] = (misc >> 16) & 0x0f
            meters['rotery-1'] = (misc >> 20) & 0x0f
            meters['rotery-2'] = 0
            if meters['rotery-0'] == 0:
                meters['switch-0'] = (misc >> 24) & 0x0f
            if meters['switch-0'] == 0:
                meters['switch-1'] = (misc >> 28) & 0x0f
            meters['rate'] = AvcConnection.sampling_rates[(misc >> 8) & 0xff]
            meters['sync'] = (misc >> 0) & 0x0f
        return meters

    def get_clock_source_labels(self):
        return self._clocks.keys()
    def set_clock_source(self, src):
        if self._unit.get_property('streaming'):
            raise ValueError('Packet streaming already runs.')
        dst = AvcCcm.get_subunit_signal_addr('music', 0, 1)
        addr = self._clocks[src]
        AvcCcm.set_signal_source(self._unit.fcp, addr, dst)
    def get_clock_source(self):
        dst = AvcCcm.get_subunit_signal_addr('music', 0, 1)
        curr = AvcCcm.get_signal_source(self._unit.fcp, dst)
        for name, addr in self._clocks.items():
            if AvcCcm.compare_addrs(curr, AvcCcm.parse_signal_addr(addr)):
                return name

    def get_sampling_rate(self):
        in_rate = AvcConnection.get_plug_signal_format(self._unit.fcp, 'input',
                                                       0)
        out_rate = AvcConnection.get_plug_signal_format(self._unit.fcp,
                                                        'output', 0)
        if in_rate != out_rate:
            raise OSError('Unexpected state of the unit: {0}!={1}'.format(
                                                            in_rate, out_rate))
        return in_rate
