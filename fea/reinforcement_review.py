"""Review an isolated reinforcement candidate; no construction release."""
import argparse
import hashlib
import importlib
import json
from collections import Counter
from pathlib import Path

import cadquery as cq

from fea.horizontal_service_floor import floor_contact_bodies, select_floor_supports
from fea.round_insert_floor import current_mass, inventory_state
from fea.round_structural_global_envelope import locations
from fea.round_structural_global_envelope import sources as baseline_sources
from fea.split_center_floor import verify_loaded_sources
from fea.user_load_envelope import envelope, hull
from mini_moonboard import round_structural_frame as baseline
from mini_moonboard.box_exports import exact_bounds
from mini_moonboard.raster import render
from mini_moonboard.split_center_hardware import BOLT_ROLES


def sources():
    paths = set(baseline_sources()) | {
        'fea/reinforcement_review.py', 'mini_moonboard/raster.py',
        'docs/moonboard-hold-hardware-reference.json',
    }
    paths.update(str(p) for p in Path('mini_moonboard').glob('*reinforcement*.py'))
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(paths)}


def connection_record(connection):
    return {'name': connection.name, 'members': list(connection.members),
            'kind': connection.kind, 'length_mm': connection.length,
            'diameter_mm': connection.diameter, 'grip_mm': connection.grip,
            'start_xyz_mm': list(connection.start.toTuple()),
            'direction_xyz': list(connection.direction.toTuple()),
            'product_status': connection.product_status}


def interference(first, second):
    """Return occupied-volume interference after a bounding-box rejection."""
    a, b = first.BoundingBox(), second.BoundingBox()
    if any(getattr(a, axis+'max') <= getattr(b, axis+'min')+1.e-6 or
           getattr(b, axis+'max') <= getattr(a, axis+'min')+1.e-6 for axis in 'xyz'):
        return 0.
    return first.intersect(second).Volume()


def added_hardware_interferences(model, added_names):
    """Check new fasteners against all other fasteners and machined bodies.

    Components belonging to a single bolt/screw are intentionally grouped.
    These nominal occupied-volume checks do not evaluate tool access or fit
    tolerances, and they do not requalify unchanged assembly geometry.
    """
    shapes = {c.name: cq.Compound.makeCompound(c.components()) for c in model.connections()}
    parts = {p.name: p.shape for p in model.parts()}
    original_parts = {p.name for p in baseline.parts()}
    added_parts = sorted(set(parts)-original_parts)
    failures, checked = [], set()
    for name in added_names:
        for other, shape in shapes.items():
            pair = tuple(sorted((name, other)))
            if name == other or pair in checked:
                continue
            checked.add(pair)
            volume = interference(shapes[name], shape)
            if volume > 1.e-5:
                failures.append({'first': name, 'second': other, 'volume_mm3': volume})
        for other, shape in parts.items():
            volume = interference(shapes[name], shape)
            if volume > 1.e-5:
                failures.append({'first': name, 'second': other, 'volume_mm3': volume})
    checked_parts = set()
    for name in added_parts:
        for other, shape in parts.items():
            pair = tuple(sorted((name, other)))
            if name == other or pair in checked_parts:
                continue
            checked_parts.add(pair)
            volume = interference(parts[name], shape)
            if volume > 1.e-5:
                failures.append({'first': name, 'second': other, 'volume_mm3': volume})
        for other, shape in shapes.items():
            if other in added_names:
                continue  # Already checked from the fastener side.
            volume = interference(parts[name], shape)
            if volume > 1.e-5:
                failures.append({'first': name, 'second': other, 'volume_mm3': volume})
    return {'scope': 'Added fasteners and added bodies versus all other fasteners and machined bodies',
            'added_body_names': added_parts,
            'added_fastener_count': len(added_names), 'interferences': failures,
            'passed': not failures, 'tool_access_checked': False,
            'manufacturing_tolerances_checked': False}


