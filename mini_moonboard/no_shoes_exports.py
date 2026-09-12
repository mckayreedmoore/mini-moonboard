"""Publish the no-shoes candidate, reusing authenticated unchanged meshes."""
import hashlib
import json
from pathlib import Path

import cadquery as cq

from . import no_shoes_frame as model
from .box_exports import exact_bounds


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export(root=Path('site')):
    root = Path(root)
    sources = {}
    data = {}
    for key in (model.previous.KEY, 'round-reinforcement-development'):
        directory = root/'hybrid'/key
        manifest = json.loads((directory/'manifest.json').read_text())
        for name, value in manifest['source_sha256'].items():
            if digest(name) != value:
                raise ValueError('Changed inherited source: '+name)
            sources[name] = value
        for name, value in manifest['artifact_sha256'].items():
            if digest(directory/name) != value:
                raise ValueError('Changed inherited artifact: '+name)
        data[key] = json.loads((directory/'parts.json').read_text())
    for name in ('no_shoes_frame.py', 'no_shoes_exports.py'):
        path = 'mini_moonboard/'+name
        sources[path] = digest(path)
    previous = data[model.previous.KEY]
    items = [p for p in previous['parts'] if not model.changed_mesh(p['name'])]
    # These additions are independent of the steel shoe revision. Neither its
    # header nor either of its trimmed/drilled outer rims is inherited.
    items.extend(p for p in data['round-reinforcement-development']['parts']
                 if p['name'].startswith(('hold_tnut_', 'fastener_kicker_header_')))
    items = [{**p, 'translation_mm': list(model.SHIFT.toTuple())} for p in items]
    directory = root/'hybrid'/model.KEY
    meshes = directory/'models'
    meshes.mkdir(parents=True, exist_ok=True)
    parts = model.parts()
    for part in parts:
        if not model.changed_mesh(part.name):
            continue
        path = meshes/(part.name+'.stl')
        cq.exporters.export(part.shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(part.shape)
        items.append({'name': part.name, 'path': str(path.relative_to(root)),
                      'viewer_aabb_mm': [bounds.xlen, bounds.ylen, bounds.zlen],
                      'fabrication': {'dimensions_mm': list(part.blank), 'kind': 'part',
                                      'description': model.LIMITS,
                                      'clearance_status': 'Unassessed geometry candidate; NOT build-ready'}})
    if len(items) != len({p['name'] for p in items}):
        raise ValueError('Duplicate viewer identity')
    design = {**previous['design'], 'key': model.KEY,
              'status': '2×6 legs · catalog base angles · no steel shoes · NOT build-ready',
              'description': model.LIMITS, 'panel_kicker_screw_count': 66,
              'hold_tnut_count': 142, 'hold_bolt_count': 0,
              'leg_stock': '2x6', 'outer_rim_stock': '2x6',
              'leg_bolt_count': 8, 'bolts_per_leg': 4,
              'custom_steel_shoe_count': 0, 'restored_base_angle_count': 2,
              'main_face_height_mm': model.KICKER_HEIGHT_MM, 'kicker_hold_height_mm': 202.,
              'pad_height_mm': model.PAD_HEIGHT_MM, 'exposed_kicker_mm': model.EXPOSED_KICKER_MM,
              'qualified_for_design': False}
    bounds = exact_bounds(cq.Compound.makeCompound([p.shape for p in parts]))
    low = [min(previous['bounds_mm'][0][i]+model.SHIFT.toTuple()[i], getattr(bounds, axis+'min'))
           for i, axis in enumerate('xyz')]
    high = [max(previous['bounds_mm'][1][i]+model.SHIFT.toTuple()[i], getattr(bounds, axis+'max'))
            for i, axis in enumerate('xyz')]
    (directory/'parts.json').write_text(json.dumps({'design': design, 'parts': items,
                        'bounds_mm': [low, high]}, indent=2)+'\n')
    assembly = cq.Assembly(name=model.KEY)
    for part in parts:
        assembly.add(part.shape, name=part.name)
    for connection in model.connections():
        assembly.add(cq.Compound.makeCompound(connection.components()), name='fastener_'+connection.name)
    assembly.save(str(directory/'assembly.step'))
    for name, expected in sources.items():
        if digest(name) != expected:
            raise ValueError('Source changed during export: '+name)
    artifacts = {str(p.relative_to(directory)): digest(p) for p in sorted(directory.rglob('*'))
                 if p.is_file() and p.name != 'manifest.json'}
    inherited = {p['path']: digest(root/p['path']) for p in items
                 if not p['path'].startswith('hybrid/'+model.KEY+'/')}
    (directory/'manifest.json').write_text(json.dumps({'design': design, 'source_sha256': sources,
        'artifact_sha256': artifacts, 'inherited_mesh_sha256': inherited,
        'step_scope': 'Wood, brackets, T-nuts and complete modeled fasteners; electrical display omitted.'}, indent=2)+'\n')
    return directory


if __name__ == '__main__':
    print(export())
