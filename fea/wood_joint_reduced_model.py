"""Assemble current physical contact and fastener paths on checked geometry.

No capacity is assigned here. A positive Hillman axial ratio is an explicit
non-qualifying sensitivity parameter, not a measured screw property. The caller
still must apply every source load and validate native response and sensitivity.
"""
from __future__ import annotations

import numpy as np

from fea.wood_joint_reduced_connections import (
    axial_outer_seats,
    compression_contact,
    lateral_plane,
)
from fea.wood_joint_reduced_geometry import (
    GEOMETRY_TOL_MM,
    _member_source_bore_at,
    _surface_distance,
    attach_body,
)


def _attach_axis_point(structure, panels, body, point):
    point = np.asarray(point, dtype=float)
    if body in panels.panels:
        _, _, _, holes, _, _ = panels._element_and_face(body, point)
        return attach_body(structure, panels, body, point, allow_source_bore=bool(holes))
    shape = panels._reduced_source_shapes[body]
    bore = _member_source_bore_at(shape, point)
    # An axis may be exactly on a finished cylinder rim. The attachment wrapper
    # distinguishes an actual cavity from its wood boundary before accepting it.
    if shape.isInside(point.tolist(), 1e-6) or _surface_distance(shape, point) <= GEOMETRY_TOL_MM:
        bore = None
    return attach_body(structure, panels, body, point, allow_source_bore=bore is not None)


def _retained_interface(row, source, contacts):
    origin = np.asarray(source["source_point_xyz_mm"], dtype=float)
    axis = np.asarray(source["axis_xyz"], dtype=float)
    axis /= np.linalg.norm(axis)
    candidates = []
    for patch in contacts["contact_patches"]:
        if set(patch["member_ids"]) != {row["first"], row["second"]}:
            continue
        normal = np.asarray(patch["normal_on_first_xyz"])
        denominator = float(normal @ axis)
        if abs(denominator) < 1e-8:
            continue
        point = origin + axis * float(normal @ (np.asarray(patch["centroid_xyz_mm"])-origin))/denominator
        if not any(np.linalg.norm(point-other) < 1e-5 for other in candidates):
            candidates.append(point)
    if len(candidates) != 1:
        raise ValueError(f"{row['axis_id']}: expected one actual retained wood-interface plane, found {len(candidates)}")
    return candidates[0]


