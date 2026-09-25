"""Screen the historical 491 midpoint envelopes against live current WJ24 geometry.

The caller supplies an already materialized current geometry and its frozen
evaluation snapshot. This adapter does not compose or mutate CAD. It preserves
the historical midpoint envelopes and obstacle categories while applying the
current, owner-recorded G2 LED datum override and current physical-object map.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard import hold_tnut_reinforcement, panel_grid_v2
from scripts import wood_joint_current_access_screen as current_access
from scripts import wood_joint_current_receiver_screen as receiver_screen
from scripts import wood_joint_current_retained_access as retained_access
from scripts import wood_joint_midpoint_clearance as historical_midpoints
from scripts import wood_joint_wj12_diagnostic as wj12_diagnostic

ROOT = Path(__file__).resolve().parents[1]
CURRENT_REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
SCHEMA = "wood_joint_current_hypothetical_midpoint_clearance/v1"
OUTPUT_DIRECTORY = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-midpoint-clearance-attempt01"
)
CURRENT_REVISION_BUNDLE = (
    ROOT / "docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24"
)
CURRENT_REVISION_REPORT_PATH = CURRENT_REVISION_BUNDLE / "revision.json"
CURRENT_REVISION_VERIFICATION_PATH = CURRENT_REVISION_BUNDLE / "verification.json"
EXPECTED_G2_PANEL_DATUM_MM = (1405.0, 199.2)
EXPECTED_TIMBER_COUNT = 44
EXPECTED_CANDIDATE_AXIS_COUNT = 92
EXPECTED_RETAINED_FRAME_BOLT_COUNT = 12
EXPECTED_RETAINED_FRAME_ROLE_COUNT = 60
EXPECTED_FIXED_PANEL_AXIS_COUNT = 66
EXPECTED_EXISTING_TNUT_COUNT = 142
EXPECTED_EXISTING_LED_COUNT = 132
EXPECTED_WIRE_COUNT = 131

_SOURCE_CODE_PATHS = (
    "scripts/wood_joint_current_midpoint_clearance.py",
    "scripts/wood_joint_midpoint_clearance.py",
    "scripts/wood_joint_current_geometry.py",
    "scripts/wood_joint_current_access_screen.py",
    "scripts/wood_joint_current_retained_access.py",
    "scripts/wood_joint_current_receiver_screen.py",
    "scripts/wood_joint_wj12_diagnostic.py",
    "mini_moonboard/panel_grid_v2.py",
    "mini_moonboard/hold_tnut_reinforcement.py",
)


def _finite_pair(value: Any, label: str) -> tuple[float, float]:
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a finite 2-vector") from error
    if len(result) != 2 or not all(math.isfinite(component) for component in result):
        raise ValueError(f"{label} must be a finite 2-vector")
    return result


def midpoint_sites_for_current_revision(
    led_datum_overrides_mm: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return the same 491 neighbor sites, with the current G2 LED datum."""
    if not isinstance(led_datum_overrides_mm, Mapping):
        raise TypeError("current revision LED datum overrides must be a mapping")
    if set(led_datum_overrides_mm) != {"G2"}:
        raise ValueError(
            "this current revision requires exactly the recorded G2 LED override"
        )

    override = _finite_pair(led_datum_overrides_mm["G2"], "G2 LED datum")
    baseline_led_datums = panel_grid_v2.main_led_datums()
    baseline_g2 = baseline_led_datums.get("G2")
    if baseline_g2 is None:
        raise ValueError("the stock-adapted LED grid omits G2")
    expected = EXPECTED_G2_PANEL_DATUM_MM
    if not (
        math.isclose(override[0], expected[0], rel_tol=0.0, abs_tol=1e-8)
        and math.isclose(override[1], expected[1], rel_tol=0.0, abs_tol=1e-8)
        and math.isclose(override[0] - baseline_g2[0], 5.0, rel_tol=0.0, abs_tol=1e-8)
        and math.isclose(override[1], baseline_g2[1], rel_tol=0.0, abs_tol=1e-8)
    ):
        raise ValueError("G2 override differs from the current reviewed +5 mm X datum")

    led_datums = dict(baseline_led_datums)
    led_datums["G2"] = override
    rows = [dict(row) for row in historical_midpoints.midpoint_sites()]
    seen_ids: set[str] = set()
    for row in rows:
        if row["id"] in seen_ids:
            raise ValueError("historical midpoint site IDs are not unique")
        seen_ids.add(row["id"])
        if row["family"] != "LED":
            continue
        first, second = row["endpoints"]
        x1, s1 = led_datums[first]
        x2, s2 = led_datums[second]
        row["x_mm"] = (x1 + x2) / 2.0
        row["s_mm"] = (s1 + s2) / 2.0

    if len(rows) != 491:
        raise ValueError(f"current midpoint grid requires 491 sites, found {len(rows)}")
    return rows


