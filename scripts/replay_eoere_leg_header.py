"""Replay captured combined-frame operators, joining the plywood metadata.

No equilibrium solve or acceptance transfer. The original reader still checks
every owner/map; the two explicit material annotations are authenticated from
the separately bound plywood input before that exact comparison.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy.linalg import block_diag

from scripts import eoere_current_response as response
from scripts.eoere_current_shop_followup import ROOT, module, require, sha
from scripts.eoere_leg_header_mechanics import MATERIAL, TRIAL


def replay_captured_sources(field_path, out):
    field = json.loads(field_path.read_bytes())
    material = json.loads((ROOT/MATERIAL).read_bytes())
    require(field['source_inputs']['plywood_material'] == {'path': str(MATERIAL), 'sha256': sha(ROOT/MATERIAL)},
            'exact constitutive input binding required')
    b = response.load('bridge').frozen()
    snapshot = b.bundle.read_snapshot(field['operator_bundle'])
    properties = material['properties']
    maps_class = b.base.OwnedMaps
    diagnostics = []
    for name in ('eoere_cleat_left', 'eoere_cleat_right'):
        row = snapshot.coordinate_map['timber'][name]
        source = next(r for r in field['source_inputs']['timber_rows'] if r['name'] == name)
        annotated = copy.deepcopy(source)
        annotated['explicit_plywood_operator'] = properties
        require(row['source'] == annotated, 'exact geometry/material annotation join required')
        index, stations = np.asarray(row['index']), np.asarray(row['stations'])
        rotation = np.array([source[k] for k in ('axis', 'section_u', 'section_v')])
        transform = block_diag(rotation, rotation/1000., rotation, rotation/1000.)
        expected = np.zeros((index.size, index.size))
        for i, length in enumerate(np.diff(stations)):
            local = np.zeros((12, 12))
            for ids, stiffness in (((0, 6), properties['EA_N']/length), ((3, 9), properties['GJ_Nmm2']/length)):
                local[np.ix_(ids, ids)] = stiffness*np.array([[1., -1.], [-1., 1.]])
            for ids, ei, ga, signs in (((1, 5, 7, 11), properties['EI_z_Nmm2'], properties['GA_u_N'], [1, 1, 1, 1]),
                                      ((2, 4, 8, 10), properties['EI_y_Nmm2'], properties['GA_v_N'], [1, -1, 1, -1])):
                phi = 12*ei/(properties['shear_factor']*ga*length**2)
                matrix = np.array([[12, 6*length, -12, 6*length],
                    [6*length, (4+phi)*length**2, -6*length, (2-phi)*length**2],
                    [-12, -6*length, 12, -6*length],
                    [6*length, (2-phi)*length**2, -6*length, (4+phi)*length**2]])
                signs = np.asarray(signs)
                local[np.ix_(ids, ids)] = ei/(length**3*(1+phi))*matrix*signs[:, None]*signs[None, :]
            section = np.arange(6*i, 6*i+12)
            expected[np.ix_(section, section)] += transform.T@local@transform
        actual = snapshot.assembly.K[index.ravel()][:, index.ravel()].toarray()
        error = float(abs(expected-actual).max())
        require(error < 1e-6 and np.allclose(actual, expected, rtol=1e-10, atol=1e-6), 'captured plywood K differs')
        diagnostics.append({'member': name, 'dofs': index.size, 'maximum_K_entry_error': error})

    def joined_maps(saved, data):
        amended = copy.deepcopy(data)
        for row in amended['timber_rows']:
            if row['name'] in ('eoere_cleat_left', 'eoere_cleat_right'):
                row['explicit_plywood_operator'] = copy.deepcopy(properties)
        return maps_class(saved, amended)

    trial = module(TRIAL/'replay_mechanics.py', 'leg_header_independent_operator_reader')
    # Authenticate the exact launcher captured before the source-only lint
    # annotations; never relabel an old field as a new launcher execution.
    input_ref = field['source_input_review']['input']
    require(sha(ROOT/input_ref['path']) == input_ref['sha256'], 'frozen source input differs')
    snapshot_path = (ROOT/input_ref['path']).parent/'producer-snapshot.py'
    launcher = ROOT/'scripts/eoere_leg_header_mechanics.py'
    original_sha = trial.sha
    require(original_sha(snapshot_path) == field['source_sha256']['scripts/eoere_leg_header_mechanics.py'],
            'exact captured numerical launcher required')

    def captured_source_sha(path):
        return original_sha(snapshot_path if Path(path).resolve() == launcher else path)

    with patch.object(b.base, 'OwnedMaps', joined_maps), patch.object(trial, 'sha', captured_source_sha):
        trial.replay(field_path, out)
    companion = out.with_name(out.stem+'-plywood.json')
    with companion.open('x') as stream:
        json.dump({'schema': 'eoere_leg_header_plywood_raw_operator_audit/v1',
            'field': {'path': str(field_path.relative_to(ROOT)), 'sha256': sha(field_path)},
            'material': {'path': str(MATERIAL), 'sha256': sha(ROOT/MATERIAL)},
            'source': {'path': str(Path(__file__).resolve().relative_to(ROOT)), 'sha256': sha(__file__)},
            'raw_operator_checks': diagnostics, 'all_unchanged_owner_map_checks_retained': True,
            'captured_launcher': {'path': str(snapshot_path.relative_to(ROOT)), 'sha256': original_sha(snapshot_path)},
            'field_q_actions_or_operators_changed': False, 'physical_stiffness_qualified': False,
            'production_admission_issued': False}, stream, indent=2, sort_keys=True)
        stream.write('\n')


def replay(field_path, out):
    field = json.loads(field_path.read_bytes())
    reference = field['source_input_review']['input']
    captured = (ROOT/reference['path']).parent/'producer-snapshot.py'
    require(sha(ROOT/reference['path']) == reference['sha256'] and
            sha(captured) == field['source_sha256']['scripts/eoere_leg_header_mechanics.py'],
            'authenticated captured source required before operator loading')
    b = response.load('bridge').frozen()
    original = b.factory.frame.sha

    def captured_sha(path):
        target = captured if Path(path).resolve() == ROOT/'scripts/eoere_leg_header_mechanics.py' else path
        return original(target)

    with patch.object(b.factory.frame, 'sha', captured_sha):
        replay_captured_sources(field_path, out)


if __name__ == '__main__':
    replay(*(Path(p).resolve() for p in sys.argv[1:3]))
