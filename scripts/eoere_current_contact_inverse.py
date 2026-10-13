"""Current guarded timber inverse and complete-own-boundary feature probes.

Reuses the frozen geodesic map, inverse iteration and genuine closed-solid
distance callbacks. A representative cell, or every occupied full-face cell,
is probed per registered pair at each saved diagnostic pose. This is a
method/branch investigation, not new-neighbor coverage, a force law, a frame
solve or structural acceptance.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path

import numpy as np

from scripts import eoere_current_components as component
from scripts import eoere_current_contact_scope as scope
from scripts import eoere_current_response as current
from scripts import eoere_current_timber_domains as domains_source
from scripts.summarize_eoere_current_response import canonical_sha

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
CONTACT_SCOPE = {"path": scope.RAW+"current-timber-contact-scope-v2.json",
                 "sha256": "03f959ccf2d851c78264ac9240bd42eb41ee6bcbf6658e0c06d736ff940737c8"}
SCOPE_PRODUCER = {"path": "scripts/eoere_current_contact_scope.py",
                  "sha256": "035c62fee025bf3cba4fa24770914fc339deb95c88c78af99cd7fddfe0d21076"}
BEDDING = {"path": "fea/generated/thin-bolted-current-contact-v1/reference-bedding-production-v1/reference_bedding.py",
           "sha256": "99655072fe0f16067bb0b17a6da22b942e7bf55ce86fb75113f7f006e6c6d8e3"}
DISTANCE_ADAPTER = {"path": "fea/generated/thin-bolted-current-contact-v1/reference-bedding-production-v1/closed_solid_distance.py",
                    "sha256": "aae29cde8a0cf7c1f157e44635c82e82e6c83cf7c2a465a0573562c3a7540a38"}
PROBE_COLUMNS = ["sample_index", "disposition", "current_slave_point_xyz_mm",
    "point_to_master_box_axis_separation_mm", "master_reference_inverse_xyz_mm", "master_branch",
    "inverse_iterations", "inverse_residual_inf_mm", "residual_to_root_ball_radius_mm", "reference_box_margin_mm",
    "rho_reference_mm", "solid_classification", "boundary_unsigned_distance_mm", "closest_own_features",
    "active_native_branch_flags", "native_record_canonical_sha256", "complete_probe_canonical_sha256"]
CLOSEST_COLUMNS = ["feature_id", "closest_support_feature_id", "support_type", "trim_classification",
                   "closest_point_xyz_mm", "distance_mm"]


def own_ref():
    current.require(current.sha(OWN) == LOADED_SHA, "loaded current inverse producer changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


class TrialDomain:
    """One immutable own chart/box, with an exact-state lazy sufficient bound.

    This generic numerical guard owns no candidate source authentication.
    The current factory below supplies and verifies its genuine source joins.
    Every iterate remains in the same box; no saved bound transfers to new q.
    """

    def __init__(self, owner, chart, extent, ndof, method):
        self.owner, self.ndof, self.method = owner, ndof, method
        self.chart, self.extent = copy.deepcopy(chart), copy.deepcopy(extent)
        current.require(extent["owner_id"] == owner and isinstance(ndof, int) and ndof > 0,
                        "own domain and positive coordinate dimension required")
        self.identity = canonical_sha([self.chart, self.extent])
        self.cached_bytes, self.cached_q, self.cached_bound = None, None, None
        self.bound_evaluation_count = 0

    def bound(self, q):
        current.require(canonical_sha([self.chart, self.extent]) == self.identity, "own source chart/domain changed")
        q = np.asarray(q, dtype=float)
        current.require(q.shape == (self.ndof,) and np.isfinite(q).all(), "finite exact full trial state required")
        content = q.tobytes()
        if content != self.cached_bytes:
            frozen = q.copy()
            frozen.setflags(write=False)
            value = self.method.sufficient_box_bound(self.chart, frozen, owner_id=self.owner,
                                                     extent=self.extent, comparison_padding=1e-10)
            current.require(value["owner_id"] == self.owner
                            and value["row_canonical_sha256"] == canonical_sha(self.chart)
                            and value["q_canonical_sha256"] == canonical_sha(frozen.tolist())
                            and value["extent_canonical_sha256"] == canonical_sha(self.extent),
                            "trial bound differs from own state/chart/domain")
            current.require(value["sufficient_global_one_to_one_criterion_met"] is True
                            and 0. <= value["padded_sufficient_L"] < 1.,
                            "trial lacks a sufficient one-to-one bound on its own ambient box")
            self.cached_bytes, self.cached_q, self.cached_bound = content, frozen, copy.deepcopy(value)
            self.bound_evaluation_count += 1
        return copy.deepcopy(self.cached_bound)

    def guard(self, q, point):
        value = self.bound(q)
        point = np.asarray(point, dtype=float)
        bounds = np.asarray(self.extent["bounds_xyz_mm"], dtype=float)
        current.require(point.shape == (3,) and np.isfinite(point).all(), "finite own inverse iterate required")
        margin = float(min(np.min(point-bounds[:, 0]), np.min(bounds[:, 1]-point)))
        current.require(margin >= 1e-6, "inverse iterate outside the guarded ambient box margin")
        return {"reference_domain_eligible": True, "owner_id": self.owner,
            "reference_point_xyz_mm": point.tolist(), "reference_box_margin_mm": margin,
            "q_canonical_sha256": value["q_canonical_sha256"],
            "row_canonical_sha256": value["row_canonical_sha256"],
            "extent_canonical_sha256": value["extent_canonical_sha256"],
            "trial_bound_canonical_sha256": canonical_sha(value), "padded_sufficient_L": value["padded_sufficient_L"],
            "target_in_image_or_occupied_wood_checked_here": False}

    def certify_observed_inverse(self, q, point, target, observed, *, residual_inf_mm, iterations):
        """Residual-to-root ball under the same real-arithmetic L<1 hypotheses.

        phi=I+g and ||Dg||<=L. On the ball B(X0,r/(1-L)), the map
        X -> target-g(X) maps the ball into itself and is a contraction.
        A ball strictly inside the ambient box gives a unique root there.
        Floating evaluation is not an interval or roundoff certificate.
        """
        guard = self.guard(q, point)
        target, observed = np.asarray(target, dtype=float), np.asarray(observed, dtype=float)
        current.require(target.shape == observed.shape == (3,) and np.isfinite(np.r_[target, observed]).all()
                        and isinstance(iterations, int) and 0 <= iterations < 20,
                        "genuine finite inverse observations required")
        residual = observed-target
        measured = float(np.max(abs(residual)))
        current.require(np.isfinite(residual_inf_mm) and 0. <= residual_inf_mm <= 1e-11
                        and measured <= 1e-11 and abs(measured-residual_inf_mm) <= 1e-15,
                        "final inverse residual is inconsistent or above the frozen gate")
        radius = float(np.linalg.norm(residual)/(1.-guard["padded_sufficient_L"]))
        current.require(radius < guard["reference_box_margin_mm"]-1e-6,
                        "residual-to-root ball does not lie strictly inside the guarded ambient box")
        return {**guard, "inverse_residual_inf_mm": measured, "inverse_iterations": iterations,
            "residual_to_root_ball_radius_mm": radius,
            "real_arithmetic_contraction_ball_condition_met": True,
            "unique_inverse_under_same_exact_map_and_bound_hypotheses": True,
            "formal_interval_or_float_roundoff_certificate": False,
            "physical_contact_pressure_or_occupied_wood_qualified": False}


def runtime_methods():
    """Load genuine generic kernels; never use their old candidate factories."""
    bedding = component.load(BEDDING, "current_guarded_inverse_bedding")
    injectivity = component.load(domains_source.INJECTIVITY, "current_guarded_inverse_bound")
    adapter = component.load(DISTANCE_ADAPTER, "current_guarded_inverse_distance")
    smooth = adapter.methods()
    container = component.load(domains_source.CONTAINER, "current_guarded_inverse_container")
    current.require(injectivity.geometry.LOADED_TEST_SHA == domains_source.INJECTIVITY_IMPORT_TEST["sha256"],
                    "exact loaded transitive geodesic test required")
    refs = [BEDDING, domains_source.INJECTIVITY, DISTANCE_ADAPTER, domains_source.CONTAINER,
            domains_source.INJECTIVITY_IMPORT_TEST]
    pins = current.join(bedding.source_pins(), injectivity.source_pins(), adapter.source_pins(), smooth.source_pins(),
                        {r["path"]: r["sha256"] for r in refs})
    return bedding, injectivity, adapter, smooth, container, pins


def authenticated_inputs():
    current.require(scope.own_ref() == SCOPE_PRODUCER and scope.LOADED_SHA == SCOPE_PRODUCER["sha256"],
                    "exact loaded current contact-scope producer required")
    current.require(current.ref(scope.intake_source.OWN) == scope.INTAKE
                    and scope.intake_source.LOADED_SHA == scope.INTAKE["sha256"], "exact loaded current intake required")
    cases, pins = scope.intake_source.intake()
    record = current.read(CONTACT_SCOPE)
    current.require(record["producer"] == SCOPE_PRODUCER and record["complete_face_measure"] == scope.MEASURE
                    and record["diagnostic_domains"] == scope.DOMAINS
                    and record["case_sequence"] == component.SEQUENCE and len(record["cases"]) == 6
                    and record["geometry_revision"] == "eoere-raised-kicker-screws-v1"
                    and record["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
                    and record["extra_grid"] is False, "exact own current scope and six cases required")
    measure, domains = current.read(scope.MEASURE), current.read(scope.DOMAINS)
    resolved, resolution = scope.resolved_domain_pins(domains)
    current.require(record["historical_source_resolutions"] == [resolution], "preserved domain receipt differs")
    bridge = current.load("bridge")
    bridge_ref = current.ref(bridge.OWN)
    current.require(bridge_ref == current.manifest()["references"]["bridge"]
                    and bridge.LOADED_SHA == bridge_ref["sha256"], "actual loaded output bridge differs")
    refs = [own_ref(), CONTACT_SCOPE, SCOPE_PRODUCER, scope.MEASURE, scope.DOMAINS, scope.INTAKE,
            domains_source.own_ref(), component.own_ref(), component.canonical_dependency(),
            current.ref(current.OWN), current.ref(current.MANIFEST), bridge_ref, current.ref(current.ROOT/"uv.lock")]
    pins = current.join(pins, record["source_sha256"], measure["source_sha256"], resolved,
                        {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    return cases, record, measure, domains, pins


def current_geometries(domains, smooth, container, pins):
    """Reconstruct all current own closed boundaries and compare frozen census."""
    geometries = {}
    for row in domains["owners"]:
        owner, topology = row["owner_id"], row["frozen_constructor_topology"]
        current.require(owner not in geometries and topology["owner_id"] == owner, "unique own current timber required")
        identity = topology["source_identity"]
        path, digest = identity["finished_raw_file_path"], identity["finished_raw_file_sha256"]
        current.require(pins.get(path) == digest == row["finished_source"]["sha256"]
                        and row["finished_source"]["path"] == path, "own cached timber source differs")
        imported = smooth.reference.cq.Shape.importBrep(str(current.ROOT/path))
        solid, wrapper = container.strict_solid(imported, smooth.reference)
        current.require(wrapper == row["strict_container"], "own current transparent container differs")
        geometry = smooth.reference.ReferenceSolidDistance(solid, owner_id=owner, source_identity=identity,
                                                          linear_tolerance_mm=1e-7, tie_tolerance_mm=1e-6)
        current.require(geometry.topology == topology and geometry.topology_sha256 == row["frozen_constructor_topology_sha256"],
                        "own current closed solid or complete boundary feature census differs")
        geometries[owner] = geometry
    current.require(len(geometries) == 22, "all22 current own genuine timber boundaries required")
    return geometries


def registered_cells(plan, measure, source_rows, *, all_cells=False):
    """Keep each pair's complete cells, or its centroid-nearest representative."""
    faces = {r["feature_id"]: r for r in measure["current_complete_reference_face_measure"]["full_faces"]}
    source = {r["id"]: r for r in source_rows if r["kind"] == "timber_face_contact"}
    current.require(len(source) == 332 and len(faces) == 51, "own332 source rows and51 whole faces required")
    selected = []
    for pair in plan["pairs"]:
        face = faces[pair["slave_feature_id"]]
        current.require(face["owner_id"] == pair["slave_owner"]
                        and [c["id"] for c in face["cells"]] == pair["complete_selected_face_cell_ids"],
                        "complete own selected face cells required")
        original = [source[k] for k in pair["source_contact_ids"]]
        current.require(all({r["first"], r["second"]} == {pair["slave_owner"], pair["master_owner"]} for r in original),
                        "representative source patch owners differ")
        area = np.asarray([r["reference_area_mm2"] for r in original])
        points = np.asarray([r["point_xyz_mm"] for r in original])
        current.require(area.ndim == 1 and len(area) > 0 and np.all(area > 0.) and np.isfinite(area).all()
                        and points.shape == (len(area), 3) and np.isfinite(points).all(), "positive finite original patch measure required")
        centroid = np.average(points, axis=0, weights=area)
        for cell in face["cells"]:
            current.require(cell["area_mm2"] > 0. and cell["own_inward_material_probe_occupied"] is True
                            and cell["reference_centroid_on_full_own_face"] is True
                            and np.asarray(cell["point_xyz_mm"]).shape == (3,)
                            and np.isfinite(cell["point_xyz_mm"]).all(), "occupied positive own full-face cell required")
        cells = face["cells"] if all_cells else [min(face["cells"], key=lambda r: (float(np.linalg.norm(np.asarray(r["point_xyz_mm"])-centroid)), r["id"]))]
        selected.extend({"pair_id": pair["id"], "slave": pair["slave_owner"], "master": pair["master_owner"],
            "slave_feature_id": pair["slave_feature_id"], "cell": copy.deepcopy(cell),
            "original_patch_area_weighted_centroid_xyz_mm": centroid.tolist()} for cell in cells)
    current.require(len(plan["pairs"]) == len({r["pair_id"] for r in selected}) == 38, "all38 own source pairs required")
    current.require(len(selected) == len({(r["pair_id"], r["cell"]["id"]) for r in selected})
                    == (plan["pair_cell_count"] if all_cells else 38), "complete unique own pair/cell bindings required")
    return selected


