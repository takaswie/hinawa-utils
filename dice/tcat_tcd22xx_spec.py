from dice.tcat_protocol_extension import ExtMixerSpace, ExtCurrentConfigSpace

class TcatTcd22xxSpec():
    # These four properties should be overridden by derived classes.
    MODELS = (
        (0x000000, 0x000000),
    )
    _INPUTS = (
        (),
    )
    _OUTPUTS = (
        (),
    )
    _FIXED = (
        {},
    )

    def __init__(self, index):
        self._index = index

    def _get_available_mixer_ports(self, protocol, mode):
        dsts = []

        count = 0
        for id, max_ports in ExtMixerSpace.MIXER_IN_MAX_PORTS.items():
            if count + max_ports > protocol._ext_caps['mixer']['input-channels']:
                max_ports = protocol._ext_caps['mixer']['input-channels'] - count
            for i in range(0, max_ports, 2):
                label = 'Mixer-{0}/{1}'.format(count + i + 1, count + i + 2)
                dst = [label, id, [i, i + 1]]
                dsts.append(dst)
            count += max_ports

        srcs = []

        max_ports = min(ExtMixerSpace.MIXER_OUT_MAX_PORTS[mode],
                        protocol._ext_caps['mixer']['output-channels'])
        for i in range(0, max_ports, 2):
            label = 'Mixer-{0}/{1}'.format(i + 1, i + 2)
            src = [label, 'mixer', [i, i + 1]]
            srcs.append(src)

        return srcs, dsts

    def _get_available_stream_ports(self, protocol, req, mode):
        STREAMS = ('avs0', 'avs1')

        stream_configs = \
                ExtCurrentConfigSpace.read_stream_config(protocol, req, mode)

        dsts = []

        for i, params in enumerate(stream_configs['tx']):
            id = STREAMS[i]
            count = params['pcm']
            if len(stream_configs['tx']) == 1:
                suffix = ''
            else:
                suffix = '-{0:c}'.format(0x41 + i)
            for j in range(0, count, 2):
                label = 'Stream{0}-{1}/{2}'.format(suffix, j + 1, j + 2)
                dst = [label, id, [j, j + 1]]
                dsts.append(dst)

        srcs = []

        for i, params in enumerate(stream_configs['rx']):
            id = STREAMS[i]
            count = params['pcm']
            if len(stream_configs['rx']) == 1:
                suffix = ''
            else:
                suffix = '-{0:c}'.format(0x41 + i)
            for j in range(0, count, 2):
                label = 'Stream{0}-{1}/{2}'.format(suffix, j + 1, j + 2)
                src = [label, id, [j, j + 1]]
                srcs.append(src)

        return srcs, dsts

    def _get_available_virt_ports(self, protocol, req, mode):
        srcs = []
        dsts = []

        stream_srcs, stream_dsts = \
                self._get_available_stream_ports(protocol, req, mode)
        srcs.extend(stream_srcs)
        dsts.extend(stream_dsts)

        mixer_srcs, mixer_dsts = self._get_available_mixer_ports(protocol, mode)
        srcs.extend(mixer_srcs)
        dsts.extend(mixer_dsts)

        return srcs, dsts

    def _get_full_spec_ports(self, protocol):
        inputs = []
        outputs = []

        asic_type = protocol._ext_caps['general']['asic-type']
        if asic_type == 'TCD-2210':
            suffix = ''
        else:
            suffix = '-A'

        inputs.append(('Analog{0}'.format(suffix), 'ins0', 16))
        outputs.append(('Analog{0}'.format(suffix), 'ins0', 16))

        if suffix != '':
            inputs.append(('Analog-B', 'ins1', 8))
            outputs.append(('Analog-B', 'ins1', 8))

        adat_count = 0
        for clock in ('adat', 'tdif'):
            if clock in protocol._clock_sources:
                adat_count += 1

        if adat_count == 1:
            inputs.append(('ADAT', 'adat', 8))
            outputs.append(('ADAT', 'adat', 8))
        elif adat_count == 2 and asic_type == 'TCD-2220':
            inputs.append(('ADAT-A', 'adat', 8))
            inputs.append(('ADAT-B', 'adat', 8))
            outputs.append(('ADAT-A', 'adat', 8))
            outputs.append(('ADAT-B', 'adat', 8))

        count = 0
        has_suffix = False
        for src in protocol._clock_sources:
            if src.find('aes') == 0:
                count += 1
                if count > 1:
                    has_suffix = True
        count = 0
        for src in protocol._clock_sources:
            if src.find('aes') == 0:
                index = {v: k for k, v in protocol.CLOCK_BITS.items()}[src]
                name = protocol._clock_source_labels[index]
                if has_suffix:
                    label = '{0}-{1:c}'.format(name, count + 0x41)
                else:
                    label = name
                inputs.append((label, 'aes', 2))
                outputs.append((label, 'aes', 2))
                count += 1

        return inputs, outputs

    def _get_available_real_ports(self, protocol, mode, inputs, outputs):
        ADAT_CHS = {
            'low': 8,
            'middle': 4,
            'high': 2,
        }

        # Update cache of physical ports. ADAT ports reduce the number of
        # available channels.
        in_ports = []
        out_ports = []
        for i, entry in enumerate(inputs):
            params = list(entry)
            if params[1] == 'adat':
                params[2] = ADAT_CHS[mode]
            in_ports.append(params)
        for i, entry in enumerate(outputs):
            params = list(entry)
            if params[1] == 'adat':
                params[2] = ADAT_CHS[mode]
            out_ports.append(params)

        # Some models have offset in their aes entries.
        aes_offset = 0
        clocks = protocol.get_supported_clock_sources()
        for clock in clocks:
            if clock.find('aes') == 0:
                for key, val in protocol.CLOCK_BITS.items():
                    if val == clock:
                        aes_offset = key * 2
                        break
                break

        dsts = []

        for params in out_ports:
            id = params[1]
            count = params[2]
            if id.find('aes') != 0:
                offset = 0
            else:
                offset = aes_offset
            for dst in dsts:
                if id == dst[1]:
                    offset += 2
            for i in range(0, count, 2):
                label = '{0}-{1}/{2}'.format(params[0], i + 1, i + 2)
                dst = [label, id, [offset + i, offset + i + 1]]
                dsts.append(dst)

        srcs = []

        for params in in_ports:
            id = params[1]
            count = params[2]
            if id.find('aes') != 0:
                offset = 0
            else:
                offset = aes_offset
            for src in srcs:
                if id == src[1]:
                    offset += 2
            for i in range(0, count, 2):
                label = '{0}-{1}/{2}'.format(params[0], i + 1, i + 2)
                src = [label, id, [offset + i, offset + i + 1]]
                srcs.append(src)

        return srcs, dsts

    def get_available_ports(self, protocol, req, mode):
        srcs = []
        dsts = []

        inputs = self._INPUTS[self._index]
        outputs = self._OUTPUTS[self._index]

        if len(inputs) == 0 and len(outputs) == 0:
            inputs, outputs = self._get_full_spec_ports(protocol)

        # Check arguments.
        for port in inputs:
            if len(port) != 3:
                raise ValueError('Invalid entry for input port.')
        for port in outputs:
            if len(port) != 3:
                raise ValueError('Invalid entry for output port.')

        real_srcs, real_dsts = \
                        self._get_available_real_ports(protocol, mode, inputs,
                                                       outputs)
        srcs.extend(real_srcs)
        dsts.extend(real_dsts)

        virt_srcs, virt_dsts = \
                            self._get_available_virt_ports(protocol, req, mode)
        srcs.extend(virt_srcs)
        dsts.extend(virt_dsts)

        return srcs, dsts

    def _refine_entries(self, entries, srcs, dsts):
        routes = []

        for entry in entries:
            # Skip mixer-to-mixer entries.
            if (entry['src-blk'] == 'mixer' and
                entry['dst-blk'] in ('mixer-tx0', 'mixer-tx1')):
                    continue

            # Skip entries with mute or reserved.
            if entry['dst-blk'] == 'mute':
                continue
            if entry['src-blk'].find('reserved') == 0:
                continue

            # Skip invalid entries for source.
            for src in srcs:
                if entry['src-blk'] == src[1] and entry['src-ch'] in src[2]:
                    break
            else:
                continue

            # Skip invalid entries for destination.
            for dst in dsts:
                if entry['dst-blk'] == dst[1] and entry['dst-ch'] in dst[2]:
                    break
            else:
                continue

            for i in range(2):
                route = {
                    'src-blk':  src[1],
                    'src-ch':   src[2][i],
                    'dst-blk':  dst[1],
                    'dst-ch':   dst[2][i],
                    'peak':     0,
                }
                if route not in routes:
                    routes.append(route)

        return routes

    def _add_fixed_entries(self, routes, maximum):
        for index, params in self._FIXED[self._index].items():
            direction = params[0]
            if direction == 'src':
                entry = {
                    'src-blk':  params[1],
                    'src-ch':   params[2],
                    'dst-blk':  'reserved6',
                    'dst-ch':   params[2] % 2,
                    'peak':     0,
                }
            elif direction == 'dst':
                entry = {
                    'src-blk':  'mute',
                    'src-ch':   params[2] % 2,
                    'dst-blk':  params[1],
                    'dst-ch':   params[2],
                    'peak':     0,
                }

            if (index < len(routes) and routes[index] != entry and
                len(routes) < maximum):
                routes.insert(index, entry)

        return routes

    def normalize_router_entries(self, protocol, entries, srcs, dsts):
        maximum = protocol._ext_caps['router']['maximum-routes']

        # Reset peak meter.
        for entry in entries:
            entry['peak'] = 0

        # Refine with missing pairs.
        routes = self._refine_entries(entries, srcs, dsts)

        # Some models require entries in fixed positions to display level in
        # its physical metrs.
        routes = self._add_fixed_entries(routes, maximum)

        return routes
