from __future__ import annotations

import copy
import hashlib
import math

import cadquery as cq
import pytest

from scripts import wood_joint_wj04_mechanics_hardware as hardware


@pytest.fixture(scope="module")
def frozen_inputs():
    return hardware.load_frozen_inputs()


def _row_by_id(rows):
    return {row["physical_bolt_id"]: row for row in rows}


def test_frozen_inputs_bind_exactly_eight_six_inch_127_mm_stacks(frozen_inputs):
    assert len(frozen_inputs.patch_inventory["wood_bodies"]) == 5
    assert {row["part_id"] for row in frozen_inputs.patch_inventory["wood_bodies"]} == (
        hardware.EXPECTED_WOOD_IDS
    )
    assert len(frozen_inputs.patch_inventory["physical_bolts"]) == 8
    assert len(frozen_inputs.mechanics_manifest["physical_bolts"]) == 8
    assert len(frozen_inputs.thread_screen["physical_bolts"]) == 8
    assert all(
        row["provisional_hardware"]["bolt"]["sku"] == "25C600HCS5Z"
        and row["wood_grip_mm"] == 127.0
        for row in frozen_inputs.patch_inventory["physical_bolts"]
    )
    assert len(hardware.EXPECTED_BOLT_IDS) == 8
    assert not any("800" in bolt_id for bolt_id in hardware.EXPECTED_BOLT_IDS)
    assert len(hardware._legacy_collision_roles(frozen_inputs.patch_inventory)) == 40


def test_contract_rejects_changed_receiver_or_wrong_bolt_class(frozen_inputs):
    patch = copy.deepcopy(frozen_inputs.patch_inventory)
    patch["physical_bolts"][0]["receivers_head_to_nut"].reverse()
    with pytest.raises(ValueError, match="ordered receiver IDs/thicknesses disagree"):
        hardware._validate_source_contract(
            patch,
            frozen_inputs.mechanics_manifest,
            frozen_inputs.thread_screen,
            frozen_inputs.input_hashes,
        )

    patch = copy.deepcopy(frozen_inputs.patch_inventory)
    patch["physical_bolts"][0]["provisional_hardware"]["bolt"]["sku"] = "25C800HCS5Z"
    with pytest.raises(ValueError, match="candidate is not the pinned six-inch"):
        hardware._validate_source_contract(
            patch,
            frozen_inputs.mechanics_manifest,
            frozen_inputs.thread_screen,
            frozen_inputs.input_hashes,
        )


@pytest.mark.parametrize(
    ("scenario", "expected_transition"),
    [
        (hardware.SCENARIOS[0], 129.032),
        (hardware.SCENARIOS[1], 127.0),
    ],
)
def test_one_stack_is_four_independent_solids_with_source_anchored_faces(
    frozen_inputs, scenario, expected_transition
):
    bolt_id = hardware.EXPECTED_BOLT_IDS[0]
    patch_row = _row_by_id(frozen_inputs.patch_inventory["physical_bolts"])[bolt_id]
    mechanics_row = _row_by_id(frozen_inputs.mechanics_manifest["physical_bolts"])[
        bolt_id
    ]

    shapes, record = hardware._one_physical_stack(patch_row, mechanics_row, scenario)

    assert set(shapes) == {"bolt", "head_washer", "nut_washer", "nut"}
    assert all(
        shape.isValid() and len(shape.Solids()) == 1 for shape in shapes.values()
    )
    assert record["underhead_origin_basis"].startswith("pinned first wood-face")
    assert record["smooth_body_transition_station_from_underhead_mm"] == (
        expected_transition
    )
    assert record["new_minus_legacy_underhead_delta_axial_mm"] == pytest.approx(0.0)
    assert record["underhead_to_far_wood_face_mm"] == pytest.approx(129.032)
    assert record["wood_grip_mm"] == pytest.approx(127.0)

    engagement = record["root_to_nut_engagement"]
    assert engagement["tie_span_mm"] == pytest.approx(hardware.NUT_THICKNESS_MM)
    assert engagement["radial_projection_gap_mm"] == pytest.approx(0.09144)
    assert engagement["solver_adjust_or_gap_closure_mm"] == 0.0
    assert engagement["full_nut_thickness_engagement_assumed"]
    assert not engagement["physical_thread_profile_or_engagement_verified"]
    assert not record["wood_or_washer_tie_assigned"]

    # The split root is a smooth-cylinder scenario at Lb or the far wood face;
    # Lg remains only a gaging marker.
    assert record["Lb_marker_station_from_underhead_mm"] == 127.0
    assert record["Lg_marker_station_from_underhead_mm"] == 133.35
    assert record["component_role_count"] == 4


