"""Build the frozen BN-0 station and load register; never run a native solve."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

from fea.horizontal_frame_members import axes as member_axes
from mini_moonboard import compact_floor_flush_frame as baseline_model
from scripts import owner_barrel_native_connector_inventory as connector_source
from scripts.clear_space_batch import CASES
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_combined_owner_trial import report as revision_report
from scripts.owner_barrel_native_connector_inventory import build_inventory
from scripts.owner_barrel_native_face_contacts import build_report as contact_report
from scripts.owner_barrel_native_preparation import IntegratedBarrelNative, prepare_case

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "owner_barrel_validation_register/v1"
EXPECTED_CASES = (
    "a12-rear",
    "a12-forward",
    "a12-left",
    "k12-right",
    "k12-rear",
    "a1-rear",
)
EXPECTED_COUNTS = {
    "stations": 24,
    "barrel_bolts": 46,
    "barrels": 46,
    "barrel_pairs": 46,
    "barrel_face_contact_cells": 132,
    "drilling_paths": 98,
    "access_paths": 92,
    "retained_frame_bolts": 12,
    "fixed_panel_kicker_screws": 66,
    "removed_legacy_structural_sds": 144,
}
SOURCE_PATHS = tuple(
    sorted(
        set(connector_source.SOURCE_PATHS)
        | {
            "scripts/owner_barrel_validation_register.py",
            "scripts/owner_barrel_native_face_contacts.py",
            "scripts/owner_barrel_combined_owner_trial.py",
            "scripts/owner_barrel_native_preparation.py",
            "scripts/owner_barrel_retained_interfaces.py",
            "scripts/owner_barrel_visual_wood.py",
            "scripts/bolted_kerf_diagnostic_probe.py",
            "scripts/compact_rail_study.py",
            "scripts/clear_space_batch.py",
            "scripts/simple_owner_duty_ledger.py",
            "fea/reinforced_frame_demand.py",
            "fea/floor_flush_mesh.py",
            "fea/floor_flush_run.py",
            "fea/floor_recess_mesh.py",
            "fea/floor_taper_mesh.py",
            "fea/floor_uncut_mesh.py",
            "fea/current_response_model.py",
            "fea/current_response_materials.py",
            "fea/horizontal_frame_members.py",
            "fea/horizontal_panel_frame.py",
            "mini_moonboard/compact_floor_flush_frame.py",
        }
    )
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.strip()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise ValueError("Current Git commit is not a full SHA-1 identity")
    return commit


def _source_hashes() -> dict[str, str]:
    hashes = {}
    for name in SOURCE_PATHS:
        path = ROOT / name
        if not path.is_file():
            raise ValueError(f"Missing register source: {name}")
        hashes[name] = _sha256(path)
    return hashes


def _finite_vector(values, *, length: int, label: str) -> list[float]:
    result = [float(value) for value in values]
    if len(result) != length or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{label} must be a finite {length}-vector")
    return result


def _counts(assembly, inventory, contacts) -> dict[str, int]:
    return {
        "stations": len(inventory["stations"]),
        "barrel_bolts": len(inventory["bolts"]),
        "barrels": len(inventory["barrels"]),
        "barrel_pairs": contacts["bolt_interface_count"],
        "barrel_face_contact_cells": contacts["contact_cell_count"],
        "drilling_paths": len(assembly["drilling_paths"]),
        "access_paths": len(assembly["access_paths"]),
        "retained_frame_bolts": len(inventory["retained_frame_bolts"]),
        "fixed_panel_kicker_screws": len(inventory["fixed_panel_screws"]),
        "removed_legacy_structural_sds": len(
            inventory["excluded_legacy"]["sds_axes"]
        ),
    }


def validate_counts(counts: dict[str, int]) -> None:
    """Fail closed if any frozen BN-0 connection count moves."""
    if counts != EXPECTED_COUNTS:
        raise ValueError(
            f"Integrated barrel inventory changed: expected {EXPECTED_COUNTS}, got {counts}"
        )


def validate_approved_revisions(revision: dict) -> None:
    """Fail closed if approved N=42 mm or +2 mm bore changes are absent."""
    expected_moved = {
        "clip_horizontal_lower_left_2_barrel_1_bolt",
        "clip_horizontal_upper_left_2_barrel_1_bolt",
    }
    expected_extended = {
        f"barrel_trial_{station}_{row}/machine_bore"
        for station in ("clip_single_top_left_1", "clip_single_top_right_2")
        for row in (1, 2)
    }
    expected_moved_paths = {
        f"{bolt.removesuffix('_bolt')}/{role}"
        for bolt in expected_moved
        for role in ("barrel_bore", "machine_bore")
    }
    expected_intersection_categories = {
        "remaining_to_protected_cut_intersections",
        "remaining_to_center_cut_intersections",
        "remaining_to_outer_header_cut_intersections",
        "unrelated_remaining_pair_cut_intersections",
    }
    expected_tip_bolts = {
        path.removesuffix("/machine_bore") + "_bolt" for path in expected_extended
    }
    actual_moved = set(revision.get("moved_first_row_bolts", ()))
    actual_moved_paths = set(revision.get("moved_first_row_drilling_paths", ()))
    actual_extended = set(revision.get("extended_top_machine_bores", ()))
    changed = set(revision.get("changed_drilling_paths_checked", ()))
    changed_intersections = revision.get("changed_cut_intersections", {})
    protected_hits = revision.get("incremental_top_tip_protected_hits", {})
    receiver_coverage = revision.get("incremental_top_tip_receiver_coverage", {})
    other_wood_hits = revision.get("incremental_top_tip_other_wood_hits", {})
    tip_clearances = revision.get("top_tip_clearance_mm", {})
    if (
        revision.get("maintained_scene_changed") is not True
        or revision.get("owner_approval_pending") is not False
        or revision.get("first_row_trial_n_mm") != 42.0
        or revision.get("extension_mm") != 2.0
        or actual_moved != expected_moved
        or actual_moved_paths != expected_moved_paths
        or actual_extended != expected_extended
        or changed != expected_moved_paths | expected_extended
        or revision.get("whole_cut_barrel_pairs") != 46
        or revision.get("whole_cut_path_host_anomalies")
        or revision.get("whole_cut_missing_paths")
        or set(changed_intersections) != expected_intersection_categories
        or set(protected_hits) != expected_extended
        or set(receiver_coverage) != expected_extended
        or any(value != 1.0 for value in receiver_coverage.values())
        or set(other_wood_hits) != expected_extended
        or set(tip_clearances) != expected_tip_bolts
        or any(value != 2.0 for value in tip_clearances.values())
        or any(changed_intersections.values())
        or any(protected_hits.values())
        or any(other_wood_hits.values())
        or revision.get("source_wood_panel_frame_release_unchanged") is not True
        or revision.get("structural_released") is not False
        or revision.get("drilling_released") is not False
        or revision.get("fabrication_released") is not False
    ):
        raise ValueError("Approved N=42 mm / +2 mm integrated revision changed")


def _grain_axis(name: str) -> tuple[list[float] | None, str]:
    try:
        grain, _ = member_axes(baseline_model, name)
    except ValueError:
        return None, "not classified by native response member-axis source"
    return (
        _finite_vector(grain.toTuple(), length=3, label=f"{name} grain"),
        "fea.horizontal_frame_members.axes",
    )


def _station_paths(assembly, barrel_names, field: str) -> list[str]:
    prefixes = tuple(f"{name}/" for name in barrel_names)
    paths = sorted(name for name in assembly[field] if name.startswith(prefixes))
    if not paths:
        raise ValueError(f"Station has no {field}")
    return paths


def _station_records(assembly, inventory, contacts) -> dict[str, dict]:
    if set(inventory["stations"]) != set(contacts["stations"]):
        raise ValueError("Connector and face-contact station identities differ")
    result = {}
    for name in sorted(inventory["stations"]):
        source = inventory["stations"][name]
        members = source["timber_members"]
        grain = {}
        for member in members:
            axis, basis = _grain_axis(member)
            grain[member] = {"axis_xyz": axis, "basis": basis}
            if axis is None:
                raise ValueError(f"{name}: timber grain axis unavailable for {member}")
        bolt_names = source["bolt_names"]
        barrel_names = source["barrel_names"]
        result[name] = {
            "identity": name,
            "family": source["family"],
            "side": source["side"],
            "timber_members": members,
            "member_grain_axes": grain,
            "current_disposition": assembly["station_dispositions"][name],
            "bolts": {bolt: inventory["bolts"][bolt] for bolt in bolt_names},
            "barrels": {
                barrel: inventory["barrels"][barrel] for barrel in barrel_names
            },
            "drilling_path_names": _station_paths(
                assembly, barrel_names, "drilling_paths"
            ),
            "access_path_names": _station_paths(
                assembly, barrel_names, "access_paths"
            ),
            "contact": contacts["stations"][name],
        }
    return result


def _load_record(case: str, module: IntegratedBarrelNative) -> dict:
    structure, metadata, summary = prepare_case(case, module=module)
    del structure
    preparation = dict(summary)
    old_contact_key = "conditional_contact_n_per_mm2"
    new_contact_key = "conditional_contact_n_per_mm3"
    if new_contact_key in preparation:
        if old_contact_key in preparation:
            raise ValueError(f"{case}: ambiguous conditional contact stiffness units")
    else:
        preparation[new_contact_key] = preparation.pop(old_contact_key)
    hold, horizontal = CASES[case]
    expected_vertical = -2.0 * metadata["pounds"] * 0.45359237 * 9.80665
    if (
        summary["native_solve"] is not False
        or summary["structural_released"] is not False
        or metadata["acceptance"] is not False
        or metadata["actual_joint_demands_qualified"] is not False
        or metadata["hold"] != hold
        or list(horizontal) != metadata["force_xyz_n"][:2]
        or not math.isclose(
            metadata["force_xyz_n"][2], expected_vertical, abs_tol=1e-9
        )
    ):
        raise ValueError(f"{case}: unsolved load preparation identity changed")
    return {
        "case": case,
        "hold": hold,
        "requested_climber_weight_lbf": float(metadata["pounds"]),
        "horizontal_force_xy_n": _finite_vector(
            horizontal, length=2, label=f"{case} horizontal force"
        ),
        "applied_force_xyz_n": _finite_vector(
            metadata["force_xyz_n"], length=3, label=f"{case} force"
        ),
        "application_point_xyz_mm": _finite_vector(
            metadata["target_xyz_mm"], length=3, label=f"{case} target"
        ),
        "moment_at_panel_midplane_nmm": _finite_vector(
            metadata["moment_at_panel_midplane_nmm"],
            length=3,
            label=f"{case} moment",
        ),
        "stand_off_from_panel_front_mm": float(metadata["standoff_from_front_mm"]),
        "panel_patch_size_mm": float(metadata["panel_patch_size_mm"]),
        "panel_patch_bounds_mm": _finite_vector(
            metadata["panel_patch_mm"], length=4, label=f"{case} patch"
        ),
        "panel_patch_load_type": metadata["panel_patch_load_type"],
        "load_kind": metadata["load_kind"],
        "equipment_mass_kg": float(metadata["equipment_kg"]),
        "modeled_mass_kg": float(metadata["modeled_mass_kg"]),
        "gravity_points": metadata["gravity_points"],
        "hardware_mass_inventory": metadata["hardware_mass_inventory"],
        "leg_floor_grid": metadata["leg_floor_grid"],
        "floor_rail_support": metadata["floor_rail_support"],
        "header_bearing_assumption": metadata["header_bearing_assumption"],
        "dynamic_assumption": {
            "multiplier": 2.0,
            "basis": (
                "Default dynamic_factor=2.0 from "
                "fea.current_response_model.prepare; the signed 300 N horizontal "
                "component is not multiplied."
            ),
        },
        "preparation": preparation,
        "native_solve": False,
        "demands_qualified": False,
    }


def validate_register(register: dict) -> None:
    if register.get("schema") != SCHEMA:
        raise ValueError("Unexpected barrel register schema")
    validate_counts(register.get("counts", {}))
    validate_approved_revisions(register.get("approved_revision_regression", {}))
    stations = register.get("stations", {})
    bolt_names = [name for row in stations.values() for name in row.get("bolts", {})]
    barrel_names = [
        name for row in stations.values() for name in row.get("barrels", {})
    ]
    drilling_paths = [
        name
        for row in stations.values()
        for name in row.get("drilling_path_names", ())
    ]
    access_paths = [
        name
        for row in stations.values()
        for name in row.get("access_path_names", ())
    ]
    fixed = register.get("fixed_features", {})
    internal_counts = {
        "stations": len(stations),
        "barrel_bolts": len(set(bolt_names)),
        "barrels": len(set(barrel_names)),
        "barrel_pairs": sum(
            len(row.get("contact", {}).get("bolt_face_crossings", ()))
            for row in stations.values()
        ),
        "barrel_face_contact_cells": sum(
            len(row.get("contact", {}).get("contact_cells", ()))
            for row in stations.values()
        ),
        "drilling_paths": len(set(drilling_paths)),
        "access_paths": len(set(access_paths)),
        "retained_frame_bolts": len(fixed.get("retained_frame_bolts", {})),
        "fixed_panel_kicker_screws": len(
            fixed.get("fixed_panel_kicker_screws", {})
        ),
        "removed_legacy_structural_sds": len(
            fixed.get("excluded_legacy", {}).get("sds_axes", ())
        ),
    }
    validate_counts(internal_counts)
    if (
        internal_counts != register["counts"]
        or len(bolt_names) != internal_counts["barrel_bolts"]
        or len(barrel_names) != internal_counts["barrels"]
        or len(drilling_paths) != internal_counts["drilling_paths"]
        or len(access_paths) != internal_counts["access_paths"]
        or set(stations)
        != set(register.get("station_identities", ()))
        or len(stations) != 24
        or tuple(register.get("load_case_order", ())) != EXPECTED_CASES
        or set(register.get("load_cases", {})) != set(EXPECTED_CASES)
        or any(row.get("native_solve") is not False for row in register["load_cases"].values())
        or register.get("release") is not False
        or any(register.get("release_flags", {}).values())
    ):
        raise ValueError("Barrel register frozen identity or release state changed")


def build_register() -> dict:
    """Derive one deterministic, source-bound register without solving."""
    repository_commit = _git_commit()
    source_sha256 = _source_hashes()
    if tuple(CASES) != EXPECTED_CASES:
        raise ValueError("Frozen six-case order or identity changed")
    assembly = build_integrated_viewer_assembly()
    inventory = build_inventory(assembly=assembly)
    contacts = contact_report(assembly=assembly)
    revision = revision_report(source=assembly)
    counts = _counts(assembly, inventory, contacts)
    validate_counts(counts)
    validate_approved_revisions(revision)
    if (
        assembly.get("post_placement") != "integrated"
        or inventory.get("release_claimed") is not False
        or contacts.get("native_solve") is not False
        or any(assembly["release_flags"].values())
    ):
        raise ValueError("Integrated candidate source or release state changed")
    stations = _station_records(assembly, inventory, contacts)
    native = IntegratedBarrelNative()
    loads = {case: _load_record(case, native) for case in EXPECTED_CASES}
    panels = sorted(
        name for name in assembly["wood"] if name.startswith(("main_", "kicker_"))
    )
    timbers = sorted(set(assembly["wood"]) - set(panels))
    if len(panels) != 6 or len(timbers) != 20:
        raise ValueError("Integrated timber or panel inventory changed")
    if _git_commit() != repository_commit or _source_hashes() != source_sha256:
        raise ValueError("Register source changed while deriving artifact")
    register = {
        "schema": SCHEMA,
        "status": "frozen_development_input",
        "candidate": "compact-floor-flush-bolted-development",
        "geometry_source": (
            "scripts.export_owner_barrel_scene.build_integrated_viewer_assembly"
        ),
        "repository_commit": repository_commit,
        "source_identity_policy": (
            "Per-file SHA-256 values bind working source content; repository_commit "
            "identifies HEAD and does not claim a clean worktree."
        ),
        "source_sha256": source_sha256,
        "units": {
            "length": "mm",
            "area": "mm^2",
            "volume": "mm^3",
            "force": "N",
            "moment": "N*mm",
            "mass": "kg",
            "stiffness": "N/mm",
            "areal_stiffness": "N/mm^3",
            "weight_request": "lbf",
        },
        "counts": counts,
        "station_identities": sorted(stations),
        "stations": stations,
        "fixed_features": {
            "framing_timber_names": timbers,
            "plywood_panel_names": panels,
            "fixed_panel_kicker_screws": inventory["fixed_panel_screws"],
            "retained_frame_bolts": inventory["retained_frame_bolts"],
            "center_kicker_screw_landings": inventory[
                "center_kicker_screw_landings"
            ],
            "excluded_legacy": inventory["excluded_legacy"],
            "service_passage_option": assembly["service_passage_option"],
        },
        "contact_summary": {
            key: contacts[key]
            for key in (
                "schema",
                "station_count",
                "contact_cell_count",
                "trial_cut_face_count",
                "trial_cut_cell_face_count",
                "adjusted_contact_point_count",
                "bolt_interface_count",
                "contact_law_qualified",
                "native_solve",
                "structural_released",
                "drilling_released",
                "limits",
            )
        },
        "connector_inventory_fingerprint_sha256": inventory[
            "inventory_fingerprint_sha256"
        ],
        "approved_revision_regression": revision,
        "load_case_source": "scripts.clear_space_batch.CASES",
        "load_case_preparation_source": (
            "scripts.owner_barrel_native_preparation.prepare_case"
        ),
        "load_case_order": list(EXPECTED_CASES),
        "load_cases": loads,
        "release": False,
        "release_flags": {
            "geometry_accepted": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
            "diy_ready": False,
        },
        "limits": (
            "BN-0 source freeze only. Provisional barrel geometry, contact cells, "
            "conditional stiffnesses, and prepared loads are not solved demands, "
            "joint resistance, drilling dimensions, fabrication approval, or a "
            "climber rating."
        ),
    }
    validate_register(register)
    return register


def render(register: dict) -> str:
    return json.dumps(register, indent=2, sort_keys=True, allow_nan=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_register()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(result))


if __name__ == "__main__":
    main()
