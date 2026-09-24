"""Synthetic coverage for heading-consistent WJ-03 withdrawal summaries."""

import pytest

from scripts import summarize_wj03_head_withdrawal as summary


def _signed(value):
    return f"{value:+g}"


def _head_shapes(heading, stroke):
    base = f"heading_{_signed(heading)}deg"
    names = set()
    for stand_off in summary.EXPECTED_STANDOFFS_MM:
        pose = f"{base}/stand_off_{stand_off:g}mm"
        names.update({f"{pose}/ratchet_head", f"{pose}/ratchet_handle"})
        names.add(f"{pose}/stroke_endpoint_{_signed(stroke)}deg/handle")
        names.add(f"{pose}/stroke_sweep_{_signed(stroke)}deg")
    names.update(
        {
            f"{base}/continuous_stand_off/ratchet_head",
            f"{base}/continuous_stand_off/ratchet_handle",
            f"{base}/continuous_stand_off_and_stroke_{_signed(stroke)}deg",
        }
    )
    return names


def _all_head_shapes():
    return set().union(
        *(
            _head_shapes(heading, stroke)
            for heading in summary.EXPECTED_HEADINGS
            for stroke in summary.EXPECTED_STROKES
        )
    )


def _nut_shapes(heading):
    base = f"heading_{_signed(heading)}deg"
    names = {
        f"{base}/stand_off_{stand_off:g}mm/{part}"
        for stand_off in summary.EXPECTED_STANDOFFS_MM
        for part in ("ratchet_head", "ratchet_handle")
    }
    names.update(
        {
            f"{base}/continuous_stand_off/ratchet_head",
            f"{base}/continuous_stand_off/ratchet_handle",
        }
    )
    return names


def _screen(candidates, hits=None, below_floor=()):
    hits = hits or {}
    below_floor = set(below_floor)
    return {
        "external_envelope_hits_mm3": hits,
        "external_envelope_clear": not bool(hits),
        "floor_screen": {
            candidate: {
                "minimum_z_mm": -1.0 if candidate in below_floor else 1.0,
                "floor_z_mm": 0.0,
                "clearance_mm": -1.0 if candidate in below_floor else 1.0,
                "below_analytical_floor": candidate in below_floor,
                "penetration_depth_mm": 1.0 if candidate in below_floor else 0.0,
            }
            for candidate in candidates
        },
    }


def _stack_record(stack_id):
    head_shapes = _all_head_shapes()
    nut_shapes = set().union(*(_nut_shapes(h) for h in summary.EXPECTED_HEADINGS))
    head_pair_candidates = {"head_side_socket"} | {
        f"head_side_ratchet/{shape}" for shape in head_shapes
    }
    withdrawal_candidates = {"head_socket_axial_withdrawal"} | {
        f"{shape}/axial_withdrawal" for shape in head_shapes
    }
    nut_exit_candidates = {"nut_socket_and_loose_nut_short_axial_exit"} | {
        f"{shape}/short_axial_exit" for shape in nut_shapes
    }
    head_cases = {}
    for heading in summary.EXPECTED_HEADINGS:
        base = f"heading_{_signed(heading)}deg"
        head_cases[f"{_signed(heading)}deg"] = {
            "starting_heading_degrees_from_face_reference": heading,
            "stand_off_range_mm": list(summary.EXPECTED_STANDOFFS_MM),
            "head_stroke_degrees": list(summary.EXPECTED_STROKES),
            "continuous_stand_off_sweeps": [
                f"{base}/continuous_stand_off/ratchet_head",
                f"{base}/continuous_stand_off/ratchet_handle",
            ],
            "continuous_stand_off_and_stroke_sweeps": [
                f"{base}/continuous_stand_off_and_stroke_{_signed(stroke)}deg"
                for stroke in summary.EXPECTED_STROKES
            ]
            + [
                f"{base}/stand_off_{stand_off:g}mm/stroke_sweep_{_signed(stroke)}deg"
                for stand_off in summary.EXPECTED_STANDOFFS_MM
                for stroke in summary.EXPECTED_STROKES
            ],
        }

    return {
        "bolt_id": stack_id,
        "hardware": {"delivered_bolt_selected": False},
        "nut_counterhold_socket": {
            "outside_envelope": _screen({"stationary_nut_socket"}),
            "internal_profile_fit_and_hand_hold_verified": False,
        },
        "nut_counterhold_ratchet": {
            "outside_envelope": _screen(nut_shapes),
            "profile_cases": {
                "sampled_handle_heading_degrees_from_face_reference": list(
                    summary.EXPECTED_HEADINGS
                ),
                "stand_off_range_mm": list(summary.EXPECTED_STANDOFFS_MM),
            },
            "ratchet_vs_its_socket": _screen(nut_shapes),
            "torque_capacity_hand_hold_and_real_tool_fit_verified": False,
        },
        "head_socket_and_ratchet": {
            "head_socket_outside_envelope": _screen({"head_side_socket"}),
            "ratchet_profile_cases": head_cases,
            "ratchet_body_and_head_strokes": _screen(head_shapes),
            "ratchet_vs_mating_head_socket": _screen(head_shapes),
            "head_tools_vs_stationary_counterhold_tools": _screen(head_pair_candidates),
        },
        "bolt_withdrawal_after_unthreading": {
            "shaft_path": _screen({"shaft_axial_withdrawal"}),
            "head_path": _screen({"bolt_head_axial_withdrawal"}),
            "head_socket_and_ratchet_path": _screen(withdrawal_candidates),
            "head_tool_against_stationary_counterhold": _screen(withdrawal_candidates),
            "threading_kinematics_or_thread_fit_verified": False,
        },
        "post_withdrawal_loose_hardware": {
            "nut_counterhold_tool_and_nut_exit": _screen(nut_exit_candidates),
            "nut_washer_exit": _screen({"nut_washer_short_axial_exit"}),
            "head_washer_exit": _screen({"head_washer_short_axial_exit"}),
            "capture_and_retrieval_path_verified": False,
        },
    }


