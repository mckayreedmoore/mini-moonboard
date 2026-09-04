import pytest

from mini_moonboard.site_inputs import total_kicker_height_mm, validate_site_inputs


def complete_inputs() -> dict[str, dict[str, float | str]]:
    return {
        "site": {
            "jurisdiction": "Example jurisdiction",
            "reviewer": "Example reviewer",
            "assembly": "fixed",
        },
        "room": {
            "clear_width_mm": 3500.0,
            "clear_depth_mm": 5000.0,
            "minimum_ceiling_height_mm": 2800.0,
        },
        "crash_pad": {
            "deployed_width_mm": 3000.0,
            "deployed_depth_mm": 2000.0,
            "highest_surface_mm": 250.0,
            "clear_face_below_active_zone_mm": 100.0,
        },
        "panels": {
            "sheet_length_mm": 2440.0,
            "sheet_width_mm": 1220.0,
            "measured_thickness_mm": 18.0,
            "frame_ply_thickness_mm": 18.0,
            "material": "birch plywood",
        },
        "hardware": {
            "tnut_bolt_system": "M10",
            "led_system_version": "V3",
            "tnut_hole_diameter_mm": 13.0,
            "tnut_barrel_length_mm": 10.0,
            "led_hole_diameter_mm": 13.0,
        },
    }


def test_complete_site_inputs_validate() -> None:
    assert validate_site_inputs(complete_inputs()) == []


def test_site_input_validation_reports_missing_and_non_positive_values() -> None:
    inputs = complete_inputs()
    inputs["room"]["clear_width_mm"] = 0.0
    del inputs["hardware"]["led_system_version"]

    assert validate_site_inputs(inputs) == [
        "hardware.led_system_version is required",
        "room.clear_width_mm must be a positive number",
    ]


def test_total_kicker_height_keeps_the_official_active_zone_above_the_pad() -> None:
    assert total_kicker_height_mm(complete_inputs()) == pytest.approx(500.0)