def build(model):
    """Preserve the selected design and evaluate actual revised mass/supports."""
    before = sources()
    verify_loaded_sources(before)
    original = {c.name: c for c in baseline.connections()}
    revised = {c.name: c for c in model.connections()}
    if len(revised) != len(model.connections()) or model.KEY == baseline.KEY:
        raise ValueError('Require a distinct candidate with unique connection names')
    legs = [name for name in original if name.startswith('lumber_leg_bolt_')]
    if len(legs) != 8 or any(name not in revised or
            connection_record(original[name]) != connection_record(revised[name])
            for name in legs):
        raise ValueError('Eight original complete leg connections must remain unchanged')
    state, inventory = current_mass(model)
    # The historical helper classifies steel by clip_ names. Keep its previous
    # consumers unchanged, and classify newly modeled hold nuts explicitly.
    for row in inventory:
        if row['name'].startswith('hold_tnut_'):
            row.update(material='steel T-nut envelope', density_kg_m3=7850,
                       mass_kg=row['volume_mm3']/1.e9*7850)
    state = inventory_state(inventory)
    supports = select_floor_supports(floor_contact_bodies(model))
    state['support_polygon_mm'] = hull([p[:2] for r in supports for p in r['vertices_mm']])
    cases = envelope(state, locations(model), weights=(250, 300))
    added = sorted(set(revised)-set(original))
    removed = sorted(set(original)-set(revised))
    modified = sorted(name for name in set(original)&set(revised)
                      if connection_record(original[name]) != connection_record(revised[name]))
    collision = added_hardware_interferences(model, added)
    if before != sources():
        raise ValueError('Source changed during reinforcement review')
    verify_loaded_sources(before)
    return {'candidate': model.KEY, 'baseline': baseline.KEY, 'source_sha256': before,
            'qualified_for_design': False, 'floor_qualification': False,
            'electrical_mass_included': False,
            'internal_connection_demands_evaluated': False,
            'unchanged_leg_bolt_count': len(legs),
            'connection_counts': dict(Counter(c.kind for c in revised.values())),
            'added_connections': [connection_record(revised[n]) for n in added],
            'removed_connections': [connection_record(original[n]) for n in removed],
            'modified_connections': modified,
            'added_hardware_interference_check': collision,
            'state': state, 'mass_inventory': inventory,
            'selected_floor_support_bodies': supports,
            'cases': cases, 'summary': dict(Counter(c['status'] for c in cases)),
            'limits': [
                'Proposed development geometry; previous candidate remains selected.',
                'Actual revised drilled bodies and unioned fastener mass at assumed densities.',
                'Steel clips, bearing plates, T-nut envelopes and fasteners use assumed density 7850 kg/m3; wood 600 kg/m3.',
                'Holds and electrical mass excluded. No ballast or kicker-floor support credit.',
                'Inherited 48 rigid-body sensitivity groups; no internal forces or strength qualification.',
                'No physical floor tests; assumed level rigid support at four posts and two leg feet.',
                'Rendering is a review illustration, not a machining or installation drawing.',
            ]}


