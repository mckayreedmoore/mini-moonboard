"""A historical lint waiver must never silently apply to changed source bytes."""

import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_lint_waivers_are_exact_paths_rules_and_source_bytes():
    record = json.loads((ROOT / 'tests/frozen-lint-sources.json').read_text())
    configuration = tomllib.loads((ROOT / 'ruff.toml').read_text())
    waivers = configuration['lint']['per-file-ignores']
    assert set(waivers) == set(record['sources'])
    for name, source in record['sources'].items():
        assert not any(character in name for character in '*?[]')
        assert sorted(waivers[name]) == source['rules']
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == source['sha256'], name
