"""Independent equilibrium and boundary controls for the unadopted cleat tie."""
import hashlib
import json
import math
import subprocess
import sys
from xml.etree import ElementTree

import pytest

from scripts.eoere_cleat_tie_proposal import (
    PACKET,
    ROOT,
    drawing,
    normal_trial,
    overlapping,
)


@pytest.mark.parametrize("wrench", [
    [100., 2., 3., 40., 0., 0.],
    [-100., 0., 0., 0., 0., 0.],
    [0., 0., 0., 0., 1000., 0.],
    [0., 0., 0., 0., 0., -1000.],
    [26., -639., 51., -75100., 10767., 2169.],
    [26., 639., -51., 75100., -10767., -2169.],
    [0., 1., 2., 3., 0., 0.],
])
def test_force_and_cross_product_moments(wrench):
    origin, tie = 278.7, 260.
    result = normal_trial(wrench, origin, tie)
    actions = [(0., tie, result["assigned_tie_tension_n"])] + [
        (p["x_offset_mm"], p["z_mm"], -p["compression_n"])
        for p in result["compression_patches"]]
    # Direct r x F in global XYZ, independent of the production formulas.
    fy = sum(force for _, _, force in actions)
    mx = sum(-(z-origin)*force for _, z, force in actions)
    mz = sum(x*force for x, _, force in actions)
    assert (fy, mz, mx) == pytest.approx((wrench[0], wrench[4], wrench[5]), abs=1e-8)
    assert min(p["compression_n"] for p in result["compression_patches"]) >= 0
    assert result["unallocated_Z_X_shear_and_Y_torque"] == wrench[1:4]
    assert result["physical_tie_load_upper_bound_or_complete_capacity"] is None


def test_origin_transport_does_not_change_physical_allocation():
    first = normal_trial([26., 0., 0., 0., 10767., 2169.], 278.7, 260.)
    second = normal_trial([26., 0., 0., 0., 10767., 2169.-100.*26.], 178.7, 260.)
    assert first["assigned_tie_tension_n"] == pytest.approx(second["assigned_tie_tension_n"])
    for a, b in zip(first["compression_patches"], second["compression_patches"], strict=True):
        assert a == pytest.approx(b)


@pytest.mark.parametrize("kwargs", [{"centroid_fraction": 0}, {"centroid_fraction": 1},
                                   {"half_x": 0}, {"patch_area": -1}, {"tie_z": math.nan}])
def test_invalid_geometry_rejects(kwargs):
    values = {"origin_z": 278.7, "tie_z": 260., **kwargs}
    with pytest.raises(ValueError):
        normal_trial([1., 0., 0., 0., 2., 3.], **values)


def test_nonfinite_or_incomplete_wrenches_reject():
    for q in ([1., 2.], [0., 0., 0., math.inf, 0., 0.]):
        with pytest.raises(ValueError):
            normal_trial(q, 278.7, 260.)


def test_collision_screen_keeps_touching_and_overlapping_boxes():
    box = [0., 1., 0., 1., 0., 1.]
    assert overlapping(box, box)
    assert overlapping(box, [1., 2., 0., 1., 0., 1.])
    assert not overlapping(box, [1.001, 2., 0., 1., 0., 1.])


def test_cli_preserves_existing_result(tmp_path):
    target = tmp_path/'existing.json'
    target.write_text('original bytes')
    call = subprocess.run([sys.executable, '-m', 'scripts.eoere_cleat_tie_proposal',
                           '--out', str(target)], cwd=ROOT, capture_output=True, text=True, check=False)
    assert call.returncode != 0
    assert 'preserve existing results' in call.stderr
    assert target.read_text() == 'original bytes'


def test_recorded_proposal_arithmetic_and_scope():
    path = PACKET/'result.json'
    result = json.loads(path.read_text())
    assert len(result['normal_allocations']) == 24
    assert len({(r['case_id'], r['member']) for r in result['normal_allocations']}) == 12
    assert result['adopted'] is False and result['complete_resistance'] is None
    assert not result['structural_acceptance'] and not result['physical_demand_bound_established']
    assert not any(result['release'].values())
    assert result['all_new_nominal_envelopes_clear']
    assert len(result['envelope_checks']) == 24
    for row in result['normal_allocations']:
        expected = normal_trial(row['source_wrench_n_nmm'], 278.6710471933452, 260.)
        assert row['assigned_tie_tension_n'] == pytest.approx(expected['assigned_tie_tension_n'])
        actions = [(0., 260., row['assigned_tie_tension_n'])] + [
            (p['x_offset_mm'], p['z_mm'], -p['compression_n']) for p in row['compression_patches']]
        recovered = (sum(f for _, _, f in actions), sum(x*f for x, _, f in actions),
                     sum(-(z-278.6710471933452)*f for _, z, f in actions))
        assert recovered == pytest.approx([row['source_wrench_n_nmm'][i] for i in (0, 4, 5)], abs=1e-7)
    assert hashlib.sha256((ROOT/result['inputs']['path']).read_bytes()).hexdigest() == result['inputs']['sha256']
    for name, digest in result['source_bindings']['additional_sources'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest
    svg = drawing(result)
    ElementTree.fromstring(svg)
    assert 'UNADOPTED PROPOSAL' in svg and 'Shear, torque' in svg
