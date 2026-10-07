"""Screen unused B104 holes against frozen cached bodies, without rebuilding CAD.

This is an unadopted geometric proposal. No capacity, fabrication or tool access
is inferred; changes to current bolts/holes remain outside the frozen model.
"""

from __future__ import annotations

import copy
import json
from collections import defaultdict
from pathlib import Path

import cadquery as cq

from scripts import hl35_candidate as shared
from scripts import thin_bolted_model as model
from scripts import thin_bolted_occupied as occupied

PACKET = model.LAYOUT.parent
MANIFEST = PACKET / "native-geometry-v4.json"
OUTPUT = PACKET / "b104-near-hole-proposal-v4.json"


def main() -> None:
    layout = model.source_layout()
    manifest = json.loads(MANIFEST.read_text())
    for name, digest in manifest["source_sha256"].items():
        if shared.sha(shared.ROOT / name) != digest:
            raise ValueError(f"cache source differs: {name}")
    parts = {r["id"]: r for r in manifest["parts"]}
    raw_rows = {r["member"]: r for r in manifest["raw_parts"]}
    loaded = {}

    def body(row: dict) -> cq.Shape:
        name = row["id"]
        if name not in loaded:
            path = shared.ROOT / row["path"]
            if shared.sha(path) != row["sha256"]:
                raise ValueError(f"cache body differs: {name}")
            loaded[name] = cq.Shape.importBrep(str(path))
        return loaded[name]

    def overlaps(a: cq.Shape, row: dict) -> float:
        b = a.BoundingBox()
        bounds = [(b.xmin, b.xmax), (b.ymin, b.ymax), (b.zmin, b.zmax)]
        if any(hi < low - 1e-6 or lo > high + 1e-6
               for (lo, hi), (low, high) in zip(bounds, row["bounds_xyz_mm"], strict=True)):
            return 0.
        return shared.overlaps(a, body(row))

    groups = defaultdict(list)
    for fitting in layout["raw_fittings"]:
        if not fitting["angle_id"].startswith("B104ZN_"):
            continue
        for old in fitting["holes"]:
            along = cq.Vector(*(fitting["u_xyz"] if old["flange"] == "beam" else fitting["v_xyz"]))
            point = cq.Vector(*old["entry_xyz_mm"]) - along.multiply(47.625)
            direction = cq.Vector(*old["axis_xyz"])
            item = {**old, "entry_xyz_mm": shared.xyz(point),
                    "angle_id": fitting["angle_id"], "duty_id": fitting["duty_id"],
                    "offset_from_assumed_outer_corner_mm": old["offset_from_assumed_outer_corner_mm"] - 47.625}
            groups[shared.line_key(old["receiver"], point, direction)].append(item)

    half = copy.deepcopy(next(a["hardware_scenario"] for a in layout["installed_axes"]
                              if a["source"] == "new_factory_fitting_axis"))
    small = copy.deepcopy(next(a["hardware_scenario"] for a in layout["installed_axes"]
                               if a["diameter_mm"] < 10))
    small["available_nominal_lengths_mm"] = [63.5, 76.2, 101.6, 114.3, 127.]
    rows = []
    for index, attachments in enumerate(groups.values(), 1):
        first = attachments[0]
        receiver = first["receiver"]
        raw = body(raw_rows[receiver])
        point = cq.Vector(*first["entry_xyz_mm"])
        direction = cq.Vector(*first["axis_xyz"])
        near, far = occupied.geometry_tools.line_span(raw, point, direction)
        point += direction.multiply(near)
        grip = far - near
        before = after = 0.
        for attachment in attachments:
            distance = (cq.Vector(*attachment["entry_xyz_mm"]) - point).dot(direction)
            if abs(distance) < 1e-5:
                before = 5.55625
            elif abs(distance - grip) < 1e-5:
                after = 5.55625
            else:
                raise ValueError("near flange leaves raw receiver face")
        grain = cq.Vector(*raw_rows[receiver]["grain_axis_xyz"])
        midpoint = point + direction.multiply(grip / 2)
        ends = occupied.geometry_tools.line_span(raw, midpoint, grain)
        # This finished ray may meet a cut/hole; it does not classify an end.
        finished_ends = occupied.geometry_tools.line_span(body(parts[receiver]), midpoint, grain)
        scenarios = []
        for label, diameter, bore_diameter, hardware in (
            ("half_large_washers", 12.7, 14.2875, half),
            ("three_eighth_reference_washers", 9.525, 11.1125, small),
        ):
            axis = {"id": f"proposal_near_{index:03d}", "point": point, "direction": direction,
                    "grip_mm": grip, "before_plate_mm": before, "after_plate_mm": after,
                    "diameter_mm": diameter, "hardware_scenario": copy.deepcopy(hardware)}
            plane = cq.Plane(origin=point, normal=direction)
            hardware_parts = [(role, solid.moved(plane.location))
                              for role, solid in occupied.local_hardware(axis)]
            bore = cq.Solid.makeCylinder(bore_diameter / 2, grip, point, direction)
            hits = []
            for role, shape in hardware_parts:
                for name, obstacle in parts.items():
                    if name == receiver and role == "shaft":
                        continue  # proposed receiver bore is intentional
                    volume = overlaps(shape, obstacle)
                    if volume > .01:
                        hits.append({"role": role, "obstacle": name, "kind": obstacle["kind"],
                                     "intersection_mm3": round(volume, 6)})
            seats = []
            for side, at, inward in (("head", point, direction),
                                      ("nut", point + direction.multiply(grip), direction.multiply(-1))):
                support = next((a["angle_id"] for a in attachments
                                if (cq.Vector(*a["entry_xyz_mm"]) - at).Length < 1e-5), receiver)
                if support != receiver:
                    at -= inward.multiply(5.55625)
                skin = cq.Solid.makeCylinder(hardware["washer_od_mm"] / 2, .05, at, inward).cut(
                    cq.Solid.makeCylinder(hardware["washer_id_mm"] / 2, .05, at, inward))
                seats.append({"side": side, "support": support,
                              "annulus_backed_fraction": min(1., overlaps(skin, parts[support]) / skin.Volume())})
            scenarios.append({"label": label, "diameter_mm": diameter,
                              "wood_bore_mm": bore_diameter, "steel_existing_bore_mm": 14.2875,
                              "nominal_length_mm": axis["nominal_under_head_length_mm"],
                              "finished_receiver_bore_fraction": overlaps(bore, parts[receiver]) / bore.Volume(),
                              "raw_receiver_bore_fraction": shared.overlaps(bore, raw) / bore.Volume(),
                              "washer_seats": seats, "occupied_hits": hits,
                              "delivered_thread_window_qualified": False})
        rows.append({"axis_id": f"proposal_near_{index:03d}", "receiver": receiver,
                     "point_xyz_mm": shared.xyz(point), "direction_xyz": shared.xyz(direction),
                     "raw_grip_mm": grip, "attachments": attachments,
                     "parallel_grain_near_far_pitch_mm": 47.625,
                     "raw_grain_end_ray_mm": [-ends[0], ends[1]],
                     "finished_first_grain_boundaries_mm": [-finished_ends[0], finished_ends[1]],
                     "width_edge_distance_mm": first["width_edge_distance_mm"],
                     "formal_end_category_and_load_direction": None, "scenarios": scenarios})
        print(f"Screened near axis {index}/{len(groups)}", flush=True)
    report = {"schema": "thin-b104-near-hole-proposal-v1", "candidate": model.CANDIDATE,
              "scope": "unadopted additional-hole feasibility; existing cache only",
              "source_sha256": {str(model.LAYOUT.relative_to(shared.ROOT)): shared.sha(model.LAYOUT),
                                str(MANIFEST.relative_to(shared.ROOT)): shared.sha(MANIFEST),
                                str(Path(__file__).relative_to(shared.ROOT)): shared.sha(Path(__file__)),
                                "scripts/thin_bolted_occupied.py": shared.sha(shared.ROOT / "scripts/thin_bolted_occupied.py")},
              "counts": {"new_flange_attachments": sum(map(len, groups.values())),
                         "new_physical_axes": len(groups), "shared_new_axes": sum(len(v) > 1 for v in groups.values())},
              "rows": rows,
              "limits": ["No current holes, hardware, wood or panel/screw counts changed.",
                         "47.625mm fails the half-inch 4D=50.8mm parallel-grain spacing criterion.",
                         "Three-eighth mixed-diameter spacing and oversized steel-hole stiffness are unqualified.",
                         "Initial nominal occupancy and sampled/ray boundaries do not establish installation/tool/removal access.",
                         "No force-couple demand, resistance or full-joint rotational restraint accepted.",
                         "B103 short post flange still has only one factory hole."],
              "reproduce": ".venv/bin/python -m scripts.thin_bolted_near_hole_proposal"}
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(str(OUTPUT), flush=True)


if __name__ == "__main__":
    main()
