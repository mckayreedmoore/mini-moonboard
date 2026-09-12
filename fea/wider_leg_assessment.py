"""Source-bound conditional assessment of the catalog six-bolt wider-leg joint.

Full-foot pressure sensitivity is separate from the middle-third assumption.
No result makes the contact/prying assumptions a validated installed restraint.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path

from fea.leg_attachment_check import LEG, RIM
from fea.leg_bolt_pattern_search import cross_row_minimum, group_factor, lateral
from fea.leg_completion_assessment import foot_joint_moment
from fea.leg_only_load_check import axial_support_force
from fea.round_structural_global_envelope import locations
from fea.wider_leg_wood_checks import dot, joint_local_checks, member_net_check
from mini_moonboard import wider_leg_hardware as hw

CAD = Path('docs/wider-leg-review/review.json')


def six_group_factor():
    """Six-fastener row bound, original smaller EA and maximum84 mm pitch."""
    ea=1600000*1.5*5.5
    u=1+180000*.5**1.5*(84/25.4)/ea
    m=1/(u+math.sqrt(u*u-1))
    n=6
    return m*(1-m**(2*n))/(n*((1+m**n)*(1+m)-1+m**(2*n)))*2/(1-m)


def planar_forces(points, compression, moment):
    top=[sum(p[k] for p in points)/len(points) for k in range(3)]
    polar=sum((p[1]-top[1])**2+(p[2]-top[2])**2 for p in points)
    return [(0.,compression*LEG[1]/len(points)-moment*(p[2]-top[2])/polar,
             compression*LEG[2]/len(points)+moment*(p[1]-top[1])/polar) for p in points]


def placement(cad, forces):
    """NDS directional edges measured along actual stock boundary rays."""
    d=12.7
    cross=math.sqrt(1-dot(LEG,RIM)**2)
    margins=[66-4*d,84-4*d,66*cross-cross_row_minimum(d),
             84*cross-cross_row_minimum(d),127-2*66*cross]
    witnesses=[]
    for row in cad['raw_edge_distances']:
        if not row['connection'].startswith('lumber_leg_bolt_left_'):
            continue
        index=int(row['connection'].rsplit('_',1)[1])-1
        leg=row['member'].startswith('lumber_leg')
        grain=LEG if leg else RIM
        # CAD rim depth is inward N, opposite the conventional sagittal normal.
        normal=(0.,grain[2],-grain[1])
        force=[(-1 if leg else 1)*v for v in forces[index]]
        depth_force=dot(force,normal)*(1 if leg else -1)
        a=row['depth_positive_mm']-(4 if depth_force>1e-9 else 1.5)*d
        b=row['depth_negative_mm']-(4 if depth_force< -1e-9 else 1.5)*d
        ends=min(row['grain_positive_mm'],row['grain_negative_mm'])-7*d
        margins.extend((a,b,ends))
        witnesses.append({'member':row['member'],'bolt':index+1,
                          'positive_depth_force_n':depth_force,
                          'minimum_margin_mm':min(a,b,ends)})
    return {'minimum_margin_mm':min(margins),'passes':min(margins)>=-1e-8,
            'witnesses':witnesses}


def evaluate(cad, points, context, compression, foot, *, permanent=False):
    leg=context['leg']
    top=context['top']
    moment=foot_joint_moment(compression_n=compression,top=top,foot=foot,
        leg_mass_kg=leg['mass_kg'],leg_centre=leg['centre_xyz_mm'])
    forces=planar_forces(points,compression,moment)
    lat=lateral(forces,.5,84)
    cg=six_group_factor()
    for bolt in lat['bolts']:
        bolt['reference_n']*=cg/group_factor(.5,84)*(.9 if permanent else 1.)
        bolt['ratio']=bolt['demand_n']/bolt['reference_n']
    lat['group_factor']=cg
    lat['peak_ratio']=max(b['ratio'] for b in lat['bolts'])
    couple=hw.axial_couple_screen(points,[0.,compression*LEG[1],compression*LEG[2]])
    hardware=[]
    for bolt,tension in zip(lat['bolts'],couple['bolt_tension_envelope_n'],strict=True):
        combined=hw.bolt_combined_screen(bolt['demand_n'],tension)
        combined['conservative_lateral_plus_axial_ratio']=bolt['ratio']+combined['axial_stress_mpa']/(92000*hw.PSI/2)
        hardware.append({'tension_n':tension,'plate':hw.plate_screen(tension),
                         'washer':hw.washer_screen(tension),'steel':combined})
    wood={}
    for name,grain,centre,ends,sign in (
        ('leg',LEG,context['leg_centre'],context['leg_ends'],-1),
        ('rim',RIM,context['rim_centre'],context['rim_ends'],1)):
        wood[name]=joint_local_checks(points,[[sign*v for v in f] for f in forces],
            grain=grain,centre=centre,end_stations_mm=ends,kmod=.6 if permanent else .8,
            additional_section_boxes=context['rim_notches'] if name=='rim' else (),
            duration_factor=.9 if permanent else 1.)
    transport_moment=compression*abs(context['joint_depth_offset_mm'])
    member=member_net_check(compression,abs(moment)+transport_moment,holes_sq_d=context['holes'],
        effective_length_mm=context['support_span_mm'],mass_kg=leg['mass_kg'],axis_vertical_cosine=LEG[2],
        duration_factor=.9 if permanent else 1.)
    geo=placement(cad,forces)
    metrics={'lateral':lat['peak_ratio'],'leg_member':member['peak_interaction'],
        'leg_parallel':wood['leg']['parallel_peak_ratio'],'rim_parallel':wood['rim']['parallel_peak_ratio'],
        'leg_splitting':wood['leg']['splitting_peak_ratio'],'rim_splitting':wood['rim']['splitting_peak_ratio'],
        'wood_plate_bearing':max(h['plate']['wood_bearing_ratio'] for h in hardware),
        'plate_plastic_bending':max(h['plate']['plate_plastic_bending_ratio'] for h in hardware),
        'washer_bending':max(h['washer']['single_washer_elastic_bending_ratio'] for h in hardware),
        'steel_direct':max(h['steel']['steel_direct_interaction_ratio'] for h in hardware),
        'conservative_lateral_plus_axial':max(h['steel']['conservative_lateral_plus_axial_ratio'] for h in hardware)}
    return {'compression_n':compression,'joint_moment_nmm':moment,'foot_xyz_mm':foot,
            'member_moment_transport_allowance_nmm':transport_moment,
            'member_moment_input_nmm':abs(moment)+transport_moment,
            'NDS_duration_factor':.9 if permanent else 1.,
            'permanent_only':permanent,'metrics':metrics,'placement':geo,
            'lateral':lat,'wood':wood,'member':member,'hardware':hardware,
            'couple':couple,'necessary_checks_pass':max(metrics.values())<=1 and geo['passes'] and member['meets_member_criteria']}


def build():
    from mini_moonboard import wider_leg_frame as model
    cad=json.loads(CAD.read_text())
    for path,expected in cad['source_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:
            raise ValueError('CAD evidence stale: '+path)
    points=[[0.,r['world_y_mm'],r['world_z_mm']] for r in cad['drilling']
            if r['member']=='lumber_leg_left']
    top=[sum(p[k] for p in points)/6 for k in range(3)]
    centre,_,_,_,_=model.axes()
    leg_centre=list(centre.toTuple())
    origin=model.previous.b.point(0,0,0)
    rim_centre=list((origin+model.previous.b.normal()*92.075).toTuple())
    leg=next(r for r in cad['mass_inventory'] if r['name']=='lumber_leg_left')
    footprint=cad['foot_polygons_xyz_mm']['lumber_leg_left']
    foot_centre=[sum(p[k] for p in footprint)/len(footprint) for k in range(3)]
    support_span=math.hypot(top[1]-foot_centre[1],top[2])
    holes=[(dot([p[i]-leg_centre[i] for i in range(3)],LEG),
            dot([p[i]-leg_centre[i] for i in range(3)],(0.,LEG[2],-LEG[1])),14.2875) for p in points]
    # All row pitches are smaller than either actual ray end distance. These
    # enclosing stock limits therefore do not govern Appendix E row capacity.
    rim_notches=[]
    for cut in cad['local_rim_cuts']:
        if 'base_side_left' not in cut['members'] or cut['connection'].startswith('lumber_leg_bolt_'):
            continue
        slo,shi=cut['grain_extent_mm']
        nlo,nhi=cut['depth_extent_inside_rim_mm']
        # Replace the shallow cylindrical opening by a full-width square notch;
        # extend grain width to its larger depth, conservatively.
        rim_notches.append(((slo+shi)/2,92.075-(nlo+nhi)/2,nhi-nlo))
    context={'top':top,'leg':leg,'leg_centre':leg_centre,'rim_centre':rim_centre,
             'leg_ends':[-1663.9599640771353,200.],
             'rim_ends':[-157.18998601159768,2438.4],
             'support_span_mm':support_span,'holes':holes,'rim_notches':rim_notches,
             'joint_depth_offset_mm':dot([top[i]-leg_centre[i] for i in range(3)],(0.,LEG[2],-LEG[1]))}
    hold_points=list(locations(model))
    equipment_y=max(p[1]+offset*n[1] for _,p,n in hold_points for offset in (0.,100.))
    mass=cad['state']['mass_kg']+25.
    dead_y=(cad['state']['mass_kg']*cad['state']['centre_xyz_mm'][1]+25*equipment_y)/mass
    half=(max(p[1] for p in footprint)-min(p[1] for p in footprint))/2
    groups={}
    for scope,mult in (('middle_third',1/3),('whole_foot',1.)):
        rows=[]
        # All hold positions, front resultants and applied horizontal/offset
        # endpoint choices are checked; do not retain only the maximum axial case.
        for foot_sign in (-1,1):
            foot=[foot_centre[0],foot_centre[1]+foot_sign*half*mult,0.]
            candidates=[]
            for name,p,n in hold_points:
                for front,offset,horizontal in itertools.product((-270.95,-36.),(0.,100.),(0.,300.)):
                    compression=axial_support_force(downward_n=250*2*4.4482216152605,
                        horizontal_n=horizontal,load_y=p[1]+offset*n[1],load_z=p[2]+offset*n[2],
                        dead_n=mass*9.80665,dead_y=dead_y,front_y=front,rear_y=foot[1],vertical_cosine=LEG[2])
                    candidates.append((compression,name,front,offset,horizontal))
            # At fixed foot geometry each force component is affine in axial
            # force. Retain unique forces (hold columns share the same Y/Z).
            unique={round(c[0],10):c for c in candidates}
            for compression,name,front,offset,horizontal in unique.values():
                row=evaluate(cad,points,context,compression,foot)
                row['load']={'hold':name,'front_y_mm':front,'offset_mm':offset,'horizontal_n':horizontal}
                rows.append(row)
            for front in (-270.95,-36.):
                compression=axial_support_force(downward_n=0.,horizontal_n=0.,load_y=0.,load_z=0.,
                    dead_n=mass*9.80665,dead_y=dead_y,front_y=front,rear_y=foot[1],vertical_cosine=LEG[2])
                row=evaluate(cad,points,context,compression,foot,permanent=True)
                row['load']={'hold':None,'front_y_mm':front,'offset_mm':0.,'horizontal_n':0.}
                rows.append(row)
        peaks={k:max(r['metrics'][k] for r in rows) for k in rows[0]['metrics']}
        governing_indices=sorted({max(range(len(rows)),key=lambda i:rows[i]['metrics'][k]) for k in peaks}
                                |{min(range(len(rows)),key=lambda i:rows[i]['placement']['minimum_margin_mm'])})
        groups[scope]={'evaluated_unique_load_cases':len(rows),'hold_positions_scanned':len(hold_points),
                      'peak_metrics':peaks,'minimum_placement_margin_mm':min(r['placement']['minimum_margin_mm'] for r in rows),
                      'necessary_checks_pass':all(r['necessary_checks_pass'] for r in rows),
                      'governing_cases':[rows[i] for i in governing_indices]}
    sources=[Path(__file__),CAD,Path('fea/wider_leg_wood_checks.py'),Path('fea/leg_bolt_pattern_search.py'),
             Path('fea/dowel_yield.py'),Path('fea/leg_completion_assessment.py'),Path('fea/leg_only_load_check.py'),
             Path('fea/round_structural_global_envelope.py'),Path('fea/reinforced_timber_resistance.py'),
             Path('mini_moonboard/wider_leg_hardware.py'),Path('mini_moonboard/wider_leg_frame.py')]
    return {'candidate':model.KEY,'qualified_for_construction':False,
            'assumptions':{'climber_lb':250,'vertical_multiplier':2,'horizontal_force_n':300,
                'equipment_allowance_kg':25,'equipment_y_mm':equipment_y,
                'actual_assembly_mass_kg':cad['state']['mass_kg'],'combined_mass_kg':mass,
                'entire_rear_load_assigned_to_one_leg':True,'no_sliding_assumed':True,
                'prying_amplification_assumed':2.,'plate_minimum_yield_psi_assumed':33000,
                'front_resultant_bounds_mm':[-270.95,-36.],
                'front_bounds_basis':'Unchanged prior front bearing footprint; widened members do not change its Y extrema'},
            'joint_depth_offset_mm':context['joint_depth_offset_mm'],
            'local_rim_notch_bounds_sq_d_mm':rim_notches,'actual_supported_span_mm':support_span,'joint_centroid_xyz_mm':top,
            'foot_polygon_xyz_mm':footprint,'hardware_dimensional_window':hw.dimensional_window(),
            'pressure_scopes':groups,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            'limits':['Middle-third pressure is an explicit assessment assumption, not an established installed bound.',
                'Whole-foot pressure endpoints bound the planar pressure-resultant position; axial load-direction and prying assumptions remain.',
                'Twofold prying is assumed, not a solved contact bound. Plate33ksi and hardware receipt dimensions require confirmation.',
                'Local rim net/tear-out/splitting checks do not constitute a whole-frame rating.',
                'No panel, T-nut or floor-friction qualification is introduced.']}


if __name__=='__main__':
    report=build()
    path=Path('fea/results/wider-leg-assessment.json')
    path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:{'passes':v['necessary_checks_pass'],'metrics':v['peak_metrics'],
                         'placement_margin_mm':v['minimum_placement_margin_mm']}
                      for k,v in report['pressure_scopes'].items()},indent=2))
