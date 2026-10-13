"""Compose current timber reference-material bedding with fresh trial guards.

This reuses the reviewed inverse/jet/energy kernel, source-face quadrature and
closed-solid callbacks. The declared bedding is a numerical scenario; neither
these diagnostic forces nor solver convergence qualify physical joint demand.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

from scripts import eoere_current_neighbor_enclosures as neighbors

inverse, current, scope = neighbors.inverse, neighbors.current, neighbors.scope
canonical_sha = neighbors.canonical_sha
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
NEIGHBORS = {"path": scope.RAW+"current-timber-neighbor-pieces-v2.json",
             "sha256": "68e9e5e3f13940a2b934a6fbc108cc35b6178ef9f5c654b849ae8984b4c2034b"}
NEIGHBOR_PRODUCER = {"path": "scripts/eoere_current_neighbor_enclosures.py",
                     "sha256": "7368b120a9ff177bb8b40162b40e3eb54d51d1ae5c8f67532f781f349391af33"}
INVERSE_PRODUCER = {"path": "scripts/eoere_current_contact_inverse.py",
                    "sha256": "bb79fc672bcf5395accfa94840b0962777aadf39b232f5aeeb493ec5ed8eab9a"}
PRESERVED_FORCE = {"path": scope.RAW+"current-timber-bedding-v1.json",
    "sha256": "5a87c2ccc0fe844567a14151116dc7bd441e367c468cedc30697e93df338cca1"}
PRESERVED_PRODUCER = {"path": scope.RAW+"source-at-current-timber-bedding-v1/eoere_current_timber_bedding.py",
    "sha256": "bb6b8c1813fa344786101f638350913148be4f66e998c6ecbaeffd94c6292a8c"}
ROW_COLUMNS = ["sample_index", "branch", "energy_nmm", "rho_reference_mm",
    "current_slave_point_xyz_mm", "reference_master_point_xyz_mm", "force_on_slave_xyz_n",
    "inverse_iterations", "inverse_residual_inf_mm", "root_ball_radius_mm",
    "full_gradient_work_residual_inf_n", "pair_spatial_moment_residual_nmm",
    "owned_distance_record_canonical_sha256"]


def own_ref():
    current.require(current.sha(OWN) == LOADED_SHA, "loaded current timber bedding producer changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def case_source(binding):
    """Keep source admission diagnostics separate from the evaluated response."""
    return {**{key: copy.deepcopy(binding[key]) for key in ["case_id", "state_id", "field"]},
            "saved_first_order_source": copy.deepcopy(binding)}


def force_samples(plan, measure, source_rows):
    """Use every fixed own cell and its pair's explicit original bedding."""
    cells = inverse.registered_cells(plan, measure, source_rows, all_cells=True)
    originals = {r["id"]: r for r in source_rows if r["kind"] == "timber_face_contact"}
    by_pair = {}
    for pair in plan["pairs"]:
        rows = [originals[key] for key in pair["source_contact_ids"]]
        values = [r["bedding_n_mm3"] for r in rows]
        current.require(all(np.isfinite(value) and value > 0. for value in values)
                        and len(set(values)) == 1 and all(
                            np.isfinite(r["stiffness"]) and abs(r["stiffness"]-r["reference_area_mm2"]*values[0])
                            <= 1e-12*max(1., r["stiffness"]) for r in rows),
                        "one explicit consistent positive bedding for each complete pair required")
        by_pair[pair["id"]] = values[0]
    return [{"id": s["pair_id"]+"/"+s["cell"]["id"], "pair_id": s["pair_id"],
        "cell_id": s["cell"]["id"], "slave": s["slave"], "master": s["master"],
        "slave_feature_id": s["slave_feature_id"], "slave_reference_point_xyz_mm": s["cell"]["point_xyz_mm"],
        "master_inverse_seed_xyz_mm": s["cell"]["point_xyz_mm"],
        "reference_area_mm2": s["cell"]["area_mm2"], "bedding_n_mm3": by_pair[s["pair_id"]]}
        for s in cells]


