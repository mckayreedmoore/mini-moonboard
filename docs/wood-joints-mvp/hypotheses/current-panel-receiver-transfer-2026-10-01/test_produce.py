from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "panel_transfer_producer_test", Path(__file__).with_name("produce.py")
)
assert SPEC is not None and SPEC.loader is not None
producer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(producer)


def test_shared_pin_is_retained_once_and_conflicting_digest_is_refused():
    record = {"path": "source.json", "sha256": "a" * 64, "size_bytes": 5}
    first = {"sources": [record]}
    assert producer.merge_pins(first, first) == first
    conflict = {"sources": [{**record, "sha256": "b" * 64}]}
    with pytest.raises(ValueError, match="conflicting source pins"):
        producer.merge_pins(first, conflict)


def test_source_size_conflict_is_refused_and_pin_uses_current_bytes(tmp_path):
    path = tmp_path / "source.txt"
    path.write_bytes(b"first")
    original = producer.pin(path, tmp_path)
    path.write_bytes(b"second")
    changed = producer.pin(path, tmp_path)
    assert original["path"] == changed["path"] == "source.txt"
    assert original["sha256"] != changed["sha256"]
    with pytest.raises(ValueError, match="conflicting source pins"):
        producer.merge_pins(
            {"sources": [original]}, {"sources": [{**original, "size_bytes": 7}]}
        )
