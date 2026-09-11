"""Authenticate retained native evidence and replay final numerical diagnostics.

Reads extracted archives without invoking CAD, Docker or a solver. Historical
source snapshots are checked against their own manifests, not current sources.
"""
import argparse
import hashlib
import json
from pathlib import Path

from fea import horizontal_frame_batch as batch
from fea import horizontal_frame_stress as stress
from fea import horizontal_panel_frame as frame

REFERENCES = {'docs/led-wiring-reference.json','docs/ml24z-reference.json',
              'docs/ml23z-reference.json','docs/panel-insert-reference.json'}


def authenticated_file(root, name, digest):
    root=Path(root).resolve();path=(root/name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Missing or escaping evidence path: '+name)
    hasher=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):hasher.update(block)
    if hasher.hexdigest()!=digest:raise ValueError('Evidence hash mismatch: '+name)
    return path


def verify_case(directory):
    directory=Path(directory);manifest=json.loads((directory/'report.json').read_text())
    for name,digest in manifest['artifact_sha256'].items():authenticated_file(directory,name,digest)
    if not REFERENCES<=set(manifest['source_sha256']):raise ValueError('Runtime reference closure incomplete')
    for name,digest in manifest['source_sha256'].items():
        authenticated_file(directory,'source_snapshots/'+name,digest)
    for cycle in manifest['contact_cycles']:
        authenticated_file(directory,cycle['directory']+'/report.json',cycle['report_sha256'])
        report=json.loads((directory/cycle['directory']/'report.json').read_text())
        for name,digest in report['artifact_sha256'].items():
            relative=cycle['directory']+'/'+name
            if manifest['artifact_sha256'].get(relative)!=digest:
                raise ValueError('Cycle/parent artifact hashes disagree')
    job=directory/manifest['final_cycle_directory']
    if not any(r['directory']==job.name for r in manifest['contact_cycles']):
        raise ValueError('Final cycle missing from history')
    record=json.loads((job/'input.json').read_text());data=(job/'frame.dat').read_text()
    replay=frame.assess(record,data)
    for name,value in replay.items():
        if manifest.get(name)!=value:raise ValueError('Numerical replay mismatch: '+name)
    diagnostic_stress=stress.assess(record,data)
    if diagnostic_stress!=manifest['diagnostic_stress']:raise ValueError('Stress replay mismatch')
    if manifest['qualified_for_design'] or manifest['actual_joint_demands_qualified']:
        raise ValueError('Unexpected qualification claim')
    passed=bool(manifest['contact_active_set_converged'] and replay['global_equilibrium_passed']
                and replay['mpc_check_passed'] and replay['closed_bearing_assumption_passed'])
    if passed!=manifest['contact_diagnostic_checks_passed']:raise ValueError('Contact acceptance mismatch')
    return {'directory':directory.name,'report_sha256':hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
            'diagnostic_checks_passed':passed,'qualified_for_design':False}


def verify(directory):
    directory=Path(directory)
    if not (directory/'summary.json').exists():return {'cases':[verify_case(directory)]}
    saved=json.loads((directory/'summary.json').read_text())
    if {r['case'] for r in saved['cases']}!={name for name,_ in batch.CASES}:
        raise ValueError('Batch case inventory mismatch')
    authenticated_file(directory,'batch-source.py',saved['batch_source_sha256'])
    results=[verify_case(directory/name) for name,_ in batch.CASES]
    rebuilt=batch.summary(directory)
    for key,value in rebuilt.items():
        if saved.get(key)!=value:raise ValueError('Batch summary replay mismatch: '+key)
    return {'cases':results,'common_load_panel_credit':rebuilt['common_load_panel_credit'],
            'qualified_for_design':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=verify(args.directory)
    result['replay_source_sha256']={str(Path(module.__file__).name):hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                                   for module in (frame,stress,batch)}
    result['verifier_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
