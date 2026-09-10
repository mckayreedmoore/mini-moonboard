"""Check assembled single-member layout, not merely each board's stock size."""
import hashlib
import json
from pathlib import Path

import pytest

from fea import single_2x6_audit as audit
from mini_moonboard import single_2x6_frame as model
from mini_moonboard import square_2x6_revised_frame as previous


@pytest.fixture(scope='module')
def report():
    return audit.build()


def test_touching_parallel_check_catches_old_paired_seam_rails():
    pairs = audit.touching_parallel_lumber({p.name: p for p in previous.wood_parts()})
    assert {frozenset(p['members']) for p in pairs} == {
        frozenset((f'base_rail_mid_lower_{side}', f'base_rail_mid_upper_{side}'))
        for side in ('left', 'right')}


def test_single_layout_and_remaining_failures(report):
    parts = {p.name: p for p in model.wood_parts()}
    assert len(report['inventory']['single_2x6_members']) == 14
    assert len(parts) == 22
    assert [n for n in parts if n.startswith('base_principal_')] == ['base_principal_center']
    assert [n for n in parts if n.startswith('base_post_center')] == ['base_post_center']
    assert sorted(n for n in parts if n.startswith('base_rail_mid_')) == [
        'base_rail_mid_left', 'base_rail_mid_right']
    assert not report['touching_parallel_lumber']
    assert not report['lower_rail_service_collisions']
    assert not report['shared_framing_service_collisions']
    assert report['future_insert_reserves']['passes_nominal_reserves']
    assert report['future_insert_reserves']['reserve_count'] == 56
    assert report['shared_seam_margins']['repair_reserve_side_ligament_mm'] == pytest.approx(3.4544)
    assert sum(r['gate'] == 'incomplete_header_bearing' for r in report['failures']) == 3
    assert sum(r['gate'] == 'shared_seam_screw_edge_screen' for r in report['failures']) == 28
    assert {r['gate'] for r in report['failures']} == {
        'incomplete_header_bearing', 'shared_seam_screw_edge_screen'}
    assert not report['qualified_for_design'] and not report['structural_analysis_run']
    for p in model.parts():
        assert p.shape.isValid() and len(p.shape.Solids()) == 1, p.name
    assert report['principal_housing_removed']


def test_published_candidate_matches_audit_and_artifacts(report):
    exported = Path('exports/single-2x6-development')
    assert report == json.loads((exported/'geometry-audit.json').read_text())
    for directory in (exported, Path('site/hybrid/single-2x6-development')):
        manifest = json.loads((directory/'manifest.json').read_text())
        for name, sha in manifest['artifact_sha256'].items():
            assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == sha
        for name, sha in manifest['source_sha256'].items():
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha
