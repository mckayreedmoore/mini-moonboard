import json
from pathlib import Path

import numpy as np
import pytest

from fea.mortar_geometry_diagnostic import (
    FIELDS,
    contact_blocks,
    diagnostic,
    project_bilinear,
    triangle_weights,
)


def frd():
    return '\n'.join(['  100CL  101 1.00000E+00         1', ' -4  CONTACT     6    1',
                      *[' -5  '+field for field in FIELDS],
                      f' -1{7:10d}'+''.join(f'{v:12.5E}' for v in (1., -2., 3.)),
                      ' -2'+' '*10+''.join(f'{v:12.5E}' for v in (4., -5., 6.)), ' -3'])


def test_frd_fixed_width_adjacent_signs_and_continuation():
    assert contact_blocks(frd()) == {1.: {7: [1., -2., 3., 4., -5., 6.]}}


@pytest.mark.parametrize('mutation', ['duplicate', 'truncated', 'missing', 'nonfinite', 'labels'])
def test_frd_fails_closed(mutation):
    data = frd()
    if mutation == 'duplicate':
        data += '\n'+data
    elif mutation == 'truncated':
        data = data.rsplit('\n', 1)[0]
    elif mutation == 'missing':
        data = data.replace('         1\n', '         2\n')
    elif mutation == 'nonfinite':
        data = data.replace(' 1.00000E+00', '         NaN')
    else:
        data = data.replace('CPRESS', 'WRONG')
    with pytest.raises(ValueError):
        contact_blocks(data)


def test_projection_flat_and_warped_master_not_mean_z():
    flat = np.array([[-1., -1., 0.], [1., -1., 0.], [1., 1., 0.], [-1., 1., 0.]])
    gap, _, error = project_bilinear([[0., 0., -.2], [.5, -.5, .1]], flat)
    assert gap == pytest.approx([-.2, .1])
    assert error < 1e-12
    # Bilinear z=.2*s*t; create point exactly0.1 along its local normal.
    warped = flat.copy()
    warped[:, 2] = .2*flat[:, 0]*flat[:, 1]
    s, t = .4, -.3
    normal = np.array([-.2*t, -.2*s, 1.])
    normal /= np.linalg.norm(normal)
    point = np.array([s, t, .2*s*t])+.1*normal
    gap, uv, _ = project_bilinear([point], warped)
    assert gap == pytest.approx([.1])
    assert uv[0] == pytest.approx([s, t])
    assert point[2] != pytest.approx(.1)


@pytest.mark.parametrize('master,point', [([[0, 0, 0]]*4, [0, 0, 0]),
    ([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]], [2, 0, .1]),
    ([[-1, -1, 0], [-1, 1, 0], [1, 1, 0], [1, -1, 0]], [0, 0, .1])])
def test_projection_rejects_degenerate_escaped_reversed(master, point):
    with pytest.raises(ValueError):
        project_bilinear([point], master)


def test_quadratic_sampling_finds_below_nodal_minimum():
    bary, weights = triangle_weights(8)
    assert weights.sum(axis=1) == pytest.approx(np.ones(len(bary)))
    # Along one edge, endpoints0,2 and midpoint0 yield minimum below zero.
    z = weights@np.array([0., 2., 0., 0., 1., 0.])
    assert min(z) < 0


@pytest.mark.parametrize('division', [True, 0, 3, 2.5])
def test_sampling_rejects_bad_divisions(division):
    with pytest.raises(ValueError):
        triangle_weights(division)


def test_published_finest_archive_coverage_and_quadratic_gap_replay():
    from fea.full_frame_refinement import digest, read_archive

    root = Path('fea/results/full_frame_refinement')
    published = json.loads((root/'report.json').read_text())['runs']['0.0625']
    path = root/published['archive']
    assert digest(path.read_bytes()) == published['archive_sha256']
    files = read_archive(path)
    assert {name: digest(raw) for name, raw in files.items()} == published['archive_contents_sha256']
    result = diagnostic(files)
    assert len(result['accepted_contact_times']) == 32
    assert result['slave_node_count'] == 610
    loaded = result['endpoints'][1]['patches']
    assert loaded['LEFT']['quadratic_face_samples'][-1]['gap_mm'][0] == pytest.approx(-.0003630510665, abs=1e-10)
    assert loaded['LEFT']['quadratic_face_samples'][-1]['gap_mm'][0] < loaded['LEFT']['nodal_geometric_gap_mm'][0]
    # This is transformed nodal output, NOT an internal Coulomb-law failure.
    assert loaded['KICKER']['displayed_excess_above_representation_bound_count_NOT_law_violations'] == 15
    assert loaded['LEFT']['displayed_excess_above_representation_bound_count_NOT_law_violations'] == 0
    assert 'NOT VALIDATED' in result['status']
    files['frame.frd'] += b'changed'
    with pytest.raises(ValueError, match='digest'):
        diagnostic(files)


@pytest.mark.parametrize('increment', ['0.125', '0.0625'])
def test_published_diagnostic_report_is_bound_and_fully_replays(increment):
    from fea.full_frame_refinement import digest, read_archive

    root = Path('fea/results/full_frame_refinement')
    source_report = (root/'report.json').read_bytes()
    published = json.loads(Path('fea/results/mortar_geometry_diagnostic/report.json').read_text())
    assert published['source_report_sha256'] == digest(source_report)
    assert published['diagnostic_source_sha256'] == digest(Path('fea/mortar_geometry_diagnostic.py').read_bytes())
    assert set(published['runs']) == set(published['archive_sha256']) == {'0.125', '0.0625'}
    item = json.loads(source_report)['runs'][increment]
    archive = root/item['archive']
    assert digest(archive.read_bytes()) == item['archive_sha256'] == published['archive_sha256'][increment]
    files = read_archive(archive)
    assert {name: digest(raw) for name, raw in files.items()} == item['archive_contents_sha256']
    # JSON normalization turns tuple face IDs into the stored arrays; compare
    # every result, including coverage, geometry, precision bounds and caveats.
    assert published['runs'][increment] == json.loads(json.dumps(diagnostic(files)))
