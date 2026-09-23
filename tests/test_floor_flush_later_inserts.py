"""Current screw axes leave room for a later insert body. Not a build or rating."""
import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as model
from mini_moonboard.timber_connections import ConnectorScrew
from mini_moonboard.timber_frame import PanelScrew

# E-Z LOK 801420-13 drawing: 0.453 in OD, 0.512 in long, ±0.025 in.
INSERT_OD_MAX_MM = 11.5062 + 0.635
INSERT_LENGTH_MAX_MM = 13.0048 + 0.635
VOLUME_TOLERANCE_MM3 = 1.0
ENTRY_STEP_MM = 0.25


def _wood_entry(connection, receiver):
    direction = connection.direction.normalized()
    for index in range(401):
        point = connection.start + direction * (index * ENTRY_STEP_MM)
        if receiver.isInside(point.toTuple()):
            return point
    return None


def _insert_cylinder(connection, receiver):
    entry = _wood_entry(connection, receiver)
    assert entry is not None, connection.name
    return cq.Solid.makeCylinder(
        INSERT_OD_MAX_MM / 2, INSERT_LENGTH_MAX_MM, entry, connection.direction.normalized())


def test_later_insert_bodies_fit_all_wood_screw_axes():
    wood = {part.name: part.shape for part in model.uncut_wood_parts()}
    connections = list(model.connections())
    sds = [c for c in connections if isinstance(c, ConnectorScrew)]
    panels = [c for c in connections if isinstance(c, PanelScrew)]
    bolts = [c for c in connections if getattr(c, 'kind', '') == 'bolt']
    assert len(sds) == 144
    assert len(panels) == 66
    assert len(bolts) == 12

    cylinders = []
    for connection in (*sds, *panels):
        receiver = wood[connection.members[1]]
        cylinder = _insert_cylinder(connection, receiver)
        missing = cylinder.cut(receiver).Volume()
        assert missing <= VOLUME_TOLERANCE_MM3, (connection.name, missing)
        cylinders.append((connection.name, cylinder, connection.start))

    others = list(cylinders)
    for bolt in bolts:
        others.append((
            bolt.name,
            cq.Solid.makeCylinder(
                bolt.diameter / 2, bolt.length, bolt.start, bolt.direction.normalized()),
            bolt.start))
    for index, (name, cylinder, origin) in enumerate(cylinders):
        box = cylinder.BoundingBox()
        for other_name, other, other_origin in others[index + 1:]:
            if (origin - other_origin).Length > 80:
                continue
            other_box = other.BoundingBox()
            if (box.xmin > other_box.xmax or other_box.xmin > box.xmax
                    or box.ymin > other_box.ymax or other_box.ymin > box.ymax
                    or box.zmin > other_box.zmax or other_box.zmin > box.zmax):
                continue
            overlap = cylinder.intersect(other).Volume()
            assert overlap <= VOLUME_TOLERANCE_MM3, (name, other_name, overlap)
