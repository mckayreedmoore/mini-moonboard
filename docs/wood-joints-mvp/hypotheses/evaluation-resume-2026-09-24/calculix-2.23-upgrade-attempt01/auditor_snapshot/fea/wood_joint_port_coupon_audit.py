"""Independent C3D8 integration and dynamic balance audit of the unit coupons."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np


def matrices():
    # Independently integrate the scalar axial subspace. All transverse DOFs
    # are fixed in this fixture. E=1, nu=0 gives lambda=0 and mu=1/2.
    signs = np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
                      [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]])
    k = np.zeros((8,8)); m = np.zeros((8,8))
    for x in (-1/np.sqrt(3), 1/np.sqrt(3)):
        for y in (-1/np.sqrt(3), 1/np.sqrt(3)):
            for z in (-1/np.sqrt(3), 1/np.sqrt(3)):
                factors = 1 + signs * [x,y,z]
                n = factors.prod(axis=1)/8
                dn = np.array([signs[:,d]*factors[:,[i for i in range(3) if i != d]].prod(axis=1)/4 for d in range(3)])
                k += (np.outer(dn[0],dn[0]) + .5*np.outer(dn[1],dn[1]) + .5*np.outer(dn[2],dn[2]))/8
                m += 3e-9*np.outer(n,n)/8
    return k,m


def read_dat(path):
    data = {}
    kind = None
    for line in path.read_text().splitlines():
        match = re.search(r'(displacements|forces|velocities) .* time\s+(\S+)',line)
        if match:
            kind,t = match.group(1),float(match.group(2))
            data.setdefault(t,{})[kind] = {}
        elif line.strip() and kind:
            fields=line.split()
            if len(fields)==4 and fields[0].isdigit():
                data[t][kind][int(fields[0])] = list(map(float,fields[1:]))
            else:
                kind=None
    return data


def audit(folder):
    k,m=matrices()
    cap=[1,2,5,6]
    kr=k[np.ix_(cap,cap)]; mr=m[np.ix_(cap,cap)]
    # x=[4*q-y1-y2-y3, y1, y2, y3]. Homogeneous reduction T
    # plus prescribed-motion lift g. True inertia includes T.T M g qddot.
    T=np.vstack((-np.ones(3),np.eye(3))); g=np.array([4.,0.,0.,0.])
    def predict(times, include_prescribed_inertia):
        km=T.T@kr@T; mm=T.T@mr@T
        y=np.zeros(3); v=y.copy(); a=y.copy(); qold=qv=qa=told=0.
        answer=[]
        for t in times:
            dt=t-told; q=.01*(t/1e-4)**3
            qanew=4*(q-qold)/dt**2-4*qv/dt-qa
            qvnew=2*(q-qold)/dt-qv
            yp=y+dt*v+dt**2*a/4
            rhs=-T.T@kr@g*q+4/dt**2*mm@yp
            if include_prescribed_inertia:
                rhs-=T.T@mr@g*qanew
            yn=np.linalg.solve(km+4/dt**2*mm,rhs)
            an=4*(yn-yp)/dt**2; vn=v+dt*(a+an)/2
            answer.append(T@yn+g*q)
            y,v,a,qold,qv,qa,told=yn,vn,an,q,qvnew,qanew,t
        return np.array(answer)
    reports={}
    for path in sorted(folder.glob('*.dat')):
        data=read_dat(path)
        old_u=np.zeros(8); old_v=np.zeros(8); old_a=np.zeros(8); old_t=0.
        old_qforce=0.; old_q=0.; work=0.
        max_res=0.; max_omitted_res=0.; max_rf_error=0.; max_warp=0.
        final={}
        for t,row in sorted(data.items()):
            u=np.array([row['displacements'][n][0] for n in range(1,9)])
            rf=np.array([row['forces'][n][0] for n in range(1,9)])
            dyn='velocities' in row
            dt=t-old_t
            if dyn:
                # Reconstruct acceleration from displacement, without
                # differentiating the rounded printed velocity a second time.
                a=4*(u-old_u)/dt**2-4*old_v/dt-old_a
                v=2*(u-old_u)/dt-old_v
            else:
                a=np.zeros(8); v=np.zeros(8)
            r=k@u+m@a
            q=float(u[cap].mean()); qa=float(a[cap].mean())
            constrained='mpc' in path.stem
            residual=T.T@r[cap]
            omitted=residual-T.T@mr@g*qa
            max_res=max(max_res,float(np.max(np.abs(residual))))
            max_omitted_res=max(max_omitted_res,float(np.max(np.abs(omitted))))
            max_rf_error=max(max_rf_error,float(np.max(np.abs(rf-k@u))))
            max_warp=max(max_warp,float(np.max(np.abs(u[cap]-q))))
            Q=float(4*r[cap[0]] if constrained else sum(r[cap]))
            work+=(old_qforce+Q)*(q-old_q)/2
            se=float(u@k@u/2); ke=float(v@m@v/2)
            final={'time_s':t,'q_mm':q,'cap_u_mm':u[cap].tolist(),
                   'strain_energy_Nmm':se,'kinetic_energy_Nmm':ke,
                   'conjugate_force_from_full_residual_N':Q,
                   'actuator_trapezoid_work_Nmm':work,
                   'energy_defect_Nmm':work-se-ke,
                   'reduced_equilibrium_residual_N':residual.tolist(),
                   'residual_if_prescribed_inertia_omitted_N':omitted.tolist()}
            old_u,old_v,old_a,old_t=u,v,a,t
            old_q,old_qforce=q,Q
        reports[path.stem]={'states':len(data),'final':final,
                           'max_cap_warp_mm':max_warp,
                           'max_RF_minus_Ku_N':max_rf_error,
                           'max_reduced_equilibrium_residual_N':max_res,
                           'max_residual_if_prescribed_inertia_omitted_N':max_omitted_res,
                           'dat_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        if path.stem=='dynamic_mpc':
            observed=np.array([[row['displacements'][n][0] for n in (2,3,6,7)] for t,row in sorted(data.items())])
            for flag in (True,False):
                predicted=predict(sorted(data),flag)
                reports[path.stem]['independent_Newmark_' + ('full_inertia' if flag else 'omitted_prescribed_inertia')]={
                    'max_displacement_difference_mm':float(np.max(np.abs(predicted-observed))),
                    'predicted_final_cap_mm':predicted[-1].tolist()}
    result={'scope':'linear C3D8 fixture only; no joint acceptance',
            'independent_axial_K':k.tolist(),'independent_consistent_M':m.tolist(),
            'rigid_axial_stiffness_N_per_mm':float(np.ones(4)@kr@np.ones(4)),
            'rigid_axial_mass_tonne':float(np.ones(4)@mr@np.ones(4)),
            'rounding_caveat':'DAT has seven significant digits; second differences amplify rounding',
            'cases':reports}
    (folder/'independent-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    (folder/'independent-auditor.py.snapshot').write_bytes(Path(__file__).read_bytes())
    return reports


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    print(json.dumps(audit(parser.parse_args().folder),indent=2))
