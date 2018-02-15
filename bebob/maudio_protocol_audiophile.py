import gi

gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from bebob.maudio_protocol_normal import MaudioProtocolNormal

from ta1394.general import AvcConnection

__all__ = ['MaudioProtocolAudiophile']

class MaudioProtocolAudiophile(MaudioProtocolNormal):
    def get_meters(self):
        labels = self._labels['meters']
        meters = {}
        req = Hinawa.FwReq()
        current = req.read(self._unit, self._ADDR_FOR_METERING, self._meters)
        for i, name in enumerate(labels):
            meters[name] = current[i]

        misc = current[-1]
        meters['rotery-0'] = (misc >> 16) & 0x0f
        meters['rotery-1'] = (misc >> 20) & 0x0f
        meters['rotery-2'] = 0
        if misc & 0x0f000000 and not misc & 0x00ff0000:
            meters['switch-0'] = 1
        else:
            meters['switch-0'] = 0
        if meters['switch-0'] == 0 and misc & 0xf0000000:
            meters['switch-1'] = 1
        else:
            meters['switch-1'] = 0
        meters['rate'] = AvcConnection.sampling_rates[(misc >> 8) & 0xff]
        meters['sync'] = misc & 0x0f

        return meters
