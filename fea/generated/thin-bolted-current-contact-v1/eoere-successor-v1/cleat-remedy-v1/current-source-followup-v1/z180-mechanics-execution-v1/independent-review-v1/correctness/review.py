"""Bounded independent review; inert controls only, never candidate preparation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[1]
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
TARGETS = {
    "bridge.py": "fc95da9c8b81b8153813b6c98895401c4f4b5cf96e61d68973ba417c386917c6",
    "test_bridge.py": "d02c448019ac7bdc0b7b465337ce52a617d18c5e771c2e307d873bcc9e4b38be",
    "source-preflight.json": "4588317f7790a8982ecd89c66c6b47c4d15474567848ce72ac409f389d3ecc97",
    "verification.json": "0028e21509a60bcf8da1628f7839f37f24c7e0244a959949ad765f07ca200050",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok):
    if not ok:
        raise AssertionError("independent inert review failed")


def rejected(call, text):
    try:
        call()
    except ValueError as error:
        require(text in str(error))
    else:
        raise AssertionError("invalid synthetic source escaped")


def evaluate():
    pins = {str((PACKET / name).relative_to(ROOT)): digest for name, digest in TARGETS.items()}
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()))
    preflight = json.loads((PACKET / "source-preflight.json").read_bytes())
    verification = json.loads((PACKET / "verification.json").read_bytes())
    for name, digest in preflight["source_sha256"].items():
        require(name not in pins or pins[name] == digest)
        pins[name] = digest
    for key in ("files", "inherited_sources_before_after"):
        for name, record in verification[key].items():
            require(name not in pins or pins[name] == record["sha256"])
            pins[name] = record["sha256"]
            require((ROOT / name).stat().st_size == record["bytes"])
    manifest = json.loads((PACKET / "parent-sources-v1.json").read_bytes())
    for key in ("geometry", "parent_descriptors", "parent_geometry", "saved_finished_receiver_evidence", "unchanged_panel_method"):
        ref = manifest[key]
        require(ref["path"] not in pins or pins[ref["path"]] == ref["sha256"])
        pins[ref["path"]] = ref["sha256"]
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins)
    spec = importlib.util.spec_from_file_location("independent_z180_inert_controls", PACKET / "test_bridge.py")
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    a = tests.a
    require(a.PRODUCTION_SHA == "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643")
    require(a.manifest() == manifest)
    require(preflight["missing"] == ["source_export", "inputs", "input_review", "method_input", "source_manifest", "panel_bank"])
    require(preflight["provided"] == {} and preflight["production_readiness_claimed"] is False)
    require(preflight["complete_joint_resistance"] is None and not any(preflight["release"].values()))
    require(preflight["generalized_residual_tolerance_n_inclusive"] == 1e-5)
    require(preflight["nut_spacer_proposal_included"] is False)

    # Reuse only individually inspected inert controls. IO/main fixtures are not run.
    for schema in ("eoere_extended_cleat_cached_source_export/v1", "eoere_lower_cleat_z180_geometry_patch/v1"):
        tests.test_old_or_layout_only_descriptor_rejected_before_source_joins(schema)
    inert_names = (
        "test_distinct_source_joins_then_old_input_and_mismatched_own_rows_reject",
        "test_native_relabel_and_missing_proposal_source_pin_rejected",
        "test_original_panel_source_geometry_and_own_sources_COM_apertures_ports",
        "test_missing_own_review_stops_proxy_before_any_bank_callback",
        "test_proxy_authorization_and_explicit_original_identity_precede_bank_load",
        "test_source_pin_conflict_not_silently_replaced",
        "test_own_method_rejects_missing_descriptor_review_before_authentication",
        "test_own_pending_identity_and_unchanged_inclusive_force_tolerance",
        "test_gravity_Z_translation_wrench_invariant_and_X_translation_rejects",
    )
    for name in inert_names:
        getattr(tests, name)()

    panel_mutations = (
        (lambda data: data["physical_owner_gravity_rows"][0]["center_xyz_mm"].__setitem__(0, 2.), "own panel gravity/COM differs"),
        (lambda data: data["hillman_rows"][0]["source_screw_descriptor"].__setitem__("id", -1), "unchanged own340"),
        (lambda data: data["panel_operator_source_inputs"].__setitem__("geometry", a.GEOMETRY), "original panel-source geometry"),
    )
    for mutate, message in panel_mutations:
        _, _, data, read = tests.fixture()
        mutate(data)
        with patch.object(a, "read_ref", side_effect=read):
            rejected(lambda data=data: a.panel_view(data, data["panel_operator_source_inputs"]), message)
    descriptor_mutations = (
        (lambda data: data["shafts"][0]["metal_roles"][0]["center_of_mass_xyz_mm"].__setitem__(0, 1.), "only Z180 translation"),
        (lambda data: data["shafts"][0]["source_axis"].__setitem__("nominal_under_head_length_mm", 114.3), "retain nominal4in"),
        (lambda data: data["shafts"][4]["point"].__setitem__(2, 180.), "unmoved physical shaft"),
    )
    for mutate, message in descriptor_mutations:
        _, exported, _, read = tests.fixture()
        mutate(exported)
        with patch.object(a, "read_ref", side_effect=read):
            rejected(lambda exported=exported: a.validate_descriptor(exported), message)
    _, _, data, read = tests.fixture()
    data["historical_q"] = [0.]
    with patch.object(a, "read_ref", side_effect=read):
        rejected(lambda: a.require_sources(data), "without predecessor response")

    # Exercise the actual frozen run's review hook, with an in-memory ownership
    # token and inert readers. Neither a candidate input nor output file is built.
    w, events = a.production(), []
    b = w.frozen()
    output_path = HERE / "inert-never-created-field.json"
    input_path = HERE / "inert-never-created-source.json"
    require(not output_path.exists() and not input_path.exists())

    @contextmanager
    def reservation(_path):
        yield SimpleNamespace(path=output_path, owned=lambda: None,
                              write=lambda value: events.append(("unexpected_write", value)))

    ref = lambda digest: {"path": b.bundle.artifact_path(input_path), "sha256": digest}
    args = SimpleNamespace(run=True, case_id="a12-rear", wall_seconds=10., out=output_path,
        inputs=input_path, inputs_sha256="a"*64, input_review=input_path, input_review_sha256="b"*64,
        method_input=input_path, method_input_sha256="c"*64)
    method = {"input": ref(args.inputs_sha256), "input_review": ref(args.input_review_sha256),
              "input_record": ref(args.method_input_sha256)}

    def reject_review(*_args, **_kwargs):
        events.append("independent_review")
        raise ValueError("synthetic review absent")

    with patch.object(w, "reserve", reservation), patch.object(a, "read_method", return_value=method), \
            patch.object(a, "source_pins", return_value={}), patch.object(b, "slot_check", return_value={}), \
            patch.object(b, "read_inputs", return_value=({"raw": True}, {})), \
            patch.object(b.driver, "select_case", return_value=({"selected": True}, {"case_id": args.case_id})), \
            patch.object(b, "authenticate_review", side_effect=reject_review), \
            patch.object(a, "methods", side_effect=AssertionError("invalid review reached panel methods")):
        rejected(lambda: a.run_case(args), "synthetic review absent")
    require(events == ["independent_review"])
    require(b.OWN == w.FROZEN and b.LOADED_SHA == w.FROZEN_SHA)
    require(b.factory.SCHEMA == b.ORIGINAL_SCHEMA and b.factory.read_inputs is b.ORIGINAL_READ)
    require(b.factory.authenticate_source_review is b.ORIGINAL_AUTHENTICATE)
    require(not output_path.exists() and not input_path.exists())
    with patch.object(w, "reserve", side_effect=FileExistsError("synthetic occupied output")), \
            patch.object(w, "frozen", side_effect=AssertionError("occupied output reached frozen import")):
        try:
            a.main(["--out", str(output_path)])
        except FileExistsError:
            pass
        else:
            raise AssertionError("reservation failure escaped")

    # Independent cross-product known answer, including applied free couples.
    wrench = a.applied_wrench([
        {"point_xyz_mm": [2., -3., 4.], "force_xyz_n": [5., 6., -7.], "moment_xyz_nmm": [11., -13., 17.]},
        {"point_xyz_mm": [8., 9., -10.], "force_xyz_n": [-2., 3., 4.]},
    ])
    require(wrench == [3., 9., -3., 74., 9., 86.])
    require({name: sha(ROOT / name) for name in pins} == before)
    return {
        "schema": "independent_z180_execution_source_correctness_review/v1", "findings": [],
        "reviewer_source_sha256": sha(Path(__file__)), "reviewed_sha256": pins,
        "checks": {"source_and_target_pins_before_after": len(pins),
                   "selected_existing_inert_controls_passed": len(inert_names) + 2,
                   "additional_synthetic_source_panel_mutation_rejects": 7,
                   "actual_frozen_review_before_methods_hook_no_outputs": True,
                   "reservation_rejection_before_frozen_import_with_mock_token": True,
                   "scoped_hooks_and_factory_restored": True,
                   "independent_force_plus_cross_product_plus_free_couple_known_answer": True},
        "scope": ["Static review of all four targets, source/schema joins, original491653 execution adapter composition and original014f panel identity.",
                  "Panel own source/volume/COM/aperture/screw/gravity invariant checks; raw/selected independent review and descriptor/method readiness ordering.",
                  "Immutable source provenance, distinct pending/admission schemas, inclusive original1e-5 arithmetic, ownership/failure behavior and false releases."],
        "limits": ["No authentic Z180 final descriptor/input/review/method/slot was available or admitted; source preflight remains production-unready.",
                   "No genuine input construction, panel preparation/K, frame K, candidate solve, CAD/BREP/native/browser work or actual saved-field/q/action consumption.",
                   "Only in-memory synthetic rows, tiny pending-field controls and an inert frozen orchestration failure were executed; no target CLI output or filesystem fixture written.",
                   "Old mechanics arithmetic is reused within frozen provenance, without repeating its complete validation; no capacity, physical applicability, model/hardware adoption or fabrication acceptance."],
    }


if __name__ == "__main__":
    receipt = evaluate()
    with (HERE / "receipt.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"findings": receipt["findings"], "review_sha256": receipt["reviewer_source_sha256"],
                      "receipt_sha256": sha(HERE / "receipt.json"), "checks": receipt["checks"]}))
