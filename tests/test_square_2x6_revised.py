"""All-2x6 revision keeps the known bearing failure while correcting placements."""
import hashlib
import json
from pathlib import Path

import pytest

from fea import square_2x6_revised_audit as audit
from mini_moonboard import square_2x6_revised_frame as model


@pytest.fixture(scope='module')
def report():
    return audit.build()


def test_all_lumber_remains_single_2x6_and_only_bearing_gate_fails(report):
    assert len(report['inventory']['single_2x6_members']) == 18
    assert report['inventory']['wood_parts'] == 26
    assert report['inventory']['installed_inserts'] == 0
    assert report['inventory']['brackets'] == 20
    assert all(r['passed'] for r in report['receiver_checks'])
    assert all(r['passed'] for r in report['rim_edge_checks'])
    assert all(r['passes_4D_side_7D_top_screen'] for r in report['leg_edge_end_checks'])
    assert {f['gate'] for f in report['failures']} == {'incomplete_header_bearing'}
    assert len(report['failures']) == 4
    assert report['future_insert_reserves']['passes_nominal_reserves']
    assert not report['qualified_for_design'] and not report['all_tested_geometry_gates_passed']
    assert not report['structural_analysis_run']
    header = next(p for p in model.wood_parts() if p.name == 'base_header')
    assert header.blank[1:] == (139.7, 38.1)


def test_leg_outline_and_bottom_square_rails_preserved():
    current = {p.name: p for p in model.wood_parts()}
    old = {p.name: p for p in model.previous.wood_parts()}
    for name in ('lumber_leg_left', 'lumber_leg_right', 'base_rail_bottom_left', 'base_rail_bottom_right'):
        assert current[name].shape is old[name].shape
    assert not any(name.endswith('_rear') and name.startswith('base_post_center_') for name in current)
    assert not any(c.name.startswith('timber_backing_bolt_') for c in model.connections())


def test_published_audit_render_and_viewer_hashes(report):
    directory = Path('exports/square-2x6-revised-development')
    saved = json.loads((directory/'geometry-audit.json').read_text())
    assert report == saved
    for name, sha in report['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha
    manifest = json.loads((directory/'manifest.json').read_text())
    for name, sha in manifest['artifact_sha256'].items():
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == sha
    for key in ('square-2x6-development', model.KEY):
        viewer = Path('site/hybrid')/key
        manifest = json.loads((viewer/'manifest.json').read_text())
        assert not manifest['design']['qualified_for_design']
        for name, sha in manifest['source_sha256'].items():
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha
        for name, sha in manifest['artifact_sha256'].items():
            assert hashlib.sha256((viewer/name).read_bytes()).hexdigest() == sha
        parts = json.loads((viewer/'parts.json').read_text())['parts']
        assert len(parts) == (254 if key == 'square-2x6-development' else 238)
        assert not any(p['name'].startswith('insert_') for p in parts)
