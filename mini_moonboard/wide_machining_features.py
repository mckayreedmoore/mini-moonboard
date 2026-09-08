"""Part-local nonconnection cutter reservations for the current wide candidate.

Toolpath overshoot and occupied-volume reservations are not approved drill depths.
Historical face grids and fabrication schedules remain untouched.
"""
import math

import cadquery as cq

from . import base_frame as base
from . import box_frame as b
from . import panel_grid_v2 as grid
from . import product_frame as product
from . import timber_frame as timber
from . import wide_frame as frame
from .bolted_frame import WASHER


def overlaps(first, second):
    a, c = first.BoundingBox(), second.BoundingBox()
    return all(getattr(a, axis+"max") >= getattr(c, axis+"min") and
               getattr(c, axis+"max") >= getattr(a, axis+"min") for axis in "xyz")


def panel_name(x, s=None):
    if not math.isfinite(x) or not 0 <= x < 2*b.HALF:
        raise ValueError("Grid coordinate outside actual panels")
    side = "left" if x < b.HALF else "right"
    if s is None:
        return "kicker_"+side
    if not math.isfinite(s) or not 0 <= s < b.LENGTH:
        raise ValueError("Grid station outside actual main panels")
    return f"main_{'lower' if s < b.HALF else 'upper'}_{side}"


def lower_bearing_plane(shape):
    """Extract the actual lowest horizontal outward face, never a blank guess."""
    z = shape.BoundingBox().zmin
    faces = []
    for face in shape.Faces():
        box = face.BoundingBox()
        if abs(box.zmin-z) > 1e-5 or abs(box.zmax-z) > 1e-5:
            continue
        normal = face.normalAt().normalized()
        if (normal-cq.Vector(0, 0, -1)).Length > 1e-8:
            raise ValueError("Lowest bearing face has unexpected outward normal")
        if not math.isfinite(face.Area()) or face.Area() <= 0:
            raise ValueError("Invalid lower bearing face area")
        faces.append(face)
    if not faces:
        raise ValueError("No finite-area horizontal lower bearing face")
    area = sum(face.Area() for face in faces)
    centre = sum((face.Center()*face.Area() for face in faces), cq.Vector())/area
    return centre, cq.Vector(0, 0, -1), area, len(faces)


