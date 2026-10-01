"""Five-member imposed-action probes, never climber-case/native responses."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import minimize, linprog

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
OPERATOR=BASE/"current-corner-equilibrium-operator-attempt01/operator.json"
MODEL=BASE/"reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json"
PINS={OPERATOR:"f2c9588165b5b56c7eef71d3b2f01c11a600ed64c3853f97dda5aea55debc0f2",
      MODEL:"d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0"}
DATUM=np.array([-1219.2,-137.6,192.475])


def compatible_displacement(A,k,unilateral,f):
    # Recover a witness for the original spring law, without changing QP forces.
    active=(~unilateral)|(f>1e-8)
    inactive=unilateral & ~active
    result=linprog(np.zeros(A.shape[1]),A_ub=-A[inactive],b_ub=np.zeros(sum(inactive)),
                   A_eq=A[active],b_eq=-f[active]/k[active],
                   bounds=[(None,None)]*A.shape[1],method="highs",
                   options={"primal_feasibility_tolerance":1e-10,
                            "dual_feasibility_tolerance":1e-10})
    return result.x if result.success else None


def energy_solution(A,k,unilateral,w,initial):
    C=A.T*np.sqrt(k)
    L=np.linalg.cholesky(C@C.T)
    E=np.linalg.solve(L,C);q=np.linalg.solve(L,-w)
    result=minimize(lambda z: .5*np.dot(z,z),initial,jac=lambda z:z,method="SLSQP",
                    bounds=[(0.,None) if on else (None,None) for on in unilateral],
                    constraints={"type":"eq","fun":lambda z:E@z-q,"jac":lambda z:E},
                    options={"ftol":1e-14,"maxiter":200})
    f=np.sqrt(k)*result.x
    u=-np.linalg.solve(L.T,result.multipliers[:len(w)])
    gap=A@u;predicted=-k*np.where(unilateral,np.minimum(gap,0.),gap)
    recovery="QP equality multipliers"
    if max(abs(f-predicted))>1e-5:
        witness=compatible_displacement(A,k,unilateral,f)
        if witness is not None:
            u=witness
            gap=A@u;predicted=-k*np.where(unilateral,np.minimum(gap,0.),gap)
            recovery="Linear spring-law feasibility witness"
    return u,f,float(max(abs(f-predicted))),result.nit,recovery


def build():
    for path,pin in PINS.items():assert hashlib.sha256(path.read_bytes()).hexdigest()==pin
    d=json.loads(OPERATOR.read_text());m=json.loads(MODEL.read_text())
    B=np.array(d["operator_rows"]);records=d["carrier_records"];bodies=d["bodies"]
    anchor="base_post_outer_left";anchor_index=bodies.index(anchor)*6
    free=[i for i in range(30) if not anchor_index<=i<anchor_index+6]
    A=B[free].T;unilateral=np.array([r["role"]!="bolt_lateral" for r in records])
    stiffness=[]
    for row in records:
        name=row["name"].split("/transverse")[0]
        if row["role"]=="compression_contact":
            stiffness.append(100.*m["connection_ownership"][name]["source_area_mm2"])
        else:
            springs=[r for r in m["springs"] if r["name"]==name]
            assert springs and all(abs(r["stiffness_n_per_mm"]-springs[0]["stiffness_n_per_mm"])<1e-9 for r in springs)
            stiffness.append(springs[0]["stiffness_n_per_mm"])
    k=np.array(stiffness)
    # Independent opposing unilateral springs: hand-derived forces and displacement.
    for load,expected_f,expected_u in [(10.,[0.,10.],10./3.),(-9.,[9.,0.],-4.5)]:
        u,f,error,_,_=energy_solution(np.array([[1.],[-1.]]),np.array([2.,3.]),np.ones(2,dtype=bool),np.array([load]),np.zeros(2))
        assert np.allclose(f,expected_f,atol=1e-8) and abs(u[0]-expected_u)<1e-8 and error<1e-8
    # A free inactive coordinate must open rather than create a fictitious action.
    fixture_A=np.array([[1.,0.],[-1.,0.],[0.,1.]])
    fixture_k=np.array([2.,3.,4.]);fixture_f=np.array([0.,10.,0.])
    witness=compatible_displacement(fixture_A,fixture_k,np.ones(3,dtype=bool),fixture_f)
    assert witness is not None and abs(witness[0]-10./3.)<1e-8 and witness[1]>=-1e-10
    assert np.allclose(-fixture_k*np.minimum(fixture_A@witness,0.),fixture_f,atol=1e-8)
    rng=np.random.default_rng(20260929)
    starts=[np.zeros(len(k)),rng.normal(size=len(k))*1e-4]
    cases=[]
    for body in bodies:
        if body==anchor:continue
        for component in range(6):
            for direction in (-1.,1.):
                force=np.zeros(3);couple=np.zeros(3)
                if component<3:force[component]=direction
                else:couple[component-3]=direction*1000.
                w=np.zeros(30)
                for receiver,s in ((body,1.),(anchor,-1.)):
                    index=bodies.index(receiver)*6
                    moment=np.cross(DATUM-np.array(d["datums_mm"][receiver]),s*force)+s*couple
                    w[index:index+6]=np.r_[s*force,moment/100.]
                solutions=[]
                for initial in starts:
                    u,f,constitutive_error,nfev,recovery=energy_solution(A,k,unilateral,w[free],initial)
                    residual=B@f+w
                    physical=residual*np.tile([1.,1.,1.,100.,100.,100.],5)
                    solutions.append((u,f,float(max(abs(physical))),nfev,constitutive_error,recovery))
                u,f,error,nfev,ce,recovery=solutions[0];u2,f2,error2,nfev2,ce2,recovery2=solutions[1]
                row={"loaded_member":body,"component":component,"sign":direction,
                     "imposed_force_N":force.tolist(),"imposed_couple_Nmm":couple.tolist(),
                     "common_action_datum_mm":DATUM.tolist(),"all_member_external_wrench_rows_scaled":w.tolist(),
                     "max_physical_residual":max(error,error2),"iterations_each_start":[nfev,nfev2],
                     "max_constitutive_force_error_N":max(ce,ce2),"displacement_recovery_each_start":[recovery,recovery2],
                     "max_displacement_witness_difference_mm":float(max(abs(u-u2))),
                     "different_compatible_displacements_detected":bool(max(abs(u-u2))>1e-7)}
                if max(error,error2)>1e-6 or max(ce,ce2)>1e-5:
                    row.update(status="UNRESOLVED",stop="Equilibrium or constitutive guard failed within bounded two-start calculation")
                elif np.max(abs(f-f2))>1e-5:
                    row.update(status="UNRESOLVED",stop="Different compatible carrier forces")
                else:
                    assert min(f[unilateral])>=-1e-10
                    row.update(status="CONDITIONAL_CLOSED",carrier_actions_N=f.tolist(),
                               free_displacement_coordinates_mm=u.tolist(),
                               second_start_displacement_coordinates_mm=u2.tolist(),
                               second_start_carrier_actions_N=f2.tolist(),max_carrier_difference_N=float(max(abs(f-f2))))
                cases.append(row)
    return {"pins":{str(p.relative_to(BASE)):pin for p,pin in PINS.items()},"carrier_names":[r["name"] for r in records],
            "scipy_version":scipy.__version__,"numpy_version":np.__version__,
            "carrier_roles":[r["role"] for r in records],"stiffness_N_per_mm":stiffness,"free_coordinate_indices":free,
            "gauge":"Outer post displacement coordinates zero; balanced imposed post actions remain in all-member closure",
            "scope":"48 balanced imposed action pairs on five rigid local members; fixed coarse contact cells, zero preload/gaps, no frame demands",
            "method":"Minimum complementary energy, 50 carrier variables, equality balance and nonnegative unilateral forces; SLSQP with 200-iteration/two-start bounds and explicit constitutive/root/force-agreement guards; linear feasibility recovery if multipliers fail the unchanged constitutive guard",
            "known_answer":"Opposing unilateral springs k=2/3: external +10 gives forces 0/10 and u=10/3; -9 gives 9/0 and u=-4.5",
            "cases":cases,"qualified_for_design":False,"native_solve_executed":False}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--verify",action="store_true");args=parser.parse_args()
    data=build();out=HERE/"conditional-corner-energy.json"
    if args.verify:
        old=json.loads(out.read_text());assert old["pins"]==data["pins"]
        for a,b in zip(data["cases"],old["cases"],strict=True):
            assert a["status"]==b["status"]
            if a["status"]=="CONDITIONAL_CLOSED":assert np.allclose(a["carrier_actions_N"],b["carrier_actions_N"],rtol=1e-7,atol=1e-6)
    else:out.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    from collections import Counter
    print(dict(Counter(r["status"] for r in data["cases"])))
    for r in data["cases"]:
        if r["status"]=="UNRESOLVED":print(r["loaded_member"],r["component"],r["sign"],r["stop"],r["max_physical_residual"])
