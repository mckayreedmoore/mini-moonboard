"""Build the current viewer and STEP directly from CAD, without archived assets."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import cadquery as cq

from . import no_shoes_frame as model
from .box_exports import exact_bounds
from .export import _export_step
from .panel_grid_v2 import main_tnut_datums
from .split_center_hardware import BOLT_ROLES

ROOT = Path(__file__).resolve().parents[1]
STATUS = 'Development geometry; NOT build-ready'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sources():
    """Follow local Python imports; record the data files those factories read.

    Historical factories remain source dependencies, but their exported meshes,
    manifests, reports and unrelated experiments are not build inputs.
    """
    pending = [Path(__file__).resolve(), ROOT/'mini_moonboard/__init__.py']
    paths = set()
    while pending:
        path = pending.pop()
        if path in paths:
            continue
        paths.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.level == 1:
                names = [node.module] if node.module else [alias.name for alias in node.names]
                for name in names:
                    dependency = path.parent/(name.replace('.', '/')+'.py')
                    if dependency.is_file():
                        pending.append(dependency)
    paths.update(ROOT/name for name in (
        'uv.lock', 'pyproject.toml', 'docs/ml24z-reference.json',
        'docs/panel-insert-reference.json', 'docs/led-wiring-reference.json',
        'docs/round-service-wiring-reference.json',
    ))
    wiring = json.loads((ROOT/'docs/round-service-wiring-reference.json').read_text())
    paths.add(ROOT/wiring['route_reference'])
    return {str(path.relative_to(ROOT)): digest(path) for path in sorted(paths)}


def viewer_parts(parts, connections):
    """Yield CAD bodies and presentation metadata, preserving selectable bolt stacks."""
    for part in parts:
        kind = 'tnut' if part.name.startswith('hold_tnut_') else 'part'
        yield part.name, part.shape, {
            'dimensions_mm': list(part.blank), 'kind': kind,
            'description': part.description, 'clearance_status': STATUS,
        }
    for part in model.electrical_parts():
        bounds = exact_bounds(part.shape)
        yield part.name, part.shape, {
            'dimensions_mm': [bounds.xlen, bounds.ylen, bounds.zlen],
            'kind': part.kind, 'description': 'Provisional electrical display envelope',
            'clearance_status': STATUS, 'mass_included': False,
            'mass_status': 'Unknown electrical mass; excluded from estimate',
        }
    for connection in connections:
        components = connection.components()
        prefix = 'fastener_'+connection.name
        if connection.kind == 'bolt':
            for role, shape in zip(BOLT_ROLES, components, strict=True):
                bounds = exact_bounds(shape)
                yield prefix+'_'+role, shape, {
                    'dimensions_mm': [bounds.xlen, bounds.ylen, bounds.zlen],
                    'kind': 'bolt', 'connection_name': connection.name, 'hardware_role': role,
                    'description': role.replace('_', ' ')+'; '+connection.product_status,
                    'clearance_status': STATUS,
                }
        else:
            yield prefix, cq.Compound.makeCompound(components), {
                'dimensions_mm': [connection.length, connection.diameter, connection.diameter],
                'kind': connection.kind, 'description': connection.product_status,
                'clearance_status': STATUS,
            }


def design_metadata(parts, connections):
    bolts = [c for c in connections if c.kind == 'bolt']
    kicker_heights = {row['rear_seating_xyz_mm'][2] for row in model.tnuts.datums(model)
                      if row['panel'].startswith('kicker_')}
    if len(kicker_heights) != 1:
        raise ValueError('Viewer requires a single kicker foothold row')
    return {
        'key': model.KEY,
        'status': '2×6 legs · catalog base angles · no steel shoes · NOT build-ready',
        'description': model.LIMITS, 'qualified_for_design': False,
        'panel_kicker_screw_count': len(model.panel_connections()),
        'electrical_mass_included': False, 'panel_kicker_insert_count': 0,
        'future_insert_pilots_cut': False,
        'tnut_row_stations_mm': [main_tnut_datums()[f'A{row}'][1] for row in range(1, 13)],
        'hold_tnut_count': sum(p.name.startswith('hold_tnut_') for p in parts),
        'hold_bolt_count': 0, 'leg_stock': '2x6', 'outer_rim_stock': '2x6',
        'leg_bolt_count': len(bolts), 'bolts_per_leg': len(bolts)//2,
        'custom_steel_shoe_count': 0,
        'restored_base_angle_count': sum(p.name in ('clip_angle_base_left', 'clip_angle_base_right')
                                         for p in parts),
        'main_face_height_mm': model.KICKER_HEIGHT_MM,
        'kicker_hold_height_mm': kicker_heights.pop(),
        'pad_height_mm': model.PAD_HEIGHT_MM, 'exposed_kicker_mm': model.EXPOSED_KICKER_MM,
    }


def export(root=Path('site')):
    """Regenerate every current asset; ``root`` may be an empty directory."""
    source_hashes = sources()
    root = Path(root)
    directory = root/'hybrid'/model.KEY
    meshes = directory/'models'
    meshes.mkdir(parents=True, exist_ok=True)
    parts, connections = model.parts(), model.connections()
    design = design_metadata(parts, connections)
    items, shapes = [], []
    names = set()
    for name, shape, fabrication in viewer_parts(parts, connections):
        if name in names:
            raise ValueError('Duplicate viewer identity: '+name)
        if not shape.isValid():
            raise ValueError('Invalid current CAD body: '+name)
        names.add(name)
        path = meshes/(name+'.stl')
        cq.exporters.export(shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(shape)
        items.append({'name': name, 'path': str(path.relative_to(root)),
                      'viewer_aabb_mm': [bounds.xlen, bounds.ylen, bounds.zlen],
                      'fabrication': fabrication})
        shapes.append(shape)
    bounds = exact_bounds(cq.Compound.makeCompound(shapes))
    inventory = {'design': design, 'parts': items,
                 'bounds_mm': [[getattr(bounds, axis+end) for axis in 'xyz']
                               for end in ('min', 'max')]}
    (directory/'parts.json').write_text(json.dumps(inventory, indent=2, allow_nan=False)+'\n')
    assembly = cq.Assembly(name=model.KEY)
    for part in parts:
        assembly.add(part.shape, name=part.name)
    for connection in connections:
        assembly.add(cq.Compound.makeCompound(connection.components()), name='fastener_'+connection.name)
    _export_step(assembly, directory/'assembly.step')
    if sources() != source_hashes:
        raise ValueError('Source changed during export')
    artifacts = [directory/'parts.json', directory/'assembly.step',
                 *(meshes/(name+'.stl') for name in sorted(names))]
    manifest = {'design': design, 'source_sha256': source_hashes,
                'artifact_sha256': {str(p.relative_to(directory)): digest(p) for p in artifacts},
                'inherited_mesh_sha256': {},
                'step_scope': 'Wood, brackets, T-nuts and complete modeled fasteners; electrical display omitted.'}
    (directory/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return directory


def check(root=Path('site')):
    """Rebuild into an empty directory and compare all committed current assets."""
    published = Path(root)/'hybrid'/model.KEY
    with TemporaryDirectory(prefix='moonboard-current-rebuild-') as temporary:
        rebuilt = export(Path(temporary))
        manifest = json.loads((rebuilt/'manifest.json').read_text())
        for name, expected in manifest['artifact_sha256'].items():
            path = published/name
            if not path.is_file() or digest(path) != expected:
                raise ValueError('Current candidate rebuild differs: '+str(path))
        if json.loads((published/'manifest.json').read_text()) != manifest:
            raise ValueError('Current candidate manifest differs from rebuild')
    return published


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('site'))
    parser.add_argument('--check', action='store_true', help='Rebuild in a temporary directory and verify committed assets')
    args = parser.parse_args()
    print(check(args.root) if args.check else export(args.root))
