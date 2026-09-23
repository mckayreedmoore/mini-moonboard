"""Validate the bounded hardware selection without claiming joint capacity."""

import argparse
import json
from math import isclose, pi
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / "docs/barrel-nut-selected-hardware.json"
STATIONS = ROOT / "docs/barrel-nut-stations.json"
SCHEMA = "owner_barrel_selected_hardware/v1"
MEASUREMENT_SCHEMA = "owner_barrel_selected_hardware_measurements/v1"
EXPECTED_BOLT_QUANTITIES = {88.9: 8, 114.3: 24, 127.0: 4, 165.1: 12}
REPLACED_PRINCIPAL_PAIRS = {
    "barrel_center_clip_split_base_center_left_1_bolt",
    "barrel_center_clip_split_base_center_right_1_bolt",
}
VERTICAL_PRINCIPAL_PAIRS = tuple(
    {
        "pair_id": f"vertical_principal_{side}_{index}",
        "station": f"vertical_principal_header_{side}",
        "selected_bolt_product": "1456BHT5",
        "selected_bolt_nominal_length_mm": 88.9,
        "selected_barrel_product": "JCD14201606NL ZN",
        "selected_washer_product": "33857",
    }
    for side in ("left", "right")
    for index in (1, 2)
)
SELECTED_BOLT_BY_MODELED_LENGTH = {
    88.9: ("1456BHT5", 88.9),
    114.3: ("1472BHT5", 114.3),
    127.0: ("1480BHT5", 127.0),
    152.4: ("14104BHT5", 165.1),
}
ACTUAL_FIELDS = (
    "bolt_length_mm",
    "male_complete_start_mm",
    "male_complete_end_mm",
    "installed_thread_axis_from_head_mm",
    "female_complete_start_from_axis_mm",
    "female_complete_end_from_axis_mm",
    "bore_cap_from_head_mm",
    "barrel_od_min_mm",
    "barrel_od_max_mm",
    "finished_bore_min_mm",
    "finished_bore_max_mm",
    "axis_offset_mm",
)
ACCEPTANCE_FIELDS = (
    "required_engagement_mm",
    "minimum_tip_clearance_mm",
    "minimum_insertion_clearance_mm",
    "maximum_insertion_clearance_mm",
    "maximum_axis_offset_mm",
)


def load_selection(path=SELECTION):
    return json.loads(Path(path).read_text())


def annular_area_mm2(outer_diameter_mm, inner_diameter_mm):
    if outer_diameter_mm <= inner_diameter_mm or inner_diameter_mm < 0:
        raise ValueError("washer diameters must define a positive annulus")
    return pi / 4 * (outer_diameter_mm**2 - inner_diameter_mm**2)


def measurement_template(stations_path=STATIONS):
    """Return one blank, selected-product-bound measurement row per barrel pair."""
    stations = json.loads(Path(stations_path).read_text())["stations"]
    rows = []
    for station, record in sorted(stations.items()):
        for pair_id, bolt in sorted(record["bolts"].items()):
            if pair_id in REPLACED_PRINCIPAL_PAIRS:
                continue
            modeled_length = round(float(bolt["length_mm"]), 1)
            try:
                product, selected_length = SELECTED_BOLT_BY_MODELED_LENGTH[
                    modeled_length
                ]
            except KeyError as exc:
                raise ValueError(
                    f"{pair_id}: unsupported modeled bolt length {modeled_length}"
                ) from exc
            rows.append(
                {
                    "pair_id": pair_id,
                    "station": station,
                    "selected_bolt_product": product,
                    "selected_bolt_nominal_length_mm": selected_length,
                    "selected_barrel_product": "JCD14201606NL ZN",
                    "selected_washer_product": "33857",
                    "actual": {field: None for field in ACTUAL_FIELDS},
                    "acceptance": {field: None for field in ACCEPTANCE_FIELDS},
                }
            )
    rows.extend(
        {
            **row,
            "actual": {field: None for field in ACTUAL_FIELDS},
            "acceptance": {field: None for field in ACCEPTANCE_FIELDS},
        }
        for row in VERTICAL_PRINCIPAL_PAIRS
    )
    if len(rows) != 48 or len({row["pair_id"] for row in rows}) != 48:
        raise ValueError("vertical-center candidate does not contain 48 unique pairs")
    counts = {}
    for row in rows:
        length = row["selected_bolt_nominal_length_mm"]
        counts[length] = counts.get(length, 0) + 1
    if counts != EXPECTED_BOLT_QUANTITIES:
        raise ValueError("station register no longer matches selected bolt inventory")
    return {"schema": MEASUREMENT_SCHEMA, "pairs": rows}


