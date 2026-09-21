"""Export source-bound V4 diagnostic primitives for the existing 3D viewer.

This is a partial visual overlay, not a combined V4 assembly or shop output.
"""

import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import simple_center_current_stack_tip_screen as pb02
from scripts import simple_center_wide_post_probe as wide
from scripts import simple_rail_joint_comparison as pb01

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site/v4-diagnostic-scene.json"
BASELINE = ROOT / "site/hybrid/compact-floor-flush-kerf-right/parts.json"


def build_scene():
    baseline = json.loads(BASELINE.read_text())
    names = {part["name"] for part in baseline["parts"]}
    fixed = [
        name
        for name in names
        if name.startswith(
            (
                "fastener_round_panel_",
                "fastener_round_kicker_",
                "fastener_kicker_header_",
            )
        )
    ]
    if len(fixed) != 66 or baseline["design"]["panel_kicker_screw_count"] != 66:
        raise ValueError("selected baseline no longer contains 66 fixed screw visuals")

    wood = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    upright = wood[pb01.UPRIGHT].BoundingBox()
    rail = wood[pb01.RAIL]
    rail_box = rail.BoundingBox()
    rail_t = [v.Y * pb01.T[0] + v.Z * pb01.T[1] for v in rail.Vertices()]
    rail_n = [v.Y * pb01.N[0] + v.Z * pb01.N[1] for v in rail.Vertices()]
    x_width, t_width, n_length = pb01.PB01_GROUP_TRIAL_SIZE_MM
    t_face, n_front = max(rail_t), min(rail_n)
    y, z = pb01._yz(t_face, n_front)
    boxes = [
        {
            "name": "PB01 short rail block",
            "station": "PB01",
            "origin_mm": [upright.xmax, y, z],
            "size_mm": [x_width, t_width, n_length],
            "rotation_x_deg": 50,
        }
    ]
    axes = []
    for name, n_center in (("u1", 265.0), ("u2", 310.0)):
        y, z = pb01._yz(t_face + t_width / 2, n_center)
        axes.append(
            {
                "name": name,
                "station": "PB01",
                "start_mm": [upright.xmin - 2.5, y, z],
                "axis": [1, 0, 0],
                "length_mm": upright.xlen + x_width + 5,
                "diameter_mm": 7.5,
            }
        )
    for name, x_from_butt in (("r1", 70.0), ("r2", 110.0)):
        y, z = pb01._yz(min(rail_t) - 2.5, 290.0)
        axes.append(
            {
                "name": name,
                "station": "PB01",
                "start_mm": [rail_box.xmin + x_from_butt, y, z],
                "axis": [0, *pb01.T],
                "length_mm": 38.1 + t_width + 5,
                "diameter_mm": 7.5,
            }
        )

    parts, bores, ends = pb02._geometry()
    block = parts["header_post_side_cleat"].BoundingBox()
    boxes.append(
        {
            "name": "PB02 post/header block",
            "station": "PB02",
            "origin_mm": [block.xmin, block.ymin, block.zmin],
            "size_mm": [block.xlen, block.ylen, block.zlen],
            "rotation_x_deg": 0,
        }
    )
    if set(bores) != set(pb02.PAIRS):
        raise ValueError("PB02 ten-bore source inventory changed")
    for name, (start_name, end_name) in pb02.PAIRS.items():
        start = ends[start_name][0]
        finish = ends[end_name][0]
        delta = [b - a for a, b in zip(start, finish)]
        length = sum(value * value for value in delta) ** 0.5
        axes.append(
            {
                "name": name,
                "station": "PB02",
                "start_mm": list(start),
                "axis": [value / length for value in delta],
                "length_mm": length,
                "diameter_mm": 2 * wide.BORE_RADIUS,
            }
        )
    return {
        "status": "partial_development_visualization",
        "baseline": "compact-floor-flush-kerf-right",
        "fixed_panel_kicker_screw_axes": len(fixed),
        "fabrication_released": False,
        "boxes": boxes,
        "axes": axes,
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build_scene(), indent=2) + "\n")
