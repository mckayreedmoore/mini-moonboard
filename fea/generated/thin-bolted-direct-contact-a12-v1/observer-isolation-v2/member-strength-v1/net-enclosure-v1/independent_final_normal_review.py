"""Independent saved same-cut arithmetic and provenance review; no solve/query."""

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
MEMBER = LEAF.parent
PARENT = MEMBER.parent
ROOT = OWN.parents[6]
FIXED = {
    LEAF / "final-normal-dispositions.json": "2b58f158f8fd8dcc0906060c918b591ce3e71b72056ae91e670f3b1a505ed913",
    LEAF / "refine_normal.py": "c59b9ecb3f34df7d396bb97ab99f71139bb81f9ee7d35f7457f6dcec129009eb",
    LEAF / "test_refine_normal.py": "d6f45d771187b87c25845ec9b444712d539ce5cfc91adcd931553cc2e9984485",
    LEAF / "normal-refinement-plan.json": "906d74545c4a4df6cb4636ad346107608b771fa7abb7188e5f26aac9478e68bb",
    LEAF / "net-enclosure.json": "e43cf8217c54e2ad16fbb00ff892009421e0c5a145bbecdd905156b986dae029",
    LEAF / "selected-net-geometry.json": "861b31720b71067df4eeeb7993a86b03e9d85bbcec8b6a585d6e5c0914c52776",
    MEMBER / "member-strength.json": "6f362bdb7e4b2321f37a644ecc2d5b913e73b286937483f5ae8e16d5fe9ba708",
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
    assert all(sha(path) == digest for path, digest in FIXED.items())
    out = json.loads((LEAF / "final-normal-dispositions.json").read_bytes())
    plan = json.loads((LEAF / "normal-refinement-plan.json").read_bytes())
    pins = out["source_sha256"]
    assert len(pins) == 387 and len(plan["source_sha256"]) == 25
    assert all(pins[path] == digest and sha(ROOT / path) == digest for path, digest in plan["source_sha256"].items())
    assert all(sha(ROOT / path) == digest for path, digest in pins.items())
    spec = importlib.util.spec_from_file_location("independent_final_normal_actual_gate", PARENT / "admission.py")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    payload = (PARENT / "a12-rear.json").read_bytes()
    admission = json.loads((PARENT / "admission.json").read_bytes())
    field, _ = gate.require_admitted_payload(payload, admission, admission_sha256=FIXED[PARENT / "admission.py"])
    assert out["field_sha256"] == FIXED[PARENT / "a12-rear.json"]
    assert canonical(field) == "33d7dbf5033ac5e3715277e7af51e2747a082c657df2081e4e38a5d6d10155a9"
    q_sha = canonical(field["response"]["q"])
    assert q_sha == admission["original_gradient_checks"]["final_q_canonical_sha256"] == "2c13826c3c6061fd327470f7ed7e7f80dfd7c50283a732cef0b353d72107e342"
    for name in ("state_id", "case_id", "accessory_placement"):
        assert out[name] == field[name]
    old = json.loads((LEAF / "net-enclosure.json").read_bytes())
    member = json.loads((MEMBER / "member-strength.json").read_bytes())
    geometry = json.loads((LEAF / "selected-net-geometry.json").read_bytes())
    previous = old["conditional_net_affine_normal_enclosures"]
    current = out["final_802_scoped_normal_dispositions"]
    detailed = out["46_refined_exact_centroid_inertia_box_findings"]
    measured = {(r["member"], r["requested_station_global_grain_projection_mm"]): r["finished_section_properties"] for r in geometry["finished_sections"]}
    vectors = {key(r): r for r in member["same_cut_rows"] if r["geometry_classification"] == "net_hole_recess_or_service_cut"}
    refined = {key(r): r for r in detailed}
    assert len(previous) == len(current) == len(vectors) == 802
    assert len(refined) == len(measured) == len(detailed) == 46 and set(refined) == set(measured)
    assert set(refined) == {key(r) for r in plan["exact_requested_cut_ids"]}
    assert {key(r) for r in previous} == {key(r) for r in current} == set(vectors)
    reference = out["CD1_fully_braced_reference_values"]
    assert reference == old["CD1_reference_values"]
    errors = {"moment_Nmm": 0., "mean_MPa": 0., "gradient_N_mm3": 0., "corner_stress_MPa": 0., "corner_point_mm": 0., "separate_bending_MPa": 0., "reference_ratio": 0.}
    kinds = {"new_exact": 0, "old_exact": 0, "coarse": 0}
    for index, (before, final) in enumerate(zip(previous, current, strict=True)):
        cut = key(before)
        assert key(final) == cut and final["source_original_net_result_row_index_unitless"] == index
        assert final["actual_member_strength_or_acceptance"] is None
        if cut in refined:
            kinds["new_exact"] += 1
            row, prop = refined[cut], measured[cut]
            normal = row["exact_centroid_coupled_inertia_normal_stress_box_enclosure"]
            wrench = vectors[cut]["signed_same_cut_wrench"]
            assert normal["signed_same_cut_wrench"] == wrench == before["signed_same_cut_wrench"]
            assert row["original_conservative_reference_enclosure_upper"] == before["fully_braced_CD1_normal_reference_enclosure"]
            assert row["source_exact_geometry_requested_station_key"] == {"member": cut[0], "station_global_grain_projection_mm": cut[1]}
            B = np.array(prop["basis_u_v_grain_xyz"])
            centroid = np.array(prop["centroid_xyz_mm"])
            force = np.array(wrench["force_on_lower_portion_xyz_n"])
            moment = np.array(wrench["moment_on_lower_portion_about_cut_xyz_nmm"]) - np.cross(centroid - wrench["cut_point_xyz_mm"], force)
            local_moment = B @ moment
            N = B[2] @ force
            A = prop["finished_area_mm2"]
            covariance = np.array(prop["centroidal_area_moment_matrix_uv_mm4"])
            assert np.linalg.eigvalsh(covariance)[0] > 0
            a, b, d = covariance[0, 0], covariance[0, 1], covariance[1, 1]
            determinant = a * d - b * b
            beta = np.array([(-d * local_moment[1] - b * local_moment[0]) / determinant, (b * local_moment[1] + a * local_moment[0]) / determinant])
            mean = N / A
            center_uv = np.array(prop["centroid_uv_mm"])
            bounds = np.array([prop["bounds_uv_mm"][axis] for axis in ("u", "v")])
            corners = [(np.array([u, v]), float(mean + beta @ (np.array([u, v]) - center_uv))) for u in bounds[0] for v in bounds[1]]
            component = sum(abs(value) * max(abs(low - center), abs(high - center)) for value, (low, high), center in zip(beta, bounds, center_uv, strict=True))
            ratio = ((max(-mean, 0.) / reference["Fc_star_mpa"]) ** 2 + component / reference["Fb_star_mpa"] if mean < 0 else max(mean, 0.) / reference["Ft_mpa"] + component / reference["Fb_star_mpa"])
            errors["moment_Nmm"] = max(errors["moment_Nmm"], float(np.max(abs(moment - normal["moment_about_reference_finished_centroid_xyz_nmm"]))))
            errors["mean_MPa"] = max(errors["mean_MPa"], abs(mean - normal["mean_axial_normal_stress_mpa"]))
            errors["gradient_N_mm3"] = max(errors["gradient_N_mm3"], float(np.max(abs(beta - normal["normal_stress_gradient_uv_n_mm3"]))))
            for name, selector in (("minimum_signed_normal_stress_box_witness", min), ("maximum_signed_normal_stress_box_witness", max)):
                uv, stress = selector(corners, key=lambda item: item[1])
                saved = normal[name]
                assert saved["box_corner_uv_mm"] == uv.tolist() and saved["actual_material_occupancy_at_corner_verified"] is False
                errors["corner_stress_MPa"] = max(errors["corner_stress_MPa"], abs(stress - saved["signed_linear_normal_stress_mpa"]))
                xyz = np.array(prop["section_origin_xyz_mm"]) + B[:2].T @ uv
                errors["corner_point_mm"] = max(errors["corner_point_mm"], float(np.linalg.norm(xyz - saved["reference_box_corner_xyz_mm"])))
            errors["separate_bending_MPa"] = max(errors["separate_bending_MPa"], abs(component - row["sum_of_separate_linear_gradient_component_maxima_upper_mpa"]))
            errors["reference_ratio"] = max(errors["reference_ratio"], abs(ratio - row["fully_braced_CD1_normal_reference_enclosure"]))
            assert final["fully_braced_CD1_normal_reference_enclosure"] == row["fully_braced_CD1_normal_reference_enclosure"] and final["method"] == "new_exact_centroid_coupled_inertia_box_enclosure"
            assert normal["reference_finished_centroid_xyz_mm"] == prop["centroid_xyz_mm"] and normal["finished_net_area_mm2"] == A
            assert normal["finite_current_pose_or_occupied_corner_claimed"] is False
            for name in ("actual_trimmed_directional_stress_extrema", "NDS_component_ratio_or_complete_member_resistance", "shear_torsion_fracture_buckling_stability"):
                assert normal[name] is None
            assert row["actual_trimmed_extrema_or_complete_member_strength"] is None
        else:
            assert final["fully_braced_CD1_normal_reference_enclosure"] == before["fully_braced_CD1_normal_reference_enclosure"]
            if before["method"].startswith("stronger_existing"):
                kinds["old_exact"] += 1
                assert final["method"] == "existing_exact_centroid_coupled_inertia_finding_preserved"
            else:
                kinds["coarse"] += 1
                assert final["method"] == "conservative_recorded_rectangle_finding_preserved"
        assert final["fully_braced_CD1_normal_reference_enclosure"] <= 1 and final["disposition"] == "conditional_reference_enclosure_below_one"
    assert kinds == {"new_exact": 46, "old_exact": 5, "coarse": 751}
    assert all(value < 1e-8 for value in errors.values())
    assert out["counts"] == {"total_full_raw_net_sections": 802, "existing_exact_property_findings_preserved": 5, "new_exact_centroid_coupled_inertia_box_findings": 46, "preserved_conservative_findings": 751, "final_conditional_reference_enclosures_below_one": 802, "final_conditional_reference_enclosures_exceeding_one": 0}
    assert out["largest_preserved_original_conservative_reference_enclosure"] == max(r["fully_braced_CD1_normal_reference_enclosure"] for r in previous) == 9.804070532148222
    assert not any(out["release"].values()) and out["actual_current_distributed_contact_pressure_bound_established"] is False
    assert out["actual_restraint_concentration_fracture_shear_torsion_or_complete_member_strength"] is None and out["partial_raw_end_sections_terminal_tips_or_continuous_station_maxima_included"] is False
    argv = [".venv/bin/python", "-m", "fea.generated.thin-bolted-direct-contact-a12-v1.observer-isolation-v2.member-strength-v1.net-enclosure-v1.refine_normal", "--field", str((PARENT / "a12-rear.json").relative_to(ROOT)), "--admission", str((PARENT / "admission.json").relative_to(ROOT)), "--plan", str((LEAF / "normal-refinement-plan.json").relative_to(ROOT)), "--plan-sha256", FIXED[LEAF / "normal-refinement-plan.json"], "--out", str((LEAF / "final-normal-dispositions.json").relative_to(ROOT))]
    assert out["execution"]["sys_orig_argv"] == argv
    assert all(sha(ROOT / path) == digest for path, digest in pins.items()) and all(sha(path) == digest for path, digest in FIXED.items())
    maximum = max(current, key=lambda row: row["fully_braced_CD1_normal_reference_enclosure"])
    maximum_refined = max(detailed, key=lambda row: row["fully_braced_CD1_normal_reference_enclosure"])
    return {"schema": "thin_bolted_independent_final802_affine_normal_numeric_review/v1", "disposition": "PASS_WITHIN_RECORDED_SCOPE", "reviewer_source_sha256": sha(OWN), "direct_input_sha256": {str(path.relative_to(ROOT)): digest for path, digest in FIXED.items()}, "production_bytes": (LEAF / "final-normal-dispositions.json").stat().st_size, "production_union_pin_count": 387, "readiness_pin_count": 25, "production_source_map_canonical_sha256": canonical(pins), "pins_before_after_unchanged": True, "state_id": out["state_id"], "q_canonical_sha256": q_sha, "field_canonical_sha256": canonical(field), "all46_hand_replay_max_errors": errors, "all802_counts": out["counts"], "preserved_source_row_count": 756, "largest_original_conservative_upper_bound_preserved": 9.804070532148222, "maximum_final_reference_witness": maximum, "maximum_new_exact_reference_witness": {name: maximum_refined[name] for name in ("member", "station_global_grain_projection_mm", "fully_braced_CD1_normal_reference_enclosure")}, "limits": ["All802 conditional affine normal component enclosures below one; no actual strength, pressure, stability, shear/torsion or fracture acceptance.", "51 exact-property box findings and751 preserved conservative findings; actual box-corner occupancy is unverified.", "18 partial raw ends,4 separate terminals and continuous station maxima remain excluded; current field physical applicability remains unqualified."], "new_CAD_query_q_projection_K_global_native_or_pressure_execution": False, "release": out["release"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists()
    result = review()
    result["review_execution"] = {"actual_orig_argv": list(sys.orig_argv), "actual_sys_argv": list(sys.argv), "cwd": str(Path.cwd()), "environment": {name: os.environ.get(name) for name in ("PYTHONPATH", "OPENBLAS_NUM_THREADS")}, "tool_versions": {"python": platform.python_version(), "numpy": importlib.metadata.version("numpy")}}
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "bytes": args.out.stat().st_size, "sha256": sha(args.out)}))
