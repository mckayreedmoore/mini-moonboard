"""Current face/edge drilling references; development geometry, never shop release."""
import argparse
import hashlib
import html
import json
from pathlib import Path

from . import panel_grid_v2 as grid

LIMITS = 'DEVELOPMENT REFERENCE — NOT RELEASED FOR CONSTRUCTION. Dimensions govern; do not scale or use as a drill template.'
TEMPLATE = 'https://moonclimbing.com/media/moonboard-pdf/Mini_MoonBoard_Template_Guide_Metric.pdf'


def source_hashes():
    paths = [*sorted(Path('mini_moonboard').glob('*.py')), Path('docs/led-wiring-reference.json')]
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def assert_sources_unchanged(sources):
    if any(hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha for path, sha in sources.items()):
        raise ValueError('Source changed during drilling generation')


def panel_rows():
    """Four front-view panels; lower rows down from top, upper rows up from bottom."""
    result = {}
    height = grid.PANEL_HEIGHT_MM
    for band in ('lower', 'upper'):
        for side in ('left', 'right'):
            rows = []
            x0 = 0. if side == 'left' else height
            s0 = 0. if band == 'lower' else height
            for kind, datums, diameter in (('T-nut', grid.main_tnut_datums(), 11.1125),
                                            ('LED', grid.main_led_datums(), 13.)):
                for label, (x, s) in datums.items():
                    if x0 <= x < x0+height and s0 <= s < s0+height:
                        rows.append({'label': label, 'kind': kind, 'diameter_mm': diameter,
                                     'from_left_mm': x-x0,
                                     'from_datum_edge_mm': height-s if band == 'lower' else s-height,
                                     'from_bottom_mm': s-s0})
            result[f'main_{band}_{side}'] = {'width_mm': height, 'height_mm': height,
                'datum_edge': 'TOP' if band == 'lower' else 'BOTTOM',
                'measurement_direction': 'DOWN' if band == 'lower' else 'UP', 'rows': rows}
    return result


def bolt_rows(model):
    """Physical broad-face coordinates: top end and front/side long edge."""
    from .connection_geometry import material_intervals

    raw = {p.name: p for p in model.wood_parts()}
    tangent = (model.b.point(0, 1, 0)-model.b.point(0, 0, 0)).normalized()
    _, _, along, across = model.leg.geometry('2x6', 0.)
    selected = [c for c in model.connections() if c.name.startswith('lumber_leg_bolt_')]
    if len(selected) != 8:
        raise ValueError('Require eight current structural leg bolts')
    result = {}
    for side in ('left', 'right'):
        for name in (f'base_side_{side}', f'lumber_leg_{side}'):
            part = raw[name]
            down, inward = (-tangent, model.b.normal()) if name.startswith('base_side_') else (-along, across)
            vertices = [v.Center() for v in part.shape.Vertices()]
            low_u, low_v = min(p.dot(inward) for p in vertices), min(p.dot(down) for p in vertices)
            rows = []
            for c in selected:
                if name not in c.members:
                    continue
                # Move to the wood mid-thickness before evaluating in-face boundaries.
                import cadquery as cq
                box = part.shape.BoundingBox()
                point = cq.Vector((box.xmin+box.xmax)/2, c.start.y, c.start.z)
                spans = [material_intervals(part.shape, point, axis, -5000., 5000.) for axis in (inward, down)]
                if any(len(runs) != 1 or not runs[0][0] < 0 < runs[0][1] for runs in spans):
                    raise ValueError('Bolt needs one continuous face interval: '+c.name+' '+name)
                rows.append({'connection': c.name, 'from_long_edge_mm': point.dot(inward)-low_u,
                    'from_top_end_mm': point.dot(down)-low_v, 'diameter_mm': 11.1125,
                    'long_edge_distances_mm': [-spans[0][0][0], spans[0][0][1]],
                    'end_distances_on_axis_mm': [-spans[1][0][0], spans[1][0][1]],
                    'axis_world': list(c.start.toTuple())})
            result[name] = {'side': side, 'width_mm': max(p.dot(inward) for p in vertices)-low_u,
                'length_mm': max(p.dot(down) for p in vertices)-low_v,
                'long_edge': 'panel-contact front edge' if name.startswith('base_side_') else 'frontmost long edge (smaller world Y at a fixed leg station)',
                'down_axis_world': list(down.toTuple()), 'width_axis_world': list(inward.toTuple()),
                'face': f'OUTER broad face, {side} side of assembled frame',
                'drill_direction': '+X, toward frame center' if side == 'left' else '-X, toward frame center',
                'outline': sorted({(p.dot(inward)-low_u, p.dot(down)-low_v) for p in vertices}),
                'rows': rows}
    return result


