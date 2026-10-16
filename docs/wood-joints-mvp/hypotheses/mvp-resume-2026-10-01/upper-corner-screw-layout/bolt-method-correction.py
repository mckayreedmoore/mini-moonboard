"""Correct catalog top-side bolt references without overwriting frozen results.

This postprocessor preserves each saved simultaneous action. A new diameter
reference is not a changed-clearance/stiffness frame response or a fit pass.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SCALAR = HERE / "rawlocal/joint-frame-bolt-reference/profile-attempt01/scalar-bolts.jsonl"
SCALAR_SHA = "b5954ea303eeb118c74bf0adfecb953ca8c5bc412ddc29f8af5bf7de54fb1cf1"
HARDWARE = HERE.parent / "assembly-package/hardware-engagement.md"
GRADE8_REMEDY_AXES = frozenset({
    "rail_front_bolt_left_1", "rail_front_bolt_left_2",
    "rail_front_bolt_right_1", "rail_front_bolt_right_2",
    "bottom_outer/clip_horizontal_bottom_left_1/side_1",
    "bottom_outer/clip_horizontal_bottom_left_1/side_2",
})


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def references():
    binding = module(HERE / "joint-frame-bolt-reference.py", "corrected_bolt_binding")
    for path in (binding.LATERAL, binding.PURE_LOADER, binding.TOP, binding.NDS,
                 ROOT / "fea/dowel_yield.py"):
        if sha(path) != binding.PINS[path]:
            raise ValueError("Changed reference helper: " + str(path))
    lateral = binding.module(binding.LATERAL, "corrected_bolt_lateral")
    loader = binding.module(binding.PURE_LOADER, "corrected_bolt_loader")
    top = loader.pure_functions(binding.TOP, ("lateral_reference",),
        {"math": math, "correction": SimpleNamespace(lateral=lateral)})
    return binding, top


def correct(rows, top, diameter_mm=7.9375, bending_yield_psi=130000.):
    """Return references for caller-supplied, authenticated same-state rows."""
    fields = []
    for row in rows:
        selected = (row["lateral_reference_method"] == "EXISTING_TOP_DIAMETER_DEPENDENT_Fe"
                    and "/side_" in row["axis_id"])
        if selected:
            grains = [(math.cos(math.radians(a)), math.sin(math.radians(a)), 0.)
                      for a in row["grain_angles_degrees"]]
            reference = top.lateral_reference((1., 0., 0.), diameter_mm,
                row["source_bearing_lengths_mm"], grains, bending_yield_psi)
            capacity = reference["reference_n"] * row["duration_factor"]
            mode = reference["governing_mode"]
        else:
            capacity = (row["lateral_reference_n"] * row["duration_factor"]
                        if row["lateral_reference_n"] is not None else None)
            mode = None
        fields.append({"axis_id": row["axis_id"], "state_tag": row["state_tag"],
            "demand_n": row["V_n"], "reference_n": capacity,
            "index": row["V_n"] / capacity if capacity is not None else None,
            "top_side_corrected": selected, "governing_mode": mode,
            "duration_factor": row["duration_factor"]})
    return fields


def summary(fields):
    finite = [r for r in fields if r["index"] is not None]
    return {"finite_fields": len(finite), "method_limits": len(fields)-len(finite),
        "exceedance_count": sum(r["index"] > 1. for r in finite),
        "peak": max(finite, key=lambda r:r["index"]) if finite else None}


def build(output):
    output = Path(output).resolve()
    if output.exists() or not output.is_relative_to((HERE / "rawlocal").resolve()):
        raise ValueError("Fresh ignored output below this packet's rawlocal required")
    if sha(SCALAR) != SCALAR_SHA:
        raise ValueError("Saved scalar action/reference source changed")
    binding, top = references()
    paths = [Path(__file__), SCALAR, HARDWARE, HERE / "joint-frame-bolt-reference.py",
             binding.LATERAL, binding.PURE_LOADER, binding.TOP, binding.NDS,
             ROOT / "fea/dowel_yield.py", binding.OPERATORS / "model-inputs.json"]
    pins = {p:sha(p) for p in paths}
    if pins[binding.OPERATORS / "model-inputs.json"] != binding.PINS[binding.OPERATORS / "model-inputs.json"]:
        raise ValueError("Reviewed bore source changed")
    text = HARDWARE.read_text()
    if "28650" not in text or "Grade 8" not in text:
        raise ValueError("Grade 8 top-side catalog route not found")
    rows = [json.loads(s) for s in SCALAR.read_text().splitlines()]
    reproduced = correct(rows, top, 6.35, 92000.)
    error = max(abs(r["index"]-s["lateral_reference_index"])
                for r,s in zip(reproduced,rows,strict=True) if r["index"] is not None)
    if len(rows) != 1200 or error > 1e-12:
        raise ValueError("Original comparison reproduction failed")
    corrected = correct(rows, top)
    top_fields = [r for r in corrected if r["top_side_corrected"]]
    if len(top_fields) != 48:
        raise ValueError("Top-side state census changed")
    identities = {r["axis_id"] for r in top_fields}
    model = json.loads((binding.OPERATORS / "model-inputs.json").read_text())
    fits = [{"axis_id":c["axis_id"], "receiver_id":g["receiver_id"],
        "reviewed_bore_diameter_mm":2*g["unique_bore_radius_mm"],
        "catalog_nominal_shaft_mm":7.9375,
        "nominal_radial_clearance_mm":g["unique_bore_radius_mm"]-7.9375/2,
        "catalog_shaft_fits_reviewed_bore":2*g["unique_bore_radius_mm"] >= 7.9375}
        for c in model["connections"] if c["axis_id"] in identities
        for g in c["receiver_clearance_geometry"]]
    result = {"schema":"bolt_catalog_method_correction/v1",
        "scope":"same_saved_simultaneous_actions_reference_correction",
        "reported_catalog_basis":{"diameter_mm":7.9375,"catalog_grade":"SAE J429 Grade 8",
            "conditional_Fyb_psi":130000.,"Fyb_basis":"Published minimum tensile yield, NDS 12.3.6.2 route",
            "part_url":"https://boltdepot.com/Product-Details?product=28650",
            "property_url":"https://crafter.fastenal.com/static-assets/pdfs/Mechanical_Properties_of_Inch_Fasteners.pdf"},
        "source_sha256":{p.relative_to(ROOT).as_posix():h for p,h in pins.items()},
        "known_answer":{"original_reference_maximum_absolute_error":error,
            "original":summary(reproduced)},
        "corrected_all_scalar_states":summary(corrected),"corrected_top_side":summary(top_fields),
        "top_side_bore_fit":fits,"fields":corrected,
        "limits":["Keeps saved force fields, grain angles, bearing lengths and duration factors.",
            "The catalog-grade source is conditional; delivered hardware and smooth bearing lengths remain unobserved.",
            "A nominal shaft larger than the reviewed bore requires a reported geometry correction before an updated physical frame model.",
            "No changed-diameter stiffness, clearance, thread bearing, edge/group, washer or full joint acceptance is inferred."],
        "frame_solve_run":False,"reviewed_geometry_changed":False,"physical_release":False,
        "complete_joint_acceptance":False}
    if any(sha(p)!=h for p,h in pins.items()):
        raise ValueError("A source changed during postprocessing")
    output.mkdir(parents=True)
    (output/".gitignore").write_text("*\n")
    (output/"producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    (output/"result.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"output":str(output.relative_to(ROOT)),"sha256":sha(output/"result.json"),
        "corrected_all":result["corrected_all_scalar_states"],
        "corrected_top":result["corrected_top_side"],
        "nonfitting_bores":sum(not r["catalog_shaft_fits_reviewed_bore"] for r in fits)},indent=2))
    return result


def horizontal(output,source,grade8_residual=False):
    """Recover scalar forces and their signed grain-dependent references anew."""
    import numpy as np
    source,output=Path(source).resolve(),Path(output).resolve()
    if output.exists() or not output.is_relative_to((HERE/"rawlocal").resolve()):
        raise ValueError("Fresh ignored output required")
    receipt=json.loads((source/"receipt.json").read_text())
    for name in ("comparison.json","response.npz"):
        if sha(source/name)!=receipt["output_sha256"][name]:
            raise ValueError("Horizontal response differs from receipt")
    if sha(SCALAR)!=SCALAR_SHA:
        raise ValueError("Original scalar geometry binding changed")
    binding,top=references()
    for path in (binding.OPERATORS/"model-inputs.json",binding.OPERATORS/"row-identities.json"):
        if sha(path)!=binding.PINS[path]:
            raise ValueError("Current scalar geometry/rows changed")
    lateral=module(binding.LATERAL,"horizontal_bolt_lateral")
    nds=module(binding.NDS,"horizontal_bolt_nds")
    model=json.loads((binding.OPERATORS/"model-inputs.json").read_text())
    members={m["member_id"]:m["reduced_geometry_descriptor"] for m in model["members"] if m["member_kind"]!="panel"}
    mapping_path=HERE/"rawlocal/joint-frame-action-reconciliation/profile-attempt01/source-row-map.json"
    if sha(mapping_path)!="f9ae9865e80ea95db9dccd6e6cd484ce60c6bb3aa6f617ec4387e346c55a5b8d":
        raise ValueError("Canonical force map changed")
    mapping=json.loads(mapping_path.read_text())["kept_map"]
    available={i for item in mapping for i in item["raw_rows"]}
    templates=[json.loads(s) for s in SCALAR.read_text().splitlines()]
    states=json.loads((source/"comparison.json").read_text())["states"]
    raw_forces={}
    with np.load(source/"response.npz",allow_pickle=False) as response:
        for state in states:
            tag=state["state_tag"]
            if not state["audit"]["all_passed"]:
                raise ValueError("Unaudited source field")
            f=response[tag+"_force"]
            raw=np.zeros(1888)
            for item in mapping:
                raw[item["raw_rows"]]=np.asarray(item["weights"])*f[item["kept_position"]]
            raw_forces[tag]=raw
    rows=[]
    canonical=json.loads((binding.OPERATORS/"row-identities.json").read_text())
    for template in templates:
        tag=template["state_tag"]
        if tag not in raw_forces:
            continue
        force=raw_forces[tag]
        indices=template["source_rows"]
        if any(i not in available for i in indices):
            raise ValueError("A replaced continuous-shaft placeholder entered a scalar comparison")
        components=force[indices[:2]]
        basis=np.asarray([canonical[i]["ownership"]["direction_global_xyz"] for i in indices[:2]])
        vector=components@basis
        grains=[np.asarray(members[m]["axis"],dtype=float) for m in template["receivers"]]
        grains=[g/np.linalg.norm(g) for g in grains]
        angles=[lateral.angle(vector,g) for g in grains]
        method=template["lateral_reference_method"]
        diameter=template["source_diameter_mm"]
        lengths=template["source_bearing_lengths_mm"]
        Fyb=130000. if grade8_residual and template["axis_id"] in GRADE8_REMEDY_AXES else 92000.
        reference=None
        if method=="EXISTING_RETAINED_PRIMARY_NDS":
            receiving=[{"bearing_length_in":length/25.4,"fe_theta_psi":nds._fe_theta_psi(
                specific_gravity=.5,diameter_in=diameter/25.4,angle_degrees=angle)}
                for length,angle in zip(lengths,angles,strict=True)]
            modes=nds._single_shear_modes(*receiving,diameter/25.4,Fyb,nds._reduction_terms(
                diameter_in=diameter/25.4,nominal_diameter_in=diameter/25.4,angle_max_degrees=max(angles)))
            reference=min(modes.values())*binding.N_PER_LBF
        elif method=="EXISTING_CANDIDATE_ROUNDED_Fe":
            reference=lateral.reference(lengths,angles,Fyb)["reference_lateral_lbf"]*binding.N_PER_LBF
        elif method=="EXISTING_TOP_DIAMETER_DEPENDENT_Fe":
            reference=top.lateral_reference(vector,diameter,lengths,grains,Fyb)["reference_n"]
        elif method=="EXISTING_Ceg_0p67_SINGLE_SHEAR_REFERENCE":
            main=next(i for i,m in enumerate(template["receivers"]) if m!="base_header")
            header=template["receivers"].index("base_header")
            reference=.67*lateral.reference([lengths[main],lengths[header]],[90.,angles[header]],Fyb)["reference_lateral_lbf"]*binding.N_PER_LBF
        elif method is not None:
            raise ValueError("Unrecognized scalar reference method")
        cd=template["duration_factor"]
        rows.append({**template,"V_n":float(np.linalg.norm(vector)),"signed_T_n":float(force[indices[2]]),
            "lateral_components_n":components.tolist(),"signed_sourceD_lateral_vector_xyz_n":vector.tolist(),
            "grain_angles_degrees":angles,"lateral_reference_n":reference,
            "lateral_reference_index":float(np.linalg.norm(vector))/(reference*cd) if reference else None,
            "residual_Grade8_reference_proposed":grade8_residual and template["axis_id"] in GRADE8_REMEDY_AXES,
            "source_direct_steel_and_washer_checks_not_recomputed":True})
    if len(rows)!=100*len(states):
        raise ValueError("Current scalar force census incomplete")
    corrected=correct(rows,top)
    if grade8_residual and {r["axis_id"] for r in rows if r["residual_Grade8_reference_proposed"]} != GRADE8_REMEDY_AXES:
        raise ValueError("Proposed Grade8 six-axis census differs")
    paths=(Path(__file__),SCALAR,mapping_path,binding.OPERATORS/"model-inputs.json",
        binding.OPERATORS/"row-identities.json",source/"receipt.json",source/"comparison.json",source/"response.npz",
        binding.LATERAL,binding.PURE_LOADER,binding.TOP,binding.NDS,ROOT/"fea/dowel_yield.py",HARDWARE)
    pins={str(p.relative_to(ROOT)):sha(p) for p in paths}
    result={"schema":"horizontal_bolt_catalog_reference_correction/v1",
        "force_basis":str(source.relative_to(ROOT)),"accepted_states":len(states),
        "residual_Grade8_proposal":{"enabled":grade8_residual,
            "axis_ids":sorted(GRADE8_REMEDY_AXES) if grade8_residual else [],
            "conditional_Fyb_psi":130000. if grade8_residual else None,
            "diameters_and_elastic_laws_changed":False,
            "catalog_profile_and_delivered_thread_windows_qualified":False,
            "property_source":"https://crafter.fastenal.com/static-assets/pdfs/Mechanical_Properties_of_Inch_Fasteners.pdf",
            "limit":"Yield-reference remedy only; nominal smooth diameters, bearing lengths and elastic forces retained. Complete steel/washer/joint and delivered profile checks remain separate."},
        "all_scalar_states":summary(corrected),"top_side":summary([r for r in corrected if r["top_side_corrected"]]),
        "fields":corrected,"source_sha256":pins,"changed_diameter_force_feedback_evaluated":False,
        "catalog_top_side_basis":{"diameter_mm":7.9375,"grade":"SAE J429 Grade8",
            "conditional_Fyb_psi":130000.,"source":"https://boltdepot.com/Product-Details?product=28650",
            "yield_route":"NDS12.3.6.2 with published minimum tensile yield; delivery conformance unobserved"},
        "reviewed_bores_still_incompatible_with_top_side_catalog_shaft":True,
        "complete_joint_acceptance":False,"physical_release":False}
    if any(sha(ROOT/p)!=h for p,h in pins.items()):
        raise ValueError("A source changed during the current scalar comparison")
    output.mkdir(parents=True)
    (output/".gitignore").write_text("*\n")
    (output/"producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    (output/"result.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"all":result["all_scalar_states"],"top":result["top_side"],"sha256":sha(output/"result.json")},indent=2),flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--horizontal-source",type=Path)
    parser.add_argument("--grade8-residual",action="store_true",
        help="Unadopted same-diameter Grade8 reference on four front and two bottom-left side axes")
    args = parser.parse_args()
    sys.path[:0]=[str(ROOT),str(HERE.parent)]
    if args.horizontal_source:
        horizontal(args.output,args.horizontal_source,args.grade8_residual)
    else:
        if args.grade8_residual:
            parser.error("--grade8-residual requires --horizontal-source")
        build(args.output)
