"""Current cleat opening, top-rail bore sections and compression event census.

Reuses admitted fields and cached solids. No frame solve, CAD rebuild,
strength adoption or geometry change is performed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts import eoere_current_components as component
from scripts import eoere_current_response as current
from scripts import eoere_current_sections as targeted
from scripts.summarize_eoere_current_response import SEQUENCE, canonical_sha

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
PACKET = current.DOC / "selected-hardware-v1/current-response-v1/joint-closure-v1"
OPENING = {
    "path": str((current.DOC / "bounded-strength-v1/analyze.py").relative_to(current.ROOT)),
    "sha256": "8bffd53e9e730e63db2f041a10626edb002cba7034af118d6dc9bdf3fed69ae3",
}


def cleat_opening(field, data, opening_force):
    shafts = {s["axis_id"]: s for s in field["source_inputs"]["shafts"]}
    results = []
    for name in ["eoere_cleat_left", "eoere_cleat_right"]:
        terms = []
        for row in data["findings"]["timber"]["wood_surfaces"]:
            if row["receiver"] == name:
                shaft = shafts[row["axis_id"]]
                current.require(abs(shaft["basis"][0][1]) < 1e-10, "cleat bolt must not cross Y-normal plane")
                y = row["own_aggregate_point_xyz_mm"][1]
                radius = shaft["bore_diameter_mm"]/2
                terms.append([y-radius, y+radius, row["own_force_xyz_n"][1]])
        current.require(len(terms) == 4, "four own complete cleat bore wrenches required")
        for table in ["contact_actions", "shaft_end_capture_actions", "panel_screw_actions"]:
            current.require(all(abs(r["force_on_first_xyz_n"][1]) < 1e-10 for r in field[table]
                                if name in (r["first"], r["second"])), "additional cleat Y force must be included")
        current.require(all(abs(r["force_xyz_n"][1]) < 1e-10 for r in field["body_applied_loads"] if r["body"] == name)
                        and abs(sum(q[2] for q in terms)) < 1e-5, "cleat applied-force/equilibrium guard failed")
        results.append({"member": name, "plane_y_mm": -105.85, "whole_bore_supports_y_min_max_force_n": terms,
                        **opening_force(terms, -105.85), "actual_cross_grain_fracture_resistance_n": None,
                        "retained_X_axis_bolts_cross_this_Y_normal_plane": False,
                        "force_only_lower_bound_disposes_couples_or_all_crack_planes": False})
    return results


def compression_events(field, gross):
    actions, gravity = gross.own.member_point_inputs(field)
    rows = []
    for member in field["source_inputs"]["timber_rows"]:
        name, grain = member["name"], np.array(member["axis"])
        start = np.array(member["start"])
        low, high = float(grain @ start), float(grain @ member["end"])
        stations = {low, high}
        for point, _, _ in actions[name]:
            s = float(grain @ point)
            stations.update([float(np.clip(s-1e-5, low, high)), float(np.clip(s+1e-5, low, high))])
        center, weight = gravity[name]
        candidates = []
        for station in sorted(stations):
            point = start+grain*(station-low)
            wrench = gross.own.previous.member_cut_wrench(grain.tolist(), low, high, point.tolist(), center, weight, actions[name])
            candidates.append({"station_global_grain_projection_mm": station,
                               "axial_tension_positive_n": float(grain @ wrench["force_on_lower_portion_xyz_n"]),
                               "signed_same_cut_wrench": wrench})
        rows.append({"member": name, "action_event_side_candidate_count": len(candidates),
                     "most_compressive_action_event_witness": min(candidates, key=lambda r: r["axial_tension_positive_n"]),
                     "continuous_finished_stability_or_qualified_restraint": None})
    return rows


def run():
    parent_ref = current.ref(PACKET / "inputs-v2.json")
    parent = current.read(parent_ref)
    forces, components = current.read(parent["current_response"]), current.read(parent["current_components"])
    refs = [parent_ref, parent["current_response"], parent["current_components"], *parent["case_components"],
            current.ref(OWN), current.ref(Path(targeted.__file__)), OPENING, *targeted.METHODS.values()]
    maps = []
    for report in [forces, components]:
        union = report["source_union"]
        sources = current.read(union["record"])
        current.require(len(sources) == union["count"] and canonical_sha(sources) == union["canonical_sha256"], "parent source union differs")
        maps.append(sources)
        refs.append(union["record"])
    pins = current.join(*maps, targeted.IMPORT_CLOSURE, {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    current.require(forces["case_sequence"] == components["case_sequence"] == SEQUENCE
                    and components["current_response"] == parent["current_response"]
                    and forces["all_six_saved_field_admissions_pass"] is True
                    and forces["geometry_revision"] == "eoere-raised-kicker-screws-v1"
                    and forces["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
                    and forces["extra_grid"] is False and components["extra_grid"] is False,
                    "exact admitted current OFF cases required")
    current.require([r.get("case_id") for r in forces["cases"]] == SEQUENCE
                    and len({r.get("state_id") for r in forces["cases"]}) == len(SEQUENCE)
                    and all(isinstance(r.get("state_id"), str) and r["state_id"] for r in forces["cases"]),
                    "exact ordered case bindings and unique states required")
    fields, raw, bindings = {}, {}, []
    for binding, ref in zip(forces["cases"], parent["case_components"], strict=True):
        field, data = current.read(binding["field"]), current.read(ref)
        case = binding["case_id"]
        current.require(field["case_id"] == data["case_id"] == case
                        and field["state_id"] == data["state_id"] == binding["state_id"]
                        and data["field"] == binding["field"] and data["admission"] == binding["admission"]
                        and data["raw_field_canonical_sha256"] == canonical_sha(field), "own exact field/component join required")
        fields[case], raw[case] = field, data
        bindings.append({"case_id": case, "state_id": field["state_id"], "field": binding["field"], "components": ref})
    # All current evidence authenticates before imported geometry is reached.
    section = component.load(targeted.METHODS["sections"], "closure_section_method")
    plane = component.load(targeted.METHODS["plane"], "closure_plane_method")
    gross = component.load(targeted.METHODS["cuts"], "closure_cut_method")
    opening = component.load(OPENING, "closure_opening_method")
    pins = current.join(pins, gross.source_pins())
    cases = [{**binding, "cleat_opening": cleat_opening(fields[binding["case_id"]], raw[binding["case_id"]], opening.opening_force),
              "compression_action_events": compression_events(fields[binding["case_id"]], gross)} for binding in bindings]
    witnesses = []
    for case in SEQUENCE:
        member = next(r for r in raw[case]["component_reductions"]["fresh_gross_member_diagnostics"] if r["member"] == "base_rail_top")
        witness = member["witnesses"]["sufficient_shear_torsion"]
        witnesses.append((witness["gross_CD1_comparison"]["equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio"], case, witness))
    ratio, governing_case, witness = max(witnesses, key=lambda r: r[0])
    source0 = fields[SEQUENCE[0]]["source_inputs"]
    member = next(r for r in source0["timber_rows"] if r["name"] == "base_rail_top")
    observation = next(r for r in source0["finished_body_observations"] if r["id"] == member["name"])
    source = observation["source"]
    current.require(all(next(r for r in f["source_inputs"]["finished_body_observations"] if r["id"] == member["name"]) == observation
                        for f in fields.values()), "same exact current rail solid required")
    pins = current.join(pins, {source["path"]: source["sha256"]})
    current.verify(pins)
    import cadquery as cq

    shape = cq.Shape.importBrep(str(current.ROOT / source["path"]))
    current.require(shape.isValid() and len(shape.Solids()) == 1 and abs(shape.Volume()-observation["volume_mm3"]) < .01, "current rail BREP differs")
    grain, start = np.asarray(member["axis"]), np.asarray(member["start"])
    low, high = float(grain @ start), float(grain @ member["end"])
    stations = {witness["station_global_grain_projection_mm"]}
    bores = []
    for shaft in source0["shafts"]:
        if shaft["axis_id"] in ["eoere_bolt_017", "eoere_bolt_018"]:
            current.require(any(s["host"] == member["name"] for s in shaft["surfaces"])
                            and abs(grain @ shaft["basis"][0]) < 1e-10, "own transverse top rail bore required")
            center, radius = float(grain @ shaft["point"]), shaft["bore_diameter_mm"]/2
            bores.append({"axis_id": shaft["axis_id"], "center_grain_station_mm": center, "nominal_bore_radius_mm": radius})
            stations.update([center, center-radius-.01, center-radius+.01, center+radius-.01, center+radius+.01])
    current.require(len(bores) == 2, "two governing-neighborhood top rail bores required")
    actions = {case: gross.own.member_point_inputs(field) for case, field in fields.items()}
    reference = gross.rectangle.nds.adjusted_reference(139.7)
    sections = []
    for station in sorted(stations):
        origin = start+grain*(station-low)
        properties = section.measure_section(shape, origin=origin.tolist(), grain=grain.tolist())
        axes = [cq.Vector(*v) for v in properties["basis_u_v_grain_xyz"]]
        point = cq.Vector(*origin)
        matrix = plane._basis_matrix(point, *axes)
        local = shape.intersect(plane._plane_face(point, axes[2])).transformShape(section.rigid_matrix(
            [[matrix.wrapped.Value(i, j) for j in (1, 2, 3, 4)] for i in (1, 2, 3)]))
        comparisons = []
        for case in SEQUENCE:
            inputs, gravity = actions[case]
            center, weight = gravity[member["name"]]
            cut = gross.own.previous.member_cut_wrench(grain.tolist(), low, high, origin.tolist(), center, weight, inputs[member["name"]])
            stress = section.linear_normal_stress(local, properties, cut)
            force = np.asarray(cut["force_on_lower_portion_xyz_n"])
            shear = force-grain*float(grain @ force)
            comparisons.append({"case_id": case, "state_id": fields[case]["state_id"], "linear_normal_stress": stress,
                                "fully_braced_normal_reference": targeted.normal_reference(stress, reference),
                                "necessary_mean_shear_mpa": float(np.linalg.norm(shear))/properties["finished_area_mm2"],
                                "finished_shear_torsion_or_local_fracture_resistance": None})
        sections.append({"station_global_grain_projection_mm": station, "properties": properties, "case_comparisons": comparisons})
    current.verify(pins)
    current.require(current.sha(OWN) == LOADED_SHA, "loaded producer changed")
    return {"schema": "eoere_current_local_timber_closure_queries/v1", "producer": current.ref(OWN), "parent_inputs": parent_ref,
            "geometry_revision": forces["geometry_revision"], "hardware_revision": forces["hardware_revision"], "extra_grid": False,
            "cases": cases, "top_rail_governing_gross_witness": {"case_id": governing_case, "ratio": ratio, "witness": witness},
            "top_rail_bore_neighborhood": bores, "top_rail_finished_source": source, "top_rail_finished_sections": sections,
            "source_sha256": pins, "all_input_sources_unchanged": True, "native_solve_CAD_rebuild_or_remedy_performed": False,
            "finished_member_capacity": None, "physical_demand_bounds_established": False, "structural_acceptance": False,
            "release": forces["release"], "limits": [
                "Own current cleat force-only opening lower bound at one uncut Y-normal plane; couples and other crack planes require separate resistance.",
                "Most-compressive action-event-side witnesses are a directed census, not continuous finished strength or restraint qualification.",
                "Selected exact cached rail cuts target the governing gross shear/torsion bore neighborhood. Normal references and necessary average shear do not qualify finished torsion, local hole loading, fracture or physical demands."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
