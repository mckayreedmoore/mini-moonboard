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
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
OFFICIAL_AXES = ROOT / "docs/floor-flush-construction/connection-axes.csv"
CENTER_MEMBERS = {
    "base_principal_center_left",
    "base_principal_center_right",
    "base_post_center_left",
    "base_post_center_right",
}
INNER_RAILS = {
    f"base_rail_{band}_{side}"
    for band in ("bottom", "service_lower", "service_upper")
    for side in ("left", "right")
}
SUPPORT_WIDTH_MM = 38.1
BASELINE_CLEAR_GAP_MM = 101.9
BASELINE_PANEL_OVERHANG_MM = 50.95
_AXIS_GEOMETRY_FIELDS = (
    "kind",
    "first_member",
    "second_member",
    "start_x_mm",
    "start_y_mm",
    "start_z_mm",
    "direction_x",
    "direction_y",
    "direction_z",
    "modeled_length_mm",
    "modeled_diameter_mm",
    "occupied_length_mm",
    "occupied_diameter_mm",
    "shop_opening_kind",
    "shop_finished_opening_min_mm",
    "shop_finished_opening_max_mm",
)


def _same_axis_geometry(
    left: list[dict[str, str]], right: list[dict[str, str]]
) -> bool:
    """Compare axis identity and geometry, excluding packet-specific prose."""

    def keyed(rows: list[dict[str, str]]) -> dict[str, tuple[str, ...]]:
        return {
            row["name"]: tuple(row[field] for field in _AXIS_GEOMETRY_FIELDS)
            for row in rows
        }

    left_by_name = keyed(left)
    right_by_name = keyed(right)
    return (
        len(left_by_name) == len(left)
        and len(right_by_name) == len(right)
        and left_by_name == right_by_name
    )


def _panel_axes(path: Path, members: set[str]) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if row["shop_opening_kind"] == "hillman_panel"
            and row["second_member"] in members]


def _center_panel_axes() -> list[dict[str, str]]:
    return _panel_axes(AXES, CENTER_MEMBERS)


def _rail_panel_axes() -> list[dict[str, str]]:
    return _panel_axes(AXES, INNER_RAILS)


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
    rails = {part.name: part.shape for part in baseline.uncut_wood_parts()
             if part.name in INNER_RAILS}
    if set(rails) != INNER_RAILS:
        raise ValueError("baseline center-adjacent rail inventory changed")
    rail_rows = _rail_panel_axes()
    if len(rail_rows) != 12 or {row["second_member"] for row in rail_rows} != INNER_RAILS:
        raise ValueError("frozen center-adjacent rail panel-axis schedule changed")
    if not _same_axis_geometry(
        rows + rail_rows,
        _panel_axes(OFFICIAL_AXES, CENTER_MEMBERS)
        + _panel_axes(OFFICIAL_AXES, INNER_RAILS),
    ):
        raise ValueError("official/kerf-right relevant panel axes diverged")
    rail_cylinders = [(row, _occupied_cylinder(row)) for row in rail_rows]
    rail_edges = {name: round(shape.BoundingBox().xmax if name.endswith("left")
                              else shape.BoundingBox().xmin, 4)
                  for name, shape in sorted(rails.items())}
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
        recut_rails = {}
        for name, shape in rails.items():
            bounds = shape.BoundingBox()
            x0 = bounds.xmin if name.endswith("left") else bounds.xmin + delta
            x1 = bounds.xmax - delta if name.endswith("left") else bounds.xmax
            keep = cq.Solid.makeBox(x1 - x0, bounds.ylen + 2, bounds.zlen + 2,
                                    cq.Vector(x0, bounds.ymin - 1, bounds.zmin - 1))
            recut_rails[name] = shape.intersect(keep)
        rail_volumes = [recut_rails[row["second_member"]].intersect(cylinder).Volume()
                        for row, cylinder in rail_cylinders]
        rail_faces_follow = all(
            abs((shape.BoundingBox().xmax if name.endswith("left")
                 else shape.BoundingBox().xmin) -
                (translated[f"base_principal_center_{'left' if name.endswith('left') else 'right'}"]
                 .BoundingBox().xmin if name.endswith("left") else
                 translated["base_principal_center_right"].BoundingBox().xmax)) < 1e-5
            for name, shape in recut_rails.items()
        )
        samples.append({
            "delta_mm": delta,
            "clear_gap_mm": round(BASELINE_CLEAR_GAP_MM + 2 * delta, 4),
            "panel_seam_overhang_mm": round(BASELINE_PANEL_OVERHANG_MM + delta, 4),
            "minimum_nominal_bore_edge_material_mm": round(edge_material, 4),
            "geometrically_inside_support": edge_material > 0,
            "axes_intersecting_shifted_timber": sum(volume > 1e-6 for volume in volumes),
            "minimum_intersection_volume_mm3": round(min(volumes), 4),
            "rail_axes_intersecting_recut_timber": sum(volume > 1e-6 for volume in rail_volumes),
            "minimum_rail_axis_intersection_volume_mm3": round(min(rail_volumes), 4),
            "rail_end_faces_follow_shifted_supports": rail_faces_follow,
        })
    return {
        "status": "geometry_screen_only",
        "baseline_candidate": baseline.KEY,
        "panel_axis_source": str(AXES.relative_to(ROOT)),
        "official_width_relevant_axes_identical": True,
        "center_panel_axis_count": len(rows),
        "center_members": sorted(CENTER_MEMBERS),
        "dependent_center_clip_station_count": len(dependent_stations),
        "dependent_lower_rail_inner_edges_mm": rail_inner_edges,
        "dependent_rail_inner_edges_mm": rail_edges,
        "dependent_rail_panel_axis_count": len(rail_rows),
        "selected_offset_mm": None,
        "samples": samples,
        "limitations": [
            "Nominal occupied cylinders are historical SPAX envelopes, not delivered Hillman screw dimensions.",
            "A positive cylinder/timber overlap does not establish screw engagement or edge-distance capacity.",
            "Connector hole coordinates, installed hardware envelopes, panel seam support, and structural rail-to-principal interfaces remain unverified.",
            "A real shift must recheck twelve center-receiver clip stations and recut six center-adjacent rail inner ends; this screen checks only nominal face alignment and retained screw-cylinder intersection.",
            "This screen shifts center principals and posts together, so it does not separate their opposed header bolt axes; a post-only de-stacking trial is a distinct geometry problem.",
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
