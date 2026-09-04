"""Box-frame geometry and single-source part/connection schedule, in mm.

Local X is across the panel, S uphill along it, N into its back.
Connection sizes are modelling assumptions, not strength approvals.
"""
import math
from dataclasses import dataclass
from functools import cache

import cadquery as cq

from .model import (
    ANGLE_FROM_VERTICAL_DEG,
    PANEL_THICKNESS_MM,
    V1_KICKER_HEIGHT_MM,
    V1_PANEL_SIZE_MM,
    V1_SUPPORT_THICKNESS_MM,
    V1_SUPPORT_WIDTH_MM,
    _kicker_panel_with_holes,
    _main_panel_placement,
    _panel_with_holes,
    _v1_kicker_holes,
    _v1_main_panel_holes,
    v1_support_side_point,
)
from .panel_grid import main_led_datums, main_tnut_datums

DEPTH = 304.8
THICKNESS = V1_SUPPORT_THICKNESS_MM
HALF = V1_PANEL_SIZE_MM
LENGTH = 2 * HALF
BATTEN_WIDTH = 70.0
SCREW_EDGE = 25.0
SCREW_LENGTH = 50.8
LEG_NORMAL = DEPTH - V1_SUPPORT_WIDTH_MM / 2
LEG_STATIONS = (1540.0, 1620.0, 1740.0, 1820.0)
CROSS_STATIONS = (400.0, HALF, 2000.0)


def point(x: float, s: float, n: float) -> cq.Vector:
    y, z = v1_support_side_point(s, n)
    return cq.Vector(x, y, z)


def normal() -> cq.Vector:
    a = math.radians(ANGLE_FROM_VERTICAL_DEG)
    return cq.Vector(0, -math.cos(a), math.sin(a))


def block(x0: float, x1: float, s0: float, s1: float, n0: float, n1: float) -> cq.Shape:
    """Box defined by board-local face coordinates."""
    return (cq.Workplane("XY").box(x1-x0, n1-n0, s1-s0)
            .rotate((0, 0, 0), (1, 0, 0), -ANGLE_FROM_VERTICAL_DEG)
            .translate(point((x0+x1)/2, (s0+s1)/2, (n0+n1)/2).toTuple()).val())


@dataclass(frozen=True)
class Part:
    name: str
    shape: cq.Shape
    blank: tuple[float, float, float]
    description: str
    laminations: int = 2


@dataclass(frozen=True)
class Connection:
    name: str
    start: cq.Vector
    direction: cq.Vector
    length: float
    diameter: float
    members: tuple[str, ...]
    kind: str = "screw"
    grip: float = 0.0

    def components(self) -> tuple[cq.Shape, ...]:
        d = self.direction.normalized()
        shaft = cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, d)
        if self.kind == "bolt":
            washer1 = cq.Solid.makeCylinder(12.7, 2, self.start, d)
            washer2 = cq.Solid.makeCylinder(12.7, 2, self.start+d*(2+self.grip), d)
            head = cq.Solid.makeCylinder(9, 6, self.start-d*6, d)
            nut = cq.Solid.makeCylinder(9, 9, self.start+d*(4+self.grip), d)
            return shaft, washer1, washer2, head, nut
        return shaft, cq.Solid.makeCone(5, self.diameter/2, 3, self.start, d)


def panel_screws() -> tuple[tuple[str, float, float], ...]:
    """24 perimeter screws per panel; slide along edges to clear hardware."""
    positions = []
    ticks = [40 + i*(HALF-80)/6 for i in range(7)]
    bores=[(x-HALF,s) for x,s in (*main_tnut_datums().values(),*main_led_datums().values())]
    for row, row_name in enumerate(("lower", "upper")):
        for col, side in enumerate(("left", "right")):
            name = f"main_{row_name}_{side}"
            perimeter = [(u,v,0) for v in (SCREW_EDGE,HALF-SCREW_EDGE) for u in ticks]
            perimeter += [(u,v,1) for u in (SCREW_EDGE,HALF-SCREW_EDGE) for v in ticks[1:-1]]
            for u,v,axis in perimeter:
                for delta in (0,*[d for offset in range(1,71) for d in (offset,-offset)]):
                    uu,vv=(u+delta,v) if axis==0 else (u,v+delta)
                    x,s=-HALF+col*HALF+uu,row*HALF+vv
                    if 25<=uu<=HALF-25 and 25<=vv<=HALF-25 and all(math.hypot(x-bx,s-bs)>=28 for bx,bs in bores):
                        positions.append((name,x,s))
                        break
                else:
                    raise ValueError(f"no hardware-clear screw location: {name} {u} {v}")
    return tuple(positions)


