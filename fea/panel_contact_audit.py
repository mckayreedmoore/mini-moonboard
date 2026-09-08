"""Independent two-body contact-wrench control; not frame or material approval."""
import math
import re

from fea.floor_contact_results import blocks, cross


def time_rows(text, label):
    pattern = rf"^\s*{re.escape(label)}[^\n]*time\s+([0-9.Ee+\-]+)\n\s*\n((?:[ \t]*[+\-0-9][^\n]*\n)+)"
    result = {}
    for match in re.finditer(pattern, text, re.MULTILINE):
        time = float(match[1])
        rows = [[float(v) for v in line.split()] for line in match[2].splitlines()]
        if time in result or not rows or not all(math.isfinite(v) for row in rows for v in row):
            raise ValueError("Duplicate or invalid contact rows")
        result[time] = rows
    return result


def wrench(positions, forces):
    force = [math.fsum(f[i] for f in forces.values()) for i in range(3)]
    moments = [cross(positions[n], f) for n, f in forces.items()]
    return force+[math.fsum(m[i] for m in moments) for i in range(3)]


def audit_history(status, rows, maximum_increment):
    records = [line.split() for line in status.splitlines() if line.split() and line.split()[0].isdigit()]
    if len(records) != len(rows) or not rows:
        raise ValueError("Status and output endpoint counts differ")
    previous = 0.
    for index, (record, row) in enumerate(zip(records, rows, strict=True), 1):
        if len(record) != 7 or int(record[0]) != 1 or int(record[1]) != index:
            raise ValueError("Unexpected step or increment sequence")
        time, step_time, increment = map(float, record[4:])
        if (not all(map(math.isfinite, (time, step_time, increment)))
                or not 0 < increment <= maximum_increment+1e-6
                or abs(time-row["time"]) > 1e-6 or abs(time-step_time) > 1e-6
                or abs(time-previous-increment) > 1e-6):
            raise ValueError("Status history or increment limit differs")
        previous = time
    if abs(previous-1.) > 1e-9:
        raise ValueError("Incomplete coupon step")


def audit(text, context):
    nodes = {int(n): tuple(p) for n, p in context["nodes"].items()}
    upper, lower, top, support = (set(context[k]) for k in ("upper", "lower", "top", "support"))
    if (upper & lower or upper | lower != nodes.keys() or not top <= upper
            or not support <= lower or not all((upper, lower, top, support))):
        raise ValueError("Invalid body/support ownership")
    prescribed = {int(n): z for n, z in context["prescribed_top_z_mm"].items()}
    slave_faces = {tuple(v) for v in context["surfaces"]["SLAVE"]}
    if (prescribed.keys() != top or not all(math.isfinite(v) and v < 0 for v in prescribed.values())
            or not math.isfinite(context["penalty"]) or context["penalty"] <= 0):
        raise ValueError("Invalid contact or actuator context")
    parsed = blocks(text)
    times = sorted({t for _, _, t in parsed})
    expected = {(kind, name, t) for t in times for kind, name in
                (("displacements", "UPPER"), ("displacements", "LOWER"),
                 ("forces", "TOP"), ("forces", "SUPPORT"))}
    if not times or times[-1] != 1. or times[0] <= 0 or set(parsed) != expected:
        raise ValueError("Incomplete nodal endpoints")
    gaps = time_rows(text, "relative contact displacement")
    pressures = time_rows(text, "contact stress")
    counts = time_rows(text, "total number of contact elements")
    contact = {}
    pattern = (r"statistics for slave set SLAVE, master set MASTER and time\s+([0-9.Ee+\-]+)"
               r"\s+total surface force[^\n]*\n\s*\n([^\n]+)")
    for match in re.finditer(pattern, text):
        t, values = float(match[1]), [float(v) for v in match[2].split()]
        if t in contact or len(values) != 6 or not all(map(math.isfinite, values)):
            raise ValueError("Invalid or duplicate pair wrench")
        contact[t] = values
    if any(set(values) != set(times) for values in (gaps, pressures, counts, contact)):
        raise ValueError("Incomplete contact endpoints")
    if len(re.findall("statistics for slave set", text)) != len(times):
        raise ValueError("Unexpected contact pair output")
    result = []
    for t in times:
        u = parsed["displacements", "UPPER", t]
        v = parsed["displacements", "LOWER", t]
        a = parsed["forces", "TOP", t]
        b = parsed["forces", "SUPPORT", t]
        if u.keys() != upper or v.keys() != lower or a.keys() != top or b.keys() != support:
            raise ValueError("Incomplete body or reaction output")
        if any(abs(u[n][0]) > 1e-9 or abs(u[n][1]) > 1e-9 or
               abs(u[n][2]-t*prescribed[n]) > 1e-9 for n in top):
            raise ValueError("Actuator history differs")
        if any(abs(x) > 1e-9 for n in support for x in v[n]):
            raise ValueError("Support moved")
        positions = {n: [nodes[n][i]+displacement[i] for i in range(3)]
                     for n, displacement in {**u, **v}.items()}
        if not all(math.isfinite(x) for p in positions.values() for x in p):
            raise ValueError("Nonfinite deformed position")
        wa, wb, wc = wrench(positions, a), wrench(positions, b), contact[t]
        residuals = {"global": [x+y for x, y in zip(wa, wb, strict=True)],
                     "upper": [x+y for x, y in zip(wa, wc, strict=True)],
                     "lower": [x-y for x, y in zip(wb, wc, strict=True)]}
        for values in residuals.values():
            if max(map(abs, values[:3])) > .1 or max(map(abs, values[3:])) > 1.:
                raise ValueError(f"Contact/free-body wrench mismatch: {residuals}")
        if counts[t] != [[float(len(gaps[t]))]] or len(gaps[t]) != len(pressures[t]):
            raise ValueError("Contact integration count differs")
        covered = set()
        for d, p in zip(gaps[t], pressures[t], strict=True):
            if len(d) != 5 or len(p) != 5 or d[:2] != p[:2]:
                raise ValueError("Contact integration rows differ")
            if tuple(d[:2]) not in slave_faces:
                raise ValueError("Contact output belongs to an undeclared face")
            covered.add(tuple(d[:2]))
            if p[2] < -1e-8 or max(map(abs, p[3:])) > 1e-8:
                raise ValueError("Tensile or frictional contact")
            if abs(p[2]-max(0., -context["penalty"]*d[2])) > 1e-6*(1+abs(p[2])):
                raise ValueError("Normal penalty law differs")
        if not gaps[t] or max(p[2] for p in pressures[t]) <= 0:
            raise ValueError("No compressive contact")
        if covered != slave_faces:
            raise ValueError("Control contact face coverage is incomplete")
        offset = cross((50., 50., 0.), wc[:3])
        eccentric = [wc[i+3]-offset[i] for i in range(3)]
        if max(map(abs, eccentric)) <= 1.:
            raise ValueError("Control does not exercise eccentric moment transfer")
        result.append({"time": t, "top_wrench_n_nmm": wa, "support_wrench_n_nmm": wb,
            "contact_on_upper_wrench_n_nmm": wc, "residual_wrenches_n_nmm": residuals,
            "contact_moment_about_face_center_nmm": eccentric,
            "contact_point_count": len(gaps[t]), "maximum_pressure_mpa": max(p[2] for p in pressures[t]),
            "maximum_penetration_mm": max(-d[2] for d in gaps[t])})
    return result
