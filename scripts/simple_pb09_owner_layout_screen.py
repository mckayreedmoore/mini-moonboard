"""Detached 139.7-mm ten-block owner-layout geometry screen; no native solve."""

import hashlib
from dataclasses import replace
from itertools import combinations
from pathlib import Path
from unittest.mock import patch

import cadquery as cq

from mini_moonboard import no_shoes_frame, round_structural_wiring
from scripts import owner_layout_protected as protected
from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_cross_family as cross
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_center_pair as upper_center
from scripts import simple_pb03_upper_outer_pair as upper_outer
from scripts import simple_pb05_narrow_outer_screen as narrow
from scripts import simple_pb05_short_block_screen as short
from scripts import simple_pb07_outer_rail_native as pb07

SOURCE_ID = "pb09-owner-139p7-ten-block-layout-v1"
LAYOUT_REVISION = "lower-service-wire-channel-v3"
LENGTH_MM = 139.7
OUTER_WIDTH_MM = 101.6
CENTER_WIDTH_MM = 114.3
RAIL_X_MM = (46.0, 74.0)
UPRIGHT_N_MM = (60.0, 92.25)
LOWER_SERVICE_T_MM = 76.2
OTHER_T_MM = 57.15
WIRE_CHANNEL_RADIUS_MM = 5.0
SERVICE_CHANNEL_QUALIFIED = False
LOWER_RAIL_N_MM = lower.RAIL_N_OFFSET_MM
UPPER_OUTER_RAIL_N_MM = 45.0
UPPER_CENTER_RAIL_N_MM = 45.0
CONDITIONAL_TOOL_DIAMETER_MM = 25.4
STATIONS = (
    *lower.TARGET_STATIONS,
    *pb07.OUTER_STATIONS,
    *upper_center.TARGET_STATIONS,
)
SPECS = {
    **lower.STATION_SPECS,
    **upper_outer.STATION_SPECS,
    **bottom.STATION_SPECS,
    **upper_center.STATION_SPECS,
}
_NO_RELEASE = {
    "native_solve": False,
    "force_transfer": False,
    "acceptance": False,
    "drilling_released": False,
    "fabrication_released": False,
    "structural_released": False,
}


def layout_reserves():
    """Signed center-distance margins; loading directions still need a solve."""
    seven_d = 7 * lower.BOLT_DIAMETER_MM
    four_d = 4 * lower.BOLT_DIAMETER_MM
    margins = {
        "upright_pitch_4d_mm": UPRIGHT_N_MM[1] - UPRIGHT_N_MM[0] - four_d,
        "outer_near_rail_end_7d_mm": RAIL_X_MM[0] - seven_d,
        "outer_far_x_loaded_edge_4d_mm": OUTER_WIDTH_MM - RAIL_X_MM[1] - four_d,
        "outer_rail_row_spacing_4d_mm": RAIL_X_MM[1] - RAIL_X_MM[0] - four_d,
        "center_far_x_loaded_edge_4d_mm": CENTER_WIDTH_MM - RAIL_X_MM[1] - four_d,
    }
    for label, n in (
        ("upright_front", UPRIGHT_N_MM[0]),
        ("upright_rear", UPRIGHT_N_MM[1]),
        ("lower_rail", LOWER_RAIL_N_MM),
        ("upper_outer", UPPER_OUTER_RAIL_N_MM),
        ("upper_center", UPPER_CENTER_RAIL_N_MM),
    ):
        margins[f"{label}_front_end_7d_mm"] = round(n - seven_d, 6)
        margins[f"{label}_rear_end_7d_mm"] = round(LENGTH_MM - n - seven_d, 6)
    return margins


def _n_bounds(shape):
    return (
        min(v.Y * lower.pb01.N[0] + v.Z * lower.pb01.N[1] for v in shape.Vertices()),
        max(v.Y * lower.pb01.N[0] + v.Z * lower.pb01.N[1] for v in shape.Vertices()),
    )


