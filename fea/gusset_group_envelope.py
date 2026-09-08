"""Two distinct gusset interfaces; conditional in-plane equal-stiffness statics."""
import math

from fea.two_member_yield import build as reference_values
from mini_moonboard import wide_frame as frame


def pair_forces(points, force, moment):
    """In-plane forces at two equal-stiffness bolts, moment about pair centroid.

    Coordinates/forces are world (Y,Z), moment is world X in Nmm.
    No fit/slip/contact/group-adjustment or material resistance is established.
    """
    if (len(points) != 2 or any(len(p) != 2 for p in points) or len(force) != 2
            or not all(math.isfinite(v) for p in points for v in p)
            or not all(math.isfinite(v) for v in (*force, moment))):
        raise ValueError("Require finite planar two-point group and wrench")
    center = [sum(p[i] for p in points)/2 for i in range(2)]
    offsets = [[p[i]-center[i] for i in range(2)] for p in points]
    polar = sum(y*y+z*z for y, z in offsets)
    if polar <= 0:
        raise ValueError("Distinct bolt positions required")
    return [[force[0]/2-moment*z/polar, force[1]/2+moment*y/polar]
            for y, z in offsets]


def build():
    references = {r["connection"]: r["reference_lateral_n"] for r in reference_values()}
    bolts = {c.name: c for c in frame.connections() if c.name.startswith("timber_base_")}
    rows = []
    for side in ("left", "right"):
        upper = [bolts[f"timber_base_{side}_{i}"] for i in (1, 2)]
        lower = [bolts[f"timber_base_{side}_{i}"] for i in (3, 4)]
        for group, member in ((upper, f"base_side_{side}"), (lower, f"base_post_outer_{side}")):
            if any(c.members != (member, f"timber_base_gusset_{side}") for c in group):
                raise ValueError("Unexpected gusset load-path ownership")
        up = [(c.start.y, c.start.z) for c in upper]
        low = [(c.start.y, c.start.z) for c in lower]
        delta = [sum(p[i] for p in up)/2-sum(p[i] for p in low)/2 for i in range(2)]
        for label, force, moment in (("unit_FY", (1., 0.), 0.),
                                     ("unit_FZ", (0., 1.), 0.),
                                     ("unit_MX_Nmm", (0., 0.), 1.)):
            lower_moment = -moment-delta[0]*force[1]+delta[1]*force[0]
            forces = pair_forces(up, force, moment)+pair_forces(low, [-v for v in force], lower_moment)
            limits = [references[c.name]/math.hypot(*f) for c, f in zip(upper+lower, forces, strict=True)
                      if math.hypot(*f) > 0]
            rows.append({"side": side, "basis": label, "upper_yz_mm": up, "lower_yz_mm": low,
                         "upper_to_lower_centroid_delta_yz_mm": delta,
                         "bolt_names": [c.name for c in upper+lower], "bolt_forces_per_unit": forces,
                         "conditional_basis_scale": min(limits)})
    return rows
