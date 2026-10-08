"""Check provenance, identity and restoration at the new orchestration seam."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

from scripts import run_thin_bolted_support_search_frame as driver


def arguments(tmp_path, **options):
    out = options.pop("out", tmp_path / "field.json")
    result = ["driver", "--out", str(out), "--support-method-receipt", "receipt.json",
              "--support-method-sha256", "0" * 64]
    for key, value in options.items():
        result.extend(["--" + key.replace("_", "-"), str(value)])
    return result


@pytest.mark.parametrize("extra", [{"support_mask_budget": 0}, {"support_mask_budget": 257},
                                  {"beam_size": 100}, {"shaft_segment": 20},
                                  {"wood_bedding": 2}, {"floor_tangent_stiffness": 99999}])
def test_scope_rejection_happens_before_preparation(monkeypatch, tmp_path, extra):
    monkeypatch.setattr(sys, "argv", arguments(tmp_path, **extra))
    monkeypatch.setattr(driver.lean, "main", lambda: pytest.fail("out-of-scope model prepared"))
    with pytest.raises(SystemExit):
        driver.main()


@pytest.mark.parametrize("suffix", ["", ".interrupted.json"])
def test_failed_prior_field_and_sidecar_are_preserved(monkeypatch, tmp_path, suffix):
    path = tmp_path / ("field.json" + suffix)
    path.write_bytes(b"preserved failure")
    monkeypatch.setattr(sys, "argv", arguments(tmp_path))
    with pytest.raises(SystemExit):
        driver.main()
    assert path.read_bytes() == b"preserved failure"


def test_delegate_records_actual_command_and_only_one_case(monkeypatch, tmp_path):
    pins = {"source": "a" * 64}
    captured = {}
    monkeypatch.setattr(driver, "source_pins", lambda *a: (pins, {}))
    monkeypatch.setattr(driver.lean.common, "bind_common_metadata", lambda report, *a: report)

    def search(*args, **kwargs):
        captured["options"] = kwargs.copy()
        kwargs["branch_observer"]({"phase": "start", "branch_index": 0})
        return {"converged": False}

    def lean_main():
        captured["inner_argv"] = sys.argv.copy()
        driver.lean.incremental.compatible_contact_solve("matrix", max_iterations=300, warm_q=None)
        with pytest.raises(ValueError, match="one joint case"):
            driver.lean.incremental.compatible_contact_solve("matrix")
        report = {"parameters": {}, "source_sha256": {}, "limits": []}
        captured["report"] = driver.lean.common.bind_common_metadata(report, None, {}, ["internal"])

    monkeypatch.setattr(driver.search, "compatible_contact_solve", search)
    monkeypatch.setattr(driver.lean, "main", lean_main)
    old_metadata = driver.lean.common.bind_common_metadata
    old_solver = driver.lean.incremental.compatible_contact_solve
    argv = arguments(tmp_path, support_mask_budget=32)
    monkeypatch.setattr(sys, "argv", argv)
    driver.main()
    execution = captured["report"]["support_state_search_execution"]
    assert execution["command"][1:3] == ["-m", "scripts.run_thin_bolted_support_search_frame"]
    assert execution["command"][3:] == argv[1:]
    assert execution["branch_events"] == [{"phase": "start", "branch_index": 0}]
    assert captured["options"]["mask_budget"] == 32
    assert captured["options"]["warm_q"] is None
    assert "--support-mask-budget" not in captured["inner_argv"]
    assert captured["report"]["parameters"]["support_state_search_mask_budget"] == 32
    assert sys.argv == argv
    assert driver.lean.common.bind_common_metadata is old_metadata
    assert driver.lean.incremental.compatible_contact_solve is old_solver


def test_new_parameters_enter_finished_state_identity():
    result = []
    for budget in (32, 64):
        report = {"state_id": "previous", "case_id": "a12-rear", "accessory_placement": "test",
                  "geometry_cache_sha256": "a" * 64, "parameters": {},
                  "source_sha256": {}, "limits": [], "actions": [{"state_id": "previous"}]}
        driver.bind_search_metadata(report, {}, ["actual"], driver.frame.ROOT / "fea/generated/fixture-receipt",
                                    "b" * 64, budget, [])
        finished = driver.lean.common.finished
        finished.bind_finished_state(report, [], {}, "c" * 64)
        assert report["actions"][0]["state_id"] == report["state_id"]
        result.append(report["state_id"])
    assert result[0] != result[1]


def test_outside_response_interruption_binds_new_sources_and_command(monkeypatch, tmp_path):
    monkeypatch.setattr(driver, "source_pins", lambda *a: ({"new-source": "a" * 64}, {}))
    output = tmp_path / "field.json"

    def lean_main():
        driver.lean.write_interruption(output, ["old-command"], {}, {}, {"phase": "preparation"})

    monkeypatch.setattr(driver.lean, "main", lean_main)
    monkeypatch.setattr(sys, "argv", arguments(tmp_path))
    driver.main()
    report = json.loads(Path(str(output) + ".interrupted.json").read_bytes())
    assert report["command"][2] == "scripts.run_thin_bolted_support_search_frame"
    assert report["source_sha256"]["new-source"] == "a" * 64
    assert report["accepted_field_exported"] is False
    assert report["response"]["gradient_inf_n"] is None
    assert "q" not in report["response"]
    assert not any(report["release"].values())
    assert not output.exists()


def test_receipt_binds_loaded_producers_and_detects_modified_input(monkeypatch, tmp_path):
    monkeypatch.setattr(driver.frame, "ROOT", tmp_path)
    sources = {}
    for path in (driver.OWN, driver.LEAN_DRIVER, driver.SEARCH_PATH):
        source = tmp_path / path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(path)
        sources[path] = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(driver, "LOADED_DRIVER_SHA256", sources[driver.OWN])
    monkeypatch.setattr(driver, "LEAN_DRIVER_SHA256", sources[driver.LEAN_DRIVER])
    monkeypatch.setattr(driver.search, "LOADED_PRODUCER_SHA256", sources[driver.SEARCH_PATH])
    monkeypatch.setattr(driver.search, "source_pins", dict)
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": driver.METHOD_SCHEMA, "method_checks_pass": True,
                                   "released": False, "release": driver.frame.RELEASE,
                                   "source_sha256": sources}))
    digest = hashlib.sha256(receipt.read_bytes()).hexdigest()
    pins, _ = driver.source_pins(receipt, digest)
    assert pins["receipt.json"] == digest
    (tmp_path / driver.SEARCH_PATH).write_text("changed after freeze")
    with pytest.raises(ValueError, match="source changed"):
        driver.source_pins(receipt, digest)


def test_unreleased_method_check_is_required(monkeypatch, tmp_path):
    monkeypatch.setattr(driver.frame, "ROOT", tmp_path)
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": driver.METHOD_SCHEMA, "method_checks_pass": True,
                                   "released": True, "release": driver.frame.RELEASE}))
    with pytest.raises(ValueError, match="unreleased"):
        driver.source_pins(receipt, hashlib.sha256(receipt.read_bytes()).hexdigest())
