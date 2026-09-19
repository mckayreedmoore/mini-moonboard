"""Conditional A66 wood-geometry envelope on current raw CAD, not a drill model."""

import json
from math import hypot, isfinite, pi
from pathlib import Path
from typing import Literal

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as frame
from scripts.bolted_candidate_ab205_center_fit import _grain_edge_lines, _line_y

Family = Literal["center", "outer"]
Side = Literal["left", "right"]
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/bolted-candidate-prototypes/a66-feasibility-envelope.json"
BOLT_D_MM = 9.525
BORE_D_MM = 11.1125  # Hypothetical 7/16-inch clearance bore; not a bit instruction.
OFFSET_SEARCH_CAP_MM = (
    149.225  # Retail 5-7/8-inch outside size, not bend-to-hole reach.
)
EDGE_MM = 4 * BOLT_D_MM


def _context(family: Family, side: Side) -> dict:
    if family not in ("center", "outer") or side not in ("left", "right"):
        raise ValueError("Expected center/outer family and left/right side")
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    station_name = (
        f"clip_split_base_center_{side}"
        if family == "center"
        else f"clip_angle_base_{side}"
    )
    station = next(item for item in frame.stations() if item[0] == station_name)
    face_member = parts[
        f"base_principal_center_{side}" if family == "center" else f"base_side_{side}"
    ]
    header = parts["base_header"]
    x = station[1].x
    z = station[1].z
    face = next(
        face
        for face in face_member.Faces()
        if face.Vertices()
        and all(abs(v.Center().x - x) < 1e-5 for v in face.Vertices())
    )
    lines = sorted(_grain_edge_lines(face), key=lambda line: _line_y(line, z))
    if len(lines) != 2 or abs(lines[0][2] - lines[1][2]) > 1e-5:
        raise ValueError("Expected two parallel raw-CAD grain edges")
    slope = lines[0][2]
    if slope <= 0:
        raise ValueError("Expected rising grain edges at this butt")
    ny = 1 / hypot(1, slope)
    vertices = [vertex.Center() for vertex in face.Vertices()]
    center_y = sum(vertex.y for vertex in vertices) / len(vertices)
    center_z = sum(vertex.z for vertex in vertices) / len(vertices)
    polygon_edges = []
    for edge in face.Edges():
        a, b = (vertex.Center() for vertex in edge.Vertices())
        dy, dz = b.y - a.y, b.z - a.z
        if hypot(dy, dz) < 1e-6:
            continue
        # Inward signed distance from each straight boundary of the raw face.
        sign = 1 if dy * (center_z - a.z) - dz * (center_y - a.y) > 0 else -1
        polygon_edges.append((a.y, a.z, dy, dz, sign))
    inward_x = (
        (-1 if side == "left" else 1)
        if family == "center"
        else (1 if side == "left" else -1)
    )
    header_box = header.BoundingBox()
    x_room = x - header_box.xmin if inward_x < 0 else header_box.xmax - x
    return {
        "station": station_name,
        "legacy_y": station[1].y,
        "x": x,
        "z": z,
        "face_member": face_member,
        "header": header,
        "lines": lines,
        "slope": slope,
        "ny": ny,
        "polygon_edges": polygon_edges,
        "inward_x": inward_x,
        "x_room": x_room,
    }


def _vertical_band(context: dict, row_y_mm: float) -> tuple[float, float]:
    """Offset interval from two 4D edge half-planes and raw bottom bore clearance."""
    if not isfinite(row_y_mm):
        raise ValueError("Row must be finite")
    z = context["z"]
    lower_y = _line_y(context["lines"][0], z)
    upper_y = _line_y(context["lines"][1], z)
    slope = context["slope"]
    offset_low = max(
        BORE_D_MM / 2, (row_y_mm - upper_y + EDGE_MM / context["ny"]) / slope
    )
    offset_high = min(
        OFFSET_SEARCH_CAP_MM, (row_y_mm - lower_y - EDGE_MM / context["ny"]) / slope
    )
    radius = BORE_D_MM / 2
    for edge_y, edge_z, dy, dz, sign in context["polygon_edges"]:
        # sign * cross(edge, hole_center - edge_start) >= bore radius * edge length.
        coefficient = sign * dy
        remainder = radius * hypot(dy, dz) - sign * (
            dy * (z - edge_z) - dz * (row_y_mm - edge_y)
        )
        if abs(coefficient) < 1e-9:
            if remainder > 1e-7:
                return (offset_low, min(offset_high, offset_low - 1))
        elif coefficient > 0:
            offset_low = max(offset_low, remainder / coefficient)
        else:
            offset_high = min(offset_high, remainder / coefficient)
    header_box = context["header"].BoundingBox()
    if not header_box.ymin + EDGE_MM <= row_y_mm <= header_box.ymax - EDGE_MM:
        return (offset_low, min(offset_high, offset_low - 1))
    return (offset_low, offset_high)


