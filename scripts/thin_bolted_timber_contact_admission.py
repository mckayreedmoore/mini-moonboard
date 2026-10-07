"""Separate admission of source-bound timber-face compression extensions.

The frozen finite audit supplies all unchanged map/load/current-law/132-body
checks. This module independently authenticates the new geometry proof and
adds its exact contact census. No CAD, K, response solve or capacity occurs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from scripts import thin_bolted_finite_state_audit as original

ROOT, PACKET = original.ROOT, original.PACKET
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_SHA256 = original.support.digest(Path(__file__))
LOADED_PRODUCER_SHA256 = LOADED_SHA256
ORIGINAL_GATE = "scripts/thin_bolted_finite_state_audit.py"
ORIGINAL_GATE_SHA256 = "532c093c5426e3d4f78384ea0e4aff63353dce8b63ea8bdfe6eb17321bd196b1"
PROOF = PACKET / "timber-face-contact-geometry-v4.json"
PROOF_SCHEMA = "thin_bolted_timber_face_contact_geometry/v1"
PROOF_SHA256 = "be88aeb6754bc03e8afd523f5127f74b93b90bd00e8c3ceaa910e70aab3f125a"
METHOD = "scripts/thin_bolted_timber_face_contact.py"
METHOD_SHA256 = "9558a036f9f8b06fb6a1a1a711419aaa961f655e8f7fb02deb7808e8ade4ed8c"
METHOD_RECEIPT = PACKET / "timber-face-contact-method-v4.json"
METHOD_RECEIPT_SHA256 = "529841caf86c039d6e2672908a878f1be40f72078d0d2710779bace9a0b86c42"
DRIVER = "scripts/run_thin_bolted_timber_contact_frame.py"
DRIVER_SHA256 = "3ff26fdbe0d76048c5088ac086d8b9c1a0d8b01171d3c389a1f9f946fc1ffa82"
DRIVER_RECEIPT = PACKET / "timber-contact-frame-orchestration-method-v4.json"
DRIVER_RECEIPT_SHA256 = "f0e48cce4d2cbb629234538141d2bb57705e44a8b6f68056bba2b089b5ca9d02"
BASIS = "source-bound-finished-paired-wood-compression-v1"
SCHEMA = "thin_bolted_independent_timber_contact_admission/v1"
SUCCESS = "independent_finite_timber_contact_support_load_and_equilibrium_checks_pass"
PAIR_HOSTS = {
    frozenset(("base_side_left", "lumber_leg_left")),
    frozenset(("base_side_right", "lumber_leg_right")),
    frozenset(("base_post_outer_left", "base_floor_left")),
    frozenset(("base_post_outer_right", "base_floor_right")),
    frozenset(("base_floor_left", "lumber_leg_left")),
    frozenset(("base_floor_right", "lumber_leg_right")),
}
HOSTS = set().union(*PAIR_HOSTS)


def source_pins():
    # This review receipt is audit-only; the frozen physical driver binds its
    # own source and need not acquire a circular dependency on this audit.
    original.require(original.support.digest(DRIVER_RECEIPT) == DRIVER_RECEIPT_SHA256,
                     "timber-contact orchestration review receipt changed")
    receipt = json.loads(DRIVER_RECEIPT.read_bytes())
    pins = merge_pins({OWN: LOADED_SHA256, ORIGINAL_GATE: ORIGINAL_GATE_SHA256, DRIVER: DRIVER_SHA256,
                       str(DRIVER_RECEIPT.relative_to(ROOT)): DRIVER_RECEIPT_SHA256}, receipt["source_sha256"])
    original.require(all(original.support.digest(ROOT / path) == value for path, value in pins.items()),
                     "timber-contact admission or frozen base gate changed")
    return pins


def merge_pins(*groups):
    """A repeated dependency may agree, never replace another frozen digest."""
    result = {}
    for group in groups:
        for path, value in group.items():
            original.require(path not in result or result[path] == value, "conflicting timber admission source pin: " + path)
            result[path] = value
    return result


def member_pair(row):
    first, second = row["first"], row["second"]
    original.require(isinstance(first, str) and isinstance(second, str) and first != second,
                     "two distinct timber contact hosts required")
    pair = frozenset((first, second))
    original.require(pair in PAIR_HOSTS, "foreign retained timber interface")
    return pair


def retained_pair_inventory(layout):
    result = defaultdict(list)
    for axis in layout["installed_axes"]:
        if axis.get("source") != "original_starting_frame_axis":
            continue
        original.require(len(axis["receivers"]) == 2 and not axis["attachments"],
                         "retained frame shaft must have two timber receivers")
        result[frozenset(axis["receivers"])].append(axis["id"])
    original.require(set(result) == PAIR_HOSTS and all(len(v) == 2 and len(set(v)) == 2 for v in result.values()),
                     "six retained timber pairs with two distinct shafts each required")
    return result


def verify_patch_inventory(proof, cache, layout):
    """JSON conservation/census checks; geometric truth remains source-bound."""
    original.require(proof.get("schema") == PROOF_SCHEMA
                     and proof.get("candidate") == "compact-floor-flush-thin-bolted-development"
                     and proof.get("layout_report_sha256") == original.arithmetic.PINS["mixed-offset-rows-shallow-wires-v4.json"]
                     and proof.get("geometry_cache_sha256") == original.arithmetic.PINS["native-geometry-v4.json"],
                     "new source-bound finished timber contact proof required")
    axes = retained_pair_inventory(layout)
    pairs = proof["pairs"]
    indexed_pairs = {member_pair(row): row for row in pairs}
    original.require(len(pairs) == len(indexed_pairs) == 6 and set(indexed_pairs) == PAIR_HOSTS,
                     "all six retained pair query dispositions required")
    cache_parts = original.unique(cache["parts"])
    sources = original.unique(proof["sources"], "member")
    original.require(set(sources) == HOSTS, "all eight finished source timbers required")
    for member, source in sources.items():
        cached = cache_parts[member]
        original.require(cached["kind"] == "timber" and source == {**cached, "member": member},
                         "finished contact source differs from complete cached timber record")
    method = proof["method"]
    cell_size = original.support.finite_scalar(method["cell_size_mm"])
    occupancy_tol = original.support.finite_scalar(method["occupancy_tolerance_mm"])
    original.require(cell_size > 0. and 0. < occupancy_tol <= original.POINT_TOL
                     and method["minimum_divisions"] == 2 and method["recreated_geometry"] is False,
                     "exact clipped reference contact query/grid required")
    patches = original.unique(proof["patches"])
    original.require(patches, "missing wood-face compression patches")
    seen_regions = set()
    patch_ids_by_pair = defaultdict(list)
    all_cell_ids = set()
    cell_count = 0
    for identity, patch in patches.items():
        pair = member_pair(patch)
        patch_ids_by_pair[pair].append(identity)
        normal = original.array(patch["normal_from_second_to_first_xyz"], (3,))
        original.require(abs(np.linalg.norm(normal) - 1.) <= 1e-8, "unit opposed timber-face normal required")
        area = original.support.finite_scalar(patch["area_mm2"])
        centroid = original.array(patch["centroid_xyz_mm"], (3,))
        original.require(area > 0., "positive trimmed contact patch area required")
        first_normal = original.array(patch["first_outward_normal_xyz"], (3,))
        original.close(first_normal, -normal, 1e-8, "finished source timber face normals are not opposed")
        original.require(abs(original.support.finite_scalar(patch["opposed_normal_dot"])+1.) <= 1e-8
                         and 0. <= original.support.finite_scalar(patch["coplanar_offset_mm"]) <= original.POINT_TOL,
                         "opposed coplanar finished timber faces required")
        for host, facekey, outward in ((patch["first"], "source_first_face", first_normal),
                                      (patch["second"], "source_second_face", normal)):
            face = patch[facekey]
            signature = face["signature"]
            ordinal = face["face_ordinal_1_based"]
            original.require(isinstance(ordinal, int) and not isinstance(ordinal, bool) and ordinal > 0
                             and signature["surface_type"] == "PLANE"
                             and original.canonical_sha(signature) == face["signature_sha256"]
                             and face["face_id"] == f"{host}/step-face-{ordinal:04d}-{face['signature_sha256'][:16]}",
                             "source planar face identity/signature differs")
            original.close(signature["oriented_normal_xyz"], outward, 1e-8, "source face outward normal differs")
            original.require(original.support.finite_scalar(signature["area_mm2"]) >= area-1e-5,
                             "trimmed contact region exceeds source face area")
        region = patch["trimmed_region_geometry"]
        region_sha = original.canonical_sha(region)
        original.require(region_sha == patch["trimmed_region_signature_sha256"] and region["surface_type"] == "PLANE",
                         "trimmed planar contact signature differs")
        original.require(abs(original.support.finite_scalar(region["area_mm2"])-area) <= 1e-5,
                         "trimmed contact area differs from geometry signature")
        original.close(region["center_xyz_mm"], centroid, original.POINT_TOL, "trimmed contact centroid differs")
        key = (pair, region_sha)
        original.require(key not in seen_regions, "duplicate trimmed patch assigned per retained shaft")
        seen_regions.add(key)
        level = patch["occupancy_refinement_levels"]
        effective = original.support.finite_scalar(patch["effective_cell_size_mm"])
        original.require(isinstance(level, int) and not isinstance(level, bool) and 0 <= level <= 6
                         and effective == cell_size / 2**level, "contact occupancy refinement/grid differs")
        cells = original.unique(patch["cells"])
        original.require(cells, "positive patch must retain contact cells")
        total = 0.
        first_moment = np.zeros(3)
        for cell_id, cell in cells.items():
            original.require(isinstance(cell_id, str) and cell_id and cell_id.startswith(identity+"/cell-")
                             and cell_id not in all_cell_ids, "duplicate or foreign physical timber contact cell")
            all_cell_ids.add(cell_id)
            weight = original.support.finite_scalar(cell["area_mm2"])
            point = original.array(cell["point_xyz_mm"], (3,))
            original.require(weight > 0., "positive clipped cell area required")
            original.require(cell.get("reference_centroid_on_trimmed_patch") is True
                             and cell.get("both_inward_material_probes_occupied") is True,
                             "source cell centroid needs both actual trimmed reference faces")
            distance = original.support.finite_scalar(cell["reference_centroid_patch_distance_mm"])
            original.require(0. <= distance <= occupancy_tol, "source cell centroid is outside trimmed reference patch")
            original.require(abs(normal @ (point-centroid)) <= original.POINT_TOL,
                             "contact cell leaves the source patch plane")
            total += weight
            first_moment += weight * point
        original.require(abs(total-area) <= max(1e-5, 1e-8*area), "contact cell sum loses trimmed patch area")
        original.close(first_moment / total, centroid, 1e-6, "contact cells lose trimmed patch first moment")
        sampled = sum((cell["area_mm2"] * np.outer(original.array(cell["point_xyz_mm"])-centroid,
                        original.array(cell["point_xyz_mm"])-centroid) for cell in cells.values()), np.zeros((3, 3)))
        exact_second = original.array(patch["exact_centroidal_second_moment_matrix_xyz_mm4"], (3, 3))
        original.close(sampled, patch["sampled_centroidal_second_moment_matrix_xyz_mm4"], 1e-5,
                       "saved contact centroid second moment differs")
        original.close(exact_second, exact_second.T, 1e-5, "source contact second moment is not symmetric")
        original.require(np.linalg.norm(exact_second) > 0., "nonzero source contact second moment required")
        error = float(np.linalg.norm(sampled-exact_second)/np.linalg.norm(exact_second))
        original.require(abs(error-original.support.finite_scalar(patch["second_moment_relative_frobenius_error"])) <= 1e-10,
                         "source contact quadrature error differs")
        cell_count += len(cells)
    original.require(set(patch_ids_by_pair) == PAIR_HOSTS, "one retained timber pair has no compression load path")
    for pair, row in indexed_pairs.items():
        ids = patch_ids_by_pair[pair]
        original.require(set(row["retained_axis_ids"]) == set(axes[pair]) and len(row["retained_axis_ids"]) == 2,
                         "contact pair binds wrong retained frame shafts")
        original.require(len(row["patch_ids"]) == len(set(row["patch_ids"]))
                         and set(row["patch_ids"]) == set(ids) and row["patch_count"] == len(ids),
                         "pair query and physical patch census disagree")
        expected_area = sum(patches[identity]["area_mm2"] for identity in ids)
        original.require(abs(original.support.finite_scalar(row["area_mm2"])-expected_area) <= max(1e-5, 1e-8*expected_area),
                         "pair query loses contact patch area")
    original.require(proof["counts"] == {"finished_timbers": 8, "member_pairs": 6, "retained_axes": 12,
                     "patches": len(patches), "cells": cell_count}, "contact proof header census differs")
    return {"retained_pair_count": 6, "source_timber_count": 8, "patch_count": len(patches),
            "contact_cell_count": cell_count,
            "retained_axis_ids_by_pair": [{"members": sorted(pair), "axis_ids": sorted(ids)} for pair, ids in axes.items()],
            "geometry_is_authenticated_source_query_not_independent_CAD_reconstruction": True,
            "current_projected_footprint_pressure_or_contact_capacity_established": False}


def contact_parameters(field, proof):
    params = field["parameters"]
    original.require(params.get("timber_face_contact_basis") == BASIS, "new timber contact basis required")
    bedding = original.support.finite_scalar(params["timber_face_contact_bedding_n_mm3"])
    scenario = params["timber_face_contact_scenario_id"]
    original.require(bedding > 0. and isinstance(scenario, str) and scenario, "explicit finite positive bedding scenario required")
    original.require(params.get("timber_face_contact_geometry_sha256") == PROOF_SHA256
                     and params.get("timber_face_contact_producer_sha256") == METHOD_SHA256
                     and params.get("timber_face_contact_method_receipt_sha256") == METHOD_RECEIPT_SHA256,
                     "source-bound timber contact proof/method scenario required")
    original.require(np.isfinite(params["timber_face_contact_cell_mm"]) and params["timber_face_contact_cell_mm"] > 0.
                     and params["timber_face_contact_cell_mm"] == proof["method"]["cell_size_mm"],
                     "source-bound positive timber contact grid required")
    return bedding, scenario


def expected_contact_descriptors(proof, bedding, scenario):
    """Independent recreation; never call the contact producer’s descriptor API."""
    result = {}
    for patch in proof["patches"]:
        first, second, normal = patch["first"], patch["second"], patch["normal_from_second_to_first_xyz"]
        for cell in patch["cells"]:
            identity = cell["id"]
            original.require(identity not in result, "duplicate expected timber contact identity")
            result[identity] = {"id": identity, "kind": "timber_face_contact", "first": first, "second": second,
                "reference_first_point_xyz_mm": cell["point_xyz_mm"], "reference_second_point_xyz_mm": cell["point_xyz_mm"],
                "reference_director_xyz": normal, "director_owner": second,
                "first_port_kind": "point", "first_flange": None, "second_flange": None, "director_flange": None,
                "axial_stiffness_n_mm": bedding * cell["area_mm2"], "lateral_stiffness_n_mm": 0., "radial_gap_mm": 0.,
                "axial_tension_only": True, "axial_sign": -1., "reference_axial_projection_mm": 0.,
                "source_descriptor": {"patch_id": patch["id"], "cell_id": cell["id"],
                    "patch_area_mm2": patch["area_mm2"], "cell_area_mm2": cell["area_mm2"],
                    "patch_centroid_xyz_mm": patch["centroid_xyz_mm"],
                    "normal_from_second_to_first_xyz": normal, "bedding_n_mm3": bedding, "scenario_id": scenario,
                    "geometry_proof_sha256": PROOF_SHA256,
                    "trimmed_region_signature_sha256": patch["trimmed_region_signature_sha256"],
                    "source_first_face": {k: v for k, v in patch["source_first_face"].items() if k != "signature"},
                    "source_second_face": {k: v for k, v in patch["source_second_face"].items() if k != "signature"},
                    "effective_cell_size_mm": patch["effective_cell_size_mm"],
                    "reference_centroid_on_trimmed_patch": cell["reference_centroid_on_trimmed_patch"],
                    "both_inward_material_probes_occupied": cell["both_inward_material_probes_occupied"],
                    "reference_centroid_patch_distance_mm": cell["reference_centroid_patch_distance_mm"]}}
    return result


def verify_contact_source_aliases(field, proof):
    """Authenticate compact aliases; complete geometry is bound once by SHA."""
    bedding, scenario = contact_parameters(field, proof)
    expected = expected_contact_descriptors(proof, bedding, scenario)
    for table in ("reference_interaction_descriptors", "finite_interaction_actions"):
        rows = original.unique(field[table])
        contacts = {key: row for key, row in rows.items() if row["kind"] == "timber_face_contact"}
        original.require(set(contacts) == set(expected), "complete additional timber contact source census required")
        for identity, descriptor in expected.items():
            source = contacts[identity]["source_descriptor"]
            original.require(original.canonical_sha(source) == original.canonical_sha(descriptor["source_descriptor"]),
                             "compact timber patch/cell source aliases differ")


def read_proof(field, cache, layout):
    original.require("UNISSUED" not in (PROOF_SHA256, METHOD_SHA256, METHOD_RECEIPT_SHA256),
                     "wood contact proof and method must be issued before admission")
    payload = PROOF.read_bytes()
    original.require(hashlib.sha256(payload).hexdigest() == PROOF_SHA256, "issued timber contact geometry proof changed")
    proof = json.loads(payload)
    explicit_pins = {str(PROOF.relative_to(ROOT)): PROOF_SHA256, METHOD: METHOD_SHA256,
                     str(METHOD_RECEIPT.relative_to(ROOT)): METHOD_RECEIPT_SHA256}
    method_receipt = json.loads(METHOD_RECEIPT.read_bytes())
    pins = merge_pins(explicit_pins, proof["source_sha256"], method_receipt["source_sha256"])
    original.require(pins[METHOD] == METHOD_SHA256, "method receipt binds a foreign wood contact producer")
    for path, value in pins.items():
        original.require(field["source_sha256"].get(path) == value and original.support.digest(ROOT / path) == value,
                         "finite contact state omits or changes an exact proof/method source")
    inventory = verify_patch_inventory(proof, cache, layout)
    bedding, scenario = contact_parameters(field, proof)
    return proof, inventory, bedding, scenario, pins


def verify_orchestration(field):
    original.require(field["source_sha256"].get(DRIVER) == DRIVER_SHA256,
                     "corrected finite execution must bind the new timber-contact driver")
    command = field.get("execution", {}).get("command")
    original.require(isinstance(command, list) and len(command) >= 3
                     and all(isinstance(part, str) for part in command)
                     and command[1:3] == ["-m", "scripts.run_thin_bolted_timber_contact_frame"],
                     "new timber-contact execution module required")
    original.require(field.get("timber_contact_geometry_sha256") == PROOF_SHA256,
                     "exported contact geometry identity differs")


def audit_timber_contact_state(path_or_dict):
    """Read one payload, reuse frozen checks and admit the exact extended paths."""
    pins = source_pins()
    path = None if isinstance(path_or_dict, (bytes, dict)) else Path(path_or_dict)
    payload = path.read_bytes() if path else path_or_dict if isinstance(path_or_dict, bytes) else None
    field = json.loads(payload) if payload is not None else path_or_dict
    q = original.verify_header(field)
    verify_orchestration(field)
    contact, cache, unit, layout, takeoff, integrated, base_pins = original.source_receipt(field)
    pins = merge_pins(pins, base_pins)
    proof, geometry, bedding, scenario, additional_pins = read_proof(field, cache, layout)
    pins = merge_pins(pins, additional_pins)
    original.verify_floor_proofs(field, contact, cache)
    bodies, loads, _ = original.common.expected_common_loads(field, cache, takeoff, integrated)
    original.common.verify_load_table(field["body_reference_applied_loads"], loads)
    names = [r["id"] if isinstance(r, dict) else r for r in field["body_identities"]]
    original.require(len(names) == len(set(names)) == 132 and set(names) == set(bodies), "132 unchanged physical body identities required")
    shafts = original.common_method.shaft_inputs(layout, unit, cache)
    panels, datums = original.verify_maps(field, q, layout, shafts, integrated)
    expected = original.descriptor_expected(field, contact, layout, shafts, panels, datums)
    additional = expected_contact_descriptors(proof, bedding, scenario)
    original.require(additional and not (set(expected) & set(additional)), "new timber compression cells may not replace existing physical paths")
    original.require(set(expected) != {row["id"] for row in field["finite_interaction_actions"]},
                     "old finite census must not masquerade as corrected timber contact")
    expected.update(additional)
    verify_contact_source_aliases(field, proof)
    action_receipt = original.verify_current_actions(field, q, expected)
    original.require(action_receipt["counts"].get("timber_face_contact") == geometry["contact_cell_count"],
                     "full additional zero/loaded timber contact census required")
    load_receipt = original.verify_current_loads(field, q, loads, panels, integrated)
    equilibrium = original.verify_equilibrium(field, bodies)
    original.require(path is None or path.read_bytes() == payload, "timber contact field changed during admission")
    for name, value in pins.items():
        original.require(original.support.digest(ROOT / name) == value, "timber admission source changed while checking: " + name)
    return {"schema": SCHEMA, SUCCESS: True,
            **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
            **original.field_hashes(field, payload), "source_sha256": pins,
            "timber_contact_geometry": geometry, "current_action_replay": action_receipt,
            "source_current_load_replay": load_receipt, "equilibrium": equilibrium,
            "old_exact_interaction_census_would_reject_extended_field": True,
            "unchanged_body_mass_shaft_screw_floor_panel_correction_sources_reused": True,
            "CAD_K_response_or_native_execution": False,
            "physical_current_contact_footprint_pressure_strength_or_stiffness_bounds_established": False,
            "release": {key: False for key in field["release"]}}


def method_report():
    """Authenticate issued extension inputs without admitting any force field."""
    proof = json.loads(PROOF.read_bytes())
    method = json.loads(METHOD_RECEIPT.read_bytes())
    explicit = {str(PROOF.relative_to(ROOT)): PROOF_SHA256, METHOD: METHOD_SHA256,
                str(METHOD_RECEIPT.relative_to(ROOT)): METHOD_RECEIPT_SHA256}
    graph = merge_pins(explicit, proof["source_sha256"], method["source_sha256"])
    params = {"timber_face_contact_basis": BASIS, "timber_face_contact_geometry_sha256": PROOF_SHA256,
              "timber_face_contact_producer_sha256": METHOD_SHA256,
              "timber_face_contact_method_receipt_sha256": METHOD_RECEIPT_SHA256,
              "timber_face_contact_bedding_n_mm3": 1., "timber_face_contact_scenario_id": "paired-wood-bedding-declared-v1",
              "timber_face_contact_cell_mm": proof["method"]["cell_size_mm"]}
    cache = json.loads((PACKET/"native-geometry-v4.json").read_bytes())
    layout = json.loads((PACKET/"mixed-offset-rows-shallow-wires-v4.json").read_bytes())
    _, geometry, bedding, scenario, pins = read_proof({"parameters": params, "source_sha256": graph}, cache, layout)
    pins = merge_pins(source_pins(), pins)
    for test in ("tests/test_thin_bolted_timber_contact_admission.py", "tests/test_thin_bolted_finite_frame.py",
                 "tests/test_thin_bolted_finite_mechanics.py"):
        pins[test] = original.support.digest(ROOT/test)
    descriptors = expected_contact_descriptors(proof, bedding, scenario)
    original.require(len(descriptors) == geometry["contact_cell_count"], "independent descriptor mapping lost source cells")
    return {"schema": "thin_bolted_timber_contact_admission_method/v1", "source_sha256": pins,
            "admission_schema": SCHEMA, "admission_success_key": SUCCESS, "geometry": geometry,
            "descriptor_count": len(descriptors), "declared_method_reference_parameters": params,
            "validation_command": [".venv/bin/python", "-m", "pytest", "-q", "tests/test_thin_bolted_timber_contact_admission.py"],
            "independent_review": "Existing access/takeoff worker; exact census, source graph and unchanged current-action/load/equilibrium reuse",
            "candidate_CAD_K_response_or_force_field_prepared_admitted_or_solved": False,
            "limits": ["Numerical admission requires original full-gradient and 132 current-body/global wrench closure; solver convergence alone is insufficient.",
                       "Fixed occupied reference cells with declared bedding do not establish current overlapping patches, physical pressure, stiffness bounds or complete joint resistance.",
                       "Original exact interaction census rejects extended force fields; only this distinct admission may authenticate the added cells."],
            "release": {key: False for key in proof["release"]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("field", type=Path, nargs="?")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--method", action="store_true", help="write an extension-only method receipt; no field admission")
    args = parser.parse_args()
    original.require(not args.out.exists(), "preserve issued receipt; choose a new output path")
    original.require(args.method == (args.field is None), "choose either a field or --method")
    report = method_report() if args.method else audit_timber_contact_state(args.field)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
