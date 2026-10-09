"""Bounded catalog runtime-wrapper testing; frozen inputs, owned scratch IO."""
from __future__ import annotations

import builtins
import copy
import hashlib
import importlib.util
import io
import json
import os
import runpy
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import FunctionType, SimpleNamespace
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
OUT = OWN.parent
PACKET = OUT.parent.parent
FIXTURE = PACKET.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "adapter-v2.py": "dae93a7011242ad3878f47040cbf3af9cd224d7077eb503621a8816d55cd4014",
    "result-v3.json": "1060bc7a57fb90b6dc8b3dd1aeb18bb863eb3e0fbe7dd2043c524a15c5d48fbf",
    "result-v3.svg": "4b52eaba8f98d5457b606061f5d51eace14bc222d38dc6bc0f873d91ff2e1b6b",
    "verify-v2.py": "2f01212e390c5ea53a23821ecb6042e82fe0c9b64fd1fc54341c0944b3c0757f",
    "verification-v2.json": "286c4df35620d46d4a3276904ffb6f4997c5a0cf57f8c49b6e113a0f9231410e",
    "controls01/publication-file-inventory-v2.json": "e0f7e412e4f8a64385dc564d7793c8b3b9cdf6fbe256c561c7c8eb9f1497f514",
}
PRIOR_REVIEW_SHA = "9fddef5ba3f4c8148eab1ce2858671ef54aceda46b9bb6bae0434353893bd00e"
ALTERNATE = "3.12.99 (synthetic runtime-only testing control, not another interpreter)"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, (*path, key))
    elif isinstance(value, list):
        for key, child in enumerate(value):
            yield from leaves(child, (*path, key))
    else:
        yield path, value


def different(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value + 1
    if isinstance(value, str):
        return value + "_testing_mutation"
    return "_testing_nonnull_mutation"


def review():
    prior_path = PACKET / "independent-review-v1/testing/review.py"
    assert sha(prior_path) == PRIOR_REVIEW_SHA
    # Reuse the retained testing utility API, not its review execution or files.
    prior = load(prior_path, "retained_catalog_testing_utilities")
    require, rejected, change = prior.require, prior.rejected, prior.change
    before = {name: sha(PACKET / name) for name in EXPECTED}
    require(before == EXPECTED, "six target bytes changed")
    wrapper = load(PACKET / "adapter-v2.py", "catalog_v2_actual_producer")
    verifier = load(PACKET / "verify-v2.py", "catalog_v2_actual_verifier")
    generic_verifier = load(FIXTURE / "verify.py", "retained_generic_guard_API")
    v1_verifier = load(PACKET / "verify.py", "retained_catalog_decimal_API")
    saved = json.loads((PACKET / "result-v3.json").read_bytes())
    issued = json.loads((PACKET / "verification-v2.json").read_bytes())
    inventory = json.loads((PACKET / "controls01/publication-file-inventory-v2.json").read_bytes())
    inventory_before = {name: {"sha256": sha(PACKET / name), "bytes": (PACKET / name).stat().st_size}
                        for name in inventory["files"]}
    require(inventory_before == inventory["files"], "publication inventory differs")
    require(sum(row["bytes"] for row in inventory_before.values()) == inventory["total_bytes_excluding_this_inventory_and_parent_owned_reviews"], "inventory total")
    require(sum(inventory_before[name]["bytes"] for name in inventory["corrected_final_files"]) == inventory["new_corrected_final_file_bytes"], "v2 byte total")
    original_shared_loader = runpy.run_path
    actual, old = wrapper.calculate()
    require(actual == {k: v for k, v in saved.items() if k != "drawing"}, "actual current scalar replay")
    require(old["drawing"](actual) == (PACKET / "result-v3.svg").read_bytes(), "actual unchanged drawing replay")
    pins = saved["source_sha256"]
    require(len(pins) == 30 and saved["source_pin_count"] == 30 and all(sha(ROOT / n) == h for n, h in pins.items()), "thirty live source pins")
    decimal = v1_verifier.decimal_corners(saved)
    require(decimal == issued["reused_independent_decimal_checks"] and decimal["independent_decimal_endpoint_corners"] == 256, "retained independent Decimal API")
    runtime_api = verifier.runtime_controls(vars(wrapper), actual)
    require(runtime_api == issued["runtime_reproduction_controls"], "actual runtime-control API replay")

    recorded = json.loads((FIXTURE / "result.json").read_bytes())
    recorded.pop("drawing")
    alternate = copy.deepcopy(recorded)
    alternate["execution"]["python"] = ALTERNATE
    untouched = copy.deepcopy(alternate)
    require(wrapper.normalized_generic(alternate, recorded) == recorded and alternate == untouched, "runtime-only acceptance and immutability")
    normalizer_controls = []
    for path, value in leaves(recorded):
        if path == ("execution", "python"):
            continue
        bad = copy.deepcopy(alternate)
        change(bad, path, different(value))
        normalizer_controls.append({"path": list(path), "rejection": rejected(lambda bad=bad: wrapper.normalized_generic(bad, recorded))})
    structural_controls = []
    for label, bad in (("missing_execution", {k: v for k, v in alternate.items() if k != "execution"}),
                       ("extra_top_level", {**alternate, "unexpected": True})):
        structural_controls.append({"name": label, "rejection": rejected(lambda bad=bad: wrapper.normalized_generic(bad, recorded))})
    for value in (None, False, 3.12, [], {}):
        bad = copy.deepcopy(alternate)
        bad["execution"]["python"] = value
        structural_controls.append({"name": "nonstring_runtime_" + type(value).__name__, "rejection": rejected(lambda bad=bad: wrapper.normalized_generic(bad, recorded))})

    source_controls = []
    original_sha = wrapper.sha
    for name in wrapper.PREVIOUS:
        boundary = Mock(side_effect=AssertionError("loader entered before frozen-v1 rejection"))
        with patch.object(wrapper, "sha", side_effect=lambda path, name=name: "0" * 64 if Path(path) == PACKET / name else original_sha(path)), patch.object(wrapper, "runpy", SimpleNamespace(run_path=boundary)):
            message = rejected(lambda: wrapper.method_with_runtime_join({}))
        require(not boundary.called, "source rejection did work")
        source_controls.append({"source": name, "rejection": message, "before_loader": True})

    def simulated_loader(*, mutate=None, change_wrapper=False):
        def loader(path, *args, **kwargs):
            method = original_shared_loader(path, *args, **kwargs)
            if Path(path).resolve() == FIXTURE / "design.py":
                evaluate = method["evaluate"]

                def changed_runtime():
                    inp, result, shapes = evaluate()
                    result["execution"]["python"] = ALTERNATE
                    if mutate is not None:
                        field, replacement = mutate
                        change(result, field, replacement)
                    return inp, result, shapes

                method["evaluate"] = changed_runtime
            if change_wrapper and Path(path).resolve() == PACKET / "adapter-v2.py":
                globals_ = method["calculate"].__globals__
                globals_["sys"] = SimpleNamespace(version=ALTERNATE)
                globals_["runpy"] = SimpleNamespace(run_path=simulated_loader())
            return method
        return loader

    production_controls = []
    production_changes = [(("pointwise_error_and_reach_budget", "relative_bore_screw_bound_mm"), 1.501),
                          (("execution", "native_BREP_CAD_mesh_FEA_global_force_or_physical_execution"), True),
                          (("release", "geometry_adoption"), True),
                          (("current_geometry_or_100_axes_or_66_screws_changed",), True),
                          (("current_Z_mm",), 201), (("proposed_Z_mm",), 181)]
    for path, replacement in production_changes:
        with patch.object(wrapper, "runpy", SimpleNamespace(run_path=simulated_loader(mutate=(path, replacement)))):
            production_controls.append({"path": list(path), "rejection": rejected(wrapper.calculate)})
    with patch.object(wrapper, "runpy", SimpleNamespace(run_path=simulated_loader())):
        alternate_result, _ = wrapper.calculate()
    require(alternate_result["runtime_reproduction"]["generic_live_execution_python"] == ALTERNATE, "production provenance missing")
    require({k: v for k, v in alternate_result.items() if k != "runtime_reproduction"} == {k: v for k, v in actual.items() if k != "runtime_reproduction"}, "runtime-only production changed arithmetic")

    cli_controls = []
    virtual = PACKET / ("_testing_unwritten_v2_" + str(os.getpid()) + ".json")
    require(not os.path.lexists(virtual), "virtual leaf already exists")
    # Actual verifier main: a different allowed live runtime is rejected before
    # its runtime control API or any output. No input/source hash is altered.
    runtime_loader = SimpleNamespace(run_path=simulated_loader(change_wrapper=True))
    with patch.object(verifier, "runpy", runtime_loader), patch.object(sys, "argv", [str(PACKET / "verify-v2.py"), "--out", str(virtual)]):
        runtime_main_rejection = rejected(verifier.main)
    require(runtime_main_rejection == "v2 wrapper exact scalar/source replay" and not os.path.lexists(virtual), "runtime verifier main observation changed")
    original_verifier_sha = verifier.sha
    for name in verifier.EXPECTED:
        boundary = Mock(side_effect=AssertionError("loader entered before v2 input rejection"))
        with patch.object(verifier, "sha", side_effect=lambda path, name=name: "0" * 64 if Path(path) == PACKET / name else original_verifier_sha(path)), patch.object(verifier, "runpy", SimpleNamespace(run_path=boundary)), patch.object(sys, "argv", [str(PACKET / "verify-v2.py"), "--out", str(virtual)]):
            message = rejected(verifier.main)
        require(not boundary.called and not os.path.lexists(virtual), "v2 input rejection did work")
        cli_controls.append({"name": "verifier_frozen_" + name, "rejection": message, "before_loader": True})

    with tempfile.TemporaryDirectory(prefix="scratch-", dir=OUT) as raw:
        scratch = Path(raw)
        (scratch / "controls01").mkdir()
        (scratch / "result.json").write_bytes(b"owned historical-result output guard fixture")
        original_guards = generic_verifier.guard_checks

        def own_guards(function):
            with patch.object(generic_verifier, "HERE", scratch), patch.dict(function.__globals__, {"HERE": scratch}):
                return original_guards(function)

        guards = own_guards(old["output_paths"])
        require(guards == issued["reused_output_guard_controls"] and len(guards) == 8, "actual inherited output guards")

        def producer_loader(path, *args, **kwargs):
            method = original_shared_loader(path, *args, **kwargs)
            if Path(path).resolve() == PACKET / "adapter.py":
                guard = method["output_paths"]

                def owned_paths(requested):
                    with patch.dict(guard.__globals__, {"HERE": scratch}):
                        return guard(requested)

                method["output_paths"] = owned_paths
            return method

        producer = scratch / "producer.json"
        with patch.object(wrapper, "runpy", SimpleNamespace(run_path=producer_loader)), patch.object(sys, "argv", [str(PACKET / "adapter-v2.py"), "--out", str(producer)]), redirect_stdout(io.StringIO()):
            wrapper.main()
        replay = json.loads(producer.read_bytes())
        replay["drawing"]["path"] = saved["drawing"]["path"]
        require(replay == saved and producer.with_suffix(".svg").read_bytes() == (PACKET / "result-v3.svg").read_bytes(), "owned actual producer main replay")
        producer_hash = sha(producer)
        for label, requested in (("existing_JSON", producer), ("outside_parent", scratch.parent / "unwritten.json"), ("wrong_suffix", scratch / "unwritten.txt")):
            boundary = Mock(side_effect=AssertionError("calculate entered before output rejection"))
            with patch.object(wrapper, "runpy", SimpleNamespace(run_path=producer_loader)), patch.object(wrapper, "calculate", boundary), patch.object(sys, "argv", [str(PACKET / "adapter-v2.py"), "--out", str(requested)]):
                message = rejected(wrapper.main)
            require(not boundary.called and sha(producer) == producer_hash, "producer output rejection did work or overwrote")
            cli_controls.append({"name": "producer_" + label, "rejection": message, "before_calculate": True})
        dangling = scratch / "dangling.json"
        dangling.symlink_to(scratch / "absent.json")
        with patch.object(wrapper, "runpy", SimpleNamespace(run_path=producer_loader)), patch.object(wrapper, "calculate", Mock(side_effect=AssertionError("dangling output reached calculate"))), patch.object(sys, "argv", [str(PACKET / "adapter-v2.py"), "--out", str(dangling)]):
            cli_controls.append({"name": "producer_dangling_symlink", "rejection": rejected(wrapper.main)})
        require(dangling.is_symlink() and not dangling.exists(), "dangling link not preserved")

        # Main replay retains real source/read/reproduction logic. Only receipt
        # IO and inherited guard scratch are redirected to exclusive own paths.
        owned_verification = scratch / "verification.json"
        original_open, original_stat, original_mkdir = Path.open, Path.stat, Path.mkdir

        def guard_proxy(function):
            return own_guards(function)

        isolated_proxy = FunctionType(guard_proxy.__code__, {}, closure=guard_proxy.__closure__)

        def verifier_loader(path, *args, **kwargs):
            return {"guard_checks": isolated_proxy} if Path(path).resolve() == FIXTURE / "verify.py" else original_shared_loader(path, *args, **kwargs)

        def redirect_open(path, *args, **kwargs):
            return original_open(owned_verification if path == virtual else path, *args, **kwargs)

        def redirect_stat(path, *args, **kwargs):
            return original_stat(owned_verification if path == virtual else path, *args, **kwargs)

        def redirect_mkdir(path, *args, **kwargs):
            return original_mkdir(scratch / "controls01" if path == PACKET / "controls01" else path, *args, **kwargs)

        with patch.object(verifier, "runpy", SimpleNamespace(run_path=verifier_loader)), patch.object(Path, "open", redirect_open), patch.object(Path, "stat", redirect_stat), patch.object(Path, "mkdir", redirect_mkdir), patch.object(sys, "argv", [str(PACKET / "verify-v2.py"), "--out", str(virtual)]), redirect_stdout(io.StringIO()):
            verifier.main()
        require(owned_verification.read_bytes() == (PACKET / "verification-v2.json").read_bytes() and not os.path.lexists(virtual), "actual verifier main replay not byte exact or wrote shared path")
        verifier_hash = sha(owned_verification)
        for label, requested in (("existing_receipt", PACKET / "verification-v2.json"), ("outside_parent", scratch / "unwritten.json"), ("wrong_suffix", PACKET / "_testing_unwritten.txt")):
            boundary = Mock(side_effect=AssertionError("loader entered before receipt output rejection"))
            with patch.object(verifier, "runpy", SimpleNamespace(run_path=boundary)), patch.object(sys, "argv", [str(PACKET / "verify-v2.py"), "--out", str(requested)]):
                message = rejected(verifier.main)
            require(not boundary.called, "receipt output rejection did work")
            cli_controls.append({"name": "verifier_" + label, "rejection": message, "before_loader": True})

    require(before == {name: sha(PACKET / name) for name in EXPECTED}, "target preservation")
    require(inventory_before == {name: {"sha256": sha(PACKET / name), "bytes": (PACKET / name).stat().st_size} for name in inventory_before}, "historical/publication preservation")
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "source preservation")
    require(runpy.run_path is original_shared_loader, "shared loader changed")
    require(len(saved["release"]) == 13 and all(v is False for v in saved["release"].values()), "release boundary")
    require(len(saved["actual_observations"]) == 9 and all(v == "" for v in saved["actual_observations"].values()), "blank actuals")
    require(all(not row.get("within_generic_allocation", row.get("within_generic_target")) for row in saved["generic_error_allowance_comparisons"].values()) and saved["FISCH_nominal_comparison"]["NL_minus_full_cap_chip_path_reference_mm"] < 0, "unmet targets or negative reference lost")
    return {
        "schema": "eoere_Z180_catalog_adapter_independent_testing_review/v2",
        "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "reused_testing_utility_sha256": PRIOR_REVIEW_SHA,
        "six_target_sha256_before_after": before,
        "publication_inventory_file_count": len(inventory_before), "publication_inventory_bytes": sum(row["bytes"] for row in inventory_before.values()),
        "inventory_and_historical_hash_only_before_after": inventory_before,
        "source_pin_count": 30, "source_pins_authenticated_before_after": pins,
        "actual_current_scalar_and_SVG_replay_exact": True,
        "owned_actual_producer_main_JSON_sha256": producer_hash,
        "producer_main_sole_normalized_difference": "drawing.path points to own temporary SVG",
        "owned_actual_verifier_main_byte_exact_sha256": verifier_hash,
        "reused_independent_Decimal_API": decimal,
        "issued_runtime_control_API_replayed": runtime_api,
        "normalizer_nonruntime_leaf_mutations_rejected": len(normalizer_controls),
        "normalizer_mutated_paths": [row["path"] for row in normalizer_controls],
        "normalizer_additional_structure_controls": structural_controls,
        "production_runtime_join_corruption_controls": production_controls,
        "production_alternate_generic_runtime_accepted_and_provenance_retained": True,
        "frozen_v1_rejections_before_loader": source_controls,
        "actual_CLI_rejection_and_preservation_controls": cli_controls,
        "reused_eight_output_guard_API_controls": guards,
        "runtime_only_actual_verifier_main_rejection": runtime_main_rejection,
        "findings": [{"severity": "medium", "file": str((PACKET / "verify-v2.py").relative_to(ROOT)), "line": 128,
                      "title": "Verifier still requires the original live Python build text",
                      "impact": "The producer intentionally accepts and records a different /execution/python runtime, but verifier main compares all runtime_reproduction fields against saved result-v3. A synthetic alternate generic and wrapper live runtime, with all source bytes and numerical fields intact, fails before verification or output. The later runtime_controls API excludes runtime_reproduction in its successful comparison, so its seven reported controls miss this main-path reproducibility failure. Issued current-interpreter numerical/SVG observations remain correct.",
                      "fix": "Join the live and saved result while excluding only the explicitly permitted live runtime metadata fields; keep recorded runtime, all arithmetic/source/guard fields and provenance schema strict. Record saved and current live runtime separately and add a main-path alternate-runtime positive control."}],
        "shared_runpy_unchanged": True, "all_targets_sources_and_history_unchanged": True,
        "all13_release_flags_false_and9_observations_blank": True,
        "scope": "Actual stdlib scalar/SVG producer API, runtime normalizer and production loader, all non-runtime generic scalar leaf value mutations, reused Decimal endpoint and output-guard APIs, producer/verifier main replay with only final receipt/output binding and guard scratch redirected to exclusive own paths. Runtime controls are synthetic metadata; no second interpreter qualification. Frozen v1 arithmetic/manufacturer evidence reused, not independently re-qualified.",
        "excluded": ["native/CAD/BREP/FEA/global/browser/physical execution", "manufacturer fact or PDF interpretation re-audit", "actual hardware/bit fit or workholding proof", "current Z200 geometry/100 bolts/66 screws/force fields or HOLD changes", "panel remedies, budget relaxation or strength/physical release", "shared files, staging or commit"],
        "mechanics_or_physical_release": False,
    }


if __name__ == "__main__":
    original_import = builtins.__import__
    native_attempts = []

    def no_native(name, *args, **kwargs):
        if name.split(".")[0] in ("cadquery", "OCP", "numpy", "scipy"):
            native_attempts.append(name)
            raise AssertionError("forbidden import: " + name)
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=no_native):
        receipt = review()
    assert not native_attempts
    receipt["native_or_numeric_library_import_attempts"] = native_attempts
    destination = OUT / "receipt.json"
    with destination.open("xb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"receipt": str(destination.relative_to(ROOT)), "sha256": sha(destination), "findings": len(receipt["findings"])}))
