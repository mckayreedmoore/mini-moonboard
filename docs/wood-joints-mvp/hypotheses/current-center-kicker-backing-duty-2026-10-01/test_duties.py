"""In-memory tests for the current center-kicker source join."""

import unittest
from copy import deepcopy

from duties import DutiesInputError, build_duties

CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
POLICY = "Hillman 42605; existing purchased screw and pilot policy retained"
CENTERS = {
    "round_kicker_left_center_1": (
        "kicker_left",
        "base_post_center_left",
        "inner_kicker_backer_left",
        60.0,
        "base_post_center_left/facet009",
    ),
    "round_kicker_left_center_2": (
        "kicker_left",
        "base_post_center_left",
        "inner_kicker_backer_left",
        192.0,
        "base_post_center_left/facet010",
    ),
    "round_kicker_right_center_1": (
        "kicker_right",
        "base_post_center_right",
        "inner_kicker_backer_right",
        60.0,
        "base_post_center_right/facet009",
    ),
    "round_kicker_right_center_2": (
        "kicker_right",
        "base_post_center_right",
        "inner_kicker_backer_right",
        192.0,
        "base_post_center_right/facet010",
    ),
}
LOWER_MOVES = {
    "round_panel_lower_left_edge_1": (
        "base_rail_bottom_left",
        "base_rail_bottom_left/facet004",
    ),
    "round_panel_lower_left_edge_2": (
        "base_rail_bottom_left",
        "base_rail_bottom_left/facet006",
    ),
    "round_panel_lower_right_edge_1": (
        "base_rail_bottom_right",
        "base_rail_bottom_right/facet016",
    ),
    "round_panel_lower_right_edge_2": (
        "base_rail_bottom_right",
        "base_rail_bottom_right/facet014",
    ),
}
SIDE_DUTIES = {
    "left": {
        "post": "base_post_center_left",
        "cleat": "center_post_cleat_left",
        "post_axes": ("center_post_left_1", "center_post_left_2"),
        "header_axes": ("center_post_header_left_1", "center_post_header_left_2"),
        "duty": "clip_split_header_center_left",
    },
    "right": {
        "post": "base_post_center_right",
        "cleat": "center_post_cleat_right",
        "post_axes": ("center_post_right_1", "center_post_right_2"),
        "header_axes": ("center_post_header_right_1", "center_post_header_right_2"),
        "duty": "clip_split_header_center_right",
    },
}


def _bolt_specs():
    result = {}
    feature_ids = {}
    for side, spec in SIDE_DUTIES.items():
        for index, axis_id in enumerate(spec["post_axes"], start=1):
            result[axis_id] = {
                "pair": [spec["post"], spec["cleat"]],
                "role": "post_to_cleat",
                "side": side,
                "station": spec["duty"],
                "center": [
                    (-201.7023 if side == "left" else 200.3423),
                    -131.25,
                    145.0 + 50.0 * (index - 1),
                ],
                "direction": [1.0, 0.0, 0.0] if side == "left" else [-1.0, 0.0, 0.0],
                "length": 139.2174,
                "grip": 127.0,
            }
            post_facet = "facet006" if index == 1 else "facet007"
            cleat_facet = post_facet
            feature_ids[axis_id] = {
                spec["post"]: f"{spec['post']}/{post_facet}",
                spec["cleat"]: f"{spec['cleat']}/{cleat_facet}",
            }
        for index, axis_id in enumerate(spec["header_axes"], start=1):
            result[axis_id] = {
                "pair": ["base_header", spec["cleat"]],
                "role": "cleat_to_header",
                "side": side,
                "station": spec["duty"],
                "center": [
                    (-225.71 if side == "left" else 224.35),
                    -148.75 + 35.0 * (index - 1),
                    189.0423,
                ],
                "direction": [0.0, 0.0, -1.0],
                "length": 179.2174,
                "grip": 167.0,
            }
            if side == "left":
                header_facet = "facet013" if index == 1 else "facet011"
            else:
                header_facet = "facet010" if index == 1 else "facet007"
            cleat_facet = "facet009" if index == 1 else "facet010"
            feature_ids[axis_id] = {
                "base_header": f"base_header/{header_facet}",
                spec["cleat"]: f"{spec['cleat']}/{cleat_facet}",
            }
    return result, feature_ids


def _step_binding(member_id):
    return {
        "path": f"members/{member_id}.step",
        "sha256": f"sha-{member_id}",
        "file_sha256": f"sha-{member_id}",
        "size_bytes": 1000 + len(member_id),
        "face_count": 12,
        "solid_count": 1,
        "valid": True,
    }


def _surface_feature(feature_id):
    return {
        "feature_id": feature_id,
        "surface_kind": "CYLINDER",
        "classification": "descriptive_cylindrical_patch",
        "area_mm2": 100.0,
        "cylinder": {
            "radius_mm": 2.0701 if "round_kicker" in feature_id else 3.175,
            "axis_origin_global_xyz_mm": [0.0, 0.0, 0.0],
            "axis_unit_global_xyz": [0.0, 0.0, 1.0],
            "axis_station_interval_mm": [0.0, 1.0],
            "material_side_geometry": "bore_like",
        },
    }


