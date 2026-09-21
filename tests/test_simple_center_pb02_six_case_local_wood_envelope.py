"""PB02 local wood envelope remains source-bound and mechanism-limited."""

import copy

import pytest

from scripts import simple_center_pb02_six_case_local_wood_envelope as envelope


def test_all_six_cases_and_four_crossed_bore_incidences_are_checked():
    result = envelope.screen()

    assert result["status"] == "authenticated_six_case_local_wood_envelope"
    assert result["authentication"]["accepted_case_count"] == 6
    assert result["case_order"] == list(envelope.six_case_evidence.EXPECTED_CASES)
    assert set(result["incidences"]) == set(envelope.INCIDENCES)
    assert result["record_count"] == 24
    for incidence in result["incidences"].values():
        assert incidence["neighboring_orthogonal_bore"]["force_included"] is False
        assert incidence["neighboring_orthogonal_bore"]["diameter_mm"] == pytest.approx(
            7.3
        )
        assert list(incidence["cases"]) == result["case_order"]
        for case in incidence["cases"].values():
            assert case["one_fastener_connection"] is True
            assert case["force_count"] == 1
            assert case["additional_opening_count"] == 1
            assert case["neighbor_force_cancellation_credited"] is False
            assert case["signed_member_local_force_n"]
            assert case["nds_appendix_e"]["governing_ratio"] >= 0
            assert case["supplemental_ec5_splitting"]["governing_ratio"] >= 0


def test_local_axes_and_stock_references_are_explicit_and_conservative():
    result = envelope.screen()

    expected = {
        "shifted_right_post/post_cleat_2": (88.9, 88.9, "section_u", "section_v"),
        "shifted_right_post/post_high": (88.9, 88.9, "section_v", "section_u"),
        "upright_side_cleat/upright": (88.9, 61.6, "section_u", "section_v"),
        "upright_side_cleat/cleat_link": (61.6, 88.9, "section_v", "section_u"),
    }
    for name, (width, depth, through, transverse) in expected.items():
        incidence = result["incidences"][name]
        frame = incidence["member_local_frame"]
        assert frame["through_bolt_width_mm"] == pytest.approx(width)
        assert frame["transverse_depth_mm"] == pytest.approx(depth)
        assert frame["through_axis_source"] == through
        assert frame["transverse_axis_source"] == transverse
        assert incidence["material"]["basis"] == (
            "conservative_conditional_2024_NDS_Table_4D_DF-L_No.2_"
            "Posts_and_Timbers_base_CD_1"
        )
        assert incidence["material"]["duration_factor_CD"] == 1.0
        assert incidence["material"]["size_factor_benefit_used"] is False
        assert (
            incidence["material"]["finished_stock_classification_qualified"] is False
        )


