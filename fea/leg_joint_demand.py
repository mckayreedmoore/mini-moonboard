"""Retained bonded-baseline leg free bodies; no solve or bolt/ply capacity."""
import argparse
import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path

from fea.floor_contact import FACES, integrated_weights
from fea.floor_contact_results import blocks, cross
from fea.full_frame_mortar import GRAVITY_PER_MM3_N, verify_deck
from fea.full_frame_refinement import read_archive, replay

ARCHIVE = Path('fea/results/full_frame_refinement/0.0625.tar.gz')
ARCHIVE_SHA = 'b7191366c224835aa6f790996671cc491ad3ae878cb9b797698a04d45e0b373b'
IMAGE = 'sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646'
TOL = 1e-5
LIMITS = ('Aggregate leg-on-rim demand of the retained undrilled bonded baseline only; '
          'conditional on baseline contact and global equilibrium. No individual bolt, '
          'ply, stitch, screw, candidate or capacity result. Nonlinear load history '
          'cannot be scaled to other climber weights. No new FEA solve.')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_new(path, data):
    with Path(path).open('x') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write('\n')


def select_leg(nodes, elements, sign, inner, outer, contains):
    """Select whole elements beyond rim; reject crossing or non-leg nodes."""
    selected = {}
    for e, ids in elements.items():
        coordinates = [nodes[n] for n in ids]
        if not any(sign*p[0] > inner+TOL for p in coordinates):
            continue
        if (len(ids) != 10 or len(set(ids)) != 10 or
                any(not all(math.isfinite(v) for v in p) or
                    not inner-TOL <= sign*p[0] <= outer+TOL or
                    not contains(p) for p in coordinates)):
            raise ValueError('Element crosses leg slab or leaves CAD leg')
        selected[e] = ids
    if not selected:
        raise ValueError('Missing leg elements')
    return selected


def validate_weights(nodes, weights, cad):
    if weights.keys() != nodes.keys() or not all(math.isfinite(w) for w in weights.values()):
        raise ValueError('Incomplete/nonfinite leg weights')
    volume = sum(weights.values())
    if volume <= 0:
        raise ValueError('Nonpositive leg volume')
    centre = [sum(weights[n]*p[i] for n, p in nodes.items())/volume for i in range(3)]
    if abs(volume/cad['volume_mm3']-1) > .001 or math.dist(centre, cad['centre_mm']) > 1:
        raise ValueError('Integrated leg volume/CG differs from CAD')
    return {'volume_mm3': volume, 'centre_mm': centre,
            'relative_volume_error': abs(volume/cad['volume_mm3']-1),
            'centre_error_mm': math.dist(centre, cad['centre_mm']),
            'negative_weight_count': sum(w < 0 for w in weights.values())}


def free_body(nodes, weights, displacement, supports, reaction, reference, gravity_factor):
    """Leg-on-rim = floor-on-leg + gravity, expressed about fixed reference."""
    if (displacement.keys() != nodes.keys() or weights.keys() != nodes.keys() or
            reaction.keys() != supports.keys() or not 0 <= gravity_factor <= 1):
        raise ValueError('Incomplete free-body output coverage')
    values = [v for mapping in (nodes, displacement, supports, reaction)
              for row in mapping.values() for v in row]+list(weights.values())+list(reference)
    if not all(math.isfinite(v) for v in values):
        raise ValueError('Nonfinite free-body input')
    floor_force = [sum(f[i] for f in reaction.values()) for i in range(3)]
    floor_moment = [sum(cross([p[j]-reference[j] for j in range(3)], reaction[n])[i]
                        for n, p in supports.items()) for i in range(3)]
    gravity_force, gravity_moment = [0., 0., 0.], [0., 0., 0.]
    for n, weight in weights.items():
        force = (0., 0., -weight*GRAVITY_PER_MM3_N*gravity_factor)
        position = [nodes[n][i]+displacement[n][i]-reference[i] for i in range(3)]
        moment = cross(position, force)
        for i in range(3):
            gravity_force[i] += force[i]
            gravity_moment[i] += moment[i]
    resultant = [a+b for a, b in zip(floor_force+floor_moment,
                                    gravity_force+gravity_moment, strict=True)]
    return {'floor_on_leg_force_moment': floor_force+floor_moment,
            'gravity_force_moment': gravity_force+gravity_moment,
            'leg_on_rim_force_moment': resultant,
            'rim_on_leg_force_moment': [-v for v in resultant]}


def local_components(resultant, axes):
    # An orthonormal right-handed basis avoids pseudovector sign ambiguity.
    if (len(axes) != 3 or any(len(a) != 3 for a in axes) or
            any(abs(sum(x*y for x, y in zip(a, b, strict=True))-float(i == j)) > 1e-10
                for i, a in enumerate(axes) for j, b in enumerate(axes)) or
            math.dist(cross(axes[0], axes[1]), axes[2]) > 1e-10):
        raise ValueError('Invalid local basis')
    return [sum(resultant[offset+i]*axis[i] for i in range(3))
            for offset in (0, 3) for axis in axes]


