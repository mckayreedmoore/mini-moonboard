"""Portable admission-process provenance checks without raw cases or a solve."""

import copy
import datetime

import pytest

from scripts import eoere_current_response as current
from scripts import summarize_eoere_current_response as summary


def process_pair():
    refs = {name: {"path": name + ".json", "sha256": name + "-hash"}
            for name in ["adapter", "inputs", "input_review", "method_input", "slot"]}
    execution_ref = {"path": "execution.json", "sha256": "execution-hash"}
    field_ref = {"path": "case/field.json", "sha256": "field-hash"}
    admission_ref = {"path": "case/admission.json", "sha256": "admission-hash"}
    command = ["python", "-B", refs["adapter"]["path"], "--mode", "run", "--case-id", "case"]
    pins = {r["path"]: r["sha256"] for r in [*refs.values(), execution_ref]}
    producer = {"schema": "eoere_serial_current_run_process_capture/v1", "case_id": "case",
                "command": command, "cwd": str(current.ROOT), "status": "FINISHED", "exit_code": 0,
                "controlled_environment": {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
                                           "EOERE_PARENT_SERIALIZED_FORCE_RUN": "1"},
                "pins_unchanged": True, "pins_before": pins, "pins_after": copy.deepcopy(pins),
                "historical_state_or_actions_used": False,
                "started_at_utc": "2026-10-10T12:00:00+00:00", "finished_at_utc": "2026-10-10T12:01:00+00:00"}
    admission = copy.deepcopy(producer)
    admission.update(schema="eoere_serial_current_admit_process_capture/v1",
                     command=["python", "-B", refs["adapter"]["path"], "--mode", "admit",
                              "--field", str(current.ROOT / field_ref["path"]),
                              "--out", str(current.ROOT / admission_ref["path"])],
                     controlled_environment={"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"},
                     started_at_utc="2026-10-10T12:01:01+00:00", finished_at_utc="2026-10-10T12:02:00+00:00")
    kwargs = {"case_id": "case", "producer_command": command, "refs": refs, "execution_ref": execution_ref,
              "field_ref": field_ref, "admission_ref": admission_ref,
              "previous_end": datetime.datetime.fromisoformat("2026-10-10T11:59:00+00:00")}
    return producer, admission, kwargs


def test_exact_saved_run_and_admission_are_serial_and_bound():
    producer, admission, kwargs = process_pair()
    assert summary.verify_process_pair(producer, admission, **kwargs) == datetime.datetime.fromisoformat(
        admission["finished_at_utc"])


@pytest.mark.parametrize("mode", ["run", "admit"])
@pytest.mark.parametrize("mutation", ["schema", "case", "command", "cwd", "environment", "exit",
                                      "status", "missing_pin", "changed_pin", "unchanged_flag", "history"])
def test_foreign_or_failed_process_cannot_authenticate_a_case(mode, mutation):
    producer, admission, kwargs = process_pair()
    record = producer if mode == "run" else admission
    if mutation == "schema":
        record["schema"] = "foreign_capture/v1"
    elif mutation == "case":
        record["case_id"] = "different-case"
    elif mutation == "command":
        record["command"] = ["python", "-c", "pass"]
    elif mutation == "cwd":
        record["cwd"] = "/different-checkout"
    elif mutation == "environment":
        record["controlled_environment"]["OMP_NUM_THREADS"] = "8"
    elif mutation == "exit":
        record["exit_code"] = 1
    elif mutation == "status":
        record["status"] = "STARTED"
    elif mutation == "missing_pin":
        del record["pins_before"][kwargs["refs"]["inputs"]["path"]]
        record["pins_after"] = copy.deepcopy(record["pins_before"])
    elif mutation == "changed_pin":
        record["pins_after"][kwargs["refs"]["inputs"]["path"]] = "different-hash"
    elif mutation == "unchanged_flag":
        record["pins_unchanged"] = False
    else:
        record["historical_state_or_actions_used"] = True
    with pytest.raises(ValueError):
        summary.verify_process_pair(producer, admission, **kwargs)


@pytest.mark.parametrize("position", [6, 8])
def test_admission_must_read_own_field_and_write_own_receipt(position):
    producer, admission, kwargs = process_pair()
    admission["command"][position] = str(current.ROOT / "other-case" / "foreign.json")
    with pytest.raises(ValueError, match="command/schema/context"):
        summary.verify_process_pair(producer, admission, **kwargs)


@pytest.mark.parametrize("mutation", ["negative_run", "overlap_audit", "negative_audit", "overlap_previous"])
def test_captured_timestamps_must_establish_serial_execution(mutation):
    producer, admission, kwargs = process_pair()
    if mutation == "negative_run":
        producer["finished_at_utc"] = "2026-10-10T11:59:59+00:00"
    elif mutation == "overlap_audit":
        admission["started_at_utc"] = "2026-10-10T12:00:59+00:00"
    elif mutation == "negative_audit":
        admission["finished_at_utc"] = "2026-10-10T12:01:00+00:00"
    else:
        kwargs["previous_end"] = datetime.datetime.fromisoformat("2026-10-10T12:00:01+00:00")
    with pytest.raises(ValueError, match="run and admit serially"):
        summary.verify_process_pair(producer, admission, **kwargs)
