"""Copy or check frozen Candidate 13 presentation evidence without CAD or mechanics."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath

PROVENANCE_SHA256 = 'de8a8b3581e2bd808d866a10b8e7cf63e0815d21ca2b98d7244eaa2c931418e4'
PREFIX = 'docs/bolted-frame-development/owner-frame-v10/candidate13/'
SCENE = 'site/eoere-v10-scene-13.json.gz'
COUNTS = {'Hillman_axes': 66, 'angles': 24, 'bolt_stacks': 116, 'occupied_parts': 1167,
          'panels': 6, 'plywood_cleats': 4, 'sawn_members': 22, 'spacer_pieces': 60}
FLAGS = ('complete_conditional_frame_evaluation', 'complete_joint_qualified',
         'physical_force_bounds_established', 'physical_operations_authorized',
         'structural_acceptance', 'fabrication_released', 'climbing_released')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def local_path(root, relative):
    if not isinstance(relative, str):
        raise TypeError('Repository-relative file path required')
    parts = PurePosixPath(relative)
    if (not relative or any(c in relative for c in '\\:?#') or parts.is_absolute()
            or '..' in parts.parts or '.' in relative.split('/') or str(parts) != relative):
        raise ValueError('Repository-relative file path required: '+relative)
    root = Path(root).resolve()
    target = root / relative
    if not target.resolve().is_relative_to(root):
        raise ValueError('File path escapes root: '+relative)
    return target


def records(manifest):
    return [*manifest['artifacts'].values(), *manifest['support_files']]


def validate_manifest(manifest):
    if (manifest.get('schema') != 'eoere_v10_candidate13_provenance/v1'
            or manifest.get('geometry_revision') != 'eoere-candidate13-side-depth-v10'
            or manifest.get('model') != 'eoere-owner-frame-v10-development'
            or manifest.get('counts') != COUNTS):
        raise ValueError('Candidate identity or census differs')
    if any(manifest.get(flag) is not False for flag in FLAGS):
        raise ValueError('Candidate claim boundary differs')
    if len(manifest.get('artifacts', {})) != 29 or len(manifest.get('support_files', [])) != 28:
        raise ValueError('Exactly 29 delivery and 28 support roots are required')
    seen, sources = set(), set()
    for row in records(manifest):
        original, integrated = row['original'], row['integrated']
        local_path(Path.cwd(), row['source_path'])
        local_path(Path.cwd(), integrated['path'])
        if not original['path'].endswith('/'+row['source_path']):
            raise ValueError('Original/source relocation differs')
        compress = row['source_path'].endswith('.json') and original['bytes'] > 256000
        expected_path = SCENE if row['source_path'] == SCENE else PREFIX+row['source_path']+('.gz' if compress else '')
        if row['encoding'] != ('gzip' if compress else 'identity') or integrated['path'] != expected_path:
            raise ValueError('Encoding or relocation policy differs')
        for binding in (original, integrated):
            if (not isinstance(binding['bytes'], int) or binding['bytes'] <= 0
                    or len(binding['sha256']) != 64
                    or any(c not in '0123456789abcdef' for c in binding['sha256'])):
                raise ValueError('Invalid file binding')
        if integrated['path'] in seen or original['path'] in sources:
            raise ValueError('Duplicate relocation')
        seen.add(integrated['path'])
        sources.add(original['path'])
        if not compress and {k: original[k] for k in ('bytes', 'sha256')} != {
                k: integrated[k] for k in ('bytes', 'sha256')}:
            raise ValueError('Identity binding differs')
    if (len(manifest.get('paper_audit_artifact_paths', [])) != 19
            or len(set(manifest['paper_audit_artifact_paths'])) != 19
            or not set(manifest['paper_audit_artifact_paths']) <= seen):
        raise ValueError('Paper audit inventory differs')
    for ref in manifest.get('center_principal_correction', {}).values():
        if ref not in [row['integrated'] for row in records(manifest)]:
            raise ValueError('Correction relocation differs')
    if set(manifest.get('center_principal_correction', {})) != {'index', 'record', 'read_first', 'summary'}:
        raise ValueError('Corrected interpretation is required')
    if manifest.get('standards_and_relocation_handoff') not in [row['integrated'] for row in records(manifest)]:
        raise ValueError('Group and relocation handoff is required')
    raw = manifest.get('retained_raw_evidence', {})
    if raw.get('source_package_required_for_replay') is not True or raw.get('archive_or_prune_authorized') is not False:
        raise ValueError('Raw evidence boundary differs')
    return manifest


def load_manifest(path):
    raw = Path(path).read_bytes()
    if sha(raw) != PROVENANCE_SHA256:
        raise ValueError('Provenance metadata bytes differ')
    return validate_manifest(json.loads(raw))


def deterministic_gzip(raw):
    buffer = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=buffer, compresslevel=9, mtime=0) as stream:
        stream.write(raw)
    return buffer.getvalue()


def verify_payload(row, stored):
    integrated = row['integrated']
    if len(stored) != integrated['bytes'] or sha(stored) != integrated['sha256']:
        raise ValueError('Integrated binding differs: '+integrated['path'])
    original = gzip.decompress(stored) if row['encoding'] == 'gzip' else stored
    if len(original) != row['original']['bytes'] or sha(original) != row['original']['sha256']:
        raise ValueError('Decoded original binding differs: '+integrated['path'])
    return original


def verify_parents(manifest, root):
    for binding in manifest['parents'].values():
        raw = local_path(root, binding['path']).read_bytes()
        if sha(raw) != binding['sha256'] or len(raw) != binding['bytes']:
            raise ValueError('Canonical V9 parent differs: '+binding['path'])


def verify_joins(manifest, originals):
    bundle = json.loads(originals['delivery-bundle-13.json'])
    expected = {name: {key: row['original'][key] for key in ('path', 'sha256')}
                for name, row in manifest['artifacts'].items()}
    if bundle['artifacts'] != expected:
        raise ValueError('Frozen delivery artifact join differs')
    paper = json.loads(originals['paper-audit/paper-audit-bundle-v1.json'])
    actual = {row['original']['path']: row['original']['sha256'] for row in records(manifest)
              if row['integrated']['path'] in manifest['paper_audit_artifact_paths']}
    if {row['path']: row['sha256'] for row in paper['artifacts']} != actual:
        raise ValueError('Frozen paper artifact join differs')
    index = json.loads(originals['paper-audit/completion-index-v3.json'])
    correction = json.loads(originals['paper-audit/center-principal-correction-13-v1.json'])
    for ref, relative in [
        (index['prior_completion'], 'paper-audit/completion-index-v2.json'),
        (index['read_first_correction'], 'paper-audit/center-principal-correction-13-v1.json'),
        (index['completion_summary'], 'paper-audit/completion-summary-corrected-13-v1.txt'),
        (correction['correction'], 'paper-audit/center-principal-correction-13-v1.txt'),
        *[(ref, 'paper-audit/'+name) for name, ref in correction['sources'].items()],
    ]:
        if (not ref['path'].replace('\\', '/').endswith('/'+relative)
                or sha(originals[relative]) != ref['sha256']):
            raise ValueError('Corrected interpretation source join differs')
    if (correction['net_actions_toward_near_edge_all_cases'] is not False
            or correction['established_NDS_near_edge_violation'] is not False
            or correction['fourD_both_edges_is_optional_conservative_envelope'] is not True
            or correction['idealized_resultant_edge_screen_clears'] is not True
            or correction['complete_oblique_eccentric_splitting_qualified'] is not False):
        raise ValueError('Corrected edge classification differs')


def check(manifest, root):
    validate_manifest(manifest)
    verify_parents(manifest, root)
    originals = {row['source_path']: verify_payload(row, local_path(root, row['integrated']['path']).read_bytes())
                 for row in records(manifest)}
    verify_joins(manifest, originals)
    return {'status': 'portable_frozen_roots_verified', 'roots': len(originals),
            'integrated_bytes': sum(row['integrated']['bytes'] for row in records(manifest)),
            'raw_case_operator_banks_recovered': False, 'structural_acceptance': False,
            'fabrication_released': False, 'climbing_released': False}


def publish(manifest, source_package, root):
    """Preflight the complete copy set, preserving every existing nonmatching file."""
    validate_manifest(manifest)
    verify_parents(manifest, root)
    pending, originals = [], {}
    for row in records(manifest):
        original = local_path(source_package, row['source_path']).read_bytes()
        if len(original) != row['original']['bytes'] or sha(original) != row['original']['sha256']:
            raise ValueError('Source binding differs: '+row['source_path'])
        stored = deterministic_gzip(original) if row['encoding'] == 'gzip' else original
        verify_payload(row, stored)
        destination = local_path(root, row['integrated']['path'])
        if destination.exists() and destination.read_bytes() != stored:
            raise ValueError('Preserve existing differing file: '+row['integrated']['path'])
        originals[row['source_path']] = original
        pending.append((destination, stored))
    verify_joins(manifest, originals)
    for destination, stored in pending:
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as stream:
                stream.write(stored)
    return check(manifest, root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--source-package', type=Path)
    parser.add_argument('--write', action='store_true', help='Copy verified frozen roots; default is read-only checking')
    args = parser.parse_args()
    manifest = load_manifest(args.manifest or args.root/'site/eoere-v10-candidate13-provenance.json')
    if args.write and args.source_package is None:
        parser.error('--write requires --source-package')
    result = publish(manifest, args.source_package, args.root) if args.write else check(manifest, args.root)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
