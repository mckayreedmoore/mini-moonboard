"""Published PB02 stiffness bases stay source-bound and non-releasing."""

import math

import pytest

from scripts.simple_center_published_stiffness_basis import report


@pytest.fixture(scope="module")
def result():
    return report()


def test_published_lateral_bases_preserve_formula_and_unit_semantics(result):
    nds = result["lateral_bolt_slip"]["nds_2024"]

    assert nds["edition"] == "2024 NDS with 2025-03-28 errata/addenda"
    assert nds["connection_type"] == "wood-to-wood dowel-type connection"
    assert nds["formula"] == "gamma = 180000 * D^1.5 lb/in"
    assert nds["diameter_D_in"] == pytest.approx(0.25)
    assert nds["gamma_lb_per_in"] == pytest.approx(22_500.0)
    assert nds["gamma_n_per_mm"] == pytest.approx(3940.353779527591)
    assert "11.3.6.1" in nds["basis"]
    assert "group-action" in nds["basis"]
    assert "Single-bolt, single-shear-plane" in nds["semantics"]
    assert "2024-NDS-Errata" in nds["source_url"]
    assert any(
        "not a general 3D spring law" in row for row in nds["applicability_limits"]
    )
    assert any("not a strength" in row for row in nds["applicability_limits"])

    ec5 = result["lateral_bolt_slip"]["ec5_service"]
    expected = {
        460.0: 2723.8465448699562,
        480.0: 2903.405835262168,
        500.0: 3086.746012418188,
        520.0: 3273.7906553716116,
    }
    assert ec5["formula"] == "Kser = rho_mean^1.5 * d / 23"
    assert ec5["diameter_d_mm"] == pytest.approx(6.35)
    assert ec5["semantics"] == "Per fastener per shear plane at service-level loading."
    assert "fpl_2016_rammer001P.pdf" in ec5["source_url"]
    assert {
        row["rho_mean_kg_per_m3"]: row["kser_n_per_mm_per_bolt_per_shear_plane"]
        for row in ec5["density_sensitivities"]
    } == pytest.approx(expected)


def test_clearance_is_only_an_unselected_geometric_sensitivity(result):
    clearance = result["diagnostic_bore_clearance_sensitivity"]

    assert clearance["diagnostic_bore_diameter_mm"] == pytest.approx(7.5)
    assert clearance["nominal_bolt_diameter_mm"] == pytest.approx(6.35)
    assert clearance["diametral_difference_mm"] == pytest.approx(1.15)
    assert clearance["one_sided_geometric_dead_zone_mm"] == pytest.approx(0.575)
    assert "Ideal centered radial travel" in clearance["interpretation"]
    assert clearance["is_drill_size"] is False
    assert clearance["is_selected_clearance"] is False
    assert clearance["design_input_qualified"] is False


def test_all_ten_active_bolts_use_nominal_and_root_ea_over_l_arithmetic(result):
    axial = result["steel_only_bolt_axial_sensitivities"]
    rows = axial["rows"]

    assert len(rows) == 10
    assert len({row["bolt"] for row in rows}) == 10
    assert all(row["active_wood_grip_mm"] > 0 for row in rows)
    assert "active_geometry()" in axial["grip_source"]
    assert axial["formula"] == "K_bolt,steel-only = E_steel * A / L"

    expected_areas = {
        "nominal_6_35mm_full_shank_area": math.pi * 6.35**2 / 4,
        "typical_root_4_8006mm_diameter_sensitivity": math.pi * 4.8006**2 / 4,
    }
    assert axial["area_models_mm2"] == pytest.approx(expected_areas)
    for row in rows:
        grip = row["active_wood_grip_mm"]
        expected_stiffnesses = {
            label: axial["steel_modulus_n_per_mm2"] * area / grip
            for label, area in expected_areas.items()
        }
        assert row["steel_only_ea_over_l_n_per_mm"] == pytest.approx(
            expected_stiffnesses
        )


def test_unresolved_compliances_remain_templates_and_nothing_is_released(result):
    templates = result["uncomputed_compliance_templates"]
    washer = templates["washer_seat_and_axial_joint"]
    contact = templates["wood_face_contact"]

    assert washer["computed"] is False
    assert washer["qualified"] is False
    assert washer["value_n_per_mm"] is None
    assert contact["computed"] is False
    assert contact["qualified"] is False
    assert contact["value_n_per_mm"] is None
    assert contact["effective_depth_mm"] is None
    assert contact["dfl_elastic_ratios"] == {
        "radial_E_R_over_E_L": pytest.approx(0.068),
        "tangential_E_T_over_E_L": pytest.approx(0.050),
    }

    status = result["status"]
    assert status["lateral_values_are_published_sensitivities_not_selected_properties"]
    assert status["axial_joint_stiffness_unqualified_and_uncomputed"]
    assert status["face_contact_stiffness_unqualified_and_uncomputed"]
    assert status["design_release"] is False
    assert status["fabrication_release"] is False
    assert status["drilling_release"] is False