def _validate_current_g2_shape(
    geometry: Any, led_datums: Mapping[str, cq.Shape]
) -> tuple[float, float]:
    shape = led_datums.get("light_G2")
    if shape is None or not callable(getattr(shape, "Center", None)):
        raise ValueError(
            "current protected LED map must include a centerable light_G2 solid"
        )
    source = getattr(geometry, "source", None)
    basis = getattr(source, "b", None)
    if basis is None or not callable(getattr(basis, "point", None)):
        raise TypeError(
            "current source geometry must expose its panel coordinate basis"
        )

    origin = basis.point(0.0, 0.0, 0.0)
    tangent = (basis.point(0.0, 1.0, 0.0) - origin).normalized()
    center = shape.Center()
    actual = (
        float(center.x) + float(basis.HALF),
        float((center - origin).dot(tangent)),
    )
    if not (
        math.isclose(
            actual[0], EXPECTED_G2_PANEL_DATUM_MM[0], rel_tol=0.0, abs_tol=1e-4
        )
        and math.isclose(
            actual[1], EXPECTED_G2_PANEL_DATUM_MM[1], rel_tol=0.0, abs_tol=1e-4
        )
    ):
        raise ValueError(
            "live light_G2 solid does not match the frozen current panel datum: "
            f"{actual!r}"
        )
    return actual


def _wood_member_ids(geometry: Any) -> tuple[str, ...]:
    inventory = getattr(geometry, "source_inventory", None)
    if not isinstance(inventory, Mapping):
        raise TypeError("current geometry must expose source_inventory metadata")
    part_rows = inventory.get("parts")
    if not isinstance(part_rows, (tuple, list)):
        raise TypeError("current source inventory part rows must be a sequence")
    timber_ids = [
        row.get("part_id")
        for row in part_rows
        if isinstance(row, Mapping) and row.get("kind") == "timber"
    ]
    if (
        len(timber_ids) != 20
        or any(not isinstance(name, str) or not name for name in timber_ids)
        or len(set(timber_ids)) != len(timber_ids)
    ):
        raise ValueError(
            "current source inventory must provide 20 unique timber member IDs"
        )

    hosts = getattr(geometry, "finished_hosts", None)
    candidates = getattr(geometry, "finished_candidate_parts", None)
    overlays = getattr(geometry, "additional_finished_source_parts", {})
    for value, label in (
        (hosts, "finished_hosts"),
        (candidates, "finished_candidate_parts"),
        (overlays, "additional_finished_source_parts"),
    ):
        if not isinstance(value, Mapping):
            raise TypeError(f"current geometry {label} must be a mapping")

    unknown_host_ids = set(hosts) - set(timber_ids)
    unknown_overlay_ids = set(overlays) - set(timber_ids)
    if unknown_host_ids or unknown_overlay_ids:
        raise ValueError("finished source timber overlays include unknown member IDs")
    result = set(timber_ids) | set(hosts) | set(candidates) | set(overlays)
    if len(result) != EXPECTED_TIMBER_COUNT:
        raise ValueError(
            f"current midpoint screen requires 44 timber members, found {len(result)}"
        )
    return tuple(sorted(result))


