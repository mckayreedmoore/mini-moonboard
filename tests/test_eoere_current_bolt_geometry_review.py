"""Pure current-review wrapper tests; no analysis bank or solver is read."""

from scripts.eoere_current_bolt_geometry_review import upgrade_case


def _shaft(axis_id, y, receiver):
    return {
        "axis_id": axis_id,
        "point": [0.0, y, 0.0],
        "basis": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "surfaces": [
            {"kind": "wood", "host": "member", "interval_mm": [0.0, 38.1]},
            {"kind": "steel", "host": receiver},
        ],
    }


def _occurrence(axis_id):
    return {
        "axis_id": axis_id,
        "host": "member",
        "placement": {"bearing_interval_mm": [0.0, 38.1]},
        "raw_affine_endpoint_pressures_on_host_N_per_mm": [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
    }


def test_current_wrapper_keeps_original_component_and_new_pairs_unresolved():
    shafts = {
        "a": _shaft("a", 0.0, "shared_plate"),
        "b": _shaft("b", 50.8, "shared_plate"),
        "c": _shaft("c", 101.6, "other_plate"),
    }
    case = {
        "case_id": "synthetic-case",
        "wood_occurrences": [_occurrence(axis_id) for axis_id in shafts],
        "receiver_pairs": [
            {
                "host": "member",
                "axes": ["a", "b"],
                "rule": {"status": "pass", "required_mm": 28.575},
                "complete_Cdelta": None,
            }
        ],
        "axes": [
            {"axis_id": axis_id, "component_status": "PASS_COMPONENTS_ONLY", "complete_Cdelta": None,
             "complete_joint_qualified": False}
            for axis_id in shafts
        ],
    }

    result = upgrade_case(case, shafts)

    assert len(result["same_host_pairs"]) == 3
    by_axes = {tuple(row["axes"]): row for row in result["same_host_pairs"]}
    assert by_axes[("a", "b")]["status"] == "PASS_COMPONENTS_ONLY"
    assert by_axes[("a", "b")]["rule_scope"] == "component_only"
    for axes in (("a", "c"), ("b", "c")):
        row = by_axes[axes]
        assert row["existing_connection_group_pair"] is False
        assert row["status"] == row["component_status"] == "UNRESOLVED"
        assert row["complete_Cdelta"] is None
        assert row["complete_joint_qualified"] is False
    assert all(row["component_status"] == "UNRESOLVED" for row in result["axes"])
    assert all(row["complete_joint_qualified"] is False for row in result["axes"])
    assert all("reconstructed_affine_endpoint_pressures_on_host_N_per_mm" in row
               for row in result["wood_occurrences"])
    assert all("raw_affine_endpoint_pressures_on_host_N_per_mm" not in row
               for row in result["wood_occurrences"])
    assert all(row["case_id"] == "synthetic-case" for row in result["receiver_pairs"])