def export_viewer(model, destination, report):
    destination = Path(destination)
    meshes = destination/'models'
    meshes.mkdir(parents=True, exist_ok=False)
    records = [(p.name, p.shape, 'tnut' if p.name.startswith('hold_tnut_') else 'part',
                p.description, {}) for p in model.parts()]
    for c in model.connections():
        components = c.components()
        if c.kind == 'bolt':
            if len(components) != len(BOLT_ROLES):
                raise ValueError('Require complete independently selectable bolt stacks')
            records.extend(('fastener_'+c.name+'_'+role, shape, 'bolt', c.product_status,
                            {'connection_name': c.name, 'hardware_role': role})
                           for role, shape in zip(BOLT_ROLES, components, strict=True))
        else:
            records.append(('fastener_'+c.name, cq.Compound.makeCompound(components),
                            c.kind, c.product_status, {}))
    records.extend((p.name, p.shape, p.kind, 'Provisional electrical envelope; mass excluded',
                    {'mass_included': False}) for p in model.electrical_parts())
    items = []
    for name, shape, kind, description, metadata in records:
        path = meshes/(name+'.stl')
        cq.exporters.export(shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(shape)
        dimensions = [bounds.xlen, bounds.ylen, bounds.zlen]
        items.append({'name': name, 'path': f'hybrid/{model.KEY}/models/{path.name}',
                      'viewer_aabb_mm': dimensions,
                      'fabrication': {'dimensions_mm': dimensions, 'kind': kind,
                                      'description': description,
                                      'clearance_status': 'Provisional revision; NOT build-ready',
                                      **metadata}})
    if len(items) != len({p['name'] for p in items}):
        raise ValueError('Duplicate viewer part name')
    bounds = exact_bounds(cq.Compound.makeCompound([r[1] for r in records]))
    design = {'key': model.KEY, 'status': 'Reinforcement study with T-nuts — NOT build-ready',
              'description': ('Proposed fabricated steel base shoes and ten added kicker header screws. '
                              '142 owned-type T-nut envelopes; hold bolts omitted because installed hold '
                              'recess geometry is unavailable. Fit checks and conditional force witnesses '
                              'do not qualify the structure. Previous selected candidate remains preserved.'),
              'qualified_for_design': False, 'panel_kicker_screw_count': len(model.panel_connections()),
              'hold_tnut_count': sum(p['fabrication']['kind'] == 'tnut' for p in items),
              'panel_kicker_insert_count': 0, 'hold_bolt_count': 0,
              'electrical_mass_included': False}
    design['tnut_row_stations_mm'] = [model.timber.grid.main_tnut_datums()[f'A{i}'][1]
                                      for i in range(1, 13)]
    (destination/'parts.json').write_text(json.dumps({'design': design, 'parts': items,
        'bounds_mm': [[getattr(bounds, axis+end) for axis in 'xyz'] for end in ('min', 'max')]}, indent=2)+'\n')
    if report['source_sha256'] != sources():
        raise ValueError('Source changed during viewer export')
    (destination/'manifest.json').write_text(json.dumps({'design': design,
        'source_sha256': report['source_sha256'],
        'artifact_sha256': {str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(destination.rglob('*')) if p.is_file()}}, indent=2)+'\n')


def export(model, output, viewer=None):
    output = Path(output)
    if output.exists():
        raise FileExistsError('Refusing to overwrite reinforcement review evidence')
    if viewer is not None and Path(viewer).exists():
        raise FileExistsError('Refusing to overwrite reinforcement viewer')
    report = build(model)
    output.mkdir(parents=True, exist_ok=False)
    solids = [(p.shape, (130, 145, 155) if p.name.startswith(('clip_', 'hold_tnut_')) else (157, 90, 36))
              for p in model.parts() if not p.name.startswith(('main_', 'kicker_'))]
    for connection in model.connections():
        solids.extend((shape, (154, 165, 177) if connection.kind == 'bolt' else (41, 182, 214))
                      for shape in connection.components())
    render(solids, output/'open-frame.png')
    # Render the lower assembly only; the clipped wood remains intact in CAD.
    crop = cq.Solid.makeBox(3000., 3000., 430., cq.Vector(-1500., -500., -5.))
    detail = []
    for shape, color in solids:
        clipped = shape.intersect(crop)
        if clipped.Volume() > 1.e-5:
            detail.append((clipped, color))
    render(detail, output/'lower-frame.png')
    if report['source_sha256'] != sources():
        raise ValueError('Source changed during reinforcement rendering')
    report['artifact_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(output.glob('*.png'))}
    (output/'review.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    if viewer is not None:
        export_viewer(model, viewer, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--viewer', type=Path)
    args = parser.parse_args()
    if not args.module.startswith('mini_moonboard.'):
        parser.error('Require an explicit local candidate module')
    result = export(importlib.import_module(args.module), args.output, args.viewer)
    print(json.dumps({'candidate': result['candidate'], 'summary': result['summary']}))
