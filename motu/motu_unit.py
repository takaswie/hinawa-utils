from gi.repository import Hinawa

from motu.motu_protocol_v1 import MotuProtocolV1
from motu.motu_protocol_v2 import MotuProtocolV2
from motu.motu_protocol_v3 import MotuProtocolV3

__all__ = ['MotuUnit']

class MotuUnit(Hinawa.SndMotu):
    SUPPORTED_MODELS = {
        0x102802: ('828',       MotuProtocolV1),
        0x101800: ('828mk2',    MotuProtocolV2),
        0x106800: ('828mk3',    MotuProtocolV3),    # FireWire only
        0x100800: ('828mk3',    MotuProtocolV3),    # Hybrid
    }
    _pcm_frame_fetch_mode = ('Enable', 'Disable')

    def __init__(self, path):
        super().__init__()
        self.open(path)
        if self.get_property('type') != 7:
            raise ValueError('The character device is not for Motu unit.')
        self.listen()

        # TODO: apply more intelligent way and pick up more information.
        model_id = self.get_config_rom()[13]
        if model_id >> 24 == 17:
            raise OSError('Unknown model for Motu unit.')
        model_id &= 0x00ffffff
        if model_id in self.SUPPORTED_MODELS:
            self.name = self.SUPPORTED_MODELS[model_id][0]
            self._protocol = self.SUPPORTED_MODELS[model_id][1](self, False)
        else:
            raise OSError('Unsupported model')

    def get_sampling_rates(self):
        return self._protocol.get_supported_sampling_rates()

    def get_sampling_rate(self):
        rate = self._protocol.get_sampling_rate()
        if rate not in self._protocol.get_supported_sampling_rates():
            raise RuntimeError('A bug of protocol abstraction, report this.')

        return rate

    def set_sampling_rate(self, rate):
        if self.get_property('streaming'):
            raise ValueError('Packet streaming already runs.')
        if rate not in self._protocol.get_supported_sampling_rates():
            raise ValueError('Unsupported sampling rate.')
        self._protocol.set_sampling_rate(rate)

    def get_supported_clock_sources(self):
        return self._protocol.get_supported_clock_sources()

    def get_clock_source(self):
        source = self._protocol.get_clock_source()
        if source not in self.get_supported_clock_sources():
            raise RuntimeError('A bug of protocol abstraction, report this.')

        return source

    def set_clock_source(self, source):
        if self.get_property('streaming'):
            raise ValueError('Packet streaming already runs.')
        if source not in self._protocol.get_supported_clock_sources():
            raise ValueError('Unsupported or unavailable clock source.')
        self._protocol.set_clock_source(source)

    #
    # Modes for optical interfaces.
    # This is for 828mk2 and Model dependent.
    #
    def get_supported_opt_iface_directions(self):
        return self._protocol.get_supported_opt_iface_directions()

    def get_opt_iface_modes(self):
        return self._protocol.get_supported_opt_iface_modes()

    def get_opt_iface_indexes(self):
        return self._protocol.get_supported_opt_iface_indexes()

    def get_opt_iface_mode(self, direction, index):
        if direction not in self._protocol.get_supported_opt_iface_directions():
            raise ValueError('Invalid argument for direction of optical iface.')

        if index not in self._protocol.get_supported_opt_iface_indexes():
            raise ValueError('Invalid argument for index of optical iface.')

        mode = self._protocol.get_opt_iface_mode(direction, index)
        if mode not in self._protocol.get_supported_opt_iface_modes():
            raise RuntimeError('A bug of protocol abstraction, report this.')

        return mode

    def set_opt_iface_mode(self, direction, index, mode):
        if self.get_property('streaming'):
            raise ValueError('Packet streaming already runs.')

        if index not in self._protocol.get_supported_opt_iface_indexes():
            raise ValueError('Invalid argument for index of optical iface.')

        if mode not in self._protocol.get_supported_opt_iface_modes():
            raise ValueError('Invalid argument for mode of optical iface.')

        self._protocol.set_opt_iface_mode(direction, index, mode)
