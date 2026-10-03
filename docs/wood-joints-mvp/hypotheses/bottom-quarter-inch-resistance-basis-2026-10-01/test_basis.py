"""Independent NDS closed forms and frozen-action/applicability checks."""

import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

import produce as p


def oracle(lm, ls, fm, fs, theta, fyb):
    """NDS Table 12.3.1A closed forms, independent of the quadratic helper."""
    d, re, rt, kt = 0.25, fm / fs, lm / ls, 1 + theta / 360
    k1 = (math.sqrt(re + 2 * re**2 * (1 + rt + rt**2) + rt**2 * re**3)
          - re * (1 + rt)) / (1 + re)
    k2 = -1 + math.sqrt(2 * (1 + re) + 2 * fyb * (1 + 2 * re) * d**2 / (3 * fm * lm**2))
    k3 = -1 + math.sqrt(2 * (1 + re) / re + 2 * fyb * (2 + re) * d**2 / (3 * fm * ls**2))
    return {
        "Im": d * lm * fm / (4 * kt), "Is": d * ls * fs / (4 * kt),
        "II": k1 * d * ls * fs / (3.6 * kt),
        "IIIm": k2 * d * lm * fm / ((1 + 2 * re) * 3.2 * kt),
        "IIIs": k3 * d * ls * fm / ((2 + re) * 3.2 * kt),
        "IV": d**2 * math.sqrt(2 * fm * fyb / (3 * (1 + re))) / (3.2 * kt),
    }


class BasisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = [Path("/tmp/mini-moonboard-" + name + "-2026-10-01.json") for name in
                     ("remaining-single-shear-reference", "bottom-outer-placement", "bottom-outer-joint")]
        cls.report = p.produce(*cls.paths)
        cls.source = json.loads(cls.paths[0].read_text())

    def test_all_2016_modes_independent_from_vectors_and_grains(self):
        count = 0
        for row in self.report["bolt_state_rows"]:
            source = row["unchanged_source_bolt_state"]
            receivers = self.report["unchanged_axis_geometry_and_grain"][source["axis_id"]]["receivers"]
            lengths = [r["modeled_bearing_length_mm"] / 25.4 for r in receivers]
            angles, bearings = [], []
            for i, receiver in enumerate(receivers):
                force = source[f"actual_lateral_force_on_receiver_{i}_N"]
                grain = receiver["pinned_map_grain_axis_unit_global_xyz"]
                dot = sum(a * b for a, b in zip(force, grain, strict=True))
                theta = math.acos(min(1, abs(dot) / (math.hypot(*force) * math.hypot(*grain))))
                angles.append(math.degrees(theta))
                bearings.append(5600 * 4450 / (5600 * math.sin(theta)**2 + 4450 * math.cos(theta)**2))
            for result in row["conditional_references"]:
                m, s = (0, 1) if result["assignment"] == "receiver_0_as_main" else (1, 0)
                values = oracle(lengths[m], lengths[s], bearings[m], bearings[s], max(angles),
                                result["Fyb_scenario_psi"])
                for mode, value in values.items():
                    self.assertTrue(math.isclose(value, result["reference_values_lbf"][mode], rel_tol=1e-8))
                    count += 1
        self.assertEqual(count, 2016)

    def test_all_actions_and_wrenches_preserved_and_no_acceptance(self):
        wanted = [r for r in self.source["state_rows"] if r["axis_id"] in p.AXES]
        self.assertEqual(wanted, [r["unchanged_source_bolt_state"] for r in self.report["bolt_state_rows"]])
        placement, joint = [json.loads(path.read_text()) for path in self.paths[1:]]
        for output, source in [("unchanged_member_bolt_states", "member_bolt_states"),
                               ("unchanged_interface_wrenches", "member_interface_states")]:
            self.assertEqual(self.report[output], placement[source])
        self.assertEqual(self.report["unchanged_cleat_complete_joint_states"], joint["joint_states"])
        self.assertEqual(self.report["unchanged_contact_cell_states"], joint["contact_cell_states"])
        self.assertFalse(self.report["joint_accepted"])
        self.assertFalse(self.report["adopted_capacity"])
        for row in self.report["bolt_state_rows"]:
            for result in row["conditional_references"]:
                self.assertIsNone(result["Cg"])
                self.assertIsNone(result["Cdelta"])
                self.assertIsNone(result["adjusted_reference_N"])

    def test_critical_budget_and_nonzero_axial_action(self):
        row = next(r for r in self.report["bolt_state_rows"] if p.state_key(r["unchanged_source_bolt_state"])
                   == ("a1-rear", 6, p.PREFIX + "side_1"))
        self.assertEqual(row["unchanged_source_bolt_state"]["same_state_signed_outer_tie_N_once"], 197.1248)
        self.assertAlmostEqual(row["conditional_references"][0]["lateral_demand_to_unadjusted_reference"],
                               1.0945088665197509, places=12)
        self.assertAlmostEqual(row["conditional_references"][1]["reference_lateral_N"], 928.2217781407836)
        self.assertAlmostEqual(self.report["critical_unity_factor_mode_IV_Fyb_budget_psi"],
                               53907.73465006574)

    def test_quarter_inch_boundary_is_not_subquarter(self):
        self.assertFalse(p.geometry_triggers(0.25)["sub_quarter_Cg_exception_applies"])
        self.assertFalse(p.geometry_triggers(0.25)["sub_quarter_Cdelta_exception_applies"])
        self.assertTrue(p.geometry_triggers(math.nextafter(0.25, 0))["sub_quarter_Cg_exception_applies"])
        for bad in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                p.geometry_triggers(bad)

    def test_reject_missing_duplicate_and_changed_signed_force(self):
        rows = [r["unchanged_source_bolt_state"] for r in self.report["bolt_state_rows"]]
        for bad in (rows[:-1], rows + [rows[0]]):
            with self.assertRaises(ValueError):
                p.validate_rows(bad)
        bad = copy.deepcopy(rows)
        bad[0]["actual_lateral_force_on_receiver_0_N"][1] *= -1
        with self.assertRaises(ValueError):
            p.validate_rows(bad)

    def test_changed_frozen_report_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "changed.json"
            path.write_bytes(self.paths[0].read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "changed frozen reference"):
                p.checked_report(path, "reference")

    def test_mode_switch_and_invalid_yield_input(self):
        # A shorter asymmetric member can change the governing mode as Fyb grows.
        self.assertEqual(p.modes(3.5, 1.5, 5600, 4450, 90, 45000)["governing_mode"], "IV")
        self.assertEqual(p.modes(3.5, 1.5, 5600, 4450, 90, 106000)["governing_mode"], "IIIs")
        for fyb in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                p.modes(3.5, 3.5, 5600, 4450, 90, fyb)


if __name__ == "__main__":
    unittest.main()
