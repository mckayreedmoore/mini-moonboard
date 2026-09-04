import argparse
import csv
import math
import re
from pathlib import Path

import cadquery as cq
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .model import (
    ANGLE_FROM_VERTICAL_DEG,
    MAIN_PANEL_SIZE_MM,
    OFFICIAL_KICKER_HEIGHT_MM,
    PANEL_THICKNESS_MM,
    V1_KICKER_HEIGHT_MM,
    V1_PANEL_SIZE_MM,
    V1_REAR_TIE_WIDTH_MM,
    V1_STRUCTURAL_BOLT_DISTANCES_MM,
    V1_SUPPORT_THICKNESS_MM,
    V1_SUPPORT_WIDTH_MM,
    build_reference_board,
    build_v1_concept,
    reference_envelope,
    v1_leg_geometry,
    v1_structural_bolt_position,
)
from .panel_grid import kicker_foothold_datums, main_led_datums, main_tnut_datums


def _imperial(mm: float) -> str:
    sixteenths = round(mm / 25.4 * 16)
    whole, numerator = divmod(sixteenths, 16)
    if not numerator:
        return str(whole)
    divisor = math.gcd(numerator, 16)
    return f"{whole} {numerator // divisor}/{16 // divisor}"


def _svg(title: str, body: str, warning: str = "REFERENCE ONLY - NOT A FRAME DESIGN") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="750" viewBox="0 0 900 750" data-units="mm">
  <title>{title}</title>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse">
      <path d="M 0 0 L 8 4 L 0 8 z" fill="#333" />
    </marker>
  </defs>
  <style>
    .panel {{ fill: #20252b; stroke: #f0b429; stroke-width: 2; }}
    .kicker {{ fill: #444b53; stroke: #f0b429; stroke-width: 2; }}
    .seam {{ stroke: #aaa; stroke-width: 1.5; }}
    .dim {{ stroke: #333; stroke-width: 1.5; marker-start: url(#arrow); marker-end: url(#arrow); }}
    .guide {{ stroke: #777; stroke-width: 1; stroke-dasharray: 5 5; }}
    text {{ fill: #222; font: 16px sans-serif; }}
    .on-dark {{ fill: white; }}
    .warning {{ fill: #a3261f; font-weight: bold; }}
  </style>
  <rect width="900" height="750" fill="white" />
  <text x="450" y="35" text-anchor="middle" font-size="24">{title}</text>
  <text class="warning" x="450" y="65" text-anchor="middle">{warning}</text>
{body}
</svg>
"""


def _front_svg(kicker_height_mm: float, panel_size_mm: float = MAIN_PANEL_SIZE_MM) -> str:
    width, _, height = reference_envelope(kicker_height_mm, panel_size_mm)
    main_vertical = height - kicker_height_mm
    scale = 600 / width
    left, right, bottom = 150.0, 750.0, 650.0
    top = bottom - height * scale
    kicker_top = bottom - kicker_height_mm * scale
    main_seam = kicker_top - main_vertical / 2 * scale
    center = (left + right) / 2
    active_zone = ""
    if kicker_height_mm != OFFICIAL_KICKER_HEIGHT_MM:
        active_zone_bottom = kicker_top + OFFICIAL_KICKER_HEIGHT_MM * scale
        active_zone = f"""
  <line class="seam" x1="{left:.1f}" y1="{active_zone_bottom:.1f}" x2="{right:.1f}" y2="{active_zone_bottom:.1f}" />
  <text class="on-dark" x="{center:.1f}" y="{kicker_top + 20:.1f}" text-anchor="middle">official 150 mm / 5 7/8 in active zone</text>"""
    body = f"""  <rect class="kicker" x="{left:.1f}" y="{kicker_top:.1f}" width="{width * scale:.1f}" height="{kicker_height_mm * scale:.1f}" />
  <rect class="panel" x="{left:.1f}" y="{top:.1f}" width="{width * scale:.1f}" height="{main_vertical * scale:.1f}" />
  <line class="seam" x1="{center:.1f}" y1="{top:.1f}" x2="{center:.1f}" y2="{bottom:.1f}" />
  <line class="seam" x1="{left:.1f}" y1="{main_seam:.1f}" x2="{right:.1f}" y2="{main_seam:.1f}" />
  <line class="dim" x1="{left:.1f}" y1="700" x2="{right:.1f}" y2="700" />
  <text x="{center:.1f}" y="725" text-anchor="middle">{width:.0f} mm / {_imperial(width)} in</text>
  <line class="dim" x1="100" y1="{top:.1f}" x2="100" y2="{bottom:.1f}" />
  <text x="85" y="{(top + bottom) / 2:.1f}" text-anchor="middle" transform="rotate(-90 85 {(top + bottom) / 2:.1f})">{height:.1f} mm / {_imperial(height)} in overall</text>
  <text class="on-dark" x="{center:.1f}" y="{bottom - 8:.1f}" text-anchor="middle">kicker {kicker_height_mm:g} mm / {_imperial(kicker_height_mm)} in</text>{active_zone}"""
    warning = (
        "REFERENCE ONLY - NOT A FRAME DESIGN"
        if kicker_height_mm == OFFICIAL_KICKER_HEIGHT_MM
        else "CUSTOM KICKER INPUT - UNREVIEWED"
    )
    return _svg("Mini MoonBoard reference front envelope", body, warning)


def _side_svg(kicker_height_mm: float, panel_size_mm: float = MAIN_PANEL_SIZE_MM) -> str:
    _, depth, height = reference_envelope(kicker_height_mm, panel_size_mm)
    scale = 520 / height
    base_x, bottom = 180.0, 650.0
    kicker_top = bottom - kicker_height_mm * scale
    top_x = base_x + depth * scale
    top_y = bottom - height * scale
    body = f"""  <line class="guide" x1="100" y1="{bottom:.1f}" x2="800" y2="{bottom:.1f}" />
  <rect class="kicker" x="{base_x - 5:.1f}" y="{kicker_top:.1f}" width="10" height="{kicker_height_mm * scale:.1f}" />
  <line class="panel" x1="{base_x:.1f}" y1="{kicker_top:.1f}" x2="{top_x:.1f}" y2="{top_y:.1f}" stroke-width="8" />
  <line class="guide" x1="{base_x:.1f}" y1="{kicker_top:.1f}" x2="{base_x:.1f}" y2="{top_y:.1f}" />
  <text x="{base_x + 25:.1f}" y="{kicker_top - 25:.1f}">{ANGLE_FROM_VERTICAL_DEG:g} degrees from vertical</text>
  <line class="dim" x1="{base_x:.1f}" y1="700" x2="{top_x:.1f}" y2="700" />
  <text x="{(base_x + top_x) / 2:.1f}" y="725" text-anchor="middle">depth {depth:.1f} mm / {_imperial(depth)} in</text>
  <line class="dim" x1="100" y1="{top_y:.1f}" x2="100" y2="{bottom:.1f}" />
  <text x="85" y="{(top_y + bottom) / 2:.1f}" text-anchor="middle" transform="rotate(-90 85 {(top_y + bottom) / 2:.1f})">height {height:.1f} mm / {_imperial(height)} in</text>
  <text x="{base_x - 15:.1f}" y="{(kicker_top + bottom) / 2:.1f}" text-anchor="end">kicker {kicker_height_mm:g} mm</text>"""
    warning = (
        "REFERENCE ONLY - NOT A FRAME DESIGN"
        if kicker_height_mm == OFFICIAL_KICKER_HEIGHT_MM
        else "CUSTOM KICKER INPUT - UNREVIEWED"
    )
    return _svg("Mini MoonBoard reference side envelope", body, warning)


def _export_step(board: cq.Assembly, path: Path) -> None:
    # Open CASCADE emits presentation styles in unstable order, so the committed
    # interchange file deliberately omits color metadata.
    stable_board = cq.Assembly(name=board.name)
    for child in board.children:
        stable_board.add(child.obj, name=child.name)
    stable_board.export(str(path))

    step = path.read_text()
    step = re.sub(
        r"(FILE_NAME\('Open CASCADE Shape Model',')[^']+(')",
        r"\g<1>1970-01-01T00:00:00\2",
        step,
        count=1,
    )
    occurrence = iter(range(1, len(board.children) + 1))
    step = re.sub(
        r"(NEXT_ASSEMBLY_USAGE_OCCURRENCE\(')\d+(')",
        lambda match: f"{match[1]}{next(occurrence)}{match[2]}",
        step,
    )
    # STEP treats whitespace as insignificant outside strings. The exporter
    # wraps lines differently as its process-wide occurrence counter grows.
    step = re.sub(r"\s+", " ", step)
    step = re.sub(r"\s*([(),;$])\s*", r"\1", step).replace(";", ";\n")
    path.write_text(step.rstrip() + "\n")


def export_reference(
    output_dir: Path,
    kicker_height_mm: float = OFFICIAL_KICKER_HEIGHT_MM,
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    step_path = output_dir / "mini_moonboard_reference.step"
    front_path = output_dir / "mini_moonboard_reference_front.svg"
    side_path = output_dir / "mini_moonboard_reference_side.svg"

    _export_step(build_reference_board(kicker_height_mm), step_path)
    front_path.write_text(_front_svg(kicker_height_mm))
    side_path.write_text(_side_svg(kicker_height_mm))
    return step_path, front_path, side_path


def export_v1_concept(output_dir: Path) -> Path:
    """Export the provisional board-and-legs concept for review, not fabrication."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_concept.step"
    _export_step(build_v1_concept(), path)
    return path


def export_v1_cad_render(output_dir: Path) -> Path:
    """Render tessellated solids from the actual V1 CadQuery assembly."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_cad_front_render.png"
    figure = plt.figure(figsize=(12, 9), facecolor="#f4f1ea")
    axes = figure.add_subplot(projection="3d")
    colors = {"main": "#20252b", "kicker": "#444b53", "leg": "#8a4b16", "face": "#6f3510"}
    # Matplotlib cannot depth-sort separate tessellated collections reliably.
    # This README view intentionally presents the underside climbing face,
    # kicker, and exterior legs; the interactive viewer retains every solid.
    front_visible = ("main_", "kicker_left", "kicker_right", "leg_left", "leg_right")
    for child in build_v1_concept().children:
        if not child.name.startswith(front_visible):
            continue
        shape = child.obj if not hasattr(child.obj, "val") else child.obj.val()
        vertices, triangles = shape.tessellate(2.0)
        faces = [[vertices[index].toTuple() for index in triangle] for triangle in triangles]
        category = next((key for key in colors if child.name.startswith(key)), "face")
        axes.add_collection3d(Poly3DCollection(faces, facecolors=colors[category], edgecolors="#171717", linewidths=0.1))
    axes.set_box_aspect((2438.4, 1700, 2100))
    # Look upward at the underside, where holds are installed. Holds themselves
    # remain unmodelled pending the physical/template audit.
    axes.view_init(elev=-14, azim=-35)
    axes.set_axis_off()
    axes.set_xlim(-1500, 1500)
    axes.set_ylim(-100, 1700)
    axes.set_zlim(0, 2200)
    figure.tight_layout(pad=0)
    figure.savefig(path, dpi=180, facecolor=figure.get_facecolor())
    plt.close(figure)
    return path


def export_v1_viewer_mesh(output_dir: Path) -> Path:
    """Export the actual V1 assembly as an STL mesh for the static web viewer."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_concept.stl"
    shapes = [child.obj if not hasattr(child.obj, "val") else child.obj.val() for child in build_v1_concept().children]
    cq.exporters.export(cq.Compound.makeCompound(shapes), str(path), cq.exporters.ExportTypes.STL, tolerance=0.5)
    return path


def _v1_side_svg() -> str:
    _, board_depth, board_height = reference_envelope(V1_KICKER_HEIGHT_MM, V1_PANEL_SIZE_MM)
    scale = 520 / board_height
    base_x, bottom = 155.0, 650.0
    kicker_top = bottom - V1_KICKER_HEIGHT_MM * scale
    top_x, top_y = base_x + board_depth * scale, bottom - board_height * scale
    leg = v1_leg_geometry()
    bend_y, bend_z = leg["bend_y"], leg["bend_z"]
    upper_y, upper_z = leg["upper_y"], leg["upper_z"]
    foot_y = leg["foot_y"]

    def point(y: float, z: float) -> tuple[float, float]:
        return base_x + y * scale, bottom - z * scale

    bend_x, bend_screen_y = point(bend_y, bend_z)
    upper_x, upper_screen_y = point(upper_y, upper_z)
    foot_x, foot_screen_y = point(foot_y, 0.0)
    body = f"""  <line class="guide" x1="90" y1="{bottom:.1f}" x2="820" y2="{bottom:.1f}" />
  <rect class="kicker" x="{base_x - 5:.1f}" y="{kicker_top:.1f}" width="10" height="{V1_KICKER_HEIGHT_MM * scale:.1f}" />
  <line class="panel" x1="{base_x:.1f}" y1="{kicker_top:.1f}" x2="{top_x:.1f}" y2="{top_y:.1f}" stroke-width="8" />
  <line class="leg" x1="{foot_x:.1f}" y1="{foot_screen_y:.1f}" x2="{bend_x:.1f}" y2="{bend_screen_y:.1f}" />
  <line class="leg" x1="{bend_x:.1f}" y1="{bend_screen_y:.1f}" x2="{upper_x:.1f}" y2="{upper_screen_y:.1f}" />
  <circle class="datum" cx="{bend_x:.1f}" cy="{bend_screen_y:.1f}" r="5" />
  <text x="{bend_x + 12:.1f}" y="{bend_screen_y - 12:.1f}">row 8 bend datum</text>
  <text x="{upper_x + 10:.1f}" y="{upper_screen_y - 8:.1f}">row 10 upper datum</text>
  <text x="{foot_x + 8:.1f}" y="{foot_screen_y - 12:.1f}">provisional lower-member endpoint</text>
  <text x="{base_x - 12:.1f}" y="{(bottom + kicker_top) / 2:.1f}" text-anchor="end">225 mm kicker</text>
  <text x="450" y="700" text-anchor="middle">Two exterior laminated legs are coincident in this side view; 60 degree lower-leg angle.</text>"""
    return _svg(
        "Mini MoonBoard v1 provisional side concept",
        body,
        "PROVISIONAL GEOMETRY - HUMAN STRUCTURAL AUDIT REQUIRED",
    ).replace(
        ".guide {",
        ".leg { stroke: #8a4b16; stroke-width: 16; stroke-linecap: round; }\n"
        "    .datum { fill: #a3261f; }\n    .guide {",
    )


def export_v1_concept_side_drawing(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_concept_side.svg"
    path.write_text(_v1_side_svg())
    return path


def export_v1_front_drawing(output_dir: Path) -> Path:
    """Export the underside climbing-face elevation with its fixed kicker."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_front.svg"
    drawing = _front_svg(V1_KICKER_HEIGHT_MM, V1_PANEL_SIZE_MM).replace(
        "Mini MoonBoard reference front envelope", "Mini MoonBoard v1 climbing-face elevation (underside)"
    )
    path.write_text(drawing.replace("CUSTOM KICKER INPUT - UNREVIEWED", "V1 PROVISIONAL - AUDIT BEFORE FABRICATION"))
    return path


def _v1_rear_svg() -> str:
    width, _, height = reference_envelope(V1_KICKER_HEIGHT_MM, V1_PANEL_SIZE_MM)
    scale = 600 / width
    left, right, bottom = 150.0, 750.0, 650.0
    top = bottom - height * scale
    kicker_top = bottom - V1_KICKER_HEIGHT_MM * scale
    rail_x = [left + width * fraction * scale for fraction in (0.0, 1 / 3, 0.5, 2 / 3, 1.0)]
    rails = "\n".join(
        f'  <line class="rail" x1="{x:.1f}" y1="{top:.1f}" x2="{x:.1f}" y2="{kicker_top:.1f}" />'
        for x in rail_x
    )
    braces = "\n".join(
        f'  <line class="brace" x1="{left:.1f}" y1="{y:.1f}" x2="{right:.1f}" y2="{y:.1f}" />'
        for y in (kicker_top, (top + kicker_top) / 2, top)
    )
    body = f"""  <rect class="kicker" x="{left:.1f}" y="{kicker_top:.1f}" width="{width * scale:.1f}" height="{V1_KICKER_HEIGHT_MM * scale:.1f}" />
  <rect class="panel" x="{left:.1f}" y="{top:.1f}" width="{width * scale:.1f}" height="{(kicker_top - top):.1f}" />
{rails}
{braces}
  <text x="450" y="700" text-anchor="middle">Four outer/intermediate rails plus center-seam rail, and three panel-joint-brace rows; 54 mm provisional hardware/wiring gap.</text>
  <text x="450" y="725" text-anchor="middle">Support-side ties are split at center for 4 x 8 stock; splice detail requires human review.</text>"""
    return _svg(
        "Mini MoonBoard v1 support-side elevation",
        body,
        "PROVISIONAL GEOMETRY - HUMAN STRUCTURAL AUDIT REQUIRED",
    ).replace(
        ".guide {",
        ".rail { stroke: #8a4b16; stroke-width: 18; }\n"
        "    .brace { stroke: #6f3510; stroke-width: 14; }\n    .guide {",
    )


def export_v1_rear_drawing(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_rear.svg"
    path.write_text(_v1_rear_svg())
    return path


def _v1_isometric_svg() -> str:
    """Render a lightweight isometric review view from the v1 model dimensions."""
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)

    def point(x: float, y: float, z: float) -> tuple[float, float]:
        return 450 + x * 0.18 + y * 0.12, 630 + x * 0.055 - y * 0.07 - z * 0.22

    def polygon(points: tuple[tuple[float, float, float], ...], css: str) -> str:
        return f'  <polygon class="{css}" points="' + " ".join(
            f"{u:.1f},{v:.1f}" for u, v in (point(*vertex) for vertex in points)
        ) + '" />'

    def line(start: tuple[float, float, float], end: tuple[float, float, float], css: str) -> str:
        start_u, start_v = point(*start)
        end_u, end_v = point(*end)
        return f'  <line class="{css}" x1="{start_u:.1f}" y1="{start_v:.1f}" x2="{end_u:.1f}" y2="{end_v:.1f}" />'

    x_left, x_right = -V1_PANEL_SIZE_MM, V1_PANEL_SIZE_MM
    surface = lambda distance: (distance * math.sin(angle), V1_KICKER_HEIGHT_MM + distance * math.cos(angle))
    main_bottom_y, main_bottom_z = surface(0.0)
    mid_y, mid_z = surface(V1_PANEL_SIZE_MM)
    top_y, top_z = surface(2 * V1_PANEL_SIZE_MM)
    board = polygon(
        ((x_left, main_bottom_y, main_bottom_z), (x_right, main_bottom_y, main_bottom_z),
         (x_right, top_y, top_z), (x_left, top_y, top_z)),
        "panel",
    )
    kicker = polygon(
        ((x_left, 0.0, 0.0), (x_right, 0.0, 0.0),
         (x_right, main_bottom_y, main_bottom_z), (x_left, main_bottom_y, main_bottom_z)),
        "kicker",
    )
    seams = "\n".join(
        (
            line((0.0, main_bottom_y, main_bottom_z), (0.0, top_y, top_z), "seam"),
            line((x_left, mid_y, mid_z), (x_right, mid_y, mid_z), "seam"),
        )
    )
    leg = v1_leg_geometry()
    bend_y, bend_z = leg["bend_y"], leg["bend_z"]
    upper_y, upper_z = leg["upper_y"], leg["upper_z"]
    foot_y, foot_z = leg["foot_y"], leg["foot_center_z"]
    legs = "\n".join(
        line((x, foot_y, foot_z), (x, bend_y, bend_z), "leg")
        + "\n"
        + line((x, bend_y, bend_z), (x, upper_y, upper_z), "leg")
        for x in (
            -V1_PANEL_SIZE_MM - V1_SUPPORT_WIDTH_MM / 2 - V1_SUPPORT_THICKNESS_MM / 2,
            V1_PANEL_SIZE_MM + V1_SUPPORT_WIDTH_MM / 2 + V1_SUPPORT_THICKNESS_MM / 2,
        )
    )
    rails = "\n".join(
        line((x, main_bottom_y + 54.0, main_bottom_z), (x, top_y + 54.0, top_z), "rail")
        for x in (-V1_PANEL_SIZE_MM, -V1_PANEL_SIZE_MM / 3, 0.0, V1_PANEL_SIZE_MM / 3, V1_PANEL_SIZE_MM)
    )
    body = f"""{kicker}
{board}
{seams}
{rails}
{legs}
  <text x="450" y="710" text-anchor="middle">Isometric support-side review render: panels, kicker, five rails, and two exterior hockey-stick legs.</text>"""
    return _svg(
        "Mini MoonBoard v1 provisional isometric render",
        body,
        "PROVISIONAL GEOMETRY - HUMAN STRUCTURAL AUDIT REQUIRED",
    ).replace(
        ".guide {",
        ".leg { stroke: #8a4b16; stroke-width: 16; stroke-linecap: round; }\n"
        "    .rail { stroke: #6f3510; stroke-width: 9; }\n    .guide {",
    )


def export_v1_isometric_drawing(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_isometric.svg"
    path.write_text(_v1_isometric_svg())
    return path


def export_v1_cut_list(output_dir: Path) -> Path:
    """Export a provisional, laminations-expanded cut list for audit and nesting."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_cut_list.csv"
    rows = (
        ("climbing surface", "main climbing panel", 4, V1_PANEL_SIZE_MM, V1_PANEL_SIZE_MM, PANEL_THICKNESS_MM),
        ("climbing surface", "kicker panel", 2, V1_PANEL_SIZE_MM, V1_KICKER_HEIGHT_MM, PANEL_THICKNESS_MM),
        ("support frame", "face-rail lamination segment", 20, V1_PANEL_SIZE_MM, V1_SUPPORT_WIDTH_MM, PANEL_THICKNESS_MM),
        ("support frame", "panel-joint-brace-half lamination", 12, V1_PANEL_SIZE_MM, V1_REAR_TIE_WIDTH_MM, PANEL_THICKNESS_MM),
        ("support frame", "kicker-center-seam lamination", 2, V1_KICKER_HEIGHT_MM, V1_SUPPORT_WIDTH_MM, PANEL_THICKNESS_MM),
        ("support frame", "kicker-bottom-backing-half lamination", 4, V1_PANEL_SIZE_MM, V1_REAR_TIE_WIDTH_MM, PANEL_THICKNESS_MM),
        ("support frame", "rear-tie-half lamination", 12, V1_PANEL_SIZE_MM + V1_SUPPORT_THICKNESS_MM, V1_REAR_TIE_WIDTH_MM, PANEL_THICKNESS_MM),
        ("support frame", "leg-lower lamination", 4, v1_leg_geometry()["lower_length"], V1_SUPPORT_WIDTH_MM, PANEL_THICKNESS_MM),
        ("support frame", "leg-upper lamination", 4, 400.0, V1_SUPPORT_WIDTH_MM, PANEL_THICKNESS_MM),
    )
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("assembly", "part", "quantity", "length_mm", "width_mm", "thickness_mm", "note"))
        for assembly, part, quantity, length, width, thickness in rows:
            writer.writerow(
                (
                    assembly,
                    part,
                    quantity,
                    f"{length:.1f}",
                    f"{width:.1f}",
                    f"{thickness:.1f}",
                    "PROVISIONAL: verify stock and joint/connection details before cutting",
                )
            )
    return path


def export_v1_drill_schedule(output_dir: Path) -> Path:
    """Export selected-hardware drilling data, retaining official center datums."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_drill_schedule.csv"
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("feature", "label", "x_mm", "y_mm", "diameter_mm", "note"))
        for label, (x, y) in main_tnut_datums().items():
            writer.writerow(("T-nut", label, f"{x:.3f}", f"{y:.3f}", "11.112", "Escape 3/8-16: offcut test required"))
        for label, (x, y) in main_led_datums().items():
            writer.writerow(("LED", label, f"{x:.3f}", f"{y:.3f}", "13.000", "MoonBoard LED kit: verify supplied guide"))
        for label, (x, y) in kicker_foothold_datums().items():
            writer.writerow(("kicker T-nut", label, f"{x:.3f}", f"{y:.3f}", "11.112", "Escape 3/8-16: offcut test required"))
    return path


def export_v1_connection_schedule(output_dir: Path) -> Path:
    """Export provisional structural connection datums for human review."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_connection_schedule.csv"
    bolt_distances = V1_STRUCTURAL_BOLT_DISTANCES_MM
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            (
                "connection",
                "side",
                "quantity",
                "datum",
                "x_mm",
                "y_mm",
                "z_mm",
                "axis",
                "clearance_hole_mm",
                "hardware_assumption",
                "status",
            )
        )
        for side in ("left", "right"):
            for distance in bolt_distances:
                sign = -1 if side == "left" else 1
                x, y, z = v1_structural_bolt_position(sign, distance)
                writer.writerow(
                    (
                        "leg upper member to exterior outer support-side rail",
                        side,
                        1,
                        "O: board centerline / kicker-face plane / finished-floor plane; +X right facing board, +Y rearward, +Z upward; X is bolt-stack midpoint, Y/Z are hole centerline",
                        f"{x:.3f}",
                        f"{y:.3f}",
                        f"{z:.3f}",
                        "X",
                        "10.000",
                        "3/8 in Grade-5 through-bolt; length unresolved pending approved washer/plate/nut stack and thread engagement",
                        "PROVISIONAL: envelope modeled; reviewer must check edge distance, panel/T-nut/LED clearance, bolt stack, and load path",
                    )
                )
    return path


def export_v1_bom(output_dir: Path) -> Path:
    """Export the provisional purchasing BOM separately from the plywood cut list."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_bom.csv"
    rows = (
        ("3/4 in 4 x 8 birch plywood", "unresolved", "User-selected source stock; no sheet count until a reviewed nesting plan"),
        ("Escape 3-hole screw-in T-nuts, 3/8-16", "200", "142 positions plus spares; selected 7/16 in bore"),
        ("3/8-16 hold bolts", "142 minimum plus spares", "Length mix must match final hold set"),
        ("MoonBoard LED System", "1", "SKU 60-201-V5; supplied kit guide controls installation"),
        ("3/8 in Grade-5 structural through-bolts", "8; length unresolved", "Do not purchase length until approved washer/plate/nut stack and thread engagement calculation"),
        ("3/8 in x 1.5 in fender washers", "16", "Provisional leg connection hardware"),
        ("3/8 in nyloc nuts", "8", "Provisional leg connection hardware"),
        ("Panel-to-rail fasteners", "unresolved", "Select only after physical fit test and review"),
        ("Lamination adhesive", "unresolved", "Select compatible product, cure, and clamping schedule after review"),
        ("Feet / anti-slip / floor protection", "unresolved", "Required for unanchored installation"),
    )
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("item", "quantity", "note"))
        writer.writerows(rows)
    return path


def export_panel_grid(output_dir: Path) -> Path:
    """Export source-backed center datums; these are not drilling diameters."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_metric_template_datums.csv"
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("feature", "label", "x_mm", "y_mm", "x_in", "y_in"))
        for feature, datums in (
            ("tnut", main_tnut_datums()),
            ("led", main_led_datums()),
            ("kicker_foothold", kicker_foothold_datums()),
        ):
            for label, (x, y) in datums.items():
                writer.writerow(
                    (feature, label, f"{x:.3f}", f"{y:.3f}", f"{x / 25.4:.4f}", f"{y / 25.4:.4f}")
                )
    return path


def _panel_grid_svg() -> str:
    template_width_mm = 2437.0
    main_height_mm = 2440.0
    kicker_height_mm = OFFICIAL_KICKER_HEIGHT_MM
    scale = 650.0 / template_width_mm
    left, top = 150.0, 135.0
    main_bottom = top + main_height_mm * scale
    kicker_bottom = main_bottom + kicker_height_mm * scale

    def x_coordinate(x_mm: float) -> float:
        return left + x_mm * scale

    def y_coordinate(y_mm: float) -> float:
        return main_bottom - y_mm * scale

    tnut_circles = "\n".join(
        f'  <circle class="tnut" cx="{x_coordinate(x):.2f}" cy="{y_coordinate(y):.2f}" r="2.3" />'
        for x, y in main_tnut_datums().values()
    )
    led_circles = "\n".join(
        f'  <circle class="led" cx="{x_coordinate(x):.2f}" cy="{y_coordinate(y):.2f}" r="1.2" />'
        for x, y in main_led_datums().values()
    )
    kicker_circles = "\n".join(
        f'  <circle class="kicker-hole" cx="{x_coordinate(x):.2f}" cy="{y_coordinate(y):.2f}" r="2.3" />'
        for x, y in kicker_foothold_datums().values()
    )
    column_labels = "\n".join(
        f'  <text class="axis" x="{x_coordinate(200.0 * index):.2f}" y="125" text-anchor="middle">{column}</text>'
        for index, column in enumerate("ABCDEFGHIJK", start=1)
    )
    row_labels = "\n".join(
        f'  <text class="axis" x="132" y="{y_coordinate(80.0 + 200.0 * (row - 1)) + 4:.2f}" text-anchor="end">{row}</text>'
        for row in range(1, 13)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="950" viewBox="0 0 900 950" data-units="mm">
  <title>Mini MoonBoard metric-template datum drawing</title>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse">
      <path d="M 0 0 L 8 4 L 0 8 z" fill="#333" />
    </marker>
  </defs>
  <style>
    .panel {{ fill: #20252b; stroke: #f0b429; stroke-width: 2; }}
    .kicker {{ fill: #444b53; stroke: #f0b429; stroke-width: 2; }}
    .seam {{ stroke: #aaa; stroke-width: 1.5; }}
    .tnut {{ fill: #f0b429; }}
    .led {{ fill: #78b7e5; }}
    .kicker-hole {{ fill: #e07a5f; }}
    .dim {{ stroke: #333; stroke-width: 1.5; marker-start: url(#arrow); marker-end: url(#arrow); }}
    text {{ fill: #222; font: 16px sans-serif; }}
    .axis {{ font-weight: bold; }}
    .on-dark {{ fill: white; }}
    .warning {{ fill: #a3261f; font-weight: bold; }}
  </style>
  <rect width="900" height="950" fill="white" />
  <text x="450" y="35" text-anchor="middle" font-size="24">Mini MoonBoard metric-template datum drawing</text>
  <text class="warning" x="450" y="65" text-anchor="middle">CENTER DATUMS ONLY - NOT A DRILL TEMPLATE</text>
  <text x="450" y="90" text-anchor="middle">Verify hole diameters and 100 percent print calibration before fabrication.</text>
  <line class="dim" x1="{left:.2f}" y1="110" x2="{left + template_width_mm * scale:.2f}" y2="110" />
  <text x="450" y="105" text-anchor="middle">2437 mm / {_imperial(template_width_mm)} in template width</text>
  <rect class="panel" x="{left:.2f}" y="{top:.2f}" width="{template_width_mm * scale:.2f}" height="{main_height_mm * scale:.2f}" />
  <rect class="kicker" x="{left:.2f}" y="{main_bottom:.2f}" width="{template_width_mm * scale:.2f}" height="{kicker_height_mm * scale:.2f}" />
  <line class="seam" x1="{x_coordinate(template_width_mm / 2):.2f}" y1="{top:.2f}" x2="{x_coordinate(template_width_mm / 2):.2f}" y2="{kicker_bottom:.2f}" />
  <line class="seam" x1="{left:.2f}" y1="{y_coordinate(1220.0):.2f}" x2="{left + template_width_mm * scale:.2f}" y2="{y_coordinate(1220.0):.2f}" />
  <line class="seam" x1="{left:.2f}" y1="{main_bottom:.2f}" x2="{left + template_width_mm * scale:.2f}" y2="{main_bottom:.2f}" />
{tnut_circles}
{led_circles}
{kicker_circles}
{column_labels}
{row_labels}
  <text class="on-dark" x="{left + 12:.2f}" y="{top + 22:.2f}">main surface: T-nut centers in yellow; LED centers in blue</text>
  <text class="on-dark" x="{left + 12:.2f}" y="{kicker_bottom - 10:.2f}">official kicker foothold centers in orange</text>
  <text x="450" y="870" text-anchor="middle">Origin: lower-left of main surface; x right; y up. Kicker coordinates are negative y.</text>
  <text x="450" y="895" text-anchor="middle">Metric-template source. Imperial values are conversions, not replacement template dimensions.</text>
</svg>
"""


def export_panel_grid_drawing(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_metric_template_datums.svg"
    path.write_text(_panel_grid_svg())
    return path


def export_reference_panel_cut_list(
    output_dir: Path,
    kicker_height_mm: float = OFFICIAL_KICKER_HEIGHT_MM,
) -> Path:
    """Export known panel blanks only; frame parts need a reviewed design."""
    reference_envelope(kicker_height_mm)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_reference_panel_cut_list.csv"
    scope = "reference climbing surface only — excludes frame and hardware"
    material = "birch plywood; verify grade and actual thickness"
    rows = (
        ("main climbing panel", 4, MAIN_PANEL_SIZE_MM, MAIN_PANEL_SIZE_MM),
        ("kicker panel", 2, MAIN_PANEL_SIZE_MM, kicker_height_mm),
    )
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            (
                "scope",
                "part",
                "quantity",
                "length_mm",
                "width_mm",
                "thickness_mm",
                "length_in",
                "width_in",
                "thickness_in",
                "material",
            )
        )
        for part, quantity, length, width in rows:
            writer.writerow(
                (
                    scope,
                    part,
                    quantity,
                    f"{length:.1f}",
                    f"{width:.1f}",
                    f"{PANEL_THICKNESS_MM:.1f}",
                    f"{length / 25.4:.4f}",
                    f"{width / 25.4:.4f}",
                    f"{PANEL_THICKNESS_MM / 25.4:.4f}",
                    material,
                )
            )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the Mini MoonBoard reference envelope")
    parser.add_argument("--output-dir", type=Path, default=Path("exports"))
    parser.add_argument("--kicker-height-mm", type=float, default=OFFICIAL_KICKER_HEIGHT_MM)
    args = parser.parse_args()

    paths = (
        *export_reference(args.output_dir, args.kicker_height_mm),
        export_v1_concept(args.output_dir),
        export_v1_cad_render(args.output_dir),
        export_v1_concept_side_drawing(args.output_dir),
        export_v1_front_drawing(args.output_dir),
        export_v1_rear_drawing(args.output_dir),
        export_v1_isometric_drawing(args.output_dir),
        export_v1_cut_list(args.output_dir),
        export_v1_drill_schedule(args.output_dir),
        export_v1_connection_schedule(args.output_dir),
        export_v1_bom(args.output_dir),
        export_panel_grid(args.output_dir),
        export_panel_grid_drawing(args.output_dir),
        export_reference_panel_cut_list(args.output_dir, args.kicker_height_mm),
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
