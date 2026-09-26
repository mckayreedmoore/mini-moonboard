from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARSER_PATH = HERE / "parse_contact_energy_point_map.py"
SPEC = importlib.util.spec_from_file_location("point_map_parser", PARSER_PATH)
assert SPEC and SPEC.loader
parser = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parser)

FIXTURE_ROOT = HERE.parent / "contact-energy-point-map-attempt01"
C_FIXTURE = FIXTURE_ROOT / "parent-emitter-harness-attempt01" / "pilot.wj-contact-energy-map.csv"
DAT_FIXTURE = FIXTURE_ROOT / "parent-fortran-harness-attempt01" / "printer-harness.dat"


class PointMapParserTests(unittest.TestCase):
    def write_sta(self, path: Path) -> None:
        path.write_text(
            "SUMMARY OF JOB INFORMATION\n"
            "  STEP INC ATT ITRS TOT TIME STEP TIME INC TIME\n"
            "     1 1 1 1 0.500000E-03 0.500000E-03 0.500000E-03\n"
            "     1 2 1 1 0.100000E-02 0.500000E-03 0.500000E-03\n"
            "     1 3 1 1 0.150000E-02 0.500000E-03 0.500000E-03\n",
            encoding="ascii",
        )

    def test_actual_c_fixture_framing_and_sta_binding(self) -> None:
        blocks, incomplete = parser.parse_csv_blocks(C_FIXTURE)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(incomplete, [])
        with tempfile.TemporaryDirectory() as temporary:
            sta_path = Path(temporary) / "pilot.sta"
            self.write_sta(sta_path)
            accepted, rejected = parser.read_sta(sta_path)
        self.assertEqual(len(rejected), 0)
        matched = parser.accepted_blocks(blocks, accepted)
        self.assertEqual([(b["state_key"], len(b["points"])) for b, _ in matched], [((1, 1), 2), ((1, 2), 2), ((1, 3), 2)])
        self.assertEqual([int(b["state"]["nener"]) for b, _ in matched], [1, 1, 0])

    def test_truncated_block_is_not_admitted(self) -> None:
        lines = C_FIXTURE.read_text(encoding="ascii").splitlines()
        lines.remove(next(line for line in lines if line.startswith("END,1,1,")))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "partial.csv"
            path.write_text("\n".join(lines) + "\n", encoding="ascii")
            blocks, incomplete = parser.parse_csv_blocks(path)
        self.assertEqual([b["state_key"] for b in blocks], [(1, 2), (1, 3)])
        self.assertEqual(incomplete[0]["reason"], "new STATE before END")

    def test_fortran_fixture_records_and_formula(self) -> None:
        parsed = parser.parse_dat(DAT_FIXTURE)
        complete = [row for row in parsed["cep"] if row.get("complete")]
        self.assertEqual(len(complete), 3)
        self.assertEqual(len(parsed["eif"]), 3)
        self.assertEqual(len(parsed["cels"]), 0)
        self.assertEqual(parser.point_formula(parser.dec("2"), parser.dec("5"), parser.dec("-0.1")), parser.dec("0.5"))

    def test_distinct_harnesses_do_not_false_join(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sta_path = Path(temporary) / "pilot.sta"
            self.write_sta(sta_path)
            result = parser.summarize_first(C_FIXTURE, DAT_FIXTURE, sta_path)
        self.assertEqual(result["csv"]["selected_time_s"], 0.0005)
        self.assertEqual(result["csv"]["point_count"], 2)
        self.assertEqual(result["dat"]["complete_WJ_CEP_point_value_records_at_selected_time"], 0)
        self.assertEqual(result["join"]["matched_point_rows"], 0)


if __name__ == "__main__":
    unittest.main()
