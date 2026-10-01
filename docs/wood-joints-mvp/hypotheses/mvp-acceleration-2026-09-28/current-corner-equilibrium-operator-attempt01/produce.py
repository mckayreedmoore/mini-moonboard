"""Complete five-body internal carrier operator; no response or native solve."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/"current-corner-interface-recovery-map-attempt01/interface-map.json"
PIN="c5ce97cbe1fffbb18dfaf1a544fa9a300991b06056b21b37ba3e08b8a1c6aec8"
LENGTH=100.


def build():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==PIN
    d=json.loads(SOURCE.read_text());bodies=d["bodies"];datums=d["descriptor_midpoint_datums_mm"]
    columns=[];records=[]
    def add(name,first,second,p1,p2,direction,role):
        v=np.zeros(6*len(bodies));n=np.array(direction)
        assert abs(np.linalg.norm(n)-1)<1e-8
        for body,point,sign in ((first,p1,1.),(second,p2,-1.)):
            index=bodies.index(body)*6;r=np.array(point)-datums[body];f=sign*n
            v[index:index+6]=np.r_[f,np.cross(r,f)/LENGTH]
        columns.append(v);records.append({"name":name,"first":first,"second":second,
                                         "first_point_mm":p1,"second_point_mm":p2,
                                         "direction_on_first":direction,"role":role})
    for row in d["connection_ownership"]:
        if not row["internal"] or row.get("axis_id") not in d["new_corner_axes"]:continue
        if row["role"]=="candidate_bolt_lateral_plane":
            for index,n in enumerate(row["force_basis"][1:]):
                add(row["name"]+f"/transverse{index+1}",row["first"],row["second"],
                    row["point"],row["point"],n,"bolt_lateral")
        elif row["role"]=="physical_bolt_outer_seat_tension":
            add(row["name"],row["first"],row["second"],row["first_point"],
                row["second_point"],row["scalar_normal"],"bolt_axial")
    for group in d["contact_groups"]:
        if not group["internal"]:continue
        for row in group["cells"]:
            add(row["name"],row["first"],row["second"],row["point_xyz_mm"],
                row["point_xyz_mm"],row["normal_xyz"],"compression_contact")
    B=np.column_stack(columns);assert B.shape==(30,50)
    # Independent global rigid-motion work: forces and moments must cancel.
    G=np.zeros((6,30))
    for i,body in enumerate(bodies):
        r=np.array(datums[body])/LENGTH
        G[:3,i*6:i*6+3]=np.eye(3)
        skew=np.array([[0,-r[2],r[1]],[r[2],0,-r[0]],[-r[1],r[0],0]])
        G[3:,i*6:i*6+3]=skew;G[3:,i*6+3:i*6+6]=np.eye(3)
    cancel=float(np.max(abs(G@B)));assert cancel<1e-10
    bolt_indices=[i for i,r in enumerate(records) if r["role"]!="compression_contact"]
    def rank_report(matrix):
        u,s,vh=np.linalg.svd(matrix,full_matrices=True)
        rank=int(sum(s>1e-10*s[0]));null=vh[rank:].T
        null_res=float(np.max(abs(matrix@null))) if null.size else 0.
        return {"columns":matrix.shape[1],"rank":rank,
                "relative_motion_nullity_after_six_rigid_modes":30-rank-6,
                "force_sharing_nullity":matrix.shape[1]-rank,
                "singular_values":s.tolist(),"nullspace_residual":null_res},null
    all_report,null=rank_report(B);bolts_report,_=rank_report(B[:,bolt_indices])
    assert all_report["rank"]<=24
    # Null columns describe algebraic self-stress; they need not obey unilateral signs.
    return {"source_sha256":PIN,"bodies":bodies,"datums_mm":datums,
            "moment_row_scale_mm":LENGTH,"carrier_records":records,"operator_rows":B.tolist(),
            "all_carrier_report":all_report,"bolts_only_report":bolts_report,
            "global_wrench_cancellation_residual":cancel,
            "force_sharing_nullspace_columns":null.T.tolist(),
            "scope":"Input geometry operator only; contact/tie sign feasibility, stiffness and applied actions not supplied",
            "qualified_for_design":False,"native_solve_executed":False}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--verify",action="store_true");args=parser.parse_args()
    data=build();out=HERE/"operator.json"
    if args.verify:
        old=json.loads(out.read_text());assert old["source_sha256"]==data["source_sha256"]
        assert np.allclose(old["operator_rows"],data["operator_rows"],rtol=0,atol=1e-12)
        for key in ("all_carrier_report","bolts_only_report"):
            assert old[key]["rank"]==data[key]["rank"]
    else:out.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    for key in ("all_carrier_report","bolts_only_report"):
        print(key,{k:v for k,v in data[key].items() if k!="singular_values"})
    print("global internal-wrench cancellation",data["global_wrench_cancellation_residual"])
