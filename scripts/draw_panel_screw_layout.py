"""Draw the actual round-candidate panel attachment datums for visual review."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from mini_moonboard import panel_grid_v2 as grid
from mini_moonboard import round_panel_layout as layout


def main():
    rows = layout.datums()
    counts = Counter(row['panel'] for row in rows)
    assert len(rows) == 56 and all(n == (4 if p.startswith('kicker') else 12) for p, n in counts.items())
    points = {(row['x'], row['s'], row['panel'].split('_')[0]) for row in rows}
    assert all((-x, s, kind) in points for x, s, kind in points)
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1040" viewBox="0 0 2700 3120">',
                '<rect width="2700" height="3120" fill="white"/>',
                '<g font-family="sans-serif" fill="#18212b">',
                '<text x="130" y="75" font-size="48">Panel screw placement — front view</text>',
                '<text x="130" y="135" font-size="30">12 per main panel; 4 per kicker. Blue dots are attachment screws.</text>',
                '<text x="130" y="190" font-size="28">Mirrored positions; straight principal columns with shared row heights.</text>',
                '<g transform="translate(1350 2730) scale(1 -1)">']
    for x in (-layout.HALF, 0):
        for s in (0, layout.HALF):
            elements.append(f'<rect x="{x}" y="{s}" width="1219.2" height="1219.2" fill="#f5f2eb" stroke="#46525e" stroke-width="5"/>')
        elements.append(f'<rect x="{x}" y="-245" width="1219.2" height="225" fill="#f5f2eb" stroke="#46525e" stroke-width="5"/>')
    for x in (-layout.OUTER_X, -layout.CENTER_X, layout.CENTER_X, layout.OUTER_X):
        elements.append(f'<path d="M {x} 0 V 2438.4" stroke="#ccd3d9" stroke-width="22"/>')
    for x, s in grid.main_tnut_datums().values():
        elements.append(f'<circle cx="{x-layout.HALF}" cy="{s}" r="10" fill="#bcc0c3"/>')
    for row in rows:
        s = row['s'] if row['panel'].startswith('main_') else row['s']-245
        elements.append(f'<circle cx="{row["x"]}" cy="{s}" r="17" fill="#0878b8" stroke="white" stroke-width="3"/>')
    elements += ['</g>',
                 '<text x="130" y="3045" font-size="26">Schematic only; use drilling PDF for dimensions. Kicker shown separated for clarity.</text>',
                 '<text x="130" y="3090" font-size="26" fill="#a12d27">Development layout. Symmetry and screw count do not establish structural adequacy.</text>',
                 '</g></svg>']
    output = Path('docs/round-panel-screw-layout.svg')
    output.write_text('\n'.join(elements)+'\n')
    sources = [Path(__file__), Path(layout.__file__), Path(grid.__file__)]
    output.with_suffix('.json').write_text(json.dumps({
        'candidate': 'round-bore-service-development', 'counts': dict(counts),
        'qualified_for_design': False,
        'source_sha256': {str(p.resolve().relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'artifact_sha256': {output.name: hashlib.sha256(output.read_bytes()).hexdigest()},
    }, indent=2)+'\n')
    print(output)


if __name__ == '__main__':
    main()
