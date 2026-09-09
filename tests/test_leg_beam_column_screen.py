"""Archive-backed mapping diagnostics, deliberately not strength qualification."""
import json
import tarfile
from pathlib import Path

import pytest

from fea import leg_beam_column_screen as diagnostic


def test_force_decomposition_keeps_eccentric_moment_exactly_once():
    p, f = {1: [19.05, 0., 100.]}, {1: [10., 20., -1000.]}
    result = diagnostic.decompose(p, f, [0., 0., 0.], [0., 0., 1.], [0., 1., 0.])
    assert result["axial_n_tension_positive"] == -1000.
    assert result["eccentricity_xyz_mm"] == pytest.approx([19.05, 0., 0.])
    assert result["axial_moment_xyz_nmm"] == pytest.approx([0., 19050., 0.])
    assert result["side_load_moment_xyz_nmm"] == pytest.approx([-2000., 1000., 381.])
    assert result["total_moment_xyz_nmm"] == pytest.approx([-2000., 20050., 381.])
    moved = diagnostic.decompose(p, f, [0., 0., 70.], [0., 0., 1.], [0., 1., 0.])
    assert moved["axial_moment_xyz_nmm"] == result["axial_moment_xyz_nmm"]
    assert moved["eccentricity_xyz_mm"] == result["eccentricity_xyz_mm"]
    assert moved["side_load_moment_xyz_nmm"] == pytest.approx([-600., 300., 381.])


def test_cancelling_axial_loads_have_no_single_resultant_eccentricity():
    r = diagnostic.decompose({1: [10., 0., 50.], 2: [-10., 0., 100.]},
        {1: [0., 0., -100.], 2: [0., 0., 100.]},
        [0., 0., 0.], [0., 0., 1.], [0., 1., 0.])
    assert r["axial_n_tension_positive"] == 0
    assert r["eccentricity_xyz_mm"] is None
    assert r["axial_moment_xyz_nmm"] == [0., 2000., 0.]


def test_invalid_decomposition_axes_and_force_rejected():
    with pytest.raises(ValueError):
        diagnostic.decompose({1: [0., 0., 1.]}, {1: [0., 0., -1.]},
                             [0., 0., 0.], [1., 0., 0.], [0., 0., 0.])
    with pytest.raises(ValueError):
        diagnostic.decompose({1: [0., 0., 1.]}, {1: [0., 0., float("nan")]},
                             [0., 0., 0.], [0., 0., 1.], [0., 1., 0.])


def test_clear_strip_cancellation_does_not_bound_loaded_region_moment():
    # Three transverse forces have zero total force and zero total moment
    # below the group, but a 100 Nmm moment at the middle applied force.
    points = {1: [0., 0., 1.], 2: [0., 0., 2.], 3: [0., 0., 3.]}
    forces = {1: [100., 0., 0.], 2: [-200., 0., 0.], 3: [100., 0., 0.]}
    result = diagnostic.envelope(points, forces, lambda s: [0., 0., s],
                                 [0., 0., 1.], [0., 1., 2., 3.])
    assert result["absolute_total_bending_in_out_nmm"] == [0., 100.]
    assert result["witnesses"][1]["station_from_foot_mm"] == 2.
    for station in (0., .5):
        clear = diagnostic.decompose(points, forces, [0., 0., station],
                                     [0., 0., 1.], [0., 1., 0.])
        assert clear["total_moment_xyz_nmm"] == [0., 0., 0.]


@pytest.mark.parametrize("station_roundoff", [0., 1e-10])
def test_eccentric_axial_load_jumps_are_sampled_on_both_sides(station_roundoff):
    result = diagnostic.envelope({1: [10., 0., 1.+station_roundoff], 2: [10., 0., 2.]},
        {1: [0., 0., 100.], 2: [0., 0., -100.]},
        lambda s: [0., 0., s], [0., 0., 1.], [0., 1., 2.])
    assert result["absolute_total_bending_in_out_nmm"] == [0., 1000.]
    assert result["witnesses"][1] == {"station_from_foot_mm": 1.,
                                      "include_station_loads": False, "moment_nmm": 1000.}


