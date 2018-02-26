import gi
gi.require_version('Hinawa', '1.0')
from gi.repository import Hinawa

from array import array
from math import log10

__all__ = ['EftInfo', 'EftFlash', 'EftTransmit', 'EftHwctl', 'EftPhysOutput',
           'EftPhysInput', 'EftPlayback', 'EftCapture', 'EftMonitor',
           'EftIoconf']

#
# Category No.0, for hardware information
#
class EftInfo():
    SUPPORTED_MODELS = (
        'Audiofire2',
        'Audiofire4',
        'Audiofire8',
        'Audiofire8p',
        'Audiofire12',
        'Audiofire12HD',
        'Audiofire12Apple',
        'FireworksHDMI',
        'Onyx400F',
        'Onyx1200f',
        'Fireworks8',
        'RobotInterfacePack',
        'AudioPunk',
    )

    SUPPORTED_FEATURES = (
        'changeable-resp-addr',
        'control-room-mirroring',
        'spdif-coax',
        'aesebu-xlr',
        'dsp',
        'fpga',
        'phantom-powering',
        'rx-mapping',
        'adjust-input-level',
        'spdif-opt',
        'adat-opt',
        'nominal-input',
        'nominal-output',
        'soft-clip',
        'robot-hex-input',
        'robot-battery-charge',
        # For our purpose
        'tx-mapping',
    )

    SUPPORTED_CLOCK_SOURCES = (
        'internal',
        'syt-match',
        'word-clock',
        'spdif',
        'adat1',
        'adat2',
        'continuous'
    )

    SUPPORTED_SAMPLING_RATES = (
        32000, 44100, 48000,
        88200, 96000,
        176400, 192000
    )

    SUPPORTED_FIRMWARES = ('ARM', 'DSP', 'FPGA')

    SUPPORTED_PORT_NAMES = (
        'analog',
        'spdif',
        'adat',
        'spdif/adat',
        'analog mirroring',
        'headphones',
        'I2S',
        'guitar',
        'piezo guitar',
        'guitar string'
    )

    _MODELS = {
        'Audiofire2':           0x000af2,
        'Audiofire4':           0x000af4,
        'Audiofire8':           0x000af8,
        'Audiofire8p':          0x000af9,
        'Audiofire12':          0x00af12,
        'Audiofire12HD':        0x0af12d,
        'Audiofire12Apple':     0x0af12a,
        'FireworksHDMI':        0x00afd1,
        'Onyx400F':             0x00400f,
        'Onyx1200f':            0x01200f,
        'Fireworks8':           0x0000f8,
        'RobotInterfacePack':   0x00afb2,
        'AudioPunk':            0x00afb9,
    }

    _FEATURE_FLAGS = {
        'changeable-resp-addr':    0x0001,
        'control-room-mirroring':  0x0002,
        'spdif-coax':              0x0004,
        'aesebu-xlr':              0x0008,
        'dsp':                     0x0010,
        'fpga':                    0x0020,
        'phantom-powering':        0x0040,
        'rx-mapping':              0x0080,
        'adjust-input-level':      0x0100,
        'spdif-opt':               0x0200,
        'adat-opt':                0x0400,
        'nominal-input':           0x0800,
        'nominal-output':          0x1000,
        'soft-clip':               0x2000,
        'robot-hex-input':         0x4000,
        'robot-battery-charge':    0x8000,
    }

    _CLOCK_FLAGS = {
        'internal':    0x0001,
        'syt-match':   0x0002,
        'word-clock':  0x0004,
        'spdif':       0x0008,
        'adat1':       0x0010,
        'adat2':       0x0020,
        'continuous':  0x0040,
    }

    _MIDI_FLAGS = {
        'midi-in-1':        0x00000100,
        'midi-out-1':       0x00000200,
        'midi-in-2':        0x00000400,
        'midi-out-2':       0x00000800,
    }

    _ROBOT_FLAGS = {
        'battery-charging': 0x20000000,
        'stereo-connect':   0x40000000,
        'hex-signal':       0x80000000,
    }

    @staticmethod
    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(0, cmd, args)

    @classmethod
    def get_spec(cls, unit):
        params = cls._execute_command(unit, 0, None)
        info = {}
        info['features'] = cls._parse_capability(params)
        info['clock-sources'] = cls._parse_clock_source(params)
        info['sampling-rates'] = cls._parse_sampling_rate(params)
        info.update(cls._parse_phys_ports(params))
        info.update(cls._parse_mixer_channels(params))
        info.update(cls._parse_stream_formation(params))
        info['firmware-versions'] = cls._parse_firmware_versions(params)
        return info

    @classmethod
    def get_metering(cls, unit):
        params = cls._execute_command(unit, 1, None)
        metering = {}
        metering['clocks'] = {}
        for name, flag in cls._CLOCK_FLAGS.items():
            if params[0] & flag:
                metering['clocks'][name] = True
            else:
                metering['clocks'][name] = False
        metering['midi'] = {}
        for name, flag in cls._MIDI_FLAGS.items():
            if params[0] & flag:
                metering['midi'][name] = True
            else:
                metering['midi'][name] = False
        metering['robot'] = {}
        for name, flag in cls._ROBOT_FLAGS.items():
            if params[0] & flag:
                metering['robot'][name] = True
            else:
                metering['robot'][name] = False
        metering['spdif'] = params[1]
        metering['adat'] = params[2]
        metering['outputs'] = []
        for i in range(params[5]):
            index = 9 + i
            if params[index] == 0:
                db = -144.0
            else:
                db = round(20 * log10(params[index] / 0x80000000), 1)
            metering['outputs'].append(db)
        metering['inputs'] = []
        for i in range(params[6]):
            index = 9 + params[5] + i
            if params[index] == 0:
                db = -144.0
            else:
                db = round(20 * log10(params[index] / 0x80000000), 1)
            metering['inputs'].append(db)
        return metering

    @classmethod
    def set_resp_addr(cls, unit, addr):
        args = array('I')
        args.append((addr >> 24) & 0xffffffff)
        args.append(addr         & 0xffffffff)
        cls._execute_command(unit, 2, args)

    @classmethod
    def read_session_data(cls, unit, offset, quadlets):
        args = array('I')
        args.append(offset)
        args.append(quadlets)
        params = cls._execute_command(unit, 3, args)
        return params

    @classmethod
    def get_debug_info(cls, unit):
        params = cls._execute_command(unit, 4, None)

        # params[00]: isochronous stream 1 flushed
        # params[01]: isochronous stream 1 underruns
        # params[02]: firewire3 control
        # params[03]: firewire3 control written
        # params[04-15]: data
        return params

    @classmethod
    def test_dsp(cls, unit, value):
        args = array('I')
        args.append(value)
        params = cls._execute_command(unit, 5, args)
        return params[0]

    @classmethod
    def test_arm(cls, unit, value):
        args = array('I')
        args.append(value)
        params = cls._execute_command(unit, 6, args)
        return params[0]

    @classmethod
    def _parse_capability(cls, params):
        caps = {}
        for name, flag in cls._FEATURE_FLAGS.items():
            if params[0] & flag:
                caps[name] = True
            else:
                caps[name] = False
        # This is supported just by Onyx 1200F.
        if params[3] == 0x01200f:
            caps['tx-mapping'] = True
        else:
            caps['tx-mapping'] = False
        return caps

    @classmethod
    def _parse_clock_source(cls, params):
        srcs = {}
        for name, flag in cls._CLOCK_FLAGS.items():
            if params[21] & flag:
                srcs[name] = True
            else:
                srcs[name] = False
        return srcs

    @classmethod
    def _parse_sampling_rate(cls, params):
        rates = {}
        for rate in cls.SUPPORTED_SAMPLING_RATES:
            if params[39] <= rate and rate <= params[38]:
                rates[rate] = True
            else:
                rates[rate] = False
        return rates

    @classmethod
    def _parse_phys_ports(cls, params):
        def parse_ports(params):
            ports = []
            data = (params[1] >> 16, params[1] & 0xffff,
                    params[2] >> 16, params[2] & 0xffff,
                    params[3] >> 16, params[3] & 0xffff,
                    params[4] >> 16, params[4] & 0xffff)
            for i in range(params[0]):
                count = data[i] & 0xff
                index = data[i] >> 8
                if index > len(cls.SUPPORTED_PORT_NAMES):
                    name = 'dummy'
                else:
                    name = cls.SUPPORTED_PORT_NAMES[index]
                for j in range(count):
                    ports.append(name)
            return ports

        return {'phys-inputs': parse_ports(params[26:]),
                'phys-outputs': parse_ports(params[31:])}

    @staticmethod
    def _parse_mixer_channels(params):
        return {'capture-channels': params[43],
                'playback-channels': params[42]}

    @staticmethod
    def _parse_stream_formation(params):
        return {'tx-stream-channels': (params[23], params[46], params[48]),
                'rx-stream-channels': (params[22], params[45], params[47])}

    @classmethod
    def _parse_firmware_versions(cls, params):
        return {'DSP':  cls._get_literal_version(params[40]),
                'ARM':  cls._get_literal_version(params[41]),
                'FPGA': cls._get_literal_version(params[44])}

    @staticmethod
    def _get_literal_version(val):
        return '{0}.{1}.{2}'.format((val >> 24) & 0xff, \
                                    (val >> 16) & 0xff, \
                                    (val >>  8) & 0xff)

