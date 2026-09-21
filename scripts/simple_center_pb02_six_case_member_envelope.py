"""Build source-bound six-case PB02 bore-member demand screens."""

import hashlib
import json
import math

from fea.current_response_materials import df_l_no2_post_timber
from fea.reinforced_timber_resistance import (
    PSI_MPA,
    effective_beam_length,
    member_check,
)
from scripts import simple_center_pb02_bore_net_section_screen as bore_screen
from scripts import simple_center_pb02_six_case_evidence as six_case_evidence

CASE_ORDER = list(six_case_evidence.EXPECTED_CASES)
DIMENSION_LUMBER_REFERENCE = {
    "Fb_star_mpa": 900 * PSI_MPA,
    "Ft_mpa": 575 * PSI_MPA,
    "Fc_star_mpa": 1350 * PSI_MPA,
    "Fv_mpa": 180 * PSI_MPA,
    "Fc_perp_mpa": 625 * PSI_MPA,
    "Emin_mpa": 580_000 * PSI_MPA,
}
DIMENSION_LUMBER_MEMBERS = {
    "base_principal_center_right",
    "rear_cleat",
}
POST_TIMBER_MEMBERS = {"upright_side_cleat"}


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _authenticate_boundary() -> dict:
    result = six_case_evidence.screen()
    source = result.get("source_snapshot_authentication", {})
    if (
        result.get("status")
        != "authenticated_pb02_rear_clear_six_case_development_evidence"
        or result.get("summary", {}).get("accepted_case_count") != 6
        or result.get("summary", {}).get("geometry_fingerprint")
        != six_case_evidence.EXPECTED_GEOMETRY_FINGERPRINT
        or list(result.get("cases", {})) != CASE_ORDER
        or source.get("all_snapshot_hashes_match") is not True
        or result.get("qualified_for_design") is not False
        or result.get("drilling_released") is not False
        or result.get("fabrication_released") is not False
        or result.get("structural_released") is not False
    ):
        raise ValueError("six-case evidence boundary changed")
    return result


def _load_reports(authentication: dict) -> dict:
    reports = {}
    for case in CASE_ORDER:
        authenticated = authentication["cases"][case]
        path = six_case_evidence.SIX_CASE / authenticated["path"] / "report.json"
        if _sha256(path) != authenticated["report_sha256"]:
            raise ValueError(f"{case}: authenticated report changed while loading")
        reports[case] = json.loads(path.read_text())
    return reports


def _section_axes(spec: dict) -> dict:
    size_u, size_v = spec["size"]
    swapped = size_u > size_v
    local_to_sorted = {
        "u": "depth" if swapped else "width",
        "v": "width" if swapped else "depth",
    }
    return {
        "width_mm": min(size_u, size_v),
        "depth_mm": max(size_u, size_v),
        "original_size_u_v_mm": [size_u, size_v],
        "original_axes_swapped_for_member_check": swapped,
        "local_u_maps_to": local_to_sorted["u"],
        "local_v_maps_to": local_to_sorted["v"],
        "centered_hole_diameter_mm": bore_screen.DIAGNOSTIC_BORE_DIAMETER_MM,
        "centered_hole_spans_local_axis": spec["bore_spans"],
        "centered_hole_spans_section_axis": local_to_sorted[spec["bore_spans"]],
    }


def _reference(member: str) -> tuple[str, dict]:
    if member in DIMENSION_LUMBER_MEMBERS:
        return (
            "2024_NDS_DF-L_No.2_dimension_lumber_base_no_size_factor_benefit",
            dict(DIMENSION_LUMBER_REFERENCE),
        )
    if member in POST_TIMBER_MEMBERS:
        return (
            "2024_NDS_Table_4D_DF-L_No.2_Posts_and_Timbers",
            dict(df_l_no2_post_timber()["reference_override"]),
        )
    raise ValueError(f"No conservative stock classification for {member}")


def _member_actions(side: dict, axes: dict) -> dict:
    if axes["original_axes_swapped_for_member_check"]:
        return {
            "moment_strong_nmm": side["gross_centroid_moment_v_nmm"],
            "moment_weak_nmm": side["gross_centroid_moment_u_nmm"],
            "shear_strong_n": side["shear_u_n"],
            "shear_weak_n": side["shear_v_n"],
        }
    return {
        "moment_strong_nmm": side["gross_centroid_moment_u_nmm"],
        "moment_weak_nmm": side["gross_centroid_moment_v_nmm"],
        "shear_strong_n": side["shear_v_n"],
        "shear_weak_n": side["shear_u_n"],
    }


