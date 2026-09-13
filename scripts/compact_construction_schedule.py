"""Generate compact-candidate development coordinates from its current export.

Stock blanks come from the standalone current viewer export; fastener and panel
axes come from current model factories. These are dimensional records, not a
resistance approval or a screw pilot specification.
"""
import csv
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard import compact_thick_exports as exporter
from mini_moonboard import compact_thick_frame as model
from mini_moonboard import panel_grid_v2 as grid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/compact-construction'
INVENTORY = ROOT / 'site/hybrid/compact-thick-development/parts.json'


def write_csv(name, rows):
    with (OUT/name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def bolt_member_datums(connections):
    """Physical side-face corner plus grain/cross-grain axes for each member.

    The origin is an actual profile vertex, not the intersection of extrapolated
    end cuts. Signed cross-grain offsets preserve the bevel corner choice.
    """
    raw = {p.name: p for p in model.uncut_wood_parts()}
    _, _, leg, _, rim = model.axes()
    rows = []
    for connection in connections:
        if connection.kind != 'bolt':
            continue
        for name in connection.members:
            part = raw[name]
            along = leg if name in model.previous.LEGS else rim
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
                'hole_diameter_mm': model.HOLE_DIAMETER,
                'instruction': 'Axis normal to side face; use profile to identify corner and positive directions. Development dimensions.'})
    return rows


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
<text x="25" y="25" font-family="sans-serif" font-size="18">Outer rim at header — development profile, mm</text>
<text x="25" y="49" font-family="sans-serif" font-size="13">YZ side view; +Y right, +Z up. Upper member continues beyond crop.</text>
<g clip-path="url(#detail)">
<polygon points="{outline}" fill="#ead5b3" stroke="#333" stroke-width="2"/>
<rect x="{hx}" y="{hy}" width="{(front-rear)*scale}" height="{(model.base.HEADER_TOP-model.base.HEADER_BOTTOM)*scale}" fill="#b7cde0" stroke="#333"/>
<line x1="{tx}" x2="{tx}" y1="75" y2="365" stroke="#c44" stroke-dasharray="4 4"/>
<line x1="{hx}" x2="{hx}" y1="75" y2="365" stroke="#468" stroke-dasharray="4 4"/>
</g>
<text x="25" y="397" font-family="sans-serif" font-size="13">Header depth {model.HEADER_DEPTH:g}; rear trim projects {model.REAR_OVERHANG_MM:g} behind header.</text>
<text x="25" y="420" font-family="sans-serif" font-size="13">Trim Y={model.INCLINED_TRIM_Y:g}; header rear Y={rear:g}; bearing Z={ztop:g}.</text>
<text x="25" y="441" font-family="sans-serif" font-size="12">Profile location only; partial bearing and remaining section require current checks.</text>
</svg>'''
    (OUT/'outer-rim-end-trim.svg').write_text(svg)


def generate():
    sources = exporter.sources()
    manifest_path = INVENTORY.with_name('manifest.json')
    published = json.loads(manifest_path.read_text())
    if published['source_sha256'] != sources:
        raise ValueError('Compact export source manifest is stale; rebuild before scheduling')
    if published['artifact_sha256']['parts.json'] != exporter.shared.digest(INVENTORY):
        raise ValueError('Compact inventory does not match its export manifest')
    sources[str(INVENTORY.relative_to(ROOT))] = exporter.shared.digest(INVENTORY)
    sources[str(Path(__file__).relative_to(ROOT))] = exporter.shared.digest(__file__)
    inventory = json.loads(INVENTORY.read_text())
    if inventory['design']['key'] != model.KEY or inventory['design']['main_face_height_mm'] != 277:
        raise ValueError('Require current 277 mm inventory')
    OUT.mkdir(exist_ok=True)
    stock = []
    for part in inventory['parts']:
        if part['fabrication']['kind'] != 'part' or part['name'].startswith('clip_'):
            continue
        dimensions = part['fabrication']['dimensions_mm']
        stock.append({'member': part['name'], 'blank_length_or_panel_width_mm': dimensions[0],
                          'blank_depth_or_panel_height_mm': dimensions[1], 'thickness_mm': dimensions[2],
                          'quantity': 1, 'detail': 'Model blank envelope; end profile is specified separately.'})
    write_csv('stock.csv', stock)
    connections = model.connections()
    axes = []
    for c in connections:
        axes.append({'name': c.name,'kind': c.kind,'first_member': c.members[0],'second_member': c.members[1],
            'start_x_mm': c.start.x,'start_y_mm': c.start.y,'start_z_mm': c.start.z,
            'direction_x': c.direction.x,'direction_y': c.direction.y,'direction_z': c.direction.z,
            'modeled_length_mm': c.length,'modeled_diameter_mm': c.diameter,
            'operation': f'Provisional leg bolt axis; {model.HOLE_DIAMETER:g} mm modeled clearance.' if c.kind=='bolt'
                else 'Fastener axis only; occupied diameter is not a pilot-bit instruction.'})
    write_csv('connection-axes.csv',axes)
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
    for kind,datums,diameter in [('hold',grid.main_tnut_datums(),11.1125),('LED',grid.main_led_datums(),13.)]:
        for label,(x,s) in datums.items():
            side='left' if x<model.b.HALF else 'right'
            band='lower' if s<model.b.HALF else 'upper'
            holes.append({'label': label,'kind': kind,'panel': f'main_{band}_{side}',
                'from_left_mm': x-(0 if side=='left' else model.b.HALF),
                'from_bottom_mm': s-(0 if band=='lower' else model.b.HALF),'diameter_mm': diameter})
    for label,(x,z) in grid.kicker_foothold_datums().items():
        side='left' if x<model.b.HALF else 'right'
        holes.append({'label': label,'kind': 'hold','panel': 'kicker_'+side,
            'from_left_mm': x-(0 if side=='left' else model.b.HALF),
            'from_bottom_mm': model.previous.KICKER_HEIGHT_MM+z,'diameter_mm': 11.1125})
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
    write_csv('leg-bolt-member-datums.csv', bolt_member_datums(connections))
    end_trim_diagram()
    if len(stock)!=24 or len(axes)!=216 or len(panel)!=66 or sum(r['kind']=='hold' for r in holes)!=142:
        raise ValueError('Current inventory count changed; update package deliberately')
    if any(exporter.shared.digest(ROOT/path)!=sha for path,sha in sources.items()):
        raise ValueError('Source changed during generation')
    artifacts={p.name:exporter.shared.digest(p) for p in sorted(OUT.iterdir()) if p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps({'candidate': model.KEY,
        'main_face_height_mm': model.previous.KICKER_HEIGHT_MM,'source_sha256': sources,
        'artifact_sha256': artifacts,'scope': 'Compact 4x6 development dimensional package; not released for construction. Actual connection, bearing and frame checks remain pending.'},indent=2)+'\n')
    return OUT


if __name__=='__main__':
    print(generate())
