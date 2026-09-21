"""Source-bound PB03 a12-forward demand and direction analysis."""

import json

import pytest

from scripts.simple_pb03_first_case_demand import (
    DEFAULT_REPORT,
    REPORT_SHA256,
    analyze,
)

REPORT = DEFAULT_REPORT


@pytest.fixture(scope="module")
def result():
    return analyze(REPORT)


def test_authenticates_exact_report_and_geometry_sources(result):
    assert result["schema"] == "simple_pb03_first_case_demand/v1"
    assert result["case"] == "a12-forward"
    assert result["report_sha256"] == REPORT_SHA256
    assert result["candidate"] == "pb03-lower-service-plus-upper-and-bottom-outer-v1"
    assert result["source_identity"]["report_numerically_accepted"] is True
    assert result["source_identity"]["pb03_bolt_count"] == 32
    assert result["source_identity"]["pb03_contact_cell_count"] == 64
    assert result["source_identity"]["active_geometry_station_count"] == 8
    assert result["source_identity"]["three_eighths_geometry_station_count"] == 8


def test_recovers_simultaneous_bolts_and_combined_interface_resultants(result):
    bolts = result["bolts"]
    assert len(bolts) == 32
    assert len({row["name"] for row in bolts}) == 32
    assert all(len(row["force_on_host_xyz_n"]) == 3 for row in bolts)
    assert all(len(row["axial_on_host_xyz_n"]) == 3 for row in bolts)
    assert all(len(row["lateral_on_host_xyz_n"]) == 3 for row in bolts)
    assert all(
        row["transverse_shear_n"]
        == pytest.approx(
            sum(value * value for value in row["lateral_on_host_xyz_n"]) ** 0.5
        )
        for row in bolts
    )
    assert len(result["interfaces"]) == 16
    assert {row["connector_count"] for row in result["interfaces"]} == {6}
    assert {row["bolt_count"] for row in result["interfaces"]} == {2}
    assert {row["contact_cell_count"] for row in result["interfaces"]} == {4}
    assert all(len(row["force_on_block_xyz_n"]) == 3 for row in result["interfaces"])
    assert all(
        len(row["moment_about_interface_centroid_nmm"]) == 3
        for row in result["interfaces"]
    )


def test_maps_force_signs_and_checks_both_diameters_without_combining_modes(result):
    for row in result["bolts"]:
        assert set(row["member_directions"]) == set(row["members"])
        for member in row["member_directions"].values():
            assert member["grain_force_n"] == pytest.approx(
                sum(
                    force * axis
                    for force, axis in zip(
                        member["lateral_force_xyz_n"],
                        member["grain_axis_xyz"],
                        strict=True,
                    )
                )
            )
            assert member["edge_force_n"] == pytest.approx(
                sum(
                    force * axis
                    for force, axis in zip(
                        member["lateral_force_xyz_n"],
                        member["edge_axis_xyz"],
                        strict=True,
                    )
                )
            )
        assert set(row["diameter_checks"]) == {"quarter_in", "three_eighths_in"}
        for check in row["diameter_checks"].values():
            assert set(check["component_ratios"]) == {
                "wood_yield",
                "bolt_steel_shear",
                "bolt_steel_tension",
                "washer_wood_bearing",
            }
            assert "combined_ratio" not in check


def test_reports_exact_geometry_failures_and_development_decision(result):
    summary = result["summary"]
    assert summary["maximum_demand_n"] == pytest.approx(110.3996588054)
    assert summary["maximum_demand_bolt"] == "pb03_bottom_outer_left_rail_2"
    assert summary["maximum_conditional_component_ratio"] == pytest.approx(0.2308728482)
    assert summary["quarter_in"]["failed_geometry_stations"] == [
        "clip_horizontal_upper_left_1",
        "clip_horizontal_upper_right_2",
    ]
    assert summary["three_eighths_in"]["failed_geometry_stations"] == list(
        result["source_identity"]["mechanics_identity"]["replaced_stations"]
    )
    assert summary["decision"] == "REVISE"
    assert summary["decision_scope"] == "development_only"
    assert result["capacity_aggregation"] == "prohibited_serial_components_not_combined"
    assert result["developmental_only"] is True
    assert result["actual_joint_demands_qualified"] is False
    assert result["acceptance"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def test_rejects_any_report_mutation(tmp_path):
    changed = json.loads(REPORT.read_text())
    changed["parameters"]["force_xyz_n"][1] += 1
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="report SHA-256"):
        analyze(path)
