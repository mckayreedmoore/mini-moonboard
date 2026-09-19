"""Export two non-drilling AB205 center-joint trial sheets from raw kerf-right CAD.

Run: .venv/bin/python scripts/draw_rs2_center_joint.py
"""

import csv
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mini_moonboard import floor_flush_width

OUT = ROOT / "exports/rs2-center-joint"
RECORD = ROOT / "docs/bolted-candidate-prototypes/ab205-center-fit.json"
STAGGER = ROOT / "docs/bolted-candidate-prototypes/center-y-stagger.json"
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"


def fmt(value):
    return f"{value:.3f}".rstrip("0").rstrip(".")


def polygon(shape, x):
    """Actual raw broad-face YZ outline; these center members are convex."""
    face = next(
        f for f in shape.Faces()
        if f.Vertices() and all(abs(v.Center().x - x) < 1e-5 for v in f.Vertices())
    )
    points = sorted({(v.Center().y, v.Center().z) for v in face.Vertices()})
    lower = []
    upper = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def path(points, view):
    return " ".join(f"{fmt(x)},{fmt(y)}" for x, y in (view(*p) for p in points))


def text(x, y, value, size=15, color="#172432"):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{escape(str(value))}</text>'


def circle(x, y, color, label=None):
    result = f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="6" fill="white" stroke="{color}" stroke-width="2.5"/>'
    if label:
        result += text(fmt(x + 10), fmt(y - 7), label, 12, color)
    return result


def sheet(kind, underside_y, parts, top_y, station_x, header_top, header_bottom, offsets, protected):
    side = lambda y, z: (110 + (y + 205) * 1.48, 740 - z * 1.48)
    front = lambda x, z: (610 + (x + 230) * 1.48, 740 - z * 1.48)
    plan = lambda x, y: (610 + (x + 230) * 1.48, 1060 - (y + 180) * 1.48)
    principal = parts["base_principal_center_left"]
    post = parts["base_post_center_left"]
    header = parts["base_header"]
    principal_face = polygon(principal, principal.BoundingBox().xmin)
    post_face = polygon(post, post.BoundingBox().xmin)
    hb = header.BoundingBox()
    header_face = [(hb.ymin, hb.zmin), (hb.ymax, hb.zmin), (hb.ymax, hb.zmax), (hb.ymin, hb.zmax)]
    chunks = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1180" viewBox="0 0 1200 1180">',
        '<rect width="1200" height="1180" fill="#fffdf8"/>',
        '<style>text{font-family:Arial,sans-serif} .wood{stroke:#263746;stroke-width:2} .axis{stroke:#b32d32;stroke-width:2;stroke-dasharray:6 4}</style>',
        '<clipPath id="sideclip"><rect x="105" y="155" width="365" height="600"/></clipPath>',
        '<clipPath id="frontclip"><rect x="605" y="155" width="360" height="600"/></clipPath>',
        text(36, 39, f"RS-2 CENTER JOINT | {kind.upper()} AB205 TRIAL", 24),
        text(36, 66, "NON-DRILLING • nominal, unverified fitting • no accepted holes • no fabrication release", 16, "#b32d32"),
        text(105, 130, "SIDE / Y–Z  (left center member)", 17),
        text(605, 130, "FRONT / X–Z  (local crop)", 17),
        '<g clip-path="url(#sideclip)">',
    ]
    for name, points, fill in (
        ("post", post_face, "#d8b786"),
        ("header", header_face, "#e8cfab"),
        ("principal", principal_face, "#b9d2ca"),
    ):
        chunks.append(f'<polygon class="wood" points="{path(points, side)}" fill="{fill}"/>')
    # The red circles are projected trial axes, not raw-CAD holes.
    for z in (header_top + offsets["short"][0], header_top + offsets["short"][1]):
        x, yy = side(top_y, z)
        chunks.append(circle(x, yy, "#b32d32"))
    for z in (header_bottom - offsets["short"][0], header_bottom - offsets["short"][1]):
        x, yy = side(underside_y, z)
        chunks.append(circle(x, yy, "#6d3d9e"))
    for y, z, color in ((top_y, header_top, "#b32d32"), (underside_y, header_bottom, "#6d3d9e")):
        x, yy = side(y, z)
        chunks.append(f'<line x1="{fmt(x)}" y1="{fmt(yy-11)}" x2="{fmt(x)}" y2="{fmt(yy+11)}" stroke="{color}" stroke-width="3"/>')
    for index, row in enumerate(protected, 1):
        x, yy = side(float(row["start_y_mm"]), float(row["start_z_mm"]))
        chunks.append(f'<path d="M {fmt(x-5)} {fmt(yy-5)} L {fmt(x+5)} {fmt(yy+5)} M {fmt(x-5)} {fmt(yy+5)} L {fmt(x+5)} {fmt(yy-5)}" stroke="#17659b" stroke-width="2.5"/>')
        chunks.append(text(fmt(x-28), fmt(yy-9), f"S{index}", 12, "#17659b"))
    chunks += ['</g>', text(111, 776, "Grain ↗ principal; oblique cut at header top", 14),
               text(111, 797, "Grain ↑ post; grain ↔ header (X)", 14),
               text(111, 820, "Red: top. Purple: underside. Blue: protected screws.", 14),
               text(111, 842, f"{len(protected)} of 66 screw starts in crop; 0 of 12 frame bolts.", 13)]
    # XZ elevation displays the x locations of all header axes and the raw member sections.
    chunks.append('<g clip-path="url(#frontclip)">')
    for shape, fill in ((header, "#e8cfab"), (post, "#d8b786"), (principal, "#b9d2ca")):
        b = shape.BoundingBox()
        x1, y1 = front(b.xmin, b.zmax)
        x2, y2 = front(b.xmax, b.zmin)
        chunks.append(f'<rect class="wood" x="{fmt(x1)}" y="{fmt(y1)}" width="{fmt(x2-x1)}" height="{fmt(y2-y1)}" fill="{fill}"/>')
    # Ideal AB205 short vertical (3.5 in), long horizontal (4.125 in).
    # The stroke is schematic: bend radii, exact hole-to-edge registration and fit are unverified.
    for bend_z, tip_z, color in ((header_top, header_top + 88.9, "#b32d32"),
                                 (header_bottom, header_bottom - 88.9, "#6d3d9e")):
        chunks.append(f'<polyline points="{path([(station_x, tip_z), (station_x, bend_z), (station_x-104.775, bend_z)], front)}" fill="none" stroke="{color}" stroke-width="8" stroke-opacity="0.55"/>')
    top_x = [station_x - offset for offset in offsets["long"]]
    under_x = [station_x - offset for offset in offsets["long"]]
    for x in top_x:
        sx, sy = front(x, (header_top + header_bottom) / 2)
        chunks.append(circle(sx, sy, "#b32d32"))
    for x in under_x:
        sx, sy = front(x, (header_top + header_bottom) / 2)
        chunks.append(f'<circle cx="{fmt(sx)}" cy="{fmt(sy)}" r="10" fill="none" stroke="#6d3d9e" stroke-width="2"/>')
    for z, color in [*( (header_top + o, "#b32d32") for o in offsets["short"]),
                     *( (header_bottom - o, "#6d3d9e") for o in offsets["short"])]:
        sx, sy = front(station_x, z)
        chunks.append(circle(sx, sy, color))
    chunks += ['</g>', text(607, 776, "Nominal AB205 L: short vertical / long horizontal", 14),
               text(607, 797, "Principal & post side bores: 2 each", 14),
               text(605, 845, "PLAN / X–Y: through-header trial axes", 17)]
    if abs(top_y - underside_y) < 1e-6:
        for index, x in enumerate(top_x, 1):
            sx, sy = plan(x, top_y)
            chunks.append(circle(sx, sy, "#6d3d9e", f"T/U{index}"))
    else:
        for label, row_y, color in (("T", top_y, "#b32d32"), ("U", underside_y, "#6d3d9e")):
            for index, x in enumerate(top_x, 1):
                sx, sy = plan(x, row_y)
                chunks.append(circle(sx, sy, color, f"{label}{index}"))
    chunks += [
        text(605, 1070, f"Top Y={fmt(top_y)} mm; underside Y={fmt(underside_y)} mm; X={fmt(station_x)} mm", 15),
        text(605, 1094, f"Header Z={fmt(header_bottom)}…{fmt(header_top)} mm; nominal bore Ø14.2875 mm", 15),
        text(36, 1145, "Drawing is a projected geometry question. See source notes and frozen screw-axis CSV.", 15),
        '</svg>',
    ]
    return "\n".join(chunks), top_x


