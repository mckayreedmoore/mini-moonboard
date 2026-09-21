"""Detached PB05 outer rail-hole offset trial; fixed A12 actions are not a new solve."""

import json
from unittest.mock import patch

from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_cross_family as cross
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_outer_pair as upper
from scripts import simple_pb05_first_case_demand as demand
from scripts import simple_pb05_narrow_outer_screen as narrow
from scripts import simple_pb05_native as pb05

TRIAL_OFFSETS_MM = (26.0, 70.0)
TRIAL_UPPER_N_MM = 45.0
SPECS = {**lower.STATION_SPECS, **upper.STATION_SPECS, **bottom.STATION_SPECS}


def _shift_signed(old, direction, delta_xyz):
    """Translate a signed NDS center-distance check under an unchanged load sign."""
    revised = {}
    for key, axis in (
        ("grain_end", direction["grain_axis_xyz"]),
        ("cross_grain_edge", direction["edge_axis_xyz"]),
    ):
        check = old[key]
        if not check["applicable"]:
            revised[key] = check
            continue
        step = sum(a * b for a, b in zip(axis, delta_xyz, strict=True))
        if check["sign"] == "negative":
            step = -step
        loaded = check["loaded_distance_mm"] - step
        unloaded = check["unloaded_distance_mm"] + step
        revised[key] = {
            **check,
            "loaded_distance_mm": loaded,
            "unloaded_distance_mm": unloaded,
            "loaded_margin_mm": loaded - check["loaded_required_mm"],
            "unloaded_margin_mm": unloaded - check["unloaded_required_mm"],
            "passes": loaded + 1e-8 >= check["loaded_required_mm"]
            and unloaded + 1e-8 >= check["unloaded_required_mm"],
        }
    return {**revised, "passes": all(row["passes"] for row in revised.values())}


def _installed(item):
    """Reuse PB05's nominal no-pocket stacks, including full shaft lengths."""
    rows = {}
    for bolt in item.bolts:
        if bolt.members[0] == item.upright_name:
            rows[bolt.name] = narrow._installed_upright(bolt)
        else:
            stack = dict(item.stacks[bolt.name])
            axis = bolt.direction.normalized()
            wood_start = bolt.start + axis * lower.END_ALLOWANCE_MM
            stack["shaft"] = narrow.hardware._cylinder(
                (wood_start - axis * 2).toTuple(),
                axis.toTuple(),
                5 * narrow.hardware.MM_PER_IN,
                lower.BOLT_DIAMETER_MM,
            )
            rows[bolt.name] = stack
    return rows


