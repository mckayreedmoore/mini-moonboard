from __future__ import annotations

from pathlib import Path

import actions
import pytest


def point_action(action_id: str, x: float, force: list[float]) -> dict:
    return {
        "action_id": action_id,
        "point_xyz_mm": [x, 0.0, 0.0],
        "force_n": force,
        "force_rounding_radius_n": [0.0, 0.0, 0.0],
    }


def test_paired_endpoint_forces_preserve_separated_point_couple() -> None:
    datum = [0.0, 0.0, 0.0]
    block = actions.wrench_at_point(
        [0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [0.0, 0.0, 0.0], datum
    )
    receiver = actions.wrench_at_point(
        [0.0, 1.0, 0.0], [-10.0, 0.0, 0.0], [0.0, 0.0, 0.0], datum
    )

    assert actions.add(block["force_n"], receiver["force_n"]) == [0.0, 0.0, 0.0]
    assert block["moment_nmm"] == [0.0, 0.0, 0.0]
    assert receiver["moment_nmm"] == [0.0, 0.0, 10.0]
    assert actions.add(block["moment_nmm"], receiver["moment_nmm"]) == [0.0, 0.0, 10.0]


def test_opposite_side_signed_actions_reconstruct_zero_whole_body_wrench() -> None:
    trace = actions.section_traces(
        [point_action("negative", -1.0, [4.0, 0.0, 0.0]), point_action("positive", 1.0, [-4.0, 0.0, 0.0])],
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
    )
    assert trace["whole_point_action_wrench_at_plane"]["force_n"] == [0.0, 0.0, 0.0]
    for sides in trace["one_sided_traces"].values():
        assert sides["positive_side_external_wrench"]["force_n"] == [-4.0, 0.0, 0.0]
        assert sides["negative_side_external_wrench"]["force_n"] == [4.0, 0.0, 0.0]
        assert sides["cut_wrench_on_positive_side_material"]["force_n"] == [4.0, 0.0, 0.0]
        assert sides["cut_wrench_on_negative_side_material"]["force_n"] == [-4.0, 0.0, 0.0]
        assert sides["two_cut_side_reactions_plus_whole_external_residual"]["force_n"] == [0.0, 0.0, 0.0]


def test_moment_transport_uses_new_datum_arm() -> None:
    wrench = actions.wrench_at_point(
        [1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    )
    moved = actions._wrench_transport_to_datum(wrench, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    assert wrench["moment_nmm"] == [0.0, 0.0, 2.0]
    assert moved["moment_nmm"] == [0.0, 0.0, 0.0]
    assert moved["force_n"] == [0.0, 2.0, 0.0]


def test_on_plane_point_action_is_whole_in_each_distinct_one_sided_trace() -> None:
    actions_at_plane = [
        point_action("negative", -1.0, [2.0, 0.0, 0.0]),
        point_action("on-plane", 0.0, [3.0, 0.0, 0.0]),
        point_action("positive", 1.0, [-5.0, 0.0, 0.0]),
    ]
    trace = actions.section_traces(actions_at_plane, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    below = trace["one_sided_traces"]["approached_from_negative_coordinate"]
    above = trace["one_sided_traces"]["approached_from_positive_coordinate"]

    assert trace["on_plane_action_ids"] == ["on-plane"]
    assert below["on_plane_actions_assigned_to"] == "positive"
    assert above["on_plane_actions_assigned_to"] == "negative"
    assert "on-plane" in below["positive_side_action_ids"]
    assert "on-plane" in above["negative_side_action_ids"]
    assert below["positive_side_external_wrench"]["force_n"] == [-2.0, 0.0, 0.0]
    assert above["positive_side_external_wrench"]["force_n"] == [-5.0, 0.0, 0.0]
    assert actions.sub(
        above["positive_side_external_wrench"]["force_n"],
        below["positive_side_external_wrench"]["force_n"],
    ) == [-3.0, 0.0, 0.0]
    assert trace["whole_point_action_wrench_at_plane"]["force_n"] == [0.0, 0.0, 0.0]


def test_source_pin_change_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "pinned.json"
    source.write_bytes(b"current source")
    monkeypatch.setattr(actions, "PINNED_SHA256", {"pinned.json": "0" * 64})

    with pytest.raises(actions.SourceRefusal, match="pinned source changed"):
        actions.verify_pinned_sources(tmp_path)


def test_duplicate_or_nonfinite_section_actions_fail_closed() -> None:
    duplicate_ids = [point_action("same", -1.0, [1.0, 0.0, 0.0]), point_action("same", 1.0, [-1.0, 0.0, 0.0])]
    with pytest.raises(actions.SourceRefusal, match="duplicate IDs"):
        actions.section_traces(duplicate_ids, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])

    nonfinite = [point_action("bad", 0.0, [float("nan"), 0.0, 0.0])]
    with pytest.raises(actions.SourceRefusal, match="finite"):
        actions.section_traces(nonfinite, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])


def test_full_source_replay_retains_all_same_state_rows_without_acceptance_claims() -> None:
    report, pins = actions.build_report()

    assert len(pins["sources"]) == len(actions.PINNED_SHA256)
    assert report["counts"] == {
        "blocks": 2,
        "cases": 3,
        "increments_per_case": 7,
        "same_state_records": 42,
        "receiver_point_action_rows": 672,
        "discrete_body_load_rows": 840,
        "exact_section_state_records": 210,
        "cut_side_traces": 420,
    }
    assert report["claim_boundary"]["complete_joint_resistance_established"] is False
    assert report["claim_boundary"]["six_case_envelope_established"] is False
    assert report["claim_boundary"]["section_capacity_calculated"] is False
    for state in report["states"]:
        assert state["source_point_action_count"] == 36
        assert state["source_incident_connection_count"] == 16
        assert state["source_body_load_node_count"] == 20
        assert state["receiver_groups_reproduce_frozen_source"] is True
        assert state["whole_body_equilibrium"]["source_upper_residual_reproduced"] is True
        assert len(state["exact_geometry_section_wrenches"]) == 5
        for section in state["exact_geometry_section_wrenches"]:
            trace = section["point_action_wrench_and_traces"]
            assert trace["actual_finite_element_half_body_traction_established"] is False
            assert len(trace["one_sided_traces"]) == 2
