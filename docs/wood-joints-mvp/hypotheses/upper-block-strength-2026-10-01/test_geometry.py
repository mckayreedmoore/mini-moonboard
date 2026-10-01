"""Focused checks for source pins, axis consistency, and exact section cuts."""

from __future__ import annotations

import math
import unittest

import cadquery as cq
from geometry import (
    InventoryError,
    _section_components,
    build_inventory,
    load_pinned_sources,
)


class GeometryInventoryTests(unittest.TestCase):
    def test_corrupt_source_bytes_fail_the_pin_before_json_parse(self) -> None:
        with self.assertRaisesRegex(InventoryError, "source hash mismatch"):
            load_pinned_sources({"upper_outer_and_center": b"{"})

    def test_action_axis_must_exist_in_the_pinned_geometry_map(self) -> None:
        documents = load_pinned_sources()
        documents[0].data["bolt_actions"][0]["axis_id"] = "missing-axis"
        with self.assertRaisesRegex(InventoryError, "action references absent geometry axis"):
            build_inventory(documents, verify_step_files=False, extract_sections=False)

    def test_transverse_bore_section_matches_known_cube_answer(self) -> None:
        cube = cq.Workplane("XY").box(20.0, 30.0, 20.0).val()
        transverse_bore = cq.Solid.makeCylinder(
            2.0,
            20.0,
            cq.Vector(-10.0, 0.0, 0.0),
            cq.Vector(1.0, 0.0, 0.0),
        )
        drilled = cube.cut(transverse_bore)
        self.assertTrue(drilled.isValid())
        self.assertEqual(len(drilled.Solids()), 1)

        at_bore = _section_components(drilled, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        between_bore_stations = _section_components(
            drilled, (0.0, 0.0, 5.0), (0.0, 0.0, 1.0)
        )
        self.assertTrue(math.isclose(at_bore["area_mm2"], 520.0, abs_tol=1e-7))
        self.assertEqual(at_bore["material_component_count"], 2)
        self.assertEqual(at_bore["section_face_count"], 2)
        self.assertTrue(
            math.isclose(between_bore_stations["area_mm2"], 600.0, abs_tol=1e-7)
        )
        self.assertEqual(between_bore_stations["material_component_count"], 1)

    def test_replay_keeps_pure_direction_and_actual_vector_dispositions_separate(self) -> None:
        report = build_inventory(load_pinned_sources())
        self.assertEqual(
            report["counts"],
            {
                "blocks": 8,
                "physical_bolt_axes": 32,
                "sampled_bolt_action_states": 672,
                "block_host_member_direction_rows": 64,
                "two_bolt_block_host_groups": 16,
                "hash_verified_unique_member_step_sources": 15,
                "exact_block_solid_section_samples": 40,
            },
        )

        directions = {
            (row["block"], row["member_role"], row["axis_id"]): row
            for row in report["member_direction_inventory"]
        }
        self.assertFalse(
            any(
                row["conditional_pure_direction_geometry_comparators"]["cross_grain_loaded_edge"]["shorter_than_conditional_reference"]
                for row in report["member_direction_inventory"]
            )
        )
        left_axis = "top_outer/clip_single_top_left_1/side_2"
        left_block = directions[("top_outer_left_cleat", "block", left_axis)]
        left_host = directions[("top_outer_left_cleat", "host", left_axis)]
        self.assertEqual(
            left_block["conditional_pure_direction_geometry_comparators"]["grain_parallel_loaded_end"]["conditional_7D_reference_mm"],
            44.45,
        )
        self.assertEqual(
            left_block["sampled_actual_lateral_vector_envelope"]["states_with_nonzero_grain_and_cross_grain_components"],
            21,
        )
        self.assertEqual(
            left_block["sampled_actual_lateral_vector_envelope"]["actual_vector_applicability"],
            left_host["sampled_actual_lateral_vector_envelope"]["actual_vector_applicability"],
        )
        self.assertLess(
            left_block["sampled_actual_lateral_vector_envelope"]["unsigned_angle_to_grain_max_degrees"],
            10.0,
        )
        self.assertGreater(
            left_host["sampled_actual_lateral_vector_envelope"]["unsigned_angle_to_grain_min_degrees"],
            80.0,
        )

        sections = {row["block"]: row for row in report["block_exact_sections"]}
        outer_left = sections["top_outer_left_cleat"]["sampled_sections"]
        self.assertEqual(len(outer_left), 5)
        center_station = outer_left[2]
        self.assertEqual(len(center_station["station_axis_ids"]), 2)
        self.assertEqual(center_station["material_component_count"], 3)
        self.assertTrue(math.isclose(center_station["area_mm2"], 6569.71, abs_tol=1e-6))
        midpoint = outer_left[1]
        self.assertEqual(midpoint["sample_kind"], "between_adjacent_bolt_stations")
        self.assertFalse(midpoint["continuous_between_samples_inferred"])
        self.assertTrue(math.isclose(midpoint["area_mm2"], 7903.21, abs_tol=1e-6))
        self.assertFalse(report["complete_joint_resistance_established"])


if __name__ == "__main__":
    unittest.main()
