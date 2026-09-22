"""Export a complete but unqualified owner-review barrel-nut frame scene."""

import json
from functools import lru_cache
from pathlib import Path

from scripts import owner_barrel_backer_layout as backer
from scripts import owner_barrel_center_layout as center
from scripts import owner_barrel_outer_top_layout as outer
from scripts import owner_barrel_rail_layout as rail
from scripts.owner_barrel_layout_assembly import build_assembly
from scripts.simple_owner_duty_ledger import legacy_visual_names, selected_duties

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "site/hybrid/compact-floor-flush-kerf-right/parts.json"
OUTPUT = ROOT / "site/owner-barrel-layout-scene.json"
MOVED_POSTS = ("base_post_center_left", "base_post_center_right")
BACKERS = ("inner_kicker_backer_left", "inner_kicker_backer_right")
OUTER_HEADER_STATIONS = frozenset(
    {"clip_timber_header_outer_left", "clip_timber_header_outer_right"}
)


def build_viewer_assembly():
    """Compose reviewed geometry-only revisions; preserve producer defaults."""
    assembly = build_assembly(
        producers={
            "rail10": rail.build_revised_layout,
            "center6": center.build_revised_layout,
            "outer_top8": outer.build_recessed_viewer_layout,
        },
    )
    assembly["backer_attachment"] = backer.build_layout(assembly)
    return assembly


def _mesh(shape):
    vertices, triangles = shape.tessellate(0.5)
    return {
        "vertices_mm": [list(vertex.toTuple()) for vertex in vertices],
        "triangles": [list(triangle) for triangle in triangles],
    }


def _solid(name, role, shape, station=None):
    bounds = shape.BoundingBox()
    return {
        "name": name,
        "role": role,
        "source_station": station,
        "bounds_xyz_mm": [
            bounds.xmin,
            bounds.xmax,
            bounds.ymin,
            bounds.ymax,
            bounds.zmin,
            bounds.zmax,
        ],
        "mesh": _mesh(shape),
    }


def _axis(name, bolt, station):
    direction = bolt.direction.normalized()
    return {
        "name": name,
        "source_station": station,
        "start_mm": list(bolt.start.toTuple()),
        "axis": list(direction.toTuple()),
        "length_mm": bolt.length,
        "diameter_mm": bolt.diameter,
        "diagnostic_only": True,
    }


def _cut_header_trial(assembly):
    """Cut a detached header copy with the four selected seats and machine bores."""
    from scripts import owner_barrel_outer_header_cut_integrity as integrity

    report = integrity.probe(assembly=assembly)
    measured = report["members"]["base_header"]
    paths = measured["intended_paths"]
    if (
        len(paths) != 8
        or sum(row["role"] == "counterbore" for row in paths) != 4
        or sum(row["role"] == "machine_bore" for row in paths) != 4
        or report["inventory"]["fixed_panel_screws"] != 66
        or report["inventory"]["retained_frame_bolts"] != 12
        or report["clearance_approved"]
        or any(report["release_flags"].values())
    ):
        raise ValueError("Outer-header cut trial changed")
    uncut = assembly["wood"]["base_header"]
    cut = uncut
    for row in paths:
        cut = cut.cut(assembly["drilling_paths"][row["path"]].intersect(uncut))
    if (
        not cut.isValid()
        or len(cut.Solids()) != 1
        or abs(cut.Volume() - measured["cut_volume_mm3"]) > 0.1
        or abs(uncut.Volume() - measured["uncut_volume_mm3"]) > 0.1
        or measured["minimum_modeled_radial_edge_residual_mm"] <= 0
        or measured["counterbore_floor_residual_mm"] <= 0
    ):
        raise ValueError("Derived outer-header cut fails finite integrity screen")
    diagnostics = {
        "source_member": "base_header",
        "counterbore_count": 4,
        "machine_bore_count": 4,
        "uncut_volume_mm3": measured["uncut_volume_mm3"],
        "cut_volume_mm3": measured["cut_volume_mm3"],
        "removed_volume_mm3": measured["removed_volume_mm3"],
        "connected_solid_count": len(cut.Solids()),
        "cut_is_valid": cut.isValid(),
        "minimum_modeled_radial_edge_residual_mm": measured[
            "minimum_modeled_radial_edge_residual_mm"
        ],
        "counterbore_floor_residual_mm": measured["counterbore_floor_residual_mm"],
        "fixed_axis_proximity": measured["fixed_axis_proximity"],
        "net_section_capacity_verified": False,
        "disposition": report["disposition"],
        "clearance_approved": report["clearance_approved"],
    }
    return cut, diagnostics


