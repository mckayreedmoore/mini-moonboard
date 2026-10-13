"""Current closed timber boundaries and registered full-face source bindings.

Reuses genuine closed-solid construction and transparent-container handling.
Only cached geometry is read. Optional injectivity bounds reuse the frozen
geodesic kernel at current saved diagnostic poses. Optional full-face measure
reuses own-solid clipped area cells. No inverse, contact force, candidate
assembly or native mechanics solve is performed.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from scripts import eoere_current_components as component
from scripts import eoere_current_response as current
from scripts import eoere_current_washer_lands as intake_source
from scripts import wood_joint_current_face_pair_atlas_attempt01 as atlas
from scripts.summarize_eoere_current_response import canonical_sha

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
ATLAS = Path(atlas.__file__).resolve()
ATLAS_SHA = current.sha(ATLAS)
INTAKE = {"path": "scripts/eoere_current_washer_lands.py",
          "sha256": "d759bcab2d92bcb709f24726c324d83426483e2fd650dff80775ec0aa17b74d9"}
DISTANCE = {
    "path": "fea/generated/thin-bolted-current-contact-v1/reference-solid-distance-v1/distance.py",
    "sha256": "b0b94063be8fc595bb01ffcb08f876061e3aa9efca6cb4466e5c74fb183fdc8d",
}
CONTAINER = {
    "path": "fea/generated/thin-bolted-current-contact-v1/candidate-reference-solids-v2/bridge.py",
    "sha256": "a215a91e1ef3f1f48c36e41065bea5078be5f3d3e1bfcb9fc5e6bd263bf91098",
}
INJECTIVITY = {
    "path": "fea/generated/thin-bolted-current-contact-v1/injectivity-v1/injectivity.py",
    "sha256": "2b7843a5049bfbbf8d76da54e1bef5088c9938d8f6e83b131c06fabbbe668bf4",
}
INJECTIVITY_IMPORT_TEST = {
    "path": "fea/generated/thin-bolted-direct-contact-a12-v1/observer-isolation-v2/current-contact-v1/test_contact_geometry.py",
    "sha256": "ac59fb397b7aef8d49906cda0433df3933050e6e65fc88919b301264bb355b6b",
}
PREFLIGHT = {
    "path": "fea/generated/selected-hardware-followup-v1/engineering-closure-v1/finite-preflight-v4.json",
    "sha256": "c6c57f23c237c7adbb1b19d537ea63c11d2ecf21cd297a7a9d7551067972c5a3",
}
QUADRATURE = {
    "path": "fea/generated/thin-bolted-current-contact-v1/full-own-face-quadrature-v1/query.py",
    "sha256": "ac88cde06d78dfccc247a92f50c54ddcfcba0e97a02ca553c78ff7e550cc9783",
}


def own_ref():
    current.require(current.sha(OWN) == LOADED_SHA, "loaded current timber-domain producer changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def current_sources(cases):
    """Bind identical current geometry and contact sources across six cases."""
    current.require(len(cases) == 6 and [b["case_id"] for b, _, _ in cases] == component.SEQUENCE,
                    "six own current cases in source order required")
    first = cases[0][1]
    sources = first["source_inputs"]
    names = {r["name"] for r in sources["timber_rows"]}
    observations = {r["id"]: r for r in sources["finished_body_observations"] if r["id"] in names}
    rows = [r for r in first["reference_interaction_descriptors"] if r["kind"] == "timber_face_contact"]
    current.require(len(names) == len(observations) == 22 and len(rows) == 332
                    and len({r["id"] for r in rows}) == len(rows)
                    and len({(r["first"], r["second"]) for r in rows}) == 38,
                    "current 22 timber owners and 332 rows across 38 pairs required")
    for _, field, _ in cases:
        same = field["source_inputs"]
        contacts = [r for r in field["reference_interaction_descriptors"] if r["kind"] == "timber_face_contact"]
        current.require(same["timber_rows"] == sources["timber_rows"]
                        and same["finished_body_observations"] == sources["finished_body_observations"]
                        and contacts == rows, "own current geometry or source contact rows differ between cases")
    return observations, rows


def bind_registered_faces(geometries, planar_faces, rows):
    """Keep each side's complete own face; do not clip to an opposing body."""
    by_signature, by_feature = {}, {}
    for owner, geometry in geometries.items():
        current.require(geometry.owner_id == owner, "own closed-solid registry owner differs")
        features = {r["face_ordinal_1_based"]: r for r in geometry.face_records}
        for face in planar_faces[owner]:
            key = owner, face["signature_sha256"]
            current.require(key not in by_signature, "ambiguous own full-face signature")
            feature = features[face["face_ordinal_1_based"]]
            current.require(feature["surface_type"] == "PLANE", "registered contact face must be planar")
            by_signature[key] = face
            by_feature[key] = feature
    registered, bindings = {}, []
    for row in rows:
        own = {}
        for side in ["first", "second"]:
            owner = row[side]
            key = owner, row["source_"+side+"_face_signature_sha256"]
            current.require(key in by_signature, "registered face is absent from its own finished solid")
            face, feature = by_signature[key], by_feature[key]
            point, normal = np.asarray(row["point_xyz_mm"]), np.asarray(row["direction_xyz"])
            outward = np.asarray(face["signature"]["oriented_normal_xyz"])
            expected = -normal if side == "first" else normal
            current.require(np.linalg.norm(outward-expected) < 1e-8,
                            "registered face orientation differs from source contact side")
            feature_id = feature["feature_id"]
            if feature_id not in registered:
                registered[feature_id] = {
                    "owner_id": owner, "source_geometry": geometries[owner].source_identity,
                    "topology_sha256": geometries[owner].topology_sha256,
                    "closed_boundary_feature": feature,
                    "complete_planar_face": {k: v for k, v in face.items() if k != "_shape"},
                    "registered_opposing_owners": [], "registered_source_patch_ids": [],
                }
            record = registered[feature_id]
            record["registered_opposing_owners"].append(row["second" if side == "first" else "first"])
            record["registered_source_patch_ids"].append(row["source_patch_id"])
            own[side+"_owner"] = owner
            own[side+"_feature_id"] = feature_id
            current.require(point.shape == (3,) and np.isfinite(point).all(), "finite source contact centroid required")
        bindings.append({"source_contact_id": row["id"], "source_patch_id": row["source_patch_id"], **own})
    for record in registered.values():
        for key in ["registered_opposing_owners", "registered_source_patch_ids"]:
            record[key] = sorted(set(record[key]))
    return list(registered.values()), bindings


