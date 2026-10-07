"""Build the mixed-factory-angle thin-frame raw-geometry comparison.

This preserves the original timber sections and all older candidates. A raw
geometry comparison is not a finished model, resistance assessment or release.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import hl35_candidate as shared
from scripts import thin_bolted_fitting_screen as screen

ROOT = shared.ROOT
PACKET = screen.PACKET
REVISION = "thin-mixed-far-hole-raw-v2"
BOTTOM_SHIFT_MM = 50.8
T = cq.Vector(0, math.sin(math.radians(40)), math.cos(math.radians(40)))
B103 = screen.Fitting("B103ZN", 4.125 * screen.INCH, 1.625 * screen.INCH,
                      2, 1, 3.53, .56)
PRICE_URLS = {
    "B104ZN": "https://www.platt.com/p/0151375/eaton-b-line/four-hole-corner-angle-steel-zinc-plated/781011500436/blib104zn",
    "B103ZN": "https://www.platt.com/p/0151547/eaton-b-line/three-hole-corner-angle-zinc-plated/781011500337/blib103zn",
}


def geometry() -> tuple[dict[str, cq.Shape], list[tuple[shared.Angle, screen.Fitting]], dict]:
    """Raw wood and installed envelopes, without services/bores or washers."""
    snapshot, inventory, _ = shared.load_sources()
    frame = variant(KERF_RIGHT)
    parts = frame.uncut_wood_parts()
    wood = {p.name: p.shape for p in parts}
    for name in ("base_rail_bottom_left", "base_rail_bottom_right"):
        wood[name] = wood[name].translate(T.multiply(BOTTOM_SHIFT_MM))
    angles = []
    for station in frame.stations():
        fitting = screen.FITTINGS["B104ZN"]
        angles.append((screen.pose(fitting, wood, station, 0.), fitting))
        if "horizontal" in station[0]:
            angles.append((screen.pose(B103, wood, station, 0., True), B103))
    timber = [{"member": p.name, "blank_mm": list(p.blank),
               "raw_volume_mm3": p.shape.Volume(),
               "mass_lb_at_500_kg_m3": p.shape.Volume() * 1e-9 * 500 / .45359237}
              for p in parts if p.name.startswith(("base_", "lumber_leg_"))]
    context = {"inventory": inventory, "snapshot": snapshot, "timber": timber}
    return wood, angles, context


def screw_backing(wood: dict[str, cq.Shape], context: dict) -> dict:
    """Conditional 5-mm bodies, owner 9-mm head and 63.5-mm nominal length.

    Returns every proposal relative to both original and reviewed axes. The
    actual major diameter, head height and thread/tip geometry remain unknown.
    """
    prior_moves = {r["axis_id"]: r for r in context["snapshot"]["panel_screws"]}
    rows, moves = [], []
    for row in context["inventory"]["fixed_panel_kicker_screws"]:
        original = cq.Vector(*row["origin_global_xyz_mm"])
        point = original
        direction = cq.Vector(*row["axis_global_xyz"])
        receiver = row["source_finished_receiver_member"]
        if receiver.startswith("base_rail_bottom"):
            point += T.multiply(BOTTOM_SHIFT_MM)
        old = prior_moves.get(row["axis_id"])
        reviewed = cq.Vector(*(old["new_start_global_xyz_mm"] if old
                               else row["origin_global_xyz_mm"]))
        length = 63.5 - 19.05
        body = cq.Solid.makeCylinder(2.5, length, point + direction.multiply(19.05), direction)
        fraction = min(1., shared.overlaps(body, wood[receiver]) / body.Volume())
        record = {"axis_id": row["axis_id"], "panel": row["panel_member"],
                  "receiver": receiver, "origin_xyz_mm": shared.xyz(point),
                  "direction_xyz": shared.xyz(direction),
                  "conditional_raw_wood_penetration_body_fraction": round(fraction, 6)}
        rows.append(record)
        if (point - original).Length > 1e-5 or (point - reviewed).Length > 1e-5:
            moves.append({**record, "original_origin_xyz_mm": shared.xyz(original),
                          "reviewed_origin_xyz_mm": shared.xyz(reviewed),
                          "delta_from_original_xyz_mm": shared.xyz(point - original),
                          "delta_from_reviewed_xyz_mm": shared.xyz(point - reviewed),
                          "change_from_original": (point - original).Length > 1e-5,
                          "change_from_reviewed": (point - reviewed).Length > 1e-5})
    if len(rows) != 66 or len({r["axis_id"] for r in rows}) != 66:
        raise ValueError("retain exactly 66 unique purchased-screw axes")
    return {
        "policy": "66 Hillman 42605 screws; nominal 63.5 mm; owner 9 mm head; no SPAX transfer",
        "scenario_major_diameter_mm": 5., "scenario_panel_thickness_mm": 19.05,
        "scenario_penetration_body_length_mm": 44.45,
        "actual_major_diameter_or_tip_thread_profile_verified": False,
        "full_raw_receiver_body_count": sum(r["conditional_raw_wood_penetration_body_fraction"] >= .99999
                                             for r in rows),
        "count": len(rows), "axes": rows, "moved_axes": moves,
        "moves_from_original": sum(r["change_from_original"] for r in moves),
        "moves_from_reviewed": sum(r["change_from_reviewed"] for r in moves),
        "panel_edge_support_checked": False, "installed_clearance_checked": False,
        "panel_resistance_checked": False,
    }


def build_report() -> dict:
    wood, angles, context = geometry()
    retained = screen.retained_axes()
    installed = [screen.audit_pose(angle, fitting, wood, retained)
                 for angle, fitting in angles]
    collisions = []
    for i, (angle, _) in enumerate(angles):
        for other, _ in angles[i + 1:]:
            if (volume := shared.overlaps(angle.shape, other.shape)) > .01:
                collisions.append({"first": angle.id, "second": other.id,
                                   "intersection_mm3": round(volume, 6)})
    holes = [h for row in installed for h in row["holes"]]
    by_axis: dict[tuple, list[dict]] = {}
    for row in installed:
        for hole in row["holes"]:
            by_axis.setdefault(tuple(hole["key"]), []).append({
                "angle_id": row["angle_id"], "duty_id": row["duty_id"],
                **hole,
            })
    axes = [{"axis_id": f"thin_factory_bolt_{index:03d}",
             "receiver": attachments[0]["receiver"], "attachments": attachments,
             "shared_physical_bore": len(attachments) > 1,
             "complete_stack_verified": False, "mechanics_verified": False}
            for index, attachments in enumerate(by_axis.values(), 1)]
    counts = Counter(f.model for _, f in angles)
    model_inputs = {f.model: asdict(f) for _, f in angles}
    backing = screw_backing(wood, context)
    return {
        "schema": "thin_bolted_raw_geometry_comparison/v2",
        "candidate": "compact-floor-flush-thin-bolted-development",
        "revision": REVISION, "disposition": "REVISE_UNQUALIFIED_RAW_GEOMETRY",
        "source_pins": shared.SOURCE_PINS,
        "additional_source_sha256": {
            str(screen.AXES.relative_to(ROOT)): shared.sha(screen.AXES),
            screen.NDS_LOCAL: shared.sha(ROOT / screen.NDS_LOCAL),
            "scripts/thin_bolted_fitting_screen.py": shared.sha(Path(screen.__file__)),
            str(Path(__file__).relative_to(ROOT)): shared.sha(Path(__file__)),
        },
        "runtime": {"python": platform.python_version(), "cadquery": cq.__version__},
        "question": "Do mixed shorter factory fittings clear nominal raw-stock collisions while retaining the original member sections?",
        "geometry_basis": "Original kerf-right 4x6 rims/legs, single 2x6 receivers/runners and split center; bottom rails moved 50.8 mm upslope only.",
        "fittings": model_inputs, "factory_geometry_source": screen.CATALOG,
        "exact_product_geometry_consistent": False,
        "catalog_discrepancies": [
            "B104 SKU description conflicts with its dimension fields and catalog mass.",
            "B103 SKU description says two 4.12-inch legs and 1/4-inch steel; the dimensioned catalog indicates 4-1/8 and 1-5/8 legs with general 7/32-inch thickness.",
            "Hole centers are inferred from general free-end/pitch rules, not authenticated bend tangent datums or measured tolerances.",
        ],
        "changes": {
            "enlarged_members": [], "built_up_members": [],
            "new_structural_wood_screws": 0, "custom_steel": False,
            "bottom_rail_shift_mm": BOTTOM_SHIFT_MM,
            "bottom_rail_shift_xyz_mm": shared.xyz(T.multiply(BOTTOM_SHIFT_MM)),
            "climbing_surface_and_panel_outlines_changed": False,
            "reviewed_wood_lane_geometry_changed": False,
        },
        "counts": {
            "source_duties": len({row["duty_id"] for row in installed}),
            "fittings": len(angles), "fittings_by_model": dict(counts),
            "flange_attachments": len(holes), "new_physical_wood_bolt_axes": len(axes),
            "starting_frame_bolt_axes": 12, "total_structural_planning_axes": len(axes) + 12,
            "shared_new_axes": sum(a["shared_physical_bore"] for a in axes),
            "full_raw_bore_attachments": sum(h["raw_full_bore_fraction"] >= .99999 for h in holes),
            "full_rectangular_raw_flange_seats": sum(s["ideal_rectangular_seat_fraction"] >= .99999
                                                      for r in installed for s in r["seats"]),
            "plate_plate_intersections": len(collisions),
            "plate_raw_wood_intersections": sum(len(r["ideal_plate_raw_wood_intersections"])
                                                 for r in installed),
            "legacy_axis_conflicting_attachments": sum(bool(h["intersecting_legacy_occupied_axes"])
                                                       for h in holes),
            "hillman_panel_kicker_axes": backing["count"],
        },
        "takeoff_sensitivity": {
            "brackets_only_cost_usd": round(sum(f.price_usd for _, f in angles), 2),
            "brackets_only_catalog_mass_lb": round(sum(f.catalog_mass_lb for _, f in angles), 3),
            "price_date": "2026-10-06", "price_sources": PRICE_URLS,
            "tax_shipping_bolt_nut_washer_cost_included": False,
            "assumed_density_kg_m3": 500.,
            "raw_20_member_frame_timber_mass_lb": sum(r["mass_lb_at_500_kg_m3"] for r in context["timber"]),
            "raw_16_receivers_excluding_legs_runners_mass_lb": sum(r["mass_lb_at_500_kg_m3"]
                                                                  for r in context["timber"]
                                                                  if not r["member"].startswith(("lumber_leg_", "base_floor_"))),
            "timber": context["timber"],
            "whole_board_mass_or_installed_quote": False,
        },
        "installed": installed, "physical_axes": axes,
        "plate_plate_intersections": collisions, "panel_screw_backing": backing,
        "mechanics_gates": {
            "fresh_signed_whole_frame_demands": False,
            "bolt_body_thread_root_nut_washer_and_steel_resistance": False,
            "group_action_and_shared_axis_load_paths": False,
            "member_net_section_splitting_and_panel_resistance": False,
            "joint_contact_clearance_and_rotational_freedom": False,
            "native_solve_ready": False,
        },
        "mechanics_limit": "A shared single beam bore does not establish a fixed joint or torsional resistance about its own axis. Derive contact/release behavior and frame stability explicitly; do not borrow rigid ML24Z/SDS or prior block-lane stiffness/forces, or double a single-shear resistance for unequal shared-side actions.",
        "release": shared.RELEASE,
        "limits": [
            "All geometric counts concern ideal nominal plates and raw stock, not finished service-cut wood or complete hardware.",
            "No installed bolt head, nut, washer, tool, removal corridor, or revised 66-screw/service collision check is included.",
            "The lower-rail move needs panel bottom-edge support/cantilever and load-transfer reassessment despite intact raw screw receivers.",
            "Exact factory drawing datums, bend radii, dimensions and product identity remain conditional.",
            "The original twelve frame-bolt layouts start the comparison but have no inherited force/resistance pass.",
            "Original 250 lb / 2x downward / 300 N horizontal / 100 mm lever loads and unverified no-slip floor assumption are retained for later assessment, not evaluated here.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET / "mixed-far-hole-raw-v2.json")
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f"preserve prior experiment: {args.out}")
    report = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(args.out), "counts": report["counts"],
                      "backed_screws": report["panel_screw_backing"]["full_raw_receiver_body_count"],
                      "cost_usd": report["takeoff_sensitivity"]["brackets_only_cost_usd"]}, indent=2))


if __name__ == "__main__":
    main()
