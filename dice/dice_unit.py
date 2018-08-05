# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from dice.tcat_protocol_general import TcatProtocolGeneral
from ta1394.config_rom_parser import Ta1394ConfigRomParser

__all__ = ['DiceUnit']

class DiceUnit(Hinawa.SndDice):
    def __init__(self, path):
        if path.find('/dev/snd/hw') == 0:
            super().__init__()
            self.open(path)
            if self.get_property('type') != 1:
                raise ValueError('The character device is not for Dice unit')
            self.listen()
            self._on_juju = False
        elif path.find('/dev/fw') == 0:
            # Just using parent class.
            super(Hinawa.FwUnit, self).__init__()
            Hinawa.FwUnit.open(self, path)
            Hinawa.FwUnit.listen(self)
            self._on_juju = True
        else:
            raise ValueError('Invalid argument for character device')

        parser = Ta1394ConfigRomParser()
        info = parser.parse_rom(self.get_config_rom())
        self.vendor_id = info['vendor-id']
        self.model_id = info['model-id']

        req = Hinawa.FwReq()
        self._protocol = TcatProtocolGeneral(self, req)

    def get_owner_addr(self):
        req = Hinawa.FwReq()
        return self._protocol.read_owner_addr(req)

    def get_latest_notification(self):
        req = Hinawa.FwReq()
        return self._protocol.read_latest_notification(req)

    def set_nickname(self, name):
        req = Hinawa.FwReq()
        self._protocol.write_nickname(req, name)

    def get_nickname(self):
        req = Hinawa.FwReq()
        return self._protocol.read_nickname(req)

    def get_supported_clock_sources(self):
        labels = []
        clk_srcs = self._protocol.get_supported_clock_sources()
        for i, label in enumerate(self._protocol.get_clock_source_names()):
            if label != 'Unused' and self._protocol.CLOCK_BITS[i] in clk_srcs:
                labels.append(label)
        return labels

    def set_clock_source(self, source):
        if self.get_property('streaming'):
            raise RuntimeError('Packet streaming started.')
        if self._on_juju:
            raise RuntimeError('This operation is not supported withou ALSA.')
        req = Hinawa.FwReq()
        labels = self._protocol.get_clock_source_names()
        if source not in labels or source == 'Unused':
            raise ValueError('Invalid argument for clock source.')
        alias = self._protocol.CLOCK_BITS[labels.index(source)]
        self._protocol.write_clock_source(req, alias)

    def get_clock_source(self):
        req = Hinawa.FwReq()
        labels = self._protocol.get_clock_source_names()
        src = self._protocol.read_clock_source(req)
        index = {v: k for k, v in self._protocol.CLOCK_BITS.items()}[src]
        return labels[index]

    def get_supported_sampling_rates(self):
        return self._protocol.get_supported_sampling_rates()

    def set_sampling_rate(self, rate):
        if self.get_property('streaming'):
            raise RuntimeError('Packet streaming started.')
        if self._on_juju:
            raise RuntimeError('This operation is not supported withou ALSA.')
        req = Hinawa.FwReq()
        self._protocol.write_sampling_rate(req, rate)

    def get_sampling_rate(self):
        req = Hinawa.FwReq()
        return self._protocol.read_sampling_rate(req)

    def get_enabled(self):
        req = Hinawa.FwReq()
        return self._protocol.read_enabled(req)

    def get_clock_status(self):
        req = Hinawa.FwReq()
        return self._protocol.read_clock_status(req)

    def get_external_clock_states(self):
        req = Hinawa.FwReq()
        return self._protocol.read_external_clock_states(req)

    def get_measured_sampling_rate(self):
        req = Hinawa.FwReq()
        return self._protocol.read_measured_sampling_rate(req)

    def get_dice_version(self):
        return self._protocol.get_dice_version()

    def get_tx_params(self):
        req = Hinawa.FwReq()
        return self._protocol.read_tx_params(req)

    def get_rx_params(self):
        req = Hinawa.FwReq()
        return self._protocol.read_rx_params(req)

    def get_external_sync_clock_source(self):
        req = Hinawa.FwReq()
        return self._protocol.read_external_sync_clock_source(req)

    def get_external_sync_locked(self):
        req = Hinawa.FwReq()
        return self._protocol.read_external_sync_locked(req)

    def get_external_sync_rate(self):
        req = Hinawa.FwReq()
        return self._protocol.read_external_sync_rate(req)

    def get_external_sync_adat_status(self):
        req = Hinawa.FwReq()
        return self._protocol.read_external_sync_adat_status(req)
