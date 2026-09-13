"""Knee tab cuts and all connection holes remain explicit in sampled sections."""
import copy

import pytest

from scripts import compact_knee_results as knee


def fixture():
    member = {'grain': [0., 0., 1.], 'centre_mm': [0., 0., 0.],
              'width_mm': 88.9, 'depth_mm': 139.7, 'all_openings_represented': True,
              'opening_records': [{'source': 'tab_end', 'kind': 'tab_notch',
                                   'section_box_sxq_mm': [-100., 0., 0., 44.45, -69.85, 69.85]}]}
    rows = {
        'lumber_leg_bolt_left_1': {'first': 'brace', 'second': 'host', 'point': [0., 0., 50.]},
        'knee_bolt_left_leg': {'first': 'brace', 'second': 'host', 'point': [0., 0., -50.]}}
    hardware = {name: {'hole_diameter_mm': 14.2875} for name in rows}
    native = {'width_mm': 88.9, 'depth_mm': 139.7, 'axis': [0., 0., 1.],
              'section_u': [1., 0., 0.], 'section_v': [0., 1., 0.]}
    data = {'member': native, 'sections': [{'origin_xyz_mm': [0., 0., -50.]}]}
    return member, rows, hardware, data


def test_partial_width_tab_and_both_bolt_families_are_retained():
    member, rows, hardware, _ = fixture()
    cuts = knee.cut_inventory('brace', member, rows, hardware)
    assert {r['source'] for r in cuts} == {'tab_end', *rows}
    active = [r['box_sxq_mm'][2:] for r in cuts if r['box_sxq_mm'][0] <= -50 <= r['box_sxq_mm'][1]]
    props = knee.bounded_section_properties(88.9, 139.7, active)
    # The through-hole and half-width notch overlap; subtract the union once.
    assert props['area_mm2'] == pytest.approx(44.45*(139.7-14.2875))


def test_intersected_tab_still_reports_unsampled_shoulders(monkeypatch):
    member, rows, hardware, data = fixture()
    geometry = {'members': {'brace': member, 'host': copy.deepcopy(member)},
                'hardware_by_name': hardware}
    report = {'member_section_demands': {'brace': data, 'host': copy.deepcopy(data)}}
    monkeypatch.setattr(knee, 'bounded_section_check', lambda *args:
                        {'conservative_net_section_envelope_ratio': .25})
    result = knee.sampled_sections(report, geometry, rows)['brace']
    notch = result['unsampled_notch_records'][0]
    assert notch['intersects_any_sample'] is True
    assert notch['unsampled_stations_mm'] == [-100., 0.]
    assert result['qualified_for_design'] is False
    del geometry['members']['host']
    with pytest.raises(ValueError, match='every upper and knee'):
        knee.sampled_sections(report, geometry, rows)