def _report():
    return {
        "schema": summary.SCHEMA,
        "trial_id": summary.TRIAL_ID,
        "candidate_stack_count": summary.EXPECTED_STACK_COUNT,
        "source_pins": {"coverage": "direct file pins only"},
        "tool_candidates": {
            "deep_socket": {
                "selected": False,
                "outer_proxy_internal_profile_or_fit_verified": False,
            },
            "head_ratchet": {
                "selected": False,
                "screened_head_strokes_degrees": list(summary.EXPECTED_STROKES),
                "handle_proxy_is_guaranteed_catalog_bound": False,
            },
            "counterhold_ratchet": {
                "selected": False,
                "stationary_handle_heading_samples_degrees": list(
                    summary.EXPECTED_HEADINGS
                ),
                "heading_samples_are_continuous_coverage": False,
            },
        },
        "ratchet_socket_mating": {
            "ratchet_head_standoff_range_mm": list(summary.EXPECTED_STANDOFFS_MM)
        },
        "release_claims": {
            "tool_selected": False,
            "physical_tool_access_established": False,
            "threading_and_bolt_withdrawal_procedure_accepted": False,
            "hardware_capture_path_verified": False,
            "fabrication_released": False,
            "structural_released": False,
        },
        "stacks": {
            f"stack_{index:02d}": _stack_record(f"stack_{index:02d}")
            for index in range(summary.EXPECTED_STACK_COUNT)
        },
    }


