"""One narrow rear-face trial against unified 24-duty topology only."""

import json

import pytest

from scripts import owner_layout_bottom_center_pair as first
from scripts import owner_layout_bottom_center_rear as rear


def test_source_declares_one_rear_pose_without_changing_front_trial():
    assert rear.SOURCE_ID not in (first.SOURCE_ID,)
    assert rear.BLOCK_X_MM == 77.0
    assert rear.BLOCK_N_MIN_MM == 260.0
    assert rear.RAIL_N_OFFSET_MM == 85.0
    assert first.BLOCK_X_MM == 139.7
    assert first.RAIL_N_MM == 69.85


@pytest.fixture(scope="module")
def report():
    result = rear.screen()
    print(
        "REAR_TRIAL_OUTCOME="
        + json.dumps(
            {
                "decision": result["decision"],
                "binding_constraints": result["binding_constraints"],
                "block_bounds": {
                    name: {
                        "t": row["block_local_t_bounds_mm"],
                        "n": row["block_local_n_bounds_mm"],
                        "contact": row["contact_area_mm2"],
                        "bores": row["complete_bores_by_bolt"],
                    }
                    for name, row in result["pairs"].items()
                },
            },
            sort_keys=True,
        )
    )
    return result


def test_unified_topology_and_rear_host_diagnostic(report):
    assert report["source_id"] == rear.SOURCE_ID
    assert report["block_side"] == "rear"
    assert report["retained_pb02_side_cleat"] is False
    assert report["inventory"]["fixed_panel_kicker_axes"] == 66
    assert report["inventory"]["retained_frame_bolts"] == 12
    assert report["inventory"]["target_legacy_sds"] == 12
    for name, row in report["pairs"].items():
        side = "left" if "_left_" in name else "right"
        assert row["block_dimensions_mm"] == [77.0, 57.15, 139.7]
        assert row["block_local_n_bounds_mm"] == [260.0, 399.7]
        assert row["block_local_t_bounds_mm"] == pytest.approx(
            [183.474134, 240.624134], abs=0.00001
        )
        assert row["block_side_cleat_hit_mm3"] is None
        assert row["contact_area_mm2"]["rail"] > 0
        assert row["contact_area_mm2"]["principal"] > 0
        assert (
            row["complete_bores_by_bolt"][f"owner_bottom_{side}_principal_2"] is False
        )
        assert all(
            complete
            for bolt, complete in row["complete_bores_by_bolt"].items()
            if not bolt.endswith("principal_2")
        )
        assert not row["other_timber_hits_mm3"]
        assert not row["protected_axis_hits_mm3"]


def test_finite_wire_conflict_and_no_release(report):
    left, right = (report["pairs"][name] for name in first.STATIONS)
    assert not left["finite_protected_hits"].get("block")
    assert right["finite_protected_hits"]["block"]["wires"] == {
        "wire_072_F1_G1": pytest.approx(533.4042)
    }
    assert report["decision"] == "REVISE"
    assert report["rear_basis"]["F1_G1_wire_n_overlap_with_block_mm"] == pytest.approx(
        21.690589594209
    )
    assert report["rear_basis"]["owner_rear_envelope_compliant"] is False
    assert report["rear_basis"]["owner_exception_required"] is True
    assert report["rear_basis"][
        "rear_block_n_overhang_beyond_rail_mm"
    ] == pytest.approx(50.159032140687)
    assert report["rear_basis"][
        "max_block_n_low_for_two_4D_edges_and_4D_pitch_mm"
    ] == pytest.approx(273.340967859313)
    assert all(
        gate["status"] == "UNVERIFIED" for gate in report["protected_3d_gates"].values()
    )
    assert not report["native_solve"]
    assert not report["drilling_released"]
    assert not report["structural_released"]