def diagnostic_poses(cases, record, domains):
    """Check every saved identity and state before reconstructing geometry."""
    saved = domains["current_diagnostic_ambient_injectivity"]["cases"]
    current.require(len(cases) == len(record["cases"]) == len(saved) == 6
                    and [b["case_id"] for b, _, _ in cases] == component.SEQUENCE,
                    "six own cases in current source order required")
    poses = []
    for (binding, field, _), source_case, source_domain in zip(cases, record["cases"], saved, strict=True):
        current.require(all(binding[k] == source_case[k] == source_domain[k] for k in ["case_id", "state_id", "field"]),
                        "own current case/state/field required")
        old_q = np.asarray(field["response"]["q"], dtype=float)
        current.require(old_q.shape == (9350,) and np.isfinite(old_q).all()
                        and canonical_sha(old_q.tolist()) == field["response"]["q_canonical_sha256"], "own saved diagnostic state differs")
        q = np.r_[old_q, np.zeros(100)]
        current.require(canonical_sha(q.tolist()) == source_case["full_diagnostic_q_canonical_sha256"]
                        == source_domain["full_diagnostic_q_canonical_sha256"], "own full diagnostic state differs")
        poses.append((binding, q, source_case, source_domain))
    return poses


def inverse_feature_probe(sample, q, maps, guards, boxes, callbacks, bedding, adapter):
    slave, master = sample["slave"], sample["master"]
    point = np.asarray(sample["cell"]["point_xyz_mm"], dtype=float)
    target = maps[slave].point_field(q, point, tangent=False)["value_xyz"]
    box = np.asarray(boxes[master]["bounds_xyz_mm"])
    gaps = np.maximum(box[:, 0]-target, target-box[:, 1])
    if np.max(gaps) > 0.:
        return {**sample, "current_slave_point_xyz_mm": target.tolist(), "disposition": "STRICTLY_OUTSIDE_CONTAINING_MASTER_BOX",
            "point_to_master_box_axis_separation_mm": gaps.tolist(), "inverse_or_distance_queried": False,
            "force_or_zero_response_supplied": False}
    try:
        inverse, iterations, residual = bedding.implicit.inverse(maps[master], q, target, point)
        jet = maps[master].jet(q, inverse, tangent=False)
        observed = jet["field"]["value_xyz"]
        certificate = guards[master].certify_observed_inverse(q, inverse, target, observed,
                                                             residual_inf_mm=residual, iterations=iterations)
    except ValueError as error:
        return {**sample, "current_slave_point_xyz_mm": target.tolist(), "disposition": "UNRESOLVED_INVERSE_BRANCH",
            "reason": str(error), "force_or_zero_response_supplied": False}
    result = {**sample, "current_slave_point_xyz_mm": target.tolist(), "master_reference_inverse_xyz_mm": inverse.tolist(),
              "master_branch": jet["branch"], "inverse_observation": certificate, "force_or_zero_response_supplied": False}
    try:
        distance = callbacks[master](inverse)
    except adapter.GuardedReferenceFeatureError as error:
        current.require(error.distance_record["owner_id"] == master
                        and np.array_equal(error.distance_record["reference_point_xyz_mm"], inverse),
                        "guarded feature record differs from own master/inverse point")
        return {**result, "disposition": "UNRESOLVED_DISTANCE_FEATURE", "reason": str(error),
                "guarded_native_distance_record": error.distance_record}
    current.require(distance["schema"] == bedding.DISTANCE_SCHEMA and distance["owner_id"] == master
                    and np.array_equal(distance["reference_point_xyz_mm"], inverse),
                    "owned distance differs from current master/inverse point")
    return {**result, "disposition": "STRICT_REFERENCE_OPEN" if distance["strict_closed_solid_open_classification"] else "QUALIFIED_ORDINARY_REFERENCE_FEATURE",
            "owned_distance_record": distance}