def _rim_first_sequence():
    """Summarize the existing rim dependency probe without granting service approval."""
    from scripts import owner_barrel_outer_header_sequence_probe as sequence

    report = sequence.probe()
    if (
        report["fixed_axis_inventory"] != {"panel_kicker_screws": 66, "frame_bolts": 12}
        or report["fixed_axis_coordinates_changed"]
        or not report["temporary_fixed_fastener_removal_required"]
        or any(
            report[key]
            for key in (
                "drilling_released",
                "fabrication_released",
                "structural_released",
            )
        )
        or any(
            len(row["release_before_rim_withdrawal"]["fixed_panel_screws"]) != 8
            or len(row["release_before_rim_withdrawal"]["fixed_frame_bolts"]) != 2
            or len(row["release_before_rim_withdrawal"]["candidate_barrel_stations"])
            != 5
            or row["operational_result"] != "conditional_unverified"
            or not row["nominal_wood_withdrawal"]["sampled_wood_clear"]
            for row in report["sides"].values()
        )
    ):
        raise ValueError("Rim-first dependency inventory changed")
    return {
        "temporary_fixed_fastener_removal_required": True,
        "per_rim_release": {
            "panel_screws": 8,
            "frame_bolts": 2,
            "trial_rim_joint_bolts": 10,
        },
        "removal_order": (
            "Unload and independently support board and panels; temporarily remove each rim's "
            "eight panel screws, two leg/rim bolts, and ten trial rim-joint bolts; withdraw "
            "the rim; then operate the recessed header/post bolts."
        ),
        "installation_order": (
            "With each rim absent and the board supported, operate the header/post bolts; "
            "then fit the rim and reconnect its trial joints, leg/rim bolts, and panel screws "
            "on the unchanged axes."
        ),
        "sampled_wood_withdrawal_clear": True,
        "continuous_sweep_verified": False,
        "retained_hardware_clearance_verified": False,
        "operational_result": "conditional_unverified",
    }


