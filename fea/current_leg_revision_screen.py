"""Fixed-resultant bolt-layout screen, not reanalysis or construction approval."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np

SOURCE = Path('fea/results/current-frame-response.json')
PROFILES = Path('docs/current-construction/stock-profiles.json')
LEG = np.array([0., -.26015745792854417, .9655662054381139])
RIM = np.array([0., .6427876096865427, .7660444431189752])
LN = np.array([0., LEG[2], -LEG[1]])
RN = np.array([0., RIM[2], -RIM[1]])


def loads():
    source = json.loads(SOURCE.read_text())
    if source.get('candidate') != 'no-shoes-development':
        raise ValueError('Require the current no-shoes-development candidate')
    if not source.get('cases') or not all(case.get('numerically_accepted') is True
                                          for case in source['cases']):
        raise ValueError('Require numerically accepted native cases')
    result = []
    for case in source['cases']:
        for side in ('left', 'right'):
            rows = [v for k, v in case['mechanical_connection_forces'].items()
                    if k.startswith('lumber_leg_bolt_' + side)]
            p = np.array([r['point'] for r in rows])
            c = p.mean(axis=0)
            f = np.array([r['force_on_second_xyz_n'] for r in rows])
            assert all(r['second'] == 'lumber_leg_' + side for r in rows)
            result.append((case['name'] + '/' + side, c, f.sum(axis=0),
                           np.cross(p-c, f).sum(axis=0)))
    return result


def capacity(forces, d):
    demand2 = np.sum(forces[...,1:]**2, axis=-1)
    bearing = []
    for grain in (RIM, LEG):
        cosine2 = np.clip((forces @ grain)**2/np.maximum(demand2,1e-20),0,1)
        perp = 6100*.5**1.45/math.sqrt(d)
        bearing.append(5600*perp/(5600*(1-cosine2)+perp*cosine2)*d)
    qm, qs = bearing
    lm = ls = 1.5
    my = 45000*d**3/6
    values = [qm*lm/5,qs*ls/5]
    for a,b,c,rd in ((1/(4*qs)+1/(4*qm),1.5,-qs*ls**2/4-qm*lm**2/4,4.5),
                     (1/(2*qs)+1/(4*qm),.75,-my-qm*lm**2/4,4),
                     (1/(4*qs)+1/(2*qm),.75,-qs*ls**2/4-my,4),
                     (1/(2*qs)+1/(2*qm),0,-2*my,4)):
        values.append(-2*c/(b+np.sqrt(b*b-4*a*c))/rd)
    return np.minimum.reduce(values)*4.4482216152605


def build():
    cases = loads()
    profiles = json.loads(PROFILES.read_text())
    rim_vertices = np.array(profiles['base_side_left']['vertices_world_mm'])
    leg_vertices = np.array(profiles['lumber_leg_left']['vertices_world_mm'])
    centre = cases[0][1]
    rim_front_offset = float(((rim_vertices-centre)@RN).max())
    original_top = float(((leg_vertices-centre)@LEG).max())
    assert abs(rim_front_offset-69.85)<1e-6
    assert abs(original_top-177.10543797035)<1e-6
    f = np.array([v[2] for v in cases])
    m = np.array([v[3] for v in cases])
    sine = np.linalg.norm(np.cross(LEG, RIM))
    results = []
    # Stock remains 38.1 mm thick. Rim front face stays fixed; deeper stock grows rearward.
    for ld, rd in ((139.7,139.7),(139.7,184.15),(184.15,184.15),(184.15,234.95),(234.95,234.95)):
      for nl, nr in ((3,2),(2,3),(4,2),(2,4),(3,3)):
       for d in (.375,.5,.625):
        best = None
        count = 0
        D = d*25.4
        row_min = 2.5*D if 38.1/D <= 2 else (5*38.1+10*D)/8
        pitch_min = math.ceil(max(4*D+2, (row_min+2)/sine)/5)*5
        for a in range(pitch_min,131,5):
         for b in range(pitch_min,131,5):
          if max((nl-1)*a*sine,(nr-1)*b*sine)>127: continue
          points = np.array([LEG*(i-(nl-1)/2)*a+RIM*(j-(nr-1)/2)*b for i in range(nl) for j in range(nr)])
          # Direction-dependent edge distances follow force on each joined member.
          for sl in range(-60,61,10):
           for sr in range(-40,61,10):
            shift = sl*LEG+sr*RIM
            q = points+shift
            margins = [float((ld/2-np.abs(q@LN)-1.5*D).min()),
                       float((rd/2-np.abs(q@RN+rd/2-rim_front_offset)-1.5*D).min()),
                       float((250-q@LEG-7*D).min())]
            if min(margins)<2: continue
            # Translate original resultant to candidate centroid; resolve planar elastic group.
            moment = m-np.cross(shift,f)
            polar = np.sum(points[:,1:]**2)
            forces = np.broadcast_to(f[:,None,:]/len(points),(len(cases),len(points),3)).copy()
            forces[:,:,1] -= moment[:,0,None]*points[None,:,2]/polar
            forces[:,:,2] += moment[:,0,None]*points[None,:,1]/polar
            # Axial fastener forces from out-of-plane moment require separate contact/prying analysis.
            for normal, depth, offset, sign in ((LN,ld,0,1),(RN,rd,rd/2-rim_front_offset,-1)):
                edge_coordinate = q@normal+offset
                demand_sign = forces@normal*sign
                positive = np.where(demand_sign>1e-9,4*D,1.5*D)
                negative = np.where(demand_sign< -1e-9,4*D,1.5*D)
                margins += [float((depth/2-edge_coordinate-positive).min()),
                            float((depth/2+edge_coordinate-negative).min())]
            if min(margins)<2: continue
            ratios = np.linalg.norm(forces[:,:,1:],axis=-1)/capacity(forces,d)
            ratio = float(ratios.max())
            subset150 = np.array(['250' not in case[0] for case in cases])
            ratio150 = float(ratios[subset150].max())
            count += 1
            if best is None or ratio < best['peak_lateral_ratio']:
             best = {'peak_lateral_ratio': float(ratio),'peak_150_comparison_ratio': ratio150,'required_top_extension_mm': max(original_top,float((q@LEG).max()+7*D+2)),'leg_pitch_mm': a,'rim_pitch_mm': b,
                         'shift_leg_mm': sl,'shift_rim_mm': sr,'minimum_directional_edge_end_margin_mm': min(margins),
                         'points_relative_original_centroid_mm': q.tolist()}
        if best:
            best['points_left_xyz_mm'] = (np.array(best['points_relative_original_centroid_mm'])+cases[0][1]).tolist()
        results.append({'leg_depth_mm': ld,'rim_depth_mm': rd,'rows_along_leg': nl,'rows_along_rim': nr,
                            'bolts_per_leg': nl*nr,'diameter_in': d,'geometry_passing_count': count,'best': best})
        if best: print(ld,rd,nl,nr,d,best['peak_lateral_ratio'],flush=True)
    return {'source_sha256': {str(SOURCE):hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                               __file__:hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               str(PROFILES):hashlib.sha256(PROFILES.read_bytes()).hexdigest()},
                'qualified_for_construction': False,'results': results,
                'assumptions': ['Fixed original full-frame resultants for all nine cases and both legs; no revised stiffness, footprint or added mass analysis.',
                'Same grain axes and square top extended up to 250 mm; widened rim keeps climbing-side face fixed.',
                'Smooth-shank 45 ksi bending yield, G=0.50 wood, CD=CM=Ct=Cdelta=1; no friction credit.',
                'Isotropic rigid planar bolt group only; Cg=1 matched member axial stiffness is approximate for unlike widths.',
                'Directional 4D loaded/1.5D unloaded edge screen, 7D top, full-value spacing and 127 mm cross-grain spread.',
                'No CAD collision, local shear/splitting/net-section, axial washer/prying, revised foot pressure or whole-frame qualification.']}


if __name__ == '__main__':
    Path('fea/results/current-leg-revision-screen.json').write_text(json.dumps(build(),indent=2)+'\n')
