"""Compare existing corner section-traction proxies with conditional wood references."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "net-section-material-reference.json"
PSI_TO_MPA = 0.006894757293168361

TRACTION = (
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "current-corner-net-section-normal-traction-attempt01/normal-traction.json"
)
TRACTION_PRODUCER = (
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "current-corner-net-section-normal-traction-attempt01/convert.py"
)
MATERIALS = (
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/"
    "material-inputs.json"
)
MATERIALS_NOTE = (
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/"
    "materials.md"
)
TABLE_4A = (
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/"
    "materials-source/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf"
)
PS_20_25 = (
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/"
    "materials-source/PS-20-25-Voluntary-Product-Standard.pdf"
)
MODEL_BY_CASE = {
    "a12-rear": (
        "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
        "current-springa-selected-floor-a12-rear-attempt03/model.json"
    ),
    "a1-rear": (
        "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
        "current-springa-selected-floor-a1-rear-attempt02/model.json"
    ),
    "k12-rear": (
        "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
        "current-k12-rear-spr489-direct-native-attempt01/model.json"
    ),
}

# These exact source pins bind the previously produced proxies, their section
# axes, and the current conditional material scenario. No parent register or
# mutable corner summary is an input.
PINNED_INPUT_SHA256 = {
    TRACTION: "4ac5094c733f4497c69f9890858581c1a283cb2782c1922f0a149185df66c386",
    TRACTION_PRODUCER: "885d883f67e6be64c68790ace19a33c1e30710ab5b225e1a1666397b750c63f0",
    MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    MATERIALS_NOTE: "943e5ecb26a5bb9e49e55e4c510bbbf697b08a6b9415c26bbcb41c48db70a2d6",
    TABLE_4A: "1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b",
    PS_20_25: "8868066272130bf7a6621b7fda6f9539bf2e26e57975f2c6c00489b6613f51ca",
    MODEL_BY_CASE["a12-rear"]: "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    MODEL_BY_CASE["a1-rear"]: "72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd",
    MODEL_BY_CASE["k12-rear"]: "8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd",
}

MEMBERS = ("knee_outer_left_spine", "knee_outer_left_inner_frame_block")
CASE_ORDER = ("a12-rear", "a1-rear", "k12-rear")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text())


def pinned_sources() -> dict[str, str]:
    actual = {path: sha256(ROOT / path) for path in PINNED_INPUT_SHA256}
    assert actual == PINNED_INPUT_SHA256, "pinned source hash changed"
    return actual


def material_member(materials: dict, member_id: str) -> dict:
    matches = [item for item in materials["members"] if item["member_id"] == member_id]
    assert len(matches) == 1
    return matches[0]


def verify_applicability(traction: dict, materials: dict) -> dict:
    # The section axis and XY section basis are checked against each original
    # case model, rather than inferred from the proxy label.
    input_sources = traction["source_sha256"]
    alignments = {}
    for case in CASE_ORDER:
        model_path = MODEL_BY_CASE[case]
        assert input_sources[model_path] == PINNED_INPUT_SHA256[model_path]
        model = read_json(model_path)
        assert model["case_id"] == case
        for member_id in MEMBERS:
            geometry = model["body_geometry"][member_id]["geometry_record"]
            axis = geometry["axis"]
            u = geometry["section_u"]
            v = geometry["section_v"]
            assert axis == [0.0, 0.0, 1.0]
            assert u == [1.0, 0.0, 0.0] and v == [0.0, 1.0, 0.0]
            cut_normal = [
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0],
            ]
            proposed_grain = material_member(materials, member_id)[
                "source_proposed_longitudinal_grain_global_xyz"
            ]
            dot = sum(a * b for a, b in zip(cut_normal, proposed_grain))
            assert cut_normal == axis and proposed_grain == [0.0, 0.0, 1.0]
            assert math.isclose(dot, 1.0, abs_tol=1e-12)
            entry = alignments.setdefault(
                member_id,
                {
                    "source_proposed_longitudinal_grain_global_xyz": proposed_grain,
                    "section_cut_normal_global_xyz": cut_normal,
                    "absolute_grain_normal_dot": abs(dot),
                    "classification": "parallel_to_longitudinal_grain",
                    "model_geometry_checks": [],
                },
            )
            entry["model_geometry_checks"].append(case)

    for member_id in MEMBERS:
        assert alignments[member_id]["model_geometry_checks"] == list(CASE_ORDER)
    return alignments


def verify_conditional_properties(materials: dict) -> dict:
    base = materials["conditional_DF_L_No2_base_row"]["base_properties"]
    assert base["Ft_parallel"] == 575 and base["Fc_parallel"] == 1350
    assert base["conditions"] == (
        "NDS Supplement Table 4A reference values: normal load duration and dry service; conditional scenario only."
    )
    spine = material_member(materials, MEMBERS[0])
    block = material_member(materials, MEMBERS[1])
    assert spine["conditional_final_nominal_stock_class"] == "2x6"
    assert spine["code_Table4A_CF"] == {"Fb": 1.3, "Ft_parallel": 1.3, "Fc_parallel": 1.1}
    assert block["code_Table4A_CF"] is None
    assert block["study_only_CF_for_arithmetic"] == 1.0
    assert block["source_grade_inheritance_from_ripped_4x6"] is False
    return {
        "species_group_scenario": "Douglas Fir-Larch (not DF-L North)",
        "grade_scenario": "No. 2, conditional arithmetic only",
        "Ft_parallel_psi": base["Ft_parallel"],
        "Fc_parallel_psi": base["Fc_parallel"],
        "psi_to_MPa": PSI_TO_MPA,
        "Ft_parallel_MPa": base["Ft_parallel"] * PSI_TO_MPA,
        "Fc_parallel_MPa": base["Fc_parallel"] * PSI_TO_MPA,
        "reference_basis": "unadjusted Table 4A base row; CF=1 raw-reference arithmetic",
        "conditions": "dry service, normal load duration, normal temperature, unincised; CM=Ct=Ci=1 baseline assumptions",
        "spine_size_factor_context": {
            "nominal_section": "2x6",
            "Table4A_CF_Ft_parallel": 1.3,
            "Table4A_CF_Fc_parallel": 1.1,
            "applied_here": False,
            "reason": "screen reports ratios to unadjusted named base references; not an adjusted NDS check",
        },
        "ripped_block_CF_context": {
            "CFstudy": 1.0,
            "code_assigned_CF": None,
            "post_rip_grade_observed": False,
            "meaning": "explicit hypothetical final-section no-size-increase arithmetic scenario only",
        },
        "duration_and_other_adjustments": "No CD or other adjusted-capacity credit is applied; ratios are not adjusted design values.",
    }


def row_key(row: dict, extreme: str) -> dict:
    return {
        "case": row["case"],
        "load_factor": row["load_factor"],
        "member": row["member"],
        "axis": row["axis"],
        "cut_side": row["cut_side"],
        "extreme": extreme,
    }


def summarize(traction: dict, material_reference: dict) -> list[dict]:
    rows = traction["rows"]
    assert len(rows) == 252
    assert set(row["case"] for row in rows) == set(CASE_ORDER)
    expected_factors = {0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0}
    assert {row["load_factor"] for row in rows} == expected_factors
    all_keys = [
        (row["case"], row["load_factor"], row["member"], row["axis"], row["cut_side"])
        for row in rows
    ]
    assert len(all_keys) == len(set(all_keys))

    results = []
    ft_mpa = material_reference["Ft_parallel_MPa"]
    fc_mpa = material_reference["Fc_parallel_MPa"]
    for case in CASE_ORDER:
        for member in MEMBERS:
            subset = [row for row in rows if row["case"] == case and row["member"] == member]
            expected_count = 56 if member == MEMBERS[0] else 28
            assert len(subset) == expected_count
            tension_row = max(subset, key=lambda row: row["nominal_affine_min_max_normal_traction_MPa"][1])
            compression_row = min(subset, key=lambda row: row["nominal_affine_min_max_normal_traction_MPa"][0])
            tension = max(0.0, tension_row["nominal_affine_min_max_normal_traction_MPa"][1])
            compression = max(0.0, -compression_row["nominal_affine_min_max_normal_traction_MPa"][0])
            results.append(
                {
                    "case": case,
                    "member": member,
                    "source_proxy_records_examined": len(subset),
                    "tension": {
                        "peak_positive_nominal_affine_sigma_MPa": tension,
                        "reference_property": "Ft_parallel",
                        "reference_MPa": ft_mpa,
                        "raw_proxy_to_reference_ratio": tension / ft_mpa,
                        "source_row_key": row_key(tension_row, "nominal_affine_max"),
                    },
                    "compression": {
                        "peak_negative_nominal_affine_sigma_magnitude_MPa": compression,
                        "reference_property": "Fc_parallel",
                        "reference_MPa": fc_mpa,
                        "raw_proxy_to_reference_ratio": compression / fc_mpa,
                        "source_row_key": row_key(compression_row, "nominal_affine_min"),
                    },
                }
            )
    assert sum(item["source_proxy_records_examined"] for item in results) == len(rows)
    return results


def produce() -> dict:
    pins = pinned_sources()
    traction = read_json(TRACTION)
    assert traction["schema"] == "current_corner_net_section_affine_normal_traction/v1"
    assert traction["status"] == "PASS_SOURCE_BOUND_NOMINAL_SECTION_PROPERTIES_AND_TRACTION_ONLY"
    assert traction["strength_checked"] is False and traction["joint_accepted"] is False
    materials = read_json(MATERIALS)
    material_reference = verify_conditional_properties(materials)
    alignments = verify_applicability(traction, materials)
    results = summarize(traction, material_reference)
    pins[str(Path(__file__).relative_to(ROOT))] = sha256(Path(__file__))
    return {
        "schema": "current_corner_net_section_material_reference/v1",
        "status": "PASS_CONDITIONAL_RAW_REFERENCE_RATIOS_ONLY",
        "source_sha256": pins,
        "source_proxy_schema": traction["schema"],
        "source_proxy_record_count": len(traction["rows"]),
        "material_reference_scenario": material_reference,
        "grain_applicability": alignments,
        "case_member_summaries": results,
        "scope_limits": [
            "Existing 252 section-traction records only; no new cuts, loads, geometry, local stress solve, or native solve.",
            "Ratios compare the extrema of an existing nominal affine normal-stress proxy with unadjusted conditional DF-L No.2 parallel-grain Ft/Fc references; not NDS adjusted design checks or acceptance.",
            "Both section normals align with proposed +Z grain. Grain vectors, species, grade and service conditions are conditional scenarios, not observations of delivered timber.",
            "The inner block is a ripped 4x6 section with grade/design-value inheritance unresolved; CFstudy=1 is hypothetical arithmetic only.",
            "The section proxy assumes a common affine strain field across disconnected inner-block ligaments; this does not establish physical common strain, hole-wall stress, bearing transfer, or actual local stress.",
            "No splitting, shear/torsion, stability, duration credit, other capacity adjustment, interaction, member resistance, or complete-joint behavior is evaluated.",
        ],
        "joint_accepted": False,
        "strength_acceptance_checked": False,
        "geometry_changed": False,
        "native_solve_run": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(produce(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.verify:
        assert OUTPUT.read_text() == rendered, "saved material-reference screen differs from source replay"
        print("PASS_CONDITIONAL_RAW_REFERENCE_RATIOS_ONLY: 252 source proxies; 6 case/member summaries")
    else:
        OUTPUT.write_text(rendered)
        print("Wrote conditional raw-reference ratios for 6 case/member combinations")


if __name__ == "__main__":
    main()
