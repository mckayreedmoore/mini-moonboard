"""Known-answer and fail-closed tests for the hardware requirement packet."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SPEC = importlib.util.spec_from_file_location("hardware_requirements", HERE / "produce.py")
assert SPEC is not None and SPEC.loader is not None
requirements = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(requirements)

GRIP_PATH = ROOT / requirements.GRIP_PATH
COVERAGE_PATH = ROOT / requirements.COVERAGE_PATH
CATALOG_PATH = ROOT / requirements.CATALOG_PATH


class QuarterThreadKnownAnswers(unittest.TestCase):
    def test_multi_receiver_bound_uses_each_member_thickness(self) -> None:
        """Two physical members need two bounds; their total grip is not one member."""
        near = requirements.quarter_thread_lb_requirement(2.0, 40.0)
        far = requirements.quarter_thread_lb_requirement(40.0, 129.0)
        self.assertEqual(near["member_interval_thickness_mm"], 38.0)
        self.assertEqual(near["maximum_thread_bearing_in_member_mm"], 9.5)
        self.assertEqual(near["minimum_LB_underhead_to_last_thread_scratch_mm"], 30.5)
        self.assertEqual(far["member_interval_thickness_mm"], 89.0)
        self.assertEqual(far["maximum_thread_bearing_in_member_mm"], 22.25)
        self.assertEqual(far["minimum_LB_underhead_to_last_thread_scratch_mm"], 106.75)
        self.assertGreater(far["minimum_LB_underhead_to_last_thread_scratch_mm"], near["minimum_LB_underhead_to_last_thread_scratch_mm"])

    def test_axis_source_member_with_split_intervals_fails_closed(self) -> None:
        grip = json.loads(GRIP_PATH.read_text(encoding="utf-8"))
        axis = copy.deepcopy(next(a for a in grip["axes"] if a["axis_id"] == "knee_outer_left_post_1"))
        axis["wood_receiver_intervals"][0]["intersection_solid_intervals_from_underhead_mm"].append([50.0, 51.0])
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        row = next(row for row in catalog["axis_rows"] if axis["axis_id"] in row["axis_ids"])
        with self.assertRaisesRegex(requirements.RequirementError, "member-level gap analysis"):
            requirements.build_axis_requirement(axis, "candidate_outer_post_4", row)


class DatumAndNutEnvelopeKnownAnswers(unittest.TestCase):
    def test_global_axis_datum_is_subtracted_once(self) -> None:
        global_interval = requirements.normalize_interval_to_underhead(
            [101.651, 139.751],
            coordinate_origin="global_axis",
            underhead_global_axis_mm=100.0,
        )
        already_relative = requirements.normalize_interval_to_underhead(
            [1.651, 39.751], coordinate_origin="underhead_relative"
        )
        self.assertAlmostEqual(global_interval[0], 1.651)
        self.assertAlmostEqual(global_interval[1], 39.751)
        self.assertEqual(already_relative, (1.651, 39.751))
        with self.assertRaisesRegex(requirements.RequirementError, "underhead global-axis datum"):
            requirements.normalize_interval_to_underhead([101.651, 139.751], coordinate_origin="global_axis")

    def test_long_smooth_shank_inside_nut_fails_sufficient_profile_condition(self) -> None:
        """A sufficient envelope requires full form to start before the nut seat."""
        self.assertFalse(requirements.evaluate_full_thread_profile(
            86.01,
            120.0,
            earliest_nut_bearing_plane_mm=78.7908,
            latest_nut_far_face_mm=86.0044,
        ))
        self.assertTrue(requirements.evaluate_full_thread_profile(
            78.7908,
            86.0044,
            earliest_nut_bearing_plane_mm=78.7908,
            latest_nut_far_face_mm=86.0044,
        ))

    def test_short_tip_fails_the_hand_calculated_worst_case_stack(self) -> None:
        """Published maxima plus a 3.81 mm physical projection set a hard length edge."""
        envelope = requirements.nut_stack_envelope(
            10.0,
            modeled_head_washer_thickness_mm=2.032,
            head_washer_range_mm=(1.2954, 2.032),
            nut_washer_range_mm=(1.2954, 2.032),
            nut_finished_height_range_mm=(5.3848, 5.7404),
            physical_tip_projection_mm=3.81,
        )
        self.assertEqual(envelope["earliest_nut_bearing_plane_mm"], 10.5588)
        self.assertEqual(envelope["latest_nut_far_face_mm"], 17.7724)
        self.assertEqual(envelope["minimum_physical_tip_target_mm"], 21.5824)
        self.assertEqual(round(21.5 - envelope["minimum_physical_tip_target_mm"], 4), -0.0824)


class PinsAndInventoryFailClosed(unittest.TestCase):
    @staticmethod
    def axis_fixture():
        grip = json.loads(GRIP_PATH.read_text(encoding="utf-8"))
        coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        axis_by_id, family_by_axis, catalog_by_axis = requirements.validate_inventory(grip, coverage, catalog)
        axis_id = "knee_outer_left_post_1"
        return (
            copy.deepcopy(axis_by_id[axis_id]),
            family_by_axis[axis_id],
            catalog_by_axis[axis_id],
        )

    def test_source_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "input.json").write_bytes(b"changed source")
            pin = {
                "id": "fixture",
                "path": "input.json",
                "sha256": hashlib.sha256(b"reviewed source").hexdigest(),
                "role": "test fixture",
            }
            with self.assertRaisesRegex(requirements.RequirementError, "Pinned source changed"):
                requirements.verify_source_hashes(root, [pin])

    def test_missing_geometry_axis_is_rejected_before_build(self) -> None:
        grip = json.loads(GRIP_PATH.read_text(encoding="utf-8"))
        coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        grip["axes"].pop()
        with self.assertRaisesRegex(requirements.RequirementError, "Expected 92"):
            requirements.validate_inventory(grip, coverage, catalog)

    def test_nonfinite_datum_is_rejected(self) -> None:
        grip = json.loads(GRIP_PATH.read_text(encoding="utf-8"))
        coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        axis_by_id, family_by_axis, catalog_by_axis = requirements.validate_inventory(grip, coverage, catalog)
        axis = copy.deepcopy(axis_by_id["knee_outer_left_post_1"])
        axis["underhead_datum"]["head_underface_contact_check"]["signed_gap_mm"] = float("nan")
        with self.assertRaisesRegex(requirements.RequirementError, "non-finite underhead datum"):
            requirements.build_axis_requirement(axis, family_by_axis[axis["axis_id"]], catalog_by_axis[axis["axis_id"]])

    def test_nonfinite_receiver_reported_length_is_rejected(self) -> None:
        axis, family_id, catalog_row = self.axis_fixture()
        axis["wood_receiver_intervals"][0]["receiver_wood_axis_length_mm"] = float("nan")
        with self.assertRaisesRegex(requirements.RequirementError, "receiver wood axis length must be finite and positive"):
            requirements.build_axis_requirement(axis, family_id, catalog_row)

    def test_nonfinite_wood_grip_material_length_is_rejected(self) -> None:
        axis, family_id, catalog_row = self.axis_fixture()
        axis["wood_grip_material_length_mm"] = float("nan")
        with self.assertRaisesRegex(requirements.RequirementError, "wood_grip_material_length_mm must be finite and positive"):
            requirements.build_axis_requirement(axis, family_id, catalog_row)

    def test_negative_underhead_receiver_coordinate_is_rejected(self) -> None:
        axis, family_id, catalog_row = self.axis_fixture()
        receiver = axis["wood_receiver_intervals"][0]
        receiver["intersection_solid_intervals_from_underhead_mm"] = [[-0.5, 37.6]]
        with self.assertRaisesRegex(requirements.RequirementError, "begins headward of the underhead datum"):
            requirements.build_axis_requirement(axis, family_id, catalog_row)

    def test_frozen_geometry_family_answers_and_corner_nut_envelopes(self) -> None:
        data = requirements.build_requirements(ROOT)
        families = {family["family_id"]: family for family in data["family_requirements"]}
        expected_direct_lb_mm = {
            "candidate_ordinary_48": 119.507,
            "candidate_side_16": 157.607,
            "candidate_outer_post_4": 68.326,
            "candidate_center_post_4": 119.126,
            "candidate_center_principal_4": 114.126,
            "candidate_center_post_header_4": 136.426,
            "candidate_center_principal_header_4": 164.926,
            "candidate_knee_inner_header_4": 169.226,
            "candidate_knee_side_4": 195.326,
        }
        self.assertEqual(data["candidate_summary"]["candidate_axes"], 92)
        self.assertEqual(data["retained_starting_stack_reference"]["axis_count"], 12)
        self.assertEqual(
            {key: value["family_minimum_LB_underhead_to_last_thread_scratch_mm"] for key, value in families.items()},
            expected_direct_lb_mm,
        )
        axes = {axis["axis_id"]: axis for axis in data["axis_requirements"]}
        self.assertEqual(
            axes["knee_outer_left_post_1"]["nut_and_tip_requirements"]["nut_bearing_plane_range_underhead_mm"],
            [78.7908, 80.264],
        )
        self.assertEqual(
            axes["knee_outer_left_post_1"]["nut_and_tip_requirements"]["nut_far_face_range_underhead_mm"],
            [84.1756, 86.0044],
        )
        self.assertEqual(
            axes["knee_outer_left_post_1"]["nut_and_tip_requirements"]["minimum_physical_tip_target_underhead_mm"],
            89.8144,
        )
        self.assertEqual(len(axes), 92)


if __name__ == "__main__":
    unittest.main()
