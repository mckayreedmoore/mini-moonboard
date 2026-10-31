"""Export only the retained T-nut/LED grid as current front-face dimensions.

No CAD imports, model construction, screws or historical fastening rows.
The saved current descriptor below verifies every world-X and face-height
coordinate, including the three right panels repaired by the fixed-grid adapter
and the already retained 5 mm outward move of light_G2. No new layout is selected.
Current feature source:
fea/generated/v11-six-bolt-cleat-v1/mechanics/analysis-v1/four-hosts/a12-forward/field.json
SHA256: 290c35ca9d20e19316a9719f2e0090783f122103c2ac15716a91475b2af70010

Front means the climbing face; left is the viewer's left. TOP/DOWN or BOTTOM/UP
is retained from the grid table. TOP uses the current finished bounding reference,
including the kicker's 277 mm top datum, not its tiny through-thickness edge relief.
The 11.1125/13 mm openings remain the existing product-nominal hole assumptions.
"""
import argparse
import ast
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCES = {
    'docs/round-service-drilling/drilling.json':
        'd8d13dea9f9451f4327bfc883a575988bb8e2edcd476fc3e3c1d69c09fc074a3',
    'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/build-package/geometry-packet/geometry-packet.json':
        'd8a1fc555d79b92debc3ea9536837093847baac0b1ad15e33462746f3cecdce0',
    'fea/generated/v11-six-bolt-cleat-v1/mechanics/analysis-v1/four-hosts/a12-forward/field.json':
        '290c35ca9d20e19316a9719f2e0090783f122103c2ac15716a91475b2af70010',
    'mini_moonboard/wood_joint_panel_machining.py':
        '1928e32ba5b5e75caca99abb42e5d5b01822d6697c6f892dda38650cca302afd',
    'mini_moonboard/panel_grid_v2.py':
        '666e0e5c5daa70eb08ad9c49312a5b4478bc20e7d4d58cfb5062ad3c4be96fe8',
    'scripts/wood_joint_wj24_led_clearance.py':
        '4c33379985baaf4dd19b0909abbd1a9f361fd8fe50c5d91260167c74425f35a9',
}


def source(index):
    path, expected = list(SOURCES.items())[index]
    data = (ROOT/path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == expected, path
    return json.loads(data) if path.endswith('.json') else data.decode()


def number(value):
    return f'{value:.4f}'.rstrip('0').rstrip('.')


def build():
    panels = source(0)['panels']  # Deliberately never read panel_fastening_axes.
    packet = source(1)
    machining = source(2)['source_inputs']['current_panel_machining_descriptors']
    source(3); source(4)  # Bind the existing fixed-grid implementation, no import.
    moves = ast.parse(source(5))
    g2_move = ast.literal_eval(next(n.value for n in moves.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'G2_TRANSLATION_MM' for t in n.targets)))
    assert g2_move == (5., 0., 0.)
    members = {r['member_id']: r for r in packet['members'] if r['role'] == 'face_panel_reuse'}
    features = {(r['panel'], r['identity']): r for r in machining['features']
                if r['kind'] in ('tnut', 'light')}
    assert len(packet['members']) == 30 and len(members) == len(panels) == 6
    assert len(features) == 274 and machining['feature_counts']['conditional_screw_clearance'] == 66
    rows, seen = [], set()
    for name, old in panels.items():
        member = members[name]
        datum, basis = member['datum_xyz_mm'], member['basis_LUV_rows_xyz']
        lo, hi = member['finished_local_min_LUV_mm'], member['finished_local_max_LUV_mm']
        width, height = hi[0]-lo[0], hi[1]-lo[1]
        assert abs(width-1217.6125) < 1e-7 and basis[0] == [1., 0., 0.]
        assert (old['datum_edge'], old['measurement_direction']) in [('TOP', 'DOWN'), ('BOTTOM', 'UP')]
        for row in old['rows']:
            if row['kind'] not in ('T-nut', 'LED'):
                continue
            diameter = {'T-nut': 11.1125, 'LED': 13.}[row['kind']]
            prefix = 'hold_tnut_kicker_' if name.startswith('kicker_') else 'hold_tnut_main_'
            identity = (prefix if row['kind'] == 'T-nut' else 'light_') + row['label']
            feature = features[name, identity]
            assert feature['diameter_mm'] == row['diameter_mm'] == diameter
            # Old local X -> full-grid X -> world X; current datum then sets the
            # front-left offset. The output uses the verified current feature X.
            grid_x = row['from_left_mm'] + (1219.2 if name.endswith('_right') else 0.)
            moved = identity == 'light_G2'
            expected_world_x = grid_x-1219.2 + (g2_move[0] if moved else 0.)
            assert abs(feature['start_xyz_mm'][0]-expected_world_x) < 1e-7, identity
            left = feature['start_xyz_mm'][0] - datum[0] - lo[0]
            distance = row.get('from_datum_edge_mm', row.get('from_top_mm'))
            local_u = hi[1]-distance if old['datum_edge'] == 'TOP' else lo[1]+distance
            actual_u = sum(b*(p-d) for b, p, d in zip(basis[1], feature['start_xyz_mm'], datum))
            assert abs(local_u-actual_u) < 1e-6, (name, identity, local_u, actual_u)
            assert all(abs(sum(b*d for b, d in zip(axis, feature['direction_xyz']))) < 1e-8
                       for axis in basis[:2]), identity
            radius = diameter/2
            assert radius < left < width-radius and lo[1]+radius < local_u < hi[1]-radius
            seen.add((name, identity))
            rows.append(dict(panel=name, label=row['label'], kind=row['kind'], diameter_mm=number(diameter),
                view='CLIMBING_FACE_FRONT', from_left_mm=number(left), datum_edge=old['datum_edge'],
                measurement_direction=old['measurement_direction'], from_datum_edge_mm=number(distance),
                current_panel_width_mm=number(width), current_panel_height_mm=number(height),
                current_feature_id=identity, diameter_basis='RECORDED_PRODUCT_NOMINAL',
                layout_note='RETAINED_G2_5_MM_OUTWARD_MOVE' if moved else ''))
    assert seen == set(features) and Counter(r['kind'] for r in rows) == {'T-nut': 142, 'LED': 132}
    assert len({(r['panel'], r['kind'], r['label']) for r in rows}) == 274
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return out.getvalue().encode(), Counter((r['panel'], r['kind']) for r in rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Compare the saved CSV without writing.')
    args = parser.parse_args()
    data, counts = build()
    path = HERE/'panel-opening-layout.csv'
    if args.check:
        assert path.read_bytes() == data, 'Saved opening layout differs from current source-bound export'
    else:
        path.write_bytes(data)
    print(f'{path.relative_to(ROOT)}: 142 T-nut holes, 132 LED holes, 274 total; six current faces; no screws.')
    for (panel, kind), count in counts.items():
        print(f'{panel}: {kind} {count}')
