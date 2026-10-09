"""Independent boundary coupons; frozen fixtures, no genuine admission/reducers."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from threading import RLock
from types import SimpleNamespace
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
TARGET = OWN.parents[2]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "consume.py": "673498ce0cb1cb95bf6f263e2710b357f9792eaf8d12020c25a0812dc12a1d80",
    "test_consume.py": "1024873b79c965172ddd7d4324063863c4d41561570f30c24d9cd895b6bd7d44",
    "verification.json": "fe7cdb509058d116049fef87bf91266378d4dc252b68c9e80b64d9a439ce2286",
    "../review-fix-v2/bridge.py": "dc224c51a46f78433df614ce53b76e2a8f4b1a7ac4c436b7d0d212f784388f55",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def load_fixture():
    spec = importlib.util.spec_from_file_location("independent_z180_inert_fixtures", TARGET / "test_consume.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def boundary_controls(tests, scratch):
    observed = {}
    cases = ("extra_config_key", "released_config", "wrong_state", "unaffected_parent_axis", "escaping_reference",
             "escaping_symlink", "reducer_changes_field", "reducer_changes_source", "source_join_exception", "nested_duplicate_key")
    for mode in cases:
        root = scratch / mode
        root.mkdir()
        with pytest.MonkeyPatch.context() as monkey:
            t = tests.tiny.__wrapped__(root, monkey)
            m = tests.m
            callback = m.reduce_admitted
            if mode == "extra_config_key":
                t.config["unexpected"] = True
            elif mode == "released_config":
                t.config["release"]["candidate_accepted"] = True
            elif mode == "wrong_state":
                t.field["state_id"] = "foreign-state"
                t.freeze()
            elif mode == "unaffected_parent_axis":
                t.parent["shafts"][10]["source_axis"]["point_xyz_mm"][2] += 1.
                t.freeze()
            elif mode in {"escaping_reference", "escaping_symlink"}:
                outside = scratch / "foreign.json"
                outside.write_text("{}")
                if mode == "escaping_symlink":
                    (root / "escape.json").symlink_to(outside)
                t.config["sources"]["geometry"] = {"path": "escape.json" if mode == "escaping_symlink" else "../foreign.json",
                                                     "sha256": sha(outside)}
            elif mode in {"reducer_changes_field", "reducer_changes_source"}:
                def mutate(*args, mode=mode, callback=callback, t=t, **kwargs):
                    result = callback(*args, **kwargs)
                    if mode == "reducer_changes_field":
                        args[2]["case_id"] = "mutated"
                    else:
                        (t.root / "proof.bin").write_bytes(b"changed after admission")
                    return result
                monkey.setattr(m, "reduce_admitted", mutate)
            elif mode == "source_join_exception":
                original = t.gate.original
                def original_with_error(original=original, m=m):
                    adapter = original()
                    adapter.require_sources = lambda _data: m.require(False, "inert source join stop")
                    return adapter
                t.gate.original = original_with_error
            elif mode == "nested_duplicate_key":
                field_path = root / "field.json"
                raw = field_path.read_bytes().replace(b'"case_id": "inert-case"',
                    b'"case_id": "foreign", "case_id": "inert-case"')
                assert raw != field_path.read_bytes()
                field_path.write_bytes(raw)
                t.config["field"]["sha256"] = m.digest(raw)
            t.config_ref = tests.write(root, "config.json", t.config)
            try:
                tests.call(t)
            except ValueError as error:
                observed[mode] = str(error)
            else:
                raise AssertionError("boundary corruption accepted: " + mode)
            if mode == "source_join_exception":
                assert t.events[-1] == "source_scope_restored" and "inert_reducer_callback" not in t.events
            if mode not in {"reducer_changes_field", "reducer_changes_source", "source_join_exception"}:
                assert "inert_reducer_callback" not in t.events
    return observed


def retained_unknowns_and_failures(tests, scratch):
    root = scratch / "unknowns"
    root.mkdir()
    with pytest.MonkeyPatch.context() as monkey:
        t = tests.tiny.__wrapped__(root, monkey)
        m, callback = tests.m, tests.m.reduce_admitted
        def exceedance(*args, **kwargs):
            findings, contract = callback(*args, **kwargs)
            findings.update(reference_exceedance=1.7, complete_joint_resistance=None)
            return findings, contract
        monkey.setattr(m, "reduce_admitted", exceedance)
        output = root / "owned.json"
        result = m.consume_to_file(root / "config.json", t.config_ref["sha256"], output)
        assert result["findings"]["reference_exceedance"] == 1.7
        assert result["findings"]["complete_joint_resistance"] is None and result["complete_joint_resistance"] is None
        assert result["nominal_seat_geometry"]["nominal_wood_seats"] is None
        assert all(value is False for value in result["release"].values()) and read(output) == result
    failed = scratch / "interrupted.json"
    m = tests.m
    with patch.object(m, "consume", side_effect=KeyboardInterrupt("inert interruption")):
        try:
            m.consume_to_file("unused", "0" * 64, failed)
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError("interruption swallowed")
    record = read(failed)
    assert record["status"] == "FAILED" and record["exception"]["type"] == "KeyboardInterrupt"
    assert all(value is False for value in record["release"].values())
    before = failed.read_bytes()
    with patch.object(m, "consume") as callback:
        try:
            m.consume_to_file("unused", "0" * 64, failed)
        except FileExistsError:
            pass
        else:
            raise AssertionError("retained failure overwritten")
        assert not callback.called and failed.read_bytes() == before
    return {"reference_exceedance_and_nulls_retained": True, "interrupted_attempt_retained_exclusively": True}


def nominal_and_composition_controls(tests):
    m = tests.m
    rejected = []
    for mode in ("backing", "skin", "own_host", "old_support", "unaffected_source"):
        args = tests.seat_coupon()
        row = args[2]["scenarios"][0]["annular_queries"][0]
        if mode == "backing":
            row["observed_backing_fraction"] = .99
        elif mode == "skin":
            row["inward_skin_mm"] = .1
        elif mode == "own_host":
            row["single_own_host_targets"] = 2
        elif mode == "old_support":
            args[4]["washer_seat_rows"][-1]["full_modeled_support"] = False
        else:
            args[1]["finished_body_observations"][-1]["source"] = {"path": "foreign", "sha256": "0" * 64}
        try:
            m.nominal_seats(*args)
        except ValueError:
            rejected.append(mode)
        else:
            raise AssertionError("nominal support corruption accepted: " + mode)
    args = tests.fitting_coupon()
    args[2]["service_cuts"][-1] = copy.deepcopy(args[2]["service_cuts"][0])
    assert m.washer_composition(*args) is None
    args = tests.fitting_coupon()
    args[0]["fitting_operator_descriptors"][-1]["body"] = "0"
    try:
        m.washer_composition(*args)
    except ValueError:
        rejected.append("duplicate_fitting_body")
    else:
        raise AssertionError("duplicate fitting body accepted")
    return {"nominal_support_and_identity_rejections": rejected, "duplicate_service_cut_stays_null": True}


def mode_hook_controls(module, scratch):
    observed = {}
    plan_path = scratch / "inert-plan.py"
    plan_path.write_text("# inert registry only\n")
    for mode, fails in (("coarse", False), ("rich", False), ("both", False), ("rich", True)):
        calls = []
        old_provider = lambda _plan: "old-provider"
        old_methods = lambda *_args: "old-methods"
        old_composition = lambda *_args: "old-composition"
        coarse = SimpleNamespace(PLAN=plan_path, PLAN_SHA=sha(plan_path), BOUNDARY_LOCK=RLock(), FIELD_SCHEMA="old-schema",
                                 _load_gate=old_provider, _load_plan=lambda: None)
        rich = SimpleNamespace(_methods=old_methods, washer_geometry=old_composition, GATE_SHA="old-gate")
        compiler = SimpleNamespace(checked_ast=lambda _sha: "inert exact compiler")
        def coarse_reduce(_field, *_args, calls=calls, coarse=coarse):
            assert coarse.FIELD_SCHEMA == module.FIELD_SCHEMA
            calls.append("coarse")
            return {"inert": True}
        def rich_reduce(_field, _path, _coarse, _plan, _pins, _contract, calls=calls, rich=rich, fails=fails):
            assert rich.GATE_SHA == "a" * 64 and rich.washer_geometry(None) is None
            calls.append("rich")
            if fails:
                raise ValueError("inert rich-only failure")
            return {"missing_current_inputs": {}}
        coarse._reduce, rich._reduce = coarse_reduce, rich_reduce
        def load(ref, _pins, _label, coarse=coarse, rich=rich, compiler=compiler):
            return {"coarse": coarse, "rich": rich, "compiler": compiler}[
                next(key for key, value in module.FROZEN.items() if ref == value)]
        facade = SimpleNamespace(ARTIFACTS={"parent_geometry": {"path": "inert-parent", "sha256": "b" * 64}})
        config = {"sources": {"gate": {"sha256": "a" * 64}}, "field": {"path": "inert-field"}}
        with patch.object(module, "ROOT", scratch), patch.object(module, "load", load), \
                patch.object(module, "source_contract", return_value={}), \
                patch.object(module, "prepare_contract", return_value=(facade, {}, {})), \
                patch.object(module, "washer_composition", return_value=None):
            try:
                module.reduce_admitted(config, {}, {}, {}, None, mode=mode, samples=3)
            except ValueError as error:
                assert fails and str(error) == "inert rich-only failure"
            else:
                assert not fails
        assert calls == (["coarse", "rich"] if mode == "both" else [mode])
        assert coarse.FIELD_SCHEMA == "old-schema" and coarse._load_gate is old_provider
        assert rich._methods is old_methods and rich.washer_geometry is old_composition and rich.GATE_SHA == "old-gate"
        observed[mode + ("_failure" if fails else "_success")] = "only requested inert callbacks; every hook restored"
    return observed


def main():
    frozen = {str((TARGET / name).resolve().relative_to(ROOT)): expected for name, expected in EXPECTED.items()}
    verification = read(TARGET / "verification.json")
    for ref in verification["preserved_sources"].values():
        frozen[ref["path"]] = ref["sha256"]
    prior_review = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-component-followup-review-v1/testing/receipt.json"
    frozen[str(prior_review.relative_to(ROOT))] = "978136a0dc1ebbd7491f21ea3af94d6c34f179d56b0d1e562361bb4ea1c2a034"

    def unchanged():
        assert all(sha(ROOT / path) == digest for path, digest in frozen.items())

    unchanged()
    tests = load_fixture()
    with tempfile.TemporaryDirectory(prefix="z180-component-testing-") as directory:
        boundary = boundary_controls(tests, Path(directory))
        retention = retained_unknowns_and_failures(tests, Path(directory))
        nominal = nominal_and_composition_controls(tests)
        hooks = mode_hook_controls(tests.m, Path(directory))
        command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(TARGET / "test_consume.py")]
        run = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
        assert run.returncode == 0 and "39 passed" in run.stdout, run.stderr + run.stdout
    unchanged()
    assert not any(name in sys.modules for name in ("cadquery", "OCP", "numpy", "scipy"))
    report = {"schema": "eoere_z180_component_independent_testing_review/v1", "status": "PASS_WITHIN_INERT_SOURCE_SCOPE",
              "confirmed_substantial_findings": [], "source_sha256": frozen,
              "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)}, "all_frozen_sources_unchanged_before_after": True,
              "existing_inert_suite": {"passed": 39, "command": command, "stdout": run.stdout},
              "independent_boundary_corruptions_rejected": boundary, "retention_controls": retention,
              "nominal_and_composition_controls": nominal, "mode_specific_hook_controls": hooks,
              "arithmetic_evidence_reused": {"frozen_rich_testing_receipt_sha256": frozen[str(prior_review.relative_to(ROOT))],
                                              "no_real_reductions_repeated": True},
              "readiness": verification["readiness"], "release": verification["release"],
              "execution": {"only_inert_callbacks_and_dependency_definitions": True,
                            "actual_configs_fields_admissions_reducers_CAD_BREP_native_panel_K_q_solve_or_browser": False,
                            "shared_docs_Git_index_staging_or_commit_changes": False},
              "retention": "Keep compact helper/receipt with deferred consumer. Existing numerical method evidence remains frozen; private fake configs and outputs removed. Genuine consumption remains parent-owned and not ready."}
    output = OWN.with_name("receipt.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output), "bytes": output.stat().st_size,
                      "confirmed_substantial_findings": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
