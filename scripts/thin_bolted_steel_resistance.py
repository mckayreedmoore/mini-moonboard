"""Conditional steel/hardware checks for the frozen thin bolted frame.

No fitting load rating, bolt preload, friction, equal paired-angle sharing or
unsolved own-end moment is credited. Nominal elastic comparisons and AISC
component equations are separate from exact-product and complete-joint gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from itertools import pairwise
from pathlib import Path

import numpy as np

from mini_moonboard.wood_joint_bolt_resistance import (
    bolt_first_yield_reference,
    wood_washer_annulus_reference_lbf,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
LAYOUT = PACKET / "mixed-offset-rows-shallow-wires-v4.json"
LAYOUT_SHA = "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c"
PSI_TO_MPA = 0.006894757293168361
INCH = 25.4
CATALOG = "https://www-dev.eaton.com/content/dam/eaton/products/support-systems/strut-systems-%26-accessories/strut-fittings-and-accessories/strut-fittings-catalog-section.pdf"
MIT_PLATE = "https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013/de27f1d8f647ff995771d4b8d48d34bc_MIT2_080JF13_Recitation5.pdf"
AISC_TEAROUT = "https://www.aisc.org/globalassets/aisc/research-library/denavit-et-al.-2021---final-report---tearout---2021-07-03.pdf"
AISC_BLOCK = "https://ej.aisc.org/index.php/engj/article/download/1117/1116"
AISC_CURRENT_BLOCK = "https://ej.aisc.org/index.php/engj/article/download/1342/1333/1371"
FITTINGS = {
    "B104ZN": {"beam_length_mm": 104.775, "post_length_mm": 88.9,
                "beam_holes_mm": [36.5125, 84.1375], "post_holes_mm": [20.6375, 68.2625]},
    "B103ZN": {"beam_length_mm": 104.775, "post_length_mm": 41.275,
                "beam_holes_mm": [36.5125, 84.1375], "post_holes_mm": [20.6375]},
}
WIDTH = 41.275
THICKNESS = 5.55625
HOLE = 14.2875
FY_CATALOG = 33000 * PSI_TO_MPA


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value: float, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite number")
    value = float(value)
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{name} must be {'positive ' if positive else ''}finite")
    return value


def vector(value, name: str) -> np.ndarray:
    value = np.asarray(value, dtype=float)
    if value.shape != (3,) or not np.isfinite(value).all():
        raise ValueError(f"{name} must be a finite 3-vector")
    return value


def section_reference(*, width_mm: float, thickness_mm: float,
                      removed_center_width_mm: float, force_local_n,
                      moment_local_nmm, fy_mpa: float | None) -> dict:
    """Same-section nominal elastic stress; x along leg, y across, z normal.

    The central removed chord leaves two symmetric side strips. The in-plane
    second moment therefore subtracts the missing strip's cube, rather than
    cubing the remaining total width. The sum of extrema and 1.5 V/A is an
    upper envelope of nominal normal/transverse stresses, not a hole-edge
    concentration or a curved-heel solution. Torsion remains a separate gap.
    """
    b = number(width_mm, "width", positive=True)
    t = number(thickness_mm, "thickness", positive=True)
    removed = number(removed_center_width_mm, "removed width")
    if not 0 <= removed < b:
        raise ValueError("removed width must lie in [0,width)")
    f, m = vector(force_local_n, "force"), vector(moment_local_nmm, "moment")
    area = (b - removed) * t
    z_out = (b - removed) * t**2 / 6
    z_in = t * (b**3 - removed**3) / (6 * b)
    sigma = abs(f[0]) / area + abs(m[1]) / z_out + abs(m[2]) / z_in
    tau = 1.5 * math.hypot(f[1], f[2]) / area
    equivalent = math.hypot(sigma, math.sqrt(3) * tau)
    if fy_mpa is not None:
        fy_mpa = number(fy_mpa, "yield strength", positive=True)
    return {"area_mm2": area, "out_of_plane_section_modulus_mm3": z_out,
            "in_plane_section_modulus_mm3": z_in, "nominal_normal_stress_envelope_mpa": sigma,
            "nominal_transverse_shear_envelope_mpa": tau,
            "nominal_von_mises_envelope_mpa": equivalent,
            "required_fy_mpa_at_nominal_first_yield": equivalent,
            "specified_fy_mpa": fy_mpa,
            "nominal_first_yield_index": equivalent / fy_mpa if fy_mpa else None,
            "torsion_nmm": float(m[0]), "torsion_method_complete": bool(abs(m[0]) < 1e-8),
            "local_hole_and_bend_stress_concentrations_included": False,
            "complete_joint_acceptance": False}


def bolt_section_reference(*, force_n, moment_nmm, diameter_mm: float,
                           fy_mpa: float | None, material_basis: str | None,
                           section_basis: str | None) -> dict:
    """Solid-circle same-section T/V/M elastic envelope with explicit area.

    x is the shaft direction. For a threaded section, diameter must identify
    the actual root and its basis. Nominal purchased diameter is insufficient.
    Reuse the repository's direct T/V material helper and add the circular
    bending/torsion envelope; all simultaneous actions belong to one section.
    """
    f, m = vector(force_n, "bolt force"), vector(moment_nmm, "bolt moment")
    d = number(diameter_mm, "loaded section diameter", positive=True)
    area = math.pi * d**2 / 4
    direct = bolt_first_yield_reference(
        axial_force_n=float(f[0]), lateral_shear_vector_n=(float(f[1]), float(f[2])),
        minimum_tensile_area_mm2=area, shear_plane_area_mm2=area,
        specified_min_yield_mpa=fy_mpa, property_scenario_id="caller_specified_same_section",
        material_basis=material_basis, tensile_area_basis=section_basis,
        shear_area_basis=section_basis, combined_action_area_mm2=area if section_basis else None,
        combined_action_section_basis=section_basis,
    )
    sigma = abs(f[0]) / area + 32 * math.hypot(m[1], m[2]) / (math.pi * d**3)
    tau = 4 * math.hypot(f[1], f[2]) / (3 * area) + 16 * abs(m[0]) / (math.pi * d**3)
    required = math.hypot(sigma, math.sqrt(3) * tau)
    return {"direct_reference": direct, "diameter_at_loaded_section_mm": d,
            "same_section_nominal_stress_envelope_mpa": required,
            "same_section_nominal_first_yield_index": required / fy_mpa
            if fy_mpa and material_basis and section_basis else None,
            "thread_notch_head_nut_pullthrough_and_stripping_checked": False,
            "complete_joint_acceptance": False}


def hole_clear_distance(*, length_mm: float, width_mm: float, hole_mm: float,
                        used_center_mm: float, other_centers_mm: list[float],
                        direction_xy) -> float:
    """First clear ligament on a ray toward an edge or another factory hole."""
    length = number(length_mm, "leg length", positive=True)
    width = number(width_mm, "width", positive=True)
    hole = number(hole_mm, "hole", positive=True)
    x = number(used_center_mm, "used hole center")
    direction = np.asarray(direction_xy, dtype=float)
    if direction.shape != (2,) or not np.isfinite(direction).all() or np.linalg.norm(direction) == 0:
        raise ValueError("bearing direction must be finite and nonzero")
    direction /= np.linalg.norm(direction)
    if not hole / 2 < x < length - hole / 2 or hole >= width:
        raise ValueError("used hole must be inside the rectangular plate")
    distances = []
    for axis, boundaries, station in ((0, (0., length), x), (1, (-width / 2, width / 2), 0.)):
        if abs(direction[axis]) > 1e-14:
            distances.extend((edge - station) / direction[axis] for edge in boundaries
                             if (edge - station) / direction[axis] > 0)
    for other in other_centers_mm:
        center = np.array([number(other, "other hole center") - x, 0.])
        projection = float(center @ direction)
        discriminant = (hole / 2)**2 - (float(center @ center) - projection**2)
        if discriminant >= 0 and projection - math.sqrt(discriminant) > 0:
            distances.append(projection - math.sqrt(discriminant))
    return max(0., min(distances) - hole / 2)


def bearing_tearout_reference(*, clear_distance_mm: float, bolt_diameter_mm: float,
                              thickness_mm: float, fu_mpa: float | None) -> dict:
    """AISC deformation-considered standard/oversize-hole component equations.

    Published 2021 AISC primary research reproduces nominal bearing 2.4dtFu
    and tearout 1.2Lc t Fu. No Fu is inferred from the catalog's minimum Fy.
    Applicability to the exact material, bend and all failure paths is a gate.
    """
    lc = number(clear_distance_mm, "clear distance")
    if lc < 0:
        raise ValueError("clear distance cannot be negative")
    d = number(bolt_diameter_mm, "bolt diameter", positive=True)
    t = number(thickness_mm, "thickness", positive=True)
    if fu_mpa is not None:
        fu_mpa = number(fu_mpa, "tensile strength", positive=True)
    coefficient = min(2.4 * d * t, 1.2 * lc * t)
    return {"bearing_coefficient_n_per_mpa_fu": 2.4 * d * t,
            "tearout_coefficient_n_per_mpa_fu": 1.2 * lc * t,
            "governing_coefficient_n_per_mpa_fu": coefficient,
            "fu_mpa": fu_mpa, "nominal_strength_n": coefficient * fu_mpa if fu_mpa else None,
            "asd_component_reference_n": coefficient * fu_mpa / 2 if fu_mpa else None,
            "source": AISC_TEAROUT, "complete_joint_acceptance": False}


def block_shear_reference(*, gross_shear_area_mm2: float, net_shear_area_mm2: float,
                          net_tension_area_mm2: float, ubs: float,
                          fy_mpa: float, fu_mpa: float, path_basis: str) -> dict:
    """AISC J4-5 component equation; caller must supply an authenticated path."""
    agv = number(gross_shear_area_mm2, "Agv", positive=True)
    anv = number(net_shear_area_mm2, "Anv", positive=True)
    ant = number(net_tension_area_mm2, "Ant")
    fy, fu = number(fy_mpa, "Fy", positive=True), number(fu_mpa, "Fu", positive=True)
    if anv > agv or ant < 0 or ubs not in (.5, 1.) or not path_basis.strip():
        raise ValueError("invalid block-shear areas, distribution factor or path basis")
    nominal = min(.6 * fu * anv, .6 * fy * agv) + ubs * fu * ant
    return {"nominal_strength_n": nominal, "asd_component_reference_n": nominal / 2,
            "path_basis": path_basis, "source": AISC_CURRENT_BLOCK,
            "complete_joint_acceptance": False}


def annulus_pressure(*, axial_n: float, moment_xy_nmm, inner_radius_mm: float,
                     outer_radius_mm: float) -> dict:
    """Full annulus linear pressure carrying same-state signed T and M.

    The minimum must be nonnegative for this full-contact field to be
    admissible. A negative result requires compression-only contact recovery,
    rather than retaining tensile bearing or silently dropping the moment.
    """
    t = number(axial_n, "axial force")
    a = number(inner_radius_mm, "inner radius", positive=True)
    b = number(outer_radius_mm, "outer radius", positive=True)
    moment = np.asarray(moment_xy_nmm, dtype=float)
    if b <= a or moment.shape != (2,) or not np.isfinite(moment).all():
        raise ValueError("invalid annulus or moment")
    area = math.pi * (b**2 - a**2)
    inertia = math.pi / 4 * (b**4 - a**4)
    mean = t / area
    amplitude = float(np.linalg.norm(moment)) * b / inertia
    return {"area_mm2": area, "second_moment_mm4": inertia,
            "pressure_min_mpa": mean - amplitude, "pressure_max_mpa": mean + amplitude,
            "full_contact_admissible": mean - amplitude >= -1e-12,
            "moment_full_contact_limit_nmm": max(0., t) * inertia / (area * b),
            "compression_only_contact_solved": False}


def _plate_basis(r: float, nu: float) -> np.ndarray:
    """Columns 1, ln r, r², r²ln r; rows w,w',Mr,Qr,Mtheta for D=1."""
    log = math.log(r)
    w = np.array([1., log, r*r, r*r*log])
    slope = np.array([0., 1/r, 2*r, r*(2*log+1)])
    second = np.array([0., -1/r**2, 2., 2*log+3])
    third = np.array([0., 2/r**3, 0., 2/r])
    return np.vstack((w, slope, -second-nu*slope/r,
                      -third-second/r+slope/r**2, -nu*second-slope/r))