def timber_chart(row, source):
    """Bind the current world-storage chart without remapping source indices."""
    start, axis, stations = (np.asarray(row[k], dtype=float) for k in ["start", "axis", "stations"])
    indices = np.asarray(row["index"])
    current.require(row["source"] == source and row["start"] == source["start"]
                    and row["axis"] == source["axis"] and start.shape == axis.shape == (3,)
                    and np.isfinite(np.r_[start, axis]).all() and abs(np.linalg.norm(axis)-1.) < 1e-8
                    and stations.ndim == 1 and len(stations) >= 2 and np.isfinite(stations).all()
                    and np.all(np.diff(stations) > 0.) and stations[0] == 0.
                    and np.linalg.norm(start+stations[-1]*axis-source["end"]) < 1e-6
                    and indices.shape == (len(stations), 6) and np.isfinite(indices).all()
                    and np.array_equal(indices, indices.astype(int)) and np.all(indices >= 0)
                    and np.all(indices < 9350) and len(set(indices.ravel())) == indices.size,
                    "exact own current timber source, stations and original indices required")
    return {"kind": "timber", "reference_start_xyz_mm": start.tolist(),
            "reference_axis_xyz": axis.tolist(), "reference_stations_mm": stations.tolist(),
            "node_reference_centers_xyz_mm": (start+stations[:, None]*axis).tolist(),
            "node_dof_indices": indices.astype(int).tolist(), "storage_basis_columns_xyz": np.eye(3).tolist()}


