"""Independent scalar witnesses and fail-closed thick-pivot inputs."""
import copy
import math

import pytest

from fea.current_response_resistance import VALIDITY
from fea.thick_leg_checks import assess, bolt_check

LEG = [0.,-.26015745792854417,.9655662054381139]
RIM = [0.,.6427876096865427,.7660444431189752]


def inputs():
    row = {'first':'rim','second':'leg','axis':[1.,0.,0.],
           'force_on_first_xyz_n':[3200*v for v in LEG],
           'force_on_second_xyz_n':[-3200*v for v in LEG]}
    geometry = {'diameter_mm':19.05,'bending_yield_psi':45000.,'members':{}}
    for name,grain in [('rim',RIM),('leg',LEG)]:
        geometry['members'][name] = {'grain':grain,'bearing_length_mm':88.9,
            'specific_gravity':.5,'parallel_bearing_psi':5600.,
            'edge_distances_mm':{'grain_positive':160.,'grain_negative':1000.,
                                 'depth_positive':60.,'depth_negative':79.7}}
    washer = {'outer_diameter_mm':60.,'hole_diameter_mm':21.,'seat_diameter_mm':30.,
              'thickness_mm':5.,'wood_bearing_mpa':4.3,'yield_mpa':227.,'safety_factor':1.67}
    hardware = {'tensile_area_mm2':215.,'shear_area_mm2':180.,'steel_yield_mpa':634.,
                'steel_safety_factor':2.,'washers':[washer.copy(),washer.copy()]}
    return row,geometry,hardware


def test_thick_pivot_all_modes_and_capacity_match_scalar_witness():
    result = bolt_check(*inputs())
    assert result['lateral_reference_n'] == pytest.approx(4369.674838922678)
    assert result['lateral_ratio'] == pytest.approx(.7323199363705846)
    assert result['dowel_reference']['governing_mode'] == 'IIIm'
    assert len(result['dowel_reference']['reference_values_lbf']) == 6
    assert result['bearing_lengths_mm'] == [88.9,88.9]
    assert result['placement']['rim']['margins_mm']['depth_negative'] == pytest.approx(3.5)
    assert result['qualified_for_design'] is False


def test_force_reversal_changes_loaded_edge_without_changing_dowel_capacity():
    row,geometry,hardware = inputs()
    original = bolt_check(row,geometry,hardware)
    row['force_on_first_xyz_n'],row['force_on_second_xyz_n'] = row['force_on_second_xyz_n'],row['force_on_first_xyz_n']
    reversed_result = bolt_check(row,geometry,hardware)
    assert reversed_result['lateral_ratio'] == pytest.approx(original['lateral_ratio'])
    assert reversed_result['placement']['rim']['passes_directional_screen'] is False
    assert original['placement']['rim']['passes_directional_screen'] is True


def test_actual_thickness_changes_modes_and_resistance():
    row,geometry,hardware = inputs()
    original = bolt_check(row,geometry,hardware)
    for member in geometry['members'].values():
        member['bearing_length_mm'] = 38.1
    thin = bolt_check(row,geometry,hardware)
    assert thin['lateral_reference_n'] < original['lateral_reference_n']
    assert thin['lateral_ratio'] > 1


def test_axial_increment_is_not_a_prying_bound_and_washers_are_independent():
    row,geometry,hardware = inputs()
    row['force_on_first_xyz_n'][0] = -1000.
    row['force_on_second_xyz_n'][0] = 1000.
    result = bolt_check(row,geometry,hardware)['hardware']
    assert result['absolute_axial_increment_n'] == 1000.
    assert result['preload_or_prying_bound_established'] is False
    assert result['washers'][0]['wood_bearing_ratio'] == pytest.approx(1000/(math.pi*(60**2-21**2)/4)/4.3)
    assert result['washers'][0] == result['washers'][1]