def _plate_particular(r: float, pressure: float, nu: float) -> np.ndarray:
    return pressure * np.array([r**4/64, r**3/16,
                               -(3+nu)*r*r/16, -r/2, -(1+3*nu)*r*r/16])


def washer_axisymmetric_bending(*, axial_n: float, inner_radius_mm: float,
                               outer_radius_mm: float, bearing_radius_mm: float,
                               support_opening_radius_mm: float, thickness_mm: float,
                               nu: float = .3) -> dict:
    """Free-edge annulus under prescribed, opposing two-face ring pressures.

    This is an elastic diagnostic, not solved assembly contact. One face has
    uniform head/nut pressure from a to c; the opposite face has uniform
    support pressure from max(a,opening) to b. Both carry the same axial T.
    Piecewise classical plate solutions impose continuity of w,w',Mr,Qr.
    Free radial edges have Mr=Qr=0; w(a)=0 removes rigid translation. Generic
    thin-plate constitutive equations support this idealization, but thick
    washers, real hex/chamfers, own-end moments and contact require more work.
    """
    force = number(axial_n, "axial force")
    a = number(inner_radius_mm, "inner radius", positive=True)
    b = number(outer_radius_mm, "outer radius", positive=True)
    c = number(bearing_radius_mm, "bearing radius", positive=True)
    s = max(a, number(support_opening_radius_mm, "support opening", positive=True))
    thickness = number(thickness_mm, "thickness", positive=True)
    nu = number(nu, "Poisson ratio")
    if force < 0 or not a < c <= b or not a <= s < b or not -1 < nu < .5:
        raise ValueError("invalid two-face washer scenario")
    # ponytail: normalize by OD radius; three constant-pressure regions suffice.
    radii = sorted({a/b, c/b, s/b, 1.})
    pressures = []
    for left, right in pairwise(radii):
        mid = (left+right)/2
        pressures.append((force/(math.pi*(c*c-a*a)) if mid < c/b else 0.)
                         - (force/(math.pi*(b*b-s*s)) if mid > s/b else 0.))
    n = len(pressures)
    matrix, rhs = [], []
    for region, radius, row in ((0, radii[0], 0), (0, radii[0], 2),
                                (0, radii[0], 3), (n-1, 1., 2)):
        line = np.zeros(4*n); line[4*region:4*region+4] = _plate_basis(radius, nu)[row]
        matrix.append(line); rhs.append(-_plate_particular(radius, pressures[region], nu)[row])
    for region, radius in enumerate(radii[1:-1]):
        for row in range(4):
            line = np.zeros(4*n)
            line[4*region:4*region+4] = _plate_basis(radius, nu)[row]
            line[4*region+4:4*region+8] = -_plate_basis(radius, nu)[row]
            matrix.append(line)
            rhs.append(_plate_particular(radius, pressures[region+1]-pressures[region], nu)[row])
    matrix, rhs = np.asarray(matrix), np.asarray(rhs)
    coefficients = np.linalg.solve(matrix, rhs).reshape(n, 4)
    samples = []
    for region, (left, right) in enumerate(pairwise(radii)):
        for radius in np.linspace(left, right, 65):
            state = _plate_basis(radius, nu) @ coefficients[region] + _plate_particular(radius, pressures[region], nu)
            radial, hoop = -6*state[2]*b*b/thickness**2, -6*state[4]*b*b/thickness**2
            equivalent = math.sqrt(max(0., radial**2-radial*hoop+hoop**2))
            samples.append({"radius_mm": float(radius*b), "radial_stress_mpa": float(radial),
                            "hoop_stress_mpa": float(hoop), "von_mises_mpa": equivalent})
    outer = _plate_basis(1., nu) @ coefficients[-1] + _plate_particular(1., pressures[-1], nu)
    return {"status": "prescribed_two_face_axisymmetric_elastic_diagnostic",
            "axial_n": force, "sampled_bending_peak": max(samples, key=lambda r: r["von_mises_mpa"]),
            "required_fy_mpa_at_sampled_bending_first_yield": max(r["von_mises_mpa"] for r in samples),
            "matrix_residual": float(np.max(np.abs(matrix @ coefficients.ravel()-rhs))),
            "outer_free_shear_residual_n_per_mm": float(outer[3]*b),
            "thickness_to_radial_width": thickness/(b-a),
            "radial_bridge_width_mm": s-a, "numeric_product_fy_mpa": None,
            "actual_head_nut_bearing_circle_verified": False,
            "own_end_moment_included": False, "nonlinear_contact_solved": False,
            "steel_through_thickness_bearing_and_local_shear_checked": False,
            "source": MIT_PLATE, "complete_joint_acceptance": False}


