"""Known answers, frozen action joins and fail-closed resistance boundaries."""
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("retained_producer_test", HERE / "produce.py")
producer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(producer)
LOAD = Path("/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json")
RAW = Path("/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01-raw-oracle.json")


class ResistanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = producer.produce(LOAD, RAW)
        cls.nds = producer.module("retained_nds_test", "mini_moonboard/nds_2024_multi_member_bolt_yield.py")

    def test_current_census_and_refusal(self):
        report = self.report
        self.assertEqual(len(report["state_rows"]), 252)
        self.assertEqual(len(report["group_state_rows"]), 126)
        expected = {(case, i, axis) for case in producer.CASES
                    for i in range(7) for axis in producer.AXES}
        self.assertEqual({(r["case_id"], r["increment_index"], r["axis_id"])
                          for r in report["state_rows"]}, expected)
        self.assertEqual(report["counts"]["pending_criteria"], 47)
        self.assertEqual(report["counts"]["closed_criteria"], 0)
        self.assertTrue(all(report[k] is False for k in producer.FLAGS))
        for row in report["state_rows"]:
            for receiver in row["receivers"]:
                self.assertIsNone(receiver["finished_loaded_end_distance_mm"])
                self.assertIsNone(receiver["finished_loaded_edge_distance_mm"])
                self.assertIsNone(receiver["minimum_spacing_end_edge_verified"])
            for result in row["lateral_references"]:
                for field in ("Cg", "Cdelta", "CD", "CM", "Ct", "adjusted_resistance_n",
                              "adjusted_joint_utilization"):
                    self.assertIsNone(result[field])
                self.assertFalse(result["reference_qualified_for_this_finished_joint"])
            actual = row["steel"]["actual_bolt_material_reference"]
            self.assertEqual(actual["status"], "unresolved")
            self.assertIsNone(actual["interaction_utilization"])
            self.assertIsNone(row["steel"]["axial_complete_joint_resistance_n"])
            self.assertFalse(row["steel"]["wrench_offset_is_bolt_bending"])

    def test_grain_bearing_known_answers(self):
        for diameter, perpendicular in ((.5, 3150.), (.375, 3650.)):
            self.assertEqual(self.nds._fe_theta_psi(specific_gravity=.5,
                                                  diameter_in=diameter, angle_degrees=0), 5600.)
            self.assertEqual(self.nds._fe_theta_psi(specific_gravity=.5,
                                                  diameter_in=diameter, angle_degrees=90), perpendicular)
            expected = 2 * 5600 * perpendicular / (5600 + perpendicular)
            self.assertAlmostEqual(self.nds._fe_theta_psi(specific_gravity=.5,
                                                         diameter_in=diameter, angle_degrees=45), expected)

    def test_independent_mode_IV_and_assignment_reversal(self):
        for row in self.report["state_rows"]:
            for ref in row["lateral_references"]:
                d, fm, fs = ref["diameter_scenario_in"], ref["main_Fe_psi"], ref["side_Fe_psi"]
                expected = d**2 * math.sqrt(2 * ref["Fyb_scenario_psi"] * fm * fs
                                           / (3 * (fm + fs))) / ref["reduction_terms"]["IV"]
                self.assertAlmostEqual(expected, ref["mode_reference_lbf"]["IV"], places=9)
                self.assertAlmostEqual(min(ref["mode_reference_lbf"].values()),
                                       min(ref["reverse_assignment_mode_reference_lbf"].values()), places=9)

    def test_signed_same_state_and_steel_known_answer(self):
        for row in self.report["state_rows"]:
            r0, r1 = row["receivers"]
            self.assertLess(math.hypot(*producer.add(r0["force_on_receiver_xyz_n"],
                                                    r1["force_on_receiver_xyz_n"])), 1e-9)
            steel = row["steel"]
            actual = steel["conditional_nominal_material_reference"]
            self.assertEqual(actual["axial_tension_demand_n"], row["same_state_axial_tie_n"])
            self.assertAlmostEqual(actual["lateral_shear_demand_n"], row["lateral_resultant_n"])
            expected = math.hypot(row["same_state_axial_tie_n"], math.sqrt(3) * row["lateral_resultant_n"])
            expected /= steel["hypothetical_full_D_interface_area_mm2"] * 92000 * producer.PSI_TO_MPA
            self.assertAlmostEqual(expected, actual["interaction_utilization"], places=12)

    def test_current_grips_thresholds_and_oblique_rows(self):
        for axis, row in self.report["axis_register"].items():
            grip, threshold = ((177.8, 158.9278) if axis.startswith("lumber_leg") else
                               ((76.2, 69.3166) if axis.startswith("rail_front") else (88.9, 78.8416)))
            self.assertAlmostEqual(row["modeled_wood_grip_mm"], grip)
            self.assertAlmostEqual(row["conditional_full_body_transition_threshold_mm"], threshold)
            self.assertIsNone(row["hardware_policy"]["delivered_full_body_to_transition_mm"])
        for row in self.report["group_state_rows"]:
            self.assertGreater(row["resultant_to_bolt_row_degrees"], 1e-6)
            self.assertIsNone(row["Cg"])
            self.assertIsNone(row["group_adjusted_resistance_n"])

    def test_changed_load_bytes_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "changed.json"
            path.write_bytes(LOAD.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "changed frozen load"):
                producer.checked_load(path, RAW)

    def test_every_signed_row_matches_its_frozen_source_state(self):
        load = json.loads(LOAD.read_text())
        by_key = {(s["case_id"], s["increment_index"]): s for s in load["states"]}
        for row in self.report["state_rows"]:
            state = by_key[row["case_id"], row["increment_index"]]
            source = state["bolt_states"][row["axis_id"]]
            self.assertEqual(row["load_factor"], state["load_factor"])
            self.assertEqual(row["lateral_force_on_first_xyz_n"],
                             source["lateral_interface_action"]["force_on_first_xyz_n"])
            self.assertEqual(row["same_state_axial_tie_n"],
                             source["axial_interface_action"]["axial_along_installation_direction_n"])
            for side, receiver in zip(("first", "second"), row["receivers"], strict=True):
                self.assertEqual(receiver["member"], source["lateral_interface_action"][side])
                self.assertEqual(receiver["force_on_receiver_xyz_n"],
                                 source["lateral_interface_action"][f"force_on_{side}_xyz_n"])

    def test_changed_and_misbound_raw_receipt_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "wrong-raw.json"
            data = json.loads(RAW.read_text())
            data["report_sha256"] = "0" * 64
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "changed accepted raw receipt"):
                producer.checked_load(LOAD, path)
            real_sha = producer.sha
            def force_expected_sha(p):
                return producer.RAW_SHA if p == path else real_sha(p)
            with patch.object(producer, "sha", force_expected_sha), self.assertRaisesRegex(
                ValueError, "raw receipt does not bind load report"
            ):
                producer.checked_load(LOAD, path)

    def test_changed_manifest_and_input_pin_refused(self):
        real_sha, real_pin = producer.sha, producer.pin
        def wrong_manifest(path):
            return "0" * 64 if path.name == "source-pins.json" else real_sha(path)
        with patch.object(producer, "sha", wrong_manifest), self.assertRaisesRegex(
            ValueError, "changed source manifest"
        ):
            producer.produce(LOAD, RAW)
        target = next(iter(self.report["rechecked_load_input_pins"]))
        def wrong_input(path):
            return {"sha256": "0" * 64, "size_bytes": 0} if str(path) == str(producer.ROOT / target) else real_pin(path)
        with patch.object(producer, "pin", wrong_input), self.assertRaisesRegex(
            ValueError, "changed load input"
        ):
            producer.checked_load(LOAD, RAW)


if __name__ == "__main__":
    unittest.main()