def _upper_trial():
    """Rebuild just the displaced family and check its exact installed envelope."""
    module = pb05.PB05Native()
    reference = module.pb03_geometries()
    parts, finished, panels, _, connections = lower._source_inventory()
    if (
        tuple(map(narrow._signature, panels))
        != tuple(map(narrow._signature, module.panel_connections()))
        or len(panels) != 66
        or len(module.legacy_proxy_stations()) != 14
    ):
        raise ValueError("fixed panel or legacy duties changed")
    fixed_axes = lower._fixed_axis_solids(panels)
    frame_axes = {
        row.name: narrow._axis(row) for row in connections if row.kind == "bolt"
    }
    if len(frame_axes) != 12:
        raise ValueError("frame bolt inventory changed")
    with (
        patch.object(lower, "BLOCK_X_MM", pb05.BLOCK_X_MM),
        patch.object(lower, "RAIL_X_OFFSETS_MM", TRIAL_OFFSETS_MM),
    ):
        trial = {
            name: lower._build_station(
                SPECS[name],
                parts,
                finished,
                fixed_axes,
                rail_n_offset_mm=(
                    TRIAL_UPPER_N_MM
                    if name in upper.TARGET_STATIONS
                    else lower.RAIL_N_OFFSET_MM
                ),
            )
            for name in pb05.OUTER_STATIONS
        }
    combined = {
        **{name: reference[name] for name in lower.TARGET_STATIONS},
        **trial,
    }
    revised = {name: trial[name] for name in upper.TARGET_STATIONS}
    others = {name: item for name, item in combined.items() if name not in revised}
    cross_hits = cross.screen_cross_family(revised, others)
    installed = {name: _installed(item) for name, item in combined.items()}
    fixed = {
        **{
            f"panel/{name}": shape
            for name, shape in finished.items()
            if name.startswith(("main_", "kicker_"))
        },
        **{f"panel_axis/{name}": shape for name, shape in fixed_axes.items()},
        **{f"frame_axis/{name}": shape for name, shape in frame_axes.items()},
    }
    hits = {}
    local = {}
    for name, item in revised.items():
        local[name] = {
            "contact": item.report["contact_verified"],
            "complete_bores": item.report["complete_bores"],
            "collision": item.report["collision_clear"],
            "access": item.report["access_clear"],
        }
        nonhosts = {
            f"wood/{key}": shape
            for key, shape in finished.items()
            if key not in (item.upright_name, item.rail_name)
            and not key.startswith(("main_", "kicker_"))
        }
        opposite = {key: other for key, other in combined.items() if key != name}
        external = {
            **fixed,
            **nonhosts,
            **{f"block/{key}": other.block for key, other in opposite.items()},
            **{
                f"bore/{key}/{bolt}": shape
                for key, other in opposite.items()
                for bolt, shape in other.bores.items()
            },
            **{
                f"stack/{key}/{bolt}/{role}": shape
                for key in opposite
                for bolt, stack in installed[key].items()
                for role, shape in stack.items()
            },
        }
        own_installed = installed[name]
        for bolt in item.bolts:
            own_other = {
                f"own/{other}/{role}": shape
                for other, stack in own_installed.items()
                if other != bolt.name
                for role, shape in stack.items()
            }
            own_other.update(
                {
                    f"own_bore/{other}": shape
                    for other, shape in item.bores.items()
                    if other != bolt.name
                }
            )
            for role, shape in own_installed[bolt.name].items():
                hits.update(
                    {
                        f"{bolt.name}/{role}|{target}": volume
                        for target, volume in narrow._hits(
                            shape, {**external, **own_other}
                        ).items()
                    }
                )
            for end, shape in item.tools[bolt.name].items():
                hits.update(
                    {
                        f"{bolt.name}/tool/{end}|{target}": volume
                        for target, volume in narrow._hits(shape, external).items()
                    }
                )
        reverse_targets = {
            f"block/{name}": item.block,
            **{f"bore/{bolt}": shape for bolt, shape in item.bores.items()},
            **{
                f"tool/{bolt}/{end}": shape
                for bolt, ends in item.tools.items()
                for end, shape in ends.items()
            },
        }
        for other in opposite:
            for bolt, stack in installed[other].items():
                for role, shape in stack.items():
                    hits.update(
                        {
                            f"stack/{other}/{bolt}/{role}|{target}": volume
                            for target, volume in narrow._hits(
                                shape, reverse_targets
                            ).items()
                        }
                    )
    return (
        reference,
        trial,
        {
            "local": local,
            "cross_family": cross_hits,
            "full_nominal_stack_and_tool_hits_mm3": hits,
            "passes": all(all(row.values()) for row in local.values())
            and cross_hits["all_cross_family_collision_gates_pass"]
            and not hits,
        },
    )


