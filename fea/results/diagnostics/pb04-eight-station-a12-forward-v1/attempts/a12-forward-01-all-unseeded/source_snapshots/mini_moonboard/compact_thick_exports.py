"""Export the preferred compact 4x6 three-bolt development candidate."""
import argparse
import ast
from pathlib import Path

from . import compact_thick_frame as model
from . import no_shoes_exports as shared


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
    return {**shared.design_metadata(parts, connections), 'key': model.KEY,
            'status': '4×6 legs / rims · three bolts per leg · preferred development · NOT build-ready',
            'description': model.LIMITS, 'leg_stock': '4x6', 'outer_rim_stock': '4x6',
            'joint_note': 'Three-bolt joints retain moment transfer; no free-rotation hinge is claimed.'}


def export(root=Path('site')):
    return shared.export(root, candidate=model, metadata=metadata, source_reader=sources)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('site'))
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(shared.check(args.root, candidate=model, exporter=export) if args.check else export(args.root))
