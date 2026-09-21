"""Authenticate the compact PB05 A12-forward developmental evidence package."""

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "fea/results/diagnostics/pb05-eight-station-a12-forward-v1"
SUMMARY = PACKAGE / "pb05-eight-station-diagnostic.json"
ATTEMPT_PATH = "attempts/a12-forward-01-all-unseeded"
ATTEMPT = PACKAGE / ATTEMPT_PATH
SNAPSHOTS = ATTEMPT / "source_snapshots"

CASE = "a12-forward"
CANDIDATE = "pb05-six-narrow-no-pocket-outer-v1"
FINGERPRINT = "9fc6d74b949ec9f82e933182263c8e219cb09b82a5a885b625f4c32e1ae145e3"
SOURCE_FINGERPRINT = "74ec72045345fe59ef1a225e85fcc1f608ccd36e6bfa15d8375b576cb5b943f2"
FORCE_XYZ_N = [0.0, -300.0, -2224.11080763025]
FINAL_CYCLE = "cycle-08"
SUMMARY_SHA256 = "c1302f6911754903459ac93d4652ec24723ed2ea38bd6bd70f77d09d5ad8823e"
REPORT_SHA256 = "6b58b7df844b2071f0cfc04e501a2d761c51e0ce12064b9cb6292100eec2cdee"
ARTIFACTS = {
    "model.pkl": "11f2416d242acffb5f02e9b715aba178285a867c311ee18cd2fc4d91d381b9d9",
    "diagnostic-scope.json": "b9c8186870e565dc0f6ac2485d9e29a42795aee1745723ac65ef8a384ba5347e",
    f"{FINAL_CYCLE}/input.json": "0caa88902542573ad3c9352e54893011b0f16d577dce0f81e68d5c6a159bb159",
    f"{FINAL_CYCLE}/report.json": "98777c305225ff7bbfdaaff635ca61b8b564352f1c7d8ccd8a9d3ae7f03639bf",
}
RELEASE_FIELDS = (
    "qualified_for_design",
    "acceptance",
    "drilling_released",
    "fabrication_released",
    "structural_released",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _unreleased(record: dict) -> bool:
    return all(record.get(field) is False for field in RELEASE_FIELDS)


def _validate_summary(summary: dict) -> dict:
    accepted = summary.get("accepted_cases", {}).get(CASE, {})
    attempts = summary.get("attempts", [])
    inventory = summary.get("topology_inventory", {})
    mechanics = summary.get("mechanics_identity", {})
    if (
        summary.get("schema") != "simple_pb05_eight_station_diagnostic_run/v1"
        or summary.get("candidate") != CANDIDATE
        or summary.get("deterministic_input_fingerprint") != FINGERPRINT
        or summary.get("case_order", [None])[0] != CASE
        or summary.get("loads", {}).get(CASE)
        != {"hold": "A12", "horizontal_force_xy_n": FORCE_XYZ_N[:2]}
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
        or attempts[0].get("native_report_sha256") != REPORT_SHA256
        or attempts[0].get("numerically_accepted") is not True
        or attempts[0].get("forces_in_suite_summary") is not False
        or mechanics.get("pb05_source_id") != CANDIDATE
        or mechanics.get("source_fingerprint_sha256") != SOURCE_FINGERPRINT
        or mechanics.get("legacy_proxy_stations") != 14
        or mechanics.get("fixed_panel_kicker_axes") != 66
        or inventory.get("legacy_station_count") != 14
        or inventory.get("fixed_panel_kicker_axis_count") != 66
        or inventory.get("pb05_tension_only_bolt_count") != 32
        or len(inventory.get("pb05_bolt_names", [])) != 32
        or inventory.get("pb02_tension_only_bolt_count") != 10
        or len(inventory.get("tension_only_bolt_names", [])) != 42
        or inventory.get("pb05_contact_cell_count") != 64
        or len(inventory.get("pb05_contact_names", [])) != 64
        or inventory.get("block_member_count") != 8
        or summary.get("developmental_only") is not True
        or summary.get("rejected_attempt_forces_included") is not False
        or not _unreleased(summary)
    ):
        raise ValueError("PB05 summary identity changed")
    return inventory


def _validate_report(report: dict, summary: dict, inventory: dict) -> None:
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
        or report.get("pb05_diagnostic_identity") != FINGERPRINT
        or report.get("pb05_mechanics_identity") != summary.get("mechanics_identity")
        or report.get("pb05_model_identity") != ARTIFACTS["model.pkl"]
        or report.get("parameters", {}).get("hold") != "A12"
        or report.get("parameters", {}).get("force_xyz_n") != FORCE_XYZ_N
        or scope.get("case") != CASE
        or scope.get("candidate") != CANDIDATE
        or scope.get("deterministic_input_fingerprint") != FINGERPRINT
        or scope.get("contact_update_strategy") != "all"
        or scope.get("search_seed_case") is not None
        or scope.get("developmental_only") is not True
        or any(report.get(field) is not True for field in audits)
        or len(report.get("angle_stations", [])) != 14
        or report.get("axial_tension_names") != inventory["tension_only_bolt_names"]
        or len(report.get("axial_tension", [])) != 42
        or [row.get("directory") for row in cycles]
        != [f"cycle-{index:02d}" for index in range(9)]
        or any(row.get("contact_passed") is True for row in cycles[:-1])
        or cycles[-1].get("contact_passed") is not True
        or cycles[-1].get("axial_tension_passed") is not True
        or not _unreleased(report)
        or not _unreleased(scope)
    ):
        raise ValueError("PB05 report identity changed")
    if (
        not set(inventory["pb05_contact_names"])
        <= {row.get("name") for row in report.get("bearings", [])}
        or not set(inventory["block_member_names"])
        <= set(report.get("member_section_demands", {}))
        or not set(inventory["required_physical_names"])
        <= set(report.get("physical_connection_forces", {}))
    ):
        raise ValueError("PB05 physical inventory incomplete")
    for record in report["physical_connection_forces"].values():
        force = record.get("force_on_first_xyz_n")
        if (
            not isinstance(force, list)
            or len(force) != 3
            or any(
                not isinstance(value, (int, float)) or not math.isfinite(value)
                for value in force
            )
        ):
            raise ValueError("PB05 physical force invalid")
    if any(
        not isinstance(value, (int, float))
        or not math.isfinite(value)
        or abs(value) > limit
        for residuals, limit in (
            (report.get("force_residual_n", []), 0.1),
            (report.get("moment_residual_nmm", []), 20.0),
        )
        for value in residuals
    ) or any(
        len(report.get(field, [])) != 3
        for field in ("force_residual_n", "moment_residual_nmm")
    ):
        raise ValueError("PB05 numerical equilibrium changed")


