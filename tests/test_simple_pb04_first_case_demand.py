"""Authenticated PB04 first-case development screen."""

import json

import pytest

from scripts.simple_pb04_first_case_demand import DEFAULT_REPORT, REPORT_SHA256, analyze


@pytest.fixture(scope="module")
def result():
    return analyze()


def test_authenticated_same_case_inventory(result):
    assert result["report_sha256"] == REPORT_SHA256
    assert result["case"] == "a12-forward"
    assert result["source_identity"]["mechanics_identity"][
        "mechanics_source_id"
    ].startswith("pb04-")
    assert len(result["bolts"]) == 32
    assert len({row["name"] for row in result["bolts"]}) == 32
    assert len(result["interfaces"]) == 16
    assert all(
        row["bolt_count"] == 2 and row["contact_cell_count"] == 4
        for row in result["interfaces"]
    )


def test_signed_directions_and_separate_component_sensitivities(result):
    for bolt in result["bolts"]:
        assert bolt["transverse_shear_n"] >= 0
        assert bolt["axial_tension_n"] >= 0
        assert set(bolt["member_directions"]) == set(bolt["members"])
        checks = bolt["separate_checks"]
        assert set(checks) == {
            "wood_yield_bearing_sensitivity",
            "bolt_shear",
            "bolt_tension",
            "washer_wood_bearing_sensitivity",
            "signed_end_edge",
        }
        assert checks["signed_end_edge"]["passes"] == all(
            row["passes"] for row in checks["signed_end_edge"]["members"].values()
        )
        assert "combined_ratio" not in bolt


def test_counterbore_net_gates_remain_unqualified(result):
    local = result["counterbore_local_gates"]
    assert len(local["stations"]) == 6
    assert all(row["pocket_count"] == 2 for row in local["stations"])
    assert all(
        row["remaining_axial_wood_mm"] < row["gross_block_length_mm"]
        for row in local["stations"]
    )
    assert all(
        row["remaining_axial_wood_mm"] == pytest.approx(102.7176)
        for row in local["stations"]
    )
    assert all(
        row["pocket_to_outer_edge_ligament_mm"] == pytest.approx(15.875)
        for row in local["stations"]
    )
    assert all(
        row["between_pockets_ligament_mm"] == pytest.approx(19.6)
        for row in local["stations"]
    )
    assert all(
        len(row["upright_interface_moment_nmm"]) == 3 for row in local["stations"]
    )
    assert local["net_section_qualified"] is False
    assert local["group_action_qualified"] is False
    assert local["splitting_qualified"] is False
    assert result["summary"]["development_decision"] == "REVISE"
    assert result["summary"]["failed_signed_edge_end_bolts"] == []
    assert result["summary"]["maximum_transverse_shear_n"] == pytest.approx(
        111.4434667003
    )
    assert result["summary"]["maximum_axial_tension_n"] == pytest.approx(69.0783045185)
    assert "net-section" in result["summary"]["exact_next_physical_revision_or_gate"]
    assert result["summary"]["altered_geometry_assessed"] is False
    assert result["structural_released"] is False


def test_upper_outer_block_short_ends_use_reduced_geometry_reference(result):
    expected = {
        "pb03_upper_outer_left_rail_1": (-39.0837606600, 396.4410528350),
        "pb03_upper_outer_right_rail_1": (-45.7190298883, 371.6172637401),
    }
    targets = [bolt for bolt in result["bolts"] if bolt["name"] in expected]
    assert len(targets) == 2
    for bolt in targets:
        block = bolt["members"][1]
        end = bolt["separate_checks"]["signed_end_edge"]["members"][block]["grain_end"]
        conditional = bolt["separate_checks"]["wood_yield_bearing_sensitivity"][
            "conditional_block_end_distance"
        ]
        assert end["force_component_n"] == pytest.approx(expected[bolt["name"]][0])
        assert end["loaded_distance_mm"] == pytest.approx(35.709)
        assert end["minimum_loaded_mm"] == pytest.approx(22.225)
        assert end["full_value_loaded_mm"] == pytest.approx(44.45)
        assert end["passes"] is True
        assert end["full_value_attained"] is False
        assert end["oblique_shear_area_qualified"] is False
        assert conditional["geometry_factor"] == pytest.approx(35.709 / 44.45)
        assert conditional["conditional_reference_n"] == pytest.approx(
            expected[bolt["name"]][1]
        )
        assert conditional["conditional_reference_n"] == pytest.approx(
            bolt["separate_checks"]["wood_yield_bearing_sensitivity"]["capacity_n"]
            * conditional["geometry_factor"]
        )
        assert conditional["demand_n"] == pytest.approx(bolt["transverse_shear_n"])
        assert conditional["geometry_scope"] == "initial_authenticated_PB04_only"
        assert conditional["joint_rating"] is False
        assert conditional["oblique_shear_area_qualified"] is False


def test_rejects_report_mutation(tmp_path):
    changed = json.loads(DEFAULT_REPORT.read_text())
    changed["parameters"]["force_xyz_n"][1] += 1
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="report SHA-256"):
        analyze(path)
