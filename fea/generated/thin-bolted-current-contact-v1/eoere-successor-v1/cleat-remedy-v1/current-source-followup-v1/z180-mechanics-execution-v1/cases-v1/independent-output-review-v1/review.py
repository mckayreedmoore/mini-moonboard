"""Read-only saved Z180 evidence audit; genuine admissions own operator arithmetic."""
from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
MECH = BASE / "adjusted-base-mechanics-v1"
E = BASE / "cleat-remedy-v1/current-source-followup-v1/z180-mechanics-execution-v1"
CASES = E / "cases-v1"
ROSTER = CASES / "result-v1.json"
ROSTER_SHA = "b37923501498fe35f500105df8b1ee601d7f4d4a553d80a109692565bac3400a"
PRIOR = MECH / "current-cases-v1/parent-verify-v1.py"
PRIOR_SHA = "084cece33e1d5b7563caff2965d35c77117c48f9c354ea02c127a643051346b2"
SEQUENCE = ["a12-forward", "a12-rear", "a12-left", "k12-right", "k12-rear", "a1-rear"]
GATE = E / "review-fix-v2/bridge.py"
GATE_SHA = "dc224c51a46f78433df614ce53b76e2a8f4b1a7ac4c436b7d0d212f784388f55"
INPUT = E / "inputs-v1/attempt01/inputs.json"
INPUT_SHA = "80b5c013b5c69e895c4286d8673f91143f57ac0b0b5243c7370450ec87a2565a"
INPUT_REVIEW = E / "inputs-review-v1/runs-v1/attempt01/receipt.json"
INPUT_REVIEW_SHA = "3b8b6e2dff8cc8d047cf53b7865137aea11d5085d86359041f6541c78e9dcedf"
METHOD = E / "readiness-v1/method-input.json"
METHOD_SHA = "2549e962a5feac6617e27e8f324b6b7b576beb0683289c5dcfd1ee4b5d588654"
SLOT = E / "readiness-v1/serialized-slot.json"
SLOT_SHA = "74b562805b1aad0b7461554c791b5526391f7f751ee6f7f555987da4c46f035c"
GEOMETRY = {"path": str(E.parent / "viewer-revision-v1/runs-v1/export01/layout.json"),
            "sha256": "4886a4bccaee43b93b23e521710b7d8b84dcb7b5ba627ef722694ceb79b7f319"}
RELEASE = dict.fromkeys(("candidate_accepted", "capacity_established", "climbing_released",
                         "complete_joint_acceptance", "fabrication_released", "structural_released"), False)
ABSOLUTE = {
    "/home/mckay-linux/repos/mini-moonboard-cleanup-backups-2026-10-08/eoere-aligned-wire-cutouts-v1.tar.gz.manifest.json":
        "688acf55c2884086ff14352d6d5ac6377b8f6bcebeb29c0e8275e4ffcdf3a15c",
    "/home/mckay-linux/repos/mini-moonboard/scripts/eoere_2026_adjustments.py":
        "136d7e63f1e337ef8a65421d22d4614b336697cb1b8556ff099995fe26a92821",
}
TABLES = {"common_shaft_bearing_actions", "common_shaft_section_cut_actions", "common_shaft_steel_port_actions",
          "common_shaft_wood_bearing_actions", "contact_actions", "floor_actions", "four_port_fitting_actions",
          "member_section_action_samples", "panel_generalized_coefficients", "panel_screw_actions", "shaft_end_capture_actions"}
LEGS = {"lumber_leg_left", "lumber_leg_right"}


def reused_metadata_helpers():
    data = (ROOT / PRIOR).read_bytes()
    if hashlib.sha256(data).hexdigest() != PRIOR_SHA:
        raise ValueError("frozen metadata helper changed")
    names = {"require", "sha", "canonical", "norm", "same"}
    nodes = [n for n in ast.parse(data).body if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in nodes} != names or len(nodes) != len(names):
        raise ValueError("exact five metadata helpers required")
    namespace = {"hashlib": hashlib, "json": json, "math": math}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(ROOT / PRIOR), "exec"), namespace)  # noqa: S102
    return {name: namespace[name] for name in names}


_metadata = reused_metadata_helpers()
require, sha, canonical, norm, same = (_metadata[name] for name in ("require", "sha", "canonical", "norm", "same"))


