"""One nominal UB66/B66 installed center trial; never drilling data."""

import argparse
import csv
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
REACH = 152.4
WIDTH = 38.1
SHEET = 2.66  # Illustrative envelope; delivered bend and coating unknown.
BORE = 10.3  # DXF circle diameter, not a specified wood drill size.
OFFSETS = (25.4, 126.744)  # Approximate free-end centers from official DXF.
HEADER_DEPTH = 76.2
POST_WIDTH = 184.15
POST_DEPTH = 139.7
PRINCIPAL_WIDTH = 88.9


def box(x, y, z, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x, y, z))


def hits(shape, others):
    return [
        name for name, other in others.items() if shape.intersect(other).Volume() > 0.01
    ]


def screw(row):
    start = cq.Vector(*(float(row[f"start_{a}_mm"]) for a in "xyz"))
    direction = cq.Vector(*(float(row[f"direction_{a}"]) for a in "xyz"))
    return cq.Solid.makeCylinder(
        float(row["occupied_diameter_mm"]) / 2,
        float(row["occupied_length_mm"]),
        start,
        direction,
    )


def screen_b66_center():
    """Check one front-aligned post and rear-face lower / outer-face upper pose."""
    with AXES.open(newline="") as handle:
        rows = [
            r
            for r in csv.DictReader(handle)
            if r["shop_opening_kind"] == "hillman_panel"
        ]
    if len(rows) != 66 or len({r["name"] for r in rows}) != 66:
        raise ValueError("expected 66 distinct protected screw axes")
    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    hb = raw["base_header"].BoundingBox()
    front = raw["kicker_left"].BoundingBox().ymin
    if abs(front - raw["kicker_right"].BoundingBox().ymin) > 1e-5:
        raise ValueError("kicker back planes differ")
    rear = front - POST_DEPTH
    header = box(
        hb.xmin, rear - REACH, hb.zmin, hb.xlen, hb.ymax - rear + REACH, HEADER_DEPTH
    )
    post = box(-POST_WIDTH / 2, rear, 0, POST_WIDTH, POST_DEPTH, hb.zmin)
    principals = {}
    for side in ("left", "right"):
        source = raw[f"base_principal_center_{side}"]
        growth = (PRINCIPAL_WIDTH - source.BoundingBox().xlen) / 2
        wide = source.fuse(
            *(
                source.translate((d, 0, 0))
                for d in (-growth, -growth / 2, growth / 2, growth)
            )
        ).clean()
        b = wide.BoundingBox()
        principals[side] = wide.intersect(
            box(
                b.xmin - 1,
                b.ymin - 1,
                hb.zmin + HEADER_DEPTH,
                b.xlen + 2,
                b.ylen + 2,
                b.zmax - hb.zmin - HEADER_DEPTH + 1,
            )
        ).clean()

    plates = {}
    bores = {}
    receivers = {}
    # Lower factory legs sit on the single post's rear Y face, with seats
    # running rearward under the header. Upper legs sit on outer X faces.
    for side, cx in (("left", -70.0), ("right", 70.0)):
        key = f"lower_{side}"
        x0 = cx - WIDTH / 2
        plates[f"{key}_vertical"] = box(
            x0, rear - SHEET, hb.zmin - REACH, WIDTH, SHEET, REACH
        )
        plates[f"{key}_seat"] = box(
            x0, rear - REACH, hb.zmin - SHEET, WIDTH, REACH, SHEET
        )
        receivers[key] = post
        for i, offset in enumerate(OFFSETS, 1):
            z = hb.zmin - REACH + offset
            bores[f"{key}_vertical_{i}"] = cq.Solid.makeCylinder(
                BORE / 2, POST_DEPTH, cq.Vector(cx, rear, z), cq.Vector(0, 1, 0)
            )
            y = rear - REACH + offset
            bores[f"{key}_seat_{i}"] = cq.Solid.makeCylinder(
                BORE / 2, HEADER_DEPTH, cq.Vector(cx, y, hb.zmin), cq.Vector(0, 0, 1)
            )

        key = f"upper_{side}"
        member = principals[side]
        face = (
            member.BoundingBox().xmin if side == "left" else member.BoundingBox().xmax
        )
        vx = face - SHEET if side == "left" else face
        sx = face - REACH if side == "left" else face
        y0 = -137.6  # Rearward from fixed panel, within original header depth.
        plates[f"{key}_vertical"] = box(
            vx, y0, hb.zmin + HEADER_DEPTH, SHEET, WIDTH, REACH
        )
        plates[f"{key}_seat"] = box(sx, y0, hb.zmin + HEADER_DEPTH, REACH, WIDTH, SHEET)
        receivers[key] = member
        for i, offset in enumerate(OFFSETS, 1):
            z = hb.zmin + HEADER_DEPTH + REACH - offset
            b = member.BoundingBox()
            bores[f"{key}_vertical_{i}"] = cq.Solid.makeCylinder(
                BORE / 2,
                b.xlen,
                cq.Vector(b.xmin, y0 + WIDTH / 2, z),
                cq.Vector(1, 0, 0),
            )
            x = sx + REACH - offset if side == "left" else sx + offset
            bores[f"{key}_seat_{i}"] = cq.Solid.makeCylinder(
                BORE / 2,
                HEADER_DEPTH,
                cq.Vector(x, y0 + WIDTH / 2, hb.zmin),
                cq.Vector(0, 0, 1),
            )

    panels = {k: v for k, v in raw.items() if k.startswith(("kicker_", "main_"))}
    changed = {
        "header": header,
        "post": post,
        **{f"principal_{k}": v for k, v in principals.items()},
    }
    excluded = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_principal_center_left",
        "base_principal_center_right",
    }
    neighbors = {k: v for k, v in raw.items() if k not in excluded and k not in panels}
    protected = {r["name"]: screw(r) for r in rows}
    bore_targets = {
        name: header if "_seat_" in name else receivers["_".join(name.split("_")[:2])]
        for name in bores
    }
    missing = {
        name: round(
            max(0, bore.Volume() - bore.intersect(bore_targets[name]).Volume()), 3
        )
        for name, bore in bores.items()
        if bore.Volume() - bore.intersect(bore_targets[name]).Volume() > 0.01
    }

    def conflicts(first, second):
        return [
            f"{name}:{other}"
            for name, shape in first.items()
            for other in hits(shape, second)
        ]

    screw_receiver_count = sum(
        bool(
            hits(
                shape,
                {
                    "receiver": post
                    if r["second_member"].startswith("base_post_center_")
                    else principals[r["second_member"].split("_")[-1]]
                    if r["second_member"].startswith("base_principal_center_")
                    else raw[r["second_member"]]
                },
            )
        )
        for r in rows
        for shape in (protected[r["name"]],)
    )
    support = {
        side: post.BoundingBox().xmin <= edge <= post.BoundingBox().xmax
        and abs(post.BoundingBox().ymax - front) < 1e-5
        for side, edge in (
            ("left", panels["kicker_left"].BoundingBox().xmax),
            ("right", panels["kicker_right"].BoundingBox().xmin),
        )
    }
    plate_plate = [
        f"{a}:{b}"
        for i, (a, shape) in enumerate(plates.items())
        for b, other in list(plates.items())[i + 1 :]
        if "_".join(a.split("_")[:2]) != "_".join(b.split("_")[:2])
        and shape.intersect(other).Volume() > 0.01
    ]
    bore_bore = [
        f"{a}:{b}"
        for i, (a, shape) in enumerate(bores.items())
        for b, other in list(bores.items())[i + 1 :]
        if shape.intersect(other).Volume() > 0.01
    ]
    lower_post_outer_edge = POST_WIDTH / 2 - 70.0
    edge_filter = 4 * 9.525  # Reversible loaded-edge search filter, not NDS verdict.
    blockers = (
        lower_post_outer_edge < edge_filter
        or missing
        or conflicts(plates, panels)
        or conflicts(changed, panels)
        or conflicts(protected, plates)
        or conflicts(protected, bores)
        or conflicts(bores, panels)
        or conflicts(bores, neighbors)
        or conflicts(plates, neighbors)
        or conflicts(changed, neighbors)
        or plate_plate
        or bore_bore
    )
    return {
        "status": "rejected_nominal_installed_geometry"
        if blockers
        else "conditional_nominal_fit_only",
        "concept": "one front-aligned solid post; two rear-Y lower B66 and two outer-X upper B66; butt contact and removable through-bolts",
        "factory_pattern_source": "docs/bolted-candidate-prototypes/mitek-b66-drawing-followup.md",
        "width_option": KERF_RIGHT,
        "protected_axis_count": len(rows),
        "bracket_count": 4,
        "factory_circle_paths_screened": len(bores),
        "nominal_dxf_free_end_offsets_mm": list(OFFSETS),
        "nominal_circle_diameter_mm": BORE,
        "illustrative_sheet_mm": SHEET,
        "receiving_stock_mm": {
            "header_z": HEADER_DEPTH,
            "post_x": POST_WIDTH,
            "post_y": POST_DEPTH,
            "principals_x": PRINCIPAL_WIDTH,
        },
        "lower_post_outer_x_edge_screen": {
            "nominal_center_to_edge_mm": round(lower_post_outer_edge, 3),
            "conservative_4D_filter_mm": edge_filter,
            "passes_filter": lower_post_outer_edge >= edge_filter,
            "qualification": "3/8-in bolt reversible loaded-edge search filter only; not a formal NDS loaded-edge determination.",
        },
        "kicker_edge_backed": support,
        "protected_screw_receiver_intersection_count": screw_receiver_count,
        "panel_plate_conflicts": conflicts(plates, panels),
        "changed_wood_panel_conflicts": conflicts(changed, panels),
        "protected_screw_plate_conflicts": conflicts(protected, plates),
        "protected_screw_bore_conflicts": conflicts(protected, bores),
        "panel_bore_conflicts": conflicts(bores, panels),
        "bore_neighbor_conflicts": conflicts(bores, neighbors),
        "bore_bore_conflicts": bore_bore,
        "nominal_bores_missing_wood_mm3": missing,
        "plate_plate_conflicts": plate_plate,
        "plate_neighbor_conflicts": conflicts(plates, neighbors),
        "changed_wood_neighbor_conflicts": conflicts(changed, neighbors),
        "one_piece_stock_envelope": {
            "post_cross_section_mm": [POST_WIDTH, POST_DEPTH],
            "post_blank_bounding_mm": [POST_WIDTH, POST_DEPTH, round(hb.zmin, 2)],
            "header_cross_section_mm": [round(hb.ymax - rear + REACH, 2), HEADER_DEPTH],
            "header_span_mm": round(hb.xlen, 2),
            "header_blank_bounding_mm": [
                round(hb.xlen, 2),
                round(hb.ymax - rear + REACH, 2),
                HEADER_DEPTH,
            ],
            "principals_width_mm": PRINCIPAL_WIDTH,
            "principal_original_full_blank_envelope_each": {
                side: {
                    "bounding_xyz_mm": [
                        PRINCIPAL_WIDTH,
                        round(
                            raw[f"base_principal_center_{side}"].BoundingBox().ylen, 2
                        ),
                        round(
                            raw[f"base_principal_center_{side}"].BoundingBox().zlen, 2
                        ),
                    ],
                    "yz_bounding_diagonal_mm": round(
                        math.hypot(
                            raw[f"base_principal_center_{side}"].BoundingBox().ylen,
                            raw[f"base_principal_center_{side}"].BoundingBox().zlen,
                        ),
                        2,
                    ),
                }
                for side in principals
            },
            "retail_feasibility": "unverified blocker: the 184 x 140 x 239 mm one-piece post implies a nominal 6x8 class. A public Home Depot listing was found for 6x8x8 Douglas-fir pressure-treated stock, which changes the wood/service basis; no ordinary untreated DF-L No.2 big-box lead is established. The approximately 2435 x 292 x 76 mm one-piece header also lacks a verified ordinary untreated DF-L No.2 retail blank. Bounding sizes are minimum ideal solid envelopes, not purchase or cut instructions.",
            "two_post_alternative": "Not part of this trial. Two smaller posts plus separate seam backing add at least one backing-to-post connection to count and qualify; fixed x=±70 kicker screw axes and both seam edges need continuous verified receiving wood.",
        },
        "access_caveat": "Rear lower bolt heads and underside nuts require access behind and below the enlarged header; upper outer-face bolts require room beside principals. Full head/washer/nut stacks, grip, tool sweep, installation order, and removal with panels installed are not modeled.",
        "unmodeled": "Existing frame bolt axes and stacks after hidden-member changes, full washer/tool access, delivered bracket tolerances, and local untreated DF-L No.2 retail availability are not checked.",
        "disposition": "Reject this pose: lower post bolt X edge distance fails the conservative 4D filter; upper principal bores lack full wood; enlarged header and principals clash with neighboring wood, and upper plates clash with bottom rails. One-piece stock procurement and grade/service basis are additionally unresolved. No structural capacity, selection, fabrication, or drilling approval. ESR-3455 C_D=1.6 loads are not transferred to climbing use.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_b66_center(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
