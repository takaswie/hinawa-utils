from bebob.bebob_unit import BebobUnit

from ta1394.general import AvcGeneral
from ta1394.general import AvcConnection
from ta1394.audio import AvcAudio

from bebob.extensions import BcoVendorDependent
from bebob.extensions import BcoPlugInfo
from bebob.extensions import BcoStreamFormatInfo

__all__ = ['YamahaTerratec']

class YamahaTerratec(BebobUnit):
    channel_ops = ('volume', 'mute')
    supported_clock_sources = ('Internal', 'S/PDIF')
    supported_sampling_rates = (32000, 44100, 48000, 88200, 96000, 192000)

    def __init__(self, path):
        super().__init__(path)
        for quad in self.get_config_rom():
            # Vendor ID
            if quad >> 24 == 0x03:
                vendor_id = quad & 0x00ffffff
                continue
            # Model ID
            if quad >> 24 == 0x17:
                model_id = quad & 0x00ffffff
                break
        else:
            raise ValueError('Invalid argument for Yamaha/Terratec unit')
        # Check vendor ID for Yamaha/Terratec OUI
        if vendor_id != 0x00a0de and vendor_id != 0x000aac:
            raise ValueError('Invalid argument for Yamaha/Terratec unit')
        # Yamaha GO 44 or Terratec Phase 24 FW
        if model_id == 0x10000b or model_id == 0x000005:
            self.name = 'GO44'
            self._output_sink_labels = (
                'analog-1/2', 'headphone-1/2', 'digital-1/2')
            self._mixer_output_fb = 1
            self._input_level_labels = {
                'low':      (0xf4, 0x00),
                'middle':   (0xfd, 0x00),
                'high':     (0x00, 0x00),
            }
            self._output_labels = ()
        # Yamaha GO 46 or Terratec Phase X24 FW
        elif model_id == 0x10000c or model_id == 0x000007:
            self.name = 'GO46'
            self._output_sink_labels = (
                'analog-1/2', 'analog-3/4', 'digital-1/2')
            self._mixer_output_fb = 2
            self._output_fb = 1
            self._input_level_labels = {}
            self._output_labels = ('analog-1/2', 'analog-3/4')
        else:
            raise ValueError('Invalid argument for Yamaha/Terratec unit')
        unit_info = AvcGeneral.get_unit_info(self.fcp)
        self._company_ids = unit_info['company-id']

    def get_stream_formats(self):
        fmts = dict.fromkeys(('capture', 'playback'), [])
        addr = BcoPlugInfo.get_unit_addr('output', 'isoc', 0)
        fmts['capture'] = BcoStreamFormatInfo.get_entry_list(self.fcp, addr)
        addr = BcoPlugInfo.get_unit_addr('input', 'isoc', 0)
        fmts['playback'] = BcoStreamFormatInfo.get_entry_list(self.fcp, addr)
        return fmts

    def _set_state(self, op, fb, ch, db):
        if op == 'volume':
            data = AvcAudio.build_data_from_db(db)
            AvcAudio.set_feature_volume_state(self.fcp, 0, 'current',
                                              fb, ch, data)
        elif op == 'mute':

            AvcAudio.set_feature_mute_state(self.fcp, 0, 'current',
                                            fb, ch, value)
        else:
            raise ValueError('Invalid argument for channel operation')
    def _get_state(self, op, fb, ch):
        if op == 'volume':
            data = AvcAudio.get_feature_volume_state(self.fcp, 0, 'current',
                                                     fb, ch)
            return AvcAudio.parse_data_to_db(data)
        elif op == 'mute':
            return AvcAudio.get_feature_mute_state(self.fcp, 0, 'current',
                                                   fb, ch)
        else:
            raise ValueError('Invalid argument for channel operation')

    def get_input_level_labels(self):
        return self._input_level_labels.keys()
    def set_input_level(self, level):
        if len(self._input_level_labels) == 0:
            raise OSError('Not supported')
        if level not in self._input_level_labels:
            raise ValueError('Invalid argument for input level.')
        data = self._input_level_labels[level]
        AvcAudio.set_feature_volume_state(self.fcp, 0, 'current', 2, 0, data)
    def get_input_level(self):
        if len(self._input_level_labels) == 0:
            raise OSError('Not supported')
        result = AvcAudio.get_feature_volume_state(self.fcp, 0, 'current', 2, 0)
        for name, data in self._input_level_labels.items():
            if data == result:
                return name
        else:
            raise OSError('Unexpected value for input level')

    def get_output_labels(self):
        return self._output_labels
    def set_output(self, op, output, ch, db):
        if len(self._output_labels) == 0:
            raise ValueError('Not supported')
        if op not in self.channel_ops:
            raise ValueError('Invalid argument for channel operation')
        if output not in self._output_labels:
            raise ValueError('Invalid argument for channel name')
        ch = self._output_labels.index(output) + ch
        self._set_state(op, 1, ch, db)
    def get_output(self, op, output, ch):
        if len(self._output_labels) == 0:
            raise ValueError('Not supported')
        if op not in self.channel_ops:
            raise ValueError('Invalid argument for channel operation')
        if output not in self._output_labels:
            raise ValueError('Invalid argument for channel name')
        ch = 1 + self._output_labels.index(output) + ch
        return self._get_state(op, 1, ch)

    _mixer_input_labels = (
        'analog-1/2', 'digital-1/2',
        'stream-1/2', 'stream-3/4', 'stream-5/6')
    _mixer_input_fbs = (6, 7, 3, 4, 5)
    def get_mixer_input_labels(self):
        return self._mixer_input_labels
    def set_mixer_input(self, op, pair, ch, db):
        if op not in self.channel_ops:
            raise ValueError('Invalid argument for channel operation.')
        if pair not in self._mixer_input_labels:
            raise ValueError('Invalid argument for input stereo pair.')
        fb = self._mixer_input_fbs[self._mixer_input_labels.index(pair)]
        self._set_state(op, fb, ch, db)
    def get_mixer_input(self, op, pair, ch):
        if op not in self.channel_ops:
            raise ValueError('Invalid argument for channel operation.')
        if pair not in self._mixer_input_labels:
            raise ValueError('Invalid argument for input stereo pair.')
        fb = self._mixer_input_fbs[self._mixer_input_labels.index(pair)]
        return self._get_state(op, fb, ch)

    def set_mixer_output(self, op, ch, db):
        self._set_state(op, self._mixer_output_fb, ch, db)
    def get_mixer_output(self, op, ch):
        return self._get_state(op, self._mixer_output_fb, ch)

    _output_sources = {
        'analog-1/2': 2, 'digital-1/2': 3,
        'stream-1/2': 0, 'stream-3/4':  1, 'stream-5/6': 5,
        'mixer-1/2':  4,
    }
    _output_sink_fbs = (1, 2, 3)
    def get_output_sink_labels(self):
        return self._output_sink_labels
    def get_output_source_labels(self):
        return self._output_sources.keys()
    def set_output_source(self, output, source):
        if output not in self._output_sink_labels:
            raise ValueError('Invalid argument for output')
        if source not in self._output_sources:
            raise ValueError('Invalid argument for output source')
        fb = self._output_sink_fbs[self._output_sink_labels.index(output)]
        ch = self._output_sources[source]
        AvcAudio.set_selector_state(self.fcp, 0, 'current', fb, ch)
    def get_output_source(self, output):
        if output not in self._output_sink_labels:
            raise ValueError('Invalid argument for output')
        fb = self._output_sink_fbs[self._output_sink_labels.index(output)]
        idx = AvcAudio.get_selector_state(self.fcp, 0, 'current', fb)
        for name, value in self._output_sources.items():
            if value == idx:
                return name
        else:
            raise ValueError('Unexpected value for output source.')

    def check_digital_input_signal(self):
        # External input plug 1 is for S/PDIF in.
        return BcoVendorDependent.get_stream_detection(self.fcp,
                                                self.company_ids, 'input', 1)

    def get_clock_source_labels(self):
        return self.supported_clock_sources
    def set_clock_source(self, source):
        if self.supported_clock_sources.count(source) == 0:
            raise ValueError('Invalid argument for clock source')
        val = self.supported_clock_sources.index(source)
        AvcAudio.set_selector_state(self.fcp, 0, 'current', 4, val)
    def get_clock_source(self):
        state = AvcAudio.get_selector_state(self.fcp, 0, 'current', 4)
        return self.supported_clock_sources[state]

    def get_sampling_rate_labels(self):
        return self.supported_sampling_rates
    def set_sampling_rate(self, rate):
        AvcConnection.set_plug_signal_format(self.fcp, 'input', 0, rate)
        AvcConnection.set_plug_signal_format(self.fcp, 'output', 0, rate)
    def get_sampling_rate(self):
        return AvcConnection.get_plug_signal_format(self.fcp, 'output', 0)
