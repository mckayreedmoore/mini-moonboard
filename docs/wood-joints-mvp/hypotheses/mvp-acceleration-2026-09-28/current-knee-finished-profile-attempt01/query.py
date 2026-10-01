#!/usr/bin/env python3
"""Read-only finished STEP profile rays for the two BG001 outer-left knee bolts."""
import hashlib
import json
import math
from pathlib import Path
import sys

import cadquery as cq
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
from OCP.gce import gce_MakeLin
from OCP.gp import gp_Dir, gp_Pnt

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
from mini_moonboard.connection_geometry import material_intervals


ACCEL_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/bolt-groups/bolt-groups.json"
)
MEMBER_GEOMETRY_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/member-geometry.json"
)
MANIFEST_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
)
HELPER_REL = Path("mini_moonboard/connection_geometry.py")
EXPECTED_HELPER_SHA = "f729bc64e7ea7fb9df9308411df07e02f98fc309efcf26038809a9e7bd4bc4a4"
TARGET_AXES = ("knee_outer_left_post_1", "knee_outer_left_post_2")
TARGET_MEMBERS = ("base_post_outer_left", "knee_outer_left_spine")
GEOM_TOL = 1e-7
FACE_TOL = 2e-4
MATCH_TOL = 2e-4
AXIAL_INSET = 0.01


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    if n == 0:
        raise ValueError("zero vector")
    return tuple(x / n for x in v)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def add(p, a, scale):
    return tuple(p[i] + a[i] * scale for i in range(3))


def clean(value):
    if isinstance(value, float):
        return round(value, 9)
    if isinstance(value, (tuple, list)):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    return value


def bbox_ray_limit(shape, origin, direction):
    b = shape.BoundingBox()
    corners = [
        (x, y, z)
        for x in (b.xmin, b.xmax)
        for y in (b.ymin, b.ymax)
        for z in (b.zmin, b.zmax)
    ]
    return max(dot(tuple(c[i] - origin[i] for i in range(3)), direction) for c in corners) + 5.0


def finite_face_hits(shape, origin, direction, limit):
    """Return exact intersections with trimmed faces, including their normals."""
    line = gce_MakeLin(gp_Pnt(*origin), gp_Dir(*direction)).Value()
    iterator = BRepIntCurveSurface_Inter()
    iterator.Init(shape.wrapped, line, FACE_TOL)
    faces = shape.Faces()
    hits = []
    while iterator.More():
        point = iterator.Pnt()
        xyz = (point.X(), point.Y(), point.Z())
        t = dot(tuple(xyz[i] - origin[i] for i in range(3)), direction)
        if -MATCH_TOL <= t <= limit + MATCH_TOL:
            raw_face = iterator.Face()
            index = next(
                (i for i, face in enumerate(faces, 1) if face.wrapped.IsSame(raw_face)),
                None,
            )
            row = {"t_mm": t, "point_global_xyz_mm": xyz, "face_index_1based": index}
            if index is not None:
                face = faces[index - 1]
                row.update(
                    surface_type=face.geomType(),
                    face_area_mm2=face.Area(),
                    face_center_global_xyz_mm=face.Center().toTuple(),
                )
                try:
                    normal = face.normalAt(cq.Vector(*xyz)).toTuple()
                    row.update(
                        normal_at_hit_global_xyz=normal,
                        abs_normal_dot_ray=abs(dot(normal, direction)),
                    )
                except Exception as error:  # pragma: no cover - recorded as query evidence
                    row["normal_error"] = type(error).__name__
            hits.append(row)
        iterator.Next()
    return sorted(hits, key=lambda hit: hit["t_mm"])