@lru_cache(maxsize=1)
def build_scene():
    """Preserve every source duty and release flag in one detached viewer export."""
    assembly = build_viewer_assembly()
    backer_attachment = assembly["backer_attachment"]
    backer_stations = backer_attachment["stations"]
    duties = selected_duties()
    baseline = json.loads(BASELINE.read_text())
    baseline_parts = baseline["parts"]
    baseline_names = {part["name"] for part in baseline_parts}
    if (
        set(assembly["station_dispositions"]) != set(duties)
        or set(assembly["station_modes"]) != set(duties)
        or set(assembly["removed_legacy_stations"]) != set(duties)
        or len(assembly["removed_legacy_sds"]) != 144
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
        or not set(MOVED_POSTS).issubset(baseline_names)
        or not (set(MOVED_POSTS) | set(BACKERS)).issubset(assembly["wood"])
        or assembly["post_placement"] != "outward"
        or set(assembly["barrel_station"]) != set(assembly["barrels"])
        or set(assembly["bolt_station"]) != set(assembly["bolts"])
        or set(assembly["barrel_station"].values()) != set(duties)
        or any(
            not {"head", "washer"} <= set(stack)
            for stack in assembly["stacks"].values()
        )
        or any(assembly["release_flags"].values())
        or set(backer_stations) != {"backer_attachment_left", "backer_attachment_right"}
        or any(backer_attachment["release_flags"].values())
        or sum(len(row["bolts"]) for row in backer_stations.values()) != 4
        or sum(len(row["barrels"]) for row in backer_stations.values()) != 4
    ):
        raise ValueError(
            "Owner barrel assembly is incomplete or release boundary changed"
        )
    hidden = sorted(
        set(legacy_visual_names(duties, baseline_parts))
        | set(MOVED_POSTS)
        | {"base_header"}
    )
    if len(hidden) != 171:
        raise ValueError("Owner barrel legacy visual inventory changed")
    cut_header, cut_diagnostics = _cut_header_trial(assembly)
    rim_sequence = _rim_first_sequence()
    solids = [
        _solid(name, "moved_center_post", assembly["wood"][name])
        for name in MOVED_POSTS
    ]
    solids.extend(
        _solid(name, "kicker_screw_backer", assembly["wood"][name]) for name in BACKERS
    )
    solids.append(
        _solid("base_header/derived_outer_header_cut", "derived_cut_header", cut_header)
    )
    barrels = [
        _solid(name, "barrel_nut_envelope", shape, assembly["barrel_station"][name])
        for name, shape in assembly["barrels"].items()
    ]
    bolts = [
        _axis(name, bolt, assembly["bolt_station"][name])
        for name, bolt in assembly["bolts"].items()
    ]
    rail_stacks = [
        _solid(f"{name}/{role}", f"rail_{role}", shape, assembly["bolt_station"][name])
        for name, stack in assembly["stacks"].items()
        if assembly["diagnostics"]["station_family"][assembly["bolt_station"][name]]
        == "rail10"
        for role, shape in stack.items()
        if role in ("washer", "head")
    ]
    other_stacks = [
        _solid(f"{name}/{role}", f"joint_{role}", shape, assembly["bolt_station"][name])
        for name, stack in assembly["stacks"].items()
        if assembly["diagnostics"]["station_family"][assembly["bolt_station"][name]]
        != "rail10"
        and assembly["bolt_station"][name] not in OUTER_HEADER_STATIONS
        for role, shape in stack.items()
        if role in ("washer", "head")
    ]
    backer_barrels = [
        _solid(name, "backer_barrel", shape, station)
        for station, row in backer_stations.items()
        for name, shape in row["barrels"].items()
    ]
    backer_bolts = [
        _axis(name, bolt, station)
        for station, row in backer_stations.items()
        for name, bolt in row["bolts"].items()
    ]
    backer_stacks = [
        _solid(f"{name}/{role}", f"backer_{role}", shape, station)
        for station, row in backer_stations.items()
        for name, stack in row["stacks"].items()
        for role, shape in stack.items()
        if role in ("washer", "head")
    ]
    recessed = [
        _solid(
            f"{name}/{role}", f"recess_{role}", shape, assembly["bolt_station"][name]
        )
        for name, stack in assembly["stacks"].items()
        for role, shape in stack.items()
        if role in ("washer", "head")
        and assembly["bolt_station"][name] in OUTER_HEADER_STATIONS
    ]
    recessed.extend(
        _solid(
            name,
            "recess_counterbore",
            shape,
            assembly["bolt_station"][name.split("/")[0] + "_bolt"],
        )
        for name, shape in assembly["drilling_paths"].items()
        if name.endswith("/counterbore")
    )
    if (
        not barrels
        or not bolts
        or len(recessed) != 12
        or len(rail_stacks) != 40
        or len(other_stacks) != 48
        or len(backer_barrels) != 4
        or len(backer_bolts) != 4
        or len(backer_stacks) != 8
        or {row["role"] for row in recessed}
        != {"recess_head", "recess_washer", "recess_counterbore"}
        or not all(
            row["mesh"]["triangles"]
            for row in solids
            + barrels
            + recessed
            + rail_stacks
            + other_stacks
            + backer_barrels
            + backer_stacks
        )
    ):
        raise ValueError("Barrel viewer has empty geometry")
    clash_stations = set()
    for pair in assembly["diagnostics"]["cross_family_physical_hits_mm3"]:
        for part in pair.split("|"):
            kind, name, *_ = part.split("/")
            if kind == "barrel":
                clash_stations.add(assembly["barrel_station"][name])
            elif kind == "bolt":
                clash_stations.add(assembly["bolt_station"][name])
    if not clash_stations <= set(duties):
        raise ValueError("Cross-family clash references an unknown duty")
    return {
        "schema": "owner_barrel_layout_scene/v1",
        "status": "complete_layout_concept_not_qualified",
        "baseline": "compact-floor-flush-kerf-right",
        "hidden_baseline_visual_names": hidden,
        "station_modes": assembly["station_modes"],
        "station_dispositions": assembly["station_dispositions"],
        "cross_family_physical_clash_stations": sorted(clash_stations),
        "solids": solids,
        "barrel_nut_envelopes": barrels,
        "diagnostic_bolt_axes": bolts,
        "rail_head_washer_envelopes": rail_stacks,
        "other_head_washer_envelopes": other_stacks,
        "backer_barrel_nut_envelopes": backer_barrels,
        "backer_diagnostic_bolt_axes": backer_bolts,
        "backer_head_washer_envelopes": backer_stacks,
        "backer_attachment": {
            "source_id": backer_attachment["source_id"],
            "station_dispositions": {
                name: row["disposition"] for name, row in backer_stations.items()
            },
            "finite_clearance_screen_passed": backer_attachment["collision_screen"][
                "finite_clearance_screen_passed"
            ],
            "thread_engagement_verified": backer_attachment[
                "thread_engagement_verified"
            ],
            "capacity_verified": backer_attachment["capacity_verified"],
            "release_flags": backer_attachment["release_flags"],
        },
        "conditional_outer_header_recess_envelopes": recessed,
        "outer_header_cut_diagnostics": cut_diagnostics,
        "rim_first_sequence": rim_sequence,
        "outer_header_recess_trial": {
            "forward_row_y_mm": outer.VIEWER_HEADER_FORWARD_Y_MM,
            "counterbore_depth_mm": outer.VIEWER_HEADER_RECESS_MM,
            "washer_od_mm": outer.VIEWER_HEADER_WASHER_OD_MM,
            "head_od_mm": outer.VIEWER_HEADER_HEAD_OD_MM,
            "head_height_mm": outer.VIEWER_HEADER_HEAD_HEIGHT_MM,
            "nominal_head_below_header_top_mm": outer.VIEWER_HEADER_HEAD_COVER_MM,
            "side_rim_removal_required_for_driver": True,
            "actual_rim_removal_verified": False,
            "delivered_hardware_verified": False,
            "structural_capacity_verified": False,
        },
        "hardware_basis": assembly["hardware_basis"],
        "assembly_diagnostics": assembly["diagnostics"],
        "inventory": {
            "replaced_angle_duties": len(duties),
            "removed_structural_sds": len(assembly["removed_legacy_sds"]),
            "direct_joint_duties": sum(
                mode == "direct" for mode in assembly["station_modes"].values()
            ),
            "moved_center_posts": len(MOVED_POSTS),
            "kicker_screw_backers": len(BACKERS),
            "derived_cut_headers": 1,
            "barrel_nut_envelopes": len(barrels),
            "new_diagnostic_bolt_axes": len(bolts),
            "rail_head_washer_envelopes": len(rail_stacks),
            "other_head_washer_envelopes": len(other_stacks),
            "backer_attachment_duties": len(backer_stations),
            "backer_barrel_nut_envelopes": len(backer_barrels),
            "backer_diagnostic_bolt_axes": len(backer_bolts),
            "backer_head_washer_envelopes": len(backer_stacks),
            "conditional_outer_header_recess_envelopes": len(recessed),
            "fixed_panel_kicker_screw_axes": len(assembly["panel_connections"]),
            "retained_frame_bolt_axes": len(assembly["frame_connections"]),
        },
        "limits": (
            "A barrel-only comparison layout, including red REVISE stations, not a cut, drill, "
            "purchase, or structural release. Retail barrel identity is provisional; "
            "outer-header rim-first removal, delivered recessed hardware, "
            "counterbore wood capacity, thread-axis location, engagement, strength, access, service conflicts, "
            "backer attachment strength, tolerances and whole-frame load path remain open."
        ),
        "layout_clearance_approved": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build_scene(), separators=(",", ":")) + "\n")
