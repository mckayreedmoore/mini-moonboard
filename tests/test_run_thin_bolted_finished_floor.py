"""Protect finished support interpretation and compatible state provenance."""

import copy

import pytest

from scripts.run_thin_bolted_finished_floor import (
    CONTACT_SHA,
    FLOOR_BASIS,
    bind_finished_state,
    ordered_rectangle,
)


def test_horizontal_face_is_ordered_with_positive_area():
    polygon = ordered_rectangle([[2., 3., 0.], [0., 0., 0.], [2., 0., 0.], [0., 3., 0.]])
    twice_area = sum(polygon[i][0] * polygon[(i + 1) % 4][1]
                     - polygon[(i + 1) % 4][0] * polygon[i][1] for i in range(4))
    assert twice_area == 12.


@pytest.mark.parametrize("points", [
    [[0., 0., 0.], [2., 0., 0.], [0., 3., 0.], [1., 3., 0.]],
    [[0., 0., 0.], [2., 0., 0.], [0., 3., 1.], [2., 3., 0.]],
    [[0., 0., 0.], [2., 0., 0.], [0., 3., 0.], [0., 3., 0.]],
])
def test_incompatible_support_geometry_is_rejected(points):
    with pytest.raises(ValueError):
        ordered_rectangle(points)


def test_support_method_changes_every_action_identity_without_changing_forces():
    report = {"state_id": "raw", "case_id": "a12-rear", "accessory_placement": "retained-original-top-hold",
              "parameters": {"beam_size_mm": 150.}, "geometry_cache_sha256": "geometry",
              "source_sha256": {}, "limits": [],
              "contact_actions": [{"state_id": "raw", "force_on_first_xyz_n": [0., 0., 12.]}]}
    # The producer's flange table contains the same row objects as contacts.
    report["flange_contact_actions"] = report["contact_actions"][:]
    original = copy.deepcopy(report)
    bound = bind_finished_state(report, [], {}, "driver")
    assert bound["state_id"] != original["state_id"]
    for table in ("contact_actions", "flange_contact_actions"):
        assert bound[table][0]["state_id"] == bound["state_id"]
        assert bound[table][0]["force_on_first_xyz_n"] == original[table][0]["force_on_first_xyz_n"]
    assert bound["parameters"]["floor_support_basis"] == FLOOR_BASIS
    assert bound["parameters"]["floor_contact_geometry_sha256"] == CONTACT_SHA
    assert bound["geometry_cache_sha256"] == original["geometry_cache_sha256"]


def test_mixed_action_state_is_rejected():
    report = {"state_id": "raw", "case_id": "a12-rear", "accessory_placement": "original",
              "parameters": {}, "geometry_cache_sha256": "geometry", "source_sha256": {}, "limits": [],
              "floor_actions": [{"state_id": "foreign"}]}
    with pytest.raises(ValueError, match="mixed action"):
        bind_finished_state(report, [], {}, "driver")