def ambient_extent(owner, geometry, observation):
    """Use the genuine imported solid's box, keeping a source-bound margin."""
    current.require(geometry.owner_id == owner and observation["id"] == owner
                    and geometry.source_identity == {
                        "finished_raw_file_path": observation["source"]["path"],
                        "finished_raw_file_sha256": observation["source"]["sha256"]},
                    "own current solid and source required for ambient box")
    bounds = np.asarray(atlas._bounds(geometry.shape, "current timber ambient bound"), dtype=float).reshape(3, 2)
    recorded = np.asarray(observation["bounds_xyz_mm"], dtype=float)
    current.require(bounds.shape == recorded.shape == (3, 2) and np.isfinite(np.r_[bounds, recorded]).all()
                    and np.all(bounds[:, 0] < bounds[:, 1]) and np.max(abs(bounds-recorded)) < 1e-5,
                    "current imported solid bounding box differs from authenticated observation")
    return {"schema": "thin_bolted_finite_reference_domain_box/v1", "owner_id": owner,
            "bounds_xyz_mm": (bounds+[-100.000001, 100.000001]).tolist(),
            "source_identity": {**geometry.source_identity, "topology_sha256": geometry.topology_sha256,
                "genuine_cached_solid_bounds_xyz_mm": bounds.tolist(), "body_box_padding_mm": 1e-6,
                "ambient_additional_padding_mm": 100.,
                "containment_basis": "CadQuery BoundingBox of the genuine closed current cached solid",
                "box_role": "ambient map domain; exterior points do not become occupied wood"}}


def injectivity_checks(cases, geometries, observations, preflight, method, pins):
    """Evaluate every current chart and own diagnostic state on its own box."""
    current.require(preflight["case_sequence"] == component.SEQUENCE and len(preflight["cases"]) == 6,
                    "current six-case finite preflight required")
    extents = {owner: ambient_extent(owner, geometry, observations[owner]) for owner, geometry in geometries.items()}
    results, original_charts = [], None
    for (binding, field, _), prior in zip(cases, preflight["cases"], strict=True):
        bundle_ref = field["operator_bundle"]["manifest"]
        current.require(prior["case_id"] == binding["case_id"] and prior["state_id"] == binding["state_id"]
                        and prior["field"] == binding["field"] and prior["operator_manifest"] == bundle_ref
                        and prior["coordinate_ownership"]["first_order_ndof"] == 9350
                        and prior["coordinate_ownership"]["prospective_full_ndof"] == 9450
                        and pins.get(bundle_ref["path"]) == bundle_ref["sha256"],
                        "own current preflight, field and operator identities required")
        bundle = current.read(bundle_ref)
        current.require(bundle["original_operator_fingerprint_sha256"] == field["original_operator_fingerprint_sha256"]
                        and bundle["coordinate_map"]["final_ndof"] == 9350
                        and bundle["coordinate_map"]["rotation_scale"] == 1000.,
                        "own current operator and rotation storage required")
        old_q = np.asarray(field["response"]["q"], dtype=float)
        current.require(old_q.shape == (9350,) and np.isfinite(old_q).all()
                        and canonical_sha(old_q.tolist()) == field["response"]["q_canonical_sha256"],
                        "own exact saved first-order diagnostic vector required")
        q = np.r_[old_q, np.zeros(100)]
        sources = {r["name"]: r for r in field["source_inputs"]["timber_rows"]}
        timber = bundle["coordinate_map"]["timber"]
        current.require(set(timber) == set(sources) == set(extents) and len(timber) == 22,
                        "all22 current own timber sources and domains required")
        charts = {owner: timber_chart(row, sources[owner]) for owner, row in timber.items()}
        if original_charts is None:
            original_charts = charts
        current.require(charts == original_charts, "current timber charts differ between six own fields")
        owned_indices = [i for chart in charts.values() for row in chart["node_dof_indices"] for i in row]
        current.require(len(owned_indices) == len(set(owned_indices)), "current timber charts share source indices")
        bounds = []
        for owner, chart in charts.items():
            value = method.sufficient_box_bound(chart, q, owner_id=owner, extent=extents[owner], comparison_padding=1e-10)
            current.require(value["owner_id"] == owner and value["row_canonical_sha256"] == canonical_sha(chart)
                            and value["q_canonical_sha256"] == canonical_sha(q.tolist())
                            and value["extent_canonical_sha256"] == canonical_sha(extents[owner]),
                            "bound result differs from its own chart, state or genuine solid extent")
            bounds.append(value)
        results.append({"case_id": binding["case_id"], "state_id": binding["state_id"], "field": binding["field"],
                        "operator_manifest": bundle_ref, "full_diagnostic_q_canonical_sha256": canonical_sha(q.tolist()),
                        "bounds": bounds})
    all_bounds = [b for c in results for b in c["bounds"]]
    return {"method": INJECTIVITY, "current_preflight": PREFLIGHT, "reference_ndof": 9350, "full_ndof": 9450,
            "charts": original_charts, "extents": extents, "cases": results,
            "bound_count": len(all_bounds), "sufficient_count": sum(b["sufficient_global_one_to_one_criterion_met"] for b in all_bounds),
            "all132_sufficient_on_own_ambient_box": all(b["sufficient_global_one_to_one_criterion_met"] for b in all_bounds),
            "maximum_padded_sufficient_L": max(b["padded_sufficient_L"] for b in all_bounds),
            "saved_first_order_q_is_only_a_diagnostic_pose": True,
            "restored_shaft_spin_is_zero_only_for_initial_pose_not_a_finite_gauge_representative": True,
            "actual_inverse_or_target_image_membership_or_contact_query": False,
            "formal_interval_arithmetic_or_physical_demand_qualification": False}


