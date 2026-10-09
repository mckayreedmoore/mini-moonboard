"""Independent inert producer/admission integration probes; no candidate mechanics."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").exists())
BASE = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1"
BRIDGE = BASE / "adjusted-base-mechanics-v1/current-force-bridge-v1"
WRAPPER = BRIDGE / "review-fix-v2/bridge.py"
EXPECTED = {
    BRIDGE / "bridge.py": "ddc85386050d97145597dc720bef78634c9b326f0878aced8c02c8df4710c05b",
    BRIDGE / "test_bridge.py": "72cdd692b40df93e2a6a194e31d9bd03fe7125baf6fb605a09b66954bbecacf6",
    BRIDGE / "source-preflight.json": "4118719a61da4645085f4840b1888ac6df600df2307edc8c0d40ffb79d4eafe0",
    BRIDGE / "verification.json": "7ca9a676dd1c7b1ae41a4408caeae6d0d22c0ee57da43095663b8587238d5fab",
    WRAPPER: "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643",
    WRAPPER.with_name("test_bridge.py"): "cdaf6e63a542b738fd81b99e4c211952dd46765fb8c2082a1d43c0d977b88c90",
    WRAPPER.with_name("source-preflight.json"): "158b2fd603cabac3d5e39ac81f726da251ce6a393b797e7e047daef3dee85fdc",
    WRAPPER.with_name("verification.json"): "18903e345a4c7f59ecbf0036cd68946733981f8a8b9de29a3fef0a63b68a3f7a",
    BASE / "adjusted-base-mechanics-v1/current-source-observations-v1/attempt01.json":
        "0f7e95f0dabfb5f0b5d63f8ef7d78e3c52c07672b4f482a89a89496eec703de7",
    BASE / "adjusted-base-mechanics-v1/parent-authority-v1/extended-cleat-manifest.json":
        "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reject(callback, message=None):
    try:
        callback()
    except (ValueError, KeyError) as error:
        if message is not None:
            assert message in str(error), str(error)
        return str(error)
    raise AssertionError("invalid fixture unexpectedly passed")


def fixture(w, b, out, pins):
    """One coordinate, inert 150-owner census; no physical operators."""
    case = {"case_id": b.driver.CASE_IDS[0], "accessory_placement": "synthetic", "loads": []}
    raw = {"cases": [{**case, "case_id": name} for name in b.driver.CASE_IDS], "case": case,
           "floor_footprints": {name: [] for name in [*b.law.RESTRAINED_HOSTS, "normal_only"]}}
    selected, selection = b.driver.select_case(raw, case["case_id"])
    refs = {key: {"path": b.bundle.artifact_path(out.with_name(key + ".json")), "sha256": value * 64}
            for key, value in (("input", "a"), ("input_review", "b"), ("input_record", "c"))}
    method = {**refs, "source_sha256": pins}
    command = [sys.executable, str(w.OWN), "--mode", "run", "--run", "--case-id", case["case_id"],
               "--out", str(out), "--wall-seconds", "10"]
    for flag, key in (("inputs", "input"), ("input-review", "input_review"), ("method-input", "input_record")):
        command += ["--" + flag, str(ROOT / refs[key]["path"]), "--" + flag + "-sha256", refs[key]["sha256"]]
    command += ["--slot", str(out.with_name("slot.json")), "--slot-sha256", "d" * 64]
    pointer = {key: {"path": b.bundle.artifact_path(out.with_suffix(out.suffix + suffix)), "sha256": char * 64}
               for key, suffix, char in (("arrays", ".operators.npz", "e"), ("manifest", ".operators.json", "f"))}
    pins.update({row["path"]: row["sha256"] for row in pointer.values()})
    contacts = [{"id": "normal-" + str(i), "kind": "floor_normal"} for i in range(32)]
    tangents = [{"id": "tangent-" + str(i), "kind": "floor_tangent", "first": b.law.RESTRAINED_HOSTS[i % 2]}
                for i in range(16)]
    bodies = [{"id": "body-" + str(i)} for i in range(150)]
    counts = {"contacts": 32, "dofs": 1, "bearings": 0, "end_captures": 200,
              "floor_normals": 32, "floor_xy_components": 16}
    panels = {"panel-" + str(i): {"indices": [0]} for i in range(6)}
    snapshot = SimpleNamespace(case=case, groups=[], contacts=contacts, tangents=tangents, applied=None,
        assembly=SimpleNamespace(ndof=1, geo={"bodies": bodies}, K=None), coordinate_map={"panels": panels},
        manifest={"source_sha256": pins, "execution_command": command,
                  "original_operator_fingerprint_sha256": "1" * 64, "body_descriptors": bodies, "fitting_descriptors": []})
    normals = dict.fromkeys(b.law.RESTRAINED_HOSTS, 1.)
    field = {"schema": b.FIELD_SCHEMA, "release": copy.deepcopy(b.core.RELEASE), "counts": counts,
        "case_id": case["case_id"], "accessory_placement": case["accessory_placement"],
        "disposition": "CONVERGED_CANDIDATE_PENDING_INDEPENDENT_ADMISSION",
        "analytical_support_scenario": b.law.contract(), "independent_admission_required": True,
        "usable_conditional_actions": True, "source_inputs": selected, "source_sha256": pins,
        "equilibrium_verification": {"all_body_and_global_checks_pass": True},
        "source_case_selection": selection, "source_input_review": {"synthetic_review": True},
        "current_panel_operator_preparation": {"synthetic_panel_proof": True}, "current_method_input": refs["input_record"],
        "operator_bundle": pointer, "original_operator_fingerprint_sha256": "1" * 64,
        "body_applied_loads": [], "physical_body_descriptors": bodies, "fitting_operator_descriptors": [],
        "reference_interaction_descriptors": contacts + tangents, "body_identities": [r["id"] for r in bodies],
        "current_execution": {"command": command, "geometry": b.GEOMETRY, "loaded_driver_path": b.bundle.artifact_path(w.OWN),
            "loaded_driver_sha256": w.LOADED_SHA, "one_preparation_one_fixed_branch": True, "historical_q_or_forces_used": False,
            "input_path": refs["input"]["path"], "input_sha256": refs["input"]["sha256"],
            "input_review_path": refs["input_review"]["path"], "input_review_sha256": refs["input_review"]["sha256"]},
        "execution": {"command": command, "wall_seconds": 10., "loaded_driver_sha256": b.bundle.CORE_SHA,
            "loaded_factory_sha256": b.factory.LOADED_SHA, "one_preparation": True, "one_case": True,
            "automatic_retry": False, "historical_q_used": False},
        "response": {"converged": True, "original_floor_switching_law_used": False,
            "original_joint_and_normal_laws_used": True, "physical_residual_uses_unmodified_laws": False,
            "physical_residual_uses_declared_support_scenario": True, "generalized_residual_tolerance_n": 1e-5,
            "legacy_nonbearing_key_means_disabled_xy_hosts": True, "q": [0.], "q_canonical_sha256": b.canonical([0.]),
            "gradient_n": [1e-5], "gradient_canonical_sha256": b.canonical([1e-5]), "gradient_inf_n": 1e-5,
            "nonbearing_no_slip_removed": ["normal_only"],
            "fixed_floor_support_v1": {**b.law.contract(), "normal_force_n_by_host": normals, "both_credited_legs_in_bearing": True}}}
    for key in b.base.TABLES:
        field[key] = []
    field["panel_generalized_coefficients"] = {name: {**chart, "global_dof_start": 0, "coefficients": [0.]}
                                               for name, chart in panels.items()}
    field["state_id"] = b.STATE_PREFIX + b.canonical({"source_sha256": pins, "inputs": selected, "case": case,
                                                     "counts": counts, "mask_budget": 1, "max_iterations": 300})[:24]
    closure = {"full_signed_gradient_canonical_sha256": b.canonical([1e-5]), "gradient_inf_n": 1e-5,
               "floor_force_and_declared_fixed_rear_leg_mask_replayed": True}
    return SimpleNamespace(raw=raw, selected=selected, selection=selection, refs=refs, method=method, command=command,
                           pointer=pointer, snapshot=snapshot, field=field, normals=normals, closure=closure, panels=panels)


@contextlib.contextmanager
def inert_admission(w, b, f, pins, events):
    """Retain actual wrapper/admission orchestration; replace numerical and input providers."""
    centroidal = SimpleNamespace(correction_context=lambda _factory: contextlib.nullcontext())
    bank = SimpleNamespace(verify_panel_source_inputs=lambda *_: {"source_sha256": pins})
    def authenticate(*_args, **_kwargs):
        events.append("authenticate_selected_review")
        return pins, {"synthetic_review": True}
    def replay(*_args):
        events.append("saved_q_replay")
        return {}
    def auditor():
        events.append("declared_force_auditor")
        return lambda *_: (f.normals, f.closure)
    patches = [patch.object(w, "runtime_source_pins", side_effect=lambda _b, extra=None, **_: {**pins, **(extra or {})}),
        patch.object(b, "read_method", return_value=f.method), patch.object(b, "methods", return_value=(centroidal, bank)),
        patch.object(b, "read_inputs", return_value=(f.raw, pins)), patch.object(b, "verify_selected_case", return_value=None),
        patch.object(b, "authenticate_review", side_effect=authenticate), patch.object(b.factory, "validate_rows", return_value={}),
        patch.object(b.bundle, "read_snapshot", return_value=f.snapshot),
        patch.object(b.base, "OwnedMaps", return_value=SimpleNamespace(panels=f.panels)),
        patch.object(b.base, "verify_physical_bodies", return_value=None), patch.object(b.base, "verify_ports", return_value={}),
        patch.object(b.base, "verify_load_work", return_value={}), patch.object(b.law, "replay", side_effect=replay),
        patch.object(b.old_gate, "declared_force_auditor", side_effect=auditor),
        patch.object(b.driver.ordered, "verify_fitting_and_alias_recovery", return_value={}),
        patch.object(b.base, "motion_diagnostics", return_value={})]
    with contextlib.ExitStack() as stack:
        for item in patches:
            stack.enter_context(item)
        yield


def producer_probe(w, b, work, checks, real_pins):
    pins = copy.deepcopy(real_pins)
    out = work / "producer-field.json"
    f = fixture(w, b, out, pins)
    events = []
    args = b.parse_args(f.command[2:])
    prepared = SimpleNamespace(source_sha256=pins)
    centroidal = SimpleNamespace(correction_context=lambda _factory: contextlib.nullcontext())
    def panel_load(data):
        assert data == f.selected
        events.append("panel_dependencies")
        return {}, {}, pins, f.field["current_panel_operator_preparation"]
    bank = SimpleNamespace(load_panel_dependencies=panel_load,
                           verify_panel_source_inputs=lambda *_: {"source_sha256": pins})
    def prepare(data, _panels, _integrated, **kwargs):
        assert data == f.selected and kwargs["source_review"] == f.refs["input_review"]
        assert b.factory.SCHEMA == b.INPUT_SCHEMA and b.factory.read_inputs is b.read_inputs
        events.append("fresh_prepare")
        return prepared
    def snapshot(data, **kwargs):
        assert data is prepared and kwargs["command"] == f.command
        events.append("save_own_pre_solve_operators")
        return f.pointer
    def execute(data, **kwargs):
        assert data is prepared and kwargs["mask_budget"] == 1 and kwargs["max_iterations"] == 300
        events.append("one_fixed_branch_execute")
        return copy.deepcopy(f.field)
    with inert_admission(w, b, f, pins, events), patch.object(sys, "orig_argv", f.command), \
            patch.object(b, "slot_check", return_value={"synthetic_authorized_slot": True}), \
            patch.object(b, "methods", return_value=(centroidal, bank)), \
            patch.object(b.factory, "prepare", side_effect=prepare), \
            patch.object(b.bundle, "snapshot", side_effect=snapshot), \
            patch.object(b.bundle, "coordinate_map", return_value=f.snapshot.coordinate_map), \
            patch.object(b, "compile_execute", return_value=execute):
        assert w.run_case(args) == 0
    field = json.loads(out.read_bytes())
    assert field["schema"] == b.FIELD_SCHEMA and field["current_execution"]["loaded_driver_sha256"] == w.LOADED_SHA
    assert field["current_execution"]["command"] == f.command and field["usable_conditional_actions"] is True
    assert field["panel_generalized_coefficients"] == f.field["panel_generalized_coefficients"]
    assert not any(field["release"].values())
    assert events == ["authenticate_selected_review", "panel_dependencies", "fresh_prepare",
                      "save_own_pre_solve_operators", "one_fixed_branch_execute"]
    checks.append({"name": "actual_wrapper_successful_producer", "events": events,
                   "limits": "all input/panel/preparation/snapshot/solve providers inert; actual run orchestration/output/export"})


def raw_review_probe(w, b, work, checks, pins):
    """Exercise the real review authenticator with a tiny raw six-case source."""
    f = fixture(w, b, work / "review-fixture.json", copy.deepcopy(pins))
    review = {"schema": b.REVIEW_SCHEMA, "success": b.REVIEW_SUCCESS,
              "complete_reference_contact_inventory": True, "geometry": b.GEOMETRY,
              "release": copy.deepcopy(b.core.RELEASE), "input": f.refs["input"],
              "source_sha256": {f.refs["input"]["path"]: f.refs["input"]["sha256"]}}
    review_pins = {**pins, f.refs["input"]["path"]: f.refs["input"]["sha256"]}
    def read_ref(ref):
        if ref == f.refs["input_review"]:
            return review
        assert ref == f.refs["input"]
        return f.raw
    with patch.object(w, "runtime_source_pins", side_effect=lambda _b, extra=None, **_: {**pins, **(extra or {})}), \
            patch.object(b, "require_current_sources", return_value=None), patch.object(b, "read_ref", side_effect=read_ref), \
            w.corrected_context(b):
        joined, checked = b.authenticate_review(f.refs["input_review"], f.selected, review_pins,
                                               raw_data=f.raw, selection=f.selection)
        assert joined and checked["inputs_canonical_sha256"] == b.canonical(f.raw)
        assert checked["source_case_selection"] == f.selection
        review["schema"] = b.old_gate.SCHEMA
        reject(lambda: b.authenticate_review(f.refs["input_review"], f.selected, review_pins,
                                            raw_data=f.raw, selection=f.selection))
        review["schema"] = b.REVIEW_SCHEMA
        reject(lambda: b.authenticate_review(f.refs["input_review"], f.selected, {},
                                            raw_data=f.raw, selection=f.selection))
        altered = copy.deepcopy(f.selected)
        altered["case"]["loads"] = [{"id": "unreviewed"}]
        reject(lambda: b.authenticate_review(f.refs["input_review"], altered, review_pins,
                                            raw_data=f.raw, selection=f.selection))
        altered = copy.deepcopy(f.selection)
        altered["selected_index"] = 1
        reject(lambda: b.authenticate_review(f.refs["input_review"], f.selected, review_pins,
                                            raw_data=f.raw, selection=altered))
    checks.append({"name": "real_raw_selected_review_authenticator", "happy_path": True,
                   "negative_controls": ["foreign_review_schema", "missing_raw_source_pin", "changed_selected_load", "changed_selection"]})


def input_join_probe(w, b, work, checks, pins):
    """Run the real input join on empty descriptors, with inert method providers."""
    f = fixture(w, b, work / "input-join-fixture.json", copy.deepcopy(pins))
    export_ref = {"path": b.bundle.artifact_path(work / "synthetic-export.json"), "sha256": "2" * 64}
    exported = {"schema": "eoere_extended_cleat_cached_source_export/v1", "geometry": b.GEOMETRY,
        "manifest": b.SOURCE_MANIFEST, "source_sha256": {b.GEOMETRY["path"]: b.GEOMETRY["sha256"]},
        "parameters": {}, "material_scenario": {},
        "source_pins_before_after_unchanged": True, "native_cached_solid_queries_performed": True,
        "native_nominal_flat_reference_flange_masks_created": 88, "fresh_contact_domains_not_copied_from_old_field": True,
        "candidate_CAD_rebuild_mesh_K_assembly_factorization_q_forces_load_cases_or_native_solve_performed": False}
    for key in ("physical_owner_gravity_rows", "shafts", "auxiliary_metal_gravity_descriptors", "raw_gross_timber_rows",
                "fitting_ports", "fitting_poses", "all_factory_holes", "floor_observations", "finished_receiver_wall_queries",
                "finished_body_observations", "direct_contacts", "timber_and_panel_shared_face_patches", "shared_pair_query_census",
                "flange_domains", "flange_shared_face_patches", "hillman_rows", "current_panel_machining_descriptors"):
        exported[key] = []
    manifest = {"schema": "eoere_extended_cleat_mechanics_frozen_sources/v1", "parent_model_review_approved": True,
                "optional_2026_extra": False, "geometry": b.GEOMETRY}
    def read_ref(ref):
        if ref == export_ref:
            return exported
        if ref == b.SOURCE_MANIFEST:
            return manifest
        assert ref == b.GEOMETRY
        return {"synthetic_geometry_metadata_only": True}
    bank = SimpleNamespace(source_inputs=lambda: {"synthetic_metadata_only": True},
                           verify_panel_source_inputs=lambda _data: {"source_sha256": {}})
    centroidal = SimpleNamespace(SCENARIO="eoere-centroidal-four-half-strips-preserved-span-v1",
                                correction_contract=lambda: {"synthetic_correction_metadata_only": True})
    cases = SimpleNamespace(derive_fresh_cases=lambda *_args, **_kwargs: (f.raw["cases"], {"synthetic_gravity": True}))
    def provider(path, _sha, _name):
        if Path(path) == ROOT / b.PANEL_BANK["path"]:
            return bank
        assert Path(path) == b.PACKET / "raised-rail-cases-v1/cases.py"
        return cases
    selected = []
    def verify(data, _centroidal):
        selected.append(data["case"]["case_id"])
    def prohibited(*_args, **_kwargs):
        raise AssertionError("candidate mechanics provider called")
    with patch.object(w, "runtime_source_pins", side_effect=lambda _b, extra=None, **_: {**pins, **(extra or {})}), \
            patch.object(b, "read_ref", side_effect=read_ref), patch.object(b, "load", side_effect=provider), \
            patch.object(b.driver, "load", return_value=centroidal), patch.object(b, "verify_selected_case", side_effect=verify), \
            patch.object(b.factory, "validate_rows", return_value={}), patch.object(b.factory, "prepare", side_effect=prohibited), \
            patch.object(b.frame, "ElasticAssembly", side_effect=prohibited):
        data = w.build_inputs(export_ref, b.SOURCE_MANIFEST, b.PANEL_BANK)
        assert data["schema"] == b.INPUT_SCHEMA and data["historical_q"] is None and data["old_field"] is None
        assert data["readiness"] == {"source_joins_independently_reviewed": False, "complete_reference_contact_inventory": False}
        assert selected == list(b.driver.CASE_IDS) and not any(data["release"].values())
        for key in ("timber_rows", "hillman_rows", "direct_contacts", "flange_domains"):
            changed = copy.deepcopy(data)
            changed[key].append({"unreviewed_descriptor": True})
            reject(lambda changed=changed: b.require_current_sources(changed))
    checks.append({"name": "actual_wrapper_pure_input_join", "case_selection_count": len(selected),
                   "descriptor_join_negative_controls": 4,
                   "limits": "empty synthetic descriptors and inert method/input providers; no genuine bank or mechanics"})


def run():
    assert {path: sha(path) for path in EXPECTED} == EXPECTED
    w = load(WRAPPER, "independent_current_force_testing_review")
    b = w.frozen()
    closure = {ROOT / p: digest for p, digest in w.source_pins().items()}
    before = {**EXPECTED, **closure}
    assert {path: sha(path) for path in before} == before
    probes = OWN.parent / "_probes"
    probes.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="attempt-", dir=probes))
    checks = []
    result = subprocess.run(["uv", "run", "pytest", "--import-mode=importlib", "-q", str(BRIDGE / "test_bridge.py"),
                             str(WRAPPER.with_name("test_bridge.py"))], cwd=ROOT, capture_output=True, text=True, check=True)
    checks.append({"name": "both_issued_test_suites", "result": result.stdout.strip()})
    pins = {str(path.relative_to(ROOT)): digest for path, digest in closure.items()}
    producer_probe(w, b, work, checks, pins)
    raw_review_probe(w, b, work, checks, pins)
    input_join_probe(w, b, work, checks, pins)
    out = work / "synthetic-field.json"
    f = fixture(w, b, out, pins)
    events = []
    with inert_admission(w, b, f, pins, events):
        out.write_text(json.dumps(f.field))
        receipt = w.audit(out)
        assert receipt[b.SUCCESS] is True and receipt["schema"] == b.ADMISSION_SCHEMA
        assert receipt["source_path"] == b.bundle.artifact_path(w.OWN)
        admitted, returned_pins = w.require_admitted_payload(out.read_bytes(), receipt, admission_sha256=w.LOADED_SHA)
        assert admitted == f.field and returned_pins == pins
        assert events == ["authenticate_selected_review", "saved_q_replay", "declared_force_auditor"]
        checks.append({"name": "actual_wrapper_saved_field_admit_and_consume", "events": events.copy(),
                       "limits": "one-coordinate synthetic census; providers and numerical kernels stubbed"})
        cli_out = work / "admission-cli-receipt.json"
        assert w.main(["--mode", "admit", "--field", str(out), "--out", str(cli_out)]) == 0
        assert json.loads(cli_out.read_bytes()) == receipt
        checks.append({"name": "actual_admit_cli_reserves_and_writes_receipt", "passed": True})
        mutations = {
            "foreign_field_schema": lambda x: x.update(schema=b.old_runner.FIELD_SCHEMA),
            "foreign_producer_sha": lambda x: x["current_execution"].update(loaded_driver_sha256="0" * 64),
            "foreign_geometry": lambda x: x["current_execution"].update(geometry={}),
            "wrong_saved_q_hash": lambda x: x["response"].update(q=[1.]),
            "wrong_state_id": lambda x: x.update(state_id="foreign"),
            "foreign_operator_path": lambda x: x["operator_bundle"]["arrays"].update(path="foreign.npz"),
            "missing_panel_export": lambda x: x["panel_generalized_coefficients"].pop(next(iter(f.panels))),
            "lost_rear_leg_bearing": lambda x: x["response"]["fixed_floor_support_v1"]["normal_force_n_by_host"].update({b.law.RESTRAINED_HOSTS[0]: 0.}),
            "above_inclusive_tolerance": lambda x: x["response"].update(gradient_inf_n=1.00000001e-5),
        }
        for name, mutate in mutations.items():
            altered = copy.deepcopy(f.field)
            mutate(altered)
            out.write_text(json.dumps(altered))
            reject(lambda: w.audit(out))
            checks.append({"name": name, "rejected": True})
        out.write_text(json.dumps(f.field))
        for key in b.base.TABLES:
            altered = copy.deepcopy(f.field)
            altered[key] = {"changed": True} if isinstance(altered[key], dict) else [{"changed": True}]
            altered_bytes = json.dumps(altered).encode()
            rehashed = copy.deepcopy(receipt)
            rehashed.update(input_raw_sha256=hashlib.sha256(altered_bytes).hexdigest(), input_canonical_sha256=b.canonical(altered))
            reject(lambda altered_bytes=altered_bytes, rehashed=rehashed:
                   w.require_admitted_payload(altered_bytes, rehashed, admission_sha256=w.LOADED_SHA),
                   "state/q/gradient/operators/source selection/actions receipt binding differs")
        checks.append({"name": "every_saved_action_table_bytes_bound", "rejected_tables": list(b.base.TABLES)})
        for mutate in (lambda x: x.update(schema=b.old_gate.SCHEMA),
                       lambda x: x.update(admission_source_sha256="0" * 64),
                       lambda x: x["table_canonical_sha256"].update(panel_screw_actions="0" * 64)):
            altered = copy.deepcopy(receipt)
            mutate(altered)
            reject(lambda altered=altered: w.require_admitted_payload(out.read_bytes(), altered, admission_sha256=w.LOADED_SHA))
        checks.append({"name": "foreign_or_changed_admission_receipt", "rejections": 3})
    assert b.OWN == w.FROZEN and b.factory.SCHEMA == b.ORIGINAL_SCHEMA
    after = {path: sha(path) for path in before}
    assert after == before
    receipt = {"schema": "eoere_current_force_bridge_testing_review/v2", "status": "CLEAN_NO_SUBSTANTIAL_FINDINGS",
               "substantial_findings": [], "checks": checks, "source_hashes_before_after_unchanged": True,
               "source_sha256": {str(path.relative_to(ROOT)): digest for path, digest in before.items()},
               "probe_directory": str(work.relative_to(ROOT)),
               "review_path": str(OWN.relative_to(ROOT)), "review_sha256": sha(OWN),
               "original_sources_or_issued_evidence_changed": False,
               "retention": {"active": "review.py, receipt.json and owned ignored inert fixtures",
                             "archive_prune_staging_or_commit_performed": False},
               "candidate_CAD_BRep_real_panel_bank_preparation_frame_K_current_load_solver_native_browser_executed": False,
               "historical_response_or_acceptance_transferred": False,
               "release": copy.deepcopy(b.core.RELEASE)}
    path = OWN.with_name("receipt.json")
    assert not path.exists() or json.loads(path.read_bytes())["status"] == "IN_PROGRESS", "preserve issued testing receipt"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"receipt": str(path), "checks": len(checks), "status": receipt["status"]}))


if __name__ == "__main__":
    run()
