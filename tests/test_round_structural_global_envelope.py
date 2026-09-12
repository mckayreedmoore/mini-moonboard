"""Current geometry mapping and independently recovered rigid-body moments."""
import json
import math
from pathlib import Path

import pytest

from fea.round_structural_global_envelope import locations, sources
from fea.user_load_envelope import GRAVITY, envelope

RESULT = Path('fea/results/round-structural-global-envelope-v1.json')


def test_current_load_points_use_current_panel_faces():
    from mini_moonboard import round_structural_frame as model

    points = locations(model)
    normal = model.b.normal()
    origin = model.b.point(0., 0., 0.)
    for name, point, outward in points:
        if name.startswith('kicker_'):
            assert point[1] == pytest.approx(model.base.HEADER_FRONT_Y+model.wide.PANEL)
            assert point[2] == pytest.approx(150.)
            assert outward == (0., 1., 0.)
        else:
            depth = sum((p-o)*n for p, o, n in
                        zip(point, origin.toTuple(), normal.toTuple(), strict=True))
            assert depth == pytest.approx(-model.wide.PANEL)
            assert sum(a*b for a, b in zip(outward, normal.toTuple(), strict=True)) == pytest.approx(-1.)


def test_saved_envelope_replays_current_hold_mapping_and_sources():
    from mini_moonboard import round_structural_frame as model

    report = json.loads(RESULT.read_text())
    current = sources()
    recorded = report['source_sha256']
    assert recorded == {path: current[path] for path in recorded}
    # The broad source collector also discovers new, separate candidate files.
    # Their addition must not relabel or overwrite unchanged historical CAD
    # evidence. Every original source still requires an exact byte match.
    assert set(current)-set(recorded) <= {
        'mini_moonboard/hold_tnut_reinforcement.py',
        'mini_moonboard/kicker_header_reinforcement.py',
        'mini_moonboard/round_reinforcement_frame.py',
        'mini_moonboard/steel_base_reinforcement.py',
    }
    replay = envelope(report['state'], locations(model), weights=(250, 300))
    # JSON normalization converts saved vertex tuples to arrays.
    assert report['cases'] == json.loads(json.dumps(replay))
    assert not report['qualified_for_design']
    assert not report['internal_connection_demands_evaluated']
    assert not report['floor_qualification']


def test_all_saved_edge_moments_balance_independently():
    report = json.loads(RESULT.read_text())
    state = report['state']
    support_names = {r['name'] for r in report['selected_floor_support_bodies']}
    assert len(support_names) == 6
    assert not any('kicker' in name for name in support_names)
    for case in report['cases']:
        for edge in case['edges']:
            a, b = edge['vertices_mm']
            length = math.dist(a, b)
            # Moment projected onto the edge tangent: cross(r,F).dot(tangent).
            tangent = ((b[0]-a[0])/length, (b[1]-a[1])/length)

            def moment(point, force, a=a, tangent=tangent):
                rx, ry, rz = point[0]-a[0], point[1]-a[1], point[2]
                fx, fy, fz = force
                return (ry*fz-rz*fy)*tangent[0]+(rz*fx-rx*fz)*tangent[1]

            dead = moment(state['centre_xyz_mm'],
                          (0., 0., -state['mass_kg']*case['mass_scale']*GRAVITY))
            direction = edge['horizontal_direction_xy']
            live = moment(edge['load_position_mm'],
                          (direction[0]*case['horizontal_n'],
                           direction[1]*case['horizontal_n'], -case['downward_n']))
            assert dead == pytest.approx(-edge['dead_restoring_nmm'])
            assert live == pytest.approx(-edge['live_signed_restoring_nmm'])
            assert -(dead+live) == pytest.approx(edge['net_restoring_nmm'])
