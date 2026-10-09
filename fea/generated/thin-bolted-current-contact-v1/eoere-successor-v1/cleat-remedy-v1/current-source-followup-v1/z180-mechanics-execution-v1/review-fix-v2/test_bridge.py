"""Inert exact-roster controls reusing the frozen source-only fixture."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("eoere_z180_roster_correction_inert_tests", OWN.with_name("bridge.py"))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
fixture_path = c.FROZEN.with_name("test_bridge.py")
assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == "d02c448019ac7bdc0b7b465337ce52a617d18c5e771c2e307d873bcc9e4b38be"
spec = importlib.util.spec_from_file_location("eoere_z180_retained_source_fixture_for_roster_fix", fixture_path)
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)


def mutated(kind):
    parent, exported, data, read = fixture_module.fixture()
    if kind == "duplicate_moved":
        exported["shafts"][0] = copy.deepcopy(exported["shafts"][4])
    elif kind == "omitted_moved":
        exported["shafts"].pop(0)
    elif kind == "unknown_axis":
        exported["shafts"][0]["axis_id"] = "unknown_axis"
    data["shafts"] = copy.deepcopy(exported["shafts"])
    return parent, exported, data, read


def test_import_has_no_original_adapter_or_candidate_callback():
    spec = importlib.util.spec_from_file_location("eoere_z180_correction_import_only", OWN.with_name("bridge.py"))
    module = importlib.util.module_from_spec(spec)
    with patch.object(importlib.util, "spec_from_file_location", side_effect=AssertionError("import-time adapter load")):
        spec.loader.exec_module(module)
    assert module._original is None


def test_exact_roster_delegates_original_all_source_checks_once():
    a = c.original()
    parent, exported, data, read = mutated("valid")
    original_validate = Mock(wraps=a.validate_descriptor)
    with patch.object(a, "read_ref", side_effect=read), patch.object(a, "validate_descriptor", original_validate), c.corrected_context(a):
        assert a.validate_descriptor(exported) is parent
        assert a.require_sources(data)["cached_source_export"] is exported
    assert original_validate.call_count == 2


@pytest.mark.parametrize("kind", ["duplicate_moved", "omitted_moved", "unknown_axis"])
def test_bad_roster_rejects_descriptor_and_coherently_joined_inputs_before_delegate(kind):
    a = c.original()
    _, exported, data, read = mutated(kind)
    original_validate = Mock(side_effect=AssertionError("bad roster reached frozen descriptor validation"))
    with patch.object(a, "read_ref", side_effect=read), patch.object(a, "validate_descriptor", original_validate), c.corrected_context(a):
        with pytest.raises(ValueError, match="exact unique 100 authenticated parent axes"):
            a.validate_descriptor(exported)
        with pytest.raises(ValueError, match="exact unique 100 authenticated parent axes"):
            a.require_sources(data)
    original_validate.assert_not_called()


@pytest.mark.parametrize("kind", ["duplicate_moved", "omitted_moved", "unknown_axis"])
def test_bad_roster_stops_original_builder_before_any_panel_callback(kind):
    a = c.original()
    _, _, data, read = mutated(kind)
    builder = Mock(side_effect=AssertionError("bad roster reached genuine builder/panel metadata"))
    with patch.object(a, "read_ref", side_effect=read), c.corrected_context(a), \
            pytest.raises(ValueError, match="exact unique 100 authenticated parent axes"):
        a.build_inputs(SimpleNamespace(build_inputs=builder), data["geometry"]["cached_source_export"],
                       a.SOURCE_MANIFEST, a.manifest()["unchanged_panel_method"])
    builder.assert_not_called()


def test_authenticated_parent_and_declared_moved_rosters_are_exact():
    a = c.original()
    parent, exported, _, read = mutated("valid")
    parent["shafts"][0] = copy.deepcopy(parent["shafts"][4])
    with patch.object(a, "read_ref", side_effect=read), c.corrected_context(a), \
            pytest.raises(ValueError, match="exact unique 100 authenticated parent axes"):
        a.validate_descriptor(exported)


def test_default_preflight_own_source_identity_and_original_numerical_hooks(tmp_path):
    a = c.original()
    w = a.production()
    b = w.frozen()
    before = {name: getattr(a, name) for name in ("OWN", "LOADED_SHA", "validate_descriptor", "source_pins")}
    core_prepare = Mock(side_effect=AssertionError("preflight reached preparation"))
    with patch.object(b.factory, "prepare", core_prepare), \
            patch.object(a, "build_inputs", side_effect=AssertionError("preflight built candidate input")), \
            patch.object(a, "validate_descriptor", side_effect=AssertionError("preflight consumed actual descriptor")):
        out = tmp_path / "source-only.json"
        assert c.main(["--out", str(out)]) == 0
    result = json.loads(out.read_bytes())
    expected = {str(c.OWN.relative_to(a.ROOT)): c.LOADED_SHA, str(c.FROZEN.relative_to(a.ROOT)): c.FROZEN_SHA}
    assert all(result["source_sha256"][path] == digest for path, digest in expected.items())
    assert result["provided"] == {} and len(result["missing"]) == 6
    assert result["production_readiness_claimed"] is False and result["complete_joint_resistance"] is None
    assert result["candidate_descriptor_or_input_construction_panel_K_frame_K_q_actions_solve_or_native_work_performed"] is False
    assert not any(result["release"].values()) and result["support"] == b.law.contract()
    assert result["generalized_residual_tolerance_n_inclusive"] == 1e-5
    assert result["schemas"] == {"descriptor": a.DESCRIPTOR_SCHEMA, "inputs": a.INPUT_SCHEMA, "review": a.REVIEW_SCHEMA,
                                  "method": a.METHOD_SCHEMA, "field": a.FIELD_SCHEMA, "admission": a.ADMISSION_SCHEMA}
    assert all(getattr(a, name) is value for name, value in before.items())
    with c.corrected_context(a), a.context(w, b):
        assert b.OWN == c.OWN and b.LOADED_SHA == c.LOADED_SHA
        pins = b.source_pins()
        method_pins = b.source_pins(method={"source_sha256": pins,
            "input_record": {"path": str(c.OWN.relative_to(a.ROOT)), "sha256": c.LOADED_SHA}})
        assert all(pins[path] == method_pins[path] == digest for path, digest in expected.items())
    assert b.OWN == w.FROZEN and b.LOADED_SHA == w.FROZEN_SHA
    core_prepare.assert_not_called()


@pytest.mark.parametrize("source", ["original", "correction"])
def test_conflicting_adapter_source_pin_rejected(source):
    a = c.original()
    path = c.FROZEN if source == "original" else c.OWN
    with c.corrected_context(a), pytest.raises(ValueError, match="source.*pin conflict"):
        a.source_pins(None, None, {str(path.relative_to(a.ROOT)): "0"*64})


def test_source_drift_and_nested_context_fail_closed_and_restore():
    a = c.original()
    with patch.object(c, "FROZEN_SHA", "0"*64), pytest.raises(ValueError, match="adapter bytes changed"):
        c.original()
    before = {name: getattr(a, name) for name in ("OWN", "LOADED_SHA", "validate_descriptor", "source_pins")}
    with pytest.raises(ValueError, match="unnested and serialized"), c.corrected_context(a), c.corrected_context(a):
        pytest.fail("nested source context admitted")
    assert all(getattr(a, name) is value for name, value in before.items())


@pytest.mark.parametrize("kind", ["file", "dangling_symlink"])
def test_original_output_ownership_stays_before_frozen_mechanics_import(tmp_path, kind):
    a = c.original()
    out = tmp_path / "occupied.json"
    out.write_text("preserved") if kind == "file" else out.symlink_to(tmp_path / "absent.json")
    with patch.object(a.production(), "frozen", side_effect=AssertionError("occupied output reached mechanics")), \
            pytest.raises(FileExistsError):
        c.main(["--out", str(out)])
    assert out.read_text() == "preserved" if kind == "file" else out.is_symlink()