#
# Category No.1, for flash commands
#
class EftFlash():
    @staticmethod
    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(1, cmd, args)

    @classmethod
    def erase(cls, unit, offset):
        args = array('I')
        args.append(offset)
        cls._execute_command(unit, 0, args)

    @classmethod
    def read_block(cls, unit, offset, quadlets):
        args = array('I')
        args.append(offset)
        args.append(quadlets)
        return cls._execute_command(unit, 1, args)

    @classmethod
    def write_block(cls, unit, offset, data):
        args = array('I')
        args.append(offset)
        args.append(len(data))
        for datum in data:
            args.append(datum)
        cls._execute_command(unit, 2, args)

    @classmethod
    def get_status(cls, unit):
        # return status means it.
        cls._execute_command(unit, 3, none)

    @classmethod
    def get_session_offset(cls, unit):
        params = cls._execute_command(unit, 4, None)
        return params[0]

    @classmethod
    def set_lock(cls, unit, lock):
        args = array('I')
        if lock is not 0:
            args.append(1)
        else:
            args.append(0)
        cls._execute_command(unit, 5, args)

#
# Category No.2, for transmission control commands
#
class EftTransmit():
    SUPPORTED_MODES = ('windows', 'iec61883-6')
    SUPPORTED_PLAYBACK_DROPS = (1, 2, 4)
    SUPPORTED_RECORD_STREATCH_RATIOS = (1, 2, 4)
    SUPPORTED_SERIAL_BPS = (16, 24)
    SUPPORTED_SERIAL_DATA_FORMATS = ('left-adjusted', 'i2s')

    @staticmethod
    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(2, cmd, args)

    @classmethod
    def set_mode(cls, unit, mode):
        if cls.SUPPORTED_MODES.count(mode) == 0:
            raise ValueError('Invalid argument for mode')
        args = array('I')
        args.append(cls.SUPPORTED_MODES.index(mode))
        cls._execute_command(unit, 0, args)

    @classmethod
    def set_fw_hdmi(cls, unit, playback_drop, record_stretch_ratio, serial_bps,
                    serial_data_format):
        if cls.SUPPORTED_PLAYBACK_DROPS.count(playback_drop) == 0:
            raise ValueError('Invalid argument for playback drop')
        if cls.SUPPORTED_RECORD_STREATCH_RATIOS(record_stretch_ratio) == 0:
            raise ValueError('Invalid argument for record stretch')
        if cls.SUPPORTED_SERIAL_BPS.count(serial_bps) == 0:
            raise ValueError('Invalid argument for serial bits per second')
        if cls.SUPPORTED_SERIAL_DATA_FORMATS(serial_data_format) == 0:
            raise ValueError('Invalid argument for serial data format')

        args = array('I')
        args.append(playback_drop)
        args.append(record_stretch_ratio)
        args.append(serial_bps)
        args.append(cls.SUPPORTED_SERIAL_DATA_FORMATS.index(serial_data_format))
        cls._execute_command(unit, 4, args)

