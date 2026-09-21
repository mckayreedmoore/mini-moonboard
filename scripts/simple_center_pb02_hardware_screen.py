"""Authenticated conditional PB02 direct bolt-shaft and washer-demand screen."""

import hashlib
import json
import math
from pathlib import Path

from fea.reinforced_steel_capacity import KSI
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH_ORIGINAL = ROOT / (
    "fea/results/diagnostics/pb02-rear-clear-10333d2-v1/"
    "refinement/density-2x/report.json"
)
REPORT_PATH = REPORT_PATH_ORIGINAL
GEOMETRY_SOURCE = "scripts/simple_center_pb02_geometry.py"
CANDIDATE = "pb02-kerf-right-native-development-only"
EXPECTED_REPORT_SHA256 = (
    "4e8f9c193c225fe3d28002ab93ed3258d7560558ed089f27a49752adeea36023"
)
EXPECTED_MODEL_IDENTITY = (
    "6ff81b19cd60be0e2241af7350534de26b3fb68214de6d73fa80433221468b6f"
)
EXPECTED_SCOPE_FINGERPRINT = (
    "ce354d1ed95456b07e3c04cfe857f064d3987106124425391736c361d46dd773"
)
EXPECTED_GEOMETRY_FINGERPRINT = (
    "4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb"
)

NOMINAL_DIAMETER_MM = 6.35
WOOD_BEARING_MPA = 625 * KSI / 1000
DIAGNOSTIC_BORE_MM = 7.3
IDEAL_CAD_WASHER_OD_MM = 20.0


def _bolt(first, second, axis, edge, stack_name, grip_mm, trial_length_in, index=1):
    name = f"{edge}/bolt_{index}"
    return name, {
        "first": first,
        "second": second,
        "axis": axis,
        "edge": edge,
        "source_rows": [
            f"{name}/shear_1",
            f"{name}/shear_2",
            f"{name}/tension",
        ],
        "stack_name": stack_name,
        "wood_grip_mm": grip_mm,
        "trial_length_in": trial_length_in,
    }


