"""Authenticate PB02 contact refinement and bounded density evidence."""

import argparse
import hashlib
import importlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "fea/results/diagnostics/pb02-contact-refinement-a12-forward-v1"
SOURCE_SNAPSHOTS = EVIDENCE / "source_snapshots"
GEOMETRY_SOURCE = "scripts/simple_center_pb02_geometry.py"
EXPECTED_GEOMETRY_FINGERPRINT = (
    "06f0cd1a1754d26fb2ff74cc2eb7da8eed80fbbea5cc84d7627ae8ff07d61387"
)
REPORTS = {
    "grid_2x2": (
        "grid-2x2/report.json",
        "837523aeebf3f997cc6271fe3f11a7bb19830573d6fbfabc3dbe8b90eb644504",
    ),
    "grid_4x4": (
        "grid-4x4/report.json",
        "d1e04abaefbda829125b12cd13392d8567b8ed7c7df89baf1e931f9a0eda7653",
    ),
    "grid_8x8": (
        "grid-8x8/report.json",
        "5587450b5760cee02e3b9895301959aa361c6cc644384f6ce35047c4f0de70ef",
    ),
    "density_0p5x": (
        "density-0p5x/report.json",
        "eb1cfe5987b7edfe79102c1f1507ab3302be9e570eff0560e64dab857cd1a6d6",
    ),
    "density_2x": (
        "density-2x/report.json",
        "a5e24552a90e4d6e27a987e381665bcc489a9021b61769c77fbbd0c5948e3631",
    ),
}
EXPECTED_REPORT_SCOPE = {
    "grid_2x2": {
        "grid": [2, 2],
        "mean_contact_total_n_per_mm": 1000.0,
        "model_identity": "83fc82f95c89a63d07ce2dccdbbdd059c2484e1dd985902e568e7087aba59d3c",
        "scope_fingerprint": "359e4eacd3f9312f32e36963da20b90988fa1e9a52f934b6d294f1c0247048c3",
    },
    "grid_4x4": {
        "grid": [4, 4],
        "mean_contact_total_n_per_mm": 1000.0,
        "model_identity": "6973760a3e837078db6b15619534acde6c1601e76e67829c56df29053b8e9232",
        "scope_fingerprint": "f60d3bc138e08d8d68aacf4b15f9c563674945a8c9e53eb87e54a585e1fe4d26",
    },
    "grid_8x8": {
        "grid": [8, 8],
        "mean_contact_total_n_per_mm": 1000.0,
        "model_identity": "6c7826ff24b3427e5abfc4ac4f4d0deb1205905deec177f8bb80233babdc9824",
        "scope_fingerprint": "0dc36a7cf57f8e1f93fc5505e094bbd459aa4893aca9027afc4b9abedd4e0ba1",
    },
    "density_0p5x": {
        "grid": [8, 8],
        "mean_contact_total_n_per_mm": 500.0,
        "model_identity": "fd9379062004256ac4d8de3265d51a5e9b59274e1633a95060e0245d080eab7f",
        "scope_fingerprint": "9b74e0754354938e2881806d4bddf46669be07b3922b1bf2f0ec05794dae3657",
    },
    "density_2x": {
        "grid": [8, 8],
        "mean_contact_total_n_per_mm": 2000.0,
        "model_identity": "876f860e709ab8a0d5fc6d3e755367adeb51e97f6aa63f28f3be0541c4c73d1a",
        "scope_fingerprint": "9c019a17ebf5b2600e67b4686d55363be6f6b109861ef6db71ef13718cf9d930",
    },
}
CANDIDATE = "pb02-kerf-right-native-development-only"


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
        or contact.get("grid_resolution") != expected["grid"]
        or selected.get("face_normal_total_per_interface_n_per_mm")
        != expected["mean_contact_total_n_per_mm"]
        or report.get("pb02_model_identity") != expected["model_identity"]
        or scope.get("deterministic_input_fingerprint") != expected["scope_fingerprint"]
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
            "Run the remaining five prescribed cases at 8x8/reference density, then "
            "apply the bounded density envelope where it can change the component decision."
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
