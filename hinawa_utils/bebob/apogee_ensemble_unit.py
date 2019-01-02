# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from pathlib import Path
from json import load, dump

from hinawa_utils.bebob.bebob_unit import BebobUnit
from hinawa_utils.bebob.extensions import BcoPlugInfo
from hinawa_utils.ta1394.general import AvcGeneral, AvcConnection
from hinawa_utils.ta1394.ccm import AvcCcm

from hinawa_utils.bebob.apogee_protocol import (
    HwCmd, DisplayCmd, OptIfaceCmd, MicCmd, InputCmd, OutputCmd, MixerCmd,
    RouteCmd, StatusCmd, KnobCmd, SpdifResampleCmd
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

        unit_info = AvcGeneral.get_unit_info(self.fcp)
        self.__company_ids = unit_info['company-id']

        guid = self.get_property('guid')
        self.__path = Path('/tmp/hinawa-{0:08x}'.format(guid))

        if self.__path.exists() and self.__path.is_file():
            self.__load_cache()
        else:
            self.__create_cache()
            self.__initialize()
            self.__save_cache()

    def __load_cache(self):
        with self.__path.open(mode='r') as f:
            self.__cache = load(f)

    def __save_cache(self):
        with self.__path.open(mode='w+') as f:
            dump(self.__cache, f)

    def __create_cache(self):
        cache = {}
        cache['hw'] = HwCmd.create_cache()
        cache['display'] = DisplayCmd.create_cache()
        cache['opt-iface'] = OptIfaceCmd.create_cache()
        cache['mic'] = MicCmd.create_cache()
        cache['input'] = InputCmd.create_cache()
        cache['output'] = OutputCmd.create_cache()
        cache['mixer'] = MixerCmd.create_cache()
        cache['route'] = RouteCmd.create_cache()
        cache['spdif-resample'] = SpdifResampleCmd.create_cache()
        self.__cache = cache

    def __initialize(self):
        states = self.__cache['hw']
        self.set_16bit_mode(states['16bit'])
        self.set_cd_mode(states['cd'])
        states = self.__cache['display']
        self.set_display_mode(states['mode'])
        self.set_display_target(states['target'])
        self.set_display_illuminate(states['illuminate'])
        self.set_display_overhold(states['overhold'])
        states = self.__cache['opt-iface']
        for target, val in states.items():
            self.set_opt_iface_mode(target, val)
        states = self.__cache['mic']
        for target, val in states['power'].items():
            self.set_phantom_power(target, val)
        for target, val in states['polarity'].items():
            self.set_polarity(target, val)
        states = self.__cache['input']
        for target, val in states['soft-limit'].items():
            self.set_soft_limit(target, val)
        for target, val in states['attr'].items():
            self.set_in_attr(target, val)
        states = self.__cache['output']
        for target, val in states['attr'].items():
            self.set_out_attr(target, val)
        states = self.__cache['mixer']
        for target, src_params in states.items():
            for src, params in src_params.items():
                db, balance = params
                self.set_mixer_src(target, src, db, balance)
        states = self.__cache['route']
        for target, src in states['out'].items():
            self.set_out_src(target, src)
        for target, src in states['cap'].items():
            self.set_cap_src(target, src)
        for target, src in states['hp'].items():
            self.set_hp_src(target, src)
        states = self.__cache['spdif-resample']
        self.set_spdif_resample(states['state'], states['iface'],
                                states['direction'], states['rate'])

    def __command_control(self, args):
        # At least, 6 bytes should be required to align to 3 quadlets.
        # Unless, target unit is freezed.
        if len(args) < 6:
            for i in range(6 - len(args)):
                args.append(0x00)
        resps = AvcGeneral.set_vendor_dependent(self.fcp, self.__company_ids,
                                                args)
        if resps[0] != args[0]:
            raise OSError('Unexpected value for vendor-dependent command.')
        return resps

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
        if AvcCcm.compare_addrs(src, AvcCcm.parse_signal_addr(plugs['output'])):
            return 'Internal'
        for name, addr in self.__CLOCK_SRCS.items():
            if AvcCcm.compare_addrs(src, AvcCcm.parse_signal_addr(addr)):
                return name
        raise OSError('Unexpected state of device.')

    def get_stream_mode_labels(self):
        return HwCmd.get_stream_mode_labels()
    def set_stream_mode(self, mode):
        args = HwCmd.build_stream_mode(mode)
        self.__command_control(args)
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
        args = HwCmd.build_meter_reset()
        self.__command_control(args)

    def set_cd_mode(self, enable):
        if enable:
            if self.__cache['hw']['16bit-mode'] != 'spdif-coax-out-1/2':
                raise ValueError('16bit-mode should be spdif-coax-out-1/2.')
            rate = AvcConnection.get_plug_signal_format(self.fcp, 'output', 0)
            if rate == 44100:
                raise ValueError('Sampling rate should be 44100.')
        args = HwCmd.build_cd_mode(enable)
        self.__command_control(args)
        self.__cache['hw']['cd'] = enable
        self.__save_cache()
    def get_cd_mode(self):
        return self.__cache['hw']['cd']

    def get_16bit_mode_labels(self):
        return HwCmd.get_16bit_mode_labels()
    def set_16bit_mode(self, target):
        if target != 'none':
            rate = AvcConnection.get_plug_signal_format(self.fcp, 'output', 0)
            if rate not in (44100, 48000):
                raise ValueError('Sampling rate should be 44100 or 48000.')
        args = HwCmd.build_16bit_mode(target)
        self.__command_control(args)
        self.__cache['hw']['16bit-mode'] = target
        self.__save_cache()
    def get_16bit_mode(self):
        return self.__cache['hw']['16bit-mode']

    # Hardware configurations.
    def set_display_mode(self, enable):
        args = DisplayCmd.build_mode(enable)
        self.__command_control(args)
        self.__cache['display']['mode'] = enable
        self.__save_cache()
    def get_display_mode(self):
        return self.__cache['display']['mode']

    def get_display_target_labels(self):
        return DisplayCmd.get_target_labels()
    def set_display_target(self, target):
        args = DisplayCmd.build_target(target)
        self.__command_control(args)
        self.__cache['display']['target'] = target
        self.__save_cache()
    def get_display_target(self):
        return self.__cache['display']['target']

    def set_display_illuminate(self, enable):
        args = DisplayCmd.build_illuminate(enable)
        self.__command_control(args)
        self.__cache['display']['illuminate'] = enable
        self.__save_cache()
    def get_display_illuminate(self):
        return self.__cache['display']['illuminate']

    def set_display_overhold(self, enable):
        args = DisplayCmd.build_overhold(enable)
        self.__command_control(args)
        self.__cache['display']['overhold'] = enable
        self.__save_cache()
    def get_display_overhold(self):
        return self.__cache['display']['overhold']

    def get_opt_iface_target_labels(self):
        return OptIfaceCmd.get_target_labels()
    def get_opt_iface_mode_labels(self):
        return OptIfaceCmd.get_mode_labels()
    def set_opt_iface_mode(self, target, mode):
        args = OptIfaceCmd.build_opt_iface(target, mode)
        self.__command_control(args)
        self.__cache['opt-iface'][target] = mode
        self.__save_cache()
    def get_opt_iface_mode(self, target):
        if target not in OptIfaceCmd.get_target_labels():
            raise ValueError('Invalid argument for optical iface.')
        return self.__cache['opt-iface'][target]

    # Knob configurations.
    def get_out_volume_labels(self):
        return KnobCmd.get_knob_labels()
    def set_out_volume(self, target, db):
        args = KnobCmd.build_vol(target, db)
        self.__command_control(args)
    def get_out_volume(self, target):
        if target not in KnobCmd.get_knob_labels():
            raise ValueError('Invalid argument for knob.')
        status = self.get_status()
        return status[target]

    # Microphone configurations.
    def get_mic_labels(self):
        return MicCmd.get_mic_labels()
    def set_polarity(self, target, invert):
        args = MicCmd.build_polarity(target, invert)
        self.__command_control(args)
        self.__cache['mic']['polarity'][target] = invert
        self.__save_cache()
    def get_polarity(self, target):
        if target not in MicCmd.get_mic_labels():
            raise ValueError('Invalid argument for mic.')
        return self.__cache['mic']['polarity'][target]

    def set_phantom_power(self, target, enable):
        args = MicCmd.build_power(target, enable)
        self.__command_control(args)
        self.__cache['mic']['power'][target] = enable
        self.__save_cache()
    def get_phantom_power(self, target):
        if target not in MicCmd.get_mic_labels():
            raise ValueError('Invalid argument for mic.')
        return self.__cache['mic']['power'][target]

    # Line input/output configurations.
    def get_line_in_labels(self):
        return InputCmd.get_in_labels()
    def set_soft_limit(self, target, enable):
        args = InputCmd.build_soft_limit(target, enable)
        self.__command_control(args)
        self.__cache['input']['soft-limit'][target] = enable
        self.__save_cache()
    def get_soft_limit(self, target):
        if target not in InputCmd.get_in_labels():
            raise ValueError('Invalid argument for input')
        return self.__cache['input']['soft-limit'][target]

    def get_in_attr_labels(self):
        return InputCmd.get_attr_labels()
    def set_in_attr(self, target, attr):
        args = InputCmd.build_attr(target, attr)
        self.__command_control(args)
        self.__cache['input']['attr'][target] = attr
        self.__save_cache()
    def get_in_attr(self, target):
        if target not in InputCmd.get_in_labels():
            raise ValueError('Invalid argument for input.')
        return self.__cache['input']['attr'][target]

    def get_line_out_labels(self):
        return OutputCmd.get_target_labels()
    def get_out_attr_labels(self):
        return OutputCmd.get_attr_labels()
    def set_out_attr(self, target, attr):
        if target not in OutputCmd.get_target_labels():
            raise ValueError('Invalid argument for output.')
        if attr not in OutputCmd.get_attr_labels():
            raise ValueError('Invalid argument for attenuation')
        args = OutputCmd.build_attr(target, attr)
        self.__command_control(args)
        self.__cache['output']['attr'][target] = attr
        self.__save_cache()
    def get_out_attr(self, target):
        if target not in OutputCmd.get_target_labels():
            raise ValueError('Invalid argument for output.')
        return self.__cache['output']['attr'][target]

    # Route configurations.
    def get_out_labels(self):
        return RouteCmd.get_out_labels()
    def get_out_src_labels(self):
        return RouteCmd.get_out_src_labels()
    def set_out_src(self, target, src):
        args = RouteCmd.build_out_src(target, src)
        self.__command_control(args)
        self.__cache['route']['out'][target] = src
        self.__save_cache()
    def get_out_src(self, target):
        if target not in RouteCmd.get_out_labels():
            raise ValueError('Invalid argument for output.')
        return self.__cache['route']['out'][target]

    def get_cap_labels(self):
        return RouteCmd.get_cap_labels()
    def get_cap_src_labels(self):
        return RouteCmd.get_cap_src_labels()
    def set_cap_src(self, target, src):
        args = RouteCmd.build_cap_src(target, src)
        self.__command_control(args)
        self.__cache['route']['cap'][target] = src
        self.__save_cache()
    def get_cap_src(self, target):
        if target not in RouteCmd.get_cap_labels():
            raise ValueError('Invalid argument for capture.')
        return self.__cache['route']['cap'][target]

    def get_hp_labels(self):
        return RouteCmd.get_hp_labels()
    def get_hp_src_labels(self):
        return RouteCmd.get_hp_src_labels()
    def set_hp_src(self, target, src):
        args = RouteCmd.build_hp_src(target, src)
        self.__command_control(args)
        self.__cache['route']['hp'][target] = src
        self.__save_cache()
    def get_hp_src(self, target):
        if target not in RouteCmd.get_hp_labels():
            raise ValueError('Invalid argument for headphone.')
        return self.__cache['route']['hp'][target]

    # Internal multiplexer configuration.
    def get_mixer_labels(self):
        return MixerCmd.get_target_labels()
    def get_mixer_src_labels(self):
        return MixerCmd.get_mixer_src_labels()
    def set_mixer_src(self, target, src, db, balance):
        cache = self.__cache['mixer']
        args = MixerCmd.build_src_gain(cache, target, src, db, balance)
        self.__command_control(args)
        self.__cache['mixer'][target][src] = [db, balance]
        self.__save_cache()
    def get_mixer_src(self, target, src):
        return self.__cache['mixer'][target][src]

    def get_status(self):
        args = StatusCmd.build_status()
        params = self.__command_control(args)
        return StatusCmd.parse_params(params)

    # S/PDIF resampler configuration.
    def get_spdif_resample_iface_labels(self):
        return SpdifResampleCmd.get_iface_labels()
    def get_spdif_resample_direction_labels(self):
        return SpdifResampleCmd.get_direction_labels()
    def get_spdif_resample_rate_labels(self):
        return SpdifResampleCmd.get_rate_labels()
    def set_spdif_resample(self, enable, iface, direction, rate):
        args = SpdifResampleCmd.build_args(enable, iface, direction, rate)
        self.__command_control(args)
        self.__cache['spdif-resample']['state'] = enable
        self.__cache['spdif-resample']['iface'] = iface
        self.__cache['spdif-resample']['direction'] = direction
        self.__cache['spdif-resample']['rate'] = rate
        self.__save_cache()
    def get_spdif_resample(self):
        return self.__cache['spdif-resample']
