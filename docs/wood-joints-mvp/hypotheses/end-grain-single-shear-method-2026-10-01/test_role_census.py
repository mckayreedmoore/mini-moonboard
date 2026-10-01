"""Focused tests for the source census geometry and signed state guards."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).with_name("role_census.py")
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("role_census_under_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
ROLE_CENSUS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ROLE_CENSUS)


def axis_fixture() -> dict[str, Any]:
    return {
        "axis_id": "fixture_axis",
        "receiver_ids_underhead_to_tip": ["end_grain_member", "side_grain_member"],
        "modeled_bolt_axis_unit_global_xyz": [0.0, 0.0, 1.0],
        "receivers": [
            {
                "receiver_id": "end_grain_member",
                "source_descriptor_grain_axis_unit_global_xyz": [0.0, 0.0, 1.0],
            },
            {
                "receiver_id": "side_grain_member",
                "source_descriptor_grain_axis_unit_global_xyz": [1.0, 0.0, 0.0],
            },
        ],
    }


def state_fixture() -> dict[str, Any]:
    return {
        "case_id": "a1-rear",
        "increment_index": 0,
        "load_factor": 0.1,
        "axis_id": "fixture_axis",
        "lateral_plane_source_name": "fixture_plane",
        "lateral_plane_source_row_ids": ["SPR1", "SPR2"],
        "lateral_plane_point_xyz_mm": [1.0, 2.0, 3.0],
        "actual_lateral_force_on_receiver_0_N": [0.0, 3.0, 4.0],
        "actual_lateral_force_on_receiver_1_N": [0.0, -3.0, -4.0],
        "actual_lateral_resultant_N": 5.0,
        "actual_lateral_angle_to_grain_deg_by_receiver": {
            "end_grain_member": 36.86989764584401,
            "side_grain_member": 90.0,
        },
        "same_state_signed_outer_tie_N_once": 7.0,
        "same_state_tie_source_row_ids": ["SPR3"],
        "single_shear_reference_exclusion": "EXCLUDED_END_GRAIN_APPLICABILITY_UNESTABLISHED",
        "single_shear_reference_assignments": None,
        "demand_to_reference_ratios_unadjusted_only": None,
        "joint_accepted": False,
    }


class RoleCensusTests(unittest.TestCase):
    def test_identifies_exactly_one_parallel_grain_receiver(self) -> None:
        axis = axis_fixture()
        self.assertEqual(
            ROLE_CENSUS.parallel_grain_receiver(
                axis["modeled_bolt_axis_unit_global_xyz"], axis["receivers"]
            ),
            "end_grain_member",
        )

    def test_rejects_ambiguous_parallel_grain_receivers(self) -> None:
        axis = axis_fixture()
        axis["receivers"][1]["source_descriptor_grain_axis_unit_global_xyz"] = [0, 0, -1]
        with self.assertRaisesRegex(ValueError, "one parallel-grain"):
            ROLE_CENSUS.parallel_grain_receiver(
                axis["modeled_bolt_axis_unit_global_xyz"], axis["receivers"]
            )

    def test_validates_and_preserves_raw_signed_state(self) -> None:
        axis = axis_fixture()
        state = state_fixture()
        before = state.copy()
        self.assertIsNone(ROLE_CENSUS.validate_state(state, axis))
        self.assertEqual(state, before)

    def test_rejects_nonclosing_sign_or_wrong_grain_angle(self) -> None:
        axis = axis_fixture()
        state = state_fixture()
        state["actual_lateral_force_on_receiver_1_N"] = [0.0, 3.0, 4.0]
        with self.assertRaisesRegex(ValueError, "do not close"):
            ROLE_CENSUS.validate_state(state, axis)

        state = state_fixture()
        state["actual_lateral_angle_to_grain_deg_by_receiver"]["end_grain_member"] = 0.0
        with self.assertRaisesRegex(ValueError, "load-to-grain angle differs"):
            ROLE_CENSUS.validate_state(state, axis)

    def test_rejects_nonfinite_components_and_duplicate_plane_sources(self) -> None:
        axis = axis_fixture()
        state = state_fixture()
        state["actual_lateral_force_on_receiver_0_N"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            ROLE_CENSUS.validate_state(state, axis)

        state = state_fixture()
        state["lateral_plane_source_row_ids"] = ["SPR1", "SPR1"]
        with self.assertRaisesRegex(ValueError, "two-row pair"):
            ROLE_CENSUS.validate_state(state, axis)


if __name__ == "__main__":
    unittest.main()
