# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from threading import Thread

import gi
gi.require_version('GLib', '2.0')
gi.require_version('Hinawa', '3.0')
from gi.repository import GLib, Hinawa

from hinawa_utils.motu.motu_protocol_v1 import MotuProtocolV1
from hinawa_utils.motu.motu_protocol_v2 import MotuProtocolV2
from hinawa_utils.motu.motu_protocol_v3 import MotuProtocolV3
from hinawa_utils.motu.config_rom_parser import MotuConfigRomParser

__all__ = ['MotuUnit']


class MotuUnit(Hinawa.SndMotu):
    SUPPORTED_MODELS = {
        0x000001: ('828',       MotuProtocolV1),
        0x000002: ('828',       MotuProtocolV1),
        0x000003: ('828mk2',    MotuProtocolV2),
        0x000009: ('Traveler',  MotuProtocolV2),
        0x000015: ('828mk3',    MotuProtocolV3),    # FireWire only
        0x000035: ('828mk3',    MotuProtocolV3),    # Hybrid
        0x000033: ('AudioExpress', MotuProtocolV3),
    }

    def __init__(self, path):
        super().__init__()
        self.open(path)
        if self.get_property('type') != 7:
            raise ValueError('The character device is not for Motu unit.')

        ctx = GLib.MainContext.new()
        self.create_source().attach(ctx)
        self.__unit_dispatcher = GLib.MainLoop.new(ctx, False)
        self.__unit_th = Thread(target=lambda d: d.run(), args=(self.__unit_dispatcher, ))
        self.__unit_th.start()

        node = self.get_node()
        ctx = GLib.MainContext.new()
        node.create_source().attach(ctx)
        self.__node_dispatcher = GLib.MainLoop.new(ctx, False)
        self.__node_th = Thread(target=lambda d: d.run(), args=(self.__node_dispatcher, ))
        self.__node_th.start()

        parser = MotuConfigRomParser()
        info = parser.parse_rom(self.get_node().get_config_rom())

        if info['model-id'] in self.SUPPORTED_MODELS:
            name, protocol = self.SUPPORTED_MODELS[info['model-id']]
            self.name = name
            self._protocol = protocol(self, False)
        else:
            raise OSError('Unsupported model')

    def release(self):
        self.__unit_dispatcher.quit()
        self.__node_dispatcher.quit()
        self.__unit_th.join()
        self.__node_th.join()

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.release()

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
            raise ValueError(
                'Invalid argument for direction of optical iface.')

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
