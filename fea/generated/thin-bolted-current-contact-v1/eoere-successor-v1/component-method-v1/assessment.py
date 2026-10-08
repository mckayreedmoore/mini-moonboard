"""Compact successor component receipt, after exact fresh field admission only.

Pure reductions reuse source-bound methods. No constructor, CAD, stiffness
assembly, solve, historical action or historical admission is consumed here.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

from scripts import thin_bolted_common_shaft_steel as shaft_ports
from scripts import thin_bolted_panel_coupled as panel

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PACKET = OWN.parent.parent
GATE = PACKET / "four-port-method-v1/first_order_admission.py"
STEEL = PACKET / "steel-shaft-comparison-v1/comparison.py"
GROSS = OWN.with_name("gross_members.py")
FIELD_SCHEMA = "eoere_first_order_common_shaft_four_port_candidate/v2"
ADMISSION_SCHEMA = "eoere_first_order_independent_field_admission/v1"
SUCCESS = "independent_eoere_original_law_gradient_work_and_equilibrium_checks_pass"
RELEASE = {key: False for key in ("candidate_accepted", "complete_joint_acceptance", "capacity_established",
    "fabrication_released", "structural_released", "climbing_released")}
PINS = {"scripts/thin_bolted_panel_coupled.py": "abd6da1911ec79ec25b57fc2a5cc20b9e687057a15b6df2f5e8fb292a42c6bd0",
        "scripts/thin_bolted_common_shaft_steel.py": "4b28f7a055c50dc127569b7df387f8e8d973f74080d2937ceb5db356a89d9952",
        "fea/current_response_materials.py": "72af0456272d91282928014d8fde557d347e36df6b7bdf23bcc41ef923d0d135",
        "scripts/thin_bolted_panel_mechanics.py": "472eef63a8af59367533028008c68e4f7e32780e49891499154ba2950559a3aa",
        str(GROSS.relative_to(ROOT)): "01aaf22c8b2cf93430e7bbce4768260efea39bed3d527b8f5486ba4e38e32258",
        str((PACKET/"bolt-placement-v1/input-feasibility.json").relative_to(ROOT)):
            "5d24d39ec3775fc448ca4c02589aa52cf91d5cf1587878abb585d9bd746204b6",
        str((PACKET/"cleat-corners-v1/lower-bolt-z-v2.json").relative_to(ROOT)):
            "a615cb247cf48426f139cc3149ff658d38a96861c3166d0fa27e5912d650c04b"}
PINS.update({str(panel.panel_method.LEGACY_METHOD.relative_to(ROOT)):
    "7c8aadbc15fe3fca1932c9bf32ee1029bed7e4ac10ccca74368f95c2bf80bde8",
    str(panel.panel_method.NDS_PDF.relative_to(ROOT)): panel.panel_method.NDS_SHA,
    str(panel.panel_method.APA_PDF.relative_to(ROOT)): panel.panel_method.APA_SHA})


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, "component source differs: "+path)


def join(pins, extra):
    for path, digest in extra.items():
        require(path not in pins or pins[path] == digest, "component source join conflict: "+path)
        pins[path] = digest


def load(path, digest, name):
    require(sha(path) == digest, "loaded reduction source differs")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(sha(path) == digest, "reduction changed during import")
    return module


def identity_check(field, row, *, required=True):
    for key in ("state_id", "case_id", "accessory_placement"):
        require((not required and key not in row) or row.get(key) == field[key], "mixed component "+key)


def unique(rows, key, label):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), "duplicate "+label)
    return result


def capture_diagnostics(row, shaft):
    """Own nominal annulus N/A only; point-only capture has no pressure couple."""
    ends = {end["end"]: end for end in shaft["ends"]}
    end = row["end"]
    require(end == ends[end["end"]] and row["axis_id"] == shaft["axis_id"]
            and row["first"] == shaft["body"] and row["second"] == end["host"], "own capture/end source differs")
    p, axis = np.asarray(shaft["point"]), np.asarray(shaft["basis"])[0]
    require(np.max(abs(p+axis*end["pressure_face_s_mm"]-row["point_xyz_mm"])) < 1e-7
            and np.max(abs(p+axis*end["support_s_mm"]-row["host_support_point_xyz_mm"])) < 1e-7,
            "own capture pressure/receiving planes differ")
    n = float(row["compression_n"])
    require(math.isfinite(n) and n >= 0. and np.max(abs(np.asarray(row["force_on_first_xyz_n"])
            -n*np.asarray(end["direction_on_shaft_xyz"]))) < 1e-7, "own capture signed force differs")
    hardware = shaft["source_axis"]["hardware_scenario"]
    outer, inner = hardware["washer_od_mm"], hardware["washer_id_mm"]
    require(outer > inner > 0., "positive own nominal washer annulus required")
    area = math.pi*(outer*outer-inner*inner)/4
    return {"id": row["id"], "axis_id": shaft["axis_id"], "end": end["end"], "host": end["host"],
            "compression_n": n, "nominal_full_annulus_area_mm2": area,
            "nominal_full_annulus_average_pressure_mpa": n/area,
            "actual_pressure_couple_nmm": None, "actual_contact_area_or_peak_pressure": None,
            "washer_bending_nut_head_or_wood_seat_resistance": None,
            "point_capture_free_couple_is_annular_pressure_couple": False}


def own_port_joins(field, fitting):
    """External forces at each exact kinematic port, separate from internal roots."""
    body = fitting["body"]
    result = []
    for port in fitting["port_actions"]:
        point = np.asarray(port["point_xyz_mm"])
        force, moment, ids = np.zeros(3), np.zeros(3), []
        for row in field["common_shaft_steel_port_actions"]:
            if row["host"] == body and row["flange"] == port["port_id"]:
                f = np.asarray(row["force_on_steel_xyz_n"])
                force += f
                moment += np.asarray(row["moment_on_steel_at_point_xyz_nmm"])+np.cross(np.asarray(row["point_xyz_mm"])-point, f)
                ids.append("shaft-surface/"+row["axis_id"]+"/"+str(row["surface_index"]))
        for row in field["contact_actions"]:
            if row["kind"] == "flange_contact" and row["first"] == body and row["flange"] == port["port_id"]:
                f = np.asarray(row["force_on_first_xyz_n"])
                force += f
                moment += np.cross(np.asarray(row["point_xyz_mm"])-point, f)
                ids.append(row["id"])
        result.append({"port_id": port["port_id"], "own_external_action_ids": ids,
            "own_external_force_xyz_n": force.tolist(), "own_external_couple_about_port_xyz_nmm": moment.tolist(),
            "external_minus_elastic_required_force_xyz_n": (force-port["external_force_required_at_port_xyz_n"]).tolist(),
            "external_minus_elastic_required_couple_xyz_nmm": (moment-port["external_couple_required_at_port_xyz_nmm"]).tolist()})
    return result


def steel_surface_projection(source):
    """Pure argument shape projection of new88 exact ports, no old layout."""
    axes = []
    for shaft in source["shafts"]:
        bindings = [row for row in source["fitting_port_bindings"] if row["axis_id"] == shaft["axis_id"]]
        ports = []
        for binding in bindings:
            surfaces = [s for s in shaft["surfaces"] if s["kind"] == "steel"
                        and s["host"] == binding["angle_id"] and s["flange"] == binding["model_port_id"]]
            require(len(surfaces) == 1, "each new binding requires one actual own steel surface")
            ports.append({"angle_id": binding["angle_id"], "flange": binding["model_port_id"],
                          "entry_xyz_mm": binding["entry_xyz_mm"], "receiver": surfaces[0]["receiver"]})
        axes.append({"id": shaft["axis_id"], "attachments": ports})
    return {"installed_axes": axes}


def panel_slice_projection(field):
    """Declared exact key projection to the old pure q-slice API, no old state."""
    orders = {row["basis_order_per_direction"] for row in field["panel_generalized_coefficients"].values()}
    require(len(orders) == 1, "uniform source panel basis required")
    coefficients = copy.deepcopy(field["panel_generalized_coefficients"])
    for row in coefficients.values():
        require(row["indices"] == list(range(row["global_dof_start"], row["global_dof_start"]+len(row["coefficients"])))
                and row["thickness_mm"] == panel.panel_method.CAT,
                "reused panel slice API requires authentic contiguous indices/CAT thickness")
        row["coefficients_mm"] = row["coefficients"]
    return {"parameters": {"panel_intervals": orders.pop()-3}, "response": field["response"],
            "panel_generalized_coefficients": coefficients}


def panel_reductions(field, *, samples=41):
    """Exact q-slice adapter to the unchanged six-panel pure field functions."""
    if "panel_generalized_coefficients" not in field:
        return {"status": "UNAVAILABLE", "missing": "genuine panel coefficient slices/basis/global map export",
                "panel_ids": field["source_inputs"]["panel_ids"], "panel_diagnostics": []}, {}
    sources = {str(panel.ASSESSMENT.relative_to(ROOT)): panel.ASSESSMENT_SHA,
        str(panel.DATUMS.relative_to(ROOT)): panel.DATUMS_SHA,
        str(panel.panel_method.INTEGRATED.relative_to(ROOT)): panel.panel_method.INTEGRATED_SHA,
        str(panel.panel_method.NDS_PDF.relative_to(ROOT)): panel.panel_method.NDS_SHA,
        str(panel.panel_method.APA_PDF.relative_to(ROOT)): panel.panel_method.APA_SHA}
    legacy = panel.panel_method.LEGACY_METHOD
    sources[str(legacy.relative_to(ROOT))] = PINS[str(legacy.relative_to(ROOT))]
    verify(sources)
    projection = panel_slice_projection(field)
    panels = panel.prepared_datums(projection, json.loads(panel.ASSESSMENT.read_bytes()),
        json.loads(panel.DATUMS.read_bytes()), json.loads(panel.panel_method.INTEGRATED.read_bytes()))
    for name, sheet in panels.items():
        geometry = field["panel_generalized_coefficients"][name]["geometry"]
        require(np.max(abs(np.asarray(geometry["origin"])-sheet["geometry"]["origin"])) < 1e-7
                and np.max(abs(np.asarray(geometry["axes"])-sheet["geometry"]["axes"])) < 1e-8,
                "unchanged source panel origin/axes differ from the new field chart")
    results = [{"panel": name,
        "resolved_section_diagnostics": panel.panel_method.resolved_section_references(sheet, sheet["q"], samples),
        "deformation_diagnostics": panel.deformation_diagnostics(sheet, sheet["q"], samples)}
        for name, sheet in panels.items()]
    return {"status": "SAME_NEW_STATE_CONDITIONAL_REFERENCE", "panel_diagnostics": results,
            "sample_count_per_axis": samples, "old_state_validator_or_old_demand_called": False}, sources


def reduce_field(field, steel, gross, reference_axes, *, samples=41):
    """Caller-only pure reduction; this function itself does not admit a field."""
    require(field["schema"] == FIELD_SCHEMA and field["response"].get("converged") is True
            and field["release"] == RELEASE, "fresh converged unreleased successor schema required")
    source = field["source_inputs"]
    shafts = unique(source["shafts"], "axis_id", "physical shaft")
    fitting = unique(field["four_port_fitting_actions"], "body", "fitting recovery")
    descriptors = unique(field["fitting_operator_descriptors"], "body", "fitting descriptor")
    cuts = unique(field["common_shaft_section_cut_actions"], "axis_id", "shaft cut table")
    screws = unique(field["panel_screw_actions"], "axis_id", "Hillman axis")
    expected_screws = unique(source["hillman_rows"], "id", "source Hillman axis")
    poses = unique(source["fitting_poses"], "id", "fitting pose")
    require(len(shafts) == 100 and len(fitting) == 22 and set(fitting) == set(descriptors) == set(poses)
            and set(cuts) == set(shafts) and len(screws) == 66 and set(screws) == set(expected_screws)
            and len(source["timber_rows"]) == 22 and len(source["panel_ids"]) == 6,
            "complete22/100/66/22/6 successor census required")
    require(set(reference_axes) == set(shafts) and all(canonical(shaft["source_axis"]) == canonical(reference_axes[key])
            for key, shaft in shafts.items()), "admitted shafts must join exact final occupied source axes")
    for table in ("panel_screw_actions", "contact_actions", "floor_actions", "common_shaft_bearing_actions",
                  "shaft_end_capture_actions", "common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions"):
        for row in field[table]:
            identity_check(field, row)
    for row in [*fitting.values(), *cuts.values()]:
        identity_check(field, row, required=False)
    capture = [capture_diagnostics(row, shafts[row["axis_id"]]) for row in field["shaft_end_capture_actions"]]
    require(len(capture) == 200 and len({(r["axis_id"], r["end"]) for r in capture}) == 200,
            "all200 own washer/end captures required")
    surfaces = shaft_ports.aggregate_steel_ports(steel_surface_projection(source),
        field["common_shaft_bearing_actions"], field["shaft_end_capture_actions"])
    require(len(surfaces) == 88, "all88 own steel bore/washer paths required")
    gross.own.verify_steel_aliases(field, surfaces)
    require(len(field["common_shaft_wood_bearing_actions"]) == 120,
            "all120 own timber receiver paths required")
    angles = []
    for body, recovery in fitting.items():
        bindings = [r for r in source["fitting_port_bindings"] if r["angle_id"] == body]
        require(len(bindings) == 4 and {r["model_port_id"] for r in bindings}
                == {r["port_id"] for r in recovery["port_actions"]}, "four exact own port/shaft bindings required")
        angles.append({"body": body, "duty_id": poses[body]["duty_id"], "physical_axis_ids": sorted(r["axis_id"] for r in bindings),
            "loaded_strip_comparison": steel.fitting_strip_comparisons(recovery, descriptors[body]),
            "own_external_port_joins": own_port_joins(field, recovery),
            "complete_group_heel_hole_prying_or_corner_resistance": None})
    shaft_comparisons = [steel.shaft_circle_comparisons(cuts[key], reference_axes[key])
                         for key, shaft in shafts.items()]
    screw_refs = []
    for key, action in screws.items():
        src = expected_screws[key]
        require(action["first"] == action["panel"] == src["first"] and action["second"] == action["receiver"] == src["second"]
                and np.max(abs(np.asarray(action["point_xyz_mm"])-src["point_xyz_mm"])) < 1e-7
                and np.max(abs(np.asarray(src["basis"]).T @ action["local_force_n"]-action["force_on_receiver_xyz_n"])) < 1e-7,
                "same own screw source/signed simultaneous world force differs")
        screw_refs.append(panel.screw_references(action, panel.panel_method.CAT))
    corners = []
    for side in ("left", "right"):
        cleat = "eoere_cleat_"+side
        axes = [s["axis_id"] for s in shafts.values() if cleat in s["source_axis"]["receivers"]]
        require(len(axes) == 4, "complete four-axis exterior corner path required")
        members = [cleat, "base_side_"+side, "base_post_outer_"+side, "base_header"]
        contacts = [r["id"] for r in field["contact_actions"] if r["first"] in members and r["second"] in members]
        corners.append({"duty_id": "exterior-cleat-corner-"+side, "members": members,
            "physical_axis_ids": sorted(axes), "own_direct_contact_ids": contacts,
            "complete_corner_splitting_group_or_bearing_resistance": None})
    panel_result, panel_pins = panel_reductions(field, samples=samples)
    return {"angle_duties": angles, "exterior_cleat_corners": corners,
        "own_steel_surface_wrenches": surfaces,
        "own_wood_bearing_resultants_from_admitted_field": copy.deepcopy(field["common_shaft_wood_bearing_actions"]),
        "complete_wood_bolt_yield_end_edge_Cdelta_group_splitting_resistance": None,
        "own_shaft_circle_comparisons": shaft_comparisons, "own_washer_capture_diagnostics": capture,
        "simultaneous_Hillman_actions_and_generic_references": screw_refs,
        "six_panel_reductions": panel_result, "fresh_gross_member_diagnostics": gross.member_witnesses(field)}, panel_pins


def consume(field_path, receipt_path, *, expected_field_sha256, admission_sha256, steel_sha256, samples=41):
    """Authenticate exact bytes first; no predecessor admission/schema projection."""
    pins = {**PINS, str(OWN.relative_to(ROOT)): LOADED_SHA,
        str(GATE.relative_to(ROOT)): admission_sha256, str(STEEL.relative_to(ROOT)): steel_sha256}
    verify(pins)
    payload = Path(field_path).read_bytes()
    require(hashlib.sha256(payload).hexdigest() == expected_field_sha256, "expected fresh field bytes differ")
    receipt_bytes = Path(receipt_path).read_bytes()
    receipt_sha = hashlib.sha256(receipt_bytes).hexdigest()
    receipt = json.loads(receipt_bytes)
    require(receipt["schema"] == ADMISSION_SCHEMA and receipt.get(SUCCESS) is True, "new numerical admission required")
    gate = load(GATE, admission_sha256, "eoere_component_fresh_gate")
    field, admitted_pins = gate.require_admitted_payload(payload, receipt, admission_sha256=admission_sha256)
    original = canonical(field)
    require(original == canonical(json.loads(payload)), "gate changed admitted payload")
    join(pins, admitted_pins)
    steel = load(STEEL, steel_sha256, "eoere_component_steel")
    gross = load(GROSS, PINS[str(GROSS.relative_to(ROOT))], "eoere_component_gross")
    join(pins, gross.source_pins())
    steel_contract = steel.source_contract()
    join(pins, steel_contract["source_sha256"])
    reference_axes = unique(steel_contract["geometry"]["axes"], "id", "occupied source axis")
    reductions, extra = reduce_field(field, steel, gross, reference_axes, samples=samples)
    join(pins, extra)
    join(pins, {str(Path(field_path).resolve().relative_to(ROOT)): expected_field_sha256,
                str(Path(receipt_path).resolve().relative_to(ROOT)): receipt_sha})
    verify(pins)
    require(canonical(field) == original, "component methods changed admitted field")
    return {"schema": "eoere_same_state_conditional_component_receipt/v1",
        **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
        "raw_field_sha256": expected_field_sha256, "field_admission_receipt_sha256": receipt_sha,
        "fresh_gate_sha256": admission_sha256, "source_sha256": pins, "component_reductions": reductions,
        "enclosed_unlabeled_recovery_table_canonical_sha256": {key: canonical(field[key]) for key in
            ("four_port_fitting_actions", "common_shaft_section_cut_actions")},
        "limits": ["First-order spring-model actions are conditional, not established physical demand bounds.",
            "Actual steel/Fy/Fu/bolt grade, delivered root/shank and complete heel/hole/group mechanisms remain unavailable.",
            "N/A is nominal annulus average only; annular couples/contact area/peak pressure and washer resistance are unavailable.",
            "Hillman generic head/withdrawal comparisons do not qualify screw steel/lateral/edge/punching or product capacity.",
            "Resolved panel peaks and fresh sampled gross-member references do not qualify changed net cuts, fracture, bracing or finite contact applicability.",
            "Cleat/post99.2mm overlap cannot fit both full7D ends, but3.5D softwood tension minimum/reducedCdelta and signed loaded-end context remain distinct; posttop38.9/cleatbottom60.3mm atZ200 and nominal bore/screw gap0.340625mm are not delivered acceptance.",
            "Mainfar65.0875mm/7D66.675mm=.97619 is an end-only marker, not completeCdelta/group strength. Rim29.108mm edge vs4D38.1mm needs signed loaded-direction/beveled geometry applicability."],
        "disposition": "SAME_NEW_STATE_CONDITIONAL_COMPONENT_FINDINGS", "release": copy.deepcopy(RELEASE)}


def main():
    command = list(sys.orig_argv)
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("field", "receipt", "out"):
        parser.add_argument("--"+name, type=Path, required=True)
    for name in ("expected-field-sha256", "admission-sha256", "steel-sha256"):
        parser.add_argument("--"+name, required=True)
    options = parser.parse_args()
    require(not options.out.exists(), "preserve existing component receipt")
    result = consume(options.field, options.receipt, expected_field_sha256=options.expected_field_sha256,
        admission_sha256=options.admission_sha256, steel_sha256=options.steel_sha256)
    result["execution"] = {"sys_orig_argv": command, "PYTHONPATH": os.environ.get("PYTHONPATH"),
                           "cwd": str(Path.cwd()), "python": sys.version, "no_CAD_K_or_solve": True}
    with options.out.open("x") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(options.out), "state_id": result["state_id"], "release": RELEASE}))


if __name__ == "__main__":
    main()
