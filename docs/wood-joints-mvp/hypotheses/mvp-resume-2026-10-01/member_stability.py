"""Saved six-case timber torsion and stability arithmetic; no solve or CAD.

Keep each complete signed cut together. Existing timber bolt stations are
conditional lateral restraints, not an inference of brace stiffness from a
first-order response. Rectangular torsion uses a declared parallel-grain shear
allowance; the NDS does not supply a separate torsional allowable here.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import sys
from collections import Counter
from functools import cache
from itertools import pairwise
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

import bottom_corner_checks as bottom
import frame_state_contract as frame_contract
import member_screen as member
import numpy as np

from fea.reinforced_timber_resistance import effective_beam_length, member_check
from scripts.floor_taper_checks import rectangular_shear

accounting = member.accounting
sha, read, require = member.sha, member.read, member.require
FRAME = HERE / "corner-frame-attempt01"
RESPONSE = HERE / "all-outer-corner-frame-attempt01"
MEMBER = HERE / "member-screen-attempt02/all-outer-clearance01"
GEOMETRY_REFERENCE = MEMBER / "geometry.json"
OUTPUT = HERE / "member-stability-attempt01"
FRAME_MAP = (HERE.parent / "evaluation-resume-2026-09-24"
             / "current-frame-timber-material-frame-map-attempt01"
             / "current-frame-timber-material-frame-map.json")
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    FRAME / "model.json": "d17dadd7c999e4a1634f53226cf63e131f547cd9cf5d46d87d75c935f2dc807e",
    FRAME / "row-identities.json": "bec1feb75be61b321220a047a652cc42f09c4c11d1d3c66377c4035bde4826d5",
    FRAME / "operators.npz": "f40bf53412afb400df23ff108e90bac66db3c493da26a19af5c05de329c165ad",
    GEOMETRY_REFERENCE: "ecfeee2627fc67d91ce89acd5253bf99a4d79b06451c94ced6b915a664009f9d",
    accounting.MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    FRAME_MAP: "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
    Path(frame_contract.__file__).resolve(): "22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5",
}
PRIMARY = {
    "NDS2024_chapter3": {
        "url": "https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf",
        "sha256": "205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644",
        "clauses": ["3.3.3", "Table 3.3.3 footnote 1", "3.6.3", "3.7.1", "3.9.1", "3.9.2"],
    },
    "FPL_Wood_Handbook_chapter9": {
        "url": "https://research.fs.usda.gov/download/treesearch/37423.pdf",
        "equations": ["9-9", "9-11", "9-24", "Figure 9-6"],
    },
}


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def csv_write(path, records):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


@cache
def torsion_faces(width, depth, gu_over_gv):
    """Closed rectangular Saint-Venant series, including aligned orthotropy.

    Phi_uu/G_Lv + Phi_vv/G_Lu = -2*twist. Put v'=s*v,
    s=sqrt(G_Lu/G_Lv); the isotropic rectangle is width by s*depth.
    T=2*integral(Phi) and shear=(Phi_v,-Phi_u). Coefficients below
    multiply signed T, giving shear at opposing face midpoints. This
    local section arithmetic supplies no altered beam/contact response.
    For gu=gv it evaluates the FPL rectangle coefficient without graph
    interpolation. The 200 odd terms are a fixed arithmetic truncation.
    """
    s = math.sqrt(gu_over_gv)
    w, h = width, s * depth
    b, d = sorted((w, h))
    odd = range(1, 400, 2)
    j = d * b**3 / 3 * (1 - 192 * b / (math.pi**5 * d)
        * sum(math.tanh(n * math.pi * d / (2*b)) / n**5 for n in odd))

    def face_factor(ratio):
        # Stable sech; avoid overflow on slender transformed rectangles.
        return 1 - 8/math.pi**2 * sum(
            2*math.exp(-n*math.pi*ratio/2)
            / (1+math.exp(-n*math.pi*ratio)) / n**2 for n in odd)

    return (s*s*h*face_factor(w/h)/j, s*w*face_factor(h/w)/j)


def shear_check(value, width, depth, fv, aligned, gu_over_gv):
    """Same-cut parabolic transverse shear plus compatible torsional shear.

    At u faces the transverse u component vanishes, and conversely at v
    faces. Opposing faces have opposite torsion signs; at least one adds
    to the signed transverse component. The component rectangle bound
    is a sufficient all-section check. Its exceedance alone is a sensitivity;
    a face exceedance is a failure of the declared prismatic strength screen.
    Fv is explicitly assumed applicable to both longitudinal shear components.
    No normal/shear strength interaction or torsional shape enhancement is added.
    """
    _n, vu, vv, torque, _mu, _mv = value
    area = width*depth
    cu, cv = torsion_faces(round(width,9), round(depth,9), gu_over_gv if aligned else 1.)
    su, sv = 1.5*abs(vu)/area, 1.5*abs(vv)/area
    tu, tv = abs(torque)*cu, abs(torque)*cv
    face_u, face_v = (su+tu)/fv, (sv+tv)/fv
    bound = math.hypot(su+tu, sv+tv)/fv
    iso = rectangular_shear(width, depth, vu, vv, torque)
    require(abs(iso["unreduced_asd_shear_reference_mpa"] - fv) < 1e-10,
            "reused torsion helper has another shear allowance")
    result = {
        "face_at_v_edge_ratio": face_u,
        "face_at_u_edge_ratio": face_v,
        "face_lower_bound_ratio": max(face_u, face_v),
        "component_rectangle_upper_bound_ratio": bound,
        "coefficient5_isotropic_sensitivity_ratio": iso["combined_shear_ratio"],
        "transverse_shear_u_v_max_mpa": [su, sv],
        "torsional_shear_u_v_max_mpa": [tu, tv],
        "torsion_coefficient_u_v_per_mm3": [cu, cv],
        "strength_allowance_mpa": fv,
        "stress_distribution": "aligned_source_longitudinal_orthotropy" if aligned
            else "equal_longitudinal_shear_moduli_rectangle_approximation",
        "disposition": "FACE_EXCEEDS_DECLARED_ALLOWANCE" if max(face_u, face_v) > 1
            else "RECTANGLE_BOUND_BELOW_ALLOWANCE" if bound <= 1
            else "CONSERVATIVE_COMPONENT_BOUND_EXCEEDS_ONLY",
    }
    if aligned:
        ru, rv = torsion_faces(round(width,9), round(depth,9), 1/gu_over_gv)
        result["RT_swap_fixed_action_face_ratio"] = max(
            (su+abs(torque)*ru)/fv, (sv+abs(torque)*rv)/fv)
    return result


def references(body, geometry, materials):
    binding = member.reference_values(body, geometry, materials)
    v = binding["CF_only_reference_mpa"]
    base = materials["conditional_DF_L_No2_base_row"]["base_properties"]
    return binding, {"Fb_star_mpa": v["Fb"], "Ft_mpa": v["Ft_parallel"],
        "Fc_star_mpa": v["Fc_parallel"], "Fv_mpa": v["Fv_parallel"],
        "Fc_perp_mpa": base["Fc_perpendicular"]*member.PSI_MPA,
        "Emin_mpa": base["Emin"]*member.PSI_MPA}


def stability_kernel(short, long, length, weak_length, ref):
    """Uniform minimum intact rectangle over the entire span is conservative.

    Bore sections and clipped terminal profiles are excluded from this
    approximation. No local-opening capacity is inferred. For the 1:12
    rear recess the minimum retained width is extended over the full span.
    """
    result = member_check(width_mm=short, depth_mm=long, axial_n=0,
        moment_strong_nmm=0, moment_weak_nmm=0, shear_strong_n=0,
        shear_weak_n=0, torsion_nmm=0, column_effective_strong_mm=length,
        column_effective_weak_mm=weak_length,
        beam_effective_mm=effective_beam_length(length, long), reference_override=ref)
    if abs(short-long) < 1e-6:
        result["CL"] = 1.
        result["adjusted_Fb_strong_mpa"] = ref["Fb_star_mpa"]
    return result


def normal_check(value, width, depth, kernel, ref):
    n, _vu, _vv, _torque, mu, mv = value
    area = width*depth
    fc, ft = max(-n, 0)/area, max(n, 0)/area
    fu, fv = 6*abs(mu)/(width*depth**2), 6*abs(mv)/(depth*width**2)
    fb1, fb2 = (fv, fu) if width > depth else (fu, fv)
    fce1, fce2 = kernel["FcE_strong_weak_mpa"]
    fbe = kernel["FbE_mpa"]
    d1 = 1-fc/fce1
    d2 = 1-fc/fce2-(fb1/fbe)**2
    stability = fc/fce2+(fb1/fbe)**2
    if n < 0:
        ratio = ((fc/kernel["adjusted_Fc_mpa"])**2
            + fb1/(kernel["adjusted_Fb_strong_mpa"]*d1)
            + fb2/(ref["Fb_star_mpa"]*d2)) if min(d1, d2) > 0 else None
        branch = "NDS_3_9_3_and_3_9_4"
    else:
        # Conservative biaxial extension: no tension relief to compression-edge
        # bending, and strong-axis CL applies to that independent bending check.
        ratio = max(ft/ref["Ft_mpa"]+(fb1+fb2)/ref["Fb_star_mpa"],
            fb1/kernel["adjusted_Fb_strong_mpa"]+fb2/ref["Fb_star_mpa"])
        branch = "NDS_3_9_1_plus_no_tension_relief_biaxial_bending"
    domain = kernel["beam_slenderness"] <= 50 and (
        n >= 0 or max(kernel["column_slenderness_strong_weak"]) <= 50+1e-9)
    return {"interaction_ratio": ratio, "branch": branch,
        "stability_3_9_4_ratio": stability, "Euler_denominators_positive": min(d1,d2)>0,
        "within_slenderness_limits": bool(domain),
        "stress_compression_tension_strong_weak_mpa": [fc, ft, fb1, fb2],
        "ratio_qualified_inside_declared_stability_domain": bool(domain and ratio is not None),
        "ratio_exceeds_one": ratio is None or ratio > 1 or stability >= 1}


def brace_candidates(body, record, arrays, rows, timber_bodies):
    """Existing timber bolt/bearing stations projected on weak dimension.

    A receiver is a candidate, not automatically a non-sway brace. Neither
    one-sided face contact alone nor panel attachment is credited. A tension
    tie needs its compression counterface in the same timber interface. The
    pair is assumed to provide restraint in both displacement senses; that
    requires the joint to take up opening slack and its receiver to be braced.
    Beam end rotation remains separate. These stations only shorten the weak
    effective column length in the second scenario.
    """
    g = record["geometry"]
    weak = np.array(g["section_u" if g["width_mm"] < g["depth_mm"] else "section_v"])
    counterfaces = {}
    for role, other, station, row in zip(record["point_action_roles"],
        record["point_action_other_bodies"], arrays[body+"__point_stations_mm"],
        arrays[body+"__point_rows"], strict=True):
        if row >= 0 and other in timber_bodies and role == "timber_or_panel_contact":
            source = rows[int(row)]
            projection = abs(float(weak @ source["ownership"]["direction_global_xyz"]))
            if source["law"]["intended_law"] == "compression_only" and projection > .1:
                counterfaces.setdefault(other,[]).append({"row":int(row),
                    "station_mm":float(station),"absolute_weak_direction_projection":projection})
    candidates = []
    for identity, role, other, station, row in zip(record["point_action_ids"],
        record["point_action_roles"], record["point_action_other_bodies"],
        arrays[body+"__point_stations_mm"], arrays[body+"__point_rows"], strict=True):
        if (row < 0 or other not in timber_bodies
            or role not in ("candidate_bolt_lateral_plane", "retained_bolt_lateral_plane",
                            "physical_bolt_outer_seat_tension")):
            continue
        source = rows[int(row)]
        law = source["law"]["intended_law"]
        if law != "bilateral" and not (law == "tension_only" and other in counterfaces):
            continue
        projection = abs(float(weak @ source["ownership"]["direction_global_xyz"]))
        if projection > .1:
            candidates.append({"station_mm": float(station), "receiver": other,
                "source_id": identity, "row": int(row),
                "absolute_weak_direction_projection": projection,
                "restraint_condition": "bilateral_lateral_plane_to_braced_receiver"
                    if law == "bilateral" else "tension_tie_plus_counterface_to_braced_receiver_no_opening_slack",
                "compression_counterface_rows":counterfaces.get(other,[])})
    return candidates


def peak(records, metric):
    values = [r for r in records if r[metric] is not None]
    return max(values, key=lambda r: r[metric]) if values else None


def run(output, clearance=RESPONSE, members=MEMBER, frame_directory=FRAME):
    require(output == OUTPUT or OUTPUT in output.parents, "output outside owned packet")
    require(not output.exists() or set(output.iterdir()) == {output/"preliminary-bilateral-only"},
            "preserve saved attempt; choose an owned child for new inputs")
    pins = dict(PINS)
    if frame_directory != FRAME:
        comparison = read(clearance / "comparison.json")
        require(comparison["frame_operator_directory"] == str(frame_directory.relative_to(ROOT)),
                "response has another operator directory")
        assessment = read(frame_directory / "operator-assessment.json")
        for name in ("model.json", "row-identities.json", "operators.npz"):
            pins.pop(FRAME / name)
            path = frame_directory / name
            expected = assessment["output_sha256"][name]
            require(comparison["source_sha256"][str(path.relative_to(ROOT))] == expected,
                    "response and physical operator assessment disagree")
            pins[path] = expected
        pins[frame_directory / "operator-assessment.json"] = sha(frame_directory / "operator-assessment.json")
    for path, digest in pins.items():
        require(sha(path) == digest, "changed consumed source: "+str(path))
    comparison_path, report_path = clearance/"comparison.json", members/"member-results.json"
    comparison, report = read(comparison_path), read(report_path)
    force_scope = frame_contract.force_state_scope(comparison)
    require(report.get("source_force_state_scope", force_scope) == force_scope,
            "member and frame force-state scopes differ")
    dynamic = {
        comparison_path: sha(comparison_path),
        clearance/"response.npz": comparison["response_sha256"],
        report_path: sha(report_path),
        **{members/name: report["output_sha256"][name] for name in
           ("geometry.json", "action-section-arrays.npz", "producer.py.snapshot")},
    }
    for path, digest in dynamic.items():
        require(path not in pins or pins[path] == digest, "conflicting fixed/input hash: "+str(path))
        pins[path] = digest
        require(sha(path) == digest, "changed response/member input: "+str(path))
    require(report["producer_sha256"] == pins[members/"producer.py.snapshot"],
            "saved member producer snapshot does not match report")
    packet, reference_geometry = read(members/"geometry.json"), read(GEOMETRY_REFERENCE)
    records, model, rows = packet["members"], read(frame_directory/"model.json"), read(frame_directory/"row-identities.json")
    expected_records = copy.deepcopy(reference_geometry["members"])
    pins.update(member.apply_screw_station_exclusions(expected_records, model))
    materials, frame_map = read(accounting.MATERIALS), read(FRAME_MAP)
    frame_bodies = {r["member_id"] for r in frame_map["members"]}
    require(len(frame_bodies) == 20 and len(records) == 44, "timber census changed")
    require(set(records) == set(reference_geometry["members"]), "fixed geometry census changed")
    require(tuple(c["case_id"] for c in report["cases"]) == CASES, "six-case census changed")
    require(all(c["source_force_key"] == c["case_id"]+"_gap_raw_force_n" for c in report["cases"]),
            "member packet has another force-state convention")
    require(report["clearance_input_directory"] == str(clearance.relative_to(ROOT)), "mixed responses")
    require(report["same_state_dead_load_factor"] == comparison["dead_load_factor"], "mixed dead loads")
    for path in (comparison_path, clearance/"response.npz", frame_directory/"model.json",
                 frame_directory/"row-identities.json", frame_directory/"operators.npz", accounting.MATERIALS, FRAME_MAP):
        digest = pins[path]
        key = str(path.relative_to(ROOT))
        require(report["source_sha256"].get(key) == digest, "saved actions have another source: "+key)
        if path.parent == frame_directory:
            require(comparison["source_sha256"].get(key) == digest, "response has another frame: "+key)
    for path in (Path(__file__), Path(bottom.__file__), Path(member.__file__),
        Path(accounting.__file__), Path(frame_contract.__file__), ROOT/"fea/reinforced_timber_resistance.py",
        ROOT/"scripts/floor_taper_checks.py", ROOT/"fea/current_response_materials.py",
        ROOT/"fea/wood_joint_patch_materials.py"):
        digest = sha(path)
        require(path not in pins or pins[path] == digest, "fixed helper hash changed: "+str(path))
        pins[path] = digest
    for body, record in records.items():
        frozen = expected_records[body]
        for key in ("member_kind", "geometry", "current_finished_step", "current_finished_step_sha256",
                    "original_finished_step_sha256", "profile_planes", "bore_or_passage_intervals",
                    "recess_source", "replaced_original_bore_features"):
            require(record.get(key) == frozen.get(key), "fixed member geometry changed: "+body+"/"+key)
        pins[ROOT/frozen["current_finished_step"]] = frozen["current_finished_step_sha256"]
        grain = model["material_binding"]["orientation_overrides"][body]["material_axes_global_xyz"]["L"]
        require(np.max(abs(np.array(grain)-record["geometry"]["axis"])) < 1e-8, "grain changed")
    for path, digest in pins.items():
        require(sha(path) == digest, "changed consumed geometry/helper: "+str(path))
    output.mkdir(parents=True,exist_ok=True)
    (output/"producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    states, balances, summaries = [], [], []
    with (np.load(members/"action-section-arrays.npz", allow_pickle=False) as arrays,
          np.load(clearance/"response.npz", allow_pickle=False) as responses,
          np.load(frame_directory/"operators.npz", allow_pickle=False) as operators):
        require(operators["D"].shape == (1888,300), "physical operator changed")
        for body in sorted(records, key=lambda b: (b not in frame_bodies,b)):
            record, g = records[body], records[body]["geometry"]
            length = float(np.linalg.norm(np.array(g["end"])-g["start"]))
            frame = member.basis(g)
            rectangles = record["rectangle_at_station"]
            intact = [r for r in rectangles if r["status"].startswith("BORE_FREE_")]
            binding, ref = references(body,g,materials)
            orientation = model["material_binding"]["orientation_overrides"][body]
            radial = np.array(orientation["material_axes_global_xyz"]["R"])
            radial_u = abs(float(radial@frame[1]))
            radial_v = abs(float(radial@frame[2]))
            aligned = max(radial_u,radial_v) > 1-1e-7
            # Both consumed source elastic categories have GLR/GLT=.064/.078.
            # The absolute elastic modulus cancels out of torsional stresses.
            gu_over_gv = .064/.078 if radial_u > radial_v else .078/.064
            if intact:
                dimensions = [sorted(r["width_depth_mm"]) for r in intact]
                short, long = map(float, np.min(dimensions,axis=0))
            else:
                short, long = sorted((g["width_mm"],g["depth_mm"]))
            candidates = brace_candidates(body,record,arrays,rows,set(records))
            stations = sorted({0.,length,*[c["station_mm"] for c in candidates]})
            weak_bay = max(b-a for a,b in pairwise(stations))
            kernels = {
                "end_supported_only": stability_kernel(short,long,length,length,ref),
                "existing_timber_weak_restraints": stability_kernel(short,long,length,weak_bay,ref),
            }
            body_states = []
            for case in CASES:
                raw = responses[case+"_gap_raw_force_n"]
                require(raw.shape == (1888,) and np.isfinite(raw).all(), "invalid raw force")
                actions = bottom.saved_actions(body,case,record,arrays)
                ids = model["body_nodes"][body]
                datum = np.mean([model["physical_node_coordinates_mm"][str(n)] for n in ids],axis=0)
                closure = accounting.wrench(actions,datum)
                require(max(abs(closure[:3])) < .1 and max(abs(closure[3:])) < 2, "body imbalance")
                body_index = model["body_names"].index(body)
                for action in actions:
                    if action["row"] < 0:
                        continue
                    expected = -operators["D"][action["row"],6*body_index:6*body_index+6]*raw[action["row"]]
                    actual = accounting.wrench([action],datum)
                    require(max(abs(actual[:3]-expected[:3])) < 1e-7
                        and max(abs(actual[3:]-expected[3:]*1000)) < 1e-5, "saved action/operator mismatch")
                balances.append({"case_id":case,"member":body,"residual_xyz_n_nmm":closure.tolist()})
                negative = arrays[case+"__"+body+"__internal_negative_grain_u_v"]
                positive = arrays[case+"__"+body+"__internal_positive_grain_u_v"]
                require(len(negative) == 2*len(rectangles), "cut station mismatch")
                require(np.max(abs(negative+positive)) < 1e-6, "opposite cut sides disagree")
                for index, value in enumerate(negative):
                    station = float(record["stations_mm"][index//2])
                    rectangle = rectangles[index//2]
                    supported = rectangle["status"].startswith("BORE_FREE_")
                    value = value.copy()
                    if supported:
                        w,d = rectangle["width_depth_mm"]
                        cut_datum = np.array(g["start"])+station*frame[0]
                        offset = frame@(np.array(rectangle["centroid_xyz_mm"])-cut_datum)
                        value[3:] -= np.cross(offset,value[:3])
                        normal = {s:normal_check(value,w,d,k,ref) for s,k in kernels.items()}
                        shear = shear_check(value,w,d,ref["Fv_mpa"],aligned,gu_over_gv)
                    else:
                        normal, shear = {}, {}
                    state = {"case_id":case,"member":body,"kind":"frame" if body in frame_bodies else "block",
                        "cut_array_index":index,"station_mm":station,"trace":"before" if index%2==0 else "after",
                        "cut_side":"negative_grain_half_N_tension_positive",
                        "section_status":rectangle["status"],"centroid_shift_applied":supported,
                        "N_n":float(value[0]),"Vu_n":float(value[1]),"Vv_n":float(value[2]),
                        "T_nmm":float(value[3]),"Mu_nmm":float(value[4]),"Mv_nmm":float(value[5]),
                        "width_mm":float(w) if supported else None,"depth_mm":float(d) if supported else None,
                        "end_only_normal_ratio":normal.get("end_supported_only",{}).get("interaction_ratio"),
                        "end_only_slenderness_ok":normal.get("end_supported_only",{}).get("within_slenderness_limits"),
                        "timber_braced_normal_ratio":normal.get("existing_timber_weak_restraints",{}).get("interaction_ratio"),
                        "timber_braced_slenderness_ok":normal.get("existing_timber_weak_restraints",{}).get("within_slenderness_limits"),
                        "timber_braced_stability_3_9_4":normal.get("existing_timber_weak_restraints",{}).get("stability_3_9_4_ratio"),
                        "shear_face_ratio":shear.get("face_lower_bound_ratio"),
                        "shear_component_bound_ratio":shear.get("component_rectangle_upper_bound_ratio"),
                        "coefficient5_sensitivity_ratio":shear.get("coefficient5_isotropic_sensitivity_ratio"),
                        "RT_swap_fixed_action_face_ratio":shear.get("RT_swap_fixed_action_face_ratio"),
                        "torsion_disposition":shear.get("disposition","NONRECTANGULAR_LOCAL_SECTION_SEPARATE"),
                    }
                    states.append(state)
                    body_states.append(state)
            screened = [r for r in body_states if r["shear_face_ratio"] is not None]
            compression = any(r["N_n"] < -1e-8 for r in body_states)
            # A single permitted effective length for weak-axis compression.
            # The 50*d limit is separate from a strength-ratio root.
            def acceptable(weak, *, short=short, long=long, length=length, ref=ref, screened=screened):
                k = stability_kernel(short,long,length,weak,ref)
                for state in screened:
                    value = [state[k] for k in ("N_n","Vu_n","Vv_n","T_nmm","Mu_nmm","Mv_nmm")]
                    c = normal_check(value,state["width_mm"],state["depth_mm"],k,ref)
                    if c["ratio_exceeds_one"] or not c["within_slenderness_limits"]:
                        return False
                return True
            maximum = min(length,50*short) if compression else length
            if screened and not acceptable(maximum):
                if acceptable(.001):
                    lo,hi = .001,maximum
                    for _ in range(48):
                        mid=(lo+hi)/2
                        if acceptable(mid):lo=mid
                        else:hi=mid
                    maximum=lo
                else:
                    maximum=None
            summary = {"member":body,"kind":"frame" if body in frame_bodies else "block",
                "source_geometry":g,"finished_step":record["current_finished_step"],
                "finished_step_sha256":record["current_finished_step_sha256"],
                "material_strength_binding":binding,"references":ref,"frozen_elastic_orientation":orientation,
                "torsion_stress_assumption": "aligned orthotropic Saint-Venant rectangle plus parabolic transverse shear"
                    if aligned else "FPL equal-shear-modulus stress approximation; header frozen R/T is rotated 50 degrees from u",
                "length_mm":length,"minimum_intact_rectangle_short_long_mm":[short,long],
                "source_bolt_weak_restraint_candidates":candidates,"maximum_candidate_weak_bay_mm":weak_bay,
                "has_signed_axial_compression":compression,
                "maximum_permitted_weak_effective_length_mm":maximum,
                "weak_length_requirement_governed_by":"NDS_3_7_1_4_50_times_short_dimension"
                    if maximum is not None and compression and abs(maximum-50*short)<1e-5
                    else "same_cut_interaction" if maximum is None or maximum < min(length,50*short)-1e-5
                    else "entire_member_length_permitted",
                "stability_kernels":kernels,
                "section_status_trace_counts":dict(Counter(r["section_status"] for r in body_states)),
                "torsion_disposition_trace_counts":dict(Counter(r["torsion_disposition"] for r in body_states)),
                "end_only_normal_peak":peak(screened,"end_only_normal_ratio"),
                "timber_braced_normal_peak":peak(screened,"timber_braced_normal_ratio"),
                "shear_face_peak":peak(screened,"shear_face_ratio"),
                "shear_component_bound_peak":peak(screened,"shear_component_bound_ratio"),
                "coefficient5_sensitivity_peak":peak(screened,"coefficient5_sensitivity_ratio"),
                "maximum_abs_signed_torque_cut":max(body_states,key=lambda r:abs(r["T_nmm"])),
                "minimum_signed_axial_n":min(r["N_n"] for r in body_states),
                "all_bore_free_braced_normal_checks_below_one": bool(screened) and all(
                    r["timber_braced_normal_ratio"] is not None and r["timber_braced_normal_ratio"] <= 1
                    and r["timber_braced_stability_3_9_4"] < 1 and r["timber_braced_slenderness_ok"] for r in screened),
                "whole_member_or_local_opening_qualification":False,
            }
            summaries.append(summary)
    csv_write(output/"same-cut-states.csv",states)
    write(output/"body-balances.json",balances)
    require(all(sha(p)==h for p,h in pins.items()),"source changed during arithmetic")
    screened = [r for r in states if r["shear_face_ratio"] is not None]
    if any(r["shear_face_ratio"] > 1 for r in screened):
        status = "FINITE_CONDITIONAL_MEMBER_SCREEN_WITH_PRISM_SHEAR_EXCESS"
    elif any(m["shear_face_peak"] is not None and not m["all_bore_free_braced_normal_checks_below_one"]
             for m in summaries):
        status = "FINITE_CONDITIONAL_MEMBER_SCREEN_WITH_NORMAL_OR_RESTRAINT_EXCEPTION"
    elif any(r["shear_component_bound_ratio"] > 1 for r in screened):
        status = "FINITE_CONDITIONAL_MEMBER_SCREEN_WITH_COMPONENT_BOUND_SENSITIVITY"
    else:
        status = "FINITE_CONDITIONAL_MEMBER_SCREEN_BELOW_DECLARED_ALLOWANCES"
    result = {
        "schema":"wood_joint_member_stability/v1","candidate":model["candidate"],
        "status":status,"producer_sha256":pins[Path(__file__)],
        "clearance_input_directory":str(clearance.relative_to(ROOT)),
        "member_input_directory":str(members.relative_to(ROOT)),
        "frame_operator_directory":str(frame_directory.relative_to(ROOT)),
        "source_comparison_sha256":pins[comparison_path],
        "source_response_sha256":pins[clearance/"response.npz"],
        "source_member_results_sha256":pins[report_path],
        "source_force_scope":force_scope,"same_state_dead_load_factor":comparison["dead_load_factor"],
        "source_sha256":{str(p.relative_to(ROOT)):h for p,h in sorted(pins.items())},
        "primary_sources":PRIMARY,"case_ids":CASES,"source_force_key":"case_id + '_gap_raw_force_n'",
        "counts":{"frame_members":20,"blocks":24,"body_case_balances":len(balances),
            "signed_cut_traces":len(states),"bore_free_signed_cut_traces":len(screened)},
        "restraint_assumptions":{
            "end_supported_only":"Both ends restrained in lateral translation in both section directions; no sway, K=1; end rotation about grain prevented. Actual start-to-end length is conservatively used as span. No panel or intermediate restraint credit.",
            "existing_timber_weak_restraints":"Same end conditions; enumerated timber bolt stations lead to receivers restrained against weak-direction translation. Where the source uses tension-only ties, the corresponding timber compression face must supply the opposite sense and opening slack must be taken up. K=1 in each weak bay; strong-column and beam lengths remain full span. These are declared brace duties, not stiffness/capacity proof from row existence.",
            "reduced_profile":"Uniform minimum bore-free rectangular section over the entire span, including the 1:12 rear recess; holes and terminal profiles remain separate local-section duties.",
            "torsion_strength":"Both longitudinal shear components use the unchanged 180 psi Fv, CD=1, no torsional enhancement; free warping and no concentration factor in an intact prism. This is an explicit engineering screen, not an NDS-listed torsion resistance.",
        },
        "members":summaries,
        "global_bore_free_peaks":{k:peak(screened,k) for k in ("end_only_normal_ratio",
            "timber_braced_normal_ratio","shear_face_ratio","shear_component_bound_ratio",
            "coefficient5_sensitivity_ratio")},
        "source_acceptance_transferred":False,"panel_stiffness_or_sharing_evaluated":False,
        "native_launch":False,"frame_solve":False,"CAD_rebuilt":False,"tests_run":False,
        "review_run":False,"formal_torsion_qualification":False,"physical_release":False,
        "output_sha256":{p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()},
    }
    write(output/"checks.json",result)
    print(json.dumps({"output":str(output.relative_to(ROOT)),"status":status,"counts":result["counts"],
        "peaks":{k:{a:v[a] for a in ("member","case_id","station_mm",k)}
            for k,v in result["global_bore_free_peaks"].items()}},indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=OUTPUT)
    parser.add_argument("--clearance",type=Path,default=RESPONSE,
                        help="Saved frame comparison/response directory; defaults to the original all-outer packet")
    parser.add_argument("--members",type=Path,default=MEMBER,
                        help="Saved member actions/sections directory matching --clearance; defaults to all-outer")
    parser.add_argument("--frame",type=Path,default=FRAME,
                        help="physical operator directory matching the selected force and member packets")
    args=parser.parse_args()
    run(args.output.resolve(), args.clearance.resolve(), args.members.resolve(), args.frame.resolve())
