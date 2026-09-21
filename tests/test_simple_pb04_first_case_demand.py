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
    assert result["summary"]["failed_signed_edge_end_bolts"] == [
        "pb03_upper_outer_left_rail_1",
        "pb03_upper_outer_right_rail_1",
    ]
    assert result["summary"]["maximum_transverse_shear_n"] == pytest.approx(
        111.4434667003
    )
    assert result["summary"]["maximum_axial_tension_n"] == pytest.approx(69.0783045185)
    assert "11.741 mm" in result["summary"]["exact_next_physical_revision_or_gate"]
    assert result["structural_released"] is False


def test_rejects_report_mutation(tmp_path):
    changed = json.loads(DEFAULT_REPORT.read_text())
    changed["parameters"]["force_xyz_n"][1] += 1
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="report SHA-256"):
        analyze(path)
