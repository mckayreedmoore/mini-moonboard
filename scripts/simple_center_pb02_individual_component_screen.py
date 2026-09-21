"""Authenticated conditional PB02 upright/link individual-bolt screen."""

import hashlib
import json
import math
from pathlib import Path

from mini_moonboard.bolted_wood_wood_yield import (
    dowel_bending_yield_moment_lb_in,
    wood_wood_single_shear_reference,
)
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / (
    "fea/results/diagnostics/pb02-corrected-a12-forward-z202-link328p5-v1/report.json"
)
CANDIDATE = "pb02-kerf-right-native-development-only"
EXPECTED_GEOMETRY_FINGERPRINT = (
    "06f0cd1a1754d26fb2ff74cc2eb7da8eed80fbbea5cc84d7627ae8ff07d61387"
)
EXPECTED_REPORT_SHA256 = (
    "6e5fe950f796e86c17fc575899c4e5b3a3314166e1fc3fafc81c96e530f1c7df"
)
EXPECTED_MODEL_IDENTITY = (
    "c6981acec1a15913cd792189f5bb2d7081d0b2afe9a7509503e974d0aca94cc3"
)
EXPECTED_SCOPE_FINGERPRINT = (
    "c90bfe845d12bfed4a2d4a4b657cb26f34ba0e6b95af43fb8800596a723020d3"
)
GEOMETRY_SOURCE = "scripts/simple_center_pb02_geometry.py"
N_PER_LBF = 4.4482216152605
MM_PER_IN = 25.4
NOMINAL_DIAMETER_MM = 6.35
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")

