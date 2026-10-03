"""Focused checks for mirrored hypothetical horizontal screw placement."""

from __future__ import annotations

import copy
import json
import unittest

import count_layout
import count_mirrored_layout


def _parameter(row, tangent):
    return sum(a * b for a, b in zip(row["source_point_xyz_mm"], tangent))


def _closest_at_parameter(rows, target, tangent):
    return min(rows, key=lambda row: abs(_parameter(row, tangent) - target))


class MirroredCountLayoutTests(unittest.TestCase):
    def test_mirrors_outer_and_middle_gap_choices_without_changing_source(self):
        source = json.loads(count_layout.MODEL_INPUTS.read_text())
        before = copy.deepcopy(source)
        original = count_layout.build_layout(source)
        result = count_mirrored_layout.build_layout(source)
        self.assertEqual(source, before)
        self.assertEqual(len(result["added_connections"]), 32)
        self.assertEqual(result["comparisons"]["main_panel_screws"], 80)
        self.assertEqual(result["comparisons"]["panel_screw_total_in_proposed_input"], 98)
        self.assertEqual(len(result["comparisons"]["mirrored_horizontal_adjustments"]), 4)
        self.assertTrue(result["comparisons"]["all_saved_coordinate_aabb_checks_pass"])
        source_by_id = {axis["axis_id"]: axis for axis in source["connections"]}
        final_by_id = {axis["axis_id"]: axis for axis in result["model_inputs"]["connections"]}
        for axis_id, axis in source_by_id.items():
            self.assertEqual(final_by_id[axis_id], axis)

        original_by_id = {axis["axis_id"]: axis for axis in original["added_connections"]}
        mirrored_by_id = {axis["axis_id"]: axis for axis in result["added_connections"]}
        for panel in ("main_lower_left", "main_upper_left"):
            for rail in ("edge", "service"):
                for gap in (1, 2):
                    axis_id = f"hyp20_{panel}_{rail}_gap_{gap}"
                    self.assertEqual(mirrored_by_id[axis_id], original_by_id[axis_id])

        for panel in ("main_lower_right", "main_upper_right"):
            for rail in ("edge", "service"):
                old_id = f"hyp20_{panel}_{rail}_gap_1"
                middle_id = f"hyp20_{panel}_{rail}_gap_2"
                outer_id = f"hyp20_{panel}_{rail}_gap_3"
                self.assertNotIn(old_id, mirrored_by_id)
                self.assertEqual(mirrored_by_id[middle_id], original_by_id[middle_id])
                addition = mirrored_by_id[outer_id]
                change = next(
                    row for row in result["comparisons"]["mirrored_horizontal_adjustments"]
                    if row["old_axis_id"] == old_id
                )
                self.assertAlmostEqual(change["old_x_mm"], 252.5375, places=6)
                self.assertAlmostEqual(addition["source_point_xyz_mm"][0], 1016.025, places=6)
                self.assertEqual(addition["template_axis_id"], f"round_panel_{panel.removeprefix('main_')}_{rail}_2")
                self.assertEqual(addition["source_point_xyz_mm"][1:], addition["source_record"]["origin_global_xyz_mm"][1:])
                self.assertEqual(addition["hypothetical_gap_index"], 3)

    def test_horizontal_midpoints_are_midpoints_of_the_normalized_outer_and_middle_gaps(self):
        result = count_mirrored_layout.build_layout()
        input_connections = result["model_inputs"]["connections"]
        source_axes = {
            row["axis_id"]: row for row in input_connections
            if row.get("kind") == "panel_screw" and not row.get("hypothetical_layout")
        }
        additions = {
            row["axis_id"]: row for row in result["added_connections"]
            if row["hypothetical_edge_role"] in ("edge", "service")
        }
        for panel in count_layout.MAIN_PANELS:
            panel_key = panel.removeprefix("main_")
            for rail_role in ("edge", "service"):
                rail_point = source_axes[f"round_panel_{panel_key}_{rail_role}_1"]["source_point_xyz_mm"]
                tangent_start = source_axes[f"round_panel_{panel_key}_center_1"]["source_point_xyz_mm"]
                tangent_end = source_axes[f"round_panel_{panel_key}_center_4"]["source_point_xyz_mm"]
                tangent = [tangent_end[i] - tangent_start[i] for i in range(3)]
                norm = sum(value * value for value in tangent) ** 0.5
                tangent = [value / norm for value in tangent]
                rim_rows = [source_axes[f"round_panel_{panel_key}_rim_{i}"] for i in range(1, 5)]
                center_rows = [source_axes[f"round_panel_{panel_key}_center_{i}"] for i in range(1, 5)]
                rail_t = sum(a * b for a, b in zip(rail_point, tangent))
                corners = [
                    _closest_at_parameter(group, rail_t, tangent)
                    for group in (rim_rows, center_rows)
                ]
                rail_pair = [source_axes[f"round_panel_{panel_key}_{rail_role}_{i}"] for i in (1, 2)]
                stations = sorted([*corners, *rail_pair], key=lambda row: row["source_point_xyz_mm"][0])
                xs = [row["source_point_xyz_mm"][0] for row in stations]
                rim_is_left = corners[0]["source_point_xyz_mm"][0] == xs[0]
                outer_gap = 0 if rim_is_left else 2
                gap_indices = (outer_gap + 1, 2) if panel.endswith("_left") else (2, outer_gap + 1)
                for gap in gap_indices:
                    addition = additions[f"hyp20_{panel}_{rail_role}_gap_{gap}"]
                    left_x, right_x = xs[gap - 1], xs[gap]
                    normalized = (addition["source_point_xyz_mm"][0] - left_x) / (right_x - left_x)
                    self.assertAlmostEqual(normalized, 0.5, places=10)

        source_ids = {row["axis_id"] for row in source_axes.values()}
        final_ids = {row["axis_id"] for row in input_connections}
        self.assertTrue(source_ids <= final_ids)


if __name__ == "__main__":
    unittest.main()
