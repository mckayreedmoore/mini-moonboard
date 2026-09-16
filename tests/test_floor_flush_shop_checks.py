"""Keep the selected FR-3 CAD and fixture screen executable."""
import pytest

from scripts.floor_flush_shop_checks import build, front_fixture_budget


def test_front_finished_pitch_and_registration_preserve_existing_budget():
    fixture = front_fixture_budget()
    assert fixture['minimum_4D_margin_mm'] == pytest.approx(.9)
    assert fixture['maximum_axis_error_mm'] == pytest.approx((.75**2+.5**2)**.5)
    assert fixture['within_recorded_1mm_position_allowance'] is True


def test_max_washers_hillman_axes_and_contact_pairs_fit_selected_cad():
    result = build()
    assert result['bolt_count'] == 12
    assert result['receiver_seat_count'] == 24
    assert result['maximum_catalog_washer_unsupported_mm3'] < .01
    assert result['panel_screw_count'] == 66
    assert result['minimum_hillman_tip_reserve_mm'] == pytest.approx(94.45625)
    assert result['contact_interface_count'] == 6
    assert result['qualified_for_design'] is False
