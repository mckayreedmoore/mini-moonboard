"""Composite registered-kernel trials for unchanged continuous-model reactions."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
WRAPPER = {'path': 'scripts/eoere_normal_patch_functional_consumer.py',
           'sha256': 'd311934f977138a5d2b8784bcede9ec6e0dd3b1b851fa4f95c8ea865015aed2b'}
DRIVER = {'path': 'scripts/eoere_normal_patch_functionals.py',
          'sha256': '221bd5ff7313815cac7cc61825403187e32e95ab8c6fc9ba14f8a6b17c189d07'}
DIRECTION_BEFORE = """direction = [row.get(column, F(0)) for row in maps]
require(all(not v or owners[i] == name for i, v in enumerate(direction)), 'owner-isolated kernel direction required')
action = h.core.action(rows, direction)
"""
DIRECTION_AFTER = """virtual, direction, shaft_profiles = _composite_direction(name, bodies, maps, owners, field, manifest, source, h, inputs['shaft_profile_fraction'], inputs['shaft_profile_intercept'])
action = h.core.action(rows, direction)
"""
EXPRESSIONS = [
    ("components[j]['kind'] in ('common_shaft_bearing', 'floor_normal')",
     "components[j]['kind'] in ('common_shaft_bearing', 'floor_normal', 'shaft_end_capture')"),
    ('-load[column]', '-sum((load[i]*value for i, value in virtual.items()), F(0))')]
MESSAGE = ('this equivalent leg functional must use unchanged bearing/floor laws only',
           'this equivalent leg functional must use unchanged bearing/floor/capture laws only')
RECORD_FIELDS = {
    'virtual_kernel_weights': '{str(i): str(value) for i, value in virtual.items()}',
    'shaft_profiles': 'shaft_profiles',
    'exact_registered_virtual_load_n': 'str(sum((load[i]*value for i, value in virtual.items()), F(0)))'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def captured(reference, pins):
    path = (ROOT/reference['path']).resolve()
    require(path.is_relative_to(ROOT), 'repository source required')
    data = path.read_bytes(); digest = hashlib.sha256(data).hexdigest()
    require(digest == reference['sha256'] and pins.get(reference['path'], digest) == digest,
            'preserved shaft-profile source changed: '+reference['path'])
    pins[reference['path']] = digest
    return data


def private(reference, pins):
    module = ModuleType('_eoere_verified_profile_'+Path(reference['path']).stem)
    module.__file__ = str(ROOT/reference['path'])
    exec(compile(captured(reference, pins), module.__file__, 'exec'), module.__dict__)  # noqa: S102 - pinned buffer
    return module


def shaft_weights(body, point, reference, axis_x, leg_center, other_center, fraction, intercept):
    """A fixed transverse affine trial, expressed in registered rigid columns."""
    require(body['source_mode_columns'] == [0, 1, 2, 4, 5]
            and type(body['first_rigid_column']) is int and body['first_rigid_column'] >= 0,
            'own horizontal-shaft registered modes required')
    point, reference = [list(map(F, values)) for values in (point, reference)]
    require(len(point) == len(reference) == 3, 'complete point and rigid reference required')
    axis_x, leg_center, other_center, fraction, intercept = map(F, (axis_x, leg_center, other_center, fraction, intercept))
    require(axis_x in (-1, 1) and leg_center != other_center, 'horizontal axis and distinct surface centroids required')
    slope = fraction/(leg_center-other_center)
    constant = intercept-slope*other_center
    ny = -axis_x
    px, _, pz = [a-b for a, b in zip(point, reference, strict=True)]
    first = body['first_rigid_column']
    # Stored global rotation columns are divided by 1000 in the registered R.
    values = {first: -slope*ny*pz, first+2: constant+slope*ny*px, first+3: 1000*slope*ny}
    return {j: value for j, value in values.items() if value}


def composite_direction(name, bodies, maps, owners, field, manifest, source, h, fraction, intercept):
    fraction, intercept = F(fraction), F(intercept)
    require((fraction, intercept) == (F(3, 4), F(1, 8)), 'predeclared fixed proof profile required')
    body, = [row for row in bodies if row['body'] == name]
    require(body['source_mode_columns'] == [0, 1, 2, 3, 4, 5], 'own registered leg direction required')
    virtual = {body['first_rigid_column']+2: F(1)}
    shafts = [s for s in field['source_inputs']['shafts'] if any(surface['host'] == name for surface in s['surfaces'])]
    require(len(shafts) == 4 and len({s['axis_id'] for s in shafts}) == 4, 'four distinct own connected shafts required')
    allowed, profiles = {name}, []
    for shaft in shafts:
        require(len(shaft['surfaces']) == 2 and all(s['kind'] == 'wood' for s in shaft['surfaces']),
                'retained ordinary two-wood-surface shaft required')
        leg, = [s for s in shaft['surfaces'] if s['host'] == name]
        other, = [s for s in shaft['surfaces'] if s['host'] != name]
        intervals = [list(map(F, s['interval_mm'])) for s in (leg, other)]
        require(all(len(interval) == 2 and interval[0] < interval[1] for interval in intervals), 'positive own surface intervals required')
        centers = [(a+b)/2 for a, b in intervals]
        axis = list(map(F, shaft['source_axis']['direction_xyz']))
        require(len(axis) == 3 and axis[0] in (-1, 1) and axis[1:] == [0, 0], 'retained global-X shaft required')
        registered, = [row for row in bodies if row['body'] == shaft['body']]
        own = shaft_weights(registered, shaft['point'], manifest['rigid_modes_reference_xyz_mm'], axis[0], *centers, fraction, intercept)
        require(not (set(virtual) & set(own)), 'disjoint owner kernel columns required')
        virtual.update(own); allowed.add(shaft['body'])
        profiles.append({'axis_id': shaft['axis_id'], 'body': shaft['body'],
                         'leg_host': name, 'other_host': other['host'],
                         'exact_leg_centroid_s_mm': str(centers[0]), 'exact_other_centroid_s_mm': str(centers[1]),
                         'exact_fraction': str(fraction), 'exact_intercept': str(intercept),
                         'exact_rigid_weights': {str(j): str(value) for j, value in own.items()}})
    require(all(not (allowed & {patch['first'], patch['second']}) for patch in field['source_inputs']['flange_shared_face_patches']),
            'complete continuous bed must exclude every composite-trial owner')
    require(all(sum((F(row['exact_rigid_compression_row'].get(str(j), '0'))*value for j, value in virtual.items()), F(0)) == 0
                for row in source['shared_material_support_records']), 'all continuous support derivatives must also vanish exactly')
    dimension = max(j for row in maps for j in row)+1
    require(all(type(j) is int and 0 <= j < dimension for j in virtual), 'bounded own rigid columns required')
    direction = h.core.action(maps, [virtual.get(j, F(0)) for j in range(dimension)])
    require(len(direction) == len(owners) and all(not value or owners[i] in allowed for i, value in enumerate(direction)),
            'composite direction must remain owner isolated')
    return virtual, direction, profiles


def rewrite(tree, *, reverse=False):
    before = ast.parse(DIRECTION_BEFORE).body; after = ast.parse(DIRECTION_AFTER).body
    pairs = [(ast.parse(a, mode='eval').body, ast.parse(b, mode='eval').body) for a, b in EXPRESSIONS]
    pairs.append((ast.Constant(MESSAGE[0]), ast.Constant(MESSAGE[1])))
    if reverse:
        before, after = after, before
        pairs = [(b, a) for a, b in pairs]
    replacements = {ast.dump(a): (i, b) for i, (a, b) in enumerate(pairs)}
    counts = [0]*5
    class Trial(ast.NodeTransformer):
        def generic_visit(self, node):
            node = super().generic_visit(node)
            found = replacements.get(ast.dump(node))
            if found is not None:
                i, replacement = found; counts[i] += 1
                return ast.copy_location(replacement, node)
            return node
        def visit_For(self, node):
            self.generic_visit(node)
            own, i = [], 0
            while i < len(node.body):
                if [ast.dump(n) for n in node.body[i:i+len(before)]] == [ast.dump(n) for n in before]:
                    own.extend(after); i += len(before); counts[3] += 1
                else:
                    own.append(node.body[i]); i += 1
            node.body = own
            return node
        def visit_Dict(self, node):
            self.generic_visit(node)
            labels = [key.value if isinstance(key, ast.Constant) else None for key in node.keys]
            if 'registered_translation_column' not in labels:
                return node
            counts[4] += 1
            if reverse:
                require(all(labels.count(key) == 1 for key in RECORD_FIELDS), 'all declared composite record fields required')
                keep = [i for i, label in enumerate(labels) if label not in RECORD_FIELDS]
                node.keys, node.values = [node.keys[i] for i in keep], [node.values[i] for i in keep]
            else:
                require(not (set(labels) & set(RECORD_FIELDS)), 'composite record fields must be new')
                for key, value in RECORD_FIELDS.items():
                    node.keys.append(ast.Constant(key)); node.values.append(ast.parse(value, mode='eval').body)
            return node
    result = Trial().visit(tree)
    require(counts == [1]*5, 'exact declared composite direction, offset, metric gate and record delta required')
    return ast.fix_missing_locations(result)


def producer(pins):
    wrapper = private(WRAPPER, pins)
    require(wrapper.BASE == DRIVER, 'same frozen functional driver required')
    tree = rewrite(wrapper.rewrite(ast.parse(captured(DRIVER, pins))))
    digest = hashlib.sha256(ast.dump(tree).encode()).hexdigest()
    module = ModuleType('_eoere_verified_composite_trial_driver')
    module.__file__ = str(ROOT/DRIVER['path'])
    exec(compile(tree, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - pinned declared AST delta
    module._composite_direction = composite_direction
    return module, digest


def run(reference):
    pins = {}; inputs = json.loads(captured(reference, pins))
    require(inputs['consumer_schema'] == 'eoere_equilibrium_functional_shaft_profile/v1'
            and (inputs['shaft_profile_fraction'], inputs['shaft_profile_intercept']) == ('3/4', '1/8'),
            'predeclared unchanged-model composite proof trial required')
    previous = json.loads(captured(inputs['preserved_equilibrium_result'], pins))
    require(previous['schema'] == 'eoere_continuous_normal_equilibrium_functionals/v2'
            and previous['inputs'] == inputs['preserved_v2_inputs'], 'completed preserved equilibrium-functional result required')
    for path, digest in previous['source_sha256'].items():
        captured({'path': path, 'sha256': digest}, pins)
    original = json.loads(captured(inputs['preserved_v2_inputs'], pins))
    wrapper = private(WRAPPER, pins); wrapper.same_scope(inputs, original)
    require(all(inputs[key] == original[key] for key in ('preserved_v1_inputs', 'preserved_stopped_preflight')),
            'same preserved preflight and original input required')
    for source in inputs['execution_sources']:
        captured(source, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing composite consumer required')
    driver, ast_digest = producer(pins); result = driver.run(reference)
    for path, digest in result['source_sha256'].items():
        captured({'path': path, 'sha256': digest}, pins)
    for case, old in zip(result['cases'], previous['cases'], strict=True):
        require(all(case[key] == old[key] for key in ('binding', 'operator_bundle', 'exact_original_rigid_load_sha256',
                    'exact_reused_total_Fenchel_gap_upper_nmm')), 'same complete original case, load and gap required')
    result.update({'schema': 'eoere_continuous_normal_shaft_profile_functionals/v1', 'source_sha256': pins,
                   'execution_driver': {'path': str(OWN.relative_to(ROOT)), 'sha256': LOADED_SHA},
                   'transformed_driver_source': DRIVER, 'preserved_remainder_adapter': WRAPPER,
                   'adapted_driver_AST_sha256': ast_digest, 'preserved_equilibrium_result': inputs['preserved_equilibrium_result'],
                   'declared_AST_delta': {'direction_before': DIRECTION_BEFORE, 'direction_after': DIRECTION_AFTER,
                                          'expressions': EXPRESSIONS, 'message': MESSAGE, 'record_fields': RECORD_FIELDS},
                   'fixed_profile_is_auxiliary_not_physical_sharing_or_stiffness': True,
                   'all_nonzero_transformed_coefficients_retained': True})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'preserve issued composite-profile evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(),
                      'positive_leg_resultants_certified': result['positive_leg_resultants_certified']}))


if __name__ == '__main__':
    main()
