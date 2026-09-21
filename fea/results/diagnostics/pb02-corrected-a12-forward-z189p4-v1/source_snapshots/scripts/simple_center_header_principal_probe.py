"""One bounded PB-02 header/right-principal bolt geometry trial; no release."""

import csv
import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_link_edge_probe as link
from scripts import simple_center_wide_post_probe as wide

AXIS_X = 65.0
AXIS_Y = -160.0
WASHER_RADIUS = 10.0  # Illustrative envelope, not selected hardware.
TOOL_RADIUS = 20.0
HEADER_BOTTOM = 238.9
HEADER_TOP = 277.0
PRINCIPAL_REAR_Y = -182.7
PRINCIPAL_REAR_TOP_Z = 326.055774
PRINCIPAL_FAR_TOP_Y = 1404.078
PRINCIPAL_FAR_TOP_Z = 2217.10408


def _fixed_screws():
    screws = {}
    counts = {"panel": 0, "kicker": 0}
    with wide.AXES.open(newline="") as handle:
        for row in csv.DictReader(handle):
            name = row["name"]
            if name.startswith("round_panel_"):
                counts["panel"] += 1
            elif name.startswith(("round_kicker_", "kicker_header_")):
                counts["kicker"] += 1
            else:
                continue
            screws[name] = cq.Solid.makeCylinder(
                float(row["modeled_diameter_mm"]) / 2,
                float(row["shop_purchased_length_mm"]),
                cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz")),
                cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz")),
            )
    return counts, screws


def _hits(shape, named_solids):
    return {
        name: round(volume, 5)
        for name, other in named_solids.items()
        if (volume := wide.hit_volume(shape, other)) > wide.TOL
    }


def _parts():
    parts = {part.name: part.shape for part in wide.frame.uncut_wood_parts()}
    parts.pop("base_post_center_right")
    parts.update(
        shifted_right_post=cq.Solid.makeBox(
            88.9,
            88.9,
            wide.POST_TOP,
            cq.Vector(88.75, wide.POST_REAR_Y, 0),
        ),
        backer=wide.BACKER,
        rear_cleat=cq.Solid.makeBox(88.9, 38.1, 460, cq.Vector(89.05, -213.8, 0)),
        upright_side_cleat=link.SIDE,
    )
    return parts


