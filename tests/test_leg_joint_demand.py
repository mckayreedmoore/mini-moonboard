import csv
import hashlib
import json
import math
import re

import numpy as np
import pytest

from fea.leg_joint_demand import (
    ARCHIVE,
    ARCHIVE_SHA,
    GRAVITY_PER_MM3_N,
    assemble_endpoints,
    free_body,
    local_components,
    read_archive,
    replay,
    select_leg,
    sha,
    validate_weights,
    verify_deck,
)


def test_free_body_sign_couple_deformed_gravity_and_reference():
    nodes = {1: (0., 2., 3.)}
    weights = {1: 10/GRAVITY_PER_MM3_N}
    displacement = {1: (1., 2., 0.)}
    supports = {2: (-1., 0., 0.), 3: (1., 0., 0.)}
    forces = {2: (0., 3., 20.), 3: (0., -3., 20.)}
    result = free_body(nodes, weights, displacement, supports, forces, (0., 0., 0.), 1.)
    assert result['leg_on_rim_force_moment'] == pytest.approx([0, 0, 30, -40, 10, -6])
    assert result['rim_on_leg_force_moment'] == pytest.approx([0, 0, -30, 40, -10, 6])
    moved = free_body(nodes, weights, displacement, supports, forces, (0., 2., 0.), 1.)
    assert moved['leg_on_rim_force_moment'] == pytest.approx([0, 0, 30, -100, 10, -6])
    half = free_body(nodes, weights, displacement, supports, forces, (0., 0., 0.), .5)
    assert half['gravity_force_moment'] == pytest.approx([0, 0, -5, -20, 5, 0])


def test_all_ten_nodes_and_cad_membership_control_ownership():
    nodes = {n: (1.5, n/10, 0.) for n in range(1, 11)}
    elements = {1: list(nodes)}
    assert select_leg(nodes, elements, 1, 1, 2, lambda p: True) == elements
    nodes[10] = (.5, 0., 0.)
    with pytest.raises(ValueError, match='crosses'):
        select_leg(nodes, elements, 1, 1, 2, lambda p: True)
    nodes[10] = (1.5, 0., 0.)
    with pytest.raises(ValueError, match='leaves'):
        select_leg(nodes, elements, 1, 1, 2, lambda p: p[1] != 0)
    with pytest.raises(ValueError, match='Missing'):
        select_leg(nodes, elements, -1, 1, 2, lambda p: True)


def test_output_coverage_and_nonfinite_rejected():
    values = ({1: (0., 0., 0.)}, {1: 1.}, {1: (0., 0., 0.)},
              {2: (0., 0., 0.)}, {2: (0., 0., 1.)}, (0., 0., 0.), 1.)
    for index in range(5):
        broken = list(values)
        broken[index] = {}
        with pytest.raises(ValueError, match='coverage'):
            free_body(*broken)
    broken = list(values)
    broken[4] = {2: (0., 0., math.nan)}
    with pytest.raises(ValueError, match='Nonfinite'):
        free_body(*broken)


def test_signed_consistent_weights_and_geometry_gates():
    nodes = {1: (0., 0., 0.), 2: (1., 0., 0.)}
    weights = {1: -.1, 2: 1.1}
    cad = {'volume_mm3': 1., 'centre_mm': [1.1, 0, 0]}
    assert validate_weights(nodes, weights, cad)['negative_weight_count'] == 1
    with pytest.raises(ValueError, match='volume/CG'):
        validate_weights(nodes, weights, {**cad, 'volume_mm3': 2})
    with pytest.raises(ValueError, match='Incomplete'):
        validate_weights(nodes, {1: 1}, cad)
    assert local_components([1, 2, 3, 4, 5, 6], [(1, 0, 0), (0, 0, 1), (0, -1, 0)]) == [1, 3, -2, 4, 6, -5]
    with pytest.raises(ValueError, match='basis'):
        local_components([1]*6, [(1, 0, 0), (0, 1, 0), (0, 0, -1)])