def test_archive_diagnostic_retains_cases_and_actual_span_and_no_ratio():
    path = Path("fea/results/lumber-leg-response/2x8-e300-m40-E7000.tar.gz")
    result = diagnostic.screen(path)
    with tarfile.open(path) as archive:
        inputs = json.load(archive.extractfile("input.json"))
    _, foot, along, _ = diagnostic.source.model.geometry("2x8", 300.)
    def station(n):
        return diagnostic.source.dot([inputs["nodes"][str(n)][i]-foot.toTuple()[i]
                                      for i in range(3)], along.toTuple())
    assert len(result["rows"]) == result["summary"]["case_leg_count"] == 1296
    assert result["summary"]["opposing_axial_force_cases"] == 3
    assert result["summary"]["missed_loaded_region_peak_cases"] == 1163
    witness = next(r for r in result["rows"] if r["stiffness"] == "k10000" and r["side"] == "left"
                   and r["case"]["hold"] == "A12" and r["case"]["climber_lb"] == 300
                   and r["case"]["weight_factor"] == 2 and r["case"]["horizontal_direction_deg"] == 90)
    assert witness["clear_total_moment_envelope_nmm"][0] == pytest.approx(55775.183393873)
    assert witness["through_loaded_region_envelope"]["absolute_total_bending_in_out_nmm"][0] == pytest.approx(67531.022006570)
    for side, span in result["span_candidates"].items():
        support = [n for name, p in inputs["points"].items()
                   if name.startswith(f"lumber_leg_bolt_{side}_")
                   for n, w in zip(p["gusset_nodes"], p["other_weights"], strict=True) if w != 0]
        lo = min(map(station, inputs["legs"][side]["floor_nodes"]))
        hi = max(map(station, support))
        assert span["lowest_floor_station_mm"] == lo
        assert span["highest_loaded_station_mm"] == hi
        assert span["unsupported_span_candidate_mm"] == hi-lo
        assert not span["restraints_physically_established"]
    assert not result["qualified_for_design"]
    assert not result["combined_member_strength_evaluated"]
    for row in result["rows"]:
        assert row["interaction_ratio"] is None
        assert row["status"] == "unassessed_NDS_end_load_mapping"
        assert row["maximum_below_group_moment_equivalence_error_nmm"] < .001
        a, b = row["clear_endpoint_decomposition"]
        assert a["axial_moment_xyz_nmm"] == pytest.approx(b["axial_moment_xyz_nmm"], abs=1e-6)
        assert a["eccentricity_xyz_mm"] == pytest.approx(b["eccentricity_xyz_mm"], abs=1e-6)
        for axis in range(2):
            assert row["same_case_clear_side_moment_envelope_nmm"][axis] == max(
                abs(a["side_bending_in_out_nmm"][axis]), abs(b["side_bending_in_out_nmm"][axis]))


@pytest.mark.parametrize("stock,missed,span", [("2x6", 1296, 1863.54164190765),
                                               ("2x8", 1295, 1870.229064359185)])
def test_completed_spread_archives_keep_mapping_unassessed(stock, missed, span):
    path = Path(f"fea/results/spread-leg-response/{stock}-e300-m40-E7000.tar.gz")
    result = diagnostic.screen(path)
    assert result["stock"] == stock and result["extension_mm"] == 300.
    assert result["geometry"] == "spread-100x50-top150"
    assert result["summary"] == {"case_leg_count": 1296, "opposing_axial_force_cases": 3,
                                 "missed_loaded_region_peak_cases": missed}
    for side in ("left", "right"):
        assert result["span_candidates"][side]["unsupported_span_candidate_mm"] == pytest.approx(span)
        assert not result["span_candidates"][side]["restraints_physically_established"]
    assert not result["combined_member_strength_evaluated"] and not result["qualified_for_design"]
    assert all(r["interaction_ratio"] is None and r["status"] == "unassessed_NDS_end_load_mapping"
               and r["maximum_below_group_moment_equivalence_error_nmm"] < .001 for r in result["rows"])
