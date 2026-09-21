"""Schedules and diagnostics derived from the current box-frame assembly."""
import csv
from collections import Counter
from functools import cache
from itertools import combinations
from pathlib import Path

import cadquery as cq
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

from .box_frame import connections, frame_parts


def exact_bounds(shape):
    """Ignore cached display triangulations when reporting CAD dimensions."""
    box=Bnd_Box()
    BRepBndLib.AddOptimal_s(shape.wrapped,box,False,False)
    return cq.BoundBox(box)


def write_csv(directory, filename, header, rows):
    directory.mkdir(parents=True, exist_ok=True)
    path=directory/filename
    with path.open("w",newline="") as stream:
        writer=csv.writer(stream,lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return path


def cut_list(directory):
    write_csv(directory,"mini_moonboard_v1_sheet_layout.csv",
              ("sheet","stock_thickness_mm","part","layer","x_mm","y_mm","width_mm","length_mm","kerf_mm"),sheet_layout())
    return write_csv(directory,"mini_moonboard_v1_cut_list.csv",
        ("assembly","part","quantity","length_mm","width_mm","thickness_mm","length_in","width_in","thickness_in","note"),
        [("box frame",p.name,p.laminations,*[f"{v:.3f}" for v in (*p.blank[:2],p.blank[2]/p.laminations)],*[f"{v/25.4:.4f}" for v in (*p.blank[:2],p.blank[2]/p.laminations)],p.description) for p in frame_parts()])


def sheet_layout():
    """First-fit bounding-blank layout, preserving factory edges, 2.4 mm kerf."""
    sheets=[]
    rows=[]
    blanks=[(p.blank[2]/p.laminations,p.blank[0],p.blank[1],p.name,layer)
            for p in frame_parts() for layer in range(1,p.laminations+1)]
    for thickness,length,width,name,layer in sorted(blanks,key=lambda b:(b[0],-b[1],-b[2],b[3],b[4])):
        if length>2438.4+1e-5 or width>1219.2+1e-5:
            raise ValueError(f"blank does not fit stock: {name}")
        placement=None
        for index,(stock,shelves) in enumerate(sheets):
            if stock!=thickness:
                continue
            for shelf in shelves:
                if length<=shelf[1]+1e-5 and shelf[2]+width<=1219.2+1e-5:
                    placement=(index,shelf[2],shelf[0])
                    shelf[2]+=width+2.4
                    break
            if placement:
                break
            y=shelves[-1][0]+shelves[-1][1]+2.4
            if y+length<=2438.4+1e-5:
                shelves.append([y,length,width+2.4])
                placement=(index,0,y)
                break
        if placement is None:
            sheets.append((thickness,[[0,length,width+2.4]]))
            placement=(len(sheets)-1,0,0)
        index,x,y=placement
        rows.append((index+1,thickness,name,layer,x,y,width,length,2.4))
    return rows


def connection_schedule(directory):
    return write_csv(directory,"mini_moonboard_v1_connection_schedule.csv",
        ("connection","members","quantity","x_mm","y_mm","z_mm","axis_x","axis_y","axis_z","length_mm","length_in","diameter_mm","grip_mm","clearance_hole_mm","status"),
        [(c.name," + ".join(c.members),1,*[f"{v:.3f}" for v in c.start.toTuple()],*c.direction.toTuple(),c.length,c.length/25.4,c.diameter,c.grip,"10" if c.kind=="bolt" else "5.2 clearance / 3.2 pilot; 10 mm countersink", "PROVISIONAL connection; strength and plywood edge fastening require review") for c in connections()])


def bom(directory):
    counts=Counter((c.kind,c.diameter,c.length) for c in connections())
    bolts=sum(v for (kind,_,_),v in counts.items() if kind=="bolt")
    layout=sheet_layout()
    stock_counts=Counter(thickness for _,thickness in {(r[0],r[1]) for r in layout})
    rows=[("19.05 mm / 3/4 in birch plywood for laminations",f"{stock_counts[19.05]} sheets","Conservative bounding-blank sheet layout; two layers = 38.1 mm; 2.4 mm separating kerf."),
          ("18 mm climbing plywood",f"{stock_counts[18]} sheets","4 main panels + 2 kicker panels; separate stock thickness."),
          ("Mini MoonBoard 2025 Setup Hold Bundle","1, SKU 60-105-2025","User-owned; hold-specific bolts and pin screws separate."),
          ("Escape 3-hole screw-in T-nuts, 3/8-16","142 + spares","Received flange geometry; fixing screws included per selected listing."),
          ("MoonBoard LED System","1, SKU 60-201-V5","132 installed lights; retain unused kit lights."),
          ("3/8 in washers, 25.4 mm OD x 2 mm",2*bolts,"Two per bolt; nominal dimensions modelled."),
          ("3/8 in nuts, 9 mm axial envelope",bolts,"Actual thread engagement and locking method require review."),
          ("Lamination adhesive","coverage-dependent","Select product and documented spread/clamping/cure procedure."),
          ("Floor pads / anti-slip interface","pending floor properties","No anchoring; pad is a separate user element.")]
    rows += [(f"{kind}: diameter {diameter:g} mm, length {length:g} mm / {length/25.4:g} in",count,"Provisional hardware envelope; connection schedule gives each axis and joined members.") for (kind,diameter,length),count in sorted(counts.items())]
    return write_csv(directory,"mini_moonboard_v1_bom.csv",("item","quantity","note"),rows)


def overlap(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if any(min(getattr(aa,k+"max"),getattr(bb,k+"max"))-max(getattr(aa,k+"min"),getattr(bb,k+"min")) <= 1e-5 for k in "xyz"):
        return 0.0
    return a.intersect(b).Volume()


@cache
def collisions():
    found=[]
    for c in connections():
        roles=("washer inside","washer outside","head","nut") if c.kind=="bolt" else ("countersunk head",)
        for role,shape in zip(roles,c.components()[1:],strict=True):
            for p in frame_parts():
                volume=overlap(shape,p.shape)
                if volume>0.01:
                    found.append((c.name,role,p.name,volume))
    # Distinct fasteners may not cross one another. Same-fastener compound
    # components intentionally overlap (shaft/head/nut simplified envelopes).
    solids=[(c,cq.Compound.makeCompound(c.components())) for c in connections()]
    for (a,sa),(b,sb) in combinations(solids,2):
        volume=overlap(sa,sb)
        if volume>.01:
            found.append((a.name,"other fastener",b.name,volume))
    return tuple(found)


def metadata(name):
    from .export import _inch_fraction
    parts={p.name:p for p in frame_parts()}
    if name in parts:
        p=parts[name]
        dims,description=p.blank,p.description
        status=None
    else:
        c=next(c for c in connections() if c.name==name)
        dims=(c.length,c.diameter,c.diameter)
        description=f"{c.kind}: {' to '.join(c.members)}; nominal hardware, strength not assessed"
        status="FAIL: hardware collision" if any(row[0]==name or row[2]==name for row in collisions()) else "PASS: hardware clearance only"
    result={"description":description,"dimensions_mm":list(dims),"dimensions_imperial":[_inch_fraction(v) for v in dims]}
    if status:
        result["clearance_status"]=status
    return result


def clearance_report():
    rows=collisions()
    panel=sum(r[0].startswith("analysis_panel_screw_") for r in rows)
    table="\n".join(f"| {a} | {b} | {c} | {v:.3f} |" for a,b,c,v in rows) or "| None | — | — | 0 |"
    return f"""# Box-frame fastener clearance screen

Status: **{'FAIL' if rows else 'PASS'}** for nominal hardware clearance only.
Total non-shank collisions: **{len(rows)}**.
Panel-screw countersunk-head collisions: **{panel}**.

Every head, washer and nut is checked against every timber part. Countersinks
are cut into the receiving panel; screw shanks intentionally engage pilots.
Complete fasteners, including shanks, are also checked against other fasteners.
This is not a strength, withdrawal, edge-distance or thread-engagement approval.

| Connection | Component | Wood part | Overlap mm3 |
| --- | --- | --- | ---: |
{table}
"""


def drawing(directory: Path, suffix: str, direction):
    directory.mkdir(parents=True,exist_ok=True)
    shape=cq.Compound.makeCompound([p.shape for p in frame_parts()])
    svg=cq.exporters.getSVG(shape,opts={"projectionDir":direction,"showHidden":False,"width":900,"height":750})
    svg=svg.replace('<svg', '<svg data-units="mm"',1)
    svg=svg.replace('</svg>','<text x="20" y="30" fill="red">PROVISIONAL box frame — CAD-derived projection</text></svg>')
    path=directory/f"mini_moonboard_v1_{suffix}.svg"
    path.write_text("\n".join(line.rstrip() for line in svg.splitlines())+"\n")
    return path


def leg_profiles(directory):
    rows=[]
    for p in frame_parts():
        if not p.name.startswith("leg_"):
            continue
        # A side-facing orthographic drawing includes the true profile and
        # bolt bores. STEP is the exact 1:1 geometry for machining transfer.
        svg=cq.exporters.getSVG(p.shape,opts={"projectionDir":(1,0,0),"showHidden":False})
        (directory/f"mini_moonboard_v1_{p.name}_profile.svg").write_text("\n".join(line.rstrip() for line in svg.splitlines())+"\n")
        rows.append((p.name,2,*p.blank[:2],19.05,"continuous profile; see STEP and side SVG; no separate knee splice"))
    return write_csv(directory,"mini_moonboard_v1_leg_cut_schedule.csv",("member","lamination_quantity","blank_height_mm","blank_depth_mm","thickness_mm","cut_instruction"),rows)
