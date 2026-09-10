"""Current screw product geometry must not become a joint-strength pass."""
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import cadquery as cq
import pytest

from fea import selective_connection_strength as screen


def test_bevel_entry_section_does_not_use_global_bounding_box():
    shape = cq.Workplane('XZ').polyline([(0, 0), (100, 0), (100, 100)]).close().extrude(20).val()
    ends, _ = screen.boundary_distances(shape, cq.Vector(75, -10, 50), cq.Vector(1, 0, 0))
    assert ends == pytest.approx([25, 25])


def test_spacing_checks_same_receiver_and_grain():
    screw = next(c for c in screen.model.connections()
                 if isinstance(c, screen.model.timber.PanelScrew) and c.members[1] == 'base_post_center')
    d = json.loads(screen.REFERENCE.read_text())['spax']['table_19_mm']
    near = replace(screw, name='near', start=screw.start+cq.Vector(0, 0, 30))
    row = screen.spacing_checks([screw, near], d)[0]
    assert row['rule'] == 'same_row_parallel' and not row['passed']
    far = replace(near, start=screw.start+cq.Vector(0, 0, 45))
    assert screen.spacing_checks([screw, far], d)[0]['passed']
    other = replace(near, members=(near.members[0], 'base_post_outer_left'))
    assert screen.spacing_checks([screw, other], d) == []


def test_current_product_screen_retains_end_failure_and_no_strength_pass():
    result = screen.build()
    assert len(result['panel_kicker_screws']) == 56
    kicker = next(r for r in result['panel_kicker_screws'] if r['connection'] == 'timber_kicker_right_0_2')
    assert min(kicker['end_distances_mm']) == pytest.approx(26.9)
    assert not kicker['passes_end_away_or_perpendicular']
    upper = next(r for r in result['panel_kicker_screws'] if r['connection'] == 'timber_panel_upper_right_2')
    assert min(upper['end_distances_mm']) == pytest.approx(41.9)
    assert not upper['passes_reversible_end']
    assert not result['all_tested_product_geometry_gates_passed']
    assert not result['qualified_for_design'] and not result['joint_strength_passed']
    assert not result['current_connection_demands_available']
    assert len(result['leg_bolt_stacks']) == 8
    assert result['conditional_leg_single_fastener_reference']['reference_lateral_n'] == pytest.approx(668.0340582853437)
    assert result['recommended_kicker_axis']['resulting_post_top_distance_mm'] > 44.45
    assert 'fea/dowel_yield.py' in result['source_sha256']
    saved = json.loads(Path('fea/results/selective-connection-strength-v1.json').read_text())
    result = json.loads(json.dumps(result))  # JSON represents interval tuples as arrays.
    assert {k: v for k, v in saved.items() if k != 'source_sha256'} == {
        k: v for k, v in result.items() if k != 'source_sha256'}
    for name, sha in saved['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha
