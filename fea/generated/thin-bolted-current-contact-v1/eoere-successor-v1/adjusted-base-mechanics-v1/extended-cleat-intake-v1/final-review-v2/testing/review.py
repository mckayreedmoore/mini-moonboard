"""Independent cheap intake checks; never load genuine CAD/query methods."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
INTAKE = OWN.parents[2]
ROOT = OWN.parents[8]
CORRECTED = INTAKE / "review-fix-v2/export.py"
MANIFEST = INTAKE.parent / "parent-authority-v1/extended-cleat-manifest.json"
MANIFEST_SHA = "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6"
EXPECTED = {
    INTAKE / "export.py": "bdfa95b4da8dfcb3d183dcaf59574afdb2f42e938f8e535680739fa0637696bb",
    INTAKE / "test_extended_intake.py": "786cdfb9e8560716ab603d26179ce3a0b5635965d3238e234f669811768fe63a",
    INTAKE / "verification.json": "e5b8451c7b6d23822b8909378f2df98e6132e16384900ac20b5c3522b5193544",
    CORRECTED: "93ed36c39b4237cd587498fbb9dd2b2b7e3d275afc2be89302dab178c25d5858",
    CORRECTED.with_name("test_output_reservation.py"): "3ceae6b82c0022493115a9ab0ce0b5a6c54a628337cb30cdb3fe6b1b3018daae",
    CORRECTED.with_name("verification.json"): "a046295fd38714893276dda6f495307821ab2c2545107298bb530d897e7e8ed3",
    MANIFEST: MANIFEST_SHA,
    MANIFEST.with_name("adjusted-base-manifest.json"): "27220ec69ebe96e0c637d02d74aea1a7732f68d111b9918c973fa8ee954b48c2",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("independent_testing_reservation_wrapper", CORRECTED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect(error_type, action, text=None):
    try:
        action()
    except error_type as error:
        assert text is None or text in str(error), repr(error)
        return error
    raise AssertionError(f"expected {error_type.__name__}")


def controls():
    checked = {}
    with tempfile.TemporaryDirectory(prefix="isolated-fixtures-", dir=OWN.parent) as directory:
        temp = Path(directory)
        x = load()
        calls = []
        for kind in ("file", "directory", "live-symlink"):
            out = temp / kind
            target = temp / "target"
            if kind == "file":
                out.write_bytes(b"preserved\n")
            elif kind == "directory":
                out.mkdir()
            else:
                target.write_bytes(b"target preserved\n")
                out.symlink_to(target)
            with patch.object(x, "load_frozen", lambda: calls.append("loaded")):
                expect(FileExistsError, lambda out=out: x.export_to_file(None, None, out, extract=True))
            assert not calls
            if kind == "file":
                assert out.read_bytes() == b"preserved\n"
            elif kind == "live-symlink":
                assert target.read_bytes() == b"target preserved\n" and out.is_symlink()
            checked[f"existing_{kind}_rejected_before_loader"] = True

        out = temp / "interrupt.json"
        expect(KeyboardInterrupt, lambda: x.reserved_output(out, lambda: (_ for _ in ()).throw(KeyboardInterrupt("control"))))
        record = json.loads(out.read_bytes())
        assert record["status"] == "FAILED" and record["exception"]["type"] == "KeyboardInterrupt"
        checked["keyboard_interrupt_retains_FAILED"] = True

        out = temp / "nonfinite.json"
        expect(ValueError, lambda: x.reserved_output(out, lambda: {"schema": "fake", "value": float("nan")}))
        assert json.loads(out.read_bytes())["status"] == "FAILED"
        checked["nonfinite_producer_result_retains_FAILED"] = True

        original = x.FROZEN
        fake_frozen = temp / "tampered-frozen.py"
        fake_frozen.write_text("raise AssertionError('tampered code executed')\n")
        out = temp / "bad-frozen.json"
        with patch.object(x, "FROZEN", fake_frozen):
            expect(ValueError, lambda: x.export_to_file(None, None, out), "preserve the frozen extended-cleat intake")
        assert json.loads(out.read_bytes())["status"] == "FAILED" and x.FROZEN == original
        checked["tampered_frozen_helper_rejected_before_module_execution"] = True

        frozen = x.load_frozen()
        for phase in ("before_producer", "after_producer"):
            fake_own = temp / f"wrapper-source-{phase}.py"
            fake_own.write_text("fixture bytes\n")
            digest = sha(fake_own)
            produced = []
            def produce(*_, produced=produced, fake_own=fake_own):
                produced.append(True)
                fake_own.write_text("changed fixture bytes\n")
                return {"schema": "synthetic_callback_only/v1", "source_sha256": {}}
            def loader(phase=phase, fake_own=fake_own):
                if phase == "before_producer":
                    fake_own.write_text("changed fixture bytes\n")
                return frozen
            out = temp / f"tamper-{phase}.json"
            with patch.object(x, "OWN", fake_own), patch.object(x, "LOADED_SHA", digest), patch.object(x, "load_frozen", loader), patch.object(frozen, "source_plan", produce):
                expect(ValueError, lambda out=out: x.export_to_file(None, None, out), "source bytes changed")
            assert bool(produced) is (phase == "after_producer")
            record = json.loads(out.read_bytes())
            assert record["status"] == "FAILED" and "source bytes changed" in record["exception"]["message"]
            checked[f"isolated_wrapper_tamper_{phase}_rejected"] = True

        # This is the actual corrected CLI, with source-only preparation followed
        # by a deliberately invalid slot. Neither case reaches query loading.
        environment = dict(os.environ, PYTHONPATH=str(ROOT), EOERE_PARENT_SERIALIZED_EXTRACTION="1")
        for label, slot_record, supplied_sha, message in (
            ("missing", None, None, "exact parent serial-slot record required"),
            ("foreign-manifest", {"status": "FREE_SLOT", "cached_descriptor_extraction_authorized": True,
                                  "approved_geometry_sha256": frozen.GEOMETRY["sha256"],
                                  "approved_manifest_sha256": "foreign"}, "actual", "exact frozen intake manifest SHA"),
            ("stale-sha", {"status": "FREE_SLOT", "cached_descriptor_extraction_authorized": True,
                           "approved_geometry_sha256": frozen.GEOMETRY["sha256"],
                           "approved_manifest_sha256": MANIFEST_SHA}, "stale", "exact parent serial-slot record required"),
        ):
            out = temp / f"cli-{label}.json"
            command = [sys.executable, "-B", str(CORRECTED), "--manifest", str(MANIFEST),
                       "--manifest-sha256", MANIFEST_SHA, "--out", str(out), "--extract"]
            if slot_record is not None:
                slot = temp / f"slot-{label}.json"
                slot.write_text(json.dumps(slot_record))
                command += ["--slot", str(slot), "--slot-sha256", sha(slot) if supplied_sha == "actual" else supplied_sha]
            result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=20)
            assert result.returncode != 0 and message in result.stderr, result.stderr
            record = json.loads(out.read_bytes())
            assert record["status"] == "FAILED" and message in record["exception"]["message"]
            checked[f"actual_CLI_{label}_slot_rejected_with_FAILED_receipt"] = True

        out = temp / "bad-manifest.json"
        command = [sys.executable, "-B", str(CORRECTED), "--manifest", str(MANIFEST),
                   "--manifest-sha256", "stale", "--out", str(out)]
        result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=20)
        assert result.returncode != 0 and "exact frozen parent manifest SHA" in result.stderr
        assert json.loads(out.read_bytes())["status"] == "FAILED"
        checked["actual_source_CLI_stale_manifest_sha_rejected_with_FAILED_receipt"] = True
        assert "cadquery" not in sys.modules and not any(name == "OCP" or name.startswith("OCP.") for name in sys.modules)
        checked["in_process_controls_did_not_import_cadquery_or_OCP"] = True
    return checked


def main():
    if "--controls" in sys.argv:
        print(json.dumps(controls(), sort_keys=True))
        return
    start = time.monotonic()
    before = {str(path.relative_to(ROOT)): sha(path) for path in EXPECTED}
    assert all(sha(path) == digest for path, digest in EXPECTED.items())
    environment = dict(os.environ, PYTHONPATH=str(ROOT))
    groups = []
    for path in (CORRECTED.with_name("test_output_reservation.py"), INTAKE / "test_extended_intake.py", INTAKE.parent / "current-source-export-v1/test_export.py"):
        command = [sys.executable, "-B", "-m", "pytest", "-q", str(path.relative_to(ROOT))]
        result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        groups.append({"command": command, "result": result.stdout.strip(), "stderr": result.stderr})
    result = subprocess.run([sys.executable, "-B", str(OWN), "--controls"], cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    checked = json.loads(result.stdout)
    lint_command = [sys.executable, "-B", "-m", "ruff", "check", str(OWN.relative_to(ROOT))]
    lint = subprocess.run(lint_command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=30)
    assert lint.returncode == 0, lint.stdout + lint.stderr
    after = {str(path.relative_to(ROOT)): sha(path) for path in EXPECTED}
    assert before == after
    receipt = {
        "schema": "independent_cached_solid_intake_testing_review/v2",
        "status": "PASS_NO_SUBSTANTIAL_TESTING_FINDINGS",
        "scope": "Current extended-cleat cached-solid intake and corrected output reservation only",
        "reviewer": "/root/intake_final_testing",
        "branch": "master",
        "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)},
        "frozen_target_sha256": before,
        "frozen_target_bytes_unchanged": True,
        "separate_process_test_groups": groups,
        "independent_isolated_controls": checked,
        "review_helper_lint": {"command": lint_command, "result": lint.stdout.strip()},
        "substantial_findings": [],
        "genuine_CAD_BREP_native_browser_K_q_force_load_or_candidate_execution_performed": False,
        "parent_slot_created_or_authorized": False,
        "temporary_slot_fixtures": "deliberately invalid; removed after CLI rejection controls",
        "elapsed_seconds": time.monotonic() - start,
        "remaining": "Parent owns final validation, exact same-manifest serial slot and authentic cached-solid extraction; no structural or physical readiness follows from these tests",
    }
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"], "controls": len(checked), "groups": [r["result"] for r in groups]}))


if __name__ == "__main__":
    main()
