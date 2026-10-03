"""Check completeness, rounding and the explicit reference/acceptance boundary."""

import copy
import hashlib
import importlib.util
import json
import math
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("service_joint_check", Path(__file__).with_name("check_joint.py"))
joint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(joint)


class JointChecks(unittest.TestCase):
    def test_scope_requires_candidate(self):
        joint.require_scope({"candidate": joint.CANDIDATE, "geometry_revision_id": joint.REVISION})
        with self.assertRaises(ValueError):
            joint.require_scope({"candidate": "compact-floor-flush-development",
                                 "geometry_revision_id": joint.REVISION})
        with self.assertRaises(ValueError):
            joint.require_scope({"candidate": joint.CANDIDATE, "geometry_revision_id": "other-model"})

    def test_rounding_box_extremum(self):
        # Independently enumerate all eight interval vertices, including sign changes.
        import itertools
        force, radii = [-3.0, 0.1, 4.0], [0.5, 0.2, 0.3]
        expected = max(math.hypot(*(f + sign * r for f, r, sign in zip(force, radii, signs)))
                       for signs in itertools.product((-1, 1), repeat=3))
        self.assertAlmostEqual(joint.force_upper_bound(force, radii), expected)
        with self.assertRaises(ValueError):
            joint.force_upper_bound(force, [-1.0, 0.0, 0.0])
        with self.assertRaises(ValueError):
            joint.force_upper_bound([float("nan"), 0.0, 0.0], radii)

    def test_source_state_coverage(self):
        rows = [{"block": joint.BLOCK, "axis_id": axis, "case": case,
                 "increment_index": i, "load_factor": factor}
                for axis in joint.AXES for case in joint.CASES
                for i, factor in enumerate(joint.FACTORS)]
        self.assertEqual(len(joint.select_states({"bolt_actions": rows})), 84)
        for invalid in (rows[:-1], rows + [rows[0]]):
            with self.assertRaises(ValueError):
                joint.select_states({"bolt_actions": invalid})
        invalid = copy.deepcopy(rows)
        invalid[0]["case"] = "a12-forward"
        with self.assertRaises(ValueError):
            joint.select_states({"bolt_actions": invalid})
        invalid = copy.deepcopy(rows)
        invalid[0]["load_factor"] = 1.0
        with self.assertRaises(ValueError):
            joint.select_states({"bolt_actions": invalid})

    def test_complete_boundary_identity(self):
        receivers = {}
        for i, (name, names) in enumerate(joint.BOUNDARY_SOURCES.items()):
            sign = 1 if i == 0 else -1
            receivers[name] = {"source_names": sorted(names), "force_n": [sign * x for x in (1.0, 2.0, 3.0)],
                               "moment_at_block_datum_nmm": [sign * x for x in (4.0, 5.0, 6.0)]}
        rows = [{"block": joint.BLOCK, "case": case, "increment_index": i,
                 "load_factor": factor, "source_balance_reproduced": True,
                 "incident_connection_count": 16, "source_load_node_count": 20,
                 "receiver_actions_on_block": copy.deepcopy(receivers),
                 "force_residual_n": [0.0, 0.0, 0.0], "force_rounding_radius_n": [1e-6] * 3,
                 "moment_residual_nmm": [0.0, 0.0, 0.0], "moment_rounding_radius_nmm": [1e-6] * 3}
                for case in joint.CASES for i, factor in enumerate(joint.FACTORS)]
        expected = copy.deepcopy(rows)
        self.assertEqual(joint.select_boundaries({"block_balances": rows}), expected)
        for invalid in (rows[:-1], rows + [rows[0]]):
            with self.assertRaises(ValueError):
                joint.select_boundaries({"block_balances": invalid})
        for mutation in ("factor", "receiver", "duplicate_source", "missing_source", "residual"):
            invalid = copy.deepcopy(rows)
            if mutation == "factor":
                invalid[0]["load_factor"] = 0.2
            elif mutation == "receiver":
                receiver_rows = invalid[0]["receiver_actions_on_block"]
                receiver_rows["base_side_right"] = receiver_rows.pop("base_side_left")
            elif mutation in ("duplicate_source", "missing_source"):
                sources = invalid[0]["receiver_actions_on_block"]["base_side_left"]["source_names"]
                if mutation == "duplicate_source":
                    sources[0] = sources[1]
                else:
                    sources.pop()
            else:
                invalid[0]["moment_residual_nmm"][0] = 2e-6
            with self.assertRaises(ValueError, msg=mutation):
                joint.select_boundaries({"block_balances": invalid})

    def test_frozen_joint_result(self):
        report = joint.produce()
        self.assertEqual(report["counts"], {"bolt_states": 84, "whole_boundary_states": 21,
                                           "incident_ports_per_state": 16, "nominal_washer_seats": 8})
        self.assertAlmostEqual(max(r["lateral_upper_n"] for r in report["components"]), 33.808167067, places=8)
        self.assertAlmostEqual(max(r["tension_upper_n"] for r in report["components"]), 57.210125, places=8)
        self.assertTrue(report["assumed_local_contract"]["all_saved_states_inside_force_box"])
        self.assertAlmostEqual(report["component_scenario"]
                               ["force_box_to_worst_direction_reference_budget_ratio"], 0.704414, places=5)
        self.assertEqual(set(report["remaining_joint_gates"]), {
            "coupled_bolt_head_nut_washer_contact_and_metal_resistance",
            "finished_member_sections_local_splitting_and_group_applicability",
            "selected_hardware_functional_thread_fit_and_material_basis",
            "joint_slip_rotation_and_frame_compatibility",
            "finite_installed_clearance_tools_removal_and_cost",
            "supported_shop_sequence_and_individual_member_transport",
            "authenticated_missing_frame_cases_or_adopted_local_envelope_coverage",
        })
        self.assertEqual(report["status"], "HOLD_COMPLETE_JOINT_EVIDENCE_MISSING")
        self.assertEqual(report["candidate"], "compact-floor-flush-wood-joints-development")
        for field in ("local_joint_mvp_complete", "complete_joint_accepted",
                      "six_case_envelope_established", "geometry_changed", "native_solve_executed",
                      "fabrication_released", "drilling_released", "structural_released", "climbing_released"):
            self.assertIs(report[field], False, msg=field)
        self.assertEqual(len(report["complete_same_state_receiver_wrenches"]), 21)
        # Independent golden digest of the 21 original source rows: changing a
        # receiver force, moment, datum, sign, factor or source identity fails.
        canonical = json.dumps(report["complete_same_state_receiver_wrenches"],
                               sort_keys=True, separators=(",", ":"))
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(),
                         "63cf2ad4d39762ee541ca06a733e1a73de15cce7e915e4141d9e6c2ef830ad27")
        for row in report["hardware_requirements"]:
            profile = row["declared_profile_screen"]
            for field in ("quarter_thread_condition_met", "sufficient_external_nut_envelope_coverage_met",
                          "physical_tip_requirement_met"):
                self.assertTrue(profile[field])
            self.assertFalse(profile["matched_nut_functional_fit_established"])

    def test_declared_profile_boundaries(self):
        hardware = {
            "member_requirements": [{"conservative_interval_underhead_mm_at_max_published_head_washer": [2.032, 90.932]},
                                    {"conservative_interval_underhead_mm_at_max_published_head_washer": [90.932, 129.032]}],
            "nut_and_tip_requirements": {
                "full_thread_sufficient_profile_condition": {"continuous_full_form_interval_must_cover_mm": [129.5908, 136.8044]},
                "minimum_physical_tip_target_underhead_mm": 140.6144,
            },
        }
        boundary = joint.profile_screen(hardware, runout_start=119.507,
                                       full_form_interval=(129.5908, 136.8044), tip=140.6144)
        self.assertAlmostEqual(boundary["thread_bearing_fractions"][1], 0.25)
        # Use a tiny inward margin here because the hand-entered decimal interval
        # produces a binary floating-point fraction just above exactly one quarter.
        valid = joint.profile_screen(hardware, runout_start=119.507000001,
                                    full_form_interval=(129.5908, 136.8044), tip=140.6144)
        self.assertTrue(valid["quarter_thread_condition_met"])
        for start, full, tip, field in (
            (119.506, (129.5908, 136.8044), 140.6144, "quarter_thread_condition_met"),
            (127, (129.5909, 136.8044), 140.6144, "sufficient_external_nut_envelope_coverage_met"),
            (127, (128, 136.8043), 140.6144, "sufficient_external_nut_envelope_coverage_met"),
            (127, (128, 136.8044), 140.6143, "physical_tip_requirement_met"),
        ):
            self.assertFalse(joint.profile_screen(hardware, runout_start=start,
                                                  full_form_interval=full, tip=tip)[field])
        with self.assertRaises(ValueError):
            joint.profile_screen(hardware, runout_start=130, full_form_interval=(128, 136), tip=141)


if __name__ == "__main__":
    unittest.main()
