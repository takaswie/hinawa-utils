from ieee1394.config_rom import Ieee1394ConfigRom

__all__ = ['MotuConfigRom']

'''
[ ['vendor', 'immediate', 498],
  ['node-capabilities', 'immediate', 33728],
  [ 'unit',
    'directory',
    [ ['specifier-id', 'immediate', 498],
      ['version', 'immediate', 51],
      ['model', 'immediate', 1067008]]],
  ['eui-64', 'leaf', 68118045948250624]]
'''

class MotuConfigRom(Ieee1394ConfigRom):
    def __init__(self):
        super().__init__(None, None)

    def _handle_unit(self, info, entries):
        # 3 entries in this unit.
        for entry in entries:
            key, type, value = entry
            if key == 'specifier-id':
                if type != 'immediate' or value != 0x0001f2:
                    raise OSError('Unsupported value for specifier-id: {0}'.format(value))
            elif key == 'version':
                if type != 'immediate':
                    raise OSError('Unsupported value for version: {0}'.format(value))
                info['version'] = value
            elif key == 'model':
                if type != 'immediate':
                    raise OSError('Unsupported value for model: {0}'.format(value))
                info['model-id'] = value
            else:
                raise OSError('Unsupported entry: {0},{1}'.format(key, type))

    def parse_root_directory(self, rom):
        PARSERS = (
            ('vendor', 'immediate', 'vendor-id', None),
            ('node-capabilities', 'immediate', 'node-capabilities', None),
            ('unit', 'directory', None, self._handle_unit),
            ('eui-64', 'immediate', 'eui-64', None),
        )
        info = {}

        entries = self.get_root_directory(rom)
        for entry in entries:
            for parser in PARSERS:
                key, type, label, handler = parser
                if entry[0] == key and entry[1] == type:
                    if label:
                        info[label] = entry[2]
                    elif handler:
                        handler(info, entry[2])

        return info
