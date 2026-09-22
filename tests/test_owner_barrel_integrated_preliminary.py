"""Current integrated barrel layout: conditional components, not a joint rating."""

import unittest

from scripts.owner_barrel_integrated_preliminary import report


class IntegratedPreliminaryTest(unittest.TestCase):
    def test_current_rail_and_center_are_source_bound_and_unrated(self):
        result = report()
        self.assertEqual(result["geometry_source"], "integrated_viewer_assembly")
        self.assertEqual(result["modeled_barrel_pairs"], 46)
        self.assertEqual(result["former_angle_duties"], 24)
        self.assertEqual(result["fixed_panel_kicker_screws"], 66)
        self.assertEqual(result["retained_frame_bolts"], 12)
        rail = result["joints"]["lower_outer_rail"]
        center = result["joints"]["center_principal_header"]
        outer_headers = [
            result["joints"][f"outer_header_{side}"] for side in ("left", "right")
        ]
        self.assertEqual(rail["station"], "clip_horizontal_lower_right_2")
        self.assertEqual(center["station"], "clip_split_base_center_right")
        self.assertEqual(len(rail["rows"]), 2)
        self.assertEqual(len(center["rows"]), 1)
        for side, joint in zip(("left", "right"), outer_headers, strict=True):
            self.assertEqual(joint["station"], f"clip_timber_header_outer_{side}")
            self.assertEqual(len(joint["rows"]), 2)
            self.assertAlmostEqual(joint["row_spacing_mm"], 50.0, places=3)
            self.assertGreater(joint["trial_cut_face_area_mm2"], 0)
            self.assertLess(
                joint["trial_cut_face_area_mm2"],
                joint["gross_face_contact_area_mm2"],
            )
            self.assertAlmostEqual(
                joint["counterbore_min_radial_edge_stock_mm"], 6.35, places=2
            )
            self.assertIn(
                "Mx/row_spacing_mm",
                joint["ideal_equal_stiffness_pair_axial_row_action"],
            )
            self.assertNotIn("historical_bracket_two_point_scale_only", joint)
            self.assertIsNone(joint["actual_barrel_joint_demand_n"])
            self.assertFalse(joint["rim_first_assembly_sequence_verified"])
            self.assertIsNone(joint["actual_new_topology_demand_n"])
            self.assertIsNone(joint["complete_joint_capacity_n"])
            self.assertIsNone(joint["complete_joint_stiffness_n_per_mm"])
        self.assertNotIn("historical_bracket_two_point_scale_only", rail)
        self.assertAlmostEqual(rail["row_spacing_mm"], 32.25, places=3)
        self.assertAlmostEqual(rail["gross_face_contact_area_mm2"], 5322.57, places=2)
        self.assertAlmostEqual(rail["trial_cut_face_area_mm2"], 5234.213, places=2)
        self.assertAlmostEqual(center["rows"][0]["nominal_length_mm"], 114.3)
        self.assertAlmostEqual(
            center["barrel_body_ligament_to_nearest_x_edge_mm"], 14.046, places=2
        )
        self.assertAlmostEqual(center["head_pocket_edge_stock_mm"], 2.092, places=2)
        face = center["gross_contact_geometry"]
        self.assertAlmostEqual(face["area_mm2"], 5113.122, places=2)
        self.assertAlmostEqual(face["trial_cut_area_mm2"], 5055.451, places=2)
        self.assertEqual(face["cell_count"], 16)
        self.assertAlmostEqual(face["bolt_rearward_of_centroid_mm"], 50.907, places=2)
        self.assertAlmostEqual(face["rear_edge_margin_from_bolt_mm"], 16.195, places=2)
        self.assertAlmostEqual(
            face["front_edge_margin_from_bolt_mm"], 118.008, places=2
        )
        self.assertAlmostEqual(face["bolt_axis_normal_projection_abs"], 0.766, places=3)
        self.assertAlmostEqual(face["trial_cut_rear_strip_area_mm2"], 588.18, places=2)
        self.assertGreater(
            center["conditional_wood"]["ideal_full_contact_washer_fc_perp_n"], 0
        )
        self.assertGreater(center["stiffness"]["steel_only_ea_over_length_n_per_mm"], 0)
        self.assertIsNone(center["single_fastener_free_moment_resistance_nmm"])
        for joint in (rail, center, *outer_headers):
            self.assertIsNone(joint["actual_new_topology_demand_n"])
            self.assertIsNone(joint["complete_joint_capacity_n"])
            self.assertIsNone(joint["complete_joint_stiffness_n_per_mm"])
        self.assertFalse(result["structural_released"])


if __name__ == "__main__":
    unittest.main()
