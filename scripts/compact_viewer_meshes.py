"""Share byte-identical viewer STLs without changing frozen manifests.

Use --compact after an export, --check to verify the compact tree, or
--run -- COMMAND to temporarily restore legacy paths for unchanged replay tools.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1] / 'site'
MAP_NAME = 'mesh-aliases.json'
SCHEMA = 'viewer_mesh_aliases/v1'
PROTECTED_MODELS = ('compact-floor-flush-development', 'compact-floor-flush-kerf-right')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def mesh_path(root, relative):
    """Validate local mesh names before reading, writing, or removing them."""
    if not isinstance(relative, str):
        raise TypeError(f'Invalid mesh path: {relative}')
    parts = PurePosixPath(relative)
    if ('\\' in relative or parts.is_absolute()
            or '..' in parts.parts or parts.suffix != '.stl' or str(parts) != relative):
        raise ValueError(f'Invalid mesh path: {relative}')
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Mesh path outside site: {relative}')
    return path


def read_map(root):
    path = root / MAP_NAME
    data = json.loads(path.read_text()) if path.exists() else {
        'schema': SCHEMA, 'assets': {}, 'aliases': {}}
    if data.get('schema') != SCHEMA:
        raise ValueError('Unsupported mesh alias schema')
    for relative, record in data['assets'].items():
        mesh_path(root, relative)
        if (not isinstance(record['sha256'], str) or len(record['sha256']) != 64
                or any(c not in '0123456789abcdef' for c in record['sha256'])
                or not isinstance(record['bytes'], int) or record['bytes'] < 0):
            raise ValueError(f'Invalid retained mesh record: {relative}')
    for relative, canonical in data['aliases'].items():
        mesh_path(root, relative)
        if relative in data['assets'] or canonical not in data['assets']:
            raise ValueError(f'Invalid mesh alias: {relative}')
    return data


def resolve(root, relative, data=None):
    data = read_map(root) if data is None else data
    return mesh_path(root, data['aliases'].get(relative, relative))


def verify_assets(root, data):
    for relative, record in data['assets'].items():
        path = mesh_path(root, relative)
        if (not path.is_file() or path.stat().st_size != record['bytes']
                or digest(path) != record['sha256']):
            raise ValueError(f'Retained mesh missing or changed: {relative}')


def protected(relative):
    return any(relative.startswith(f'hybrid/{model}/') for model in PROTECTED_MODELS)


def compact(root=ROOT, backup=None, *, materialized=False):
    """Retain one original file per hash, plus both selected width packets."""
    root = Path(root)
    previous = read_map(root)
    if materialized:
        # Old aliases hold independent original bytes while exporters replace a canonical.
        if any(not mesh_path(root, name).is_file() for name in previous['aliases']):
            raise ValueError('Full materialization required before changing retained assets')
        selected = {name: row for name, row in previous['assets'].items() if protected(name)}
        verify_assets(root, {'assets': selected})
    else:
        verify_assets(root, previous)
    groups = defaultdict(list)
    sizes = {}
    for path in sorted(root.rglob('*.stl')):
        relative = path.relative_to(root).as_posix()
        mesh_path(root, relative)
        sha = digest(path)
        groups[sha].append(relative)
        sizes[relative] = path.stat().st_size
    aliases = dict(previous['aliases'])
    assets, removed = {}, {}
    for sha, paths in sorted(groups.items()):
        selected = [p for p in paths if protected(p)]
        existing = [p for p in paths if p in previous['assets']]
        canonical = (selected or existing or paths)[0]
        for relative in paths:
            aliases.pop(relative, None)  # A regenerated alias can contain new geometry.
            if (relative == canonical or protected(relative)
                    or (not materialized and relative in previous['assets'])):
                assets[relative] = {'sha256': sha, 'bytes': sizes[relative]}
            else:
                aliases[relative] = canonical
                removed[relative] = sha
    data = {'schema': SCHEMA, 'assets': dict(sorted(assets.items())),
            'aliases': dict(sorted(aliases.items()))}
    # Previous canonical paths stay retained, so missing legacy aliases remain valid.
    for relative, canonical in aliases.items():
        if canonical not in assets:
            raise ValueError(f'Previous alias lost its retained mesh: {relative}')
    if backup is not None:
        backup = Path(backup)
        backup.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(backup, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(MAP_NAME, json.dumps(data, indent=2) + '\n')
            archive.writestr('removed-paths.json', json.dumps(removed, indent=2) + '\n')
            copied = set()
            for relative, sha in removed.items():
                if sha not in copied:
                    archive.write(mesh_path(root, relative), f'assets/{sha}.stl')
                    copied.add(sha)
        with zipfile.ZipFile(backup) as archive:
            for sha in copied:
                if hashlib.sha256(archive.read(f'assets/{sha}.stl')).hexdigest() != sha:
                    raise ValueError(f'Backup mesh changed: {sha}')
    temporary = root / (MAP_NAME + '.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(root / MAP_NAME)
    for relative, sha in removed.items():
        source, retained = mesh_path(root, relative), resolve(root, relative, data)
        # Verify both byte identities immediately before removing the duplicate.
        if digest(source) != sha or digest(retained) != sha:
            raise ValueError(f'Mesh changed during compaction: {relative}')
        source.unlink()
    return {'retained_files': len(assets), 'alias_paths': len(aliases),
            'removed_files': len(removed), 'removed_bytes': sum(sizes[p] for p in removed)}


def check(root=ROOT):
    root = Path(root)
    data = read_map(root)
    if not (root / MAP_NAME).is_file():
        raise ValueError('Mesh alias map missing')
    verify_assets(root, data)
    present = {path.relative_to(root).as_posix() for path in root.rglob('*.stl')}
    if present != set(data['assets']):
        raise ValueError('Unindexed or restored mesh files; run --compact')
    for manifest in root.rglob('parts.json'):
        for part in json.loads(manifest.read_text())['parts']:
            relative = part['path']
            if not resolve(root, relative, data).is_file():
                raise ValueError(f'Viewer mesh unavailable: {manifest}: {relative}')
    return {'retained_files': len(data['assets']), 'alias_paths': len(data['aliases'])}


def run(command, root=ROOT):
    """Replay unchanged tools against independent copies, then share exports again."""
    root = Path(root)
    data = read_map(root)
    verify_assets(root, data)
    created = []
    try:
        for relative in data['aliases']:
            path = mesh_path(root, relative)
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(resolve(root, relative, data), path)
                created.append(relative)
        result = subprocess.run(command, check=False)
    except BaseException:
        cleanup_restored(root, data, created)
        raise
    if result.returncode == 0:
        # Rebuild sharing while original alias copies still preserve the old geometry.
        compact(root, materialized=True)
    else:
        cleanup_restored(root, data, created)
    return result.returncode


def cleanup_restored(root, data, created):
    # If a failed exporter changed retained geometry, keep originals for recovery.
    verify_assets(root, data)
    for relative in created:
        path = mesh_path(root, relative)
        expected = data['assets'][data['aliases'][relative]]['sha256']
        if path.is_file() and digest(path) == expected:
            path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--compact', action='store_true')
    actions.add_argument('--check', action='store_true')
    actions.add_argument('--run', action='store_true')
    parser.add_argument('--backup', type=Path, help='New external ZIP for removed mesh bytes and paths')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.run:
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        if not command:
            parser.error('--run requires -- COMMAND')
        raise SystemExit(run(command, args.root))
    if args.command or (args.backup and not args.compact):
        parser.error('--backup applies only to --compact; command applies only to --run')
    print(json.dumps(compact(args.root, args.backup) if args.compact else check(args.root)))


if __name__ == '__main__':
    main()
