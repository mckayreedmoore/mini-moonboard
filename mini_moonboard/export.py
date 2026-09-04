import argparse
import csv
import json
import math
import re
from functools import cache
from pathlib import Path

import cadquery as cq

from . import box_exports
from .box_frame import connections, frame_parts
from .model import (
    ANGLE_FROM_VERTICAL_DEG,
    MAIN_PANEL_SIZE_MM,
    OFFICIAL_KICKER_HEIGHT_MM,
    PANEL_THICKNESS_MM,
    V1_KICKER_HEIGHT_MM,
    V1_PANEL_SIZE_MM,
    build_reference_board,
    build_v1_concept,
    reference_envelope,
)
from .panel_grid import kicker_foothold_datums, main_led_datums, main_tnut_datums
from .stability import render_v1_stability_screen


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
  <text x="{center:.1f}" y="725" text-anchor="middle">{width:.1f} mm / {_imperial(width)} in</text>
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


def export_v1_stability_screen(output_dir: Path) -> Path:
    """Export the current CAD-volume unanchored-stability screen."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_stability_screen.md"
    path.write_text(render_v1_stability_screen())
    return path


def export_v1_cad_render(output_dir: Path) -> Path:
    from .raster import render
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_cad_front_render.png"
    solids = [(p.shape, (40,46,51) if p.name.startswith("main_") else (75,83,90) if p.name in ("kicker_left","kicker_right") else (157,90,36)) for p in frame_parts()]
    solids += [(cq.Compound.makeCompound(c.components()), (41,182,214) if c.kind == "screw" else (175,184,190)) for c in connections()]
    render(solids, path)
    return path


def export_v1_viewer_mesh(output_dir: Path) -> Path:
    """Export selectable frame and connection-representation meshes for review."""
    output_dir.mkdir(parents=True, exist_ok=True)
    models_dir = output_dir / "models"
    models_dir.mkdir(exist_ok=True)
    parts = []
    for child in build_v1_concept().children:
        shape = child.obj if not hasattr(child.obj, "val") else child.obj.val()
        bounds = box_exports.exact_bounds(shape)
        filename = f"{child.name}.stl"
        cq.exporters.export(shape, str(models_dir / filename), cq.exporters.ExportTypes.STL, tolerance=0.5)
        fabrication = _v1_viewer_fabrication_metadata(child.name)
        parts.append(
            {
                "name": child.name,
                "path": f"models/{filename}",
                "fabrication": fabrication,
                "viewer_aabb_mm": [round(bounds.xlen, 1), round(bounds.ylen, 1), round(bounds.zlen, 1)],
            }
        )
    # The STEP/cut model does not pretend that threads are structural solids.
    # The viewer does need each primary connector location, though: it is the
    # review representation that precedes connection modelling in FEA.
    for name, shape in _v1_viewer_connection_solids():
        bounds = box_exports.exact_bounds(shape)
        filename = f"{name}.stl"
        cq.exporters.export(shape, str(models_dir / filename), cq.exporters.ExportTypes.STL, tolerance=0.5)
        parts.append(
            {
                "name": name,
                "path": f"models/{filename}",
                "fabrication": _v1_viewer_fabrication_metadata(name),
                "viewer_aabb_mm": [round(bounds.xlen, 1), round(bounds.ylen, 1), round(bounds.zlen, 1)],
            }
        )
    path = output_dir / "parts.json"
    bounds = box_exports.exact_bounds(cq.Compound.makeCompound([p.shape for p in frame_parts()]))
    bounds_mm = [[getattr(bounds, axis + end) for axis in "xyz"] for end in ("min", "max")]
    path.write_text(json.dumps({"parts": parts, "bounds_mm": bounds_mm}, indent=2) + "\n")
    return path


def _v1_viewer_connection_solids() -> tuple[tuple[str, cq.Shape], ...]:
    return tuple((c.name, cq.Compound.makeCompound(c.components())) for c in connections())






@cache
def _v1_fastener_head_collisions():
    return box_exports.collisions()


def render_v1_fastener_clearance_screen() -> str:
    return box_exports.clearance_report()


def export_v1_fastener_clearance_screen(output_dir: Path) -> Path:
    """Export the repeatable nominal fastener-head collision screen."""
    path = output_dir / "mini_moonboard_v1_fastener_clearance_screen.md"
    path.write_text(render_v1_fastener_clearance_screen())
    return path


def _v1_viewer_fabrication_metadata(name):
    return box_exports.metadata(name)


def _inch_fraction(mm: float) -> str:
    """Format a millimetre cut dimension to the nearest 1/16 inch."""
    sixteenths = round(mm / 25.4 * 16)
    whole, remainder = divmod(sixteenths, 16)
    if not remainder:
        return f"{whole} in"
    divisor = math.gcd(remainder, 16)
    fraction = f"{remainder // divisor}/{16 // divisor}"
    return f"{whole} {fraction} in" if whole else f"{fraction} in"



def export_v1_concept_side_drawing(output_dir: Path) -> Path:
    return box_exports.drawing(output_dir, "concept_side", (1,0,0))


def export_v1_front_drawing(output_dir: Path) -> Path:
    """Export the underside climbing-face elevation with its fixed kicker."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_front.svg"
    drawing = _front_svg(V1_KICKER_HEIGHT_MM, V1_PANEL_SIZE_MM).replace(
        "Mini MoonBoard reference front envelope", "Mini MoonBoard v1 climbing-face elevation (underside)"
    )
    path.write_text(drawing.replace("CUSTOM KICKER INPUT - UNREVIEWED", "V1 PROVISIONAL - AUDIT BEFORE FABRICATION"))
    return path



