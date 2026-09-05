"""Publish only completed, independently balanced contact coupons."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from .joint_contact_results import audit, audit_deck


def checked(prefix):
    context = json.loads(prefix.with_suffix('.context.json').read_text())
    if context['name'] != prefix.name or context['geometry']['candidate'] != '2x8-foot100':
        raise ValueError('Changed contact candidate/job identity')
    audit_deck(prefix.with_suffix('.inp').read_text(), context)
    if hashlib.sha256((prefix.parent/'leg.step').read_bytes()).hexdigest() != context['geometry']['step_sha256']:
        raise ValueError('Frozen contact STEP changed')
    result = audit(prefix.with_suffix('.dat').read_text(), context,
                   prefix.with_suffix('.sta').read_text(), prefix.with_suffix('.log').read_text())
    record = {k: v for k, v in context.items() if k not in ('nodes', 'driven', 'pins')}
    record.update(result)
    run_path = prefix.with_suffix('.run.json')
    if run_path.exists():
        run = json.loads(run_path.read_text())
        if (run['input_sha256'] != hashlib.sha256(prefix.with_suffix('.inp').read_bytes()).hexdigest()
                or run['context_sha256'] != hashlib.sha256(prefix.with_suffix('.context.json').read_bytes()).hexdigest()):
            raise ValueError('Inputs changed since pre-solve freeze')
        record['execution_provenance'] = run
    else:
        record['execution_provenance'] = 'Early trial without pre-solve digest capture; intended deck independently checked, hashes below captured at re-audit, NOT immutable execution provenance'
    record['evidence_sha256'] = {prefix.with_suffix(suffix).name: hashlib.sha256(prefix.with_suffix(suffix).read_bytes()).hexdigest()
                                for suffix in ('.inp', '.dat', '.sta', '.cvg', '.log', '.context.json')}
    if run_path.exists():
        record['evidence_sha256'][run_path.name] = hashlib.sha256(run_path.read_bytes()).hexdigest()
    record['audit_source_sha256'] = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                                    for p in ('fea/record_joint_contact.py', 'fea/joint_contact_results.py')}
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    args = parser.parse_args()
    if args.name == 'inventory':
        output = Path('fea/results/joint_contact')
        output.mkdir(parents=True, exist_ok=True)
        trials = []
        for path in sorted(Path('fea/generated/joint_contact').glob('contact_*.context.json')):
            prefix = path.with_name(path.name.removesuffix('.context.json'))
            context = json.loads(path.read_text())
            log = prefix.with_suffix('.log').read_text()
            row = {'name': prefix.name, 'parameters': context['args'],
                   'solver_reported_finished': 'Job finished' in log and '*ERROR' not in log.upper(),
                   'source_sha256': context['solver_source_sha256'],
                   'prelaunch_digest_capture': prefix.with_suffix('.run.json').exists(),
                   'evidence_sha256': {prefix.with_suffix(suffix).name: hashlib.sha256(prefix.with_suffix(suffix).read_bytes()).hexdigest()
                                       for suffix in ('.inp', '.dat', '.sta', '.log', '.context.json')}}
            try:
                record = checked(prefix)
                row['status'] = 'NUMERICAL AUDIT ACCEPTED; NOT PHYSICAL VALIDATION'
                row['driven_force_axis_n'] = record['driven_force_axis_n']
            except ValueError as error:
                row['status'] = 'REJECTED NUMERICAL AUDIT; NOT PHYSICAL FAILURE'
                row['reason'] = str(error)
            trials.append(row)
        (output/'trial_inventory.json').write_text(json.dumps(trials, indent=2)+'\n')
        print(f'{len(trials)} completed trial records')
        return
    if '/' in args.name or not args.name.startswith('contact_'):
        parser.error('Expected local contact job name')
    record = checked(Path('fea/generated/joint_contact')/args.name)
    output = Path('fea/results/joint_contact')
    output.mkdir(parents=True, exist_ok=True)
    (output/(args.name+'.json')).write_text(json.dumps(record, indent=2)+'\n')
    if args.name == 'contact_S_8_100000_0p2375':
        bundle = output/'reference_raw'
        bundle.mkdir(parents=True, exist_ok=True)
        raw = Path('fea/generated/joint_contact')
        for filename in (*record['evidence_sha256'], 'leg.step'):
            (bundle/(filename+'.gz')).write_bytes(gzip.compress((raw/filename).read_bytes(), mtime=0))
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
