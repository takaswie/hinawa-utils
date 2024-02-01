# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from threading import Thread

import gi
gi.require_version('GLib', '2.0')
gi.require_version('Hinawa', '4.0')
gi.require_version('Hitaki', '0.0')
from gi.repository import GLib, Hinawa, Hitaki

from hinawa_utils.efw.transactions import EftInfo
from hinawa_utils.efw.transactions import EftHwctl
from hinawa_utils.efw.transactions import EftPhysOutput
from hinawa_utils.efw.transactions import EftPhysInput
from hinawa_utils.efw.transactions import EftPlayback
from hinawa_utils.efw.transactions import EftMonitor
from hinawa_utils.efw.transactions import EftIoconf
from math import log10

__all__ = ['EfwUnit']


class EfwUnit(Hitaki.SndEfw):
    def __init__(self, path):
        super().__init__()
        self.open(path, 0)

        ctx = GLib.MainContext.new()
        _, src = self.create_source()
        src.attach(ctx)
        self.__unit_dispatcher = GLib.MainLoop.new(ctx, False)
        self.__unit_th = Thread(target=lambda d: d.run(), args=(self.__unit_dispatcher, ))
        self.__unit_th.start()

        fw_node_path = '/dev/{}'.format(self.get_property('node-device'))
        self.__node = Hinawa.FwNode.new()
        self.__node.open(fw_node_path, 0)
        ctx = GLib.MainContext.new()
        _, src = self.__node.create_source()
        src.attach(ctx)
        self.__node_dispatcher = GLib.MainLoop.new(ctx, False)
        self.__node_th = Thread(target=lambda d: d.run(), args=(self.__node_dispatcher, ))
        self.__node_th.start()

        self.info = EftInfo.get_spec(self)
        self._fixup_info()

    def release(self):
        self.__unit_dispatcher.quit()
        self.__node_dispatcher.quit()
        self.__unit_th.join()
        self.__node_th.join()

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.release()

    def get_node(self):
        return self.__node

    def _fixup_info(self):
        # Mapping for channels on tx stream is supported by Onyx1200F only.
        if self.info['model'] == 'Onyx1200F':
            self.info['features']['tx-mapping'] = True
        else:
            self.info['features']['tx-mapping'] = False

        # S/PDIF on coaxial interfae is available in Onyx400F.
        if self.info['model'] == 'Onyx400F':
            self.info['features']['spdif-coax'] = True

        # Nominal level of input/output is always supported by AudioFire series.
        if self.info['model'].find('Audiofire') == 0:
            self.info['features']['nominal-input'] = True
            self.info['features']['nominal-output'] = True

    @staticmethod
    def _calcurate_vol_from_db(db):
        if db <= -144.0:
            return 0x00000000
        else:
            return int(0x01000000 * pow(10, db / 20))

    @staticmethod
    def _calcurate_vol_to_db(vol):
        if vol == 0:
            return -144.0
        else:
            return 20 * log10(vol / 0x01000000)

    def get_metering(self):
        return EftInfo.get_metering(self)

    def set_clock_state(self, rate, src):
        EftHwctl.set_clock(self, rate, src, 0)

    def get_clock_state(self):
        return EftHwctl.get_clock(self)

    def get_box_state_labels(self, name):
        if name not in EftHwctl.SUPPORTED_BOX_STATES:
            raise ValueError('Invalid argument for name of box state')
        return EftHwctl.SUPPORTED_BOX_STATES[name]

    def set_box_states(self, name, state):
        states = EftHwctl.get_box_states(self)
        states[name] = state
        EftHwctl.set_box_states(self, states)

    def get_box_states(self):
        states = {}
        state_all = EftHwctl.get_box_states(self)
        if self.info['features']['spdif-coax'] or \
           self.info['features']['spdif-opt']:
            states['spdif-pro'] = state_all['spdif-pro']
            states['spdif-non-audio'] = state_all['spdif-non-audio']
        if self.info['model'] == 'Onyx1200F':
            states['control-room'] = state_all['control-room']
            states['output-level-bypass'] = state_all['output-level-bypass']
            states['metering-mode-in'] = state_all['metering-mode-in']
            states['metering-mode-out'] = state_all['metering-mode-out']
        if self.info['features']['soft-clip']:
            states['soft-clip'] = state_all['soft-clip']
        if self.info['features']['robot-hex-input']:
            states['robot-hex-input'] = state_all['robot-hex-input']
        if self.info['features']['robot-battery-charge']:
            states['robot-battery-charge'] = state_all['robot-battery-charge']
        states['internal-multiplexer'] = state_all['internal-multiplexer']
        return states

    def set_phys_out_gain(self, ch, db):
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        vol = self._calcurate_vol_from_db(db)
        EftPhysOutput.set_param(self, 'gain', ch, vol)

    def get_phys_out_gain(self, ch):
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        vol = EftPhysOutput.get_param(self, 'gain', ch)
        return self._calcurate_vol_to_db(vol)

    def set_phys_out_mute(self, ch, val):
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        EftPhysOutput.set_param(self, 'mute', ch, val)

    def get_phys_out_mute(self, ch):
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        return EftPhysOutput.get_param(self, 'mute', ch)

    def set_phys_out_nominal(self, ch, val):
        if not self.info['features']['nominal-output']:
            raise RuntimeError('Not supported by this model')
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        EftPhysOutput.set_param(self, 'nominal', ch, val)

    def get_phys_out_nominal(self, ch):
        if not self.info['features']['nominal-output']:
            raise RuntimeError('Not supported by this model')
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        return EftPhysOutput.get_param(self, 'nominal', ch)

    def set_phys_in_nominal(self, ch, val):
        if not self.info['features']['nominal-input']:
            raise RuntimeError('Not supported by this model')
        if ch >= len(self.info['phys-inputs']):
            raise ValueError('Invalid argument for physical input channel')
        EftPhysInput.set_param(self, 'nominal', ch, val)

    def get_phys_in_nominal(self, ch):
        if not self.info['features']['nominal-input']:
            raise RuntimeError('Not supported by this model')
        if ch >= len(self.info['phys-inputs']):
            raise ValueError('Invalid argument for physical input channel')
        return EftPhysInput.get_param(self, 'nominal', ch)

    def set_playback_gain(self, ch, db):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        vol = self._calcurate_vol_from_db(db)
        EftPlayback.set_param(self, 'gain', ch, vol)

    def get_playback_gain(self, ch):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        vol = EftPlayback.get_param(self, 'gain', ch)
        return self._calcurate_vol_to_db(vol)

    def set_playback_mute(self, ch, val):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftPlayback.set_param(self, 'mute', ch, val)

    def get_playback_mute(self, ch):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftPlayback.get_param(self, 'mute', ch)

    def set_playback_solo(self, ch, val):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftPlayback.set_param(self, 'solo', ch, val)

    def get_playback_solo(self, ch):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftPlayback.get_param(self, 'solo', ch)

    def set_monitor_gain(self, in_ch, out_ch, db):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        vol = self._calcurate_vol_from_db(db)
        EftMonitor.set_param(self, 'gain', in_ch, out_ch, vol)

    def get_monitor_gain(self, in_ch, out_ch):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        vol = EftMonitor.get_param(self, 'gain', in_ch, out_ch)
        return self._calcurate_vol_to_db(vol)

    def set_monitor_mute(self, in_ch, out_ch, val):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftMonitor.set_param(self, 'mute', in_ch, out_ch, val)

    def get_monitor_mute(self, in_ch, out_ch):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftMonitor.get_param(self, 'mute', in_ch, out_ch)

    def set_monitor_solo(self, in_ch, out_ch, val):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftMonitor.set_param(self, 'solo', in_ch, out_ch, val)

    def get_monitor_solo(self, in_ch, out_ch):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftMonitor.get_param(self, 'solo', in_ch, out_ch)

    def set_monitor_pan(self, in_ch, out_ch, val):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftMonitor.set_param(self, 'pan', in_ch, out_ch, val)

    def get_monitor_pan(self, in_ch, out_ch):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftMonitor.get_param(self, 'pan', in_ch, out_ch)

    def get_control_room_source_labels(self):
        labels = []
        for i in range(1, self.info['playback-channels'], 2):
            labels.append('mixer-{0}/{1}'.format(i, i + 1))
        return labels

    def set_control_room_mirroring(self, source):
        if not self.info['features']['control-room-mirroring']:
            raise RuntimeError('Not supported by this model')
        labels = self.get_control_room_source_labels()
        if source not in labels:
            raise ValueError('Invalid argument for source')
        val = labels.index(source) * 2
        EftIoconf.set_control_room_mirroring(self, val)

    def get_control_room_mirroring(self):
        if not self.info['features']['control-room-mirroring']:
            raise RuntimeError('Not supported by this model')
        val = EftIoconf.get_control_room_mirroring(self)
        labels = self.get_control_room_source_labels()
        return labels[val // 2]

    def get_digital_input_mode_labels(self):
        labels = []
        for mode in EftIoconf.DIGITAL_INPUT_MODES:
            if mode in self.info['features'] and self.info['features'][mode]:
                labels.append(mode)
        return labels

    def set_digital_input_mode(self, mode):
        if not self.info['features'][mode]:
            raise RuntimeError('Not supported by this model')
        EftIoconf.set_digital_input_mode(self, mode)

    def get_digital_input_mode(self):
        return EftIoconf.get_digital_input_mode(self)

    def set_phantom_powering(self, state):
        if not self.info['features']['phantom-powering']:
            raise RuntimeError('Not supported by this model')
        EftIoconf.set_phantom_powering(self, state)

    def get_phantom_powering(self):
        if not self.info['features']['phantom-powering']:
            raise RuntimeError('Not supported by this model')
        return EftIoconf.get_phantom_powering(self)

    def set_stream_mapping(self, rx_maps, tx_maps):
        if not rx_maps and self.info['features']['rx-mapping']:
            raise RuntimeError('Not supported by this model')
        if not tx_maps and self.info['features']['tx-mapping']:
            raise RuntimeError('Not supported by this model')
        EftIoconf.set_stream_mapping(self, rx_maps, tx_maps)

    def get_stream_mapping(self):
        if not self.info['features']['rx-mapping'] and \
           not self.info['features']['tx-mapping']:
            raise RuntimeError('Not supported by this model')
        return EftIoconf.get_stream_mapping(self)
