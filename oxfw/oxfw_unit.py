import re

from gi.repository import Hinawa

from ta1394.general import AvcGeneral
from ta1394.general import AvcConnection
from ta1394.streamformat import AvcStreamFormatInfo

class OxfwUnit(Hinawa.SndUnit):
    # Public properties
    hw_info = dict.fromkeys(('asic-type', 'asic-id', 'firmware-version'))
    playback_only = False
    supported_sampling_rates = dict.fromkeys(AvcConnection.sampling_rates,
                                             False)
    supported_stream_formats = dict.fromkeys(('playback', 'capture'), [])

    # For private use.
    on_juju = False,

    def __init__(self, path):
        if re.match('/dev/snd/hwC[0-9]*D0', path):
            super().__init__()
            self.open(path)
            self.listen()
        elif re.match('/dev/fw[0-9]*', path):
            # Just using parent class.
            super(Hinawa.FwUnit, self).__init__()
            Hinawa.FwUnit.open(self, '/dev/fw1')
            Hinawa.FwUnit.listen(self)
            self.on_juju = True
        else:
            raise ValueError('Invalid argument for character device')
        self.fcp = Hinawa.FwFcp()
        self.fcp.listen(self)
        self._parse_hardware_info()
        self._parse_supported_sampling_rates()
        self._parse_supported_stream_formats()

    def _parse_hardware_info(self):
        def _read_transaction(addr, quads):
            if self.on_juju:
                req = Hinawa.FwReq()
                return req.read(self, addr, quads)
            return self.read_transact(addr, quads)

        params = _read_transaction(0xfffff0050000, 1)
        val = params[0]
        self.hw_info['asic-type'] = \
            'FW{0}{1}{2}'.format((val >> 28) & 0xf,
                                 (val >> 24) & 0xf,
                                 (val >> 20) & 0xf)
        self.hw_info['firmware-version'] = \
            '{0}.{1}'.format((val >> 8) & 0xf,
                             (val & 0xf))
        params = _read_transaction(0xfffff0090020, 1)
        val = params[0]
        self.hw_info['asic-id'] = \
            bytes([(val >> 24) & 0xff,
                   (val >> 16) & 0xff,
                   (val >>  8) & 0xff,
                   (val >>  0) & 0xff]).decode().rstrip('\0')

    def _parse_supported_sampling_rates(self):
        playback = []
        capture  = []
        # Assume that PCM playback is available for all of models.
        for rate, status in self.supported_sampling_rates.items():
            if AvcConnection.ask_plug_signal_format(self.fcp, 'input', 0, rate):
                playback.append(rate)
        # PCM capture is not always available depending on models.
        for rate, status in self.supported_sampling_rates.items():
            if AvcConnection.ask_plug_signal_format(self.fcp, 'output', 0, rate):
                capture.append(rate)
        if len(capture) == 0:
            self.playback_only = True
        for rate in AvcConnection.sampling_rates:
            if rate in playback or rate in capture:
                self.supported_sampling_rates[rate] = True

    def _parse_supported_stream_formats(self):
        self.supported_stream_formats['playback'] = \
            AvcStreamFormatInfo.get_formats(self.fcp, 'input', 0)
        if len(self.supported_stream_formats['playback']) == 0:
            self._assume_supported_stram_formats('input', 0)

        if not self.playback_only:
            self.supported_stream_formats['capture'] = \
                AvcStreamFormatInfo.get_formats(self.fcp, 'input', 0)
            if len(self.supported_stream_formats['capture']) == 0:
                self._assume_supported_stram_formats('output', 0)

    def _assume_supported_stram_formats(self, direction, plug):
        fmt = AvcStreamFormatInfo.get_format(self.fcp, 'input', 0)
        for rate, state in self.supported_sampling_rates.items():
            if state == False:
                continue
            assumed = {}
            assumed['sampling-rate'] = rate
            assumed['rate-control'] = fmt['rate-control']
            assumed['formation'] = fmt['formation']
            if direction == 'input':
                self.supported_stream_formats['playback'].append(assumed)
            else:
                self.supported_stream_formats['capture'].append(assumed)

    def set_stream_formats(self, playback, capture):
        if playback not in self.supported_stream_formats['playback']:
            raise ValueError('Invalid argument for playback stream format')
        if not self.playback_only:
            if self.playback_only and capture != None:
                raise ValueError('This unit is playback only')
            if capture not in self.supported_stream_formats['capture']:
                raise ValueError('Invalid argument for capture stream format')
            if playback['sampling-rate'] != capture['sampling-rate']:
                raise ValueError('Sampling rate mis-match between playback and capture')
        AvcStreamFormatInfo.set_format(self.fcp, 'input', 0, playback)
        if not self.playback_only:
            AvcStreamFormatInfo.set_format(self.fcp, 'output', 0, capture)
