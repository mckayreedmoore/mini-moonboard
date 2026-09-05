"""Rotated-rear 2x8 candidate; nominal geometry, NOT construction approval.

Reuse the complete hybrid backing rather than changing the frozen timber-only
2x8 reference. Custom angle envelopes still need rated connection design.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import hybrid
from . import hybrid_frame as h

REAR=hybrid.WIDTHS['2x8']-18
BEAM_DEPTH=b.THICKNESS
BEAM_WIDTH=h.EDGE


@cache
def connections():
    result=[]
    tangent=(b.point(0,1,0)-b.point(0,0,0)).normalized()
    for c in h.connections('2x8'):
        if c.name.startswith('cheek_splice_'):
            # Old deep-rim stations nearly coincide at this reduced depth.
            index=int(c.name.rsplit('_',1)[1])
            n=65. if index%2 else 105.
            sign=-1 if '_left_' in c.name else 1
            c=replace(c,start=b.point(sign*(b.HALF-b.THICKNESS),-50 if index<=2 else 50,n))
        elif c.name.startswith(('angle_left_cross_', 'angle_right_cross_')):
            # Crossmembers are wider uphill; angles move outside that face.
            c=replace(c,start=c.start+tangent*((BEAM_WIDTH-b.THICKNESS)/2))
            if '_beam_' in c.name:
                sign=-1 if '_left_' in c.name else 1
                row=int(c.name.split('_')[3])
                j=int(c.name.rsplit('_',1)[1])
                c=replace(c,start=b.point(sign*(b.HALF-(40 if j==1 else 75)),
                          b.CROSS_STATIONS[row-1]-BEAM_WIDTH/2-2,REAR-BEAM_DEPTH/2),
                          length=114.3,grip=BEAM_WIDTH+h.STEEL)
        elif c.name.startswith('angle_rib_'):
            if '_rib_' in c.name and c.name.rsplit('_',2)[1]=='rib':
                c=replace(c,start=c.start+b.normal()*(h.EDGE-BEAM_DEPTH))
            else:
                c=replace(c,length=63.5,grip=BEAM_DEPTH+h.STEEL)
        result.append(c)
    return tuple(result)


@cache
def parts(drilled=True):
    result={p.name:p for p in h.parts('2x8',False)}
    def put(name,shape,blank,note):
        result[name]=b.Part(name,shape,blank,note)
    for row,s in enumerate(b.CROSS_STATIONS,1):
        put(f'rear_cross_{row}',b.block(-b.HALF,b.HALF,s-BEAM_WIDTH/2,s+BEAM_WIDTH/2,
            REAR-BEAM_DEPTH,REAR),(2*b.HALF,BEAM_WIDTH,BEAM_DEPTH),
            '2x4 rear crossmember rotated broad face parallel to panel; unrated bolted angles')
        for side,sign in h.SIDES:
            station=s+BEAM_WIDTH/2
            x0,x1=sorted((sign*b.HALF,sign*(b.HALF-100)))
            sx0,sx1=sorted((sign*b.HALF,sign*(b.HALF-h.STEEL)))
            shape=b.block(x0,x1,station,station+h.STEEL,REAR-h.EDGE,REAR).fuse(
                b.block(sx0,sx1,station+h.STEEL,station+100,REAR-h.EDGE,REAR)).clean()
            put(f'angle_{side}_cross_{row}',shape,(100,100,h.EDGE),
                'STEEL custom 100x100x6 angle, 88.9 long; nominal, capacity unresolved')
        for label,x in (('seam_left',-48.),('seam_right',48.),
                        ('mid_left',h.mid_x(-1)),('mid_right',h.mid_x(1))):
            put(f'rib_{row}_{label}',b.block(x-b.THICKNESS/2,x+b.THICKNESS/2,
                s-h.EDGE/2,s+h.EDGE/2,b.THICKNESS,REAR-BEAM_DEPTH),
                (REAR-BEAM_DEPTH-b.THICKNESS,h.EDGE,b.THICKNESS),
                '2x4 normal rib; permanent front end-grain screw and detachable rear angle; capacity unresolved')
            name=f'angle_rib_{row}_{label}'
            p=result[name]
            result[name]=replace(p,shape=p.shape.translate(b.normal()*(h.EDGE-BEAM_DEPTH)))
    # Recreate the backing reliefs/hold holes before connection drilling. The
    # baseline unbored model intentionally omits both for bulk stiffness FEA.
    if drilled:
        bored={p.name:p for p in h.parts('2x8',True)}
        # Reuse only parts unaffected by relocated holes. Baseline hardware is
        # not valid for 2x8; never reuse its drilled rims, rear joints or cheeks.
        for name in result:
            if name.startswith(('main_', 'kicker_batten_', 'panel_', 'mid_')) or name in ('kicker_left','kicker_right'):
                result[name]=bored[name]
        for c in connections():
            for i,name in enumerate(c.members):
                p=result[name]
                radius=5 if c.kind=='bolt' else (2.6 if i==0 else 1.6)
                shape=p.shape.cut(cq.Solid.makeCylinder(radius,c.length+2,c.start-c.direction,c.direction))
                if c.kind=='screw' and i==0:
                    shape=shape.cut(c.components()[1])
                result[name]=replace(p,shape=shape)
    return tuple(result.values())