CONNECTIONS = {
    "principal_upright_block/bolt_1": {
        "first": "base_principal_center_right",
        "second": "upright_side_cleat",
        "axis": [1.0, 0.0, 0.0],
        "source_rows": [
            "principal_upright_block/bolt_1/shear_1",
            "principal_upright_block/bolt_1/shear_2",
            "principal_upright_block/bolt_1/tension",
        ],
        "bearing_lengths_mm": [38.1, 88.9],
        "members": {
            "base_principal_center_right": {
                "grain": [0.0, 0.6427876096865427, 0.7660444431189752],
                "transverse": [0.0, -0.7660444431189752, 0.6427876096865427],
                "grain_ends_mm": {"negative": 85.072, "positive": 2421.095},
                "transverse_edges_mm": {"negative": 129.685, "positive": 10.015},
            },
            "upright_side_cleat": {
                "grain": [0.0, 0.0, 1.0],
                "transverse": [0.0, 1.0, 0.0],
                "grain_ends_mm": {"negative": 79.0, "positive": 104.0},
                "transverse_edges_mm": {"negative": 31.2, "positive": 30.4},
            },
        },
    },
    "upright_rear_block/bolt_1": {
        "first": "upright_side_cleat",
        "second": "rear_cleat",
        "axis": [0.0, -1.0, 0.0],
        "source_rows": [
            "upright_rear_block/bolt_1/shear_1",
            "upright_rear_block/bolt_1/shear_2",
            "upright_rear_block/bolt_1/tension",
        ],
        "bearing_lengths_mm": [61.6, 38.1],
        "members": {
            "upright_side_cleat": {
                "grain": [0.0, 0.0, 1.0],
                "transverse": [1.0, 0.0, 0.0],
                "grain_ends_mm": {"negative": 51.5, "positive": 131.5},
                "transverse_edges_mm": {"negative": 44.45, "positive": 44.45},
            },
            "rear_cleat": {
                "grain": [0.0, 0.0, 1.0],
                "transverse": [1.0, 0.0, 0.0],
                "grain_ends_mm": {"negative": 328.5, "positive": 131.5},
                "transverse_edges_mm": {"negative": 44.45, "positive": 44.45},
            },
        },
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dot(first, second) -> float:
    return sum(a * b for a, b in zip(first, second))


def _magnitude(vector) -> float:
    return math.sqrt(_dot(vector, vector))


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
        report.get("pb02_model_identity") == EXPECTED_MODEL_IDENTITY,
        scope.get("deterministic_input_fingerprint") == EXPECTED_SCOPE_FINGERPRINT,
        report.get("source_sha256", {}).get(GEOMETRY_SOURCE) == _sha256(geometry_path),
        report.get("numerically_accepted") is True,
        report.get("actual_joint_demands_qualified") is False,
    )
    if not all(checks):
        raise ValueError("PB02 report, geometry, scope, or numerical identity changed")
    return report, {
        "candidate": CANDIDATE,
        "case": "a12-forward",
        "active_geometry_fingerprint": ACTIVE_FINGERPRINT,
        "report_sha256": EXPECTED_REPORT_SHA256,
        "model_identity": EXPECTED_MODEL_IDENTITY,
        "diagnostic_scope_fingerprint": EXPECTED_SCOPE_FINGERPRINT,
        "numerically_accepted": True,
        "actual_joint_demands_qualified": False,
    }


def _directional_distances(distances, component, loaded_minimum, unloaded_minimum):
    loaded_direction = "positive" if component > 0 else "negative"
    unloaded_direction = "negative" if component > 0 else "positive"

    def result(direction, minimum):
        distance = distances[direction]
        return {
            "direction": direction,
            "distance_mm": distance,
            "minimum_mm": minimum,
            "reserve_mm": distance - minimum,
            "passes_nominal_minimum": distance >= minimum,
        }

    return {
        "loaded": result(loaded_direction, loaded_minimum),
        "unloaded": result(unloaded_direction, unloaded_minimum),
    }


def _placement(member_spec, force):
    grain_component = _dot(force, member_spec["grain"])
    transverse_component = _dot(force, member_spec["transverse"])
    ends = _directional_distances(
        member_spec["grain_ends_mm"],
        grain_component,
        7 * NOMINAL_DIAMETER_MM,
        4 * NOMINAL_DIAMETER_MM,
    )
    edges = _directional_distances(
        member_spec["transverse_edges_mm"],
        transverse_component,
        4 * NOMINAL_DIAMETER_MM,
        1.5 * NOMINAL_DIAMETER_MM,
    )
    edges["ten_mm_edge_is_loaded"] = math.isclose(
        edges["loaded"]["distance_mm"], 10.015, abs_tol=1e-9
    )
    return {
        "force_components_n": {
            "parallel_to_grain": grain_component,
            "transverse_to_grain": transverse_component,
        },
        "grain_ends": ends,
        "transverse_edges": edges,
        "geometry_factor": 1.0,
    }


def _root_case(root_diameter_in, lengths_mm, angles, lateral_demand_n):
    angle_factor = 1 + 0.25 * max(angles) / 90
    reduction = (10 * root_diameter_in + 0.5) * angle_factor
    yield_moment = dowel_bending_yield_moment_lb_in(
        bending_yield_strength_psi=45_000,
        effective_diameter_in=root_diameter_in,
    )
    lengths_in = [length / MM_PER_IN for length in lengths_mm]
    result = wood_wood_single_shear_reference(
        main_bearing_length_in=lengths_in[0],
        side_bearing_length_in=lengths_in[1],
        main_load_to_grain_degrees=angles[0],
        side_load_to_grain_degrees=angles[1],
        main_bolt_axis_parallel_to_grain=False,
        side_bolt_axis_parallel_to_grain=False,
        bolt_full_body_diameter_in=0.25,
        bolt_thread_root_diameter_in=root_diameter_in,
        main_thread_bearing_length_in=lengths_in[0],
        side_thread_bearing_length_in=lengths_in[1],
        bolt_bending_yield_moment_lb_in=yield_moment,
        bolt_bending_yield_strength_psi=45_000,
        gap_in=0.0,
        reduction_terms=dict.fromkeys(MODES, reduction),
    )
    adjusted_reference_n = result["reference_lateral_lbf"] * N_PER_LBF
    return {
        "root_diameter_in": root_diameter_in,
        "effective_bearing_diameter_in": result["effective_bearing_diameter_in"],
        "bearing_lengths_mm": lengths_mm,
        "bearing_psi": {
            "first_member": result["main_bearing_psi"],
            "second_member": result["side_bearing_psi"],
        },
        "yield_moment_lb_in": yield_moment,
        "reduction_terms": dict.fromkeys(MODES, reduction),
        "yield_values_lbf": result["yield_values_lbf"],
        "reference_values_lbf": result["reference_values_lbf"],
        "governing_mode": result["governing_mode"],
        "unadjusted_reference_lbf": result["reference_lateral_lbf"],
        "adjusted_reference_n": adjusted_reference_n,
        "demand_ratio": lateral_demand_n / adjusted_reference_n,
        "adjustments": {
            "CD": 1.0,
            "CM": 1.0,
            "Ct": 1.0,
            "Cdi": 1.0,
            "Ctn": 1.0,
            "CDelta": 1.0,
            "Cg": 1.0,
        },
    }


def _connection(report, name, spec):
    row = report.get("physical_connection_forces", {}).get(name)
    if row is None:
        raise ValueError(f"Missing authenticated physical force: {name}")
    expected = {key: spec[key] for key in ("first", "second", "axis", "source_rows")}
    if any(row.get(key) != value for key, value in expected.items()):
        raise ValueError(f"{name}: force ownership changed")
    first_force = row["force_on_first_xyz_n"]
    second_force = row["force_on_second_xyz_n"]
    if any(abs(a + b) > 1e-9 for a, b in zip(first_force, second_force)):
        raise ValueError(f"{name}: action/reaction ownership changed")
    axial = _dot(first_force, spec["axis"])
    lateral = [force - axial * axis for force, axis in zip(first_force, spec["axis"])]
    lateral_magnitude = _magnitude(lateral)
    if not (
        math.isclose(axial, row["axial_along_installation_direction_n"], abs_tol=1e-9)
        and math.isclose(lateral_magnitude, row["transverse_shear_n"], abs_tol=1e-9)
    ):
        raise ValueError(f"{name}: reported axial/lateral decomposition changed")

    members = list(spec["members"])
    forces = (first_force, second_force)
    angles = []
    placement = {}
    for member, force in zip(members, forces):
        grain = spec["members"][member]["grain"]
        cosine = abs(_dot(lateral, grain)) / lateral_magnitude
        angles.append(math.degrees(math.acos(min(1.0, cosine))))
        placement[member] = _placement(spec["members"][member], force)

    roots = {
        "root_0p189_in": _root_case(
            0.189, spec["bearing_lengths_mm"], angles, lateral_magnitude
        ),
        "root_0p180_in": _root_case(
            0.180, spec["bearing_lengths_mm"], angles, lateral_magnitude
        ),
    }
    return {
        "force_ownership": expected
        | {"force_on_first_xyz_n": first_force, "force_on_second_xyz_n": second_force},
        "demand": {"axial_n": max(0.0, axial), "lateral_n": lateral_magnitude},
        "load_to_grain_degrees": dict(zip(members, angles)),
        "placement": placement,
        "fastener_group": {
            "fastener_count": 1,
            "group_factor": 1.0,
            "group_action_applicable": False,
        },
        "root_sensitivities": roots,
        "washer": {
            "demand_n": max(0.0, axial),
            "qualified": False,
            "reason": (
                "Zero means no tensile washer demand in this case only; exact washer "
                "metal, dimensions, bolt tension, preload, and prying are unqualified."
            ),
        },
    }


def screen() -> dict:
    report, authentication = _authenticate()
    return {
        "authentication": authentication,
        "basis": {
            "edition": "2024 NDS with current errata",
            "wood": "conditional dry, unincised DF-L No. 2",
            "specific_gravity": 0.50,
            "bolt_bending_yield_strength_psi": 45_000,
            "nominal_bolt_diameter_in": 0.25,
            "thread_condition": "root through both wood bearing lengths",
            "connection_form": "two solid-wood members, one shear plane",
        },
        "connections": {
            name: _connection(report, name, spec) for name, spec in CONNECTIONS.items()
        },
        "unqualified": [
            "local_crossed_bore_splitting",
            "nearby_bore_interaction_and_stress_concentration",
            "net_section_combined_mechanics",
            "washer_metal_bending_and_bearing",
            "bolt_tension_nut_threads_preload_and_prying",
            "exact_hardware_root_thread_runout_and_bearing_regions",
            "face_contact_bearing_distribution",
            "fabrication_tolerances",
            "other_five_load_cases",
            "complete_joint_resistance",
        ],
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
