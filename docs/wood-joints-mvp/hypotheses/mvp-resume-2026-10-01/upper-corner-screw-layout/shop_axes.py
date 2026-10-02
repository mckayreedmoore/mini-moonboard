#!/usr/bin/env python3
"""Export and reconcile the authorized 66-axis shop overlay."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").exists()
)
HERE = Path(__file__).resolve().parent
RAW = HERE / "rawlocal/shop-axes"
INPUTS = HERE / "operators-attempt02/model-inputs.json"
MODEL = HERE / "operators-attempt02/model.json"
SETUP = HERE / "rawlocal/attempt01/setup.json"
RESULT = HERE / "rawlocal/attempt01/result.json"
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
PINS = {
    "operator_model_inputs": (INPUTS, "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc"),
    "operator_model": (MODEL, "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626"),
    "geometry_setup": (SETUP, "00cfa71d30a1d8d789df7c4a40770f9ec46e3e56c0ee9d23018d62e6c11583bc"),
    "geometry_result": (RESULT, "81b75c3fe8dced195d36d3a2a3f1ca69b1e796b89e048870a16e3864bb5a06d9"),
    "base_model_inputs": (BASE, "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9"),
}
RECEIVERS = {
    "round_panel_upper_left_rim_4": ("base_side_left", "base_side_left"),
    "round_panel_upper_right_rim_4": ("base_side_right", "base_side_right"),
    "round_panel_upper_left_center_4": ("base_principal_center_left", "base_rail_top"),
    "round_panel_upper_right_center_4": ("base_principal_center_right", "base_rail_top"),
}
FIELDS = [
    "axis_id", "location_status", "panel_member", "receiver_member",
    "front_datum_x_global_mm", "front_datum_y_global_mm", "front_datum_z_global_mm",
    "direction_x_global", "direction_y_global", "direction_z_global", "authorized_move_T_mm",
]
MOVE_MM = 65.95
TOL = 1e-7


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def vec(value: list, label: str) -> tuple[float, float, float]:
    result = tuple(float(item) for item in value)
    if len(result) != 3 or not all(math.isfinite(item) for item in result):
        raise ValueError(f"{label} must be a finite 3-vector")
    return result


def same(actual: tuple[float, ...], expected: tuple[float, ...], label: str, tol: float = TOL) -> None:
    if any(abs(a - b) > tol for a, b in zip(actual, expected, strict=True)):
        raise ValueError(f"{label} differs: {actual} != {expected}")


def fmt(value: float) -> str:
    return repr(value)


def export(output: Path) -> tuple[Path, Path, dict]:
    for name, (path, expected) in PINS.items():
        if sha(path) != expected:
            raise ValueError(f"{name} SHA-256 changed")

    inputs, model, setup, result, base = map(read_json, (INPUTS, MODEL, SETUP, RESULT, BASE))
    if inputs["candidate"] != model["candidate"] or inputs["revision_id"] != model["source_revision"]:
        raise ValueError("operator inputs and mechanics model identity differ")
    base_hash = PINS["base_model_inputs"][1]
    if inputs["derived_from_model_inputs_sha256"] != base_hash or setup["model_inputs_sha256"] != base_hash:
        raise ValueError("operator geometry does not bind the pinned base inputs")
    if base["candidate"] != inputs["candidate"]:
        raise ValueError("base and operator candidates differ")
    if result["setup_sha256"] != PINS["geometry_setup"][1]:
        raise ValueError("geometry result does not bind pinned setup")
    if result["geometry_rebuilt"] is not False or result["source_unchanged_after_run"] is not True:
        raise ValueError("geometry receipt does not describe unchanged saved solids")

    geometry_pins = result["source_sha256"]
    if len(geometry_pins) != 172:
        raise ValueError(f"expected 172 geometry source pins, found {len(geometry_pins)}")
    for relative, expected in geometry_pins.items():
        path = ROOT / relative
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f"geometry source pin changed or missing: {relative}")

    baseline = {row["axis_id"]: row for row in setup["all_66_panel_screw_axes_before"]}
    source = {
        row["axis_id"]: row for row in inputs["connections"] if row.get("kind") == "panel_screw"
    }
    moved_ids = set(RECEIVERS)
    if len(source) != 66 or len(baseline) != 66 or source.keys() != baseline.keys():
        raise ValueError("frozen and geometry axis schedules must contain same 66 IDs")
    if set(setup["changed_axis_ids"]) != moved_ids or len(inputs["owner_authorized_upper_screw_movements"]) != 4:
        raise ValueError("source does not bind exactly four authorized axes")

    basis = vec(setup["move_basis_T_xyz"], "T basis")
    if abs(math.sqrt(sum(component * component for component in basis)) - 1) > 1e-12:
        raise ValueError("T basis is not a unit vector")
    if abs(float(setup["move_mm"]) - MOVE_MM) > TOL:
        raise ValueError("saved movement magnitude differs from 65.95 mm")
    moves = {row["axis_id"]: row for row in setup["before_after"]}
    authorized = {row["axis_id"]: row for row in inputs["owner_authorized_upper_screw_movements"]}
    if moves.keys() != moved_ids or authorized.keys() != moved_ids:
        raise ValueError("saved before/after or owner authorization axis set differs")
    geometry_checks = {(row["axis_id"], row["scenario"]): row for row in result["checks"]}
    expected_checks = {(axis_id, scenario) for axis_id in moved_ids for scenario in ("before", "after")}
    if geometry_checks.keys() != expected_checks:
        raise ValueError("saved geometry result must cover all four moves before and after")

    rows = []
    for axis_id, row in sorted(source.items()):
        record = row["source_record"]
        origin = vec(row["source_point_xyz_mm"], f"{axis_id} datum")
        direction = vec(row["axis_xyz"], f"{axis_id} direction")
        panel, receiver = record["panel_member"], record["receiver_member"]
        same(vec(record["origin_global_xyz_mm"], axis_id), origin, f"{axis_id} record datum")
        same(vec(record["axis_global_xyz"], axis_id), direction, f"{axis_id} record direction", 1e-12)
        if set(row["receiver_member_ids"]) != {panel, receiver}:
            raise ValueError(f"{axis_id} receiver IDs differ from row")
        if not record["purchased_policy"].startswith("Hillman 42605;"):
            raise ValueError(f"{axis_id} screw policy changed")
        if float(record["purchased_nominal_length_mm"]) != 63.5:
            raise ValueError(f"{axis_id} nominal screw length changed")

        old = baseline[axis_id]
        old_origin = vec(old["origin_xyz_mm"], f"{axis_id} baseline datum")
        same(direction, vec(old["axis_direction_xyz"], axis_id), f"{axis_id} direction", 1e-12)
        if old["panel_member"] != panel:
            raise ValueError(f"{axis_id} panel changed")
        if axis_id not in moved_ids:
            same(origin, old_origin, f"{axis_id} unchanged datum")
            if receiver != old["receiver_member"]:
                raise ValueError(f"{axis_id} unchanged receiver changed")
            status, move_t = "unchanged", 0.0
        else:
            old_receiver, new_receiver = RECEIVERS[axis_id]
            change, owner = moves[axis_id], authorized[axis_id]
            same(vec(change["before"]["axis_origin_xyz_mm"], axis_id), old_origin, f"{axis_id} geometry baseline")
            same(vec(change["after"]["axis_origin_xyz_mm"], axis_id), origin, f"{axis_id} geometry datum")
            same(vec(owner["after"]["origin_global_xyz_mm"], axis_id), origin, f"{axis_id} owner datum")
            if old["receiver_member"] != old_receiver or change["after"]["receiver_member"] != new_receiver:
                raise ValueError(f"{axis_id} receiver transition differs")
            if owner["before"]["receiver_member"] != old_receiver or owner["after"]["receiver_member"] != new_receiver or receiver != new_receiver:
                raise ValueError(f"{axis_id} owner receiver transition differs")
            delta = tuple(origin[i] - old_origin[i] for i in range(3))
            same(delta, tuple(MOVE_MM * item for item in basis), f"{axis_id} T translation")
            owner_move = owner["after"]["owner_moved_axis_record"]
            if owner_move["date"] != "2026-10-02":
                raise ValueError(f"{axis_id} owner authorization date differs")
            same(vec(owner_move["translation_xyz_mm"], axis_id), delta, f"{axis_id} authorized move record")
            same(vec(owner_move["previous_origin_xyz_mm"], axis_id), old_origin, f"{axis_id} authorized prior datum")
            if owner_move["previous_receiver_member"] != old_receiver:
                raise ValueError(f"{axis_id} authorized prior receiver differs")
            move_t = sum(delta[i] * basis[i] for i in range(3))
            if abs(move_t - MOVE_MM) > TOL or record["current_location_status"] != "owner_authorized_upper_corner_row_move":
                raise ValueError(f"{axis_id} movement/status differs")
            move_t = MOVE_MM
            for scenario, expected_receiver in (("before", old_receiver), ("after", new_receiver)):
                check = geometry_checks[(axis_id, scenario)]
                if check["receiver_member"] != expected_receiver or check["screw_bolt_axis_conflicts"]:
                    raise ValueError(f"{axis_id} {scenario} saved geometry check differs")
            status = "owner_authorized_move"

        rows.append({
            "axis_id": axis_id, "location_status": status, "panel_member": panel,
            "receiver_member": receiver, "origin": origin, "direction": direction,
            "authorized_move_T_mm": move_t,
        })

    if sum(row["location_status"] == "unchanged" for row in rows) != 62:
        raise ValueError("expected exactly 62 unchanged axes")

    output.mkdir(parents=True, exist_ok=True)
    csv_path, receipt_path = output / "axes.csv", output / "receipt.json"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "axis_id": row["axis_id"], "location_status": row["location_status"],
                "panel_member": row["panel_member"], "receiver_member": row["receiver_member"],
                **dict(zip(FIELDS[4:7], map(fmt, row["origin"]), strict=True)),
                **dict(zip(FIELDS[7:10], map(fmt, row["direction"]), strict=True)),
                "authorized_move_T_mm": fmt(row["authorized_move_T_mm"]),
            })

    with csv_path.open(encoding="utf-8", newline="") as stream:
        exported = list(csv.DictReader(stream))
    if len(exported) != 66 or len({row["axis_id"] for row in exported}) != 66:
        raise ValueError("CSV round-trip failed 66 unique-axis check")
    for actual, expected in zip(exported, rows, strict=True):
        if actual["panel_member"] != expected["panel_member"] or actual["receiver_member"] != expected["receiver_member"]:
            raise ValueError(f"CSV receiver/panel mismatch: {actual['axis_id']}")
        same(tuple(float(actual[key]) for key in FIELDS[4:7]), expected["origin"], f"CSV datum {actual['axis_id']}")
        same(tuple(float(actual[key]) for key in FIELDS[7:10]), expected["direction"], f"CSV direction {actual['axis_id']}", 1e-12)

    pin_map = json.dumps(geometry_pins, sort_keys=True, separators=(",", ":")).encode()
    receipt = {
        "schema": "upper_corner_shop_axes_receipt/v1",
        "source_sha256": {name: expected for name, (_, expected) in PINS.items()},
        "geometry_source_pin_count": len(geometry_pins),
        "geometry_source_pin_map_sha256": hashlib.sha256(pin_map).hexdigest(),
        "producer_sha256": sha(Path(__file__).resolve()),
        "csv": {"path": csv_path.name, "sha256": sha(csv_path), "rows": len(rows), "columns": FIELDS},
        "reconciliation": {
            "unchanged": 62, "owner_authorized_moved": 4, "move_T_mm": MOVE_MM,
            "move_basis_T_xyz": list(basis),
            "moved_axis_ids": sorted(moved_ids),
            "receiver_changes": {key: {"before": a, "after": b} for key, (a, b) in RECEIVERS.items()},
        },
        "checks": {"all_172_geometry_source_pins_match": True, "csv_round_trip_passed": True,
                   "source_step_or_authority_modified": False, "physical_cut_or_guide_adoption_claimed": False},
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return csv_path, receipt_path, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=RAW)
    csv_path, receipt_path, receipt = export(parser.parse_args().output_dir)
    print(f"CSV {csv_path} sha256={receipt['csv']['sha256']}")
    print(f"Receipt {receipt_path} sha256={sha(receipt_path)}")
    print("66 axes: 62 unchanged, 4 moved")


if __name__ == "__main__":
    main()