def _validate_pool_counts(
    wood: Mapping[str, Any],
    candidate_hardware: Mapping[str, Mapping[str, Any]],
    retained_targets: Mapping[str, Mapping[str, Any]],
    fixed_axes: Mapping[str, Any],
    tnuts: Mapping[str, Any],
    lights: Mapping[str, Any],
) -> dict[str, int]:
    expected_candidate_roles = set(current_access.ORDINARY_ROLES)
    expected_retained_roles = set(retained_access.FRAME_ROLE_ORDER)
    if len(wood) != EXPECTED_TIMBER_COUNT:
        raise ValueError("midpoint timber pool must contain exactly 44 current solids")
    if len(candidate_hardware) != EXPECTED_CANDIDATE_AXIS_COUNT:
        raise ValueError("midpoint scene must include exactly 92 candidate bolt stacks")
    if len(retained_targets) != EXPECTED_RETAINED_FRAME_BOLT_COUNT:
        raise ValueError(
            "midpoint scene must include exactly 12 retained frame-bolt stacks"
        )
    if len(fixed_axes) != EXPECTED_FIXED_PANEL_AXIS_COUNT:
        raise ValueError("midpoint scene must include exactly 66 panel screw axes")
    if len(tnuts) != EXPECTED_EXISTING_TNUT_COUNT:
        raise ValueError("midpoint scene must include exactly 142 existing T-nuts")
    if len(lights) != EXPECTED_EXISTING_LED_COUNT:
        raise ValueError("midpoint scene must include exactly 132 existing LED bodies")
    if set(tnuts) & set(lights):
        raise ValueError("existing T-nut and LED obstacle IDs must be disjoint")

    for axis_id, roles in candidate_hardware.items():
        if not isinstance(roles, Mapping) or set(roles) != expected_candidate_roles:
            raise ValueError(
                f"candidate stack {axis_id} must have exactly five physical roles"
            )
    for axis_id, target in retained_targets.items():
        roles = target.get("roles")
        if not isinstance(roles, Mapping) or set(roles) != expected_retained_roles:
            raise ValueError(
                f"retained stack {axis_id} must have exactly five physical roles"
            )

    return {
        "timber_solids": len(wood),
        "candidate_bolt_axes": len(candidate_hardware),
        "candidate_bolt_components": sum(
            len(roles) for roles in candidate_hardware.values()
        ),
        "retained_frame_bolt_stacks": len(retained_targets),
        "retained_frame_bolt_components": sum(
            len(target["roles"]) for target in retained_targets.values()
        ),
        "fixed_panel_screw_axes": len(fixed_axes),
        "existing_tnut_solids": len(tnuts),
        "existing_led_bodies": len(lights),
        "tested_obstacle_shapes": len(wood)
        + sum(len(roles) for roles in candidate_hardware.values())
        + sum(len(target["roles"]) for target in retained_targets.values())
        + len(fixed_axes)
        + len(tnuts)
        + len(lights),
    }


def _require_scene_shape(
    obstacles: Mapping[str, cq.Shape], obstacle_id: str, expected: cq.Shape
) -> cq.Shape:
    shape = obstacles.get(obstacle_id)
    if shape is not expected:
        raise ValueError(f"current obstacle map omits or remaps {obstacle_id}")
    return shape


def _load_current_revision_report() -> tuple[dict[str, Any], str, str]:
    report_bytes = CURRENT_REVISION_REPORT_PATH.read_bytes()
    verification = json.loads(CURRENT_REVISION_VERIFICATION_PATH.read_text())
    report_hash = hashlib.sha256(report_bytes).hexdigest()
    if verification.get("revision_report_sha256") != report_hash:
        raise RuntimeError(
            "current G2 revision report does not match its verification hash"
        )
    report = json.loads(report_bytes)
    if report.get("revision_id") != CURRENT_REVISION_ID:
        raise ValueError(
            "current G2 override report describes a different geometry revision"
        )
    return (
        report,
        report_hash,
        hashlib.sha256(CURRENT_REVISION_VERIFICATION_PATH.read_bytes()).hexdigest(),
    )


