"""Pure-Python checks for the unexecuted STI17 preparation packet."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))


def load_packet_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load packet helper {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BUILD = load_packet_module("sti17_build_test_target", "build_sti17.py")
PREPARE = load_packet_module("sti17_prepare_test_target", "prepare_sti17_coupon.py")
CHECK = load_packet_module("sti17_check_test_target", "check_sti17_coupon.py")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def valid_parent_readiness() -> dict:
    return {
        "schema": "ccx223_sti17_parent_build_readiness/v1",
        "status": "READY_STI17_BUILD",
        "parent_validation_sha256": BUILD.PARENT_VALIDATION_SHA256,
        "source_pins_sha256": BUILD.SOURCE_PINS_SHA256,
        "base_image_id": BUILD.BASE_IMAGE_ID,
        "new_image_tag": BUILD.NEW_IMAGE_TAG,
        "base_tag_resolves_to_id": True,
        "new_image_tag_unused": True,
        "candidate_export_authorized": False,
        "native_run_authorized": False,
        "max_cpu": 1,
        "memory_bytes": 2 * 1024**3,
        "wall_seconds": 60,
        "created_unix": 900,
    }


def valid_build_freeze(readiness_sha256: str) -> tuple[dict, dict[str, str]]:
    files = {
        relative: sha_bytes(relative.encode())
        for relative in BUILD.REQUIRED_BUILD_FILE_PINS
    }
    files[BUILD.READINESS_REL] = readiness_sha256
    packet = {
        "schema": "ccx223_sti17_build_input_freeze/v1",
        "status": "FROZEN_FOR_ONE_ISOLATED_BUILD",
        "scope": "copy pinned CalculiX 2.23 image source/object tree; rebuild matrixstorage.o only",
        "created_unix": 900,
        "base_image_id": BUILD.BASE_IMAGE_ID,
        "new_image_tag": BUILD.NEW_IMAGE_TAG,
        "parent_readiness_sha256": readiness_sha256,
        "parent_validation_sha256": BUILD.PARENT_VALIDATION_SHA256,
        "source_pins_sha256": BUILD.SOURCE_PINS_SHA256,
        "patch_sha256": BUILD.PATCH_SHA256,
        "resource_limits": {
            "cpu_count": 1,
            "memory_bytes": 2 * 1024**3,
            "wall_seconds": 60,
        },
        "files_sha256": files,
        "native_solver_run": False,
        "candidate_matrix_exported": False,
        "mechanical_acceptance": False,
    }
    return packet, files.copy()


class BuildPreparationTests(unittest.TestCase):
    def test_build_review_binding_refuses_reviewed_source_or_review_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "builder.py"
            source.write_text("reviewed builder\n")
            files = {"builder.py": BUILD.sha_file(source)}
            target = root / "target.json"
            target.write_text(
                json.dumps(
                    {"files": [{"path": "builder.py", "sha256": files["builder.py"]}]}
                )
            )
            files["target.json"] = BUILD.sha_file(target)
            reviews = {}
            for role in ("correctness", "testing", "architecture"):
                name = role + ".md"
                (root / name).write_text(role + " independent final review\n")
                files[name] = BUILD.sha_file(root / name)
                reviews[role] = {
                    "path": name,
                    "sha256": files[name],
                    "agent_id": "synthetic-" + role,
                }
            binding = {
                "target": {"path": "target.json", "sha256": files["target.json"]},
                "reviews": reviews,
            }
            BUILD.validate_review_binding(root, binding, files)
            duplicate = copy.deepcopy(binding)
            duplicate["reviews"]["testing"] = duplicate["reviews"]["correctness"].copy()
            with self.assertRaisesRegex(RuntimeError, "three distinct"):
                BUILD.validate_review_binding(root, duplicate, files)
            source.write_text("unreviewed builder\n")
            with self.assertRaisesRegex(RuntimeError, "reviewed source changed"):
                BUILD.validate_review_binding(root, binding, files)
            source.write_text("reviewed builder\n")
            files["builder.py"] = "0" * 64
            with self.assertRaisesRegex(RuntimeError, "differs from reviewed source"):
                BUILD.validate_review_binding(root, binding, files)
            files["builder.py"] = BUILD.sha_file(source)
            (root / "correctness.md").write_text("changed review\n")
            with self.assertRaisesRegex(RuntimeError, "source-review record"):
                BUILD.validate_review_binding(root, binding, files)

    def test_patch_changes_only_stiffness_format_and_keeps_mass_format(self):
        original = (
            b"prefix\n" + BUILD.SOURCE_OLD + b"\n" + BUILD.MASS_WRITER + b"\nsuffix\n"
        )

        patched = BUILD.patch_stiffness_writer(original)

        self.assertEqual(patched.count(BUILD.SOURCE_NEW), 1)
        self.assertEqual(patched.count(BUILD.MASS_WRITER), 1)
        self.assertNotIn(BUILD.SOURCE_OLD, patched)
        self.assertEqual(
            patched.replace(BUILD.SOURCE_NEW, BUILD.SOURCE_OLD, 1),
            original,
        )

    def test_patch_refuses_a_changed_mass_writer_or_duplicate_stiffness_writer(self):
        original = BUILD.SOURCE_OLD + b"\n" + BUILD.MASS_WRITER

        with self.assertRaisesRegex(RuntimeError, "mass writer"):
            BUILD.patch_stiffness_writer(
                original.replace(BUILD.MASS_WRITER, b"changed")
            )
        with self.assertRaisesRegex(RuntimeError, "one original stiffness writer"):
            BUILD.patch_stiffness_writer(original + b"\n" + BUILD.SOURCE_OLD)

    def test_make_plan_accepts_only_the_one_compile_archive_and_link_plan(self):
        plan = """\
