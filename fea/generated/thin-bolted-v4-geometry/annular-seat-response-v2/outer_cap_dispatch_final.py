"""Corrected outer-only cap dispatch over preserved annular v1/first-v2 leaves.

Reuse the checked cap series and independent pressure oracle. The switch is
the inner rim, where v1 is well conditioned, rather than a small numeric width.
"""
import argparse
import json
import math
import runpy
import sys
from decimal import Decimal as D
from decimal import localcontext
from itertools import pairwise
from pathlib import Path

import numpy as np

FIRST_PATH = Path(__file__).with_name('stable_annular_opening.py')
FIRST_SHA = '198f4d2ea05575dab99b33808b7e6bae7c8768bf5fe7ddef35043958c5feabe2'
FIRST = runpy.run_path(str(FIRST_PATH))
V1, ROOT = FIRST['V1'], FIRST['ROOT']
assert V1['steel'].sha(FIRST_PATH) == FIRST_SHA


def cap_kinematics(kwargs):
    with localcontext() as context:
        context.prec = 140
        a, b, delta = [D.from_float(float(kwargs[key])) for key in
                       ('inner_radius_mm', 'outer_radius_mm', 'normal_approach_mm')]
        sx, sy = [D.from_float(float(v)) for v in kwargs['closure_slopes']]
        tilt = (sx*sx+sy*sy).sqrt()
        return a, b, tilt, b+delta/tilt if tilt else D(-1)


def outer_cap(kwargs, precision=100):
    """Minimal centered primitive override; reuse first-v2 beta integrals."""
    with localcontext() as context:
        context.prec = precision
        a, b, tilt, h = cap_kinematics(kwargs)
        assert tilt > 0 and 0 < h <= b-a
        k = D.from_float(float(kwargs['bedding_n_mm3']))
        sx, sy = [D.from_float(float(v)) for v in kwargs['closure_slopes']]
        # Dimensionless moments avoid any subtraction of large cap primitives.
        integrals = [FIRST['beta_series'](D('.5'), j, h/(2*b)) for j in range(3)]
        base = 2*(2*b).sqrt()*h*h.sqrt()
        A, Z, Z2 = [base*h**j*integrals[j][0] for j in range(3)]
        transverse, transverse_tail = FIRST['beta_series'](D('1.5'), 1, h/(2*b))
        transverse_scale = D(2)/3*(2*b)*(2*b).sqrt()*h*h*h.sqrt()
        Jperp = transverse_scale*transverse
        variance = Z2-Z*Z/A
        ex, ey, mean = sx/tilt, sy/tilt, b-Z/A
        factors = [[D(1), mean*ex, mean*ey], [D(0), -ex, -ey], [D(0), -ey, ex]]
        weights = [k*A, k*variance, k*Jperp]
        assert all(v > 0 for v in weights)
        H = [[D(0)]*3 for _ in range(3)]
        for i in range(3):
            for j in range(i, 3):
                H[i][j] = H[j][i] = sum(w*v[i]*v[j] for w, v in zip(weights, factors, strict=True))
        N = k*tilt*(h*A-Z)
        G = k*tilt*(b*(h*A-Z)-(h*Z-Z2))
        E = k*tilt*tilt*(h*h*A-2*h*Z+Z2)/2
        assert N > 0 and G > 0 and E > 0
        return {'h':h, 'energy':E, 'gradient':[N, G*ex, G*ey], 'H':H,
                'area':A, 'centered_moments':[A, Z, Z2, Jperp],
                'gram_weights':weights, 'gram_vectors':factors, 'pressure_max':k*tilt*h,
                'series_tail_bounds':[base*h**j*integrals[j][1] for j in range(3)]+[transverse_scale*transverse_tail]}