def screen():
    """Check X and upper-row N moves; original actions are sensitivity only."""
    if (
        pb05.BLOCK_X_MM != narrow.BLOCK_X_MM
        or pb05.RAIL_X_OFFSETS_MM != (25.0, 70.0)
        or set(pb05.OUTER_STATIONS) != set(narrow.OUTER_STATIONS)
    ):
        raise ValueError("PB05 outer source geometry changed")
    actions = demand.analyze()
    if (
        actions["source_identity"]["fixed_panel_kicker_axes"] != 66
        or actions["source_identity"]["legacy_proxy_stations"] != 14
    ):
        raise ValueError("PB05 fixed policy changed")
    # ponytail: the existing exact six-station screen already checks full stacks,
    # seats, access, other timber, panels, and fixed axes; change only its input.
    with patch.object(narrow, "RAIL_X_OFFSETS_MM", TRIAL_OFFSETS_MM):
        geometry = narrow.screen()
    reference, revised, upper_geometry = _upper_trial()
    inventory = geometry["inventory"]
    if inventory != {
        "outer_stations": 6,
        "unchanged_center_stations": 2,
        "outer_bolt_axes": 24,
        "fixed_panel_kicker_axes": 66,
        "original_frame_bolt_axes": 12,
        "legacy_duties": 14,
    }:
        raise ValueError("trial topology changed")
    signed = {}
    for bolt in actions["bolts"]:
        if bolt["station"] not in pb05.OUTER_STATIONS or "_rail_" not in bolt["name"]:
            continue
        station = geometry["stations"][bolt["station"]]
        if tuple(station["rail_x_offsets_from_butt_mm"]) != TRIAL_OFFSETS_MM:
            raise ValueError("trial rail coordinates changed")
        old_axis = next(
            row for row in reference[bolt["station"]].bolts if row.name == bolt["name"]
        )
        new_axis = next(
            row for row in revised[bolt["station"]].bolts if row.name == bolt["name"]
        )
        delta = tuple((new_axis.start - old_axis.start).toTuple())
        checks = {
            member: _shift_signed(
                bolt["signed_end_edge"]["members"][member],
                bolt["member_directions"][member],
                delta,
            )
            for member in bolt["members"]
        }
        signed[bolt["name"]] = {
            "station": bolt["station"],
            "old_point_xyz_mm": bolt["point_xyz_mm"],
            "trial_point_xyz_mm": [
                old + change
                for old, change in zip(bolt["point_xyz_mm"], delta, strict=True)
            ],
            "original_passes": bolt["signed_end_edge"]["passes"],
            "fixed_action_trial": checks,
            "trial_passes": all(check["passes"] for check in checks.values()),
        }
    if len(signed) != 12:
        raise ValueError("outer rail-bolt demand inventory changed")
    geometry_pass = (
        geometry["decision"] == "ADVANCE_GEOMETRY_ONLY" and upper_geometry["passes"]
    )
    signed_pass = all(row["trial_passes"] for row in signed.values())
    return {
        "schema": "simple_pb05_outer_rail_revision/v1",
        "candidate": pb05.SOURCE_ID,
        "original_offsets_from_butt_mm": pb05.RAIL_X_OFFSETS_MM,
        "trial_offsets_from_butt_mm": TRIAL_OFFSETS_MM,
        "trial_upper_rail_n_offset_mm": TRIAL_UPPER_N_MM,
        "source_report_sha256": demand.REPORT_SHA256,
        "source_geometry_fingerprint_sha256": actions["source_identity"][
            "geometry_fingerprint_sha256"
        ],
        "inventory": inventory,
        "geometry": geometry,
        "upper_shift_geometry": upper_geometry,
        "signed_end_edge": signed,
        "geometry_pass": geometry_pass,
        "fixed_action_signed_pass": signed_pass,
        "decision": "ADVANCE_TO_NEW_NATIVE_SOLVE"
        if geometry_pass and signed_pass
        else "REVISE",
        "limits": [
            "The A12 actions and signs are from the original PB05 geometry; moved holes require a new native solve.",
            "No complete group, net-section, splitting, oblique shear, washer, steel, or six-case joint verdict.",
            "Nominal 5-in rail shaft and generic stack/access envelopes are not SKU-controlled hardware.",
        ],
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
