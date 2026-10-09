"""Deferred cached-solid metadata export, using unchanged genuine query APIs.

Default mode is source-only. Native descriptor extraction requires an exact
approved OFF manifest and a parent-issued serial-slot record. No frame,
stiffness matrix, load case, response, or candidate acceptance is constructed.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[6]
ADAPTER = OWN.parent.parent / "adapter.py"
ADAPTER_SHA = "3eddbab497ae328608b4e5ff93fc2f8e7262ad0bba908afe2f474c1c6fbcca3d"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
if hashlib.sha256(ADAPTER.read_bytes()).hexdigest() != ADAPTER_SHA:
    raise ValueError("preserve the frozen source adapter")
spec = importlib.util.spec_from_file_location("frozen_adjusted_source_adapter_for_cached_export", ADAPTER)
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
require = a.require


def prepare(manifest, manifest_sha):
    preflight = a.preflight(manifest, manifest_sha)
    pins = dict(preflight["source_sha256"])
    a.join(pins, {str(OWN.relative_to(ROOT)): LOADED_SHA})
    old = a.read_ref({"path": a.OLD_INPUT, "sha256": a.OLD_INPUT_SHA}, pins)
    current = a.read_ref(preflight["geometry"], pins)
    baseline = a.read_ref(old["geometry"]["report"], pins)
    sources = {r["id"]: copy.deepcopy(r["source"]) for r in preflight["physical_owner_gravity_descriptors"] if r["kind"] in {"timber", "panel"}}
    require(len(sources) == 28, "exact28 current cached solid sources required")
    report = {"axes": current["axes"], "scenario": baseline["scenario"],
              "finished_solids": [sources[n] for n in sorted(sources) if n not in old["panel_ids"]]}
    panels = [sources[n] for n in old["panel_ids"]]
    a.verify(pins)
    return preflight, old, report, panels, pins


def source_plan(manifest, manifest_sha):
    p, old, report, panels, pins = prepare(manifest, manifest_sha)
    old_sources = {r["id"]: r["source"] for r in old["finished_body_observations"]}
    sources = {r["id"]: r for r in report["finished_solids"]+panels}
    return {"schema": "eoere_adjusted_base_cached_source_export_plan/v1", "source_sha256": pins,
            "geometry": p["geometry"], "optional_2026_extra": False,
            "byte_identical_cached_measure_candidates": sorted(n for n in sources if sources[n]["sha256"] == old_sources[n]["sha256"]),
            "changed_cached_solid_ids": p["changed_finished_owner_ids"],
            "missing_prior_bounds_are_new_observations": sorted(n for n in sources if "bounds_xyz_mm" not in sources[n]),
            "potential_reusable_wall_rows": 120-len(p["required_own_wall_queries"]),
            "fresh_wall_rows_expected": p["required_own_wall_queries"],
            "contact_route": "fresh complete current28 owner face atlas and pair census; all88 flange masks freshly queried",
            "floor_route": "all8 current own floor-face observations; exact32 points must match seven unchanged footprints and four moved post corners",
            "native_queries_deferred": True, "candidate_K_q_forces_or_acceptance": None,
            "serial_slot_API": {"status": "FREE_SLOT", "cached_descriptor_extraction_authorized": True,
                                "approved_geometry_sha256": p["geometry"]["sha256"]},
            "release": p["release"]}


def slot(path, expected_sha, geometry_sha):
    require(os.environ.get("EOERE_PARENT_SERIALIZED_EXTRACTION") == "1", "parent serialized extraction marker required before native method loading")
    require(path is not None and expected_sha is not None and a.sha(path) == expected_sha, "exact parent serial-slot record required")
    record = json.loads(Path(path).read_bytes())
    require(record.get("status") == "FREE_SLOT" and record.get("cached_descriptor_extraction_authorized") is True
            and record.get("approved_geometry_sha256") == geometry_sha, "parent slot does not authorize this exact source-only geometry export")
    return {"path": str(Path(path).resolve()), "sha256": expected_sha, "record_at_start": record}


def import_current(ex, report, panels, pins, q):
    """Measure missing bounds, then use the genuine importer once per BREP.

    Derived bounds are observations, not independent prior-input evidence.
    Actual source row bytes and volume still pass the original hash/volume and
    strict-container checks. The local import cache never changes disk files.
    """
    ex.verify(pins)
    originals = {r["id"]: copy.deepcopy(r) for r in report["finished_solids"]+panels}
    arguments, panel_args = copy.deepcopy(report), copy.deepcopy(panels)
    cache, derived = {}, []
    importer = q.cq.Shape.importBrep
    reference = SimpleNamespace(cq=q.cq, brep_sha=q.distance.brep_sha)
    for row in arguments["finished_solids"]+panel_args:
        require(a.sha(ROOT / row["path"]) == row["sha256"], "cached source changed before bounds observation")
        if "bounds_xyz_mm" not in row:
            path = str(ROOT / row["path"])
            original = importer(path)
            cache[path] = original
            body, _ = q.bridge.strict_solid(original, reference)
            bounds = q.atlas._bounds(body, "current cached source bound")
            row["bounds_xyz_mm"] = [[bounds[2*i], bounds[2*i+1]] for i in range(3)]
            derived.append(row["id"])

    def cached(path):
        if path not in cache:
            cache[path] = importer(path)
        return cache[path]

    with patch.object(q.cq.Shape, "importBrep", staticmethod(cached)):
        bodies, observed = ex.import_cached(arguments, panel_args, pins, q)
    for row in observed:
        row["source"] = originals[row["id"]]
        row["bounds_were_supplied_prior_metadata"] = row["id"] not in derived
        expected_center = row["source"].get("center_of_mass_xyz_mm")
        require(expected_center is None or math.dist(expected_center, row["center_xyz_mm"]) < 1e-5,
                "provided own source COM differs from current cached solid")
    ex.verify(pins)
    return bodies, observed, {"native_cached_BREP_imports": len(cache),
                              "missing_bounds_measured_owner_ids": sorted(derived),
                              "derived_bounds_claimed_as_independent_prior_metadata": False,
                              "original_import_function_restored": q.cq.Shape.importBrep == importer}


def wall_cache(ex, old, report, observations, gross, q, m):
    """Reuse a wall query only with byte-identical source and exact descriptors."""
    old_shapes = {r["id"]: r["source"]["sha256"] for r in old["finished_body_observations"]}
    shapes = {r["id"]: r["source"]["sha256"] for r in observations}
    old_axes = {r["axis_id"]: r["source_axis"] for r in old["shafts"]}
    eligible = {}
    old_walls = {(r["axis_id"], r["receiver"]): r for r in old["finished_receiver_wall_queries"]}
    for axis in report["axes"]:
        prior = old_axes[axis["id"]]
        for receiver in axis["receivers"]:
            if (shapes[receiver] == old_shapes[receiver] and axis["point_xyz_mm"] == prior["point_xyz_mm"]
                    and axis["direction_xyz"] == prior["direction_xyz"] and axis["bore_diameter_mm"] == prior["bore_diameter_mm"]):
                eligible[(receiver, tuple(axis["point_xyz_mm"]), tuple(m.unit(axis["direction_xyz"])), axis["bore_diameter_mm"]/2)] = old_walls[(axis["id"], receiver)]
    body_names, calls = {}, {"reused": [], "fresh": []}
    native = q.bore.finished_bore_wall_intervals

    def query(body, point, direction, radius):
        receiver = body_names[id(body)]
        key = (receiver, tuple(point.toTuple()), tuple(direction.toTuple()), radius)
        # Use the same pinned normalization as the genuine shafts helper.
        # Exact equality can miss reuse; it cannot create a false match.
        row = eligible.get(key)
        if row is None:
            calls["fresh"].append({"receiver": receiver, "point_xyz_mm": list(point.toTuple())})
            return native(body, point, direction, radius)
        require(gross[receiver]["axis"] == row["grain_axis_xyz"], "unchanged wall grain descriptor differs")
        calls["reused"].append({"axis_id": row["axis_id"], "receiver": receiver})
        return {k: copy.deepcopy(v) for k, v in row.items() if k not in {"axis_id", "receiver", "grain_axis_xyz", "finished_full_wall_intervals_from_axis_point_mm"}}

    return query, body_names, calls


def floor_observations(p, bodies, q):
    rows = []
    for expected in p["floor_descriptors"]:
        points = [list(point) for point in q.floor.level_face_points(bodies[expected["host"]], True)]
        require(len(points) == 4 and all(len(x) == 3 and all(math.isfinite(v) for v in x) for x in points), "four finite own floor corners required")
        reference = expected["normal_reference_points_xyz_mm"]
        require(all(sum(math.dist(x, y) < 1e-5 for y in points) == 1 for x in reference), "own current floor face differs from reviewed translation")
        rows.append({**expected, "observed_normal_reference_points_xyz_mm": points,
                     "own_floor_face_confirmed_from_current_cached_solid": True})
    return rows


def export_native(manifest, manifest_sha, slot_path, slot_sha):
    require(os.environ.get("EOERE_PARENT_SERIALIZED_EXTRACTION") == "1", "parent serialized extraction marker required before source/native extraction")
    p, old, report, panels, pins = prepare(manifest, manifest_sha)
    serial_slot = slot(slot_path, slot_sha, p["geometry"]["sha256"])
    ex, m = a.generic()
    q = ex.load_query_methods(pins)
    bodies, observations, import_proof = import_current(ex, report, panels, pins, q)
    profiles = {r["name"]: r for r in p["gross_raw_timber_rows"]}
    query, names, wall_proof = wall_cache(ex, old, report, observations, profiles, q, m)
    names.update({id(body): name for name, body in bodies.items()})
    with patch.object(q.bore, "finished_bore_wall_intervals", query):
        shafts, walls = ex.shafts(report, profiles, bodies, q, m)
    patches, direct, pair_census, faces = ex.contact_bank(bodies, sorted(profiles), old["panel_ids"], q, p["parameters"])
    domains, flange_patches, flange_contacts = ex.flange_bank(p["fitting_poses"], report, bodies, faces, q, m, p["parameters"])
    floors = floor_observations(p, bodies, q)
    owner_rows = [{"id": r["id"], "kind": "panel" if r["id"] in old["panel_ids"] else "timber",
                   "mass_kg": r["volume_mm3"]*p["parameters"]["wood_density_kg_m3"]*1e-9,
                   "center_xyz_mm": r["center_xyz_mm"], "mass_basis": "current finished volume at unchanged declared wood density"} for r in observations]
    old_owners = {r["id"]: r for r in old["physical_owner_gravity_rows"]}
    owner_rows += [{"id": pose["id"], "kind": "fitting", "mass_kg": old_owners[pose["id"]]["mass_kg"],
                    "center_xyz_mm": ex.fitting_centroid(report["scenario"], pose, m),
                    "mass_basis": "unchanged catalog mass and nominal sharp holed-angle centroid"} for pose in p["fitting_poses"]]
    for shaft in shafts:
        roles = shaft["metal_roles"]
        mass = sum(r["mass_kg"] for r in roles)
        owner_rows.append({"id": shaft["body"], "kind": "shaft", "mass_kg": mass,
                           "center_xyz_mm": [sum(r["mass_kg"]*r["center_of_mass_xyz_mm"][j] for r in roles)/mass for j in range(3)],
                           "gravity_route": "five separate own nominal metal-role loads; no duplicate owner selfweight"})
    require(len(owner_rows) == len({r["id"] for r in owner_rows}) == 150 and len(domains) == 88, "all150 owners/all88 flange domains required")
    a.verify(pins)
    return {"schema": "eoere_adjusted_base_cached_source_export/v1", "status": "CURRENT_DESCRIPTORS_PENDING_PARENT_INPUT_REVIEW_AND_BRIDGE",
            "source_sha256": pins, "source_pins_before_after_unchanged": True, "geometry": p["geometry"],
            "serial_slot_at_start": serial_slot, "pinned_query_versions": q.versions,
            "finished_body_observations": observations, "import_proof": import_proof,
            "raw_gross_timber_rows": p["gross_raw_timber_rows"], "fitting_poses": p["fitting_poses"],
            "fitting_ports": p["fitting_ports"], "all_factory_holes": p["all_factory_holes"],
            "shafts": shafts, "finished_receiver_wall_queries": walls, "wall_query_proof": wall_proof,
            "physical_owner_gravity_rows": owner_rows, "auxiliary_metal_gravity_descriptors": p["auxiliary_metal_gravity_descriptors"],
            "hillman_rows": p["hillman_rows"], "current_panel_machining_descriptors": p["current_panel_machining_descriptors"],
            "timber_and_panel_shared_face_patches": patches, "shared_pair_query_census": pair_census,
            "flange_domains": domains, "flange_shared_face_patches": flange_patches,
            "direct_contacts": direct+flange_contacts, "floor_observations": floors,
            "fresh_contact_domains_not_copied_from_old_field": True,
            "native_nominal_flat_reference_flange_masks_created": 88,
            "candidate_CAD_rebuild_mesh_K_assembly_factorization_q_forces_load_cases_or_native_solve_performed": False,
            "native_cached_solid_queries_performed": True, "input_schema_or_mechanics_admission_bridge_claimed": False,
            "remaining": ["Three changed panel K/mass/screw-port refresh", "Genuine fresh full-case loads", "Parent input/method/readiness/field/admission bridge"],
            "release": p["release"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--slot", type=Path)
    parser.add_argument("--slot-sha256")
    args = parser.parse_args()
    require(not args.out.exists(), "preserve prior descriptor output")
    start = time.monotonic()
    result = export_native(args.manifest, args.manifest_sha256, args.slot, args.slot_sha256) if args.extract else source_plan(args.manifest, args.manifest_sha256)
    result["execution"] = {"command": list(sys.orig_argv), "elapsed_seconds": time.monotonic()-start}
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.out), "schema": result["schema"]}))


if __name__ == "__main__":
    main()
