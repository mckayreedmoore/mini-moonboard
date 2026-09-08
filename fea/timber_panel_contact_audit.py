"""Nonlinear panel-contact diagnostic audit; no isolated bolt/rim force proof."""
import math
import re

from fea.floor_contact_results import blocks, cross
from fea.panel_contact_audit import audit_history, time_rows, wrench
from fea.timber_release import gap_summary

LIMITS = ("Fixed-floor, ideally bonded rim/common-edge diagnostic. Per-leg action "
          "is inferred from floor reaction plus panel-on-leg contact, not independently "
          "validated against unavailable rim reactions; not bolt forces or joint capacity.")


def contact_rows(text, label, times):
    """Keep explicitly printed empty contact sections; reject missing sections."""
    headers = [float(t) for t in re.findall(
        rf"^\s*{re.escape(label)}[^\n]*time\s+([0-9.Ee+\-]+)", text, re.MULTILINE)]
    if len(headers) != len(times) or set(headers) != set(times):
        raise ValueError("Missing or duplicate contact section")
    rows = time_rows(text, label)
    return {t: rows.get(t, []) for t in times}


def at_reference(world, reference):
    offset = cross(reference, world[:3])
    return world[:3]+[world[i+3]-offset[i] for i in range(3)]


def audit(text, context):
    nodes = {int(n): p for n, p in context["nodes"].items()}
    feet, load = set(context["floor_nodes"]), context["load_node"]
    mapping = {s: {int(n): int(v) for n, v in values.items()}
               for s, values in context["node_map"].items()}
    pairs = {n for values in mapping.values() for old, new in values.items() for n in (old, new)}
    legs = {s: set(ids) for s, ids in context["leg_floor_nodes"].items()}
    force, penalty = context["force_n"], context["penalty"]
    references = context["leg_references_world_mm"]
    if (not feet or load in feet or not feet | pairs | {load} <= nodes.keys()
            or set(legs) != {"left", "right"} or set(mapping) != set(legs)
            or set(references) != set(legs) or set(context["contact_faces"]) != set(legs)
            or any(not m for m in mapping.values())
            or len(pairs) != 2*sum(len(m) for m in mapping.values())
            or pairs & (feet | {load})
            or any(len(p) != 3 or not all(map(math.isfinite, p))
                   for p in [*nodes.values(), *references.values()])
            or feet != {n for n, p in nodes.items() if abs(p[2]) < 1e-5}
            or any(not ids or not ids <= feet for ids in legs.values())
            or legs["left"] & legs["right"] or len(force) != 3
            or not all(map(math.isfinite, force)) or not math.isfinite(penalty) or penalty <= 0):
        raise ValueError("Invalid frame contact context")
    parsed = blocks(text)
    times = sorted({t for _, _, t in parsed})
    expected = {(kind, name, t) for t in times for kind, name in
                (("displacements", "TOP"), ("displacements", "FEET"),
                 ("displacements", "PAIRS"), ("forces", "FEET"))}
    if not times or times[0] <= 0 or times[-1] != 1. or set(parsed) != expected:
        raise ValueError("Incomplete nodal endpoints")
    gaps = contact_rows(text, "relative contact displacement", times)
    pressures = contact_rows(text, "contact stress", times)
    counts = contact_rows(text, "total number of contact elements", times)
    contact = {}
    pattern = (r"statistics for slave set (\w+), master set (\w+) and time\s+([0-9.Ee+\-]+)"
               r"\s+total surface force[^\n]*\n\s*\n([^\n]+)")
    for match in re.finditer(pattern, text):
        slave, master, time, raw = match.groups()
        key = (slave, master, float(time))
        values = [float(v) for v in raw.split()]
        if key in contact or len(values) != 6 or not all(map(math.isfinite, values)):
            raise ValueError("Invalid contact pair wrench")
        contact[key] = values
    if (set(contact) != {(f"SLAVE_{s.upper()}", f"MASTER_{s.upper()}", t)
                         for s in legs for t in times}
            or len(re.findall("statistics for slave set", text)) != len(contact)):
        raise ValueError("Incomplete or foreign contact pair endpoints")
    owners = {}
    for side, row in context["contact_faces"].items():
        if not row["pairs"]:
            raise ValueError("Missing declared contact faces")
        for pair in row["pairs"]:
            face = pair["leg"]
            key = (face["element"], int(face["face"][1:]))
            if key in owners:
                raise ValueError("Duplicate slave face ownership")
            owners[key] = side
    result = []
    for t in times:
        top, fixed, relative, reactions = (parsed[k, name, t] for k, name in
            (("displacements", "TOP"), ("displacements", "FEET"),
             ("displacements", "PAIRS"), ("forces", "FEET")))
        if top.keys() != {load} or fixed.keys() != feet or relative.keys() != pairs or reactions.keys() != feet:
            raise ValueError("Incomplete displacement/reaction inventory")
        if any(abs(v) > 1e-9 for xyz in fixed.values() for v in xyz):
            raise ValueError("Fixed floor moved")
        positions = {n: [nodes[n][i]+u[i] for i in range(3)]
                     for n, u in {**top, **fixed, **relative}.items()}
        floor = wrench(positions, reactions)
        applied = wrench(positions, {load: [t*f for f in force]})
        residual = [a+b for a, b in zip(floor, applied, strict=True)]
        if max(map(abs, residual[:3])) > .1 or max(map(abs, residual[3:])) > 1.:
            raise ValueError("Global deformed force/moment imbalance")
        if counts[t] != [[float(len(gaps[t]))]] or len(gaps[t]) != len(pressures[t]):
            raise ValueError("Contact integration count differs")
        local = {s: [] for s in legs}
        for d, p in zip(gaps[t], pressures[t], strict=True):
            if len(d) != 5 or len(p) != 5 or d[:2] != p[:2] or tuple(d[:2]) not in owners:
                raise ValueError("Contact row has foreign face ownership")
            if p[2] < -1e-8 or max(map(abs, p[3:])) > 1e-8:
                raise ValueError("Tensile or frictional contact")
            if abs(p[2]-max(0., -penalty*d[2])) > 1e-6*(1+abs(p[2])):
                raise ValueError("Normal penalty law differs")
            local[owners[tuple(d[:2])]].append((d[2], p[2]))
        per_leg = {}
        nodal_gaps = gap_summary(relative, mapping)
        for side, ids in legs.items():
            reference = context["leg_references_world_mm"][side]
            cf = contact[f"SLAVE_{side.upper()}", f"MASTER_{side.upper()}", t]
            rf = wrench(positions, {n: reactions[n] for n in ids})
            if not local[side] and max(map(abs, cf)) > 1e-8:
                raise ValueError("Contact wrench without reported integration points")
            if not local[side] and nodal_gaps[side]["interpenetrating_pair_count"]:
                raise ValueError("Inactive contact has unresolved signed-X nodal overlap")
            per_leg[side] = {"reference_world_mm": reference,
                "signed_x_nodal_gap_diagnostic": nodal_gaps[side],
                "nodal_gap_limit": "Original X-axis paired-node projection, not exact deformed surface distance or integration-point gap",
                "floor_on_leg_n_nmm": at_reference(rf, reference),
                "panel_on_leg_n_nmm": at_reference(cf, reference),
                "inferred_leg_on_rim_common_edge_n_nmm": at_reference([a+b for a, b in zip(rf, cf, strict=True)], reference),
                "reported_contact_point_count": len(local[side]),
                "maximum_pressure_mpa": max((p for _, p in local[side]), default=0.),
                "maximum_penetration_mm": max((max(0., -d) for d, _ in local[side]), default=0.)}
        result.append({"time": t, "applied_wrench_n_nmm": applied, "floor_wrench_n_nmm": floor,
                       "global_residual_n_nmm": residual, "loaded_displacement_mm": top[load],
                       "legs": per_leg, "limits": LIMITS})
    return result


def audit_with_history(text, context, status):
    rows = audit(text, context)
    audit_history(status, rows, context["increment"])
    return rows
