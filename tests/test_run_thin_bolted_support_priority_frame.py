"""Check the new orchestration contract without preparing a candidate model."""

import copy
import hashlib
import json
import sys

import pytest

from scripts import run_thin_bolted_support_priority_frame as driver


def arguments(tmp_path, **options):
    result = ["priority", "--out", str(tmp_path / "field.json"),
              "--support-prior-failure", "fea/generated/prior-failure.json",
              "--support-prior-sha256", "c" * 64,
              "--support-priority-method-receipt", str(driver.PRIORITY_RECEIPT),
              "--support-priority-method-sha256", "b" * 64,
              "--support-mask-budget", "64", "--support-method-receipt", str(driver.CORE_RECEIPT),
              "--support-method-sha256", driver.CORE_RECEIPT_SHA256]
    for key, value in options.items():
        result.extend(["--" + key.replace("_", "-"), str(value)])
    return result


def prepare_stubs(monkeypatch):
    previous = {"source_sha256": {"prior": "c" * 64},
                "previous_field_path": "fea/generated/prior-failure.json",
                "previous_field_sha256": "c" * 64}
    monkeypatch.setattr(driver.scheduling, "load_previous_schedule", lambda *args: copy.deepcopy(previous))
    monkeypatch.setattr(driver, "source_pins", lambda *args: {"all-frozen": "d" * 64})
    monkeypatch.setattr(driver.core.lean.common, "bind_common_metadata", lambda report, *args: report)
    return previous


@pytest.mark.parametrize("suffix", ["", ".interrupted.json", ".priority-interrupted.json"])
def test_existing_fields_and_both_interruption_records_stop_before_preparation(monkeypatch, tmp_path, suffix):
    path = tmp_path / ("field.json" + suffix)
    path.write_bytes(b"preserve prior evidence")
    monkeypatch.setattr(sys, "argv", arguments(tmp_path))
    monkeypatch.setattr(driver.scheduling, "load_previous_schedule", lambda *args: pytest.fail("prepared prior field"))
    monkeypatch.setattr(driver.core, "main", lambda: pytest.fail("prepared model"))
    with pytest.raises(SystemExit):
        driver.main()
    assert path.read_bytes() == b"preserve prior evidence"


@pytest.mark.parametrize("flag", ["--support-method-receipt", "--support-method-sha256", "--support-priority-method-receipt"])
def test_receipt_mismatch_stops_before_any_preparation(monkeypatch, tmp_path, flag):
    argv = arguments(tmp_path)
    argv[argv.index(flag) + 1] = "unreviewed-receipt.json" if flag.endswith("receipt") else "0" * 64
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(driver.scheduling, "load_previous_schedule", lambda *args: pytest.fail("prepared prior field"))
    monkeypatch.setattr(driver.core, "main", lambda: pytest.fail("prepared model"))
    with pytest.raises(SystemExit):
        driver.main()


