"""Selective solid-stock changes resolve fit gates without claiming strength."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from fea import selective_2x6_audit as audit
from mini_moonboard import selective_2x6_frame as model


@pytest.fixture(scope='module')
def report():
    return audit.build()


def test_selective_stock_resolves_bearing_edges_and_reserves(report):
    inventory = report['inventory']
    assert len(inventory['single_2x6_members']) == 9
    assert len(inventory['single_3x6_members']) == 4
    assert inventory['single_2x10_members'] == ['base_header']
    assert inventory['wood_parts'] == 22
    assert inventory['panel_kicker_screws'] == 56
    assert inventory['installed_inserts'] == 0
    assert not report['failures'] and report['all_tested_geometry_gates_passed']
    assert not report['qualified_for_design'] and not report['structural_analysis_run']
    assert len(report['shared_seam_edge_checks']) == 28
    assert all(r['nominal_contact_area_fraction'] == pytest.approx(1.) for r in report['header_support'])
    assert report['shared_seam_margins']['repair_reserve_side_ligament_mm'] == pytest.approx(9.8044)
    assert report['future_insert_reserves']['reserve_count'] == 56
    for p in model.parts():
        assert p.shape.isValid() and len(p.shape.Solids()) == 1, p.name
    old = {p.name: p for p in model.previous.wood_parts()}
    for p in model.wood_parts():
        if p.name.startswith(('lumber_leg_', 'base_side_')):
            assert p.shape is old[p.name].shape


def test_published_audit_sources_and_artifacts(report):
    exported = Path('exports/selective-2x6-development')
    assert report == json.loads((exported/'geometry-audit.json').read_text())
    for directory in (exported, Path('site/hybrid/selective-2x6-development')):
        manifest = json.loads((directory/'manifest.json').read_text())
        for name, sha in manifest['artifact_sha256'].items():
            assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == sha
        for name, sha in manifest['source_sha256'].items():
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha


def test_floor_witnesses_balance_current_geometry_loads():
    report = json.loads(gzip.decompress(Path('fea/results/selective-floor-v1.json.gz').read_bytes()))
    assert report['candidate'] == model.KEY and report['case_count'] == 1296
    assert not report['qualified_for_design'] and not report['structural_analysis_run']
    assert len(report['mass_inventory']) == 192
    points = np.array(report['floor_vertices_mm'])
    checked = 0
    for case in report['cases']:
        for mu, result in case['friction_results'].items():
            if not result['polygon_feasible']:
                assert not result['circular_cone_infeasibility_proven']
                continue
            forces = np.array(result['point_forces_n'])
            residual = np.r_[forces.sum(axis=0), np.cross(points, forces).sum(axis=0)] + case['wrench_n_nmm']
            assert np.max(np.abs(residual[:3])) <= result['force_tolerance_n']
            assert np.max(np.abs(residual[3:])) <= result['moment_tolerance_nmm']
            assert np.min(forces[:, 2]) >= -result['force_tolerance_n']
            assert np.max(np.linalg.norm(forces[:, :2], axis=1)-float(mu)*forces[:, 2]) <= result['force_tolerance_n']
            checked += 1
    assert checked == report['witness_validation']['checked_feasible_witnesses'] > 0
