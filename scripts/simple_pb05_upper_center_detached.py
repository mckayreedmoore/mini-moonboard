"""Detached upper-center pair against committed PB05 solids; geometry only."""

import json
import math

import cadquery as cq

from scripts import simple_pb03_cross_family as cross
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_center_pair as upper_center
from scripts import simple_pb05_narrow_outer_screen as retail
from scripts import simple_pb05_native as pb05


def _hits(shape, others):
    return {
        name: round(volume, 6)
        for name, other in others.items()
        if (volume := lower._intersection_volume(shape, other)) > lower.TOL_MM3
    }


def _axis(row):
    return cq.Solid.makeCylinder(row.diameter / 2, row.length, row.start, row.direction)


def _signature(row):
    return (
        row.name,
        row.start.toTuple(),
        row.direction.toTuple(),
        row.length,
        row.diameter,
        row.members,
        row.kind,
        row.grip,
    )


def _same_shape(first, second):
    return first.distance(second) < 1e-8 and math.isclose(
        first.Volume(), second.Volume(), abs_tol=1e-5
    )


def build_inputs():
    """Reuse the prior pair while retaining PB05 legacy duties in source."""
    return upper_center.build_pair(), pb05.PB05Native()


def screen(*, pair=None, module=None):
    if pair is None or module is None:
        if pair is not None or module is not None:
            raise ValueError("candidate pair and PB05 module must be supplied together")
        pair, module = build_inputs()
    if (
        module.KEY != pb05.SOURCE_ID
        or module.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
    ):
        raise ValueError("PB05 source identity changed")
    reference = module.pb03_geometries()
    if set(pair) != set(upper_center.TARGET_STATIONS) or set(reference) != set(
        pb05.OUTER_STATIONS
    ) | set(lower.TARGET_STATIONS):
        raise ValueError("PB05 or candidate station inventory changed")

    actual = {part.name: part.shape for part in module.wood_parts()}
    source_parts, finished, panels, _, source_connections = lower._source_inventory()
    panel_axes = tuple(module.panel_connections())
    frame_axes = tuple(
        row
        for row in module.connections()
        if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    source_frame = tuple(row for row in source_connections if row.kind == "bolt")
    legacy = tuple(
        row
        for row in module.connections()
        if any(
            row.name.startswith(station + "_")
            for station in upper_center.TARGET_STATIONS
        )
    )
    all_legacy = tuple(
        row for row in module.connections() if row.name.startswith("clip_")
    )
    fixed_axes = lower._fixed_axis_solids(panel_axes)
    receiver_support = lower._receiver_support(panel_axes, source_parts)
    blocks = {name: actual[item.block_name] for name, item in reference.items()}
    panels_actual = {
        name: shape
        for name, shape in actual.items()
        if name.startswith(("main_", "kicker_"))
    }
    candidate_members = {
        member
        for item in pair.values()
        for member in (item.upright_name, item.rail_name)
    }

    # ponytail: the same exact-volume screen handles every candidate feature.
    features = {f"block/{station}": item.block for station, item in pair.items()}
    features.update(
        {
            f"bore/{station}/{name}": shape
            for station, item in pair.items()
            for name, shape in item.bores.items()
        }
    )
    features.update(
        {
            f"stack/{station}/{name}/{role}": shape
            for station, item in pair.items()
            for name, stack in item.stacks.items()
            for role, shape in stack.items()
        }
    )
    features.update(
        {
            f"tool/{station}/{name}/{end}": shape
            for station, item in pair.items()
            for name, ends in item.tools.items()
            for end, shape in ends.items()
        }
    )
    families = {
        "pb05_blocks": blocks,
        "pb05_bores": {
            f"{station}/{name}": shape
            for station, item in reference.items()
            for name, shape in item.bores.items()
        },
        "pb05_stacks": {
            f"{station}/{name}/{role}": shape
            for station, item in reference.items()
            for name, stack in item.stacks.items()
            for role, shape in stack.items()
        },
        "pb05_tools": {
            f"{station}/{name}/{end}": shape
            for station, item in reference.items()
            for name, ends in item.tools.items()
            for end, shape in ends.items()
        },
        "frame_bolt_axes": {row.name: _axis(row) for row in frame_axes},
        "panel_kicker_axes": fixed_axes,
        "panel_solids": panels_actual,
        "unrelated_timber": {
            name: shape
            for name, shape in finished.items()
            if name not in panels_actual and name not in candidate_members
        },
    }
    collisions = {
        family: {
            f"{feature}|{target}": volume
            for feature, shape in features.items()
            for target, volume in _hits(shape, solids).items()
        }
        for family, solids in families.items()
    }
    pair_interactions = cross.screen_cross_family(
        {upper_center.TARGET_STATIONS[0]: pair[upper_center.TARGET_STATIONS[0]]},
        {upper_center.TARGET_STATIONS[1]: pair[upper_center.TARGET_STATIONS[1]]},
    )
    local = {station: item.report for station, item in pair.items()}

    # The listed upright retail bolt can be checked; the rail product is unselected.
    retail_shapes = {}
    retail_grip = {}
    for station, item in pair.items():
        for bolt in item.bolts:
            if bolt.members[0] == item.upright_name:
                retail_shapes.update(
                    {
                        f"{station}/{bolt.name}/{role}": shape
                        for role, shape in retail._installed_upright(bolt).items()
                    }
                )
                required = (
                    bolt.grip
                    + 2 * retail.hardware.WASHER_EACH_SIDE_MM
                    + retail.hardware.NUT_HEIGHT_MM
                    + retail.hardware.TWO_THREAD_PROJECTION_MM
                )
                retail_grip[bolt.name] = {
                    "nominal_length_margin_mm": retail.hardware.BOLT_LENGTH_MM
                    - required,
                    "nut_on_listed_thread": (
                        bolt.grip + 2 * retail.hardware.WASHER_EACH_SIDE_MM
                        >= retail.hardware.BOLT_LENGTH_MM
                        - retail.hardware.BOLT_LISTED_THREAD_LENGTH_MM
                    ),
                }
    retail_fixed = {
        **families["pb05_blocks"],
        **families["frame_bolt_axes"],
        **families["panel_kicker_axes"],
        **families["panel_solids"],
        **families["unrelated_timber"],
    }
    retail_hits = {}
    for name, shape in retail_shapes.items():
        station = name.split("/", 1)[0]
        other_pair = {
            key: solid
            for key, solid in features.items()
            if key.split("/", 2)[1] != station
        }
        retail_hits.update(
            {
                f"{name}|{target}": volume
                for target, volume in _hits(
                    shape, {**retail_fixed, **other_pair}
                ).items()
            }
        )
    source_preserved = (
        len(legacy) == 12
        and all(row.kind == "screw" for row in legacy)
        and len(all_legacy) == 84
        and all(row.kind == "screw" for row in all_legacy)
        and len(module.legacy_proxy_stations()) == 14
        and len(frame_axes) == len(source_frame) == 12
        and tuple(map(_signature, frame_axes)) == tuple(map(_signature, source_frame))
        and len(panel_axes) == len(panels) == 66
        and tuple(map(_signature, panel_axes)) == tuple(map(_signature, panels))
        and len(panels_actual) == 6
        and all(
            _same_shape(shape, finished[name]) for name, shape in panels_actual.items()
        )
        and len(blocks) == 8
        and all(
            _same_shape(blocks[name], item.block) for name, item in reference.items()
        )
        and all(
            reference[name].report["block_dimensions_mm"] == [95.25, 57.15, 300.0]
            for name in pb05.OUTER_STATIONS
        )
        and all(
            reference[name].report["block_dimensions_mm"] == [139.7, 57.15, 300.0]
            for name in lower.TARGET_STATIONS
        )
    )
    gates = {
        "source_preserved": source_preserved,
        "candidate_inventory": len(pair) == 2
        and all(
            len(item.bolts)
            == len(item.bores)
            == len(item.stacks)
            == len(item.tools)
            == 4
            for item in pair.values()
        ),
        "complete_candidate_bores": all(
            row["complete_bores"] for row in local.values()
        ),
        "fixed_receivers_supported": len(receiver_support) == 66
        and all(receiver_support.values()),
        "local_geometry_clear": all(
            row["collision_clear"] and row["access_clear"] and row["contact_verified"]
            for row in local.values()
        ),
        "pair_geometry_clear": pair_interactions[
            "all_cross_family_collision_gates_pass"
        ],
        "pb05_and_fixed_geometry_clear": not any(collisions.values()),
        "listed_upright_retail_clear": not retail_hits
        and len(retail_grip) == 4
        and all(
            row["nominal_length_margin_mm"] >= 0 and row["nut_on_listed_thread"]
            for row in retail_grip.values()
        ),
    }
    return {
        "schema": "simple_pb05_upper_center_detached/v1",
        "source_id": pb05.SOURCE_ID,
        "candidate_stations": list(pair),
        "inventory": {
            "pb05_outer_blocks": len(pb05.OUTER_STATIONS),
            "pb05_unchanged_center_blocks": len(reference) - len(pb05.OUTER_STATIONS),
            "candidate_blocks": len(pair),
            "candidate_bolt_axes": sum(len(item.bolts) for item in pair.values()),
            "legacy_sds_axes_retained": len(legacy),
            "legacy_sds_axes_total_retained": len(all_legacy),
            "original_frame_bolt_axes": len(frame_axes),
            "fixed_panel_kicker_axes": len(panel_axes),
        },
        "hypothetical_duties": {"before": 14, "after": 12},
        "stations": local,
        "pair_interactions": pair_interactions,
        "collision_hits_mm3": collisions,
        "retail_upright": {
            "product_basis": "listed 8-in bolt, washer and nut envelope",
            "rail_product_selected": False,
            "grip": retail_grip,
            "collision_hits_mm3": retail_hits,
        },
        "gates": gates,
        "geometry_decision": "ADVANCE_GEOMETRY_ONLY"
        if all(gates.values())
        else "REVISE_GEOMETRY",
        "strength_checked": False,
        "installed_retail_stacks_checked": False,
        "native_solve": False,
        "acceptance": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