def _range(name, low, high):
    if low > high:
        raise ValueError(f"{name}: minimum exceeds maximum")


def evaluate_pair(row):
    """Evaluate measured fit/engagement only; never infer complete-joint strength."""
    actual = row["actual"]
    acceptance = row["acceptance"]
    missing = [
        f"actual.{field}" for field in ACTUAL_FIELDS if actual.get(field) is None
    ] + [
        f"acceptance.{field}"
        for field in ACCEPTANCE_FIELDS
        if acceptance.get(field) is None
    ]
    result = {
        "pair_id": row["pair_id"],
        "station": row["station"],
        "status": "EVIDENCE_BLOCKED",
        "missing": missing,
        "failures": [],
        "metrics": {},
    }
    if missing:
        return result

    _range(
        f"{row['pair_id']} male complete-thread interval",
        actual["male_complete_start_mm"],
        actual["male_complete_end_mm"],
    )
    _range(
        f"{row['pair_id']} female complete-thread interval",
        actual["female_complete_start_from_axis_mm"],
        actual["female_complete_end_from_axis_mm"],
    )
    _range(
        f"{row['pair_id']} barrel OD",
        actual["barrel_od_min_mm"],
        actual["barrel_od_max_mm"],
    )
    _range(
        f"{row['pair_id']} finished bore",
        actual["finished_bore_min_mm"],
        actual["finished_bore_max_mm"],
    )
    _range(
        f"{row['pair_id']} accepted insertion clearance",
        acceptance["minimum_insertion_clearance_mm"],
        acceptance["maximum_insertion_clearance_mm"],
    )
    if any(value < 0 for value in acceptance.values()):
        raise ValueError(f"{row['pair_id']}: acceptance limits must be nonnegative")
    nonnegative_actual = (
        "bolt_length_mm",
        "male_complete_start_mm",
        "male_complete_end_mm",
        "installed_thread_axis_from_head_mm",
        "bore_cap_from_head_mm",
        "barrel_od_min_mm",
        "barrel_od_max_mm",
        "finished_bore_min_mm",
        "finished_bore_max_mm",
        "axis_offset_mm",
    )
    if any(actual[field] < 0 for field in nonnegative_actual):
        raise ValueError(f"{row['pair_id']}: physical dimensions must be nonnegative")

    female_start = (
        actual["installed_thread_axis_from_head_mm"]
        + actual["female_complete_start_from_axis_mm"]
    )
    female_end = (
        actual["installed_thread_axis_from_head_mm"]
        + actual["female_complete_end_from_axis_mm"]
    )
    overlap = max(
        0.0,
        min(actual["male_complete_end_mm"], female_end)
        - max(actual["male_complete_start_mm"], female_start),
    )
    tip_clearance = actual["bore_cap_from_head_mm"] - actual["bolt_length_mm"]
    minimum_fit_clearance = actual["finished_bore_min_mm"] - actual["barrel_od_max_mm"]
    maximum_fit_clearance = actual["finished_bore_max_mm"] - actual["barrel_od_min_mm"]
    axis_margin = acceptance["maximum_axis_offset_mm"] - actual["axis_offset_mm"]
    result["metrics"] = {
        "usable_complete_thread_overlap_mm": overlap,
        "tip_clearance_mm": tip_clearance,
        "minimum_insertion_diametral_clearance_mm": minimum_fit_clearance,
        "maximum_insertion_diametral_clearance_mm": maximum_fit_clearance,
        "axis_alignment_margin_mm": axis_margin,
    }
    checks = (
        (
            overlap >= acceptance["required_engagement_mm"],
            "INSUFFICIENT_COMPLETE_THREAD_ENGAGEMENT",
        ),
        (
            tip_clearance >= acceptance["minimum_tip_clearance_mm"],
            "INSUFFICIENT_TIP_CLEARANCE",
        ),
        (
            minimum_fit_clearance >= acceptance["minimum_insertion_clearance_mm"],
            "INSERTION_FIT_TOO_TIGHT",
        ),
        (
            maximum_fit_clearance <= acceptance["maximum_insertion_clearance_mm"],
            "INSERTION_FIT_TOO_LOOSE",
        ),
        (axis_margin >= 0, "AXIS_MISALIGNMENT_EXCEEDS_LIMIT"),
    )
    result["failures"] = [name for passed, name in checks if not passed]
    result["status"] = (
        "NO_GO_MEASURED_FIT" if result["failures"] else "PASS_GEOMETRY_ONLY"
    )
    return result


