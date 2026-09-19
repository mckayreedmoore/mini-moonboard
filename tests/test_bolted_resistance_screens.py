"""LB-11A/B geometric screens stay distinct from capacity."""

import math
from decimal import Decimal

import pytest

from mini_moonboard.a66_geometry_screen import screen_a66_geometry
from mini_moonboard.bolted_steel_checks import screen_a66, screen_ab90
from mini_moonboard.bolted_timber_checks import screen_geometry


def test_timber_screen_reports_geometry_and_unresolved_capacity_separately() -> None:
    result = screen_geometry(139.7, 38.1, 10.0, 50.0, 80.0)
    assert result.geometry_status == "nominal_pass"
    assert result.edge_4d_reserve_mm == pytest.approx(10.0)
    assert result.capacity_status.startswith("unresolved")


def test_timber_screen_exposes_a_narrow_face_failure() -> None:
    assert screen_geometry(38.1, 38.1, 10.0, 19.05, 80.0).geometry_status == "nominal_fail"


@pytest.mark.parametrize("argument_index", range(5))
@pytest.mark.parametrize(
    "invalid_value",
    [math.nan, math.inf, -math.inf, True, False, 0, -1, 1 + 2j, Decimal(1), "10", None],
)
def test_timber_screen_rejects_invalid_input_for_every_argument(argument_index, invalid_value) -> None:
    arguments = [139.7, 38.1, 10.0, 50.0, 80.0]
    arguments[argument_index] = invalid_value

    with pytest.raises(ValueError):
        screen_geometry(*arguments)


def test_ab90_screen_uses_factory_hole_and_does_not_claim_capacity() -> None:
    result = screen_ab90()
    assert result.diametric_clearance_mm == 1.0
    assert result.hole_status == "nominal_fit"
    assert result.resistance_status.startswith("unresolved")


def test_a66_screen_keeps_common_retail_bolt_capacity_unresolved() -> None:
    result = screen_a66()
    assert result.product == "Simpson Strong-Tie A66"
    assert result.hole_status == "unresolved_factory_hole"
    assert result.factory_hole_mm is None
    assert result.diametric_clearance_mm is None
    assert result.resistance_status.startswith("unresolved")


def test_a66_explicit_hole_dimension_is_required_for_a_fit_screen() -> None:
    assert screen_a66(factory_hole_mm=10.0).hole_status == "nominal_fit"
    assert screen_a66(factory_hole_mm=9.0).hole_status == "nominal_fail"


def test_a66_narrow_2x6_face_fails_nominal_edge_screen() -> None:
    result = screen_a66_geometry()
    assert result.wide_face_status == "best_case_screen_pass"
    assert result.narrow_face_status == "best_case_screen_fail"
    assert result.wide_face_edge_distance_mm == pytest.approx(69.85)
    assert result.narrow_face_edge_distance_mm == pytest.approx(19.05)
    assert result.wide_face_edge_reserve_mm == pytest.approx(31.75)
    assert result.narrow_face_edge_reserve_mm == pytest.approx(-19.05)
    assert result.capacity_status.startswith("unresolved")
