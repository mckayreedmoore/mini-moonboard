"""Tests for signed per-member fastener-load boundary geometry."""

import math

import pytest

from mini_moonboard.wood_joint_directional_geometry import classify_member_fastener_load
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL


def _identity_case(**overrides):
    values = {
        "force_on_member_global_n": (6.0, -8.0, 5.0),
        "grain_axis_global_unit": (1.0, 0.0, 0.0),
        "bolt_axis_global_unit": (0.0, 0.0, 1.0),
        "bolt_center_global_mm": (20.0, 10.0, 20.0),
        "member_frame_origin_global_mm": (0.0, 0.0, 0.0),
        "member_axes_global_unit": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        "member_bounds_local_mm": ((0.0, 100.0), (0.0, 20.0), (0.0, 50.0)),
    }
    values.update(overrides)
    return classify_member_fastener_load(**values)


def test_oblique_signed_load_classifies_end_and_edge_separately():
    result = _identity_case()

    assert result["load_convention"] == "force_on_member"
    assert result["force_along_bolt_axis_signed_n"] == pytest.approx(5.0)
    assert result["bolt_lateral_force_global_xyz_n"] == pytest.approx((6.0, -8.0, 0.0))
    assert result["force_parallel_to_grain_signed_n"] == pytest.approx(6.0)
    assert result["force_cross_grain_global_xyz_n"] == pytest.approx((0.0, -8.0, 0.0))

    end = result["grain_end_direction"]
    assert end["loaded_component_direction"] == "positive_axis"
    assert end["loaded_boundary_direction_global_xyz"] == pytest.approx((1.0, 0.0, 0.0))
    assert end["local_boundary_side"] == "upper_coordinate_boundary"
    assert end["distance_to_loaded_outer_boundary_mm"] == pytest.approx(80.0)

    edge = result["cross_grain_edge_direction"]
    assert edge["loaded_component_direction"] == "negative_axis"
    assert edge["loaded_boundary_direction_global_xyz"] == pytest.approx(
        (0.0, -1.0, 0.0)
    )
    assert edge["local_boundary_side"] == "lower_coordinate_boundary"
    assert edge["distance_to_loaded_outer_boundary_mm"] == pytest.approx(10.0)
    assert result["outer_box_only"] is True
    assert (
        "wood or bolt resistance, utilization, or pass/fail" in result["not_evaluated"]
    )


def test_reversing_member_force_reverses_selected_boundaries():
    result = _identity_case(force_on_member_global_n=(-6.0, 8.0, -5.0))

    assert (
        result["grain_end_direction"]["loaded_component_direction"] == "negative_axis"
    )
    assert (
        result["grain_end_direction"]["local_boundary_side"]
        == "lower_coordinate_boundary"
    )
    assert result["grain_end_direction"][
        "distance_to_loaded_outer_boundary_mm"
    ] == pytest.approx(20.0)
    assert (
        result["cross_grain_edge_direction"]["loaded_component_direction"]
        == "positive_axis"
    )
    assert (
        result["cross_grain_edge_direction"]["local_boundary_side"]
        == "upper_coordinate_boundary"
    )
    assert result["cross_grain_edge_direction"][
        "distance_to_loaded_outer_boundary_mm"
    ] == pytest.approx(10.0)


def test_zero_direction_component_does_not_select_an_arbitrary_boundary():
    result = _identity_case(force_on_member_global_n=(0.0, -8.0, 5.0))

    end = result["grain_end_direction"]
    assert end["status"] == "zero_component_no_loaded_boundary"
    assert end["loaded_component_direction"] is None
    assert end["local_boundary_side"] is None
    assert end["distance_to_loaded_outer_boundary_mm"] is None
    assert end["distance_to_both_outer_boundaries_mm"] == {
        "lower_coordinate_boundary_mm": pytest.approx(20.0),
        "upper_coordinate_boundary_mm": pytest.approx(80.0),
    }

    axial_only = _identity_case(force_on_member_global_n=(0.0, 0.0, 5.0))
    assert (
        axial_only["grain_end_direction"]["status"]
        == "zero_component_no_loaded_boundary"
    )
    assert (
        axial_only["cross_grain_edge_direction"]["status"]
        == "zero_component_no_loaded_boundary"
    )

    grain_only = _identity_case(force_on_member_global_n=(6.0, 0.0, 5.0))
    assert (
        grain_only["grain_end_direction"]["local_boundary_side"]
        == "upper_coordinate_boundary"
    )
    assert (
        grain_only["cross_grain_edge_direction"]["status"]
        == "zero_component_no_loaded_boundary"
    )