gcc -Wall -O2 -I/usr/include/spooles -DARCH=Linux -DSPOOLES -DARPACK -DMATRIXSTORAGE -DNETWORKOUT -c matrixstorage.c -o matrixstorage.o
ar rcs ccx_2.23.a matrixstorage.o util.o
gfortran -O2 -o ccx_2.23 ccx_2.23.o ccx_2.23.a -lspooles -larpack -llapack -lblas -lpthread -lm -fopenmp"""

        self.assertEqual(
            BUILD.validate_make_plan(plan, ["matrixstorage.o", "util.o"]),
            [
                "gcc",
                "-Wall",
                "-O2",
                "-I/usr/include/spooles",
                "-DARCH=Linux",
                "-DSPOOLES",
                "-DARPACK",
                "-DMATRIXSTORAGE",
                "-DNETWORKOUT",
                "-c",
                "matrixstorage.c",
                "-o",
                "matrixstorage.o",
            ],
        )

    def test_make_plan_refuses_any_wider_compile(self):
        plan = """\
gcc -Wall -O2 -I/usr/include/spooles -DARCH=Linux -DSPOOLES -DARPACK -DMATRIXSTORAGE -DNETWORKOUT -c matrixstorage.c -o matrixstorage.o
gcc -Wall -O2 -c ccx_2.23.c -o ccx_2.23.o
ar rcs ccx_2.23.a matrixstorage.o util.o
gfortran -O2 -o ccx_2.23 ccx_2.23.o ccx_2.23.a -lspooles -larpack -llapack -lblas -lpthread -lm -fopenmp"""

        with self.assertRaisesRegex(RuntimeError, "broader"):
            BUILD.validate_make_plan(plan, ["matrixstorage.o", "util.o"])

    def test_parent_readiness_rejects_a_source_pin_mismatch(self):
        readiness = valid_parent_readiness()
        BUILD.validate_parent_readiness(readiness, now=1000)
        readiness["source_pins_sha256"] = "0" * 64

        with self.assertRaisesRegex(RuntimeError, "source pins"):
            BUILD.validate_parent_readiness(readiness, now=1000)

    def test_build_freeze_rejects_readiness_and_live_pin_mismatches(self):
        readiness_sha256 = "a" * 64
        packet, live_hashes = valid_build_freeze(readiness_sha256)
        BUILD.validate_build_input_freeze(
            packet,
            readiness_sha256=readiness_sha256,
            live_hashes=live_hashes,
            now=1000,
        )

        with self.assertRaisesRegex(RuntimeError, "readiness and source pins"):
            BUILD.validate_build_input_freeze(
                packet,
                readiness_sha256="b" * 64,
                live_hashes=live_hashes,
                now=1000,
            )

        changed = live_hashes.copy()
        pinned_file = next(name for name in changed if name != BUILD.READINESS_REL)
        changed[pinned_file] = "f" * 64
        with self.assertRaisesRegex(RuntimeError, "frozen build input changed"):
            BUILD.validate_build_input_freeze(
                packet,
                readiness_sha256=readiness_sha256,
                live_hashes=changed,
                now=1000,
            )


class CouponPreparationTests(unittest.TestCase):
    def test_current_pinned_manual_passes_before_missing_terminal_receipts_stop(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.object(
                PREPARE, "BUILD_RECEIPT", Path(temporary) / "missing-build-receipt.json"
            ),
            self.assertRaisesRegex(RuntimeError, "terminal build/image receipts"),
        ):
            PREPARE.main()

    def test_coupon_readiness_refuses_different_build_or_image_receipts(self):
        readiness = {
            "schema": "ccx223_sti17_coupon_readiness/v1",
            "status": "READY_FOR_STI17_COUPON_FREEZE",
            "build_receipt_sha256": "1" * 64,
            "image_id": "sha256:" + "2" * 64,
            "image_receipt_sha256": "3" * 64,
            "scope": "free-c3d20-sti17-output-precision-coupon-only",
            "candidate_export_authorized": False,
            "native_run_authorized": False,
            "max_cpu": 1,
            "memory_bytes": 2 * 1024**3,
            "wall_seconds": 60,
            "max_native_runs": 1,
            "created_unix": 900,
        }
        PREPARE.validate_coupon_readiness(
            readiness,
            build_receipt_sha256="1" * 64,
            image_id="sha256:" + "2" * 64,
            image_receipt_sha256="3" * 64,
            now=1000,
        )

        with self.assertRaisesRegex(RuntimeError, "exact build and image"):
            PREPARE.validate_coupon_readiness(
                readiness,
                build_receipt_sha256="4" * 64,
                image_id="sha256:" + "2" * 64,
                image_receipt_sha256="3" * 64,
                now=1000,
            )

        changed_image_id = copy.deepcopy(readiness)
        changed_image_id["image_id"] = "sha256:" + "4" * 64
        with self.assertRaisesRegex(RuntimeError, "exact build and image"):
            PREPARE.validate_coupon_readiness(
                changed_image_id,
                build_receipt_sha256="1" * 64,
                image_id="sha256:" + "2" * 64,
                image_receipt_sha256="3" * 64,
                now=1000,
            )

        changed_image_receipt = copy.deepcopy(readiness)
        changed_image_receipt["image_receipt_sha256"] = "4" * 64
        with self.assertRaisesRegex(RuntimeError, "terminal image receipt"):
            PREPARE.validate_coupon_readiness(
                changed_image_receipt,
                build_receipt_sha256="1" * 64,
                image_id="sha256:" + "2" * 64,
                image_receipt_sha256="3" * 64,
                now=1000,
            )

    def test_generated_freeze_schema_is_accepted_by_stock_runner_verify(self):
        from fea.wood_joint_reduced_native import verify

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manual = root / "synthetic-manual.pdf"
            manual.write_bytes(b"synthetic pinned manual fixture\n")
            profile = {
                "version": "2.23-sti17",
                "image_id": "sha256:" + "a" * 64,
                "binary_path": "/usr/local/bin/ccx-upstream-2.23-sti17",
                "binary_sha256": "b" * 64,
                "manual": {
                    "local_path": str(manual),
                    "sha256": sha_bytes(manual.read_bytes()),
                },
            }
            source_relative = "synthetic/runner_source.py"
            source_bytes = b"# synthetic source snapshot only\n"
            source_hashes = {source_relative: sha_bytes(source_bytes)}
            deck = b"* Synthetic unit coupon deck; no solver execution\n"
            model = PREPARE.make_model_record(sha_bytes(deck))
            directory = root / "freeze"
            directory.mkdir()
            sources = directory / "sources" / source_relative
            sources.parent.mkdir(parents=True)
            sources.write_bytes(source_bytes)
            (directory / "model.inp").write_bytes(deck)
            model_bytes = (json.dumps(model, indent=2, allow_nan=False) + "\n").encode()
            (directory / "model.json").write_bytes(model_bytes)
            packet = PREPARE.make_coupon_freeze_packet(
                profile,
                source_hashes,
                deck_sha256=sha_bytes(deck),
                model_sha256=sha_bytes(model_bytes),
            )
            (directory / "freeze.json").write_text(json.dumps(packet, indent=2) + "\n")

            verified = verify(directory, check_live=False)

        self.assertEqual(verified["schema"], "wood_joint_reduced_native_freeze/v1")
        self.assertEqual(verified["solver_profile"]["version"], "2.23-sti17")
        self.assertEqual(verified["files_sha256"].keys(), {"model.inp", "model.json"})
        self.assertFalse(verified["native_solve_executed"])
        self.assertFalse(verified["candidate_export_authorized"])


class CouponOutputChecks(unittest.TestCase):
    def test_sti17_accepts_16_decimal_places_and_refuses_13(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic.sti"
            path.write_text("1 1 1.2345678901234567e+00\n")
            self.assertEqual(
                CHECK.check_format(path, CHECK.EXPECTED_STI_PLACES)["rows"], 1
            )
            path.write_text("1 1 1.2345678901235e+00\n")
            with self.assertRaisesRegex(RuntimeError, "16 decimal places"):
                CHECK.check_format(path, CHECK.EXPECTED_STI_PLACES)

    def test_mas14_accepts_13_decimal_places_and_refuses_16(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic.mas"
            path.write_text("1 1 1.2345678901235e+00\n")
            self.assertEqual(
                CHECK.check_format(path, CHECK.EXPECTED_MAS_PLACES)["rows"], 1
            )
            path.write_text("1 1 1.2345678901234567e+00\n")
            with self.assertRaisesRegex(RuntimeError, "13 decimal places"):
                CHECK.check_format(path, CHECK.EXPECTED_MAS_PLACES)


class RunnerRecordSchemaTests(unittest.TestCase):
    def synthetic_runner_bundle(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        freeze_digest = "a" * 64
        scope = PREPARE.FREEZE_SCOPE
        attempt = directory / "attempt01"
        attempt.mkdir()
        run_id = "sti17-free-c3d20-attempt01"
        profile = {
            "version": "2.23-sti17",
            "image_id": "sha256:" + "9" * 64,
            "binary_path": CHECK.EXPECTED_BINARY_PATH,
            "binary_sha256": "8" * 64,
            "candidate_export_authorized": False,
            "mechanical_acceptance": False,
        }
        command = [
            "docker",
            "--context",
            "default",
            "run",
            "--rm",
            "--name",
            "moonboard-" + run_id.lower(),
            "--network=none",
            "--cpus=1",
            "--memory=2g",
            "--user",
            "1000:1000",
            "-e",
            "OMP_NUM_THREADS=1",
            "--memory-swap=2g",
            "-v",
            f"{attempt.resolve()}:/output",
            "-v",
            f"{attempt.resolve() / 'model.inp'}:/output/model.inp:ro",
            "-w",
            "/output",
            profile["image_id"],
            "/usr/bin/timeout",
            "--signal=KILL",
            "60s",
            profile["binary_path"],
            "-i",
            "model",
        ]
        authorization = {
            "run_id": run_id,
            "scope": scope,
            "input_freeze_sha256": freeze_digest,
            "parent_readiness": True,
            "native_execution_authorized": True,
            "independent_review": "synthetic-review.json",
            "independent_review_sha256": "b" * 64,
            "owner_authority": "AGENTS.md resumed reviewed wood-joint native-analysis authorization",
            "owner_authority_sha256": "c" * 64,
            "command": command,
            "timeout_control": CHECK.EXPECTED_TIMEOUT_CONTROL.copy(),
            "mechanical_acceptance": False,
        }
        execution = {
            "run_id": run_id,
            "command": list(authorization["command"]),
            "timeout_control": CHECK.EXPECTED_TIMEOUT_CONTROL.copy(),
            "started_unix": 1000.0,
            "native_solve_executed": True,
            "mechanical_acceptance": False,
            "returncode": 0,
            "elapsed_seconds": 0.5,
            "container_confirmed_terminal": True,
            "outputs_sha256": {
                "model.sti": "d" * 64,
                "model.mas": "e" * 64,
                "model.dof": "f" * 64,
            },
        }
        authorization_bytes = (
            json.dumps(authorization, indent=2, allow_nan=False) + "\n"
        ).encode()
        execution_bytes = (
            json.dumps(execution, indent=2, allow_nan=False) + "\n"
        ).encode()
        authorization_sha256 = sha_bytes(authorization_bytes)
        execution_sha256 = sha_bytes(execution_bytes)
        review = {
            "input_freeze_sha256": freeze_digest,
            "ready_for_scoped_native_run": True,
        }
        ledger = {
            "runs": [
                {
                    "run_id": run_id,
                    "scope": scope,
                    "attempt_directory": "synthetic/attempt01",
                    "input_freeze_sha256": freeze_digest,
                    "max_launches": 1,
                    "launches_consumed": 1,
                    "state": "consumed_terminal",
                    "parent_readiness": True,
                    "native_execution_authorized": True,
                    "authorization_sha256": authorization_sha256,
                    "execution_record_sha256": execution_sha256,
                }
            ],
        }
        return {
            "freeze_digest": freeze_digest,
            "scope": scope,
            "attempt": attempt,
            "attempt_relative": "synthetic/attempt01",
            "profile": profile,
            "authorization": authorization,
            "execution": execution,
            "review": review,
            "ledger": ledger,
            "authorization_sha256": authorization_sha256,
            "execution_sha256": execution_sha256,
        }

    def check_bundle(self, bundle):
        return CHECK.validate_runner_records(
            bundle["freeze_digest"],
            bundle["scope"],
            bundle["attempt"],
            bundle["attempt_relative"],
            bundle["authorization"],
            bundle["execution"],
            bundle["review"],
            bundle["profile"],
            bundle["ledger"],
            bundle["authorization_sha256"],
            bundle["execution_sha256"],
        )

    def test_checker_accepts_records_written_by_the_existing_runner(self):
        with tempfile.TemporaryDirectory() as temporary:
            bundle = self.synthetic_runner_bundle(Path(temporary))
            checked_run_id, ledger_row = self.check_bundle(bundle)
        self.assertEqual(checked_run_id, bundle["authorization"]["run_id"])
        self.assertEqual(ledger_row["state"], "consumed_terminal")

    def test_recorded_output_hashes_match_synthetic_fixtures_and_reject_gaps(self):
        fixtures = {
            "model.sti": b"synthetic STI17 output fixture\n",
            "model.mas": b"synthetic MAS14 output fixture\n",
            "model.dof": b"synthetic DOF output fixture\n",
        }
        recorded_hashes = {
            "model.sti": "f02adec16f88ec13e82a829a48b5e4a585412045eea5d52915148edada6adb72",
            "model.mas": "c53e5d6de2d6e5a6c542fe0fd2dcb8951bc095f447d0376f1c67ef14392fac92",
            "model.dof": "4e3ee5c6bc99b1992dc839d6bc556f67107bd114b7f1eff6a03025f6b43fb90b",
        }
        with tempfile.TemporaryDirectory() as temporary:
            fixture_dir = Path(temporary)
            observed_hashes = {}
            for name, contents in fixtures.items():
                output = fixture_dir / name
                output.write_bytes(contents)
                observed_hashes[name] = sha_bytes(output.read_bytes())

            execution = {"outputs_sha256": recorded_hashes.copy()}
            CHECK.validate_recorded_outputs(execution, observed_hashes)

            for name in fixtures:
                with self.subTest(output=name, defect="mismatched recorded hash"):
                    changed_hashes = recorded_hashes.copy()
                    changed_hashes[name] = "0" * 64
                    with self.assertRaisesRegex(
                        RuntimeError, f"{name} raw output hash differs"
                    ):
                        CHECK.validate_recorded_outputs(
                            {"outputs_sha256": changed_hashes}, observed_hashes
                        )

                with self.subTest(output=name, defect="missing recorded hash"):
                    missing_hash = recorded_hashes.copy()
                    del missing_hash[name]
                    with self.assertRaisesRegex(
                        RuntimeError, f"{name} raw output hash differs"
                    ):
                        CHECK.validate_recorded_outputs(
                            {"outputs_sha256": missing_hash}, observed_hashes
                        )

    def test_runner_chain_refuses_broken_freeze_review_and_ledger_links(self):
        mutations = {
            "authorization freeze": lambda b: b["authorization"].__setitem__(
                "input_freeze_sha256",
                "0" * 64,
            ),
            "authorization scope": lambda b: b["authorization"].__setitem__(
                "scope", "other"
            ),
            "authorization readiness": lambda b: b["authorization"].__setitem__(
                "parent_readiness",
                False,
            ),
            "authorization execution grant": lambda b: b["authorization"].__setitem__(
                "native_execution_authorized",
                False,
            ),
            "execution run ID": lambda b: b["execution"].__setitem__(
                "run_id", "other-run"
            ),
            "nonzero exit": lambda b: b["execution"].__setitem__("returncode", 1),
            "unconfirmed terminal": lambda b: b["execution"].__setitem__(
                "container_confirmed_terminal",
                False,
            ),
            "review freeze": lambda b: b["review"].__setitem__(
                "input_freeze_sha256",
                "0" * 64,
            ),
            "review readiness": lambda b: b["review"].__setitem__(
                "ready_for_scoped_native_run",
                False,
            ),
            "duplicate run ID": lambda b: b["ledger"]["runs"].append(
                copy.deepcopy(b["ledger"]["runs"][0]),
            ),
            "no ledger row": lambda b: b["ledger"]["runs"].clear(),
            "ledger scope": lambda b: b["ledger"]["runs"][0].__setitem__(
                "scope", "other"
            ),
            "ledger attempt": lambda b: b["ledger"]["runs"][0].__setitem__(
                "attempt_directory",
                "other/attempt",
            ),
            "ledger freeze": lambda b: b["ledger"]["runs"][0].__setitem__(
                "input_freeze_sha256",
                "0" * 64,
            ),
            "ledger max launches": lambda b: b["ledger"]["runs"][0].__setitem__(
                "max_launches",
                2,
            ),
            "ledger launches consumed": lambda b: b["ledger"]["runs"][0].__setitem__(
                "launches_consumed",
                0,
            ),
            "ledger terminal state": lambda b: b["ledger"]["runs"][0].__setitem__(
                "state",
                "consumed_running",
            ),
            "ledger parent readiness": lambda b: b["ledger"]["runs"][0].__setitem__(
                "parent_readiness",
                False,
            ),
            "ledger execution grant": lambda b: b["ledger"]["runs"][0].__setitem__(
                "native_execution_authorized",
                False,
            ),
            "authorization record hash": lambda b: b["ledger"]["runs"][0].__setitem__(
                "authorization_sha256",
                "0" * 64,
            ),
            "execution record hash": lambda b: b["ledger"]["runs"][0].__setitem__(
                "execution_record_sha256",
                "0" * 64,
            ),
            "authorization bytes hash": lambda b: b.__setitem__(
                "authorization_sha256",
                "0" * 64,
            ),
            "execution bytes hash": lambda b: b.__setitem__(
                "execution_sha256",
                "0" * 64,
            ),
        }
        with tempfile.TemporaryDirectory() as temporary:
            for label, mutate in mutations.items():
                with self.subTest(broken_link=label):
                    bundle = self.synthetic_runner_bundle(
                        Path(temporary) / label.replace(" ", "_")
                    )
                    mutate(bundle)
                    with self.assertRaises(RuntimeError):
                        self.check_bundle(bundle)

    def test_runner_chain_refuses_resource_image_and_command_changes(self):
        def change_both_commands(bundle, index, value):
            bundle["authorization"]["command"][index] = value
            bundle["execution"]["command"][index] = value

        mutations = {
            "different auth/execution commands": lambda b: b["execution"][
                "command"
            ].__setitem__(
                8,
                "--cpus=2",
            ),
            "wrong docker context": lambda b: change_both_commands(b, 2, "other"),
            "wrong container name": lambda b: change_both_commands(
                b, 6, "moonboard-other"
            ),
            "container retained or reused": lambda b: change_both_commands(
                b, 4, "--reused"
            ),
            "two CPUs": lambda b: change_both_commands(b, 8, "--cpus=2"),
            "memory limit": lambda b: change_both_commands(b, 9, "--memory=4g"),
            "network access": lambda b: change_both_commands(b, 7, "--network=bridge"),
            "different image": lambda b: change_both_commands(
                b, 21, "sha256:" + "1" * 64
            ),
            "different binary": lambda b: change_both_commands(b, 25, "/usr/bin/ccx"),
            "different timeout": lambda b: change_both_commands(b, 24, "61s"),
            "TERM-only timeout": lambda b: change_both_commands(b, 23, "--signal=TERM"),
            "PATH-resolved utility": lambda b: change_both_commands(b, 22, "timeout"),
            "swap allowance": lambda b: change_both_commands(b, 14, "--memory-swap=4g"),
            "writable input": lambda b: change_both_commands(
                b, 18, "/tmp/model.inp:/output/model.inp"
            ),
            "wrong utility hash": lambda b: b["execution"][
                "timeout_control"
            ].__setitem__("sha256", "0" * 64),
            "different output directory": lambda b: change_both_commands(
                b,
                16,
                "/tmp/other:/output",
            ),
            "missing solver thread pin": lambda b: change_both_commands(
                b,
                13,
                "OMP_NUM_THREADS=4",
            ),
        }
        with tempfile.TemporaryDirectory() as temporary:
            for label, mutate in mutations.items():
                with self.subTest(command_change=label):
                    bundle = self.synthetic_runner_bundle(
                        Path(temporary) / label.replace(" ", "_")
                    )
                    mutate(bundle)
                    with self.assertRaises(RuntimeError):
                        self.check_bundle(bundle)

    def test_recorded_independent_review_path_and_hash_are_exact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            review = root / "review.json"
            payload = {
                "input_freeze_sha256": "a" * 64,
                "ready_for_scoped_native_run": True,
            }
            review.write_text(json.dumps(payload, indent=2) + "\n")
            digest = sha_bytes(review.read_bytes())
            self.assertEqual(
                CHECK.load_bound_review(root, "review.json", digest),
                payload,
            )
            with self.assertRaisesRegex(RuntimeError, "changed"):
                CHECK.load_bound_review(root, "review.json", "0" * 64)
            with self.assertRaisesRegex(RuntimeError, "repository-relative"):
                CHECK.load_bound_review(root, "../review.json", digest)

    def test_result_destination_refuses_frozen_native_or_existing_file_aliases(self):
        with tempfile.TemporaryDirectory() as temporary:
            attempt = Path(temporary) / "attempt"
            attempt.mkdir()
            (attempt / "model.dat").write_text("synthetic native output\n")
            safe = CHECK.safe_result_path(attempt, attempt / CHECK.RESULT_NAME)
            self.assertEqual(safe.name, CHECK.RESULT_NAME)
            with self.assertRaisesRegex(RuntimeError, "filename is reserved"):
                CHECK.safe_result_path(attempt, attempt / "model.dat")
            (attempt / CHECK.RESULT_NAME).write_text("already written\n")
            with self.assertRaisesRegex(RuntimeError, "already exists"):
                CHECK.safe_result_path(attempt, attempt / CHECK.RESULT_NAME)


if __name__ == "__main__":
    unittest.main()
