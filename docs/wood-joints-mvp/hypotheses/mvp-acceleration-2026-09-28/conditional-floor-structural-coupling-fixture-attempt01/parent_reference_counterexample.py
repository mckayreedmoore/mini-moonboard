"""Exact-rational counterexample to general fixed-reference static solvability."""
from fractions import Fraction as F
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
fixture=json.loads((HERE/"fixture.json").read_text())
K=fixture["model"]["carrier_stiffness_n_per_mm"]
assert [row[:2] for row in K[:2]]==[[20.,5.],[5.,100.]]
assert fixture["model"]["normal_penalty_stiffness_n_per_mm"]==100.
a,b,c,kn=map(F,[20,5,100,100]);Hx,Pz=map(F,[4,F(1,2)])
det=a*c-b*b
open_x=(c*Hx-b*Pz)/det;open_z=(a*Pz-b*Hx)/det
ref=F(0);bear_z=(Pz-b*ref)/(c+kn);bear_N=-kn*bear_z;bear_T=a*ref+b*bear_z-Hx
assert open_z<0 and bear_z>0 and bear_N<0
assert Hx-a*open_x-b*open_z==0 and Pz-b*open_x-c*open_z==0
assert Hx-a*ref-b*bear_z+bear_T==0 and Pz-b*ref-c*bear_z+bear_N==0
out={"fixture_sha256":hashlib.sha256((HERE/"fixture.json").read_bytes()).hexdigest(),
     "scope":"One-cell fixture subset; fixed preceding-open episode reference zero, not a current-frame case",
     "stiffness_N_per_mm":[[20,5],[5,100]],"normal_penalty_N_per_mm":100,
     "external_tangent_normal_N":[4,.5],"episode_reference_mm":0,
     "open_branch":{"q_mm":[float(open_x),float(open_z)],"z_exact":str(open_z),"admissible":False,"reason":"Negative gap with no normal reaction"},
     "bearing_branch":{"q_mm":[0,float(bear_z)],"contact_T_N":[float(bear_T),float(bear_N)],"N_exact":str(bear_N),"admissible":False,"reason":"Positive gap and negative candidate normal force"},
     "admissible_branch_count":0,
     "mirrored_load_example":{"external_tangent_normal_N":[-4,-.5],
          "open_branch":{"q_mm":[float(-open_x),float(-open_z)],"contact_T_N":[0,0],"admissible":True},
          "bearing_branch":{"q_mm":[0,float(-bear_z)],"contact_T_N":[float(-bear_T),float(-bear_N)],"admissible":True},
          "admissible_branch_count":2,"disposition":"Branch selection needs defined history; SPD carrier alone does not establish uniqueness"},
     "physical_frame_failure":False,"qualified_for_design":False,"native_solve_executed":False}
(HERE/"parent-reference-counterexample.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
assert -open_z>0 and -bear_z<0 and -bear_N>0
print("Exact two-branch counterexample: no admissible fixed-reference static state; mirrored load has 2 valid branches; no current-frame failure claim")
