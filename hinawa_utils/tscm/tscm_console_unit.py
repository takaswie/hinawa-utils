# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

from hinawa_utils.tscm.tscm_unit import TscmUnit

__all__ = ['TscmConsoleUnit']

class TscmConsoleUnit(TscmUnit):
    def __init__(self, path):
        super().__init__(path)

        if self.model_name not in ('FW-1082', 'FW-1884'):
            raise ValueError('Unsupported model: {0}'.format(self.model_name))

    def bright_led(self, position, state):
        if state not in self.supported_led_status:
            raise ValueError('Invalid argument for LED state.')
        frames = bytearray(4)
        frames[3] = position
        if self.supported_led_status.index(state) == 1:
            frames[1] = 0x01
        self.write_quadlet(0x0404, frames)

    def set_master_fader(self, mode):
        frames = bytearray(4)
        if mode:
            frames[2] = 0x40
        else:
            frames[1] = 0x40
        self.write_quadlet(0x022c, frames)
    def get_master_fader(self):
        frames = self.read_quadlet(0x022c)
        return bool(frames[3] & 0x40)
