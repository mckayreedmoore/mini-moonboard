"""Portable exact-case process provenance for the current structural summary."""

import contextlib
import copy
import json
from types import SimpleNamespace

import pytest

from scripts import summarize_eoere_current_components as summary


def fixture(monkeypatch, tmp_path):
    monkeypatch.setattr(summary.current, "ROOT", tmp_path)
    producer = {"path": "component.py", "sha256": "c"}
    monkeypatch.setattr(summary.component, "own_ref", lambda: producer)
    release = {"structural_released": False}
    force = {"geometry": {"path": "geometry", "sha256": "g"},
             "hardware_model": {"path": "hardware", "sha256": "h"}, "release": release}
    binding = {"case_id": "a12-forward", "state_id": "own-state", "field": {"path": "field", "sha256": "f"},
               "admission": {"path": "admission", "sha256": "a"}}
    result_ref, input_ref = {"path": "components.json", "sha256": "r"}, {"path": "inputs", "sha256": "i"}
    data = {"schema": "eoere_selected_hardware_current_component_case/v1", "producer": producer,
            **binding, **force, "complete_joint_resistance": None, "finished_member_capacity": None,
            "native_or_global_solve_performed": False, "historical_pass_or_actions_transferred": False}
    pins = {r["path"]: r["sha256"] for r in [producer, input_ref, binding["field"], binding["admission"]]}
    process = {"schema": "eoere_current_component_process_capture/v1", "case_id": binding["case_id"], "result": result_ref,
               "command": ["python", "-B", "-m", "scripts.eoere_current_components", "--case-id", binding["case_id"],
                           "--out", str(tmp_path/result_ref["path"])], "cwd": str(tmp_path),
               "controlled_environment": {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"},
               "status": "FINISHED", "exit_code": 0, "historical_state_or_actions_used": False,
               "pins_unchanged": True, "pins_before": pins, "pins_after": copy.deepcopy(pins),
               "started_at_utc": "2026-10-10T12:00:00+00:00", "finished_at_utc": "2026-10-10T12:00:30+00:00"}
    return data, process, binding, force, result_ref, input_ref


def test_saved_component_case_requires_exact_process_and_current_inputs(monkeypatch, tmp_path):
    summary.verify_saved_case(*fixture(monkeypatch, tmp_path))


def test_relocated_evidence_keeps_captured_cwd_and_repository_relative_identity(monkeypatch, tmp_path):
    args = fixture(monkeypatch, tmp_path)
    before = copy.deepcopy(args)
    monkeypatch.setattr(summary.current, "ROOT", tmp_path / "recovered-checkout")
    summary.verify_saved_case(*args)
    assert args == before
    # A changed capture root with the old command is still contradictory.
    args[1]["cwd"] = str(tmp_path / "other-execution")
    with pytest.raises(ValueError, match="successful own component process"):
        summary.verify_saved_case(*args)


@pytest.mark.parametrize("mutation", ["schema", "case", "state", "field", "admission", "geometry", "hardware", "producer",
                                      "release", "capacity", "native", "history"])
def test_foreign_or_accepted_component_cannot_join_current_summary(monkeypatch, tmp_path, mutation):
    args = list(fixture(monkeypatch, tmp_path))
    data = args[0]
    if mutation in ["schema", "case", "state"]:
        data[{"case": "case_id", "state": "state_id"}.get(mutation, mutation)] = "foreign"
    elif mutation in ["field", "admission", "geometry", "producer"]:
        data[mutation] = {"path": "foreign", "sha256": "x"}
    elif mutation == "hardware":
        data["hardware_model"] = {"path": "foreign", "sha256": "x"}
    elif mutation == "release":
        data["release"] = {"structural_released": True}
    elif mutation == "capacity":
        data["complete_joint_resistance"] = 123.
    elif mutation == "native":
        data["native_or_global_solve_performed"] = True
    else:
        data["historical_pass_or_actions_transferred"] = True
    with pytest.raises(ValueError):
        summary.verify_saved_case(*args)


@pytest.mark.parametrize("mutation", ["schema", "case", "result", "command_case", "command_out", "cwd", "environment",
                                      "status", "exit", "history", "pin_omitted", "pin_changed", "unchanged_flag", "timestamps"])
def test_failed_or_foreign_process_cannot_authenticate_current_component(monkeypatch, tmp_path, mutation):
    args = list(fixture(monkeypatch, tmp_path))
    process = args[1]
    if mutation in ["schema", "status", "cwd"]:
        process[mutation] = "foreign"
    elif mutation == "case":
        process["case_id"] = "foreign"
    elif mutation == "result":
        process["result"] = {"path": "foreign", "sha256": "x"}
    elif mutation.startswith("command_"):
        process["command"][5 if mutation == "command_case" else 7] = "foreign"
    elif mutation == "environment":
        process["controlled_environment"]["OMP_NUM_THREADS"] = "8"
    elif mutation == "exit":
        process["exit_code"] = 1
    elif mutation == "history":
        process["historical_state_or_actions_used"] = True
    elif mutation == "pin_omitted":
        del process["pins_before"][args[5]["path"]]
        process["pins_after"] = copy.deepcopy(process["pins_before"])
    elif mutation == "pin_changed":
        process["pins_after"][args[5]["path"]] = "changed"
    elif mutation == "unchanged_flag":
        process["pins_unchanged"] = False
    else:
        process["finished_at_utc"] = "2026-10-10T11:59:59+00:00"
    with pytest.raises(ValueError):
        summary.verify_saved_case(*args)


def sections_fixture(monkeypatch):
    producer = {"path": "sections.py", "sha256": "s"}
    monkeypatch.setattr(summary.section, "own_ref", lambda: producer)
    bindings = [{"case_id": case_id, "state_id": "own-"+case_id} for case_id in summary.SEQUENCE]
    rows = [{"member": "member-"+str(i % 22), "station_global_grain_projection_mm": float(i),
             "selection": {}, "finished_source": {"path": "solid", "sha256": "b"}, "gross_stock_area_mm2": 100.,
             "section_properties": {"finished_area_mm2": 90., "centroid_xyz_mm": [0., 0., 0.],
                                    "centroidal_area_moment_matrix_uv_mm4": [[1., 0.], [0., 1.]]},
             "case_comparisons": [{**b, "normal_reference": {"fully_braced_linear_normal_CD1_reference_index": .9 if i == 0 else .2},
                                   "necessary_mean_shear_over_CD1_Fv": .1} for b in bindings]} for i in range(38)]
    data = {"schema": "eoere_current_targeted_finished_sections/v1", "producer": producer,
            "selected_unique_planes": 38, "same_plane_case_comparisons": 228,
            "source_pins_and_fields_unchanged": True, "native_solve_or_CAD_rebuild": False,
            "continuous_finished_extrema_or_member_resistance": None, "tool_versions": {}, "limits": [],
            "finished_sections": rows}
    return data, {"path": "sections.json", "sha256": "r"}, bindings


@pytest.mark.parametrize('mutation', ['success', 'bad_admission', 'wrong_section_join', 'short_spacer', 'field_identity'])
def test_summary_orchestration_keeps_six_admitted_cases_and_exact_source_union(monkeypatch, tmp_path, mutation):
    current, component = summary.current, summary.component
    monkeypatch.setattr(current, 'ROOT', tmp_path)
    all_refs = {}
    def saved(name, value):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, allow_nan=False))
        ref = current.ref(path)
        all_refs[ref['path']] = ref['sha256']
        return ref
    force_producer = saved('force.py', 'force producer')
    monkeypatch.setattr(current, 'OWN', tmp_path / force_producer['path'])
    monkeypatch.setattr(current, 'LOADED_SHA', force_producer['sha256'])
    component_ref = saved('component.py', 'component producer')
    section_ref = saved('section.py', 'section producer')
    summary_ref = saved('summary.py', 'summary producer')
    canonical_ref = saved('canonical.py', 'canonical helper')
    helper_ref = saved('helper.py', 'frozen reductions stand-in')
    monkeypatch.setattr(component, 'own_ref', lambda: component_ref)
    monkeypatch.setattr(component, 'canonical_dependency', lambda: canonical_ref)
    monkeypatch.setattr(summary, 'own_ref', lambda: summary_ref)
    geometry, hardware = saved('geometry.json', {}), saved('hardware.json', {})
    release = {'structural_released': False, 'fabrication_released': False}
    monkeypatch.setattr(current, 'manifest', lambda: {'release': release, 'references': {'geometry': geometry, 'hardware': hardware}})
    static = {'spacer_contact': {'nominal_projection_areas_mm2': {'spacer_annulus': 200., 'washer_overlap': 180., 'nut_overlap': 100.}},
              'thread_catalog_envelope_counts': {'geometry_only': 100}, 'raised_screw_placement': {'axes_moved': 2}}
    monkeypatch.setattr(summary, 'STATIC', saved('static.json', static))
    sections, _, bindings = sections_fixture(monkeypatch)
    monkeypatch.setattr(summary.section, 'own_ref', lambda: section_ref)
    sections.update(producer=section_ref, geometry=geometry, hardware_model=hardware, extra_grid=False, release=release)
    fields = []
    for i, binding in enumerate(bindings):
        field = {'case_id': binding['case_id'], 'state_id': binding['state_id'], 'source_inputs': {'fixture_case_action': [11.*i, -13.*i, 17.+i]}}
        fields.append(field)
        binding.update(field=saved(f'fields/{i}.json', field), admission=saved(f'admissions/{i}.json', {'case_id': binding['case_id']}))
    forces = {'case_sequence': summary.SEQUENCE, 'cases': bindings, 'all_six_saved_field_admissions_pass': True,
              'geometry': geometry, 'hardware_model': hardware, 'extra_grid': False, 'release': release,
              'geometry_revision': 'fixture-geometry', 'hardware_revision': 'fixture-hardware'}
    force_ref = saved('forces.json', forces)
    inputs = saved('inputs.json', {'current_response': force_ref, 'methods': {'summary': helper_ref}})
    monkeypatch.setattr(component, 'INPUTS', tmp_path / inputs['path'])
    monkeypatch.setattr(component, 'RAW', tmp_path / 'raw')
    # Authenticate these shared sources through the saved section closure.
    sections['source_sha256'] = dict(all_refs)
    section_bindings, raw_outputs = [], []
    for i, (binding, field) in enumerate(zip(bindings, fields, strict=True)):
        case = binding['case_id']
        screws = [{'axis_id': 'screw-'+str(j), 'case_id': case, 'state_id': binding['state_id'],
                   'generic_head_ratio_CD1': (i+1)*.25+j*.01,
                   'generic_withdrawal_required_effective_thread_mm_CD1': 2.*i+j,
                   'gross_nominal_length_after_panel_mm': 30., 'same_axis_lateral_n': i*100.+j} for j in range(66)]
        timbers = [{'member': 'member-'+str(j), 'source_span_mm': 1000.+j, 'source_width_mm': 20., 'source_depth_mm': 30.,
                    'witnesses': {name: {'station_global_grain_projection_mm': i*10.+j+k,
                        'gross_CD1_comparison': {'full_length_K1_pin_end_normal_sensitivity': {
                            'interaction_ratio': (i+1)*.1+j*.001+k*.0001, 'ratio_exceeds_one': False}}}
                        for k, name in enumerate(['fully_braced_normal', 'sufficient_shear_torsion'])}} for j in range(22)]
        washers = [{'axis_id': 'bolt-'+str(j), 'capture_id': 'bolt-'+str(j)+'/nut-capture', 'host': 'host-'+str(j),
                    'N_n': (i+1)*1000.+j, 'spacer_bore_and_od_mm': [10.31875, 19.05],
                    'spacer_nominal_axial_mean_stress_mpa': (i+1)*1000.+j,
                    'spacer_strength_nut_contact_or_compatible_pressure_bound': None, 'washer_loading_basis': 'fixture-own-annulus',
                    'nominal_own_hardware_geometry': {'ID_mm': 11., 'OD_mm': 25., 't_mm': 2.,
                        'uniform_load_ring_outer_radius_mm': 19.05/2, 'sampled_axial_only_Fy_required_mpa': i+j/10.,
                        'raw_ring_Fc_perp625psi_mean_ratio_conditional': None, 'physical_contact_pressure_bound_mpa': None,
                        'actual_product_Fy_mpa': None, 'combined_washer_strength_index': None}} for j in range(8)]
        if mutation == 'short_spacer' and i == 2:
            washers.pop()
        data = {'schema': 'eoere_selected_hardware_current_component_case/v1', 'producer': component_ref,
                **binding, 'geometry': geometry, 'hardware_model': hardware, 'release': release,
                'complete_joint_resistance': None, 'finished_member_capacity': None,
                'native_or_global_solve_performed': False, 'historical_pass_or_actions_transferred': False,
                'source_inputs_canonical_sha256': summary.canonical_sha(field['source_inputs']),
                'raw_field_canonical_sha256': summary.canonical_sha(field),
                'component_reductions': {'simultaneous_Hillman_actions_and_generic_references': screws,
                                        'fresh_gross_member_diagnostics': timbers},
                'findings': {'rich_steel': [], 'washers': {'all200_own_end_diagnostics': [{'unspaced': True}, *washers]}},
                'connected_mixed_stack_statics': {'own_surface_trials': [{'fixture_trial': j} for j in range(24)],
                                                'fixture_case': case, 'compatible_threaded_contact_or_yield_capacity': None},
                'support_screen': {'fixture_case': case, 'actual_no_slip_or_overturning_qualified': False},
                'source_sha256': {component_ref['path']: component_ref['sha256']}}
        if mutation == 'field_identity' and i == 2:
            data['raw_field_canonical_sha256'] = summary.canonical_sha(fields[0])
        folder = f'raw/cases-v1/{case}/{component.CASE_ATTEMPT}/'
        pointer = saved(folder+'components.json', data)
        source_pins = {r['path']: r['sha256'] for r in [component_ref, inputs, binding['field'], binding['admission']]}
        process = {'schema': 'eoere_current_component_process_capture/v1', 'case_id': case, 'result': pointer,
                   'command': ['python', '-B', '-m', 'scripts.eoere_current_components', '--case-id', case,
                               '--out', str(tmp_path/pointer['path'])], 'cwd': str(tmp_path),
                   'controlled_environment': {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'},
                   'status': 'FINISHED', 'exit_code': 0, 'historical_state_or_actions_used': False,
                   'pins_unchanged': True, 'pins_before': source_pins, 'pins_after': copy.deepcopy(source_pins),
                   'started_at_utc': '2026-10-10T12:00:00+00:00', 'finished_at_utc': '2026-10-10T12:00:01+00:00',
                   'logs': {name: saved(folder+name+'.json', {'fixture_log': name}) for name in ['stdout', 'stderr']}}
        saved(folder+'process.json', process)
        section_bindings.append({**binding, 'components': pointer})
        raw_outputs.append(data)
    sections['cases'] = section_bindings
    if mutation == 'wrong_section_join':
        sections['cases'][2]['components'] = section_bindings[0]['components']
    sections_ref = saved('sections.json', sections)
    events = []
    def admission(raw, receipt, *, admission_sha256):
        field = json.loads(raw)
        assert admission_sha256 == force_producer['sha256'] and receipt['case_id'] == field['case_id']
        events.append(('gate', field['case_id']))
        if mutation == 'bad_admission' and field['case_id'] == summary.SEQUENCE[2]:
            raise ValueError('fixture admission rejected')
        return field, {force_producer['path']: force_producer['sha256']}
    @contextlib.contextmanager
    def response_context():
        yield SimpleNamespace(require_admitted_payload=admission), None
    monkeypatch.setattr(current, 'response_context', response_context)
    def coarse(data):
        assert events[-1] == ('gate', data['case_id']) and data['limits'] == summary.LIMITS
        events.append(('coarse', data['case_id']))
        return {'generic_screw_references': {'fixture_case': data['case_id']}}
    def rich(data):
        assert events[-1] == ('coarse', data['case_id'])
        events.append(('rich', data['case_id']))
        return {'steel_scenarios': [], 'fixture_case': data['case_id']}
    def load(ref, name):
        assert ref == helper_ref and name == 'current_saved_summary'
        return SimpleNamespace(coarse_findings=coarse, rich_findings=rich)
    monkeypatch.setattr(component, 'load', load)
    if mutation != 'success':
        with pytest.raises(ValueError):
            summary.summarize(sections_ref)
        assert all(case in summary.SEQUENCE[:3] for _, case in events)
        expected_tail = {'bad_admission': [('gate', summary.SEQUENCE[2])],
                         'field_identity': [('gate', summary.SEQUENCE[2])],
                         'wrong_section_join': [],
                         'short_spacer': [('gate', summary.SEQUENCE[2]), ('coarse', summary.SEQUENCE[2]), ('rich', summary.SEQUENCE[2])]}
        assert events == [(kind, case) for case in summary.SEQUENCE[:2] for kind in ['gate', 'coarse', 'rich']] + expected_tail[mutation]
        return
    result, pins = summary.summarize(sections_ref)
    assert pins == all_refs
    assert events == [(kind, case) for case in summary.SEQUENCE for kind in ['gate', 'coarse', 'rich']]
    assert result['case_sequence'] == summary.SEQUENCE and [r['case_id'] for r in result['cases']] == summary.SEQUENCE
    assert result['targeted_finished_sections']['same_plane_case_comparisons'] == 228
    for i, (row, data) in enumerate(zip(result['cases'], raw_outputs, strict=True)):
        assert row['state_id'] == fields[i]['state_id'] and row['field'] == bindings[i]['field']
        assert row['coarse']['generic_screw_references']['all_screw_reference_scalars'] == summary.screw_exceedances(
            data['component_reductions']['simultaneous_Hillman_actions_and_generic_references'])['all_screw_reference_scalars']
        assert row['coarse']['generic_screw_references']['fixture_case'] == row['rich']['fixture_case'] == summary.SEQUENCE[i]
        assert len(row['spacer_nuts']) == 8
        for j, spacer in enumerate(row['spacer_nuts']):
            force = (i+1)*1000.+j
            assert spacer['axis_id'] == 'bolt-'+str(j) and spacer['N_n'] == force
            assert spacer['ideal_projected_mean_pressure_mpa'] == {k: force/v for k, v in static['spacer_contact']['nominal_projection_areas_mm2'].items()}
            assert spacer['nominal_washer_ring_reference'] == data['findings']['washers']['all200_own_end_diagnostics'][j+1]['nominal_own_hardware_geometry']
            assert spacer['spacer_strength_nut_contact_or_compatible_pressure_bound'] is None
        assert row['mixed_stack_statics'] == {'own_surface_count': 24, 'fixture_case': summary.SEQUENCE[i], 'compatible_threaded_contact_or_yield_capacity': None}
        assert row['support_screen'] == data['support_screen']
        stability = row['gross_member_stability']
        assert stability['member_count'] == 22 and stability['saved_sampled_witness_count'] == 44
        assert stability['largest_saved_K1_normal_sensitivity']['interaction_ratio'] == pytest.approx((i+1)*.1+.021+.0001)
    for key in ['complete_joint_resistance', 'finished_member_capacity', 'Hillman_product_capacity']:
        assert result[key] is None
    assert result['release'] == release and result['structural_acceptance'] is False
    assert len(result['missing_inputs']) == 8
    for ref in [force_ref, sections_ref, inputs]:
        assert current.read(ref) is not None


def test_finished_findings_preserve_exact_current_states_and_unique_planes(monkeypatch):
    data, pointer, bindings = sections_fixture(monkeypatch)
    result = summary.finished_findings(data, pointer, bindings)
    assert len(result["planes"]) == 38
    assert len(result["per_case_worst_witnesses"]) == 6
    assert result["maximum_normal_reference"]["state_id"] == bindings[0]["state_id"]


@pytest.mark.parametrize("comparison_index", [0, 1, 113, 227])
def test_foreign_state_rejects_even_on_discarded_nonworst_plane(monkeypatch, comparison_index):
    data, pointer, bindings = sections_fixture(monkeypatch)
    plane_index, case_index = divmod(comparison_index, 6)
    data["finished_sections"][plane_index]["case_comparisons"][case_index]["state_id"] = "foreign-old-state"
    with pytest.raises(ValueError, match="same admitted case/state"):
        summary.finished_findings(data, pointer, bindings)


def test_duplicate_finished_plane_rejects_even_with_exact_counts(monkeypatch):
    data, pointer, bindings = sections_fixture(monkeypatch)
    data["finished_sections"][-1] = copy.deepcopy(data["finished_sections"][-2])
    with pytest.raises(ValueError, match="all current members and selected planes"):
        summary.finished_findings(data, pointer, bindings)


def test_section_states_must_match_given_current_bindings(monkeypatch):
    data, pointer, bindings = sections_fixture(monkeypatch)
    bindings[0]["state_id"] = "different-admitted-state"
    with pytest.raises(ValueError, match="same admitted case/state"):
        summary.finished_findings(data, pointer, bindings)


def test_foreign_case_at_finished_plane_rejects(monkeypatch):
    data, pointer, bindings = sections_fixture(monkeypatch)
    data["finished_sections"][-1]["case_comparisons"][-1]["case_id"] = "foreign-case"
    with pytest.raises(ValueError, match="six own cases"):
        summary.finished_findings(data, pointer, bindings)


def test_screw_thresholds_keep_every_exceeding_axis_and_whole_thread_witness():
    rows = [{"axis_id": axis, "generic_head_ratio_CD1": head,
             "generic_withdrawal_required_effective_thread_mm_CD1": thread,
             "gross_nominal_length_after_panel_mm": 10., "state_id": "own-state",
             "case_id": "own-case", "same_axis_simultaneous_lateral_n": lateral}
            for axis, head, thread, lateral in [("below", .9, 9., 300.), ("equal", 1., 10., 200.),
                                               ("above", 1.01, 10.01, 100.), ("thread-only", .4, 15., 400.),
                                               ("head-only", 1.5, 8., 500.)]]
    before = copy.deepcopy(rows)
    result = summary.screw_exceedances(rows)
    assert result["generic_CD1_head_exceedance_axis_ids"] == ["above", "head-only"]
    assert result["all_screw_reference_scalars"] == [
        {"axis_id": axis, "generic_head_ratio_CD1": ratio, "generic_withdrawal_required_effective_thread_mm_CD1": thread,
         "gross_nominal_length_after_panel_mm": 10., "effective_thread_exceedance_witness": rows[i] if thread > 10. else None}
        for i, (axis, ratio, thread) in enumerate(
        [("below", .9, 9.), ("equal", 1., 10.), ("above", 1.01, 10.01), ("thread-only", .4, 15.), ("head-only", 1.5, 8.)])]
    assert result["all_effective_thread_length_reference_exceedances"] == [rows[2], rows[3]]
    assert result["reference_counts"] == {"axes": 5, "generic_CD1_head_exceedances": 2, "effective_thread_length_exceedances": 2}
    assert rows == before


def test_stability_census_preserves_whole_witnesses_strict_thresholds_and_domain_limits():
    def witness(station, ratio):
        return {"station_global_grain_projection_mm": station, "gross_CD1_comparison": {
            "full_length_K1_pin_end_normal_sensitivity": {"interaction_ratio": ratio, "ratio_exceeds_one": ratio > 1.,
                "within_slenderness_limits": False, "ratio_qualified_inside_declared_stability_domain": False,
                "Euler_denominators_positive": True, "stress_compression_tension_strong_weak_mpa": [station, 3., 4., 5.]}}}
    rows = [{"member": member, "source_span_mm": span, "source_width_mm": 10., "source_depth_mm": 20.,
             "witnesses": {"fully_braced_normal": witness(station, normal),
                           "sufficient_shear_torsion": witness(station+1., shear)}}
            for member, span, station, normal, shear in [('below', 499., 7., .9, 1.), ('equal', 500., 11., 1., 1.2),
                                                       ('above', 501., 17., 1.3, 1.1)]]
    before = copy.deepcopy(rows)
    result = summary.stability_findings(rows)
    records = result['all_member_witness_records']
    assert result['member_count'] == 3 and result['saved_sampled_witness_count'] == 6
    assert [r['member'] for r in records] == ['below', 'equal', 'above']
    for saved, source in zip(records, rows, strict=True):
        assert saved['span_mm'] == source['source_span_mm']
        assert saved['weak_column_domain_limit_mm'] == 500.
        assert saved['full_length_over_weak_column_domain_limit'] == source['source_span_mm']/500.
        assert saved['actual_restraint_or_complete_resistance'] is None
        assert saved['two_saved_witness_sensitivities'] == [
            {'witness': name, 'station_global_grain_projection_mm': value['station_global_grain_projection_mm'],
             **value['gross_CD1_comparison']['full_length_K1_pin_end_normal_sensitivity']}
            for name, value in source['witnesses'].items()]
    assert result['full_length_domain_exceedances'] == [{
        'member': 'above', 'span_mm': 501., 'weak_column_domain_limit_mm': 500., 'full_length_over_weak_column_domain_limit': 1.002}]
    expected = [{'member': records[i]['member'], **records[i]['two_saved_witness_sensitivities'][j]}
                for i, j in [(1, 1), (2, 0), (2, 1)]]
    assert result['saved_witness_reference_exceedances'] == expected
    assert result['largest_saved_K1_normal_sensitivity'] == expected[1]
    assert rows == before


def test_steel_disclosure_keeps_all_category_values_and_whole_nonworst_exceedances():
    metric = 'conditional_combined_yield_reference_ratio'
    categories = {
        'physical_cut_nominal_combined': (metric, [.8, 1., 1.3, 1.2]),
        'near_hole_nominal_combined': (metric, [.2, .3, .4, .5]),
        'far_hole_nominal_combined': (metric, [.6, .7, .8, .9]),
        'radius_conditioned_heel_component_with_gravity': (metric, [.9, 1., 1.1, 1.4]),
        'separate_whole_flange_torsion_warping': (metric, [.5, 1.6, 1., .9]),
        'used_hole_bearing': ('bearing_reference_ratio', [.9, 1., 1.2, 1.1]),
        'used_hole_tearout': ('tearout_reference_ratio', [.1, .2, .3, .4]),
        'unused_near_hole_net_shear': ('net_shear_rupture_reference_ratio', [1.4, 1.1, 1., .8]),
    }
    def value(name, i):
        key, values = categories[name]
        return {key: values[i]}
    angles = [{'bands': [{
        'governing': {'governing_combined': value('physical_cut_nominal_combined', i)},
        'near_hole': {'governing_combined': value('near_hole_nominal_combined', i)},
        'far_hole': {'governing_combined': value('far_hole_nominal_combined', i)},
        'heel_component': value('radius_conditioned_heel_component_with_gravity', i),
        'unused_near_hole_center': value('unused_near_hole_net_shear', i)}],
        'used_hole_bearing_tearout': [value('used_hole_bearing', i) | value('used_hole_tearout', i)],
        'whole_flange_torsion_warping_references': [value('separate_whole_flange_torsion_warping', i)]} for i in range(4)]
    saved, compact = [], []
    for identity in ['t6_r6', 't6p35_r6p35']:
        saved.append({'comparison': {'id': identity}, 'angles': copy.deepcopy(angles)})
        stats = {}
        for name, (key, values) in categories.items():
            witnesses = [{key: v, 'saved_metric': key, 'body': 'own-'+str(i), 'same_case_action': [7.*i, 1.-i]}
                         for i, v in enumerate(values)]
            stats[name] = {'comparison_count': 4, 'exceedance_count': sum(v > 1. for v in values),
                           'worst': max(witnesses, key=lambda w: w[key]), 'exceedances': [w for w in witnesses if w[key] > 1.]}
        compact.append({'comparison': {'id': identity}, 'summary': stats})
    before = copy.deepcopy(saved)
    summary.add_steel_disclosures(saved, compact)
    assert saved == before
    for scenario in compact:
        for name, (_, values) in categories.items():
            assert scenario['summary'][name]['all_reference_values'] == values
            assert scenario['summary'][name]['whole_exceedance_witness_bindings'] == scenario['summary'][name]['exceedances']
    assert [w['body'] for w in compact[0]['summary']['radius_conditioned_heel_component_with_gravity']['whole_exceedance_witness_bindings']] == ['own-2', 'own-3']


def test_finished_exceedances_use_strict_thresholds_and_whole_same_case_witnesses(monkeypatch):
    data, pointer, bindings = sections_fixture(monkeypatch)
    for plane_index, case_index, normal, shear in [(7, 1, 1.25, .4), (8, 2, 1., .2), (9, 3, .999, .3), (10, 1, 1.1, .7),
                                                 (17, 4, .5, 1.5), (18, 5, .6, 1.), (19, 0, .7, .999), (20, 4, .8, 1.1)]:
        row = data["finished_sections"][plane_index]["case_comparisons"][case_index]
        row["normal_reference"]["fully_braced_linear_normal_CD1_reference_index"] = normal
        row["necessary_mean_shear_over_CD1_Fv"] = shear
    def expected(plane_index, case_index):
        row = data["finished_sections"][plane_index]
        return {"member": row["member"], "station_global_grain_projection_mm": row["station_global_grain_projection_mm"],
                "finished_area_mm2": row["section_properties"]["finished_area_mm2"], **row["case_comparisons"][case_index]}
    result = summary.finished_findings(data, pointer, bindings)
    assert result["all_selected_plane_normal_reference_exceedances"] == [expected(7, 1), expected(10, 1)]
    assert result["all_selected_plane_necessary_shear_reference_exceedances"] == [expected(17, 4), expected(20, 4)]
    assert result["maximum_normal_reference"] == expected(7, 1)
    assert result["maximum_necessary_mean_shear"] == expected(17, 4)
    assert result["per_case_worst_witnesses"][1]["normal_worst"] == expected(7, 1)
    assert result["per_case_worst_witnesses"][4]["necessary_shear_worst"] == expected(17, 4)
    scalars = result["all_selected_plane_reference_scalars"]
    assert len(scalars) == 228
    for plane_index in range(38):
        for case_index in range(6):
            witness = expected(plane_index, case_index)
            normal = witness["normal_reference"]["fully_braced_linear_normal_CD1_reference_index"]
            shear = witness["necessary_mean_shear_over_CD1_Fv"]
            assert scalars[plane_index*6+case_index] == {
                **{k: witness[k] for k in ("member", "station_global_grain_projection_mm", "case_id", "state_id",
                                           "necessary_mean_shear_over_CD1_Fv")},
                "fully_braced_linear_normal_CD1_reference_index": normal,
                "exceedance_witness": witness if normal > 1. or shear > 1. else None}
