"""Analytical wrench checks and accepted-archive demand replay, not approval."""
import json
import math
import tarfile
from pathlib import Path

import pytest

from fea import lumber_leg_resistance as resistance


def test_concentric_and_eccentric_upper_free_body():
    props = resistance.section(38.1, 184.15)
    result = resistance.section_demand({"bolt": [19.05, 0., 100.]},
        {"bolt": [10., 20., -1000.]}, [0., 0., 0.], [0., 0., 1.], [0., 1., 0.], props)
    assert result["axial_n_tension_positive"] == -1000
    assert result["upper_load_moment_xyz_nmm"] == pytest.approx([-2000., 20050., 381.])
    assert result["bending_in_out_plane_nmm"] == [-2000., 20050.]
    assert result["torsion_nmm"] == 381
    spread = 2000/props["in_plane_S_mm3"]+20050/props["out_of_plane_S_mm3"]
    assert result["normal_stress_extrema_mpa_tension_positive"] == pytest.approx(
        [-1000/props["area_mm2"]-spread, -1000/props["area_mm2"]+spread])


def test_wrench_transport_and_common_translation():
    props = resistance.section(38.1, 139.7)
    p, f = {"a": [3., 4., 50.]}, {"a": [10., 20., 30.]}
    a = resistance.section_demand(p, f, [0., 0., 0.], [0., 0., 1.], [0., 1., 0.], props)
    b = resistance.section_demand(p, f, [0., 0., 10.], [0., 0., 1.], [0., 1., 0.], props)
    assert b["upper_load_moment_xyz_nmm"] == pytest.approx(
        [x-y for x, y in zip(a["upper_load_moment_xyz_nmm"], resistance.cross([0., 0., 10.], f["a"]), strict=True)])
    shifted = resistance.section_demand({"a": [103., 204., 350.]}, f,
        [100., 200., 300.], [0., 0., 1.], [0., 1., 0.], props)
    assert shifted["upper_load_moment_xyz_nmm"] == a["upper_load_moment_xyz_nmm"]


@pytest.mark.parametrize("size,cfb,cfc", [("2x6", 1.3, 1.1), ("2x8", 1.2, 1.05),
                                         ("2x10", 1.1, 1.), ("2x12", 1., 1.)])
def test_nds_column_reference_independent_quadratic(size, cfb, cfc):
    result = resistance.column_reference(size, 1700.)
    q = min(result["FcE_mpa"].values())/result["Fc_star_mpa"]
    cp = (1+q)/1.6-math.sqrt(((1+q)/1.6)**2-q/.8)
    assert result["Cp"] == pytest.approx(cp)
    assert result["Fb_size_only_mpa"] == pytest.approx(900*cfb*resistance.PSI_MPA)
    assert result["Fc_star_mpa"] == pytest.approx(1350*cfc*resistance.PSI_MPA)
    assert result["reference_concentric_compression_n"] == pytest.approx(
        result["Fc_star_mpa"]*cp*38.1*resistance.model.WIDTHS[size])
    assert not resistance.column_reference(size, 2000.)["within_slenderness_limit"]
    assert resistance.column_reference(size, 2000.)["reference_concentric_compression_n"] is None


def test_actual_two_sawn_members_not_old_bonded_plywood():
    result = resistance.bolt_reference()
    assert result["governing_mode"] == "II"
    assert result["reference_lateral_n"] == pytest.approx(668.034058285)
    assert result["inputs"]["main_bearing_lb_in"] == result["inputs"]["side_bearing_lb_in"]
    assert not result["steel_and_thread_geometry_qualified"]


def test_native_screen_retains_all_common_cases_and_eccentricities():
    path = Path("fea/results/lumber-leg-response/2x8-e0-m40-E7000.tar.gz")
    result = resistance.screen(path)
    with tarfile.open(path) as archive:
        inputs = json.load(archive.extractfile("input.json"))
    _, foot, along, _ = resistance.model.geometry("2x8", 0.)
    load_stations = {side: [resistance.dot(
        [inputs["nodes"][str(node)][i]-foot.toTuple()[i] for i in range(3)], along.toTuple())
        for name, point in inputs["points"].items() if name.startswith(f"lumber_leg_bolt_{side}_")
        for node, weight in zip(point["gusset_nodes"], point["other_weights"], strict=True) if weight != 0]
        for side in ("left", "right")}
    assert len(result["rows"]) == 648
    assert not result["qualified_for_design"] and not result["combined_strength_evaluated"]
    for row in result["rows"]:
        assert len(row["bolts"]) == 8
        assert row["case"]["climber_lb"] in (150, 200, 250, 300)
        for side, sections in row["sections"].items():
            assert len(sections) == 2
            assert sections[0]["station_from_foot_mm"] < sections[1]["station_from_foot_mm"]
            assert sections[1]["station_from_foot_mm"] < min(load_stations[side])
            assert abs(sections[0]["origin_xyz_mm"][0]) == 1238.25
            forces = [b["force_xyz_n"] for n, b in row["bolts"].items() if f"_{side}_" in n]
            expected = [math.fsum(f[i] for f in forces) for i in range(3)]
            assert sections[0]["upper_load_force_xyz_n"] == expected
            assert sections[1]["upper_load_force_xyz_n"] == expected


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        resistance.column_reference("2x8", float("nan"))
    with pytest.raises(ValueError):
        resistance.section_demand({"a": [0., 0., 0.]}, {"b": [0., 0., 0.]},
            [0., 0., 0.], [0., 0., 1.], [0., 1., 0.], resistance.section(38.1, 139.7))
