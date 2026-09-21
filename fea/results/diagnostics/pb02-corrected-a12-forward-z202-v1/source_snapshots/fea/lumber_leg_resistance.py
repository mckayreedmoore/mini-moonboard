"""Conditional sawn-leg section demands and references; NOT an adequacy check.

2024 NDS/Supplement, US Douglas Fir-Larch No.2, dry, unincised, normal
temperature; CD=CM=Ct=Ci=Cr=1. No repetitive-member or flat-use increase.
No beam stability, beam-column interaction, torsional strength, local bolt-group
strength, floor restraint, steel procurement or construction qualification.
"""
import argparse
import hashlib
import json
import math
import tarfile
from pathlib import Path

from fea.dowel_yield import single_shear
from fea.leg_stock_screen import section
from mini_moonboard import lumber_leg_frame as model

PSI_MPA = 0.006894757293168361
SOURCES = {
    "2024 Supplement Table4A pp32,34": "https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf",
    "2024 NDS 3.7,3.9": "https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf",
    "2024 NDS Appendices G and J": "https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf",
    "2024 NDS Chapter12": "https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf",
    "TR12 Table1-1": "https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf",
}
LIMITS = (__doc__ + "\nDemands inherit native fixed XYZ floor, omitted gravity, isotropic "
          "wood and uncalibrated bilateral connectors. Separate references are NOT "
          "combined resistance, an interaction ratio, a pass/fail decision or approval.")


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def column_reference(size, length_mm):
    """K=1 in BOTH axes requires translation restraint at both ends, unverified.

    Eq3.7-1, c=.8. No column resistance returned beyond NDS slenderness limit.
    This is concentric compression only, not beam-column resistance.
    """
    if size not in model.WIDTHS or not math.isfinite(length_mm) or length_mm <= 0:
        raise ValueError("Require supported stock and positive finite length")
    width = model.WIDTHS[size]
    cfb, cfc = {"2x6": (1.3, 1.1), "2x8": (1.2, 1.05),
                "2x10": (1.1, 1.), "2x12": (1., 1.)}[size]
    fc = 1350*cfc*PSI_MPA
    emin = 580000*PSI_MPA
    ratios = {"in_plane": length_mm/width, "out_of_plane": length_mm/38.1}
    fce = {axis: .822*emin/r**2 for axis, r in ratios.items()}
    q = min(fce.values())/fc
    # Rationalized NDS quadratic root avoids subtractive cancellation.
    cp = 2*q/(1+q+math.sqrt((1+q)**2-3.2*q))
    valid = max(ratios.values()) <= 50
    return {"species_grade": "US Douglas Fir-Larch No.2, NOT North/South substitute",
        "K_both_axes": 1., "length_mm": length_mm, "slenderness": ratios,
        "within_slenderness_limit": valid, "FcE_mpa": fce, "Cp": cp if valid else None,
        "Fc_star_mpa": fc, "Fb_size_only_mpa": 900*cfb*PSI_MPA,
        "Fv_mpa": 180*PSI_MPA, "Emin_mpa": emin,
        "reference_concentric_compression_n": fc*cp*38.1*width if valid else None}


def bolt_reference(main_fe_psi=3650., side_fe_psi=3650.):
    """Two 38.1mm sawn members, root diameter throughout; assumed steel yield.

    Fe=3650 psi is conservative perpendicular bearing for US DF-L G=.50,
    3/8in nominal bolt. Ktheta=1.25 reduction bound. No group multiplication.
    """
    if not all(math.isfinite(v) and v > 0 for v in (main_fe_psi, side_fe_psi)):
        raise ValueError("Require positive finite bearing reference values")
    inputs = {"main_length_in": 1.5, "side_length_in": 1.5,
        "main_bearing_lb_in": main_fe_psi*.298, "side_bearing_lb_in": side_fe_psi*.298,
        "main_yield_moment_lb_in": 45000*.298**3/6,
        "side_yield_moment_lb_in": 45000*.298**3/6, "gap_in": 0.,
        "reduction_terms": {"Im": 5., "Is": 5., "II": 4.5, "IIIm": 4., "IIIs": 4., "IV": 4.}}
    result = single_shear(**inputs)
    return {"inputs": inputs, **result,
        "reference_lateral_n": result["reference_lateral_lbf"]*4.4482216152605,
        "steel_Fyb_assumed_psi": 45000., "steel_and_thread_geometry_qualified": False}


