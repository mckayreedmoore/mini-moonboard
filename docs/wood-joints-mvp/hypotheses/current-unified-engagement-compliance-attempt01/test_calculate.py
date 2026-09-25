import math
import shutil
import tempfile
import unittest
from pathlib import Path

from calculate import SOURCE_PINS, build_calculation


class UnifiedEngagementCalculationTests(unittest.TestCase):
    def test_reference_post_seating_tangent_reproduces_pinned_scenario(self):
        result = build_calculation()
        tangent = result["post_seating_tangent"]
        self.assertAlmostEqual(tangent["tensile_stress_area_mm2"], 20.529631503310, 11)
        self.assertAlmostEqual(tangent["equivalent_thread_length_mm"], 5.3975, 11)
        self.assertAlmostEqual(tangent["stiffness_kN_per_mm"], 760.708902392208, 9)
        self.assertAlmostEqual(tangent["compliance_mm_per_kN"], 0.001314563293, 12)
        self.assertAlmostEqual(tangent["extension_at_1kN_mm"], 0.001314563293, 12)

    def test_fixed_rotation_class_clearance_is_separate_from_tangent(self):
        result = build_calculation()
        fit = result["fit_slack_comparator"]
        self.assertAlmostEqual(fit["total_reversal_travel_mm"][0], 0.016130708389, 12)
        self.assertAlmostEqual(fit["total_reversal_travel_mm"][1], 0.142243519427, 12)
        self.assertEqual(fit["one_way_initial_free_travel_mm_if_phase_unknown"][0], 0.0)
        self.assertAlmostEqual(
            fit["one_way_initial_free_travel_mm_if_phase_unknown"][1],
            fit["total_reversal_travel_mm"][1],
            14,
        )
        self.assertIn(
            "not a spring compliance",
            result["compliance_partition"]["fit_is_not_compliance"],
        )

    def test_unresolved_fit_and_physical_transfer_are_not_promoted(self):
        result = build_calculation()
        self.assertFalse(result["scope"]["applies_to_delivered_hardware"])
        self.assertFalse(result["scope"]["physical_axial_engagement_resolved"])
        self.assertFalse(result["full_height_fit"]["established"])
        self.assertIn(
            "overlap length", result["full_height_fit"]["missing_exact_parameter"]
        )
        self.assertFalse(result["scope"]["capacity_or_resistance_calculated"])

    def test_source_drift_refuses_to_recompute(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            copied_root = Path(temporary_directory)
            actual_root = Path(__file__).resolve().parents[4]
            for relative_path in SOURCE_PINS:
                source = actual_root / relative_path
                destination = copied_root / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            changed_source = copied_root / next(iter(SOURCE_PINS))
            changed_source.write_text(changed_source.read_text() + "\n")
            with self.assertRaisesRegex(ValueError, "source drift"):
                build_calculation(copied_root)

    def test_output_records_all_source_pins(self):
        result = build_calculation()
        pins = result["source_pins"]
        self.assertEqual(len(pins), 8)
        self.assertTrue(all(len(pin["sha256"]) == 64 for pin in pins))
        self.assertTrue(
            math.isfinite(result["post_seating_tangent"]["stiffness_N_per_mm"])
        )


if __name__ == "__main__":
    unittest.main()
