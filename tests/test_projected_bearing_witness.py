"""Known-answer controls for the anisotropic projected-bearing witness."""

import pytest

from mini_moonboard import projected_bearing_witness as method
from scripts import eoere_joint_vector_tests as existing


def surface(interval, force, first_moment, *, cap=1.0, grain=(1.0, 0.0), region_id="uniform"):
    return {"interval": list(interval), "force": list(force), "first_moment": list(first_moment),
            "regions": [{"id": region_id, "interval": list(interval),
                         "grain_parallel": list(grain), "cap_parallel_n_per_mm": cap,
                         "cap_perpendicular_n_per_mm": cap}]}


def couple_case():
    surfaces = [surface([0., 1.], [1., 0.], [0., 0.]),
                surface([1., 2.], [-1., 0.], [0., 0.])]
    points = [{"s": 2., "force": [0., 0.], "couple": [0., 1.]}]
    caps = [{"interval": [0., 2.], "cap": 100.}]
    return surfaces, points, [0., 2.], caps


def test_equal_isotropic_caps_match_existing_vector_lp_and_preserve_couple():
    surfaces, points, domain, caps = couple_case()
    legacy_surfaces = [{k: v for k, v in s.items() if k != "regions"} | {"cap": 1.} for s in surfaces]
    legacy = existing.solve(legacy_surfaces, points, domain, caps, cells=2, facets=16)
    result = method.solve(surfaces, points, domain, caps, cells=2, facets=16)
    check = method.verify_witness(surfaces, points, domain, caps, result, cells=2)
    assert result["certified_raw_reference_index"] == pytest.approx(legacy["certified_raw_reference_index"], abs=1e-8)
    assert result["certified_raw_reference_index"] == pytest.approx(1.0)
    assert check["maximum_member_first_moment_error_nmm"] < 1e-10
    assert check["end_moment_error_nmm"] < 1e-8
    assert result["physical_compatibility"] is False


def test_grain_rotation_changes_directional_ellipse_cap():
    surfaces = [surface([0., 1.], [1., 0.], [0., 0.], cap=1.0, grain=(1., 0.), region_id="parallel"),
                surface([1., 2.], [-1., 0.], [0., 0.], cap=1.0, grain=(0., 1.), region_id="perpendicular")]
    surfaces[0]["regions"][0]["cap_perpendicular_n_per_mm"] = 2.0
    surfaces[1]["regions"][0]["cap_perpendicular_n_per_mm"] = 2.0
    points = [{"s": 2., "force": [0., 0.], "couple": [0., 1.]}]
    caps = [{"interval": [0., 2.], "cap": 100.}]
    result = method.solve(surfaces, points, [0., 2.], caps, cells=2)
    check = method.verify_witness(surfaces, points, [0., 2.], caps, result, cells=2)
    assert check["maximum_ellipse_index"] == pytest.approx(1.0, abs=1e-8)
    assert max(c["ellipse_utilization"] for c in result["cells"] if c["region_id"] == "parallel") == pytest.approx(1.0)
    assert max(c["ellipse_utilization"] for c in result["cells"] if c["region_id"] == "perpendicular") == pytest.approx(.5)


def test_root_region_split_applies_local_cap_while_receiver_wrench_stays_aggregate():
    surfaces, points, domain, caps = couple_case()
    surfaces[1]["regions"] = [
        {"id": "body", "interval": [1., 1.5], "grain_parallel": [1., 0.],
         "cap_parallel_n_per_mm": 1., "cap_perpendicular_n_per_mm": 1.},
        {"id": "root", "interval": [1.5, 2.], "grain_parallel": [1., 0.],
         "cap_parallel_n_per_mm": .5, "cap_perpendicular_n_per_mm": .5},
    ]
    result = method.solve(surfaces, points, domain, caps, cells=2)
    check = method.verify_witness(surfaces, points, domain, caps, result, cells=2)
    assert {c["region_id"] for c in result["cells"]} == {"uniform", "body", "root"}
    assert check["maximum_member_force_error_n"] < 1e-10
    assert check["maximum_member_first_moment_error_nmm"] < 1e-10
    assert check["maximum_ellipse_index"] == pytest.approx(2.0, abs=1e-8)


def test_continuous_interior_bending_peak_and_signed_couple_match_existing_control():
    surfaces = [surface([0., 10.], [10., 0.], [0., 0.]),
                surface([10., 11.], [0., 0.], [0., 0.])]
    points = [{"s": 0., "force": [-7., 0.], "couple": [0., 0.]},
              {"s": 10., "force": [-3., 0.], "couple": [0., -20.]}]
    caps = [{"interval": [0., 11.], "cap": 1.}]
    result = method.solve(surfaces, points, [0., 11.], caps, cells=2, facets=16)
    check = method.verify_witness(surfaces, points, [0., 11.], caps, result, cells=2)
    assert result["continuous_raw_bending_index"] == pytest.approx(24.5, rel=1e-8)
    worst = max(result["continuous_segments"], key=lambda s: s["raw_index"])
    assert worst["maximum_bending"]["station_mm"] == pytest.approx(7.0, abs=1e-6)
    assert check["end_force_error_n"] < 1e-8
    assert check["end_moment_error_nmm"] < 1e-8


@pytest.mark.parametrize("bad", ["grain", "gap", "cap"])
def test_invalid_cap_region_inputs_fail_closed(bad):
    surfaces, points, domain, caps = couple_case()
    if bad == "grain":
        surfaces[0]["regions"][0]["grain_parallel"] = [2., 0.]
    elif bad == "gap":
        surfaces[0]["regions"][0]["interval"] = [.1, 1.]
    else:
        surfaces[0]["regions"][0]["cap_parallel_n_per_mm"] = 0.
    with pytest.raises(ValueError):
        method.solve(surfaces, points, domain, caps, cells=2)