def _batten_for(x: float, s: float) -> str:
    if s < BATTEN_WIDTH:
        return "panel_edge_bottom"
    if s > LENGTH-BATTEN_WIDTH:
        return "panel_edge_top"
    if abs(s-HALF) < BATTEN_WIDTH:
        return "panel_seam_horizontal"
    side = "left" if x < 0 else "right"
    row = "lower" if s < HALF else "upper"
    if abs(x) > HALF-BATTEN_WIDTH:
        return f"panel_edge_{side}_{row}"
    return f"panel_seam_vertical_{row}"


@cache
def connections() -> tuple[Connection, ...]:
    result = []
    for index,(panel,x,s) in enumerate(panel_screws(),1):
        result.append(Connection(f"analysis_panel_screw_{index}",point(x,s,-PANEL_THICKNESS_MM),normal(),SCREW_LENGTH,4.826,(panel,_batten_for(x,s))))
    for side,sign in (("left",-1),("right",1)):
        for index,s in enumerate(LEG_STATIONS,1):
            result.append(Connection(f"analysis_leg_wall_bolt_{side}_{index}",point(sign*(HALF-2),s,LEG_NORMAL),cq.Vector(sign,0,0),95.25,9.525,(f"box_side_{side}",f"leg_{side}"),"bolt",2*THICKNESS))
        for row,s in enumerate(CROSS_STATIONS,1):
            cleat=f"cross_seat_{side}_{row}"
            for k,ds in enumerate((-12,12),1):
                result.append(Connection(f"analysis_seat_bolt_{side}_{row}_{k}",point(sign*(HALF+THICKNESS+2),s+2*ds,DEPTH-100),cq.Vector(-sign,0,0),95.25,9.525,(f"box_side_{side}",cleat),"bolt",2*THICKNESS))
                result.append(Connection(f"analysis_cross_screw_{side}_{row}_{k}",point(sign*(HALF-THICKNESS/2),s+ds,DEPTH),-normal(),88.9,4.826,(f"rear_cross_{row}",cleat)))
        for index,s in enumerate((150.,650.,1000.,1500.,1850.,2250.),1):
            row="lower" if s<HALF else "upper"
            result.append(Connection(f"analysis_edge_screw_{side}_{index}",point(sign*(HALF+THICKNESS),s,THICKNESS/2),cq.Vector(-sign,0,0),88.9,4.826,(f"box_side_{side}",f"panel_edge_{side}_{row}")))
        for index,s in enumerate((35.,HALF-35,HALF+35,LENGTH-55),1):
            batten=_batten_for(sign*(HALF-25),s)
            result.append(Connection(f"analysis_batten_end_{side}_{index}",point(sign*(HALF+THICKNESS),s,THICKNESS/2),cq.Vector(-sign,0,0),88.9,4.826,(f"box_side_{side}",batten)))
        for index,n in enumerate((100.,200.,280.),1):
            result.append(Connection(f"analysis_top_end_{side}_{index}",point(sign*(HALF+THICKNESS),LENGTH-THICKNESS/2,n),cq.Vector(-sign,0,0),88.9,4.826,(f"box_side_{side}","box_top")))
        # Broad-face splice joins each main wall to the floor-reaching cheek.
        for index,(s,n) in enumerate(((-60,130),(-60,240),(60,130),(60,240)),1):
            wall=f"kicker_cheek_{side}" if s<0 else f"box_side_{side}"
            result.append(Connection(f"analysis_cheek_splice_{side}_{index}",point(sign*(HALF-THICKNESS),s,n),cq.Vector(sign,0,0),63.5,4.826,(f"cheek_splice_{side}",wall)))
        for index,z in enumerate((12.,187.),1):
            result.append(Connection(f"analysis_kicker_end_{side}_{index}",cq.Vector(sign*(HALF+THICKNESS),-2*PANEL_THICKNESS_MM-THICKNESS/2,z),cq.Vector(-sign,0,0),88.9,4.826,(f"kicker_cheek_{side}",f"kicker_batten_{'bottom' if z<100 else 'top'}")))
    # Central seam battens connect to the rear beams through normal ribs;
    # opposed screws enter the broad faces of the laminated ribs.
    for row,s in enumerate(CROSS_STATIONS,1):
        batten="panel_seam_horizontal" if row==2 else f"panel_seam_vertical_{'lower' if row==1 else 'upper'}"
        for side,sign in (("left",-1),("right",1)):
            rib=f"seam_rib_{row}_{side}"
            result.append(Connection(f"analysis_rib_front_{row}_{side}",point(sign*48,s,0),normal(),88.9,4.826,(batten,rib)))
            result.append(Connection(f"analysis_rib_back_{row}_{side}",point(sign*48,s,DEPTH),-normal(),88.9,4.826,(f"rear_cross_{row}",rib)))
    for col,side in enumerate(("left","right")):
        for edge,z in (("bottom",25.),("top",200.)):
            for index in range(7):
                x=-HALF+col*HALF+25+index*(HALF-50)/6
                result.append(Connection(f"analysis_kicker_screw_{side}_{edge}_{index}",cq.Vector(x,-PANEL_THICKNESS_MM,z),cq.Vector(0,-1,0),50.8,4.826,(f"kicker_{side}",f"kicker_batten_{edge}")))
    return tuple(result)


