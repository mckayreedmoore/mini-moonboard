from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("capture_reader", HERE / "capture_reader.py")
reader = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = reader
assert spec.loader is not None
spec.loader.exec_module(reader)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CaptureSinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("cc") or shutil.which("gcc")
        if compiler is None:
            raise unittest.SkipTest("a C compiler is required for the offline sink harness")
        cls.temp = tempfile.TemporaryDirectory(prefix="ccxcap-offline-")
        temp = Path(cls.temp.name)
        cls.default_harness = temp / "sink-harness"
        cls.smallcap_harness = temp / "sink-harness-smallcap"
        common = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-I", str(HERE)]
        source = str(HERE / "tests/sink_harness.c")
        subprocess.run([*common, source, "-lm", "-o", str(cls.default_harness)], check=True,
                       capture_output=True, text=True)
        subprocess.run([*common, "-DWJCC_MAX_BYTES=8192", source, "-lm", "-o",
                        str(cls.smallcap_harness)], check=True, capture_output=True, text=True)
        cls.bindings = {
            "input_sha256": sha((HERE / "coupon/input/contact_touch.inp").read_bytes()),
            "include_closure_sha256": sha(b""),
            "source_archive_sha256": sha((HERE / "build/context/source.tar.bz2").read_bytes()),
            "patch_sha256": sha((HERE / "build/context/capture.patch").read_bytes()),
            "binary_sha256": sha(cls.default_harness.read_bytes()),
            "pair_roster_sha256": sha(b"synthetic-pair-roster-v1"),
            "face_roster_sha256": sha(b"synthetic-face-roster-v1"),
        }

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_sink(self, harness=None, mode="positive", expected_faces=2, cap=reader.CAPTURE_CAP,
                 extra_env=None):
        harness = harness or self.default_harness
        with tempfile.TemporaryDirectory(prefix="ccxcap-output-") as temp_dir:
            output = Path(temp_dir) / "capture.tsv"
            env = os.environ.copy()
            env.update({
                "CCX_CONTACT_CAPTURE_PATH": str(output),
                "CCX_CAPTURE_INPUT_SHA256": self.bindings["input_sha256"],
                "CCX_CAPTURE_INCLUDE_SHA256": self.bindings["include_closure_sha256"],
                "CCX_CAPTURE_SOURCE_SHA256": self.bindings["source_archive_sha256"],
                "CCX_CAPTURE_PATCH_SHA256": self.bindings["patch_sha256"],
                "CCX_CAPTURE_BINARY_SHA256": self.bindings["binary_sha256"],
                "CCX_CAPTURE_PAIR_SHA256": self.bindings["pair_roster_sha256"],
                "CCX_CAPTURE_FACE_SHA256": self.bindings["face_roster_sha256"],
                "CCX_CAPTURE_EXPECTED_FACES": str(expected_faces),
                "CCX_CAPTURE_EXPECTED_TIES": "1",
            })
            if extra_env:
                env.update(extra_env)
            proc = subprocess.run([str(harness), mode], env=env, capture_output=True, text=True, check=True)
            self.assertEqual(proc.stdout, "")
            data = output.read_bytes()
            return data

    def expected(self, faces=2, cap=reader.CAPTURE_CAP):
        return {"tie_count": 1, "face_count_by_tie": {"1": faces},
                "face_ids_by_tie": {"1": [101 + i for i in range(faces)]},
                "minimum_accepted_links": 1, "require_linear_law": True,
                "require_force": True, "require_energy": True,
                "capture_byte_cap": cap, "run_bindings": self.bindings}

    def test_positive_sink_stream_identity_join_force_energy_and_acceptance(self):
        data = self.run_sink()
        result = reader.validate_capture(data, self.expected())
        self.assertEqual(result["status"], "PASS_CAPTURE_STRUCTURE")
        self.assertEqual(result["generation_count"], 2)
        self.assertEqual(len(result["accepted_states"]), 1)
        self.assertEqual(result["accepted_states"][0]["iteration"], 2)
        self.assertEqual(result["trial_rows"], 2)
        for summary in result["trial_summaries"]:
            law = reader.linear_penalty_point(1.0, 10.0, -0.1, (0.0, 0.0, 1.0))
            self.assertAlmostEqual(law["pressure"], 1.0)
            self.assertEqual(summary["force_on_slave_N"], law["force"])
            self.assertAlmostEqual(summary["sum_abs_point_force_N"], 1.0)
            self.assertAlmostEqual(summary["stored_energy_N_mm"], law["energy"])
        text = data.decode()
        join_rows = [line.split("\t") for line in text.splitlines() if line.startswith("STATE_JOIN\t")]
        gen2 = next(row for row in join_rows if row[1] == "2")
        self.assertEqual([int(gen2[i]) for i in (9, 10, 11, 12, 13, 14)], [1, 2, 0, 0, 1, 1])

    def test_uninstrumented_seed_end_hook_is_noop_after_iteration_link(self):
        data = self.run_sink(mode="seed")
        result = reader.validate_capture(data, self.expected())
        self.assertEqual(result["generation_count"], 1)
        rows = [line.split("\t") for line in data.decode().splitlines()]
        self.assertEqual(sum(row[0] == "GEN_END" for row in rows), 1)
        self.assertEqual(rows[-1][0], "RUN_END")

    def test_reader_rejects_identity_reason_span_join_and_acceptance_mutations(self):
        source = self.run_sink().decode()
        self.assertEqual(reader.validate_capture(source, self.expected())["status"], "PASS_CAPTURE_STRUCTURE")

        def mutate_record(record, field, transform):
            lines = source.splitlines()
            for i, line in enumerate(lines):
                cells = line.split("\t")
                if cells[0] == record:
                    cells[field] = transform(cells[field])
                    lines[i] = "\t".join(cells)
                    break
            else:
                self.fail(f"missing test record {record}")
            return "\n".join(lines) + "\n"

        bad = mutate_record("MAP_SUMMARY", 16, lambda value: str(int(value) + 1))
        with self.assertRaises(reader.CaptureError): reader.validate_capture(bad, self.expected())

        # Keep the total reason histogram unchanged while moving one live
        # projection failure into a constitutive-clearance exclusion. The
        # source-reason partition must still reject this reinterpretation.
        reason_lines = source.splitlines()
        for index, line in enumerate(reason_lines):
            cells = line.split("\t")
            if cells[0] == "MAP_SUMMARY" and cells[1] == "1" and cells[7] == "1":
                self.assertGreater(int(cells[17]), 0)
                cells[17] = str(int(cells[17]) - 1)
                cells[18] = str(int(cells[18]) + 1)
                reason_lines[index] = "\t".join(cells)
                break
        else:
            self.fail("missing MAP_SUMMARY row for source-reason partition control")
        bad = "\n".join(reason_lines) + "\n"
        with self.assertRaises(reader.CaptureError): reader.validate_capture(bad, self.expected())

        aleatoric_lines = source.splitlines()
        for index, line in enumerate(aleatoric_lines):
            cells = line.split("\t")
            if cells[0] == "MAP_SUMMARY" and cells[1] == "1" and cells[7] == "1":
                self.assertGreater(int(cells[18]), 0)
                cells[18] = str(int(cells[18]) - 1)
                cells[20] = str(int(cells[20]) + 1)
                aleatoric_lines[index] = "\t".join(cells)
                break
        else:
            self.fail("missing MAP_SUMMARY row for aleatoric policy control")
        bad = "\n".join(aleatoric_lines) + "\n"
        with self.assertRaises(reader.CaptureError): reader.validate_capture(bad, self.expected())

        bad = mutate_record("FACE", 8, lambda value: str(int(value) + 1))
        with self.assertRaises(reader.CaptureError): reader.validate_capture(bad, self.expected())
        bad = mutate_record("FACE", 5, lambda value: str(int(value) + 900))
        with self.assertRaises(reader.CaptureError): reader.validate_capture(bad, self.expected())
        bad = mutate_record("STATE_JOIN", 10, lambda value: str(int(value) + 1))
        with self.assertRaises(reader.CaptureError): reader.validate_capture(bad, self.expected())
        bad = mutate_record("ITERATION_LINK", 8, lambda value: "0" if value == "1" else "1")
        with self.assertRaises(reader.CaptureError): reader.validate_capture(bad, self.expected())
        bad = mutate_record("TRIAL_SUMMARY", 17, lambda value: "NaN")
        with self.assertRaises(reader.CaptureError): reader.validate_capture(bad, self.expected())
        bad = mutate_record("GEN_BEGIN", 6, lambda value: str(int(value) + 1))
        with self.assertRaises(reader.CaptureError): reader.validate_capture(bad, self.expected())

    def test_writer_fails_closed_on_unclassified_duplicate_and_span_loss(self):
        for mode in ("unclassified", "duplicate", "missing"):
            data = self.run_sink(mode=mode)
            self.assertTrue(data.endswith(b"\n"))
            end = data.decode().splitlines()[-1].split("\t")
            self.assertEqual(end[0], "RUN_END")
            self.assertEqual(end[8], "1")
            self.assertEqual(end[9], "0")

    def test_invalid_face_roster_binding_fails_closed(self):
        for count in ("2junk", "13002"):
            data = self.run_sink(extra_env={"CCX_CAPTURE_EXPECTED_FACES": count})
            rows = [line.split("\t") for line in data.decode().splitlines()]
            begin = next(row for row in rows if row[0] == "RUN_BEGIN")
            end = rows[-1]
            self.assertEqual(begin[12], "0")
            self.assertEqual(end[8], "1")
            self.assertEqual(end[9], "0")

    def test_unavailable_energy_stays_na_not_zero(self):
        data = self.run_sink(mode="noenergy")
        expected = self.expected()
        expected["require_energy"] = False
        result = reader.validate_capture(data, expected)
        self.assertEqual(len(result["trial_summaries"]), 2)
        self.assertTrue(all(not row["energy_enabled"] and row["stored_energy_N_mm"] is None
                            for row in result["trial_summaries"]))

    def test_writer_byte_cap_leaves_footer_and_marks_overflow(self):
        data = self.run_sink(self.smallcap_harness, mode="cap", expected_faces=200, cap=8192)
        self.assertLessEqual(len(data), 8192)
        self.assertTrue(data.endswith(b"\n"))
        end = data.decode().splitlines()[-1].split("\t")
        self.assertEqual(end[0], "RUN_END")
        self.assertEqual(end[7], "1")
        self.assertEqual(end[9], "0")
        with self.assertRaises(reader.CaptureError):
            reader.validate_capture(data, self.expected(faces=200, cap=8192))
        with self.assertRaises(reader.CaptureError):
            reader.check_capture_size(8193, 8192)

    def test_force_and_energy_convention_rejects_invalid_analytic_inputs(self):
        value = reader.linear_penalty_point(2.0, 5.0, -0.2, (0.0, 0.0, 1.0))
        self.assertEqual(value["pressure"], 1.0)
        self.assertEqual(value["force"], (0.0, 0.0, -2.0))
        self.assertEqual(value["energy"], 0.2)
        self.assertIsNone(reader.linear_penalty_point(2.0, 5.0, -0.2,
                                                     (0.0, 0.0, 1.0), energy_enabled=False)["energy"])
        with self.assertRaises(reader.CaptureError):
            reader.linear_penalty_point(-1.0, 5.0, -0.2, (0.0, 0.0, 1.0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
