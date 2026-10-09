"""Deferred independent saved Z180 input review; default is source preflight only."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
from collections import Counter, defaultdict
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").exists())
EXECUTION = OWN.parent.parent
MECH = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1"
PRIOR_REVIEW = MECH / "current-inputs-v1/independent-review-v1/review.py"
PRIOR_SHA = "18c699b5fde2471bf1c5328eb0cb93c1fa29dd3589639907bf92277a451abb64"
GATE = EXECUTION / "review-fix-v2/bridge.py"
GATE_SHA = "dc224c51a46f78433df614ce53b76e2a8f4b1a7ac4c436b7d0d212f784388f55"
ADAPTER = EXECUTION / "bridge.py"
ADAPTER_SHA = "fc95da9c8b81b8153813b6c98895401c4f4b5cf96e61d68973ba417c386917c6"
DESCRIPTOR = EXECUTION.parent / "z180-mechanics-inputs-v1/runs-v1/attempt04/descriptor.json"
DESCRIPTOR_SHA = "deccc585f3cc38cc315bf5618cb7ab7007b948e90cec8a4144c04a89cd2275df"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
INPUT_SCHEMA = "eoere_z180_first_order_mechanics_inputs/v1"
REVIEW_SCHEMA = "eoere_z180_mechanics_inputs_independent_review/v1"
SUCCESS = "independent_z180_source_input_checks_pass"
RELEASE = dict.fromkeys(("candidate_accepted", "complete_joint_acceptance", "capacity_established",
                         "fabrication_released", "structural_released", "climbing_released"), False)
DESCRIPTOR_RELEASE = dict.fromkeys(("candidate_admitted", "climbing", "complete_joint_resistance", "fabrication",
                                    "physical_contact", "structural"), False)
JOINS = (("timber_rows", "raw_gross_timber_rows"), ("physical_owner_gravity_rows", "physical_owner_gravity_rows"),
    ("fitting_poses", "fitting_poses"), ("fitting_port_bindings", "fitting_ports"), ("all_factory_holes", "all_factory_holes"),
    *[(key, key) for key in ("shafts", "finished_receiver_wall_queries", "finished_body_observations", "direct_contacts",
        "hillman_rows", "current_panel_machining_descriptors", "flange_domains", "flange_shared_face_patches",
        "timber_and_panel_shared_face_patches", "shared_pair_query_census")])


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def reference(path, expected):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and sha(path) == expected, "exact review source bytes differ: " + str(path))
    return {"path": str(path.relative_to(ROOT)), "sha256": expected}


def read(ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"} and not Path(ref["path"]).is_absolute(),
            "exact repository-relative review reference required")
    path = ROOT / ref["path"]
    require(reference(path, ref["sha256"]) == ref, "review source alias prohibited")
    return json.loads(path.read_bytes())


def merge_pins(*maps):
    result = {}
    for values in maps:
        for path, digest in values.items():
            require(path not in result or result[path] == digest, "review source pin conflict: " + path)
            result[path] = digest
    return result


def verify_pins(pins):
    for path, digest in pins.items():
        require(reference(ROOT / path, digest) == {"path": path, "sha256": digest}, "review pin alias prohibited")
    return pins


def independent_load_method():
    """Extract five vector helpers and the unchanged independent load block only."""
    require(__debug__, "independent review requires enabled assertions")
    reference(PRIOR_REVIEW, PRIOR_SHA)
    raw = PRIOR_REVIEW.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PRIOR_SHA, "independent compiler bytes changed before parse")
    tree = ast.parse(raw)
    helpers = ("indexed", "add", "scale", "cross", "close")
    nodes = [copy.deepcopy(n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in helpers]
    require([n.name for n in nodes] == list(helpers), "exact independent arithmetic helpers required")
    constants = [copy.deepcopy(n) for n in tree.body if isinstance(n, ast.Assign)
                 and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in {"CASE_IDS", "LIVE", "GRAVITY"}]
    require([n.targets[0].id for n in constants] == ["CASE_IDS", "LIVE", "GRAVITY"], "exact independent load constants required")
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    start = next(i for i, n in enumerate(main.body) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "permanent")
    stop = next(i for i, n in enumerate(main.body) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "fixed")
    body = copy.deepcopy(main.body[start:stop])
    require(body[0].lineno == 157 and body[-1].end_lineno == 226, "exact independent permanent/live-load block required")
    function = ast.parse("def independent_load_checks(raw, exported, owners, bases):\n    pass\n").body[0]
    function.body = body + ast.parse("return dict(cases=case_results, roles=roles, aux=aux, physical_mass=physical_mass, aux_mass=aux_mass, total_mass=total_mass)").body
    context = {"copy": copy, "math": math, "defaultdict": defaultdict}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[*constants, *nodes, function], type_ignores=[])), str(PRIOR_REVIEW), "exec"), context)  # noqa: S102
    return context["independent_load_checks"]


class Output:
    """Reserve an exclusive inode before loading any dependent implementation."""
    def __init__(self, path):
        self.path = Path(os.path.abspath(path))
        self.stream = self.path.open("x+")
        self.identity = os.fstat(self.stream.fileno())
        self.write({"schema": "eoere_z180_input_review_attempt/v1", "status": "STARTED", "review_readiness": False,
                    "reviewed_input": None, "complete_reference_contact_inventory": False, "release": RELEASE})

    def write(self, data):
        current = self.path.lstat()
        require((current.st_dev, current.st_ino) == (self.identity.st_dev, self.identity.st_ino), "review output ownership changed")
        payload = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
        self.stream.seek(0)
        self.stream.write(payload)
        self.stream.truncate()
        self.stream.flush()
        os.fsync(self.stream.fileno())


@contextmanager
def reserve(path):
    output = Output(path)
    try:
        yield output
    except BaseException as error:
        output.write({"schema": "eoere_z180_input_review_attempt/v1", "status": "FAILED", "review_readiness": False,
            "reviewed_input": None, "complete_reference_contact_inventory": False, "error_type": type(error).__name__,
            "error": str(error), "release": RELEASE})
        raise
    finally:
        output.stream.close()


def load_gate():
    reference(GATE, GATE_SHA)
    reference(ADAPTER, ADAPTER_SHA)
    spec = importlib.util.spec_from_file_location("independent_z180_saved_input_corrected_gate", GATE)
    gate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gate
    spec.loader.exec_module(gate)
    return gate


def check_process(process, input_ref, process_ref, adapter, bridge):
    require(process.get("exit_code") == 0 and process.get("output_sha256") == input_ref["sha256"]
            and process.get("wrapper_sha256") == GATE_SHA and isinstance(process.get("elapsed_seconds"), (int, float))
            and math.isfinite(process["elapsed_seconds"]) and process["elapsed_seconds"] >= 0
            and type(process.get("source_pins_verified_before_after")) is int and process["source_pins_verified_before_after"] > 0
            and process.get("source_drift") == [],
            "successful exact source-only raw-input process required")
    command = process["command"]
    require(isinstance(command, list) and all(isinstance(item, str) for item in command), "actual raw-input command required")
    positions = [i for i, item in enumerate(command) if (ROOT / item).resolve() == GATE]
    require(len(positions) == 1 and positions[0] in (1, 2), "corrected Z180 source producer command required")
    args = bridge.parse_args(command[positions[0] + 1:])
    require(args.mode == "build-inputs" and not args.run and args.slot is None and args.case_id is None
            and args.out.resolve() == (ROOT / input_ref["path"]).resolve()
            and {"path": str(args.source_export.resolve().relative_to(ROOT)), "sha256": args.source_export_sha256}
            == {"path": str(DESCRIPTOR.relative_to(ROOT)), "sha256": DESCRIPTOR_SHA}
            and {"path": str(args.source_manifest.resolve().relative_to(ROOT)), "sha256": args.source_manifest_sha256} == adapter.SOURCE_MANIFEST
            and {"path": str(args.panel_bank.resolve().relative_to(ROOT)), "sha256": args.panel_bank_sha256}
            == adapter.manifest()["unchanged_panel_method"], "raw-input command source/output references differ")
    directory = (ROOT / process_ref["path"]).parent
    require(directory == (ROOT / input_ref["path"]).parent, "input/process/logs must share the recorded trial directory")
    logs = {str((directory / name).relative_to(ROOT)): process[key]
            for key, name in (("stdout_sha256", "stdout.log"), ("stderr_sha256", "stderr.log"))}
    for digest in logs.values():
        require(isinstance(digest, str) and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest), "exact raw-input log hashes required")
    return logs


def check_descriptor_receipt(review, descriptor_ref):
    require(review.get("schema") == "eoere_z180_geometry_descriptors_independent_review/v1"
            and review.get("success") == "independent_z180_descriptor_source_checks_pass"
            and review.get("descriptor") == descriptor_ref and review.get("release") == DESCRIPTOR_RELEASE,
            "own successful exact descriptor review and geometry release contract required")
    pins = review["source_sha256"]
    require(pins.get(descriptor_ref["path"]) == descriptor_ref["sha256"], "descriptor review lacks exact descriptor pin")
    return pins


def check_rows(raw, exported, parent, arithmetic):
    require(raw.get("schema") == INPUT_SCHEMA and raw.get("status") == "CURRENT_SOURCE_ROWS_PENDING_INDEPENDENT_REVIEW"
            and raw.get("optional_2026_extra") is False and raw.get("historical_q") is None and raw.get("old_field") is None
            and raw.get("readiness") == {"source_joins_independently_reviewed": False, "complete_reference_contact_inventory": False}
            and raw.get("source_pins_before_after_unchanged") is True and raw.get("release") == RELEASE,
            "own pending Z180 source inputs with every qualification false required")
    for key, source_key in JOINS:
        require(raw[key] == exported[source_key], "independent proposal descriptor join differs: " + key)
    require(raw["parameters"] == exported["parameters"] and raw["scenario"] == exported["material_scenario"], "own material/contact priors differ")
    indexed = lambda rows, key="id": {row[key]: row for row in rows}
    owners = indexed(raw["physical_owner_gravity_rows"])
    require(len(owners) == len(raw["physical_owner_gravity_rows"]) == 150
            and Counter(row["kind"] for row in owners.values()) == {"timber": 22, "fitting": 22, "panel": 6, "shaft": 100}, "150 unique own owners required")
    bases = [row for row in owners.values() if row["kind"] != "shaft"]
    require(raw["base_bodies"] == bases and len(bases) == 50, "50 own base gravity owners required")
    axes = [row["axis_id"] for row in raw["shafts"]]
    parent_axes = [row["axis_id"] for row in parent["shafts"]]
    require(len(axes) == len(set(axes)) == len(parent_axes) == len(set(parent_axes)) == 100 and set(axes) == set(parent_axes),
            "exact unique 100 parent shaft identities required")
    require(len(raw["finished_body_observations"]) == 28 and len(raw["finished_receiver_wall_queries"]) == 120
            and sum(len(row["ends"]) for row in raw["shafts"]) == 200
            and len(raw["fitting_port_bindings"]) == 88 and len(raw["hillman_rows"]) == 66, "own finished/receiver/seat/port census differs")
    panels = sorted(row["id"] for row in owners.values() if row["kind"] == "panel")
    require(raw["panel_ids"] == panels and len(panels) == 6, "six own panel owners required")
    holes = [{**hole, "angle_id": angle["angle_id"], "used": hole["installed_bolt_axis_id"] is not None}
             for angle in raw["all_factory_holes"] for hole in angle["holes"]]
    require(raw["factory_holes"] == holes and len(holes) == 176 and sum(row["used"] for row in holes) == 88, "176 own factory holes/88 installed ports required")
    require(raw["floor_footprints"] == {row["host"]: row["observed_normal_reference_points_xyz_mm"] for row in exported["floor_observations"]}
            and len(raw["floor_footprints"]) == 8 and sum(map(len, raw["floor_footprints"].values())) == 32
            and exported["support"]["enabled_centroid_xy_hosts"] == ["lumber_leg_left", "lumber_leg_right"]
            and exported["support"]["no_slip_assumed_not_verified"] is True, "32 own normal points and unverified rear-leg XY support required")
    contacts, common, flanges = (indexed(raw[key]) for key in ("direct_contacts", "timber_and_panel_shared_face_patches", "flange_shared_face_patches"))
    require(len(contacts) == len(raw["direct_contacts"]) == 1606
            and len(common) == len(raw["timber_and_panel_shared_face_patches"]) == 96
            and len(flanges) == len(raw["flange_shared_face_patches"]) == 88
            and Counter(row["kind"] for row in contacts.values()) == {"timber_face_contact": 332, "panel_contact": 922, "flange_contact": 352}
            and sum(len(row["cells"]) for row in [*common.values(), *flanges.values()]) == 1606
            and len(raw["shared_pair_query_census"]) == 72, "complete unique 1606-cell own reference contact inventory required")
    require(all(row["first"] in owners and row["second"] in owners and row["first"] != row["second"]
                and math.isfinite(row["stiffness"]) and row["stiffness"] > 0
                and math.isfinite(row["reference_area_mm2"]) and row["reference_area_mm2"] > 0 for row in contacts.values()), "own finite contact/owner graph differs")
    return arithmetic(raw, exported, owners, bases)


def check_panels(raw, parent, parent_input, adapter):
    contract = raw["panel_operator_source_inputs"]
    require(contract == parent_input["panel_operator_source_inputs"]
            and contract["geometry"] == adapter.manifest()["parent_geometry"] and contract["optional_2026_extra"] is False,
            "authentic original panel contract/geometry must remain explicit")
    observations = {row["id"]: row for row in raw["finished_body_observations"]}
    slim = lambda row: {key: row[key] for key in ("id", "path", "sha256", "volume_mm3")}
    require({row["id"]: row for row in contract["finished_panel_solids"]}
            == {name: slim(observations[name]["source"]) for name in raw["panel_ids"]}
            and contract["panel_machining_canonical_sha256"] == canonical(raw["current_panel_machining_descriptors"])
            and contract["screw_axes_canonical_sha256"] == canonical([row["source_screw_descriptor"] for row in raw["hillman_rows"]])
            and contract["screw_axis_ids"] == [row["source_screw_descriptor"]["axis_id"] for row in raw["hillman_rows"]]
            and contract["old_contact_domains_reused"] is False and contract["old_response_or_acceptance_used"] is False,
            "own authentic panel sources/apertures/screw ports differ")
    require(raw["current_panel_machining_descriptors"] == parent["current_panel_machining_descriptors"]
            and raw["hillman_rows"] == parent["hillman_rows"], "protected panel/screw source joins differ")
    view, proof = adapter.panel_view(raw, contract)
    require(view["geometry"]["report"] == contract["geometry"] and proof["proposal_geometry"] == raw["geometry"]["report"]
            and proof["panel_source_geometry"] == contract["geometry"] and proof["apertures"] == 340 and proof["screw_ports"] == 66
            and proof["historical_q_actions_or_contacts_reused"] is False, "genuine unchanged-panel geometry proof differs")
    return proof


def prohibited(*_args, **_kwargs):
    raise AssertionError("independent saved-input review prohibits panel callbacks and preparation")


def authenticate_receipt(bridge, issued, raw, pins):
    _, checked = bridge.authenticate_review(issued, raw, pins)
    require(checked["inputs_canonical_sha256"] == canonical(raw), "genuine raw review authentication differs")
    require(len(bridge.driver.CASE_IDS) == 6 and len(set(bridge.driver.CASE_IDS)) == 6, "six distinct selected cases required")
    for case_id in bridge.driver.CASE_IDS:
        selected, selection = bridge.driver.select_case(raw, case_id)
        _, checked = bridge.authenticate_review(issued, selected, pins, raw_data=raw, selection=selection)
        require(checked["source_case_selection"] == selection, "genuine selected review authentication differs")


def review(args, output):
    require(args.run, "saved-input review needs explicit --run after parent authorization")
    refs = {}
    for key in ("inputs", "process", "descriptor_review"):
        path, digest = getattr(args, key), getattr(args, key + "_sha256")
        require(path is not None and digest is not None, "exact caller-supplied " + key + " reference required")
        refs[key] = reference(path, digest)
    descriptor_ref = reference(DESCRIPTOR, DESCRIPTOR_SHA)
    test_ref = reference(OWN.with_name("test_review.py"), sha(OWN.with_name("test_review.py")))
    preflight_ref = reference(OWN.with_name("preflight.json"), sha(OWN.with_name("preflight.json")))
    prepared = read(preflight_ref)
    require(prepared["schema"] == "eoere_z180_saved_input_review_source_preflight/v1"
            and prepared["actual_saved_input_review_performed"] is False and prepared["review_readiness"] is False
            and prepared["source_sha256"].get(str(OWN.relative_to(ROOT))) == LOADED_SHA
            and prepared["source_sha256"].get(test_ref["path"]) == test_ref["sha256"], "frozen own source/inert preflight differs")
    raw, exported, process, descriptor_review = read(refs["inputs"]), read(descriptor_ref), read(refs["process"]), read(refs["descriptor_review"])
    descriptor_pins = check_descriptor_receipt(descriptor_review, descriptor_ref)
    require(raw["geometry"]["cached_source_export"] == descriptor_ref
            and exported["source_sha256"].items() <= raw["source_sha256"].items(), "own final descriptor/raw-input source closure differs")
    evidence = {ref["path"]: ref["sha256"] for ref in [*refs.values(), descriptor_ref, test_ref, preflight_ref,
                reference(OWN, LOADED_SHA), reference(PRIOR_REVIEW, PRIOR_SHA), reference(GATE, GATE_SHA), reference(ADAPTER, ADAPTER_SHA)]}
    gate = load_gate()
    adapter = gate.original()
    with gate.corrected_context(adapter):
        fixed = adapter.production()
        bridge = fixed.frozen()
        with adapter.context(fixed, bridge), ExitStack() as stack:
            for obj, name in ((bridge, "methods"), (bridge, "load"), (bridge.factory, "_prepare"), (bridge.factory, "prepare")):
                stack.enter_context(patch.object(obj, name, side_effect=prohibited))
            evidence = merge_pins(evidence, check_process(process, refs["inputs"], refs["process"], adapter, bridge))
            sources = merge_pins(raw["source_sha256"], descriptor_pins, evidence)
            verify_pins(sources)
            adapter.validate_descriptor(exported)
            parent = adapter.read_ref(adapter.PARENT_DESCRIPTOR)
            results = check_rows(raw, exported, parent, independent_load_method())
            panel_proof = check_panels(raw, parent, adapter.read_ref(adapter.PARENT_INPUT), adapter)
            adapter.require_sources(raw)
            source_case = bridge.PACKET / "raised-rail-cases-v1/cases.py"
            # Only the pinned source recipe is imported; no bank or K API is used.
            spec = importlib.util.spec_from_file_location("independent_z180_genuine_source_load_recipe", source_case)
            require(sha(source_case) == bridge.REUSED["raised-rail-cases-v1/cases.py"], "genuine load recipe source differs")
            recipe = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(recipe)
            regenerated, gravity = recipe.derive_fresh_cases({"panel_machining": exported["current_panel_machining_descriptors"]},
                {"bodies": raw["base_bodies"], "bolt_gravity_components": results["roles"] + results["aux"]},
                expected_owner_ids=[row["id"] for row in raw["physical_owner_gravity_rows"]], source_sha256=raw["source_sha256"])
            require(regenerated == raw["cases"] and gravity == raw["gravity"], "genuine fresh source recipe differs")
            with bridge.factory_boundary():
                for case in raw["cases"]:
                    require(bridge.factory.validate_rows({**raw, "case": case})
                            == {"timber": 22, "fitting": 22, "shaft": 100, "panel": 6, "physical_bodies": 150}, "own per-case row census differs")
            sources = bridge.source_pins(sources)
            receipt = {"schema": REVIEW_SCHEMA, "success": SUCCESS, "complete_reference_contact_inventory": True,
                "input": refs["inputs"], "geometry": copy.deepcopy(raw["geometry"]["report"]), "release": copy.deepcopy(RELEASE),
                "source_sha256": sources, "findings": [], "saved_descriptor_review": refs["descriptor_review"],
                "input_process": refs["process"], "inputs_canonical_sha256": canonical(raw),
                "selected_case_canonical_sha256": {case["case_id"]: canonical(case) for case in raw["cases"]},
                "checks": {"physical_owners": 150, "unique_shafts": 100, "reference_contact_cells": 1606, "normal_floor_points": 32,
                    "independent_permanent_live_loads_and_seven_wrenches": results["cases"], "authentic_original_panel_geometry_proof": panel_proof,
                    "all_used_sources_before_after_unchanged": True},
                "mass_reconciliation_kg": {"physical_owners": results["physical_mass"], "auxiliary_metal": results["aux_mass"],
                                            "accessory_allowance": 25., "total": results["total_mass"]},
                "force_execution_readiness_claimed": False, "complete_joint_resistance": None, "actual_saved_input_review_performed": True,
                "review_input_construction_BREP_query_panel_K_preparation_frame_K_q_field_solve_or_browser_performed": False}
            output.write(receipt)
            issued = reference(output.path, sha(output.path))
            pins = bridge.source_pins(merge_pins(sources, {refs["inputs"]["path"]: refs["inputs"]["sha256"]}))
            authenticate_receipt(bridge, issued, raw, pins)
            verify_pins(sources)
    return receipt


def preflight():
    independent_load_method()
    refs = (reference(OWN, LOADED_SHA), reference(PRIOR_REVIEW, PRIOR_SHA), reference(GATE, GATE_SHA),
            reference(ADAPTER, ADAPTER_SHA), reference(DESCRIPTOR, DESCRIPTOR_SHA),
            reference(OWN.with_name("test_review.py"), sha(OWN.with_name("test_review.py"))))
    sources = {ref["path"]: ref["sha256"] for ref in refs}
    return {"schema": "eoere_z180_saved_input_review_source_preflight/v1", "status": "SOURCE_AND_INERT_CONTROLS_ONLY",
        "source_sha256": sources, "review_readiness": False, "reviewed_input": None,
        "complete_reference_contact_inventory": False, "actual_saved_input_review_performed": False,
        "force_execution_readiness_claimed": False, "release": RELEASE,
        "descriptor_review_release_contract": DESCRIPTOR_RELEASE,
        "independent_load_arithmetic": {"source": {"path": str(PRIOR_REVIEW.relative_to(ROOT)), "sha256": PRIOR_SHA},
            "extracted_helpers": ["indexed", "add", "scale", "cross", "close"], "main_statement_lines": [157, 226],
            "prior_main_or_saved_input_executed": False},
        "missing_actual_inputs": ["caller_supplied_exact_raw_input_ref", "caller_supplied_exact_process_ref",
                                  "caller_supplied_exact_final_descriptor_review_ref", "parent_authorization_for_actual_review"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=("preflight", "review"), default="preflight")
    parser.add_argument("--run", action="store_true")
    for key in ("inputs", "process", "descriptor-review"):
        parser.add_argument("--" + key, type=Path)
        parser.add_argument("--" + key + "-sha256")
    args = parser.parse_args(argv)
    with reserve(args.out) as output:
        require(__debug__, "independent review requires enabled assertions")
        if args.mode == "preflight":
            require(not args.run, "source preflight does not run a saved-input review")
            result = preflight()
            output.write(result)
        else:
            result = review(args, output)
        print(json.dumps({"output": str(output.path), "sha256": sha(output.path),
                          "actual_saved_input_review_performed": result["actual_saved_input_review_performed"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