def test_matching_route_ignores_mutually_exclusive_heading_overlaps():
    report = _report()
    stack = report["stacks"]["stack_00"]
    head_map = stack["head_socket_and_ratchet"]["ratchet_body_and_head_strokes"]
    signed_bad_pose = "heading_+0deg/continuous_stand_off_and_stroke_-5deg"
    alternative_head_pose = "heading_+90deg/stand_off_0mm/ratchet_head"
    head_map["external_envelope_hits_mm3"] = {
        signed_bad_pose: {"finished_wood/signed_stroke_obstacle": 1.0},
        alternative_head_pose: {"finished_wood/alternative_heading_obstacle": 1.0},
    }
    head_map["external_envelope_clear"] = False

    nut_screen = stack["nut_counterhold_ratchet"]["outside_envelope"]
    alternative_nut_pose = "heading_+180deg/continuous_stand_off/ratchet_handle"
    nut_screen["external_envelope_hits_mm3"] = {
        alternative_nut_pose: {"finished_wood/alternative_nut_heading": 1.0}
    }
    nut_screen["external_envelope_clear"] = False

    pair_screen = stack["head_socket_and_ratchet"][
        "head_tools_vs_stationary_counterhold_tools"
    ]
    selected_head_pose = (
        "head_side_ratchet/heading_+0deg/continuous_stand_off/ratchet_handle"
    )
    alternate_nut_tool = (
        "tool_pair/stationary_nut_ratchet/"
        "heading_+90deg/continuous_stand_off/ratchet_head"
    )
    pair_screen["external_envelope_hits_mm3"] = {
        selected_head_pose: {alternate_nut_tool: 1.0}
    }
    pair_screen["external_envelope_clear"] = False

    withdrawal_pair = stack["bolt_withdrawal_after_unthreading"][
        "head_tool_against_stationary_counterhold"
    ]
    selected_withdrawal_pose = (
        "heading_+0deg/continuous_stand_off_and_stroke_+5deg/axial_withdrawal"
    )
    withdrawal_pair["external_envelope_hits_mm3"] = {
        selected_withdrawal_pose: {alternate_nut_tool: 1.0}
    }
    withdrawal_pair["external_envelope_clear"] = False

    result = summary.summarize_report(report)
    routes = result["stacks"][0]["proxy_clear_combinations"]
    assert {
        "head_heading_degrees": 0.0,
        "head_stroke_degrees": 5.0,
        "nut_counterhold_heading_degrees": 0.0,
    } in routes
    assert {
        "head_heading_degrees": 0.0,
        "head_stroke_degrees": -5.0,
        "nut_counterhold_heading_degrees": 0.0,
    } not in routes
    assert {
        "head_heading_degrees": 0.0,
        "head_stroke_degrees": 5.0,
        "nut_counterhold_heading_degrees": 90.0,
    } not in routes
    assert result["limitations"]["capture_and_retrieval_verified"] is False


def test_selected_pose_floor_penetration_marks_only_routes_using_that_heading():
    report = _report()
    screen = report["stacks"]["stack_00"]["head_socket_and_ratchet"][
        "ratchet_body_and_head_strokes"
    ]
    selected_pose = "heading_+0deg/continuous_stand_off_and_stroke_+5deg"
    screen["floor_screen"][selected_pose]["below_analytical_floor"] = True
    screen["floor_screen"][selected_pose]["minimum_z_mm"] = -0.1
    screen["floor_screen"][selected_pose]["clearance_mm"] = -0.1
    screen["floor_screen"][selected_pose]["penetration_depth_mm"] = 0.1

    result = summary.summarize_report(report)
    stack = result["stacks"][0]
    assert stack["proxy_clear_combination_count"] == 28
    assert not any(
        route["head_heading_degrees"] == 0.0 and route["head_stroke_degrees"] == 5.0
        for route in stack["proxy_clear_combinations"]
    )
    assert (
        stack["combinations_with_nonclear_proxy_by_check"][
            "head_ratchet_signed_stroke_environment"
        ]
        == 4
    )


def test_missing_required_pose_family_fails_closed():
    report = _report()
    screen = report["stacks"]["stack_00"]["head_socket_and_ratchet"][
        "ratchet_body_and_head_strokes"
    ]
    missing = "heading_+0deg/stand_off_0mm/ratchet_head"
    del screen["floor_screen"][missing]

    with pytest.raises(summary.ReportSchemaError, match="candidate family mismatch"):
        summary.summarize_report(report)


def test_alternate_floor_pose_does_not_block_selected_route():
    report = _report()
    screen = report["stacks"]["stack_00"]["head_socket_and_ratchet"][
        "ratchet_body_and_head_strokes"
    ]
    alternate = "heading_+90deg/continuous_stand_off/ratchet_handle"
    screen["floor_screen"][alternate]["below_analytical_floor"] = True
    screen["floor_screen"][alternate]["minimum_z_mm"] = -1.0
    screen["floor_screen"][alternate]["clearance_mm"] = -1.0
    screen["floor_screen"][alternate]["penetration_depth_mm"] = 1.0

    result = summary.summarize_report(report)
    assert {
        "head_heading_degrees": 0.0,
        "head_stroke_degrees": 5.0,
        "nut_counterhold_heading_degrees": 0.0,
    } in result["stacks"][0]["proxy_clear_combinations"]