def test_nds_and_supplemental_ec5_results_remain_distinct():
    result = envelope.screen()

    assert result["governing"]["nds_appendix_e"]["ratio"] >= 0
    assert result["governing"]["supplemental_ec5_splitting"]["ratio"] >= 0
    assert result["governing"]["combined_capacity_claim"] is False
    assert result["disposition"]["decision"] in {"ADVANCE", "REVISE"}
    assert result["disposition"]["scope"] == "local_wood_mechanism_only"
    assert (
        result["boundaries"]["orthogonal_hole_stress_concentration_qualified"] is False
    )
    assert result["boundaries"]["complete_joint_verdict"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def test_signed_force_mapping_preserves_action_and_magnitude():
    result = envelope.screen()

    for incidence in result["incidences"].values():
        for case in incidence["cases"].values():
            global_force = case["signed_force_on_member_xyz_n"]
            local_force = case["signed_member_local_force_n"]
            assert sum(value * value for value in global_force) == pytest.approx(
                sum(value * value for value in local_force)
            )
            assert case["action_reaction_verified"] is True


def test_per_incidence_rotation_is_invariant_and_preserves_loaded_edge_sign():
    member = {
        "axis": [0.0, 0.0, 1.0],
        "section_u": [1.0, 0.0, 0.0],
        "section_v": [0.0, 1.0, 0.0],
        "width_mm": 88.9,
        "depth_mm": 61.6,
        "start": [10.0, -4.0, 2.0],
    }
    installation = [1.0, 0.0, 0.0]
    point = [13.0, 3.0, 22.0]
    force = [11.0, -17.0, 23.0]
    frame = envelope._build_frame(member, installation, "section_u")
    local_point = envelope._point_to_local(point, member, frame)
    local_force = envelope._to_local(force, frame)

    # Proper cyclic rigid rotation: global (X,Y,Z) -> (Z,X,Y).  The grain is
    # no longer global +Z, which catches accidental direct use of helper axes.
    rotate = lambda vector: [vector[2], vector[0], vector[1]]
    rotated_member = {
        **member,
        "axis": rotate(member["axis"]),
        "section_u": rotate(member["section_u"]),
        "section_v": rotate(member["section_v"]),
        "start": rotate(member["start"]),
    }
    rotated_frame = envelope._build_frame(
        rotated_member, rotate(installation), "section_u"
    )
    assert envelope._point_to_local(
        rotate(point), rotated_member, rotated_frame
    ) == pytest.approx(local_point)
    assert envelope._to_local(rotate(force), rotated_frame) == pytest.approx(
        local_force
    )
    assert local_force[1] < 0

    result = envelope.screen()
    for incidence in result["incidences"].values():
        for case in incidence["cases"].values():
            transverse = case["signed_member_local_force_n"][1]
            loaded = case["loaded_transverse_edge"]
            expected_sign = 1 if transverse > 0 else -1 if transverse < 0 else 0
            assert (
                loaded is None
                if expected_sign == 0
                else loaded["sign"] == expected_sign
            )
            if loaded is not None:
                assert (
                    case["supplemental_ec5_splitting"]["governing_loaded_edge_sign"]
                    == expected_sign
                )


def test_both_orthogonal_bore_boxes_are_mapped_without_false_helper_projection():
    result = envelope.screen()
    expected = {
        "shifted_right_post/post_cleat_2": (26.0, 18.7),
        "shifted_right_post/post_high": (26.0, 18.7),
        "upright_side_cleat/upright": (27.5, 20.2),
        "upright_side_cleat/cleat_link": (27.5, 20.2),
    }
    for name, (separation, ligament) in expected.items():
        incidence = result["incidences"][name]
        neighbor = incidence["neighboring_orthogonal_bore"]
        assert neighbor["station_separation_mm"] == pytest.approx(separation)
        assert neighbor["surface_ligament_mm"] == pytest.approx(ligament)
        assert neighbor["represented_as_helper_additional_box"] is False
        for case in incidence["cases"].values():
            net = case["orthogonal_net_section"]
            boxes = net["bore_boxes_in_active_incidence_frame"]
            assert boxes["active_through_x"]["axis_local"] == [1.0, 0.0, 0.0]
            assert boxes["neighbor_through_y"]["axis_local_parallel_to"] == [
                0.0,
                1.0,
                0.0,
            ]
            assert net["helper_additional_section_boxes_used"] is False
            width = incidence["member_local_frame"]["through_bolt_width_mm"]
            depth = incidence["member_local_frame"]["transverse_depth_mm"]
            assert net["active_bore_station_net_area_mm2"] == pytest.approx(
                width * (depth - 7.3)
            )
            assert net["neighbor_bore_station_net_area_mm2"] == pytest.approx(
                (width - 7.3) * depth
            )


def test_unrepresentable_three_dimensional_incidence_fails_closed():
    member = {
        "axis": [0.0, 0.0, 1.0],
        "section_u": [1.0, 0.0, 0.0],
        "section_v": [0.0, 1.0, 0.0],
        "width_mm": 88.9,
        "depth_mm": 61.6,
    }
    with pytest.raises(ValueError, match="not perpendicular"):
        envelope._build_frame(member, [1.0, 0.0, 0.1], "section_u")


def test_governing_result_is_pinned():
    result = envelope.screen()

    assert result["disposition"]["decision"] == "ADVANCE"
    assert result["governing"]["overall"]["ratio"] == pytest.approx(0.02373178159642489)
    assert result["governing"]["overall"]["mode"] == "parallel_row_tear_out"
    assert result["governing"]["overall"]["case"] == "k12-rear"
    assert result["governing"]["overall"]["incidence"] == (
        "upright_side_cleat/cleat_link"
    )
    ec5 = result["governing"]["supplemental_ec5_splitting"]
    assert ec5["ratio"] == pytest.approx(0.010709559438296991)
    assert ec5["mode"] == "directional_splitting"
    assert ec5["case"] == "k12-right"
    assert ec5["incidence"] == "shifted_right_post/post_high"


def test_fails_closed_if_authenticated_evidence_boundary_changes(monkeypatch):
    original = envelope.six_case_evidence.screen

    def changed():
        result = copy.deepcopy(original())
        result["structural_released"] = True
        return result

    monkeypatch.setattr(envelope.six_case_evidence, "screen", changed)
    with pytest.raises(ValueError, match="six-case evidence boundary changed"):
        envelope.screen()


def test_fails_closed_if_bolt_inventory_or_force_ownership_changes(monkeypatch):
    authentication = envelope._authenticate_boundary()
    reports = envelope._load_reports(authentication)
    changed = copy.deepcopy(reports)
    changed[envelope.CASE_ORDER[0]]["physical_connection_forces"].pop(
        "post_block/bolt_2"
    )

    monkeypatch.setattr(envelope, "_load_reports", lambda _: changed)
    with pytest.raises(ValueError, match="bolt inventory changed"):
        envelope.screen()