def _check_side(
    report: dict,
    cut: dict,
    side: dict,
    axes: dict,
    reference: dict,
) -> dict:
    demand = report["member_section_demands"][cut["member"]]
    unsupported_length = demand["length_mm"] - demand["section_valid_from_mm"]
    actions = _member_actions(side, axes)
    checked = member_check(
        width_mm=axes["width_mm"],
        depth_mm=axes["depth_mm"],
        axial_n=side["axial_n_tension_positive"],
        moment_strong_nmm=actions["moment_strong_nmm"],
        moment_weak_nmm=actions["moment_weak_nmm"],
        shear_strong_n=actions["shear_strong_n"],
        shear_weak_n=actions["shear_weak_n"],
        torsion_nmm=side["torsion_nmm"],
        column_effective_strong_mm=unsupported_length,
        column_effective_weak_mm=unsupported_length,
        beam_effective_mm=effective_beam_length(unsupported_length, axes["depth_mm"]),
        centered_hole_diameter_mm=axes["centered_hole_diameter_mm"],
        centered_hole_spans_section_axis=axes["centered_hole_spans_section_axis"],
        reference_override=reference,
    )
    normal_mode = (
        "necessary_compression_even_if_fully_braced"
        if side["axial_n_tension_positive"] < 0
        else "conservative_tension_and_bending"
    )
    normal_ratio = (
        checked["necessary_compression_interaction_even_if_fully_braced"]
        if side["axial_n_tension_positive"] < 0
        else checked["tension_conservative_interaction"]
    )
    return {
        "include_station_loads": side["include_station_loads"],
        "same_case_actions": {
            "axial_n_tension_positive": side["axial_n_tension_positive"],
            **actions,
            "torsion_nmm": side["torsion_nmm"],
        },
        "normal_interaction_mode": normal_mode,
        "necessary_fully_braced_normal_interaction": normal_ratio,
        "average_net_shear_ratio": checked["shear_ratio"],
        "governing_applicable_ratio": max(normal_ratio, checked["shear_ratio"]),
        "torsion_demand_nmm": checked["torsion_demand_nmm"],
        "torsion_demand_abs_nmm": abs(checked["torsion_demand_nmm"]),
        "torsion_resistance_evaluated": False,
        "stability_qualified": False,
        "stability_used_for_disposition": False,
        "member_check": {
            "references": checked["references"],
            "net_area_mm2": checked["net_area_mm2"],
            "centered_hole_spans_section_axis": checked[
                "centered_hole_spans_section_axis"
            ],
            "section_moduli_strong_weak_mm3": checked["section_moduli_strong_weak_mm3"],
            "stress_mpa": checked["stress_mpa"],
            "necessary_compression_interaction_even_if_fully_braced": checked[
                "necessary_compression_interaction_even_if_fully_braced"
            ],
            "tension_conservative_interaction": checked[
                "tension_conservative_interaction"
            ],
            "shear_ratio": checked["shear_ratio"],
            "shear_scope": checked["shear_scope"],
            "torsion_demand_nmm": checked["torsion_demand_nmm"],
            "torsion_resistance_evaluated": False,
            "local_opening_resistance_evaluated": False,
            "qualified_for_design": False,
        },
    }


def _cut_envelope(reports: dict, name: str, spec: dict) -> tuple[dict, list[dict]]:
    axes = _section_axes(spec)
    reference_basis, reference = _reference(spec["member"])
    cases = {}
    records = []
    expected_exact = name != "principal_at_upright_bore"
    for case in CASE_ORDER:
        cut = bore_screen._screen_cut(reports[case], name, spec)
        if cut["report_rows_exact_at_cut"] is not expected_exact:
            raise ValueError(f"{case}/{name}: cut provenance changed")
        if not math.isclose(
            cut["net_section"]["net_area_mm2"],
            _expected_net_area(axes),
            abs_tol=1e-7,
        ):
            raise ValueError(f"{case}/{name}: centered-hole section changed")
        sides = {}
        for side in cut["cut_sides"]:
            side_name = (
                "station_loads_included"
                if side["include_station_loads"]
                else "station_loads_excluded"
            )
            checked = _check_side(reports[case], cut, side, axes, reference)
            checked["report_rows_exact_at_cut"] = expected_exact
            checked["within_report_valid_full_section_interval"] = cut[
                "within_report_valid_full_section_interval"
            ]
            checked["action_provenance"] = cut["action_provenance"]
            sides[side_name] = checked
            records.append(
                {
                    "case": case,
                    "cut": name,
                    "side": side_name,
                    "report_rows_exact_at_cut": expected_exact,
                    "provenance_kind": cut["action_provenance"]["kind"],
                    "applicable_to_disposition": expected_exact,
                    "normal_interaction": checked[
                        "necessary_fully_braced_normal_interaction"
                    ],
                    "average_net_shear_ratio": checked["average_net_shear_ratio"],
                    "ratio": checked["governing_applicable_ratio"],
                    "torsion_demand_nmm": checked["torsion_demand_nmm"],
                    "torsion_demand_abs_nmm": checked["torsion_demand_abs_nmm"],
                    "torsion_resistance_evaluated": False,
                }
            )
        cases[case] = {
            "station_along_grain_mm": cut["station_along_grain_mm"],
            "report_rows_exact_at_cut": cut["report_rows_exact_at_cut"],
            "within_report_valid_full_section_interval": cut[
                "within_report_valid_full_section_interval"
            ],
            "action_provenance": cut["action_provenance"],
            "net_section": cut["net_section"],
            "cut_sides": sides,
        }
    return (
        {
            "member": spec["member"],
            "connection": spec["connection"],
            "sorted_section": axes,
            "reference_basis": reference_basis,
            "reference_values_mpa": reference,
            "exact_cut_applicable_to_disposition": expected_exact,
            "cases": cases,
        },
        records,
    )


