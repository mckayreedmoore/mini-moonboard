"""Saved-force bearing means for accepted coupled states; no equation solve.

Preparation authenticates source geometry/material joins without reading array
values. Parent build performs scalar arithmetic on an exact action receipt.
The frozen action adapter and every prior result remain unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/joint-frame-action-reconciliation"
CONTACT = HERE / "rawlocal/contact-bearing-completion/attempt02"
WASHER = HERE / "rawlocal/washer-reference-completion/attempt02"
MATERIAL = HERE.parent.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
PSI_MPA = .006894757293168361
PINS = {
    HERE / "contact-bearing-completion.py": "4c1240a296f764d2565edf219e2a5aa1b0fae25958840f7cc64a610662bee1ee",
    HERE / "receiver-bearing-completion.py": "767da34553071c946b9f0ea88047bb1dedf83b7034cdb47e4945382cb50de8b4",
    HERE / "washer-reference-completion.py": "8746aed9bba5c8a1a897bb1bbf60a14ecd3f0928a760803ca05a309231a3575a",
    CONTACT / "receipt.json": "7e7fdf6195f1611dcf4b020e75cd6ec9c99b04a09e58bdb7631e9e7d51aae326",
    CONTACT / "geometry-inventory.json": "68b421d5d8b16579fbbd5214167830cc0376163e629fcec7a2f407efcf0d1db3",
    WASHER / "receipt.json": "fceaeb1c3d2a2f4d6e23ec1beb19e48ad40e8ab1a2eac1d50b5d39b7af4acac2",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
}
FLAGS = {key:False for key in ("complete_joint_acceptance","physical_release","fabrication_release",
    "numerical_goal_complete","geometry_changed","force_repaired","native_CAD_or_frame_solve_executed",
    "washer_metal_stress_qualified","actual_pressure_patch_qualified")}


def require(value, message):
    if not value:
        raise ValueError("STOP: "+message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value,separators=(",",":"),allow_nan=False)+"\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name,path)
    result = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(result)
    finally:
        sys.dont_write_bytecode = previous
    return result


def frozen_inputs(actions, receipt_digest):
    """Reuse geometry-only helpers; do not call any producer build/prepare."""
    adapter = module(HERE/"joint-frame-action-reconciliation.py","mean_frozen_action_adapter")
    actions = Path(actions).resolve()
    require(actions.parent == RAW.resolve() and sha(actions/"receipt.json") == receipt_digest,
            "exact owned action receipt required")
    action_inputs, action_summary = read(actions/"inputs.json"), read(actions/"summary.json")
    preparation, reduction, response = [ROOT/action_inputs[key] for key in ("preparation","wood_reduction","response")]
    api, pins, request = adapter.sources(preparation,reduction,response)
    for path,digest in PINS.items():
        api.bind(pins,path,digest)
    api.bind(pins,Path(__file__).resolve(),sha(__file__))
    api.bind(pins,actions/"receipt.json",receipt_digest)
    action_receipt = read(actions/"receipt.json")
    resolutions = {}
    for relative,digest in action_receipt["source_sha256"].items():
        path = (ROOT/relative).resolve()
        if path == HERE/"joint-frame-action-reconciliation.py" and digest == action_receipt["output_sha256"]["producer.py.snapshot"]:
            snapshot = actions/"producer.py.snapshot"
            api.bind(pins,snapshot,digest)
            resolutions[relative] = {"original_path":relative,"sha256":digest,"snapshot_path":api.key(snapshot)}
        else:
            api.bind(pins,path,digest)
    for relative,digest in action_receipt["output_sha256"].items():
        path = (actions/relative).resolve()
        require(path.is_relative_to(actions), "action receipt output leaves owned packet")
        api.bind(pins,path,digest)
    for directory in (CONTACT,WASHER):
        api.receipt_sources(pins,directory/"receipt.json")
    api.authenticate(pins)
    loader = adapter.module(HERE/"panel-reference-completion.py","mean_inert_definitions")
    frame, frame_inputs = read(response/"comparison.json"), read(response/"inputs.json")
    inventory, accepted = adapter.response_inventory(api,pins,response,frame,frame_inputs,loader)
    require(action_summary["status"] == "COMPLETE_SAVED_COUPLED_ACTION_RECONCILIATION_NOT_RESISTANCE_QUALIFICATION"
            and action_summary["required_state_inventory"] == inventory
            and {(s["case_id"],s["gap_scale"]) for s in action_summary["states"]} == set(accepted)
            and action_summary["action_exports_complete_for_accepted_states"] is True,
            "action source inventory/provenance differs")
    geometry = read(actions/"nominal-gap/geometry.json")["members"]
    rows = read(HERE/"operators-attempt02/row-identities.json")
    require(len(geometry) == 44 and len(rows) == 1888, "reviewed geometry/row census differs")
    contacts = read(CONTACT/"geometry-inventory.json")
    groups, floors = contacts["contact_faces"], contacts["floor_footprints"]
    require(len(groups) == 117 and len(floors) == 8
            and sum(bool(g["wood_bodies"]) for g in groups) == 108, "contact geometry census differs")
    for group in groups+floors:
        for cell in group["cells"]:
            row = rows[cell["row"]]
            own = row["ownership"]
            require(row["row_id"] == cell["row_id"] and (own["first_body"],own["second_body"]) ==
                    (cell["first"],cell["second"]) and own["role"] == cell["role"]
                    and max(abs(x-y) for x,y in zip(own["point_mm"],cell["point_mm"],strict=True)) < 1e-7
                    and max(abs(x-y) for x,y in zip(own["direction_global_xyz"],cell["normal_force_on_first_xyz"],strict=True)) < 1e-8
                    and row["law"]["stiffness_N_per_mm"] == cell["k_n_per_mm"],
                    "old contact inventory differs from consumed canonical row")
    members = {m["member_id"]:m for m in read(MATERIAL)["members"]}
    require(read(MATERIAL)["conditional_DF_L_No2_base_row"]["base_properties"]["Fc_parallel"] == 1350
            and read(MATERIAL)["conditional_DF_L_No2_base_row"]["base_properties"]["Fc_perpendicular"] == 625,
            "wood reference scenario differs")
    for body,record in geometry.items():
        grain = record["geometry"]["axis"]
        material_grain = members[body]["source_proposed_longitudinal_grain_global_xyz"]
        require(abs(sum(x*y for x,y in zip(grain,material_grain,strict=True))) > 1-1e-7,
                "material/geometry longitudinal direction differs: "+body)
    axes = {}
    for row in rows:
        if row["ownership"]["role"] == "physical_bolt_outer_seat_tension":
            axis = row["row_id"].rsplit("/",1)[0]
            require(axis not in axes, "duplicate axial connector identity")
            axes[axis] = {"outer_tie":row["ownership"],"raw_tie_row":row["row"],
                "receivers":[row["ownership"][key] for key in ("first_body","second_body")]}
    require(len(axes) == 104, "104 exterior tie identities required")
    washer = adapter.module(HERE/"washer-reference-completion.py","mean_frozen_washer_supports")
    for path,digest in washer.PINS.items():
        api.bind(pins,path,digest)
    api.authenticate(pins)
    support, *_ = washer.normalized_supports(pins,axes)
    require(len(support) == 208, "208 exterior support identities required")
    for (_axis,body),seat in support.items():
        record = geometry[body]
        seat["matches_reviewed104_finished_step"] = (seat["support_step_sha256"] == record["current_finished_step_sha256"])
        seat["reviewed104_finished_step"] = record["current_finished_step"]
        seat["reviewed104_finished_step_sha256"] = record["current_finished_step_sha256"]
        seat.setdefault("ideal_annulus_area_mm2",washer.GENERIC_AREA_MM2)
        api.bind(pins,ROOT/record["current_finished_step"],record["current_finished_step_sha256"])
    special = {tuple(c["row"] for c in group["cells"])+(body,) for group in groups for body in group["wood_bodies"]
        if abs(sum(x*y for x,y in zip(group["normal_force_on_first_xyz"],geometry[body]["geometry"]["axis"],strict=True))) > 1e-8}
    require(len(special) == 34, "current parallel/oblique receiver interface census differs")
    receiver_source = adapter.module(HERE/"receiver-bearing-completion.py","mean_existing_nds_source_bindings")
    for path,digest in receiver_source.PINS.items():
        if path.suffix == ".pdf":
            api.bind(pins,path,digest)
    expressions = loader.definitions(HERE/"contact-bearing-completion.py",("bearing_expressions","ratios"),
        {"ast":__import__("ast"),"BEARING":ROOT/"scripts/compact_thick_results.py","PSI_MPA":PSI_MPA,"require":require})
    receiver_api = loader.definitions(HERE/"receiver-bearing-completion.py",("scalar_comparison",),
        {"math":math,"require":require})
    api.authenticate(pins)
    return api,pins,adapter,action_summary,frame,contacts,geometry,rows,members,axes,support,special,expressions,receiver_api,request,preparation,resolutions


def wood_reference(body, normal, cd, geometry, members):
    grain = geometry[body]["geometry"]["axis"]
    cosine = abs(sum(x*y for x,y in zip(grain,normal,strict=True)))
    require(cosine <= 1+1e-7, "nonunit bearing direction")
    cosine = 1. if abs(cosine-1) < 1e-8 else (0. if cosine < 1e-8 else cosine)
    binding = members[body]["code_Table4A_CF"]
    study = binding is None
    cf = 1. if study else binding["Fc_parallel"]
    return {"decision":"S" if study else "P" if cosine == 1 else "O",
        "normal_grain_dot_abs":cosine}, {"Fc_star_mpa":1350*PSI_MPA*cf*cd,"Fc_perp_mpa":625*PSI_MPA}


def build(output, actions, receipt_digest, prepare_only=False):
    started = time.monotonic()
    values = frozen_inputs(actions,receipt_digest)
    api,pins,_adapter,summary,frame,contacts,geometry,_rows,members,axes,support,special,expressions,receiver_api,request,preparation,resolutions = values
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate action-packet output child required")
    output.mkdir(parents=True)
    (output/".gitignore").write_text("*\n")
    (output/"producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    inventory = summary["required_state_inventory"]
    source_record = {"path":api.key(Path(actions).resolve()/"receipt.json"),"sha256":receipt_digest}
    report = {"schema":"joint_frame_bearing_reference/v1","status":"PREPARED_SOURCE_ONLY_NOT_MEAN_COMPARISONS",
        "action_source_receipt":source_record,"required_state_inventory":inventory,
        "source_resolution":resolutions,
        "force_basis":"reviewed104_coupled_knee_sensitivity","source_state_count":len(summary["states"]),
        "complete_required_accepted_comparisons":False,"mean_comparisons_complete_for_accepted_states":False,
        "limits":["Exact saved force arithmetic; no force correction or source-law tolerance change.",
            "The inherited 1e-4 N contact gate is reported separately from the compatible source 0.1 N gate.",
            "Positive-force area and uniform floor means remain represented model areas, not physical pressure patches.",
            "Nine panel/panel interfaces and the non-timber sides of timber/panel interfaces have no plywood-bearing reference here.",
            "Ripped-stock resistance is hypothetical; no grade inheritance or observed stock is inferred.",
            "Scalar connector own-end moments remain unknown; continuous washer planes are rigid and supply no metal stress.",
            "Four top rail source-quarter-inch/shop-5/16 mismatches remain unsupported product joins."],**FLAGS}
    write(output/"source-plan.json",{"action_source_receipt":source_record,"required_state_inventory":inventory,
        "contact_faces":108,"floor_footprints":8,"wood_contact_cells":856,"base_header_faces":16,
        "parallel_or_oblique_receiver_interfaces":34,"washer_axes":104,"washer_ends":208,
        "array_values_read":False,"estimated_parent_runtime_seconds":"5-20","estimated_memory_mb":"under 100"})
    if not prepare_only:
        import numpy as np

        face_results, receiver_results, washer_results, cell_results = [], [], [], []
        bearing = expressions.bearing_expressions()
        frame_states = {(s["case_id"],s["gap_scale"]):s for s in frame["states"]}
        labels = read(preparation/"port-labels.json")["new_ports"]
        terms = request["new_wood_port_terms"]
        nold = len(request["old_kept_lumped_rows"])
        continuous = {label["axis_id"] for label in labels}
        require(len(continuous) == 4, "four continuous axes required")
        with np.load(Path(actions)/"source-row-response.npz",allow_pickle=False) as saved:
            available, positions = saved["canonical_raw_row_available"],saved["canonical_raw_row_to_kept_lumped_position"]
            require(available.shape == (1888,) and np.count_nonzero(~available) == 20, "source availability mask differs")
            for state in summary["states"]:
                tag,case,gap = state["state_tag"],state["case_id"],state["gap_scale"]
                cd = .9 if case == "dead-only" else 1.
                force,q,coupled = [saved[tag+suffix] for suffix in
                    ("_raw_force_n","_kept_lumped_relative_motion_mm","_coupled_force_n")]
                common = {"state_tag":tag,"case_id":case,"gap_scale":gap,"source_state_record":state["source_state_record"],"duration_factor":cd}
                for group in [g for g in contacts["contact_faces"] if g["wood_bodies"]]+contacts["floor_footprints"]:
                    ids = [c["row"] for c in group["cells"]]
                    require(available[ids].all(), "replaced row used for contact mean")
                    reactions = force[ids].tolist()
                    require(all(v >= 0 and math.isfinite(v) for v in reactions), "negative/nonfinite signed normal force")
                    motions = q[positions[ids]].tolist()
                    floor = group["second"] == "floor"
                    if floor:
                        require(len(set(positions[ids].tolist())) == 1, "floor normal motion joins multiple kept rows")
                    area = sum(c["area_mm2"] for c,f in zip(group["cells"],reactions,strict=True) if f > 0)
                    errors = [abs(f-c["k_n_per_mm"]*max(m,0)) for c,f,m in zip(group["cells"],reactions,motions,strict=True)]
                    resultant_error = abs(sum(reactions)-group["normal_stiffness_n_per_mm"]*max(motions[0],0)) if floor else None
                    projection_errors = [abs(f-c["k_n_per_mm"]/group["normal_stiffness_n_per_mm"]*sum(reactions))
                        for c,f in zip(group["cells"],reactions,strict=True)] if floor else None
                    law_error = resultant_error if floor else max(errors,default=0)
                    law_pass = law_error < 1e-4 and max(motions) <= 10 and (
                        not floor or max(projection_errors,default=0) < 1e-4)
                    for cell,f,m,error in zip(group["cells"],reactions,motions,errors,strict=True):
                        disagreement = (f > 0) != (m > 0)
                        cell_results.append({**common,"group_id":group["group_id"],"raw_row":cell["row"],
                            "signed_compression_n":f,"source_motion_mm":m,"area_mm2":cell["area_mm2"],
                            "mean_pressure_mpa":f/cell["area_mm2"],"original_law_residual_n":error,
                            "legacy_contact_law_1e_4_n_met":error < 1e-4,"force_motion_active_disagreement":disagreement,
                            "legacy_activity_disagreement_gate_met":not disagreement or abs(m) <= 1e-8 or f <= 1e-4,
                            "q_is_uniform_footprint_mean":floor,"is_stress_peak":False})
                    average,quarter = expressions.ratios(bearing,reactions,area)
                    full_average,full_quarter = expressions.ratios(bearing,reactions,group["represented_area_mm2"])
                    face_results.append({**common,"group_id":group["group_id"],"kind":group["kind"],
                        "base_header_interface":group["base_header_interface"],"raw_rows":ids,
                        "signed_compression_n":sum(reactions),"positive_force_area_mm2":area,
                        "represented_area_mm2":group["represented_area_mm2"],"active_mean_Fc_perp_index":average,
                        "represented_mean_Fc_perp_index":full_average,"quarter_area_corner_index":quarter,
                        "represented_quarter_area_corner_index":full_quarter,"legacy_contact_law_1e_4_n_met":law_pass,
                        "original_law_residual_peak_n":law_error,
                        "floor_resultant_law_residual_n":resultant_error,
                        "floor_cell_projection_residual_peak_n":max(projection_errors,default=0) if floor else None,
                        "pressure_patch_qualified":False})
                    for body in group["wood_bodies"]:
                        local,reference = wood_reference(body,group["normal_force_on_first_xyz"],cd,geometry,members)
                        local.update(saved_compression_n=sum(reactions),saved_active_area_mm2=area)
                        result = receiver_api.scalar_comparison(local,reference,True) if area > 0 else {
                            "law":"NO_ACTIVE_AREA","supported_resistance_ratio":None,"hypothetical_reference_ratio":None,
                            "mean_stress_mpa":0.,"parallel_plate_trigger_ratio":None}
                        receiver_results.append({**common,"group_id":group["group_id"],"receiver":body,
                            "raw_rows":ids,"parallel_or_oblique_interface":tuple(ids)+(body,) in special,
                            "normal_grain_dot_abs":local["normal_grain_dot_abs"],"decision":local["decision"],
                            "legacy_contact_law_1e_4_n_met":law_pass,"comparison":result})
                for axis,identity in axes.items():
                    direction = identity["outer_tie"]["direction_global_xyz"]
                    for body in identity["receivers"]:
                        seat = support[(axis,body)]
                        mismatch = axis.startswith("top_outer/") and "/rail_" in axis
                        normal_pressure = None
                        if axis in continuous:
                            ports = [i for i,label in enumerate(labels) if label["axis_id"] == axis
                                and label["role"] == "wood_seat" and label["member_id"] == body]
                            require(ports, "continuous own-end seat has no consumed wood ports")
                            areas = np.asarray([labels[i]["area_mm2"] for i in ports])
                            points = np.asarray([labels[i]["point_mm"] for i in ports])
                            center = areas@points/areas.sum()
                            pressure = coupled[nold+np.asarray(ports)]/areas
                            tension,ideal_area = float(np.sum(coupled[nold+np.asarray(ports)])),float(areas.sum())
                            physical = []
                            for port in ports:
                                require(len(terms[port]) == 1 and terms[port][0]["member_id"] == body,
                                        "continuous seat wood-term identity differs")
                                physical.append(-coupled[nold+port]*np.asarray(terms[port][0]["direction_global_xyz"]))
                            moment = np.sum(np.cross(points-center,np.asarray(physical)),axis=0).tolist()
                            diagnostic = next(r for r in frame_states[(case,gap)]["compatible_shaft_diagnostics"] if r["axis_id"] == axis)
                            diagnostic = next(r for r in diagnostic["wood_seat_pressure_diagnostics"] if r["receiver"] == body)
                            require(abs(tension-diagnostic["normal_resultant_n"]) < 1e-8
                                    and abs(ideal_area-diagnostic["area_mm2"]) < 1e-8, "continuous pressure diagnostic join differs")
                            normal_pressure = {"sampled_peak_mpa":float(pressure.max()),"source_diagnostic":diagnostic}
                        else:
                            require(available[identity["raw_tie_row"]], "unavailable scalar tie used as zero")
                            tension = float(force[identity["raw_tie_row"]])
                            ideal_area = seat["ideal_annulus_area_mm2"]
                            moment = None
                        require(tension >= 0 and ideal_area > 0, "invalid own-end compression/annulus area")
                        geometric_area = seat["saved_supported_area_mm2"]
                        exact_geometry = seat["matches_reviewed104_finished_step"]
                        qualified_area = geometric_area if exact_geometry and geometric_area and not mismatch \
                            and seat["support_evidence"].get("scenario_supported") is not False else None
                        local,reference = wood_reference(body,direction,cd,geometry,members)
                        local.update(saved_compression_n=tension,saved_active_area_mm2=ideal_area)
                        ideal_comparison = receiver_api.scalar_comparison(local,reference,True)
                        local["saved_active_area_mm2"] = qualified_area
                        supported_comparison = receiver_api.scalar_comparison(local,reference,True) if qualified_area else None
                        washer_results.append({**common,"axis_id":axis,"receiver":body,"end_role":seat["role"],
                            "continuous_own_end":axis in continuous,"signed_end_compression_n":tension,
                            "ideal_annulus_area_mm2":ideal_area,"ideal_mean_pressure_mpa":tension/ideal_area,
                            "saved_geometric_support_area_mm2":geometric_area,
                            "geometric_area_pressure_diagnostic_mpa":tension/geometric_area if geometric_area and exact_geometry else None,
                            "applicable_supported_area_mm2":qualified_area,"supported_mean_pressure_mpa":tension/qualified_area if qualified_area else None,
                            "ideal_area_reference_comparison":ideal_comparison,
                            "supported_area_reference_comparison":supported_comparison,
                            "ideal_area_reference_is_pressure_patch_qualification":False,
                            "comparison_is_supported_area_reference":bool(qualified_area),
                            "own_end_wood_moment_xyz_nmm":moment,"own_end_moment_unknown_not_zero":moment is None,
                            "wood_pressure_diagnostics":normal_pressure,"shop_source_profile_mismatch":mismatch,
                            "support":seat,"washer_metal_stress_mpa":None,"washer_metal_resistance_index":None,
                            "partial_seat_limit":axis == "center_principal_right_2"})
        nstates = len(summary["states"])
        require(len(face_results) == 116*nstates and len(receiver_results) == 198*nstates
                and len(washer_results) == 208*nstates
                and sum(r["parallel_or_oblique_interface"] for r in receiver_results) == 34*nstates,
                "mean comparison census differs")
        for name,records in (("contact-cells.jsonl",cell_results),("contact-floor-means.jsonl",face_results),
                ("receiver-means.jsonl",receiver_results),("washer-own-end-means.jsonl",washer_results)):
            with (output/name).open("w") as stream:
                for row in records:
                    stream.write(json.dumps(row,separators=(",",":"),allow_nan=False)+"\n")
        report.update(status="COMPLETE_SAVED_MEAN_REFERENCES_WITH_DECLARED_CONTACT_PROFILE_MATERIAL_STRESS_LIMITS",
            mean_comparisons_complete_for_accepted_states=True,
            counts={"accepted_states":nstates,"required_states":14,"excluded_states":14-nstates,
                "wood_contact_face_states":108*nstates,"floor_mean_states":8*nstates,
                "base_header_face_states":16*nstates,"receiver_mean_states":len(receiver_results),
                "parallel_or_oblique_receiver_interface_states":34*nstates,"washer_own_end_states":len(washer_results),
                "continuous_own_end_states":8*nstates,"scalar_own_end_moment_limits":200*nstates,
                "legacy_contact_law_gate_limited_groups":sum(not r["legacy_contact_law_1e_4_n_met"] for r in face_results),
                "legacy_contact_law_gate_limited_cells":sum(not r["legacy_contact_law_1e_4_n_met"] for r in cell_results),
                "force_motion_activity_disagreements":sum(r["force_motion_active_disagreement"] for r in cell_results),
                "legacy_activity_gate_limited_cells":sum(not r["legacy_activity_disagreement_gate_met"] for r in cell_results),
                "unsupported_washer_area_states":sum(not r["applicable_supported_area_mm2"] for r in washer_results),
                "shop_source_profile_mismatch_end_states":sum(r["shop_source_profile_mismatch"] for r in washer_results),
                "washer_metal_stress_method_limits":len(washer_results)},
            peaks={"contact_active_mean_Fc_perp":max(r["active_mean_Fc_perp_index"] for r in face_results),
                "floor_represented_mean_Fc_perp":max(r["represented_mean_Fc_perp_index"] for r in face_results if r["kind"] == "floor"),
                "supported_receiver_index":max((r["comparison"].get("supported_resistance_ratio") or 0) for r in receiver_results),
                "hypothetical_receiver_index":max((r["comparison"].get("hypothetical_reference_ratio") or 0) for r in receiver_results),
                "washer_supported_mean_pressure_mpa":max((r["supported_mean_pressure_mpa"] or 0) for r in washer_results)})
    api.authenticate(pins)
    report["source_sha256"] = {api.key(p):h for p,h in pins.items()}
    write(output/"summary.json",report)
    outputs = {p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    write(output/"receipt.json",{"schema":"joint_frame_bearing_reference_receipt/v1","status":report["status"],
        "source_sha256":report["source_sha256"],"output_sha256":outputs,"counts":report.get("counts",{}),
        "source_resolution":resolutions,"required_state_inventory":inventory,
        "sources_unchanged_before_and_after":True,"elapsed_seconds":time.monotonic()-started,**FLAGS})
    api.authenticate(pins)
    require(all(sha(output/name) == digest for name,digest in outputs.items()), "published mean output changed")
    return {"status":report["status"],"receipt_sha256":sha(output/"receipt.json"),"output":api.key(output)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=("prepare","build"))
    parser.add_argument("--actions",type=Path,required=True)
    parser.add_argument("--receipt-sha256",required=True)
    parser.add_argument("--output",type=Path,required=True)
    arguments = parser.parse_args()
    print(json.dumps(build(arguments.output,arguments.actions,arguments.receipt_sha256,arguments.stage == "prepare")))
