"""Separate lights-last circular-passage drawings; never released shop instructions."""
import argparse
import hashlib
import html
import json
from pathlib import Path

import cadquery as cq

from . import horizontal_service_drilling as previous
from .connection_geometry import material_intervals

LIMITS = previous.LIMITS


def passage_rows(model):
    """Dimension each enclosed passage from its actual entry face and long edges.

    Ligaments are local center-section distances minus the bore radius. They
    do not replace full-solid intersection, notch or resistance checks.
    """
    raw = {p.name: p for p in model.uncut_wood_parts()}
    origin = model.b.point(0., 0., 0.)
    tangent = (model.b.point(0., 1., 0.)-origin).normalized()
    result = []
    for bore in model.bore_records():
        part = raw[bore['member']]
        center = model.b.point(bore['center_x_mm'], bore['center_s_mm'], bore['center_n_mm'])
        direction = cq.Vector(*bore['direction'])
        if bore['axis_local'] not in ('S', 'X'):
            raise ValueError('Unknown passage direction')
        expected = tangent if bore['axis_local'] == 'S' else cq.Vector(1., 0., 0.)
        if (direction-expected).Length > 1e-8:
            raise ValueError('Passage axis differs from stated positive drilling direction')
        cross = cq.Vector(1., 0., 0.) if bore['axis_local'] == 'S' else tangent
        distances = []
        for axis in (direction, cross, model.b.normal()):
            runs = material_intervals(part.shape, center, axis, -5000., 5000.)
            if len(runs) != 1 or not runs[0][0] < 0 < runs[0][1]:
                raise ValueError('Passage center requires one continuous raw member interval: '+bore['name'])
            distances.append([-runs[0][0], runs[0][1]])
        axial, width, depth = distances
        radius = bore['diameter_mm']/2
        ligaments = [value-radius for value in (*width, *depth)]
        if min(ligaments) <= 0:
            raise ValueError('Passage is open to a long face: '+bore['name'])
        result.append({**bore,
            'entry_world_mm': list((center-direction*axial[0]).toTuple()),
            'exit_world_mm': list((center+direction*axial[1]).toTuple()),
            'through_wood_length_mm': sum(axial),
            'drilling_direction_world': list(direction.toTuple()),
            'entry_face_description': ('LOWER station end face; drill UP along +S' if bore['axis_local'] == 'S'
                                       else 'LEFT broad face; drill RIGHT along +X'),
            'width_datum_description': ('Member LEFT edge, increasing X' if bore['axis_local'] == 'S'
                                        else 'Member LOWER end, increasing S along slope'),
            'width_axis_world': list(cross.toTuple()),
            'center_from_width_edges_mm': width,
            'center_from_front_rear_faces_mm': depth,
            'local_ligaments_width_low_high_front_rear_mm': ligaments,
            'ligament_scope': 'Center-section geometry only; full bore and oblique end-face clearance require separate audit',
            'qualified_for_machining': False})
    return result


def passage_svg(row):
    out = previous.start_svg(row['name']+' — CIRCULAR STRAND PASSAGE', row['entry_face_description'])
    radius = row['diameter_mm']/2
    width, depth = row['center_from_width_edges_mm'], row['center_from_front_rear_faces_mm']
    # A local face projection keeps the circular bore circular. It is not a
    # mirrored photograph or a full member outline.
    extent = max(row['diameter_mm']+30., min(*width, *depth)+radius+20.)
    scale = min(3., 280./(2*extent))
    cx, cy = 840., 255.
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{radius*scale}" fill="#d7eff5" stroke="#007b92" stroke-width="2"/>')
    out.append(f'<path d="M {cx-90} {cy} H {cx+90} M {cx} {cy-90} V {cy+90}" stroke="#888" stroke-dasharray="4 4"/>')
    out.append('<text x="660" y="390" font-size="13">LOCAL ENTRY-FACE PROJECTION; circle is not a template.</text>')
    lines = [row['member'], 'LED segment: '+' → '.join(row['datums']),
             f'Circular diameter: {row["diameter_mm"]:.3f} mm.',
             f'THROUGH actual wood: {row["through_wood_length_mm"]:.3f} mm along stated axis.',
             'Width datum: '+row['width_datum_description']+'.',
             f'Center from width datum / opposite edge: {width[0]:.3f} / {width[1]:.3f} mm.',
             f'Center from panel-contact FRONT / REAR face: {depth[0]:.3f} / {depth[1]:.3f} mm.',
             'Width offsets follow their axis at bore-center N; respect any oblique end cut.',
             'FRONT is N=0; depth increases INTO timber (+N).',
             'No front-open slot, countersink or counterbore is specified.',
             'Member entry XYZ (mm): '+str([round(v, 6) for v in row['entry_world_mm']]),
             'Member exit XYZ (mm): '+str([round(v, 6) for v in row['exit_world_mm']]),
             'Drill unit direction XYZ: '+str([round(v, 6) for v in row['drilling_direction_world']]),
             'Width unit direction XYZ: '+str([round(v, 6) for v in row['width_axis_world']]),
             'Local remaining wood, width low/high/front/rear (mm):',
             ' / '.join(f'{v:.3f}' for v in row['local_ligaments_width_low_high_front_rear_mm']),
             'Ligaments above are center-section checks, not a strength approval.',
             'Oblique end cuts and the complete circular bore require the separate fit audit.',
             'Fit panels first; feed harness and install lights afterward.',
             'Verify actual feeding access, bends and connector length before machining.',
             'Panel screw cylinders do not specify approved pilot diameters.']
    for i, line in enumerate(lines):
        out.append(f'<text x="35" y="{105+i*29}" font-size="13">{html.escape(line)}</text>')
    return previous.finish_svg(out)


