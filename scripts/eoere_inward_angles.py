"""Build an unadopted six-millimetre inward upper-angle geometry proposal.

The move is closed through shared bolt attachments. Affected receivers are
rebuilt from computational fresh stock by restoring every old bolt bore before
machining the current bore positions. This does not represent physical repair,
transfer forces, or qualify a complete joint.
"""

from __future__ import annotations

import argparse
import copy
import inspect
import json
import math
from pathlib import Path

from scripts import eoere_bolted_candidate as angles
from scripts import eoere_leg_header_clearance as clearance
from scripts import eoere_leg_header_revision as revision
from scripts.eoere_paired_frame_basis import ROOT, read, ref, sha
from scripts.eoere_v6_analysis import BASE as ANALYSIS_BASE

OWN = Path(__file__).resolve()
RECEIPT = Path("docs/bolted-frame-development/owner-frame-v6/geometry.json")
EXPECTED_RECEIPT_SHA256 = (
    "d2849e0bb7e3751396854556fa0bb411d83f3cf94dec55ec157a582f4f5b6e80"
)
OUTPUT = ANALYSIS_BASE / "inward-angle-study-v1/geometry"
REVISION = "eoere-v6-inward-upper-angle-translation-v1"
SHIFT_MM = 6.0
SEED_ANGLES = {
    "eoere_clip_angle_base_left",
    "eoere_clip_angle_base_right",
    "eoere_clip_split_base_center_left",
    "eoere_clip_split_base_center_right",
}
EXPECTED_ANGLES = SEED_ANGLES | {
    "eoere_clip_header_outer_under_left",
    "eoere_clip_header_outer_under_right",
    "eoere_clip_split_header_center_left",
    "eoere_clip_split_header_center_right",
}
WOOD_RECEIVERS = {
    "base_header",
    "base_side_left",
    "base_side_right",
    "base_principal_center_left",
    "base_principal_center_right",
    "base_post_outer_left",
    "base_post_outer_right",
    "base_post_center_left",
    "base_post_center_right",
    "eoere_cleat_left",
    "eoere_cleat_right",
    "eoere_cleat_left_outer",
    "eoere_cleat_right_outer",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _bounds(body) -> list[float]:
    box = body.BoundingBox()
    return [getattr(box, axis + end) for axis in "xyz" for end in ("min", "max")]


def _axis_component(direction: list[float]) -> tuple[int, float]:
    _require(
        len(direction) == 3 and all(math.isfinite(v) for v in direction),
        "finite three-component bolt axis required",
    )
    nonzero = [i for i, value in enumerate(direction) if abs(value) > 1e-8]
    _require(len(nonzero) == 1, "receiver wall axis must be parallel to X or Z")
    index = nonzero[0]
    _require(
        index in (0, 2) and abs(abs(direction[index]) - 1.0) < 1e-8,
        "receiver wall axis must be a unit X or Z axis",
    )
    return index, math.copysign(1.0, direction[index])


def _full_wall_cylinder(
    body, point: list[float], direction: list[float], diameter: float
):
    """Create a bore across the receiver's projected stock width on X or Z."""
    import cadquery as cq

    _require(
        len(point) == 3 and all(math.isfinite(v) for v in point),
        "finite three-component bore point required",
    )
    _require(
        math.isfinite(diameter) and diameter > 0.0, "positive bore diameter required"
    )
    index, sign = _axis_component(direction)
    box = body.BoundingBox()
    axis_name = "xyz"[index]
    low, high = getattr(box, axis_name + "min"), getattr(box, axis_name + "max")
    _require(
        math.isfinite(low) and math.isfinite(high) and high > low,
        "positive receiver wall span required",
    )
    start = list(point)
    start[index] = low if sign > 0.0 else high
    unit = [0.0, 0.0, 0.0]
    unit[index] = sign
    cylinder = cq.Solid.makeCylinder(
        diameter / 2.0, high - low, cq.Vector(*start), cq.Vector(*unit)
    )
    return cylinder, high - low


def _flat_cleat_outline(body) -> list[tuple[float, float]]:
    """Return the two straight-sided X-face outlines of a plywood leaf."""
    outlines = []
    for face in body.Faces():
        if face.geomType() != "PLANE":
            continue
        normal = face.normalAt()
        if abs(abs(normal.x) - 1.0) > 1e-8:
            continue
        edges = face.outerWire().Edges()
        _require(
            len(edges) == 4 and all(edge.geomType() == "LINE" for edge in edges),
            "each cleat flat face must retain its four straight outline edges",
        )
        points = sorted(
            {
                (round(vertex.Y, 8), round(vertex.Z, 8))
                for vertex in face.outerWire().Vertices()
            }
        )
        _require(len(points) == 4, "four distinct Y/Z perimeter vertices required")
        outlines.append(points)
    _require(
        len(outlines) == 2 and outlines[0] == outlines[1],
        "both plywood flat faces must share one four-sided outline",
    )
    return outlines[0]


def _closure(geometry: dict) -> tuple[set[str], set[str]]:
    poses = {row["id"] for row in geometry["fitting_poses"]}
    moved_angles, moved_axes = set(SEED_ANGLES), set()
    _require(
        moved_angles <= poses, "all four owner-directed base-angle seeds must exist"
    )
    changed = True
    while changed:
        changed = False
        for axis in geometry["axes"]:
            attached = {port["angle_id"] for port in axis["attachments"]}
            if axis["id"] not in moved_axes and attached & moved_angles:
                moved_axes.add(axis["id"])
                changed = True
                for angle_id in attached & poses:
                    if angle_id not in moved_angles:
                        moved_angles.add(angle_id)
                        changed = True
    _require(
        moved_angles == EXPECTED_ANGLES,
        f"shared-axis closure changed: {sorted(moved_angles)}",
    )
    _require(len(moved_axes) == 24, "the eight-angle closure must move 24 bolt axes")
    return moved_angles, moved_axes


def build(out: Path = OUTPUT) -> dict:
    """Write a fresh ignored geometry proposal and incremental clearance check."""
    out = Path(out).resolve()
    _require(
        Path.cwd() == ROOT, "run the guarded clearance adapter from the repository root"
    )
    _require(
        out == OUTPUT.resolve() and not out.exists(),
        "fresh analysis/inward-angle-study-v1/geometry output required",
    )

    pins = {ref(OWN)["path"]: sha(OWN)}
    receipt = read(RECEIPT, pins, EXPECTED_RECEIPT_SHA256)
    geometry_ref = receipt["checked_geometry"]
    source_path = Path(geometry_ref["path"])
    source = read(source_path, pins, geometry_ref["sha256"])
    prior_clearance_ref = receipt["checked_clearance"]
    prior_clearance = read(
        prior_clearance_ref["path"], pins, prior_clearance_ref["sha256"]
    )
    _require(
        prior_clearance.get("geometry") == geometry_ref
        and prior_clearance.get("nominal_geometry_clear")
        and not prior_clearance.get("collisions")
        and not prior_clearance.get("missing_candidates"),
        "the unchanged v6 occupied-clearance receipt must be admitted",
    )
    _require(
        source["revision"] == "eoere-flat-cleats-principal-upper-pairs-v6"
        and len(source["axes"]) == 96
        and len(source["fitting_poses"]) == 24
        and len(source["screw_axes"]) == 66
        and len(source["profiles"]) == 30,
        "authenticated current v6 inventory required",
    )

    g = copy.deepcopy(source)
    original = copy.deepcopy(source)
    moved_angles, moved_axes = _closure(g)
    output_geometry = out / "geometry.json"
    out.mkdir(parents=True)

    import cadquery as cq

    shape_cache = {}

    def load(row: dict):
        path = row["path"]
        _require(sha(path) == row["sha256"], "cached BRep differs: " + path)
        pins[path] = row["sha256"]
        if path not in shape_cache:
            shape = cq.Shape.importBrep(str(ROOT / path))
            _require(
                shape.isValid() and len(shape.Solids()) == 1 and shape.Volume() > 0.0,
                "one valid cached solid required: " + path,
            )
            shape_cache[path] = shape
        return shape_cache[path]

    changed = {row["id"]: copy.deepcopy(row) for row in g["changed_finished_solids"]}
    replacements: set[str] = set()
    hardware_moves, angle_moves, axis_moves = [], [], []

    def save(identity: str, body, kind: str) -> dict:
        _require(
            body.isValid() and len(body.Solids()) == 1 and body.Volume() > 0.0,
            "replacement must be one valid solid: " + identity,
        )
        path = out / (identity + ".brep")
        _require(body.exportBrep(str(path)), "BRep export failed: " + identity)
        restored = cq.Shape.importBrep(str(path))
        _require(
            restored.isValid()
            and len(restored.Solids()) == 1
            and abs(restored.Volume() - body.Volume()) < 1e-6,
            "BRep round trip differs: " + identity,
        )
        row = {
            "id": identity,
            "kind": kind,
            "path": str(path.relative_to(ROOT)),
            "sha256": sha(path),
            "bytes": path.stat().st_size,
            "volume_mm3": restored.Volume(),
            "center_of_mass_xyz_mm": list(restored.Center().toTuple()),
            "bounds_xyz_mm": _bounds(restored),
        }
        changed[identity] = row
        replacements.add(identity)
        if identity in g["profiles"]:
            g["profiles"][identity]["finished"] = row
        return row

    # Compute shared fit receivers before translating axes and attachments.
    receivers: dict[tuple[str, str], set[str]] = {}
    for axis in original["axes"]:
        for port in axis["attachments"]:
            if port["angle_id"] in moved_angles:
                receivers.setdefault((port["angle_id"], port["flange"]), set()).add(
                    port["receiver"]
                )
    receiver_map = {}
    for angle_id in moved_angles:
        for flange in ("beam", "post"):
            names = receivers.get((angle_id, flange), set())
            _require(
                len(names) == 1, f"unique {flange} receiver required for {angle_id}"
            )
            receiver_map[(angle_id, flange)] = next(iter(names))

    # Reconstruct all eight current catalog angles from the pinned factory template.
    template = angles.template(angles.Scenario())
    pose_rows = {row["id"]: row for row in g["fitting_poses"]}
    for angle_id in sorted(moved_angles):
        before = pose_rows[angle_id]
        after = copy.deepcopy(before)
        old_origin = list(before["origin_xyz_mm"])
        after["origin_xyz_mm"] = [
            old_origin[0],
            old_origin[1] + SHIFT_MM,
            old_origin[2],
        ]
        fitted = angles.pose(
            {
                **after,
                "beam": receiver_map[(angle_id, "beam")],
                "post": receiver_map[(angle_id, "post")],
            },
            template,
        ).shape
        prior = angles.pose(
            {
                **before,
                "beam": receiver_map[(angle_id, "beam")],
                "post": receiver_map[(angle_id, "post")],
            },
            template,
        ).shape
        old_bounds, new_bounds = _bounds(prior), _bounds(fitted)
        expected = [
            value + (SHIFT_MM if i in (2, 3) else 0.0)
            for i, value in enumerate(old_bounds)
        ]
        _require(
            max(abs(a - b) for a, b in zip(expected, new_bounds, strict=True)) < 1e-6,
            "reconstructed angle pose must be a pure +6 mm world-Y translation",
        )
        pose_rows[angle_id] = after
        save(angle_id, fitted, "angle")
        angle_moves.append(
            {
                "angle_id": angle_id,
                "before_origin_xyz_mm": old_origin,
                "after_origin_xyz_mm": after["origin_xyz_mm"],
                "receiver_by_flange": {
                    flange: receiver_map[(angle_id, flange)]
                    for flange in ("beam", "post")
                },
            }
        )
    g["fitting_poses"] = [pose_rows[row["id"]] for row in g["fitting_poses"]]

    # Move every stack component, including spacer pieces, for all 24 shared axes.
    selected = {row["axis_id"]: row for row in g["selected_stack_overrides"]}
    axes_by_id = {row["id"]: row for row in g["axes"]}
    for axis_id in sorted(moved_axes):
        axis = axes_by_id[axis_id]
        before = list(axis["point_xyz_mm"])
        axis["point_xyz_mm"] = [before[0], before[1] + SHIFT_MM, before[2]]
        moved_attachment_ids = set()
        for port in axis["attachments"]:
            _require(
                port["angle_id"] in moved_angles,
                "every attachment on a moved shared axis must join closure",
            )
            port["point"] = [
                port["point"][0],
                port["point"][1] + SHIFT_MM,
                port["point"][2],
            ]
            moved_attachment_ids.add(port["angle_id"])
        axis_moves.append(
            {
                "axis_id": axis_id,
                "before_xyz_mm": before,
                "after_xyz_mm": axis["point_xyz_mm"],
                "attachment_count": len(axis["attachments"]),
                "attached_angle_ids": sorted(moved_attachment_ids),
            }
        )

        old_part_ids = sorted(
            name for name in changed if name.startswith(axis_id + "_")
        )
        spacer_count = int(float(selected[axis_id].get("spacer_piece_count", 0)))
        _require(
            len(old_part_ids) == 5 + spacer_count and len(old_part_ids) in (5, 6, 8),
            f"complete five/six/eight-piece stack required for {axis_id}",
        )
        role_names = sorted(name[len(axis_id) + 1 :] for name in old_part_ids)
        for name in old_part_ids:
            original_row = changed[name]
            shape = load(original_row).translate(cq.Vector(0.0, SHIFT_MM, 0.0))
            bounds_before = original_row["bounds_xyz_mm"]
            bounds_after = _bounds(shape)
            expected = [
                value + (SHIFT_MM if i in (2, 3) else 0.0)
                for i, value in enumerate(bounds_before)
            ]
            _require(
                max(abs(a - b) for a, b in zip(expected, bounds_after, strict=True))
                < 1e-6,
                "hardware part must receive the same pure world-Y translation",
            )
            save(name, shape, original_row["kind"])
        hardware_moves.append(
            {
                "axis_id": axis_id,
                "part_ids": old_part_ids,
                "part_roles": role_names,
                "complete_piece_count": len(old_part_ids),
            }
        )

    revision.verify_attachment_axes(g["axes"], expected_ports=96)

    # Restore all old bolt bores in every affected receiver before any recutting.
    original_axes = {row["id"]: row for row in original["axes"]}
    old_bores_by_wood = {name: [] for name in WOOD_RECEIVERS}
    for axis in original["axes"]:
        for receiver in axis["receivers"]:
            if receiver in old_bores_by_wood:
                old_bores_by_wood[receiver].append(axis)
    _require(
        sum(map(len, old_bores_by_wood.values())) == 78,
        "the 13 affected members must contain 78 original receiver walls",
    )

    source_bodies = {
        name: load(original["profiles"][name]["finished"])
        for name in sorted(WOOD_RECEIVERS)
    }
    fresh_stock, restoration_proofs = {}, []
    for name in sorted(WOOD_RECEIVERS):
        original_body = source_bodies[name]
        tools, individual = [], []
        for axis in old_bores_by_wood[name]:
            cylinder, span = _full_wall_cylinder(
                original_body,
                axis["point_xyz_mm"],
                axis["direction_xyz"],
                axis["bore_diameter_mm"],
            )
            intersection = cylinder.intersect(original_body).Volume()
            _require(
                intersection < 1e-4,
                f"old full-wall bore must be absent from cached wood: {axis['id']} / {name}",
            )
            tools.append(cylinder)
            individual.append(
                {
                    "axis_id": axis["id"],
                    "receiver": name,
                    "projected_wall_span_mm": span,
                    "bore_diameter_mm": axis["bore_diameter_mm"],
                    "cylinder_volume_mm3": cylinder.Volume(),
                    "old_wood_intersection_mm3": intersection,
                }
            )
        _require(tools, f"at least one original bolt bore must be restored: {name}")
        union = tools[0]
        for tool in tools[1:]:
            union = union.fuse(tool)
        union = union.clean()
        missing = union.intersect(original_body).Volume()
        _require(
            missing < 1e-4, f"old-hole restoration union overlaps retained wood: {name}"
        )
        restored = original_body.fuse(union).clean()
        restored_delta = restored.Volume() - original_body.Volume()
        _require(
            restored.isValid()
            and len(restored.Solids()) == 1
            and abs(restored_delta - union.Volume()) < 0.01,
            f"fresh-stock bore restoration volume differs: {name}",
        )
        old_bounds, stock_bounds = _bounds(original_body), _bounds(restored)
        _require(
            max(abs(a - b) for a, b in zip(old_bounds, stock_bounds, strict=True))
            < 1e-6,
            f"fresh-stock restoration must preserve the member envelope: {name}",
        )
        fresh_stock[name] = restored
        restoration_proofs.append(
            {
                "receiver": name,
                "old_bore_count": len(tools),
                "old_bores": individual,
                "restoration_union_volume_mm3": union.Volume(),
                "restored_stock_volume_mm3": restored.Volume(),
                "restored_volume_delta_mm3": restored_delta,
                "restoration_union_intersection_with_old_wood_mm3": missing,
                "fresh_stock_only_not_a_physical_repair": True,
            }
        )

    # Machine every current receiver bore from the restored stock at its new pose.
    current_axes = {name: [] for name in WOOD_RECEIVERS}
    for axis in g["axes"]:
        for receiver in axis["receivers"]:
            if receiver in current_axes:
                current_axes[receiver].append(axis)
    _require(
        sum(map(len, current_axes.values())) == 78,
        "all 78 current receiver walls must be recut",
    )
    reboring_proofs = []
    cleat_names = {name for name in WOOD_RECEIVERS if name.startswith("eoere_cleat_")}
    cleat_outlines_before = {
        name: _flat_cleat_outline(source_bodies[name]) for name in cleat_names
    }
    for name in sorted(WOOD_RECEIVERS):
        stock = fresh_stock[name]
        tools, bore_rows = [], []
        for axis in current_axes[name]:
            cylinder, span = _full_wall_cylinder(
                stock,
                axis["point_xyz_mm"],
                axis["direction_xyz"],
                axis["bore_diameter_mm"],
            )
            outside = cylinder.cut(stock).Volume()
            _require(
                outside < 1e-4,
                f"current full-wall bore must lie within fresh stock: {axis['id']} / {name}",
            )
            tools.append(cylinder)
            bore_rows.append(
                {
                    "axis_id": axis["id"],
                    "receiver": name,
                    "center_xyz_mm": list(axis["point_xyz_mm"]),
                    "direction_xyz": list(axis["direction_xyz"]),
                    "projected_wall_span_mm": span,
                    "bore_diameter_mm": axis["bore_diameter_mm"],
                    "cylinder_volume_mm3": cylinder.Volume(),
                    "cylinder_outside_fresh_stock_mm3": outside,
                }
            )
        _require(tools, f"at least one current bolt bore must be machined: {name}")
        union = tools[0]
        for tool in tools[1:]:
            union = union.fuse(tool)
        union = union.clean()
        _require(
            abs(union.Volume() - math.fsum(tool.Volume() for tool in tools)) < 0.01,
            f"distinct current bore cylinders must retain independent volumes: {name}",
        )
        before_cut = stock.Volume()
        after = stock.cut(union).clean()
        removed = before_cut - after.Volume()
        _require(
            after.isValid()
            and len(after.Solids()) == 1
            and abs(removed - union.Volume()) < 0.01,
            f"current bore removal must match the full-wall cylinder union: {name}",
        )
        original_bounds, after_bounds = _bounds(source_bodies[name]), _bounds(after)
        _require(
            max(abs(a - b) for a, b in zip(original_bounds, after_bounds, strict=True))
            < 1e-6,
            f"new bores must preserve the receiver envelope: {name}",
        )
        save(name, after, "timber")
        reboring_proofs.append(
            {
                "receiver": name,
                "new_bore_count": len(tools),
                "new_bores": bore_rows,
                "bore_union_volume_mm3": union.Volume(),
                "removed_wood_volume_mm3": removed,
                "remaining_wood_volume_mm3": after.Volume(),
            }
        )

    cleat_outlines_after = {
        name: _flat_cleat_outline(load(g["profiles"][name]["finished"]))
        for name in cleat_names
    }
    _require(
        cleat_outlines_after == cleat_outlines_before,
        "all four flat-cleat outlines must remain the current four-sided shape",
    )

    for axis in g["axes"]:
        old_axis = original_axes[axis["id"]]
        if axis["id"] not in moved_axes:
            _require(
                axis == old_axis,
                "unattached bolt axes must remain byte-equivalent data",
            )
        else:
            _require(
                axis["point_xyz_mm"]
                == [
                    old_axis["point_xyz_mm"][0],
                    old_axis["point_xyz_mm"][1] + SHIFT_MM,
                    old_axis["point_xyz_mm"][2],
                ],
                "all closed axes must translate exactly six millimetres in world Y",
            )
    _require(
        g["screw_axes"] == original["screw_axes"] and len(g["screw_axes"]) == 66,
        "all 66 panel and kicker screw descriptors must remain identical",
    )
    _require(
        len(g["axes"]) == 96
        and len(g["fitting_poses"]) == 24
        and len(g["profiles"]) == 30,
        "all physical member and hardware counts must remain unchanged",
    )
    for name, profile in g["profiles"].items():
        before = {
            k: v for k, v in original["profiles"][name].items() if k != "finished"
        }
        after = {k: v for k, v in profile.items() if k != "finished"}
        _require(
            after == before, f"member section and outline metadata changed: {name}"
        )

    g.update(
        revision=REVISION,
        parent_owner_geometry=geometry_ref,
        geometry_adopted=False,
        new_response_computed=False,
        complete_joint_qualified=False,
        release=False,
        changed_finished_solids=[changed[name] for name in sorted(changed)],
        source_sha256={**g.get("source_sha256", {}), **pins},
        inward_angle_study={
            "revision": REVISION,
            "parent_geometry": geometry_ref,
            "prior_clearance": prior_clearance_ref,
            "world_translation_xyz_mm": [0.0, SHIFT_MM, 0.0],
            "seed_angle_ids": sorted(SEED_ANGLES),
            "moved_angle_ids": sorted(moved_angles),
            "moved_axis_ids": sorted(moved_axes),
            "angle_moves": angle_moves,
            "axis_moves": axis_moves,
            "complete_hardware_stack_moves": hardware_moves,
            "affected_wood_receivers": sorted(WOOD_RECEIVERS),
            "old_bore_restoration_proofs": restoration_proofs,
            "current_full_wall_reboring_proofs": reboring_proofs,
            "flat_cleat_outline_preserved": {
                name: cleat_outlines_after[name] for name in sorted(cleat_names)
            },
            "panel_and_kicker_screws_changed": False,
            "member_outlines_changed": False,
            "fresh_stock_only_not_a_physical_repair_instruction": True,
            "prior_force_results_transferred": False,
            "geometry_adopted": False,
            "complete_joint_or_frame_qualified": False,
        },
    )

    snapshot = out / "producer-snapshot.py"
    snapshot.write_bytes(OWN.read_bytes())
    snapshot_ref = ref(snapshot)
    g["inward_angle_study"]["source_snapshot"] = snapshot_ref
    g["source_sha256"].update({snapshot_ref["path"]: snapshot_ref["sha256"]})
    # Include every builder/adapter whose behavior defines this geometry receipt.
    for path in (
        angles.__file__,
        clearance.__file__,
        revision.__file__,
        Path(__file__).with_name("eoere_paired_frame_basis.py"),
        Path(__file__).with_name("eoere_v6_analysis.py"),
    ):
        path = Path(path).resolve().relative_to(ROOT)
        pins[str(path)] = sha(path)
    g["source_sha256"].update(pins)
    for path, digest in pins.items():
        _require(sha(path) == digest, "source changed during geometry build: " + path)

    output_geometry.write_text(
        json.dumps(g, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )

    # Reuse the pinned 1,037-part exact-intersection method, checking only new parts.
    code = inspect.getsource(clearance.check)
    patches = {
        "    geometry = read(geometry_path)": "    geometry = read(geometry_path)\n    read(PRIOR_CLEARANCE, PRIOR_HASH)",
        "    for first in sorted(changed):": "    for first in sorted(REPLACEMENT_IDS):",
        "'occupied_part_count': len(bank),": "'reused_unchanged_pair_clearance': PRIOR_REF, "
        "'newly_checked_part_ids': sorted(REPLACEMENT_IDS), 'occupied_part_count': len(bank),",
    }
    for before, after in patches.items():
        _require(
            code.count(before) == 1,
            "clearance adapter source anchor changed: " + before,
        )
        code = code.replace(before, after)
    scope = {
        **vars(clearance),
        "PRIOR_CLEARANCE": Path(prior_clearance_ref["path"]),
        "PRIOR_HASH": prior_clearance_ref["sha256"],
        "PRIOR_REF": prior_clearance_ref,
        "REPLACEMENT_IDS": replacements,
    }
    exec(compile(code, str(OWN), "exec"), scope)  # noqa: S102 -- reuse the pinned checker with an explicit incremental part set
    scope["check"](output_geometry, out / "clearance.json")
    result = json.loads((out / "clearance.json").read_bytes())
    _require(
        result["occupied_part_count"] == 1037
        and set(result["newly_checked_part_ids"]) == replacements,
        "incremental clearance must cover every replacement against the full occupied registry",
    )
    result_summary = {
        key: result[key]
        for key in (
            "occupied_part_count",
            "changed_parts",
            "nominal_geometry_clear",
            "collisions",
            "missing_candidates",
            "intentional_screw_engagements",
        )
    }
    summary_path = out / "build-summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "geometry": ref(output_geometry),
                "clearance": ref(out / "clearance.json"),
                "replacement_part_count": len(replacements),
                "moved_angle_count": len(moved_angles),
                "moved_axis_count": len(moved_axes),
                "affected_wood_count": len(WOOD_RECEIVERS),
                "old_bore_wall_count": 78,
                "current_bore_wall_count": 78,
                "clearance_result": result_summary,
                "geometry_adopted": False,
                "prior_force_results_transferred": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return json.loads(summary_path.read_bytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?", default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(build(args.output), sort_keys=True), flush=True)
