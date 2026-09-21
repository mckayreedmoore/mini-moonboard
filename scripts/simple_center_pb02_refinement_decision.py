"""Authenticate PB02 contact refinement and bounded density evidence."""

import argparse
import hashlib
import importlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "fea/results/diagnostics/pb02-rear-clear-10333d2-v1"
SOURCE_SNAPSHOTS = EVIDENCE / "source_snapshots"
GEOMETRY_SOURCE = "scripts/simple_center_pb02_geometry.py"
EXPECTED_GEOMETRY_FINGERPRINT = (
    "4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb"
)
REPORTS = {
    "grid_2x2": (
        "refinement/grid-2x2/report.json",
        "5eabdc13399213e7e1eab32d55b8f72e5c47fd536840b74e9b3d9fce8aa82c84",
    ),
    "grid_4x4": (
        "refinement/grid-4x4/report.json",
        "81c11dfd88bca1c34312210b49082f282e034b81b77a3974a555d68c0b654bd3",
    ),
    "grid_8x8": (
        "refinement/grid-8x8/report.json",
        "eb3de71cc9c752244599540413c107c84eb225decd029183d491a5ac034cdfed",
    ),
    "density_0p5x": (
        "refinement/density-0p5x/report.json",
        "ff8b8cd6bc40f8b42f65d72971c0b12b4cee5097f31c55b0779a0bb4455a34ac",
    ),
    "density_2x": (
        "refinement/density-2x/report.json",
        "4e8f9c193c225fe3d28002ab93ed3258d7560558ed089f27a49752adeea36023",
    ),
}
EXPECTED_REPORT_SCOPE = {
    "grid_2x2": {
        "grid": [2, 2],
        "mean_contact_total_n_per_mm": 1000.0,
        "model_identity": "2dff09bd82efc968c8355bb283647b4bcac07ae65f7674d66f97be897bee0dd5",
        "scope_fingerprint": "a8498e3fd74b4229579c03d43a03f6cdc5de49308ba9d328b93263775f840786",
        "partition_fingerprint": "2f105d500f308d344cf72773d53001c1a187321d625d20624f00cd463823d67a",
    },
    "grid_4x4": {
        "grid": [4, 4],
        "mean_contact_total_n_per_mm": 1000.0,
        "model_identity": "9aebb8efc13d8df1ce41bfeef05164668a6363898738df5ece91cf5ee00fa492",
        "scope_fingerprint": "6c3b4994a594960fb76f26624ea72a5090c5599a042ae94b395327847241648d",
        "partition_fingerprint": "89079b51b9cad87bba882dc1b392f0a26d688109b556caf5a51a63f1180e5628",
    },
    "grid_8x8": {
        "grid": [8, 8],
        "mean_contact_total_n_per_mm": 1000.0,
        "model_identity": "19ee74cc32fe1079ac3647469aee6e1935d99a7253f912f28541fbb5e2774991",
        "scope_fingerprint": "b6ae00b8b90622260bcf79e0f6a37ec382b66df1efc8a289d761789eefb0e5c0",
        "partition_fingerprint": "e9cb8ea7a1f197728ed3f02e99b27b9b3445446b989a167474e9d6da674c77c4",
    },
    "density_0p5x": {
        "grid": [8, 8],
        "mean_contact_total_n_per_mm": 500.0,
        "model_identity": "b92349520bca4a9d040d721ddc1a3c98fa88469f586636a72ca4c534cbf773a0",
        "scope_fingerprint": "c8a72c2f503fe7dca994aba0a77a1c5c9c107e6e408f376b6402e20496ee3ec8",
        "partition_fingerprint": "e9cb8ea7a1f197728ed3f02e99b27b9b3445446b989a167474e9d6da674c77c4",
    },
    "density_2x": {
        "grid": [8, 8],
        "mean_contact_total_n_per_mm": 2000.0,
        "model_identity": "6ff81b19cd60be0e2241af7350534de26b3fb68214de6d73fa80433221468b6f",
        "scope_fingerprint": "ce354d1ed95456b07e3c04cfe857f064d3987106124425391736c361d46dd773",
        "partition_fingerprint": "e9cb8ea7a1f197728ed3f02e99b27b9b3445446b989a167474e9d6da674c77c4",
    },
}
CANDIDATE = "pb02-kerf-right-native-development-only"
EXPECTED_FORCE_XYZ_N = [0.0, -300.0, -2224.11080763025]
RETAINED_FINAL_FILES = ("input.json", "frame.dat", "frame.frd", "frame.12d")


def _active_geometry_fingerprint() -> str:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    geometry = importlib.import_module("scripts.simple_center_pb02_geometry")
    return geometry.ACTIVE_FINGERPRINT


def _magnitude(values):
    return math.sqrt(sum(value * value for value in values))


