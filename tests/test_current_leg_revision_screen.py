"""Independent kernel and physical-face checks for the exploratory joint screen."""
import json
from pathlib import Path

import numpy as np
import pytest

from fea import current_leg_revision_screen as screen
from fea.current_leg_revision_screen import LEG, PROFILES, RIM, capacity, loads
from fea.dowel_yield import single_shear


@pytest.mark.parametrize('diameter', [.375, .5, .625])
def test_vector_capacity_matches_scalar_yield_kernel(diameter):
    forces = np.array([[0., 100., 0.], [0., 0., -200.], [30., -450., 1900.]])
    actual = capacity(forces, diameter)
    for force, value in zip(forces, actual, strict=True):
        bearing = []
        for grain in (RIM, LEG):
            cosine2 = (force @ grain / np.linalg.norm(force[1:]))**2
            perpendicular = 6100 * .5**1.45 / np.sqrt(diameter)
            bearing.append(diameter * 5600 * perpendicular /
                           (5600 * (1-cosine2) + perpendicular * cosine2))
        reference = single_shear(
            main_length_in=1.5, side_length_in=1.5,
            main_bearing_lb_in=bearing[0], side_bearing_lb_in=bearing[1],
            main_yield_moment_lb_in=45000 * diameter**3 / 6,
            side_yield_moment_lb_in=45000 * diameter**3 / 6, gap_in=0,
            reduction_terms={'Im': 5., 'Is': 5., 'II': 4.5,
                             'IIIm': 4., 'IIIs': 4., 'IV': 4.})
        assert value == pytest.approx(reference['reference_lateral_lbf'] * 4.4482216152605)


@pytest.mark.parametrize('candidate,accepted', [('historical', True),
                                               ('no-shoes-development', False)])
def test_invalid_native_evidence_is_rejected(tmp_path, monkeypatch, candidate, accepted):
    source = tmp_path / 'invalid.json'
    source.write_text(json.dumps({'candidate': candidate,
                                  'cases': [{'numerically_accepted': accepted}]}))
    monkeypatch.setattr(screen, 'SOURCE', source)
    with pytest.raises(ValueError):
        screen.loads()


def test_saved_trial_centers_remain_inside_actual_fixed_front_plane():
    # Read actual current stock vertices, independently of the search's centered
    # rim-coordinate formula. Widening must retain this front plane exactly.
    profiles = json.loads(PROFILES.read_text())
    front_normal = np.array([0., RIM[2], -RIM[1]])
    front = max(np.array(profiles['base_side_left']['vertices_world_mm']) @ front_normal)
    report = json.loads(Path('fea/results/current-leg-revision-screen.json').read_text())
    assert len(loads()) == 18
    for row in report['results']:
        if not row['best']:
            continue
        points = np.array(row['best']['points_left_xyz_mm'])
        distance_from_front = front - points @ front_normal
        minimum = 1.5 * row['diameter_in'] * 25.4 + 2.
        assert min(distance_from_front) >= minimum - 1e-6
        assert max(distance_from_front) <= row['rim_depth_mm'] - minimum + 1e-6
