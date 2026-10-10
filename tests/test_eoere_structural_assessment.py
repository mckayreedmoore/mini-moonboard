"""Thread occupancy is a geometric bound, never a current resistance result."""

import copy
import csv
import json
from collections import Counter

import pytest

from scripts import eoere_structural_assessment as assessment


@pytest.mark.parametrize('interval,body,expected', [
    ((10, 50), 60, (0, 0)), ((10, 50), 0, (40, 1)),
    ((10, 50), 40, (10, .25)), ((10, 50), 39, (11, .275)),
    ((8.9916, 47.0916), 30.226, (16.8656, .4426666666666667)),
])
def test_intersection_known_answers_and_quarter_boundary(interval, body, expected):
    assert assessment.potential_thread_fraction(*interval, body) == pytest.approx(expected)


@pytest.mark.parametrize('values', [
    (10, 10, 5), (-1, 10, 5), (10, 20, -1), (10, 20, True),
    (10, float('inf'), 5), (float('nan'), 20, 5), (10, 20, 'nan'),
])
def test_invalid_geometry_cannot_become_a_thread_bound(values):
    with pytest.raises(ValueError):
        assessment.potential_thread_fraction(*values)


@pytest.mark.parametrize('body,expected', [
    (40, 'POTENTIAL_OCCUPANCY_WITHIN_QUARTER'),
    (39.6, 'POTENTIAL_OCCUPANCY_EXCEEDS_QUARTER'),
    (50, 'NOMINAL_SMOOTH_BODY_COVERS_WOOD'),
])
def test_stack_disposition_at_quarter_above_quarter_and_full_coverage(body, expected):
    # Independent 40-mm wood interval at underhead stations 10..50 mm.
    selection = {'axis_id': 'A', 'receiver_member_ids': 'wood', 'minimum_body_mm': body,
                 'selected_underhead_length_mm': 70,
                 'body_to_farthest_wood_plate_end_margin_mm': body - 50}
    stack = {'axis_id': 'A', 'receiver_member_ids': 'wood',
             'catalog_each_washer_max_mm': 10, 'head_side_plate_mm': 0, 'nut_side_plate_mm': 0}
    wood = {'axis_id': 'A', 'receiver': 'wood', 'entry_from_axis_point_mm': 0,
            'exit_from_axis_point_mm': 40, 'saved_full_wall_length_mm': 40}
    row, = assessment.thread_inventory([selection], [stack], [wood])
    assert row['catalog_envelope_disposition'] == expected
    assert row['maximum_potential_fraction'] == pytest.approx((50 - body) / 40)


@pytest.fixture
def issued_tables():
    paths = [assessment.CURRENT_SHOP / 'hardware-selection.csv',
             assessment.SHOP / 'bolt-stacks.csv', assessment.SHOP / 'receiver-holes.csv']
    tables = []
    for path in paths:
        with (assessment.ROOT / path).open(newline='') as stream:
            tables.append(list(csv.DictReader(stream)))
    return tables


def test_all_current_rows_join_to_catalog_datums_without_claiming_capacity(issued_tables):
    rows = assessment.thread_inventory(*issued_tables)
    assert len(rows) == 100
    assert sum(len(row['members']) for row in rows) == 120
    assert Counter(row['catalog_envelope_disposition'] for row in rows) == {
        'POTENTIAL_OCCUPANCY_EXCEEDS_QUARTER': 68,
        'POTENTIAL_OCCUPANCY_WITHIN_QUARTER': 24,
        'NOMINAL_SMOOTH_BODY_COVERS_WOOD': 8,
    }
    assert all(row['actual_thread_fraction'] is row['current_capacity'] is None for row in rows)
    # A shared header has one wood member between two plates, not two timbers.
    header = next(row for row in rows if row['axis_id'] == 'eoere_bolt_065')
    assert len(header['members']) == 1
    assert header['nut_plate_mm'] == pytest.approx(6.35)
    assert header['members'][0]['underhead_interval_mm'] == pytest.approx([8.9916, 47.0916])
    assert header['minimum_body_mm'] - (47.0916 + header['nut_plate_mm']) == pytest.approx(2.1844)
    assert header['maximum_potential_fraction'] == 0
    cleat = next(row for row in rows if row['axis_id'] == 'eoere_bolt_067')
    assert cleat['maximum_potential_fraction'] == pytest.approx(.276)