def _leg(sign: int) -> cq.Shape:
    bend,upper=point(0,1480,LEG_NORMAL),point(0,1880,LEG_NORMAL)
    foot=cq.Vector(0,bend.y+bend.z/math.tan(math.radians(70)),0)
    x=sign*(HALF+1.5*THICKNESS)
    def member(start,end):
        delta=end-start
        return (cq.Workplane("XY").box(THICKNESS,V1_SUPPORT_WIDTH_MM,delta.Length,centered=(True,True,False))
                .rotate((0,0,0),(1,0,0),-math.degrees(math.atan2(delta.y,delta.z)))
                .translate((x,start.y,start.z)).val())
    extended=foot+(foot-bend).normalized()*120
    knee=cq.Solid.makeCylinder(V1_SUPPORT_WIDTH_MM/2,THICKNESS,cq.Vector(x-THICKNESS/2,bend.y,bend.z),cq.Vector(1,0,0))
    shape=member(bend,upper).fuse(member(bend,extended),knee).clean()
    floor=cq.Workplane("XY").box(10000,10000,10000,centered=(True,True,False)).val()
    return shape.intersect(floor).clean()


@cache
def frame_parts(drilled: bool = True) -> tuple[Part, ...]:
    parts=[]
    def add(name,shape,blank,description,laminations=2):
        parts.append(Part(name,shape,blank,description,laminations))
    for row,row_name in enumerate(("lower","upper")):
        for col,side in enumerate(("left","right")):
            panel=_main_panel_placement(_panel_with_holes(HALF,HALF,_v1_main_panel_holes(col,row) if drilled else []),(-.5+col)*HALF,row*HALF,V1_KICKER_HEIGHT_MM).val()
            add(f"main_{row_name}_{side}",panel,(HALF,HALF,PANEL_THICKNESS_MM),"climbing panel; 24 perimeter screws",1)
    for col,side in enumerate(("left","right")):
        panel=_kicker_panel_with_holes(HALF,V1_KICKER_HEIGHT_MM,_v1_kicker_holes(col) if drilled else []).translate(((-.5+col)*HALF,-PANEL_THICKNESS_MM,0)).val()
        add(f"kicker_{side}",panel,(HALF,V1_KICKER_HEIGHT_MM,PANEL_THICKNESS_MM),"kicker panel",1)
    for side,sign in (("left",-1),("right",1)):
        xa,xb=sorted((sign*HALF,sign*(HALF+THICKNESS)))
        add(f"box_side_{side}",block(xa,xb,0,LENGTH,-PANEL_THICKNESS_MM,DEPTH),(LENGTH,DEPTH+PANEL_THICKNESS_MM,THICKNESS),"laminated side wall; front flush with climbing face")
        leg=_leg(sign)
        b=leg.BoundingBox()
        add(f"leg_{side}",leg,(b.zlen,b.ylen,THICKNESS),"continuous laminated hockey-stick profile; bounding blank, profile governs")
        front,back=point(0,0,-PANEL_THICKNESS_MM),point(0,0,DEPTH)
        cheek=cq.Workplane("YZ").polyline([(front.y,0),(front.y,front.z),(back.y,back.z),(back.y,0)]).close().extrude(THICKNESS).translate((xa,0,0)).val()
        add(f"kicker_cheek_{side}",cheek,(back.z,abs(back.y-front.y),THICKNESS),"kicker-to-side-wall transition profile")
        sx0,sx1=sorted((sign*HALF,sign*(HALF-THICKNESS)))
        add(f"cheek_splice_{side}",block(sx0,sx1,-100,100,80,280),(200,200,THICKNESS),"broad-face wall/cheek splice; four screws")
    add("box_top",block(-HALF,HALF,LENGTH-THICKNESS,LENGTH,THICKNESS,DEPTH),(LENGTH,DEPTH-THICKNESS,THICKNESS),"laminated top closure; front batten completes flush rim")
    for label,z in (("bottom",0.),("top",175.)):
        shape=cq.Workplane("XY").box(LENGTH,THICKNESS,50,centered=(True,False,False)).translate((0,-2*PANEL_THICKNESS_MM-THICKNESS,z)).val()
        add(f"kicker_batten_{label}",shape,(LENGTH,50,THICKNESS),"kicker perimeter backing; screws from climbing face")
    bounds=[
        ("panel_edge_bottom",-HALF,HALF,0,BATTEN_WIDTH),
        ("panel_edge_top",-HALF,HALF,LENGTH-BATTEN_WIDTH,LENGTH),
        ("panel_seam_horizontal",-HALF,HALF,HALF-BATTEN_WIDTH,HALF+BATTEN_WIDTH),
    ]
    for row,s0,s1 in (("lower",BATTEN_WIDTH,HALF-BATTEN_WIDTH),("upper",HALF+BATTEN_WIDTH,LENGTH-BATTEN_WIDTH)):
        bounds += [(f"panel_edge_left_{row}",-HALF,-HALF+BATTEN_WIDTH,s0,s1),(f"panel_edge_right_{row}",HALF-BATTEN_WIDTH,HALF,s0,s1),(f"panel_seam_vertical_{row}",-BATTEN_WIDTH,BATTEN_WIDTH,s0,s1)]
    for name,x0,x1,s0,s1 in bounds:
        shape=block(x0,x1,s0,s1,0,THICKNESS)
        for x,s in ((*main_tnut_datums().values(),*main_led_datums().values()) if drilled else ()):
            x-=HALF
            if x0-20 < x < x1+20 and s0-20 < s < s1+20:
                shape=shape.cut(cq.Solid.makeCylinder(20,THICKNESS+2,point(x,s,-1),normal()))
        add(name,shape,(max(x1-x0,s1-s0),min(x1-x0,s1-s0),THICKNESS),"panel-bearing batten; 40 mm hardware relief bores; profile governs")
    for row,s in enumerate(CROSS_STATIONS,1):
        add(f"rear_cross_{row}",block(-HALF,HALF,s-THICKNESS/2,s+THICKNESS/2,DEPTH-60,DEPTH),(LENGTH,60,THICKNESS),"rear transverse member on bearing seats")
        for side,sign in (("left",-1),("right",1)):
            x0,x1=sorted((sign*HALF,sign*(HALF-THICKNESS)))
            add(f"cross_seat_{side}_{row}",block(x0,x1,s-55,s+55,DEPTH-140,DEPTH-60),(110,80,THICKNESS),"laminated bearing seat, through-bolted to wall")
        for side,sign in (("left",-1),("right",1)):
            x0,x1=sorted((sign*(48-THICKNESS/2),sign*(48+THICKNESS/2)))
            add(f"seam_rib_{row}_{side}",block(x0,x1,s-THICKNESS/2,s+THICKNESS/2,THICKNESS,DEPTH-60),(DEPTH-60-THICKNESS,THICKNESS,THICKNESS),"normal rib joining panel seam support to rear cross member")
    by_name={p.name:p for p in parts}
    for c in (connections() if drilled else ()):
        d=c.direction.normalized()
        for i,name in enumerate(c.members):
            p=by_name[name]
            radius=5 if c.kind=="bolt" else (2.6 if i==0 else 1.6)
            cutter=cq.Solid.makeCylinder(radius,c.length+2,c.start-d,d)
            shape=p.shape.cut(cutter)
            if c.kind=="screw" and i==0:
                shape=shape.cut(c.components()[1])
            by_name[name]=Part(p.name,shape,p.blank,p.description,p.laminations)
    return tuple(by_name.values())


def build_box_frame() -> cq.Assembly:
    assembly=cq.Assembly(name="mini_moonboard_v1_box_frame")
    for p in frame_parts():
        assembly.add(p.shape,name=p.name,color=cq.Color("black" if p.name.startswith("main_") else "saddlebrown"))
    return assembly