def response(**kwargs):
    # Immutable v1 supplies validation, physical datum and reused moderate fields.
    result = V1['response'](**kwargs)
    a, b, tilt, h = cap_kinematics(kwargs)
    if tilt == 0 or h <= 0 or h > b-a:
        result['numerical_method'] = 'immutable-v1-beyond-outer-only-cap'
        result['rounded_dense_tangent_usable'] = FIRST['binary_dense_psd'](result['tangent_delta_sx_sy'])
        if not result['rounded_dense_tangent_usable']:
            raise ArithmeticError('v1 rounded tangent is not PSD; representation rejected')
        return result
    fine, check = outer_cap(kwargs), outer_cap(kwargs, 140)
    compared = [fine['energy'], *fine['gradient'], *fine['centered_moments'], *[value for row in fine['H'] for value in row]]
    checked = [check['energy'], *check['gradient'], *check['centered_moments'], *[value for row in check['H'] for value in row]]
    assert all(abs(x-y) <= abs(y)*D('1e-80') for x, y in zip(compared, checked, strict=True))
    dense = [[float(v) for v in row] for row in fine['H']]
    usable = FIRST['binary_dense_psd'](dense)
    R = [float(v) for v in fine['gradient']]
    force, moment = [0., 0., R[0]], [R[2], -R[1], 0.]
    closure = np.array([[0.,0.,-1.,0.,0.,0.], [0.,0.,0.,0.,1.,0.], [0.,0.,0.,-1.,0.,0.]])
    result.update(energy_nmm=float(fine['energy']), resisting_gradient_N_Gx_Gy=R,
        tangent_delta_sx_sy=dense if usable else None,
        relative_six_dof_tangent=(closure.T @ np.array(dense) @ closure).tolist() if usable else None,
        rounded_dense_tangent_diagnostic=dense, rounded_dense_tangent_usable=usable,
        force_on_washer_local_xyz_n=force, moment_on_washer_at_annulus_center_local_xyz_nmm=moment,
        force_on_receiving_body_local_xyz_n=[-v for v in force],
        moment_on_receiving_body_at_annulus_center_local_xyz_nmm=[-v for v in moment],
        active_area_mm2=float(fine['area']), contact_state='partial-contact',
        pressure_min_mpa=0., pressure_max_mpa=float(fine['pressure_max']),
        numerical_method='decimal-centered-all-outer-only-caps',
        authoritative_tangent_representation='positive-Gram-factors-and-highprecision-matrix',
        highprecision_tangent_delta_sx_sy=[[str(v) for v in row] for row in fine['H']],
        highprecision_energy_nmm=str(fine['energy']),
        highprecision_resisting_gradient_N_Gx_Gy=[str(v) for v in fine['gradient']],
        effective_cap_width_from_binary_inputs_mm=str(h),
        centered_A_depth_depth2_transverse=[str(v) for v in fine['centered_moments']],
        positive_Gram_weights=[str(v) for v in fine['gram_weights']],
        positive_Gram_vectors=[[str(v) for v in row] for row in fine['gram_vectors']],
        checked_series_tail_bounds=[str(v) for v in fine['series_tail_bounds']],
        rounded_dense_max_abs_coefficient_error=str(max(abs(D.from_float(dense[i][j])-fine['H'][i][j]) for i in range(3) for j in range(3))),
        highprecision_recheck_digits=140, dense_PSD_check='exact-binary-float-principal-minors',
        no_diagonal_shift_or_force_clamp=True)
    return result