def test_portable_retained_dat_to_report_all_increments():
    """Authenticate frozen evidence and exercise the same assembly as production."""
    path = 'fea/results/leg_joint_demand/successful.tar.gz'
    assert sha(path) == '44babcb9329b5e6cc87c4946a76dad241ea779de73f8d79502569120d3190e43'
    retained = {name.removeprefix('./'): data for name, data in read_archive(path).items()}
    def digest(data):
        return hashlib.sha256(data).hexdigest()
    assert digest(retained['report.json']) == '6c09595cccfb5f58e44a3f20035fd60c41f82d6a0a702b85f4ac83a4b8c06c49'
    report = json.loads(retained['report.json'])
    info = json.loads(retained['input.json'])
    integration = json.loads(retained['integration.json'])
    assert digest(retained['input.json']) == report['input_sha256'] == integration['input_sha256']
    assert digest(retained['integration.json']) == report['integration_sha256']
    assert digest(retained['integration.log']) == report['integration_log_sha256']
    for name, expected in info['source_sha256'].items():
        assert digest(retained['launch_sources/'+name]) == expected
    assert sha(ARCHIVE) == ARCHIVE_SHA == info['archive_sha256'] == report['archive_sha256']
    files = read_archive(ARCHIVE)
    assert {name: digest(data) for name, data in files.items()} == info['archive_members_sha256']
    record = json.loads(files['frame.json'])
    nodes, _, _, ground, bottom = verify_deck(files['frame.inp'].decode(), record)
    baseline = replay(files)
    data = files['frame.dat'].decode()
    actual = assemble_endpoints(data, nodes, ground, bottom, baseline, info['legs'], integration)
    # Exact nested equality covers every six-component vector, both signs,
    # floor/gravity terms, local transforms, times and flags for both legs.
    assert actual == report['endpoints']
    assert [row['time'] for row in actual] == [n/16 for n in range(1, 33)]
    assert [row['time'] for row in actual if not row['baseline_global_gate_pass']] == [
        1.0625, 1.125, 1.1875, 1.25, 1.3125, 1.75, 1.8125]
    for row in actual:
        assert set(row['legs']) == {'left', 'right'}
        for leg in row['legs'].values():
            assert len(leg) == 5
            assert all(len(vector) == 6 and all(map(math.isfinite, vector)) for vector in leg.values())

    # Delete a node from the FIRST accepted timber output, not the final case.
    # Hash authentication above is deliberately outside this mutation probe so
    # the production coverage guard, rather than a digest mismatch, must catch it.
    damaged, count = re.subn(r'(displacements[^\n]*for set WOODN[^\n]*\n\s*\n)[^\n]+\n',
                             r'\1', data, count=1)
    assert count == 1 and damaged != data
    with pytest.raises(ValueError, match='Incomplete timber output'):
        assemble_endpoints(damaged, nodes, ground, bottom, baseline, info['legs'], integration)


def test_collinear_upper_bolt_points_cannot_supply_uphill_axis_moment():
    """Point-force model limitation, not a physical connection capacity test."""
    retained = {name.removeprefix('./'): data for name, data in
                read_archive('fea/results/leg_joint_demand/successful.tar.gz').items()}
    info, report = (json.loads(retained[name]) for name in ('input.json', 'report.json'))
    with open('exports/screw-spacing-development/screw-spacing-development_connections.csv') as stream:
        connections = list(csv.DictReader(stream))
    def resultant_map(positions):
        moments = np.hstack([np.column_stack([np.cross(r, axis) for axis in np.eye(3)])
                             for r in positions])
        return np.vstack((np.tile(np.eye(3), (1, len(positions))), moments))
    endpoint = report['endpoints'][-1]
    assert endpoint['time'] == 2 and endpoint['baseline_global_gate_pass']
    for side in ('left', 'right'):
        leg = info['legs'][side]
        reference, axes = np.array(leg['reference_mm']), np.array(leg['local_axes_world'])
        group = [c for c in connections if c['connection'].startswith('analysis_leg_wall_bolt_'+side+'_')]
        assert len(group) == 4
        # CSV X is the bolt start, not its point on the rim/leg interface.
        points = np.array([[reference[0], float(c['y_mm']), float(c['z_mm'])] for c in group])
        local = (points-reference) @ axes.T
        np.testing.assert_allclose(local, [[0, s, 0] for s in (-140, -60, 60, 140)], atol=1e-9)
        matrix = resultant_map(local/1000)  # N and N*m, not mixed mm/m moments.
        assert np.linalg.matrix_rank(matrix, tol=1e-10) == 5
        demand = np.array(endpoint['legs'][side]['leg_on_rim_local_force_moment'])
        demand[3:] /= 1000
        forces = np.linalg.lstsq(matrix, demand, rcond=None)[0]
        np.testing.assert_allclose(demand-matrix@forces, [0, 0, 0, 0, demand[4], 0], atol=1e-9)
        assert abs(demand[4]) > 10  # Requires mechanics beyond four point forces.
    # Synthetic noncollinear control; NOT a selected or fit-checked bolt layout.
    rectangle = np.array([[0, s, n] for s in (-.14, .14) for n in (-.04, .04)])
    assert np.linalg.matrix_rank(resultant_map(rectangle), tol=1e-10) == 6
