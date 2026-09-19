"""Screen an outward center-support shift against frozen panel screw axes.

This only intersects nominal occupied screw cylinders with uncut timber. It
does not model connector holes, timber capacity, or panel bending resistance.
"""

import argparse
import csv
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as baseline

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction/connection-axes.csv"
CENTER_MEMBERS = {
    "base_principal_center_left",
    "base_principal_center_right",
    "base_post_center_left",
    "base_post_center_right",
}
SUPPORT_WIDTH_MM = 38.1
BASELINE_CLEAR_GAP_MM = 101.9
BASELINE_PANEL_OVERHANG_MM = 50.95


def _center_panel_axes() -> list[dict[str, str]]:
    with AXES.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if row["shop_opening_kind"] == "hillman_panel"
            and row["second_member"] in CENTER_MEMBERS]


def _occupied_cylinder(row: dict[str, str]) -> cq.Solid:
    start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
    direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
    return cq.Solid.makeCylinder(float(row["occupied_diameter_mm"]) / 2,
                                 float(row["occupied_length_mm"]), start, direction)


def screen_center_shift(deltas_mm: tuple[float, ...] = (0, 5, 10, 15)) -> dict[str, object]:
    """Check retained screw-axis contact, not a structurally permissible offset."""
    if any(not math.isfinite(delta) or delta < 0 for delta in deltas_mm):
        raise ValueError("center shift deltas must be nonnegative and finite")
    rows = _center_panel_axes()
    if len(rows) != 20 or {row["second_member"] for row in rows} != CENTER_MEMBERS:
        raise ValueError("frozen center panel-axis schedule changed")
    wood = {part.name: part.shape for part in baseline.uncut_wood_parts()
            if part.name in CENTER_MEMBERS}
    dependent_stations = [station for station in baseline.stations()
                          if station[5] in CENTER_MEMBERS]
    lower_rails = {part.name: part.shape.BoundingBox()
                   for part in baseline.uncut_wood_parts()
                   if part.name in {"base_rail_bottom_left", "base_rail_bottom_right"}}
    rail_inner_edges = [round(lower_rails["base_rail_bottom_left"].xmax, 4),
                        round(lower_rails["base_rail_bottom_right"].xmin, 4)]
    cylinders = [(row, _occupied_cylinder(row)) for row in rows]
    radii = [float(row["occupied_diameter_mm"]) / 2 for row in rows]
    samples = []
    for delta in deltas_mm:
        translated = {name: shape.translate((-delta if name.endswith("left") else delta, 0, 0))
                      for name, shape in wood.items()}
        volumes = [translated[row["second_member"]].intersect(cylinder).Volume()
                   for row, cylinder in cylinders]
        edge_material = SUPPORT_WIDTH_MM / 2 - delta - max(radii)
        samples.append({
            "delta_mm": delta,
            "clear_gap_mm": round(BASELINE_CLEAR_GAP_MM + 2 * delta, 4),
            "panel_seam_overhang_mm": round(BASELINE_PANEL_OVERHANG_MM + delta, 4),
            "minimum_nominal_bore_edge_material_mm": round(edge_material, 4),
            "geometrically_inside_support": edge_material > 0,
            "axes_intersecting_shifted_timber": sum(volume > 1e-6 for volume in volumes),
            "minimum_intersection_volume_mm3": round(min(volumes), 4),
        })
    return {
        "status": "geometry_screen_only",
        "baseline_candidate": baseline.KEY,
        "panel_axis_source": str(AXES.relative_to(ROOT)),
        "center_panel_axis_count": len(rows),
        "center_members": sorted(CENTER_MEMBERS),
        "dependent_center_clip_station_count": len(dependent_stations),
        "dependent_lower_rail_inner_edges_mm": rail_inner_edges,
        "selected_offset_mm": None,
        "samples": samples,
        "limitations": [
            "Nominal occupied cylinders are historical SPAX envelopes, not delivered Hillman screw dimensions.",
            "A positive cylinder/timber overlap does not establish screw engagement or edge-distance capacity.",
            "Connector hole coordinates, installed hardware envelopes, panel seam support, and lower-rail interfaces remain unverified.",
            "A real shift must recheck twelve center-receiver clip stations and recut the two lower rail inner ends; this screen does neither.",
            "The selected baseline and panel screw axes have not moved.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(screen_center_shift(), indent=2) + "\n")


if __name__ == "__main__":
    main()