class TimberBedding:
    """Fixed quadrature with own inverse domains and all-pair trial screening.

    Generic numerical orchestration; prepare_current supplies authenticated
    current source ownership. A failed feature, inverse or neighbor guard stops
    the whole response. Strict exterior-box points supply locally zero energy.
    """

    def __init__(self, charts, extents, geometries, samples, *, methods, local_boxes,
                 reference_distances=(), source_sha256, ndof):
        self.bedding, injectivity, adapter, self.smooth, _container, _ = methods
        self.charts, self.extents = copy.deepcopy(charts), copy.deepcopy(extents)
        self.geometries, self.samples, self.ndof = dict(geometries), copy.deepcopy(samples), ndof
        self.local_boxes = copy.deepcopy(local_boxes)
        self.source_sha256 = dict(source_sha256)
        current.require(set(charts) == set(extents) == set(geometries) == set(local_boxes) and len(charts) >= 2,
                        "complete own source/chart/extent/local-box registry required")
        self.guards = {o: inverse.TrialDomain(o, chart, extents[o], ndof, injectivity) for o, chart in charts.items()}
        self.maps = {o: self.bedding.TimberSpatialMap(chart, owner_id=o, ndof=ndof, domain_guard=self.guards[o].guard)
                     for o, chart in charts.items()}
        self.callbacks = {o: adapter.OwnedDistanceCallback(g, self.smooth) for o, g in geometries.items()}
        for owner, geometry in self.geometries.items():
            box = self.local_boxes[owner]
            current.require(geometry.owner_id == owner and box["owner_id"] == owner
                            and box["source_identity"] == geometry.source_identity
                            and box["topology_sha256"] == geometry.topology_sha256
                            and box["original_canonical_solid_sha256"] == geometry.shape_sha256
                            and all(extents[owner]["source_identity"].get(k) == v for k, v in geometry.source_identity.items())
                            and extents[owner]["source_identity"]["topology_sha256"] == geometry.topology_sha256,
                            "own genuine boundary, native box and ambient domain must join")
        ids = [s["id"] for s in self.samples]
        current.require(ids and len(ids) == len(set(ids)), "unique nonempty fixed material-cell IDs required")
        for sample in self.samples:
            current.require(sample["slave"] != sample["master"] and {sample["slave"], sample["master"]} <= charts.keys()
                            and np.isfinite([sample["reference_area_mm2"], sample["bedding_n_mm3"]]).all()
                            and min(sample["reference_area_mm2"], sample["bedding_n_mm3"]) > 0.
                            and all(np.asarray(sample[k]).shape == (3,) and np.isfinite(sample[k]).all()
                                    for k in ["slave_reference_point_xyz_mm", "master_inverse_seed_xyz_mm"]),
                            "fixed positive own reference cells and bedding required")
        self.registered = {tuple(sorted([s["slave"], s["master"]])) for s in self.samples}
        self.distances = {(r["first"], r["second"]): copy.deepcopy(r) for r in reference_distances}
        current.require(len(self.distances) == len(reference_distances), "unique source pair-distance records required")
        self.descriptor_sha = self._descriptor_sha()

    def _descriptor_sha(self):
        return canonical_sha([self.charts, self.extents, self.local_boxes, self.samples, self.source_sha256])

    def trial_scope(self, q):
        current.require(self._descriptor_sha() == self.descriptor_sha, "fixed timber source or quadrature descriptors changed")
        bounds = {o: guard.bound(q) for o, guard in self.guards.items()}
        covers = {o: neighbors.piece_enclosures(self.charts[o], q, self.extents[o], b, self.local_boxes[o]) for o, b in bounds.items()}
        boxes = {o: c["coarse_enclosure"] for o, c in covers.items()}
        screens = []
        for old in scope.screen_pairs(boxes, self.registered):
            a, b = old["first"], old["second"]
            piece = neighbors.separate_piece_covers(covers[a], covers[b])
            excluded = old["excluded_by_strict_containing_box_separation"] or piece["excluded_by_strict_separation_of_every_covering_piece_pair"]
            motion = None
            if not excluded and not old["registered_source_pair"]:
                if (a, b) not in self.distances:
                    self.distances[a, b] = neighbors.reference_pair_distance(self.geometries[a], self.geometries[b], self.smooth)
                motion = neighbors.distance_motion_screen(self.distances[a, b], covers[a], covers[b])
                excluded = motion["excluded_by_strict_reference_distance_minus_motion"]
            screens.append({**old, "piece_screen": piece, "source_distance_motion_screen": motion,
                "excluded_by_any_source_bound_screen": bool(excluded),
                "remaining_possible_new_neighbor": not excluded and not old["registered_source_pair"]})
        unresolved = [r for r in screens if r["remaining_possible_new_neighbor"]]
        current.require(not unresolved, "trial has unregistered timber neighbors requiring complete coverage: "+str([(r["first"], r["second"]) for r in unresolved]))
        return {"own_bounds": list(bounds.values()), "own_piece_covers": list(covers.values()),
                "all_pair_screens": screens, "remaining_possible_new_neighbor_count": 0}, boxes

    def response(self, q, *, tangent=True, progress=None):
        current.verify(self.source_sha256)
        q = np.array(q, dtype=float, copy=True)
        current.require(q.shape == (self.ndof,) and np.isfinite(q).all(), "finite complete timber response state required")
        q.setflags(write=False)
        trial, boxes = self.trial_scope(q)
        energy, gradient = 0., np.zeros(self.ndof)
        hessian = csr_matrix((self.ndof, self.ndof)) if tangent else None
        rows, counts, extrema = [], Counter(), {}
        owner_wrenches = {o: np.zeros(6) for o in self.maps}
        for index, sample in enumerate(self.samples):
            slave, master = sample["slave"], sample["master"]
            field = self.maps[slave].point_field(q, sample["slave_reference_point_xyz_mm"], tangent=tangent)
            point = field["value_xyz"]
            box = np.asarray(boxes[master]["bounds_xyz_mm"])
            separation = np.maximum(point-box[:, 1], box[:, 0]-point)
            if np.any(separation > 0.):
                row = [index, "strict-master-box-open", 0., None, point.tolist(), None, [0., 0., 0.], None, None, None, 0., [0., 0., 0.], None]
            else:
                try:
                    value = self.bedding.response(self.maps[master], q, field, sample["master_inverse_seed_xyz_mm"], self.callbacks[master],
                        stiffness_n_mm=sample["reference_area_mm2"]*sample["bedding_n_mm3"], tangent=tangent)
                    observation = self.guards[master].certify_observed_inverse(q, value["reference_master_point_xyz_mm"], point,
                        value["current_master_penalty_point_xyz_mm"], residual_inf_mm=value["inverse_residual_inf_mm"], iterations=value["inverse_iterations"])
                except ValueError as error:
                    raise ValueError(f"timber sample {index} {sample['id']} has no admissible response: {error}") from error
                energy += value["energy_nmm"]
                gradient += value["gradient_n"]
                if tangent: hessian += value["hessian_csr"]
                force = value["force_on_slave_xyz_n"]
                owner_wrenches[slave] += np.r_[force, np.cross(point, force)]
                owner_wrenches[master] += np.r_[-force, np.cross(value["current_master_penalty_point_xyz_mm"], -force)]
                row = [index, value["branch"], value["energy_nmm"], value["rho_reference_mm"], point.tolist(),
                    value["reference_master_point_xyz_mm"].tolist(), force.tolist(), value["inverse_iterations"],
                    value["inverse_residual_inf_mm"], observation["residual_to_root_ball_radius_mm"],
                    value["full_gradient_work_residual_inf_n"], value["pair_spatial_moment_residual_nmm"].tolist(), canonical_sha(value["owned_distance_record"])]
                scores = {"max_force_norm_n": float(np.linalg.norm(force)), "max_work_residual_inf_n": value["full_gradient_work_residual_inf_n"],
                    "max_inverse_residual_inf_mm": value["inverse_residual_inf_mm"], "max_root_ball_radius_mm": observation["residual_to_root_ball_radius_mm"]}
                for name, score in scores.items():
                    if name not in extrema or score > extrema[name]["value"]:
                        extrema[name] = {"value": score, "sample_index": index, "sample": copy.deepcopy(sample),
                            "inverse_observation": observation, "complete_owned_distance_record": value["owned_distance_record"], "row": row}
            rows.append(row)
            counts[row[1]] += 1
            if progress and (index+1) % 500 == 0: progress({"cells_completed": index+1, "branches": dict(counts)})
        current.require(len(rows) == len(self.samples) and np.isfinite(energy) and np.isfinite(gradient).all()
                        and (not tangent or np.isfinite(hessian.data).all()), "complete finite timber response required")
        current.verify(self.source_sha256)
        return {"energy_nmm": energy, "gradient_n": gradient, "hessian_csr": hessian,
            "final_q_canonical_sha256": canonical_sha(q.tolist()), "trial_scope": trial,
            "sample_rows": rows, "branch_counts": dict(counts), "complete_extrema": extrema,
            "owner_wrenches_at_world_origin": {o: w.tolist() for o, w in owner_wrenches.items()},
            "all_owner_wrench_sum": sum(owner_wrenches.values()).tolist(),
            "fixed_sample_descriptor_sha256": self.descriptor_sha,
            "physical_pressure_stiffness_or_demand_qualified": False}


