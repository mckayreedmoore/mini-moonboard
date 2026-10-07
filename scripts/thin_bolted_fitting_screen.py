"""Compare nominal factory-angle layouts on the original single-2x6 frame.

Catalog-rule hole coordinates and square-corner plate envelopes are explicit
scenarios, not authenticated bend tangencies, received parts or capacities.
This reuses the original CAD and existing geometric helpers; no native solve.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import (
    KERF_RIGHT,
    KERF_RIGHT_MM,
    TRANSLATE_NAMES,
    variant,
)
from scripts import hl35_candidate as shared

ROOT = shared.ROOT
PACKET = shared.PACKET / "thin-frame-comparison"
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
INCH = 25.4
BORE = 9 / 16 * INCH
BOLT = 1 / 2 * INCH
N = cq.Vector(0, -math.cos(math.radians(40)), math.sin(math.radians(40)))
CATALOG = (
    "https://www-dev.eaton.com/content/dam/eaton/products/support-systems/"
    "strut-systems-%26-accessories/strut-fittings-and-accessories/"
    "strut-fittings-catalog-section.pdf"
)
NDS_LOCAL = (
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/"
    "materials-source/AWC_NDS2024_withCommentary_20250328_"
    "WebsiteChapter-12-Dowel-type-fasteners.pdf"
)


@dataclass(frozen=True)
class Fitting:
    model: str
    u_leg_mm: float
    v_leg_mm: float
    u_holes: int
    v_holes: int
    price_usd: float
    catalog_mass_lb: float
    width_mm: float = 1.625 * INCH
    thickness_mm: float = 7 / 32 * INCH

    def offsets(self, flange: str) -> tuple[float, ...]:
        """Infer centers from outer extent, 13/16 end offset, 1-7/8 pitch.

        This inference intentionally remains conditional until the exact
        drawing datum and actual bend/hole positions are reconciled.
        """
        if flange not in ("beam", "post"):
            raise ValueError("flange must be beam or post")
        length = self.u_leg_mm if flange == "beam" else self.v_leg_mm
        count = self.u_holes if flange == "beam" else self.v_holes
        return tuple(sorted(length - .8125 * INCH - i * 1.875 * INCH
                            for i in range(count)))


FITTINGS = {
    "B104ZN": Fitting("B104ZN", 4.125 * INCH, 3.5 * INCH, 2, 2, 5.52, .78),
    "B115ZN": Fitting("B115ZN", 3.75 * INCH, 3.9375 * INCH, 2, 2, 6.92, .76),
    "B102ZN": Fitting("B102ZN", 3.5 * INCH, 2.25 * INCH, 2, 1, 6.48, .56),
}


def template(fitting: Fitting) -> cq.Shape:
    """Ideal outside-corner occupancy, including all factory holes."""
    t, w = fitting.thickness_mm, fitting.width_mm
    shape = cq.Solid.makeBox(fitting.u_leg_mm, t, w, cq.Vector(0, 0, -w / 2))
    shape = shape.fuse(cq.Solid.makeBox(t, fitting.v_leg_mm, w,
                                     cq.Vector(0, 0, -w / 2))).clean()
    for flange in ("beam", "post"):
        for offset in fitting.offsets(flange):
            point, direction = (
                (cq.Vector(offset, -1, 0), cq.Vector(0, 1, 0))
                if flange == "beam" else
                (cq.Vector(-1, offset, 0), cq.Vector(1, 0, 0))
            )
            shape = shape.cut(cq.Solid.makeCylinder(BORE / 2, t + 2,
                                                   point, direction))
    return shape.clean()


def retained_axes() -> list[tuple[str, cq.Shape]]:
    """Legacy CAD occupancy only; no Hillman dimensions are inferred here."""
    rows = []
    counts = {"hillman_panel": 0, "bolt_clearance": 0}
    with AXES.open(newline="") as handle:
        for row in csv.DictReader(handle):
            kind = row["shop_opening_kind"]
            if kind not in counts:
                continue
            counts[kind] += 1
            point = cq.Vector(*(float(row[f"start_{a}_mm"]) for a in "xyz"))
            direction = cq.Vector(*(float(row[f"direction_{a}"]) for a in "xyz"))
            shape = cq.Solid.makeCylinder(float(row["occupied_diameter_mm"]) / 2,
                                         float(row["occupied_length_mm"]),
                                         point, direction)
            rows.append((row["name"], shape))
    if counts != {"hillman_panel": 66, "bolt_clearance": 12}:
        raise ValueError("original retained-axis census changed")
    return rows


def pose(fitting: Fitting, wood: dict[str, cq.Shape], station: tuple,
         row_shift_mm: float, opposite_beam_face: bool = False) -> shared.Angle:
    duty, origin, u, v, beam, post = station
    if duty in TRANSLATE_NAMES:
        origin += cq.Vector(-KERF_RIGHT_MM, 0, 0)
    if opposite_beam_face:
        v = v.multiply(-1)
    w = u.cross(v)
    # Align to real receiving planes, rather than assuming an old ML24Z datum.
    _, post_face = shared.projected_extent(wood[post], u)
    _, beam_face = shared.projected_extent(wood[beam], v)
    lo = max(shared.projected_extent(wood[name], w)[0] for name in (beam, post))
    hi = min(shared.projected_extent(wood[name], w)[1] for name in (beam, post))
    origin += u.multiply(post_face - origin.dot(u))
    origin += v.multiply(beam_face - origin.dot(v))
    origin += w.multiply((lo + hi) / 2 + row_shift_mm - origin.dot(w))
    result = shared.Angle(
        f"{fitting.model}_{duty}_{'opposite' if opposite_beam_face else 'reference'}",
        duty, beam, post, origin, u, v, w, template(fitting),
    )
    result.shape = result.placed(result.shape)
    return result


def audit_pose(angle: shared.Angle, fitting: Fitting,
               wood: dict[str, cq.Shape], retained: list[tuple[str, cq.Shape]],
               holes: str = "far") -> dict:
    if holes not in ("all", "far"):
        raise ValueError("holes must be all or far")
    records, seats = [], []
    for flange, member, inward, along in (
        ("beam", angle.beam, angle.v.multiply(-1), angle.u),
        ("post", angle.post, angle.u.multiply(-1), angle.v),
    ):
        extent = shared.projected_extent(wood[member], inward)
        thickness = extent[1] - extent[0]
        length = fitting.u_leg_mm if flange == "beam" else fitting.v_leg_mm
        skin = (cq.Solid.makeBox(length, .05, fitting.width_mm,
                                 cq.Vector(0, -.05, -fitting.width_mm / 2))
                if flange == "beam" else
                cq.Solid.makeBox(.05, length, fitting.width_mm,
                                 cq.Vector(-.05, 0, -fitting.width_mm / 2)))
        skin = angle.placed(skin)
        seats.append({"flange": flange, "receiver": member,
                      "ideal_rectangular_seat_fraction": round(
                          min(1., shared.overlaps(skin, wood[member]) / skin.Volume()), 6)})
        offsets = fitting.offsets(flange)
        if holes == "far":
            offsets = (max(offsets),)
        for offset in offsets:
            point = angle.origin + along.multiply(offset)
            bore = cq.Solid.makeCylinder(BORE / 2, thickness, point, inward)
            bounds = shared.projected_extent(wood[member], angle.w)
            edge = min(point.dot(angle.w) - bounds[0], bounds[1] - point.dot(angle.w))
            records.append({
                "flange": flange, "receiver": member,
                "offset_from_assumed_outer_corner_mm": round(offset, 6),
                "entry_xyz_mm": shared.xyz(point), "axis_xyz": shared.xyz(inward),
                "projected_raw_thickness_mm": round(thickness, 6),
                "raw_full_bore_fraction": round(
                    min(1., shared.overlaps(bore, wood[member]) / bore.Volume()), 6),
                "width_edge_distance_mm": round(edge, 6),
                "conditional_two_edge_4d_reserve_mm": round(edge - 4 * BOLT, 6),
                "intersecting_legacy_occupied_axes": [
                    name for name, obstacle in retained
                    if shared.overlaps(bore, obstacle) > .01
                ],
                "key": list(shared.line_key(member, point, inward)),
            })
    collisions = [{"member": name, "intersection_mm3": round(volume, 3)}
                  for name, solid in wood.items()
                  if (volume := shared.overlaps(angle.shape, solid)) > .01]
    return {
        "angle_id": angle.id, "duty_id": angle.duty,
        "beam": angle.beam, "post": angle.post,
        "origin_xyz_mm": shared.xyz(angle.origin),
        "u_xyz": shared.xyz(angle.u), "v_xyz": shared.xyz(angle.v),
        "w_xyz": shared.xyz(angle.w), "used_holes": holes,
        "holes": records, "seats": seats,
        "ideal_plate_raw_wood_intersections": collisions,
        "end_distance_classified": False,
        "strength_checked": False, "installation_access_checked": False,
    }


def run_screen(fitting: Fitting, row_shift_mm: float = 0.) -> dict:
    """All source stations, with mirrored beam-face rail pairs as a new trial."""
    shared.load_sources()
    frame = variant(KERF_RIGHT)
    wood = {part.name: part.shape for part in frame.uncut_wood_parts()}
    stations = frame.stations()
    if len(stations) != 24:
        raise ValueError("expected all 24 original structural duties")
    retained = retained_axes()
    angles, records = [], []
    for station in stations:
        options = (False, True) if "horizontal" in station[0] else (False,)
        for other in options:
            angle = pose(fitting, wood, station, row_shift_mm, other)
            angles.append(angle)
            records.append(audit_pose(angle, fitting, wood, retained))
    plate_collisions = []
    for i, angle in enumerate(angles):
        for other in angles[i + 1:]:
            if (volume := shared.overlaps(angle.shape, other.shape)) > .01:
                plate_collisions.append({"first": angle.id, "second": other.id,
                                         "intersection_mm3": round(volume, 3)})
    holes = [h for row in records for h in row["holes"]]
    keys = {tuple(row["key"]) for row in holes}
    return {
        "schema": "thin_bolted_factory_fitting_screen/v1",
        "candidate": "compact-floor-flush-thin-bolted-development",
        "disposition": "CONDITIONAL_GEOMETRY_COMPARISON_ONLY",
        "question": "Can inexpensive narrow factory fittings retain original-size stock with far holes and rail-face pairs?",
        "input_fitting": asdict(fitting),
        "conditional_catalog_hole_offsets_mm": {
            flange: list(fitting.offsets(flange)) for flange in ("beam", "post")
        },
        "row_shift_mm": row_shift_mm,
        "source_pins": shared.SOURCE_PINS,
        "additional_source_sha256": {
            str(AXES.relative_to(ROOT)): shared.sha(AXES),
            NDS_LOCAL: shared.sha(ROOT / NDS_LOCAL),
            str(Path(__file__).relative_to(ROOT)): shared.sha(Path(__file__)),
        },
        "sources": {"eaton_catalog": CATALOG,
                    "exact_model": f"https://www.eaton.com/us/en-us/skuPage.{fitting.model}.html"},
        "raw_geometry_basis": "Original kerf-right single-2x6 frame; no reviewed block-lane member translations or services applied.",
        "counts": {
            "source_duties": len(stations), "fittings": len(angles),
            "flange_attachments": len(holes), "distinct_trial_wood_axes": len(keys),
            "full_raw_bore_attachments": sum(h["raw_full_bore_fraction"] >= .99999 for h in holes),
            "full_rectangular_raw_seats": sum(s["ideal_rectangular_seat_fraction"] >= .99999
                                              for r in records for s in r["seats"]),
            "plate_plate_intersections": len(plate_collisions),
            "plate_wood_intersections": sum(len(r["ideal_plate_raw_wood_intersections"])
                                             for r in records),
            "legacy_axis_conflicting_attachments": sum(bool(h["intersecting_legacy_occupied_axes"])
                                                       for h in holes),
        },
        "brackets_only_cost_usd": round(len(angles) * fitting.price_usd, 2),
        "catalog_brackets_only_mass_lb": round(len(angles) * fitting.catalog_mass_lb, 3),
        "installed": records,
        "plate_plate_intersections": plate_collisions,
        "release": shared.RELEASE,
        "limits": [
            "Outer-corner hole-datum inference, bend radius and tolerances remain unverified. Exact product/SKU discrepancies are not silently reconciled.",
            "Only far holes are attached to wood; unused steel holes remain in the plate. No strut-system rating or full-fastener catalog installation is claimed.",
            "Broad-face projection is valid as an edge marker for rail pairs, not for an oblique principal or arbitrary header joint. End distances remain unclassified.",
            "Raw wood excludes service voids, recesses, retained bores and other machining. No net section or resistance is established.",
            "Legacy retained-axis cylinders are CAD occupancy only, not purchased Hillman physical envelopes or the reviewed eight-move layout.",
            "Bolt heads/nuts/washers, complete extraction/tool corridors and hardware-to-service/panel collisions remain unchecked.",
            "No whole-frame/joint/member/panel solve, support verification or fabrication/climbing release exists.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=FITTINGS, default="B102ZN")
    parser.add_argument("--row-shift-mm", type=float, default=0.)
    parser.add_argument("--out", type=Path, default=PACKET / "b102-far-hole-pairs-v1.json")
    args = parser.parse_args()
    if not math.isfinite(args.row_shift_mm):
        parser.error("row shift must be finite")
    report = run_screen(FITTINGS[args.model], args.row_shift_mm)
    if args.out.exists():
        raise FileExistsError(f"preserve prior experiment: {args.out}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(args.out), "counts": report["counts"],
                      "cost_usd": report["brackets_only_cost_usd"]}, indent=2))


if __name__ == "__main__":
    main()
