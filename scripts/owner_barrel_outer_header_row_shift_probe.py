"""Detached four-pose sensitivity of recessed outer-header barrel rows.

These are nominal CAD envelopes, not drill dimensions or joint qualification.
Only the two forward rows move; the viewer and its wood/fixed axes are untouched.
"""

import json
from math import inf, sqrt

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import export_owner_barrel_scene as viewer
from scripts import owner_layout_protected as protected

SCHEMA = "owner_barrel_outer_header_row_shift_probe/v1"
OPTIONS_MM = (-75.0, -80.0, -85.0, -90.0)
SOURCE_FORWARD_Y_MM = -85.0
REAR_Y_MM = -135.0
HIT_TOL_MM3 = 1.0
ROLES = ("counterbore", "machine_bore", "barrel_bore")


def _axis_signature(row):
    return (
        row.name,
        row.start.toTuple(),
        row.direction.toTuple(),
        row.length,
        row.diameter,
        tuple(row.members),
    )


def _overlap_bounds(a, b):
    return all(
        min(getattr(a, f"{axis}max"), getattr(b, f"{axis}max"))
        > max(getattr(a, f"{axis}min"), getattr(b, f"{axis}min"))
        for axis in "xyz"
    )


def _bounds_gap(a, b):
    return sqrt(
        sum(
            max(
                getattr(a, f"{axis}min") - getattr(b, f"{axis}max"),
                getattr(b, f"{axis}min") - getattr(a, f"{axis}max"),
                0.0,
            )
            ** 2
            for axis in "xyz"
        )
    )


def _hit(a, b, a_box=None, b_box=None):
    a_box = a.BoundingBox() if a_box is None else a_box
    b_box = b.BoundingBox() if b_box is None else b_box
    if not _overlap_bounds(a_box, b_box):
        return 0.0
    volume = a.intersect(b).Volume()
    return round(volume, 6) if volume > HIT_TOL_MM3 else 0.0


def _fixed_axes_unchanged(assembly):
    source = variant(KERF_RIGHT)
    for key, expected in (
        ("panel_connections", tuple(source.panel_connections())),
        (
            "frame_connections",
            tuple(row for row in source.connections() if row.kind == "bolt"),
        ),
    ):
        actual = tuple(assembly[key])
        if len(actual) != (66 if key == "panel_connections" else 12) or tuple(
            map(_axis_signature, actual)
        ) != tuple(map(_axis_signature, expected)):
            raise ValueError(f"Fixed source axes changed: {key}")


def _source_rows(assembly):
    source_forward_y = assembly["diagnostics"]["producer_diagnostics"]["outer_top8"][
        "viewer_trial_outer_header_forward_y_mm"
    ]
    if abs(source_forward_y - SOURCE_FORWARD_Y_MM) > 1e-6:
        raise ValueError("Viewer outer-header forward row changed")
    rows = {}
    for side in ("left", "right"):
        station = f"clip_timber_header_outer_{side}"
        for index, source_y in ((1, REAR_Y_MM), (2, source_forward_y)):
            prefix = f"barrel_trial_{station}_{index}"
            bolt = f"{prefix}_bolt"
            paths = {
                role: assembly["drilling_paths"][f"{prefix}/{role}"] for role in ROLES
            }
            access = {
                role: assembly["access_paths"][f"{prefix}/{role}"]
                for role in ("bolt_access", "barrel_access")
            }
            stack = assembly["stacks"][bolt]
            axis = assembly["bolts"][bolt]
            if (
                assembly["barrel_station"].get(prefix) != station
                or assembly["bolt_station"].get(bolt) != station
                or set(stack) != {"shaft", "washer", "head"}
                or set(assembly["drilling_paths"])
                & {f"{prefix}/{role}" for role in ROLES}
                != {f"{prefix}/{role}" for role in ROLES}
                or abs(axis.start.y - source_y) > 1e-6
                or any(
                    abs(shape.Center().y - source_y) > 1e-5 for shape in paths.values()
                )
            ):
                raise ValueError(f"Viewer outer-header row changed: {prefix}")
            rows[prefix] = {
                "side": side,
                "index": index,
                "station": station,
                "source_y": source_y,
                "paths": paths,
                "access": access,
                "physical": {
                    f"barrel/{prefix}": assembly["barrels"][prefix],
                    **{f"bolt/{bolt}/{role}": shape for role, shape in stack.items()},
                },
            }
    if len(rows) != 4:
        raise ValueError("Expected four recessed outer-header rows")
    return rows, source_forward_y


