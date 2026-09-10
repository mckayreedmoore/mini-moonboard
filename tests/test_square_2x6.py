"""Keep an inspectable failed baseline without hiding unqualified interfaces."""
import hashlib
import json
from pathlib import Path

import pytest

from fea import square_2x6_audit as audit
from mini_moonboard import square_2x6_frame as model


@pytest.fixture(scope='module')
def report():
    return audit.build()


def test_layout_constraints_and_recorded_failures(report):
    assert len(report['inventory']['single_2x6_members']) == 20
    assert report['inventory']['panel_kicker_screws'] == 56
    assert report['inventory']['bolts'] == 16
    assert report['inventory']['installed_inserts'] == 0
    assert report['principal_housing_removed']
    assert report['lower_rail_service_collisions'] == []
    assert report['wood_collisions'] == []
    assert report['future_insert_reserves']['passes_nominal_reserves']
    assert report['lower_panel_edge_overhang_mm'] == 40.
    assert not report['all_tested_geometry_gates_passed']
    assert not report['qualified_for_design'] and not report['structural_analysis_run']
    assert {r['gate'] for r in report['failures']} == {
        'receiver_material', 'rim_bolt_edge', 'incomplete_header_bearing'}
    support = {r['member']: r for r in report['header_support']}
    assert support['base_post_center_left_rear']['nominal_contact_area_fraction'] == 0.
    assert support['base_principal_left']['nominal_contact_area_fraction'] == pytest.approx(.73592285)


def test_lower_rails_are_whole_square_stock_and_principals_not_housed():
    parts = {p.name: p for p in model.wood_parts()}
    assert 'timber_bottom_backing' not in parts
    for side in model.UPRIGHTS:
        rail = parts[f'base_rail_bottom_{side}']
        assert rail.shape.Volume() == pytest.approx(rail.blank[0]*139.7*38.1)
        assert rail.laminations == 1
        principal = parts[f'base_principal_{side}']
        assert principal.shape.isInside(model.b.point(model.CENTERS[side], 40., 20.), 1e-6)
    assert not any(c.name.startswith('timber_backing_bolt_') for c in model.connections())


def test_audit_and_review_package_replay(report):
    saved = json.loads(Path('fea/results/square-2x6-audit-v1.json').read_text())
    assert {k: v for k, v in report.items() if k != 'source_sha256'} == {
        k: v for k, v in saved.items() if k != 'source_sha256'}
    for name, sha in report['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha
    directory = Path('exports/square-2x6-development')
    manifest = json.loads((directory/'manifest.json').read_text())
    assert not manifest['qualified_for_design']
    for name, sha in manifest['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha
    for name, sha in manifest['artifact_sha256'].items():
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == sha
    assert json.loads((directory/'geometry-audit.json').read_text()) == saved
    assert len((directory/'future-insert-reserves.csv').read_text().splitlines()) == 57
