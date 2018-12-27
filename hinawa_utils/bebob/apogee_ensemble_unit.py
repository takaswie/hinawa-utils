# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from struct import unpack, pack
from pathlib import Path
from json import load, dump
from enum import Enum

from hinawa_utils.bebob.bebob_unit import BebobUnit
from hinawa_utils.bebob.extensions import BcoPlugInfo

from hinawa_utils.ta1394.general import AvcGeneral, AvcConnection 
from hinawa_utils.ta1394.ccm import AvcCcm

__all__ = ['ApogeeEnsembleUnit']

class VendorCmd(Enum):
    INPUT_LIMIT     = 0xe4
    MIC_POWER       = 0xe5
    IO_ATTENUATION  = 0xe8
    IO_ROUTING      = 0xef
    HW_CONFIG       = 0xeb
    HP_SRC          = 0xab
    MIXER_SRC1      = 0xb0
    MIXER_SRC2      = 0xb1
    MIXER_SRC3      = 0xb2
    MIXER_SRC4      = 0xb3
    OPTICAL_MODE    = 0xf1
    MIC_POLARITY    = 0xf5
    OUT_VOL         = 0xf6
    HW_STATUS       = 0xff

class MonitorLabels(Enum):
    MAIN    = 'main'
    HP1     = 'hp-1'
    HP2     = 'hp-2'

class MicInputLabels(Enum):
    MIC1    = 'mic-1'
    MIC2    = 'mic-2'
    MIC3    = 'mic-3'
    MIC4    = 'mic-4'

class ApogeeEnsembleUnit(BebobUnit):
    # Apogee Ensemble implements no command to return current status.
    # This module save current status into a temporary file.
    __CACHE_LAYOUT = {
        'display': {
            'mode': ( (0, 1), ),
            'target': ( ('output', 'input'), ),
            'overhold': ( (0, 1), ),
            'illuminate':   ( (0, 1), ),
        },
        'input': {
            'mic-polarity': (
                ('mic-1', 'mic-2', 'mic-3', 'mic-4'),
                (0, 1),
            ),
            'mic-power': (
                ('mic-1', 'mic-2', 'mic-3', 'mic-4'),
                (0, 1),
            ),
            'soft-limit': (
                ('analog-1', 'analog-2', 'analog-3', 'analog-4',
                 'analog-5', 'analog-6', 'analog-7', 'analog-8'),
                (0, 1),
            ),
            'attr': (
                ('analog-1', 'analog-2', 'analog-3', 'analog-4',
                 'analog-5', 'analog-6', 'analog-7', 'analog-8'),
                ('-10dB', '+4dB'),
            ),
            'opt-iface': (
                ('S/PDIF', 'ADAT/SMUX'),
            )
        },
        'output': {
            'attr': (
                ('analog-1', 'analog-2', 'analog-3', 'analog-4',
                 'analog-5', 'analog-6', 'analog-7', 'analog-8'),
                ('-10dB', '+4dB'),
            ),
            'opt-iface': (
                ('S/PDIF', 'ADAT/SMUX'),
            )
        },
        'mixer': {
            'src': (
                ('mixer-1/2', 'mixer-3/4'),
                ('analog-1', 'analog-2', 'analog-3', 'analog-4',
                 'analog-5', 'analog-6', 'analog-7', 'analog-8',
                 'spdif-1', 'spdif-2',
                 'adat-1', 'adat-2', 'adat-3', 'adat-4',
                 'adat-5', 'adat-6', 'adat-7', 'adat-8'),
                float,
                float,
            )
        },
        'route': {
            'out-src': (
                ('analog-1', 'analog-2', 'analog-3', 'analog-4',
                 'analog-5', 'analog-6', 'analog-7', 'analog-8',
                 'spdif-1', 'spdif-2',
                 'adat-1', 'adat-2', 'adat-3', 'adat-4',
                 'adat-5', 'adat-6', 'adat-7', 'adat-8'),
                ('stream-1', 'stream-2', 'stream-3', 'stream-4',
                 'stream-5', 'stream-6', 'stream-7', 'stream-8',
                 'stream-9', 'stream-10', 'stream-11', 'stream-12',
                 'stream-13', 'stream-14', 'stream-15', 'stream-16',
                 'stream-17', 'stream-18',
                 'analog-1', 'analog-2', 'analog-3', 'analog-4',
                 'analog-5', 'analog-6', 'analog-7', 'analog-8',
                 'spdif-1', 'spdif-2',
                 'adat-1', 'adat-2', 'adat-3', 'adat-4',
                 'adat-5', 'adat-6', 'adat-7', 'adat-8',
                 'mixer-1', 'mixer-2', 'mixer-3', 'mixer-4'),
            ),
            'cap-src': (
                ('stream-1', 'stream-2', 'stream-3', 'stream-4',
                 'stream-5', 'stream-6', 'stream-7', 'stream-8',
                 'stream-9', 'stream-10', 'stream-11', 'stream-12',
                 'stream-13', 'stream-14', 'stream-15', 'stream-16',
                 'stream-17', 'stream-18'),
                ('analog-1', 'analog-2', 'analog-3', 'analog-4',
                 'analog-5', 'analog-6', 'analog-7', 'analog-8',
                 'spdif-1', 'spdif-2',
                 'adat-1', 'adat-2', 'adat-3', 'adat-4',
                 'adat-5', 'adat-6', 'adat-7', 'adat-8'),
            ),
            'hp-src': (
                ('hp-1', 'hp-2'),
                ('analog-1/2', 'analog-3/4', 'analog-5/6', 'analog-7/8',
                 'spdif-1/2', 'none'),
            ),
        },
        'knob': {
            'main-assign': (
                ('analog-1/2', 'analog-1/2/3/4', 'analog-1/2/3/4/5/6/7/8',
                 'none'),
            ),
        },
        'downgrade': {
            'target': (
                ('analog-in-1/2', 'analog-in-3/4',
                 'analog-in-5/6', 'analog-in-7/8',
                 'spdif-opt-in-1/2','spdif-coax-in-1/2',
                 'spdif-opt-out-1/2', 'spdif-coax-out-1/2'),
            ),
        },
        'spdif-resample': {
            'target': (
                ('coax-in-1/2', 'opt-in-1/2', 'coax-out-1/2', 'opt-out-1/2'),
            ),
            'rate': (
                (44100, 48000, 88200, 96000, 176400, 192000),
            ),
        },
    }

    __CLOCK_SRCS = {
        'Coaxial':      AvcCcm.get_unit_signal_addr('external', 4),
        'Optical':      AvcCcm.get_unit_signal_addr('external', 5),
        'Word-clock':   AvcCcm.get_unit_signal_addr('external', 6),
    }

    __STREAM_MODE_LABELS = {
        '16x16':    0x00,
        '10x10':    0x01,
        '8x8':      0x02,
    }

    __OUT_LABELS = {
        'analog-1': 0x00,
        'analog-2': 0x01,
        'analog-3': 0x02,
        'analog-4': 0x03,
        'analog-5': 0x04,
        'analog-6': 0x05,
        'analog-7': 0x06,
        'analog-8': 0x07,
        'spdif-1':  0x1a,
        'spdif-2':  0x1b,
        'adat-1':   0x1c,
        'adat-2':   0x1d,
        'adat-3':   0x1e,
        'adat-4':   0x1f,
        'adat-5':   0x20,
        'adat-6':   0x21,
        'adat-7':   0x22,
        'adat-8':   0x23,
    }

    __PORT_LABELS = {
        # From external interfaces.
        'analog-1':     0x00,
        'analog-2':     0x01,
        'analog-3':     0x02,
        'analog-4':     0x03,
        'analog-5':     0x04,
        'analog-6':     0x05,
        'analog-7':     0x06,
        'analog-8':     0x07,
        # From host computer.
        'stream-1':     0x08,
        'stream-2':     0x09,
        'stream-3':     0x0a,
        'stream-4':     0x0b,
        'stream-5':     0x0c,
        'stream-6':     0x0d,
        'stream-7':     0x0e,
        'stream-8':     0x0f,
        'stream-9':     0x10,
        'stream-10':    0x11,
        'stream-11':    0x12,
        'stream-12':    0x13,
        'stream-13':    0x14,
        'stream-14':    0x15,
        'stream-15':    0x16,
        'stream-16':    0x17,
        'stream-17':    0x18,
        'stream-18':    0x19,
        # From external interfaces.
        'spdif-1':      0x1a,
        'spdif-2':      0x1b,
        'adat-1':       0x1c,
        'adat-2':       0x1d,
        'adat-3':       0x1e,
        'adat-4':       0x1f,
        'adat-5':       0x20,
        'adat-6':       0x21,
        'adat-7':       0x22,
        'adat-8':       0x23,
        # From internal multiplexers.
        'mixer-1':      0x24,
        'mixer-2':      0x25,
        'mixer-3':      0x26,
        'mixer-4':      0x27,
    }

    __MIC_LABELS = {
        'mic-1':    0x00,
        'mic-2':    0x01,
        'mic-3':    0x02,
        'mic-4':    0x03,
    }

    __IN_LABELS = {
        'analog-1': 0x00,
        'analog-2': 0x01,
        'analog-3': 0x02,
        'analog-4': 0x03,
        'analog-5': 0x04,
        'analog-6': 0x05,
        'analog-7': 0x06,
        'analog-8': 0x07,
        'spdif-1':  0x1a,
        'spdif-2':  0x1b,
        'adat-1':   0x1c,
        'adat-2':   0x1d,
        'adat-3':   0x1e,
        'adat-4':   0x1f,
        'adat-5':   0x20,
        'adat-6':   0x21,
        'adat-7':   0x22,
        'adat-8':   0x23,
    }

    __ATT_LABELS = {
        '+4dB':     0x00,
        '-10dB':    0x01,
    }

    __DISPLAY_TARGET = {
        'output':   0x00,
        'input':    0x01,
    }

    __OPT_IFACE_TARGETS = {
        'output':   0x00,
        'input':    0x01,
    }
    __OPT_IFACE_MODES = {
        'S/PDIF':       0x00,
        'ADAT/SMUX':    0x01,
    }

    __HP_LABELS = {
        'hp-2': 0x00,
        'hp-1': 0x01,
    }

    __HP_SRC_LABELS = {
        'analog-1/2':   0x01,
        'analog-3/4':   0x03,
        'analog-5/6':   0x05,
        'analog-7/8':   0x07,
        'spdif-1/2':    0x09,
        'none':         0xff,
    }

    __DB_MIN = -127.0
    __DB_MAX = 127.0

    __MIXER_TARGETS = {
        'mixer-1/2':  0x00,
        'mixer-3/4':  0x01,
    }

    __MIXER_SRCS = (
        'analog-1', 'analog-2', 'analog-3', 'analog-4',
        'analog-5', 'analog-6', 'analog-7', 'analog-8',
        'stream-1', 'stream-2', 'stream-3', 'stream-4',
        'stream-5', 'stream-6', 'stream-7', 'stream-8',
        'stream-9', 'stream-10', 'stream-11', 'stream-12',
        'stream-13', 'stream-14', 'stream-15', 'stream-16',
        'stream-17', 'stream-18',
        'adat-1', 'adat-2', 'adat-3', 'adat-4',
        'adat-5', 'adat-6', 'adat-7', 'adat-8',
        'spdif-1', 'spdif-2',
    )

    __MIXER_PARAMS = {
        VendorCmd.MIXER_SRC1: (
            'analog-1', 'analog-2', 'analog-3', 'analog-4',
            'analog-5', 'analog-6', 'analog-7', 'analog-8',
            'stream-1',
        ),
        VendorCmd.MIXER_SRC2: (
            'stream-2', 'stream-3', 'stream-4', 'stream-5',
            'stream-6', 'stream-7', 'stream-8', 'stream-9',
            'stream-10',
        ),
        VendorCmd.MIXER_SRC3: (
            'stream-11', 'stream-12', 'stream-13', 'stream-14',
            'stream-15', 'stream-16', 'stream-17', 'stream-18',
            'adat-1',
        ),
        VendorCmd.MIXER_SRC4: (
            'adat-2', 'adat-3', 'adat-4', 'adat-5',
            'adat-6', 'adat-7', 'adat-8', 'spdif-1',
            'spdif-2',
        ),
    }

    def __init__(self, path):
        super().__init__(path)

        if (self.vendor_id, self.model_id) != (0x0003db, 0x01eeee):
            raise OSError('Not supported.')

        unit_info = AvcGeneral.get_unit_info(self.fcp)
        self._company_ids = unit_info['company-id']

        guid = self.get_property('guid')
        self.__path = Path('/tmp/hinawa-{0:08x}'.format(guid))

        if self.__path.exists() and self.__path.is_file():
            self.__load_cache()
        else:
            self.__generate_cache()
            self.__save_cache()

    def __load_cache(self):
        with self.__path.open(mode='r') as f:
            self.__cache = load(f)

    def __save_cache(self):
        with self.__path.open(mode='w+') as f:
            dump(self.__cache, f)

    def __generate_cache(self):
        cache = {}
        for category, elems in self.__CACHE_LAYOUT.items():
            if category not in cache:
                cache[category] = {}
            for name, params in elems.items():
                if name not in cache[category]:
                    if len(params) == 1:
                        cache[category][name] = None
                    else:
                        cache[category][name] = {}

        # Display/Input/Output/Downgrade/Spdif-resample settings.
        for direction in ('display', 'input', 'output', 'knob', 'downgrade', 'spdif-resample'):
            for name, params in self.__CACHE_LAYOUT[direction].items():
                if len(params) == 1:
                    if isinstance(params[0], tuple):
                        cache[direction][name] = params[0][0]
                else:
                    for target in params[0]:
                        if params[1] == float:
                            cache[direction][name][target] = 0.0
                        elif isinstance(params[1], tuple):
                            cache[direction][name][target] = params[1][0]

        # Mixer settings.
        for target in self.__MIXER_TARGETS:
            if target not in cache['mixer']['src']:
                cache['mixer']['src'][target] = {}
            for i, src in enumerate(self.__MIXER_SRCS):
                db = 0.00
                balance = 100.0 if i % 2 else 0.0
                cache['mixer']['src'][target][src] = [db, balance]

        # Route settings.
        for name, params in self.__CACHE_LAYOUT['route'].items():
            targets, values = params
            for i, target in enumerate(targets):
                cache['route'][name][target] = values[i]

        self.__cache = cache

    @classmethod
    def __build_db_from_val(cls, val):
        if val > 256:
            raise ValueError('Invalid argument for linear value.')
        if val > 0x7f:
            db = (0xff - val)
        else:
            db = -val
        return float(db)
    @classmethod
    def __parse_val_from_db(cls, db):
        if db < cls.__DB_MIN or db > cls.__DB_MAX:
            raise ValueError('Invalid argument for dB.')
        return int(-db)

    def __command_set_param(self, cmd:VendorCmd, params):
        deps = bytearray()
        deps.append(cmd.value)
        deps.extend(params)

        params = AvcGeneral.set_vendor_dependent(self.fcp, self._company_ids,
                                                 deps)
        if params[0] != cmd.value:
            raise OSError('Unexpected value for vendor-dependent command.')
        return params[2:]

    def __get_clock_dst_plug(self):
        info = AvcConnection.get_subunit_plug_info(self.fcp, 'music', 0)
        for i in range(info['input']):
            addr = BcoPlugInfo.get_subunit_addr('input', 'music', 0, i)
            plug_type = BcoPlugInfo.get_plug_type(self.fcp, addr)
            if plug_type == 'Sync':
                break
        else:
            raise OSError('Unexpected state of device.')
        return i

    def get_clock_src_labels(self):
        labels = [k for k in self.__CLOCK_SRCS.keys()]
        labels.append('Internal')
        return labels
    def set_clock_src(self, src):
        if self.get_property('streaming'):
            raise OSError('Packet streaming started.')
        if src not in self.__CLOCK_SRCS and src != 'Internal':
            raise ValueError('Invalid argument for source of clock.')
        plug_id = self.__get_clock_dst_plug()
        dst = AvcCcm.get_subunit_signal_addr('music', 0, plug_id)
        if src == 'Internal':
            # Assume input/output sync plug has the same numerical id.
            src = dst
        else:
            src = self.__CLOCK_SRCS[src]
        AvcCcm.set_signal_source(self.fcp, src, dst)
    def get_clock_src(self):
        plug_id = self.__get_clock_dst_plug()
        dst = AvcCcm.get_subunit_signal_addr('music', 0, plug_id)
        src = AvcCcm.get_signal_source(self.fcp, dst)
        for name, addr in self.__CLOCK_SRCS.items():
            if AvcCcm.compare_addrs(src, AvcCcm.parse_signal_addr(addr)):
                return name
        # Assume input/output sync plug has the same numerical id.
        if (src['mode'] == 'subunit' and
                src['data']['type'] == 'music' and
                src['data']['id'] == 0 and
                src['data']['plug'] == plug_id):
            return 'Internal'
        raise OSError('Unexpected state of device.')

    def get_status(self):
        IN_KNOBS = {
            # name: (value-pos, selected-value, peak-pos)
            # 0x7f - 0x00
            MicInputLabels.MIC1:    (0, 0x00, 12),
            MicInputLabels.MIC2:    (1, 0x08, 13),
            MicInputLabels.MIC3:    (2, 0x10, 14),
            MicInputLabels.MIC4:    (3, 0x18, 15),
        }
        OUT_KNOBS = {
            # name: (value-pos, selected-mask)
            # 0x7f - 0x00
            MonitorLabels.MAIN: (7, 0x01),
            MonitorLabels.HP1:  (6, 0x02),
            MonitorLabels.HP2:  (5, 0x04),
        }
        params = bytearray(5)
        params.append(0x01)
        data = self.__command_set_param(VendorCmd.HW_STATUS, params)

        status = {}
        for label, params in IN_KNOBS.items():
            val_pos, sel_val, peak_pos = params
            db = self.__build_db_from_val(data[val_pos])
            status[label.value] = (db, bool(data[peak_pos] > 0x00))
            if data[4] & 0x18 == sel_val:
                status['in-knob'] = (label.value, data[8])
        for label, params in OUT_KNOBS.items():
            val_pos, sel_mask = params
            db = self.__build_db_from_val(data[val_pos])
            status[label.value] = db
            if data[4] & sel_mask:
                status['out-knob'] = (label.value, data[9])
        return status

    def reset_meters(self):
        params = bytearray(5)
        params[0] = 0x0f
        self.__command_set_param(VendorCmd.HW_CONFIG, params)

    def get_stream_mode_labels(self):
        return self.__STREAM_MODE_LABELS.keys()
    def set_stream_mode(self, mode):
        if mode not in self.__STREAM_MODE_LABELS:
            raise ValueError('Invalid argument for stream mode.')
        params = bytearray(5)
        params[0] = 0x06
        params[1] = self.__STREAM_MODE_LABELS[mode]
        self.__command_set_param(VendorCmd.HW_CONFIG, params)
    def get_stream_mode(self):
        SYNC_PLUG_IDS = {
            5:  '8x8',
            6:  '10x10',
            7:  '18x18',
        }
        plug_id = self.__get_clock_dst_plug()
        if plug_id not in SYNC_PLUG_IDS:
            raise OSError('Unexpected state of device.')
        return SYNC_PLUG_IDS[plug_id]

    # Hardware configurations.
    def set_display_mode(self, enable):
        params = bytearray(5)
        params[0] = 0x09
        if enable:
            params[1] = 0x01
        self.__command_set_param(VendorCmd.HW_CONFIG, params)
        self.__cache['display']['mode'] = 1 if enable else 0
        self.__save_cache()
    def get_display_mode(self):
        return self.__cache['display']['mode']

    def get_display_target_labels(self):
        return self.__DISPLAY_TARGET.keys()
    def set_display_target(self, target):
        if target not in self.__DISPLAY_TARGET:
            raise ValueError('Invalid argument for display target.')
        params = bytearray(5)
        params[0] = 0x0a
        params[1] = self.__DISPLAY_TARGET[target]
        self.__command_set_param(VendorCmd.HW_CONFIG, params)
        self.__cache['display']['target'] = target
        self.__save_cache()
    def get_display_target(self):
        return self.__cache['display']['target']

    def set_display_illuminate(self, enable):
        params = bytearray(5)
        params[0] = 0x08
        if enable:
            params[1] = 0x01
        self.__command_set_param(VendorCmd.HW_CONFIG, params)
        self.__cache['display']['illuminate'] = 1 if enable else 0
        self.__save_cache()
    def get_display_illuminate(self):
        return self.__cache['display']['illuminate']

    def set_display_overhold(self, enable):
        params = bytearray(5)
        params[0] = 0x0e
        if enable:
            params[1] = 0x01
        self.__command_set_param(VendorCmd.HW_CONFIG, params)
        self.__cache['display']['overhold'] = 1 if enable else 0
        self.__save_cache()
    def get_display_overhold(self):
        return self.__cache['display']['overhold']

    def get_opt_iface_target_labels(self):
        return self.__OPT_IFACE_TARGETS.keys()
    def get_opt_iface_mode_labels(self):
        return self.__OPT_IFACE_MODES.keys()
    def set_opt_iface_mode(self, target, mode):
        if target not in self.__OPT_IFACE_TARGETS:
            raise ValueError('Invalid argumetns for target of optical inteface.')
        if mode not in self.__OPT_IFACE_MODES:
            raise ValueError('Invalid argument for mode of optical interface.')
        params = bytearray(5)
        params[0] = self.__OPT_IFACE_TARGETS[target]
        params[1] = self.__OPT_IFACE_MODES[mode]
        self.__command_set_param(VendorCmd.HW_CONFIG, params)
        self.__cache[target]['opt-iface'] = mode
        self.__save_cache()
    def get_opt_iface_mode(self, target):
        return self.__cache[target]['opt-iface']

    def set_cd_mode(self, enable):
        params = bytearray(5)
        params[0] = 0xf5
        if enable:
            params[1] = 0x01
        self.__command_set_param(VendorCmd.HW_CONFIG, params)

    # Monitor configurations.
    def get_out_volume_labels(self):
        labels = []
        for monitor in MonitorLabels:
            labels.append(monitor.value)
        return labels
    def set_out_volume(self, target, db):
        SUBCMDS = {
            MonitorLabels.MAIN.value:   0x00,
            MonitorLabels.HP1.value:    0x01,
            MonitorLabels.HP2.value:    0x02,
        }
        if target not in SUBCMDS:
            raise ValueError('Invalid argument for output.')

        params = bytearray(5)
        params[0] = SUBCMDS[target]
        params[1] = self.__parse_val_from_db(db)
        self.__command_set_param(VendorCmd.OUT_VOL, params)
    def get_out_volume(self, target):
        for monitor in MonitorLabels:
            if target == monitor.value:
                break
        else:
            raise ValueError('Invalid argument for output.')

        status = self.get_status()
        return status[target]

    # Microphone configurations.
    def get_mic_labels(self):
        return self.__MIC_LABELS.keys()
    def set_polarity(self, target, invert):
        if target not in self.__MIC_LABELS:
            raise ValueError('Invalid argument for mic.')
        params = bytearray(5)
        params[0] = self.__MIC_LABELS[target]
        if invert:
            params[1] = 1
        self.__command_set_param(VendorCmd.MIC_POLARITY, params)
        self.__cache['input']['mic-polarity'][target] = 1 if invert else 0
        self.__save_cache()
    def get_polarity(self, target):
        if target not in self.__MIC_LABELS:
            raise ValueError('Invalid argument for mic.')
        return self.__cache['input']['mic-polarity'][target]

    def set_phantom_power(self, target, enable):
        if target not in self.__MIC_LABELS:
            raise ValueError('Invalid argument for mic.')
        params = bytearray(5)
        params[0] = self.__MIC_LABELS[target]
        if enable:
            params[1] = 1
        self.__command_set_param(VendorCmd.MIC_POWER, params)
        self.__cache['input']['mic-power'][target] = 1 if enable else 0
        self.__save_cache()
    def get_phantom_power(self, target):
        if target not in self.__MIC_LABELS:
            raise ValueError('Invalid argument for mic.')
        return self.__cache['input']['mic-power'][target]

    # Line input/output configurations.
    def get_line_in_labels(self):
        labels = []
        for label in self.__IN_LABELS:
            if label.find('analog-') == 0:
                labels.append(label)
        return labels
    def get_line_out_labels(self):
        labels = []
        for label in self.__OUT_LABELS:
            if label.find('analog-') == 0:
                labels.append(label)
        return labels

    def set_soft_limit(self, target, enable):
        if target not in self.__IN_LABELS:
            raise ValueError('Invalid argument for input')
        params = bytearray(5)
        params[0] = self.__IN_LABELS[target]
        if enable:
            params[1] = 1
        self.__command_set_param(VendorCmd.INPUT_LIMIT, params)
        self.__cache['input']['soft-limit'][target] = 1 if enable else 0
        self.__save_cache()
    def get_soft_limit(self, target):
        if target not in self.__IN_LABELS:
            raise ValueError('Invalid argument for input')
        return self.__cache['input']['soft-limit'][target]

    def get_attr_labels(self):
        return self.__ATT_LABELS.keys()
    def set_in_attr(self, target, attr):
        if target not in self.__IN_LABELS:
            raise ValueError('Invalid argument for input.')
        if attr not in self.__ATT_LABELS:
            raise ValueError('Invalid argument for attenuation')
        params = bytearray(5)
        params[0] = self.__IN_LABELS[target]
        params[1] = 0x01    # Input
        params[2] = self.__ATT_LABELS[attr]
        self.__command_set_param(VendorCmd.IO_ATTENUATION, params)
        self.__cache['input']['attr'][target] = attr
        self.__save_cache()
    def get_in_attr(self, target):
        if target not in self.__IN_LABELS:
            raise ValueError('Invalid argument for input.')
        return self.__cache['input']['attr'][target]

    def set_out_attr(self, target, attr):
        if target not in self.__OUT_LABELS:
            raise ValueError('Invalid argument for output.')
        if attr not in self.__ATT_LABELS:
            raise ValueError('Invalid argument for attenuation')
        params = bytearray(5)
        params[0] = self.__OUT_LABELS[target]
        params[1] = 0x00    # Output
        params[2] = self.__ATT_LABELS[attr]
        self.__command_set_param(VendorCmd.IO_ATTENUATION, params)
        self.__cache['output']['attr'][target] = attr
        self.__save_cache()
    def get_out_attr(self, target):
        if target not in self.__OUT_LABELS:
            raise ValueError('Invalid argument for output.')
        return self.__cache['output']['attr'][target]

    # Route configurations.
    def get_out_labels(self):
        labels = []
        for port in self.__PORT_LABELS:
            if port.find('stream-') == 0 or port.find('mixer-') == 0:
                continue
            labels.append(port)
        return labels
    def get_out_src_labels(self):
        return self.__PORT_LABELS.keys()
    def set_out_src(self, target, src):
        if target not in self.__PORT_LABELS:
            raise ValueError('Invalid argument for output.')
        if src not in self.__PORT_LABELS:
            raise ValueError('Invalid argument for source of output.')
        params = bytearray(5)
        params[0] = self.__PORT_LABELS[target]
        params[1] = self.__PORT_LABELS[src]
        self.__command_set_param(VendorCmd.IO_ROUTING, params)
        self.__cache['route']['out-src'][target] = src
        self.__save_cache()
    def get_out_src(self, target):
        if target not in self.__PORT_LABELS:
            raise ValueError('Invalid argument for output.')
        return self.__cache['route']['out-src'][target]

    def get_cap_labels(self):
        labels = []
        for port in self.__PORT_LABELS:
            if port.find('stream-') == 0:
                labels.append(port)
        return labels
    def get_cap_src_labels(self):
        labels = []
        for port in self.__PORT_LABELS:
            if port.find('stream-') == 0 or port.find('mixer-') == 0:
                continue
            labels.append(port)
        return labels
    def set_cap_src(self, target, src):
        if target not in self.__PORT_LABELS:
            raise ValueError('Invalid argument for capture.')
        if src not in self.__PORT_LABELS:
            raise ValueError('Invalid argument for source of capture.')
        params = bytearray(5)
        params[0] = self.__PORT_LABELS[target]
        params[1] = self.__PORT_LABELS[src]
        self.__command_set_param(VendorCmd.IO_ROUTING, params)
        self.__cache['route']['cap-src'][target] = src
        self.__save_cache()
    def get_cap_src(self, target):
        if target not in self.__PORT_LABELS:
            raise ValueError('Invalid argument for capture.')
        return self.__cache['route']['cap-src'][target]

    def get_hp_labels(self):
        return self.__HP_LABELS.keys()
    def get_hp_src_labels(self):
        return self.__HP_SRC_LABELS.keys()
    def set_hp_src(self, target, src):
        if target not in self.__HP_LABELS:
            raise ValueError('Invalid argument for headphone.')
        if src not in self.__HP_SRC_LABELS:
            raise ValueError('Invalid argument for source of headphone.')
        params = bytearray(5)
        params[0] = self.__HP_LABELS[target]
        params[1] = self.__HP_SRC_LABELS[src]
        self.__command_set_param(VendorCmd.HP_SRC, params)
        self.__cache['route']['hp-src'][target] = src
        self.__save_cache()
    def get_hp_src(self, target):
        if target not in self.__HP_LABELS:
            raise ValueError('Invalid argument for headphone.')
        return self.__cache['route']['hp-src'][target]

    # Internal multiplexer configuration.
    def get_mixer_labels(self):
        return self.__MIXER_TARGETS.keys()
    def get_mixer_src_labels(self):
        return self.__MIXER_SRCS
    def set_mixer_src(self, target, src, db, balance):
        if target not in self.__MIXER_TARGETS:
            raise ValueError('Invalid argument for mixer.')
        if src not in self.__MIXER_SRCS:
            raise ValueError('Invalid argument for source of mixer.')
        if db < -48 or db > 0:
            raise ValueError('Invalid argument for db of source.')
        if balance < 0 or 100 < balance:
            raise ValueError('Invalid argument for balance of source.')
        data = [db, balance]

        params = bytearray()
        params.append(self.__MIXER_TARGETS[target])
        for cmd, sources in self.__MIXER_PARAMS.items():
            if src in sources:
                for source in sources:
                    if src == source:
                        db, balance = data
                    else:
                        db, balance = self.__cache['mixer']['src'][target][source]
                    val = int(0xffff * (1 + db / 48))
                    right = int(val * balance // 100)
                    left = val - right
                    params.extend(pack('<H', left))
                    params.extend(pack('<H', right))
                break
        else:
            raise OSError('Invalid definition of source of mixer.')

        self.__command_set_param(cmd, params)
        self.__cache['mixer']['src'][target][src] = data
        self.__save_cache()
    def get_mixer_src(self, target, src):
        return self.__cache['mixer']['src'][target][src]