def prepare_geometry(nodes, elements, groups, record):
    import cadquery as cq

    from mini_moonboard import box_frame as b
    from mini_moonboard import footprint_frame as frame

    for name, expected in record['geometry_source_sha256'].items():
        if sha(name) != expected:
            raise ValueError('Frozen CAD source differs: '+name)
    parts = {p.name: p.shape for p in frame.parts(100, drilled=False)}
    result = {}
    for side, sign in (('left', -1), ('right', 1)):
        shape, rim = parts['leg_'+side], parts['box_side_'+side]
        bounds = shape.BoundingBox()
        inner, outer = sorted((sign*bounds.xmin, sign*bounds.xmax))
        if abs(inner-(b.HALF+b.THICKNESS)) > TOL or abs(outer-inner-38.1) > TOL:
            raise ValueError('Unexpected leg slab')
        cache = {}
        def contains(p, cache=cache, shape=shape):
            key = tuple(p)
            if key not in cache:
                cache[key] = shape.isInside(cq.Vector(*p), TOL)
            return cache[key]
        chosen = select_leg(nodes, elements, sign, inner, outer, contains)
        ids = {n for row in chosen.values() for n in row}
        other = {n for e, row in elements.items() if e not in chosen for n in row}
        shared = ids & other
        if not shared or any(abs(sign*nodes[n][0]-inner) > TOL or
                             not rim.isInside(cq.Vector(*nodes[n]), TOL) for n in shared):
            raise ValueError('Leg exchanges load outside rim interface')
        for name, other_shape in parts.items():
            if name.startswith('angle_') or name in ('leg_'+side, 'box_side_'+side):
                continue
            other_bounds = other_shape.BoundingBox()
            if (max(sign*other_bounds.xmin, sign*other_bounds.xmax) > inner+TOL
                    and not name.startswith('leg_')):
                raise ValueError('Other timber occupies outer leg slab')
        floor = groups[side.upper()]
        if any(e not in chosen for e, face in floor):
            raise ValueError('Floor patch includes non-leg element')
        actual_floor = [(e, face) for e, row in chosen.items()
                        for face, indices in enumerate(FACES, 1)
                        if all(abs(nodes[row[i]][2]) < TOL for i in indices)]
        if set(actual_floor) != set(map(tuple, floor)):
            raise ValueError('Incomplete isolated leg floor patch')
        if ids & set(record['load_nodes']):
            raise ValueError('Climber loads applied directly to leg')
        bolts = [c for c in frame.connections() if 'leg_'+side in c.members]
        if len(bolts) != 4 or any(c.kind != 'bolt' for c in bolts):
            raise ValueError('Expected four upper bolt locations')
        reference = [sign*inner, *[sum(c.start.toTuple()[i] for c in bolts)/4 for i in (1, 2)]]
        uphill = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized().toTuple()
        axes = [(1., 0., 0.), uphill, tuple(cross((1., 0., 0.), uphill))]
        result[side] = {'nodes': {n: nodes[n] for n in sorted(ids)}, 'elements': chosen,
                        'interface_nodes': sorted(shared), 'floor_faces': floor,
                        'cad': {'volume_mm3': shape.Volume(), 'centre_mm': shape.Center().toTuple(),
                                'x_interval_mm': [bounds.xmin, bounds.xmax]},
                        'reference_mm': reference, 'local_axes_world': axes,
                        'local_axes_names': ['global X', 'upper member uphill S', 'board normal N'],
                        'reference_basis': 'Fixed undeformed rim/leg interface at mean four upper bolt Y/Z; not a moving material point'}
    if set(result['left']['elements']) & set(result['right']['elements']):
        raise ValueError('Overlapping leg ownership')
    return result


def integrate(directory):
    import gmsh
    directory = Path(directory)
    data = json.loads((directory/'input.json').read_text())
    results = {}
    for side, item in data['legs'].items():
        nodes = {int(n): p for n, p in item['nodes'].items()}
        elements = {int(e): row for e, row in item['elements'].items()}
        weights = integrated_weights(elements, nodes)
        results[side] = {'weights_mm3': weights, 'validation': validate_weights(nodes, weights, item['cad'])}
    save_new(directory/'integration.json', {'input_sha256': sha(directory/'input.json'),
                                          'gmsh_version': gmsh.__version__, 'legs': results})


