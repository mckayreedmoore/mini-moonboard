"""Authenticate the compact PB04 A12-forward first-case evidence package."""

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "fea/results/diagnostics/pb04-eight-station-a12-forward-v1"
SUMMARY = PACKAGE / "pb04-eight-station-diagnostic.json"
ATTEMPT_PATH = "attempts/a12-forward-01-all-unseeded"
ATTEMPT = PACKAGE / ATTEMPT_PATH
SOURCE_SNAPSHOTS = ATTEMPT / "source_snapshots"

CANDIDATE = "pb04-upper-edge-plus-outer-counterbores-v1"
INPUT_FINGERPRINT = "57f8d6901f663c725ced98ac392f8d42c272e6fb4472dc5811e8ae38eb3988cd"
SUMMARY_SHA256 = "6a6c6d26f5680028745130e1bfae819b251a06ffd556371b8d4cd9cedcf07486"
REPORT_SHA256 = "23ed26f229d18ca956696f433a40f8d66297a052d5d2b95b7150f2a4830bf1cd"
MODEL_SHA256 = "cffcf742a88b2e95490b7a367b595763e7281cf24b32950055f59588f2e86c42"
SCOPE_SHA256 = "30f8fb31e3353fc6dfc5d1aae7b0c8282f6f3c4914d7ab73fcbcdf347300c027"
FINAL_INPUT_SHA256 = "2acc8737a8a0a2d5d400d49cc7d29f896b72ea81b61fbebb11a7d31255a90f59"
FINAL_REPORT_SHA256 = "8cf3b4558440f73325b3f4554cb0bc480e1ab8cbaede22493a11e98ab7196c29"
CASE = "a12-forward"
HOLD = "A12"
FORCE_XYZ_N = [0.0, -300.0, -2224.11080763025]
FINAL_CYCLE = "cycle-08"
SOURCE_FILE_COUNT = 292
PRODUCER_FILE_COUNT = 205
SELECTED_ARTIFACTS = {
    "model.pkl": MODEL_SHA256,
    "diagnostic-scope.json": SCOPE_SHA256,
    f"{FINAL_CYCLE}/input.json": FINAL_INPUT_SHA256,
    f"{FINAL_CYCLE}/report.json": FINAL_REPORT_SHA256,
}
RELEASE_FIELDS = (
    "qualified_for_design",
    "acceptance",
    "drilling_released",
    "fabrication_released",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _false_flags(record: dict, fields: tuple[str, ...]) -> bool:
    return all(record.get(field) is False for field in fields)


def _validate_summary(summary: dict) -> dict:
    accepted = summary.get("accepted_cases", {}).get(CASE, {})
    attempts = summary.get("attempts", [])
    inventory = summary.get("topology_inventory", {})
    if (
        summary.get("schema") != "simple_pb04_eight_station_diagnostic_run/v1"
        or summary.get("candidate") != CANDIDATE
        or summary.get("deterministic_input_fingerprint") != INPUT_FINGERPRINT
        or summary.get("case_order", [None])[0] != CASE
        or summary.get("loads", {}).get(CASE)
        != {"hold": HOLD, "horizontal_force_xy_n": FORCE_XYZ_N[:2]}
        or summary.get("accepted_case_count") != 1
        or set(summary.get("accepted_cases", {})) != {CASE}
        or accepted.get("path") != ATTEMPT_PATH
        or accepted.get("attempt") != "01-all-unseeded"
        or accepted.get("contact_update_strategy") != "all"
        or accepted.get("search_seed_case") is not None
        or accepted.get("numerically_accepted") is not True
        or accepted.get("forces_reported_only_in_authenticated_case_report") is not True
        or accepted.get("report_sha256") != REPORT_SHA256
        or len(attempts) != 1
        or attempts[0].get("case") != CASE
        or attempts[0].get("native_report_sha256") != REPORT_SHA256
        or attempts[0].get("contact_active_set_converged") is not True
        or attempts[0].get("numerically_accepted") is not True
        or attempts[0].get("forces_in_suite_summary") is not False
        or inventory.get("pb04_tension_only_bolt_count") != 32
        or len(inventory.get("pb04_bolt_names", [])) != 32
        or inventory.get("pb02_tension_only_bolt_count") != 10
        or len(inventory.get("tension_only_bolt_names", [])) != 42
        or inventory.get("pb04_contact_cell_count") != 64
        or len(inventory.get("pb04_contact_names", [])) != 64
        or inventory.get("block_member_count") != 8
        or len(inventory.get("block_member_names", [])) != 8
        or inventory.get("fixed_panel_kicker_axis_count") != 66
        or summary.get("developmental_only") is not True
        or summary.get("rejected_attempt_forces_included") is not False
        or not _false_flags(summary, RELEASE_FIELDS)
    ):
        raise ValueError("first-case summary identity changed")
    return inventory


def _validate_report(report: dict, inventory: dict) -> None:
    scope = report.get("diagnostic_scope", {})
    cycles = report.get("contact_cycles", [])
    audits = (
        "contact_active_set_converged",
        "axial_tension_active_set_converged",
        "axial_tension_assumption_passed",
        "closed_bearing_assumption_passed",
        "global_equilibrium_passed",
        "member_equilibrium_passed",
        "mpc_check_passed",
        "numerically_accepted",
    )
    if (
        report.get("candidate") != CANDIDATE
        or report.get("pb04_diagnostic_identity") != INPUT_FINGERPRINT
        or report.get("pb04_model_identity") != MODEL_SHA256
        or report.get("artifact_sha256", {}).get("model.pkl") != MODEL_SHA256
        or report.get("parameters", {}).get("hold") != HOLD
        or report.get("parameters", {}).get("force_xyz_n") != FORCE_XYZ_N
        or scope.get("case") != CASE
        or scope.get("candidate") != CANDIDATE
        or scope.get("deterministic_input_fingerprint") != INPUT_FINGERPRINT
        or scope.get("contact_update_strategy") != "all"
        or scope.get("search_seed_case") is not None
        or scope.get("developmental_only") is not True
        or any(report.get(field) is not True for field in audits)
        or len(report.get("angle_stations", [])) != 14
        or report.get("axial_tension_names") != inventory["tension_only_bolt_names"]
        or len(report.get("axial_tension", [])) != 42
        or [row.get("directory") for row in cycles]
        != [f"cycle-{index:02d}" for index in range(9)]
        or any(
            row.get("contact_passed") is True
            and row.get("axial_tension_passed") is True
            for row in cycles[:-1]
        )
        or cycles[-1].get("contact_passed") is not True
        or cycles[-1].get("axial_tension_passed") is not True
        or not _false_flags(report, RELEASE_FIELDS)
        or not _false_flags(scope, RELEASE_FIELDS)
    ):
        raise ValueError("accepted first-case report identity changed")

    if not set(inventory["pb04_contact_names"]) <= {
        row.get("name") for row in report.get("bearings", [])
    }:
        raise ValueError("PB04 contact inventory is incomplete")
    if not set(inventory["block_member_names"]) <= set(
        report.get("member_section_demands", {})
    ):
        raise ValueError("PB04 block inventory is incomplete")
    physical = report.get("physical_connection_forces", {})
    if not set(inventory.get("required_physical_names", [])) <= set(physical):
        raise ValueError("physical-force inventory is incomplete")
    for record in physical.values():
        force = record.get("force_on_first_xyz_n")
        if (
            not isinstance(force, list)
            or len(force) != 3
            or any(
                not isinstance(value, (int, float)) or not math.isfinite(value)
                for value in force
            )
        ):
            raise ValueError("physical-force inventory contains an invalid record")


def _authenticate_artifacts(report: dict) -> None:
    manifest = report.get("artifact_sha256", {})
    for relative, expected in SELECTED_ARTIFACTS.items():
        if (
            manifest.get(relative) != expected
            or _sha256(ATTEMPT / relative) != expected
        ):
            raise ValueError(f"retained artifact changed: {relative}")
    scope = _load(ATTEMPT / "diagnostic-scope.json")
    final_input = _load(ATTEMPT / FINAL_CYCLE / "input.json")
    final_report = _load(ATTEMPT / FINAL_CYCLE / "report.json")
    if scope != report.get("diagnostic_scope"):
        raise ValueError("retained diagnostic scope differs from accepted report")
    if (
        final_input.get("candidate") != CANDIDATE
        or final_input.get("hold") != HOLD
        or final_input.get("force_xyz_n") != FORCE_XYZ_N
        or not _false_flags(
            final_input, RELEASE_FIELDS + ("actual_joint_demands_qualified",)
        )
        or final_report.get("qualified_for_design") is not False
        or final_report.get("actual_joint_demands_qualified") is not False
    ):
        raise ValueError("retained final-cycle identity changed")
    for field in (
        "physical_connection_forces",
        "member_section_demands",
        "bearings",
        "axial_tension",
        "global_equilibrium_passed",
        "member_equilibrium_passed",
        "mpc_check_passed",
    ):
        if final_report.get(field) != report.get(field):
            raise ValueError(
                f"final-cycle report differs from accepted report: {field}"
            )


def _authenticate_sources(summary: dict, report: dict) -> dict:
    expected = report.get("source_sha256")
    producer = summary.get("producer_source_sha256")
    actual = {
        path.relative_to(SOURCE_SNAPSHOTS).as_posix(): _sha256(path)
        for path in SOURCE_SNAPSHOTS.rglob("*")
        if path.is_file()
    }
    if (
        not isinstance(expected, dict)
        or len(expected) != SOURCE_FILE_COUNT
        or actual != expected
        or not isinstance(producer, dict)
        or len(producer) != PRODUCER_FILE_COUNT
        or any(expected.get(name) != digest for name, digest in producer.items())
    ):
        raise ValueError("source snapshot closure changed")
    return {
        "path": f"{ATTEMPT_PATH}/source_snapshots",
        "file_count": len(actual),
        "producer_file_count": len(producer),
        "all_snapshot_hashes_match": True,
        "summary_producer_map_is_authenticated_subset": True,
    }


def _authenticate_package_inventory(report: dict) -> None:
    expected = {
        SUMMARY.relative_to(PACKAGE).as_posix(),
        (ATTEMPT / "report.json").relative_to(PACKAGE).as_posix(),
    }
    expected.update(
        (ATTEMPT / name).relative_to(PACKAGE).as_posix() for name in SELECTED_ARTIFACTS
    )
    expected.update(
        (SOURCE_SNAPSHOTS / name).relative_to(PACKAGE).as_posix()
        for name in report["source_sha256"]
    )
    actual = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        raise ValueError("compact package contains missing or extra files")


def screen() -> dict:
    """Fail closed unless the retained first case is complete and authenticated."""
    if _sha256(SUMMARY) != SUMMARY_SHA256:
        raise ValueError("first-case summary hash changed")
    summary = _load(SUMMARY)
    inventory = _validate_summary(summary)
    if _sha256(ATTEMPT / "report.json") != REPORT_SHA256:
        raise ValueError("accepted report hash changed")
    report = _load(ATTEMPT / "report.json")
    _validate_report(report, inventory)
    _authenticate_artifacts(report)
    sources = _authenticate_sources(summary, report)
    _authenticate_package_inventory(report)
    return {
        "schema": "simple_pb04_first_case_evidence/v1",
        "candidate": CANDIDATE,
        "case": CASE,
        "deterministic_input_fingerprint": INPUT_FINGERPRINT,
        "summary_sha256": SUMMARY_SHA256,
        "report_sha256": REPORT_SHA256,
        "model_sha256": MODEL_SHA256,
        "final_cycle": FINAL_CYCLE,
        "cycle_count": 9,
        "pb04_bolt_count": 32,
        "pb04_contact_cell_count": 64,
        "pb04_block_count": 8,
        "source_snapshot_authentication": sources,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    encoded = json.dumps(screen(), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
