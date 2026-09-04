import argparse
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .model import OFFICIAL_KICKER_HEIGHT_MM

_REQUIRED_TEXT = (
    ("site", "jurisdiction"),
    ("site", "reviewer"),
    ("site", "assembly"),
    ("panels", "material"),
    ("hardware", "tnut_bolt_system"),
    ("hardware", "led_system_version"),
)
_REQUIRED_POSITIVE = (
    ("room", "clear_width_mm"),
    ("room", "clear_depth_mm"),
    ("room", "minimum_ceiling_height_mm"),
    ("crash_pad", "deployed_width_mm"),
    ("crash_pad", "deployed_depth_mm"),
    ("crash_pad", "highest_surface_mm"),
    ("crash_pad", "clear_face_below_active_zone_mm"),
    ("panels", "sheet_length_mm"),
    ("panels", "sheet_width_mm"),
    ("panels", "measured_thickness_mm"),
    ("panels", "frame_ply_thickness_mm"),
)


def _section(inputs: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = inputs.get(name, {})
    return value if isinstance(value, Mapping) else {}


def validate_site_inputs(inputs: Mapping[str, Any]) -> list[str]:
    """Return missing or invalid fields required before frame design begins."""
    errors: list[str] = []
    for section_name, field_name in _REQUIRED_TEXT:
        value = _section(inputs, section_name).get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{section_name}.{field_name} is required")
    for section_name, field_name in _REQUIRED_POSITIVE:
        value = _section(inputs, section_name).get(field_name)
        if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
            errors.append(f"{section_name}.{field_name} must be a positive number")
    return errors


def total_kicker_height_mm(inputs: Mapping[str, Any]) -> float:
    """Return pad top + chosen clearance + the official active 150 mm kicker."""
    errors = validate_site_inputs(inputs)
    if errors:
        raise ValueError("invalid site inputs: " + "; ".join(errors))
    crash_pad = _section(inputs, "crash_pad")
    return float(crash_pad["highest_surface_mm"]) + float(
        crash_pad["clear_face_below_active_zone_mm"]
    ) + OFFICIAL_KICKER_HEIGHT_MM


def load_site_inputs(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Mini MoonBoard site inputs")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    inputs = load_site_inputs(args.path)
    errors = validate_site_inputs(inputs)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print(f"site inputs valid; derived total kicker height: {total_kicker_height_mm(inputs):g} mm")


if __name__ == "__main__":
    main()
