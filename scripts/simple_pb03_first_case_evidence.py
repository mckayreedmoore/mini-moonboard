"""Authenticate the compact PB03 A12-forward first-case evidence package."""

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "fea/results/diagnostics/pb03-eight-station-a12-forward-v1"
SUMMARY = PACKAGE / "pb03-eight-station-diagnostic.json"
ATTEMPT = PACKAGE / "attempts/a12-forward-01-all-unseeded"
SOURCE_SNAPSHOTS = ATTEMPT / "source_snapshots"

CANDIDATE = "pb03-lower-service-plus-upper-and-bottom-outer-v1"
INPUT_FINGERPRINT = "cfcea003c0f83dbd6e2ee7d7a3ce20b2662806076ccfce5d930509f40e8e1e84"
SUMMARY_SHA256 = "ffa4c7fdc846780216cfe99088f8366bdfa6fe1e3130df128ce5f7c8dd8d4d3d"
REPORT_SHA256 = "a2f203541c52cff205e432d4043c722c0b1df4cfc3b850c2fae4dbae9688c93e"
MODEL_SHA256 = "9fb69a3450202b78f210b7a01867f093008ea8e86db8e3729c133bbc6903e6a4"
SCOPE_SHA256 = "45a86565b49260589c588a0b7003b57bf386b6b47fbae49c41a4cc731752fb14"
FINAL_INPUT_SHA256 = "8488c61e9f2a3f5e1d437e602d6bc6c46195730a5109952e3da25315aa5c0ef5"
FINAL_REPORT_SHA256 = "1645b182696bdd1ce82198d3f67411ac2dcfe3ac039f30eaab70eec643a49e1f"
ATTEMPT_PATH = "attempts/a12-forward-01-all-unseeded"
CASE = "a12-forward"
HOLD = "A12"
FORCE_XYZ_N = [0.0, -300.0, -2224.11080763025]
FINAL_CYCLE = "cycle-08"
SOURCE_FILE_COUNT = 287
SELECTED_ARTIFACTS = {
    "model.pkl": MODEL_SHA256,
    "diagnostic-scope.json": SCOPE_SHA256,
    f"{FINAL_CYCLE}/input.json": FINAL_INPUT_SHA256,
    f"{FINAL_CYCLE}/report.json": FINAL_REPORT_SHA256,
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _python_cache(path: Path) -> bool:
    return path.suffix == ".pyc" and "__pycache__" in path.parts


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _false_release_flags(record: dict, fields: tuple[str, ...]) -> bool:
    return all(record.get(field) is False for field in fields)


def _validate_summary(summary: dict) -> dict:
    expected_load = {"hold": HOLD, "horizontal_force_xy_n": FORCE_XYZ_N[:2]}
    accepted = summary.get("accepted_cases", {}).get(CASE, {})
    attempts = summary.get("attempts", [])
    inventory = summary.get("topology_inventory", {})
    if (
        summary.get("schema") != "simple_pb03_eight_station_diagnostic_run/v1"
        or summary.get("candidate") != CANDIDATE
        or summary.get("deterministic_input_fingerprint") != INPUT_FINGERPRINT
        or summary.get("case_order", [None])[0] != CASE
        or summary.get("loads", {}).get(CASE) != expected_load
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
        or inventory.get("pb03_tension_only_bolt_count") != 32
        or inventory.get("pb02_tension_only_bolt_count") != 10
        or len(inventory.get("tension_only_bolt_names", [])) != 42
        or inventory.get("pb03_contact_cell_count") != 64
        or len(inventory.get("pb03_contact_names", [])) != 64
        or inventory.get("block_member_count") != 8
        or len(inventory.get("block_member_names", [])) != 8
        or summary.get("developmental_only") is not True
        or summary.get("rejected_attempt_forces_included") is not False
        or not _false_release_flags(
            summary,
            (
                "qualified_for_design",
                "acceptance",
                "drilling_released",
                "fabrication_released",
            ),
        )
    ):
        raise ValueError("first-case summary identity changed")
    return inventory


def _validate_report(report: dict, inventory: dict) -> None:
    scope = report.get("diagnostic_scope", {})
    cycles = report.get("contact_cycles", [])
    required_audits = (
        "contact_active_set_converged",
        "axial_tension_active_set_converged",
        "axial_tension_assumption_passed",
        "closed_bearing_assumption_passed",
        "global_equilibrium_passed",
        "member_equilibrium_passed",
        "mpc_check_passed",
        "numerically_accepted",
    )
    expected_cycles = [f"cycle-{index:02d}" for index in range(9)]
    if (
        report.get("candidate") != CANDIDATE
        or report.get("pb03_diagnostic_identity") != INPUT_FINGERPRINT
        or report.get("parameters", {}).get("hold") != HOLD
        or report.get("parameters", {}).get("force_xyz_n") != FORCE_XYZ_N
        or scope.get("case") != CASE
        or scope.get("candidate") != CANDIDATE
        or scope.get("deterministic_input_fingerprint") != INPUT_FINGERPRINT
        or scope.get("contact_update_strategy") != "all"
        or scope.get("search_seed_case") is not None
        or any(report.get(field) is not True for field in required_audits)
        or len(report.get("angle_stations", [])) != 14
        or report.get("axial_tension_names") != inventory["tension_only_bolt_names"]
        or len(report.get("axial_tension", [])) != 42
        or [row.get("directory") for row in cycles] != expected_cycles
        or any(
            row.get("contact_passed") is True
            and row.get("axial_tension_passed") is True
            for row in cycles[:-1]
        )
        or cycles[-1].get("contact_passed") is not True
        or cycles[-1].get("axial_tension_passed") is not True
        or report.get("pb03_model_identity") != MODEL_SHA256
        or report.get("artifact_sha256", {}).get("model.pkl") != MODEL_SHA256
        or not _false_release_flags(
            report,
            (
                "qualified_for_design",
                "acceptance",
                "drilling_released",
                "fabrication_released",
            ),
        )
        or scope.get("developmental_only") is not True
        or not _false_release_flags(
            scope,
            (
                "qualified_for_design",
                "acceptance",
                "drilling_released",
                "fabrication_released",
            ),
        )
    ):
        raise ValueError("accepted first-case report identity changed")

    pb03_contacts = set(inventory["pb03_contact_names"])
    bearing_names = {row.get("name") for row in report.get("bearings", [])}
    block_names = set(inventory["block_member_names"])
    if not pb03_contacts <= bearing_names:
        raise ValueError("PB03 contact inventory is incomplete")
    if not block_names <= set(report.get("member_section_demands", {})):
        raise ValueError("PB03 block inventory is incomplete")

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


def _authenticate_artifacts(report: dict) -> tuple[dict, dict, dict]:
    manifest = report.get("artifact_sha256", {})
    for relative, expected in SELECTED_ARTIFACTS.items():
        path = ATTEMPT / relative
        if manifest.get(relative) != expected or _sha256(path) != expected:
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
        or not _false_release_flags(
            final_input,
            (
                "qualified_for_design",
                "acceptance",
                "drilling_released",
                "fabrication_released",
                "actual_joint_demands_qualified",
            ),
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
    return scope, final_input, final_report


def _authenticate_sources(summary: dict, report: dict) -> dict:
    expected = report.get("source_sha256")
    actual = {
        path.relative_to(SOURCE_SNAPSHOTS).as_posix(): _sha256(path)
        for path in SOURCE_SNAPSHOTS.rglob("*")
        if path.is_file() and not _python_cache(path)
    }
    producer = summary.get("producer_source_sha256")
    if (
        not isinstance(expected, dict)
        or len(expected) != SOURCE_FILE_COUNT
        or not isinstance(producer, dict)
        or any(expected.get(name) != digest for name, digest in producer.items())
    ):
        raise ValueError("source snapshot closure changed")
    if actual != expected:
        missing = sorted(expected.keys() - actual.keys())
        extra = sorted(actual.keys() - expected.keys())
        altered = sorted(
            name
            for name in expected.keys() & actual.keys()
            if expected[name] != actual[name]
        )
        raise ValueError(
            "source snapshot closure changed: "
            f"missing={missing}, extra={extra}, hash_mismatches={altered}"
        )
    return {
        "path": f"{ATTEMPT_PATH}/source_snapshots",
        "file_count": len(actual),
        "all_snapshot_hashes_match": True,
        "summary_producer_map_is_authenticated_subset": True,
    }


def _authenticate_package_inventory(report: dict) -> None:
    expected = {
        SUMMARY.relative_to(PACKAGE).as_posix(),
        (ATTEMPT / "report.json").relative_to(PACKAGE).as_posix(),
    }
    expected.update(
        (ATTEMPT / relative).relative_to(PACKAGE).as_posix()
        for relative in SELECTED_ARTIFACTS
    )
    expected.update(
        (SOURCE_SNAPSHOTS / relative).relative_to(PACKAGE).as_posix()
        for relative in report["source_sha256"]
    )
    actual = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file()
        and not (path.is_relative_to(SOURCE_SNAPSHOTS) and _python_cache(path))
    }
    if actual != expected:
        raise ValueError("compact package contains missing or extra files")


def screen() -> dict:
    """Fail closed unless the retained first case is complete and authenticated."""
    if _sha256(SUMMARY) != SUMMARY_SHA256:
        raise ValueError("first-case summary hash changed")
    summary = _load(SUMMARY)
    inventory = _validate_summary(summary)

    report_path = ATTEMPT / "report.json"
    if _sha256(report_path) != REPORT_SHA256:
        raise ValueError("accepted report hash changed")
    report = _load(report_path)
    _validate_report(report, inventory)
    _authenticate_artifacts(report)
    sources = _authenticate_sources(summary, report)
    _authenticate_package_inventory(report)
    return {
        "schema": "simple_pb03_first_case_evidence/v1",
        "candidate": CANDIDATE,
        "case": CASE,
        "deterministic_input_fingerprint": INPUT_FINGERPRINT,
        "summary_sha256": SUMMARY_SHA256,
        "report_sha256": REPORT_SHA256,
        "model_sha256": MODEL_SHA256,
        "final_cycle": FINAL_CYCLE,
        "cycle_count": 9,
        "tension_only_bolt_count": 42,
        "pb03_contact_cell_count": 64,
        "pb03_block_count": 8,
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
    result = screen()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
