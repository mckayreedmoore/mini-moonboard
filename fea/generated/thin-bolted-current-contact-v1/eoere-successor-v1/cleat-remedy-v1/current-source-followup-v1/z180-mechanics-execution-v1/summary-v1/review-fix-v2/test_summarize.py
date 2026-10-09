"""Inert anchored-output controls only; no genuine summary or pair."""
import hashlib
import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("z180_summary_output_v2", HERE/"summarize.py")
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)
REAL_FROZEN = c.FROZEN


@pytest.fixture
def inert(tmp_path, monkeypatch):
    summary = tmp_path/"summary-v1"
    summary.mkdir()
    monkeypatch.setattr(c, "FROZEN", summary/"summarize.py")
    out = summary/"runs-v1/attempt/out.json"
    out.parent.mkdir(parents=True)
    calls = []
    root = next(p for p in c.OWN.parents if (p/"AGENTS.md").exists())
    manifest = {"source_sha256": {str(c.OWN.relative_to(root)): c.LOADED_SHA}}
    result = {"schema": "inert-result", "cases": ["inert"], "release": c.RELEASE}
    def original():
        assert json.loads(out.read_bytes())["status"] == "STARTED"
        calls.append("load")
        return SimpleNamespace(ROOT=root, decode=json.loads, checked=lambda *_: json.dumps(manifest).encode(),
            build=lambda *_: calls.append("build") or result)
    monkeypatch.setattr(c, "original", original)
    return SimpleNamespace(out=out, summary=summary, calls=calls, manifest=manifest, result=result)


def test_positive_reserved_before_loading_and_unchanged_delegation(inert):
    assert c.write_to_file({}, inert.out) is inert.result
    assert json.loads(inert.out.read_bytes()) == inert.result
    assert inert.calls == ["load", "build"]


@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_actual_canonical_parent_replaced_at_exclusive_leaf_open(inert, tmp_path, monkeypatch, replacement):
    parent, parked, foreign = inert.out.parent, inert.out.parent.with_name("parked"), tmp_path/"foreign"
    foreign.mkdir()
    original_open = os.open
    def attacked(path, flags, *args, **kwargs):
        if path == inert.out.name and kwargs.get("dir_fd") is not None:
            assert flags & os.O_EXCL and flags & os.O_NOFOLLOW
            parent.rename(parked)
            if replacement == "symlink":
                parent.symlink_to(foreign, target_is_directory=True)
            else:
                parent.mkdir()
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(c.os, "open", attacked)
    with pytest.raises(ValueError, match="canonical parent identity changed"):
        c.write_to_file({}, inert.out)
    assert not (foreign/inert.out.name).exists()
    if replacement == "directory":
        assert not inert.out.exists()
    failed = json.loads((parked/inert.out.name).read_bytes())
    assert failed["status"] == "FAILED" and failed["directory_fd_anchored"] is True
    assert inert.calls == []


@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_parent_replaced_before_directory_handle_open(inert, tmp_path, monkeypatch, replacement):
    parent, parked, foreign = inert.out.parent, inert.out.parent.with_name("parked"), tmp_path/"foreign"
    foreign.mkdir()
    original_open = os.open
    def attacked(path, flags, *args, **kwargs):
        if path == parent and flags & os.O_DIRECTORY:
            parent.rename(parked)
            if replacement == "symlink":
                parent.symlink_to(foreign, target_is_directory=True)
            else:
                parent.mkdir()
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(c.os, "open", attacked)
    with pytest.raises((ValueError, OSError)):
        c.write_to_file({}, inert.out)
    assert not (parked/inert.out.name).exists() and not (foreign/inert.out.name).exists()
    assert inert.calls == []