def compact_probe(sample_index, probe):
    """Keep resolved observations compact; full native/probe hashes bind omissions.

    Complete unresolved records and selected extrema remain separate. These
    rows are a diagnostic export, never an input to a contact-force callback.
    """
    observation = probe.get("inverse_observation", {})
    distance = probe.get("owned_distance_record", {})
    native = distance.get("guarded_native_distance_record", probe.get("guarded_native_distance_record"))
    native_values = {} if native is None else native
    features = [[f.get(key) for key in CLOSEST_COLUMNS] for f in native_values.get("complete_near_minimum_own_features", [])]
    return [sample_index, probe["disposition"], probe["current_slave_point_xyz_mm"],
        probe.get("point_to_master_box_axis_separation_mm"), probe.get("master_reference_inverse_xyz_mm"), probe.get("master_branch"),
        observation.get("inverse_iterations"), observation.get("inverse_residual_inf_mm"),
        observation.get("residual_to_root_ball_radius_mm"), observation.get("reference_box_margin_mm"),
        distance.get("rho_reference_mm", native_values.get("reference_signed_distance_rho_mm")),
        native_values.get("solid_classification"), native_values.get("boundary_unsigned_distance_mm"), features,
        sorted(k for k, v in native_values.get("branch_flags", {}).items() if v),
        None if native is None else canonical_sha(native), canonical_sha(probe)]


