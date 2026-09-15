"""Bounded native search blocks; no physical or acceptance changes."""
import gzip
import hashlib
import json
import shutil
from pathlib import Path

from guarded_coulomb_aitken_seed import build as accelerated_seed

from fea.current_coulomb_run import run
from mini_moonboard import compact_exterior_brace_frame as model
from scripts.clear_space_batch import CASES, archive
from scripts.compact_rail_study import bolt_properties

ROOT = Path('fea/generated/exterior-finish-control')
ARCHIVES = Path('fea/results/exterior-revised-cells04')
GEOMETRY = Path('fea/generated/exterior-revised-geometry.json')
REMAINING = ('a12-forward','k12-right','k12-rear','a1-rear')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def simple_seed(report, native=None):
    result = {'initial_contact_names':[b['name'] for b in report['bearings'] if b['active']],
            'initial_tangent_secants':{n:v['next_secant_n_per_mm']
                                      for n,v in report['floor_friction_law']['feet'].items()}}
    if native is not None and not report['closed_bearing_assumption_passed']:
        job = native/report['contact_cycles'][-1]['directory']
        record = json.loads((job/'input.json').read_text())
        names = set(result['initial_tangent_secants'])
        values = {name: {s['stiffness_n_per_mm'] for s in record['springs'] if s['name'] == name}
                  for name in names}
        if any(len(v) != 1 for v in values.values()):
            raise ValueError('Missing or inconsistent actual last-cycle tangent stiffness')
        result['initial_tangent_secants'] = {name: next(iter(v)) for name,v in values.items()}
        result['seed_basis'] = 'Normal contact invalid: preserve actual last input stiffness'
        result['last_input_sha256'] = {str(job/'input.json'): digest(job/'input.json')}
    return result


def archive_search(case):
    destination = ARCHIVES/case/'search'
    destination.mkdir()
    files = [Path(__file__), Path('/tmp/guarded_coulomb_aitken_seed.py'),
             ROOT/'controller-provenance.json', ROOT/'history.json', *ROOT.glob(case+'-seed-*.json')]
    for path in files:
        shutil.copy2(path, destination/path.name)
    evidence = {str(path): digest(path) for path in (ROOT/case).rglob('*') if path.is_file()}
    manifest = {'scope': 'Search provenance only; unchanged native acceptance manifest remains authoritative',
                'files': {path.name: digest(path) for path in destination.iterdir()},
                'retained_full_native_block_files': evidence}
    (ARCHIVES/case/'search-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


def main():
    previous = ARCHIVES/'a12-rear'
    manifest = json.loads((previous/'manifest.json').read_text())
    for name, sha in manifest['files'].items():
        if digest(previous/name) != sha:
            raise ValueError('Rear archive checksum mismatch: '+name)
    report = json.loads(gzip.decompress((previous/'report.json.gz').read_bytes()))
    assessment = json.loads((previous/'assessment.json').read_text())
    if (report.get('numerically_accepted') is not True or report['candidate'] != model.KEY
            or report['floor_friction_law']['mu_assumed'] != .4
            or not assessment.get('criteria') or not all(assessment['criteria'].values())):
        raise ValueError('Require the accepted, passing current rear case at mu0.4')
    if any((ARCHIVES/case).exists() for case in REMAINING):
        raise FileExistsError('A remaining final archive already exists; preserve it')
    ROOT.mkdir(parents=True,exist_ok=False)
    provenance = {str(p):digest(p) for p in (Path(__file__),Path('/tmp/guarded_coulomb_aitken_seed.py'),
                                            GEOMETRY,previous/'report.json.gz',previous/'assessment.json')}
    (ROOT/'controller-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    bolts = {c.name:bolt_properties(c) for c in model.connections() if c.kind == 'bolt'}
    contacts = [{**row,'stiffness_n_per_mm':100.*row['tributary_area_mm2']}
                for row in model.overlap_contact_datums()]
    history = []
    for case in REMAINING:
        hold, force = CASES[case]
        seed, damping, consumed = simple_seed(report), .5, 0
        for block in range(8):
            native = ROOT/case/f'block-{block:02d}'
            seed_path = ROOT/f'{case}-seed-{block:02d}.json'
            seed_path.write_text(json.dumps({**seed,'damping':damping,'provenance':provenance},indent=2)+'\n')
            report = run(native,module=model,mu=.4,damping=damping,max_cycles=min(30,240-consumed),
                **{k:seed[k] for k in ('initial_contact_names','initial_tangent_secants')},
                bolt_stiffness={**next(iter(bolts.values())),'by_name':bolts},member_contacts=contacts,
                hold=hold,pounds=250.,horizontal_force=force,leg_floor_grid=3,patch_size=20.)
            consumed += len(report['contact_cycles'])
            entry = {'case':case,'block':block,'native':str(native),'seed_file':str(seed_path),
                     'iterations_this_case':consumed,'numerically_accepted':report['numerically_accepted'],
                     'termination':report['termination']}
            history.append(entry)
            print(json.dumps(entry),flush=True)
            (ROOT/'history.json').write_text(json.dumps(history,indent=2)+'\n')
            if report['numerically_accepted']:
                result = archive(native,GEOMETRY,ARCHIVES/case,model)
                archive_search(case)
                if not result.get('criteria') or not all(result['criteria'].values()):
                    raise SystemExit('Actual design check failed: '+case)
                break
            if consumed >= 240:
                raise SystemExit('Numerical budget exhausted: '+case)
            try:
                candidate_seed = accelerated_seed(native)
                if candidate_seed['extrapolated_count'] == 0:
                    raise ValueError('No cell meets guarded acceleration conditions')
                seed, damping = candidate_seed, 1.
            except ValueError as exc:
                seed, damping = {**simple_seed(report,native),'acceleration_rejected':str(exc)}, .5
        else:
            raise SystemExit('Eight-block numerical budget exhausted: '+case)
    print('Four remaining cases passed; existing rear and left archives retained.',flush=True)


if __name__ == '__main__':
    main()
