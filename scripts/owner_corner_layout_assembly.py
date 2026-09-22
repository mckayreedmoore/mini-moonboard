"""Source-distinct, kerf-right 24-duty corner-block viewer assembly.

This is a detached layout composition, not a structural or drilling release.
Nominal stack solids are display envelopes, not approved purchased hardware.
"""

from dataclasses import replace
from functools import lru_cache

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import center_posts_outward_owner_layout as posts
from scripts import owner_layout_bottom_center_pair as bottom_center
from scripts import owner_layout_bottom_center_revision as bottom_center_revision
from scripts import owner_layout_center_header_four as center_header
from scripts import owner_layout_outer_header_pair as outer_header
from scripts import simple_owner_duty_ledger as ledger
from scripts import simple_owner_outer_base_pair as outer_base
from scripts import simple_pb07_outer_rail_native as pb07
from scripts import simple_pb09_owner_layout_screen as pb09
from scripts import simple_top_same_side_four as top

FAMILY_STATIONS = {
    "pb09_ten": pb09.STATIONS,
    "top_four": top.TARGET_STATIONS,
    "bottom_center_two": bottom_center.STATIONS,
    "center_header_four": center_header.STATIONS,
    "outer_header_two": outer_header.STATIONS,
    "outer_base_two": outer_base.TARGETS,
}
_RELEASE_FLAGS = {
    "geometry_accepted": False,
    "purchased_hardware_approved": False,
    "backer_attachment_qualified": False,
    "native_solve": False,
    "force_transfer": False,
    "drilling_released": False,
    "fabrication_released": False,
    "structural_released": False,
}


def _overlap(first, second):
    """Exact positive-volume clash, with a cheap bounding-box rejection."""
    a, b = first.BoundingBox(), second.BoundingBox()
    if (
        min(a.xmax, b.xmax) - max(a.xmin, b.xmin) <= 0
        or min(a.ymax, b.ymax) - max(a.ymin, b.ymin) <= 0
        or min(a.zmax, b.zmax) - max(a.zmin, b.zmin) <= 0
    ):
        return 0.0
    volume = first.intersect(second).Volume()
    return round(volume, 6) if volume > 1.0 else 0.0


def _cross_family_hits(blocks, stacks, bolt_station, station_family):
    """Screen distinct source families; same-family checks belong to producers."""
    hits = {}
    stations = tuple(blocks)
    for index, first in enumerate(stations):
        for second in stations[index + 1 :]:
            if station_family[first] == station_family[second]:
                continue
            volume = _overlap(blocks[first], blocks[second])
            if volume:
                hits[f"block/{first}|block/{second}"] = volume
    for station, block in blocks.items():
        for bolt_name, roles in stacks.items():
            if station_family[station] == station_family[bolt_station[bolt_name]]:
                continue
            for role, solid in roles.items():
                volume = _overlap(block, solid)
                if volume:
                    hits[f"block/{station}|bolt/{bolt_name}/{role}"] = volume
    return hits


