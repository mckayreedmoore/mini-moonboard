"""Screen hypothetical hold sites against supplied current CAD; never mutate it."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from itertools import pairwise
from typing import Any

import cadquery as cq

from mini_moonboard import hold_tnut_reinforcement, panel_grid_v2

FLANGE_DIAMETER_MM = 25.4
FLANGE_THICKNESS_MM = 1.86
PROJECTION_DIAMETER_MM = 11.1125
PROJECTION_LENGTH_MM = 50.8
VOLUME_TOLERANCE_MM3 = 1e-4


def midpoint_sites() -> list[dict[str, Any]]:
    """Nearest neighbors only; no diagonal midpoints or extrapolated edge sites."""
    result = []
    for family, datums in [
        ("LED", panel_grid_v2.main_led_datums()),
        ("T-nut", panel_grid_v2.main_tnut_datums()),
    ]:
        for direction in ["horizontal", "vertical"]:
            for label, (x, s) in datums.items():
                column, row = label[0], int(label[1:])
                neighbor = (
                    f"{chr(ord(column) + 1)}{row}"
                    if direction == "horizontal"
                    else f"{column}{row + 1}"
                )
                if neighbor not in datums:
                    continue
                nx, ns = datums[neighbor]
                result.append(
                    {
                        "id": f"{family}:{label}-{neighbor}",
                        "family": family,
                        "direction": direction,
                        "endpoints": [label, neighbor],
                        "surface": "main",
                        "x_mm": (x + nx) / 2,
                        "s_mm": (s + ns) / 2,
                    }
                )
    datums = panel_grid_v2.kicker_foothold_datums()
    labels = sorted(datums, key=lambda label: datums[label][0])
    for left, right in pairwise(labels):
        x, z = datums[left]
        nx, nz = datums[right]
        result.append(
            {
                "id": f"kicker:{left}-{right}",
                "family": "kicker T-nut",
                "direction": "horizontal",
                "endpoints": [left, right],
                "surface": "kicker",
                "x_mm": (x + nx) / 2,
                "s_mm": (z + nz) / 2,
            }
        )
    assert len(result) == 491
    return result


def _bbox(shape: cq.Shape) -> tuple[float, ...]:
    b = shape.BoundingBox()
    return b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax


def _overlap(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    return all(a[i] < b[i + 1] and b[i] < a[i + 1] for i in (0, 2, 4))


def screen_midpoints(
    geometry: Any, *, progress: Callable | None = None
) -> dict[str, Any]:
    source = geometry.source
    source_parts = {p.name: p.shape for p in source.parts()}
    wood = {
        r["part_id"]: source_parts[r["part_id"]]
        for r in geometry.source_inventory["parts"]
        if r["kind"] == "timber"
    }
    wood.update(geometry.finished_hosts)
    wood.update(geometry.finished_candidate_parts)
    wood.update(geometry.additional_finished_source_parts)
    hardware = {
        f"{axis}/{role}": shape
        for axis, roles in geometry.candidate_installed_hardware.items()
        for role, shape in roles.items()
    }
    hardware.update(geometry.protected["retained_12_frame_bolt_components"])
    hardware.update(
        {f"panel screw/{axis}": shape for axis, shape in geometry.fixed_axes.items()}
    )
    protected = {
        f"{group}/{name}": shape
        for group in ["tnuts", "lights"]
        for name, shape in geometry.protected[group].items()
    }
    pools = {
        "timber": wood,
        "structural_hardware": hardware,
        "existing_hold_or_LED": protected,
    }
    bounds = {
        group: {name: _bbox(shape) for name, shape in shapes.items()}
        for group, shapes in pools.items()
    }
    old_datums = hold_tnut_reinforcement.datums(source)
    old_holds = {
        r["label"]: cq.Vector(*r["rear_seating_xyz_mm"])
        for r in old_datums
        if r["name"].startswith("hold_tnut_main_")
    }
    grid = panel_grid_v2.main_tnut_datums()
    for label, (x, s) in grid.items():
        expected = source.b.point(x - source.b.HALF, s, 0)
        if (old_holds[label] - expected).Length > 1e-6:
            raise ValueError("Current T-nut grid is not the assumed grid transform")
    rows = []
    for i, site in enumerate(midpoint_sites()):
        site = dict(site)
        if site["surface"] == "main":
            rear = source.b.point(site["x_mm"] - source.b.HALF, site["s_mm"], 0)
            normal = source.b.normal().normalized()
        else:
            rear = cq.Vector(
                site["x_mm"] - source.b.HALF,
                source.base.HEADER_FRONT_Y,
                source.b.V1_KICKER_HEIGHT_MM + site["s_mm"],
            )
            normal = cq.Vector(0, -1, 0)
        site["rear_xyz_mm"] = list(rear.toTuple())
        probes = {
            "flange": cq.Solid.makeCylinder(
                FLANGE_DIAMETER_MM / 2, FLANGE_THICKNESS_MM, rear, normal
            ),
            "rear_projection": cq.Solid.makeCylinder(
                PROJECTION_DIAMETER_MM / 2, PROJECTION_LENGTH_MM, rear, normal
            ),
        }
        hits = {group: [] for group in pools}
        for probe_name, probe in probes.items():
            box = _bbox(probe)
            for group, shapes in pools.items():
                for name, shape in shapes.items():
                    if not _overlap(box, bounds[group][name]):
                        continue
                    intersection = probe.intersect(shape)
                    volume = intersection.Volume()
                    if volume <= VOLUME_TOLERANCE_MM3:
                        continue
                    hit = {
                        "member": name,
                        "envelope": probe_name,
                        "intersection_mm3": round(volume, 6),
                    }
                    if group == "timber" and probe_name == "rear_projection":
                        # Rotating the normal onto +Z gives the full curved-solid extrema.
                        angle = -50 if site["surface"] == "main" else -90
                        projected = intersection.rotate(
                            (0, 0, 0), (1, 0, 0), angle
                        ).BoundingBox()
                        origin_n = rear.dot(normal)
                        hit["first_occupied_depth_mm"] = round(
                            projected.zmin - origin_n, 4
                        )
                    hits[group].append(hit)
        site["hits"] = hits
        site["timber_status"] = (
            "flange blocked"
            if any(h["envelope"] == "flange" for h in hits["timber"])
            else "rear projection blocked"
            if hits["timber"]
            else "no timber hit within envelope"
        )
        rows.append(site)
        if progress and (i + 1) % 100 == 0:
            progress(f"midpoint geometry screen: {i + 1}/491 sites")
    groups = {}
    for family, direction in sorted({(r["family"], r["direction"]) for r in rows}):
        subset = [
            r for r in rows if r["family"] == family and r["direction"] == direction
        ]
        groups[f"{family} / {direction}"] = {
            "sites": len(subset),
            "timber_blocked": sum(bool(r["hits"]["timber"]) for r in subset),
            "flange_blocked": sum(
                r["timber_status"] == "flange blocked" for r in subset
            ),
            "structural_hardware_blocked": sum(
                bool(r["hits"]["structural_hardware"]) for r in subset
            ),
            "existing_hold_or_LED_overlap": sum(
                bool(r["hits"]["existing_hold_or_LED"]) for r in subset
            ),
            "timber_members": dict(
                Counter(
                    member
                    for r in subset
                    for member in {h["member"] for h in r["hits"]["timber"]}
                )
            ),
        }
    return {
        "schema": "wood_joint_hypothetical_midpoint_clearance/v1",
        "revision_id": geometry.layout_id,
        "scope": "Hypothetical nearest-neighbor midpoints, not an official future hold layout. Geometry only; no joint evaluations.",
        "envelopes": {
            "flange_diameter_mm": FLANGE_DIAMETER_MM,
            "flange_rear_thickness_mm": FLANGE_THICKNESS_MM,
            "rear_projection_diameter_mm": PROJECTION_DIAMETER_MM,
            "rear_projection_length_mm": PROJECTION_LENGTH_MM,
        },
        "limits": [
            "No diagonal sites, future hold bodies, new LED stations, retention screws or tool-access sweeps checked.",
            "The 50.8 mm rear projection is provisional; shorter/longer actual hold bolts change clearance.",
            "The flange is a full disk envelope. No holes or supports were modified.",
            "Existing main-panel T-nut and LED centers use the current stock-adapted grid, including row-boundary exceptions.",
            "Kicker has one hold row and no LEDs: only nine horizontal hold midpoints exist.",
        ],
        "wood_member_count": len(wood),
        "groups": groups,
        "sites": rows,
        "joint_evaluations_run": False,
        "candidate_accepted": False,
    }
