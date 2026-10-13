"""Current registered timber contact pairs and conservative neighbor screening.

Reuses the frozen complete faces, area cells and own geodesic bounds. All
timber pairs are screened with containing deformed boxes at saved diagnostic
poses. Box overlap is unresolved, never a contact or an exclusion certificate.
No distance query, inverse, contact potential or frame solve is performed.
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations, product
from pathlib import Path

import numpy as np

from scripts import eoere_current_components as component
from scripts import eoere_current_response as current
from scripts import eoere_current_washer_lands as intake_source
from scripts.summarize_eoere_current_response import canonical_sha

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
RAW = "fea/generated/selected-hardware-followup-v1/engineering-closure-v1/"
MEASURE = {"path": RAW+"current-timber-fullfaces-v5.json",
           "sha256": "6dce08e63a1d1b33c223657cd652bbfd2e938aa4a51f6eb8527ba7661cda4145"}
DOMAINS = {"path": RAW+"current-timber-domains-v3.json",
           "sha256": "12d3cc0b8c0969942aaedc0609a10379ae4b02bcba15f8cb88802dc7ba0d4302"}
DOMAIN_PRODUCER = "scripts/eoere_current_timber_domains.py"
DOMAIN_SNAPSHOT = RAW+"source-at-current-timber-domains-v3/eoere_current_timber_domains.py"
INTAKE = {"path": "scripts/eoere_current_washer_lands.py",
          "sha256": "d759bcab2d92bcb709f24726c324d83426483e2fd650dff80775ec0aa17b74d9"}


def own_ref():
    current.require(current.sha(OWN) == LOADED_SHA, "loaded current contact-scope producer changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def resolved_domain_pins(record):
    """Resolve the one preserved producer, keeping its original receipt intact."""
    pins = dict(record["source_sha256"])
    old = record["producer"]
    current.require(old["path"] == DOMAIN_PRODUCER and pins[old["path"]] == old["sha256"],
                    "exact original domain producer receipt required")
    snapshot = {"path": DOMAIN_SNAPSHOT, "sha256": old["sha256"]}
    current.require(current.ref(current.ROOT/DOMAIN_SNAPSHOT) == snapshot,
                    "exact preserved domain producer bytes required")
    del pins[old["path"]]
    pins = current.join(pins, {snapshot["path"]: snapshot["sha256"]})
    return pins, {"record": DOMAINS, "original": old, "preserved_source": snapshot}


def registered_plan(faces, bindings, measure):
    """One whole selected face per registered pair; retain every pair's cells."""
    by_id = {f["closed_boundary_feature"]["feature_id"]: f for f in faces}
    measured = {f["feature_id"]: f for f in measure["full_faces"]}
    current.require(len(by_id) == len(faces) == len(measured) == len(measure["full_faces"])
                    and by_id.keys() == measured.keys(), "complete unique own face measures required")
    for key, face in by_id.items():
        saved = measured[key]
        current.require(all(saved[k] == face[k] for k in ["owner_id", "topology_sha256"])
                        and saved["source_geometry"] == face["source_geometry"]
                        and saved["complete_source_face_locator"] == {
                            "face_ordinal_1_based": face["complete_planar_face"]["face_ordinal_1_based"],
                            "signature_sha256": face["complete_planar_face"]["signature_sha256"]}
                        and saved["cell_count"] == len(saved["cells"]) > 0,
                        "exact own topology, full face and nonempty cell set required")
    pairs, row_ids = {}, set()
    for binding in bindings:
        current.require(binding["source_contact_id"] not in row_ids, "duplicate source contact row")
        row_ids.add(binding["source_contact_id"])
        keys = tuple(sorted(binding[side+"_feature_id"] for side in ["first", "second"]))
        current.require(len(set(keys)) == 2 and all(k in by_id for k in keys), "two own bound faces required")
        for side in ["first", "second"]:
            current.require(by_id[binding[side+"_feature_id"]]["owner_id"] == binding[side+"_owner"],
                            "bound face differs from its source owner")
        if keys not in pairs:
            slave = min(keys, key=lambda k: (by_id[k]["complete_planar_face"]["signature"]["area_mm2"], k))
            master = keys[1] if slave == keys[0] else keys[0]
            current.require(by_id[slave]["owner_id"] != by_id[master]["owner_id"], "distinct timber owners required")
            pairs[keys] = {"id": "registered-timber-pair/"+canonical_sha(keys)[:24],
                "slave_owner": by_id[slave]["owner_id"], "slave_feature_id": slave,
                "master_owner": by_id[master]["owner_id"], "master_source_feature_id": master,
                "source_patch_ids": set(), "source_contact_ids": [],
                "complete_selected_face_cell_ids": [c["id"] for c in measured[slave]["cells"]],
                "complete_selected_face_area_mm2": measured[slave]["full_reference_face_moments"]["area_mm2"]}
        pairs[keys]["source_patch_ids"].add(binding["source_patch_id"])
        pairs[keys]["source_contact_ids"].append(binding["source_contact_id"])
    records = []
    for row in pairs.values():
        row["source_patch_ids"] = sorted(row["source_patch_ids"])
        row["source_contact_ids"].sort()
        records.append(row)
    groups = {}
    for row in records:
        groups.setdefault(row["slave_feature_id"], []).append(row["master_owner"])
    return {"selection_rule": "smaller complete own source face; feature ID breaks exact area ties",
            "pairs": records, "pair_count": len(records), "selected_full_face_count": len(groups),
            "pair_cell_count": sum(len(r["complete_selected_face_cell_ids"]) for r in records),
            "multiple_master_faces": {k: sorted(set(v)) for k, v in groups.items() if len(set(v)) > 1},
            "all_source_contact_ids": sorted(row_ids), "no_opposing_footprint_cell_clipping": True,
            "multiple_masters_collapsed_or_two_sided_pair_force_duplicated": False,
            "pair_cells_are_force_model_or_new_feature_coverage": False}


