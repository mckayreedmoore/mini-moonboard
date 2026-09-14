"""Standalone viewer exports for the two clear-space support alternatives."""
import argparse
import ast
import gzip
import importlib
import json
import math
from pathlib import Path

from fea.reinforced_frame_demand import repository_source_closure
from mini_moonboard import no_shoes_exports as shared
from scripts.clear_space_batch import CASES
from scripts.clear_space_results import checks
from scripts.clear_space_study import MODELS

PACKAGE = 'docs/clear-space-study.md'


def sources(model, kind):
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
    for case in CASES:
        directory = shared.ROOT/'fea/results'/('clear-space-'+kind)/case
        for path in directory.glob('*'):
            if path.is_file():
                hashes[str(path.relative_to(shared.ROOT))] = shared.digest(path)
    return dict(sorted(hashes.items()))



def native_source_requirements(active):
    """Separate native producer inputs from postprocessing/export dependencies."""
    native = repository_source_closure([shared.ROOT/'fea/current_response_run.py',
        shared.ROOT/'fea/current_response_model.py', shared.ROOT/'fea/current_response_materials.py'])
    required = {str(path.relative_to(shared.ROOT)):shared.digest(path) for path in native}
    required.update({name:sha for name, sha in active.items()
                     if name.startswith('mini_moonboard/') and name.endswith('.py')})
    return required


def validate_case(report, geometry, assessment, candidate, case, required):
    """Require the named load case and reproduce its present assessment."""
    if report['candidate'] != candidate or any(report['source_sha256'].get(name) != sha
                                               for name, sha in required.items()):
        raise ValueError('Case evidence does not match current candidate sources')
    hold, horizontal = CASES[case]
    parameters = report['parameters']
    force = parameters.get('force_xyz_n', ())
    expected = (*horizontal, -2.*250.*.45359237*9.80665)
    if (parameters.get('hold') != hold or parameters.get('pounds') != 250.
            or len(force) != 3 or not all(math.isclose(a, b, rel_tol=1.e-9, abs_tol=1.e-6)
                                         for a, b in zip(force, expected, strict=True))):
        raise ValueError('Case archive does not contain its named load case')
    fresh = json.loads(json.dumps(checks(report, geometry), allow_nan=False))
    if fresh != assessment:
        raise ValueError('Saved assessment differs from current checks')
    return fresh


def status(kind, model):
    cases = []
    required = native_source_requirements(sources(model, kind))
    for case in CASES:
        path = shared.ROOT/'fea/results'/('clear-space-'+kind)/case/'assessment.json'
        if path.exists():
            manifest = json.loads((path.parent/'manifest.json').read_text())
            for name, sha in manifest['files'].items():
                if shared.digest(path.parent/name) != sha:
                    raise ValueError('Case archive changed: '+name)
            report = json.loads(gzip.decompress((path.parent/'report.json.gz').read_bytes()))
            geometry = json.loads((path.parent/'geometry.json').read_text())
            cases.append(validate_case(report, geometry, json.loads(path.read_text()), model.KEY, case, required))
    passed = len(cases) == len(CASES) and all(r.get('criteria') and all(r['criteria'].values()) for r in cases)
    label = '2×6 floor rails · no raised knees' if kind == 'floor' else 'Exterior 4×6 / 2×6 braces · no inboard knee wood'
    decision = ('Conditional listed checks met' if passed else
        'NOT ACCEPTED · numerical response rejected' if any(
            row.get('status') == 'INVALID_RESPONSE_DIAGNOSTIC_ONLY' for row in cases) else
        'Development · listed checks incomplete or failed')
    return decision+' · '+label


def export(kind, root=Path('site')):
    model = importlib.import_module('mini_moonboard.'+MODELS[kind])
    label = status(kind, model)
    scope = ('Finite recorded load cases and material/hardware assumptions apply. '
        'No-slip floor and accepted panel basis retained. Unlisted commercial-angle separation '
        'and independent flange moments remain explicit limits. See '+PACKAGE+'.')
    def metadata(parts, connections):
        bolts = [c for c in connections if c.kind == 'bolt']
        return {**shared.design_metadata(parts, connections), 'key':model.KEY,
            'status':label, 'description':label+'. '+scope, 'build_package':PACKAGE,
            'assessment_scope':scope, 'leg_stock':'4x6', 'outer_rim_stock':'4x6',
            'leg_bolt_count':4, 'bolts_per_leg':2, 'total_bolt_count':len(bolts),
            'knee_piece_count':len(model.KNEE_NAMES), 'upper_bolt_pitch_mm':56.,
            'lower_kicker_screw_height_mm':60., 'base_clip_center_y_mm':model.CLIP_CENTER_Y_MM,
            'joint_note':label+'. Heads inside; nuts and tips outside. '+scope}
    source_reader = lambda: sources(model, kind)
    directory = shared.export(root, candidate=model, metadata=metadata, source_reader=source_reader)
    inventory_path = directory/'parts.json'
    inventory = json.loads(inventory_path.read_text())
    for part in inventory['parts']:
        fabrication = part['fabrication']
        if not fabrication.get('clearance_status', '').startswith('FAIL'):
            fabrication['clearance_status'] = label+'. '+scope
        fabrication['description'] = part['name']+'. '+label+'. '+scope
        fabrication['build_package'] = PACKAGE
        if fabrication['kind'] == 'bolt':
            fabrication['hardware_reference'] = 'docs/clear-space-hardware.md'
    inventory_path.write_text(json.dumps(inventory, indent=2, allow_nan=False)+'\n')
    manifest_path = directory/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['artifact_sha256']['parts.json'] = shared.digest(inventory_path)
    if source_reader() != manifest['source_sha256']:
        raise ValueError('Candidate sources changed during export')
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    return directory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', choices=MODELS)
    parser.add_argument('--root', type=Path, default=Path('site'))
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    model = importlib.import_module('mini_moonboard.'+MODELS[args.candidate])
    if args.check:
        print(shared.check(args.root, candidate=model, exporter=lambda root: export(args.candidate, root)))
    else:
        print(export(args.candidate, args.root))
