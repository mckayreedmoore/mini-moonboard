"""Actual orchestration, compiler-byte and fresh-output controls; inert models."""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("eoere_current_force_bridge_review_fix_fixture", OWN.with_name("bridge.py"))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def run_stub(tmp_path, *, valid_review):
    b = w.frozen()
    events = []
    dummy = tmp_path / "source.json"
    args = SimpleNamespace(run=True, case_id="a12-rear", wall_seconds=10., out=tmp_path / "field.json",
        inputs=dummy, inputs_sha256="a"*64, input_review=dummy, input_review_sha256="b"*64,
        method_input=dummy, method_input_sha256="c"*64)
    ref = lambda sha: {"path": str(dummy.resolve()), "sha256": sha}
    method = {"input": ref(args.inputs_sha256), "input_review": ref(args.input_review_sha256),
              "input_record": ref(args.method_input_sha256)}
    raw, selected, selection = {"raw": True}, {"selected": True}, {"case_id": args.case_id}
    def authenticate(record, data, pins, **kwargs):
        events.append("exact_raw_selected_review")
        assert record == method["input_review"] and data == selected
        assert kwargs == {"raw_data": raw, "selection": selection}
        if not valid_review:
            raise ValueError("invalid independent input review")
        return {}, {}
    def bank_load(data):
        assert data == selected
        events.append("bank_load_panel_dependencies")
        raise RuntimeError("sentinel stops before panel K")
    def methods(_method):
        events.append("methods_bank_callback")
        return SimpleNamespace(correction_context=lambda *_: contextlib.nullcontext()), SimpleNamespace(load_panel_dependencies=bank_load)
    with patch.object(w, "runtime_source_pins", return_value={}), \
            patch.object(b.bundle, "artifact_path", side_effect=lambda path: str(Path(path).resolve())), \
            patch.object(b, "read_method", return_value=method), patch.object(b, "slot_check", return_value={}), \
            patch.object(b, "read_inputs", return_value=(raw, {})), \
            patch.object(b.driver, "select_case", return_value=(selected, selection)), \
            patch.object(b, "verify_selected_case", return_value=None), \
            patch.object(b, "authenticate_review", side_effect=authenticate), patch.object(b, "methods", side_effect=methods), \
            pytest.raises(ValueError if not valid_review else RuntimeError):
        w.run_case(args)
    assert b.OWN == w.FROZEN and b.LOADED_SHA == w.FROZEN_SHA
    assert b.factory.SCHEMA == b.ORIGINAL_SCHEMA and b.factory.read_inputs is b.ORIGINAL_READ
    assert b.factory.authenticate_source_review is b.ORIGINAL_AUTHENTICATE
    failure = json.loads(args.out.read_bytes())
    assert failure["status"] == "FAILED" and failure["accepted_q"] is None and failure["accepted_actions"] is None
    return events, args.out


def test_actual_run_case_rejects_invalid_review_before_any_bank_callback(tmp_path):
    events, path = run_stub(tmp_path, valid_review=False)
    assert events == ["exact_raw_selected_review"]
    assert not path.with_suffix(".json.failed.json").exists()


def test_actual_run_case_valid_review_precedes_bank_and_preserves_failure(tmp_path):
    events, path = run_stub(tmp_path, valid_review=True)
    assert events == ["exact_raw_selected_review", "methods_bank_callback", "bank_load_panel_dependencies"]
    assert path.with_suffix(".json.failed.json").exists()
    with patch.object(w, "frozen", side_effect=AssertionError("duplicate reached imports")), pytest.raises(FileExistsError):
        w.main(["--out", str(path)])


def test_every_reused_source_including_live_floor_admission_is_pinned():
    b = w.frozen()
    pins = w.source_pins()
    for name, sha in b.REUSED.items():
        assert pins[b.bundle.artifact_path(b.PACKET / name)] == sha
    assert pins[b.bundle.artifact_path(b.old_gate.OWN)] == b.REUSED["floor-practical-resolution-v1/admission.py"]
    assert pins[b.bundle.artifact_path(w.FROZEN)] == w.FROZEN_SHA
    assert pins[b.bundle.artifact_path(w.OWN)] == w.LOADED_SHA


def test_changed_owned_admission_copy_refused_by_runtime_pins(tmp_path):
    b = w.frozen()
    name = "floor-practical-resolution-v1/admission.py"
    path = tmp_path / name
    path.parent.mkdir()
    path.write_bytes(b.old_gate.OWN.read_bytes().replace(b"1e-5", b"1e-2"))
    with patch.object(b, "PACKET", tmp_path), patch.object(b, "REUSED", {name: b.REUSED[name]}), \
            patch.object(b, "review_fix_original_source_pins", return_value={}), \
            pytest.raises(ValueError, match="exact compiler/source bytes changed"):
        w.runtime_source_pins(b)


def test_actual_admission_compiler_checks_owned_copy_exact_bytes(tmp_path):
    b = w.frozen()
    path = tmp_path / "admission.py"
    raw = b.old_gate.OWN.read_bytes()
    path.write_bytes(raw)
    context = {**vars(b.old_gate), "runner": SimpleNamespace(FIELD_SCHEMA=b.FIELD_SCHEMA)}
    with patch.dict(b.review_fix_compiler_sources, {path.resolve(): w.digest(raw)}):
        assert callable(w.compile_function(b, path, "require_pending_field", context))
        path.write_bytes(raw.replace(b"1e-5", b"1e-2"))
        with pytest.raises(ValueError, match="exact compiler/source bytes changed"):
            w.compile_function(b, path, "require_pending_field", context)


