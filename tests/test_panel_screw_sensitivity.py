import copy
import json
from pathlib import Path

import numpy as np
import pytest

from fea import horizontal_panel_frame as frame
from fea import panel_screw_sensitivity as sensitivity


def test_partial_cell_load_preserves_rigid_virtual_work_and_signed_shape():
    nodes, elements, _ = frame.panel_kernel.grid([0., 10.], [0., 20.])
    patch = (1., 4., 3., 8.)
    weights = sensitivity.patch_weights(nodes, elements.values(), patch)
    assert sum(weights.values()) == pytest.approx(1.)
    assert sum(nodes[n][0]*w for n, w in weights.items()) == pytest.approx(2.5)
    assert sum(nodes[n][1]*w for n, w in weights.items()) == pytest.approx(5.5)
    assert min(weights.values()) < 0.
    full = sensitivity.patch_weights(nodes, elements.values(), (0., 10., 0., 20.))
    reference, _ = frame.panel_kernel.pressure_load(nodes, elements, (0., 10., 0., 20.), 1.)
    assert full == pytest.approx(reference)
    with pytest.raises(ValueError, match='entirely'):
        sensitivity.patch_weights(nodes, elements.values(), (-1., 10., 0., 20.))


@pytest.fixture(scope='module')
def frozen():
    root = Path('fea/generated/horizontal-frame-batch-v2/f10-k1000')
    if not root.exists():
        pytest.skip('Local archived expanded native evidence unavailable')
    report = json.loads((root/'report.json').read_text())
    return json.loads((root/report['final_cycle_directory']/'input.json').read_text())


def test_deletion_changes_only_panel_spring_triplets(frozen):
    before = copy.deepcopy(frozen)
    name = 'infill_main_upper_left_base_principal_center_left_3_1'
    full = sensitivity.restore(frozen)
    reduced = sensitivity.restore(frozen, [name])
    assert frozen == before
    assert len(full.elements)-len(reduced.elements) == 3
    assert len(full.springs)-len(reduced.springs) == 3
    for attr in ('nodes', 'loads', 'equations', 'fixed', 'members', 'panels', 'rotation_masters'):
        assert getattr(full, attr) == getattr(reduced, attr)
    assert {n for ids in reduced.groups.values() for n in ids} == reduced.elements.keys()
    for name in ('missing', 'clip_single_top_left_1_beam_1'):
        with pytest.raises(ValueError):
            sensitivity.restore(frozen, [name])


def test_mirrored_patch_preserves_gravity_and_reflects_wrench(frozen):
    result = sensitivity.mirror_load(frozen)
    coords = {int(n): np.array(p) for n, p in result['nodes'].items()}
    field = result['panel_load']
    f = np.array(field['forces_xyz_n'])
    xyz = np.array([coords[n] for n in field['nodes']])
    assert f.sum(axis=0) == pytest.approx(result['force_xyz_n'], abs=1e-8)
    assert np.cross(xyz-result['target_xyz_mm'], f).sum(axis=0) == pytest.approx(
        result['moment_at_panel_midplane_nmm'], abs=1e-7)
    assert result['target_xyz_mm'][0] == -frozen['target_xyz_mm'][0]
    assert result['force_xyz_n'] == pytest.approx(np.array(frozen['force_xyz_n'])*[-1., 1., 1.])
    assert result['moment_at_panel_midplane_nmm'] == pytest.approx(
        np.array(frozen['moment_at_panel_midplane_nmm'])*[1., -1., -1.])
    def gravity(r):
        loads = {int(n): np.array(f) for n, f in r['loads'].items()}
        for n, f in zip(r['panel_load']['nodes'], r['panel_load']['forces_xyz_n'], strict=True):
            loads[n] -= f
        return loads
    old, new = gravity(frozen), gravity(result)
    for n in old.keys() | new.keys():
        assert old.get(n, np.zeros(3)) == pytest.approx(new.get(n, np.zeros(3)), abs=1e-10)
    assert result['nodes'] == frozen['nodes']
    assert result['elements'] == frozen['elements']
    assert not result['qualified_for_design']


def test_authenticated_parent_reproduces_exact_native_deck(frozen):
    record, provenance = sensitivity.authenticated_input('fea/generated/horizontal-frame-batch-v2/f10-k1000')
    assert record == frozen
    assert len(provenance['input_sha256']) == 64
