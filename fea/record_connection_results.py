"""Reparse accepted C10 cases and publish compact comparison evidence."""
import json
import subprocess
import sys
from pathlib import Path

from .record_updated_results import verify_hashes


def main():
    directory=Path("fea/generated/connection")
    paths=sorted(directory.glob("c10_*.json"))
    records=[]
    for path in paths:
        r=json.loads(path.read_text())
        verify_hashes({"evidence_sha256":{n:h for n,h in r["evidence_sha256"].items() if n.endswith((".inp",".dat"))}},directory)
        k=r["assumed_axial_stiffness_n_per_mm"]/(2 if r["variant"]=="stiffer_attachment" else 1)
        command=[sys.executable,"fea/solve_connection.py","--reparse","--size",str(r["mesh_mm"]),
                 "--variant",r["variant"],"--stiffness",str(k),"--penalty",str(r["backing_penalty_n_per_mm3"])]
        if r["modulus_mpa"]!=7000:
            command += ["--modulus",str(r["modulus_mpa"])]
        if r.get("initial_backing_gap_mm",0):
            command += ["--contact-gap",str(r["initial_backing_gap_mm"])]
        if r.get("tight_convergence",False):
            command.append("--tight")
        if r["load_direction"]=="push":
            command.append("--push")
        subprocess.run(command,check=True,capture_output=True,text=True)
        records.append(json.loads(path.read_text()))
    if {r["variant"] for r in records}!={"baseline","stiffer_attachment","closer_backing"}:
        raise ValueError("Three accepted comparison variants required")
    output=Path("fea/results/connection_comparison.json")
    output.write_text(json.dumps(records,indent=2)+"\n")
    geometry=[]
    for size in (20,15):
        m=json.loads((directory/f"mesh_{size}.json").read_text())
        geometry.append({k:v for k,v in m.items() if k not in ("heads","backing","loads")}|{
            "head_count":len(m["heads"]),"head_projected_area_mm2":{k:sum(w.values()) for k,w in m["heads"].items()},
            "backing_area_mm2":{k:sum(w.values()) for k,w in m["backing"].items()},"applied_normal_force_n":sum(m["loads"].values())})
    Path("fea/results/connection_geometry.json").write_text(json.dumps(geometry,indent=2)+"\n")
    print(f"Published {len(records)} independently reparsed cases")


if __name__=="__main__":
    main()
