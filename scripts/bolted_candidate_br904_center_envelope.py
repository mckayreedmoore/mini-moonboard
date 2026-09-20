"""Conditional BR904 center-hole search envelope, not an installed detail."""

from math import hypot, isfinite

from mini_moonboard import compact_floor_flush_frame as frame
from scripts.bolted_candidate_ab205_center_fit import (
    _grain_edge_lines,
    _grain_ray_to_face_boundary,
    _line_y,
    _principal_broad_face,
)

FACTORY_HOLE_DIAMETER_MM = 14.2875
FACTORY_PITCH_MM = 47.625


def screen_center_envelope(
    bolt_diameter_mm: float,
    first_vertical_offset_mm: float,
    first_horizontal_offset_mm: float,
) -> dict[str, object]:
    """Screen two assumed factory offsets without claiming they exist on BR904.

    The 4D reversible edge rule and 3.5D oblique grain ray are search filters,
    not classified NDS acceptance rules for this actual joint.
    """
    values = (bolt_diameter_mm, first_vertical_offset_mm, first_horizontal_offset_mm)
    if any(
        isinstance(value, bool) or not isfinite(value) or value <= 0 for value in values
    ):
        raise ValueError("Trial diameters and offsets must be positive and finite")
    if bolt_diameter_mm > FACTORY_HOLE_DIAMETER_MM:
        raise ValueError("Trial bolt diameter exceeds stated factory hole diameter")

    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    principal = parts["base_principal_center_left"]
    header = parts["base_header"]
    x = principal.BoundingBox().xmin
    z = header.BoundingBox().zmax
    face = _principal_broad_face(principal, x)
    lines = _grain_edge_lines(face)
    if len(lines) != 2 or abs(lines[0][2] - lines[1][2]) > 1e-5:
        raise ValueError("Expected two parallel principal grain edges")
    grain_z = 1 / hypot(1, lines[0][2])
    # Applying the advertised pitch independently to both legs is a trial
    # assumption, not a dimensioned factory pattern.
    vertical_z = (
        z + first_vertical_offset_mm,
        z + first_vertical_offset_mm + FACTORY_PITCH_MM,
    )
    edge_screen_mm = 4 * bolt_diameter_mm

    def edge_bounds(hole_z: float) -> tuple[float, float]:
        lower, upper = sorted(_line_y(line, hole_z) for line in lines)
        return lower + edge_screen_mm / grain_z, upper - edge_screen_mm / grain_z

    header_bounds = header.BoundingBox()
    lower_y = max(
        header_bounds.ymin + edge_screen_mm,
        *(edge_bounds(hole_z)[0] for hole_z in vertical_z),
    )
    upper_y = min(
        header_bounds.ymax - edge_screen_mm,
        *(edge_bounds(hole_z)[1] for hole_z in vertical_z),
    )
    row_y = (lower_y + upper_y) / 2
    ray_mm, _, _ = _grain_ray_to_face_boundary(face, row_y, vertical_z[0], lines[0][2])
    ray_filter_mm = 3.5 * bolt_diameter_mm
    radial_play_mm = (FACTORY_HOLE_DIAMETER_MM - bolt_diameter_mm) / 2
    return {
        "product": "Newhouse BR904",
        "station": "clip_split_base_center_left",
        "pose": "trial top principal/header BR904; mirrored lower post/header BR904; shared header axes proposed",
        "source_cad": "mini_moonboard.compact_floor_flush_frame.uncut_wood_parts()",
        "contact_x_mm": round(x, 6),
        "contact_z_mm": round(z, 6),
        "bolt_diameter_mm": bolt_diameter_mm,
        "factory_hole_diameter_mm": FACTORY_HOLE_DIAMETER_MM,
        "factory_hole_minus_bolt_diameter_mm": round(
            FACTORY_HOLE_DIAMETER_MM - bolt_diameter_mm, 6
        ),
        "factory_hole_radial_clearance_mm": round(radial_play_mm, 6),
        "hole_pitch_mm": FACTORY_PITCH_MM,
        "pitch_applies_to_both_legs_verified": False,
        "first_vertical_offset_from_bend_mm": first_vertical_offset_mm,
        "first_horizontal_offset_from_bend_mm": first_horizontal_offset_mm,
        "factory_vertical_offset_verified": False,
        "factory_horizontal_offset_verified": False,
        "vertical_principal_hole_z_mm": [round(value, 6) for value in vertical_z],
        "shared_header_hole_x_mm": [
            round(x - first_horizontal_offset_mm, 6),
            round(x - first_horizontal_offset_mm - FACTORY_PITCH_MM, 6),
        ],
        "trial_row_y_mm": round(row_y, 6),
        "reversible_4d_lower_y_mm": round(lower_y, 6),
        "reversible_4d_upper_y_mm": round(upper_y, 6),
        "reversible_4d_band_width_mm": round(upper_y - lower_y, 6),
        "maximum_symmetric_row_allowance_mm": round((upper_y - lower_y) / 2, 6),
        "nearest_grain_ray_to_oblique_end_mm": round(ray_mm, 6),
        "grain_ray_proxy_threshold_mm": round(ray_filter_mm, 6),
        "nearest_ray_proxy_margin_mm": round(ray_mm - ray_filter_mm, 6),
        "ray_proxy_margin_after_radial_hole_play_mm": round(
            ray_mm - ray_filter_mm - radial_play_mm, 6
        ),
        "end_distance_classified": False,
        "factory_leg_size_or_bend_verified": False,
        "steel_wood_and_tool_fit_verified": False,
        "drilling_released": False,
    }