def directional_bolt_reference(force, along):
    """NDS Appendix J Eq.J-2; only YZ lateral load sets bearing angles.

    US DF-L G=.50: Fe_parallel5600psi, tabulated Fe_perpendicular3650psi.
    Keep conservative reduction terms unchanged. Axial/group strength absent.
    """
    if len(force) != 3 or not all(math.isfinite(v) for v in force):
        raise ValueError("Require finite XYZ force")
    if (len(along) != 3 or not all(math.isfinite(v) for v in along)
            or abs(math.hypot(*along)-1) > 1e-8 or abs(along[0]) > 1e-8):
        raise ValueError("Require a unit leg-grain vector in the YZ plane")
    lateral = math.hypot(force[1], force[2])
    tangent = (model.b.point(0., 1., 0.)-model.b.point(0., 0., 0.)).normalized().toTuple()
    bearing, angles = [], []
    for grain in (tangent, along):
        cos2 = min(1., ((force[1]*grain[1]+force[2]*grain[2])/lateral)**2) if lateral else 0.
        bearing.append(5600*3650/(5600*(1-cos2)+3650*cos2))
        angles.append(math.degrees(math.acos(math.sqrt(cos2))) if lateral else None)
    reference = bolt_reference(*bearing)
    return {"rim_leg_angle_deg": angles, "rim_leg_bearing_psi": bearing,
        "reference_lateral_n": reference["reference_lateral_n"],
        "governing_mode": reference["governing_mode"],
        "lateral_demand_reference_ratio": lateral/reference["reference_lateral_n"],
        "axial_strength_evaluated": False, "group_strength_evaluated": False}


def section_demand(points, forces, origin, along, across, properties):
    """Loads on the upper free body; cut traction is the NEGATIVE wrench.

    Negative axial force is compression. Moments include actual interface-to-
    centroid eccentricity. Shear stresses are separate rectangular VQ/It maxima;
    they exclude torsion. Normal stress extrema combine simultaneous biaxial
    bending, not independent scenario peaks. No stress-to-strength verdict.
    """
    if set(points) != set(forces) or not points:
        raise ValueError("Require matching nonempty connector points and forces")
    if any(len(v) != 3 or not all(math.isfinite(x) for x in v)
           for v in [*points.values(), *forces.values(), origin, along, across]):
        raise ValueError("Require finite XYZ vectors")
    force = [math.fsum(f[i] for f in forces.values()) for i in range(3)]
    moments = [cross([p[i]-origin[i] for i in range(3)], forces[n]) for n, p in points.items()]
    moment = [math.fsum(m[i] for m in moments) for i in range(3)]
    axial = dot(force, along)
    shear = [force[0], dot(force, across)]
    bending = [moment[0], dot(moment, across)]
    normal = axial/properties["area_mm2"]
    spread = abs(bending[0])/properties["in_plane_S_mm3"] + abs(bending[1])/properties["out_of_plane_S_mm3"]
    return {"origin_xyz_mm": origin, "upper_load_force_xyz_n": force,
        "upper_load_moment_xyz_nmm": moment, "axial_n_tension_positive": axial,
        "shear_out_in_plane_n": shear, "bending_in_out_plane_nmm": bending,
        "torsion_nmm": dot(moment, along),
        "normal_stress_extrema_mpa_tension_positive": [normal-spread, normal+spread],
        "shear_out_in_plane_max_mpa_excluding_torsion": [1.5*abs(v)/properties["area_mm2"] for v in shear]}


