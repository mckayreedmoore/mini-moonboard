"""Export the infilled panel-attachment candidate and its own unqualified audit evidence."""
import argparse
import json
from pathlib import Path

import cadquery as cq

from . import infill_panel_frame as model
from .box_exports import exact_bounds, write_csv
from .box_frame import Part
from .export import _export_step
from .panel_grid_v2 import main_tnut_datums
from .raster import render
from .selective_2x6_viewer import DEPENDENCIES, digest
from .split_center_hardware import BOLT_ROLES

AUDIT = Path('fea/results/infill-panel-audit-v1.json')


def export(directory=None, output_root=Path('site/hybrid')):
    directory = Path(directory) if directory is not None else Path('exports')/model.KEY
    viewer = Path(output_root)/model.KEY
    for destination in (directory, viewer):
        if destination.exists():
            raise FileExistsError(f'Refusing to overwrite {destination}')
    audit = json.loads(AUDIT.read_text())
    if audit['candidate'] != model.KEY or not audit['source_sha256'] or any(
            digest(path) != sha for path, sha in audit['source_sha256'].items()):
        raise ValueError('Recompute the candidate geometry audit before export')
    dependencies = (*DEPENDENCIES, 'selective_2x6_frame', 'paired_rail_frame', 'vertical_principal_frame', 'split_center_frame', 'split_center_hardware', 'infill_panel_frame', 'infill_panel_exports')
    sources = {f'mini_moonboard/{name}.py': digest(f'mini_moonboard/{name}.py')
               for name in dependencies}
    sources.update(audit['source_sha256'])
    for path in (AUDIT, Path('docs/selective-stock-reference.json'),
                 Path('docs/ml24z-reference.json'), Path('docs/panel-insert-reference.json')):
        sources[str(path)] = digest(path)
    directory.mkdir(parents=True, exist_ok=False)
    meshes = viewer/'models'
    meshes.mkdir(parents=True, exist_ok=False)
    (directory/'geometry-audit.json').write_bytes(AUDIT.read_bytes())
    parts, connections = list(model.parts()), tuple(model.connections())
    if any(not part.shape.isValid() or len(part.shape.Solids()) != 1 for part in parts):
        raise ValueError('Invalid candidate body')
    kinds, roles = {}, {}
    for connection in connections:
        prefix = 'fastener_'+connection.name
        components = connection.components()
        if connection.kind == 'bolt':
            if len(components) != len(BOLT_ROLES):
                raise ValueError('Unexpected bolt component contract')
            for role, shape in zip(BOLT_ROLES, components, strict=True):
                name = prefix+'_'+role
                kinds[name], roles[name] = 'bolt', (connection.name, role)
                bounds = exact_bounds(shape)
                parts.append(Part(name, shape, (bounds.xlen, bounds.ylen, bounds.zlen),
                                  role.replace('_', ' ')+' of '+connection.name+'; '+connection.product_status, 1))
        else:
            kinds[prefix] = connection.kind
            parts.append(Part(prefix, cq.Compound.makeCompound(components),
                              (connection.length, connection.diameter, connection.diameter),
                              connection.product_status+'; '+' + '.join(connection.members), 1))
    if len({part.name for part in parts}) != len(parts):
        raise ValueError('Duplicate candidate part names')
    panel_screw_count = sum(isinstance(c, model.timber.PanelScrew) for c in connections)
    infill_count = sum(c.name.startswith('infill_') for c in connections)
    design = {
        'key': model.KEY,
        'status': 'Infilled panel screws on six 2x6 principals — NOT build-ready',
        'description': f'{panel_screw_count} ordinary panel/kicker screws, including {infill_count} new infill screws. '
                       f'Intervals are at most {model.MAX_INTERVAL_MM:g} mm between existing first and last '
                       'screws on each panel along all six interior principals; panel end distances remain unchanged. '
                       'Six independent interior 2x6 principals retain aligned single 2x10 posts; '
                       'two separated center principals leave a 101.9 mm service corridor and '
                       '50.95 mm unsupported plywood edges at the vertical joint. The horizontal '
                       'seam remains unsupported between principals. Ordinary panel screws remain. '
                       'Through-bolt heads, nuts and both washers are separate selectable geometry. '
                       'No previous strength or floor qualification transfers to this layout.',
        'qualified_for_design': False,
        'panel_kicker_screw_count': panel_screw_count,
        'infill_screw_count': infill_count,
        'maximum_infill_interval_mm': model.MAX_INTERVAL_MM,
        'tnut_row_stations_mm': [main_tnut_datums()[f'A{row}'][1] for row in range(1, 13)],
    }
    assembly, items, raster = cq.Assembly(name=model.KEY.replace('-', '_')), [], []
    for part in parts:
        assembly.add(part.shape, name=part.name)
        path = meshes/(part.name+'.stl')
        cq.exporters.export(part.shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(part.shape)
        kind = kinds.get(part.name, 'part')
        items.append({'name': part.name, 'path': f'hybrid/{model.KEY}/models/{path.name}',
                      'viewer_aabb_mm': [bounds.xlen, bounds.ylen, bounds.zlen],
                      'fabrication': {'dimensions_mm': list(part.blank), 'description': part.description,
                                      'kind': kind, 'clearance_status':
                                      'Geometry revision; NOT build-ready; resistance and floor stability unqualified'}})
        if part.name in roles:
            connection_name, role = roles[part.name]
            items[-1]['fabrication'].update(connection_name=connection_name, hardware_role=role)
        color = ((210, 65, 65) if kind == 'bolt' else (41, 182, 214) if kind == 'screw' else
                 (120, 135, 145) if part.name.startswith('clip_') else (157, 90, 36))
        if not part.name.startswith(('main_', 'kicker_')):
            raster.append((part.shape, color))
    bounds = exact_bounds(cq.Compound.makeCompound([part.shape for part in parts]))
    (viewer/'parts.json').write_text(json.dumps({'design': design, 'parts': items,
        'bounds_mm': [[getattr(bounds, axis+end) for axis in 'xyz'] for end in ('min', 'max')]}, indent=2)+'\n')
    _export_step(assembly, directory/(model.KEY+'.step'))
    render(raster, directory/'open-frame.png')
    # Visualization-only added-principal crop exposes the small base brackets. STEP and
    # STL exports above retain the full, unmodified principal geometry.
    detail_names = {'base_principal_center_left', 'base_principal_center_right', 'base_header',
                    'base_post_center_left', 'base_post_center_right',
                    'clip_split_base_center_left', 'clip_split_header_center_left',
                    'clip_split_base_center_right', 'clip_split_header_center_right'}
    detail_fasteners = {'fastener_'+c.name for c in connections
                        if any(member in ('clip_split_base_center_left', 'clip_split_header_center_left',
                                           'clip_split_base_center_right', 'clip_split_header_center_right')
                               for member in c.members)}
    detail_cut = cq.Solid.makeBox(320., 10000., 1400., cq.Vector(-160., -5000., -1000.))
    detail = []
    for part in parts:
        if part.name not in detail_names | detail_fasteners:
            continue
        shape = part.shape.intersect(detail_cut)
        color = ((41, 182, 214) if part.name in detail_fasteners else
                 (120, 135, 145) if part.name.startswith('clip_') else (157, 90, 36))
        # Default view shows the left face carrying the new principal bracket.
        detail.append((shape, color))
    render(detail, directory/'base-connection.png')
    # A local wood cutaway exposes the original, unshifted bolt stack. The
    # removed visualization material is retained in every STEP/STL export.
    bolt = next(c for c in connections if c.name == 'lumber_leg_bolt_right_1')
    center = bolt.start
    cutaway = cq.Solid.makeBox(bolt.length+20., 70., 29.,
                               cq.Vector(center.x-10., center.y-35., center.z-35.))
    bolt_detail = [(shape, (210, 65, 65)) for shape in bolt.components()]
    members = {part.name: part for part in parts}
    for name in bolt.members:
        shape = members[name].shape.intersect(cutaway)
        if shape.Volume() <= 0.:
            raise ValueError('Bolt detail cutaway missed '+name)
        bolt_detail.append((shape, (157, 90, 36)))
    render(bolt_detail, directory/'bolt-ends-cutaway.png')
    (directory/'visualization.json').write_text(json.dumps({
        'base-connection.png': 'Visualization-only crop x +/-160 mm and z <=400 mm; full CAD retained.',
        'bolt-ends-cutaway.png': 'Visualization-only local wood cutaway below the bolt axis; '
                                 'head, shaft, both washers and nut retain actual assembled coordinates. '
                                 'No machining instruction and no structural qualification.',
    }, indent=2)+'\n')
    write_csv(directory, 'wood-parts.csv', ('member', 'blank_length_mm', 'blank_width_mm',
              'blank_thickness_mm', 'description'),
              [(part.name, *part.blank, part.description) for part in model.wood_parts()])
    write_csv(directory, 'parts.csv', ('part', 'kind', 'dimension_1_mm', 'dimension_2_mm',
              'dimension_3_mm', 'description'),
              [(part.name, kinds.get(part.name, 'part'), *part.blank, part.description) for part in parts])
    write_csv(directory, 'connections.csv', ('connection', 'kind', 'members', 'length_mm',
              'diameter_mm', 'x_mm', 'y_mm', 'z_mm', 'dx', 'dy', 'dz', 'status'),
              [(c.name, c.kind, ' + '.join(c.members), c.length, c.diameter,
                *c.start.toTuple(), *c.direction.toTuple(), c.product_status) for c in connections])
    reserves = audit.get('future_insert_reserves', {}).get('schedule', [])
    if reserves:
        columns = tuple(reserves[0])
        write_csv(directory, 'future-insert-reserves.csv', columns,
                  [tuple(row[column] for column in columns) for row in reserves])
    if any(digest(path) != sha for path, sha in sources.items()):
        raise ValueError('Sources changed during export')
    viewer_artifacts = {str(path.relative_to(viewer)): digest(path)
                        for path in sorted(viewer.rglob('*')) if path.is_file()}
    (viewer/'manifest.json').write_text(json.dumps({
        'design': design, 'source_sha256': sources, 'artifact_sha256': viewer_artifacts}, indent=2)+'\n')
    (directory/'manifest.json').write_text(json.dumps({
        'candidate': model.KEY, 'design': design, 'qualified_for_design': False,
        'source_sha256': sources,
        'artifact_sha256': {path.name: digest(path) for path in sorted(directory.iterdir()) if path.is_file()},
        'viewer_artifact_sha256': viewer_artifacts,
    }, indent=2)+'\n')
    return directory, viewer


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--output-root', type=Path, default=Path('site/hybrid'))
    args = parser.parse_args()
    print(*export(args.output, args.output_root), sep='\n')
