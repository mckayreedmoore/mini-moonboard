"""Both physical bolt ends survive the new candidate's inspectable geometry."""
import cadquery as cq
import pytest

from mini_moonboard.bolted_frame import WASHER, FrameBolt
from mini_moonboard.selected_hardware import BoltSpec
from mini_moonboard.split_center_hardware import BOLT_ROLES, with_hex_ends


@pytest.mark.parametrize('sign', [-1., 1.])
def test_hex_bolt_retains_two_washers_head_nut_and_axial_positions(sign):
    original = FrameBolt('test', cq.Vector(100., 20., 30.), cq.Vector(sign, 0., 0.),
                         95.25, 9.525, ('rim', 'leg'), 'bolt', 76.2)
    bolt = with_hex_ends(original)
    parts, old = bolt.components(), original.components()
    spec = BoltSpec('test', bolt.length, bolt.grip, 0.)
    assert len(parts) == len(BOLT_ROLES) == 5
    for part in parts:
        assert part.isValid() and len(part.Solids()) == 1 and part.Volume() > 0.
    for index in range(3):
        assert parts[index].Volume() == pytest.approx(old[index].Volume())
    for index, start, end in ((3, -spec.head_height_max_mm, 0.),
                             (4, bolt.grip+2*WASHER,
                              bolt.grip+2*WASHER+spec.nut_height_max_mm)):
        coordinates = [(vertex.Center()-bolt.start).dot(bolt.direction)
                       for vertex in parts[index].Vertices()]
        assert min(coordinates) == pytest.approx(start)
        assert max(coordinates) == pytest.approx(end)
        assert parts[index].Volume() < old[index].Volume()
    assert sum(face.geomType() == 'PLANE' for face in parts[3].Faces()) == 8
    assert sum(face.geomType() == 'PLANE' for face in parts[4].Faces()) == 8
    assert parts[4].intersect(parts[0]).Volume() < 1e-8
    assert bolt.start == original.start and bolt.direction == original.direction
    assert bolt.length == original.length and bolt.grip == original.grip