def containing_deformed_box(chart, q, extent, bound, *, numerical_padding_mm=1e-6):
    """Contain phi(X) using nodal translations and geodesic rotation bounds.

    For interior stations phi(X)-X = u(t)+(R(t)-I)(X-C(t)). The arm is
    perpendicular to the straight chart axis. Its norm is bounded on all box
    corners. Translation lies in the nodal convex hull and ||R-I|| is bounded
    by the frozen segment angle. Endpoint arms additionally include overhang.
    This is a real-arithmetic enclosure with numerical padding, not intervals.
    """
    q = np.asarray(q, dtype=float)
    current.require(q.ndim == 1 and np.isfinite(q).all()
                    and np.isfinite(numerical_padding_mm) and numerical_padding_mm >= 0., "finite state and padding required")
    owner = extent["owner_id"]
    current.require(bound["owner_id"] == owner and bound["row_canonical_sha256"] == canonical_sha(chart)
                    and bound["q_canonical_sha256"] == canonical_sha(q.tolist())
                    and bound["extent_canonical_sha256"] == canonical_sha(extent)
                    and bound["sufficient_global_one_to_one_criterion_met"] is True,
                    "own source-bound sufficient chart/state/domain record required")
    declared_indices = np.asarray(chart["node_dof_indices"])
    indices = np.asarray(chart["node_dof_indices"], dtype=int)
    start, axis = np.asarray(chart["reference_start_xyz_mm"]), np.asarray(chart["reference_axis_xyz"])
    stations = np.asarray(chart["reference_stations_mm"])
    basis = np.asarray(chart["storage_basis_columns_xyz"])
    centers = np.asarray(chart["node_reference_centers_xyz_mm"])
    current.require(chart["kind"] == "timber" and start.shape == axis.shape == (3,)
                    and np.isfinite(np.r_[start, axis]).all() and abs(np.linalg.norm(axis)-1.) < 1e-8
                    and stations.ndim == 1 and len(stations) >= 2 and np.isfinite(stations).all()
                    and np.all(np.diff(stations) > 0.) and stations[0] == 0.
                    and indices.shape == (len(stations), 6) and np.array_equal(declared_indices, indices)
                    and len(set(indices.ravel())) == indices.size
                    and centers.shape == (len(stations), 3)
                    and np.max(abs(centers-start-stations[:, None]*axis)) < 1e-7
                    and basis.shape == (3, 3) and np.linalg.norm(basis.T@basis-np.eye(3)) < 1e-8
                    and abs(np.linalg.det(basis)-1.) < 1e-8 and np.all(indices >= 0) and np.all(indices < len(q)),
                    "proper finite straight chart required")
    source = extent["source_identity"]
    box = np.asarray(source["genuine_cached_solid_bounds_xyz_mm"], dtype=float)
    ambient = np.asarray(extent["bounds_xyz_mm"], dtype=float)
    current.require(box.shape == ambient.shape == (3, 2) and np.isfinite(box).all()
                    and np.all(box[:, 0] < box[:, 1]) and np.all(ambient[:, 0] <= box[:, 0])
                    and np.all(ambient[:, 1] >= box[:, 1]), "own finished-solid box inside declared ambient box required")
    corners = np.asarray(list(product(*box.tolist())))
    axial = (corners-start)@axis
    arms = corners-start-axial[:, None]*axis
    radial = float(np.linalg.norm(arms, axis=1).max())
    segments = bound["segments"]
    current.require(len(segments) == len(stations)-1 and [r["segment_index"] for r in segments] == list(range(len(stations)-1))
                    and all(r["station_interval_mm"] == stations[i:i+2].tolist() for i, r in enumerate(segments)),
                    "every source segment in order required")
    angles = np.asarray([r["absolute_geodesic_angle_upper_rad"] for r in segments])
    current.require(np.isfinite(angles).all() and np.all((angles >= 0.) & (angles <= np.pi)), "valid source rotation bounds required")
    rotation_radius = float((2.*np.sin(angles/2.)*radial).max())
    endpoints = bound["rigid_endpoint_extensions"]
    current.require(len(endpoints) == 2 and [r["endpoint"] for r in endpoints] == ["first", "last"]
                    and [r["station_mm"] for r in endpoints] == [stations[0], stations[-1]], "both own endpoint extensions required")
    endpoint_rows = []
    for i, endpoint in enumerate(endpoints):
        overhang = max(0., -float(axial.min())) if i == 0 else max(0., float(axial.max()-stations[-1]))
        factor = endpoint["rigid_endpoint_extension_L"]
        current.require(np.isfinite(factor) and 0. <= factor <= 2., "valid endpoint rotation bound required")
        radius = float(np.hypot(radial, overhang))
        if overhang > 0.:
            rotation_radius = max(rotation_radius, factor*radius)
        endpoint_rows.append({"endpoint": endpoint["endpoint"], "box_axial_overhang_mm": overhang,
                              "arm_radius_bound_mm": radius, "rotation_factor_bound": factor})
    translation = q[indices[:, :3]]@basis.T
    padding = rotation_radius+numerical_padding_mm
    result = box+np.column_stack((translation.min(axis=0)-padding, translation.max(axis=0)+padding))
    return {"owner_id": owner, "bounds_xyz_mm": result.tolist(), "reference_solid_box_xyz_mm": box.tolist(),
            "source_geometry": {k: source[k] for k in ["finished_raw_file_path", "finished_raw_file_sha256", "topology_sha256"]},
            "q_canonical_sha256": bound["q_canonical_sha256"], "chart_canonical_sha256": bound["row_canonical_sha256"],
            "reference_radial_arm_radius_bound_mm": radial, "rotation_displacement_norm_bound_mm": rotation_radius,
            "translation_component_min_mm": translation.min(axis=0).tolist(), "translation_component_max_mm": translation.max(axis=0).tolist(),
            "endpoint_extensions": endpoint_rows, "numerical_padding_mm": numerical_padding_mm,
            "formal_interval_arithmetic": False}


