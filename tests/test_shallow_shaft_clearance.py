"""Fastener shanks may enter named receivers, not unrelated frame members."""

from mini_moonboard import shallow_frame
from mini_moonboard.box_exports import overlap


def test_shanks_clear_nonreceiving_parts():
    parts = shallow_frame.parts()
    collisions = []
    for connection in shallow_frame.connections():
        shaft = connection.components()[0]
        for part in parts:
            if part.name not in connection.members:
                volume = overlap(shaft, part.shape)
                if volume > 0.01:
                    collisions.append((connection.name, part.name, volume))
    assert not collisions, collisions
