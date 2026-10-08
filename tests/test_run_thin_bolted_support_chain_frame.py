"""Check the cumulative-chain seam with synthetic orchestration only."""

import copy
import hashlib
import json
import sys

import pytest

from scripts import run_thin_bolted_support_chain_frame as driver


def arguments(tmp_path):
    return ["chain", "--out", str(tmp_path / "field.json"),
            "--support-chain-prior-failure", "fea/generated/prior.json", "--support-chain-prior-sha256", "a" * 64,
            "--support-chain-method-receipt", str(driver.METHOD_RECEIPT), "--support-chain-method-sha256", "b" * 64,
            "--support-mask-budget", "64", "--support-method-receipt", str(driver.CORE_RECEIPT),
            "--support-method-sha256", driver.CORE_RECEIPT_SHA256]


def setup(monkeypatch):
    chain = {"previous_field_path": "fea/generated/prior.json", "previous_field_sha256": "a" * 64,
             "source_sha256": {"frozen": "c" * 64}, "cohorts": [{"local_mask_ids": ["11", "00"]},
             {"local_mask_ids": ["11", "01"]}], "host_order": ["first", "second"],
             "union_mask_ids": ["11", "00", "01"]}
    captured = {}

    def load(*args, **kwargs):
        captured["loader_args"] = args
        captured["loader_options"] = kwargs
        return copy.deepcopy(chain)

    monkeypatch.setattr(driver.scheduling, "load_failed_chain", load)
    monkeypatch.setattr(driver, "source_pins", lambda *args: {"frozen": "c" * 64})
    monkeypatch.setattr(driver.scheduling, "chain_metadata", lambda value: {k: v for k, v in value.items() if k != "source_sha256"})
    monkeypatch.setattr(driver.core.lean.common, "bind_common_metadata", lambda report, *args: report)
    return chain, captured


@pytest.mark.parametrize("suffix", ["", ".interrupted.json", ".chain-interrupted.json"])
def test_existing_evidence_stops_before_lineage_loading(monkeypatch, tmp_path, suffix):
    path = tmp_path / ("field.json" + suffix)
    path.write_bytes(b"preserve")
    monkeypatch.setattr(sys, "argv", arguments(tmp_path))
    monkeypatch.setattr(driver.scheduling, "load_failed_chain", lambda *args, **kwargs: pytest.fail("loaded before fresh-output guard"))
    with pytest.raises(SystemExit):
        driver.main()
    assert path.read_bytes() == b"preserve"


@pytest.mark.parametrize("flag", ["--support-chain-method-receipt", "--support-method-receipt", "--support-method-sha256"])
def test_incompatible_method_stops_before_lineage_loading(monkeypatch, tmp_path, flag):
    argv = arguments(tmp_path)
    argv[argv.index(flag) + 1] = "other-receipt" if flag.endswith("receipt") else "0" * 64
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(driver.scheduling, "load_failed_chain", lambda *args, **kwargs: pytest.fail("loaded incompatible source"))
    with pytest.raises(SystemExit):
        driver.main()


def test_shortened_chain_options_stop_before_lineage_loading(monkeypatch, tmp_path):
    argv = arguments(tmp_path)
    argv[argv.index("--support-chain-prior-failure")] = "--support-chain-prior-fail"
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(driver.scheduling, "load_failed_chain", lambda *args, **kwargs: pytest.fail("loaded unauditable command"))
    with pytest.raises(SystemExit):
        driver.main()


def test_source_contract_actual_command_and_distinct_chain_metadata(monkeypatch, tmp_path):
    chain, captured = setup(monkeypatch)
    argv = arguments(tmp_path)

    def solve(*args, **kwargs):
        captured["solve_args"] = args
        captured["solve_options"] = kwargs
        return {"converged": False}

    def core_main():
        captured["inner_argv"] = sys.argv.copy()
        driver.core.search.compatible_contact_solve("unchanged-K", warm_q=None)
        captured["report"] = driver.core.lean.common.bind_common_metadata(
            {"response": {"converged": False}, "parameters": {}, "source_sha256": {}})

    monkeypatch.setattr(driver.scheduling, "compatible_contact_solve", solve)
    monkeypatch.setattr(driver.core, "main", core_main)
    monkeypatch.setattr(sys, "argv", argv)
    driver.main()
    assert captured["loader_options"] == {"chain_driver_sha256": driver.LOADED_DRIVER_SHA256,
        "method_receipt_path": driver.METHOD_RECEIPT, "method_receipt_sha256": "b" * 64}
    record = captured["report"]
    assert record["support_mask_chain_execution"]["command"] == [sys.executable, "-m", "scripts.run_thin_bolted_support_chain_frame", *argv[1:]]
    assert record["parameters"]["support_mask_schedule_chain_prior_failure_sha256"] == "a" * 64
    assert record["response"]["support_mask_chain_schedule_v1"]["union_mask_ids"] == chain["union_mask_ids"]
    assert "support_mask_schedule_v1" not in record["response"]
    assert "--support-chain-prior-failure" not in captured["inner_argv"]
    assert "--support-mask-budget" in captured["inner_argv"]
    assert captured["solve_options"]["previous_chain"] == chain
    assert captured["solve_options"]["warm_q"] is None
    assert captured["solve_args"] == ("unchanged-K",)
    assert sys.argv is argv


