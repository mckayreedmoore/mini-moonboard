"""Small, testable load distribution and output checks for bearing screens."""
import math
import re


def bolt_forces(stations, shear_s, shear_n, moment_nmm):
    if len(stations)<2 or len(set(stations))!=len(stations) or not all(math.isfinite(v) for v in (*stations,shear_s,shear_n,moment_nmm)):
        raise ValueError("Finite, distinct bolt stations and finite loads required")
    centre = sum(stations)/len(stations)
    polar = sum((s-centre)**2 for s in stations)
    return [(shear_s/len(stations), shear_n/len(stations)+moment_nmm*(s-centre)/polar) for s in stations]


def radial_loads(samples, force):
    """Compressive radial nodal forces with exactly the requested 2D resultant.

    Samples = (tag, surface-area weight, radial S, radial N). Solve a 2x2
    discrete cosine-pressure system; remove any tensile nodes and repeat.
    This prescribes bearing tractions; it does NOT solve bolt contact.
    """
    active = [p for p in samples if p[2]*force[0]+p[3]*force[1] > 1e-10]
    if math.hypot(*force) == 0:
        return {}
    while active:
        aa = sum(w*s*s for _, w, s, n in active)
        ab = sum(w*s*n for _, w, s, n in active)
        bb = sum(w*n*n for _, w, s, n in active)
        det = aa*bb-ab*ab
        if det <= 1e-15:
            raise ValueError("Insufficient bore surface for radial load")
        a, b = (bb*force[0]-ab*force[1])/det, (aa*force[1]-ab*force[0])/det
        positive = [p for p in active if a*p[2]+b*p[3] >= 0]
        if len(positive) == len(active):
            return {tag: (w*(a*s+b*n)*s, w*(a*s+b*n)*n) for tag, w, s, n in active}
        active = positive
    raise ValueError("No compressive bearing solution")


def parse_joint_results(data, applied, nodes=None, applied_moment=None, expected_elements=None):
    def block(title):
        match = re.search(title+r"[^\n]*\n(.*?)(?=\n\s*[A-Za-z]|\Z)", data, re.IGNORECASE|re.DOTALL)
        if not match:
            raise ValueError(f"Missing {title}")
        return [line.split() for line in match[1].splitlines() if line.strip()]
    u_rows = [r for r in block("displacements") if len(r)==4 and r[0].isdigit()]
    u = [[float(x) for x in r[1:]] for r in u_rows]
    stress_rows = [r for r in block("stresses") if len(r)==8 and r[0].isdigit()]
    stress = [[float(x) for x in r[2:]] for r in stress_rows]
    if expected_elements is not None:
        expected = {(element,point) for element in expected_elements for point in range(1,5)}
        if len(stress_rows)!=len(expected) or {(int(r[0]),int(r[1])) for r in stress_rows}!=expected:
            raise ValueError("Incomplete C3D10 integration-point stresses")
    reaction = [float(v) for v in block("total force")[0]]
    if not u or not stress or len(reaction)!=3 or not all(math.isfinite(v) for r in (*u, *stress, reaction) for v in (r if isinstance(r,list) else [r])):
        raise ValueError("Missing/nonfinite joint results")
    if len(applied)!=3 or not all(math.isfinite(v) for v in applied):
        raise ValueError("Invalid applied force")
    if any(abs(a+r)>.1 for a,r in zip(applied, reaction, strict=True)):
        raise ValueError("Joint force equilibrium failed")
    moment = None
    if nodes is not None:
        if len(u)!=len(nodes) or {int(r[0]) for r in u_rows}!=set(nodes):
            raise ValueError("Incomplete nodal displacement output")
        forces = {int(r[0]):[float(v) for v in r[1:]] for r in block("forces") if len(r)==4 and r[0].isdigit()}
        if not forces or applied_moment is None:
            raise ValueError("Missing nodal reactions or applied moment")
        moment = [sum(nodes[t][(i+1)%3]*v[(i+2)%3]-nodes[t][(i+2)%3]*v[(i+1)%3] for t,v in forces.items()) for i in range(3)]
        if any(not math.isfinite(r) or abs(a+r)>1 for a,r in zip(applied_moment,moment,strict=True)):
            raise ValueError("Joint moment equilibrium failed")
    # Isotropic equivalent stress is only a scalar comparison metric, NOT a
    # plywood failure criterion. Preserve individual component maxima too.
    vm = sorted(math.sqrt(((a-b)**2+(b-c)**2+(c-a)**2)/2+3*(d*d+e*e+f*f)) for a,b,c,d,e,f in stress)
    return {"max_displacement_mm": max(math.sqrt(sum(v*v for v in r)) for r in u),
                "peak_equivalent_stress_mpa": max(vm), "p95_equivalent_stress_mpa": vm[int(.95*(len(vm)-1))],
                "max_abs_stress_components_mpa": [max(abs(r[i]) for r in stress) for i in range(6)],
                "reaction_n": reaction, "reaction_moment_nmm": moment, "stress_points": len(stress)}
