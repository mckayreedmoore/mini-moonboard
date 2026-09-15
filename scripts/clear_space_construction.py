"""Generate complete candidate-specific clear-space fabrication coordinates.

Stock blanks come from the standalone current viewer export; fastener and panel
axes come from current model factories. These are dimensional records, not a
resistance approval or a screw pilot specification.
"""
import argparse
import csv
import importlib
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard import no_shoes_frame as baseline
from mini_moonboard import panel_grid_v2 as grid
from scripts import clear_space_exports as exporter
from scripts.clear_space_study import MODELS

ROOT = Path(__file__).resolve().parents[1]
OUT = None
INVENTORY = None
model = None
PACKET_STATUS = None
PACKAGE = exporter.PACKAGE
HARDWARE = exporter.hardware_path('floor')


def member_grain(candidate, name):
    """Use actual post, rail, leg or principal grain when choosing corner datums."""
    if name.startswith('base_post_'):
        return cq.Vector(0., 0., 1.)
    if name in candidate.MEMBER_AXES:
        return candidate.MEMBER_AXES[name][0]
    return candidate.axes()[2] if name in baseline.LEGS else candidate.axes()[4]


def kicker_notch_records(candidate):
    rows = []
    for panel, cutouts in candidate.panel_edge_cutouts().items():
        left = -candidate.b.HALF if panel.endswith('left') else 0.
        for xmin, xmax, zmin, zmax in cutouts:
            rows.append({'panel': panel, 'from_left_mm': xmin-left,
                         'from_bottom_mm': zmin, 'width_mm': xmax-xmin,
                         'height_mm': zmax-zmin,
                         'instruction': 'Open bottom and outside edge; preserve the 2 mm rail clearance.'})
    return rows


def kicker_notch_sheets():
    """Actual non-convex panel profile plus all nine retained screw axes."""
    from html import escape

    rows = kicker_notch_records(model)
    write_csv('kicker-notch-cuts.csv', rows)
    for row in rows:
        name = row['panel']
        width, height = model.b.HALF, baseline.KICKER_HEIGHT_MM
        notch_w, notch_h = row['width_mm'], row['height_mm']
        left_notch = name.endswith('left')
        polygon = ([(notch_w, 0), (width, 0), (width, height), (0, height),
                    (0, notch_h), (notch_w, notch_h)] if left_notch else
                   [(0, 0), (width-notch_w, 0), (width-notch_w, notch_h),
                    (width, notch_h), (width, height), (0, height)])
        scale = 1000/width
        def xy(x, z, scale=scale):
            return 50+x*scale, 360-z*scale
        points = ' '.join(f'{xy(x,z)[0]:.3f},{xy(x,z)[1]:.3f}' for x,z in polygon)
        lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="580" viewBox="0 0 1120 580">',
                 f'<title>{escape(name)} floor-rail notch and screw placement</title>',
                 '<rect width="100%" height="100%" fill="white"/>',
                 '<style>text{font-family:sans-serif;font-size:14px;fill:#17202a}</style>',
                 f'<text x="25" y="30">{escape(name)} — floor-rail clearance, dimensions in mm</text>',
                 '<text x="25" y="55">Front view. Dimension from original rectangular panel edges; use numbers, not image scale.</text>',
                 f'<polygon points="{points}" fill="#eee1c7" stroke="#333" stroke-width="2"/>']
        panel_left = -width if left_notch else 0.
        screws = [c for c in model.panel_connections() if c.members[0] == name]
        if len(screws) != 9:
            raise ValueError('Kicker packet requires nine screws per independent panel')
        for screw in screws:
            x, z = screw.start.x-panel_left, screw.start.z
            sx, sz = xy(x, z)
            lines.append(f'<circle cx="{sx:.3f}" cy="{sz:.3f}" r="4" fill="#245a81"/>')
        lines.extend([
            f'<text x="25" y="400">Panel blank {width:g} × {height:g}; notch {notch_w:g} wide × {notch_h:g} high, open to bottom/outside edge.</text>',
            f'<text x="25" y="425">Rail section {model.RAIL_THICKNESS_MM:g} × {model.RAIL_DEPTH_MM:g}; clearance {model.KICKER_CLEARANCE_MM:g} above and beside rail.</text>',
            '<text x="25" y="450">Outer post screws: world X = ±1162.05; Z = 60 and 192. All nine axes: panel-attachment-axes.csv.</text>',
            '<text x="25" y="475">Notch-edge clearance to lower outer screw axis: 17.05. Hold/LED drilling: panel-hole-axes.csv.</text>',
            '<text x="25" y="500">SPAX axes shown; occupied diameter does not specify a pilot. Do not bridge the independent center seam.</text>',
            f'<text x="25" y="525">Conditions: ../{Path(PACKAGE).name}. Hardware: ../{Path(HARDWARE).name}.</text>',
            '</svg>'])
        (OUT/(name+'-notch-sheet.svg')).write_text('\n'.join(lines)+'\n')



