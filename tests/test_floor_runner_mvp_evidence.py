"""Guard the six-case aggregate against omitted producer-validity gates."""
import json
import shutil

import pytest

from scripts.floor_runner_mvp_evidence import ARCHIVE, ROOT, build, digest, read_case


def test_saved_aggregate_rebuilds():
    saved = json.loads((ROOT/'docs/floor-runner-mvp-evidence.json').read_text())
    assert build() == saved


def test_missing_producer_validity_cannot_pass(tmp_path):
    archive = tmp_path/ARCHIVE/'a12-left'
    shutil.copytree(ROOT/ARCHIVE/'a12-left', archive)
    checks_path = archive/'checks.json'
    checks = json.loads(checks_path.read_text())
    checks['producer_validity'] = {}
    checks_path.write_text(json.dumps(checks))
    manifest_path = archive/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files']['checks.json'] = digest(checks_path)
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='Frozen case checks do not pass'):
        read_case(tmp_path, 'a12-left')
