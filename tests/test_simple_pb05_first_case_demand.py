"""PB05 demands must remain tied to the accepted A12 report and PB05 solids."""

import json

import pytest

from scripts.simple_pb05_first_case_demand import DEFAULT_REPORT, REPORT_SHA256, analyze


@pytest.fixture(scope="module")
def result():
    return analyze()


def test_authenticated_inventory_and_signed_actions(result):
    assert result["report_sha256"] == REPORT_SHA256
    assert result["case"] == "a12-forward"
    assert result["source_identity"]["fixed_panel_kicker_axes"] == 66
    assert result["source_identity"]["legacy_proxy_stations"] == 14
    assert len(result["bolts"]) == 32
    assert len(result["contacts"]) == 64
    assert len(result["interfaces"]) == 16
    assert all(
        row["bolt_count"] == 2 and row["contact_cell_count"] == 4
        for row in result["interfaces"]
    )
    assert all(
        len(row["moment_about_interface_centroid_nmm"]) == 3
        for row in result["interfaces"]
    )
    assert all(
        set(row["signed_end_edge"]["members"]) == set(row["members"])
        for row in result["bolts"]
    )
    assert all(
        row["wood_yield_bearing_sensitivity"]["qualified"] is False
        for row in result["bolts"]
    )
    assert max(row["transverse_shear_n"] for row in result["bolts"]) == pytest.approx(
        124.2508294813382
    )
    assert max(row["axial_tension_n"] for row in result["bolts"]) == pytest.approx(
        73.3488307960223
    )
    assert {
        row["name"] for row in result["bolts"] if not row["signed_end_edge"]["passes"]
    } == {
        f"pb03_{station}_outer_{side}_rail_1"
        for station in ("lower", "upper", "bottom")
        for side in ("left", "right")
    }
    assert result["uncomputed_joint_modes"]["group_action"] is False
    assert result["uncomputed_joint_modes"]["splitting"] is False
    assert result["qualified_for_design"] is False
    assert result["structural_released"] is False
    assert "joint_verdict" not in result


def test_rejects_changed_report(tmp_path):
    changed = json.loads(DEFAULT_REPORT.read_text())
    changed["parameters"]["force_xyz_n"][1] += 1
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="report SHA-256"):
        analyze(path)