def ref(path, digest):
    return {"path": str(path), "sha256": digest}


def location(name, digest=None):
    item = Path(name)
    if item.is_absolute():
        require(ABSOLUTE.get(name) == digest, "unapproved absolute source")
        return item
    require(str(item) == name and str(item.resolve().relative_to(ROOT)) == name, "exact relative path required")
    return ROOT / item


def merge(*mappings):
    result = {}
    for mapping in mappings:
        for name, digest in mapping.items():
            require(name not in result or result[name] == digest, "source identity conflict: " + name)
            result[name] = digest
    return result


def source_inventories(method, manifest, field, pointer):
    method_ref = {str(METHOD): METHOD_SHA}
    require(len(method) == 1171 and len(manifest) == 1172 and len(field) == 1174, "distinct method/operator/field inventories")
    require(manifest == merge(method, method_ref), "operator source closure differs")
    require(field == merge(manifest, {v["path"]: v["sha256"] for v in pointer.values()}), "field source closure differs")


def vector_checks(response, admission, ndof):
    for name, key in (("q", "q"), ("gradient", "gradient_n")):
        values = response[key]
        require(len(values) == ndof and all(type(v) in (float, int) and math.isfinite(v) for v in values), "saved full finite vector")
        require(canonical(values) == response[name + "_canonical_sha256"] == admission[name + "_canonical_sha256"], "saved vector binding")
    gradient = max(abs(v) for v in response["gradient_n"])
    require(gradient == response["gradient_inf_n"] <= 1e-5 and response["generalized_residual_tolerance_n"] == 1e-5
            and response["converged"] is True, "unchanged inclusive full-gradient limit")
    same(gradient, admission["declared_law_checks"]["gradient_inf_n"])
    require(admission["declared_law_checks"]["full_signed_gradient_canonical_sha256"] == canonical(response["gradient_n"]), "signed gradient binding")
    return gradient


def identities(value, expected, path=()):
    if isinstance(value, dict):
        for key, item in value.items():
            child = (*path, key)
            if child == ("source_inputs", "cases"):
                continue
            if key in expected:
                require(item == expected[key], "foreign saved action identity")
            else:
                identities(item, expected, child)
    elif isinstance(value, list):
        for item in value:
            identities(item, expected, path)


