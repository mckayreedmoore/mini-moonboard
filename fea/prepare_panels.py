"""Export current drilled face panels and their actual screw-head locations."""
import json
import math
import subprocess
from pathlib import Path

import cadquery as cq

from mini_moonboard.box_frame import HALF, connections, frame_parts, normal, point
from mini_moonboard.model import (
    ANGLE_FROM_VERTICAL_DEG,
    PANEL_THICKNESS_MM,
    V1_KICKER_HEIGHT_MM,
    V1_SELECTED_TNUT_FLANGE_DIAMETER_MM,
)
from mini_moonboard.panel_grid import kicker_foothold_datums, main_tnut_datums


def main():
    directory=Path("fea/generated")
    directory.mkdir(parents=True,exist_ok=True)
    a=math.radians(ANGLE_FROM_VERTICAL_DEG)
    frames={p.name:p for p in frame_parts()}
    records=[]
    for name in ("main_upper_left","kicker_left"):
        main=name.startswith("main")
        origin=point(-HALF,HALF,-PANEL_THICKNESS_MM) if main else cq.Vector(-HALF,-PANEL_THICKNESS_MM,0)
        n=normal() if main else cq.Vector(0,-1,0)
        along=cq.Vector(0,math.sin(a),math.cos(a)) if main else cq.Vector(0,0,1)
        screws=[c for c in connections() if c.kind=="screw" and c.members[0]==name]
        targets=[]
        for label in (("C10","C12") if main else ("3",)):
            if main:
                x,s=main_tnut_datums()[label]
                target=point(x-HALF,s,0)
            else:
                x,z=kicker_foothold_datums()[label]
                target=cq.Vector(x-HALF,-2*PANEL_THICKNESS_MM,V1_KICKER_HEIGHT_MM+z)
            targets.append({"label":label,"back_centre_mm":target.toTuple(),"patch_radius_mm":V1_SELECTED_TNUT_FLANGE_DIAMETER_MM/2})
        shape=frames[name].shape
        if not shape.isValid() or len(shape.Solids())!=1:
            raise ValueError("Invalid face panel")
        cq.exporters.export(shape,str(directory/f"panel_{name}.step"))
        records.append({"name":name,"origin_mm":origin.toTuple(),"normal":n.toTuple(),"along":along.toTuple(),
                        "thickness_mm":PANEL_THICKNESS_MM,"targets":targets,
                        "screws":[{"name":c.name,"head_mm":c.start.toTuple(),"shank_diameter_mm":c.diameter} for c in screws],
                        "geometry_commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()})
    (directory/"panels.json").write_text(json.dumps(records,indent=2)+"\n")


if __name__=="__main__":
    main()