def test_axis_point_translation_preserves_underhead_bearing_intervals(issued_tables):
    original = assessment.thread_inventory(*issued_tables)
    for row in issued_tables[2]:
        for key in ('entry_from_axis_point_mm', 'exit_from_axis_point_mm'):
            row[key] = str(float(row[key]) + 100)
    translated = assessment.thread_inventory(*issued_tables)
    for first, second in zip(original, translated, strict=True):
        assert first['maximum_potential_fraction'] == pytest.approx(second['maximum_potential_fraction'])
        for a, b in zip(first['members'], second['members'], strict=True):
            assert a['underhead_interval_mm'] == pytest.approx(b['underhead_interval_mm'])


@pytest.mark.parametrize('mutation', [
    lambda tables: tables[0].append(copy.deepcopy(tables[0][0])),
    lambda tables: tables[2].pop(),
    lambda tables: tables[2][0].update(receiver='foreign'),
    lambda tables: tables[1][0].update(head_side_plate_mm='0'),
    lambda tables: tables[0][0].update(body_to_farthest_wood_plate_end_margin_mm='0'),
    lambda tables: tables[2][0].update(saved_full_wall_length_mm='1'),
])
def test_missing_duplicate_or_reinterpreted_issued_geometry_is_rejected(issued_tables, mutation):
    mutation(issued_tables)
    with pytest.raises(ValueError):
        assessment.thread_inventory(*issued_tables)