def _shift_rows(rows, forward_y):
    result = {}
    for prefix, row in rows.items():
        delta = forward_y - row["source_y"] if row["index"] == 2 else 0.0
        move = cq.Vector(0, delta, 0)
        result[prefix] = {
            **{key: row[key] for key in ("side", "index", "station")},
            "y_mm": REAR_Y_MM if row["index"] == 1 else forward_y,
            "paths": {
                key: solid.translate(move) for key, solid in row["paths"].items()
            },
            "access": {
                key: solid.translate(move) for key, solid in row["access"].items()
            },
            "physical": {
                key: solid.translate(move) for key, solid in row["physical"].items()
            },
        }
    return result


def _nearest_fixed_cut(cutters, fixed):
    """Nearest distance from *removed wood* to one of the 66 fixed screw axes."""
    axes = fixed["solids"]["panel_screws"]
    boxes = fixed["bounds"]["panel_screws"]
    best = (inf, None, None)
    for path_name, removed in cutters.items():
        box = removed.BoundingBox()
        for name in axes:
            if _bounds_gap(box, boxes[name]) >= best[0]:
                continue
            distance = removed.distance(axes[name])
            if distance < best[0]:
                best = (distance, name, path_name)
    if best[1] is None:
        raise ValueError("No fixed screw-axis distance evaluated")
    return {
        "distance_mm": round(best[0], 6),
        "fixed_screw": best[1],
        "cut_path": best[2],
    }


def _cuts(rows, wood, fixed):
    assigned = {
        "base_header": [],
        "base_post_outer_left": [],
        "base_post_outer_right": [],
    }
    coverage = {}
    clipped = {}
    for prefix, row in rows.items():
        host_for = {
            "counterbore": ("base_header",),
            "machine_bore": ("base_header", f"base_post_outer_{row['side']}"),
            "barrel_bore": (f"base_post_outer_{row['side']}",),
        }
        for role, hosts in host_for.items():
            name = f"{prefix}/{role}"
            cutter = row["paths"][role]
            parts = [cutter.intersect(wood[host]) for host in hosts]
            total = sum(part.Volume() for part in parts)
            coverage[name] = round(total / cutter.Volume(), 6)
            for host, part in zip(hosts, parts):
                if part.Volume() > HIT_TOL_MM3:
                    assigned[host].append((name, part))
                    clipped[f"{name}@{host}"] = part
    members = {}
    for host, paths in assigned.items():
        uncut = wood[host]
        cut = uncut
        for _, part in paths:
            cut = cut.cut(part)
        members[host] = {
            "uncut_solid_count": len(uncut.Solids()),
            "cut_solid_count": len(cut.Solids()),
            "cut_is_valid": cut.isValid(),
            "removed_volume_mm3": round(uncut.Volume() - cut.Volume(), 6),
            "connected_nominally": len(cut.Solids()) == 1 and cut.isValid(),
        }
    return coverage, members, _nearest_fixed_cut(clipped, fixed)


def _protected_hits(rows, fixed):
    shapes = {
        f"{prefix}/{kind}/{role}": shape
        for prefix, row in rows.items()
        for kind, values in (
            ("cut", row["paths"]),
            ("hardware", row["physical"]),
            ("access", row["access"]),
        )
        for role, shape in values.items()
    }
    return {key: hit for key, hit in protected.hits(shapes, fixed).items() if hit}