#
# Category No.3, for hardware control commands
#
class EftHwctl():
    SUPPORTED_BOX_STATES = (
        'internal-multiplexer',
        'spdif-pro',
        'spdif-non-audio',
        'control-room',
        'output-level-bypass',
        'metering-mode-in',
        'metering-mode-out',
        'soft-clip',
        'robot-hex-input',
        'robot-battery-charge',
        'phantom-powering'
    )

    # Internal parameters
    _BOX_STATE_PARAMS = {
        # identifier,         shift,        zero,       one
        'internal-multiplexer': ( 0, ('Disabled', 'Enabled')),
        'spdif-pro':            ( 1, ('Disabled', 'Enabled')),
        'spdif-non-audio':      ( 2, ('Disabled', 'Enabled')),
        'control-room':         ( 8, ('A', 'B')),
        'output-level-bypass':  ( 9, ('Disabled', 'Enabled')),
        'metering-mode-in':     (12, ('A', 'B')),
        'metering-mode-out':    (13, ('D1', 'D2')),
        'soft-clip':            (16, ('Disabled', 'Enabled')),
        'robot-hex-input':      (29, ('Disabled', 'Enabled')),
        'robot-battery-charge': (30, ('Disabled', 'Enabled')),
        'phantom-powering':     (31, ('Disabled', 'Enabled')),
    }

    @staticmethod
    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(3, cmd, args)

    @classmethod
    def set_clock(cls, unit, rate, source, reset):
        if EftInfo.SUPPORTED_SAMPLING_RATES.count(rate) == 0:
            raise ValueError('Invalid argument for sampling rate')
        if EftInfo.SUPPORTED_CLOCK_SOURCES.count(source) == 0:
            raise ValueError('Invalid argument for source of clock')
        if reset > 0:
            reset = 0x80000000
        args = array('I')
        args.append(EftInfo.SUPPORTED_CLOCK_SOURCES.index(source))
        args.append(rate)
        args.append(reset)
        cls._execute_command(unit, 0, args)

    @classmethod
    def get_clock(cls, unit):
        params = cls._execute_command(unit, 1, None)
        if params[0] >= len(EftInfo.SUPPORTED_CLOCK_SOURCES):
            raise OSError('Unexpected clock source in response')
        if EftInfo.SUPPORTED_SAMPLING_RATES.count(params[1]) == 0:
            raise OSError('Unexpected sampling rate in response')
        return (params[1], EftInfo.SUPPORTED_CLOCK_SOURCES[params[0]])

    @classmethod
    def set_box_states(cls, unit, states):
        enabled = 0
        disabled = 0
        for name,state in states.items():
            if name not in cls._BOX_STATE_PARAMS:
                raise ValueError('Invalid value in box states')
            shift   = cls._BOX_STATE_PARAMS[name][0]
            values  = cls._BOX_STATE_PARAMS[name][1]
            value = values.index(state)
            if value is 0:
                disabled |= (1 << shift)
            else:
                enabled |= (1 << shift)
        args = array('I')
        args.append(enabled)
        args.append(disabled)
        cls._execute_command(unit, 3, args)

    @classmethod
    def get_box_states(cls, unit):
        params = cls._execute_command(unit, 4, None)
        state = params[0]
        states = {}
        for name,params in cls._BOX_STATE_PARAMS.items():
            shift = params[0]
            values = params[1]
            index = (state >> shift) & 0x01
            states[name] = values[index]
        return states

    @classmethod
    def reconnect_phy(cls, unit):
        cls._execute_command(unit, 6, None)

    @classmethod
    def blink_leds(cls, unit):
        cls._execute_command(unit, 7, None)

    @classmethod
    def set_continuous_clock(cls, unit, continuous_rate):
        args = array('I')
        args.append(continuous_rate * 512 // 1500)
        cls._execute_command(unit, 8, args)

#
# Category No.4, for physical output multiplexer commands
#
class EftPhysOutput():
    OPERATIONS = ('gain', 'mute', 'nominal')

    @staticmethod
    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(4, cmd, args)

    @classmethod
    def set_param(cls, unit, operation, channel, value):
        if operation is 'gain':
            cmd = 0
        elif operation is 'mute':
            cmd = 2
            if value > 0:
                value = 1
        elif operation is 'nominal':
            cmd = 8
            if value > 0:
                value = 2
        else:
            raise ValueError('Invalid argument for operation.')
        args = array('I')
        args.append(channel)
        args.append(value)
        cls._execute_command(unit, cmd, args)

    @classmethod
    def get_param(cls, unit, operation, channel):
        if operation is 'gain':
            cmd = 1
        elif operation is 'mute':
            cmd = 3
        elif operation is 'nominal':
            cmd = 9
        else:
            raise ValueError('Invalid argument for operation.')
        args = array('I')
        args.append(channel)
        params = cls._execute_command(unit, cmd, args)
        if operation is 'nominal':
            if params[1] == 2:
                params[1] = 1
        return params[1]

#
# Category No.5, for physical input multiplexer commands
#
class EftPhysInput():
    OPERATIONS = ('nominal')

    @staticmethod
    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(5, cmd, args)

    @classmethod
    def set_param(cls, unit, operation, channel, value):
        if operation is 'nominal':
            cmd = 8
            if value > 0:
                value = 2
        else:
            raise ValueError('Invalid argument for operation')
        args = array('I')
        args.append(channel)
        args.append(value)
        cls._execute_command(unit, cmd, args)

    @classmethod
    def get_param(cls, unit, operation, channel):
        if operation is 'nominal':
            cmd = 9
        else:
            raise ValueError('Invalid argumentfor operation')
        args = array('I')
        args.append(channel)
        args.append(0xff)
        params = cls._execute_command(unit, cmd, args)
        return params[1]

#
# Category No.6, for playback stream multiplexer commands
#
class EftPlayback():
    OPERATIONS = ('gain', 'mute', 'solo')

    @staticmethod
    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(6, cmd, args)

    @classmethod
    def set_param(cls, unit, operation, channel, value):
        if operation is 'gain':
            cmd = 0
        elif operation is 'mute':
            cmd = 2
            if value > 0:
                value = 1
        elif operation is 'solo':
            cmd = 4
            if value > 0:
                value = 1
        else:
            raise ValueError('Invalid argument for operation.')
        args = array('I')
        args.append(channel)
        args.append(value)
        cls._execute_command(unit, cmd, args)

    @classmethod
    def get_param(cls, unit, operation, channel):
        if operation is 'gain':
            cmd = 1
        elif operation is 'mute':
            cmd = 3
        elif operation is 'solo':
            cmd = 5
        else:
            raise ValueError('Invalid argument for operation.')
        args = array('I')
        args.append(channel)
        params = cls._execute_command(unit, cmd, args)
        return params[1]

class EftCapture():
    OPERATIONS = ()

    @staticmethod
    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(7, cmd, args)

#
# Category No.8, for input monitoring multiplexer commands
#
class EftMonitor():
    OPERATIONS = ('gain', 'mute', 'solo', 'pan')

    @staticmethod
    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(8, cmd, args)

    @classmethod
    def set_param(cls, unit, operation, in_ch, out_ch, value):
        if operation is 'gain':
            cmd = 0
        elif operation is 'mute':
            cmd = 2
            if value > 0:
                value = 1
        elif operation is 'solo':
            cmd = 4
            if value > 0:
                value = 1
        elif operation is 'pan':
            cmd = 6
            if value < 0 or value > 255:
                raise ValueError('Invalid argument for panning')
        else:
            raise ValueError('Invalid argument for operation.')
        args = array('I')
        args.append(in_ch)
        args.append(out_ch)
        args.append(value)
        cls._execute_command(unit, cmd, args)

    @classmethod
    def get_param(cls, unit, operation, in_ch, out_ch):
        if operation is 'gain':
            cmd = 1
        elif operation is 'mute':
            cmd = 3
        elif operation is 'solo':
            cmd = 5
        elif operation is 'pan':
            cmd = 7
        else:
            raise ValueError('Invalid argument for operation.')
        args = array('I')
        args.append(in_ch)
        args.append(out_ch)
        params = cls._execute_command(unit, cmd, args)
        return params[2]

#
# Category No.9, for input/output configuration commands
#
class EftIoconf():
    # NOTE: use the same strings in features of EftInfo.
    DIGITAL_INPUT_MODES = ('spdif-coax', 'aesebu-xlr', 'spdif-opt', 'adat-opt')

    @staticmethod
    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(9, cmd, args)

    @classmethod
    def set_control_room_mirroring(cls, unit, output_pair):
        args = array('I')
        args.append(output_pair)
        cls._execute_command(unit, 0, args)

    @classmethod
    def get_control_room_mirroring(cls, unit):
        params = cls._execute_command(unit, 1, None)
        return params[0]

    @classmethod
    def set_digital_input_mode(cls, unit, mode):
        if cls.DIGITAL_INPUT_MODES.count(mode) == 0:
            raise ValueError('Invalid argument for digital mode')
        args = array('I')
        args.append(cls.DIGITAL_INPUT_MODES.index(mode))
        cls._execute_command(unit, 2, args)

    @classmethod
    def get_digital_input_mode(cls, unit):
        params = cls._execute_command(unit, 3, None)
        if params[0] >= len(cls.DIGITAL_INPUT_MODES):
            raise OSError
        return cls.DIGITAL_INPUT_MODES[params[0]]

    @classmethod
    def set_phantom_powering(cls, unit, state):
        if state > 0:
            state = 1
        args = array('I')
        args.append(state)
        cls._execute_command(unit, 4, args)

    @classmethod
    def get_phantom_powering(cls, unit):
        params= cls._execute_command(unit, 5, None)
        return params[0]

    @classmethod
    def set_stream_mapping(cls, unit, rx_maps, tx_maps):
        params = cls._execute_command(unit, 7, None)
        rx_map_count = params[2]
        if len(rx_maps) > rx_map_count:
            ValueError('Invalid argument for rx stream mapping')
        tx_map_count = params[34]
        if len(tx_maps) > tx_map_count:
            ValueError('Invalid argument for tx stream mapping')
        for i in range(len(rx_maps)):
            params[4 + i] = rx_maps[i]
        for i in range(len(tx_maps)):
            params[36 + i] = tx_maps[i]
        cls._execute_command(unit, 6, params)

    @classmethod
    def get_stream_mapping(cls, unit):
        param = cls._execute_command(unit, 7, None)
        tx_map_count = param[34]
        tx_map = []
        for i in range(tx_map_count):
            tx_map.append(param[36 + i])
        rx_map_count = param[2]
        rx_map = []
        for i in range(rx_map_count):
            rx_map.append(param[4 + i])
        return {'tx-map': tx_map, 'rx-map': rx_map}
