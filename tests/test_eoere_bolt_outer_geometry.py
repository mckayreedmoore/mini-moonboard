"""Analytic profiles, whole-bore minima and cached-face claim controls."""
import copy
import itertools
import math
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.spatial import QhullError

from scripts import eoere_bolt_outer_geometry as geometry
from scripts.thin_bolted_timber_resistance import end_geometry_factor


def box():
    return {'member': 'ownwood', 'basis_grain_u_v_xyz': np.eye(3).tolist(), 'datum_xyz_mm': [0., 0., 0.],
            'raw_profile_vertices_luv_mm': list(map(list, itertools.product((0., 240.), (0., 20.), (0., 80.))))}


def bore(profile=None, direction=(0., 1., 0.)):
    if profile is None:
        profile = geometry.outer_profile(box())
    surface = {'kind': 'wood', 'host': profile['member'], 'interval_mm': [0., 20.]}
    shaft = {'axis_id': 'ownbolt', 'point': [100., 0., 40.], 'basis': [list(direction)],
             'diameter_mm': 10., 'surfaces': [surface]}
    return profile, shaft, surface


def test_cube_hull_equations_have_correct_outward_sign_unique_planes_and_volume():
    profile = geometry.outer_profile(box())
    assert len(profile['outer_planes']) == 6
    assert profile['profile_hull_volume_mm3'] == pytest.approx(240*20*80)
    assert profile['all_grain_end_planes_square'] is True
    row = geometry.placement(*bore(profile), end_geometry_factor)
    assert row['minimum_grain_end_distance_mm'] == 100.
    assert row['minimum_outer_edge_distance_mm'] == 40.
    assert row['full_7D_end_marker_pass'] and row['full_4D_outer_edge_marker_pass']
    assert row['square_end_component_factor_if_profile_applies'] == 1.
    assert row['complete_Cdelta'] is None and row['complete_joint_resistance'] is None


def test_other_transverse_bore_direction_selects_its_own_remaining_edge_dimension():
    profile, shaft, surface = bore(direction=(0., 0., -1.))
    shaft['point'], surface['interval_mm'] = [100., 10., 80.], [0., 80.]
    row = geometry.placement(profile, shaft, surface, end_geometry_factor)
    assert row['bore_transverse_dimension'] == 2 and row['edge_transverse_dimension'] == 1
    assert row['minimum_outer_edge_distance_mm'] == 10.
    assert row['full_4D_outer_edge_marker_pass'] is False
    assert row['marker_miss_is_adopted_failure'] is False


def test_three_compound_end_planes_remain_separate_and_do_not_get_square_end_factor():
    raw = box()
    polygon = [(20., 0.), (0., 40.), (20., 80.), (200., 80.), (200., 0.)]
    raw['raw_profile_vertices_luv_mm'] = [[g, u, v] for u in (0., 20.) for g, v in polygon]
    profile = geometry.outer_profile(raw)
    end_planes = [p for p in profile['outer_planes'] if abs(p['normal_luv'][0]) > 1e-7]
    assert len(end_planes) == 3 and not profile['all_grain_end_planes_square']
    row = geometry.placement(*bore(profile), end_geometry_factor)
    assert row['minimum_grain_end_distance_mm'] == pytest.approx(100.)
    assert row['square_end_component_trial']['end_factor_only'] == 1.
    assert row['square_end_component_factor_if_profile_applies'] is None


def test_sloping_end_minimum_uses_whole_bearing_band_instead_of_its_midpoint():
    raw = box()
    raw['raw_profile_vertices_luv_mm'] = [[g, u, v] for u in (0., 20.) for v in (0., 80.) for g in (.1*u, 240.)]
    profile = geometry.outer_profile(raw)
    row = geometry.placement(*bore(profile), end_geometry_factor)
    assert row['minimum_grain_end_distance_mm'] == pytest.approx(98.)
    assert row['minimum_grain_end_distance_mm'] != 99.  # Midshaft is less conservative.


def test_changed_union_vertex_extent_is_used_without_mutating_stale_end_offset_metadata():
    raw = box()
    raw['end_cut_planes'] = [{'outward_normal_luv': [-1., 0., 0.], 'offset_from_datum_mm': 0.}]
    raw['raw_profile_vertices_luv_mm'] = [[g-39.2 if g == 0. else g, u, v]
                                           for g, u, v in raw['raw_profile_vertices_luv_mm']]
    saved = copy.deepcopy(raw)
    profile, shaft, surface = bore(geometry.outer_profile(raw))
    shaft['point'][0] = 20.
    row = geometry.placement(profile, shaft, surface, end_geometry_factor)
    assert row['minimum_grain_end_distance_mm'] == pytest.approx(59.2)
    assert raw == saved and raw['end_cut_planes'][0]['offset_from_datum_mm'] == 0.
    assert row['square_end_component_factor_if_profile_applies'] == pytest.approx(59.2/70.)


def cleat():
    return {'member': 'eoere_cleat_left', 'basis_grain_u_v_xyz': [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]],
            'datum_xyz_mm': [0., 0., 0.],
            'raw_profile_vertices_luv_mm': list(map(list, itertools.product((0., 280.), (0., 38.1), (0., 80.)))),
            'finished_YZ_polygon_mm': [[0., 0.], [80., 0.], [80., 280.], [0., 200.]]}


