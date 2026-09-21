"""RV-2 bounded PB-01 rail decision from the preserved four-contact diagnostic."""

import json
import math

from scripts.simple_pb01_cleat_gross_section_screen import screen as cleat_screen
from scripts.simple_pb01_hybrid_component_comparison import compare as bolt_compare
from scripts.simple_pb01_hybrid_local_actions import (
    ARCHIVE_SHA256,
    CANDIDATE,
    REPORT_SHA256,
    extract,
)
from scripts.simple_pb01_quarter_member_screen import screen as member_screen
from scripts.simple_pb01_rail_receiving_envelope import screen as rail_stack_screen

HOSTS = {
    "upright": "base_principal_center_right",
    "rail": "base_rail_service_lower_right",
}
MEMBER_REASONS = {
    "rail_host_row_toward_butt": "Actual row force toward the butt and its critical failure path are not established by connector forces alone.",
    "cleat_upright_row_toward_front": "Actual cleat row force toward the front and its critical failure path are not established by connector forces alone.",
    "upright_host_net_tension": "Tensile force at the bored critical section is not available from connector forces alone.",
    "rail_host_net_tension": "Tensile force at the bored critical section is not available from connector forces alone.",
    "cleat_rail_holes_net_tension": "Tensile force at the bored critical section is not available from connector forces alone.",
    "cleat_upright_hole_net_tension": "Tensile force at the bored critical section is not available from connector forces alone.",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decide():
    """Keep simultaneous signed actions; compare only established components."""
    source = extract()
    require(
        source["case"] == "a12-left"
        and source["scope"] == "diagnostic_only"
        and source["candidate"] == CANDIDATE
        and source["archive_sha256"] == ARCHIVE_SHA256
        and source["report_sha256"] == REPORT_SHA256
        and source["proxy_station_count"] == 23
        and set(source["interfaces"]) == set(HOSTS),
        "PB-01 diagnostic identity changed",
    )
    components = bolt_compare()
    members = member_screen()
    cleat = cleat_screen()
    stack = rail_stack_screen()
    require(
        components["case"] == source["case"]
        and components["source_archive_sha256"] == source["archive_sha256"]
        and components["proxy_station_count"] == 23
        and cleat["case"] == source["case"]
        and cleat["archive_sha256"] == source["archive_sha256"]
        and cleat["report_sha256"] == source["report_sha256"]
        and members["conditional_only"] is True
        and members["physical_width"] == "kerf-right"
        and set(members["components_lbf"]) == set(MEMBER_REASONS)
        and stack["receiving_accepted"] is False,
        "PB-01 helper identity changed",
    )

    interfaces = {}
    bolt_checks = {}
    for family, host in HOSTS.items():
        face = source["interfaces"][family]
        compared = components["interfaces"][family]
        require(
            face["host"] == compared["host"] == host
            and face["cleat"] == "base_cleat_pb01"
            and len(face["bolts"]) == 2
            and len(face["contacts"]) == 4
            and sum(row["active"] for row in face["contacts"]) == 2
            and len(compared["bolts"]) == 2,
            "PB-01 interface identity changed",
        )
        for bolt, comparison in zip(face["bolts"], compared["bolts"], strict=True):
            require(
                bolt["name"] == comparison["name"]
                and math.isclose(
                    bolt["axial_n"], comparison["axial_on_host_n"], abs_tol=1e-8
                )
                and math.isclose(
                    bolt["lateral_magnitude_n"],
                    comparison["lateral_on_host_magnitude_n"],
                    abs_tol=1e-8,
                )
                and bolt["force_on_host_xyz_n"] == comparison["force_on_host_xyz_n"],
                "PB-01 bolt action identity changed",
            )
            bolt_checks[bolt["name"]] = {
                "lateral_yield": comparison["conditional_lateral_yield"],
                "positive_axial_wood_annulus_reference_lbf": comparison[
                    "washer_positive_axial_reference_lbf"
                ],
                "positive_axial_wood_annulus_ratio": comparison[
                    "washer_positive_axial_ratio"
                ],
                "axial_steel_nut_ratio": None,
                "washer_metal_ratio": None,
                "group_action_factor": comparison["group_action_factor"],
                "host_load_to_grain_degrees": comparison["host_load_to_grain_degrees"],
                "cleat_load_to_grain_degrees": comparison[
                    "cleat_load_to_grain_degrees"
                ],
            }
        interfaces[family] = {
            "host": host,
            "cleat": face["cleat"],
            "resultant_on_host": face["resultant_on_host"],
            "resultant_on_cleat": face["resultant_on_cleat"],
            "bolts": face["bolts"],
            "contacts": face["contacts"],
            "checks": {
                "group_action": {
                    "status": "missing_oblique_row_method_and_force_sharing",
                    "ratio": None,
                },
                "face_bearing": {
                    "status": "missing_physical_patch_and_pressure_resistance",
                    "ratio": None,
                },
            },
        }

    member_checks = {
        key: {
            "reference_lbf": reference,
            "same_case_critical_section_demand_lbf": None,
            "utilization": None,
            "missing": MEMBER_REASONS[key],
        }
        for key, reference in members["components_lbf"].items()
    }
    return {
        "decision": "revise",
        "decision_scope": "development_only",
        "case": source["case"],
        "candidate": source["candidate"],
        "archive_sha256": source["archive_sha256"],
        "report_sha256": source["report_sha256"],
        "proxy_station_count": source["proxy_station_count"],
        "datum_xyz_mm": source["datum_xyz_mm"],
        "interfaces": interfaces,
        "bolt_checks": bolt_checks,
        "member_checks": member_checks,
        "cleat_check": {
            "gross_section_only": True,
            "maxima": cleat["maxima"],
            "reference_design_values_mpa": None,
            "net_section_stress_mpa": None,
            "torsional_stress_mpa": None,
            "combined_stress_mpa": None,
            "utilization": None,
        },
        "rail_stack": stack,
        "missing_checks": [
            "Delivered bolt root, steel axial/nut resistance, and group action for both two-bolt interfaces",
            "Washer metal stiffness, full wood annulus seating, preload, and bolt/contact partition",
            "Member critical-section directions, split/perpendicular-grain action, and adjustment factors",
            "Cleat bored net sections, torsion, combined stresses, verified wood strength, and adjustments",
            "Physical face-contact patches, bearing pressure and resistance",
            "Verified rail bolt and washer dimensions, complete threads, and receiving fit",
            "Connected all-station V4 topology and six authenticated same-configuration cases",
        ],
        "reason": "Keep the solid-cleat family for targeted revision; one provisional a12-left hybrid cannot establish a complete rail connection or V4 demand.",
        "advance_to_connected_v4": False,
        "joint_utilization": None,
        "design_pass": None,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(decide(), indent=2, sort_keys=True))
