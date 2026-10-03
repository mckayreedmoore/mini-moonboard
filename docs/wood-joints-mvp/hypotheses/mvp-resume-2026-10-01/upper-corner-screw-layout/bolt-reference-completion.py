"""Prepare N01 and N10 from authenticated, saved fresh-gravity bolt actions.

Import is inert. build(output) defaults to recover(output): only the two
recovery-attempt01 numerical nulls, using a bounded convex initial pose and
preserving all accepted output rows exactly. Explicit full/n01 modes retain
the original reference APIs. No historical producer, frame, native solver,
CAD, test or review entry point is called.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import math
import os
import sys
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from types import CodeType, FunctionType

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = HERE.parents[4]
HYPOTHESES = PACKET.parent
RAW = HERE / "rawlocal/bolt-reference-completion"
SAVED = HERE / "rawlocal/knee-bridge-other-bolts/attempt01"
EXTRACTOR = HERE / "knee-bridge-other-bolts.py"
SHAFT = HERE / "upper-right-combined-transfer.py"
TRACTION = HERE / "cleat-traction.py"
REFERENCE_LOADER = HERE / "knee-bridge-corner-references.py"
HARDWARE = PACKET / "assembly-package/hardware_engagement.py"
HARDWARE_AXES = HARDWARE.parent / "rawlocal/hardware-axes.csv"
FEATURES = HYPOTHESES / "current-finished-feature-register-2026-10-01/surfaces.json"
FEATURE_METHOD = FEATURES.with_name("surfaces.py")
GEOMETRY_METHOD = ROOT / "mini_moonboard/wood_joint_geometry.py"
CONTACT = HYPOTHESES / "mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json"
N01_PRODUCER_SNAPSHOT = RAW / "n01-attempt02/producer.py.snapshot"
FULL01 = RAW / "full-attempt01"
FULL01_RECEIPT_SHA = "54125505dce1a499e964ef6b708f3148de7eac934e50f0c00e3bda28fd3ca274"
FULL01_PRODUCER_SHA = "f5a881203dcd21a446fb05c9e99aa997f7590542b59d55d0bcb5f929bb692d49"
RECOVERY_BASE = RAW / "recovery-attempt01"
RECOVERY_RECEIPT_SHA = "bd46885849c203001d4e520a0601f16cf1be950da4d3cab44045da2cf8630173"
RECOVERY_PRODUCER_SHA = "509af84792f319b04883bebc9dbb9b1a78804129b1bfda7e48bd3e532b28b0f0"
CONIC_METHOD = HERE / "conic_frame.py"
CONIC_ORACLE = HERE / "rawlocal/load-lever/frame-attempt01/conic-seeding.json"
RECOVERY_METHOD_PINS = {
    CONIC_METHOD: "445574a04559e8faa28a3b69bfdbf1a439f6fc25940e0f02837b0927c48f0025",
    CONIC_ORACLE: "4f04814e435742108b4cb6aa80562ea2fb7faca1bb27d94f082b2e0a94576ea7",
    RAW / "preparation-five-recovery/documentation.md.snapshot": "b69d725999c22265dfeb3467d045ae403088fa2e6a0d426e22677fafd1d6c017",
}
RECOVERY_STATES = frozenset({
    ("a12-left", "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_rail_1"),
    ("k12-right", "bottom_center/clip_horizontal_bottom_left_2/rail_2"),
})
STEEL = ROOT / "mini_moonboard/wood_joint_bolt_resistance.py"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
CEG, FYB_PSI, PSI_MPA, KWOOD = 0.67, 92000.0, 0.006894757293168, 20.0
GEOMETRY_PRECISION_MM, RECORDED_SPAN_MISMATCH_BOUND_MM = 1e-6, 2.295365e-7
PRECISION_AXES = frozenset({
    *(f"left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_{level}_left_{station}/{level}_rail_{rail}"
      for level in ("lower", "upper") for station in (1, 2) for rail in (1, 2)),
    *(f"wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/{level}_rail_{rail}"
      for level in ("lower", "upper") for rail in (1, 2)),
    *(f"wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/{level}_rail_{rail}"
      for level in ("lower", "upper") for rail in (1, 2)),
})
PINS = {
    EXTRACTOR: "7a03ecabeb89fd0415877152842fea3e7a80cfef4be6ebea3b52e602dce2585d",
    SAVED / "receipt.json": "ee67b7e042a8fcf88d1c37eaaaaac8aebcb815e2cf73b8f1a22a61f44283da83",
    REFERENCE_LOADER: "188b7626d989eb16fb09ee75b8218dd9968974c95c72830dcd83c33f856c4b83",
    SHAFT: "fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0",
    TRACTION: "2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764",
    HERE / "corner-first-order.py": "6e3f899ac99d6eef629ac12570b6ea31ea5c3914467c1c7399b7bcdd8d320563",
    HERE / "central-seat-transfer.py": "b0ad536b3fad418dad1c07b56edd126ae78bace32eb8ecb150ba756880f7d7fa",
    PACKET / "end_grain_route.py": "5b9faca5696d6c7add02e9ac6d5056363896bb2a7badb7ab7bb3fa8bfc9fe5d4",
    HARDWARE: "d8e2a08e46fd9507a89d8e7ecb238ddf229490f4909345cbb641374ee8133295",
    HARDWARE_AXES: "2fb010f1b55757e614d90940bfa2a8400df6ee41ab0f950ffa56d30157150b01",
    FEATURES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    FEATURE_METHOD: "a58e8f76b0d308352c734b6eab6bdea8c3adb75ab1c538e0905997d0232bab4f",
    GEOMETRY_METHOD: "e437385d4894c7bcd4bbf4ee66aa9f96a53a8d3570efc6230fb225570abbb90e",
    CONTACT: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    # Historical producer identity is authenticated at its immutable snapshot,
    # never by changing the old receipt's pin to this maintained producer.
    N01_PRODUCER_SNAPSHOT: "a007b59e423985e598ddf350b870420dcd5733dc551519ca04e21f02ded5dd45",
    STEEL: "488e58bbd58fbc2f22af5d4122e734732bae09de79dad71bbf2623eeca60b166",
    ROOT / "pyproject.toml": "84e007ad5c9cfffa853f21627fecbaec0a85c602560d5d5e0b507326e9b02452",
    ROOT / "uv.lock": "5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3",
}
FLAGS = {
    "proposal_adopted": False,
    "formal_criteria_updated": False,
    "historical_acceptance_transferred": False,
    "actual_changed_hole_stiffness_qualified": False,
    "hardware_capacity_qualified": False,
    "common_host_compatibility_established": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
    "native_or_CAD_or_frame_run": False,
    "tests_or_review_run": False,
}
ARTIFACTS = frozenset({
    "end-grain.jsonl", "steel.jsonl", "shaft-fields.jsonl", "summary.json",
    "sources.json", "producer.py.snapshot", "receipt.json", "washer-ends.jsonl",
    "recovery-trace.json", "reuse-manifest.json", "seed-known-answer.json",
})


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


class UnsupportedGeometry(ValueError):
    """An authenticated geometry lies outside the existing shaft model."""


def geometry_require(condition, message):
    if not condition:
        raise UnsupportedGeometry(message)


def digest(source_path):
    with source_path.open("rb") as source_stream:
        return hashlib.file_digest(source_stream, "sha256").hexdigest()


def load_module(source_path, name):
    require(digest(source_path) == PINS[source_path], "helper changed: " + str(source_path))
    spec = importlib.util.spec_from_file_location(name, source_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def imports():
    """Prevent foreign bytecode writes and restore the caller's import settings."""
    saved_path, saved_bytecode = list(sys.path), sys.dont_write_bytecode
    sys.path[:0] = [str(ROOT), str(PACKET)]
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        sys.path[:] = saved_path
        sys.dont_write_bytecode = saved_bytecode


def write_owned(output, name, payload):
    """Exclusive creation at a fixed owned directory descriptor; never replace."""
    require(name in ARTIFACTS and output.parent == RAW and output.resolve() == output,
            "write destination is outside the owned fresh child")
    directory = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o644, dir_fd=directory)
        options = {} if isinstance(payload, bytes) else {"encoding": "utf-8"}
        with os.fdopen(descriptor, "wb" if isinstance(payload, bytes) else "w", **options) as owned_stream:
            owned_stream.write(payload)
    finally:
        os.close(directory)


def serialize(value):
    return json.dumps(value, sort_keys=True, allow_nan=False) + "\n"


def source_closure(api, mode):
    """Reuse the saved extraction receipt and its original source/output bindings."""
    selected_sources = set(PINS) if mode == "full" else {
        EXTRACTOR, SAVED / "receipt.json", REFERENCE_LOADER, PACKET / "end_grain_route.py",
        ROOT / "pyproject.toml", ROOT / "uv.lock",
    }
    pins = {**{source_path: expected for source_path, expected in PINS.items() if source_path in selected_sources},
            Path(__file__).resolve(): digest(Path(__file__).resolve())}
    api.authenticate(pins)
    receipt = api.read(SAVED / "receipt.json")
    require(receipt["producer_sha256"] == PINS[EXTRACTOR]
            and receipt["sources_authenticated_before_and_after"] is True
            and receipt["census"]["owned_physical_axes"] == 84
            and receipt["census"]["axis_states"] == 504, "saved extraction contract differs")
    for source_name, expected in receipt["source_sha256"].items():
        api.bind(pins, ROOT / source_name, expected)
    for artifact_name, expected in receipt["output_sha256"].items():
        artifact_path = SAVED / artifact_name
        require(artifact_path.resolve().parent == SAVED, "saved artifact escapes its packet")
        api.bind(pins, artifact_path, expected)
    for source_path, expected in api.PINS.items():
        api.bind(pins, source_path, expected)
    api.authenticate(pins)
    inputs = api.read(api.GEOMETRY)
    for source_name, expected in inputs["source_sha256"].items():
        api.bind(pins, ROOT / source_name, expected)
    retained = None
    if mode == "full":
        retained = api.read(api.RETAINED)
        for source_name, binding in retained["source_pins"].items():
            api.bind(pins, ROOT / source_name, binding["sha256"])
        # Saved geometric bindings only: hashing STEP bytes does not run CAD.
        for member in api.read(FEATURES)["records"]:
            binding = member["step_binding"]
            api.bind(pins, ROOT / binding["path"], binding["file_sha256"])
    api.authenticate(pins)
    return pins, inputs, retained


def reference_status(value):
    return "NULL_UNSUPPORTED" if value is None else "EXCEEDANCE" if value > 1.0 else "SUPPORTED_COMPARISON"


def saved_span_evidence(record, bolt, retained):
    """Keep original intervals and receiver identities even outside applicability."""
    if record["kind"] == "candidate_bolt":
        receivers = [{"receiver_member": row["receiver_id"],
                      "intervals_mm": row["current_shaft_intersection_solid_intervals_from_underhead_mm"]}
                     for row in bolt["source_record"]["geometry"]["wood_receiver_intervals"]]
        datum = "saved candidate underhead axis datum"
    else:
        receivers = [{"receiver_member": row["member"], "intervals_mm": [row["interval_from_axis_datum_mm"]]}
                     for row in retained["axis_register"][record["axis_id"]]["finished_receivers"]]
        datum = "saved retained axis datum"
    require(len(receivers) == 2 and {row["receiver_member"] for row in receivers} == set(record["receivers"]),
            "saved physical receiver identity differs")
    order = gap = None
    if all(len(row["intervals_mm"]) == 1 for row in receivers):
        receivers.sort(key=lambda row: row["intervals_mm"][0][0])
        order = [row["receiver_member"] for row in receivers]
        gap = receivers[1]["intervals_mm"][0][0] - receivers[0]["intervals_mm"][0][1]
    return {"saved_receivers": record["receivers"], "physical_receivers_head_to_nut": order,
            "interval_datum": datum, "receiver_intervals": receivers,
            "signed_endpoint_gap_mm": gap, "contiguity_abs_tol_mm": 1e-7, "contiguity_rel_tol": 1e-9}


