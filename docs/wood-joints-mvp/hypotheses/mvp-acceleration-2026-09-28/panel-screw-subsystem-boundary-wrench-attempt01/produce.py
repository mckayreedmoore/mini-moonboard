"""Source-bound aggregate boundary wrench for the panel/screw subsystem.

This is a rigid-body equilibrium bookkeeping result. It does not distribute
the wrench among screws, bearing faces, or frame members and is not a solver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "panel-screw-subsystem-boundary-wrench.json"
GRAVITY_M_S2 = 9.80665
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_CASES = {
    "a12-rear",
    "a12-forward",
    "a12-left",
    "k12-right",
    "k12-rear",
    "a1-rear",
}
EXPECTED_GROUP_COUNTS = {
    "plywood panels": 6,
    "hold T-nuts": 142,
    "panel kicker screws": 66,
}
EXPECTED_INPUT_SHA256 = {
    "AGENTS.md": "672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json": "9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json": "4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json": "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b, strict=True)]


def sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b, strict=True)]


def scale(a: list[float], s: float) -> list[float]:
    return [s * x for x in a]


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def close(a: list[float], b: list[float], atol: float) -> bool:
    return all(abs(x - y) <= atol for x, y in zip(a, b, strict=True))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_self_checks() -> None:
    """Check wrench translation and the reaction sign with known answers."""
    point = [20.0, 30.0, 100.0]
    force = [10.0, -5.0, -100.0]
    moment_at_point = [-3.0, 4.0, 7.0]
    origin_moment = add(moment_at_point, cross(point, force))
    # Translating an origin-referenced wrench back to its application point
    # must recover the original moment.
    translated = sub(origin_moment, cross(point, force))
    require(close(translated, moment_at_point, 1e-12), "wrench translation fixture failed")
    external_force = [1.0, -2.0, 3.0]
    external_moment = [-4.0, 5.0, -6.0]
    reaction = [scale(external_force, -1.0), scale(external_moment, -1.0)]
    require(close(add(external_force, reaction[0]), [0.0, 0.0, 0.0], 1e-12),
            "known-answer force closure failed")
    require(close(add(external_moment, reaction[1]), [0.0, 0.0, 0.0], 1e-12),
            "known-answer moment closure failed")


def build_result() -> dict:
    verify_self_checks()
    input_paths = {name: ROOT / name for name in EXPECTED_INPUT_SHA256}
    actual_pins = {name: sha256(path) for name, path in input_paths.items()}
    for name, expected in EXPECTED_INPUT_SHA256.items():
        require(actual_pins[name] == expected, f"pinned source changed: {name}")

    manifest = json.loads(input_paths[
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
    ].read_text())
    load_contract = json.loads(input_paths[
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json"
    ].read_text())
    mass_record = json.loads(input_paths[
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json"
    ].read_text())
    require(manifest["candidate"] == CANDIDATE, "manifest candidate mismatch")
    require(manifest["geometry_revision_id"] == REVISION, "manifest revision mismatch")
    require(load_contract["candidate"] == CANDIDATE, "load-contract candidate mismatch")
    require(load_contract["geometry_revision_id"] == REVISION, "load-contract revision mismatch")
    require(mass_record["revision_id"] == REVISION, "mass-record revision mismatch")

    rows = mass_record["rows"]
    by_group: dict[str, list[dict]] = {}
    for row in rows:
        by_group.setdefault(row["group"], []).append(row)
    selected = {
        group: by_group.get(group, [])
        for group in EXPECTED_GROUP_COUNTS
    }
    observed_counts = {group: len(group_rows) for group, group_rows in selected.items()}
    require(observed_counts == EXPECTED_GROUP_COUNTS,
            f"unexpected component counts: {observed_counts}")
    selected_rows = [row for group_rows in selected.values() for row in group_rows]
    names = [row["name"] for row in selected_rows]
    require(len(set(names)) == len(names), "duplicate component names in selected subsystem")

    total_mass = 0.0
    weighted_center = [0.0, 0.0, 0.0]
    gravity_force = [0.0, 0.0, 0.0]
    gravity_moment_origin = [0.0, 0.0, 0.0]
    for row in selected_rows:
        row_mass = float(row["mass_kg"])
        center = [float(x) for x in row["mass_center_global_xyz_mm"]]
        expected_mass = float(row["volume_mm3"]) * 1e-9 * float(row["density_kg_m3"])
        require(abs(row_mass - expected_mass) <= max(1e-12, abs(row_mass) * 1e-12),
                f"mass/volume/density mismatch: {row['name']}")
        weight = [0.0, 0.0, -row_mass * GRAVITY_M_S2]
        weight_moment = cross(center, weight)
        require(close([float(x) for x in row["gravity_force_global_xyz_n"]], weight, 1e-9),
                f"source gravity force mismatch: {row['name']}")
        require(close([float(x) for x in row["gravity_moment_about_global_origin_nmm"]],
                      weight_moment, 1e-6), f"source gravity moment mismatch: {row['name']}")
        total_mass += row_mass
        weighted_center = add(weighted_center, scale(center, row_mass))
        gravity_force = add(gravity_force, weight)
        gravity_moment_origin = add(gravity_moment_origin, weight_moment)

    group_center = scale(weighted_center, 1.0 / total_mass)
    gravity_moment_at_center = sub(gravity_moment_origin, cross(group_center, gravity_force))
    require(close(gravity_moment_at_center, [0.0, 0.0, 0.0], 1e-5),
            "source-assigned group gravity does not act through its computed centroid")
    require(abs(total_mass - sum(float(row["mass_kg"]) for row in rows
                                 if row["group"] in EXPECTED_GROUP_COUNTS)) <= 1e-12,
            "selected subsystem mass closure failed")

    cases = []
    case_ids: list[str] = []
    for case in load_contract["cases"]:
        case_id = case["case_id"]
        case_ids.append(case_id)
        wrench = case["applied_wrench"]
        force = [float(x) for x in wrench["force_global_xyz_n"]]
        ref = [float(x) for x in wrench["reference_point_global_xyz_mm"]]
        moment_ref = [float(x) for x in wrench["moment_global_xyz_nmm"]]
        panel_ref = [float(x) for x in case["panel_midplane_applicationpoint_global_xyz_mm"]]
        require(close(ref, panel_ref, 1e-9), f"panel reference mismatch: {case_id}")
        require(close(force, [float(x) for x in case["applied_force_global_xyz_n"]], 1e-9),
                f"applied force mismatch: {case_id}")
        require(close(moment_ref,
                      [float(x) for x in case["moment_about_panel_midplane_applicationpoint_global_xyz_nmm"]],
                      1e-6), f"applied moment mismatch: {case_id}")
        force_point = [float(x) for x in case["standoff"]["force_application_point_global_xyz_mm"]]
        moment_from_point = cross(sub(force_point, ref), force)
        require(close(moment_ref, moment_from_point, 1e-6),
                f"standoff wrench does not reconstruct: {case_id}")

        moment_at_center = add(moment_ref, cross(sub(ref, group_center), force))
        external_force = add(force, gravity_force)
        external_moment = add(moment_at_center, gravity_moment_at_center)
        required_reaction_force = scale(external_force, -1.0)
        required_reaction_moment = scale(external_moment, -1.0)
        applied_moment_origin = add(moment_ref, cross(ref, force))
        external_moment_origin = add(applied_moment_origin, gravity_moment_origin)
        reaction_moment_origin = scale(external_moment_origin, -1.0)
        reaction_moment_from_origin = sub(
            reaction_moment_origin,
            cross(group_center, required_reaction_force),
        )
        origin_transform_residual = sub(required_reaction_moment, reaction_moment_from_origin)
        require(close(origin_transform_residual, [0.0, 0.0, 0.0], 1e-6),
                f"independent global-origin moment transform mismatch: {case_id}")
        force_residual = add(external_force, required_reaction_force)
        moment_residual = add(external_moment, required_reaction_moment)
        require(close(force_residual, [0.0, 0.0, 0.0], 1e-9),
                f"force equilibrium residual: {case_id}")
        require(close(moment_residual, [0.0, 0.0, 0.0], 1e-6),
                f"moment equilibrium residual: {case_id}")
        cases.append({
            "case_id": case_id,
            "hold_id": case["hold_id"],
            "applied_climber_force_global_xyz_n": force,
            "applied_climber_moment_about_subsystem_centroid_global_xyz_nmm": moment_at_center,
            "source_assigned_subsystem_gravity_force_global_xyz_n": gravity_force,
            "source_assigned_subsystem_gravity_moment_about_subsystem_centroid_global_xyz_nmm": gravity_moment_at_center,
            "external_wrench_on_subsystem_about_subsystem_centroid": {
                "force_global_xyz_n": external_force,
                "moment_global_xyz_nmm": external_moment,
            },
            "required_reaction_from_remaining_frame_on_subsystem_about_subsystem_centroid": {
                "force_global_xyz_n": required_reaction_force,
                "moment_global_xyz_nmm": required_reaction_moment,
            },
            "independent_global_origin_transform_residual_nmm": origin_transform_residual,
            "equilibrium_residual": {"force_global_xyz_n": force_residual,
                                      "moment_global_xyz_nmm": moment_residual},
        })
    require(set(case_ids) == EXPECTED_CASES and len(case_ids) == len(EXPECTED_CASES),
            f"unexpected six-case set: {case_ids}")

    excluded_groups = {
        group: len(group_rows)
        for group, group_rows in by_group.items()
        if group not in EXPECTED_GROUP_COUNTS
    }
    return {
        "schema": "panel_screw_subsystem_boundary_wrench/v1",
        "status": "PASS_SCOPED_SOURCE_ASSIGNED_AGGREGATE_EQUILIBRIUM",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "source_sha256": {
            **actual_pins,
            str(Path(__file__).resolve().relative_to(ROOT)): sha256(Path(__file__).resolve()),
        },
        "subsystem_definition": {
            "included_source_groups": EXPECTED_GROUP_COUNTS,
            "included_component_count": len(selected_rows),
            "included_mass_kg": total_mass,
            "conditional_center_of_mass_global_xyz_mm": group_center,
            "source_assigned_gravity_force_global_xyz_n": gravity_force,
            "source_assigned_gravity_moment_about_global_origin_global_xyz_nmm": gravity_moment_origin,
            "source_assigned_gravity_moment_about_subsystem_centroid_global_xyz_nmm": gravity_moment_at_center,
            "excluded_mass_centroid_allowance_kg": float(mass_record["equipment_allowance_kg_excluded_from_centroid"]),
            "excluded_source_group_counts": excluded_groups,
        },
        "case_results": cases,
        "assumptions_and_limits": [
            "The subsystem is the six modeled plywood-panel bodies, 142 source-assigned hold T-nuts, and 66 panel/kicker screw-axis mass proxies; it is a bookkeeping cut, not an inspected installed assembly.",
            "The applied climber wrench is the frozen direct-to-panel load; this calculation does not model load transfer through holds or T-nuts.",
            "Panel mass uses the source's conditional 600 kg/m^3 density; T-nut and screw-axis masses use source CAD estimates/proxies.",
            "The separate 25 kg accessory allowance, frame timber, corner blocks, candidate block bolts, and retained frame bolts are excluded from this subsystem result.",
            "The reported reaction is the aggregate resultant required from the remainder of the frame on this selected subsystem under the included loads. It does not allocate force or moment among any screw, bearing face, block, or member.",
            "This does not establish active contact, connection stiffness, load sharing, connection resistance, support reactions, or a closed downstream member path.",
            "This is a rigid-body force and first-moment equilibrium screen only; no mesh or native solve was run, and no acceptance or release flag is changed.",
        ],
        "mechanical_acceptance": False,
        "native_solve_run": False,
        "mesh_generated": False,
    }


def canonical(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the derived JSON record")
    mode.add_argument("--verify", action="store_true", help="recompute and compare without writing")
    args = parser.parse_args()
    result = build_result()
    if args.write:
        OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {OUTPUT.relative_to(ROOT)}")
        return 0
    observed = json.loads(OUTPUT.read_text())
    require(canonical(observed) == canonical(result), "saved result differs from recomputed result")
    print(json.dumps({
        "status": result["status"],
        "included_mass_kg": result["subsystem_definition"]["included_mass_kg"],
        "case_count": len(result["case_results"]),
        "max_force_residual_n": max(max(abs(x) for x in c["equilibrium_residual"]["force_global_xyz_n"])
                                     for c in result["case_results"]),
        "max_moment_residual_nmm": max(max(abs(x) for x in c["equilibrium_residual"]["moment_global_xyz_nmm"])
                                       for c in result["case_results"]),
        "max_independent_origin_transform_residual_nmm": max(
            max(abs(x) for x in c["independent_global_origin_transform_residual_nmm"])
            for c in result["case_results"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
