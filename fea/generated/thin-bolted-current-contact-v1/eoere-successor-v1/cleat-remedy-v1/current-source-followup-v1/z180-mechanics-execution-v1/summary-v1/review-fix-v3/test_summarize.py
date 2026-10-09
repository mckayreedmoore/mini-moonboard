"""Inert whole-ancestry ownership controls; no candidate roster or result."""
import hashlib
import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("z180_summary_output_v3", HERE/"summarize.py")
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)
REAL_SUMMARY = c.SUMMARY_ROOT


@pytest.fixture
def inert(tmp_path, monkeypatch):
    summary = tmp_path/"summary-v1"
    summary.mkdir()
    monkeypatch.setattr(c, "SUMMARY_ROOT", summary)
    monkeypatch.setattr(c, "ROOT_ID", c.identity(summary.lstat()))
    out = summary/"runs-v1/attempt/nested/out.json"
    out.parent.mkdir(parents=True)
    calls = []
    root = next(p for p in c.OWN.parents if (p/"AGENTS.md").exists())
    manifest = {"source_sha256": {str(c.OWN.relative_to(root)): c.LOADED_SHA,
                                str(c.V2.relative_to(root)): c.V2_SHA}}
    result = {"schema": "inert-result", "cases": ["inert"], "release": c.RELEASE}
    def original():
        assert json.loads(out.read_bytes())["status"] == "STARTED"
        calls.append("load")
        return SimpleNamespace(ROOT=root, decode=json.loads, checked=lambda *_: json.dumps(manifest).encode(),
            build=lambda *_: calls.append("build") or result)
    monkeypatch.setattr(c, "original", original)
    return SimpleNamespace(out=out, summary=summary, calls=calls, manifest=manifest, result=result)


def replace(target, replacement, foreign):
    """Retain the actual old subtree and supply a synthetic replacement."""
    parked = target.with_name(target.name+"-parked")
    target.rename(parked)
    if replacement == "symlink":
        target.symlink_to(foreign, target_is_directory=True)
    else:
        target.mkdir()
    return parked


def target_for(inert, level):
    return inert.summary.joinpath(*("runs-v1", "attempt", "nested")[:level])


def test_positive_reserved_before_loading_and_unchanged_delegation(inert):
    assert c.write_to_file({}, inert.out) is inert.result
    assert json.loads(inert.out.read_bytes()) == inert.result
    assert inert.calls == ["load", "build"]


def test_missing_parents_created_only_through_held_directory_fds(inert, monkeypatch):
    for parent in (inert.out.parent, inert.out.parent.parent, inert.out.parent.parent.parent):
        parent.rmdir()
    original_mkdir = os.mkdir
    created = []
    def anchored(path, *args, **kwargs):
        assert kwargs.get("dir_fd") is not None
        created.append(path)
        return original_mkdir(path, *args, **kwargs)
    monkeypatch.setattr(c.os, "mkdir", anchored)
    assert c.write_to_file({}, inert.out) is inert.result
    assert created == ["runs-v1", "attempt", "nested"]


@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_source_owned_root_replaced_before_call_rejects_import_identity(inert, tmp_path, replacement):
    foreign = tmp_path/"foreign"
    foreign.mkdir()
    parked = replace(inert.summary, replacement, foreign)
    with pytest.raises((ValueError, OSError)):
        c.write_to_file({}, inert.out)
    assert not list(foreign.rglob("out.json")) and not list(parked.rglob("out.json"))
    assert inert.calls == []


@pytest.mark.parametrize("level", [0, 1, 2, 3], ids=["root", "runs", "attempt", "nested"])
@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_each_directory_replaced_immediately_before_open(inert, tmp_path, monkeypatch, level, replacement):
    target, foreign = target_for(inert, level), tmp_path/"foreign"
    foreign.mkdir()
    original_open, changed = os.open, []
    def attacked(path, flags, *args, **kwargs):
        expected = target if level == 0 else target.name
        if path == expected and flags & os.O_DIRECTORY and not changed:
            changed.append(replace(target, replacement, foreign))
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(c.os, "open", attacked)
    with pytest.raises((ValueError, OSError)):
        c.write_to_file({}, inert.out)
    assert len(changed) == 1 and inert.calls == []
    assert not list(foreign.rglob("out.json")) and not list(changed[0].rglob("out.json"))


def test_runs_ancestor_retarget_after_mkdir_cannot_redirect_following_stat(inert, tmp_path, monkeypatch):
    for parent in (inert.out.parent, inert.out.parent.parent, inert.out.parent.parent.parent):
        parent.rmdir()
    runs, foreign = inert.summary/"runs-v1", tmp_path/"foreign"
    (foreign/"attempt/nested").mkdir(parents=True)
    original_mkdir, changed = os.mkdir, []
    def attacked(path, *args, **kwargs):
        value = original_mkdir(path, *args, **kwargs)
        if path == "runs-v1" and kwargs.get("dir_fd") is not None:
            parked = runs.with_name("runs-parked")
            runs.rename(parked)
            runs.symlink_to(foreign, target_is_directory=True)
            changed.append(parked)
        return value
    monkeypatch.setattr(c.os, "mkdir", attacked)
    with pytest.raises(ValueError, match="ancestor is not a directory"):
        c.write_to_file({}, inert.out)
    assert len(changed) == 1 and inert.calls == []
    assert not list(foreign.rglob("out.json")) and not list(changed[0].rglob("out.json"))