def kicker_hold_rows():
    """Use the same metric datums and vertical offset as base_frame.raw_parts."""
    from . import base_frame as base

    result = {}
    for column, side in enumerate(('left', 'right')):
        rows = []
        for label, (x, z) in previous.grid.kicker_foothold_datums().items():
            if column*base.b.HALF <= x < (column+1)*base.b.HALF:
                rows.append({'label': label, 'kind': 'T-nut', 'diameter_mm': 11.1125,
                    'from_left_mm': x-column*base.b.HALF, 'from_top_mm': -z,
                    'from_bottom_mm': base.b.V1_KICKER_HEIGHT_MM+z})
        result['kicker_'+side] = {'width_mm': base.b.HALF,
            'height_mm': base.b.V1_KICKER_HEIGHT_MM, 'datum_edge': 'TOP',
            'measurement_direction': 'DOWN', 'rows': rows}
    return result


def kicker_hold_svg(name, record):
    out = previous.start_svg(name+' — FIVE HOLD / T-NUT BORES',
        'FRONT / CLIMBING FACE: left stays left. Drill perpendicular toward rear (-Y); do not mirror.')
    x0, y0, scale = 55., 125., .75
    out.append(f'<rect x="{x0}" y="{y0}" width="{record["width_mm"]*scale}" '
               f'height="{record["height_mm"]*scale}" fill="#fff8e8" stroke="#243745"/>')
    for row in record['rows']:
        x, y = x0+row['from_left_mm']*scale, y0+row['from_top_mm']*scale
        out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="4" fill="none" stroke="#243745"/>')
        out.append(f'<text x="{x+7:.3f}" y="{y-8:.3f}" font-size="13">{row["label"]}</text>')
    lines = [f'Panel: {record["width_mm"]:.3f} mm wide x {record["height_mm"]:.3f} mm high.',
        'Measure RIGHT from this panel’s LEFT edge (+X); measure DOWN from TOP.',
        'Every bore: 75.000 mm below TOP, 150.000 mm above BOTTOM; diameter 11.1125 mm (7/16 in).',
        'These are existing hold/T-nut axes; no LED holes or panel-fastening pilots are added.',
        'Verify the purchased T-nut; retention-screw instructions remain separate.',
        '', 'HOLD LABEL — FROM THIS PANEL’S LEFT EDGE (mm)']
    lines += [f'{row["label"]}: {row["from_left_mm"]:.3f}' for row in record['rows']]
    for i, line in enumerate(lines):
        out.append(f'<text x="55" y="{340+i*27}" font-size="13">{html.escape(line)}</text>')
    return previous.finish_svg(out)


def panel_fastening_rows():
    """Panel-local axes; no pilot diameter or machining depth is inferred."""
    from . import round_panel_layout as layout

    result = {}
    for row in layout.datums():
        panel = row['panel']
        left = -layout.HALF if panel.endswith('_left') else 0.
        bottom = layout.HALF if panel.startswith('main_upper_') else 0.
        result.setdefault(panel, []).append({**row,
            'from_left_mm': row['x']-left, 'from_bottom_mm': row['s']-bottom,
            'station_axis': 'vertical Z' if panel.startswith('kicker_') else 'slope S',
            'pilot_diameter_mm': None, 'qualified_for_machining': False})
    return result


