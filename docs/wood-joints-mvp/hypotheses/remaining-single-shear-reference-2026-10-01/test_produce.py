"""Focused arithmetic and direction checks for produce.py."""

from __future__ import annotations

import importlib.util
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRODUCER_PATH = HERE / "produce.py"
spec = importlib.util.spec_from_file_location("remaining_single_shear_producer", PRODUCER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load produce.py")
producer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = producer
spec.loader.exec_module(producer)


class SingleShearReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        producer.pin_sources()
        _, cls.nds_method, cls.fe_helper = producer.basis_sources()

    def test_published_tr12_example_3_1_six_mode_answer(self) -> None:
        result = self.nds_method.calculate(0.5, 1.5, 1.5, 4800.0, 4800.0, 0.0)
        expected = {"Im": 900.0, "Is": 900.0, "II": 414.0,
                    "IIIm": 550.0, "IIIs": 550.0, "IV": 663.0}
        for mode, value in expected.items():
            self.assertLess(
                abs(result["reference_values_lbf"][mode] - value), 0.6
            )
        self.assertEqual(result["governing_mode"], "II")

    def test_signed_resultant_and_grain_axis_are_unoriented(self) -> None:
        force = [3.0, -4.0, 0.0]
        grain = [0.0, 0.0, 1.0]
        angle = producer.angle_to_grain_degrees(force, grain)
        self.assertTrue(math.isclose(angle, 90.0, abs_tol=1e-12))
        self.assertTrue(
            math.isclose(
                producer.angle_to_grain_degrees([-x for x in force], grain),
                angle,
                abs_tol=1e-12,
            )
        )
        self.assertTrue(
            math.isclose(
                producer.angle_to_grain_degrees(force, [-x for x in grain]),
                angle,
                abs_tol=1e-12,
            )
        )
        self.assertTrue(
            math.isclose(
                producer.angle_to_grain_degrees([0.0, 0.0, -2.0], grain),
                0.0,
                abs_tol=1e-12,
            )
        )

    def test_both_receiver_role_assignments_close_by_mode_permutation(self) -> None:
        axis = {
            "receivers": [
                {
                    "receiver_id": "receiver-A",
                    "modeled_bearing_length_in": 1.5,
                    "source_descriptor_grain_axis_unit_global_xyz": [0.0, 0.0, 1.0],
                },
                {
                    "receiver_id": "receiver-B",
                    "modeled_bearing_length_in": 0.75,
                    "source_descriptor_grain_axis_unit_global_xyz": [0.0, 1.0, 0.0],
                },
            ]
        }
        forces = {"receiver-A": [0.0, 1.0, 0.0], "receiver-B": [0.0, -1.0, 0.0]}
        report = producer.make_reference_assignments(
            self.nds_method, self.fe_helper, axis, forces
        )
        self.assertTrue(
            report["assignment_difference"]["permutation_mode_map_closure_passed"]
        )
        first, second = report["scenarios"]
        swap = producer.PERMUTED_MODES
        for mode in producer.MODES:
            self.assertTrue(
                math.isclose(
                    first["unadjusted_reference_modes_lbf"][mode],
                    second["unadjusted_reference_modes_lbf"][swap[mode]],
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
            )
        self.assertTrue(
            math.isclose(
                first["governing_unadjusted_reference_N"],
                second["governing_unadjusted_reference_N"],
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        )

    def test_end_grain_rows_keep_reference_and_ratio_null(self) -> None:
        receivers = [
            {"receiver_id": "end-grain", "source_descriptor_grain_axis_unit_global_xyz": [1, 0, 0]},
            {"receiver_id": "side-grain", "source_descriptor_grain_axis_unit_global_xyz": [0, 1, 0]},
        ]
        exclusion = producer.applicability_exclusion([1, 0, 0], receivers)
        self.assertEqual(exclusion, "EXCLUDED_END_GRAIN_APPLICABILITY_UNESTABLISHED")
        axis = {"receivers": receivers, "single_shear_applicability_exclusion": exclusion}
        forces = {"end-grain": [0, 1, 0], "side-grain": [0, -1, 0]}
        reason, assignments, ratios, angles = producer.state_reference_fields(
            self.nds_method, self.fe_helper, axis, forces
        )
        self.assertEqual(reason, exclusion)
        self.assertIsNone(assignments)
        self.assertIsNone(ratios)
        self.assertEqual(set(angles), {"end-grain", "side-grain"})

    def test_zero_lateral_resultant_keeps_direction_and_reference_null(self) -> None:
        axis = {
            "receivers": [
                {
                    "receiver_id": "receiver-A",
                    "source_descriptor_grain_axis_unit_global_xyz": [0, 0, 1],
                },
                {
                    "receiver_id": "receiver-B",
                    "source_descriptor_grain_axis_unit_global_xyz": [0, 0, 1],
                },
            ],
            "single_shear_applicability_exclusion": None,
        }
        forces = {"receiver-A": [0.0, 0.0, 0.0], "receiver-B": [0.0, 0.0, 0.0]}
        reason, assignments, ratios, angles = producer.state_reference_fields(
            self.nds_method, self.fe_helper, axis, forces
        )
        self.assertEqual(reason, "EXCLUDED_ZERO_LATERAL_RESULTANT_DIRECTION_UNDEFINED")
        self.assertIsNone(assignments)
        self.assertIsNone(ratios)
        self.assertIsNone(angles)

    def test_model_grain_map_hash_mismatch_fails_closed(self) -> None:
        map_path, map_sha = producer.PINS["frame_grain_map"]
        receiver = {
            "receiver_id": "base_header",
            "current_shaft_intersection_solid_intervals_from_underhead_mm": [[0.0, 38.1]],
            "intersection_solid_intervals_from_underhead_mm": [[0.0, 38.1]],
        }
        descriptor = {
            "member_kind": "timber",
            "member_id": "base_header",
            "material_frame_map": map_path.relative_to(producer.ROOT).as_posix(),
            "material_frame_map_sha256": map_sha,
            "grain_global_xyz": [0.0, 1.0, 0.0],
        }
        bodies = {"base_header": {"geometry_record": {"source_descriptor": descriptor,
                                                       "name": "base_header"}}}
        maps = {"frame": {"base_header": {"conditional_grain_assignment":
                                             {"proposed_global_xyz": [0.0, 1.0, 0.0]}}},
                "block": {}}
        self.assertEqual(
            producer.receiver_basis(receiver, [1.0, 0.0, 0.0], bodies, maps)["receiver_id"],
            "base_header",
        )
        descriptor["material_frame_map_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "not bound to pinned map"):
            producer.receiver_basis(receiver, [1.0, 0.0, 0.0], bodies, maps)


if __name__ == "__main__":
    unittest.main()
