"""Build a source-bound PB02 six-case component-demand envelope."""

import hashlib
import json
import math

from scripts import simple_center_pb02_end_grain_screen as end_grain_screen
from scripts import simple_center_pb02_hardware_screen as hardware_screen
from scripts import simple_center_pb02_individual_component_screen as individual_screen
from scripts import simple_center_pb02_six_case_evidence as six_case_evidence

CASE_ORDER = list(six_case_evidence.EXPECTED_CASES)
EXPECTED_INTERFACE_NAMES = {
    "post_block",
    "block_header",
    "header_principal_block",
    "principal_block_principal",
    "principal_upright_block",
    "upright_rear_block",
    "rear_block_post",
}


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _magnitude(vector) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _cross(first, second) -> list[float]:
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ]


def _authenticate_boundary() -> dict:
    result = six_case_evidence.screen()
    if (
        result.get("status")
        != "authenticated_pb02_rear_clear_six_case_development_evidence"
        or result.get("summary", {}).get("accepted_case_count") != 6
        or result.get("summary", {}).get("geometry_fingerprint")
        != six_case_evidence.EXPECTED_GEOMETRY_FINGERPRINT
        or list(result.get("cases", {})) != CASE_ORDER
        or result.get("source_snapshot_authentication", {}).get(
            "all_snapshot_hashes_match"
        )
        is not True
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
        relative = authentication["cases"][case]["path"]
        path = six_case_evidence.SIX_CASE / relative / "report.json"
        if _sha256(path) != authentication["cases"][case]["report_sha256"]:
            raise ValueError(f"{case}: authenticated report changed while loading")
        reports[case] = json.loads(path.read_text())
    return reports


def _direct_comparisons(bolt: dict, axial_n: float, lateral_n: float) -> dict:
    capacities = hardware_screen._a307_direct_capacities(bolt["wood_grip_mm"])
    tension_ratio = axial_n / capacities["tension_asd_reference_n"]
    shear_ratio = lateral_n / capacities["single_shear_asd_reference_n"]
    washer = hardware_screen._washer_demand(axial_n)[
        "ideal_20mm_od_7p3mm_bore_sensitivity"
    ]
    return {
        "direct_shaft": {
            "tension_ratio": tension_ratio,
            "shear_ratio": shear_ratio,
            "conservative_linear_interaction_ratio": tension_ratio + shear_ratio,
            "long_grip_factor": capacities["long_grip_factor"],
            "conditional_comparator_only": True,
            "qualified": False,
        },
        "ideal_20mm_washer_wood_bearing_sensitivity": {
            "demand_ratio": washer["demand_ratio"],
            "wood_bearing_reference_n": washer["wood_bearing_reference_n"],
            "actual_washer_result": False,
        },
    }


def _individual_comparison(report: dict, name: str) -> dict | None:
    spec = individual_screen.CONNECTIONS.get(name)
    if spec is None:
        return None
    result = individual_screen._connection(report, name, spec)
    return {
        root: {
            "adjusted_reference_n": row["adjusted_reference_n"],
            "demand_ratio": row["demand_ratio"],
            "governing_mode": row["governing_mode"],
        }
        for root, row in result["root_sensitivities"].items()
    }


def _end_grain_comparison(name: str, lateral_n: float) -> dict | None:
    if not name.startswith("block_header/bolt_"):
        return None
    return {
        "root_0p189_in": _end_grain_ratio(0.189, lateral_n),
        "root_0p180_in": _end_grain_ratio(0.180, lateral_n),
    }


def _end_grain_ratio(root_diameter_in: float, lateral_n: float) -> dict:
    row = end_grain_screen.root_case(root_diameter_in, lateral_n)
    return {
        "end_grain_adjusted_reference_n": row["end_grain_adjusted_reference_n"],
        "demand_ratio": row["demand_ratio"],
        "governing_mode": row["governing_mode"],
    }


def _bolt_envelope(reports: dict) -> tuple[dict, list[dict]]:
    expected_names = set(hardware_screen.BOLTS)
    for case, report in reports.items():
        actual = {
            name
            for name in report.get("physical_connection_forces", {})
            if "/bolt_" in name
        }
        if actual != expected_names:
            raise ValueError(f"{case}: PB02 exact ten-bolt inventory changed")

    bolts = {}
    ratio_records = []
    for name, bolt in hardware_screen.BOLTS.items():
        demand_by_case = {}
        for case in CASE_ORDER:
            source = reports[case]["physical_connection_forces"][name]
            expected_ownership = {
                field: bolt[field] for field in ("first", "second", "axis", "edge")
            }
            if any(
                source.get(field) != value
                for field, value in expected_ownership.items()
            ):
                raise ValueError(f"{case}/{name}: bolt force ownership changed")
            axial_n = max(0.0, source["axial_along_installation_direction_n"])
            lateral_n = source["transverse_shear_n"]
            comparisons = _direct_comparisons(bolt, axial_n, lateral_n)
            individual = _individual_comparison(reports[case], name)
            end_grain = _end_grain_comparison(name, lateral_n)
            if individual is not None:
                comparisons["individual_wood_yield"] = individual
            if end_grain is not None:
                comparisons["block_header_end_grain"] = end_grain
            demand_by_case[case] = {
                "axial_tension_n": axial_n,
                "lateral_n": lateral_n,
                "combined_n": math.hypot(axial_n, lateral_n),
                "simultaneous_from_same_solve": True,
                "conditional_comparison_ratios": comparisons,
            }
            ratio_records.extend(_ratio_records(case, name, comparisons))

        governing_case, governing = max(
            demand_by_case.items(), key=lambda item: item[1]["combined_n"]
        )
        bolts[name] = {
            "interface": bolt["edge"],
            "inventory": {
                "first": bolt["first"],
                "second": bolt["second"],
                "axis": bolt["axis"],
                "stack_name": bolt["stack_name"],
                "wood_grip_mm": bolt["wood_grip_mm"],
                "trial_length_in": bolt["trial_length_in"],
            },
            "demand_by_case": demand_by_case,
            "governing_combined_demand": {
                "case": governing_case,
                "axial_tension_n": governing["axial_tension_n"],
                "lateral_n": governing["lateral_n"],
                "combined_n": governing["combined_n"],
            },
        }
    return bolts, ratio_records


def _ratio_records(case: str, name: str, comparisons: dict) -> list[dict]:
    records = [
        {
            "family": "direct_shaft",
            "name": name,
            "case": case,
            "variant": "conservative_linear_interaction",
            "ratio": comparisons["direct_shaft"][
                "conservative_linear_interaction_ratio"
            ],
        },
        {
            "family": "washer_bearing_sensitivity",
            "name": name,
            "case": case,
            "variant": "ideal_20mm_od_7p3mm_bore",
            "ratio": comparisons["ideal_20mm_washer_wood_bearing_sensitivity"][
                "demand_ratio"
            ],
        },
    ]
    for family in ("individual_wood_yield", "block_header_end_grain"):
        for variant, row in comparisons.get(family, {}).items():
            records.append(
                {
                    "family": family,
                    "name": name,
                    "case": case,
                    "variant": variant,
                    "ratio": row["demand_ratio"],
                }
            )
    return records


def _interface_envelope(reports: dict) -> dict:
    for case, report in reports.items():
        actual = set(report.get("pb02_contact_aggregation", {}).get("interfaces", {}))
        if actual != EXPECTED_INTERFACE_NAMES:
            raise ValueError(f"{case}: PB02 seven-interface inventory changed")
    interfaces = {}
    for name in sorted(EXPECTED_INTERFACE_NAMES):
        demand_by_case = {}
        for case in CASE_ORDER:
            row = reports[case]["pb02_contact_aggregation"]["interfaces"][name]
            centroid = row["reference_net_centroid_mm"]
            complete_force = list(row["force_resultant_n"])
            complete_moment = list(row["moment_resultant_about_net_centroid_nmm"])
            for bolt_name, bolt in hardware_screen.BOLTS.items():
                if bolt["edge"] != name:
                    continue
                bolt_force = reports[case]["physical_connection_forces"][bolt_name]
                if (
                    bolt_force.get("first") != row["first"]
                    or bolt_force.get("second") != row["second"]
                ):
                    raise ValueError(f"{case}/{name}: bolt/contact ownership changed")
                force = bolt_force["force_on_first_xyz_n"]
                arm = [bolt_force["point"][axis] - centroid[axis] for axis in range(3)]
                bolt_moment = _cross(arm, force)
                complete_force = [
                    complete_force[axis] + force[axis] for axis in range(3)
                ]
                complete_moment = [
                    complete_moment[axis] + bolt_moment[axis] for axis in range(3)
                ]
            demand_by_case[case] = {
                "contact_force_resultant_xyz_n": row["force_resultant_n"],
                "contact_force_resultant_n": _magnitude(row["force_resultant_n"]),
                "contact_moment_resultant_about_net_centroid_xyz_nmm": row[
                    "moment_resultant_about_net_centroid_nmm"
                ],
                "contact_moment_resultant_nmm": _magnitude(
                    row["moment_resultant_about_net_centroid_nmm"]
                ),
                "complete_interface_force_resultant_xyz_n": complete_force,
                "complete_interface_force_resultant_n": _magnitude(complete_force),
                "complete_interface_moment_about_net_centroid_xyz_nmm": (
                    complete_moment
                ),
                "complete_interface_moment_resultant_nmm": _magnitude(complete_moment),
                "active_tributary_area_mm2": row["active_tributary_area_mm2"],
                "peak_cell_average_pressure_n_per_mm2": row[
                    "peak_average_cell_pressure_n_per_mm2"
                ],
            }
        interfaces[name] = {
            "demand_by_case": demand_by_case,
            "resistance_ratio": None,
            "resistance_qualified": False,
        }
    return interfaces


def _governing(bolts: dict, interfaces: dict) -> dict:
    bolt_rows = [
        (name, case, demand)
        for name, bolt in bolts.items()
        for case, demand in bolt["demand_by_case"].items()
    ]
    bolt_name, bolt_case, bolt = max(bolt_rows, key=lambda row: row[2]["combined_n"])
    axial_name, axial_case, axial = max(
        bolt_rows, key=lambda row: row[2]["axial_tension_n"]
    )
    lateral_name, lateral_case, lateral = max(
        bolt_rows, key=lambda row: row[2]["lateral_n"]
    )

    interface_rows = [
        (name, case, demand)
        for name, interface in interfaces.items()
        for case, demand in interface["demand_by_case"].items()
    ]
    force_name, force_case, force = max(
        interface_rows,
        key=lambda row: row[2]["complete_interface_force_resultant_n"],
    )
    moment_name, moment_case, moment = max(
        interface_rows,
        key=lambda row: row[2]["complete_interface_moment_resultant_nmm"],
    )
    pressure_name, pressure_case, pressure = max(
        interface_rows,
        key=lambda row: row[2]["peak_cell_average_pressure_n_per_mm2"],
    )
    return {
        "bolt_combined_demand": {
            "name": bolt_name,
            "interface": bolts[bolt_name]["interface"],
            "case": bolt_case,
            "axial_tension_n": bolt["axial_tension_n"],
            "lateral_n": bolt["lateral_n"],
            "combined_n": bolt["combined_n"],
        },
        "bolt_axial_tension": {
            "name": axial_name,
            "interface": bolts[axial_name]["interface"],
            "case": axial_case,
            "axial_tension_n": axial["axial_tension_n"],
        },
        "bolt_lateral_demand": {
            "name": lateral_name,
            "interface": bolts[lateral_name]["interface"],
            "case": lateral_case,
            "lateral_n": lateral["lateral_n"],
        },
        "complete_interface_force_resultant": {
            "name": force_name,
            "case": force_case,
            "force_n": force["complete_interface_force_resultant_n"],
        },
        "complete_interface_moment_resultant": {
            "name": moment_name,
            "case": moment_case,
            "moment_nmm": moment["complete_interface_moment_resultant_nmm"],
        },
        "interface_peak_cell_average_pressure": {
            "name": pressure_name,
            "case": pressure_case,
            "pressure_n_per_mm2": pressure["peak_cell_average_pressure_n_per_mm2"],
            "local_pressure_qualified": False,
        },
        "case_by_maximum_bolt_combined_demand": bolt_case,
    }


def _comparison_summary(records: list[dict]) -> dict:
    families = {}
    applicable_counts = {
        "direct_shaft": 10,
        "washer_bearing_sensitivity": 10,
        "individual_wood_yield": 2,
        "block_header_end_grain": 2,
    }
    for family, applicable_bolt_count in applicable_counts.items():
        rows = [row for row in records if row["family"] == family]
        governing = max(rows, key=lambda row: row["ratio"])
        families[family] = {
            "applicable_bolt_count": applicable_bolt_count,
            "governing": governing,
            "conditional_comparator_only": True,
            "qualified": False,
        }
    all_below_one = all(row["ratio"] < 1.0 for row in records)
    return families | {
        "all_supported_conditional_ratios_below_one": all_below_one,
        "complete_joint_verdict": False,
    }


def screen() -> dict:
    """Return authenticated demands and bounded comparator ratios, not acceptance."""
    authentication = _authenticate_boundary()
    reports = _load_reports(authentication)
    bolts, ratio_records = _bolt_envelope(reports)
    interfaces = _interface_envelope(reports)
    comparisons = _comparison_summary(ratio_records)
    governing = _governing(bolts, interfaces)
    decision = (
        "ADVANCE"
        if comparisons["all_supported_conditional_ratios_below_one"]
        else "REVISE"
    )
    return {
        "status": "authenticated_six_case_component_demand_envelope",
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
        "bolts": bolts,
        "interfaces": interfaces,
        "governing": governing,
        "conditional_comparisons": comparisons,
        "calculation_scope": {
            "reused_helpers": [
                "simple_center_pb02_hardware_screen._a307_direct_capacities",
                "simple_center_pb02_hardware_screen._washer_demand",
                "simple_center_pb02_individual_component_screen._connection",
                "simple_center_pb02_end_grain_screen.root_case",
            ],
            "local_pure_adapters": (
                "Load authenticated reports, preserve simultaneous per-case bolt "
                "components, compute vector magnitudes, and select envelope maxima."
            ),
        },
        "sensitivity_caveats": [
            (
                "The six-case envelope uses the authenticated 8x8 reference-density "
                "contact model; density sensitivity is not a six-case envelope."
            ),
            (
                "Direct A307 shaft ratios retain the existing unqualified long-grip "
                "method and do not establish product-specific bolt suitability."
            ),
            (
                "The 20 mm washer ratio is an ideal wood-bearing sensitivity only; "
                "actual washer dimensions, metal bending, preload, and prying remain open."
            ),
            (
                "Wood-yield ratios cover only the two existing individual-bolt routes "
                "and the block/header end-grain route, with stated root sensitivities."
            ),
            (
                "Interface force, moment, area, and cell-average pressure are demands; "
                "they are not local bearing or complete-joint resistance checks."
            ),
            (
                "Crossed-bore splitting, net sections, group effects, fabrication "
                "tolerances, delivered hardware, and remaining connector proxies are open."
            ),
        ],
        "disposition": {
            "decision": decision,
            "scope": "development_only",
            "meaning": (
                "Advance the source-bound PB02 candidate to the unresolved component "
                "and complete-joint checks; this is not design acceptance or release."
            ),
            "reject_trigger": "evidence authentication failure",
            "revise_trigger": "any supported conditional comparison ratio at or above 1",
        },
        "boundaries": {
            "factory_connectors_only": True,
            "custom_steel_authorized": False,
            "lap_joints_authorized": False,
            "component_resistance_complete": False,
            "complete_joint_verdict": False,
        },
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True, allow_nan=False))
