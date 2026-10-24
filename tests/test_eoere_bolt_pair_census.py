"""Tests for the independent same-host bolt-pair census."""

from copy import deepcopy

import pytest

from scripts.eoere_bolt_pair_census import pair_census


def _shaft(axis_id, point, *, direction=(1.0, 0.0, 0.0), receiver="plate"):
    return {
        "axis_id": axis_id,
        "point": list(point),
        "basis": [list(direction), [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
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
    }


def _original_pair(first, second, status="pass"):
    return {
        "host": "member",
        "axes": [first, second],
        "rule": {"status": status, "required_mm": 28.575},
    }


def _census(shafts, occurrences=None, pairs=None):
    if occurrences is None:
        occurrences = [_occurrence(axis_id) for axis_id in shafts]
    return pair_census(shafts, occurrences, [] if pairs is None else pairs)


def test_enumerates_all_same_host_pairs_without_a_distance_cutoff():
    shafts = {
        "a": _shaft("a", (0.0, 0.0, 0.0)),
        "b": _shaft("b", (100.0, 3.0, 4.0)),
        "c": _shaft("c", (0.0, 0.0, 10000.0)),
    }

    result = _census(shafts)

    assert [row["axes"] for row in result] == [["a", "b"], ["a", "c"], ["b", "c"]]
    assert [row["actual_spacing_mm"] for row in result] == pytest.approx(
        [5.0, 10000.0, (3.0**2 + 9996.0**2) ** 0.5]
    )
    assert all(row["parallel_bore_axes"] for row in result)
    assert all(row["status"] == "UNRESOLVED" for row in result)
    assert all(row["rule_status"] == "unresolved" for row in result)
    assert all(row["complete_Cdelta"] is None for row in result)
    assert all(row["complete_joint_qualified"] is False for row in result)


def test_cross_receiver_pair_is_listed_as_unresolved_with_both_intervals():
    shafts = {
        "a": _shaft("a", (0.0, 0.0, 0.0), receiver="left_plate"),
        "b": _shaft("b", (0.0, 12.0, 0.0), receiver="right_plate"),
    }

    [row] = _census(shafts)

    assert row["existing_connection_group_pair"] is False
    assert row["parallel_bore_axes"] is True
    assert row["actual_spacing_mm"] == pytest.approx(12.0)
    assert row["status"] == row["component_status"] == "UNRESOLVED"
    assert row["rule_status"] == "unresolved"
    assert "applicability is unverified" in row["reasons"][0]
    assert row["complete_Cdelta"] is None
    assert row["complete_joint_qualified"] is False
    assert row["wood_bearing_intervals_mm"] == [
        {
            "axis_id": "a",
            "shaft_surface_interval_mm": [0.0, 38.1],
            "placement_bearing_interval_mm": [0.0, 38.1],
        },
        {
            "axis_id": "b",
            "shaft_surface_interval_mm": [0.0, 38.1],
            "placement_bearing_interval_mm": [0.0, 38.1],
        },
    ]


def test_original_rule_is_kept_as_component_only_never_a_joint_pass():
    shafts = {"a": _shaft("a", (0.0, 0.0, 0.0)), "b": _shaft("b", (0.0, 0.0, 12.0))}

    [row] = _census(shafts, pairs=[_original_pair("b", "a")])

    assert row["existing_connection_group_pair"] is True
    assert row["axes"] == ["a", "b"]
    assert row["status"] == row["component_status"] == "PASS_COMPONENTS_ONLY"
    assert row["rule_status"] == row["original_rule_status"] == "pass"
    assert row["rule_scope"] == "component_only"
    assert row["original_rule"] == {"status": "pass", "required_mm": 28.575}
    assert row["complete_Cdelta"] is None
    assert row["complete_joint_qualified"] is False


def test_census_identity_ignores_order_axis_reversal_and_along_axis_point_shift():
    shafts = {
        "a": _shaft("a", (2.0, 0.0, 0.0)),
        "b": _shaft("b", (50.0, 3.0, 4.0)),
    }
    occurrences = [_occurrence("a"), _occurrence("b")]
    pairs = [_original_pair("a", "b")]
    baseline = pair_census(shafts, occurrences, pairs)

    transformed = deepcopy(shafts)
    transformed["a"]["basis"][0] = [-1.0, 0.0, 0.0]
    transformed["a"]["point"][0] += 70.0
    transformed["b"]["point"][0] -= 250.0
    for shaft in transformed.values():
        shaft["surfaces"].reverse()
    equivalent = pair_census(
        dict(reversed(list(transformed.items()))),
        list(reversed(occurrences)),
        [_original_pair("b", "a")],
    )

    assert equivalent == baseline
    assert equivalent[0]["axes"] == ["a", "b"]
    assert equivalent[0]["actual_spacing_mm"] == pytest.approx(5.0)


def test_nonparallel_bores_have_no_single_reported_spacing_or_formal_rule():
    shafts = {
        "a": _shaft("a", (0.0, 0.0, 0.0)),
        "b": _shaft("b", (0.0, 10.0, 0.0), direction=(0.0, 1.0, 0.0)),
    }

    [row] = _census(shafts)

    assert row["parallel_bore_axes"] is False
    assert row["actual_spacing_mm"] is None
    assert row["status"] == row["component_status"] == "UNRESOLVED"
    assert row["rule_status"] == "unresolved"
    assert "nonparallel bore axes" in row["reasons"][0]


@pytest.mark.parametrize(
    ("mutate", "occurrences", "pairs", "error"),
    [
        (None, [_occurrence("a"), _occurrence("a")], [], "duplicate wood occurrence"),
        (None, [_occurrence("a"), _occurrence("missing")], [], "missing shaft"),
        (None, [_occurrence("a")], [], "census differs"),
        (
            lambda shafts: shafts["a"]["basis"].__setitem__(0, [2.0, 0.0, 0.0]),
            None,
            [],
            "unit length",
        ),
        (
            lambda shafts: shafts["a"]["point"].__setitem__(1, float("nan")),
            None,
            [],
            "finite number",
        ),
        (
            lambda shafts: shafts["a"]["surfaces"].append(
                {"kind": "wood", "host": "member", "interval_mm": [0.0, 12.0]}
            ),
            None,
            [],
            "multiple wood surfaces",
        ),
        (
            None,
            None,
            [_original_pair("a", "missing")],
            "lacks a same-host occurrence",
        ),
        (
            None,
            None,
            [_original_pair("a", "b"), _original_pair("b", "a")],
            "duplicate original pair",
        ),
    ],
)
def test_rejects_duplicate_missing_or_malformed_source_records(
    mutate, occurrences, pairs, error
):
    shafts = {"a": _shaft("a", (0.0, 0.0, 0.0)), "b": _shaft("b", (0.0, 0.0, 10.0))}
    if mutate is not None:
        mutate(shafts)

    with pytest.raises((TypeError, ValueError), match=error):
        pair_census(
            shafts,
            [_occurrence("a"), _occurrence("b")] if occurrences is None else occurrences,
            [] if pairs is None else pairs,
        )
