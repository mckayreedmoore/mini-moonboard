"""Unsupported load directions cannot silently acquire angle capacity."""
import hashlib
import json
from pathlib import Path

import pytest

from fea import angle_base_connection_screen as screen


@pytest.mark.parametrize('sign', [-1., 1.])
def test_mirrored_outer_angles_have_same_local_limits(sign):
    u, v = [sign, 0., 0.], [0., 0., 1.]
    outward = screen.assess([-sign*1000, 0., 0.], [0., 0., 0.], u, v)
    inward = screen.assess([sign*1000, 0., 0.], [0., 0., 0.], u, v)
    assert outward['component_references'][0]['direction'] == 'F3'
    assert inward['component_references'][0]['direction'] == 'F4'
    assert outward['conditional_single_direction_within_reference']
    assert not outward['qualified_for_design']
    excessive = screen.assess([-sign*3000, 0., 0.], [0., 0., 0.], u, v)
    assert not excessive['conditional_single_direction_within_reference']


@pytest.mark.parametrize('force,moment', [([0, 0, 1], [0, 0, 0]), ([0, 0, -1], [0, 0, 0]),
                                         ([1, 1, 0], [0, 0, 0]), ([1, 0, 0], [0, 1, 0])])
def test_unlisted_uplift_bearing_mixed_axis_and_moment_fail_closed(force, moment):
    result = screen.assess(force, moment, [1, 0, 0], [0, 0, 1])
    assert result['conditional_single_direction_within_reference'] is None
    assert result['unassessed_reasons']
    assert not result['qualified_for_design']


@pytest.fixture(scope='module')
def current_report():
    return screen.build()


def test_current_angles_are_identified_without_inventing_demands(current_report):
    result = current_report
    assert len(result['angles']) == 2
    assert all(len(r['single_axis_1000n_probes']) == 6 for r in result['angles'])
    assert result['conditional_single_direction_reference_n']['F1'] == pytest.approx(2646.69186108)
    assert not result['current_frame_forces_available'] and not result['joint_strength_passed']
    assert not result['qualified_for_design'] and not result['frame_solve_run']


def test_published_directional_screen_replays_with_authenticated_sources(current_report):
    saved = json.loads(Path('fea/results/angle-base-connection-screen-v1.json').read_text())
    for name, digest in saved['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
    # The package-wide source glob grows with unrelated later variants. Retain
    # every authenticated historical input and compare all engineering output.
    assert saved['source_sha256'].items() <= current_report['source_sha256'].items()
    assert {k: v for k, v in saved.items() if k != 'source_sha256'} == {
        k: v for k, v in current_report.items() if k != 'source_sha256'
    }
    for flag in ('qualified_for_design', 'joint_strength_passed', 'current_frame_forces_available', 'frame_solve_run'):
        assert saved[flag] is False
    assert all(not probe['qualified_for_design'] and not probe['actual_installation_approved']
               for row in saved['angles'] for probe in row['single_axis_1000n_probes'])