def _axis_membership(member_id, feature_id):
    binding = _step_binding(member_id)
    return {
        "receiver_member_id": member_id,
        "match_status": "matched_bore_patch",
        "matched_feature_ids": [feature_id],
        "current_finished_step_binding": {
            "path": binding["path"],
            "file_sha256": binding["sha256"],
            "size_bytes": binding["size_bytes"],
        },
        "axis_in_stock_frame": {"axis_interval_from_datum_mm": [0.0, 1.0]},
        "cylinder_surface_candidates": [
            {
                "association_status": "eligible_bore_patch",
                "feature_id": feature_id,
                "surface_kind": "CYLINDER",
                "material_side_geometry": "bore_like",
            }
        ],
    }


def _center_panel_axis(axis_id, spec):
    panel, post, previous, z_mm, feature_id = spec
    origin = (
        [-161.71, -17.74375, z_mm]
        if panel == "kicker_left"
        else [160.35, -17.74375, z_mm]
    )
    translation = [-91.71, 0.0, 0.0] if panel == "kicker_left" else [90.35, 0.0, 0.0]
    binding = _step_binding(post)
    feature = {
        "feature_id": feature_id,
        "match_status": "matched_bore_patch",
        "finished_step_binding": {
            "path": binding["path"],
            "sha256": binding["sha256"],
            "size_bytes": binding["size_bytes"],
        },
        "bore_patch": {
            "surface_kind": "CYLINDER",
            "material_side_geometry": "bore_like",
            "finite_interval_status": "contained_in_source_finite_interval",
            "axial_overlap_length_mm": 45.24375,
            "patch_interval_projected_from_axis_datum_mm": [18.25625, 63.5],
            "cylinder_radius_mm": 2.0701,
        },
    }
    return {
        "axis_id": axis_id,
        "panel_member": panel,
        "receiver_member": post,
        "previous_receiver_member": previous,
        "current_location_status": "moved",
        "origin_global_xyz_mm": origin,
        "axis_global_xyz": [0.0, -1.0, 0.0],
        "translation_from_source_xyz_mm": translation,
        "features": [feature],
        "nominal_embedment_envelope": {
            "purchased_nominal_length_mm": 63.5,
            "source_historical_occupied_length_mm": 50.8,
            "matched_bore_patch_interval_from_axis_datum_mm": [18.25625, 63.5],
            "matched_bore_patch_overlap_length_mm": 45.24375,
            "status": "modeled receiver overlap only; not actual screw embedment or installed engagement",
        },
        "source_provenance": {"receiver_to_frame_path_complete": False},
        "owner_moved_axis_record": {
            "axis_id": axis_id,
            "previous_receiver_member": previous,
            "receiver_member": post,
            "new_start_global_xyz_mm": origin,
            "old_start_global_xyz_mm": [0.0, -17.74375, z_mm],
            "translation_global_xyz_mm": translation,
            "purchased_product_policy": POLICY,
        },
    }


def _generic_panel_axis(axis_id, status):
    return {
        "axis_id": axis_id,
        "panel_member": "main_lower_left",
        "receiver_member": "base_header",
        "previous_receiver_member": "base_header",
        "current_location_status": status,
        "origin_global_xyz_mm": [0.0, 0.0, 0.0],
        "axis_global_xyz": [0.0, -1.0, 0.0],
        "translation_from_source_xyz_mm": [0.0, 0.0, 0.0],
        "features": [],
        "nominal_embedment_envelope": {},
        "source_provenance": {"receiver_to_frame_path_complete": False},
    }


def _panel_manifest_axis(row):
    return {
        "axis_id": row["axis_id"],
        "panel_member": row["panel_member"],
        "receiver_member": row["receiver_member"],
        "previous_receiver_member": row["previous_receiver_member"],
        "current_location_status": row["current_location_status"],
        "origin_global_xyz_mm": deepcopy(row["origin_global_xyz_mm"]),
        "axis_global_xyz": deepcopy(row["axis_global_xyz"]),
        "translation_from_source_xyz_mm": deepcopy(
            row["translation_from_source_xyz_mm"]
        ),
        "purchased_nominal_length_mm": 63.5,
        "purchased_policy": POLICY,
        "purchased_product_policy": POLICY,
    }