def groove_rows(model):
    """Front-open groove bounds from each member's left edge and top edge."""
    raw = {part.name: part for part in model.uncut_wood_parts()}
    origin = model.b.point(0, 0, 0)
    tangent = (model.b.point(0, 1, 0)-origin).normalized()
    result = {}
    for cut in model.cutout_records():
        name = cut['member']
        if name not in result:
            vertices = [v.Center() for v in raw[name].shape.Vertices()]
            xs = [v.x for v in vertices]
            stations = [(v-origin).dot(tangent) for v in vertices]
            result[name] = {'left_edge_world_x_mm': min(xs), 'top_edge_station_mm': max(stations),
                'width_mm': max(xs)-min(xs), 'height_mm': max(stations)-min(stations),
                'entry_face': 'Panel-contact FRONT face N=0; panel removed',
                'x_direction': 'RIGHT from this member left edge, viewed from climbing face',
                'vertical_direction': 'DOWN from this member top edge along inclined frame', 'rows': []}
        datum = result[name]
        datum['rows'].append({**cut,
            'from_left_start_mm': cut['x0_mm']-datum['left_edge_world_x_mm'],
            'from_left_end_mm': cut['x1_mm']-datum['left_edge_world_x_mm'],
            'from_top_start_mm': datum['top_edge_station_mm']-cut['s1_mm'],
            'from_top_end_mm': datum['top_edge_station_mm']-cut['s0_mm']})
    return result


def start_svg(title, subtitle):
    return ['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="790" viewBox="0 0 1120 790">',
            '<rect width="1120" height="790" fill="white"/>', '<g font-family="Arial,sans-serif" fill="#182a35">',
            f'<text x="35" y="34" font-size="23">{html.escape(title)}</text>',
            f'<text x="35" y="61" font-size="14">{html.escape(subtitle)}</text>']


def finish_svg(out):
    return '\n'.join(out+[f'<text x="30" y="764" font-size="12" fill="#a02020">{html.escape(LIMITS)}</text>', '</g></svg>'])+'\n'


