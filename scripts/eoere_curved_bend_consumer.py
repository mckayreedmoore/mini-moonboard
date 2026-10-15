"""Captured-byte intake for the frozen ideal-bend mechanics and field checker.

The first adapter remains immutable evidence. This consumer reuses its
mechanics while authenticating each parsed/compiled buffer before use.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import scipy

from scripts import eoere_curved_bend_field as method

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/'fea/generated/selected-hardware-followup-v1/engineering-closure-v1'
INPUT = ROOT/'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/current-response-v1/joint-closure-v1/steel-curved-bend-inputs-v2.json'
LOADED_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def captured(ref, pins):
    path = (ROOT/ref['path']).resolve()
    require(path.is_relative_to(ROOT), 'source outside repository')
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(ref.get('sha256', digest) == digest, 'consumed source buffer changed: '+ref['path'])
    require(ref['path'] not in pins or pins[ref['path']] == digest, 'contradictory source buffer')
    pins[ref['path']] = digest
    return data


def read_json(ref, pins):
    return json.loads(captured(ref, pins))


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, 'source changed since capture: '+path)


def read_input(path):
    path = path.resolve()
    require(path.is_relative_to(ROOT), 'owned input inside repository required')
    pins = {}
    inputs = read_json({'path': str(path.relative_to(ROOT))}, pins)
    verify(pins)
    return inputs, pins


def captured_module(ref, name, pins):
    data = captured(ref, pins)
    module = ModuleType(name)
    module.__file__ = str((ROOT/ref['path']).resolve())
    # SHA-256 is checked on this exact buffer before compilation.
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102
    return module


def frozen_mechanics(ref, pins):
    data = captured(ref, pins)
    filename = str((ROOT/ref['path']).resolve())
    tree = ast.parse(data, filename=filename)
    names = {'gravity_partition', 'reduce'}
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    rotation = [node for node in tree.body if isinstance(node, ast.Assign)
                and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == 'ROTATION']
    require({node.name for node in functions} == names and len(rotation) == 1, 'complete frozen mechanics required')
    namespace = {'np': np, 'math': math, 'method': method, 'require': require}
    # Reuse authenticated definitions without importing v1's generic loader.
    code = compile(ast.Module(body=rotation+functions, type_ignores=[]), filename, 'exec')
    exec(code, namespace)  # noqa: S102
    return SimpleNamespace(**{name: namespace[name] for name in names})


def calculator(refs, pins):
    core = captured_module(refs['core'], 'eoere_captured_bend_core', pins)
    previous = sys.modules.get('core')
    sys.modules['core'] = core
    try:
        module = captured_module(refs['calculator'], 'eoere_captured_bend_calculator', pins)
    finally:
        if previous is None:
            del sys.modules['core']
        else:
            sys.modules['core'] = previous
    require(module.core is core, 'calculator did not bind its captured core')
    return module


def run(input_path):
    inputs, pins = read_input(input_path)
    require(inputs['schema'] == 'current_ideal_curved_bend_captured_inputs/v2'
            and inputs['comparisons_mm'] == [6.35, 6.0] and inputs['interval_cell_budget'] == 10000,
            'exact declared captured-intake inputs required')
    for ref in inputs['implementation'].values():
        captured(ref, pins)
    require(inputs['implementation']['field']['sha256'] == method.LOADED_SHA
            and inputs['implementation']['consumer']['sha256'] == LOADED_SHA, 'loaded implementation differs')
    runtime = inputs['runtime']
    for ref in runtime['files'].values():
        captured(ref, pins)
    require(runtime['python'] == platform.python_version() and runtime['numpy'] == np.__version__
            and runtime['scipy'] == scipy.__version__, 'shared runtime version differs')
    index = read_json(inputs['revision_index'], pins)
    require(index['current_response']['cases'] == inputs['current_response']
            and index['current_response']['components'] == inputs['current_components'], 'current authority differs')
    for role in ('geometry', 'hardware_model'):
        read_json(index['current_response'][role], pins)
    current = read_json(inputs['current_response'], pins)
    read_json(inputs['current_components'], pins)
    material = read_json(inputs['retained_material_source'], pins)
    guide = material['primary_guide']
    require(guide['minimum_yield_mpa'] == 235 and guide['minimum_tensile_mpa'] == 370,
            'changed conditional material reference')
    captured({'path': guide['local_path'], 'sha256': guide['sha256']}, pins)
    require(current['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and current['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and current['extra_grid'] is False and len(current['cases']) == 6, 'exact current response required')
    read_json(inputs['prior_input'], pins)
    previous = read_json(inputs['preceding_attempt'], pins)
    mechanics = frozen_mechanics(inputs['implementation']['adapter'], pins)
    calc = calculator(inputs['frozen_steel_calculator'], pins)
    verify(pins)
    rows = []
    for case in current['cases']:
        data = read_json(case['field'], pins)
        require(data['case_id'] == case['case_id'] and data['state_id'] == case['state_id']
                and len(data['source_inputs']['shafts']) == 100 and len(data['source_inputs']['hillman_rows']) == 66
                and len(data['fitting_operator_descriptors']) == 22 and not any(data['release'].values()),
                'matching unreleased current field required')
        for descriptor in data['fitting_operator_descriptors']:
            rows.extend(mechanics.reduce(data, descriptor, thickness, calc, inputs['interval_cell_budget'])
                        for thickness in inputs['comparisons_mm'])
    require(len(rows) == 264 and len({(r['case_id'], r['body'], r['comparison_thickness_mm']) for r in rows}) == 264,
            'complete own fitting/case/scenario census required')
    verify(pins)
    require(rows == previous['rows'], 'captured-intake replay changed frozen arithmetic rows')
    summaries = []
    for thickness in inputs['comparisons_mm']:
        selected = [r for r in rows if r['comparison_thickness_mm'] == thickness]
        complete = [r for r in selected if r['certificate']['all_material_boxes_covered']]
        worst = max(complete, key=lambda r: r['certificate']['covering_upper_index_squared']) if complete else None
        summaries.append({'thickness_mm': thickness, 'inside_radius_mm': thickness, 'comparisons': len(selected),
            'everywhere_constructions_within_reference': len(complete), 'inconclusive': len(selected)-len(complete),
            'maximum_certified_upper_index_display': worst['certificate']['covering_upper_index_display'] if worst else None,
            'maximum_certified_upper_index_squared': worst['certificate']['covering_upper_index_squared'] if worst else None,
            'worst_upper_case': worst['case_id'] if worst else None, 'worst_upper_body': worst['body'] if worst else None,
            'total_visited_interval_boxes': sum(r['certificate']['visited_boxes'] for r in selected)})
    require(summaries == previous['summary'], 'captured-intake replay changed frozen arithmetic summary')
    return {'schema': 'current_ideal_curved_bend_captured_audit/v2', 'status': 'IDEAL_BEND_REFERENCE_CONSTRUCTIONS_EVALUATED',
        'geometry_revision': current['geometry_revision'], 'hardware_revision': current['hardware_revision'],
        'source_sha256': pins, 'source_count': len(pins), 'summary': summaries, 'rows': rows,
        'parsed_and_compiled_buffers_authenticated_before_use': True,
        'input_pin_hashes_the_consumed_buffer': True, 'prior_arithmetic_rows_and_summary_unchanged': True,
        'uniform_bend_gravity_and_source_total_wrench_retained': True,
        'source_recovery_gates_n_nmm': [1e-4, .1], 'source_recovery_residuals_are_not_exact_balance': True,
        'actual_flange_interface_traction_matched': False, 'elastic_first_yield_or_stiffness_qualified': False,
        'actual_formed_fitting_or_complete_joint_resistance_qualified': False, 'structural_acceptance': False,
        'panel_screw_exceedances_deferred': True, 'native_FEA_frame_response_CAD_or_design_change': False,
        'assumptions': inputs['assumptions'], 'limits': inputs['limits'],
        'execution': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
                      'command': 'uv run python -B -m scripts.eoere_curved_bend_consumer --input INPUT --output OUTPUT'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(RAW) and not output.exists(), 'new owned ignored output required')
    result = run(args.input)
    with output.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'output': str(output.relative_to(ROOT)), 'bytes': output.stat().st_size,
                      'sha256': sha(output), 'summary': result['summary']}))


if __name__ == '__main__':
    main()