BOLTS = dict(
    [
        _bolt(
            "shifted_right_post",
            "header_post_side_cleat",
            [1.0, 0.0, 0.0],
            "post_block",
            "post_cleat_1",
            177.8,
            8,
        ),
        _bolt(
            "shifted_right_post",
            "header_post_side_cleat",
            [1.0, 0.0, 0.0],
            "post_block",
            "post_cleat_2",
            177.8,
            8,
            2,
        ),
        _bolt(
            "header_post_side_cleat",
            "base_header",
            [0.0, 0.0, 1.0],
            "block_header",
            "cleat_header_1",
            182.0,
            8,
        ),
        _bolt(
            "header_post_side_cleat",
            "base_header",
            [0.0, 0.0, 1.0],
            "block_header",
            "cleat_header_2",
            182.0,
            8,
            2,
        ),
        _bolt(
            "base_header",
            "header_side_cleat",
            [0.0, 0.0, 1.0],
            "header_principal_block",
            "header_cleat",
            105.1,
            5,
        ),
        _bolt(
            "header_side_cleat",
            "base_principal_center_right",
            [1.0, 0.0, 0.0],
            "principal_block_principal",
            "cleat_principal",
            109.05,
            5,
        ),
        _bolt(
            "base_principal_center_right",
            "upright_side_cleat",
            [1.0, 0.0, 0.0],
            "principal_upright_block",
            "upright",
            127.0,
            6,
        ),
        _bolt(
            "upright_side_cleat",
            "rear_cleat",
            [0.0, -1.0, 0.0],
            "upright_rear_block",
            "cleat_link",
            99.7,
            5,
        ),
        _bolt(
            "rear_cleat",
            "shifted_right_post",
            [0.0, 1.0, 0.0],
            "rear_block_post",
            "post_low",
            127.0,
            6,
        ),
        _bolt(
            "rear_cleat",
            "shifted_right_post",
            [0.0, 1.0, 0.0],
            "rear_block_post",
            "post_high",
            127.0,
            6,
            2,
        ),
    ]
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _authenticate() -> tuple[dict, dict]:
    report = json.loads(REPORT_PATH.read_text())
    scope = report.get("diagnostic_scope", {})
    geometry_path = ROOT / GEOMETRY_SOURCE
    checks = (
        _sha256(REPORT_PATH) == EXPECTED_REPORT_SHA256,
        report.get("candidate") == CANDIDATE,
        scope.get("candidate") == CANDIDATE,
        scope.get("case") == "a12-forward",
        report.get("pb02_model_identity") == EXPECTED_MODEL_IDENTITY,
        scope.get("deterministic_input_fingerprint") == EXPECTED_SCOPE_FINGERPRINT,
        ACTIVE_FINGERPRINT == EXPECTED_GEOMETRY_FINGERPRINT,
        report.get("source_sha256", {}).get(GEOMETRY_SOURCE) == _sha256(geometry_path),
        report.get("numerically_accepted") is True,
        report.get("actual_joint_demands_qualified") is False,
    )
    if not all(checks):
        raise ValueError(
            "PB02 report, model, scope, or geometry authentication changed"
        )

    physical = report.get("physical_connection_forces", {})
    report_bolts = {name for name in physical if "/bolt_" in name}
    if report_bolts != set(BOLTS):
        raise ValueError("PB02 exact ten-bolt inventory changed")
    for name, expected in BOLTS.items():
        row = physical[name]
        for field in ("first", "second", "axis", "edge", "source_rows"):
            if row.get(field) != expected[field]:
                raise ValueError(f"PB02 ten-bolt inventory changed at {name}/{field}")

    return report, {
        "candidate": CANDIDATE,
        "case": "a12-forward",
        "report_sha256": EXPECTED_REPORT_SHA256,
        "model_identity": EXPECTED_MODEL_IDENTITY,
        "diagnostic_scope_fingerprint": EXPECTED_SCOPE_FINGERPRINT,
        "active_geometry_fingerprint": EXPECTED_GEOMETRY_FINGERPRINT,
        "numerically_accepted": True,
        "actual_joint_demands_qualified": False,
    }


def _a307_direct_capacities(grip_mm: float) -> dict:
    """Parameterize reinforced_steel_capacity.bolt_capacities for this diameter."""
    area = math.pi * NOMINAL_DIAMETER_MM**2 / 4
    reduction = 1 - max(0.0, grip_mm - 5 * NOMINAL_DIAMETER_MM) / 1.5875 * 0.01
    if reduction <= 0:
        raise ValueError("existing A307 long-grip method gives no positive reference")
    return {
        "gross_area_mm2": area,
        "long_grip_factor": reduction,
        "tension_asd_reference_n": 45 * KSI * reduction * area / 2,
        "single_shear_asd_reference_n": 27 * KSI * reduction * area / 2,
        "basis": (
            "Parameterized existing fea/reinforced_steel_capacity.py method: "
            "AISC 360-16 Table J3.2 A307, ASD Omega=2, gross area; both stresses "
            "reduced 1% per 1/16 in of grip beyond 5D"
        ),
        "long_grip_applicability_qualified": False,
    }


def _washer_demand(axial_tension_n: float) -> dict:
    demand = max(0.0, axial_tension_n)
    required_area = demand / WOOD_BEARING_MPA
    ideal_area = math.pi / 4 * (IDEAL_CAD_WASHER_OD_MM**2 - DIAGNOSTIC_BORE_MM**2)
    ideal_reference = WOOD_BEARING_MPA * ideal_area
    return {
        "head_n": demand,
        "nut_n": demand,
        "load_split_between_ends": False,
        "required_annular_area_each_end_mm2": required_area,
        "required_outer_diameter_formula_mm": (
            "sqrt(unsupported_diameter_mm^2 + 4*required_annular_area_each_end_mm2/pi)"
        ),
        "required_outer_diameter_at_7p3mm_unsupported_mm": math.sqrt(
            DIAGNOSTIC_BORE_MM**2 + 4 * required_area / math.pi
        ),
        "ideal_20mm_od_7p3mm_bore_sensitivity": {
            "outside_diameter_mm": IDEAL_CAD_WASHER_OD_MM,
            "unsupported_diameter_mm": DIAGNOSTIC_BORE_MM,
            "annular_area_mm2": ideal_area,
            "wood_bearing_reference_n": ideal_reference,
            "demand_ratio": demand / ideal_reference,
            "actual_washer_result": False,
        },
        "actual_washer_inputs": {
            "outside_diameter_mm": None,
            "inside_diameter_mm": None,
            "thickness_mm": None,
            "material": None,
        },
        "washer_qualified": False,
    }


def screen() -> dict:
    """Return one authenticated case; no hardware or complete-joint acceptance."""
    report, authentication = _authenticate()
    rows = []
    for name, bolt in BOLTS.items():
        source = report["physical_connection_forces"][name]
        tension = max(0.0, source["axial_along_installation_direction_n"])
        shear = source["transverse_shear_n"]
        capacities = _a307_direct_capacities(bolt["wood_grip_mm"])
        tension_ratio = tension / capacities["tension_asd_reference_n"]
        shear_ratio = shear / capacities["single_shear_asd_reference_n"]
        rows.append(
            {
                "name": name,
                "inventory": {
                    "first": bolt["first"],
                    "second": bolt["second"],
                    "axis": bolt["axis"],
                    "stack_name": bolt["stack_name"],
                    "nominal_diameter_mm": NOMINAL_DIAMETER_MM,
                    "wood_grip_mm": bolt["wood_grip_mm"],
                    "trial_length_in": bolt["trial_length_in"],
                    "product_specific_A307_status_qualified": False,
                },
                "demand": {
                    "axial_tension_n": tension,
                    "transverse_shear_n": shear,
                },
                "direct_shaft_comparator": capacities
                | {
                    "tension_ratio": tension_ratio,
                    "shear_ratio": shear_ratio,
                    "conservative_linear_interaction_ratio": (
                        tension_ratio + shear_ratio
                    ),
                    "conditional_comparator_only": True,
                    "qualified": False,
                },
                "washer_demand_each_end": _washer_demand(tension),
            }
        )

    governing = max(
        rows,
        key=lambda row: row["direct_shaft_comparator"][
            "conservative_linear_interaction_ratio"
        ],
    )
    return {
        "status": "authenticated_one_case_conditional_hardware_screen",
        "authentication": authentication,
        "bolts": rows,
        "governing_direct_shaft_comparator": {
            "name": governing["name"],
            "conservative_linear_interaction_ratio": governing[
                "direct_shaft_comparator"
            ]["conservative_linear_interaction_ratio"],
        },
        "unqualified": [
            "product-specific A307 status",
            "thread root, runout, and bearing location",
            "applicability of the existing steel long-grip reduction to this wood joint",
            "actual washer ID, OD, thickness, material, tolerances, and metal bending",
            "nut proof strength, thread engagement, and stripping",
            "installation preload",
            "prying and eccentric bolt-axis tension",
            "remaining five load cases and qualified joint demands",
        ],
        "qualified": False,
        "procurement_released": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