def test_actual_outer_command_and_fresh_initialization_are_preserved(monkeypatch, tmp_path):
    previous = prepare_stubs(monkeypatch)
    captured = {}
    argv = arguments(tmp_path)

    def solve(*args, **kwargs):
        captured["solver_arguments"] = args
        captured["solver_options"] = kwargs
        return {"converged": False}

    def core_main():
        captured["internal_argv"] = sys.argv.copy()
        driver.core.search.compatible_contact_solve("original-matrix", warm_q=None, max_iterations=300)
        report = {"parameters": {}, "source_sha256": {"original": "a" * 64}}
        captured["report"] = driver.core.lean.common.bind_common_metadata(report)

    monkeypatch.setattr(driver.scheduling, "compatible_contact_solve", solve)
    monkeypatch.setattr(driver.core, "main", core_main)
    old_metadata = driver.core.lean.common.bind_common_metadata
    old_solver = driver.core.search.compatible_contact_solve
    old_finished = driver.core.lean.common.finished.bind_finished_state
    monkeypatch.setattr(sys, "argv", argv)
    driver.main()
    execution = captured["report"]["support_priority_execution"]
    assert execution["command"] == [sys.executable, "-m", "scripts.run_thin_bolted_support_priority_frame", *argv[1:]]
    assert execution["prior_failure_sha256"] == previous["previous_field_sha256"]
    assert execution["prior_q_or_forces_used"] is False
    assert execution["nested_support_search_execution_is_reused_internal_call"] is True
    assert "--support-prior-failure" not in captured["internal_argv"]
    assert "--support-priority-method-receipt" not in captured["internal_argv"]
    assert "--support-mask-budget" in captured["internal_argv"]
    assert "--support-method-receipt" in captured["internal_argv"]
    assert captured["solver_arguments"] == ("original-matrix",)
    assert captured["solver_options"]["warm_q"] is None
    assert captured["solver_options"]["previous_schedule"] == previous
    assert "diagnostic_last_q" not in captured["solver_options"]
    assert sys.argv is argv
    assert driver.core.lean.common.bind_common_metadata is old_metadata
    assert driver.core.search.compatible_contact_solve is old_solver
    assert driver.core.lean.common.finished.bind_finished_state is old_finished


def test_complete_physical_input_validation_follows_finished_state_binding(monkeypatch, tmp_path):
    prepare_stubs(monkeypatch)
    observed = []
    finished = driver.core.lean.common.finished

    def binding(report, *args):
        assert report["parameters"]["support_priority_prior_failure_sha256"] == "c" * 64
        report["finished_floor_footprints"] = ["final physical footprints"]
        report["state_id"] = "bound-new-priority-state"
        observed.append("finished")
        return report

    def validate(report, previous):
        assert report["finished_floor_footprints"] == ["final physical footprints"]
        assert report["state_id"] == "bound-new-priority-state"
        observed.append("validate")

    def core_main():
        report = driver.core.lean.common.bind_common_metadata({"parameters": {}, "source_sha256": {}})
        finished.bind_finished_state(report)

    monkeypatch.setattr(finished, "bind_finished_state", binding)
    monkeypatch.setattr(driver.scheduling, "validate_current_report", validate)
    monkeypatch.setattr(driver.core, "main", core_main)
    monkeypatch.setattr(sys, "argv", arguments(tmp_path))
    driver.main()
    assert observed == ["finished", "validate"]


@pytest.mark.parametrize("failure", ["changed-physical-input", "changed-source"])
def test_failure_restores_all_runtime_seams_and_original_argv(monkeypatch, tmp_path, failure):
    prepare_stubs(monkeypatch)
    finished = driver.core.lean.common.finished
    monkeypatch.setattr(finished, "bind_finished_state", lambda report, *args: report)
    if failure == "changed-source":
        calls = []

        def pins(*args):
            calls.append(True)
            return {"all-frozen": ("d" if len(calls) == 1 else "e") * 64}

        monkeypatch.setattr(driver, "source_pins", pins)
    else:
        monkeypatch.setattr(driver.scheduling, "validate_current_report",
                            lambda *args: (_ for _ in ()).throw(ValueError("physical inputs changed")))

    def core_main():
        report = driver.core.lean.common.bind_common_metadata({"parameters": {}, "source_sha256": {}})
        finished.bind_finished_state(report)

    monkeypatch.setattr(driver.core, "main", core_main)
    old_metadata = driver.core.lean.common.bind_common_metadata
    old_solver = driver.core.search.compatible_contact_solve
    old_finished = finished.bind_finished_state
    argv = arguments(tmp_path)
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(ValueError):
        driver.main()
    assert sys.argv is argv
    assert driver.core.lean.common.bind_common_metadata is old_metadata
    assert driver.core.search.compatible_contact_solve is old_solver
    assert finished.bind_finished_state is old_finished