@pytest.mark.parametrize("physical_failure", [False, True])
def test_binding_happens_before_physical_comparison_and_restores_seams(monkeypatch, tmp_path, physical_failure):
    setup(monkeypatch)
    finished = driver.core.lean.common.finished
    order = []

    def binding(report, *args):
        assert "support_mask_schedule_chain_method_sha256" in report["parameters"]
        report["state_id"] = "finished-identity"
        report["finished_floor_footprints"] = ["finished-physical-input"]
        order.append("finished")
        return report

    def validate(report, chain):
        assert report["state_id"] == "finished-identity"
        assert report["finished_floor_footprints"] == ["finished-physical-input"]
        order.append("validate")
        if physical_failure:
            raise ValueError("changed physical inputs")

    def core_main():
        report = driver.core.lean.common.bind_common_metadata({"response": {}, "parameters": {}, "source_sha256": {}})
        finished.bind_finished_state(report)

    monkeypatch.setattr(finished, "bind_finished_state", binding)
    monkeypatch.setattr(driver.scheduling, "validate_current_report", validate)
    monkeypatch.setattr(driver.core, "main", core_main)
    old_binding = finished.bind_finished_state
    old_metadata = driver.core.lean.common.bind_common_metadata
    old_solver = driver.core.search.compatible_contact_solve
    argv = arguments(tmp_path)
    monkeypatch.setattr(sys, "argv", argv)
    if physical_failure:
        with pytest.raises(ValueError, match="physical inputs"):
            driver.main()
    else:
        driver.main()
    assert order == ["finished", "validate"]
    assert sys.argv is argv
    assert finished.bind_finished_state is old_binding
    assert driver.core.lean.common.bind_common_metadata is old_metadata
    assert driver.core.search.compatible_contact_solve is old_solver


def test_full_wall_failure_preserves_input_lineage_but_no_accepted_q(monkeypatch, tmp_path):
    chain, captured = setup(monkeypatch)

    def core_main():
        captured["report"] = driver.core.lean.common.bind_common_metadata({
            "response": {"converged": False, "wall_time_limit_reached": True},
            "parameters": {}, "source_sha256": {}})

    monkeypatch.setattr(driver.core, "main", core_main)
    monkeypatch.setattr(sys, "argv", arguments(tmp_path))
    driver.main()
    response = captured["report"]["response"]
    assert response["support_mask_chain_schedule_v1"]["cohorts"] == chain["cohorts"]
    assert response["wall_time_limit_reached"] is True
    assert response["converged"] is False
    assert "q" not in response


def test_outer_sidecar_binds_original_interruption_bytes(monkeypatch, tmp_path):
    setup(monkeypatch)
    monkeypatch.setattr(driver.frame, "ROOT", tmp_path)
    monkeypatch.setattr(driver, "METHOD_RECEIPT", tmp_path / "chain-method.json")
    path = tmp_path / "field.json.interrupted.json"
    payload = b'{}\n'

    def core_main():
        path.write_bytes(payload)
        raise SystemExit(124)

    monkeypatch.setattr(driver.core, "main", core_main)
    argv = arguments(tmp_path)
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as error:
        driver.main()
    assert error.value.code == 124
    record = json.loads((tmp_path / "field.json.chain-interrupted.json").read_bytes())
    assert record["internal_interruption_sha256"] == hashlib.sha256(payload).hexdigest()
    assert record["support_mask_chain_execution"]["command"][3:] == argv[1:]
    assert record["usable_conditional_actions"] is False
    assert record["accepted_field_exported"] is False
    assert not any(record["release"].values())
    assert path.read_bytes() == payload