@lru_cache(maxsize=1)
def build_assembly():
    """Return all 24 proposed solids plus explicit unchanged-source/gate ledgers."""
    source = variant(KERF_RIGHT)
    source_connections = source.connections()
    panel_connections = source.panel_connections()
    frame_connections = tuple(row for row in source_connections if row.kind == "bolt")
    expected = {name for names in FAMILY_STATIONS.values() for name in names}
    duties = ledger.selected_duties()
    if len(expected) != 24 or set(duties) != expected:
        raise ValueError(
            "The six source families no longer partition 24 selected duties"
        )
    removed_legacy_sds = tuple(
        row
        for row in source_connections
        if row.name in {name for duty in duties.values() for name in duty["sds_axes"]}
    )
    if (
        len(panel_connections) != 66
        or len(frame_connections) != 12
        or len(removed_legacy_sds) != 144
        or len({row.name for row in source_connections}) != len(source_connections)
    ):
        raise ValueError("Kerf-right fixed connection inventory changed")

    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    placement = posts.build_layout()
    for side, sign in (("left", -1), ("right", 1)):
        name = f"base_post_center_{side}"
        wood[name] = wood[name].translate(
            cq.Vector(placement["post_shift_x_mm"][side], 0, 0)
        )
        x0, x1 = placement["backer_bounds_x_mm"][side]
        wood[f"inner_kicker_backer_{side}"] = cq.Solid.makeBox(
            x1 - x0,
            posts.BACKER_FRONT_Y_MM - posts.BACKER_REAR_Y_MM,
            posts.BACKER_TOP_Z_MM,
            cq.Vector(x0, posts.BACKER_REAR_Y_MM, 0),
        )
        if (
            abs(
                (wood[name].BoundingBox().xmin + wood[name].BoundingBox().xmax) / 2
                - sign * 180
            )
            > 1e-6
        ):
            raise ValueError(
                f"Owner-approved X±180 center post placement changed: {name}"
            )

    blocks, bolts, stacks, bores, bolt_station, station_family = {}, {}, {}, {}, {}, {}

    def add(station, family, block, rows, row_stacks, row_bores):
        if station in blocks:
            raise ValueError(f"Duplicate station: {station}")
        blocks[station], station_family[station] = block, family
        for bolt in rows:
            if (
                bolt.name in bolts
                or bolt.name not in row_stacks
                or bolt.name not in row_bores
            ):
                raise ValueError(f"Duplicate or incomplete bolt: {bolt.name}")
            bolts[bolt.name] = bolt
            stacks[bolt.name] = row_stacks[bolt.name]
            bores[bolt.name] = row_bores[bolt.name]
            bolt_station[bolt.name] = station

    pb09_rows, _, _, _, _, _, pb09_alignment = pb09._build(pb07.PB07Native())
    service_station = pb09.lower.TARGET_STATIONS[0]
    channel_report = pb09_rows[service_station].report["service_channel"]
    channel_removed = channel_report["removed_wood_mm3"]
    if channel_report["channel_applied"]:
        if channel_report["pre_cut_wire_hit_mm3"] <= 0 or channel_removed <= 1:
            raise ValueError("PB09 E6-E7 relief did not remove conflicting wood")
    elif abs(channel_removed) > 1 or channel_report["pre_cut_wire_hit_mm3"] > 0:
        raise ValueError("PB09 E6-E7 relief evidence is inconsistent")
    if channel_report["post_cut_wire_hit_mm3"] > 1:
        raise ValueError("PB09 shared block still intersects the E6-E7 wire")
    channel_hits = channel_report["bore_or_stack_hits_mm3"]
    for station, row in pb09_rows.items():
        add(
            station,
            "pb09_ten",
            row.block,
            row.bolts,
            {bolt.name: pb07._nominal_stack(row, bolt) for bolt in row.bolts},
            row.bores,
        )

    for station in top.TARGET_STATIONS:
        row = top._station(station, wood)
        add(
            station, "top_four", row["block"], row["bolts"], row["stacks"], row["bores"]
        )

    bottom_complete = {}
    for station in bottom_center.STATIONS:
        row = bottom_center._station(
            station,
            wood,
            block_x_mm=bottom_center_revision.BLOCK_X_MM,
            rail_x_mm=bottom_center_revision.RAIL_X_MM,
        )
        add(
            station,
            "bottom_center_two",
            row["block"],
            row["bolts"],
            row["stacks"],
            row["bores"],
        )
        bottom_complete[station] = row["complete"]

    center_coverage = {}
    for station in center_header.STATIONS:
        side = "left" if station.endswith("left") else "right"
        family = "post" if "header_center" in station else "principal"
        row = center_header._candidate(side, family, wood)
        add(
            station,
            "center_header_four",
            row["block"],
            row["bolts"],
            row["stacks"],
            row["bores"],
        )
        center_coverage[station] = row["coverage"]

    for station in outer_header.STATIONS:
        side = station.rsplit("_", 1)[1]
        block, rows, _, _ = outer_header._candidate(side, wood)
        add(
            station,
            "outer_header_two",
            block,
            (entry[0] for entry in rows.values()),
            {name: entry[1] for name, entry in rows.items()},
            {name: entry[2] for name, entry in rows.items()},
        )

    for station in outer_base.TARGETS:
        block, rows, _, _, _ = outer_base._pair(station, wood)
        canonical = f"owner_outer_base_{station.rsplit('_', 1)[1]}_block"
        corrected = [
            replace(
                entry[0],
                members=tuple(
                    canonical if member == "trial_cleat" else member
                    for member in entry[0].members
                ),
            )
            for entry in rows.values()
        ]
        add(
            station,
            "outer_base_two",
            block,
            corrected,
            {name: entry[1] for name, entry in rows.items()},
            {name: entry[2] for name, entry in rows.items()},
        )

    if set(blocks) != expected or len(bolts) != 92 or set(stacks) != set(bolts):
        raise ValueError("Incomplete source-distinct 24-duty candidate assembly")
    cross_hits = _cross_family_hits(blocks, stacks, bolt_station, station_family)
    diagnostics = {
        "status": "REVISE",
        "local_dispositions": {
            "pb09_ten": "REVISE_LAYOUT",
            "top_four": "ADVANCE_GEOMETRY_ONLY",
            "bottom_center_two": "REVISE",
            "center_header_four": "LAYOUT_ONLY_CLEAR",
            "outer_header_two": "GEOMETRY_TRIAL_ONLY",
            "outer_base_two": "ADVANCE_GEOMETRY_ONLY",
        },
        "local_dispositions_basis": "Producer notes/screens at composition time; not re-run or transferred as integrated approval",
        "station_family": station_family,
        "bolt_station": bolt_station,
        "cross_family_hits_mm3": cross_hits,
        "pb09_envelope_alignment": pb09_alignment,
        "pb09_service_channel_removed_mm3": channel_removed,
        "pb09_service_wire_pre_cut_hit_mm3": channel_report["pre_cut_wire_hit_mm3"],
        "pb09_service_wire_post_cut_hit_mm3": channel_report["post_cut_wire_hit_mm3"],
        "pb09_service_channel_applied": channel_report["channel_applied"],
        "pb09_service_channel_bore_stack_hits_mm3": channel_hits,
        "pb09_service_channel_basis": "Measured wire overlap governs shared PB09 _build() relief",
        "bottom_center_complete_bores": bottom_complete,
        "bottom_center_revision_source_id": bottom_center_revision.SOURCE_ID,
        "bottom_center_open_gates": (
            "Producer revision's full-host bore and finite block-protected screens are layout-only",
            "Generic tool/installed-stack host and protected-volume hits require review",
            "Only 2.05 mm nominal right G1 flange separation; tolerances unverified",
            "Load-aware 26 mm far-rail bolt end distance unverified",
            "Finished-wood bore confirmation is producer-owned; this assembly uses uncut wood",
        ),
        "bottom_center_known_tool_stack_hits": (
            "right principal-1 far tool intersects provisional G1 hold path and G1 T-nut flange",
            "right principal-1 far nut intersects provisional G1 hold path",
            "right principal-2 far nut intersects provisional G1 hold path",
            "left principal-1 far tool intersects E1 T-nut flange",
        ),
        "bottom_center_known_hit_volume_mm3": None,
        "center_header_core_coverage": center_coverage,
        "known_local_revise_gates": (
            "PB09 protected light/wire and tool-clearance gates remain producer-owned",
            "bottom-center historical 139.7-mm X first-trial left bore was incomplete",
            "bottom-center revised 77-mm X tools/stacks and tolerances remain open",
            "outer-base local protected/neighbor screen remains producer-owned",
            "backer structural attachment and installed hardware dimensions unverified",
        ),
        "unverified_protected_geometry": (
            "delivered hold-bolt length",
            "wiring bends",
            "panel screw heads and access",
            "frame bolt heads/nuts and access",
            "candidate purchased bolt lengths and access",
        ),
        "wood_basis": "kerf-right uncut original members; only center posts shifted and two backers added",
        "outer_base_full_length_shaft_displayed": False,
        "outer_base_stack_basis": "Generic _pair() stack envelopes only; nominal full 8/6-in shaft protrusions are not in this assembly display",
        "cross_family_screen_complete": False,
        "cross_family_omitted_modes": (
            "bolt-stack versus bolt-stack across families",
            "bores versus other-family blocks and stacks",
            "tool envelopes across families",
            "installed purchased-hardware lengths, seats, and access",
        ),
        "source_family_counts": {
            family: len(names) for family, names in FAMILY_STATIONS.items()
        },
    }
    return {
        "blocks": blocks,
        "bolts": bolts,
        "stacks": stacks,
        "bores": bores,
        "wood": wood,
        "removed_legacy_stations": tuple(sorted(expected)),
        "removed_legacy_sds": removed_legacy_sds,
        "panel_connections": panel_connections,
        "frame_connections": frame_connections,
        "diagnostics": diagnostics,
        "release_flags": dict(_RELEASE_FLAGS),
    }
