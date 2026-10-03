"""Synthetic execution-control checks; Docker and CalculiX never run."""

import contextlib
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "sti17_hard_stop_launcher", HERE / "launch_sti17_coupon.py"
)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
from fea import wood_joint_reduced_native as legacy


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class HardStopLauncherTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.repo = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.attempt = self.repo / "attempt"
        self.attempt.mkdir()
        legacy_copy = self.repo / "fea/wood_joint_reduced_native.py"
        legacy_copy.parent.mkdir()
        legacy_copy.write_bytes(launcher.LEGACY_PATH.read_bytes())
        launcher_copy = self.repo / "launch_sti17_coupon.py"
        launcher_copy.write_bytes((HERE / "launch_sti17_coupon.py").read_bytes())
        preparer_copy = self.repo / "prepare_sti17_coupon.py"
        preparer_copy.write_bytes((HERE / "prepare_sti17_coupon.py").read_bytes())
        sources = {
            "fea/wood_joint_reduced_native.py": sha(legacy_copy),
            "launch_sti17_coupon.py": sha(launcher_copy),
            "prepare_sti17_coupon.py": sha(preparer_copy),
        }
        for name in sources:
            p = self.attempt / "sources" / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((self.repo / name).read_bytes())
        (self.repo / "manual.pdf").write_bytes(b"synthetic manual")
        (self.repo / "AGENTS.md").write_text("synthetic resumed analysis authority")
        from prepare_sti17_coupon import DECK

        (self.attempt / "model.inp").write_bytes(DECK.read_bytes())
        (self.attempt / "model.json").write_text(
            json.dumps(
                launcher.make_model_record(launcher.EXPECTED_DECK_SHA256), indent=2
            )
            + "\n"
        )
        self.profile = {
            "version": "2.23-sti17",
            "binary_path": launcher.BINARY_PATH,
            "binary_sha256": "a" * 64,
            "image_id": "sha256:" + "b" * 64,
            "candidate_export_authorized": False,
            "mechanical_acceptance": False,
            "manual": {
                "local_path": "manual.pdf",
                "sha256": sha(self.repo / "manual.pdf"),
            },
        }
        self.packet = {
            "schema": "wood_joint_reduced_native_freeze/v1",
            "candidate": "compact-floor-flush-wood-joints-development",
            "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
            "candidate_export_authorized": False,
            "mechanical_acceptance": False,
            "scope": launcher.SCOPE,
            "files_sha256": {
                name: sha(self.attempt / name) for name in ("model.inp", "model.json")
            },
            "source_sha256": sources,
            "solver_profile": self.profile,
        }
        self.write_packet()
        self.review = self.repo / "review.json"
        self.review.write_text(
            json.dumps(
                {
                    "input_freeze_sha256": sha(self.attempt / "freeze.json"),
                    "ready_for_scoped_native_run": True,
                }
            )
        )
        self.ledger = self.repo / "ledger.json"
        self.ledger.write_text(
            json.dumps({"slot": {"state": "idle", "active_run_id": None}, "runs": []})
        )
        for module, name, value in [
            (legacy, "ROOT", self.repo),
            (launcher, "ROOT", self.repo),
            (launcher, "LEDGER", self.ledger),
            (launcher, "LEGACY_PATH", legacy_copy),
            (launcher, "FREEZE_DIR", self.attempt),
            (launcher, "PREPARER_PATH", preparer_copy),
            (launcher, "__file__", str(launcher_copy)),
        ]:
            self.stack.enter_context(patch.object(module, name, value))

    def write_packet(self):
        (self.attempt / "freeze.json").write_text(json.dumps(self.packet))

    def docker_result(self, command, **kwargs):
        if "inspect" in command:
            return subprocess.CompletedProcess(
                command, 0, self.profile["image_id"] + "\n", ""
            )
        if "sha256sum" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                self.profile["binary_sha256"]
                + "  "
                + self.profile["binary_path"]
                + "\n"
                + launcher.TIMEOUT_CONTROL["sha256"]
                + "  "
                + launcher.TIMEOUT_CONTROL["path"]
                + "\n",
                "",
            )
        if "ps" in command:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, self.native_exit)

    def test_generated_command_forces_kill_and_shares_single_terminal_ledger(self):
        self.native_exit = 0
        with patch.object(
            launcher.subprocess, "run", side_effect=self.docker_result
        ) as run:
            result = launcher.launch(self.attempt, "synthetic-hard-stop", self.review)
        command = result["command"]
        start = command.index("/usr/bin/timeout")
        self.assertEqual(
            command[start:],
            [
                "/usr/bin/timeout",
                "--signal=KILL",
                "60s",
                launcher.BINARY_PATH,
                "-i",
                "model",
            ],
        )
        self.assertEqual(run.call_count, 4)
        self.assertIn(f"{self.attempt / 'model.inp'}:/output/model.inp:ro", command)
        self.assertEqual(result["timeout_control"], launcher.TIMEOUT_CONTROL)
        ledger = json.loads(self.ledger.read_text())
        self.assertEqual(ledger["slot"]["state"], "idle")
        self.assertEqual(len(ledger["runs"]), 1)
        self.assertEqual(ledger["runs"][0]["state"], "consumed_terminal")
        self.assertEqual(ledger["runs"][0]["launches_consumed"], 1)
        self.assertEqual(
            ledger["runs"][0]["execution_record_sha256"],
            sha(self.attempt / "execution.json"),
        )

    def test_missing_exact_launcher_binding_refused_before_docker(self):
        del self.packet["source_sha256"]["launch_sti17_coupon.py"]
        self.write_packet()
        with (
            patch.object(launcher.subprocess, "run") as run,
            self.assertRaisesRegex(ValueError, "both exact launch sources"),
        ):
            launcher.launch(self.attempt, "synthetic-hard-stop", self.review)
        run.assert_not_called()
        self.assertEqual(json.loads(self.ledger.read_text())["runs"], [])

    def test_widened_scope_refused_before_docker(self):
        self.packet["scope"] = "candidate export"
        self.write_packet()
        with (
            patch.object(launcher.subprocess, "run") as run,
            self.assertRaisesRegex(ValueError, "limited to the isolated STI17 coupon"),
        ):
            launcher.launch(self.attempt, "synthetic-hard-stop", self.review)
        run.assert_not_called()

    def test_relabelled_deck_or_model_refused_before_docker(self):
        for name in ("model.inp", "model.json"):
            with self.subTest(changed=name):
                original = (self.attempt / name).read_bytes()
                (self.attempt / name).write_bytes(
                    b"candidate deck" if name.endswith("inp") else b"{}"
                )
                self.packet["files_sha256"][name] = sha(self.attempt / name)
                self.write_packet()
                with (
                    patch.object(launcher.subprocess, "run") as run,
                    self.assertRaisesRegex(ValueError, "exact free-C3D20"),
                ):
                    launcher.launch(self.attempt, "synthetic-hard-stop", self.review)
                run.assert_not_called()
                (self.attempt / name).write_bytes(original)
                self.packet["files_sha256"][name] = sha(self.attempt / name)
                self.write_packet()

    def test_noncanonical_directory_refused_before_docker(self):
        with (
            patch.object(launcher, "FREEZE_DIR", self.repo / "another"),
            patch.object(launcher.subprocess, "run") as run,
            self.assertRaisesRegex(ValueError, "canonical attempt"),
        ):
            launcher.launch(self.attempt, "synthetic-hard-stop", self.review)
        run.assert_not_called()

    def test_wrong_timeout_utility_refused_before_reservation(self):
        def changed_utility(command, **kwargs):
            result = self.docker_result(command, **kwargs)
            if "sha256sum" in command:
                result.stdout = result.stdout.replace(
                    launcher.TIMEOUT_CONTROL["sha256"], "0" * 64
                )
            return result

        self.native_exit = 0
        with (
            patch.object(launcher.subprocess, "run", side_effect=changed_utility),
            self.assertRaisesRegex(ValueError, "timeout utility hash"),
        ):
            launcher.launch(self.attempt, "synthetic-hard-stop", self.review)
        self.assertEqual(json.loads(self.ledger.read_text())["runs"], [])

    def test_freeze_change_during_preflight_refused_before_reservation(self):
        def replace_freeze(command, **kwargs):
            result = self.docker_result(command, **kwargs)
            if "sha256sum" in command:
                self.packet["extra_context"] = "changed after reviewed digest"
                self.write_packet()
            return result

        self.native_exit = 0
        with (
            patch.object(launcher.subprocess, "run", side_effect=replace_freeze),
            self.assertRaisesRegex(ValueError, "freeze changed before reservation"),
        ):
            launcher.launch(self.attempt, "synthetic-hard-stop", self.review)
        self.assertEqual(json.loads(self.ledger.read_text())["runs"], [])

    def test_review_change_during_preflight_refused_before_reservation(self):
        def replace_review(command, **kwargs):
            result = self.docker_result(command, **kwargs)
            if "sha256sum" in command:
                self.review.write_text(
                    json.dumps(
                        {
                            "input_freeze_sha256": sha(self.attempt / "freeze.json"),
                            "ready_for_scoped_native_run": False,
                        }
                    )
                )
            return result

        self.native_exit = 0
        with (
            patch.object(launcher.subprocess, "run", side_effect=replace_review),
            self.assertRaisesRegex(ValueError, "review changed before reservation"),
        ):
            launcher.launch(self.attempt, "synthetic-hard-stop", self.review)
        self.assertEqual(json.loads(self.ledger.read_text())["runs"], [])

    def test_killed_run_is_consumed_terminal_with_nonzero_exit(self):
        self.native_exit = 137
        with patch.object(launcher.subprocess, "run", side_effect=self.docker_result):
            result = launcher.launch(self.attempt, "synthetic-hard-stop", self.review)
        self.assertEqual(result["returncode"], 137)
        ledger = json.loads(self.ledger.read_text())
        self.assertEqual(ledger["slot"]["state"], "idle")
        self.assertEqual(ledger["runs"][0]["state"], "consumed_terminal")
        self.assertEqual(ledger["runs"][0]["outcome"], "Native exit 137")


if __name__ == "__main__":
    unittest.main()
