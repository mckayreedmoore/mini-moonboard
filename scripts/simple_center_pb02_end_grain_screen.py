"""Conditional PB02 block/header end-grain single-bolt yield screen."""

import hashlib
import importlib
import json
import math
import sys
from pathlib import Path

from fea.dowel_yield import single_shear
from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi
from mini_moonboard.bolted_wood_wood_yield import (
    dowel_bending_yield_moment_lb_in,
)

MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
N_PER_LBF = 4.4482216152605
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_REPORT = (
    ROOT / "fea/results/diagnostics/pb02-rear-clear-10333d2-v1/"
    "refinement/density-2x/report.json"
)
CANDIDATE = "pb02-kerf-right-native-development-only"
GEOMETRY_SOURCE = "scripts/simple_center_pb02_geometry.py"
EXPECTED_GEOMETRY_FINGERPRINT = (
    "4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb"
)
EXPECTED_REPORT_SHA256 = (
    "4e8f9c193c225fe3d28002ab93ed3258d7560558ed089f27a49752adeea36023"
)
EXPECTED_MODEL_IDENTITY = (
    "6ff81b19cd60be0e2241af7350534de26b3fb68214de6d73fa80433221468b6f"
)
EXPECTED_SCOPE_FINGERPRINT = (
    "ce354d1ed95456b07e3c04cfe857f064d3987106124425391736c361d46dd773"
)


def _active_geometry_fingerprint() -> str:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    geometry = importlib.import_module("scripts.simple_center_pb02_geometry")
    return geometry.ACTIVE_FINGERPRINT


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _authenticated_report() -> tuple[dict, dict]:
    report = json.loads(EVIDENCE_REPORT.read_text())
    scope = report.get("diagnostic_scope", {})
    stiffness = scope.get("stiffness_selection", {})
    selected = stiffness.get("exact_selected_values", {})
    contact = stiffness.get("contact_model", {})
    geometry_path = ROOT / GEOMETRY_SOURCE
    checks = (
        _sha256(EVIDENCE_REPORT) == EXPECTED_REPORT_SHA256,
        report.get("candidate") == CANDIDATE,
        scope.get("candidate") == CANDIDATE,
        scope.get("case") == "a12-forward",
        report.get("parameters", {}).get("hold") == "A12",
        contact.get("grid_resolution") == [8, 8],
        selected.get("face_normal_total_per_interface_n_per_mm") == 2000.0,
        report.get("pb02_model_identity") == EXPECTED_MODEL_IDENTITY,
        scope.get("deterministic_input_fingerprint") == EXPECTED_SCOPE_FINGERPRINT,
        _active_geometry_fingerprint() == EXPECTED_GEOMETRY_FINGERPRINT,
        report.get("source_sha256", {}).get(GEOMETRY_SOURCE) == _sha256(geometry_path),
        report.get("numerically_accepted") is True,
        report.get("actual_joint_demands_qualified") is False,
        report.get("qualified_for_design") is False,
        report.get("drilling_released") is False,
        report.get("fabrication_released") is False,
        report.get("structural_released", False) is False,
        scope.get("developmental_only") is True,
        scope.get("qualified_for_design") is False,
        scope.get("actual_joint_demands_qualified") is False,
        scope.get("resistance_checked") is False,
        scope.get("acceptance") is False,
        scope.get("drilling_released") is False,
        scope.get("fabrication_released") is False,
    )
    if not all(checks):
        raise ValueError("PB02 end-grain evidence authentication changed")
    return report, {
        "candidate": CANDIDATE,
        "case": "a12-forward",
        "contact_grid": [8, 8],
        "mean_contact_total_n_per_mm": 2000.0,
        "report_sha256": EXPECTED_REPORT_SHA256,
        "model_identity": EXPECTED_MODEL_IDENTITY,
        "diagnostic_scope_fingerprint": EXPECTED_SCOPE_FINGERPRINT,
        "active_geometry_fingerprint": EXPECTED_GEOMETRY_FINGERPRINT,
        "numerically_accepted": True,
        "no_release": True,
    }