def quadrature_sources(method):
    """Bind actual imported libraries and the mandatory plan/test file reads."""
    current.require(method.LOADED_SHA == QUADRATURE["sha256"], "loaded whole-face query source differs")
    refs = [QUADRATURE, {"path": method.PLAN_SOURCE, "sha256": method.PLAN_SOURCE_SHA},
            {"path": method.PLAN_OUTPUT, "sha256": method.PLAN_SHA},
            {"path": str(method.TEST.relative_to(current.ROOT)), "sha256": method.LOADED_TEST_SHA}]
    current.require(method.versions() == method.EXPECTED_VERSIONS, "pinned whole-face geometry tools required")
    return current.join(method.INITIAL_PINS, {r["path"]: r["sha256"] for r in refs})


def full_face_measure(geometries, faces, method, *, progress=None):
    """Measure both registered sides once each, without choosing a slave."""
    current.require(len(faces) == 51 and len({f["closed_boundary_feature"]["feature_id"] for f in faces}) == 51,
                    "all51 distinct current own full faces required")
    records = []
    for record in faces:
        owner, feature, saved = record["owner_id"], record["closed_boundary_feature"], record["complete_planar_face"]
        geometry = geometries[owner]
        current.require(geometry.owner_id == owner and geometry.source_identity == record["source_geometry"]
                        and geometry.topology_sha256 == record["topology_sha256"]
                        and feature in geometry.face_records
                        and feature["face_ordinal_1_based"] == saved["face_ordinal_1_based"],
                        "exact own current solid, topology and face required for measure")
        locator = {"face_ordinal_1_based": saved["face_ordinal_1_based"], "signature_sha256": saved["signature_sha256"]}
        native = method.select_native_face(geometry.shape, locator, saved)
        normal = np.asarray(native.normalAt().normalized().toTuple())
        current.require(np.linalg.norm(normal-np.asarray(saved["signature"]["oriented_normal_xyz"])) < 1e-8,
                        "own native full-face orientation differs")
        cells, attempts = method.own_occupied_cells(native, geometry.shape, normal, cell_size_mm=25., maximum_refinements=6)
        current.require(cells and all(c["reference_centroid_on_full_own_face"] is True
                        and c["own_inward_material_probe_occupied"] is True for c in cells),
                        "every full-face area resultant must occupy its own material")
        moments = method.moment_report(cells, native.Area(), np.asarray(native.Center().toTuple()),
                                       method.geometry.centroidal_second_moments(native))
        for i, cell in enumerate(cells):
            cell["id"] = feature["feature_id"]+f"/full-area-cell-{i:06d}"
        records.append({"owner_id": owner, "feature_id": feature["feature_id"], "source_geometry": geometry.source_identity,
            "topology_sha256": geometry.topology_sha256, "complete_source_face_locator": locator,
            "registered_opposing_owners": record["registered_opposing_owners"],
            "registered_source_patch_ids": record["registered_source_patch_ids"],
            "unsnapped_native_outward_normal_xyz": normal.tolist(), "partition_attempts": attempts,
            "cells": cells, "cell_count": len(cells), "full_reference_face_moments": moments})
        if progress is not None:
            progress({"full_faces_completed": len(records), "full_faces_total": len(faces),
                      "feature_id": feature["feature_id"], "cell_count": len(cells)})
    return {"method": QUADRATURE, "full_faces": records, "full_face_count": len(records),
            "area_cell_count": sum(r["cell_count"] for r in records),
            "full_reference_area_mm2": sum(r["full_reference_face_moments"]["area_mm2"] for r in records),
            "maximum_second_moment_relative_frobenius_error": max(r["full_reference_face_moments"]["second_moment_relative_frobenius_error"] for r in records),
            "all51_complete_own_faces_measured_once": True,
            "opposing_body_clipping_or_occupancy_cell_discard_or_slave_selection": False,
            "geometry_measure_parameters": {"initial_cell_size_mm": 25., "maximum_whole_grid_refinements": 6,
                "minimum_divisions": 2, "numerical_cell_area_cutoff_mm2": 1e-8,
                "own_face_occupancy_tolerance_mm": method.OCCUPANCY_TOL_MM,
                "own_inward_probe_depth_mm": method.PROBE_DEPTH_MM,
                "whole_face_area_absolute_tolerance_mm2": 1e-5, "whole_face_area_relative_tolerance": 1e-8,
                "whole_face_centroid_tolerance_mm": 1e-6},
            "deformed_contact_measure_or_pressure_energy_convergence_qualified": False}


