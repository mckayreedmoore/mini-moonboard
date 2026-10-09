"""Current extended-cleat inputs, deferred producer and saved-field admission.

Default CLI mode only checks sources and identifies missing reviewed inputs.
The original factory equations, fixed-floor solver, sparse snapshot and force
auditor are reused. Explicit context hooks change the input/review boundary;
private AST hooks change outer identities and provenance keys only. None of
the frozen files is edited or impersonated. Importing prepares no candidate.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
import signal
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[6]
PACKET = OWN.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REUSED = {
    "floor-practical-resolution-v1/runner.py": "02b35eb6eb148e1b178fcca069b761065eaec8f0641ec5adc91f211b3e9eceb4",
    "floor-practical-resolution-v1/admission.py": "ee47bca7795483c3d304030a26e368c9e2bf9b3bbff48ef10b5416e8aa344fa9",
    "floor-practical-resolution-v1/support_law.py": "b4bc326d2060d6fc49d0f29218306533e4cea305db72dce2f0e09338c7e3ad2e",
    "raised-rail-execution-v1/driver.py": "4aaaa91dbad2674dc5bd42a43b38949675c94aa9619534c15d0f6f906e532692",
    "raised-rail-cases-v1/cases.py": "1f7a1b332ee37627725ce8127df8ff3541ac4deec5fdc586a36e7f7953860978",
}
GEOMETRY = {
    "path": "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-extended-cleats-v1.json",
    "sha256": "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d",
}
SOURCE_MANIFEST = {
    "path": "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/parent-authority-v1/extended-cleat-manifest.json",
    "sha256": "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6",
}
PANEL_BANK = {
    "path": "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-panel-bank-v1/panel_operators.py",
    "sha256": "014f867eac1e9286dee188024544b5853e5cda2aa1cd11037d7aee5a2b29966b",
}
INPUT_SCHEMA = "eoere_extended_cleat_first_order_mechanics_inputs/v1"
REVIEW_SCHEMA = "eoere_extended_cleat_mechanics_inputs_independent_review/v1"
REVIEW_SUCCESS = "independent_extended_cleat_source_input_checks_pass"
METHOD_SCHEMA = "eoere_extended_cleat_fixed_floor_method_inputs/v1"
FIELD_SCHEMA = "eoere_extended_cleat_fixed_floor_candidate/v1"
STATE_PREFIX = "eoere-extended-cleat-fixed-floor-"
ADMISSION_SCHEMA = "eoere_extended_cleat_fixed_floor_independent_field_admission/v1"
SUCCESS = "current_extended_cleat_equilibrium_and_recovery_pass"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()


def load(path, digest, name):
    path = Path(path).resolve()
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError("preserve bound source: " + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


for relative, digest in REUSED.items():
    if hashlib.sha256((PACKET / relative).read_bytes()).hexdigest() != digest:
        raise ValueError("frozen mechanics source changed: " + relative)
old_gate = load(PACKET / "floor-practical-resolution-v1/admission.py",
                REUSED["floor-practical-resolution-v1/admission.py"], "eoere_current_bridge_frozen_floor_gate")
old_runner, driver, law = old_gate.runner, old_gate.driver, old_gate.law
base, frame, core, factory, bundle = driver.base, driver.frame, driver.core, driver.factory, driver.bundle
require, canonical = driver.require, driver.canonical
ORIGINAL_SCHEMA = factory.SCHEMA
ORIGINAL_AUTHENTICATE = factory.authenticate_source_review
ORIGINAL_READ = factory.read_inputs


def source_pins(extra=None, *, method=None):
    pins = old_runner.source_pins(extra)
    additions = {bundle.artifact_path(OWN): LOADED_SHA}
    if method is not None:
        additions.update(method["source_sha256"])
        additions[method["input_record"]["path"]] = method["input_record"]["sha256"]
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, "current bridge source conflict: " + path)
        pins[path] = digest
    require(frame.sha(OWN) == LOADED_SHA, "loaded current bridge changed")
    return base.verify_pins(pins)


def read_ref(ref):
    require(set(ref) == {"path", "sha256"}, "exact current source reference required")
    path = (ROOT / ref["path"]).resolve()
    require(path.is_relative_to(ROOT) and frame.sha(path) == ref["sha256"], "current source bytes differ")
    return json.loads(path.read_bytes())


def require_current_sources(data):
    """The current report is a report; a descriptor export is not a scene."""
    require(data.get("schema") == INPUT_SCHEMA and data.get("release") == core.RELEASE
            and data.get("optional_2026_extra") is False, "distinct current OFF inputs with every release false required")
    refs = data["geometry"]
    require(set(refs) == {"report", "source_manifest", "cached_source_export"}
            and refs["report"] == GEOMETRY and refs["source_manifest"] == SOURCE_MANIFEST,
            "exact latest geometry and explicit parent-owned current source references required")
    rows = {key: read_ref(ref) for key, ref in refs.items()}
    manifest, exported = rows["source_manifest"], rows["cached_source_export"]
    require(manifest.get("schema") == "eoere_extended_cleat_mechanics_frozen_sources/v1"
            and manifest.get("parent_model_review_approved") is True
            and manifest.get("optional_2026_extra") is False and manifest["geometry"] == GEOMETRY,
            "parent-reviewed exact current OFF manifest required")
    require(exported.get("schema") == "eoere_extended_cleat_cached_source_export/v1"
            and exported["geometry"] == GEOMETRY and exported.get("manifest") == SOURCE_MANIFEST
            and exported.get("source_pins_before_after_unchanged") is True
            and exported.get("native_cached_solid_queries_performed") is True
            and exported.get("native_nominal_flat_reference_flange_masks_created") == 88
            and exported.get("fresh_contact_domains_not_copied_from_old_field") is True
            and exported.get("candidate_CAD_rebuild_mesh_K_assembly_factorization_q_forces_load_cases_or_native_solve_performed") is False,
            "own current source-only descriptor export required")
    pins = data["source_sha256"]
    for ref in refs.values():
        require(pins.get(ref["path"]) == ref["sha256"], "current descriptor reference is outside source closure")
    require(all(pins.get(p) == digest for p, digest in exported["source_sha256"].items()),
            "current export source closure incomplete")
    require(data["scenario"]["fitting_stiffness_basis"] == "eoere-centroidal-four-half-strips-preserved-span-v1",
            "current scenario must name genuine centroidal operator")
    for key, source_key in (("timber_rows", "raw_gross_timber_rows"), ("physical_owner_gravity_rows", "physical_owner_gravity_rows"),
                            ("fitting_poses", "fitting_poses"), ("fitting_port_bindings", "fitting_ports"),
                            ("all_factory_holes", "all_factory_holes"), ("shafts", "shafts"),
                            ("finished_receiver_wall_queries", "finished_receiver_wall_queries"),
                            ("finished_body_observations", "finished_body_observations"), ("direct_contacts", "direct_contacts"),
                            ("hillman_rows", "hillman_rows"), ("current_panel_machining_descriptors", "current_panel_machining_descriptors"),
                            ("flange_domains", "flange_domains"), ("flange_shared_face_patches", "flange_shared_face_patches"),
                            ("timber_and_panel_shared_face_patches", "timber_and_panel_shared_face_patches"),
                            ("shared_pair_query_census", "shared_pair_query_census")):
        require(data[key] == exported[source_key], "current source descriptor join differs: " + key)
    require(data["base_bodies"] == [r for r in exported["physical_owner_gravity_rows"] if r["kind"] != "shaft"]
            and data["floor_footprints"] == {r["host"]: r["observed_normal_reference_points_xyz_mm"] for r in exported["floor_observations"]},
            "current base-owner/floor-source join differs")
    require(data["parameters"] == exported["parameters"]
            and {k: v for k, v in data["scenario"].items() if k not in {"fitting_stiffness_basis", "fitting_operator_correction"}}
            == {k: v for k, v in exported["material_scenario"].items() if k not in {"fitting_stiffness_basis", "fitting_operator_correction"}},
            "current bridge must retain unchanged material/contact/floor/shaft priors")
    require(data["panel_ids"] == sorted(r["id"] for r in exported["physical_owner_gravity_rows"] if r["kind"] == "panel")
            and data["factory_holes"] == [{**hole, "angle_id": angle["angle_id"], "used": hole["installed_bolt_axis_id"] is not None}
                for angle in exported["all_factory_holes"] for hole in angle["holes"]],
            "complete own panel/factory-hole source join differs")
    return rows


def read_inputs(path, expected_sha256):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and frame.sha(path) == expected_sha256, "current input raw SHA differs")
    data = json.loads(path.read_bytes())
    require_current_sources(data)
    factory.validate_rows(data)
    return data, source_pins({**data["source_sha256"], bundle.artifact_path(path): expected_sha256})


def authenticate_review(record, data, pins, *, raw_data=None, selection=None):
    raw_data = data if raw_data is None else raw_data
    require_current_sources(raw_data)
    review = read_ref(record)
    require(review.get("schema") == REVIEW_SCHEMA and review.get("success") == REVIEW_SUCCESS
            and review.get("complete_reference_contact_inventory") is True
            and review.get("geometry") == GEOMETRY and review.get("release") == core.RELEASE,
            "independent current source-input review required before preparation")
    source = review["input"]
    require(pins.get(source["path"]) == source["sha256"]
            and review["source_sha256"].get(source["path"]) == source["sha256"]
            and canonical(read_ref(source)) == canonical(raw_data), "reviewed raw current input differs")
    checked = {**record, "input": copy.deepcopy(source), "inputs_canonical_sha256": canonical(raw_data)}
    if selection is not None:
        expected, checked_selection = driver.select_case(raw_data, selection["case_id"])
        require(data == expected and selection == checked_selection, "exact current case selection differs")
        checked["source_case_selection"] = copy.deepcopy(selection)
    else:
        require(data == raw_data, "prepared current source view differs")
    return source_pins({**pins, **review["source_sha256"], record["path"]: record["sha256"]}), checked


@contextmanager
def factory_boundary(*, raw_data=None, selection=None):
    """Only schema, source-pointer reader and outer-review hooks change.

    All original validation arithmetic, _prepare, assembly and kernels retain
    their genuine source locations. The real factory is required by the pinned
    centroidal context and independently owned geometry-map reconstruction.
    """
    require(factory.SCHEMA == ORIGINAL_SCHEMA and factory.read_inputs is ORIGINAL_READ
            and factory.authenticate_source_review is ORIGINAL_AUTHENTICATE,
            "current factory boundary must be unnested and serialized")
    def authenticate(record, data, pins):
        return authenticate_review(record, data, pins, raw_data=raw_data, selection=selection)
    with patch.object(factory, "SCHEMA", INPUT_SCHEMA), patch.object(factory, "read_inputs", read_inputs), \
            patch.object(factory, "authenticate_source_review", authenticate):
        yield


def compile_function(path, name, context, *, replacements=None, expected_counts=None):
    """Clone one genuine function with reviewed exact string hooks only."""
    tree = ast.parse(Path(path).read_bytes())
    candidates = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    require(len(candidates) == 1, "one exact reused function required")
    node = copy.deepcopy(candidates[0])
    counts = dict.fromkeys(replacements or {}, 0)
    for item in ast.walk(node):
        if isinstance(item, ast.Constant) and isinstance(item.value, str) and item.value in counts:
            counts[item.value] += 1
            item.value = replacements[item.value]
    if expected_counts is not None:
        require(counts == expected_counts, "private current identity/provenance hook locations differ")
    namespace = dict(context)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(OWN), "exec"), namespace)  # noqa: S102
    return namespace[name]


def verify_selected_case(data, centroidal):
    require_current_sources(data)
    function = compile_function(driver.OWN, "verify_selected_case", {**vars(driver), "GEOMETRY_SHA": GEOMETRY["sha256"]})
    return function(data, centroidal)


def read_method(path, digest):
    path = Path(path).resolve()
    ref = {"path": bundle.artifact_path(path), "sha256": digest}
    record = read_ref(ref)
    require(record.get("schema") == METHOD_SCHEMA and record.get("geometry") == GEOMETRY
            and record.get("source_manifest") == SOURCE_MANIFEST
            and record.get("method_checks_pass") is True and record.get("independent_readiness_pass") is True
            and record.get("support_contract") == law.contract() and record.get("release") == core.RELEASE,
            "reviewed distinct current method/readiness inputs required")
    pins = source_pins(record["source_sha256"])
    for source, expected in ((OWN, LOADED_SHA), (driver.CENTROIDAL, driver.CENTROIDAL_SHA),
                             (driver.CASE_PLAN, driver.CASE_PLAN_SHA)):
        require(record["source_sha256"].get(bundle.artifact_path(source)) == expected, "current method lacks integration source")
    bank = record["panel_bank"]
    require(bank == PANEL_BANK and pins.get(bank["path"]) == bank["sha256"], "current method lacks exact panel bank source")
    for key in ("input", "input_review", "source_manifest"):
        current = record[key]
        read_ref(current)
        require(record["source_sha256"].get(current["path"]) == current["sha256"], "current method lacks " + key)
    return {**record, "input_record": ref}


def methods(record):
    centroidal = driver.load(driver.CENTROIDAL, driver.CENTROIDAL_SHA, "eoere_current_bridge_centroidal")
    bank_ref = record["panel_bank"]
    bank = load(ROOT / bank_ref["path"], bank_ref["sha256"], "eoere_current_bridge_panel_bank")
    require(all(callable(getattr(bank, name, None)) for name in
                ("source_inputs", "verify_panel_source_inputs", "load_panel_dependencies")), "current panel API incomplete")
    require(bank.source_inputs()["geometry"] == GEOMETRY, "current panel bank must name exact latest OFF geometry")
    return centroidal, bank


def build_inputs(export_ref, manifest_ref, bank_ref):
    """Deferred pure load/metadata join; no panel or whole-frame K is loaded."""
    exported, manifest = read_ref(export_ref), read_ref(manifest_ref)
    require(bank_ref == PANEL_BANK and manifest_ref == SOURCE_MANIFEST
            and manifest["geometry"] == exported["geometry"] == GEOMETRY,
            "current export/parent manifest geometry mismatch")
    pins = source_pins({**exported["source_sha256"], export_ref["path"]: export_ref["sha256"],
                        manifest_ref["path"]: manifest_ref["sha256"], bank_ref["path"]: bank_ref["sha256"]})
    bank = load(ROOT / bank_ref["path"], bank_ref["sha256"], "eoere_current_bridge_source_panel_bank")
    centroidal = driver.load(driver.CENTROIDAL, driver.CENTROIDAL_SHA, "eoere_current_bridge_source_centroidal")
    case_provider = load(PACKET / "raised-rail-cases-v1/cases.py", REUSED["raised-rail-cases-v1/cases.py"],
                         "eoere_current_bridge_original_case_recipe")
    owners = copy.deepcopy(exported["physical_owner_gravity_rows"])
    bodies = [r for r in owners if r["kind"] != "shaft"]
    roles = [{"id": r["id"], "owner": s["body"], "mass_kg": r["mass_kg"],
              "center_xyz_mm": r["center_of_mass_xyz_mm"], "basis": r["basis"]}
             for s in exported["shafts"] for r in s["metal_roles"]]
    cases, gravity = case_provider.derive_fresh_cases(
        {"panel_machining": exported["current_panel_machining_descriptors"]},
        {"bodies": bodies, "bolt_gravity_components": roles + exported["auxiliary_metal_gravity_descriptors"]},
        expected_owner_ids=[r["id"] for r in owners], source_sha256=pins)
    scenario = copy.deepcopy(exported["material_scenario"])
    scenario.update(fitting_stiffness_basis=centroidal.SCENARIO, fitting_operator_correction=centroidal.correction_contract())
    ports = exported["fitting_ports"]
    data = {"schema": INPUT_SCHEMA, "status": "CURRENT_SOURCE_ROWS_PENDING_INDEPENDENT_REVIEW",
        "source_sha256": pins, "source_pins_before_after_unchanged": True,
        "geometry": {"report": GEOMETRY, "source_manifest": manifest_ref, "cached_source_export": export_ref},
        "optional_2026_extra": False, "parameters": exported["parameters"], "scenario": scenario,
        "timber_rows": exported["raw_gross_timber_rows"], "base_bodies": bodies,
        "physical_owner_gravity_rows": owners, "fitting_poses": exported["fitting_poses"],
        "all_factory_holes": exported["all_factory_holes"],
        "factory_holes": [{**hole, "angle_id": angle["angle_id"], "used": hole["installed_bolt_axis_id"] is not None}
                          for angle in exported["all_factory_holes"] for hole in angle["holes"]],
        "fitting_port_bindings": ports, "shafts": exported["shafts"],
        "panel_ids": sorted(r["id"] for r in owners if r["kind"] == "panel"),
        "floor_footprints": {r["host"]: r["observed_normal_reference_points_xyz_mm"] for r in exported["floor_observations"]},
        "cases": cases, "case": cases[0], "gravity": gravity,
        "panel_operator_source_inputs": bank.source_inputs(),
        "readiness": {"source_joins_independently_reviewed": False, "complete_reference_contact_inventory": False},
        "historical_q": None, "old_field": None, "release": core.RELEASE}
    for key in ("finished_receiver_wall_queries", "finished_body_observations", "direct_contacts",
                "timber_and_panel_shared_face_patches", "shared_pair_query_census", "flange_domains",
                "flange_shared_face_patches", "hillman_rows", "current_panel_machining_descriptors"):
        data[key] = copy.deepcopy(exported[key])
    require_current_sources(data)
    with factory_boundary():
        factory.validate_rows(data)
    panel_checks = bank.verify_panel_source_inputs(data)
    data["source_sha256"] = source_pins({**pins, **panel_checks["source_sha256"]})
    for case_id in driver.CASE_IDS:
        selected, _ = driver.select_case(data, case_id)
        verify_selected_case(selected, centroidal)
    source_pins(data["source_sha256"])
    return data


def compile_execute(pins_callback):
    return compile_function(old_runner.OWN, "compile_execute", {
        **vars(old_runner), "OWN": OWN, "FIELD_SCHEMA": FIELD_SCHEMA, "STATE_PREFIX": STATE_PREFIX})(pins_callback)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "build-inputs", "run", "admit"), default="preflight")
    for name in ("inputs", "input-review", "method-input", "source-export", "source-manifest", "panel-bank", "slot", "field"):
        parser.add_argument("--" + name, type=Path)
        parser.add_argument("--" + name + "-sha256")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--case-id", choices=driver.CASE_IDS)
    parser.add_argument("--wall-seconds", type=float, default=900.)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if args.mode == "run":
        require(args.run and args.case_id in driver.CASE_IDS and 0 < args.wall_seconds <= 1800
                and all(getattr(args, name) is not None and getattr(args, name + "_sha256") is not None
                        for name in ("inputs", "input_review", "method_input", "slot")),
                "current producer needs explicit exact input/review/method/slot references and bounded case")
    return args


def slot_check(args, input_sha, method_sha):
    require(os.environ.get("EOERE_PARENT_SERIALIZED_FORCE_RUN") == "1", "parent-owned serialized force-run marker required")
    require(args.slot is not None and args.slot_sha256 is not None and frame.sha(args.slot) == args.slot_sha256,
            "exact parent force-run serial-slot record required")
    record = json.loads(args.slot.read_bytes())
    require(record.get("status") == "FREE_SLOT" and record.get("current_force_run_authorized") is True
            and record.get("approved_geometry_sha256") == GEOMETRY["sha256"]
            and record.get("approved_inputs_sha256") == input_sha and record.get("approved_method_sha256") == method_sha,
            "parent slot does not authorize this exact current input/method run")
    return {"path": str(args.slot.resolve()), "sha256": args.slot_sha256, "record": record}


def run_case(args):
    require(args.run and args.case_id in driver.CASE_IDS and 0 < args.wall_seconds <= 1800,
            "one explicit bounded current case required")
    out = args.out.resolve()
    paths = [out, *[out.with_suffix(out.suffix + suffix) for suffix in
                    (".operators.npz", ".operators.json", ".failed.json")]]
    require(not any(p.exists() for p in paths), "preserve every existing current field/operator/failure")
    method = read_method(args.method_input, args.method_input_sha256)
    require(method["input"] == {"path": bundle.artifact_path(args.inputs.resolve()), "sha256": args.inputs_sha256}
            and method["input_review"] == {"path": bundle.artifact_path(args.input_review.resolve()), "sha256": args.input_review_sha256},
            "current method/readiness must bind actual input and review")
    slot = slot_check(args, args.inputs_sha256, args.method_input_sha256)
    centroidal, bank = methods(method)
    command, events = list(sys.orig_argv), []
    pins, phase, start = source_pins(method=method), "before-current-source-read", time.monotonic()
    def observe(event):
        events.append(copy.deepcopy(event))
        print(json.dumps(event, sort_keys=True), flush=True)
    def alarm(_signum, _frame):
        raise core.CaseWallTimeLimit("current fixed-floor case wall limit")
    prior = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, args.wall_seconds)
    try:
        with factory_boundary():
            raw, input_pins = factory.read_inputs(args.inputs, args.inputs_sha256)
        data, selection = driver.select_case(raw, args.case_id)
        verify_selected_case(data, centroidal)
        pins = source_pins({**pins, **input_pins}, method=method)
        phase = "current-panel-operators"
        panels, integrated, panel_pins, proof = bank.load_panel_dependencies(data)
        bank.verify_panel_source_inputs(data, proof)
        pins = source_pins({**pins, **panel_pins}, method=method)
        review = {"path": bundle.artifact_path(args.input_review.resolve()), "sha256": args.input_review_sha256}
        with factory_boundary(raw_data=raw, selection=selection), centroidal.correction_context(factory):
            phase = "fresh-current-preparation"
            prepared = factory.prepare(data, panels, integrated, source_sha256=pins, source_review=review)
            pointer = bundle.snapshot(prepared, arrays_path=paths[1], manifest_path=paths[2],
                                      pins=source_pins(prepared.source_sha256, method=method), command=command)
            pins = source_pins({**prepared.source_sha256, **{r["path"]: r["sha256"] for r in pointer.values()}}, method=method)
            phase = "one-current-fixed-support-solve"
            field = compile_execute(lambda extra=None: source_pins(extra, method=method))(
                prepared, pins=pins, command=command, mask_budget=1, max_iterations=300, branch_observer=observe)
            old_runner.export_panel_coefficients(field, bundle.coordinate_map(prepared))
        field.update(operator_bundle=pointer, analytical_support_scenario=law.contract(),
            source_case_selection=selection, current_panel_operator_preparation=proof,
            current_method_input=method["input_record"], current_execution={"command": command,
                "loaded_driver_path": bundle.artifact_path(OWN), "loaded_driver_sha256": LOADED_SHA,
                "input_path": bundle.artifact_path(args.inputs.resolve()), "input_sha256": args.inputs_sha256,
                "input_review_path": review["path"], "input_review_sha256": review["sha256"],
                "geometry": GEOMETRY, "slot_at_start": slot, "one_preparation_one_fixed_branch": True,
                "historical_q_or_forces_used": False,
                "factory_boundary_changes": ["input schema", "source pointer contract", "current outer input review"],
                "private_execute_changes": ["support dispatcher", "scenario identity", "support wording"]})
        field["execution"].update(elapsed_seconds=time.monotonic()-start, wall_seconds=args.wall_seconds, branch_events=events)
        require(field["original_operator_fingerprint_sha256"] == bundle.read_snapshot(pointer).manifest[
            "original_operator_fingerprint_sha256"], "own current pre-solve operator fingerprint differs")
        core.write_exclusive(out, field)
        return 0 if field["response"]["converged"] else 1
    except Exception as error:
        core.write_exclusive(paths[3], {"schema": "eoere_extended_cleat_fixed_floor_failure/v1",
            "command": command, "source_sha256": pins, "phase": phase, "events": events,
            "elapsed_seconds": time.monotonic()-start, "error_type": type(error).__name__, "error": str(error),
            "accepted_q": None, "accepted_actions": None, "release": core.RELEASE})
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prior)


ADMISSION_REPLACEMENTS = {"reused_raised_method_input": "current_method_input", "fixed_floor_execution": "current_execution"}
ADMISSION_COUNTS = {"audit": {"reused_raised_method_input": 1, "fixed_floor_execution": 1},
                    "require_admitted_payload": {"reused_raised_method_input": 3, "fixed_floor_execution": 0}}


def admission_functions():
    """Reuse every fixed-floor independent equation; current identities only."""
    proxy = SimpleNamespace(OWN=OWN, LOADED_SHA=LOADED_SHA, FIELD_SCHEMA=FIELD_SCHEMA, STATE_PREFIX=STATE_PREFIX, parse_args=parse_args)
    current_driver = SimpleNamespace(**{**vars(driver), "read_method": read_method, "methods": methods,
        "verify_selected_case": verify_selected_case, "authenticate_selected_review": authenticate_review})
    context = {**vars(old_gate), "OWN": OWN, "LOADED_SHA": LOADED_SHA, "SCHEMA": ADMISSION_SCHEMA,
        "SUCCESS": SUCCESS, "runner": proxy, "driver": current_driver, "source_pins": source_pins}
    pending = compile_function(old_gate.OWN, "require_pending_field", context)
    context["require_pending_field"] = pending
    result = {"require_pending_field": pending}
    for name, counts in ADMISSION_COUNTS.items():
        result[name] = compile_function(old_gate.OWN, name, context,
            replacements=ADMISSION_REPLACEMENTS, expected_counts=counts)
    return result


def audit(path):
    field = json.loads(Path(path).read_bytes())
    require(field.get("schema") == FIELD_SCHEMA and field["current_execution"]["geometry"] == GEOMETRY,
            "actual current extended-cleat field required")
    command = field["current_execution"]["command"]
    positions = [i for i, value in enumerate(command) if Path(value).resolve() == OWN]
    require(len(positions) == 1 and positions[0] in (1, 2), "actual current producer command required")
    args = parse_args(command[positions[0] + 1:])
    execution = field["current_execution"]
    require(args.mode == "run" and args.inputs_sha256 == execution["input_sha256"]
            and bundle.artifact_path(args.inputs.resolve()) == execution["input_path"]
            and args.input_review_sha256 == execution["input_review_sha256"]
            and bundle.artifact_path(args.input_review.resolve()) == execution["input_review_path"]
            and {"path": bundle.artifact_path(args.method_input.resolve()), "sha256": args.method_input_sha256} == field["current_method_input"],
            "actual current input/review/method command references differ")
    method = read_method(args.method_input, args.method_input_sha256)
    require(method["input"] == {"path": execution["input_path"], "sha256": execution["input_sha256"]}
            and method["input_review"] == {"path": execution["input_review_path"], "sha256": execution["input_review_sha256"]},
            "current readiness source binding differs")
    with factory_boundary():
        return admission_functions()["audit"](path)


def require_admitted_payload(field_bytes, receipt, *, admission_sha256):
    with factory_boundary():
        return admission_functions()["require_admitted_payload"](field_bytes, receipt, admission_sha256=admission_sha256)


def preflight(args):
    source_pins()
    compile_execute(lambda extra=None: source_pins(extra))
    admission_functions()
    refs, missing = {}, []
    for name in ("inputs", "input_review", "method_input", "source_export", "source_manifest", "panel_bank"):
        path, digest = getattr(args, name), getattr(args, name + "_sha256")
        if path is None or digest is None:
            missing.append(name)
            continue
        ref = {"path": bundle.artifact_path(path.resolve()), "sha256": digest}
        require(path.resolve().is_relative_to(ROOT) and frame.sha(path) == digest, "provided current source bytes differ")
        refs[name] = ref
    if "source_manifest" in refs:
        require(refs["source_manifest"] == SOURCE_MANIFEST, "exact parent-owned current manifest required")
        manifest = read_ref(refs["source_manifest"])
        require(manifest["geometry"] == GEOMETRY and manifest["readiness"]["candidate_assembly_or_solve"] is False,
                "descriptor-only geometry authority cannot supply candidate readiness")
    panel_sources = None
    if "panel_bank" in refs:
        require(refs["panel_bank"] == PANEL_BANK, "exact reviewed current panel method source required")
        bank = load(ROOT / refs["panel_bank"]["path"], refs["panel_bank"]["sha256"], "eoere_current_bridge_preflight_panel_sources")
        panel_sources = bank.source_inputs()
        require(panel_sources["geometry"] == GEOMETRY and panel_sources["optional_2026_extra"] is False,
                "exact current OFF panel metadata required")
    if "source_export" in refs:
        exported = read_ref(refs["source_export"])
        require(exported.get("schema") == "eoere_extended_cleat_cached_source_export/v1"
                and exported.get("geometry") == GEOMETRY and exported.get("manifest") == SOURCE_MANIFEST,
                "distinct own current descriptor export required")
    if "inputs" in refs:
        with factory_boundary():
            data, _ = read_inputs(args.inputs, args.inputs_sha256)
        if "input_review" in refs:
            authenticate_review(refs["input_review"], data, source_pins(data["source_sha256"]))
    if "method_input" in refs:
        method = read_method(args.method_input, args.method_input_sha256)
        _, bank = methods(method)
        if "inputs" in refs:
            bank.verify_panel_source_inputs(data)
    return {"schema": "eoere_extended_cleat_force_bridge_source_preflight/v1",
        "status": "SOURCE_HOOKS_VERIFIED_PRODUCTION_UNPERFORMED", "geometry": GEOMETRY,
        "source_sha256": source_pins({ref["path"]: ref["sha256"] for ref in refs.values()}),
        "provided": refs, "missing": missing, "current_panel_source_contract": panel_sources,
        "schemas": {"inputs": INPUT_SCHEMA, "review": REVIEW_SCHEMA, "method": METHOD_SCHEMA,
                    "field": FIELD_SCHEMA, "admission": ADMISSION_SCHEMA},
        "mechanics": {"factory_validation_and_preparation_arithmetic_changed": False,
            "support": law.contract(), "floor_normal_points": 32, "tangent_rows_retained": 16,
            "tangent_components_enabled": 4, "generalized_residual_tolerance_n_inclusive": 1e-5,
            "own_case_raw_operators_saved_before_solve": True, "independent_saved_q_force_work_body_replay_required": True},
        "production_readiness_claimed": False, "candidate_CAD_panel_K_global_K_q_actions_or_solve_performed": False,
        "historical_q_forces_or_acceptance_transferred": False, "release": core.RELEASE}


def main(argv=None):
    args = parse_args(argv)
    require(not args.out.exists(), "preserve existing current bridge output")
    if args.mode == "run":
        return run_case(args)
    if args.mode == "admit":
        require(args.field is not None, "actual current field required for admission")
        result = audit(args.field)
    elif args.mode == "build-inputs":
        def ref(name):
            path, digest = getattr(args, name), getattr(args, name + "_sha256")
            require(path is not None and digest is not None, "exact " + name + " reference required")
            return {"path": bundle.artifact_path(path.resolve()), "sha256": digest}
        result = build_inputs(ref("source_export"), ref("source_manifest"), ref("panel_bank"))
    else:
        result = preflight(args)
    core.write_exclusive(args.out, result)
    print(json.dumps({"schema": result["schema"], "output": str(args.out), "sha256": frame.sha(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
