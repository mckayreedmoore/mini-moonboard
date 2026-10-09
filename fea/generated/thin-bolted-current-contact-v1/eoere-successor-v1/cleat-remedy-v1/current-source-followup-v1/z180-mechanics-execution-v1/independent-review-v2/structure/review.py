"""Bounded architecture review of the frozen exact-roster correction; inert only."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
CORRECTION = PACKET / "review-fix-v2"
TARGETS = {
    "bridge.py": "dc224c51a46f78433df614ce53b76e2a8f4b1a7ac4c436b7d0d212f784388f55",
    "test_bridge.py": "7139f66d4218510d1eefc7e9d6f2b4827ff673d01c3cdb073c1a2dd9ee3b65a2",
    "source-preflight.json": "2b76796f808dce7805aaf338729571c078f4676f7e589dc626f1ceeeb483c092",
    "verification.json": "97845159bf1c8e59df46ac09ab072df2af2fcc8069b5ed57ff2eaa4e2195aaf5",
}
PREVIOUS = {
    "independent-review-v1/structure/review.py": "98abcad692fd28c1ca2d6ef8b8c3df710e7b4b2718faaaa76d7f8f93186e94bc",
    "independent-review-v1/structure/receipt.json": "fa3ff86e045bb32f75c614b8cbaeaf0223a7b7315053599655e72f36f5855fc1",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def rejects(callback, message):
    try:
        callback()
    except ValueError as error:
        require(message in str(error), "unexpected rejection: " + str(error))
    else:
        raise AssertionError("expected rejection: " + message)


def review():
    pins = {str((CORRECTION / n).relative_to(ROOT)): h for n, h in TARGETS.items()}
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "four corrected targets changed")
    issued, verification = (read(CORRECTION / n) for n in ("source-preflight.json", "verification.json"))
    for mapping in (issued["source_sha256"],
                    {n: r["sha256"] for n, r in verification["inherited_source_sha256_before_after"].items()},
                    {str((PACKET / n).relative_to(ROOT)): h for n, h in PREVIOUS.items()}):
        for name, digest in mapping.items():
            require(name not in pins or pins[name] == digest, "contradictory source binding")
            pins[name] = digest
    manifest = read(PACKET / "parent-sources-v1.json")
    for name in ("geometry", "parent_geometry", "parent_descriptors", "saved_finished_receiver_evidence", "unchanged_panel_method"):
        ref = manifest[name]
        require(ref["path"] not in pins or pins[ref["path"]] == ref["sha256"], "contradictory parent binding")
        pins[ref["path"]] = ref["sha256"]
    before = {n: sha(ROOT / n) for n in pins}
    require(before == pins and len(issued["source_sha256"]) == 30, "frozen source/retention union differs")
    for mapping in (verification["files"], verification["inherited_source_sha256_before_after"]):
        require(all((ROOT / n).stat().st_size == r["bytes"] for n, r in mapping.items()), "retained source volume differs")
    contexts = ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md")
    context_before = {n: sha(ROOT / n) for n in contexts}

    spec = importlib.util.spec_from_file_location("z180_structure_roster_correction", CORRECTION / "bridge.py")
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    require(c._original is None and c.LOADED_SHA == TARGETS["bridge.py"], "eager original load or wrong correction identity")
    a = c.original()
    require(a._production is None and a.OWN == c.FROZEN and a.LOADED_SHA == c.FROZEN_SHA,
            "lazy frozen adapter load changed source ownership")
    require(a.PRODUCTION_SHA == "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643"
            and manifest["unchanged_panel_method"]["sha256"] == "014f867eac1e9286dee188024544b5853e5cda2aa1cd11037d7aee5a2b29966b",
            "numerical or original panel source changed")
    adapter_before = {n: getattr(a, n) for n in ("OWN", "LOADED_SHA", "validate_descriptor", "source_pins")}

    # Compile only the retained standard-library synthetic fixture definition.
    # Do not import pytest, production, factories or scientific/native modules.
    tree = ast.parse((PACKET / "test_bridge.py").read_bytes())
    fixture = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "fixture")
    namespace = {"a": a, "copy": copy}
    exec(compile(ast.Module(body=[fixture], type_ignores=[]), str(PACKET / "test_bridge.py"), "exec"), namespace)  # noqa: S102
    fixture = namespace["fixture"]
    parent, exported, data, source_read = fixture()
    delegate = Mock(wraps=a.validate_descriptor)
    with patch.object(a, "read_ref", side_effect=source_read), patch.object(a, "validate_descriptor", delegate), c.corrected_context(a):
        require(a.validate_descriptor(exported) is parent and a.require_sources(data)["cached_source_export"] is exported,
                "exact roster failed retained descriptor and input joins")
    require(delegate.call_count == 2, "new roster check replaced or repeated retained validation")

    for kind in ("duplicate_moved", "omitted_moved", "unknown_axis"):
        _, exported, data, source_read = fixture()
        if kind == "duplicate_moved":
            exported["shafts"][0] = copy.deepcopy(exported["shafts"][4])
        elif kind == "omitted_moved":
            exported["shafts"].pop(0)
        else:
            exported["shafts"][0]["axis_id"] = "synthetic_unknown_axis"
        data["shafts"] = copy.deepcopy(exported["shafts"])
        delegate = Mock(side_effect=AssertionError("malformed roster reached original descriptor joins"))
        builder = Mock(side_effect=AssertionError("malformed roster reached genuine builder or panel callback"))
        with patch.object(a, "read_ref", side_effect=source_read), patch.object(a, "validate_descriptor", delegate), c.corrected_context(a):
            rejects(lambda exported=exported: a.validate_descriptor(exported), "exact unique 100 authenticated parent axes")
            rejects(lambda data=data: a.require_sources(data), "exact unique 100 authenticated parent axes")
            rejects(lambda builder=builder, data=data: a.build_inputs(SimpleNamespace(build_inputs=builder), data["geometry"]["cached_source_export"],
                                           a.SOURCE_MANIFEST, manifest["unchanged_panel_method"]),
                    "exact unique 100 authenticated parent axes")
        require(not delegate.called and not builder.called, "malformed roster crossed retained joins/builder boundary")
    parent, exported, _, source_read = fixture()
    parent["shafts"][0] = copy.deepcopy(parent["shafts"][4])
    with patch.object(a, "read_ref", side_effect=source_read), c.corrected_context(a):
        rejects(lambda: a.validate_descriptor(exported), "exact unique 100 authenticated parent axes")

    # New identity reaches the existing source hook and its method branch;
    # no genuine production module or frozen numerical module is loaded.
    calls = []
    def runtime_pins(bridge, additions, *, method=None):
        calls.append((bridge, dict(additions), method))
        return dict(additions)
    w = SimpleNamespace(runtime_source_pins=runtime_pins)
    method = {"synthetic_method": True}
    with c.corrected_context(a):
        actual = a.source_pins(w, None, method=method)
        expected = {str(c.OWN.relative_to(ROOT)): c.LOADED_SHA, str(c.FROZEN.relative_to(ROOT)): c.FROZEN_SHA,
                    a.GEOMETRY["path"]: a.GEOMETRY["sha256"], a.SOURCE_MANIFEST["path"]: a.SOURCE_MANIFEST["sha256"]}
        require(actual == expected and calls[-1][2] is method, "source union or exact method forwarding differs")
        for path in (c.FROZEN, c.OWN):
            count = len(calls)
            rejects(lambda path=path: a.source_pins(w, None, {str(path.relative_to(ROOT)): "0" * 64}), "source")
            require(len(calls) == count, "pin conflict reached production source hook")
        rejects(lambda: c.corrected_context(a).__enter__(), "unnested and serialized")
    require(all(getattr(a, n) is value for n, value in adapter_before.items()), "nested rejection did not restore hooks")
    try:
        with c.corrected_context(a):
            raise RuntimeError("synthetic context unwind")
    except RuntimeError as error:
        require(str(error) == "synthetic context unwind", "unexpected context exception")
    require(all(getattr(a, n) is value for n, value in adapter_before.items()), "exception did not restore hooks")
    with patch.object(c, "FROZEN_SHA", "0" * 64):
        rejects(c.original, "adapter bytes changed")

    # Retained adapter context receives both identities and restores every
    # hook even when the numerical bridge is a private inert namespace.
    context_node = next(n for n in ast.parse((PACKET / "bridge.py").read_bytes()).body
                        if isinstance(n, ast.FunctionDef) and n.name == "context")
    hooks_node = next(n.value for n in ast.walk(context_node) if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "hooks" for t in n.targets))
    b = SimpleNamespace(**{k.value: object() for k in hooks_node.keys if k.value != "z180_original_read_method"})
    b.load, b.read_method = lambda *_args: None, lambda *_args: None
    b.PANEL_BANK = manifest["unchanged_panel_method"]
    bridge_before = dict(vars(b))
    @contextmanager
    def inert_production_context(_bridge):
        yield
    w.corrected_context = inert_production_context
    with c.corrected_context(a), a.context(w, b):
        require(b.OWN == c.OWN and b.LOADED_SHA == c.LOADED_SHA and b.INPUT_SCHEMA == a.INPUT_SCHEMA,
                "downstream context omitted new source identity or own schema")
        require(b.source_pins(method=method) == expected and calls[-1][0] is b and calls[-1][2] is method,
                "downstream method/source identity forwarding differs")
    require(vars(b) == bridge_before and all(getattr(a, n) is value for n, value in adapter_before.items()),
            "downstream context did not restore both namespaces")

    # Exercise each public delegate with private callbacks, never real fields.
    entrypoints = {"main": ((["synthetic-argv"],), {}), "run_case": ((object(),), {}),
                   "audit": ((Path("synthetic-unread-field.json"),), {}),
                   "require_admitted_payload": ((b"synthetic-unread-payload", {}), {"admission_sha256": "a" * 64})}
    for name, (args, kwargs) in entrypoints.items():
        token = object()
        def callback(*_args, token=token, **_kwargs):
            require(a.OWN == c.OWN and a.LOADED_SHA == c.LOADED_SHA, "entrypoint escaped correction context")
            return token
        with patch.object(a, name, side_effect=callback) as stub:
            require(getattr(c, name)(*args, **kwargs) is token, "entrypoint did not return original result")
            stub.assert_called_once_with(*args, **kwargs)
        require(all(getattr(a, n) is value for n, value in adapter_before.items()), "entrypoint left hooks installed")

    events = []
    @contextmanager
    def reserve(_path):
        events.append("reserve")
        yield None
    def frozen():
        events.append("frozen")
        raise ValueError("synthetic stop before numerical import")
    with patch.object(a, "production", return_value=SimpleNamespace(reserve=reserve, frozen=frozen)):
        rejects(lambda: c.main(["--out", str(OWN.with_name("never-created.json"))]), "synthetic stop")
    require(events == ["reserve", "frozen"], "new entrypoint moved ownership after numerical import")
    with patch.object(a, "production", return_value=SimpleNamespace(reserve=Mock(side_effect=FileExistsError), frozen=Mock())) as stub:
        try:
            c.main(["--out", str(OWN.with_name("never-created.json"))])
        except FileExistsError:
            require(not stub.return_value.frozen.called, "occupied output reached numerical import")
        else:
            raise AssertionError("occupied output accepted")
    require(not OWN.with_name("never-created.json").exists() and a._production is None, "inert review created output or loaded production")

    old_preflight = read(PACKET / "source-preflight.json")
    require({k: v for k, v in old_preflight.items() if k != "source_sha256"}
            == {k: v for k, v in issued.items() if k != "source_sha256"}, "correction changed preflight engineering claims")
    require(issued["source_sha256"] == {**old_preflight["source_sha256"], str(c.OWN.relative_to(ROOT)): c.LOADED_SHA},
            "correction omitted inherited source or added unexplained source")
    require(len(issued["missing"]) == 6 and issued["provided"] == {} and issued["production_readiness_claimed"] is False
            and issued["complete_joint_resistance"] is None and issued["unadopted_proposal"] is True
            and issued["nut_spacer_proposal_included"] is False and not any(issued["release"].values())
            and issued["generalized_residual_tolerance_n_inclusive"] == 1e-5, "proposal/readiness/resistance/tolerance boundary changed")
    require(verification["genuine_descriptor_or_input_trial_performed"] is False
            and verification["current_panel_preparation_frame_K_q_actions_solve_CAD_BREP_native_or_browser_performed"] is False
            and verification["actual_saved_field_or_q_consumed"] is False and not any(verification["release"].values()),
            "inert verification implies execution or acceptance")
    require({n: sha(ROOT / n) for n in pins} == before, "target/source/history drift")
    require(not any(n in ("cadquery", "OCP", "numpy", "scipy") or n.startswith("OCP.") for n in sys.modules),
            "native/scientific module imported")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", str(OWN)], cwd=ROOT,
                          capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_z180_execution_roster_correction_structure_review/v2", "findings": [],
        "review_helper_sha256": sha(OWN), "frozen_target_sha256": TARGETS,
        "reused_immutable_v1_structure_review_sha256": PREVIOUS,
        "integrity": {"direct_source_pins": 30, "source_target_history_union": len(pins),
                      "union_canonical_json_sha256": hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                      "all_bound_bytes_unchanged_before_after": True, "historical_records_bound_by_verification": 23,
                      "four_new_target_bytes": sum((CORRECTION / n).stat().st_size for n in TARGETS)},
        "inert_checks": {"lazy_original_and_production_import": True,
                         "exact_unique_parent_export_and_four_moved_axis_sets_before_original_joins_and_builder": True,
                         "valid_synthetic_descriptor_and_input_delegate_retained_validation": True,
                         "both_adapter_pins_and_exact_method_branch_forwarded_conflicts_rejected": True,
                         "source_drift_and_nested_context_fail_closed": True,
                         "hooks_restored_after_normal_nested_failure_and_exception_paths": True,
                         "downstream_source_identity_schema_and_hook_restoration": True,
                         "four_entrypoints_delegate_under_scoped_identity": True,
                         "original_reservation_before_numerical_import_and_occupied_output_stop": True,
                         "preflight_engineering_claims_unchanged_only_correction_source_added": True},
        "ownership_and_claims": {"correction_adds_intake_and_source_identity_only": True,
                                 "frozen_fc95_source_joins_panel_gate_orchestration_output_owner_reused": True,
                                 "491653_arithmetic_and_014f_original_panel_identity_unchanged": True,
                                 "existing_distinct_descriptor_input_review_method_field_admission_schemas_retained": True,
                                 "own_descriptor_and_raw_input_reviews_before_panel_work_remain_required": True,
                                 "parent_serial_slot_and_true_input_method_readiness_remain_deferred": True,
                                 "current_Z200_100_bolts_66_screws_HOLD_and_fields_unmodified": True,
                                 "Z180_four_moves_4in_scenario_no_spacer_no_old_force_transfer": True,
                                 "missing_six_references_false_release_and_null_unqualified_resistance_retained": True,
                                 "no_reissue_relabel_archive_prune_or_historical_source_review_edits": True},
        "context": {"before_sha256": context_before, "after_sha256": {n: sha(ROOT / n) for n in contexts},
                    "maintained_prose_owned_by_parent": True},
        "ruff": {"command": ".venv/bin/ruff check --no-cache " + str(OWN.relative_to(ROOT)),
                 "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Source/hash/AST reads and private standard-library synthetic fixtures/stubs only. No genuine descriptor/input construction, production/factory/panel import, CAD/BREP/native/browser, panel preparation/K/frame/q/actions/solve or actual field/admission consumption.",
                   "Frozen 15 new plus 15 old tests and prior numerical/source proofs are authenticated evidence, not rerun or reissued. The fixture definition alone is reused without pytest or target file-writing tests.",
                   "Output ownership is checked with inert reservation stubs and the unchanged frozen source. Full real source closures, real input/panel compatibility, parent execution readiness and serialized force runs remain outside this bounded correction review.",
                   "Writes are exclusive to this new structure helper/receipt; no target, current/history/shared docs/site/index edits, Git/staging, archive/prune or new physical/fabrication/signoff requirements."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    receipt = review()
    destination = OWN.with_name("receipt.json")
    if args.write:
        with destination.open("x") as stream:
            stream.write(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"receipt_sha256": sha(destination), "review_helper_sha256": sha(OWN),
                          "findings": len(receipt["findings"]), "bound_files": receipt["integrity"]["source_target_history_union"]}))
    else:
        print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