def panel_svg(name, data):
    out = start_svg(name+' — HOLD / LED DRILLING', 'FRONT / CLIMBING FACE: left stays left. Drill perpendicular through panel toward rear; do not mirror.')
    x0, y0, scale = 65., 105., .43
    size = data['width_mm']*scale
    out.append(f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" fill="#fff8e8" stroke="#243745" stroke-width="2"/>')
    out.append(f'<text x="{x0}" y="{y0-15}" font-size="16">TOP — width / height 1219.2 mm (48 in)</text>')
    for row in data['rows']:
        x, y = x0+row['from_left_mm']*scale, y0+(data['height_mm']-row['from_bottom_mm'])*scale
        color = '#202830' if row['kind'] == 'T-nut' else '#007fa5'
        out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="3.2" fill="none" stroke="{color}"/>')
        out.append(f'<text x="{x+6:.3f}" y="{y-4:.3f}" fill="{color}" font-size="9">{row["kind"]} {row["label"]}</text>')
    lines = ['DATUM / DIRECTION', f'Measure from {data["datum_edge"]} edge {data["measurement_direction"]}.',
             'X: from this panel’s LEFT edge → RIGHT.', 'Black: T-nut bore Ø11.1125 mm (7/16 in).',
             'Blue: LED bore Ø13.000 mm.', 'CAD diameters; verify actual purchased hardware.',
             'No T-nut mounting-screw pilot schedule here.', '', 'COLUMN: distance from LEFT (mm)']
    columns = sorted({(r['label'][0], r['from_left_mm']) for r in data['rows']})
    lines += [f'{label}: {distance:.3f}' for label, distance in columns]
    lines += ['', f'ROW: {data["datum_edge"]} edge → {data["measurement_direction"]} (mm)']
    unique = sorted({(int(r['label'][1:]), r['kind'], r['from_datum_edge_mm']) for r in data['rows']})
    lines += [f'{kind} {row}: {distance:.3f}' for row, kind, distance in unique]
    for i, line in enumerate(lines):
        out.append(f'<text x="640" y="{100+i*19}" font-size="13">{html.escape(line)}</text>')
    out += ['<text x="65" y="663" font-size="13">1219.2 mm stock adaptation of nominal 1220 mm metric template; no scaling.</text>',
            '<text x="65" y="685" font-size="13">Lower LED1: 19.2 mm above bottom. LED7 belongs to LOWER panel, 20 mm below top.</text>',
            '<text x="65" y="707" font-size="13">T-nut rows 6–7 remain 220 mm apart. Panel fastening holes are a separate schedule.</text>']
    return finish_svg(out)


def bolt_svg(name, data):
    out = start_svg(name+' — FOUR LEG-JOINT BORES', data['face']+'; drill '+data['drill_direction']+'.')
    lines = ['Measure DOWN along grain from the TOP end.', 'Measure ACROSS from the named long edge:', data['long_edge']+'.',
             'Coordinates are per member; do not transfer a rim', 'pattern onto its leg or mirror the opposite side.',
             'Nominal through clearance Ø11.1125 mm (7/16 in).', 'Complete member thickness: 38.1 mm (1.5 in).',
             'Top/edge offsets below are hole CENTER distances.', 'Outer face: smaller X on LEFT; larger X on RIGHT.',
             'Width arrow follows stated world axis; opposite', 'outer-face views have opposite handedness.']
    for i, line in enumerate(lines):
        out.append(f'<text x="35" y="{102+i*21}" font-size="15">{html.escape(line)}</text>')
    top = min(r['from_top_end_mm'] for r in data['rows'])-35
    bottom = max(r['from_top_end_mm'] for r in data['rows'])+35
    scale = min(350/data['width_mm'], 330/(bottom-top))
    x0, y0 = 650., 95.
    out.append(f'<rect x="{x0}" y="{y0}" width="{data["width_mm"]*scale}" height="{(bottom-top)*scale}" fill="#fff8e8" stroke="#263b44" stroke-dasharray="5 4"/>')
    out.append('<text x="650" y="79" font-size="13">LOCAL AXIS PROJECTION / ENLARGED HOLE REGION</text>')
    out.append(f'<text x="650" y="{y0+(bottom-top)*scale+22}" font-size="13">Width {data["width_mm"]:.3f} mm; down-window starts {top:.3f} mm</text>')
    for index, row in enumerate(data['rows'], 1):
        x, y = x0+row['from_long_edge_mm']*scale, y0+(row['from_top_end_mm']-top)*scale
        out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{row["diameter_mm"]*scale/2:.3f}" fill="none" stroke="#006f9e"/>')
        out.append(f'<text x="{x+15:.3f}" y="{y:.3f}" font-size="14">{index}</text>')
    lines = ['HOLE / CONNECTION                         FROM TOP     FROM LONG EDGE     OPPOSITE EDGE    NEAREST END (mm)']
    for index, row in enumerate(data['rows'], 1):
        lines.append(f'{index}  {row["connection"]}     {row["from_top_end_mm"]:.3f}     {row["from_long_edge_mm"]:.3f}     '
                     f'{row["long_edge_distances_mm"][1]:.3f}     {min(row["end_distances_on_axis_mm"]):.3f}')
    lines += ['', 'DOWN unit vector, world XYZ: '+str([round(v, 6) for v in data['down_axis_world']]),
              'WIDTH unit vector, world XYZ: '+str([round(v, 6) for v in data['width_axis_world']]),
              'Dashed region is a detail window, not stock ends. End distances follow grain at each bore.',
              'These pages cover eight leg/rim bolt axes only. Panel screws are a separate schedule.']
    for i, line in enumerate(lines):
        out.append(f'<text x="35" y="{480+i*24}" font-family="monospace" font-size="13">{html.escape(line)}</text>')
    return finish_svg(out)


def groove_svg(name, data):
    out = start_svg(name+' — OPEN-FRONT WIRING GROOVES',
                    'FRONT / CLIMBING FACE with panel removed. Width → RIGHT; length ↓ DOWN. Do not mirror.')
    x0, y0, width, height = 60., 125., 990., 180.
    out.append(f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" fill="#fff8e8" stroke="#243745"/>')
    out.append('<text x="60" y="105" font-size="15">TOP EDGE / LEFT EDGE origin — schematic aspect ratio; use table dimensions</text>')
    for i, row in enumerate(data['rows'], 1):
        x = x0+width*row['from_left_start_mm']/data['width_mm']
        y = y0+height*row['from_top_start_mm']/data['height_mm']
        w = width*(row['from_left_end_mm']-row['from_left_start_mm'])/data['width_mm']
        h = height*(row['from_top_end_mm']-row['from_top_start_mm'])/data['height_mm']
        out.append(f'<rect x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}" fill="#b7e9f2" stroke="#007b92"/>')
        out.append(f'<text x="{x+2:.4f}" y="{y+15:.4f}" font-size="13">{i}</text>')
    lines = [f'Member front-face envelope: {data["width_mm"]:.3f} mm across × {data["height_mm"]:.3f} mm down.',
             'DEPTH: from panel-contact face N=0, perpendicular INTO timber (+N). Open grooves, NOT closed bores.',
             'Place prewired harness into open face before fitting panel. No threading bulbs/connectors through timber.',
             'CUT   LED SEGMENT        LEFT START–END (mm)        TOP START–END (mm)        DEPTH (mm)']
    for i, row in enumerate(data['rows'], 1):
        lines.append(f'{i:>2}    {" → ".join(row["datums"]):<17} '
            f'{row["from_left_start_mm"]:8.3f}–{row["from_left_end_mm"]:8.3f}       '
            f'{row["from_top_start_mm"]:8.3f}–{row["from_top_end_mm"]:8.3f}       {row["depth_mm"]:.3f}')
    lines += ['Owner bulb-base pitch ≈304.8 mm; cable diameter, body projection and bend radius remain unverified.',
              'Channel sizes are provisional CAD cuts; remaining-section, fastener and actual harness fit checks still apply.']
    if len(lines) > 17:
        raise ValueError('Groove table needs pagination: '+name)
    for i, line in enumerate(lines):
        out.append(f'<text x="35" y="{342+i*23}" font-family="monospace" font-size="13">{html.escape(line)}</text>')
    return finish_svg(out)


def generate(output):
    from . import horizontal_service_frame as model

    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    sources = source_hashes()
    panels, bolts, grooves = panel_rows(), bolt_rows(model), groove_rows(model)
    files = {name+'.svg': panel_svg(name, record) for name, record in panels.items()}
    files.update({name+'.svg': bolt_svg(name, record) for name, record in bolts.items()})
    for name, record in grooves.items():
        for offset in range(0, len(record['rows']), 10):
            page = offset//10+1
            files[f'{name}-grooves-{page}.svg'] = groove_svg(
                f'{name} / page {page}', {**record, 'rows': record['rows'][offset:offset+10]})
    output.mkdir(parents=True)
    for name, data in files.items():
        (output/name).write_text(data)
    data = {'candidate': model.KEY, 'qualified_for_design': False, 'limits': LIMITS,
            'official_template_url': TEMPLATE, 'panels': panels, 'leg_bolt_members': bolts,
            'front_open_groove_members': grooves}
    (output/'drilling.json').write_text(json.dumps(data, indent=2)+'\n')
    sections = ''.join('<section>'+svg+'</section>' for svg in files.values())
    (output/'drilling.html').write_text('<!doctype html><meta charset="utf-8"><title>Development drilling references</title>'
        '<style>@page{size:A4 landscape;margin:0}body{margin:0}section{break-after:page;width:297mm;height:210mm}'
        'svg{display:block;width:297mm;height:210mm}</style>'+sections)
    assert_sources_unchanged(sources)
    (output/'manifest.json').write_text(json.dumps({'candidate': model.KEY, 'source_sha256': sources,
        'artifact_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}}, indent=2)+'\n')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('docs/horizontal-service-drilling'))
    print(generate(parser.parse_args().output))
