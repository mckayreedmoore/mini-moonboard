"""Fail-closed checks of the completed rigid-pin contact coupon."""
import math
import re


def number(value):
    """Round-trip numeric input, retaining integer spellings in existing decks."""
    return repr(float(value)).removesuffix('.0')


def job_name(direction, size, penalty, clearance):
    values = [number(v).replace('.', 'p') for v in (size, penalty, clearance)]
    return f'contact_{direction}_'+ '_'.join(values)


def audit_deck(deck, context):
    sections = []
    for line in deck.splitlines():
        line = line.strip()
        if not line or line.startswith('**'):
            continue
        if line.startswith('*'):
            sections.append((line.upper().replace(' ', ''), []))
        elif sections:
            sections[-1][1].append(line)
    allowed = {'*HEADING', '*NODE', '*ELEMENT', '*ELSET', '*NSET', '*MATERIAL', '*ELASTIC',
               '*SOLIDSECTION', '*SURFACE', '*SURFACEINTERACTION', '*SURFACEBEHAVIOR',
               '*CONTACTPAIR', '*STEP', '*STATIC', '*BOUNDARY', '*NODEPRINT', '*CONTACTPRINT',
               '*NODEFILE', '*ENDSTEP'}
    if any(header.split(',')[0] not in allowed for header, _ in sections):
        raise ValueError('Unexpected model keyword/constraint')
    parameterless = {'*NODE', '*BOUNDARY', '*STATIC', '*ELASTIC', '*ENDSTEP'}
    if any(header.split(',')[0] in parameterless and header not in parameterless for header, _ in sections):
        raise ValueError('Unexpected keyword options/constraint replacement')
    node_blocks = [rows for header, rows in sections if header == '*NODE']
    if len(node_blocks) != 1:
        raise ValueError('Missing or multiple node blocks')
    actual = {}
    for line in node_blocks[0]:
        row = line.split(',')
        tag, xyz = int(row[0]), [float(v) for v in row[1:]]
        if tag in actual or len(xyz) != 3 or not all(math.isfinite(v) for v in xyz):
            raise ValueError('Invalid deck nodes')
        actual[tag] = xyz
    expected = {int(t): xyz for t, xyz in context['nodes'].items()}
    if actual.keys() != expected.keys() or any(math.dist(xyz, expected[t]) > 1e-8 for t, xyz in actual.items()):
        raise ValueError('Deck/context nodes differ')
    elements, elsets, surfaces = {}, {}, {}
    for header, rows in sections:
        if header.startswith('*ELEMENT,'):
            if 'TYPE=C3D10,' not in header:
                raise ValueError('Unexpected element type')
            for row in rows:
                values = [int(v) for v in row.split(',')]
                if len(values) != 11 or values[0] in elements or len(set(values[1:])) != 10 or not set(values[1:]) <= actual.keys():
                    raise ValueError('Invalid C3D10 connectivity')
                elements[values[0]] = values[1:]
        elif header.startswith('*ELSET,'):
            name = re.search(r'ELSET=([^,]+)', header).group(1)
            if 'GENERATE' in header or name in elsets:
                raise ValueError('Unexpected element set')
            elsets[name] = [int(v) for row in rows for v in row.split(',') if v.strip()]
        elif header.startswith('*SURFACE,'):
            name = re.search(r'NAME=([^,]+)', header).group(1)
            if 'TYPE=ELEMENT' not in header or name in surfaces or not rows:
                raise ValueError('Invalid contact surface definition')
            surfaces[name] = rows
    members = {'WOOD', *context['pins']}
    if elsets.keys() != members or not elements or surfaces.keys() != {k+'_SURF' for k in members}:
        raise ValueError('Missing contact material sets or surfaces')
    all_ids = [e for ids in elsets.values() for e in ids]
    if len(all_ids) != len(set(all_ids)) or set(all_ids) != elements.keys():
        raise ValueError('Incomplete/overlapping material elements')
    pin_tags = {t for tags in context['pins'].values() for t in tags}
    local_nodes = {'WOOD': set(actual)-pin_tags, **{k: set(tags) for k, tags in context['pins'].items()}}
    if sum(len(tags) for tags in local_nodes.values()) != len(actual):
        raise ValueError('Shared wood/pin mesh nodes bond the contact')
    face_nodes = ((0, 1, 2, 4, 5, 6), (0, 3, 1, 7, 8, 4),
                  (1, 3, 2, 8, 9, 5), (2, 3, 0, 9, 7, 6))
    stations = context['geometry']['stations_mm']
    for member, ids in elsets.items():
        id_set = set(ids)
        if any(not set(elements[e]) <= local_nodes[member] for e in ids):
            raise ValueError('Element bridges the separate contact members')
        candidates = stations if member == 'WOOD' else [stations[int(member[-1])-1]]
        radius = 5 if member == 'WOOD' else 5-context['args']['clearance']
        # Identify every exterior face from volume topology, independently of
        # the declared contact surfaces. A valid subset is not full coverage.
        masks = {t: sum(1 << j for j, s in enumerate(candidates)
                        if abs(math.hypot(actual[t][1]-s, actual[t][2])-radius) < 1e-4)
                 for t in local_nodes[member]}
        counts, cylindrical = {}, []
        for e in ids:
            for face, indices in enumerate(face_nodes, 1):
                key = tuple(sorted(elements[e][i] for i in indices[:3]))
                counts[key] = counts.get(key, 0)+1
                common = (1 << len(candidates))-1
                for i in indices:
                    common &= masks[elements[e][i]]
                    if not common:
                        break
                if common:
                    cylindrical.append((e, face, key))
        expected_surface = {(e, face) for e, face, key in cylindrical if counts[key] == 1}
        seen = set()
        for row in surfaces[member+'_SURF']:
            fields = row.split(',')
            if len(fields) != 2 or not re.fullmatch(r'S[1-4]', fields[1]):
                raise ValueError('Invalid tetrahedron contact face')
            e, face = int(fields[0]), int(fields[1][1:])
            if e not in id_set or (e, face) in seen:
                raise ValueError('Contact face outside assigned member or duplicated')
            seen.add((e, face))
            xyz = [actual[elements[e][i]] for i in face_nodes[face-1]]
            if not any(all(abs(math.hypot(p[1]-s, p[2])-radius) < 1e-4 for p in xyz) for s in candidates):
                raise ValueError('Contact face is not the intended bore/pin cylinder')
        if not expected_surface or seen != expected_surface:
            raise ValueError('Incomplete or non-exterior cylindrical contact surface coverage')
    sets = {}
    for header, rows in sections:
        if header.startswith('*NSET,'):
            name = re.search(r'NSET=([^,]+)', header).group(1)
            if 'GENERATE' in header or name in sets:
                raise ValueError('Unsupported/duplicate node set')
            sets[name] = [int(v) for row in rows for v in row.split(',') if v.strip()]
    for name, tags in {'ALLN': list(expected), 'DRIVE': context['driven'],
                       **{k+'_N': v for k, v in context['pins'].items()}}.items():
        if name not in sets or sorted(sets[name]) != sorted(tags):
            raise ValueError('Deck/context node sets differ')
    boundary = [rows for header, rows in sections if header == '*BOUNDARY']
    axis = 2 if context['args']['direction'] == 'S' else 3
    wanted = [('DRIVE', i, i, context['imposed_displacement_mm'] if i == axis else 0.) for i in (1, 2, 3)]
    wanted += [(k+'_N', 1, 3, 0.) for k in context['pins']]
    if len(boundary) != 1:
        raise ValueError('Missing/duplicate boundary definition')
    actual_bc = [(r[0], int(r[1]), int(r[2]), float(r[3])) for row in boundary[0] if (r := row.split(','))]
    # Decimal serialization is permitted, but not a changed direction/load.
    if len(actual_bc) != len(wanted) or any(a[:3] != b[:3] or not math.isclose(a[3], b[3], abs_tol=1e-10)
                                            for a, b in zip(actual_bc, wanted, strict=True)):
        raise ValueError('Wrong imposed boundary conditions')
    if any(header.startswith(('*CLOAD', '*DLOAD', '*TIE', '*FRICTION', '*TRANSFORM', '*EQUATION',
                              '*MPC', '*AMPLITUDE', '*PLASTIC', '*SPRING')) for header, _ in sections):
        raise ValueError('Unexpected load/bond/friction')
    pairs = [(header, rows) for header, rows in sections if header.startswith('*CONTACTPAIR,')]
    if pairs != [('*CONTACTPAIR,INTERACTION=FRICTIONLESS,TYPE=SURFACETOSURFACE', [f'WOOD_SURF,{k}_SURF']) for k in context['pins']]:
        raise ValueError('Wrong contact pairs')
    law = [rows for header, rows in sections if header == '*SURFACEBEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR']
    if (len(law) != 1 or len(law[0]) != 1 or float(law[0][0]) != context['args']['penalty']
            or sum(header.startswith('*SURFACEBEHAVIOR') for header, _ in sections) != 1):
        raise ValueError('Wrong penalty law')
    if [(header, rows) for header, rows in sections if header.startswith('*SURFACEINTERACTION')] != [('*SURFACEINTERACTION,NAME=FRICTIONLESS', [])]:
        raise ValueError('Missing/changed contact interaction')
    materials = []
    for i, (header, _) in enumerate(sections):
        if header.startswith('*MATERIAL,'):
            if i+1 >= len(sections) or sections[i+1][0] != '*ELASTIC':
                raise ValueError('Missing elastic material')
            materials.append((header, sections[i+1][1]))
    if materials != [('*MATERIAL,NAME=WOOD_SCREEN', ['7000,0.3']),
                      ('*MATERIAL,NAME=FIXED_PIN', ['210000,0.3'])]:
        raise ValueError('Changed conditional material model')
    if sum(header == '*ELASTIC' for header, _ in sections) != 2:
        raise ValueError('Additional elastic material definition')
    expected_sections = ['*SOLIDSECTION,ELSET=WOOD,MATERIAL=WOOD_SCREEN']
    expected_sections += [f'*SOLIDSECTION,ELSET={k},MATERIAL=FIXED_PIN' for k in context['pins']]
    if [header for header, _ in sections if header.startswith('*SOLIDSECTION')] != expected_sections:
        raise ValueError('Changed material assignment')
    if [header for header, _ in sections if header.startswith('*STEP')] != ['*STEP,NLGEOM,INC=1000']:
        raise ValueError('Changed nonlinear step')
    if [rows for header, rows in sections if header == '*STATIC'] != [['1,1,1e-6,1']]:
        raise ValueError('Changed static increments')


