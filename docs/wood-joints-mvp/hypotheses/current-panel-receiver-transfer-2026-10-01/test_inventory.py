from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("inventory.py")
SPEC = importlib.util.spec_from_file_location("panel_inventory_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)
GRAPH_INPUT_FIXTURE = "fixture/graph_geometry_input.json"


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def _write_json(root: Path, relative_path: str, value: object) -> tuple[str, int]:
    raw = _json_bytes(value)
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest(), len(raw)


def _fixture(root: Path) -> list[str]:
    moved_rows = [
        (
            "round_panel_lower_left_edge_1",
            "main_lower_left",
            "base_rail_bottom_left",
            [0.0, 49.430367185, 58.908817676],
        ),
        (
            "round_panel_lower_left_edge_2",
            "main_lower_left",
            "base_rail_bottom_left",
            [0.0, 49.430367185, 58.908817676],
        ),
        (
            "round_panel_lower_right_edge_1",
            "main_lower_right",
            "base_rail_bottom_right",
            [0.0, 49.430367185, 58.908817676],
        ),
        (
            "round_panel_lower_right_edge_2",
            "main_lower_right",
            "base_rail_bottom_right",
            [0.0, 49.430367185, 58.908817676],
        ),
        (
            "round_kicker_left_center_1",
            "kicker_left",
            "base_post_center_left",
            [-91.710000000, 0.0, 0.0],
        ),
        (
            "round_kicker_left_center_2",
            "kicker_left",
            "base_post_center_left",
            [-91.710000000, 0.0, 0.0],
        ),
        (
            "round_kicker_right_center_1",
            "kicker_right",
            "base_post_center_right",
            [90.350000000, 0.0, 0.0],
        ),
        (
            "round_kicker_right_center_2",
            "kicker_right",
            "base_post_center_right",
            [90.350000000, 0.0, 0.0],
        ),
    ]
    axes: list[dict] = []
    source_axes: list[dict] = []
    moved_by_id = {axis_id: row for row in moved_rows for axis_id in [row[0]]}
    for index in range(58):
        axis_id = f"fixture_panel_axis_{index:02d}"
        panel = f"fixture_panel_{index % 3}"
        receiver = f"fixture_receiver_{index % 5}"
        origin = [float(index * 10), 5.0, 10.0]
        axes.append(
            {
                "axis_id": axis_id,
                "panel_member": panel,
                "receiver_member": receiver,
                "previous_receiver_member": receiver,
                "origin_global_xyz_mm": origin,
                "axis_global_xyz": [1.0, 0.0, 0.0],
                "translation_from_source_xyz_mm": [0.0, 0.0, 0.0],
                "current_location_status": "source_station_retained",
                "owner_moved_axis_record": None,
            }
        )
    for index, (axis_id, panel, receiver, translation) in enumerate(moved_rows):
        if "kicker_left_center" in axis_id:
            origin = [-70.0, -17.74375, 60.0 if axis_id.endswith("_1") else 192.0]
            direction = [0.0, -1.0, 0.0]
            previous_receiver = "inner_kicker_backer_left"
        elif "kicker_right_center" in axis_id:
            origin = [70.0, -17.74375, 60.0 if axis_id.endswith("_1") else 192.0]
            direction = [0.0, -1.0, 0.0]
            previous_receiver = "inner_kicker_backer_right"
        else:
            origin = [-435.075 + 400.0 * (index % 2), 20.152907241, 322.070210041]
            direction = [0.0, -0.766044443119, 0.642787609687]
            previous_receiver = receiver
        new_origin = [origin[i] + translation[i] for i in range(3)]
        move = {
            "axis_id": axis_id,
            "old_start_global_xyz_mm": origin,
            "new_start_global_xyz_mm": new_origin,
            "translation_global_xyz_mm": translation,
            "axis_global_xyz_unchanged": direction,
            "panel_member": panel,
            "previous_receiver_member": previous_receiver,
            "receiver_member": receiver,
        }
        axes.append(
            {
                "axis_id": axis_id,
                "panel_member": panel,
                "receiver_member": receiver,
                "previous_receiver_member": previous_receiver,
                "origin_global_xyz_mm": new_origin,
                "axis_global_xyz": direction,
                "translation_from_source_xyz_mm": translation,
                "current_location_status": "moved",
                "owner_moved_axis_record": move,
            }
        )

    axes.sort(key=lambda row: row["axis_id"])
    current_step_bindings: dict[str, dict] = {}
    for row in axes:
        receiver = row["receiver_member"]
        current_step_bindings.setdefault(
            receiver,
            {
                "member_id": receiver,
                "path": f"members/{receiver}.step",
                "file_sha256": hashlib.sha256(receiver.encode()).hexdigest(),
                "size_bytes": len(receiver.encode()),
            },
        )

    for row in axes:
        axis_id = row["axis_id"]
        source_row = moved_by_id.get(axis_id)
        if source_row is None:
            source_origin = row["origin_global_xyz_mm"]
            source_receiver = row["receiver_member"]
            source_finished_receiver = source_receiver
        else:
            move = row["owner_moved_axis_record"]
            source_origin = move["old_start_global_xyz_mm"]
            source_receiver = row["previous_receiver_member"]
            source_finished_receiver = row["receiver_member"]
        source_axes.append(
            {
                "axis_id": axis_id,
                "members": [row["panel_member"], source_finished_receiver],
                "origin_global_xyz_mm": source_origin,
                "axis_global_xyz": row["axis_global_xyz"],
                "source_occupied_length_mm": 50.8,
                "source_occupied_diameter_mm": 4.1402,
                "shop_opening_kind": "hillman_panel",
                "panel_member": row["panel_member"],
                "source_finished_receiver_member": source_finished_receiver,
                "candidate_finished_receiver_member": source_receiver,
                "shop_purchased_length_mm": 63.5,
                "receiver_to_frame_path": "source structural member; replacement interfaces remain unqualified",
                "receiver_to_frame_path_complete": False,
            }
        )

    source_inventory = {
        "schema": "wood_joint_source_inventory/v1",
        "candidate": inventory.CANDIDATE,
        "fixed_panel_kicker_screws": source_axes,
    }
    source_hash, source_size = _write_json(
        root, inventory.SOURCE_INVENTORY, source_inventory
    )

    def manifest_row(axis: dict) -> dict:
        row = dict(axis)
        row["purchased_nominal_length_mm"] = 63.5
        row["purchased_policy"] = (
            "Hillman 42605; existing purchased screw and pilot policy retained"
        )
        row["receiver_screen"] = {
            "raw_receiver_axis_envelope_intersects": True,
            "finished_receiver_axis_envelope_clear": True,
        }
        row["historical_source_inventory_record"] = {
            "source_receiver_member": next(
                source["source_finished_receiver_member"]
                for source in source_axes
                if source["axis_id"] == axis["axis_id"]
            ),
            "candidate_receiver_member": axis["previous_receiver_member"],
            "source_occupied_length_mm": 50.8,
        }
        return row

    manifest_axes = [manifest_row(row) for row in axes]
    step_bindings = list(current_step_bindings.values())
    attempt03 = {
        "schema": "wood_joint_current_full_frame_input_manifest/v2",
        "candidate": inventory.CANDIDATE,
        "geometry_revision_id": inventory.GEOMETRY_REVISION,
        "panel_kicker_screw_axes": manifest_axes,
        "finished_member_step_bindings": step_bindings,
    }
    manifest03_hash, manifest03_size = _write_json(
        root, inventory.MANIFEST03, attempt03
    )
    attempt04 = {
        "schema": "wood_joint_current_full_frame_input_manifest/v3",
        "candidate": inventory.CANDIDATE,
        "geometry_revision_id": inventory.GEOMETRY_REVISION,
        "panel_kicker_screw_axes": manifest_axes,
        "finished_member_step_bindings": step_bindings,
        "attempt03_base_manifest": {
            "path": inventory.MANIFEST03,
            "file_sha256": manifest03_hash,
            "size_bytes": manifest03_size,
        },
        "attempt04_input_source_pins": {
            inventory.MANIFEST03: manifest03_hash,
            inventory.SOURCE_INVENTORY: source_hash,
        },
    }
    manifest04_hash, manifest04_size = _write_json(
        root, inventory.MANIFEST04, attempt04
    )

    feature_closure = {
        "schema": "wood_joint_current_finished_feature_register_source_pins/v1",
        "candidate": inventory.CANDIDATE,
        "current_manifest04_sha256": manifest04_hash,
        "pins": {
            "current_manifest04": {
                "path": inventory.MANIFEST04,
                "sha256": manifest04_hash,
                "size_bytes": manifest04_size,
            },
            "source_inventory": {
                "path": inventory.SOURCE_INVENTORY,
                "sha256": source_hash,
                "size_bytes": source_size,
            },
        },
    }
    closure_hash, _closure_size = _write_json(
        root, inventory.FEATURE_CLOSURE_PINS, feature_closure
    )

    screen_axes: list[dict] = []
    feature_axes: list[dict] = []
    graph_axes: list[dict] = []
    interfaces: dict[tuple[str, str], dict] = {}
    graph_associations: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for axis in axes:
        axis_id = axis["axis_id"]
        panel = axis["panel_member"]
        receiver = axis["receiver_member"]
        origin = axis["origin_global_xyz_mm"]
        direction = axis["axis_global_xyz"]
        binding = current_step_bindings[receiver]
        feature_id = f"{receiver}/facet_{axis_id}"
        feature_axis = {
            "axis_group": "panel_kicker_screw_axes",
            "axis_id": axis_id,
            "panel_member_reference": {
                "member_id": panel,
                "coverage_status": "outside_panel_surface_scope",
            },
            "panel_axis_station_reconciliation": {
                "current_location_status": axis["current_location_status"],
                "current_receiver_member": receiver,
                "previous_receiver_member": axis["previous_receiver_member"],
                "current_axis_origin_global_xyz_mm": origin,
                "current_axis_direction_global_xyz": direction,
            },
            "source_axis_fields": {
                "datum_global_xyz_mm": origin,
                "direction_global_xyz": direction,
                "finite_interval_from_datum_mm": [0.0, 63.5],
            },
            "receiver_memberships": [
                {
                    "receiver_member_id": receiver,
                    "match_status": "matched_bore_patch",
                    "matched_feature_ids": [feature_id],
                    "axis_in_stock_frame": {"axis_interval_from_datum_mm": [0.0, 63.5]},
                    "current_finished_step_binding": {
                        "path": binding["path"],
                        "file_sha256": binding["file_sha256"],
                        "size_bytes": binding["size_bytes"],
                    },
                    "cylinder_surface_candidates": [
                        {
                            "feature_id": feature_id,
                            "surface_kind": "CYLINDER",
                            "material_side_geometry": "bore_like",
                            "association_status": "eligible_bore_patch",
                            "finite_interval_status": "contained_in_source_finite_interval",
                            "patch_interval_projected_from_axis_datum_mm": [
                                18.25625,
                                63.5,
                            ],
                            "axial_overlap_length_mm": 45.24375,
                            "cylinder_radius_mm": 2.0701,
                            "line_distance_mm": 0.0,
                            "axis_direction_sine_error": 0.0,
                        }
                    ],
                }
            ],
        }
        feature_axes.append(feature_axis)
        screen_axes.append(
            {
                **{
                    key: axis[key]
                    for key in (
                        "axis_id",
                        "panel_member",
                        "receiver_member",
                        "previous_receiver_member",
                        "origin_global_xyz_mm",
                        "axis_global_xyz",
                        "translation_from_source_xyz_mm",
                        "current_location_status",
                    )
                },
                "source_occupied_length_mm": 50.8,
                "source_occupied_diameter_mm": 4.1402,
                "purchased_length_mm": 63.5,
                "purchased_product_policy": "Hillman 42605; existing purchased screw and pilot policy retained",
                "raw_receiver_intersection_axial_bounds_from_axis_start_mm": [
                    18.25625,
                    63.5,
                ],
                "raw_receiver_full_section_equivalent_length_mm": 45.24375,
                "finished_receiver_axis_envelope_clear": True,
                "materialized_axis_envelope": {
                    "axial_bounds_from_reported_origin_mm": [0.0, 63.5],
                },
            }
        )
        graph_axes.append(
            {
                key: axis[key]
                for key in (
                    "axis_id",
                    "panel_member",
                    "receiver_member",
                    "previous_receiver_member",
                    "origin_global_xyz_mm",
                    "axis_global_xyz",
                    "translation_from_source_xyz_mm",
                    "current_location_status",
                )
            }
            | {
                "purchased_length_mm": 63.5,
                "purchased_product_policy": "Hillman 42605; existing purchased screw and pilot policy retained",
                "source_occupied_length_mm": 50.8,
                "source_occupied_diameter_mm": 4.1402,
            }
        )
        pair = (panel, receiver)
        interfaces.setdefault(
            pair,
            {
                "panel_member": panel,
                "receiver_member": receiver,
                "fixed_hillman_axis_ids": [],
                "geometry_state": "finite_planar_face_contact",
                "finite_shared_planar_face_area_mm2": 100.0,
                "common_volume_mm3": 0.0,
                "minimum_separation_mm": 0.0,
            },
        )["fixed_hillman_axis_ids"].append(axis_id)
        graph_associations[pair].append(
            {
                "association_basis": "current 66-axis map from the frozen revision report",
                "axis_id": axis_id,
                "current_location_status": axis["current_location_status"],
                "panel_member": panel,
                "receiver_member": receiver,
            }
        )

    feature_report = {
        "schema": "wood_joint_axis_finished_feature_register/v1",
        "candidate": inventory.CANDIDATE,
        "geometry_revision_id": inventory.GEOMETRY_REVISION,
        "source_hashes": {
            "manifest_sha256": manifest04_hash,
            "source_inventory_sha256": source_hash,
            "surfaces_source_pins_sha256": closure_hash,
        },
        "source_axis_groups": {
            "panel_kicker_screw_axes": {
                "axis_count": 66,
                "axis_ids": [row["axis_id"] for row in feature_axes],
                "axes": feature_axes,
            }
        },
    }
    feature_hash, _ = _write_json(root, inventory.FEATURE_REGISTER, feature_report)
    axis_source_pins = {
        "schema": "wood_joint_axis_source_pins/v1",
        "outputs": {
            "axis_features": {
                "path": inventory.FEATURE_REGISTER,
                "sha256": feature_hash,
            }
        },
        "sources": {
            "current_full_frame_input_manifest": {
                "path": inventory.MANIFEST04,
                "sha256": manifest04_hash,
            },
            "current_screw_source_inventory": {
                "path": inventory.SOURCE_INVENTORY,
                "sha256": source_hash,
            },
            "finished_surfaces_source_pins": {
                "path": inventory.FEATURE_CLOSURE_PINS,
                "sha256": closure_hash,
            },
        },
    }
    _write_json(root, inventory.FEATURE_SOURCE_PINS, axis_source_pins)

    screen = {
        "schema": "wood_joint_current_receiver_screen/v1",
        "revision_id": inventory.GEOMETRY_REVISION,
        "counts": {
            "panel_kicker_axes_total": 66,
            "unchanged_source_station_axes": 58,
            "moved_axes": 8,
            "current_receiver_member_counts": dict(
                sorted(Counter(row["receiver_member"] for row in axes).items())
            ),
        },
        "axes": screen_axes,
        "four_moved_kicker_center_receiver_check": {
            "current_receiver_map": inventory.CENTER_KICKER_CURRENT_RECEIVERS,
            "previous_backer_shapes_present_in_current_composition": False,
            "previous_backer_shape_ids_present": [],
            "side_to_side_center_post_bbox_gap_x_mm": 283.96,
        },
        "panel_to_receiver_interfaces": {
            "interfaces": list(interfaces.values()),
            "kicker_center_seam": {
                "panel_edge_to_edge_x_gap_mm": 0.0,
                "panel_edge_planes_touch_by_x_extent": True,
                "panel_to_panel_interface": {
                    "finite_shared_planar_face_area_mm2": 50.0,
                },
                "limits": ["Geometry does not establish support or capacity."],
            },
        },
    }
    _write_json(root, inventory.RECEIVER_SCREEN, screen)

    physical_members = {
        row["panel_member"]: {"member_id": row["panel_member"], "member_kind": "panel"}
        for row in axes
    }
    for receiver in {row["receiver_member"] for row in axes}:
        physical_members[receiver] = {"member_id": receiver, "member_kind": "timber"}
        neighbor = f"support_{receiver}"
        physical_members[neighbor] = {"member_id": neighbor, "member_kind": "timber"}
    graph_edges = []
    for pair, associations in sorted(graph_associations.items()):
        graph_edges.append(
            {
                "member_ids": list(pair),
                "geometry_state": "finite_opposed_planar_touch",
                "interface_geometry_state": "finite_planar_face_contact",
                "contact_measurement_basis": "finite model planar face contact",
                "finite_shared_planar_face_area_mm2": 100.0,
                "opposed_planar_face_contact_area_mm2": 100.0,
                "cooriented_planar_face_contact_area_mm2": 0.0,
                "common_volume_mm3": 0.0,
                "minimum_separation_mm": 0.0,
                "current_panel_screw_associations": associations,
            }
        )
    for receiver in sorted({row["receiver_member"] for row in axes}):
        graph_edges.append(
            {
                "member_ids": [receiver, f"support_{receiver}"],
                "geometry_state": "finite_opposed_planar_touch",
                "interface_geometry_state": "finite_planar_face_contact",
                "contact_measurement_basis": "finite model planar face contact",
                "finite_shared_planar_face_area_mm2": 40.0,
                "opposed_planar_face_contact_area_mm2": 40.0,
                "cooriented_planar_face_contact_area_mm2": 0.0,
                "common_volume_mm3": 0.0,
                "minimum_separation_mm": 0.0,
                "current_panel_screw_associations": [],
            }
        )
    graph_input_hash, _ = _write_json(
        root, GRAPH_INPUT_FIXTURE, {"schema": "synthetic_geometry_source/v1"}
    )
    graph = {
        "schema": "wood_joint_current_contact_graph/v1",
        "geometry_revision_id": inventory.GEOMETRY_REVISION,
        "inventories": {
            "current_panel_screw_axes": graph_axes,
            "physical_members": list(physical_members.values()),
        },
        "edges": graph_edges,
        "source_sha256": {
            "geometry_source_inputs_sha256": {
                inventory.SOURCE_INVENTORY: source_hash,
                GRAPH_INPUT_FIXTURE: graph_input_hash,
            }
        },
    }
    _write_json(root, inventory.CONTACT_GRAPH, graph)
    return [row["axis_id"] for row in axes]


class PanelInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.axis_ids = _fixture(self.root)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _read(self, path: str) -> dict:
        return json.loads((self.root / path).read_text())

    def _write(self, path: str, document: dict) -> None:
        _write_json(self.root, path, document)

    def test_saved_join_preserves_all_axes_and_nominal_geometry_limits(self) -> None:
        report, pins = inventory.build_report(root=self.root)
        self.assertEqual(report["counts"]["panel_kicker_axes_total"], 66)
        self.assertEqual(report["counts"]["unchanged_source_station_axes"], 58)
        self.assertEqual(report["counts"]["moved_axes"], 8)
        self.assertEqual([row["axis_id"] for row in report["axes"]], self.axis_ids)
        self.assertEqual(
            [row["path"] for row in pins["sources"]],
            sorted(row["path"] for row in pins["sources"]),
        )
        self.assertIn(GRAPH_INPUT_FIXTURE, {row["path"] for row in pins["sources"]})

        left_center = next(
            row
            for row in report["axes"]
            if row["axis_id"] == "round_kicker_left_center_1"
        )
        self.assertEqual(left_center["receiver_member"], "base_post_center_left")
        self.assertEqual(
            left_center["previous_receiver_member"], "inner_kicker_backer_left"
        )
        self.assertEqual(
            left_center["source_provenance"]["source_occupied_length_mm"], 50.8
        )
        self.assertEqual(
            left_center["nominal_embedment_envelope"]["purchased_nominal_length_mm"],
            63.5,
        )
        self.assertAlmostEqual(
            left_center["nominal_embedment_envelope"][
                "matched_bore_patch_overlap_length_mm"
            ],
            45.24375,
        )
        self.assertIn(
            "not actual screw embedment",
            left_center["nominal_embedment_envelope"]["status"],
        )
        self.assertFalse(
            left_center["support_edge_evidence"][
                "receiver_to_frame_path_complete_in_source_inventory"
            ]
        )
        self.assertEqual(len(left_center["features"]), 1)

    def test_stale_center_post_receiver_in_screen_is_rejected(self) -> None:
        screen = self._read(inventory.RECEIVER_SCREEN)
        row = next(
            row
            for row in screen["axes"]
            if row["axis_id"] == "round_kicker_left_center_1"
        )
        row["receiver_member"] = "inner_kicker_backer_left"
        self._write(inventory.RECEIVER_SCREEN, screen)
        with self.assertRaisesRegex(
            ValueError, "current pair differs in receiver screen"
        ):
            inventory.build_report(root=self.root)

    def test_stale_center_receiver_graph_association_is_rejected(self) -> None:
        graph = self._read(inventory.CONTACT_GRAPH)
        association = next(
            association
            for edge in graph["edges"]
            for association in edge["current_panel_screw_associations"]
            if association["axis_id"] == "round_kicker_left_center_1"
        )
        association["receiver_member"] = "inner_kicker_backer_left"
        self._write(inventory.CONTACT_GRAPH, graph)
        with self.assertRaisesRegex(ValueError, "graph association metadata differs"):
            inventory.build_report(root=self.root)

    def test_feature_byte_change_without_updated_output_pin_is_rejected(self) -> None:
        feature = self._read(inventory.FEATURE_REGISTER)
        feature["source_axis_groups"]["panel_kicker_screw_axes"]["axes"][0][
            "panel_member_reference"
        ]["member_id"] = "mutated_panel"
        self._write(inventory.FEATURE_REGISTER, feature)
        with self.assertRaisesRegex(
            ValueError, "feature report does not match its output pin"
        ):
            inventory.build_report(root=self.root)

    def test_stale_contact_graph_geometry_input_is_rejected(self) -> None:
        (self.root / GRAPH_INPUT_FIXTURE).write_text("mutated source bytes\n")
        with self.assertRaisesRegex(ValueError, "pinned source hash changed"):
            inventory.build_report(root=self.root)


if __name__ == "__main__":
    unittest.main()
