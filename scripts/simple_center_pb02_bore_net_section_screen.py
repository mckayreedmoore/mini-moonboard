"""Bore-aware far-field PB02 member actions for one corrected trial case."""

import hashlib
import json
import math
from pathlib import Path

from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT
from scripts.simple_center_published_stiffness_basis import (
    DIAGNOSTIC_BORE_DIAMETER_MM as STIFFNESS_BASIS_BORE_DIAMETER_MM,
)
from scripts.simple_pb01_short_net_elastic_screen import elastic_corners

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / (
    "fea/results/diagnostics/pb02-contact-refinement-a12-forward-v1/"
    "density-2x/report.json"
)
CANDIDATE = "pb02-kerf-right-native-development-only"
GEOMETRY_SOURCE = "scripts/simple_center_pb02_geometry.py"
EXPECTED_GEOMETRY_FINGERPRINT = (
    "06f0cd1a1754d26fb2ff74cc2eb7da8eed80fbbea5cc84d7627ae8ff07d61387"
)
EXPECTED_REPORT_SHA256 = (
    "a5e24552a90e4d6e27a987e381665bcc489a9021b61769c77fbbd0c5948e3631"
)
DIAGNOSTIC_BORE_DIAMETER_MM = 7.3

CUTS = {
    "principal_at_upright_bore": {
        "member": "base_principal_center_right",
        "connection": "principal_upright_block/bolt_1",
        "size": (38.1, 139.7),
        "bore_spans": "u",
    },
    "side_cleat_at_upright_bore": {
        "member": "upright_side_cleat",
        "connection": "principal_upright_block/bolt_1",
        "size": (88.9, 61.6),
        "bore_spans": "u",
    },
    "side_cleat_at_link_bore": {
        "member": "upright_side_cleat",
        "connection": "upright_rear_block/bolt_1",
        "size": (88.9, 61.6),
        "bore_spans": "v",
    },
    "rear_cleat_at_link_bore": {
        "member": "rear_cleat",
        "connection": "upright_rear_block/bolt_1",
        "size": (88.9, 38.1),
        "bore_spans": "v",
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dot(first, second) -> float:
    return sum(a * b for a, b in zip(first, second, strict=True))


def _subtract(first, second):
    return [a - b for a, b in zip(first, second, strict=True)]


def _add(first, second):
    return [a + b for a, b in zip(first, second, strict=True)]


def _cross(first, second):
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ]


def _authenticate() -> tuple[dict, dict]:
    report = json.loads(REPORT_PATH.read_text())
    scope = report.get("diagnostic_scope", {})
    geometry_path = ROOT / GEOMETRY_SOURCE
    checks = (
        ACTIVE_FINGERPRINT == EXPECTED_GEOMETRY_FINGERPRINT,
        _sha256(REPORT_PATH) == EXPECTED_REPORT_SHA256,
        report.get("candidate") == CANDIDATE,
        scope.get("candidate") == CANDIDATE,
        scope.get("case") == "a12-forward",
        report.get("source_sha256", {}).get(GEOMETRY_SOURCE) == _sha256(geometry_path),
        report.get("numerically_accepted") is True,
        report.get("contact_active_set_converged") is True,
        report.get("axial_tension_active_set_converged") is True,
        report.get("global_equilibrium_passed") is True,
        report.get("member_equilibrium_passed") is True,
        report.get("mpc_check_passed") is True,
        report.get("actual_joint_demands_qualified") is False,
        report.get("qualified_for_design") is False,
        report.get("drilling_released") is False,
        report.get("fabrication_released") is False,
        scope.get("acceptance") is False,
    )
    if not all(checks):
        raise ValueError("PB02 report, geometry, scope, or acceptance state changed")
    return report, {
        "candidate": CANDIDATE,
        "case": "a12-forward",
        "active_geometry_fingerprint": ACTIVE_FINGERPRINT,
        "report_sha256": EXPECTED_REPORT_SHA256,
        "numerically_accepted": True,
        "actual_joint_demands_qualified": False,
    }


def _net_section(width: float, depth: float, bore_spans: str) -> dict:
    diameter = DIAGNOSTIC_BORE_DIAMETER_MM
    if bore_spans == "u":
        area = width * (depth - diameter)
        iu = width * (depth**3 - diameter**3) / 12
        iv = (depth - diameter) * width**3 / 12
        removed = width * diameter
    elif bore_spans == "v":
        area = (width - diameter) * depth
        iu = (width - diameter) * depth**3 / 12
        iv = depth * (width**3 - diameter**3) / 12
        removed = depth * diameter
    else:
        raise ValueError("Bore strip must span one local section axis")
    if min(width, depth) <= diameter:
        raise ValueError("Diagnostic bore does not leave a net section")
    return {
        "gross_area_mm2": width * depth,
        "removed_area_mm2": removed,
        "net_area_mm2": area,
        "retained_fraction": area / (width * depth),
        "centroid_x_t_mm": [width / 2, depth / 2],
        "second_moments_about_x_t_mm4": [iu, iv],
        "product_second_moment_mm4": 0.0,
        "idealized_removed_strip_spans_local_axis": bore_spans,
    }


def _station(member: dict, point) -> float:
    return _dot(_subtract(point, member["start"]), member["axis"])


def _local_row(member: dict, origin, force, moment, include: bool) -> dict:
    return {
        "station_along_grain_mm": _station(member, origin),
        "include_station_loads": include,
        "origin_xyz_mm": origin,
        "axial_n_tension_positive": _dot(force, member["axis"]),
        "shear_u_n": _dot(force, member["section_u"]),
        "shear_v_n": _dot(force, member["section_v"]),
        "moment_u_nmm": _dot(moment, member["section_u"]),
        "moment_v_nmm": _dot(moment, member["section_v"]),
        "torsion_nmm": _dot(moment, member["axis"]),
    }


def _principal_extrapolated_rows(report: dict, demand: dict, station: float):
    """Recover the bore actions without claiming a valid full-width report cut."""
    member = demand["member"]
    above = sorted(
        {
            row["station_along_grain_mm"]
            for row in demand["sections"]
            if row["station_along_grain_mm"] > station
        }
    )
    if not above:
        raise ValueError("Principal bore has no upper recovery anchor")
    anchor_station = above[0]
    anchors = [
        row
        for row in demand["sections"]
        if math.isclose(row["station_along_grain_mm"], anchor_station, abs_tol=1e-7)
        and row["include_station_loads"] is True
    ]
    if len(anchors) != 1:
        raise ValueError("Principal recovery anchor changed")
    target_origin = _add(member["start"], [station * value for value in member["axis"]])
    anchor = anchors[0]
    force = list(anchor["upper_load_force_xyz_n"])
    moment = _add(
        anchor["upper_load_moment_xyz_nmm"],
        _cross(_subtract(anchor["origin_xyz_mm"], target_origin), force),
    )
    excluded = _local_row(member, target_origin, force, moment, False)

    connection_name = "principal_upright_block/bolt_1"
    connection = report["physical_connection_forces"][connection_name]
    same_station = []
    for name, row in report["physical_connection_forces"].items():
        if row.get("first") != member["name"] and row.get("second") != member["name"]:
            continue
        if math.isclose(_station(member, row["point"]), station, abs_tol=1e-7):
            same_station.append(name)
    if same_station != [connection_name]:
        raise ValueError("Principal bore station load inventory changed")
    force_at_cut = connection["force_on_first_xyz_n"]
    included_force = _add(force, force_at_cut)
    included_moment = _add(
        moment,
        _cross(_subtract(connection["point"], target_origin), force_at_cut),
    )
    included = _local_row(member, target_origin, included_force, included_moment, True)
    return [excluded, included], {
        "kind": "free_body_extrapolation_from_first_valid_report_plane",
        "anchor_station_mm": anchor_station,
        "extrapolation_mm": anchor_station - station,
        "same_station_loads": same_station,
        "warning": "nominal full-section geometry is outside the report-valid interval",
    }


def _cut_rows(report: dict, demand: dict, station: float, cut_name: str):
    exact = [
        row
        for row in demand["sections"]
        if math.isclose(row["station_along_grain_mm"], station, abs_tol=1e-7)
    ]
    if len(exact) == 2 and {row["include_station_loads"] for row in exact} == {
        False,
        True,
    }:
        return (
            sorted(exact, key=lambda row: row["include_station_loads"]),
            {
                "kind": "exact_member_section_demands_rows",
                "anchor_station_mm": station,
                "extrapolation_mm": 0.0,
            },
            True,
        )
    if cut_name != "principal_at_upright_bore" or exact:
        raise ValueError(f"Missing exact paired report rows for {cut_name}")
    rows, provenance = _principal_extrapolated_rows(report, demand, station)
    return rows, provenance, False


def _screen_cut(report: dict, name: str, spec: dict) -> dict:
    demand = report["member_section_demands"][spec["member"]]
    member = demand["member"]
    width, depth = spec["size"]
    if (
        member["name"] != spec["member"]
        or not math.isclose(member["width_mm"], width, abs_tol=1e-6)
        or not math.isclose(member["depth_mm"], depth, abs_tol=1e-6)
        or member["qualified_for_design"] is not False
        or member["retained_area_fraction"] != 1.0
    ):
        raise ValueError(f"Modeled member section changed for {name}")
    connection = report["physical_connection_forces"][spec["connection"]]
    if spec["member"] not in (connection["first"], connection["second"]):
        raise ValueError(f"Bore connection ownership changed for {name}")
    station = _station(member, connection["point"])
    rows, provenance, exact = _cut_rows(report, demand, station, name)
    net = _net_section(width, depth, spec["bore_spans"])
    cut_sides = []
    for row in rows:
        elastic = elastic_corners(row, net, width=width, depth=depth)
        cut_sides.append(
            {
                "include_station_loads": row["include_station_loads"],
                "axial_n_tension_positive": row["axial_n_tension_positive"],
                "shear_u_n": row["shear_u_n"],
                "shear_v_n": row["shear_v_n"],
                "transverse_shear_resultant_n": math.hypot(
                    row["shear_u_n"], row["shear_v_n"]
                ),
                "gross_centroid_moment_u_nmm": row["moment_u_nmm"],
                "gross_centroid_moment_v_nmm": row["moment_v_nmm"],
                "torsion_nmm": row["torsion_nmm"],
                "torsion_separate_nmm": row["torsion_nmm"],
                "torsion_combined_with_normal_or_shear": False,
                **elastic,
            }
        )
    valid = station >= demand["section_valid_from_mm"] - 1e-7
    return {
        "member": spec["member"],
        "connection": spec["connection"],
        "station_along_grain_mm": station,
        "gross_size_u_v_mm": [width, depth],
        "report_section_valid_from_mm": demand["section_valid_from_mm"],
        "within_report_valid_full_section_interval": valid,
        "report_rows_exact_at_cut": exact,
        "action_provenance": provenance,
        "net_section": net,
        "cut_sides": cut_sides,
        "normal_stress_method": (
            "linear axial plus biaxial bending after net-centroid wrench shift"
        ),
        "transverse_shear_is_demand_only": True,
        "capacity_checked": False,
    }


def screen() -> dict:
    """Screen four bore cuts without converting one trial case into capacity."""
    report, authentication = _authenticate()
    cuts = {name: _screen_cut(report, name, spec) for name, spec in CUTS.items()}
    separation = (
        cuts["side_cleat_at_upright_bore"]["station_along_grain_mm"]
        - cuts["side_cleat_at_link_bore"]["station_along_grain_mm"]
    )
    if not math.isclose(separation, 27.5, abs_tol=1e-7):
        raise ValueError("Side-cleat bore separation changed")
    return {
        "authentication": authentication,
        "bore_basis": {
            "diagnostic_bore_diameter_mm": DIAGNOSTIC_BORE_DIAMETER_MM,
            "stiffness_basis_bore_diameter_mm": STIFFNESS_BASIS_BORE_DIAMETER_MM,
            "diameter_mismatch_mm": round(
                DIAGNOSTIC_BORE_DIAMETER_MM - STIFFNESS_BASIS_BORE_DIAMETER_MM, 10
            ),
            "diameters_match": math.isclose(
                DIAGNOSTIC_BORE_DIAMETER_MM,
                STIFFNESS_BASIS_BORE_DIAMETER_MM,
                abs_tol=1e-12,
            ),
            "drill_instruction": False,
        },
        "side_cleat_bore_center_separation_mm": separation,
        "cuts": cuts,
        "capacity_checked": False,
        "complete_joint_utilization": None,
        "unqualified": [
            "torsion_and_transverse_shear_interaction",
            "local_crossed_bore_interaction",
            "near_hole_stress_concentrations",
            "principal_bore_cut_outside_report_valid_full_section_interval",
            "material_resistance_and_capacity",
            "other_five_load_cases",
        ],
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
