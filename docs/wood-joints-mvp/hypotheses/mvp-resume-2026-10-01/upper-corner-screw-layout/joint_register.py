"""Index frozen current forces and component receipts without solving the frame."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = PACKET.parents[3]
PREFIX = "upper-corner-screw-layout/"
FRAME = PREFIX + "operators-attempt02/"
FORCES = PREFIX + "frame-250-attempt02/"
COMPARISON = FORCES + "comparison.json"
RESPONSE = FORCES + "response.npz"
MODEL = FRAME + "model.json"
ROWS = FRAME + "row-identities.json"
CASE_IDS = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
SHARED_AXES = {
    f"knee_outer_{side}_side_{number}"
    for side in ("left", "right")
    for number in (1, 2)
}
FROZEN = {
    "joint_register.py": "63379b7506e75d6d0054b64fed852f8c69f5b0c3352a221733746c33ba912d32",
    COMPARISON: "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    RESPONSE: "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    MODEL: "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    FRAME + "operator-assessment.json": "1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a",
    FRAME + "operators.npz": "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
}
# These are fresh receipts for the current response, not historical comparisons.
REPORTS = {
    "remaining": (PREFIX + "bolted-replay-results/remaining-attempt02/screen.json", "abe988897087ad9d07f94c5def6a7427cfeb9c493a26ef50d3d13b8baac94d45"),
    "top": (PREFIX + "bolted-replay-results/corner-attempt01/component-results.json", "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6"),
    "bottom": (PREFIX + "bolted-replay-results/bottom-attempt01/component-results.json", "ec421ee35b9477842660faa6d2528bd957f8a06620f7d84c46d9654e40ce146a"),
    "central_seat": (PREFIX + "bolted-replay-results/central-seat-attempt01/result.json", "a058f494bc4a733e90c0ee954f38634abadceac4c24273b92dab4434cac42b33"),
    "service": ("service-joint-current-attempt03/four-screw-250-attempt03/result.json", "850a31de41efc8e710cb45660f9822852469303e0e391fb70ed325977558293c"),
    "end_grain": ("end-grain-route-attempt03/four-screw-250-attempt02/route.json", "277e7754b2c62e5a98d140de497c753a7cd0362080cef10185cc79be549f3261"),
    "knee": ("three-member-screen-attempt02/four-screw250/screen.json", "ccd5b3bef3ff48a2468b47cc73da984f2a9ec7421e624bce3929032107ca17ba"),
    "knee_bearing": ("knee-bearing-attempt02/checks.json", "b56cc77e8a088f5cf7c1b6a84d8b8844cdfe335ecd2d2da68d6da138f0f2facb"),
    "knee_fit": ("knee-bore-fit-attempt03/fit.json", "d4c8f42e2103082c2e11f29c21b99bd8d1f65e59a6570417b86401a5683af49e"),
    "header": ("header-joint-attempt04/four-screw-250-attempt02/checks.json", "f34fba71b0416cf7a5d1081a48c66c8d518b642e53e7f7f8a80a0646b707362d"),
    "retained_group": ("retained-group-attempt02/checks.json", "c64a84c44855b3fecc53259cecd693105dec8d10b2a9dbef94aa1118fca09ef8"),
    "retained_washer": ("retained-washer-attempt02/checks.json", "f23e2f0c9c1b32aa37f53416de95f7ed97257e704b638a6f94b1d043aec1420b"),
    "members": ("member-screen-attempt02/four-screw-layout01/member-results.json", "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5"),
    "member_stability": ("member-stability-attempt01/four-screw-layout01/checks.json", "aceebc0beaee1cc178450b52b2a16a32924803c3210dc0c115c0fee7a3a7c574"),
}
UNAVAILABLE = {
    "actual_hardware_resistance_n": None,
    "coupled_axial_lateral_bolt_resistance_n": None,
    "complete_group_and_splitting_resistance_n": None,
    "actual_supported_washer_pressure_mpa": None,
    "washer_metal_resistance_n": None,
    "complete_receiver_transfer_acceptance": None,
    "complete_joint_resistance_n": None,
    "complete_joint_acceptance": None,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_register() -> tuple[dict[str, Any], dict[Path, str]]:
    pins: dict[Path, str] = {}
    inherited_receipt_differences = []

    def pin(path: Path, expected: str | None = None) -> None:
        path = path.resolve()
        actual = digest(path)
        expected = expected or actual
        require(actual == expected, f"source hash differs: {path}")
        require(path not in pins or pins[path] == expected, f"conflicting source pins: {path}")
        pins[path] = expected

    def pin_map(mapping: dict[str, str]) -> None:
        for name, expected in mapping.items():
            path = Path(name)
            pin(path if path.is_absolute() else ROOT / path, expected)

    for relative, expected in {**FROZEN, **dict(REPORTS.values())}.items():
        pin(PACKET / relative, expected)
    pin(Path(__file__))

    # Reuse only pure saved-source helpers; never call the historical producer.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("saved_register_helpers", PACKET / "joint_register.py")
    require(spec is not None and spec.loader is not None, "saved register helper unavailable")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    load_json, load_csv, close = helper.load_json, helper.load_csv, helper.assert_close

    def receipt(relative: str) -> dict[str, Any]:
        report = load_json(relative)
        for name, expected in report.get("source_sha256", {}).items():
            path = Path(name)
            path = (path if path.is_absolute() else ROOT / path).resolve()
            if (
                relative == REPORTS["member_stability"][0]
                and path == PACKET / "bottom_corner_checks.py"
                and expected == "2afb5a8af006c4ae4818e863bc4300d4e63d070a816dd5e96079718d8ede57c3"
            ):
                snapshot = PACKET / "bottom-corner-component-attempt06/producer.py.snapshot"
                current_sha = "5df7a264354e1488c2a68332820fe927e8dcb1fa9721111ec8fac5c00ad19e26"
                pin(snapshot, expected)
                pin(path, current_sha)
                old_line = '"reviewed_geometry_changed": False,'
                new_line = '"reviewed_geometry_changed": member_report.get("reviewed_geometry_changed", False),'
                old_source = snapshot.read_text()
                require(
                    old_source.count(old_line) == 1
                    and old_source.replace(old_line, new_line) == path.read_text(),
                    "inherited member helper differs beyond geometry-change reporting",
                )
                inherited_receipt_differences.append({
                    "receipt": relative,
                    "recorded_source": str(path.relative_to(ROOT)),
                    "recorded_sha256": expected,
                    "authenticated_snapshot": str(snapshot.relative_to(ROOT)),
                    "current_maintained_sha256": current_sha,
                    "difference": "Only reviewed_geometry_changed reporting changed; no numerical helper code differs.",
                    "scope": "Preserved upstream provenance, not a claim that the maintained file matches its older receipt. Neither helper version is executed by this index.",
                })
            else:
                pin(path, expected)
        for name, expected in report.get("output_sha256", {}).items():
            pin(PACKET / Path(relative).parent / name, expected)
        companion = PACKET / Path(relative).parent / "source-pins.json"
        if companion.exists():
            pin(companion)
            source_pins = json.loads(companion.read_text())
            if "rechecked_sha256" in source_pins:
                pin_map(source_pins["rechecked_sha256"])
                pin_map(source_pins["frame_source_pins"])
                # The remaining receipt explicitly keeps earlier geometry pipeline pins as provenance.
            else:
                pin_map(source_pins)
        snapshot = PACKET / Path(relative).parent / "producer.py.snapshot"
        if snapshot.exists():
            pin(snapshot, report.get("producer_sha256"))
        return report

    model = load_json(MODEL)
    rows = load_json(ROWS)
    assessment = receipt(FRAME + "operator-assessment.json")
    comparison = receipt(COMPARISON)
    require(comparison["response_sha256"] == FROZEN[RESPONSE], "comparison response binding differs")
    require(model["physical_release"] is False, "source model claims physical release")
    require(assessment["complete_joint_acceptance"] is False, "operator receipt claims joint acceptance")
    nominal = [state for state in comparison["states"] if state["gap_scale"] == 1.0]
    require([state["case_id"] for state in nominal] == CASE_IDS, "nominal case order differs")
    require(comparison["complete_joint_acceptance"] is False and comparison["physical_release"] is False,
            "force receipt claims joint acceptance or release")
    require(len(rows) == len({row["row"] for row in rows}) == 1888, "current raw row census differs")

    reports = {name: receipt(relative) for name, (relative, _sha) in REPORTS.items()}
    for name, report in reports.items():
        scope = next((report[key] for key in ("source_force_state_scope", "force_state_scope", "source_scope", "source_force_scope") if key in report), None)
        require(scope is not None and scope["bounded_nominal_cases"] == CASE_IDS,
                f"current nominal force scope differs: {name}")
        require(scope["complete_joint_acceptance"] is False and scope["physical_release"] is False,
                f"source scope claims joint acceptance or release: {name}")
        require(report.get("case_ids", CASE_IDS) == CASE_IDS, f"case order differs: {name}")
        require(report.get("complete_joint_acceptance", False) is False and report["physical_release"] is False,
                f"method claims joint acceptance or release: {name}")
        for key in ("source_response_sha256", "response_sha256"):
            require(key not in report or report[key] == FROZEN[RESPONSE], f"response binding differs: {name}")
        for key in ("source_comparison_sha256", "clearance_comparison_sha256"):
            require(key not in report or report[key] == FROZEN[COMPARISON], f"comparison binding differs: {name}")

    blocks = {
        name for name in model["body_names"]
        if name.endswith("_cleat") or "_cleat_" in name
        or name.startswith(("knee_outer_left_", "knee_outer_right_"))
        and name.endswith(("_spine", "_inner_frame_block"))
    }
    require(len(blocks) == 24, "connector block census differs")
    ties, withdrawals = {}, {}
    planes: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    screw_planes: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        role, identity = row["ownership"]["role"], row["row_id"]
        if role in ("physical_bolt_outer_seat_tension", "non_qualifying_parametric_screw_withdrawal"):
            suffix = "/outer-seat-axial-tie" if role == "physical_bolt_outer_seat_tension" else "/parametric-withdrawal"
            require(identity.endswith(suffix), f"unexpected axial identity: {identity}")
            target = ties if role == "physical_bolt_outer_seat_tension" else withdrawals
            axis_id = identity.removesuffix(suffix)
            require(axis_id not in target, f"duplicate axial row: {axis_id}")
            target[axis_id] = row
        elif role in ("candidate_bolt_lateral_plane", "retained_bolt_lateral_plane", "panel_screw_lateral_plane"):
            axis_id, separator, _plane = identity.rpartition("/")
            require(bool(separator), f"unexpected lateral identity: {identity}")
            target = screw_planes if role == "panel_screw_lateral_plane" else planes
            target[axis_id][identity].append(row)

    def map_axes(axial_rows: dict[str, Any], lateral_rows: dict[str, Any], screw: bool = False) -> dict[str, Any]:
        require(set(axial_rows) == set(lateral_rows), "axial/lateral axis census differs")
        result = {}
        for axis_id, tie in sorted(axial_rows.items()):
            interfaces = []
            for plane_id, components in sorted(lateral_rows[axis_id].items()):
                components = sorted(components, key=lambda row: row["row"])
                require(len(components) == 2, f"lateral component census differs: {plane_id}")
                ownership = components[0]["ownership"]
                receivers = [ownership["first_body"], ownership["second_body"]]
                require(all([row["ownership"]["first_body"], row["ownership"]["second_body"]] == receivers for row in components),
                        f"lateral receiver order differs: {plane_id}")
                directions = [row["ownership"]["direction_global_xyz"] for row in components]
                close(sum(a * b for a, b in zip(*directions)), 0.0, plane_id + " orthogonality")
                for direction in directions:
                    close(math.sqrt(sum(value * value for value in direction)), 1.0, plane_id + " unit direction")
                interfaces.append({"plane_id": plane_id, "receivers": receivers,
                                   "point_xyz_mm": ownership["point_mm"],
                                   "component_rows": [row["row"] for row in components],
                                   "component_row_ids": [row["row_id"] for row in components],
                                   "component_directions_xyz": directions,
                                   "block_ids_on_interface": sorted(set(receivers) & blocks) if not screw else []})
            ownership = tie["ownership"]
            block_ids = sorted({body for interface in interfaces for body in interface["receivers"]} & blocks) if not screw else []
            if not screw:
                require(block_ids == sorted({ownership["first_body"], ownership["second_body"]} & blocks),
                        f"tie/interface block census differs: {axis_id}")
            kind = "panel_kicker_screw" if screw else "candidate_bolt" if block_ids else "retained_bolt"
            result[axis_id] = {"axis_id": axis_id, "kind": kind, "block_ids": block_ids,
                               "receivers": sorted({body for interface in interfaces for body in interface["receivers"]}),
                               "interfaces": interfaces, "outer_tie": {"row": tie["row"], "row_id": tie["row_id"], **ownership},
                               "unavailable_criteria": dict(UNAVAILABLE), "full_joint_status": "HOLD", "per_state": []}
            if screw:
                result[axis_id]["unavailable_criteria"].update({"Hillman_lateral_resistance_n": None, "Hillman_withdrawal_resistance_n": None,
                                                               "Hillman_head_pullthrough_resistance_n": None,
                                                               "qualified_Hillman_stiffness_n_per_mm": None})
        return result

    axes, screws = map_axes(ties, planes), map_axes(withdrawals, screw_planes, True)
    candidate = {axis for axis, record in axes.items() if record["kind"] == "candidate_bolt"}
    retained = set(axes) - candidate
    shared = {axis for axis in candidate if len(axes[axis]["block_ids"]) > 1}
    require((len(candidate), len(retained), len(screws)) == (92, 12, 66), "physical axis census differs")
    require(shared == SHARED_AXES, "shared physical knee axis census differs")
    require(sum(len(axes[axis]["block_ids"]) for axis in candidate) == 96, "block incidence census differs")
    require(sum(len(axis["interfaces"]) for axis in axes.values()) == 108, "bolt interface census differs")

    state_index = {}
    with np.load(PACKET / RESPONSE, allow_pickle=False) as saved:
        for case_id in CASE_IDS:
            key = case_id + "_gap_raw_force_n"
            require(key in saved.files, f"missing current nominal force vector: {key}")
            force = saved[key]
            require(force.shape == (1888,) and np.isfinite(force).all(), f"invalid current force vector: {key}")
            for axis in [*axes.values(), *screws.values()]:
                tie = axis["outer_tie"]
                tension = float(force[tie["row"]])
                axial_vector = [tension * value for value in tie["direction_global_xyz"]]
                state = {"case_id": case_id, "source_key": key, "gap_scale": 1.0,
                         "outer_tie_signed_n": tension, "outer_tie_row": tie["row"], "interfaces": [],
                         "axial_seats": [{"member": tie["first_body"], "tie_sign": 1, "signed_tie_n": tension, "force_on_member_xyz_n": axial_vector},
                                         {"member": tie["second_body"], "tie_sign": -1, "signed_tie_n": tension, "force_on_member_xyz_n": [-value for value in axial_vector]}],
                         "component_references": []}
                for interface in axis["interfaces"]:
                    components = [float(force[row]) for row in interface["component_rows"]]
                    vector = [sum(component * direction[index] for component, direction in zip(components, interface["component_directions_xyz"])) for index in range(3)]
                    state["interfaces"].append({"plane_id": interface["plane_id"], "component_rows": interface["component_rows"],
                                                "components_n": components, "force_on_first_xyz_n": vector,
                                                "force_on_second_xyz_n": [-value for value in vector], "V_resultant_n": math.hypot(*components)})
                axis["per_state"].append(state)
                state_index[case_id, axis["axis_id"]] = state

    methods = {}

    def attach(name: str, source: str, records: list[dict[str, Any]], field: str,
               shear_field: str | None = None, tie_field: str | None = None) -> None:
        coverage = set()
        for index, record in enumerate(records):
            case_id, axis_id = record["case_id"], record["axis_id"]
            require(case_id in CASE_IDS and axis_id in axes, f"method axis/state outside current register: {name}")
            state = state_index[case_id, axis_id]
            if "gap_scale" in record:
                require(record["gap_scale"] == 1.0, f"non-nominal method record: {name}")
            interface = next((plane for plane in state["interfaces"] if plane["plane_id"] == record.get("plane_id")), None)
            if shear_field:
                require(interface is not None or len(state["interfaces"]) == 1, f"ambiguous lateral method record: {name}/{axis_id}")
                interface = interface or state["interfaces"][0]
                close(interface["V_resultant_n"], record[shear_field], f"{name}/{case_id}/{axis_id}/V")
            if tie_field:
                close(state["outer_tie_signed_n"], record[tie_field], f"{name}/{case_id}/{axis_id}/T")
            # Store exact source values, including unavailable nulls, without copying bulky geometry.
            reference = {key: value for key, value in record.items()
                         if any(word in key.lower() for word in ("reference", "ratio", "pressure", "stress", "utilization", "capacity", "acceptance", "cg", "cdelta", "ceg", "fyb", "margin", "placement_found", "supported_area", "washer_seats"))}
            locator = {"csv_row_index_zero_based": index} if field == "csv_rows" else {
                "record_pointer": f"/{field}/{record.get('_source_record_index', index)}" if field else f"/{index}"}
            state["component_references"].append({"method": name, "source": source, **locator,
                                                   "plane_id": record.get("plane_id"), "member": record.get("member"),
                                                   "comparisons": reference})
            coverage.add(axis_id)
        methods[name]["indexed_physical_axis_ids"] = sorted(coverage)
        methods[name]["indexed_nominal_records"] = len(records)
        methods[name]["indexed_state_source"] = source

    for name, report in reports.items():
        relative = REPORTS[name][0]
        methods[name] = {"source": relative, "sha256": FROZEN.get(relative, REPORTS[name][1]),
                         "schema": report["schema"], "counts": report.get("counts", {}),
                         "limits": report.get("limits", report.get("method_limits", report.get("formal_gaps", []))),
                         "complete_joint_acceptance": False, "physical_release": False,
                         "full_joint_status": "HOLD", "indexed_physical_axis_ids": []}

    remaining_dir = str(Path(REPORTS["remaining"][0]).parent)
    remaining_states = load_csv(remaining_dir + "/bolt-states.csv")
    washer_states = load_csv(remaining_dir + "/washer-reference-states.csv")
    require(len(remaining_states) == 576 and len(washer_states) == 1104, "remaining method state census differs")
    attach("remaining", remaining_dir + "/bolt-states.csv", remaining_states, "csv_rows", "shear_resultant_n", "outer_tie_signed_n")
    methods["remaining_washer"] = {**methods["remaining"], "counts": {"outer_seat_states": 1104},
                                     "limits": "Ideal full annulus only; actual pressure and washer metal resistance remain null."}
    attach("remaining_washer", remaining_dir + "/washer-reference-states.csv", washer_states, "csv_rows", tie_field="outer_tie_signed_n")
    missing = candidate - set(methods["remaining"]["indexed_physical_axis_ids"])
    require(missing == set(reports["remaining"]["excluded_top_axes"] + reports["remaining"]["excluded_worker_axes"]), "remaining exclusions differ")
    methods["remaining"]["excluded_candidate_axis_ids"] = sorted(missing)
    for name, shear, tie in [("top", "lateral_n", "tension_n"), ("bottom", "shear_n", "tension_n"),
                             ("service", "shear_n", "simultaneous_tension_n"), ("central_seat", None, "signed_tie_n")]:
        records = reports[name]["states"]
        if name == "central_seat":
            records = [{**record, "axis_id": reports[name]["axis_id"]} for record in records]
        attach(name, REPORTS[name][0], records, "states", shear, tie)
    route_dir = str(Path(REPORTS["end_grain"][0]).parent)
    route_states = load_csv(route_dir + "/six-case-signed-states.csv")
    require(len(route_states) == 72, "end-grain state census differs")
    attach("end_grain", route_dir + "/six-case-signed-states.csv", route_states, "csv_rows", "shear_resultant_n", "outer_tie_signed_n")
    attach("knee", REPORTS["knee"][0], reports["knee"]["bolt_cases"], "bolt_cases", tie_field="outer_tie_signed_n")
    for record in reports["knee"]["bolt_cases"]:
        state = state_index[record["case_id"], record["axis_id"]]
        for plane in record["planes"]:
            current = next(item for item in state["interfaces"] if item["plane_id"] == plane["plane_id"])
            require(current["component_rows"] == plane["raw_rows"], "knee component rows differ")
            for actual, expected in zip(current["components_n"], plane["signed_components_n"]):
                close(actual, expected, "knee signed component")
            state["component_references"].append({"method": "knee", "source": REPORTS["knee"][0],
                                                   "plane_id": plane["plane_id"], "record_selector": {"case_id": record["case_id"], "axis_id": record["axis_id"]},
                                                   "comparisons": {"single_shear_endpoint_references": plane["single_shear_endpoint_references"],
                                                                   "normative_asymmetric_reference_n": None}})
    attach("knee_bearing", REPORTS["knee_bearing"][0], reports["knee_bearing"]["states"], "states", tie_field="outer_tie_signed_n")
    nominal_fits = [{**record, "_source_record_index": index} for index, record in enumerate(reports["knee_fit"]["records"]) if record["gap_scale"] == 1.0]
    attach("knee_fit", REPORTS["knee_fit"][0], nominal_fits, "records")
    methods["knee_fit"].update({"source_records_all_gaps": len(reports["knee_fit"]["records"]),
                                "source_gap_scales": [0.0, 1.0], "nominal_index_only": True})
    header_dir = str(Path(REPORTS["header"][0]).parent)
    header_states = load_json(header_dir + "/joint-states.json")
    attach("header", header_dir + "/joint-states.json", header_states, "", "shear_n", "tension_n")
    attach("retained_group", REPORTS["retained_group"][0], reports["retained_group"]["axis_states"], "axis_states", tie_field="saved_outer_tie_signed_n")
    attach("retained_washer", REPORTS["retained_washer"][0], reports["retained_washer"]["states"], "states", tie_field="simultaneous_signed_tie_n")

    methods["service"]["counts"] = {"axes": reports["service"]["axis_count"], "states": reports["service"]["state_count"]}
    methods["end_grain"]["counts"] = {"axes": reports["end_grain"]["axis_count"], "states": reports["end_grain"]["state_count"]}
    methods["knee"]["counts"] = {"physical_axes": 4, "bolt_cases": reports["knee"]["bolt_case_count"],
                                      "plane_states": sum(len(record["planes"]) for record in reports["knee"]["bolt_cases"]),
                                      "group_states": reports["knee"]["group_case_count"]}
    methods["knee_bearing"]["counts"] = {"bolt_fields": len(reports["knee_bearing"]["states"]),
                                              "endpoint_witnesses": len(reports["knee_bearing"]["endpoint_fields"])}
    methods["knee_fit"]["counts"] = {"both_gap_placements": reports["knee_fit"]["placement_count"],
                                          "nominal_placements_indexed": len(nominal_fits)}
    methods["retained_washer"]["counts"] = {"seats": len(reports["retained_washer"]["unique_seats"]),
                                                 "states": len(reports["retained_washer"]["states"])}
    placement = load_json(header_dir + "/placement.json")
    methods["header"]["placement_counts"] = {
        "null_first_ray_states": sum(record["first_intersected_source_envelope_face"] is None for record in placement),
        "directional_states": sum(record["first_intersected_source_envelope_face"] is not None for record in placement),
        "short_first_ray_diagnostics": len(reports["header"]["first_face_below_4D_diagnostics"]),
    }
    methods["header"]["exact_remaining_detailing_fact"] = reports["header"]["exact_remaining_detailing_fact"]
    methods["member_stability"]["global_bore_free_peaks"] = reports["member_stability"]["global_bore_free_peaks"]
    for name, report in reports.items():
        methods[name]["source_collection_coverage"] = {
            field: {"records": len(records), "axis_ids": sorted({record["axis_id"] for record in records if "axis_id" in record})}
            for field, records in report.items() if isinstance(records, list) and records and isinstance(records[0], dict)
        }

    expected_coverage = {"top": (8, 48), "bottom": (8, 48), "central_seat": (1, 6), "service": (4, 24),
                         "end_grain": (12, 72), "knee": (4, 24), "knee_bearing": (4, 24), "knee_fit": (4, 48),
                         "header": (12, 72), "retained_group": (12, 72), "retained_washer": (12, 144)}
    for name, expected in expected_coverage.items():
        require((len(methods[name]["indexed_physical_axis_ids"]), methods[name]["indexed_nominal_records"]) == expected,
                f"fresh method coverage differs: {name}")
    require(set(methods["remaining"]["indexed_physical_axis_ids"]) | set(methods["top"]["indexed_physical_axis_ids"]) | set(methods["service"]["indexed_physical_axis_ids"]) == set(axes),
            "fresh component coverage does not reconcile to physical bolts")

    member_map = {record["member"]: index for index, record in enumerate(reports["member_stability"]["members"])}
    require(len(member_map) == 44 and blocks <= member_map.keys(), "fresh member coverage differs")
    for axis in [*axes.values(), *screws.values()]:
        axis["member_evidence"] = [{"member": member, "source": REPORTS["member_stability"][0], "record_pointer": f"/members/{member_map[member]}"}
                                   for member in axis["receivers"] if member in member_map]
        axis["method_ids"] = sorted({reference["method"] for state in axis["per_state"] for reference in state["component_references"]})
    for name in ("members", "member_stability"):
        methods[name]["member_ids"] = sorted(member_map)
        methods[name]["indexed_physical_axis_ids"] = sorted(axis_id for axis_id, axis in axes.items() if axis["member_evidence"])
        methods[name]["scope"] = "Member calculations retain their declared section, restraint and shear/torsion limits; no joint resistance is assigned."

    def summary(ids: list[str], block_id: str | None = None) -> dict[str, Any]:
        incident = {axis_id: {plane["plane_id"] for plane in axes[axis_id]["interfaces"]
                              if block_id is None or block_id in plane["receivers"]} for axis_id in ids}
        scoped_axes = {axis_id: {**axes[axis_id], "per_state": [
            {**state, "interfaces": [plane for plane in state["interfaces"] if plane["plane_id"] in incident[axis_id]]}
            for state in axes[axis_id]["per_state"]]} for axis_id in ids}
        peaks = helper.block_peaks(ids, scoped_axes)
        lateral_state = state_index[peaks["V_case_id"], peaks["V_axis_id"]]
        tension_state = state_index[peaks["T_case_id"], peaks["T_axis_id"]]
        comparisons = {}

        def ratios(value: Any, prefix: str = ""):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield from ratios(child, prefix + ("." if prefix else "") + key)
            elif isinstance(value, (int, float)) and not isinstance(value, bool) and any(word in prefix.lower() for word in ("ratio", "_over_", "utilization")):
                yield prefix, value

        for axis_id in ids:
            for state in axes[axis_id]["per_state"]:
                for reference in state["component_references"]:
                    if reference["plane_id"] is not None and reference["plane_id"] not in incident[axis_id]:
                        continue
                    for field, value in ratios(reference["comparisons"]):
                        key = reference["method"], field
                        if key not in comparisons or value > comparisons[key]["value"]:
                            comparisons[key] = {"method": reference["method"], "field": field, "value": value,
                                                "source": reference["source"], "case_id": state["case_id"], "axis_id": axis_id,
                                                "plane_id": reference["plane_id"], "member": reference.get("member"),
                                                "simultaneous_T_n": state["outer_tie_signed_n"]}
        return {"separate_magnitude_peaks": peaks,
                "peak_lateral": {"case_id": peaks["V_case_id"], "axis_id": peaks["V_axis_id"], "plane_id": peaks["V_plane_id"],
                                 "V_n": peaks["V_peak_n"], "simultaneous_T_n": lateral_state["outer_tie_signed_n"]},
                "peak_signed_outer_tie": {"case_id": peaks["T_case_id"], "axis_id": peaks["T_axis_id"], "signed_T_n": peaks["T_peak_signed_n"],
                                          "outer_seat_bodies": [seat["member"] for seat in tension_state["axial_seats"]],
                                          "simultaneous_interface_V_n": {plane["plane_id"]: plane["V_resultant_n"] for plane in tension_state["interfaces"] if plane["plane_id"] in incident[peaks["T_axis_id"]]}},
                "component_ratio_peaks": [comparisons[key] for key in sorted(comparisons)]}

    block_records = []
    for block in sorted(blocks):
        ids = sorted(axis for axis in candidate if block in axes[axis]["block_ids"])
        block_records.append({"block_id": block, "candidate_axis_ids": ids,
                              "physical_axis_count": len(ids), "shared_axis_ids": sorted(set(ids) & shared),
                              "receiver_interfaces": [{"axis_id": axis_id, **interface} for axis_id in ids for interface in axes[axis_id]["interfaces"] if block in interface["block_ids_on_interface"]],
                              "method_ids": sorted({name for axis in ids for name in axes[axis]["method_ids"]}),
                              **summary(ids, block),
                              "unavailable_criteria": dict(UNAVAILABLE), "full_joint_status": "HOLD"})
    retained_arrangements = [{"arrangement_id": duty["duty_id"], "physical_axis_ids": duty["axis_ids"],
                              "receivers": duty["receivers"], "method_ids": sorted({name for axis in duty["axis_ids"] for name in axes[axis]["method_ids"]}),
                              **summary(duty["axis_ids"]), "unavailable_criteria": dict(UNAVAILABLE), "full_joint_status": "HOLD"}
                             for duty in reports["remaining"]["duties"] if duty["kind"] == "retained_bolt"]
    require(len(retained_arrangements) == 6 and sum(len(item["physical_axis_ids"]) for item in retained_arrangements) == 12,
            "retained arrangement census differs")
    for path, expected in pins.items():
        require(digest(path) == expected, f"source changed during indexing: {path}")
    register = {
        "schema": "current_four_screw_nominal_joint_evidence_register/v1", "status": "HOLD",
        "candidate": model["candidate"], "source_revision": model["source_revision"],
        "development_revision": model["development_revision"], "reviewed_geometry_changed": model["reviewed_geometry_changed"],
        "owner_authorized_screw_movements": model["owner_authorized_screw_movements"],
        "complete_joint_acceptance": False, "physical_release": False, "case_ids": CASE_IDS,
        "accounting": {"connector_block_bodies": 24, "candidate_unique_physical_bolt_axes": 92,
                       "retained_frame_bolt_axes": 12, "total_unique_frame_bolt_axes": 104,
                       "candidate_block_axis_incidences": 96, "shared_physical_axes": sorted(shared),
                       "hillman_panel_kicker_axes_separate": 66, "nominal_bolt_axis_states": 624,
                       "nominal_bolt_interface_states": 648, "nominal_panel_kicker_screw_states": 396},
        "same_state_force_source": {"comparison": COMPARISON, "comparison_sha256": FROZEN[COMPARISON],
                                    "response": RESPONSE, "response_sha256": FROZEN[RESPONSE],
                                    "row_identity_source": ROWS, "model_source": MODEL, "gap_scale": 1.0,
                                    "force_key_pattern": "{case_id}_gap_raw_force_n", "nominal_source_states": nominal,
                                    "force_scope": reports["remaining"]["source_force_state_scope"],
                                    "source_limits": comparison["limits"]},
        "conventions": {"lateral": "Signed raw row components act along their declared directions on first receiver; the second receives the opposite vector. V is the two-component norm of one interface only. Interface magnitudes are never summed.",
                        "axial": "One signed outer-seat tie T per physical bolt supplies opposite receiver vectors. Both seat records refer to that same tie, not independent forces or verified head/nut bearing. Screw axial records are parametric withdrawal actions, not washer seats or Hillman resistance.",
                        "shared_axes": "Each continuous knee bolt is recorded once physically and appears in two block incidence lists; no duplicated physical demand or capacity is assigned.",
                        "provenance": "Earlier source files are hashed only where fresh receipts require provenance. Historical response arrays are never opened, and no historical force or acceptance is transferred.",
                        "criteria": "Null criteria mean unavailable complete results. Fresh conditional component comparisons retain their own hypotheses and limits; every full joint remains HOLD."},
        "axes": list(axes.values()), "blocks": block_records, "retained_frame_bolt_arrangements": retained_arrangements,
        "panel_kicker_screws": list(screws.values()), "methods": methods,
        "inherited_receipt_differences": inherited_receipt_differences,
        "source_sha256": {
            str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path): value
            for path, value in sorted(pins.items())
        },
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
    }
    return register, pins


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({key: json.dumps(value, separators=(",", ":")) if isinstance(value, (dict, list)) else value for key, value in row.items()} for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Fresh ignored output child; existing paths are refused.")
    output = parser.parse_args().output.resolve()
    require(not output.exists(), f"output already exists: {output}")
    register, pins = build_register()
    output.mkdir(parents=True, exist_ok=False)
    axis_rows, state_rows = [], []
    for axis in [*register["axes"], *register["panel_kicker_screws"]]:
        axis_rows.append({"axis_id": axis["axis_id"], "kind": axis["kind"], "block_ids": axis["block_ids"],
                          "receivers": axis["receivers"], "interfaces": len(axis["interfaces"]),
                          "axial_row": axis["outer_tie"]["row"], "method_ids": axis["method_ids"], "full_joint_status": "HOLD"})
        for state in axis["per_state"]:
            for plane in state["interfaces"]:
                state_rows.append({"case_id": state["case_id"], "axis_id": axis["axis_id"], "kind": axis["kind"],
                                   "plane_id": plane["plane_id"], "component_rows": plane["component_rows"],
                                   "signed_components_n": plane["components_n"], "force_on_first_xyz_n": plane["force_on_first_xyz_n"],
                                   "V_interface_n": plane["V_resultant_n"], "signed_T_shared_axial_row_n": state["outer_tie_signed_n"],
                                   "force_key": state["source_key"], "gap_scale": 1.0, "full_joint_status": "HOLD"})
    write_csv(output / "axes.csv", axis_rows)
    write_csv(output / "states.csv", state_rows)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    (output / ".gitignore").write_text("*\n")
    for path, expected in pins.items():
        require(digest(path) == expected, f"source changed before output completion: {path}")
    generated = {path.name: digest(path) for path in output.iterdir()}
    register["output_sha256"] = generated
    (output / "register.json").write_text(json.dumps(register, indent=2, sort_keys=True, allow_nan=False) + "\n")
    generated["register.json"] = digest(output / "register.json")
    (output / "source-pins.json").write_text(json.dumps({"source_sha256": register["source_sha256"],
                                                          "output_sha256": generated,
                                                          "complete_joint_acceptance": False, "physical_release": False},
                                                         indent=2, sort_keys=True) + "\n")
    for path, expected in pins.items():
        require(digest(path) == expected, f"source changed during output writing: {path}")
    print(json.dumps({"accounting": register["accounting"], "output": str(output), "register_sha256": generated["register.json"]}, sort_keys=True))


if __name__ == "__main__":
    main()
