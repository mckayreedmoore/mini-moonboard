"""Verify a logging-only source delta against the preserved upstream manifest."""
import hashlib
import json
import re
import subprocess
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources(upstream, patch, measured):
    expected = dict(upstream)
    changed = {}
    for name, before in patch['source_sha256'].items():
        key = './CalculiX/ccx_2.21/src/'+name
        if expected.get(key) != before:
            raise ValueError('Patch source does not match upstream inventory')
        expected[key] = patch['patched_sha256'][name]
        changed[key] = {'before': before, 'after': expected[key]}
    if set(patch['source_sha256']) != {'stressmortar.c', 'nonlingeo.c'}:
        raise ValueError('Only the two reviewed source files may change')
    if measured != expected:
        raise ValueError('Actual source inventory differs from declared two-file patch')
    return changed


def main():
    root = Path('/opt/ccx-kinematic-observer-2.21')
    upstream_root = Path('/opt/ccx-upstream-2.21')
    upstream_path = upstream_root/'build_manifest.json'
    upstream = json.loads(upstream_path.read_text())
    patch = json.loads((root/'patched/patch_manifest.json').read_text())
    measured = {name: sha(upstream_root/name) for name in upstream['upstream_files_sha256']}
    changed = verify_sources(upstream['upstream_files_sha256'], patch, measured)
    for group in ('binary_sha256', 'linked_library_sha256'):
        for path, expected in upstream[group].items():
            if sha(Path(path)) != expected:
                raise ValueError('Preserved binary/library changed: '+path)
    if sha(upstream_root/'Makefile.upstream') != upstream['build_support_sha256']['Makefile.upstream']:
        raise ValueError('Observer compiler configuration changed')
    if (sha(root/'patch.py') != patch['v1_patch_generator_sha256'] or
            sha(root/'kinematic_patch.py') != patch['v2_patch_generator_sha256']):
        raise ValueError('Patch generator snapshot changed')
    linked = subprocess.check_output(['ldd', '/usr/local/bin/ccx-kinematic-observer-2.21'], text=True)
    libraries = {str(Path(path).resolve()) for path in re.findall(r'(/\S+)\s+\(', linked)}
    if 'not found' in linked or not libraries:
        raise ValueError('Observer linked libraries could not be resolved')
    for path in libraries:
        if upstream['linked_library_sha256'].get(path) != sha(Path(path)):
            raise ValueError('Observer uses an unverified library: '+path)
    report = {
        'qualification': 'Logging-only source delta; binary/cube equivalence and local-law replay still required',
        'upstream_manifest_sha256': sha(upstream_path), 'source_changes': changed,
        'source_files_checked': len(measured), 'patch_manifest': patch,
        'binary_sha256': dict(upstream['binary_sha256']) | {
            '/usr/local/bin/ccx-kinematic-observer-2.21': sha(Path('/usr/local/bin/ccx-kinematic-observer-2.21'))},
        'preserved_linked_library_sha256': upstream['linked_library_sha256'],
        'observer_ldd': linked,
        'build_support_sha256': {name: sha(root/name) for name in ('Dockerfile', 'record_build.py', 'patch.py', 'kinematic_patch.py')},
    }
    (root/'build_manifest.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