def test_raw_shaft_aabb_overlaps_remain_pending_exact_cylinder_check():
    report = _report()
    shaft = report["stacks"]["stack_00"]["bolt_withdrawal_after_unthreading"][
        "shaft_path"
    ]
    shaft["external_envelope_hits_mm3"] = {
        "shaft_axial_withdrawal": {
            "finished_wood/intended_bore_aabb": 12.0,
            "installed_hardware/own_washer_aabb": 1.0,
        }
    }
    shaft["external_envelope_clear"] = False

    stack = summary.summarize_report(report)["stacks"][0]
    assert stack["proxy_clear_combination_count"] == 0
    assert stack["candidate_combinations_clear_except_shaft_check_count"] == 32
    assert stack["nonclear_combination_count"] == 0
    assert stack["raw_shaft_path_requires_exact_cylinder_supplement"] is True
    assert "raw_shaft_path_aabb_proxy_intersections" in stack


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("minimum_z_mm", float("nan"), "must be finite"),
        ("clearance_mm", 2.0, "disagrees with min_z-floor_z"),
        ("below_analytical_floor", True, "below-floor flag disagrees"),
    ],
)
def test_inconsistent_or_nonfinite_floor_rows_fail_closed(field, value, message):
    report = _report()
    screen = report["stacks"]["stack_00"]["head_socket_and_ratchet"][
        "ratchet_body_and_head_strokes"
    ]
    candidate = "heading_+0deg/continuous_stand_off_and_stroke_+5deg"
    screen["floor_screen"][candidate][field] = value

    with pytest.raises(summary.ReportSchemaError, match=message):
        summary.summarize_report(report)


def test_unexpected_candidate_family_fails_closed():
    report = _report()
    screen = report["stacks"]["stack_00"]["head_socket_and_ratchet"][
        "ratchet_body_and_head_strokes"
    ]
    screen["floor_screen"]["heading_+45deg/continuous_stand_off/ratchet_head"] = {
        "minimum_z_mm": 1.0,
        "floor_z_mm": 0.0,
        "clearance_mm": 1.0,
        "below_analytical_floor": False,
        "penetration_depth_mm": 0.0,
    }

    with pytest.raises(summary.ReportSchemaError, match="candidate family mismatch"):
        summary.summarize_report(report)


@pytest.mark.parametrize("reported_below", [False, True])
def test_rounded_floor_threshold_boundary_stays_ambiguous(reported_below):
    report = _report()
    screen = report["stacks"]["stack_00"]["head_socket_and_ratchet"][
        "ratchet_body_and_head_strokes"
    ]
    candidate = "heading_+0deg/continuous_stand_off_and_stroke_+5deg"
    screen["floor_screen"][candidate].update(
        {
            "minimum_z_mm": -0.000001,
            "floor_z_mm": 0.0,
            "clearance_mm": -0.000001,
            "below_analytical_floor": reported_below,
            "penetration_depth_mm": 0.000001,
        }
    )

    stack = summary.summarize_report(report)["stacks"][0]
    check_rows = stack["nonclear_proxy_examples_by_check"][
        "head_ratchet_signed_stroke_environment"
    ]
    assert check_rows
    details = check_rows[0]["details"]
    ambiguous = details.get("floor_threshold_rounding_ambiguous_proxy")
    assert ambiguous
    assert ambiguous[0]["reported_below_analytical_floor"] is reported_below
    if reported_below:
        assert (
            details["below_analytical_floor_proxy"][0]["below_analytical_floor"] is True
        )
    else:
        assert "below_analytical_floor_proxy" not in details


def test_floor_flag_inconsistent_outside_rounding_band_fails_closed():
    report = _report()
    screen = report["stacks"]["stack_00"]["head_socket_and_ratchet"][
        "ratchet_body_and_head_strokes"
    ]
    candidate = "heading_+0deg/continuous_stand_off_and_stroke_+5deg"
    screen["floor_screen"][candidate].update(
        {
            "minimum_z_mm": 0.01,
            "floor_z_mm": 0.0,
            "clearance_mm": 0.01,
            "below_analytical_floor": True,
            "penetration_depth_mm": 0.0,
        }
    )

    with pytest.raises(summary.ReportSchemaError, match="below-floor flag disagrees"):
        summary.summarize_report(report)
