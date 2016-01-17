from ta1394.general import AvcGeneral

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

    @staticmethod
    def set_selector_state(fcp, subunit_id, attr, fb_id, value):
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
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(value)
        args.append(0x01)   # Selector control
        AvcGeneral.command_control(fcp, args)

    @staticmethod
    def get_selector_state(fcp, subunit_id, attr, fb_id):
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
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(0xff)
        args.append(0x01)   # Selector control
        params = AvcGeneral.command_status(fcp, args)
        return params[7]

    @staticmethod
    def set_feature_mute_state(fcp, subunit_id, attr, fb_id, ch, mute):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if attr is not 'current':
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if ch > 255:
            raise ValueError('Invalid argument for channel number')
        if mute:
            mute = 0x70
        else:
            mute = 0x60
        args = bytearray()
        args.append(0x00)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x81)   # Feature function block
        args.append(fb_id)
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x01)   # Mute control
        args.append(0x01)   # Control data length is 1
        args.append(mute)
        AvcGeneral.command_control(fcp, args)

    @staticmethod
    def get_feature_mute_state(fcp, subunit_id, attr, fb_id, ch):
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
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x01)   # Mute control
        args.append(0x01)   # Control data length is 1
        args.append(0xff)   # Status
        params = AvcGeneral.command_status(fcp, args)
        if params[10] == 0x70:
            return True
        elif params[10] == 0x60:
            return False
        else:
            raise OSError('Unexpected value in response')

    @staticmethod
    def set_feature_volume_state(fcp, subunit_id, attr, fb_id, ch, vol):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if AvcAudio.attributes.count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if ch > 255:
            raise ValueError('Invalid argument for channel number')
        args = bytearray()
        args.append(0x00)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x81)   # Feature function block
        args.append(fb_id)
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x02)   # Volume control
        args.append(0x02)   # Control data length is 2
        args.append(vol >> 8)   # Higher part of volume
        args.append(vol & 0xff) # Lower part of volume
        AvcGeneral.command_control(fcp, args)

    @staticmethod
    def get_feature_volume_state(fcp, subunit_id, attr, fb_id, ch):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if AvcAudio.attributes.count(attr) == 0:
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
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x02)   # Volume control
        args.append(0x02)   # Control data length is 2
        args.append(0xff)   # Higher part of volume
        args.append(0xff)   # Lower part of volume
        params = AvcGeneral.command_status(fcp, args)
        return (params[10] << 8) | params[11]

    @staticmethod
    def set_feature_lr_state(fcp, subunit_id, attr, fb_id, ch, balance):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if AvcAudio.attributes.count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if ch > 255:
            raise ValueError('Invalid argument for channel number')
        args = bytearray()
        args.append(0x00)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x81)   # Feature function block
        args.append(fb_id)
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x03)   # LR control
        args.append(0x02)   # Control data length is 2
        args.append(balance >> 8)   # Higher part of balance
        args.append(balance & 0xff) # Lower part of balance
        AvcGeneral.command_control(fcp, args)

    @staticmethod
    def get_feature_lr_state(fcp, subunit_id, attr, fb_id, ch):
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if AvcAudio.attributes.count(attr) == 0:
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
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x02)   # Selector length is 2
        args.append(ch)
        args.append(0x03)   # LR control
        args.append(0x02)   # Control data length is 2
        args.append(0xff)   # Higher part of balance
        args.append(0xff)   # Lower part of balance
        params = AvcGeneral.command_status(fcp, args)
        return (params[10] << 8) | params[11]

    @staticmethod
    def set_processing_mixer_state(fcp, subunit_id, attr, fb_id, in_fb,
                                   in_ch, out_ch, setting):
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
        args.append(0x00)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x82)   # Processing function block
        args.append(fb_id)
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x04)   # Selector length is 4
        args.append(in_fb)
        args.append(in_ch)
        args.append(out_ch)
        args.append(0x03)   # Mixer control
        args.append(0x02)   # Control data is 2
        args.append(setting >> 8)   # Higher part of setting
        args.append(setting & 0xff) # Lower part of setting
        AvcGeneral.command_control(fcp, args)

    @staticmethod
    def get_processing_mixer_state(fcp, subunit_id, attr, fb_id, in_fb,
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
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x04)   # Selector length is 4
        args.append(in_fb)
        args.append(in_ch)
        args.append(out_ch)
        args.append(0x03)   # Mixer control
        args.append(0x02)   # Control data is 2
        args.append(0xff)   # Higher part of setting
        args.append(0xff)   # Lower part of setting
        params = AvcGeneral.command_status(fcp, args)
        return (params[12] << 8) | params[13]

    @staticmethod
    def set_processing_mixer_state_all(fcp, subunit_id, attr, fb_id, in_fb,
                                       states):
        attrs = ('current', 'minimum', 'maximum', 'resolution', 'default')
        if subunit_id > 0x07:
            raise ValueError('Invalid argument for subunit ID')
        if attrs.count(attr) == 0:
            raise ValueError('Invalid argument for attribute')
        if fb_id > 255:
            raise ValueError('Invalid argument for function block ID')
        if in_fb > 255:
            raise ValueError('Invalid argument for input function block ID')
        data_count = len(states) // 2
        args = bytearray()
        args.append(0x00)
        args.append(0x08 | (subunit_id & 0x07))
        args.append(0xb8)
        args.append(0x82)   # Processing function block
        args.append(fb_id)
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x04)   # Selector length is 4
        args.append(in_fb)
        args.append(0xff)
        args.append(0xff)
        args.append(0x03)   		# Mixer control
        args.append(data_count)	# The length of control data
        for i in range(data_count):
            args.append((states[i * 2] << 8) | states[i * 2 + 1])
        AvcGeneral.command_control(fcp, args)

    @staticmethod
    def get_processing_mixer_state_all(fcp, subunit_id, attr, fb_id, in_fb):
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
        args.append(AvcAudio.attribute_values[attr])
        args.append(0x04)   # Selector length is 4
        args.append(in_fb)
        args.append(0xff)
        args.append(0xff)
        args.append(0x03)   # Mixer control
        args.append(0xff)   # The length of control data in response
        params = AvcGeneral.command_status(fcp, args)
        count = params[11] // 2
        status = []
        for i in range(count):
            status.append((params[12 + i * 2] << 8) | params[13 + i * 2])
        return status
