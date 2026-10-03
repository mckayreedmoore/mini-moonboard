from __future__ import annotations

import copy
import importlib.util
import unittest
from collections import Counter
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("plan.py")
SPEC = importlib.util.spec_from_file_location(
    "right_corner_plan_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
plan_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plan_module)


def _make_inputs() -> tuple[dict, dict, dict, dict, dict]:
    members = sorted(plan_module.MEMBERS)
    frames: dict[str, dict] = {}
    surfaces: list[dict] = []
    envelopes: list[dict] = []
    model_geometry: dict[str, dict] = {}
    for index, member_id in enumerate(members):
        origin = [float(index * 100), 0.0, 0.0]
        grain, section_u, section_v = [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]
        step_path = f"synthetic/{member_id}.step"
        step_sha = f"{index + 1:064x}"
        step_size = 1000 + index
        stock_frame = {
            "basis_source": "reviewed proposed stock envelope g/q/r basis",
            "datum_status": "proposed minimum g/q/r corner; not a delivered-stock datum",
            "origin_global_xyz_mm": origin,
            "basis_columns_global_xyz": [grain, section_u, section_v],
        }
        frames[member_id] = {
            "origin": origin,
            "g": grain,
            "q": section_u,
            "r": section_v,
            "step_path": step_path,
            "step_sha": step_sha,
            "step_size": step_size,
            "stock_frame": stock_frame,
        }
        surfaces.append(
            {
                "member_id": member_id,
                "stock_frame": stock_frame,
                "step_binding": {
                    "path": step_path,
                    "file_sha256": step_sha,
                    "size_bytes": step_size,
                    "solid_count": 1,
                },
                "features": [],
            }
        )
        envelopes.append(
            {
                "member_id": member_id,
                "current_finished_step_path": step_path,
                "current_finished_step_sha256": step_sha,
                "current_finished_step_size_bytes": step_size,
                "current_finished_solid_count": 1,
                "proposed_frame": {
                    "status": "CONTAINED",
                    "grain_axis_global_xyz": grain,
                    "section_q_axis_global_xyz": section_u,
                    "section_r_axis_global_xyz": section_v,
                },
                "original_stock_containment": {
                    "proposed_stock_bounds_g_q_r_mm": [
                        [origin[0], origin[0] + 100.0],
                        [0.0, 100.0],
                        [0.0, 100.0],
                    ]
                },
            }
        )
        start = list(origin)
        end = [origin[0] + 100.0, 0.0, 0.0]
        model_geometry[member_id] = {
            "geometry_record": {
                "name": member_id,
                "start": start,
                "end": end,
                "axis": grain,
                "section_u": [0.0, 0.0, -1.0],
                "section_v": section_u,
                "source_descriptor": {
                    "member_id": member_id,
                    "length_mm": 100.0,
                    "step_path": step_path,
                    "step_sha256": step_sha,
                },
                "geometry_diagnostics": {
                    "geometry_source": step_path,
                    "geometry_sha256": step_sha,
                },
            }
        }

    input_surfaces = {
        "schema": "wood_joint_current_finished_feature_register/v1",
        "candidate": plan_module.CANDIDATE,
        "geometry_revision_id": plan_module.REVISION,
        "records": surfaces,
    }
    input_envelopes = {
        "schema": "wood_joint_proposed_starting_stock_envelopes/v1",
        "candidate": plan_module.CANDIDATE,
        "geometry_revision_id": plan_module.REVISION,
        "records": envelopes,
    }

    receiver_sets = plan_module.AXIS_RECEIVERS
    feature_axis_rows = []
    for axis_index, axis_id in enumerate(sorted(receiver_sets)):
        datum = [500.0 + axis_index * 10.0, 50.0, 25.0]
        direction = [1.0, 0.0, 0.0]
        center = [datum[0] + 1.25, datum[1], datum[2]]
        memberships = []
        for member_id in sorted(receiver_sets[axis_id]):
            frame = frames[member_id]
            feature_id = f"{member_id}/bore_{axis_id}"
            center_stock = [
                center[0] - frame["origin"][0],
                center[1],
                center[2],
            ]
            feature = {
                "feature_id": feature_id,
                "surface_kind": "CYLINDER",
                "centroid_global_xyz_mm": center,
                "cylinder": {
                    "material_side_geometry": "bore_like",
                    "radius_mm": 3.75,
                    "centroid_global_xyz_mm": center,
                    "centroid_stock_gqr_mm": center_stock,
                    "axis_unit_global_xyz": direction,
                    "axis_unit_stock_gqr": direction,
                },
            }
            surface_row = next(row for row in surfaces if row["member_id"] == member_id)
            surface_row["features"].append(feature)
            memberships.append(
                {
                    "receiver_member_id": member_id,
                    "binding_status": "bound_to_current_finished_stock_frame",
                    "match_status": "matched_bore_patch",
                    "matched_feature_ids": [feature_id],
                    "diagnostics": {
                        "eligible_bore_patches": 1,
                        "coaxial_cylinder_features": 1,
                    },
                    "cylinder_surface_candidates": [
                        {
                            "association_status": "eligible_bore_patch",
                            "feature_id": feature_id,
                            "surface_kind": "CYLINDER",
                            "material_side_geometry": "bore_like",
                            "finite_interval_status": "contained_in_source_finite_interval",
                            "line_distance_mm": 0.0,
                            "axis_direction_sine_error": 0.0,
                        }
                    ],
                    "current_finished_step_binding": {
                        "path": frame["step_path"],
                        "file_sha256": frame["step_sha"],
                        "size_bytes": frame["step_size"],
                        "solid_count": 1,
                    },
                    "stock_frame": frame["stock_frame"],
                    "axis_in_stock_frame": {
                        "datum_stock_gqr_mm": [
                            datum[0] - frame["origin"][0],
                            datum[1],
                            datum[2],
                        ],
                        "direction_stock_gqr": direction,
                        "axis_interval_from_datum_mm": [-25.4, 25.4],
                    },
                }
            )
        feature_axis_rows.append(
            {
                "axis_id": axis_id,
                "axis_group": "candidate_bolt_axes",
                "source_axis_fields": {
                    "datum_global_xyz_mm": datum,
                    "direction_global_xyz": direction,
                    "finite_interval_from_datum_mm": [-25.4, 25.4],
                    "axis_length_mm": 50.8,
                    "occupied_diameter_mm": 6.35,
                    "finite_extent_source_semantics": {
                        "interval_role": "modeled shaft occupancy envelope"
                    },
                },
                "receiver_memberships": memberships,
            }
        )
    input_axis_features = {
        "schema": "wood_joint_axis_finished_feature_register/v1",
        "candidate": plan_module.CANDIDATE,
        "geometry_revision_id": plan_module.REVISION,
        "source_axis_groups": {"candidate_bolt_axes": {"axes": feature_axis_rows}},
    }

    interfaces = []
    raw_rows = []
    for interface_index in range(338):
        first_member = members[interface_index % len(members)]
        if interface_index < 42:
            second_member = members[(interface_index + 1) % len(members)]
        else:
            second_member = f"outside_member_{interface_index}"
        point = [
            frames[first_member]["origin"][0] + 2000.0 + interface_index * 0.01,
            1.0,
            2.0,
        ]
        name = f"physical_interface_{interface_index:03d}"
        owner = {
            "first": first_member,
            "second": second_member,
            "point": point,
            "role": "timber_or_panel_contact",
        }
        raw_rows.append(
            {
                "name": name,
                "first_body": first_member,
                "second_body": second_member,
                "physical_owner": owner,
            }
        )
        interfaces.append(
            {
                "source_connection_name": name,
                "owner": owner,
                "source_indices": [interface_index],
            }
        )

    body_load_counts = {
        "base_header": 212,
        "base_post_outer_right": 32,
        "base_side_right": 212,
        "knee_outer_right_inner_frame_block": 20,
        "knee_outer_right_spine": 32,
    }
    models_by_case: dict[str, dict] = {}
    boundary_cases: dict[str, dict] = {}
    next_node_id = 1
    loads_by_member: dict[str, dict[str, list[float]]] = {}
    nodes_by_member: dict[str, list[int]] = {}
    body_node_coords: dict[str, list[float]] = {}
    for member_id in members:
        frame = frames[member_id]
        count = body_load_counts[member_id]
        load_map: dict[str, list[float]] = {}
        node_ids: list[int] = []
        for local_index in range(count):
            node_id = next_node_id
            next_node_id += 1
            load_map[str(node_id)] = [0.0, 0.0, 1.0]
            node_ids.append(node_id)
            body_node_coords[str(node_id)] = [
                frame["origin"][0] + 1000.0 + local_index * 2.0e-6,
                10.0,
                20.0,
            ]
        loads_by_member[member_id] = load_map
        nodes_by_member[member_id] = node_ids

    for case_id in plan_module.CASE_IDS:
        datums = {}
        for member_id in members:
            geometry = model_geometry[member_id]["geometry_record"]
            datums[member_id] = [
                (start + end) / 2.0
                for start, end in zip(geometry["start"], geometry["end"], strict=True)
            ]
        models_by_case[case_id] = {
            "schema": "current_springa_selected_floor_input_model/v1",
            "case_id": case_id,
            "candidate": plan_module.CANDIDATE,
            "geometry_revision_id": plan_module.REVISION,
            "body_geometry": model_geometry,
            "raw_source_carrier_law_inventory_rows": raw_rows,
            "physical_body_loads": loads_by_member,
            "physical_body_nodes": nodes_by_member,
            "nodes": body_node_coords,
        }
        boundary_cases[case_id] = {
            "interface_count": 338,
            "scalar_source_count": 338,
            "inventory": copy.deepcopy(interfaces),
            "reporting_datums_xyz_mm": datums,
        }

    boundary_report = {
        "candidate": plan_module.CANDIDATE,
        "revision": plan_module.REVISION,
        "status": "PASS_RIGHT_FIVE_BODY_BOUNDARY_RECONSTRUCTION_ONLY",
        "members": members,
        "cases": boundary_cases,
        "state_count": 21,
        "states": [
            {"case_id": case_id, "increment_index": index}
            for case_id in plan_module.CASE_IDS
            for index in range(7)
        ],
    }
    return (
        input_surfaces,
        input_axis_features,
        input_envelopes,
        boundary_report,
        models_by_case,
    )


class RightCornerPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inputs = _make_inputs()

    def test_source_plan_preserves_frames_memberships_and_all_station_identities(
        self,
    ) -> None:
        report = plan_module.build_plan(*self.inputs)
        self.assertEqual(
            report["schema"], "wood_joint_right_corner_finished_section_plan/v1"
        )
        self.assertEqual(report["counts"]["physical_interface_identities"], 338)
        self.assertEqual(report["counts"]["in_scope_interface_endpoints"], 380)
        self.assertEqual(report["counts"]["physical_body_load_nodes"], 508)
        self.assertEqual(report["counts"]["matched_receiver_bore_centers"], 14)
        self.assertEqual(report["counts"]["point_inventory"], 902)
        self.assertEqual(
            report["counts"]["unique_section_planes"], len(report["section_planes"])
        )
        self.assertEqual(
            [row["member_id"] for row in report["member_frames_and_step_bindings"]],
            sorted(plan_module.MEMBERS),
        )
        self.assertEqual(len(report["axis_memberships"]), 14)
        self.assertEqual(len(report["interface_identities"]), 338)
        self.assertEqual(len(report["selected_axes"]), 6)
        self.assertTrue(
            all("receiver_memberships" not in axis for axis in report["selected_axes"])
        )
        self.assertEqual(
            sum(plane["source_identity_count"] for plane in report["section_planes"]),
            902,
        )
        frames = {
            row["member_id"]: row for row in report["member_frames_and_step_bindings"]
        }
        for plane in report["section_planes"]:
            frame = frames[plane["member_id"]]
            offset = [
                plane["plane_origin_global_xyz_mm"][index]
                - frame["origin_global_xyz_mm"][index]
                for index in range(3)
            ]
            station = sum(
                offset[index] * frame["grain_axis_global_xyz"][index]
                for index in range(3)
            )
            self.assertAlmostEqual(station, plane["grain_station_mm"], places=10)
        kinds = Counter(row["kind"] for row in report["point_inventory"])
        self.assertEqual(
            kinds,
            {
                "interface_endpoint": 380,
                "physical_body_load_node": 508,
                "receiver_bore_center": 14,
            },
        )
        header = next(
            row
            for row in report["axis_memberships"]
            if row["axis_id"] == "knee_outer_right_inner_header_1"
            and row["receiver_member_id"] == "base_header"
        )
        self.assertAlmostEqual(
            header["saved_bore_center_grain_station_mm"]
            - header["source_axis_datum_grain_station_mm"],
            1.25,
        )
        self.assertNotEqual(
            header["source_axis_datum_global_xyz_mm"],
            header["saved_bore_center_global_xyz_mm"],
        )

    def test_left_handed_saved_stock_frame_is_rejected(self) -> None:
        surfaces, axis_features, envelopes, boundary, models = copy.deepcopy(
            self.inputs
        )
        row = next(
            item for item in surfaces["records"] if item["member_id"] == "base_header"
        )
        row["stock_frame"]["basis_columns_global_xyz"][2] = [0.0, 0.0, -1.0]
        with self.assertRaisesRegex(plan_module.PlanRefusal, "right-handed"):
            plan_module.build_plan(surfaces, axis_features, envelopes, boundary, models)

    def test_bore_centroid_off_axis_is_rejected(self) -> None:
        surfaces, axis_features, envelopes, boundary, models = copy.deepcopy(
            self.inputs
        )
        feature = next(
            row for row in surfaces["records"] if row["member_id"] == "base_header"
        )["features"][0]
        feature["centroid_global_xyz_mm"][1] += 0.25
        feature["cylinder"]["centroid_global_xyz_mm"][1] += 0.25
        with self.assertRaisesRegex(plan_module.PlanRefusal, "off source axis line"):
            plan_module.build_plan(surfaces, axis_features, envelopes, boundary, models)

    def test_duplicate_boundary_interface_identity_is_rejected(self) -> None:
        surfaces, axis_features, envelopes, boundary, models = copy.deepcopy(
            self.inputs
        )
        inventory = boundary["cases"][plan_module.CASE_IDS[0]]["inventory"]
        inventory[1]["source_connection_name"] = inventory[0]["source_connection_name"]
        with self.assertRaisesRegex(
            plan_module.PlanRefusal, "duplicate source_connection_name"
        ):
            plan_module.build_plan(surfaces, axis_features, envelopes, boundary, models)

    def test_partial_transitive_station_coincidence_is_rejected(self) -> None:
        frame = {
            "origin_global_xyz_mm": [0.0, 0.0, 0.0],
            "grain_axis_global_xyz": [1.0, 0.0, 0.0],
            "section_u_global_xyz": [0.0, 1.0, 0.0],
            "section_v_global_xyz": [0.0, 0.0, 1.0],
        }
        candidates = [
            {
                "identity_key": f"point_{index}",
                "kind": "interface_endpoint",
                "member_id": "base_header",
                "point_global_xyz_mm": [station, 0.0, 0.0],
                "source_identity": {"index": index},
            }
            for index, station in enumerate((0.0, 0.75e-6, 1.5e-6))
        ]
        with self.assertRaisesRegex(plan_module.PlanRefusal, "ambiguous transitive"):
            plan_module._merge_section_planes(candidates, {"base_header": frame})


if __name__ == "__main__":
    unittest.main()
