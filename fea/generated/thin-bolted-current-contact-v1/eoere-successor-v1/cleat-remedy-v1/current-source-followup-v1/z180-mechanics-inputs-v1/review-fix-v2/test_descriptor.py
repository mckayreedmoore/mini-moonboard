"""Narrow source-path correction controls; no real descriptor generation."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("z180_absolute_source_fix", OWN.with_name("descriptor.py"))
fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix)


def test_exact_owned_absolute_provenance_bytes_preserved_and_tamper_rejected(tmp_path):
    frozen = fix.frozen_module()
    path = tmp_path / "external-owned-source.json"
    path.write_text("{}")
    pins = {str(path): frozen.sha(path)}
    original = dict(pins)
    fix.verify_pins(frozen, pins, tmp_path, inherited_absolute=original)
    assert pins == original
    path.write_text("changed")
    with pytest.raises(ValueError, match="inherited absolute source bytes differ"):
        fix.verify_pins(frozen, pins, tmp_path, inherited_absolute=original)


def test_absolute_pin_with_wrong_hash_or_unlisted_path_rejected(tmp_path):
    frozen = fix.frozen_module()
    path = tmp_path / "unlisted.json"
    path.write_text("{}")
    pins = {str(path): frozen.sha(path)}
    for allowed in ({}, {str(path): "foreign"}):
        with pytest.raises(ValueError, match="inherited absolute source bytes differ"):
            fix.verify_pins(frozen, pins, tmp_path, inherited_absolute=allowed)


def test_relative_source_still_requires_same_exact_bytes(tmp_path):
    frozen = fix.frozen_module()
    path = tmp_path / "source.json"
    path.write_text("{}")
    pins = {"source.json": frozen.sha(path)}
    fix.verify_pins(frozen, pins, tmp_path)
    path.write_text("changed")
    with pytest.raises(ValueError, match="source bytes differ"):
        fix.verify_pins(frozen, pins, tmp_path)


def test_scoped_verifier_restored_after_success_and_failure():
    frozen = fix.frozen_module()
    original = frozen.verify
    with fix.source_context(frozen):
        assert frozen.verify is not original
    assert frozen.verify is original
    with pytest.raises(RuntimeError), fix.source_context(frozen):
        raise RuntimeError("owned failure")
    assert frozen.verify is original


def test_compiler_source_bytes_authenticated_immediately(tmp_path):
    changed = tmp_path / "descriptor.py"
    changed.write_text("raise AssertionError('untrusted source executed')")
    with patch.object(fix, "FROZEN", changed), pytest.raises(ValueError, match="source bytes differ"):
        fix.frozen_module()


def test_actual_wrapper_retains_original_fresh_output_guard(tmp_path):
    frozen = fix.frozen_module()
    frozen.OWN = tmp_path / "packet/descriptor.py"
    out = frozen.OWN.parent / "runs-v1/existing.json"
    out.parent.mkdir(parents=True)
    out.write_text("preserved")
    with patch.object(fix, "frozen_module", return_value=frozen), \
            patch.object(frozen, "load_inputs", side_effect=AssertionError("source intake reached")), pytest.raises(FileExistsError):
        fix.write_descriptor(tmp_path / "inputs.json", "wrong", out)
    assert out.read_text() == "preserved"