def _bolt_grip(geometry):
    """Nominal 8-in upright fit; excess projection is not a hardware approval."""
    hw = narrow.hardware
    grip = next(
        bolt.grip for bolt in geometry.bolts if bolt.members[0] == geometry.upright_name
    )
    nut_start = hw.WASHER_EACH_SIDE_MM * 2 + grip
    nut_end = nut_start + hw.NUT_HEIGHT_MM
    return {
        "wood_grip_mm": round(grip, 6),
        "nominal_bolt_length_mm": hw.BOLT_LENGTH_MM,
        "nominal_thread_start_mm": hw.BOLT_LENGTH_MM - hw.BOLT_LISTED_THREAD_LENGTH_MM,
        "nut_start_from_under_head_mm": round(nut_start, 6),
        "nut_end_from_under_head_mm": round(nut_end, 6),
        "projection_past_nut_mm": round(hw.BOLT_LENGTH_MM - nut_end, 6),
        "excess_projection_needs_stock_review": (
            hw.BOLT_LENGTH_MM - nut_end > hw.TWO_THREAD_PROJECTION_MM + 3.0
        ),
        "two_thread_projection_margin_mm": round(
            hw.BOLT_LENGTH_MM - nut_end - hw.TWO_THREAD_PROJECTION_MM, 6
        ),
        "nut_on_listed_thread": nut_start
        >= hw.BOLT_LENGTH_MM - hw.BOLT_LISTED_THREAD_LENGTH_MM,
    }


def _rail_grip(geometry):
    """Check the old generic 5-in rail trial against the new T thickness."""
    hw = narrow.hardware
    grip = next(
        bolt.grip for bolt in geometry.bolts if bolt.members[0] == geometry.rail_name
    )
    required = (
        grip
        + 2 * hw.WASHER_EACH_SIDE_MM
        + hw.NUT_HEIGHT_MM
        + hw.TWO_THREAD_PROJECTION_MM
    )
    return {
        "wood_grip_mm": round(grip, 6),
        "generic_5in_two_thread_margin_mm": round(5 * hw.MM_PER_IN - required, 6),
        "retail_rail_bolt_selected": False,
    }


def _conditional_tools(bolt):
    """Same 40-mm access depth, smaller unselected cylindrical tool envelope."""
    direction = bolt.direction.normalized()
    near = bolt.start + direction * lower.END_ALLOWANCE_MM
    far = near + direction * (bolt.grip + 2.0)
    return {
        "near": narrow.hardware._cylinder(
            near.toTuple(),
            (-direction).toTuple(),
            lower.TOOL_DEPTH_MM,
            CONDITIONAL_TOOL_DIAMETER_MM,
        ),
        "far": narrow.hardware._cylinder(
            far.toTuple(),
            direction.toTuple(),
            lower.TOOL_DEPTH_MM,
            CONDITIONAL_TOOL_DIAMETER_MM,
        ),
    }


def _wire_channel():
    """A provisional 3-mm radial service allowance about the modeled E6–E7 wire."""
    record = next(
        item
        for item in round_structural_wiring.segments()
        if item["name"] == "wire_054_E6_E7"
    )
    path = round_structural_wiring.wire_path(record).translate(no_shoes_frame.SHIFT)
    first, second = (
        round_structural_wiring.b.point(*record["route_local_mm"][index])
        + no_shoes_frame.SHIFT
        for index in (0, 1)
    )
    plane = cq.Plane(origin=first, normal=(second - first).normalized())
    return (
        cq.Workplane(plane)
        .circle(WIRE_CHANNEL_RADIUS_MM)
        .sweep(cq.Workplane(obj=path), isFrenet=True)
        .val()
    )


