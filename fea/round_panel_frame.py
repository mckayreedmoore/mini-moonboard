"""Fresh round-bore frame diagnostic; preparation/solve authorized separately from geometry."""
from pathlib import Path

from fea import horizontal_panel_frame as frame

current_frame, record_structure, assess = frame.current_frame, frame.record_structure, frame.assess
panel_kernel, next_bearing_set = frame.panel_kernel, frame.next_bearing_set


def source_hashes():
    import hashlib
    sources = frame.source_hashes()
    for path in (Path(__file__), Path('docs/round-service-wiring-reference.json'),
                 Path('docs/round-panel-countersink-reference.json')):
        sources[str(path.resolve().relative_to(Path.cwd()))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return sources


def run_current(directory, **parameters):
    import hashlib
    import json
    import os
    import subprocess
    from pathlib import Path

    from fea import horizontal_frame_stress
    from mini_moonboard import round_service_frame as module
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    sources=source_hashes()
    structure,metadata=current_frame(module,**parameters)
    metadata['round_service_bores']=module.bore_records()
    metadata['panel_screw_count']=sum(isinstance(c,module.timber.PanelScrew) for c in module.connections())
    metadata['round_geometry_transfer_limit']='Fresh retained-section extraction; no force/stiffness acceptance transferred from old open-channel geometry. Countersunk heads, wood pilots and local hardware contact remain absent from mechanics.'
    metadata['stress_output']={'global':True,'variables':['S','COORD'],
                              'integration_points':{'C3D20':27,'S8':27}}
    for name in sources:
        target=directory/'source_snapshots'/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(Path(name).read_bytes())
    if sources!=source_hashes():raise ValueError('Source changed during preparation')
    active={r['name'] for r in structure.springs if r['bearing_closed_assumption']}
    seen=set();history=[];converged=False
    for iteration in range(12):
        signature=tuple(sorted(active))
        if signature in seen:break
        seen.add(signature)
        job=directory/f'cycle-{iteration:02d}';job.mkdir()
        record=record_structure(structure,metadata,active)
        (job/'input.json').write_text(json.dumps(record,indent=2)+'\n')
        (job/'frame.inp').write_text(structure.deck(active_bearings=active,stress=True))
        command=['docker','run','--rm','--network=none','--cpus=1','--memory=4g','--user',f'{os.getuid()}:{os.getgid()}',
                 '-e','OMP_NUM_THREADS=1','-v',f'{job.resolve()}:/output','-w','/output',panel_kernel.IMAGE,
                 'timeout','180s','ccx','-i','frame']
        result=subprocess.run(command,capture_output=True,text=True,timeout=200,check=False)
        log=result.stdout+result.stderr;(job/'frame.log').write_text(log)
        if result.returncode or '*ERROR' in log.upper():raise ValueError('Native frame solve failed; inspect raw cycle log')
        data=(job/'frame.dat').read_text()
        report=assess(record,data)
        report['diagnostic_stress']=horizontal_frame_stress.assess(record,data)
        if sources!=source_hashes():raise ValueError('Source changed during solve')
        report['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in job.iterdir() if p.is_file()}
        (job/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        history.append({'directory':job.name,'active_bearings':list(signature),
                        'bearing_complementarity_passed':report['closed_bearing_assumption_passed'],
                        'report_sha256':hashlib.sha256((job/'report.json').read_bytes()).hexdigest()})
        if report['closed_bearing_assumption_passed']:
            converged=True;break
        active=next_bearing_set(report['bearings'])
    report={**report,'contact_active_set_converged':converged,'contact_cycles':history,
            'contact_cycle_limit':12,'contact_gap_tolerance_mm':1.e-7,
            'bearing_penalty_n_per_mm':1.e6,'final_cycle_directory':history[-1]['directory'],
            'contact_diagnostic_checks_passed':bool(converged and report['global_equilibrium_passed'] and report['mpc_check_passed']),
            'parameters':parameters,'solver_image':panel_kernel.IMAGE,'source_sha256':sources}
    report['artifact_sha256']={str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in directory.rglob('*') if p.is_file()}
    (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hold', choices=('C10','F10','C6'), default='C10')
    args = parser.parse_args()
    report = run_current(args.output, hold=args.hold, stiffness=1000., mode='coupled',
                         pounds=250., load_kind='full', frame_size=100., panel_size=80., patch_size=20.)
    print({key: report[key] for key in ('contact_diagnostic_checks_passed',
          'maximum_panel_displacement_mm','maximum_timber_displacement_mm','qualified_for_design')})
