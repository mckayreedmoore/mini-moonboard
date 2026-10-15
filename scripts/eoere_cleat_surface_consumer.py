"""Execute the preserved cleat load producer and helpers from verified buffers."""
from __future__ import annotations

import argparse
import builtins
import hashlib
import json
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PRODUCER = 'scripts/eoere_cleat_surface_loads.py'
HELPERS = {'fea': ('wood_joint_reduced_contacts', 'fea/wood_joint_reduced_contacts.py'),
           'scripts': ('wood_joint_current_face_pair_atlas_attempt01',
                       'scripts/wood_joint_current_face_pair_atlas_attempt01.py')}


def capture(reference):
    path = (ROOT/reference['path']).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('repository source required')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != reference['sha256']:
        raise ValueError('captured source changed: '+reference['path'])
    return data


def compile_private(data, path, *, import_function=builtins.__import__):
    """No sys.modules registration, source reopen or cached helper execution."""
    module = types.ModuleType('_eoere_verified_'+Path(path).stem)
    module.__file__ = str(ROOT/path)
    module.__dict__['__builtins__'] = dict(vars(builtins), __import__=import_function)
    # Execute the owner-authorized, hash-bound repository source, never a path
    # reload or third-party input program.
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102
    return module


def verified_modules(references):
    refs = {r['path']: r for r in references}
    paths = [PRODUCER, *(path for _, path in HELPERS.values())]
    buffers = {path: capture(refs[path]) for path in paths}
    helpers = {package: compile_private(buffers[path], path) for package, (_, path) in HELPERS.items()}

    def private_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in HELPERS:
            member, _ = HELPERS[name]
            if level != 0 or tuple(fromlist) != (member,):
                raise ValueError('unexpected repository helper import')
            return types.SimpleNamespace(**{member: helpers[name]})
        if name.startswith(('fea.', 'scripts.')):
            raise ValueError('unbound repository helper import')
        return builtins.__import__(name, globals, locals, fromlist, level)

    producer = compile_private(buffers[PRODUCER], PRODUCER, import_function=private_import)
    # The preserved module records its disk hash at import. Bind that field to
    # the exact executed buffer; its existing run() still rechecks every input.
    producer.LOADED_SHA = hashlib.sha256(buffers[PRODUCER]).hexdigest()
    return producer, helpers


def run(reference):
    inputs = json.loads(capture(reference))
    own_path = str(OWN.relative_to(ROOT))
    refs = {r['path']: r for r in inputs['execution_sources']}
    if refs.get(own_path, {}).get('sha256') != LOADED_SHA:
        raise ValueError('exact executing consumer required')
    producer, _ = verified_modules(inputs['execution_sources'])
    result = producer.run(reference)
    result['execution_driver'] = {'path': own_path, 'sha256': LOADED_SHA}
    result['execution_binding'] = 'Producer, atlas and partition executed from their captured verified buffers in private modules; repository helper imports bypass sys.modules.'
    result['superseded_execution_binding'] = inputs['preserved_v1_result']
    # The actual v1 result remains an authenticated retained input, not merely a
    # pathname label. All physical load rows must agree with that first attempt.
    old = json.loads(capture(inputs['preserved_v1_result']))
    for key in ('counts', 'geometry', 'contact_patch_definitions', 'records',
                'maximum_individual_wrench_error_n_nmm'):
        if result[key] != old[key]:
            raise ValueError('continuous load values changed: '+key)
    result['preserved_v1_load_rows_equal'] = True
    result['source_sha256'][inputs['preserved_v1_result']['path']] = inputs['preserved_v1_result']['sha256']
    if hashlib.sha256(OWN.read_bytes()).hexdigest() != LOADED_SHA:
        raise ValueError('consumer changed during execution')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve issued load-functional evidence')
    data = args.inputs.read_bytes()
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest()}
    result = run(reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(), 'counts': result['counts']}))


if __name__ == '__main__':
    main()