def test_bad_vectors_and_unmatched_inventory_rejected():
    row,geometry,hardware = inputs()
    bad = copy.deepcopy(row)
    bad['force_on_second_xyz_n'][0] = 1.
    with pytest.raises(ValueError,match='Action/reaction'):
        bolt_check(bad,geometry,hardware)
    report = {'candidate':'thick-pivot',**dict.fromkeys(VALIDITY,True),'physical_connection_forces':{'lumber_leg_bolt_left_1':row}}
    with pytest.raises(ValueError,match='inventory'):
        assess(report,{},hardware)
    for key in VALIDITY:
        invalid = dict(report,**{key:False})
        assert assess(invalid,{},hardware)['status'] == 'INVALID_RESPONSE_DIAGNOSTIC_ONLY'


@pytest.mark.parametrize('orientation', [-1.,1.])
def test_local_net_check_does_not_move_distant_holes_to_loaded_section(orientation):
    from fea.thick_leg_checks import assess_local

    row,_,_ = inputs()
    row['point'] = [0.,0.,500.]
    report = {'candidate':'thick-pivot',**dict.fromkeys(VALIDITY,True),
        'physical_connection_forces':{'lumber_leg_bolt_left_1':row},'member_section_demands':{}}
    members = {}
    for name in ('rim','leg'):
        members[name] = {'grain':[0.,0.,1.],'centre_mm':[0.,0.,0.],
            'end_stations_mm':[0.,2000.],'width_mm':88.9,'depth_mm':139.7,
            'additional_section_boxes':[(1000.,40.,40.)],
            'section_cut_boxes':[(980.,1020.,-44.45,44.45,20.,60.)],'openings_complete':False}
        section = {'origin_xyz_mm':[0.,0.,500.],'station_along_grain_mm':500.,
            'axial_n_tension_positive':-1000.,'moment_u_nmm':100000.,'moment_v_nmm':1000.,
            'shear_u_n':50.,'shear_v_n':100.,'torsion_nmm':0.,'include_station_loads':True}
        report['member_section_demands'][name] = {'member':{'width_mm':88.9,'depth_mm':139.7,'axis':[0.,0.,1.],
                'section_u':[orientation,0.,0.],'section_v':[0.,orientation,0.]},
            'length_mm':2000.,'sections':[section]}
    result = assess_local(report,members,hole_diameter_mm=17.4625)
    member = result['local_members']['leg']
    assert member['sampled_net_peak']['active_hole_count'] == 1
    assert member['sampled_net_peak']['actual_area_mm2'] == pytest.approx(88.9*(139.7-17.4625))
    assert member['all_opening_centres_sampled'] is False
    assert member['all_openings_represented'] is False
    assert member['joint_wood']['splitting_peak_ratio'] >= 0
    assert result['qualified_for_design'] is False


def test_partial_width_screw_preserves_actual_net_geometry():
    from fea.thick_leg_checks import bounded_section_properties

    b,d = 88.9,139.7
    rectangle = [23.3299,27.4701,36.3062499,69.8500001]
    net = bounded_section_properties(b,d,[rectangle])
    full_width = bounded_section_properties(b,d,[[-b/2,b/2,rectangle[2],rectangle[3]]])
    assert net['area_mm2'] == pytest.approx(b*d-4.1402*(69.85-36.3062499))
    assert net['strong_modulus_mm3'] > 2*full_width['strong_modulus_mm3']
    assert net['second_moments_u2_v2_uv_mm4'][2] != 0
    assert net == bounded_section_properties(b,d,[rectangle,rectangle])


def test_rectangle_section_matches_intact_and_centered_hole_reference():
    from fea.thick_leg_checks import bounded_section_properties

    b,d,h = 88.9,139.7,17.4625
    intact = bounded_section_properties(b,d,[])
    assert intact['strong_modulus_mm3'] == pytest.approx(b*d*d/6)
    assert intact['weak_modulus_mm3'] == pytest.approx(d*b*b/6)
    hole = bounded_section_properties(b,d,[[-b/2,b/2,-h/2,h/2]])
    assert hole['strong_modulus_mm3'] == pytest.approx(b*(d**3-h**3)/(6*d))
    assert hole['weak_modulus_mm3'] == pytest.approx((d-h)*b*b/6)
