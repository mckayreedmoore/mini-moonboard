"""Apply the same full hardware geometry gates to the rotated 2x8 candidate."""
from types import SimpleNamespace

import pytest
import test_hybrid_frame as gates

from mini_moonboard import hybrid_frame as h
from mini_moonboard import shallow_frame as shallow


@pytest.mark.parametrize('gate',[
    gates.test_solids_and_collisions,
    gates.test_connections_have_receivers_and_connected_graph,
    gates.test_tool_led_and_routing_envelopes,
    gates.test_floor_and_rib_orientation,
    gates.test_rib_crossed_bores_retain_recorded_ligament,
])
def test_same_complete_geometry_gates(monkeypatch,gate):
    monkeypatch.setattr(gates,'h',SimpleNamespace(
        parts=lambda size:shallow.parts(),connections=lambda size:shallow.connections(),
        panel_attachments=h.panel_attachments))
    gate('2x8')


def test_rotated_rear_dimensions_and_reference_preserved():
    parts={p.name:p for p in shallow.parts(False)}
    assert parts['rear_cross_1'].blank==(2438.4,88.9,38.1)
    assert parts['rib_1_mid_left'].blank[0]==pytest.approx(89.95)
    assert h.parts('2x8',False)!=shallow.parts(False)


def test_rear_members_remain_bolt_detachable_and_counts_preserved():
    connections=shallow.connections()
    assert len(connections)==len(h.connections('2x12'))
    for row in range(1,4):
        member=f'rear_cross_{row}'
        joints=[c for c in connections if member in c.members]
        assert len(joints)==12
        assert all(c.kind=='bolt' for c in joints)
    assert sum(c.kind=='bolt' for c in connections)==88
    assert sum(c.kind=='screw' for c in connections)==132
