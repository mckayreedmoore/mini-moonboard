#!/usr/bin/env python3
"""Authenticate and reproduce frozen center receiver boundary actions."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import boundary as b

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PARENT = "docs/wood-joints-mvp/hypotheses/"
FREEZE = PARENT+"upper-frame-joint-review-2026-09-30/freeze.json"
FREEZE_SHA = "d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73"
EXPORT = PARENT+"mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/produce.py"
EXPORT_SHA = "0e6aa1b0ec50e3137d2f431f79365de899d109a5d5c61d37de344c9596681fe8"
BACKING = PARENT+"current-center-kicker-backing-duty-2026-10-01/"
BACKING_SHA = "79f7058b9067d4c0a34206d04f6c6580c005a603a42388dd00bb54ac070979ad"
BACKING_PINS_SHA = "6bac530fd7374ddc40e3948f885befcbb5c2ebead61a4c6e17df4e46b5198d6d"
GRAPH = PARENT+"evaluation-resume-2026-09-24/complete-contact-graph-attempt02.json"
GATES = ("mpc_interval_checks_passed", "springa_law_checks_passed",
         "retained_bilateral_checks_passed", "selected_floor_complementarity_passed",
         "inactive_floor_tangent_no_restraint_or_reaction_passed", "raw_balance_passed",
         "rounding_interval_balance_passed")
FALSE_FLAGS = ("qualified_for_design", "mechanical_acceptance", "joint_demand_accepted",
               "floor_capacity_established", "friction_qualified")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_pin(root, pin):
    path = root/pin["path"]
    b.require(path.resolve().is_relative_to(root.resolve()), "source path outside repository")
    b.require(digest(path) == pin["sha256"], "source hash changed: "+pin["path"])
    if "size_bytes" in pin:
        b.require(path.stat().st_size == pin["size_bytes"], "source size changed")
    return {"path": pin["path"], "sha256": pin["sha256"], "size_bytes": path.stat().st_size}


def checked_case(case, files, model, response, audit, terminal):
    for key, value in (("candidate", b.CANDIDATE), ("geometry_revision_id", b.REVISION), ("case_id", case)):
        b.require(model[key] == response[key] == value, "source case/candidate/revision differs")
    b.require(all(response[key] is False for key in FALSE_FLAGS), "source qualification boundary changed")
    for kind, key in (("model", "source_input_model_json_sha256"),
                      ("deck", "source_input_deck_sha256"), ("native_data", "native_data_sha256")):
        b.require(response[key] == files[kind]["sha256"], "response input hash differs")
    b.require(audit["status"] == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS"
              and audit["source_model_sha256"] == files["model"]["sha256"]
              and audit["source_response_sha256"] == files["response"]["sha256"]
              and audit["physical_tolerances_N_Nmm"] == [0.1, 2.0], "source all-body audit differs")
    b.require(terminal.get("conditional_case_forces_usable",
                          terminal.get("response_usable_for_conditional_joint_checks")) is True,
              "terminal conditional response unusable")
    terminal_response = terminal.get("response_sha256", terminal.get("files_sha256", {}).get("response.json"))
    b.require(terminal["case_id"] == case
              and terminal_response == files["response"]["sha256"],
              "terminal case/response differs")
    b.require(tuple(x["load_factor"] for x in response["increments"]) == b.FACTORS
              == tuple(x["load_factor"] for x in audit["increments"]), "source state coverage differs")
    b.require(all(all(inc[key] is True for key in GATES) for inc in response["increments"]),
              "source increment gate failed")


def checked_authority(criteria, lane):
    b.require(criteria["candidate"] == lane["candidate"] == b.CANDIDATE
              and lane["current_development_revision"]["revision_id"] == b.REVISION,
              "current authority candidate/revision differs")
    rows = criteria["legacy_criteria"]+criteria["additional_candidate_obligations"]
    ids = [row.get("legacy_id", row.get("id")) for row in rows]
    b.require(len(rows) == len(set(ids)) == 47 and all(row["status"] == "pending" for row in rows),
              "pending criterion authority differs")
    b.require(all(value is False for value in criteria["release_flags"].values())
              and all(value is False for value in lane["release_flags"].values()),
              "authority release boundary changed")
    return {"criterion_count": len(rows), "pending_criterion_ids": sorted(ids),
            "all_pending": True, "release_flags": lane["release_flags"]}


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n").encode()


def build(root=ROOT, here=HERE):
    sources = {}

    def pin(path, expected):
        row = checked_pin(root, {"path": path, "sha256": expected})
        previous = sources.setdefault(path, row)
        b.require(previous == row, "conflicting source binding")
        return root/path

    freeze = json.loads(pin(FREEZE, FREEZE_SHA).read_text())
    b.require(freeze["candidate"] == b.CANDIDATE and freeze["geometry_revision_id"] == b.REVISION
              and set(freeze["cases"]) == {"a1-rear", "a12-rear", "k12-rear"}, "freeze scope changed")
    backing = json.loads(pin(BACKING+"backing-duty.json", BACKING_SHA).read_text())
    backing_pins = json.loads(pin(BACKING+"source-pins.json", BACKING_PINS_SHA).read_text())
    for row in backing_pins["sources"]:
        checked = checked_pin(root, row)
        previous = sources.setdefault(row["path"], checked)
        b.require(previous == checked, "conflicting backing source binding")
    b.require(backing["source_pins_sha256"] == BACKING_PINS_SHA
              and backing["candidate"] == b.CANDIDATE and backing["geometry_revision_id"] == b.REVISION,
              "backing source binding differs")
    authority = checked_authority(json.loads((root/"docs/wood-joints-mvp/criteria.json").read_text()),
                                  json.loads((root/"wood-joints-candidate.json").read_text()))
    export_path = pin(EXPORT, EXPORT_SHA)
    spec = importlib.util.spec_from_file_location("center_boundary_frozen_export", export_path)
    b.require(spec is not None and spec.loader is not None, "export helper unavailable")
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    graph = json.loads((root/GRAPH).read_text())
    b.require(graph["revision_id"] == b.REVISION, "geometric graph revision differs")
    cases, states, first_inventory, graph_ports = {}, [], None, None
    for case, files in sorted(freeze["cases"].items()):
        for row in files.values():
            pin(row["path"], row["sha256"])
        model, response, audit, terminal = [json.loads((root/files[key]["path"]).read_text())
                                            for key in ("model", "response", "all_body_audit", "terminal")]
        checked_case(case, files, model, response, audit, terminal)
        bindings = b.inventory(model)
        if first_inventory is None:
            first_inventory = bindings
            graph_ports = b.geometry_ports(graph, bindings, backing["duties"]["frame_duties"])
        b.require(bindings == first_inventory, "cross-case boundary topology differs")
        counts = {"interfaces": len(bindings), "scalar_rows": sum(len(r["source_indices"]) for r in bindings),
                  "body_load_nodes": sum(len(model["physical_body_loads"][body]) for body in b.MEMBERS)}
        b.require(counts == {"interfaces": 212, "scalar_rows": 250, "body_load_nodes": 316},
                  "frozen center census differs")
        cases[case] = {"source_files": files, "inventory": bindings, "counts": counts,
                       "source_terminal_status": terminal["status"],
                       "source_floor_mask": model["floor_selected_original_row_indices"]}
        for index, inc in enumerate(response["increments"]):
            state = b.checked_state(method, model, inc, audit["increments"][index], bindings)
            b.require((state["internal_interface_count"], state["boundary_interface_count"],
                       len(state["endpoint_actions"]), len(state["body_load_actions"])) == (40, 172, 252, 316),
                      "frozen center action point census differs")
            states.append({"case_id": case, "increment_index": index, **state})
    for path in sorted([*here.glob("*.py"), here/"plan.md", here/"README.md"]):
        pin(str(path.relative_to(root)), digest(path))
    pins = {"schema": "center_receiver_boundary_source_pins/v1", "sources": [sources[p] for p in sorted(sources)]}
    report = {"schema": "center_receiver_whole_boundary_actions/v1",
              "status": "PASS_FROZEN_MODELED_BOUNDARY_RECONSTRUCTION_ONLY",
              "candidate": b.CANDIDATE, "geometry_revision_id": b.REVISION, "members": list(b.MEMBERS),
              "common_datum_xyz_mm": [0., 0., 0.], "current_authority": authority,
              "case_count": len(cases), "state_count": len(states), "cases": cases, "states": states,
              "geometric_port_coverage": graph_ports,
              "historical_provenance_limit": backing["upstream_source_pin_assessment"],
              "qualification": {key: False for key in (
                  "complete_joint_accepted", "physical_contact_activity_established", "force_split_calculated",
                  "resistance_calculated", "floor_qualified", "six_case_envelope_established",
                  "geometry_changed", "cad_or_native_run", "fabrication_or_climbing_release")},
              "remaining_gaps": [
                  "Conditional source actions only; A12 source/recovery discrepancy and wider six-case gaps remain open.",
                  "Non-qualifying screw withdrawal proxies and floor assumptions remain source-model choices.",
                  "Point samples do not establish finished stress, contact pressure, stiffness or resistance.",
                  "The direct seat and cleat route are retained without load allocation or physical-path qualification.",
                  "Inner-edge support, exact Hillman engagement/resistance and receiver-to-frame capacity remain open."]}
    report["source_pins_sha256"] = hashlib.sha256(encoded(pins)).hexdigest()
    return report, pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    report, pins = build()
    for name, value in (("boundary-actions.json", report), ("source-pins.json", pins)):
        path, data = HERE/name, encoded(value)
        if args.write:
            path.write_bytes(data)
        else:
            b.require(path.read_bytes() == data, "saved output differs: "+name)
    print(json.dumps({"status": "WROTE" if args.write else "VERIFIED",
                      "state_count": report["state_count"], "source_count": len(pins["sources"])}))


if __name__ == "__main__":
    main()
