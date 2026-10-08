"""Tiny census/source and retained-spatial-deficit curation fixtures only."""
import copy
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("eoere_compact_curation_test", Path(__file__).with_name("compact_assessment.py"))
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def test_complete_unique_source_ids_and_foreign_or_missing_rows():
    method.exact_ids([{"id": "a"}, {"id": "b"}], "id", {"a", "b"}, 2)
    for rows in ([{"id": "a"}], [{"id": "a"}, {"id": "a"}], [{"id": "a"}, {"id": "foreign"}]):
        with pytest.raises(ValueError):
            method.exact_ids(rows, "id", {"a", "b"}, 2)


def test_source_hash_conflict_cannot_relabel_provenance():
    pins = {"own": "exact"}
    method.join(pins, {"own": "exact", "new": "new-sha"})
    with pytest.raises(ValueError):
        method.join(pins, {"own": "foreign"})


def test_spatial_deficits_and_motion_limits_are_copied_without_mean_substitution():
    components = {name: {"sampled_ratio_CD1": value} for name, value in
                  (("bending_x", 4.59586861167), ("bending_y", 1.82704862326),
                   ("rolling_x", 2.43890165220), ("rolling_y", .89210723219))}
    rows = [{"panel": "synthetic-panel", "resolved_section_diagnostics": {"components": components,
             "limits": "third derivative jumps; no local acceptance"},
             "deformation_diagnostics": {"linear_plate_applicability_established": False}}]
    original = copy.deepcopy(rows)
    result = method.panels_record(rows)
    assert result == original and result is not rows
    assert result[0]["resolved_section_diagnostics"]["components"]["bending_x"]["sampled_ratio_CD1"] > 1.
    del rows[0]["resolved_section_diagnostics"]["components"]["rolling_x"]
    with pytest.raises(ValueError, match="mean-only"):
        method.panels_record(rows)


def test_plan_hash_mismatch_stops_before_gate_or_curation(monkeypatch):
    monkeypatch.setattr(method, "LOADED_SHA", "foreign")
    with pytest.raises(ValueError, match="curation source differs"):
        method.method_plan()
