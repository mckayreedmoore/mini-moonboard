"""Independently replay the insert mass inventory and saved floor witnesses."""
import gzip
import json

import numpy as np
import pytest

from fea import round_insert_floor as floor


def test_current_insert_mass_and_floor_witnesses():
    report = json.loads(gzip.decompress(floor.OUTPUT.read_bytes()))
    assert report['candidate'] == 'round-insert-development'
    assert report['source_sha256'] == floor.sources()
    assert not report['qualified_for_design'] and not report['electrical_mass_included']
    inventory = report['mass_inventory']
    assert len({row['name'] for row in inventory}) == len(inventory)
    inserts = [row for row in inventory if row['name'].startswith('insert_')]
    assert len(inserts) == 56 and all(row['density_kg_m3'] == 6700 for row in inserts)
    for row in inventory:
        assert row['mass_kg'] == pytest.approx(row['volume_mm3']*row['density_kg_m3']/1e9)
    mass = sum(row['mass_kg'] for row in inventory)
    centre = [sum(row['mass_kg']*row['centre_xyz_mm'][axis] for row in inventory)/mass
              for axis in range(3)]
    assert report['state']['mass_kg'] == pytest.approx(mass)
    assert report['state']['centre_xyz_mm'] == pytest.approx(centre)
    assert len(report['selected_floor_support_bodies']) == 6
    assert not any(row['name'].startswith('kicker_') for row in report['selected_floor_support_bodies'])
    expected = list(floor.cases(report['state'], floor.locations()))
    assert len(expected) == len(report['cases']) == report['case_count'] == 1296
    points = np.asarray(report['floor_vertices_mm'])
    count = 0
    for actual, regenerated in zip(report['cases'], expected, strict=True):
        assert {key: value for key, value in actual.items() if key != 'friction_results'} == regenerated
        wrench = np.asarray(actual['wrench_n_nmm'])
        for mu, result in actual['friction_results'].items():
            assert result['necessary_conditions'] == floor.necessary_conditions(points.tolist(), wrench.tolist(), float(mu))
            if not result['polygon_feasible']:
                continue
            count += 1
            forces = np.asarray(result['point_forces_n'])
            assert forces.shape == points.shape and np.isfinite(forces).all()
            residual = np.r_[forces.sum(axis=0), np.cross(points, forces).sum(axis=0)]+wrench
            assert max(abs(residual[:3])) <= result['force_tolerance_n']
            assert max(abs(residual[3:])) <= result['moment_tolerance_nmm']
            assert min(forces[:, 2]) >= -result['force_tolerance_n']
            assert max(np.linalg.norm(forces[:, :2], axis=1)-float(mu)*forces[:, 2]) <= result['force_tolerance_n']
    assert count == report['witness_validation']['checked_feasible_witnesses']
