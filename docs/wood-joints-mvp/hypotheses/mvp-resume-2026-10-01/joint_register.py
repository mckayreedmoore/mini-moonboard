"""Build a source-pinned register from saved wood-joint evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[3]
OUTPUT = PACKET / "joint-register-attempt01"
COMPARISON = "all-outer-corner-frame-attempt01/comparison.json"
RESPONSE = "all-outer-corner-frame-attempt01/response.npz"
ROWS = "corner-frame-attempt01/row-identities.json"
MODEL = "corner-frame-attempt01/model.json"
GRADE = "remaining-joint-screen-attempt03/grade5-92ksi"
THREE = "three-member-screen-attempt01/all-outer-corners"
HEADER_CHECKS = "header-joint-attempt01/checks.json"
HEADER_REPORT = "header-joint-checks.md"
HEADER_OUTPUTS = (
    "header-joint-attempt01/joint-actions.json",
    "header-joint-attempt01/joint-states.json",
    "header-joint-attempt01/placement.json",
    "header-joint-attempt01/header-sections.csv",
)
SERVICE_RESULT = "service-joint-current-attempt02/result.json"
PARTIAL_SEAT_RESULT = "partial-seat-footprint-current-attempt02/result.json"
CASE_IDS = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
PINNED_SHA256 = {
    COMPARISON: "ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3",
    RESPONSE: "aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901",
}

INPUTS = [
    MODEL,
    ROWS,
    COMPARISON,
    RESPONSE,
    "member-screen-attempt02/all-outer-clearance01/member-results.json",
    "member-screen-attempt02/all-outer-clearance01/member-results.csv",
    f"{GRADE}/screen.json",
    f"{GRADE}/source-pins.json",
    f"{GRADE}/bolt-states.csv",
    f"{GRADE}/washer-reference-states.csv",
    "corner-component-attempt04/component-results.json",
    "corner-component-attempt04/steel-interaction.json",
    "bottom-corner-component-attempt05/component-results.json",
    "end-grain-route-attempt02/route.json",
    "end-grain-route-attempt02/six-case-signed-states.csv",
    f"{THREE}/screen.json",
    f"{THREE}/source-pins.json",
    f"{THREE}/bolt-cases.csv",
    f"{THREE}/group-states.csv",
    f"{THREE}/contact-states.csv",
    f"{THREE}/plane-states.csv",
    f"{THREE}/profile-states.csv",
    f"{THREE}/receiver-wrenches.csv",
    HEADER_REPORT,
    HEADER_CHECKS,
    "header-joint-attempt01/source-pins.json",
    *HEADER_OUTPUTS,
    SERVICE_RESULT,
    PARTIAL_SEAT_RESULT,
]


def source_path(relative: str) -> Path:
    return ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01" / relative


def load_json(relative: str) -> Any:
    return json.loads(source_path(relative).read_text())


def load_csv(relative: str) -> list[dict[str, Any]]:
    with source_path(relative).open(newline="") as stream:
        return [
            {key: csv_value(value) for key, value in row.items()}
            for row in csv.DictReader(stream)
        ]


def csv_value(value: str | None) -> Any:
    if value in (None, ""):
        return None
    if value == "True":
        return True
    if value == "False":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def sha256(relative: str) -> str:
    return hashlib.sha256(source_path(relative).read_bytes()).hexdigest()


def output_link(relative: str, label: str | None = None) -> str:
    return f"[{label or relative}]({relative})"


def source_link(relative: str, label: str | None = None) -> str:
    return output_link(Path(relative).as_posix(), label)


def assert_close(actual: float, expected: float, context: str) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-7):
        raise ValueError(f"saved-force cross-check failed for {context}: {actual} != {expected}")


def parse_register() -> dict[str, Any]:
    for path, expected in PINNED_SHA256.items():
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"pinned source changed: {path} ({actual})")

    model = load_json(MODEL)
    row_identities = load_json(ROWS)
    comparison = load_json(COMPARISON)
    grade = load_json(f"{GRADE}/screen.json")
    grade_states = load_csv(f"{GRADE}/bolt-states.csv")
    grade_washers = load_csv(f"{GRADE}/washer-reference-states.csv")
    member_report = load_json(
        "member-screen-attempt02/all-outer-clearance01/member-results.json"
    )
    member_states = load_csv(
        "member-screen-attempt02/all-outer-clearance01/member-results.csv"
    )
    top_components = load_json("corner-component-attempt04/component-results.json")
    top_steel = load_json("corner-component-attempt04/steel-interaction.json")
    bottom_components = load_json(
        "bottom-corner-component-attempt05/component-results.json"
    )
    end_grain = load_json("end-grain-route-attempt02/route.json")
    end_grain_states = load_csv("end-grain-route-attempt02/six-case-signed-states.csv")
    three_screen = load_json(f"{THREE}/screen.json")
    header_checks = load_json(HEADER_CHECKS)
    service_result = load_json(SERVICE_RESULT)
    partial_seat_result = load_json(PARTIAL_SEAT_RESULT)
    three_inputs = {
        "bolt_cases": load_csv(f"{THREE}/bolt-cases.csv"),
        "group_states": load_csv(f"{THREE}/group-states.csv"),
        "contact_states": load_csv(f"{THREE}/contact-states.csv"),
        "plane_states": load_csv(f"{THREE}/plane-states.csv"),
        "profile_states": load_csv(f"{THREE}/profile-states.csv"),
        "receiver_wrenches": load_csv(f"{THREE}/receiver-wrenches.csv"),
    }

    if grade["case_ids"] != CASE_IDS or three_screen["case_ids"] != CASE_IDS:
        raise ValueError("saved case order differs from the pinned six-case source")
    if grade["source_comparison_sha256"] != PINNED_SHA256[COMPARISON]:
        raise ValueError("Grade 5 screen does not cite the pinned comparison")
    if grade["source_response_sha256"] != PINNED_SHA256[RESPONSE]:
        raise ValueError("Grade 5 screen does not cite the pinned response")
    expected_clearance_source = (
        "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/"
        + COMPARISON.removesuffix("/comparison.json")
    )
    if three_screen["clearance_source"] != expected_clearance_source:
        raise ValueError("three-member screen points at a different clearance source")
    if (
        header_checks["schema"] != "six_current_header_joint_conditional_checks/v1"
        or header_checks["case_ids"] != CASE_IDS
        or header_checks["counts"]["joints"] != 6
        or header_checks["counts"]["axes"] != 12
        or header_checks["counts"]["bolt_states"] != 72
        or header_checks["complete_joint_acceptance"]
    ):
        raise ValueError("saved six-joint header report scope changed")
    header_lateral = header_checks["peaks"]["same_state_lateral_with_Cg_sensitivity"]
    header_washer = header_checks["peaks"]["washer"]
    if not math.isclose(
        header_lateral["same_state_V_over_Ceg_Z_Cg_sensitivity"],
        0.25986967882080486,
        rel_tol=0,
        abs_tol=1e-12,
    ) or not math.isclose(
        header_washer["pressure_over_reference"],
        0.39842246572849666,
        rel_tol=0,
        abs_tol=1e-12,
    ):
        raise ValueError("saved six-joint header peaks differ from the current report")
    for name, digest in header_checks["output_sha256"].items():
        relative = f"header-joint-attempt01/{name}"
        if sha256(relative) != digest:
            raise ValueError(f"saved header output hash differs: {relative}")

    service_peak_axis = (
        "left_service/left_service_mirrored_inner_outer_hypothesis/"
        "clip_horizontal_lower_left_1/lower_side_1"
    )
    service_peak = next(
        state
        for state in service_result["states"]
        if state["case_id"] == "k12-rear" and state["axis_id"] == service_peak_axis
    )
    if (
        service_result["schema"] != "current_lower_service_individual_reference/v1"
        or len(service_result["states"]) != 24
        or service_result["complete_joint_acceptance"]
        or not math.isclose(service_peak["ratio_92ksi"], 0.005680548080782871, rel_tol=0, abs_tol=1e-12)
        or not math.isclose(service_peak["ratio_45ksi"], 0.00812227887811448, rel_tol=0, abs_tol=1e-12)
        or not math.isclose(service_peak["shear_n"], 4.881407899275957, rel_tol=0, abs_tol=1e-9)
        or not math.isclose(service_peak["simultaneous_tension_n"], 1.6864818901845453, rel_tol=0, abs_tol=1e-9)
    ):
        raise ValueError("saved current lower-service comparison differs from its pinned record")
    zero_lateral_states = [
        state
        for state in service_result["states"]
        if state["lateral_reference_status"] == "ZERO_LATERAL_DIRECTION_UNDEFINED"
    ]
    reference_fields = [
        *(f"reference_{grade}_n" for grade in ("45ksi", "92ksi", "106ksi")),
        *(f"ratio_{grade}" for grade in ("45ksi", "92ksi", "106ksi")),
    ]
    if any(
        any(state[field] is not None for field in reference_fields)
        or any(angle is not None for angle in state["load_to_grain_angles_degrees"])
        for state in zero_lateral_states
    ):
        raise ValueError("zero-force lower-service direction/reference fields must stay null")

    partial_seat_peak = next(
        state for state in partial_seat_result["states"] if state["case_id"] == "k12-rear"
    )
    if (
        partial_seat_result["schema"] != "current_partial_seat_supported_central_footprint/v1"
        or partial_seat_result["axis_id"] != "center_principal_right_2"
        or len(partial_seat_result["states"]) != 6
        or partial_seat_result["complete_joint_acceptance"]
        or not math.isclose(partial_seat_peak["signed_tie_n"], 81.36475713341623, rel_tol=0, abs_tol=1e-9)
        or not math.isclose(
            partial_seat_peak["central_mean_pressure_over_Fc_perp"],
            0.5146803451745007,
            rel_tol=0,
            abs_tol=1e-12,
        )
    ):
        raise ValueError("saved partial central-seat report differs from its pinned record")

    pins = comparison["source_sha256"]
    for relative in (MODEL, ROWS):
        if pins.get(f"docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/{relative}") != sha256(
            relative
        ):
            raise ValueError(f"all-outer source does not pin current {relative}")
    if comparison["response_sha256"] != PINNED_SHA256[RESPONSE]:
        raise ValueError("comparison metadata response hash differs from the saved NPZ")
    gap_state_cases = {
        state["case_id"]
        for state in comparison["states"]
        if state["gap_scale"] == 1.0
    }
    if gap_state_cases != set(CASE_IDS):
        raise ValueError("all-outer comparison lacks one or more selected gap-scale states")

    blocks = {
        name
        for name in model["body_names"]
        if name.endswith("_cleat")
        or "_cleat_" in name
        or name.startswith(("knee_outer_left_", "knee_outer_right_"))
        and name.endswith(("_spine", "_inner_frame_block"))
    }
    if len(blocks) != 24:
        raise ValueError(f"expected 24 connector-block bodies, found {len(blocks)}")

    outer_ties: dict[str, dict[str, Any]] = {}
    plane_rows: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for record in row_identities:
        ownership = record["ownership"]
        role = ownership["role"]
        row_id = record["row_id"]
        if role == "physical_bolt_outer_seat_tension":
            suffix = "/outer-seat-axial-tie"
            if not row_id.endswith(suffix):
                raise ValueError(f"unexpected axial tie identity: {row_id}")
            axis_id = row_id[: -len(suffix)]
            if axis_id in outer_ties:
                raise ValueError(f"duplicate outer-seat row for {axis_id}")
            outer_ties[axis_id] = record
        elif role in ("candidate_bolt_lateral_plane", "retained_bolt_lateral_plane"):
            axis_id, separator, _plane = row_id.rpartition("/")
            if not separator:
                raise ValueError(f"unexpected lateral row identity: {row_id}")
            plane_rows[axis_id][row_id].append(record)

    grade_arrangements = {
        axis_id: duty["kind"]
        for duty in grade["duties"]
        for axis_id in duty["axis_ids"]
    }
    axis_records: dict[str, dict[str, Any]] = {}
    for axis_id, tie in outer_ties.items():
        interfaces = []
        for plane_id, components in sorted(plane_rows[axis_id].items()):
            components.sort(key=lambda item: item["row"])
            if len(components) != 2:
                raise ValueError(f"{plane_id} has {len(components)} component rows")
            first, second = components
            one = first["ownership"]
            two = second["ownership"]
            if {one["first_body"], one["second_body"]} != {
                two["first_body"],
                two["second_body"],
            }:
                raise ValueError(f"receiver pair differs inside {plane_id}")
            interfaces.append(
                {
                    "plane_id": plane_id,
                    "receivers": [one["first_body"], one["second_body"]],
                    "component_rows": [first["row"], second["row"]],
                    "component_row_ids": [first["row_id"], second["row_id"]],
                    "component_directions_xyz": [
                        one["direction_global_xyz"],
                        two["direction_global_xyz"],
                    ],
                    "block_ids_on_interface": sorted(
                        {one["first_body"], one["second_body"]} & blocks
                    ),
                }
            )
        tie_ownership = tie["ownership"]
        tie_block_ids = sorted(
            {tie_ownership["first_body"], tie_ownership["second_body"]} & blocks
        )
        block_ids = sorted(
            {
                body
                for interface in interfaces
                for body in interface["receivers"]
                if body in blocks
            }
        )
        kind = "candidate_bolt" if block_ids else "retained_bolt"
        if block_ids != tie_block_ids:
            raise ValueError(f"tie/interface block identity differs for {axis_id}")
        if kind == "candidate_bolt" and not interfaces:
            raise ValueError(f"candidate axis lacks lateral plane rows: {axis_id}")
        if kind == "retained_bolt" and axis_id not in grade_arrangements:
            raise ValueError(f"unmapped retained axis: {axis_id}")
        if (
            kind == "candidate_bolt"
            and axis_id in grade_arrangements
            and grade_arrangements[axis_id] != "candidate_bolt"
        ):
            raise ValueError(f"candidate/retained source disagreement: {axis_id}")
        axis_records[axis_id] = {
            "axis_id": axis_id,
            "kind": kind,
            "block_ids": block_ids,
            "receivers": sorted(
                {body for interface in interfaces for body in interface["receivers"]}
            ),
            "interfaces": interfaces,
            "outer_tie": {
                "row": tie["row"],
                "row_id": tie["row_id"],
                "first_body": tie_ownership["first_body"],
                "second_body": tie_ownership["second_body"],
                "direction_global_xyz": tie_ownership["direction_global_xyz"],
            },
            "per_state": [],
        }

    candidate_axes = {key for key, value in axis_records.items() if value["kind"] == "candidate_bolt"}
    retained_axes = {key for key, value in axis_records.items() if value["kind"] == "retained_bolt"}
    hillman_axis_ids = {
        record["row_id"]
        for record in row_identities
        if record["ownership"]["role"] == "non_qualifying_parametric_screw_withdrawal"
    }
    shared_axes = sorted(
        key for key in candidate_axes if len(axis_records[key]["block_ids"]) > 1
    )
    expected_shared = {
        "knee_outer_left_side_1",
        "knee_outer_left_side_2",
        "knee_outer_right_side_1",
        "knee_outer_right_side_2",
    }
    if len(candidate_axes) != 92 or len(retained_axes) != 12:
        raise ValueError(
            f"axis accounting mismatch: {len(candidate_axes)} candidate, "
            f"{len(retained_axes)} retained"
        )
    if len(hillman_axis_ids) != 66:
        raise ValueError(f"expected 66 separate Hillman axes, found {len(hillman_axis_ids)}")
    if set(shared_axes) != expected_shared:
        raise ValueError(f"unexpected shared block axes: {shared_axes}")
    if set(grade_arrangements) != candidate_axes | retained_axes:
        # The saved screen excludes 12 candidate axes but includes all 12 retained axes.
        if not retained_axes <= set(grade_arrangements):
            raise ValueError("saved retained-bolt duties do not cover all 12 physical bolts")
        if set(grade_arrangements) - retained_axes != candidate_axes - set(
            grade["excluded_top_axes"] + grade["excluded_worker_axes"]
        ):
            raise ValueError("saved Grade 5 axis coverage differs from its exclusions")

    response_path = source_path(RESPONSE)
    force_vectors = {}
    with np.load(response_path, allow_pickle=False) as response:
        for case_id in CASE_IDS:
            key = f"{case_id}_gap_raw_force_n"
            if key not in response.files:
                raise ValueError(f"missing same-state response vector {key}")
            force = response[key]
            force_vectors[case_id] = force.copy()
            for axis_id, axis in axis_records.items():
                tie_row = axis["outer_tie"]["row"]
                axis_state = {
                    "case_id": case_id,
                    "outer_tie_signed_n": float(force[tie_row]),
                    "outer_tie_row": tie_row,
                    "interfaces": [],
                    "source_key": key,
                }
                for interface in axis["interfaces"]:
                    rows = interface["component_rows"]
                    components = [float(force[row]) for row in rows]
                    axis_state["interfaces"].append(
                        {
                            "plane_id": interface["plane_id"],
                            "component_rows": rows,
                            "components_n": components,
                            "V_resultant_n": math.hypot(*components),
                        }
                    )
                axis["per_state"].append(axis_state)

    grade_state_index = {
        (row["case_id"], row["axis_id"], row["plane_id"]): row
        for row in grade_states
    }
    if len(grade_state_index) != len(grade_states):
        raise ValueError("duplicate Grade 5 state comparison key")
    matched_grade_states = set()
    for axis_id, axis in axis_records.items():
        for state in axis["per_state"]:
            for interface_state in state["interfaces"]:
                saved = grade_state_index.get(
                    (state["case_id"], axis_id, interface_state["plane_id"])
                )
                if saved is None:
                    continue
                matched_grade_states.add(
                    (state["case_id"], axis_id, interface_state["plane_id"])
                )
                assert_close(
                    state["outer_tie_signed_n"],
                    saved["outer_tie_signed_n"],
                    f"{state['case_id']} {axis_id} axial tie",
                )
                assert_close(
                    interface_state["components_n"][0],
                    saved["shear_component_1_n"],
                    f"{state['case_id']} {axis_id} component 1",
                )
                assert_close(
                    interface_state["components_n"][1],
                    saved["shear_component_2_n"],
                    f"{state['case_id']} {axis_id} component 2",
                )
                assert_close(
                    interface_state["V_resultant_n"],
                    saved["shear_resultant_n"],
                    f"{state['case_id']} {axis_id} V resultant",
                )
    if matched_grade_states != set(grade_state_index):
        raise ValueError("Grade 5 state rows do not all map to current force rows")

    for row in end_grain_states:
        rows = json.loads(row["component_rows"])
        force = force_vectors[row["case_id"]]
        assert_close(
            math.hypot(float(force[rows[0]]), float(force[rows[1]])),
            row["shear_resultant_n"],
            f"end-grain {row['case_id']} {row['axis_id']} V",
        )

    def check_component_states(
        records: list[dict[str, Any]], shear_field: str, source_label: str
    ) -> None:
        for record in records:
            axis = axis_records[record["axis_id"]]
            state = next(
                item for item in axis["per_state"] if item["case_id"] == record["case_id"]
            )
            if len(state["interfaces"]) != 1:
                raise ValueError(f"unexpected multi-plane component record: {record['axis_id']}")
            assert_close(
                state["interfaces"][0]["V_resultant_n"],
                record[shear_field],
                f"{source_label} {record['case_id']} {record['axis_id']} V",
            )
            assert_close(
                state["outer_tie_signed_n"],
                record["tension_n"],
                f"{source_label} {record['case_id']} {record['axis_id']} T",
            )

    check_component_states(top_components["states"], "lateral_n", "top component")
    check_component_states(top_steel["states"], "lateral_n", "top steel component")
    check_component_states(bottom_components["states"], "shear_n", "bottom component")
    for record in three_inputs["bolt_cases"]:
        state = next(
            item
            for item in axis_records[record["axis_id"]]["per_state"]
            if item["case_id"] == record["case_id"]
        )
        assert_close(
            state["outer_tie_signed_n"],
            record["outer_tie_signed_n"],
            f"three-member {record['case_id']} {record['axis_id']} T",
        )

    grade_duties = grade["duties"]
    for duty in grade_duties:
        rows = [row for row in grade_states if row["duty_id"] == duty["duty_id"]]
        duty["saved_lateral_reference_statuses"] = sorted(
            {row["lateral_reference_status"] for row in rows}
        )
        duty["saved_state_count"] = len(rows)
    block_axis_ids: dict[str, list[str]] = {
        block: sorted(axis for axis in candidate_axes if block in axis_records[axis]["block_ids"])
        for block in blocks
    }
    if sum(map(len, block_axis_ids.values())) != 96:
        raise ValueError("block-axis incidence total differs from four shared axes")

    blocks_out = []
    for block in sorted(blocks):
        axes = block_axis_ids[block]
        interfaces = [
            {
                "axis_id": axis_id,
                **interface,
            }
            for axis_id in axes
            for interface in axis_records[axis_id]["interfaces"]
            if block in interface["block_ids_on_interface"]
        ]
        duties = [
            duty
            for duty in grade_duties
            if duty["kind"] == "candidate_bolt"
            and set(duty["axis_ids"]) & set(axes)
        ]
        blocks_out.append(
            {
                "block_id": block,
                "candidate_axis_ids": axes,
                "receiver_interfaces": interfaces,
                "grade5_duty_ids": [duty["duty_id"] for duty in duties],
                "member_screen_members": sorted(
                    {block}
                    | {
                        receiver
                        for axis_id in axes
                        for receiver in axis_records[axis_id]["receivers"]
                    }
                ),
                "separate_magnitude_peaks": block_peaks(axes, axis_records),
            }
        )

    arrangements = []
    for duty in grade_duties:
        if duty["kind"] != "retained_bolt":
            continue
        ids = sorted(duty["axis_ids"])
        arrangements.append(
            {
                "arrangement_id": duty["duty_id"],
                "receivers": duty["receivers"],
                "physical_axis_ids": ids,
                "grade5_duty_id": duty["duty_id"],
                "separate_magnitude_peaks": block_peaks(ids, axis_records),
            }
        )
    if len(arrangements) != 6 or sum(len(x["physical_axis_ids"]) for x in arrangements) != 12:
        raise ValueError("retained frame bolts do not reconcile to six two-bolt arrangements")

    top_states = top_components["states"]
    top_steel_states = top_steel["states"]
    bottom_states = bottom_components["states"]
    end_grain_axis_ids = {row["axis_id"] for row in end_grain_states}
    three_shared_rows = {row["axis_id"] for row in three_inputs["bolt_cases"]}
    for block in blocks_out:
        ids = set(block["candidate_axis_ids"])
        block["special_comparisons"] = []
        for report, rows, metric, label in (
            (
                "corner-component-attempt04/component-results.json",
                top_states,
                "lateral_over_adjusted_conditional_reference",
                "top-corner adjusted lateral component reference",
            ),
            (
                "corner-component-attempt04/steel-interaction.json",
                top_steel_states,
                "same_state_lateral_over_adjusted_reduced_reference",
                "top-corner axial-reserved lateral component scenario",
            ),
            (
                "bottom-corner-component-attempt05/component-results.json",
                bottom_states,
                "ratio_92ksi_adjusted_component_scenario",
                "bottom-corner 92 ksi adjusted component scenario",
            ),
        ):
            matching = [row for row in rows if row["block"] == block["block_id"]]
            if matching:
                selected = max(matching, key=lambda row: row[metric])
                block["special_comparisons"].append(
                    {
                        "source": report,
                        "label": label,
                        "record_field": metric,
                        "value": selected[metric],
                        "case_id": selected["case_id"],
                        "axis_id": selected["axis_id"],
                    }
                )
        route_peaks = [
            row
            for row in end_grain["peaks_at_92ksi"]
            if row["axis_id"] in ids and row["axis_id"] in end_grain_axis_ids
        ]
        if route_peaks:
            selected = max(route_peaks, key=lambda row: row["V_over_Ceg_Z_92ksi"])
            block["special_comparisons"].append(
                {
                    "source": "end-grain-route-attempt02/route.json",
                    "label": "92 ksi end-grain individual reference",
                    "record_field": "V_over_Ceg_Z_92ksi",
                    "value": selected["V_over_Ceg_Z_92ksi"],
                    "case_id": selected["case_id"],
                    "axis_id": selected["axis_id"],
                    "plane_id": selected["plane_id"],
                }
            )
        shared = sorted(ids & three_shared_rows)
        if shared:
            shared_states = [
                row
                for row in three_inputs["bolt_cases"]
                if row["axis_id"] in shared
            ]
            peak = max(shared_states, key=lambda row: row["utilization_sum_92ksi"])
            block["special_comparisons"].append(
                {
                    "source": f"{THREE}/screen.json",
                    "label": "three-receiver conditional convex utilization sum",
                    "record_field": "utilization_sum_92ksi",
                    "value": peak["utilization_sum_92ksi"],
                    "case_id": peak["case_id"],
                    "axis_id": peak["axis_id"],
                    "shared_axis_ids": shared,
                    "contact_transfer_source": f"{THREE}/group-states.csv",
                }
            )

    missing_grade_axes = sorted(
        candidate_axes - {axis for duty in grade_duties if duty["kind"] == "candidate_bolt" for axis in duty["axis_ids"]}
    )
    expected_missing = sorted(grade["excluded_top_axes"] + grade["excluded_worker_axes"])
    if missing_grade_axes != expected_missing:
        raise ValueError("Grade 5 source exclusions do not reconcile to missing candidate axes")

    source_hashes = {relative: sha256(relative) for relative in INPUTS}
    return {
        "schema": "owner-authorized-wood-joint-mvp-register/v1",
        "status": "conditional engineering evidence register; complete joints unresolved",
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
        "candidate": model["candidate"],
        "source_revision": model["source_revision"],
        "development_revision": model["development_revision"],
        "model_reviewed_geometry_changed": model["reviewed_geometry_changed"],
        "physical_release": model["physical_release"],
        "complete_joint_acceptance": False,
        "case_ids": CASE_IDS,
        "accounting": {
            "connector_block_bodies": len(blocks),
            "candidate_unique_physical_bolt_axes": len(candidate_axes),
            "retained_frame_bolt_axes": len(retained_axes),
            "total_unique_frame_bolt_axes": len(axis_records),
            "candidate_block_axis_incidences": sum(map(len, block_axis_ids.values())),
            "shared_physical_axes": shared_axes,
            "shared_axis_counted_once_in_physical_axis_register": len(shared_axes),
            "hillman_panel_kicker_axes_separate": len(hillman_axis_ids),
            "hillman_scope_note": "Panel/kicker screws are a separate 66-axis attachment system; no structural-bolt or wood-joint resistance is transferred.",
        },
        "same_state_force_source": {
            "comparison": COMPARISON,
            "comparison_sha256": sha256(COMPARISON),
            "response": RESPONSE,
            "response_sha256": sha256(RESPONSE),
            "force_key_pattern": "{case_id}_gap_raw_force_n",
            "gap_scale": 1.0,
            "row_identity_source": ROWS,
            "row_identity_sha256": sha256(ROWS),
            "model_source": MODEL,
            "model_sha256": sha256(MODEL),
            "row_force_convention": "Signed raw force by row identity; V is the magnitude of the two saved lateral component rows on one plane. Distinct planes and signed T remain separate.",
            "clearance_joint_hosts": comparison["clearance_joint_hosts"],
            "gap_scale_1_states": [
                {
                    "case_id": state["case_id"],
                    "gap_scale": state["gap_scale"],
                    "status": state["status"],
                }
                for state in comparison["states"]
                if state["gap_scale"] == 1.0
            ],
            "other_bolted_joints": "source zero-clearance stiffness assumption",
            "complete_joint_acceptance": comparison["complete_joint_acceptance"],
        },
        "axes": [axis_records[axis_id] for axis_id in sorted(axis_records)],
        "blocks": blocks_out,
        "retained_frame_bolt_arrangements": arrangements,
        "grade5_screen": {
            "screen": f"{GRADE}/screen.json",
            "source_pins": f"{GRADE}/source-pins.json",
            "bolt_states": f"{GRADE}/bolt-states.csv",
            "washer_reference_states": f"{GRADE}/washer-reference-states.csv",
            "schema": grade["schema"],
            "counts": grade["counts"],
            "force_source_sha256": {
                "comparison": grade["source_comparison_sha256"],
                "response": grade["source_response_sha256"],
            },
            "clearance_scope": grade["source_clearance_scope"],
            "gap_definitions": grade["gap_definitions"],
            "duties": grade_duties,
            "bolt_state_comparison_source": f"{GRADE}/bolt-states.csv",
            "bolt_state_comparison_count": len(grade_states),
            "bolt_state_comparison_fields": list(grade_states[0]),
            "washer_reference_comparison_source": f"{GRADE}/washer-reference-states.csv",
            "washer_reference_comparison_count": len(grade_washers),
            "washer_reference_comparison_fields": list(grade_washers[0]),
            "excluded_candidate_axes": missing_grade_axes,
            "complete_joint_acceptance": grade["complete_joint_acceptance"],
            "limits": grade["assumptions"],
        },
        "member_screen": {
            "report": "member-screen-attempt02/all-outer-clearance01/member-results.json",
            "states": "member-screen-attempt02/all-outer-clearance01/member-results.csv",
            "status": member_report["status"],
            "counts": member_report["counts"],
            "clearance_scope": member_report["clearance_joint_hosts"],
            "method_limits": member_report["method_limits"],
            "complete_member_acceptance": member_report["complete_member_acceptance"],
            "complete_joint_acceptance": member_report["complete_joint_acceptance"],
            "member_state_comparisons": member_states,
        },
        "top_corner_component": {
            "source": "corner-component-attempt04/component-results.json",
            "steel_interaction_source": "corner-component-attempt04/steel-interaction.json",
            "component_results": strip_source_hashes(top_components),
            "steel_interaction": strip_source_hashes(top_steel),
        },
        "bottom_corner_component": {
            "source": "bottom-corner-component-attempt05/component-results.json",
            "component_results": strip_source_hashes(bottom_components),
        },
        "end_grain_route": {
            "source": "end-grain-route-attempt02/route.json",
            "state_records": "end-grain-route-attempt02/six-case-signed-states.csv",
            "route": strip_source_hashes(end_grain),
            "signed_state_comparisons": end_grain_states,
        },
        "three_member_screen": {
            "source": f"{THREE}/screen.json",
            "source_pins": f"{THREE}/source-pins.json",
            "screen": {
                key: value
                for key, value in strip_source_hashes(three_screen).items()
                if key not in {"bolt_cases", "group_states"}
            },
            "state_comparisons": three_inputs,
            "complete_joint_acceptance": three_screen["complete_joint_acceptance"],
        },
        "header_joint_checks": {
            "report_markdown": HEADER_REPORT,
            "checks_json": HEADER_CHECKS,
            "checks_sha256": sha256(HEADER_CHECKS),
            "checks": header_checks,
        },
        "current_service_joint_comparison": {
            "source": SERVICE_RESULT,
            "indexed_peak_state": service_peak,
            "result": service_result,
        },
        "current_partial_central_seat": {
            "source": PARTIAL_SEAT_RESULT,
            "indexed_peak_state": partial_seat_peak,
            "result": partial_seat_result,
            "prior_attempt_note": "Attempt 01 differs by producer format only; six saved states are identical.",
        },
        "source_sha256": source_hashes,
    }


def strip_source_hashes(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "source_sha256"}


def block_peaks(
    axis_ids: list[str], axes: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    shear: list[tuple[float, str, str, str]] = []
    tension: list[tuple[float, str, str]] = []
    for axis_id in axis_ids:
        for state in axes[axis_id]["per_state"]:
            tension.append((state["outer_tie_signed_n"], state["case_id"], axis_id))
            for interface in state["interfaces"]:
                shear.append(
                    (
                        interface["V_resultant_n"],
                        state["case_id"],
                        axis_id,
                        interface["plane_id"],
                    )
                )
    v = max(shear)
    t = max(tension)
    return {
        "V_peak_n": v[0],
        "V_case_id": v[1],
        "V_axis_id": v[2],
        "V_plane_id": v[3],
        "T_peak_signed_n": t[0],
        "T_case_id": t[1],
        "T_axis_id": t[2],
        "simultaneous": False,
        "scope": "independent magnitude maxima over saved cases and planes; no plane sum",
    }


def axis_tail(axis_id: str) -> str:
    return axis_id.rsplit("/", 1)[-1]


def compact_host_duties(block: dict[str, Any]) -> str:
    grouped: dict[str, dict[str, Any]] = {}
    block_id = block["block_id"]
    for interface in block["receiver_interfaces"]:
        root, suffix = interface["axis_id"].rsplit("_", 1)
        group = grouped.setdefault(root, {"suffixes": set(), "pairs": set()})
        group["suffixes"].add(suffix)
        group["pairs"].add(tuple(sorted(interface["receivers"])))

    lines = []
    for root, group in sorted(grouped.items()):
        suffixes = ",".join(sorted(group["suffixes"]))
        axis_range = f"`{root}_{{{suffixes}}}`"
        for pair in sorted(group["pairs"]):
            if block_id in pair:
                receivers = " / ".join(name for name in pair if name != block_id)
                host = f"→ `{receivers}`"
            else:
                host = f"↔ `{pair[0]}` / `{pair[1]}`"
            lines.append(f"{axis_range} {host}")
    return "<br>".join(lines)


def grade5_method_items(block: dict[str, Any], register: dict[str, Any]) -> list[str]:
    duties = {duty["duty_id"]: duty for duty in register["grade5_screen"]["duties"]}
    items = []
    for duty_id in block["grade5_duty_ids"]:
        duty = duties[duty_id]
        duty_name = duty_id.rsplit("/", 1)[-1]
        result = duty.get("governing_92ksi")
        if result is None:
            statuses = ",".join(duty["saved_lateral_reference_statuses"])
            items.append(f"G5 {duty_name}: no ratio ({statuses})")
            continue
        items.append(
            f"G5-92 {duty_name} {result['ratio_92ksi']:.3f} "
            f"{result['mode_92ksi']} @ {result['case_id']}/"
            f"{axis_tail(result['axis_id'])}/{axis_tail(result['plane_id'])}"
        )
    return items


def special_method_items(block: dict[str, Any], register: dict[str, Any]) -> list[str]:
    items = []
    for record in block["special_comparisons"]:
        value = record["value"]
        state = f"@ {record['case_id']}/{axis_tail(record['axis_id'])}"
        if record["label"] == "top-corner adjusted lateral component reference":
            label = "top comp"
        elif record["label"] == "top-corner axial-reserved lateral component scenario":
            label = "top axial-reserved comp"
        elif record["label"] == "bottom-corner 92 ksi adjusted component scenario":
            label = "bottom comp"
        elif record["label"] == "92 ksi end-grain individual reference":
            label = "end-grain individual"
            state += f"/{axis_tail(record['plane_id'])}"
        elif record["label"] == "three-receiver conditional convex utilization sum":
            label = "3-receiver 92ksi sum"
        else:
            label = record["label"]
        items.append(f"{label} {value:.3f} {state}")

    if block["block_id"] == "left_service_outer_lower_cleat":
        state = register["current_service_joint_comparison"]["indexed_peak_state"]
        items.append(
            f"service 92ksi {state['ratio_92ksi']:.6f} / "
            f"45ksi {state['ratio_45ksi']:.6f} @ {state['case_id']}/"
            f"{axis_tail(state['axis_id'])}; same-state V {state['shear_n']:.7f} N / "
            f"T+ {state['simultaneous_tension_n']:.8f} N"
        )

    partial = register["current_partial_central_seat"]
    if partial["result"]["axis_id"] in block["candidate_axis_ids"]:
        state = partial["indexed_peak_state"]
        items.append(
            f"central-seat wood pressure/Fc⊥ "
            f"{state['central_mean_pressure_over_Fc_perp']:.6f}; "
            f"tie {state['signed_tie_n']:.6f} N @ {state['case_id']}"
        )
    return items


def open_item(block: dict[str, Any], header_blocks: set[str]) -> str:
    block_id = block["block_id"]
    if block_id == "left_service_outer_lower_cleat":
        return "Current individual reference only; complete-joint interaction and receiver transfer remain uncalculated."
    if block_id.startswith("top_outer_"):
        return "Grade 5 excludes all eight axes; saved top ratios are component scenarios. Whole-joint resistance and interaction remain absent."
    if block_id.startswith("knee_outer_") and block_id.endswith("_inner_frame_block"):
        return "Applicable loaded-edge rule for five oblique end-grain states remains unresolved; first-face short checks are diagnostics. Integrated joint-law result also absent."
    if block_id.startswith("knee_outer_") and block_id.endswith("_spine"):
        return "Three-receiver study retains contact transfer; endpoint admissibility, shared-bolt bending/load split, washer transfer, finished-wood and frame-chain reconciliation remain open."
    if block_id in header_blocks:
        return "Header report supplies conditional interface force/contact results; complete-joint acceptance and parent integrated-law calculations remain open."
    if block_id.startswith("bottom_outer_"):
        return "Grade 5 plane ratios and adjusted component scenario only; complete-joint interaction and receiver transfer remain uncalculated."
    return "Grade 5 values are individual plane/component references; integrated joint-law interaction and complete receiver transfer remain uncalculated."


def render_markdown(register: dict[str, Any], machine_hash: str) -> str:
    force = register["same_state_force_source"]
    header = register["header_joint_checks"]["checks"]
    service = register["current_service_joint_comparison"]
    service_peak = service["indexed_peak_state"]
    partial = register["current_partial_central_seat"]
    partial_peak = partial["indexed_peak_state"]
    header_lateral = header["peaks"]["same_state_lateral_with_Cg_sensitivity"]
    header_washer = header["peaks"]["washer"]
    header_blocks = set(header["conditional_material"]) - {"base_header"}
    grade_duties = {
        duty["duty_id"]: duty for duty in register["grade5_screen"]["duties"]
    }

    lines = [
        "# Current wood-joint engineering register",
        "",
        "Compact index of saved evidence for reviewed model. No complete-joint acceptance or physical release. Full axes, states, report fields and hashes: ignored machine register.",
        "",
        f"Rebuild: `uv run python {Path(__file__).name}`. Machine register: {output_link('joint-register-attempt01/register.json')} (SHA-256 `{machine_hash}`).",
        "",
        "## Census and source convention",
        "",
        "**24 blocks; 92 unique candidate bolt axes; 12 retained frame bolts; 96 block-axis incidences; 66 separate Hillman panel/kicker axes.** Continuous knee axes `knee_outer_{left,right}_side_{1,2}` each serve two block duties. Count each of four physical bolts and capacities once. Hillman axes remain separate; no resistance transfers.",
        "",
        f"Same-state signed forces: gap-scale 1.0 arrays in {source_link(COMPARISON, 'comparison.json')} and {source_link(RESPONSE, 'response.npz')}; mapped through {source_link(ROWS, 'row-identities.json')} and {source_link(MODEL, 'model.json')}. Cases: `{', '.join(register['case_ids'])}`. V = magnitude per saved plane; T = largest signed outer-seat tension. Peaks are separate states/axes; planes are never summed.",
        "",
        f"Clearance applies to six hosts: {', '.join(f'`{name}`' for name in force['clearance_joint_hosts'])}. Other bolted joints retain source zero-clearance stiffness. {source_link('member-screen-attempt02/all-outer-clearance01/member-results.csv', 'Member results')} are elementary member screens, not joint resistance.",
        "",
        "## Current methods",
        "",
        f"**HJC** = current separate six-header method: {source_link(HEADER_REPORT, 'header-joint-checks.md')} / {source_link('header-joint-attempt01/checks.json', 'checks.json')}; 72 bolt states, 36 interfaces, 42 body balances. Maximum lateral reference **{header_lateral['same_state_V_over_Ceg_Z_Cg_sensitivity']:.6f}** at `{header_lateral['case_id']}` / `{header_lateral['axis_id']}`; maximum washer reference **{header_washer['pressure_over_reference']:.6f}** at `{header_washer['case_id']}` / `{header_washer['axis_id']}`. Report keeps complete-joint acceptance false. † Marks six covered block rows.",
        "",
        f"**Service-24** = current lower-service individual-reference report, {source_link(SERVICE_RESULT, '24 saved signed states')}. Peak **92 ksi {service_peak['ratio_92ksi']:.6f}** (**45 ksi {service_peak['ratio_45ksi']:.6f}**) at `{service_peak['case_id']}` / `{axis_tail(service_peak['axis_id'])}`; same-state V/T = **{service_peak['shear_n']:.7f}/{service_peak['simultaneous_tension_n']:.8f} N**. Zero-force lateral direction, angle and reference fields stay null. This closes source-set comparison gap; complete-joint acceptance stays false.",
        "",
        f"**Central-seat** = {source_link(PARTIAL_SEAT_RESULT, 'current preserved-geometry report')}: six states; peak tie **{partial_peak['signed_tie_n']:.6f} N**, central wood pressure/reference **{partial_peak['central_mean_pressure_over_Fc_perp']:.6f}** at `{partial_peak['case_id']}`. Attempt 01 differed by producer format; six state records match. HJC remains six-joint force baseline. Central-ring pressure remains conditional; outer washer crescent unsupported.",
        "",
        f"Other report keys: **G5-92** = conditional Grade 5 92 ksi individual plane screen ({source_link(f'{GRADE}/screen.json', 'screen.json')}, {source_link(f'{GRADE}/bolt-states.csv', 'bolt-states.csv')}); **top comp** / **axial-reserved comp** = {source_link('corner-component-attempt04/component-results.json', 'top component')} / {source_link('corner-component-attempt04/steel-interaction.json', 'steel interaction')}; **bottom comp** = {source_link('bottom-corner-component-attempt05/component-results.json', 'bottom component')}; **end-grain individual** = {source_link('end-grain-route-attempt02/route.json', 'end-grain route')}; **3-receiver** = {source_link(f'{THREE}/screen.json', 'screen')} with saved {source_link(f'{THREE}/group-states.csv', 'group/contact states')} and {source_link(f'{THREE}/receiver-wrenches.csv', 'receiver transfer')}. Component ratios remain component results. None closes a complete joint. Parent retains unresolved joints and integrated law calculations.",
        "",
        "## Connector blocks",
        "",
        "Host column gives axis prefix with `_1/_2` range; row names block. Peaks show case and axis suffix; V also names plane. Method values retain source scope. `T+` is signed tension maximum. N throughout.",
        "",
        "| Block | Host / duty prefix and axes | V peak | T peak | Current method + peak | Exact open item |",
        "|---|---|---|---|---|---|",
    ]
    for block in register["blocks"]:
        peak = block["separate_magnitude_peaks"]
        v_text = (
            f"{peak['V_peak_n']:.1f} @ {peak['V_case_id']}/"
            f"{axis_tail(peak['V_axis_id'])}/{axis_tail(peak['V_plane_id'])}"
        )
        t_text = (
            f"{peak['T_peak_signed_n']:.1f} @ {peak['T_case_id']}/"
            f"{axis_tail(peak['T_axis_id'])}"
        )
        methods = grade5_method_items(block, register)
        methods.extend(special_method_items(block, register))
        if block["block_id"] in header_blocks:
            methods.append("HJC†")
        method_text = "<br>".join(methods) or "No saved joint ratio in named reports"
        lines.append(
            f"| `{block['block_id']}` | {compact_host_duties(block)} | "
            f"{v_text} | {t_text} | {method_text} | "
            f"{open_item(block, header_blocks)} |"
        )

    lines.extend(
        [
            "",
            "## Retained frame bolts",
            "",
            "Six arrangements; each row names exact receiver pair and `_1/_2` axes.",
            "",
            "| Arrangement | Receivers / axes | Separate V / T peaks | G5-92 method + peak | Exact open item |",
            "|---|---|---|---|---|",
        ]
    )
    for arrangement in register["retained_frame_bolt_arrangements"]:
        duty = grade_duties[arrangement["grade5_duty_id"]]
        result = duty["governing_92ksi"]
        peak = arrangement["separate_magnitude_peaks"]
        v_text = (
            f"V {peak['V_peak_n']:.1f} @ {peak['V_case_id']}/"
            f"{axis_tail(peak['V_axis_id'])}/{axis_tail(peak['V_plane_id'])}"
        )
        t_text = (
            f"T+ {peak['T_peak_signed_n']:.1f} @ {peak['T_case_id']}/"
            f"{axis_tail(peak['T_axis_id'])}"
        )
        method = (
            f"{result['ratio_92ksi']:.3f} {result['mode_92ksi']} @ "
            f"{result['case_id']}/{axis_tail(result['axis_id'])}/"
            f"{axis_tail(result['plane_id'])}"
        )
        axes = f"`{arrangement['arrangement_id']}_{{1,2}}`"
        lines.append(
            f"| `{arrangement['arrangement_id']}` | "
            f"`{arrangement['receivers'][0]}` ↔ `{arrangement['receivers'][1]}`; "
            f"{axes} | {v_text}; {t_text} | {method} | "
            "Individual wood-interface reference only; full connection interaction/transfer absent. |"
        )

    lines.extend(
        [
            "",
            "## Exact coverage gaps",
            "",
            "Grade 5 covers 80 candidate axes and 12 retained axes; its 92 ksi value is conditional on product conformity. Eight top axes have only the linked component scenarios. The former lower-service source-set gap is covered by the current 24-state result above; historical 84 worker-state references remain historical, not current parent comparisons.",
            "",
            "The three-receiver study records contact transfer for four shared knee axes; it does not close shared-bolt bending/load split, washer transfer, endpoint admissibility, finished-wood or frame-chain reconciliation. Header report's exact remaining fact is loaded-edge selection for five oblique end-grain states; first-face 4D results remain diagnostics, not adopted failures. Clearance, contact, source assumptions and each report's limits remain bound in machine JSON.",
            "",
            f"Machine record holds exact physical axes, six per-axis case states, plane V, signed T, saved method records and hashes. No resistance check or force/method result is added by this register. Source hashes for comparison/response: `{force['comparison_sha256']}` / `{force['response_sha256']}`.",
            "",
        ]
    )
    return "\n".join(lines)

def main() -> None:
    register = parse_register()
    OUTPUT.mkdir(exist_ok=True)
    machine = OUTPUT / "register.json"
    machine.write_text(json.dumps(register, indent=2, sort_keys=True, allow_nan=False) + "\n")
    digest = hashlib.sha256(machine.read_bytes()).hexdigest()
    (PACKET / "joint-register.md").write_text(render_markdown(register, digest))
    print(f"blocks={register['accounting']['connector_block_bodies']}")
    print(f"candidate_axes={register['accounting']['candidate_unique_physical_bolt_axes']}")
    print(f"retained_axes={register['accounting']['retained_frame_bolt_axes']}")
    print(f"shared_axes={register['accounting']['shared_axis_counted_once_in_physical_axis_register']}")
    print(f"register_sha256={digest}")


if __name__ == "__main__":
    main()
