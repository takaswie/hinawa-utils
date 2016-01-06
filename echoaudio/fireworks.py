from array import array
from math import log10
from gi.repository import Hinawa

class Fireworks(Hinawa.SndEfw):
    # read-only properties
    #   The capabilities of this unit
    supported_features = {
        'changeable-resp-addr': False,
        'aesebu-xlr': False,
        'control-room-mirroring': False,
        'spdif-coax': False,
        'dsp': False,
        'fpga': False,
        'phantom-powering': False,
        'rx-mapping': False,
        'adjust-input-level': False,
        'spdif-opt': False,
        'adat-opt': False,
        'nominal-input': False,
        'nominal-output': False,
        'soft-clip': False,
        'robot-hex-input': False,
        'robot-battery-charge': False,
        # for my purpose.
        'tx-mapping': False,
    }

    #   Supported sources of clock
    supported_clock_sources = { 
        'internal':     False,
        'syt-match':    False,
        'word-clock':   False,
        'spdif':        False,
        'ADAT-1':       False,
        'ADAT-2':       False,
        'continuous':   False,
    }

    #   Supported sampling rates
    supported_sampling_rates = {
        32000:  False,
        44100:  False,
        48000:  False,
        88200:  False,
        96000:  False,
        176400: False,
        192000: False,
    }

    phys_inputs = []
    phys_outputs = []

    mixer_playback_channels = 0
    mixer_capture_channels = 0

    midi_out_ports = 0
    midi_in_ports = 0

    tx_stream_channels = [0, 0, 0]
    rx_stream_channels = [0, 0, 0]

    firmware_versions = {
        'ARM':  '',
        'DSP':  '',
        'FPGA': '',
    }

    metering_flags = {
        # Clock detection
        'clock-internal':   0x00000001,
        'clock-syt-match':  0x00000002,
        'clock-word':       0x00000004,
        'clock-spdif':      0x00000008,
        'clock-adat-a':     0x00000010,
        'clock-adat-b':     0x00000020,
        'clock-continuous': 0x00000040,
        # MIDI messages
        'midi-in-1':        0x00000100,
        'midi-out-1':       0x00000200,
        'midi-in-2':        0x00000400,
        'midi-out-2':       0x00000800,
        # Robot Interface Pack
        'battery-charging': 0x00000000,
        'stereo-connect':   0x00000000,
        'hex-signal':       0x00000000,
    }

    # For internal use.
    box_state_params = {
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

    # supported box states, generates in __init__().
    supported_box_states = []

    #   Firmware versions, represented as %u.%u.%u.
    arm_firmware_version = ''
    dsp_firmware_version = ''
    fpga_firmware_version = ''

    def __init__(self, card):
        super().__init__()
        self.open('/dev/snd/hwC{0}D0'.format(card))
        self.listen()

        args = self.get_array()
        params = self.transact(0, 0, args)

        self.parse_capabilities(params)
        self.parse_supported_clock_sources(params)
        self.parse_supported_sampling_rates(params)
        self.parse_phys_ports(params)
        self.parse_mixer_channels(params)
        self.parse_midi_ports(params)
        self.parse_stream_formation(params)
        self.parse_firmware_versions(params)

    def parse_capabilities(self, params):
        if params[0] & 0x0001:
            self.supported_features['changeable-resp-addr'] = True
        if params[0] & 0x0002:
            self.supported_features['aesebu-xlr']= True
        if params[0] & 0x0004:
            self.supported_features['control-room-mirroring'] = True
            self.supported_box_states.append('control-room')
        if params[0] & 0x0008:
            self.supported_features['spdif-coax'] = True
            self.supported_box_states.append('spdif-pro')
            self.supported_box_states.append('spdif-non-audio')
        if params[0] & 0x0010:
            self.supported_features['dsp'] = True
        if params[0] & 0x0020:
            self.supported_features['fpga'] = True
        if params[0] & 0x0040:
            self.supported_features['phantom-powering'] = True
            self.supported_box_states.append('phantom-powering')
        if params[0] & 0x0080:
            self.supported_features['rx-mapping'] = True
        if params[0] & 0x0100:
            self.supported_features['adjust-input-level'] = True
        if params[0] & 0x0200:
            self.supported_features['spdif-opt'] = True
            self.supported_box_states('spdif-pro')
            self.supported_box_states('spdif-non-audio')
        if params[0] & 0x0400:
            self.supported_features['adat-opt'] = True
        if params[0] & 0x0800:
            self.supported_features['nominal-input'] = True
        if params[0] & 0x1000:
            self.supported_features['nominal-output'] = True
        if params[0] & 0x2000:
            self.supported_features['soft-clip'] = True
            self.supported_box_states('soft-clip')
        if params[0] & 0x4000:
            self.supported_features['robot-hex-input'] = True
            self.supported_box_states('robot-hex-input')
        if params[0] & 0x8000:
            self.supported_features['robot-battery-charge'] = True
            self.supported_box_states('robot-battery-charge')

        # unique features.
        if params[3] is 0x0001200f or params[3] is 0x0000400f:
            self.supported_box_states.append('spdif-non-audio')
            self.supported_box_states.append('control-room')
            self.supported_box_states.append('output-level-bypass')
            self.supported_box_states.append('metering-mode-in')
            self.supported_box_states.append('metering-mode-out')

        # Onyx 1200F supports both of stream mapping to physical ports.
        if params[3] is 0x01200F:
            self.supported_features['tx-mapping'] = True

        # All models may support this.
        self.supported_box_states.append('internal-multiplexer')

        # AudioFire series support nominal inputs/outputs
        if params[3] == 0x00000af2 or \
           params[3] == 0x00000af4 or \
           params[3] == 0x00000af8 or \
           params[3] == 0x00000af9 or \
           params[3] == 0x0000af12 or \
           params[3] == 0x000af12d or \
           params[3] == 0x000af12a:
            self.supported_features['nominal-output'] = True
            self.supported_features['nominal-input'] = True

    def parse_supported_clock_sources(self, params):
        if params[21] & 0x0001:
            self.supported_clock_sources['internal'] = True
        if params[21] & 0x0002:
            self.supported_clock_sources['syt-match'] = True
        if params[21] & 0x0004:
            self.supported_clock_sources['word-clock'] = True
        if params[21] & 0x0008:
            self.supported_clock_sources['spdif'] = True
        if params[21] & 0x0010:
            self.supported_clock_sources['ADAT-1'] = True
        if params[21] & 0x0020:
            self.supported_clock_sources['ADAT-2'] = True
        if params[21] & 0x0040:
            self.supported_clock_sources['continuouos'] = True
        return

    def parse_supported_sampling_rates(self, params):
        for rate in self.supported_sampling_rates:
            if params[38] >= rate and params[39] <= rate:
                self.supported_sampling_rates[rate] = True

    def parse_phys_ports(self, params):
        port_names = (
            'analog', 'spdif', 'adat', 'spdif/adat', 'analog mirroring',
            'headphones', 'I2S', 'guitar', 'piezo guitar', 'guitar string')

        outputs = (params[27] >> 16, params[27] & 0xffff,
                   params[28] >> 16, params[28] & 0xffff,
                   params[29] >> 16, params[29] & 0xffff,
                   params[30] >> 16, params[30] & 0xffff)

        inputs = (params[32] >> 16, params[32] & 0xffff,
                  params[33] >> 16, params[33] & 0xffff,
                  params[34] >> 16, params[34] & 0xffff,
                  params[35] >> 16, params[35] & 0xffff)

        for i in range(params[26]):
            count = outputs[i] & 0xff
            id = outputs[i] >> 8
            if id > len(port_names):
                type = 'dummy'
            else:
                type = port_names[id]
            for j in range(count):
                self.phys_outputs.append(type)

        for i in range(params[31]):
            count = inputs[i] & 0xff
            id = inputs[i] >> 8
            if id > len(port_names):
                type = 'dummy'
            else:
                type = port_names[id]
            for j in range(count):
                self.phys_inputs.append(type)

    def parse_mixer_channels(self, params):
        self.mixer_playback_channels = params[42]
        self.mixer_capture_channels = params[43]

    def parse_midi_ports(self, params):
        self.midi_out_ports = params[36]
        self.midi_in_ports = params[37]

    def parse_stream_formation(self, params):
        self.rx_stream_channels[0] = params[22]
        self.rx_stream_channels[1] = params[45]
        self.rx_stream_channels[2] = params[47]
        self.tx_stream_channels[0] = params[23]
        self.tx_stream_channels[1] = params[46]
        self.tx_stream_channels[2] = params[48]

    def parse_firmware_versions(self, params):
        def get_literal_version(val):
            return '{0}.{1}.{2}'.format((val >> 24) & 0xff, \
                                        (val >> 16) & 0xff, \
                                        (val >>  8) & 0xff)
        self.firmware_versions['DSP'] = get_literal_version(params[40])
        self.firmware_versions['ARM'] = get_literal_version(params[41])
        self.firmware_versions['FPGA'] = get_literal_version(params[44])

    #
    # helper functions
    #
    def get_array(self):
        # The width with 'L' parameter is depending on environment.
        arr = array('L')
        if arr.itemsize is not 4:
            arr = array('I')
            if arr.itemsize is not 4:
                raise RuntimeError('Platform has no representation \
                                    equivalent to quadlet.')
        return arr

    def calculate_vol_from_db(self, db):
        if db <= -144.0:
            return 0x00000000
        else:
            return int(0x01000000 * pow(10, db / 20))

    def calculate_vol_to_db(self, vol):
        if vol == 0:
            return -144.0
        else:
            return 20 * log10(vol / 0x01000000)

    #
    # Category No.0, for hardware information
    #
    def info_get_metering(self):
        args = self.get_array()
        params = self.transact(0, 1, args)

        # params[00]: status: 
        # params[01]: S/PDIF detection
        # params[02]: ADAT detection
        # params[03]: reserved
        # params[04]: reserved
        # params[05]: the number of data for output meters
        # params[06]: the number of data for input meters
        # params[07]: reserved
        # params[08]: reserved
        # params[09-xx]: output meters, linear value from 0 to 0x7fffff00 (left)
        # params[xx-yy]: input meters, linear value from 0 to 0x7fffff00 (left)

        count = params[5] + params[6]
        for i in range(count):
            if params[9 + i] == 0:
                params[9 + i] = -144.0
            else:
                params[9 + i] = 20 * log10(params[9 + i] / 0x80000000)

        return params

    def info_set_resp_addr(self, addr):
        if self.supported_features['changeable-resp-addr'] is False:
            raise RuntimeError('Unsupported operation')
        args = self.get_array()
        args.append((addr >> 24) & 0xffffffff)
        args.append(addr         & 0xffffffff)
        self.transact(0, 2, args)

    def info_read_session_data(self, offset, quadlets):
        args = self.get_array()
        args.append(offset)
        args.append(quadlets)
        params = self.transact(0, 3, args)
        return params

    def info_get_debug_info(self):
        args = self.get_array()
        params = self.transact(0, 4, args)

        # params[00]: isochronous stream 1 flushed
        # params[01]: isochronous stream 1 underruns
        # params[02]: firewire3 control
        # params[03]: firewire3 control written
        # params[04-15]: data
        return params

    def info_test_dsp(self, value):
        args = self.get_array()
        args.append(value)
        params = self.transact(0, 5, args)
        return params[0]

    def info_test_arm(self, value):
        args = self.get_array()
        args.append(value)
        params = self.transact(0, 6, args)
        return params[0]

    #
    # Category No.1, for flash commands
    #
    def flash_erase(self, offset):
        args = self.get_array()
        args.append(offset)
        self.transact(1, 0, args)

    def flash_read_block(self, offset, quadlets):
        args = self.get_array()
        args.append(offset)
        args.append(quadlets)
        params = self.transact(1, 1, args)
        return params

    def flash_write_block(self, offset, data):
        args = self.get_array()
        args.append(offset)
        args.append(len(data))
        for datum in data:
            args.append(datum)
        self.transact(1, 2, args)

    def flash_get_status(self):
        args = self.get_array()
        self.transact(1, 3, args)
        # return status means it.

    def flash_get_session_offset(self):
        args = self.get_array()
        params = self.transact(1, 4, args)
        return params[0]

    def flash_lock(self, lock):
        if self.supported_features['dsp'] is True:
            raise RuntimeError('Unsupported operation')
        args = self.get_array()
        if lock is not 0:
            args.append(1)
        else:
            args.append(0)
        self.transact(1, 5, args)

    #
    # Category No.2, for transmission control commands
    #
    def transmit_set_mode(self, mode):
        args = self.get_array()
        if mode == 'windows':
            args.append(0)
        elif mode == 'iec61883-6':
            args.append(1)
        else:
            raise ValueError('Invalid argument for transmission mode')
        self.transact(2, 0, args)

    def transmit_set_fw_hdmi(self, playback_drop, record_stretch, serial_bps,
                             serial_data_format):
        # ratio (1/2/4)
        if ((1, 2, 4).count(playback_drop)) is not 1:
            raise ValueError('Invalid argument for playback drop')
        # ratio (1/2/4)
        if ((1, 2, 4).count(record_stretch_ratio)) is not 1:
            raise ValueError('Invalid argument for record stretch')
        # 16 or 24
        if ((16, 24).count(serial_bps)) is not 1:
            raise ValueError('Invalid argument for serial bits per second')
        if (('lest-adjusted', 'i2s').count(serial_data_format)) is not 1:
            raise ValueError('Invalid argument for serial data format')

        args = self.get_array()
        args.append(playback_drop)
        args.append(record_stretch)
        args.append(serial_bps)
        args.append(serial_data_format)
        self.transact(2, 4, args)

    #
    # Category No.3, for hardware control commands
    #
    def hwctl_set_clock(self, rate, source, reset):
        sources = ('internal', 'syt-match', 'word-clock', 'spdif', 'ADAT-1',
                'ADAT-2', 'continuous')
        if self.get_property('streaming') == True:
            raise RuntimeError('Packet streaming is running')
        if self.supported_sampling_rates.get(rate) == None:
            raise ValueError('Invalid argument for sampling rate')
        if sources.count(source) == 0:
            raise ValueError('Invalid argument for source of clock')
        if reset > 0:
            reset = 0x80000000
        args = self.get_array()
        args.append(rate)
        args.append(sources.index(source))
        args.append(reset)
        self.transact(3, 0, args)

    def hwctl_get_clock(self):
        args = self.get_array()
        params = self.transact(3, 1, args)
        if params[0] == 0:
            src = 'internal'
        elif params[0] == 1:
            src = 'syt-match'
        elif params[0] == 2:
            src = 'word-clock'
        elif params[0] == 3:
            src = 'spdif'
        elif params[0] == 4:
            src = 'ADAT-1'
        elif params[0] == 5:
            src = 'ADAT-2'
        elif params[0] == 6:
            src = 'continuous'
        else:
            raise IOError
        if self.supported_sampling_rates.get(params[1]) == None:
            raise IOError
        return (params[1], src)

    def hwctl_set_box_states(self, states):
        enable = 0
        disable = 0
        for name,state in states:
            # Check supported or not.
            if self.supported_box_states.count(name) is not 1:
                continue
            shift   = self.box_state_params[name][0]
            values  = self.box_state_params[name][1]
            value = values.index(state)
            if value is 0:
                disabled |= (1 << shift)
            else:
                enabled |= (1 << shift)

        args = self.get_array()
        args.append(enabled)
        args.append(disabled)
        self.transact(3, 3, args)

    def hwctl_get_box_states(self):
        args = self.get_array()
        params = self.transact(3, 4, args)
        state = params[0]

        states = {}
        for name,params in self.box_state_params.items():
            shift = params[0]
            values = params[1]
            if self.supported_box_states.count(name) is not 1:
                continue
            index = (state >> shift) & 0x01
            states[name] = values[index]
        return states

    # Not for all of models
    def hwctl_blink_leds(self):
        args = self.get_array()
        self.transact(3, 6, args)

    def hwctl_reconnect_phy(self):
        args = self.get_array()
        self.transact(3, 7, args)

    def hwctl_set_continuous_clock(self, continuous_rate):
        if self.supported_clock_sources['continuous'] is False:
            raise RuntimeError('Unsupported operation')
        if self.get_property('streaming') == True:
            raise RuntimeError('Packet streaming is running')
        args = self.get_array()
        args.append(continuous_rate * 512 // 1500)
        self.transact(3, 8, args)

    #
    # Category No.4, for physical output multiplexer commands
    #
    def phys_output_set_param(self, operation, channel, value):
        if channel >= len(self.phys_outputs):
            raise ValueError('Invalid argument for physical output channel')
        if operation is 'gain':
            cmd = 0
            value = self.calculate_vol_from_db(value)
        elif operation is 'mute':
            cmd = 2
            if value > 0:
                value = 1
        elif operation is 'nominal':
            if self.supported_features['nominal-output'] is False:
                raise RuntimeError('Unsupported operation')
            cmd = 8
            if value > 0:
                value = 2
        else:
            raise ValueError('Invalid argument for operation.')
        args = self.get_array()
        args.append(channel)
        args.append(value)
        self.transact(4, cmd, args)

    def phys_output_get_param(self, operation, channel):
        if channel >= len(self.phys_outputs):
            raise ValueError('Invalid argument for physical output channel')
        if operation is 'gain':
            cmd = 1
        elif operation is 'mute':
            cmd = 3
        elif operation is 'nominal':
            if self.supported_features['nominal-output'] is False:
                raise RuntimeError('Unsupported operation')
            cmd = 9
        else:
            raise ValueError('Invalid argument for operation.')
        args = self.get_array()
        args.append(channel)
        params = self.transact(4, cmd, args)
        if operation is 'gain':
            params[1] = self.calculate_vol_to_db(params[1])
        if operation is 'nominal':
            if params[1] == 2:
                params[1] = 1
        return params[1]

    #
    # Category No.5, for physical input multiplexer commands
    #
    def phys_input_set_param(self, operation, channel, value):
        if self.supported_features['nominal-input'] is False:
            raise RuntimeError('Unsupported operation')
        if channel >= len(self.phys_inputs):
            raise ValueError('Invalid argument for physical input channel')
        if operation is 'nominal':
            cmd = 8
            if value > 0:
                value = 2
        else:
            raise ValueError('Invalid argument for operation.')
        args = self.get_array()
        args.append(channel)
        args.append(value)
        self.transact(5, cmd, args)

    #
    # Category No.6, for playback stream multiplexer commands
    #
    def playback_set_param(self, operation, channel, value):
        if channel >= self.mixer_playback_channels:
            raise ValueError('Invalid argument for mixer playback channel')
        if operation is 'gain':
            cmd = 0
            value = self.calculate_vol_from_db(value)
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
        args = self.get_array()
        args.append(channel)
        args.append(value)
        self.transact(6, cmd, args)

    def playback_get_param(self, operation, channel):
        if channel >= self.mixer_playback_channels:
            raise ValueError('Invalid argument for mixer playback channel')
        if operation is 'gain':
            cmd = 1
        elif operation is 'mute':
            cmd = 3
        elif operation is 'solo':
            cmd = 5
        else:
            raise ValueError('Invalid argument for operation.')
        args = self.get_array()
        args.append(channel)
        params = self.transact(6, cmd, args)
        if operation is 'gain':
            params[1] = calculate_vol_to_db(params[1])
        return params[1]

    #
    # Category No.7, for capture stream multiplexer commands
    #
    # nothing

    #
    # Category No.8, for input monitoring multiplexer commands
    #
    def monitor_set_param(self, operation, input, output, value):
        if input >= len(self.phys_inputs) or output >= len(self.phys_outputs):
            raise ValueError('Invalid argument for physical in/out channels')
        if operation is 'gain':
            cmd = 0
            value = self.calculate_vol_from_db(value)
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
        args = self.get_array()
        args.append(input)
        args.append(output)
        args.append(value)
        self.transact(8, cmd, args)

    def monitor_get_param(self, operation, input, output):
        if input >= len(self.phys_inputs) or output >= len(self.phys_outputs):
            raise ValueError('Invalid argument for physical in/out channels')
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
        args = self.get_array()
        args.append(input)
        args.append(output)
        params = self.transact(8, cmd, args)
        if operation is 'gain':
            params[2] = calculate_vol_to_db(params[2])
        return params[2]

    #
    # Category No.9, for input/output configuration commands
    #
    def ioconf_set_control_room_mirroring(self, output_pair):
        if self.supported_features['control-room-mirroring'] is False:
            raise RuntimeError('Unsupported operation')
        if output_pair >= len(self.phys_outputs) or output_pair % 2:
            raise ValueError('Invalid argument for physical output pair')
        args = self.get_array()
        args.append(output_pair)
        self.transact(9, 0, args)

    def ioconf_get_control_room_mirroring(self):
        if self.supported_features['control-room-mirroring'] is False:
            raise RuntimeError('Unsupported operation')
        args = self.get_array()
        params = self.transact(9, 1, args)
        if params[0] >= len(self.phys_outputs):
            raise ValueError('Invalid argument for physical output pair')
        return params[0]

    def ioconf_set_digital_input_mode(self, mode):
        modes = ('spdif-coax', 'aesebu-xlr', 'spdif-opt', 'adat-opt')
        if modes.count(mode) is 0 or self.supported_features[mode] is False:
            raise ValueError('Invalid argument for digital input mode')
        args = self.get_array()
        args.append(modes.index(mode))
        params = self.transact(9, 2, args)

    def ioconf_get_digital_input_mode(self):
        args = self.get_array()
        params = self.transact(9, 3, args)
        if params[0] == 0:
            mode = 'spdif-coax'
        elif params[1] == 1:
            mode = 'aesebu-xlr'
        elif params[2] == 2:
            mode = 'spdif-opt'
        elif params[3] == 3:
            mode = 'adat-opt'
        else:
            raise IOError
        if self.supported_features[mode] is False:
            raise IOError
        return mode

    def ioconf_set_phantom_powering(self, state):
        if self.supported_features['phantom-powering'] is False:
            raise RuntimeError('Unsupported operation')
        if state > 0:
            state = 1
        args = self.get_array()
        args.append(state)
        self.transact(9, 4, args)

    def ioconf_get_phantom_powering(self):
        if self.supported_features['phantom-powering'] is False:
            raise RuntimeError('Unsupported operation')
        args = self.get_array()
        param = self.transact(9, 5, args)
        return param[0]

    def ioconf_set_stream_mapping(self, rx_maps, tx_maps):
        if self.supported_features['rx-mapping'] is False and len(rx_maps) > 0:
            raise RuntimeError('Unsupported operation')

        if self.supported_features['tx-mapping'] is False and len(tx_maps) > 0:
            raise RuntimeError('Unsupported operation')
        args = self.get_array()
        params = self.transact(9, 7, args)
        rx_map_count = params[2]
        if len(rx_maps) > rx_map_count:
            ValueError('Invalid argument for rx stream mapping')
        tx_map_count = params[34]
        if len(tx_maps) > tx_map_count:
            ValueError('Invalid argument for tx stream mapping')
        for i in range(rx_maps):
            params[4 + i] = rx_maps[i]
        for i in range(tx_maps):
            params[36 + i] = tx_maps[i]
        self.transact(9, 6, params)

    def ioconf_get_stream_mapping(self):
        if self.supported_features['rx-mapping'] is False and \
           self.supported_features['tx-mapping'] is False:
            raise RuntimeError('Unsupported operation')

        args = self.get_array()
        param = self.transact(9, 7, args)
        rx_map_count = param[2]
        rx_maps = []
        for i in range(rx_map_count):
            rx_maps.append(param[4 + i])

        tx_map_count = param[34]
        tx_maps = []
        for i in range(tx_map_count):
            tx_maps.append(param[36 + i])

        return (rx_maps, tx_maps)
