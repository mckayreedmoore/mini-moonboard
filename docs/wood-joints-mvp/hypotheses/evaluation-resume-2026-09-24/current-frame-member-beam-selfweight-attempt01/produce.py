"""Build source-bound equivalent beam self-weight inputs; never creates a solver deck."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Any

import cadquery as cq
from OCP.Bnd import Bnd_OBB
from OCP.BRepBndLib import BRepBndLib


ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent / "member-beam-selfweight.json"
GRAVITY_M_S2 = 9.80665
SOURCE_PINS = {
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json": "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json": "4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json": "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420",
    "uv.lock": "5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3",
    "pyproject.toml": "84e007ad5c9cfffa853f21627fecbaec0a85c602560d5d5e0b507326e9b02452",
}
EXPECTED_CADQUERY = "2.8.0"
EXPECTED_OCP = "7.9.3.1.1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cross(a: list[float] | tuple[float, ...], b: list[float] | tuple[float, ...]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _dot(a: list[float] | tuple[float, ...], b: list[float] | tuple[float, ...]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def _norm(a: list[float] | tuple[float, ...]) -> float:
    return math.sqrt(_dot(a, a))


def _round_vector(values: list[float] | tuple[float, ...]) -> list[float]:
    return [round(float(value), 12) for value in values]


def _check_oriented_box_fixture() -> dict[str, Any]:
    """Check OBB length/orientation recovery on a rotated analytic box (no mesh)."""
    length_mm, width_mm, height_mm = 1200.0, 140.0, 38.0
    angle = math.radians(31.7)
    shape = cq.Workplane("XY").box(length_mm, width_mm, height_mm).val()
    shape = shape.rotate((0, 0, 0), (0, 0, 1), math.degrees(angle))
    obb = Bnd_OBB()
    BRepBndLib.AddOBB_s(shape.wrapped, obb, False, True, False)
    sizes = [2.0 * obb.XHSize(), 2.0 * obb.YHSize(), 2.0 * obb.ZHSize()]
    directions = [obb.XDirection(), obb.YDirection(), obb.ZDirection()]
    long_index = max(range(3), key=sizes.__getitem__)
    axis = directions[long_index]
    actual_axis = [axis.X(), axis.Y(), axis.Z()]
    expected_axis = [math.cos(angle), math.sin(angle), 0.0]
    if _dot(actual_axis, expected_axis) < 1.0 - 1e-8:
        if _dot([-x for x in actual_axis], expected_axis) < 1.0 - 1e-8:
            raise ValueError("analytic OBB fixture did not recover the rotated long axis")
        actual_axis = [-x for x in actual_axis]
    if not math.isclose(sizes[long_index], length_mm, rel_tol=0, abs_tol=1e-7):
        raise ValueError("analytic OBB fixture length differs")
    other = sorted(size for i, size in enumerate(sizes) if i != long_index)
    if not math.isclose(other[0], height_mm, rel_tol=0, abs_tol=1e-7):
        raise ValueError("analytic OBB fixture short dimension differs")
    if not math.isclose(other[1], width_mm, rel_tol=0, abs_tol=1e-7):
        raise ValueError("analytic OBB fixture middle dimension differs")
    return {
        "geometry": "centered 1200 x 140 x 38 mm box rotated 31.7 degrees about global Z",
        "mesh_generated": False,
        "expected_long_axis_global": _round_vector(expected_axis),
        "recovered_long_axis_global": _round_vector(actual_axis),
        "recovered_obb_dimensions_mm_sorted": _round_vector(sorted(sizes)),
        "checks_passed": True,
        "scope": "CadQuery/OCP oriented-bounding-box extraction only",
    }


def _canonical_axis(direction: list[float]) -> list[float]:
    length = _norm(direction)
    if not math.isfinite(length) or length == 0:
        raise ValueError("OBB long-axis direction is invalid")
    unit = [component / length for component in direction]
    major_component = max(range(3), key=lambda i: abs(unit[i]))
    if unit[major_component] < 0:
        unit = [-component for component in unit]
    return unit


def _load_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    for rel, expected in SOURCE_PINS.items():
        path = ROOT / rel
        if _sha256(path) != expected:
            raise ValueError(f"pinned source changed: {rel}")
    manifest = json.loads((ROOT / next(k for k in SOURCE_PINS if "current-full-frame-input-manifest-attempt04" in k)).read_text())
    masses = json.loads((ROOT / next(k for k in SOURCE_PINS if "current-mass-centroids-attempt01" in k)).read_text())
    bundle = json.loads((ROOT / next(k for k in SOURCE_PINS if "current-full-frame-member-solids-attempt01" in k)).read_text())
    return manifest, masses, bundle


def _build_payload() -> dict[str, Any]:
    cadquery_version = version("cadquery")
    ocp_version = version("cadquery-ocp")
    if cadquery_version != EXPECTED_CADQUERY or ocp_version != EXPECTED_OCP:
        raise ValueError(f"unexpected geometry runtime CadQuery/OCP: {cadquery_version}/{ocp_version}")

    manifest, mass_inventory, bundle = _load_sources()
    if manifest.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("manifest revision differs")
    if mass_inventory.get("revision_id") != manifest["geometry_revision_id"]:
        raise ValueError("mass inventory revision differs")

    physical = {row["member_id"]: row for row in manifest["physical_members"]}
    step_records = {row["member_id"]: row for row in bundle["members"]}
    mass_rows = {
        row["name"]: row for row in mass_inventory["rows"] if row["group"] == "frame timber"
    }
    if len(mass_rows) != 20 or len(set(mass_rows)) != 20:
        raise ValueError("expected 20 unique frame-timber mass rows")

    members: list[dict[str, Any]] = []
    input_root = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01"
    for member_id in sorted(mass_rows):
        if member_id not in physical or member_id not in step_records:
            raise ValueError(f"source identity missing for {member_id}")
        member = physical[member_id]
        step_record = step_records[member_id]
        binding = member["current_finished_step_binding"]
        if member["member_kind"] != "timber" or step_record["member_kind"] != "timber":
            raise ValueError(f"non-timber identity in beam mass rows: {member_id}")
        if binding["file_sha256"] != step_record["step_sha256"]:
            raise ValueError(f"manifest/bundle STEP pins differ for {member_id}")
        step_path = input_root / step_record["step_file"]
        if _sha256(step_path) != binding["file_sha256"]:
            raise ValueError(f"STEP file hash differs for {member_id}")

        source_mass = mass_rows[member_id]
        shape = cq.importers.importStep(str(step_path)).val()
        if len(shape.Solids()) != 1:
            raise ValueError(f"expected one solid for {member_id}")
        volume = float(shape.Volume())
        expected_volume = float(source_mass["volume_mm3"])
        if not math.isclose(volume, expected_volume, rel_tol=1e-10, abs_tol=1e-5):
            raise ValueError(f"solid volume differs from mass inventory for {member_id}")
        source_cg = [float(value) for value in source_mass["mass_center_global_xyz_mm"]]
        cad_cg = list(shape.Center().toTuple())
        if _norm([a - b for a, b in zip(source_cg, cad_cg, strict=True)]) > 1e-5:
            raise ValueError(f"mass-centroid export differs from STEP solid for {member_id}")

        obb = Bnd_OBB()
        BRepBndLib.AddOBB_s(shape.wrapped, obb, False, True, False)
        half_sizes = [float(obb.XHSize()), float(obb.YHSize()), float(obb.ZHSize())]
        directions = [obb.XDirection(), obb.YDirection(), obb.ZDirection()]
        long_index = max(range(3), key=half_sizes.__getitem__)
        length_mm = 2.0 * half_sizes[long_index]
        next_largest_mm = 2.0 * sorted(half_sizes, reverse=True)[1]
        if length_mm <= next_largest_mm:
            raise ValueError(f"long axis is ambiguous for {member_id}")
        direction = directions[long_index]
        axis = _canonical_axis([direction.X(), direction.Y(), direction.Z()])
        obb_center = [float(obb.Center().X()), float(obb.Center().Y()), float(obb.Center().Z())]

        mass = float(source_mass["mass_kg"])
        density = float(source_mass["density_kg_m3"])
        if not math.isclose(mass, volume * density / 1e9, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError(f"mass is inconsistent with pinned volume and density for {member_id}")
        weight_n = mass * GRAVITY_M_S2
        line_load_n_per_mm = -weight_n / length_mm
        force = [0.0, 0.0, -weight_n]
        line_moment = _cross(obb_center, force)
        source_moment = [float(value) for value in source_mass["gravity_moment_about_global_origin_nmm"]]
        correction_couple = [source_moment[i] - line_moment[i] for i in range(3)]
        cg_delta = [source_cg[i] - obb_center[i] for i in range(3)]
        cg_axial_offset = _dot(cg_delta, axis)
        cg_transverse_delta = [cg_delta[i] - cg_axial_offset * axis[i] for i in range(3)]
        sorted_sizes = sorted(2.0 * size for size in half_sizes)

        members.append(
            {
                "member_id": member_id,
                "step_sha256": binding["file_sha256"],
                "volume_mm3": volume,
                "density_kg_m3": density,
                "source_mass_kg": mass,
                "source_center_of_mass_global_xyz_mm": _round_vector(source_cg),
                "obb_centerline_reference_global_xyz_mm": _round_vector(obb_center),
                "obb_dimensions_mm_sorted": _round_vector(sorted_sizes),
                "beam_axis_unit_global": _round_vector(axis),
                "beam_length_mm": length_mm,
                "long_to_second_obb_dimension_ratio": length_mm / next_largest_mm,
                "cg_offset_along_beam_axis_mm": cg_axial_offset,
                "cg_offset_transverse_to_beam_axis_mm": _norm(cg_transverse_delta),
                "uniform_equivalent_line_mass_kg_per_m": mass / (length_mm / 1000.0),
                "uniform_equivalent_global_line_load_n_per_mm": [0.0, 0.0, line_load_n_per_mm],
                "line_load_resultant_global_xyz_n": _round_vector(force),
                "line_load_resultant_moment_about_global_origin_nmm": _round_vector(line_moment),
                "source_gravity_moment_about_global_origin_nmm": _round_vector(source_moment),
                "first_moment_correction_couple_nmm": _round_vector(correction_couple),
                "total_equivalent_gravity_wrench_matches_source": True,
            }
        )

    total_mass = math.fsum(row["source_mass_kg"] for row in members)
    total_force = [0.0, 0.0, -total_mass * GRAVITY_M_S2]
    total_source_moment = [
        math.fsum(float(mass_rows[row["member_id"]]["gravity_moment_about_global_origin_nmm"][i]) for row in members)
        for i in range(3)
    ]
    total_represented_moment = [
        math.fsum(row["line_load_resultant_moment_about_global_origin_nmm"][i]
                  + row["first_moment_correction_couple_nmm"][i] for row in members)
        for i in range(3)
    ]
    force_total_from_source = [
        math.fsum(float(mass_rows[row["member_id"]]["gravity_force_global_xyz_n"][i]) for row in members)
        for i in range(3)
    ]
    if any(abs(a - b) > 1e-8 for a, b in zip(total_force, force_total_from_source, strict=True)):
        raise ValueError("20-member line-load resultants do not conserve source gravity force")
    if any(abs(a - b) > 1e-7 for a, b in zip(total_represented_moment, total_source_moment, strict=True)):
        raise ValueError("20-member line-load correction couples do not conserve source first moment")

    return {
        "schema": "current_frame_member_beam_selfweight_equivalent_inputs/v1",
        "status": "SOURCE_BOUND_BEAM_SELFWEIGHT_EQUIVALENT_INPUTS_NOT_SOLVER_MAPPING",
        "revision_id": manifest["geometry_revision_id"],
        "gravity_m_s2": GRAVITY_M_S2,
        "member_count": len(members),
        "included_inventory_group": "frame timber",
        "members": members,
        "aggregate": {
            "source_mass_kg": total_mass,
            "source_gravity_force_global_xyz_n": _round_vector(total_force),
            "source_gravity_moment_about_global_origin_nmm": _round_vector(total_source_moment),
            "equivalent_line_load_plus_correction_moment_nmm": _round_vector(total_represented_moment),
            "line_load_moment_residual_nmm": _round_vector(
                [total_represented_moment[i] - total_source_moment[i] for i in range(3)]
            ),
            "max_abs_member_correction_couple_nmm": max(
                _norm(row["first_moment_correction_couple_nmm"]) for row in members
            ),
        },
        "obb_method": {
            "kernel_api": "OCP.BRepBndLib.AddOBB_s",
            "arguments": {
                "use_triangulation": False,
                "is_optimal": True,
                "use_shape_tolerance": False,
            },
            "runtime": {
                "python": sys.version.split()[0],
                "cadquery": cadquery_version,
                "cadquery_ocp": ocp_version,
            },
            "known_answer_fixture": _check_oriented_box_fixture(),
        },
        "source_sha256": {rel: expected for rel, expected in SOURCE_PINS.items()},
        "limits": [
            "Only the 20 frame-timber body masses are included. Panels, 24 blocks, hardware, and the separate 25 kg accessory allowance need their own mechanical mass/load transfer.",
            "Each line load uses the exact modeled body mass spread uniformly over its OBB long-axis length. This is an equivalent beam representation, not the exact local axial mass distribution around holes, notches, or other geometry details.",
            "A concentrated couple at the OBB centerline reference preserves each source body's exact gravity first moment together with the uniform line-load resultant; it does not reproduce local mass-distribution detail.",
            "The OBB axis is a geometry-derived beam-axis proposal. It is not a solver element or DOF mapping; no material axes, support, connection law, load case, mesh, or solver deck is assigned.",
            "Masses are modeled inventory estimates, not measured delivered-member masses. The source density and geometry assumptions remain.",
            "This file provides common self-weight inputs to combine with cases; it contains no six-case structural response, reactions, demands, capacity checks, or acceptance.",
        ],
        "solver_load_mapping_ready": False,
        "native_solver_run": False,
        "mechanical_acceptance": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--destination", type=Path, default=OUT)
    args = parser.parse_args()
    destination = args.destination if args.destination.is_absolute() else ROOT / args.destination
    payload = _build_payload()
    if args.write:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
        print(f"wrote {destination.relative_to(ROOT)}")
    else:
        observed = json.loads(destination.read_text(encoding="utf-8"))
        if observed != payload:
            raise ValueError("frozen beam self-weight artifact differs from regenerated source payload")
        print(
            "PASS: 20 timber rows, source STEP/mass pins, OBB known answer, "
            "and gravity force/first-moment checks"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