@pytest.mark.parametrize("phase", ["leaf-open", "after-started"])
@pytest.mark.parametrize("level", [0, 1, 2, 3], ids=["root", "runs", "attempt", "nested"])
@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_all_held_ancestors_replaced_keep_failed_in_original_subtree(
        inert, tmp_path, monkeypatch, phase, level, replacement):
    target, foreign = target_for(inert, level), tmp_path/"foreign"
    foreign.mkdir()
    relative_leaf = inert.out.relative_to(target)
    changed = []
    if phase == "leaf-open":
        original_open = os.open
        def attacked(path, flags, *args, **kwargs):
            if path == inert.out.name and flags & os.O_EXCL and not changed:
                changed.append(replace(target, replacement, foreign))
            return original_open(path, flags, *args, **kwargs)
        monkeypatch.setattr(c.os, "open", attacked)
    else:
        original = c.original
        def attacked():
            a = original()
            changed.append(replace(target, replacement, foreign))
            return a
        monkeypatch.setattr(c, "original", attacked)
    with pytest.raises(ValueError, match="namespace changed"):
        c.write_to_file({}, inert.out)
    assert len(changed) == 1 and not list(foreign.rglob("out.json"))
    failed = json.loads((changed[0]/relative_leaf).read_bytes())
    assert failed["status"] == "FAILED" and failed["whole_ancestry_directory_fd_anchored"] is True
    assert failed["output_adapter_sha256"] == c.LOADED_SHA
    assert inert.calls == ([] if phase == "leaf-open" else ["load", "build"])
    if replacement == "directory":
        assert not list(target.rglob("out.json"))


def test_original_parent_alias_retarget_stays_bound(inert, tmp_path, monkeypatch):
    alias, foreign = inert.summary/"alias", tmp_path/"foreign"
    foreign.mkdir()
    alias.symlink_to(inert.out.parent, target_is_directory=True)
    original_open = os.open
    def attacked(path, flags, *args, **kwargs):
        if path == "runs-v1" and flags & os.O_DIRECTORY:
            alias.unlink()
            alias.symlink_to(foreign, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(c.os, "open", attacked)
    assert c.write_to_file({}, alias/inert.out.name) is inert.result
    assert not (foreign/inert.out.name).exists()


@pytest.mark.parametrize("kind", ["existing", "dangling", "late-existing", "traversal", "foreign-parent", "dangling-parent"])
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
    elif kind == "dangling-parent":
        alias = inert.summary/"dangling"
        alias.symlink_to(tmp_path/"absent", target_is_directory=True)
        out = alias/out.name
    else:
        original_open = os.open
        def occupied(path, flags, *args, **kwargs):
            if path == inert.out.name and flags & os.O_EXCL:
                inert.out.write_text("late preserve")
            return original_open(path, flags, *args, **kwargs)
        monkeypatch.setattr(c.os, "open", occupied)
    with pytest.raises((ValueError, FileExistsError)):
        c.write_to_file({}, out)
    assert inert.calls == []
    if kind in ("existing", "late-existing"):
        assert inert.out.read_text().endswith("preserve")


def test_failed_callback_retained_and_retry_rejected(inert, monkeypatch):
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


@pytest.mark.parametrize("replacement", ["symlink", "regular-file"])
def test_reserved_leaf_replaced_after_started_never_writes_replacement(inert, tmp_path, monkeypatch, replacement):
    parked, foreign = inert.out.with_name("reserved-parked.json"), tmp_path/"foreign.json"
    foreign.write_text("foreign preserve")
    original = c.original
    def attacked():
        a = original()
        inert.out.rename(parked)
        if replacement == "symlink":
            inert.out.symlink_to(foreign)
        else:
            inert.out.write_text("leaf preserve")
        return a
    monkeypatch.setattr(c, "original", attacked)
    with pytest.raises(ValueError, match="reserved summary inode changed"):
        c.write_to_file({}, inert.out)
    assert foreign.read_text() == "foreign preserve"
    assert json.loads(parked.read_bytes())["status"] == "STARTED"
    if replacement == "regular-file":
        assert inert.out.read_text() == "leaf preserve"


@pytest.mark.parametrize("path", [c.OWN, c.V2], ids=["v3", "v2-loader"])
def test_both_corrected_method_pins_required_before_unchanged_build(inert, path):
    inert.manifest["source_sha256"].pop(str(path.relative_to(next(p for p in c.OWN.parents if (p/"AGENTS.md").exists()))))
    with pytest.raises(ValueError, match="exact v3/output-loader source pin"):
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


def test_real_v2_loader_supplies_only_unchanged_original_build_and_selectors():
    a = c.original()
    frozen = REAL_SUMMARY/"summarize.py"
    assert a.OWN == frozen and a.build.__code__.co_filename == str(frozen)
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == "99ead1194671c82e0e28f905e84c4208cf2a82dc1ed4532aaf1aeb13c0c7124d"
    assert a.SELECTORS["sha256"] == "0547b984f150bb9bbd4dbe25b50825a12c047de70bcb1d86a267abd58a935735"
