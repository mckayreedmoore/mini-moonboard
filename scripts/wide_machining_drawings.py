"""Dimensioned local orthographic references, not scale-certified cut templates."""
import csv
import hashlib
import html
import json
from pathlib import Path

from mini_moonboard import wide_frame as frame
from mini_moonboard.wide_machining import datum, to_local

DIRECTORY = Path("docs/wide-machining/drawings")


def vertices(part, axes):
    return sorted({tuple(round(v, 8) for v in to_local(p.toTuple(), axes)) for p in part.shape.Vertices()})


def drawing(part, axes):
    # All raw-form edges are projected, including rear/hidden edges. Machining
    # reservations are in the CSVs; this intentionally is not a CNC outline.
    paths = []
    for edge in part.shape.Edges():
        count = 2 if edge.geomType() == "LINE" else 65
        paths.append([to_local(edge.positionAt(i/(count-1)).toTuple(), axes) for i in range(count)])
    extents = axes["extents_mm"]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="540" viewBox="0 0 1200 540">',
           '<rect width="1200" height="540" fill="white"/>',
           '<g font-family="sans-serif" fill="#202830">',
           f'<text x="24" y="28" font-size="19">{html.escape(part.name)}</text>',
           '<text x="24" y="51" font-size="13">LOCAL REFERENCE — all raw edges shown; not a cutting template or manufacturing approval</text>']
    for column, (u, v) in enumerate(((0, 1), (0, 2), (1, 2))):
        scale = min(310/extents[u], 310/extents[v])
        x0, y0 = 50+400*column, 405
        width, height = extents[u]*scale, extents[v]*scale
        def point(p, x0=x0, y0=y0, u=u, v=v, scale=scale):
            return x0+p[u]*scale, y0-p[v]*scale
        out.append(f'<text x="{x0}" y="80" font-size="15">{html.escape(axes["axis_labels"][u])} / {html.escape(axes["axis_labels"][v])}</text>')
        out.append(f'<rect x="{x0}" y="{y0-height:.4f}" width="{width:.4f}" height="{height:.4f}" fill="none" stroke="#8794a0" stroke-dasharray="5 4"/>')
        for path in paths:
            coords = " ".join(f"{x:.4f},{y:.4f}" for x, y in map(point, path))
            out.append(f'<polyline points="{coords}" fill="none" stroke="#253f50" stroke-width="1"/>')
        labels = {}
        for index, vertex in enumerate(vertices(part, axes), 1):
            xy = tuple(round(v, 3) for v in point(vertex))
            labels.setdefault(xy, []).append(str(index))
        occupied = [(x0-5, y0-18, x0+55, y0+4)]
        for (x, y), indices in labels.items():
            label = "/".join(indices)
            box = (x+4, y-15, x+4+5*len(label), y-3)
            if any(box[0] < b[2]+3 and box[2]+3 > b[0] and box[1] < b[3]+3 and box[3]+3 > b[1] for b in occupied):
                continue
            occupied.append(box)
            out.append(f'<text x="{x+4}" y="{y-5}" font-size="9" fill="#315f82">{label}</text>')
        out.append(f'<circle cx="{x0}" cy="{y0}" r="3" fill="#cc3030"/>')
        out.append(f'<text x="{x0+6}" y="{y0-6}" font-size="11" fill="#a02020">datum 0</text>')
        out.append(f'<path d="M{x0},{y0+12} v12 M{x0},{y0+18} h{width:.4f} M{x0+width:.4f},{y0+12} v12" fill="none" stroke="#202830"/>')
        out.append(f'<text x="{x0}" y="{y0+43}" font-size="13">{extents[u]:.3f} mm / {extents[u]/25.4:.4f} in</text>')
        out.append(f'<path d="M{x0-16},{y0} h10 M{x0-11},{y0} v{-height:.4f} M{x0-16},{y0-height:.4f} h10" fill="none" stroke="#202830"/>')
        out.append(f'<text x="{x0}" y="{y0+65}" font-size="13">Vertical: {extents[v]:.3f} mm / {extents[v]/25.4:.4f} in</text>')
    out += ['<text x="24" y="510" font-size="12">Dashed box: raw-form envelope, not blank stock size. Red origin can be virtual. Crowded vertex labels omitted; see vertices.csv.</text>',
            '</g></svg>']
    return "\n".join(out)+"\n"


def generate():
    manifest = json.loads(Path("exports/wide-principal-development/manifest.json").read_text())
    sources = dict(manifest["sources"])
    for name in ("scripts/wide_machining_drawings.py", "mini_moonboard/wide_machining.py"):
        sources[name] = hashlib.sha256(Path(name).read_bytes()).hexdigest()
    def unchanged():
        if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != sha for p, sha in sources.items()):
            raise ValueError("Drawing source changed")
    unchanged()
    parts = frame.wood_parts(False)
    outputs = {p.name+".svg": drawing(p, datum(p)) for p in parts}
    if len(outputs) != 29:
        raise ValueError("Expected all twenty-nine wood parts")
    unchanged()
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    for name, text in outputs.items():
        (DIRECTORY/name).write_text(text)
    with (DIRECTORY/"vertices.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("part", "vertex", "u_mm", "v_mm", "w_mm", "u_in", "v_in", "w_in"))
        for p in parts:
            for index, point in enumerate(vertices(p, datum(p)), 1):
                writer.writerow((p.name, index, *point, *[v/25.4 for v in point]))
    (DIRECTORY/"manifest.json").write_text(json.dumps({"candidate": frame.KEY, "source_sha256": sources,
        "artifact_sha256": {n: hashlib.sha256((DIRECTORY/n).read_bytes()).hexdigest()
                            for n in [*outputs, "vertices.csv"]}}, indent=2)+"\n")


if __name__ == "__main__":
    generate()
