"""Current-demand NDS beam-connection components using frozen physical geometry.

The older connection inventory supplies only geometry and source row identities.
Every force, shear cut and loaded-edge sign is taken from the current profile.
Sampled net-section singularities and complete-joint resistance stay separate.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OLD = HERE / "rawlocal/beam-connection-shear-completion/attempt01/group-case-states.jsonl"
CUTS = HERE / "rawlocal/member-opening-general-completion/washer-updated-complete-attempt02/cuts.jsonl.gz"
ACTIONS = HERE / "rawlocal/joint-frame-action-reconciliation/profile-attempt01/body-actions.jsonl.gz"
GEOMETRY = HERE / "all-joint-splitting/rawlocal/splitting-capacity-completion/coupled-prepared01/geometry.json"
CHAPTER = HERE / "rawlocal/profile-method-completion/sources/nds2024-chapter3.pdf"
FORCE_HASH = "0a262d5933367be8a6ba98efde200048af67e6005dc6134ffbccb3332d0be34a"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capacity(fv, breadth, depth, effective, branch):
    return (2./3.) * fv * breadth * effective * ((effective/depth)**2 if branch=="near" else 1.)


def read_lines(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path,"rt") as stream:
        for line in stream:
            yield json.loads(line)


def same_geometry(left,right):
    if isinstance(left,(int,float)) and isinstance(right,(int,float)):
        return math.isclose(left,right,rel_tol=1e-12,abs_tol=1e-7)
    if isinstance(left,dict) and isinstance(right,dict):
        return left.keys()==right.keys() and all(same_geometry(left[k],right[k]) for k in left)
    if isinstance(left,list) and isinstance(right,list):
        return len(left)==len(right) and all(same_geometry(a,b) for a,b in zip(left,right,strict=True))
    return left==right


def build(output):
    output = Path(output).resolve()
    if output.exists() or not output.is_relative_to((HERE/"rawlocal").resolve()):
        raise ValueError("Fresh ignored output required")
    paths=[Path(__file__),OLD,CUTS,ACTIONS,GEOMETRY,CHAPTER,HERE/"beam-connection-shear-completion.py"]
    pins={p:sha(p) for p in paths}
    templates={}
    old_error=0.
    for row in read_lines(OLD):
        identity=row["join_id"]
        if identity in templates and not same_geometry(row["geometry"],templates[identity]["geometry"]):
            raise ValueError("Frozen physical group geometry varies between cases")
        templates[identity]=row
        for comparison in row["primary_component_comparisons"]:
            for scenario in comparison["scenarios"].values():
                if scenario["Vr_prime_n"] is not None:
                    ref=capacity(scenario["Fv_mpa"],comparison["b_mm"],comparison["d_mm"],
                                 comparison["de_mm"],comparison["branch"])
                    old_error=max(old_error,abs(ref-scenario["Vr_prime_n"])/ref)
    if len(templates)!=58 or old_error>1e-12:
        raise ValueError("Original connection geometry/formula reproduction failed")
    geometry=json.loads(GEOMETRY.read_text())
    actions={}
    for row in read_lines(ACTIONS):
        if row["source_state_record"]["sha256"] != FORCE_HASH:
            raise ValueError("Different current action force basis")
        actions[row["body"],row["state_tag"]]=row
    cuts=defaultdict(list)
    terminal_counts={"normal":0,"shear":0}
    residual_counts={"normal":0,"shear":0}
    for row in read_lines(CUTS):
        if row["source_state_record"]["sha256"] != FORCE_HASH:
            raise ValueError("Different current cut force basis")
        if "normal" not in row:
            continue
        cuts[row["body"],row["state_tag"]].append(row)
        counts=terminal_counts if row["normal"]["properties"]["area_mm2"]<=1. else residual_counts
        counts["normal"]+=row["normal"]["normal_reference_sum"]>1.
        counts["shear"]+=row["elastic_shear"]["peak_reference_ratio"]>1.
    fields=[]
    for template in templates.values():
        body,g=template["body"],template["geometry"]
        component=template["primary_component_comparisons"][0]["component"]
        index=1 if component=="u" else 2
        depth_axis=g["depth_axis_global_xyz"]
        if max(abs(a-b) for a,b in zip(depth_axis,geometry[body]["frame"][index],strict=True))>1e-7:
            raise ValueError("Current section component frame differs from physical beam plane")
        for (candidate,tag),action_record in actions.items():
            if candidate!=body:
                continue
            by_row={a["row"]:a for a in action_record["actions"]
                    if isinstance(a["row"],int) and a["row"]>=0}
            row_ids=template["loading"]["group_force_row_ids"]
            missing=[r for r in row_ids if r not in by_row or not by_row[r].get("source_force_available",True)]
            own={"join_id":template["join_id"],"body":body,"state_tag":tag,
                "component":component,"reference_role":"NDS_TRANSVERSE_COMPONENT_ONLY",
                "complete_joint_acceptance":False}
            if missing:
                fields.append({**own,"index":None,"limit":"REPLACED_CONTINUOUS_SHAFT_ROWS_REQUIRE_NEW_GROUP_ALLOCATION","rows":missing})
                continue
            planes=[]
            for plane in template["loading"]["global_lateral_planes"]:
                force=[sum(by_row[r]["force_n"][k] for r in plane["component_rows"]) for k in range(3)]
                planes.append(sum(a*b for a,b in zip(force,depth_axis,strict=True)))
            signs=sorted({1 if v>0 else -1 for v in planes if abs(v)>1e-8})
            stations=[by_row[r]["station_mm"] for r in row_ids]
            lo,hi=min(stations),max(stations)
            selected=[r for r in cuts[body,tag] if lo-1e-5<=r["station_mm"]<=hi+1e-5]
            if not selected:
                fields.append({**own,"index":None,"limit":"NO_CURRENT_FINITE_CUTS_ACROSS_GROUP"})
                continue
            witness=max(selected,key=lambda r:abs(r["full_signed_wrench_n_nmm"][index]))
            fv=witness["references_mpa"]["Fv_parallel"]
            shear=abs(witness["full_signed_wrench_n_nmm"][index])
            if not g["NDS_rectangle_component_established"]:
                fields.append({**own,"index":None,"demand_n":shear,"limit":g["geometry_guard"]})
                continue
            for sign in signs if len(signs)==1 else (-1,1):
                de=g["de_by_loaded_edge_mm"][str(sign)]
                if not 0.<de<=g["d_mm"]+1e-5:
                    raise ValueError("Invalid effective depth")
                ref=capacity(fv,g["b_mm"],g["d_mm"],de,g["branch"])
                fields.append({**own,"index":shear/ref,"reference_n":ref,"demand_n":shear,
                    "duration_CD":witness["duration_CD"],"Fv_mpa":fv,"b_mm":g["b_mm"],
                    "d_mm":g["d_mm"],"de_mm":de,"branch":g["branch"],
                    "equation":"3.4-6" if g["branch"]=="near" else "3.4-7",
                    "loaded_edge_sign":sign,"unique_loaded_edge_established":len(signs)==1,
                    "same_state_plane_depth_forces_n":planes,"finite_cut_count":len(selected),
                    "cut_witness":{"station_mm":witness["station_mm"],"limit":witness["limit"],
                        "signed_N_Vu_Vv_T_Mu_Mv":witness["full_signed_wrench_n_nmm"]},
                    "remaining_duties":"Associated axial forces, other transverse component, couples, loaded-edge/group and splitting behavior are separate."})
    finite=[r for r in fields if r["index"] is not None]
    unique=[r for r in finite if r["unique_loaded_edge_established"]]
    result={"schema":"current_member_connection_method_correction/v1",
        "scope":"fresh_current_profile_demands_with_frozen_NDS_beam_component_geometry",
        "source_sha256":{p.relative_to(ROOT).as_posix():h for p,h in pins.items()},
        "known_answer":{"old_capacity_maximum_relative_error":old_error,"physical_groups":len(templates)},
        "source_terminal_separator_mm2":1.,"source_terminal_counts":terminal_counts,
        "source_remaining_counts":residual_counts,"terminal_separator_is_design_cutoff":False,
        "finite_comparisons":len(finite),"explicit_method_limits":len(fields)-len(finite),
        "unique_loaded_edge_comparisons":len(unique),
        "unique_loaded_edge_exceedances":sum(r["index"]>1. for r in unique),
        "unique_loaded_edge_peak":max(unique,key=lambda r:r["index"]) if unique else None,
        "both_edge_sensitivity_peak":max(finite,key=lambda r:r["index"]) if finite else None,
        "fields":fields,"native_or_frame_solve":False,"reviewed_geometry_changed":False,
        "complete_member_acceptance":False,"complete_joint_acceptance":False,"physical_release":False,
        "limits":["Uses maximum current finite before/after shear across each complete source group interval.",
            "Opposing or zero transverse bolt actions retain both hypothetical edges without choosing an actual unloaded edge.",
            "Trimmed/nonprismatic profiles and replaced continuous-shaft rows retain explicit method limits.",
            "This component equation does not replace unconverged hole/torsion peaks with an average or establish complete resistance.",
            "The small-area census diagnoses terminal sections; no arbitrary area-based stress acceptance is introduced."]}
    if any(sha(p)!=h for p,h in pins.items()):
        raise ValueError("Source changed during correction")
    output.mkdir(parents=True)
    (output/".gitignore").write_text("*\n")
    (output/"producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    (output/"result.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("fields","source_sha256","limits")},indent=2))
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    build(parser.parse_args().output)
