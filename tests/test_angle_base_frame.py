"""Fresh angle-base connections preserve panel/leg hardware without gusset holes."""
import pytest

from mini_moonboard import angle_base_frame as model
from mini_moonboard.connection_geometry import material_intervals


def test_only_gussets_and_their_eight_bolts_are_removed():
    old = {c.name: c for c in model.previous.connections()}
    revised = {c.name: c for c in model.connections()}
    removed = set(old)-set(revised)
    assert removed == {f'timber_base_{side}_{index}' for side in ('left', 'right') for index in range(1, 5)}
    assert all(c is old[name] for name, c in revised.items() if name in old)
    assert sum(c.kind == 'bolt' for c in revised.values()) == 8
    assert sum(isinstance(c, model.timber.PanelScrew) for c in revised.values()) == 151
    raw = {p.name: p for p in model.wood_parts()}
    prior = {p.name: p for p in model.previous.wood_parts()}
    assert set(prior)-set(raw) == {'timber_base_gusset_left', 'timber_base_gusset_right'}
    assert all(p.shape is prior[name].shape for name, p in raw.items())
    assert all(p.blank == prior[name].blank for name, p in raw.items())
    assert all('retained outer gussets' not in p.description for p in raw.values())
    assert all(model.LIMITS in p.description for name, p in raw.items()
               if model.previous.previous.LIMITS in prior[name].description)
    assert 'purchased' not in model.LIMITS


def test_angles_directly_connect_each_rim_to_header_with_full_screw_penetration():
    raw = {p.name: p for p in model.wood_parts()}
    new = [c for c in model.connections() if c.name.startswith('clip_angle_base_')]
    assert len(new) == 12
    for side in ('left', 'right'):
        assert {c.members[1] for c in new if f'_{side}_' in c.name} == {'base_header', f'base_side_{side}'}
    for c in new:
        length = sum(z-a for a, z in material_intervals(raw[c.members[1]].shape, c.start, c.direction, 0., c.length))
        assert length == pytest.approx(model.hardware.SDS['gross_penetration_through_nominal_ml24z']), c.name


def test_fresh_machining_leaves_removed_gusset_bolt_axes_solid():
    machined = {p.name: p for p in model.parts()}
    removed = [c for c in model.previous.connections()
               if c.name.startswith(('timber_base_left_', 'timber_base_right_'))]
    assert len(removed) == 8
    for c in removed:
        receiver = c.members[0]
        length = sum(z-a for a, z in material_intervals(machined[receiver].shape, c.start, c.direction, 0., c.length))
        assert length == pytest.approx(38.1), c.name
