#!/usr/bin/env python3
"""Read-only finished STEP profile rays for the three-member BG003 stack."""
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
TARGET_AXES = ("knee_outer_left_side_1", "knee_outer_left_side_2")
TARGET_MEMBERS = (
    "knee_outer_left_spine",
    "base_side_left",
    "knee_outer_left_inner_frame_block",
)
GEOM_TOL = 1e-7
FACE_TOL = 2e-4
MATCH_TOL = 2e-4
AXIAL_INSET = 0.01


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unit(vector):
    length = math.sqrt(sum(value * value for value in vector))
    if length == 0:
        raise ValueError("zero vector")
    return tuple(value / length for value in vector)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def add(point, axis, scale):
    return tuple(point[i] + axis[i] * scale for i in range(3))


def clean(value):
    if isinstance(value, float):
        return round(value, 9)
    if isinstance(value, (tuple, list)):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    return value


def bbox_ray_limit(shape, origin, direction):
    bounds = shape.BoundingBox()
    corners = [
        (x, y, z)
        for x in (bounds.xmin, bounds.xmax)
        for y in (bounds.ymin, bounds.ymax)
        for z in (bounds.zmin, bounds.zmax)
    ]
    return max(dot(tuple(c[i] - origin[i] for i in range(3)), direction) for c in corners) + 5.0