def washer_two_sided_interaction(*, axial_n: float, moment_xy_nmm,
                                inner_radius_mm: float, outer_radius_mm: float,
                                bearing_radius_mm: float, support_opening_radius_mm: float,
                                thickness_mm: float, fy_mpa: float | None) -> dict:
    """Same-end T/M pressure admissibility on both washer faces.

    Axisymmetric bending is only the T component. A nonzero M cannot receive
    a combined yield index from it. Negative pressure on either face requires
    actual unilateral contact and rotation recovery. Both T and M must come
    from the same end/state; the opposite bolt end's moment is not substituted.
    """
    moment = np.asarray(moment_xy_nmm, dtype=float)
    if moment.shape != (2,) or not np.isfinite(moment).all():
        raise ValueError("own-end moment must be a finite 2-vector")
    force = number(axial_n, "axial force")
    if force < 0:
        raise ValueError("washer axial force must be nonnegative compression")
    if fy_mpa is not None:
        fy_mpa = number(fy_mpa, "washer yield strength", positive=True)
    head = annulus_pressure(axial_n=force, moment_xy_nmm=moment,
        inner_radius_mm=inner_radius_mm, outer_radius_mm=bearing_radius_mm)
    support = annulus_pressure(axial_n=force, moment_xy_nmm=moment,
        inner_radius_mm=max(inner_radius_mm, support_opening_radius_mm), outer_radius_mm=outer_radius_mm)
    axial = washer_axisymmetric_bending(axial_n=force, inner_radius_mm=inner_radius_mm,
        outer_radius_mm=outer_radius_mm, bearing_radius_mm=bearing_radius_mm,
        support_opening_radius_mm=support_opening_radius_mm, thickness_mm=thickness_mm)
    both = head["full_contact_admissible"] and support["full_contact_admissible"]
    return {"same_end_axial_n": force, "same_end_moment_xy_nmm": moment.tolist(),
            "head_nut_face_pressure": head, "support_face_pressure": support,
            "both_full_contact_fields_admissible": both,
            "axial_component_plate_diagnostic": axial,
            "axial_component_sampled_first_yield_index": axial["required_fy_mpa_at_sampled_bending_first_yield"]/fy_mpa if fy_mpa else None,
            "combined_t_m_metal_yield_index": None,
            "non_axisymmetric_bending_required": bool(np.linalg.norm(moment) > 1e-12),
            "actual_two_face_contact_verified": False, "complete_joint_acceptance": False}


