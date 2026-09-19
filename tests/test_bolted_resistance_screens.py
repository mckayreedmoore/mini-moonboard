"""LB-11A/B geometric screens stay distinct from capacity."""

import pytest

from mini_moonboard.bolted_steel_checks import screen_ab90
from mini_moonboard.bolted_timber_checks import screen_geometry


def test_timber_screen_reports_geometry_and_unresolved_capacity_separately() -> None:
    result = screen_geometry(139.7, 38.1, 10.0, 50.0, 80.0)
    assert result.geometry_status == "nominal_pass"
    assert result.edge_4d_reserve_mm == pytest.approx(10.0)
    assert result.capacity_status.startswith("unresolved")


def test_timber_screen_exposes_a_narrow_face_failure() -> None:
    assert screen_geometry(38.1, 38.1, 10.0, 19.05, 80.0).geometry_status == "nominal_fail"


def test_ab90_screen_uses_factory_hole_and_does_not_claim_capacity() -> None:
    result = screen_ab90()
    assert result.diametric_clearance_mm == 1.0
    assert result.hole_status == "nominal_fit"
    assert result.resistance_status.startswith("unresolved")