def leg_recess_sheets():
    """Record the actual open-bottom leg recess and its remaining thickness."""
    from html import escape

    records = model.leg_recess_records()
    if set(records) != {'lumber_leg_left', 'lumber_leg_right'}:
        raise ValueError('Recess packet requires both leg records')
    if model.panel_edge_cutouts():
        raise ValueError('Outboard recess packet must retain unnotched kickers')
    raw = {p.name:p for p in model.uncut_wood_parts() if p.name in records}
    if set(raw) != set(records):
        raise ValueError('Recess sheet requires both actual raw leg shapes')
    for name, record in records.items():
        vertices = [v.Center() for v in raw[name].shape.Vertices()]
        # OCC bounding boxes include tolerances. Select the physical face from
        # actual vertex coordinates, not the padded bounding-box minimum.
        face_x = min(v.x for v in vertices)
        profile = sorted({(v.y, v.z) for v in vertices if abs(v.x-face_x) <= 1.e-6})
        if len(profile) < 3 or abs(min(z for _, z in profile)-record['bottom_z_mm']) > 1.e-5:
            raise ValueError('Recess sheet requires a physical side profile reaching the recorded floor: '+name)
        record['side_profile_yz_mm'] = profile
    (OUT/'leg-recess-geometry.json').write_text(json.dumps(records, indent=2)+'\n')
    rows = []
    for name, record in records.items():
        cut_lo, cut_hi = record['cut_inner_x_band_mm']
        keep_lo, keep_hi = record['retained_x_band_mm']
        rows.append({'member':name, 'cut_from':record['cut_from'],
            'depth_x_mm':record['depth_x_mm'], 'cut_inner_x_min_mm':cut_lo,
            'cut_inner_x_max_mm':cut_hi, 'cut_bottom_z_mm':record['bottom_z_mm'],
            'cut_top_z_mm':record['notch_top_z_mm'],
            'remaining_leg_thickness_mm':record['remaining_leg_thickness_mm'],
            'retained_x_min_mm':keep_lo, 'retained_x_max_mm':keep_hi,
            'runner_top_z_mm':record['runner_top_z_mm'],
            'shoulder_gap_mm':record['shoulder_gap_mm'],
            'transverse_clearance_mm':record['transverse_clearance_mm'],
            'operation':record['operation'], 'assessment_status':PACKET_STATUS})
        # The raw side profile is convex; order its vertices before clipping
        # at the drawing's upper edge and the actual horizontal recess shoulder.
        points = sorted(set(map(tuple, record['side_profile_yz_mm'])))
        def turn(a, b, c):
            return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        lower, upper = [], []
        for target, ordered in ((lower, points), (upper, reversed(points))):
            for point in ordered:
                while len(target)>1 and turn(target[-2], target[-1], point)<=0:
                    target.pop()
                target.append(point)
        profile = lower[:-1]+upper[:-1]
        def below(polygon, height):
            result = []
            for first, second in zip(polygon, polygon[1:]+polygon[:1], strict=True):
                first_in, second_in = first[1]<=height, second[1]<=height
                if first_in:
                    result.append(first)
                if first_in != second_in:
                    fraction = (height-first[1])/(second[1]-first[1])
                    result.append((first[0]+fraction*(second[0]-first[0]), height))
            return result
        shoulder = record['notch_top_z_mm']
        shown = below(profile, shoulder+100.)
        removed = below(profile, shoulder)
        if len(shown) < 3 or len(removed) < 3:
            raise ValueError('Actual recess profile must cross the floor and shoulder: '+name)
        min_y, max_y = min(p[0] for p in shown), max(p[0] for p in shown)
        scale = min(550/(max_y-min_y), 290/(shoulder+100.))
        def polygon_text(polygon, min_y=min_y, scale=scale):
            return ' '.join(f'{75+(y-min_y)*scale:.3f},{385-z*scale:.3f}' for y,z in polygon)
        raw_xlo, raw_xhi = record['raw_bounds_xyz_mm'][0]
        width = raw_xhi-raw_xlo
        band_scale = 260/width
        cut_x = 690+(cut_lo-raw_xlo)*band_scale
        lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="710" viewBox="0 0 1060 710">',
            f'<title>{escape(name)} open-bottom inner-face recess</title>',
            '<rect width="100%" height="100%" fill="white"/>',
            '<style>text{font-family:sans-serif;font-size:14px;fill:#17202a}</style>',
            f'<text x="25" y="30">{escape(name)} — actual leg recess, dimensions in mm</text>',
            '<text x="25" y="55">Side projection of lower leg; red is removed only within the inner X band.</text>',
            f'<polygon points="{polygon_text(shown)}" fill="#eee1c7" stroke="#333" stroke-width="2"/>',
            f'<polygon points="{polygon_text(removed)}" fill="#e9a39a" stroke="#a33" stroke-width="2"/>',
            f'<text x="75" y="415">World Y increasing right; floor Z = 0. View clipped at Z = {shoulder+100.:g}.</text>',
            '<text x="690" y="105">Transverse thickness schedule</text>',
            '<rect x="690" y="125" width="260" height="70" fill="#eee1c7" stroke="#333"/>',
            f'<rect x="{cut_x:.3f}" y="125" width="{record["depth_x_mm"]*band_scale:.3f}" height="70" fill="#e9a39a" stroke="#a33"/>',
            '<text x="690" y="220">X increases right; inner face faces board center.</text>',
            f'<text x="690" y="250">Remove {record["depth_x_mm"]:g}; retain {record["remaining_leg_thickness_mm"]:g}.</text>',
            f'<text x="690" y="280">Cut X = {cut_lo:.3f} to {cut_hi:.3f}.</text>',
            f'<text x="690" y="310">Retain X = {keep_lo:.3f} to {keep_hi:.3f}.</text>',
            f'<text x="25" y="465">Cut from inner side, open through foot end, to horizontal shoulder Z = {shoulder:g} above floor.</text>',
            f'<text x="25" y="490">Runner top Z = {record["runner_top_z_mm"]:g}; shoulder gap = {record["shoulder_gap_mm"]:g}. Shoulder bearing is not credited.</text>',
            f'<text x="25" y="515">Transverse clearance = {record["transverse_clearance_mm"]:g}. Preserve the full opposite-face leg thickness.</text>',
            '<text x="25" y="540">Matching bolt axes: bolt-member-datums.csv and leg bolt sheet. Do not use the image as a drill template.</text>',
            '<text x="25" y="565">Kickers remain unnotched; original outer-post attachment axes retained. See panel-attachment-axes.csv.</text>',
            f'<text x="25" y="590">Assessment: {escape(PACKET_STATUS)}</text>',
            f'<text x="25" y="620">Conditions: ../{Path(PACKAGE).name}. Hardware: ../{Path(HARDWARE).name}.</text>',
            '</svg>']
        (OUT/(name+'-recess-sheet.svg')).write_text('\n'.join(lines)+'\n')
    write_csv('leg-recess-cuts.csv', rows)