def fitting_condensed_stiffness(fitting: dict, beam_primitive, torsion_primitive, *,
                               elastic_modulus_mpa: float = 200000., nu: float = .3,
                               section_scenario: str = "gross") -> dict:
    """Two conditional 3D strip legs condensed to the two real flange ports.

    Reuses the frame method's beam/torsion primitives through explicit callable
    arguments, avoiding a circular import. The common heel is a rigid section
    junction at the ideal L's centroid intersection. Both ports are mapped
    from the steel centroid to their frozen wood-face hole point by exact
    small-motion rigid offsets. ``net_section_full_leg`` reduces the whole
    strip to the two side ligaments around a centered hole; it is a sensitivity
    model, not exact localized-hole/curved-bend flexibility. No bolt friction
    or shaft-axis rotation constraint is added by this steel component.
    """
    e = number(elastic_modulus_mpa, "steel elastic modulus", positive=True)
    nu = number(nu, "Poisson ratio")
    if not -1 < nu < .5 or section_scenario not in ("gross", "net_section_full_leg"):
        raise ValueError("invalid strip stiffness scenario")
    model = fitting["angle_id"].split("_", 1)[0]
    spec = FITTINGS[model]
    origin = vector(fitting["origin_xyz_mm"], "origin")
    u, v, w = [vector(fitting[key], key) for key in ("u_xyz", "v_xyz", "w_xyz")]
    if not np.allclose(np.column_stack((u, v, w)).T @ np.column_stack((u, v, w)), np.eye(3), atol=2e-8):
        raise ValueError("fitting stiffness requires orthonormal axes")
    removed = HOLE if section_scenario == "net_section_full_leg" else 0.
    area = (WIDTH-removed)*THICKNESS
    iy = (WIDTH-removed)*THICKNESS**3/12
    iz = THICKNESS*(WIDTH**3-removed**3)/12
    j = (2*torsion_primitive((WIDTH-removed)/2, THICKNESS) if removed
         else torsion_primitive(WIDTH, THICKNESS))
    heel = origin+(u+v)*(THICKNESS/2)
    matrix = np.zeros((18, 18))
    ports, legs = [], []
    for port_node, (flange, along, inward) in enumerate((("beam", u, v), ("post", v, u)), 1):
        far = max(spec[f"{flange}_holes_mm"])
        port = origin+along*far
        centroid = port+inward*(THICKNESS/2)
        length = float(np.linalg.norm(centroid-heel))
        basis = np.column_stack((along, w, np.cross(along, w)))
        rotate = np.zeros((6, 6)); rotate[:3, :3] = basis.T; rotate[3:, 3:] = basis.T
        offset = centroid-port
        x, y, z = offset
        skew = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
        rigid = np.eye(6); rigid[:3, 3:] = -skew
        transform = np.zeros((12, 12))
        transform[:6, :6] = rotate
        transform[6:, 6:] = rotate @ rigid
        element = np.asarray(beam_primitive(length, area, iy, iz, j, e, e/(2*(1+nu))), dtype=float)
        if element.shape != (12, 12) or not np.isfinite(element).all():
            raise ValueError("beam primitive must provide finite12x12 stiffness")
        global_k = transform.T @ element @ transform
        indices = list(range(6))+list(range(6*port_node, 6*port_node+6))
        matrix[np.ix_(indices, indices)] += global_k
        ports.append({"flange": flange, "point_xyz_mm": port.tolist(),
                      "steel_centroid_xyz_mm": centroid.tolist()})
        legs.append({"flange": flange, "centroid_length_mm": length})
    condensed = matrix[6:, 6:] - matrix[6:, :6] @ np.linalg.solve(matrix[:6, :6], matrix[:6, 6:])
    condensed = (condensed+condensed.T)/2
    return {"angle_id": fitting["angle_id"], "section_scenario": section_scenario,
            "ports": ports, "port_dof_order": "beam(uXYZ,thetaXYZ),post(uXYZ,thetaXYZ); rotations radians",
            "global_port_stiffness_n_mm_rad": condensed.tolist(),
            "eliminated_heel_xyz_mm": heel.tolist(), "legs": legs,
            "section": {"area_mm2": area, "inertia_y_mm4": iy, "inertia_z_mm4": iz,
                        "torsion_j_mm4": float(j), "elastic_modulus_mpa": e, "nu": nu},
            "bend_hole_locality_and_heel_compliance_verified": False,
            "bolt_friction_or_axial_rotation_constraint_added": False,
            "actual_product_stiffness_verified": False, "complete_joint_acceptance": False}


