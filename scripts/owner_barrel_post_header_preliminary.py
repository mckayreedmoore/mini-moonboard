"""Conditional components of the current integrated post/header backing path.

CAD dimensions and isolated references only; no signed demand, complete-joint
resistance, screw withdrawal, barrel strength, or fabrication release.
"""

import json
import math
from pathlib import Path

from mini_moonboard.bolted_timber_checks import (
    dfl_axial_wood_bearing_reference_lbf,
    dfl_net_parallel_tension_reference_lbf,
)
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_installed_stack_audit import _cylinder
from scripts.owner_barrel_installed_stack_audit import build_report as stack_report
from scripts.owner_barrel_integrated_backing import report as backing_report
from scripts.owner_barrel_native_face_contacts import build_report as face_report

ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ROOT / "docs/bolted-candidate-material-basis.json"
SIDES = ("left", "right")
MM_PER_IN = 25.4
N_PER_LBF = 4.4482216152605
STEEL_E_MPA_SENSITIVITY = 205_000.0
ROOT_DIAMETER_MM_SENSITIVITY = 0.189 * MM_PER_IN


def _post(assembly, backing, stack_rows, face, side):
    name = f"base_post_center_{side}"
    station = f"clip_split_header_center_{side}"
    source = backing["posts"][name]
    post_bounds = assembly["wood"][name].BoundingBox()
    header_bounds = assembly["wood"]["base_header"].BoundingBox()
    crossings = face["bolt_face_crossings"]
    names = source["post_header_bolts"]
    if (
        source["post_header_station"] != station
        or face["first_part"] != "base_header"
        or face["second_part"] != name
        or len(names) != 2
        or len(crossings) != 2
        or set(names) != {point["name"] for point in crossings}
        or any(point["direction_xyz"] != [0.0, 0.0, -1.0] for point in crossings)
    ):
        raise ValueError(f"{station}: post/header source inventory changed")
    # The two X-directed blind barrel bores share one Z-normal post section.
    barrel_centers = [
        assembly["barrels"][bolt.removesuffix("_bolt")].Center() for bolt in names
    ]
    row_spacing = abs(barrel_centers[1].y - barrel_centers[0].y)
    barrel_od = stack_rows[names[0]]["barrel_body_od_mm"]
    if (
        abs(barrel_centers[1].z - barrel_centers[0].z) > 1e-4
        or row_spacing <= barrel_od
        or any(
            min(center.y - post_bounds.ymin, post_bounds.ymax - center.y)
            <= barrel_od / 2
            for center in barrel_centers
        )
    ):
        raise ValueError(f"{station}: isolated two-slot section is not applicable")

    rows = []
    for bolt_name in names:
        axial = stack_rows[bolt_name]
        barrel_name = axial["barrel_name"]
        stack = assembly["stacks"][bolt_name]
        washer_height, washer_od = _cylinder(stack["washer"], bolt_name + "/washer")[
            1:3
        ]
        head_height, head_od = _cylinder(stack["head"], bolt_name + "/head")[1:3]
        cross_depth, cross_od = _cylinder(
            assembly["drilling_paths"][barrel_name + "/barrel_cross_bore"],
            barrel_name + "/barrel_cross_bore",
        )[1:3]
        center = axial["barrel_body_center_xyz_mm"]
        shaft_start = axial["shaft_start_xyz_mm"]
        washer_edge_stock = (
            min(
                shaft_start[0] - header_bounds.xmin,
                header_bounds.xmax - shaft_start[0],
                shaft_start[1] - header_bounds.ymin,
                header_bounds.ymax - shaft_start[1],
            )
            - washer_od / 2
        )
        if (
            axial["station"] != station
            or assembly["bolts"][bolt_name].members != ("base_header", name)
            or axial["shaft_axis_xyz"] != [0.0, 0.0, -1.0]
            or axial["nominal_axial_flags"] != ["AXIS_REACHED_WITHIN_MODELED_BORE"]
            or axial["thread_engagement"] != "UNKNOWN"
            or abs(shaft_start[2] - washer_height - header_bounds.zmax) > 1e-4
            or washer_edge_stock <= 0
            or abs(cross_od - axial["barrel_body_od_mm"]) > 1e-4
            or abs(center[2] - barrel_centers[0].z) > 1e-4
        ):
            raise ValueError(f"{bolt_name}: nominal stack or washer seat changed")
        reach = axial["assumed_thread_axis_reach_mm"]
        washer_n = (
            dfl_axial_wood_bearing_reference_lbf(
                washer_od / MM_PER_IN,
                axial["machine_bore_od_mm"] / MM_PER_IN,
                axial["shaft_od_mm"] / MM_PER_IN,
            )
            * N_PER_LBF
        )
        root_k = (
            STEEL_E_MPA_SENSITIVITY
            * math.pi
            * ROOT_DIAMETER_MM_SENSITIVITY**2
            / 4
            / reach
        )
        nominal_k = (
            STEEL_E_MPA_SENSITIVITY * math.pi * axial["shaft_od_mm"] ** 2 / 4 / reach
        )
        rows.append(
            {
                "name": bolt_name,
                "barrel_name": barrel_name,
                "barrel_center_xyz_mm": center,
                "nominal_bolt_length_mm": axial["shaft_length_mm"],
                "shaft_diameter_mm": axial["shaft_od_mm"],
                "head_diameter_mm": round(head_od, 4),
                "head_height_mm": round(head_height, 4),
                "washer_outer_diameter_mm": round(washer_od, 4),
                "washer_thickness_mm": round(washer_height, 4),
                "washer_min_radial_header_edge_stock_mm": round(washer_edge_stock, 4),
                "machine_bore_diameter_mm": axial["machine_bore_od_mm"],
                "machine_bore_far_cap_from_shaft_start_mm": axial[
                    "machine_bore_far_cap_from_shaft_start_mm"
                ],
                "barrel_body_diameter_mm": axial["barrel_body_od_mm"],
                "barrel_body_length_mm": axial["barrel_body_length_mm"],
                "barrel_cross_bore_depth_mm": round(cross_depth, 4),
                "assumed_thread_axis_reach_mm": reach,
                "tip_past_barrel_far_wall_mm": axial["tip_past_barrel_far_wall_mm"],
                "tip_to_modeled_bore_cap_mm": axial["tip_to_bore_far_cap_clearance_mm"],
                "partial_thread_comparator_body_overlap_mm": axial[
                    "partial_thread_comparator_body_overlap_mm"
                ],
                "thread_engagement": "UNKNOWN",
                "ideal_full_contact_washer_fc_perp_n": round(washer_n, 3),
                "steel_only_ea_over_length_nominal_n_per_mm": round(nominal_k, 3),
                "steel_only_ea_over_length_root_n_per_mm": round(root_k, 3),
            }
        )

    screw_connections = {row.name: row for row in assembly["panel_connections"]}
    screws = []
    for source_row in source["kicker_screws"]:
        connection = screw_connections[source_row["name"]]
        start = connection.start.toTuple()
        tip_y = start[1] - source_row["purchased_length_mm"]
        remaining = tip_y - post_bounds.ymin
        z_edge = min(start[2] - post_bounds.zmin, post_bounds.zmax - start[2])
        if (
            remaining <= 0
            or z_edge <= 0
            or not source_row["full_purchased_shaft_in_post"]
        ):
            raise ValueError(f"{source_row['name']}: fixed post receiver changed")
        screws.append(
            {
                **source_row,
                "modeled_diameter_mm": connection.diameter,
                "axis_xyz_mm": [round(value, 4) for value in start],
                "axis_to_nearest_z_end_mm": round(z_edge, 4),
                "remaining_y_stock_beyond_tip_mm": round(remaining, 4),
            }
        )
    section_n = (
        dfl_net_parallel_tension_reference_lbf(
            post_bounds.xlen / MM_PER_IN,
            post_bounds.ylen / MM_PER_IN,
            (barrel_od / MM_PER_IN,) * 2,
        )
        * N_PER_LBF
    )
    return {
        "station": station,
        "members": ["base_header", name],
        "row_spacing_mm": round(row_spacing, 4),
        "bolt_rows": rows,
        "kicker_screws": screws,
        "unit_y_screw_force_sensitivity": source["unit_y_screw_force_sensitivity"],
        "face": {
            "gross_area_mm2": face["gross_contact_area_mm2"],
            "trial_cut_area_mm2": face["trial_cut_contact_area_mm2"],
            "gross_centroid_xyz_mm": face["gross_contact_centroid_xyz_mm"],
            "normal_outward_from_header_xyz": face["normal_outward_from_first_xyz"],
            "bolt_crossings": crossings,
            "trial_cut_cell_area_basis": face["contact_cell_area_basis"],
            "contact_law_qualified": False,
        },
        "isolated_post_section": {
            "thickness_x_width_y_mm": [
                round(post_bounds.xlen, 4),
                round(post_bounds.ylen, 4),
            ],
            "grain_axis": "Z",
            "two_full_slot_parallel_tension_reference_n": round(section_n, 3),
            "basis": "2024 DF-L No. 2 Ft_parallel=575 psi; two disjoint full-X slots at the common barrel Z plane, each one barrel OD wide in Y; conservative isolated sensitivity, not the actual blind-bore/cross-cut net section",
            "actual_cut_net_section_resistance_n": None,
        },
        "post_header_joint_resistance_n": None,
        "screw_withdrawal_resistance_n": None,
        "barrel_resistance_n": None,
        "complete_backing_load_path_verified": False,
    }


