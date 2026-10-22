"""Render current paired-frame stock nesting and dimensioned member sheets."""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from html import escape
import io
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

from scripts.eoere_builder_layout import ROOT, load_sources, number, validate

PACKET = Path('docs/bolted-frame-development/paired-frame-v1')
KERF, TRIM = 3.175, 6.0


def csv_bytes(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def stock_rows(data):
    members = {r['member']: r for r in data['members'] if r['kind'] == 'timber' and not r['member'].startswith('eoere_cleat_')}
    allocations = [
        (8, [f'base_floor_{s}', f'outboard_leg_packer_{s}']) for s in ('left', 'right')
    ] + [(8, [f'base_rail_{level}_left', f'base_rail_{level}_right'])
         for level in ('bottom', 'service_lower', 'service_upper')]
    allocations += [(10, [f'base_principal_center_{s}', f'base_post_center_{s}']) for s in ('left', 'right')]
    allocations += [(10, ['base_header']), (10, ['base_rail_top']), (10, ['outboard_knee_left', 'outboard_knee_right'])]
    allocations += [(8, [f'lumber_leg_{s}', f'base_post_outer_{s}']) for s in ('left', 'right')]
    allocations += [(10, [f'base_side_{s}']) for s in ('left', 'right')]
    result, seen = [], []
    for index, (feet, names) in enumerate(allocations, 1):
        rows = [members[n] for n in names]
        sections = {tuple(sorted(float(r[k]) for k in ('nominal_blank_depth_mm', 'nominal_blank_thickness_mm'))) for r in rows}
        assert len(sections) == 1, 'One stick must supply one stock section'
        section = next(iter(sections))
        nominal = next(label for dimensions, label in [((38.1, 139.7), '2x6'), ((38.1, 184.15), '2x8'), ((38.1, 234.95), '2x10'), ((88.9, 139.7), '4x6')]
                       if np.allclose(dimensions, section, atol=1e-5))
        used = sum(float(r['nominal_blank_length_mm']) for r in rows) + len(rows)*KERF + 2*TRIM
        assert used < feet*304.8, 'Nominal stock cannot supply the listed blanks plus trim and kerf'
        result.append({'stock_id': f'S{index:02d}', 'US_nominal_section': nominal, 'US_nominal_length_ft': feet,
                       'nominal_length_mm': feet*304.8, 'actual_section_mm': ' x '.join(map(number, section)),
                       'members_in_cut_order': ';'.join(names), 'raw_blank_lengths_mm': ';'.join(number(r['nominal_blank_length_mm']) for r in rows),
                       'kerf_per_cut_mm': KERF, 'end_trim_each_mm': TRIM, 'conservative_total_used_mm': used,
                       'nominal_remainder_mm': feet*304.8-used, 'Actual': '', 'Disposition': ''})
        seen.extend(names)
    assert len(result) == 14 and len(seen) == len(set(seen)) == len(members) == 24
    return result


def hardware_rows(data):
    rows = []
    for (diameter, length, grade, sku), count in sorted(Counter(
        (number(r['selected_diameter_mm']), number(r['selected_underhead_length_mm']), r['selected_bolt_grade'], r['selected_product'])
        for r in data['selected']).items()):
        rows.append({'item': 'frame bolt', 'quantity': count, 'dimensions_mm': diameter+' x '+length,
                     'grade_or_product': grade, 'SKU': sku, 'Actual': '', 'Disposition': ''})
    for kind, column in [('matching nut', 'selected_nut_SKU'), ('USS washer', 'selected_washer_SKU')]:
        for sku, count in sorted(Counter(r[column] for r in data['selected']).items()):
            rows.append({'item': kind, 'quantity': count*(2 if kind == 'USS washer' else 1), 'dimensions_mm': '',
                         'grade_or_product': 'Use the exact stack material/dimension requirements', 'SKU': sku, 'Actual': '', 'Disposition': ''})
    for item, count, dimensions, product, sku in [
        ('factory spacer', sum(int(r['spacer_piece_count']) for r in data['selected']), '12.7 long; ID10.31875; OD19.05', 'Matched stack; conditional33ksi steel requirement', '13731'),
        ('factory angle', 26, '88.9 arms and width; t6.35; Ri6.35; eight10mm holes', 'Eoere conditional geometry/Fy235MPa/Fu370MPa; seven4-packs give two spares', ''),
        ('panel/kicker screw', 66, 'Purchased specification', 'Hillman42605; strength issues deferred', '42605'),
        ('independent plywood leaf', 4, '609.6 x203.2 x28.575 nominal; actual>=27', 'APA48ocPS1; >=5plies; Group1; strength along609.6', ''),
    ]:
        rows.append({'item': item, 'quantity': count, 'dimensions_mm': dimensions, 'grade_or_product': product,
                     'SKU': sku, 'Actual': '', 'Disposition': ''})
    return rows


def drawing(name, profile, holes):
    vertices = np.asarray(profile['vertices_luv_mm'])
    assert holes
    travel = np.array([[float(r[f'exit_in_receiver_{c}_mm'])-float(r[f'entry_in_receiver_{c}_mm']) for c in ('u', 'v')] for r in holes])
    normal = int(np.argmax(np.max(abs(travel), axis=0)))+1
    cross = 3-normal
    assert np.max(abs(travel[:, 2-normal])) < 1e-5, 'Sheet requires one normal drilling direction'
    points = np.unique(np.round(vertices[:, [0, cross]], 7), axis=0)
    outline = points[ConvexHull(points).vertices]
    lo, hi = points.min(axis=0), points.max(axis=0)
    scale = min(1030/(hi[0]-lo[0]), 210/(hi[1]-lo[1]))
    def xy(L, C):
        return 80+(L-lo[0])*scale, 115+(hi[1]-C)*scale
    height = 400+27*len(holes)
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1260 {height}" role="img" aria-labelledby="title desc">',
             '<style>text{font:17px sans-serif;fill:#111827}.small{font-size:14px}.title{font-size:25px;font-weight:600}.line{stroke:#334155;stroke-width:1.5;fill:none}</style>',
             f'<title id="title">{escape(name)} — millimetre datum and drill sheet</title>',
             '<desc id="desc">Raw end projection and numbered receiver axes. Exact drilling coordinates appear below. Do not scale this drawing.</desc>',
             '<rect width="1260" height="100%" fill="white"/>',
             f'<text class="title" x="35" y="40">{escape(name)}</text>',
             f'<text x="35" y="71">Raw blank: {escape(" x ".join(number(v) for v in profile["blank_mm"]))} mm · US stock · conditional development</text>',
             '<text class="small" x="35" y="95">Axes are symbols. Use the numeric dimensions and drilling table; do not scale-drill or scale-cut this sheet.</text>',
             '<polygon points="'+' '.join(f'{x:.4f},{y:.4f}' for x,y in (xy(*p) for p in outline))+'" fill="#e8dcc4" stroke="#334155" stroke-width="1.5"/>']
    for i, r in enumerate(holes, 1):
        C = 'u' if cross == 1 else 'v'
        x,y = xy(float(r['entry_in_receiver_l_mm']), float(r[f'entry_in_receiver_{C}_mm']))
        lines += [f'<circle cx="{x:.4f}" cy="{y:.4f}" r="4" fill="white" stroke="#b91c1c"/>',
                  f'<text class="small" x="{x+5:.4f}" y="{y-6:.4f}">{i}</text>']
    lines += [f'<text x="35" y="353">View along {"U" if normal==1 else "V"}; plot L against {"U" if cross==1 else "V"}. Coordinates retain the source datum and signs.</text>',
              '<text class="small" x="35" y="377">Raw end projection only. Retain the specified1:12 recess, bevels and service openings; see the assembly guide and passage sheet.</text>',
              '<text class="small" x="35" y="400">No. / shaft identity</text><text class="small" x="480" y="400">Entry L, U, V (mm)</text><text class="small" x="850" y="400">Exit L, U, V (mm)</text>']
    for i,r in enumerate(holes, 1):
        def coordinates(which):
            return '('+', '.join(number(r[f'{which}_in_receiver_{c}_mm']) for c in ('l','u','v'))+')'
        y = 400+27*i
        lines += [f'<text class="small" x="35" y="{y}">{i}. {escape(r["axis_id"])}</text>',
                  f'<text class="small" x="480" y="{y}">{coordinates("entry")}</text>',
                  f'<text class="small" x="850" y="{y}">{coordinates("exit")}</text>']
    lines.append('</svg>')
    return ('\n'.join(lines)+'\n').encode()


def outputs(data):
    validate(data)
    assert len(data['selected']) == data['expected_bolt_count']
    assert len(data['holes']) == data['expected_receiver_count']
    packet = Path(data['shop_result']['path']).parent
    result = {packet/'stock-nesting.csv': csv_bytes(stock_rows(data)), packet/'hardware-totals.csv': csv_bytes(hardware_rows(data))}
    names = sorted({r['receiver'] for r in data['holes']})
    assert len(names) == 28
    for name in names:
        result[packet/'drawings'/(name+'.svg')] = drawing(name, data['profiles'][name], [r for r in data['holes'] if r['receiver']==name])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    data = load_sources()
    result = outputs(data)
    for path, payload in result.items():
        target = ROOT/path
        if args.write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        elif not target.exists() or target.read_bytes() != payload:
            raise SystemExit('Shop output differs: '+str(path))
    print(f'{len(result)-2} member sheets;14 stock sticks;{len(data["selected"])} bolts;66 screws;{sum(map(len,result.values()))} generated bytes verified')


if __name__ == '__main__':
    main()
