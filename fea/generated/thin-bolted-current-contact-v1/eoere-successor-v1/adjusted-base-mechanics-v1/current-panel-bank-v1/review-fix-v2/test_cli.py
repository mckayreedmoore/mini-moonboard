"""Real subprocess CLI checks with source stubs; no panel/CAD imports."""
import json
from pathlib import Path
import select
import subprocess
import sys

import pytest

CLI = Path(__file__).with_name("cli.py")
HARNESS = """
import importlib.util,json,pathlib,sys,types
s=importlib.util.spec_from_file_location('panel_cli_checked',sys.argv[1])
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def load():
 print('SOURCE_REACHED',flush=True)
 assert 'cadquery' not in sys.modules
 assert not any('thin_bolted' in n for n in sys.modules)
 if sys.argv[2]=='block':sys.stdin.readline()
 if sys.argv[2]=='fail':raise ValueError('stub source failure')
 return types.SimpleNamespace(read_sources=lambda: ({},None,{},[],{}),
  input_record=lambda *args:{'stub':True},raised=types.SimpleNamespace(RELEASE={'fabrication_released':False}))
m.load_bank=load
m.main(sys.argv[3:])
"""


def command(out, mode="success"):
    return [sys.executable, "-c", HARNESS, str(CLI), mode, "--out", str(out)]


@pytest.mark.parametrize("kind", ["file", "dangling_symlink", "existing_target_symlink"])
def test_existing_entry_rejects_before_source_loading(tmp_path, kind):
    out, target = tmp_path/"plan.json", tmp_path/"target.json"
    if kind == "file":
        out.write_text("original")
    else:
        if kind == "existing_target_symlink":
            target.write_text("target-original")
        out.symlink_to(target)
    result = subprocess.run(command(out), text=True, capture_output=True, timeout=10)
    assert result.returncode != 0 and "FileExistsError" in result.stderr
    assert "SOURCE_REACHED" not in result.stdout
    if kind == "file":
        assert out.read_text() == "original"
    else:
        assert out.is_symlink()
        if kind == "existing_target_symlink":
            assert target.read_text() == "target-original"
        else:
            assert not target.exists()


def test_fresh_output_success_and_reserved_failure_retained(tmp_path):
    out = tmp_path/"plan.json"
    result = subprocess.run(command(out), text=True, capture_output=True, timeout=10)
    assert result.returncode == 0 and result.stdout.count("SOURCE_REACHED") == 1
    report = json.loads(out.read_text())
    assert report["source_inputs"] == {"stub": True}
    assert report["exclusive_output_reserved_before_source_preparation"]
    assert report["production_bank_prepared"] is False
    failed = tmp_path/"failure.json"
    result = subprocess.run(command(failed, "fail"), text=True, capture_output=True, timeout=10)
    assert result.returncode != 0 and result.stdout.count("SOURCE_REACHED") == 1
    report = json.loads(failed.read_text())
    assert report["status"] == "FAILED_RESERVED_OUTPUT_RETAINED"
    assert report["exception_type"] == "ValueError" and report["exception_message"] == "stub source failure"
    retry = subprocess.run(command(failed), text=True, capture_output=True, timeout=10)
    assert retry.returncode != 0 and "SOURCE_REACHED" not in retry.stdout
    assert json.loads(failed.read_text()) == report


def test_same_output_competitor_rejected_while_first_source_work_is_blocked(tmp_path):
    out = tmp_path/"contended.json"
    first = subprocess.Popen(command(out, "block"), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    try:
        assert select.select([first.stdout], [], [], 10)[0], "first source stub did not start"
        assert first.stdout.readline().strip() == "SOURCE_REACHED"
        assert out.is_file() and out.stat().st_size == 0  # Reservation precedes source work.
        second = subprocess.run(command(out), text=True, capture_output=True, timeout=10)
        assert second.returncode != 0 and "FileExistsError" in second.stderr
        assert "SOURCE_REACHED" not in second.stdout
        _, stderr = first.communicate("continue\n", timeout=10)
        assert first.returncode == 0, stderr
        assert json.loads(out.read_text())["source_inputs"] == {"stub": True}
    finally:
        if first.poll() is None:
            first.kill()
            first.communicate(timeout=10)


def test_wrapper_import_defers_frozen_bank(tmp_path):
    # Even importing this wrapper is stdlib-only; the original bank is loaded after open('x').
    code = "import runpy,sys;runpy.run_path(sys.argv[1]);assert 'cadquery' not in sys.modules;assert 'numpy' not in sys.modules"
    result = subprocess.run([sys.executable, "-c", code, str(CLI)], text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_direct_entrypoint_source_imports_work_outside_repository_with_source_stub(tmp_path):
    code = """
import importlib.util,pathlib,sys
from unittest.mock import patch
import cadquery as cq
s=importlib.util.spec_from_file_location('panel_cli_external_cwd',sys.argv[1])
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
original=m.load_bank
def load():
 bank=original()
 bank.read_sources=lambda: ({},None,{},[],{})
 bank.input_record=lambda *args:{'stub':True}
 return bank
m.load_bank=load
with patch.object(cq.Shape,'importBrep',side_effect=AssertionError('BREP forbidden')) as guard:
 m.main(['--out',sys.argv[2]])
 assert guard.call_count==0
"""
    out = tmp_path/"external-cwd.json"
    result = subprocess.run([sys.executable, "-c", code, str(CLI), str(out)], cwd=tmp_path,
                            text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert json.loads(out.read_text())["source_inputs"] == {"stub": True}