def test_current_cleat_reader_uses_finished_slope_not_the_full_height_analysis_rectangle():
    raw = cleat()
    saved = copy.deepcopy(raw)
    profile = geometry.outer_profile(raw)
    surface = {'kind': 'wood', 'host': raw['member'], 'interval_mm': [0., 38.1]}
    shaft = {'axis_id': 'ownbolt', 'point': [0., 20., 200.], 'basis': [[1., 0., 0.]],
             'diameter_mm': 9.525, 'surfaces': [surface]}
    row = geometry.placement(profile, shaft, surface, end_geometry_factor)
    assert row['minimum_grain_end_distance_mm'] == pytest.approx(20.)
    assert profile['profile_hull_volume_mm3'] == pytest.approx(80*240*38.1)
    assert not row['full_7D_end_marker_pass']
    assert row['square_end_component_factor_if_profile_applies'] is None
    assert raw == saved


def test_end_and_edge_distances_are_invariant_under_rigid_world_rotation_translation():
    theta = .6
    rotation = np.array([[math.cos(theta), -math.sin(theta), 0.],
                         [math.sin(theta), math.cos(theta), 0.], [0., 0., 1.]])
    translation = np.array([1000., -2000., 300.])
    raw = box()
    raw['basis_grain_u_v_xyz'], raw['datum_xyz_mm'] = rotation.T.tolist(), translation.tolist()
    profile, shaft, surface = bore(geometry.outer_profile(raw))
    shaft['point'] = (rotation@shaft['point']+translation).tolist()
    shaft['basis'][0] = (rotation@shaft['basis'][0]).tolist()
    row = geometry.placement(profile, shaft, surface, end_geometry_factor)
    assert row['minimum_grain_end_distance_mm'] == pytest.approx(100.)
    assert row['minimum_outer_edge_distance_mm'] == pytest.approx(40.)


@pytest.mark.parametrize('change', ['basis', 'left_handed', 'nonfinite', 'flat', 'cleat_width', 'cleat_identity'])
def test_invalid_or_unbound_profile_interpretation_is_refused(change):
    raw = cleat() if change.startswith('cleat') else box()
    if change == 'basis':
        raw['basis_grain_u_v_xyz'][0][0] = 2.
    elif change == 'left_handed':
        raw['basis_grain_u_v_xyz'][0][0] = -1.
    elif change == 'nonfinite':
        raw['raw_profile_vertices_luv_mm'][0][0] = np.nan
    elif change == 'flat':
        for point in raw['raw_profile_vertices_luv_mm']:
            point[0] = 0.
    elif change == 'cleat_width':
        raw['raw_profile_vertices_luv_mm'][-1][1] = 39.
    else:
        raw['member'] = 'other'
    with pytest.raises((ValueError, QhullError)):
        geometry.outer_profile(raw)


@pytest.mark.parametrize('change', ['foreign_host', 'foreign_surface', 'nonperpendicular', 'oblique_bore',
                                  'bad_interval', 'outside_profile', 'diameter'])
def test_wrong_bore_or_source_interval_cannot_enter_an_end_edge_screen(change):
    profile, shaft, surface = copy.deepcopy(bore())
    if change == 'foreign_host':
        surface['host'] = 'other'
    elif change == 'foreign_surface':
        shaft['surfaces'] = []
    elif change == 'nonperpendicular':
        shaft['basis'] = [[1., 0., 0.]]
    elif change == 'oblique_bore':
        shaft['basis'] = [[0., 1/math.sqrt(2), 1/math.sqrt(2)]]
    elif change == 'bad_interval':
        surface['interval_mm'] = [0., 0.]
    elif change == 'outside_profile':
        shaft['point'][0] = -1.
    else:
        shaft['diameter_mm'] = 0.
    with pytest.raises(ValueError):
        geometry.placement(profile, shaft, surface, end_geometry_factor)


def cached_shape(profile, *, missing_face=False, outside_vertex=False):
    def vector(p):
        return SimpleNamespace(toTuple=lambda: p)
    faces = []
    for plane in profile['outer_planes']:
        normal = np.asarray(plane['normal_xyz'])
        point = normal*plane['offset_world_mm']
        faces.append(SimpleNamespace(geomType=lambda: 'PLANE', normalAt=lambda n=normal: vector(n.tolist()),
                                     Center=lambda p=point: vector(p.tolist()), Area=lambda: 1.))
    if missing_face:
        faces.pop()
    else:
        # Additional inner cut plane must remain explicit, with no ligament proof.
        faces.append(SimpleNamespace(geomType=lambda: 'PLANE', normalAt=lambda: vector([1., 0., 0.]),
                                     Center=lambda: vector([120., 10., 40.]), Area=lambda: 10.))
    faces.append(SimpleNamespace(geomType=lambda: 'CYLINDER'))
    vertices = [vector(p) for p in profile['vertices_luv_mm']]
    if outside_vertex:
        vertices.append(vector([-1., 0., 0.]))
    return SimpleNamespace(Faces=lambda: faces, Vertices=lambda: vertices)


def test_cached_face_identity_keeps_other_cuts_and_curves_and_does_not_claim_ligament_strength():
    profile = geometry.outer_profile(box())
    result = geometry.confirm_faces(cached_shape(profile), profile)
    assert result['all_profile_planes_present_on_cached_finished_faces']
    assert result['cached_vertices_within_outer_hull']
    assert len(result['additional_finished_planar_faces']) == 1
    assert result['other_finished_face_types'] == {'CYLINDER': 1}
    assert result['complete_finished_ligament_or_curved_containment_proven'] is False


@pytest.mark.parametrize('missing,outside', [(True, False), (False, True)])
def test_missing_finished_plane_or_vertex_mismatch_is_visible_instead_of_repaired(missing, outside):
    profile = geometry.outer_profile(box())
    result = geometry.confirm_faces(cached_shape(profile, missing_face=missing, outside_vertex=outside), profile)
    assert result['all_profile_planes_present_on_cached_finished_faces'] is not missing
    assert result['cached_vertices_within_outer_hull'] is not outside