def run(*, include_injectivity=False, include_measure=False, progress=None):
    own_ref()
    current.require(current.ref(intake_source.OWN) == INTAKE and intake_source.LOADED_SHA == INTAKE["sha256"],
                    "exact loaded current six-case intake required")
    cases, pins = intake_source.intake()
    observations, rows = current_sources(cases)
    reference = component.load(DISTANCE, "current_timber_closed_boundary_kernel")
    container = component.load(CONTAINER, "current_timber_strict_container_kernel")
    refs = [own_ref(), INTAKE, DISTANCE, CONTAINER, component.own_ref(),
            component.canonical_dependency(), current.ref(current.OWN), current.ref(current.ROOT/"uv.lock")]
    current.require(pins.get(str(ATLAS.relative_to(current.ROOT))) == ATLAS_SHA,
                    "loaded full-face signature source differs from authenticated intake")
    pins = current.join(pins, reference.source_pins(), {r["path"]: r["sha256"] for r in refs},
                        {r["source"]["path"]: r["source"]["sha256"] for r in observations.values()})
    preflight, method = None, None
    if include_injectivity:
        preflight = current.read(PREFLIGHT)
        current.require(current.ref(current.ROOT/INJECTIVITY_IMPORT_TEST["path"]) == INJECTIVITY_IMPORT_TEST,
                        "exact transitive geodesic import test source required")
        method = component.load(INJECTIVITY, "current_timber_injectivity_kernel")
        current.require(method.geometry.LOADED_TEST_SHA == INJECTIVITY_IMPORT_TEST["sha256"],
                        "loaded geodesic import test bytes differ")
        pins = current.join(pins, preflight["source_sha256"], method.source_pins(),
                            {r["path"]: r["sha256"] for r in [PREFLIGHT, INJECTIVITY, INJECTIVITY_IMPORT_TEST]})
    quadrature = None
    if include_measure:
        quadrature = component.load(QUADRATURE, "current_own_full_face_measure_kernel")
        pins = current.join(pins, quadrature_sources(quadrature))
    current.verify(pins)
    versions = reference.tools()
    geometries, planar_faces, records = {}, {}, []
    for owner, observation in observations.items():
        shape = reference.cq.Shape.importBrep(str(current.ROOT/observation["source"]["path"]))
        solid, wrapper = container.strict_solid(shape, reference)
        identity = {"finished_raw_file_path": observation["source"]["path"],
                    "finished_raw_file_sha256": observation["source"]["sha256"]}
        geometry = reference.ReferenceSolidDistance(solid, owner_id=owner, source_identity=identity,
                                                   linear_tolerance_mm=1e-7, tie_tolerance_mm=1e-6)
        current.require(abs(geometry.topology["volume_mm3"]-observation["volume_mm3"]) < .01,
                        "own current solid volume differs from authenticated observation")
        geometries[owner] = geometry
        planar_faces[owner] = atlas.source_face_records(owner, solid)
        records.append({"owner_id": owner, "finished_source": observation["source"],
                        "strict_container": wrapper, "frozen_constructor_topology": geometry.topology,
                        "frozen_constructor_topology_sha256": geometry.topology_sha256,
                        "all_source_boundary_faces_retained": True})
    faces, bindings = bind_registered_faces(geometries, planar_faces, rows)
    injectivity = injectivity_checks(cases, geometries, observations, preflight, method, pins) if include_injectivity else None
    measure = full_face_measure(geometries, faces, quadrature, progress=progress) if include_measure else None
    current.verify(pins)
    return {"schema": "eoere_current_closed_timber_boundaries_and_registered_full_faces/v1",
        "producer": own_ref(), "source_sha256": pins, "all_sources_unchanged": True,
        "case_sequence": component.SEQUENCE,
        "cases": [{"case_id": b["case_id"], "state_id": b["state_id"], "field": b["field"]} for b, _, _ in cases],
        "geometry_revision": "eoere-raised-kicker-screws-v1", "hardware_revision": "eoere-selected-purchase-hardware-v1",
        "extra_grid": False, "environment": versions, "owners": records,
        "registered_complete_own_faces": faces, "source_contact_face_bindings": bindings,
        "current_diagnostic_ambient_injectivity": injectivity,
        "current_complete_reference_face_measure": measure,
        "counts": {"timber_owners": len(records), "registered_contact_rows": len(bindings),
                   "registered_pairs": len({(r["first"], r["second"]) for r in rows}),
                   "registered_patches": len({r["source_patch_id"] for r in rows}),
                   "registered_full_faces": len(faces),
                   "boundary_surface_types": dict(Counter(f["surface_type"] for g in geometries.values() for f in g.face_records))},
        "all22_current_finished_solids_have_valid_closed_outward_boundary": True,
        "candidate_distance_query_deformation_quadrature_or_mechanics_run": include_measure,
        "candidate_inverse_or_contact_force_or_frame_mechanics_run": False,
        "current_saved_pose_injectivity_bound_evaluated": include_injectivity,
        "complete_contact_provider_or_response_qualified": False, "structural_acceptance": False,
        "release": current.manifest()["release"],
        "limits": ["Current source topology, optional diagnostic bounds and optional reference-face measure only; no current inverse, signed-distance response or contact actions queried.",
                   "Both complete registered face sides retained without opposing-body clipping; their reference measure does not select a slave or qualify multiple-master coverage.",
                   "New neighbors, ordinary smooth features, touch normal tubes, station kinks and each trial's ambient/inverse qualification remain separate from diagnostic sufficient bounds.",
                   "No stiffness, local fracture, finished strength, physical demand bound or complete frame acceptance follows from closed topology."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--injectivity", action="store_true", help="Also evaluate current own-box sufficient bounds at all six saved diagnostic poses")
    parser.add_argument("--full-face-measure", action="store_true", help="Query complete positive own-solid area cells on all51 current registered faces")
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run(include_injectivity=args.injectivity, include_measure=args.full_face_measure,
                         progress=lambda value: print(json.dumps(value), flush=True)))
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
