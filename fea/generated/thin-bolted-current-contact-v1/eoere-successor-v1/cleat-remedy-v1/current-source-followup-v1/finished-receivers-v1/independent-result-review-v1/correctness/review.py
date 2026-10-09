"""Reusable stdlib consumer of the frozen candidate01 geometry observations."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
RESULT = PACKET/"runs-v1/candidate01/result.json"
RESULT_SHA = "6efea34ce52b3521da6d14b89853ef83ab9c1a1f7861c71f6410fc8db7738cb3"
QUERY_SHA = "88edea7a233963e32f6d56fc7fd0dd86322acc65f69bbefdd4f53cc01d919912"
PERMIT_SHA = "fce668182fcce2c36b02971b2f4ec1354844de2beb704e636c5e004f75be8a51"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes(), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))


def finite(value):
    if isinstance(value, float):
        require(math.isfinite(value), "nonfinite observation")
    elif isinstance(value, list):
        for item in value:
            finite(item)
    elif isinstance(value, dict):
        for item in value.values():
            finite(item)


def close(actual, expected, tolerance, label):
    if isinstance(expected, (tuple, list)):
        require(len(actual) == len(expected), label+" dimensions differ")
        for a, b in zip(actual, expected, strict=True):
            close(a, b, tolerance, label)
    else:
        require(abs(actual-expected) < tolerance, label+" differs")


def indexed(rows, keys, label):
    result = {tuple(row[k] for k in keys): row for row in rows}
    require(len(result) == len(rows), label+" duplicate keys")
    return result


def strict(record):
    require(record["schema"] == "thin_bolted_strict_single_child_solid_container/v2"
            and record["iterator_cumLoc"] is True and record["iterator_cumOri"] is True
            and record["original_wrapper_unchanged"] is True and record["extra_geometry_dropped"] is False
            and record["location_or_orientation_reset"] is False, "strict-solid qualification flags differ")
    nodes = record["nodes"]
    require(nodes and record["compound_wrapper_count"] == len(nodes)-1
            and nodes[-1]["shape_type"] == "TopAbs_ShapeEnum.TopAbs_SOLID"
            and all(n["shape_type"] == "TopAbs_ShapeEnum.TopAbs_COMPOUND" and n["immediate_children"] == 1
                    for n in nodes[:-1]), "strict-solid transparent chain differs")
    require(record["original_imported_topology_counts"] == record["canonical_solid_topology_counts"]
            and record["canonical_solid_topology_counts"]["solids"] == 1
            and record["original_imported_serialized_brep_sha256"] == nodes[0]["native_serialized_brep_sha256"]
            and record["canonical_solid_serialized_brep_sha256"] == nodes[-1]["native_serialized_brep_sha256"],
            "strict-solid metadata closure differs")


def context():
    """Load only authenticated stdlib adapter/intake; never call native methods."""
    path = PACKET/"query-v2.py"
    require(sha(path) == QUERY_SHA, "frozen v2 query changed")
    spec = importlib.util.spec_from_file_location("saved_result_query_v2_source_only", path)
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    query = wrapper.load_adapter()
    permit_path = PACKET/"parent-candidate-readiness-v2.json"
    require(sha(permit_path) == PERMIT_SHA, "candidate permit changed")
    inp, pins, permit, runtime = query.preflight(permit_path, False)
    pins[str(permit_path.relative_to(ROOT))] = PERMIT_SHA
    require(len(pins) == 46, "46 direct source pins required")
    geometry, axes, proposed, members, cuts = query.source_inventory(inp)
    require((len(axes), len(geometry["screw_axes"]), len(proposed), len(members), sum(map(len, cuts.values())))
            == (100, 66, 4, 4, 16), "current intake census differs")
    fixture = read(ROOT/permit["prerequisite_results"][0]["path"])
    reviews = permit["prerequisite_results"][1:]
    require(len(reviews) == 3 and all(read(ROOT/r["path"])["findings"] == [] for r in reviews),
            "three frozen clean method review receipts required")
    query.verify(pins)
    return {"query": query, "inputs": inp, "pins": pins, "permit": permit, "permit_path": permit_path,
            "runtime": runtime, "geometry": geometry, "axes": axes, "members": members, "fixture": fixture}


def evaluate(result, bound=None, *, verify_files=True):
    """Check saved arithmetic/identity and optional raw bytes; does not query BREP."""
    bound = context() if bound is None else bound
    query, inp, geometry, members = (bound[k] for k in ("query", "inputs", "geometry", "members"))
    finite(result)
    require(result["schema"] == "eoere_four_finished_receiver_observations/v1"
            and result["status"] == "UNADOPTED_LOCAL_FINISHED_GEOMETRY_OBSERVED"
            and result["current_revision"] == inp["current_revision"]
            and result["runtime"] == bound["runtime"] and result["source_sha256"] == bound["pins"],
            "saved source/scope binding differs")
    require(result["parent_readiness"] == {"path": str(bound["permit_path"].relative_to(ROOT)), "sha256": PERMIT_SHA}
            and result["method_fixtures"] == bound["fixture"]["fixtures"]
            and result["prior_native_method_fixtures_reused"] is True
            and result["sources_unchanged_before_after"] is True, "saved method/readiness binding differs")
    require(result["current100_axes_canonical_sha256"] == query.canonical(geometry["axes"])
            and result["current66_screws_canonical_sha256"] == query.canonical(geometry["screw_axes"]),
            "current100/66 identity differs")
    require(result["release"] == query.RELEASE and all(v is False for v in result["release"].values())
            and result["complete_joint_resistance"] is None
            and all(result[k] is False for k in ("candidate_native_FEA_or_global_solve",
                    "geometry_or_shop_instructions_changed", "saved_forces_reused_or_transferred")),
            "release/force/capacity boundary differs")
    require(result["limits"] == inp["limits"]
            and result["retention"] == "Raw finished BREP outputs remain active ignored inputs. No pruning or historical substitution.",
            "saved geometry/retention limits differ")
    require(result["receivers"] == list(members) and set(result["raw_receivers"]) == set(members),
            "raw receiver census differs")
    tolerance = inp["tolerances"]
    expected_bounds = {}
    for name, row in members.items():
        polygon = row["YZ_polygon_mm"]
        box = [row["X_interval_mm"], [min(p[0] for p in polygon), max(p[0] for p in polygon)],
               [min(p[1] for p in polygon), max(p[1] for p in polygon)]]
        expected_bounds[name] = box
        raw = result["raw_receivers"][name]
        close(raw["bounds_xyz_mm"], box, tolerance["coordinate_mm"], "raw bounds")
        close(raw["volume_mm3"], row["raw_volume_mm3"], tolerance["volume_mm3"], "raw volume")
        strict(raw["strict_solid"])
        require(raw["recipe"] == ("authenticated raw post BREP, no further coordinate shift"
                if name in inp["raw_post_sources"] else "exact current sloping YZ profile, straight full-thickness X extrusion"),
                "raw source coordinate recipe differs")
    require([s["scenario"] for s in result["scenarios"]] == inp["scenarios"], "exact three scenario views required")
    exports, summaries, max_area_error, max_boolean_gap = {}, [], 0., 0.
    for scenario in result["scenarios"]:
        label = scenario["scenario"]
        expected_axes = []
        for source in geometry["axes"]:
            receivers = [n for n in source["receivers"] if n in members]
            if not receivers:
                continue
            axis = copy.deepcopy(source)
            axis["receivers"] = receivers
            if label != "current_Z200_modeled" and axis["id"] in inp["axis_ids"]:
                axis["point_xyz_mm"][2] = 180.
            if label == "proposed_Z180_all11p1125":
                axis["bore_diameter_mm"] = 11.1125
            expected_axes.append(axis)
        require(scenario["local_axes"] == expected_axes and len(expected_axes) == 12
                and sum(len(a["receivers"]) for a in expected_axes) == 16, "local scenario axis view differs")
        require(scenario["void_policy"] == "four own bores per host from raw; replace eight current Z200 occurrences before applying Z180",
                "void replacement policy differs")
        require(set(scenario["finished_bodies"]) == set(members), "four finished bodies required")
        for name, body in scenario["finished_bodies"].items():
            path = str((RESULT.parent/label/(name+".brep")).relative_to(ROOT))
            require(body["path"] == path and path not in exports and body["bytes"] > 0, "export identity differs")
            exports[path] = {"sha256": body["sha256"], "bytes": body["bytes"]}
            own = [a for a in expected_axes if name in a["receivers"]]
            require(len(own) == 4, "four own cuts per finished receiver required")
            expected_volume = members[name]["raw_volume_mm3"]-sum(
                math.pi*(a["bore_diameter_mm"]/2)**2*members[name]["thickness_mm"] for a in own)
            error = body["volume_mm3"]-expected_volume
            close(body["raw_minus_four_bores_volume_error_mm3"], error, 1e-9, "raw-minus-bores error")
            require(abs(error) < tolerance["volume_mm3"], "raw-minus-four-bores volume fails")
            close(body["bounds_xyz_mm"], expected_bounds[name], tolerance["coordinate_mm"], "finished bounds")
            for key in ("strict_solid_before_export", "strict_solid_after_import"):
                strict(body[key])
                require(body[key]["canonical_solid_topology_counts"] == members[name]["cached_topology_counts"],
                        "finished topology census differs")
            require(body["strict_solid_before_export"]["canonical_solid_serialized_brep_sha256"]
                    == body["strict_solid_after_import"]["canonical_solid_serialized_brep_sha256"],
                    "canonical export/reimport metadata differs")
        walls = indexed(scenario["wall_queries"], ("axis_id", "receiver"), "own walls")
        seats = indexed(scenario["annular_queries"], ("axis_id", "receiver", "end"), "own annuli")
        expected_wall_keys, expected_seat_keys = set(), set()
        for axis in expected_axes:
            for name in axis["receivers"]:
                key = (axis["id"], name)
                expected_wall_keys.add(key)
                wall = walls[key]
                point, direction = axis["point_xyz_mm"], axis["direction_xyz"]
                interval = sorted(direction[0]*(x-point[0]) for x in members[name]["X_interval_mm"])
                require(wall["query_point_xyz_mm"] == point and wall["query_direction_xyz"] == direction
                        and wall["bore_diameter_mm"] == axis["bore_diameter_mm"]
                        and wall["changed_axis"] is (axis["id"] in inp["axis_ids"]), "wall source identity differs")
                close(wall["expected_own_interval_mm"], interval, tolerance["coordinate_mm"], "own interval")
                full, partial = [], False
                require(wall["matching_cylindrical_faces"], "matching own cylindrical face absent")
                for face in wall["matching_cylindrical_faces"]:
                    low, high = face["interval_mm"]
                    require(high > low+1e-6, "degenerate own cylindrical face")
                    theoretical = math.pi*axis["bore_diameter_mm"]*(high-low)
                    area_error = abs(face["full_cylinder_area_mm2"]-theoretical)
                    max_area_error = max(max_area_error, area_error)
                    require(area_error < 1e-8, "full-cylinder theoretical area differs")
                    fraction = face["wall_area_mm2"]/theoretical
                    close(face["circumference_integral_fraction"], fraction, 1e-12, "cylinder area fraction")
                    is_full = abs(fraction-1.) <= 1e-6
                    require(face["full_circumference_wall"] is is_full, "full circumference flag differs")
                    partial |= not is_full
                    if is_full:
                        full.append([low, high])
                merged = []
                for low, high in sorted(full):
                    if merged and low <= merged[-1][1]+1e-6:
                        merged[-1][1] = max(merged[-1][1], high)
                    else:
                        merged.append([low, high])
                close(wall["full_wall_intervals_mm"], merged, tolerance["coordinate_mm"], "reported full intervals")
                close(merged, [interval], tolerance["coordinate_mm"], "finished own full interval")
                length = sum(high-low for low, high in merged)
                close(wall["full_wall_length_mm"], length, tolerance["coordinate_mm"], "full wall length")
                close(length, members[name]["thickness_mm"], tolerance["coordinate_mm"], "own thickness")
                require(wall["partial_wall_present"] is partial and not partial
                        and wall["qualified_directional_bearing_length_mm"] is None, "wall bearing qualification differs")
                for end, station, sign in (("head", 0., 1), ("nut", axis["grip_mm"], -1)):
                    support = [p+d*station for p, d in zip(point, direction, strict=True)]
                    inward = [d*sign for d in direction]
                    face_x = members[name]["X_interval_mm"][0 if inward[0] > 0 else 1]
                    if abs(support[0]-face_x) >= tolerance["coordinate_mm"]:
                        continue
                    seat_key = (axis["id"], name, end)
                    expected_seat_keys.add(seat_key)
                    seat = seats[seat_key]
                    close(seat["support_point_xyz_mm"], support, tolerance["coordinate_mm"], "seat support point")
                    require(seat["inward_xyz"] == inward and seat["changed_axis"] is (axis["id"] in inp["axis_ids"])
                            and axis["before_plate_mm" if end == "head" else "after_plate_mm"] == 0,
                            "own external wood-seat orientation/ownership differs")
                    h = axis["hardware_scenario"]
                    require(seat["nominal_washer_OD_mm"] == h["washer_od_mm"]
                            and seat["nominal_washer_ID_mm"] == h["washer_id_mm"]
                            and seat["inward_skin_mm"] == .05 and seat["single_own_host_targets"] == 1
                            and seat["physical_contact_or_strength_qualified"] is False,
                            "nominal one-host annular scenario differs")
                    require(abs(seat["observed_backing_fraction"]-1.) < tolerance["annular_fraction"],
                            "nominal own annulus incompletely backed")
        require(set(walls) == expected_wall_keys and set(seats) == expected_seat_keys
                and len(walls) == len(seats) == 16
                and sum(w["changed_axis"] for w in walls.values()) == 8
                and sum(s["changed_axis"] for s in seats.values()) == 8, "own wall/annulus census differs")
        baseline = indexed(scenario["current_finished_baseline_comparisons"], ("receiver",), "current baseline")
        require(set(baseline) == ({(n,) for n in members} if label == "current_Z200_modeled" else set()),
                "current-only four baseline comparisons required")
        for (name,), comparison in baseline.items():
            original = members[name]["finished_source"]
            require(comparison["original"] == original and comparison["comparison"]
                    == "symmetric Boolean volume and bounds within declared tolerances, not byte identity",
                    "baseline source/claim differs")
            strict(comparison["original_strict_solid"])
            close(scenario["finished_bodies"][name]["bounds_xyz_mm"], original["bounds_xyz_mm"],
                  tolerance["coordinate_mm"], "baseline bounds")
            missing, added = (comparison[k] for k in ("reconstructed_missing_volume_mm3", "reconstructed_added_volume_mm3"))
            require(0 <= missing < tolerance["boolean_volume_mm3"]
                    and 0 <= added < tolerance["boolean_volume_mm3"], "baseline Boolean volume exceeds tolerance")
            close(missing-added, original["volume_mm3"]-scenario["finished_bodies"][name]["volume_mm3"],
                  tolerance["boolean_volume_mm3"], "baseline Boolean volume consistency")
            max_boolean_gap = max(max_boolean_gap, missing, added)
        summaries.append({"scenario": label, "axes": 12, "bodies": 4, "walls": 16, "seats": 16,
                          "changed_wall_occurrences": 8, "changed_seat_occurrences": 8})
    require(len(exports) == 12, "12 unique exported files required")
    if verify_files:
        query.verify(bound["pins"])
        for path, ref in exports.items():
            require(sha(ROOT/path) == ref["sha256"] and (ROOT/path).stat().st_size == ref["bytes"],
                    "export byte hash/size differs")
        for row in members.values():
            ref = row["finished_source"]
            require((ROOT/ref["path"]).stat().st_size == ref["bytes"], "baseline source byte count differs")
    require(not any(n == "cadquery" or n == "OCP" or n.startswith("OCP.") for n in sys.modules),
            "native initializer imported by saved-result review")
    return {"pass": True, "source_files": 46, "export_files": 12, "export_bytes": sum(r["bytes"] for r in exports.values()),
            "export_sha256": {p: r["sha256"] for p, r in exports.items()}, "scenarios": summaries,
            "wall_observations": 48, "annular_observations": 48, "maximum_theoretical_area_error_mm2": max_area_error,
            "maximum_saved_baseline_boolean_gap_mm3": max_boolean_gap}


def main():
    require(sha(RESULT) == RESULT_SHA, "exact frozen candidate result required")
    bound = context()
    result = read(RESULT)
    audit = evaluate(result, bound)
    controls = []
    changes = [
        ("current_axis_identity", lambda r: r.__setitem__("current100_axes_canonical_sha256", "0"*64)),
        ("duplicate_wall_owner", lambda r: r["scenarios"][0]["wall_queries"].__setitem__(1, copy.deepcopy(r["scenarios"][0]["wall_queries"][0]))),
        ("retained_axis_move", lambda r: r["scenarios"][1]["local_axes"][0]["point_xyz_mm"].__setitem__(2, 180.)),
        ("wrong_wall_interval", lambda r: r["scenarios"][1]["wall_queries"][0]["full_wall_intervals_mm"][0].__setitem__(0, 0.)),
        ("wrong_cylinder_area", lambda r: r["scenarios"][2]["wall_queries"][0]["matching_cylindrical_faces"][0].__setitem__("full_cylinder_area_mm2", 1.)),
        ("wrong_annular_owner", lambda r: r["scenarios"][1]["annular_queries"][0].__setitem__("receiver", "base_post_outer_left")),
        ("multiple_host_annulus", lambda r: r["scenarios"][2]["annular_queries"][0].__setitem__("single_own_host_targets", 2)),
        ("false_backing", lambda r: r["scenarios"][0]["annular_queries"][0].__setitem__("observed_backing_fraction", .5)),
        ("bad_export_bytes", lambda r: r["scenarios"][0]["finished_bodies"]["eoere_cleat_left"].__setitem__("bytes", 1)),
        ("bad_baseline_boolean", lambda r: r["scenarios"][0]["current_finished_baseline_comparisons"][0].__setitem__("reconstructed_added_volume_mm3", .01)),
        ("force_transfer", lambda r: r.__setitem__("saved_forces_reused_or_transferred", True)),
        ("adoption", lambda r: r["release"].__setitem__("geometry_adopted", True)),
    ]
    for name, mutate in changes:
        changed = copy.deepcopy(result)
        mutate(changed)
        try:
            evaluate(changed, bound)
        except (ValueError, KeyError) as error:
            controls.append({"control": name, "rejection": str(error)})
        else:
            raise ValueError("mutation unexpectedly accepted: "+name)
    all_pins = {**bound["pins"], **audit["export_sha256"], str(RESULT.relative_to(ROOT)): RESULT_SHA}
    bound["query"].verify(all_pins)
    receipt = {
        "schema": "eoere_four_finished_receiver_candidate01_independent_correctness_saved_result_review/v1",
        "status": "NO_SUBSTANTIAL_FINDINGS_WITHIN_SAVED_RESULT_SCOPE", "findings": [],
        "result": {"path": str(RESULT.relative_to(ROOT)), "sha256": RESULT_SHA, "bytes": RESULT.stat().st_size},
        "review_helper_sha256": sha(OWN), "sources_unchanged_before_after": True,
        "files_rehashed_before_after": len(all_pins), "audit": audit, "negative_consumer_controls": controls,
        "reviewed_scope": [
            "46 exact direct pins include the immutable original/v2 query, inputs, candidate permit, toy result and three clean v2 method review receipts; all12 exported BREP byte hashes and byte counts checked without imports.",
            "Current100/66 canonical identities and source-only current inventory; independent three local views contain twelve axes/sixteen receiver occurrences and exactly four Z200-to-Z180 changes; all other axes/screws retained.",
            "Four raw profiles and twelve finished volume/bounds/strict-solid metadata records; all48 own cylindrical-face areas/fractions, merged full intervals, source points/directions/radii, full thickness and unqualified-bearing flags replayed.",
            "All48 unique external one-host nominal washer seats checked against exact source endpoint/inward direction, actual owning host face, no external plate, nominal OD/ID and complete saved backing; eight targeted/eight retained occurrences per scenario.",
            "Four current-only saved Boolean missing/added-volume/bounds comparisons remain below0.001mm3 tolerance; comparison wording explicitly excludes byte identity/general topology equivalence. False release/no force/capacity transfer and active-output retention remain exact.",
        ],
        "limits": [
            "Saved JSON/byte-hash arithmetic review only. No CAD/OCP/BREP import/query, geometry reconstruction, native toy/candidate rerun, FEA, frame/global solve, model edit or physical operation.",
            "Source-bound method receipts and native observations are reused; their geometric measurements are not independently regenerated. Export/reimport/strict-container evidence is audited as saved metadata and raw byte bindings.",
            "Current baseline is a numerical Boolean-volume-and-bounds comparison, not byte identity or a general topological-equivalence proof. Area matching retains the frozen method's1e-6 fractional/full-wall tolerance.",
            "Uniform11.1125 holes apply to all twelve local axis views/sixteen four-host occurrences only; washer dimensions remain nominal. Catalog corners, delivered parts, machining/installation tolerances and unmodeled screw pilots/countersinks remain outside scope.",
            "Full geometric walls/annuli do not qualify directional bearing, physical pressure/fit, complete joint capacity, changed-case forces, adoption, shop instructions, fabrication or climbing release.",
        ],
    }
    out = OWN.with_name("receipt.json")
    with out.open("x") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    bound["query"].verify(all_pins)
    print(json.dumps({"receipt": str(out.relative_to(ROOT)), "sha256": sha(out), "helper_sha256": sha(OWN),
                      "files": len(all_pins), "findings": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
