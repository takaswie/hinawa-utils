import gi
from struct import unpack, pack

gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from bebob.maudio_protocol_abstract import MaudioProtocolAbstract

from ta1394.general import AvcConnection
from ta1394.audio import AvcAudio

__all__ = ['MaudioProtocolSpecial']

class MaudioProtocolSpecial(MaudioProtocolAbstract):
    BASE_ADDR = 0xffc700700000
    _IDS = (
        0x010071,   # Firewire 1814
        0x010091,   # ProjectMix I/O
    )

    _INPUT_LABELS = (
        'stream-1/2', 'stream-3/4',
        'analog-1/2', 'analog-3/4', 'analog-5/6', 'analog-7/8',
        'spdif-1/2', 'adat-1/2', 'adat-3/4', 'adat-5/6', 'adat-7/8',
    )

    _OUTPUT_LABELS = ('analog-1/2', 'analog-3/4')

    _HP_LABELS = ('headphone-1/2', 'headphone-3/4')

    _MIXER_LABELS = ('mixer-1/2', 'mixer-3/4')

    _HP_SOURCE_LABELS = ('mixer-1/2', 'mixer-3/4', 'aux-1/2')

    _METERING_LABELS = (
        'analog-in-1', 'analog-in-2', 'analog-in-3', 'analog-in-4',
        'analog-in-5', 'analog-in-6', 'analog-in-7', 'analog-in-8',
        'spdif-in-1', 'spdif-in-2',
        'adat-in-1', 'adat-in-2', 'adat-in-3', 'adat-in-4',
        'adat-in-5', 'adat-in-6', 'adat-in-7', 'adat-in-8',
        'analog-out-1', 'analog-out-2',
        'analog-out-3', 'analog-out-4',
        'spdif-out-1', 'spdif-out-2',
        'adat-out-1', 'adat-out-2', 'adat-out-3', 'adat-out-4',
        'adat-out-5', 'adat-out-6', 'adat-out-7', 'adat-out-8',
        'headphone-out-1', 'headphone-out-2',
        'headphone-out-3', 'headphone-out-4',
        'aux-out-1', 'aux-out-2')

    # LR balance: 0x40-60
    # Write 32 bit, upper 16bit for left channel and lower 16bit for right.
    # The value is between 0x800(L) to 0x7FFE(R) as the same as '10.3.3 LR
    # Balance Control' in 'AV/C Audio Subunit Specification 1.0 (1394TA
    # 1999008)'.

    def __init__(self, unit, debug):
        if unit.model_id not in self._IDS:
            raise OSError('Not supported')

        super().__init__(unit, debug)

        # For process local cache.
        self._cache = bytearray(160)
        # For permanent cache.
        guid = self._unit.get_property('guid')
        self._filepath = '/tmp/hinawa-{0:08x}'.format(guid)
        self._load_cache()

    # Read transactions are not allowed. We cache data.
    def _load_cache(self):
        try:
            cache = bytearray(160)
            with open(self._filepath, 'r') as f:
                for i, line in enumerate(f):
                    cache[i] = int(line.strip(), base=16)
        except Exception as e:
            # This is initial value.
            cache = [
                0x00, 0x00, 0x00, 0x00, # gain of inputs from stream 1/2
                0x00, 0x00, 0x00, 0x00, # gain of inputs from stream 3/4
                0x00, 0x00, 0x00, 0x00, # volume of outputs to analog 1/2
                0x00, 0x00, 0x00, 0x00, # volume of outputs to analog 3/4
                0x00, 0x00, 0x00, 0x00, # gain of inputs from analog 1/2
                0x00, 0x00, 0x00, 0x00, # gain of inputs from analog 3/4
                0x00, 0x00, 0x00, 0x00, # gain of inputs from analog 5/6
                0x00, 0x00, 0x00, 0x00, # gain of inputs from analog 7/8
                0x00, 0x00, 0x00, 0x00, # gain of inputs from spdif 1/2
                0x00, 0x00, 0x00, 0x00, # gain of inputs from adat 1/2
                0x00, 0x00, 0x00, 0x00, # gain of inputs from adat 3/4
                0x00, 0x00, 0x00, 0x00, # gain of inputs from adat 5/6
                0x00, 0x00, 0x00, 0x00, # gain of inputs from adat 7/8
                0x00, 0x00, 0x00, 0x00, # volume of outputs to aux 1/2
                0x00, 0x00, 0x00, 0x00, # volume of outputs to headphone 1/2
                0x00, 0x00, 0x00, 0x00, # volume of outputs to headophone 3/4
                0x7F, 0xFE, 0x80, 0x00, # balance of inputs from analog 1/2
                0x7F, 0xFE, 0x80, 0x00, # balance of inputs from analog 3/4
                0x7F, 0xFE, 0x80, 0x00, # balance of inputs from analog 5/6
                0x7F, 0xFE, 0x80, 0x00, # balance of inputs from analog 7/8
                0x7F, 0xFE, 0x80, 0x00, # balance of inputs from spdif 1/2
                0x7F, 0xFE, 0x80, 0x00, # balance of inputs from adat 1/2
                0x7F, 0xFE, 0x80, 0x00, # balance of inputs from adat 3/4
                0x7F, 0xFE, 0x80, 0x00, # balance of inputs from adat 5/6
                0x7F, 0xFE, 0x80, 0x00, # balance of inputs from adat 7/8
                0x80, 0x00, 0x80, 0x00, # inputs of stream 1/2 to aux
                0x80, 0x00, 0x80, 0x00, # inputs of stream 3/4 to aux
                0x80, 0x00, 0x80, 0x00, # inputs of analog 1/2 to aux
                0x80, 0x00, 0x80, 0x00, # inputs of analog 3/4 to aux
                0x80, 0x00, 0x80, 0x00, # inputs of analog 5/6 to aux
                0x80, 0x00, 0x80, 0x00, # inputs of analog 7/8 to aux
                0x80, 0x00, 0x80, 0x00, # inputs of spdif 1/2 to aux
                0x80, 0x00, 0x80, 0x00, # inputs of adat 1/2 to aux
                0x80, 0x00, 0x80, 0x00, # inputs of adat 3/4 to aux
                0x80, 0x00, 0x80, 0x00, # inputs of adat 5/6 to aux
                0x80, 0x00, 0x80, 0x00, # inputs of adat 7/8 to aux
                0x00, 0x00, 0x00, 0x00, # inputs of analog/digital for mixer
                0x00, 0x00, 0x00, 0x09, # inputs of stream for mixer
                0x00, 0x02, 0x00, 0x01, # source for headphone out 1/2 and 3/4
                0x00, 0x00, 0x00, 0x00] # source for analog out 1/2 and 3/4
        finally:
            self._write_data(0, cache)

    def _write_data(self, offset, data):
        # Write to the unit.
        count = 0
        req = Hinawa.FwReq()
        while True:
            try:
                req.write(self._unit, self.BASE_ADDR + offset, data)
                break
            except:
                if count > 10:
                    raise OSError('Fail to communicate to the unit.')
                count += 1
        # Refresh process cache.
        for i, datum in enumerate(data):
            self._cache[offset + i] = datum
        # Refresh permanent cache.
        with open(self._filepath, 'w+') as fd:
            for i, datum in enumerate(self._cache):
                fd.write('{0:02x}\n'.format(datum))

    def _set_volume(self, offset, db):
        if offset > len(self._cache):
            raise ValueError('Invalid argument for offset on address space')
        data = AvcAudio.build_data_from_db(db)
        self._write_data(offset, data)
    def _get_volume(self, offset):
        if offset > len(self._cache):
            raise ValueError('Invalid argument for offset on address space')
        return AvcAudio.parse_data_to_db(self._cache[offset:offset + 2])

    def get_input_labels(self):
        return self._INPUT_LABELS
    def _get_input_gain_offset(self, target, ch):
        if target not in self._INPUT_LABELS:
            raise ValueError('invalid argument for input stereo pair')
        if ch > 1:
            raise ValueError('Invalid argument for stereo pair channel')
        offset = self._INPUT_LABELS.index(target) * 4
        if offset >= 8:
            offset += 8
        return offset + ch * 2
    def set_input_gain(self, target, ch, db):
        offset = self._get_input_gain_offset(target, ch)
        self._set_volume(offset, db)
    def get_input_gain(self, target, ch):
        offset = self._get_input_gain_offset(target, ch)
        return self._get_volume(offset)

    def get_input_balance_labels(self):
        labels = []
        for label in self._INPUT_LABELS:
            if label.find('stream-') == 0:
                continue
            labels.append(label)
        return labels
    def set_input_balance(self, target, ch, balance):
        if target not in self._INPUT_LABELS:
            raise ValueError('invalid argument for input stereo pair')
        offset = (self._INPUT_LABELS.index(target) - 2 + 16) * 4 + ch * 2
        data = AvcAudio.build_data_from_db(balance)
        self._write_status(offset, data)
    def get_input_balance(self, target, ch):
        if target not in self._INPUT_LABELS:
            raise ValueError('invalid argument for input stereo pair')
        offset = (self._INPUT_LABELS.index(target) - 2 + 16) * 4 + ch * 2
        data = self._cache[offset:offset + 2]
        return AvcAudio.parse_data_to_db(data)

    def get_output_labels(self):
        return self._OUTPUT_LABELS
    def _set_output_volume_offset(self, target, ch):
        if target not in self._OUTPUT_LABELS:
            raise ValueError('invalid argument for output stereo pair')
        if ch > 1:
            raise ValueError('Invalid argument for stereo pair channel')
        return 8 + self._OUTPUT_LABELS.index(target) * 4 + ch * 2
    def set_output_volume(self, target, ch, value):
        offset = self._set_output_volume_offset(target, ch)
        self._set_volume(offset, value)
    def get_output_volume(self, target, ch):
        offset = self._set_output_volume_offset(target, ch)
        return self._get_volume(offset)

    def _get_aux_volume_offset(self, ch):
        if ch > 1:
            raise ValueError('Invalid argument for stereo pair channel')
        return 52 + ch * 2
    def set_aux_volume(self, ch, value):
        offset = self._get_aux_volume_offset(ch)
        self._set_volume(offset, value)
    def get_aux_volume(self, ch):
        offset = self._get_aux_volume_offset(ch)
        return self._get_volume(offset)

    def get_headphone_labels(self):
        return self._HP_LABELS
    def _get_headphone_volume_offset(self, target, ch):
        if target not in self._HP_LABELS:
            raise ValueError('invalid argument for heaphone stereo pair')
        if ch > 1:
            raise ValueError('Invalid argument for stereo pair channel')
        return 56 + self._HP_LABELS.index(target) * 4 + ch * 2
    def set_headphone_volume(self, target, ch, value):
        offset = self._get_headphone_volume_offset(target, ch)
        self._set_volume(offset, value)
    def get_headphone_volume(self, target, ch):
        offset = self._get_headphone_volume_offset(target, ch)
        return self._get_volume(offset)

    def get_aux_input_labels(self):
        return self._INPUT_LABELS
    def _get_aux_input_offset(self, target, ch):
        if target not in self._INPUT_LABELS:
            raise ValueError('Invalid argument for input stereo pair')
        if ch > 1:
            raise ValueError('Invalid argument for stereo pair channel')
        return 104 + self._INPUT_LABELS.index(target) * 4 + ch * 2
    def set_aux_input(self, target, ch, value):
        offset = self._get_aux_input_offset(target, ch)
        self._set_volume(offset, value)
    def get_aux_input(self, target, ch):
        offset = self._get_aux_input_offset(target, ch)
        return self._get_volume(offset)

    def get_mixer_labels(self):
        return self._MIXER_LABELS
    def get_mixer_source_labels(self):
        return self._INPUT_LABELS
    def _calculate_mixer_input_bit(self, mixer, source):
        if mixer not in self._MIXER_LABELS:
            raise ValueError('invalid argument for mixer stereo pair')
        if source not in self._INPUT_LABELS:
            raise ValueError('Invalid argument for source stereo pair')
        if source.find('stream') == 0:
            pos = 0
            if source == 'stream-3/4':
                pos = 2
            pos = pos + self._MIXER_LABELS.index(mixer)
        else:
            if source.find('analog') == 0:
                pos = self._MIXER_LABELS.index(mixer) * 4
                pos = pos + self_._INPUT_LABELS.index(source) - 2
            else:
                pos = 16 + (self._INPUT_LABELS.index(source) - 6) * 2
                pos = pos + self._MIXER_LABELS.index(mixer)
        return pos
    def _get_mixer_offset(self, source):
        if source.find('stream') == 0:
            offset = 148
        else:
            offset = 142
        return offset
    def set_mixer_routing(self, mixer, source, enable):
        pos = self._calculate_mixer_input_bit(mixer, source)
        offset = self._get_mixer_offset(source)
        val = unpack('>I', self._cache[offset:offset + 4])[0]
        if enable > 0:
            val |= (1 << pos)
        else:
            val &= ~(1 << pos)
        data = pack('>I', val)
        self._write_data(offset, data)
    def get_mixer_routing(self, mixer, source):
        pos = self._calculate_mixer_input_bit(mixer, source)
        offset = self._get_mixer_offset(source)
        val = unpack('>I', self._cache[offset:offset + 4])[0]
        return bool(val & (1 << pos))

    def get_headphone_source_labels(self, target):
        return self._HP_SOURCE_LABELS
    def set_headphone_source(self, target, source):
        if target not in self._HP_LABELS:
            raise ValueError('Invalid argument for output stereo pair')
        if source not in self._HP_SOURCE_LABELS:
            raise ValueError('Invalid argument for headphone source')
        index = (self._HP_LABELS.index(target) + 1) % 2
        pos = self._HP_SOURCE_LABELS.index(source)
        offset = 152
        vals = list(unpack('>2H', self._cache[offset:offset + 4]))
        vals[index] = 1 << pos
        data = pack('>2H', vals[0], vals[1])
        self._write_data(offset, data)
    def get_headphone_source(self, target):
        if target not in self._HP_LABELS:
            raise ValueError('Invalid argument for output stereo pair')
        index = (self._HP_LABELS.index(target) + 1) % 2
        offset = 152
        vals = unpack('>2H', self._cache[offset:offset + 4])
        for i, source in enumerate(self._HP_SOURCE_LABELS):
            if vals[index] & (1 << i):
                return source
        else:
            raise IOError('Unexpected state of register cache')

    def _calculate_output_source_bit(self, target):
        if target not in self._OUTPUT_LABELS:
            raise ValueError('Invalid argument for output stereo pair')
        return self._OUTPUT_LABELS.index(target)
    def get_output_source_labels(self, target):
        labels = []
        if target not in self._OUTPUT_LABELS:
            raise ValueError('Invalid argument for output stereo pair')
        if target.find('1/2') > 0:
            labels.append('mixer-1/2')
        else:
            labels.append('mixer-3/4')
        labels.append('aux-1/2')
        return labels
    def set_output_source(self, target, source):
        if target not in self._OUTPUT_LABELS:
            raise ValueError('Invalid argument for output stereo pair')
        pos = self._OUTPUT_LABELS.index(target)
        labels = self.get_output_source_labels(target)
        if source not in labels:
            raise ValueError('Invalid argument for output source pair')
        offset = 156
        val = unpack('>I', self._cache[offset:offset + 4])[0]
        if labels.index(source) > 0:
            val |= 1 << pos
        else:
            val &= ~(1 << pos)
        data = pack('>I', val)
        self._write_data(offset, data)
    def get_output_source(self, target):
        if target not in self._OUTPUT_LABELS:
            raise ValueError('Invalid argument for output stereo pair')
        pos = self._OUTPUT_LABELS.index(target)
        labels = self.get_output_source_labels(target)
        offset = 156
        val = unpack('>I', self._cache[offset:offset + 4])[0]
        if not val & (1 << pos):
            return labels[0]
        else:
            return labels[1]

    # 0x0000ffff - 0x7fffffff
    # db = 20 * log10(vol / 0x80000000)
    # vol = 0, then db = -144.0
    # may differs analog-in and the others.
    def get_meters(self):
        meters = {}
        req = Hinawa.FwReq()
        data = req.read(self._unit, self._ADDR_FOR_METERING, 84)
        meters['switch-0'] = data[0]
        meters['rotery-0'] = data[1]
        meters['rotery-1'] = data[2]
        meters['rotery-2'] = data[3]
        data = data[4:]
        for i, label in enumerate(self._METERING_LABELS):
            meters[label] = (data[i * 2] << 8) | data[i * 2 + 1]
        meters['rate'] = AvcConnection.sampling_rates[(data[-1] >> 8) & 0x0f]
        meters['sync'] = (data[-1] & 0x0f) > 0
        return meters

    def get_clock_source_labels(self):
        return ()
    def set_clock_source(self, src):
        print('Not supported. Please use ALSA control interface for this aim.')
    def get_clock_source(self):
        print('Not supported. Please use ALSA control interface for this aim.')

    def get_sampling_rate(self):
        # Current rate is correctly returned from a plug 0 for output direction
        # only.
        return AvcConnection.get_plug_signal_format(self._unit.fcp, 'output', 0)
