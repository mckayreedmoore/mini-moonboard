"""Read-only slope and stock/runout rebind against the current leg STEP BReps."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cadquery as cq


ROOT = Path(__file__).resolve().parents[5]
OUT_DIR = Path(__file__).resolve().parent
REPORT = OUT_DIR / "taper-geometry-rebind.json"
BASE = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
MANIFESTS = {
    "attempt03": BASE / "current-full-frame-input-manifest-attempt03/current-full-frame-input-manifest.json",
    "attempt04": BASE / "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json",
}
BUNDLE = BASE / "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json"
TAPER_REFERENCE = Path("docs/floor-flush-construction-kerf-right/leg-taper-geometry.json")
CONSTRUCTION_MANIFEST = Path("docs/floor-flush-construction-kerf-right/manifest.json")
CRITERIA = Path("docs/wood-joints-mvp/criteria.json")
COVERAGE = Path("docs/wood-joints-mvp/current-criteria-coverage.json")
METHOD_MAP = Path("docs/wood-joints-mvp/criteria-method-map.md")
SOURCE_CRITERIA = Path("docs/floor-runner-mvp-criteria.md")
PREDICATE_SOURCE = Path("scripts/floor_taper_checks.py")
SOLIDS_DIR = BASE / "current-full-frame-member-solids-attempt01"
MEMBERS = ("lumber_leg_left", "lumber_leg_right")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with (ROOT / path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def pin(path: Path) -> dict[str, Any]:
    return {"path": path.as_posix(), "file_sha256": sha256(path)}


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def f12(value: float) -> float:
    return round(float(value), 12)


def extent(points: list[tuple[float, float, float]], axis: tuple[float, float, float]) -> list[float]:
    values = [dot(p, axis) for p in points]
    return [min(values), max(values)]


def unique_face_points(face: cq.Face) -> list[tuple[float, float, float]]:
    return sorted({(round(v.X, 9), round(v.Y, 9), round(v.Z, 9)) for v in face.Vertices()})


def canonical_manifest_digest(value: dict[str, Any], *, carried_digest: str | None = None) -> str:
    payload = dict(value)
    stored = payload.pop("manifest_sha256", None)
    if carried_digest is not None:
        # Attempt04 was built from a deep copy of attempt03 and overwrote the
        # carried digest only after hashing the refreshed record.
        payload["manifest_sha256"] = carried_digest
    actual = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    if stored != actual:
        raise ValueError("current full-frame manifest canonical digest mismatch")
    return actual


def audit_leg(
    member_id: str,
    binding03: dict[str, Any],
    binding04: dict[str, Any],
    bundle_row: dict[str, Any],
    reference: dict[str, Any],
) -> dict[str, Any]:
    if binding03 != binding04:
        raise ValueError(f"attempt03/04 current STEP binding differs for {member_id}")
    if binding03["member_kind"] != "timber" or not binding03["one_solid_valid_roundtrip"]:
        raise ValueError(f"unexpected member kind or STEP roundtrip for {member_id}")
    step_path = Path(binding03["path"])
    expected_path = SOLIDS_DIR / "bundle/members" / f"{member_id}.step"
    if step_path != expected_path or sha256(step_path) != binding03["file_sha256"]:
        raise ValueError(f"current member STEP path/hash mismatch for {member_id}")
    if step_path.stat().st_size != binding03["size_bytes"]:
        raise ValueError(f"current member STEP size mismatch for {member_id}")
    if bundle_row["step_sha256"] != binding03["file_sha256"]:
        raise ValueError(f"bundle and current manifests disagree for {member_id}")

    shape = cq.importers.importStep(str(ROOT / step_path)).val()
    if len(shape.Solids()) != 1 or not shape.isValid():
        raise ValueError(f"current STEP is not one valid solid for {member_id}")

    grain = tuple(float(x) for x in reference["grain_axis_xyz"])
    across = tuple(float(x) for x in reference["normal_axis_xyz"])
    x_axis = (1.0, 0.0, 0.0)
    if not math.isclose(dot(grain, grain), 1.0, abs_tol=1e-10):
        raise ValueError(f"non-unit grain projection axis for {member_id}")
    if not math.isclose(dot(across, across), 1.0, abs_tol=1e-10) or abs(dot(grain, across)) > 1e-10:
        raise ValueError(f"invalid section projection axes for {member_id}")

    vertices = [(float(v.X), float(v.Y), float(v.Z)) for v in shape.Vertices()]
    stock_x = extent(vertices, x_axis)
    stock_across = extent(vertices, across)
    stock_grain = extent(vertices, grain)

    # Find the unique actual planar cut face using its three orthogonal spans.
    matches: list[tuple[cq.Face, list[tuple[float, float, float]]]] = []
    for face in shape.Faces():
        if face.geomType() != "PLANE":
            continue
        points = unique_face_points(face)
        if len(points) != 4:
            continue
        sx = extent(points, x_axis)
        sa = extent(points, across)
        sg = extent(points, grain)
        if (
            math.isclose(sx[1] - sx[0], 38.1, abs_tol=1e-5)
            and math.isclose(sa[1] - sa[0], 139.7, abs_tol=1e-5)
            and math.isclose(sg[1] - sg[0], 457.2, abs_tol=1e-5)
        ):
            matches.append((face, points))
    if len(matches) != 1:
        raise ValueError(f"expected one complete taper plane for {member_id}; found {len(matches)}")

    face, points = matches[0]
    stations = sorted((dot(p, grain), p) for p in points)
    start = stations[0][0]
    end = stations[-1][0]
    start_points = [p for s, p in stations if abs(s - start) <= 1e-5]
    end_points = [p for s, p in stations if abs(s - end) <= 1e-5]
    if len(start_points) != 2 or len(end_points) != 2:
        raise ValueError(f"taper face start/end edges do not resolve for {member_id}")
    depth = abs(sum(p[0] for p in end_points) / 2 - sum(p[0] for p in start_points) / 2)
    run = end - start
    ratio = run / depth
    normal = face.normalAt()
    reference_start = float(reference["taper_start_station_mm"])
    reference_end = float(reference["taper_end_station_mm"])
    if not (math.isclose(start, reference_start, abs_tol=1e-5) and math.isclose(end, reference_end, abs_tol=1e-5)):
        raise ValueError(f"current STEP and documented runout stations disagree for {member_id}")

    slope_pass = run >= 10 * depth - 1e-6
    stock_runout_pass = (
        math.isclose(stock_x[1] - stock_x[0], 88.9, abs_tol=1e-5)
        and math.isclose(stock_across[1] - stock_across[0], 139.7, abs_tol=1e-5)
        and math.isclose(depth, 38.1, abs_tol=1e-5)
        and run >= 457.2 - 1e-5
    )
    if not slope_pass or not stock_runout_pass:
        raise ValueError(f"current STEP fails a taper geometry predicate for {member_id}")

    bounds = shape.BoundingBox()
    return {
        "member_id": member_id,
        "step": {
            "path": step_path.as_posix(),
            "sha256": binding03["file_sha256"],
            "size_bytes": binding03["size_bytes"],
            "source_shape_fingerprint_sha256": binding03["source_shape_fingerprint_sha256"],
            "shape_summary_sha256": binding03["shape_summary_sha256"],
            "bundle_source_part_record_sha256": bundle_row["source_part_record_sha256"],
            "bundle_geometry_source": bundle_row["geometry_source"],
            "one_solid_valid_roundtrip": True,
        },
        "measured_solid": {
            "solid_count": len(shape.Solids()),
            "face_count": len(shape.Faces()),
            "volume_mm3": f12(shape.Volume()),
            "bounds_xyz_mm": [f12(x) for x in (bounds.xmin, bounds.xmax, bounds.ymin, bounds.ymax, bounds.zmin, bounds.zmax)],
            "projection_axes": {
                "leg_axis_g_xyz": [f12(x) for x in grain],
                "stock_section_axis_n_xyz": [f12(x) for x in across],
                "cross_section_axis_x_xyz": [1.0, 0.0, 0.0],
                "method": "For each STEP vertex p, project s=p dot g and n=p dot N in global mm coordinates; take max-minus-min. Taper run is end-start in s; removed depth is the difference between the two taper-face x edge means.",
            },
            "stock_extents_mm": {
                "x_interval": [f12(x) for x in stock_x],
                "normal_interval": [f12(x) for x in stock_across],
                "grain_interval": [f12(x) for x in stock_grain],
                "cross_section_x_width": f12(stock_x[1] - stock_x[0]),
                "cross_section_normal_depth": f12(stock_across[1] - stock_across[0]),
            },
        },
        "taper_face": {
            "selection": "unique planar four-vertex face with STEP spans 38.1 mm in x, 139.7 mm in N, and 457.2 mm in g",
            "area_mm2": f12(face.Area()),
            "unit_normal_xyz": [f12(normal.x), f12(normal.y), f12(normal.z)],
            "vertices_xyz_mm": [[f12(x) for x in p] for p in points],
            "start_edge_vertices_xyz_mm": [[f12(x) for x in p] for p in start_points],
            "end_edge_vertices_xyz_mm": [[f12(x) for x in p] for p in end_points],
            "start_grain_station_mm": f12(start),
            "end_grain_station_mm": f12(end),
            "run_mm": f12(run),
            "maximum_removed_depth_mm": f12(depth),
            "run_to_depth_ratio": f12(ratio),
            "slope_angle_deg": f12(math.degrees(math.atan(depth / run))),
            "minimum_run_for_1_to_10_mm": f12(10 * depth),
            "margin_over_1_to_10_mm": f12(run - 10 * depth),
            "exact_existing_slope_predicate_pass": slope_pass,
            "exact_existing_stock_runout_predicate_pass": stock_runout_pass,
        },
    }


def build_report() -> dict[str, Any]:
    manifests = {name: read_json(path) for name, path in MANIFESTS.items()}
    attempt03_digest = canonical_manifest_digest(manifests["attempt03"])
    canonical_manifest_digest(manifests["attempt04"], carried_digest=attempt03_digest)
    for name, manifest in manifests.items():
        if manifest["candidate"] != "compact-floor-flush-wood-joints-development" or manifest["geometry_revision_id"] != "led-clearance-2x6-runner-seated-blocks-v1":
            raise ValueError(f"unexpected candidate/revision in {name}")
        if manifest["selected_candidate_authority_preserved"] != "compact-floor-flush-development":
            raise ValueError(f"selected authority changed in {name}")

    bundle = read_json(BUNDLE)
    if bundle["readiness"]["native_solve_executed"] is not False:
        raise ValueError("STEP bundle no longer states no native solve")
    if manifests["attempt03"]["readiness"]["inputs_ready"] is not False or manifests["attempt03"]["readiness"]["native_solve_executed"] is not False:
        raise ValueError("current-frame manifest scope unexpectedly changed")
    step_maps = {
        name: {row["member_id"]: row for row in manifest["finished_member_step_bindings"]}
        for name, manifest in manifests.items()
    }
    if len(step_maps["attempt03"]) != 50 or len(step_maps["attempt04"]) != 50:
        raise ValueError("current full-frame manifest does not contain 50 exact member bindings")
    if any(step_maps["attempt03"].get(member) != step_maps["attempt04"].get(member) for member in MEMBERS):
        raise ValueError("attempt04 changed a current taper leg STEP binding")
    bundle_binding = manifests["attempt03"]["evidence_bindings"]["finished_member_geometry"]
    if bundle_binding["path"] != BUNDLE.as_posix() or bundle_binding["file_sha256"] != sha256(BUNDLE):
        raise ValueError("attempt03 does not pin the current STEP bundle")
    taper_reference = read_json(TAPER_REFERENCE)
    construction = read_json(CONSTRUCTION_MANIFEST)
    if construction["artifact_sha256"].get(TAPER_REFERENCE.name) != sha256(TAPER_REFERENCE):
        raise ValueError("construction packet does not pin taper reference")
    bundle_rows = {row["member_id"]: row for row in bundle["members"]}

    leg_rows = [
        audit_leg(member, step_maps["attempt03"][member], step_maps["attempt04"][member], bundle_rows[member], taper_reference[member])
        for member in MEMBERS
    ]
    pass_both = all(
        row["taper_face"]["exact_existing_slope_predicate_pass"]
        and row["taper_face"]["exact_existing_stock_runout_predicate_pass"]
        for row in leg_rows
    )
    right_ref_x = taper_reference["lumber_leg_right"]["raw_bounds_xyz_mm"][0]
    right_now_x = leg_rows[1]["measured_solid"]["bounds_xyz_mm"][:2]
    right_translation = [right_now_x[i] - right_ref_x[i] for i in (0, 1)]
    coverage = read_json(COVERAGE)
    return {
        "schema": "wood_joint_current_taper_geometry_rebind/v1",
        "date": "2026-09-27",
        "scope": "Read-only measurement of current source-bound leg STEP solids for the two static taper geometry predicates. No CAD rebuild, export, mesh, native solve, physical inspection, criteria edit, or acceptance transfer.",
        "candidate_identity": {
            "candidate": manifests["attempt04"]["candidate"],
            "geometry_revision_id": manifests["attempt04"]["geometry_revision_id"],
            "reviewed_repository_checkpoint": manifests["attempt04"]["reviewed_repository_commit"],
            "selected_candidate_authority_preserved": manifests["attempt04"]["selected_candidate_authority_preserved"],
            "manifest_attempt03_canonical_sha256": manifests["attempt03"]["manifest_sha256"],
            "manifest_attempt04_canonical_sha256": manifests["attempt04"]["manifest_sha256"],
            "manifest_attempt03_file_sha256": sha256(MANIFESTS["attempt03"]),
            "manifest_attempt04_file_sha256": sha256(MANIFESTS["attempt04"]),
            "both_manifests_bind_same_leg_step_hashes": True,
            "bundle_path": BUNDLE.as_posix(),
            "bundle_file_sha256": sha256(BUNDLE),
            "bundle_content_sha256": bundle["artifact_sha256"],
            "member_bundle_sha256": bundle["member_bundle_sha256"],
            "manifest04_preservation_review": "Parent independently confirmed attempt04 preserves attempt03's geometry objects and STEP hashes; this artifact checks both leg bindings directly and does not rerun the manifest producer.",
        },
        "method_and_source_pins": {
            "projection": "Read the existing STEP BRep with CadQuery/OCP; for each vertex p in mm, compute s=p·g along the reported leg axis and n=p·N across the 4x6 depth. Identify the unique planar face with spans 38.1 mm in x, 139.7 mm in N and 457.2 mm in g. Determine taper run from its endpoint-edge station difference and recess depth from the endpoint-edge x displacement.",
            "taper_predicate_source": {**pin(PREDICATE_SOURCE), "line_references": [116, 117, 118]},
            "source_criteria": {**pin(SOURCE_CRITERIA), "criteria_rows": {"taper_taper_at_least_one_in_ten": 76, "taper_intended_stock_and_runout": 77}},
            "current_method_map": {**pin(METHOD_MAP), "criteria_rows": {"taper_taper_at_least_one_in_ten": 81, "taper_intended_stock_and_runout": 82}},
            "criteria_register": pin(CRITERIA),
            "current_coverage_plan": pin(COVERAGE),
            "taper_geometry_reference": pin(TAPER_REFERENCE),
            "construction_manifest": pin(CONSTRUCTION_MANIFEST),
        },
        "exact_predicates": {
            "taper_taper_at_least_one_in_ten": {
                "predicate": "run_mm >= 10 * removed_depth_mm - 1e-6",
                "current_geometry_result": "PASS" if pass_both else "FAIL",
                "members_passed": [row["member_id"] for row in leg_rows if row["taper_face"]["exact_existing_slope_predicate_pass"]],
                "whole_frozen_criterion_disposition": "PENDING fresh-case stage; the current static candidate geometry predicate itself is proved.",
            },
            "taper_intended_stock_and_runout": {
                "predicate": "abs(width_mm-88.9)<=1e-5; abs(depth_mm-139.7)<=1e-5; abs(removed_depth_mm-38.1)<=1e-5; run_mm >= 457.2-1e-5",
                "current_geometry_result": "PASS" if pass_both else "FAIL",
                "members_passed": [row["member_id"] for row in leg_rows if row["taper_face"]["exact_existing_stock_runout_predicate_pass"]],
                "whole_frozen_criterion_disposition": "PENDING fresh-case stage; the current static candidate geometry predicate itself is proved. Modeled intended stock only, not delivered stock/inspection.",
            },
        },
        "members": leg_rows,
        "reference_position_comparison": {
            "older_taper_reference_right_leg_x_bounds_mm": [f12(x) for x in right_ref_x],
            "current_right_step_x_bounds_mm": [f12(x) for x in right_now_x],
            "current_minus_reference_global_x_translation_mm": [f12(x) for x in right_translation],
            "interpretation": "The right current STEP is translated -3.175 mm in global X from the older kerf-right taper geometry artifact. Its measured stock spans, taper endpoints in leg-axis station, recess depth, and predicates match. Current STEP coordinates govern this rebind; this is not a native-to-CAD identity result.",
        },
        "limits": [
            "This rebind is specific to the unaccepted current wood-joints design-review geometry; it does not transfer acceptance from the selected candidate or historical cases.",
            "The source criteria table labels both rows FR-3 and fresh case. No fresh native case exists for this candidate, so this audit proves only their complete static geometry predicates and leaves full frozen-row disposition pending.",
            "The right-leg translation is recorded as a separate geometry fact; no fit/load consequence is inferred here.",
            "No material/grain condition, delivered stock, physical cut, taper section samples, solver-native representation, mesh-volume result, resistance, or complete-frame criterion is established.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    report = build_report()
    content = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write:
        REPORT.write_text(content, encoding="utf-8")
        print(json.dumps({"status": "written", "path": REPORT.relative_to(ROOT).as_posix(), "sha256": sha256(REPORT)}, indent=2))
    elif args.verify:
        if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != content:
            raise SystemExit("stored taper rebind is stale; inspect inputs before updating")
        print(json.dumps({"status": "verified", "path": REPORT.relative_to(ROOT).as_posix(), "sha256": sha256(REPORT)}, indent=2))
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
