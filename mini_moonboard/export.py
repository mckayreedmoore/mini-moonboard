import argparse
import math
import re
from pathlib import Path

import cadquery as cq

from .model import (
    ANGLE_FROM_VERTICAL_DEG,
    OFFICIAL_KICKER_HEIGHT_MM,
    build_reference_board,
    reference_envelope,
)


def _imperial(mm: float) -> str:
    sixteenths = round(mm / 25.4 * 16)
    whole, numerator = divmod(sixteenths, 16)
    if not numerator:
        return str(whole)
    divisor = math.gcd(numerator, 16)
    return f"{whole} {numerator // divisor}/{16 // divisor}"


def _svg(title: str, body: str) -> str:
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
  <text class="warning" x="450" y="65" text-anchor="middle">REFERENCE ONLY - NOT A FRAME DESIGN</text>
{body}
</svg>
"""


def _front_svg(kicker_height_mm: float) -> str:
    width, _, height = reference_envelope(kicker_height_mm)
    main_vertical = height - kicker_height_mm
    scale = 600 / width
    left, right, bottom = 150.0, 750.0, 650.0
    top = bottom - height * scale
    kicker_top = bottom - kicker_height_mm * scale
    main_seam = kicker_top - main_vertical / 2 * scale
    center = (left + right) / 2
    body = f"""  <rect class="kicker" x="{left:.1f}" y="{kicker_top:.1f}" width="{width * scale:.1f}" height="{kicker_height_mm * scale:.1f}" />
  <rect class="panel" x="{left:.1f}" y="{top:.1f}" width="{width * scale:.1f}" height="{main_vertical * scale:.1f}" />
  <line class="seam" x1="{center:.1f}" y1="{top:.1f}" x2="{center:.1f}" y2="{bottom:.1f}" />
  <line class="seam" x1="{left:.1f}" y1="{main_seam:.1f}" x2="{right:.1f}" y2="{main_seam:.1f}" />
  <line class="dim" x1="{left:.1f}" y1="700" x2="{right:.1f}" y2="700" />
  <text x="{center:.1f}" y="725" text-anchor="middle">{width:.0f} mm / {_imperial(width)} in</text>
  <line class="dim" x1="100" y1="{top:.1f}" x2="100" y2="{bottom:.1f}" />
  <text x="85" y="{(top + bottom) / 2:.1f}" text-anchor="middle" transform="rotate(-90 85 {(top + bottom) / 2:.1f})">{height:.1f} mm / {_imperial(height)} in overall</text>
  <text class="on-dark" x="{center:.1f}" y="{kicker_top + 24:.1f}" text-anchor="middle">kicker {kicker_height_mm:g} mm / {_imperial(kicker_height_mm)} in</text>"""
    return _svg("Mini MoonBoard official front envelope", body)


def _side_svg(kicker_height_mm: float) -> str:
    _, depth, height = reference_envelope(kicker_height_mm)
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
    return _svg("Mini MoonBoard official side envelope", body)


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the Mini MoonBoard reference envelope")
    parser.add_argument("--output-dir", type=Path, default=Path("exports"))
    parser.add_argument("--kicker-height-mm", type=float, default=OFFICIAL_KICKER_HEIGHT_MM)
    args = parser.parse_args()

    for path in export_reference(args.output_dir, args.kicker_height_mm):
        print(path)


if __name__ == "__main__":
    main()