def leg_taper_sheets():
    """Dimension the actual X/grain cutter polygon and retain full cut vertices."""
    from html import escape

    records = model.leg_recess_records()
    if set(records) != {'lumber_leg_left', 'lumber_leg_right'} or model.panel_edge_cutouts():
        raise ValueError('Taper packet requires two actual tapered legs and unnotched kickers')
    raw = {p.name:p for p in model.uncut_wood_parts() if p.name in records}
    cutters = {name:cutter for name, _, _, cutter in model.additional_machining_cutters()}
    rows = []
    for name, record in records.items():
        shape = raw[name].shape.cut(cutters[name]).clean()
        record['retained_profile_vertices_world_mm'] = sorted({
            tuple(round(v, 9) for v in vertex.Center().toTuple()) for vertex in shape.Vertices()})
        low, high = record['grain_bounds_mm']
        start, end = record['taper_start_station_mm'], record['taper_end_station_mm']
        inner, sign = record['inner_face_x_mm'], record['outward_sign']
        depth = record['max_recess_depth_mm']
        width = record['raw_bounds_xyz_mm'][0][1]-record['raw_bounds_xyz_mm'][0][0]
        if end-start <= 0 or abs((end-start)/depth-record['taper_ratio']) > 1.e-6:
            raise ValueError('Taper run and depth do not match the recorded slope')
        rows.append({'member':name, 'datum':'A = grain dot world XYZ minus lowest raw-leg grain station; D = depth from inner face toward outer face',
            'grain_origin_station_mm':low, 'inner_face_world_x_mm':inner,
            'depth_direction_world_x':sign, 'full_recess_depth_mm':depth,
            'taper_start_A_mm':start-low, 'taper_end_A_mm':end-low,
            'run_along_grain_mm':end-start, 'run_per_depth':record['taper_ratio'],
            'minimum_remaining_thickness_mm':width-depth,
            'minimum_runner_clearance_mm':record['minimum_vertical_runner_clearance_mm'],
            'operation':record['operation'], 'assessment_status':PACKET_STATUS})
        # This transverse/grain projection defines the removal envelope. The
        # existing foot bevel remains defined by the full 3D retained vertices.
        scale = min(820/(high-low), 190/width)
        def xy(a, d, low=low, scale=scale):
            return 70+(a-low)*scale, 145+d*scale
        polygon = ' '.join(f'{xy(station, (x-inner)*sign)[0]:.3f},{xy(station, (x-inner)*sign)[1]:.3f}'
                           for x,station in record['cut_profile_xs_mm'])
        lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="660" viewBox="0 0 1060 660">',
            '<rect width="100%" height="100%" fill="white"/>',
            '<style>text{font-family:sans-serif;font-size:14px;fill:#17202a}</style>',
            f'<title>{escape(name)} inner-face taper cut</title>',
            f'<text x="25" y="30">{escape(name)} — inner-face taper, dimensions in mm</text>',
            f'<text x="25" y="56">{escape(PACKET_STATUS)}</text>',
            '<text x="25" y="82">X/grain removal envelope; retain existing foot/end bevels. Numerical coordinates govern.</text>',
            f'<rect x="70" y="145" width="{(high-low)*scale:.3f}" height="{width*scale:.3f}" fill="#eee1c7" stroke="#333"/>',
            f'<polygon points="{polygon}" fill="#e9a39a" stroke="#a33" stroke-width="2"/>',
            '<text x="70" y="125">+A along grain →; +D into timber from inner face ↓</text>',
            f'<text x="25" y="365">A origin: absolute grain station {low:.6f}; inner face X = {inner:.6f}; D direction X = {sign:+g}.</text>',
            f'<text x="25" y="390">Full depth D = {depth:.3f} until A = {start-low:.3f}; return to D = 0 at A = {end-low:.3f}.</text>',
            f'<text x="25" y="415">Run {end-start:.3f}; slope 1:{record["taper_ratio"]:g}; retain at least {width-depth:.3f} thickness.</text>',
            f'<text x="25" y="440">Grain axis world XYZ: {escape(str(record["grain_axis_xyz"]))}.</text>',
            '<text x="25" y="465">Exact cutter and cut-member vertices: leg-taper-geometry.json. Cut coordinates: leg-taper-cuts.csv.</text>',
            '<text x="25" y="490">Bolt drilling: bolt-member-datums.csv and member bolt sheets. Raw profile sheets omit this removal.</text>',
            '<text x="25" y="515">Other machining: timber-passages.json; connection-axes.csv; panel-attachment-axes.csv; panel-hole-axes.csv.</text>',
            '<text x="25" y="540">Kickers remain unnotched. No shoulder bearing credited; preserve recorded runner clearance.</text>',
            f'<text x="25" y="575">Conditions: ../{Path(PACKAGE).name}; hardware: ../{Path(HARDWARE).name}.</text>',
            '</svg>']
        (OUT/(name+'-taper-sheet.svg')).write_text('\n'.join(lines)+'\n')
    write_csv('leg-taper-cuts.csv', rows)
    (OUT/'leg-taper-geometry.json').write_text(json.dumps(records, indent=2, allow_nan=False)+'\n')


