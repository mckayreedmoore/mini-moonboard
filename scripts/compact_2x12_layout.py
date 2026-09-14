"""Small geometric screen for unbraced single-2x12 leg candidates.

This is a placement/stock-length calculation, not a resistance assessment.
It retains a centered single row along the existing 4x6 rim grain. Actual CAD
must check other openings, all washer seats and the rebuilt load path.
"""
import json
import math

RIM_ANGLE_DEG = 40.0
REFERENCE_CENTRE_YZ_MM = (1129.3450496754274, 1781.022923085547)
BOLT_DIAMETER_MM = 12.7
ALLOWANCE_MM = 3.0
LEG_DEPTH_MM = 285.75
LEG_WIDTH_MM = 38.1
RIM_DEPTH_MM = 139.7


def layout(shift_mm, lean_deg, pitch_mm, top_extension_mm, count=4, local_offsets=None):
    """Rear lean is positive; the top is square to leg grain, foot horizontal."""
    angle = math.radians(RIM_ANGLE_DEG)
    lean = math.radians(lean_deg)
    included = angle + lean
    rim = (math.sin(angle), math.cos(angle))
    centre = tuple(value + shift_mm * direction for value, direction
                   in zip(REFERENCE_CENTRE_YZ_MM, rim, strict=True))
    offsets = [(i - (count - 1) / 2) * (pitch_mm or 0) for i in range(count)]
    coords = local_offsets or [(offset, 0.0) for offset in offsets]
    leg_s = [s * math.cos(included) - q * math.sin(included) for s, q in coords]
    leg_q = [s * math.sin(included) + q * math.cos(included) for s, q in coords]
    end_margin = (top_extension_mm - max(leg_s)
                  - 7 * BOLT_DIAMETER_MM - ALLOWANCE_MM)
    leg_margin = (LEG_DEPTH_MM / 2 - max(abs(q) for q in leg_q)
                  - 4 * BOLT_DIAMETER_MM - ALLOWANCE_MM)
    rim_margin = (RIM_DEPTH_MM / 2 - max(abs(q) for _, q in coords)
                  - 4 * BOLT_DIAMETER_MM - ALLOWANCE_MM)
    spread = max(leg_q) - min(leg_q)
    min_spacing = min(math.hypot(s1 - s2, q1 - q2)
                      for i, (s1, q1) in enumerate(coords) for s2, q2 in coords[i + 1:])
    length = (centre[1] / math.cos(lean) + top_extension_mm
              + LEG_DEPTH_MM / 2 * math.tan(lean))
    return {
        'attachment_shift_along_rim_mm': shift_mm,
        'rear_lean_from_vertical_degrees': lean_deg,
        'bolt_count_per_leg': count,
        'bolt_diameter_mm': BOLT_DIAMETER_MM,
        'pitch_along_rim_mm': pitch_mm,
        'centre_yz_mm': centre,
        'rim_local_offsets_sq_mm': coords,
        'bolt_centres_yz_mm': [[centre[0] + s * rim[0] + q * rim[1],
                                centre[1] + s * rim[1] - q * rim[0]] for s, q in coords],
        'foot_centre_y_mm': centre[0] + centre[1] * math.tan(lean),
        'leg_top_above_group_along_grain_mm': top_extension_mm,
        'stock_length_mm': length,
        'full_length_weak_axis_slenderness': length / LEG_WIDTH_MM,
        'leg_adjusted_loaded_edge_margin_mm': leg_margin,
        'rim_adjusted_loaded_edge_margin_mm': rim_margin,
        'leg_adjusted_top_end_margin_mm': end_margin,
        'bolt_4d_spacing_margin_mm': min_spacing - 4 * BOLT_DIAMETER_MM,
        'adjusted_pair_spacing_margin_mm': min_spacing - 4 * BOLT_DIAMETER_MM - 2,
        'leg_cross_grain_spread_mm': spread,
        'adjusted_cross_grain_spread_margin_mm': 127 - spread - 2,
        'geometric_screen_passes': min(end_margin, leg_margin, rim_margin) >= 0
            and min_spacing >= 4 * BOLT_DIAMETER_MM + 2 and spread <= 125
            and length / LEG_WIDTH_MM <= 50,
    }


def main():
    print(json.dumps({
        'scope': 'Placement and stock length only; no structural acceptance transfers.',
        'corrected_staggered': layout(-225.0, 17.5, None, 150.0,
                                     local_offsets=[(-81, 13), (-27, 3), (27, -3), (81, -13)]),
        'original_cross_grain_failure': layout(-225.0, 17.5, 65.0, 150.0),
        'alternative': layout(-175.0, 13.837, 68.0, 158.0),
        'unlowered_control': layout(0.0, 13.837, 68.0, 158.0),
    }, indent=2))


if __name__ == '__main__':
    main()
