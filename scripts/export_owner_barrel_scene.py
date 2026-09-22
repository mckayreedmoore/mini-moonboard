"""Export a complete but unqualified owner-review barrel-nut frame scene."""

import json
from functools import lru_cache
from pathlib import Path

from scripts import owner_barrel_backer_layout as backer
from scripts import owner_barrel_center_layout as center
from scripts import owner_barrel_integrated_backing as backing
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


def build_integrated_viewer_assembly():
    """Compose seam-side posts and the single-barrel center proposal."""
    from scripts import owner_barrel_center_single_layout as integrated

    assembly = build_assembly(
        producers={
            "rail10": rail.build_integrated_layout,
            "center6": integrated.build_six_layout,
            "outer_top8": outer.build_integrated_recessed_layout,
        },
        post_placement="integrated",
    )
    if any(name.startswith("inner_kicker_backer_") for name in assembly["wood"]):
        raise ValueError("Integrated scene unexpectedly retains a separate backer")
    if (
        assembly["diagnostics"]["producer_diagnostics"]["center6"]["revised_center"][
            "candidate_service_diameter_mm"
        ]
        != 25.4
    ):
        raise ValueError("Integrated center service passage option changed")
    assembly["service_passage_option"] = "F1_G1_same_axis_25.4_mm_unqualified"
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