def test_issued_assessment_keeps_reference_exceedances_and_unknowns_distinct(issued_tables):
    path = assessment.ROOT / assessment.PACKET / 'structural-assessment.json'
    report = json.loads(path.read_text())
    assert report['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
    assert report['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
    assert report['extra_grid'] is False
    assert report['thread_method']['threshold'] == .25
    assert report['structural_acceptance'] is report['historical_pass_transferred'] is False
    assert report['remedies_attempted'] is report['native_solve_performed'] is False
    assert report['geometry_or_hardware_changed'] is False
    assert report['actual_build_fit_work_excluded_by_owner'] is True
    references = report['preceding_reference_comparisons']
    assert references['applies_to_current_model'] is False
    assert references['complete_joint_resistance'] is None
    assert len(references['saved_reference_exceedances']) == 40
    assert {row['family'] for row in references['governing_own_case_witnesses']} == {
        'generic_screw_head_CD1', 'generic_required_thread_over_gross_penetration_CD1',
        'panel_bending_x_CD1', 'panel_bending_y_CD1', 'panel_rolling_x_CD1',
        'panel_rolling_y_CD1', 'heel_t6_r6', 'heel_t6p35_r6p35',
    }
    assert {row['case'] for row in references['other_saved_exceedance_and_sensitivity_disclosures']} == {
        'a12-forward', 'a12-rear', 'a12-left', 'k12-right', 'k12-rear', 'a1-rear',
    }
    assert all(row['ratio'] > 1 for row in references['saved_reference_exceedances'])
    assert report['thread_catalog_envelope_counts'] == Counter(
        row['catalog_envelope_disposition'] for row in report['thread_stacks'])
    previous = json.loads((assessment.ROOT / assessment.PACKET / 'mechanics-review.json').read_text())
    assert report['current_unresolved_modes'] == previous['unresolved']
    assert all(row['current_resistance'] is None for row in report['current_unresolved_modes'])
    contact = report['spacer_contact']
    assert contact['current_resistance'] is contact['current_axial_actions'] is None
    assert contact['nominal_projection_areas_mm2'] == previous['nominal_projection_areas_mm2']
    assert contact['mean_pressure_mpa_per_1000n_centered_axial_force'] == pytest.approx({
        'spacer_annulus': 4.96533132, 'washer_spacer_overlap': 5.31813118,
        'ideal_hex_nut_spacer_overlap': 10.73450430,
    }, rel=1e-8)
    assert report['thread_stacks'] == assessment.thread_inventory(*issued_tables)


def test_reference_summary_retains_exceedances_and_indivisible_own_case_witnesses():
    cases = []
    for label, head_ratio, thread, gross, panel_ratio, heel_ratio in [
        ('A', 2, 60, 40, 3, .9), ('B', 1.5, 100, 50, .5, 1.1),
    ]:
        head = {'axis_id': label + '-head', 'generic_head_ratio_CD1': head_ratio,
                'withdrawal_n': 10 if label == 'A' else 20}
        withdrawal = {'axis_id': label + '-thread',
                      'generic_withdrawal_required_effective_thread_mm_CD1': thread,
                      'gross_nominal_length_after_panel_mm': gross}
        rich = {
            'steel_scenarios': [{'comparison': {'id': 'test'}, 'summary': {
                'radius_conditioned_heel_component_with_gravity': {
                    'worst': {'conditional_combined_yield_reference_ratio': heel_ratio,
                              'body': label + '-angle'},
                    'exceedance_count': int(heel_ratio > 1),
                    'exceedances': [label] if heel_ratio > 1 else [],
                }}}],
            'timber': {'summary': {'unadjusted_exceedance_axis_ids': [label + '-wood'],
                                  'Cdelta0p5_Cg1_CD1_sensitivity_exceedance_axis_ids': [label + '-sensitivity'],
                                  'worst_component': {'axis_id': label}}},
            'shaft': {'first_yield_reference_exceedances': [label + '-shaft']},
            'washers': {'exceeded_reference_diagnostics': {'test': [label + '-washer']}},
        }
        cases.append({'case_id': label, 'coarse': {'findings': {
            'generic_screw_references': {
                'generic_head_ratio_CD1': head,
                'generic_withdrawal_required_effective_thread_mm_CD1': withdrawal,
                'generic_CD1_head_exceedance_axis_ids': [label + '-head'],
            },
            'panels': {'per_panel': [{'panel': label + '-panel', 'section_components': {
                'bending_x': {'sampled_ratio_CD1': panel_ratio, 'xy_mm': [1, 2]},
            }}]},
        }}, 'rich': {'findings': rich}})
    source = {'current_geometry': {'revision': 'preceding'}, 'cases': cases}
    original = copy.deepcopy(source)
    result = assessment.reference_comparisons(source)
    assert source == original
    assert result['recorded_geometry'] == {'revision': 'preceding'}
    assert result['applies_to_current_model'] is False
    assert result['complete_joint_resistance'] is None
    maxima = {row['family']: row for row in result['governing_own_case_witnesses']}
    assert maxima['generic_screw_head_CD1'] == {
        'case': 'A', 'family': 'generic_screw_head_CD1', 'ratio': 2,
        'witness': {'axis_id': 'A-head', 'generic_head_ratio_CD1': 2, 'withdrawal_n': 10},
    }
    assert maxima['generic_required_thread_over_gross_penetration_CD1']['case'] == 'B'
    assert maxima['generic_required_thread_over_gross_penetration_CD1']['ratio'] == 2
    assert maxima['generic_required_thread_over_gross_penetration_CD1']['witness']['axis_id'] == 'B-thread'
    assert maxima['panel_bending_x_CD1']['witness']['panel'] == 'A-panel'
    assert maxima['heel_test']['witness']['body'] == 'B-angle'
    assert len(result['saved_reference_exceedances']) == 6
    assert all(row['ratio'] > 1 for row in result['saved_reference_exceedances'])
    disclosures = result['other_saved_exceedance_and_sensitivity_disclosures']
    assert len(disclosures) == 2
    assert disclosures[0]['shaft_first_yield_reference_exceedances'] == ['A-shaft']
    assert disclosures[1]['washer_reference_diagnostics'] == {'test': ['B-washer']}
    assert disclosures[1]['steel_reported_exceedances'][0]['categories'] == {
        'radius_conditioned_heel_component_with_gravity': ['B']}
    source['cases'][0]['coarse']['findings']['generic_screw_references']['generic_head_ratio_CD1']['generic_head_ratio_CD1'] = float('nan')
    with pytest.raises(ValueError, match='Invalid saved reference ratio'):
        assessment.reference_comparisons(source)
