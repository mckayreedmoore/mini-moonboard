"""Actual CLI subprocesses and fake callbacks; no genuine cached-solid query."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

OWN = Path(__file__).resolve()
EXPORT = OWN.with_name("export.py")
ROOT = OWN.parents[7]
MANIFEST = OWN.parents[2] / "parent-authority-v1/extended-cleat-manifest.json"
MANIFEST_SHA = "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6"
spec = importlib.util.spec_from_file_location("exclusive_output_export_under_test", EXPORT)
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)


def command(out, *, script=EXPORT, extract=False):
    return [sys.executable, "-B", str(script), "--manifest", str(MANIFEST),
            "--manifest-sha256", MANIFEST_SHA, "--out", str(out)] + (["--extract"] if extract else [])


def fake_cli(tmp_path):
    """Run the actual main with only the native producer replaced by a spy."""
    calls = tmp_path / "calls.txt"
    script = tmp_path / "fake-cli.py"
    script.write_text(f'''import importlib.util, os, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("actual_reserving_cli", {str(EXPORT)!r})
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)
original_loader = x.load_frozen
def load_fake_producer():
    frozen = original_loader()
    def produce(*args):
        with Path({str(calls)!r}).open("a") as stream:
            stream.write(str(os.getpid())+"\\n")
        time.sleep(.3)
        return {{"schema": "synthetic_callback_only/v1", "source_sha256": {{}}}}
    frozen.export_native = produce
    frozen.source_plan = produce
    return frozen
x.load_frozen = load_fake_producer
x.main()
''')
    return script, calls


def test_actual_cli_dangling_final_symlink_stops_before_fake_native_callback(tmp_path):
    script, calls = fake_cli(tmp_path)
    target, out = tmp_path / "missing-target.json", tmp_path / "dangling.json"
    out.symlink_to(target)
    result = subprocess.run(command(out, script=script, extract=True), cwd=ROOT, capture_output=True, text=True, check=False, timeout=10)
    assert result.returncode != 0 and "FileExistsError" in result.stderr
    assert out.is_symlink() and not target.exists() and not calls.exists()


def test_two_actual_cli_calls_get_one_reserved_output_and_one_fake_callback(tmp_path):
    script, calls = fake_cli(tmp_path)
    out = tmp_path / "shared-output.json"
    processes = [subprocess.Popen(command(out, script=script, extract=True), cwd=ROOT,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    results = [p.communicate(timeout=10) for p in processes]
    assert sorted(p.returncode for p in processes) == [0, 1]
    assert sum("FileExistsError" in stderr for _, stderr in results) == 1
    assert len(calls.read_text().splitlines()) == 1
    record = json.loads(out.read_bytes())
    assert record["schema"] == "synthetic_callback_only/v1"
    assert record["descriptor_output_reservation"]["method"] == "exclusive-create-before-frozen-intake"


def test_failed_attempt_remains_and_cannot_be_reused(tmp_path):
    out = tmp_path / "failed.json"
    def fail():
        raise ValueError("synthetic callback failed")
    with pytest.raises(ValueError, match="synthetic callback failed"):
        x.reserved_output(out, fail)
    saved = out.read_bytes()
    record = json.loads(saved)
    assert record["status"] == "FAILED" and record["exception"]["type"] == "ValueError"
    with pytest.raises(FileExistsError):
        x.reserved_output(out, lambda: pytest.fail("producer reached for retained attempt"))
    assert out.read_bytes() == saved


def test_abrupt_process_exit_retains_started_attempt(tmp_path):
    out = tmp_path / "interrupted.json"
    code = f'''import importlib.util, os
spec=importlib.util.spec_from_file_location("interrupted_reserved_output", {str(EXPORT)!r})
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
x.reserved_output({str(out)!r}, lambda: os._exit(17))
'''
    result = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, capture_output=True, text=True, check=False, timeout=10)
    assert result.returncode == 17
    assert json.loads(out.read_bytes())["status"] == "STARTED"


def test_actual_native_cli_retains_failure_and_preserves_frozen_parent_marker_gate(tmp_path):
    out = tmp_path / "missing-marker.json"
    environment = {k: v for k, v in os.environ.items() if k != "EOERE_PARENT_SERIALIZED_EXTRACTION"}
    result = subprocess.run(command(out, extract=True), cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=10)
    assert result.returncode != 0 and "parent serialized extraction marker" in result.stderr
    record = json.loads(out.read_bytes())
    assert record["status"] == "FAILED" and record["exception"]["type"] == "ValueError"
    assert "parent serialized extraction marker" in record["exception"]["message"]


def test_actual_source_only_cli_keeps_current_descriptor_schema_and_all_source_pins(tmp_path):
    out = tmp_path / "source-plan.json"
    result = subprocess.run(command(out), cwd=ROOT, capture_output=True, text=True, check=False, timeout=10)
    assert result.returncode == 0, result.stderr
    record = json.loads(out.read_bytes())
    assert record["schema"] == "eoere_extended_cleat_cached_source_export_plan/v1"
    assert record["geometry"]["sha256"] == "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d"
    assert record["manifest"]["sha256"] == MANIFEST_SHA and record["optional_2026_extra"] is False
    assert record["native_queries_deferred"] and record["candidate_K_q_forces_or_acceptance"] is None
    assert len(record["source_sha256"]) == 1077
    assert record["source_sha256"][str(EXPORT.relative_to(ROOT))] == x.LOADED_SHA
    frozen = x.load_frozen()
    frozen.a.verify(record["source_sha256"])
