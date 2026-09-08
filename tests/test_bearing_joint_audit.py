"""Numeric dimensional audit checks; these deliberately build no CAD."""
from types import SimpleNamespace

import pytest

from fea import bearing_joint_audit as audit


def test_selected_leg_bolt_stack_and_reference_thread_bearing():
    result = audit.bolt_stack(139.7, 114.3)
    assert result["projection_at_nominal_length_max_hardware_mm"] == pytest.approx(12.7762)
    assert result["projection_with_assumed_underlength_mm"] == pytest.approx(10.2362)
    assert result["two_pitch_target_mm"] == pytest.approx(3.175)
    assert result["remaining_grip_growth_allowance_mm"] == pytest.approx(7.0612)
    assert result["reference_threaded_wood_bearing_length_mm"] == pytest.approx(2.032)
    assert result["dimensional_projection_screen_pass"] is True
    assert result["thread_configuration_qualified"] is False
    assert result["connection_strength_qualified"] is False


def test_insufficient_projection_fails_without_becoming_a_strength_result():
    result = audit.bolt_stack(139.7, 122.)
    assert result["projection_with_assumed_underlength_mm"] == pytest.approx(2.5362)
    assert result["dimensional_projection_screen_pass"] is False
    assert result["remaining_grip_growth_allowance_mm"] < 0
    assert result["connection_strength_qualified"] is False
    assert audit.bolt_stack(139.7, 114.3, 0.)["projection_with_assumed_underlength_mm"] == pytest.approx(12.7762)


@pytest.mark.parametrize("length,grip,tolerance", [
    (0., 114.3, 2.54), (139.7, 0., 2.54), (139.7, 114.3, -1.),
    (float("nan"), 114.3, 2.54), (139.7, float("inf"), 2.54),
    (139.7, 114.3, float("inf")),
])
def test_invalid_dimensions_rejected(length, grip, tolerance):
    with pytest.raises(ValueError, match="positive finite"):
        audit.bolt_stack(length, grip, tolerance)


def fake_inventory():
    common = {"members": ("a", "b"), "length": 63.5, "diameter": 4.826,
              "kind": "screw", "product_status": "PROVISIONAL product; no strength"}
    result = [SimpleNamespace(**{**common, "name": f"analysis_leg_wall_bolt_{i}",
                "kind": "bolt", "diameter": 9.525}) for i in range(8)]
    result += [SimpleNamespace(**common, name=f"wood_kicker_block_{i}") for i in range(8)]
    result += [SimpleNamespace(**common, name=f"easy_lower_corner_{i}") for i in range(4)]
    return result


def test_inventory_retains_each_unselected_product_instead_of_assigning_capacity():
    leg, unresolved = audit.inventory(fake_inventory())
    assert len(leg) == 8 and len(unresolved) == 12
    assert len({row["connection"] for row in unresolved}) == 12
    assert all(row["diameter_mm"] == 4.826 for row in unresolved)
    assert all("PROVISIONAL" in row["product_status"] for row in unresolved)
    with pytest.raises(ValueError, match="Expected eight"):
        audit.inventory(fake_inventory()[:-1])
    changed = fake_inventory()
    changed[0].diameter = 6.35
    with pytest.raises(ValueError, match="family changed"):
        audit.inventory(changed)
    changed = fake_inventory()
    changed[-1].product_status = "SELECTED actual product"
    with pytest.raises(ValueError, match="disposition changed"):
        audit.inventory(changed)


def test_refuses_to_overwrite_evidence_before_loading_cad(tmp_path, monkeypatch):
    path = tmp_path/"report.json"
    path.touch()
    monkeypatch.setattr(audit, "OUTPUT", path)
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        audit.main()


def test_actual_receiver_grip_rejects_gaps_overlaps_and_wrong_washer_datum():
    intervals = {"edge": [(2.032, 40.132)], "rim": [(40.132, 78.232)],
                 "inner": [(78.232, 97.282)], "outer": [(97.282, 116.332)]}
    assert audit.validate_receiver_grip(intervals, 114.3, 2.032) == pytest.approx(114.3)
    for delta in (-1., 1.):
        broken = {**intervals, "outer": [(97.282+delta, 116.332+delta)]}
        with pytest.raises(ValueError, match="contiguous"):
            audit.validate_receiver_grip(broken, 114.3, 2.032)
    with pytest.raises(ValueError, match="contiguous"):
        audit.validate_receiver_grip(intervals, 114.3, 1.6)
    with pytest.raises(ValueError, match="topology"):
        audit.validate_receiver_grip({**intervals, "outer": []}, 114.3, 2.032)
    with pytest.raises(ValueError, match="Invalid receiver"):
        audit.validate_receiver_grip({**intervals, "outer": [(97.282, float("inf"))]}, 114.3, 2.032)
