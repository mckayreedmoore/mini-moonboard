"""Publish existing original/recovered evidence; never execute a solve or replay."""
import argparse
import hashlib
import json
import shutil
import tarfile
from pathlib import Path


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def publish(original, recovery, destination):
    evidence = recovery/'evidence'
    original_hashes = {str(p.relative_to(original)): sha(p)
                       for p in original.rglob('*') if p.is_file()}
    for name, expected in original_hashes.items():
        copied = evidence/('original-report.json' if name == 'report.json' else name)
        if sha(copied) != expected:
            raise ValueError('Recovery copy differs from original: '+name)
    launch = json.loads((original/'report.json').read_text())
    terminal = json.loads((evidence/'report.json').read_text())
    record = json.loads((recovery/'recovery.json').read_text())
    if (sha(recovery/'recovery-launch.py') != record['recovery_source_sha256'] or
            sha(original/'report.json') != record['original_report_sha256'] or
            sha(recovery/'recovery.json') != terminal['recovery_record_sha256']):
        raise ValueError('Recovery provenance changed')
    for name, expected in launch['audit_source_sha256'].items():
        archived = 'launch.py' if name == 'mortar_frame_observer.py' else 'launch_sources/'+name
        if sha(recovery/'fea'/name) != expected or original_hashes[archived] != expected:
            raise ValueError('Executing source closure differs: '+name)
    for inventory in ('prelaunch_sha256', 'output_sha256'):
        if any(original_hashes[n] != value for n, value in launch[inventory].items()):
            raise ValueError('Original evidence digest differs')
    if any(sha(evidence/n) != value for n, value in terminal['audit_output_sha256'].items()):
        raise ValueError('Audit output digest differs')
    manifest = {
        'status': 'TERMINAL DIAGNOSTIC ONLY; AUDIT REJECTED; NO PHYSICAL ACCEPTANCE',
        'meaning': 'Original cleanup failure retained. Post-hoc exact-name absence confirmation '
                   'permits one audit of existing raw output with unchanged archived source. '
                   'No solver rerun and no retroactive monitor success. Hash tests do not rerun replay.',
        'original_directory_name': original.name,
        'recovery_directory_name': recovery.name,
        'original_file_sha256': original_hashes,
        'files_sha256': {}, 'archives': {}, 'reference': {},
    }
    for name, expected in record['reference_sha256'].items():
        path = destination.parent/'full_frame_refinement'/name
        if sha(path) != expected or sha(recovery/'fea/results/full_frame_refinement'/name) != expected:
            raise ValueError('Reference changed: '+name)
        manifest['reference'][name] = {'path': '../full_frame_refinement/'+name, 'sha256': expected}
    direct = {'original-report.json': original/'report.json',
              'recovered-report.json': evidence/'report.json',
              'recovery.json': recovery/'recovery.json',
              'recovery-launch.py': recovery/'recovery-launch.py'}
    direct.update({n: evidence/n for n in ('audit.json', 'audit.log', 'coupling_resultants.json')})
    for name, source in direct.items():
        shutil.copy2(source, destination/name)
        manifest['files_sha256'][name] = sha(destination/name)
    groups = {
        'observer-log.tar.gz': {'frame.log': original/'frame.log'},
        'solver-fields.tar.gz': {n: original/n for n in original_hashes
                                 if n.startswith('frame.') and n != 'frame.log'},
        'launch-provenance.tar.gz': {n: original/n for n in original_hashes
                                    if not n.startswith('frame.') and n != 'report.json'},
        'local-replay.tar.gz': {'local_replay.json': evidence/'local_replay.json'},
    }
    for name, paths in groups.items():
        archive = destination/name
        with tarfile.open(archive, 'w:gz', compresslevel=6) as tar:
            for member, source in sorted(paths.items()):
                tar.add(source, arcname=member, recursive=False)
        if archive.stat().st_size >= 100_000_000:
            raise ValueError('Publication archive exceeds conservative 100 MB cap: '+name)
        manifest['archives'][name] = {
            'sha256': sha(archive), 'size_bytes': archive.stat().st_size,
            'contents_sha256': {member: sha(source) for member, source in paths.items()},
        }
    audit = json.loads((evidence/'audit.json').read_text())
    local = json.loads((evidence/'local_replay.json').read_text())
    manifest['summary'] = {key: value for key, value in audit.items() if key != 'diagnostic_endpoints'}
    manifest['summary'].update(observer_calls=local['calls'], accepted_calls=local['accepted_calls'],
                               failed_global_gate_times=[r['time'] for r in audit['diagnostic_endpoints']
                                                         if not r['global_gate_pass']])
    manifest['publisher_sha256'] = sha(Path(__file__))
    if original_hashes != {str(p.relative_to(original)): sha(p)
                           for p in original.rglob('*') if p.is_file()}:
        raise ValueError('Original evidence changed during publication')
    (destination/'report.json').write_text(json.dumps(manifest, indent=2, allow_nan=False)+'\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('recovery', type=Path)
    args = parser.parse_args()
    result = publish(args.original.resolve(), args.recovery.resolve(), Path(__file__).resolve().parent)
    print(json.dumps({name: item['size_bytes'] for name, item in result['archives'].items()}, indent=2))
