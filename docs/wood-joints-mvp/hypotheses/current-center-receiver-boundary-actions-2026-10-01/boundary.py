"""Complete modeled center boundary accounting, without joint acceptance."""

from __future__ import annotations

import copy
import math
from collections import defaultdict

MEMBERS = (
    "base_header", "base_post_center_left", "base_post_center_right",
    "center_post_cleat_left", "center_post_cleat_right",
)
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def vector(values, *, nonnegative=False):
    require(isinstance(values, (list, tuple)) and len(values) == 3,
            "invalid three-vector")
    result = [float(x) for x in values]
    require(all(math.isfinite(x) and (not nonnegative or x >= 0) for x in result),
            "nonfinite vector or negative radius")
    return result


def close(actual, expected, message, tolerance=1e-8):
    actual, expected = vector(actual), vector(expected)
    require(max(abs(a-b) for a, b in zip(actual, expected, strict=True)) <= tolerance,
            message)


def add(a, b):
    require(len(a) == len(b), "vector dimensions differ")
    return [x+y for x, y in zip(a, b, strict=True)]


def cross(a, b):
    a, b = vector(a), vector(b)
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def wrench(point, force):
    return vector(force) + cross(point, force)


def moment_radius(arm, radius):
    arm, radius = vector(arm), vector(radius, nonnegative=True)
    return [abs(arm[1])*radius[2]+abs(arm[2])*radius[1],
            abs(arm[2])*radius[0]+abs(arm[0])*radius[2],
            abs(arm[0])*radius[1]+abs(arm[1])*radius[0]]


def inventory(model, members=MEMBERS):
    grouped = {}
    for index, raw in enumerate(model["raw_source_carrier_law_inventory_rows"]):
        owner = raw["physical_owner"]
        require(owner["first"] == raw["first_body"]
                and owner["second"] == raw["second_body"], "inventory owner/body differs")
        if owner["first"] not in members and owner["second"] not in members:
            continue
        row = grouped.setdefault(raw["name"], {
            "source_connection_name": raw["name"], "owner": owner, "source_indices": [],
        })
        require(row["owner"] == owner, "scalar group has differing owners")
        row["source_indices"].append(index)
    require(grouped, "empty modeled boundary")
    return [grouped[name] for name in sorted(grouped)]


def checked_scalar_refs(row, binding, raw_inventory):
    owner, expected = binding["owner"], binding["source_indices"]
    refs = row["source_inventory_rows"]
    floor = owner["role"] == "assumed_no_slip_floor"
    key = "source_row_original_index" if floor else "source_inventory_row_index"
    floor_inventory = [(i, raw) for i, raw in enumerate(raw_inventory)
                       if raw["role"] == "assumed_no_slip_floor"]
    indices = [floor_inventory[ref[key]][0] if floor else ref.get(key) for ref in refs]
    require(len(indices) == len(set(indices)) and sorted(indices) == sorted(expected),
            "missing, duplicate or changed scalar indices")
    for ref in refs:
        raw = floor_inventory[ref[key]][1] if floor else raw_inventory[ref[key]]
        require(ref["source_connection_name"] == raw["name"]
                == binding["source_connection_name"], "scalar source name differs")
        if floor:
            require(ref["local_dof"] == raw["dof"], "floor scalar DOF differs")
        else:
            require(ref["source_row_id"] == raw["group"]
                    and ref["intended_law"] == raw["intended_law"],
                    "scalar identity/law differs")
    if not floor:
        for key in ("role", "axis_id", "axis", "force_basis", "scalar_normal", "source_area_mm2"):
            if key in owner:
                require(row.get(key) == owner[key], "action source owner metadata differs")