def prepare_current():
    current.require(neighbors.own_ref() == NEIGHBOR_PRODUCER and inverse.own_ref() == INVERSE_PRODUCER,
                    "exact reviewed current neighbor and inverse producers required")
    cases, record, measure, domains, pins = inverse.authenticated_inputs()
    poses = inverse.diagnostic_poses(cases, record, domains)
    neighbor_record = current.read(NEIGHBORS)
    current.require(neighbor_record["producer"] == NEIGHBOR_PRODUCER and neighbor_record["current_inverse_producer"] == INVERSE_PRODUCER
                    and neighbor_record["current_contact_scope"] == inverse.CONTACT_SCOPE
                    and neighbor_record["case_sequence"] == inverse.component.SEQUENCE
                    and neighbor_record["geometry_revision"] == record["geometry_revision"]
                    and neighbor_record["hardware_revision"] == record["hardware_revision"]
                    and neighbor_record["extra_grid"] is False and neighbor_record["tool_versions"] == neighbors.TOOL_VERSIONS,
                    "exact own source-bound neighbor evidence required")
    for pose, row in zip(poses, neighbor_record["cases"], strict=True):
        binding, q, _, _ = pose
        current.require(all(binding[k] == row[k] for k in ["case_id", "state_id", "field"])
                        and canonical_sha(q.tolist()) == row["full_diagnostic_q_canonical_sha256"]
                        and row["remaining_possible_new_neighbor_count"] == 0,
                        "own six diagnostic states and neighbor admission required")
    current.require({name: neighbors.version(name) for name in neighbors.TOOL_VERSIONS} == neighbors.TOOL_VERSIONS,
                    "pinned geometry and numerical versions required")
    methods = inverse.runtime_methods()
    pins = current.join(pins, methods[-1], neighbor_record["source_sha256"],
        {r["path"]: r["sha256"] for r in [own_ref(), NEIGHBORS, NEIGHBOR_PRODUCER, INVERSE_PRODUCER]})
    current.verify(pins)
    geometries = inverse.current_geometries(domains, methods[3], methods[4], pins)
    source_rows = cases[0][1]["reference_interaction_descriptors"]
    timber_rows = [r for r in source_rows if r["kind"] == "timber_face_contact"]
    current.require(all([r for r in f["reference_interaction_descriptors"] if r["kind"] == "timber_face_contact"] == timber_rows for _, f, _ in cases),
                    "same current fixed timber law and source rows in all six cases required")
    samples = force_samples(record["registered_plan"], measure, source_rows)
    saved = domains["current_diagnostic_ambient_injectivity"]
    potential = TimberBedding(saved["charts"], saved["extents"], geometries, samples, methods=methods,
        local_boxes={r["owner_id"]: r for r in neighbor_record["source_local_reference_boxes"]},
        reference_distances=neighbor_record["possible_pair_reference_distances"], source_sha256=pins, ndof=9450)
    return potential, poses, neighbor_record


