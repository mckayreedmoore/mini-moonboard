"""Own source-event, one-sided trace, geometry-query and claim controls."""
import hashlib
import io
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import eoere_rail_section_audit as rail


def test_brep_import_consumes_the_verified_snapshot_after_its_source_path_changes(tmp_path, monkeypatch):
    payload = b'original cached solid'
    path = tmp_path/'solid.brep'
    path.write_bytes(payload)
    monkeypatch.setattr(rail.current, 'ROOT', tmp_path)
    reference = {'path': path.name, 'sha256': hashlib.sha256(payload).hexdigest()}

    def importer(stream):
        assert isinstance(stream, io.BytesIO)
        path.write_bytes(b'replaced after intake')
        return stream.read()

    assert rail.read_pinned_brep(reference, importer) == payload
    assert path.read_bytes() == b'replaced after intake'


def test_transient_brep_replacement_restored_after_intake_refuses_before_import(tmp_path, monkeypatch):
    payload = b'original cached solid'
    path = tmp_path/'solid.brep'
    path.write_bytes(payload)
    monkeypatch.setattr(rail.current, 'ROOT', tmp_path)
    reference = {'path': path.name, 'sha256': hashlib.sha256(payload).hexdigest()}
    original_read = Path.read_bytes

    def replaced_read(target):
        if target != path:
            return original_read(target)
        target.write_bytes(b'transient replacement')
        captured = original_read(target)
        target.write_bytes(payload)
        return captured

    monkeypatch.setattr(Path, 'read_bytes', replaced_read)
    imported = []
    with pytest.raises(ValueError, match='consumed BREP bytes changed'):
        rail.read_pinned_brep(reference, lambda stream: imported.append(stream.read()))
    assert imported == [] and original_read(path) == payload


def test_world_wrench_projects_in_a_right_handed_frame_without_dropping_torque():
    basis = [[F(1), 0, 0], [0, F(3, 5), F(4, 5)], [0, F(-4, 5), F(3, 5)]]
    assert rail.local_wrench([F(2), F(5), F(10)], [F(11), F(10), F(5)], basis) == [2, 11, 2, 11, 10, -5]


def test_source_event_census_keeps_tiny_forces_and_free_couples_but_not_zero_or_boundary_events():
    tiny = F(1, 2**150)
    points = [([s, 0, 0], force, couple) for s, force, couple in [
        (0, [0, 0, 1], [0, 0, 0]), (2, [0, 0, tiny], [0, 0, 0]), (3, [0, 0, 0], [0, 0, 0]),
        (5, [0, 0, 0], [tiny, 0, 0]), (10, [0, 0, 1], [0, 0, 0])]]
    helper = SimpleNamespace(own=SimpleNamespace(member_point_inputs=lambda field: ({'rail': points}, {'rail': ([5, 0, 0], [0, 0, -1])})))
    result, center, gravity, events = rail.source_case({}, {'name': 'rail', 'axis': [1., 0., 0.]}, helper, (F(0), F(10)))
    assert len(result) == 5 and events == [2, 5]
    assert center == [5, 0, 0] and gravity == [0, 0, -1]
    assert result[1][1][2] == tiny and result[3][2][0] == tiny


def test_source_census_refuses_a_different_member_axis():
    with pytest.raises(ValueError, match='X-grain'):
        rail.source_case({}, {'axis': [0, 1, 0]}, None, (F(0), F(10)))


def test_adjacent_cubic_spans_retain_both_sides_of_a_point_force_and_free_couple():
    points = [[[F(5), F(2), F(3)], [F(4), F(5), F(6)], [F(7), F(8), F(9)]]]
    basis = rail.method.frame(0)
    left, _, left_count = rail.span_controls(0, 5, points, [5, 0, 0], [0, 0, 0], 0, 10, [0, 0], basis)
    right, _, right_count = rail.span_controls(5, 10, points, [5, 0, 0], [0, 0, 0], 0, 10, [0, 0], basis)
    assert left_count == 0 and right_count == 1
    assert left[-1] == [0]*6
    # At x=5, r=(0,2,3), r x F=(-3,12,-8); add free=(7,8,9), then negate.
    assert right[0] == [-4, -5, -6, -4, -20, -1]
    assert rail.method.evaluate_controls(right, F(1, 2)) == [-4, -5, -6, -4, -35, F(23, 2)]


def test_unregistered_interior_source_event_refuses_continuous_interpolation():
    with pytest.raises(ValueError, match='uncounted'):
        rail.span_controls(0, 10, [[[F(5), 0, 0], [0, 0, F(1, 2**150)], [0, 0, 0]]],
                           [5, 0, 0], [0, 0, 0], 0, 10, [0, 0], rail.method.frame(0))


@pytest.mark.parametrize('lower,upper,status', [
    (F(1), F(1), 'continuous_section_traction_construction_within_hypothesis'),
    (F(1)+F(1, 2**150), F(2), 'section_hypothesis_fails_at_a_recorded_actual_station'),
    (F(1, 2), F(1)+F(1, 2**150), 'section_hypothesis_inconclusive'),
])
def test_dispositions_use_exact_strict_thresholds_and_do_not_claim_member_resistance(lower, upper, status):
    scenario = {'strength_divisor': 2., 'whole_wrench_multiplier': 1.5, 'working_reference': False}
    result = rail.comparison(lower/3, upper/3, scenario)
    assert result['disposition'] == status
    assert F(result['exact_necessary_actual_station_lower']) == lower
    assert F(result['exact_continuous_construction_upper']) == upper
    assert result['complete_member_or_joint_resistance'] is None and result['physical_failure_established'] is False


class Face:
    def __init__(self, vertices, edge='LINE', wires=1):
        self.vertices, self.edge, self.wires = vertices, edge, wires

    def Wires(self):
        return [None]*self.wires

    def Edges(self):
        return [SimpleNamespace(geomType=lambda: self.edge)]*4

    def Vertices(self):
        return [SimpleNamespace(toTuple=lambda vertex=vertex: vertex) for vertex in self.vertices]


def test_polygon_query_preserves_exact_binary_coordinates_and_records_its_rounding():
    face = Face([[0., .1, .2], [0., 1.1, .2], [0., 1.1, 1.2], [0., .1, 1.2]])
    raw, rounded, error = rail.polygon(face, [F(0)]*3, rail.method.frame(0), 8)
    assert any(value == F.from_float(.1) for point in raw for value in point)
    assert any(value == F(1, 10) for point in rounded for value in point)
    assert 0 < error <= F(1, 2*10**8)
    inner, outer = rail.method.robust_boxes(rounded, F(1, 500000), F(1, 10000))
    assert inner[0] > outer[0] and inner[1] < outer[1]


@pytest.mark.parametrize('change', ['curve', 'hole', 'missing-vertex', 'off-plane'])
def test_unrepresented_face_boundaries_or_a_wrong_plane_refuse(change):
    face = Face([[0, -1, -1], [0, 1, -1], [0, 1, 1], [0, -1, 1]])
    if change == 'curve':
        face.edge = 'CIRCLE'
    elif change == 'hole':
        face.wires = 2
    elif change == 'missing-vertex':
        face.vertices.pop()
    else:
        face.vertices[0][0] = F(1, 10**5)
    with pytest.raises(ValueError):
        rail.polygon(face, [F(0)]*3, rail.method.frame(0), 8)