def flange_reference(fitting: dict, flange: str, loads: list[dict]) -> dict:
    """Recover nominal flat-leg sections from each signed external point load.

    Loads must be actions ON STEEL, with global point/force/moment. All applied
    hole and compression-contact actions on the cut's far side are included.
    No section inside the unverified bend is described as an actual heel.
    """
    if flange not in ("beam", "post"):
        raise ValueError("unknown flange")
    model = fitting["angle_id"].split("_", 1)[0]
    definition = FITTINGS[model]
    along = vector(fitting["u_xyz" if flange == "beam" else "v_xyz"], "leg axis")
    across = vector(fitting["w_xyz"], "width axis")
    normal = np.cross(along, across)
    basis = np.column_stack((along, across, normal))
    if not np.allclose(basis.T @ basis, np.eye(3), atol=2e-8):
        raise ValueError("flange basis must be orthonormal")
    origin = vector(fitting["origin_xyz_mm"], "origin")
    holes = definition[f"{flange}_holes_mm"]
    length = definition[f"{flange}_length_mm"]
    markers = {THICKNESS, length}
    markers.update(value for hole in holes for value in (hole-HOLE/2, hole, hole+HOLE/2)
                   if THICKNESS <= value <= length)
    markers.update(float((vector(load["point_xyz_mm"], "load point")-origin) @ along)
                   for load in loads if THICKNESS <= float((vector(load["point_xyz_mm"], "load point")-origin) @ along) <= length)
    stations = sorted(set(markers) | {float(s) for lo, hi in pairwise(sorted(markers))
                                     for s in np.linspace(lo, hi, 33)})
    states = []
    for station in stations:
        point = origin + along*station
        force, moment = np.zeros(3), np.zeros(3)
        for load in loads:
            at = vector(load["point_xyz_mm"], "load point")
            if float((at-origin) @ along) + 1e-7 < station:
                continue
            action = vector(load["force_on_steel_xyz_n"], "steel force")
            force += action
            moment += vector(load["moment_on_steel_at_point_xyz_nmm"], "steel moment") + np.cross(at-point, action)
        chord = max((2*math.sqrt(max(0., (HOLE/2)**2-(station-h)**2)) for h in holes), default=0.)
        states.append({"station_from_assumed_corner_mm": station,
                       "force_local_n": (basis.T @ force).tolist(),
                       "moment_local_nmm": (basis.T @ moment).tolist(),
                       **section_reference(width_mm=WIDTH, thickness_mm=THICKNESS,
                                           removed_center_width_mm=chord,
                                           force_local_n=basis.T @ force,
                                           moment_local_nmm=basis.T @ moment, fy_mpa=FY_CATALOG)})
    return {"angle_id": fitting["angle_id"], "flange": flange, "sections": states,
            "sampled_maximum_nominal_first_yield_index": max(s["nominal_first_yield_index"] for s in states),
            "continuous_section_extrema_verified": False,
            "steel_torsion_complete": all(s["torsion_method_complete"] for s in states),
            "actual_bend_flat_start_and_hole_datums_verified": False,
            "flange_prying_and_same_state_contact_solution_verified": False,
            "complete_joint_acceptance": False}


