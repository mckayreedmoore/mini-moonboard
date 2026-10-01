"""Known geometry answers and changed-source rejection checks; no native solve."""

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("bottom_placement_test", Path(__file__).with_name("produce.py"))
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class PlacementChecks(unittest.TestCase):
    def setUp(self):
        document = json.loads(p.FEATURES.read_text())
        self.axis = next(a for a in document["source_axis_groups"]["candidate_bolt_axes"]["axes"]
                         if a["axis_id"] == p.PREFIX+"side_1")
        self.membership = next(r for r in self.axis["receiver_memberships"] if r["receiver_member_id"] == p.CLEAT)

    def test_actual_axis_reconciles(self):
        row = p.checked_membership(self.axis, self.membership)
        self.assertAlmostEqual(row["stock_center_to_boundary_mm"]["e-"], 28, places=6)
        self.assertAlmostEqual(row["stock_center_to_boundary_mm"]["e+"], 60.9, places=6)

    def test_datum_corruption_rejected(self):
        membership = copy.deepcopy(self.membership)
        membership["axis_in_stock_frame"]["datum_stock_gqr_mm"][1] += 1
        with self.assertRaisesRegex(ValueError, "datum differs"):
            p.checked_membership(self.axis, membership)

    def test_direction_corruption_rejected(self):
        membership = copy.deepcopy(self.membership)
        membership["axis_in_stock_frame"]["direction_stock_gqr"][2] *= -1
        with self.assertRaisesRegex(ValueError, "axis differs"):
            p.checked_membership(self.axis, membership)

    def test_ambiguous_bore_rejected(self):
        membership = copy.deepcopy(self.membership)
        membership["matched_feature_ids"].append("invented/bore")
        with self.assertRaisesRegex(ValueError, "ambiguous finished bore"):
            p.checked_membership(self.axis, membership)

    def test_wrong_diameter_rejected(self):
        axis = copy.deepcopy(self.axis)
        axis["source_axis_fields"]["occupied_diameter_mm"] = 7.5
        with self.assertRaisesRegex(ValueError, "diameter scenario differs"):
            p.checked_membership(axis, self.membership)

    def test_nonorthogonal_frame_rejected(self):
        membership = copy.deepcopy(self.membership)
        membership["stock_frame"]["basis_columns_global_xyz"][1] = membership["stock_frame"]["basis_columns_global_xyz"][0]
        with self.assertRaisesRegex(ValueError, "not orthonormal"):
            p.checked_membership(self.axis, membership)

    def test_frozen_input_corruption_rejected_before_cad(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory)/"joint.json"
            bad.write_text('{"joint_accepted":true}')
            with self.assertRaisesRegex(ValueError, "frozen input changed"):
                p.produce(bad)

    def test_uncertain_sign_not_loaded_edge(self):
        self.assertEqual(p.resolved_sign(1e-8, 2e-8), "unresolved")
        self.assertEqual(p.resolved_sign(-3e-8, 2e-8), "negative")
        with self.assertRaisesRegex(ValueError, "rounding radii"):
            p.radius_project([1, -1, 1], [[1, 0, 0]]*3)

    def test_distinct_axial_endpoints_preserved(self):
        action = {"first": "a", "second": "b", "point": [1, 0, 0],
                  "first_point": [1, 0, 0], "second_point": [1, 0, 20],
                  "force_on_first_xyz_n": [0, 0, 5], "force_on_second_xyz_n": [0, 0, -5],
                  "force_rounding_radius_xyz_n": [0, 0, .1]}
        self.assertEqual(p.action_on_member(action, "b"), ([0, 0, -5], [0, 0, .1], [1, 0, 20]))
        action["force_on_second_xyz_n"][2] = 5
        with self.assertRaisesRegex(ValueError, "not reciprocal"):
            p.action_on_member(action, "b")


class FinishedRayAnswers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import cadquery as cq

        from mini_moonboard.connection_geometry import material_intervals

        cls.cq = cq
        cls.intervals = staticmethod(material_intervals)
        cls.shape = cq.Workplane("XY").box(50, 20, 30, centered=(False, False, False)).val()
        for x in (10, 30):
            cls.shape = cls.shape.cut(cq.Solid.makeCylinder(3.75, 20, cq.Vector(x, 0, 15), cq.Vector(0, 1, 0)))
        cls.record = {"member_id": "known_box", "bore_axis_interval_from_datum_mm": [5, 25],
                      "axis_datum_xyz_mm": [10, -5, 15], "axis_direction_xyz": [0, 1, 0],
                      "grain_direction_xyz": [1, 0, 0], "edge_direction_xyz": [0, 0, 1],
                      "bore_radius_mm": 3.75,
                      "stock_center_to_boundary_mm": {"g-": 10, "g+": 40, "e-": 15, "e+": 15}}

    def test_neighbor_bore_preserved_without_shortening_exterior_distance(self):
        rays = p.finished_rays(self.record, self.shape, self.intervals)
        self.assertEqual(len(rays), 12)
        self.assertTrue(all(r["terminal_matches_stock_boundary"] for r in rays))
        row = next(r for r in rays if r["station"] == "mid_depth" and r["ray"] == "g+")
        for actual, expected in zip(row["material_intervals_mm"], [(3.75, 16.25), (23.75, 40)], strict=True):
            for a, b in zip(actual, expected, strict=True):
                self.assertAlmostEqual(a, b, places=6)
        self.assertEqual(row["void_intervals_mm"], [[0, 3.75], [16.25, 23.75]])
        self.assertFalse(row["continuous_depth_extrema_proved"])

    def test_finished_end_cut_does_not_receive_stock_length(self):
        cut = self.cq.Workplane("XY").box(10, 20, 30, centered=(False, False, False)).translate((45, 0, 0)).val()
        rays = p.finished_rays(self.record, self.shape.cut(cut), self.intervals)
        rows = [r for r in rays if r["ray"] == "g+"]
        self.assertTrue(all(not r["terminal_matches_stock_boundary"] for r in rows))
        self.assertTrue(all(abs(r["center_to_last_material_exit_mm"]-35) < 1e-6 for r in rows))


if __name__ == "__main__":
    unittest.main()
