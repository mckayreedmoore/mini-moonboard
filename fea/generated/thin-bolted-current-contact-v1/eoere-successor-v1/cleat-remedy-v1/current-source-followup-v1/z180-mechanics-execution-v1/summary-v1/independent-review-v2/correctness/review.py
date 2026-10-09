"""Independent inert review of directory-fd reservation around frozen99 build."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import tempfile
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[1]
TARGET = PACKET / "review-fix-v2"
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
TARGETS = {
    "summarize.py": "15dd2c60a1b6db3eeae6e98b0267268a4460c9a6efc86cb711aa8376fb82046f",
    "test_summarize.py": "94cde283b30a6e935992771ab0a1a3d25e7364a5ee1938ff687675e1c3243645",
    "verification.json": "9c279b0e2cbf65bd2b62472c06dd8eb9a694d38dcfa9cadffda3b2e10e5385a5",
}
PRIOR = PACKET / "independent-review-v1/correctness"
PRIOR_HASHES = {"review.py": "14f68f4d0c6d8dfa1ba8b99677a2d22533eca05b058bef3a41cf620e26a2835a",
                "receipt.json": "a491e32721796c88da3df2e91662e29714c9dfc96191e72648b15f850b46d99d"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok):
    if not ok:
        raise AssertionError("independent fd-wrapper review failed")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def evaluate():
    pins = {str((TARGET / name).relative_to(ROOT)): digest for name, digest in TARGETS.items()}
    pins.update({str((PRIOR / name).relative_to(ROOT)): digest for name, digest in PRIOR_HASHES.items()})
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()))
    prior = json.loads((PRIOR / "receipt.json").read_bytes())
    require(prior["findings"] == [])
    pins.update(prior["reviewed_sha256"])
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins)
    tests = module(TARGET / "test_summarize.py", "independent_summary_fd_controls")
    c = tests.c

    @contextmanager
    def fixture():
        with tempfile.TemporaryDirectory(prefix="z180-summary-fd-review-") as directory, pytest.MonkeyPatch.context() as monkeypatch:
            root = Path(directory)
            yield tests.inert.__wrapped__(root, monkeypatch), root, monkeypatch

    count = 0
    with fixture() as (f, _root, _patch):
        tests.test_positive_reserved_before_loading_and_unchanged_delegation(f)
        count += 1
    for replacement in ("symlink", "directory"):
        with fixture() as (f, root, monkeypatch):
            tests.test_actual_canonical_parent_replaced_at_exclusive_leaf_open(f, root, monkeypatch, replacement)
            count += 1
        with fixture() as (f, root, monkeypatch):
            tests.test_parent_replaced_before_directory_handle_open(f, root, monkeypatch, replacement)
            count += 1
    with fixture() as (f, root, monkeypatch):
        tests.test_original_parent_alias_retarget_remains_bound(f, root, monkeypatch)
        count += 1
    for kind in ("existing", "dangling", "late-existing", "traversal", "foreign-parent"):
        with fixture() as (f, root, monkeypatch):
            tests.test_exclusive_or_foreign_output_rejected_before_callbacks(f, root, monkeypatch, kind)
            count += 1
    with fixture() as (f, _root, monkeypatch):
        tests.test_failed_callback_retained_and_no_retry(f, monkeypatch)
        count += 1
    with fixture() as (f, _root, _patch):
        tests.test_corrected_self_pin_required_before_unchanged_build(f)
        count += 1
    with fixture() as (f, _root, _patch):
        tests.test_same_output_two_callers_only_one_delegates(f)
        count += 1
    tests.test_real_frozen_source_load_has_unchanged_build_and_selectors()
    count += 1
    with fixture() as (f, root, monkeypatch):
        tests.test_parent_replaced_after_started_keeps_failed_original_inode(f, root, monkeypatch)
        count += 1
    require(count == 16)

    # Interrupt after reservation and pin admission, before any genuine work.
    with fixture() as (f, _root, monkeypatch):
        original = c.original
        def interrupted():
            a = original()
            def build(*_args):
                raise SystemExit(7)
            return SimpleNamespace(**{**vars(a), "build": build})
        monkeypatch.setattr(c, "original", interrupted)
        with pytest.raises(SystemExit, match="7"):
            c.write_to_file({}, f.out)
        failure = json.loads(f.out.read_bytes())
        require(failure["status"] == "FAILED" and failure["exception"]["type"] == "SystemExit")
        require(not any(failure["release"].values()))

    # Leaf replacement cannot overwrite an unrelated inode, including failure.
    with fixture() as (f, _root, monkeypatch):
        original = c.original
        parked = f.out.with_name("owned-started.json")
        def replaced():
            a = original()
            f.out.rename(parked)
            f.out.write_text("unrelated replacement")
            return a
        monkeypatch.setattr(c, "original", replaced)
        with pytest.raises(ValueError, match="reserved summary inode changed"):
            c.write_to_file({}, f.out)
        require(f.out.read_text() == "unrelated replacement")
        require(json.loads(parked.read_bytes())["status"] == "STARTED")

    with pytest.MonkeyPatch.context() as monkeypatch, redirect_stdout(io.StringIO()) as capture:
        delegate = Mock(return_value={"schema": "inert-result", "cases": [0]})
        monkeypatch.setattr(c, "write_to_file", delegate)
        c.main(["--manifest", "inert.json", "--manifest-sha256", "a"*64, "--out", "inert-out.json"])
        delegate.assert_called_once_with({"path": "inert.json", "sha256": "a"*64}, Path("inert-out.json"))
        require(json.loads(capture.getvalue())["cases"] == 1)
    with pytest.MonkeyPatch.context() as monkeypatch, redirect_stdout(io.StringIO()):
        callback = Mock(side_effect=AssertionError("help reached output"))
        monkeypatch.setattr(c, "write_to_file", callback)
        with pytest.raises(SystemExit) as stopped:
            c.main(["--help"])
        require(stopped.value.code == 0)
        callback.assert_not_called()
    for key in ("FROZEN_SHA", "LOADED_SHA"):
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(c, key, "0"*64)
            with pytest.raises(ValueError, match="adapter bytes changed"):
                c.original()

    # The unchanged real build runs only against the old fabricated fixture,
    # with both real source bytes copied into its temporary repository.
    old_tests = module(PACKET / "test_summarize.py", "independent_summary_fd_build_fixture")
    for missing in (None, "original", "wrapper"):
        with tempfile.TemporaryDirectory(prefix="z180-summary-fd-build-") as directory, pytest.MonkeyPatch.context() as monkeypatch:
            f = old_tests.fixture.__wrapped__(Path(directory), monkeypatch)
            wrapper = f.save("summary-v1/review-fix-v2/summarize.py", (TARGET / "summarize.py").read_bytes())
            f.manifest["source_sha256"][wrapper["path"]] = wrapper["sha256"]
            if missing == "original":
                del f.manifest["source_sha256"][str(old_tests.a.OWN.relative_to(f.root))]
            elif missing == "wrapper":
                del f.manifest["source_sha256"][wrapper["path"]]
            f.ref = f.save("manifest.json", f.manifest)
            monkeypatch.setattr(c, "OWN", f.root / wrapper["path"])
            monkeypatch.setattr(c, "FROZEN", old_tests.a.OWN)
            monkeypatch.setattr(c, "original", lambda: old_tests.a)
            out = old_tests.a.OWN.parent / "runs-v1/fd-review/result.json"
            if missing is None:
                result = c.write_to_file(f.ref, out)
                require(len(result["cases"]) == 6 and result["complete_joint_resistance"] is None)
                require(result["source_sha256"][wrapper["path"]] == TARGETS["summarize.py"])
                require(result["source_sha256"][str(old_tests.a.OWN.relative_to(f.root))] == c.FROZEN_SHA)
                require(not any(result["release"].values()))
                require(json.loads(out.read_bytes()) == result)
            else:
                with pytest.raises(ValueError, match="exact .*source"):
                    c.write_to_file(f.ref, out)
                require(json.loads(out.read_bytes())["status"] == "FAILED")
    require({name: sha(ROOT / name) for name in pins} == before)
    return {
        "schema": "independent_z180_summary_directory_fd_correctness_review/v2", "findings": [],
        "reviewer_source_sha256": sha(Path(__file__)), "reviewed_sha256": pins,
        "reused_original_review_receipt_sha256": PRIOR_HASHES["receipt.json"],
        "checks": {"source_and_target_pins_before_after": len(pins), "inspected_existing_fd_inert_controls": count,
                   "interrupted_build_FAILED_retained": True, "replaced_leaf_not_overwritten": True,
                   "CLI_delegation_and_help_before_output": True, "original_and_wrapper_hash_drift_rejected": 2,
                   "unchanged_build_six_case_inert_positive_with_both_source_pins": True,
                   "missing_original_or_wrapper_pin_FAILED_before_summary": 2},
        "limits": ["Frozen original source joins, selectors and numerical meanings are reused from the bound v1 correctness review.",
                   "Only temporary inert source/JSON/output fixtures executed and removed; no genuine candidate manifest/config/field/roster/summary consumed or created.",
                   "No gate, consumer, reducer, CAD/native/global/operator or solve called; no resistance, adoption, physical acceptance or release follows.",
                   "FAILED retention verified for intact owned leaf under parent replacement/callback interruption; replaced unrelated leaf is preserved and never overwritten."],
    }


if __name__ == "__main__":
    receipt = evaluate()
    with (HERE / "receipt.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"findings": receipt["findings"], "review_sha256": receipt["reviewer_source_sha256"],
                      "receipt_sha256": sha(HERE / "receipt.json"), "checks": receipt["checks"]}))
