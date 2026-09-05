"""Separate rim/leg layout candidates, NOT complete frames or FEA inputs.

Reuse the current datums and continuous leg profile. No global CAD constants
are mutated; the current default assembly and its exports remain unchanged.
"""
import math
from dataclasses import replace
from functools import cache
from pathlib import Path

import cadquery as cq

from . import box_frame as base
from .box_exports import write_csv
from .model import PANEL_THICKNESS_MM
from .raster import render

WIDTHS = {"2x10": 234.95, "2x12": 285.75}


def leg_normal(size):
    """Centre the upper leg across a rim starting at the climbing face."""
    return WIDTHS[size]/2-PANEL_THICKNESS_MM


def leg_bolts(size):
    delta=base.normal()*(leg_normal(size)-base.LEG_NORMAL)
    return tuple(replace(c,start=c.start+delta) for c in base.connections()
                 if c.name.startswith("analysis_leg_wall_bolt_"))


@cache
def parts(size):
    width=WIDTHS[size]
    rear=width-PANEL_THICKNESS_MM
    # Only the climbing skins are retained here. Carrying over old backing or
    # fastener holes would falsely imply that their new load paths are resolved.
    skins=[p for p in base.frame_parts(False)
           if p.name.startswith("main_") or p.name in ("kicker_left","kicker_right")]
    # Obtain hold/LED bores without inheriting the old panel screw schedule.
    for i,p in enumerate(skins):
        if p.name.startswith("main_"):
            row=int("upper" in p.name)
            col=int("right" in p.name)
            shape=base._main_panel_placement(base._panel_with_holes(
                base.HALF,base.HALF,base._v1_main_panel_holes(col,row)),
                (-.5+col)*base.HALF,row*base.HALF,base.V1_KICKER_HEIGHT_MM).val()
        else:
            col=int("right" in p.name)
            shape=base._kicker_panel_with_holes(base.HALF,base.V1_KICKER_HEIGHT_MM,
                base._v1_kicker_holes(col)).translate(
                    ((-.5+col)*base.HALF,-PANEL_THICKNESS_MM,0)).val()
        skins[i]=replace(p,shape=shape,description="reference climbing skin; attachment unresolved")
    result=skins
    for side,sign in (("left",-1),("right",1)):
        x0,x1=sorted((sign*base.HALF,sign*(base.HALF+base.THICKNESS)))
        result.append(base.Part(f"box_side_{side}",base.block(x0,x1,0,base.LENGTH,
            -PANEL_THICKNESS_MM,rear),(base.LENGTH,width,base.THICKNESS),
            f"{size} dry dressed lumber; grade/species unresolved",1))
        shape=base._leg(sign,leg_normal(size))
        bounds=shape.BoundingBox()
        result.append(base.Part(f"leg_{side}",shape,
            (bounds.zlen,bounds.ylen,base.THICKNESS),
            "two glued 19.05 mm plywood layers; changed profile; bounding blank"))
    # Top sits beyond the panel uphill edge, avoiding a panel/rim overlap and
    # allowing full stock width without ripping or reusing the old top batten.
    result.append(base.Part("box_top",base.block(-base.HALF-base.THICKNESS,base.HALF+base.THICKNESS,
        base.LENGTH,base.LENGTH+base.THICKNESS,-PANEL_THICKNESS_MM,rear),
        (base.LENGTH+2*base.THICKNESS,width,base.THICKNESS),
        f"{size} full-width top; corner connectors NOT yet designed",1))
    for c in leg_bolts(size):
        cutter=cq.Solid.makeCylinder(5,c.length+2,c.start-c.direction,c.direction)
        result=[replace(p,shape=p.shape.cut(cutter)) if p.name in c.members else p
                for p in result]
    return tuple(result)


def lower_angle(size):
    reference=base.point(0,1480,base.LEG_NORMAL)
    foot_y=reference.y+reference.z/math.tan(math.radians(70))
    bend=base.point(0,1480,leg_normal(size))
    return math.degrees(math.atan2(bend.z,foot_y-bend.y))


def export(directory=Path("exports/hybrid")):
    directory.mkdir(parents=True,exist_ok=True)
    rows=[]
    for size,width in WIDTHS.items():
        solids=[]
        assembly=cq.Assembly(name=f"{size}_INCOMPLETE_LAYOUT")
        for p in parts(size):
            assembly.add(p.shape,name=p.name)
            solids.append((p.shape,(45,53,60) if p.laminations==1 and
                           "reference" in p.description else (165,106,57)))
        for c in leg_bolts(size):
            shape=cq.Compound.makeCompound(c.components())
            assembly.add(shape,name=c.name)
            solids.append((shape,(190,65,65)))
        cq.exporters.export(assembly.toCompound(),str(directory/f"{size}_layout.step"))
        render(solids,directory/f"{size}_layout.png")
        rows.append((size,width,width/25.4,width-PANEL_THICKNESS_MM,
                     leg_normal(size),lower_angle(size),"INCOMPLETE layout; not a build/FEA model"))
        write_csv(directory,f"{size}_layout_blanks.csv",
            ("part","layers","length_mm","width_mm","total_thickness_mm",
             "length_in","width_in","total_thickness_in","note"),
            [(p.name,p.laminations,*p.blank,*[v/25.4 for v in p.blank],p.description)
             for p in parts(size)])
    write_csv(directory,"comparison.csv",
        ("candidate","rim_depth_mm","rim_depth_in","rear_N_mm","leg_bolt_N_mm",
         "lower_leg_angle_from_floor_deg","status"),rows)


if __name__ == "__main__":
    export()