def evaluate_measurements(payload):
    if payload.get("schema") != MEASUREMENT_SCHEMA:
        raise ValueError("selected-hardware measurement schema changed")
    expected = measurement_template()["pairs"]
    expected_by_id = {row["pair_id"]: row for row in expected}
    supplied = payload.get("pairs", [])
    supplied_ids = [row.get("pair_id") for row in supplied]
    if len(supplied_ids) != 48 or len(set(supplied_ids)) != 48:
        raise ValueError("measurements must contain 48 unique pair IDs")
    if set(supplied_ids) != set(expected_by_id):
        raise ValueError("measurement pair IDs do not match the station register")
    for row in supplied:
        expected_row = expected_by_id[row["pair_id"]]
        for field in (
            "station",
            "selected_bolt_product",
            "selected_bolt_nominal_length_mm",
            "selected_barrel_product",
            "selected_washer_product",
        ):
            if row.get(field) != expected_row[field]:
                raise ValueError(f"{row['pair_id']}: selected hardware binding changed")
    results = [evaluate_pair(row) for row in supplied]
    statuses = {row["status"] for row in results}
    if "NO_GO_MEASURED_FIT" in statuses:
        status = "NO_GO_MEASURED_FIT"
    elif "EVIDENCE_BLOCKED" in statuses:
        status = "EVIDENCE_BLOCKED"
    else:
        status = "PASS_GEOMETRY_ONLY"
    return {
        "schema": MEASUREMENT_SCHEMA,
        "status": status,
        "pair_count": len(results),
        "results": results,
        "structural_released": False,
        "diy_ready": False,
        "limits": (
            "A geometry-only pass does not qualify barrel metal, crossed-bore "
            "wood, joint stiffness, signed response, retained bolts, or panels."
        ),
    }


def validate_selection(data):
    if data["schema"] != SCHEMA:
        raise ValueError("selected-hardware schema changed")
    quantities = {row["nominal_length_mm"]: row["quantity"] for row in data["bolts"]}
    if quantities != EXPECTED_BOLT_QUANTITIES or sum(quantities.values()) != 48:
        raise ValueError("selected bolt inventory does not cover 48 barrel pairs")
    if data["barrel"]["quantity"] != 48:
        raise ValueError("selected barrel inventory does not cover 48 barrel pairs")
    if sum(row["quantity"] for row in data["washers"]) != 48:
        raise ValueError("selected washer inventory does not cover 48 barrel pairs")
    if any(row["minimum_tensile_psi"] < 120000 for row in data["bolts"]):
        raise ValueError("selected bolt strength fell below SAE J429 Grade 5")
    decision = data["decision"]
    if decision["current_as_drawn_six_inch_stack"] != "FAIL_CLOSED_NOT_QUALIFIED":
        raise ValueError("rejected six-inch stack was reopened")
    if decision["complete_direct_cross_dowel_design"] != "EVIDENCE_BLOCKED":
        raise ValueError("unqualified complete-joint design was overclaimed")
    if any(
        decision[key]
        for key in ("diy_ready", "fabrication_released", "structural_released")
    ):
        raise ValueError("hardware screen cannot release the design")
    if data["barrel"]["controlled_strength_n"] is not None:
        raise ValueError("STAFAST barrel strength is not controlled by public evidence")
    if data["stack_screen"]["six_and_half_required_tip_clearance_mm"] is not None:
        raise ValueError("final bore depth needs a frozen machining clearance")
    calculated = selected_stack_arithmetic(data)
    recorded = data["stack_screen"]
    for field, value in calculated.items():
        if not isclose(recorded[field], value, abs_tol=1e-9):
            raise ValueError(f"selected stack calculation drifted: {field}")
    return data