def root_case(root_diameter_in: float, demand_n: float) -> dict:
    """Apply the 2024 NDS axis-parallel main-member and end-grain route.

    This is a conditional single-fastener component calculation. It does not
    qualify group action, geometry factors, splitting, hardware, or the joint.
    """
    grain_angle_factor = 1.25
    reduction = (10 * root_diameter_in + 0.5) * grain_angle_factor
    bearing_psi = dfl_dowel_bearing_psi(root_diameter_in, 90)
    yield_moment = dowel_bending_yield_moment_lb_in(
        bending_yield_strength_psi=45_000,
        effective_diameter_in=root_diameter_in,
    )
    result = single_shear(
        main_length_in=143.9 / 25.4,
        side_length_in=1.5,
        main_bearing_lb_in=bearing_psi * root_diameter_in,
        side_bearing_lb_in=bearing_psi * root_diameter_in,
        main_yield_moment_lb_in=yield_moment,
        side_yield_moment_lb_in=yield_moment,
        gap_in=0,
        reduction_terms=dict.fromkeys(MODES, reduction),
    )
    end_grain_factor = 0.67
    adjusted_n = result["reference_lateral_lbf"] * end_grain_factor * N_PER_LBF
    return {
        "root_diameter_in": root_diameter_in,
        "dfl_specific_gravity": 0.5,
        "bearing_psi": bearing_psi,
        "bolt_bending_yield_strength_psi": 45_000,
        "yield_moment_lb_in": yield_moment,
        "reduction_term": reduction,
        "governing_mode": result["governing_mode"],
        "reference_lateral_lbf": result["reference_lateral_lbf"],
        "end_grain_factor": end_grain_factor,
        "end_grain_adjusted_reference_n": adjusted_n,
        "single_case_demand_n": demand_n,
        "demand_ratio": demand_n / adjusted_n,
        "minimum_remaining_adjustment_product": demand_n / adjusted_n,
        "limits": (
            "Conditional 2024 NDS single-bolt yield reference only; Ceg applied, "
            "CD=CM=Ct=Cdi=Ctn=1 assumed, Cg and CDelta unresolved; no group, "
            "splitting, local-ligament, hardware, joint, or drilling qualification"
        ),
    }


def screen() -> dict:
    report, authentication = _authenticated_report()
    forces = report["physical_connection_forces"]
    bolt_rows = [forces[f"block_header/bolt_{index}"] for index in (1, 2)]
    demand_by_bolt = {
        f"bolt_{index}": row["transverse_shear_n"]
        for index, row in enumerate(bolt_rows, 1)
    }
    points = [row["point"] for row in bolt_rows]
    pair_vector = [points[1][axis] - points[0][axis] for axis in range(2)]
    pair_spacing_mm = math.hypot(*pair_vector)
    pair_unit = [value / pair_spacing_mm for value in pair_vector]
    demand_angles = {}
    for index, row in enumerate(bolt_rows, 1):
        force = row["force_on_first_xyz_n"][:2]
        magnitude = math.hypot(*force)
        cosine = (
            abs(sum(force[axis] * pair_unit[axis] for axis in range(2))) / magnitude
        )
        demand_angles[f"bolt_{index}"] = math.degrees(math.acos(min(1.0, cosine)))

    governing_demand = max(demand_by_bolt.values())
    cases = {
        "typical_root": root_case(0.189, governing_demand),
        "smaller_root_sensitivity": root_case(0.180, governing_demand),
    }
    for case in cases.values():
        reference = case["end_grain_adjusted_reference_n"]
        case["individual_bolt_demand_ratios"] = {
            name: demand / reference for name, demand in demand_by_bolt.items()
        }
    return {
        "candidate": CANDIDATE,
        "interface": "block_header",
        "disposition": "retain_current_z_grain_block_for_development",
        "evidence_report": str(EVIDENCE_REPORT.relative_to(ROOT)),
        "authentication": authentication,
        "demand_by_bolt_n": demand_by_bolt,
        "pair_geometry": {
            "spacing_mm": pair_spacing_mm,
            "spacing_nominal_diameters": pair_spacing_mm / 6.35,
            "force_angle_from_pair_line_degrees": demand_angles,
        },
        "adjustments": {
            "end_grain_factor": 0.67,
            "geometry_factor": 1.0,
            "group_factor": None,
            "group_factor_applicable": False,
            "group_factor_reason": (
                "The two lateral forces are neither mutually parallel nor aligned "
                "with the bolt-pair line; they are not one NDS row in the direction "
                "of load. Individual single-bolt component checks use n=1."
            ),
        },
        "cases": cases,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(screen(), indent=2, sort_keys=True))