def end_grain_bearing_join(record, bolt):
    """Only the existing Ceg route's two-member, zero-gap bearing hypothesis."""
    geometry = bolt["source_record"]["geometry"]
    require(record["kind"] == "candidate_bolt"
            and math.isclose(geometry["modeled_shaft_diameter_mm"], 6.35, abs_tol=1e-8)
            and math.isclose(record["modeled_full_body_diameter_in"], .25, abs_tol=1e-8),
            "Ceg quarter-inch bearing hypothesis differs")
    evidence = saved_span_evidence(record, bolt, None)
    require(all(len(row["intervals_mm"]) == 1 for row in evidence["receiver_intervals"])
            and evidence["signed_endpoint_gap_mm"] is not None
            and abs(evidence["signed_endpoint_gap_mm"]) < 1e-7, "Ceg two-member zero-gap hypothesis differs")
    for row in evidence["receiver_intervals"]:
        length = row["intervals_mm"][0][1] - row["intervals_mm"][0][0]
        require(length > 0 and math.isclose(length, record["bearing_lengths_mm"][record["receivers"].index(row["receiver_member"])],
                                            abs_tol=1e-7), "Ceg saved bearing length differs")


def geometry_precision_proof(api, inputs, feature_records):
    """Read pinned tolerance declarations and saved faces; import no CAD code."""
    assignments = {node.targets[0].id: node.value for node in ast.parse(GEOMETRY_METHOD.read_text()).body
                   if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
    require(ast.literal_eval(assignments["_GEOMETRY_TOLERANCE_MM"]) == GEOMETRY_PRECISION_MM,
            "pinned geometry precision declaration differs")
    contact = api.read(CONTACT)
    require(contact["tolerances"]["contact_geometry_tolerance_mm"] == 1e-5
            and len(PRECISION_AXES) == 16, "pinned contact precision / matched axis census differs")
    return {"interfaces": inputs["candidate_bolt_adjacent_interfaces"],
            "contact_patches": contact["contact_patches"],
            "finished_faces": {(member["member_id"], feature["face_index_one_based"]):
                               (member["step_binding"], feature)
                               for member in feature_records for feature in member["features"]}}


def normalize_precision_spans(record, bolt, spans, direction, axis_datum, proof, unit, dot):
    """Normalize only the 16 authenticated, matched numerical discrepancies."""
    if record["axis_id"] not in PRECISION_AXES:
        return spans, None
    geometry_require(record["kind"] == "candidate_bolt" and len(spans) == 2,
                     "precision normalization requires the recorded two-receiver candidate")
    gap = spans[1][1][0] - spans[0][1][1]
    geometry_require(abs(gap) <= GEOMETRY_PRECISION_MM
                     and abs(gap) <= RECORDED_SPAN_MISMATCH_BOUND_MM,
                     "gap exceeds the pinned precision or recorded 16-axis mismatch bound")
    order = [body for body, interval in spans]
    matches = [row for row in proof["interfaces"] if row["axis_id"] == record["axis_id"]
               and row["adjacent_receivers_head_to_nut"] == order]
    geometry_require(len(matches) == 1, "precision normalization lacks a unique saved adjacent interface")
    interface = matches[0]
    point = record["point_xyz_mm"]
    require(point == interface["axis_point_xyz_mm"], "saved source plane differs from the authenticated common interface")
    source_station = dot([actual - datum for actual, datum in zip(point, axis_datum, strict=True)], direction)
    projected = [datum + source_station * value for datum, value in zip(axis_datum, direction, strict=True)]
    midpoint_station = (spans[0][1][1] + spans[1][1][0]) / 2
    midpoint = [datum + midpoint_station * value for datum, value in zip(axis_datum, direction, strict=True)]
    geometry_require(math.dist(projected, point) <= GEOMETRY_PRECISION_MM
                     and math.dist(midpoint, point) <= GEOMETRY_PRECISION_MM,
                     "saved common source plane is outside the numerical normalization bound")
    contact_matches = [patch for patch in proof["contact_patches"] if set(patch["member_ids"]) == set(order)
                       and any(saved["member_ids"] == patch["member_ids"] and saved["patch_index"] == patch["patch_index"]
                               for saved in interface["matching_finished_contact_planes"])]
    geometry_require(len(contact_matches) == 1, "precision normalization lacks one authenticated finished contact patch")
    patch = contact_matches[0]
    contact_distance = abs(dot([actual - centroid for actual, centroid in zip(point, patch["centroid_xyz_mm"], strict=True)],
                               unit(patch["normal_on_first_xyz"])))
    geometry_require(contact_distance <= GEOMETRY_PRECISION_MM
                     and abs(dot(direction, unit(patch["normal_on_first_xyz"]))) > 1 - 1e-8,
                     "saved source/contact plane coincidence exceeds the numerical bound")
    face_proof = []
    for member, face_index in zip(patch["member_ids"], patch["source_face_indices"], strict=True):
        binding, face = proof["finished_faces"][member, face_index]
        geometry_require(face["surface_kind"] == "PLANE", "matched finished contact face is not planar")
        plane = face["plane"]
        distance = abs(dot(point, plane["normal_global_xyz"]) - plane["signed_plane_station_global_mm"])
        geometry_require(distance <= GEOMETRY_PRECISION_MM
                         and abs(dot(direction, unit(plane["normal_global_xyz"]))) > 1 - 1e-8,
                         "individual finished contact face exceeds the numerical source-plane bound")
        face_proof.append({"member_id": member, "feature_id": face["feature_id"],
                           "face_index_one_based": face_index, "step_binding": binding,
                           "source_plane_distance_mm": distance})
    cylinders = {row["receiver_id"]: row["coaxial_cylindrical_finished_faces"]
                 for row in bolt["receiver_clearance_geometry"]}
    geometry_require(all(len(cylinders[body]) == 1 for body in order), "precision normalization lacks unique finished bore end faces")
    bore_gap = (cylinders[order[1]][0]["range_along_source_bolt_axis_from_shaft_center_mm"][0]
                - cylinders[order[0]][0]["range_along_source_bolt_axis_from_shaft_center_mm"][1])
    geometry_require(abs(bore_gap) <= GEOMETRY_PRECISION_MM,
                     "finished bore endpoint mismatch exceeds pinned geometry precision")
    normalized = [(body, list(interval)) for body, interval in spans]
    normalized[0][1][1] = normalized[1][1][0] = source_station
    corrections = [{"receiver_member": body,
                    "endpoint_corrections_mm": [new - old for new, old in zip(new_interval, old_interval, strict=True)],
                    "bearing_length_correction_mm": (new_interval[1] - new_interval[0]) - (old_interval[1] - old_interval[0])}
                   for (body, old_interval), (_body, new_interval) in zip(spans, normalized, strict=True)]
    correction_max = max(abs(value) for row in corrections for value in row["endpoint_corrections_mm"])
    geometry_require(correction_max <= GEOMETRY_PRECISION_MM,
                     "endpoint normalization correction exceeds pinned geometry precision")
    return normalized, {
        "status": "NORMALIZED_MATCHED_NUMERICAL_PRECISION", "original_ordered_spans_mm": spans,
        "normalized_ordered_spans_mm": normalized, "endpoint_corrections": corrections,
        "original_signed_endpoint_gap_mm": gap, "recorded_span_mismatch_bound_mm": RECORDED_SPAN_MISMATCH_BOUND_MM,
        "geometry_precision_mm": GEOMETRY_PRECISION_MM, "maximum_endpoint_correction_mm": correction_max,
        "source_interface_point_global_xyz_mm": point, "source_station_from_axis_datum_mm": source_station,
        "projected_source_point_global_xyz_mm": projected, "source_projection_error_mm": math.dist(projected, point),
        "source_to_original_midpoint_error_mm": math.dist(midpoint, point),
        "finished_contact_plane_distance_mm": contact_distance,
        "finished_contact_patch": {"member_ids": patch["member_ids"], "patch_index": patch["patch_index"],
                                    "source_face_indices": patch["source_face_indices"]},
        "individual_finished_face_proof": face_proof, "finished_bore_endpoint_gap_mm": bore_gap,
        "geometry_tolerance_source_sha256": PINS[GEOMETRY_METHOD], "finished_face_method_sha256": PINS[FEATURE_METHOD],
        "finished_face_register_sha256": PINS[FEATURES], "contact_geometry_sha256": PINS[CONTACT],
        "normalization_limit": "Only the 16 frozen matches; no free-gap or multi-span extension and no physical inspection claim",
    }


def geometry_for(record, bolt, retained, features, catalog, unit, dot, api, pins, proof, evidence):
    """Parameterize the retained two-host shaft, without querying geometry."""
    if record["kind"] == "candidate_bolt":
        geometry = bolt["source_record"]["geometry"]
        direction = unit(geometry["axis_head_to_nut_global"])
        spans = []
        for receiver in geometry["wood_receiver_intervals"]:
            intervals = receiver["current_shaft_intersection_solid_intervals_from_underhead_mm"]
            geometry_require(len(intervals) == 1, "multi-span receiver outside two-host method")
            spans.append((receiver["receiver_id"], list(intervals[0])))
        clearances = bolt["receiver_clearance_geometry"]
        geometry_require(len(clearances) == 2 and all(row["result_status"] == "unique_coaxial_bore_radius"
                                                    for row in clearances), "ambiguous saved bore geometry")
        require({row["receiver_id"] for row in clearances} == set(record["receivers"]),
                "clearance receiver identity differs")
        radii = [row["unique_bore_radius_mm"] for row in clearances]
        for row in clearances:
            api.bind(pins, ROOT / row["receiver_step_path"], row["receiver_step_sha256"])
        diameter = geometry["modeled_shaft_diameter_mm"]
        axis_datum = [coordinate - direction[index] * geometry["modeled_shaft_occupied_length_mm"] / 2
                      for index, coordinate in enumerate(geometry["shaft_center_global_xyz_mm"])]
    else:
        geometry = retained["axis_register"][record["axis_id"]]
        direction = unit(bolt["source_record"]["axis_global_xyz"])
        spans = [(row["member"], list(row["interval_from_axis_datum_mm"]))
                 for row in geometry["finished_receivers"]]
        cylinders = [features[row["feature_id"]]["cylinder"] for row in geometry["finished_receivers"]]
        geometry_require(all(row["material_side_geometry"] == "bore_like"
                             and abs(dot(unit(row["axis_unit_global_xyz"]), direction)) > 1 - 1e-8
                             for row in cylinders), "retained feature is not a coaxial bore")
        radii = [row["radius_mm"] for row in cylinders]
        diameter = geometry["hardware_policy"]["nominal_diameter_in"] * 25.4
        axis_datum = bolt["source_record"]["origin_global_xyz_mm"]
    spans.sort(key=lambda item: item[1][0])
    order = [item[0] for item in spans]
    require(len(order) == 2 and set(order) == set(record["receivers"]), "physical receiver mapping differs")
    geometry_require(all(interval[1] > interval[0] for body, interval in spans),
                     "nonpositive original physical bearing span")
    for body, interval in spans:
        require(math.isclose(interval[1] - interval[0], record["bearing_lengths_mm"][record["receivers"].index(body)], abs_tol=1e-7),
                "original physical grip differs from extracted bearing length")
    spans, normalization = normalize_precision_spans(record, bolt, spans, direction, axis_datum, proof, unit, dot)
    evidence["numerical_precision_normalization"] = normalization
    lengths = [item[1][1] - item[1][0] for item in spans]
    geometry_require(min(lengths) > 0 and math.isclose(spans[0][1][1], spans[1][1][0], abs_tol=1e-7),
                     "two contiguous physical bearing spans required; "
                     + json.dumps({"ordered_spans_mm": spans,
                                   "signed_endpoint_gap_mm": spans[1][1][0] - spans[0][1][1]}))
    geometry_require(math.isclose(radii[0], radii[1], abs_tol=1e-7) and 2 * radii[0] > diameter,
                     "unequal or non-clearance bores are outside the retained helper")
    require(math.isclose(diameter, 25.4 * record["modeled_full_body_diameter_in"], abs_tol=1e-7),
            "shaft diameter differs from saved extraction")
    interface_point = [coordinate + direction[index] * spans[0][1][1]
                       for index, coordinate in enumerate(axis_datum)]
    geometry_require(all(math.isclose(actual, saved, abs_tol=1e-7) for actual, saved in
                         zip(interface_point, record["point_xyz_mm"], strict=True)),
                     "source lateral plane is not the physical two-host interface; an imposed couple would be needed")
    for body, length in zip(order, lengths, strict=True):
        correction = next(row["bearing_length_correction_mm"] for row in normalization["endpoint_corrections"]
                          if row["receiver_member"] == body) if normalization else 0.0
        require(math.isclose(length, record["bearing_lengths_mm"][record["receivers"].index(body)] + correction, abs_tol=1e-7),
                "normalized physical grip differs from traced extracted bearing length")
    washer, nut = catalog["washer"], catalog["nut"]
    quarter = math.isclose(diameter, 6.35, abs_tol=1e-7)
    flat_radius = 5.0 if quarter else nut["across_flats_mm"][0] / 2
    # The central route credits only its documented 5-mm supported patch at
    # both ends. This is a restricted contact hypothesis, not a full washer seat.
    partial = record["axis_id"] == "center_principal_right_2"
    family = {
        "host_length_mm": lengths[0], "cleat_length_mm": lengths[1],
        "diameter_mm": diameter, "bore_mm": 2 * radii[0],
        "washer_ID_max_mm": washer["inside_diameter_mm"][1],
        "washer_OD_min_mm": 10.0 if partial else washer["outside_diameter_mm"][0],
        "flat_radius_mm": flat_radius,
    }
    geometry_require(family["washer_ID_max_mm"] / 2 < flat_radius <= family["washer_OD_min_mm"] / 2,
                     "empty or incompatible hypothetical end-contact ring")
    return family, order, direction, partial


def fresh_records(api, pins, inputs, np, mode):
    all_records = [json.loads(line) for line in (SAVED / "records.jsonl").read_text().splitlines()]
    summary = api.read(SAVED / "summary.json")
    axes = set(summary["owned_axis_ids"])
    identities = {(row["case_id"], row["axis_id"]) for row in all_records}
    require(len(axes) == 84 and len(all_records) == len(identities) == 504
            and identities == {(case, axis) for case in CASES for axis in axes}, "504-state census differs")
    require(Counter(row["kind"] for row in all_records) == {"candidate_bolt": 432, "retained_bolt": 72},
            "72 candidate / 12 retained census differs")
    require([row["case_id"] for row in all_records] == [case for case in CASES for _ in range(84)],
            "saved case block order differs")
    records = all_records if mode == "full" else [row for row in all_records
                                                 if row["lateral_reference_status"] == "END_GRAIN_METHOD_SEPARATE"]
    require(mode == "full" or len(records) == 72, "N01 saved record census differs")
    source_indices = {(row["case_id"], row["axis_id"]): index for index, row in enumerate(all_records)}
    prototypes = {row["axis_id"]: row for row in records if row["case_id"] == CASES[0]}
    geometry_keys = ("kind", "receivers", "point_xyz_mm", "component_rows", "component_directions_xyz",
                     "tie_row", "tie_first_body", "tie_second_body", "tie_direction_xyz", "grain_axes_xyz",
                     "bearing_lengths_mm", "modeled_full_body_diameter_in", "lateral_reference_status")
    require(all(all(row[key] == prototypes[row["axis_id"]][key] for key in geometry_keys) for row in records),
            "same-axis geometric/source joins differ across cases")
    comparison = api.read(api.FRAME / "comparison.json")
    assessment = api.read(api.GRAVITY / "operator-assessment.json")
    require(comparison["response_sha256"] == pins[api.FRAME / "response.npz"]
            and comparison["source_sha256"][api.key(api.GRAVITY / "operator-assessment.json")]
            == pins[api.GRAVITY / "operator-assessment.json"], "mixed gravity/response binding")
    require(comparison["comparison_climber_weight_lb"] == 250.0
            and comparison["comparison_horizontal_force_n"] == 300.0
            and comparison["climber_load_scale"] == comparison["horizontal_load_scale"] == 1.0
            and assessment["case_ids"] == list(CASES) and assessment["operator_ready"] is True,
            "fixed load envelope differs")
    require(summary["source_comparison_sha256"] == pins[api.FRAME / "comparison.json"]
            and comparison["modeled_mass_kg"] == summary["fresh_modeled_mass_kg"] == assessment["modeled_mass_kg"]
            and comparison["dead_load_factor"] == summary["dead_load_factor"] == assessment["dead_load_factor"],
            "fresh extraction mass/gravity binding differs")
    bolts = {row["axis_id"]: row for row in inputs["connections"]
             if row["kind"] in ("candidate_bolt", "retained_bolt")}
    require(len(bolts) == 104 and axes.issubset(bolts), "104-source geometry differs")
    rows = api.read(api.GRAVITY / "row-identities.json")
    with np.load(api.FRAME / "response.npz", allow_pickle=False) as response:
        for record in records:
            require(record["gap_scale"] == 1.0 and record["joint_accepted"] is False,
                    "nominal-gap extraction scope differs")
            force = response[record["case_id"] + "_gap_raw_force_n"]
            require(force.shape == (1888,) and np.isfinite(force).all(), "invalid saved force vector")
            indices = record["component_rows"]
            directions = np.asarray(record["component_directions_xyz"], dtype=float)
            scalars = force[indices]
            require(scalars.tolist() == record["components_n"]
                    and float(force[record["tie_row"]]) == record["signed_axial_n"] >= 0,
                    "saved T/V extraction differs from exact response rows")
            vector = scalars @ directions
            require(np.allclose(vector, record["force_on_first_body_xyz_n"], atol=1e-8, rtol=0)
                    and np.allclose(-vector, record["force_on_second_body_xyz_n"], atol=1e-8, rtol=0)
                    and math.isclose(float(np.linalg.norm(vector)), record["same_plane_lateral_n"], abs_tol=1e-8),
                    "signed lateral reconstruction differs")
            for component, index in enumerate(indices):
                ownership = rows[index]["ownership"]
                require(ownership["first_body"] == record["receivers"][0]
                        and ownership["second_body"] == record["receivers"][1]
                        and ownership["direction_global_xyz"] == record["component_directions_xyz"][component],
                        "lateral row ownership differs")
            tie = rows[record["tie_row"]]["ownership"]
            require(tie["first_body"] == record["tie_first_body"]
                    and tie["second_body"] == record["tie_second_body"]
                    and tie["direction_global_xyz"] == record["tie_direction_xyz"], "axial row ownership differs")
    return records, bolts, comparison, source_indices


def component_summary(records, component):
    finite = [row for row in records if row[component] is not None]
    require(all(math.isfinite(row[component]) and row[component] >= 0 for row in finite), "invalid comparison index")
    peak = max(finite, key=lambda row: row[component]) if finite else None
    return {
        "finite_states": len(finite), "null_states": len(records) - len(finite),
        "maximum": peak[component] if peak else None,
        "peak_witness": {key: peak[key] for key in ("case_id", "axis_id")} if peak else None,
        "exceedances": [{"case_id": row["case_id"], "axis_id": row["axis_id"], "index": row[component]}
                        for row in finite if row[component] > 1.0],
        "null_reasons": [{"case_id": row["case_id"], "axis_id": row["axis_id"], "reason": row["shaft_null_reason"]}
                         for row in records if row[component] is None],
    }


def washer_end_source(record, state, family, order, direction, partial, catalog,
                      end_index, source_join, helper, traction, np, null_reason, geometry_evidence):
    """Recover one existing end's pressure wrenches; never solve another state."""
    role = "nut" if end_index else "head"
    compression = record["signed_axial_n"]
    end_sign = -1 if end_index else 1
    axis = np.asarray(direction, dtype=float)
    interface = np.asarray(record["point_xyz_mm"], dtype=float)
    datum = None
    if family is not None:
        length = family["host_length_mm"] + family["cleat_length_mm"]
        datum = interface + (end_index * length - family["host_length_mm"]) * axis
    receiver = order[end_index] if order is not None else None
    entry = {
        "schema": "ordinary_washer_own_end_source/v1", "obligation": "N09_SOURCE_ONLY",
        "scope": "outside_corner_axial_reference", "case_id": record["case_id"],
        "gap_scale": record["gap_scale"], "axis_id": record["axis_id"],
        "end_role": role, "receiver_member": receiver,
        "join_key": [record["case_id"], record["axis_id"], role, receiver],
        "fresh_signed_T_n": compression, "signed_T_n": None,
        "signed_T_definition": "force on the receiver projected on the head-to-nut shaft axis; head positive, nut negative",
        "normal_compression_T_n": None, "force_on_receiver_xyz_n": None,
        "own_end_M_magnitude_nmm": None, "own_end_M_signed_xyz_nmm": None,
        "own_end_M_signed_transverse_pair_nmm": None,
        "physical_transverse_basis_columns_xyz": None,
        "end_wrench_datum_global_xyz_mm": datum.tolist() if datum is not None else None,
        "common_interface_datum_global_xyz_mm": interface.tolist(),
        "shaft_axis_head_to_nut_xyz": direction,
        "normal_into_receiver_xyz": (end_sign * axis).tolist(),
        "source_join": source_join,
        "geometry_applicability": geometry_evidence,
        "contact_hypotheses": {
            "first_order": True, "rigid_washer": True, "preload_n": 0,
            "Kwood_mpa_per_mm": KWOOD, "Khead_mpa_per_mm": 10000.0,
            "concentric_annuli": True, "offset_includes_beam_end_translation": False,
            "partial_supported_ring_route": partial, "actual_support_mask_qualified": False,
            "wood_contact_inner_outer_radii_mm": [family["washer_ID_max_mm"] / 2, family["washer_OD_min_mm"] / 2],
            "head_nut_contact_inner_outer_radii_mm": [family["washer_ID_max_mm"] / 2, family["flat_radius_mm"]],
            "zero_T_rule": "Retained compression() returns inactive zero-pressure contacts at T=0 regardless of stored tilt",
            "bore_diameter_mm": family["bore_mm"], "shaft_diameter_mm": family["diameter_mm"],
            "ordered_bearing_lengths_mm": [family["host_length_mm"], family["cleat_length_mm"]],
            "catalog_washer_envelope": catalog["washer"], "catalog_nut_envelope": catalog["nut"],
            "catalog_source_sha256": PINS[HARDWARE],
            "land_limit": "Hypothetical circular head/nut land; a catalog hex width does not establish its delivered bearing profile",
        } if family is not None else None,
        "local_end_moment_status": "UNKNOWN_NOT_SET_TO_ZERO",
        "status": "NULL_UNSUPPORTED", "null_reason": null_reason,
        "pressure_recovery": None, "N09_complete": False, **FLAGS,
    }
    if state is None:
        return entry
    try:
        drive = np.asarray(state["drive_unit_xyz"], dtype=float)
        rotation = np.asarray(state["rotation_axis_xyz"], dtype=float)
        basis = np.column_stack((drive, rotation))
        require(np.allclose(basis.T @ basis, np.eye(2), atol=1e-8, rtol=0)
                and np.allclose(np.cross(axis, drive), rotation, atol=1e-8, rtol=0),
                "end source lacks a physical orthonormal transverse basis")
        contacts = [state["end_head"], state["end_nut"]]
        contact = contacts[end_index]
        moment = float(contact["moment_nmm"])
        require(math.isfinite(moment), "nonfinite saved end moment")
        moment_world = moment * rotation
        force_world = end_sign * compression * axis
        entry.update({
            "signed_T_n": end_sign * compression, "normal_compression_T_n": compression,
            "force_on_receiver_xyz_n": force_world.tolist(),
            "own_end_M_magnitude_nmm": abs(moment), "own_end_M_signed_xyz_nmm": moment_world.tolist(),
            "own_end_M_signed_transverse_pair_nmm": (basis.T @ moment_world).tolist(),
            "physical_transverse_basis_columns_xyz": basis.tolist(),
            "moment_on_beam_xyz_nmm": (-moment_world).tolist(), "saved_end_contact": contact,
            "local_end_moment_status": "SIGNED_SAME_STATE_SHAFT_END_PRESSURE_RECOVERY_PENDING",
        })
        # The retained two-plane recovery takes a nonnegative pressure tilt
        # and carries its direction in the slope vector. The scalar shaft
        # stores signed tilt directly. This adapter changes representation only.
        adapted_contacts = []
        for saved_contact in contacts:
            adapted_contacts.append({**saved_contact,
                                     "wood_contact": {**saved_contact["wood_contact"],
                                                      "tilt_rad": abs(saved_contact["wood_contact"]["tilt_rad"]) if compression else 0.0},
                                     "moment_on_beam_xyz_nmm": (-saved_contact["moment_nmm"] * rotation).tolist()})
        adapter = {
            "axis_id": record["axis_id"], "interface_point_xyz_mm": interface.tolist(),
            "compatible_T_n": compression, "end_contacts": adapted_contacts,
            "end_slope_vectors_rad": [[saved_contact["relative_tilt_rad"], 0.0] for saved_contact in contacts],
            "end_moment_vectors_in_transverse_basis_nmm": [[saved_contact["moment_nmm"], 0.0] for saved_contact in contacts],
        }
        _wood_actions, wood = traction.wood_seat(helper, adapter, end_index, family, axis, basis, KWOOD)
        hardware_adapter = {**adapter, "end_contacts": [
            {**adapted, "wood_contact": {**saved["head_contact"],
                                        "tilt_rad": abs(saved["head_contact"]["tilt_rad"]) if compression else 0.0}}
            for adapted, saved in zip(adapted_contacts, contacts, strict=True)]}
        hardware_ring = {**family, "washer_OD_min_mm": 2 * family["flat_radius_mm"]}
        _hardware_actions, hardware = traction.wood_seat(helper, hardware_adapter, end_index,
                                                         hardware_ring, axis, basis, helper.K_HEAD)
        wood_wrench = np.asarray(wood["recovered_force_and_own_pressure_moment_at_seat_n_nmm"])
        hardware_wrench = np.asarray(hardware["recovered_force_and_own_pressure_moment_at_seat_n_nmm"])
        expected = np.r_[force_world, moment_world]
        residual = hardware_wrench - wood_wrench
        require(np.max(abs(wood_wrench[:3] - expected[:3])) <= 1e-7
                and np.max(abs(wood_wrench[3:] - expected[3:])) <= 1e-6
                and np.max(abs(residual[:3])) <= 1e-7 and np.max(abs(residual[3:])) <= 1e-6,
                "independent end pressure wrenches do not recover the signed same-state T/M")
        require(np.allclose(wood["nominal_outer_wood_seat_xyz_mm"], datum, atol=1e-7, rtol=0),
                "pressure recovery uses another end datum")
        entry.update({
            "status": "COMPLETE_ISOLATED_END_SOURCE", "null_reason": None,
            "local_end_moment_status": "SIGNED_SAME_STATE_SHAFT_END_WITH_INDEPENDENT_PRESSURE_RECOVERY",
            "pressure_recovery": {
                "method": "cleat-traction.py:wood_seat, saved closure/tilt, 8 Gauss radii x 32 azimuths per annulus; no contact solve",
                "method_sha256": PINS[TRACTION], "wood_annulus": wood, "hardware_annulus": hardware,
                "quadrature_points_per_annulus": 256,
                "wrench_definition": "Fxyz in N, physical Mxyz in Nmm about the named nominal seat; axes are world XYZ",
                "wood_pressure_wrench_at_seat_n_nmm": wood_wrench.tolist(),
                "hardware_pressure_wrench_on_washer_at_seat_n_nmm": hardware_wrench.tolist(),
                "wood_reaction_wrench_on_washer_at_seat_n_nmm": (-wood_wrench).tolist(),
                "washer_force_moment_balance_residual_n_nmm": residual.tolist(),
                "wood_wrench_minus_source_T_M_n_nmm": (wood_wrench - expected).tolist(),
                "wood_pressure_wrench_at_common_interface_n_nmm": traction.shifted(wood_wrench, datum, interface).tolist(),
            },
        })
    except (KeyError, TypeError, ValueError, ArithmeticError, np.linalg.LinAlgError) as error:
        entry["null_reason"] = str(error)
    return entry


def build(output, *, mode="recover"):
    """Parent API: two-null recovery by default; explicit historical full/n01."""
    if mode == "recover":
        return recover(output)
    require(mode in ("full", "n01"), "mode must be full or n01")
    output = Path(output).absolute()
    require(RAW.resolve() == RAW and output.resolve() == output
            and output.parent == RAW and not output.exists(), "fresh immediate owned RAW child required")
    with imports():
        api = load_module(EXTRACTOR, "bolt_completion_saved_extraction")
        pins, inputs, retained = source_closure(api, mode)
        import numpy as np

        require(np.__version__ == "2.5.2", "pinned NumPy arithmetic runtime differs")
        scipy = None
        if mode == "full":
            import scipy

            require(scipy.__version__ == "1.18.1", "pinned SciPy arithmetic runtime differs")
        references = load_module(REFERENCE_LOADER, "bolt_completion_reference_loader")
        lateral_path = PACKET / "lateral_reference.py"
        require(digest(lateral_path) == pins[lateral_path], "lateral helper changed")
        lateral = api.pure_module(lateral_path, "bolt_completion_lateral")
        require(Path(sys.modules["fea.dowel_yield"].__file__).resolve() == ROOT / "fea/dowel_yield.py",
                "wrong dowel helper import")
        steel = hardware = retained_method = None
        family_ids, features = {}, {}
        normalization_proof = None
        if mode == "full":
            steel = load_module(STEEL, "bolt_completion_steel")
            hardware = load_module(HARDWARE, "bolt_completion_catalog")
            for source_name, expected in hardware.PINS.items():
                api.bind(pins, ROOT / source_name, expected)
            retained_method = references.pure_functions(api.RETAINED_METHOD, ["steel_references"],
                                                        {"math": math, "PSI_TO_MPA": PSI_MPA})
            with HARDWARE_AXES.open(newline="", encoding="utf-8") as source_stream:
                family_ids = {row["axis_id"]: row["family_id"] for row in csv.DictReader(source_stream)}
            feature_records = api.read(FEATURES)["records"]
            features = {feature["feature_id"]: feature for member in feature_records
                        for feature in member["features"]}
            normalization_proof = geometry_precision_proof(api, inputs, feature_records)
        unit, dot = references.unit, references.dot
        records, bolts, comparison, source_indices = fresh_records(api, pins, inputs, np, mode)
        members = {member["member_id"]: member["reduced_geometry_descriptor"] for member in inputs["members"]
                   if member["member_kind"] != "panel"}
        model = api.read(api.GRAVITY / "model.json")
        fasteners = api.read(api.FASTENERS)
        require(1000 * fasteners["material_boundaries"]["sae_j429_grade5_1_4_through_1_in"]["machine_test_yield_ksi_min"]
                == FYB_PSI, "nominal material hypothesis differs")
        if mode == "full":
            require(fasteners["dimension_inputs"]["nut"]["tensile_stress_area_in2"] == 0.0318,
                    "nominal thread-area hypothesis differs")
        end_axes = {}
        families, geometry_evidence, geometry_issues = {}, {}, {}
        force_rows = api.read(api.GRAVITY / "row-identities.json")
        for record in (row for row in records if row["case_id"] == CASES[0]):
            bolt = bolts[record["axis_id"]]
            direction = unit(bolt["axis_xyz"])
            parallel = [body for body, grain in zip(record["receivers"], record["grain_axes_xyz"], strict=True)
                        if abs(dot(direction, unit(grain))) > 1 - 1e-8]
            if parallel:
                require(len(parallel) == 1 and "base_header" in record["receivers"]
                        and record["lateral_reference_status"] == "END_GRAIN_METHOD_SEPARATE",
                        "end-grain applicability census differs")
                end_axes[record["axis_id"]] = parallel[0]
                end_grain_bearing_join(record, bolt)
            if mode == "n01":
                continue
            catalog = hardware.STACKS[hardware.ROUTES[family_ids[record["axis_id"]]][0]]
            evidence = saved_span_evidence(record, bolt, retained)
            try:
                family_data = geometry_for(record, bolt, retained, features, catalog, unit, dot, api, pins,
                                           normalization_proof, evidence)
                tie = force_rows[record["tie_row"]]["ownership"]
                lever = np.asarray(tie["point_mm"]) - np.asarray(record["point_xyz_mm"])
                geometry_require(float(np.linalg.norm(np.cross(lever, family_data[2]))) < 1e-5,
                                 "eccentric axial tie would require an unsupported imposed shaft couple")
                families[record["axis_id"]] = family_data
            except UnsupportedGeometry as error:
                geometry_issues[record["axis_id"]] = str(error)
                shaft_direction = unit(bolt["source_record"]["geometry"]["axis_head_to_nut_global"]
                                       if record["kind"] == "candidate_bolt" else bolt["source_record"]["axis_global_xyz"])
                families[record["axis_id"]] = (None, evidence["physical_receivers_head_to_nut"], shaft_direction,
                                                record["axis_id"] == "center_principal_right_2")
            geometry_evidence[record["axis_id"]] = {**evidence,
                "status": "NULL_UNSUPPORTED" if record["axis_id"] in geometry_issues else "APPLICABLE_TWO_HOST_HYPOTHESIS",
                "reason": geometry_issues.get(record["axis_id"])}
        require(len(families) == (84 if mode == "full" else 0)
                and len(end_axes) == 12 and len(set(end_axes.values())) == 6,
                "mode-specific shaft / 12 end-grain / six block census differs")
        normalizations = {axis: evidence["numerical_precision_normalization"] for axis, evidence in geometry_evidence.items()
                          if evidence.get("numerical_precision_normalization") is not None}
        require(mode != "full" or PRECISION_AXES.issubset(families), "recorded normalization axis census differs")
        for body in set(end_axes.values()) | {"base_header"}:
            grain = unit(members[body]["axis"])
            modeled = unit(model["material_binding"]["orientation_overrides"][body]["material_axes_global_xyz"]["L"])
            require(abs(dot(grain, modeled)) > 1 - 1e-8, "end-grain material orientation differs")
        api.authenticate(pins)
        require(all(not source_path.is_relative_to(output) for source_path in pins), "output contains a consumed source")
        output.mkdir(parents=True, exist_ok=False)
        end_rows, steel_rows, field_rows, washer_rows = [], [], [], []
        shaft_calls = 0
        helper = traction = None
        if mode == "full":
            helper = load_module(SHAFT, "bolt_completion_shaft")
            original_beam_model = helper.beam_model

            def first_order_beam(family, tension):
                elastic, geometric, samples, curvatures, inertia = original_beam_model(family, tension)
                return elastic, np.zeros_like(geometric), samples, curvatures, inertia

            helper.beam_model = first_order_beam
            traction = references.pure_functions(TRACTION, ["action", "wrench", "wood_seat", "shifted"],
                                                 {"np": np, "require": require})
        try:
            for record in records:
                source_index = source_indices[(record["case_id"], record["axis_id"])]
                identity = {key: record[key] for key in ("case_id", "axis_id", "gap_scale", "kind")}
                if record["axis_id"] in end_axes:
                    main = end_axes[record["axis_id"]]
                    force = record["force_on_first_body_xyz_n"] if record["receivers"][0] == main else record["force_on_second_body_xyz_n"]
                    lengths = [record["bearing_lengths_mm"][record["receivers"].index(body)] for body in (main, "base_header")]
                    header_angle = lateral.angle(force, unit(members["base_header"]["axis"]))
                    require(abs(dot(unit(bolts[record["axis_id"]]["axis_xyz"]), unit(members[main]["axis"]))) > 1 - 1e-8,
                            "end-grain main axis changed")
                    reference = lateral.reference(lengths, [90.0, header_angle], FYB_PSI)
                    base = reference["reference_lateral_lbf"] * lateral.N_PER_LBF
                    adjusted = CEG * base
                    index = record["same_plane_lateral_n"] / adjusted
                    end_rows.append({**identity, "obligation": "N01", "main_member": main, "side_member": "base_header",
                                     "source_record_index": source_index,
                                     "signed_force_on_main_xyz_n": force, "signed_axial_n": record["signed_axial_n"],
                                     "same_plane_lateral_n": record["same_plane_lateral_n"],
                                     "main_side_bearing_lengths_mm": lengths, "main_side_load_grain_angles_deg": [90.0, header_angle],
                                     "main_Fe_psi": 4450.0, "side_Fe_theta_psi": lateral.bearing(header_angle),
                                     "Ceg": CEG, "base_reference_n": base, "Ceg_reference_n": adjusted,
                                     "governing_mode": reference["governing_mode"], "mode_references_lbf": reference["reference_values_lbf"],
                                     "Ceg_mode_references_n": {mode: CEG * value * lateral.N_PER_LBF
                                                               for mode, value in reference["reference_values_lbf"].items()},
                                     "Ceg_ratio": index, "status": reference_status(index), "adjusted_joint_resistance_n": None,
                                     "Cg": None, "Cdelta": None, "complete_joint_acceptance": False})
                if mode == "n01":
                    continue
                family, order, direction, partial = families[record["axis_id"]]
                tension = record["signed_axial_n"]
                shear = record["same_plane_lateral_n"]
                area = math.pi * (record["modeled_full_body_diameter_in"] * 25.4)**2 / 4
                if record["kind"] == "retained_bolt":
                    direct = retained_method.steel_references(tension, record["components_n"],
                                                              record["modeled_full_body_diameter_in"], steel)
                    direct = direct["conditional_nominal_material_reference"]
                    thread_area = (.1419 if record["modeled_full_body_diameter_in"] == .5 else .0775) * 25.4**2
                else:
                    thread_area = fasteners["dimension_inputs"]["nut"]["tensile_stress_area_in2"] * 25.4**2
                    direct = steel.bolt_first_yield_reference(
                        axial_force_n=tension, lateral_shear_vector_n=tuple(record["components_n"]),
                        minimum_tensile_area_mm2=thread_area, shear_plane_area_mm2=area,
                        specified_min_yield_mpa=FYB_PSI * PSI_MPA, property_scenario_id="Grade5_nominal_UNC_At_and_full_D_shank",
                        material_basis="Pinned Grade 5 92-ksi conditional material scenario; not delivered evidence",
                        tensile_area_basis="Pinned quarter-inch nominal UNC tensile stress area, not measured minimum root",
                        shear_area_basis="Hypothetical smooth full-D interface section",
                        combined_action_area_mm2=area,
                        combined_action_section_basis="Same-state T and average V at a smooth full-D section; bending excluded")
                row = {**identity, "obligation": "N10", "signed_axial_n": tension, "same_plane_lateral_n": shear,
                       "source_record_index": source_index,
                       "source_component_rows": record["component_rows"], "source_tie_row": record["tie_row"],
                       "signed_force_on_first_body_xyz_n": record["force_on_first_body_xyz_n"],
                       "receivers_head_to_nut": order, "geometry": family, "partial_supported_ring_route": partial,
                       "geometry_applicability": geometry_evidence[record["axis_id"]],
                       "nominal_thread_tensile_area_mm2": thread_area, "direct_T_V_reference": direct,
                       "thread_tension_ratio": direct["tension_first_yield_utilization"],
                       "average_T_V_ratio": direct["interaction_utilization"],
                       "shaft_ratio": None, "same_state_steel_ratio": None,
                       "shaft_null_reason": geometry_issues.get(record["axis_id"]),
                       "shaft": None, "actual_steel_resistance_n": None, **FLAGS}
                try:
                    geometry_require(family is not None, row["shaft_null_reason"])
                    force_on_host = np.asarray(record["force_on_first_body_xyz_n"] if order[0] == record["receivers"][0]
                                               else record["force_on_second_body_xyz_n"], dtype=float)
                    arbitrary = shear < 1e-9
                    drive = -force_on_host / shear if not arbitrary else np.asarray(record["component_directions_xyz"][0])
                    require(abs(float(drive @ np.asarray(direction))) < 1e-8, "drive not perpendicular to shaft")
                    rotation_axis = np.cross(direction, drive)
                    source = {**identity, "signed_T_n": tension, "V_n": shear, "drive_unit_xyz": drive.tolist(),
                              "rotation_axis_xyz": rotation_axis.tolist(), "lateral_direction_arbitrary": arbitrary,
                              "physical_interface_point_xyz_mm": record["point_xyz_mm"],
                              "shaft_axis_head_to_nut_xyz": direction, "receivers_head_to_nut": order,
                              "Fe_mpa": {role: lateral.bearing(lateral.angle(force_on_host, unit(members[body]["axis"]))) * PSI_MPA
                                         for role, body in zip(("host", "cleat"), order, strict=True)}}
                    helper.LENGTH = family["host_length_mm"] + family["cleat_length_mm"]
                    shaft_calls += 1
                    state, beam, _bore = helper.solve_state(source, family, KWOOD)
                    require(len(beam) == 80 and state["small_angle_projected_axial_shortening_mm"] == 0.0,
                            "full beam census or first-order convention differs")
                    require(abs(state["host_force_balance_residual_n"]) <= 1e-6
                            and abs(state["host_moment_balance_residual_nmm"]) <= helper.LENGTH * 1e-6,
                            "independent host wrench does not close")
                    row["shaft"] = state
                    row["shaft_ratio"] = state["peak_beam_stress_witness"]["proxy_over_conditional_92ksi_Fyb"]
                    row["same_state_steel_ratio"] = max(row["thread_tension_ratio"], row["average_T_V_ratio"], row["shaft_ratio"])
                    field_rows.extend({**identity, **field} for field in beam)
                except (KeyError, TypeError, ValueError, ArithmeticError, np.linalg.LinAlgError) as error:
                    # Preserve missing modeled bends as NULL, never as a V/T-only completion.
                    row["shaft_null_reason"] = str(error)
                row["status"] = reference_status(row["same_state_steel_ratio"])
                row["thread_tension_status"] = reference_status(row["thread_tension_ratio"])
                row["average_T_V_status"] = reference_status(row["average_T_V_ratio"])
                catalog = hardware.STACKS[hardware.ROUTES[family_ids[record["axis_id"]]][0]]
                source_join = {
                    "source_record_path": api.key(SAVED / "records.jsonl"), "source_record_index": source_index,
                    "source_record_sha256": pins[SAVED / "records.jsonl"],
                    "saved_extraction_receipt_sha256": pins[SAVED / "receipt.json"],
                    "steel_record_path": "steel.jsonl", "steel_record_index": len(steel_rows),
                    "source_component_rows": record["component_rows"], "source_tie_row": record["tie_row"],
                    "fresh_source_row_id": force_rows[record["tie_row"]]["row_id"],
                    "fresh_force_source": api.key(api.EXPORT / "global-demands.jsonl"),
                    "fresh_force_source_sha256": pins[api.EXPORT / "global-demands.jsonl"],
                    "source_comparison_sha256": pins[api.FRAME / "comparison.json"],
                    "source_response_sha256": pins[api.FRAME / "response.npz"],
                    "producer_sha256": pins[Path(__file__).resolve()], "shaft_helper_sha256": PINS[SHAFT],
                }
                for end_index in (0, 1):
                    washer_rows.append(washer_end_source(record, row["shaft"], family, order, direction, partial,
                                                         catalog, end_index, source_join, helper, traction, np,
                                                         row["shaft_null_reason"], geometry_evidence[record["axis_id"]]))
                steel_rows.append(row)
        finally:
            api.authenticate(pins)
        require(len(end_rows) == 72 and len(steel_rows) == (504 if mode == "full" else 0)
                and len(washer_rows) == (1008 if mode == "full" else 0), "finite worksheet coverage differs")
        completed = sum(row["shaft_ratio"] is not None for row in steel_rows)
        recovered_ends = sum(row["status"] == "COMPLETE_ISOLATED_END_SOURCE" for row in washer_rows)
        result = {
            "schema": "bolt_reference_completion/v2", "mode": mode,
            "status": "COMPLETE_N01_N10_PENDING" if mode == "n01" else
                      "COMPLETE_CONDITIONAL_COMPARISONS" if completed == 504 else "PARTIAL_NULL_SHAFT_STATES",
            "case_ids": list(CASES), "source_comparison_sha256": pins[api.FRAME / "comparison.json"],
            "source_response_sha256": pins[api.FRAME / "response.npz"],
            "source_gravity_assessment_sha256": pins[api.GRAVITY / "operator-assessment.json"],
            "load_envelope": {"climbers_lb": [250, 250], "signed_horizontal_n": 300, "hold_lever_mm": 100,
                              "modeled_mass_kg": comparison["modeled_mass_kg"], "dead_load_factor": comparison["dead_load_factor"]},
            "counts": {"existing_source_axes": 104, "proposal_axes": 108, "owned_existing_axes": 84,
                       "candidate_axes": 72, "retained_axes": 12, "end_grain_axes": 12, "end_grain_blocks": 6,
                       "N01_states": 72, "N10_states": len(steel_rows), "N10_required_states": 504,
                       "completed_shaft_states": completed, "pending_shaft_states": 504 if mode == "n01" else 0,
                       "shaft_helper_calls": shaft_calls, "unsupported_geometry_axes": len(geometry_issues),
                       "unsupported_geometry_states": 6 * len(geometry_issues),
                       "normalized_geometry_axes": len(normalizations), "normalized_geometry_states": 6 * len(normalizations),
                       "null_shaft_states": len(steel_rows) - completed, "shaft_field_samples": len(field_rows),
                       "washer_end_states": len(washer_rows), "required_washer_end_states": 1008,
                       "recovered_washer_end_states": recovered_ends,
                       "null_washer_end_states": len(washer_rows) - recovered_ends},
            "N01": component_summary(end_rows, "Ceg_ratio"),
            "N10_geometry_applicability": {"status": "PENDING_NOT_RUN" if mode == "n01" else "MAPPED",
                "unsupported_axes": [{"axis_id": axis, **geometry_evidence[axis]} for axis in sorted(geometry_issues)],
                "normalized_axes": [{"axis_id": axis, **normalizations[axis]} for axis in sorted(normalizations)],
                "geometry_precision_mm": GEOMETRY_PRECISION_MM,
                "recorded_span_mismatch_bound_mm": RECORDED_SPAN_MISMATCH_BOUND_MM,
                "maximum_original_normalized_span_mismatch_mm": max(
                    (abs(row["original_signed_endpoint_gap_mm"]) for row in normalizations.values()), default=None),
                "maximum_endpoint_correction_mm": max(
                    (row["maximum_endpoint_correction_mm"] for row in normalizations.values()), default=None)},
            "N10": {"status": "PENDING_NOT_RUN", "required_states": 504} if mode == "n01" else
                   {key: component_summary(steel_rows, key) for key in
                    ("thread_tension_ratio", "average_T_V_ratio", "shaft_ratio", "same_state_steel_ratio")},
            "N09_end_source_export": {
                "status": "PENDING_NOT_RUN" if mode == "n01" else
                          "COMPLETE_END_SOURCES" if recovered_ends == 1008 else "PARTIAL_NULL_END_SOURCES",
                "finite_end_sources": recovered_ends, "N09_complete": False,
                "null_reasons": [{"join_key": row["join_key"], "reason": row["null_reason"]} for row in washer_rows
                                 if row["status"] != "COMPLETE_ISOLATED_END_SOURCE"],
            },
            "assumptions": {"Ceg_applied_once": CEG, "conditional_Fyb_psi": FYB_PSI, "Kwood_mpa_per_mm": KWOOD,
                            "E_bolt_mpa": helper.E_BOLT if helper else None,
                            "Khead_mpa_per_mm": helper.K_HEAD if helper else None,
                            "geometric_stiffness_and_shortening": False, "preload_n": 0,
                            "head_nut_land": "quarter-inch radius 5 mm; retained radius half catalog minimum nut across-flats; hypothetical circular land at both ends",
                            "central_partial_seat": "5-mm supported ring at both ends; no crescent or full washer credited",
                            "other_end_seats": "concentric full annulus hypothesis; actual masks and hardware spreading unqualified"},
            "unsupported_scope": [
                "No completed N10 comparison for a state with null shaft fields; the same-state T/V diagnostic does not replace bending.",
                "N01-only mode leaves all 504 N10 shaft comparisons and all 1008 N09 end-source rows pending; it performs no shaft solve.",
                "End T/M and pressure recovery supply N09 inputs only; no washer flexure, steel stress or capacity is calculated or accepted here.",
                "Actual thread-root/shank area, delivered yield/Fyb, transition/profile and head/nut/washer strength are unqualified.",
                "Common multi-bolt timber poses, shared end pressures, group transfer and actual changed-hole stiffness are outside the isolated shaft proxy.",
                "End-grain Ceg does not close axial wood bearing, splitting, group/geometry adjustments or complete-joint resistance.",
                "No saved imposed end couples or frame beam bends exist for these 84 axes; recovered shaft bending belongs to the stated isolated contact model.",
                "Sixteen corner axes, four continuous knee shafts and four new internal bridge axes belong to their existing separate producers.",
                "Frame stability/permanent loads and common knee deformation remain parent/peer tasks; Hillman/panel qualification is outside this producer.",
            ],
            "arithmetic_runtime": {"numpy": np.__version__, "scipy": scipy.__version__ if scipy else None}, **FLAGS,
        }
        worksheet_outputs = [("end-grain.jsonl", end_rows)]
        if mode == "full":
            worksheet_outputs.extend((("steel.jsonl", steel_rows), ("shaft-fields.jsonl", field_rows),
                                      ("washer-ends.jsonl", washer_rows)))
        for name, values in worksheet_outputs:
            write_owned(output, name, "".join(serialize(value) for value in values))
        write_owned(output, "summary.json", serialize(result))
        write_owned(output, "producer.py.snapshot", Path(__file__).read_text())
        sources = {api.key(source_path): expected for source_path, expected in sorted(pins.items())}
        write_owned(output, "sources.json", serialize(sources))
        api.authenticate(pins)
        artifact_names = {name for name, _values in worksheet_outputs} | {"summary.json", "producer.py.snapshot", "sources.json"}
        artifacts = {name: digest(output / name) for name in sorted(artifact_names)}
        receipt = {"schema": "bolt_reference_completion_receipt/v2", "status": result["status"], "mode": mode,
                   "producer_sha256": pins[Path(__file__).resolve()], "source_sha256": sources,
                   "output_sha256": artifacts, "sources_authenticated_before_and_after": True,
                   "counts": result["counts"], "shaft_helper_calls": shaft_calls, "N09_complete": False,
                   "N01_comparisons_complete": len(end_rows) == 72,
                   "N10_comparisons_complete": completed == 504,
                   "N09_end_sources_complete": recovered_ends == 1008,
                   "N10_pending": completed != 504, **FLAGS}
        if mode == "full":
            receipt["historical_producer_snapshot_binding"] = {
                "snapshot_path": api.key(N01_PRODUCER_SNAPSHOT), "sha256": PINS[N01_PRODUCER_SNAPSHOT],
                "original_maintained_path": api.key(Path(__file__).resolve()),
                "scope": "Exact a007 producer consumed by completed N01; snapshot identity only, no old receipt repinning or numerical acceptance transfer",
            }
        write_owned(output, "receipt.json", serialize(receipt))
        return receipt


def recovery_closure(api):
    """Authenticate recovery01 verbatim, retaining full01 and historical pins."""
    maintained = Path(__file__).resolve()
    snapshot = RECOVERY_BASE / "producer.py.snapshot"
    pins = {**PINS, **RECOVERY_METHOD_PINS, maintained: digest(maintained),
            RECOVERY_BASE / "receipt.json": RECOVERY_RECEIPT_SHA, snapshot: RECOVERY_PRODUCER_SHA}
    api.authenticate(pins)
    baseline = api.read(RECOVERY_BASE / "receipt.json")
    require(baseline["schema"] == "bolt_reference_completion_receipt/v2"
            and baseline["mode"] == "full"
            and baseline["producer_sha256"] == RECOVERY_PRODUCER_SHA
            and baseline["output_sha256"]["producer.py.snapshot"] == RECOVERY_PRODUCER_SHA
            and baseline["sources_authenticated_before_and_after"] is True
            and len(baseline["source_sha256"]) == 146
            and len(baseline["output_sha256"]) == 9,
            "recovery01 frozen receipt contract differs")
    expected_counts = {"N01_states": 72, "N10_states": 504, "completed_shaft_states": 502,
                       "null_shaft_states": 2, "shaft_field_samples": 40160,
                       "recovered_washer_end_states": 1004, "null_washer_end_states": 4,
                       "normalized_geometry_axes": 16, "normalized_geometry_states": 96,
                       "unsupported_geometry_axes": 0, "washer_end_states": 1008}
    require(all(baseline["counts"][name] == value for name, value in expected_counts.items()),
            "recovery01 result census differs")
    exception_count = 0
    for source_name, expected in baseline["source_sha256"].items():
        source_path = ROOT / source_name
        if source_path == maintained:
            require(expected == RECOVERY_PRODUCER_SHA, "unrecognized historical producer exception")
            source_path = snapshot
            exception_count += 1
        api.bind(pins, source_path, expected)
    require(exception_count == 1, "recovery01 historical producer entry missing")
    for artifact_name, expected in baseline["output_sha256"].items():
        artifact_path = RECOVERY_BASE / artifact_name
        require(artifact_name in ARTIFACTS and artifact_path.resolve().parent == RECOVERY_BASE,
                "recovery01 artifact escapes its packet")
        api.bind(pins, artifact_path, expected)
    api.authenticate(pins)
    exception = {"original_maintained_path": api.key(maintained), "snapshot_path": api.key(snapshot),
                 "sha256": RECOVERY_PRODUCER_SHA, "original_receipt_sha256": RECOVERY_RECEIPT_SHA,
                 "scope": "Exact consumed 509 producer; original receipt pins remain unchanged"}
    require(pins[FULL01 / "receipt.json"] == FULL01_RECEIPT_SHA
            and pins[FULL01 / "producer.py.snapshot"] == FULL01_PRODUCER_SHA,
            "original full01 source closure lost")
    oracle = api.read(CONIC_ORACLE)
    require(oracle["producer_sha256"] == RECOVERY_METHOD_PINS[CONIC_METHOD]
            and oracle["clarabel_version"] == "0.11.1"
            and oracle["oracle"]["conic"]["status"] == "Solved"
            and oracle["oracle"]["circular_force_n"] == [3.0, 4.0],
            "existing Clarabel interface known-answer evidence differs")
    return pins, baseline, exception


def seeded_shaft_solver(helper):
    """Adapt the pinned function's initialization and trace only; reuse its code."""
    require(digest(SHAFT) == PINS[SHAFT], "shaft helper changed before AST adaptation")
    original = next(node for node in ast.parse(SHAFT.read_text()).body
                    if isinstance(node, ast.FunctionDef) and node.name == "solve_state")
    original_dump = ast.dump(original, include_attributes=False)

    def statement(source):
        return ast.parse(source).body[0]

    changes = Counter()
    initialization = ast.dump(statement("pose = np.zeros(36)"))
    cold_seed = ast.dump(statement('''if lateral > 1e-9:
    pose[:34:2] = gap
    pose[34] = 2*gap + lateral/(kwood*diameter*min(family["host_length_mm"], family["cleat_length_mm"]))'''))
    terminal_gate = ast.dump(statement('require(converged, "STOP: local equilibrium did not converge within 150 iterations")'))
    insertions = {
        ast.dump(statement("evaluation = evaluate(pose)")):
            ('recovery_trace("iterate", iteration, pose, evaluation)', "iteration_trace", False),
        ast.dump(statement("slope = float(gradient @ step)")):
            ('recovery_trace("step", iteration, pose, evaluation, eigenvalues=eigenvalues, positive=positive, step=step, slope=slope)',
             "step_trace", False),
        ast.dump(statement("pose = candidate")):
            ('recovery_trace("accepted", iteration, candidate, None, fraction=fraction, backtrack=backtrack)',
             "accepted_trace", True),
    }

    class SeedAndTrace(ast.NodeTransformer):
        def visit(self, node):
            if isinstance(node, ast.stmt):
                shape = ast.dump(node)
                if shape == initialization:
                    changes["seed_pose"] += 1
                    return ast.copy_location(statement("pose = recovery_seed_pose.copy()"), node)
                if shape == cold_seed:
                    changes["cold_seed_removed"] += 1
                    return None
                if shape == terminal_gate:
                    changes["terminal_trace"] += 1
                    return [ast.copy_location(statement(
                        'recovery_trace("terminal", iteration, pose, evaluate(pose), converged=converged)'), node), node]
                if shape in insertions:
                    source, label, before = insertions[shape]
                    changes[label] += 1
                    added = ast.copy_location(statement(source), node)
                    return [added, node] if before else [node, added]
            return super().visit(node)

    adapted = SeedAndTrace().visit(original)
    require(changes == {"seed_pose": 1, "cold_seed_removed": 1, "iteration_trace": 1,
                        "step_trace": 1, "accepted_trace": 1, "terminal_trace": 1},
            "pinned shaft initialization/trace AST shapes differ")
    adapted.name = "_solve_state_recovery"
    adapted.args.args.extend([ast.arg(arg="recovery_seed_pose"), ast.arg(arg="recovery_trace")])
    iteration_caps = [node.args[0].value for node in ast.walk(adapted)
                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                      and node.func.id == "range" and len(node.args) == 1
                      and isinstance(node.args[0], ast.Constant) and node.args[0].value in (150, 50)]
    require(sorted(iteration_caps) == [50, 150], "original Newton/Armijo iteration caps differ")
    adapted_dump = ast.dump(adapted, include_attributes=False)
    module = ast.fix_missing_locations(ast.Module(body=[adapted], type_ignores=[]))
    compiled = compile(module, str(SHAFT) + ":seed-and-trace-only", "exec")
    function_code = next(value for value in compiled.co_consts
                         if isinstance(value, CodeType) and value.co_name == adapted.name)
    solve = FunctionType(function_code, helper.__dict__, adapted.name)
    contract = {"helper_sha256": PINS[SHAFT], "AST_changes": dict(changes),
                "original_function_AST_sha256": hashlib.sha256(original_dump.encode()).hexdigest(),
                "adapted_function_AST_sha256": hashlib.sha256(adapted_dump.encode()).hexdigest(),
                "Newton_iterations_max": 150, "Armijo_backtracks_max": 50,
                "only_initial_pose_and_logging_changed": True,
                "extra_terminal_residual_evaluations_per_call": 1}
    return solve, contract


def contact_QP_seed(quadratic, linear, contact_rows, offsets, weights, np, sparse, clarabel, time_limit=5.0):
    """Initial guess for positive-part springs; final acceptance stays elsewhere.

    Minimize .5 z'Kz+l'z+.5 sum(w*p**2), p>=Cz-g, p>=0.
    This is the original finite spring energy with its positive parts lifted.
    """
    require(clarabel.__version__ == "0.11.1", "recorded Clarabel version required")
    free, contacts = len(linear), len(weights)
    require(quadratic.shape == (free, free) and contact_rows.shape == (contacts, free)
            and offsets.shape == weights.shape == (contacts,)
            and np.isfinite(quadratic).all() and np.isfinite(linear).all()
            and np.isfinite(contact_rows).all() and np.isfinite(offsets).all()
            and np.isfinite(weights).all() and np.min(weights) > 0, "invalid seed QP data")
    P = sparse.block_diag((sparse.csc_matrix((quadratic + quadratic.T) / 2), sparse.diags(weights)), format="csc")
    identity = sparse.eye(contacts, format="csc")
    A = sparse.vstack((sparse.hstack((sparse.csc_matrix(contact_rows), -identity)),
                       sparse.hstack((sparse.csc_matrix((contacts, free)), -identity))), format="csc")
    q, b = np.r_[linear, np.zeros(contacts)], np.r_[offsets, np.zeros(contacts)]
    settings = clarabel.DefaultSettings()
    settings.verbose, settings.max_iter, settings.time_limit = False, 150, time_limit
    settings.tol_gap_abs, settings.tol_gap_rel, settings.tol_feas = 1e-10, 1e-11, 1e-11
    result = clarabel.DefaultSolver(sparse.triu(P, format="csc"), q, A, b,
                                    [clarabel.NonnegativeConeT(2 * contacts)], settings).solve()
    status = str(result.status)
    require(status in {"Solved", "AlmostSolved", "InsufficientProgress", "MaxIterations", "MaxTime"},
            "numerical seed QP status " + status)
    values = np.asarray(result.x, dtype=float)
    require(values.shape == (free + contacts,) and np.isfinite(values).all(), "nonfinite seed QP pose")
    pose, indentations = values[:free], values[free:]
    exact_indentations = np.maximum(contact_rows @ pose - offsets, 0.0)
    report = {"status": status, "iterations": int(result.iterations), "time_seconds": float(result.solve_time),
              "free_variables": free, "spring_variables": contacts, "variables": free + contacts,
              "inequality_rows": 2 * contacts, "max_iterations": 150, "time_limit_seconds": time_limit,
              "seed_precision": {"tol_gap_abs": 1e-10, "tol_gap_rel": 1e-11, "tol_feas": 1e-11},
              "law_lift_indentation_error_mm": float(np.max(abs(indentations - exact_indentations))),
              "seed_energy_without_constant_nmm": float(0.5 * pose @ quadratic @ pose + linear @ pose
                                                         + 0.5 * np.sum(weights * exact_indentations**2)),
              "seed_base_gradient_inf": float(np.max(abs(quadratic @ pose + linear
                                                         + contact_rows.T @ (weights * exact_indentations)))),
              "seed_base_variables": pose.tolist(), "numerical_guess_only": True,
              "physical_acceptance": False, "material_or_law_change": False,
              "primary_docs": ["https://clarabel.org/stable/python/getting_started_py/",
                               "https://clarabel.org/stable/api_settings/"]}
    return pose, report


def seed_known_answer(np, sparse, clarabel):
    """Parent-only prerequisite: one analytic gap/series-spring QP, no frame."""
    rows = np.asarray([[1., 0., 0.], [-1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
    answer, info = contact_QP_seed(np.zeros((3, 3)), np.asarray([-5., -4., -4.]), rows,
                                   np.asarray([1.15, 1.15, 0., 0.]),
                                   np.asarray([1000., 1000., 10000., 20.]), np, sparse, clarabel, 2.0)
    expected = np.asarray([1.155, 4. / 10000., 4. / 20.])
    recovered = np.asarray([1000. * (max(answer[0] - 1.15, 0.) - max(-answer[0] - 1.15, 0.)),
                            10000. * max(answer[1], 0.), 20. * max(answer[2], 0.)])
    pose_error = float(np.max(abs(answer - expected)))
    force_error = float(np.max(abs(recovered - np.asarray([5., 4., 4.]))))
    require(info["status"] == "Solved" and pose_error <= 1e-7 and force_error <= 1e-6,
            "seed QP analytic clearance/series-spring answer differs")
    return {"schema": "bolt_seed_known_answer/v1", "status": "MATCH_ANALYTIC_ANSWER",
            "expected_gap_motion_and_two_closures_mm": expected.tolist(), "observed_mm": answer.tolist(),
            "recovered_gap_and_series_forces_n": recovered.tolist(), "maximum_pose_error_mm": pose_error,
            "maximum_force_error_n": force_error, "QP": info,
            "existing_interface_known_answer_path": str(CONIC_ORACLE.relative_to(ROOT)),
            "existing_interface_known_answer_sha256": RECOVERY_METHOD_PINS[CONIC_ORACLE],
            "native_CAD_frame_or_test_run": False}


def shaft_convex_seed(source, family, helper, np, sparse, clarabel):
    """Lift the exact pinned shaft's bore and prescribed-T annulus energies."""
    tension = source["signed_T_n"]
    elastic, geometric, samples, _curvatures, _inertia = helper.beam_model(family, tension)
    require(np.count_nonzero(geometric) == 0 and len(samples) == 48, "seed first-order beam convention differs")
    free = 42 if tension > 0 else 36
    quadratic = np.zeros((free, free))
    quadratic[:36, :36] = elastic
    linear = np.zeros(free)
    linear[34] = -source["V_n"]
    bore_rows = np.zeros((48, free))
    bore_rows[:, :36] = np.vstack([sample[0] for sample in samples])
    gap = (family["bore_mm"] - family["diameter_mm"]) / 2
    coefficient = KWOOD * family["diameter_mm"] * np.asarray([sample[1] for sample in samples])
    row_blocks, offset_blocks, weight_blocks = [bore_rows, -bore_rows], [np.full(48, gap)] * 2, [coefficient] * 2
    if tension > 0:
        inner = family["washer_ID_max_mm"] / 2
        head_quad = helper.annulus(inner, family["flat_radius_mm"])
        wood_quad = helper.annulus(inner, family["washer_OD_min_mm"] / 2)
        for end_index in (0, 1):
            slope = np.zeros(36)
            if end_index == 0:
                slope[1], slope[35] = 1 / helper.LENGTH, -1 / helper.LENGTH
            else:
                slope[33] = 1 / helper.LENGTH
            for hardware_side, quadrature in ((True, head_quad), (False, wood_quad)):
                area, transverse, _radius = quadrature
                require(len(area) == len(transverse) == 256, "original annulus quadrature census differs")
                contact = np.zeros((256, free))
                closure_index = 38 + 2 * end_index + (0 if hardware_side else 1)
                contact[:, closure_index] = 1.
                contact[:, 36 + end_index] = (-1 if hardware_side else 1) * transverse / helper.LENGTH
                if hardware_side:
                    contact[:, :36] = transverse[:, None] * slope
                linear[closure_index] = -tension
                row_blocks.append(contact)
                offset_blocks.append(np.zeros(256))
                weight_blocks.append((helper.K_HEAD if hardware_side else KWOOD) * area)
    seed, info = contact_QP_seed(quadratic, linear, np.vstack(row_blocks), np.concatenate(offset_blocks),
                                 np.concatenate(weight_blocks), np, sparse, clarabel)
    info.update({"method": "Same finite spring energy lifted to a convex QP; only a 36-DOF initial pose is returned",
                 "zero_T_contacts_omitted": tension == 0, "bore_quadrature_samples": 48,
                 "end_pressure_springs": 1024 if tension > 0 else 0,
                 "closure_linear_term": "-T times each of four closures; washer rotation stationarity enforces series moment balance",
                 "washer_rotation_coordinates": "length times physical radians",
                 "original_shaft_helper_sha256": PINS[SHAFT]})
    return seed[:36], info


def recover(output):
    """Parent API: two convex-seeded calls; reuse recovery01 rows byte-exact."""
    output = Path(output).absolute()
    require(RAW.resolve() == RAW and output.resolve() == output and output.parent == RAW
            and not output.exists(), "fresh immediate owned RAW child required")
    with imports():
        api = load_module(EXTRACTOR, "bolt_recovery_saved_extraction")
        pins, baseline_receipt, historical_binding = recovery_closure(api)
        import clarabel
        import numpy as np
        import scipy
        from scipy import sparse

        require(np.__version__ == "2.5.2" and scipy.__version__ == "1.18.1"
                and clarabel.__version__ == "0.11.1", "pinned recovery runtime differs")
        references = load_module(REFERENCE_LOADER, "bolt_recovery_reference_loader")
        lateral_path = PACKET / "lateral_reference.py"
        require(digest(lateral_path) == pins[lateral_path], "lateral helper changed")
        lateral = api.pure_module(lateral_path, "bolt_recovery_lateral")
        require(Path(sys.modules["fea.dowel_yield"].__file__).resolve() == ROOT / "fea/dowel_yield.py",
                "wrong dowel helper import")
        hardware = load_module(HARDWARE, "bolt_recovery_hardware")
        helper = load_module(SHAFT, "bolt_recovery_shaft")
        original_beam_model = helper.beam_model

        def first_order_beam(family, tension):
            elastic, geometric, samples, curvatures, inertia = original_beam_model(family, tension)
            return elastic, np.zeros_like(geometric), samples, curvatures, inertia

        helper.beam_model = first_order_beam
        solve, solver_contract = seeded_shaft_solver(helper)
        traction = references.pure_functions(TRACTION, ["action", "wrench", "wood_seat", "shifted"],
                                             {"np": np, "require": require})
        with HARDWARE_AXES.open(newline="", encoding="utf-8") as source_stream:
            family_ids = {row["axis_id"]: row["family_id"] for row in csv.DictReader(source_stream)}
        inputs = api.read(api.GEOMETRY)
        members = {row["member_id"]: row["reduced_geometry_descriptor"] for row in inputs["members"]
                   if row["member_kind"] != "panel"}
        saved = [json.loads(line) for line in (SAVED / "records.jsonl").read_bytes().splitlines()]
        original_bytes = {name: (RECOVERY_BASE / name).read_bytes() for name in
                          ("end-grain.jsonl", "steel.jsonl", "shaft-fields.jsonl", "washer-ends.jsonl")}
        original_lines = {name: value.splitlines(keepends=True) for name, value in original_bytes.items()}
        steel_rows = [json.loads(line) for line in original_lines["steel.jsonl"]]
        washer_rows = [json.loads(line) for line in original_lines["washer-ends.jsonl"]]
        identity = lambda row: (row["case_id"], row["axis_id"])
        targets = [index for index, row in enumerate(steel_rows) if row["shaft"] is None]
        accepted = [row for row in steel_rows if row["shaft"] is not None]
        require(len(saved) == len(steel_rows) == 504 and len(accepted) == 502
                and len(original_lines["end-grain.jsonl"]) == 72
                and len(original_lines["shaft-fields.jsonl"]) == 40160
                and len(washer_rows) == 1008 and len(targets) == 2
                and {identity(steel_rows[index]) for index in targets} == RECOVERY_STATES,
                "frozen recovery state census differs")
        require(all(row["shaft_null_reason"] == "STOP: local equilibrium did not converge within 150 iterations"
                    and row["same_state_steel_ratio"] is None and row["geometry"] is not None
                    for row in (steel_rows[index] for index in targets)), "recovery contains another unsupported scope")
        require(len({identity(row) for row in steel_rows}) == 504
                and all(identity(row) == identity(saved[row["source_record_index"]])
                        and row["signed_axial_n"] == saved[row["source_record_index"]]["signed_axial_n"]
                        and row["same_plane_lateral_n"] == saved[row["source_record_index"]]["same_plane_lateral_n"]
                        and row["source_component_rows"] == saved[row["source_record_index"]]["component_rows"]
                        and row["source_tie_row"] == saved[row["source_record_index"]]["tie_row"]
                        and row["signed_force_on_first_body_xyz_n"] == saved[row["source_record_index"]]["force_on_first_body_xyz_n"]
                        for row in steel_rows), "recovery01/saved extraction source joins differ")
        for index, row in enumerate(steel_rows):
            for end_index, role in enumerate(("head", "nut")):
                end = washer_rows[2 * index + end_index]
                require(identity(end) == identity(row) and end["end_role"] == role
                        and end["receiver_member"] == row["receivers_head_to_nut"][end_index]
                        and end["source_join"]["steel_record_index"] == index
                        and ((end["status"] == "COMPLETE_ISOLATED_END_SOURCE") == (row["shaft"] is not None)),
                        "recovery01 own-end row/state join differs")
        original_field_census = Counter(identity(json.loads(line)) for line in original_lines["shaft-fields.jsonl"])
        require(original_field_census == {identity(row): 80 for row in accepted}, "accepted shaft field census differs")
        previous_trace = api.read(RECOVERY_BASE / "recovery-trace.json")
        failed_traces = {identity(row): row for row in previous_trace["states"] if row["status"] != "SOLVED"}
        require(set(failed_traces) == RECOVERY_STATES
                and all(len(row["events"]) == 451 and row["events"][-1]["event"] == "terminal"
                        and row["events"][-1]["converged"] is False for row in failed_traces.values()),
                "authenticated two-state stagnation traces differ")
        api.authenticate(pins)
        require(all(not source_path.is_relative_to(output) for source_path in pins), "output contains a consumed source")
        try:
            known_answer = seed_known_answer(np, sparse, clarabel)
        finally:
            api.authenticate(pins)
        output.mkdir(parents=True, exist_ok=False)
        combined_lines = {name: list(lines) for name, lines in original_lines.items()}
        traces, added_fields, shaft_calls = [], [], 0
        try:
            for index in targets:
                row = dict(steel_rows[index])
                record = saved[row["source_record_index"]]
                family, order = row["geometry"], row["receivers_head_to_nut"]
                old_end = washer_rows[2 * index]
                direction = old_end["shaft_axis_head_to_nut_xyz"]
                shear, tension = row["same_plane_lateral_n"], row["signed_axial_n"]
                force_on_host = np.asarray(record["force_on_first_body_xyz_n"] if order[0] == record["receivers"][0]
                                           else record["force_on_second_body_xyz_n"], dtype=float)
                require(shear > 1e-9 and tension >= 0, "target is outside the frozen loaded-state recovery")
                drive = -force_on_host / shear
                require(abs(float(drive @ np.asarray(direction))) < 1e-8
                        and math.isclose(float(np.linalg.norm(drive)), 1.0, abs_tol=1e-8), "target transverse drive differs")
                source = {**{key: record[key] for key in ("case_id", "axis_id", "gap_scale", "kind")},
                          "signed_T_n": tension, "V_n": shear, "drive_unit_xyz": drive.tolist(),
                          "rotation_axis_xyz": np.cross(direction, drive).tolist(), "lateral_direction_arbitrary": False,
                          "physical_interface_point_xyz_mm": record["point_xyz_mm"],
                          "shaft_axis_head_to_nut_xyz": direction, "receivers_head_to_nut": order,
                          "Fe_mpa": {role: lateral.bearing(lateral.angle(force_on_host, references.unit(members[body]["axis"]))) * PSI_MPA
                                     for role, body in zip(("host", "cleat"), order, strict=True)}}
                trace = {"case_id": row["case_id"], "axis_id": row["axis_id"], "steel_record_index": index,
                         "original_null_reason": row["shaft_null_reason"],
                         "previous_terminal_residual_inf_n": failed_traces[identity(row)]["events"][-1]["scaled_gradient_inf_n"],
                         "convex_seed": None, "events": []}
                traces.append(trace)

                def log(event, iteration, pose, evaluation, _trace=trace, **details):
                    item = {"event": event, "iteration": int(iteration), "pose_inf_scaled_mm": float(np.max(abs(pose)))}
                    if evaluation is not None:
                        item.update({"energy_nmm": float(evaluation[0]),
                                     "scaled_gradient_inf_n": float(np.max(abs(evaluation[1]))),
                                     "active_bore_sample_indices": np.flatnonzero(evaluation[4]).tolist(),
                                     "own_end_moments_nmm": [float(end["moment_nmm"]) for end in evaluation[6]]})
                    if event in ("iterate", "terminal"):
                        item.update({"pose_scaled_mm": pose.tolist(),
                                     "scaled_gradient_residuals_n": evaluation[1].tolist(),
                                     "own_end_relative_tilts_rad": [float(end["relative_tilt_rad"]) for end in evaluation[6]]})
                    if "eigenvalues" in details:
                        positive = details.pop("positive")
                        eigenvalues = details.pop("eigenvalues")
                        step = details.pop("step")
                        item.update({"tangent_eigenvalue_min": float(eigenvalues[0]),
                                     "tangent_eigenvalue_max": float(eigenvalues[-1]),
                                     "tangent_nullity_at_tolerance": int(np.sum(~positive)),
                                     "Newton_step_inf_scaled_mm": float(np.max(abs(step)))})
                    item.update(details)
                    _trace["events"].append(item)

                helper.LENGTH = family["host_length_mm"] + family["cleat_length_mm"]
                row["recovery_provenance"] = {"original_receipt_sha256": RECOVERY_RECEIPT_SHA,
                                               "original_full01_receipt_sha256": FULL01_RECEIPT_SHA,
                                               "original_steel_record_index": index, "seed_method": "exact_spring_energy_convex_QP",
                                               "initial_pose_only_changed": True}
                try:
                    seed, seed_info = shaft_convex_seed(source, family, helper, np, sparse, clarabel)
                    trace["convex_seed"] = seed_info
                    shaft_calls += 1
                    state, beam, _bore = solve(source, family, KWOOD, seed, log)
                    require(len(beam) == 80 and state["small_angle_projected_axial_shortening_mm"] == 0.0,
                            "full beam census or first-order convention differs")
                    require(abs(state["host_force_balance_residual_n"]) <= 1e-6
                            and abs(state["host_moment_balance_residual_nmm"]) <= helper.LENGTH * 1e-6,
                            "independent host wrench does not close")
                    row["shaft"] = state
                    row["shaft_ratio"] = state["peak_beam_stress_witness"]["proxy_over_conditional_92ksi_Fyb"]
                    row["same_state_steel_ratio"] = max(row["thread_tension_ratio"], row["average_T_V_ratio"], row["shaft_ratio"])
                    row["shaft_null_reason"] = None
                    fields = [{**{key: record[key] for key in ("case_id", "axis_id", "gap_scale", "kind")}, **field}
                              for field in beam]
                    added_fields.extend(fields)
                except (KeyError, TypeError, ValueError, ArithmeticError, np.linalg.LinAlgError) as error:
                    row["shaft_null_reason"] = str(error)
                trace["status"] = "SOLVED" if row["shaft"] is not None else "NUMERICAL_NULL"
                trace["null_reason"] = row["shaft_null_reason"]
                row["status"] = reference_status(row["same_state_steel_ratio"])
                steel_rows[index] = row
                combined_lines["steel.jsonl"][index] = serialize(row).encode()
                catalog = hardware.STACKS[hardware.ROUTES[family_ids[row["axis_id"]]][0]]
                source_join = {**old_end["source_join"], "producer_sha256": pins[Path(__file__).resolve()],
                               "recovery_receipt_source_sha256": RECOVERY_RECEIPT_SHA,
                               "historical_producer_snapshot_path": historical_binding["snapshot_path"],
                               "original_producer_sha256": RECOVERY_PRODUCER_SHA,
                               "full01_producer_sha256": FULL01_PRODUCER_SHA}
                for end_index in (0, 1):
                    end = washer_end_source(record, row["shaft"], family, order, direction,
                                            row["partial_supported_ring_route"], catalog, end_index, source_join,
                                            helper, traction, np, row["shaft_null_reason"], row["geometry_applicability"])
                    washer_rows[2 * index + end_index] = end
                    combined_lines["washer-ends.jsonl"][2 * index + end_index] = serialize(end).encode()
        finally:
            api.authenticate(pins)
        require(shaft_calls <= 2, "bounded recovery may call only the two null states once")
        combined_lines["shaft-fields.jsonl"].extend(serialize(row).encode() for row in added_fields)
        preserved_indices = {"steel.jsonl": [index for index in range(504) if index not in targets],
                             "washer-ends.jsonl": [index for index in range(1008) if index // 2 not in targets],
                             "shaft-fields.jsonl": list(range(40160)), "end-grain.jsonl": list(range(72))}
        reused = {}
        for name, indices in preserved_indices.items():
            before = b"".join(original_lines[name][index] for index in indices)
            after = b"".join(combined_lines[name][index] for index in indices)
            require(before == after, "accepted bytes changed in " + name)
            reused[name] = {"preserved_rows": len(indices), "ordered_preserved_rows_sha256": hashlib.sha256(before).hexdigest(),
                            "byte_identical": True, "original_file_sha256": baseline_receipt["output_sha256"][name]}
        full01_lines = {name: (FULL01 / name).read_bytes().splitlines(keepends=True)
                        for name in ("steel.jsonl", "washer-ends.jsonl", "shaft-fields.jsonl", "end-grain.jsonl")}
        first_accepted = [index for index, line in enumerate(full01_lines["steel.jsonl"])
                          if json.loads(line)["shaft"] is not None]
        require(len(first_accepted) == 499, "original full01 accepted census differs")
        first_indices = {"steel.jsonl": first_accepted,
                         "washer-ends.jsonl": [2 * index + end for index in first_accepted for end in (0, 1)],
                         "shaft-fields.jsonl": list(range(39920)), "end-grain.jsonl": list(range(72))}
        original_reused = {}
        for name, indices in first_indices.items():
            first_bytes = b"".join(full01_lines[name][index] for index in indices)
            combined_bytes = b"".join(combined_lines[name][index] for index in indices)
            require(first_bytes == combined_bytes, "original full01 accepted bytes changed in " + name)
            original_reused[name] = {"preserved_rows": len(indices), "byte_identical": True,
                                     "ordered_preserved_rows_sha256": hashlib.sha256(first_bytes).hexdigest()}
        completed = sum(row["shaft"] is not None for row in steel_rows)
        recovered_ends = sum(row["status"] == "COMPLETE_ISOLATED_END_SOURCE" for row in washer_rows)
        result = api.read(RECOVERY_BASE / "summary.json")
        result["status"] = "COMPLETE_CONDITIONAL_COMPARISONS" if completed == 504 else "PARTIAL_NULL_SHAFT_STATES"
        result["execution_scope"] = "RECOVER_TWO_NULL_STATES"
        result["counts"].update({"completed_shaft_states": completed, "null_shaft_states": 504 - completed,
                                 "shaft_helper_calls": shaft_calls, "shaft_field_samples": 40160 + len(added_fields),
                                 "recovered_washer_end_states": recovered_ends, "null_washer_end_states": 1008 - recovered_ends,
                                 "reused_shaft_states": 502, "reused_washer_end_states": 1004,
                                 "seed_known_answer_calls": 1, "target_convex_seed_calls": len(traces)})
        result["N10"] = {key: component_summary(steel_rows, key) for key in
                         ("thread_tension_ratio", "average_T_V_ratio", "shaft_ratio", "same_state_steel_ratio")}
        result["N09_end_source_export"] = {
            "status": "COMPLETE_END_SOURCES" if recovered_ends == 1008 else "PARTIAL_NULL_END_SOURCES",
            "finite_end_sources": recovered_ends, "N09_complete": False,
            "null_reasons": [{"join_key": row["join_key"], "reason": row["null_reason"]} for row in washer_rows
                             if row["status"] != "COMPLETE_ISOLATED_END_SOURCE"]}
        result["recovery"] = {"original_receipt_sha256": RECOVERY_RECEIPT_SHA,
                              "original_full01_receipt_sha256": FULL01_RECEIPT_SHA, "solver_contract": solver_contract,
                              "max_calls": 2, "retry_calls": 0, "reused_outputs": reused,
                              "original_full01_reused_outputs": original_reused,
                              "new_solved_shaft_states": completed - 502, "known_answer": known_answer,
                              "numerical_nulls_are_not_physical_failures": True}
        result["arithmetic_runtime"] = {"numpy": np.__version__, "scipy": scipy.__version__, "clarabel": clarabel.__version__}
        for name, lines in combined_lines.items():
            write_owned(output, name, b"".join(lines))
        write_owned(output, "summary.json", serialize(result))
        write_owned(output, "recovery-trace.json", serialize({"solver_contract": solver_contract, "states": traces}))
        write_owned(output, "seed-known-answer.json", serialize(known_answer))
        write_owned(output, "reuse-manifest.json", serialize({"original_receipt_sha256": RECOVERY_RECEIPT_SHA,
                                                              "outputs": reused, "replaced_steel_row_indices": targets,
                                                              "original_full01_receipt_sha256": FULL01_RECEIPT_SHA,
                                                              "original_full01_preserved_outputs": original_reused,
                                                              "added_shaft_field_samples": len(added_fields)}))
        write_owned(output, "producer.py.snapshot", Path(__file__).read_bytes())
        sources = {api.key(source_path): expected for source_path, expected in sorted(pins.items())}
        write_owned(output, "sources.json", serialize(sources))
        api.authenticate(pins)
        artifact_names = set(combined_lines) | {"summary.json", "recovery-trace.json", "reuse-manifest.json",
                                               "producer.py.snapshot", "sources.json", "seed-known-answer.json"}
        artifacts = {name: digest(output / name) for name in sorted(artifact_names)}
        require(artifacts["producer.py.snapshot"] == pins[Path(__file__).resolve()]
                and artifacts["end-grain.jsonl"] == baseline_receipt["output_sha256"]["end-grain.jsonl"],
                "recovery producer snapshot or preserved N01 bytes differ")
        receipt = {"schema": "bolt_reference_completion_receipt/v2", "status": result["status"], "mode": "full",
                   "execution_scope": "RECOVER_TWO_NULL_STATES", "producer_sha256": pins[Path(__file__).resolve()],
                   "source_sha256": sources, "output_sha256": artifacts, "sources_authenticated_before_and_after": True,
                   "counts": result["counts"], "shaft_helper_calls": shaft_calls, "N09_complete": False,
                   "N01_comparisons_complete": True, "N10_comparisons_complete": completed == 504,
                   "N09_end_sources_complete": recovered_ends == 1008, "N10_pending": completed != 504,
                   "historical_producer_snapshot_binding": historical_binding,
                   "historical_producer_snapshot_bindings": [*baseline_receipt["historical_producer_snapshot_bindings"], historical_binding],
                   "recovery": result["recovery"], **FLAGS}
        write_owned(output, "receipt.json", serialize(receipt))
        return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("full", "n01", "recover"), default="recover")
    arguments = parser.parse_args()
    print(json.dumps(recover(arguments.output) if arguments.mode == "recover"
                     else build(arguments.output, mode=arguments.mode), indent=2))
