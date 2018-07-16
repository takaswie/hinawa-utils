from ieee1394.config_rom import Ieee1394ConfigRom

__all__ = ['BebobConfigRom']

class BebobConfigRom(Ieee1394ConfigRom):
    _KEY_DEFS = {
        0x3a:   ('BEBOB-A', (0x00, )),
        0x3b:   ('BEBOB-B', (0x00, )),
        0x3c:   ('BEBOB-C', (0x00, )),
        0x3d:   ('BEBOB-D', (0x00, )),
    }

    def __init__(self):
        super().__init__(None, self._KEY_DEFS)

    # One directory for unit.
    def _handle_unit(self, info, entries):
        for entry in entries:
            key, type, value = entry
            if key == 'specifier-id':
                if type != 'immediate':
                    raise OSError('')
            elif key == 'version':
                if type != 'immediate':
                    raise OSError('')
            elif key == 'model':
                if type == 'immediate' and value != info['model-id']:
                    raise OSError('')
                elif type == 'leaf' and value != info['model-name']:
                    raise OSError('')

    # One directory for dependent info if exists.
    def _handle_dependent_info(self, info, entries):
        addrs = [0] * 4

        for entry in entries:
            key, type, value = entry
            if key == 'specifier-id':
                if type != 'immediate' or value != 0x0007f5:
                    raise OSError('')
            elif key == 'version':
                if type != 'immediate' or value != 0x000001:
                    raise OSError('')
            elif key == 'BEBOB-A':
                addrs[0] = value
            elif key == 'BEBOB-B':
                addrs[1] = value
            elif key == 'BEBOB-C':
                addrs[2] = value
            elif key == 'BEBOB-D':
                addrs[3] = value

        if 0 not in addrs:
            if 'bebob' not in info:
                info['bebob'] = None
            info['bebob'] = addrs

    def parse_root_directory(self, rom):
        PARSERS = (
            ('hardware-version', 'immediate', 'hardware-version', None),
            ('node-capabilities', 'immediate', 'node-capabilities', None),
            ('vendor', 'immediate', 'vendor-id', None),
            ('vendor', 'leaf', 'vendor-name', None),
            ('model', 'immediate', 'model-id', None),
            ('model', 'leaf', 'model-name', None),
            ('version', 'immediate', 'version', None),
            ('unit', 'directory', None, self._handle_unit),
            ('dependent-info', 'directory', None, self._handle_dependent_info),
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
                        handler(info, entry[2])

        return info
