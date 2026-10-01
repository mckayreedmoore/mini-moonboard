"""Independent physical-point body wrenches for the reported closed probes."""
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
d=json.loads((HERE/"conditional-corner-energy.json").read_text())
operator=json.loads((HERE.parent/"current-corner-equilibrium-operator-attempt01/operator.json").read_text())
bodies=operator["bodies"];records=operator["carrier_records"]
largest=0.;count=0
for case in d["cases"]:
    if case["status"]!="CONDITIONAL_CLOSED":
        assert "carrier_actions_N" not in case
        continue
    count+=1
    A=np.array(operator["operator_rows"])[d["free_coordinate_indices"]].T
    k=np.array(d["stiffness_N_per_mm"])
    uni=np.array([role!="bolt_lateral" for role in d["carrier_roles"]])
    for force_key,coordinate_key in (("carrier_actions_N","free_displacement_coordinates_mm"),
                                     ("second_start_carrier_actions_N","second_start_displacement_coordinates_mm")):
        gap=A@case[coordinate_key]
        predicted=-k*np.where(uni,np.minimum(gap,0.),gap)
        assert max(abs(predicted-case[force_key]))<1e-5
    assert max(abs(np.array(case["carrier_actions_N"])-case["second_start_carrier_actions_N"]))<1e-5
    forces={body:np.zeros(3) for body in bodies}
    moments={body:np.zeros(3) for body in bodies}
    for r,action in zip(records,case["carrier_actions_N"],strict=True):
        if r["role"]!="bolt_lateral":assert action>=-1e-10
        for body,point,sign in ((r["first"],r["first_point_mm"],1.),(r["second"],r["second_point_mm"],-1.)):
            f=sign*action*np.array(r["direction_on_first"])
            forces[body]+=f
            moments[body]+=np.cross(np.array(point)-operator["datums_mm"][body],f)
    w=np.array(case["all_member_external_wrench_rows_scaled"]).reshape(5,6)
    for i,body in enumerate(bodies):
        error=max(max(abs(forces[body]+w[i,:3])),max(abs(moments[body]+100.*w[i,3:])))
        largest=max(largest,float(error));assert error<1e-6
assert count==48
print("48 independent per-member force/moment closures; maximum physical residual",largest)

# A separate analytic displacement witness for the negative-X spine unit probe.
# Move all four non-post bodies equally in X. Only the two post ties stretch.
B=np.array(operator["operator_rows"]);free=d["free_coordinate_indices"]
k=np.array(d["stiffness_N_per_mm"]);roles=d["carrier_roles"]
uni=np.array([role!="bolt_lateral" for role in roles])
post_ties=[i for i,r in enumerate(records) if r["role"]=="bolt_axial" and "post_" in r["name"]]
assert len(post_ties)==2 and abs(k[post_ties[0]]-k[post_ties[1]])<1e-9
u=np.zeros(30)
for i,body in enumerate(bodies):
    if body!="base_post_outer_left":u[i*6]=-.5/k[post_ties[0]]
gap=B.T@u;expected=-k*np.where(uni,np.minimum(gap,0.),gap)
case=next(c for c in d["cases"] if c["loaded_member"]=="knee_outer_left_spine" and c["component"]==0 and c["sign"]==-1.)
assert np.allclose(case["carrier_actions_N"],expected,atol=1e-8,rtol=0.)
residual=(B@expected+case["all_member_external_wrench_rows_scaled"])*np.tile([1.,1.,1.,100.,100.,100.],5)
assert max(abs(residual))<1e-6
print("Analytic equal-X translation witness agrees; no displacement-uniqueness claim")
