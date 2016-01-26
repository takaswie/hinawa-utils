import re

from bebob.bebob_unit import BebobUnit

from ta1394.general import AvcGeneral
from ta1394.general import AvcConnection
from ta1394.audio import AvcAudio

from bebob.extensions import BcoVendorDependent
from bebob.extensions import BcoPlugInfo
from bebob.extensions import BcoStreamFormatInfo

class YamahaGo(BebobUnit):
    channel_modes = ('volume', 'mute')
    supported_clock_sources = ('Internal', 'S/PDIF')
    supported_sampling_rates = (32000, 44100, 48000, 88200, 96000, 192000)
    supported_mixer_inputs = (
        'analog-in-1/2', 'analog-in-3/4', 'digital-in-1/2',
        'stream-in-1/2', 'stream-in-3/4', 'stream-in-5/6')
    supported_outputs = ('analog-out-1/2', 'analog-out-3/4', 'digital-out-1/2')

    _mixer_inputs = (
        {'Analog-1/2':  6, 'Digital-1/2': 7,
         'Stream-1/2':  3, 'Stream-3/4':  4, 'Stream-5/6': 5},
        {'Analog-1/2':  6, 'Digital-1/2': 7,
         'Stream-1/2':  3, 'Stream-3/4':  4, 'Stream-5/6': 5},
    )
    _mixer_output = (1, 2)

    _outputs = (
        {},
        {'Analog-1/2': 1, 'Analog-3/4': 8}
    )

    def __init__(self, path):
        super().__init__(path)
        unit_info = AvcGeneral.get_unit_info(self.fcp)
        self.company_ids = unit_info['company-id']

    def get_stream_formats(self):
        fmts = dict.fromkeys(('capture', 'playback'), [])
        addr = BcoPlugInfo.get_unit_addr('output', 'isoc', 0)
        fmts['capture'] = BcoStreamFormatInfo.get_entry_list(self.fcp, addr)
        addr = BcoPlugInfo.get_unit_addr('input', 'isoc', 0)
        fmts['playback'] = BcoStreamFormatInfo.get_entry_list(self.fcp, addr)
        return fmts

    def _set_state(self, mode, fb, ch, value):
        if mode == 'volume':
            AvcAudio.set_feature_volume_state(self.fcp, 0, 'current',
                                              fb, ch, value)
        elif mode == 'mute':

            AvcAudio.set_feature_mute_state(self.fcp, 0, 'current',
                                            fb, ch, value)
        else:
            raise ValueError('Invalid argument for channel mode')
    def _get_state(self, mode, fb, ch):
        if mode == 'volume':
            return AvcAudio.get_feature_volume_state(self.fcp, 0, 'current',
                                                     fb, ch)
        elif mode == 'mute':
            return AvcAudio.get_feature_mute_state(self.fcp, 0, 'current',
                                                   fb, ch)
        else:
            raise ValueError('Invalid argument for channel mode')

    def get_output_labels(self):
        return self.supported_outputs
    def set_output(self, mode, pair, left, val):
        if self.supported_outputs.count(pair) == 0:
            raise ValueError('Invalid argument for channel name')
        if not re.match('^analog', pair):
            raise ValueError('Invalid argument for analog pair')
        if left > 1:
            raise ValueError('Invalid argument for stereo position')
        ch = self.supported_outputs.index(pair) * 2 + left + 1
        self._set_state(mode, 1, ch, val)
    def get_output(self, mode, pair, left):
        if self.supported_outputs.count(pair) == 0:
            raise ValueError('Invalid argument for channel name')
        if not re.match('^analog', pair):
            raise ValueError('Invalid argument for analog pair')
        if left > 1:
            raise ValueError('Invalid argument for stereo position')
        if mode not in self.channel_modes:
            raise ValueError('Invalid argument for channel mode')
        ch = self.supported_outputs.index(pair) * 2 + left + 1
        return self._get_state(mode, 1, ch)

    def _calculate_fb_params(self, pair, left):
        if self.supported_mixer_inputs.count(pair) == 0:
            raise ValueError('Invalid argument for channel name')
        if left > 1:
            raise ValueError('Invalid argument for stereo position')
        index = self.supported_mixer_inputs.index(pair)
        if index < 2:
            fb = 6
            ch = index + left + 1
        elif index == 2:
            fb = 7
            ch = left + 1
        else:
            fb = index
            ch = left + 1
        return (fb, ch)

    def get_mixer_input_labels(self):
        return self.supported_mixer_inputs
    def set_mixer_input(self, mode, pair, left, val):
        fb,ch = self._calculate_fb_params(pair, left)
        self._set_state(mode, fb, ch, val)
    def get_mixer_input(self, mode, pair, left):
        fb, ch = self._calculate_fb_params(pair, left)
        return self._get_state(mode, fb, ch)

    def set_mixer_output(self, mode, left, value):
        if mode not in self.channel_modes:
            raise ValueError('Invalid argument for channel mode')
        if left > 1:
            raise ValueError('Invalid argument for stereo position')
        ch = left + 1
        self._set_state(mode, 2, ch, value)
    def get_mixer_output(self, mode, left):
        if mode not in self.channel_modes:
            raise ValueError('Invalid argument for channel mode')
        if left > 1:
            raise ValueError('Invalid argument for stereo position')
        ch = left + 1
        return self._get_state(mode, 2, ch)

    _output_sources = {
        'Analog-1/2': 2, 'Digital-1/2': 3, 'Mixer-1/2':  4,
        'Stream-1/2': 0, 'Stream-3/4':  1, 'Stream-5/6': 5}
    _output_sinks = {
    }
    def get_output_source_labels(self):
        return self._output_sources
    def set_output_source(self, output, source):
        if self._output_sources.count(source) == 0:
            raise ValueError('Invalid argument for output source pair')
        if self.supported_outputs.count(output) == 0:
            raise ValueError('Invalid argument for output channel pair')
        fb = self.supported_outputs.index(output) + 1
        src = self._output_sources.index(source)
        AvcAudio.set_selector_state(self.fcp, 0, 'current', fb, src)
    def get_output_source(self, output):
        if self.supported_outputs.count(output) == 0:
            raise ValueError('Invalid argument for output channel pair')
        num = self.supported_outputs.index(output) + 1
        idx = AvcAudio.get_selector_state(self.fcp, 0, 'current', num)
        return self._output_sources[idx]

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
        AvcConnection.set_plug_signal_format(self.fcp, 'input', rate)
        AvcConnection.set_plug_signal_format(self.fcp, 'output', rate)
    def get_sampling_rate(self):
        return AvcConnection.get_plug_signal_format(self.fcp, 'output', 0)
