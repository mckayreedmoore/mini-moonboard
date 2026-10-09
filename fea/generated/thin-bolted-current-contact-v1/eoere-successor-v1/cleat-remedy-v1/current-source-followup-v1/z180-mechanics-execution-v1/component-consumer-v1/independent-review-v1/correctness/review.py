"""Independent inert boundary controls; every admission/reducer callback is fake.

Reuse the frozen test coupons. No genuine config, response, admission, CAD,
operator preparation or component arithmetic is loaded or executed.
"""
from __future__ import annotations

import builtins
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
ROOT = OWN.parents[10]
TARGET = OWN.parents[2]
BASE = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1"
PINS = {
    TARGET / "consume.py": "673498ce0cb1cb95bf6f263e2710b357f9792eaf8d12020c25a0812dc12a1d80",
    TARGET / "test_consume.py": "1024873b79c965172ddd7d4324063863c4d41561570f30c24d9cd895b6bd7d44",
    TARGET / "verification.json": "fe7cdb509058d116049fef87bf91266378d4dc252b68c9e80b64d9a439ce2286",
    TARGET.parent / "review-fix-v2/bridge.py": "dc224c51a46f78433df614ce53b76e2a8f4b1a7ac4c436b7d0d212f784388f55",
    BASE / "current-component-bridge-v1/consumer-v1/consume.py": "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9",
    BASE / "current-component-bridge-v1/followups-v1/followups.py": "a27bacf7260905f69c2a69bae60c0f2cf4ed1f4efd229100e3c8fb846b892798",
    BASE / "current-force-bridge-v1/review-fix-v2/bridge.py": "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643",
    BASE / "current-component-followup-review-v1/correctness/receipt.json": "8558675f92323487c6ef61fcbab1763cfd3f633f12e1b785de11dd3f40f8be7a",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources():
    for path, expected in PINS.items():
        assert sha(path) == expected, str(path)


def load(path, label):
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reject(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("expected fail-closed ValueError")


def with_coupon(tests, callback):
    with tempfile.TemporaryDirectory(prefix="inert-z180-component-review-") as root, pytest.MonkeyPatch.context() as patches:
        coupon = tests.tiny.__wrapped__(Path(root), patches)
        callback(coupon, patches)


def join_probes(tests):
    m = tests.m
    coarse = m.load(m.FROZEN["coarse"], {}, "review_only_coarse_descriptor_constants")
    joined = []
    for key in coarse.DESCRIPTOR_KEYS:
        def check(coupon, _patches, key=key):
            if isinstance(coupon.field["source_inputs"][key], list):
                coupon.field["source_inputs"][key].append({"foreign": True})
            else:
                coupon.field["source_inputs"][key]["foreign"] = True
            coupon.freeze(source=False)
            reject(lambda: tests.call(coupon))
            assert "inert_gate_callback" in coupon.events
            assert "inert_reducer_callback" not in coupon.events
            assert "source_scope_restored" in coupon.events
        with_coupon(tests, check)
        joined.append(key)
    def unaffected(coupon, _patches):
        coupon.exported["shafts"][4]["source_axis"]["point_xyz_mm"][2] = 170.
        coupon.freeze()
        reject(lambda: tests.call(coupon))
        assert "inert_gate_callback" in coupon.events and "inert_reducer_callback" not in coupon.events
    with_coupon(tests, unaffected)
    return {"all_descriptor_joins_independently_corrupted_and_rejected": joined,
            "changed_axis_outside_four_proposals_rejected_against_exact96_parent_complement": True,
            "all_actual_gate_and_reducer_callbacks_mocked": True}


def binding_probes(tests):
    m = tests.m
    checked = []
    for kind in ("descriptor_review_ref", "descriptor_review_release", "empty_state", "wrong_state", "missing_inherited_source"):
        def check(coupon, _patches, kind=kind):
            if kind.startswith("descriptor_review"):
                ref = coupon.config["sources"]["descriptor_review"]
                review = json.loads((coupon.root / ref["path"]).read_bytes())
                if kind == "descriptor_review_ref":
                    review["descriptor"]["sha256"] = "0"*64
                else:
                    review["release"]["structural_released"] = True
                coupon.config["sources"]["descriptor_review"] = tests.write(coupon.root, ref["path"], review)
                coupon.config_ref = tests.write(coupon.root, "config.json", coupon.config)
            elif kind == "empty_state":
                coupon.field["state_id"] = ""
                coupon.freeze()
                coupon.config["state_id"] = ""
                coupon.config_ref = tests.write(coupon.root, "config.json", coupon.config)
            elif kind == "wrong_state":
                coupon.field["state_id"] = "foreign-state"
                coupon.freeze()
            else:
                coupon.exported["source_sha256"].pop("proof.bin")
                ref = tests.write(coupon.root, "descriptor.json", coupon.exported)
                coupon.config["sources"]["descriptor"] = ref
                review_ref = coupon.config["sources"]["descriptor_review"]
                review = json.loads((coupon.root / review_ref["path"]).read_bytes())
                review["descriptor"] = ref
                coupon.config["sources"]["descriptor_review"] = tests.write(coupon.root, review_ref["path"], review)
                coupon.config_ref = tests.write(coupon.root, "config.json", coupon.config)
            reject(lambda: tests.call(coupon))
            assert "inert_gate_callback" not in coupon.events and "inert_reducer_callback" not in coupon.events
        with_coupon(tests, check)
        checked.append(kind)
    def drift_after_callback(coupon, patches):
        original = m.reduce_admitted
        def fake(*args, **kwargs):
            result = original(*args, **kwargs)
            (coupon.root / "proof.bin").write_bytes(b"changed by inert callback")
            return result
        patches.setattr(m, "reduce_admitted", fake)
        reject(lambda: tests.call(coupon))
        assert "inert_reducer_callback" in coupon.events
    with_coupon(tests, drift_after_callback)
    return {"bad_exact_bindings_rejected_before_fake_admission": checked,
            "source_drift_after_fake_reducer_rejected_before_success_result": True}


def seat_and_composition_probes(tests):
    m = tests.m
    coupon = list(tests.seat_coupon())
    baseline = m.nominal_seats(*coupon)
    assert baseline["nominal_wood_seats"] == 112 and len(baseline["new_own_nominal_seats"]) == 16
    assert len(baseline["unaffected_capture_ids"]) == 96
    assert "unknown" in baseline["scope"] and baseline["old_actions_or_strength_transferred"] is False
    duplicate_scenario = copy.deepcopy(coupon)
    duplicate_scenario[2]["scenarios"].append(copy.deepcopy(duplicate_scenario[2]["scenarios"][0]))
    assert m.nominal_seats(*duplicate_scenario)["nominal_wood_seats"] is None
    failed_old = copy.deepcopy(coupon)
    failed_old[4]["washer_seat_rows"][-1]["full_modeled_support"] = False
    reject(lambda: m.nominal_seats(*failed_old))
    too_many_new = copy.deepcopy(coupon)
    too_many_new[2]["scenarios"][0]["annular_queries"].append(copy.deepcopy(too_many_new[2]["scenarios"][0]["annular_queries"][0]))
    assert m.nominal_seats(*too_many_new)["nominal_wood_seats"] is None
    args = tests.fitting_coupon()
    composed = m.washer_composition(*args)
    assert len(composed["axes"]) == 100 and len(composed["service_cuts"]) == 27
    assert composed["partial_layout_contains_full_axes_or_service_cuts"] is False
    duplicate_cut = copy.deepcopy(args)
    duplicate_cut[2]["service_cuts"][-1] = copy.deepcopy(duplicate_cut[2]["service_cuts"][0])
    assert m.washer_composition(*duplicate_cut) is None
    duplicate_fitting = copy.deepcopy(args)
    duplicate_fitting[0]["fitting_operator_descriptors"][-1] = copy.deepcopy(duplicate_fitting[0]["fitting_operator_descriptors"][0])
    reject(lambda: m.washer_composition(*duplicate_fitting))
    return {"nominal16_own_plus96_inherited_seat_composition": True,
            "ambiguous_or_excess_annular_evidence_stays_null": True,
            "failed_unaffected_old_nominal_proof_rejected": True,
            "full100_axes_27_cuts_22_own_fitting_composition_checked_without_reducers": True,
            "duplicate_cut_stays_null_and_duplicate_fitting_rejected": True,
            "nominal_geometry_not_pressure_or_strength": True}


def check():
    verify_sources()
    prohibited_imports = []
    original_import = builtins.__import__
    def guarded_import(name, *args, **kwargs):
        if name.split(".")[0] in {"numpy", "scipy", "cadquery", "OCP", "mini_moonboard"}:
            prohibited_imports.append(name)
            raise AssertionError("inert review attempted numerical/geometry import: " + name)
        return original_import(name, *args, **kwargs)
    with patch.object(builtins, "__import__", guarded_import):
        tests = load(TARGET / "test_consume.py", "independent_z180_inert_fixtures")
        joins = join_probes(tests)
        bindings = binding_probes(tests)
        seats = seat_and_composition_probes(tests)
        assert not prohibited_imports
    verify_sources()
    return {"schema": "independent_z180_component_consumer_correctness_review/v1", "passed": True,
            "review_program_sha256": sha(OWN), "source_sha256": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
            "descriptor_joins": joins, "exact_bindings": bindings, "support_and_composition": seats,
            "genuine_config_field_admission_consumed": False, "actual_reducer_callbacks_or_calculations": 0,
            "prohibited_import_attempts": prohibited_imports,
            "CAD_BREP_panel_K_q_solve_native_frame_browser_executed": False,
            "substantial_confirmed_findings": [], "limits": [
                "Inert coupons and fake callbacks only; this review supplies no production config or readiness.",
                "Unchanged arithmetic reuse is limited to the separately frozen prior review and exact source hashes."]}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True, allow_nan=False))
