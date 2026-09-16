"""The full-stock adapter must explicitly assign post material and restore state."""
from types import SimpleNamespace

import pytest

from fea import floor_uncut_run as adapter
from fea.current_response_materials import df_l_no2_post_timber, materials


def test_source_guard_includes_cli_case_loads_and_bolt_spring_helper():
    assert {'scripts/floor_uncut_case.py', 'scripts/clear_space_batch.py',
            'scripts/compact_rail_study.py'} <= adapter.sources().keys()


def test_front_bolt_seat_uses_lower_post_modulus_without_changing_other_joints(monkeypatch):
    # Independent 100 mm² seat witness: the old uniform-material spring is
    # 309.029 N/mm; two material paths in series give 261.752 N/mm.
    old = {'washer_net_area_mm2': 100., 'axial_n_per_mm': 309.02922430588865,
           'lateral_n_per_mm': 123., 'basis': 'Test spring.'}
    monkeypatch.setattr(adapter, 'uniform_bolt_properties', lambda connection: dict(old))
    front = SimpleNamespace(name='rail_front_bolt_left_1',
                            members=('base_post_outer_left', 'base_floor_left'),
                            grip=177.8, diameter=9.525)
    result = adapter.bolt_properties(front)
    assert result['axial_n_per_mm'] == pytest.approx(261.7517299851994)
    assert result['lateral_n_per_mm'] == old['lateral_n_per_mm']
    assert adapter.bolt_properties(SimpleNamespace(members=('lumber_leg_left', 'base_floor_left'))) == old
    front.grip = 180.
    with pytest.raises(ValueError, match='actual wood grip'):
        adapter.bolt_properties(front)


def test_post_assignment_and_response_factory_restore(monkeypatch):
    class Structure:
        def __init__(self):
            self.members = {name: {'record': {}} for name in (*adapter.POSTS, 'base_side_left')}

    def factory(module, **kwargs):
        assert set(kwargs['materials']['timber_by_name']) == set(adapter.POSTS)
        assert kwargs['materials']['timber'] == materials()['timber']
        return Structure(), {'materials': kwargs['materials']}

    monkeypatch.setattr(adapter, 'prepare_uncut', factory)
    structure, _ = adapter.prepare(adapter.candidate, materials=materials())
    for name in adapter.POSTS:
        assert structure.members[name]['record']['reference_override'] == df_l_no2_post_timber()['reference_override']
    assert 'reference_override' not in structure.members['base_side_left']['record']

    native = adapter.native
    original = native.source_hashes, native.LOADED_SOURCE_SHA256
    monkeypatch.setattr(adapter, 'face_contacts', lambda *args, **kwargs: [{'name': 'contact'}])

    def fail(*args, **kwargs):
        assert kwargs['prepare_factory'] is adapter.prepare
        assert kwargs['member_contacts'] == [{'name': 'contact'}]
        assert kwargs['clearance_monitors'] == ()
        assert kwargs['expected_candidate'] == adapter.candidate.KEY
        raise RuntimeError('native failure')

    monkeypatch.setattr(native, 'run', fail)
    with pytest.raises(RuntimeError, match='native failure'):
        adapter.run('unused')
    assert (native.source_hashes, native.LOADED_SOURCE_SHA256) == original