def test_original_parent_alias_retarget_remains_bound(inert, tmp_path, monkeypatch):
    alias, foreign = inert.out.parent.with_name("alias"), tmp_path/"foreign"
    foreign.mkdir()
    alias.symlink_to(inert.out.parent, target_is_directory=True)
    original_open = os.open
    def attacked(path, flags, *args, **kwargs):
        if path == inert.out.parent and flags & os.O_DIRECTORY:
            alias.unlink()
            alias.symlink_to(foreign, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(c.os, "open", attacked)
    assert c.write_to_file({}, alias/inert.out.name) is inert.result
    assert json.loads(inert.out.read_bytes()) == inert.result
    assert not (foreign/inert.out.name).exists()


@pytest.mark.parametrize("kind", ["existing", "dangling", "late-existing", "traversal", "foreign-parent"])
def test_exclusive_or_foreign_output_rejected_before_callbacks(inert, tmp_path, monkeypatch, kind):
    out = inert.out
    if kind == "existing":
        out.write_text("preserve")
    elif kind == "dangling":
        out.symlink_to(tmp_path/"absent")
    elif kind == "traversal":
        out = out.parent/".."/out.name
    elif kind == "foreign-parent":
        out = tmp_path/"foreign/out.json"
    else:
        original_open = os.open
        def occupied(path, flags, *args, **kwargs):
            if path == inert.out.name and kwargs.get("dir_fd") is not None:
                inert.out.write_text("late preserve")
            return original_open(path, flags, *args, **kwargs)
        monkeypatch.setattr(c.os, "open", occupied)
    with pytest.raises((ValueError, FileExistsError)):
        c.write_to_file({}, out)
    assert inert.calls == []
    if kind in ("existing", "late-existing"):
        assert inert.out.read_text().endswith("preserve")


def test_failed_callback_retained_and_no_retry(inert, monkeypatch):
    def failed():
        assert json.loads(inert.out.read_bytes())["status"] == "STARTED"
        raise RuntimeError("inert source failure")
    monkeypatch.setattr(c, "original", failed)
    with pytest.raises(RuntimeError, match="inert source failure"):
        c.write_to_file({}, inert.out)
    raw = inert.out.read_bytes()
    assert json.loads(raw)["status"] == "FAILED"
    with pytest.raises(FileExistsError):
        c.write_to_file({}, inert.out)
    assert inert.out.read_bytes() == raw


def test_corrected_self_pin_required_before_unchanged_build(inert):
    inert.manifest["source_sha256"].clear()
    with pytest.raises(ValueError, match="corrected output adapter source pin"):
        c.write_to_file({}, inert.out)
    assert inert.calls == ["load"] and json.loads(inert.out.read_bytes())["status"] == "FAILED"


def test_same_output_two_callers_only_one_delegates(inert):
    def attempt():
        try:
            c.write_to_file({}, inert.out)
            return "success"
        except FileExistsError:
            return "occupied"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: attempt(), range(2))) == ["occupied", "success"]
    assert inert.calls == ["load", "build"]


def test_real_frozen_source_load_has_unchanged_build_and_selectors():
    a = c.original()
    assert a.OWN == REAL_FROZEN
    assert hashlib.sha256(REAL_FROZEN.read_bytes()).hexdigest() == c.FROZEN_SHA
    assert a.build.__code__.co_filename == str(REAL_FROZEN)
    assert a.SELECTORS["sha256"] == "0547b984f150bb9bbd4dbe25b50825a12c047de70bcb1d86a267abd58a935735"


def test_parent_replaced_after_started_keeps_failed_original_inode(inert, tmp_path, monkeypatch):
    parent, parked, foreign = inert.out.parent, inert.out.parent.with_name("parked"), tmp_path/"foreign"
    foreign.mkdir()
    original = c.original
    def changed():
        a = original()
        parent.rename(parked)
        parent.symlink_to(foreign, target_is_directory=True)
        return a
    monkeypatch.setattr(c, "original", changed)
    with pytest.raises(ValueError, match="canonical parent identity changed"):
        c.write_to_file({}, inert.out)
    assert json.loads((parked/inert.out.name).read_bytes())["status"] == "FAILED"
    assert not (foreign/inert.out.name).exists()
