"""Estimate every viewer assembly from its actual meshes, preserving CAD evidence."""
import gzip
import hashlib
import json
import math
import struct
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path('site')
DENSITIES = {'wood/plywood': 600., 'steel': 7850., 'die-cast zinc assumption': 6700.}
AUDITED = {key+'-development': Path('fea/results')/(stem+'-floor-v1.json.gz') for key, stem in (
    ('selective-2x6', 'selective'), ('split-center', 'split-center'),
    ('infill-panel', 'infill-panel'), ('angle-base', 'angle-base'),
    ('horizontal-service', 'horizontal-service'), ('round-bore-service', 'round-service'),
    ('round-insert', 'round-insert'))}
AUDITED['round-reinforcement-development'] = Path('docs/round-reinforcement-review/review.json')
WOOD_PREFIXES = {'base', 'box', 'cheek', 'cross', 'easy', 'kicker', 'lean', 'leg', 'lumber',
                 'main', 'mid', 'panel', 'rear', 'rib', 'seam', 'timber', 'wood'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def volume(data):
    """Closed oriented STL shell volume; compound overlaps remain explicit."""
    count = struct.unpack_from('<I', data, 80)[0] if len(data) >= 84 else 0
    if count and len(data) == 84+50*count:
        dtype = np.dtype([('normal', '<f4', 3), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
        triangles = np.frombuffer(data, dtype=dtype, offset=84)['vertices'].astype(float)
    else:
        vertices = [list(map(float, line.split()[1:])) for line in data.decode('ascii').splitlines()
                    if line.strip().startswith('vertex ')]
        if not vertices or len(vertices) % 3:
            raise ValueError('Invalid STL triangle inventory')
        triangles = np.asarray(vertices).reshape((-1, 3, 3))
    if not np.isfinite(triangles).all():
        raise ValueError('Nonfinite STL coordinates')
    _, indices = np.unique(triangles.reshape((-1, 3)), axis=0, return_inverse=True)
    indices = indices.reshape((-1, 3))
    directed = np.concatenate((indices[:, [0, 1]], indices[:, [1, 2]], indices[:, [2, 0]]))
    edges = np.sort(directed, axis=1)
    _, edge_ids, counts = np.unique(edges, axis=0, return_inverse=True, return_counts=True)
    balance = np.bincount(edge_ids, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1))
    if (counts % 2).any() or balance.any():
        raise ValueError('Open STL or inconsistent shell orientation; mass unavailable')
    triangles = triangles-triangles.mean(axis=(0, 1))
    value = abs(np.einsum('ij,ij->i', triangles[:, 0],
                         np.cross(triangles[:, 1], triangles[:, 2])).sum()/6)
    if not math.isfinite(value) or value <= 0:
        raise ValueError('Nonpositive STL volume')
    return float(value)


def material(part):
    name, kind = part['name'], part['fabrication'].get('kind')
    if kind in ('light', 'wire'):
        return None  # Purchased component mass is unknown, not a material-density assumption.
    if kind == 'insert' or name.startswith('insert_'):
        return 'die-cast zinc assumption'
    if kind in ('screw', 'bolt', 'tnut') or name.startswith(('fastener_', 'analysis_', 'angle_', 'clip_')):
        return 'steel'
    if name.startswith('transition_') and '_angle_' in name:
        return 'steel'
    if name.split('_')[0] in WOOD_PREFIXES:
        return 'wood/plywood'
    raise ValueError('Unclassified material: '+name)


def audited_mass(key, parts, viewer_directory=None):
    """Use a saved full CAD total only when sources and modeled identities match."""
    path = AUDITED.get(key)
    if path is None:
        return None
    raw = path.read_bytes()
    report = json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)
    if report['candidate'] != key:
        raise ValueError('Wrong mass report candidate')
    viewer_directory = Path(viewer_directory) if viewer_directory else ROOT/'hybrid'/key
    provenance = json.loads((viewer_directory/'manifest.json').read_text())
    for name, digest in provenance['artifact_sha256'].items():
        if sha((viewer_directory/name).read_bytes()) != digest:
            raise ValueError('Audited viewer artifact changed: '+name)
    if json.loads((viewer_directory/'parts.json').read_text())['parts'] != parts:
        raise ValueError('Viewer part inventory changed')
    for name, digest in provenance['source_sha256'].items():
        if sha(Path(name).read_bytes()) != digest:
            raise ValueError('Audited viewer source changed: '+name)
        if name in report['source_sha256'] and digest != report['source_sha256'][name]:
            raise ValueError('Viewer and CAD mass use different sources: '+name)
    for name, digest in report['source_sha256'].items():
        if sha(Path(name).read_bytes()) != digest:
            raise ValueError('Mass report source changed: '+name)
    names, roles, electrical = set(), defaultdict(list), []
    for part in parts:
        fabrication = part['fabrication']
        if fabrication.get('kind') in ('light', 'wire'):
            electrical.append(part['name'])
            continue
        if fabrication.get('kind') == 'bolt' and fabrication.get('connection_name'):
            roles[fabrication['connection_name']].append(fabrication.get('hardware_role'))
        elif part['name'] in names:
            raise ValueError('Duplicate unsplit part identity')
        else:
            names.add(part['name'])
    for name, supplied in roles.items():
        if sorted(supplied) != ['far_washer', 'head', 'near_washer', 'nut', 'shaft']:
            raise ValueError('Incomplete or duplicate bolt roles: '+name)
        if 'fastener_'+name in names:
            raise ValueError('Split and unsplit hardware duplicate')
        names.add('fastener_'+name)
    if electrical and report.get('electrical_mass_included') is not False:
        raise ValueError('CAD mass report must explicitly exclude unknown electrical mass')
    if names != {r['name'] for r in report['mass_inventory']}:
        raise ValueError('CAD mass inventory differs from viewer assembly: '+key)
    value = math.fsum(r['mass_kg'] for r in report['mass_inventory'])
    if not math.isclose(value, report['state']['mass_kg'], abs_tol=1e-8):
        raise ValueError('CAD mass inventory does not reconcile')
    return value, str(path), sha(raw)


def build(root=ROOT):
    root = Path(root)
    result = {}
    for manifest in sorted(root.rglob('parts.json')):
        data = manifest.read_bytes()
        record = json.loads(data)
        key = 'plywood' if manifest.parent == root else manifest.parent.name
        totals = defaultdict(float)
        assets, excluded = {}, []
        for part in record['parts']:
            path = root/part['path']
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError('Mesh path outside site')
            raw = path.read_bytes()
            mat = material(part)
            assets[part['path']] = sha(raw)
            if mat is None:
                excluded.append({'name': part['name'], 'path': part['path'],
                                 'kind': part['fabrication']['kind'],
                                 'reason': 'Purchased component mass unknown; excluded from estimate'})
            else:
                totals[mat] += volume(raw)/1e9*DENSITIES[mat]
        if len(assets) != len(record['parts']):
            raise ValueError('Duplicate mesh path')
        mesh_mass = math.fsum(totals.values())
        audited = audited_mass(key, record['parts'], manifest.parent)
        mass = audited[0] if audited else mesh_mass
        row = {'mass_kg': mass, 'mass_lb': mass/.45359237,
               'basis': 'audited CAD' if audited else 'mesh estimate',
               'scope': 'Modeled frame, panels and represented structural hardware only; excludes holds, their unmodeled '
                        'T-nuts and hold bolts, LEDs, wiring and glue. '
                        'Hardware absent from a historical concept is not estimated. Assumed densities; not measured weight.',
               'mesh_mass_kg': mesh_mass, 'mesh_material_mass_kg': dict(totals),
               'mesh_part_count': len(record['parts']),
               'manifest_path': str(manifest.relative_to(root)), 'manifest_sha256': sha(data),
               'mesh_sha256': assets}
        if excluded:
            row.update(excluded_mass_part_count=len(excluded), excluded_mass_parts=excluded)
        if any(p['fabrication'].get('kind') == 'tnut' for p in record['parts']):
            row['scope'] = ('Modeled frame, panels, structural hardware and T-nut envelopes; '
                            'excludes holds, hold bolts, unmodeled retention screws, LEDs and wiring. '
                            'T-nut dimensions include explicit display assumptions; densities and mass are unmeasured.')
        if audited:
            row.update(mass_report=audited[1], mass_report_sha256=audited[2])
        result[key] = row
    return {'models': result, 'assumed_density_kg_m3': DENSITIES,
            'generator_sha256': sha(Path(__file__).read_bytes()),
            'limits': 'Mesh estimates integrate oriented exported STL shells, not bounding boxes. '
                      'Compound hardware overlaps are not unioned in mesh estimates; coarse tessellation, '
                      'nominal threads and missing hardware affect accuracy. Audited CAD totals instead '
                      'use their authenticated complete inventories with unioned fastener envelopes. '
                      'These are mass estimates, not load ratings.'}


if __name__ == '__main__':
    result = build()
    (ROOT/'prototype-weights.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(f"Wrote weights for {len(result['models'])} viewer prototypes")
