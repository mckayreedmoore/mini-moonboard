"""Independent saved final18 numeric review; no consumer, CAD, K or solve."""

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

OWN = Path(__file__).resolve()
LEAF = OWN.parent
PARTIAL = LEAF.parent
PARENT = PARTIAL.parent
ROOT = OWN.parents[6]
FIXED = {
    LEAF / "final-partial-normal-dispositions.json": "888365f5c9e854780968eb5dcbf101c06579beb3e64e98c2cfcc89021be79a4d",
    LEAF / "refine_one_normal.py": "0191dea2b2f62beb5f7480eb15228bddf3d7c8899b7cd2a35ef509bcf8fd6314",
    LEAF / "test_refine_one_normal.py": "3b8051d97fa39fe4c38548aab9f88918a4a0b82f48649e804837b3481e80bf1d",
    LEAF / "one-normal-plan.json": "781a74cc24e5882063772dd8ac5cf8245ee3764a8fc34f741f0bdf20d9c18c9f",
    LEAF / "one-section-geometry.json": "0490950906f1147cade510861178b0cc936552b98eb4185404c05694f224c188",
    PARTIAL / "partial-end-findings.json": "2f3954f45aae53789ef67095adda5af4b9d3d6f41d317b149b1d04aab6a94a7c",
    PARENT / "member-strength-v1/member-strength.json": "6f362bdb7e4b2321f37a644ecc2d5b913e73b286937483f5ae8e16d5fe9ba708",
    PARENT / "member-strength-v1/net-enclosure-v1/final-normal-dispositions.json": "2b58f158f8fd8dcc0906060c918b591ce3e71b72056ae91e670f3b1a505ed913",
    PARENT / "a12-rear.json": "29b25f11794a171a1364268ed676a24cee2882e47c3018b3648267d2707a0ddf",
    PARENT / "admission.json": "e5bbf8c0ad2947f42f71819d61b03fcd260a0926b5f5429481e5523ff8e122a5",
    PARENT / "admission.py": "4b78722ab407a39d6e00fc9e16be0d370d0c837dea5880e45e7a2e277dd6efb6",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def key(row):
    return row["member"], row["station_global_grain_projection_mm"]


def review():
    assert all(sha(p) == s for p, s in FIXED.items())
    out = json.loads((LEAF / "final-partial-normal-dispositions.json").read_bytes())
    plan = json.loads((LEAF / "one-normal-plan.json").read_bytes())
    pins = out["source_sha256"]
    assert len(pins) == 394 and len(plan["source_sha256"]) == 96
    assert all(pins[p] == s for p, s in plan["source_sha256"].items())
    assert all(sha(ROOT / p) == s for p, s in pins.items())
    spec = importlib.util.spec_from_file_location("independent_final_partial_actual_gate", PARENT / "admission.py")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    payload = (PARENT / "a12-rear.json").read_bytes()
    admission = json.loads((PARENT / "admission.json").read_bytes())
    field, _ = gate.require_admitted_payload(payload, admission, admission_sha256=FIXED[PARENT / "admission.py"])
    assert canonical(field) == "33d7dbf5033ac5e3715277e7af51e2747a082c657df2081e4e38a5d6d10155a9"
    q_sha = canonical(field["response"]["q"])
    assert q_sha == admission["original_gradient_checks"]["final_q_canonical_sha256"] == "2c13826c3c6061fd327470f7ed7e7f80dfd7c50283a732cef0b353d72107e342"
    coarse = json.loads((PARTIAL / "partial-end-findings.json").read_bytes())
    geometry = json.loads((LEAF / "one-section-geometry.json").read_bytes())
    member = json.loads((PARENT / "member-strength-v1/member-strength.json").read_bytes())
    for name in ("state_id", "case_id", "accessory_placement"):
        assert out[name] == coarse[name] == member[name] == field[name]
    assert out["field_sha256"] == coarse["field_sha256"] == member["field_sha256"] == FIXED[PARENT / "a12-rear.json"]
    old, final = coarse["18_conditional_partial_end_findings"], out["final_18_scoped_partial_normal_dispositions"]
    assert len(old) == len(final) == 18 and len({key(r) for r in old}) == 18
    one = out["one_refined_exact_centroid_inertia_box_finding"]
    assert key(one) == ("lumber_leg_left", -374.9922284)
    source = next(r for r in old if key(r) == key(one))
    original_member = next(r for r in member["same_cut_rows"] if key(r) == key(one))
    normal = one["exact_centroid_coupled_inertia_normal_stress_box_enclosure"]
    prop = geometry["finished_sections"][0]
    assert geometry["state_id"] is None and prop["state_id"] is None and prop["linear_normal_stress"] is None
    assert one["original_conservative_reference_enclosure_upper"] == source["fully_braced_CD1_normal_reference_enclosure"] == 2.2056877935772574
    assert normal["signed_same_cut_wrench"] == source["signed_same_cut_wrench"] == original_member["signed_same_cut_wrench"]
    assert one["preserved_necessary_average_resultant_shear_over_CD1_Fv"] == source["necessary_average_resultant_shear_over_CD1_Fv"] == 0.1324300663759149
    assert normal["reference_finished_centroid_xyz_mm"] == prop["centroid_xyz_mm"]
    assert normal["finished_net_area_mm2"] == prop["finished_area_mm2"] == 3548.380002196744
    B = np.array(prop["basis_u_v_grain_xyz"])
    center = np.array(prop["centroid_xyz_mm"])
    wrench = source["signed_same_cut_wrench"]
    force = np.array(wrench["force_on_lower_portion_xyz_n"])
    moment = np.array(wrench["moment_on_lower_portion_about_cut_xyz_nmm"]) - np.cross(center - wrench["cut_point_xyz_mm"], force)
    local_moment = B @ moment
    N = float(B[2] @ force)
    covariance = np.array(prop["centroidal_area_moment_matrix_uv_mm4"])
    assert np.linalg.eigvalsh(covariance).min() > 0 and np.linalg.det(B) > 0
    a, b, d = covariance[0, 0], covariance[0, 1], covariance[1, 1]
    det = a * d - b * b
    beta = np.array([(-d * local_moment[1] - b * local_moment[0]) / det, (b * local_moment[1] + a * local_moment[0]) / det])
    mean = N / prop["finished_area_mm2"]
    uv_center = np.array(prop["centroid_uv_mm"])
    bounds = np.array([prop["bounds_uv_mm"][axis] for axis in ("u", "v")])
    corners = [(np.array([u, v]), float(mean + beta @ (np.array([u, v]) - uv_center))) for u in bounds[0] for v in bounds[1]]
    bending = sum(abs(x) * max(abs(lo - c), abs(hi - c)) for x, (lo, hi), c in zip(beta, bounds, uv_center, strict=True))
    refs = out["CD1_fully_braced_reference_values"]
    assert refs == coarse["CD1_fully_braced_reference_values"]
    ratio = (max(-mean, 0.) / refs["Fc_star_mpa"])**2 + bending / refs["Fb_star_mpa"] if mean < 0 else max(mean, 0.) / refs["Ft_mpa"] + bending / refs["Fb_star_mpa"]
    errors = {"centroid_transport_Nmm": float(np.max(abs(moment - normal["moment_about_reference_finished_centroid_xyz_nmm"]))),
        "mean_normal_MPa": abs(mean - normal["mean_axial_normal_stress_mpa"]),
        "gradient_N_mm3": float(np.max(abs(beta - normal["normal_stress_gradient_uv_n_mm3"]))),
        "separate_component_bending_MPa": abs(bending - one["sum_of_separate_linear_gradient_component_maxima_upper_mpa"]),
        "reference_ratio": abs(ratio - one["fully_braced_CD1_normal_reference_enclosure"]), "corner_stress_MPa": 0., "corner_point_mm": 0.}
    for label, select in (("minimum_signed_normal_stress_box_witness", min), ("maximum_signed_normal_stress_box_witness", max)):
        uv, stress = select(corners, key=lambda r: r[1])
        recorded = normal[label]
        assert recorded["box_corner_uv_mm"] == uv.tolist() and recorded["actual_material_occupancy_at_corner_verified"] is False
        errors["corner_stress_MPa"] = max(errors["corner_stress_MPa"], abs(stress - recorded["signed_linear_normal_stress_mpa"]))
        xyz = np.array(prop["section_origin_xyz_mm"]) + B[:2].T @ uv
        errors["corner_point_mm"] = max(errors["corner_point_mm"], float(np.linalg.norm(xyz - recorded["reference_box_corner_xyz_mm"])))
    assert all(v < 1e-8 for v in errors.values()) and ratio <= 1
    preserved = 0
    for index, (before, after) in enumerate(zip(old, final, strict=True)):
        assert key(before) == key(after) and after["source_original_partial_result_row_index_unitless"] == index
        assert after["actual_partial_end_member_strength_or_acceptance"] is None
        if key(before) == key(one):
            assert after["fully_braced_CD1_normal_reference_enclosure"] == one["fully_braced_CD1_normal_reference_enclosure"] == 0.015030426102610987
            assert after["method"] == "new_exact_centroid_coupled_inertia_box_enclosure"
        else:
            preserved += 1
            assert after["fully_braced_CD1_normal_reference_enclosure"] == before["fully_braced_CD1_normal_reference_enclosure"]
            assert after["method"] == "original_conservative_finding_preserved"
        assert after["fully_braced_CD1_normal_reference_enclosure"] <= 1 and after["disposition"] == "conditional_reference_enclosure_below_one"
    warnings = [{"member": r["member"], "station_global_grain_projection_mm": r["station_global_grain_projection_mm"], "reference_header_bearing_patch_id": r["reference_header_bearing_patch_id"]} for r in old if r["reference_header_bearing_patch_overlaps_cut"]]
    assert len(warnings) == 12 and source["reference_header_bearing_patch_overlaps_cut"] is False
    assert out["twelve_header_bearing_overlap_dispositions_preserved"] is True
    assert preserved == 17 and out["counts"] == {"partial_end_sections": 18, "preserved_coarse_findings": 17, "new_exact_property_box_findings": 1, "conditional_normal_bounds_below_one": 18, "conditional_normal_bounds_exceeding_one": 0}
    maximum = max(final, key=lambda r: r["fully_braced_CD1_normal_reference_enclosure"])
    assert key(maximum) == ("lumber_leg_right", -374.9922284) and maximum["fully_braced_CD1_normal_reference_enclosure"] == 0.6209432333482396
    assert out["preserved_coarse_packet"] == {"path": str((PARTIAL / "partial-end-findings.json").relative_to(ROOT)), "sha256": FIXED[PARTIAL / "partial-end-findings.json"]}
    assert len(member["excluded_terminal_sections"]) == 4
    assert out["tips_802_nets_226_rectangles_or_shear_findings_recomputed"] is False
    assert out["actual_current_distributed_contact_pressure_bound_established"] is False
    assert out["complete_end_wrench_concentration_fracture_shear_torsion_stability_or_member_strength"] is None
    assert one["actual_end_traction_contact_concentration_fracture_shear_torsion_stability_or_member_strength"] is None
    assert normal["finite_current_pose_or_occupied_corner_claimed"] is False
    assert all(normal[n] is None for n in ("actual_trimmed_directional_stress_extrema", "NDS_component_ratio_or_complete_member_resistance", "shear_torsion_fracture_buckling_stability"))
    assert not any(out["release"].values())
    argv = [".venv/bin/python", "-m", "fea.generated.thin-bolted-direct-contact-a12-v1.observer-isolation-v2.partial-end-development-v1.refinement-v1.refine_one_normal", "--field", str((PARENT / "a12-rear.json").relative_to(ROOT)), "--admission", str((PARENT / "admission.json").relative_to(ROOT)), "--plan", str((LEAF / "one-normal-plan.json").relative_to(ROOT)), "--plan-sha256", FIXED[LEAF / "one-normal-plan.json"], "--out", str((LEAF / "final-partial-normal-dispositions.json").relative_to(ROOT))]
    assert out["execution"]["sys_orig_argv"] == argv and out["execution"]["environment"]["MINI_MOONBOARD_PARENT_MEMBER_EXECUTION"] == "1"
    assert all(sha(ROOT / p) == s for p, s in pins.items()) and all(sha(p) == s for p, s in FIXED.items())
    return {"schema": "thin_bolted_independent_final18_partial_normal_numeric_review/v1", "disposition": "PASS_WITHIN_RECORDED_SCOPE",
        "reviewer_source_sha256": sha(OWN), "production_bytes": 61341, "direct_input_sha256": {str(p.relative_to(ROOT)): s for p, s in FIXED.items()},
        "plan_pin_count": 96, "production_pin_count": 394, "production_source_map_canonical_sha256": canonical(pins), "pins_before_after_unchanged": True,
        "state_id": out["state_id"], "field_canonical_sha256": canonical(field), "q_canonical_sha256": q_sha,
        "hand_replay_max_errors": errors, "hand_refined_cut": {"member": key(one)[0], "station_mm": key(one)[1], "axial_tension_positive_N": N,
            "centroid_moment_world_Nmm": moment.tolist(), "normal_mean_MPa": mean, "normal_gradient_uv_N_mm3": beta.tolist(),
            "component_bending_bound_MPa": float(bending), "conditional_CD1_fully_braced_ratio": float(ratio)},
        "counts": out["counts"], "preserved_other_findings": 17, "original_conservative_upper_bound_preserved": 2.2056877935772574,
        "maximum_final_witness": {k: maximum[k] for k in ("member", "station_global_grain_projection_mm", "fully_braced_CD1_normal_reference_enclosure")},
        "unchanged_reference_header_overlap_warnings": warnings,
        "limits": ["All18 conditional affine normal enclosures are below one; this does not establish complete partial-end resistance.", "Twelve header-bearing overlaps remain load-introduction/pressure warnings, with end traction/concentration/fracture/shear/torsion/stability unqualified.", "17 ratios/source indices and original loose2.2056877935772574 remain exact; fourtips and802/226 previous results remain unchanged.", "Current linear-field physical applicability remains unqualified; actual box-corner occupancy is not claimed."],
        "reviewer_consumer_CAD_pose_query_K_global_native_or_pressure_execution": False, "release": out["release"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists()
    checked = review()
    checked["review_execution"] = {"actual_orig_argv": list(sys.orig_argv), "actual_sys_argv": list(sys.argv), "cwd": str(Path.cwd()),
        "environment": {k: os.environ.get(k) for k in ("PYTHONPATH", "OPENBLAS_NUM_THREADS")}, "tool_versions": {"python": platform.python_version(), "numpy": importlib.metadata.version("numpy")}}
    with args.out.open("x") as stream:
        stream.write(json.dumps(checked, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "bytes": args.out.stat().st_size, "sha256": sha(args.out)}))
