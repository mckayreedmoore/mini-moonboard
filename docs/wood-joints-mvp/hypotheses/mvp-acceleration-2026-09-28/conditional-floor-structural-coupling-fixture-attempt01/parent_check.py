"""Parent independent elimination oracle; no native/frame execution."""
from pathlib import Path
import hashlib,itertools,json
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
FIXTURE_PIN="65f1956c02b16e48ae6fa1fc7f112eb3a7564643dbd4dc74365aea4be4479a24"
MODEL=HERE.parent/"reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json"
assert hashlib.sha256((HERE/"fixture.json").read_bytes()).hexdigest()==FIXTURE_PIN
assert hashlib.sha256(MODEL.read_bytes()).hexdigest()=="d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0"
d=json.loads((HERE/"fixture.json").read_text())
for source in d["source_pins"].values():
    assert hashlib.sha256((ROOT/source["path"]).read_bytes()).hexdigest()==source["sha256"]
K=np.array(d["model"]["carrier_stiffness_n_per_mm"])
assert np.allclose(K,K.T,atol=0.,rtol=0.)
assert all(K[i,i]>sum(abs(K[i,j]) for j in range(4) if j!=i) for i in range(4))
# Independent literal targets, frozen by parent scalar arithmetic.
Qs=[[0,-.05,0,-.15],[0,-.05,.25,.02],[.1,.03,.35,.02],[.1,-.02,.35,-.04]]
Cs=[[-5,5,-3,15],[-2,5,0,0],[0,0,0,0],[-2,2,2,4]]
Ws=[[4.75,-8.5,3.6,-32.5],[1,-10.2,7.42,1.9],[1.1,3.3,10.12,.7],[2.85,-3.1,8.36,-10]]
previous_q=np.zeros(4);previous_active=(False,False);references=[None,None]
results=[]
for stage,Q,C,W in zip(d["stages"],Qs,Cs,Ws,strict=True):
    assert np.allclose(stage["hand_answer"]["external_W_n"],W,atol=1e-12,rtol=0.)
    assert np.allclose(K@Q-C,W,atol=1e-12,rtol=0.)
    candidates=[]
    for mask in itertools.product([False,True],repeat=2):
        fixed=[2*i for i,on in enumerate(mask) if on]
        free=[i for i in range(4) if i not in fixed]
        candidate_refs=references.copy();q=np.zeros(4)
        for i,on in enumerate(mask):
            if on:
                if not previous_active[i]:candidate_refs[i]=float(previous_q[2*i])
                q[2*i]=candidate_refs[i]
        H=K.copy()
        for i,on in enumerate(mask):
            if on:H[2*i+1,2*i+1]+=100.
        q[free]=np.linalg.solve(H[np.ix_(free,free)],(np.array(W)-H@q)[free])
        contact=K@q-W
        admissible=all(q[2*i+1]<-1e-10 if on else q[2*i+1]>=-1e-10 for i,on in enumerate(mask))
        if admissible:
            for i,on in enumerate(mask):
                assert abs(contact[2*i+1]-100*max(0,-q[2*i+1]))<1e-9
                if not on:assert abs(contact[2*i])<1e-9
                else:assert abs(q[2*i]-candidate_refs[i])<1e-10
        candidates.append({"mask":list(mask),"q_mm":q.tolist(),"contact_vector_N":contact.tolist(),
                           "admissible":admissible,"episode_references_mm":candidate_refs})
    valid=[r for r in candidates if r["admissible"]];assert len(valid)==1
    picked=valid[0]
    assert np.allclose(picked["q_mm"],Q,atol=1e-10,rtol=0.)
    assert np.allclose(picked["contact_vector_N"],C,atol=1e-9,rtol=0.)
    previous_q=np.array(picked["q_mm"]);previous_active=picked["mask"];references=picked["episode_references_mm"]
    results.append({"stage_id":stage["id"],"all_four_elimination_candidates":candidates})
observed=json.loads((HERE/"observed.json").read_text())
assert len(observed["stages"])==4
for independent,recorded in zip(results,observed["stages"],strict=True):
    assert len(recorded["branch_candidates"])==4
    for candidate in independent["all_four_elimination_candidates"]:
        label="".join("T" if flag else "F" for flag in candidate["mask"])
        peer=next(c for c in recorded["branch_candidates"] if c["mask"]==label)
        assert peer["admissible"]==candidate["admissible"]
        assert np.allclose(peer["q_mm"],candidate["q_mm"],atol=1e-10,rtol=0.)
        assert np.allclose(peer["contact_vector_n"],candidate["contact_vector_N"],atol=1e-9,rtol=0.)
        for actual,reference in zip(peer["episode_references_mm"],candidate["episode_references_mm"],strict=True):
            if reference is None:assert actual is None
            else:assert actual is not None and abs(actual-reference)<1e-10
model=json.loads(MODEL.read_text())
normals={name for name,r in model["connection_ownership"].items() if r.get("role")=="floor_normal"}
tangents={name for name,r in model["connection_ownership"].items() if r.get("role")=="assumed_no_slip_floor"}
assert len(normals)==len(tangents)==100 and {name+"_friction" for name in normals}==tangents
output={"fixture_sha256":FIXTURE_PIN,"method":"Independent constrained-coordinate elimination, all four masks per stage",
        "stages":results,"frozen_input_normal_cells":100,"frozen_input_paired_tangent_ownership_rows":100,
        "exhaustive_frozen_floor_mask_upper_count":2**100,"qualified_for_design":False,"native_solve_executed":False}
(HERE/"parent-elimination-check.json").write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
print("Parent elimination: all 4 states uniquely reproduce; 16 masks checked; global floor contains 100 cells")
