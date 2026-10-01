from __future__ import annotations

import copy
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("axis_features.py")
SPEC = importlib.util.spec_from_file_location("axis_features_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
axis_features = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(axis_features)


def cylinder(
    feature_id: str,
    interval: tuple[float, float],
    *,
    side: str = "bore_like",
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
    direction: tuple[float, float, float] = (1.0, 0.0, 0.0),
    radius: float = 2.0,
) -> dict:
    return {
        "feature_id": feature_id,
        "surface_kind": "CYLINDER",
        "classification": "cylindrical_trimmed_face",
        "cylinder": {
            "axis_origin_global_xyz_mm": list(origin),
            "axis_unit_global_xyz": list(direction),
            "radius_mm": radius,
            "axis_station_interval_mm": list(interval),
            "material_side_geometry": side,
        },
    }


def member(member_id: str, digest: str, features: list[dict]) -> dict:
    return {
        "member_id": member_id,
        "step_binding": {
            "path": f"members/{member_id}.step",
            "file_sha256": digest,
            "solid_count": 1,
            "manifest_roundtrip_valid": True,
        },
        "stock_frame": {
            "origin_global_xyz_mm": [0.0, 0.0, 0.0],
            "basis_columns_global_xyz": [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            "original_dimensions_gqr_mm": [100.0, 50.0, 20.0],
        },
        "features": features,
    }


def synthetic_inputs() -> tuple[dict, dict, dict]:
    surfaces = {
        "schema": "wood_joint_current_finished_feature_register/v1",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "source_manifest_id": "current-full-frame-input-manifest-attempt04",
        "records": [
            member(
                "frame_a",
                "a" * 64,
                [
                    cylinder(
                        "frame_a/facet001", (-5.0, 0.0), direction=(-1.0, 0.0, 0.0)
                    ),
                    cylinder(
                        "frame_a/facet002", (0.0, 5.0), direction=(-1.0, 0.0, 0.0)
                    ),
                    cylinder(
                        "frame_a/facet003",
                        (-5.0, 5.0),
                        side="exterior_like",
                        radius=5.0,
                    ),
                    cylinder(
                        "frame_a/facet004", (-5.0, 5.0), side="ambiguous", radius=3.0
                    ),
                    cylinder(
                        "frame_a/facet005",
                        (-5.0, 5.0),
                        origin=(0.0, 0.001, 0.0),
                    ),
                    {
                        "feature_id": "frame_a/facet006",
                        "surface_kind": "PLANE",
                    },
                ],
            ),
            member(
                "block_b",
                "b" * 64,
                [cylinder("block_b/facet001", (0.0, 10.0))],
            ),
        ],
    }
    manifest = {
        "manifest_id": "current-full-frame-input-manifest-attempt04",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "physical_members": [
            {
                "member_id": "frame_a",
                "member_kind": "timber",
                "current_finished_step_binding": {
                    "path": "members/frame_a.step",
                    "file_sha256": "a" * 64,
                },
            },
            {
                "member_id": "block_b",
                "member_kind": "timber",
                "current_finished_step_binding": {
                    "path": "members/block_b.step",
                    "file_sha256": "b" * 64,
                },
            },
            {"member_id": "panel_x", "member_kind": "panel"},
        ],
        "candidate_blocks": [{"part_id": "block_b"}],
        "candidate_bolt_axes": [
            {
                "axis_id": "candidate_1",
                "receiver_member_ids": ["frame_a"],
                "geometry": {
                    "shaft_center_global_xyz_mm": [0.0, 0.0, 0.0],
                    "axis_head_to_nut_global": [1.0, 0.0, 0.0],
                    "modeled_shaft_occupied_length_mm": 10.0,
                    "modeled_shaft_diameter_mm": 4.0,
                },
                "hardware_status": "candidate geometry only",
            }
        ],
        "retained_frame_bolt_axes": [
            {
                "axis_id": "retained_1",
                "members_as_recorded": ["block_b"],
                "origin_global_xyz_mm": [0.0, 0.0, 0.0],
                "axis_global_xyz": [1.0, 0.0, 0.0],
                "source_occupied_length_mm": 10.0,
                "source_occupied_diameter_mm": 6.0,
                "hardware_status": "recheck required",
            }
        ],
        "panel_kicker_screw_axes": [
            {
                "axis_id": "screw_1",
                "receiver_member": "frame_a",
                "panel_member": "panel_x",
                "origin_global_xyz_mm": [0.0, 1.0, 0.0],
                "axis_global_xyz": [1.0, 0.0, 0.0],
                "purchased_nominal_length_mm": 10.0,
                "purchased_policy": "Hillman 42605; existing policy",
                "hardware_status": "purchased policy retained",
                "current_location_status": "moved",
                "previous_receiver_member": "frame_a",
                "owner_moved_axis_record": {
                    "axis_id": "screw_1",
                    "old_start_global_xyz_mm": [0.0, 0.0, 0.0],
                    "new_start_global_xyz_mm": [0.0, 1.0, 0.0],
                    "translation_global_xyz_mm": [0.0, 1.0, 0.0],
                    "axis_global_xyz_unchanged": [1.0, 0.0, 0.0],
                    "receiver_member": "frame_a",
                    "previous_receiver_member": "frame_a",
                    "panel_member": "panel_x",
                },
                "historical_source_inventory_record": {
                    "source_occupied_length_mm": 50.8,
                },
            }
        ],
    }
    source_inventory = {
        "fixed_panel_kicker_screws": [
            {
                "axis_id": "screw_1",
                "origin_global_xyz_mm": [0.0, 0.0, 0.0],
                "axis_global_xyz": [1.0, 0.0, 0.0],
                "shop_purchased_length_mm": 10.0,
                "source_occupied_length_mm": 50.8,
                "source_occupied_diameter_mm": 4.0,
            }
        ]
    }
    # A cylinder at the moved station is a distinct patch from the source station.
    surfaces["records"][0]["features"].append(
        cylinder("frame_a/facet007", (0.0, 10.0), origin=(0.0, 1.0, 0.0))
    )
    return surfaces, manifest, source_inventory


class AxisFeatureTests(unittest.TestCase):
    def test_bounded_parallel_cylinder_matches_and_keeps_split_faces(self) -> None:
        surfaces, manifest, inventory = synthetic_inputs()
        report = axis_features.build_report(
            surfaces, manifest, inventory, require_full_inventory=False
        )
        membership = report["source_axis_groups"]["candidate_bolt_axes"]["axes"][0][
            "receiver_memberships"
        ][0]
        self.assertEqual(membership["match_status"], "ambiguous_surface_classification")
        self.assertEqual(membership["matched_feature_ids"], [])
        self.assertIn(
            "coaxial_exterior_surface_rejected",
            {
                row["association_status"]
                for row in membership["cylinder_surface_candidates"]
            },
        )
        self.assertIn(
            "coaxial_surface_classification_ambiguous",
            {
                row["association_status"]
                for row in membership["cylinder_surface_candidates"]
            },
        )
        self.assertNotIn(
            "frame_a/facet005",
            {row["feature_id"] for row in membership["cylinder_surface_candidates"]},
        )

        # Remove ambiguous and exterior possibilities; trimmed faces on one
        # finite bore stay visible as two patches of the same cylinder.
        surfaces["records"][0]["features"] = surfaces["records"][0]["features"][:2]
        report = axis_features.build_report(
            surfaces, manifest, inventory, require_full_inventory=False
        )
        membership = report["source_axis_groups"]["candidate_bolt_axes"]["axes"][0][
            "receiver_memberships"
        ][0]
        self.assertEqual(
            membership["match_status"], "matched_multiple_patches_same_radius_axis"
        )
        self.assertEqual(
            membership["matched_feature_ids"],
            ["frame_a/facet001", "frame_a/facet002"],
        )

    def test_only_bore_like_classification_is_associated(self) -> None:
        surfaces, manifest, inventory = synthetic_inputs()
        surfaces["records"][0]["features"] = [
            cylinder("frame_a/facet001", (-5.0, 5.0), side="exterior_like")
        ]
        report = axis_features.build_report(
            surfaces, manifest, inventory, require_full_inventory=False
        )
        membership = report["source_axis_groups"]["candidate_bolt_axes"]["axes"][0][
            "receiver_memberships"
        ][0]
        self.assertEqual(
            membership["match_status"], "unmatched_no_bore_like_cylinder_patch"
        )
        self.assertEqual(membership["matched_feature_ids"], [])

    def test_parallel_infinite_line_outside_finite_axis_interval_does_not_match(
        self,
    ) -> None:
        surfaces, manifest, inventory = synthetic_inputs()
        surfaces["records"][0]["features"] = [
            cylinder("frame_a/facet001", (20.0, 30.0))
        ]
        report = axis_features.build_report(
            surfaces, manifest, inventory, require_full_inventory=False
        )
        membership = report["source_axis_groups"]["candidate_bolt_axes"]["axes"][0][
            "receiver_memberships"
        ][0]
        self.assertEqual(
            membership["match_status"], "unmatched_patch_outside_finite_interval"
        )
        self.assertEqual(membership["matched_feature_ids"], [])
        self.assertEqual(
            membership["cylinder_surface_candidates"][0]["finite_interval_status"],
            "outside_source_finite_interval",
        )

    def test_near_but_noncoaxial_feature_is_rejected(self) -> None:
        candidates, diagnostics = axis_features._cylinder_candidates(
            {
                "datum_global_xyz_mm": [0.0, 0.0, 0.0],
                "direction_global_xyz": [1.0, 0.0, 0.0],
                "axis_interval_from_datum_mm": [-5.0, 5.0],
                "source_occupied_diameter_mm": None,
            },
            {
                "features": [
                    cylinder(
                        "frame_a/facet999",
                        (-5.0, 5.0),
                        origin=(0.0, 0.001, 0.0),
                    )
                ]
            },
        )
        self.assertEqual(candidates, [])
        self.assertEqual(diagnostics["coaxial_cylinder_features"], 0)

    def test_groups_and_panel_scope_remain_distinct(self) -> None:
        surfaces, manifest, inventory = synthetic_inputs()
        report = axis_features.build_report(
            surfaces, manifest, inventory, require_full_inventory=False
        )
        groups = report["source_axis_groups"]
        self.assertEqual(
            set(groups),
            {
                "candidate_bolt_axes",
                "retained_frame_bolt_axes",
                "panel_kicker_screw_axes",
            },
        )
        self.assertEqual(groups["candidate_bolt_axes"]["axis_count"], 1)
        self.assertEqual(groups["retained_frame_bolt_axes"]["axis_count"], 1)
        self.assertEqual(groups["panel_kicker_screw_axes"]["axis_count"], 1)
        screw = groups["panel_kicker_screw_axes"]["axes"][0]
        self.assertEqual(
            screw["panel_member_reference"]["coverage_status"],
            "outside_44_piece_register_panel_surface_scope",
        )
        self.assertEqual(
            screw["source_axis_fields"]["finite_extent_source_semantics"][
                "historical_proxy_used_for_current_extent"
            ],
            False,
        )
        self.assertEqual(
            screw["panel_axis_station_reconciliation"][
                "source_station_position_status"
            ],
            "owner_moved_from_source_inventory_station",
        )
        self.assertEqual(
            screw["source_axis_fields"]["finite_interval_from_datum_mm"],
            [0.0, 10.0],
        )

    def test_identity_cross_contamination_is_rejected(self) -> None:
        surfaces, manifest, inventory = synthetic_inputs()
        manifest["retained_frame_bolt_axes"][0]["axis_id"] = "candidate_1"
        with self.assertRaisesRegex(ValueError, "cross-contaminate"):
            axis_features.build_report(
                surfaces, manifest, inventory, require_full_inventory=False
            )

    def test_bad_stock_frames_are_rejected(self) -> None:
        surfaces, manifest, inventory = synthetic_inputs()
        scaled = copy.deepcopy(surfaces)
        scaled["records"][0]["stock_frame"]["basis_columns_global_xyz"][0] = [
            2.0,
            0.0,
            0.0,
        ]
        with self.assertRaisesRegex(ValueError, "not unit"):
            axis_features.build_report(
                scaled, manifest, inventory, require_full_inventory=False
            )
        mirrored = copy.deepcopy(surfaces)
        mirrored["records"][0]["stock_frame"]["basis_columns_global_xyz"][0] = [
            -1.0,
            0.0,
            0.0,
        ]
        with self.assertRaisesRegex(ValueError, "right-handed"):
            axis_features.build_report(
                mirrored, manifest, inventory, require_full_inventory=False
            )

    def test_surface_sources_reject_changed_step_or_dependency_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pins = {"pins": {}}
            for name in ("member.step", "producer.py"):
                raw = b"frozen"
                (root / name).write_bytes(raw)
                pins["pins"][name] = {
                    "path": name,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "size_bytes": len(raw),
                }
            axis_features._verify_surface_pin_files(pins, root)
            for name in ("member.step", "producer.py"):
                with self.subTest(source=name):
                    (root / name).write_bytes(b"alterd")  # same byte count
                    with self.assertRaisesRegex(ValueError, "source bytes changed"):
                        axis_features._verify_surface_pin_files(pins, root)
                    (root / name).write_bytes(b"frozen")

    def test_empty_surface_source_pin_map_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "nonempty pin map"):
            axis_features._verify_surface_pin_files({"pins": {}}, Path("."))

    def test_canonical_json_round_trip_is_exact(self) -> None:
        surfaces, manifest, inventory = synthetic_inputs()
        report = axis_features.build_report(
            surfaces, manifest, inventory, require_full_inventory=False
        )
        encoded = axis_features.canonical_json_bytes(report)
        self.assertEqual(
            axis_features.canonical_json_bytes(__import__("json").loads(encoded)),
            encoded,
        )


if __name__ == "__main__":
    unittest.main()
