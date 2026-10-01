"""Extract external force-dual motion and work from a terminal native record.

This is a port/energy observation, not a full body-equilibrium audit.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import numpy as np
from fea.wood_joint_current_transient_launch import IncrementalMonitor, digest
from fea.wood_joint_external_port_transient import sha
from fea.wood_joint_current_transient_history import _native_work_samples


def extract(folder):
    freeze=json.loads((folder/'force-freeze.json').read_text())
    execution=json.loads((folder/'execution.json').read_text())
    if execution['status']=='running' or execution.get('container_state',{}).get('Running',True):
        raise ValueError('terminal native evidence required')
    if execution['freeze_sha256']!=sha(folder/'force-freeze.json'):
        raise ValueError('freeze mismatch')
    if any(digest(folder/name)!=h for name,h in execution['outputs_sha256'].items()):
        raise ValueError('terminal output changed')
    ports=json.loads((folder/'external-ports.json').read_text())
    basis=np.array(ports['frame']['basis_columns_global_xyz'])
    origin=np.array(ports['frame']['origin_global_xyz_mm'])
    length=ports['frame']['rotation_length_mm']
    header=re.compile(r'displacements .* set PILOT_MONITOR and time\s+(\S+)')
    energy_header=re.compile(r'total (internal energy|kinetic energy|mass) for set CURRENT_ALL_ELEMENTS and time\s+(\S+)')
    fields={}; energies={}; active=None; current=None; energy_key=None
    expected=set(freeze['monitor_nodes'])
    with (folder/'pilot.dat').open() as stream:
        for line in stream:
            found=header.search(line)
            if found:
                current=float(found.group(1)); active={}; energy_key=None;continue
            found=energy_header.search(line)
            if found:
                current=float(found.group(2));energy_key=found.group(1);active=None;continue
            parts=line.split()
            if not parts:continue
            if energy_key:
                if len(parts)==1:
                    energies.setdefault(current,{})[energy_key]=float(parts[0]);energy_key=None
                continue
            if active is not None:
                if len(parts)!=4 or not parts[0].isdigit():
                    active=None;continue
                node=int(parts[0])
                if node not in expected or node in active:raise ValueError('unexpected monitor node')
                active[node]=list(map(float,parts[1:]))
                if set(active)==expected:
                    fields[current]=active;active=None
    amplitude=np.array(freeze['amplitude_points'])
    native_work=_native_work_samples((folder/'pilot.stdout').read_text())
    old_q=old_factor=work=0.;samples=[]
    for t,field in sorted(fields.items()):
        q=sum(float(f)*field[int(n)][d] for n,row in freeze['serialized_unit_load_nodes'].items() for d,f in enumerate(row['force_xyz_n']))
        port_q={};actual_moment=np.zeros(3);actual_force=np.zeros(3)
        for name,port in ports['ports'].items():
            displacements=np.array([field[n] for n in port['node_ids']])
            qp=np.array(port['displacement_map_C'])@displacements.reshape(-1)
            theta=basis@qp[3:]/length
            uj=basis@qp[:3]+np.cross(theta,origin-np.array(port['port_origin_global_xyz_mm']))
            port_q[name]=np.r_[basis.T@uj,qp[3:]].tolist()
            force=np.array([freeze['serialized_unit_load_nodes'][str(n)]['force_xyz_n'] for n in port['node_ids']])
            actual_force+=force.sum(axis=0)
            actual_moment+=np.cross(np.array(port['global_xyz_mm'])+displacements-origin,force).sum(axis=0)
        difference=np.array(port_q['rail'])-port_q['principal']
        if abs(q-difference[2])>1e-8*max(1.,abs(q)):
            raise ValueError('nodal work coordinate differs from projected joint-relative N')
        factor=float(np.interp(t,amplitude[:,0],amplitude[:,1]))
        work+=(factor+old_factor)*(q-old_q)/2
        work_matches=[row for row in native_work if abs(row['time_seconds']-t)<=1e-8*max(1.,abs(t))]
        native_work_value=work_matches[-1]['external_work_nmm'] if work_matches else None
        samples.append({'time_s':t,'applied_factor_N':factor,'force_dual_q_mm':q,
                        'relative_projected_motion_mm_and_scaled_rotation':difference.tolist(),
                        'port_joint_datum_motion':port_q,'applied_trapezoid_work_Nmm':work,
                        'applied_actual_force_N':(factor*actual_force).tolist(),
                        'applied_actual_moment_about_joint_Nmm':(factor*actual_moment).tolist(),
                        'native_external_work_Nmm':native_work_value,
                        'native_minus_nodal_trapezoid_work_Nmm':None if native_work_value is None else native_work_value-work,
                        'native_totals':energies.get(t,{})})
        old_q,old_factor=q,factor
    result={'schema':'wood_joint_external_force_history/v1','freeze_sha256':sha(folder/'force-freeze.json'),
            'execution_sha256':sha(folder/'execution.json'),'samples':samples,
            'mechanical_acceptance':False,
            'limits':['Port observations only; not full joint or body equilibrium.',
                      'Trapezoidal nodal work needs timestep comparison for nonlinear paths.',
                      'Energy balance also requires contact energy and native total-work history.',
                      'Incomplete trailing fields are omitted; monitor output is not a complete-state proof.']}
    (folder/'external-port-history.json').write_text(json.dumps(result,indent=2)+'\n')
    (folder/'external-port-history.py.snapshot').write_bytes(Path(__file__).read_bytes())
    return {'samples':len(samples),'last':samples[-1] if samples else None}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path)
    print(json.dumps(extract(p.parse_args().folder),indent=2))
