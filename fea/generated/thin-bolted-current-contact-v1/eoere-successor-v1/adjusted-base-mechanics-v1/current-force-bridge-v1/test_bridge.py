"""Source hooks and tiny saved-field/known-answer fixtures; no candidate run."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("eoere_current_force_bridge_fixture", OWN.with_name("bridge.py"))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def fixture_field():
    gradient = [1e-5]
    normals = dict.fromkeys(b.law.RESTRAINED_HOSTS, 1.)
    return {"schema": b.FIELD_SCHEMA, "release": b.core.RELEASE,
        "disposition": "CONVERGED_CANDIDATE_PENDING_INDEPENDENT_ADMISSION",
        "analytical_support_scenario": b.law.contract(), "independent_admission_required": True,
        "usable_conditional_actions": True, "response": {"converged": True,
            "original_floor_switching_law_used": False, "original_joint_and_normal_laws_used": True,
            "physical_residual_uses_unmodified_laws": False,
            "physical_residual_uses_declared_support_scenario": True,
            "generalized_residual_tolerance_n": 1e-5,
            "legacy_nonbearing_key_means_disabled_xy_hosts": True,
            "q": [0.], "q_canonical_sha256": b.canonical([0.]),
            "gradient_n": gradient, "gradient_canonical_sha256": b.canonical(gradient), "gradient_inf_n": 1e-5,
            "fixed_floor_support_v1": {**b.law.contract(), "normal_force_n_by_host": normals,
                                       "both_credited_legs_in_bearing": True}}}


def test_default_source_preflight_never_constructs_or_loads_candidate_operators(tmp_path):
    def prohibited(*_args, **_kwargs):
        raise AssertionError("candidate mechanics called")
    args = b.parse_args(["--out", str(tmp_path / "unused.json")])
    with patch.object(b.factory, "prepare", prohibited), patch.object(b.frame, "ElasticAssembly", prohibited), \
            patch.object(b, "methods", prohibited), patch.object(b, "build_inputs", prohibited):
        result = b.preflight(args)
    assert result["missing"] == ["inputs", "input_review", "method_input", "source_export", "source_manifest", "panel_bank"]
    assert result["production_readiness_claimed"] is False
    assert result["candidate_CAD_panel_K_global_K_q_actions_or_solve_performed"] is False
    assert not any(result["release"].values())


def test_factory_hooks_restore_on_error_and_reject_nested_context():
    with pytest.raises(RuntimeError, match="fixture interruption"), b.factory_boundary():
        assert b.factory.SCHEMA == b.INPUT_SCHEMA
        assert b.factory.read_inputs is b.read_inputs
        with pytest.raises(ValueError, match="unnested and serialized"), b.factory_boundary():
            pass
        raise RuntimeError("fixture interruption")
    assert b.factory.SCHEMA == b.ORIGINAL_SCHEMA
    assert b.factory.read_inputs is b.ORIGINAL_READ
    assert b.factory.authenticate_source_review is b.ORIGINAL_AUTHENTICATE


def test_private_producer_and_admission_compile_with_exact_hooks():
    assert callable(b.compile_execute(lambda extra=None: extra or {}))
    assert set(b.admission_functions()) == {"require_pending_field", "audit", "require_admitted_payload"}
    with pytest.raises(ValueError, match="hook locations differ"):
        b.compile_function(b.old_gate.OWN, "audit", vars(b.old_gate),
            replacements=b.ADMISSION_REPLACEMENTS, expected_counts=dict.fromkeys(b.ADMISSION_REPLACEMENTS, 99))


def test_inclusive_original_tolerance_passes_tiny_pending_field():
    b.admission_functions()["require_pending_field"](fixture_field())


@pytest.mark.parametrize("mutation", [
    lambda f: f.update(schema=b.old_runner.FIELD_SCHEMA),
    lambda f: f["response"].update(diagnostic_last_q=[0.]),
    lambda f: f["response"].update(gradient_inf_n=1.00000001e-5),
    lambda f: f["response"].update(q=[1.]),
    lambda f: f["response"].update(original_floor_switching_law_used=True),
    lambda f: f["response"]["fixed_floor_support_v1"]["normal_force_n_by_host"].update(lumber_leg_left=0.),
    lambda f: f["release"].update(structural_released=True),
])
def test_foreign_failed_or_unbound_pending_fields_reject(mutation):
    field = copy.deepcopy(fixture_field())
    # Release fixture must not mutate the imported frozen policy dictionary.
    field["release"] = dict(field["release"])
    mutation(field)
    with pytest.raises(ValueError):
        b.admission_functions()["require_pending_field"](field)


@pytest.mark.parametrize("data", [
    {"schema": b.ORIGINAL_SCHEMA},
    {"schema": b.INPUT_SCHEMA, "release": b.core.RELEASE, "optional_2026_extra": True},
    {"schema": b.INPUT_SCHEMA, "release": b.core.RELEASE, "optional_2026_extra": False,
     "geometry": {"report": {"path": "foreign.json", "sha256": "0"*64},
                  "source_manifest": b.SOURCE_MANIFEST, "cached_source_export": {"path": "missing.json", "sha256": "0"*64}}},
])
def test_old_schema_extra_grid_and_foreign_geometry_fail_before_source_reads(data):
    with patch.object(b, "read_ref", side_effect=AssertionError("unexpected source read")), pytest.raises(ValueError):
        b.require_current_sources(data)


def test_actual_run_requires_all_source_refs_and_parent_marker_before_preparation(tmp_path):
    with pytest.raises(ValueError, match="exact input/review/method/slot"):
        b.parse_args(["--mode", "run", "--run", "--case-id", "a12-rear", "--out", str(tmp_path / "field.json")])
    with patch.dict(b.os.environ, {}, clear=True), pytest.raises(ValueError, match="serialized force-run marker"):
        b.slot_check(b.SimpleNamespace(), "input", "method")


def test_reused_known_answer_floor_method_without_candidate_work():
    fixture = b.load(b.PACKET / "floor-practical-resolution-v1/check_method.py",
        "4c2e10ae9aa11c64fb84b19917515b9d18759d988d8fef208c63eeda65e6ff64", "eoere_current_bridge_known_answer_floor")
    result = fixture.run()
    assert result["passed"] is True and result["known_answer_and_negative_fixture_count"] == 7
    assert result["maximum_new_law_gradient_n"] < 1e-12
    assert result["no_candidate_preparation_CAD_or_response"] is True


def test_existing_output_preserved(tmp_path):
    path = tmp_path / "existing.json"
    path.write_text(json.dumps({"preserve": True}))
    original = path.read_bytes()
    with pytest.raises(ValueError, match="preserve existing"):
        b.main(["--out", str(path)])
    assert path.read_bytes() == original
