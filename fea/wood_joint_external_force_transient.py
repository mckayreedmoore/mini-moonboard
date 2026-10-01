"""Freeze and execute a bounded free-assembly external-member force transient."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time

from fea.wood_joint_external_port_transient import SOURCE, SOURCE_LOCK, SOURCE_LOCK_SHA, cards, rows, sha
from fea.wood_joint_current_port_motion_audit import audit as audit_source
from fea.wood_joint_current_transient_launch import IncrementalMonitor, digest

INCLUDES = ('mesh.inp','materials.inp','nut-coupling.inp','rigid-carriers.inp',
            'contact-fragment.inc','output-sets.inp')
PROFILE = Path(__file__).with_name('calculix_223')/'solver-profile.json'


def prepare(folder: Path):
    profile=json.loads(PROFILE.read_text())
    if profile['balanced_force_fixture_pass'] is not True:
        raise ValueError('toolchain force fixture gate missing')
    manual=Path(__file__).resolve().parents[1]/profile['manual']['local_path']
    if sha(manual)!=profile['manual']['sha256']:
        raise ValueError('pinned solver manual changed')
    if sha(SOURCE/SOURCE_LOCK)!=SOURCE_LOCK_SHA:
        raise ValueError('source lock changed')
    source_lock=json.loads((SOURCE/SOURCE_LOCK).read_text())
    pins=source_lock['input_sha256']|{SOURCE_LOCK:SOURCE_LOCK_SHA}
    if any(sha(SOURCE/n)!=h for n,h in pins.items()):
        raise ValueError('source artifact changed')
    source_audit=audit_source(SOURCE,'n_plus')
    folder.mkdir(parents=True,exist_ok=True)
    if any(p.name!='README.md' for p in folder.iterdir()):
        raise FileExistsError('preserve previous attempt')
    for name in pins:
        (folder/name).write_bytes((SOURCE/name).read_bytes())
    ports=json.loads((SOURCE/'external-ports.json').read_text())
    blocks=cards((SOURCE/'response_n_plus.inp').read_text())
    forces={}
    for header,data in blocks:
        if header.startswith('*CLOAD'):
            for row in data:
                node,dof,value=row.split(',')
                forces.setdefault(int(node),[0.,0.,0.])[int(dof)-1]+=float(value)
    allowed={n for p in ports['ports'].values() for n in p['node_ids']}
    if set(forces)!=allowed or len(forces)!=86:
        raise ValueError('loads must occupy both complete external caps only')
    controls=ports['nut_control_node_monitor_ids']
    monitor=sorted(allowed|set(controls))
    extra=['*NSET,NSET=PILOT_MONITOR',*rows(monitor)]
    for name,port in ports['ports'].items():
        extra.append('*SURFACE,NAME=WJ_'+name.upper()+'_SECTION')
        extra.extend(f'{e},S{s}' for e,s in port['face_refs_element_side'])
    (folder/'force-output-sets.inp').write_text('\n'.join(extra)+'\n')
    ramp=[(float(f'{i*.1/200:.12g}'),float(f'{(i/200)**3*(10-15*i/200+6*(i/200)**2):.12g}')) for i in range(201)]
    ramp.append((.125,1.))
    deck=['** Free-assembly external-member transient; no physical support or prescribed motion.']
    for name in INCLUDES:
        if any(h.startswith(('*BOUNDARY','*INITIAL CONDITIONS','*DAMPING')) for h,d in cards((folder/name).read_text())):
            raise ValueError('unexpected support, initial condition or damping')
        deck.append('*INCLUDE,INPUT='+name)
    deck.extend(['*INCLUDE,INPUT=force-output-sets.inp','*AMPLITUDE,NAME=EXTERNAL_FORCE'])
    deck.extend(f'{t:.12g},{a:.12g}' for t,a in ramp)
    deck.extend(['*STEP,NLGEOM,INC=1000','*DYNAMIC,ALPHA=0','0.001,0.125,1e-6,0.0025',
                 '*CLOAD,AMPLITUDE=EXTERNAL_FORCE'])
    for node,force in sorted(forces.items()):
        deck.extend(f'{node},{d+1},{f:.13e}' for d,f in enumerate(force))
    deck.extend(['*NODE PRINT,NSET=PILOT_MONITOR,FREQUENCY=1','U,V',
                 '*NODE PRINT,NSET=CURRENT_ALL_PHYSICAL_NODES,FREQUENCY=1','U,V',
                 '*NODE FILE,NSET=CURRENT_ALL_PHYSICAL_NODES,FREQUENCY=1','U,V',
                 '*SECTION PRINT,SURFACE=WJ_RAIL_SECTION,NAME=WJ_RAIL_PORT','SOF',
                 '*SECTION PRINT,SURFACE=WJ_PRINCIPAL_SECTION,NAME=WJ_PRINCIPAL_PORT','SOF',
                 '*EL FILE,FREQUENCY=1','S,E',
                 '*EL PRINT,ELSET=CURRENT_ALL_ELEMENTS,TOTALS=ONLY,FREQUENCY=1','ELSE,ELKE,EMAS,EVOL',
                 '*EL PRINT,ELSET=CURRENT_NUT_CARRIERS,TOTALS=ONLY,FREQUENCY=1','ELSE,ELKE'])
    motion_blocks=cards((SOURCE/'port_motion_n_plus.inp').read_text())
    for header,data in motion_blocks:
        if header.startswith('*CONTACT PRINT'):
            deck.extend([header,*data])
    deck.extend(['*CONTACT FILE,FREQUENCY=1','CDIS,CSTR,CELS','*END STEP'])
    (folder/'pilot.inp').write_text('\n'.join(deck)+'\n')
    (folder/'source-independent-audit.json').write_text(json.dumps(source_audit,indent=2)+'\n')
    (folder/'force-producer-runner.py.snapshot').write_bytes(Path(__file__).read_bytes())
    (folder/'incremental-monitor.py.snapshot').write_bytes(Path(__file__).with_name('wood_joint_current_transient_launch.py').read_bytes())
    (folder/'solver-profile.json').write_bytes(PROFILE.read_bytes())
    freeze={'schema':'wood_joint_external_force_transient/v1',
            'revision':ports['revision'],'solver_image':profile['image_id'],
            'solver_binary_sha256':profile['binary_sha256'],'solver_binary_path':profile['binary_path'],
            'solver_version':profile['version'],'manual':profile['manual'],
            'source_lock_sha256':SOURCE_LOCK_SHA,'source_artifacts_sha256':pins,
            'status':'FROZEN_REQUIRES_INDEPENDENT_READINESS_AUDIT',
            'case':'n_plus','force_scale_N':1.,'amplitude_points':ramp,
            'ramp_s':.1,'hold_s':.025,'initial_dt_s':.001,'max_dt_s':.0025,'minimum_dt_s':1e-6,
            'alpha':0,'mass_scaling':False,'damping':False,'cleat_restraint':False,
            'whole_assembly_support':False,'port_motion_equations':False,
            'physical_inputs_unchanged':True,'nut_engagement':'retained stiff scenario, not delivered hardware',
            'monitor_nodes':monitor,'rotation_nodes':controls[1::2],
            'serialized_unit_load_nodes':{str(n):{'force_xyz_n':f} for n,f in forces.items()},
            'sampled_travel_stop_mm':1.3,'sampled_loaded_node_displacement_stop_mm':5.,
            'sampled_controller_rotation_stop_rad':.05,
            'travel_limit_interpretation':'diagnostic bound on force-dual coordinate; not a predicted bore event',
            'resource_bounds':{'cpus':2,'memory_gib':12,'wallclock_seconds':3600,'no_accepted_state_seconds':600},
            'diagnostic_gates':{'energy_balance_relative':.05,'energy_floor_Nmm':1e-5,
                                'inertial_force_balance_relative':.01,'force_floor_N':.01,
                                'moment_floor_Nmm':10.,'KE_over_SE_plus_contact_for_quasistatic':.05,
                                'matched_rate_and_timestep_response_relative':.05},
            'scope':'bounded dynamic external-member diagnostic; not static response or capacity',
            'mechanical_acceptance':False}
    freeze['artifacts_sha256']={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
    (folder/'force-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
    return {'files':len(freeze['artifacts_sha256']),'monitor_nodes':len(monitor),'status':freeze['status']}


def run(folder: Path):
    freeze=json.loads((folder/'force-freeze.json').read_text())
    audit=json.loads((folder/'independent-readiness.json').read_text())
    if audit.get('ready_for_bounded_dynamic_diagnostic') is not True or audit.get('freeze_sha256')!=sha(folder/'force-freeze.json'):
        raise ValueError('missing matching independent readiness audit')
    pins=freeze['artifacts_sha256']
    if any(sha(folder/n)!=h for n,h in pins.items()):
        raise ValueError('frozen inputs changed')
    if (folder/'execution.json').exists():
        raise FileExistsError('preserve existing execution')
    live=subprocess.check_output(['docker','ps','--format','{{.Names}} {{.Command}}'],text=True)
    if any('wj-' in line or 'ccx' in line.lower() for line in live.splitlines()):
        raise RuntimeError('another native job is active')
    if subprocess.run(['pgrep','-x','ccx'],capture_output=True).returncode==0:
        raise RuntimeError('another native solver process is active')
    actual=subprocess.check_output(['docker','run','--rm','--network','none',freeze['solver_image'],'sha256sum',freeze['solver_binary_path']],text=True).split()[0]
    if actual!=freeze['solver_binary_sha256']:
        raise ValueError('pinned binary mismatch')
    name='wj-external-force-'+sha(folder/'force-freeze.json')[:12]
    command=['docker','run','--name',name,'--network','none','--cpus','2','--memory','12g',
             '--user',f'{os.getuid()}:{os.getgid()}','--env','OMP_NUM_THREADS=2',
             '--env','CCX_NPROC_EQUATION_SOLVER=2','--mount',f'type=bind,src={folder},dst=/work',
             '--workdir','/work',freeze['solver_image'],freeze['solver_binary_path'],'-i','pilot']
    record={'status':'running','started_utc':datetime.now(timezone.utc).isoformat(),
            'command':command,'freeze_sha256':sha(folder/'force-freeze.json'),
            'independent_readiness_sha256':sha(folder/'independent-readiness.json'),
            'solver_binary_sha256':actual,'mechanical_acceptance':False,'observations':[]}
    def save():
        (folder/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
    def stop(reason):
        record['status']=reason
        subprocess.run(['docker','kill',name],capture_output=True,check=False)
    monitor=IncrementalMonitor(freeze); started=time.monotonic();save()
    with (folder/'pilot.stdout').open('x') as out:
        proc=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT)
        try:
            while proc.poll() is None:
                record['observations']=monitor.poll(folder/'pilot.dat')
                elapsed=time.monotonic()-started
                if any(r['stop_reasons'] for r in record['observations']):
                    stop('sampled_motion_limit');break
                if not record['observations'] and elapsed>freeze['resource_bounds']['no_accepted_state_seconds']:
                    stop('no_accepted_state_timeout');break
                if elapsed>freeze['resource_bounds']['wallclock_seconds']:
                    stop('bounded_timeout');break
                record['elapsed_seconds']=elapsed;save();time.sleep(2)
        except BaseException as exc:
            record['monitor_error']=repr(exc);stop('monitor_or_parent_interruption')
        record['returncode']=proc.wait(timeout=30)
    state=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]['State']
    if state['Running']:
        raise RuntimeError('native container still running; cannot freeze output')
    record['container_state']=state
    record['observations']=monitor.poll(folder/'pilot.dat')
    if record['status']=='running':
        record['status']='process_finished' if record['returncode']==0 else 'process_failed'
    record['elapsed_seconds']=time.monotonic()-started
    record['ended_utc']=datetime.now(timezone.utc).isoformat()
    record['frozen_inputs_unchanged']=all(sha(folder/n)==h for n,h in pins.items())
    record['outputs_sha256']={p.name:digest(p) for p in folder.glob('pilot.*') if p.name not in pins}
    save()
    return {k:record[k] for k in ('status','returncode','elapsed_seconds','observations')}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','run']);parser.add_argument('folder',type=Path)
    args=parser.parse_args()
    print(json.dumps((prepare if args.action=='prepare' else run)(args.folder.resolve()),indent=2))