def _validate_live_tnut_grid(geometry: Any) -> None:
    source = getattr(geometry, "source", None)
    if source is None:
        raise TypeError("current geometry must expose its source frame")
    old_datums = {
        row["label"]: cq.Vector(*row["rear_seating_xyz_mm"])
        for row in hold_tnut_reinforcement.datums(source)
        if row["name"].startswith("hold_tnut_main_")
    }
    grid = panel_grid_v2.main_tnut_datums()
    if set(old_datums) != set(grid):
        raise ValueError(
            "current main T-nut datums differ from the 132-site stock grid"
        )
    for label, (x, s) in grid.items():
        expected = source.b.point(x - source.b.HALF, s, 0.0)
        if (old_datums[label] - expected).Length > 1e-6:
            raise ValueError(
                "current T-nut grid is not the assumed stock-adapted transform"
            )
    kicker_datums = {
        row["label"]: cq.Vector(*row["rear_seating_xyz_mm"])
        for row in hold_tnut_reinforcement.datums(source)
        if row["name"].startswith("hold_tnut_kicker_")
    }
    kicker_grid = panel_grid_v2.kicker_foothold_datums()
    if set(kicker_datums) != set(kicker_grid):
        raise ValueError(
            "current kicker T-nut datums differ from the ten-site source grid"
        )
    for label, (x, z) in kicker_grid.items():
        expected = cq.Vector(
            x - source.b.HALF,
            source.base.HEADER_FRONT_Y,
            source.b.V1_KICKER_HEIGHT_MM + z,
        )
        if (kicker_datums[label] - expected).Length > 1e-6:
            raise ValueError(
                "current kicker T-nut grid differs from its source transform"
            )