def panel_fastening_svg(name, rows):
    out = previous.start_svg(name+' — PANEL FASTENING AXES',
        'FRONT / CLIMBING FACE: measure right from LEFT edge and up from BOTTOM edge; do not mirror.')
    lines = ['Development layout: '+str(len(rows))+' screws on this panel; count does not establish resistance.',
        'Coordinates below are panel-local millimeters. Drill axis is perpendicular to the panel.',
        'SPAX XFT08P-2000 #8 x 2 inch: nominal 90-degree included head angle, 8.128 mm head diameter.',
        'Set a flush seat using the actual screw and a matched tool on an offcut; do not overdrive.',
        'No full-shank pilot diameter or countersink machining depth is specified here.',
        'Reference: docs/round-panel-countersink-reference.json (nominal US family drawing).',
        '', 'AXIS                                      FROM LEFT     FROM BOTTOM     RECEIVER']
    for row in rows:
        lines.append(f'{row["role"]} {row["name"].rsplit("_", 1)[1]}: '
                     f'{row["from_left_mm"]:.3f} / {row["from_bottom_mm"]:.3f} mm; {row["receiver"]}')
    for i, line in enumerate(lines):
        out.append(f'<text x="35" y="{105+i*27}" font-size="13">{html.escape(line)}</text>')
    return previous.finish_svg(out)


def source_hashes():
    paths = set(Path('mini_moonboard').glob('*.py')) | {
        Path('docs/round-service-wiring-reference.json'), Path('docs/led-wiring-reference.json'),
        Path('docs/ml24z-reference.json'), Path('docs/panel-insert-reference.json'),
        Path('docs/round-panel-countersink-reference.json')}
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def generate(output):
    from . import round_service_frame as model

    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    sources = source_hashes()
    panels, bolts, passages = previous.panel_rows(), previous.bolt_rows(model), passage_rows(model)
    files = {name+'.svg': previous.panel_svg(name, record) for name, record in panels.items()}
    kickers = kicker_hold_rows()
    files.update({name+'-holds.svg': kicker_hold_svg(name, record) for name, record in kickers.items()})
    panels.update(kickers)
    fastening = panel_fastening_rows()
    files.update({name+'-fastening.svg': panel_fastening_svg(name, rows) for name, rows in fastening.items()})
    for name, record in bolts.items():
        svg = previous.bolt_svg(name, record).replace(
            'Gusset bolts and panel screws are separate operations.',
            'No base gusset bolts remain. Panel screws are separate operations.')
        svg = svg.replace('</g></svg>', '<text x="35" y="730" font-size="13">Leg joint: head OUTSIDE, nut INSIDE; retain one washer at each end.</text></g></svg>')
        files[name+'.svg'] = svg
    files.update({row['name']+'.svg': passage_svg(row) for row in passages})
    if source_hashes() != sources:
        raise ValueError('Source changed during round drilling generation')
    output.mkdir(parents=True)
    for name, svg in files.items():
        (output/name).write_text(svg)
    (output/'drilling.json').write_text(json.dumps({'candidate': model.KEY, 'qualified_for_design': False,
        'limits': LIMITS, 'installation_order': 'Panels first; feed harness and install lights afterward',
        'panels': panels, 'panel_fastening_axes': fastening,
        'countersink_reference': 'docs/round-panel-countersink-reference.json', 'leg_bolt_members': bolts, 'circular_passages': passages,
        'panel_kicker_screw_count': sum(isinstance(c, model.timber.PanelScrew) for c in model.connections()),
        'panel_screw_pilots_specified': False}, indent=2)+'\n')
    sections = ''.join('<section>'+svg+'</section>' for svg in files.values())
    (output/'drilling.html').write_text('<!doctype html><meta charset="utf-8"><title>Round passage drilling references</title>'
        '<style>@page{size:A4 landscape;margin:0}body{margin:0}section{break-after:page;width:297mm;height:210mm}'
        'svg{display:block;width:297mm;height:210mm}</style>'+sections)
    if source_hashes() != sources:
        raise ValueError('Source changed during round drilling generation')
    (output/'manifest.json').write_text(json.dumps({'candidate': model.KEY, 'source_sha256': sources,
        'artifact_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}}, indent=2)+'\n')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('docs/round-service-drilling'))
    print(generate(parser.parse_args().output))
