"""Nominal wood-boundary screen for the seven center-tongue HL33 axes."""

import argparse
import json
from math import hypot
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.bolted_candidate_ab205_center_fit import (
    _grain_edge_lines,
    _line_y,
    _principal_broad_face,
)
from scripts.hardware_first_center_hl33 import ALONG_BEND, LEG_HOLE, PLATE, REACH
from scripts.hardware_first_center_hybrid import BORE, TOP, bore, box
from scripts.hardware_first_center_hybrid_toe import _principal
from scripts.hardware_first_center_tongue import (
    HOLE_INSET,
    POST_DEPTH,
    POST_HALF,
    TONGUE_HALF,
    UPPER_Y0,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT / "docs/bolted-candidate-prototypes/hardware_first_center_tongue_wood.json"
)
D = 12.7


def _round(value):
    return round(value, 4)


def _margin(distance, multiple):
    return _round(distance - multiple * D)


def _face_ray(face, y, z, gy, gz, direction):
    """First boundary of the actual broad-face polygon along a grain ray."""
    hits = []
    for edge in face.Edges():
        vertices = edge.Vertices()
        if len(vertices) != 2:
            continue
        a, b = (vertex.Center() for vertex in vertices)
        ey, ez = b.y - a.y, b.z - a.z
        dy, dz = direction * gy, direction * gz
        denominator = dy * ez - dz * ey
        if abs(denominator) < 1e-9:
            continue
        wy, wz = y - a.y, z - a.z
        distance = (wy * ez - wz * ey) / denominator
        fraction = -(wy * dz - wz * dy) / denominator
        if distance > 1e-7 and -1e-7 <= fraction <= 1 + 1e-7:
            hits.append(distance)
    if not hits:
        raise ValueError("Principal grain ray missed the shaped CAD boundary")
    return min(hits)


def _axis_record(member, center, grain, ends, edges, *, oblique=False):
    return {
        "member": member,
        "center_mm": [_round(v) for v in center],
        "grain_unit_xyz": [_round(v) for v in grain],
        "grain_negative_boundary_mm": _round(ends[0]),
        "grain_positive_boundary_mm": _round(ends[1]),
        "transverse_negative_boundary_mm": _round(edges[0]),
        "transverse_positive_boundary_mm": _round(edges[1]),
        "reversible_7d_grain_margins_mm": [_margin(v, 7) for v in ends],
        "reversible_4d_transverse_margins_mm": [_margin(v, 4) for v in edges],
        "oblique_end_unclassified": oblique,
    }


