"""Preliminary six-bolt, single-2x8 leg/rim search; not a construction release.

Uses the documented full-contact assumptions, added wood mass and wider foot.
Final wood net sections, splitting, prying and hardware fit are not established.
"""
import hashlib
import json
import math
from pathlib import Path

from fea.leg_attachment_check import LEG, RIM
from fea.leg_bolt_pattern_search import context, group_factor, lateral
from fea.leg_completion_assessment import foot_joint_moment
from fea.wider_leg_pattern_screen import geometry, load_cases


def build():
    source,c,leg=context()
    depth=184.15;d=.5; best=None
    loads=load_cases(depth,source,leg,depth)
    for a in range(54,77,2):
     for b in range(54,85,2):
      for sl in range(-28,1,4):
       for sr in range(-8,9,4):
        points=[[c[k]+(sl+s*a)*LEG[k]+(sr+t*b/2)*RIM[k] for k in range(3)] for s in(-1,0,1) for t in(-1,1)]
        top=[sum(p[k] for p in points)/6 for k in range(3)]
        polar=sum((p[1]-top[1])**2+(p[2]-top[2])**2 for p in points)
        fs=[];ms=[]
        for load in loads:
         moment=foot_joint_moment(compression_n=load['compression_n'],top=top,foot=load['foot'],leg_mass_kg=leg['mass_kg']*depth/139.7,leg_centre=leg['centre_xyz_mm'])
         ms.append(moment)
         fs.append([(0,load['compression_n']*LEG[1]/6-moment*(p[2]-top[2])/polar,load['compression_n']*LEG[2]/6+moment*(p[1]-top[1])/polar) for p in points])
        margin=min(geometry(points,c,d*25.4,a,b,fs,depth,depth),127-2*a*math.sqrt(1-sum(x*y for x,y in zip(LEG,RIM))**2))
        if margin<2:continue
        ea=1600000*1.5*5.5;gamma=180000*d**1.5;u=1+gamma*(max(a,b)/25.4)/ea;m=1/(u+math.sqrt(u*u-1));n=6
        cg=m*(1-m**(2*n))/(n*((1+m**n)*(1+m)-1+m**(2*n)))*2/(1-m)
        ratio=max(lateral(f,d,max(a,b))['peak_ratio']*group_factor(d,max(a,b))/cg for f in fs)
        if best is None or ratio<best['ratio']:best={'ratio':ratio,'a':a,'b':b,'shift_leg':sl,'shift_rim':sr,'margin':margin,'moments':ms,'cg':cg,'points':points,'forces':fs,'loads':loads}
    paths = [Path(__file__), Path('fea/wider_leg_pattern_screen.py'),
             Path('fea/leg_bolt_pattern_search.py'), Path('fea/leg_completion_assessment.py'),
             Path('fea/dowel_yield.py'), Path('fea/results/leg-completion-assessment-v2.json')]
    return {'leg_depth_mm':depth,'rim_depth_mm':depth,'bolt_diameter_in':d,
            'bolts_per_leg':6,'best':best,'qualified_for_construction':False,
            'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'limits':['Lateral capacity and placement screen only; material/bearing assumptions follow the preceding search.',
                      'Larger wood is centered on the existing axes; actual CAD installation and other connections not revised.',
                      'Full-contact pressure range grows with leg width; extra wood mass included approximately at previous centers of gravity.',
                      'Smaller original group stiffness and six-fastener/max-pitch factor retained conservatively.',
                      'Fresh stock and unthreaded shank through both members assumed; final washer and bolt stack not specified.',
                      'Member net sections, splitting, prying and final hardware/collision checks remain outstanding.']}


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=build()
    with args.output.open('x') as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps({'ratio':report['best']['ratio'],'placement_margin_mm':report['best']['margin']}))
