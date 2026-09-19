"""Nominal AB205 holes on the current center butt; no connector approval."""

from math import hypot, pi
from typing import Literal

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as frame


def _principal_broad_face(principal: cq.Solid, x_mm: float) -> cq.Face:
    return next(
        face
        for face in principal.Faces()
        if face.Vertices()
        and all(abs(vertex.Center().x - x_mm) < 1e-5 for vertex in face.Vertices())
    )


def _grain_edge_lines(face: cq.Face) -> tuple[tuple[float, float, float], ...]:
    """Return the two long YZ-side edges as (y0, z0, dy/dz)."""
    lines = []
    for edge in sorted(face.Edges(), key=lambda item: item.Length(), reverse=True)[:2]:
        a, b = (vertex.Center() for vertex in edge.Vertices())
        lines.append((a.y, a.z, (b.y - a.y) / (b.z - a.z)))
    return tuple(lines)


def _line_y(line: tuple[float, float, float], z_mm: float) -> float:
    y0, z0, slope = line
    return y0 + slope * (z_mm - z0)


def screen_center_fit(
    vertical_leg: Literal["long", "short"] = "long",
) -> dict[str, object]:
    """Check one flush-bend orientation against raw CAD, before new drilling."""
    if vertical_leg not in ("long", "short"):
        raise ValueError("Vertical AB205 leg must be long or short")
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    station = next(
        item for item in frame.stations() if item[0] == "clip_split_base_center_left"
    )
    header = parts["base_header"]
    principal = parts["base_principal_center_left"]
    x = principal.BoundingBox().xmin
    z = header.BoundingBox().zmax
    y = station[1].y
    bolt_diameter_mm = 12.7
    wood_hole_radius_mm = 14.2875 / 2
    loaded_edge_mm = 4 * bolt_diameter_mm
    long_offsets_in = (1.4375, 3.3125)
    short_offsets_in = (0.8125, 2.6875)
    vertical_offsets_in = (
        long_offsets_in if vertical_leg == "long" else short_offsets_in
    )
    horizontal_offsets_in = (
        short_offsets_in if vertical_leg == "long" else long_offsets_in
    )
    vertical_z_mm = tuple(z + offset * 25.4 for offset in vertical_offsets_in)
    face = _principal_broad_face(principal, x)
    lines = _grain_edge_lines(face)
    if len(lines) != 2 or abs(lines[0][2] - lines[1][2]) > 1e-5:
        raise ValueError("Expected two parallel principal broad-face grain edges")
    ny = 1 / hypot(1, lines[0][2])

    def edge_bounds(z_mm: float) -> tuple[float, float]:
        lower, upper = sorted(_line_y(line, z_mm) for line in lines)
        return lower + loaded_edge_mm / ny, upper - loaded_edge_mm / ny

    header_bounds = header.BoundingBox()
    lower_y = max(
        header_bounds.ymin + loaded_edge_mm,
        *(edge_bounds(hole_z)[0] for hole_z in vertical_z_mm),
    )
    upper_y = min(
        header_bounds.ymax - loaded_edge_mm,
        *(edge_bounds(hole_z)[1] for hole_z in vertical_z_mm),
    )
    far_lower_line_y = min(_line_y(line, vertical_z_mm[1]) for line in lines)
    far_upper_line_y = max(_line_y(line, vertical_z_mm[1]) for line in lines)
    far_edge_distance = min((y - far_lower_line_y) * ny, (far_upper_line_y - y) * ny)

    bore_fractions = []
    wood_length_mm = 38.1
    for hole_z in vertical_z_mm:
        bore = cq.Solid.makeCylinder(
            wood_hole_radius_mm,
            wood_length_mm,
            cq.Vector(x, y, hole_z),
            cq.Vector(1, 0, 0),
        )
        bore_fractions.append(
            principal.intersect(bore).Volume()
            / (pi * wood_hole_radius_mm**2 * wood_length_mm)
        )
    for offset_in in horizontal_offsets_in:
        bore = cq.Solid.makeCylinder(
            wood_hole_radius_mm,
            wood_length_mm,
            cq.Vector(x - offset_in * 25.4, y, z),
            cq.Vector(0, 0, -1),
        )
        bore_fractions.append(
            header.intersect(bore).Volume()
            / (pi * wood_hole_radius_mm**2 * wood_length_mm)
        )

    end_minimum_mm = 3.5 * bolt_diameter_mm
    vertical_offset_mm = vertical_offsets_in[0] * 25.4
    return {
        "station": station[0],
        "source_cad": "mini_moonboard.compact_floor_flush_frame.uncut_wood_parts() and stations()",
        "placement": f"AB205 bend at header-top/principal-side butt; {vertical_leg} leg vertical, {'short' if vertical_leg == 'long' else 'long'} leg horizontal; hole row at old clip Y",
        "contact_x_mm": round(x, 6),
        "contact_z_mm": round(z, 6),
        "legacy_station_y_mm": round(y, 6),
        "bolt_diameter_mm": bolt_diameter_mm,
        "nominal_bore_diameter_mm": 2 * wood_hole_radius_mm,
        "vertical_hole_offsets_from_bend_in": list(vertical_offsets_in),
        "horizontal_hole_offsets_from_bend_in": list(horizontal_offsets_in),
        "wood_bore_count": len(bore_fractions),
        "wood_bore_full_section_fractions": [
            round(value, 6) for value in bore_fractions
        ],
        "legacy_y_far_principal_4d_reserve_mm": round(
            far_edge_distance - loaded_edge_mm, 6
        ),
        "reversible_4d_y_lower_mm": round(lower_y, 6),
        "reversible_4d_y_upper_mm": round(upper_y, 6),
        "reversible_4d_y_band_width_mm": round(upper_y - lower_y, 6),
        "nearest_principal_hole_vertical_offset_mm": round(vertical_offset_mm, 6),
        "principal_grain_z_component": round(ny, 6),
        "nearest_principal_hole_grain_ray_mm": round(vertical_offset_mm / ny, 6),
        "softwood_loaded_end_minimum_mm": round(end_minimum_mm, 6),
        "principal_end_square_to_grain": abs(ny - 1) < 1e-6,
        "end_distance_classified": False,
        "angle_placement_verified": False,
        "drilling_released": False,
    }
