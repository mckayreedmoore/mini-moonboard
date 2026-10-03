"""Focused known answers for neutral normal motion and common-datum motion."""

import unittest

import numpy as np
import study
from normal_model import minimum_norm_feasible, normal_response

BOLTS = [[1, 0, -1], [1, 0, 1]]
PATCHES = [[1, -2, -2], [1, -2, 2], [1, 2, -2], [1, 2, 2]]


class NormalMotionChecks(unittest.TestCase):
    def test_pure_tension_reports_neutral_tilt_and_selects_zero_tilt(self):
        result = normal_response(BOLTS, PATCHES, 1, [1] * 4, [-20, 0, 0])
        np.testing.assert_allclose(result["motion_mm_rad_rad"], [10, 0, 0], atol=1e-12)
        np.testing.assert_allclose(result["tension_n"], [10, 10], atol=1e-12)
        np.testing.assert_allclose(result["compression_n"], [0] * 4, atol=1e-12)
        self.assertEqual(result["force_bearing_stiffness_rank"], 2)
        self.assertEqual(result["zero_force_touching_contacts"], 0)
        self.assertFalse(result["motion_uniqueness_established"])
        mode = np.asarray(result["neutral_mode_basis_mm_rad_rad_per_mm"][0])
        interval = result["one_neutral_mode_parameter_interval_mm"]
        endpoints = sorted(mode[1] * parameter for parameter in interval)
        np.testing.assert_allclose(endpoints, [-5, 5], atol=1e-12)

    def test_alternate_pure_tension_tilt_has_same_forces(self):
        motion = np.array([10, 3, 0])
        opening = np.asarray(BOLTS + PATCHES) @ motion
        self.assertTrue(np.all(opening[2:] > 0))
        traction = np.asarray(BOLTS).T @ (-opening[:2])
        np.testing.assert_allclose(traction, [-20, 0, 0])

    def test_permuting_contacts_does_not_choose_different_free_tilt(self):
        normal = normal_response(BOLTS, PATCHES, 1, [1] * 4, [-20, 0, 0])
        reversed_result = normal_response(BOLTS, PATCHES[::-1], 1, [1] * 4, [-20, 0, 0])
        np.testing.assert_allclose(normal["motion_mm_rad_rad"], reversed_result["motion_mm_rad_rad"], atol=1e-12)

    def test_compression_has_four_force_bearing_contacts(self):
        result = normal_response(BOLTS, PATCHES, 1, [1] * 4, [20, 0, 0])
        np.testing.assert_allclose(result["motion_mm_rad_rad"], [-5, 0, 0], atol=1e-12)
        np.testing.assert_allclose(result["tension_n"], [0, 0], atol=1e-12)
        np.testing.assert_allclose(result["compression_n"], [5] * 4, atol=1e-12)
        self.assertEqual(result["force_bearing_stiffness_rank"], 3)
        self.assertTrue(result["motion_uniqueness_established"])

    def test_unloaded_contacts_do_not_gain_force_bearing_stiffness(self):
        result = normal_response(BOLTS, PATCHES, 1, [1] * 4, [0, 0, 0])
        np.testing.assert_allclose(result["motion_mm_rad_rad"], [0, 0, 0], atol=1e-12)
        self.assertEqual(result["force_bearing_stiffness_rank"], 0)
        self.assertEqual(result["zero_force_touching_contacts"], 4)

    def test_corner_projection_handles_two_neutral_coordinates(self):
        base = np.array([1.0, 0, 0])
        basis = np.array([[0.0, 0], [1, 0], [0, 1]])
        constraints = np.array([[-1.0, 1, 0], [-2, 0, 1]])
        result = minimum_norm_feasible(base, basis, constraints)
        np.testing.assert_allclose(result, [1, 1, 2], atol=1e-12)

    def test_mixed_load_returns_the_forces_of_its_returned_motion(self):
        result = normal_response(BOLTS, PATCHES, 10, [30] * 4, [-15, 8, 12])
        opening = np.asarray(BOLTS + PATCHES) @ result["motion_mm_rad_rad"]
        tensions = 10 * np.maximum(opening[:2], 0)
        compression = 30 * np.maximum(-opening[2:], 0)
        np.testing.assert_allclose(tensions, result["tension_n"], atol=1e-10)
        np.testing.assert_allclose(compression, result["compression_n"], atol=1e-10)
        recovered = np.asarray(BOLTS + PATCHES).T @ np.r_[-tensions, compression]
        np.testing.assert_allclose(recovered, [-15, 8, 12], atol=1e-10)