def _action_screw_state(axis_id, panel, post, load_factor):
    endpoint = {
        "body": post,
        "point_xyz_mm": [11.25, 22.5, 33.75],
        "force_xyz_n": [-7.5, 2.25, 4.0],
        "force_radius_xyz_n": [0.01, 0.02, 0.03],
        "mpc_transfer_status": "REFUSED_MPC_ENDPOINT_TRANSFER_MISMATCH",
        "mpc_transfer_wrench_at_common_datum": {
            "force_n": [-7.5, 2.25, 4.0],
            "force_radius_n": [0.01, 0.02, 0.03],
            "moment_nmm": [13.0, -14.0, 15.0],
            "moment_radius_nmm": [0.1, 0.2, 0.3],
        },
        "physical_owner_terminal_mapping_role": "first_physical_owned_receiver_dof",
        "physical_owner_terminal_mapping_status": "DIAGNOSTIC_MATCHES_EXISTING_TRANSFER_COMPARISON",
        "physical_owner_terminal_mapping_wrench_at_common_datum": {
            "force_n": [-7.5, 2.25, 4.0],
            "force_radius_n": [0.01, 0.02, 0.03],
            "moment_nmm": [13.0, -14.0, 15.0],
            "moment_radius_nmm": [0.1, 0.2, 0.3],
        },
    }

    lateral = {
        "bilateral_kdu_n": -12.375,
        "force_rounding_radius_local_n": 0.0125,
        "local_dof": 2,
        "relative_displacement_mm": -0.004,
        "signed_force_on_first_local_n": -12.375,
        "source_law": "bilateral",
        "source_row_id": f"{axis_id}-SPR2",
        "source_stiffness_n_per_mm": 2689.0,
    }
    return {
        "axis_id": axis_id,
        "panel_member": panel,
        "receiver_member": post,
        "load_factor": load_factor,
        "receiver_wrench_preserves_both_lateral_and_withdrawal": True,
        "lateral_scalar_components": [
            deepcopy(lateral),
            {**deepcopy(lateral), "local_dof": 3, "source_row_id": f"{axis_id}-SPR3"},
        ],
        "withdrawal_scalar_component": {
            "native_internal_force_n": -1.75,
            "native_internal_radius_n": 0.005,
            "source_row_id": f"{axis_id}-SPR-A",
            "source_law": "non_qualifying_parametric_screw_withdrawal",
            "source_stiffness_n_per_mm": 2689.0,
        },
        "same_state_panel_screw_wrench_at_panel_centroid": {
            "force_n": [7.5, -2.25, -4.0],
            "force_rounding_radius_n": [0.01, 0.02, 0.03],
            "moment_nmm": [-13.0, 14.0, -15.0],
            "moment_rounding_radius_nmm": [0.1, 0.2, 0.3],
        },
        "same_state_receiver_screw_wrench_at_receiver_centroid": {
            "force_n": [-7.5, 2.25, 4.0],
            "force_rounding_radius_n": [0.01, 0.02, 0.03],
            "moment_nmm": [13.0, -14.0, 15.0],
            "moment_rounding_radius_nmm": [0.1, 0.2, 0.3],
        },
        "source_connections": [
            {
                "connection_name": f"{axis_id}/panel-wood-interface",
                "source_row_ids": [f"{axis_id}-SPR2", f"{axis_id}-SPR3"],
                "native_endpoint_order": [panel, post],
                "force_on_first_xyz_n": [7.5, -2.25, -4.0],
                "force_on_second_xyz_n": [-7.5, 2.25, 4.0],
                "force_rounding_radius_xyz_n": [0.01, 0.02, 0.03],
                "panel_endpoint": {
                    "body": panel,
                    "point_xyz_mm": [10.0, 20.0, 30.0],
                    "force_xyz_n": [7.5, -2.25, -4.0],
                },
                "receiver_endpoint": deepcopy(endpoint),
            },
            {
                "connection_name": f"{axis_id}/parametric-withdrawal",
                "source_row_ids": [f"{axis_id}-SPR-A"],
                "native_endpoint_order": [post, panel],
                "force_on_first_xyz_n": [-1.75, 0.0, 0.0],
                "force_on_second_xyz_n": [1.75, 0.0, 0.0],
                "force_rounding_radius_xyz_n": [0.005, 0.0, 0.0],
                "panel_endpoint": {
                    "body": panel,
                    "point_xyz_mm": [10.0, 20.0, 30.0],
                    "force_xyz_n": [1.75, 0.0, 0.0],
                },
                "receiver_endpoint": deepcopy(endpoint),
            },
        ],
        "geometry_application_datum_differences": {
            role: {
                "native_application_point_xyz_mm": [10.0, 20.0, 30.0],
                "signed_axial_offset_mm": 18.25625,
                "transverse_offset_mm": 0.0,
            }
            for role in (
                "lateral_model_point",
                "lateral_response_point",
                "withdrawal_model_point",
                "withdrawal_response_point",
            )
        },
        "withdrawal_law_status": "non-qualifying tension-only source law; not a Hillman property",
    }


def _panel_contact_summary(panel, post):
    wrench = {
        "force_n": [0.75, -0.25, 0.5],
        "force_rounding_radius_n": [0.01, 0.02, 0.03],
        "moment_nmm": [1.0, -2.0, 3.0],
        "moment_rounding_radius_nmm": [0.1, 0.2, 0.3],
    }
    return {
        "panel_member": panel,
        "receiver_member": post,
        "physical_contact_pressure_established": False,
        "modeled_contact_actions_on_panel": deepcopy(wrench),
        "modeled_contact_actions_on_receiver": {
            **deepcopy(wrench),
            "force_n": [-0.75, 0.25, -0.5],
            "moment_nmm": [-1.0, 2.0, -3.0],
        },
    }


