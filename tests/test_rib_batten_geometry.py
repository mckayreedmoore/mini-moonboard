"""Guard the actual foot100 detail against accidentally auditing its ancestor."""
import pytest

from mini_moonboard import box_frame as b
from mini_moonboard.box_exports import overlap
from mini_moonboard.footprint_frame import connections, parts


def local_n_range(shape):
    origin, normal = b.point(0, 0, 0), b.normal()
    values = [(vertex.Center()-origin).dot(normal) for vertex in shape.Vertices()]
    return min(values), max(values)


def test_actual_foot100_rib_and_front_screw_depths():
    # Undrilled bodies isolate the nominal timber interfaces, not fastener
    # resistance or the orientation of grain in purchased stock.
    bodies = {part.name: part for part in parts(100, False)}
    front = [c for c in connections() if c.name.startswith("rib_") and c.name.endswith("_front")]
    assert len(front) == 12
    origin, normal = b.point(0, 0, 0), b.normal()
    for connection in front:
        batten, rib = [bodies[name].shape for name in connection.members]
        assert local_n_range(batten) == pytest.approx((0., 38.1), abs=1e-7)
        assert local_n_range(rib) == pytest.approx((38.1, 128.05), abs=1e-7)
        assert connection.direction.dot(normal) == pytest.approx(1.)
        start = (connection.start-origin).dot(normal)
        end = (connection.start+connection.direction*connection.length-origin).dot(normal)
        assert start == pytest.approx(0., abs=1e-7)
        assert end == pytest.approx(88.9, abs=1e-7)
        assert end-38.1 == pytest.approx(50.8, abs=1e-7)
        assert 128.05-end == pytest.approx(39.15, abs=1e-7)
        assert local_n_range(rib)[1]-local_n_range(rib)[0] > 88.9
        shaft = connection.components()[0]
        bounds = shaft.BoundingBox()
        hits = set()
        for name, part in bodies.items():
            other = part.shape.BoundingBox()
            if all(min(getattr(bounds, axis+"max"), getattr(other, axis+"max")) >
                   max(getattr(bounds, axis+"min"), getattr(other, axis+"min"))
                   for axis in "xyz") and shaft.intersect(part.shape).Volume() > 1e-4:
                hits.add(name)
        assert hits == set(connection.members), (connection.name, hits)


@pytest.mark.parametrize("width,length,expected_overlap", [
    (44.45, 114.3, 22580.6),  # Centred axial-only SDWS16 distance envelope.
    (50.8, 203.2, 42858.69),  # Centred SDWS16312 perpendicular lateral envelope.
])
def test_enlarged_rib_distance_envelopes_require_relocated_rear_angles(
        width, length, expected_overlap):
    # Geometric exclusion screen only: no product capacity, stock selection,
    # bore/head clearance or manufacturing allowance is established here.
    bodies = {part.name: part.shape for part in parts(100, False)}
    origin = b.point(0, 0, 0)
    tangent = (b.point(0, 1, 0)-origin).normalized()
    ribs = {name: shape for name, shape in bodies.items() if name.startswith("rib_")}
    assert len(ribs) == 12
    for name, original in ribs.items():
        center = original.Center()
        x, s = center.x, (center-origin).dot(tangent)
        enlarged = b.block(x-width/2, x+width/2, s-length/2, s+length/2,
                           38.1, 128.05)
        hits = {other: volume for other, shape in bodies.items()
                if other != name and (volume := overlap(enlarged, shape)) > 1e-4}
        assert set(hits) == {"angle_"+name}
        assert hits["angle_"+name] == pytest.approx(expected_overlap, abs=1e-3)