def coordinate_checks(field, manifest):
    chart = manifest["coordinate_map"]
    n = manifest["final_ndof"]
    require(chart["schema"] == "eoere_first_order_owned_coordinate_map/v1" and chart["final_ndof"] == n == 9302
            and chart["rotation_scale"] == 1000. and chart["unused_legacy_two_port_fitting_indices"] == {}
            and chart["shaft_axial_spin_is_free_numerical_gauge_without_torque_reaction"] is True, "owned coordinate contract")
    require([len(chart[k]) for k in ("timber", "panels", "four_port_fittings", "shafts")] == [22, 6, 22, 100], "owned map census")
    owners = [*chart["timber"], *chart["panels"], *chart["four_port_fittings"], *chart["shafts"]]
    require(len(set(owners)) == 150 and set(owners) == set(field["body_identities"]), "owned map identities")
    indices = []
    for row in [*chart["timber"].values(), *chart["shafts"].values()]:
        indices.extend(i for node in row["index"] for i in node if i != -1)
    for name, row in chart["panels"].items():
        saved = field["panel_generalized_coefficients"][name]
        require({k: saved[k] for k in row} == row and saved["global_dof_start"] == row["indices"][0]
                and saved["coefficients"] == [field["response"]["q"][i] for i in row["indices"]], "panel map/q export binding")
        indices.extend(row["indices"])
    require({row["body"]: row for row in field["fitting_operator_descriptors"]} == chart["four_port_fittings"], "fitting map binding")
    for row in chart["four_port_fittings"].values():
        indices.extend(row["dof_indices"])
    require(len(indices) == len(set(indices)) == n and set(indices) == set(range(n)), "full disjoint owned coordinate coverage")
    return canonical(chart)


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def floor_checks(field, admission, raw, support):
    require(field["analytical_support_scenario"] == admission["support_contract"] == support
            and support["enabled_centroid_xy_hosts"] == sorted(LEGS) and support["no_slip_assumed_not_verified"] is True
            and support["physical_floor_capacity_established"] is False and support["no_vertical_tension_or_anchor"] is True, "unverified fixed-floor contract")
    hosts = set(raw["floor_footprints"])
    normals = dict.fromkeys(hosts, 0.)
    horizontal = {h: [0., 0., 0.] for h in hosts}
    wrench = [0.] * 6
    normal_rows, tangent_rows = [], []
    for row in field["floor_actions"]:
        host = row["first"]
        require(host in hosts and row["second"] == "floor", "floor owner")
        force = row["force_on_first_xyz_n"]
        require(len(force) == 3 and all(math.isfinite(v) for v in force), "finite floor force")
        if row["kind"] == "floor_normal":
            normal_rows.append(row)
            require(row["compression_n"] >= 0 and force == [0., 0., row["compression_n"]]
                    and row["point_xyz_mm"] in raw["floor_footprints"][host], "unilateral original normal point")
            normals[host] += row["compression_n"]
        else:
            require(row["kind"] == "floor_tangent", "floor action kind")
            tangent_rows.append(row)
            require(row["interaction_enabled"] is (host in LEGS) and force[2] == 0.
                    and (host in LEGS or force == [0., 0., 0.]), "only credited legs receive XY")
            horizontal[host] = [a+b for a,b in zip(horizontal[host], force, strict=True)]
        moment = cross([a-b for a,b in zip(row["point_xyz_mm"], [0., 750., 1100.], strict=True)], force)
        wrench = [a+b for a,b in zip(wrench, force+moment, strict=True)]
    require(len(normal_rows) == 32 and len(tangent_rows) == 16
            and Counter(r["first"] for r in normal_rows) == dict.fromkeys(hosts, 4)
            and len({r["id"] for r in field["floor_actions"]}) == 48, "32 original normals and 16 tangent rows")
    require(set(admission["normal_force_n_by_host"]) == set(admission["horizontal_force_xyz_n_by_host"]) == hosts, "eight floor host summaries")
    for host in hosts:
        same(normals[host], admission["normal_force_n_by_host"][host])
        for actual, expected in zip(horizontal[host], admission["horizontal_force_xyz_n_by_host"][host], strict=True):
            same(actual, expected)
    require(min(normals[h] for h in LEGS) > 1e-7, "credited leg unloaded")
    require(field["response"]["fixed_floor_support_v1"] == {**support, "normal_force_n_by_host": admission["normal_force_n_by_host"], "both_credited_legs_in_bearing": True}, "saved floor report binding")
    global_residual = field["global_equilibrium_residual_force_n"] + field["global_equilibrium_residual_moment_nmm"]
    require(global_residual == admission["declared_law_checks"]["global_residual_n_nmm"], "global residual binding")
    applied = admission["applied_load_checks"]["applied_wrench_about_reference_n_nmm"]
    # Saved global moments use the global origin; load-work moments use REFERENCE.
    reference_shift = cross([0., 750., 1100.], global_residual[:3])
    residual_at_reference = global_residual[:3] + [a-b for a,b in zip(global_residual[3:], reference_shift, strict=True)]
    for i, (floor, load, residual) in enumerate(zip(wrench, applied, residual_at_reference, strict=True)):
        require(abs(floor+load-residual) <= (1e-8 if i < 3 else 1e-5), "saved floor/applied wrench closure")
    require(norm(global_residual[:3]) < 1e-4 and norm(global_residual[3:]) < .1, "original global residual limits")
    return min(normals[h] for h in LEGS)


def command_checks(command, case, directory, phase):
    prefix = [str(ROOT / ".venv/bin/python3"), "-B", str(GATE), "--mode", phase]
    if phase == "run":
        expected = prefix + ["--run", "--case-id", case, "--wall-seconds", "900", "--inputs", str(INPUT), "--inputs-sha256", INPUT_SHA,
            "--input-review", str(INPUT_REVIEW), "--input-review-sha256", INPUT_REVIEW_SHA,
            "--method-input", str(METHOD), "--method-input-sha256", METHOD_SHA,
            "--slot", str(SLOT), "--slot-sha256", SLOT_SHA, "--out", str(directory / "field.json")]
    else:
        require(phase == "admit", "saved process phase")
        expected = prefix + ["--field", str(directory / "field.json"), "--out", str(directory / "admission.json")]
    require(command == expected, "exact source/method/slot/gate process command")