def _fixture():
    panel_rows = {
        axis_id: _center_panel_axis(axis_id, spec) for axis_id, spec in CENTERS.items()
    }
    for index in range(58):
        axis_id = f"source_station_{index:02d}"
        panel_rows[axis_id] = _generic_panel_axis(axis_id, "source_station_retained")
    for axis_id, (receiver, feature_id) in LOWER_MOVES.items():
        panel, _ = ("main_lower_left", None)
        if "right" in axis_id:
            panel = "main_lower_right"
        panel_rows[axis_id] = {
            **_generic_panel_axis(axis_id, "moved"),
            "panel_member": panel,
            "receiver_member": receiver,
            "features": [{"feature_id": feature_id}],
        }

    panel_axis_rows = list(panel_rows.values())
    manifest_screw_rows = [_panel_manifest_axis(row) for row in panel_axis_rows]
    graph_screw_rows = [
        {
            **_panel_manifest_axis(row),
            "purchased_length_mm": 63.5,
            "source_occupied_diameter_mm": 4.1402,
            "source_occupied_length_mm": 50.8,
        }
        for row in panel_axis_rows
    ]
    panel_feature_axes = []
    for row in panel_axis_rows:
        source_fields = {
            "axis_length_mm": 63.5,
            "datum_global_xyz_mm": deepcopy(row["origin_global_xyz_mm"]),
            "direction_global_xyz": deepcopy(row["axis_global_xyz"]),
        }
        station = {
            "current_axis_origin_global_xyz_mm": deepcopy(row["origin_global_xyz_mm"]),
            "current_axis_direction_global_xyz": deepcopy(row["axis_global_xyz"]),
            "current_location_status": row["current_location_status"],
            "current_receiver_member": row["receiver_member"],
        }
        feature_axis = {
            "axis_id": row["axis_id"],
            "axis_group": "panel_kicker_screw_axes",
            "source_axis_fields": source_fields,
            "panel_axis_station_reconciliation": station,
        }
        if row["axis_id"] in CENTERS:
            post = row["receiver_member"]
            feature_id = CENTERS[row["axis_id"]][4]
            feature_axis["source_hardware_policy"] = {
                "purchased_nominal_length_mm": 63.5,
                "purchased_policy": POLICY,
            }
            feature_axis["receiver_memberships"] = [_axis_membership(post, feature_id)]
        panel_feature_axes.append(feature_axis)

    member_ids = ["base_header"]
    for spec in SIDE_DUTIES.values():
        member_ids.extend((spec["post"], spec["cleat"]))
    member_ids.extend(f"member_extra_{index:02d}" for index in range(39))
    member_ids = list(dict.fromkeys(member_ids))
    step_bindings = {member_id: _step_binding(member_id) for member_id in member_ids}

    bolt_specs, bolt_feature_ids = _bolt_specs()
    manifest_bolts = []
    graph_bolts = []
    feature_bolts = []
    candidate_feature_axes = []
    surface_features = {member_id: [] for member_id in member_ids}

    for axis_id, spec in bolt_specs.items():
        pair_association = {
            "association_basis": "both members occur in this candidate bore receiver membership",
            "member_pair": list(spec["pair"]),
            "receiver_pair_as_recorded": list(spec["pair"]),
            "physical_head_to_nut_order_established": False,
        }
        manifest_axis = {
            "axis_id": axis_id,
            "family": "wj05_center_x190",
            "trial_id": "wj05-center-node-posts-x190-outward-v1",
            "station_id": spec["station"],
            "receiver_member_ids": list(spec["pair"]),
            "geometric_member_pair_associations": [deepcopy(pair_association)],
            "hardware_status": "modeled CAD roles only; product and delivered dimensions unselected/unverified",
            "length_status": "modeled occupancy envelope; not a purchase length or delivered shank",
            "member_order_limit": "The geometric association does not establish physical head-to-nut stack order.",
            "scene_modeled_component_role_ids": [
                "head",
                "head_washer",
                "nut",
                "nut_washer",
                "shaft",
            ],
            "geometry": {
                "shaft_center_global_xyz_mm": deepcopy(spec["center"]),
                "axis_head_to_nut_global": deepcopy(spec["direction"]),
                "modeled_shaft_diameter_mm": 6.35,
                "modeled_shaft_occupied_length_mm": spec["length"],
                "wood_grip_material_length_mm": spec["grip"],
            },
        }
        graph_axis = {
            "axis_id": axis_id,
            "member_pair_associations": [deepcopy(pair_association)],
            "receiver_member_ids_as_recorded": list(spec["pair"]),
            "receiver_member_order_semantics": "preserved provider order only; not interpreted as physical head-to-nut order",
        }
        source_axis_fields = {
            "datum_global_xyz_mm": deepcopy(spec["center"]),
            "direction_global_xyz": deepcopy(spec["direction"]),
            "axis_length_mm": spec["length"],
            "occupied_diameter_mm": 6.35,
            "finite_interval_from_datum_mm": [
                -spec["length"] / 2.0,
                spec["length"] / 2.0,
            ],
        }
        memberships = []
        for member_id in spec["pair"]:
            feature_id = bolt_feature_ids[axis_id][member_id]
            feature = _surface_feature(feature_id)
            feature["cylinder"]["axis_origin_global_xyz_mm"] = deepcopy(spec["center"])
            feature["cylinder"]["axis_unit_global_xyz"] = deepcopy(spec["direction"])
            feature["cylinder"]["axis_station_interval_mm"] = [
                -spec["length"] / 2.0,
                spec["length"] / 2.0,
            ]
            surface_features[member_id].append(feature)
            memberships.append(_axis_membership(member_id, feature_id))
        feature_axis = {
            "axis_id": axis_id,
            "axis_group": "candidate_bolt_axes",
            "source_axis_fields": source_axis_fields,
            "receiver_memberships": memberships,
        }
        manifest_bolts.append(manifest_axis)
        graph_bolts.append(graph_axis)
        feature_bolts.append(feature_axis)

    # The current screw bores share the same five-member finished-solid bundle.
    for axis_id, spec in CENTERS.items():
        post = spec[1]
        feature = _surface_feature(spec[4])
        feature["cylinder"]["axis_origin_global_xyz_mm"] = (
            [-161.71, -17.74375, spec[3]]
            if spec[0] == "kicker_left"
            else [160.35, -17.74375, spec[3]]
        )
        feature["cylinder"]["axis_unit_global_xyz"] = [0.0, -1.0, 0.0]
        feature["cylinder"]["axis_station_interval_mm"] = [18.25625, 63.5]
        surface_features[post].append(feature)

    surface_records = []
    envelope_records = []
    for member_id in member_ids:
        binding = step_bindings[member_id]
        surface_records.append(
            {
                "member_id": member_id,
                "step_binding": {
                    "path": binding["path"],
                    "file_sha256": binding["sha256"],
                    "size_bytes": binding["size_bytes"],
                },
                "features": surface_features[member_id],
            }
        )
        is_header = member_id == "base_header"
        is_post = member_id.startswith("base_post_center_")
        is_cleat = member_id.startswith("center_post_cleat_")
        envelope_records.append(
            {
                "member_id": member_id,
                "member_kind": "frame_timber"
                if is_header or is_post
                else "candidate_block"
                if is_cleat
                else "other",
                "stock_class": "2x6"
                if is_header or is_post
                else "4x4"
                if is_cleat
                else "other",
                "stock_blank_length_mm": 2435.225
                if is_header
                else 238.9
                if is_post
                else 128.9
                if is_cleat
                else 100.0,
                "original_stock_section_mm": [38.1, 139.7]
                if is_header or is_post
                else [88.9, 88.9]
                if is_cleat
                else [10.0, 10.0],
                "original_stock_containment": {
                    "finished_oriented_spans_g_q_r_mm": [100.0, 50.0, 25.0]
                },
                "grade_assignment_status": "conditional_DF-L_No._2_basis_not_received_stock_grade"
                if is_header or is_post
                else "not_assigned",
                "conditional_grain_axis_global_xyz": [1.0, 0.0, 0.0]
                if is_header
                else [0.0, 0.0, 1.0],
                "proposed_frame": {"status": "CONTAINED"},
                "containment_status": "CONTAINED",
                "current_finished_step_path": binding["path"],
                "current_finished_step_sha256": binding["sha256"],
                "current_finished_step_size_bytes": binding["size_bytes"],
                "proposal_limits": ["Analytical stock envelope only."],
            }
        )

    panel_node_ids = [
        "main_lower_left",
        "main_lower_right",
        "kicker_left",
        "kicker_right",
        "panel_upper_left",
        "panel_upper_right",
    ]
    physical_members = [
        {"member_id": member_id} for member_id in member_ids + panel_node_ids
    ]
    finished_bindings = [
        {
            "member_id": member_id,
            "path": step_bindings[member_id]["path"],
            "file_sha256": step_bindings[member_id]["sha256"],
            "size_bytes": step_bindings[member_id]["size_bytes"],
        }
        for member_id in member_ids
    ]

    edge_data = []
    edge_specs = [
        ("base_header", "base_post_center_left", 5322.57, []),
        ("base_header", "base_post_center_right", 5322.57, []),
    ]
    for spec in SIDE_DUTIES.values():
        edge_specs.append(
            (spec["post"], spec["cleat"], 11375.5023, list(spec["post_axes"]))
        )
        edge_specs.append(
            ("base_header", spec["cleat"], 7819.5023, list(spec["header_axes"]))
        )
    graph_candidate_by_id = {row["axis_id"]: row for row in graph_bolts}
    for member_a, member_b, area, axes in edge_specs:
        edge_data.append(
            {
                "member_ids": sorted([member_a, member_b]),
                "geometry_state": "finite_opposed_planar_touch",
                "interface_geometry_state": "finite_planar_face_contact",
                "finite_shared_planar_face_area_mm2": area,
                "common_volume_mm3": 0.0,
                "minimum_separation_mm": 0.0,
                "candidate_bolt_associations": [
                    {
                        "axis_id": axis_id,
                        "member_pair": deepcopy(
                            graph_candidate_by_id[axis_id]["member_pair_associations"][
                                0
                            ]["member_pair"]
                        ),
                        "receiver_member_ids_as_recorded": deepcopy(
                            graph_candidate_by_id[axis_id][
                                "receiver_member_ids_as_recorded"
                            ]
                        ),
                        "receiver_pair_as_recorded": deepcopy(
                            graph_candidate_by_id[axis_id]["member_pair_associations"][
                                0
                            ]["receiver_pair_as_recorded"]
                        ),
                        "physical_head_to_nut_order_established": False,
                    }
                    for axis_id in axes
                ],
                "retained_frame_bolt_source_membership": [],
            }
        )

    graph_physical = [{"member_id": member_id} for member_id in member_ids]
    graph_physical.extend({"member_id": member_id} for member_id in panel_node_ids)
    graph = {
        "schema": "wood_joint_current_contact_graph/v1",
        "revision_id": REVISION,
        "counts": {"physical_member_nodes": 50},
        "parent_run": {"collector_sha256": "graph-collector"},
        "source_sha256": {"source_inventory_sha256": "source-inventory"},
        "inventories": {
            "current_panel_screw_axes": graph_screw_rows,
            "candidate_bolt_axes": graph_bolts
            + [
                {
                    "axis_id": f"candidate_extra_{index:02d}",
                    "member_pair_associations": [],
                    "receiver_member_ids_as_recorded": [],
                    "receiver_member_order_semantics": "preserved provider order only; not interpreted as physical head-to-nut order",
                }
                for index in range(84)
            ],
            "physical_members": graph_physical,
        },
        "edges": edge_data,
    }

    candidate_feature_axes.extend(feature_bolts)
    candidate_feature_axes.extend(
        {
            "axis_id": f"candidate_extra_{index:02d}",
            "axis_group": "candidate_bolt_axes",
            "source_axis_fields": {},
            "receiver_memberships": [],
        }
        for index in range(84)
    )
    manifest_bolts.extend(
        {
            "axis_id": f"candidate_extra_{index:02d}",
            "family": "other",
            "trial_id": "other",
            "station_id": "other",
            "receiver_member_ids": [],
            "geometric_member_pair_associations": [],
            "hardware_status": "other",
            "length_status": "other",
            "geometry": {},
        }
        for index in range(84)
    )

    manifest = {
        "schema": "wood_joint_current_full_frame_input_manifest/v3",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "manifest_id": "current-full-frame-input-manifest-attempt04",
        "manifest_sha256": "manifest-declared-sha",
        "inventory_counts": {
            "panel_kicker_screw_axes": 66,
            "panel_axes_owner_moved": 8,
            "panel_axes_unchanged": 58,
            "candidate_bolt_axes": 92,
            "retained_starting_frame_bolt_axes": 12,
            "full_physical_member_nodes": 50,
        },
        "panel_kicker_screw_axes": manifest_screw_rows,
        "candidate_bolt_axes": manifest_bolts,
        "retained_frame_bolt_axes": [
            {"axis_id": f"retained_{index}"} for index in range(12)
        ],
        "physical_members": physical_members,
        "finished_member_step_bindings": finished_bindings,
        "target_duties": [spec["duty"] for spec in SIDE_DUTIES.values()],
    }

    panel_feature_axes.extend(
        {
            "axis_id": f"retained_feature_{index}",
            "axis_group": "retained_frame_bolt_axes",
            "source_axis_fields": {},
            "receiver_memberships": [],
        }
        for index in range(12)
    )
    axis_features = {
        "schema": "wood_joint_axis_finished_feature_register/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "source_hashes": {
            "manifest_sha256": "manifest-file-sha",
            "surfaces_report_sha256": "surfaces-report-sha",
        },
        "source_manifest": {"manifest_sha256_field": "manifest-declared-sha"},
        "source_axis_groups": {
            "panel_kicker_screw_axes": {
                "axis_count": 66,
                "axis_ids": list(panel_rows),
                "axes": panel_feature_axes[:66],
            },
            "candidate_bolt_axes": {
                "axis_count": 92,
                "axis_ids": [row["axis_id"] for row in manifest_bolts],
                "axes": candidate_feature_axes,
            },
            "retained_frame_bolt_axes": {
                "axis_count": 12,
                "axis_ids": [f"retained_feature_{index}" for index in range(12)],
                "axes": panel_feature_axes[66:],
            },
        },
    }
    surfaces = {
        "schema": "wood_joint_current_finished_feature_register/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "source_manifest_sha256": "manifest-file-sha",
        "source_pins_sha256": "surface-pins-sha",
        "producer_sha256": "surface-producer-sha",
        "record_count": 44,
        "records": surface_records,
    }
    envelopes = {
        "schema": "wood_joint_proposed_starting_stock_envelopes/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "source_manifest_sha256": "manifest-file-sha",
        "source_pins_sha256": "stock-pins-sha",
        "producer_sha256": "stock-producer-sha",
        "record_count": 44,
        "records": envelope_records,
    }

    states = []
    for case in ("a12-rear", "a1-rear", "k12-rear"):
        for increment in range(7):
            factor = [0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0][increment]
            screw_states = [
                _action_screw_state(axis_id, spec[0], spec[1], factor)
                for axis_id, spec in CENTERS.items()
            ]
            screw_states.extend(
                {"axis_id": axis_id} for axis_id in panel_rows if axis_id not in CENTERS
            )
            mpc_summaries = []
            physical_summaries = []
            for post in ("base_post_center_left", "base_post_center_right"):
                for role in (
                    "panel_screw_lateral_plane",
                    "non_qualifying_parametric_screw_withdrawal",
                ):
                    mpc_summaries.append(
                        {
                            "body": post,
                            "source_role": role,
                            "whole_wrench_transfer_status": "REFUSED_MPC_ENDPOINT_TRANSFER_MISMATCH",
                        }
                    )
                    physical_summaries.append(
                        {
                            "body": post,
                            "source_role": role,
                            "mapping_status": "DIAGNOSTIC_MATCHES_EXISTING_TRANSFER_COMPARISON",
                            "not_a_qualified_receiver_or_support_reaction": True,
                        }
                    )
            states.append(
                {
                    "case": case,
                    "increment_index": increment,
                    "load_factor": factor,
                    "panel_receiver_mpc_transfer_status": "REFUSED",
                    "screw_states": screw_states,
                    "panel_receiver_mpc_transfer_summaries": mpc_summaries,
                    "physical_body_endpoint_projection_summaries": physical_summaries,
                    "panel_contact_receiver_summaries": [
                        _panel_contact_summary("kicker_left", "base_post_center_left"),
                        _panel_contact_summary(
                            "kicker_right", "base_post_center_right"
                        ),
                    ],
                    "source_hillman_scenario": {
                        "hillman_physical_stiffness_bounds_established": False
                    },
                }
            )

    panel_report = {
        "schema": "current_panel_receiver_transfer/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "source_pins_sha256": "panel-source-pins-sha",
        "inventory": {
            "candidate": CANDIDATE,
            "geometry_revision_id": REVISION,
            "status": "SOURCE_BOUND_INVENTORY_ONLY",
            "counts": {
                "panel_kicker_axes_total": 66,
                "moved_axes": 8,
                "unchanged_source_station_axes": 58,
            },
            "axes": panel_axis_rows,
            "current_center_kicker_receiver_check": {
                "current_receiver_map": {
                    axis_id: spec[1] for axis_id, spec in CENTERS.items()
                },
                "previous_backer_shapes_present_in_current_composition": False,
                "previous_backer_shape_ids_present": [],
                "center_seam": {
                    "panel_edge_to_edge_x_gap_mm": 0.0,
                    "panel_to_panel_interface": {
                        "finite_shared_planar_face_area_mm2": 5056.95735
                    },
                },
            },
        },
        "actions": {
            "candidate": CANDIDATE,
            "geometry_revision_id": REVISION,
            "schema": "current_panel_receiver_actions/v1",
            "producer_sha256": "panel-actions-producer-sha",
            "inventory_report_sha256": "inventory-sha",
            "panel_receiver_mpc_transfer_status": "REFUSED",
            "recursive_reduced_free_dof_mpc_transfer_status": "REFUSED",
            "claim_boundary": {
                "hillman_physical_stiffness_established": False,
                "native_solve_executed_by_this_packet": False,
                "hillman_resistance_established": False,
                "complete_joint_accepted": False,
            },
            "states": states,
        },
    }
    return panel_report, manifest, graph, axis_features, surfaces, envelopes


