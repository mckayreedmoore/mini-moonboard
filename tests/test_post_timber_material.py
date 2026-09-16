"""Separately classified posts must change both response and resistance inputs."""
import pytest

from fea.current_response_materials import df_l_no2_post_timber, materials
from fea.current_response_model import CurrentStructure
from fea.reinforced_timber_resistance import PSI_MPA, member_check, section_report
from fea.thick_leg_checks import bounded_section_check, bounded_section_properties


def test_post_deck_override_is_local_and_unknown_members_fail():
    original = materials()
    post = df_l_no2_post_timber()
    selected = dict(original, timber_by_name={'post': post['constants']})
    structure = CurrentStructure(selected)
    for name, x in (('post', 0.), ('rail', 300.)):
        structure.member({'name': name, 'start': [x, 0., 0.], 'end': [x, 0., 200.],
                          'section_u': [1., 0., 0.], 'width_mm': 139.7, 'depth_mm': 139.7})
    deck = structure.deck()
    assert '*SOLID SECTION,ELSET=post,MATERIAL=TIMBER_MEMBER_post,' in deck
    assert '*SOLID SECTION,ELSET=rail,MATERIAL=TIMBER,' in deck
    assert '*MATERIAL,NAME=TIMBER_MEMBER_rail' not in deck
    assert str(post['constants'][0]) in deck
    assert post['constants'][0] == pytest.approx(1_300_000*PSI_MPA)
    assert original['timber'][0] == pytest.approx(1_600_000*PSI_MPA)
    selected['timber_by_name']['typo'] = post['constants']
    with pytest.raises(ValueError, match='existing members'):
        structure.deck()


def test_lower_post_references_propagate_through_gross_and_sampled_net_checks():
    override = df_l_no2_post_timber()['reference_override']
    member = {'width_mm': 139.7, 'depth_mm': 139.7}
    section = {'axial_n_tension_positive': 10_000., 'moment_u_nmm': 100_000.,
               'moment_v_nmm': 10_000., 'shear_u_n': 100., 'shear_v_n': 500.,
               'torsion_nmm': 0., 'station_along_grain_mm': 100.,
               'include_station_loads': False}
    data = {'member': member, 'length_mm': 238.9, 'section_valid_from_mm': 0.,
            'force_residual_n': [0., 0., 0.], 'moment_residual_nmm': [0., 0., 0.],
            'sections': [section]}
    post_member = dict(member, reference_override=override)
    report = section_report({'member_section_demands': {
        'post': dict(data, member=post_member), 'rail': data}})
    post = report['post']['checks'][0]
    rail = report['rail']['checks'][0]
    assert post['references'] == override
    assert rail['references']['Fb_star_mpa'] == pytest.approx(900*1.3*PSI_MPA)
    assert post['tension_conservative_interaction'] > rail['tension_conservative_interaction']
    properties = bounded_section_properties(139.7, 139.7, [])
    net = bounded_section_check(data, post_member, section, properties)
    assert net['references'] == override
    assert net['tension_conservative_interaction'] == pytest.approx(post['tension_conservative_interaction'])
    noisy_square = dict(post_member, width_mm=139.70000000000005)
    assert bounded_section_check(data, noisy_square, section, properties)['references'] == override
    assert 'reference_override' not in member


@pytest.mark.parametrize('override', [{}, {'Fb_star_mpa': 1.},
                                     dict(df_l_no2_post_timber()['reference_override'], Emin_mpa=float('nan'))])
def test_incomplete_or_invalid_reference_override_fails(override):
    with pytest.raises(ValueError, match='six positive finite'):
        member_check(width_mm=139.7, depth_mm=139.7, axial_n=0.,
                     moment_strong_nmm=0., moment_weak_nmm=0., shear_strong_n=0.,
                     shear_weak_n=0., torsion_nmm=0., column_effective_strong_mm=200.,
                     column_effective_weak_mm=200., beam_effective_mm=300.,
                     reference_override=override)


def test_current_gross_comparison_rejects_load_hidden_by_dimension_lumber_values():
    from fea.current_response_resistance import member_comparisons

    member = {'width_mm': 139.7, 'depth_mm': 139.7}
    section = {'axial_n_tension_positive': 80_000., 'moment_u_nmm': 0.,
               'moment_v_nmm': 0., 'shear_u_n': 0., 'shear_v_n': 0.,
               'torsion_nmm': 0., 'station_along_grain_mm': 100.,
               'include_station_loads': False}
    data = {'member': member, 'length_mm': 238.9, 'section_valid_from_mm': 0.,
            'force_residual_n': [0., 0., 0.], 'moment_residual_nmm': [0., 0., 0.],
            'sections': [section]}
    post = dict(member, reference_override=df_l_no2_post_timber()['reference_override'])
    result = member_comparisons({'member_section_demands': {
        'post': dict(data, member=post), 'ordinary': data}})
    assert result['ordinary']['gross_section_peak']['necessary_gross_section_ratio'] < 1
    assert result['post']['gross_section_peak']['necessary_gross_section_ratio'] > 1


def test_actual_group_uses_post_shear_reference_and_lower_e_without_leaking():
    from scripts.compact_splice_results import local_groups

    rows, bolts, hardware, actual = {}, {}, {}, {}
    for index, z in enumerate((-75., -25., 25., 75.)):
        name = f'bolt_{index}'
        rows[name] = {'first': 'post', 'second': 'ordinary', 'point': [0., 0., z],
                      'force_on_first_xyz_n': [0., 0., 8500.],
                      'force_on_second_xyz_n': [0., 0., -8500.]}
        bolts[name] = {'diameter_mm': 9.525}
        hardware[name] = {'hole_diameter_mm': 11.1125}
        actual[name] = {'comparisons': {'actual_angle': {'ratio_CD_1': .5}}}
    member = {'grain': [0., 0., 1.], 'centre_mm': [0., 0., 0.],
              'width_mm': 139.7, 'depth_mm': 139.7,
              'end_stations_mm': [-500., 500.], 'additional_section_boxes': []}
    geometry = {'members': {'post': dict(member), 'ordinary': dict(member)},
                'geometries_by_bolt_name': bolts, 'hardware_by_name': hardware}
    old = next(iter(local_groups(rows, geometry, actual).values()))
    geometry['members']['post'].update(
        reference_override=df_l_no2_post_timber()['reference_override'],
        elastic_modulus_psi=1_300_000.)
    current = next(iter(local_groups(rows, geometry, actual).values()))
    assert old['member_checks']['post']['wood']['parallel_peak_ratio'] < 1
    assert current['member_checks']['post']['wood']['parallel_peak_ratio'] > 1
    assert current['member_checks']['ordinary'] == old['member_checks']['ordinary']
    assert current['additional_group_factor_sensitivity'] < old['additional_group_factor_sensitivity']