def envelope(family: Family, side: Side) -> dict:
    """Return one useful Y slice plus exact inequalities for other hypothetical rows."""
    c = _context(family, side)
    sample_offset = OFFSET_SEARCH_CAP_MM / 2
    lower = _line_y(c["lines"][0], c["z"] + sample_offset) + EDGE_MM / c["ny"]
    upper = _line_y(c["lines"][1], c["z"] + sample_offset) - EDGE_MM / c["ny"]
    header_box = c["header"].BoundingBox()
    lower = max(lower, header_box.ymin + EDGE_MM)
    upper = min(upper, header_box.ymax - EDGE_MM)
    if lower > upper:
        raise ValueError("No conditional broad-face row at mid leg")
    row_y = (lower + upper) / 2
    band = _vertical_band(c, row_y)
    return {
        "station": c["station"],
        "raw_cad_source": "mini_moonboard.compact_floor_flush_frame.uncut_wood_parts() and stations()",
        "bend_xyz_mm": [round(c["x"], 6), round(c["legacy_y"], 6), round(c["z"], 6)],
        "face_member": f"base_principal_center_{side}"
        if family == "center"
        else f"base_side_{side}",
        "header_member": "base_header",
        "bolt_diameter_mm": BOLT_D_MM,
        "hypothetical_bore_diameter_mm": BORE_D_MM,
        "reversible_both_edge_boundary_mm": EDGE_MM,
        "grain_edge_slope_dy_dz": round(c["slope"], 9),
        "grain_z_component": round(c["ny"], 9),
        "extended_grain_line_y_at_bend_z_mm": [
            round(_line_y(line, c["z"]), 6) for line in c["lines"]
        ],
        "hypothetical_offset_search_cap_mm": OFFSET_SEARCH_CAP_MM,
        "horizontal_offset_band_mm": [
            round(BORE_D_MM / 2, 6),
            round(min(OFFSET_SEARCH_CAP_MM, c["x_room"] - BORE_D_MM / 2), 6),
        ],
        "example_row_y_mm": round(row_y, 6),
        "example_row_displacement_from_legacy_mm": round(row_y - c["legacy_y"], 6),
        "vertical_offset_band_mm": [round(v, 6) for v in band],
        "legacy_row_vertical_offset_band_mm": [
            round(v, 6) for v in _vertical_band(c, c["legacy_y"])
        ],
        "parameter_rule": (
            "For any row Y, each hypothetical vertical hole offset v from the bend must satisfy "
            "v >= bore_radius, v <= hypothetical_offset_search_cap, full bore circle inside the raw "
            "broad-face polygon, "
            "lower_grain_edge_y(bend_z+v)+4D/grain_z_component <= Y <= "
            "upper_grain_edge_y(bend_z+v)-4D/grain_z_component; "
            "header_ymin+4D <= Y <= header_ymax-4D. "
            "Both vertical offsets must be distinct and inside that same band; "
            "both horizontal offsets must be distinct and inside the horizontal raw-wood band."
        ),
        "oblique_end_grain_ray_at_vertical_offsets_mm": "v / grain_z_component; diagnostic only",
        "square_end_softwood_tension_marker_rays_mm": [
            round(3.5 * BOLT_D_MM, 6),
            round(7 * BOLT_D_MM, 6),
        ],
        "factory_hole_coordinates_known": False,
        "oblique_end_distance_classified": False,
        "connector_strength_classified": False,
        "drilling_released": False,
    }


