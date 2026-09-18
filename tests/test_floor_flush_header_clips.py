"""Center-header SDS must sit in the header, not on its front edge."""
from mini_moonboard import compact_floor_flush_frame as model


def test_base_center_header_sds_holes_stay_inside_the_header():
    header = next(part for part in model.uncut_wood_parts() if part.name == 'base_header')
    bounds = header.shape.BoundingBox()
    hole_radius = 6.731 / 2
    found = 0
    for connection in model.connections():
        if 'clip_split_base_center' not in connection.name or '_beam_' not in connection.name:
            continue
        found += 1
        assert bounds.ymin + hole_radius <= connection.start.y <= bounds.ymax - hole_radius, connection.name
        assert bounds.xmin < connection.start.x < bounds.xmax
    assert found == 6
