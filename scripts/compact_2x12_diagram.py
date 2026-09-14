"""Geometry-backed side-elevation comparison; not a drilling drawing."""
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

from mini_moonboard import compact_2x12_staggered_frame as alternative
from mini_moonboard import compact_spliced_trimmed as current

OUTPUT = Path('docs/compact-2x12-comparison.svg')
SCALE = 0.275
GROUND = 755.0


def main():
    pieces = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="960" viewBox="0 0 1200 960">',
              '<title>Current braced frame and unbraced 2x12 alternative</title>',
              ('<desc>Equal-scale side elevations derived from actual raw timber shapes. '
              'The separate unbraced alternative fails the conditional bolt resistance check.</desc>'),
              '<rect width="1200" height="960" fill="#f6f4ef"/>',
              ('<style>text{font-family:Arial,sans-serif;fill:#232c33}.title{font-size:25px;font-weight:bold}'
              '.heading{font-size:20px;font-weight:bold}.body{font-size:16px}.small{font-size:13px}</style>'),
              '<text x="34" y="39" class="title">Fewer parts, but the unbraced joint exceeds its reference</text>',
              '<text x="34" y="67" class="body">Equal-scale side elevations · actual raw timber geometry · bolt-axis centers shown</text>']
    counts = []
    for index, (model, title, status, status_color) in enumerate((
        (current, 'Current selected braced candidate', 'Retain current viable DIY candidate', '#236d50'),
        (alternative, 'Separate unbraced 2×12 alternative', 'Bolt demand / reference = 2.08 > 1.00', '#b13d33'),
    )):
        origin = 100 + index * 580
        def point(y, z, origin=origin):
            return origin + y * SCALE, GROUND - z * SCALE
        pieces.append(f'<text x="{34+index*580}" y="106" class="heading">{escape(title)}</text>')
        pieces.append(f'<text x="{34+index*580}" y="135" class="body" style="fill:{status_color}">{escape(status)}</text>')
        parts = [part for part in model.uncut_wood_parts()
                 if part.name in ('base_side_left', 'lumber_leg_left', 'base_header',
                                  'base_knee_left_rim', 'base_knee_left_leg')
                 or part.name.startswith('base_post_')]
        counts.append(len(parts))
        for part in parts:
            coords = np.unique(np.array([(v.Center().y, v.Center().z) for v in part.shape.Vertices()]), axis=0)
            hull = ConvexHull(coords)
            polygon = ' '.join(f'{x:.3f},{y:.3f}' for x,y in (point(*coords[i]) for i in hull.vertices))
            fill = '#c7a675' if 'knee' not in part.name else '#d8be95'
            pieces.append(f'<polygon points="{polygon}" fill="{fill}" fill-opacity="0.76" stroke="#66513c" stroke-width="1.2">'
                          f'<title>{escape(part.name)}</title></polygon>')
        bolts = [connection for connection in model.connections()
                 if connection.kind == 'bolt' and 'left' in connection.name]
        for connection in bolts:
            x, y = point(connection.start.y, connection.start.z)
            pieces.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{connection.diameter*SCALE/2:.3f}" '
                          f'fill="#374958" stroke="#fff" stroke-width="0.6"><title>{escape(connection.name)}</title></circle>')
        pieces.append(f'<line x1="{origin-65}" y1="{GROUND}" x2="{origin+475}" y2="{GROUND}" stroke="#6d7477" stroke-width="1.4"/>')
        pieces.append(f'<text x="{origin-65}" y="779" class="small">Climbing face / front ←</text>')
        if index == 0:
            pieces.append('<text x="34" y="818" class="body">4×6 legs and rims · two spliced 2×6 knees</text>')
            pieces.append('<text x="34" y="844" class="body">20 complete bolt stacks across both sides</text>')
        else:
            centre, foot, _grain, _, rim = model.axes()
            reference = centre-rim*model.JOINT_SHIFT_ALONG_RIM_MM
            a=point(reference.y,reference.z);b=point(centre.y,centre.z)
            pieces.append(f'<line x1="{a[0]+29:.2f}" y1="{a[1]:.2f}" x2="{b[0]+29:.2f}" y2="{b[1]:.2f}" '
                          'stroke="#b13d33" stroke-width="2"/>')
            pieces.append(f'<text x="{a[0]+35:.2f}" y="{a[1]+15:.2f}" class="small">225 mm</text>')
            pieces.append(f'<text x="{a[0]+35:.2f}" y="{a[1]+32:.2f}" class="small">lower joint</text>')
            x,y=point(foot.y,foot.z)
            pieces.append(f'<line x1="{x:.2f}" y1="{y}" x2="{x:.2f}" y2="{y-115}" stroke="#777" stroke-dasharray="4 4"/>')
            pieces.append(f'<text x="{x-108:.2f}" y="{y-99}" class="small">17.5° from vertical</text>')
            pieces.append('<text x="614" y="818" class="body">Single 2×12 legs: 38.1 × 285.75 mm</text>')
            pieces.append('<text x="614" y="844" class="body">4×6 rims retained · 8 bolts total · no knee braces</text>')
    pieces.extend(['<text x="34" y="894" class="body">Alternative result: 4,162 N bolt demand / 2,002 N conditional reference. Current candidate stays selected.</text>',
                   '<text x="34" y="923" class="small">Review illustration only. No machining dimensions, additional rating or construction release for the alternative.</text>',
                   '</svg>'])
    if min(counts) < 4:
        raise ValueError('Missing structural members from elevation')
    content = '\n'.join(pieces)+'\n'
    ET.fromstring(content)
    OUTPUT.write_text(content)
    print(f'{OUTPUT}: {counts} raw member projections; XML valid')


if __name__ == '__main__':
    main()
