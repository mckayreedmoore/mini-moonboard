import json
import tarfile
from pathlib import Path

import numpy as np
import pytest

from fea import panel_load_sensitivity as load


@pytest.fixture(scope='module')
def record():
    published = Path('fea/results/round-frame-batch-v1.tar.gz')
    if published.exists():
        with tarfile.open(published, 'r:gz') as archive:
            report = json.load(archive.extractfile('f10-k1000/report.json'))
            return json.load(archive.extractfile('f10-k1000/'+report['final_cycle_directory']+'/input.json'))
    root = Path('fea/generated/horizontal-frame-batch-v2/f10-k1000')
    if not root.exists():
        pytest.skip('Local expanded native evidence unavailable')
    report = json.loads((root/'report.json').read_text())
    return json.loads((root/report['final_cycle_directory']/'input.json').read_text())


def test_original_assumptions_recover_identical_hold_load_and_gravity(record):
    result = load.change_load(record)
    before = {int(n): np.array(f) for n, f in record['loads'].items()}
    after = {int(n): np.array(f) for n, f in result['loads'].items()}
    for n in before.keys() | after.keys():
        assert before.get(n, np.zeros(3)) == pytest.approx(after.get(n, np.zeros(3)), abs=1e-7)
    for key in ('nodes', 'elements', 'springs', 'equations', 'fixed_nodes'):
        assert result[key] == record[key]


@pytest.mark.parametrize('values', [(1., 300., 100.), (2., 0., 100.), (2., 300., 0.), (2., 300., 50.)])
def test_each_scenario_preserves_gravity_and_target_wrench(record, values):
    result = load.change_load(record, *values)
    target = np.array(result['target_xyz_mm'])
    coords = {int(n): np.array(x) for n, x in result['nodes'].items()}
    tags, forces = result['panel_load']['nodes'], np.array(result['panel_load']['forces_xyz_n'])
    assert forces.sum(axis=0) == pytest.approx(result['force_xyz_n'], abs=1e-8)
    assert np.cross(np.array([coords[n] for n in tags])-target, forces).sum(axis=0) == pytest.approx(
        result['moment_at_panel_midplane_nmm'], abs=1e-7)
    gravity = []
    for r in (record, result):
        residual = {int(n): np.array(f) for n, f in r['loads'].items()}
        for n, f in zip(r['panel_load']['nodes'], r['panel_load']['forces_xyz_n'], strict=True):
            residual[n] -= f
        gravity.append(residual)
    for n in gravity[0].keys() | gravity[1].keys():
        assert gravity[0].get(n, np.zeros(3)) == pytest.approx(gravity[1].get(n, np.zeros(3)), abs=1e-9)
    assert result['force_xyz_n'][1] == values[1]
    assert result['force_xyz_n'][2] == pytest.approx(-values[0]*250*.45359237*9.80665)
    assert result['load_assumption_scenario']['standoff_mm'] == values[2]
    assert not result['qualified_for_design']
    assert not result['load_assumption_scenario']['measured_or_qualified']
    if values[2] == 0.:
        assert np.linalg.norm(result['moment_at_panel_midplane_nmm']) > 0.  # Front face differs from midsurface.