def selected_stack_arithmetic(data):
    """Bind critical reach checks to selected bolt and washer tolerances."""
    inputs = data["stack_screen"]["calculation_inputs"]
    washer = data["washers"][0]
    bolts = {row["nominal_length_mm"]: row for row in data["bolts"]}
    wood_to_axis = (
        inputs["modeled_outer_rail_axis_reach_from_head_mm"]
        - inputs["modeled_washer_thickness_mm"]
    )
    wood_to_bore_cap = (
        inputs["modeled_outer_rail_bore_cap_from_head_mm"]
        - inputs["modeled_washer_thickness_mm"]
    )
    rejected_min = (
        inputs["rejected_six_in_nominal_length_mm"]
        + inputs["rejected_six_in_length_tolerance_mm"][0]
    )
    rejected_tip = rejected_min - (wood_to_axis + washer["thickness_max_mm"])
    selected = bolts[165.1]
    selected_min = selected["nominal_length_mm"] + selected["length_tolerance_mm"][0]
    selected_max = selected["nominal_length_mm"] + selected["length_tolerance_mm"][1]
    selected_tip = selected_min - (wood_to_axis + washer["thickness_max_mm"])
    bore_extension = selected_max - (wood_to_bore_cap + washer["thickness_min_mm"])
    five = bolts[127.0]
    five_clearance = (
        inputs["modeled_five_in_tip_clearance_mm"]
        + washer["thickness_min_mm"]
        - inputs["modeled_washer_thickness_mm"]
        - five["length_tolerance_mm"][1]
    )
    tip_allowance = inputs["two_pitch_tip_allowance_mm"]
    return {
        "rejected_six_in_minimum_physical_tip_past_axis_mm": rejected_tip,
        "rejected_six_in_minimum_complete_thread_past_axis_mm": (
            rejected_tip - tip_allowance
        ),
        "six_and_half_minimum_physical_tip_past_axis_mm": selected_tip,
        "six_and_half_minimum_complete_thread_past_axis_mm": (
            selected_tip - tip_allowance
        ),
        "six_and_half_minimum_added_bore_depth_to_zero_clearance_mm": (bore_extension),
        "six_and_half_provisional_2mm_clearance_added_bore_depth_mm": (
            bore_extension + 2.0
        ),
        "five_in_minimum_adverse_clearance_before_machining_error_mm": (five_clearance),
    }


def report(data=None):
    data = validate_selection(data or load_selection())
    strength = data["standard_strength_calculation"]
    area = strength["quarter_twenty_tensile_stress_area_in2"]
    proof = data["bolts"][0]["minimum_proof_psi"] * area
    yield_load = data["bolts"][0]["minimum_yield_psi"] * area
    tensile = data["bolts"][0]["minimum_tensile_psi"] * area
    if not all(
        isclose(actual, strength[expected], abs_tol=1e-9)
        for actual, expected in (
            (proof, "minimum_proof_load_lbf"),
            (yield_load, "minimum_yield_load_lbf"),
            (tensile, "minimum_tensile_load_lbf"),
        )
    ):
        raise ValueError("recorded bolt strength calculation drifted")
    washer = data["washers"][0]
    minimum_washer_area = annular_area_mm2(washer["od_min_mm"], washer["id_max_mm"])
    return {
        "schema": SCHEMA,
        "selected_barrel": data["barrel"]["product"],
        "selected_bolt_count": sum(row["quantity"] for row in data["bolts"]),
        "selected_washer_count": sum(row["quantity"] for row in data["washers"]),
        "bolt_minimum_proof_load_lbf": proof,
        "bolt_minimum_yield_load_lbf": yield_load,
        "bolt_minimum_tensile_load_lbf": tensile,
        "washer_minimum_annular_area_mm2": minimum_washer_area,
        "as_drawn_six_inch_stack": data["decision"]["current_as_drawn_six_inch_stack"],
        "complete_design": data["decision"]["complete_direct_cross_dowel_design"],
        "blocking_gates": data["decision"]["blocking_gates"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--measurement-template", action="store_true")
    parser.add_argument("--measurements", type=Path)
    args = parser.parse_args()
    if args.measurement_template and args.measurements:
        parser.error("choose either --measurement-template or --measurements")
    if args.measurement_template:
        output = measurement_template()
    elif args.measurements:
        output = evaluate_measurements(json.loads(args.measurements.read_text()))
    else:
        output = report()
    print(json.dumps(output, indent=2, sort_keys=True))
