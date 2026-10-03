"""Project authenticated planar face signatures; no CAD or mechanical model."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from itertools import combinations, pairwise

CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
PANELS = ("kicker_left", "kicker_right")
GEOMETRY_TOL_MM = 1e-5
AREA_TOL_MM2 = 1e-6


class ProjectionRefusal(ValueError):
    """The saved signature does not prove the requested projection."""


def require(condition, message):
    if not condition:
        raise ProjectionRefusal(message)


def number(value):
    require(type(value) in (int, float) and math.isfinite(value), "nonfinite number")
    return float(value)


def vector(value, size=3):
    require(isinstance(value, (list, tuple)) and len(value) == size, "invalid vector")
    return [number(x) for x in value]


def close(first, second, tolerance=GEOMETRY_TOL_MM):
    require(len(first) == len(second), "vector sizes differ")
    require(
        max((abs(a - b) for a, b in zip(first, second, strict=True)), default=0)
        <= tolerance,
        "saved geometry values differ",
    )


def signature_sha(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def rectangle_holes(signature):
    """Prove a rear X/Z rectangle minus contained disjoint full circular holes."""
    require(signature.get("surface_type") == "PLANE", "nonplanar signature")
    x0, x1, y0, y1, z0, z1 = vector(signature["bounds_xyz_mm"], 6)
    require(x1 > x0 and z1 > z0, "nonpositive rectangle dimensions")
    close([y0], [y1])
    expected = [
        sorted([[x0, y0, z0], [x0, y0, z1]]),
        sorted([[x1, y0, z0], [x1, y0, z1]]),
        sorted([[x0, y0, z0], [x1, y0, z0]]),
        sorted([[x0, y0, z1], [x1, y0, z1]]),
    ]
    found, holes = [], []
    for edge in signature["edge_signatures"]:
        kind = edge.get("curve_type")
        bounds = vector(edge["bounds_xyz_mm"], 6)
        center = vector(edge["center_xyz_mm"])
        vertices = [vector(p) for p in edge["vertex_xyz_mm"]]
        length = number(edge["length_mm"])
        require(length > 0, "nonpositive edge length")
        if kind == "LINE":
            require(len(vertices) == 2, "line lacks two endpoints")
            ordered = sorted(vertices)
            matches = [
                i
                for i, pair in enumerate(expected)
                if all(
                    abs(a - b) <= GEOMETRY_TOL_MM
                    for p, q in zip(pair, ordered, strict=True)
                    for a, b in zip(p, q, strict=True)
                )
            ]
            require(
                len(matches) == 1 and matches[0] not in found,
                "outline is not four distinct rectangle edges",
            )
            found.append(matches[0])
            close([length], [math.dist(*vertices)])
            close(center, [(a + b) / 2 for a, b in zip(*vertices, strict=True)])
            close(
                bounds,
                [
                    v
                    for k in range(3)
                    for v in (min(p[k] for p in vertices), max(p[k] for p in vertices))
                ],
            )
        elif kind == "CIRCLE":
            require(len(vertices) == 1, "circle is not a full closed edge")
            radius = (bounds[1] - bounds[0]) / 2
            require(radius > 0, "nonpositive hole radius")
            close(
                bounds,
                [
                    center[0] - radius,
                    center[0] + radius,
                    y0,
                    y0,
                    center[2] - radius,
                    center[2] + radius,
                ],
            )
            close([center[1], vertices[0][1]], [y0, y0])
            close([length], [2 * math.pi * radius])
            close([math.dist(center, vertices[0])], [radius])
            require(
                x0 + GEOMETRY_TOL_MM < center[0] - radius
                and center[0] + radius < x1 - GEOMETRY_TOL_MM
                and z0 + GEOMETRY_TOL_MM < center[2] - radius
                and center[2] + radius < z1 - GEOMETRY_TOL_MM,
                "hole is not strictly contained",
            )
            holes.append({"center_xz_mm": [center[0], center[2]], "radius_mm": radius})
        else:
            raise ProjectionRefusal(f"unsupported trim curve: {kind}")
    require(sorted(found) == list(range(4)), "incomplete rectangular outline")
    require(signature.get("wire_count") == 1 + len(holes), "wire count differs")
    for first, second in combinations(holes, 2):
        require(
            math.dist(first["center_xz_mm"], second["center_xz_mm"])
            > first["radius_mm"] + second["radius_mm"] + GEOMETRY_TOL_MM,
            "holes intersect or touch",
        )
    area = (x1 - x0) * (z1 - z0) - math.fsum(
        math.pi * h["radius_mm"] ** 2 for h in holes
    )
    close([area], [number(signature["area_mm2"])], AREA_TOL_MM2)
    return {
        "x_interval_mm": [x0, x1],
        "y_mm": y0,
        "z_interval_mm": [z0, z1],
        "holes": holes,
        "reconstructed_area_mm2": area,
        "area_difference_mm2": area - signature["area_mm2"],
    }


def union_intervals(intervals):
    result = []
    for lo, hi in sorted(intervals):
        require(hi >= lo, "reversed interval")
        if result and lo <= result[-1][1]:
            result[-1][1] = max(result[-1][1], hi)
        else:
            result.append([lo, hi])
    return result


def subtract_intervals(domain, removed):
    lo, hi = domain
    result, cursor = [], lo
    for a, b in union_intervals(removed):
        a, b = max(a, lo), min(b, hi)
        if b < lo or a > hi:
            continue
        if a > cursor:
            result.append([cursor, a])
        cursor = max(cursor, b)
    if cursor < hi:
        result.append([cursor, hi])
    return result


def project_strip(region, seam_x, inward_sign, width):
    """Project material in a reporting strip, retaining isolated hole tangencies."""
    require(inward_sign in (-1, 1), "invalid inward direction")
    width = number(width)
    require(width >= 0, "negative strip width")
    first, last = sorted((seam_x, seam_x + inward_sign * width))
    lo = max(first, region["x_interval_mm"][0])
    hi = min(last, region["x_interval_mm"][1])
    if hi < lo or (width > 0 and hi == lo):
        return {"covered_z_intervals_mm": [], "isolated_hole_tangencies_z_mm": []}
    removed, isolated = [], []
    for hole in region["holes"]:
        cx, cz = hole["center_xz_mm"]
        radius = hole["radius_mm"]
        distance = max(abs(lo - cx), abs(hi - cx))
        if distance < radius:
            dz = math.sqrt(radius * radius - distance * distance)
            removed.append([cz - dz, cz + dz])
        elif distance == radius:
            isolated.append(cz)
    return {
        "covered_z_intervals_mm": subtract_intervals(region["z_interval_mm"], removed),
        "isolated_hole_tangencies_z_mm": sorted(isolated),
        "interval_boundary_convention": "closures of positive material intervals; isolated hole tangencies are separate",
    }


def build_backing(atlas, graph, manifest):
    """Join current face identities and project only supported analytic trims."""
    require(
        atlas.get("candidate") == manifest.get("candidate") == CANDIDATE,
        "candidate differs",
    )
    require(
        atlas.get("revision_id")
        == graph.get("revision_id")
        == manifest.get("geometry_revision_id")
        == REVISION,
        "revision differs",
    )
    bodies = {b["member_id"]: b for b in atlas["body_inventory"]}
    require(len(bodies) == len(atlas["body_inventory"]) == 50, "body census differs")
    graph_bodies = {b["member_id"]: b for b in graph["inventories"]["physical_members"]}
    require(set(bodies) == set(graph_bodies), "graph and atlas body IDs differ")
    bindings = {r["member_id"]: r for r in manifest["finished_member_step_bindings"]}
    require(set(bindings) == set(bodies), "STEP binding census differs")
    faces = {}
    for body in bodies.values():
        binding = bindings[body["member_id"]]
        require(
            body["step_path"] == binding["path"]
            and body["step_sha256"] == binding["file_sha256"],
            "STEP binding differs",
        )
        for face in body["planar_faces"]:
            require(face["face_id"] not in faces, "duplicate source face identity")
            require(
                signature_sha(face["signature"]) == face["signature_sha256"],
                "source face signature hash differs",
            )
            faces[face["face_id"]] = face
    interfaces = {tuple(r["member_ids"]): r for r in atlas["finite_opposed_interfaces"]}
    require(
        len(interfaces) == len(atlas["finite_opposed_interfaces"]),
        "duplicate interface",
    )
    edges = [e for e in graph["edges"] if any(p in e["member_ids"] for p in PANELS)]
    expected_pairs = {tuple(sorted((p, m))) for p in PANELS for m in bodies if m != p}
    require(
        {tuple(e["member_ids"]) for e in edges} == expected_pairs and len(edges) == 97,
        "kicker pair census differs",
    )
    counts = Counter(e["geometry_state"] for e in edges)
    require(
        counts
        == {
            "separated": 82,
            "finite_opposed_planar_touch": 11,
            "zero_area_touch_or_unresolved": 4,
        },
        "kicker states differ",
    )
    result = []
    for panel, sign in zip(PANELS, (-1, 1), strict=True):
        rear = [
            f
            for f in bodies[panel]["planar_faces"]
            if f["signature"]["oriented_normal_xyz"] == [0.0, -1.0, 0.0]
        ]
        require(len(rear) == 1, "panel lacks one rear planar face")
        panel_face = rear[0]
        outline = rectangle_holes(panel_face["signature"])
        seam = outline["x_interval_mm"][1 if sign == -1 else 0]
        close([outline["y_mm"]], [-36.0])
        bounds = vector(graph_bodies[panel]["finished"]["bounds_xyz_mm"], 6)
        thickness = bounds[3] - bounds[2]
        require(thickness > 0, "panel thickness is nonpositive")
        close(
            [bounds[0], bounds[1], bounds[2], bounds[4], bounds[5]],
            [*outline["x_interval_mm"], outline["y_mm"], *outline["z_interval_mm"]],
        )
        patch_rows, context_rows, edge_intervals, strip_intervals = [], [], [], []
        for edge in edges:
            if panel not in edge["member_ids"]:
                continue
            pair = tuple(edge["member_ids"])
            finite = edge["geometry_state"] == "finite_opposed_planar_touch"
            require(
                (pair in interfaces) == finite, "finite atlas/graph pair join differs"
            )
            if not finite:
                context_rows.append(
                    {
                        "member_ids": list(pair),
                        "state": edge["geometry_state"],
                        "backing_credited": False,
                    }
                )
                continue
            interface = interfaces[pair]
            close(
                [interface["reconstructed_opposed_area_mm2"]],
                [edge["opposed_planar_face_contact_area_mm2"]],
                max(AREA_TOL_MM2, edge["opposed_planar_face_contact_area_mm2"] * 1e-10),
            )
            other = next(m for m in pair if m != panel)
            for fp in interface["face_pairs"]:
                for side in ("a", "b"):
                    face = faces[fp[f"face_{side}_id"]]
                    require(
                        face["signature_sha256"] == fp[f"face_{side}_signature_sha256"],
                        "interface source face signature differs",
                    )
                    require(
                        fp[f"face_{side}_id"].startswith(
                            pair[0 if side == "a" else 1] + "/"
                        ),
                        "source face member differs",
                    )
                rear_pair = panel_face["face_id"] in (fp["face_a_id"], fp["face_b_id"])
                direct = rear_pair and graph_bodies[other]["member_kind"] == "timber"
                if not direct:
                    context_rows.append(
                        {
                            "member_ids": list(pair),
                            "state": edge["geometry_state"],
                            "source_face_ids": [fp["face_a_id"], fp["face_b_id"]],
                            "backing_credited": False,
                            "reason": "not direct rear timber contact",
                        }
                    )
                    continue
                close(
                    fp["face_a_oriented_normal_xyz"],
                    faces[fp["face_a_id"]]["signature"]["oriented_normal_xyz"],
                )
                close(
                    fp["face_b_oriented_normal_xyz"],
                    faces[fp["face_b_id"]]["signature"]["oriented_normal_xyz"],
                )
                require(fp["normal_dot"] < 0, "source contact normals are not opposed")
                other_face = faces[
                    fp["face_a_id"] if pair[0] == other else fp["face_b_id"]
                ]
                close(other_face["signature"]["oriented_normal_xyz"], [0.0, 1.0, 0.0])
                for i, signature in enumerate(fp["overlap_regions"]):
                    region = rectangle_holes(signature)
                    close([region["y_mm"]], [outline["y_mm"]])
                    for actual, domain in (
                        (region["x_interval_mm"], outline["x_interval_mm"]),
                        (region["z_interval_mm"], outline["z_interval_mm"]),
                    ):
                        require(
                            actual[0] >= domain[0] - GEOMETRY_TOL_MM
                            and actual[1] <= domain[1] + GEOMETRY_TOL_MM,
                            "overlap region exceeds the panel face",
                        )
                    line = project_strip(region, seam, sign, 0.0)
                    strip = project_strip(region, seam, sign, thickness)
                    edge_intervals.extend(line["covered_z_intervals_mm"])
                    strip_intervals.extend(strip["covered_z_intervals_mm"])
                    offsets = sorted(sign * (x - seam) for x in region["x_interval_mm"])
                    patch_rows.append(
                        {
                            "other_member_id": other,
                            "source_face_ids": [fp["face_a_id"], fp["face_b_id"]],
                            "region_index": i,
                            "signature_sha256": signature_sha(signature),
                            "analytic_region": region,
                            "inward_x_interval_mm": offsets,
                            "positive_strip_overlap_requires_width_greater_than_mm": max(
                                0.0, offsets[0]
                            ),
                            "full_rectangle_x_coverage_at_width_mm": offsets[1],
                            "edge_line_projection": line,
                            "panel_thickness_reporting_strip_projection": strip,
                        }
                    )
        covered = union_intervals(edge_intervals)
        strips = union_intervals(strip_intervals)
        breaks = sorted(
            {
                *outline["z_interval_mm"],
                *(z for p in patch_rows for z in p["analytic_region"]["z_interval_mm"]),
            }
        )
        stand_off = []
        for lo, hi in pairwise(breaks):
            if hi <= lo:
                continue
            middle = (lo + hi) / 2
            available = [
                p
                for p in patch_rows
                if p["analytic_region"]["z_interval_mm"][0]
                < middle
                < p["analytic_region"]["z_interval_mm"][1]
            ]
            distance = min(
                (max(0.0, p["inward_x_interval_mm"][0]) for p in available),
                default=None,
            )
            stand_off.append(
                {
                    "z_interval_mm": [lo, hi],
                    "minimum_geometric_inward_offset_mm": distance,
                    "nearest_member_ids": sorted(
                        {
                            p["other_member_id"]
                            for p in available
                            if max(0.0, p["inward_x_interval_mm"][0]) == distance
                        }
                    ),
                    "effective_mechanical_span_established": False,
                }
            )
        result.append(
            {
                "panel_member_id": panel,
                "rear_face_id": panel_face["face_id"],
                "rear_face_signature_sha256": panel_face["signature_sha256"],
                "inner_edge_start_global_xyz_mm": [
                    seam,
                    outline["y_mm"],
                    outline["z_interval_mm"][0],
                ],
                "inner_edge_end_global_xyz_mm": [
                    seam,
                    outline["y_mm"],
                    outline["z_interval_mm"][1],
                ],
                "inward_x_sign": sign,
                "edge_z_domain_mm": outline["z_interval_mm"],
                "panel_thickness_reporting_width_mm": thickness,
                "direct_rear_timber_edge_covered_z_intervals_mm": covered,
                "direct_rear_timber_edge_gap_z_intervals_mm": subtract_intervals(
                    outline["z_interval_mm"], covered
                ),
                "panel_thickness_strip_covered_z_intervals_mm": strips,
                "direct_rear_timber_patches": patch_rows,
                "nearest_rear_timber_stand_off_by_z": stand_off,
                "other_contact_context": context_rows,
                "gap_establishes_mechanical_failure": False,
                "reporting_width_is_adopted_bearing_requirement": False,
            }
        )
    close(
        result[0]["inner_edge_start_global_xyz_mm"],
        result[1]["inner_edge_start_global_xyz_mm"],
    )
    close(
        result[0]["inner_edge_end_global_xyz_mm"],
        result[1]["inner_edge_end_global_xyz_mm"],
    )
    return {
        "schema": "current_center_kicker_backing_projection/v1",
        "status": "SAVED_PLANAR_GEOMETRY_PROJECTION_ONLY",
        "panels": result,
        "pair_census": [
            {
                "member_ids": edge["member_ids"],
                "geometry_state": edge["geometry_state"],
                "broadphase_candidate": edge["broadphase_candidate"],
            }
            for edge in sorted(edges, key=lambda e: e["member_ids"])
        ],
        "counts": {
            "kicker_other_body_pairs": len(edges),
            "broadphase_candidates": sum(e["broadphase_candidate"] for e in edges),
            "geometry_states": dict(counts),
            "validated_source_face_signatures": len(faces),
        },
        "source_precision": {
            "signature_decimals": 9,
            "geometry_comparison_mm": GEOMETRY_TOL_MM,
            "area_reconstruction_comparison_mm2": AREA_TOL_MM2,
            "purpose": "saved signature arithmetic only; no physical gate",
        },
        "continuous_direct_backing_is_adopted_criterion": False,
        "active_contact_or_complete_edge_load_transfer_established": False,
    }