def checked_state(method, model, saved, audit, bindings, members=MEMBERS):
    """Retain all endpoints and loads while reproducing frozen source balances."""
    require((method.BALANCE_FORCE_TOL_N, method.BALANCE_MOMENT_TOL_NMM) == (0.1, 2.0),
            "source balance gates changed")
    factor = saved["load_factor"]
    require(factor == audit["load_factor"], "response/audit state differs")
    datums = {body: [(a+b)/2 for a, b in zip(
        vector(model["body_geometry"][body]["geometry_record"]["start"]),
        vector(model["body_geometry"][body]["geometry_record"]["end"]), strict=True)]
        for body in members}
    # The frozen floor adapter adds basis provenance to a copy, never the file.
    recovered = method.response_interfaces(copy.deepcopy(saved), bindings)
    rows = {name: recovered[name] for name in sorted(recovered)}
    require(set(rows) == {r["source_connection_name"] for r in bindings},
            "incomplete or extra modeled interface coverage")
    endpoints, loads = [], []
    radii = {b: {"force": [0.]*3, "moment": [0.]*3} for b in members}
    internal, boundary = [0.]*6, [0.]*6
    ports = defaultdict(lambda: {"wrench_about_origin_N_Nmm": [0.]*6,
                                "connection_names": []})
    internal_count = 0
    for binding in bindings:
        name = binding["source_connection_name"]
        row = rows[name]
        # The adapter omits a floor role, and common-point interfaces may omit
        # explicit endpoint fields. Bind the role to the inventory and expose
        # both points; retain distinct outer-seat coordinates when supplied.
        row.setdefault("role", binding["owner"]["role"])
        row.setdefault("first_point", row["point"])
        row.setdefault("second_point", row["point"])
        method.validate_response_owner(row, binding, name)
        checked_scalar_refs(row, binding, model["raw_source_carrier_law_inventory_rows"])
        radius = vector(row["force_rounding_radius_xyz_n"], nonnegative=True)
        inside = row["first"] in members and row["second"] in members
        internal_count += int(inside)
        pair = [0.]*6
        for side in ("first", "second"):
            body = row[side]
            if body not in members:
                continue
            point = vector(row.get(side+"_point", row["point"]))
            force = vector(row["force_on_"+side+"_xyz_n"])
            arm = [p-d for p, d in zip(point, datums[body], strict=True)]
            action = wrench(point, force)
            mr = moment_radius(arm, radius)
            endpoints.append({"connection_name": name, "body": body, "side": side,
                              "point_xyz_mm": point, "force_xyz_N": force,
                              "force_radius_xyz_N": radius,
                              "moment_about_body_datum_xyz_Nmm": cross(arm, force),
                              "moment_radius_about_body_datum_xyz_Nmm": mr,
                              "internal_to_assembly": inside})
            radii[body]["force"] = add(radii[body]["force"], radius)
            radii[body]["moment"] = add(radii[body]["moment"], mr)
            pair = add(pair, action)
            other = row["second" if side == "first" else "first"]
            port = ports[(body, other, binding["owner"]["role"], inside)]
            port["wrench_about_origin_N_Nmm"] = add(port["wrench_about_origin_N_Nmm"], action)
            port["connection_names"].append(name)
        if inside:
            close(pair[:3], [0.]*3, "internal force cancellation failed")
            close(pair[3:], [0.]*3, "internal couple cancellation failed", 1e-6)
            internal = add(internal, pair)
        else:
            boundary = add(boundary, pair)
    for body in members:
        require(body in model["physical_body_loads"], "missing body-load map")
        for node, source_force in sorted(model["physical_body_loads"][body].items(),
                                         key=lambda item: int(item[0])):
            require(str(node) in model["nodes"], "missing physical body-load node")
            loads.append({"body": body, "node": str(node),
                          "point_xyz_mm": vector(model["nodes"][str(node)]),
                          "unscaled_force_xyz_N": vector(source_force),
                          "force_xyz_N": [factor*x for x in vector(source_force)],
                          "load_factor": factor,
                          "precision_basis": "saved model nodal load, not a printed RF token"})
    balances = method.member_balance(model, {"corner_body_names": list(members)},
                                     {"descriptor_midpoint_datums_mm": datums}, rows, factor)
    transported = [0.]*6
    for body, balance in balances.items():
        original = audit["body_equilibrium"][body]
        close(datums[body], original["reference_xyz_mm"], "source body datum differs")
        require(original["printed_resultants_passed"] is True
                and original["interval_resultants_passed"] is True
                and balance["raw_balance_passed"] and balance["rounding_interval_balance_passed"],
                "source physical body balance failed")
        for kind, suffix, tolerance in (("force", "xyz_n", 1e-8), ("moment", "xyz_nmm", 1e-6)):
            close(balance["combined_residual_wrench"][kind+"_"+suffix],
                  original[kind+"_residual_"+suffix], "saved all-body residual differs", tolerance)
            close(radii[body][kind], original[kind+"_rounding_radius_"+suffix],
                  "saved all-body precision bound differs", tolerance)
        balance["source_force_radius_xyz_N"] = radii[body]["force"]
        balance["source_moment_radius_xyz_Nmm"] = radii[body]["moment"]
        residual = balance["combined_residual_wrench"]
        transported = add(transported, add(
            residual["force_xyz_n"]+residual["moment_xyz_nmm"],
            [0.]*3+cross(datums[body], residual["force_xyz_n"])))
    load_wrench = [0.]*6
    for row in loads:
        load_wrench = add(load_wrench, wrench(row["point_xyz_mm"], row["force_xyz_N"]))
    combined = add(add(internal, boundary), load_wrench)
    close(combined[:3], transported[:3], "assembly force reconstruction differs")
    close(combined[3:], transported[3:], "assembly moment reconstruction differs", 1e-6)
    return {"load_factor": factor, "reporting_datums_xyz_mm": datums,
            "interface_actions": rows, "endpoint_actions": endpoints, "body_load_actions": loads,
            "member_balances": balances, "internal_interface_count": internal_count,
            "boundary_interface_count": len(rows)-internal_count,
            "internal_cancellation_wrench_N_Nmm": internal,
            "boundary_wrench_about_origin_N_Nmm": boundary,
            "body_load_wrench_about_origin_N_Nmm": load_wrench,
            "combined_residual_wrench_about_origin_N_Nmm": combined,
            "transported_source_residual_wrench_N_Nmm": transported,
            "ports": [{"body": key[0], "other_owner": key[1], "role": key[2],
                       "internal_to_assembly": key[3], **value}
                      for key, value in sorted(ports.items())]}


