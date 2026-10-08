"""New saved-field provenance guards; rectangle/torsion fixtures remain reused."""

import json
from copy import deepcopy

import pytest

from scripts import thin_bolted_saved_flange_torsion as writer


@pytest.fixture(scope="module")
def saved_inputs():
    return tuple(json.loads(path.read_bytes()) for path in (writer.OLD_REPORT, writer.OLD_FIELD, writer.steel.LAYOUT))


def test_saved_shapes_and_actual_source_actions_bind_to_original_state(saved_inputs):
    identity, fittings, rows = writer.validate_inputs(*saved_inputs)
    assert writer.canonical_sha(identity).startswith("84ad844f63afddc032cf922c")
    assert len(fittings) == 36 and len(rows) == 72


def test_same_case_forged_steel_force_is_rejected(saved_inputs):
    report, field, layout = deepcopy(saved_inputs)
    report["fresh_demand_comparison"]["flange_comparisons"][0]["external_point_actions_on_steel"][0]["force_on_steel_xyz_n"][0] += 1.
    with pytest.raises(ValueError, match="differ from actual field"):
        writer.validate_inputs(report, field, layout)


@pytest.mark.parametrize("change", ["missing", "duplicate"])
def test_saved_report_requires_complete_unique_flange_census(saved_inputs, change):
    report, field, layout = deepcopy(saved_inputs)
    rows = report["fresh_demand_comparison"]["flange_comparisons"]
    if change == "missing":
        rows.pop()
    else:
        rows[-1] = deepcopy(rows[0])
    with pytest.raises(ValueError, match="all72 unique"):
        writer.validate_inputs(report, field, layout)


@pytest.mark.parametrize("change", ["state", "count", "nonfinite"])
def test_source_action_state_count_and_finite_vectors_are_required(saved_inputs, change):
    field = deepcopy(saved_inputs[1])
    if change == "state":
        field["attachment_actions"][0]["state_id"] += "-changed"
    elif change == "count":
        field["flange_contact_actions"].pop()
    else:
        field["attachment_actions"][0]["force_on_receiver_xyz_n"][0] = float("nan")
    with pytest.raises(ValueError, match="mix states|complete72|finite3-vector|finite 3-vector"):
        writer.point_actions_from_field(field)


def test_unchanged_state_id_does_not_allow_changed_input_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(writer, "ROOT", tmp_path)
    source = tmp_path / "field.json"
    source.write_text(json.dumps({"state_id": "saved-state", "force_n": 1.}))
    pins = {"field.json": writer.steel.sha(source)}
    assert writer.verify_pins(pins) == pins
    source.write_text(json.dumps({"state_id": "saved-state", "force_n": 2.}))
    with pytest.raises(ValueError, match="frozen input changed"):
        writer.verify_pins(pins)


def test_contradictory_embedded_source_pins_are_rejected():
    value = {"source_sha256": {"source.py": "1" * 64},
             "nested": {"source_sha256": {"source.py": "2" * 64}}}
    with pytest.raises(ValueError, match="contradictory source pin"):
        writer.gather_pins(value, {}, [0])


@pytest.mark.parametrize("change", ["count", "index", "witness"])
def test_saved_nominal_replay_must_match_count_maximum_and_same_cut(saved_inputs, change):
    report, _, layout = deepcopy(saved_inputs)
    row = report["fresh_demand_comparison"]["flange_comparisons"][0]
    fitting = next(item for item in layout["raw_fittings"] if item["angle_id"] == row["angle_id"])
    if change == "count":
        row["section_count"] += 1
    elif change == "index":
        row["sampled_maximum_nominal_first_yield_index"] += 0.001
    else:
        row["sampled_stress_witness"]["force_local_n"][0] += 1.
    with pytest.raises(ValueError, match="saved nominal"):
        writer.replay_cuts(fitting, row)