def run(*, progress=None):
    potential, poses, neighbor_record = prepare_current()
    results = []
    for (binding, q, _source_case, source_domain), neighbor in zip(poses, neighbor_record["cases"], strict=True):
        response = potential.response(q, tangent=False, progress=None if progress is None else lambda value, case_id=binding["case_id"]: progress({"case_id": case_id, **value}))
        current.require(response["trial_scope"]["own_bounds"] == source_domain["bounds"]
                        and response["trial_scope"]["own_piece_covers"] == neighbor["own_piece_covers"],
                        "fresh own trial guards and covers differ from reviewed diagnostic evidence")
        response.pop("hessian_csr")
        response["gradient_n"] = response["gradient_n"].tolist()
        results.append({**case_source(binding), **response})
        if progress: progress({"case_id": binding["case_id"], "cells": len(response["sample_rows"]), "branches": response["branch_counts"], "energy_nmm": response["energy_nmm"]})
    current.verify(potential.source_sha256)
    return {"schema": "eoere_current_reference_material_timber_bedding/v2", "producer": own_ref(),
        "source_sha256": potential.source_sha256, "force_law_source_sha256": potential.source_sha256,
        "all_sources_unchanged": True,
        "case_sequence": inverse.component.SEQUENCE, "cases": results, "fixed_samples": potential.samples,
        "sample_row_columns": ROW_COLUMNS, "reviewed_neighbor_evidence": NEIGHBORS,
        "geometry_revision": neighbor_record["geometry_revision"], "hardware_revision": neighbor_record["hardware_revision"], "extra_grid": False,
        "law": ".5*A_reference*k*min(rho_reference(phi_master_inverse(x_slave)),0)^2",
        "all_fixed_registered_cells_retained_including_open_zero_rows": True,
        "saved_first_order_states_are_diagnostic_only": True,
        "force_and_gradient_evaluated": True, "full_current_tangent_evaluated": False,
        "finite_frame_equilibrium_or_native_FEA_performed": False,
        "physical_stiffness_or_demand_or_strength_qualified": False, "structural_acceptance": False,
        "release": current.manifest()["release"],
        "limits": ["Trial source bounds and all timber pairs are screened anew; any unregistered unresolved neighbor stops the response.",
            "Distance and inverse feature failures, station kinks and touch branches stop the response rather than supplying zero forces.",
            "Reference bedding uses original declared stiffness and complete fixed selected-face cells. It is not calibrated wood pressure or a physical stiffness bound.",
            "Reaction is a colocated interior penalty port with the complete F^-T normal magnitude; no surface-force relocation is made.",
            "Only timber contact is composed here. Fittings, shafts, panels, floor and external loads still require full finite-frame composition and equilibrium.",
            "Analytic gradients reuse the reviewed kernel. Its optional Hessian uses the recorded central derivative of port Jacobians; this diagnostic run does not evaluate it.",
            "Numerical source geometry, injectivity and inverse root balls retain their non-interval limitations; no fabrication or climbing release follows."]}