def geometry_ports(graph, bindings, frame_duties, members=MEMBERS):
    """Compare geometric duties with modeled ports without inventing missing forces."""
    modeled_contacts, modeled_axes, modeled_axis_pairs = defaultdict(list), defaultdict(list), defaultdict(set)
    for row in bindings:
        owner = row["owner"]
        pair = tuple(sorted((owner["first"], owner["second"])))
        if owner["role"] == "timber_or_panel_contact":
            modeled_contacts[pair].append(row["source_connection_name"])
        if "axis_id" in owner:
            modeled_axes[owner["axis_id"]].append(row["source_connection_name"])
            modeled_axis_pairs[owner["axis_id"]].add(pair)
    geometric_axis_pairs = defaultdict(set)
    pairs, missing = [], []
    for edge in graph["edges"]:
        pair = tuple(sorted(edge["member_ids"]))
        if not set(pair).intersection(members):
            continue
        contacts = sorted(modeled_contacts.get(pair, []))
        for association in edge["candidate_bolt_associations"]+edge["current_panel_screw_associations"]:
            geometric_axis_pairs[association["axis_id"]].add(pair)
        row = {"member_ids": list(pair), "geometry_state": edge["geometry_state"],
               "interface_geometry_state": edge["interface_geometry_state"],
               "broadphase_candidate": edge["broadphase_candidate"],
               "opposed_planar_face_contact_area_mm2": edge["opposed_planar_face_contact_area_mm2"],
               "minimum_separation_mm": edge["minimum_separation_mm"],
               "modeled_contact_names": contacts}
        pairs.append(row)
        if edge["opposed_planar_face_contact_area_mm2"] > 0 and not contacts:
            missing.append({**row, "status": "FINITE_GEOMETRIC_CONTACT_WITHOUT_MODELED_CONTACT_PORT"})
        elif edge["broadphase_candidate"] and edge["interface_geometry_state"] not in (
                "finite_planar_face_contact", "separated") and not contacts:
            missing.append({**row, "status": "UNRESOLVED_GEOMETRY_WITHOUT_MODELED_CONTACT_PORT"})
    routes = []
    for duty in frame_duties:
        portions = []
        for name in ("direct_post_header_seat", "post_to_cleat_attachment", "cleat_to_header_attachment"):
            detail = duty[name]
            pair = tuple(sorted(detail["member_pair"]))
            axes = detail["candidate_bolt_axes"]
            require(pair in {tuple(row["member_ids"]) for row in pairs}, "duty geometric pair missing")
            contacts = sorted(modeled_contacts.get(pair, []))
            require(len(contacts) == 4, "center duty four-sample contact coverage differs")
            for axis in axes:
                require(len(modeled_axes.get(axis, [])) == 2, "center duty bolt channels missing")
                axis_bindings = [b for b in bindings if b["owner"].get("axis_id") == axis]
                require(all(tuple(sorted((b["owner"]["first"], b["owner"]["second"]))) == pair
                            for b in axis_bindings), "center duty bolt receiver pair differs")
            portions.append({"duty": name, "member_ids": list(pair),
                             "modeled_contact_names": contacts,
                             "candidate_bolt_axes": axes,
                             "modeled_bolt_names": sorted(n for axis in axes for n in modeled_axes[axis]),
                             "force_split_calculated": False})
        routes.append({"panel_receiver_post": duty["panel_receiver_post"], "portions": portions})
    require(len(pairs) == len({tuple(row["member_ids"]) for row in pairs}),
            "duplicate geometric pairs")
    finite_pairs = {tuple(row["member_ids"]) for row in pairs
                    if row["opposed_planar_face_contact_area_mm2"] > 0}
    require(set(modeled_contacts) == finite_pairs, "modeled/geometric contact pair coverage differs")
    require(dict(modeled_axis_pairs) == dict(geometric_axis_pairs),
            "modeled/geometric fastener receiver pair coverage differs")
    return {"incident_pair_count": len(pairs), "incident_pairs": sorted(pairs, key=lambda r: r["member_ids"]),
            "unmodeled_geometric_ports": sorted(missing, key=lambda r: r["member_ids"]),
            "center_routes": routes,
            "limits": ["Finite geometry does not establish contact activity or resistance.",
                       "Unmodeled geometric ports carry no inferred force and are not automatically failed criteria.",
                       "Modeled coverage does not establish physical compatibility, stiffness or a qualified load path."]}
