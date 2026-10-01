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
        cls.io_failure_harness = temp / "sink-harness-io-failure"
        cls.fixed_pid_harness = temp / "sink-harness-fixed-pid"
        common = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-I", str(HERE)]
        source = str(HERE / "tests/sink_harness.c")
        subprocess.run([*common, source, "-lm", "-o", str(cls.default_harness)], check=True,
                       capture_output=True, text=True)
        subprocess.run([*common, "-DWJCC_MAX_BYTES=8192", source, "-lm", "-o",
                        str(cls.smallcap_harness)], check=True, capture_output=True, text=True)
        subprocess.run([*common, "-DWJCC_TEST_IO_FAILURE", source, "-lm", "-o",
                        str(cls.io_failure_harness)], check=True, capture_output=True, text=True)
        subprocess.run([*common, "-DWJCC_TEST_FIXED_PID", source, "-lm", "-o",
                        str(cls.fixed_pid_harness)], check=True, capture_output=True, text=True)
        cls.bindings = {
            "input_sha256": sha(b"synthetic offline capture input"),
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

    def run_sink(self, harness=None, mode="positive", expected_faces=2, expected_ties=1,
                 cap=reader.CAPTURE_CAP, extra_env=None):
        exists, data = self.run_sink_with_status(harness, mode, expected_faces,
                                                 expected_ties, cap, extra_env)
        self.assertTrue(exists, f"sink did not publish capture for mode {mode}")
        assert data is not None
        return data

    def run_sink_with_status(self, harness=None, mode="positive", expected_faces=2,
                             expected_ties=1, cap=reader.CAPTURE_CAP, extra_env=None):
        harness = harness or self.default_harness
        with tempfile.TemporaryDirectory(prefix="ccxcap-output-") as temp_dir:
            output = Path(temp_dir) / "capture.tsv"
            env = self.capture_env(output, expected_faces, expected_ties, extra_env)
            proc = subprocess.run([str(harness), mode], env=env, capture_output=True, text=True, check=True)
            self.assertEqual(proc.stdout, "")
            return output.is_file(), output.read_bytes() if output.is_file() else None

    def capture_env(self, output, expected_faces=2, expected_ties=1, extra_env=None):
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
            "CCX_CAPTURE_EXPECTED_TIES": str(expected_ties),
        })
        if extra_env:
            env.update(extra_env)
        return env

    def expected(self, faces=2, cap=reader.CAPTURE_CAP, ties=1):
        by_tie = {"1": faces} if ties == 1 else {"1": 1, "2": 1}
        ids = {"1": [101 + i for i in range(faces)]} if ties == 1 else {"1": [101], "2": [201]}
        return {"tie_count": ties, "face_count_by_tie": by_tie,
                "face_ids_by_tie": ids,
                "minimum_accepted_links": 1, "require_linear_law": True,
                "require_force": True,
                "capture_byte_cap": cap, "run_bindings": self.bindings}

    def test_positive_sink_stream_identity_join_force_energy_and_acceptance(self):
        data = self.run_sink()
        result = reader.validate_capture(data, self.expected())
        self.assertEqual(result["status"], "PASS_CAPTURE_STRUCTURE")
        self.assertEqual(result["generation_count"], 2)
        self.assertEqual(len(result["accepted_states"]), 1)
        self.assertEqual(result["accepted_states"][0]["iteration"], 2)
        self.assertEqual(result["trial_rows"], 2)
        links = [line.split("\t") for line in data.decode().splitlines()
                 if line.startswith("ITERATION_LINK\t")]
        self.assertEqual([int(row[5]) for row in links], [1, 2])
        self.assertEqual([int(row[7]) for row in links], [0, 1])
        self.assertEqual([int(row[8]) for row in links], [0, 1])
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

    def test_two_step_sink_lifecycle_keeps_buffers_and_writes_one_job_footer(self):
        data = self.run_sink(mode="two-step")
        result = reader.validate_capture(data, self.expected())
        self.assertEqual(result["generation_count"], 2)
        self.assertEqual(len(result["accepted_states"]), 2)
        rows = [line.split("\t") for line in data.decode().splitlines()]
        self.assertEqual(sum(row[0] == "RUN_BEGIN" for row in rows), 1)
        self.assertEqual(sum(row[0] == "RUN_END" for row in rows), 1)
        self.assertEqual(sum(row[0] == "GEN_BEGIN" for row in rows), 2)
        self.assertEqual(sum(row[0] == "GEN_END" for row in rows), 2)
        self.assertEqual([int(row[2]) for row in rows if row[0] == "GEN_BEGIN"], [1, 2])

    def test_explicit_multistep_route_does_not_publish_unlinked_generations(self):
        exists, data = self.run_sink_with_status(mode="explicit-multistep")
        self.assertFalse(exists)
        self.assertIsNone(data)

    def test_missing_capture_path_leaves_generation_hooks_inert(self):
        exists, data = self.run_sink_with_status(
            mode="disabled-path-multistep",
            extra_env={"CCX_CONTACT_CAPTURE_PATH": ""},
        )
        self.assertFalse(exists)
        self.assertIsNone(data)

    def test_mixed_case_pass_two_is_optional_per_tie(self):
        data = self.run_sink(mode="mixed-pass2", expected_faces=2, expected_ties=2)
        result = reader.validate_capture(data, self.expected(ties=2))
        self.assertEqual(result["status"], "PASS_CAPTURE_STRUCTURE")
        rows = [line.split("\t") for line in data.decode().splitlines()]
        face_keys = {(int(r[2]), int(r[3])) for r in rows if r[0] == "FACE"}
        self.assertEqual(face_keys, {(1, 1), (1, 2), (2, 1)})
        map_keys = {(int(r[6]), int(r[7])) for r in rows if r[0] == "MAP_SUMMARY"}
        self.assertEqual(map_keys, {(1, 1), (1, 2), (2, 1)})
        self.assertNotIn((2, 2), map_keys)

    def test_writer_rejects_pass_two_face_identity_mismatch(self):
        for mode in ("bad-pass2-identity", "bad-pass2-offset", "bad-pass2-status"):
            with self.subTest(mode=mode):
                data = self.run_sink(mode=mode, expected_faces=2, expected_ties=2)
                rows = [line.split("\t") for line in data.decode().splitlines()]
                gen_end = next(row for row in rows if row[0] == "GEN_END")
                run_end = rows[-1]
                self.assertEqual(gen_end[9], "0")
                self.assertEqual(run_end[8:10], ["1", "0"])
                with self.assertRaises(reader.CaptureError):
                    reader.validate_capture(data, self.expected(ties=2))

    def test_reader_rejects_second_header_pass_two_identity_and_offset_mutations(self):
        source = self.run_sink(mode="mixed-pass2", expected_faces=2, expected_ties=2).decode()
        self.assertEqual(reader.validate_capture(source, self.expected(ties=2))["status"],
                         "PASS_CAPTURE_STRUCTURE")

        lines = source.splitlines()
        footer = next(i for i, line in enumerate(lines) if line.startswith("RUN_END\t"))
        duplicate_header = lines[:footer] + ["CCXCAP\t1"] + lines[footer:]
        with self.assertRaisesRegex(reader.CaptureError, "one leading CCXCAP"):
            reader.validate_capture("\n".join(duplicate_header) + "\n", self.expected(ties=2))

        def mutate_pass_two(field, transform):
            changed = source.splitlines()
            for i, line in enumerate(changed):
                cells = line.split("\t")
                if cells[0] == "FACE" and cells[3] == "2":
                    cells[field] = str(transform(int(cells[field])))
                    changed[i] = "\t".join(cells)
                    break
            else:
                self.fail("missing optional pass-two FACE row")
            return "\n".join(changed) + "\n"

        changed_identity = mutate_pass_two(5, lambda value: value + 1)
        with self.assertRaises(reader.CaptureError):
            reader.validate_capture(changed_identity, self.expected(ties=2))

        changed_offset = mutate_pass_two(6, lambda value: value + 10)
        changed_offset_lines = changed_offset.splitlines()
        for i, line in enumerate(changed_offset_lines):
            cells = line.split("\t")
            if cells[0] == "FACE" and cells[3] == "2":
                cells[7] = str(int(cells[7]) + 10)
                changed_offset_lines[i] = "\t".join(cells)
                break
        changed_offset = "\n".join(changed_offset_lines) + "\n"
        with self.assertRaises(reader.CaptureError):
            reader.validate_capture(changed_offset, self.expected(ties=2))

    def test_reader_rejects_missing_required_record_classes_and_footer_totals(self):
        source = self.run_sink().decode()
        record_classes = ("RUN_BEGIN", "GEN_BEGIN", "FACE", "MAP_SUMMARY", "GEN_END",
                          "STATE_JOIN", "STATE_CORRECTED", "TRIAL_SUMMARY",
                          "ITERATION_LINK", "RUN_END")
        for record in record_classes:
            with self.subTest(record=record):
                missing = "\n".join(
                    line for line in source.splitlines() if not line.startswith(record + "\t")
                ) + "\n"
                with self.assertRaises(reader.CaptureError):
                    reader.validate_capture(missing, self.expected())

        rows = source.splitlines()
        for i, line in enumerate(rows):
            if line.startswith("RUN_END\t"):
                fields = line.split("\t")
                fields[1] = str(int(fields[1]) + 1)
                rows[i] = "\t".join(fields)
                break
        with self.assertRaisesRegex(reader.CaptureError, "RUN_END generation/face totals"):
            reader.validate_capture("\n".join(rows) + "\n", self.expected())

    def test_reader_rejects_run_begin_provenance_hash_mismatch(self):
        rows = self.run_sink().decode().splitlines()
        begin = next(i for i, line in enumerate(rows) if line.startswith("RUN_BEGIN\t"))
        fields = rows[begin].split("\t")
        fields[2] = sha(b"different frozen input")
        rows[begin] = "\t".join(fields)
        with self.assertRaisesRegex(reader.CaptureError, "provenance differs"):
            reader.validate_capture("\n".join(rows) + "\n", self.expected())

    def test_reader_enforces_combined_candidate_cap_at_and_above_boundary(self):
        data = self.run_sink(mode="candidate-cap-boundary", expected_faces=1)
        result = reader.validate_capture(data, self.expected(faces=1))
        summary = next(row.split("\t") for row in data.decode().splitlines()
                       if row.startswith("MAP_SUMMARY\t"))
        self.assertEqual(int(summary[11]), reader.MAX_CANDIDATES_PER_GENERATION)
        self.assertEqual(result["status"], "PASS_CAPTURE_STRUCTURE")

        rows = data.decode().splitlines()
        for i, line in enumerate(rows):
            fields = line.split("\t")
            if fields[0] == "MAP_SUMMARY":
                fields[11] = fields[12] = fields[15] = str(reader.MAX_CANDIDATES_PER_GENERATION + 1)
                fields[18] = str(reader.MAX_CANDIDATES_PER_GENERATION + 1)
                rows[i] = "\t".join(fields)
                break
        with self.assertRaisesRegex(reader.CaptureError, "combined pass candidate cap"):
            reader.validate_capture("\n".join(rows) + "\n", self.expected(faces=1))

    def test_writer_enforces_candidate_cap_combined_across_passes(self):
        data = self.run_sink(mode="combined-pass-cap-overflow", expected_faces=1)
        rows = [line.split("\t") for line in data.decode().splitlines()]
        generation_end = next(row for row in rows if row[0] == "GEN_END")
        run_end = rows[-1]
        self.assertEqual(generation_end[9], "0")
        self.assertEqual(run_end[7], "1")
        self.assertEqual(run_end[9], "0")
        with self.assertRaises(reader.CaptureError):
            reader.validate_capture(data, self.expected(faces=1))

    def test_reader_enforces_combined_candidate_cap_across_both_passes(self):
        data = self.run_sink(mode="combined-pass-cap-boundary", expected_faces=1)
        result = reader.validate_capture(data, self.expected(faces=1))
        self.assertEqual(result["point_candidates"], reader.MAX_CANDIDATES_PER_GENERATION)
        map_rows = [line.split("\t") for line in data.decode().splitlines()
                    if line.startswith("MAP_SUMMARY\t")]
        self.assertEqual([int(row[7]) for row in map_rows], [1, 2])
        self.assertEqual([int(row[11]) for row in map_rows], [125000, 125000])

        rows = data.decode().splitlines()
        for i, line in enumerate(rows):
            fields = line.split("\t")
            if fields[0] == "GEN_BEGIN":
                fields[6] = "125001"
            elif fields[0] == "FACE":
                fields[7] = fields[8] = "125001"
            elif fields[0] == "MAP_SUMMARY":
                fields[10] = fields[11] = fields[13] = fields[17] = "125001"
            elif fields[0] == "GEN_END":
                fields[3] = fields[6] = "250002"
                fields[4] = "125001"
            elif fields[0] == "RUN_END":
                fields[3] = "250002"
            rows[i] = "\t".join(fields)
        mutated = "\n".join(rows) + "\n"
        self.assertEqual(len(mutated.encode()), len(data))
        mutated_rows = [line.split("\t") for line in rows]
        self.assertEqual(next(int(row[6]) for row in mutated_rows if row[0] == "GEN_BEGIN"), 125001)
        self.assertEqual([int(row[8]) for row in mutated_rows if row[0] == "FACE"], [125001, 125001])
        self.assertEqual([int(row[11]) for row in mutated_rows if row[0] == "MAP_SUMMARY"], [125001, 125001])
        self.assertTrue(all(int(row[11]) < reader.MAX_CANDIDATES_PER_GENERATION
                            for row in mutated_rows if row[0] == "MAP_SUMMARY"))
        self.assertEqual(next(int(row[6]) for row in mutated_rows if row[0] == "GEN_END"), 250002)
        self.assertEqual(next(int(row[3]) for row in mutated_rows if row[0] == "RUN_END"), 250002)
        with self.assertRaisesRegex(reader.CaptureError, "combined pass candidate cap"):
            reader.validate_capture(mutated, self.expected(faces=1))

    def test_writer_and_reader_fail_closed_when_nener_one_energy_is_incomplete(self):
        for mode in ("energy-missing-row", "energy-disabled-row", "energy-nonfinite-row",
                     "energy-aggregate-overflow"):
            with self.subTest(mode=mode):
                multiple_ties = mode == "energy-aggregate-overflow"
                expected = self.expected(ties=2) if multiple_ties else self.expected()
                data = self.run_sink(mode=mode, expected_faces=2 if multiple_ties else 2,
                                     expected_ties=2 if multiple_ties else 1)
                rows = [line.split("\t") for line in data.decode().splitlines()]
                gen = "1" if multiple_ties else "2"
                summary = next(row for row in rows
                               if row[0] == "TRIAL_SUMMARY" and row[1] == gen)
                link = next(row for row in rows
                            if row[0] == "ITERATION_LINK" and row[1] == gen)
                run_end = rows[-1]
                self.assertEqual(summary[21], "1")
                self.assertLess(int(summary[12]), int(summary[7]))
                self.assertEqual(summary[17], "NA")
                self.assertEqual(link[12], "0")
                self.assertEqual(run_end[8:10], ["1", "0"])
                with self.assertRaises(reader.CaptureError):
                    reader.validate_capture(data, expected)

    def test_reader_requires_nener_one_energy_even_if_caller_requests_permissive_mode(self):
        rows = self.run_sink().decode().splitlines()
        for i, line in enumerate(rows):
            fields = line.split("\t")
            if fields[0] == "TRIAL_SUMMARY" and fields[1] == "1":
                fields[12] = str(int(fields[12]) - 1)
                fields[17] = "NA"
                rows[i] = "\t".join(fields)
                break
        else:
            self.fail("missing energy-bearing trial summary")
        permissive_expectation = self.expected()
        permissive_expectation["require_energy"] = False
        with self.assertRaisesRegex(reader.CaptureError, "stored energy"):
            reader.validate_capture("\n".join(rows) + "\n", permissive_expectation)

    def test_reader_requires_force_rows_even_if_caller_requests_permissive_mode(self):
        rows = self.run_sink().decode().splitlines()
        for i, line in enumerate(rows):
            fields = line.split("\t")
            if fields[0] == "TRIAL_SUMMARY" and fields[1] == "2":
                fields[11] = "0"
                fields[13:17] = ["NA"] * 4
                rows[i] = "\t".join(fields)
                break
        else:
            self.fail("missing generated-trial force summary")
        permissive_expectation = self.expected()
        permissive_expectation["require_force"] = False
        with self.assertRaisesRegex(reader.CaptureError, "expected force resultant"):
            reader.validate_capture("\n".join(rows) + "\n", permissive_expectation)

    def test_post_convergence_link_closes_captured_iteration_and_cutback_identity(self):
        data = self.run_sink(mode="cutback-link")
        expected = self.expected()
        expected["minimum_accepted_links"] = 0
        result = reader.validate_capture(data, expected)
        self.assertEqual(result["accepted_states"], [])
        link = next(line.split("\t") for line in data.decode().splitlines()
                    if line.startswith("ITERATION_LINK\t"))
        self.assertEqual([int(link[i]) for i in (4, 5, 6, 7, 8)], [1, 1, 2, 1, 0])

    def test_successful_retry_after_cutback_resets_attempt_and_is_accepted(self):
        data = self.run_sink(mode="retry-accepted-reset")
        result = reader.validate_capture(data, self.expected())
        self.assertEqual(len(result["accepted_states"]), 1)
        self.assertEqual(result["accepted_states"][0]["attempt"], 2)
        link = next(line.split("\t") for line in data.decode().splitlines()
                    if line.startswith("ITERATION_LINK\t"))
        self.assertEqual([int(link[i]) for i in (4, 5, 6, 7, 8)], [2, 1, 1, 1, 1])

    def test_invalid_transition_emits_link_clears_pending_and_marks_footer_incomplete(self):
        data = self.run_sink(mode="invalid-transition")
        rows = [line.split("\t") for line in data.decode().splitlines()]
        links = [row for row in rows if row[0] == "ITERATION_LINK"]
        self.assertEqual(len(links), 1)
        self.assertEqual(rows[-1][0], "RUN_END")
        self.assertEqual(rows[-1][7:10], ["0", "1", "0"])
        with self.assertRaises(reader.CaptureError):
            reader.validate_capture(data, self.expected())

    def test_empty_eligible_state_joins_count_new_missing_and_allow_zero_zero_tie(self):
        data = self.run_sink(mode="empty-state-join", expected_faces=2, expected_ties=2)
        result = reader.validate_capture(data, self.expected(ties=2))
        self.assertEqual(result["status"], "PASS_CAPTURE_STRUCTURE")
        joins = [line.split("\t") for line in data.decode().splitlines()
                 if line.startswith("STATE_JOIN\t") and line.split("\t")[1] == "2"]
        tie1 = next(row for row in joins if row[6] == "1")
        tie2 = next(row for row in joins if row[6] == "2")
        self.assertEqual([int(tie1[i]) for i in range(9, 15)], [0, 0, 0, 1, 0, 0])
        self.assertEqual([int(tie2[i]) for i in range(9, 15)], [0, 0, 0, 0, 0, 0])

    def assert_current_empty_join_reports_old_missing(self, data, expected):
        result = reader.validate_capture(data, expected)
        self.assertEqual(result["status"], "PASS_CAPTURE_STRUCTURE")
        rows = [line.split("\t") for line in data.decode().splitlines()
                if line.startswith("STATE_JOIN\t") and line.split("\t")[1] == "2"
                and line.split("\t")[6] == "1"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(int(rows[0][11]), 1)

    def test_empty_current_state_join_reports_old_missing_and_rejects_skip_mutant(self):
        data = self.run_sink(mode="disappearing-state-join", expected_faces=2,
                             expected_ties=2)
        expected = self.expected(ties=2)
        self.assert_current_empty_join_reports_old_missing(data, expected)

        compiler = shutil.which("cc") or shutil.which("gcc")
        self.assertIsNotNone(compiler)
        with tempfile.TemporaryDirectory(prefix="ccxcap-empty-current-mutant-") as temp_dir:
            temp = Path(temp_dir)
            sink_path = temp / "capture-sink-skip-empty.inc"
            sink = (HERE / "capture-sink.inc").read_text()
            call = "  wjcc_join_previous();wjcc_emit_map_summaries();wjcc_emit_state_joins();"
            self.assertEqual(sink.count(call), 1)
            sink_path.write_text(sink.replace(
                call,
                "  if(wjcc_points_n!=0)wjcc_join_previous();wjcc_emit_map_summaries();wjcc_emit_state_joins();",
                1,
            ))

            include = '#include "../capture-sink.inc"'
            harness_source = (HERE / "tests/sink_harness.c").read_text()
            self.assertEqual(harness_source.count(include), 1)
            mutant_source = temp / "sink-harness-mutant.c"
            mutant_source.write_text(harness_source.replace(
                include, f'#include "{sink_path}"', 1
            ))
            mutant_harness = temp / "sink-harness-mutant"
            subprocess.run([
                compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-I", str(HERE),
                str(mutant_source), "-lm", "-o", str(mutant_harness),
            ], check=True, capture_output=True, text=True)

            output = temp / "mutant-capture.tsv"
            mutant_binary_sha = sha(mutant_harness.read_bytes())
            mutant_bindings = dict(self.bindings)
            mutant_bindings["binary_sha256"] = mutant_binary_sha
            mutant_expected = self.expected(ties=2)
            mutant_expected["run_bindings"] = mutant_bindings
            env = self.capture_env(
                output, expected_faces=2, expected_ties=2,
                extra_env={"CCX_CAPTURE_BINARY_SHA256": mutant_binary_sha},
            )
            subprocess.run([str(mutant_harness), "disappearing-state-join"],
                           env=env, capture_output=True, text=True, check=True)
            with self.assertRaises((AssertionError, reader.CaptureError)):
                self.assert_current_empty_join_reports_old_missing(
                    output.read_bytes(), mutant_expected
                )

    def test_temp_exclusive_create_collision_preserves_unowned_file(self):
        with tempfile.TemporaryDirectory(prefix="ccxcap-temp-collision-") as temp_dir:
            output = Path(temp_dir) / "capture.tsv"
            temp_path = Path(f"{output}.ccxcap-part-731029")
            sentinel = b"pre-existing temporary owner data\n"
            temp_path.write_bytes(sentinel)
            proc = subprocess.run([str(self.fixed_pid_harness), "seed"],
                                  env=self.capture_env(output), capture_output=True,
                                  text=True, check=True)
            self.assertEqual(proc.stdout, "")
            self.assertFalse(output.exists())
            self.assertEqual(temp_path.read_bytes(), sentinel)

    def test_existing_destination_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(prefix="ccxcap-collision-") as temp_dir:
            output = Path(temp_dir) / "capture.tsv"
            sentinel = b"existing owner data\n"
            output.write_bytes(sentinel)
            proc = subprocess.run([str(self.default_harness), "seed"],
                                  env=self.capture_env(output), capture_output=True,
                                  text=True, check=True)
            self.assertEqual(proc.stdout, "")
            self.assertEqual(output.read_bytes(), sentinel)
            self.assertEqual(list(Path(temp_dir).glob("capture.tsv.ccxcap-part-*")), [])

    def test_flush_and_close_errors_do_not_publish_successful_capture(self):
        for mode in ("fail-gen-flush", "fail-footer-flush-after-run-end", "fail-close"):
            with self.subTest(mode=mode):
                exists, data = self.run_sink_with_status(
                    harness=self.io_failure_harness,
                    mode=mode,
                )
                self.assertFalse(exists)
                self.assertIsNone(data)

    def test_tie_count_validation_accepts_exact_and_rejects_zero_or_extra(self):
        valid = self.run_sink(mode="seed")
        self.assertEqual(reader.validate_capture(valid, self.expected())["generation_count"], 1)
        for mode in ("invalid-zero", "invalid-extra"):
            data = self.run_sink(mode=mode)
            rows = [line.split("\t") for line in data.decode().splitlines()]
            self.assertEqual(sum(row[0] == "RUN_BEGIN" for row in rows), 1)
            self.assertEqual(sum(row[0] == "GEN_BEGIN" for row in rows), 0)
            self.assertEqual(sum(row[0] == "RUN_END" for row in rows), 1)
            self.assertEqual(rows[-1][8:10], ["1", "0"])
            with self.assertRaises(reader.CaptureError):
                reader.validate_capture(data, self.expected())

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
        for field in (2, 3, 4, 5):
            with self.subTest(map_identity_field=field):
                bad = mutate_record("MAP_SUMMARY", field,
                                    lambda value: str(int(value) + 1))
                with self.assertRaisesRegex(reader.CaptureError, "MAP_SUMMARY identity differs"):
                    reader.validate_capture(bad, self.expected())

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
        for field in range(9, 15):
            with self.subTest(negative_state_join_field=field):
                bad = mutate_record("STATE_JOIN", field, lambda _value: "-1")
                with self.assertRaisesRegex(reader.CaptureError, "STATE_JOIN contains a negative count"):
                    reader.validate_capture(bad, self.expected())
        bad = mutate_record("ITERATION_LINK", 8, lambda value: "0" if value == "1" else "1")
        with self.assertRaises(reader.CaptureError): reader.validate_capture(bad, self.expected())
        bad = mutate_record("ITERATION_LINK", 6, lambda _value: "9")
        with self.assertRaisesRegex(reader.CaptureError, "nonconverged iteration link"):
            reader.validate_capture(bad, self.expected())
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
        result = reader.validate_capture(data, self.expected())
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
