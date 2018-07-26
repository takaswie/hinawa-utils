from re import match

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from dg00x.config_rom_parser import Dg00xConfigRomParser

__all__ = ['Dg00xUnit']

class Dg00xUnit(Hinawa.SndDg00x):
    supported_sampling_rates = (44100, 48000, 88200, 96000)
    supported_clock_sources = ('Internal', 'S/PDIF', 'ADAT', 'Word-clock')
    supported_optical_interfaces = ('ADAT', 'S/PDIF')

    def __init__(self, path):
        if match('/dev/snd/hwC[0-9]*D0', path):
            super().__init__()
            self.open(path)
            if self.get_property('type') != 5:
                raise ValueError('The character device is not for Dg00x unit')
            self.listen()
        elif match('/dev/fw[0-9]*', path):
            # Just using parent class.
            super(Hinawa.FwUnit, self).__init__()
            Hinawa.FwUnit.open(self, path)
            Hinawa.FwUnit.listen(self)
        else:
            raise ValueError('Invalid argument for character device')

        parser = Dg00xConfigRomParser()
        info = parser.parse_rom(self.get_config_rom())
        self._model_name = info['model-name']

    def _read_transaction(self, addr, quads):
        req = Hinawa.FwReq()
        return req.read(self, addr, quads)

    def _write_transaction(self, addr, data):
        req = Hinawa.FwReq()
        return req.write(self, addr, data)

    def set_clock_source(self, source):
        if source not in self.supported_clock_sources:
            raise ValueError('Invalid argument for clock source.')
        data = bytearray(4)
        data[3] = self.supported_clock_sources.index(source)
        self._write_transaction(0xffffe0000118, data)
    def get_clock_source(self):
        data = self._read_transaction(0xffffe0000118, 4)
        if data[3] >= len(self.supported_clock_sources):
            raise OSError('Unexpected value for clock source.')
        return self.supported_clock_sources[data[3]]

    def set_local_sampling_rate(self, rate):
        if rate not in self.supported_sampling_rates:
            raise ValueError('Invalid argument for local sampling rate.')
        data = bytearray(4)
        data[3] = self.supported_sampling_rates.index(rate)
        self._write_transaction(0xffffe0000110, data)
    def get_local_sampling_rate(self):
        data = self._read_transaction(0xffffe0000110, 4)
        if data[3] >= len(self.supported_sampling_rates):
            raise OSError('Unexpected value for local sampling rate.')
        return self.supported_sampling_rates[data[3]]

    def get_external_sampling_rate(self):
        data = self._read_transaction(0xffffe0000114, 4)
        if data[3] >= len(self.supported_sampling_rates):
            raise OSError('Unexpected value for external sampling rate.')
        return self.supported_sampling_rates[data[3]]
    def check_external_input(self):
        data = self._read_transaction(0xffffe000012c, 4)
        return data[3] > 0

    def set_opt_iface(self, mode):
        if mode not in self.supported_optical_interfaces:
            raise ValueError('Invalid argument for optical interface mode.')
        data = bytearray(4)
        data[3] = self.supported_optical_interfaces.index(mode)
        self._write_transaction(0xffffe000011c, data)
    def get_opt_iface(self):
        data = self._read_transaction(0xffffe000011c, 4)
        if data[3] >= len(self.supported_optical_interfaces):
            raise ValueError('Unexpected value for optical interface mode.')
        return self.supported_optical_interfaces[data[3]]

    def set_mixer_mode(self, mode):
        if mode > 0:
            mode = 1
        else:
            mode = 0
        data = bytearray(4)
        data[3] = mode
        self._write_transaction(0xffffe0000124, data)
    def get_mixer_mode(self):
        data =self._read_transaction(0xffffe0000124, 4)
        return (data[3] > 0)
