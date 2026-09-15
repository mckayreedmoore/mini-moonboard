"""Residual-band diagnostics cannot silently qualify a re-entrant wood notch."""
from copy import deepcopy

import pytest

from scripts import floor_recess_checks as checks


def fixture_data(name='lumber_leg_left'):
    member = {'width_mm':88.9, 'depth_mm':139.7, 'grain':[0.,0.,1.], 'centre_mm':[0.,0.,0.],
        'opening_records':[{'source':'recess', 'kind':'tab_notch',
            'section_box_sxq_mm':[-100.,0.,-44.45,-6.35,-69.85,69.85]}]}
    data = {'member':{'name':name}, 'sections':[
        {'origin_xyz_mm':[0.,0.,z], 'axial_n_tension_positive':-123.} for z in (-50.,50.)]}
    return data, member


def test_continuous_band_keeps_eccentricity_above_shoulder_and_bore_removal(monkeypatch):
    data, member = fixture_data()
    def comparison(data, member, section, properties):
        assert section['axial_n_tension_positive'] == -123.
        return {'conservative_net_section_envelope_ratio':1/properties['area_mm2']}
    monkeypatch.setattr(checks, 'bounded_section_check', comparison)
    rows = {'rail_rear_bolt_left_1':{'first':'lumber_leg_left','second':'base_floor_left','point':[0.,0.,50.]}}
    result = checks.continuous_band_sections(data,member,rows,{'rail_rear_bolt_left_1':{'hole_diameter_mm':10.}})
    assert result['unbored_band_properties']['area_mm2'] == pytest.approx(50.8*139.7)
    assert result['unbored_band_properties']['centroid_uv_mm'] == pytest.approx([19.05,0.])
    assert result['sampled_sections'][0]['actual_cut_box_properties']['area_mm2'] == pytest.approx(50.8*139.7)
    # Even above the cut's end, the core-only diagnostic removes the entire band.
    assert result['sampled_sections'][1]['actual_cut_box_properties']['area_mm2'] == pytest.approx(50.8*(139.7-10.))
    assert result['local_notch_resistance_qualified'] is False


@pytest.mark.parametrize('box', [[-100.,0.,-44.45,44.45,-69.85,69.85],
    [-100.,0.,-19.05,19.05,-69.85,69.85], [-100.,0.,float('nan'),-6.35,-69.85,69.85]])
def test_reject_wrong_or_nonfinite_recess_geometry(box):
    data, member = fixture_data()
    member['opening_records'][0]['section_box_sxq_mm'] = box
    with pytest.raises(ValueError):
        checks.continuous_band_sections(data,member,{}, {})


def test_all_nominal_passes_do_not_waive_local_notch_gate(monkeypatch):
    monkeypatch.setattr(checks,'bounded_section_check',lambda *args:{'conservative_net_section_envelope_ratio':.1})
    report={'candidate':checks.CANDIDATE,'physical_connection_forces':{},'member_section_demands':{}}
    geometry={'candidate':checks.CANDIDATE,'members':{},'receiver_fit':[],'hardware_by_name':{}}
    sections={}
    for name in checks.LEGS:
        data,member=fixture_data(name)
        data['member'].update(native_section_geometry=checks.NATIVE_BASIS, retained_mesh_volume_mm3=100.,
            additional_recovery_stations_mm=[-50.,50.], floor_recess_geometry={
                'notch_top_z_mm':141.7,'retained_x_band_mm':[-6.35,44.45],
                'cut_inner_x_band_mm':[-44.45,-6.35], 'expected_retained_volume_mm3':100.,
                'expected_removed_volume_mm3':50.,'shoulder_bearing_credited':False})
        member['opening_records'][0]['actual_removed_volume_mm3']=50.
        report['member_section_demands'][name]=data
        geometry['members'][name]=member
        sections[name]={'all_openings_represented':True,
            'sampled_sections':[{'station_mm_from_cad_centre':v} for v in (-50.,50.)], 'cut_coverage':[
            {'kind':'tab_notch','unsampled_stations_mm':[]},{'kind':'bolt_bore','unsampled_stations_mm':[]}]}
        geometry['receiver_fit'] += [{'member':name,'bolt':f'rail_rear_bolt_{name}_{i}',
            'passes':True,'bearing_length_mm':50.8} for i in (1,2)]
    result=checks.checks(report,geometry,sections)
    assert result['criteria']['native_actual_recess'] is True
    assert result['criteria']['shoulder_bounds_sampled'] is True
    assert result['criteria']['continuous_band_nominal_resistance'] is True
    assert result['criteria']['local_notch_corner_resistance'] is False
    assert result['passes'] is False
    stale=deepcopy(report)
    del stale['member_section_demands'][checks.LEGS[0]]['member']['native_section_geometry']
    assert checks.checks(stale,geometry,sections)['criteria']['native_actual_recess'] is False