def report(assembly=None):
    """Bind live viewer, backing, stack, contact face, and DF-L references."""
    assembly = build_integrated_viewer_assembly() if assembly is None else assembly
    material = json.loads(MATERIAL.read_text())
    values = material["reference_values"]
    backing = backing_report(assembly)
    stack = stack_report(assembly)
    faces = face_report(assembly)
    if (
        material["source"]["edition"] != "2024 NDS and 2024 NDS Supplement"
        or values["Ft_parallel"]["value"] != 575
        or values["Fc_perpendicular"]["value"] != 625
        or values["G"]["value"] != 0.5
        or material["fabrication_release"]
        or assembly["post_placement"] != "integrated"
        or any(assembly["release_flags"].values())
        or stack["row_count"] != 46
        or stack["source"]
        != "scripts.export_owner_barrel_scene.build_integrated_viewer_assembly()"
        or stack["structural_released"]
        or faces["station_count"] != 24
        or faces["bolt_interface_count"] != 46
        or faces["structural_released"]
        or backing["fixed_center_kicker_screw_count"] != 4
        or backing["post_header_barrel_pair_count"] != 4
        or backing["post_header_joint_resistance_verified"]
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
    ):
        raise ValueError(
            "Current integrated source/material or release boundary changed"
        )
    stack_rows = {row["bolt_name"]: row for row in stack["rows"]}
    posts = {
        f"base_post_center_{side}": _post(
            assembly,
            backing,
            stack_rows,
            faces["stations"][f"clip_split_header_center_{side}"],
            side,
        )
        for side in SIDES
    }
    return {
        "schema": "owner_barrel_post_header_preliminary/v1",
        "geometry_source": stack["source"],
        "backing_source": "scripts.owner_barrel_integrated_backing.report()",
        "stack_source": stack["schema"],
        "face_source": faces["schema"],
        "material_source": "docs/bolted-candidate-material-basis.json",
        "edition": material["source"]["edition"],
        "inventory": {
            "barrel_pairs": len(assembly["bolts"]),
            "former_angle_stations": len(set(assembly["bolt_station"].values())),
            "fixed_panel_kicker_screws": len(assembly["panel_connections"]),
            "retained_frame_bolts": len(assembly["frame_connections"]),
            "post_header_bolts": backing["post_header_barrel_pair_count"],
            "fixed_center_kicker_screws": backing["fixed_center_kicker_screw_count"],
            "separate_backers": backing["separate_backer_count"],
        },
        "posts": posts,
        "steel_sensitivity": {
            "E_MPa": STEEL_E_MPA_SENSITIVITY,
            "typical_root_diameter_mm": round(ROOT_DIAMETER_MM_SENSITIVITY, 4),
            "basis": "illustrative steel-only EA/L to assumed barrel axis; bolt grade, actual root and joint stiffness unverified",
        },
        "limits": "Ideal washer Fc-perp assumes sound full contact on the modeled header top; washer OD/head are CAD envelopes. Trial face area is not a contact law. Full-X post slots ignore actual blind bores, intersecting machine bores, other cuts and splitting. No screw withdrawal, barrel resistance, delivered thread fit, signed demand, or complete backing path is established.",
        "signed_demand_n": None,
        "complete_joint_capacity_n": None,
        "native_solve": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