def test_rotated_right_handed_frame_preserves_signed_component_directions():
    axes = ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    result = classify_member_fastener_load(
        force_on_member_global_n=(3.0, 7.0, 4.0),  # 7*b0 - 3*b1 + 4*b2
        grain_axis_global_unit=axes[0],
        bolt_axis_global_unit=axes[2],
        bolt_center_global_mm=(97.0, 204.0, 310.0),
        member_frame_origin_global_mm=(100.0, 200.0, 300.0),
        member_axes_global_unit=axes,
        member_bounds_local_mm=((-5.0, 15.0), (0.0, 8.0), (0.0, 20.0)),
    )

    assert result["bolt_center_local_coordinates_mm"] == pytest.approx((4.0, 3.0, 10.0))
    assert result["force_parallel_to_grain_signed_n"] == pytest.approx(7.0)
    assert result["force_cross_grain_signed_on_frame_axis_n"] == pytest.approx(-3.0)
    assert result["grain_end_direction"][
        "distance_to_loaded_outer_boundary_mm"
    ] == pytest.approx(11.0)
    assert result["cross_grain_edge_direction"][
        "distance_to_loaded_outer_boundary_mm"
    ] == pytest.approx(3.0)


def test_canonical_wj04_cleat_adapter_is_cad_free_and_uses_synthetic_force_only():
    config = WJ04_TRIAL
    cleat = config.cleat
    frame = config.frame
    axes = (frame.x_global, frame.t_global, frame.n_global)
    result = classify_member_fastener_load(
        # Deliberately synthetic direction fixture, not a WJ04 demand.
        force_on_member_global_n=frame.vector_to_global((0.0, 20.0, 30.0)),
        grain_axis_global_unit=frame.vector_to_global((0.0, 0.0, 1.0)),
        bolt_axis_global_unit=config.axis_direction_global("upright_2"),
        bolt_center_global_mm=config.axis_point_global("upright_2"),
        member_frame_origin_global_mm=frame.to_global(cleat.origin_x_t_n_mm),
        member_axes_global_unit=axes,
        member_bounds_local_mm=(
            (0.0, cleat.size_x_t_n_mm[0]),
            (0.0, cleat.size_x_t_n_mm[1]),
            (0.0, cleat.size_x_t_n_mm[2]),
        ),
    )

    assert result["force_parallel_to_grain_signed_n"] == pytest.approx(30.0)
    assert result["force_cross_grain_signed_on_frame_axis_n"] == pytest.approx(20.0)
    assert result["grain_end_direction"][
        "distance_to_loaded_outer_boundary_mm"
    ] == pytest.approx(349.540968 - 320.0)
    assert result["cross_grain_edge_direction"][
        "distance_to_loaded_outer_boundary_mm"
    ] == pytest.approx(19.05)
    assert result["outer_box_only"] is True
    assert "fresh demand provenance" in result["not_evaluated"][-1]


@pytest.mark.parametrize(
    "axes",
    [
        ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),  # left-handed
        ((1.0, 0.0, 0.0), (0.0, 0.8, 0.6), (0.0, 0.0, 1.0)),  # nonorthogonal
    ],
)
def test_non_right_handed_or_nonorthogonal_frame_is_rejected(axes):
    with pytest.raises(ValueError, match="member frame"):
        _identity_case(member_axes_global_unit=axes)


def test_nonfinite_inputs_and_hole_center_outside_box_are_rejected():
    with pytest.raises(ValueError, match="finite"):
        _identity_case(force_on_member_global_n=(math.inf, 0.0, 0.0))
    with pytest.raises(ValueError, match="outside member bounds"):
        _identity_case(bolt_center_global_mm=(101.0, 10.0, 20.0))


def test_grain_and_bolt_axes_must_be_distinct_and_orthogonal():
    with pytest.raises(ValueError, match="different member-frame axes"):
        _identity_case(bolt_axis_global_unit=(1.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="perpendicular"):
        _identity_case(bolt_axis_global_unit=(1e-5, 0.0, math.sqrt(1.0 - 1e-10)))