def _change_percent(first, second):
    return abs(second / first - 1.0) * 100 if abs(first) > 1.0e-12 else None


def _authenticate(name, relative, expected_sha256):
    path = EVIDENCE / relative
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ValueError(f"{name}: report hash changed")
    report = json.loads(path.read_text())
    scope = report.get("diagnostic_scope", {})
    stiffness = scope.get("stiffness_selection", {})
    selected = stiffness.get("exact_selected_values", {})
    contact = stiffness.get("contact_model", {})
    expected = EXPECTED_REPORT_SCOPE[name]
    required = (
        "contact_active_set_converged",
        "axial_tension_active_set_converged",
        "closed_bearing_assumption_passed",
        "global_equilibrium_passed",
        "member_equilibrium_passed",
        "mpc_check_passed",
        "numerically_accepted",
    )
    if (
        report.get("candidate") != CANDIDATE
        or scope.get("candidate") != CANDIDATE
        or scope.get("case") != "a12-forward"
        or report.get("parameters", {}).get("hold") != "A12"
        or report.get("parameters", {}).get("force_xyz_n") != EXPECTED_FORCE_XYZ_N
        or contact.get("grid_resolution") != expected["grid"]
        or selected.get("face_normal_total_per_interface_n_per_mm")
        != expected["mean_contact_total_n_per_mm"]
        or selected.get("floor_contact_n_per_mm") != 10000.0
        or report.get("pb02_model_identity") != expected["model_identity"]
        or scope.get("deterministic_input_fingerprint") != expected["scope_fingerprint"]
        or report.get("pb02_contact_aggregation", {}).get("partition_fingerprint")
        != expected["partition_fingerprint"]
        or _active_geometry_fingerprint() != EXPECTED_GEOMETRY_FINGERPRINT
        or scope.get("developmental_only") is not True
        or scope.get("qualified_for_design") is not False
        or scope.get("actual_joint_demands_qualified") is not False
        or scope.get("resistance_checked") is not False
        or scope.get("acceptance") is not False
        or scope.get("drilling_released") is not False
        or scope.get("fabrication_released") is not False
        or any(report.get(field) is not True for field in required)
        or report.get("qualified_for_design") is not False
        or report.get("actual_joint_demands_qualified") is not False
        or report.get("drilling_released") is not False
        or report.get("fabrication_released") is not False
    ):
        raise ValueError(f"{name}: authenticated developmental scope changed")
    final_cycle = report["contact_cycles"][-1]["directory"]
    retained = {}
    for filename in RETAINED_FINAL_FILES:
        artifact = f"{final_cycle}/{filename}"
        artifact_path = path.parent / artifact
        actual_artifact = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if report.get("artifact_sha256", {}).get(artifact) != actual_artifact:
            raise ValueError(f"{name}: retained final-cycle artifact changed")
        retained[artifact] = actual_artifact
    return report, {
        "path": relative,
        "report_sha256": actual,
        "model_identity": report["pb02_model_identity"],
        "deterministic_input_fingerprint": report["diagnostic_scope"][
            "deterministic_input_fingerprint"
        ],
        "partition_fingerprint": report["pb02_contact_aggregation"][
            "partition_fingerprint"
        ],
        "cycles": len(report["contact_cycles"]),
        "retained_final_cycle_artifacts": retained,
    }


def _authenticate_source_snapshots(reports):
    source_maps = [report.get("source_sha256") for report in reports.values()]
    if not source_maps or any(
        source_map != source_maps[0] for source_map in source_maps
    ):
        raise ValueError("common source snapshot closure changed")
    actual = {
        path.relative_to(SOURCE_SNAPSHOTS).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in SOURCE_SNAPSHOTS.rglob("*")
        if path.is_file()
    }
    if actual != source_maps[0]:
        raise ValueError("common source snapshot closure changed")
    return {
        "path": str(SOURCE_SNAPSHOTS.relative_to(EVIDENCE)),
        "file_count": len(actual),
        "source_sha256_map_identical_across_reports": True,
        "all_snapshot_hashes_match": True,
    }


def _interface_metrics(report):
    return {
        name: {
            "force_n": _magnitude(row["force_resultant_n"]),
            "moment_nmm": _magnitude(row["moment_resultant_about_net_centroid_nmm"]),
            "active_area_mm2": row["active_tributary_area_mm2"],
            "peak_cell_average_pressure_n_per_mm2": row[
                "peak_average_cell_pressure_n_per_mm2"
            ],
        }
        for name, row in report["pb02_contact_aggregation"]["interfaces"].items()
    }


