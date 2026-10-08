"""One cold A12 original-floor case with all source-proved timber faces.

This wrapper replaces the six-pair preparation, preserves the frozen producer
and controller, and exports immutable operators for an independent same-q
original-gradient replay.  Preparation/review does not authorize execution.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import platform
import sys
from collections import Counter
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import scipy
from scipy.sparse import csr_matrix, vstack

from scripts import run_thin_bolted_linear_timber_frame as lean
from scripts import thin_bolted_numerical_step as numerical

frame, common, incremental = lean.frame, lean.common, lean.incremental
PACKET = Path(__file__).resolve().parent
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_SHA256 = frame.sha(Path(__file__))
ADAPTER_PATH = ROOT / "fea/generated/thin-bolted-complete-timber-contact-v1/adapter.py"
ADAPTER_SHA256 = "531d8e3393e309de172442b6a936c76b0d8db73f97a2bf63f831fa2a87d3b67f"
NUMERICAL_SHA256 = "82b7d5a8d9d9dc871ee6410fb4c5854093a998cfd9b331fdd986917b63ebbc28"
KNOWN_ORIGINAL_FIELDS = numerical.physical_fields
KNOWN_ORIGINAL_STAMP = lean.faces.stamp_recovered_actions
KNOWN_ELASTIC_ASSEMBLY = frame.ElasticAssembly
RECEIPT_SCHEMA = "thin_bolted_complete_timber_a12_method_inputs/v1"
OPERATOR_SCHEMA = "thin_bolted_complete_timber_original_operator_inputs/v1"


def load_leaf(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = load_leaf("complete_timber_adapter_for_a12", ADAPTER_PATH)
admission = load_leaf("complete_timber_admission_for_a12", PACKET / "admission.py")
canonical_sha = admission.canonical_sha
require = admission.require


def json_value(value):
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT))


def assert_original_source():
    require(frame.sha(Path(numerical.__file__)) == NUMERICAL_SHA256
            and KNOWN_ORIGINAL_FIELDS.__name__ == "physical_fields"
            and Path(KNOWN_ORIGINAL_FIELDS.__code__.co_filename).resolve() == Path(numerical.__file__).resolve(),
            "known original physical_fields source changed")


def method_sources():
    """Authenticate bytes only; never create a candidate or read a saved q."""
    require(frame.sha(Path(__file__)) == LOADED_SHA256, "loaded wrapper source changed")
    require(frame.sha(ADAPTER_PATH) == ADAPTER_SHA256, "frozen complete adapter changed")
    assert_original_source()
    _, adapter_pins = adapter.read_inputs()
    pins = lean.merge_pins(adapter_pins, admission.source_pins(), common.shafts.source_pins(),
        incremental.source_pins(), lean.PANEL_OPERATOR_PINS,
        {OWN: LOADED_SHA256, relative(PACKET / "test_runner.py"): frame.sha(PACKET / "test_runner.py"),
         relative(PACKET / "test_admission.py"): frame.sha(PACKET / "test_admission.py"),
         relative(ADAPTER_PATH.with_name("preparation.json")): frame.sha(ADAPTER_PATH.with_name("preparation.json")),
         relative(Path(lean.__file__)): lean.LOADED_DRIVER_SHA256,
         relative(Path(lean.reused.__file__)): lean.REUSED_DRIVER_SHA256,
         relative(Path(lean.saved_panels.__file__)): lean.SAVED_PANEL_HELPER_SHA256,
         relative(lean.reused.CERTIFICATE): lean.reused.CERTIFICATE_SHA})
    certificate = json.loads(lean.reused.CERTIFICATE.read_bytes())
    pins = lean.merge_pins(pins, certificate["source_sha256"])
    admission.linear.verify_pins(pins)
    return pins


def freeze_method_inputs(path, *, reviewed_checks):
    """Parent-owned explicit freeze after reviews; no case preparation/launch."""
    pins = method_sources()
    require(reviewed_checks["focused_fixtures_pass"] is True
            and reviewed_checks["independent_readiness_review_pass"] is True
            and reviewed_checks["runner_sha256"] == LOADED_SHA256
            and reviewed_checks["admission_sha256"] == admission.LOADED_PRODUCER_SHA256,
            "parent-supplied passing focused checks and independent review required before freeze")
    receipt = {"schema": RECEIPT_SCHEMA, "source_sha256": pins,
        "driver": {"path": OWN, "sha256": LOADED_SHA256},
        "complete_face_basis": adapter.BASIS, "complete_face_scenario": adapter.SCENARIO,
        "expected_census": {"timber": 20, "fittings": 36, "panels": 6, "shafts": 70,
            "bodies": 132, "dofs": 8018, "timber_pairs": 30, "timber_cells": 584,
            "compression_contacts": 1402, "normal_contacts": 1574},
        "fixed_options": {"cases": ["a12-rear"], "wood_bedding": 1., "intervals": 8,
            "contact_edge": 70., "newton_limit": 300, "wall_seconds": 600.},
        "controller": "frozen-lean-common-shaft-incremental-original-cold",
        "method_checks_pass": True, "reviewed_checks": copy.deepcopy(reviewed_checks),
        "original_physical_fields_source_sha256": NUMERICAL_SHA256,
        "historical_q_force_or_acceptance_transferred": False,
        "floor_datum_or_constitutive_law_changed": False,
        "execution_authorization_supplied_by_receipt": False,
        "tool_versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "release": copy.deepcopy(frame.RELEASE)}
    with Path(path).open("x") as stream:
        stream.write(common.finished.writer.dump(receipt))
    return receipt


def read_method_inputs(path, expected_sha):
    require(frame.sha(path) == expected_sha, "parent-frozen method-input bytes differ")
    receipt = json.loads(Path(path).read_bytes())
    require(receipt["schema"] == RECEIPT_SCHEMA and receipt["source_sha256"] == method_sources()
            and receipt["driver"] == {"path": OWN, "sha256": LOADED_SHA256}
            and receipt["complete_face_basis"] == adapter.BASIS and receipt["method_checks_pass"] is True
            and receipt["tool_versions"] == {"python": platform.python_version(),
                "numpy": np.__version__, "scipy": scipy.__version__}
            and not any(receipt["release"].values()), "parent-frozen method inputs differ")
    return receipt


def parse_options(arguments):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--method-input", type=Path, required=True)
    parser.add_argument("--method-input-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cases", nargs="+", default=["a12-rear"])
    parser.add_argument("--wall-seconds", type=float, default=600.)
    parser.add_argument("--newton-limit", type=int, default=300)
    parser.add_argument("--wood-bedding", type=float, default=1.)
    parser.add_argument("--intervals", type=int, default=8)
    parser.add_argument("--contact-edge", type=float, default=70.)
    selected = parser.parse_args(arguments)
    require(selected.cases == ["a12-rear"] and selected.wall_seconds == 600.
            and selected.newton_limit == 300 and selected.wood_bedding == 1.
            and selected.intervals == 8 and selected.contact_edge == 70.,
            "one unchanged cold A12 case with the frozen bounded options required")
    require(selected.out.resolve().parent == PACKET and selected.method_input.resolve().parent == PACKET,
            "case and method input must use the exclusive ignored packet")
    return selected


def put_csr(arrays, prefix, matrix):
    value = csr_matrix(matrix, copy=True)
    require(np.isfinite(value.data).all(), "finite original sparse operator required")
    arrays.update({prefix + "_data": value.data.copy(), prefix + "_indices": value.indices.copy(),
        prefix + "_indptr": value.indptr.copy(), prefix + "_shape": np.asarray(value.shape, dtype=np.int64)})
    return {"prefix": prefix, "shape": list(value.shape)}


def csr_digest(matrix):
    arrays = {}
    put_csr(arrays, "m", matrix)
    return canonical_sha({key: value.tolist() for key, value in arrays.items()})


def write_arrays(path, arrays):
    with Path(path).open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    return {"path": relative(path), "sha256": frame.sha(path)}


def write_json(path, value):
    with Path(path).open("x") as stream:
        stream.write(common.finished.writer.dump(json_value(value)))
    return {"path": relative(path), "sha256": frame.sha(path)}


def capture_operators(K, applied, groups, contacts, tangents, *, directory, pins, command, receipt):
    """Save the actual existing material/port operators, before response."""
    arrays = {"applied": np.asarray(applied, dtype=float).copy(),
              "ck": np.asarray([row["stiffness"] for row in contacts], dtype=float)}
    ndof = K.shape[0]
    require(K.shape == (ndof, ndof) and arrays["applied"].shape == (ndof,), "operator dimensions differ")
    metadata = {"schema": OPERATOR_SCHEMA, "ndof": ndof, "command": command,
        "source_sha256": pins, "method_input": receipt,
        "material_K": put_csr(arrays, "K", K), "applied": {"key": "applied"},
        "C": put_csr(arrays, "C", vstack([row["B"] for row in contacts], format="csr")),
        "ck": {"key": "ck"}, "groups": [], "contacts": [], "tangents": [],
        "controller": "frozen-lean-common-shaft-incremental-original-cold",
        "historical_q_initialization": False, "warm_initialization": None,
        "material_K_includes_floor_tangents_or_damping": False,
        "retained_source_CSR_order": True, "no_operator_numeric_or_sparsity_normalization": True}
    for category, rows in (("groups", groups), ("contacts", contacts), ("tangents", tangents)):
        for index, row in enumerate(rows):
            record = json_value({key: value for key, value in row.items() if key != "B"})
            if category != "contacts":
                record["B"] = put_csr(arrays, category + "_B_" + f"{index:04d}", row["B"])
            metadata[category].append(record)
    metadata["array_bundle"] = write_arrays(directory / "operators.npz", arrays)
    record = write_json(directory / "operator-inputs.json", metadata)
    return metadata, arrays, record


def verify_complete_census(K, groups, contacts, tangents):
    kinds = Counter(row["kind"] for row in contacts)
    group_kinds = Counter(row["kind"] for row in groups)
    require(K.shape == (8018, 8018) and len(contacts) == 1574
            and kinds["timber_face_contact"] == 584 and kinds["floor_normal"] == 32
            and kinds["shaft_end_capture"] == 140
            and sum(kinds.values()) - kinds["floor_normal"] - kinds["shaft_end_capture"] == 1402
            and len(tangents) == 16 and len({row["first"] for row in tangents}) == 8
            and len({row["id"] for row in contacts}) == 1574
            and len(groups) == 374 and group_kinds == {"common_shaft_bearing": 308, "panel_screw": 66},
            "complete current operator census differs")


def immutable_operator_signature(K, applied, groups, contacts, tangents):
    return canonical_sha({"material": csr_digest(K), "applied": np.asarray(applied).tolist(),
        "groups": [{"metadata": json_value({k: v for k, v in row.items() if k != "B"}),
                    "B": csr_digest(row["B"])} for row in groups],
        "contacts": [{"metadata": json_value({k: v for k, v in row.items() if k != "B"}),
                      "B": csr_digest(row["B"])} for row in contacts],
        "tangents": [{"metadata": json_value({k: v for k, v in row.items() if k != "B"}),
                      "B": csr_digest(row["B"])} for row in tangents]})


def stamp_complete_once(report, prepared, q):
    # Adapter.linear and lean.faces are the same module. Restore only the
    # inner frozen function while the complete adapter calls it once.
    with patch.object(lean.faces, "stamp_recovered_actions", KNOWN_ORIGINAL_STAMP):
        return adapter.stamp_complete_recovered_actions(report, prepared, q)


def prepare_complete_once(assembly, *, bedding_n_mm3):
    # The common driver temporarily replaces frame.ElasticAssembly with its
    # constructor wrapper. Authenticate the existing original instance and
    # restore the class symbol only for the adapter's exact-class check.
    require(type(assembly) is KNOWN_ELASTIC_ASSEMBLY, "existing frozen ElasticAssembly instance required")
    with patch.object(frame, "ElasticAssembly", KNOWN_ELASTIC_ASSEMBLY):
        return adapter.prepare_complete_timber_faces(assembly, bedding_n_mm3=bedding_n_mm3)


def add_complete_metadata(report, prepared, *, command, pins, method_record, operator_record,
                          operator_manifest, wall_seconds):
    """Bind new physics/actual outer invocation before finished state identity."""
    require(report["counts"]["dofs"] == 8018 and report["counts"]["structural_bodies"] == 132,
            "current complete field dimensions differ")
    report["parameters"].update(prepared["metadata"]["parameters"])
    report["parameters"].update({"complete_timber_a12_driver_sha256": LOADED_SHA256,
        "complete_timber_a12_method_input_sha256": method_record["sha256"],
        "complete_timber_original_operator_input_sha256": operator_record["sha256"],
        "complete_timber_original_operator_bundle_sha256": operator_manifest["array_bundle"]["sha256"]})
    report["counts"].update({"paired_timber_interfaces": 30, "paired_timber_compression_cells": 584,
                             "compression_contacts": 1402, "normal_contacts": 1574})
    report["linear_timber_face_method"] = adapter.BASIS
    report["complete_timber_face_contact_metadata"] = copy.deepcopy(prepared["metadata"])
    report["complete_timber_face_contact_physical_signature_sha256"] = prepared["metadata"]["parameters"][
        "complete_timber_face_contact_physical_signature_sha256"]
    report["linear_timber_coordinate_map"] = copy.deepcopy(prepared["coordinate_map"])
    report["source_sha256"] = lean.merge_pins(report["source_sha256"], pins,
        {r["path"]: r["sha256"] for r in (method_record, operator_record, operator_manifest["array_bundle"])})
    report["complete_timber_original_operator_inputs"] = {**operator_record,
        "array_bundle": operator_manifest["array_bundle"]}
    report["complete_timber_a12_execution"] = {"command": command, "one_case_only": True,
        "automatic_retries": 0, "wall_time_limit_seconds": wall_seconds,
        "loaded_driver_sha256": LOADED_SHA256, "loaded_admission_sha256": admission.LOADED_PRODUCER_SHA256,
        "loaded_adapter_sha256": ADAPTER_SHA256, "nested_lean_execution_is_a_reused_internal_call": True,
        "environment": {"OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS")},
        "controller": "frozen-lean-common-shaft-incremental-original-cold", "warm_initialization": None,
        "method_input": method_record, "operator_inputs": report["complete_timber_original_operator_inputs"],
        "all_30_patches_used_once": True, "only_added_physics": "24 source-proved timber compression interfaces",
        "original_floor_datum_and_law_preserved": True, "new_constitutive_law": False,
        "native_or_CAD_execution": False, "old_q_force_or_acceptance_transfer": False}
    report["complete_contact_admission_pending"] = True
    report["complete_joint_acceptance"] = False
    report["complete_joint_capacity_established"] = False
    report["compatible_numerical_mvp_complete"] = False
    require(not any(report["release"].values()), "release flag changed")
    old_limit = "All six paired timber faces use reference-cell linear ports"
    report["limits"] = [row for row in report["limits"] if not row.startswith(old_limit)]
    report["limits"].append("All thirty source-proved timber faces use friction-free first-order compression ports with unchanged declared bedding1. Independent complete-field admission, motion applicability, real washer/contact restraint and complete-joint resistance remain required.")
    return report


def final_gradient_capture(report, context):
    """Fresh known-source original fields plus independent read-only replay."""
    response = report["response"]
    q_kind = "q" if "q" in response else "diagnostic_last_q"
    if response.get(q_kind) is None:
        response["original_gradient_replay_unavailable"] = "no current or diagnostic vector observed"
        return
    require("last_linear" in context and context["operator_manifest"], "observed original branch unavailable")
    assert_original_source()
    q = np.asarray(response[q_kind], dtype=float)
    material, applied, groups, contacts, tangents = context["inputs"]
    C = vstack([row["B"] for row in contacts], format="csr")
    ck = np.asarray([row["stiffness"] for row in contacts])
    linear = context["last_linear"].copy()
    enabled = lean.reused.enabled_floor_hosts(linear, material, tangents)
    fields = KNOWN_ORIGINAL_FIELDS(linear, applied, groups, C, ck, q, tangent=False)
    gradient, energy = fields[:2]
    arrays = {"q": q.copy(), "gradient": np.asarray(gradient).copy()}
    callback = context.get("last_callback")
    if callback:
        arrays.update(last_callback_q=callback["q"], last_callback_gradient=callback["gradient"])
    descriptor = put_csr(arrays, "final_K", linear)
    bundle = write_arrays(context["directory"] / "final-branch-operators.npz", arrays)
    capture = {"schema": "thin_bolted_complete_timber_original_closed_branch_capture/v1",
        "q_kind": q_kind, "diagnostic_only": q_kind != "q", "final_q_canonical_sha256": canonical_sha(q.tolist()),
        "original_physical_fields_path": relative(Path(numerical.__file__)),
        "original_physical_fields_source_sha256": NUMERICAL_SHA256,
        "fresh_known_original_function_called": True, "full_signed_gradient_n": gradient.tolist(),
        "gradient_canonical_sha256": canonical_sha(gradient.tolist()),
        "gradient_inf_n": float(abs(gradient).max()), "potential_energy_nmm": float(energy),
        "observed_enabled_centroid_xy_hosts": enabled, "observed_linear_K": descriptor,
        "observed_linear_K_canonical_sha256": csr_digest(linear), "array_bundle": bundle,
        "pre_response_operator_inputs": context["operator_record"],
        "pre_response_array_bundle": context["operator_manifest"]["array_bundle"],
        "source_sha256": context["pins"], "controller_claimed_gradient_inf_n": response.get("gradient_inf_n"),
        "last_successful_callback_q_canonical_sha256": context.get("last_q_sha256"),
        "last_successful_callback_gradient_canonical_sha256": context.get("last_gradient_sha256"),
        "last_successful_callback": None if callback is None else {
            "q_array_key": "last_callback_q", "gradient_array_key": "last_callback_gradient",
            "q_canonical_sha256": context["last_q_sha256"],
            "gradient_canonical_sha256": context["last_gradient_sha256"],
            "gradient_inf_n": float(abs(callback["gradient"]).max()),
            "potential_energy_nmm": callback["energy"],
            "observed_linear_K_canonical_sha256": csr_digest(context["last_linear"]),
            "q_equals_final_q": context["last_q_sha256"] == canonical_sha(q.tolist())},
        "physical_laws_changed": False, "current_action_admission_or_capacity_established": False}
    capture_record = write_json(context["directory"] / "final-branch-inputs.json", capture)
    require(numerical.physical_fields is KNOWN_ORIGINAL_FIELDS, "independent replay seam is still patched")
    replay = admission.replay_original_gradient(report, context["operator_manifest"], context["operator_arrays"],
        observed_enabled_hosts=enabled, observed_linear_K=linear)
    observed = replay["observed_branch"]
    require(replay["final_q_canonical_sha256"] == capture["final_q_canonical_sha256"]
            and observed["gradient_canonical_sha256"] == capture["gradient_canonical_sha256"]
            and observed["gradient_inf_n"] == capture["gradient_inf_n"]
            and observed["potential_energy_nmm"] == capture["potential_energy_nmm"],
            "fresh original capture and independent replay differ")
    replay.update({"original_closed_branch_capture": capture_record,
        "operator_inputs": context["operator_record"],
        "operator_array_bundle": context["operator_manifest"]["array_bundle"],
        "replay_helper_sha256": admission.LOADED_PRODUCER_SHA256})
    response["original_closed_branch_capture_v1"] = {**capture_record, "array_bundle": bundle,
        "final_q_canonical_sha256": capture["final_q_canonical_sha256"],
        "gradient_canonical_sha256": capture["gradient_canonical_sha256"]}
    response["original_gradient_replay_v1"] = replay
    report["source_sha256"] = lean.merge_pins(report["source_sha256"],
        {r["path"]: r["sha256"] for r in (bundle, capture_record)})
    report["complete_timber_a12_execution"]["final_original_closed_branch_capture"] = capture_record
    assert_original_source()


def run_case(options, arguments, receipt):
    """Reuse nested frozen orchestration; all mutations are restored."""
    directory = options.out.resolve().parent
    command = [sys.executable, str(Path(__file__).resolve()), *arguments]
    pins = receipt["source_sha256"]
    method_record = {"path": relative(options.method_input), "sha256": options.method_input_sha256}
    context = {"pins": pins, "directory": directory, "prepared": {}, "operator_manifest": None}
    original_solve = incremental.compatible_contact_solve
    original_metadata = common.bind_common_metadata
    original_finished = common.finished.bind_finished_state

    def prepare(assembly, proof_path, expected_sha, *, bedding_n_mm3):
        require(not context["prepared"] and proof_path == lean.PROOF and expected_sha == lean.PROOF_SHA256,
                "one replacement of the authenticated six-pair preparation required")
        require(bedding_n_mm3 == 1., "unchanged bedding1 required")
        result = prepare_complete_once(assembly, bedding_n_mm3=bedding_n_mm3)
        context["prepared"] = result
        return result

    def observe(linear, applied, groups, C, ck, q, *, tangent=False):
        if "inputs" in context:
            _, saved_applied, saved_groups, saved_contacts, _ = context["inputs"]
            require(groups is saved_groups and np.array_equal(applied, saved_applied),
                    "original callback input identity differs")
            if C is not context.get("observed_C") or ck is not context.get("observed_ck"):
                require(csr_digest(C) == csr_digest(vstack([r["B"] for r in saved_contacts], format="csr"))
                        and np.array_equal(ck, [r["stiffness"] for r in saved_contacts]),
                        "original callback normal operator/order differs")
                context.update(observed_C=C, observed_ck=ck)
        fields = KNOWN_ORIGINAL_FIELDS(linear, applied, groups, C, ck, q, tangent=tangent)
        # Store a branch only after a successful unmodified function return.
        context["last_linear"] = linear
        context["last_q_sha256"] = canonical_sha(np.asarray(q).tolist())
        context["last_gradient_sha256"] = canonical_sha(np.asarray(fields[0]).tolist())
        context["last_callback"] = {"q": np.asarray(q).copy(), "gradient": np.asarray(fields[0]).copy(),
                                    "energy": float(fields[1])}
        return fields

    def solve(K, applied, groups, contacts, tangents, max_iterations=500, *, warm_q=None):
        require(context["operator_manifest"] is None and warm_q is None and max_iterations == 300,
                "one cold original initialization at the frozen Newton limit required")
        verify_complete_census(K, groups, contacts, tangents)
        admission.linear.verify_pins(pins)
        context["inputs"] = (K, applied, groups, contacts, tangents)
        manifest, arrays, record = capture_operators(K, applied, groups, contacts, tangents,
            directory=directory, pins=pins, command=command, receipt=method_record)
        context.update(operator_manifest=manifest, operator_arrays=arrays, operator_record=record,
                       original_operator_signature=immutable_operator_signature(K, applied, groups, contacts, tangents))
        return original_solve(K, applied, groups, contacts, tangents, max_iterations=max_iterations, warm_q=None)

    def metadata(report, system, supplied_pins, _internal_command):
        return original_metadata(report, system, supplied_pins, command)

    def finish(report, proof, supplied_pins, driver_sha):
        require(context["prepared"] and context["operator_manifest"], "full new preparation/capture required")
        require(immutable_operator_signature(*context["inputs"]) == context["original_operator_signature"],
                "pre-response material/port/load operators mutated")
        admission.linear.verify_pins(pins)
        add_complete_metadata(report, context["prepared"], command=command, pins=pins,
            method_record=method_record, operator_record=context["operator_record"],
            operator_manifest=context["operator_manifest"], wall_seconds=options.wall_seconds)
        final_gradient_capture(report, context)
        admission.linear.verify_pins(report["source_sha256"])
        return original_finished(report, proof, supplied_pins, driver_sha)

    def interruption(path, _command, prepared, panels, last):
        sidecar = path.with_name(path.name + ".interrupted.json")
        payload = {"schema": "thin_bolted_complete_timber_a12_interrupted/v1", "command": command,
            "source_sha256": pins, "method_input": method_record, "phase": last.get("phase"),
            "response": lean.failed_wall_response(last), "accepted_field_exported": False,
            "usable_conditional_actions": False, "complete_contact_admission_pending": True,
            "complete_joint_acceptance": False, "release": copy.deepcopy(frame.RELEASE),
            "operator_inputs": context.get("operator_record"), "preparation_complete": bool(prepared),
            "saved_panel_preparation_complete": bool(panels)}
        write_json(sidecar, payload)
        return sidecar

    old_argv = sys.argv.copy()
    try:
        sys.argv = [str(Path(__file__)), "--cases", "a12-rear", "--out", str(options.out),
            "--wall-seconds", "600", "--newton-limit", "300", "--wood-bedding", "1",
            "--intervals", "8", "--contact-edge", "70"]
        with (patch.object(lean.faces, "prepare_linear_timber_faces", prepare),
              patch.object(lean.faces, "stamp_recovered_actions", stamp_complete_once),
              patch.object(incremental, "compatible_contact_solve", solve),
              patch.object(incremental, "ORIGINAL_FIELDS", observe),
              patch.object(common, "bind_common_metadata", metadata),
              patch.object(common.finished, "bind_finished_state", finish),
              patch.object(lean, "write_interruption", interruption)):
            lean.main()
    finally:
        sys.argv = old_argv
        admission.linear.verify_pins(pins)


def main():
    arguments = sys.argv[1:]
    options = parse_options(arguments)
    receipt = read_method_inputs(options.method_input, options.method_input_sha256)
    expected = {"cases": options.cases, "wood_bedding": options.wood_bedding,
        "intervals": options.intervals, "contact_edge": options.contact_edge,
        "newton_limit": options.newton_limit, "wall_seconds": options.wall_seconds}
    require(receipt["fixed_options"] == expected, "actual invocation differs from parent-frozen options")
    require(os.environ.get("OPENBLAS_NUM_THREADS") == "1", "serialized case requires OPENBLAS_NUM_THREADS=1")
    for path in (options.out, options.out.with_name(options.out.name + ".interrupted.json"),
                 PACKET / "operator-inputs.json", PACKET / "operators.npz",
                 PACKET / "final-branch-inputs.json", PACKET / "final-branch-operators.npz"):
        require(not path.exists(), "preserve existing output: " + str(path))
    run_case(options, arguments, receipt)


if __name__ == "__main__":
    main()