def annular_pressure_oracle(kwargs):
    """Distinct direct positive-pressure strips, including the inner disk cutout."""
    a, b, k = [kwargs[key] for key in ('inner_radius_mm', 'outer_radius_mm', 'bedding_n_mm3')]
    tilt = math.hypot(*kwargs['closure_slopes']); cutoff=-kwargs['normal_approach_mm']/tilt
    def integrand(x):
        outer=math.sqrt(max(0.,b*b-x*x));inner=math.sqrt(max(0.,a*a-x*x))
        strip=2*(outer-inner);pressure=k*tilt*(x-cutoff)
        return [pressure*tilt*(x-cutoff)*strip/2,pressure*strip,pressure*x*strip,
                k*strip,k*x*strip,k*x*x*strip,k*2*(outer**3-inner**3)/3]
    ends=sorted(set([cutoff,b]+[v for v in [-a,a] if cutoff<v<b]))
    values,errors=[],[]
    for i in range(7):
        pairs=[V1['quad'](lambda x, j=i:integrand(x)[j],lo,hi,epsabs=1e-8,epsrel=2e-13)
               for lo,hi in pairwise(ends)]
        values.append(sum(v for v,e in pairs));errors.append(sum(e for v,e in pairs))
    return {'E_N_G_A_Q_Jparallel_Jperp':values, 'quadrature_abs_error_estimates':errors}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    given=json.loads(args.input.read_bytes())
    first_result_path=FIRST_PATH.with_name('result.json')
    assert V1['steel'].sha(first_result_path)==given['preserved_first_result_sha256']
    prior=json.loads(first_result_path.read_bytes())
    pins=prior['source_sha256'].copy()
    pins.update({str(p.resolve().relative_to(ROOT)):V1['steel'].sha(p) for p in [Path(__file__),args.input.resolve(),first_result_path]})
    a,b,k=7.14375,17.526,1.
    def arguments(q):return {'inner_radius_mm':a,'outer_radius_mm':b,'bedding_n_mm3':k,'normal_approach_mm':q[0],'closure_slopes':q[1:]}
    caps=[]
    for row in prior['cases']:
        kw=arguments(row['q']);out=response(**kw);fine=outer_cap(kw);oracle=FIRST['direct_pressure_oracle'](kw)
        for key in ['energy_nmm','resisting_gradient_N_Gx_Gy','active_area_mm2','rounded_dense_tangent_usable']:
            assert out[key]==row['stable_response'][key]
        with localcontext() as context:
            context.prec=120
            sx,sy=map(D.from_float,row['q'][1:]);tilt=(sx*sx+sy*sy).sqrt();ex,ey=sx/tilt,sy/tilt
            H=[[oracle['A'],oracle['Q']*ex,oracle['Q']*ey],
               [oracle['Q']*ex,oracle['JX']*ex*ex+oracle['JY']*ey*ey,(oracle['JX']-oracle['JY'])*ex*ey],
               [oracle['Q']*ey,(oracle['JX']-oracle['JY'])*ex*ey,oracle['JX']*ey*ey+oracle['JY']*ex*ex]]
            errors=[abs(fine['H'][i][j]-H[i][j])/abs(H[i][j]) if H[i][j] else abs(fine['H'][i][j]) for i in range(3) for j in range(3)]
            assert max(errors)<D('1e-80')
        reverse=response(**arguments([row['q'][0],-row['q'][1],-row['q'][2]]))
        assert reverse['resisting_gradient_N_Gx_Gy']==[out['resisting_gradient_N_Gx_Gy'][0],-out['resisting_gradient_N_Gx_Gy'][1],-out['resisting_gradient_N_Gx_Gy'][2]]
        assert reverse['energy_nmm']==out['energy_nmm']
        response(**arguments([-.1,0.,0.]))
        assert response(**kw)==out
        caps.append({'q':row['q'],'stable_response':out,'direct_pressure_tangent_relative_errors':[str(v) for v in errors],
                     'first_v2_positive_response_reused':True,'reverse_and_stateless_replay_pass':True})
    seam=[]
    for offset in given['inner_rim_normal_offsets_mm']:
        q=[-a+offset,1.,0.];out=response(**arguments(q));oracle=annular_pressure_oracle(arguments(q))
        E,N,G,A,Q,JX,JY=oracle['E_N_G_A_Q_Jparallel_Jperp']
        np.testing.assert_allclose([out['energy_nmm'],*out['resisting_gradient_N_Gx_Gy']],[E,N,G,0.],rtol=2e-12,atol=1e-8)
        np.testing.assert_allclose(out['tangent_delta_sx_sy'],[[A,Q,0.],[Q,JX,0.],[0.,0.,JY]],rtol=2e-12,atol=1e-8)
        seam.append({'q':q,'response':out,'independent_annular_pressure_oracle':oracle})
    # At the geometric switch, v1 and the new primitive describe the same area.
    boundary=arguments([-a,1.,0.]);new=response(**boundary);old=V1['response'](**boundary)
    for key in ['energy_nmm','resisting_gradient_N_Gx_Gy','tangent_delta_sx_sy']:
        np.testing.assert_allclose(new[key],old[key],rtol=2e-14,atol=1e-10)
    derivative=[]
    for q in [[-a,1.,0.],[-b+b*1e-4,1.,0.]]:
        out=response(**arguments(q));H=np.array(out['tangent_delta_sx_sy']);R=np.array(out['resisting_gradient_N_Gx_Gy'])
        steps=[1e-5,1e-7,1e-7] if q[0]==-a else [1e-6,1e-8,1e-8]
        finite_H=np.zeros((3,3));finite_R=np.zeros(3)
        for i,step in enumerate(steps):
            plus,minus=q.copy(),q.copy();plus[i]+=step;minus[i]-=step
            pp,pm=response(**arguments(plus)),response(**arguments(minus))
            span=plus[i]-minus[i]
            finite_H[:,i]=(np.array(pp['resisting_gradient_N_Gx_Gy'])-np.array(pm['resisting_gradient_N_Gx_Gy']))/span
            finite_R[i]=(pp['energy_nmm']-pm['energy_nmm'])/span
        np.testing.assert_allclose(finite_H,H,rtol=2e-7,atol=1e-5)
        np.testing.assert_allclose(finite_R,R,rtol=2e-7,atol=1e-6)
        derivative.append({'q':q,'finite_difference_tangent_max_abs_error':float(abs(finite_H-H).max()),
                           'finite_difference_energy_gradient_max_abs_error':float(abs(finite_R-R).max())})
    # Concrete continuity: both sides approach the common boundary with bounded
    # changes from the integrated Hessian. No force/energy is artificially fixed.
    boundary_R=np.array(new['resisting_gradient_N_Gx_Gy']);boundary_H=np.array(new['tangent_delta_sx_sy'])
    for row in [seam[0],seam[-1]]:
        dq=abs(row['q'][0]+a);difference=abs(np.array(row['response']['resisting_gradient_N_Gx_Gy'])-boundary_R)
        assert np.all(difference<=1.001*abs(boundary_H[:,0])*dq+1e-9)
    base=json.loads((ROOT/prior['inputs']['base_input_path']).read_bytes());replay=[]
    for row in base['states']:
        old=V1['response'](**arguments(row['q']));out=response(**arguments(row['q']))
        same=all(out[key]==old[key] for key in old)
        if row['id']!='point-grazing':assert same
        replay.append({'id':row['id'],'immutable_v1_fields_identical':same,'response':out})
    exact_open=response(**arguments([-b,1.,0.]));assert exact_open['resisting_gradient_N_Gx_Gy']==[0.,0.,0.]
    unit=response(**arguments([1e-10,0.,0.]));assert unit['tangent_delta_sx_sy'][0][0]>0
    assert abs(unit['resisting_gradient_N_Gx_Gy'][0]/1e-10-unit['tangent_delta_sx_sy'][0][0])<1e-10
    report={'schema':'thin_bolted_annular_outer_cap_dispatch_coupon/v2',
        'command':[sys.executable,str(Path(__file__).resolve()),'--input',str(args.input),'--output',str(args.output)],
        'source_sha256':pins,'inputs':given,'positive_tiny_caps':caps,'inner_rim_dispatch_checks':seam,
        'boundary_and_old_numeric_switch_derivatives':derivative,'immutable_v1_moderate_replay':replay,
        'exact_open_and_whole_annulus_unit_derivative_pass':True,
        'dispatch':'0<h<=b-a: checked centered outer-only cap series; beyond inner rim: preserved v1. This is a geometric integration switch, not a changed activation law.',
        'dense_representation':'Exact-binary principal-minor PSD test; None rejects indefinite rounded dense tangents. Positive highprecision Gram factors remain authoritative. No shift/clamp.',
        'old_failed_seam_retained':True,'pressure_law_unchanged':True,
        'limits':['Declared rigid uniform-bedding frictionless annular response only; k remains unmeasured scenario input.',
                 'A factor/highprecision consumer is required when dense float tangent is None; no solver is integrated here.',
                 'Nominal grazing binary-rounding distinction and whole-touch generalized derivative conventions stay explicit.',
                 'No washer bending, wood strength, delivered pressure area, global candidate equilibrium or capacity established.'],
        'candidate_global_native_CAD_solved':False,'released':False}
    assert all(V1['steel'].sha(ROOT/path)==digest for path,digest in pins.items())
    with args.output.open('x') as handle:json.dump(report,handle,sort_keys=True,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps({'source_sha256':V1['steel'].sha(Path(__file__)),'input_sha256':V1['steel'].sha(args.input),
                      'result_sha256':V1['steel'].sha(args.output),'source_pins':len(pins),'tiny_caps':len(caps),
                      'inner_rim_cases':len(seam),'derivative_states':len(derivative)}))


if __name__=='__main__':main()