def _expected_net_area(axes: dict) -> float:
    width = axes["width_mm"]
    depth = axes["depth_mm"]
    hole = axes["centered_hole_diameter_mm"]
    if axes["centered_hole_spans_section_axis"] == "width":
        return width * (depth - hole)
    return (width - hole) * depth


def _governing(records: list[dict]) -> dict:
    exact = [row for row in records if row["applicable_to_disposition"]]
    if not exact:
        raise ValueError("No exact cut is available for development disposition")
    by_case = {
        case: max(
            (row for row in exact if row["case"] == case),
            key=lambda row: row["ratio"],
        )
        for case in CASE_ORDER
    }
    by_cut = {
        name: {
            **max(
                (row for row in records if row["cut"] == name),
                key=lambda row: row["ratio"],
            ),
            "applicable": name != "principal_at_upright_bore",
        }
        for name in bore_screen.CUTS
    }
    return {
        "by_case": by_case,
        "by_cut": by_cut,
        "exact_cut_only": {
            **max(exact, key=lambda row: row["ratio"]),
            "applicable": True,
        },
        "extrapolated_principal_only": {
            **max(
                (row for row in records if not row["applicable_to_disposition"]),
                key=lambda row: row["ratio"],
            ),
            "applicable": False,
        },
    }


def screen() -> dict:
    """Return exact-cut member ratios without qualifying stability or openings."""
    authentication = _authenticate_boundary()
    reports = _load_reports(authentication)
    cuts = {}
    records = []
    for name, spec in bore_screen.CUTS.items():
        cuts[name], cut_records = _cut_envelope(reports, name, spec)
        records.extend(cut_records)
    governing = _governing(records)
    decision = "ADVANCE" if governing["exact_cut_only"]["ratio"] < 1 else "REVISE"
    return {
        "status": "authenticated_six_case_bore_member_envelope",
        "authentication": {
            "six_case_status": authentication["status"],
            "summary_sha256": authentication["summary"]["sha256"],
            "geometry_fingerprint": authentication["summary"]["geometry_fingerprint"],
            "accepted_case_count": authentication["summary"]["accepted_case_count"],
            "source_snapshot_file_count": authentication[
                "source_snapshot_authentication"
            ]["file_count"],
        },
        "case_order": CASE_ORDER,
        "bore_basis": {
            "diagnostic_centered_strip_diameter_mm": (
                bore_screen.DIAGNOSTIC_BORE_DIAMETER_MM
            ),
            "drill_instruction": False,
        },
        "cuts": cuts,
        "governing": governing,
        "disposition": {
            "decision": decision,
            "scope": "development_only",
            "uses_exact_cuts_only": True,
            "criterion": (
                "Maximum same-case necessary fully-braced normal interaction or "
                "average net shear ratio across exact cuts only."
            ),
            "meaning": (
                "Advance only to unresolved local opening, torsion, stability, and "
                "complete-joint checks; this is not member or structural acceptance."
            ),
        },
        "boundaries": {
            "stability_qualified": False,
            "stability_used_for_disposition": False,
            "torsion_resistance_evaluated": False,
            "local_splitting_qualified": False,
            "near_hole_stress_concentration_qualified": False,
            "extrapolated_principal_accepted": False,
            "complete_joint_verdict": False,
        },
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True, allow_nan=False))
