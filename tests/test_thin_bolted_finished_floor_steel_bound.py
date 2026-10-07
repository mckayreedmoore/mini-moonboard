"""Independent file-change and state-change fixtures for the source guard."""

import json
from pathlib import Path

import pytest

from scripts import thin_bolted_finished_floor_steel_bound as writer


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(writer, "ROOT", tmp_path)
    producer = tmp_path / "writer.py"
    producer.write_text("fixture")
    monkeypatch.setattr(writer, "__file__", str(producer))
    source = tmp_path / "state.json"
    source.write_text(json.dumps({"state_id": "initial"}))
    report = {"source_sha256": {str(source.relative_to(tmp_path)): writer.sha(source)},
              "state": {"state_id": "initial"}}
    return source, report


def test_read_binding_records_exact_unchanged_source(tmp_path, monkeypatch):
    source, report = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(writer, "consume_finished_state", lambda _: report)
    result = writer.consume_bound_state(source)
    assert result["unchanged_input_binding"]["source_sha256_before_and_after"] == writer.sha(source)
    assert result["unchanged_input_binding"]["state_id_before_and_after"] == "initial"


def test_field_changed_between_reads_is_rejected_even_with_same_state_id(tmp_path, monkeypatch):
    source, report = fixture(tmp_path, monkeypatch)

    def mutate(path: Path):
        path.write_text(json.dumps({"state_id": "initial", "different_force": 1.}))
        return report

    monkeypatch.setattr(writer, "consume_finished_state", mutate)
    with pytest.raises(ValueError, match="changed between support"):
        writer.consume_bound_state(source)


def test_component_state_mismatch_is_rejected_even_with_unchanged_file(tmp_path, monkeypatch):
    source, report = fixture(tmp_path, monkeypatch)
    report["state"]["state_id"] = "different"
    monkeypatch.setattr(writer, "consume_finished_state", lambda _: report)
    with pytest.raises(ValueError, match="initially audited"):
        writer.consume_bound_state(source)
