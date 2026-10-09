"""Independent force-bridge correctness review; metadata and inert fixtures only.

Run with PYTHONDONTWRITEBYTECODE=1 uv run python PATH/TO/review.py.
No candidate input builder, panel bank, CAD reader, preparation or solve runs.
The sole persistent output is the sibling exclusive receipt.json.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import CodeType
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[3]
TARGET = PACKET / "adjusted-base-mechanics-v1/current-force-bridge-v1"
EXPECTED = {
    "bridge.py": "ddc85386050d97145597dc720bef78634c9b326f0878aced8c02c8df4710c05b",
    "test_bridge.py": "72cdd692b40df93e2a6a194e31d9bd03fe7125baf6fb605a09b66954bbecacf6",
    "source-preflight.json": "4118719a61da4645085f4840b1888ac6df600df2307edc8c0d40ffb79d4eafe0",
    "verification.json": "7ca9a676dd1c7b1ae41a4408caeae6d0d22c0ee57da43095663b8587238d5fab",
    "review-fix-v2/bridge.py": "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643",
    "review-fix-v2/test_bridge.py": "cdaf6e63a542b738fd81b99e4c211952dd46765fb8c2082a1d43c0d977b88c90",
    "review-fix-v2/source-preflight.json": "158b2fd603cabac3d5e39ac81f726da251ce6a393b797e7e047daef3dee85fdc",
    "review-fix-v2/verification.json": "18903e345a4c7f59ecbf0036cd68946733981f8a8b9de29a3fef0a63b68a3f7a",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def authenticate():
    expected = {str((TARGET / name).relative_to(ROOT)): value for name, value in EXPECTED.items()}
    preflight = json.loads((TARGET / "review-fix-v2/source-preflight.json").read_bytes())
    expected.update(preflight["source_sha256"])
    observed = {name: sha(ROOT / name) for name in expected}
    assert observed == expected, "frozen target or source closure changed"
    return observed


def signature(code, replacements=None):
    """Compare executable structure while ignoring filename/line positions."""
    replacements = replacements or {}
    def constant(value):
        if isinstance(value, CodeType):
            return signature(value, replacements)
        if isinstance(value, str):
            return replacements.get(value, value)
        return value
    return (code.co_code, tuple(constant(c) for c in code.co_consts), code.co_names,
            code.co_varnames, code.co_freevars, code.co_cellvars, code.co_argcount,
            code.co_posonlyargcount, code.co_kwonlyargcount, code.co_flags,
            code.co_exceptiontable)


def rejects(callback):
    try:
        callback()
    except (ValueError, FileExistsError):
        return
    raise AssertionError("negative fixture was accepted")


def source_code(path, name, replacements=None):
    """Compile original function alone, matching Python's isolated-AST context.

    Whole-module imports change NULL-call bytecode optimization in Python;
    compiling both original and current functions alone removes that artifact.
    """
    tree = ast.parse(Path(path).read_bytes())
    node = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name))
    for item in ast.walk(node):
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            item.value = (replacements or {}).get(item.value, item.value)
    module = compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), "exec")
    return next(c for c in module.co_consts if isinstance(c, CodeType) and c.co_name == name)


def pending(b):
    gradient = [1e-5]
    return {"schema": b.FIELD_SCHEMA, "release": dict(b.core.RELEASE),
        "disposition": "CONVERGED_CANDIDATE_PENDING_INDEPENDENT_ADMISSION",
        "analytical_support_scenario": b.law.contract(), "independent_admission_required": True,
        "usable_conditional_actions": True, "response": {"converged": True,
            "original_floor_switching_law_used": False, "original_joint_and_normal_laws_used": True,
            "physical_residual_uses_unmodified_laws": False,
            "physical_residual_uses_declared_support_scenario": True,
            "generalized_residual_tolerance_n": 1e-5,
            "legacy_nonbearing_key_means_disabled_xy_hosts": True,
            "q": [0.], "q_canonical_sha256": b.canonical([0.]),
            "gradient_n": gradient, "gradient_canonical_sha256": b.canonical(gradient), "gradient_inf_n": 1e-5,
            "fixed_floor_support_v1": {**b.law.contract(),
                "normal_force_n_by_host": dict.fromkeys(b.law.RESTRAINED_HOSTS, 1.),
                "both_credited_legs_in_bearing": True}}}


def consumer_fixture(b, w):
    field = pending(b)
    field.update(state_id="synthetic-current-consumer-fixture", case_id="a12-rear", accessory_placement="top",
        source_inputs={"cases": [{"case_id": "a1-rear"}]},
        source_sha256={b.bundle.artifact_path(w.OWN): w.LOADED_SHA},
        operator_bundle={"arrays": {"path": "synthetic-not-read.npz", "sha256": "a" * 64}},
        original_operator_fingerprint_sha256="b" * 64,
        current_method_input={"path": "synthetic-not-read.json", "sha256": "c" * 64},
        source_case_selection={"case_id": "a12-rear"}, current_panel_operator_preparation={"fixture": True})
    field.update({key: [] for key in b.base.TABLES})
    receipt = {"schema": b.ADMISSION_SCHEMA, b.SUCCESS: True,
        **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
        "admission_source_sha256": w.LOADED_SHA, "support_contract": b.law.contract(),
        "source_path": b.bundle.artifact_path(w.OWN), "release": dict(b.core.RELEASE),
        "q_canonical_sha256": field["response"]["q_canonical_sha256"],
        "gradient_canonical_sha256": field["response"]["gradient_canonical_sha256"],
        "declared_law_checks": {
            "full_signed_gradient_canonical_sha256": field["response"]["gradient_canonical_sha256"],
            "gradient_inf_n": 1e-5, "floor_force_and_declared_fixed_rear_leg_mask_replayed": True},
        "normal_force_n_by_host": field["response"]["fixed_floor_support_v1"]["normal_force_n_by_host"],
        "operator_bundle": field["operator_bundle"],
        "original_operator_fingerprint_sha256": field["original_operator_fingerprint_sha256"],
        "method_input": field["current_method_input"], "source_case_selection": field["source_case_selection"],
        "current_panel_operator_preparation_sha256": b.canonical(field["current_panel_operator_preparation"]),
        "table_canonical_sha256": {key: b.canonical(field[key]) for key in b.base.TABLES},
        "source_sha256": field["source_sha256"]}
    return field, receipt


def payload(b, field, receipt):
    raw = json.dumps(field, sort_keys=True, allow_nan=False).encode()
    receipt.update(input_raw_sha256=hashlib.sha256(raw).hexdigest(), input_canonical_sha256=b.canonical(field))
    return raw


def main():
    before = authenticate()
    spec = importlib.util.spec_from_file_location("independent_current_force_correctness", TARGET / "review-fix-v2/bridge.py")
    w = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(w)
    b = w.frozen()
    checks = []
    with w.corrected_context(b):
        functions = b.admission_functions()
        assert signature(functions["require_pending_field"].__code__) == signature(source_code(b.old_gate.OWN, "require_pending_field"))
        for name in ("audit", "require_admitted_payload"):
            assert signature(functions[name].__code__) == signature(source_code(b.old_gate.OWN, name, b.ADMISSION_REPLACEMENTS))
        checks.append("Three current admission clones retain original executable structure with only declared provenance string replacements")
        replacements = {
            "eoere-a12-": b.STATE_PREFIX,
            "eoere_first_order_common_shaft_four_port_candidate/v1": b.FIELD_SCHEMA,
            "support_state_search_v1": "fixed_floor_support_v1",
            "accepted_enabled_centroid_xy_hosts": "enabled_centroid_xy_hosts",
            "Whole-foot centroid no-slip is an unverified analytical assumption; no friction capacity, anchor or no-separation clamp.":
                "Only rear-leg centroid XY springs are credited; both legs must remain in bearing. Other feet are normal-only. No-slip and floor capacity remain unverified.",
            "fresh full original-law gradient must be a finite full-coordinate vector":
                "fresh declared-support gradient must be a finite full-coordinate vector",
            "fresh full original-law gradient exceeds original tolerance":
                "fresh declared-support gradient exceeds the unchanged force tolerance"}
        execute = b.compile_execute(lambda extra=None: extra or {})
        assert signature(execute.__code__) == signature(source_code(b.core.OWN, "execute", replacements))
        assert execute.__globals__["search"].compatible_contact_solve is b.law.solve
        assert execute.__globals__["search"]._fresh_fields is b.core.search._fresh_fields
        checks.append("Producer clone preserves original arithmetic and recovery bytecode; support dispatcher alone targets reviewed fixed-floor law")
        verified = b.compile_function(b.driver.OWN, "verify_selected_case", {**vars(b.driver), "GEOMETRY_SHA": b.GEOMETRY["sha256"]})
        assert signature(verified.__code__) == signature(source_code(b.driver.OWN, "verify_selected_case"))
        assert verified.__globals__["GEOMETRY_SHA"] == b.GEOMETRY["sha256"]
        functions["require_pending_field"](pending(b))
        for key, value in (("gradient_inf_n", 1.000000001e-5), ("q", [float("nan")]),
                           ("original_floor_switching_law_used", True), ("wall_time_limit_reached", True)):
            field = pending(b)
            field["response"][key] = value
            rejects(lambda field=field: functions["require_pending_field"](field))
        field = pending(b)
        field["response"]["fixed_floor_support_v1"]["normal_force_n_by_host"][b.law.RESTRAINED_HOSTS[0]] = 1e-7
        rejects(lambda: functions["require_pending_field"](field))
        checks.append("Inclusive 1e-5 pending-field boundary accepted; five nonfinite, residual, support, old-law and interrupted-field controls reject")
        with patch.object(b, "source_pins", side_effect=lambda extra=None, **kwargs: dict(extra or {})), \
                patch.object(b, "read_method", return_value={"synthetic": True}):
            consume = b.admission_functions()["require_admitted_payload"]
            field, receipt = consumer_fixture(b, w)
            accepted, pins = consume(payload(b, field, receipt), receipt, admission_sha256=w.LOADED_SHA)
            assert accepted == field and pins == field["source_sha256"]
            mutations = [
                lambda f, r: f.update(schema=b.old_runner.FIELD_SCHEMA),
                lambda f, r: f["release"].update(climbing_released=True),
                lambda f, r: f["source_case_selection"].update(case_id="a1-rear"),
                lambda f, r: r.update(q_canonical_sha256="0" * 64),
                lambda f, r: r.update(method_input={"path": "foreign", "sha256": "0" * 64}),
                lambda f, r: f["panel_screw_actions"].append({"case_id": "a12-rear", "force": 1.}),
                lambda f, r: r.update(admission_source_sha256="0" * 64),
                lambda f, r: r.update(source_path=b.bundle.artifact_path(b.old_gate.OWN)),
            ]
            for mutate in mutations:
                trial, issued = copy.deepcopy(field), copy.deepcopy(receipt)
                mutate(trial, issued)
                raw = payload(b, trial, issued)  # Keep whole-payload hashes valid to exercise inner joins.
                rejects(lambda raw=raw, issued=issued: consume(raw, issued, admission_sha256=w.LOADED_SHA))
        checks.append("Actual cloned consumer accepts one inert bound pair and rejects eight independently mutated schema/release/case/q/method/action/gate/source identities")
    assert b.OWN == w.FROZEN and b.LOADED_SHA == w.FROZEN_SHA
    assert b.factory.SCHEMA == b.ORIGINAL_SCHEMA and b.factory.read_inputs is b.ORIGINAL_READ
    assert b.factory.authenticate_source_review is b.ORIGINAL_AUTHENTICATE
    with tempfile.TemporaryDirectory(prefix="fixtures-", dir=OWN.parent) as directory:
        directory = Path(directory)
        out = directory / "attempt.json"
        with patch.object(w, "frozen", side_effect=RuntimeError("inert pre-import sentinel")):
            try:
                w.main(["--out", str(out)])
            except RuntimeError as error:
                assert str(error) == "inert pre-import sentinel"
            else:
                raise AssertionError("failure callback unexpectedly succeeded")
        failure = json.loads(out.read_bytes())
        assert failure["status"] == "FAILED" and failure["accepted_q"] is None and failure["accepted_actions"] is None
        assert not any(failure["release"].values())
        preserved = out.read_bytes()
        with patch.object(w, "frozen", side_effect=AssertionError("existing output reached imports")):
            rejects(lambda: w.main(["--out", str(out)]))
        assert out.read_bytes() == preserved
        link = directory / "dangling.json"
        link.symlink_to(directory / "missing")
        rejects(lambda: w.main(["--out", str(link)]))
    checks.append("Failed import leaves exclusive null-action false-release receipt; repeat and dangling outputs refuse before imports")
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--import-mode=importlib",
               str(TARGET / "test_bridge.py"), str(TARGET / "review-fix-v2/test_bridge.py")]
    result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=True)
    assert "32 passed" in result.stdout, result.stdout
    after = authenticate()
    assert after == before
    receipt = {"schema": "eoere_current_force_bridge_independent_correctness_review/v2",
        "status": "NO_SUBSTANTIAL_FINDINGS_WITHIN_METADATA_AND_TINY_FIXTURE_SCOPE",
        "findings": [], "checks": checks, "existing_suite": {"command": command, "output": result.stdout.strip()},
        "source_sha256_before": before, "source_sha256_after": after,
        "sources_exact_before_after_unchanged": True,
        "review_script": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "candidate_inputs_panel_bank_CAD_BRep_preparation_K_current_q_actions_native_solve_or_browser_run": False,
        "limits": ["No current field, current operator bundle or current admission exists; production was not exercised.",
                   "Synthetic consumer pair exercises bindings only; it is not a candidate field or an issued admission.",
                   "Descriptor manifest remains descriptor-only; source/input/method readiness and matching current force evidence remain outstanding.",
                   "Reference exceedances, null complete joint resistance and unverified no-slip assumption remain unchanged."],
        "release": dict(b.core.RELEASE),
        "retention": {"active": "Frozen target, source dependencies and this review evidence", "archive_or_prune_performed": False}}
    with OWN.with_name("receipt.json").open("x") as output:
        json.dump(receipt, output, indent=2, sort_keys=True, allow_nan=False)
        output.write("\n")
    print(json.dumps({"status": receipt["status"], "authenticated_sources": len(before),
                      "receipt_sha256": sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
