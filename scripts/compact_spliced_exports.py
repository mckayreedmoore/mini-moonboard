"""Export the compact 4x6 spliced-knee development candidate."""
import argparse
import ast
import json
from pathlib import Path

from mini_moonboard import compact_spliced_knee_frame as model
from mini_moonboard import no_shoes_exports as shared

STATUS = 'Conditional build package · 4×6 legs/rims · spliced 2×6 knees'
PACKAGE = 'docs/compact-spliced-build-package.md'
ASSUMPTIONS = ('Applies only to the stated load cases, specified hardware/material conditions '
               'and installation details in '+PACKAGE+'. No-slip support is assumed; '
               'accepted panel construction is retained. No unconditional qualification.')


def sources():
    """Include the shared source/data closure and every extra candidate import."""
    hashes = shared.sources()
    pending = [Path(__file__).resolve(), Path(model.__file__).resolve()]
    visited = set()
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        hashes[str(path.relative_to(shared.ROOT))] = shared.digest(path)
        for node in ast.walk(ast.parse(path.read_text())):
            dependencies = []
            if isinstance(node, ast.ImportFrom):
                parent = path.parent if node.level else shared.ROOT
                for _ in range(max(0, node.level-1)):
                    parent = parent.parent
                module = parent/(node.module or '').replace('.', '/')
                dependencies = [module, *(module/alias.name for alias in node.names)]
            elif isinstance(node, ast.Import):
                dependencies = [shared.ROOT/alias.name.replace('.', '/') for alias in node.names]
            for dependency in dependencies:
                for source in (dependency.with_suffix('.py'), dependency/'__init__.py'):
                    if source.is_file() and source.is_relative_to(shared.ROOT):
                        pending.append(source)
    return dict(sorted(hashes.items()))


def metadata(parts, connections):
    # The compact frame retains the baseline panel, kicker and electrical datums.
    upper = [c for c in connections if c.name.startswith('lumber_leg_bolt_')]
    bolts = [c for c in connections if c.kind == 'bolt']
    return {**shared.design_metadata(parts, connections), 'key': model.KEY,
            'status': STATUS,
            'description': STATUS+'. '+ASSUMPTIONS, 'build_package': PACKAGE,
            'assessment_scope': ASSUMPTIONS, 'leg_stock': '4x6', 'outer_rim_stock': '4x6',
            'leg_bolt_count': len(upper), 'bolts_per_leg': len(upper)//2,
            'total_bolt_count': len(bolts), 'knee_piece_count': len(model.KNEE_NAMES),
            'upper_bolt_pitch_mm': model.UPPER_BOLT_PITCH_MM,
            'joint_note': 'Two upper bolts per leg; each knee has two independent unnotched members, four splice bolts and two bolts at each host end. No composite action or free-rotation hinge is assumed.'}


def export(root=Path('site')):
    directory = shared.export(root, candidate=model, metadata=metadata, source_reader=sources)
    inventory_path = directory/'parts.json'
    inventory = json.loads(inventory_path.read_text())
    for item in inventory['parts']:
        fabrication = item['fabrication']
        kind = fabrication['kind']
        if not fabrication.get('clearance_status', '').startswith('FAIL'):
            fabrication['clearance_status'] = STATUS+'; '+ASSUMPTIONS
        # Replace inherited variant prose only in presentation. Native geometry,
        # source snapshots and numerical launch inputs remain unchanged.
        if kind == 'part':
            identity = ('Commercial ML24Z angle' if item['name'].startswith('clip_')
                        else 'Current member '+item['name'])
            fabrication['description'] = identity+'. '+STATUS+'. '+ASSUMPTIONS
        elif kind == 'bolt':
            role = fabrication.get('hardware_role', 'complete bolt stack').replace('_', ' ')
            fabrication['description'] = role+'; '+fabrication.get('connection_name', item['name'])+'. '+ASSUMPTIONS
            fabrication['hardware_reference'] = ('docs/compact-splice-hardware.md'
                if 'knee_' in item['name'] else 'docs/compact-half-inch-hardware.md')
        fabrication['build_package'] = PACKAGE
    inventory_path.write_text(json.dumps(inventory, indent=2, allow_nan=False)+'\n')
    manifest_path = directory/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['artifact_sha256']['parts.json'] = shared.digest(inventory_path)
    if sources() != manifest['source_sha256']:
        raise ValueError('Source changed during presentation export')
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    return directory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('site'))
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(shared.check(args.root, candidate=model, exporter=export) if args.check else export(args.root))
