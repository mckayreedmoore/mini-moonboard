"""The alternative drilling must fit both component axes and stay independent."""
import pytest

from fea.compact_thick_checks import layout_check
from mini_moonboard import compact_2x12_leg_frame as original
from mini_moonboard import compact_2x12_staggered_frame as model


def test_staggered_group_satisfies_both_component_layouts():
    points = [point.toTuple() for point in model.bolt_points()]
    for grain, width in ((model.axes()[2], 38.1), (model.axes()[4], 88.9)):
        result = layout_check(points, {'grain': grain.toTuple(), 'width_mm': width}, 12.7)
        assert result['component_spacing_screen_passed']
        assert result['noncollinear']
        assert result['cross_grain_spread_mm'] + 2 < 127
        assert result['minimum_component_spacing_margin_mm'] > 2
    unchanged = layout_check([point.toTuple() for point in original.bolt_points()],
                             {'grain': original.axes()[2].toTuple(), 'width_mm': 38.1}, 12.7)
    assert not unchanged['component_spacing_screen_passed']


def test_only_bolt_centers_change_and_tips_remain_outward():
    points = model.bolt_points()
    old = {connection.name: connection for connection in original.connections()}
    bolts = [connection for connection in model.connections() if connection.kind == 'bolt']
    assert len(bolts) == 8
    for connection in model.connections():
        baseline = old[connection.name]
        if connection.kind != 'bolt':
            assert connection is baseline
            continue
        point = points[int(connection.name.rsplit('_', 1)[1]) - 1]
        assert connection.start.y == pytest.approx(point.y)
        assert connection.start.z == pytest.approx(point.z)
        assert connection.start.x == baseline.start.x
        assert connection.direction == baseline.direction
        assert connection.grip == baseline.grip
        assert connection.members == baseline.members
        assert connection.direction.x == (-1 if 'left' in connection.name else 1)


@pytest.mark.parametrize('case, ratio, layout_pass', [
    ('row-a12-rear', 1.9489773998, False),
    ('staggered-a12-rear', 2.0789714800, True),
])
def test_preserved_fresh_cases_fail_connection_resistance(case, ratio, layout_pass):
    import gzip
    import hashlib
    import json
    from pathlib import Path

    from scripts.compact_2x12_results import check

    directory = Path(__file__).resolve().parents[1] / 'fea/results/compact-2x12-study' / case
    manifest = json.loads((directory / 'manifest.json').read_text())
    for name, sha in manifest['files'].items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == sha
    report = json.loads(gzip.decompress((directory / 'report.json.gz').read_bytes()))
    geometry = json.loads((directory / 'geometry.json').read_text())
    result = check(report, geometry)
    assert result['status'] == 'DESIGN_SHORTFALL'
    assert not result['qualified_for_design']
    assert not result['criteria']['actual_angle_lateral']
    assert result['criteria']['layout'] is layout_pass
    assert result['metrics']['actual_angle_lateral'] == pytest.approx(ratio)
    assert result['criteria']['receiver_fit']
