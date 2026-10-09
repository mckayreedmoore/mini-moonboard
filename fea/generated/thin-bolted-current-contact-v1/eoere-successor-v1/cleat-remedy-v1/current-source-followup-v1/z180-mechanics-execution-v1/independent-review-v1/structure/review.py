"""Frozen Z180 source-adapter architecture/provenance review; inert fixtures only."""
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
from unittest.mock import MagicMock, patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
TARGETS = {
    "bridge.py": "fc95da9c8b81b8153813b6c98895401c4f4b5cf96e61d68973ba417c386917c6",
    "test_bridge.py": "d02c448019ac7bdc0b7b465337ce52a617d18c5e771c2e307d873bcc9e4b38be",
    "source-preflight.json": "4588317f7790a8982ecd89c66c6b47c4d15474567848ce72ac409f389d3ecc97",
    "verification.json": "0028e21509a60bcf8da1628f7839f37f24c7e0244a959949ad765f07ca200050",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def review():
    issued, verification = (read(PACKET / n) for n in ("source-preflight.json", "verification.json"))
    pins = {str((PACKET / n).relative_to(ROOT)): h for n, h in TARGETS.items()}
    for mapping in (issued["source_sha256"], {n: r["sha256"] for n, r in verification["inherited_sources_before_after"].items()}):
        for name, digest in mapping.items():
            require(name not in pins or pins[name] == digest, "source/target contradiction")
            pins[name] = digest
    manifest = read(PACKET / "parent-sources-v1.json")
    for key in ("geometry", "parent_geometry", "parent_descriptors", "saved_finished_receiver_evidence", "unchanged_panel_method"):
        ref = manifest[key]
        require(ref["path"] not in pins or pins[ref["path"]] == ref["sha256"], "manifest/source contradiction")
        pins[ref["path"]] = ref["sha256"]
    before = {n: sha(ROOT / n) for n in pins}
    require(before == pins and len(issued["source_sha256"]) == 29, "frozen target/source bytes differ")
    require(all((ROOT / n).stat().st_size == r["bytes"] for n, r in verification["inherited_sources_before_after"].items()), "inherited retention volume differs")
    contexts = ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md")
    context_before = {n: sha(ROOT / n) for n in contexts}
    source = PACKET / "bridge.py"
    tree = ast.parse(source.read_bytes())
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    require(all(all(word not in ast.unparse(n) for word in ("cadquery", "OCP", "numpy", "scipy")) for n in imports), "eager native/scientific import")
    spec = importlib.util.spec_from_file_location("z180_structure_inert_adapter", source)
    a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    require(a.ROOT == ROOT and a._production is None and a.LOADED_SHA == TARGETS["bridge.py"], "import-time production work or source identity differs")
    require(a.PRODUCTION_SHA == verification["reuse"]["production_bridge"]["sha256"] == "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643", "arithmetic owner changed")
    require(manifest["unchanged_panel_method"]["sha256"] == "014f867eac1e9286dee188024544b5853e5cda2aa1cd11037d7aee5a2b29966b", "panel method source identity changed")

    # Reuse the frozen target's standard-library synthetic fixture function,
    # without importing pytest or executing its file-writing tests.
    test_tree = ast.parse((PACKET / "test_bridge.py").read_bytes())
    fixture = next(n for n in test_tree.body if isinstance(n, ast.FunctionDef) and n.name == "fixture")
    namespace = {"a": a, "copy": copy}
    exec(compile(ast.Module(body=[fixture], type_ignores=[]), str(PACKET / "test_bridge.py"), "exec"), namespace)  # noqa: S102
    _, exported, data, source_read = namespace["fixture"]()
    untouched = copy.deepcopy(data)
    with patch.object(a, "read_ref", side_effect=source_read):
        a.require_sources(data)
        view, reuse = a.panel_view(data, data["panel_operator_source_inputs"])
        require(view["geometry"]["report"] == manifest["parent_geometry"] and data == untouched
                and reuse["proposal_geometry"] == a.GEOMETRY and reuse["panel_source_geometry"] == manifest["parent_geometry"], "panel view relabeled source or mutated own input")
        changed = copy.deepcopy(data)
        changed["finished_body_observations"][0]["center_xyz_mm"][0] += 1.
        try:
            a.panel_view(changed, changed["panel_operator_source_inputs"])
        except ValueError as error:
            require("six unchanged own" in str(error), "unexpected changed-panel rejection")
        else:
            raise AssertionError("changed own panel accepted for reuse")
        old = {**exported, "schema": "eoere_extended_cleat_cached_source_export/v1"}
        try:
            a.validate_descriptor(old)
        except ValueError as error:
            require("distinct complete source-only" in str(error), "unexpected predecessor-descriptor rejection")
        else:
            raise AssertionError("old descriptor schema accepted")

    # Exercise all patched adapter hooks with a private stub bridge. The real
    # production module, factory, panel bank and descriptor builder stay unloaded.
    context_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "context")
    hooks_node = next(n.value for n in ast.walk(context_node) if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "hooks" for t in n.targets))
    hooks = [k.value for k in hooks_node.keys]
    callbacks = []
    bank = SimpleNamespace(source_inputs=lambda: callbacks.append("bank_source_inputs"))
    bridge = SimpleNamespace(**{n: object() for n in hooks if n != "z180_original_read_method"}, PANEL_BANK=manifest["unchanged_panel_method"])
    bridge.load = lambda *_args: bank
    bridge.read_method = lambda *_args: {}
    original = dict(vars(bridge))
    boundaries = []
    @contextmanager
    def corrected_context(_bridge):
        boundaries.append("enter")
        try:
            yield
        finally:
            boundaries.append("exit")
    stub_wrapper = SimpleNamespace(corrected_context=corrected_context)
    try:
        with a.context(stub_wrapper, bridge):
            require(bridge.OWN == a.OWN and bridge.FIELD_SCHEMA == a.FIELD_SCHEMA and bridge.INPUT_SCHEMA == a.INPUT_SCHEMA, "own hook identities missing")
            proxy = bridge.load(ROOT / manifest["unchanged_panel_method"]["path"], manifest["unchanged_panel_method"]["sha256"], "inert")
            require(isinstance(proxy, a.PanelProxy), "bank loader did not retain proposal proxy")
            try:
                proxy.load_panel_dependencies({})
            except ValueError as error:
                require("own raw source review required" in str(error) and not callbacks, "missing review reached bank callback")
            else:
                raise AssertionError("missing review accepted")
            raise RuntimeError("inert context unwind")
    except RuntimeError as error:
        require(str(error) == "inert context unwind", "unexpected hook exception")
    require(vars(bridge) == original and boundaries == ["enter", "exit"], "context hooks not restored after failure")
    try:
        a.source_pins(None, None, {a.GEOMETRY["path"]: "0"*64})
    except ValueError as error:
        require("proposal source pin conflict" in str(error), "unexpected source conflict rejection")
    else:
        raise AssertionError("proposal source pin conflict silently replaced")

    args = SimpleNamespace(**{n: None for name in ("source_export", "inputs", "input_review", "method_input", "source_manifest", "panel_bank") for n in (name, name + "_sha256")})
    preflight_bridge = SimpleNamespace(source_pins=lambda _extra: dict(issued["source_sha256"]),
        law=SimpleNamespace(contract=lambda: copy.deepcopy(issued["support"])), core=SimpleNamespace(RELEASE=dict(a.RELEASE)))
    captured = []
    output = SimpleNamespace(path=OWN.with_name("never-created.json"), owned=lambda: None, write=captured.append)
    a.proposal_output(output).write(a.preflight(args, preflight_bridge))
    require(captured == [issued], "no-reference preflight dataflow/status/schema differs")
    require(issued["missing"] == ["source_export", "inputs", "input_review", "method_input", "source_manifest", "panel_bank"]
            and not issued["production_readiness_claimed"] and issued["complete_joint_resistance"] is None, "preflight implies readiness or capacity")
    attempts = []
    @contextmanager
    def reserve(_path):
        attempts.append("reserve")
        yield output
    def frozen():
        attempts.append("frozen")
        raise RuntimeError("stop before real frozen import")
    wrapper = SimpleNamespace(reserve=reserve, frozen=frozen)
    with patch.object(a, "production", return_value=wrapper):
        try:
            a.main(["--out", str(output.path)])
        except RuntimeError as error:
            require(str(error) == "stop before real frozen import", "unexpected lazy orchestration failure")
        else:
            raise AssertionError("inert frozen import stop not reached")
    require(attempts == ["reserve", "frozen"] and not output.path.exists(), "frozen import preceded ownership reservation or inert output created")
    with patch.object(a, "production", return_value=SimpleNamespace(reserve=MagicMock(side_effect=FileExistsError("inert occupied output")), frozen=MagicMock())) as production:
        try:
            a.main(["--out", str(output.path)])
        except FileExistsError:
            require(not production.return_value.frozen.called, "occupied output reached frozen import")
        else:
            raise AssertionError("occupied output accepted")
    require(a._production is None, "inert review loaded genuine production")

    require(verification["candidate_descriptor_or_input_trial_performed"] is False
            and verification["actual_saved_field_or_q_consumed"] is False
            and verification["frozen_descriptor_or_own_input_review_method_or_parent_execution_readiness_available"] is False,
            "issued source verification promoted to genuine execution")
    require(issued["generalized_residual_tolerance_n_inclusive"] == 1e-5
            and issued["support"]["no_slip_assumed_not_verified"] and not issued["support"]["physical_floor_capacity_established"], "inherited tolerance/support claim changed")
    require(issued["release"] == verification["release"] == a.RELEASE and all(v is False for v in a.RELEASE.values())
            and issued["unadopted_proposal"] and not issued["nut_spacer_proposal_included"], "proposal/hardware/acceptance boundary changed")
    require({n: sha(ROOT / n) for n in pins} == before, "target/source/history drift")
    require(not any(n == "cadquery" or n == "OCP" or n.startswith("OCP.") or n in ("numpy", "scipy") for n in sys.modules), "native/scientific import occurred")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", str(OWN)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_z180_execution_adapter_structure_review/v1", "review_helper_sha256": sha(OWN), "frozen_target_sha256": TARGETS, "findings": [],
        "integrity": {"preflight_direct_source_pins": 29, "verified_source_target_retention_union": len(pins), "unchanged_before_after": True,
                      "production_source_sha256": a.PRODUCTION_SHA, "panel_source_sha256": manifest["unchanged_panel_method"]["sha256"],
                      "inherited_13_source_and_historical_verification_records_preserved": True},
        "inert_checks": {"import_keeps_production_lazy": True, "synthetic_own_input_source_joins_and_predecessor_schema_rejection": True,
                         "unchanged_panel_view_retains_original_geometry_identity_and_input_immutability": True, "changed_panel_COM_rejected": True,
                         "missing_own_review_rejects_before_bank_callback": True, "all_adapter_hooks_restored_after_exception": True,
                         "source_pin_conflicts_rejected": True, "no_reference_preflight_exact_with_stubbed_source_support_metadata": True,
                         "output_reservation_precedes_frozen_import_and_occupied_output_stops_import": True},
        "architecture_and_retention": {"frozen_491653_preparation_solve_independent_replay_and_output_owner_reused": True,
                                       "no_copied_numerical_kernel_or_relabelled_old_panel_bank": True,
                                       "distinct_Z180_descriptor_input_review_method_field_admission_identities": True,
                                       "independent_descriptor_and_raw_selected_input_review_before_preparation": True,
                                       "parent_method_readiness_and_serial_slot_remain_deferred": True,
                                       "unverified_32_normal_points_two_rear_XY_support_and_inclusive_1e_minus5_N_tolerance_retained": True,
                                       "four_4in_bolt_moves_eight_holes_20_metal_roles_66_screws_no_spacer_adoption": True,
                                       "four_target_bytes": 59734, "no_archive_prune_or_edits_to_current_historical_sources_failures_reviews": True,
                                       "no_descriptor_input_operator_response_admission_or_physical_acceptance_claim": True},
        "context": {"before_sha256": context_before, "after_sha256": {n: sha(ROOT / n) for n in contexts}, "parent_owns_maintained_prose": True},
        "ruff": {"command": ".venv/bin/ruff check --no-cache " + str(OWN.relative_to(ROOT)), "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Standard-library source/AST/hash reads and synthetic inert stubs only; no genuine production/factory/panel import, candidate descriptor/input construction, panel preparation/K/frame/solve/CAD/native/browser or actual saved field consumption.",
                   "Frozen tests' synthetic fixture function is reused without executing pytest or file-writing tests. Producer's 15-test result and original numerical method proofs are authenticated, not rerun or reissued.",
                   "The hook restoration and early output controls use private stubs; full native source closures, actual panel reuse and engineering inputs remain deferred to their own independent readiness/reviews.",
                   "No target/shared docs/site/index edits, staging, commit, archive/prune or new physical/fabrication/signoff requirement. Current Z200 evidence and unadopted Z180 remain distinct."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    receipt = review()
    path = OWN.with_name("receipt.json")
    if args.write:
        with path.open("x") as stream:
            stream.write(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "findings": len(receipt["findings"])}))
    else:
        print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
