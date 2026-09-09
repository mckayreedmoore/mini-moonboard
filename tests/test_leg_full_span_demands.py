"""First-order cut-envelope regressions, not strength validation."""
import hashlib
import json
from pathlib import Path

import pytest

from fea import leg_full_span_demands as model


def peaks(points, forces, low=0.):
    return model.cut_peaks(points, forces, [0., 0., 0.], [0., 0., 1.], 0., low,
                           model.source.section(38.1, 139.7))


def test_loaded_region_recovers_cancelled_clear_strip_peak_and_wrench():
    result = peaks({1: [0., 0., 1.], 2: [0., 0., 2.], 3: [0., 0., 3.]},
                   {1: [100., 0., 0.], 2: [-200., 0., 0.], 3: [100., 0., 0.]})
    peak = result["bending_out_nmm"]
    assert peak["value"] == 100.
    assert peak["station_from_foot_mm"] == 2.
    assert peak["simultaneous_section"]["upper_load_moment_xyz_nmm"] == [0., 100., 0.]
    assert peak["simultaneous_section"]["upper_load_force_xyz_n"] == [100., 0., 0.]
    assert result["normal_compression_mpa"]["value"] > 0


@pytest.mark.parametrize("roundoff", [0., 1e-10, -1e-10])
def test_axial_jumps_and_negative_nodal_force(roundoff):
    result = peaks({1: [10., 0., 1.+roundoff], 2: [10., 0., 2.]},
                   {1: [0., 0., 100.], 2: [0., 0., -100.]})
    assert result["compression_n"]["value"] == 100
    assert result["bending_out_nmm"]["value"] == 1000
    assert result["bending_out_nmm"]["simultaneous_section"]["axial_n_tension_positive"] == -100


def test_simultaneous_biaxial_stress_and_torsion_are_not_discarded():
    result = peaks({1: [10., 20., 100.]}, {1: [30., 40., -1000.]})
    witness = result["normal_compression_mpa"]["simultaneous_section"]
    props = model.source.section(38.1, 139.7)
    expected = 1000/props["area_mm2"]+24000/props["in_plane_S_mm3"]+13000/props["out_of_plane_S_mm3"]
    assert result["normal_compression_mpa"]["value"] == pytest.approx(expected)
    assert witness["upper_load_moment_xyz_nmm"] == [-24000., 13000., -200.]
    assert result["torsion_nmm"]["value"] == 200


def test_near_equal_load_planes_do_not_create_a_spurious_jump():
    result = peaks({1: [10., 0., 1.], 2: [10., 0., 1.+1e-10]},
                   {1: [0., 0., 100.], 2: [0., 0., -100.]})
    assert result["bending_out_nmm"]["value"] == 0
    assert result["compression_n"]["value"] == 0


@pytest.mark.parametrize("extension", [0, 300])
def test_archive_retains_cases_stations_and_no_strength_verdict(extension):
    result = model.screen(f"fea/results/spread-leg-response/2x6-e{extension}-m40-E7000.tar.gz")
    saved = json.loads(Path(f"fea/results/leg-full-span-demands/2x6-e{extension}.json").read_text())
    assert result == saved
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha
               for p, sha in saved["reporting_source_sha256"].items())
    assert result["case_leg_count"] == 1296 and len(result["rows"]) == 12
    assert not result["qualified_for_design"] and not result["combined_strength_evaluated"]
    for row in result["rows"]:
        assert len(row["peaks"]) == 11
        for name, peak in row["peaks"].items():
            assert peak["case"]["climber_lb"] == row["climber_lb"]
            assert peak["side"] in ("left", "right")
            assert peak["station_from_foot_mm"] > 0
            assert model.measures(peak["simultaneous_section"])[name] == peak["value"]


def test_rejects_a_load_below_the_scanned_interval():
    with pytest.raises(ValueError, match="above"):
        peaks({1: [0., 0., 1.]}, {1: [0., 0., -1.]}, low=2.)