def _current_panel_axis_rows(
    geometry: Any, revision_report: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Reconcile live panel axes with the current cumulative revision report."""
    fixed_axes = getattr(geometry, "fixed_axes", None)
    source_inventory = getattr(geometry, "source_inventory", None)
    if not isinstance(fixed_axes, Mapping):
        raise TypeError("current geometry must expose its 66 fixed panel screw axes")
    if not isinstance(source_inventory, Mapping):
        raise TypeError("current geometry must expose source_inventory metadata")
    return receiver_screen.build_current_panel_axis_map(
        source_inventory, revision_report, fixed_axis_ids=set(fixed_axes)
    )


def build_current_midpoint_clearance_report(
    geometry: Any,
    frozen_snapshot: Mapping[str, Any],
    *,
    progress: Callable[[str], None] | None = None,
    output_directory: str = OUTPUT_DIRECTORY,
) -> dict[str, Any]:
    """Screen current hypothetical midpoint sites against supplied live geometry.

    ``geometry`` is the already materialized current ``g24_outer_2x6`` object;
    ``frozen_snapshot`` is the current evaluation geometry snapshot. The
    function performs only the midpoint intersections, not CAD composition or
    native mechanics.
    """
    if getattr(geometry, "layout_id", None) != CURRENT_REVISION_ID:
        raise ValueError(f"midpoint screen requires {CURRENT_REVISION_ID!r}")
    if getattr(geometry, "trial_id", None) != CURRENT_REVISION_ID:
        raise ValueError("current midpoint geometry trial ID differs from its revision")
    snapshot_sha256 = retained_access._validate_freeze(frozen_snapshot, geometry)
    source_inventory_sha256 = retained_access._source_inventory_digest(geometry)

    revision_report, revision_report_sha256, verification_sha256 = (
        _load_current_revision_report()
    )
    led_overrides = revision_report.get("led_datum_overrides_mm")
    rows = midpoint_sites_for_current_revision(led_overrides)

    candidate_bores = getattr(geometry, "candidate_bores", None)
    candidate_hardware = getattr(geometry, "candidate_installed_hardware", None)
    if not isinstance(candidate_bores, Mapping) or not isinstance(
        candidate_hardware, Mapping
    ):
        raise TypeError(
            "current geometry must expose candidate bore and installed-hardware maps"
        )
    current_access._candidate_axis_groups(
        candidate_bores, candidate_hardware, include_all_candidate_axes=True
    )
    fixed_axes = getattr(geometry, "fixed_axes", None)
    if not isinstance(fixed_axes, Mapping):
        raise TypeError("current geometry must expose its 66 fixed panel screw axes")
    _current_panel_axis_rows(geometry, revision_report)

    protected = getattr(geometry, "protected", None)
    if not isinstance(protected, Mapping):
        raise TypeError("current geometry must expose protected physical role maps")
    tnuts = protected.get("tnuts")
    lights = protected.get("lights")
    wires = protected.get("wires")
    if not isinstance(tnuts, Mapping) or not isinstance(lights, Mapping):
        raise TypeError("current geometry must expose existing T-nut and LED solids")
    if not isinstance(wires, Mapping):
        raise TypeError("current geometry must expose its modeled wire spans")
    if len(wires) != EXPECTED_WIRE_COUNT:
        raise ValueError(
            f"current midpoint inputs require 131 modeled wires, found {len(wires)}"
        )
    if len(lights) != EXPECTED_EXISTING_LED_COUNT or "light_G2" not in lights:
        raise ValueError(
            "current midpoint inputs require all 132 LED bodies including G2"
        )
    actual_g2 = _validate_current_g2_shape(geometry, lights)
    _validate_live_tnut_grid(geometry)

    raw_receivers, finished_scene_wood = wj12_diagnostic._composed_wood(geometry)
    del raw_receivers
    targets, display_proxy_ids = retained_access._frame_targets(geometry)
    obstacles, access_only = retained_access._retained_scene_obstacles(
        geometry, finished_scene_wood, targets
    )

    timber_ids = _wood_member_ids(geometry)
    wood = {}
    for name in timber_ids:
        obstacle_id = f"wood/{name}"
        if obstacle_id not in obstacles:
            raise ValueError(f"current obstacle map omits timber member {obstacle_id}")
        wood[name] = obstacles[obstacle_id]
    candidate_pool = {
        axis_id: {
            role: _require_scene_shape(
                obstacles, f"candidate_stack/{axis_id}/{role}", shape
            )
            for role, shape in roles.items()
        }
        for axis_id, roles in candidate_hardware.items()
    }
    retained_pool = {
        axis_id: {
            **target,
            "roles": {
                role: _require_scene_shape(
                    obstacles, f"candidate_stack/{axis_id}/{role}", shape
                )
                for role, shape in target["roles"].items()
            },
        }
        for axis_id, target in targets.items()
    }
    fixed_pool = {}
    for axis_id, shape in fixed_axes.items():
        obstacle_id = f"fixed_panel_axis/{axis_id}"
        fixed_pool[axis_id] = _require_scene_shape(obstacles, obstacle_id, shape)
    tnut_pool = {
        name: _require_scene_shape(obstacles, f"protected/tnuts/{name}", shape)
        for name, shape in tnuts.items()
    }
    light_pool = {
        name: _require_scene_shape(obstacles, f"protected/lights/{name}", shape)
        for name, shape in lights.items()
    }
    pool_counts = _validate_pool_counts(
        wood,
        candidate_pool,
        retained_pool,
        fixed_pool,
        tnut_pool,
        light_pool,
    )

    pools = {
        "timber": wood,
        "structural_hardware": {
            **{
                f"candidate/{axis_id}/{role}": shape
                for axis_id, roles in candidate_pool.items()
                for role, shape in roles.items()
            },
            **{
                f"retained/{axis_id}/{role}": shape
                for axis_id, target in retained_pool.items()
                for role, shape in target["roles"].items()
            },
            **{
                f"panel screw/{axis_id}": shape for axis_id, shape in fixed_pool.items()
            },
        },
        "existing_hold_or_LED": {**tnut_pool, **light_pool},
    }
    bounds = {
        group: {
            name: historical_midpoints._bbox(shape) for name, shape in shapes.items()
        }
        for group, shapes in pools.items()
    }

    site_rows: list[dict[str, Any]] = []
    for index, site in enumerate(rows):
        site = dict(site)
        if site["surface"] == "main":
            rear = geometry.source.b.point(
                site["x_mm"] - geometry.source.b.HALF, site["s_mm"], 0.0
            )
            normal = geometry.source.b.normal().normalized()
        else:
            rear = cq.Vector(
                site["x_mm"] - geometry.source.b.HALF,
                geometry.source.base.HEADER_FRONT_Y,
                geometry.source.b.V1_KICKER_HEIGHT_MM + site["s_mm"],
            )
            normal = cq.Vector(0.0, -1.0, 0.0)
        site["rear_xyz_mm"] = list(rear.toTuple())
        probes = {
            "flange": cq.Solid.makeCylinder(
                historical_midpoints.FLANGE_DIAMETER_MM / 2,
                historical_midpoints.FLANGE_THICKNESS_MM,
                rear,
                normal,
            ),
            "rear_projection": cq.Solid.makeCylinder(
                historical_midpoints.PROJECTION_DIAMETER_MM / 2,
                historical_midpoints.PROJECTION_LENGTH_MM,
                rear,
                normal,
            ),
        }
        hits = {group: [] for group in pools}
        for probe_name, probe in probes.items():
            box = historical_midpoints._bbox(probe)
            for group, shapes in pools.items():
                for name, shape in shapes.items():
                    if not historical_midpoints._overlap(box, bounds[group][name]):
                        continue
                    intersection = probe.intersect(shape)
                    volume = intersection.Volume()
                    if volume <= historical_midpoints.VOLUME_TOLERANCE_MM3:
                        continue
                    hit = {
                        "member": name,
                        "envelope": probe_name,
                        "intersection_mm3": round(volume, 6),
                    }
                    if group == "timber" and probe_name == "rear_projection":
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
            if any(hit["envelope"] == "flange" for hit in hits["timber"])
            else "rear projection blocked"
            if hits["timber"]
            else "no timber hit within envelope"
        )
        site_rows.append(site)
        if progress and (index + 1) % 100 == 0:
            progress(f"current midpoint geometry screen: {index + 1}/491 sites")

    groups = {}
    for family, direction in sorted(
        {(row["family"], row["direction"]) for row in site_rows}
    ):
        subset = [
            row
            for row in site_rows
            if row["family"] == family and row["direction"] == direction
        ]
        groups[f"{family} / {direction}"] = {
            "sites": len(subset),
            "timber_blocked": sum(bool(row["hits"]["timber"]) for row in subset),
            "flange_blocked": sum(
                row["timber_status"] == "flange blocked" for row in subset
            ),
            "structural_hardware_blocked": sum(
                bool(row["hits"]["structural_hardware"]) for row in subset
            ),
            "existing_hold_or_LED_overlap": sum(
                bool(row["hits"]["existing_hold_or_LED"]) for row in subset
            ),
            "timber_members": dict(
                Counter(
                    member
                    for row in subset
                    for member in {hit["member"] for hit in row["hits"]["timber"]}
                )
            ),
        }

    source_code_hashes = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in _SOURCE_CODE_PATHS
    }
    access_exclusion_counts = dict(Counter(row["family"] for row in access_only))
    expected_access_exclusion_counts = {
        "retained_12_frame_bolt_tools_withdrawals": 36,
        "hold_hole_and_provisional_projection": 142,
    }
    if access_exclusion_counts != expected_access_exclusion_counts:
        raise ValueError(
            "current midpoint exclusions differ from the live access-proxy inventory"
        )
    if len(display_proxy_ids) != EXPECTED_RETAINED_FRAME_BOLT_COUNT:
        raise ValueError(
            "exactly twelve retained source-axis display proxies must be excluded"
        )
    return {
        "schema": SCHEMA,
        "revision_id": CURRENT_REVISION_ID,
        "geometry_snapshot_sha256_canonical": snapshot_sha256,
        "source_inventory_sha256": source_inventory_sha256,
        "current_revision_report_sha256": revision_report_sha256,
        "current_revision_verification_sha256": verification_sha256,
        "source_code_sha256": source_code_hashes,
        "output_directory": output_directory,
        "scope": (
            "Hypothetical nearest-neighbor midpoints on the current WJ24 revision; "
            "not a selected future hold layout or product-compatibility result."
        ),
        "grid": {
            "site_count": len(site_rows),
            "counts": {
                "LED / horizontal": sum(
                    row["family"] == "LED" and row["direction"] == "horizontal"
                    for row in site_rows
                ),
                "LED / vertical": sum(
                    row["family"] == "LED" and row["direction"] == "vertical"
                    for row in site_rows
                ),
                "T-nut / horizontal": sum(
                    row["family"] == "T-nut" and row["direction"] == "horizontal"
                    for row in site_rows
                ),
                "T-nut / vertical": sum(
                    row["family"] == "T-nut" and row["direction"] == "vertical"
                    for row in site_rows
                ),
                "kicker T-nut / horizontal": sum(
                    row["family"] == "kicker T-nut" and row["direction"] == "horizontal"
                    for row in site_rows
                ),
            },
            "led_datum_overrides_mm": {"G2": list(actual_g2)},
            "led_midpoint_sites_affected_by_g2": sorted(
                row["id"]
                for row in site_rows
                if row["family"] == "LED" and "G2" in row["endpoints"]
            ),
            "site_ids_and_neighbors": "reused from historical midpoint grid; only LED endpoint G2 is repositioned",
        },
        "envelopes": {
            "flange_diameter_mm": historical_midpoints.FLANGE_DIAMETER_MM,
            "flange_rear_thickness_mm": historical_midpoints.FLANGE_THICKNESS_MM,
            "rear_projection_diameter_mm": historical_midpoints.PROJECTION_DIAMETER_MM,
            "rear_projection_length_mm": historical_midpoints.PROJECTION_LENGTH_MM,
        },
        "object_inventory": {
            **pool_counts,
            "display_only_frame_axis_proxies_excluded": len(display_proxy_ids),
            "temporary_tool_and_withdrawal_envelopes_excluded_by_family": access_exclusion_counts,
            "modeled_wire_spans_not_in_historical_midpoint_obstacle_scope": len(wires),
            "current_panel_replacement_bodies_outside_midpoint_scope": len(
                getattr(geometry, "panel_replacements", {})
            ),
        },
        "groups": groups,
        "sites": site_rows,
        "joint_evaluations_run": False,
        "candidate_accepted": False,
        "limits": [
            "The screen uses the historical nearest-neighbor site definitions and provisional flange/rear-projection envelopes.",
            "The current G2 LED datum is +5 mm X at panel coordinates (1405, 199.2) mm; its four adjacent LED midpoint sites are recomputed.",
            "Current 44 timber members, 92 candidate stacks, 12 retained physical bolt stacks, 66 panel screw axes, 142 existing T-nuts, and 132 existing LED bodies are screened.",
            "Twelve source occupied-axis display proxies, 36 retained-bolt tool/withdrawal envelopes, and 142 hold-hole/rear-projection envelopes are excluded as non-installed access proxies.",
            "Wires and plywood bodies remain outside the historical midpoint obstacle scope; this is not a full service-state or panel-fit check.",
            "Plywood is excluded intentionally because candidate panel bores are hypothetical; no panel holes or parts are changed.",
            "The 50.8 mm rear projection is provisional and does not establish compatibility with any future hold, bolt, retainer, or tool.",
            "No native mechanics or joint evaluation is performed, and a no-hit site is not an approval of a future setting.",
        ],
    }
