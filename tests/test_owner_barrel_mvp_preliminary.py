"""Current outward-post source geometry and historical-demand separation."""

import math
import unittest

from scripts.owner_barrel_mvp_preliminary import _historical_scale, report


class PreliminaryBarrelAssessmentTest(unittest.TestCase):
    def test_current_two_joint_assembly_stays_unrated(self):
        result = report()
        rail = result["joints"]["outer_rail"]
        header = result["joints"]["outer_header_post"]
        self.assertEqual(rail["station"], "clip_horizontal_lower_right_2")
        self.assertEqual(header["station"], "clip_timber_header_outer_right")
        self.assertAlmostEqual(rail["row_spacing_mm"], 32.25, places=3)
        self.assertAlmostEqual(header["row_spacing_mm"], 50, places=3)
        self.assertAlmostEqual(rail["barrel_center_to_grain_end_mm"], 60, places=3)
        self.assertAlmostEqual(header["barrel_center_to_grain_end_mm"], 70, places=3)
        self.assertAlmostEqual(
            header["rows"][0]["tip_past_barrel_far_wall_mm"], 18.8962, places=3
        )
        # The later header-bore depth revision leaves nominal tip clearance.
        self.assertEqual(header["rows"][0]["tip_to_bore_cap_mm"], 4)
        for joint in (rail, header):
            self.assertEqual(len(joint["rows"]), 2)
            self.assertAlmostEqual(joint["shaft_diameter_mm"], 6.35)
            self.assertAlmostEqual(joint["barrel_body_diameter_mm"], 10.0076)
            self.assertAlmostEqual(joint["washer_outer_diameter_mm"], 25.4)
            self.assertAlmostEqual(
                joint["stiffness"]["centered_7p5_vs_6p35_radial_clearance_mm"],
                0.575,
            )
            self.assertIsNone(joint["actual_barrel_joint_demand_n"])
            self.assertIsNone(joint["complete_joint_capacity_n"])
            self.assertIsNone(joint["pass"])
            self.assertIsNone(
                joint["stiffness"]["complete_axial_or_lateral_joint_stiffness_n_per_mm"]
            )
            self.assertGreater(
                joint["conditional_wood"][
                    "ideal_full_contact_washer_fc_perp_n_per_bolt"
                ],
                0,
            )
            self.assertGreater(
                joint["conditional_wood"]["two_slot_net_parallel_tension_reference_n"],
                0,
            )
            self.assertAlmostEqual(
                joint["conditional_wood"][
                    "ideal_full_contact_washer_fc_perp_n_per_bolt"
                ],
                1993.1400,
                places=2,
            )
        self.assertFalse(result["structural_released"])

    def test_historical_scale_keeps_force_and_moment_in_same_case(self):
        def case(force, moment):
            return {
                "angles": {
                    "station": {
                        "flanges": {
                            "beam": {"force_norm_n": force, "moment_norm_nmm": moment}
                        }
                    }
                }
            }

        payload = {
            "candidate": "compact-floor-flush-development",
            "case_order": ["high-force", "high-moment"],
            "cases": {"high-force": case(100, 0), "high-moment": case(0, 3000)},
        }
        scale = _historical_scale("station", 50, payload)
        self.assertEqual(scale["case"], "high-moment")
        self.assertTrue(math.isclose(scale["ideal_pair_one_row_n"], 60))
        self.assertNotEqual(scale["ideal_pair_one_row_n"], 110)


if __name__ == "__main__":
    unittest.main()
