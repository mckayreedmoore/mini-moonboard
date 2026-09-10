"""Reject unmodified stock substitutions; do not turn geometry into approval."""
import hashlib
import json
from pathlib import Path

import pytest

from fea import single_2x6_screen as screen
from mini_moonboard import screw_mvp_frame as model


@pytest.fixture(scope='module')
def report():
    return screen.build()


def test_actual_cad_substitutions_fail_before_solver(report):
    assert report['hardware'] == {'panel_kicker_wood_screws': 56, 'threaded_inserts': 0,
                                  'frame_bolts': 18, 'bracket_screws': 108}
    variants = report['variants']
    assert variants['baseline']['passes_tested_direct_substitution_gates']
    for name in screen.VARIANTS[1:]:
        assert not variants[name]['passes_tested_direct_substitution_gates']
        assert not variants[name]['structural_analysis_run']
        assert not variants[name]['qualified_for_design']
    rim = next(e for e in variants['rims']['bolt_edge_checks']
               if e['connection'] == 'lumber_leg_bolt_left_3')
    assert rim['minimum_transverse_edge_mm'] == pytest.approx(6.62769159)
    backing = next(e for e in variants['principals']['bolt_edge_checks']
                   if e['connection'] == 'timber_backing_bolt_left')
    assert backing['minimum_transverse_edge_mm'] == pytest.approx(19.05)
    assert backing['existing_reversible_4D_screen_mm'] == pytest.approx(38.1)


def test_saved_screen_replays(report):
    saved = json.loads(Path('fea/results/single-2x6-screw-screen.json').read_text())
    assert {k: v for k, v in report.items() if k != 'source_sha256'} == {
        k: v for k, v in saved.items() if k != 'source_sha256'}
    for name, sha in saved['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha


def test_screw_candidate_has_no_insert_bodies_or_insert_display_bores():
    parts = {p.name: p for p in model.parts()}
    assert len(parts) == 45
    assert not any(name.startswith('insert_') for name in parts)
    assert all(p.shape.isValid() and len(p.shape.Solids()) == 1 for p in parts.values())
    for c in model.connections():
        if not isinstance(c, model.wide.timber.PanelScrew):
            continue
        # A point beyond the screw radius but within the old insert envelope
        # remains wood: no future insert pilot has been predrilled.
        entry = c.start+c.direction*model.wide.PANEL
        across = model.cq.Vector(1., 0., 0.)
        assert parts[c.members[1]].shape.isInside(entry+c.direction*5+across*3., 1e-6)
