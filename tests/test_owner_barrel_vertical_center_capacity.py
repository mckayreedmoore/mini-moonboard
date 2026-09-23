"""Fail-closed tests for the vertical principal/header capacity screen."""

import pytest

from scripts import owner_barrel_vertical_center_capacity as capacity


@pytest.fixture(scope="module")
def report():
    return capacity.build_report()


def test_fixed_geometry_and_proxy_scope_are_explicit(report):
    assert report["geometry"] == {
        "row_pitch_mm": 80.0,
        "barrel_x_ligament_mm": pytest.approx(14.0462),
        "wood_beyond_blind_barrel_bore_mm": pytest.approx(9.0424),
        "washer_header_edge_reserve_mm": pytest.approx(20.1877),
        "panel_kicker_screw_count": 66,
        "panel_kicker_axes_unchanged": 62,
        "panel_kicker_axes_relocated": 4,
        "old_2p092_mm_header_pocket_applicable": False,
        "old_header_pocket_disposition": (
            "Eliminated by the flat underside seats of the vertical bolts."
        ),
    }
    demands = report["demands"]
    assert demands["fresh_barrel_cases"] == 0
    assert demands["missing_case"] == "a12-forward"
    assert demands["qualified_demand"] is False
    assert demands["maximum_absolute_axial_row_n"] == pytest.approx(
        921.800384, abs=1e-6
    )
    assert demands["maximum_face_compression_row_n"] == pytest.approx(
        921.800384, abs=1e-6
    )
    assert demands["maximum_bolt_tension_row_n"] == pytest.approx(301.493967, abs=1e-6)
    assert demands["maximum_unresolved_my_nmm"] == pytest.approx(10589.378494, abs=1e-6)


def test_published_method_adaptations_are_numerically_pinned(report):
    bearing = report["resistance"]["wood_barrel_bearing"]
    assert bearing["dfl_dowel_bearing_psi"] == pytest.approx(4521.253581)
    assert bearing["fabbri_projected_area_mm2"] == pytest.approx(115.962969)
    assert bearing["nds_mode_i_reduction_term"] == pytest.approx(4.444444)
    assert bearing["nds_fabbri_nominal_reference_n"] == pytest.approx(813.354158)
    assert bearing["fpl_rectangular_area_mm2"] == pytest.approx(85.084615)
    assert bearing["fpl_divide_by_four_reference_n"] == pytest.approx(663.084531)
    assert bearing["worst_provisional_distance_factor"] == pytest.approx(0.521766)
    assert bearing["distance_reduced_nds_fabbri_reference_n"] == pytest.approx(
        424.381, abs=0.01
    )
    assert bearing["distance_reduced_fpl_reference_n"] == pytest.approx(
        345.975, abs=0.01
    )
    assert bearing["comparison"]["proxy_bolt_tension_demand_n"] == pytest.approx(
        report["demands"]["maximum_bolt_tension_row_n"]
    )
    assert bearing["comparison"]["relation"] == "ABOVE_PROXY_REFERENCE"


def test_washer_and_bolt_are_kept_as_separate_constituents(report):
    resistance = report["resistance"]
    washer = resistance["header_washer_bearing"]
    assert washer["washer_contact_area_mm2"] == pytest.approx(213.627873)
    assert washer["nominal_reference_n"] == pytest.approx(920.57021)
    assert washer["comparison"]["demand_to_reference_ratio"] < 1
    assert washer["comparison"]["relation"] == "ABOVE_PROXY_REFERENCE"
    bolt = resistance["bolt_constituent_proof"]
    assert bolt["minimum_proof_n"] == pytest.approx(12023.543026)
    assert bolt["comparison"]["relation"] == "ABOVE_PROXY_REFERENCE"
    assert resistance["unsupported"]["barrel_metal_thread_wall_and_flexure"].startswith(
        "UNRESOLVED"
    )


def test_signed_raw_face_rays_replace_projected_bbox_distances(report):
    rows = report["resistance"]["principal_raw_face_rays"]
    assert len(rows) == 4
    for row in rows:
        assert row["grain_negative_mm"] == pytest.approx(36.551404)
    rear = next(row for row in rows if row["bolt"].endswith("_1"))
    forward = next(row for row in rows if row["bolt"].endswith("_2"))
    assert rear["cross_grain_positive_mm"] == pytest.approx(41.648258)
    assert rear["cross_grain_negative_mm"] == pytest.approx(43.560267)
    assert forward["cross_grain_positive_mm"] == pytest.approx(102.931814)
    assert forward["cross_grain_negative_mm"] == pytest.approx(36.768186)


def test_decision_does_not_turn_proxy_or_screen_into_release(report):
    decision = report["decision"]
    assert (
        decision["cad_only_adapted_reference_screen"]
        == "ABOVE_PROXY_ADAPTED_REFERENCES_ONLY"
    )
    assert decision["below_proxy_adapted_references"] == []
    assert decision["finite_decision"] == "EVIDENCE_BLOCKED"
    assert decision["physical_joint_failure_proved"] is False
    assert decision["paper_only_go_available_for_current_stafast_part"] is False
    assert not decision["diy_ready"]
    assert not decision["drilling_released"]
    assert not decision["fabrication_released"]
    assert not decision["structural_released"]