def evaluate() -> dict:
    if sha(LAYOUT) != LAYOUT_SHA:
        raise ValueError("frozen occupied source differs")
    source = json.loads(LAYOUT.read_text())
    angles = source["raw_fittings"]
    axes = source["installed_axes"]
    if len(angles) != 36 or len(axes) != 70 or sum(len(a["attachments"]) for a in axes) != 72:
        raise ValueError("candidate fitting/physical-shaft census differs")
    capacity_geometry = []
    for model, fitting in FITTINGS.items():
        for flange in ("beam", "post"):
            far = max(fitting[f"{flange}_holes_mm"])
            clear = min(hole_clear_distance(length_mm=fitting[f"{flange}_length_mm"],
                                           width_mm=WIDTH, hole_mm=HOLE, used_center_mm=far,
                                           other_centers_mm=[h for h in fitting[f"{flange}_holes_mm"] if h != far],
                                           direction_xy=d) for d in ((1., 0.), (-1., 0.), (0., 1.), (0., -1.)))
            unit = section_reference(width_mm=WIDTH, thickness_mm=THICKNESS,
                                     removed_center_width_mm=0., force_local_n=(0., 0., 1.),
                                     moment_local_nmm=(0., -(far-THICKNESS), 0.), fy_mpa=FY_CATALOG)
            capacity_geometry.append({"model": model, "flange": flange, **fitting,
                                      "width_mm": WIDTH, "thickness_mm": THICKNESS, "factory_hole_mm": HOLE,
                                      "minimum_cardinal_clear_ligament_mm": clear,
                                      "catalog_fy_mpa_scenario": FY_CATALOG,
                                      "unsupported_flat_leg_unit_normal_load_reference": unit,
                                      "unsupported_flat_leg_first_yield_force_reference_n": 1/unit["nominal_first_yield_index"],
                                      "bearing_tearout": bearing_tearout_reference(clear_distance_mm=clear,
                                          bolt_diameter_mm=12.7, thickness_mm=THICKNESS, fu_mpa=None)})
    small = {(r["axis_id"], r["role"]): r for r in source["small_washer_changes"]}
    washers, bending_profiles = [], {}
    by_axis = {r["id"]: r for r in axes}
    for seat in source["washer_seats"]:
        change = small.get((seat["axis_id"], seat["role"]))
        axis = by_axis[seat["axis_id"]]
        hardware = axis["hardware_scenario"]
        minimum_t = change["minimum_published_thickness_mm_for_resistance"] if change else None
        # Larger washers have occupied max dimensions, not authenticated minima.
        profile_id, profile_ids = None, []
        if change:
            # Across flats is NOT an authenticated circular bearing footprint.
            # Include smaller comparison hardware; do not transfer proxy22.225.
            for bearing in (18.6944, 19.05, hardware["hex_across_flats_mm"]):
                identity = f"small-sae-half-opening{seat['planned_support_opening_mm']}-bearing{bearing}"
                profile_ids.append(identity)
                if identity not in bending_profiles:
                    corners = [washer_axisymmetric_bending(axial_n=1., inner_radius_mm=inside/2,
                        outer_radius_mm=outside/2, bearing_radius_mm=bearing/2,
                        support_opening_radius_mm=seat["planned_support_opening_mm"]/2,
                        thickness_mm=minimum_t) | {"id_mm": inside, "od_mm": outside}
                        for inside in (.526*INCH, .546*INCH) for outside in (1.055*INCH, 1.092*INCH)]
                    bending_profiles[identity] = {"assumed_circular_bearing_diameter_mm": bearing,
                        "actual_bearing_circle_from_AF_inferred": False,
                        "unit_axial_two_face_bending": max(corners,
                            key=lambda r: r["required_fy_mpa_at_sampled_bending_first_yield"]),
                        "small_washer_tolerance_corner_comparisons": corners}
            profile_id = profile_ids[-1]
        wood = wood_washer_annulus_reference_lbf(washer_outer_diameter_in=1.055 if change else seat["od_mm"]/INCH,
                washer_inner_diameter_in=seat["id_mm"]/INCH,
                wood_bore_diameter_in=seat["planned_support_opening_mm"]/INCH) if seat["support_material"] == "wood" else None
        washers.append({"axis_id": seat["axis_id"], "role": seat["role"],
                        "support_material": seat["support_material"],
                        "nominal_occupied_od_mm": seat["od_mm"], "nominal_occupied_id_mm": seat["id_mm"],
                        "minimum_published_thickness_mm": minimum_t,
                        "small_washer_product": change["source"] if change else None,
                        "unit_axial_two_face_bending_profile_id": profile_id,
                        "bearing_circle_sensitivity_profile_ids": profile_ids,
                        "nominal_wood_annulus_reference": wood,
                        "numeric_washer_fy_mpa": None, "delivered_stack_verified": False,
                        "larger_washer_minimum_dimensions_and_property_basis_verified": False,
                        "actual_two_face_contact_and_own_end_moment_verified": False})
    return {"schema": "thin_bolted_steel_resistance/v1", "candidate": source["candidate"],
            "revision": source["revision"], "status": "CONDITIONAL_COMPONENT_METHODS_WITH_NAMED_GAPS",
            "source_sha256": {str(LAYOUT.relative_to(ROOT)): LAYOUT_SHA,
                              str(Path(__file__).relative_to(ROOT)): sha(Path(__file__)),
                              "mini_moonboard/wood_joint_bolt_resistance.py": sha(ROOT/"mini_moonboard/wood_joint_bolt_resistance.py"),
                              "mini_moonboard/bolted_timber_checks.py": sha(ROOT/"mini_moonboard/bolted_timber_checks.py"),
                              "uv.lock": sha(ROOT/"uv.lock")},
            "counts": {"fittings": len(angles), "flange_ports": 72, "new_physical_shafts": 58,
                       "starting_physical_shafts": 12, "shared_new_shafts": sum(len(a["attachments"]) > 1 for a in axes),
                       "washer_ends": len(washers), "small_washer_ends": len(small)},
            "sources": {"catalog": CATALOG,
                        "b103_current_sku": "https://www.eaton.com/us/en-us/skuPage.B103ZN.html",
                        "b104_current_sku": "https://www.eaton.com/us/en-us/skuPage.B104ZN.html",
                        "small_washer": "https://boltdepot.com/Product-Details?product=3051",
                        "comparison_half_nut_min_AF_not_bearing_circle": "https://boltdepot.com/Product-Details?product=2586",
                        "plate_equations": MIT_PLATE, "bearing_tearout_equations": AISC_TEAROUT,
                        "block_shear_equation": AISC_CURRENT_BLOCK,
                        "independent_block_shear_example": AISC_BLOCK},
            "material_and_product_gates": {
                "catalog_fy_mpa_scenario": FY_CATALOG, "catalog_fu_mpa": None,
                "exact_current_sku_catalog_geometry_reconciled": False,
                "b103_conflict": "Current SKU 4.12x4.12in legs and1/4in thickness versus catalog short1.625in leg and general7/32in thickness.",
                "b104_conflict": "Current SKU description says4.12x4.12in; specification4.125/3.5in and0.64lb versus catalog0.78lb.",
                "actual_bend_datums_radius_thickness_tolerances_verified": False,
                "factory_strut_rating_transferred": False, "strut_torque_to_wood_transferred": False,
                "bolt_product_grade_root_area_fyb_thread_occupancy_verified": False,
                "washer_grade8_to_yield_conversion_used": False},
            "nominal_fitting_component_geometry": capacity_geometry,
            "fitting_compliance_method": {
                "api": "fitting_condensed_stiffness(fitting,beam_stiffness,rectangular_torsion)",
                "frame_primitives": "scripts.thin_bolted_frame_mechanics beam_stiffness/rectangular_torsion; caller must pin producer when used",
                "elastic_modulus_mpa_scenario": 200000., "nu_scenario": .3,
                "section_scenarios": ["gross", "net_section_full_leg"],
                "ports": "actual frozen wood-face bolt holes with t/2 steel centroid rigid offsets",
                "internal_node": "common nominal L heel centroid statically condensed",
                "known_answer_fixture": "100N beam-port force along post axis, post port fixed; F[Lb³/(3EI)+Lb²Lp/(EI)+Lb/(kGA)+Lp/(EA)]",
                "tests": "tests/test_thin_bolted_steel_resistance.py: analytical L-frame, six rigid motions and net softening",
                "actual_product_stiffness_or_physical_bounds_established": False},
            "washer_reference_inputs": washers,
            "washer_bending_profiles": bending_profiles,
            "demand_comparison_input": {
                "attachment_actions": "case_id,axis_id,angle_id,flange,point_xyz_mm,force_on_receiver_xyz_n,moment_on_receiver_at_point_xyz_nmm",
                "flange_contact_actions": "same keys; force on receiver and matching independent point; do not combine unequal pair forces",
                "bolt_sections": "same-state force_n/moment_nmm in shaft basis; actual diameter_mm/material_basis/section_basis/Fy required",
                "washer_end_states": "axis_id,end role,same-state axial_n,moment_xy_nmm and actual bearing circle/min dimensions required",
                "unknown_moments_zero_filled": False},
            "missing": ["Exact B103/B104 dimensional applicability, bend/radius/tolerance and minimum steel thickness basis.",
                        "Catalog Fu and authenticated complete block-shear paths/net-section rupture applicability.",
                        "Fresh complete fitting wrenches, same-state flange/prying/contact and shared-shaft allocations.",
                        "Bolt product/grade, loaded shank/root/tensile area, actual thread occupancy, same-section bending and nut/head/stripping checks.",
                        "Larger washer minimum dimensions; all washer numeric yield basis and actual head/nut bearing circles.",
                        "Washer own-end moments and compression-only two-face contact, local3D/thickness applicability and loaded support."],
            "limits": ["Nominal flat-leg first-yield comparisons omit hole/bend stress concentrations and do not establish an angle rating.",
                       "AISC equations are independently reproducible component references; Fu/path/applicability gaps prevent candidate strengths.",
                       "Unit washer plate responses are prescribed axisymmetric pressure diagnostics; no actual capacity or prying=0 inference.",
                       "The existing625psi wood-annulus reference uses a full nominal annulus and perpendicular bearing; actual grain/contact checks remain separate.",
                       "Neither a catalog yield scenario nor solver convergence is complete-joint acceptance."],
            "release": source["release"], "complete_joint_acceptance": False,
            "fabrication_release": False, "climbing_release": False}


