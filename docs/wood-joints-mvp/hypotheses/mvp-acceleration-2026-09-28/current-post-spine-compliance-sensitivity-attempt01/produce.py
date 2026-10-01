"""Existing property scenarios applied to a fixed refined local pressure grid."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from fea.wood_joint_reduced_properties import build as property_inputs
PROPERTY_PIN = "26b6e8bf8800208bfb867439694afa705558ac63ca338778e9210e940a55d9a1"


def build():
    prop_path = ROOT / "fea/wood_joint_reduced_properties.py"
    assert hashlib.sha256(prop_path.read_bytes()).hexdigest() == PROPERTY_PIN
    pressure_path = HERE.parent / "current-post-spine-pressure-resolution-attempt01/produce.py"
    spec = importlib.util.spec_from_file_location("pressure", pressure_path)
    pressure = importlib.util.module_from_spec(spec); spec.loader.exec_module(pressure)
    for path, pin in pressure.PINS.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == pin
    p = property_inputs()
    axes = [f"knee_outer_left_post_{i}" for i in (1, 2)]
    ties = {r["axis_id"]: r for r in p["bolt_outer_seat_axial_ties"] if r["axis_id"] in axes}
    n = 256
    yy, zz = np.meshgrid(-175.7+(np.arange(n)+.5)*133.35/n,
                          139.7+(np.arange(n)+.5)*99.2/n)
    y,z = yy.ravel(),zz.ravel(); keep = np.ones(len(y), dtype=bool)
    for zc in (171.45,213.5):
        keep &= (y+137.6)**2+(z-zc)**2 >= 3.75**2
    y,z = y[keep],z[keep]; cell_area=133.35*99.2/n**2
    tie_A=np.array([[1.,(zc-192.475)/50.,0.] for zc in (171.45,213.5)])
    A=np.vstack((tie_A,np.column_stack((np.ones(len(y)),(z-192.475)/50.,(y+137.6)/50.))))
    sign=np.r_[np.ones(2),-np.ones(len(y))]
    scenarios=[r["stiffness_basis"]["sensitivity_scenarios"] for r in (ties[a] for a in axes)]
    assert len(scenarios[0]) == len(scenarios[1]) == 24
    rows=[]
    fields=("first_outer_seat_frame_scenario_id","second_outer_seat_frame_scenario_id",
            "wood_column_depth_factor_of_equivalent_washer_diameter","steel_E_mpa")
    for index, pair in enumerate(zip(*scenarios, strict=True)):
        assert all(pair[0][key]==pair[1][key] for key in fields)
        kval=[r["effective_axial_stiffness_n_per_mm"] for r in pair]
        k=np.r_[kval,np.full(len(y),100.*cell_area)]
        for name,q in {"My+":[0.,20.,0.],"My-":[0.,-20.,0.],"Mz+":[0.,0.,-20.],"Mz-":[0.,0.,20.]}.items():
            u,f,err=pressure.solve(A,k,sign,np.array(q),np.array([.001,0.,0.]))
            u2,f2,_=pressure.solve(A,k,sign,np.array(q),u+[1e-4,-1e-4,1e-4])
            assert np.allclose(u,u2,rtol=1e-7,atol=1e-9)
            assert np.max(abs(f[:2]-f2[:2]))<1e-5
            rows.append({"scenario_index":index,"case":name,"tie_stiffness_N_per_mm":kval,
                         "ties_N":f[:2].tolist(),"total_tie_N":float(sum(f[:2])),
                         "wrench_residual":err,"scenario":{key:pair[0][key] for key in fields}})
    summary={name:{"min_total_tie_N":min(r["total_tie_N"] for r in rows if r["case"]==name),
                   "max_total_tie_N":max(r["total_tie_N"] for r in rows if r["case"]==name)}
             for name in ("My+","My-","Mz+","Mz-")}
    return {"property_producer_sha256":PROPERTY_PIN,"pressure_producer_sha256":hashlib.sha256(pressure_path.read_bytes()).hexdigest(),
            "property_source_pins":p["source_sha256"],"grid":n,"rows":rows,"summary":summary,
            "post_1_exact_stiffness_basis":ties[axes[0]]["stiffness_basis"],
            "scope":"24 existing paired ring/depth/steel-E scenarios; imposed unit moments on rigid local BG001 only",
            "qualified_for_design":False,"native_solve_executed":False}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--verify",action="store_true");args=parser.parse_args()
    d=build();out=HERE/"sensitivity.json"
    if args.verify:
        old=json.loads(out.read_text());assert d["property_source_pins"]==old["property_source_pins"]
        assert d["pressure_producer_sha256"]==old["pressure_producer_sha256"]
        for a,b in zip(d["rows"],old["rows"],strict=True):
            assert a["scenario"]==b["scenario"] and a["case"]==b["case"]
            assert np.allclose(a["ties_N"],b["ties_N"],rtol=1e-8,atol=1e-7)
    else:
        out.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
    print(json.dumps(d["summary"],indent=2))
