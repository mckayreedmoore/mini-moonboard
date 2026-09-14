"""Equal-scale raw-timber elevations with actual lateral-width comparison."""
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

from mini_moonboard import compact_exterior_brace_frame as exterior
from mini_moonboard import compact_floor_rail_frame as floor

OUTPUT = Path('docs/clear-space-comparison.svg')
SCALE = .25
GROUND = 700.


def main():
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1260" height="1170" viewBox="0 0 1260 1170">',
           '<title>Clear-space candidates: floor rails and exterior knees</title>',
           '<desc>Equal-scale side elevations of actual raw timber, plus separate lateral member-width extents.</desc>',
           '<rect width="1260" height="1170" fill="#f6f4ef"/>',
           ('<style>text{font-family:Arial,sans-serif;fill:#26313a}.title{font-size:26px;font-weight:bold}'
            '.head{font-size:21px;font-weight:bold}.body{font-size:16px}.small{font-size:13px}</style>'),
           '<text x="30" y="38" class="title">Two ways to open the space beneath the climbing face</text>',
           '<text x="30" y="67" class="body">Floor rails: listed conditional checks met · exterior brace: NOT ACCEPTED (contact solve unresolved)</text>']
    for index, (model, heading) in enumerate(((floor, 'Floor-level 2×6 side rails'), (exterior, 'Knees moved outside the panel edges'))):
        column = 30 + index*620
        origin = column+72
        def projected(y,z,origin=origin):
            return origin+y*SCALE,GROUND-z*SCALE
        svg.append(f'<text x="{column}" y="111" class="head">{escape(heading)}</text>')
        raw = {p.name:p for p in model.uncut_wood_parts()}
        names = ['base_side_left','lumber_leg_left','base_header']
        names += [name for name in raw if name.startswith('base_post_')]
        names += [name for name in raw if name.startswith(('base_floor_left','base_knee_left'))]
        for name in names:
            coords = np.unique([(v.Center().y,v.Center().z) for v in raw[name].shape.Vertices()],axis=0)
            hull=ConvexHull(coords)
            points=' '.join(f'{x:.2f},{y:.2f}' for x,y in (projected(*coords[i]) for i in hull.vertices))
            fill='#b99056' if ('floor' in name or 'knee' in name) else '#d0b58c'
            svg.append(f'<polygon points="{points}" fill="{fill}" fill-opacity=".78" stroke="#705b40" stroke-width="1.2"><title>{name}</title></polygon>')
        for c in model.connections():
            if c.kind=='bolt' and 'left' in c.name:
                x,y=projected(c.start.y,c.start.z)
                svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{c.diameter*SCALE/2:.2f}" fill="#354b5e" stroke="white" stroke-width=".5"><title>{c.name}</title></circle>')
        svg.append(f'<line x1="{column}" y1="{GROUND}" x2="{column+565}" y2="{GROUND}" stroke="#69737a"/>')
        svg.append(f'<text x="{column}" y="727" class="small">Climbing face / front ← · side elevations use the same scale</text>')
        explanation = ('Rails sit on the floor and replace both diagonal knees.' if index==0
                       else 'Side view overlaps the legs and knees; lateral separation is below.')
        svg.append(f'<text x="{column}" y="761" class="body">{explanation}</text>')
        svg.append(f'<text x="{column}" y="807" class="head">Left-edge width inset</text>')
        edge_x=column+300
        svg.append(f'<line x1="{edge_x}" y1="822" x2="{edge_x}" y2="1029" stroke="#b2453d" stroke-dasharray="5 4"/>')
        svg.append(f'<text x="{edge_x-115}" y="843" class="small">Outside ←</text>')
        svg.append(f'<text x="{edge_x+15}" y="843" class="small">→ Central climbing space</text>')
        width_names=['base_side_left','lumber_leg_left']
        width_names += (['base_floor_left'] if index==0 else ['base_knee_left_rim','base_knee_left_leg'])
        labels=['4×6 rim','4×6 leg']+(['2×6 floor rail'] if index==0 else ['4×6 rim-end knee','2×6 leg-end knee'])
        for row,(name,label) in enumerate(zip(width_names,labels,strict=True)):
            bb=raw[name].shape.BoundingBox()
            lo,hi=bb.xmin+model.b.HALF,bb.xmax+model.b.HALF
            x1=edge_x+lo*1.75
            y=864+row*37
            svg.append(f'<rect x="{x1:.2f}" y="{y}" width="{(hi-lo)*1.75:.2f}" height="22" fill="#c7a674" stroke="#705b40"/>')
            svg.append(f'<text x="{column+465}" y="{y+16}" class="small">{label}</text>')
            svg.append(f'<text x="{x1+4:.2f}" y="{y+16}" class="small">{hi-lo:.1f} mm</text>')
        svg.append(f'<text x="{column}" y="1048" class="small">Red datum: panel edge X = −1219.2 mm; right side mirrors.</text>')
        note=('Rail occupies 38.1 mm inward of each panel edge.' if index==0
              else 'Knee wood extends 127 mm outward; none lies inside the edge.')
        svg.append(f'<text x="{column}" y="1075" class="body">{note}</text>')
    svg += ['<text x="30" y="1119" class="small">Width insets show actual X extents; member rows are separated for clarity. Insets use their own shared width scale.</text>',
            '<text x="30" y="1145" class="small">Review illustration only. Actual raw timber and bolt-axis centers; no machining or hardware-clearance dimensions are released here.</text>','</svg>']
    data='\n'.join(svg)+'\n'
    ET.fromstring(data)
    OUTPUT.write_text(data)
    print(f'{OUTPUT}: raw geometry projected; XML valid')


if __name__=='__main__':
    main()
