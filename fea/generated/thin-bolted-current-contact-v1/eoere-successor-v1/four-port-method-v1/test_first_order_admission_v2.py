"""Narrow compatibility/source-label coupons; no candidate field or assembly."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).with_name("first_order_admission_v2.py")
SPEC = importlib.util.spec_from_file_location("eoere_corrected_gate_fixtures", PATH)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
COUPON_SPEC = importlib.util.spec_from_file_location("eoere_e61_genuine_coupons", PATH.with_name("test_first_order_admission.py"))
coupon = importlib.util.module_from_spec(COUPON_SPEC)
COUPON_SPEC.loader.exec_module(coupon)


def recovered_toy(tmp_path, *, zero_q=False):
    data, p, snapshot = coupon.saved_toy(tmp_path)
    q = np.zeros(p.assembly.ndof) if zero_q else np.random.default_rng(14).normal(size=p.assembly.ndof)*.001
    fresh = gate.base.replay_original(snapshot, q, ["wood-a"])
    response = {"converged": True, "q": q, "connector_local_force_n": fresh[3], "normal_contact_force_n": fresh[4],
        "nonbearing_no_slip_removed": [], "support_state_search_v1": {"accepted_enabled_centroid_xy_hosts": ["wood-a"]}}
    field = gate.core.recover(p, response)
    field["source_inputs"] = data
    return field, snapshot, gate.base.OwnedMaps(snapshot, data), q


def test_genuine_loaded_recovery_and_strict_alias_metadata_at_zero_and_nonzero_q(tmp_path):
    for zero in (False, True):
        field, snapshot, maps, q = recovered_toy(tmp_path/str(zero), zero_q=zero)
        result = gate.verify_fitting_and_alias_recovery(field, snapshot, maps, q)
        assert result["loaded_root_recoveries_replayed"] == 1
        assert result["own_surface_aggregate_recoveries_replayed"] == 2
        assert result["own_signed_external_action_shaft_cut_recoveries_replayed"] == 1


@pytest.mark.parametrize("mutation", ["steel-flange", "steel-receiver", "steel-angle", "steel-interval", "wood-member", "wood-grain", "own-only", "table", "extra-key", "raw-axis", "raw-host", "raw-flange", "raw-quad", "capture-end", "screw-panel", "screw-withdrawal", "screw-receiver-force"])
def test_exact_source_label_mutations_reject_even_on_zero_force_rows(tmp_path, mutation):
    field, snapshot, maps, q = recovered_toy(tmp_path, zero_q=True)
    steel, wood = field["common_shaft_steel_port_actions"][0], field["common_shaft_wood_bearing_actions"][0]
    if mutation.startswith("steel-"):
        key = {"steel-flange": "flange", "steel-receiver": "receiver", "steel-angle": "angle_id", "steel-interval": "surface_interval_mm"}[mutation]
        steel[key] = [99., 100.] if key == "surface_interval_mm" else "foreign"
    elif mutation == "wood-member":
        wood["member"] = "foreign-wood"
    elif mutation == "wood-grain":
        wood["grain_axis_xyz"] = [0., 1., 0.]
    elif mutation == "own-only":
        steel["force_on_opposed_flange_or_other_host_not_inferred"] = False
    elif mutation == "table":
        field["common_shaft_wood_bearing_actions"].append(field["common_shaft_steel_port_actions"].pop())
    elif mutation == "extra-key":
        steel["adopted_capacity"] = 1.
    elif mutation.startswith("raw-"):
        raw = field["common_shaft_bearing_actions"][0]
        key = {"raw-axis": "axis_id", "raw-host": "host", "raw-flange": "flange", "raw-quad": "quad_index"}[mutation]
        raw[key] = 99 if key == "quad_index" else "foreign"
    elif mutation == "capture-end":
        field["shaft_end_capture_actions"][0]["end"]["host"] = "foreign"
    elif mutation == "screw-panel":
        field["panel_screw_actions"][0]["panel"] = "foreign"
    elif mutation == "screw-withdrawal":
        field["panel_screw_actions"][0]["withdrawal_n"] = 1.
    else:
        field["panel_screw_actions"][0]["force_on_receiver_xyz_n"][0] = 1.
    with pytest.raises(ValueError):
        gate.verify_fitting_and_alias_recovery(field, snapshot, maps, q)


def minimal_pending():
    return {"schema": gate.base.FIELD_SCHEMA, "disposition": "CONVERGED_CANDIDATE_PENDING_INDEPENDENT_ADMISSION",
        "independent_admission_required": True, "state_id": "synthetic-contract", "case_id": "a12-rear",
        "accessory_placement": "retained-original-top-hold", "release": gate.core.RELEASE,
        "source_sha256": gate.source_pins(), "operator_bundle": {}, "original_operator_fingerprint_sha256": "fixture",
        "response": {"q": [0.], "gradient_n": [0.], "converged": True,
            "physical_residual_uses_unmodified_laws": True, "generalized_residual_tolerance_n": 1e-5},
        **{key: [] for key in gate.base.TABLES}}


def correction():
    return {"reused_source_path": str(gate.ORIGINAL.relative_to(gate.frame.ROOT)), "reused_source_sha256": gate.ORIGINAL_SHA,
        "removed_absent_historical_flag_guards": list(gate.CORRECTED_FUNCTIONS),
        "exact_own_alias_metadata_and_table_membership_verified": True,
        "physical_laws_or_algorithms_changed": False, "field_bytes_or_action_aliases_modified": False}


def contract_receipt(field, raw):
    # Cheap consumer contract fixture ONLY; no full numerical audit is asserted.
    return {"schema": gate.SCHEMA, gate.SUCCESS: True, "source_path": str(gate.OWN.relative_to(gate.frame.ROOT)),
        "admission_source_sha256": gate.LOADED_SHA, "input_raw_sha256": hashlib.sha256(raw).hexdigest(),
        "input_canonical_sha256": gate.base.canonical(field), "release": gate.core.RELEASE, "source_sha256": gate.source_pins(),
        **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
        "support_search_checks": {"final_q_canonical_sha256": gate.base.canonical(field["response"]["q"])},
        "original_law_checks": {"full_signed_gradient_canonical_sha256": gate.base.canonical(field["response"]["gradient_n"])},
        "operator_bundle": field["operator_bundle"], "original_operator_fingerprint_sha256": field["original_operator_fingerprint_sha256"],
        "table_canonical_sha256": {key: gate.base.canonical(field[key]) for key in gate.base.TABLES},
        "admission_compatibility_correction": correction()}


def test_absent_historical_flag_passes_only_corrected_contract_and_actual_new_sha(monkeypatch):
    field = minimal_pending()
    assert "usable_conditional_actions" not in field
    raw = json.dumps(field).encode()
    receipt = contract_receipt(field, raw)
    parsed, pins = gate.require_admitted_payload(raw, receipt, admission_sha256=gate.LOADED_SHA)
    assert parsed == field and pins[str(gate.OWN.relative_to(gate.frame.ROOT))] == gate.LOADED_SHA
    with pytest.raises(ValueError):
        gate.base.require_admitted_payload(raw, receipt, admission_sha256=gate.base.LOADED_SHA)

    def no_operator_consumption(_pointer):
        raise ValueError("synthetic before operator read")

    monkeypatch.setattr(gate.base.bundle, "read_snapshot", no_operator_consumption)
    with pytest.raises(ValueError, match="synthetic before operator read"):
        gate.CORRECTED_AUDIT(raw)
    with pytest.raises(ValueError, match="pending"):
        gate.base.audit_first_order_state(raw)


@pytest.mark.parametrize("mutation", ["raw", "q", "table", "state", "source", "old-path", "correction"])
def test_corrected_same_byte_consumer_mutations_reject(mutation):
    field = minimal_pending()
    raw = json.dumps(field).encode()
    receipt = contract_receipt(field, raw)
    if mutation == "raw":
        raw += b" "
    elif mutation == "q":
        receipt["support_search_checks"]["final_q_canonical_sha256"] = "0"*64
    elif mutation == "table":
        receipt["table_canonical_sha256"]["four_port_fitting_actions"] = "0"*64
    elif mutation == "state":
        receipt["state_id"] = "old"
    elif mutation == "source":
        receipt["source_sha256"][str(gate.ORIGINAL.relative_to(gate.frame.ROOT))] = "0"*64
    elif mutation == "old-path":
        receipt["source_path"] = str(gate.ORIGINAL.relative_to(gate.frame.ROOT))
    else:
        receipt["admission_compatibility_correction"]["physical_laws_or_algorithms_changed"] = True
    with pytest.raises(ValueError):
        gate.require_admitted_payload(raw, receipt, admission_sha256=gate.LOADED_SHA)


def test_original_sources_module_identity_and_globals_remain_genuine():
    before = {key: gate.base.__dict__[key] for key in ("OWN", "LOADED_SHA", "audit_first_order_state", "require_admitted_payload", "verify_fitting_and_alias_recovery")}
    for name in gate.CORRECTED_FUNCTIONS:
        fn = gate.corrected_function(name, dict(gate.CONTEXT))
        assert fn.__code__.co_filename == str(gate.OWN)
    assert {key: gate.base.__dict__[key] for key in before} == before
    assert Path(gate.base.__file__).resolve() == gate.ORIGINAL
    assert gate.frame.sha(gate.ORIGINAL) == gate.ORIGINAL_SHA
    with pytest.raises(ValueError):
        gate.corrected_function("verify_actions", dict(gate.CONTEXT))