def export_v1_rear_drawing(output_dir: Path) -> Path:
    return box_exports.drawing(output_dir, "rear", (0,-1,0))



def export_v1_isometric_drawing(output_dir: Path) -> Path:
    return box_exports.drawing(output_dir, "isometric", (1,-1,1))


def export_v1_cut_list(output_dir: Path) -> Path:
    return box_exports.cut_list(output_dir)


def export_v1_leg_cut_schedule(output_dir: Path) -> Path:
    return box_exports.leg_profiles(output_dir)


def _dominant_axis(shape: cq.Shape) -> tuple[float, float, float]:
    """Return a deterministic unit vector along the longest straight edge."""
    edge = max(shape.Edges(), key=lambda candidate: candidate.Length())
    first, second = edge.Vertices()
    start, end = first.Center(), second.Center()
    delta = (end.x - start.x, end.y - start.y, end.z - start.z)
    length = math.sqrt(sum(component * component for component in delta))
    if length == 0:
        raise ValueError("part has no orientable longest edge")
    # Flip the vector to a stable lexicographic orientation so regenerated
    # CSVs do not depend on CAD-kernel edge vertex ordering.
    if next(component for component in delta if abs(component) > 1e-6) < 0:
        delta = tuple(-component for component in delta)
    return tuple(component / length for component in delta)