def write_csv(name, rows):
    with (OUT/name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(dict.fromkeys(
            key for row in rows for key in row)))
        writer.writeheader()
        writer.writerows(rows)


def bolt_member_datums(connections):
    """Physical side-face corner plus grain/cross-grain axes for each member.

    The origin is an actual profile vertex, not the intersection of extrapolated
    end cuts. Signed cross-grain offsets preserve the bevel corner choice.
    """
    raw = {p.name: p for p in model.uncut_wood_parts()}
    rows = []
    for connection in connections:
        if connection.kind != 'bolt':
            continue
        for name in connection.members:
            part = raw[name]
            along = member_grain(model, name)
            cross = along.cross(cq.Vector(1., 0., 0.)).normalized()
            vertices = [v.Center() for v in part.shape.Vertices()]
            xmin = min(v.x for v in vertices)
            face = [v for v in vertices if abs(v.x-xmin) < 1.e-6]
            corner = min(face, key=lambda p: (round(p.dot(along), 6), p.dot(cross)))
            point = cq.Vector(xmin, connection.start.y, connection.start.z)
            offset = point-corner
            rows.append({'connection': connection.name, 'member': name,
                'datum': 'Minimum-X side face; lowest along-grain physical profile corner',
                'origin_x_mm': corner.x, 'origin_y_mm': corner.y, 'origin_z_mm': corner.z,
                'along_y': along.y, 'along_z': along.z, 'cross_y': cross.y, 'cross_z': cross.z,
                'along_from_corner_mm': offset.dot(along), 'signed_cross_from_corner_mm': offset.dot(cross),
                'hole_diameter_mm': model.bolt_dimensions(connection)['hole_diameter_mm'],
                'instruction': 'Axis normal to side face; use profile to identify corner and positive directions. Conditional package dimensions; follow the stated installation assumptions.'})
    return rows


