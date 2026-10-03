"""Recompute frozen timber references for a declared cumulative peak duration.

Parent executes this finite saved-cut calculation. No frame response, stiffness,
section geometry, floor law, screw capacity or physical-release flag changes.
The permanent-load comparison remains a separate required calculation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = PACKET.parents[3]
SOURCE = PACKET / "member-stability-attempt01/four-screw-layout01"
GEOMETRY = PACKET / "member-screen-attempt02/four-screw-layout01/geometry.json"
RAW = HERE / "rawlocal/member-duration"
CD = 1.25
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    SOURCE / "checks.json": "aceebc0beaee1cc178450b52b2a16a32924803c3210dc0c115c0fee7a3a7c574",
    SOURCE / "same-cut-states.csv": "dd7b437a32f3e0f1c7b06d1dd743644f643c6abeb67d6a2a97fc67f79faf91c1",
    GEOMETRY: "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    HERE / "frame-250-attempt02/comparison.json": "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    HERE / "frame-250-attempt02/response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    PACKET / "member_stability.py": "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    PACKET / "member_screen.py": "5ecbfcebc8ea45bba83961305735f919d5e6caa3862625befec875655dd0b5d9",
    PACKET / "bottom_corner_checks.py": "5df7a264354e1488c2a68332820fe927e8dcb1fa9721111ec8fac5c00ad19e26",
    PACKET / "frame_state_contract.py": "22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5",
    ROOT / "fea/reinforced_timber_resistance.py": "d4e8302d39beb9f53c70fa264762c59c231f6e6b086cb866906ca39eeab9cfbc",
    ROOT / "scripts/floor_taper_checks.py": "bf15d8983b42d95dda0d0329bc2d8c2664f9c146813f21e1a0cc8f0f6a3bf1c3",
    PACKET.parent / "upper-block-strength-2026-10-01/source-cache/chapter2-2024-awc.pdf": "6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100",
}
PRIMARY = {
    "url": "https://web-media.awc.org/wp-content/uploads/2021/12/17210153/AWC_NDS2024_20231129_AWCWebsite_Chapter2.pdf",
    "edition": "2024 NDS", "clauses": ["2.3.2.1", "2.3.2.2", "2.3.2.3", "Table 2.3.2"],
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def authenticate():
    for path, expected in PINS.items():
        require(sha(path) == expected, f"changed frozen source: {path}")


def load_helper():
    sys.path[:0] = [str(PACKET), str(ROOT)]
    spec = importlib.util.spec_from_file_location("duration_member_stability", PACKET / "member_stability.py")
    require(spec is not None and spec.loader is not None, "stability import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def same(actual, prior, label):
    if prior in (None, ""):
        require(actual is None, "missing baseline changed: " + label)
        return 0.0
    delta = abs(actual - float(prior))
    require(delta <= 1e-10 * max(1.0, abs(float(prior))), "baseline reproduction failed: " + label)
    return delta


def peak(rows, key):
    applicable = [row for row in rows if row[key] is not None]
    return max(applicable, key=lambda row: row[key]) if applicable else None


def build(output):
    authenticate()
    require(RAW.resolve() in output.resolve().parents and not output.exists(), "use a fresh owned output child")
    output.mkdir(parents=True)
    method = load_helper()
    source = json.loads((SOURCE / "checks.json").read_text())
    geometry = json.loads(GEOMETRY.read_text())["members"]
    source_members = {record["member"]: record for record in source["members"]}
    require(set(source_members) == set(geometry) and len(source_members) == 44, "member census changed")
    kernels, references, orientation = {}, {}, {}
    baseline_error = 0.0
    for body, record in source_members.items():
        base = record["references"]
        adjusted = {key: value * CD if key in ("Fb_star_mpa", "Ft_mpa", "Fc_star_mpa", "Fv_mpa") else value
                    for key, value in base.items()}
        references[body] = {"cd1": base, "cd1_25": adjusted}
        require(adjusted["Emin_mpa"] == base["Emin_mpa"] and adjusted["Fc_perp_mpa"] == base["Fc_perp_mpa"], "duration changed excluded references")
        short, long = record["minimum_intact_rectangle_short_long_mm"]
        length = record["length_mm"]
        kernels[body] = {}
        for name, weak in (("end_supported_only", length), ("existing_timber_weak_restraints", record["maximum_candidate_weak_bay_mm"])):
            old = method.stability_kernel(short, long, length, weak, base)
            prior = record["stability_kernels"][name]
            for key in ("Cp", "CL", "adjusted_Fc_mpa", "adjusted_Fb_strong_mpa"):
                baseline_error = max(baseline_error, same(old[key], prior[key], body + "/" + name + "/" + key))
            new = method.stability_kernel(short, long, length, weak, adjusted)
            require(new["FcE_strong_weak_mpa"] == old["FcE_strong_weak_mpa"] and new["FbE_mpa"] == old["FbE_mpa"], "duration changed Euler references")
            kernels[body][name] = {"cd1": old, "cd1_25": new}
        basis = method.member.basis(geometry[body]["geometry"])
        axes = record["frozen_elastic_orientation"]["material_axes_global_xyz"]
        require(np.max(abs(np.array(axes["L"]) - basis[0])) < 1e-8, "grain frame changed")
        ru, rv = abs(float(np.array(axes["R"]) @ basis[1])), abs(float(np.array(axes["R"]) @ basis[2]))
        orientation[body] = (max(ru, rv) > 1 - 1e-7, .064 / .078 if ru > rv else .078 / .064)
    with (SOURCE / "same-cut-states.csv").open() as stream:
        all_rows = list(csv.DictReader(stream))
    records, excluded = [], Counter()
    for old in all_rows:
        if not old["section_status"].startswith("BORE_FREE_"):
            excluded[old["section_status"]] += 1
            continue
        body = old["member"]
        base, adjusted = references[body]["cd1"], references[body]["cd1_25"]
        width, depth = float(old["width_mm"]), float(old["depth_mm"])
        value = [float(old[key]) for key in ("N_n", "Vu_n", "Vv_n", "T_nmm", "Mu_nmm", "Mv_nmm")]
        row = dict(old)
        for name, prefix in (("end_supported_only", "end_only"), ("existing_timber_weak_restraints", "timber_braced")):
            original = method.normal_check(value, width, depth, kernels[body][name]["cd1"], base)
            baseline_error = max(baseline_error, same(original["interaction_ratio"], old[prefix + "_normal_ratio"], body + "/normal"))
            require(original["within_slenderness_limits"] == (old[prefix + "_slenderness_ok"] == "True"), "baseline stability domain changed")
            new = method.normal_check(value, width, depth, kernels[body][name]["cd1_25"], adjusted)
            require(new["within_slenderness_limits"] == original["within_slenderness_limits"], "duration changed slenderness")
            row[prefix + "_normal_ratio_cd1_25"] = new["interaction_ratio"]
            row[prefix + "_qualified_domain_cd1_25"] = new["ratio_qualified_inside_declared_stability_domain"]
            row[prefix + "_checked_exceedance_cd1_25"] = new["ratio_exceeds_one"]
            if prefix == "timber_braced":
                baseline_error = max(baseline_error, same(original["stability_3_9_4_ratio"], old["timber_braced_stability_3_9_4"], body + "/3.9.4"))
                require(new["stability_3_9_4_ratio"] == original["stability_3_9_4_ratio"], "duration changed Euler demand")
        shear = method.shear_check(value, width, depth, base["Fv_mpa"], *orientation[body])
        for old_key, helper_key in (("shear_face_ratio", "face_lower_bound_ratio"), ("shear_component_bound_ratio", "component_rectangle_upper_bound_ratio"), ("coefficient5_sensitivity_ratio", "coefficient5_isotropic_sensitivity_ratio")):
            baseline_error = max(baseline_error, same(shear[helper_key], old[old_key], body + "/" + old_key))
            row[old_key + "_cd1_25"] = shear[helper_key] / CD
        row["shear_allowance_cd1_25_mpa"] = adjusted["Fv_mpa"]
        records.append(row)
    require(len(all_rows) == 55176 and len(records) == 34704, "cut census changed")
    require({r["case_id"] for r in records} == set(CASES), "six-case census changed")
    columns = ("end_only_normal_ratio_cd1_25", "timber_braced_normal_ratio_cd1_25", "shear_face_ratio_cd1_25", "shear_component_bound_ratio_cd1_25", "coefficient5_sensitivity_ratio_cd1_25")
    with (output / "same-cut-states.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    result = {
        "schema": "conditional_member_duration_comparison/v1",
        "status": "COMPLETED_SAVED_CUT_COMPARISON",
        "producer_sha256": sha(Path(__file__)),
        "source_sha256": {str(p.relative_to(ROOT)): digest for p, digest in PINS.items()},
        "primary_basis": PRIMARY,
        "load_hypothesis": {"wood_strength_CD": CD, "cumulative_full_peak_load_days_max": 7,
                            "original_250_lb_times_2_and_signed_300_N_and_100_mm_lever": True,
                            "permanent_load_CD": .9, "permanent_load_check_included": False,
                            "force_or_elastic_or_hardware_multiplier": 1.0,
                            "duration_adoption_complete": False},
        "counts": {"members": 44, "cases": 6, "source_traces": len(all_rows), "applicable_traces": len(records), "excluded_by_status": dict(excluded)},
        "baseline_max_absolute_reproduction_error": baseline_error,
        "global_peaks": {key: peak(records, key) for key in columns},
        "per_case_peaks": {case: {key: peak([r for r in records if r["case_id"] == case], key) for key in columns} for case in CASES},
        "members": {body: {"references": references[body], "kernels": kernels[body]} for body in source_members},
        "unqualified_timber_braced_trace_count": sum(not r["timber_braced_qualified_domain_cd1_25"] for r in records),
        "timber_braced_checked_exceedance_count": sum(r["timber_braced_checked_exceedance_cd1_25"] for r in records),
        "all_sampled_component_bounds_below_one": all(r["shear_component_bound_ratio_cd1_25"] <= 1 for r in records),
        "claim_limits": ["Existing timber restraint and nominal rectangular torsion hypotheses are retained.", "Excluded bores, terminal profiles, unsampled stations and joint-local effects are not qualified.", "CD=1 original findings remain unchanged; the seven-day cumulative peak hypothesis is conditional and unobserved.", "The separate permanent-load comparison is required before the combined duration basis is complete.", "No Hillman product resistance or stiffness is supplied by this calculation."],
        "physical_release": False, "complete_member_acceptance": False, "complete_joint_acceptance": False,
        "frame_solve": False, "geometry_changed": False, "formal_torsion_qualification": False,
        "output_sha256": {name: sha(output / name) for name in ("same-cut-states.csv", "producer.py.snapshot")},
    }
    authenticate()
    dump(output / "checks.json", result)
    dump(output / "receipt.json", {"producer_sha256": result["producer_sha256"], "checks_sha256": sha(output / "checks.json"), "output_sha256": result["output_sha256"]})
    print("COMPLETED", len(records), "cuts; baseline error", baseline_error)
    for key in columns:
        print(key, result["global_peaks"][key][key])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