def generate():
    record = json.loads(RECORD.read_text())
    stagger = json.loads(STAGGER.read_text())
    parts = {p.name: p.shape for p in floor_flush_width.variant(floor_flush_width.KERF_RIGHT).uncut_wood_parts()}
    needed = ("base_header", "base_principal_center_left", "base_post_center_left")
    assert all(name in parts for name in needed)
    hb = parts["base_header"].BoundingBox()
    px = parts["base_principal_center_left"].BoundingBox().xmin
    assert abs(px - parts["base_post_center_left"].BoundingBox().xmin) < 1e-6
    assert abs(hb.zmax - parts["base_principal_center_left"].BoundingBox().zmin) < 1e-6
    assert abs(hb.zmin - parts["base_post_center_left"].BoundingBox().zmax) < 1e-6
    top_y = float(record["short_vertical_midband_trial"]["row_y_mm"])
    stagger_y = float(stagger["conditional_parallel_interval_midpoint_trial"]["underside_row_y_mm"])
    offsets = {"short": tuple(25.4 * n for n in (0.8125, 2.6875)),
               "long": tuple(25.4 * n for n in (1.4375, 3.3125))}
    with AXES.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    counts = {kind: sum(row["shop_opening_kind"] == kind for row in rows)
              for kind in ("hillman_panel", "bolt_clearance")}
    assert counts == {"hillman_panel": 66, "bolt_clearance": 12}
    protected = [row for row in rows if row["shop_opening_kind"] == "hillman_panel"
                 and -230 <= float(row["start_x_mm"]) <= 13
                 and -205 <= float(row["start_y_mm"]) <= 31.5
                 and 0 <= float(row["start_z_mm"]) <= 395]
    assert [row["name"] for row in protected] == [
        "round_panel_lower_left_center_1", "round_kicker_left_center_1",
        "round_kicker_left_center_2", "kicker_header_left_1"]
    assert all(abs(float(row["start_x_mm"])) > 1000 for row in rows
               if row["shop_opening_kind"] == "bolt_clearance")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, y in (("shared", top_y), ("stagger", stagger_y)):
        svg, xs = sheet(name, y, parts, top_y, px, hb.zmax, hb.zmin, offsets, protected)
        (OUT / f"rs2-ab205-{name}.svg").write_text(svg)
        assert len(xs) == 2
    return {"top_y": top_y, "stagger_y": stagger_y, "contact_x": px,
            "header_z": (hb.zmin, hb.zmax), "retained_axes": counts}


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2))
