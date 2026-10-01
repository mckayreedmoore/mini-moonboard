#!/usr/bin/env python3
"""Replay the bounded seven-pair contact-pressure and wrench extraction."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
REGISTER_REL = BASE / "current-six-case-corner-response-register-attempt04/register.json"
REGISTER_PRODUCER_REL = BASE / "current-six-case-corner-response-register-attempt04/produce.py"
PIN_PATH = HERE / "source-pins.json"
OUTPUT_PATH = HERE / "screen.json"
DATUM_XYZ_MM = [0.0, 0.0, 0.0]

CASE_SPECS = {
    "a12-rear": {
        "run_id": "current-springa-selected-floor-a12-rear-attempt03",
        "report": BASE / "current-corner-native-demand-export-attempt03/corner-demand-report.json",
        "model": BASE / "current-springa-selected-floor-a12-rear-attempt03/model.json",
        "response": BASE / "current-springa-selected-floor-a12-rear-attempt03/response.json",
    },
    "a1-rear": {
        "run_id": "springa-selected-a1-rear-attempt02",
        "report": BASE / "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
        "model": BASE / "current-springa-selected-floor-a1-rear-attempt02/model.json",
        "response": BASE / "current-springa-selected-floor-a1-rear-attempt02/response-zero-u-token.json",
    },
    "k12-rear": {
        "run_id": "k12-rear-spr489-direct-attempt01",
        "report": BASE / "current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json",
        "model": BASE / "current-k12-rear-spr489-direct-native-attempt01/model.json",
        "response": BASE / "current-k12-rear-spr489-direct-native-attempt01/response.json",
    },
}

TARGET_PAIRS = [
    ("post-spine", "base_post_outer_left", "knee_outer_left_spine"),
    ("spine-side", "knee_outer_left_spine", "base_side_left"),
    ("side-innerblock", "base_side_left", "knee_outer_left_inner_frame_block"),
    ("block-header", "knee_outer_left_inner_frame_block", "base_header"),
    ("header-post", "base_header", "base_post_outer_left"),
    ("header-side", "base_header", "base_side_left"),
    ("header-spine", "base_header", "knee_outer_left_spine"),
]


class ScreenError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScreenError(f"cannot read JSON {path}: {exc}") from exc


def source_path(rel: str | Path) -> Path:
    return ROOT / Path(rel)


def close(a: float, b: float, *, atol: float = 1e-9, rtol: float = 1e-10) -> bool:
    return math.isclose(float(a), float(b), abs_tol=atol, rel_tol=rtol)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScreenError(message)


def dot(a: list[float], b: list[float]) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b, strict=True))


def vadd(a: list[float], b: list[float]) -> list[float]:
    return [float(x) + float(y) for x, y in zip(a, b, strict=True)]


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def vector_close(a: list[float], b: list[float], *, atol: float = 1e-9) -> bool:
    return len(a) == len(b) and all(close(x, y, atol=atol) for x, y in zip(a, b, strict=True))


def point_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b, strict=True)))


def moment_radius(point_from_datum: list[float], force_radius: list[float]) -> list[float]:
    x, y, z = point_from_datum
    rx, ry, rz = force_radius
    return [abs(y) * rz + abs(z) * ry, abs(z) * rx + abs(x) * rz, abs(x) * ry + abs(y) * rx]


def interval(center: float, radius: float) -> list[float]:
    return [float(center) - float(radius), float(center) + float(radius)]


def vector_intervals(center: list[float], radius: list[float]) -> list[list[float]]:
    return [interval(value, rad) for value, rad in zip(center, radius, strict=True)]


def freeze_source_pins() -> None:
    if PIN_PATH.exists():
        raise ScreenError(f"refusing to replace existing source freeze: {PIN_PATH}")
    register_path = source_path(REGISTER_REL)
    register = read_json(register_path)
    source_map = register.get("source_pins_sha256", {})
    case_records = {row["case_id"]: row for row in register.get("cases", [])}
    files: dict[str, str] = {
        str(REGISTER_REL): sha256(register_path),
        str(REGISTER_PRODUCER_REL): sha256(source_path(REGISTER_PRODUCER_REL)),
    }
    cases: dict[str, dict[str, str]] = {}
    for case_id, spec in CASE_SPECS.items():
        record = case_records.get(case_id)
        require(record is not None, f"register missing {case_id}")
        require(record.get("run_id") == spec["run_id"], f"register run mismatch for {case_id}")
        require(str(spec["model"]).startswith(record["native_directory"] + "/"), f"register native directory mismatch for {case_id}")
        require(record.get("corner_demands_usable") is True, f"register rejects corner demands for {case_id}")
        native_dir = Path(record["native_directory"])
        response_name = Path(spec["response"]).name
        needed = {
            "report": spec["report"],
            "model": spec["model"],
            "response": spec["response"],
            "deck": native_dir / "model.inp",
            "native_data": native_dir / "model.dat",
            "execution": native_dir / "execution.json",
        }
        for rel in needed.values():
            rel_string = str(rel)
            expected = source_map.get(rel_string)
            actual = sha256(source_path(rel))
            require(expected == actual, f"register pin mismatch while freezing {rel_string}")
            files[rel_string] = actual
        cases[case_id] = {
            "run_id": spec["run_id"],
            "report_path": str(spec["report"]),
            "model_path": str(spec["model"]),
            "response_path": str(spec["response"]),
            "deck_path": str(needed["deck"]),
            "native_data_path": str(needed["native_data"]),
            "execution_path": str(needed["execution"]),
            "native_directory": str(native_dir),
            "response_filename": response_name,
            "register_status": record["status"],
        }
    pins = {
        "schema": "corner_timber_contact_pressure_screen_source_pins/v1",
        "register_path": str(REGISTER_REL),
        "register_sha256": files[str(REGISTER_REL)],
        "register_producer_path": str(REGISTER_PRODUCER_REL),
        "register_producer_sha256": files[str(REGISTER_PRODUCER_REL)],
        "files_sha256": dict(sorted(files.items())),
        "cases": cases,
        "note": "The three report, model, response, deck, native DAT and execution files must also match the selected register's source pins.",
    }
    PIN_PATH.write_text(json.dumps(pins, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"froze {len(files)} source files in {PIN_PATH.relative_to(ROOT)}")


def load_and_check_sources() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    pins = read_json(PIN_PATH)
    require(pins.get("schema") == "corner_timber_contact_pressure_screen_source_pins/v1", "unsupported source freeze schema")
    files: dict[str, str] = pins.get("files_sha256", {})
    for rel, expected in files.items():
        path = source_path(rel)
        require(path.is_file(), f"pinned source missing: {rel}")
        actual = sha256(path)
        require(actual == expected, f"source SHA mismatch: {rel} expected {expected}, got {actual}")

    register = read_json(source_path(REGISTER_REL))
    require(register.get("schema") == "current_six_case_corner_response_register/v1", "unexpected selected response register schema")
    require(register.get("candidate") == "compact-floor-flush-wood-joints-development", "selected register candidate mismatch")
    require(register.get("revision") == "led-clearance-2x6-runner-seated-blocks-v1", "selected register revision mismatch")
    require(register.get("case_count") == 6, "selected register no longer has six cases")
    require(register.get("source_pins_sha256", {}).get(str(REGISTER_PRODUCER_REL)) == pins["register_producer_sha256"], "register producer pin changed")
    case_records = {row["case_id"]: row for row in register.get("cases", [])}
    loaded: dict[str, dict[str, Any]] = {}

    for case_id, spec in CASE_SPECS.items():
        frozen = pins["cases"].get(case_id)
        record = case_records.get(case_id)
        require(frozen is not None and record is not None, f"register or freeze missing case {case_id}")
        require(record.get("run_id") == frozen["run_id"] == spec["run_id"], f"run identity changed for {case_id}")
        require(record.get("native_directory") == frozen["native_directory"], f"native directory changed for {case_id}")
        require(record.get("corner_demands_usable") is True, f"corner response no longer usable for {case_id}")
        require(record.get("conditional_physical_case_forces_usable") is True, f"conditional case force gate no longer passes for {case_id}")
        require(record.get("status") == frozen["register_status"], f"register case status changed for {case_id}")
        for key in ("report_path", "model_path", "response_path"):
            require(frozen[key] == str(spec[key.removesuffix("_path")]), f"frozen {key} does not match replay source for {case_id}")
        for key in ("report_path", "model_path", "response_path", "deck_path", "native_data_path", "execution_path"):
            rel = frozen[key]
            expected = files[rel]
            require(register.get("source_pins_sha256", {}).get(rel) == expected, f"selected register no longer authenticates {rel}")

        report = read_json(source_path(frozen["report_path"]))
        model = read_json(source_path(frozen["model_path"]))
        response = read_json(source_path(frozen["response_path"]))
        require(report.get("case_id") == case_id, f"report case id mismatch for {case_id}")
        require(response.get("case_id") == case_id, f"response case id mismatch for {case_id}")
        require(model.get("candidate") == register["candidate"], f"model candidate mismatch for {case_id}")
        require(model.get("geometry_revision_id") == register["revision"], f"model revision mismatch for {case_id}")
        require(len(report.get("increments", [])) == 7, f"report increment count mismatch for {case_id}")
        require(len(response.get("increments", [])) == 7, f"response increment count mismatch for {case_id}")
        require(record.get("increment_count") == 7, f"register increment count mismatch for {case_id}")
        require(response.get("source_input_model_json_sha256") == files[frozen["model_path"]], f"response model pin mismatch for {case_id}")
        require(response.get("native_data_sha256") == files[frozen["native_data_path"]], f"response native DAT pin mismatch for {case_id}")
        loaded[case_id] = {"spec": spec, "frozen": frozen, "register_record": record, "report": report, "model": model, "response": response}
    return pins, loaded


def cell_state(force_n: float, force_radius_n: float, q_mm: float, q_radius_mm: float, table_interval_n: list[float]) -> str:
    low, high = interval(force_n, force_radius_n)
    if low > 0.0:
        return "active_resolved"
    if high <= 0.0:
        return "open_resolved"
    if q_mm + q_radius_mm < 0.0 and table_interval_n == [0.0, 0.0]:
        return "open_resolved"
    return "ambiguous_at_rounded_contact_boundary"


def build_screen(pins: dict[str, Any], loaded: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cells_out: list[dict[str, Any]] = []
    pair_out: list[dict[str, Any]] = []
    state_counts = {"active_resolved": 0, "open_resolved": 0, "ambiguous_at_rounded_contact_boundary": 0}
    max_cell: dict[str, Any] | None = None

    for case_id in ("a12-rear", "a1-rear", "k12-rear"):
        case = loaded[case_id]
        report = case["report"]
        model = case["model"]
        response = case["response"]
        bindings = {row["name"]: row for row in model.get("unilateral_springa_bindings", [])}
        for index, (report_inc, response_inc) in enumerate(zip(report["increments"], response["increments"], strict=True)):
            require(close(report_inc["time"], response_inc["time"], atol=1e-10), f"time mismatch for {case_id} increment {index}")
            require(close(report_inc["load_factor"], response_inc["load_factor"], atol=1e-10), f"load factor mismatch for {case_id} increment {index}")
            require(response_inc.get("springa_law_checks_passed") is True, f"source SPRINGA audit does not pass for {case_id} increment {index}")
            response_springs = {row["source_row_id"]: row for row in response_inc["springa_components"]}
            physical = response_inc["physical_connection_forces"]
            report_cells = report_inc["member_contact_bearing"]["contact_cells"]
            report_pairs = report_inc["member_contact_bearing"]["pair_summaries"]

            for pair_id, member_a, member_b in TARGET_PAIRS:
                matched = [row for row in report_cells if {row["first"], row["second"]} == {member_a, member_b}]
                require(len(matched) == 4, f"{case_id} increment {index} {pair_id}: expected 4 contact cells, got {len(matched)}")
                matched.sort(key=lambda row: row["source_connection_name"])
                summary_matches = [row for row in report_pairs if {row["first"], row["second"]} == {member_a, member_b}]
                require(len(summary_matches) == 1, f"{case_id} increment {index} {pair_id}: report pair summary not unique")
                report_pair = summary_matches[0]
                require(report_pair.get("contact_cell_count") == 4, f"{case_id} increment {index} {pair_id}: report contact count changed")

                pair_area = 0.0
                pair_force_scalar = 0.0
                pair_force_scalar_radius = 0.0
                pair_force_a = [0.0, 0.0, 0.0]
                pair_force_b = [0.0, 0.0, 0.0]
                pair_force_radius = [0.0, 0.0, 0.0]
                pair_moment_a = [0.0, 0.0, 0.0]
                pair_moment_b = [0.0, 0.0, 0.0]
                pair_moment_radius = [0.0, 0.0, 0.0]
                pair_cell_pressures: list[float] = []
                pair_active = pair_open = pair_ambiguous = 0

                for report_cell in matched:
                    name = report_cell["source_connection_name"]
                    source_ids = report_cell["source_row_ids"]
                    require(len(source_ids) == 1, f"{case_id} {name}: expected one native SPRINGA row")
                    source_id = source_ids[0]
                    binding = bindings.get(name)
                    spring = response_springs.get(source_id)
                    end_forces = physical.get(name)
                    require(binding is not None and spring is not None and end_forces is not None, f"{case_id} {name}: missing model/SPRINGA/end-force source")
                    owner = binding["physical_owner"]
                    require(binding.get("source_row_id") == source_id, f"{case_id} {name}: source row id mismatch")
                    require({owner["first"], owner["second"]} == {member_a, member_b}, f"{case_id} {name}: model pair mismatch")
                    require({report_cell["first"], report_cell["second"]} == {owner["first"], owner["second"]}, f"{case_id} {name}: exported pair mismatch")

                    point = [float(x) for x in end_forces["point"]]
                    normal = [float(x) for x in owner["scalar_normal"]]
                    area = float(owner["source_area_mm2"])
                    first_force = [float(x) for x in end_forces["force_on_first_xyz_n"]]
                    second_force = [float(x) for x in end_forces["force_on_second_xyz_n"]]
                    force_radius = [float(x) for x in end_forces["force_rounding_radius_xyz_n"]]
                    q_force = float(spring["native_endpoint_internal_force_N"])
                    q_native_radius = float(spring["native_endpoint_internal_radius_N"])
                    q_projected = dot(first_force, normal)
                    q_projected_radius = sum(abs(normal[i]) * force_radius[i] for i in range(3))
                    q_radius = max(q_native_radius, q_projected_radius)
                    q_elongation = float(spring["q_from_qghost_mm"])
                    q_elongation_radius = float(spring["qghost_allowed_radius_mm"])
                    law_interval = [float(x) for x in spring["native_table_force_interval_N"]]
                    force_first_from_spring = [float(x) for x in spring["physical_force_on_first_body_xyz_n"]]

                    require(area > 0.0, f"{case_id} {name}: nonpositive contact area")
                    require(close(area, report_cell["contact"]["source_area_mm2"], atol=1e-8), f"{case_id} {name}: exported area mismatch")
                    require(close(area, end_forces["source_area_mm2"], atol=1e-8), f"{case_id} {name}: response area mismatch")
                    require(close(area, report_cell["contact"]["source_area_mm2"], atol=1e-8), f"{case_id} {name}: contact area mismatch")
                    require(point_distance(point, owner["point"]) <= 1e-8, f"{case_id} {name}: source point differs from model")
                    require(point_distance(point, report_cell["first_point_global_xyz_mm"]) <= 1e-8, f"{case_id} {name}: source point differs from report")
                    require(vector_close(normal, end_forces["scalar_normal"], atol=1e-12), f"{case_id} {name}: response normal differs from model")
                    require(vector_close(first_force, report_cell["force_on_first_xyz_n"], atol=1e-9), f"{case_id} {name}: report end force differs from authenticated response")
                    require(vector_close(first_force, force_first_from_spring, atol=1e-9), f"{case_id} {name}: SPRINGA end force differs from connection force")
                    require(vector_close(second_force, [-x for x in first_force], atol=1e-9), f"{case_id} {name}: end forces are not equal and opposite")
                    require(abs(q_projected - q_force) <= q_radius + q_projected_radius + 1e-9, f"{case_id} {name}: scalar SPRINGA force and projected end force do not overlap")
                    require(close(q_projected, report_cell["contact"]["normal_action_on_first_n"], atol=1e-8), f"{case_id} {name}: report normal force differs from response")
                    require(q_force >= 0.0, f"{case_id} {name}: compression-only SPRINGA force is negative")

                    q_interval = interval(q_force, q_radius)
                    q_elongation_interval = interval(q_elongation, q_elongation_radius)
                    state = cell_state(q_force, q_radius, q_elongation, q_elongation_radius, law_interval)
                    state_counts[state] += 1
                    pair_active += state == "active_resolved"
                    pair_open += state == "open_resolved"
                    pair_ambiguous += state == "ambiguous_at_rounded_contact_boundary"
                    pressure = q_force / area
                    pressure_interval = [q_interval[0] / area, q_interval[1] / area]
                    compression_pressure_interval = [max(0.0, q_interval[0]) / area, max(0.0, q_interval[1]) / area]
                    pair_cell_pressures.append(pressure)
                    pair_area += area
                    pair_force_scalar += q_force
                    pair_force_scalar_radius += q_radius

                    if owner["first"] == member_a:
                        force_a, force_b = first_force, second_force
                    else:
                        force_a, force_b = second_force, first_force
                    r_from_datum = [point[i] - DATUM_XYZ_MM[i] for i in range(3)]
                    moment_a_cell = cross(r_from_datum, force_a)
                    moment_b_cell = cross(r_from_datum, force_b)
                    mr = moment_radius(r_from_datum, force_radius)
                    pair_force_a = vadd(pair_force_a, force_a)
                    pair_force_b = vadd(pair_force_b, force_b)
                    pair_force_radius = vadd(pair_force_radius, force_radius)
                    pair_moment_a = vadd(pair_moment_a, moment_a_cell)
                    pair_moment_b = vadd(pair_moment_b, moment_b_cell)
                    pair_moment_radius = vadd(pair_moment_radius, mr)

                    cell = {
                        "case_id": case_id,
                        "increment_index_zero_based": index,
                        "time": float(report_inc["time"]),
                        "load_factor": float(report_inc["load_factor"]),
                        "pair_id": pair_id,
                        "member_a": member_a,
                        "member_b": member_b,
                        "source_connection_name": name,
                        "source_row_id": source_id,
                        "source_springa_element": int(spring["element"]),
                        "source_first_body": owner["first"],
                        "source_second_body": owner["second"],
                        "source_point_global_xyz_mm": point,
                        "source_scalar_normal_global_xyz": normal,
                        "source_contact_area_mm2": area,
                        "springa_law": binding["force_law"],
                        "springa_q_elongation_mm": q_elongation,
                        "springa_q_elongation_rounding_interval_mm": q_elongation_interval,
                        "native_springa_scalar_end_force_n": q_force,
                        "native_springa_scalar_end_force_rounding_interval_n": q_interval,
                        "native_springa_table_force_from_geometric_length_n": float(spring["native_table_force_N_from_actual_dd_minus_dd0"]),
                        "native_springa_table_force_interval_n": law_interval,
                        "native_end_force_on_source_first_xyz_n": first_force,
                        "native_end_force_on_source_second_xyz_n": second_force,
                        "native_end_force_rounding_radius_xyz_n": force_radius,
                        "normal_force_from_end_vector_n": q_projected,
                        "average_cell_pressure_mpa": pressure,
                        "average_cell_pressure_rounding_interval_mpa": pressure_interval,
                        "compression_only_average_pressure_interval_mpa": compression_pressure_interval,
                        "rounded_contact_state": state,
                        "source_corner_report_state": report_cell["contact"]["normal_state_from_force_interval"],
                    }
                    cells_out.append(cell)
                    if max_cell is None or pressure > max_cell["average_cell_pressure_mpa"]:
                        max_cell = {
                            "case_id": case_id,
                            "increment_index_zero_based": index,
                            "time": float(report_inc["time"]),
                            "load_factor": float(report_inc["load_factor"]),
                            "pair_id": pair_id,
                            "source_connection_name": name,
                            "source_row_id": source_id,
                            "native_springa_scalar_end_force_n": q_force,
                            "source_contact_area_mm2": area,
                            "average_cell_pressure_mpa": pressure,
                            "average_cell_pressure_rounding_interval_mpa": pressure_interval,
                        }

                require(close(pair_area, report_pair["modeled_area_mm2"], atol=1e-7), f"{case_id} increment {index} {pair_id}: pair area differs from source summary")
                require(close(pair_force_scalar, report_pair["summed_normal_action_on_first_n"], atol=1e-7), f"{case_id} increment {index} {pair_id}: summed SPRINGA force differs from source summary")
                require(close(pair_force_scalar / pair_area, report_pair["modeled_pair_average_pressure_mpa"], atol=1e-10), f"{case_id} increment {index} {pair_id}: pair average pressure differs from source summary")
                require(vector_close(pair_force_b, [-x for x in pair_force_a], atol=1e-8), f"{case_id} increment {index} {pair_id}: pair action-reaction resultant mismatch")
                require(vector_close(pair_moment_b, [-x for x in pair_moment_a], atol=1e-5), f"{case_id} increment {index} {pair_id}: pair action-reaction moment mismatch")

                pair_q_interval = interval(pair_force_scalar, pair_force_scalar_radius)
                pair_avg_pressure = pair_force_scalar / pair_area
                pair_pressure_interval = [pair_q_interval[0] / pair_area, pair_q_interval[1] / pair_area]
                pair_out.append({
                    "case_id": case_id,
                    "increment_index_zero_based": index,
                    "time": float(report_inc["time"]),
                    "load_factor": float(report_inc["load_factor"]),
                    "pair_id": pair_id,
                    "member_a": member_a,
                    "member_b": member_b,
                    "contact_cell_count": 4,
                    "source_contact_area_sum_mm2": pair_area,
                    "sum_native_springa_scalar_force_n": pair_force_scalar,
                    "sum_native_springa_scalar_force_rounding_interval_n": pair_q_interval,
                    "area_average_pressure_mpa": pair_avg_pressure,
                    "area_average_pressure_rounding_interval_mpa": pair_pressure_interval,
                    "maximum_cell_average_pressure_mpa": max(pair_cell_pressures),
                    "cell_state_counts": {"active_resolved": pair_active, "open_resolved": pair_open, "ambiguous_at_rounded_contact_boundary": pair_ambiguous},
                    "wrench_datum_global_xyz_mm": DATUM_XYZ_MM,
                    "wrench_on_member_a": {
                        "force_xyz_n": pair_force_a,
                        "force_rounding_radius_xyz_n": pair_force_radius,
                        "force_rounding_intervals_xyz_n": vector_intervals(pair_force_a, pair_force_radius),
                        "moment_xyz_nmm": pair_moment_a,
                        "moment_rounding_radius_xyz_nmm": pair_moment_radius,
                        "moment_rounding_intervals_xyz_nmm": vector_intervals(pair_moment_a, pair_moment_radius),
                    },
                    "wrench_on_member_b": {
                        "force_xyz_n": pair_force_b,
                        "force_rounding_radius_xyz_n": pair_force_radius,
                        "force_rounding_intervals_xyz_n": vector_intervals(pair_force_b, pair_force_radius),
                        "moment_xyz_nmm": pair_moment_b,
                        "moment_rounding_radius_xyz_nmm": pair_moment_radius,
                        "moment_rounding_intervals_xyz_nmm": vector_intervals(pair_moment_b, pair_moment_radius),
                    },
                    "source_report_pair_summary_matches": True,
                })

    require(len(cells_out) == 588, f"expected 588 cell states, got {len(cells_out)}")
    require(len(pair_out) == 147, f"expected 147 pair resultants, got {len(pair_out)}")
    return {
        "schema": "current_corner_timber_contact_pressure_screen/v1",
        "status": "SOURCE_BOUND_CONDITIONAL_NUMERICAL_DEMAND_ONLY",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": {
            "case_ids": ["a12-rear", "a1-rear", "k12-rear"],
            "target_pair_ids": [row[0] for row in TARGET_PAIRS],
            "recorded_increments_per_case": 7,
            "contact_cells_per_pair_per_increment": 4,
            "cell_state_count": len(cells_out),
            "pair_resultant_count": len(pair_out),
            "excluded": ["all other corner contacts", "panels", "general frame response", "native solver launches", "wood strength acceptance", "actual peak contact pressure", "physical candidate acceptance"],
        },
        "source_authentication": {
            "register_path": str(REGISTER_REL),
            "register_sha256": pins["register_sha256"],
            "register_producer_path": str(REGISTER_PRODUCER_REL),
            "register_producer_sha256": pins["register_producer_sha256"],
            "source_pins_path": str(PIN_PATH.relative_to(ROOT)),
            "source_pins_sha256": sha256(PIN_PATH),
            "files_sha256": pins["files_sha256"],
            "case_bindings": {case_id: loaded[case_id]["frozen"] for case_id in loaded},
            "native_solve_launched_by_this_packet": False,
        },
        "calculation": {
            "cell_average_pressure": "native SPRINGA scalar end-force magnitude divided by the source modeled contact-cell area; N/mm^2 = MPa",
            "pair_force": "sum of the four source native end-force vectors on each member side",
            "pair_moment": "sum((source point - declared global datum) cross native end-force vector) on each member side",
            "rounding_intervals": "Native RF token half-last-place vector radii and native SPRINGA scalar end-force radius are propagated through the stated sums; unilateral pressure lower bounds are clipped at zero in a separate field.",
            "contact_state": "Active when the rounded scalar-force interval is strictly positive; open when the compression-only force interval is nonpositive or the source q-elongation interval is strictly negative with a zero native table-force interval; otherwise ambiguous.",
            "datum_global_xyz_mm": DATUM_XYZ_MM,
        },
        "summary": {
            "cell_state_counts": state_counts,
            "maximum_cell_average_pressure": max_cell,
            "wood_strength_screen_performed": False,
            "candidate_block_bearing_strength": "not sourced; no block strength comparison is available",
            "actual_peak_pressure_or_strength_acceptance": False,
            "complete_joint_acceptance": False,
        },
        "cell_states": cells_out,
        "pair_resultants": pair_out,
        "limits": [
            "Pressures are modeled area averages for discrete compression-only SPRINGA cells; they are not a local pressure field, actual peak pressure, or wood stress distribution.",
            "Force and moment intervals cover native output rounding only. They do not cover uncertainty in material, geometry, contact support, model formulation, or actual construction.",
            "No candidate-block bearing strength is available, and this packet makes no resistance comparison or acceptance claim.",
            "The three case responses remain conditional numerical cases. This packet does not validate the floor, actual wood, contact faces, complete joints, or the candidate as a build or climbing system.",
        ],
    }


def write_screen(screen: dict[str, Any]) -> None:
    OUTPUT_PATH.write_text(json.dumps(screen, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze-sources", action="store_true", help="create the initial read-only source SHA freeze")
    group.add_argument("--write", action="store_true", help="write screen.json from frozen sources")
    group.add_argument("--verify", action="store_true", help="verify source SHAs and replay screen.json without writing")
    args = parser.parse_args()
    try:
        if args.freeze_sources:
            freeze_source_pins()
            return 0
        pins, loaded = load_and_check_sources()
        expected = build_screen(pins, loaded)
        expected_bytes = json.dumps(expected, indent=2, sort_keys=True) + "\n"
        if args.write:
            write_screen(expected)
            print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}: {len(expected['cell_states'])} cell states, {len(expected['pair_resultants'])} pair resultants")
            return 0
        existing = OUTPUT_PATH.read_text(encoding="utf-8")
        require(existing == expected_bytes, "screen.json differs from a fresh source-bound replay")
        print(f"PASS: {len(expected['cell_states'])} cell states; {len(expected['pair_resultants'])} pair resultants; states={expected['summary']['cell_state_counts']}")
        print("maximum cell-average pressure: " + json.dumps(expected["summary"]["maximum_cell_average_pressure"], sort_keys=True))
        return 0
    except (ScreenError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