def screen_center_tongue_wood():
    """Measure centerline rays; threshold margins are search filters only."""
    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    hb = raw["base_header"].BoundingBox()
    front = hb.ymax
    post_rear = front - POST_DEPTH
    lower_top = hb.zmin - PLATE
    post = (
        box(-POST_HALF, post_rear, 0, 2 * POST_HALF, POST_DEPTH, lower_top)
        .fuse(
            box(-TONGUE_HALF, post_rear, lower_top, 2 * TONGUE_HALF, POST_DEPTH, PLATE)
        )
        .clean()
    )
    header = (
        raw["base_header"]
        .fuse(
            box(
                -230,
                hb.ymin - REACH,
                hb.zmin,
                460,
                front - hb.ymin + REACH,
                TOP - hb.zmin,
            )
        )
        .clean()
    )
    principals = {side: _principal(side) for side in ("left", "right")}
    if (
        len(post.Solids()) != 1
        or len(header.Solids()) != 1
        or any(len(shape.Solids()) != 1 for shape in principals.values())
    ):
        raise ValueError("Expected one-piece shaped CAD wood")

    axes = {}
    post_y = post_rear + ALONG_BEND
    post_z = lower_top - LEG_HOLE
    axes["shared_post"] = _axis_record(
        "post",
        (0, post_y, post_z),
        (0, 0, 1),
        (post_z, lower_top - post_z),
        (post_y - post_rear, front - post_y),
    )
    header_centers = {}
    for side, sign in (("left", -1), ("right", 1)):
        lower_x = sign * (POST_HALF - HOLE_INSET)
        upper_x = sign * (70 + 44.45 + LEG_HOLE)
        lower_y = post_y
        upper_y = UPPER_Y0 + ALONG_BEND
        header_centers[f"lower_{side}_header"] = (lower_x, lower_y)
        header_centers[f"upper_{side}_header"] = (upper_x, upper_y)
        member = principals[side]
        x = member.BoundingBox().xmin
        face = _principal_broad_face(member, x)
        lines = _grain_edge_lines(face)
        if len(lines) != 2 or abs(lines[0][2] - lines[1][2]) > 1e-6:
            raise ValueError("Expected parallel principal grain edges")
        slope = lines[0][2]
        gy, gz = slope / hypot(slope, 1), 1 / hypot(slope, 1)
        z = TOP + LEG_HOLE
        lower_y_edge, upper_y_edge = sorted(_line_y(line, z) for line in lines)
        axes[f"upper_{side}_principal"] = _axis_record(
            f"base_principal_center_{side}",
            (sign * 70, upper_y, z),
            (0, gy, gz),
            (
                _face_ray(face, upper_y, z, gy, gz, -1),
                _face_ray(face, upper_y, z, gy, gz, 1),
            ),
            ((upper_y - lower_y_edge) * gz, (upper_y_edge - upper_y) * gz),
            oblique=True,
        )

    # At every header axis the upper portion of the full bore meets the
    # +/-230 mm profile shoulder. It is an internal shoulder, not a free end.
    hbox = header.BoundingBox()
    for name, (x, y) in header_centers.items():
        if not -230 < x < 230 or not hb.zmin < TOP:
            raise ValueError("Header axis outside the one-piece raised region")
        axes[name] = _axis_record(
            "header",
            (x, y, (hb.zmin + TOP) / 2),
            (1, 0, 0),
            (x - -230, 230 - x),
            (y - hbox.ymin, hbox.ymax - y),
        )
        axes[name]["grain_boundary_kind"] = "raised_profile_shoulder_not_free_end"
        axes[name]["full_span_grain_rays_at_lower_section_mm"] = [
            _round(x - hbox.xmin),
            _round(hbox.xmax - x),
        ]

    groups = {}
    for a, b in (
        ("lower_left_header", "lower_right_header"),
        ("upper_left_header", "upper_right_header"),
    ):
        x0, y0 = header_centers[a]
        x1, y1 = header_centers[b]
        spacing = hypot(x1 - x0, y1 - y0)
        groups[f"{a} / {b}"] = {
            "center_spacing_mm": _round(spacing),
            "parallel_row_3d_minimum_margin_mm": _margin(spacing, 3),
            "parallel_row_4d_full_factor_margin_mm": _margin(spacing, 4),
        }
    cross_group = {}
    for lower in ("lower_left_header", "lower_right_header"):
        for upper in ("upper_left_header", "upper_right_header"):
            x0, y0 = header_centers[lower]
            x1, y1 = header_centers[upper]
            spacing = hypot(x1 - x0, y1 - y0)
            cross_group[f"{lower} / {upper}"] = {
                "delta_along_grain_x_mm": _round(abs(x1 - x0)),
                "delta_transverse_y_mm": _round(abs(y1 - y0)),
                "center_spacing_mm": _round(spacing),
                "nominal_bore_surface_gap_mm": _round(spacing - BORE),
            }

    toe_proximity = {}
    for name, (x, y) in header_centers.items():
        cylinder = bore((x, y, hb.zmin), (0, 0, 1), TOP - hb.zmin)
        toe_proximity[name] = {
            side: _round(cylinder.distance(shape)) for side, shape in principals.items()
        }

    return {
        "status": "conditional_nominal_geometry_only",
        "source_pose": "scripts.hardware_first_center_tongue",
        "wood_source": "kerf-right uncut CAD plus parent tongue/header/principal shaping",
        "bolt_diameter_mm": D,
        "nominal_bore_diameter_mm": BORE,
        "nds_basis": "2024 NDS 12.5.1.2-.3, Tables 12.5.1A-D; category and geometry factor require load direction/member classification",
        "formal_nds_categories_unresolved": {
            "end_distance_table_12_5_1a": "Tension/compression and member/end geometry must be classified; softwood parallel-tension markers are 3.5D reduced factor and 7D full factor for square-cut ends. No classification of the principal oblique cut or header profile shoulder.",
            "row_spacing_table_12_5_1b": "Parallel-to-grain row 3D minimum and 4D full-factor markers; loading and grouping still unresolved.",
            "edge_distance_table_12_5_1c": "Loaded versus unloaded transverse edge cannot be assigned without each member's load direction.",
            "between_rows_table_12_5_1d": "Cross-group Y separation is measured, but applicable row-spacing category and bearing-length ratio are unresolved.",
        },
        "search_filters_mm": {
            "both_transverse_edges_4d": _round(4 * D),
            "both_grain_directions_7d": _round(7 * D),
        },
        "axis_margins": axes,
        "independent_header_group_spacing": groups,
        "cross_group_header_spacing": cross_group,
        "header_bore_to_principal_toe_solid_gap_mm": toe_proximity,
        "limits": "Centerline rays on ideal one-piece solids; oblique principal cut and header shoulder are not classified NDS end distances. No delivered tolerances, capacity, or wood-joint pass.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(screen_center_tongue_wood(), indent=2) + "\n")


if __name__ == "__main__":
    main()
