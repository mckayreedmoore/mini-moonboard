"""Admission-first, K-free current-q pose markers using frozen pure APIs."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OWN = Path(__file__).resolve()
TEST = OWN.with_name("test_pose_applicability.py")
GATE = OWN.with_name("admission.py")
GATE_SHA = "4b78722ab407a39d6e00fc9e16be0d370d0c837dea5880e45e7a2e277dd6efb6"
POSE = ROOT / "fea/generated/thin-bolted-joint-wrench-review/review-v4.py"
POSE_SHA = "c86cb3e84c0d16648e6a3d115da686afc6e2c97272cd06c4cbe3bfb93a15be55"
CONFIG = POSE.with_name("input-v4.json")
CONFIG_SHA = "a7ef7b7d82072b7f8898e34551661185f9108b8cca09179875f0f4fa5a005d7d"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
TEST_SHA = hashlib.sha256(TEST.read_bytes()).hexdigest()
LIMITS = [
    "Fixed admitted first-order q is replayed through finite rigid arms/geodesic interpolation; no force, equilibrium or branch is recomputed.",
    "Seventy zero first-shaft-roll coordinates are a pose lift only. Every finite shaft director/material rotation and OD*sin(tilt) marker depends on that lift; objective shaft/washer orientation is not recovered.",
    "Panel markers provide Ritz surface-normal tilt, not a complete panel material rotation.",
    "All thirty reference patches/584 points are retained; current trimmed overlap, holes, pressure, seating and surviving cell ownership are unresolved.",
    "No new motion, strain, overlap or strength criterion, resistance, complete-joint acceptance or release is established.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(pins):
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, "pose route source changed: " + path)


def load(path, expected, name):
    require(sha(path) == expected, "pose route module source differs")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(sha(path) == expected, "pose route module changed while loaded")
    return module


def _observe(field, gate, method):
    config = json.loads(CONFIG.read_bytes())
    # Use only frozen geometry/configuration; never read the three cold fields.
    cold_paths = {r["path"] for r in config["cold_diagnostic_sources"]}
    pins = {p: h for p, h in config["source_sha256"].items() if p not in cold_paths}
    verify(pins)
    keys = ("layout", "timber_unit_geometry", "geometry_cache", "panel_metadata", "panel_assessment", "integrated_geometry")
    layout, unit, cache, metadata, assessment, integrated = [json.loads((ROOT / config[k]).read_bytes()) for k in keys]
    geometry = gate.read_complete_geometry()
    require(geometry["pair_count"] == 30 and geometry["cell_count"] == 584, "complete pose reference census required")
    gate.linear.verify_timber_map(field, cache, geometry["grain_geometry"])
    pins = gate.linear.merge_pins(pins, geometry["source_sha256"])
    proof = {"patches": [p for _, _, p in geometry["patch_sources"]], "method": {"cell_size_mm": 25.}}
    # Local pose API view only: actual response.q stays untouched and admitted.
    view = {**field, "response": {"diagnostic_last_q": field["response"]["q"]}}
    out = method.evaluate(view, config, layout, method.shaft_inputs(layout, unit, cache), metadata,
                          assessment, integrated, proof, cache)
    cells, pairs = out["all272_timber_cell_motions"], out["all_six_timber_pair_summaries"]
    require(len(cells) == len({r["id"] for r in cells}) == 584 and len(pairs) == 30
            and {r["id"] for r in cells} == {c["id"] for p in proof["patches"] for c in p["cells"]}
            and out["diagnostic_q_sha256"] == method.canonical(field["response"]["q"]),
            "current q/all584 reference markers must remain exact")
    # Supersede the frozen helper's stale shaft-gauge wording in EVERY row.
    for table in ("representative_shaft_bearing_ports", "representative_own_washer_captures"):
        for row in out[table]:
            row.pop("gauge_independent_rotation_metric", None)
            row["finite_shaft_orientation_is_recorded_zero_linear_roll_lift_marker"] = True
            row["objective_shaft_or_washer_orientation_recovered"] = False
    metrics = tuple(method.max_summary(cells))
    compact_pairs = [{**{k: row[k] for k in ("patch_id", "first", "second", "reference_overlap_area_mm2", "cell_count")},
        "governing_markers": {k: {"id": row["witnesses"][k]["id"], k: row["witnesses"][k][k]} for k in metrics}}
        for row in pairs]
    worst = {name: method.max_summary(out[key]) for name, key in (
        ("flanges", "representative_flange_contacts"), ("bearings", "representative_shaft_bearing_ports"),
        ("captures", "representative_own_washer_captures"), ("panels", "representative_panel_receiver_points"))}
    return {"all30_reference_pair_summaries": compact_pairs, "all584_marker_sha256": method.canonical(cells),
        "all584_governing_markers": method.max_summary(cells), "representative_governing_markers": worst,
        "representative_internal_fitting_pose": out["representative_internal_fitting_pose"],
        "pose_map_sha256": out["pure_reconstructed_map_sha256"],
        "admitted_timber_map_sha256": out["diagnostic_current_coordinate_map_sha256"],
        "physical_q_dofs": field["counts"]["dofs"], "pose_only_added_zero_roll_coordinates": 70,
        "shaft_dof_start": out["recorded_base_shaft_dof_start"], "source_sha256": pins}


def consume(field_path, admission, *, expected_field_sha256, admission_sha256):
    """Authenticate actual new receipt/raw bytes BEFORE accessing any q."""
    pins = {str(p.relative_to(ROOT)): h for p, h in
            ((OWN, LOADED_SHA), (TEST, TEST_SHA), (GATE, GATE_SHA), (POSE, POSE_SHA), (CONFIG, CONFIG_SHA))}
    require(admission_sha256 == GATE_SHA, "mandatory actual new pose admission gate SHA required")
    payload = Path(field_path).read_bytes()
    require(hashlib.sha256(payload).hexdigest() == expected_field_sha256, "exact raw pose field SHA required before vector consumption")
    verify(pins)
    gate = load(GATE, GATE_SHA, "current_pose_actual_observer_isolation_gate")
    field, admitted_pins = gate.require_admitted_payload(payload, admission, admission_sha256=GATE_SHA)
    method = load(POSE, POSE_SHA, "frozen_current_q_pure_pose_apis")
    before, receipt_before = method.canonical(field), method.canonical(admission)
    observed = _observe(field, gate, method)
    pins = gate.linear.merge_pins(pins, admitted_pins, observed.pop("source_sha256"))
    verify(pins)
    require(Path(field_path).read_bytes() == payload and method.canonical(field) == before
            and method.canonical(admission) == receipt_before, "immutable current pose inputs changed")
    return {"schema": "thin_bolted_admitted_current_q_pose_applicability/v1",
        "field_sha256": expected_field_sha256, "field_canonical_sha256": before,
        "state_id": field["state_id"], "case_id": field["case_id"], "accessory_placement": field["accessory_placement"],
        "q_canonical_sha256": method.canonical(field["response"]["q"]),
        "admission_receipt_canonical_sha256": receipt_before, "actual_gate_sha256": GATE_SHA,
        "source_sha256": pins, "markers": observed, "limits": LIMITS,
        "material_K_loaded_assembled_or_evaluated": False, "old_main_or_old_field_admission_called": False,
        "finite_response_equilibrium_contact_area_strain_acceptance_or_capacity_established": False,
        "release": copy.deepcopy(field["release"])}