def export_v1_assembly_layout(output_dir: Path) -> Path:
    """Export every physical V1 part's global placement from datum O."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_assembly_layout.csv"
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            (
                "part",
                "center_x_mm",
                "center_y_mm",
                "center_z_mm",
                "dominant_axis_x",
                "dominant_axis_y",
                "dominant_axis_z",
                "world_aabb_x_mm",
                "world_aabb_y_mm",
                "world_aabb_z_mm",
                "datum",
            )
        )
        for child in build_v1_concept().children:
            shape = child.obj.val() if hasattr(child.obj, "val") else child.obj
            # A hockey-stick leg is one display compound but two separately cut,
            # separately placed physical members.  Expand it here so the layout
            # is a construction placement source rather than a viewer summary.
            if False:  # Legacy legs had separate upper/lower solids; current profiles are continuous.
                lower, upper = sorted(shape.Solids(), key=lambda solid: solid.Center().z)
                physical_parts = ((f"{child.name}_lower", lower), (f"{child.name}_upper", upper))
            else:
                physical_parts = ((child.name, shape),)
            for part_name, physical_shape in physical_parts:
                center = physical_shape.Center()
                axis = _dominant_axis(physical_shape)
                bounds = box_exports.exact_bounds(physical_shape)
                writer.writerow(
                    (
                        part_name,
                        f"{center.x:.3f}",
                        f"{center.y:.3f}",
                        f"{center.z:.3f}",
                        *(f"{component:.6f}" for component in axis),
                        f"{bounds.xlen:.3f}",
                        f"{bounds.ylen:.3f}",
                        f"{bounds.zlen:.3f}",
                        "O: board centerline / kicker-face plane / finished-floor plane; +X right facing board, +Z upward; Y is a world coordinate, while front/back are board-normal directions",
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


def export_v1_panel_drill_schedule(output_dir: Path) -> Path:
    """Export direct local-coordinate drilling records for every V1 blank.

    Coordinates are measured from the finished blank's lower-left corner while
    looking at its climbing face. This is the cuttable V1 transfer schedule;
    the whole-board datum CSV remains a cross-check against Moon's template.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mini_moonboard_v1_panel_drill_schedule.csv"
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("part", "feature", "label", "x_from_left_mm", "z_from_bottom_mm", "diameter_mm", "datum"))
        for row, row_label in enumerate(("lower", "upper")):
            for column, side in enumerate(("left", "right")):
                x_min, z_min = column * V1_PANEL_SIZE_MM, row * V1_PANEL_SIZE_MM
                part = f"main_{row_label}_{side}"
                for feature, datums, diameter in (
                    ("T-nut", main_tnut_datums(), 11.112),
                    ("LED", main_led_datums(), 13.0),
                ):
                    for label, (x, z) in datums.items():
                        if x_min <= x < x_min + V1_PANEL_SIZE_MM and z_min <= z < z_min + V1_PANEL_SIZE_MM:
                            writer.writerow(
                                (part, feature, label, f"{x - x_min:.3f}", f"{z - z_min:.3f}", f"{diameter:.3f}", "finished blank lower-left, climbing face")
                            )
        for column, side in enumerate(("left", "right")):
            x_min = column * V1_PANEL_SIZE_MM
            part = f"kicker_{side}"
            for label, (x, y) in kicker_foothold_datums().items():
                if x_min <= x < x_min + V1_PANEL_SIZE_MM:
                    writer.writerow((part, "T-nut", label, f"{x - x_min:.3f}", f"{V1_KICKER_HEIGHT_MM + y:.3f}", "11.112", "finished blank lower-left, climbing face"))
            for label, (x, y) in main_led_datums().items():
                if x_min <= x < x_min + V1_PANEL_SIZE_MM and y < 0:
                    writer.writerow((part, "LED", label, f"{x - x_min:.3f}", f"{V1_KICKER_HEIGHT_MM + y:.3f}", "13.000", "finished blank lower-left, climbing face"))
    return path


def export_v1_connection_schedule(output_dir: Path) -> Path:
    return box_exports.connection_schedule(output_dir)


def export_v1_bom(output_dir: Path) -> Path:
    return box_exports.bom(output_dir)



def export_v1_secondary_joinery_schedule(output_dir: Path) -> Path:
    return box_exports.write_csv(output_dir, "mini_moonboard_v1_secondary_joinery_schedule.csv", ("connection", "members"), [(c.name, " + ".join(c.members)) for c in connections() if not c.name.startswith(("analysis_panel_", "analysis_leg_"))])


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
        export_v1_stability_screen(args.output_dir),
        export_v1_fastener_clearance_screen(args.output_dir),
        export_v1_cad_render(args.output_dir),
        export_v1_concept_side_drawing(args.output_dir),
        export_v1_front_drawing(args.output_dir),
        export_v1_rear_drawing(args.output_dir),
        export_v1_isometric_drawing(args.output_dir),
        export_v1_cut_list(args.output_dir),
        export_v1_leg_cut_schedule(args.output_dir),
        export_v1_assembly_layout(args.output_dir),
        export_v1_drill_schedule(args.output_dir),
        export_v1_panel_drill_schedule(args.output_dir),
        export_v1_connection_schedule(args.output_dir),
        export_v1_secondary_joinery_schedule(args.output_dir),
        export_v1_bom(args.output_dir),
        export_panel_grid(args.output_dir),
        export_panel_grid_drawing(args.output_dir),
        export_reference_panel_cut_list(args.output_dir, args.kicker_height_mm),
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
