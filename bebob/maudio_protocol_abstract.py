from abc import ABCMeta, abstractmethod

from ta1394.general import AvcConnection

__all__ = ['MaudioProtocolAbstract']

class MaudioProtocolAbstract(metaclass=ABCMeta):
    _METER_LABELS = ('analog-in-1', 'analog-in-2',
                     'digital-in-1', 'digital-in-2',
                     'analog-out-1', 'analog-out-2',
                     'analog-out-3', 'analog-out-4',
                     'analog-out-5', 'analog-out-6',
                     'analog-out-7', 'analog-out-8',
                     'digital-out-1', 'digital-out-2',
                     'headphone-out-1', 'headphone-out-2',
                     'headphone-out-3', 'headphone-out-4',
                     'switch-0', 'switch-1'
                     'rotery-0', 'rotery-1', 'rotery-2'
                     'rate', 'sync')

    def __init__(self, unit, debug):
        self._unit = unit

    # For input gains.
    @abstractmethod
    def get_input_labels(self):
        pass
    @abstractmethod
    def set_input_gain(self, target, ch, db):
        pass
    @abstractmethod
    def get_input_gain(self, target, ch):
        pass

    # For input LR balance.
    def get_input_balance_labels(self):
        pass
    def set_input_balance(self, target, ch, balance):
        pass
    def get_input_balance(self, target, ch):
        pass

    # For output volumes.
    @abstractmethod
    def get_output_labels(self):
        pass
    @abstractmethod
    def set_output_volume(self, target, ch, db):
        pass
    @abstractmethod
    def get_output_volume(self, target, ch):
        pass

    # For aux inputs.
    @abstractmethod
    def get_aux_input_labels(self):
        pass
    @abstractmethod
    def set_aux_input(self, target, ch, db):
        pass
    @abstractmethod
    def get_aux_input(self, target, ch):
        pass

    # For aux volume.
    @abstractmethod
    def set_aux_volume(self, ch, db):
        pass
    @abstractmethod
    def get_aux_volume(self, ch):
        pass

    # For headphone volume.
    @abstractmethod
    def get_headphone_labels(self):
        pass
    @abstractmethod
    def set_headphone_volume(self, target, ch, db):
        pass
    @abstractmethod
    def get_headphone_volume(self, target, ch):
        pass

    # For mixer routing.
    @abstractmethod
    def get_mixer_labels(self):
        pass
    @abstractmethod
    def get_mixer_source_labels(self):
        pass
    @abstractmethod
    def set_mixer_routing(self, target, source, enable):
        pass
    @abstractmethod
    def get_mixer_routing(self, target, source):
        pass

    # For headphone source.
    @abstractmethod
    def get_headphone_source_labels(self, target):
        pass
    @abstractmethod
    def set_headphone_source(self, target, source):
        pass
    @abstractmethod
    def get_headphone_source(self, target):
        pass

    # For output source.
    @abstractmethod
    def get_output_source_labels(self, target):
        pass
    @abstractmethod
    def set_output_source(self, target, source):
        pass
    @abstractmethod
    def get_output_source(self, target):
        pass

    # For metering.
    def get_meter_labels(self):
        return self._METER_LABELS
    @abstractmethod
    def get_meters(self):
        pass

    # For source of clock.
    @abstractmethod
    def get_clock_source_labels(self):
        pass
    @abstractmethod
    def set_clock_source(self, src):
        pass
    @abstractmethod
    def get_clock_source(self):
        pass

    # For sampling rate.
    def get_sampling_rate_labels(self):
        rates = []
        for rate in AvcConnection.sampling_rates:
            if not AvcConnection.ask_plug_signal_format(self._unit.fcp,
                                                        'input', 0, rate):
                continue
            if not AvcConnection.ask_plug_signal_format(self._unit.fcp,
                                                        'output', 0, rate):
                continue
            rates.append(rate)
        return rates
    def set_sampling_rate(self, rate):
        if self._unit.get_property('streaming'):
            raise ValueError('Packet streaming already runs.')
        if rate not in self.get_sampling_rate_labels():
            raise ValueError('Invalid argument for sampling rate')
        old_timeout = self._unit.fcp.get_property('timeout')
        # The unit tends to respond with larger interval from these requests.
        self._unit.fcp.set_property('timeout', 500)
        AvcConnection.set_plug_signal_format(self._unit.fcp, 'input', 0, rate)
        AvcConnection.set_plug_signal_format(self._unit.fcp, 'output', 0, rate)
        self._unit.fcp.set_property('timeout', old_timeout)
    @abstractmethod
    def get_sampling_rate(self):
        pass