class CommonDatumChecks(unittest.TestCase):
    def test_rotation_translation_has_correct_cross_product_sign(self):
        result = study.motion_at_point([1, 2, 3], [0, 0, 0.1], [0, 0, 0], [10, 0, 0])
        np.testing.assert_allclose(result, [1, 3, 3])

    def test_local_motion_components_rejoin_global_vectors(self):
        translation, rotation = study.global_motion([1, 0.2, 0.3], [4, 5, 0.6],
                                                     [1, 0, 0], [0, 1, 0], [0, 0, 1])
        np.testing.assert_allclose(translation, [4, 5, 1])
        np.testing.assert_allclose(rotation, [0.2, 0.3, 0.6])

    def test_same_motion_at_different_datums_cancels_at_common_point(self):
        rotation = [0, 0, 0.1]
        common = [10, 0, 0]
        rail = study.motion_at_point([1, 0, 0], rotation, [0, 0, 0], common)
        side = study.motion_at_point([1, 1, 0], rotation, [10, 0, 0], common)
        translation, relative_rotation = study.relative_host_motion((rail, rotation), (side, rotation))
        np.testing.assert_allclose(translation, [0, 0, 0])
        np.testing.assert_allclose(relative_rotation, [0, 0, 0])

    def test_host_relative_sign_is_opposite_cleat_relative_sign(self):
        translation, rotation = study.relative_host_motion(([1, 0, 0], [0.1, 0, 0]),
                                                         ([0, 2, 0], [0, 0.2, 0]))
        np.testing.assert_allclose(translation, [-1, 2, 0])
        np.testing.assert_allclose(rotation, [-0.1, 0.2, 0])


class SavedSourceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.original, old, cls.responses, _, _ = study.inputs()
        cls.budget = old["assumed_local_contract"]["per_bolt_lateral_limit_n"] / old["component_scenario"][
            "force_box_to_worst_direction_reference_budget_ratio"]
        cls.baseline = study.evaluate(1.15, 300, 1, cls.source, cls.responses, cls.budget)

    def test_all_saved_baseline_motions_have_real_full_rank_and_match_previous(self):
        before = {(r["case"], r["increment_index"], r["receiver"]): r
                  for r in self.original["receiver_states"]}
        self.assertEqual(len(self.baseline["receiver_states"]), 42)
        self.assertEqual(len(self.baseline["both_host_states"]), 21)
        for row in self.baseline["receiver_states"]:
            old = before[row["case"], row["increment_index"], row["receiver"]]
            self.assertEqual(row["normal"]["force_bearing_stiffness_rank"], 3)
            self.assertTrue(row["normal"]["motion_uniqueness_established"])
            np.testing.assert_allclose(row["normal"]["motion_mm_rad_rad"],
                                       old["normal_motion_mm_rad_rad"], rtol=0, atol=1e-10)
            np.testing.assert_allclose(row["shear_motion_mm_mm_rad"],
                                       old["shear_motion_mm_mm_rad"], rtol=0, atol=1e-10)

    def test_clearance_changes_spin_without_changing_normal_motion(self):
        zero = study.evaluate(0, 300, 1, self.source, self.responses, self.budget)
        for z, b in zip(zero["receiver_states"], self.baseline["receiver_states"], strict=True):
            np.testing.assert_allclose(z["normal"]["motion_mm_rad_rad"], b["normal"]["motion_mm_rad_rad"], atol=1e-12)
        self.assertLess(zero["maxima"]["face_spin_degrees"], 0.1)
        self.assertGreater(self.baseline["maxima"]["face_spin_degrees"], 3.6)


if __name__ == "__main__":
    unittest.main()
