"""Export the single-member layout into its own interactive-viewer directory."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path

import cadquery as cq

from .box_exports import exact_bounds
from .box_frame import Part
from .panel_grid_v2 import main_tnut_datums

# Explicit shared dependencies keep unrelated future variants out of replay hashes.
DEPENDENCIES = (
    'base_frame', 'bearing_frame', 'bolted_frame', 'box_exports', 'box_frame',
    'bracket_mvp', 'clip_frame', 'continuous_frame', 'easy_frame', 'export',
    'footprint_frame', 'hybrid', 'hybrid_frame', 'independent_leg_frame',
    'insert_frame', 'joint_frame', 'lean_frame', 'lumber_leg_frame',
    'lumber_leg_spread_frame', 'model', 'panel_grid', 'panel_grid_v2',
    'product_connections', 'product_frame', 'raster', 'screw_mvp_frame',
    'selected_hardware', 'shallow_frame', 'spacing_frame', 'square_2x6_frame',
    'stability', 'timber_connections', 'timber_frame', 'top_joint_frame',
    'transition_frame', 'wide_frame', 'wood_mvp', 'square_2x6_revised_frame', 'square_2x6_base_revision', 'single_2x6_frame', 'selective_2x6_viewer',
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export(output_root=Path('site/hybrid')):
    module = 'selective_2x6_frame'
    model = importlib.import_module('.'+module, __package__)
    sources = {f'mini_moonboard/{name}.py' for name in (*DEPENDENCIES, module)}
    sources.update(('docs/selective-stock-reference.json', 'docs/ml24z-reference.json', 'docs/panel-insert-reference.json'))
    sources = {path: digest(path) for path in sorted(sources)}
    directory = Path(output_root)/model.KEY
    directory.mkdir(parents=True, exist_ok=False)
    meshes = directory/'models'
    meshes.mkdir()
    parts = list(model.parts())
    kinds = {}
    for connection in model.connections():
        name = 'fastener_'+connection.name
        kinds[name] = connection.kind
        parts.append(Part(name, cq.Compound.makeCompound(connection.components()),
                                 (connection.length, connection.diameter, connection.diameter),
                                 connection.product_status+'; '+' + '.join(connection.members), 1))
    if len({part.name for part in parts}) != len(parts):
        raise ValueError('Duplicate viewer part names')
    items = []
    for part in parts:
        if not part.shape.isValid():
            raise ValueError('Invalid viewer shape: '+part.name)
        path = meshes/(part.name+'.stl')
        cq.exporters.export(part.shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(part.shape)
        items.append({'name': part.name, 'path': f'hybrid/{model.KEY}/models/{path.name}',
                      'viewer_aabb_mm': [bounds.xlen, bounds.ylen, bounds.zlen],
                      'fabrication': {'dimensions_mm': list(part.blank),
                                      'description': part.description,
                                      'kind': kinds.get(part.name, 'part'),
                                      'clearance_status': 'Development geometry; NOT build-ready; resistance unqualified'}})
    bounds = exact_bounds(cq.Compound.makeCompound([part.shape for part in parts]))
    design = {
        'key': model.KEY,
        'status': 'Selective single-stock receivers and header — NOT build-ready',
        'description': 'Nine 2x6 members, four single 3x6 receivers and one 2x10 header; no paired framing. '
                       'Ordinary panel screws and through-bolts; no installed inserts. '
                       'Service pockets remain in center framing; bottom rails remain pocket-free. '
                       'Wider receivers and header target edge and bearing fit; strength and floor behavior unqualified.',
        'qualified_for_design': False,
        'tnut_row_stations_mm': [main_tnut_datums()[f'A{row}'][1] for row in range(1, 13)],
    }
    (directory/'parts.json').write_text(json.dumps({
        'design': design, 'parts': items,
        'bounds_mm': [[getattr(bounds, axis+end) for axis in 'xyz'] for end in ('min', 'max')],
    }, indent=2)+'\n')
    if any(digest(path) != sha for path, sha in sources.items()):
        raise ValueError('Sources changed during viewer export')
    manifest = {'design': design, 'source_sha256': sources,
                'artifact_sha256': {str(path.relative_to(directory)): digest(path)
                                    for path in sorted(directory.rglob('*')) if path.is_file()}}
    (directory/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return directory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', type=Path, default=Path('site/hybrid'))
    args = parser.parse_args()
    print(export(args.output_root))
