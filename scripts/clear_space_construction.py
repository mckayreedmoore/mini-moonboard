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
            '<text x="25" y="525">Conditions: ../clear-space-study.md. Hardware: ../clear-space-hardware.md.</text>',
            '</svg>'])
        (OUT/(name+'-notch-sheet.svg')).write_text('\n'.join(lines)+'\n')


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
        text(25,foot+90,'Conditions and installation: ../clear-space-study.md; hardware: ../clear-space-hardware.md + bolt-hardware.csv.')
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
    global OUT, INVENTORY, model, PACKET_STATUS
    root = ROOT
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
    if kind == 'floor':
        kicker_notch_sheets()
    expected_stock, expected_axes, expected_bolts = (26, 222, 12) if kind == 'floor' else (28, 230, 20)
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
        'artifact_sha256': artifacts,'scope': 'Conditional clear-space '+kind+' fabrication packet. Applies only to the recorded candidate and stated loads, hardware/material conditions and installation details. See docs/clear-space-study.md and docs/clear-space-hardware.md. No unconditional qualification.'},indent=2)+'\n')
    return OUT


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', choices=MODELS)
    args = parser.parse_args()
    print(generate(args.candidate))
