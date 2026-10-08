"""Audit the owner-directed eoere successor on authenticated cached raw stock.

This replaces fitting holes and poses in a distinct nominal study. It does
not consume predecessor forces, reconstruct its occupied assembly or qualify
hardware, drilling, contact, resistance or fabrication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import cadquery as cq

from scripts import hl35_candidate as shared
from scripts import hl35_full_fit_candidate as geometry_tools

ROOT = shared.ROOT
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
STATIONS = PACKET / "eoere-successor-v1/owner-stations.json"
MANIFEST = PACKET / "native-geometry-v4.json"
LAYOUT = PACKET / "mixed-offset-rows-shallow-wires-v4.json"
LAYOUT_SHA = "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c"
MANIFEST_SHA = "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9"
OUTPUT = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/raw-angle-geometry-v1.json"


@dataclass(frozen=True)
class Scenario:
    """One coherent inch drawing scenario; hole heel datums are inferred."""

    leg_mm: float = 88.9
    width_mm: float = 88.9
    thickness_mm: float = 6.35
    transverse_pitch_mm: float = 50.8
    axial_pitch_mm: float = 41.275
    far_offset_mm: float = 65.0875
    factory_hole_mm: float = 10.0
    bolt_mm: float = 9.525
    wood_bore_mm: float = 10.31875

    def validate(self) -> None:
        if any(not math.isfinite(v) or v <= 0 for v in asdict(self).values()):
            raise ValueError("finite positive scenario dimensions required")
        near = self.far_offset_mm - self.axial_pitch_mm
        radius = self.factory_hole_mm / 2
        if (near - radius <= self.thickness_mm
                or self.far_offset_mm + radius >= self.leg_mm
                or self.transverse_pitch_mm / 2 + radius >= self.width_mm / 2
                or self.bolt_mm >= self.factory_hole_mm
                or self.bolt_mm >= self.wood_bore_mm):
            raise ValueError("scenario holes/bolt do not fit the ideal sharp angle")

    def holes(self, active_only: bool = False) -> list[dict]:
        self.validate()
        offsets = [("far", self.far_offset_mm)] if active_only else [
            ("near", self.far_offset_mm - self.axial_pitch_mm),
            ("far", self.far_offset_mm),
        ]
        return [{"flange": flange, "row": row, "transverse": sign,
                 "along_mm": offset, "transverse_mm": sign * self.transverse_pitch_mm / 2}
                for flange in ("beam", "post") for row, offset in offsets
                for sign in (-1, 1)]


def template(scenario: Scenario) -> cq.Shape:
    """All eight factory holes remain, including the four unused near holes."""
    scenario.validate()
    leg, width, thick = scenario.leg_mm, scenario.width_mm, scenario.thickness_mm
    shape = cq.Solid.makeBox(leg, thick, width, cq.Vector(0, 0, -width / 2))
    shape = shape.fuse(cq.Solid.makeBox(thick, leg, width, cq.Vector(0, 0, -width / 2)))
    for hole in scenario.holes():
        along, across = hole["along_mm"], hole["transverse_mm"]
        point, direction = ((cq.Vector(along, -1, across), cq.Vector(0, 1, 0))
                            if hole["flange"] == "beam" else
                            (cq.Vector(-1, along, across), cq.Vector(1, 0, 0)))
        shape = shape.cut(cq.Solid.makeCylinder(scenario.factory_hole_mm / 2,
                                               thick + 2, point, direction))
    return shape.clean()


def pose(row: dict, shape: cq.Shape) -> shared.Angle:
    u = cq.Vector(*row["u_xyz"]).normalized()
    v = cq.Vector(*row["v_xyz"])
    v = (v - u.multiply(v.dot(u))).normalized()
    w = u.cross(v)
    if (w - cq.Vector(*row["w_xyz"])).Length > 1e-8:
        raise ValueError("station is not a proper orthonormal starting pose")
    angle = shared.Angle("eoere_" + row["duty_id"], row["duty_id"], row["beam"],
                         row["post"], cq.Vector(*row["origin_xyz_mm"]), u, v, w, shape)
    angle.shape = angle.placed(shape)
    return angle


def line_key(point: cq.Vector, direction: cq.Vector) -> tuple:
    """Physical line identity independent of receiver or flange direction."""
    unit = direction.normalized()
    if next(v for v in unit.toTuple() if abs(v) > 1e-8) < 0:
        unit *= -1
    foot = point - unit.multiply(point.dot(unit))
    return (*[round(v, 6) for v in unit.toTuple()],
            *[round(v, 6) for v in foot.toTuple()])


def audit(scenario: Scenario) -> dict:
    pins = {str(path.relative_to(ROOT)): shared.sha(path)
            for path in (STATIONS, MANIFEST, LAYOUT, Path(__file__), ROOT / "uv.lock")}
    if shared.sha(MANIFEST) != MANIFEST_SHA or shared.sha(LAYOUT) != LAYOUT_SHA:
        raise ValueError("predecessor input bytes differ")
    manifest, stations = json.loads(MANIFEST.read_bytes()), json.loads(STATIONS.read_bytes())
    if stations["source_sha256"] != LAYOUT_SHA:
        raise ValueError("owner station handoff is not bound to the frozen predecessor")
    for path, digest in manifest["source_sha256"].items():
        if shared.sha(ROOT / path) != digest:
            raise ValueError(f"predecessor source differs: {path}")
        pins[path] = digest
    rows = [*stations["main_stations"], *stations["remaining_base_header_starting_stations"]]
    if (len(stations["main_stations"]) != 16 or len(rows) != 24
            or len({row["duty_id"] for row in rows}) != 24):
        raise ValueError("expected sixteen main and eight base/header starting duties")
    raw = {row["member"]: row for row in manifest["raw_parts"]}
    if len(raw) != 20:
        raise ValueError("twenty starting stock members required")
    bodies = {}

    def load(row: dict) -> cq.Shape:
        if row["id"] not in bodies:
            path = ROOT / row["path"]
            if shared.sha(path) != row["sha256"]:
                raise ValueError(f"cache bytes differ: {path}")
            body = cq.Shape.importBrep(str(path))
            if not body.isValid() or len(body.Solids()) != 1:
                raise ValueError(f"invalid one-solid cached geometry: {path}")
            bodies[row["id"]] = body
            pins[row["path"]] = row["sha256"]
        return bodies[row["id"]]

    timber = {name: load(row) for name, row in raw.items()}
    local = template(scenario)
    angles = [pose(row, local) for row in rows]
    attachments, records = [], []
    for index, angle in enumerate(angles):
        seats, holes = [], []
        for flange, receiver, along, inward in (
                ("beam", angle.beam, angle.u, -angle.v),
                ("post", angle.post, angle.v, -angle.u)):
            skin = (cq.Solid.makeBox(scenario.leg_mm, .05, scenario.width_mm,
                                     cq.Vector(0, -.05, -scenario.width_mm / 2))
                    if flange == "beam" else
                    cq.Solid.makeBox(.05, scenario.leg_mm, scenario.width_mm,
                                     cq.Vector(-.05, 0, -scenario.width_mm / 2)))
            placed = angle.placed(skin)
            seats.append({"flange": flange, "receiver": receiver,
                          "raw_rectangular_seat_fraction": min(
                              1., shared.overlaps(placed, timber[receiver]) / placed.Volume())})
            for hole in (h for h in scenario.holes(active_only=True) if h["flange"] == flange):
                point = angle.origin + along.multiply(hole["along_mm"]) + angle.w.multiply(hole["transverse_mm"])
                record = {**hole, "angle_id": angle.id, "duty_id": angle.duty,
                          "receiver": receiver, "starting_entry_xyz_mm": shared.xyz(point),
                          "axis_xyz": shared.xyz(inward), "complete_joint_accepted": False}
                try:
                    near, far = geometry_tools.line_span(timber[receiver], point, inward)
                    grip = far - near
                    bore = cq.Solid.makeCylinder(scenario.wood_bore_mm / 2, grip,
                                                 point + inward.multiply(near), inward)
                    lo, hi = shared.projected_extent(timber[receiver], angle.w)
                    record.update({"line_near_mm": near, "raw_grip_mm": grip,
                                   "raw_bore_fraction": min(1., shared.overlaps(bore, timber[receiver]) / bore.Volume()),
                                   "raw_width_edge_distances_mm": [point.dot(angle.w) - lo, hi - point.dot(angle.w)],
                                   "line_key": list(line_key(point, inward))})
                except ValueError as error:
                    record["geometry_error"] = str(error)
                holes.append(record)
                attachments.append(record)
        records.append({"angle_id": angle.id, "duty_id": angle.duty,
                        "family": "main" if index < 16 else "base_header_starting",
                        "origin_xyz_mm": shared.xyz(angle.origin), "u_xyz": shared.xyz(angle.u),
                        "v_xyz": shared.xyz(angle.v), "w_xyz": shared.xyz(angle.w),
                        "seats": seats, "holes": holes,
                        "plate_raw_timber_intersections": [
                            {"member": name, "volume_mm3": volume}
                            for name, body in timber.items()
                            if (volume := shared.overlaps(angle.shape, body)) > .01]})
        print(json.dumps({"duty": angle.duty, "seat_fraction": [s["raw_rectangular_seat_fraction"] for s in seats],
                          "missed_holes": sum("geometry_error" in h for h in holes)}), flush=True)
    collisions = [{"first": angle.id, "second": other.id, "volume_mm3": volume}
                  for i, angle in enumerate(angles) for other in angles[i + 1:]
                  if (volume := shared.overlaps(angle.shape, other.shape)) > .01]
    grouped = {}
    for hole in attachments:
        if "line_key" in hole:
            grouped.setdefault(tuple(hole["line_key"]), []).append(hole)
    for path, digest in pins.items():
        if shared.sha(ROOT / path) != digest:
            raise ValueError(f"input changed during audit: {path}")
    return {"schema": "eoere_successor_raw_angle_geometry/v1",
            "candidate": "compact-floor-flush-eoere-bolted-development",
            "disposition": "CONDITIONAL_STARTING_POSE_AUDIT",
            "question": "Do the new far transverse pairs enter the raw receivers at the owner's starting poses?",
            "scenario": asdict(scenario), "source_sha256": pins,
            "tool_versions": {"cadquery": cq.__version__},
            "counts": {"main_angles": 16, "base_header_starting_angles": 8,
                       "all_factory_holes": 192, "active_flange_attachments": len(attachments),
                       "main_attachments": 64, "distinct_valid_attachment_lines": len(grouped),
                       "missing_receiver_lines": sum("geometry_error" in h for h in attachments),
                       "partial_raw_bores": sum(h.get("raw_bore_fraction", 0) < .99999 for h in attachments),
                       "starting_frame_bolts_to_recheck": 12, "Hillman_axes_preserved": 66,
                       "angle_angle_intersections": len(collisions)},
            "angles": records, "angle_intersections": collisions,
            "coincident_attachment_lines": [v for v in grouped.values() if len(v) > 1],
            "release": shared.RELEASE, "mechanics_ready": False,
            "limits": ["Centered axial rows and transverse symmetry are assumptions; actual heel offsets and bend geometry are unavailable.",
                       "Raw timbers precede service cuts, recesses and all bolt bores. Old finished holes are not carried over.",
                       "Base/header poses are starting points; the two underside blocks and two exterior cleats are not yet included.",
                       "No panel/service, hardware/tool, installed washer or complete load-path/strength clearance is established.",
                       "No stiffness, q, force, native mechanics solve or predecessor strength pass is consumed."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument("--far-offset", type=float, default=Scenario.far_offset_mm)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve prior experiment; choose a distinct output")
    result = audit(Scenario(far_offset_mm=args.far_offset))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "counts": result["counts"],
                      "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest()}, indent=2))


if __name__ == "__main__":
    main()
