"""Conditional affine normal traction on reviewed rectangular-minus-bore sections."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
PINS = {
    'current-corner-local-wood-screen-attempt01/section-screen.json':
        '22209a82b0bda6dfc5c140ccc4e481717e0e7c71d30a5827271c81ac71070564',
    'current-corner-conditional-section-demands-attempt01/section-demands.json':
        'bb275cf2748f3aae7fd2d0f67ce5a37c67bcfffd32e413d79f1270015e8b5e6f',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def properties(width, depth, voids):
    # Coordinates relative to gross centroid. Voids are disjoint and internal.
    area = width*depth
    sx = sy = 0.0
    sxx, syy, sxy = area*width**2/12, area*depth**2/12, 0.0
    for a,x,y,own_xx,own_yy in voids:
        area -= a
        sx -= a*x
        sy -= a*y
        sxx -= own_xx+a*x*x
        syy -= own_yy+a*y*y
        sxy -= a*x*y
    cx, cy = sx/area, sy/area
    xx, yy, xy = sxx-area*cx*cx, syy-area*cy*cy, sxy-area*cx*cy
    assert area > 0 and xx > 0 and yy > 0 and xx*yy-xy*xy > 0
    return {'area_mm2':area, 'centroid_offset_from_gross_XY_mm':[cx,cy],
            'integral_x2_about_net_centroid_mm4':xx,
            'integral_y2_about_net_centroid_mm4':yy,
            'integral_xy_about_net_centroid_mm4':xy}


def normal_field(section, force, moment):
    cx,cy = section['centroid_offset_from_gross_XY_mm']
    # Transport the source datum moment to the net centroid.
    mx, my, mz = moment
    fx,fy,n = force
    mx -= cy*n
    my += cx*n
    mz -= cx*fy-cy*fx
    xx = section['integral_x2_about_net_centroid_mm4']
    yy = section['integral_y2_about_net_centroid_mm4']
    xy = section['integral_xy_about_net_centroid_mm4']
    determinant = xx*yy-xy*xy
    # sigma=N/A + a(x-cx)+b(y-cy), so (-My,Mx)=J(a,b).
    a = (-my*yy-xy*mx)/determinant
    b = (xx*mx+xy*my)/determinant
    assert abs(xx*a+xy*b+my) < 1e-8
    assert abs(xy*a+yy*b-mx) < 1e-8
    return n/section['area_mm2'],a,b,[mx,my,mz]


def fixtures():
    section = properties(20,40,[])
    mean,a,b,m = normal_field(section,[0,0,80],[1600,-800,0])
    assert mean == .1
    assert math.isclose(a,800/(40*20**3/12))
    assert math.isclose(b,1600/(20*40**3/12))
    off = properties(20,40,[(40,0,10,40*20**2/12,40*2**2/12)])
    cx,cy=off['centroid_offset_from_gross_XY_mm']
    mean,a,b,m = normal_field(off,[0,0,100],[100*cy,-100*cx,0])
    assert abs(a)<1e-14 and abs(b)<1e-14
    assert math.isclose(mean,100/760)
    return {'status':'PASS_RECTANGULAR_BENDING_AND_ECCENTRIC_NET_CENTROID_ORACLES'}


def produce():
    pins = {}
    sources = {}
    for name,pin in PINS.items():
        path=BASE/name
        assert sha(path)==pin,name
        sources[name]=json.loads(path.read_text())
        pins[str(path.relative_to(ROOT))]=pin
    geometry=sources['current-corner-local-wood-screen-attempt01/section-screen.json']
    demands=sources['current-corner-conditional-section-demands-attempt01/section-demands.json']
    for name,pin in demands['source_hashes'].items():
        assert sha(ROOT/name)==pin,name
        pins[name]=pin
    for auth in demands['case_authentication']:
        assert auth['usable_for_conditional_corner_demands'] and not auth['joint_acceptance']
    g=geometry['modeled_geometry_inputs']
    diameter=g['modeled_bore_diameter_mm_from_profile_void_intervals']
    radius=diameter/2
    rows=[]
    sections={}
    models={auth['case_id']:json.loads((ROOT/auth['source_paths']['model']).read_text())
            for auth in demands['case_authentication']}
    reports={auth['case_id']:json.loads((ROOT/auth['source_paths']['report']).read_text())
             for auth in demands['case_authentication']}
    for row in demands['per_increment_body_sections']:
        member=row['body']
        auth=next(r for r in demands['case_authentication'] if r['case_id']==row['case_id'])
        model=models[row['case_id']]
        record=model['body_geometry'][member]['geometry_record']
        assert record['axis']==[0.0,0.0,1.0]
        assert record['section_u']==[1.0,0.0,0.0] and record['section_v']==[0.0,1.0,0.0]
        origin=record['start']
        width,depth = g['spine_XY_envelope_mm' if member.endswith('spine') else 'inner_block_XY_envelope_mm']
        assert abs(width-record['gross_width_mm'])<1e-8 and abs(depth-record['gross_depth_mm'])<1e-8
        for station in row['section_stations']:
            assert station['cut_datum_global_xyz_mm'][:2]==origin[:2]
            report=reports[row['case_id']]
            bolt=next(b for b in report['increments'][-1]['primary_physical_bolt_groups'][station['group_id']]['bolts'] if b['axis_id']==station['axis_id'])
            strip_y=bolt['axis_datum_global_xyz_mm'][1]-origin[1]
            assert abs(strip_y)+radius<depth/2
            voids=[(width*diameter,0,strip_y,width*diameter*width**2/12,width*diameter*diameter**2/12)]
            if not member.endswith('spine'):
                for gx,gy in g['BG045_inner_block_bore_centers_xy_mm']:
                    x,y=gx-origin[0],gy-origin[1]
                    assert abs(x)+radius<width/2 and abs(y)+radius<depth/2
                    assert abs(y-strip_y)>diameter
                    voids.append((math.pi*radius**2,x,y,math.pi*radius**4/4,math.pi*radius**4/4))
            section=properties(width,depth,voids)
            applicable=next(item for item in geometry['candidate_net_section_inputs']
                if item['member_id']==member and station['axis_id'] in item['applies_to_axes'])
            assert abs(section['area_mm2']-applicable['candidate_net_area_mm2'])<1e-7
            old_context_area=station['nominal_net_section_area_mm2_from_pinned_geometry_screen']
            area_correction=abs(section['area_mm2']-old_context_area)>1e-7
            if area_correction:
                assert member=='knee_outer_left_inner_frame_block'
                assert math.isclose(old_context_area-section['area_mm2'],width*diameter,abs_tol=1e-7)
            sections[member+'/'+station['axis_id']]=section
            for side in ['just_below','just_above']:
                cut=station['one_sided_cut_results'][side]
                action=cut['lower_segment_material_action']
                mean,a,b,m=normal_field(section,action['force_xyz_n'],action['moment_xyz_nmm'])
                cx,cy=section['centroid_offset_from_gross_XY_mm']
                corners=[mean+a*(x-cx)+b*(y-cy) for x in [-width/2,width/2] for y in [-depth/2,depth/2]]
                rows.append({'case':row['case_id'],'load_factor':row['load_factor'],
                    'member':member,'axis':station['axis_id'],'cut_side':side,
                    'source_context_area_mm2':old_context_area,
                    'applicable_net_section_area_mm2':section['area_mm2'],
                    'source_context_area_corrected_in_this_packet':area_correction,
                    'source_signed_force_XYZ_N':action['force_xyz_n'],
                    'moment_about_net_centroid_XYZ_Nmm':m,
                    'uniform_normal_traction_MPa':mean,
                    'affine_gradient_XY_MPa_per_mm':[a,b],
                    'outer_corner_normal_tractions_MPa':corners,
                    'nominal_affine_min_max_normal_traction_MPa':[min(corners),max(corners)]})
    assert len(rows)==252 and len(sections)==6
    pins[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    return {'schema':'current_corner_net_section_affine_normal_traction/v1',
        'status':'PASS_SOURCE_BOUND_NOMINAL_SECTION_PROPERTIES_AND_TRACTION_ONLY',
        'fixtures':fixtures(),'source_sha256':pins,'sections':sections,'rows':rows,
        'source_metadata_correction':'Preserved section-demand report labels inner-block BG003 center cuts with 11766.458mm2, the away-from-cross-bore area. At those cuts the disjoint full-width 7.5mm BG003 strip must also be subtracted: applicable area11099.708mm2. This packet uses the explicit matching-axis geometry entry and records the difference; original signed actions and source report remain unchanged.',
        'limits':'Rectangular envelopes minus disjoint modeled bores, uniform linear-elastic affine normal strain, both one-sided source-discrete actions. X-bore center cuts have disconnected ligaments; common affine strain is an unqualified proxy, not demonstrated local bearing/transfer. No physical gravity, hole concentration/contact traction, shear/torsional stress, strength factor, stability, splitting, group or joint acceptance.',
        'strength_checked':False,'joint_accepted':False,'geometry_changed':False,
        'native_solve_run':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    data=json.dumps(produce(),indent=2,sort_keys=True,allow_nan=False)+'\n'
    target=HERE/'normal-traction.json'
    if args.verify:
        assert target.read_text()==data
        print('PASS_SOURCE_BOUND_NOMINAL_SECTION_PROPERTIES_AND_TRACTION_ONLY: 252 cuts')
    else:
        target.write_text(data)
        print('Wrote 252 signed nominal section-traction conversions')
