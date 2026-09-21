"""Complete-step and deformed force/moment audit of unpinned contact trials."""
import hashlib
import math
import re


def blocks(data):
    pattern = r"(displacements|forces)[^\n]*for set (\w+) and time\s+([\d.Ee+\-]+)\n(.*?)(?=\n\s*[A-Za-z]|\Z)"
    result = {}
    for kind, name, time, body in re.findall(pattern, data, re.DOTALL | re.IGNORECASE):
        values = {}
        for line in body.splitlines():
            cells = line.split()
            if len(cells) == 4 and cells[0].isdigit():
                tag = int(cells[0])
                if tag in values:
                    raise ValueError("Duplicate node output")
                values[tag] = tuple(map(float,cells[1:]))
        if not all(math.isfinite(v) for xyz in values.values() for v in xyz):
            raise ValueError("Nonfinite nodal output")
        key = kind.lower(), name.upper(), float(time)
        if key in result:
            raise ValueError("Duplicate output set/time")
        result[key] = values
    return result


def cross(a, b):
    return [a[(i+1)%3]*b[(i+2)%3]-a[(i+2)%3]*b[(i+1)%3] for i in range(3)]


def verify_deck(text,nodes,elements,groups,record):
    if __package__:
        from .floor_contact import deck
    else:
        from floor_contact import deck
    if hashlib.sha256(text.encode()).hexdigest()!=record["deck_sha256"]:
        raise ValueError("Floor deck differs from frozen launch digest")
    expected, _ = deck(nodes,elements,groups,record["load_nodes"],record["mu"],record["normal_penalty_n_mm3"])
    if text != expected:
        raise ValueError("Floor deck differs from intended materials, loads, contact or constraints")


def audit(data, nodes, elements, groups, record):
    if __package__:
        from .floor_contact import FACES
    else:
        from floor_contact import FACES

    weights = {int(n):v for n,v in record["nodal_volume_mm3"].items()}
    if (weights.keys()!=nodes.keys() or not all(map(math.isfinite,weights.values()))
            or not math.isfinite(sum(weights.values())) or sum(weights.values())<=0):
        raise ValueError("Incomplete/nonfinite gravity context")
    coordinates = list(nodes.values())+[xyz for item in record["ground_nodes"].values() for xyz in item.values()]
    if any(len(xyz)!=3 or not all(map(math.isfinite,xyz)) for xyz in coordinates):
        raise ValueError("Nonfinite coordinate context")
    if not math.isfinite(record["mu"]) or not 0<record["mu"]<=1:
        raise ValueError("Invalid friction context")
    top = record["load_nodes"]
    if not top or len(set(top))!=len(top) or not set(top)<=set(nodes):
        raise ValueError("Invalid load-node context")
    parsed = blocks(data)
    output = []
    for time, load in ((1.,0.), (2.,1200.)):
        displacement = parsed.get(("displacements","WOODN",time),{})
        if displacement.keys() != nodes.keys():
            raise ValueError(f"Incomplete wood output at final step time {time}")
        positions = {n:[a+b for a,b in zip(xyz,displacement[n],strict=True)] for n,xyz in nodes.items()}
        force, moment, patches = [0.,0.,0.], [0.,0.,0.], {}
        for name, coordinates in record["ground_nodes"].items():
            coordinates = {int(n):xyz for n,xyz in coordinates.items()}
            reactions = parsed.get(("forces","GROUND_"+name,time),{})
            if reactions.keys() != coordinates.keys():
                raise ValueError(f"Incomplete ground reaction output {name} at time {time}")
            total = [sum(v[i] for v in reactions.values()) for i in range(3)]
            torque = [sum(cross(coordinates[n],v)[i] for n,v in reactions.items()) for i in range(3)]
            if total[2] < -.1:
                raise ValueError("Ground patch requires tensile normal force")
            if math.hypot(*total[:2]) > record["mu"]*max(0,total[2])+.1:
                raise ValueError("Ground patch exceeds necessary aggregate friction bound")
            feet = {elements[e][i] for e,face in groups[name] for i in FACES[face-1]}
            gaps = [positions[n][2] for n in feet]
            patches[name] = {"reaction_n":total, "reaction_moment_origin_nmm":torque,
                             "minimum_physical_gap_mm":min(gaps), "maximum_physical_gap_mm":max(gaps)}
            force = [a+b for a,b in zip(force,total,strict=True)]
            moment = [a+b for a,b in zip(moment,torque,strict=True)]
        for n, volume in record["nodal_volume_mm3"].items():
            applied = [0,0,-float(volume)*6e-10*9806.65]
            force = [a+b for a,b in zip(force,applied,strict=True)]
            moment = [a+b for a,b in zip(moment,cross(positions[int(n)],applied),strict=True)]
        for n in record["load_nodes"]:
            applied = [0,0,-load/len(record["load_nodes"])]
            force = [a+b for a,b in zip(force,applied,strict=True)]
            moment = [a+b for a,b in zip(moment,cross(positions[n],applied),strict=True)]
        if not all(map(math.isfinite,force+moment)) or max(map(abs,force)) > .1 or max(map(abs,moment)) > 1:
            raise ValueError(f"Deformed equilibrium failed at {time}: force {force}, moment {moment}")
        output.append({"time":time,"downward_climber_n":load,"force_residual_n":force,
                       "moment_residual_nmm":moment,"patches":patches,
                       "max_sampled_loaded_displacement_mm":max(math.hypot(*displacement[n]) for n in record["load_nodes"])})
    return output