def _maximum_bolt(report):
    interfaces = set(report["pb02_contact_aggregation"]["interfaces"])
    rows = []
    for name, row in report["physical_connection_forces"].items():
        if "/bolt_" not in name or name.split("/", 1)[0] not in interfaces:
            continue
        rows.append(
            {
                "name": name,
                "combined_n": _magnitude(row["force_on_first_xyz_n"]),
                "axial_n": max(0.0, row["axial_along_installation_direction_n"]),
                "lateral_n": row["transverse_shear_n"],
            }
        )
    return max(rows, key=lambda row: row["combined_n"])


def screen():
    reports = {}
    authentication = {}
    for name, (relative, digest) in REPORTS.items():
        reports[name], authentication[name] = _authenticate(name, relative, digest)
    source_snapshot_authentication = _authenticate_source_snapshots(reports)

    grid_metrics = {
        name: _interface_metrics(reports[name])
        for name in ("grid_2x2", "grid_4x4", "grid_8x8")
    }
    refinement = {}
    for interface in grid_metrics["grid_8x8"]:
        coarse = grid_metrics["grid_4x4"][interface]
        fine = grid_metrics["grid_8x8"][interface]
        refinement[interface] = {
            field: {
                "grid_4x4": coarse[field],
                "grid_8x8": fine[field],
                "absolute_change_percent": _change_percent(coarse[field], fine[field]),
            }
            for field in coarse
        }

    density_names = ("density_0p5x", "grid_8x8", "density_2x")
    density_metrics = {
        name: _interface_metrics(reports[name]) for name in density_names
    }
    density = {}
    for interface in density_metrics["grid_8x8"]:
        density[interface] = {}
        for field in ("force_n", "moment_nmm"):
            values = {
                name: density_metrics[name][interface][field] for name in density_names
            }
            density[interface][field] = values | {
                "maximum_to_minimum": max(values.values()) / min(values.values())
            }

    bolts = {name: _maximum_bolt(reports[name]) for name in density_names}
    refinement_bolts = {
        name: _maximum_bolt(reports[name]) for name in ("grid_4x4", "grid_8x8")
    }
    displacement = {
        name: reports[name]["maximum_panel_displacement_mm"] for name in density_names
    }
    return {
        "status": "authenticated_a12_forward_development_decision",
        "authentication": authentication,
        "source_snapshot_authentication": source_snapshot_authentication,
        "grid_refinement_4x4_to_8x8": {
            "interfaces": refinement,
            "maximum_force_change_percent": max(
                row["force_n"]["absolute_change_percent"] for row in refinement.values()
            ),
            "maximum_moment_change_percent": max(
                row["moment_nmm"]["absolute_change_percent"]
                for row in refinement.values()
            ),
            "maximum_active_area_change_percent": max(
                row["active_area_mm2"]["absolute_change_percent"]
                for row in refinement.values()
            ),
            "maximum_peak_cell_average_pressure_change_percent": max(
                row["peak_cell_average_pressure_n_per_mm2"]["absolute_change_percent"]
                for row in refinement.values()
            ),
            "panel_displacement_change_percent": _change_percent(
                reports["grid_4x4"]["maximum_panel_displacement_mm"],
                reports["grid_8x8"]["maximum_panel_displacement_mm"],
            ),
            "governing_bolt_grid_4x4": refinement_bolts["grid_4x4"],
            "governing_bolt_grid_8x8": refinement_bolts["grid_8x8"],
            "maximum_bolt_combined_force_change_percent": _change_percent(
                refinement_bolts["grid_4x4"]["combined_n"],
                refinement_bolts["grid_8x8"]["combined_n"],
            ),
            "selected_force_moment_resolution": "8x8",
            "local_pressure_qualified": False,
        },
        "contact_density_sensitivity_8x8": {
            "interfaces": density,
            "maximum_force_ratio": max(
                row["force_n"]["maximum_to_minimum"] for row in density.values()
            ),
            "maximum_moment_ratio": max(
                row["moment_nmm"]["maximum_to_minimum"] for row in density.values()
            ),
            "governing_bolt_by_density": bolts,
            "governing_bolt_combined_force_ratio": (
                max(row["combined_n"] for row in bolts.values())
                / min(row["combined_n"] for row in bolts.values())
            ),
            "panel_displacement_mm": displacement,
            "panel_displacement_ratio": max(displacement.values())
            / min(displacement.values()),
            "stiffness_qualified": False,
        },
        "decision": "RETAIN_PB02_FOR_DEVELOPMENT_WITH_REVISION",
        "revision": (
            "Use the 8x8 model for global force and moment demand; carry the 2x "
            "contact-density case as the current same-case component screen. Do not "
            "use cell-average pressure as local bearing qualification."
        ),
        "next_case_action": (
            "Use the separately authenticated six-case suite to build current-geometry "
            "component envelopes; keep this density study scoped to A12-forward."
        ),
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
