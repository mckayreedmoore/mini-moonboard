"""Focused known-answer tests for the independent raw-DAT source oracle."""

from __future__ import annotations

import unittest

import raw_dat_oracle as oracle


def dat_pair(*, displacement_row: str | None = None, force_row: str | None = None) -> str:
    displacement_row = displacement_row or "1 1.250D-03 -2.00E+00 0.0"
    force_row = force_row or "1 -4.00E+00 2.500D-01 0.0"
    return (
        "displacements (vx,vy,vz) for set ALLN and time 1.000000D+00\n"
        f"{displacement_row}\n"
        "forces (fx,fy,fz) for set ALLN and time 1.000000D+00\n"
        f"{force_row}\n"
    )


class RawDatParserTests(unittest.TestCase):
    def test_parses_d_exponents_and_keeps_printed_token_radii(self) -> None:
        state = oracle.parse_dat_text(dat_pair(), expected_count=1, expected_nodes={1})[1.0]

        self.assertEqual(state["u_tokens"][1], ["1.250D-03", "-2.00E+00", "0.0"])
        self.assertEqual(state["u"][1], [0.00125, -2.0, 0.0])
        self.assertAlmostEqual(state["u_radius"][1][0], 0.0000005)
        self.assertAlmostEqual(state["u_radius"][1][1], 0.005)
        self.assertAlmostEqual(state["u_radius"][1][2], 0.05)
        self.assertAlmostEqual(state["rf_radius"][1][0], 0.005)
        self.assertAlmostEqual(oracle.half_last_place("-3D+02"), 50.0)

    def test_rejects_missing_force_block(self) -> None:
        source = "displacements (vx,vy,vz) for set ALLN and time 1.0\n1 0 0 0\n"
        with self.assertRaisesRegex(oracle.OracleError, "unmatched ALLN"):
            oracle.parse_dat_text(source, expected_count=1)

    def test_rejects_duplicate_block_and_duplicate_node(self) -> None:
        duplicate_block = dat_pair() + "forces (fx,fy,fz) for set ALLN and time 1.000000D+00\n1 0 0 0\n"
        with self.assertRaisesRegex(oracle.OracleError, "duplicate ALLN rf block"):
            oracle.parse_dat_text(duplicate_block, expected_count=1)

        duplicate_node = dat_pair(force_row="1 0 0 0\n1 0 0 0")
        with self.assertRaisesRegex(oracle.OracleError, "duplicate node"):
            oracle.parse_dat_text(duplicate_node, expected_count=1)

    def test_rejects_missing_node_and_nonfinite_token(self) -> None:
        with self.assertRaisesRegex(oracle.OracleError, "node inventory differs"):
            oracle.parse_dat_text(dat_pair(), expected_count=1, expected_nodes={1, 2})

        with self.assertRaisesRegex(oracle.OracleError, "invalid numeric token"):
            oracle.parse_dat_text(dat_pair(force_row="1 nan 0 0"), expected_count=1)

    def test_deck_parser_preserves_continued_c3d20_connectivity(self) -> None:
        nodes = "".join(f"{node},{node}.0,0.0,0.0\n" for node in range(1, 21))
        deck = (
            "*NODE\n"
            + nodes
            + "*ELEMENT,TYPE=C3D20,ELSET=body\n"
            + "1,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15\n"
            + "16,17,18,19,20\n"
            + "*STATIC\n0.1,1.0,1e-8,0.1\n"
        )

        parsed = oracle.parse_deck_text(deck)

        self.assertEqual(parsed["elements"][1]["type"], "C3D20")
        self.assertEqual(parsed["elements"][1]["nodes"], list(range(1, 21)))


class SourceRecoveryTests(unittest.TestCase):
    def test_common_floor_point_matches_explicit_endpoints_without_collapsing_overrides(self) -> None:
        actual = {"local_dof": 2, "point": [1., 2., 3.]}
        expected = {**actual, "first_point": [1., 2., 3.], "second_point": [1., 2., 3.]}
        oracle._compare_channel_rows([actual], [expected], "common floor point", {})
        actual["second_point"] = [1., 2., 4.]
        with self.assertRaises(oracle.OracleError):
            oracle._compare_channel_rows([actual], [expected], "changed endpoint", {})

    def test_spring2_uses_endpoint_difference_for_force_on_first(self) -> None:
        force, radius = oracle.recover_spring2_scalar(
            {10: [-4.0, 0.0, 0.0], 20: [4.0, 0.0, 0.0]},
            {10: [0.001, 0.001, 0.001], 20: [0.001, 0.001, 0.001]},
            [10, 20],
            1,
        )

        self.assertEqual(force, 4.0)
        self.assertEqual(radius, 0.001)

    def test_springa_projects_q_endpoint_force_onto_physical_axis(self) -> None:
        force, radius = oracle.recover_springa_scalar(
            {3: [3.0, 4.0, 0.0], 4: [-3.0, -4.0, 0.0]},
            {3: [0.01, 0.02, 0.03], 4: [0.01, 0.01, 0.01]},
            [3, 4],
            [0.6, 0.8, 0.0],
        )

        self.assertEqual(force, 5.0)
        self.assertAlmostEqual(radius, 0.022)

    def test_selected_floor_removes_scaled_source_load_and_keeps_rf_radius(self) -> None:
        force, radius = oracle.recover_selected_floor_scalar(3.5, 0.012, 2.0, 0.45)

        self.assertAlmostEqual(force, 2.6)
        self.assertEqual(radius, 0.012)

    def test_released_floor_accepts_only_zero_containing_carryover_interval(self) -> None:
        force, radius = oracle.verify_inactive_floor_zero(
            {8: [0.0002, -0.0004, 0.0]},
            {8: [0.001, 0.001, 0.001]},
            8,
        )

        self.assertEqual(force, [0.0002, -0.0004, 0.0])
        self.assertEqual(radius, [0.001, 0.001, 0.001])
        with self.assertRaisesRegex(oracle.OracleError, "interval excludes zero"):
            oracle.verify_inactive_floor_zero(
                {8: [0.002, 0.0, 0.0]},
                {8: [0.001, 0.001, 0.001]},
                8,
            )

    def test_rejects_missing_spring_endpoint(self) -> None:
        with self.assertRaisesRegex(oracle.OracleError, "endpoint is absent"):
            oracle.recover_spring2_scalar({1: [0.0, 0.0, 0.0]}, {1: [0.0, 0.0, 0.0]}, [1, 2], 1)


if __name__ == "__main__":
    unittest.main()
