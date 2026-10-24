"""Tests for conservative principal-axis geometry rule classification."""

import math

import pytest

from scripts import eoere_bolt_geometry_rules as rules


def test_affine_load_stays_parallel_when_cross_component_is_below_resolution():
    result = rules.classify_affine_load((10.0, 1e-9), (20.0, -1e-9))

    assert result["direction"] == "parallel"
    assert result["reversal"] is False
    assert result["grain_sign"] == 1
    assert result["crossgrain_sign"] is None


def test_affine_load_classifies_a_signed_perpendicular_path():
    result = rules.classify_affine_load((0.0, -2.0), (0.0, -3.0))

    assert result["direction"] == "perpendicular"
    assert result["reversal"] is False
    assert result["crossgrain_sign"] == -1


def test_affine_load_detects_oblique_interior_between_principal_endpoints():
    result = rules.classify_affine_load((1.0, 0.0), (0.0, 1.0))

    assert result["direction"] == "oblique"
    assert result["reversal"] is False


def test_affine_load_detects_narrow_resolved_oblique_interior():
    result = rules.classify_affine_load((2.0, 0.0), (0.0, 2.01), force_gate=1.0)

    assert result["direction"] == "oblique"


def test_affine_load_retains_signed_reversal_on_a_principal_axis():
    result = rules.classify_affine_load((-2.0, 0.0), (3.0, 0.0))

    assert result["direction"] == "parallel"
    assert result["reversal"] is True
    assert result["grain_sign"] is None


def test_affine_load_is_unresolved_when_both_components_stay_below_gate():
    result = rules.classify_affine_load((0.0, 0.0), (1e-10, -1e-10))

    assert result["direction"] == "unresolved"
    assert result["reversal"] is False


@pytest.mark.parametrize(
    ("first", "last", "gate"),
    [
        ((1.0,), (1.0, 0.0), 1e-8),
        ((1.0, 0.0, 0.0), (1.0, 0.0, 0.0), 1e-8),
        ((math.nan, 0.0), (1.0, 0.0), 1e-8),
        ((1.0, 0.0), (1.0, 0.0), 0.0),
        ((1.0, 0.0), (1.0, 0.0), -1.0),
    ],
)
def test_affine_load_rejects_malformed_or_invalid_inputs(first, last, gate):
    with pytest.raises(ValueError):
        rules.classify_affine_load(first, last, force_gate=gate)


def test_perpendicular_edge_rule_applies_four_d_loaded_edge_by_force_sign():
    positive = rules.edge_rule(
        (20.0, 38.1), 9.525, 38.1, rules.classify_affine_load((0, 2), (0, 3))
    )
    negative = rules.edge_rule(
        (38.1, 20.0), 9.525, 38.1, rules.classify_affine_load((0, -2), (0, -3))
    )

    assert positive["status"] == negative["status"] == "pass"
    assert positive["required_mm"] == pytest.approx([14.2875, 38.1])
    assert negative["required_mm"] == pytest.approx([38.1, 14.2875])


def test_perpendicular_edge_rule_fails_a_short_signed_loaded_edge():
    result = rules.edge_rule(
        (100.0, 33.2), 9.525, 38.1, rules.classify_affine_load((0, 1), (0, 2))
    )

    assert result["status"] == "fail"
    assert result["required_mm"] == pytest.approx([14.2875, 38.1])


def test_parallel_edge_rule_uses_half_row_spacing_only_above_six_diameters():
    short = rules.edge_rule(
        (14.3, 14.3), 9.525, 38.1, rules.classify_affine_load((2, 0), (3, 0))
    )
    long = rules.edge_rule(
        (49.0, 60.0),
        9.525,
        60.0,
        rules.classify_affine_load((2, 0), (3, 0)),
        maximum_row_spacing=100.0,
    )

    assert short["status"] == "pass"
    assert short["required_mm"] == pytest.approx([14.2875, 14.2875])
    assert long["status"] == "fail"
    assert long["required_mm"] == pytest.approx([50.0, 50.0])


def test_parallel_edge_rule_is_unresolved_when_long_row_spacing_is_unknown():
    result = rules.edge_rule(
        (100.0, 100.0), 9.525, 60.0, rules.classify_affine_load((2, 0), (3, 0))
    )

    assert result["status"] == "unresolved"
    assert result["required_mm"] is None


