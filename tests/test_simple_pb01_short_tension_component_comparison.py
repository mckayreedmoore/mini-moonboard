"""The two short-block cases remain separate provisional component screens."""

import pytest

from scripts.simple_pb01_short_tension_component_comparison import compare


def test_two_finished_cases_keep_signed_actions_and_unknown_utilizations():
    result = compare()
    assert result["block_length_mm"] == 152.4
    assert result["proxy_station_count_per_case"] == 23
    assert set(result["cases"]) == {"a12-left", "k12-right"}
    assert result["whole_joint_utilization"] is None
    assert result["drilling_released"] is False
    for case in result["cases"].values():
        assert case["numerically_accepted"] is True
        assert case["whole_joint_utilization"] is None
        assert set(case["interfaces"]) == {"upright", "rail"}
        rows = {
            row["name"]: row
            for face in case["interfaces"].values()
            for row in face["bolts"]
        }
        assert len(rows) == 4
        assert rows["pb01_rail_r1"]["axial_on_host_n"] > 0
        for name in ("pb01_upright_u1", "pb01_upright_u2", "pb01_rail_r2"):
            assert rows[name]["axial_on_host_n"] == pytest.approx(0, abs=1e-6)
            assert rows[name]["axial_status"] == "slack"
        for row in rows.values():
            assert row["lateral_on_host_magnitude_n"] >= 0
            assert (
                row["conditional_one_bolt_lateral"]["0.189"]["modeled_direction_ratio"]
                >= 0
            )
            assert row["group_utilization"] is None
            assert row["washer_utilization"] is None
        for face in case["interfaces"].values():
            assert len(face["contacts"]) == 4
            assert face["active_contact_count"] == sum(
                c["active"] for c in face["contacts"]
            )
            assert face["compression_n"] == pytest.approx(
                sum(c["compression_n"] for c in face["contacts"])
            )
            assert face["group_utilization"] is None
            assert face["cleat_utilization"] is None
            assert face["contact_utilization"] is None


def test_specific_contact_sets_and_case_differences():
    result = compare()
    a12 = result["cases"]["a12-left"]
    k12 = result["cases"]["k12-right"]
    assert a12["interfaces"]["upright"]["active_contact_count"] == 2
    assert k12["interfaces"]["upright"]["active_contact_count"] == 4
    assert a12["interfaces"]["rail"]["active_contact_count"] == 2
    assert k12["interfaces"]["rail"]["active_contact_count"] == 2
    assert a12["interfaces"]["upright"]["compression_n"] == pytest.approx(14.5645)
    assert k12["interfaces"]["upright"]["compression_n"] == pytest.approx(62.831)
    assert a12["interfaces"]["rail"]["compression_n"] == pytest.approx(19.80844975)
    assert k12["interfaces"]["rail"]["compression_n"] == pytest.approx(31.19565)
    assert a12["interfaces"]["rail"]["bolts"][0]["axial_on_host_n"] == pytest.approx(
        20.49452
    )
    assert k12["interfaces"]["rail"]["bolts"][0]["axial_on_host_n"] == pytest.approx(
        19.6676
    )
    assert a12["interfaces"]["upright"]["resultant_on_host"][
        "force_xyz_n"
    ] == pytest.approx([-14.5645, 0.371, -9.993], abs=0.001)
    assert k12["interfaces"]["rail"]["resultant_on_host"][
        "moment_xyz_nmm"
    ] == pytest.approx([-559.5465, 596.3107, -28.8343], abs=0.001)


def test_rejects_archive_swap():
    from scripts.simple_pb01_short_tension_component_comparison import RUNS

    with pytest.raises(ValueError, match="Archive digest"):
        compare({"a12-left": RUNS["k12-right"], "k12-right": RUNS["a12-left"]})
