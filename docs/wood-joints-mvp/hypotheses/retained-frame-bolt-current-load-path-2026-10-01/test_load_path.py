"""Bounded signed-action, complete-boundary and refusal checks."""

import copy
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("retained_load_path_test", HERE/"produce.py")
producer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(producer)


class LoadPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = producer.build()
        cls.features = producer.read(producer.FEATURE+"axis-features.json")
        cls.model = producer.read(cls.report["case_sources"]["a1-rear"]["model"]["path"])
        cls.response = producer.read(cls.report["case_sources"]["a1-rear"]["response"]["path"])
        spec = importlib.util.spec_from_file_location("retained_test_math", producer.ROOT/producer.EXPORT)
        cls.method = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.method)

    def test_complete_current_census_and_simultaneous_states(self):
        report = self.report
        self.assertEqual(report["counts"]["bolt_states"], 252)
        self.assertEqual(report["counts"]["complete_body_states"], 168)
        self.assertEqual(sum(len(bolt["combined_receiver_actions"]) for state in report["states"]
                             for bolt in state["bolt_states"].values()), 504)
        self.assertFalse(set(report["axis_register"]) & set(report["candidate_bolt_axis_ids_separate"]))
        for case in ("a1-rear", "a12-rear", "k12-rear"):
            self.assertEqual(report["cases"][case]["boundary_scalar_count"], 720)
            states = [s for s in report["states"] if s["case_id"] == case]
            self.assertEqual(tuple(s["load_factor"] for s in states), producer.FACTORS)
            for state in states:
                self.assertEqual(set(state["bolt_states"]), set(report["axis_register"]))
                for bolt in state["bolt_states"].values():
                    self.assertEqual(set(bolt["combined_receiver_actions"]), {"first", "second"})
                self.assertEqual(len(state["interface_actions"]), 568)
                self.assertEqual(set(state["body_balances"]), set(report["receiver_bodies"]))
        for key in producer.ACCEPTANCE+("joint_accepted", "fabrication_release", "native_solve_executed"):
            self.assertIs(report[key], False)

    def test_every_current_receiver_port_and_physical_load_is_present(self):
        members = set(self.report["receiver_bodies"])
        expected = {r["name"] for r in self.model["raw_source_carrier_law_inventory_rows"]
                    if r["first_body"] in members or r["second_body"] in members}
        state = self.report["states"][0]
        self.assertEqual(set(state["interface_actions"]), expected)
        self.assertTrue(any(r["role"] == "candidate_bolt_lateral_plane"
                            for r in state["interface_actions"].values() if "role" in r))
        self.assertTrue(state["floor_tangent_state_counts"])
        for body, balance in state["body_balances"].items():
            loads = self.model["physical_body_loads"][body]
            expected_force = [state["load_factor"] * sum(f[i] for f in loads.values()) for i in range(3)]
            for actual, expected_value in zip(balance["external_load_wrench"]["force_xyz_n"], expected_force, strict=True):
                self.assertAlmostEqual(actual, expected_value, places=8)
            self.assertIs(balance["origin_balance_gate_applied"], False)

    def test_wrench_known_answer_preserves_signed_vectors_and_offsets(self):
        lateral = {"role": "retained_bolt_lateral_plane", "first": "a", "second": "b",
                   "point": [2., 3., 4.], "force_on_first_xyz_n": [1., -2., 3.],
                   "force_on_second_xyz_n": [-1., 2., -3.], "force_rounding_radius_xyz_n": [.1, .2, .3]}
        axial = {"role": "physical_bolt_outer_seat_tension", "first": "a", "second": "b",
                 "point": [4., 3., 4.], "first_point": [4., 3., 4.], "second_point": [8., 3., 4.],
                 "force_on_first_xyz_n": [2., 0., 0.], "force_on_second_xyz_n": [-2., 0., 0.],
                 "force_rounding_radius_xyz_n": [.05, 0., 0.]}
        result = producer.endpoint_wrenches(lateral, axial, {"a": [1., 1., 1.], "b": [2., 2., 2.]}, self.method)
        self.assertEqual(result["first"]["force_xyz_n"], [3., -2., 3.])
        self.assertEqual(result["first"]["moment_about_reporting_datum_xyz_nmm"], [12., 6., -8.])
        self.assertEqual(result["first"]["moment_about_origin_xyz_nmm"], [17., 6., -13.])
        for actual, expected in zip(result["first"]["moment_radius_about_reporting_datum_xyz_nmm"],
                                    [1.2, .75, .5], strict=True):
            self.assertAlmostEqual(actual, expected)

    def test_missing_duplicate_axes_and_receivers_refuse(self):
        for mutation in ("missing_axis", "duplicate_axis", "missing_receiver"):
            features = copy.deepcopy(self.features)
            rows = features["source_axis_groups"]["retained_frame_bolt_axes"]["axes"]
            if mutation == "missing_axis":
                rows.pop()
            elif mutation == "duplicate_axis":
                rows.append(copy.deepcopy(rows[0]))
            else:
                rows[0]["receiver_memberships"].pop()
            with self.assertRaises(ValueError):
                producer.geometry_register(features, {})

    def test_missing_projection_and_wrong_owner_refuse(self):
        axis_id = "lumber_leg_bolt_left_1"
        geometry = self.report["axis_register"][axis_id]
        projection = producer.read(producer.PROJECTION+"projection-contract.json")["rows"]
        missing = [r for r in projection if r["source_group"] != "SPR1515"]
        with self.assertRaisesRegex(ValueError, "physical projection row"):
            producer.bind_axis_model(axis_id, geometry, self.model, missing)
        changed = copy.deepcopy(self.model)
        row = next(r for r in changed["raw_source_carrier_law_inventory_rows"] if r["group"] == "SPR1515")
        row["physical_owner"]["first"] = "base_side_right"
        with self.assertRaisesRegex(ValueError, "owner/receiver"):
            producer.bind_axis_model(axis_id, geometry, changed, projection)

    def test_false_source_law_gates_and_wrong_element_refuse(self):
        bindings = self.report["cases"]["a1-rear"]["retained_scalar_bindings"]["lumber_leg_bolt_left_1"]
        for mutation in ("law_gate", "wrong_element", "duplicate_scalar"):
            increment = copy.deepcopy(self.response["increments"][0])
            component = next(r for r in increment["springa_components"] if r["source_row_id"] == bindings[2]["source_row_id"])
            if mutation == "law_gate":
                component["table_force_interval_intersects_native_rf"] = False
            elif mutation == "wrong_element":
                component["element"] += 1
            else:
                increment["springa_components"].append(copy.deepcopy(component))
            with self.assertRaises(ValueError):
                producer.scalar_actions(bindings, increment)

    def test_changed_source_bytes_refuse(self):
        with tempfile.TemporaryDirectory(prefix="retained-frame-pin-test-") as directory:
            source = Path(directory)/"source.json"
            source.write_text('{"case":"a1-rear"}\n')
            digest = producer.sha(source)
            pins = {}
            producer.pin_file(str(source), digest, pins)
            source.write_text('{"case":"a12-rear"}\n')
            with self.assertRaisesRegex(ValueError, "source byte changed"):
                producer.pin_file(str(source), digest, pins)

    def test_replay_is_identical_across_process_hash_seeds(self):
        with tempfile.TemporaryDirectory(prefix="retained-frame-replay-test-") as directory:
            hashes = []
            for seed in ("11", "73"):
                output = Path(directory)/f"replay-{seed}.json"
                environment = dict(os.environ, PYTHONHASHSEED=seed)
                with output.open("wb") as stream:
                    subprocess.run([str(producer.ROOT/".venv/bin/python"), str(HERE/"produce.py"), "--check"],
                                   cwd=producer.ROOT, env=environment, stdout=stream, check=True)
                hashes.append(producer.sha(output))
            self.assertEqual(hashes[0], hashes[1])


if __name__ == "__main__":
    unittest.main()