def record_extrema(extrema, sample_index, probe):
    observation, distance = probe.get("inverse_observation", {}), probe.get("owned_distance_record", {})
    candidates = {"max_inverse_residual_inf_mm": observation.get("inverse_residual_inf_mm"),
                  "max_residual_to_root_ball_radius_mm": observation.get("residual_to_root_ball_radius_mm")}
    if "reference_box_margin_mm" in observation:
        candidates["min_reference_box_margin_mm"] = -observation["reference_box_margin_mm"]
    if probe["disposition"] == "QUALIFIED_ORDINARY_REFERENCE_FEATURE":
        candidates["max_compressed_reference_distance_magnitude_mm"] = -distance["rho_reference_mm"]
    for name, score in candidates.items():
        if score is not None and (name not in extrema or score > extrema[name]["comparison_score"]):
            extrema[name] = {"comparison_score": score, "sample_index": sample_index, "complete_probe": copy.deepcopy(probe)}


def run(*, progress=None, all_cells=False):
    cases, record, measure, domains, pins = authenticated_inputs()
    poses = diagnostic_poses(cases, record, domains)
    bedding, injectivity, adapter, smooth, container, method_pins = runtime_methods()
    pins = current.join(pins, method_pins)
    current.verify(pins)
    geometries = current_geometries(domains, smooth, container, pins)
    saved = domains["current_diagnostic_ambient_injectivity"]
    charts, extents = saved["charts"], saved["extents"]
    current.require(set(charts) == set(extents) == set(geometries), "complete own current map/domain/geometry owners required")
    for owner, geometry in geometries.items():
        identity = extents[owner]["source_identity"]
        current.require(all(identity[k] == value for k, value in geometry.source_identity.items())
                        and identity["topology_sha256"] == geometry.topology_sha256,
                        "own runtime chart/domain and genuine geometry source differ")
    guards = {o: TrialDomain(o, chart, extents[o], 9450, injectivity) for o, chart in charts.items()}
    maps = {o: bedding.TimberSpatialMap(chart, owner_id=o, ndof=9450, domain_guard=guards[o].guard) for o, chart in charts.items()}
    callbacks = {o: adapter.OwnedDistanceCallback(geometry, smooth) for o, geometry in geometries.items()}
    samples = registered_cells(record["registered_plan"], measure, cases[0][1]["reference_interaction_descriptors"], all_cells=all_cells)
    results = []
    for binding, q, source_case, source_domain in poses:
        bounds = {o: guard.bound(q) for o, guard in guards.items()}
        current.require(list(bounds.values()) == source_domain["bounds"], "fresh current bounds differ from own saved bounds")
        boxes = {o: scope.containing_deformed_box(charts[o], q, extents[o], bound) for o, bound in bounds.items()}
        current.require(list(boxes.values()) == source_case["containing_deformed_boxes"], "fresh own deformed boxes differ")
        probes, unresolved, extrema, counts = [], [], {}, Counter()
        for index, sample in enumerate(samples):
            probe = inverse_feature_probe(sample, q, maps, guards, boxes, callbacks, bedding, adapter)
            counts[probe["disposition"]] += 1
            if all_cells:
                probes.append(compact_probe(index, probe))
                if probe["disposition"].startswith("UNRESOLVED_"):
                    unresolved.append({"sample_index": index, "complete_probe": probe})
                record_extrema(extrema, index, probe)
                if progress and (index+1) % 500 == 0:
                    progress({"case_id": binding["case_id"], "probes_completed": index+1, "dispositions": dict(counts)})
            else:
                probes.append(probe)
        value = {**binding, "full_diagnostic_q_canonical_sha256": canonical_sha(q.tolist()),
                 "probe_count": len(probes), "disposition_counts": dict(counts)}
        value.update({"probe_rows": probes, "complete_unresolved_probes": unresolved, "complete_extrema": extrema} if all_cells else {"probes": probes})
        results.append(value)
        if progress: progress({"case_id": binding["case_id"], "probes": len(probes), "dispositions": value["disposition_counts"]})
    current.verify(pins)
    output = {"schema": "eoere_current_guarded_inverse_and_owned_feature_probes/"+("v2" if all_cells else "v1"), "producer": own_ref(),
        "source_sha256": pins, "all_sources_unchanged": True, "current_contact_scope": CONTACT_SCOPE,
        "case_sequence": component.SEQUENCE, "cases": results, "registered_pair_count": 38, "probe_count": sum(r["probe_count"] for r in results),
        "fresh_current_bound_count": sum(g.bound_evaluation_count for g in guards.values()),
        "selection_rule": "every occupied complete source-face cell per registered pair in frozen pair/cell order" if all_cells else "one occupied full-face cell per registered pair nearest its original area-weighted patch centroid; cell ID breaks exact distance ties",
        "all_registered_pair_cells_probed_at_saved_poses": bool(all_cells),
        "geometry_revision": record["geometry_revision"], "hardware_revision": record["hardware_revision"], "extra_grid": False,
        "all_full_face_cells_or_new_neighbors_or_station_touch_branches_qualified": False,
        "contact_force_or_frame_equilibrium_or_native_FEA_performed": False,
        "physical_stiffness_or_demand_or_complete_resistance_qualified": False,
        "structural_acceptance": False, "release": current.manifest()["release"],
        "limits": ["All registered pair/cell bindings are queried at saved poses; the six possible new-neighbor pairs and future trial states are not covered." if all_cells else "One representative cell per registered source pair, not all 10484 pair/cell bindings or six possible new-neighbor pairs.",
                   "Saved first-order poses are diagnostic only. Current per-trial bounds and all inverse iterates are guarded; the tiny residual-to-root ball uses real-arithmetic hypotheses, not certified floating intervals.",
                   "Native closest-feature queries retain each genuine own closed boundary; unresolved inverse, station, touch or compressed feature branches remain explicit and supply no replacement zero response.",
                   "Reference signed distance and its analytic jet do not qualify current Euclidean pressure, wood bedding, physical stiffness, movement, frame equilibrium or complete strength."]}
    if all_cells:
        output.update({"probe_columns": PROBE_COLUMNS, "closest_own_feature_columns": CLOSEST_COLUMNS,
            "sample_binding_columns": ["pair_id", "cell_id"],
            "sample_bindings": [[s["pair_id"], s["cell"]["id"]] for s in samples],
            "compact_rows_are_contact_force_inputs": False,
            "complete_unresolved_records_retained": True,
            "resolved_native_records_reproducible_and_bound_by_canonical_hash": True})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--all-cells", action="store_true", help="Probe every frozen registered pair/cell binding and export compact resolved rows.")
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run(progress=lambda value: print(json.dumps(value), flush=True), all_cells=args.all_cells))
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
