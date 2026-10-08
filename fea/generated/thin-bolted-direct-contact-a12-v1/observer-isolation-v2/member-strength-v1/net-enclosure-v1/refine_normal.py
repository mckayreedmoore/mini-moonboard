"""Reuse exact geometry to sharpen only 46 inconclusive affine normal bounds.

Original conservative results and five older exact findings remain immutable.
Final 802 dispositions are conditional CD1 fully braced normal comparisons;
contact pressure, concentration, fracture, shear/torsion and stability are
separate. No CAD, q/K/global response or native execution occurs.
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
MEMBER_DIR = LEAF.parent
GATE_DIR = MEMBER_DIR.parent
NET_METHOD_SHA = "578698f8f96a8a1f57712c7f6a0f16e091c7c3a31058486b9ea5fa62cf68dd95"
NET_SHA = "e43cf8217c54e2ad16fbb00ff892009421e0c5a145bbecdd905156b986dae029"
GEOMETRY_SHA = "861b31720b71067df4eeeb7993a86b03e9d85bbcec8b6a585d6e5c0914c52776"
GEOMETRY_PLAN_SHA = "7cfd9d7e6e0f93ab786ad4023436f18a4446e7087d717bc1e7c39456fe0f5390"
STRESS_TEST_SHA = "2e4f337401fe3007e4b0c52faf0f52c17d851ffb9697e1c762e4c83330b573b7"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


net_path = LEAF / "net_enclosure.py"
require(sha(net_path) == NET_METHOD_SHA, "reuse unchanged reviewed area/rectangle method and reference arithmetic")
_spec = importlib.util.spec_from_file_location("frozen_net_reference_for_exact_refinement", net_path)
net = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(net)
pure, box = net.pure, net.box


def cut_key(row, station_key="station_global_grain_projection_mm"):
    return row["member"], row[station_key]


def join46(geometry, request, net_rows):
    """Join via exact requested IDs; only computed plane roundoff is tolerated."""
    require(geometry["schema"] == "thin_bolted_46_selected_net_finished_geometry/v1"
            and geometry["candidate"] == pure.unit.CANDIDATE and geometry["state_id"] is None
            and geometry["selected_cut_count"] == 46 and geometry["cached_finished_BREP_count"] == 5
            and geometry["source_pins_before_after_unchanged"] is True
            and geometry["candidate_response_or_current_field_consumed"] is False
            and geometry["five_existing_exact_sections_requeried"] is False
            and not any(geometry["release"].values()), "reviewed geometry-only 46-cut schema required")
    require(request["schema"] == "thin_bolted_46_selected_net_geometry_query_readiness/v1"
            and request["candidate"] == pure.unit.CANDIDATE and request["state_id"] is None
            and request["request_count"] == 46, "parent-frozen exact query plan required")
    selected = {cut_key(r): r for r in net_rows if r["fully_braced_CD1_normal_reference_enclosure"] > 1}
    planned = {cut_key(r): r for r in request["requests"]}
    measured = {cut_key(r, "requested_station_global_grain_projection_mm"): r for r in geometry["finished_sections"]}
    require(len(selected) == len(planned) == len(measured) == len(request["requests"]) == len(geometry["finished_sections"]) == 46
            and set(selected) == set(planned) == set(measured), "one-to-one same 46 selected/planned/measured cut IDs required")
    for key, row in measured.items():
        properties, plan = row["finished_section_properties"], planned[key]
        require(abs(properties["station_global_grain_projection_mm"] - key[1]) <= 1e-8
                and abs(properties["finished_area_mm2"] - plan["expected_frozen_same_station_area_mm2"]) <= .001
                and properties["expected_frozen_same_station_area_mm2"] == plan["expected_frozen_same_station_area_mm2"]
                and np.linalg.norm(np.asarray(properties["basis_u_v_grain_xyz"]) - plan["basis_u_v_grain_xyz"]) < 1e-8
                and properties["linear_normal_stress"] is None and properties["bores_or_other_voids_restored"] is False
                and properties["shear_area_method_qualified"] is False,
                "own existing plane/area/basis and geometry-only measured section required")
    return {key: row["finished_section_properties"] for key, row in measured.items()}


def read_frozen_packets():
    paths = [LEAF / "net-enclosure.json", LEAF / "selected-net-geometry.json", LEAF / "selected-net-geometry-plan.json",
             MEMBER_DIR / "member-strength.json"]
    digests = [NET_SHA, GEOMETRY_SHA, GEOMETRY_PLAN_SHA, net.MEMBER_RESULT_SHA]
    for path, digest in zip(paths, digests, strict=True):
        require(sha(path) == digest, "exact reviewed reduction/geometry packet required: " + str(path))
    packets = [json.loads(path.read_bytes()) for path in paths]
    return packets, {str(path.relative_to(ROOT)): digest for path, digest in zip(paths, digests, strict=True)}


def plan():
    """Publish immutable pure-reduction scope; do not consume any field actions."""
    require(sha(OWN) == LOADED_SOURCE_SHA, "loaded refinement helper changed")
    (previous, geometry, geometry_plan, _member), pins = read_frozen_packets()
    properties = join46(geometry, geometry_plan, previous["conditional_net_affine_normal_enclosures"])
    pins = net.merge_pins(pins, geometry["source_sha256"], {
        str(OWN.relative_to(ROOT)): LOADED_SOURCE_SHA,
        str(net_path.relative_to(ROOT)): NET_METHOD_SHA,
        str((GATE_DIR / "section-box-v1/test_normal_stress.py").relative_to(ROOT)): STRESS_TEST_SHA,
        str(OWN.with_name("test_refine_normal.py").relative_to(ROOT)): sha(OWN.with_name("test_refine_normal.py"))})
    pure.verify_pins(pins)
    return {"schema": "thin_bolted_46_exact_net_normal_refinement_readiness/v1", "candidate": pure.unit.CANDIDATE,
        "source_sha256": pins, "field_sha256": net.FIELD_SHA, "actual_admission_sha256": net.ADMISSION_SHA,
        "actual_gate_sha256": net.GATE_SHA, "refinement_count": 46,
        "exact_requested_cut_ids": [{"member": key[0], "station_global_grain_projection_mm": key[1]} for key in sorted(properties)],
        "final_expected_census": {"total_full_raw_net_sections": 802, "stronger_existing_exact_findings_reused": 5,
            "new_exact_centroid_coupled_inertia_box_findings": 46, "preserved_conservative_findings_already_below_one": 751},
        "methods_reused": "Unchanged box6bd/c222 coupled-stress coefficients and net578 CD1 reference function/NDSd4e kernel.",
        "existing_stress_fixture_count": 13, "parent_method_readiness_required_before_actual_consume": True,
        "current_field_actions_consumed": False, "CAD_K_global_response_native_or_pressure_query_executed": False}


def consume(field_path, admission_path, plan_path, plan_sha):
    require(sha(OWN) == LOADED_SOURCE_SHA and sha(net_path) == NET_METHOD_SHA
            and importlib.metadata.version("numpy") == "2.5.2", "reviewed loaded method and tools required")
    require(sha(plan_path) == plan_sha, "parent-frozen refinement plan required")
    readiness = json.loads(Path(plan_path).read_bytes())
    require(readiness["schema"] == "thin_bolted_46_exact_net_normal_refinement_readiness/v1"
            and readiness["source_sha256"][str(OWN.relative_to(ROOT))] == LOADED_SOURCE_SHA,
            "same-source pure refinement readiness required")
    payload, admission_payload = Path(field_path).read_bytes(), Path(admission_path).read_bytes()
    require(hashlib.sha256(payload).hexdigest() == net.FIELD_SHA and hashlib.sha256(admission_payload).hexdigest() == net.ADMISSION_SHA,
            "exact current field and actual receipt required")
    admission = json.loads(admission_payload)
    gate = net.load("actual_current_gate_for_exact_net_refinement", GATE_DIR / "admission.py", net.GATE_SHA)
    # Authenticate before any actual same-cut force/couple is read or reduced.
    field, verified = gate.require_admitted_payload(payload, admission, admission_sha256=net.GATE_SHA)
    before, admission_before = pure.references.canonical_sha(field), pure.references.canonical_sha(admission)
    box.member.verify_alias_state_labels(field)
    (previous, geometry, geometry_plan, member), extra = read_frozen_packets()
    for packet in (previous, member):
        require(packet["field_sha256"] == net.FIELD_SHA and all(packet[key] == field[key] for key in pure.IDENTITIES)
                and not any(packet["release"].values()), "only exact admitted same-state prior cut vectors/results allowed")
    properties = join46(geometry, geometry_plan, previous["conditional_net_affine_normal_enclosures"])
    require({(r["member"], r["station_global_grain_projection_mm"]) for r in readiness["exact_requested_cut_ids"]} == set(properties),
            "frozen refinement IDs must match the 46 geometry and conservative selections")
    pins = net.merge_pins(previous["source_sha256"], member["source_sha256"], geometry["source_sha256"], verified,
        readiness["source_sha256"], extra, {str(Path(plan_path).resolve().relative_to(ROOT)): plan_sha,
        str(Path(field_path).resolve().relative_to(ROOT)): net.FIELD_SHA,
        str(Path(admission_path).resolve().relative_to(ROOT)): net.ADMISSION_SHA})
    pure.verify_pins(pins)
    own_wrenches = {cut_key(r): r for r in member["same_cut_rows"] if r["geometry_classification"] == "net_hole_recess_or_service_cut"}
    original_rows = previous["conditional_net_affine_normal_enclosures"]
    require(len(original_rows) == len(own_wrenches) == 802 and {cut_key(r) for r in original_rows} == set(own_wrenches),
            "802 own net cut IDs must stay complete")
    reference = net.nds.adjusted_reference(139.7)
    detailed, summaries = [], []
    for index, row in enumerate(original_rows):
        key = cut_key(row)
        ratio = row["fully_braced_CD1_normal_reference_enclosure"]
        result_method = ("existing_exact_centroid_coupled_inertia_finding_preserved" if row["method"].startswith("stronger_existing")
                         else "conservative_recorded_rectangle_finding_preserved")
        if key in properties:
            prop, wrench = properties[key], own_wrenches[key]["signed_same_cut_wrench"]
            require(abs(prop["finished_area_mm2"] - own_wrenches[key]["finished_area_mm2"]) <= .001,
                    "new exact geometry and existing own wrench section area differ")
            normal = box.section_box_bound(prop, wrench)
            mean = normal["mean_axial_normal_stress_mpa"]
            component_bound = sum(abs(beta) * max(abs(a - center), abs(b - center))
                for beta, (a, b), center in zip(normal["normal_stress_gradient_uv_n_mm3"],
                    [prop["bounds_uv_mm"][axis] for axis in ("u", "v")], prop["centroid_uv_mm"], strict=True))
            refined_ratio = net.reference_enclosure(mean, component_bound, reference)
            detailed.append({"member": key[0], "station_global_grain_projection_mm": key[1],
                "original_conservative_reference_enclosure_upper": ratio,
                "source_exact_geometry_requested_station_key": {"member": key[0], "station_global_grain_projection_mm": key[1]},
                "exact_centroid_coupled_inertia_normal_stress_box_enclosure": normal,
                "sum_of_separate_linear_gradient_component_maxima_upper_mpa": float(component_bound),
                "fully_braced_CD1_normal_reference_enclosure": float(refined_ratio),
                "actual_trimmed_extrema_or_complete_member_strength": None})
            ratio, result_method = float(refined_ratio), "new_exact_centroid_coupled_inertia_box_enclosure"
        elif result_method == "conservative_recorded_rectangle_finding_preserved":
            require(ratio <= 1, "all remaining conservative findings were already bounded below one")
        summaries.append({"member": key[0], "station_global_grain_projection_mm": key[1], "method": result_method,
            "source_original_net_result_row_index_unitless": index,
            "fully_braced_CD1_normal_reference_enclosure": ratio,
            "disposition": "conditional_reference_enclosure_below_one" if ratio <= 1 else "conditional_reference_enclosure_exceeds_one",
            "actual_member_strength_or_acceptance": None})
    require(len(detailed) == 46 and len(summaries) == 802
            and sum(r["method"].startswith("existing_exact") for r in summaries) == 5
            and sum(r["method"].startswith("conservative_recorded") for r in summaries) == 751,
            "final802 must preserve51 exact-property and751 conservative findings")
    pure.verify_pins(pins)
    require(Path(field_path).read_bytes() == payload and Path(admission_path).read_bytes() == admission_payload
            and pure.references.canonical_sha(field) == before and pure.references.canonical_sha(admission) == admission_before,
            "admitted field/receipt changed during refinement")
    return {"schema": "thin_bolted_final802_scoped_affine_normal_dispositions/v1",
        **{key: field[key] for key in pure.IDENTITIES}, "field_sha256": net.FIELD_SHA,
        "source_sha256": pins, "source_pins_before_after_unchanged": True,
        "counts": {"total_full_raw_net_sections": 802, "existing_exact_property_findings_preserved": 5,
            "new_exact_centroid_coupled_inertia_box_findings": 46, "preserved_conservative_findings": 751,
            "final_conditional_reference_enclosures_below_one": sum(r["fully_braced_CD1_normal_reference_enclosure"] <= 1 for r in summaries),
            "final_conditional_reference_enclosures_exceeding_one": sum(r["fully_braced_CD1_normal_reference_enclosure"] > 1 for r in summaries)},
        "final_802_scoped_normal_dispositions": summaries, "46_refined_exact_centroid_inertia_box_findings": detailed,
        "CD1_fully_braced_reference_values": reference,
        "preserved_original_bound_packet": {"path": str((LEAF / "net-enclosure.json").relative_to(ROOT)), "sha256": NET_SHA},
        "largest_preserved_original_conservative_reference_enclosure": max(r["fully_braced_CD1_normal_reference_enclosure"] for r in original_rows),
        "partial_raw_end_sections_terminal_tips_or_continuous_station_maxima_included": False,
        "actual_current_distributed_contact_pressure_bound_established": False,
        "actual_restraint_concentration_fracture_shear_torsion_or_complete_member_strength": None,
        "CAD_K_global_response_new_geometry_or_native_execution": False,
        "release": dict(pure.unit.RELEASE),
        "execution": {"sys_orig_argv": list(sys.orig_argv), "sys_argv": list(sys.argv),
            "python_executable": sys.executable, "python_version": platform.python_version(),
            "numpy_version": importlib.metadata.version("numpy"), "environment": {"PYTHONPATH": os.environ.get("PYTHONPATH")}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-plan", action="store_true")
    parser.add_argument("--field", type=Path)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--plan-sha256")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "distinct normal refinement evidence output required")
    if args.prepare_plan:
        require(args.field is None and args.admission is None, "scope plan reads no field actions")
        result = plan()
    else:
        require(all(v is not None for v in (args.field, args.admission, args.plan, args.plan_sha256)),
                "exact field/actual receipt and parent-frozen readiness plan required")
        result = consume(args.field, args.admission, args.plan, args.plan_sha256)
    args.out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