def joined_member_sheets(datums):
    """Nominal side-face profiles and bolt ordinates for the eight joined members."""
    from html import escape

    raw = {p.name: p for p in model.uncut_wood_parts()}
    names = sorted({r['member'] for r in datums})
    if len(names) != 8:
        raise ValueError('Expected exactly eight joined timber members')
    for name in names:
        part = raw[name]
        holes = [r for r in datums if r['member'] == name]
        row = holes[0]
        origin = cq.Vector(*(row[f'origin_{axis}_mm'] for axis in 'xyz'))
        along = cq.Vector(0., row['along_y'], row['along_z'])
        cross = cq.Vector(0., row['cross_y'], row['cross_z'])
        vertices = [v.Center() for v in part.shape.Vertices()]
        points = sorted({(round((v-origin).dot(along), 6), round((v-origin).dot(cross), 6))
                         for v in vertices if abs(v.x-origin.x) < 1.e-6})
        def turn(a, b, c):
            return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        lower, upper = [], []
        for target, ordered in ((lower, points), (upper, reversed(points))):
            for point in ordered:
                while len(target)>1 and turn(target[-2], target[-1], point)<=0:
                    target.pop()
                target.append(point)
        polygon = lower[:-1]+upper[:-1]
        xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
        ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
        scale = min(860/(xmax-xmin), 140/(ymax-ymin))
        def xy(a, c, xmin=xmin, ymin=ymin, scale=scale):
            return 70+(a-xmin)*scale, 270-(c-ymin)*scale
        trim = model.trim_planes().get(name)
        height = 640+len(holes)*27+(75 if trim else 0)
        lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}">',
            f'<title>{escape(name)} nominal side-face profile and bolt coordinates</title>',
            '<rect width="100%" height="100%" fill="white"/>',
            '<style>text{font-family:sans-serif;fill:#17202a;font-size:14px}.small{font-size:12px}.title{font-size:21px;font-weight:bold}</style>',
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#245a81"/></marker></defs>']
        def text(x, y, value, style='', lines=lines):
            lines.append(f'<text x="{x}" y="{y}" class="{style}">{escape(str(value))}</text>')
        text(25,30,name,'title')
        text(25,56,('CONDITIONAL BUILD PACKAGE — stated assumptions apply.'
                    if PACKET_STATUS.startswith('Conditional') else
                    'NOT ACCEPTED — geometry reference only; do not use as a build release.'))
        text(25,80,'Blank length × depth × thickness: '+' × '.join(f'{n:.3f}' for n in part.blank)+' mm; quantity 1.')
        text(25,102,'Minimum-X side face; full outline. All dimensions in mm. Use dimensions, not image scale.')
        outline = ' '.join(f'{xy(a,c)[0]:.3f},{xy(a,c)[1]:.3f}' for a,c in polygon)
        lines.append(f'<polygon points="{outline}" fill="#eee1c7" stroke="#333" stroke-width="1.5"/>')
        ox, oy = xy(0,0)
        lines.append(f'<circle cx="{ox}" cy="{oy}" r="4" fill="#c33"/>')
        text(ox+6,oy+22,'D: physical corner','small')
        for number,hole in enumerate(holes,1):
            hx,hy = xy(hole['along_from_corner_mm'],hole['signed_cross_from_corner_mm'])
            lines.append(f'<circle cx="{hx}" cy="{hy}" r="{hole["hole_diameter_mm"]*scale/2}" fill="white" stroke="#245a81" stroke-width="1.2"/>')
            # Stagger the short IDs; exact coordinates are listed in the table.
            ly = 305+((number-1)%2)*20
            lines.append(f'<line x1="{hx}" y1="{hy}" x2="{hx}" y2="{ly-12}" stroke="#637785" stroke-width=".6"/>')
            text(hx+3,ly,f'H{number}','small')
        lines.append('<path d="M75 395H195M75 395V345" fill="none" stroke="#245a81" stroke-width="1.5" marker-end="url(#arrow)"/>')
        # Separate arrow markers show both positive directions.
        lines.append('<path d="M75 395H195" fill="none" stroke="#245a81" stroke-width="1.5" marker-end="url(#arrow)"/>')
        text(205,400,'+A along grain');text(85,355,'+C across grain')
        text(25,425,'D world XYZ: '+', '.join(f'{v:.3f}' for v in origin.toTuple())+' mm. Both ordinates start at D.')
        text(25,448,f'+A world YZ = ({along.y:.9f}, {along.z:.9f}); +C = ({cross.y:.9f}, {cross.z:.9f}).')
        for x,title in [(25,'ID'),(75,'Connection ID (matches bolt-member-datums.csv)'),(575,'A from D'),(705,'Signed C from D'),(875,'Hole Ø')]:
            text(x,483,title,'small')
        for number,hole in enumerate(holes,1):
            y=483+number*27
            for x,value in [(25,f'H{number}'),(75,hole['connection']),(575,f'{hole["along_from_corner_mm"]:.3f}'),(705,f'{hole["signed_cross_from_corner_mm"]:.3f}'),(875,f'{hole["hole_diameter_mm"]:.4f}')]:
                text(x,y,value,'small')
        foot=510+len(holes)*27
        text(25,foot,'Bolt axes normal to this side face. Signed C may be negative; do not mirror the corner convention.')
        text(25,foot+24,'Full raw side profile shown; these sheets do not include every machining operation.')
        text(25,foot+46,'LED passages: timber-passages.json. Panel/SDS screw axes: connection-axes.csv; no pilot size inferred.')
        text(25,foot+68,'Panel operations: panel-attachment-axes.csv + panel-hole-axes.csv. End details: stock-profiles.json.')
        text(25,foot+90,f'Conditions and installation: ../{Path(PACKAGE).name}; hardware: ../{Path(HARDWARE).name} + bolt-hardware.csv.')
        if trim:
            normal = cq.Vector(*trim['keep_normal_xyz'])
            ends = sorted({(round((v-origin).dot(along),3),round((v-origin).dot(cross),3))
                           for v in vertices if abs(v.x-origin.x)<1.e-6
                           and abs(v.dot(normal)-trim['offset_mm'])<1.e-5})
            if len(ends) != 2:
                raise ValueError('Expected two side-profile trim endpoints: '+name)
            text(25,foot+118,f'End cut: {trim["angle_from_square_deg"]:.3f}° off square. Connect these two (A, C) points from D:')
            text(25,foot+142,' to '.join(f'({a:.3f}, {c:.3f}) mm' for a,c in ends))
        lines.append('</svg>')
        (OUT/(name+'-bolt-sheet.svg')).write_text('\n'.join(lines)+'\n')


