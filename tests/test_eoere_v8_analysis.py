"""Reject loss of a reviewed inward orientation before response preparation."""

import copy

import pytest

from scripts.eoere_v8_analysis import context, verify_inward_axis


def axis():
    return {
        "id": "known-inward",
        "point_xyz_mm": [100.0, 20.0, 30.0],
        "direction_xyz": [-1.0, 0.0, 0.0],
        "before_plate_mm": 0.0,
        "after_plate_mm": 6.35,
        "diameter_mm": 9.525,
        "bore_diameter_mm": 10.31875,
        "grip_mm": 100.0,
        "nominal_under_head_length_mm": 152.4,
        "nut_side_spacer_mm": 38.1,
        "hardware_scenario": {"washer_thickness_mm": 2.6416},
        "head_faces": "exterior",
        "nut_faces": "interior",
        "installation_orientation_revision": "eoere-inward-exterior-bolts-v7",
    }


def test_recorded_translation_preserves_asymmetric_inward_stack():
    prior = axis()
    moved = copy.deepcopy(prior)
    moved["point_xyz_mm"][1] += 6.0
    verify_inward_axis(moved, prior, [0.0, 6.0, 0.0])
    verify_inward_axis(prior, prior, [0.0, 0.0, 0.0])


@pytest.mark.parametrize(
    "key,value",
    [
        ("direction_xyz", [1.0, 0.0, 0.0]),
        ("point_xyz_mm", [100.0, 20.0, 30.0]),
        ("before_plate_mm", 6.35),
        ("nominal_under_head_length_mm", 165.1),
        ("nut_side_spacer_mm", 0.0),
        ("head_faces", "interior"),
    ],
)
def test_translation_cannot_revert_or_resize_inward_hardware(key, value):
    prior = axis()
    moved = copy.deepcopy(prior)
    moved["point_xyz_mm"][1] += 6.0
    moved[key] = value
    with pytest.raises(ValueError):
        verify_inward_axis(moved, prior, [0.0, 6.0, 0.0])


def test_missing_parent_hashes_cannot_select_default_current_geometry():
    with pytest.raises(ValueError, match="explicit SHA-256"):
        context(None, None)