def _build(module):
    source = module.pb03_geometries()
    parts, finished, panels, _, connections = lower._source_inventory()
    panel_axes = tuple(map(narrow._signature, module.panel_connections()))
    frame = tuple(
        row
        for row in module.connections()
        if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    source_frame = tuple(row for row in connections if row.kind == "bolt")
    legacy = set(module.legacy_proxy_stations())
    sds = tuple(row for row in module.connections() if row.name.startswith("clip_"))
    if (
        module.KEY != pb07.SOURCE_ID
        or set(source) != set(STATIONS)
        or len(source) != 10
        or len(panels) != 66
        or panel_axes != tuple(map(narrow._signature, panels))
        or len(frame) != 12
        or len(source_frame) != 12
        or tuple(map(narrow._signature, frame))
        != tuple(map(narrow._signature, source_frame))
        or len(legacy) != 12
        or len(sds) != 72
        or len({b.name for row in source.values() for b in row.bolts}) != 40
    ):
        raise ValueError("PB07 source axes or duties changed")
    axes = lower._fixed_axis_solids(panels)
    geometry = {}
    # ponytail: producer constants are patched only for each detached family rebuild.
    for names, width, thickness in (
        (lower.TARGET_STATIONS, CENTER_WIDTH_MM, LOWER_SERVICE_T_MM),
        (lower.LOWER_OUTER_STATIONS, OUTER_WIDTH_MM, LOWER_SERVICE_T_MM),
        (
            (*upper_outer.TARGET_STATIONS, *bottom.TARGET_STATIONS),
            OUTER_WIDTH_MM,
            OTHER_T_MM,
        ),
        (upper_center.TARGET_STATIONS, CENTER_WIDTH_MM, OTHER_T_MM),
    ):
        with (
            patch.object(lower, "BLOCK_X_MM", width),
            patch.object(lower, "BLOCK_T_MM", thickness),
            patch.object(lower, "RAIL_X_OFFSETS_MM", RAIL_X_MM),
            patch.object(lower, "UPRIGHT_N_OFFSETS_MM", UPRIGHT_N_MM),
        ):
            geometry.update(
                {
                    name: lower._build_station(
                        SPECS[name],
                        parts,
                        finished,
                        axes,
                        rail_n_offset_mm=(
                            UPPER_OUTER_RAIL_N_MM
                            if name in upper_outer.TARGET_STATIONS
                            else UPPER_CENTER_RAIL_N_MM
                            if name in upper_center.TARGET_STATIONS
                            else LOWER_RAIL_N_MM
                        ),
                        block_length_mm=LENGTH_MM,
                    )
                    for name in names
                }
            )
    # Keep the assembly and the screen on the identical, actually relieved solid.
    service_name = lower.TARGET_STATIONS[0]
    service_row = geometry[service_name]
    wire = protected.inventory()["solids"]["wires"]["wire_054_E6_E7"]
    pre_cut_wire_hit = protected._volume(service_row.block, wire)
    channel_applied = pre_cut_wire_hit > 1e-6
    channel_hits = {}
    cut_block = service_row.block
    if channel_applied:
        channel = _wire_channel()
        channel_hits = narrow._hits(
            channel,
            {
                **{f"bore/{name}": shape for name, shape in service_row.bores.items()},
                **{
                    f"stack/{bolt}/{role}": shape
                    for bolt, stack in service_row.stacks.items()
                    for role, shape in stack.items()
                },
            },
        )
        cut_block = service_row.block.cut(channel).clean()
    post_cut_wire_hit = protected._volume(cut_block, wire)
    service_contact = {
        "rail": lower._contact_area(
            cut_block,
            finished[service_row.rail_name],
            (0, -lower.pb01.T[0], -lower.pb01.T[1]),
        ),
        "upright": lower._contact_area(
            cut_block,
            finished[service_row.upright_name],
            (
                -1 if SPECS[service_name].rail_extension_direction == "right" else 1,
                0,
                0,
            ),
        ),
    }
    channel_report = {
        "wire": "wire_054_E6_E7",
        "radius_mm": WIRE_CHANNEL_RADIUS_MM,
        "pre_cut_wire_hit_mm3": round(pre_cut_wire_hit, 6),
        "post_cut_wire_hit_mm3": round(post_cut_wire_hit, 6),
        "channel_applied": channel_applied,
        "bore_or_stack_hits_mm3": channel_hits,
        "remaining_contact_area_mm2": service_contact,
        "removed_wood_mm3": round(service_row.block.Volume() - cut_block.Volume(), 6),
        "owner_approval_and_strength_check_required": channel_applied,
        "qualified_for_layout_selection": not channel_applied
        or SERVICE_CHANNEL_QUALIFIED,
    }
    geometry[service_name] = replace(
        service_row,
        block=cut_block,
        report={**service_row.report, "service_channel": channel_report},
    )
    envelope_alignment = {}
    for name, row in geometry.items():
        block_n = _n_bounds(row.block)
        rail_n = _n_bounds(parts[row.rail_name])
        envelope_alignment[name] = (
            abs(block_n[0] - rail_n[0]) < 1e-6 and abs(block_n[1] - rail_n[1]) < 1e-6
        )
    return geometry, finished, axes, frame, legacy, sds, envelope_alignment


def screen(module=None):
    """Evaluate one layout; any hit returns REVISE, never active geometry."""
    module = pb07.PB07Native() if module is None else module
    geometry, finished, axes, frame, legacy, sds, alignment = _build(module)
    service_name = lower.TARGET_STATIONS[0]
    channel_report = geometry[service_name].report["service_channel"]
    channel_hits = channel_report["bore_or_stack_hits_mm3"]
    service_contact = channel_report["remaining_contact_area_mm2"]
    installed = {
        name: replace(
            row,
            stacks={bolt.name: pb07._nominal_stack(row, bolt) for bolt in row.bolts},
        )
        for name, row in geometry.items()
    }
    fixed = {
        **{f"panel_axis/{name}": shape for name, shape in axes.items()},
        **{f"frame_axis/{row.name}": narrow._axis(row) for row in frame},
        **{
            f"legacy_angle/{part.name}": part.shape
            for part in module.parts()
            if part.name in legacy
        },
        **{f"legacy_sds/{row.name}": narrow._axis(row) for row in sds},
        **{
            f"panel/{name}": shape
            for name, shape in finished.items()
            if name.startswith(("main_", "kicker_"))
        },
    }
    rows = {}
    protected_candidates = {}
    protected_tool_candidates = {}
    for name, row in installed.items():
        protected_candidates[f"block/{name}"] = row.block
        protected_candidates.update(
            {f"bore/{bolt}": shape for bolt, shape in row.bores.items()}
        )
        other_stacks = {
            f"{bolt}/{role}": shape
            for bolt, stack in row.stacks.items()
            for role, shape in stack.items()
        }
        installed_hits = {}
        tool_hits = {}
        conditional_tool_hits = {}
        for bolt in row.bolts:
            other = {
                f"own/{key}": shape
                for key, shape in other_stacks.items()
                if not key.startswith(bolt.name + "/")
            }
            other.update(
                {
                    f"own_bore/{key}": shape
                    for key, shape in row.bores.items()
                    if key != bolt.name
                }
            )
            nonhost = {
                f"timber/{key}": shape
                for key, shape in finished.items()
                if key not in bolt.members and not key.startswith(("main_", "kicker_"))
            }
            for role, shape in row.stacks[bolt.name].items():
                protected_candidates[f"installed/{bolt.name}/{role}"] = shape
                if hit := narrow._hits(shape, {**fixed, **nonhost, **other}):
                    installed_hits[f"{bolt.name}/{role}"] = hit
            for end, shape in row.tools[bolt.name].items():
                if hit := narrow._hits(shape, {**fixed, **nonhost, **other}):
                    tool_hits[f"{bolt.name}/{end}"] = hit
            for end, shape in _conditional_tools(bolt).items():
                protected_tool_candidates[f"access_25p4/{bolt.name}/{end}"] = shape
                if hit := narrow._hits(shape, {**fixed, **nonhost, **other}):
                    conditional_tool_hits[f"{bolt.name}/{end}"] = hit
        rows[name] = {
            "block_dimensions_mm": row.report["block_dimensions_mm"],
            "rail_n_mm": row.report["rail_bore_n_offset_mm"],
            "rail_x_mm": RAIL_X_MM,
            "upright_n_mm": UPRIGHT_N_MM,
            "aligned_to_rearward_2x6_n_envelope": alignment[name],
            "local_contact_and_bores": row.report["contact_verified"]
            and row.report["complete_bores"],
            "local_collision_clear": row.report["collision_clear"],
            "local_access_clear": row.report["access_clear"],
            "local_block_fixed_hits_mm3": narrow._hits(row.block, fixed),
            "installed_stack_hits_mm3": installed_hits,
            "tool_to_installed_or_fixed_hits_mm3": tool_hits,
            "conditional_25p4_tool_hits_mm3": conditional_tool_hits,
            "stock_8in_upright": _bolt_grip(row),
            "generic_5in_rail": _rail_grip(row),
            "service_channel_clear_of_bores_and_stacks": (
                not channel_hits if name == service_name else None
            ),
        }
    envelopes = {name: short._envelope(row) for name, row in installed.items()}
    pair_hits = {}
    for first, second in combinations(installed, 2):
        if not short._envelopes_overlap(envelopes[first], envelopes[second]):
            continue
        result = cross.screen_cross_family(
            {first: installed[first]}, {second: installed[second]}
        )
        if hits := {
            key: value
            for key, value in result.items()
            if key.endswith("hits_mm3") and value
        }:
            pair_hits[f"{first}|{second}"] = hits
    blocking_pairs = {
        name: {
            key: value
            for key, value in hit.items()
            if key != "cross_family_tool_tool_hits_mm3"
        }
        for name, hit in pair_hits.items()
        if any(key != "cross_family_tool_tool_hits_mm3" for key in hit)
    }
    protected_inventory = protected.inventory()
    targeted = {
        "block/clip_horizontal_lower_left_2": protected_candidates[
            "block/clip_horizontal_lower_left_2"
        ],
        "access_25p4/pb03_lower_outer_right_upright_1/far": protected_tool_candidates[
            "access_25p4/pb03_lower_outer_right_upright_1/far"
        ],
    }
    target_solids = {
        "solids": {
            "lights": {"light_E7": protected_inventory["solids"]["lights"]["light_E7"]},
            "wires": {
                "wire_054_E6_E7": protected_inventory["solids"]["wires"][
                    "wire_054_E6_E7"
                ],
                "wire_126_K6_K7": protected_inventory["solids"]["wires"][
                    "wire_126_K6_K7"
                ],
            },
        }
    }
    targeted_hits = {
        name: hits
        for name, hits in protected.hits(targeted, target_solids).items()
        if hits
    }
    protected_hits = {
        name: hits
        for name, hits in protected.hits(
            protected_candidates, protected_inventory
        ).items()
        if hits
    }
    service_wire_hit_mm3 = (
        protected_hits.get(f"block/{service_name}", {})
        .get("wires", {})
        .get("wire_054_E6_E7", 0.0)
    )
    # ponytail: a blocked core layout needs no expensive protected-tool pass.
    protected_tool_hits = (
        {}
        if protected_hits
        else {
            name: hits
            for name, hits in protected.hits(
                protected_tool_candidates, protected_inventory
            ).items()
            if hits
        }
    )
    protected_tool_status = (
        "not_run_due_core_intersections" if protected_hits else "screened"
    )
    protected_family_hits = {
        family: {
            name: rows[family]
            for name, rows in protected_hits.items()
            if family in rows
        }
        for family in protected_inventory["counts"]
    }
    reserves = layout_reserves()
    passed = (
        all(value > 0 for value in reserves.values())
        and all(
            row["local_contact_and_bores"]
            and row["aligned_to_rearward_2x6_n_envelope"]
            and row["local_collision_clear"]
            and row["local_access_clear"]
            and not row["local_block_fixed_hits_mm3"]
            and not row["installed_stack_hits_mm3"]
            and not row["conditional_25p4_tool_hits_mm3"]
            and row["stock_8in_upright"]["nut_on_listed_thread"]
            and row["stock_8in_upright"]["two_thread_projection_margin_mm"] > 0
            and row["generic_5in_rail"]["generic_5in_two_thread_margin_mm"] >= 0
            for row in rows.values()
        )
        and not blocking_pairs
        and not targeted_hits
        and not protected_hits
        and not protected_tool_hits
        and not channel_hits
        and all(value > 0 for value in service_contact.values())
        and channel_report["qualified_for_layout_selection"]
    )
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "schema": "simple_pb09_owner_layout_screen/v1",
        "source_id": SOURCE_ID,
        "parent_source_id": pb07.SOURCE_ID,
        "layout_revision": LAYOUT_REVISION,
        "source_sha256": source_hash,
        "inventory": {
            "blocks": 10,
            "new_bolt_axes": 40,
            "panel_kicker_axes": len(axes),
            "original_frame_bolt_axes": len(frame),
            "legacy_sds_axes": len(sds),
            "legacy_duties": len(legacy),
        },
        "layout_reserves_mm": reserves,
        "stations": rows,
        "pair_hits_mm3": pair_hits,
        "blocking_pair_hits_mm3": blocking_pairs,
        "targeted_revision_hits_mm3": targeted_hits,
        "service_channel": {
            **channel_report,
            "actual_wire_hit_mm3": service_wire_hit_mm3,
        },
        "protected_hits_mm3": protected_hits,
        "protected_tool_hits_mm3": protected_tool_hits,
        "protected_tool_status": protected_tool_status,
        "protected_geometry_gates": {
            "inventory_counts": protected_inventory["counts"],
            "core_modeled_family_clear": {
                family: not hits for family, hits in protected_family_hits.items()
            },
            "all_66_panel_screw_axes_modeled": len(axes) == 66,
            "panel_screw_installed_bodies_and_heads_clear": None,
            "all_12_retained_frame_bolt_axes_modeled": len(frame) == 12,
            "retained_frame_bolt_installed_stacks_clear": None,
            "delivered_hold_bolt_length_clear": None,
            "actual_wiring_bends_clear": None,
        },
        "decision": (
            "CONDITIONAL_TOOL_LAYOUT_ONLY"
            if passed
            and any(row["tool_to_installed_or_fixed_hits_mm3"] for row in rows.values())
            else "LAYOUT_ONLY_CLEAR"
            if passed
            else "REVISE_LAYOUT"
        ),
        "limits": [
            "Signed 7D/4D checks are conditional until PB09 has its own load cases.",
            "Nominal 8-in upright shafts and generic rail stacks are not purchased hardware verification.",
            "40-mm generic access hits remain reported. The 25.4-mm envelope is a conditional unselected tool, not an actual socket or assembly proof.",
            "Tool/tool overlaps are diagnostic for a one-tool-at-a-time sequence; conditional tool/installed hits block.",
            "Finite T-nut, 50.8-mm trial hold-hole/protrusion, LED, wire, panel screw shaft, and frame bolt shaft solids screen core block/bore/stack geometry first; protected tool screening is skipped and marked unverified if core intersections block. Delivered hold-bolt length, wiring bends, and heads/stacks remain unverified.",
            "No native solve, joint resistance, drilling, or fabrication release.",
            "The lower-left center block has a provisional wire-following 5-mm-radius service channel; feeding, strength, and owner approval are open. Four lower-service blocks use 76.2-mm T thickness, which requires a fresh rail-bolt stock/grip check.",
        ],
        **_NO_RELEASE,
    }
