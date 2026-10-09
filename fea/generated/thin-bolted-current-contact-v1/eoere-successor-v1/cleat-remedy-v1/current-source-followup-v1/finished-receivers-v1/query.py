"""Four-host finished-receiver query for the unadopted Z180 proposal.

Reuses the authenticated bore, cylindrical-wall, annular-backing and strict
single-solid methods. No frame assembly, meshes, mechanics or adoption.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import math
import platform
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
RELEASE = dict.fromkeys(("geometry_adopted", "mechanics_ready", "capacity_established",
                         "fabrication_released", "structural_released", "climbing_released"), False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    def reject(value):
        raise ValueError("nonfinite JSON: " + value)
    return json.loads(Path(path).read_bytes(), parse_constant=reject)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "source changed: " + path)


def module(ref, name):
    require(sha(ROOT / ref["path"]) == ref["sha256"], "authenticated helper required")
    spec = importlib.util.spec_from_file_location(name, ROOT / ref["path"])
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    require(sha(ROOT / ref["path"]) == ref["sha256"], "helper changed during import")
    return loaded


def write(path, value):
    with path.open("xb") as stream:
        stream.write((json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n").encode())


def preflight(permit_path, fixtures_only):
    """Reject stale sources/authority before importing any native query module."""
    require(not any(n == "cadquery" or n == "OCP" or n.startswith("OCP.") for n in sys.modules), "fresh pre-native process required")
    permit = read(permit_path)
    require(permit["schema"] == "eoere_four_receiver_geometry_query_parent_readiness/v1", "distinct geometry readiness required")
    require(permit["fixtures_authorized"] is True and permit["candidate_query_authorized"] is (not fixtures_only), "mode not authorized by parent")
    require(all(v is False for v in permit["release"].values()) and permit["release"] == RELEASE, "release must remain false")
    require(permit["query"] == {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)}, "query source differs from readiness")
    inp_path = HERE / "inputs.json"
    require(permit["inputs"] == {"path": str(inp_path.relative_to(ROOT)), "sha256": sha(inp_path)}, "input source differs from readiness")
    inp = read(inp_path)
    pins = {**inp["source_sha256"], **{r["path"]: r["sha256"] for r in (permit["query"], permit["inputs"])}}
    require(inp["schema"] == "eoere_four_finished_receiver_query_inputs/v1" and inp["current_revision"] == "eoere-base-side-edge-cleats-v1", "input scope differs")
    require(inp["optional_2026_extra"] is False and inp["release"] == RELEASE, "input release/scope differs")
    require(inp["scenarios"] == ["current_Z200_modeled", "proposed_Z180_modeled", "proposed_Z180_all11p1125"], "exact three local scenarios required")
    runtime = {"python": platform.python_version(), **{n: importlib.metadata.version(n) for n in ("cadquery", "cadquery-ocp")}}
    require(runtime == inp["runtime"], "pinned native query runtime required")
    for ref in permit.get("prerequisite_results", []):
        require(ref["path"] not in pins or pins[ref["path"]] == ref["sha256"], "conflicting prerequisite pin")
        pins[ref["path"]] = ref["sha256"]
    if not fixtures_only:
        require(bool(permit["prerequisite_results"]), "candidate query requires method fixtures")
        fixture = read(ROOT / permit["prerequisite_results"][0]["path"])
        require(fixture["schema"] == "eoere_four_receiver_native_method_fixtures/v1" and fixture["pass"] is True,
                "passing exact method fixtures required")
        require(fixture["query_sha256"] == sha(OWN) and fixture["inputs_sha256"] == sha(inp_path), "fixture source binding differs")
    verify(pins)
    return inp, pins, permit, runtime


def methods(inp):
    import cadquery as cq

    loader = module(inp["helpers"]["pure_loader"], "four_receiver_pure_loader")
    pins = inp["source_sha256"]
    refs = inp["helpers"]
    load = loader.pinned_functions
    overlap = load(refs["overlap"]["path"], ["overlaps"], pins, {"cq": cq})["overlaps"]
    brep = load(refs["brep"]["path"], ["brep_sha"], pins, {"io": io, "hashlib": hashlib})["brep_sha"]
    strict = load(refs["strict_solid"]["path"], ["strict_solid", "wrapper_fixture"], pins)
    return SimpleNamespace(cq=cq, overlaps=overlap, brep_sha=brep, **strict,
                           bore_wood=load(refs["bore"]["path"], ["bore_wood"], pins, {"cq": cq})["bore_wood"],
                           wall=load(refs["wall"]["path"], ["finished_bore_wall_intervals"], pins)["finished_bore_wall_intervals"],
                           annulus=load(refs["annulus"]["path"], ["annular_backing"], pins,
                                        {"cq": cq, "shared": SimpleNamespace(overlaps=overlap)})["annular_backing"])


def method_fixtures(q):
    """Native toy solids only; candidate path imports are forbidden."""
    cq = q.cq
    with patch.object(cq.Shape, "importBrep", side_effect=AssertionError("candidate import forbidden in method fixtures")):
        raw = cq.Solid.makeBox(10., 20., 30.)
        axis = {"id": "toy", "point": cq.Vector(0, 10, 15), "direction": cq.Vector(1, 0, 0),
                "bore_diameter_mm": 3., "grip_mm": 10., "receivers": ["toy"]}
        finished = q.bore_wood({"toy": raw}, [axis])["toy"]
        wall = q.wall(finished, axis["point"], axis["direction"], 1.5)
        require(abs(wall["full_wall_length_mm"]-10.) < 1e-9 and not wall["partial_wall_present"], "full wall fixture failed")
        missing_rejected = False
        try:
            q.wall(finished, axis["point"], axis["direction"], 1.6)
        except ValueError:
            missing_rejected = True
        require(missing_rejected, "wrong own radius accepted")
        backing = q.annulus(8., 4., axis["point"], axis["direction"], [finished])
        require(abs(backing-1.) < 1e-9, "full annulus fixture failed")
        # Moving the ring to a stock edge must expose missing support.
        edge_backing = q.annulus(8., 4., cq.Vector(0, 0, 15), axis["direction"], [finished])
        require(abs(edge_backing-.5) < 1e-9, "half annulus fixture failed")
        partial_raw = cq.Solid.makeBox(100., 139.7, 38.1)
        p, g = cq.Vector(50., 69.85, 0), cq.Vector(0, 0, 1)
        partial = partial_raw.cut(cq.Solid.makeCylinder(14.2875/2, 38.1, p)).cut(
            cq.Solid.makeBox(50., 139.7, 10., cq.Vector(0, 0, 10.))).clean()
        partial_wall = q.wall(partial, p, g, 14.2875/2)
        require(partial_wall["partial_wall_present"] and partial_wall["full_wall_intervals_mm"] == []
                and partial_wall["full_wall_length_mm"] == 0., "partial wall promoted to full wall")
        solid, wrapped = q.wrapper_fixture(q)
        canonical_shape, strict_record = q.strict_solid(wrapped, q)
        expected_center = [13.+2.*math.cos(math.pi/6)-3.*math.sin(math.pi/6),
                           18.+2.*math.sin(math.pi/6)+3.*math.cos(math.pi/6), 39.]
        require(abs(canonical_shape.Volume()-192.) < 1e-9 and math.dist(canonical_shape.Center().toTuple(), expected_center) < 1e-10
                and strict_record["compound_wrapper_count"] == 2, "strict location/orientation fixture failed")
        sibling_rejected = False
        try:
            q.strict_solid(cq.Compound.makeCompound([solid, solid.Faces()[0]]), q)
        except ValueError:
            sibling_rejected = True
        require(sibling_rejected, "extra sibling silently dropped")
    return {"full_wall": wall, "wrong_radius_rejected": missing_rejected, "full_annulus_fraction": backing,
            "half_annulus_fraction": edge_backing, "partial_wall": partial_wall,
            "strict_nested_location_orientation": strict_record, "extra_face_sibling_rejected": sibling_rejected,
            "candidate_BREP_imports": 0, "known_answer_or_negative_checks": 7}


def source_inventory(inp):
    analytic = module(inp["helpers"]["analytic_inventory"], "four_receiver_analytic_inventory")
    bound_input = read(ROOT / inp["analytic_inputs"]["path"])
    data = {k: read(ROOT / ref["path"]) for k, ref in bound_input["sources"].items() if ref["path"].endswith(".json")}
    datum = module(bound_input["sources"]["datum_helper"], "four_receiver_datum")
    axes, proposed, members, own_cuts = analytic.existing_inventory(bound_input, data, datum)
    prior = read(ROOT / inp["analytic_result"]["path"])
    require(members == prior["affected_members"] and list(proposed.values()) == prior["proposed_axes"], "analytic source inventory differs")
    require(set(members) == set(inp["receivers"]) and set(proposed) == set(inp["axis_ids"]), "exact four-host/axis scope required")
    return data["geometry"], axes, proposed, members, own_cuts


def bounds(shape):
    box = shape.BoundingBox()
    return [[getattr(box, a+"min"), getattr(box, a+"max")] for a in "xyz"]


def close_bounds(actual, expected, tolerance):
    require(max(abs(a-b) for aa, bb in zip(actual, expected, strict=True) for a, b in zip(aa, bb, strict=True)) < tolerance, "receiver bounds differ")


def reconstruct(inp, members, q):
    raw, records = {}, {}
    manifest = read(ROOT / inp["raw_post_manifest"]["path"])
    raw_post_records = {r["member"]: r for r in manifest["raw_parts"] if r["member"] in inp["raw_post_sources"]}
    require(set(raw_post_records) == set(inp["raw_post_sources"]), "two authentic raw post records required")
    for name, row in members.items():
        xlo, xhi = row["X_interval_mm"]
        if name in inp["raw_post_sources"]:
            ref = inp["raw_post_sources"][name]
            require(all(raw_post_records[name][k] == ref[k] for k in ("path", "sha256")), "raw post manifest binding differs")
            shape = q.cq.Shape.importBrep(str(ROOT / ref["path"]))
            recipe = "authenticated raw post BREP, no further coordinate shift"
        else:
            shape = q.cq.Workplane("YZ", origin=(xlo, 0, 0)).polyline(row["YZ_polygon_mm"]).close().extrude(xhi-xlo).val()
            recipe = "exact current sloping YZ profile, straight full-thickness X extrusion"
        shape, strict = q.strict_solid(shape, q)
        polygon = row["YZ_polygon_mm"]
        expected_bounds = [row["X_interval_mm"], [min(p[0] for p in polygon), max(p[0] for p in polygon)],
                           [min(p[1] for p in polygon), max(p[1] for p in polygon)]]
        close_bounds(bounds(shape), expected_bounds, inp["tolerances"]["coordinate_mm"])
        require(abs(shape.Volume()-row["raw_volume_mm3"]) < inp["tolerances"]["volume_mm3"], "raw source volume differs")
        raw[name] = shape
        records[name] = {"recipe": recipe, "strict_solid": strict, "bounds_xyz_mm": bounds(shape), "volume_mm3": shape.Volume()}
    return raw, records


def local_axes(geometry, proposed, hosts, q, *, scenario):
    selected = []
    for axis in geometry["axes"]:
        own_hosts = [n for n in axis["receivers"] if n in hosts]
        if not own_hosts:
            continue
        a = copy.deepcopy(proposed.get(axis["id"], axis) if scenario != "current_Z200_modeled" else axis)
        a["receivers"] = own_hosts
        if scenario == "proposed_Z180_all11p1125":
            a["bore_diameter_mm"] = 11.1125
        a["point"], a["direction"] = q.cq.Vector(*a["point_xyz_mm"]), q.cq.Vector(*a["direction_xyz"])
        selected.append(a)
    require(len(selected) == 12 and sum(len(a["receivers"]) for a in selected) == 16, "local12axis/16receiver census differs")
    return selected


def query_scenario(inp, scenario, raw, members, axes, out, q):
    finished = q.bore_wood(raw, axes)
    body_records, wall_records, seats, baseline = {}, [], [], []
    for name, shape in finished.items():
        shape, strict = q.strict_solid(shape, q)
        require(shape.isValid(), "finished receiver invalid")
        path = out / (name+".brep")
        require(not path.exists() and shape.exportBrep(str(path)), "fresh receiver BREP export failed")
        restored, roundtrip = q.strict_solid(q.cq.Shape.importBrep(str(path)), q)
        close_bounds(bounds(restored), bounds(shape), inp["tolerances"]["coordinate_mm"])
        require(abs(shape.Volume()-restored.Volume()) < inp["tolerances"]["volume_mm3"], "roundtrip volume differs")
        # Observations are made on the exported/reimported finished body.
        finished[name] = restored
        row = members[name]
        own = [a for a in axes if name in a["receivers"]]
        expected_volume = row["raw_volume_mm3"]-sum(math.pi*(a["bore_diameter_mm"]/2)**2*row["thickness_mm"] for a in own)
        require(abs(restored.Volume()-expected_volume) < inp["tolerances"]["volume_mm3"], "finished raw-minus-four-bores volume differs")
        body_records[name] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "bytes": path.stat().st_size,
                              "volume_mm3": restored.Volume(), "raw_minus_four_bores_volume_error_mm3": restored.Volume()-expected_volume,
                              "bounds_xyz_mm": bounds(restored), "strict_solid_before_export": strict, "strict_solid_after_import": roundtrip}
        if scenario == "current_Z200_modeled":
            original, original_record = q.strict_solid(q.cq.Shape.importBrep(str(ROOT / row["finished_source"]["path"])), q)
            overlap = q.overlaps(original, restored)
            missing, added = max(0., original.Volume()-overlap), max(0., restored.Volume()-overlap)
            close_bounds(bounds(original), bounds(restored), inp["tolerances"]["coordinate_mm"])
            require(max(missing, added) < inp["tolerances"]["boolean_volume_mm3"], "current reconstruction Boolean volume comparison failed")
            baseline.append({"receiver": name, "original": row["finished_source"], "original_strict_solid": original_record,
                             "reconstructed_missing_volume_mm3": missing, "reconstructed_added_volume_mm3": added,
                             "comparison": "symmetric Boolean volume and bounds within declared tolerances, not byte identity"})
    for a in axes:
        for name in a["receivers"]:
            row = members[name]
            wall = q.wall(finished[name], a["point"], a["direction"], a["bore_diameter_mm"]/2)
            expected_interval = sorted(a["direction_xyz"][0]*(x-a["point_xyz_mm"][0]) for x in row["X_interval_mm"])
            require(len(wall["full_wall_intervals_mm"]) == 1 and not wall["partial_wall_present"], "continuous full bore wall not observed")
            close_bounds([wall["full_wall_intervals_mm"][0]], [expected_interval], inp["tolerances"]["coordinate_mm"])
            require(abs(wall["full_wall_length_mm"]-row["thickness_mm"]) < inp["tolerances"]["coordinate_mm"], "finished wall length differs")
            wall_records.append({"axis_id": a["id"], "receiver": name, "changed_axis": a["id"] in inp["axis_ids"],
                                 "query_point_xyz_mm": a["point_xyz_mm"], "query_direction_xyz": a["direction_xyz"],
                                 "bore_diameter_mm": a["bore_diameter_mm"], "expected_own_interval_mm": expected_interval, **wall})
            h = a["hardware_scenario"]
            for end, station, sign in (("head", 0., 1), ("nut", a["grip_mm"], -1)):
                point = a["point"]+a["direction"].multiply(station)
                inward = a["direction"].multiply(sign)
                face_x = row["X_interval_mm"][0 if inward.x > 0 else 1]
                if abs(point.x-face_x) >= inp["tolerances"]["coordinate_mm"]:
                    continue
                fraction = q.annulus(h["washer_od_mm"], h["washer_id_mm"], point, inward, [finished[name]])
                require(abs(fraction-1.) < inp["tolerances"]["annular_fraction"], "own finished nominal annular seat incomplete")
                seats.append({"axis_id": a["id"], "receiver": name, "end": end, "changed_axis": a["id"] in inp["axis_ids"],
                              "support_point_xyz_mm": list(point.toTuple()), "inward_xyz": list(inward.toTuple()),
                              "nominal_washer_OD_mm": h["washer_od_mm"], "nominal_washer_ID_mm": h["washer_id_mm"],
                              "inward_skin_mm": .05, "single_own_host_targets": 1, "observed_backing_fraction": fraction,
                              "physical_contact_or_strength_qualified": False})
    require(len(wall_records) == len(seats) == 16 and sum(w["changed_axis"] for w in wall_records) == 8
            and sum(s["changed_axis"] for s in seats) == 8, "16own walls/seats with8changed occurrences required")
    return {"scenario": scenario, "void_policy": "four own bores per host from raw; replace eight current Z200 occurrences before applying Z180",
            "local_axes": [{k: v for k, v in a.items() if k not in ("point", "direction")} for a in axes],
            "finished_bodies": body_records, "wall_queries": wall_records, "annular_queries": seats,
            "current_finished_baseline_comparisons": baseline}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permit", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--fixtures-only", action="store_true")
    args = parser.parse_args()
    inp, pins, permit, runtime = preflight(args.permit, args.fixtures_only)
    out = args.outdir.resolve()
    require(out.parent == (HERE / "runs-v1").resolve() and not out.exists(), "fresh owned runs-v1 output directory required")
    permit_ref = {"path": str(args.permit.resolve().relative_to(ROOT)), "sha256": sha(args.permit)}
    pins[permit_ref["path"]] = permit_ref["sha256"]
    with Path("/tmp/moonboard-four-receiver-native-geometry.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        out.mkdir(parents=True, exist_ok=False)
        verify(pins)
        q = methods(inp)
        fixtures = (method_fixtures(q) if args.fixtures_only else
                    read(ROOT / permit["prerequisite_results"][0]["path"])["fixtures"])
        result = {"schema": "eoere_four_receiver_native_method_fixtures/v1", "pass": True,
                  "query_sha256": sha(OWN), "inputs_sha256": sha(HERE / "inputs.json"), "source_sha256": pins,
                  "runtime": runtime, "fixtures": fixtures, "parent_readiness": permit_ref, "release": RELEASE}
        if not args.fixtures_only:
            geometry, _, proposed, members, _ = source_inventory(inp)
            raw, raw_records = reconstruct(inp, members, q)
            scenarios = []
            for scenario in inp["scenarios"]:
                scenario_out = out / scenario
                scenario_out.mkdir(exist_ok=False)
                axes = local_axes(geometry, proposed, members, q, scenario=scenario)
                scenarios.append(query_scenario(inp, scenario, raw, members, axes, scenario_out, q))
            result = {"schema": "eoere_four_finished_receiver_observations/v1", "status": "UNADOPTED_LOCAL_FINISHED_GEOMETRY_OBSERVED",
                      "source_sha256": pins, "runtime": runtime, "parent_readiness": permit_ref, "method_fixtures": fixtures,
                      "current_revision": inp["current_revision"], "current100_axes_canonical_sha256": canonical(geometry["axes"]),
                      "current66_screws_canonical_sha256": canonical(geometry["screw_axes"]), "receivers": list(members),
                      "raw_receivers": raw_records, "scenarios": scenarios, "release": RELEASE,
                      "complete_joint_resistance": None, "geometry_or_shop_instructions_changed": False,
                      "candidate_native_FEA_or_global_solve": False, "saved_forces_reused_or_transferred": False,
                      "prior_native_method_fixtures_reused": True,
                      "limits": inp["limits"], "retention": "Raw finished BREP outputs remain active ignored inputs. No pruning or historical substitution."}
        verify(pins)
        result["sources_unchanged_before_after"] = True
        write(out / "result.json", result)
        verify(pins)
        print(json.dumps({"path": str((out / "result.json").relative_to(ROOT)), "sha256": sha(out / "result.json"),
                          "source_files": len(pins), "scenarios": len(result.get("scenarios", [])), "release": RELEASE}, sort_keys=True))


if __name__ == "__main__":
    main()
