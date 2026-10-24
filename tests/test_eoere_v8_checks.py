"""Installation-coordinate controls for current conditional shank checks."""

import copy

import pytest

from scripts import eoere_v8_checks as checks


@pytest.fixture
def inward_shaft_bank(monkeypatch):
    axes, shafts, selections = [], [], []
    for i in range(96):
        identity = f"bolt_{i}"
        reversed_stack = i < 40
        sign = 1 if reversed_stack else -1
        direction = [sign, 0, 0]
        axes.append({"id": identity, "direction_xyz": direction, "point_xyz_mm": [0, 0, 0],
                     "head_faces": "exterior" if reversed_stack else "retained"})
        shafts.append({"axis_id": identity, "basis": [direction], "point": [0, 0, 0],
                       "shaft_interval_mm": [-2.6416, 120.],
                       "ends": [{"end": "head", "pressure_face_s_mm": -2.6416,
                                 "direction_on_shaft_xyz": [-sign, 0, 0]},
                                {"end": "nut", "pressure_face_s_mm": 97.8916,
                                 "direction_on_shaft_xyz": direction}],
                       "surfaces": [{"host": "side", "kind": "wood", "interval_mm": [0, 88.9]},
                                    {"host": "angle", "kind": "steel", "interval_mm": [88.9, 95.25]}]})
        selections.append({"axis_id": identity, "minimum_body_mm": 87.376})
    monkeypatch.setattr(checks.issued, "selections", lambda geometry: selections)
    return {"axes": axes}, {"source_inputs": {"shafts": shafts}}


def test_reversed_and_retained_stacks_use_installation_not_world_coordinates(inward_shaft_bank):
    geometry, field = inward_shaft_bank
    result = checks.head_to_nut_coordinates(geometry, field)
    assert sum(row["reversed_exterior_stack"] for row in result) == 40
    for row in (result[0], result[-1]):
        assert row["body_to_thread_transition_s_mm"] == pytest.approx(84.7344)
        assert row["surfaces"][0]["length_beyond_minimum_body_mm"] == pytest.approx(4.1656)
        assert row["surfaces"][1]["length_beyond_minimum_body_mm"] == pytest.approx(6.35)


@pytest.mark.parametrize("change", [
    lambda shaft: shaft.update(basis=[[-1, 0, 0]]),
    lambda shaft: shaft["ends"][0].update(pressure_face_s_mm=100.),
    lambda shaft: shaft["ends"][0].update(direction_on_shaft_xyz=[1, 0, 0]),
    lambda shaft: shaft["surfaces"][0].update(interval_mm=[88.9, 0.]),
])
def test_old_orientation_or_reversed_intervals_cannot_qualify_shank(inward_shaft_bank, change):
    geometry, field = copy.deepcopy(inward_shaft_bank)
    change(field["source_inputs"]["shafts"][0])
    with pytest.raises(ValueError):
        checks.head_to_nut_coordinates(geometry, field)