def _authenticate_artifacts(report: dict) -> None:
    for relative, expected in ARTIFACTS.items():
        if (
            report.get("artifact_sha256", {}).get(relative) != expected
            or _sha256(ATTEMPT / relative) != expected
        ):
            raise ValueError(f"retained artifact changed: {relative}")
    final_input = _load(ATTEMPT / FINAL_CYCLE / "input.json")
    final_report = _load(ATTEMPT / FINAL_CYCLE / "report.json")
    if _load(ATTEMPT / "diagnostic-scope.json") != report["diagnostic_scope"]:
        raise ValueError("retained scope differs from accepted report")
    if (
        final_input.get("candidate") != CANDIDATE
        or final_input.get("hold") != "A12"
        or final_input.get("force_xyz_n") != FORCE_XYZ_N
        or not _unreleased(final_input)
        or final_input.get("actual_joint_demands_qualified") is not False
        or final_report.get("qualified_for_design") is not False
        or any(final_report.get(field) is True for field in RELEASE_FIELDS)
        or final_report.get("actual_joint_demands_qualified") is not False
    ):
        raise ValueError("retained final-cycle identity changed")
    for field in (
        "physical_connection_forces",
        "member_section_demands",
        "bearings",
        "axial_tension",
        "force_residual_n",
        "moment_residual_nmm",
        "global_equilibrium_passed",
        "member_equilibrium_passed",
        "mpc_check_passed",
    ):
        if final_report.get(field) != report.get(field):
            raise ValueError(f"final-cycle report differs: {field}")


def _authenticate_sources(summary: dict, report: dict) -> dict:
    expected = report.get("source_sha256")
    producer = summary.get("producer_source_sha256")
    actual = {
        path.relative_to(SNAPSHOTS).as_posix(): _sha256(path)
        for path in SNAPSHOTS.rglob("*")
        if path.is_file()
    }
    if (
        not isinstance(expected, dict)
        or len(expected) != 293
        or actual != expected
        or not isinstance(producer, dict)
        or len(producer) != 206
        or any(expected.get(name) != digest for name, digest in producer.items())
    ):
        raise ValueError("source snapshot closure changed")
    return {"file_count": len(actual), "producer_file_count": len(producer)}


def _authenticate_package_inventory(report: dict) -> None:
    expected = {
        SUMMARY.relative_to(PACKAGE).as_posix(),
        (ATTEMPT / "report.json").relative_to(PACKAGE).as_posix(),
    }
    expected.update(
        (ATTEMPT / name).relative_to(PACKAGE).as_posix() for name in ARTIFACTS
    )
    expected.update(
        (SNAPSHOTS / name).relative_to(PACKAGE).as_posix()
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
    """Fail closed unless the retained PB05 first case is complete and authenticated."""
    if _sha256(SUMMARY) != SUMMARY_SHA256:
        raise ValueError("PB05 summary hash changed")
    summary = _load(SUMMARY)
    inventory = _validate_summary(summary)
    if _sha256(ATTEMPT / "report.json") != REPORT_SHA256:
        raise ValueError("PB05 accepted report hash changed")
    report = _load(ATTEMPT / "report.json")
    _validate_report(report, summary, inventory)
    _authenticate_artifacts(report)
    sources = _authenticate_sources(summary, report)
    _authenticate_package_inventory(report)
    return {
        "schema": "simple_pb05_first_case_evidence/v1",
        "candidate": CANDIDATE,
        "case": CASE,
        "deterministic_input_fingerprint": FINGERPRINT,
        "pb05_source_fingerprint_sha256": SOURCE_FINGERPRINT,
        "summary_sha256": SUMMARY_SHA256,
        "report_sha256": REPORT_SHA256,
        "model_sha256": ARTIFACTS["model.pkl"],
        "final_cycle": FINAL_CYCLE,
        "cycle_count": 9,
        "fixed_panel_kicker_axis_count": 66,
        "legacy_station_count": 14,
        "pb05_bolt_count": 32,
        "pb05_contact_cell_count": 64,
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
