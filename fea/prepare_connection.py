"""Freeze current C10 panel geometry; reuse a verified drilled-panel mesh."""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import cadquery as cq

from mini_moonboard.box_frame import HALF, block, frame_parts, normal, point
from mini_moonboard.panel_grid import main_led_datums, main_tnut_datums

from .panel_math import dot, head_nodes, minus
from .record_joint_results import read_deck


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--size",type=int,choices=(20,15),default=20)
    args=parser.parse_args()
    source=Path("fea/generated")
    output=source/"connection"
    output.mkdir(exist_ok=True)
    name=f"panel_main_upper_left_{args.size}_C10"
    raw=(source/f"{name}.inp").read_text()
    record=next(r for r in json.loads((source/"panels.json").read_text()) if r["name"]=="main_upper_left")
    parts={p.name:p.shape for p in frame_parts()}
    reference=cq.importers.importStep(str(source/"panel_main_upper_left.step")).val()
    current=parts["main_upper_left"]
    difference=current.cut(reference).Volume()+reference.cut(current).Volume()
    if difference>1e-3:
        raise ValueError("Current panel differs from mesh source: regenerate panel mesh first")
    world,_,_,elements=read_deck(raw)
    nodes={t:(xyz[0],dot(minus(xyz,record["origin_mm"]),record["along"]),
              dot(minus(xyz,record["origin_mm"]),record["normal"])) for t,xyz in world.items()}
    heads={s["name"]:set(head_nodes(world,record,s)) for s in record["screws"]}
    # Recover exterior planar/back and conical/head triangles from the C3D10
    # volume mesh. No new nearest-node point constraints are introduced.
    faces=((0,1,2,4,5,6),(0,1,3,4,8,7),(1,2,3,5,9,8),(0,2,3,6,9,7))
    section=""
    head_weights={name:{} for name in heads}
    back_weights={}
    for line in raw.splitlines():
        if line.startswith("*"):
            section=line.upper()
            continue
        if not section.startswith("*ELEMENT"):
            continue
        cells=[int(v) for v in line.split(",") if v.strip()]
        if len(cells)!=11:
            raise ValueError("Expected single-line C3D10 connectivity")
        for indices in faces:
            tri=[cells[i+1] for i in indices]
            matches=[name for name,tags in heads.items() if set(tri)<=tags]
            is_back=all(abs(nodes[t][2]-18)<1e-5 for t in tri)
            if not matches and not is_back:
                continue
            a,b,c=[nodes[t] for t in tri[:3]]
            # Projected seating/contact area in the panel plane.
            area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
            for weights in ([back_weights] if is_back else [head_weights[n] for n in matches]):
                for t in tri[3:]:
                    weights[t]=weights.get(t,0)+area/3
    if any(not weights for weights in head_weights.values()):
        raise ValueError("Unresolved head quadrature")
    backing=[parts[n] for n in ("panel_edge_left_upper","panel_seam_vertical_upper","panel_edge_top","panel_seam_horizontal")]
    # Analysis-only alternative: central longitudinal batten, with existing
    # 40 mm hardware reliefs. No added attachment is silently assumed.
    centre=-HALF/2
    extra=block(centre-35,centre+35,HALF,2*HALF,0,38.1)
    for x,s in (*main_tnut_datums().values(),*main_led_datums().values()):
        if abs(x-HALF-centre)<55:
            extra=extra.cut(cq.Solid.makeCylinder(20,40,point(x-HALF,s,-1),normal()))
    patches={"baseline":{},"closer_backing":{}}
    for t,w in back_weights.items():
        probe=cq.Vector(*world[t])+normal()*.1
        present=any(shape.isInside(probe,1e-6) for shape in backing)
        if present:
            patches["baseline"][t]=w
        if present or extra.isInside(probe,1e-6):
            patches["closer_backing"][t]=w
    loads={}
    section=""
    for line in raw.splitlines():
        if line.startswith("*"):
            section=line.upper()
        elif section=="*CLOAD" and line.strip():
            t,dof,value=line.split(",")
            loads[int(t)]=loads.get(int(t),0)+float(value)*record["normal"][int(dof)-1]
    if not math.isclose(sum(loads.values()),-1200,abs_tol=1e-6):
        raise ValueError("Unexpected C10 resultant")
    start=raw.index("******* E L E M E N T S")
    end=raw.index("*NSET,NSET=ALLN")
    mesh="*NODE\n"+"\n".join(f"{t},{x:.12g},{y:.12g},{z:.12g}" for t,(x,y,z) in nodes.items())+"\n"+raw[start:end]
    mesh_path=output/f"mesh_{args.size}.inp"
    mesh_path.write_text(mesh)
    info={"revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
          "mesh_mm":args.size,"panel_geometry_difference_mm3":difference,
          "nodes":len(nodes),"elements":len(elements),"heads":head_weights,"backing":patches,"loads":loads,
          "coordinates":"X across panel; Y uphill from upper-panel bottom; Z from climbing face into backing",
          "source_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
              (source/f"{name}.inp",source/"panel_main_upper_left.step",mesh_path,Path("mini_moonboard/box_frame.py"),Path("mini_moonboard/model.py"))}}
    (output/f"mesh_{args.size}.json").write_text(json.dumps(info,indent=2)+"\n")
    print({"revision":info["revision"],"nodes":len(nodes),"heads":len(heads),"backing_nodes":{k:len(v) for k,v in patches.items()}})


if __name__=="__main__":
    main()