def _rows(text, title):
    matches = list(re.finditer(title.replace('.*?', '[^\n]*?')+r'[^\n]*\n(.*?)(?=\n\s*[A-Za-z]|\Z)', text, re.IGNORECASE | re.DOTALL))
    if len(matches) != 1 or '0.1000000E+01' not in matches[0].group(0).splitlines()[0]:
        raise ValueError(f'Missing/duplicate/nonfinal {title}')
    return [row.split() for row in matches[0].group(1).splitlines() if row.strip()]


def _vectors(text, title, expected):
    rows = _rows(text, title)
    if any(len(row) != 4 for row in rows):
        raise ValueError('Malformed nodal vector output')
    values = {int(row[0]): tuple(float(v) for v in row[1:]) for row in rows}
    if len(values) != len(rows) or set(values) != set(expected):
        raise ValueError('Incomplete or duplicate nodal output')
    if not all(math.isfinite(v) for row in values.values() for v in row):
        raise ValueError('Nonfinite nodal output')
    return values


def audit(text, context, status, log):
    if 'CalculiX Version 2.21' not in log or 'Job finished' not in log or '*ERROR' in log.upper():
        raise ValueError('No successful CalculiX2.21 completion')
    increments = [line.split() for line in status.splitlines() if re.match(r'^\s*1\s+\d', line)]
    if not increments or not math.isfinite(float(increments[-1][4])) or abs(float(increments[-1][4])-1) > 1e-8:
        raise ValueError('Final increment not completed')
    nodes = {int(t): xyz for t, xyz in context['nodes'].items()}
    if not math.isfinite(context['min_jacobian']) or context['min_jacobian'] <= 0:
        raise ValueError('Invalid final mesh Jacobian')
    if not nodes or not all(len(xyz) == 3 and all(math.isfinite(v) for v in xyz) for xyz in nodes.values()):
        raise ValueError('Nonfinite/invalid context coordinates')
    if context['args']['direction'] not in ('S', 'N') or not math.isfinite(context['args']['penalty']) or context['args']['penalty'] <= 0:
        raise ValueError('Invalid intended contact parameters')
    u = _vectors(text, r'displacements .*?set ALLN', nodes)
    axis = 1 if context['args']['direction'] == 'S' else 2
    for t in context['driven']:
        expected = [0., 0., 0.]
        expected[axis] = context['imposed_displacement_mm']
        if any(abs(a-b) > 1e-7 for a, b in zip(u[t], expected, strict=True)):
            raise ValueError('Incorrect imposed motion')
    for tags in context['pins'].values():
        if any(abs(v) > 1e-10 for t in tags for v in u[t]):
            raise ValueError('Pin moved despite rigid restraint')
    reactions, moments, centroid_moments = {}, {}, {}
    centre = [sum(nodes[t][i]+u[t][i] for t in context['driven'])/len(context['driven']) for i in range(3)]
    roundoff = [0., 0., 0.]
    for label, tags in {'DRIVE': context['driven'], **{k+'_N': v for k, v in context['pins'].items()}}.items():
        rf = _vectors(text, rf'(?<!total )forces .*?set {label}\b', tags)
        total = [sum(row[i] for row in rf.values()) for i in range(3)]
        reported = _rows(text, rf'total force .*?set {label}\b')
        if len(reported) != 1 or len(reported[0]) != 3:
            raise ValueError('Missing reported total')
        if any(not math.isfinite(float(v)) or abs(float(v)-actual) > .01
               for v, actual in zip(reported[0], total, strict=True)):
            raise ValueError('Reported/nodal force mismatch')
        reactions[label] = total
        moments[label] = [sum((nodes[t][(i+1)%3]+u[t][(i+1)%3])*row[(i+2)%3]
                             -(nodes[t][(i+2)%3]+u[t][(i+2)%3])*row[(i+1)%3]
                             for t, row in rf.items()) for i in range(3)]
        centroid_moments[label] = [sum((nodes[t][(i+1)%3]+u[t][(i+1)%3]-centre[(i+1)%3])*row[(i+2)%3]
                                      -(nodes[t][(i+2)%3]+u[t][(i+2)%3]-centre[(i+2)%3])*row[(i+1)%3]
                                      for t, row in rf.items()) for i in range(3)]
        for t, row in rf.items():
            # DAT RF uses seven significant decimal digits. Bound its rounding
            # contribution separately, not as an excuse to accept any residual.
            error = [.5*10**(math.floor(math.log10(abs(v)))-6) if v else 0 for v in row]
            for i in range(3):
                a, b = (i+1)%3, (i+2)%3
                roundoff[i] += abs(nodes[t][a]+u[t][a]-centre[a])*error[b]+abs(nodes[t][b]+u[t][b]-centre[b])*error[a]
    residual = [sum(v[i] for v in reactions.values()) for i in range(3)]
    moment_residual = [sum(v[i] for v in moments.values()) for i in range(3)]
    centroid_residual = [sum(v[i] for v in centroid_moments.values()) for i in range(3)]
    # Fixed physical characteristic length: the 400 mm coupon, not an observed
    # residual. A 1 ppm force*length numerical tolerance is not a capacity limit.
    moment_tolerance = max(1., 1e-6*400*math.sqrt(sum(v*v for v in reactions['DRIVE'])))
    if max(map(abs, residual)) > .1 or max(map(abs, moment_residual+centroid_residual)) > moment_tolerance:
        raise ValueError(f'Force/moment equilibrium failed: {residual}, {moment_residual}')
    dis = _rows(text, 'relative contact displacement')
    pressure = _rows(text, 'contact stress')
    count = _rows(text, 'total number of contact elements')
    if len(count) != 1 or len(count[0]) != 1 or int(count[0][0]) != len(dis) or len(dis) != len(pressure):
        raise ValueError('Incomplete contact integration output')
    if not dis:
        raise ValueError('No contact')
    max_pressure, max_overlap = 0., 0.
    for d, p in zip(dis, pressure, strict=True):
        if len(d) != 5 or len(p) != 5 or d[:2] != p[:2]:
            raise ValueError('Mismatched contact points')
        dv, pv = [float(v) for v in d[2:]], [float(v) for v in p[2:]]
        if not all(math.isfinite(v) for v in dv+pv) or pv[0] < -1e-7 or max(map(abs, pv[1:])) > 1e-7:
            raise ValueError('Nonfinite, tensile, or frictional contact')
        # Observed CalculiX2.21 face-to-face DAT convention: compressive
        # penetration is NEGATIVE CDIS, positive CSTR, p=-K*CDIS.
        if abs(pv[0]-max(0., -context['args']['penalty']*dv[0])) > .001:
            raise ValueError('Contact penalty law/sign mismatch')
        max_pressure = max(max_pressure, pv[0])
        max_overlap = max(max_overlap, -dv[0])
    if max_pressure <= 0:
        raise ValueError('No compressive load transfer')
    pair_centres = {}
    if 'geometry' in context:
        for label, station in zip(context['pins'], context['geometry']['stations_mm'], strict=True):
            match = re.search(rf'statistics for slave set WOOD_SURF, master set {label}_SURF[^\n]*\n'
                              r'(.*?)(?=\n\s*statistics for slave|\Z)', text, re.DOTALL)
            if not match:
                raise ValueError('Missing per-pin contact statistics')
            force = re.search(r'total surface force[^\n]*\n\s*\n([^\n]+)', match[1])
            centre = re.search(r'center of gravity and mean normal\s*\n\s*\n([^\n]+)', match[1])
            if not force or not centre:
                raise ValueError('Incomplete per-pin contact statistics')
            values, xyz = [float(v) for v in force[1].split()], [float(v) for v in centre[1].split()]
            if len(values) != 6 or len(xyz) != 6 or not all(math.isfinite(v) for v in values+xyz):
                raise ValueError('Invalid per-pin contact statistics')
            if any(abs(a-b) > .1 for a, b in zip(values[:3], reactions[label+'_N'], strict=True)):
                raise ValueError('Contact force differs from independent pin reaction')
            if not (-1 <= xyz[0] <= 39.1 and abs(xyz[1]-station) <= 6 and abs(xyz[2]) <= 6):
                raise ValueError('Active contact not localized at its matching bore')
            pair_centres[label] = xyz[:3]
    return {'reactions_n': reactions, 'reaction_moments_deformed_nmm': moments,
            'force_residual_n': residual, 'moment_residual_nmm': moment_residual,
            'moment_about_drive_centroid_residual_nmm': centroid_residual,
            'moment_rf_roundoff_bound_nmm': roundoff, 'moment_tolerance_nmm': moment_tolerance,
            'moment_residual_fraction_of_limit': max(map(abs, moment_residual+centroid_residual))/moment_tolerance,
            'completed_time': float(increments[-1][4]), 'increments': len(increments),
            'last_increment_iterations': int(increments[-1][3]), 'nodes': len(nodes),
            'contact_points': len(dis), 'max_contact_pressure_mpa': max_pressure,
            'contact_pair_centres_mm': pair_centres,
            'max_penalty_penetration_mm': max_overlap,
            'max_displacement_mm': max(math.sqrt(sum(v*v for v in row)) for row in u.values()),
            'driven_force_axis_n': reactions['DRIVE'][axis],
            'pin_axis_share': [-reactions[k+'_N'][axis]/reactions['DRIVE'][axis] for k in context['pins']]}