def _other_inventory(assembly, row_names):
    physical = {
        f"barrel/{name}": shape
        for name, shape in assembly["barrels"].items()
        if name not in row_names
    }
    physical.update(
        {
            f"bolt/{name}/{role}": shape
            for name, stack in assembly["stacks"].items()
            if name.removesuffix("_bolt") not in row_names
            for role, shape in stack.items()
        }
    )
    paths = {
        f"cut/{name}": shape
        for name, shape in assembly["drilling_paths"].items()
        if name.split("/")[0] not in row_names
    }
    paths.update(
        {
            f"access/{name}": shape
            for name, shape in assembly["access_paths"].items()
            if name.split("/")[0] not in row_names
        }
    )
    return physical, paths


def _neighbor_hits(rows, other_physical, other_paths):
    """Compare each row with every *other* row's physical and path envelope."""
    current = {}
    for prefix, row in rows.items():
        for kind, values in (
            ("physical", row["physical"]),
            ("cut", row["paths"]),
            ("access", row["access"]),
        ):
            for name, shape in values.items():
                current[f"{prefix}|{kind}|{name}"] = (prefix, kind, shape)
    other = {
        **{f"physical|{name}": shape for name, shape in other_physical.items()},
        **{name: shape for name, shape in other_paths.items()},
    }
    hits = {}
    current_items = list(current.items())
    for i, (name, (prefix, kind, shape)) in enumerate(current_items):
        box = shape.BoundingBox()
        # Paths are cuts/access envelopes; report path-path as well as path-hardware.
        for other_name, other_shape in other.items():
            if volume := _hit(shape, other_shape, box, other_shape.BoundingBox()):
                hits[f"{name} -> {other_name}"] = volume
        for peer_name, (peer_prefix, peer_kind, peer_shape) in current_items[i + 1 :]:
            if prefix == peer_prefix:
                continue  # Designed bolt/barrel and own bore contacts are not clashes.
            if volume := _hit(shape, peer_shape, box, peer_shape.BoundingBox()):
                hits[f"{name} -> {peer_name}"] = volume
    return hits


def _row_wood_and_rim(rows, wood):
    data = {}
    for prefix, row in rows.items():
        own = {"base_header", f"base_post_outer_{row['side']}"}
        rim = wood[f"base_side_{row['side']}"]
        tool = row["access"]["bolt_access"]
        counterbore = row["paths"]["counterbore"]
        machine = row["paths"]["machine_bore"]
        barrel_bore = row["paths"]["barrel_bore"]
        hardware = row["physical"]
        washer = hardware[f"bolt/{prefix}_bolt/washer"]
        head = hardware[f"bolt/{prefix}_bolt/head"]
        shaft = hardware[f"bolt/{prefix}_bolt/shaft"]
        barrel = hardware[f"barrel/{prefix}"]
        data[prefix] = {
            "y_mm": row["y_mm"],
            "counterbore_diameter_mm": round(counterbore.BoundingBox().xlen, 6),
            "shaft_diameter_mm": round(shaft.BoundingBox().xlen, 6),
            "head_diameter_mm": round(head.BoundingBox().xlen, 6),
            "washer_diameter_mm": round(washer.BoundingBox().xlen, 6),
            "driver_diameter_mm": round(tool.BoundingBox().xlen, 6),
            "counterbore_wood_coverage": round(
                counterbore.intersect(wood["base_header"]).Volume()
                / counterbore.Volume(),
                6,
            ),
            "head_in_counterbore_fraction": round(
                head.intersect(counterbore).Volume() / head.Volume(), 6
            ),
            "washer_in_counterbore_fraction": round(
                washer.intersect(counterbore).Volume() / washer.Volume(), 6
            ),
            "machine_bore_meets_barrel_bore": _hit(machine, barrel_bore) > 0,
            "barrel_in_cross_bore_fraction": round(
                barrel.intersect(barrel_bore).Volume() / barrel.Volume(), 6
            ),
            "installed_stack_side_rim_hit_mm3": round(
                sum(_hit(shape, rim) for shape in hardware.values()), 6
            ),
            "rim_on_driver_hit_mm3": _hit(tool, rim),
            "tool_other_wood_hits_with_rim_removed_mm3": {
                name: volume
                for name, shape in wood.items()
                if name not in own | {f"base_side_{row['side']}"}
                if (volume := _hit(tool, shape))
            },
            "unrelated_wood_hits_mm3": {
                f"{kind}/{role}@{name}": volume
                for kind, values in (
                    ("cut", row["paths"]),
                    ("hardware", row["physical"]),
                )
                for role, item in values.items()
                for name, shape in wood.items()
                if name not in own
                if (volume := _hit(item, shape))
            },
        }
    return data


