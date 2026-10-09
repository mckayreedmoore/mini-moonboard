"""Independent saved-summary review using source bytes and temporary inert JSON."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[1]
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
TARGETS = {
    "summarize.py": "99ead1194671c82e0e28f905e84c4208cf2a82dc1ed4532aaf1aeb13c0c7124d",
    "test_summarize.py": "53fb7a6a9be0678116f877de6b7659a8b9356406765b9ca9035b32059d1dcb7d",
    "source-proof.json": "94fb0a568c3d8332c30653b136c5b57e2d0fdffe4e2353a10a705d90b514be39",
    "verification.json": "d74713c46802bb959b450646175fa08f907ce403ee31cdc3dbae5deaa2b79c09",
}
BASE = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/"
STATIC_CONTRACTS = {
    BASE + "cleat-remedy-v1/current-source-followup-v1/z180-mechanics-execution-v1/component-consumer-v1/consume.py":
        "673498ce0cb1cb95bf6f263e2710b357f9792eaf8d12020c25a0812dc12a1d80",
    BASE + "adjusted-base-mechanics-v1/current-component-bridge-v1/followups-v1/followups.py":
        "a27bacf7260905f69c2a69bae60c0f2cf4ed1f4efd229100e3c8fb846b892798",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok):
    if not ok:
        raise AssertionError("independent summary review failed")


def evaluate():
    pins = {str((PACKET / name).relative_to(ROOT)): digest for name, digest in TARGETS.items()}
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()))
    proof = json.loads((PACKET / "source-proof.json").read_bytes())
    verification = json.loads((PACKET / "verification.json").read_bytes())
    for name, digest in {**proof["verified_source_pins"], **STATIC_CONTRACTS}.items():
        require(name not in pins or pins[name] == digest)
        pins[name] = digest
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins)
    require(proof["actual_six_case_manifest"] is None and proof["actual_summary_output"] is None)
    require(verification["production_manifest_supplied"] is False and verification["production_output_ready"] is False)
    selector_ref = proof["selected_original_definitions"]["source"]
    selector_tree = ast.parse((ROOT / selector_ref["path"]).read_bytes())
    nodes = {n.name: n for n in selector_tree.body if isinstance(n, ast.FunctionDef)}
    for name, digest in proof["selected_original_definitions"]["AST_sha256"].items():
        require(hashlib.sha256(ast.dump(nodes[name]).encode()).hexdigest() == digest)
    spec = importlib.util.spec_from_file_location("independent_inert_z180_summary", PACKET / "test_summarize.py")
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    a = tests.a

    @contextmanager
    def fixture():
        # Only copies of selector/guard/source definitions and fabricated JSON;
        # never real candidate artifacts. Cleanup removes the temporary tree.
        with tempfile.TemporaryDirectory(prefix="z180-summary-independent-") as directory, pytest.MonkeyPatch.context() as monkeypatch:
            yield tests.fixture.__wrapped__(Path(directory), monkeypatch)

    def update_result(f, index, mutate):
        component = f.manifest["cases"][index]["component"]
        result = json.loads((f.root / component["result"]["path"]).read_bytes())
        mutate(result)
        component["result"] = f.save(component["result"]["path"], result)
        process = json.loads((f.root / component["process"]["path"]).read_bytes())
        process["result"] = {**component["result"], "bytes": (f.root / component["result"]["path"]).stat().st_size}
        component["process"] = f.save(component["process"]["path"], process)
        f.ref = f.save("manifest.json", f.manifest)

    with fixture() as f:
        def normal_witness(row):
            row["findings"]["coarse"]["fresh_gross_member_diagnostics"][3]["witnesses"]["fully_braced_normal"]["gross_CD1_comparison"]["fully_braced_component_normal_interaction"] = 3.7
            row["findings"]["rich"]["rich_steel"][1]["summary"]["used_hole_bearing"]["worst"]["comparison"]["bearing_reference_ratio"] = 2.0
        def shear_witness(row):
            row["findings"]["coarse"]["fresh_gross_member_diagnostics"][7]["witnesses"]["sufficient_shear_torsion"]["gross_CD1_comparison"]["equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio"] = 4.1
        update_result(f, 0, normal_witness)
        update_result(f, 1, shear_witness)
        result = a.build(f.manifest, f.ref)
        require([r["case_id"] for r in result["cases"]] == list(a.CASES))
        first, second = result["cases"][:2]
        normal = "fully_braced_component_normal_interaction"
        shear = "equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio"
        witness = first["coarse"]["gross_raw_members"][normal]["worst"]
        require(witness["member"] == "member3" and witness["value"] == 3.7)
        require(witness["local_N_Vu_Vv_T_Mu_Mv_n_nmm"] == [3]*6)
        require(second["coarse"]["gross_raw_members"][normal]["worst"]["value"] == 2.1)
        require(second["coarse"]["gross_raw_members"][shear]["worst"]["member"] == "member7")
        require(first["coarse"]["gross_raw_members"][shear]["worst"]["value"] == 2.1)
        require(first["rich"]["steel_scenarios"][0]["summary"]["used_hole_bearing"]["worst"]["bearing_reference_ratio"] == 1.5)
        require(first["rich"]["steel_scenarios"][1]["summary"]["used_hole_bearing"]["worst"]["bearing_reference_ratio"] == 2.0)
        require(first["coarse"]["source_limits"] == ["own inert field limit"])
        require(first["coarse_selector_limits_provenance"]["source"] == f.manifest["cases"][0]["field"])
        require(first["rich"]["shaft"]["worst"]["axis_id"] == "shaft99")
        require(first["outer_snapshot_caveats"]["complete_outer_pre_snapshot_claimed"] is False)
        require(second["outer_snapshot_caveats"]["complete_outer_pre_snapshot_claimed"] is True)
        require(len(first["nominal_seat_geometry"]["new_own_nominal_seats"]) == 16)
        require(first["nominal_seat_geometry"]["unaffected_proof_count"] == 96)
        require(result["complete_joint_resistance"] is None and not any(result["release"].values()))
        require(result["unadopted_proposal"] is True and result["spacer_or_4p5in_adopted"] is False)
        require(result["execution"]["gate_consumer_reducer_CAD_operator_K_q_native_or_solve_called"] is False)
    negatives = (
        ("order", "six exact ordered"), ("duplicate_state", "six unique"), ("old_schema", "Z180 schemas"),
        ("raw_pair", "raw field/admission"), ("samples", "command binding"), ("drift", "process source drift"),
        ("spacer_source", "component source"), ("non_null", "null resistance"), ("seat", "own16/unchanged96"),
        ("sample_grid", "41 samples"), ("producer", "corrected consumer"), ("log_ref", "recorded reference differs"),
        ("snapshot_missing", "coverage caveat"),
    )
    for mutation, message in negatives:
        with fixture() as f:
            tests.test_saved_pair_process_and_source_negative_controls(f, mutation, message)
    additional = (
        (lambda r: r["nominal_seat_geometry"]["new_own_nominal_seats"][0].update(capture_id="own1"), "distinct own16/inherited96"),
        (lambda r: r["nominal_seat_geometry"]["new_own_nominal_seats"][0].update(capture_id="unchanged0"), "distinct own16/inherited96"),
        (lambda r: r.update(case_id="a1-rear"), "same-state own identity"),
    )
    for mutate, message in additional:
        with fixture() as f:
            update_result(f, 0, mutate)
            with pytest.raises(ValueError, match=message):
                a.build(f.manifest, f.ref)
    with fixture() as f:
        component = f.manifest["cases"][0]["component"]
        process = json.loads((f.root / component["process"]["path"]).read_bytes())
        after = json.loads((f.root / process["source_pins_after"]["path"]).read_bytes())
        after["result_pins_missing_before_snapshot"] = []
        ref = f.save(process["source_pins_after"]["path"], after)
        process["source_pins_after"] = {**ref, "bytes": (f.root / ref["path"]).stat().st_size}
        component["process"] = f.save(component["process"]["path"], process)
        f.ref = f.save("manifest.json", f.manifest)
        with pytest.raises(ValueError, match="missing-before coverage caveat"):
            a.build(f.manifest, f.ref)
    for text in ('{"x":NaN}', '{"x":Infinity}', '{"x":1e999}', '{"x":-1e999}', '{"x":1,"x":2}'):
        with pytest.raises(ValueError):
            a.decode(text)
    with fixture() as f, pytest.MonkeyPatch.context() as monkeypatch:
        tests.test_exact_selector_hash_checked_before_ast(f, monkeypatch)
    require({name: sha(ROOT / name) for name in pins} == before)
    return {
        "schema": "independent_z180_saved_summary_correctness_review/v1", "findings": [],
        "reviewer_source_sha256": sha(Path(__file__)), "reviewed_sha256": pins,
        "checks": {"target_and_source_hashes_before_after": len(pins),
                   "all_seven_selector_AST_hashes_exact": True,
                   "six_case_inert_summary_separate_complete_witnesses_and_steel_scenarios": True,
                   "coarse_field_limit_and_single_rich_wrapper_contracts": True,
                   "existing_source_pair_case_process_negative_controls": len(negatives),
                   "additional_seat_identity_case_and_missing_before_rejects": 4,
                   "duplicate_and_nonfinite_JSON_rejects": 5,
                   "wrong_selector_hash_rejected_before_AST_parse": True},
        "limits": ["Source-method review only; no real candidate artifact, raw field/config, production roster or summary output was read or constructed.",
                   "Only selector/guard definitions executed against fabricated temporary JSON/source copies, removed after each inert fixture; no gate, consumer or reducer imported/called.",
                   "Static consumer/rich return-schema inspection and byte hashes support the adapter contract; prior engineering arithmetic/classifiers are preserved, not independently re-audited.",
                   "The summary preserves nominal112/own16/inherited96 geometry and incomplete historical outer pre-snapshots without a pressure, capacity, physical, panel-remedy, hardware/geometry adoption or release claim."],
    }


if __name__ == "__main__":
    receipt = evaluate()
    with (HERE / "receipt.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"findings": receipt["findings"], "review_sha256": receipt["reviewer_source_sha256"],
                      "receipt_sha256": sha(HERE / "receipt.json"), "checks": receipt["checks"]}))
