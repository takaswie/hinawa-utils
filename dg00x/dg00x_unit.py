import re
from array import array

import gi
gi.require_version('Hinawa', '1.0')
from gi.repository import Hinawa

__all__ = ['Dg00xUnit']

class Dg00xUnit(Hinawa.SndDg00x):
    supported_sampling_rates = (44100, 48000, 88200, 96000)
    supported_clock_sources = ('Internal', 'S/PDIF', 'ADAT', 'Word-clock')
    supported_optical_interfaces = ('ADAT', 'S/PDIF')

    def __init__(self, path):
        if re.match('/dev/snd/hwC[0-9]*D0', path):
            super().__init__()
            self.open(path)
            if self.get_property('type') != 5:
                raise ValueError('The character device is not for Dg00x unit')
            self.listen()
        elif re.match('/dev/fw[0-9]*', path):
            # Just using parent class.
            super(Hinawa.FwUnit, self).__init__()
            Hinawa.FwUnit.open(self, path)
            Hinawa.FwUnit.listen(self)
        else:
            raise ValueError('Invalid argument for character device')

    def _read_transaction(self, addr, quads):
        req = Hinawa.FwReq()
        return req.read(self, addr, quads)

    def _write_transaction(self, addr, data):
        req = Hinawa.FwReq()
        return req.write(self, addr, data)

    def set_clock_source(self, source):
        if source not in self.supported_clock_sources:
            raise ValueError('Invalid argument for clock source.')
        data = array('I')
        data.append(self.supported_clock_sources.index(source))
        self._write_transaction(0xffffe00000118, data)
    def get_clock_source(self):
        data = self._read_transaction(0xffffe0000118, 1)
        if data[0] >= len(self.supported_clock_sources):
            raise OSError('Unexpected value for clock source.')
        return self.supported_clock_sources[data[0]]

    def set_local_sampling_rate(self, rate):
        if rate not in self.supported_sampling_rates:
            raise ValueError('Invalid argument for local sampling rate.')
        data = array('I')
        data.append(self.supported_sampling_rates.index(rate))
        self._write_transaction(0xffffe00000118, data)
    def get_local_sampling_rate(self):
        data = self._read_transaction(0xffffe0000118, 1)
        if data[0] >= len(self.supported_sampling_rates):
            raise OSError('Unexpected value for local sampling rate.')
        return self.supported_sampling_rates[data[0]]

    def get_external_sampling_rate(self):
        data = self._read_transaction(0xffffe0000114, 1)
        if data[0] >= len(self.supported_sampling_rates):
            raise OSError('Unexpected value for external sampling rate.')
        return self.supported_sampling_rates[data[0]]
    def check_external_input(self):
        data = self._read_transaction(0xffffe000012c)
        return data[0] > 0

    def set_opt_iface(self, mode):
        if mode not in self.supported_optical_interfaces:
            raise ValueError('Invalid argument for optical interface mode.')
        data = array('I')
        data.append(self.supported_optical_interfaces.index(mode))
        self._write_transaction(0xffffe000011c, data)
    def get_opt_iface(self):
        data = self._read_transaction(0xffffe000011c, 1)
        if data[0] >= len(self.supported_optical_interfaces):
            raise ValueError('Unexpected value for optical interface mode.')
        return self.supported_optical_interfaces[data[0]]

    def set_mixer_mode(self, mode):
        if mode > 0:
            mode = 1
        else:
            mode = 0
        data = array('I')
        data.append(mode)
        self._write_transaction(0xffffe0000124, data)
    def get_mixer_mode(self):
        data =self._read_transaction(0xffffe0000124, 1)
        return (data[0] > 0)
