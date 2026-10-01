"""Exercise meaningful corruptions of the real frozen contact source join."""

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("bottom_join_test", HERE / "produce.py")
producer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = producer
spec.loader.exec_module(producer)


class FrozenContactSourceGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.final = producer.load(producer.OLD, producer.OLD_SHA, "bottom_guard_prior")
        shared = cls.final.load_module("bottom_guard_shared", cls.final.DEMAND_PATH,
                                      cls.final.PINS["remaining_demand_producer"][1])
        producer.require(producer.sha(shared.FREEZE) == shared.FREEZE_SHA, "freeze changed")
        freeze = json.loads(shared.FREEZE.read_text())
        files = freeze["cases"]["a1-rear"]
        for pin in files.values():
            producer.require(producer.sha(producer.ROOT / pin["path"]) == pin["sha256"],
                             "case source changed")
        model = json.loads((producer.ROOT / files["model"]["path"]).read_text())
        response = json.loads((producer.ROOT / files["response"]["path"]).read_text())
        name = "contact_58_0"
        cell = next(row for row in model["contact_cell_ownership"] if row["name"] == name)
        binding = next(row for row in model["unilateral_springa_bindings"] if row["name"] == name)
        inc = response["increments"][-1]
        component = next(row for row in inc["springa_components"]
                         if row["source_row_id"] == binding["source_row_id"])
        cls.source = (cell, inc["physical_connection_forces"][name], binding, component,
                      model["raw_source_carrier_law_inventory_rows"])
        tie_name = "bottom_outer/clip_horizontal_bottom_left_1/side_1/outer-seat-axial-tie"
        tie_binding = next(row for row in model["unilateral_springa_bindings"] if row["name"] == tie_name)
        cls.tie_source = (inc["physical_connection_forces"][tie_name],
                          next(row for row in inc["springa_components"]
                               if row["source_row_id"] == tie_binding["source_row_id"]))
        materials = json.loads(producer.MATERIAL.read_text())
        cls.material_members = {row["member_id"]: row for row in materials["members"]}

    def check(self, source):
        return producer.checked_cell(self.final, *source)

    def corrupted(self, index, key, value):
        source = copy.deepcopy(self.source)
        source[index][key] = value
        return source

    def test_frozen_compression_source_is_valid(self):
        row = self.check(self.source)
        self.assertEqual(row["contact_state"], "active_resolved")
        self.assertGreater(row["native_compression_force_N"], row["native_force_radius_N"])

    def test_wrong_receiver_rejected(self):
        with self.assertRaisesRegex(ValueError, "receiver differs"):
            self.check(self.corrupted(0, "second", producer.SIDE))

    def test_wrong_finished_cell_area_rejected(self):
        with self.assertRaisesRegex(ValueError, "area differs"):
            self.check(self.corrupted(0, "area_mm2", self.source[0]["area_mm2"] + 1))

    def test_reversed_physical_contact_force_rejected(self):
        with self.assertRaisesRegex(ValueError, "native contact action differs"):
            self.check(self.corrupted(1, "force_on_first_xyz_n",
                                      [-v for v in self.source[1]["force_on_first_xyz_n"]]))

    def test_wrong_native_force_radius_rejected(self):
        with self.assertRaisesRegex(ValueError, "force radii differ"):
            self.check(self.corrupted(1, "force_rounding_radius_xyz_n", [0, 0, 0]))

    def test_disjoint_table_interval_rejected_even_with_stored_gate_true(self):
        with self.assertRaisesRegex(ValueError, "intervals do not intersect"):
            self.check(self.corrupted(3, "native_table_force_interval_N", [0, 0]))

    def test_nonfinite_native_force_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid signed compression"):
            self.check(self.corrupted(3, "native_endpoint_internal_force_N", float("nan")))

    def test_tensile_contact_force_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid signed compression"):
            self.check(self.corrupted(3, "native_endpoint_internal_force_N", -1))

    def test_numerical_ground_cannot_become_physical_receiver(self):
        with self.assertRaisesRegex(ValueError, "source contact gate failed"):
            self.check(self.corrupted(3, "numerical_ground_rf_excluded_from_physical_balance", False))

    def test_native_source_element_substitution_rejected(self):
        with self.assertRaisesRegex(ValueError, "source mapping differs"):
            self.check(self.corrupted(3, "element", self.source[3]["element"] + 1))

    def test_perpendicular_reference_excluded_for_parallel_rail(self):
        context = producer.reference_context(self.final, 1.0, [1, 0, 0],
                                             self.material_members, (producer.RAIL, producer.SIDE),
                                             "active_resolved")
        self.assertEqual(context[producer.RAIL]["normal_to_proposed_grain"], "parallel")
        self.assertIsNone(context[producer.RAIL]["unadjusted_Fc_perpendicular_psi"])
        self.assertIsNone(context[producer.RAIL]["cell_average_to_unadjusted_Fc_perpendicular_ratio"])
        self.assertEqual(context[producer.SIDE]["normal_to_proposed_grain"], "perpendicular")
        self.assertIsNotNone(context[producer.SIDE]["cell_average_to_unadjusted_Fc_perpendicular_ratio"])

    def test_open_cell_has_no_bearing_reference_comparison(self):
        context = producer.reference_context(self.final, 0.0, [1, 0, 0],
                                             self.material_members, (producer.SIDE,), "open_resolved")
        self.assertFalse(context[producer.SIDE]["compression_reference_comparison_applicable"])
        self.assertIsNone(context[producer.SIDE]["cell_average_to_unadjusted_Fc_perpendicular_ratio"])

    def test_ambiguous_cell_has_no_bearing_reference_comparison(self):
        context = producer.reference_context(self.final, 0.01, [1, 0, 0],
                                             self.material_members, (producer.SIDE,),
                                             "ambiguous_at_rounded_boundary")
        self.assertFalse(context[producer.SIDE]["compression_reference_comparison_applicable"])
        self.assertIsNone(context[producer.SIDE]["cell_average_to_unadjusted_Fc_perpendicular_ratio"])

    def test_native_tie_radius_is_valid(self):
        producer.checked_tie_radius(*self.tie_source)

    def test_axial_tie_radius_substitution_rejected(self):
        action, component = copy.deepcopy(self.tie_source)
        action["force_rounding_radius_xyz_n"] = [0, 0, 0]
        with self.assertRaisesRegex(ValueError, "tie force radii differ"):
            producer.checked_tie_radius(action, component)


if __name__ == "__main__":
    unittest.main()
