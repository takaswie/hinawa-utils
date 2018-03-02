from struct import unpack, pack

from ta1394.general import AvcGeneral

__all__ = ['AvcAudio']

class AvcAudio():
    attributes = ('resolution', 'minimum', 'maximum', 'default', 'duration',
                  'current', 'move', 'delta')

    attribute_values = {
        'resolution':   0x01,
        'minimum':      0x02,
        'maximum':      0x03,
        'default':      0x04,
        'duration':     0x08,
        'current':      0x10,
        'move':         0x18,
        'delta':        0x19,
    }

    @classmethod
    def set_selector_state(cls, fcp, subunit_id, attr, fb_id, value):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if ('current', 'minimum', 'maximum', 'default').count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if value > 255:
            raise ValueError('Invalid argument for selector value')
        args = bytearray()
        args.append(0x00)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x80)   # Selector function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(value)
        args.append(0x01)   # Selector control
        AvcGeneral.command_control(fcp, args)

    @classmethod
    def get_selector_state(cls, fcp, subunit_id, attr, fb_id):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if ('current', 'minimum', 'maximum', 'default').count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        args = bytearray()
        args.append(0x01)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x80)   # Selector function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(0xff)
        args.append(0x01)   # Selector control
        params = AvcGeneral.command_status(fcp, args)
        return params[7]

    @classmethod
    def set_feature_mute_state(cls, fcp, subunit_id, attr, fb_id, ch, mute):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if attr is not 'current':
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if ch > 255:
            raise ValueError('Invalid argument for channel number')
        if mute:
            val = 0x70
        else:
            val = 0x60
        args = bytearray()
        args.append(0x00)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x81)   # Feature function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x01)   # Mute control
        args.append(0x01)   # Control data length is 1
        args.append(val)
        AvcGeneral.command_control(fcp, args)

    @classmethod
    def get_feature_mute_state(cls, fcp, subunit_id, attr, fb_id, ch):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if attr is not 'current':
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if ch > 255:
            raise ValueError('Invalid argument for channel number')
        args = bytearray()
        args.append(0x01)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x81)   # Feature function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x01)   # Mute control
        args.append(0x01)   # Control data length is 1
        args.append(0xff)   # Status
        params = AvcGeneral.command_status(fcp, args)
        val = params[10]
        if val == 0x70:
            return True
        elif val == 0x60:
            return False
        else:
            raise OSError('Unexpected value in response')

    @classmethod
    def set_feature_volume_state(cls, fcp, subunit_id, attr, fb_id, ch, data):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if cls.attributes.count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if ch > 255:
            raise ValueError('Invalid argument for channel number')
        if len(data) != 2:
            raise ValueError('Invalid argument for data array')
        args = bytearray()
        args.append(0x00)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x81)   # Feature function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x02)   # Volume control
        args.append(0x02)   # Control data length is 2
        args.extend(data)   # Higher and lower parts of volume
        AvcGeneral.command_control(fcp, args)

    @classmethod
    def get_feature_volume_state(cls, fcp, subunit_id, attr, fb_id, ch):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if cls.attributes.count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if ch > 255:
            raise ValueError('Invalid argument for channel number')
        args = bytearray()
        args.append(0x01)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x81)   # Feature function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x02)   # Volume control
        args.append(0x02)   # Control data length is 2
        args.append(0xff)   # Higher part of volume
        args.append(0xff)   # Lower part of volume
        params = AvcGeneral.command_status(fcp, args)
        data = params[10:12]
        return data

    @classmethod
    def set_feature_lr_state(cls, fcp, subunit_id, attr, fb_id, ch, data):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if cls.attributes.count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if ch > 255:
            raise ValueError('Invalid argument for channel number')
        if len(data) != 2:
            raise ValueError('Invalid argument for data array')
        args = bytearray()
        args.append(0x00)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x81)   # Feature function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x03)   # LR control
        args.append(0x02)   # Control data length is 2
        args.extend(data)   # Higher and lower parts of volume
        AvcGeneral.command_control(fcp, args)

    @classmethod
    def get_feature_lr_state(cls, fcp, subunit_id, attr, fb_id, ch):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if cls.attributes.count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if ch > 255:
            raise ValueError('Invalid argument for channel number')
        args = bytearray()
        args.append(0x01)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x81)   # Feature function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x03)   # LR control
        args.append(0x02)   # Control data length is 2
        args.append(0xff)   # Higher part of balance
        args.append(0xff)   # Lower part of balance
        params = AvcGeneral.command_status(fcp, args)
        data = params[10:12]
        return data

    @classmethod
    def set_processing_mixer_state(cls, fcp, subunit_id, attr, fb_id, in_fb,
                                   in_ch, out_ch, data):
        attrs = ('current', 'minimum', 'maximum', 'resolution', 'default')
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if attrs.count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if in_fb > 255:
            raise ValueError('Invalid argument for input function block ID')
        if in_ch > 255:
            raise ValueError('Invalid argument for input channel number')
        if out_ch > 255:
            raise ValueError('Invalid argument for output channel number')
        if len(data) != 2:
            raise ValueError('Invalid argument for data array')
        args = bytearray()
        args.append(0x00)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x82)   # Processing function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x04)   # Selector length is 4
        args.append(in_fb)
        args.append(in_ch)
        args.append(out_ch)
        args.append(0x03)   # Mixer control
        args.append(0x02)   # Control data is 2
        args.extend(data)   # Higher and lower parts of setting
        AvcGeneral.command_control(fcp, args)

    @classmethod
    def get_processing_mixer_state(cls, fcp, subunit_id, attr, fb_id, in_fb,
                                   in_ch, out_ch):
        attrs = ('current', 'minimum', 'maximum', 'resolution', 'default')
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if attrs.count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if in_fb > 255:
            raise ValueError('Invalid argument for input function block ID')
        if in_ch > 255:
            raise ValueError('Invalid argument for input channel number')
        if out_ch > 255:
            raise ValueError('Invalid argument for output channel number')
        args = bytearray()
        args.append(0x01)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x82)   # Processing function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x04)   # Selector length is 4
        args.append(in_fb)
        args.append(in_ch)
        args.append(out_ch)
        args.append(0x03)   # Mixer control
        args.append(0x02)   # Control data is 2
        args.append(0xff)   # Higher part of setting
        args.append(0xff)   # Lower part of setting
        params = AvcGeneral.command_status(fcp, args)
        data = params[12:14]
        return data

    @classmethod
    def set_processing_mixer_state_all(cls, fcp, subunit_id, attr, fb_id, in_fb,
                                       data):
        attrs = ('current', 'minimum', 'maximum', 'resolution', 'default')
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if attrs.count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if in_fb > 255:
            raise ValueError('Invalid argument for input function block ID')
        for datum in data:
            if len(data) != 2:
                raise ValueError('Invalid argument for array of data array')
        args = bytearray()
        args.append(0x00)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x82)   # Processing function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x04)   # Selector length is 4
        args.append(in_fb)
        args.append(0xff)
        args.append(0xff)
        args.append(0x03)       # Mixer control
        args.append(len(data))  # The length of control data
        for datum in data:
            args.extend(datum)
        AvcGeneral.command_control(fcp, args)

    @classmethod
    def get_processing_mixer_state_all(cls, fcp, subunit_id, attr,
                                       fb_id, in_fb):
        attrs = ('current', 'minimum', 'maximum', 'resolution', 'default')
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if attrs.count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if in_fb > 255:
            raise ValueError('Invalid argument for input function block ID')
        args = bytearray()
        args.append(0x01)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x82)   # Processing function block
        args.append(fb_id)
        args.append(cls.attribute_values[attr])
        args.append(0x04)   # Selector length is 4
        args.append(in_fb)
        args.append(0xff)
        args.append(0xff)
        args.append(0x03)   # Mixer control
        args.append(0xff)   # The length of control data in response
        params = AvcGeneral.command_status(fcp, args)
        count = params[11] // 2
        data = []
        params = params[12:]
        for i in range(0, count, 2):
            data.append(params[i * 2:i * 2 + 1])
        return data

    # MEMO: 0x8000 represents negative infinite. 0x7fff is invalid. However,
    # in this method, they're used to represent minimum/maximum value.
    @classmethod
    def parse_data_to_db(cls, data):
        if data[0] == 0x80 and data[1] == 0x00:
            return -128.0
        elif data[0] == 0x7f and data[1] == 0xff:
            return 128.0
        else:
            return unpack('>h', data)[0] * 128 / 0x7fff
    @classmethod
    def build_data_from_db(cls, db):
        if db == 128.0:
            return (0x7f, 0xff)
        elif db == -128.0:
            return (0x80, 0x00)
        else:
            return pack('>h', int(0x7fff * db/ 128))