def test_underhead_is_derived_from_pinned_wood_face_not_legacy_collision_origin(
    frozen_inputs,
):
    bolt_id = hardware.EXPECTED_BOLT_IDS[0]
    patch_row = _row_by_id(frozen_inputs.patch_inventory["physical_bolts"])[bolt_id]
    mechanics_row = copy.deepcopy(
        _row_by_id(frozen_inputs.mechanics_manifest["physical_bolts"])[bolt_id]
    )
    direction = hardware._unit(
        mechanics_row["world_axis_direction_head_to_nut"], "test axis"
    )
    mechanics_row["modeled_bolt_under_head_origin_xyz_mm"] = list(
        hardware._add(
            tuple(mechanics_row["modeled_bolt_under_head_origin_xyz_mm"]),
            hardware._scale(direction, 0.25),
        )
    )

    _shapes, record = hardware._one_physical_stack(
        patch_row, mechanics_row, hardware.SCENARIOS[0]
    )

    expected = hardware._sub(
        tuple(mechanics_row["world_axis_origin_xyz_mm"]),
        hardware._scale(direction, hardware.WASHER_THICKNESS_MM),
    )
    assert record["underhead_origin_global_xyz_mm"] == pytest.approx(expected)
    assert record["new_minus_legacy_underhead_delta_axial_mm"] == pytest.approx(-0.25)
    assert record["new_minus_legacy_underhead_transverse_delta_mm"] == pytest.approx(
        0.0, abs=1e-9
    )


def test_hex_dimensions_are_consistent_and_inside_published_flat_bounds():
    head_af = hardware.HEAD_ACROSS_CORNERS_MM * math.sqrt(3) / 2
    nut_af = hardware.NUT_ACROSS_CORNERS_MM * math.sqrt(3) / 2
    assert (
        hardware.HEAD_ACROSS_FLATS_RANGE_MM[0]
        <= head_af
        <= (hardware.HEAD_ACROSS_FLATS_RANGE_MM[1])
    )
    assert (
        hardware.NUT_ACROSS_FLATS_RANGE_MM[0]
        <= nut_af
        <= (hardware.NUT_ACROSS_FLATS_RANGE_MM[1])
    )
    assert hardware.THREAD_ROOT_BASIC_MM == pytest.approx(4.79298)
    assert hardware.NUT_BORE_BASIC_MM == pytest.approx(4.97586)
    assert hardware.NBS_THREAD_REFERENCE["printed_page"] == 21
    assert hardware.NBS_THREAD_REFERENCE["pdf_page_index_zero_based"] == 30
    assert "0.1887 in" in hardware.NBS_THREAD_REFERENCE["cached_excerpt"]
    assert hardware.NBS_THREAD_REFERENCE["rendered_page_verification"][
        "status"
    ].startswith("parent independently confirmed")


def test_step_roundtrip_checks_single_solid_and_bidirectional_occupancy(tmp_path):
    outer = cq.Solid.makeBox(20.0, 14.0, 9.0)
    cut = cq.Solid.makeCylinder(2.0, 11.0, cq.Vector(10.0, 7.0, -1.0))
    source = outer.cut(cut).clean()
    path = tmp_path / "response-solid.step"

    record = hardware._write_step_solid(source, path, "synthetic response solid")

    assert path.is_file()
    assert record["identity_checks"]["solid_count"]
    assert record["identity_checks"]["symmetric_difference"]["passed"]
    assert (
        record["identity_checks"]["symmetric_difference"]["source_only_volume_mm3"]
        <= 1e-4
    )
    assert (
        record["identity_checks"]["symmetric_difference"]["step_only_volume_mm3"]
        <= 1e-4
    )
    assert not record["identity_checks"]["face_ordinal_used"]
    assert record["file_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