def load_and_validate_inputs():
    accel_path = ROOT / ACCEL_REL
    member_geometry_path = ROOT / MEMBER_GEOMETRY_REL
    manifest_path = ROOT / MANIFEST_REL
    helper_path = ROOT / HELPER_REL
    accel_sha = sha256(accel_path)
    member_geometry_sha = sha256(member_geometry_path)
    manifest_file_sha = sha256(manifest_path)
    helper_sha = sha256(helper_path)
    if helper_sha != EXPECTED_HELPER_SHA:
        raise RuntimeError("connection_geometry.py changed; review the pinned method before querying")

    accel = json.loads(accel_path.read_text())
    member_geometry = json.loads(member_geometry_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    if accel["geometry_revision_id"] != member_geometry["geometry_revision_id"]:
        raise RuntimeError("bolt-groups/member-geometry revision mismatch")
    if member_geometry["inputs"]["manifest"]["sha256"] != manifest_file_sha:
        raise RuntimeError("member-geometry manifest pin mismatch")
    if accel["source_pins"][MANIFEST_REL.as_posix()]["sha256"] != manifest_file_sha:
        raise RuntimeError("bolt-groups manifest source pin mismatch")
    if accel["source_sha256_observed"][MANIFEST_REL.as_posix()] != manifest_file_sha:
        raise RuntimeError("bolt-groups observed manifest hash mismatch")
    for source_path, pin in accel["source_pins"].items():
        actual = sha256(ROOT / source_path)
        if actual != pin["sha256"] or actual != accel["source_sha256_observed"][source_path]:
            raise RuntimeError(f"bolt-groups nested source pin mismatch: {source_path}")

    acceleration_axes = {
        row["axis_id"]: row
        for row in accel["candidate_axes"]
        if row["axis_id"] in TARGET_AXES
    }
    manifest_axes = {
        row["axis_id"]: row
        for row in manifest["candidate_bolt_axes"]
        if row["axis_id"] in TARGET_AXES
    }
    if set(acceleration_axes) != set(TARGET_AXES) or set(manifest_axes) != set(TARGET_AXES):
        raise RuntimeError("one or more target bolts are absent from pinned inputs")

    geometry_members = {row["member_id"]: row for row in member_geometry["members"]}
    manifest_members = {
        row["member_id"]: row for row in manifest["finished_member_step_bindings"]
    }
    if not set(TARGET_MEMBERS).issubset(geometry_members):
        raise RuntimeError("target member missing from reduced-static member geometry")
    if not set(TARGET_MEMBERS).issubset(manifest_members):
        raise RuntimeError("target member missing from attempt04 finished STEP bindings")

    shapes = {}
    step_pins = {}
    for member_id in TARGET_MEMBERS:
        geometry = geometry_members[member_id]
        binding = manifest_members[member_id]
        if geometry["step_path"] != binding["path"]:
            raise RuntimeError(f"member geometry/manifest STEP path mismatch: {member_id}")
        if geometry["step_sha256"] != binding["file_sha256"]:
            raise RuntimeError(f"member geometry/manifest STEP hash mismatch: {member_id}")
        step_rel = Path(binding["path"])
        step_path = ROOT / step_rel
        step_sha = sha256(step_path)
        if step_sha != binding["file_sha256"]:
            raise RuntimeError(f"attempt04 STEP file hash mismatch: {member_id}")
        if member_geometry["inputs"]["member_step_file_sha256"].get(step_rel.as_posix()) != step_sha:
            raise RuntimeError(f"reduced-static STEP pin mismatch: {member_id}")
        shape = cq.importers.importStep(str(step_path)).val()
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise RuntimeError(f"invalid or non-single-solid finished STEP: {member_id}")
        shapes[member_id] = shape
        step_pins[step_rel.as_posix()] = step_sha

    for axis_id in TARGET_AXES:
        accel_axis = acceleration_axes[axis_id]
        manifest_axis = manifest_axes[axis_id]
        if accel_axis["group_id"] != "BG001" or accel_axis["receiver_member_ids"] != [
            "base_post_outer_left",
            "knee_outer_left_spine",
        ]:
            raise RuntimeError(f"unexpected BG001 membership/order: {axis_id}")
        g = manifest_axis["geometry"]
        if g["axis_head_to_nut_global"] != accel_axis["axis_head_to_nut_unit_global_xyz"]:
            raise RuntimeError(f"acceleration/attempt04 axis mismatch: {axis_id}")
        if g["shaft_center_global_xyz_mm"] != accel_axis["shaft_center_global_xyz_mm"]:
            raise RuntimeError(f"acceleration/attempt04 shaft-center mismatch: {axis_id}")
        if g["modeled_underhead_to_tip_mm"] != accel_axis["modeled_underhead_to_tip_mm"]:
            raise RuntimeError(f"acceleration/attempt04 modeled-length mismatch: {axis_id}")
        manifest_intervals = {
            item["receiver_id"]: item["current_shaft_intersection_solid_intervals_from_underhead_mm"]
            for item in g["wood_receiver_intervals"]
        }
        proposed = accel_axis["geometric_receiver_order_proposal"][
            "receiver_intervals_from_underhead_mm"
        ]
        for member_id in TARGET_MEMBERS:
            if manifest_intervals[member_id] != [proposed[member_id]]:
                raise RuntimeError(f"acceleration/attempt04 receiver interval mismatch: {axis_id}/{member_id}")

    return {
        "accel": accel,
        "member_geometry": member_geometry,
        "manifest": manifest,
        "acceleration_axes": acceleration_axes,
        "manifest_axes": manifest_axes,
        "geometry_members": geometry_members,
        "shapes": shapes,
        "source_pins": {
            ACCEL_REL.as_posix(): accel_sha,
            MEMBER_GEOMETRY_REL.as_posix(): member_geometry_sha,
            MANIFEST_REL.as_posix(): manifest_file_sha,
            "manifest_embedded_manifest_sha256": manifest["manifest_sha256"],
            HELPER_REL.as_posix(): helper_sha,
            **step_pins,
        },
    }


inputs = load_and_validate_inputs()
axes = inputs["acceleration_axes"]
members = inputs["geometry_members"]
shapes = inputs["shapes"]
rays = []

for axis_id in TARGET_AXES:
    bolt = axes[axis_id]
    manifest_bolt = inputs["manifest_axes"][axis_id]
    axis = unit(tuple(bolt["axis_head_to_nut_unit_global_xyz"]))
    center = tuple(bolt["shaft_center_global_xyz_mm"])
    underhead_to_tip = bolt["modeled_underhead_to_tip_mm"]
    underhead_datum = add(center, axis, -underhead_to_tip / 2.0)
    e_map = bolt["geometric_receiver_order_proposal"]["receiver_intervals_from_underhead_mm"]

    for member_id in TARGET_MEMBERS:
        member = members[member_id]
        grain = unit(tuple(member["grain_global_xyz"]))
        if abs(dot(grain, axis)) > 1e-6:
            raise RuntimeError(f"grain/bolt axes not orthogonal: {axis_id}/{member_id}")
        e = unit(cross(grain, axis))
        interval = e_map[member_id]
        lo, hi = interval
        if hi - lo <= 2 * AXIAL_INSET:
            raise RuntimeError(f"receiver too thin for 0.01-mm endpoint and middepth probes: {axis_id}/{member_id}")

        # The receiver projection is anchored at the modeled underhead datum.
        # Confirm its two limits agree with the exact STEP solid's bolt-axis
        # projection before placing the profile rays.
        shape = shapes[member_id]
        vertices = [v.Center().toTuple() for v in shape.Vertices()]
        projected = [dot(tuple(p[i] - underhead_datum[i] for i in range(3)), axis) for p in vertices]
        proj_lo, proj_hi = min(projected), max(projected)
        if max(abs(proj_lo - lo), abs(proj_hi - hi)) > 5e-4:
            raise RuntimeError(
                f"receiver interval/finished STEP projection mismatch: {axis_id}/{member_id}; "
                f"pin=[{lo}, {hi}], STEP=[{proj_lo}, {proj_hi}]"
            )

        stations = (
            ("near_headward", lo + AXIAL_INSET),
            ("mid_depth", (lo + hi) / 2.0),
            ("near_nutward", hi - AXIAL_INSET),
        )
        for station_name, axial_t in stations:
            origin = add(underhead_datum, axis, axial_t)
            for basis_label, basis in (("g", grain), ("e", e)):
                for sign, suffix in ((-1.0, "-"), (1.0, "+")):
                    direction = tuple(sign * value for value in basis)
                    limit = bbox_ray_limit(shape, origin, direction)
                    intervals = material_intervals(
                        shape, origin, direction, 0.0, limit, tolerance=GEOM_TOL
                    )
                    hits = finite_face_hits(shape, origin, direction, limit)
                    gaps = []
                    last = 0.0
                    for start, end in intervals:
                        if start > last + MATCH_TOL:
                            gaps.append([last, start])
                        last = end
                    terminal = intervals[-1][1] if intervals else None
                    terminal_faces = (
                        [hit for hit in hits if abs(hit["t_mm"] - terminal) <= MATCH_TOL]
                        if terminal is not None
                        else []
                    )
                    rays.append(
                        {
                            "bolt_id": axis_id,
                            "group_id": bolt["group_id"],
                            "member_id": member_id,
                            "receiver_axis_interval_from_underhead_mm": interval,
                            "receiver_step_projection_from_underhead_mm": [proj_lo, proj_hi],
                            "axial_station_label": station_name,
                            "axial_station_from_underhead_mm": axial_t,
                            "ray_origin_global_xyz_mm": origin,
                            "grain_axis_global_xyz": grain,
                            "bolt_axis_global_xyz": axis,
                            "e_axis_global_xyz": e,
                            "ray_label": basis_label + suffix,
                            "ray_direction_global_xyz": direction,
                            "center_to_last_material_exit_mm": terminal,
                            "initial_and_intermediate_void_intervals_mm": gaps,
                            "material_intervals_mm": intervals,
                            "exact_finite_face_hits": hits,
                            "terminal_face_candidates": terminal_faces,
                            "terminal_face_match_count": len(terminal_faces),
                            "query_limit_mm": limit,
                        }
                    )

out = {
    "query": "read-only OCC intersections of pinned finished STEP BReps; no CAD rebuild, native solve, or model change",
    "candidate": inputs["accel"]["candidate"],
    "geometry_revision_id": inputs["accel"]["geometry_revision_id"],
    "scope": {
        "group_id": "BG001",
        "bolt_ids": list(TARGET_AXES),
        "member_ids": list(TARGET_MEMBERS),
        "ray_count": len(rays),
    },
    "source_sha256_verified": inputs["source_pins"],
    "tolerances_mm": {
        "solid_intervals": GEOM_TOL,
        "trimmed_face_intersection": FACE_TOL,
        "interval_face_matching": MATCH_TOL,
        "near_end_axial_inset": AXIAL_INSET,
    },
    "station_method": "For each receiver, use its pinned projected bolt-axis interval from underhead; sample 0.01 mm inside each interval end and at middepth. Confirm both projected limits against all exact STEP vertices. Stations are discrete and do not prove continuous through-thickness extrema.",
    "direction_method": "g is the reduced-static declared grain axis; e=unit(g cross a), where a points head-to-nut. In every sampled plane perpendicular to the bolt axis, query g-/g+/e-/e+ from the bolt centerline.",
    "void_and_terminal_method": "Preserve all material intervals and preceding void intervals. Terminal profile face candidates are exact intersections with finite trimmed BRep faces whose t matches the final material exit; report face surface and normal so a bore wall is not confused with the finished exterior.",
    "claim_boundary": "Finished-CAD geometry only. No capacity, force, species/grade verification, inspection, acceptance, or physical build claim. Modeled bolt location, member geometry, and materials remain conditional/unverified.",
    "rays": rays,
}
print(json.dumps(clean(out), indent=2, sort_keys=True))
