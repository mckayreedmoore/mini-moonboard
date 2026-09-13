"""Independent rigid-body statics examples; no CAD rebuild required."""
import pytest

from fea.current_frame_equilibrium import equilibrium, reaction_ranges

SQUARE = [[-1., -1.], [1., -1.], [1., 1.], [-1., 1.]]


def test_centered_vertical_load():
    result = equilibrium([[0, 0, 2]], [[0, 0, -100]], SQUARE)
    assert result['required_pressure_centre_xy_mm'] == pytest.approx([0, 0])
    assert result['minimum_restoring_moment_nmm'] == pytest.approx(100)


def test_horizontal_load_shifts_pressure_and_allows_overturning():
    result = equilibrium([[0, 0, 2]], [[60, 0, -100]], SQUARE)
    assert result['required_pressure_centre_xy_mm'] == pytest.approx([1.2, 0])
    assert not result['normal_equilibrium_feasible']
    assert result['minimum_edge_margin_mm'] == pytest.approx(-.2)


def test_reaction_ranges_do_not_assume_equal_sharing():
    supports = [{'name': str(i), 'vertices_mm': [[*p, 0]]} for i, p in enumerate(SQUARE)]
    result = equilibrium([[0, 0, 2]], [[0, 0, -100]], SQUARE)
    for row in reaction_ranges(supports, result):
        assert row['minimum_n'] == pytest.approx(0)
        assert row['maximum_n'] == pytest.approx(50)


def test_support_edge_contact_is_admissible_without_tension():
    supports = [{'name': str(i), 'vertices_mm': [[*p, 0]]} for i, p in enumerate(SQUARE)]
    result = equilibrium([[1, 0, 0]], [[0, 0, -100]], SQUARE)
    rows = reaction_ranges(supports, result)
    assert rows[0]['maximum_n'] == pytest.approx(0)
    assert rows[3]['maximum_n'] == pytest.approx(0)
    assert rows[1]['minimum_n'] == pytest.approx(50)
    assert rows[2]['minimum_n'] == pytest.approx(50)


def test_exact_azimuth_envelope_and_equipment_bound():
    from fea.current_frame_equilibrium import azimuth_envelope

    # Diamond's outward normals are diagonal: cardinal-only forces miss them.
    polygon = [[0., -1000.], [1000., 0.], [0., 1000.], [-1000., 0.]]
    supports = [{'name': str(i), 'vertices_mm': [[*p, 0]]} for i, p in enumerate(polygon)]
    report = {'support_polygon_mm': polygon, 'supports': supports,
              'modeled_centre_xyz_mm': [0., 0., 100.], 'modeled_mass_kg': 100.,
              'equipment_point_xyz_mm': [0., 0., 100.],
              'load_locations': [{'name': 'edge', 'front_xyz_mm': [100., 0., 100.],
                                  'outward_xyz': [0., 0., 1.]}]}
    rows = azimuth_envelope(report)
    baseline, bounded = rows[0], rows[4]
    assert abs(baseline['horizontal_force_xy_n'][0]) == pytest.approx(300/2**.5)
    assert abs(baseline['horizontal_force_xy_n'][1]) == pytest.approx(300/2**.5)
    assert bounded['minimum_edge_margin_mm'] < baseline['minimum_edge_margin_mm']