def screen(path):
    """Consume an accepted native archive; hashes are integrity, not a new solve."""
    path = Path(path)
    with tarfile.open(path) as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
    report = json.loads(files["report.json"])
    if set(report["artifact_sha256"]) != set(files)-{"report.json"} or any(
            hashlib.sha256(files[n]).hexdigest() != sha for n, sha in report["artifact_sha256"].items()):
        raise ValueError("Native evidence hash differs")
    if not report["passed"] or set(report["runs"]) != {"k100", "k1000", "k10000"}:
        raise ValueError("Require all three accepted native runs")
    for name, sha in report["source_sha256"].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != sha:
            raise ValueError("Native source identity changed")
    geometry_name = report.get("geometry")
    if geometry_name == "spread-100x50-top150":
        from mini_moonboard import lumber_leg_spread_frame as spread
        if spread.geometry is not model.geometry:
            raise ValueError("Revised leg axes require a new section mapping")
    elif geometry_name is not None:
        raise ValueError("Unsupported native leg geometry")
    size, extension = report["stock"], report["extension_mm"]
    centre, foot, along_v, across_v = model.geometry(size, extension)
    length = (centre-foot).Length
    along, across = list(along_v.toTuple()), list(across_v.toTuple())
    properties = section(38.1, model.WIDTHS[size])
    inputs = json.loads(files["input.json"])
    points = {n: p["point_mm"] for n, p in inputs["points"].items()
              if n.startswith("lumber_leg_bolt_")}
    if len(points) != 8:
        raise ValueError("Require eight actual two-member leg connectors")
    rows = []
    for stiffness, run in report["runs"].items():
        if len(run["basis"]) != 9 or not all(r["passed"] for r in run["basis"]) or len(run["scenarios"]) != 216:
            raise ValueError("Incomplete accepted native cases")
        for case in run["scenarios"]:
            forces = case["leg_connector_force_on_leg_n"]
            if set(forces) != set(points):
                raise ValueError("Connector force ownership differs")
            legs = {}
            for side, sign in (("left", -1), ("right", 1)):
                pp = {n: p for n, p in points.items() if n.startswith(f"lumber_leg_bolt_{side}_")}
                ff = {n: forces[n] for n in pp}
                # Lowest full rectangular section above the bevel; highest clear
                # section below BOTH the physical hole envelope and the native
                # MPC nodal load spread. The latter can extend beyond a bore.
                low = abs(across[2])*model.WIDTHS[size]/(2*along[2]) + .001
                hole_low = min(dot([p[i]-foot.toTuple()[i] for i in range(3)], along)
                               for p in pp.values())-11.1125/2
                support_nodes = {n for name in pp for n, w in zip(
                    inputs["points"][name]["gusset_nodes"],
                    inputs["points"][name]["other_weights"], strict=True) if w != 0}
                load_low = min(dot([inputs["nodes"][str(n)][i]-foot.toTuple()[i]
                                    for i in range(3)], along) for n in support_nodes)
                high = min(hole_low, load_low)-.001
                if not 0 <= low < high < length:
                    raise ValueError("No clear prismatic section interval")
                sections = []
                for station in (low, high):
                    origin = list((foot+along_v*station).toTuple())
                    origin[0] = sign*(model.b.HALF+38.1/2)
                    sections.append({"station_from_foot_mm": station,
                        **section_demand(pp, ff, origin, along, across, properties)})
                legs[side] = sections
            rows.append({"stiffness": stiffness,
                "case": {k: case[k] for k in ("hold", "climber_lb", "weight_factor", "horizontal_direction_deg", "force_n")},
                "sections": legs,
                "bolts": {n: {"force_xyz_n": f, "lateral_n": math.hypot(f[1], f[2]),
                              "axial_global_x_n": f[0],
                              "directional_reference": directional_bolt_reference(f, along)}
                          for n, f in forces.items()}})
    return {"archive": str(path), "archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "stock": size, "geometry": geometry_name or "compact-50x50-top120",
        "extension_mm": extension, "native_leg_modulus_mpa": report["leg_modulus_mpa"],
        "qualified_for_design": False, "combined_strength_evaluated": False,
        "limits": LIMITS, "sources": SOURCES, "section_properties": properties,
        "conditional_column_reference": column_reference(size, length),
        "conditional_single_bolt_reference": bolt_reference(), "rows": rows,
        "section_scope": "Two endpoints bound force/bending-derived stress extrema in the unloaded "
            "clear prismatic interval only. Excludes bolt group, bevel, local stresses and torsional shear."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    print(json.dumps(screen(parser.parse_args().archive), indent=2, allow_nan=False))
