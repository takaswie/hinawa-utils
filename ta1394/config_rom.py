from ieee1394.config_rom import Ieee1394ConfigRom

__all__ = ['1394taConfigRom']

# TA Document 1999027 Configuration ROM for AV/C Devices 1.0
# http://1394ta.org/specifications/
class Ta1394ConfigRom(Ieee1394ConfigRom):
    def __init__(self, spec_entry_defs, vendor_entry_defs):
        super().__init__(spec_entry_defs, vendor_entry_defs)

    def _parse_vendor_dir(self, info, entries):
        raise OSError('Vendor directory is not supported.')

    def _parse_model_dir(self, info, entries):
        raise OSError('Model directory is not supported.')

    def _parse_unit_dir(self, info, entries):
        MANDATORY_IMMEDIATE_KEYS = ('specifier-id', 'version')
        unit = {}

        for entry in entries:
            name, type, value = entry
            if type == 'directory':
                raise OSError('Directory entries are not supported.')
            if name == 'model':
                if type == 'immediate':
                    unit['model-id'] = value
                elif type == 'leaf':
                    unit['model-name'] = value
            unit[name] = value

        for key in MANDATORY_IMMEDIATE_KEYS:
            if key not in unit:
                raise ValueError('Missing mandatory entry: {0}'.format(key))

        return unit

    def parse_root_directory(self, rom):
        PARSERS = (
            # key, type, label, handler
            ('vendor',  'immediate',    'vendor-id',    None),
            ('vendor',  'leaf',         'vendor-name',  None),
            ('vendor',  'directory',    None,           self._parse_vendor_dir),
            ('model',   'immediate',    'model-id',     None),
            ('model',   'leaf',         'model-name',   None),
            ('model',   'directory',    None,           self._parse_model_dir),
            ('node-capabilities', 'immediate', 'node-capabilities', None),
            ('unit',    'directory',    None,           self._parse_unit_dir)
        )
        info = {}

        entries = self.get_root_directory(rom)
        for entry in entries:
            for parser in PARSERS:
                key, type, label, handler = parser
                if entry[0] == key and entry[1] == type:
                    if label:
                        info[label] = entry[2]
                    else:
                        if 'units' not in info:
                            info['units'] = []
                        info['units'].append(handler(info, entry[2]))
        return info