def assemble_endpoints(data, nodes, ground, bottom, baseline, legs, integration):
    """Pure DAT-to-report assembly; callers authenticate mesh and evidence first."""
    if set(legs) != {'left', 'right'} or set(integration['legs']) != set(legs):
        raise ValueError('Incomplete leg inventory')
    parsed, endpoints = blocks(data), []
    for endpoint in baseline['diagnostic_endpoints']:
        time = endpoint['time']
        u = parsed.get(('displacements', 'WOODN', time), {})
        if u.keys() != nodes.keys():
            raise ValueError('Incomplete timber output')
        row = {'time': time, 'baseline_global_gate_pass': endpoint['global_gate_pass'], 'legs': {}}
        for side, item in legs.items():
            leg_nodes = {int(n): p for n, p in item['nodes'].items()}
            weights = {int(n): w for n, w in integration['legs'][side]['weights_mm3'].items()}
            validate_weights(leg_nodes, weights, item['cad'])
            name = side.upper()
            rf = parsed.get(('forces', 'GROUND_'+name, time), {})
            gu = parsed.get(('displacements', 'GROUND_'+name, time), {})
            if rf.keys() != ground[name].keys() or gu.keys() != ground[name].keys():
                raise ValueError('Incomplete ground output')
            positions = {n: [a+b for a, b in zip(ground[name][n], gu[n], strict=True)] for n in bottom[name]}
            result = free_body(leg_nodes, weights, {n: u[n] for n in leg_nodes},
                               positions, {n: rf[n] for n in bottom[name]}, item['reference_mm'], min(time, 1.))
            result['leg_on_rim_local_force_moment'] = local_components(result['leg_on_rim_force_moment'], item['local_axes_world'])
            row['legs'][side] = result
        endpoints.append(row)
    return endpoints


def run():
    if sha(ARCHIVE) != ARCHIVE_SHA:
        raise ValueError('Exact retained archive differs')
    files = read_archive(ARCHIVE)
    record = json.loads(files['frame.json'])
    nodes, elements, groups, ground, bottom = verify_deck(files['frame.inp'].decode(), record)
    baseline = replay(files)
    legs = prepare_geometry(nodes, elements, groups, record)
    directory = Path(tempfile.mkdtemp(prefix='leg-joint-demand-', dir='fea/generated')).resolve()
    print(directory, flush=True)
    sources = [Path('fea')/name for name in ('leg_joint_demand.py', 'floor_contact.py',
               'floor_contact_results.py', 'full_frame_mortar.py', 'full_frame_refinement.py',
               'floor_contact_recovery.py')]+sorted(Path('mini_moonboard').glob('*.py'))
    source_hashes = {}
    for source in sources:
        target = directory/'launch_sources'/source
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        source_hashes[str(source)] = sha(target)
    save_new(directory/'input.json', {'archive': str(ARCHIVE), 'archive_sha256': ARCHIVE_SHA,
             'archive_members_sha256': {name: hashlib.sha256(value).hexdigest() for name, value in files.items()},
             'source_sha256': source_hashes, 'frozen_geometry_source_sha256': record['geometry_source_sha256'],
             'image_id': IMAGE, 'limits': LIMITS, 'legs': legs,
             'gates': {'relative_volume': .001, 'centre_mm': 1., 'geometry_mm': TOL}})
    command = ['docker', 'run', '--rm', '--network=none', '--read-only', '--memory=2g', '--cpus=2',
               '--tmpfs', '/tmp:rw,size=64m', '-v', f'{directory}:/evidence:rw',
               '-v', f'{directory / "launch_sources"}:/sources:ro', '-w', '/sources',
               '-e', 'PYTHONDONTWRITEBYTECODE=1', IMAGE, 'python3', '-m', 'fea.leg_joint_demand',
               '--integrate', '/evidence']
    with (directory/'integration.log').open('x') as log:
        execution = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=120, check=False)
    if execution.returncode:
        raise ValueError('Leg integration failed; retained '+str(directory))
    integration = json.loads((directory/'integration.json').read_text())
    if integration['input_sha256'] != sha(directory/'input.json'):
        raise ValueError('Integration input changed')
    for source, expected in source_hashes.items():
        if sha(source) != expected or sha(directory/'launch_sources'/source) != expected:
            raise ValueError('Audit source changed during run')
    endpoints = assemble_endpoints(files['frame.dat'].decode(), nodes, ground, bottom, baseline, legs, integration)
    save_new(directory/'report.json', {'limits': LIMITS, 'archive_sha256': ARCHIVE_SHA,
             'input_sha256': sha(directory/'input.json'), 'integration_sha256': sha(directory/'integration.json'),
             'integration_log_sha256': sha(directory/'integration.log'), 'integration_command': command,
             'units': 'N and Nmm; forces first then moments', 'endpoints': endpoints,
             'gravity_basis': 'Selected whole-element consistent weights, signed quadratic weights retained; deformed nodal positions',
             'floor_basis': 'Noncontact bottom SPC RF only; massless static ground brick transmits equal opposite resultants',
             'numerical_limits': 'Uses printed DAT values. CAD gates are geometry diagnostics, not uncertainty estimates. No independently measured interface traction or new contact acceptance.'})
    return directory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--integrate', type=Path)
    args = parser.parse_args()
    integrate(args.integrate) if args.integrate else run()
