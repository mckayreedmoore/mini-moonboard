"""Known answers for the small unilateral-contact and clearance model."""

import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("working_scenario", Path(__file__).with_name("working_scenario.py"))
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class WorkingScenarioKnownAnswers(unittest.TestCase):
    def test_axial_tension_uses_bolts_and_opens_faces(self):
        motion, bolts, faces = s.normal_response(
            [[1, 0, -1], [1, 0, 1]],
            [[1, -2, -2], [1, -2, 2], [1, 2, -2], [1, 2, 2]],
            1, [1] * 4, [-20, 0, 0])
        self.assertAlmostEqual(motion[0], 10)
        self.assertEqual(bolts, [10, 10])
        self.assertEqual(faces, [0, 0, 0, 0])

    def test_compression_uses_faces_and_releases_bolts(self):
        motion, bolts, faces = s.normal_response(
            [[1, 0, -1], [1, 0, 1]],
            [[1, -2, -2], [1, -2, 2], [1, 2, -2], [1, 2, 2]],
            1, [1] * 4, [20, 0, 0])
        self.assertAlmostEqual(motion[0], -5)
        self.assertEqual(bolts, [0, 0])
        self.assertEqual(faces, [5, 5, 5, 5])

    def test_parallel_shear_includes_clearance(self):
        motion, forces = s.shear_response(20, 0, 0, 2, 100, 0.5)
        self.assertAlmostEqual(motion[0], -0.6)
        self.assertAlmostEqual(motion[1], 0)
        self.assertAlmostEqual(motion[2], 0)
        self.assertAlmostEqual(forces[0][0], 10)
        self.assertAlmostEqual(forces[1][0], 10)

    def test_pure_face_torque_has_opposed_bolt_forces(self):
        motion, forces = s.shear_response(0, 0, 20, 2, 100, 0)
        self.assertEqual(forces, [[0, -10], [0, 10]])
        self.assertAlmostEqual(motion[2], -0.1)


if __name__ == "__main__":
    unittest.main()