def finite_face_hits(shape, origin, direction, limit):
    """Return exact intersections with finite trimmed STEP faces and normals."""
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
                except Exception as error:  # pragma: no cover - preserved in raw evidence
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
        raise RuntimeError("connection_geometry.py changed; review the pinned ray method before querying")

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
    nested_source_pins = {}
    for source_path, pin in accel["source_pins"].items():
        actual = sha256(ROOT / source_path)
        if actual != pin["sha256"] or actual != accel["source_sha256_observed"][source_path]:
            raise RuntimeError(f"bolt-groups nested source pin mismatch: {source_path}")
        nested_source_pins[source_path] = actual

    accel_axes = {
        row["axis_id"]: row
        for row in accel["candidate_axes"]
        if row["axis_id"] in TARGET_AXES
    }
    manifest_axes = {
        row["axis_id"]: row
        for row in manifest["candidate_bolt_axes"]
        if row["axis_id"] in TARGET_AXES
    }
    if set(accel_axes) != set(TARGET_AXES) or set(manifest_axes) != set(TARGET_AXES):
        raise RuntimeError("one or more BG003 target bolts are absent from pinned inputs")
    for axis_id in TARGET_AXES:
        if accel_axes[axis_id]["group_id"] != "BG003":
            raise RuntimeError(f"unexpected group for target axis {axis_id}")

    geometry_members = {row["member_id"]: row for row in member_geometry["members"]}
    manifest_bindings = {
        row["member_id"]: row for row in manifest["finished_member_step_bindings"]
    }
    if not set(TARGET_MEMBERS).issubset(geometry_members):
        raise RuntimeError("a target receiver is missing from reduced-static member geometry")
    if not set(TARGET_MEMBERS).issubset(manifest_bindings):
        raise RuntimeError("a target receiver is missing from attempt04 finished STEP bindings")

    grain_proposals = {}
    for axis_member in accel["candidate_axis_receiver_grain_angles"]:
        if axis_member["axis_id"] in TARGET_AXES and axis_member["receiver_member_id"] in TARGET_MEMBERS:
            grain_proposals[(axis_member["axis_id"], axis_member["receiver_member_id"])] = axis_member
    expected_keys = {(axis, member) for axis in TARGET_AXES for member in TARGET_MEMBERS}
    if set(grain_proposals) != expected_keys:
        raise RuntimeError("missing or duplicate source-proposed receiver grain mapping")

    shapes = {}
    step_pins = {}
    for member_id in TARGET_MEMBERS:
        descriptor = geometry_members[member_id]
        binding = manifest_bindings[member_id]
        if descriptor["step_path"] != binding["path"]:
            raise RuntimeError(f"member geometry/manifest STEP path mismatch: {member_id}")
        if descriptor["step_sha256"] != binding["file_sha256"]:
            raise RuntimeError(f"member geometry/manifest STEP hash mismatch: {member_id}")
        step_rel = Path(binding["path"])
        step_path = ROOT / step_rel
        step_sha = sha256(step_path)
        if step_sha != binding["file_sha256"]:
            raise RuntimeError(f"attempt04 finished STEP file hash mismatch: {member_id}")
        if member_geometry["inputs"]["member_step_file_sha256"].get(step_rel.as_posix()) != step_sha:
            raise RuntimeError(f"reduced-static STEP pin mismatch: {member_id}")
        shape = cq.importers.importStep(str(step_path)).val()
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise RuntimeError(f"invalid or non-single-solid finished STEP: {member_id}")
        shapes[member_id] = shape
        step_pins[step_rel.as_posix()] = step_sha

    for axis_id in TARGET_AXES:
        accel_axis = accel_axes[axis_id]
        manifest_axis = manifest_axes[axis_id]
        geometry = manifest_axis["geometry"]
        if geometry["axis_head_to_nut_global"] != accel_axis["axis_head_to_nut_unit_global_xyz"]:
            raise RuntimeError(f"acceleration/attempt04 axis mismatch: {axis_id}")
        if geometry["shaft_center_global_xyz_mm"] != accel_axis["shaft_center_global_xyz_mm"]:
            raise RuntimeError(f"acceleration/attempt04 shaft-center mismatch: {axis_id}")
        if geometry["modeled_underhead_to_tip_mm"] != accel_axis["modeled_underhead_to_tip_mm"]:
            raise RuntimeError(f"acceleration/attempt04 modeled length mismatch: {axis_id}")
        manifest_rows = geometry["wood_receiver_intervals"]
        ordered_rows = sorted(
            manifest_rows,
            key=lambda item: item["current_shaft_intersection_solid_intervals_from_underhead_mm"][0][0],
        )
        if [item["receiver_id"] for item in ordered_rows] != list(TARGET_MEMBERS):
            raise RuntimeError(f"attempt04 modeled receiver stack order mismatch: {axis_id}")
        if [item["receiver_id"] for item in manifest_rows] != list(TARGET_MEMBERS):
            raise RuntimeError(f"attempt04 receiver row order differs from recorded stack order: {axis_id}")
        proposal_intervals = accel_axis["geometric_receiver_order_proposal"][
            "receiver_intervals_from_underhead_mm"
        ]
        for member_id in TARGET_MEMBERS:
            row = next(item for item in manifest_rows if item["receiver_id"] == member_id)
            manifest_intervals = row["current_shaft_intersection_solid_intervals_from_underhead_mm"]
            if len(manifest_intervals) != 1 or manifest_intervals[0] != proposal_intervals[member_id]:
                raise RuntimeError(f"acceleration/attempt04 receiver interval mismatch: {axis_id}/{member_id}")
            proposed_grain = unit(
                tuple(grain_proposals[(axis_id, member_id)]["source_proposed_grain_unit_global_xyz"])
            )
            descriptor_grain = unit(tuple(geometry_members[member_id]["grain_global_xyz"]))
            if max(abs(proposed_grain[i] - descriptor_grain[i]) for i in range(3)) > 1e-8:
                raise RuntimeError(f"source grain proposal/reduced-static grain mismatch: {axis_id}/{member_id}")

    return {
        "accel": accel,
        "member_geometry": member_geometry,
        "manifest": manifest,
        "accel_axes": accel_axes,
        "manifest_axes": manifest_axes,
        "geometry_members": geometry_members,
        "grain_proposals": grain_proposals,
        "shapes": shapes,
        "source_pins": {
            ACCEL_REL.as_posix(): accel_sha,
            MEMBER_GEOMETRY_REL.as_posix(): member_geometry_sha,
            MANIFEST_REL.as_posix(): manifest_file_sha,
            **nested_source_pins,
            "manifest_embedded_manifest_sha256": manifest["manifest_sha256"],
            HELPER_REL.as_posix(): helper_sha,
            **step_pins,
        },
    }


inputs = load_and_validate_inputs()
rays = []
stack_intervals = {}