def constitutive_ast(path):
    """Fingerprint the complete cell factory and numerical force/guard class."""
    nodes = {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_text()).body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    return {key: nodes[key] for key in ["force_samples", "TimberBedding"]}


def reexport_preserved():
    """Correct v1's status namespace without repeating any contact evaluation.

    The immutable v1 digest authenticates all numerical values. The preserved
    producer and unchanged constitutive AST bind that evaluation to this law.
    Only case metadata and the descriptor's updated provenance hash change.
    """
    original = current.read(PRESERVED_FORCE)
    snapshot = current.ROOT/PRESERVED_PRODUCER["path"]
    current.verify({PRESERVED_PRODUCER["path"]: PRESERVED_PRODUCER["sha256"]})
    own = own_ref()
    old_producer = original["producer"]
    current.require(original["schema"] == "eoere_current_reference_material_timber_bedding/v1"
        and old_producer == {"path": own["path"], "sha256": PRESERVED_PRODUCER["sha256"]}
        and constitutive_ast(snapshot) == constitutive_ast(OWN),
        "exact preserved force producer and unchanged complete constitutive implementation required")
    old_pins = original["source_sha256"]
    current.require(old_pins.get(own["path"]) == old_producer["sha256"],
                    "preserved force closure must bind its producer")
    resolved = {key: value for key, value in old_pins.items() if key != own["path"]}
    resolved[PRESERVED_PRODUCER["path"]] = PRESERVED_PRODUCER["sha256"]
    current.verify(resolved)
    law_pins = {**old_pins, own["path"]: own["sha256"]}
    current.verify(law_pins)
    cases, record, measure, domains, _pins = inverse.authenticated_inputs()
    poses = inverse.diagnostic_poses(cases, record, domains)
    neighbor = current.read(NEIGHBORS)
    samples = force_samples(record["registered_plan"], measure, cases[0][1]["reference_interaction_descriptors"])
    saved = domains["current_diagnostic_ambient_injectivity"]
    descriptor = [saved["charts"], saved["extents"],
                  {row["owner_id"]: row for row in neighbor["source_local_reference_boxes"]}, samples]
    current.require(original["fixed_samples"] == samples and original["sample_row_columns"] == ROW_COLUMNS
        and original["case_sequence"] == inverse.component.SEQUENCE
        and original["reviewed_neighbor_evidence"] == NEIGHBORS
        and original["geometry_revision"] == neighbor["geometry_revision"]
        and original["hardware_revision"] == neighbor["hardware_revision"]
        and original["extra_grid"] is False and original["all_sources_unchanged"] is True
        and original["force_and_gradient_evaluated"] is True
        and all(original[key] is False for key in ["full_current_tangent_evaluated",
            "finite_frame_equilibrium_or_native_FEA_performed", "physical_stiffness_or_demand_or_strength_qualified",
            "structural_acceptance"]), "complete preserved current six-case force record required")
    results = []
    for row, (binding, q, _case, domain), source_neighbor in zip(original["cases"], poses, neighbor["cases"], strict=True):
        current.require(all(row[key] == value for key, value in binding.items())
            and row["final_q_canonical_sha256"] == canonical_sha(q.tolist())
            and row["fixed_sample_descriptor_sha256"] == canonical_sha([*descriptor, old_pins])
            and row["trial_scope"]["own_bounds"] == domain["bounds"]
            and row["trial_scope"]["own_piece_covers"] == source_neighbor["own_piece_covers"],
            "preserved numerical response must belong to each exact current source state")
        response = {key: value for key, value in row.items() if key not in binding}
        response["fixed_sample_descriptor_sha256"] = canonical_sha([*descriptor, law_pins])
        results.append({**case_source(binding), **response})
    result = {**original, "schema": "eoere_current_reference_material_timber_bedding/v2", "producer": own,
        "source_sha256": current.join(law_pins, {r["path"]: r["sha256"] for r in [PRESERVED_FORCE, PRESERVED_PRODUCER]}),
        "force_law_source_sha256": law_pins, "cases": results,
        "preserved_force_evaluation": {"result": PRESERVED_FORCE, "producer_snapshot": PRESERVED_PRODUCER,
            "numerical_evaluation_repeated": False, "constitutive_ast_unchanged": True,
            "change": "Source first-order status is nested; only its namespace and source-provenance descriptor are corrected."}}
    current.verify(result["source_sha256"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reexport-preserved", action="store_true",
                        help="Correct frozen v1 status metadata without repeating numerical evaluation")
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(reexport_preserved() if args.reexport_preserved else
                     run(progress=lambda value: print(json.dumps(value), flush=True)))
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__": main()
