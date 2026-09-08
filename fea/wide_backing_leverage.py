"""Projected two-support backing statics; not actual panel load distribution."""
import json
import math
from pathlib import Path

from mini_moonboard import box_frame as b
from mini_moonboard import wide_frame as frame
from scripts.wide_purchase_bom import build as authenticate_inventory

OUTPUT = Path("fea/results/wide-backing-leverage.json")


def reactions(left, right, load_x, outward_force):
    """Positive reactions oppose outward load; negative requires compression.

    Only force balance and the moment about board-slope S are represented.
    No rotational restraint, rail stiffness, contact patch or strength credit.
    """
    if not all(map(math.isfinite, (left, right, load_x, outward_force))) or left >= right:
        raise ValueError("Finite loads/coordinates and distinct ordered supports required")
    return (outward_force*(right-load_x)/(right-left),
            outward_force*(load_x-left)/(right-left))


def build():
    authenticate_inventory()
    bolts = sorted((c for c in frame.connections() if c.name.startswith("timber_backing_bolt_")),
                   key=lambda c: c.start.x)
    loads = [c for c in frame.panel_connections() if c.members[1] == "timber_bottom_backing"]
    if len(bolts) != 2 or len(loads) != 6:
        raise ValueError("Unexpected backing connection inventory")
    tangent = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
    station = lambda c: (c.start-b.point(0, 0, 0)).dot(tangent)
    if abs(station(bolts[0])-station(bolts[1])) > 1e-8:
        raise ValueError("Projected supports must share slope station")
    rows = []
    for c in loads:
        if (c.direction-b.normal()).Length > 1e-8:
            raise ValueError("Unexpected panel attachment direction")
        left, right = reactions(bolts[0].start.x, bolts[1].start.x, c.start.x, 1.)
        rows.append({"attachment": c.name, "x_mm": c.start.x,
            "s_mm": station(c), "left_reaction_per_unit_outward": left,
            "right_reaction_per_unit_outward": right,
            "largest_positive_retention_multiplier": max(left, right),
            "unrepresented_world_x_moment_nmm_per_n": -(station(c)-station(bolts[0]))})
    return {"candidate": frame.KEY,
        "model": "Two point supports at bolt X coordinates; outward force projected to bolt S station",
        "limits": "Conditional planar influence coefficients, NOT actual bolt forces or a conservative bound. "
                  "Positive reaction may require retention; negative reaction needs a compression path. "
                  "Finite housing contact, panel/frame load sharing, rail bending/torsion, joint compliance, "
                  "preload and resistance unqualified. Real attachment S offsets leave additional torsion.",
        "support_x_mm": [c.start.x for c in bolts], "support_s_mm": station(bolts[0]),
        "source_export_manifest": "exports/wide-principal-development/manifest.json",
        "rows": rows}


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build(), indent=2)+"\n")
