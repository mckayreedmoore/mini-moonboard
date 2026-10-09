"""Saved-coordinate builder drawings; standard library only, no CAD or solves."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PACKET = ROOT / 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1'
SHOP = PACKET / 'shop-assembly-v1'
MEMBERS = ('base_floor_left', 'lumber_leg_left', 'base_side_left')
IDS = ('rail_rear_bolt_left_1', 'rail_rear_bolt_left_2',
       'lumber_leg_bolt_left_1', 'lumber_leg_bolt_left_2')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict]:
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    # Source vertex indices are not perimeter order.
    points = sorted(set(points))
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower, upper = [], []
    for seq, target in ((points, lower), (reversed(points), upper)):
        for point in seq:
            while len(target) >= 2 and cross(target[-2], target[-1], point) <= 0:
                target.pop()
            target.append(point)
    return lower[:-1]+upper[:-1]


def extract() -> dict:
    geometry_path = PACKET / 'occupied-aligned-wire-v1.json'
    geometry = json.loads(geometry_path.read_text())
    assert geometry['revision'] == 'eoere-grid-aligned-wire-cutouts-v1'
    member_rows = {r['member']: r for r in rows(SHOP / 'members.csv')}
    ends = rows(SHOP / 'member-end-datums.csv')
    holes = rows(SHOP / 'receiver-holes.csv')
    datums = json.loads((SHOP / 'cut-datums-result.json').read_text())
    unchanged = {r['id']: r for r in geometry['unchanged_finished_solids']}
    sources = [geometry_path, SHOP / 'members.csv', SHOP / 'member-end-datums.csv',
               SHOP / 'receiver-holes.csv', SHOP / 'cut-datums-result.json']
    parts = {}
    for name in MEMBERS:
        r = member_rows[name]
        current = unchanged[name]
        assert r['current_finished_source_sha256'] == current['sha256']
        path = ROOT / current['path']
        assert sha(path) == current['sha256']
        sources.append(path)
        vertices = [v for v in ends if v['member'] == name and v['record_kind'] == 'raw_profile_vertex']
        parts[name] = {
            'finished_source': current,
            'datum_xyz_mm': [float(r[f'datum_{k}_mm']) for k in 'xyz'],
            'basis_L': [float(r[f'basis_l_{k}_unitless']) for k in 'xyz'],
            'basis_W': [-float(r[f'basis_v_{k}_unitless']) for k in 'xyz'],
            'raw_profile_yz_mm': hull([(float(v['point_y_mm']), float(v['point_z_mm'])) for v in vertices]),
            'raw_profile_LW_mm': hull([(float(v['point_l_mm']), -float(v['point_v_mm'])) for v in vertices]),
            'end_angles_away_from_square_deg': [float(v['normal_to_L_deg']) for v in ends
                if v['member'] == name and v['record_kind'] == 'raw_end_plane'],
        }
    bolts = []
    for key in IDS:
        axis = next(a for a in geometry['axes'] if a['id'] == key)
        assert axis['direction_xyz'] == [-1.0, 0.0, 0.0]
        receiver_rows = [r for r in holes if r['axis_id'] == key]
        assert [r['receiver'] for r in receiver_rows] == axis['receivers']
        assert abs(sum(float(r['saved_full_wall_length_mm']) for r in receiver_rows)-axis['grip_mm']) < 1e-6
        for r in receiver_rows:
            assert max(abs(float(r[f'axis_point_{k}_mm'])-axis['point_xyz_mm'][i])
                       for i, k in enumerate('xyz')) < 1e-6
        bolts.append({
            'id': key, 'label': ('R' if key.startswith('rail_rear') else 'U')+key[-1],
            'point_xyz_mm': axis['point_xyz_mm'], 'direction_xyz': axis['direction_xyz'],
            'timber_grip_mm': axis['grip_mm'], 'nominal_bolt_diameter_mm': axis['diameter_mm'],
            'nominal_underhead_length_mm': axis['nominal_under_head_length_mm'],
            'receiver_centers': [{
                'member': r['receiver'], 'L_mm': float(r['entry_in_receiver_l_mm']),
                'W_mm': -float(r['entry_in_receiver_v_mm']),
                'wood_interval_mm': float(r['saved_full_wall_length_mm']),
            } for r in receiver_rows],
        })
    recess = next(r for r in datums['recess_definitions']['definitions'] if r['member'] == 'lumber_leg_left')
    s0 = recess['cut_profile_world_x_global_grain_s_mm'][0][1]
    start = recess['cut_profile_world_x_global_grain_s_mm'][2][1]-s0
    finish = recess['cut_profile_world_x_global_grain_s_mm'][3][1]-s0
    assert abs(finish-start-457.2) < 1e-6
    return {
        'schema': 'eoere_builder_leg_corner_nominal/v1',
        'revision': geometry['revision'],
        'status': 'NOMINAL_LAYOUT_AND_FIXTURE_CONCEPT_NOT_FABRICATION_RELEASE',
        'units': 'mm; degrees',
        'tool_policy': 'Owner: circular saw, handheld drill, clamps and pull saw; prefer pull saw for 4x6.',
        'sources': {str(p.relative_to(ROOT)): sha(p) for p in sources},
        'parts': parts, 'bolts': bolts,
        'recess': {'maximum_depth_mm': 38.1, 'remaining_lower_thickness_mm': 50.8,
                   'run_mm': 457.2, 'start_from_heel_L_mm': start, 'end_from_heel_L_mm': finish,
                   'nominal_runner_top_clearance_mm': 2.0, 'transverse_fit_allowance_mm': 0.0},
        'limits': [
            'Raw broad-face outlines are not finished recess/service-cut contours.',
            'Target crosshairs are nominal centers, not drilled-hole outlines or selected bit sizes.',
            'No machining tolerance, actual printer scale, tool travel, fixture retention or physical fit is verified.',
            'Only the left side is drawn; no right-side recess or head/nut mirroring instruction is issued.',
            'No current complete joint resistance, fabrication release or transferred six-case pass.',
        ],
    }


class SVG:
    def __init__(self, width, height, physical=False):
        unit = 'mm' if physical else ''
        self.items = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}{unit}" height="{height}{unit}" viewBox="0 0 {width} {height}">',
                      '<rect width="100%" height="100%" fill="white"/>']
    def text(self, x, y, value, size=15, weight='normal', color='#223044'):
        self.items.append(f'<text x="{x:.4f}" y="{y:.4f}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(value)}</text>')
    def line(self, a, b, color='#223044', width=1, dashed=False):
        dash = ' stroke-dasharray="3 2"' if dashed else ''
        self.items.append(f'<line x1="{a[0]:.4f}" y1="{a[1]:.4f}" x2="{b[0]:.4f}" y2="{b[1]:.4f}" stroke="{color}" stroke-width="{width}"{dash}/>')
    def polygon(self, points, fill='#edf2f7', color='#223044', width=1):
        pts = ' '.join(f'{x:.4f},{y:.4f}' for x, y in points)
        self.items.append(f'<polygon points="{pts}" fill="{fill}" stroke="{color}" stroke-width="{width}"/>')
    def rect(self, x, y, w, h, fill='#edf2f7', color='#223044', width=1):
        self.polygon([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],fill,color,width)
    def cross(self, x, y, label, physical=False):
        radius = 2 if physical else 5
        width = .3 if physical else 1.5
        self.items.append(f'<circle cx="{x:.4f}" cy="{y:.4f}" r="{radius}" fill="white" stroke="#9a3140" stroke-width="{width}"/>')
        self.line((x-radius*1.6,y),(x+radius*1.6,y),'#9a3140',width)
        self.line((x,y-radius*1.6),(x,y+radius*1.6),'#9a3140',width)
        self.text(x+radius*2,y-radius,label,3.5 if physical else 14,'bold','#9a3140')
    def render(self):
        return '\n'.join(self.items+['</svg>'])+'\n'


def overview(data):
    s = SVG(1200, 850)
    s.text(35,42,'Left leg / runner / sloping side',29,'bold')
    s.text(35,70,'Nominal layout and fixture concept | existing geometry retained | not a fabrication release',16)
    scale=.22
    project=lambda y,z:(55+(y+175.7)*scale,650-z*scale)
    colors={'base_floor_left':('#e1f1e5','#2e7651'), 'lumber_leg_left':('#fff0d9','#976522'),
            'base_side_left':('#e0ecfa','#39679a')}
    s.text(55,110,'A. Side elevation: +Y rearward, +Z upward',17,'bold')
    s.text(55,134,'Profiles overlap in projection; X offsets are shown at right.',13)
    for name in ('base_side_left','lumber_leg_left','base_floor_left'):
        fill,color=colors[name]
        s.polygon([project(*p) for p in data['parts'][name]['raw_profile_yz_mm']],fill,color,2)
    s.line((40,650),(500,650),'#223044',2)
    s.text(55,676,'Front runner datum: Y = -175.700; floor Z = 0',14)
    s.text(55,699,'Runner bottom length 1815.646; top length 1781.239',14)
    s.text(55,722,'Leg lean 13.836° from vertical; frame slope 50° above floor',14)
    label_points={'R1':(485,640),'R2':(485,609),'U1':(420,283),'U2':(420,253)}
    for b in data['bolts']:
        y,z=b['point_xyz_mm'][1:];point=project(y,z);s.cross(*point,'')
        x,label_y=label_points[b['label']]
        s.line(point,(x-5,label_y-4),'#9a3140',.8)
        s.text(x,label_y,b['label'],14,'bold','#9a3140')
    s.text(290,220,'Sloping 4×6 side',15,'bold',colors['base_side_left'][1])
    s.text(327,410,'4×6 leg',15,'bold',colors['lumber_leg_left'][1])
    s.text(75,606,'2×6 runner',15,'bold',colors['base_floor_left'][1])
    s.text(580,110,'B. Transverse drilling: entry at left, travel toward -X',17,'bold')
    s.text(580,139,'Schematic thickness sections; floor/table orientation not specified.',13)
    for y,title,segments,caption in [
        (190,'Lower R1/R2',[('Runner',38.1,'#e1f1e5'),('Recessed leg',50.8,'#fff0d9')],
         '38.1 + 50.8 = 88.9 mm timber grip; nominal 3/8 × 4½-inch bolts'),
        (320,'Upper U1/U2',[('Side',88.9,'#e0ecfa'),('Leg',88.9,'#fff0d9')],
         '88.9 + 88.9 = 177.8 mm timber grip; nominal 1/2 × 8-inch bolts')]:
        s.text(580,y-18,title,17,'bold');x=580
        for name,w,fill in segments:
            s.rect(x,y,w*2.5,52,fill);s.text(x+8,y+21,name,13);s.text(x+8,y+41,f'{w:.1f} mm',13);x+=w*2.5
        s.line((565,y+26),(x+20,y+26),'#9a3140',2)
        s.polygon([(x+20,y+26),(x+11,y+21),(x+11,y+31)],'#9a3140','#9a3140',1)
        s.text(580,y+78,caption,13)
    s.text(580,458,'C. Coordinates for common paired-hole layout',17,'bold')
    s.text(580,484,'All four axes run across X. World coordinates in mm:',14)
    for i,b in enumerate(data['bolts']):
        _,y,z=b['point_xyz_mm'];s.text(595,512+26*i,f'{b["label"]}: Y {y:.3f}   Z {z:.3f}',15)
    rear=data['bolts'][:2];upper=data['bolts'][2:]
    for y,title,pair in [(633,'Lower pair',rear),(659,'Upper pair',upper)]:
        a,b=[x['point_xyz_mm'] for x in pair]
        distance=math.hypot(b[1]-a[1],b[2]-a[2]);s.text(580,y,f'{title}: center distance {distance:.3f} mm (diagonal)',14)
    s.text(580,699,'Fixture: locate seated pieces, support both, clamp independently;',14)
    s.text(580,722,'guide both holes from one common setup. Tool travel is unverified.',14)
    s.text(35,774,'R = rear runner/leg bolts; U = upper side/leg bolts. Crosshair circles do not select hole diameters.',15)
    s.text(35,800,'Raw profiles shown. Leg recess: 38.1 mm maximum depth with 457.2 mm (1:12) return; see guide.',14)
    s.text(35,826,'No scale for marking from this overview. Use the separate 190 × 260 mm layout sheets and their scale checks.',14)
    return s.render()


def calibration(s):
    s.line((25,243),(125,243),width=.3)
    for x in (25,125):s.line((x,241),(x,245),width=.3)
    s.text(25,239,'Horizontal check: 100 mm',3.5)
    s.line((180,130),(180,230),width=.3)
    for y in (130,230):s.line((178,y),(182,y),width=.3)
    s.items.append('<text x="184" y="220" transform="rotate(-90 184 220)" font-family="Arial,sans-serif" font-size="3.3">Vertical check: 100 mm</text>')
    s.text(8,252,'Print 100%, no fit-to-page. Verify BOTH 100-mm checks.',3.3)
    s.text(8,258,'Nominal layout only; circles are targets, not drill diameters.',3.1)


def leg_template(data, top=False):
    s=SVG(190,260,True)
    title='LEFT LEG TOP' if top else 'LEFT LEG FOOT'
    s.text(8,10,title+' | outer broad face',5,'bold')
    s.text(8,17,'W from rear long edge; L along grain from foot heel.',3.3)
    s.text(8,23,'Left side only. No cutting or drilling release.',3.2)
    profile=data['parts']['lumber_leg_left']['raw_profile_LW_mm']
    rear_top=max(l for l,w in profile if abs(w)<1e-6)
    front_top=max(l for l,w in profile if abs(w-139.7)<1e-6)
    front_foot=min(l for l,w in profile if abs(w-139.7)<1e-6)
    if top:
        project=lambda l,w:(25+w,30+rear_top-l)
        cutoff=rear_top-200
        points=[project(rear_top,0),project(front_top,139.7),project(cutoff,139.7),project(cutoff,0)]
        s.polygon(points,'#fff8ed',width=.35)
        s.line(project(rear_top,0),project(front_top,139.7),'#9a3140',.65)
        s.line(project(cutoff,0),project(cutoff,139.7),'white',.8)
        s.line(project(cutoff,0),project(cutoff,139.7),width=.4,dashed=True)
        s.text(85,43,'Rear-edge top L = 1989.026',3.3)
        s.text(85,52,'Front-edge top L = 1886.918',3.3)
        s.text(85,61,'36.164° away from square',3.3)
        s.text(85,70,'Waste above red line',3.3)
        s.text(28,225,'Continues to foot; dashed line is NOT a cut.',3.3)
        selected=data['bolts'][2:]
    else:
        project=lambda l,w:(25+w,220-l)
        points=[project(190,0),project(190,139.7),project(front_foot,139.7),project(0,0)]
        s.polygon(points,'#fff8ed',width=.35)
        s.line(project(0,0),project(front_foot,139.7),'#9a3140',.65)
        s.line(project(190,0),project(190,139.7),'white',.8)
        s.line(project(190,0),project(190,139.7),width=.4,dashed=True)
        s.text(29,42,'Continues upward; dashed line is NOT a cut.',3.1)
        s.text(29,54,'Foot: rear heel L=0; front edge L=34.408',3.1)
        s.text(29,65,'13.836° away from square',3.3)
        s.text(29,176,'Outer-face outline; inner recess is NOT shown.',3.2)
        s.text(29,228,'Datum B: rear heel, L=0 / W=0',3.3)
        selected=data['bolts'][:2]
    for b in selected:
        r=next(r for r in b['receiver_centers'] if r['member']=='lumber_leg_left')
        s.cross(*project(r['L_mm'],r['W_mm']),b['label'],True)
    calibration(s)
    return s.render()


def runner_template(data):
    s=SVG(190,260,True)
    s.text(8,10,'LEFT RUNNER REAR | inner face',5,'bold')
    s.text(8,17,'Register bottom edge and rear heel B; +Y toward rear.',3.3)
    s.text(8,23,'Intended R1/R2 entry. No cutting or drilling release.',3.2)
    profile=data['parts']['base_floor_left']['raw_profile_yz_mm']
    rear=max(y for y,z in profile if abs(z)<1e-6)
    rear_top=max(y for y,z in profile if abs(z-139.7)<1e-6)
    project=lambda y,z:(25+y-(rear-155),40+139.7-z)
    s.polygon([project(rear-155,0),project(rear,0),project(rear_top,139.7),project(rear-155,139.7)],'#eff8f1',width=.35)
    s.line(project(rear,0),project(rear_top,139.7),'#9a3140',.65)
    s.line(project(rear-155,0),project(rear-155,139.7),'white',.8)
    s.line(project(rear-155,0),project(rear-155,139.7),width=.4,dashed=True)
    s.text(28,35,'Top edge; rear cut is 13.836° away from square',3.1)
    for b in data['bolts'][:2]:
        _,y,z=b['point_xyz_mm'];s.cross(*project(y,z),b['label'],True)
    s.text(29,195,'R1: 88.946 mm forward of B; 69.000 mm up',3.1)
    s.text(29,205,'R2: 122.946 mm forward of B; 97.500 mm up',3.1)
    s.text(29,217,'B = rear bottom heel. Dashed line is NOT a cut.',3.1)
    s.text(29,227,'Side-face width shown: 139.700 mm vertically.',3.1)
    calibration(s)
    return s.render()


def outputs(data):
    return {
        'leg-corner-data.json': json.dumps(data,indent=2,sort_keys=True)+'\n',
        'leg-corner-overview.svg': overview(data),
        'left-leg-foot-template.svg': leg_template(data),
        'left-leg-top-template.svg': leg_template(data,True),
        'left-runner-rear-template.svg': runner_template(data),
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write',action='store_true')
    group.add_argument('--check',action='store_true')
    args=parser.parse_args()
    if args.check:
        frozen=json.loads((OUT/'leg-corner-data.json').read_text())
        for p,h in frozen['sources'].items():
            if sha(ROOT/p)!=h:raise ValueError(f'Changed source: {p}')
    data=extract()
    result=outputs(data)
    for name,content in result.items():
        path=OUT/name
        if args.write:path.write_text(content)
        elif path.read_text()!=content:raise ValueError(f'Drawing differs: {name}')
    print(json.dumps({'status':'PASS_SAVED_COORDINATE_DRAWINGS' if args.check else 'WROTE_NOMINAL_DRAWINGS',
                      'sources':len(data['sources']), 'members':len(data['parts']), 'bolt_axes':len(data['bolts']),
                      'generated_bytes':sum(len(t.encode()) for t in result.values()),
                      'limits':'No fabrication tolerance, bit selection, tool/fixture qualification or mechanics pass.'}))


if __name__=='__main__':
    main()
