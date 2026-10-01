"""Focused tests for signed seat ownership and conditional pressure routing."""

import pytest
import seats as seat_module
from seats import (
    axial_sign_and_pressure,
    bind_outer_seats,
    classify_support_helper_error,
    pressure_reference,
)


def synthetic_axis() -> dict:
    # The signed axis runs from the host's exterior face to the block's face.
    # Endpoint input order is reversed to ensure role ownership comes from the
    # signed coordinate and the member-face locations.
    return {
        "head_to_nut_axis_xyz": [1.0, 0.0, 0.0],
        "lateral_plane_xyz_mm": [5.0, 0.0, 0.0],
        "outer_seat_endpoints_xyz_mm": [[12.0, 0.0, 0.0], [-2.0, 0.0, 0.0]],
        "members": {
            "block": {
                "member": "block_member",
                "bolt_line_mid_bearing_xyz_mm": [10.0, 0.0, 0.0],
                "bearing_length_mm": 4.0,
                "conditional_grain_xyz": [0.0, 1.0, 0.0],
            },
            "host": {
                "member": "host_member",
                "bolt_line_mid_bearing_xyz_mm": [0.0, 0.0, 0.0],
                "bearing_length_mm": 4.0,
                "conditional_grain_xyz": [1.0, 0.0, 0.0],
            },
        },
    }


def test_outer_seat_owners_follow_signed_axis_and_face_coordinates() -> None:
    seats = bind_outer_seats(synthetic_axis())

    assert seats["head"]["owner_role"] == "host"
    assert seats["head"]["owner_member_id"] == "host_member"
    assert seats["nut"]["owner_role"] == "block"
    assert seats["nut"]["owner_member_id"] == "block_member"
    assert seats["head"]["grain_relation"] == "parallel_to_bolt_axis"
    assert seats["nut"]["grain_relation"] == "perpendicular_to_bolt_axis"


def test_tension_and_compression_have_the_same_physical_sign_at_both_seats() -> None:
    axis = (1.0, 0.0, 0.0)
    head = {"owner_role": "block", "seat_inward_normal_global_xyz": [1.0, 0.0, 0.0]}
    nut = {"owner_role": "host", "seat_inward_normal_global_xyz": [-1.0, 0.0, 0.0]}
    tension = {
        "axial_force_on_block_n": [10.0, 0.0, 0.0],
        "axial_force_rounding_radius_n": [0.0, 0.0, 0.0],
        "axial_tension_n": 10.0,
    }
    compression = {
        "axial_force_on_block_n": [-10.0, 0.0, 0.0],
        "axial_force_rounding_radius_n": [0.0, 0.0, 0.0],
        "axial_tension_n": 10.0,
    }

    tension_head = axial_sign_and_pressure(action=tension, seat=head, axis=axis)
    tension_nut = axial_sign_and_pressure(action=tension, seat=nut, axis=axis)
    compression_head = axial_sign_and_pressure(action=compression, seat=head, axis=axis)
    compression_nut = axial_sign_and_pressure(action=compression, seat=nut, axis=axis)

    assert (
        tension_head["physical_axial_state"]
        == tension_nut["physical_axial_state"]
        == "tension_into_wood_seat"
    )
    assert (
        tension_head["washer_pressure_demand_n"]
        == tension_nut["washer_pressure_demand_n"]
        == 10.0
    )
    assert (
        compression_head["physical_axial_state"]
        == compression_nut["physical_axial_state"]
        == "compression_unloading_wood_seat"
    )
    assert compression_head["signed_axial_load_into_receiver_member_n"] == -10.0
    assert compression_nut["signed_axial_load_into_receiver_member_n"] == -10.0
    assert (
        compression_head["washer_pressure_demand_n"]
        == compression_nut["washer_pressure_demand_n"]
        == 0.0
    )


def test_fc_perp_reference_requires_supported_perpendicular_grain_tension() -> None:
    scenario = {"scenario_id": "cad", "annulus_area_mm2": 100.0}
    supported = {"support_status": "full_modeled_support"}
    tension = {
        "physical_axial_state": "tension_into_wood_seat",
        "washer_pressure_demand_n": 10.0,
        "signed_axial_load_into_receiver_member_n": 10.0,
    }

    perpendicular = pressure_reference(
        signed=tension,
        seat={"grain_relation": "perpendicular_to_bolt_axis"},
        support=supported,
        scenario=scenario,
        fc_perp_psi=625.0,
    )
    parallel = pressure_reference(
        signed=tension,
        seat={"grain_relation": "parallel_to_bolt_axis"},
        support=supported,
        scenario=scenario,
        fc_perp_psi=625.0,
    )
    clipped = pressure_reference(
        signed=tension,
        seat={"grain_relation": "perpendicular_to_bolt_axis"},
        support={"support_status": "conditional_incompatibility"},
        scenario=scenario,
        fc_perp_psi=625.0,
    )

    assert (
        perpendicular["pressure_route_status"]
        == "conditional_fc_perp_ideal_annulus_reference_only"
    )
    assert perpendicular["fc_perp_reference_ratio"] == pytest.approx(
        10.0 / 100.0 / (625.0 * 0.006894757293168361)
    )
    assert (
        parallel["pressure_route_status"] == "unresolved_grain_parallel_pressure_route"
    )
    assert parallel["fc_perp_reference_ratio"] is None
    assert (
        clipped["pressure_route_status"]
        == "conditional_incompatibility_no_full_annulus_pressure_comparison"
    )
    assert clipped["fc_perp_reference_ratio"] is None


def test_modeled_support_errors_are_distinguished_from_unexpected_helper_errors() -> (
    None
):
    assert (
        classify_support_helper_error(
            "annulus is clipped by a bore or wood edge at block"
        )
        == "inward_annulus_clipped_by_modeled_wood_boundary"
    )
    assert (
        classify_support_helper_error(
            "washer datum has no matching planar wood boundary face"
        )
        == "no_matching_planar_datum_face"
    )
    assert classify_support_helper_error("unexpected STEP reader failure") is None


def test_verify_refuses_conflicting_duplicate_acceptance_flag(tmp_path, monkeypatch, capsys) -> None:
    report = {
        "joint_accepted": False,
        "geometry_seats": [],
        "seat_states": [],
        "modeled_geometry_status": "fixture_only",
    }
    output = tmp_path / "seats.json"
    monkeypatch.setattr(seat_module, "ROOT", tmp_path)
    monkeypatch.setattr(seat_module, "OUTPUT", output)
    monkeypatch.setattr(seat_module, "build_report", lambda: report)
    canonical = seat_module.canonical_json(report)
    output.write_text(canonical, encoding="utf-8")
    assert seat_module.main(["--verify"]) == 0
    output.write_text(canonical.replace("{", '{"joint_accepted": true,', 1), encoding="utf-8")
    assert seat_module.main(["--verify"]) == 2
    assert "differs from the current source-bound replay" in capsys.readouterr().err
