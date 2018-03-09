from bebob.phase_go_protocol_abstract import PhaseGoProtocolAbstract

from ta1394.audio import AvcAudio

__all__ = ['PhaseGoProtocolOpt']

class PhaseGoProtocolOpt(PhaseGoProtocolAbstract):
    _MIXER_OUTPUT_FB = 2
    _OUTPUTS = {
        'analog-1/2':       1,
        'analog-3/4':       2,
        'digital-1/2':      3,
    }

    _ANALOG_OUTPUT_TARGETS = ('analog-1/2', 'analog-3/4')
    _OPS = ('volume', 'mute')
    _ANALOG_OUTPUT_FB = 1

    def __init__(self, fcp):
        super().__init__(fcp)

    def get_analog_output_labels(self):
        return self._ANALOG_OUTPUT_TARGETS

    def _check_analog_output_channel(self, target, ch):
        if target not in self._ANALOG_OUTPUT_TARGETS:
            raise ValueError('Invalid argument for stereo pair')
        if ch not in (1, 2):
            raise ValueError('Invalid argument for channel number')
        return self._ANALOG_OUTPUT_FB, ch

    def set_analog_output_volume(self, target, ch, db):
        fb, ch = self._check_analog_output_channel(target, ch)
        data = AvcAudio.build_data_from_db(db)
        AvcAudio.set_feature_volume_state(self._fcp, 0, 'current', fb, ch,
                                          data)

    def get_analog_output_volume(self, target, ch):
        fb, ch = self._check_analog_output_channel(target, ch)
        data = AvcAudio.get_feature_volume_state(self._fcp, 0, 'current', fb,
                                                 ch)
        return AvcAudio.parse_data_to_db(data)

    def set_analog_output_mute(self, target, ch, enable):
        fb, ch = self._check_analog_output_channel(target, ch)
        AvcAudio.set_feature_mute_state(self._fcp, 0, 'current', fb, ch,
                                        enable)

    def get_analog_output_mute(self, target, ch):
        fb, ch = self._check_analog_output_channel(target, ch)
        return AvcAudio.get_feature_mute_state(self._fcp, 0, 'current', fb, ch)
