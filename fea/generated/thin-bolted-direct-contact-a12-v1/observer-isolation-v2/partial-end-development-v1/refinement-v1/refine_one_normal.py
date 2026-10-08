"""Refine only one loose partial-end affine normal enclosure, without CAD.

Keep the other 17 results and the original coarse bound unchanged. Reuse the
reviewed coupled section-stress kernel and CD1 fully braced reference function.
Pressure, end traction, concentration, fracture, shear/torsion and stability
remain separate and unqualified.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[6]
OWN = Path(__file__).resolve()
LOADED_SOURCE_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
LEAF = OWN.parent
PARTIAL_DIR = LEAF.parent
GATE_DIR = PARTIAL_DIR.parent
PARTIAL_PATH = PARTIAL_DIR / "partial_end.py"
PARTIAL_SHA = "84f60fe9afacd78c22fcf09e7757d49d2923b26c096cebca033e3adc1a9ce165"
COARSE_SHA = "2f3954f45aae53789ef67095adda5af4b9d3d6f41d317b149b1d04aab6a94a7c"
GEOMETRY_SHA = "0490950906f1147cade510861178b0cc936552b98eb4185404c05694f224c188"
GEOMETRY_PLAN_SHA = "4f622ca991a2bc5829faf5a01401df18c558d315cdc5ab28c0d514389e5f9a72"
STRESS_TEST_SHA = "2e4f337401fe3007e4b0c52faf0f52c17d851ffb9697e1c762e4c83330b573b7"
EXPECTED_KEY = ("lumber_leg_left", -374.9922284)
EXPECTED_AREA_MM2 = 3548.380002


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


require(sha(PARTIAL_PATH) == PARTIAL_SHA, "unchanged reviewed partial-end adapter required")
_spec = importlib.util.spec_from_file_location("frozen_partial_reference_for_one_normal_cut", PARTIAL_PATH)
partial = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(partial)
net, pure, box = partial.net, partial.pure, partial.net.box


def cut_key(row):
    return row["member"], row["station_global_grain_projection_mm"]


def join_one(geometry, request, coarse):
    """Exact requested cut IDs; tolerance applies only to computed geometry."""
    require(geometry["schema"] == "thin_bolted_one_partial_end_finished_geometry/v1"
            and geometry["candidate"] == pure.unit.CANDIDATE and geometry["state_id"] is None
            and geometry["selected_cut_count"] == geometry["cached_finished_BREP_count"] == 1
            and geometry["source_pins_before_after_unchanged"] is True
            and geometry["candidate_response_current_force_pressure_or_strength_consumed"] is False
            and geometry["other_partial_net_tip_or_lower_subsolid_queries_executed"] is False
            and geometry["requested_station_global_grain_projection_mm"] == EXPECTED_KEY[1]
            and not any(geometry["release"].values()), "one reviewed geometry-only partial section required")
    require(request["schema"] == "thin_bolted_one_partial_end_geometry_readiness/v1"
            and request["candidate"] == pure.unit.CANDIDATE and request["state_id"] is None
            and request["request_count"] == request["cached_BREP_count"] == 1
            and request["selection_source"]["sha256"] == COARSE_SHA,
            "parent-frozen one-cut geometry request required")
    require(coarse["schema"] == "thin_bolted_18_partial_end_conditional_affine_normal_findings/v1"
            and coarse["counts"] == {"partial_end_sections": 18, "reference_header_bearing_patch_overlap_witnesses": 12,
                "conditional_normal_bounds_below_one": 17, "conservative_normal_bounds_exceeding_one": 1}
            and coarse["source_pins_before_after_unchanged"] is True and not any(coarse["release"].values()),
            "preserve exact reviewed 18-cut coarse census")
    rows = coarse["18_conditional_partial_end_findings"]
    chosen = [row for row in rows if row["fully_braced_CD1_normal_reference_enclosure"] > 1]
    require(len(rows) == len({cut_key(row) for row in rows}) == 18 and len(chosen) == 1
            and cut_key(chosen[0]) == EXPECTED_KEY and chosen[0]["expected_finished_area_mm2"] == EXPECTED_AREA_MM2
            and len(request["requests"]) == len(geometry["finished_sections"]) == 1,
            "only sole coarse-inconclusive own partial cut may be refined")
    planned, properties = request["requests"][0], geometry["finished_sections"][0]
    require(cut_key(planned) == EXPECTED_KEY and properties["member"] == EXPECTED_KEY[0]
            and properties["state_id"] is None and planned["expected_frozen_same_station_area_mm2"] == EXPECTED_AREA_MM2
            and properties["expected_frozen_same_station_area_mm2"] == EXPECTED_AREA_MM2
            and abs(properties["station_global_grain_projection_mm"] - EXPECTED_KEY[1]) <= 1e-8
            and abs(properties["finished_area_mm2"] - EXPECTED_AREA_MM2) <= .001
            and np.linalg.norm(np.asarray(properties["basis_u_v_grain_xyz"]) - planned["basis_u_v_grain_xyz"]) < 1e-8
            and properties["linear_normal_stress"] is None and properties["bores_or_other_voids_restored"] is False
            and properties["shear_area_method_qualified"] is False,
            "exact one requested cut/area/basis and geometry-only properties required")
    return properties


def read_frozen():
    paths = (PARTIAL_DIR / "partial-end-findings.json", LEAF / "one-section-geometry.json", LEAF / "one-section-plan.json")
    digests = (COARSE_SHA, GEOMETRY_SHA, GEOMETRY_PLAN_SHA)
    for path, digest in zip(paths, digests, strict=True):
        require(sha(path) == digest, "frozen coarse/geometry source changed: " + str(path))
    coarse, geometry, request = [json.loads(path.read_bytes()) for path in paths]
    properties = join_one(geometry, request, coarse)
    pins = net.merge_pins(geometry["source_sha256"],
        {str(path.relative_to(ROOT)): digest for path, digest in zip(paths, digests, strict=True)}, {
        str(OWN.relative_to(ROOT)): LOADED_SOURCE_SHA, str(PARTIAL_PATH.relative_to(ROOT)): PARTIAL_SHA,
        str(OWN.with_name("test_refine_one_normal.py").relative_to(ROOT)): sha(OWN.with_name("test_refine_one_normal.py")),
        str((GATE_DIR / "section-box-v1/test_normal_stress.py").relative_to(ROOT)): STRESS_TEST_SHA,
        str(partial.NET_PATH.relative_to(ROOT)): partial.NET_SHA,
        str((GATE_DIR / "section-box-v1/normal_stress.py").relative_to(ROOT)): net.BOX_SHA})
    pure.verify_pins(pins)
    return coarse, geometry, properties, pins


def plan():
    require(sha(OWN) == LOADED_SOURCE_SHA, "loaded one-cut normal helper changed")
    _, _, properties, pins = read_frozen()
    pure.verify_pins(pins)
    return {"schema": "thin_bolted_one_partial_normal_refinement_readiness/v1", "candidate": pure.unit.CANDIDATE,
        "source_sha256": pins, "source_pins_before_after_unchanged": True,
        "field_sha256": net.FIELD_SHA, "actual_admission_sha256": net.ADMISSION_SHA, "actual_gate_sha256": net.GATE_SHA,
        "refinement_count": 1, "exact_requested_cut_id": {"member": EXPECTED_KEY[0], "station_global_grain_projection_mm": EXPECTED_KEY[1]},
        "expected_frozen_area_mm2": EXPECTED_AREA_MM2, "exact_measured_area_mm2": properties["finished_area_mm2"],
        "final_expected_census": {"partial_end_sections": 18, "preserved_coarse_findings": 17, "new_exact_property_box_findings": 1},
        "methods_reused": "Unchanged box6bd/c222 full-centroid/coupled stress kernel and partial84f/net578 CD1 fully braced reference function.",
        "existing_stress_fixture_count": 13, "new_one_join_fixture_count": 1,
        "current_field_actions_consumed": False, "parent_readiness_required_before_actual_consume": True,
        "CAD_query_K_native_global_or_pressure_execution": False, "release": dict(pure.unit.RELEASE)}


def consume(field_path, admission_path, plan_path, plan_sha):
    require(bool(os.environ.get("MINI_MOONBOARD_PARENT_MEMBER_EXECUTION")), "parent-owned actual refinement marker required")
    require(sha(OWN) == LOADED_SOURCE_SHA and sha(PARTIAL_PATH) == PARTIAL_SHA
            and importlib.metadata.version("numpy") == "2.5.2",
            "reviewed loaded one-cut and partial methods required")
    require(sha(plan_path) == plan_sha, "parent-frozen one-cut normal readiness required")
    readiness = json.loads(Path(plan_path).read_bytes())
    require(readiness == plan(), "exact unchanged readiness and source joins required")
    payload, receipt_payload = Path(field_path).read_bytes(), Path(admission_path).read_bytes()
    require(hashlib.sha256(payload).hexdigest() == net.FIELD_SHA and hashlib.sha256(receipt_payload).hexdigest() == net.ADMISSION_SHA,
            "exact current field and actual receipt required")
    receipt = json.loads(receipt_payload)
    gate = net.load("actual_admission_for_one_partial_normal_refinement", GATE_DIR / "admission.py", net.GATE_SHA)
    # Authenticate before accessing any saved signed wrench or force component.
    field, verified = gate.require_admitted_payload(payload, receipt, admission_sha256=net.GATE_SHA)
    before, receipt_before = pure.references.canonical_sha(field), pure.references.canonical_sha(receipt)
    box.member.verify_alias_state_labels(field)
    coarse, geometry, properties, extra = read_frozen()
    require(coarse["field_sha256"] == net.FIELD_SHA and all(coarse[key] == field[key] for key in pure.IDENTITIES),
            "only same admitted-state saved partial wrench allowed")
    pins = net.merge_pins(extra, coarse["source_sha256"], geometry["source_sha256"], verified, {
        str(Path(plan_path).resolve().relative_to(ROOT)): plan_sha,
        str(Path(field_path).resolve().relative_to(ROOT)): net.FIELD_SHA,
        str(Path(admission_path).resolve().relative_to(ROOT)): net.ADMISSION_SHA})
    pure.verify_pins(pins)
    rows = coarse["18_conditional_partial_end_findings"]
    original = next(row for row in rows if cut_key(row) == EXPECTED_KEY)
    normal = box.section_box_bound(properties, original["signed_same_cut_wrench"])
    component_bound = sum(abs(beta) * max(abs(low - center), abs(high - center))
        for beta, (low, high), center in zip(normal["normal_stress_gradient_uv_n_mm3"],
            [properties["bounds_uv_mm"][axis] for axis in ("u", "v")], properties["centroid_uv_mm"], strict=True))
    reference = net.nds.adjusted_reference(139.7)
    ratio = net.reference_enclosure(normal["mean_axial_normal_stress_mpa"], component_bound, reference)
    refined = {"member": EXPECTED_KEY[0], "station_global_grain_projection_mm": EXPECTED_KEY[1],
        "original_conservative_reference_enclosure_upper": original["fully_braced_CD1_normal_reference_enclosure"],
        "exact_centroid_coupled_inertia_normal_stress_box_enclosure": normal,
        "sum_of_separate_linear_gradient_component_maxima_upper_mpa": float(component_bound),
        "fully_braced_CD1_normal_reference_enclosure": float(ratio),
        "preserved_necessary_average_resultant_shear_over_CD1_Fv": original["necessary_average_resultant_shear_over_CD1_Fv"],
        "actual_end_traction_contact_concentration_fracture_shear_torsion_stability_or_member_strength": None}
    summaries = []
    for index, row in enumerate(rows):
        exact = cut_key(row) == EXPECTED_KEY
        value = float(ratio) if exact else row["fully_braced_CD1_normal_reference_enclosure"]
        require(exact or value <= 1, "all 17 preserved coarse findings were already below one")
        summaries.append({"member": row["member"], "station_global_grain_projection_mm": row["station_global_grain_projection_mm"],
            "source_original_partial_result_row_index_unitless": index,
            "method": "new_exact_centroid_coupled_inertia_box_enclosure" if exact else "original_conservative_finding_preserved",
            "fully_braced_CD1_normal_reference_enclosure": value,
            "disposition": "conditional_reference_enclosure_below_one" if value <= 1 else "conditional_upper_bound_exceeds_one",
            "actual_partial_end_member_strength_or_acceptance": None})
    require(len(summaries) == 18 and sum(row["method"].startswith("new_exact") for row in summaries) == 1,
            "preserve final 18-cut census with only one exact refinement")
    pure.verify_pins(pins)
    require(sha(OWN) == LOADED_SOURCE_SHA and Path(field_path).read_bytes() == payload
            and Path(admission_path).read_bytes() == receipt_payload and pure.references.canonical_sha(field) == before
            and pure.references.canonical_sha(receipt) == receipt_before, "loaded helper or admitted inputs changed")
    return {"schema": "thin_bolted_final18_partial_end_affine_normal_dispositions/v1",
        **{key: field[key] for key in pure.IDENTITIES}, "field_sha256": net.FIELD_SHA,
        "source_sha256": pins, "source_pins_before_after_unchanged": True,
        "counts": {"partial_end_sections": 18, "preserved_coarse_findings": 17, "new_exact_property_box_findings": 1,
            "conditional_normal_bounds_below_one": sum(row["fully_braced_CD1_normal_reference_enclosure"] <= 1 for row in summaries),
            "conditional_normal_bounds_exceeding_one": sum(row["fully_braced_CD1_normal_reference_enclosure"] > 1 for row in summaries)},
        "final_18_scoped_partial_normal_dispositions": summaries, "one_refined_exact_centroid_inertia_box_finding": refined,
        "CD1_fully_braced_reference_values": reference,
        "preserved_coarse_packet": {"path": str((PARTIAL_DIR / "partial-end-findings.json").relative_to(ROOT)), "sha256": COARSE_SHA},
        "gravity_law": coarse["gravity_law"], "twelve_header_bearing_overlap_dispositions_preserved": True,
        "tips_802_nets_226_rectangles_or_shear_findings_recomputed": False,
        "actual_current_distributed_contact_pressure_bound_established": False,
        "complete_end_wrench_concentration_fracture_shear_torsion_stability_or_member_strength": None,
        "CAD_query_q_K_native_global_or_pressure_execution": False, "release": dict(pure.unit.RELEASE),
        "execution": {"sys_orig_argv": list(sys.orig_argv), "sys_argv": list(sys.argv), "python_executable": sys.executable,
            "python_version": platform.python_version(), "numpy_version": importlib.metadata.version("numpy"),
            "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "MINI_MOONBOARD_PARENT_MEMBER_EXECUTION")}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-plan", action="store_true")
    parser.add_argument("--field", type=Path)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--plan-sha256")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "distinct one-cut normal evidence output required")
    if args.prepare_plan:
        require(all(value is None for value in (args.field, args.admission, args.plan, args.plan_sha256)),
                "readiness accesses no field actions")
        result = plan()
    else:
        require(all(value is not None for value in (args.field, args.admission, args.plan, args.plan_sha256)),
                "exact field/receipt and parent-frozen normal readiness required")
        result = consume(args.field, args.admission, args.plan, args.plan_sha256)
    args.out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