def chronology(producer, audit, previous_end):
    times = [datetime.datetime.fromisoformat(p[k]) for p,k in ((producer,"started_at_utc"), (producer,"finished_at_utc"),
                                                               (audit,"started_at_utc"), (audit,"finished_at_utc"))]
    require(all(t.utcoffset() == datetime.timedelta(0) for t in times), "actual UTC process timestamps")
    require(times == sorted(times) and (previous_end is None or previous_end <= times[0]), "serialized producer/admission phases")
    for p, start, end in ((producer,times[0],times[1]), (audit,times[2],times[3])):
        elapsed = p["elapsed_seconds"]
        require(math.isfinite(elapsed) and elapsed >= 0 and abs((end-start).total_seconds()-elapsed) < 1., "process elapsed timing")
    return times[-1]


class Audit:
    def __init__(self):
        self.sources = {}
        self.field_sources = {}

    def bind(self, reference):
        item = location(reference["path"], reference["sha256"])
        require(sha(item) == reference["sha256"], "reference bytes changed: " + str(item))
        require("bytes" not in reference or item.stat().st_size == reference["bytes"], "reference byte volume changed")
        self.sources = merge(self.sources, {reference["path"]: reference["sha256"]})
        return item

    def read(self, reference):
        return json.loads(self.bind(reference).read_bytes())

    def pins(self, mapping):
        self.sources = merge(self.sources, mapping)

    def case(self, case, raw, method, slot, previous_end, roster_row=None):
        directory = CASES / case / "attempt01"
        proof_name = "parent-pair-validation.json" if case == SEQUENCE[0] else "pair-validation.json"
        proof_path = ROOT / directory / proof_name
        proof_ref = ref(directory / proof_name, sha(proof_path))
        proof = self.read(proof_ref)
        field, admission = self.read(proof["field"]), self.read(proof["admission"])
        require(proof["field"]["path"] == str(directory / "field.json") and proof["admission"]["path"] == str(directory / "admission.json"), "own saved pair paths")
        self.bind(proof["gate"])
        require(proof["gate"]["path"] == str(GATE) and proof["gate"]["sha256"] == GATE_SHA
                and proof["success"] is True and proof["source_pin_count"] == 1174 and proof["release"] == RELEASE, "genuine own raw-pair validation")
        expected_schema = "eoere_parent_z180_first_pair_validation/v1" if case == SEQUENCE[0] else "eoere_serial_z180_raw_pair_validation/v1"
        require(proof["schema"] == expected_schema, "actual pair proof schema")
        require(field["schema"] == "eoere_z180_fixed_floor_candidate/v1"
                and admission["schema"] == "eoere_z180_fixed_floor_independent_field_admission/v1"
                and admission["unadopted_z180_equilibrium_and_recovery_pass"] is True
                and field["case_id"] == admission["case_id"] == proof["case_id"] == case
                and field["state_id"] == admission["state_id"] == proof["state_id"], "own Z180 field/admission identities")
        require(admission["admission_source_sha256"] == GATE_SHA and admission["source_path"] == str(GATE)
                and admission["input_raw_sha256"] == proof["field"]["sha256"] and admission["input_canonical_sha256"] == canonical(field), "raw/canonical own admission binding")
        for payload in (field, admission):
            require(payload["release"] == RELEASE and payload["unadopted_proposal"] is True
                    and payload["nut_spacer_proposal_included"] is False and payload["complete_joint_resistance"] is None, "unadopted unchanged scope")
            identities(payload, {k: field[k] for k in ("state_id", "case_id", "accessory_placement")})
        require(admission["no_candidate_preparation_or_solve_in_admission"] is True
                and admission["first_order_physical_applicability_established"] is False
                and admission["physical_demand_bounds_established"] is False, "bounded genuine admission scope")
        index = next(i for i,c in enumerate(raw["cases"]) if c["case_id"] == case)
        selected = {**raw, "case": raw["cases"][index]}
        selection = {"case_id": case, "only_case_selection_changed": True, "raw_input_canonical_sha256": canonical(raw),
            "selected_case_canonical_sha256": canonical(selected["case"]), "selected_index": index,
            "selected_input_canonical_sha256": canonical(selected), "source_path": "cases"}
        require(field["source_inputs"] == selected and field["source_case_selection"] == admission["source_case_selection"] == selection, "raw/selected saved source binding")
        require(field["source_input_review"] == {**ref(INPUT_REVIEW, INPUT_REVIEW_SHA), "input": ref(INPUT, INPUT_SHA),
                "inputs_canonical_sha256": canonical(raw), "source_case_selection": selection}, "independent input review binding")
        require(field["state_id"] == "eoere-z180-fixed-floor-" + canonical({"source_sha256": field["source_sha256"],
            "inputs": selected, "case": selected["case"], "counts": field["counts"], "mask_budget": 1, "max_iterations": 300})[:24], "source-bound state digest")
        require(set(admission["table_canonical_sha256"]) == TABLES, "complete adopted action-table bindings")
        for table, digest in admission["table_canonical_sha256"].items():
            require(canonical(field[table]) == digest, "own action table binding: " + table)
        require(admission["current_panel_operator_preparation_sha256"] == canonical(field["current_panel_operator_preparation"]), "panel preparation metadata binding")
        require(field["current_method_input"] == admission["method_input"] == ref(METHOD, METHOD_SHA)
                and field["proposal_geometry"] == admission["proposal_geometry"] == GEOMETRY, "own geometry/method binding")
        pointer = field["operator_bundle"]
        require(pointer == admission["operator_bundle"] and set(pointer) == {"manifest", "arrays"}, "operator pointers")
        for key, suffix in (("manifest", ".operators.json"), ("arrays", ".operators.npz")):
            require(pointer[key]["path"] == str(directory / ("field.json" + suffix)), "own operator paths")
            self.bind(pointer[key])
        manifest = self.read(pointer["manifest"])
        require(manifest["schema"] == "eoere_first_order_original_operator_bundle/v1" and manifest["arrays"] == pointer["arrays"]
                and manifest["captured_before_one_fresh_solve"] is True and manifest["historical_q_or_forces_used"] is False
                and manifest["original_support_rows_preserved_in_source_order"] is True, "saved original operator contract")
        source_inventories(method["source_sha256"], manifest["source_sha256"], field["source_sha256"], pointer)
        require(field["source_sha256"] == admission["source_sha256"], "admission source closure differs")
        self.pins(field["source_sha256"])
        self.field_sources = merge(self.field_sources, field["source_sha256"])
        require(manifest["case"] == selected["case"] and manifest["case"]["loads"] == field["body_applied_loads"]
                and manifest["body_descriptors"] == field["physical_body_descriptors"]
                and manifest["fitting_descriptors"] == field["fitting_operator_descriptors"]
                and manifest["original_operator_fingerprint_sha256"] == field["original_operator_fingerprint_sha256"] == admission["original_operator_fingerprint_sha256"], "operator source/maps/descriptors binding")
        require(field["reference_interaction_descriptors"] == [r["descriptor"] for key in ("groups", "contacts", "tangents") for r in manifest["partitions"][key]], "reference interaction map binding")
        gradient = vector_checks(field["response"], admission, manifest["final_ndof"])
        map_digest = coordinate_checks(field, manifest)
        for key, count in (("body_equilibrium_residuals",150), ("common_shaft_section_cut_actions",100),
                           ("common_shaft_steel_port_actions",88), ("panel_screw_actions",66),
                           ("panel_generalized_coefficients",6), ("shaft_end_capture_actions",200)):
            require(len(field[key]) == count, "physical action census: " + key)
        require({r["axis_id"] for r in field["common_shaft_section_cut_actions"]} == {r["axis_id"] for r in raw["shafts"]}
                and len({(r["axis_id"], r["surface_index"]) for r in field["common_shaft_steel_port_actions"]}) == 88
                and {r["axis_id"] for r in field["panel_screw_actions"]} == {r["source_screw_descriptor"]["axis_id"] for r in raw["hillman_rows"]}
                and len({r["id"] for r in field["shaft_end_capture_actions"]}) == 200, "unique shaft/steel-port/screw/end-action census")
        partitions = manifest["partitions"]
        require(field["counts"] == {"bearings": 416, "contacts": 1838, "dofs": 9302, "end_captures": 200,
                "fitting": 22, "floor_normals": 32, "floor_xy_components": 16, "panel": 6, "physical_bodies": 150,
                "shaft": 100, "timber": 22} and [len(partitions[k]) for k in ("contacts", "groups", "tangents")] == [1838, 482, 16]
                and len({r["descriptor"]["id"] for rows in partitions.values() for r in rows}) == 2336, "complete own interaction census")
        require(len(set(field["body_identities"])) == 150 and set(field["body_identities"]) == {r["id"] for r in raw["physical_owner_gravity_rows"]}
                and {r["body"] for r in field["body_equilibrium_residuals"]} == set(field["body_identities"]), "150 unique residual owners")
        force = max(norm(r["force_xyz_n"]) for r in field["body_equilibrium_residuals"])
        moment = max(norm(r["moment_about_reference_xyz_nmm"]) for r in field["body_equilibrium_residuals"])
        require(force < 1e-4 and moment < .1, "original body equilibrium limits")
        same(force, admission["declared_law_checks"]["maximum_body_force_norm_n"], tolerance=1e-8)
        same(moment, admission["declared_law_checks"]["maximum_body_moment_about_reference_norm_nmm"], tolerance=1e-8)
        minimum_leg = floor_checks(field, admission, raw, method["support_contract"])
        processes = []
        for phase, name in (("run", "process.json"), ("admit", "admission-process.json")):
            process_ref = ref(directory / name, sha(ROOT / directory / name))
            process = self.read(process_ref)
            command_checks(process["command"], case, directory, phase)
            require(process["case_id"] == case and process["exit_code"] == 0, "successful own process")
            require("release" not in process or process["release"] == RELEASE, "process release claim")
            if case == SEQUENCE[0]:
                require(process["schema"] == ("eoere_parent_z180_case_process_capture/v1" if phase == "run" else "eoere_parent_z180_admission_process_capture/v1")
                        and process["source_drift"] == [] and process["source_pins_verified_before_after"] == 1171, "first source process capture")
                if phase == "admit":
                    require(process["field"] == proof["field"] and process["admission"] == proof["admission"], "first process pair binding")
            else:
                require(process["schema"] == "eoere_serial_current_" + phase + "_process_capture/v1" and process["status"] == "FINISHED"
                        and process["pins_unchanged"] is True and process["pins_before"] == process["pins_after"], "serial source process capture")
                self.pins(process["pins_before"])
            for name, reference in process["logs"].items():
                require(Path(reference["path"]).parent == directory and Path(reference["path"]).name == name, "own exact process logs")
                self.bind(reference)
            require(len(process["logs"]) == 2, "both process logs")
            processes.append(process)
        current = field["current_execution"]
        require(current["command"] == field["execution"]["command"] == manifest["execution_command"] == processes[0]["command"]
                and current["loaded_driver_path"] == str(GATE) and current["loaded_driver_sha256"] == GATE_SHA
                and current["geometry"] == GEOMETRY and current["historical_q_or_forces_used"] is False
                and current["one_preparation_one_fixed_branch"] is True, "actual own execution/source command")
        require(current["slot_at_start"] == {"path": str(ROOT / SLOT), "sha256": SLOT_SHA, "record": slot}, "actual frozen serialized slot")
        require(field["execution"]["automatic_retry"] is False and field["execution"]["historical_q_used"] is False
                and field["execution"]["one_case"] is True and field["execution"]["one_preparation"] is True, "single fresh case without retry")
        if roster_row is not None:
            require(roster_row["case_id"] == case and roster_row["state_id"] == field["state_id"]
                    and roster_row["field_schema"] == field["schema"] and roster_row["admission_schema"] == admission["schema"]
                    and roster_row["declared_law_checks"] == admission["declared_law_checks"]
                    and roster_row["applied_load_checks"] == admission["applied_load_checks"]
                    and roster_row["support_contract"] == admission["support_contract"]
                    and roster_row["normal_force_n_by_host"] == admission["normal_force_n_by_host"]
                    and roster_row["unchanged_generalized_residual_tolerance_n"] == 1e-5
                    and roster_row["release"] == RELEASE and roster_row["raw_pair_gate_validation_success"] is True
                    and roster_row["raw_pair_gate_source_pin_count"] == 1174 and roster_row["unadopted_proposal"] is True
                    and roster_row["nut_spacer_proposal_included"] is False and roster_row["complete_joint_resistance"] is None
                    and roster_row["first_order_physical_applicability_established"] is False
                    and roster_row["physical_demand_bounds_established"] is False, "roster own numerical/pair summaries")
            require(roster_row["logs"] == {"producer": processes[0]["logs"], "admission": processes[1]["logs"]}, "roster logs binding")
            for label, process in zip(("producer", "admission"), processes, strict=True):
                for key in ("started_at_utc", "finished_at_utc", "elapsed_seconds"):
                    require(roster_row[label+"_"+key] == process[key], "roster process timing binding")
            for key, reference in (("field.json",proof["field"]), ("admission.json",proof["admission"]),
                                   (proof_name,proof_ref), ("operator_manifest",pointer["manifest"]), ("operator_arrays",pointer["arrays"])):
                require({k: roster_row["references"][key][k] for k in ("path", "sha256")}
                        == {k: reference[k] for k in ("path", "sha256")}, "roster exact pair/operator binding")
            require(roster_row["field_body_equilibrium"] == field["equilibrium_verification"]
                    and roster_row["counts"] == {**field["counts"], "saved_panel_blocks": 6, "saved_panel_screw_rows": 66,
                        "saved_shaft_section_cut_blocks": 100, "saved_steel_port_rows": 88}, "roster census/residual summary")
            same(roster_row["global_force_norm_n"], norm(field["global_equilibrium_residual_force_n"]))
            same(roster_row["global_moment_about_reference_norm_nmm"], norm(field["global_equilibrium_residual_moment_nmm"]))
        end = chronology(*processes, previous_end)
        if case != SEQUENCE[0]:
            require(proof["pins_before"] == proof["pins_after"] and proof["unadopted_proposal"] is True
                    and proof["nut_spacer_proposal_included"] is False and proof["complete_joint_resistance"] is None, "serial raw-pair scope/pins")
            self.pins(proof["pins_before"])
            start = datetime.datetime.fromisoformat(proof["started_at_utc"])
            end_pair = datetime.datetime.fromisoformat(proof["finished_at_utc"])
            require(end <= start <= end_pair, "raw pair validation follows admission")
            end = end_pair
        return {"case_id": case, "state_id": field["state_id"], "field": proof["field"], "admission": proof["admission"],
                "pair_validation": proof_ref, "gradient_inf_n": gradient, "maximum_body_force_norm_n": force,
                "maximum_body_moment_norm_nmm": moment, "minimum_credited_leg_normal_n": minimum_leg,
                "coordinate_map_canonical_sha256": map_digest, "field_source_pin_count": 1174, "method_source_pin_count": 1171}, end

    def verify(self):
        fixed = {str(GATE): GATE_SHA, str(INPUT): INPUT_SHA, str(INPUT_REVIEW): INPUT_REVIEW_SHA,
                 str(METHOD): METHOD_SHA, str(SLOT): SLOT_SHA, str(PRIOR): PRIOR_SHA, str(OWN.relative_to(ROOT)): sha(OWN),
                 str(OWN.with_name("test_review.py").relative_to(ROOT)): sha(OWN.with_name("test_review.py")),
                 str(OWN.with_name("controls.json").relative_to(ROOT)): sha(OWN.with_name("controls.json"))}
        roster_ref = ref(ROSTER, ROSTER_SHA)
        roster = self.read(roster_ref)
        require(roster["schema"] == "eoere_unadopted_z180_six_case_serial_capture/v1"
                and roster["status"] == "SIX_FRESH_Z180_CASES_INDEPENDENTLY_ADMITTED_AND_RAW_PAIR_VALIDATED"
                and roster["case_sequence"] == SEQUENCE and len(roster["cases"]) == 6
                and roster["execution_serialized"] is True and roster["no_retries_or_alternative_masks"] is True
                and roster["all_exact_raw_pairs_gate_validated"] is True
                and roster["all_unadopted_z180_equilibrium_and_recovery_gates_pass"] is True
                and roster["release"] == RELEASE and roster["unadopted_proposal"] is True
                and roster["nut_spacer_proposal_included"] is False and roster["complete_joint_resistance"] is None
                and roster["optional_extra_grid"] is False and roster["proposal_geometry"] == GEOMETRY, "exact frozen six-case roster")
        require(roster["exact_pins_before"] == roster["exact_pins_after"], "roster capture source drift")
        self.pins(roster["exact_pins_before"])
        for key in ("capture_driver", "reused_stdlib_capture_helper"):
            self.bind(roster[key])
        for row in roster["cases"]:
            for reference in row["references"].values():
                self.bind(reference)
            for logs in row["logs"].values():
                for reference in logs.values():
                    self.bind(reference)
        for name, digest in fixed.items():
            self.bind(ref(name, digest))
        raw, method, slot = [json.loads((ROOT / p).read_bytes()) for p in (INPUT, METHOD, SLOT)]
        require(method["schema"] == "eoere_z180_fixed_floor_method_inputs/v1" and method["release"] == RELEASE
                and method["input"] == ref(INPUT, INPUT_SHA) and method["input_review"] == ref(INPUT_REVIEW, INPUT_REVIEW_SHA)
                and method["geometry"] == GEOMETRY and len(method["source_sha256"]) == 1171, "exact own method")
        require(slot["schema"] == "eoere_parent_z180_serialized_force_slot/v1" and slot["maximum_concurrent_runs"] == 1
                and slot["case_sequence"] == SEQUENCE and slot["release"] == RELEASE, "parent serial roster")
        self.pins(method["source_sha256"])
        before = dict(self.sources)
        for name, digest in before.items():
            require(sha(location(name, digest)) == digest, "source before mismatch: " + name)
        summaries, end = [], None
        for case, row in zip(SEQUENCE, roster["cases"], strict=True):
            summary, end = self.case(case, raw, method, slot, end, row)
            summaries.append(summary)
        require(len(self.field_sources) == roster["closure_field_admission_source_pin_union_count"] == 1184
                and roster["closure_field_admission_source_pin_union_verified"] is True, "six-case source/operator union")
        same(max(r["gradient_inf_n"] for r in summaries), roster["maxima"]["admitted_gradient_inf_n"])
        same(min(r["minimum_credited_leg_normal_n"] for r in summaries), roster["minimum_credited_leg_normal_n"])
        require(sum(r["references"]["field.json"]["bytes"] for r in roster["cases"]) == roster["total_field_bytes"]
                and sum(r["references"][k]["bytes"] for r in roster["cases"] for k in ("operator_arrays", "operator_manifest")) == roster["total_operator_bytes"], "retained field/operator volume")
        for name, digest in self.sources.items():
            require(sha(location(name, digest)) == digest, "source after mismatch: " + name)
        require(sha(ROOT / PRIOR) == PRIOR_SHA, "frozen helper changed during review")
        return {"schema": "eoere_z180_saved_six_case_independent_output_review/v1", "status": "PASS_IN_BOUNDED_SAVED_FIELD_SCOPE",
                "success": "independent_saved_z180_six_case_metadata_checks_pass", "case_sequence": SEQUENCE,
                "cases": summaries, "source_sha256": self.sources, "verified_unique_source_pins": len(self.sources),
                "roster": roster_ref, "field_admission_source_union_count": len(self.field_sources),
                "findings": [], "numerical_operator_and_recovery_arithmetic_relied_on": ref(GATE, GATE_SHA),
                "no_candidate_preparation_solver_gate_import_native_CAD_or_BREP_query": True, "release": RELEASE,
                "unadopted_proposal": True, "nut_spacer_proposal_included": False, "complete_joint_resistance": None,
                "limits": ["Saved metadata audit relies on each genuine own admission for full operator/work/recovery arithmetic.",
                           "Distributed panel RHS remains source-authenticated capture rather than independent regeneration.",
                           "First-order applicability, physical floor capacity and complete-joint resistance remain unestablished."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with args.out.open("x") as stream:
        result = Audit().verify()
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "case_count": len(result["cases"]), "verified_unique_source_pins": result["verified_unique_source_pins"]}))


if __name__ == "__main__":
    main()