def add_connections(structure, panels, geometry_metadata, properties, model_inputs,
                    contact_geometry, *, hillman_axial_ratio, bolt_gap_factor=1.,
                    contact_penalty_n_per_mm3=100.):
    """Add all current interfaces without converting them to rigid connections."""
    if hillman_axial_ratio is not None and (not np.isfinite(hillman_axial_ratio) or hillman_axial_ratio <= 0):
        raise ValueError("Hillman diagnostic ratio must be positive, or None for the known omission case")
    if not np.isfinite(bolt_gap_factor) or bolt_gap_factor < 0:
        raise ValueError("Finite nonnegative bolt-gap multiplier required")
    if not np.isfinite(contact_penalty_n_per_mm3) or contact_penalty_n_per_mm3 <= 0:
        raise ValueError("Positive numerical contact penalty required")
    audit = geometry_metadata["attachment_audit"]
    if not audit["all_passed"]:
        raise ValueError("Geometry attachment audit has unresolved failures")
    if structure.springs or structure.fixed:
        raise ValueError("Connections/supports were already installed")
    sources = {row["axis_id"]: row for row in model_inputs["connections"]}
    owners, floor_groups, attachment_rows = {}, {}, []
    for cell in audit["sample_geometry_records"]:
        name = cell["name"]
        owner = {"first": cell["first"], "second": cell["second"],
                 "source_area_mm2": cell["area_mm2"], "role": cell["kind"]}
        is_floor = cell["second"] == "floor"
        if is_floor:
            first = audit["floor_attachment_nodes"][name]
            second = structure.node(cell["point_xyz_mm"])
            structure.fixed.add(second)
        else:
            first, second = (audit["contact_attachment_nodes"][name][which] for which in ("first", "second"))
        stiffness = contact_penalty_n_per_mm3 * cell["area_mm2"]
        compression_contact(structure, first, second, name=name, inward=cell["normal_xyz"],
                            stiffness_n_per_mm=stiffness, owner=owner)
        owners[name] = owner
        if is_floor:
            tangential = name + "_friction"
            tangent_owner = {"first": cell["first"], "second": "floor", "role": "assumed_no_slip_floor"}
            before = len(structure.springs)
            lateral_plane(structure, first, second, name=tangential, axis=cell["normal_xyz"],
                          stiffness_n_per_mm=stiffness, owner=tangent_owner)
            for spring in structure.springs[before:]:
                spring["bearing_closed_assumption"] = True
            owners[tangential] = tangent_owner
            floor_groups[name] = tangential
    lateral_count = axial_count = screw_axial_count = 0
    for row in properties["lateral_planes"]:
        source = sources[row["axis_id"]]
        kind = source["kind"]
        if kind == "candidate_bolt":
            point = np.asarray(row["point_xyz_mm"])
            axis = row["axis_head_to_nut_xyz"]
            first_body, second_body = row["first"], row["second"]
        elif kind == "retained_bolt":
            point = _retained_interface(row, source, contact_geometry)
            axis = source["axis_xyz"]
            first_body, second_body = row["first"], row["second"]
        elif kind == "panel_screw":
            first_body = source["source_record"]["panel_member"]
            second_body = source["source_record"]["receiver_member"]
            source_axis = np.asarray(source["axis_xyz"], dtype=float)
            source_axis /= np.linalg.norm(source_axis)
            thickness = panels.panels[first_body].geometry["thickness_mm"]
            head_point = np.asarray(source["source_point_xyz_mm"])
            normal = np.asarray(panels.panels[first_body].geometry["normal_xyz"])
            _, _, depth = panels.local_point(first_body, head_point)
            if abs(abs(depth)-thickness/2.) > 1e-5 or abs(source_axis @ normal) < 1.-1e-8:
                raise ValueError("Panel screw source head is not a normal broad-face axis")
            axis = np.sign(depth)*normal
            point = head_point-axis*thickness
        else:
            raise ValueError("Unexpected source connection kind")
        first = _attach_axis_point(structure, panels, first_body, point)
        second = _attach_axis_point(structure, panels, second_body, point)
        owner = {"first": first_body, "second": second_body, "axis_id": row["axis_id"],
                 "role": kind + "_lateral_plane"}
        name = row["spring_group_name"]
        lateral_k = row["lateral_stiffness_n_per_mm_per_fastener_per_shear_plane"]
        gap = (row["radial_clearance_mm"] or 0.)*bolt_gap_factor
        lateral_plane(structure, first, second, name=name, axis=axis,
                      stiffness_n_per_mm=lateral_k, owner=owner, radial_gap_mm=gap)
        owners[name] = owner
        lateral_count += 1
        attachment_rows.append({"axis_id": row["axis_id"], "kind": kind, "first": first_body,
            "second": second_body, "point_xyz_mm": point.tolist(), "lateral_spring_name": name})
        if kind == "panel_screw" and hillman_axial_ratio is not None:
            # axis points out of the panel: wood first and panel second makes
            # positive scalar extension mean separation and screw tension.
            axial_name = row["axis_id"] + "/parametric-withdrawal"
            axial_owner = {"first": second_body, "second": first_body, "axis_id": row["axis_id"],
                           "role": "non_qualifying_parametric_screw_withdrawal"}
            compression_contact(structure, second, first, name=axial_name, inward=axis,
                                stiffness_n_per_mm=hillman_axial_ratio*lateral_k, owner=axial_owner)
            structure.springs[-1]["tension_only_assumption"] = True
            owners[axial_name] = axial_owner
            screw_axial_count += 1
    for row in properties["bolt_outer_seat_axial_ties"]:
        first_point, second_point = row["outer_seat_points_xyz_mm"]
        first = _attach_axis_point(structure, panels, row["first"], first_point)
        second = _attach_axis_point(structure, panels, row["second"], second_point)
        owner = {"first": row["first"], "second": row["second"], "axis_id": row["axis_id"],
                 "role": "physical_bolt_outer_seat_tension"}
        name = row["spring_name"]
        axial_outer_seats(structure, first, second, name=name, axis=row["axis_head_to_nut_xyz"],
                          stiffness_n_per_mm=row["stiffness_n_per_mm"], owner=owner)
        owners[name] = owner
        axial_count += 1
    if lateral_count != 174 or axial_count != 104 or screw_axial_count != (66 if hillman_axial_ratio is not None else 0):
        raise ValueError("Current physical connector coverage changed")
    return {"connection_ownership": owners, "floor_tangential_groups": floor_groups,
        "connection_attachment_rows": attachment_rows,
        "counts": {"lateral_planes": lateral_count, "physical_bolt_outer_seat_ties": axial_count,
                   "parametric_screw_axial_ties": screw_axial_count, "floor_cells": len(floor_groups)},
        "scenario": {"hillman_axial_to_lateral_ratio": hillman_axial_ratio,
                     "hillman_physical_stiffness_bounds_established": False,
                     "bolt_gap_factor": bolt_gap_factor,
                     "contact_penalty_n_per_mm3": contact_penalty_n_per_mm3,
                     "floor": "unverified no-slip assumption only while each floor cell bears"},
        "mechanical_acceptance": False, "native_solve_executed": False}


def normalize_active_groups(structure, active_bearings):
    """Pair each assumed floor no-slip group with its normal contact branch.

    Use this same returned set for both deck generation and record_structure.
    Unilateral behavior still requires solved displacement/sign complementarity;
    metadata alone does not turn a linear SPRING2 into a one-sided material law.
    """
    names = {row["name"] for row in structure.springs}
    active = set(active_bearings)
    if active-names:
        raise ValueError("Active set contains unknown spring groups")
    for name in names:
        if name.startswith("floor_") and name.endswith("_friction"):
            normal = name.removesuffix("_friction")
            if normal not in names:
                raise ValueError("Floor tangential group lacks its normal group")
            if normal in active:
                active.add(name)
            else:
                active.discard(name)
    return active


def oriented_deck(structure, material_binding, *, active_bearings=None):
    """Replace only material orientation coordinates, retaining geometric axes."""
    if active_bearings is not None and set(active_bearings) != normalize_active_groups(structure, active_bearings):
        raise ValueError("Normalize floor active groups before producing both deck and model record")
    text = structure.deck(active_bearings=active_bearings)
    orientations = material_binding["orientation_overrides"]
    for name, row in orientations.items():
        marker = f"*ORIENTATION,NAME=ORI_{name}\n"
        if text.count(marker) != 1:
            raise ValueError("Missing or duplicate material orientation for " + name)
        before, after = text.split(marker, 1)
        _, remainder = after.split("\n", 1)
        text = before + marker + row["deck_orientation_line"] + "\n" + remainder
    return text