def features(parts=None, frames=None):
    """Return local feature rows using wide_machining's explicit datum frames.

    ``parts`` must be undrilled wide wood parts, not display insert solids.
    Housings are already present in undrilled CAD, so their removed material is
    checked against reconstructed un-housed principal stock instead.
    """
    from .wide_machining import datums, direction_to_local, to_local

    parts = frame.wood_parts(False) if parts is None else parts
    parts = parts if isinstance(parts, dict) else {p.name: p for p in parts}
    frames = datums(tuple(parts.values())) if frames is None else frames
    if set(frames) != set(parts):
        raise ValueError("Feature datum and part inventories differ")
    rows = []

    def add(name, feature, kind, origin, axis, cutter, dimensions, note, *, entry=None, target=None, transverse_axes=()):
        if name not in parts or name not in frames:
            raise ValueError("Unknown feature target part")
        material = parts[name].shape if target is None else target
        if not overlaps(material, cutter) or material.intersect(cutter).Volume() <= 1e-6:
            raise ValueError(f"Feature misses its declared target: {name}/{feature}")
        if any(not math.isfinite(v) or v <= 0 for v in dimensions.values()):
            raise ValueError("Invalid feature dimensions")
        point = to_local(origin, frames[name])
        entry_role = "physical_panel_face" if entry is not None else "cutter_reference_not_verified_surface"
        entry = origin if entry is None else entry
        local_entry = to_local(entry, frames[name])
        rows.append({"part": name, "feature": feature, "class": kind,
            "cutter_origin_local_mm": list(point), "cutter_origin_local_in": [v/25.4 for v in point],
            "entry_local_mm": list(local_entry), "entry_local_in": [v/25.4 for v in local_entry],
            "entry_role": entry_role,
            "axis_local": list(direction_to_local(axis, frames[name])),
            "transverse_axes_local": [list(direction_to_local(v, frames[name])) for v in transverse_axes],
            "dimensions_mm": dimensions, "dimensions_in": {k: v/25.4 for k, v in dimensions.items()},
            "status": note+"; development geometry, machining tolerance and resistance unqualified"})

    panel = product.FACE_THICKNESS_MM
    main_datums = (("tnut", grid.main_tnut_datums(), 11.1125), ("led", grid.main_led_datums(), 13.))
    for kind, datums_by_label, diameter in main_datums:
        for label, (x, s) in datums_by_label.items():
            name = panel_name(x, s)
            entry = b.point(x-b.HALF, s, -panel)
            origin = entry-b.normal()
            cutter = cq.Solid.makeCylinder(diameter/2, panel+2., origin, b.normal())
            add(name, f"{kind}_{label}", "through_hole", origin, b.normal(), cutter,
                {"diameter": diameter, "material_thickness": panel, "cutter_depth": panel+2.},
                "Physical face entry differs from cutter origin by 1 mm overshoot; through drilling, not a blind depth", entry=entry)
    for label, (x, z) in grid.kicker_foothold_datums().items():
        name = panel_name(x)
        axis = cq.Vector(0, 1, 0)
        entry = cq.Vector(x-b.HALF, product.KICKER_BACK_Y_MM, b.V1_KICKER_HEIGHT_MM+z)
        origin = entry-axis
        cutter = cq.Solid.makeCylinder(11.1125/2, panel+2., origin, axis)
        add(name, "tnut_kicker_"+str(label), "through_hole", origin, axis, cutter,
            {"diameter": 11.1125, "material_thickness": panel, "cutter_depth": panel+2.},
            "Inherited cutter enters rear of kicker; opposite front entry is possible but not a second feature; 1 mm cutter overshoot", entry=entry)
    service_targets = {name: p for name, p in parts.items()
                       if name.startswith(("base_side_", "base_principal_", "base_rail_", "timber_bottom_"))}
    expected_targets = {"base_side_left", "base_side_right", "base_principal_left", "base_principal_right",
        "base_rail_top", "timber_bottom_backing", *{f"base_rail_mid_{level}_{side}"
          for level in ("lower", "upper") for side in ("left", "right")}}
    if set(service_targets) != expected_targets:
        raise ValueError("Unknown or missing service-target member")
    labeled = [(kind, label, x, s) for kind, datums_by_label, _ in main_datums for label, (x, s) in datums_by_label.items()]
    for (kind, label, x, s), cutter in zip(labeled, timber.service_envelopes(), strict=True):
        for name, part in service_targets.items():
            if overlaps(part.shape, cutter) and part.shape.intersect(cutter).Volume() > 1e-6:
                add(name, f"service_{kind}_{label}", "service_reservation", b.point(x-b.HALF, s, 0.),
                    b.normal(), cutter, {"diameter": timber.SERVICE_DIAMETER, "cutter_depth": timber.SERVICE_DEPTH},
                    "Straight access reservation, not a qualified bore or wire/driver routing instruction")
    tangent = b.point(0, 1, 0)-b.point(0, 0, 0)
    for side, (x0, x1) in frame.UPRIGHTS.items():
        stock, _ = base._sloped_bearing_member(x0, x1, 139.7, b.LENGTH-38.1)
        cutter = b.block(x0, x1, 0., 88.9, 0., 38.1)
        add(f"base_principal_{side}", "lower_backing_housing", "housing", b.point(x0, 0., 0.),
            b.normal(), cutter, {"width_x": x1-x0, "length_s": 88.9, "depth_n": 38.1},
            "Rectangular front housing; stock has the modeled level lower bearing cut but is not yet housed; cutter corner is a datum, not necessarily an exposed edge",
            target=stock, transverse_axes=(cq.Vector(1, 0, 0), tangent))
    bolts = [c for c in frame.connections() if c.name.startswith("timber_backing_bolt_")]
    if len(bolts) != 2:
        raise ValueError("Expected two current backing recesses")
    for c in bolts:
        origin = c.start-b.normal()*10.
        cutter = cq.Solid.makeCylinder(28.575/2, 10.+WASHER, origin, b.normal())
        add("timber_bottom_backing", "counterbore_"+c.name, "counterbore", origin, b.normal(), cutter,
            {"diameter": 28.575, "depth": 10.+WASHER},
            "Front timber surface N=0, not bolt under-head origin N=10; socket access and ligament strength unresolved")
    panels = frame.panel_connections()
    if len(panels) != 56:
        raise ValueError("Expected 56 panel-head envelopes")
    for c in panels:
        head = frame.SCREW["head_diameter_max"]
        angle = frame.SCREW["head_angle_min_deg"]
        depth = (head-c.diameter)/2/math.tan(math.radians(angle/2))
        add(c.members[0], "head_envelope_"+c.name, "countersink_envelope", c.start, c.direction,
            c.components()[1], {"major_diameter": head, "minor_diameter": c.diameter, "cutter_depth": depth},
            "80-degree maximum-head CAD clearance envelope, not an 82-degree workshop countersink-depth instruction; seating depth remains unresolved")
        rows[-1]["included_angle_deg"] = angle
    bearing_names = {f"base_{member}_{side}" for member in ("side", "principal") for side in ("left", "right")}
    leg_names = {f"leg_{side}_{layer}" for side in ("left", "right") for layer in ("inner", "outer")}
    if not bearing_names | leg_names <= parts.keys():
        raise ValueError("Missing one of eight prescribed bearing-plane parts")
    for name in sorted(bearing_names | leg_names):
        origin, normal, area, count = lower_bearing_plane(parts[name].shape)
        expected_z = base.HEADER_TOP if name in bearing_names else 0.
        if abs(origin.z-expected_z) > 1e-5:
            raise ValueError("Actual lower plane is not at its prescribed bearing elevation")
        local = to_local(origin, frames[name])
        rows.append({"part": name, "feature": "lower_bearing_plane",
            "class": "header_bearing_plane" if name in bearing_names else "floor_bearing_plane",
            "plane_point_world_mm": list(origin.toTuple()),
            "plane_point_world_in": [v/25.4 for v in origin.toTuple()],
            "plane_point_local_mm": list(local), "plane_point_local_in": [v/25.4 for v in local],
            "plane_normal_world": list(normal.toTuple()),
            "plane_normal_local": list(direction_to_local(normal, frames[name])),
            "actual_face_area_mm2": area, "actual_face_area_in2": area/25.4**2,
            "coplanar_face_count": count,
            "status": "Actual lowest horizontal outward CAD face; point is area-weighted face centroid, not a timber corner. "
            "Plane marker only, not a cutter or saw setup. Bearing capacity and machining tolerances unqualified."})
    identities = [(r["part"], r["feature"]) for r in rows]
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate feature identity")
    return rows