def _axis(name, bolt, station, nominal_axial=None):
    direction = bolt.direction.normalized()
    return {
        "name": name,
        "source_station": station,
        "start_mm": list(bolt.start.toTuple()),
        "axis": list(direction.toTuple()),
        "length_mm": bolt.length,
        "diameter_mm": bolt.diameter,
        "diagnostic_only": True,
        "nominal_axial": nominal_axial,
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


def _integrated_service_geometry(assembly):
    """Summarize current sampled access without upgrading it to service approval."""
    from scripts import owner_barrel_rim_outer_top_service_probe as outer_service
    from scripts import owner_barrel_rim_withdrawal_hardware_probe as rim_service

    outer = outer_service.probe(assembly=assembly)
    rim = rim_service.probe(assembly=assembly)
    if (
        not outer["viewer_source"].endswith("build_integrated_viewer_assembly")
        or not rim["source_assembly"].endswith("build_integrated_viewer_assembly")
        or outer["station_count"] != 4
        or set(rim["sides"]) != {"left", "right"}
        or any(
            rim[key]
            for key in (
                "drilling_released",
                "fabrication_released",
                "structural_released",
            )
        )
    ):
        raise ValueError("Integrated service-screen inventory changed")
    return {
        "source_pair_count": len(assembly["bolts"]),
        "outer_top_station_count": outer["station_count"],
        "outer_top_nominal_straight_paths_clear": all(
            row["rim_on_nominal_service_clear"] for row in outer["stations"].values()
        ),
        "rim_sample_count_per_side": len(rim["sides"]["left"]["withdrawal"]["samples"]),
        "both_rims_sampled_clear_with_retained_modeled_hardware": all(
            row["withdrawal"]["sampled_clear"] for row in rim["sides"].values()
        ),
        "both_rims_continuous_swept_aabb_clear_of_retained_hardware": all(
            row["withdrawal"]["continuous_swept_aabb"][
                "retained_hardware_and_protected_clear"
            ]
            for row in rim["sides"].values()
        ),
        "both_rims_continuous_swept_aabb_clear_of_other_wood": all(
            row["withdrawal"]["continuous_swept_aabb"]["other_wood_clear"]
            for row in rim["sides"].values()
        ),
        "all_retained_trial_stacks_include_heads_and_washers": all(
            not row["viewer_supplemental_heads_washers_absent_for"]
            for row in rim["sides"].values()
        ),
        "continuous_withdrawal_verified": False,
        "delivered_hardware_or_tool_verified": False,
        "barrel_insertion_alignment_extraction_verified": False,
        "safe_supported_panel_removal_verified": False,
        "operational_result": "sampled_nominal_only",
    }


@lru_cache(maxsize=1)
def build_scene():
    """Preserve every source duty and release flag in one detached viewer export."""
    assembly = build_integrated_viewer_assembly()
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
        or not set(MOVED_POSTS).issubset(assembly["wood"])
        or set(BACKERS) & set(assembly["wood"])
        or assembly["post_placement"] != "integrated"
        or assembly.get("service_passage_option")
        != "F1_G1_same_axis_25.4_mm_unqualified"
        or set(assembly["barrel_station"]) != set(assembly["barrels"])
        or set(assembly["bolt_station"]) != set(assembly["bolts"])
        or set(assembly["barrel_station"].values()) != set(duties)
        or any(
            not {"head", "washer"} <= set(stack)
            for stack in assembly["stacks"].values()
        )
        or any(assembly["release_flags"].values())
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
    service_geometry = _integrated_service_geometry(assembly)
    from scripts.owner_barrel_visual_wood import EXPECTED_TIMBERS, build_visual_wood

    visual = build_visual_wood(
        assembly=assembly,
        candidate_service=True,
        candidate_center_cuts=True,
        candidate_all_cuts=True,
    )
    if (
        set(visual["wood"]) != EXPECTED_TIMBERS
        or visual["report"]["excluded_legacy_sds_axes"] != 144
        or visual["report"]["replacement_timber_members"] != 16
        or visual["report"]["center_trial_cuts"] != 20
        or visual["report"]["outer_header_barrel_body_cuts"] != 4
        or visual["report"]["center_barrel_body_cuts"] != 6
        or visual["report"]["candidate_barrel_pairs_with_cut_wood"] != 46
        or visual["report"]["barrel_drilling_paths_without_cut_wood"]
        or visual["report"]["barrel_path_host_anomalies"]
        or visual["report"]["unrelated_remaining_pair_cut_intersections"]
        or visual["report"]["candidate_service_diameter_mm"] != 25.4
        or visual["report"]["release"]
    ):
        raise ValueError("Barrel visual timber replacement changed")
    hidden = sorted(set(hidden) | EXPECTED_TIMBERS)
    if len(hidden) != 184:
        raise ValueError("Owner barrel replaced timber inventory changed")
    # Surface the source-built axial audit in the viewer without changing a bore.
    from scripts.owner_barrel_installed_stack_audit import build_report

    reach = build_report(assembly)
    reach_by_bolt = {row["bolt_name"]: row for row in reach["rows"]}
    if (
        set(reach_by_bolt) != set(assembly["bolts"])
        or reach["counts"]["short_of_assumed_barrel_axis"] != 0
        or reach["counts"]["beyond_modeled_machine_bore"] != 0
        or reach["fit_qualified"]
    ):
        raise ValueError("Current viewer nominal axial audit changed")
    solids = [
        _solid(name, "integrated_center_post", visual["wood"][name])
        for name in MOVED_POSTS
    ]
    solids.extend(
        _solid(name, "barrel_replacement_timber", visual["wood"][name])
        for name in sorted(EXPECTED_TIMBERS - set(MOVED_POSTS) - {"base_header"})
    )
    visual_header = visual["wood"]["base_header"]
    if visual_header.Volume() > cut_header.Volume() + 0.1:
        raise ValueError("Visual header has lost its derived outer-header cuts")
    cut_diagnostics["displayed_visual_header_volume_mm3"] = visual_header.Volume()
    cut_diagnostics["displayed_visual_header_includes_retained_cuts"] = True
    solids.append(
        _solid(
            "base_header/derived_outer_header_cut", "derived_cut_header", visual_header
        )
    )
    barrels = [
        _solid(name, "barrel_nut_envelope", shape, assembly["barrel_station"][name])
        for name, shape in assembly["barrels"].items()
    ]
    bolts = [
        _axis(
            name,
            bolt,
            assembly["bolt_station"][name],
            {
                "tip_past_assumed_axis_mm": reach_by_bolt[name][
                    "tip_past_assumed_axis_mm"
                ],
                "maximum_body_overlap_if_fully_threaded_mm": reach_by_bolt[name][
                    "maximum_body_overlap_with_fully_threaded_shaft_mm"
                ],
                "partial_thread_comparator_body_overlap_mm": reach_by_bolt[name][
                    "partial_thread_comparator_body_overlap_mm"
                ],
                "partial_thread_comparator_end_length_mm": reach[
                    "partial_thread_comparator"
                ]["nominal_end_thread_length_mm"],
                "tip_to_modeled_bore_cap_mm": reach_by_bolt[name][
                    "tip_to_bore_far_cap_clearance_mm"
                ],
                "flags": reach_by_bolt[name]["nominal_axial_flags"],
                "thread_engagement": "UNKNOWN",
            },
        )
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
        or len(other_stacks) != 44
        or {row["role"] for row in recessed}
        != {"recess_head", "recess_washer", "recess_counterbore"}
        or not all(
            row["mesh"]["triangles"]
            for row in solids + barrels + recessed + rail_stacks + other_stacks
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
        "backer_barrel_nut_envelopes": [],
        "backer_diagnostic_bolt_axes": [],
        "backer_head_washer_envelopes": [],
        "backer_attachment": {"status": "not_applicable_integrated_center_posts"},
        "integrated_kicker_backing": backing.report(assembly),
        "integrated_center_joint_trial": assembly["diagnostics"][
            "producer_diagnostics"
        ]["center6"]["revised_center"],
        "conditional_outer_header_recess_envelopes": recessed,
        "outer_header_cut_diagnostics": cut_diagnostics,
        "visual_wood_replacement": visual["report"],
        "rim_first_sequence": rim_sequence,
        "integrated_service_geometry": service_geometry,
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
            "integrated_center_posts": len(MOVED_POSTS),
            "barrel_replacement_timbers": len(visual["wood"]),
            "kicker_screw_backers": 0,
            "derived_cut_headers": 1,
            "barrel_nut_envelopes": len(barrels),
            "new_diagnostic_bolt_axes": len(bolts),
            "rail_head_washer_envelopes": len(rail_stacks),
            "other_head_washer_envelopes": len(other_stacks),
            "backer_attachment_duties": 0,
            "backer_barrel_nut_envelopes": 0,
            "backer_diagnostic_bolt_axes": 0,
            "backer_head_washer_envelopes": 0,
            "conditional_outer_header_recess_envelopes": len(recessed),
            "fixed_panel_kicker_screw_axes": len(assembly["panel_connections"]),
            "retained_frame_bolt_axes": len(assembly["frame_connections"]),
        },
        "limits": (
            "A barrel-only comparison layout, including red REVISE stations, not a cut, drill, "
            "purchase, or structural release. Retail barrel identity is provisional; "
            "outer-header rim-first removal, delivered recessed hardware, "
            "counterbore wood capacity, thread-axis location, engagement, strength, access, service conflicts, "
            "candidate F1-G1 strand feeding, single-center-joint moment transfer, barrel insertion, "
            "tolerances and whole-frame load path remain open."
        ),
        "layout_clearance_approved": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build_scene(), separators=(",", ":")) + "\n")
