# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from pathlib import Path
from json import load, dump

from hinawa_utils.bebob.bebob_unit import BebobUnit
from hinawa_utils.bebob.extensions import BcoPlugInfo
from hinawa_utils.ta1394.general import AvcConnection
from hinawa_utils.ta1394.ccm import AvcCcm

from hinawa_utils.bebob.apogee_protocol import (
    HwCmd, DisplayCmd, OptIfaceCmd, MicCmd, InputCmd, OutputCmd, MixerCmd,
    RouteCmd, KnobCmd, SpdifResampleCmd
)

__all__ = ['ApogeeEnsembleUnit']


class ApogeeEnsembleUnit(BebobUnit):
    __CLOCK_SRCS = {
        'Coaxial':      AvcCcm.get_unit_signal_addr('external', 4),
        'Optical':      AvcCcm.get_unit_signal_addr('external', 5),
        'Word-clock':   AvcCcm.get_unit_signal_addr('external', 6),
    }

    def __init__(self, path):
        super().__init__(path)

        if (self.vendor_id, self.model_id) != (0x0003db, 0x01eeee):
            raise OSError('Not supported.')

        guid = self.get_property('guid')
        self.__path = Path('/tmp/hinawa-{0:08x}'.format(guid))

        if self.__path.exists() and self.__path.is_file():
            self.__load_cache()
        else:
            self.__create_cache()
            self.__set_from_cache()
            self.__save_cache()

    def __load_cache(self):
        with self.__path.open(mode='r') as f:
            self.__cache = load(f)

    def __save_cache(self):
        with self.__path.open(mode='w+') as f:
            dump(self.__cache, f)

    def __create_cache(self):
        cache = {}
        HwCmd.create_cache(cache)
        DisplayCmd.create_cache(cache)
        OptIfaceCmd.create_cache(cache)
        MicCmd.create_cache(cache)
        InputCmd.create_cache(cache)
        OutputCmd.create_cache(cache)
        MixerCmd.create_cache(cache)
        RouteCmd.create_cache(cache)
        SpdifResampleCmd.create_cache(cache)
        self.__cache = cache

    def __set_from_cache(self):
        val = HwCmd.get_cd_mode(self.__cache)
        HwCmd.set_cd_mode(self.__cache, self.fcp, val)
        val = HwCmd.get_16bit_mode(self.__cache)
        HwCmd.set_16bit_mode(self.__cache, self.fcp, val)

        val = DisplayCmd.get_illuminate(self.__cache)
        DisplayCmd.set_illuminate(self.__cache, self.fcp, val)
        val = DisplayCmd.get_mode(self.__cache)
        DisplayCmd.set_mode(self.__cache, self.fcp, val)
        val = DisplayCmd.get_target(self.__cache)
        DisplayCmd.set_target(self.__cache, self.fcp, val)
        val = DisplayCmd.get_overhold(self.__cache)
        DisplayCmd.set_overhold(self.__cache, self.fcp, val)

        for target in OptIfaceCmd.get_target_labels():
            val = OptIfaceCmd.get_mode(self.__cache, target)
            OptIfaceCmd.set_mode(self.__cache, self.fcp, target, val)

        for target in MicCmd.get_mic_labels():
            val = MicCmd.get_power(self.__cache, target)
            MicCmd.set_power(self.__cache, self.fcp, target, val)
            val = MicCmd.get_polarity(self.__cache, target)
            MicCmd.set_polarity(self.__cache, self.fcp, target, val)

        for target in InputCmd.get_in_labels():
            val = InputCmd.get_soft_limit(self.__cache, target)
            InputCmd.set_soft_limit(self.__cache, self.fcp, target, val)
            val = InputCmd.get_attr(self.__cache, target)
            InputCmd.set_attr(self.__cache, self.fcp, target, val)

        for target in OutputCmd.get_target_labels():
            val = OutputCmd.get_attr(self.__cache, target)
            OutputCmd.set_attr(self.__cache, self.fcp, target, val)

        for target in MixerCmd.get_target_labels():
            for src in MixerCmd.get_src_labels():
                vals = MixerCmd.get_src_gain(self.__cache, target, src)
                MixerCmd.set_src_gain(self.__cache, self.fcp, target, src,
                                      *vals)

        for target in RouteCmd.get_out_labels():
            src = RouteCmd.get_out_src(self.__cache, target)
            RouteCmd.set_out_src(self.__cache, self.fcp, target, src)
        for target in RouteCmd.get_cap_labels():
            src = RouteCmd.get_cap_src(self.__cache, target)
            RouteCmd.set_cap_src(self.__cache, self.fcp, target, src)
        for target in RouteCmd.get_hp_labels():
            src = RouteCmd.get_hp_src(self.__cache, target)
            RouteCmd.set_hp_src(self.__cache, self.fcp, target, src)

        params = SpdifResampleCmd.get_params(self.__cache)
        SpdifResampleCmd.set_params(self.__cache, self.fcp, *params)

    def __get_clock_plugs(self):
        plugs = {}
        info = AvcConnection.get_subunit_plug_info(self.fcp, 'music', 0)
        for direction in ('input', 'output'):
            for i in range(info[direction]):
                addr = BcoPlugInfo.get_subunit_addr(direction, 'music', 0, i)
                plug_type = BcoPlugInfo.get_plug_type(self.fcp, addr)
                if plug_type == 'Sync':
                    plugs[direction] = \
                        AvcCcm.get_subunit_signal_addr('music', 0, i)
                    break
            else:
                raise OSError('Unexpected state of device for clock source.')
        return plugs

    def get_clock_src_labels(self):
        labels = list(self.__CLOCK_SRCS.keys())
        labels.append('Internal')
        return labels

    def set_clock_src(self, src):
        if self.get_property('streaming'):
            raise OSError('Packet streaming started.')
        if src not in self.__CLOCK_SRCS and src != 'Internal':
            raise ValueError('Invalid argument for source of clock.')
        plugs = self.__get_clock_plugs()
        dst = plugs['input']
        if src == 'Internal':
            src = plugs['output']
        else:
            src = self.__CLOCK_SRCS[src]
        AvcCcm.set_signal_source(self.fcp, src, dst)

    def get_clock_src(self):
        plugs = self.__get_clock_plugs()
        dst = plugs['input']
        src = AvcCcm.get_signal_source(self.fcp, dst)
        addr = AvcCcm.parse_signal_addr(plugs['output'])
        if AvcCcm.compare_addrs(src, addr):
            return 'Internal'
        for name, addr in self.__CLOCK_SRCS.items():
            if AvcCcm.compare_addrs(src, AvcCcm.parse_signal_addr(addr)):
                return name
        raise OSError('Unexpected state of device.')

    def get_stream_mode_labels(self):
        return HwCmd.get_stream_mode_labels()

    def set_stream_mode(self, mode):
        HwCmd.set_stream_mode(mode)

    def get_stream_mode(self):
        sync_plug_ids = {
            5: '8x8',
            6: '10x10',
            7: '16x16',
        }
        plugs = self.__get_clock_plugs()
        addr = AvcCcm.parse_signal_addr(plugs['output'])
        plug_id = addr['data']['plug']
        if plug_id not in sync_plug_ids:
            raise OSError('Unexpected state of device.')
        return sync_plug_ids[plug_id]

    def reset_meters(self):
        DisplayCmd.reset_meter(self.fcp)

    def set_cd_mode(self, enable):
        if enable:
            if self.__cache['hw']['16bit'] != 'spdif-coax-out-1/2':
                raise ValueError('16bit-mode should be spdif-coax-out-1/2.')
            rate = AvcConnection.get_plug_signal_format(self.fcp, 'output', 0)
            if rate != 44100:
                raise ValueError('Sampling rate should be 44100.')
        HwCmd.set_cd_mode(self.__cache, self.fcp, enable)
        self.__save_cache()

    def get_cd_mode(self):
        return HwCmd.get_cd_mode(self.__cache)

    def get_16bit_mode_labels(self):
        return HwCmd.get_16bit_mode_labels()

    def set_16bit_mode(self, target):
        if target != 'none':
            rate = AvcConnection.get_plug_signal_format(self.fcp, 'output', 0)
            if rate not in (44100, 48000):
                raise ValueError('Sampling rate should be 44100 or 48000.')
        HwCmd.set_16bit_mode(self.__cache, self.fcp, target)
        self.__save_cache()

    def get_16bit_mode(self):
        return HwCmd.get_16bit_mode(self.__cache)

    # Hardware configurations.
    def set_display_mode(self, enable):
        DisplayCmd.set_mode(self.__cache, self.fcp, enable)
        self.__save_cache()

    def get_display_mode(self):
        return DisplayCmd.get_mode(self.__cache)

    def get_display_target_labels(self):
        return DisplayCmd.get_target_labels()

    def set_display_target(self, target):
        DisplayCmd.set_target(self.__cache, self.fcp, target)
        self.__save_cache()

    def get_display_target(self):
        return DisplayCmd.get_target(self.__cache)

    def set_display_illuminate(self, enable):
        DisplayCmd.set_illuminate(self.__cache, self.fcp, enable)
        self.__save_cache()

    def get_display_illuminate(self):
        return DisplayCmd.get_illuminate(self.__cache)

    def set_display_overhold(self, enable):
        DisplayCmd.set_overhold(self.__cache, self.fcp, enable)
        self.__save_cache()

    def get_display_overhold(self):
        return DisplayCmd.get_overhold(self.__cache)

    def get_opt_iface_target_labels(self):
        return OptIfaceCmd.get_target_labels()

    def get_opt_iface_mode_labels(self):
        return OptIfaceCmd.get_mode_labels()

    def set_opt_iface_mode(self, target, mode):
        OptIfaceCmd.set_mode(self.__cache, self.fcp, target, mode)
        self.__save_cache()

    def get_opt_iface_mode(self, target):
        return OptIfaceCmd.get_mode(self.__cache, target)

    # Knob configurations.
    def get_knob_out_labels(self):
        return KnobCmd.get_knob_out_labels()

    def set_knob_out_volume(self, target, db):
        KnobCmd.set_out_vol(self.fcp, target, db)

    def get_knob_states(self):
        return KnobCmd.get_states(self.fcp)

    # Microphone configurations.
    def get_mic_labels(self):
        return MicCmd.get_mic_labels()

    def set_polarity(self, target, invert):
        MicCmd.set_polarity(self.__cache, self.fcp, target, invert)
        self.__save_cache()

    def get_polarity(self, target):
        return MicCmd.get_polarity(self.__cache, target)

    def set_phantom_power(self, target, enable):
        MicCmd.set_power(self.__cache, self.fcp, target, enable)
        self.__save_cache()

    def get_phantom_power(self, target):
        return MicCmd.get_power(self.__cache, target)

    # Line input/output configurations.
    def get_line_in_labels(self):
        return InputCmd.get_in_labels()

    def set_soft_limit(self, target, enable):
        InputCmd.set_soft_limit(self.__cache, self.fcp, target, enable)
        self.__save_cache()

    def get_soft_limit(self, target):
        return InputCmd.get_soft_limit(self.__cache, target)

    def get_in_attr_labels(self):
        return InputCmd.get_attr_labels()

    def set_in_attr(self, target, attr):
        InputCmd.set_attr(self.__cache, self.fcp, target, attr)
        self.__save_cache()

    def get_in_attr(self, target):
        return InputCmd.get_attr(self.__cache, target)

    def get_line_out_labels(self):
        return OutputCmd.get_target_labels()

    def get_out_attr_labels(self):
        return OutputCmd.get_attr_labels()

    def set_out_attr(self, target, attr):
        OutputCmd.set_attr(self.__cache, self.fcp, target, attr)
        self.__save_cache()

    def get_out_attr(self, target):
        return OutputCmd.get_attr(self.__cache, target)

    # Route configurations.
    def get_out_labels(self):
        return RouteCmd.get_out_labels()

    def get_out_src_labels(self):
        return RouteCmd.get_out_src_labels()

    def set_out_src(self, target, src):
        RouteCmd.set_out_src(self.__cache, self.fcp, target, src)
        self.__save_cache()

    def get_out_src(self, target):
        return RouteCmd.get_out_src(self.__cache, target)

    def get_cap_labels(self):
        return RouteCmd.get_cap_labels()

    def get_cap_src_labels(self):
        return RouteCmd.get_cap_src_labels()

    def set_cap_src(self, target, src):
        RouteCmd.set_cap_src(self.__cache, self.fcp, target, src)
        self.__save_cache()

    def get_cap_src(self, target):
        return RouteCmd.get_cap_src(self.__cache, target)

    def get_hp_labels(self):
        return RouteCmd.get_hp_labels()

    def get_hp_src_labels(self):
        return RouteCmd.get_hp_src_labels()

    def set_hp_src(self, target, src):
        RouteCmd.set_hp_src(self.__cache, self.fcp, target, src)
        self.__save_cache()

    def get_hp_src(self, target):
        return RouteCmd.get_hp_src(self.__cache, target)

    # Internal multiplexer configuration.
    def get_mixer_labels(self):
        return MixerCmd.get_target_labels()

    def get_mixer_src_labels(self):
        return MixerCmd.get_src_labels()

    def set_mixer_src(self, target, src, db, balance):
        MixerCmd.set_src_gain(self.__cache, self.fcp, target, src, db, balance)
        self.__save_cache()

    def get_mixer_src(self, target, src):
        return MixerCmd.get_src_gain(self.__cache, target, src)

    # S/PDIF resampler configuration.
    def get_spdif_resample_iface_labels(self):
        return SpdifResampleCmd.get_iface_labels()

    def get_spdif_resample_direction_labels(self):
        return SpdifResampleCmd.get_direction_labels()

    def get_spdif_resample_rate_labels(self):
        return SpdifResampleCmd.get_rate_labels()

    def set_spdif_resample(self, enable, iface, direction, rate):
        SpdifResampleCmd.set_params(self.__cache, self.fcp, enable, iface,
                                    direction, rate)
        self.__save_cache()

    def get_spdif_resample(self):
        return SpdifResampleCmd.get_params(self.__cache)
