# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.oxfw.oxfw_unit import OxfwUnit
from hinawa_utils.oxfw.tascam_protocol import TascamProtocol

__all__ = ['TascamFireone']


class TascamFireone(OxfwUnit):
    def __init__(self, path):
        super().__init__(path)

        if self.vendor_name != 'TASCAM' or self.model_name != 'FireOne':
            raise ValueError('Unsupported model: {0}, {1}'.format(
                                            self.vendor_name, self.model_name))

    def get_display_mode_labels(self):
        return TascamProtocol.get_display_mode_labels()

    def set_display_mode(self, mode):
        TascamProtocol.set_display_mode(self.fcp, mode)

    def get_display_mode(self):
        return TascamProtocol.get_display_mode(self.fcp)

    def get_control_mode_labels(self):
        return TascamProtocol.get_control_mode_labels()

    def set_control_mode(self, mode):
        TascamProtocol.set_control_mode(self.fcp, mode)

    def get_control_mode(self):
        return TascamProtocol.get_control_mode(self.fcp)

    def get_input_mode_labels(self):
        return TascamProtocol.get_input_mode_labels()

    def set_input_mode(self, mode):
        TascamProtocol.set_input_mode(self.fcp, mode)

    def get_input_mode(self):
        return TascamProtocol.get_input_mode(self.fcp)

    def get_firmware_version(self):
        return TascamProtocol.get_firmware_version(self.fcp)