for axis_id in TARGET_AXES:
    bolt = inputs["accel_axes"][axis_id]
    manifest_bolt = inputs["manifest_axes"][axis_id]
    axis = unit(tuple(bolt["axis_head_to_nut_unit_global_xyz"]))
    center = tuple(bolt["shaft_center_global_xyz_mm"])
    underhead_to_tip = bolt["modeled_underhead_to_tip_mm"]
    underhead_datum = add(center, axis, -underhead_to_tip / 2.0)
    manifest_rows = manifest_bolt["geometry"]["wood_receiver_intervals"]
    ordered_rows = sorted(
        manifest_rows,
        key=lambda item: item["current_shaft_intersection_solid_intervals_from_underhead_mm"][0][0],
    )
    stack_intervals[axis_id] = []

    for order_index, receiver in enumerate(ordered_rows, 1):
        member_id = receiver["receiver_id"]
        interval = receiver["current_shaft_intersection_solid_intervals_from_underhead_mm"][0]
        lo, hi = interval
        if hi - lo <= 2 * AXIAL_INSET:
            raise RuntimeError(f"receiver too thin for endpoint and midpoint probes: {axis_id}/{member_id}")
        member = inputs["geometry_members"][member_id]
        grain_record = inputs["grain_proposals"][(axis_id, member_id)]
        grain = unit(tuple(grain_record["source_proposed_grain_unit_global_xyz"]))
        if abs(dot(grain, axis)) > 1e-6:
            raise RuntimeError(f"proposed grain/bolt axes not orthogonal: {axis_id}/{member_id}")
        e = unit(cross(grain, axis))
        shape = inputs["shapes"][member_id]

        # Check both recorded axial limits against the exact STEP vertex projection.
        vertices = [vertex.Center().toTuple() for vertex in shape.Vertices()]
        projected = [dot(tuple(point[i] - underhead_datum[i] for i in range(3)), axis) for point in vertices]
        proj_lo, proj_hi = min(projected), max(projected)
        if max(abs(proj_lo - lo), abs(proj_hi - hi)) > 5e-4:
            raise RuntimeError(
                f"attempt04 receiver interval/STEP projection mismatch: {axis_id}/{member_id}; "
                f"interval=[{lo}, {hi}], STEP=[{proj_lo}, {proj_hi}]"
            )

        stack_intervals[axis_id].append(
            {
                "stack_order_from_modeled_underhead": order_index,
                "member_id": member_id,
                "source_proposed_grain_global_xyz": grain,
                "grain_map_source": grain_record["grain_map_source"],
                "interval_from_underhead_mm": interval,
                "step_vertex_projection_from_underhead_mm": [proj_lo, proj_hi],
                "interval_length_mm": hi - lo,
                "physical_head_to_nut_order_verified": False,
            }
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
                    voids = []
                    last = 0.0
                    for start, end in intervals:
                        if start > last + MATCH_TOL:
                            voids.append([last, start])
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
                            "stack_receiver_order_from_modeled_underhead": order_index,
                            "member_id": member_id,
                            "grain_map_source": grain_record["grain_map_source"],
                            "grain_proposal_global_xyz": grain,
                            "receiver_interval_from_underhead_mm": interval,
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
                            "initial_and_intermediate_void_intervals_mm": voids,
                            "material_intervals_mm": intervals,
                            "exact_finite_face_hits": hits,
                            "terminal_face_candidates": terminal_faces,
                            "terminal_face_match_count": len(terminal_faces),
                            "query_limit_mm": limit,
                        }
                    )

out = {
    "query": "read-only OCC intersections of pinned finished STEP BReps; no CAD rebuild, mesh, native solve, or model change",
    "candidate": inputs["accel"]["candidate"],
    "geometry_revision_id": inputs["accel"]["geometry_revision_id"],
    "scope": {
        "physical_stack_group_id": "BG003",
        "bolt_ids": list(TARGET_AXES),
        "receiver_order_basis": "attempt04 modeled underhead-to-tip interval order; physical installed head/nut order remains unverified",
        "member_ids_head_to_nut_proposal": list(TARGET_MEMBERS),
        "ray_count": len(rays),
    },
    "modeled_receiver_intervals_and_source_proposed_grains": stack_intervals,
    "source_sha256_verified": inputs["source_pins"],
    "tolerances_mm": {
        "solid_intervals": GEOM_TOL,
        "trimmed_face_intersection": FACE_TOL,
        "interval_face_matching": MATCH_TOL,
        "near_end_axial_inset": AXIAL_INSET,
    },
    "station_method": "For each receiver in the single modeled three-member BG003 stack, use its attempt04 current-shaft solid interval from underhead; sample 0.01 mm inside each interval end and at middepth. Confirm both limits against the exact STEP vertex projection. Stations are discrete and do not prove continuous through-thickness extrema.",
    "direction_method": "g is the receiver-specific source-proposed grain unit vector in bolt-groups.json, checked against reduced-static member geometry; e=unit(g cross a), with a pointing head-to-nut. Query g-/g+/e-/e+ from the bolt centerline at each station.",
    "void_and_terminal_method": "Preserve all material intervals and intervening voids. A terminal exterior face candidate is an exact intersection with a finite trimmed BRep face whose ray parameter matches the final material exit; report surface type and normal to distinguish bores from outside profiles.",
    "claim_boundary": "Modeled finished-CAD geometry only. Receiver stack order is a geometric interval proposal, not verified hardware head-to-nut order. No capacity, force, species/grade verification, inspection, acceptance, or physical build claim.",
    "rays": rays,
}
print(json.dumps(clean(out), indent=2, sort_keys=True))
