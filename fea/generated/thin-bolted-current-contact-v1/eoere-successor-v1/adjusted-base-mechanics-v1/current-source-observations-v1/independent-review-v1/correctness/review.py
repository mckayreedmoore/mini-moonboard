"""Review exact saved cached-source observations using metadata and stdlib only."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[8]
PACKET = OWN.parents[2]
OUTPUT = PACKET / "attempt01.json"
OUTPUT_SHA = "0f7e95f0dabfb5f0b5d63f8ef7d78e3c52c07672b4f482a89a89496eec703de7"
SLOT = Path("/tmp/moonboard-current-source-parent-slot.json")
SLOT_SHA = "292cbc1aa3f361450b676c3b15d835a82f2b210fee8707abc98e7601e9fa2c7b"
MANIFEST_SHA = "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6"
EXPORT_SHA = "93ed36c39b4237cd587498fbb9dd2b2b7e3d275afc2be89302dab178c25d5858"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def indexed(rows, key="id"):
    result = {row[key]: row for row in rows}
    assert len(rows) == len(result), key
    return result


def finite(value):
    if isinstance(value, (list, tuple)):
        return all(finite(item) for item in value)
    if isinstance(value, dict):
        return all(finite(item) for item in value.values())
    return not isinstance(value, (int, float)) or math.isfinite(value)


def close(a, b, tolerance=1e-5):
    return math.dist(a, b) < tolerance


def main():
    assert sha(OUTPUT) == OUTPUT_SHA and OUTPUT.stat().st_size == 11401385
    data = json.loads(OUTPUT.read_bytes())
    process_path = PACKET / "attempt01.process.json"
    process_sha = sha(process_path)
    process = json.loads(process_path.read_bytes())
    assert sha(SLOT) == SLOT_SHA
    slot = json.loads(SLOT.read_bytes())
    assert data["serial_slot_at_start"]["record_at_start"] == process["slot_at_start"] == slot
    assert data["serial_slot_at_start"]["sha256"] == process["slot_sha256"] == SLOT_SHA
    assert process["exit_code"] == 0 and process["output_sha256"] == OUTPUT_SHA
    assert slot["approved_exporter_sha256"] == EXPORT_SHA and slot["approved_manifest_sha256"] == MANIFEST_SHA
    assert slot["heavy_run_authorized_by_this_file"] is False
    assert finite(data)

    # Reuse the independently reviewed source-only API. No native method loader is called.
    exporter = PACKET.parent / "extended-cleat-intake-v1/review-fix-v2/export.py"
    assert sha(exporter) == EXPORT_SHA
    spec = importlib.util.spec_from_file_location("saved_observation_review_source_metadata", exporter)
    fixed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixed)
    intake = fixed.load_frozen()
    manifest = PACKET.parent / "parent-authority-v1/extended-cleat-manifest.json"
    p, old, report, panels, prepared_pins = intake.prepare(manifest, MANIFEST_SHA)
    expected_pins = {**prepared_pins, str(exporter.relative_to(ROOT)): EXPORT_SHA}
    assert data["source_sha256"] == expected_pins and len(expected_pins) == 1077
    intake.a.verify(expected_pins)
    assert data["geometry"] == p["geometry"] and data["manifest"] == p["manifest"]
    assert data["parent_base_geometry"] == p["parent_base_geometry"]
    assert data["parent_base_manifest"] == p["parent_base_manifest"]
    assert data["schema"] == "eoere_extended_cleat_cached_source_export/v1"
    assert data["status"] == "CURRENT_DESCRIPTORS_PENDING_PARENT_INPUT_REVIEW_AND_BRIDGE"
    assert data["release"] == p["release"] and not any(data["release"].values())
    assert data["input_schema_or_mechanics_admission_bridge_claimed"] is False
    assert data["candidate_CAD_rebuild_mesh_K_assembly_factorization_q_forces_load_cases_or_native_solve_performed"] is False
    assert data["native_cached_solid_queries_performed"] is True and data["source_pins_before_after_unchanged"] is True
    for key in ("parameters", "material_scenario", "support", "case_provider", "panel_refresh", "geometry_review_evidence"):
        assert data[key] == p[key], key
    for saved, prepared in (("raw_gross_timber_rows", "gross_raw_timber_rows"), ("fitting_poses", "fitting_poses"),
                            ("fitting_ports", "fitting_ports"), ("all_factory_holes", "all_factory_holes"),
                            ("hillman_rows", "hillman_rows"), ("current_panel_machining_descriptors", "current_panel_machining_descriptors"),
                            ("auxiliary_metal_gravity_descriptors", "auxiliary_metal_gravity_descriptors")):
        assert data[saved] == p[prepared], saved
    assert data["pinned_query_versions"] == {"python": "3.12.3", "cadquery": "2.8.0", "cadquery-ocp": "7.9.3.1.1", "numpy": "2.5.2", "scipy": "1.18.1"}

    sources = indexed(report["finished_solids"] + panels)
    observations = indexed(data["finished_body_observations"])
    owners = indexed(data["physical_owner_gravity_rows"])
    profiles = indexed(data["raw_gross_timber_rows"], "name")
    assert observations.keys() == sources.keys() and len(observations) == 28 and len(profiles) == 22 and len(owners) == 150
    assert all(r["mass_kg"] > 0 and len(r["center_xyz_mm"]) == 3 for r in owners.values())
    missing_bounds = set()
    for name, row in observations.items():
        source = sources[name]
        assert row["source"] == source and row["volume_mm3"] > 0
        assert abs(row["volume_mm3"] - source["volume_mm3"]) < max(.01, source["volume_mm3"]*1e-9)
        bounds = row["bounds_xyz_mm"]
        assert len(bounds) == 3 and all(len(pair) == 2 and pair[1] > pair[0] for pair in bounds)
        assert all(lo-1e-5 <= center <= hi+1e-5 for center, (lo, hi) in zip(row["center_xyz_mm"], bounds, strict=True))
        if "bounds_xyz_mm" in source:
            assert close([v for pair in bounds for v in pair], [v for pair in source["bounds_xyz_mm"] for v in pair])
        else:
            missing_bounds.add(name)
        assert row["bounds_were_supplied_prior_metadata"] == (name not in missing_bounds)
        if source.get("center_of_mass_xyz_mm") is not None:
            assert close(row["center_xyz_mm"], source["center_of_mass_xyz_mm"])
        container = row["strict_container"]
        assert container["canonical_solid_topology_counts"]["solids"] == 1
        assert container["extra_geometry_dropped"] is False and container["location_or_orientation_reset"] is False
        assert container["original_wrapper_unchanged"] is True
        owner = owners[name]
        assert owner["kind"] == ("panel" if name in old["panel_ids"] else "timber")
        assert close(owner["center_xyz_mm"], row["center_xyz_mm"])
        assert math.isclose(owner["mass_kg"], row["volume_mm3"] * data["parameters"]["wood_density_kg_m3"] * 1e-9)
    assert data["import_proof"]["native_cached_BREP_imports"] == 28
    assert set(data["import_proof"]["missing_bounds_measured_owner_ids"]) == missing_bounds
    assert data["import_proof"]["original_import_function_restored"] is True
    assert data["import_proof"]["derived_bounds_claimed_as_independent_prior_metadata"] is False

    shafts = indexed(data["shafts"], "axis_id")
    axes = indexed(report["axes"])
    walls = {(r["axis_id"], r["receiver"]): r for r in data["finished_receiver_wall_queries"]}
    assert len(shafts) == 100 and shafts.keys() == axes.keys() and len(walls) == 120
    required = {(r["axis_id"], r["receiver"]) for r in p["required_own_wall_queries"]}
    lookup = {(receiver, tuple(axis["point_xyz_mm"])): axis["id"] for axis in axes.values() for receiver in axis["receivers"]}
    fresh = {(lookup[(r["receiver"], tuple(r["point_xyz_mm"]))], r["receiver"]) for r in data["wall_query_proof"]["fresh"]}
    reused = {(r["axis_id"], r["receiver"]) for r in data["wall_query_proof"]["reused"]}
    assert fresh == required and len(fresh) == len(reused) == 60 and not fresh & reused and fresh | reused == walls.keys()
    assert sum(receiver in intake.CLEATS for _, receiver in fresh) == 8
    old_walls = {(r["axis_id"], r["receiver"]): r for r in old["finished_receiver_wall_queries"]}
    old_sources = {r["id"]: r["source"] for r in old["finished_body_observations"]}
    for pair, wall in walls.items():
        axis_id, receiver = pair
        assert wall["full_wall_length_mm"] > 0 and wall["partial_wall_present"] is False
        assert wall["grain_axis_xyz"] == profiles[receiver]["axis"]
        assert wall["qualified_directional_bearing_length_mm"] is None
        assert all(hi > lo for lo, hi in wall["full_wall_intervals_mm"])
        if pair in reused:
            assert sources[receiver]["sha256"] == old_sources[receiver]["sha256"]
            assert wall["full_wall_intervals_mm"] == old_walls[pair]["full_wall_intervals_mm"]
    seat_count, role_count, steel_count = 0, 0, 0
    expected_owner_ids = set(sources) | {r["id"] for r in data["fitting_poses"]}
    for axis_id, shaft in shafts.items():
        axis = axes[axis_id]
        assert shaft["source_axis"] == axis and shaft["point"] == axis["point_xyz_mm"]
        assert shaft["nominal_geometry_not_delivered_thread_root_or_shank"] is True
        assert len(shaft["basis"]) == 3
        assert all(math.isclose(sum(v*v for v in row), 1., abs_tol=1e-10) for row in shaft["basis"])
        for i in range(3):
            for j in range(i):
                assert abs(sum(a*b for a,b in zip(shaft["basis"][i], shaft["basis"][j], strict=True))) < 1e-10
        for receiver in axis["receivers"]:
            expected_intervals = walls[(axis_id, receiver)]["finished_full_wall_intervals_from_axis_point_mm"]
            assert [r["interval_mm"] for r in shaft["surfaces"] if r["kind"] == "wood" and r["host"] == receiver] == expected_intervals
        steel_count += sum(r["kind"] == "steel" for r in shaft["surfaces"])
        ends = indexed(shaft["ends"], "end")
        assert set(ends) == {"head", "nut"}
        for end, row in ends.items():
            i = 0 if end == "head" else 1
            support = -axis["before_plate_mm"] if end == "head" else axis["grip_mm"]+axis["after_plate_mm"]
            assert math.isclose(row["support_s_mm"], support, abs_tol=1e-10)
            candidates = [s for s in shaft["surfaces"] if s["kind"] == "steel" and abs(s["interval_mm"][i]-support) < 1e-5]
            if not candidates:
                target = 0. if end == "head" else axis["grip_mm"]
                candidates = [s for s in shaft["surfaces"] if s["kind"] == "wood" and abs(s["interval_mm"][i]-target) < 1e-5]
            assert len(candidates) == 1 and row["host"] == candidates[0]["host"]
            assert row["delivered_bearing_seat_or_pressure_qualified"] is False
            seat_count += 1
        roles = indexed(shaft["metal_roles"], "kind")
        assert set(roles) == {"shaft", "head", "head_washer", "nut_washer", "nut"}
        assert all(r["volume_mm3"] > 0 and math.isclose(r["mass_kg"], r["volume_mm3"]*7850e-9) for r in roles.values())
        mass = sum(r["mass_kg"] for r in roles.values())
        center = [sum(r["mass_kg"]*r["center_of_mass_xyz_mm"][j] for r in roles.values())/mass for j in range(3)]
        assert math.isclose(owners[shaft["body"]]["mass_kg"], mass) and close(owners[shaft["body"]]["center_xyz_mm"], center)
        expected_owner_ids.add(shaft["body"])
        role_count += len(roles)
    assert set(owners) == expected_owner_ids and seat_count == 200 and role_count == 500 and steel_count == 88
    prepared_owners = indexed(p["physical_owner_gravity_descriptors"])
    for pose in data["fitting_poses"]:
        owner, prior = owners[pose["id"]], prepared_owners[pose["id"]]
        assert owner["mass_kg"] == prior["mass_kg"] and close(owner["center_xyz_mm"], prior["center_xyz_mm"])
    assert len(data["fitting_ports"]) == 88 and sum(len(r["holes"]) for r in data["all_factory_holes"]) == 176
    assert len(data["hillman_rows"]) == 66 and len(data["auxiliary_metal_gravity_descriptors"]) == 274
    assert all(r["owner"] in sources and r["mass_kg"] > 0 for r in data["auxiliary_metal_gravity_descriptors"])

    floors = indexed(data["floor_observations"], "host")
    expected_floors = indexed(p["floor_descriptors"], "host")
    assert floors.keys() == expected_floors.keys() and len(floors) == 8
    for name, row in floors.items():
        assert all(row[key] == value for key, value in expected_floors[name].items())
        points = row["observed_normal_reference_points_xyz_mm"]
        assert len(points) == 4 and len({tuple(point) for point in points}) == 4
        assert all(abs(point[2]) < 1e-5 for point in points)
        assert all(sum(close(point, other) for other in points) == 1 for point in row["normal_reference_points_xyz_mm"])
        assert row["own_floor_face_confirmed_from_current_cached_solid"] is True
    assert {name for name, row in floors.items() if row["centroid_XY_enabled"]} == {"lumber_leg_left", "lumber_leg_right"}
    assert data["support"]["normal_count"] == 32 and data["support"]["no_slip_assumed_not_verified"] is True

    timber_ids, panel_ids = sorted(profiles), old["panel_ids"]
    candidate_pairs = [(a,b,"timber_face_contact") for i,a in enumerate(timber_ids) for b in timber_ids[i+1:]]
    candidate_pairs += [(a,b,"panel_contact") for a in panel_ids for b in timber_ids]
    overlap = lambda a,b: all(observations[a]["bounds_xyz_mm"][i][0] <= observations[b]["bounds_xyz_mm"][i][1]+1e-5
        and observations[b]["bounds_xyz_mm"][i][0] <= observations[a]["bounds_xyz_mm"][i][1]+1e-5 for i in range(3))
    expected_pairs = {(a,b,kind) for a,b,kind in candidate_pairs if overlap(a,b)}
    census = {(r["first"],r["second"],r["kind"]):r["patch_count"] for r in data["shared_pair_query_census"]}
    assert len(candidate_pairs) == 363 and len(census) == len(data["shared_pair_query_census"]) == 72 and census.keys() == expected_pairs
    common = indexed(data["timber_and_panel_shared_face_patches"])
    flange = indexed(data["flange_shared_face_patches"])
    domains = indexed(data["flange_domains"])
    contacts = indexed(data["direct_contacts"])
    assert len(common) == 96 and len(flange) == len(domains) == 88 and len(contacts) == 1606
    patch_counts = Counter((r["first"],r["second"],r["kind"]) for r in common.values())
    assert all(patch_counts[pair] == count for pair,count in census.items())
    cell_counts, max_area_error, max_centroid_error = Counter(), 0., 0.
    for patch in [*common.values(), *flange.values()]:
        assert patch["area_mm2"] > 0 and patch["opposed_normal_dot"] < -1.+1e-8
        assert abs(patch["coplanar_offset_mm"]) < 1e-5
        assert canonical(patch["trimmed_region_geometry"]) == patch["trimmed_region_signature_sha256"]
        for side in ("first", "second"):
            face = patch["source_"+side+"_face"]
            assert canonical(face["signature"]) == face["signature_sha256"]
            assert face["face_id"].startswith(patch[side]+"/step-face-")
        cells = patch["cells"]
        assert cells and all(cell["area_mm2"] > 0 and cell["both_inward_material_probes_occupied"] is True
            and cell["reference_centroid_on_trimmed_patch"] is True for cell in cells)
        area = sum(cell["area_mm2"] for cell in cells)
        centroid = [sum(cell["area_mm2"]*cell["point_xyz_mm"][i] for cell in cells)/area for i in range(3)]
        area_error, centroid_error = abs(area-patch["area_mm2"])/patch["area_mm2"], math.dist(centroid,patch["centroid_xyz_mm"])
        assert area_error < 1e-7 and centroid_error < 1e-5
        max_area_error, max_centroid_error = max(max_area_error,area_error), max(max_centroid_error,centroid_error)
        if patch["id"] in common:
            kind = patch["kind"]
            for cell in cells:
                contact = contacts[cell["id"]]
                assert contact["source_patch_id"] == patch["id"] and contact["source_trimmed_region_signature_sha256"] == patch["trimmed_region_signature_sha256"]
                assert contact["first"] == patch["first"] and contact["second"] == patch["second"]
                assert contact["point_xyz_mm"] == cell["point_xyz_mm"] and contact["reference_area_mm2"] == cell["area_mm2"]
                assert contact["pressure_convergence_or_physical_contact_qualified"] is False
                density = data["parameters"]["panel_foundation_n_mm3" if kind == "panel_contact" else "wood_bedding_n_mm3"]
                assert contact["bedding_n_mm3"] == density and math.isclose(contact["stiffness"], density*cell["area_mm2"])
                cell_counts[kind] += 1
    baseline = json.loads((ROOT / old["geometry"]["report"]["path"]).read_bytes())
    scenario = baseline["scenario"]
    nominal_area = scenario["width_mm"]*(scenario["leg_mm"]-scenario["thickness_mm"])-4*math.pi*(scenario["factory_hole_mm"]/2)**2
    flange_contacts = [r for r in contacts.values() if r["kind"] == "flange_contact"]
    assert len(flange_contacts) == 352
    for domain in domains.values():
        assert domain["unmeasured_sharp_flat_flange_scenario"] is True
        assert math.isclose(domain["nominal_full_holed_flange_area_mm2"], nominal_area)
        assert math.isclose(domain["nominal_half_area_mm2"], nominal_area/2)
        own = [r for r in flange.values() if r["id"].startswith(domain["id"]+"/")]
        assert own and math.isclose(domain["clipped_area_mm2"], sum(r["area_mm2"] for r in own))
        assert 0 < domain["clipped_area_mm2"] <= domain["nominal_half_area_mm2"]+1e-5
        density = data["parameters"]["flange_nominal_total_stiffness_n_mm"]/nominal_area
        assert math.isclose(domain["declared_flange_area_density_n_mm3"], density)
        own_contacts = [r for r in flange_contacts if r["source_domain_id"] == domain["id"]]
        assert len(own_contacts) == sum(len(r["cells"]) for r in own)
        for contact in own_contacts:
            assert contact["first"] == domain["fitting"] and contact["second"] == domain["receiver"]
            assert contact["first_port_id"] == domain["model_port_id"]
            assert math.isclose(contact["stiffness"], density*contact["reference_area_mm2"])
            assert contact["rigid_translation_total_prior_only_no_old_rocking_or_forces"] is True
    assert sum(cell_counts.values())+len(flange_contacts) == len(contacts)
    graph = defaultdict(set)
    for row in common.values():
        graph[row["first"]].add(row["second"])
        graph[row["second"]].add(row["first"])
    reached, pending = set(), [next(iter(sources))]
    while pending:
        item = pending.pop()
        if item not in reached:
            reached.add(item)
            pending.extend(graph[item]-reached)
    assert reached == set(sources)

    changed_sources = sorted(name for name in sources if sources[name]["sha256"] != old_sources[name]["sha256"])
    pair_key = lambda row: (row["first"],row["second"],row.get("source_owned_port_id"))
    old_pairs = {pair_key(row) for row in old["timber_and_panel_shared_face_patches"]}
    current_pairs = {pair_key(row) for row in common.values()}
    intake.a.verify(expected_pins)
    assert sha(OUTPUT) == OUTPUT_SHA and sha(process_path) == process_sha and sha(SLOT) == SLOT_SHA
    assert all(name not in sys.modules for name in ("cadquery", "OCP", "numpy"))
    receipt = {"schema": "eoere_current_saved_descriptor_correctness_review/v1", "status": "PASS_NO_SUBSTANTIAL_FINDINGS",
        "findings": [], "review_script_sha256": sha(OWN),
        "sources": {str(OUTPUT.relative_to(ROOT)): OUTPUT_SHA, str(process_path.relative_to(ROOT)): process_sha,
            str(SLOT): SLOT_SHA, str(exporter.relative_to(ROOT)): EXPORT_SHA},
        "verified_source_closure": {"pins": 1077, "all_before_after_unchanged": True},
        "counts": {"finished_body_observations": 28, "gross_timber_profiles": 22, "physical_gravity_owners": 150,
            "shaft_roles": 500, "shafts": 100, "fitting_ports": 88, "factory_holes": 176, "Hillman_screws": 66,
            "wall_rows": 120, "fresh_walls": 60, "fresh_cleat_walls": 8, "source_identical_reused_walls": 60,
            "external_seats": 200, "floor_hosts": 8, "floor_normal_points": 32, "complete_broadphase_pairs": 363,
            "broadphase_overlapping_pairs": 72, "timber_panel_patches": 96, "flat_flange_domains_and_patches": 88,
            "timber_contact_cells": cell_counts["timber_face_contact"], "panel_contact_cells": cell_counts["panel_contact"],
            "flat_flange_cells": 352, "total_direct_contacts": 1606, "connected_timber_panel_owners": len(reached)},
        "contact_arithmetic": {"max_cell_area_relative_error": max_area_error, "max_area_weighted_centroid_error_mm": max_centroid_error,
            "max_recorded_sampled_second_moment_relative_error": max(r["second_moment_relative_frobenius_error"] for r in [*common.values(),*flange.values()])},
        "current_vs_preserved": {"changed_finished_source_ids": changed_sources,
            "new_timber_panel_owner_pairs": sorted(current_pairs-old_pairs), "removed_timber_panel_owner_pairs": sorted(old_pairs-current_pairs),
            "old_direct_contact_cells": len(old["direct_contacts"]), "current_direct_contact_cells": len(contacts),
            "matching_current_forces_or_prior_passes_transferred": False},
        "physical_owner_total_mass_kg_without_auxiliary_source_shares": sum(r["mass_kg"] for r in owners.values()),
        "review_performed_only_saved_metadata_reads_and_source_hashes": True, "review_native_queries_or_K_q_forces_solve_or_browser": False,
        "limits": ["Saved source and nominal geometry observations authenticate this extraction; no physical inspection is claimed.",
            "Gross-stock beam sections, uninspected declared grain, nominal flat flange masks and assumed no-slip support retain their analytical limits.",
            "Fresh current contact graph has connected geometry descriptors; it is not a stiffness, force, stability or resistance result.",
            "Sampled second-moment errors and unqualified contact pressure prevent a convergence or physical-contact claim.",
            "Current panel bank, pure input bridge and independent raw-field admission remain separate gates; all release flags remain false."]}
    with OWN.with_name("receipt.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "source_pins": 1077, "contacts": 1606, "seats": 200, "findings": 0}))


if __name__ == "__main__":
    main()
