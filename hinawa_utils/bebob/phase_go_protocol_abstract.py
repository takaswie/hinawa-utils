# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from abc import ABCMeta

from hinawa_utils.ta1394.general import AvcGeneral
from hinawa_utils.ta1394.general import AvcConnection
from hinawa_utils.ta1394.audio import AvcAudio

from hinawa_utils.bebob.extensions import BcoVendorDependent
from hinawa_utils.bebob.extensions import BcoPlugInfo
from hinawa_utils.bebob.extensions import BcoStreamFormatInfo

__all__ = ['PhaseGoProtocolAbstract']

class PhaseGoProtocolAbstract(metaclass=ABCMeta):
    __MIXER_INPUTS = {
        'analog-1/2':   6,
        'digital-1/2':  7,
        'stream-1/2':   3,
        'stream-3/4':   4,
        'stream-5/6':   5,
    }
    __OUTPUT_SOURCES = {
        'analog-1/2':   2,
        'digital-1/2':  3,
        'stream-1/2':   0,
        'stream-3/4':   1,
        'stream-5/6':   5,
        'mixer-1/2':    4,
    }
    __SUPPORTED_CLOCK_SOURCES = ('Internal', 'S/PDIF')
    __SUPPORTED_SAMPLING_RATES = (32000, 44100, 48000, 88200, 96000, 192000)

    def __init__(self, fcp, mixer_output_fb, output_labels):
        unit_info = AvcGeneral.get_unit_info(fcp)
        self.fcp = fcp
        self.__company_ids = unit_info['company-id']
        self.__mixer_output_fb = mixer_output_fb
        self.__output_labels = output_labels

    # For mixer inputs.
    def get_mixer_input_labels(self):
        return self.__MIXER_INPUTS
    def __check_mixer_input_channel(self, target, ch):
        if target not in self.__MIXER_INPUTS:
            raise ValueError('Invalid argument for stereo pair')
        if ch not in (1, 2):
            raise ValueError('Invalid argument for channel number')
        return self.__MIXER_INPUTS[target], ch
    def set_mixer_input_volume(self, target, ch, db):
        fb, ch = self.__check_mixer_input_channel(target, ch)
        data = AvcAudio.build_data_from_db(db)
        AvcAudio.set_feature_volume_state(self.fcp, 0, 'current', fb, ch, data)
    def get_mixer_input_volume(self, target, ch):
        fb, ch = self.__check_mixer_input_channel(target, ch)
        data = AvcAudio.get_feature_volume_state(self.fcp, 0, 'current', fb, ch)
        return AvcAudio.parse_data_to_db(data)
    def set_mixer_input_mute(self, target, ch, enable):
        fb, ch = self.__check_mixer_input_channel(target, ch)
        AvcAudio.set_feature_mute_state(self.fcp, 0, 'current', fb, ch, enable)
    def get_mixer_input_mute(self, target, ch):
        fb, ch = self.__check_mixer_input_channel(target, ch)
        return AvcAudio.get_feature_mute_state(self.fcp, 0, 'current', fb, ch)

    # For mixer output.
    def __check_mixer_output_channel(self, ch):
        if ch not in (1, 2):
            raise ValueError('Invalid argument for channel number')
        return self.__mixer_output_fb, ch
    def set_mixer_output_volume(self, ch, db):
        fb, ch = self.__check_mixer_output_channel(ch)
        data = AvcAudio.build_data_from_db(db)
        AvcAudio.set_feature_volume_state(self.fcp, 0, 'current', fb, ch, data)
    def get_mixer_output_volume(self, ch):
        fb, ch = self.__check_mixer_output_channel(ch)
        data = AvcAudio.get_feature_volume_state(self.fcp, 0, 'current', fb, ch)
        return AvcAudio.parse_data_to_db(data)
    def set_mixer_output_mute(self, ch, enable):
        fb, ch = self.__check_mixer_output_channel(ch)
        AvcAudio.set_feature_mute_state(self.fcp, 0, 'current', fb, ch, enable)
    def get_mixer_output_mute(self, ch):
        fb, ch = self.__check_mixer_output_channel(ch)
        return AvcAudio.get_feature_mute_state(self.fcp, 0, 'current', fb, ch)

    # For output sources.
    def get_output_labels(self):
        return list(self.__output_labels.keys())
    def get_output_source_labels(self):
        return list(self.__OUTPUT_SOURCES.keys())
    def set_output_source(self, target, source):
        if target not in self.__output_labels:
            raise ValueError('Invalid argumetn for output')
        if source not in self.__OUTPUT_SOURCES:
            raise ValueError('Invalid argumetn for output source')
        fb = self.__output_labels[target]
        ch = self.__OUTPUT_SOURCES[source]
        AvcAudio.set_selector_state(self.fcp, 0, 'current', fb, ch)
    def get_output_source(self, target):
        if target not in self.__output_labels:
            raise ValueError('Invalid argumetn for output')
        fb = self.__output_labels[target]
        idx = AvcAudio.get_selector_state(self.fcp, 0, 'current', fb)
        for key, val in self.__OUTPUT_SOURCES.items():
            if val == idx:
                return key
        else:
            raise ValueError('Unexpected value for output source.')

    def get_stream_formats(self):
        fmts = {}
        addr = BcoPlugInfo.get_unit_addr('output', 'isoc', 0)
        fmts['capture'] = BcoStreamFormatInfo.get_entry_list(self.fcp, addr)
        addr = BcoPlugInfo.get_unit_addr('input', 'isoc', 0)
        fmts['playback'] = BcoStreamFormatInfo.get_entry_list(self.fcp, addr)
        return fmts

    def check_digital_input_signal(self):
        # External input plug 1 is for S/PDIF in.
        return BcoVendorDependent.get_stream_detection(self.fcp,
                                                self.__company_ids, 'input', 1)

    def get_clock_source_labels(self):
        return self.__SUPPORTED_CLOCK_SOURCES
    def set_clock_source(self, source):
        if source not in self.__SUPPORTED_CLOCK_SOURCES:
            raise ValueError('Invalid argument for clock source')
        val = self.__SUPPORTED_CLOCK_SOURCES.index(source)
        AvcAudio.set_selector_state(self.fcp, 0, 'current', 4, val)
    def get_clock_source(self):
        state = AvcAudio.get_selector_state(self.fcp, 0, 'current', 4)
        return self.__SUPPORTED_CLOCK_SOURCES[state]

    def get_sampling_rate_labels(self):
        return self.__SUPPORTED_SAMPLING_RATES
    def set_sampling_rate(self, rate):
        if rate not in self.__SUPPORTED_SAMPLING_RATES:
            raise ValueError('Invalid argument for sampling rate')
        AvcConnection.set_plug_signal_format(self.fcp, 'input', 0, rate)
        AvcConnection.set_plug_signal_format(self.fcp, 'output', 0, rate)
    def get_sampling_rate(self):
        return AvcConnection.get_plug_signal_format(self.fcp, 'output', 0)
