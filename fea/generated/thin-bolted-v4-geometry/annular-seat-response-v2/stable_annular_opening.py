"""Stable opening-cap leaf over immutable rigid_annular_seat v1.

Decimal centered cap-depth moments preserve tiny pressure response. Positive
Gram factors are authoritative; an indefinite rounded dense tangent is unusable.
"""
import argparse
import json
import math
import runpy
import sys
from decimal import Decimal as D
from decimal import localcontext
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
V1_PATH = Path(__file__).parents[1] / "annular-seat-response-v1/rigid_annular_seat.py"
V1_SHA = "5b55dcaaf663dd6954ba2f6a7a61aeb48c0ec4014edcf1d7f814defaacb97428"
V1 = runpy.run_path(str(V1_PATH))
assert V1["steel"].sha(V1_PATH) == V1_SHA


def binary_dense_psd(matrix):
    """Exact signs of every principal minor of the rounded binary-float matrix."""
    m = [[Fraction.from_float(float(v)) for v in row] for row in matrix]
    diagonal = [m[i][i] for i in range(3)]
    pairs = [m[i][i]*m[j][j]-m[i][j]*m[j][i] for i, j in [(0, 1), (0, 2), (1, 2)]]
    determinant = (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
                   -m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
                   +m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
    return all(v >= 0 for v in [*diagonal, *pairs, determinant])


def beta_series(alpha, power, epsilon):
    """Integral u^(power+1/2)*(1-epsilon*u)^alpha, with tail bound."""
    coefficient, total = D(1), D(0)
    target = D(10) ** (-(100-15))
    for n in range(1000):
        total += coefficient/(D(power+n)+D('1.5'))
        following = coefficient*(alpha-D(n))/D(n+1)*(-epsilon)
        tail = abs(following)/(D(power+n)+D('2.5'))/(1-epsilon)
        if n >= 2 and tail <= target*abs(total):
            return total, tail
        coefficient = following
    raise ArithmeticError("checked cap series did not terminate")


def stable_cap(kwargs, precision=100):
    with localcontext() as context:
        context.prec = precision
        dec = lambda value: D.from_float(float(value))
        b, k, delta = [dec(kwargs[key]) for key in ('outer_radius_mm', 'bedding_n_mm3', 'normal_approach_mm')]
        sx, sy = [dec(v) for v in kwargs['closure_slopes']]
        tilt = (sx*sx+sy*sy).sqrt()
        h = b+delta/tilt
        assert h > 0 and h <= b*D('1e-4')
        if b-h < dec(kwargs['inner_radius_mm']):
            raise ArithmeticError('opening seam crosses inner rim; thin-annulus representation is not qualified')
        epsilon = h/(2*b)
        base = 2*(2*b).sqrt()*h*h.sqrt()
        moments, bounds = [], []
        for power in range(3):
            integral, tail = beta_series(D('.5'), power, epsilon)
            moments.append(base*h**power*integral)
            bounds.append(base*h**power*tail)
        transverse, tail = beta_series(D('1.5'), 1, epsilon)
        jy = D(2)/3*(2*b)*(2*b).sqrt()*h*h*h.sqrt()*transverse
        bounds.append(D(2)/3*(2*b)*(2*b).sqrt()*h*h*h.sqrt()*tail)
        area, depth, depth2 = moments
        variance = depth2-depth*depth/area
        assert area > 0 and variance > 0 and jy > 0
        normal = k*tilt*(h*area-depth)
        parallel = k*tilt*(b*(h*area-depth)-(h*depth-depth2))
        energy = k*tilt*tilt*(h*h*area-2*h*depth+depth2)/2
        assert normal > 0 and energy > 0 and parallel > 0
        ex, ey = sx/tilt, sy/tilt
        mean_x = b-depth/area
        vectors = [[D(1), mean_x*ex, mean_x*ey], [D(0), -ex, -ey], [D(0), -ey, ex]]
        weights = [k*area, k*variance, k*jy]
        H = [[sum(weights[n]*vectors[n][i]*vectors[n][j] for n in range(3))
              for j in range(3)] for i in range(3)]
        gradient = [normal, parallel*ex, parallel*ey]
        return {'h':h, 'energy':energy, 'gradient':gradient, 'H':H, 'area':area,
                'centered_moments':[area, depth, depth2, jy], 'series_tail_bounds':bounds,
                'gram_weights':weights, 'gram_vectors':vectors, 'pressure_max':k*tilt*h}


def response(**kwargs):
    """Reuse v1 outside numerical seam; inside expose certified response/factors."""
    result = V1['response'](**kwargs)
    with localcontext() as context:
        context.prec = 100
        sx, sy = [D.from_float(float(v)) for v in kwargs['closure_slopes']]
        tilt = (sx*sx+sy*sy).sqrt()
        b = D.from_float(float(kwargs['outer_radius_mm']))
        h = b+D.from_float(float(kwargs['normal_approach_mm']))/tilt if tilt else D(-1)
    if tilt == 0 or h <= 0 or h > b*D('1e-4'):
        result['numerical_method'] = 'immutable-v1-outside-positive-opening-cap-seam'
        result['rounded_dense_tangent_usable'] = True
        return result
    fine = stable_cap(kwargs)
    check = stable_cap(kwargs, 140)
    compared = [fine['energy'], *fine['gradient'], *fine['centered_moments']]
    compared_check = [check['energy'], *check['gradient'], *check['centered_moments']]
    assert all(abs(a-b) <= abs(b)*D('1e-80') for a, b in zip(compared, compared_check, strict=True))
    dense = [[float(v) for v in row] for row in fine['H']]
    usable = binary_dense_psd(dense)
    R = [float(v) for v in fine['gradient']]
    force, moment = [0., 0., R[0]], [R[2], -R[1], 0.]
    closure_map = np.array([[0.,0.,-1.,0.,0.,0.], [0.,0.,0.,0.,1.,0.], [0.,0.,0.,-1.,0.,0.]])
    result.update(energy_nmm=float(fine['energy']), resisting_gradient_N_Gx_Gy=R,
        tangent_delta_sx_sy=dense if usable else None,
        relative_six_dof_tangent=(closure_map.T @ np.array(dense) @ closure_map).tolist() if usable else None,
        rounded_dense_tangent_diagnostic=dense, rounded_dense_tangent_usable=usable,
        force_on_washer_local_xyz_n=force, moment_on_washer_at_annulus_center_local_xyz_nmm=moment,
        force_on_receiving_body_local_xyz_n=[-v for v in force],
        moment_on_receiving_body_at_annulus_center_local_xyz_nmm=[-v for v in moment],
        active_area_mm2=float(fine['area']), contact_state='partial-contact', pressure_min_mpa=0., pressure_max_mpa=float(fine['pressure_max']),
        numerical_method='decimal-centered-opening-cap-series',
        authoritative_tangent_representation='positive-Gram-factors-and-highprecision-matrix',
        highprecision_tangent_delta_sx_sy=[[str(v) for v in row] for row in fine['H']],
        highprecision_energy_nmm=str(fine['energy']), highprecision_resisting_gradient_N_Gx_Gy=[str(v) for v in fine['gradient']],
        effective_cap_width_from_binary_inputs_mm=str(fine['h']),
        centered_A_depth_depth2_transverse=[str(v) for v in fine['centered_moments']],
        positive_Gram_weights=[str(v) for v in fine['gram_weights']], positive_Gram_vectors=[[str(v) for v in row] for row in fine['gram_vectors']],
        checked_series_tail_bounds=[str(v) for v in fine['series_tail_bounds']],
        rounded_dense_max_abs_coefficient_error=str(max(abs(D.from_float(dense[i][j])-fine['H'][i][j]) for i in range(3) for j in range(3))),
        highprecision_recheck_digits=140, dense_PSD_check='exact-binary-float-principal-minors', no_diagonal_shift_or_force_clamp=True)
    return result


def direct_pressure_oracle(kwargs):
    """Independent Decimal120 Gauss-Legendre32 in z=h*v^2, not beta series."""
    with localcontext() as context:
        context.prec = 120
        dec = lambda value: D.from_float(float(value))
        b, k, delta = [dec(kwargs[key]) for key in ('outer_radius_mm','bedding_n_mm3','normal_approach_mm')]
        sx, sy = [dec(v) for v in kwargs['closure_slopes']]
        tilt = (sx*sx+sy*sy).sqrt(); h=b+delta/tilt
        n=32; nodes=[]
        for i in range(1,n+1):
            x=dec(math.cos(math.pi*(i-.25)/(n+.5)))
            for _ in range(24):
                previous, current=D(1), x
                for j in range(2,n+1):
                    previous,current=current,((2*j-1)*x*current-(j-1)*previous)/j
                derivative=n*(x*current-previous)/(x*x-1)
                step=current/derivative; x-=step
                if abs(step)<D('1e-110'): break
            else: raise ArithmeticError('independent quadrature root did not converge')
            nodes.append(((x+1)/2,1/((1-x*x)*derivative*derivative)))
        E,N,G,A,Q,JX,JY=[D(0)]*7
        for v,weight in nodes:
            z=h*v*v; x=b-z; y=(2*b*z-z*z).sqrt(); dx=2*h*v
            strip=2*y*dx; pressure=k*tilt*(h-z)
            E+=weight*pressure*(tilt*(h-z))*strip/2
            N+=weight*pressure*strip; G+=weight*pressure*x*strip
            A+=weight*strip; Q+=weight*x*strip; JX+=weight*x*x*strip
            JY+=weight*D(2)/3*y*y*y*dx
        return {'E':E,'N':N,'G':G,'A':A,'Q':Q,'JX':JX,'JY':JY}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    given=json.loads(args.input.read_bytes());base_path=ROOT/given['base_input_path']
    assert V1['steel'].sha(base_path)==given['base_input_sha256'] and given['v1_source_sha256']==V1_SHA
    base=json.loads(base_path.read_bytes())
    v1_result_path=V1_PATH.with_name('result.json')
    assert V1['steel'].sha(v1_result_path)=='04e7939dc3bde3bef9878cf5a6cc8f8fe8a1e1bacb79368a98db7598136631f5'
    pins=json.loads(v1_result_path.read_bytes())['source_sha256'].copy()
    pins.update({str(p.resolve().relative_to(ROOT)):V1['steel'].sha(p) for p in [Path(__file__),args.input.resolve(),V1_PATH,base_path,v1_result_path]})
    a,b,k=[base[name] for name in ('inner_radius_mm','outer_radius_mm','bedding_n_mm3')]
    def arguments(q):return {'inner_radius_mm':a,'outer_radius_mm':b,'bedding_n_mm3':k,'normal_approach_mm':float(q[0]),'closure_slopes':q[1:]}
    rows=[]
    for slope in given['closure_slope_scenarios']:
        tilt=float(np.linalg.norm(slope))
        for text in given['requested_cap_widths_mm']:
            delta=tilt*(-b+float(text));kw=arguments([delta,*slope]);out=response(**kw);fine=stable_cap(kw);oracle=direct_pressure_oracle(kw)
            np.testing.assert_allclose(out['moment_on_washer_at_annulus_center_local_xyz_nmm'],[float(fine['gradient'][2]),-float(fine['gradient'][1]),0.],atol=0,rtol=0)
            for actual,expected in [(fine['energy'],oracle['E']),(fine['gradient'][0],oracle['N']),
                ((fine['gradient'][1]**2+fine['gradient'][2]**2).sqrt(),oracle['G']), (fine['area'],oracle['A'])]:
                assert abs(actual-expected)<=abs(expected)*D('1e-26')
            assert all(v>0 for v in fine['gram_weights']) and out['energy_nmm']>0 and out['resisting_gradient_N_Gx_Gy'][0]>0
            assert out['rounded_dense_tangent_usable']==binary_dense_psd(out['rounded_dense_tangent_diagnostic'])
            if not out['rounded_dense_tangent_usable']:assert out['tangent_delta_sx_sy'] is None and out['relative_six_dof_tangent'] is None
            derivative_errors=[]
            for component in range(3):
                q=[delta,*slope]
                step=float(fine['h'])*tilt*1e-3/(1 if component==0 else b)
                if q[component]:
                    # A slope at a binary binade boundary has asymmetric ULPs.
                    # Quantize the fixture step to the larger ULP, so its midpoint
                    # stays at the state whose derivative is being checked.
                    quantum=math.ulp(q[component])
                    step=max(1,round(step/quantum))*quantum
                plus,minus=q.copy(),q.copy();plus[component]+=step;minus[component]-=step
                pp,pm=stable_cap(arguments(plus)),stable_cap(arguments(minus))
                with localcontext() as context:
                    context.prec=100
                    actual_span=D.from_float(plus[component])-D.from_float(minus[component])
                    assert actual_span>0
                    assert (D.from_float(plus[component])+D.from_float(minus[component]))/2==D.from_float(q[component])
                    values=[(pp['energy']-pm['energy'])/actual_span]
                    targets=[fine['gradient'][component]]
                    values.extend((pp['gradient'][i]-pm['gradient'][i])/actual_span for i in range(3))
                    targets.extend(fine['H'][i][component] for i in range(3))
                    errors=[abs(value-target)/abs(target) if target else abs(value-target) for value,target in zip(values,targets,strict=True)]
                    assert all(error<=D('5e-6') for error in errors)
                    derivative_errors.extend(str(error) for error in errors)
            old=V1['response'](**kw)
            rows.append({'requested_cap_width_mm':text,'q':[delta,*slope],'stable_response':out,
                         'independent_direct_pressure_E_N_G':[str(oracle[v]) for v in ('E','N','G')],
                         'finite_difference_energy_gradient_and_tangent_relative_errors':derivative_errors,
                         'old_v1_E_N':[old['energy_nmm'],old['resisting_gradient_N_Gx_Gy'][0]]})
    reused=[]
    for row in base['states']:
        kw=arguments(row['q']);old=V1['response'](**kw);out=response(**kw)
        exact=all(old[key]==out[key] for key in old)
        if row['id']!='point-grazing':assert exact
        reused.append({'id':row['id'],'v1_fields_byte_values_reused':exact,'new_method':out['numerical_method'],
                       'new_energy_nmm':out['energy_nmm'],'new_normal_n':out['resisting_gradient_N_Gx_Gy'][0]})
    opened=response(**arguments([-b,1.,0.]));assert opened['energy_nmm']==0 and opened['resisting_gradient_N_Gx_Gy']==[0.,0.,0.]
    uniform=response(**arguments([1e-10,0.,0.]));assert uniform['tangent_delta_sx_sy'][0][0]>0
    assert abs(uniform['resisting_gradient_N_Gx_Gy'][0]/1e-10-uniform['tangent_delta_sx_sy'][0][0])<1e-10
    report={'schema':'thin_bolted_annular_opening_seam_coupon/v2','command':[sys.executable,str(Path(__file__).resolve()),'--input',str(args.input),'--output',str(args.output)],
        'source_sha256':pins,'inputs':given,'cases':rows,'immutable_v1_state_replay':reused,
        'exact_open_and_whole_annulus_unit_derivative_pass':True,
        'algorithm_switch':'h/b<=1e-4 selects higher precision only; original pressure law unchanged, no physical activation threshold',
        'floating_grazing_qualification':'The old point-grazing q contains multiplication rounding; Decimal gives tiny positive cap rather than artificial zero. Its immutable v1 numeric-touch result is retained.',
        'tangent_consumption':'Positive Gram factors/highprecision matrix are authoritative inside seam. None marks an indefinite rounded dense tangent unusable; no diagonal shift or altered force is used.',
        'limitations':['Opening seam only; numerically thin annulus crossing inner rim explicitly rejects rather than reuse unqualified cancellation.',
            'Any application needs a source-bound factor/highprecision operator path; positive precise tangent does not make every rounded dense representation accurate.',
            'Declared rigid annular bedding scenario only, no washer bending/wood strength/current contact area/product capacity.'],
        'physical_law_or_stiffness_changed':False,'candidate_global_native_CAD_solved':False,'capacity_established':False,'released':False}
    assert all(V1['steel'].sha(ROOT/path)==digest for path,digest in pins.items())
    with args.output.open('x') as f:json.dump(report,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'source_sha256':V1['steel'].sha(Path(__file__)),'input_sha256':V1['steel'].sha(args.input),'result_sha256':V1['steel'].sha(args.output),'positive_cap_cases':len(rows),'dense_unusable_cases':sum(not r['stable_response']['rounded_dense_tangent_usable'] for r in rows)}))


if __name__=='__main__':main()
