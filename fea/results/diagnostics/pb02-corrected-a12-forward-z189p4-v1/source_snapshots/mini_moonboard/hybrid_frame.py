"""Complete candidate geometry and nominal connections; NOT strength approval.

The original plywood frame and initial rim-only studies remain separate.
Board-local X/S/N and fastener envelopes reuse box_frame. Straight backing is
dry dressed lumber; shaped legs and kicker cheeks/splices remain laminated ply.
"""
import math
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import hybrid
from .panel_grid import kicker_foothold_datums, main_led_datums, main_tnut_datums

EDGE=88.9  # dressed 2x4, face width
SEAM=139.7  # dressed 2x6, face width
STEEL=6.0  # custom angle envelope, not a rated bracket product
SIDES=(("left",-1),("right",1))


def mid_x(sign):
    # Between grid columns C/D and I/J, not at the geometric panel centres
    # which lie nearly on a hold/LED column.
    return (700 if sign<0 else 1900)-b.HALF


def panel_attachments():
    result=list(b.panel_screws())
    for row,label in enumerate(("lower","upper")):
        for side,sign in SIDES:
            result.extend((f"main_{label}_{side}",mid_x(sign),row*b.HALF+s)
                          for s in (250.,550.,850.,1050.))
    return tuple(result)


@cache
def connections(size):
    rear=hybrid.WIDTHS[size]-18
    result=list(hybrid.leg_bolts(size))
    def screw(name,x,s,n,d,length,members):
        result.append(b.Connection(name,b.point(x,s,n),d,length,4.826,members))
    def bolt(name,start,d,members):
        result.append(b.Connection(name,start,d,63.5,9.525,members,"bolt",b.THICKNESS+STEEL))
    for i,(panel,x,s) in enumerate(panel_attachments(),1):
        member=b._batten_for(x,s) if i<=48 else "mid_"+panel.removeprefix("main_")
        screw(f"panel_{i}",x,s,-18,b.normal(),50.8,(panel,member))
    # Permanent screws stay in their backing modules during relocation.
    for c in b.connections():
        if c.name.startswith(("analysis_edge_screw_","analysis_batten_end_",
                              "analysis_kicker_end_")):
            result.append(c)
    # Kicker LED bodies need relief in the top backing. Locate the four screws
    # per long edge around those reliefs, with shared end columns on both edges.
    bores=[(x-b.HALF,b.V1_KICKER_HEIGHT_MM+s) for x,s in
           (*kicker_foothold_datums().values(),*[v for v in main_led_datums().values() if v[1]<0])]
    for col,(side,_) in enumerate(SIDES):
        for i in range(4):
            x=-b.HALF+col*b.HALF+50+i*(b.HALF-100)/3
            offsets=(0,) if i in (0,3) else (0,*[d for n in range(1,41) for d in (n,-n)])
            x=next(x+delta for delta in offsets
                   if all(math.hypot(x+delta-bx,z-bz)>=28 for bx,bz in bores for z in (25.,200.)))
            for edge,z in (("bottom",25.),("top",200.)):
                result.append(b.Connection(f"kicker_{side}_{edge}_{i}",cq.Vector(x,-18,z),
                    cq.Vector(0,-1,0),50.8,4.826,(f"kicker_{side}",f"kicker_batten_{edge}")))
    tangent=(b.point(0,1,0)-b.point(0,0,0)).normalized()
    for side,sign in SIDES:
        for index,(s,n) in enumerate(((s,n) for s in (-50.,50.)
                                      for n in (80.,rear-90)),1):
            screw(f"cheek_splice_{side}_{index}",sign*(b.HALF-b.THICKNESS),s,n,
                  cq.Vector(sign,0,0),63.5,(f"cheek_splice_{side}",
                  f"kicker_cheek_{side}" if s<0 else f"box_side_{side}"))
        # Two through-bolts per angle leaf. Top cap bolts are normal to cap;
        # cross-member bolts are normal to their broad uphill/downhill faces.
        for label,station,up in [("top",b.LENGTH,-1),
                                *[(f"cross_{i}",s+b.THICKNESS/2,1)
                                  for i,s in enumerate(b.CROSS_STATIONS,1)]]:
            angle=f"angle_{side}_{label}"
            beam="box_top" if label=="top" else "rear_"+label
            for j,n in enumerate((rear-65,rear-30),1):
                bolt(f"{angle}_wall_{j}",b.point(sign*(b.HALF+b.THICKNESS+2),
                     station+up*65,n),cq.Vector(-sign,0,0),(f"box_side_{side}",angle))
                start_s=station-up*(b.THICKNESS+2)
                bolt(f"{angle}_beam_{j}",b.point(sign*(b.HALF-60),start_s,n),
                     tangent*up,(beam,angle))
    for row,s in enumerate(b.CROSS_STATIONS,1):
        band="lower" if row==1 else "upper"
        for label,x in (("seam_left",-48.),("seam_right",48.),
                        ("mid_left",mid_x(-1)),("mid_right",mid_x(1))):
            rib=f"rib_{row}_{label}"
            batten="panel_seam_horizontal" if row==2 else (
                f"panel_seam_vertical_{band}" if label.startswith("seam")
                else f"mid_{band}_{label.removeprefix('mid_')}")
            screw(f"{rib}_front",x,s-28,0,b.normal(),88.9,(batten,rib))
            sign=-1 if x<0 else 1
            angle=f"angle_{rib}"
            for j,n in enumerate((rear-EDGE-25,rear-EDGE-60),1):
                bolt(f"{angle}_rib_{j}",b.point(x+sign*(b.THICKNESS/2+STEEL+2),s+26,n),
                     cq.Vector(-sign,0,0),(angle,rib))
            for j,dx in enumerate((38.,66.),1):
                result.append(b.Connection(f"{angle}_beam_{j}",
                    b.point(x+sign*(b.THICKNESS/2+dx),s,rear+2),-b.normal(),
                    114.3,9.525,(f"rear_cross_{row}",angle),"bolt",EDGE+STEEL))
    # Mid battens also have a declared connection to each horizontal end rail.
    for band,s0,s1 in (("lower",EDGE,b.HALF-SEAM/2),
                       ("upper",b.HALF+SEAM/2,b.LENGTH-EDGE)):
        for side,sign in SIDES:
            for end,station,d,rail in (
                ("bottom",s0-EDGE,tangent,"panel_edge_bottom") if band=="lower" else
                ("bottom",s0-SEAM,tangent,"panel_seam_horizontal"),
                ("top",s1+SEAM,-tangent,"panel_seam_horizontal") if band=="lower" else
                ("top",s1+EDGE,-tangent,"panel_edge_top")):
                # Through the full rail width, then 50 mm into the batten end.
                width=SEAM if rail=="panel_seam_horizontal" else EDGE
                screw(f"mid_end_{band}_{side}_{end}",mid_x(sign)+(-18 if band=="lower" else 18),station,19.05,
                      d,width+50,(rail,f"mid_{band}_{side}"))
    return tuple(result)


