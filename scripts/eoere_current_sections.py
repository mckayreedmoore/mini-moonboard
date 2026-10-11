"""Bounded current finished-section queries and same-cut six-case comparisons.

Read the existing cached BREPs, never rebuild CAD or solve mechanics. Select
one largest gross normal witness per timber plus sixteen high-action bore
stations. These 38 planes do not establish continuous finished-member strength.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
from pathlib import Path

import numpy as np

from scripts import eoere_current_components as component
from scripts import eoere_current_response as current
from scripts.summarize_eoere_current_response import SEQUENCE, canonical_sha

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
METHODS = {
    "sections": {"path": "scripts/thin_bolted_timber_section_properties.py",
                 "sha256": "398e883849dfd83a34aeb60b5ac0b5d50f57ffa9b01f3f2427e341725749a80a"},
    "plane": {"path": "scripts/wood_joint_wj12_sections.py",
              "sha256": "8d448eb02238a4fdfb019fa8274d68cfbbfb2718f329670e5f1a1d5a154952ba"},
    "cuts": {"path": component.BASE + "component-method-v1/gross_members.py",
             "sha256": "01aaf22c8b2cf93430e7bbce4768260efea39bed3d527b8f5486ba4e38e32258"},
}
# Existing section helpers import these historical modules while loading.
# Pin the complete local import closure; their designs/actions are not inputs.
IMPORT_CLOSURE = {
    "mini_moonboard/wood_joint_frame.py": "77b4a8b28b02088878f1f0e0483610a7918cb85f5694f0551f50cf8888886545",
    "mini_moonboard/wood_joint_geometry.py": "e437385d4894c7bcd4bbf4ee66aa9f96a53a8d3570efc6230fb225570abbb90e",
    "mini_moonboard/wood_joint_panel_machining.py": "1928e32ba5b5e75caca99abb42e5d5b01822d6697c6f892dda38650cca302afd",
    "mini_moonboard/wood_joint_wj04_config.py": "4f94f49ebc0c5f92e6dce339794983607614299f53150fc7264ca54b29e987be",
    "mini_moonboard/wood_joint_wj05_socket.py": "cca786d898621058bddf5c58ee266d3da3d8550b84805be1c7a856cf693c6913",
    "scripts/owner_layout_protected.py": "405db94a8adc2da465d137d3b35bba5848fbe67cbd35d52c0613a01161560e58",
    "scripts/wood_joint_clearance.py": "82ec31eacab279cfb1c3e2e2fe976e13712f36b8bc5d64f794a0601608d8bd2d",
    "scripts/wood_joint_wj03_compact_outer_access.py": "d1a909da2bfa660d00731551972e6b256da70c9e124f4057b04a47c5404592bc",
    "scripts/wood_joint_wj03_compact_outer_probe.py": "1b87fffdb250e7e3021f43913bb26d2e0c6f4a3b3f198d31c6bd8b875320065e",
    "scripts/wood_joint_wj03_sequence.py": "27d62b50bdbe3084c68caa35f186785e57cff412fb9e68eb5fafe423ed260386",
    "scripts/wood_joint_wj04_full_stock_probe.py": "965b997a2b3f4ecb4c39e161fc9dde1757ff8a4c8d7bc8acc90d851a122f8bde",
    "scripts/wood_joint_wj04_probe.py": "75d397795e5fa69d1d04f1d14caeb57f93a2da94cacecd4a1edc5bdad3fe4d94",
    "scripts/wood_joint_wj04_tool_access.py": "91e0a8c4bd1681fe5f10d96d99c8e6b3ef39b8d7a26fb42b4bb77c6f85ae2fc8",
    "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py": "94d2b301450c942f1c7a95f89e3e7ee1ed643ce4db43576c78c1bce04f9302b9",
    "scripts/wood_joint_wj04_upper_pair_probe.py": "7e042ed35b6670191e2549f4f4922af4643db8d6552fef09b6998546ae123860",
    "scripts/wood_joint_wj05_center_node_probe.py": "eafffbc95d5989bcc21a7cfed90ff25e917c778bf9758154b915cbba0ec3d173",
    "scripts/wood_joints_wj05_center_backer_transfer_probe.py": "3da60ba6931f791e6b877b59aab7157f6e62a7e2b9db276187113e122aa8d062",
}


def own_ref():
    component.canonical_dependency()
    current.require(current.sha(OWN) == LOADED_SHA, "loaded current section adapter changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def select_requests(cases, fields, *, extra_bore_planes=16):
    """Whole saved witnesses choose stations; subsequent actions stay per case."""
    current.require(list(cases) == list(fields) == SEQUENCE, "six ordered own states required")
    members = {r["name"]: r for r in fields[SEQUENCE[0]]["source_inputs"]["timber_rows"]}
    current.require(len(members) == 22 and all(
        {r["name"]: r for r in f["source_inputs"]["timber_rows"]} == members for f in fields.values()),
        "same current 22-member source rows required")
    requests, seen = [], set()
    def add(name, station, selection):
        row = members[name]
        g = np.asarray(row["axis"])
        low, high = float(g @ row["start"]), float(g @ row["end"])
        current.require(high-low > .2, "positive interior member span required")
        # End-profile stations retain a small interior offset; the wrench is
        # freshly recovered at the actual requested station for every case.
        station = float(np.clip(station, low+.1, high-.1))
        key = name, round(station, 5)
        if key in seen:
            return False
        seen.add(key)
        requests.append({"member": name, "station_global_grain_projection_mm": station,
                         "selection": selection})
        return True
    for name in members:
        witnesses = []
        for case_id, data in cases.items():
            row = next(r for r in data["component_reductions"]["fresh_gross_member_diagnostics"] if r["member"] == name)
            witness = row["witnesses"]["fully_braced_normal"]
            witnesses.append((witness["gross_CD1_comparison"]["fully_braced_component_normal_interaction"], case_id, witness))
        value, case_id, witness = max(witnesses, key=lambda item: item[0])
        add(name, witness["station_global_grain_projection_mm"],
            {"basis": "largest saved gross normal witness for this member", "case_id": case_id,
             "gross_normal_reference_index": value, "original_gross_station_mm": witness["station_global_grain_projection_mm"]})
    candidates = []
    for case_id, field in fields.items():
        for port in field["common_shaft_wood_bearing_actions"]:
            length = port["surface_interval_mm"][1]-port["surface_interval_mm"][0]
            score = float(np.linalg.norm(port["force_on_host_xyz_n"]) + np.linalg.norm(port["moment_on_host_at_point_xyz_nmm"])/length)
            station = float(np.asarray(members[port["host"]]["axis"]) @ port["point_xyz_mm"])
            candidates.append((score, case_id, port["axis_id"], port["host"], station))
    added = 0
    for score, case_id, aid, name, station in sorted(candidates, reverse=True):
        if added == extra_bore_planes:
            break
        if add(name, station, {"basis": "largest remaining own wood port force plus couple/interval selection score",
                               "case_id": case_id, "axis_id": aid, "selection_score_n": score}):
            added += 1
    current.require(len(requests) == 22+extra_bore_planes, "bounded distinct plane census required")
    return requests


def normal_reference(stress, reference):
    """Same-cut fully-braced component comparison, without local strength credit."""
    mean = stress["mean_axial_normal_stress_n_mm2"]
    bending = stress["bending_normal_stress_extrema_n_mm2"]
    current.require(math.isfinite(mean) and len(bending) == 2 and all(math.isfinite(v) for v in bending) and
                    all(math.isfinite(reference[k]) and reference[k] > 0 for k in ("Ft_mpa", "Fc_star_mpa", "Fb_star_mpa")),
                    "finite normal components and positive conditional references required")
    bend = max(abs(v) for v in bending)
    ratio = (mean / reference["Ft_mpa"] if mean >= 0 else (mean/reference["Fc_star_mpa"])**2) + bend/reference["Fb_star_mpa"]
    return {"mean_axial_normal_stress_mpa": mean, "largest_abs_bending_normal_stress_mpa": bend,
            "fully_braced_linear_normal_CD1_reference_index": ratio,
            "exceeds_conditional_normal_reference": ratio > 1.,
            "local_hole_notch_fracture_restraint_or_complete_resistance": None}


def run():
    """Genuine current admission precedes geometry imports or cut recovery."""
    own_ref()
    config_ref = current.ref(component.INPUTS)
    config = current.read(config_ref)
    summary = current.read(config["current_response"])
    current.require(summary["case_sequence"] == SEQUENCE and summary["extra_grid"] is False
                    and summary["all_six_saved_field_admissions_pass"] is True
                    and summary["force_producer"] == current.ref(current.OWN)
                    and summary["geometry"] == current.manifest()["references"]["geometry"]
                    and summary["hardware_model"] == current.manifest()["references"]["hardware"]
                    and summary["release"] == config["release"] == current.manifest()["release"],
                    "exact current admitted force summary required")
    pins = current.join(IMPORT_CLOSURE, {r["path"]: r["sha256"] for r in [
        own_ref(), component.own_ref(), component.canonical_dependency(), config_ref, config["current_response"], *METHODS.values()]})
    cases, fields, bindings, canonicals = {}, {}, [], {}
    with current.response_context() as (gate, _):
        for binding in summary["cases"]:
            case_id = binding["case_id"]
            case_ref = current.ref(component.RAW / "cases-v1" / case_id / component.CASE_ATTEMPT / "components.json")
            data = current.read(case_ref)
            current.require(data["schema"] == "eoere_selected_hardware_current_component_case/v1"
                            and data["producer"] == component.own_ref()
                            and data["field"] == binding["field"] and data["admission"] == binding["admission"]
                            and data["geometry"] == summary["geometry"] and data["hardware_model"] == summary["hardware_model"]
                            and data["release"] == summary["release"], "own current component binding required")
            raw = (current.ROOT / binding["field"]["path"]).read_bytes()
            current.require(current.sha(current.ROOT / binding["field"]["path"]) == binding["field"]["sha256"], "exact own raw field required")
            field, admitted = gate.require_admitted_payload(raw, current.read(binding["admission"]), admission_sha256=current.LOADED_SHA)
            current.require(field["state_id"] == data["state_id"] == binding["state_id"] and field["case_id"] == case_id,
                            "own same-case section state required")
            current.require(data["raw_field_canonical_sha256"] == canonical_sha(field), "component source field differs")
            pins = current.join(pins, admitted, data["source_sha256"],
                                {r["path"]: r["sha256"] for r in [case_ref, binding["field"], binding["admission"]]})
            cases[case_id], fields[case_id], canonicals[case_id] = data, field, canonical_sha(field)
            bindings.append({"case_id": case_id, "state_id": field["state_id"], "components": case_ref,
                             "field": binding["field"], "admission": binding["admission"]})
    current.verify(pins)
    requests = select_requests(cases, fields)
    # Source-bound helpers and cached solids are reached only after all six
    # genuine saved-field admissions. No helper's historical intake is called.
    section = component.load(METHODS["sections"], "current_sections")
    plane = component.load(METHODS["plane"], "current_plane")
    gross = component.load(METHODS["cuts"], "current_cuts")
    pins = current.join(pins, gross.source_pins())
    reference = gross.rectangle.nds.adjusted_reference(139.7)
    import cadquery as cq
    source0 = fields[SEQUENCE[0]]["source_inputs"]
    members = {r["name"]: r for r in source0["timber_rows"]}
    observations = {r["id"]: r for r in source0["finished_body_observations"]}
    current.require(all(f["source_inputs"]["finished_body_observations"] == source0["finished_body_observations"] for f in fields.values()),
                    "same exact current finished solids required")
    inputs = {case_id: gross.own.member_point_inputs(field) for case_id, field in fields.items()}
    shapes, results = {}, []
    for request in requests:
        name, station = request["member"], request["station_global_grain_projection_mm"]
        row, observation = members[name], observations[name]
        source = observation["source"]
        current.require(current.sha(current.ROOT/source["path"]) == source["sha256"], "current finished BREP changed")
        pins = current.join(pins, {source["path"]: source["sha256"]})
        if name not in shapes:
            shape = cq.Shape.importBrep(str(current.ROOT/source["path"]))
            current.require(shape.isValid() and len(shape.Solids()) == 1 and abs(shape.Volume()-observation["volume_mm3"]) < .01,
                            "current single-solid BREP import differs")
            shapes[name] = shape
        shape = shapes[name]
        grain, start, end = np.asarray(row["axis"]), np.asarray(row["start"]), np.asarray(row["end"])
        low, high = float(grain @ start), float(grain @ end)
        origin = start+grain*(station-low)
        properties = section.measure_section(shape, origin=origin.tolist(), grain=grain.tolist())
        axes = [cq.Vector(*v) for v in properties["basis_u_v_grain_xyz"]]
        point = cq.Vector(*origin)
        matrix = plane._basis_matrix(point, *axes)
        local = shape.intersect(plane._plane_face(point, axes[2])).transformShape(section.rigid_matrix(
            [[matrix.wrapped.Value(i, j) for j in (1, 2, 3, 4)] for i in (1, 2, 3)]))
        per_case = []
        for case_id in SEQUENCE:
            actions, gravity = inputs[case_id]
            center, weight = gravity[name]
            wrench = gross.own.previous.member_cut_wrench(grain.tolist(), low, high, origin.tolist(), center, weight, actions[name])
            stress = section.linear_normal_stress(local, properties, wrench)
            shear = np.asarray(wrench["force_on_lower_portion_xyz_n"])
            shear -= grain * float(grain @ shear)
            mean = float(np.linalg.norm(shear)) / properties["finished_area_mm2"]
            per_case.append({"case_id": case_id, "state_id": fields[case_id]["state_id"],
                             "linear_normal_stress": stress, "normal_reference": normal_reference(stress, reference),
                             "necessary_mean_shear_mpa": mean, "necessary_mean_shear_over_CD1_Fv": mean/reference["Fv_mpa"],
                             "finished_shear_torsion_fracture_or_stability_resistance": None})
        results.append({**request, "finished_source": source, "gross_stock_area_mm2": row["width_mm"]*row["depth_mm"],
                        "section_properties": properties, "case_comparisons": per_case})
    current.require(all(canonical_sha(fields[k]) == v for k, v in canonicals.items()), "section recovery changed admitted fields")
    current.verify(pins)
    own_ref()
    return {"schema": "eoere_current_targeted_finished_sections/v1", "producer": own_ref(),
            "geometry": summary["geometry"], "hardware_model": summary["hardware_model"], "extra_grid": False,
            "cases": bindings, "selected_unique_planes": len(results), "same_plane_case_comparisons": len(results)*6,
            "source_sha256": pins, "reference_CD1_DFL_No2_dry_unincised": reference,
            "finished_sections": results, "source_pins_and_fields_unchanged": True,
            "tool_versions": {n: importlib.metadata.version(n) for n in ["cadquery", "cadquery-ocp", "numpy"]},
            "native_solve_or_CAD_rebuild": False, "continuous_finished_extrema_or_member_resistance": None,
            "limits": ["38 selected exact cached-solid planes: 22 largest per-member gross normal witnesses and 16 distinct high-action wood bore stations; six same-case wrenches on every plane.",
                       "Interior end offsets are recorded; every wrench is recovered at the actual queried station with own capture support points, free couples and affine member gravity.",
                       "Centroid/cross-inertia/trimmed-material linear normal references and necessary average shear only; no local stress concentration, shear/torsion/fracture, brace/contact qualification or finished-stiffness response.",
                       "DF-L No.2/CD1 component scalars remain conditional. No continuous minimum-section inventory, complete member acceptance or physical demand bound is established."],
            "release": current.manifest()["release"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
