"""Independent scalar Newmark oracle for the free balanced-force unit cube."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from fea.wood_joint_port_coupon_audit import read_dat, matrices


def audit(folder):
    k,m=matrices(); mass=2.5e-10
    signs=np.array([-1,1,1,-1,-1,1,1,-1])
    results={}
    for path in sorted(folder.glob('force_*.dat')):
        data=read_dat(path)
        q=v=a=old_t=old_force=work=0.
        max_u=max_v=max_se=max_ke=max_center=0.
        native_work=0.; old_native_q=0.
        for t,row in sorted(data.items()):
            dt=t-old_t; force=.01*(t/1e-4)**3
            qp=q+dt*v+.25*dt*dt*a
            qn=(force+4*mass/dt**2*qp)/(1+4*mass/dt**2)
            an=4*(qn-qp)/dt**2; vn=v+dt*(a+an)/2
            u=np.array([row['displacements'][n][0] for n in range(1,9)])
            velocity=np.array([row['velocities'][n][0] for n in range(1,9)])
            uq=signs@u/4
            work+=(force+old_force)*(qn-q)/2
            native_work+=(force+old_force)*(uq-old_native_q)/2
            se=float(u@k@u/2); ke=float(velocity@m@velocity/2)
            max_u=max(max_u,float(np.max(abs(u-signs*qn/2))))
            max_v=max(max_v,float(np.max(abs(velocity-signs*vn/2))))
            max_se=max(max_se,abs(se-qn**2/2))
            max_ke=max(max_ke,abs(ke-mass*vn**2/2))
            max_center=max(max_center,abs(float(u.mean())))
            q,v,a,old_t,old_force=qn,vn,an,t,force
            old_native_q=uq
        scales={'u':max(abs(q)/2,1e-6),'v':max(abs(v)/2,1e-6),
                'se':max(q*q/2,1e-6),'ke':max(mass*v*v/2,1e-6)}
        dat=path.read_text()
        printed_se=[float(x) for x in re.findall(r'total internal energy for set CUBE and time\s+\S+\s+([\d.Ee+-]+)',dat)]
        printed_ke=[float(x) for x in re.findall(r'total kinetic energy for set CUBE and time\s+\S+\s+([\d.Ee+-]+)',dat)]
        stdout=path.with_suffix('.stdout').read_text()
        printed_work=float(re.findall(r'external work =\s+([\d.Ee+-]+)',stdout)[-1])
        passed=(len(data)==100 and len(printed_se)==100 and len(printed_ke)==100 and abs(old_t-1e-4)<1e-12 and
                max_u<=1e-10+1e-4*scales['u'] and max_v<=1e-10+1e-4*scales['v'] and
                max_se<=1e-10+1e-4*scales['se'] and max_ke<=1e-10+1e-4*scales['ke'] and
                max_center<=1e-10 and abs(native_work-se-ke)<=1e-10+1e-4*(se+ke) and
                abs(printed_se[-1]-se)<=1e-10+1e-4*se and abs(printed_ke[-1]-ke)<=1e-10+1e-4*ke and
                abs(printed_work-native_work)<=1e-10+1e-4*abs(native_work))
        results[path.stem]={'method_fixture_pass':bool(passed),'accepted_states':len(data),
                           'max_displacement_error_mm':max_u,'max_velocity_error_mm_s':max_v,
                           'max_strain_energy_error_Nmm':max_se,'max_kinetic_energy_error_Nmm':max_ke,
                           'max_mass_center_displacement_mm':max_center,
                           'final_q_mm':float(uq),'oracle_final_q_mm':q,
                           'final_strain_energy_Nmm':se,'final_kinetic_energy_Nmm':ke,
                           'applied_force_work_from_native_U_Nmm':float(native_work),
                           'native_work_minus_SE_KE_Nmm':float(native_work-se-ke),
                           'native_printed_final_ELSE_Nmm':printed_se[-1],
                           'native_printed_final_ELKE_Nmm':printed_ke[-1],
                           'native_printed_external_work_Nmm':printed_work,
                           'oracle_energy_defect_Nmm':work-q*q/2-mass*v*v/2,
                           'dat_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    result={'method_fixture_pass':len(results)==2 and all(r['method_fixture_pass'] for r in results.values()),
            'mechanical_acceptance':False,'cases':results}
    (folder/'independent-force-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    (folder/'independent-force-auditor.py.snapshot').write_bytes(Path(__file__).read_bytes())
    (folder/'independent-integration.py.snapshot').write_bytes(Path(__file__).with_name('wood_joint_port_coupon_audit.py').read_bytes())
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    print(json.dumps(audit(parser.parse_args().folder),indent=2))
