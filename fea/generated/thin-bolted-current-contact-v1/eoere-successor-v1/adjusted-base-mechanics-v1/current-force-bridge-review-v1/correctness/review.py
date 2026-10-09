"""Independent source/stub/consumer checks; never construct current mechanics."""
from __future__ import annotations

import copy
import dis
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import CodeType, SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
TARGET = OWN.parent.parent.parent / "current-force-bridge-v1"
EXPECTED = {
    "bridge.py": "ddc85386050d97145597dc720bef78634c9b326f0878aced8c02c8df4710c05b",
    "test_bridge.py": "72cdd692b40df93e2a6a194e31d9bd03fe7125baf6fb605a09b66954bbecacf6",
    "source-preflight.json": "4118719a61da4645085f4840b1888ac6df600df2307edc8c0d40ffb79d4eafe0",
    "verification.json": "7ca9a676dd1c7b1ae41a4408caeae6d0d22c0ee57da43095663b8587238d5fab",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def refused(call):
    try:
        call()
    except (ValueError, KeyError, TypeError):
        return
    raise AssertionError("negative control unexpectedly passed")


def main():
    assert {name: sha(TARGET / name) for name in EXPECTED} == EXPECTED
    spec = importlib.util.spec_from_file_location("independent_current_force_bridge", TARGET / "bridge.py")
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    pins_before = b.source_pins()
    check_counts = {}

    # Compare semantic instructions, including nested code. CPython can assign
    # different constant indexes to a separately compiled AST of the same code.
    def instructions(code, replacements):
        def value(item):
            if isinstance(item, CodeType):
                return instructions(item, replacements)
            return replacements.get(item, item) if isinstance(item, str) else item
        return [(item.opname, value(item.argval)) for item in dis.get_instructions(code)]

    # Only exactly enumerated outer provenance strings change in admission.
    cloned = b.admission_functions()
    for name, function in cloned.items():
        original = getattr(b.old_gate, name)
        assert instructions(function.__code__, {}) == instructions(original.__code__, b.ADMISSION_REPLACEMENTS)
    old_execute = b.old_runner.compile_execute(lambda extra=None: extra or {})
    new_execute = b.compile_execute(lambda extra=None: extra or {})
    assert instructions(new_execute.__code__, {}) == instructions(old_execute.__code__, {
        b.old_runner.FIELD_SCHEMA: b.FIELD_SCHEMA, b.old_runner.STATE_PREFIX: b.STATE_PREFIX})
    assert callable(new_execute.__globals__["runtime_pins"])
    assert new_execute.__globals__["search"].compatible_contact_solve is b.law.solve
    check_counts["unchanged_cloned_equation_instructions"] = 4

    # A synthetic descriptor export exercises every bridge equality join,
    # without reading a genuine descriptor, panel operator or candidate field.
    export_ref = {"path": "synthetic/current-export.json", "sha256": "e" * 64}
    owners = [{"id": "wood", "kind": "timber", "mass_kg": 2., "center_xyz_mm": [1., 2., 3.]},
              {"id": "panel", "kind": "panel", "mass_kg": 3., "center_xyz_mm": [4., 5., 6.]},
              {"id": "shaft/one", "kind": "shaft", "mass_kg": .5, "center_xyz_mm": [7., 8., 9.]}]
    roles = [{"id": "role/one", "mass_kg": .5, "center_of_mass_xyz_mm": [7., 8., 9.], "basis": "synthetic"}]
    mappings = {
        "timber_rows": "raw_gross_timber_rows", "physical_owner_gravity_rows": "physical_owner_gravity_rows",
        "fitting_poses": "fitting_poses", "fitting_port_bindings": "fitting_ports",
        "all_factory_holes": "all_factory_holes", "shafts": "shafts",
        "finished_receiver_wall_queries": "finished_receiver_wall_queries", "finished_body_observations": "finished_body_observations",
        "direct_contacts": "direct_contacts", "hillman_rows": "hillman_rows",
        "current_panel_machining_descriptors": "current_panel_machining_descriptors", "flange_domains": "flange_domains",
        "flange_shared_face_patches": "flange_shared_face_patches", "timber_and_panel_shared_face_patches": "timber_and_panel_shared_face_patches",
        "shared_pair_query_census": "shared_pair_query_census",
    }
    exported = {key: [{"synthetic": key}] for key in mappings.values()}
    exported.update(schema="eoere_extended_cleat_cached_source_export/v1", geometry=b.GEOMETRY, manifest=b.SOURCE_MANIFEST,
        source_pins_before_after_unchanged=True, native_cached_solid_queries_performed=True,
        native_nominal_flat_reference_flange_masks_created=88, fresh_contact_domains_not_copied_from_old_field=True,
        candidate_CAD_rebuild_mesh_K_assembly_factorization_q_forces_load_cases_or_native_solve_performed=False,
        source_sha256={"synthetic/dependency": "d" * 64, b.GEOMETRY["path"]: b.GEOMETRY["sha256"]}, physical_owner_gravity_rows=owners,
        all_factory_holes=[{"angle_id": "angle", "holes": [{"id": "used", "installed_bolt_axis_id": "axis"},
                                                            {"id": "unused", "installed_bolt_axis_id": None}]}],
        shafts=[{"body": "shaft/one", "metal_roles": roles}], auxiliary_metal_gravity_descriptors=[],
        floor_observations=[{"host": "wood", "observed_normal_reference_points_xyz_mm": [[0., 0., 0.]]}],
        parameters={"synthetic": True}, material_scenario={"E": 123.})
    manifest = {"schema": "eoere_extended_cleat_mechanics_frozen_sources/v1", "parent_model_review_approved": True,
                "optional_2026_extra": False, "geometry": b.GEOMETRY}
    refs = {"report": b.GEOMETRY, "source_manifest": b.SOURCE_MANIFEST, "cached_source_export": export_ref}
    sources = {b.GEOMETRY["path"]: {}, b.SOURCE_MANIFEST["path"]: manifest, export_ref["path"]: exported}
    synthetic_pins = {**exported["source_sha256"], **{r["path"]: r["sha256"] for r in refs.values()}}
    data = {key: copy.deepcopy(exported[value]) for key, value in mappings.items()}
    data.update(schema=b.INPUT_SCHEMA, release=copy.deepcopy(b.core.RELEASE), optional_2026_extra=False, geometry=refs,
        source_sha256=synthetic_pins, parameters=exported["parameters"],
        scenario={**exported["material_scenario"], "fitting_stiffness_basis": "eoere-centroidal-four-half-strips-preserved-span-v1"},
        base_bodies=owners[:2], floor_footprints={"wood": [[0., 0., 0.]]}, panel_ids=["panel"],
        factory_holes=[{**h, "angle_id": "angle", "used": h["installed_bolt_axis_id"] is not None}
                       for h in exported["all_factory_holes"][0]["holes"]])
    with patch.object(b, "read_ref", lambda ref: copy.deepcopy(sources[ref["path"]])):
        b.require_current_sources(data)
        for key in [*mappings, "base_bodies", "floor_footprints", "panel_ids", "factory_holes", "parameters", "scenario"]:
            altered = copy.deepcopy(data)
            altered[key] = None if key != "scenario" else {"fitting_stiffness_basis": "foreign"}
            refused(lambda: b.require_current_sources(altered))
        altered = copy.deepcopy(data)
        altered["source_sha256"].pop("synthetic/dependency")
        refused(lambda: b.require_current_sources(altered))
    check_counts["synthetic_descriptor_join_positive"] = 1
    check_counts["synthetic_descriptor_join_rejections"] = len(mappings) + 7

    # Deferred builder API wiring only: stub load generation and validators;
    # current genuine cases, descriptors and panel dependencies are not built.
    roster = [{"case_id": name, "accessory_placement": "synthetic"} for name in b.driver.CASE_IDS]
    def derive(evidence, geometry, **kwargs):
        assert evidence == {"panel_machining": exported["current_panel_machining_descriptors"]}
        assert geometry["bodies"] == owners[:2]
        assert geometry["bolt_gravity_components"] == [{"id": "role/one", "owner": "shaft/one", "mass_kg": .5,
            "center_xyz_mm": [7., 8., 9.], "basis": "synthetic"}]
        assert kwargs["expected_owner_ids"] == [r["id"] for r in owners]
        return copy.deepcopy(roster), {"synthetic": True}
    bank = SimpleNamespace(source_inputs=lambda: {"geometry": b.GEOMETRY},
        verify_panel_source_inputs=lambda _data: {"source_sha256": {}})
    centroidal = SimpleNamespace(SCENARIO="eoere-centroidal-four-half-strips-preserved-span-v1",
        correction_contract=lambda: {"synthetic": True})
    def loading(path, _digest, _name):
        return bank if Path(path) == b.ROOT / b.PANEL_BANK["path"] else SimpleNamespace(derive_fresh_cases=derive)
    with patch.object(b, "read_ref", lambda ref: copy.deepcopy(sources[ref["path"]])), \
            patch.object(b, "source_pins", lambda extra=None, **_kwargs: copy.deepcopy(extra or {})), \
            patch.object(b, "load", loading), patch.object(b.driver, "load", return_value=centroidal), \
            patch.object(b.factory, "validate_rows", return_value={}), patch.object(b, "verify_selected_case") as selected:
        built = b.build_inputs(export_ref, b.SOURCE_MANIFEST, b.PANEL_BANK)
        assert selected.call_count == 6 and built["historical_q"] is None and built["old_field"] is None
        assert built["readiness"] == {"source_joins_independently_reviewed": False, "complete_reference_contact_inventory": False}
        assert built["case"] == roster[0] and built["cases"] == roster
        assert built["source_sha256"][b.PANEL_BANK["path"]] == b.PANEL_BANK["sha256"]
    check_counts["stubbed_builder_current_COM_mass_owners_and_six_selections"] = 1

    # Independent review must bind exact raw input and current selected view.
    data.update(cases=roster, case=roster[0])
    input_ref = {"path": "synthetic/current-input.json", "sha256": "i" * 64}
    review_ref = {"path": "synthetic/current-review.json", "sha256": "r" * 64}
    review = {"schema": b.REVIEW_SCHEMA, "success": b.REVIEW_SUCCESS, "complete_reference_contact_inventory": True,
        "geometry": b.GEOMETRY, "release": b.core.RELEASE, "input": input_ref,
        "source_sha256": {input_ref["path"]: input_ref["sha256"]}}
    sources.update({input_ref["path"]: data, review_ref["path"]: review})
    input_pins = {**synthetic_pins, input_ref["path"]: input_ref["sha256"]}
    with patch.object(b, "read_ref", lambda ref: copy.deepcopy(sources[ref["path"]])), \
            patch.object(b, "source_pins", lambda extra=None, **_kwargs: copy.deepcopy(extra or {})):
        for name in b.driver.CASE_IDS:
            view, selection = b.driver.select_case(data, name)
            _, checked = b.authenticate_review(review_ref, view, input_pins, raw_data=data, selection=selection)
            assert checked["source_case_selection"] == selection
            changed = copy.deepcopy(view)
            changed["case"]["foreign"] = True
            refused(lambda: b.authenticate_review(review_ref, changed, input_pins, raw_data=data, selection=selection))
        for key, value in (("geometry", {}), ("success", "old-success"), ("complete_reference_contact_inventory", False)):
            previous = review[key]
            review[key] = value
            refused(lambda: b.authenticate_review(review_ref, data, input_pins))
            review[key] = previous
    check_counts["current_review_selections"] = 6
    check_counts["current_review_rejections"] = 9

    # Source-bound consumer uses a synthetic issued receipt. Only read_method
    # and source-pin IO are stubbed; production pending/identity/hash/table and
    # exact loaded bridge-source checks execute unchanged.
    test_spec = importlib.util.spec_from_file_location("independent_bridge_pending_fixture", TARGET / "test_bridge.py")
    fixture = importlib.util.module_from_spec(test_spec)
    test_spec.loader.exec_module(fixture)
    field = fixture.fixture_field()
    field.update(state_id=b.STATE_PREFIX + "synthetic", case_id=b.driver.CASE_IDS[0], accessory_placement="synthetic",
        operator_bundle={"synthetic": True}, original_operator_fingerprint_sha256="synthetic",
        current_method_input={"path": "synthetic/method.json", "sha256": "m" * 64}, source_case_selection={"synthetic": True},
        current_panel_operator_preparation={"synthetic": True}, source_sha256={"synthetic/dep": "d" * 64})
    field.update({key: [] for key in b.base.TABLES})
    raw = json.dumps(field).encode()
    response = field["response"]
    receipt = {"schema": b.ADMISSION_SCHEMA, b.SUCCESS: True, "input_raw_sha256": hashlib.sha256(raw).hexdigest(),
        "input_canonical_sha256": b.canonical(field), "admission_source_sha256": b.LOADED_SHA,
        "source_path": b.bundle.artifact_path(b.OWN), "support_contract": b.law.contract(), "release": b.core.RELEASE,
        **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
        "q_canonical_sha256": response["q_canonical_sha256"], "gradient_canonical_sha256": response["gradient_canonical_sha256"],
        "declared_law_checks": {"full_signed_gradient_canonical_sha256": response["gradient_canonical_sha256"],
            "gradient_inf_n": response["gradient_inf_n"], "floor_force_and_declared_fixed_rear_leg_mask_replayed": True},
        "normal_force_n_by_host": response["fixed_floor_support_v1"]["normal_force_n_by_host"],
        "operator_bundle": field["operator_bundle"], "original_operator_fingerprint_sha256": field["original_operator_fingerprint_sha256"],
        "method_input": field["current_method_input"], "source_case_selection": field["source_case_selection"],
        "current_panel_operator_preparation_sha256": b.canonical(field["current_panel_operator_preparation"]),
        "table_canonical_sha256": {key: b.canonical(field[key]) for key in b.base.TABLES},
        "source_sha256": field["source_sha256"]}
    with patch.object(b, "read_method", return_value={}), \
            patch.object(b, "source_pins", lambda extra=None, **_kwargs: copy.deepcopy(extra or {})):
        admitted, _ = b.require_admitted_payload(raw, receipt, admission_sha256=b.LOADED_SHA)
        assert admitted == field
        refused(lambda: b.require_admitted_payload(raw + b"\n", receipt, admission_sha256=b.LOADED_SHA))
        refused(lambda: b.require_admitted_payload(raw, receipt, admission_sha256="old-gate"))
        mutations = {
            "action_table": lambda f: f["floor_actions"].append({"force": 1.}),
            "panel_chart": lambda f: f.update(panel_generalized_coefficients={"panel": {"coefficients": [1.]}}),
            "method": lambda f: f["current_method_input"].update(sha256="x" * 64),
            "operator": lambda f: f["operator_bundle"].update(synthetic=False),
            "panel_source_proof": lambda f: f["current_panel_operator_preparation"].update(synthetic=False),
            "case_selection": lambda f: f["source_case_selection"].update(synthetic=False),
            "signed_gradient": lambda f: f["response"].update(gradient_n=[-1e-5], gradient_canonical_sha256=b.canonical([-1e-5])),
            "q": lambda f: f["response"].update(q=[1.], q_canonical_sha256=b.canonical([1.])),
            "nested_identity": lambda f: f["floor_actions"].append({"case_id": "foreign"}),
            "source_closure": lambda f: f["source_sha256"].update({"synthetic/missing": "x" * 64}),
        }
        for mutation in mutations.values():
            changed, issued = copy.deepcopy(field), copy.deepcopy(receipt)
            mutation(changed)
            encoded = json.dumps(changed).encode()
            issued.update(input_raw_sha256=hashlib.sha256(encoded).hexdigest(), input_canonical_sha256=b.canonical(changed))
            refused(lambda: b.require_admitted_payload(encoded, issued, admission_sha256=b.LOADED_SHA))
    check_counts["synthetic_issued_consumer_positive"] = 1
    check_counts["synthetic_issued_consumer_rejections"] = len(mutations) + 2
    assert b.factory.SCHEMA == b.ORIGINAL_SCHEMA and b.factory.read_inputs is b.ORIGINAL_READ
    assert b.factory.authenticate_source_review is b.ORIGINAL_AUTHENTICATE

    # Rerun only the supplied 17 cheap source/stub/tiny-floor tests. All temp
    # outputs stay in this review's exclusive directory, without pytest cache.
    with tempfile.TemporaryDirectory(prefix="fixtures-", dir=OWN.parent) as temp:
        completed = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "--basetemp", str(Path(temp) / "pytest"), str(TARGET / "test_bridge.py")], cwd=ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, text=True, capture_output=True, check=True)
        assert "17 passed" in completed.stdout
    assert b.source_pins() == pins_before
    assert {name: sha(TARGET / name) for name in EXPECTED} == EXPECTED
    return {"schema": "eoere_current_force_bridge_independent_correctness_review/v1",
        "target_source_sha256": {str((TARGET / name).relative_to(ROOT)): digest for name, digest in EXPECTED.items()},
        "review_helper_sha256": sha(OWN), "findings": [], "supplied_tests_passed": 17,
        "supplied_tiny_floor_known_answer_and_negative_fixtures": 7,
        "independent_checks": check_counts, "source_closure_pins_rehashed": len(pins_before),
        "current_geometry": b.GEOMETRY, "source_manifest": b.SOURCE_MANIFEST, "panel_bank": b.PANEL_BANK,
        "limits": ["Source and synthetic fixtures only; builder validators/load generation and consumer source IO explicitly stubbed where stated.",
            "No genuine current descriptor extraction/input, panel K, global K, current load cases/q/actions, candidate solve or current field admission was executed.",
            "No CAD/BRep/native/browser/global install, hardware change, old force/capacity transfer or engineering/build/climbing acceptance.",
            "Actual descriptor export, independent current input review, current method/readiness evidence and parent serial slot remain missing/gated.",
            "Unverified fixed-floor no-slip assumption: all32 normal components unilateral Z; only two rear-leg XY supports credited.",
            "Receipt fixture tests consumption only; it is synthetic and is never an actual issued mechanical field or admission."],
        "production_readiness_claimed": False, "release": copy.deepcopy(b.core.RELEASE)}


if __name__ == "__main__":
    receipt = main()
    destination = OWN.with_name("receipt.json")
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"passed": True, "findings": receipt["findings"], "checks": receipt["independent_checks"],
        "receipt_sha256": sha(destination)}))
