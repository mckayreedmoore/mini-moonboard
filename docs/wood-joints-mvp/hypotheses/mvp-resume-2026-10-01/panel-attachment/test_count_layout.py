"""Focused checks for the hypothetical count-layout generator."""

from __future__ import annotations

import copy
import json
import unittest

import count_layout


class CountLayoutTests(unittest.TestCase):
    def test_adds_eight_hypothetical_axes_per_main_panel(self):
        source = json.loads(count_layout.MODEL_INPUTS.read_text())
        before = copy.deepcopy(source)
        result = count_layout.build_layout(source)
        self.assertEqual(source, before)
        self.assertEqual(len(result["added_connections"]), 32)
        self.assertEqual(result["comparisons"]["main_panel_screws"], 80)
        self.assertEqual(result["comparisons"]["unchanged_kicker_screws"], 18)
        self.assertEqual(result["comparisons"]["panel_screw_total_in_proposed_input"], 98)
        self.assertEqual(len(result["model_inputs"]["connections"]), len(source["connections"]) + 32)
        self.assertTrue(result["comparisons"]["all_saved_coordinate_aabb_checks_pass"])

        for panel in result["comparisons"]["panels"]:
            self.assertEqual(panel["existing_main_panel_screws"], 12)
            self.assertEqual(panel["added_hypothetical_screws"], 8)
            self.assertEqual(panel["proposed_main_panel_screws"], 20)
            self.assertEqual(panel["added_vertical"], 4)
            self.assertEqual(panel["added_horizontal"], 4)
            self.assertEqual(panel["hypothetical_front_origins_inside_panel_aabb"], 8)
            self.assertEqual(panel["hypothetical_interface_points_inside_receiver_aabb"], 8)

    def test_additions_keep_named_template_direction_and_receiver_without_inheriting_screen(self):
        result = count_layout.build_layout()
        source_by_id = {axis["axis_id"]: axis for axis in json.loads(count_layout.MODEL_INPUTS.read_text())["connections"]}
        for addition in result["added_connections"]:
            template = source_by_id[addition["template_axis_id"]]
            self.assertTrue(addition["source_record"]["hypothetical"])
            self.assertFalse(addition["mechanical_attachment_defined"])
            self.assertEqual(addition["axis_xyz"], template["axis_xyz"])
            self.assertEqual(addition["receiver_member_ids"], template["receiver_member_ids"])
            self.assertEqual(addition["source_record"]["receiver_member"], template["source_record"]["receiver_member"])
            self.assertEqual(addition["source_record"]["derived_from_axis_id"], template["axis_id"])
            self.assertFalse(addition["source_record"]["receiver_screen"].get("finished_receiver_axis_envelope_clear", False))
            self.assertEqual(addition["source_record"]["saved_coordinate_screen"]["screen_limit"],
                             "AABB only; not a B-rep intersection or installation-clearance check")

    def test_horizontal_insertions_stay_on_the_actual_rail_row(self):
        result = count_layout.build_layout()
        source_by_id = {axis["axis_id"]: axis for axis in json.loads(count_layout.MODEL_INPUTS.read_text())["connections"]}
        for addition in result["added_connections"]:
            if addition["hypothetical_edge_role"] not in ("edge", "service"):
                continue
            template = source_by_id[addition["template_axis_id"]]
            self.assertEqual(addition["source_point_xyz_mm"][1:], template["source_point_xyz_mm"][1:])


if __name__ == "__main__":
    unittest.main()