def test_parallel_edge_rule_treats_zero_row_spacing_as_missing_evidence():
    short = rules.edge_rule(
        (20.0, 20.0),
        9.525,
        38.1,
        rules.classify_affine_load((2, 0), (3, 0)),
        maximum_row_spacing=0.0,
    )
    long = rules.edge_rule(
        (100.0, 100.0),
        9.525,
        60.0,
        rules.classify_affine_load((2, 0), (3, 0)),
        maximum_row_spacing=0.0,
    )

    assert short["status"] == "pass"
    assert long["status"] == "unresolved"


@pytest.mark.parametrize(
    "load_info",
    [
        rules.classify_affine_load((1, 0), (0, 1)),
        rules.classify_affine_load((-1, 0), (1, 0)),
    ],
)
def test_edge_rule_does_not_formally_classify_oblique_or_reversing_loads(load_info):
    result = rules.edge_rule((100.0, 100.0), 9.525, 38.1, load_info)

    assert result["status"] == "unresolved"
    assert result["required_mm"] is None


@pytest.mark.parametrize(
    ("distances", "diameter", "length", "row_spacing"),
    [
        ((1.0,), 9.525, 38.1, None),
        ((1.0, math.nan), 9.525, 38.1, None),
        ((1.0, 2.0), 0.0, 38.1, None),
        ((1.0, 2.0), 9.525, -1.0, None),
        ((1.0, 2.0), 9.525, 60.0, -1.0),
    ],
)
def test_edge_rule_rejects_invalid_dimensions(distances, diameter, length, row_spacing):
    with pytest.raises(ValueError):
        rules.edge_rule(
            distances,
            diameter,
            length,
            rules.classify_affine_load((0, 1), (0, 1)),
            maximum_row_spacing=row_spacing,
        )


def test_square_tension_end_uses_the_existing_classified_end_factor():
    result = rules.end_rule(40.0, 9.525, "softwood_parallel_tension", square_end=True)

    assert result["status"] == "pass"
    assert result["minimum_mm"] == pytest.approx(3.5 * 9.525)
    assert result["full_value_mm"] == pytest.approx(7 * 9.525)
    assert result["factor"] == pytest.approx(40.0 / (7 * 9.525))


def test_square_end_below_the_minimum_fails_the_end_component():
    result = rules.end_rule(30.0, 9.525, "softwood_parallel_tension", square_end=True)

    assert result["status"] == "fail"
    assert result["factor"] is None


@pytest.mark.parametrize("square_end", [False, None])
def test_sloped_or_unclassified_end_is_diagnostic_only(square_end):
    result = rules.end_rule(
        40.0, 9.525, "softwood_parallel_tension", square_end=square_end
    )

    assert result["status"] == "unresolved"
    assert result["factor"] is None
    assert result["diagnostic_trial_only"]["end_factor_only"] == pytest.approx(
        40.0 / (7 * 9.525)
    )


def test_unclassified_end_category_cannot_be_promoted_to_a_formal_result():
    result = rules.end_rule(40.0, 9.525, "oblique_to_grain", square_end=True)

    assert result["status"] == "unresolved"
    assert result["factor"] is None
    assert result["diagnostic_trial_only"] is None


def test_missing_end_category_from_oblique_load_is_unresolved():
    result = rules.end_rule(40.0, 9.525, None, square_end=True)

    assert result["status"] == "unresolved"
    assert result["factor"] is None
    assert result["diagnostic_trial_only"] is None


@pytest.mark.parametrize(
    ("distance", "diameter", "category", "square_end"),
    [
        (-1.0, 9.525, "perpendicular", True),
        (10.0, 0.0, "perpendicular", True),
        (math.inf, 9.525, "perpendicular", True),
        (10.0, 9.525, "perpendicular", "yes"),
    ],
)
def test_end_rule_rejects_invalid_inputs(distance, diameter, category, square_end):
    with pytest.raises(ValueError):
        rules.end_rule(distance, diameter, category, square_end=square_end)


