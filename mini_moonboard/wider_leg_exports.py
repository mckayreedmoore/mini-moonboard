"""Publish the assessed wider-leg candidate without changing selected geometry.

Unchanged meshes reference the preserved 2x6 viewer assets. Only four revised
wood members and twelve complete eight-piece bolt stacks receive new meshes.
"""
import hashlib
import json
from pathlib import Path

import cadquery as cq

from . import wider_leg_frame as model
from .box_exports import exact_bounds


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export(root=Path('site')):
    root = Path(root)
    inherited = root/'hybrid'/model.previous.KEY
    previous = json.loads((inherited/'parts.json').read_text())
    provenance = json.loads((inherited/'manifest.json').read_text())
    for name, value in provenance['artifact_sha256'].items():
        if digest(inherited/name) != value:
            raise ValueError('Changed inherited artifact: '+name)
    sources = model.source_hashes()
    for name, value in provenance['source_sha256'].items():
        if digest(name) != value:
            raise ValueError('Changed inherited source: '+name)
    directory = root/'hybrid'/model.KEY
    meshes = directory/'models'
    meshes.mkdir(parents=True, exist_ok=True)
    # The predecessor's other members and fasteners retain their identities and
    # source geometry. Do not copy 128 MB of identical meshes into another tree.
    items = [p for p in previous['parts'] if p['name'] not in model.CHANGED_NAMES
             and not p['fabrication'].get('connection_name', '').startswith('lumber_leg_bolt_')]
    records = [(p.name, p.shape, 'part', p.description, {}) for p in model.parts()
               if p.name in model.CHANGED_NAMES]
    for connection in model.connections():
        if not isinstance(connection, model.WiderLegBolt):
            continue
        records.extend(('fastener_'+connection.name+'_'+role, shape, 'bolt', connection.product_status,
                        {'connection_name': connection.name, 'hardware_role': role,
                         'stack_roles': list(model.COMPONENT_LABELS)})
                       for role, shape in zip(model.COMPONENT_LABELS, connection.components(), strict=True))
    for name, shape, kind, description, metadata in records:
        path = meshes/(name+'.stl')
        cq.exporters.export(shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(shape)
        dimensions = [bounds.xlen, bounds.ylen, bounds.zlen]
        items.append({'name': name, 'path': str(path.relative_to(root)),
                      'viewer_aabb_mm': dimensions,
                      'fabrication': {'dimensions_mm': dimensions, 'kind': kind,
                                      'description': description,
                                      'clearance_status': 'Nominal fit checked; resistance conditional; NOT build-ready',
                                      **metadata}})
    if len(items) != len({p['name'] for p in items}):
        raise ValueError('Duplicate viewer identity')
    bounds = exact_bounds(cq.Compound.makeCompound([r[1] for r in records]))
    old_low, old_high = previous['bounds_mm']
    low = [min(old_low[i], getattr(bounds, axis+'min')) for i, axis in enumerate('xyz')]
    high = [max(old_high[i], getattr(bounds, axis+'max')) for i, axis in enumerate('xyz')]
    design = {**previous['design'], 'key': model.KEY,
              'status': '2×8 legs and outer rims · six ½-inch bolts per leg · assessed, NOT build-ready',
              'description': 'Single 2×8 legs and matching outer rims with catalog leg hardware. '
              'The inherited assembly still includes provisional custom steel base shoes. '
              'Conditional leg checks and nominal fit do not qualify this candidate for construction. '
              'Loaded-edge interpretation, contact forces, prying and plate material remain limited. '
              'The selected structural-screw candidate is preserved.',
              'leg_stock': '2x8', 'outer_rim_stock': '2x8', 'leg_bolt_count': 12,
              'bolts_per_leg': 6, 'leg_bolt_diameter_mm': 12.7,
              'qualified_for_design': False}
    (directory/'parts.json').write_text(json.dumps({'design': design, 'parts': items,
                                                   'bounds_mm': [low, high]}, indent=2)+'\n')
    if sources != model.source_hashes():
        raise ValueError('CAD sources changed during export')
    sources['mini_moonboard/wider_leg_exports.py'] = digest(__file__)
    artifacts = {str(p.relative_to(directory)): digest(p) for p in sorted(directory.rglob('*'))
                 if p.is_file() and p.name != 'manifest.json'}
    inherited_assets = {p['path']: digest(root/p['path']) for p in items
                        if not p['path'].startswith('hybrid/'+model.KEY+'/')}
    (directory/'manifest.json').write_text(json.dumps({'design': design, 'source_sha256': sources,
        'artifact_sha256': artifacts, 'inherited_mesh_sha256': inherited_assets}, indent=2)+'\n')
    return directory


if __name__ == '__main__':
    print(export())