class CenterKickerDutiesTests(unittest.TestCase):
    def setUp(self):
        self.sources = _fixture()

    def build(self):
        return build_duties(*self.sources)

    def test_stock_members_have_stable_identity_order(self):
        identifiers = [row["member_id"] for row in self.build()["stock_members"]]
        self.assertEqual(
            identifiers,
            [
                "base_header",
                "base_post_center_left",
                "base_post_center_right",
                "center_post_cleat_left",
                "center_post_cleat_right",
            ],
        )

    def test_source_join_binds_four_current_screws_eight_bolts_and_open_paths(self):
        report = self.build()
        self.assertEqual(report["schema"], "current_center_kicker_backing_duties/v1")
        self.assertEqual(report["counts"]["panel_kicker_axes"], 66)
        self.assertEqual(report["counts"]["unchanged_source_stations"], 58)
        self.assertEqual(report["counts"]["owner_moved_axes"], 8)
        self.assertEqual(report["counts"]["center_screw_action_states"], 84)
        self.assertEqual(report["counts"]["center_screw_scalar_components"], 252)
        self.assertEqual(report["counts"]["center_candidate_bolt_axes"], 8)
        self.assertEqual(
            {row["axis_id"] for row in report["center_screws"]},
            set(CENTERS),
        )
        self.assertEqual(
            {row["axis_id"] for row in report["candidate_frame_bolts"]},
            {
                axis_id
                for spec in SIDE_DUTIES.values()
                for axis_id in spec["post_axes"] + spec["header_axes"]
            },
        )
        self.assertEqual(
            report["frame_duties"][0]["direct_post_header_seat"]["candidate_bolt_axes"],
            [],
        )
        self.assertFalse(
            report["frame_duties"][0]["complete_mechanical_load_path_established"]
        )
        self.assertFalse(
            report["qualification"]["continuous_direct_inner_edge_backing_required"]
        )
        self.assertFalse(report["qualification"]["geometry_failure_asserted"])
        self.assertTrue(
            report["open_edge_obligation"]["panel_edge_support_and_load_transfer_open"]
        )

    def test_rejects_duplicate_moved_axis_id(self):
        panel_report = self.sources[0]
        panel_report["inventory"]["axes"].append(
            deepcopy(panel_report["inventory"]["axes"][0])
        )
        with self.assertRaisesRegex(DutiesInputError, "duplicate axis_id"):
            self.build()

    def test_rejects_old_backer_returned_as_current_shape(self):
        self.sources[1]["physical_members"][-1]["member_id"] = (
            "inner_kicker_backer_left"
        )
        with self.assertRaisesRegex(
            DutiesInputError, "former center backer shape identity"
        ):
            self.build()

    def test_rejects_wrong_center_receiver_identity(self):
        axis_id = "round_kicker_left_center_1"
        next(
            row
            for row in self.sources[0]["inventory"]["axes"]
            if row["axis_id"] == axis_id
        )["receiver_member"] = "inner_kicker_backer_left"
        with self.assertRaisesRegex(DutiesInputError, "receiver_member mismatch"):
            self.build()

    def test_rejects_changed_or_duplicate_finished_bore_membership(self):
        axis_id = "round_kicker_right_center_2"
        feature_axis = next(
            row
            for row in self.sources[3]["source_axis_groups"]["panel_kicker_screw_axes"][
                "axes"
            ]
            if row["axis_id"] == axis_id
        )
        feature_axis["receiver_memberships"][0]["matched_feature_ids"] = [
            "inner_kicker_backer_right/facet010"
        ]
        with self.assertRaisesRegex(DutiesInputError, "axis feature ID mismatch"):
            self.build()

    def test_rejects_missing_saved_action_state(self):
        self.sources[0]["actions"]["states"].pop()
        with self.assertRaisesRegex(DutiesInputError, "must contain 21 states"):
            self.build()

    def test_rejects_saved_action_factor_drift(self):
        self.sources[0]["actions"]["states"][3]["load_factor"] = 0.4
        with self.assertRaisesRegex(DutiesInputError, "saved action factor"):
            self.build()

    def test_rejects_duplicate_center_action_in_state(self):
        state = self.sources[0]["actions"]["states"][0]
        state["screw_states"].append(deepcopy(state["screw_states"][0]))
        with self.assertRaisesRegex(DutiesInputError, "duplicate axis_id"):
            self.build()

    def test_action_signs_radii_application_points_and_refusal_are_copied(self):
        input_state = self.sources[0]["actions"]["states"][0]
        input_row = next(
            row
            for row in input_state["screw_states"]
            if row["axis_id"] == "round_kicker_left_center_1"
        )
        report = self.build()
        output_state = report["center_screw_action_states"][0]
        output_row = next(
            row
            for row in output_state["center_screw_states"]
            if row["axis_id"] == "round_kicker_left_center_1"
        )
        self.assertEqual(output_row, input_row)
        self.assertEqual(
            output_row["lateral_scalar_components"][0]["signed_force_on_first_local_n"],
            -12.375,
        )
        self.assertEqual(
            output_row["lateral_scalar_components"][0]["force_rounding_radius_local_n"],
            0.0125,
        )
        self.assertEqual(
            output_row["source_connections"][0]["receiver_endpoint"]["point_xyz_mm"],
            [11.25, 22.5, 33.75],
        )
        self.assertEqual(
            output_row["source_connections"][0]["receiver_endpoint"][
                "mpc_transfer_status"
            ],
            "REFUSED_MPC_ENDPOINT_TRANSFER_MISMATCH",
        )
        self.assertEqual(
            output_row["source_connections"][0]["receiver_endpoint"][
                "physical_owner_terminal_mapping_status"
            ],
            "DIAGNOSTIC_MATCHES_EXISTING_TRANSFER_COMPARISON",
        )
        output_row["source_connections"][0]["receiver_endpoint"]["force_xyz_n"][0] = (
            999.0
        )
        self.assertEqual(
            input_row["source_connections"][0]["receiver_endpoint"]["force_xyz_n"][0],
            -7.5,
        )


if __name__ == "__main__":
    unittest.main()
