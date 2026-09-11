"""Replay saved floor evidence without CAD integration or optimization solves."""
import gzip
import json
from collections import Counter
from itertools import product

import numpy as np
import pytest

from fea import horizontal_service_floor as screen
from fea.rigid_floor_screen import RAYS
from fea.timber_floor_screen import HOLDS, cases
from fea.wide_structural import locations


def test_kicker_edges_never_expand_credited_support():
    contacts = [{'name': name, 'vertices_mm': [[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]}
                for name in sorted(screen.SUPPORT_NAMES)]
    contacts.append({'name': 'kicker_left', 'vertices_mm': [[1000., 1000., 0.]]})
    selected = screen.select_floor_supports(contacts)
    assert len(selected) == 6
    assert screen.hull([p[:2] for row in selected for p in row['vertices_mm']]) == [(0., 0.), (1., 0.), (0., 1.)]
    with pytest.raises(ValueError, match='four post'):
        screen.select_floor_supports(contacts[1:])


def test_saved_horizontal_service_floor_evidence_replays():
    report = json.loads(gzip.decompress(screen.OUTPUT.read_bytes()))
    assert report['candidate'] == 'horizontal-service-development'
    assert report['qualified_for_design'] is False
    assert report['structural_analysis_run'] is False
    assert report['source_sha256'] == screen.sources()
    assert report['case_count'] == len(report['cases']) == 1296
    state, inventory = report['state'], report['mass_inventory']
    assert not any('gusset' in row['name'] for row in inventory)
    assert sum(row['name'].startswith('base_post_') for row in inventory) == 4
    assert not report['electrical_mass_included']
    assert not any(row['name'].startswith(('wire_', 'light_', 'led_')) for row in inventory)
    all_contacts = report['floor_contact_bodies']
    assert len(all_contacts) == 8
    assert {row['name'] for row in all_contacts if row['name'].startswith('kicker_')} == {'kicker_left', 'kicker_right'}
    assert [list(point) for point in screen.hull(
        [point[:2] for row in all_contacts for point in row['vertices_mm']])] == report['geometric_contact_hull_mm']
    contacts = report['selected_floor_support_bodies']
    assert contacts == screen.select_floor_supports(all_contacts)
    assert sum(row['name'].startswith('base_post_') for row in contacts) == 4
    assert sum(row['name'].startswith('lumber_leg_') for row in contacts) == 2
    assert len(contacts) == 6
    assert [list(point) for point in screen.hull(
        [point[:2] for row in contacts for point in row['vertices_mm']])] == state['support_polygon_mm']
    assert 'mini_moonboard/horizontal_service_frame.py' in report['source_sha256']
    assert 'fea/horizontal_service_floor.py' in report['source_sha256']
    assert len({row['name'] for row in inventory}) == len(inventory) == state['part_count']
    for row in inventory:
        assert row['density_kg_m3'] == (7850 if row['material'] == 'steel' else 600)
        assert row['material'] in ('steel', 'wood/plywood')
        assert np.isfinite([row['volume_mm3'], row['mass_kg'], *row['centre_xyz_mm']]).all()
        assert row['volume_mm3'] > 0 and row['mass_kg'] > 0
        assert row['mass_kg'] == pytest.approx(row['volume_mm3']*row['density_kg_m3']/1e9)
    total = sum(row['mass_kg'] for row in inventory)
    centre = np.array([sum(row['mass_kg']*row['centre_xyz_mm'][axis] for row in inventory)/total
                       for axis in range(3)])
    assert state['mass_kg'] == pytest.approx(total, abs=1e-9)
    assert state['centre_xyz_mm'] == pytest.approx(centre, abs=1e-8)
    assert state['centre_xy_mm'] == pytest.approx(centre[:2], abs=1e-8)
    points = np.asarray(report['floor_vertices_mm'])
    assert points.tolist() == [[x, y, 0.] for x, y in state['support_polygon_mm']]
    assert np.isfinite(points).all()

    identity_fields = ('climber_lb', 'weight_factor', 'mass_fraction', 'hold', 'horizontal_direction_deg')
    identities = [tuple(row[key] for key in identity_fields) for row in report['cases']]
    expected_identities = set(product((150, 200, 250, 300), (1, 2), (.8, 1.), HOLDS,
                                      (None, *range(0, 360, 45))))
    assert len(set(identities)) == 1296 and set(identities) == expected_identities
    regenerated = {tuple(row[key] for key in identity_fields): row for row in cases(state, locations())}
    assert set(regenerated) == expected_identities
    statuses = {str(mu): Counter() for mu in screen.FRICTION}
    reasons = {str(mu): Counter() for mu in screen.FRICTION}
    proven, uncertain = Counter(), Counter()
    witnesses = []
    for saved, identity in zip(report['cases'], identities, strict=True):
        assert set(saved) == set(regenerated[identity]) | {'friction_results'}
        wrench = np.asarray(saved['wrench_n_nmm'])
        assert wrench == pytest.approx(regenerated[identity]['wrench_n_nmm'], abs=1e-8)
        assert set(saved['friction_results']) == {'0.1', '0.2', '0.4'}
        for key, result in saved['friction_results'].items():
            mu = float(key)
            necessary = screen.necessary_conditions(points.tolist(), wrench.tolist(), mu)
            assert result['necessary_conditions'] == necessary
            assert result['circular_cone_infeasibility_proven'] is necessary['circular_cone_infeasibility_proven']
            assert result['status'] in ('feasible', 'infeasible')
            assert result['polygon_feasible'] is (result['status'] == 'feasible')
            statuses[key][result['status']] += 1
            proven[key] += necessary['circular_cone_infeasibility_proven']
            reasons[key].update(necessary['failure_reasons'])
            uncertain[key] += not result['polygon_feasible'] and not necessary['circular_cone_infeasibility_proven']
            if not result['polygon_feasible']:
                assert 'point_forces_n' not in result
                continue
            assert not necessary['circular_cone_infeasibility_proven']
            forces = np.asarray(result['point_forces_n'])
            assert forces.shape == points.shape and np.isfinite(forces).all()
            residual = np.r_[forces.sum(axis=0), np.cross(points, forces).sum(axis=0)]+wrench
            force_tolerance = 1e-7*max(1., max(abs(wrench[:3])))
            moment_tolerance = 1e-7*max(1000., max(abs(wrench[3:])),
                                       np.max(abs(points))*max(1., max(abs(wrench[:3]))))
            assert result['force_tolerance_n'] == pytest.approx(force_tolerance)
            assert result['moment_tolerance_nmm'] == pytest.approx(moment_tolerance)
            assert max(abs(residual[:3])) <= force_tolerance
            assert max(abs(residual[3:])) <= moment_tolerance
            assert result['residual_wrench'] == pytest.approx(residual, abs=1e-8)
            normals = forces[:, 2]
            excess = np.linalg.norm(forces[:, :2], axis=1)-mu*normals
            assert min(normals) >= -force_tolerance and max(excess) <= force_tolerance
            # Confirm the claimed inscribed-polygon witness, not only circular friction.
            angles = (np.arange(RAYS)+.5)*2*np.pi/RAYS
            sides = np.column_stack((np.cos(angles), np.sin(angles)))
            assert np.max(forces[:, :2] @ sides.T-
                          mu*normals[:, None]*np.cos(np.pi/RAYS)) <= force_tolerance
            assert result['minimum_normal_force_n'] == pytest.approx(min(normals), abs=1e-8)
            assert result['maximum_friction_excess_n'] == pytest.approx(max(excess), abs=1e-8)
            witnesses.append((max(abs(residual[:3])), max(abs(residual[3:])), min(normals), max(excess)))
    expected_summary = {key: {**dict(statuses[key]), 'circular_cone_infeasibility_proven': proven[key],
                              'polygon_infeasible_without_analytic_proof': uncertain[key],
                              'analytic_failure_reasons': dict(reasons[key])} for key in statuses}
    assert report['summary'] == expected_summary
    measured = report['witness_validation']
    assert measured['checked_feasible_witnesses'] == len(witnesses)
    for column, key, function in ((0, 'maximum_force_residual_n', max),
                                  (1, 'maximum_moment_residual_nmm', max),
                                  (2, 'minimum_normal_force_n', min),
                                  (3, 'maximum_friction_excess_n', max)):
        if witnesses:
            assert measured[key] == pytest.approx(function(row[column] for row in witnesses), abs=1e-8)
        else:
            assert measured[key] is None