def test_second_read_of_compiler_bytes_is_checked_immediately_before_parse():
    b = w.frozen()
    raw = b.old_gate.OWN.read_bytes().replace(b"1e-5", b"1e-2")
    fake_path = lambda _path: SimpleNamespace(read_bytes=lambda: raw)
    with patch.object(b, "Path", fake_path), pytest.raises(ValueError, match="immediately before AST parse"):
        w.compile_function(b, b.old_gate.OWN, "require_pending_field", vars(b.old_gate))


def test_nested_execute_compiler_checks_actual_core_bytes(tmp_path):
    b = w.frozen()
    path = tmp_path / "core.py"
    path.write_bytes(b.bundle.CORE.read_bytes() + b"\n# owned mutation\n")
    context = {**vars(b.old_runner), "bundle": SimpleNamespace(CORE=path)}
    compile_execute = w.compile_function(b, b.old_runner.OWN, "compile_execute", context)
    with pytest.raises(ValueError, match="immediately before AST parse"):
        compile_execute(lambda extra=None: extra or {})


def test_context_restores_originals_after_interruption():
    b = w.frozen()
    old_source, old_compile, old_ast = b.source_pins, b.compile_function, b.old_gate.ast
    with pytest.raises(RuntimeError, match="interruption"), w.corrected_context(b):
        assert b.OWN == w.OWN and b.LOADED_SHA == w.LOADED_SHA
        raise RuntimeError("interruption")
    assert b.OWN == w.FROZEN and b.LOADED_SHA == w.FROZEN_SHA
    assert b.source_pins is old_source and b.compile_function is old_compile and b.old_gate.ast is old_ast


def test_declared_force_auditor_compiles_exact_source_and_single_reviewed_literal():
    b = w.frozen()
    with w.corrected_context(b):
        assert callable(b.old_gate.declared_force_auditor())
        with pytest.raises(ValueError, match="unreviewed literal AST expression"):
            b.old_gate.ast.parse("set(FOREIGN_HOSTS)", mode="eval")


@pytest.mark.parametrize("kind", ["file", "dangling_symlink"])
def test_existing_or_dangling_output_refused_before_frozen_loading(tmp_path, kind):
    path = tmp_path / "existing.json"
    if kind == "file":
        path.write_text("preserved")
    else:
        path.symlink_to(tmp_path / "missing-target")
    with patch.object(w, "frozen", side_effect=AssertionError("fresh-output failure reached imports")), pytest.raises(FileExistsError):
        w.main(["--out", str(path)])
    assert path.read_text() == "preserved" if kind == "file" else path.is_symlink()


def test_callback_failure_keeps_exclusive_failed_attempt(tmp_path):
    path = tmp_path / "attempt.json"
    with patch.object(w, "frozen", side_effect=RuntimeError("frozen load sentinel")), pytest.raises(RuntimeError):
        w.main(["--out", str(path)])
    result = json.loads(path.read_bytes())
    assert result["status"] == "FAILED" and result["accepted_q"] is None and result["accepted_actions"] is None
    assert not any(result["release"].values())
    with pytest.raises(FileExistsError):
        w.main(["--out", str(path)])


def test_run_case_dangling_companion_refused_before_method_callback(tmp_path):
    b = w.frozen()
    path = tmp_path / "field.json"
    companion = path.with_suffix(".json.operators.npz")
    companion.symlink_to(tmp_path / "absent.npz")
    args = SimpleNamespace(run=True, case_id="a12-rear", wall_seconds=10., out=path)
    with patch.object(b, "read_method", side_effect=AssertionError("occupied output reached method callback")), \
            pytest.raises(ValueError, match="preserve every existing"):
        w.run_case(args)
    assert companion.is_symlink() and json.loads(path.read_bytes())["status"] == "FAILED"


def test_same_output_subprocess_race_runs_only_one_expensive_callback(tmp_path):
    out, marker = tmp_path / "race.json", tmp_path / "callbacks.txt"
    code = '''
import contextlib,importlib.util,sys,time
from pathlib import Path
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location("race_wrapper",sys.argv[1]);w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
def callback(_args):
    with Path(sys.argv[3]).open("a") as f:f.write("callback\\n")
    time.sleep(.2)
    return {"schema":"stub_preflight","readiness":False}
b=SimpleNamespace(parse_args=lambda argv:SimpleNamespace(mode="preflight"),preflight=callback,core=SimpleNamespace(serial=lambda x:x))
w.frozen=lambda:b
@contextlib.contextmanager
def context(_b):yield _b
w.corrected_context=context
try:sys.exit(w.main(["--out",sys.argv[2]]))
except FileExistsError:sys.exit(3)
'''
    command = [sys.executable, "-c", code, str(w.OWN), str(out), str(marker)]
    workers = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    codes = []
    for worker in workers:
        stdout, stderr = worker.communicate(timeout=10)
        assert not stderr, (stdout, stderr)
        codes.append(worker.returncode)
    assert sorted(codes) == [0, 3]
    assert marker.read_text().splitlines() == ["callback"]
    assert json.loads(out.read_bytes()) == {"schema": "stub_preflight", "readiness": False}


def test_pure_build_inputs_delegates_under_corrected_source_context_only():
    b = w.frozen()
    observed = []
    def build(*refs):
        observed.append((refs, b.OWN, b.LOADED_SHA))
        return {"schema": b.INPUT_SCHEMA, "production_readiness": False}
    refs = ({"path": "export", "sha256": "a"*64}, {"path": "manifest", "sha256": "b"*64}, {"path": "bank", "sha256": "c"*64})
    with patch.object(b, "build_inputs", side_effect=build):
        result = w.build_inputs(*copy.deepcopy(refs))
    assert observed == [(refs, w.OWN, w.LOADED_SHA)] and result["production_readiness"] is False