def end_trim_diagram():
    """Actual uncut outer-rim YZ profile at the base, with header datums."""
    part = next(p for p in model.uncut_wood_parts() if p.name == 'base_side_left')
    points = sorted({(round(v.Y, 6), round(v.Z, 6)) for v in part.shape.Vertices()})
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower, upper = [], []
    for target, ordered in ((lower, points), (upper, reversed(points))):
        for p in ordered:
            while len(target)>1 and cross(target[-2], target[-1], p)<=0:
                target.pop()
            target.append(p)
    polygon = lower[:-1]+upper[:-1]
    front = model.base.HEADER_FRONT_Y
    rear = model.HEADER_BACK_Y
    ztop = model.base.HEADER_TOP
    scale = 2.
    def xy(y, z):
        return (70+(y-(rear-25))*scale, 380-(z-(ztop-60))*scale)
    outline = ' '.join(f'{xy(y,z)[0]:.3f},{xy(y,z)[1]:.3f}' for y,z in polygon)
    hx, hy = xy(rear, ztop)
    tx, _ = xy(model.INCLINED_TRIM_Y, ztop)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="650" height="450" viewBox="0 0 650 450">
<title>Compact outer-rim base trim, side profile</title>
<rect width="650" height="450" fill="white"/>
<defs><clipPath id="detail"><rect x="35" y="70" width="565" height="310"/></clipPath></defs>
<text x="25" y="25" font-family="sans-serif" font-size="18">Outer rim at header — conditional package profile, mm</text>
<text x="25" y="49" font-family="sans-serif" font-size="13">YZ side view; +Y right, +Z up. Upper member continues beyond crop.</text>
<g clip-path="url(#detail)">
<polygon points="{outline}" fill="#ead5b3" stroke="#333" stroke-width="2"/>
<rect x="{hx}" y="{hy}" width="{(front-rear)*scale}" height="{(model.base.HEADER_TOP-model.base.HEADER_BOTTOM)*scale}" fill="#b7cde0" stroke="#333"/>
<line x1="{tx}" x2="{tx}" y1="75" y2="365" stroke="#c44" stroke-dasharray="4 4"/>
<line x1="{hx}" x2="{hx}" y1="75" y2="365" stroke="#468" stroke-dasharray="4 4"/>
</g>
<text x="25" y="397" font-family="sans-serif" font-size="13">Header depth {model.HEADER_DEPTH:g}; rear trim projects {model.REAR_OVERHANG_MM:g} behind header.</text>
<text x="25" y="420" font-family="sans-serif" font-size="13">Trim Y={model.INCLINED_TRIM_Y:g}; header rear Y={rear:g}; bearing Z={ztop:g}.</text>
<text x="25" y="441" font-family="sans-serif" font-size="12">Profile location only; follow the stated load, hardware and installation assumptions.</text>
</svg>'''
    (OUT/'outer-rim-end-trim.svg').write_text(svg)


def generate(kind):
    global OUT, INVENTORY, model, PACKET_STATUS, PACKAGE, HARDWARE
    root = ROOT
    PACKAGE, HARDWARE = exporter.package_path(kind), exporter.hardware_path(kind)
    model = importlib.import_module('mini_moonboard.'+MODELS[kind])
    OUT = root / ('docs/clear-space-'+kind+'-construction')
    INVENTORY = root / 'site/hybrid' / model.KEY / 'parts.json'
    sources = exporter.sources(model, kind)
    manifest_path = INVENTORY.with_name('manifest.json')
    published = json.loads(manifest_path.read_text())
    if published['source_sha256'] != sources:
        raise ValueError('Compact export source manifest is stale; rebuild before scheduling')
    for name, sha in published['artifact_sha256'].items():
        if exporter.shared.digest(INVENTORY.parent/name) != sha:
            raise ValueError('Standalone export artifact does not match its manifest: '+name)
    sources[str(INVENTORY.relative_to(ROOT))] = exporter.shared.digest(INVENTORY)
    sources[str(manifest_path.relative_to(ROOT))] = exporter.shared.digest(manifest_path)
    sources[str(Path(__file__).relative_to(ROOT))] = exporter.shared.digest(__file__)
    inventory = json.loads(INVENTORY.read_text())
    if inventory['design']['key'] != model.KEY or inventory['design']['main_face_height_mm'] != 277:
        raise ValueError('Require current 277 mm inventory')
    PACKET_STATUS = inventory['design']['status']
    OUT.mkdir(parents=True, exist_ok=True)
    stock = []
    for part in inventory['parts']:
        if part['fabrication']['kind'] != 'part' or part['name'].startswith('clip_'):
            continue
        dimensions = part['fabrication']['dimensions_mm']
        stock.append({'member': part['name'], 'blank_length_or_panel_width_mm': dimensions[0],
                          'blank_depth_or_panel_height_mm': dimensions[1], 'thickness_mm': dimensions[2],
                          'quantity': 1, 'detail': 'Model blank envelope; end profile is specified separately.', 'assessment_status': PACKET_STATUS})
    write_csv('stock.csv', stock)
    connections = model.connections()
    axes = []
    for c in connections:
        axes.append({'name': c.name,'kind': c.kind,'first_member': c.members[0],'second_member': c.members[1],
            'start_x_mm': c.start.x,'start_y_mm': c.start.y,'start_z_mm': c.start.z,
            'direction_x': c.direction.x,'direction_y': c.direction.y,'direction_z': c.direction.z,
            'modeled_length_mm': c.length,'modeled_diameter_mm': c.diameter,
            'operation': f"Scheduled bolt axis; {model.bolt_dimensions(c)['hole_diameter_mm']:g} mm modeled clearance." if c.kind=='bolt'
                else 'Fastener axis only; occupied diameter is not a pilot-bit instruction.'})
    write_csv('connection-axes.csv',axes)
    write_csv('bolt-hardware.csv', [dict(name=c.name, first_member=c.members[0],
        second_member=c.members[1], **model.bolt_dimensions(c))
        for c in connections if c.kind == 'bolt'])
    panel = []
    for row in model.attachment_datums():
        name=row['panel']; left=-model.b.HALF if name.endswith('_left') else 0.
        bottom=model.b.HALF if name.startswith('main_upper_') else 0.
        panel.append({'name': row['name'],'panel': name,'receiver': row['receiver'],
            'from_left_mm': row['x']-left,'from_bottom_mm': row['s']-bottom,
            'vertical_axis': 'Z from floor' if name.startswith('kicker_') else 'S along panel slope',
            'operation': 'SPAX axis; no insert pilot or pilot diameter specified.'})
    write_csv('panel-attachment-axes.csv',panel)
    holes=[]
    for hole_kind,datums,diameter in [('hold',grid.main_tnut_datums(),11.1125),('LED',grid.main_led_datums(),13.)]:
        for label,(x,s) in datums.items():
            side='left' if x<model.b.HALF else 'right'
            band='lower' if s<model.b.HALF else 'upper'
            holes.append({'label': label,'kind': hole_kind,'panel': f'main_{band}_{side}',
                'from_left_mm': x-(0 if side=='left' else model.b.HALF),
                'from_bottom_mm': s-(0 if band=='lower' else model.b.HALF),'diameter_mm': diameter})
    for label,(x,z) in grid.kicker_foothold_datums().items():
        side='left' if x<model.b.HALF else 'right'
        holes.append({'label': label,'kind': 'hold','panel': 'kicker_'+side,
            'from_left_mm': x-(0 if side=='left' else model.b.HALF),
            'from_bottom_mm': baseline.KICKER_HEIGHT_MM+z,'diameter_mm': 11.1125})
    write_csv('panel-hole-axes.csv',holes)
    from mini_moonboard.round_service_drilling import passage_rows
    passages = passage_rows(model)
    (OUT/'timber-passages.json').write_text(json.dumps(passages,indent=2)+'\n')
    # Exact raw-member vertices preserve bevels and panel transition profiles.
    # These are world coordinates, suitable for CAD measurement, not drill jigs.
    profiles = {p.name: {'blank_mm': p.blank, 'vertices_world_mm': sorted({
        tuple(round(v,9) for v in vertex.Center().toTuple())
        for vertex in p.shape.Vertices()})} for p in model.uncut_wood_parts()}
    (OUT/'stock-profiles.json').write_text(json.dumps(profiles,indent=2)+'\n')
    member_datums = bolt_member_datums(connections)
    write_csv('bolt-member-datums.csv', member_datums)
    joined_member_sheets(member_datums)
    end_trim_diagram()
    if kind in ('floor', 'floor2x4'):
        kicker_notch_sheets()
    elif kind == 'floorrecess':
        leg_recess_sheets()
    elif kind == 'floortaper':
        leg_taper_sheets()
    expected_stock, expected_axes, expected_bolts = {
        'floor':(26, 222, 12), 'floor2x4':(26, 224, 14),
        'floorrecess':(26, 222, 12), 'floortaper':(26, 222, 12), 'exterior':(28, 230, 20)}[kind]
    if (len(stock)!=expected_stock or len(axes)!=expected_axes or len(panel)!=66
            or sum(c.kind=='bolt' for c in connections)!=expected_bolts
            or sum(r['kind']=='hold' for r in holes)!=142):
        raise ValueError('Current inventory count changed; update package deliberately')
    if any(exporter.shared.digest(ROOT/path)!=sha for path,sha in sources.items()):
        raise ValueError('Source changed during generation')
    artifacts={p.name:exporter.shared.digest(p) for p in sorted(OUT.iterdir()) if p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps({'candidate': model.KEY,
        'main_face_height_mm': baseline.KICKER_HEIGHT_MM,'source_sha256': sources,
        'assessment_status': PACKET_STATUS,
        'artifact_sha256': artifacts,'scope': 'Conditional clear-space '+kind+' fabrication packet. Applies only to the recorded candidate and stated loads, hardware/material conditions and installation details. See '+PACKAGE+' and '+HARDWARE+'. No unconditional qualification.'},indent=2)+'\n')
    return OUT


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', choices=MODELS)
    args = parser.parse_args()
    print(generate(args.candidate))