def trial(
    family: Family,
    side: Side,
    row_y_mm: float,
    vertical_offsets_mm: tuple[float, float],
    horizontal_offsets_mm: tuple[float, float],
) -> dict:
    """Check a hypothetical four-axis set against full raw CAD wood volumes."""
    values = (*vertical_offsets_mm, *horizontal_offsets_mm)
    if not isfinite(row_y_mm) or any(not isfinite(v) or v < 0 for v in values):
        raise ValueError("Row must be finite; offsets finite and nonnegative")
    if (
        not vertical_offsets_mm[0] < vertical_offsets_mm[1]
        or not horizontal_offsets_mm[0] < horizontal_offsets_mm[1]
    ):
        raise ValueError("Each offset pair must be strictly increasing")
    c = _context(family, side)
    band = _vertical_band(c, row_y_mm)
    horizontal_band = (
        BORE_D_MM / 2,
        min(OFFSET_SEARCH_CAP_MM, c["x_room"] - BORE_D_MM / 2),
    )
    face_box = c["face_member"].BoundingBox()
    header_box = c["header"].BoundingBox()
    face_direction = 1 if abs(c["x"] - face_box.xmin) < 1e-5 else -1
    radius = BORE_D_MM / 2
    bores = [
        cq.Solid.makeCylinder(
            radius,
            face_box.xlen,
            cq.Vector(c["x"], row_y_mm, c["z"] + v),
            cq.Vector(face_direction, 0, 0),
        )
        for v in vertical_offsets_mm
    ] + [
        cq.Solid.makeCylinder(
            radius,
            header_box.zlen,
            cq.Vector(c["x"] + c["inward_x"] * h, row_y_mm, c["z"]),
            cq.Vector(0, 0, -1),
        )
        for h in horizontal_offsets_mm
    ]
    receivers = (c["face_member"], c["face_member"], c["header"], c["header"])
    lengths = (face_box.xlen, face_box.xlen, header_box.zlen, header_box.zlen)
    fractions = [
        bore.intersect(receiver).Volume() / (pi * radius**2 * length)
        for bore, receiver, length in zip(bores, receivers, lengths, strict=True)
    ]
    in_band = all(band[0] <= v <= band[1] for v in vertical_offsets_mm) and all(
        horizontal_band[0] <= h <= horizontal_band[1] for h in horizontal_offsets_mm
    )
    return {
        "station": c["station"],
        "hypothetical_row_y_mm": row_y_mm,
        "hypothetical_vertical_offsets_mm": list(vertical_offsets_mm),
        "hypothetical_horizontal_offsets_mm": list(horizontal_offsets_mm),
        "hypothetical_horizontal_axis_x_mm": [
            round(c["x"] + c["inward_x"] * h, 6) for h in horizontal_offsets_mm
        ],
        "raw_wood_bore_fractions": [round(v, 6) for v in fractions],
        "vertical_offset_band_mm": [round(v, 6) for v in band],
        "horizontal_offset_band_mm": [round(v, 6) for v in horizontal_band],
        "oblique_end_grain_rays_mm": [
            round(v / c["ny"], 6) for v in vertical_offsets_mm
        ],
        "conditional_wood_geometry": in_band and all(v >= 1 - 1e-5 for v in fractions),
        "oblique_end_distance_classified": False,
        "connector_strength_classified": False,
        "drilling_released": False,
    }


def main() -> None:
    """Regenerate the bounded report without selecting factory coordinates."""
    records = [
        envelope(family, side)
        for family in ("center", "outer")
        for side in ("left", "right")
    ]
    report = {
        "title": "Conditional A66 wood-geometry feasibility envelope",
        "scope": "Actual center and outer joints on current raw CAD; hypothetical factory offsets from bend only",
        "basis": (
            "2024 NDS Table 12.5.1C reversible 4D possibly loaded-edge diagnostic "
            "on both broad-face grain edges for a 3/8-inch bolt. "
            "Table 12.5.1A 3.5D (reduced factor) and 7D (full factor) "
            "softwood parallel-to-grain tension square-end markers are shown only as rays, "
            "not applied to oblique ends."
        ),
        "nds_chapter_12_url": (
            "https://awc.org/wp-content/uploads/2026/08/"
            "AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-"
            "%E2%80%93-Dowel-type-fasteners.pdf"
        ),
        "assumption_sources": {
            "offset_search_cap": (
                "149.225 mm = 5-7/8 in retailer-listed A66 outside leg size, "
                "docs/bolted-candidate-prototypes/simpson-a66-retail.json product.dimensions_in; "
                "https://www.homedepot.ca/product/1000170470. No manufacturer-confirmed "
                "bend-to-hole usable extent; this is only a hypothetical search cap."
            ),
            "bore_diameter": (
                "11.1125 mm = 7/16 in assumed clearance cylinder for a 3/8-in bolt, "
                "consistent with the project's modeled clearance convention in "
                "mini_moonboard/product_frame.py BOLT_HOLE_DIAMETER_MM. "
                "No A66 wood-bore diameter or drill bit is specified here."
            ),
        },
        "factory_pattern": "Unknown: no vertical, horizontal, transverse hole offsets or pitch adopted",
        "geometry_records": records,
        "interpretation": (
            "A nonempty band means some hypothetical offsets could preserve full raw wood and "
            "the reversible both-edge centerline boundary. It does not establish actual A66 hole fit, "
            "NDS oblique end distance, load direction, bolt spacing, plate/washer access, "
            "retained-axis clearance, strength, or a drilling layout."
        ),
        "oblique_end_distance_classified": False,
        "connector_strength_classified": False,
        "drilling_released": False,
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
