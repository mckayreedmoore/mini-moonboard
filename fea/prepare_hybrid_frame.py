"""Freeze complete hybrid timber for matching ideal-bonded bulk comparisons."""
import hashlib
import json
import math
import subprocess
from pathlib import Path

import cadquery as cq

from mini_moonboard import box_frame as b
from mini_moonboard import hybrid_frame as h
from mini_moonboard.panel_grid import main_tnut_datums
from mini_moonboard.stability import evaluate_load, load_cases, row_point


def stability(size):
    # Separate densities remain explicit assumptions.
    items=[(p.shape,7850 if p.name.startswith("angle_") else 600) for p in h.parts(size)]
    # Hardware mass is omitted for comparability with the old timber-only screen;
    # angle plates are a distinct candidate material and included explicitly.
    masses=[shape.Volume()/1e9*density for shape,density in items]
    mass=sum(masses)
    centre=sum(m*shape.centerOfMass(shape).y for m,(shape,_) in zip(masses,items,strict=True))/mass
    faces=[f for shape,_ in items for f in shape.Faces()
           if abs(f.BoundingBox().zmin)<1e-5 and abs(f.BoundingBox().zmax)<1e-5]
    a=min(f.BoundingBox().ymin for f in faces)
    bb=max(f.BoundingBox().ymax for f in faces)
    y,z=row_point(12)
    results=[]
    for load in load_cases():
        case=evaluate_load(mass_kg=mass,centre_y_mm=centre,kicker_toe_y_mm=a,
            leg_toe_y_mm=bb,load_y_mm=y,load_z_mm=z,load=load)
        results.append({"case":load.name,"basis":load.basis,
            "kicker_reaction_n":case.kicker_reaction_n,"leg_reaction_n":case.leg_reaction_n,
            "overturning_factor":case.overturning_factor if math.isfinite(case.overturning_factor) else None,
            "friction_required":case.friction_required,
            "status":case.status})
    return {"mass_kg":mass,"centre_y_mm":centre,"kicker_toe_y_mm":a,"leg_toe_y_mm":bb,
            "load_y_mm":y,"load_z_mm":z,"cases":results,
            "assumptions":"Drilled wood 600 kg/m3, drilled angle steel 7850 kg/m3. Fasteners, holds, glue, LEDs omitted. 2D rigid body; no measured friction, no 3D tipping, no strength rating."}


def main():
    for size in ("2x10","2x12"):
        directory=Path("fea/generated/hybrid")/size
        directory.mkdir(parents=True,exist_ok=True)
        timber=[p for p in h.parts(size,False) if not p.name.startswith("angle_")]
        step=directory/"box_frame_bulk.step"
        cq.exporters.export(cq.Compound.makeCompound([p.shape for p in timber]),str(step))
        info={"parts":[p.name for p in timber],"candidate":size,
            "geometry_commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "step_sha256":hashlib.sha256(step.read_bytes()).hexdigest(),
            "geometry_source_sha256":{name:hashlib.sha256(Path(name).read_bytes()).hexdigest()
                for name in ("mini_moonboard/hybrid_frame.py","mini_moonboard/hybrid.py","mini_moonboard/box_frame.py")},
            "audited_load_targets_mm":[b.point(main_tnut_datums()[label][0]-b.HALF,
                main_tnut_datums()[label][1],-18).toTuple() for label in ("A12","C12","F12","H12","K12")],
            "audited_cases":[{"name":c.name,"basis":c.basis,"force_n":[0,c.force_y_n,c.force_z_n]} for c in load_cases()],
            "assumptions":"Hybrid timber bulk without holes/reliefs; all touching timber perfectly bonded, including interfaces actually fastened via angles. Steel/fastener stiffness not resolved. Fixed floor, no gravity. Isotropic screening E=7000MPa nu=.3 for all wood, not selected lumber properties. Comparable incremental stiffness only, no joint or unanchored validation."}
        (directory/"box_frame_bulk.json").write_text(json.dumps(info,indent=2)+"\n")
        (directory/"stability.json").write_text(json.dumps(stability(size),indent=2)+"\n")
        print(directory)


if __name__=="__main__":
    main()
