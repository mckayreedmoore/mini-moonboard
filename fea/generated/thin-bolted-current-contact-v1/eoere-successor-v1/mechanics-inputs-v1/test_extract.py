"""Tiny extraction/math contracts only; candidate file imports are forbidden."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
SPEC = importlib.util.spec_from_file_location('eoere_metadata_extract_fixture', OWN.with_name('extract.py'))
x = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(x)


def query_methods():
    return x.load_query_methods(x.METHODS)


def test_cleat_gross_profile_and_grain():
    m = x.pure_methods()
    row = x.gross_row(x.cleat_profile('left'), m)
    assert row['start'] == [-1238.25, -105.85, 139.7]
    assert row['end'] == [-1238.25, -105.85, 429.4]
    assert row['axis'] == [0., 0., 1.]
    assert row['width_mm'] == pytest.approx(38.1)
    assert row['depth_mm'] == pytest.approx(139.7)
    assert row['finished_cut_stiffness_or_resistance_qualified'] is False


def test_exact_strip_port_sign_and_reject():
    assert x.port_id('beam', -1) == 'arm-x/far-plus'
    assert x.port_id('post', 1) == 'arm-z/far-minus'
    with pytest.raises(ValueError, match='exact owned'):
        x.port_id('beam', 0)


def test_capture_external_host_and_multiple_host_reject():
    m = x.pure_methods()
    axis = {'id': 'synthetic', 'direction_xyz': [1., 0., 0.], 'grip_mm': 30.,
            'before_plate_mm': 2., 'after_plate_mm': 0., 'hardware_scenario': {'washer_thickness_mm': 1.}}
    surfaces = [{'kind': 'steel', 'host': 'toy-fitting', 'flange': 'arm-x/far-plus', 'interval_mm': [-2., 0.]},
                {'kind': 'wood', 'host': 'toy-timber', 'interval_mm': [0., 30.]}]
    rows = x.end_seats(axis, surfaces, m)
    assert [(r['host'], r['flange']) for r in rows] == [('toy-fitting', 'arm-x/far-plus'), ('toy-timber', None)]
    assert [r['pressure_face_s_mm'] for r in rows] == [-3., 31.]
    with pytest.raises(ValueError, match='one actual external host'):
        x.end_seats(axis, [*surfaces, surfaces[0]], m)


def test_serialization_guard_before_candidate_import(monkeypatch):
    monkeypatch.delenv('EOERE_PARENT_SERIALIZED_EXTRACTION', raising=False)
    with patch.object(x, 'load_query_methods', side_effect=AssertionError('too early')), pytest.raises(ValueError, match='parent serialized'):
        x.extract({}, {}, {}, [], {})


def test_role_scalar_midpoints_known_answer():
    m, q = x.pure_methods(), query_methods()
    axis = {'id': 'synthetic', 'point_xyz_mm': [20., 30., 40.], 'direction_xyz': [-1., 0., 0.],
            'diameter_mm': 4., 'grip_mm': 10., 'before_plate_mm': 2., 'after_plate_mm': 3.,
            'nominal_under_head_length_mm': 30., 'hardware_scenario': {'washer_thickness_mm': 1.,
                'washer_od_mm': 8., 'washer_id_mm': 5., 'head_height_mm': 2., 'nut_height_mm': 4., 'hex_across_flats_mm': 7.}}
    rows = {r['kind']: r for r in x.role_rows(axis, m, q.inventory.hardware_volumes(axis))}
    assert rows['shaft']['volume_mm3'] == pytest.approx(120 * math.pi)
    assert rows['shaft']['center_of_mass_xyz_mm'] == [8., 30., 40.]
    assert rows['head']['center_of_mass_xyz_mm'] == [24., 30., 40.]
    assert rows['nut_washer']['center_of_mass_xyz_mm'] == [6.5, 30., 40.]
    assert rows['nut']['center_of_mass_xyz_mm'] == [4., 30., 40.]


def test_generic_finished_full_bore_wall_toy_only():
    q = query_methods()
    with patch.object(q.cq.Shape, 'importBrep', side_effect=AssertionError('candidate import forbidden')):
        stock = q.cq.Solid.makeBox(10., 20., 30.)
        p, g = q.cq.Vector(0., 10., 15.), q.cq.Vector(1., 0., 0.)
        cutter = q.cq.Solid.makeCylinder(1.5, 12., p - g, g)
        result = q.bore.finished_bore_wall_intervals(stock.cut(cutter), p, g, 1.5)
    assert result['full_wall_length_mm'] == pytest.approx(10., abs=1e-10)
    assert result['partial_wall_present'] is False
    assert result['qualified_directional_bearing_length_mm'] is None


def test_generic_holed_shared_face_geometry_toy_only():
    q = query_methods()
    with patch.object(q.cq.Shape, 'importBrep', side_effect=AssertionError('candidate import forbidden')):
        upper = q.cq.Solid.makeBox(120., 80., 3.)
        lower = q.cq.Solid.makeBox(120., 80., 5., q.cq.Vector(0., 0., -5.))
        hole = q.cq.Solid.makeCylinder(2., 10., q.cq.Vector(30., 20., -6.))
        shapes = {'toy-upper': upper.cut(hole), 'toy-lower': lower.cut(hole)}
        faces = {name: q.atlas.source_face_records(name, body) for name, body in shapes.items()}
        patches = q.geometry.find_patches('toy-upper', 'toy-lower', faces, shapes, cell_size_mm=40.)
    assert len(patches) == 1
    witness = patches[0]
    area = 9600. - math.pi * 4.
    assert witness['area_mm2'] == pytest.approx(area, rel=1e-12)
    expected = [(9600. * r - math.pi * 4. * h) / area for r, h in ((60., 30.), (40., 20.))]
    assert witness['centroid_xyz_mm'] == pytest.approx([*expected, 0.], abs=1e-10)
    assert all(r['both_inward_material_probes_occupied'] for r in witness['cells'])
    assert witness['cell_area_error_mm2'] == pytest.approx(0., abs=1e-8)


def test_nominal_flange_half_area_centroid_and_weight_rule_toy_only():
    q, m = query_methods(), x.pure_methods()
    pose = {'id': 'toy', 'origin_xyz_mm': [10., 20., 30.], 'u_xyz': [1., 0., 0.], 'v_xyz': [0., 1., 0.], 'w_xyz': [0., 0., 1.]}
    s = {'leg_mm': 40., 'width_mm': 30., 'thickness_mm': 2., 'factory_hole_mm': 2.,
         'far_offset_mm': 25., 'axial_pitch_mm': 15., 'transverse_pitch_mm': 10.}
    with patch.object(q.cq.Shape, 'importBrep', side_effect=AssertionError('candidate import forbidden')):
        body, area, normal = x.fitting_face(pose, 'beam', -1, s, q, m)
    assert area == pytest.approx(38. * 15. - 2 * math.pi, rel=1e-12)
    assert body.Volume() == pytest.approx(2 * area, rel=1e-12)
    assert normal == [0., 1., 0.]
    assert sum(40000. * a / (2 * area) for a in (area / 4, 3 * area / 4)) == pytest.approx(20000.)
    assert x.fitting_centroid(s, pose, m)[2] == 30.
