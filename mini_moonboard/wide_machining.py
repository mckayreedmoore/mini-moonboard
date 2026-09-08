"""Part-local axis schedules for wide development CAD, not released shop plans."""
import csv
import hashlib
import json
from pathlib import Path

import cadquery as cq

from . import box_frame as b
from . import product_frame as product
from . import wide_frame as frame
from .box_exports import exact_bounds
from .connection_geometry import material_intervals

OUTPUT = Path("docs/wide-machining")
LIMITS = ("Development geometry only, not build approval. Datums are oriented BRep "
          "envelope minima and may be virtual corners removed by slope/housing. "
          "Full-axis raw-stock intersections are layout witnesses, NOT drill depth, "
          "effective engagement, or completed-hole measurements.")


def family_axes(name):
    if name == "base_header" or name.startswith("base_post_"):
        return "world", ("X", "Y", "Z"), ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))
    if name.startswith(("leg_", "timber_base_gusset_")):
        return "side_profile", ("Y", "Z", "X"), ((0., 1., 0.), (0., 0., 1.), (1., 0., 0.))
    if name.startswith("kicker_"):
        return "kicker", ("X", "Z", "minus_Y"), ((1., 0., 0.), (0., 0., 1.), (0., -1., 0.))
    if name.startswith(("main_", "base_side_", "base_principal_", "base_rail_")) or name == "timber_bottom_backing":
        return "inclined", ("X", "S", "N"), ((1., 0., 0.),
            (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized().toTuple(), b.normal().toTuple())
    raise ValueError(f"No explicit machining datum family for {name}")


def direction_to_local(vector, datum):
    v = cq.Vector(vector)
    return tuple(v.dot(cq.Vector(axis)) for axis in datum["axes_world"])


def to_local(point, datum):
    return direction_to_local(cq.Vector(point)-cq.Vector(datum["origin_world_mm"]), datum)


def to_world(point, datum):
    result = cq.Vector(datum["origin_world_mm"])
    for value, axis in zip(point, datum["axes_world"], strict=True):
        result += cq.Vector(axis)*value
    return result.toTuple()


def datum(part):
    family, labels, axes = family_axes(part.name)
    plane = cq.Plane(origin=(0, 0, 0), xDir=axes[0], normal=axes[2])
    bounds = exact_bounds(plane.toLocalCoords(part.shape))
    low = (bounds.xmin, bounds.ymin, bounds.zmin)
    extents = (bounds.xlen, bounds.ylen, bounds.zlen)
    origin = plane.toWorldCoords(low).toTuple()
    return {"part": part.name, "family": family, "axis_labels": labels,
            "axes_world": axes, "origin_world_mm": origin, "extents_mm": extents,
            "extents_in": tuple(v/25.4 for v in extents),
            "datum_note": "Virtual oriented raw-BRep envelope minimum corner; verify actual edge/face witnesses before marking stock"}


def datums(parts=None):
    parts = frame.wood_parts(False) if parts is None else parts
    if isinstance(parts, dict):
        parts = parts.values()
    return {p.name: datum(p) for p in parts}


def operation(connection, member):
    if isinstance(connection, frame.PanelMachineScrew):
        if member == connection.members[0]:
            return "panel_clearance", frame.ASSUMPTIONS["panel_clearance_bore_diameter"], "Through panel; head countersink is a separate feature, not this axis interval"
        return "insert_installation_pilot", frame.INSERT["pilot_diameter_inch_recommendation"], (
            "Pilot diameter only; 17 mm CAD clearance reservation is NOT a selected drilling depth. "
            "Insert OD envelope is NOT pilot diameter; drill depth/stop and bit tip remain unresolved")
    if connection.kind == "bolt":
        return "bolt_clearance", product.BOLT_HOLE_DIAMETER_MM, "Through joint stack; backing counterbore is separate and starts at N=0, not bolt start N=10"
    if connection.name.startswith("clip_"):
        return "factory_clip_screw_axis", None, "Transfer through actual ML24Z factory holes; no invented SDS pilot diameter/depth"
    raise ValueError(f"Unclassified connection {connection.name}")


def connection_rows(raw=None, frames=None):
    raw = {p.name: p for p in frame.wood_parts(False)} if raw is None else raw
    if not isinstance(raw, dict):
        raw = {p.name: p for p in raw}
    frames = datums(raw) if frames is None else frames
    connections = frame.connections()
    if len(connections) != 188 or len({c.name for c in connections}) != 188:
        raise ValueError("Expected exact 188-connection wide inventory")
    rows = []
    for c in connections:
        direction = c.direction.normalized()
        for member in c.members:
            if member.startswith("clip_"):
                continue
            if member not in raw:
                raise ValueError(f"Unknown wood receiver {member}")
            intervals = material_intervals(raw[member].shape, c.start, direction, -5000., 5000.)
            if not intervals:
                raise ValueError(f"Axis misses raw receiver: {c.name}/{member}")
            label, diameter, note = operation(c, member)
            entries = [to_local(c.start+direction*a, frames[member]) for a, _ in intervals]
            exits = [to_local(c.start+direction*z, frames[member]) for _, z in intervals]
            rows.append({"connection": c.name, "part": member, "operation": label,
                "diameter_mm": diameter, "diameter_in": None if diameter is None else diameter/25.4,
                "axis_origin_local_mm": to_local(c.start, frames[member]),
                "axis_direction_local": direction_to_local(direction, frames[member]),
                "raw_entry_local_mm": entries, "raw_exit_local_mm": exits,
                "raw_entry_local_in": [[v/25.4 for v in p] for p in entries],
                "raw_exit_local_in": [[v/25.4 for v in p] for p in exits],
                "signed_raw_intervals_from_hardware_origin_mm": intervals,
                "machining_depth_mm": None, "note": note})
    return rows


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    from .wide_machining_features import features

    manifest = Path("exports/wide-principal-development/manifest.json")
    published = json.loads(manifest.read_text())
    sources = dict(published["sources"])
    if published["design"]["key"] != frame.KEY or not sources:
        raise ValueError("Wrong or unbound wide geometry")
    for path in (manifest, Path("mini_moonboard/wide_machining.py"),
                 Path("mini_moonboard/wide_machining_features.py"),
                 Path("mini_moonboard/connection_geometry.py"), Path("mini_moonboard/box_exports.py")):
        current = digest(path)
        if str(path) in sources and sources[str(path)] != current:
            raise ValueError("Conflicting machining source")
        sources[str(path)] = current
    if any(digest(p) != h for p, h in sources.items()):
        raise ValueError("Published wide sources changed")
    raw = {p.name: p for p in frame.wood_parts(False)}
    frames = datums(raw)
    rows = connection_rows(raw, frames)
    feature_rows = features(raw, frames)
    if any(digest(p) != h for p, h in sources.items()):
        raise ValueError("Machining sources changed during generation")
    return {"candidate": frame.KEY, "limits": LIMITS, "source_sha256": sources,
            "datums": frames, "connections": rows, "features": feature_rows,
            "connection_count": 188}


def write():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite machining schedule")
    result = build()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    for name, rows in (("datums", list(result["datums"].values())),
                       ("connections", result["connections"]), ("features", result["features"])):
        with (OUTPUT/(name+".csv")).open("x", newline="") as stream:
            fields = list(dict.fromkeys(key for row in rows for key in row))
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows({k: json.dumps(v) if isinstance(v, (tuple, list, dict)) else v
                             for k, v in row.items()} for row in rows)
    with (OUTPUT/"metadata.json").open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    write()