def compare_flange_actions(attachment_actions: list[dict], flange_contact_actions: list[dict]) -> dict:
    """Compare explicit fresh scenario actions; never infer angle allocation.

    Attachment/contact moments are whatever the caller's method exports.
    A point-pin method's numeric zeros remain idealized zeros, rather than
    evidence that physical bolt-end moments or angle prying vanish.
    """
    if sha(LAYOUT) != LAYOUT_SHA:
        raise ValueError("frozen occupied source differs")
    layout = json.loads(LAYOUT.read_text())
    fittings = {f["angle_id"]: f for f in layout["raw_fittings"]}
    attachment_by_id = {(axis["id"], port["angle_id"], port["flange"]): port
                        for axis in layout["installed_axes"] for port in axis["attachments"]}
    grouped, used = {}, set()
    for action in attachment_actions:
        identity = (action["axis_id"], action["angle_id"], action["flange"])
        if identity not in attachment_by_id:
            raise ValueError(f"attachment leaves the frozen candidate: {identity}")
        key = (action["case_id"], action.get("accessory_placement", "unspecified"), action["angle_id"], action["flange"])
        if key in used:
            raise ValueError(f"duplicate case/flange attachment action: {key}")
        used.add(key)
        port = attachment_by_id[identity]
        if not np.allclose(vector(action["point_xyz_mm"], "attachment point"),
                           vector(port["entry_xyz_mm"], "frozen port"), atol=1e-5, rtol=0):
            raise ValueError("attachment point leaves the frozen flange hole")
        grouped.setdefault(key, []).append({"point_xyz_mm": action["point_xyz_mm"],
            "force_on_steel_xyz_n": (-vector(action["force_on_receiver_xyz_n"], "receiver force")).tolist(),
            "moment_on_steel_at_point_xyz_nmm": (-vector(action["moment_on_receiver_at_point_xyz_nmm"], "receiver moment")).tolist()})
    for contact in flange_contact_actions:
        key = (contact["case_id"], contact.get("accessory_placement", "unspecified"), contact["angle_id"], contact["flange"])
        if key not in grouped:
            raise ValueError("contact has no corresponding case/flange attachment")
        grouped[key].append({"point_xyz_mm": contact["point_xyz_mm"],
            "force_on_steel_xyz_n": (-vector(contact["force_on_receiver_xyz_n"], "contact force")).tolist(),
            "moment_on_steel_at_point_xyz_nmm": (-vector(contact["moment_on_receiver_at_point_xyz_nmm"], "contact moment")).tolist()})
    results = []
    for (case, placement, angle_id, flange), loads in sorted(grouped.items()):
        fitting = fittings[angle_id]
        result = flange_reference(fitting, flange, loads)
        sections = result.pop("sections")
        result["section_count"] = len(sections)
        result["sampled_stress_witness"] = max(sections, key=lambda s: s["nominal_first_yield_index"])
        definition = FITTINGS[angle_id.split("_", 1)[0]]
        along = vector(fitting["u_xyz" if flange == "beam" else "v_xyz"], "leg axis")
        across = vector(fitting["w_xyz"], "width axis")
        attachment_force = vector(loads[0]["force_on_steel_xyz_n"], "attachment force")
        lateral = np.array([attachment_force @ along, attachment_force @ across])
        magnitude = float(np.linalg.norm(lateral))
        holes = definition[f"{flange}_holes_mm"]
        clear = hole_clear_distance(length_mm=definition[f"{flange}_length_mm"],
                width_mm=WIDTH, hole_mm=HOLE, used_center_mm=max(holes),
                other_centers_mm=[h for h in holes if h != max(holes)],
                direction_xy=lateral) if magnitude > 1e-10 else None
        bearing = bearing_tearout_reference(clear_distance_mm=clear, bolt_diameter_mm=12.7,
                                           thickness_mm=THICKNESS, fu_mpa=None) if clear is not None else None
        results.append({"case_id": case, "accessory_placement": placement, **result, "external_point_actions_on_steel": loads,
                        "attachment_in_plane_force_n": magnitude,
                        "signed_hole_clear_distance_mm": clear,
                        "required_fu_mpa_for_asd_bearing_tearout_component": 2*magnitude/bearing["governing_coefficient_n_per_mpa_fu"]
                        if bearing and bearing["governing_coefficient_n_per_mpa_fu"] > 0 else None,
                        "actual_own_end_moments_verified": False,
                        "force_allocation_unique_compatible_and_physical_verified": False})
    expected = {(f["angle_id"], flange) for f in fittings.values() for flange in ("beam", "post")}
    cases = []
    for case, placement in sorted({(r["case_id"], r["accessory_placement"]) for r in results}):
        rows = [r for r in results if r["case_id"] == case and r["accessory_placement"] == placement]
        missing = sorted(expected-{(r["angle_id"], r["flange"]) for r in rows})
        cases.append({"case_id": case, "accessory_placement": placement, "flange_actions_checked": len(rows), "missing_flange_actions": missing,
                      "nominal_sampled_first_yield_exceedances": sum(r["sampled_maximum_nominal_first_yield_index"] > 1 for r in rows),
                      "sampled_maximum_nominal_first_yield_index": max(r["sampled_maximum_nominal_first_yield_index"] for r in rows),
                      "complete_joint_acceptance": False})
    return {"status": "FRESH_SCENARIO_FLANGE_COMPONENT_COMPARISONS", "cases": cases,
            "flange_comparisons": results, "paired_angle_equal_sharing_assumed": False,
            "bolt_end_moment_and_prying_zero_inferred": False,
            "physical_shared_shaft_strength_checked": False,
            "washer_same_state_tension_and_own_end_moments_available": False,
            "complete_joint_acceptance": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET/"steel-resistance-methods-v4.json")
    parser.add_argument("--demands", type=Path, help="Fresh source-bound attachment/contact action report")
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve prior component evidence")
    report = evaluate()
    if args.demands:
        demands = json.loads(args.demands.read_text())
        if demands.get("candidate") != report["candidate"] or demands.get("source_sha256", {}).get(str(LAYOUT.relative_to(ROOT))) != LAYOUT_SHA:
            raise ValueError("demand source must authenticate this candidate and frozen occupied source")
        report["fresh_demand_comparison"] = compare_flange_actions(demands["attachment_actions"],
                                                                   demands["flange_contact_actions"])
        report["source_sha256"][str(args.demands.resolve().relative_to(ROOT))] = sha(args.demands)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"output": str(args.out), "counts": report["counts"], "status": report["status"]}, indent=2))


if __name__ == "__main__":
    main()
