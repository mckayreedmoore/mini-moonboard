"""PB-02 solid 4x4 rip side-cleat/link-axis follow-up; nominal CAD only."""

import csv
import json
import sys
from pathlib import Path
from unittest.mock import patch

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_edge_reserve_probe as prior
from scripts import simple_center_wide_post_probe as wide

SIDE = cq.Solid.makeBox(88.9, 56.8, 183, cq.Vector(89.05, -175.7, 277))
LINK_X = 133.5
UPRIGHT_RIGHT_X = 177.95
SIDE_BLANK_NOMINAL_MM = [88.9, 88.9, 183]
SIDE_FINISHED_NOMINAL_MM = [88.9, 56.8, 183]


def probe():
    """Check a solid 4x4 rip and the longer upright through-path."""
    with patch.object(wide, "SIDE", SIDE), patch.object(prior, "LINK_X", LINK_X):
        trial = prior.probe()

    parts = {part.name: part.shape for part in wide.frame.uncut_wood_parts()}
    parts.pop("base_post_center_right")
    parts.update(
        shifted_right_post=cq.Solid.makeBox(
            88.9, 88.9, wide.POST_TOP, cq.Vector(wide.POST_X, wide.POST_REAR_Y, 0)
        ),
        backer=wide.BACKER,
        rear_cleat=cq.Solid.makeBox(88.9, 38.1, 460, cq.Vector(89.05, -213.8, 0)),
        upright_side_cleat=SIDE,
    )
    # The previous right endpoint at X=139.85 is now buried in the wider
    # cleat. Recheck the full upright/side through-bore at its exposed face.
    upright = cq.Solid.makeCylinder(
        wide.BORE_RADIUS,
        UPRIGHT_RIGHT_X - 50.95,
        cq.Vector(50.95, -147.3, 350),
        cq.Vector(1, 0, 0),
    )
    intended = ("base_principal_center_right", "upright_side_cleat")
    trial["bore_received_fraction"]["upright"] = round(
        sum(wide.hit_volume(upright, parts[name]) for name in intended)
        / upright.Volume(),
        8,
    )
    trial["bore_unintended_wood_hits_mm3"] = {
        k: v
        for k, v in trial["bore_unintended_wood_hits_mm3"].items()
        if not k.startswith("upright/")
    }
    trial["bore_unintended_wood_hits_mm3"].update(
        {
            f"upright/{name}": round(volume, 5)
            for name, wood in parts.items()
            if name not in intended
            if (volume := wide.hit_volume(upright, wood)) > wide.TOL
        }
    )

    trial["fixed_screw_hits_mm3"] = {
        k: v
        for k, v in trial["fixed_screw_hits_mm3"].items()
        if not k.startswith("bore/upright/")
    }
    for row in csv.DictReader(wide.AXES.open(newline="")):
        name = row["name"]
        if not name.startswith(("round_panel_", "round_kicker_", "kicker_header_")):
            continue
        screw = cq.Solid.makeCylinder(
            float(row["modeled_diameter_mm"]) / 2,
            float(row["shop_purchased_length_mm"]),
            cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz")),
            cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz")),
        )
        if (volume := wide.hit_volume(upright, screw)) > wide.TOL:
            trial["fixed_screw_hits_mm3"][f"bore/upright/{name}"] = round(volume, 5)

    other_bores = {
        **{
            name: cq.Solid.makeCylinder(
                wide.BORE_RADIUS,
                127,
                cq.Vector(prior.BOLT_X, -213.8, z),
                cq.Vector(0, 1, 0),
            )
            for name, z in zip(("post_low", "post_high"), wide.BOLT_Z)
        },
        "cleat_link": cq.Solid.makeCylinder(
            wide.BORE_RADIUS,
            94.9,
            cq.Vector(LINK_X, -213.8, 370),
            cq.Vector(0, 1, 0),
        ),
    }
    trial["bore_pair_hits_mm3"] = {
        f"upright/{name}": round(volume, 5)
        for name, bore in other_bores.items()
        if (volume := wide.hit_volume(upright, bore)) > wide.TOL
    } | trial["bore_pair_hits_mm3"]

    outward = cq.Vector(1, 0, 0)
    end = cq.Vector(UPRIGHT_RIGHT_X, -147.3, 350)
    washer = cq.Solid.makeCylinder(10, 0.01, end, cq.Vector(-1, 0, 0))
    tool = cq.Solid.makeCylinder(20, 20, end, outward)
    trial["washer_bearing_fraction"]["upright_right"] = round(
        wide.hit_volume(washer, SIDE) / washer.Volume(), 8
    )
    trial["trial_20mm_radius_tool_wood_hits_mm3"] = {
        k: v
        for k, v in trial["trial_20mm_radius_tool_wood_hits_mm3"].items()
        if not k.startswith("upright_right/")
    }
    trial["trial_20mm_radius_tool_wood_hits_mm3"].update(
        {
            f"upright_right/{name}": round(volume, 5)
            for name, wood in parts.items()
            if (volume := wide.hit_volume(tool, wood)) > wide.TOL
        }
    )
    rear = trial["cleat_bounds_mm"]["rear"]
    side = trial["cleat_bounds_mm"]["side"]
    trial["actual_edge_end_mm"]["cleat_link_side_x_edges"] = [
        round(LINK_X - side[0], 5),
        round(side[1] - LINK_X, 5),
    ]
    trial["actual_edge_end_mm"]["cleat_link_x_edges"] = [
        round(LINK_X - rear[0], 5),
        round(rear[1] - LINK_X, 5),
    ]
    trial["minimum_link_4d_x_reserve_mm"] = round(
        min(
            *trial["actual_edge_end_mm"]["cleat_link_x_edges"],
            *trial["actual_edge_end_mm"]["cleat_link_side_x_edges"],
        )
        - trial["conditional_4d_mm"],
        5,
    )
    trial["upright_bolt_x_span_mm"] = [50.95, UPRIGHT_RIGHT_X]
    trial["link_bolt_x_mm"] = LINK_X
    trial["side_stock"] = {
        "blank_nominal_mm": SIDE_BLANK_NOMINAL_MM,
        "finished_nominal_mm": SIDE_FINISHED_NOMINAL_MM,
        "nominal_y_removed_including_kerf_mm": 32.1,
        "kerf_mm": None,
        "single_solid_no_pocket": True,
    }
    return trial


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
