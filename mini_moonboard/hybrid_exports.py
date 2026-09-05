"""Separate full candidate artifacts; never overwrite the plywood reference."""
import hashlib
import json
from pathlib import Path

import cadquery as cq

from . import hybrid_frame as h
from .box_exports import exact_bounds, write_csv
from .export import _export_step
from .raster import render


def export(directory=Path("exports/hybrid-full"), viewer=None):
    directory.mkdir(parents=True,exist_ok=True)
    for size in ("2x10","2x12"):
        parts=h.parts(size)
        connections=h.connections(size)
        assembly=cq.Assembly(name=f"hybrid_{size}_PROVISIONAL")
        solids=[]
        for p in parts:
            assembly.add(p.shape,name=p.name)
            color=(120,135,145) if p.name.startswith("angle_") else (
                (40,46,51) if p.name.startswith("main_") else (157,90,36))
            solids.append((p.shape,color))
        for c in connections:
            shape=cq.Compound.makeCompound(c.components())
            assembly.add(shape,name="fastener_"+c.name)
            solids.append((shape,(210,65,65) if c.kind=="bolt" else (41,182,214)))
        _export_step(assembly,directory/f"{size}.step")
        render(solids,directory/f"{size}_front.png")
        # Rear view keeps geometry exact: rotate camera-equivalent scene 180°
        # around Z for this second projection, not the export or viewer model.
        render([(shape.rotate((0,0,0),(0,0,1),180),color) for shape,color in solids],
               directory/f"{size}_rear.png")
        write_csv(directory,f"{size}_parts.csv",
            ("part","layers","dimension_1_mm","dimension_2_mm","dimension_3_mm",
             "dimension_1_in","dimension_2_in","dimension_3_in","description"),
            [(p.name,p.laminations,*[round(v,3) for v in p.blank],
              *[round(v/25.4,4) for v in p.blank],p.description) for p in parts])
        write_csv(directory,f"{size}_connections.csv",
            ("connection","kind","members","x_mm","y_mm","z_mm","axis_x","axis_y","axis_z",
             "length_mm","length_in","diameter_mm","grip_mm","status"),
            [(c.name,c.kind," + ".join(c.members),*c.start.toTuple(),*c.direction.toTuple(),
              c.length,c.length/25.4,c.diameter,c.grip,"NOMINAL envelope; no rated product/capacity selected")
             for c in connections])
        if viewer is not None:
            viewer_mesh(size,viewer)
    write_manifest(directory)


def write_manifest(directory):
    sources=("mini_moonboard/hybrid_frame.py","mini_moonboard/hybrid.py",
             "mini_moonboard/box_frame.py","mini_moonboard/model.py",
             "mini_moonboard/panel_grid.py","mini_moonboard/raster.py",
             "mini_moonboard/hybrid_exports.py")
    data={"sources":{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
          "artifacts":{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted(directory.iterdir()) if p.name!="manifest.json"}}
    (directory/"manifest.json").write_text(json.dumps(data,indent=2)+"\n")


def viewer_mesh(size, root):
    if size not in ("2x10", "2x12"):
        raise ValueError("Only clearance-screened complete candidates have viewer exports")
    directory=root/"hybrid"/size
    models=directory/"models"
    models.mkdir(parents=True,exist_ok=True)
    items=[]
    entries=[(p.name,p.shape,p.blank,p.description,"part") for p in h.parts(size)]
    entries.extend(("fastener_"+c.name,cq.Compound.makeCompound(c.components()),
                    (c.length,c.diameter,c.diameter)," + ".join(c.members)+
                    "; nominal hardware envelope, capacity unvalidated",c.kind) for c in h.connections(size))
    for name,shape,dims,description,kind in entries:
        path=models/f"{name}.stl"
        cq.exporters.export(shape,str(path),cq.exporters.ExportTypes.STL,tolerance=.5)
        bounds=exact_bounds(shape)
        items.append({"name":name,"path":str(path.relative_to(root)),
            "viewer_aabb_mm":[bounds.xlen,bounds.ylen,bounds.zlen],
            "fabrication":{"dimensions_mm":list(dims),"description":description,
                "kind":kind,"clearance_status":"Geometry screened; NOT structural approval"}})
    bounds=exact_bounds(cq.Compound.makeCompound([p.shape for p in h.parts(size)]))
    (directory/"parts.json").write_text(json.dumps({"parts":items,
        "bounds_mm":[[getattr(bounds,a+end) for a in "xyz"] for end in ("min","max")]},indent=2)+"\n")


if __name__=="__main__":
    export()
