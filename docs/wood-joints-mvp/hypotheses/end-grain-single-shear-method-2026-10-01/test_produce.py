"""Observable scope and factor checks for conditional end-grain arithmetic."""

from __future__ import annotations

import copy
import importlib.util
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("test_end_grain_producer", HERE / "produce.py")
producer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = producer
spec.loader.exec_module(producer)


def fixture():
    receivers = [
        {"receiver_id": "end-grain-block", "modeled_bearing_length_in": 5.0,
         "modeled_interval_from_underhead_mm": [0.0, 127.0],
         "source_descriptor_grain_axis_unit_global_xyz": [1.0, 0.0, 0.0]},
        {"receiver_id": "header", "modeled_bearing_length_in": 1.5,
         "modeled_interval_from_underhead_mm": [127.0, 165.1],
         "source_descriptor_grain_axis_unit_global_xyz": [0.0, 1.0, 0.0]},
    ]
    axis = {"receiver_ids_underhead_to_tip": [row["receiver_id"] for row in receivers],
            "receivers": receivers, "modeled_bolt_axis_unit_global_xyz": [1.0, 0.0, 0.0],
            "parallel_grain_receiver_id": "end-grain-block"}
    state = {"actual_lateral_force_on_receiver_0_N": [0.0, 3.0, 4.0],
             "actual_lateral_force_on_receiver_1_N": [0.0, -3.0, -4.0],
             "actual_lateral_resultant_N": 5.0,
             "actual_lateral_angle_to_grain_deg_by_receiver": {
                 "end-grain-block": 90.0, "header": math.degrees(math.acos(0.6))},
             "same_state_signed_outer_tie_N_once": 9000.0}
    return axis, state


class EndGrainReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.final, cls.nds, cls.bearing = producer.methods()

    def calculate(self, axis, state):
        return producer.conditional_reference(self.final, self.nds, self.bearing, axis, state)

    def test_endgrain_factor_once_and_axial_tie_separate(self):
        axis, state = fixture()
        before = copy.deepcopy(state)
        result = self.calculate(axis, state)
        self.assertEqual(state, before)
        self.assertEqual(result["main_receiver"], "end-grain-block")
        self.assertEqual(result["main_Fe_perpendicular_psi"], 4450.0)
        self.assertEqual(result["Ktheta"], 1.25)
        self.assertEqual(result["Ceg_application_count"], 1)
        for mode in producer.MODES:
            self.assertAlmostEqual(result["Ceg_only_reference_modes_lbf"][mode],
                                   0.67 * result["unadjusted_reference_modes_lbf"][mode])
        reference = 0.67 * result["governing_unadjusted_reference_N"]
        self.assertAlmostEqual(result["governing_Ceg_only_reference_N"], reference)
        self.assertAlmostEqual(result["lateral_demand_to_Ceg_only_reference_ratio"], 5.0 / reference)
        self.assertFalse(result["joint_accepted"])

    def test_endpoint_reversal_keeps_physical_main_and_modes(self):
        axis, state = fixture()
        first = self.calculate(axis, state)
        axis["receivers"].reverse()
        axis["receiver_ids_underhead_to_tip"].reverse()
        axis["modeled_bolt_axis_unit_global_xyz"] = [-1.0, 0.0, 0.0]
        # Reversing the modeled endpoint convention reverses the interval datum.
        for receiver in axis["receivers"]:
            start, end = receiver["modeled_interval_from_underhead_mm"]
            receiver["modeled_interval_from_underhead_mm"] = [165.1 - end, 165.1 - start]
        state["actual_lateral_force_on_receiver_0_N"], state["actual_lateral_force_on_receiver_1_N"] = (
            state["actual_lateral_force_on_receiver_1_N"], state["actual_lateral_force_on_receiver_0_N"]
        )
        second = self.calculate(axis, state)
        self.assertEqual(first["main_receiver"], second["main_receiver"])
        self.assertNotEqual(first["main_receiver_underhead_to_tip_index"],
                            second["main_receiver_underhead_to_tip_index"])
        for mode in producer.MODES:
            self.assertAlmostEqual(first["Ceg_only_reference_modes_lbf"][mode],
                                   second["Ceg_only_reference_modes_lbf"][mode])

    def test_ambiguous_or_oblique_grain_rejects_method(self):
        for grain in ([1.0, 0.0, 0.0], [1.0, 1.0, 0.0]):
            axis, state = fixture()
            axis["receivers"][1]["source_descriptor_grain_axis_unit_global_xyz"] = grain
            with self.assertRaisesRegex(ValueError, "one parallel and one perpendicular"):
                self.calculate(axis, state)

    def test_axial_force_is_rejected_as_lateral(self):
        axis, state = fixture()
        state["actual_lateral_force_on_receiver_0_N"] = [1.0, 3.0, 4.0]
        state["actual_lateral_force_on_receiver_1_N"] = [-1.0, -3.0, -4.0]
        with self.assertRaisesRegex(ValueError, "bolt-axis component"):
            self.calculate(axis, state)

    def test_zero_direction_or_changed_interval_rejected(self):
        axis, state = fixture()
        state["actual_lateral_force_on_receiver_0_N"] = [0.0, 0.0, 0.0]
        with self.assertRaisesRegex(ValueError, "zero or invalid"):
            self.calculate(axis, state)
        axis, state = fixture()
        axis["receivers"][0]["modeled_bearing_length_in"] = 4.0
        with self.assertRaisesRegex(ValueError, "interval length differs"):
            self.calculate(axis, state)


if __name__ == "__main__":
    unittest.main()
