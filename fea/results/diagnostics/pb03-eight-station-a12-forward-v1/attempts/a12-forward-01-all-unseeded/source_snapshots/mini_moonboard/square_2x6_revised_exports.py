"""Export revised all-2x6 layout, retaining failed shallow-header bearing."""
import argparse
import hashlib
import json
from pathlib import Path

import cadquery as cq

from . import square_2x6_revised_frame as model
from .box_exports import write_csv
from .export import _export_step
from .raster import render


def export(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    sources = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(Path('mini_moonboard').glob('*.py'))}
    audit_path = Path('fea/results/square-2x6-revised-audit-v1.json')
    audit = json.loads(audit_path.read_text())
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != sha
           for p, sha in audit['source_sha256'].items()):
        raise ValueError('Recompute the geometry audit before export')
    sources.update(audit['source_sha256'])
    sources[str(audit_path)] = hashlib.sha256(audit_path.read_bytes()).hexdigest()
    (directory/'geometry-audit.json').write_bytes(audit_path.read_bytes())
    reserves = audit['future_insert_reserves']['schedule']
    write_csv(directory, 'future-insert-reserves.csv', tuple(reserves[0]),
              [tuple(row.values()) for row in reserves])
    parts, connections = model.parts(), model.connections()
    if any(not p.shape.isValid() or len(p.shape.Solids()) != 1 for p in parts):
        raise ValueError('Invalid body in candidate export')
    assembly = cq.Assembly(name=model.KEY.replace('-', '_'))
    for p in parts:
        assembly.add(p.shape, name=p.name)
    for c in connections:
        assembly.add(cq.Compound.makeCompound(c.components()), name='fastener_'+c.name)
    _export_step(assembly, directory/'square-2x6.step')
    write_csv(directory, 'wood-parts.csv', ('member', 'blank_length_mm', 'blank_width_mm',
              'blank_thickness_mm', 'description'),
              [(p.name, *p.blank, p.description) for p in model.wood_parts()])
    write_csv(directory, 'connections.csv', ('connection', 'kind', 'members', 'length_mm',
              'diameter_mm', 'x_mm', 'y_mm', 'z_mm', 'dx', 'dy', 'dz', 'status'),
              [(c.name, c.kind, ' + '.join(c.members), c.length, c.diameter,
                *c.start.toTuple(), *c.direction.toTuple(), c.product_status) for c in connections])
    # Remove only face panels from this inspection view to reveal framing.
    render([(p.shape, (120, 135, 145) if p.name.startswith('clip_') else (157, 90, 36))
            for p in parts if not p.name.startswith(('main_', 'kicker_'))],
           directory/'open-frame.png')
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != sha for p, sha in sources.items()):
        raise ValueError('Sources changed during export')
    manifest = {'candidate': model.KEY, 'status': model.LIMITS,
                'known_geometry_failures': 'See fea/results/square-2x6-revised-audit-v1.json; shallow-header bearing failure intentionally retained.',
                'qualified_for_design': False, 'source_sha256': sources,
                'artifact_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in directory.iterdir() if p.is_file()}}
    (directory/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return directory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(export(args.output))
