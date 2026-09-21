"""Authenticated one-case PB02 bolt-shaft and washer-demand regression."""

import json

import pytest

from scripts import simple_center_pb02_hardware_screen as screen


def test_current_case_hardware_screen_is_bound_and_conditional():
    result = screen.screen()
    rows = {row["name"]: row for row in result["bolts"]}

    assert result["authentication"] == {
        "candidate": "pb02-kerf-right-native-development-only",
        "case": "a12-forward",
        "report_sha256": screen.EXPECTED_REPORT_SHA256,
        "model_identity": screen.EXPECTED_MODEL_IDENTITY,
        "diagnostic_scope_fingerprint": screen.EXPECTED_SCOPE_FINGERPRINT,
        "active_geometry_fingerprint": screen.EXPECTED_GEOMETRY_FINGERPRINT,
        "numerically_accepted": True,
        "actual_joint_demands_qualified": False,
    }
    assert set(rows) == set(screen.BOLTS)
    assert len(rows) == 10

    positive = {
        name: row["demand"]["axial_tension_n"]
        for name, row in rows.items()
        if row["demand"]["axial_tension_n"] > 0
    }
    assert positive == pytest.approx(
        {
            "header_principal_block/bolt_1": 0.5501900000000007,
            "principal_block_principal/bolt_1": 9.8539,
            "principal_upright_block/bolt_1": 0.945499999999988,
            "rear_block_post/bolt_2": 17.659800000000004,
        }
    )
    assert rows["block_header/bolt_2"]["demand"]["transverse_shear_n"] == (
        pytest.approx(35.81052578517264)
    )

    governing = result["governing_direct_shaft_comparator"]
    assert governing["name"] == "block_header/bolt_2"
    assert governing["conservative_linear_interaction_ratio"] == pytest.approx(
        0.2269, abs=0.0001
    )
    assert rows["block_header/bolt_2"]["direct_shaft_comparator"][
        "long_grip_factor"
    ] == pytest.approx(0.0535433071)

    for row in rows.values():
        washer = row["washer_demand_each_end"]
        assert washer["head_n"] == pytest.approx(row["demand"]["axial_tension_n"])
        assert washer["nut_n"] == pytest.approx(row["demand"]["axial_tension_n"])
        assert washer["actual_washer_inputs"] == {
            "outside_diameter_mm": None,
            "inside_diameter_mm": None,
            "thickness_mm": None,
            "material": None,
        }
        assert washer["washer_qualified"] is False

    sensitivity = rows["rear_block_post/bolt_2"]["washer_demand_each_end"][
        "ideal_20mm_od_7p3mm_bore_sensitivity"
    ]
    assert sensitivity["wood_bearing_reference_n"] == pytest.approx(1173, abs=1)
    assert sensitivity["demand_ratio"] == pytest.approx(0.01505, abs=0.00001)
    assert result["qualified"] is False


def test_authentication_fails_closed_on_report_or_inventory_drift(
    tmp_path, monkeypatch
):
    original = json.loads(screen.REPORT_PATH.read_text())

    changed_demand = tmp_path / "changed-demand.json"
    original["physical_connection_forces"]["post_block/bolt_1"][
        "transverse_shear_n"
    ] += 1
    changed_demand.write_text(json.dumps(original))
    monkeypatch.setattr(screen, "REPORT_PATH", changed_demand)
    with pytest.raises(ValueError, match="authentication changed"):
        screen.screen()

    original = json.loads(screen.REPORT_PATH_ORIGINAL.read_text())
    original["physical_connection_forces"]["unexpected/bolt_1"] = original[
        "physical_connection_forces"
    ]["post_block/bolt_1"]
    changed_inventory = tmp_path / "changed-inventory.json"
    changed_inventory.write_text(json.dumps(original))
    monkeypatch.setattr(screen, "REPORT_PATH", changed_inventory)
    monkeypatch.setattr(
        screen,
        "EXPECTED_REPORT_SHA256",
        screen._sha256(changed_inventory),
    )
    with pytest.raises(ValueError, match="ten-bolt inventory changed"):
        screen.screen()
