"""Actual frozen recovery export and source-bound adapter regression coupons."""

import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import thin_bolted_common_shaft as producer
from scripts import thin_bolted_common_shaft_export_audit as audit


@pytest.fixture(scope="module")
def actual_producer_export():
    """Run only frozen action serialization at zero forces, without assembly."""
    _, cache, unit, layout, _, _, _ = audit.frozen.read_sources()
    shafts = producer.shaft_inputs(layout, unit, cache)
    bodies = sorted({surface["host"] for shaft in shafts for surface in shaft["surfaces"]}
                    | {shaft["body"] for shaft in shafts})
    system = SimpleNamespace(
        assembly=SimpleNamespace(geo={"bodies": [{"id": name} for name in bodies]}),
        shafts={shaft["body"]: shaft for shaft in shafts}, recovery=lambda _: [],
        section_cut_actions=lambda *_: [])
    groups, contacts = [], []
    for shaft in shafts:
        point, axis = shaft["point"], shaft["basis"][0]
        for index, surface in enumerate(shaft["surfaces"]):
            low, high = surface["interval_mm"]
            for quad, abscissa in enumerate((-1 / np.sqrt(3.), 1 / np.sqrt(3.))):
                station = (low + high) / 2 + (high - low) / 2 * abscissa
                groups.append({"id": shaft["axis_id"] + f"/bearing-{index}-{quad}",
                    "axis_id": shaft["axis_id"], "kind": "common_shaft_bearing",
                    "first": shaft["body"], "second": surface["host"],
                    "point_xyz_mm": (point + axis * station).tolist(), "basis": shaft["basis"],
                    "surface": surface, "surface_index": index, "quad_index": quad,
                    "axis_station_mm": station, "weight_length_mm": (high - low) / 2,
                    "kl": 1., "clearance": 0.})
        for end in shaft["ends"]:
            contacts.append({"id": shaft["axis_id"] + "/" + end["end"] + "-capture",
                "axis_id": shaft["axis_id"], "kind": "shaft_end_capture",
                "first": shaft["body"], "second": end["host"],
                "point_xyz_mm": (point + axis * end["pressure_face_s_mm"]).tolist(),
                "host_support_point_xyz_mm": (point + axis * end["support_s_mm"]).tolist(),
                "direction_xyz": end["direction_on_shaft_xyz"], "end": copy.deepcopy(end)})
    blank = {"attachment_actions": [], "retained_bolt_actions": [], "panel_screw_actions": [],
             "contact_actions": [], "floor_actions": [],
             "global_equilibrium_residual_force_n": [0., 0., 0.],
             "global_equilibrium_residual_moment_nmm": [0., 0., 0.]}
    # Only the unrelated legacy recovery/stock-section diagnostic are mocked.
    # The new frozen compatible_actions export itself is called unchanged.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(producer, "LEGACY_ELASTIC_ACTIONS", lambda *_: copy.deepcopy(blank))
        patch.setattr(producer.frame, "member_sections", lambda *_: [])
        state = producer.CommonShaftSystem.compatible_actions(system, {"loads": []},
            {"q": np.zeros(0), "connector_local_force_n": [np.zeros(3) for _ in groups],
             "normal_contact_force_n": np.zeros(len(contacts))}, groups, contacts, [])
    identity = {"state_id": "serialization-coupon", "case_id": "a12-rear",
                "accessory_placement": "retained-original-top-hold"}
    state.update(identity)
    for name in ("common_shaft_bearing_actions", "shaft_end_capture_actions"):
        for row in state[name]:
            row.update(identity)
    # A JSON round trip matches the real file's list/dictionary values.
    return json.loads(json.dumps(state)), shafts, layout


def test_actual_frozen_recovery_dictionary_export_adapts_without_force_or_datum_changes(actual_producer_export):
    state, shafts, _ = actual_producer_export
    assert len(state["shaft_end_capture_actions"]) == 140
    assert isinstance(state["shaft_end_capture_actions"][0]["end"], dict)
    with pytest.raises(ValueError, match="capture end metadata"):
        audit.frozen.verify_common_actions(state, shafts)
    adapted = audit.normalized_capture_state(state, shafts)
    assert audit.frozen.verify_common_actions(adapted, shafts)["unilateral_end_capture_actions"] == 140
    for original, normalized in zip(state["shaft_end_capture_actions"], adapted["shaft_end_capture_actions"], strict=True):
        expected = copy.deepcopy(original)
        expected["end"] = expected["end"]["end"]
        assert normalized == expected
        assert isinstance(original["end"], dict)


@pytest.mark.parametrize("mutation", ["label-only", "host", "flange", "direction", "pressure", "washer", "duplicate", "missing"])
def test_wrong_or_incomplete_actual_end_geometry_is_rejected(actual_producer_export, mutation):
    original, shafts, _ = actual_producer_export
    state = copy.deepcopy(original)
    end = state["shaft_end_capture_actions"][0]["end"]
    if mutation == "label-only":
        state["shaft_end_capture_actions"][0]["end"] = end["end"]
    elif mutation == "host":
        end["host"] = "absent-host"
    elif mutation == "flange":
        end["flange"] = "absent-flange"
    elif mutation == "direction":
        end["direction_on_shaft_xyz"] = [0., 0., 0.]
    elif mutation == "pressure":
        end["pressure_face_s_mm"] += 1.
    elif mutation == "washer":
        end["washer_id"] = "opposite-washer"
    elif mutation == "duplicate":
        state["shaft_end_capture_actions"].append(copy.deepcopy(state["shaft_end_capture_actions"][0]))
    else:
        state["shaft_end_capture_actions"].pop()
    with pytest.raises((ValueError, TypeError)):
        audit.normalized_capture_state(state, shafts)


def test_retained_panel_midplane_datums_are_source_authenticated(actual_producer_export):
    _, _, layout = actual_producer_export
    state = json.loads((audit.frozen.PACKET / "compatible-frame-a12-rear-finished-floor-v4.json").read_text())
    audit.verify_panel_screw_datums(state, layout)
    state["panel_screw_actions"][0]["point_xyz_mm"][0] += 1.
    with pytest.raises(ValueError, match="midplane datum"):
        audit.verify_panel_screw_datums(state, layout)


def test_panel_point_law_does_not_gain_an_export_free_couple(actual_producer_export):
    _, _, layout = actual_producer_export
    state = json.loads((audit.frozen.PACKET / "compatible-frame-a12-rear-finished-floor-v4.json").read_text())
    state["panel_screw_actions"][0]["moment_at_point_model_xyz_nmm"] = [0., 0., 1.]
    with pytest.raises(ValueError, match="no free couple"):
        audit.verify_panel_screw_datums(state, layout)
