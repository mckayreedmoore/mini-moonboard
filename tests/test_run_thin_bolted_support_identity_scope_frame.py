"""Exercise the new outer invocation without repeating a candidate solve."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

from scripts import run_thin_bolted_support_identity_scope_frame as driver
from scripts import thin_bolted_support_identity_scope_admission as admission


def arguments():
    return ["--support-identity-method-receipt", str(driver.METHOD_RECEIPT),
            "--support-identity-method-sha256", "b" * 64,
            "--support-chain-prior-failure", "prior.json", "--support-chain-prior-sha256", "c" * 64,
            "--support-chain-method-receipt", str(driver.chain.METHOD_RECEIPT),
            "--support-chain-method-sha256", driver.CHAIN_RECEIPT_SHA256,
            "--support-method-receipt", str(driver.chain.CORE_RECEIPT),
            "--support-method-sha256", driver.chain.CORE_RECEIPT_SHA256,
            "--support-mask-budget", "64", "--cases", "a12-rear", "--out", "fresh.json"]


def prepare(monkeypatch):
    def original(report, *args):
        return report
    monkeypatch.setattr(driver.chain.core.lean.common, "bind_common_metadata", original)
    monkeypatch.setattr(driver.chain.scheduling, "load_failed_chain", lambda *args, **kwargs: {"cohorts": []})
    monkeypatch.setattr(driver.chain, "source_pins", lambda *args: {"old": "c" * 64})
    monkeypatch.setattr(admission, "source_pins", lambda *args: {"new": "d" * 64})
    calls = []
    monkeypatch.setattr(admission, "verify_recorded_ancestor_scopes", lambda *args, **kwargs: calls.append((args, kwargs)))
    argv = ["outer", *arguments()]
    monkeypatch.setattr(sys, "argv", argv)
    return original, calls, argv


def test_actual_outer_command_source_params_and_reversible_seams(monkeypatch):
    original, calls, argv = prepare(monkeypatch)
    finished = driver.chain.core.lean.common.finished.bind_finished_state
    captured = {}

    def nested():
        captured["arguments"] = sys.argv[1:]
        report = {"source_sha256": {}, "parameters": {}}
        captured["report"] = driver.chain.core.lean.common.bind_common_metadata(report, object())
        assert driver.chain.core.lean.common.finished.bind_finished_state is driver.bind_scoped_finished_state

    monkeypatch.setattr(driver.chain, "main", nested)
    driver.main()
    report = captured["report"]
    assert report["support_identity_scope_execution"]["command"] == [sys.executable, "-m", "scripts.run_thin_bolted_support_identity_scope_frame", *argv[1:]]
    assert captured["arguments"] == arguments()[4:]
    assert report["source_sha256"] == {"old": "c" * 64, "new": "d" * 64}
    assert report["parameters"]["support_mask_schedule_identity_scope_driver_sha256"] == driver.LOADED_DRIVER_SHA256
    assert report["parameters"]["support_mask_schedule_identity_scope_method_receipt_sha256"] == "b" * 64
    assert calls[0][1]["driver_sha256"] == driver.LOADED_DRIVER_SHA256
    assert sys.argv is argv
    assert driver.chain.core.lean.common.bind_common_metadata is original
    assert driver.chain.core.lean.common.finished.bind_finished_state is finished


@pytest.mark.parametrize("flag", ["--support-identity-method-receipt", "--support-chain-method-receipt", "--support-chain-method-sha256"])
def test_reject_changed_fixed_method_paths_and_frozen_chain_receipt(monkeypatch, flag):
    original, _calls, argv = prepare(monkeypatch)
    argv[argv.index(flag) + 1] = "wrong.json" if flag.endswith("receipt") else "0" * 64
    with pytest.raises(SystemExit):
        driver.main()
    assert driver.chain.core.lean.common.bind_common_metadata is original


@pytest.mark.parametrize("failure", [ValueError("nested failed"), SystemExit(124)])
def test_restore_patches_and_arguments_on_failed_nested_execution(monkeypatch, failure):
    original, _calls, argv = prepare(monkeypatch)
    finished = driver.chain.core.lean.common.finished.bind_finished_state

    def nested():
        raise failure

    monkeypatch.setattr(driver.chain, "main", nested)
    with pytest.raises(type(failure)):
        driver.main()
    assert sys.argv is argv
    assert driver.chain.core.lean.common.bind_common_metadata is original
    assert driver.chain.core.lean.common.finished.bind_finished_state is finished


def test_recheck_frozen_sources_before_metadata_write(monkeypatch):
    original, _calls, argv = prepare(monkeypatch)
    revisions = iter(({"new": "d" * 64}, {"new": "e" * 64}))
    monkeypatch.setattr(admission, "source_pins", lambda *args: next(revisions))
    before = {"source_sha256": {}, "parameters": {}}
    untouched = copy.deepcopy(before)
    monkeypatch.setattr(driver.chain, "main", lambda: driver.chain.core.lean.common.bind_common_metadata(before, object()))
    with pytest.raises(ValueError, match="changed during"):
        driver.main()
    assert before == untouched
    assert sys.argv is argv
    assert driver.chain.core.lean.common.bind_common_metadata is original


def test_method_paths_live_in_same_existing_packet():
    assert driver.METHOD_RECEIPT.parent == driver.chain.METHOD_RECEIPT.parent
    assert Path(driver.OWN).name == "run_thin_bolted_support_identity_scope_frame.py"