def _same_side_row_gaps(rows):
    result = {}
    for side in ("left", "right"):
        pair = sorted(
            (row for row in rows.values() if row["side"] == side),
            key=lambda row: row["index"],
        )
        if len(pair) != 2:
            raise ValueError(f"Missing outer-header pair: {side}")
        result[side] = round(
            pair[0]["paths"]["counterbore"].distance(pair[1]["paths"]["counterbore"]),
            6,
        )
    return result


def probe(*, assembly=None, fixed=None):
    """Screen actual nominal shifted solids without modifying any source object."""
    assembly = viewer.build_viewer_assembly() if assembly is None else assembly
    _fixed_axes_unchanged(assembly)
    if any(assembly["release_flags"].values()):
        raise ValueError("Source viewer unexpectedly carries release approval")
    rows, source_forward_y = _source_rows(assembly)
    fixed = protected.inventory() if fixed is None else fixed
    other_physical, other_paths = _other_inventory(assembly, set(rows))
    options = {}
    for forward_y in OPTIONS_MM:
        shifted = _shift_rows(rows, forward_y)
        coverage, members, nearest = _cuts(shifted, assembly["wood"], fixed)
        options[str(int(forward_y))] = {
            "rear_y_mm": REAR_Y_MM,
            "forward_y_mm": forward_y,
            "rows": _row_wood_and_rim(shifted, assembly["wood"]),
            "intended_bore_wood_coverage": coverage,
            "cut_hosts": members,
            "nearest_fixed_screw_to_removed_wood": nearest,
            "same_side_counterbore_clear_gaps_mm": _same_side_row_gaps(shifted),
            "protected_fixed_solid_hits_mm3": _protected_hits(shifted, fixed),
            "other_viewer_hardware_and_path_hits_mm3": _neighbor_hits(
                shifted, other_physical, other_paths
            ),
            "disposition": "REVISE",
            "clearance_approved": False,
        }
    return {
        "schema": SCHEMA,
        "baseline": KERF_RIGHT,
        "source_assembly": "export_owner_barrel_scene.build_viewer_assembly",
        "source_forward_y_mm": source_forward_y,
        "inventory": {
            "outer_header_rows": len(rows),
            "fixed_panel_screws": len(assembly["panel_connections"]),
            "retained_frame_bolts": len(assembly["frame_connections"]),
            "other_viewer_physical_solids": len(other_physical),
            "other_viewer_paths": len(other_paths),
        },
        "options": options,
        "rim_on_driver": "BLOCKED; rim removal only a conditional sequence, unverified",
        "release_flags": dict(assembly["release_flags"]),
        "layout_approved": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
        "limits": (
            "Nominal Boolean CAD only: displayed wood is uncut. Coverage and one-solid "
            "connectedness do not establish edge/end distance, wood net-section strength, "
            "bolt/barrel/thread capacity, hardware tolerance, or safe service. "
            "Twenty-millimeter straight driver is a trial envelope; installed rim blocks it."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