def screen_pairs(boxes, registered):
    """A strictly positive separating axis excludes the whole solid pair."""
    current.require(all(k == row["owner_id"] for k, row in boxes.items()), "own deformed-box registry required")
    pairs = []
    for first, second in combinations(sorted(boxes), 2):
        a, b = (np.asarray(boxes[k]["bounds_xyz_mm"], dtype=float) for k in [first, second])
        current.require(a.shape == b.shape == (3, 2) and np.isfinite(np.r_[a, b]).all()
                        and np.all(a[:, 0] < a[:, 1]) and np.all(b[:, 0] < b[:, 1]), "finite nondegenerate boxes required")
        gaps = np.maximum(b[:, 0]-a[:, 1], a[:, 0]-b[:, 1])
        separated = bool(np.max(gaps) > 0.)
        pairs.append({"first": first, "second": second, "registered_source_pair": (first, second) in registered,
                      "axis_separation_mm": gaps.tolist(), "excluded_by_strict_containing_box_separation": separated,
                      "possible_new_neighbor_requiring_own_feature_coverage": not separated and (first, second) not in registered})
    return pairs


def run():
    current.require(current.ref(intake_source.OWN) == INTAKE and intake_source.LOADED_SHA == INTAKE["sha256"],
                    "exact loaded current intake required")
    cases, pins = intake_source.intake()
    measure, domains = current.read(MEASURE), current.read(DOMAINS)
    resolved, resolution = resolved_domain_pins(domains)
    bridge = current.load("bridge")
    bridge_ref = current.ref(bridge.OWN)
    current.require(bridge_ref == current.manifest()["references"]["bridge"]
                    and bridge.LOADED_SHA == bridge_ref["sha256"], "loaded output bridge differs")
    refs = [own_ref(), INTAKE, MEASURE, DOMAINS, component.own_ref(), component.canonical_dependency(),
            current.ref(current.OWN), current.ref(current.MANIFEST), bridge_ref, current.ref(current.ROOT/"uv.lock")]
    pins = current.join(pins, measure["source_sha256"], resolved, {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    for key in ["owners", "registered_complete_own_faces", "source_contact_face_bindings", "cases", "counts",
                "geometry_revision", "hardware_revision", "extra_grid"]:
        current.require(measure[key] == domains[key], "current measure/domain source binding differs: "+key)
    current.require(measure["case_sequence"] == domains["case_sequence"] == component.SEQUENCE
                    and measure["counts"]["timber_owners"] == 22
                    and measure["counts"]["registered_full_faces"] == 51,
                    "current 22-owner/51-face six-case scope required")
    plan = registered_plan(measure["registered_complete_own_faces"], measure["source_contact_face_bindings"],
                           measure["current_complete_reference_face_measure"])
    current.require(plan["pair_count"] == 38 and len(plan["all_source_contact_ids"]) == 332,
                    "all current 38 source pairs and 332 contact rows required")
    registered = {tuple(sorted((r["slave_owner"], r["master_owner"]))) for r in plan["pairs"]}
    geometry = {r["owner_id"]: r for r in domains["owners"]}
    saved = domains["current_diagnostic_ambient_injectivity"]
    current.require(saved["all132_sufficient_on_own_ambient_box"] is True and len(saved["cases"]) == 6
                    and set(saved["charts"]) == set(saved["extents"]) == set(geometry), "complete own current domains required")
    records = []
    for (binding, field, _), source_case, prior in zip(cases, measure["cases"], saved["cases"], strict=True):
        current.require(all(source_case[k] == binding[k] == prior[k] for k in ["case_id", "state_id", "field"]),
                        "own current case/state/field required")
        old_q = np.asarray(field["response"]["q"])
        current.require(old_q.shape == (9350,) and canonical_sha(old_q.tolist()) == field["response"]["q_canonical_sha256"],
                        "exact own saved diagnostic vector required")
        q = np.r_[old_q, np.zeros(100)]
        current.require(canonical_sha(q.tolist()) == prior["full_diagnostic_q_canonical_sha256"], "own full diagnostic state differs")
        bounds = {r["owner_id"]: r for r in prior["bounds"]}
        current.require(len(bounds) == len(prior["bounds"]) == 22 and bounds.keys() == geometry.keys(), "all22 own bound records required")
        boxes = {}
        for owner, chart in saved["charts"].items():
            extent = saved["extents"][owner]
            identity = extent["source_identity"]
            source = geometry[owner]["finished_source"]
            current.require(identity["finished_raw_file_path"] == source["path"]
                            and identity["finished_raw_file_sha256"] == source["sha256"]
                            and identity["topology_sha256"] == geometry[owner]["frozen_constructor_topology_sha256"],
                            "own deformed domain/finished solid source differs")
            boxes[owner] = containing_deformed_box(chart, q, extent, bounds[owner])
        pairs = screen_pairs(boxes, registered)
        records.append({**source_case, "full_diagnostic_q_canonical_sha256": prior["full_diagnostic_q_canonical_sha256"],
            "containing_deformed_boxes": list(boxes.values()), "all231_pair_screens": pairs,
            "excluded_pair_count": sum(r["excluded_by_strict_containing_box_separation"] for r in pairs),
            "possible_new_neighbor_pair_count": sum(r["possible_new_neighbor_requiring_own_feature_coverage"] for r in pairs)})
    current.verify(pins)
    return {"schema": "eoere_current_registered_timber_contact_and_neighbor_scope/v1", "producer": own_ref(),
        "source_sha256": pins, "historical_source_resolutions": [resolution], "all_sources_unchanged": True,
        "complete_face_measure": MEASURE, "diagnostic_domains": DOMAINS, "registered_plan": plan,
        "case_sequence": component.SEQUENCE, "cases": records,
        "geometry_revision": measure["geometry_revision"], "hardware_revision": measure["hardware_revision"], "extra_grid": False,
        "saved_poses_only_not_trial_state_neighbor_coverage": True,
        "distance_inverse_contact_force_or_frame_solve_performed": False,
        "complete_contact_feature_coverage_or_physical_stiffness_qualified": False,
        "native_FEA_authorized_or_run": False, "structural_acceptance": False, "release": current.manifest()["release"],
        "limits": ["Every pair screen covers whole current timber solids through containing boxes, but overlaps are unresolved possibilities, not detected contact.",
                   "The 38 registered source pairs preserve complete selected faces and all eligible masters. Other boundary features and possible new neighbors require their own coverage before contact composition.",
                   "Saved first-order poses are diagnostic only. Every new trial state needs fresh geometric enclosures and inverse/contact branch checks.",
                   "Geodesic bounds are real-arithmetic estimates with 1e-6 mm box padding, not interval certificates or physical demand bounds."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
