"""Authenticate the compact PB02 rear-clear six-case evidence package."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "fea/results/diagnostics/pb02-rear-clear-10333d2-v1"
SIX_CASE = PACKAGE / "six-case"
SUMMARY = SIX_CASE / "pb02-six-case-diagnostic.json"
SOURCE_SNAPSHOTS = PACKAGE / "source_snapshots"

EXPECTED_SUMMARY_SHA256 = (
    "3aa766d4d374235922e8a0a0ec6ae7371e24bf2f1deb7ae0ab84bfbf548264f8"
)
EXPECTED_GEOMETRY_FINGERPRINT = (
    "4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb"
)
EXPECTED_SCOPE_FINGERPRINT = (
    "b6ae00b8b90622260bcf79e0f6a37ec382b66df1efc8a289d761789eefb0e5c0"
)
EXPECTED_PARTITION_FINGERPRINT = (
    "e9cb8ea7a1f197728ed3f02e99b27b9b3445446b989a167474e9d6da674c77c4"
)
CANDIDATE = "pb02-kerf-right-native-development-only"
FLOOR_STIFFNESS_N_PER_MM = 10000.0
EXPECTED_SOURCE_FILE_COUNT = 278
EXPECTED_PRODUCER_SOURCE_FILE_COUNT = 191
FINAL_ARTIFACTS = ("input.json", "frame.dat", "frame.frd", "frame.12d")
EXPECTED_VALIDATION = {
    "geometry_inventory": True,
    "topology_inventory": True,
    "candidate_identity": True,
    "stiffness_inventory": True,
    "producer_source_inventory": True,
    "six_case_load_inventory": True,
    "all_accepted_case_equilibrium_audits": True,
}

EXPECTED_CASES = {
    "a12-forward": {
        "hold": "A12",
        "horizontal_force_xy_n": [0.0, -300.0],
        "force_xyz_n": [0.0, -300.0, -2224.11080763025],
        "path": "attempts/a12-forward-01-all-unseeded",
        "report_sha256": (
            "eb3de71cc9c752244599540413c107c84eb225decd029183d491a5ac034cdfed"
        ),
        "model_identity": (
            "19ee74cc32fe1079ac3647469aee6e1935d99a7253f912f28541fbb5e2774991"
        ),
    },
    "a12-rear": {
        "hold": "A12",
        "horizontal_force_xy_n": [0.0, 300.0],
        "force_xyz_n": [0.0, 300.0, -2224.11080763025],
        "path": "attempts/a12-rear-01-all-unseeded",
        "report_sha256": (
            "dee289ff5a897fa8e0730919e93c681bef69390efbf71066d13e6b02e3550af4"
        ),
        "model_identity": (
            "b291b10482e3d98be9e84a2feeb5d5a438045ce801309cc43a13bcb046f207dc"
        ),
    },
    "a12-left": {
        "hold": "A12",
        "horizontal_force_xy_n": [-300.0, 0.0],
        "force_xyz_n": [-300.0, 0.0, -2224.11080763025],
        "path": "attempts/a12-left-01-all-unseeded",
        "report_sha256": (
            "0655276c0d37a30599c897a055618bf16a4b28997879da2be8944b2ce73daa7c"
        ),
        "model_identity": (
            "c9e859f3a8c9b492455631dcfdcc84a401053e783399646cf791822cbe9667de"
        ),
    },
    "k12-right": {
        "hold": "K12",
        "horizontal_force_xy_n": [300.0, 0.0],
        "force_xyz_n": [300.0, 0.0, -2224.11080763025],
        "path": "attempts/k12-right-01-all-unseeded",
        "report_sha256": (
            "0344ce5df9e4dcf3125ea05c16ae41e0c2de434dc5a940d0ccf9c4b00b94426e"
        ),
        "model_identity": (
            "f11e8cd99c2cfd675a724ff570fbf7310c333e8955ca59a89278cad1c099ced4"
        ),
    },
    "k12-rear": {
        "hold": "K12",
        "horizontal_force_xy_n": [0.0, 300.0],
        "force_xyz_n": [0.0, 300.0, -2224.11080763025],
        "path": "attempts/k12-rear-01-all-unseeded",
        "report_sha256": (
            "ef6646e86b6cb41d89e3d540c9bbae557ffa556e5e63f97efe2ddebc0c59a458"
        ),
        "model_identity": (
            "0807e7d5fa47c2b5a746b7f1e40abed20e944802a2161f42a524d35f17b218ae"
        ),
    },
    "a1-rear": {
        "hold": "A1",
        "horizontal_force_xy_n": [0.0, 300.0],
        "force_xyz_n": [0.0, 300.0, -2224.11080763025],
        "path": "attempts/a1-rear-01-all-unseeded",
        "report_sha256": (
            "471ec6ab82b6632c5d91b4fe5867cef13baa4efd122e21e3bdedcbd7369144fc"
        ),
        "model_identity": (
            "25b0abd698ea7320e6df8914557cf38fd0b5cc45e0e6f09dff9bea825b6b8076"
        ),
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _authenticate_summary() -> tuple[dict, str]:
    actual_sha256 = _sha256(SUMMARY)
    if actual_sha256 != EXPECTED_SUMMARY_SHA256:
        raise ValueError("six-case summary hash changed")
    summary = json.loads(SUMMARY.read_text())
    selected = summary.get("stiffness_selection", {}).get("exact_selected_values", {})
    contact = summary.get("stiffness_selection", {}).get("contact_model", {})
    expected_loads = {
        name: {
            "hold": expected["hold"],
            "horizontal_force_xy_n": expected["horizontal_force_xy_n"],
        }
        for name, expected in EXPECTED_CASES.items()
    }
    validation = summary.get("validation", {})
    if (
        summary.get("schema") != "simple_center_pb02_diagnostic_run/v1"
        or summary.get("candidate") != CANDIDATE
        or summary.get("active_geometry_fingerprint") != EXPECTED_GEOMETRY_FINGERPRINT
        or summary.get("case_order") != list(EXPECTED_CASES)
        or summary.get("loads") != expected_loads
        or summary.get("accepted_case_count") != len(EXPECTED_CASES)
        or set(summary.get("accepted_cases", {})) != set(EXPECTED_CASES)
        or summary.get("deterministic_input_fingerprint") != EXPECTED_SCOPE_FINGERPRINT
        or selected.get("floor_contact_n_per_mm") != FLOOR_STIFFNESS_N_PER_MM
        or contact.get("partition_fingerprint") != EXPECTED_PARTITION_FINGERPRINT
        or len(summary.get("attempts", [])) != len(EXPECTED_CASES)
        or validation != EXPECTED_VALIDATION
        or summary.get("developmental_only") is not True
        or summary.get("acceptance") is not False
        or summary.get("qualified_for_design") is not False
        or summary.get("actual_joint_demands_qualified") is not False
        or summary.get("resistance_checked") is not False
        or summary.get("drilling_released") is not False
        or summary.get("fabrication_released") is not False
        or summary.get("rejected_attempt_forces_included") is not False
    ):
        raise ValueError("six-case summary identity changed")
    return summary, actual_sha256


def _authenticate_attempts(summary: dict) -> None:
    attempts = {row.get("case"): row for row in summary["attempts"]}
    if set(attempts) != set(EXPECTED_CASES):
        raise ValueError("six-case attempt inventory changed")
    for name, expected in EXPECTED_CASES.items():
        accepted = summary["accepted_cases"][name]
        attempt = attempts[name]
        if (
            accepted.get("path") != expected["path"]
            or accepted.get("report_sha256") != expected["report_sha256"]
            or accepted.get("numerically_accepted") is not True
            or accepted.get("forces_reported_only_in_authenticated_case_report")
            is not True
            or attempt.get("native_report_sha256") != expected["report_sha256"]
            or attempt.get("contact_active_set_converged") is not True
            or attempt.get("numerically_accepted") is not True
            or attempt.get("forces_in_suite_summary") is not False
        ):
            raise ValueError(f"{name}: accepted attempt identity changed")


def _authenticate_report(name: str, expected: dict) -> tuple[dict, dict]:
    directory = SIX_CASE / expected["path"]
    report_path = directory / "report.json"
    actual_sha256 = _sha256(report_path)
    if actual_sha256 != expected["report_sha256"]:
        raise ValueError(f"{name}: report hash changed")
    report = json.loads(report_path.read_text())
    scope = report.get("diagnostic_scope", {})
    selected = scope.get("stiffness_selection", {}).get("exact_selected_values", {})
    required_true = (
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
        or scope.get("candidate") != CANDIDATE
        or scope.get("case") != name
        or report.get("parameters", {}).get("hold") != expected["hold"]
        or report.get("parameters", {}).get("force_xyz_n") != expected["force_xyz_n"]
        or report.get("pb02_model_identity") != expected["model_identity"]
        or scope.get("deterministic_input_fingerprint") != EXPECTED_SCOPE_FINGERPRINT
        or report.get("pb02_contact_aggregation", {}).get("partition_fingerprint")
        != EXPECTED_PARTITION_FINGERPRINT
        or scope.get("stiffness_selection", {})
        .get("contact_model", {})
        .get("partition_fingerprint")
        != EXPECTED_PARTITION_FINGERPRINT
        or selected.get("floor_contact_n_per_mm") != FLOOR_STIFFNESS_N_PER_MM
        or report.get("parameters", {}).get("stiffnesses", {}).get("floor")
        != FLOOR_STIFFNESS_N_PER_MM
        or any(report.get(field) is not True for field in required_true)
        or scope.get("developmental_only") is not True
        or scope.get("acceptance") is not False
        or scope.get("qualified_for_design") is not False
        or scope.get("actual_joint_demands_qualified") is not False
        or scope.get("resistance_checked") is not False
        or scope.get("drilling_released") is not False
        or scope.get("fabrication_released") is not False
        or report.get("qualified_for_design") is not False
        or report.get("actual_joint_demands_qualified") is not False
        or report.get("drilling_released") is not False
        or report.get("fabrication_released") is not False
    ):
        raise ValueError(f"{name}: authenticated report scope changed")

    cycles = report.get("contact_cycles", [])
    if not cycles or not isinstance(cycles[-1].get("directory"), str):
        raise ValueError(f"{name}: final-cycle identity changed")
    cycle_name = cycles[-1]["directory"]
    artifact_hashes = report.get("artifact_sha256", {})
    authenticated_artifacts = {}
    for filename in FINAL_ARTIFACTS:
        relative = f"{cycle_name}/{filename}"
        path = directory / relative
        expected_artifact_sha256 = artifact_hashes.get(relative)
        if not expected_artifact_sha256 or _sha256(path) != expected_artifact_sha256:
            raise ValueError(f"{name}: retained final-cycle artifact changed")
        authenticated_artifacts[filename] = expected_artifact_sha256

    return report, {
        "path": expected["path"],
        "report_sha256": actual_sha256,
        "model_identity": report["pb02_model_identity"],
        "deterministic_input_fingerprint": scope["deterministic_input_fingerprint"],
        "partition_fingerprint": report["pb02_contact_aggregation"][
            "partition_fingerprint"
        ],
        "full_load_vector_xyz_n": report["parameters"]["force_xyz_n"],
        "final_cycle": cycle_name,
        "final_cycle_artifact_sha256": authenticated_artifacts,
    }


def _authenticate_sources(summary: dict, reports: dict) -> dict:
    source_maps = [report.get("source_sha256") for report in reports.values()]
    if not source_maps or any(
        source_map != source_maps[0] for source_map in source_maps
    ):
        raise ValueError("common source snapshot closure changed")
    common = source_maps[0]
    producer = summary.get("producer_source_sha256")
    if not isinstance(common, dict) or len(common) != EXPECTED_SOURCE_FILE_COUNT:
        raise ValueError("common source snapshot closure changed")
    try:
        actual = {
            relative: _sha256(SOURCE_SNAPSHOTS / relative)
            for relative in common
            if not Path(relative).is_absolute() and ".." not in Path(relative).parts
        }
    except OSError as error:
        raise ValueError("common source snapshot closure changed") from error
    if (
        actual != common
        or not isinstance(producer, dict)
        or len(producer) != EXPECTED_PRODUCER_SOURCE_FILE_COUNT
        or any(common.get(path) != digest for path, digest in producer.items())
    ):
        raise ValueError("common source snapshot closure changed")
    return {
        "path": "../source_snapshots",
        "file_count": len(actual),
        "source_sha256_map_identical_across_reports": True,
        "all_snapshot_hashes_match": True,
        "summary_producer_map_is_authenticated_subset": True,
    }


def screen() -> dict:
    summary, summary_sha256 = _authenticate_summary()
    _authenticate_attempts(summary)
    reports = {}
    cases = {}
    for name, expected in EXPECTED_CASES.items():
        reports[name], cases[name] = _authenticate_report(name, expected)
    sources = _authenticate_sources(summary, reports)
    return {
        "status": "authenticated_pb02_rear_clear_six_case_development_evidence",
        "summary": {
            "path": SUMMARY.relative_to(PACKAGE).as_posix(),
            "sha256": summary_sha256,
            "candidate": CANDIDATE,
            "geometry_fingerprint": EXPECTED_GEOMETRY_FINGERPRINT,
            "deterministic_input_fingerprint": EXPECTED_SCOPE_FINGERPRINT,
            "partition_fingerprint": EXPECTED_PARTITION_FINGERPRINT,
            "floor_contact_n_per_mm": FLOOR_STIFFNESS_N_PER_MM,
            "accepted_case_count": len(cases),
        },
        "cases": cases,
        "source_snapshot_authentication": sources,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    result = screen()
    encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if arguments.output:
        arguments.output.write_text(encoded)
    else:
        print(encoded, end="")