@cache
def parts(size, drilled=True):
    rear=hybrid.WIDTHS[size]-18
    result={p.name:p for p in hybrid.parts(size,drilled)}
    def add(name,shape,blank,note,layers=1):
        result[name]=b.Part(name,shape,blank,note,layers)
    def box(name,x0,x1,s0,s1,n0,n1,note):
        dims=sorted((x1-x0,s1-s0,n1-n0),reverse=True)
        add(name,b.block(x0,x1,s0,s1,n0,n1),tuple(dims),note)
    for name,p in list(result.items()):
        if name.startswith("main_"):
            result[name]=replace(p,description="18 mm climbing plywood; 12 perimeter + 4 mid-batten screws")
        elif name.startswith("kicker_"):
            result[name]=replace(p,description="18 mm kicker plywood; eight perimeter screws")
        elif name=="box_top":
            result[name]=replace(p,description=f"{size} top cap; detachable bolted steel angles")
    for p in b.frame_parts(False):
        if p.name.startswith("kicker_batten_"):
            shape=p.shape
            for x,s in (main_led_datums().values() if drilled else ()):
                if s<0:
                    shape=shape.cut(cq.Solid.makeCylinder(20,b.THICKNESS+2,
                        cq.Vector(x-b.HALF,-35,b.V1_KICKER_HEIGHT_MM+s),cq.Vector(0,-1,0)))
            result[p.name]=replace(p,shape=shape,laminations=1,
                description="lumber backing ripped to 50 mm from 2x4; top has LED relief notches")
    for side,sign in SIDES:
        xa=min(sign*b.HALF,sign*(b.HALF+b.THICKNESS))
        front,back=b.point(0,0,-18),b.point(0,0,rear)
        cheek=cq.Workplane("YZ").polyline([(front.y,0),(front.y,front.z),
              (back.y,back.z),(back.y,0)]).close().extrude(b.THICKNESS).translate((xa,0,0)).val()
        add(f"kicker_cheek_{side}",cheek,(back.z,abs(back.y-front.y),b.THICKNESS),
            "two-layer plywood floor-reaching transition",2)
        x0,x1=sorted((sign*b.HALF,sign*(b.HALF-b.THICKNESS)))
        splice=b.block(x0,x1,-100,100,50,rear-20)
        cut=cq.Workplane("XY").box(10000,10000,10000).translate((0,back.y-5000,0)).val()
        add(f"cheek_splice_{side}",splice.cut(cut).clean(),(200,rear-70,b.THICKNESS),
            "two-layer plywood splice trimmed to cheek rear; permanent screws",2)
        for label,station,up in [("top",b.LENGTH,-1),
                                *[(f"cross_{i}",s+b.THICKNESS/2,1)
                                  for i,s in enumerate(b.CROSS_STATIONS,1)]]:
            x0,x1=sorted((sign*b.HALF,sign*(b.HALF-100)))
            sx0,sx1=sorted((sign*b.HALF,sign*(b.HALF-STEEL)))
            s0,s1=sorted((station,station+up*STEEL))
            vs0,vs1=sorted((station+up*STEEL,station+up*100))
            shape=b.block(x0,x1,s0,s1,rear-EDGE,rear).fuse(
                b.block(sx0,sx1,vs0,vs1,rear-EDGE,rear)).clean()
            add(f"angle_{side}_{label}",shape,(100,100,EDGE),
                "STEEL custom 100x100x6 angle, 88.9 long; nominal sharp corner; fabrication/capacity unresolved")
    bounds=[("panel_edge_bottom",-b.HALF,b.HALF,0,EDGE),
            ("panel_edge_top",-b.HALF,b.HALF,b.LENGTH-EDGE,b.LENGTH),
            ("panel_seam_horizontal",-b.HALF,b.HALF,b.HALF-SEAM/2,b.HALF+SEAM/2)]
    for band,s0,s1 in (("lower",EDGE,b.HALF-SEAM/2),
                       ("upper",b.HALF+SEAM/2,b.LENGTH-EDGE)):
        bounds.extend([(f"panel_edge_left_{band}",-b.HALF,-b.HALF+EDGE,s0,s1),
                       (f"panel_edge_right_{band}",b.HALF-EDGE,b.HALF,s0,s1),
                       (f"panel_seam_vertical_{band}",-SEAM/2,SEAM/2,s0,s1)])
        bounds.extend((f"mid_{band}_{side}",mid_x(sign)-EDGE/2,
                       mid_x(sign)+EDGE/2,s0,s1) for side,sign in SIDES)
    for name,x0,x1,s0,s1 in bounds:
        shape=b.block(x0,x1,s0,s1,0,b.THICKNESS)
        for x,s in ((*main_tnut_datums().values(),*main_led_datums().values()) if drilled else ()):
            x-=b.HALF
            if x0-20<x<x1+20 and s0-20<s<s1+20:
                shape=shape.cut(cq.Solid.makeCylinder(20,b.THICKNESS+2,b.point(x,s,-1),b.normal()))
        add(name,shape,(max(x1-x0,s1-s0),min(x1-x0,s1-s0),b.THICKNESS),
            "2x6 lumber" if abs(min(x1-x0,s1-s0)-SEAM)<.01 else "2x4 lumber")
    for row,s in enumerate(b.CROSS_STATIONS,1):
        box(f"rear_cross_{row}",-b.HALF,b.HALF,s-b.THICKNESS/2,s+b.THICKNESS/2,
            rear-EDGE,rear,"2x4 rear crossmember; bolted angle interfaces")
        for label,x in (("seam_left",-48.),("seam_right",48.),
                        ("mid_left",mid_x(-1)),("mid_right",mid_x(1))):
            box(f"rib_{row}_{label}",x-b.THICKNESS/2,x+b.THICKNESS/2,
                s-EDGE/2,s+EDGE/2,b.THICKNESS,rear-EDGE,
                "2x4 lumber normal rib; front permanent screw and detachable rear angle; end-grain capacity unresolved")
            sign=-1 if x<0 else 1
            edge=x+sign*b.THICKNESS/2
            x0,x1=sorted((edge,edge+sign*80))
            vx0,vx1=sorted((edge,edge+sign*STEEL))
            n=rear-EDGE
            shape=b.block(x0,x1,s-EDGE/2,s+EDGE/2,n-STEEL,n).fuse(
                b.block(vx0,vx1,s-EDGE/2,s+EDGE/2,n-80,n-STEEL)).clean()
            add(f"angle_rib_{row}_{label}",shape,(80,80,EDGE),
                "STEEL custom 80x80x6 angle, 88.9 long; detachable rib/beam interface; capacity unresolved")
    for c in (connections(size) if drilled else ()):
        for i,name in enumerate(c.members):
            p=result[name]
            radius=5 if c.kind=="bolt" else (2.6 if i==0 else 1.6)
            cutter=cq.Solid.makeCylinder(radius,c.length+2,c.start-c.direction,c.direction)
            shape=p.shape.cut(cutter)
            if c.kind=="screw" and i==0:
                shape=shape.cut(c.components()[1])
            result[name]=replace(p,shape=shape)
    return tuple(result.values())