def test_v6_oblique_diagonal_pair_retains_markers_without_a_formal_spacing_verdict():
    result = rules.pair_rule(
        (32.6536, 38.9151),
        9.525,
        38.1,
        rules.classify_affine_load((1.0, -0.2), (2.0, -0.3)),
    )

    assert result["status"] == "unresolved"
    assert result["actual_spacing_mm"] == pytest.approx(50.8, abs=1e-3)
    assert result["grain_projection_mm"] == pytest.approx(32.6536)
    assert result["crossgrain_projection_mm"] == pytest.approx(38.9151)
    assert result["principal_markers_mm"][
        "perpendicular_between_rows_min_mm"
    ] == pytest.approx(35.71875)
    assert result["required_mm"] is None


def test_diagonal_pair_stays_unresolved_without_explicit_row_classification():
    result = rules.pair_rule(
        (32.6536, 38.9151),
        9.525,
        38.1,
        rules.classify_affine_load((2.0, 0.0), (3.0, 0.0)),
    )

    assert result["status"] == "unresolved"
    assert "row classification" in result["reasons"][0]


def test_explicit_perpendicular_between_row_minimum_can_fail():
    result = rules.pair_rule(
        (32.6536, 0.0),
        9.525,
        38.1,
        rules.classify_affine_load((0.0, 2.0), (0.0, 3.0)),
        row_classification="between_rows",
    )

    assert result["status"] == "fail"
    assert result["required_mm"] == pytest.approx(35.71875)


def test_parallel_same_row_minimum_still_fails_when_explicitly_classified():
    result = rules.pair_rule(
        (27.0, 0.0),
        9.525,
        38.1,
        rules.classify_affine_load((2.0, 0.0), (3.0, 0.0)),
        row_classification="same_row",
    )

    assert result["status"] == "fail"
    assert result["required_mm"] == pytest.approx(3 * 9.525)


def test_perpendicular_between_rows_passes_at_the_table_minimum():
    result = rules.pair_rule(
        (35.71875, 0.0),
        9.525,
        38.1,
        rules.classify_affine_load((0.0, -2.0), (0.0, -3.0)),
        row_classification="between_rows",
    )

    assert result["status"] == "pass"
    assert result["required_mm"] == pytest.approx(35.71875)


def test_pair_rule_is_invariant_to_coordinate_sign_reflection():
    load = rules.classify_affine_load((0.0, 2.0), (0.0, 3.0))
    direct = rules.pair_rule(
        (0.0, 16.0), 9.525, 38.1, load, row_classification="between_rows"
    )
    reflected = rules.pair_rule(
        (0.0, -16.0), 9.525, 38.1, load, row_classification="between_rows"
    )

    assert reflected["status"] == direct["status"]
    assert reflected["actual_spacing_mm"] == direct["actual_spacing_mm"]
    assert reflected["required_mm"] == direct["required_mm"]


@pytest.mark.parametrize(
    ("delta", "diameter", "length", "row_classification"),
    [
        ((1.0,), 9.525, 38.1, "same_row"),
        ((1.0, math.nan), 9.525, 38.1, "same_row"),
        ((1.0, 0.0), 0.0, 38.1, "same_row"),
        ((1.0, 0.0), 9.525, -1.0, "same_row"),
        ((1.0, 0.0), 9.525, 38.1, "diagonal"),
    ],
)
def test_pair_rule_rejects_invalid_inputs(delta, diameter, length, row_classification):
    with pytest.raises(ValueError):
        rules.pair_rule(
            delta,
            diameter,
            length,
            rules.classify_affine_load((2.0, 0.0), (3.0, 0.0)),
            row_classification=row_classification,
        )


def test_rule_rollup_fails_closed_to_component_statuses_only():
    result = rules.rollup_status(["pass", "unresolved"])
    failed = rules.rollup_status(["unresolved", "fail"])
    passed = rules.rollup_status(["pass", "pass"])

    assert result == "UNRESOLVED"
    assert failed == "FAIL"
    assert passed == "PASS_COMPONENTS_ONLY"


def test_rule_rollup_accepts_rule_results_and_rejects_unknown_statuses():
    edge = rules.edge_rule(
        (20.0, 38.1), 9.525, 38.1, rules.classify_affine_load((0.0, 2.0), (0.0, 3.0))
    )

    assert rules.rollup_status([edge]) == "PASS_COMPONENTS_ONLY"
    assert rules.rollup_status("pass") == "PASS_COMPONENTS_ONLY"
    with pytest.raises(ValueError):
        rules.rollup_status(["probably okay"])
