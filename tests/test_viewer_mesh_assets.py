"""Mesh sharing preserves original bytes, identities, and isolated replay writes."""
import json
import sys
import zipfile
from pathlib import Path

import pytest

from scripts import compact_viewer_meshes as meshes


def test_compaction_backup_and_replay_preserve_model_metadata_and_mesh_bytes(tmp_path):
    root = tmp_path / 'site'
    names = [f'hybrid/{key}/models/bolt.stl' for key in (
        'compact-floor-flush-development', 'compact-floor-flush-kerf-right', 'old-a', 'old-b')]
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True)
        path.write_bytes(b'original mesh bytes')
        (path.parent.parent / 'parts.json').write_text(json.dumps({
            'parts': [{'name': 'bolt', 'path': name, 'fabrication': {'kind': 'bolt'}}]}))
    before = {p: p.read_bytes() for p in root.rglob('parts.json')}
    backup = tmp_path / 'removed.zip'
    result = meshes.compact(root, backup)
    assert result['removed_files'] == 2
    assert all((root / name).is_file() for name in names[:2])
    assert all(not (root / name).exists() for name in names[2:])
    assert {p: p.read_bytes() for p in root.rglob('parts.json')} == before
    data = meshes.read_map(root)
    assert all(meshes.resolve(root, name, data).read_bytes() == b'original mesh bytes' for name in names)
    assert meshes.check(root)['alias_paths'] == 2
    with zipfile.ZipFile(backup) as archive:
        removed = json.loads(archive.read('removed-paths.json'))
        assert set(removed) == set(names[2:])
        for sha in removed.values():
            assert archive.read(f'assets/{sha}.stl') == b'original mesh bytes'
    assert meshes.compact(root)['removed_files'] == 0
    # Writing a materialized old mesh must not change either selected packet.
    command = [sys.executable, '-c',
               ("from pathlib import Path; p=Path(__import__('sys').argv[1]); "
                "assert p.read_bytes()==b'original mesh bytes'; p.write_bytes(b'new geometry')"),
               str(root / names[2])]
    assert meshes.run(command, root) == 0
    assert all((root / name).read_bytes() == b'original mesh bytes' for name in names[:2])
    assert meshes.resolve(root, names[2]).read_bytes() == b'new geometry'
    assert meshes.resolve(root, names[3]).read_bytes() == b'original mesh bytes'
    assert meshes.check(root)['alias_paths'] == 1


def test_replay_failure_cleanup_and_changed_retained_asset_are_explicit(tmp_path):
    root = tmp_path / 'site'
    root.mkdir()
    (root / 'a.stl').write_bytes(b'original')
    (root / 'b.stl').write_bytes(b'original')
    meshes.compact(root)
    assert meshes.run([sys.executable, '-c', 'raise SystemExit(3)'], root) == 3
    assert not (root / 'b.stl').exists()
    command = [sys.executable, '-c',
               "from pathlib import Path; Path(__import__('sys').argv[1]).write_bytes(b'changed')",
               str(root / 'a.stl')]
    assert meshes.run(command, root) == 0
    assert (root / 'a.stl').read_bytes() == b'changed'
    assert meshes.resolve(root, 'b.stl').read_bytes() == b'original'
    meshes.check(root)
    (root / 'a.stl').write_bytes(b'unreviewed mutation')
    with pytest.raises(ValueError, match='Retained mesh missing or changed'):
        meshes.compact(root)
    with pytest.raises(ValueError, match='Retained mesh missing or changed'):
        meshes.check(root)


def test_alias_map_rejects_escaping_paths_and_chains(tmp_path):
    for relative in ('../escape.stl', '/absolute.stl', 'a/../escape.stl'):
        with pytest.raises(ValueError, match='Invalid mesh path'):
            meshes.mesh_path(tmp_path, relative)
    (tmp_path / meshes.MAP_NAME).write_text(json.dumps({
        'schema': meshes.SCHEMA, 'assets': {}, 'aliases': {'a.stl': 'b.stl'}}))
    with pytest.raises(ValueError, match='Invalid mesh alias'):
        meshes.read_map(tmp_path)


def test_shared_map_covers_every_published_model_and_selected_meshes_stay_local():
    root = Path('site')
    data = meshes.read_map(root)
    for manifest in root.rglob('parts.json'):
        for part in json.loads(manifest.read_text())['parts']:
            assert meshes.resolve(root, part['path'], data).is_file(), (manifest, part['path'])
            if manifest.parent.name in meshes.PROTECTED_MODELS:
                assert part['path'] not in data['aliases']
                assert (root / part['path']).is_file()
