"""Print existing fixed-design part coordinates; stdlib only, no CAD or solve."""
import argparse
import csv
import hashlib
import html
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OLD = HERE.parents[1] / 'shorter-bolts/build-package/geometry-packet'
PASSAGES = ROOT/'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/enclosed-passages-v1'
SOURCES = {}


def source(path, kind='json'):
    data = path.read_bytes()
    SOURCES[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    return json.loads(data) if kind == 'json' else list(csv.DictReader(io.StringIO(data.decode())))


def f(value):
    return f'{0. if abs(value) < .0000005 else value:.3f}'


def vec(values):
    return '(' + ', '.join(f(x) for x in values) + ')'


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def local(member, point):
    return [dot(row, [p-d for p, d in zip(point, member['datum_xyz_mm'])])
            for row in member['basis_LUV_rows_xyz']]


def project(member, origin, direction, plane):
    p = local(member, origin)
    d = [dot(row, direction) for row in member['basis_LUV_rows_xyz']]
    assert abs(d[2]) > .99, 'Panel screw is not normal to saved panel plane'
    t = (plane-p[2])/d[2]
    world = [o+t*v for o, v in zip(origin, direction)]
    return local(member, world), world


def clip(poly, a, b, offset):
    """Intersect an existing rectangular projection with a saved cut plane."""
    result = []
    for p, q in zip(poly, poly[1:]+poly[:1]):
        dp, dq = a*p[0]+b*p[1]-offset, a*q[0]+b*q[1]-offset
        if dp <= 1e-7:
            result.append(p)
        if (dp < -1e-7 and dq > 1e-7) or (dp > 1e-7 and dq < -1e-7):
            t = dp/(dp-dq)
            result.append([p[i]+t*(q[i]-p[i]) for i in (0, 1)])
    assert len(result) >= 3, 'Saved cut planes eliminated the projection'
    return result


def outline(member, q):
    lo, hi = member['finished_local_min_LUV_mm'], member['finished_local_max_LUV_mm']
    poly = [[lo[0], lo[q]], [hi[0], lo[q]], [hi[0], hi[q]], [lo[0], hi[q]]]
    normal = 3-q
    for face in member['finished_planar_faces_with_grain_normal_component']:
        n = face['outward_normal_LUV']
        # Out-of-plane feature faces are listed separately, never hidden in a hull.
        if abs(n[normal]) < 1e-7:
            poly = clip(poly, n[0], n[q], face['plane_offset_local_mm'])
    return poly


def drawing(poly, names, title, marks=()):
    xmin, xmax = min(p[0] for p in poly), max(p[0] for p in poly)
    ymin, ymax = min(p[1] for p in poly), max(p[1] for p in poly)
    sx, sy = 660/max(xmax-xmin, 1), 112/max(ymax-ymin, 1)
    def xy(p):
        return 78+(p[0]-xmin)*sx, 166-(p[1]-ymin)*sy
    pts = ' '.join(f'{x:.3f},{y:.3f}' for x, y in map(xy, poly))
    out = [f'<svg viewBox="0 0 800 245" role="img" aria-label="{html.escape(title)}"><title>{html.escape(title)}</title>',
           f'<text x="18" y="23">{html.escape(title)}</text>',
           f'<polygon points="{pts}" fill="#f1ead9" stroke="#333" stroke-width="1.5"/>',
           '<path d="M78 190H738 M78 184V196 M738 184V196 M49 54V166 M43 54H55 M43 166H55" fill="none" stroke="#666"/>',
           f'<text x="350" y="207">{names[0]} span {f(xmax-xmin)} mm</text>',
           f'<text x="5" y="43">{names[1]} span {f(ymax-ymin)} mm</text>',
           f'<text x="78" y="229">Bounding reference: {names[0]}={f(xmin)}, {names[1]}={f(ymin)}; positive offsets → and ↑</text>']
    for i, p in enumerate(poly):
        x, y = xy(p)
        out.append(f'<circle cx="{x}" cy="{y}" r="2"/><text x="{x+3}" y="{y-5}">C{i+1}</text>')
    for label, point, *diameter in marks:
        x, y = xy(point)
        if diameter:
            out.append(f'<ellipse cx="{x}" cy="{y}" rx="{diameter[0]*sx/2}" ry="{diameter[0]*sy/2}" fill="none" stroke="#b44d00" stroke-width="1.5"/><text x="{x+4}" y="{y-6}" fill="#b44d00">{label}</text>')
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="3" fill="white" stroke="#165f91"/><text x="{x+4}" y="{y+12}" fill="#165f91">{label}</text>')
    return ''.join(out)+'</svg><p class="stations">Corner stations '+ '; '.join(f'C{i+1} {vec(p)}' for i, p in enumerate(poly))+'</p>'


def table(headers, rows):
    return '<table><thead><tr>'+''.join('<th>'+html.escape(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'


def csv_bytes(headers, rows):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=headers, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def build():
    packet = source(OLD/'geometry-packet.json')
    stock = source(OLD/'stock-allocation.csv', 'csv')
    axes = source(HERE/'hardware-axis-crosswalk.csv', 'csv')
    receivers = source(HERE/'receiver-planning.csv', 'csv')
    screws = source(OLD/'panel-screw-axis-planning.csv', 'csv')
    omitted = source(HERE/'omitted-post-hole-mask.csv', 'csv')
    passage_receipt = source(PASSAGES/'geometry.json')
    passages = source(PASSAGES/'passage-datums.csv', 'csv')
    current = source(ROOT/'fea/generated/v11-six-bolt-cleat-v1/geometry-v1/geometry.json')
    assert current['parent_geometry']['receipt']['sha256'] == SOURCES[str((PASSAGES/'geometry.json').relative_to(ROOT))]
    assert passage_receipt['shop_override']['sha256'] == SOURCES[str((PASSAGES/'passage-datums.csv').relative_to(ROOT))]
    for path in [ROOT/'scripts/eoere_builder_layout.py', ROOT/'scripts/eoere_front_posts_4x6.py', Path(__file__)]:
        SOURCES[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    members = {m['member_id']: m for m in packet['members']}
    assert len(members) == 30 and len(receivers) == 136 and len(axes) == 102 and len(screws) == 66
    assert len({r['axis_id'] for r in screws}) == 66
    assert all(r['receiver'] in members for r in receivers)
    ids = {r['axis_id'] for r in axes}
    assert len(ids) == 102 and {r['axis_id'] for r in receivers} == ids
    assert len(omitted) == 4 and not ids.intersection(r['axis_id'] for r in omitted)
    boards = {}
    for row in stock:
        for name in row['member_ids'].split(';'):
            assert name not in boards
            boards[name] = row
    assert len(boards) == 20 and len(stock) == 13
    cuts, screwrows, panelmarks, passagerows, passage_marks = [], [], {}, [], {}
    assert len(passages) == 32 and len({(r['member'], r['service']) for r in passages}) == 32
    assert len({r['member'] for r in passages}) == 8
    assert len(passage_receipt['passages']) == 32
    for row in passages:
        m = members[row['member']]; lo, hi = m['finished_local_min_LUV_mm'], m['finished_local_max_LUV_mm']
        old_profile, current_profile = passage_receipt['profile_overrides'][row['member']], current['profiles'][row['member']]
        assert old_profile['datum_xyz_mm'] == current_profile['datum_xyz_mm'] == m['datum_xyz_mm']
        assert old_profile['basis_grain_u_v_xyz'] == current_profile['basis_grain_u_v_xyz'] == m['basis_LUV_rows_xyz']
        if row['member'].startswith('base_rail_'):
            assert old_profile['finished']['sha256'] == current_profile['finished']['sha256'] == m['finished_BRep']['sha256']
        a, z = [local(m, json.loads(row[k])) for k in ('entry_xyz_mm', 'exit_xyz_mm')]
        centre = [(x+y)/2 for x, y in zip(a, z)]
        assert row['service'].startswith('wire_') and float(row['diameter_mm']) == 38.1
        assert max(abs(x-y) for x, y in zip(centre, json.loads(row['centre_receiver_L_U_V_mm']))) < 1e-7
        assert all(lo[i]-1e-5 <= centre[i] <= hi[i]+1e-5 for i in range(3))
        assert abs(a[0]-z[0])+abs(a[2]-z[2]) < 1e-7
        assert abs(abs(z[1]-a[1])-float(row['through_wood_mm'])) < 1e-7
        assert float(row['grain_offset_mm']) == (40. if row['service'] == 'wire_072_F1_G1' else 0.)
        entry, exit = [[p[i]-lo[i] for i in range(3)] for p in (a, z)]
        passagerows.append(dict(member_id=row['member'], service_id=row['service'], source_opening_diameter_mm=row['diameter_mm'], through_wood_mm=f(float(row['through_wood_mm'])), entry_local_LUV_mm=vec(a), exit_local_LUV_mm=vec(z), entry_positive_LUV_from_finished_min_mm=vec(entry), exit_positive_LUV_from_finished_min_mm=vec(exit), source_entry_world_XYZ_mm=row['entry_xyz_mm'], source_exit_world_XYZ_mm=row['exit_xyz_mm'], retained_grain_shift_mm=row['grain_offset_mm'], source_pointer=str((PASSAGES/'geometry.json').relative_to(ROOT))+'#/passages/'+str(len(passagerows))))
        passage_marks.setdefault(row['member'], []).append((row, centre, a, z))
    for row in screws:
        m = members[row['panel']]
        origin, direction = [json.loads(row[k]) for k in ['CURRENT_origin_xyz_mm_json', 'CURRENT_direction_xyz_json']]
        front, world = project(m, origin, direction, m['finished_local_min_LUV_mm'][2])
        back, backworld = project(m, origin, direction, m['finished_local_max_LUV_mm'][2])
        offsets = [front[i]-m['finished_local_min_LUV_mm'][i] for i in (0, 1)]
        assert all(-1e-5 <= offsets[i] <= m['finished_local_span_LUV_mm'][i]+1e-5 for i in (0, 1))
        assert max(abs(front[i]-back[i]) for i in (0, 1)) < 1e-5
        screwrows.append(dict(axis_id=row['axis_id'], panel=row['panel'], receiver=row['receiver'], front_A_from_Lmin_mm=f(offsets[0]), front_B_from_Umin_mm=f(offsets[1]), front_local_LUV_mm=vec(front), front_world_XYZ_mm=vec(world), backing_local_LUV_mm=vec(back), backing_world_XYZ_mm=vec(backworld), source_origin_XYZ_mm=row['CURRENT_origin_xyz_mm_json'], source_direction_XYZ=row['CURRENT_direction_xyz_json']))
        panelmarks.setdefault(row['panel'], []).append((row['axis_id'], front))
    cards = []
    for index, m in enumerate(packet['members']):
        name = m['member_id']; panel = m['role'] == 'face_panel_reuse'
        own = [r for r in receivers if r['receiver'] == name]
        b = m['basis_LUV_rows_xyz']; lo, hi = m['finished_local_min_LUV_mm'], m['finished_local_max_LUV_mm']
        normal_U = sum(abs(dot(b[1], json.loads(r['axis_direction_world_xyz_json']))) for r in own)
        normal_V = sum(abs(dot(b[2], json.loads(r['axis_direction_world_xyz_json']))) for r in own)
        q = 1 if panel or normal_V > normal_U else 2
        poly = outline(m, q); marks = []
        for j, row in enumerate(own):
            point = json.loads(row['increasing_t_entry_local_LUV_mm_json']); marks.append((f'B{j+1}', [point[0], point[q]]))
        if panel:
            marks = [(f'S{j+1}', [p[0], p[1]]) for j, (_, p) in enumerate(panelmarks[name])]
        own_passages = passage_marks.get(name, [])
        assert not own_passages or q == 2, 'Service circles require the L/V view normal to the bore'
        marks += [(f'P{j+1}', [centre[0], centre[q]], 38.1) for j, (_, centre, _, _) in enumerate(own_passages)]
        board = boards.get(name, {})
        cuts.append(dict(member_id=name, role=m['role'], quantity=1, stock=m['nominal_stock_planning'], board_id=board.get('board_id', ''), stock_length_ft=board.get('nominal_length_ft', ''), finished_L_min_mm=f(lo[0]), finished_L_max_mm=f(hi[0]), finished_L_span_mm=f(hi[0]-lo[0]), finished_U_span_mm=f(hi[1]-lo[1]), finished_V_span_mm=f(hi[2]-lo[2]), datum_XYZ_mm=vec(m['datum_xyz_mm']), basis_LUV_rows_XYZ=json.dumps(b, separators=(',', ':')), source_member_pointer=f'{(OLD/"geometry-packet.json").relative_to(ROOT)}#/members/{index}'))
        kind = 'face panel/kicker' if panel else ('solid timber' if m['role'] == 'sawn_timber' else 'plywood cleat leaf')
        card = [f'<article class="part" id="{name}"><h2>{html.escape(name)}</h2>',
                f'<p>{kind}; quantity 1; stock {m["nominal_stock_planning"].replace("_", " ")}; board {board.get("board_id", "plywood piece; no sheet nesting assigned")}. Finished L/U/V spans: {vec(m["finished_local_span_LUV_mm"])} mm.</p>',
                f'<p>Saved datum XYZ {vec(m["datum_xyz_mm"])}. Positive L/U/V vectors: '+ '; '.join(vec(x) for x in b)+'. L is the saved grain/reference direction.</p>',
                '<p>The drawing reference is the positive-offset finished bounding corner, not necessarily a material corner. A beveled-end saved datum can be virtual. Use the numbered material corner stations to identify the part; do not mirror left/right.</p>',
                drawing(poly, ('L', 'LUV'[q]), f'{name}: '+('climbing/head face, Vmin' if panel else 'finished end-cut reference projection'), marks)]
        if name.startswith('lumber_leg_'):
            # Source finished leg slope face: no convex hull or filled-in recess.
            ramp = [p for face in m['finished_planar_faces_with_grain_normal_component'] if abs(face['outward_normal_LUV'][1]) > .9 for p in face['boundary_vertices_LUV_mm']]
            assert ramp
            start, stop = min(p[0] for p in ramp), max(p[0] for p in ramp)
            thin = min(p[1] for p in ramp)
            recess = [[lo[0], lo[1]], [hi[0], lo[1]], [hi[0], hi[1]], [stop, hi[1]], [start, thin], [lo[0], thin]]
            card += [drawing(recess, ('L', 'U'), 'Separate finished thickness/recess projection'), f'<p>1:12 open-bottom inner-face recess: L {f(start)} / U {f(thin)} → L {f(stop)} / U {f(hi[1])}; runout 457.2 mm, maximum removal 38.1 mm. The cut spans V depth 139.7 mm; removal depth is not saw through-cut thickness. End bevels are shown in the L/V view.</p>']
        if name.startswith('base_post_outer_'):
            a, z, bevel = hi[1], hi[2], 9.525
            section = [[0, 0], [a, 0], [a, z-bevel], [a-bevel, z], [0, z]] if name.endswith('left') else [[0, 0], [a, 0], [a, z], [bevel, z], [0, z-bevel]]
            card += [drawing(section, ('U', 'V'), 'Finished outer-post cross-section; full height bevel'), '<p>9.525×9.525 mm, 45° longitudinal corner bevel for full L 0–238.9 mm. Left: U 88.9/V 139.7 corner; right: U 0/V 139.7 corner. This feature is absent from raw box vertices.</p>']
        if panel:
            card += [f'<p>Physical climbing/screwhead face: Vmin={f(lo[2])}; timber/backing face: Vmax={f(hi[2])}. S labels use front-face projection along each existing screw axis, never mirrored. Front/back L/U centers coincide for these normal axes.</p>', table(['S', 'Current screw ID', 'Receiver', 'Positive A/B from Lmin/Umin (mm)'], [(j+1, aid, next(r['receiver'] for r in screws if r['axis_id']==aid), vec([pt[0]-lo[0], pt[1]-lo[1]])) for j, (aid, pt) in enumerate(panelmarks[name])])]
            if name.startswith('kicker_'):
                edge = m['finished_planar_faces_with_grain_normal_component'][0]['boundary_vertices_LUV_mm']
                card += ['<p>Whole 277 mm front outline shown. Small modeled top-edge relief is not enlarged into a new cut or reconstructed from a hull. Existing end-section U/V vertices: '+ '; '.join(vec(p[1:]) for p in edge)+'. This front view alone does not specify that tiny through-thickness edge detail.</p>']
        if own:
            card += [table(['B', 'Current bolt axis', 'A entry L/U/V (mm)', 'B exit L/U/V (mm)', 'Positive projected entry offsets (mm)'], [(j+1, r['axis_id'], vec(json.loads(r['increasing_t_entry_local_LUV_mm_json'])), vec(json.loads(r['increasing_t_exit_local_LUV_mm_json'])), vec([json.loads(r['increasing_t_entry_local_LUV_mm_json'])[k]-lo[k] for k in (0, q)])) for j, r in enumerate(own)]), '<p>Entry/exit follow increasing saved shaft parameter; they are not two independent drilling targets or a selected approach side. Current fitting registration, actual finished lands and a supported clamped transfer govern. Blue marks are axis references, not bore diameters, drill bits or bushing sizes.</p>']
        if own_passages:
            card += ['<h3>Retained enclosed service passages</h3><p>Orange P outlines show the actual source Ø38.1 mm service openings in the L/V projection, with the same adjusted drawing proportions. These are separate from blue bolt/screw axis symbols and occupied bolt-bore envelopes. The recorded service-opening size is not a new drill-selection policy. Entry/exit follow the saved service route; the coordinate table retains the current finished bounding reference.</p>', table(['P', 'Service ID', 'Entry L/U/V (mm)', 'Exit L/U/V (mm)', 'Positive entry L/U/V offsets (mm)', 'Positive exit L/U/V offsets (mm)'], [(j+1, r['service'], vec(a), vec(z), vec([a[k]-lo[k] for k in range(3)]), vec([z[k]-lo[k] for k in range(3)])) for j, (r, _, a, z) in enumerate(own_passages)]), '<p>One current passage per principal and five per rail. F1–G1 retains its source +40 mm grain shift; older front-open channels and ten superseded T-nut recesses are not marked. Six rail finished solids match the passage receipt; the two principals inherit its passages through later bolt/end revisions with unchanged datum/basis.</p>']
        faces = m['finished_planar_faces_with_grain_normal_component']
        card += [table(['Saved cut-face ref', 'Outward normal L/U/V', 'Offset n·(L,U,V)=offset (mm)', 'Boundary L/U/V stations (mm)'], [(str(face['finished_BRep_face_index_zero_based'])+' (historical source only)', vec(face['outward_normal_LUV']), f(face['plane_offset_local_mm']), '; '.join(vec(p) for p in face['boundary_vertices_LUV_mm'])) for face in faces]), '<p class="small">Source member '+str(index)+'; finished-BRep SHA256 '+m['finished_BRep']['sha256']+'. Face numbering locates that source only. Out-of-projection cut faces remain listed above. No hole, recess or service feature may be inferred absent from an end-face subset.</p></article>']
        cards.append(''.join(card))
    cutdata = csv_bytes(list(cuts[0]), cuts); screwdata = csv_bytes(list(screwrows[0]), screwrows)
    passagedata = csv_bytes(list(passagerows[0]), passagerows)
    metadata = dict(candidate='v11-six-bolt-cleat-v1', counts=dict(parts=30, timbers=20, plywood_leaves=4, face_panels=6, stock_boards=13, receiver_rows=136, bolt_axes=102, screw_axes=66, omitted_axes=4, service_passages=32, service_hosts=8), sources=SOURCES, csv_sha256={'cut-list.csv': hashlib.sha256(cutdata).hexdigest(), 'screw-layout.csv': hashlib.sha256(screwdata).hexdigest(), 'service-passage-layout.csv': hashlib.sha256(passagedata).hexdigest()})
    intro = '<h1>Fixed 102-bolt design: part reference sheets</h1><p>30 parts; 102 bolts; 136 receiver references; 66 existing panel/kicker screw axes; 32 retained Ø38.1 mm service passages in eight timbers. These sheets present the retained geometry and do not resolve recorded exceedances or physical fit. Current build guide governs scope; four omitted near-post axes are never marked.</p><p>All dimensions mm. Diagram proportions are adjusted for readability: not 1:1 templates or automatic saw settings. Displayed coordinates round the source to three decimals, not a machining tolerance. L/U/V values retain saved signs; A/B offsets start at the finished bounding reference. L arrows follow grain/reference; L is world X for the existing face-panel frame, and world Z for cleat face-grain orientation.</p><p>Panel marks show climbing/head-face Vmin; Vmax is the backing reference. Use current 102-axis hardware/receiver tables and omission mask; no old SPAX instructions, spacers, or occupied-CAD bit selection transfers. Hold/LED templates are supplied separately.</p>'
    style = 'body{font:14px Arial,sans-serif;color:#17232c;max-width:1000px;margin:24px auto;padding:0 12px}h2{font-size:22px}p{line-height:1.35}svg{width:100%;font:12px Arial}table{border-collapse:collapse;width:100%;font-size:11px;margin:8px 0}td,th{border:1px solid #bbb;padding:4px;text-align:left;overflow-wrap:anywhere}th{background:#eee}.small,.stations{font-size:11px}.part{border-top:2px solid #546e7a;margin-top:28px;padding-top:10px;break-before:page}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:10px}@media print{body{margin:0;max-width:none;padding:0;font-size:11px}h2{font-size:18px}table{font-size:8px}tr,svg{break-inside:avoid}.part{margin-top:0}svg{max-height:190px}.small,.stations{font-size:9px}}@page{size:A4;margin:12mm}'
    footer = '<footer><h2>Source/count receipt</h2><p>No CAD, mesh, solve, source installation or frozen table is regenerated. The current omission mask removes four axes; counts above are asserted by the generator. Source coordinates are unobserved design references.</p><pre>'+html.escape(json.dumps(metadata, indent=2))+'</pre></footer>'
    document = '<!doctype html><html lang="en"><meta charset="utf-8"><title>102-bolt part references</title><style>'+style+'</style><body>'+intro+''.join(cards)+footer+'<script type="application/json" id="part-reference-metadata">'+json.dumps(metadata, sort_keys=True).replace('<', '\\u003c')+'</script></body></html>\n'
    assert len(document.encode()) < 250_000
    return {'cut-list.csv': cutdata, 'screw-layout.csv': screwdata, 'service-passage-layout.csv': passagedata, 'part-reference-sheets.html': document.encode()}, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Compare existing outputs without writing')
    args = parser.parse_args(); outputs, metadata = build()
    for name, payload in outputs.items():
        path = HERE/name
        if args.check:
            assert path.read_bytes() == payload, f'Output differs: {name}'
        else:
            path.write_bytes(payload)
    print(json.dumps({'counts': metadata['counts'], 'outputs': {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in outputs.items()}, 'check_only': args.check}))


if __name__ == '__main__':
    main()