def test_outer_interruption_binds_inner_bytes_without_rewriting_them(monkeypatch, tmp_path):
    prepare_stubs(monkeypatch)
    monkeypatch.setattr(driver.frame, "ROOT", tmp_path)
    monkeypatch.setattr(driver.frame, "PACKET", tmp_path)
    monkeypatch.setattr(driver, "PRIORITY_RECEIPT", tmp_path / "receipt.json")
    output = tmp_path / "field.json"
    inner = output.with_name(output.name + ".interrupted.json")
    raw = b'{"schema":"original inner failed interruption"}\n'

    def core_main():
        inner.write_bytes(raw)
        raise SystemExit(124)

    monkeypatch.setattr(driver.core, "main", core_main)
    argv = arguments(tmp_path)
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as error:
        driver.main()
    assert error.value.code == 124
    record = json.loads(output.with_name(output.name + ".priority-interrupted.json").read_bytes())
    assert record["internal_interruption_sha256"] == hashlib.sha256(raw).hexdigest()
    assert record["support_priority_execution"]["command"][3:] == argv[1:]
    assert record["accepted_field_exported"] is False
    assert record["usable_conditional_actions"] is False
    assert not any(record["release"].values())
    assert inner.read_bytes() == raw
    assert not output.exists()


def receipt_fixture(monkeypatch, tmp_path):
    monkeypatch.setattr(driver.frame, "ROOT", tmp_path)
    sources = {}
    for path in (driver.OWN, driver.SCHEDULE_PATH, "core-source.py"):
        source = tmp_path / path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(path)
        sources[path] = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(driver, "LOADED_DRIVER_SHA256", sources[driver.OWN])
    monkeypatch.setattr(driver.scheduling, "LOADED_PRODUCER_SHA256", sources[driver.SCHEDULE_PATH])
    monkeypatch.setattr(driver.core, "source_pins", lambda *args: ({"core-source.py": sources["core-source.py"]}, {}))
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(driver, "PRIORITY_RECEIPT", receipt)
    record = {"schema": driver.METHOD_SCHEMA, "method_checks_pass": True,
              "released": False, "release": driver.frame.RELEASE, "source_sha256": sources}
    receipt.write_text(json.dumps(record))
    return receipt, record, sources


@pytest.mark.parametrize("change", ["raw", "schema", "checked", "release", "loaded", "current-source", "conflict"])
def test_changed_or_unreviewed_method_sources_are_rejected(monkeypatch, tmp_path, change):
    receipt, record, _ = receipt_fixture(monkeypatch, tmp_path)
    previous = {"source_sha256": {}}
    if change == "schema":
        record["schema"] = "old-unreviewed-method"
    elif change == "checked":
        record["method_checks_pass"] = False
    elif change == "release":
        record["released"] = True
    elif change == "loaded":
        record["source_sha256"][driver.SCHEDULE_PATH] = "0" * 64
    elif change == "current-source":
        (tmp_path / driver.SCHEDULE_PATH).write_text("edited after freeze")
    elif change == "conflict":
        previous["source_sha256"] = {"core-source.py": "0" * 64}
    receipt.write_text(json.dumps(record))
    digest = "0" * 64 if change == "raw" else hashlib.sha256(receipt.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        driver.source_pins(receipt, digest, previous)


def test_frozen_method_and_previous_payload_pins_are_merged(monkeypatch, tmp_path):
    receipt, _, sources = receipt_fixture(monkeypatch, tmp_path)
    previous_path = tmp_path / "previous.json"
    previous_path.write_text("authenticated earlier failure")
    previous_sha = hashlib.sha256(previous_path.read_bytes()).hexdigest()
    digest = hashlib.sha256(receipt.read_bytes()).hexdigest()
    pins = driver.source_pins(receipt, digest, {"source_sha256": {"previous.json": previous_sha}})
    assert pins == {**sources, "previous.json": previous_sha, "receipt.json": digest}
