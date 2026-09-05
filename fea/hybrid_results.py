"""Additional equilibrium checks for the hybrid bulk comparison."""
import math
import re


def support_moments(data,nodes,feet,top,cases):
    if any(len(force)!=3 or not all(math.isfinite(v) for v in force) for _,force in cases):
        raise ValueError("Invalid case force")
    if not set(feet+top)<=set(nodes) or not all(math.isfinite(v) for t in feet+top for v in nodes[t]):
        raise ValueError("Missing/nonfinite support or load coordinates")
    blocks=re.findall(r"\n\s*forces[^\n]*\n(.*?)(?=\n\s*[A-Za-z]|\Z)",data,re.DOTALL|re.IGNORECASE)
    if len(blocks)!=len(cases):
        raise ValueError("Missing support reaction cases")
    moments=[]
    for block,(_,force) in zip(blocks,cases,strict=True):
        rows=[line.split() for line in block.splitlines() if line.strip()]
        rows=[r for r in rows if len(r)==4 and r[0].isdigit()]
        if len(rows)!=len(feet) or {int(r[0]) for r in rows}!=set(feet):
            raise ValueError("Incomplete support reactions")
        reactions={int(r[0]):[float(v) for v in r[1:]] for r in rows}
        if not all(math.isfinite(v) for xyz in reactions.values() for v in xyz):
            raise ValueError("Nonfinite support reaction")
        if any(abs(sum(v[i] for v in reactions.values())+1200*force[i])>.1 for i in range(3)):
            raise ValueError("Nodal reaction forces do not balance the load")
        applied=[1200*f/len(top) for f in force]
        moment=[sum(nodes[t][(i+1)%3]*v[(i+2)%3]-nodes[t][(i+2)%3]*v[(i+1)%3]
                    for t,v in reactions.items()) for i in range(3)]
        target=[sum(nodes[t][(i+1)%3]*applied[(i+2)%3]-nodes[t][(i+2)%3]*applied[(i+1)%3]
                    for t in top) for i in range(3)]
        if any(abs(a+r)>1 for a,r in zip(target,moment,strict=True)):
            raise ValueError(f"Hybrid moment equilibrium failed: {target} + {moment}")
        moments.append(moment)
    return moments


def deck_geometry(text,cases):
    """Read the frozen load/support sets and verify each actual CLOAD vector."""
    nodes,sets,loads,boundaries={},{},[],[]
    section=name=""
    for line in text.splitlines():
        if line.startswith("**") or not line.strip():
            continue
        if line.startswith("*"):
            section=line.upper().split(",")[0]
            if section=="*NSET":
                name=re.search(r"NSET=([^,\s]+)",line,re.IGNORECASE).group(1).upper()
                sets.setdefault(name,[])
            elif section=="*CLOAD":
                if "OP=NEW" not in line.upper():
                    raise ValueError("Load cases must replace previous loads")
                loads.append({})
            continue
        cells=[c.strip() for c in line.split(",") if c.strip()]
        if section=="*NODE":
            nodes[int(cells[0])]=tuple(float(v) for v in cells[1:4])
        elif section=="*NSET":
            sets[name].extend(int(v) for v in cells)
        elif section=="*CLOAD":
            key=(int(cells[0]),int(cells[1]))
            if key in loads[-1]:
                raise ValueError("Duplicate nodal load")
            loads[-1][key]=float(cells[2])
        elif section=="*BOUNDARY":
            boundaries.append(cells)
    top,feet=sets.get("TOP",[]),sets.get("FEET",[])
    if len(top)!=5 or len(set(top))!=5 or not feet or set(top)&set(feet):
        raise ValueError("Invalid load/support sets")
    if not set(top+feet)<=set(nodes):
        raise ValueError("Unknown load/support node")
    if not all(math.isfinite(v) for xyz in nodes.values() for v in xyz):
        raise ValueError("Nonfinite deck node")
    if len(loads)!=len(cases) or boundaries!=[["FEET","1","3","0"]]*len(cases):
        raise ValueError("Wrong load cases or supports")
    for actual,(_,force) in zip(loads,cases,strict=True):
        if len(force)!=3 or not all(math.isfinite(f) for f in force):
            raise ValueError("Invalid recorded force")
        expected={(tag,i):1200*f/len(top) for tag in top for i,f in enumerate(force,1) if f}
        if actual.keys()!=expected.keys() or any(not math.isfinite(actual[k]) or
                abs(actual[k]-expected[k])>1e-7 for k in expected):
            raise ValueError("Actual deck load differs from recorded case")
    return nodes,feet,top