def probe():
    """Screen one full-section vertical bolt without modifying any wood."""
    baseline = link.probe()
    parts = _parts()
    slope = (PRINCIPAL_FAR_TOP_Z - PRINCIPAL_REAR_TOP_Z) / (
        PRINCIPAL_FAR_TOP_Y - PRINCIPAL_REAR_Y
    )
    top_z = PRINCIPAL_REAR_TOP_Z + slope * (AXIS_Y - PRINCIPAL_REAR_Y)
    # Span the full sloped exit, including the high side of the bore.
    bore_top = top_z + abs(slope) * wide.BORE_RADIUS
    bore = cq.Solid.makeCylinder(
        wide.BORE_RADIUS,
        bore_top - HEADER_BOTTOM,
        cq.Vector(AXIS_X, AXIS_Y, HEADER_BOTTOM),
        cq.Vector(0, 0, 1),
    )
    header_segment = cq.Solid.makeCylinder(
        wide.BORE_RADIUS,
        HEADER_TOP - HEADER_BOTTOM,
        cq.Vector(AXIS_X, AXIS_Y, HEADER_BOTTOM),
        cq.Vector(0, 0, 1),
    )
    principal_segment = cq.Solid.makeCylinder(
        wide.BORE_RADIUS,
        bore_top - HEADER_TOP,
        cq.Vector(AXIS_X, AXIS_Y, HEADER_TOP),
        cq.Vector(0, 0, 1),
    )
    top_tool = cq.Solid.makeCylinder(
        TOOL_RADIUS, 20, cq.Vector(AXIS_X, AXIS_Y, top_z), cq.Vector(0, 0, 1)
    )
    bottom_tool = cq.Solid.makeCylinder(
        TOOL_RADIUS, 20, cq.Vector(AXIS_X, AXIS_Y, HEADER_BOTTOM), cq.Vector(0, 0, -1)
    )
    counts, screws = _fixed_screws()
    existing_bores = {
        **{
            f"post_{name}": cq.Solid.makeCylinder(
                wide.BORE_RADIUS, 127, cq.Vector(140, -213.8, z), cq.Vector(0, 1, 0)
            )
            for name, z in zip(("low", "high"), wide.BOLT_Z)
        },
        "upright": cq.Solid.makeCylinder(
            wide.BORE_RADIUS, 127, cq.Vector(50.95, -147.3, 350), cq.Vector(1, 0, 0)
        ),
        "cleat_link": cq.Solid.makeCylinder(
            wide.BORE_RADIUS, 94.9, cq.Vector(133.5, -213.8, 370), cq.Vector(0, 1, 0)
        ),
    }
    excluded = {"base_header", "base_principal_center_right"}
    baseline_clear = (
        baseline["fixed_axes"] == {"panel": 48, "kicker": 18}
        and all(baseline["inner_kicker_edges_supported"].values())
        and set(baseline["center_kicker_screw_receiver_fraction"].values()) == {1.0}
        and all(
            not baseline[key]
            for key in (
                "solid_overlaps_mm3",
                "fixed_screw_hits_mm3",
                "bore_unintended_wood_hits_mm3",
                "bore_pair_hits_mm3",
                "trial_20mm_radius_tool_wood_hits_mm3",
            )
        )
    )
    candidate = {
        "kind": "single full-section vertical through-bolt",
        "axis_xyz_mm": [AXIS_X, AXIS_Y, round(top_z, 5)],
        "bore_diameter_mm": 2 * wide.BORE_RADIUS,
        "fixed_axes": counts,
        "baseline_clear": baseline_clear,
        "header_bore_wood_mm3": round(wide.hit_volume(bore, parts["base_header"]), 5),
        "principal_bore_wood_mm3": round(
            wide.hit_volume(bore, parts["base_principal_center_right"]), 5
        ),
        "header_bore_envelope_received_fraction": round(
            wide.hit_volume(header_segment, parts["base_header"])
            / header_segment.Volume(),
            8,
        ),
        "principal_bore_envelope_received_fraction": round(
            wide.hit_volume(principal_segment, parts["base_principal_center_right"])
            / principal_segment.Volume(),
            8,
        ),
        "wood_overlap_mm3": {},  # No new timber in this full-section pose.
        "bore_fixed_screw_hits_mm3": _hits(bore, screws),
        "bore_other_wood_hits_mm3": _hits(
            bore, {name: wood for name, wood in parts.items() if name not in excluded}
        ),
        "bore_existing_bore_hits_mm3": _hits(bore, existing_bores),
        "bottom_tool_wood_hits_mm3": _hits(bottom_tool, parts),
        "top_vertical_tool_wood_hits_mm3": _hits(top_tool, parts),
        "principal_top_slope_abs_dz_dy": round(abs(slope), 8),
        "top_face_z_variation_across_20mm_washer_mm": round(
            2 * WASHER_RADIUS * abs(slope), 5
        ),
        "status": "rejected",
        "rejection_reason": (
            "The principal's exposed top face is sloped relative to the vertical "
            "through-bolt. An ordinary flat 20-mm washer has no full planar "
            "bearing seat; a coaxial 20-mm-radius straight tool envelope from "
            "the center exit intersects principal wood. A bevel seat or "
            "angled hardware would be a different, untested construction."
        ),
    }
    return {
        "station": "clip_split_base_center_right",
        "pose": "simple_center_link_edge_probe",
        "trials": [candidate],
        "rating_or_drilling_release": False,
        "old_proxy_forces_are_new_demand": False,
        "untried_y_axis_header_bolt_conditional_edge_limit": {
            "basis": "2024 NDS Table 12.5.1C, perpendicular-to-grain loaded edge",
            "nominal_bolt_diameter_mm": 6.35,
            "loaded_edge_4d_mm": 25.4,
            "unloaded_edge_1_5d_mm": 9.525,
            "header_z_thickness_mm": round(HEADER_TOP - HEADER_BOTTOM, 5),
            "minimum_for_reversible_loaded_z_edges_mm": 50.8,
            "symmetric_z_edge_distance_mm": 19.05,
            "shortfall_at_each_symmetric_loaded_edge_mm": 6.35,
            "conclusion": (
                "No Y-axis header bolt center can have 4D to both Z edges "
                "in this 38.1-mm section if either edge may be loaded. "
                "Signed new demand and applicable edge classification remain unknown."
            ),
        },
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
