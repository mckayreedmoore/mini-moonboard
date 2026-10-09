"""Independent Z180 saved-descriptor correctness audit, entirely source-only.

Replay authenticated stdlib producers in memory, then use separate polygon,
cylinder and angular quadrature calculations. Never call the descriptor CLI,
import CAD/mechanics, query BREP, construct operators or consume old forces.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
D = OWN.parents[2]
ROOT = D.parents[6]
TARGETS = {
    "descriptor.py": "691f46fd47b2e952e3b8911d61ddf855d9806c20190f77a1d6e0f57ad022a9ac",
    "review-fix-v2/descriptor.py": "8ab67c15c544ba1cf1f0209020fb87614072c665a8eaa39dc667a23db5b2823a",
    "review-fix-v3/descriptor.py": "b9540ab1612033194c8ae7ac230ab21082813cd63cf824cc77b58cba9bfa6b1b",
    "review-fix-v4/descriptor.py": "a7b27b82eb3bafc698d371ce2f4b2e71c89cc4306459cd795ed1ca1c983ae106",
    "review-fix-v4/inputs.json": "a359cb1c7c3c30954d6e36204bd523cd0d565c10a9b78f9af09e6ddcbb66b6be",
    "runs-v1/attempt03/descriptor.json": "e7a1a56f7c61119445c85f554d534abc5c43f77fede27a7fab42ad252bb275f0",
    "result.json": "3b8c2b7849573104a10ca1b0cf827bd9b0055c6edf3ee2ac91feaab88e3357d4",
    "test_descriptor.py": "7aba4dc793b49da7c775185a8cf21422e222ec8f0eff4de99dc8afffa587f3c3",
    "review-fix-v2/test_descriptor.py": "18107aaeb56d22fb9f931dcb4ec189394be6287e655f3805e10a18bae954f10d",
    "review-fix-v3/test_descriptor.py": "be029b65fd043d0d85cad200700f3a6c3ad322e96d415447d59f363b1d2ae0f2",
    "review-fix-v4/test_descriptor.py": "077609ecc14077fc3e6c27eb63d749b434b80a64c0c8c261087889650ac796b9",
}


def require(value, message):
    if not value:
        raise AssertionError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def path_name(path):
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def near(a, b, *, absolute=1e-7, relative=1e-11):
    if isinstance(a, (list, tuple)):
        require(len(a) == len(b), "numerical shape differs")
        for x, y in zip(a, b, strict=True):
            near(x, y, absolute=absolute, relative=relative)
    else:
        require(math.isfinite(a) and math.isfinite(b)
                and abs(a-b) <= absolute + relative*max(abs(a), abs(b)),
                f"independent numerical check differs: {a!r} vs {b!r}")


def index(rows, key="id"):
    result = {r[key]: r for r in rows}
    require(len(result) == len(rows), "duplicate independent join")
    return result


def profile_raw(profile):
    polygon = profile["YZ_polygon_mm"]
    cross = [a[0]*b[1]-b[0]*a[1] for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True)]
    twice = sum(cross)
    require(twice > 0, "positive oriented source profile required")
    # Every corner has the same positive turn: source profiles are convex.
    for i in range(len(polygon)):
        a, b, c = polygon[i-1], polygon[i], polygon[(i+1) % len(polygon)]
        require((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]) > 0,
                "convex source profile required by material proof")
    center_yz = [sum((a[j]+b[j])*q for a, b, q in zip(polygon, polygon[1:]+polygon[:1], cross, strict=True))/(3*twice)
                 for j in range(2)]
    x0, x1 = profile["X_interval_mm"]
    return twice/2*(x1-x0), [(x0+x1)/2, *center_yz]


def independent_com(profile, axes, host, finished_volume):
    raw_volume, raw_center = profile_raw(profile)
    moment = [raw_volume*c for c in raw_center]
    void_volume = 0.
    own = [a for a in axes.values() if host in a["receivers"]]
    require(len(own) == 4, "four own bores required")
    for axis in own:
        require(abs(axis["direction_xyz"][0]) == 1. and axis["direction_xyz"][1:] == [0., 0.],
                "independent cylinder reduction requires X axes")
        volume = math.pi*(axis["bore_diameter_mm"]/2)**2*(profile["X_interval_mm"][1]-profile["X_interval_mm"][0])
        center = [raw_center[0], *axis["point_xyz_mm"][1:]]
        void_volume += volume
        moment = [m-volume*c for m, c in zip(moment, center, strict=True)]
    near(raw_volume, profile["raw_volume_mm3"], absolute=.001)
    near(raw_volume-void_volume, finished_volume, absolute=.001)
    return [m/finished_volume for m in moment]


def disk_numeric(y, z, radius, lower, upper, n=2048):
    """Independent smooth angular Simpson integration; no closed primitive."""
    low = max(-radius, lower-y)
    high = min(radius, upper-y)
    if high <= low:
        return [0.]*6
    a, b = math.asin(low/radius), math.asin(high/radius)
    result = [0.]*6
    for j in range(n+1):
        angle = a+(b-a)*j/n
        cosine = math.cos(angle)
        center_y = y+radius*math.sin(angle)
        area = 2*radius**2*cosine**2
        values = [area, center_y*area, z*area, center_y**2*area, z*center_y*area,
                  z*z*area+2*radius**4*cosine**4/3]
        weight = 1 if j in (0, n) else 4 if j % 2 else 2
        result = [v+weight*w for v, w in zip(result, values, strict=True)]
    return [v*(b-a)/(3*n) for v in result]


def rectangular_moments(bounds):
    y0, y1, z0, z1 = bounds
    area = (y1-y0)*(z1-z0)
    cy, cz = (y0+y1)/2, (z0+z1)/2
    return [area, area*cy, area*cz, area*(cy*cy+(y1-y0)**2/12), area*cy*cz,
            area*(cz*cz+(z1-z0)**2/12)]


def independent_patch(patch, axes, host, profiles):
    x0, x1, y0, y1, z0, z1 = patch["trimmed_region_geometry"]["bounds_xyz_mm"]
    near(x0, x1)
    holes = [a for a in axes.values() if a["id"].startswith("cleat_post_bolt_") and host in a["receivers"]]
    require(len(holes) == 2, "two own overlap disks required")
    whole = rectangular_moments([y0, y1, z0, z1])
    for axis in holes:
        y, z = axis["point_xyz_mm"][1:]
        radius = axis["bore_diameter_mm"]/2
        require(y0 < y-radius < y+radius < y1 and z0 < z-radius < z+radius < z1,
                "whole disks must fit own contact rectangle")
        area = math.pi*radius**2
        disk = [area, area*y, area*z, area*(y*y+radius**2/4), area*y*z, area*(z*z+radius**2/4)]
        whole = [a-b for a, b in zip(whole, disk, strict=True)]
    area, fy, fz, yy, yz, zz = whole
    center = [x0, fy/area, fz/area]
    second = [[0., 0., 0.], [0., yy-fy*fy/area, yz-fy*fz/area], [0., yz-fy*fz/area, zz-fz*fz/area]]
    near(area, patch["area_mm2"])
    near(center, patch["centroid_xyz_mm"])
    near(second, patch["exact_centroidal_second_moment_matrix_xyz_mm4"], absolute=1e-5)
    maximum_cell_area_error = 0.
    for cell in patch["cells"]:
        bounds = cell["analytic_cell_bounds_local_YZ_mm"]
        moments = rectangular_moments(bounds)
        for axis in holes:
            y, z = axis["point_xyz_mm"][1:]
            radius = axis["bore_diameter_mm"]/2
            local_y, local_z = y-y0, z-z0
            if local_z+radius <= bounds[2] or local_z-radius >= bounds[3]:
                continue
            require(bounds[2] <= local_z-radius and local_z+radius <= bounds[3],
                    "actual disk must fit its Z row")
            disk = disk_numeric(local_y, local_z, radius, bounds[0], bounds[1])
            moments = [a-b for a, b in zip(moments, disk, strict=True)]
        maximum_cell_area_error = max(maximum_cell_area_error, abs(moments[0]-cell["area_mm2"]))
        near(moments[0], cell["area_mm2"])
        near([x0, y0+moments[1]/moments[0], z0+moments[2]/moments[0]], cell["point_xyz_mm"])
        probes = cell["analytic_material_at_reference"]["probes"]
        require(len(probes) == 2 and all(min(p["minimum_X_profile_clearance_mm"], p["minimum_YZ_profile_clearance_mm"],
                                            p["minimum_bore_clearance_mm"]) > 0 for p in probes),
                "both analytic own-material probes required")
        for sign, probe, owner in zip((1., -1.), probes, (patch["first"], patch["second"]), strict=True):
            require(probe["host"] == owner, "foreign inward material probe host")
            point = [p+sign*.05*n for p, n in zip(cell["point_xyz_mm"], patch["normal_from_second_to_first_xyz"], strict=True)]
            near(point, probe["point_xyz_mm"])
            profile = profiles[owner]
            xgap = min(point[0]-profile["X_interval_mm"][0], profile["X_interval_mm"][1]-point[0])
            polygon = profile["YZ_polygon_mm"]
            pgap = min(((b[0]-a[0])*(point[2]-a[1])-(b[1]-a[1])*(point[1]-a[0]))/math.dist(a,b)
                       for a,b in zip(polygon, polygon[1:]+polygon[:1], strict=True))
            bore_gap = min(math.dist(point[1:], a["point_xyz_mm"][1:])-a["bore_diameter_mm"]/2
                           for a in axes.values() if owner in a["receivers"])
            near([xgap,pgap,bore_gap], [probe["minimum_X_profile_clearance_mm"], probe["minimum_YZ_profile_clearance_mm"],probe["minimum_bore_clearance_mm"]])
            require(min(xgap,pgap,bore_gap) > 0, "independent inward material probe failed")
    return maximum_cell_area_error


def separation(region_bounds, host, profiles, old, new):
    box = [[region_bounds[2*i], region_bounds[2*i+1]] for i in range(3)]
    proofs = []
    for name, before in old.items():
        if not name.startswith("cleat_post_bolt_") or host not in before["receivers"]:
            continue
        after = new[name]
        radius = before["bore_diameter_mm"]/2
        sweep = [profiles[host]["X_interval_mm"], [before["point_xyz_mm"][1]-radius, before["point_xyz_mm"][1]+radius],
                 [after["point_xyz_mm"][2]-radius, before["point_xyz_mm"][2]+radius]]
        candidates = [(box[i][0]-sweep[i][1], i) for i in range(3)] + [(sweep[i][0]-box[i][1], i) for i in range(3)]
        gap, coordinate = max(candidates)
        require(gap > 1e-6, "own whole-region sweep intersection")
        proofs.append({"axis_id": name, "gap_mm": gap, "separating_coordinate": "XYZ"[coordinate]})
    return proofs


def check_summary(summary, saved, current, inp, descriptor_raw):
    proof = saved["geometry_delta_proof"]
    require(summary["schema"] == "eoere_z180_geometry_delta_descriptor_trial/v1"
            and summary["status"] == "SOURCE_ONLY_UNADOPTED_DESCRIPTOR_BUILT_PENDING_INDEPENDENT_REVIEW",
            "compact source-only identity differs")
    require(summary["descriptor"] == {"path": path_name(D/"runs-v1/attempt03/descriptor.json"), "sha256": digest(descriptor_raw)}
            and summary["descriptor_bytes"] == len(descriptor_raw), "compact descriptor exact reference differs")
    for summary_key, saved_key in (("counts", "counts"), ("byte_identical_descriptor_fields", "byte_identical_descriptor_fields"),
                                   ("changed_host_inherited_regions", "changed_host_inherited_regions")):
        require(summary[summary_key] == proof[saved_key], "compact geometry proof claim differs: "+summary_key)
    for key, expected in (("frozen_geometry", saved["geometry"]), ("parent_geometry", saved["parent_geometry"]),
                          ("parent_descriptors", saved["parent_descriptors"]), ("source_only_parent_manifest", saved["manifest"]),
                          ("contact_reuse", saved["mixed_contact_source_contract"]),
                          ("source_corrections", saved["descriptor_source_corrections"]), ("unresolved_joins", saved["unresolved_joins"]),
                          ("release", saved["release"]), ("helper", inp["sources"]["mixed_contact_contract_adapter"]),
                          ("source_contract_audit", inp["sources"]["late_source_contract_audit"]),
                          ("inputs", {"path": path_name(D/"review-fix-v4/inputs.json"), "sha256": TARGETS["review-fix-v4/inputs.json"]})):
        require(summary[key] == expected, "compact exact claim differs: "+key)
    require(summary["consumed_source_pins"] == len(saved["source_sha256"]) == 1116
            and summary["source_closure_canonical_sha256"] == canonical(saved["source_sha256"]), "compact source closure differs")
    for key in ("force_execution_readiness_claimed", "historical_q_forces_operators_or_acceptance_transferred",
                "native_CAD_BREP_import_K_panel_preparation_response_or_solve_performed"):
        require(summary[key] is saved[key] is False, "compact scope claim differs")
    require(summary["original_4in_hardware_retained_spacer_proposal_excluded"]
            is saved["current_4in_hardware_retained_spacer_proposal_excluded"] is True, "compact hardware claim differs")
    for name, value in summary["COM"].items():
        own = proof["COM"][name]
        require(value == {"old_center_xyz_mm": own["old_center_xyz_mm"], "new_center_xyz_mm": own["new_center_xyz_mm"],
            "old_volume_mm3": own["old_volume_mm3"], "new_volume_mm3": own["new_volume_mm3"],
            "center_delta_xyz_mm": [a-b for a, b in zip(own["new_center_xyz_mm"], own["old_center_xyz_mm"], strict=True)],
            "old_COM_source": own["old_COM_observation_source"], "new_native_receiver_evidence": own["saved_native_receiver_evidence"],
            "native_COM_query_performed": False}, "compact COM summary differs")
    before, after = index(current["timber_and_panel_shared_face_patches"]), index(saved["timber_and_panel_shared_face_patches"])
    for row in summary["rebuilt_contact_patches"]:
        item = next(p for p in proof["rebuilt_patches"] if p["id"] == row["id"])
        expected = {**item, "old_area_mm2": before[row["id"]]["area_mm2"], "new_area_mm2": after[row["id"]]["area_mm2"],
            "old_center_xyz_mm": before[row["id"]]["centroid_xyz_mm"], "new_center_xyz_mm": after[row["id"]]["centroid_xyz_mm"],
            **{k: after[row["id"]][k] for k in ("analytic_source_region_sha256", "cell_area_error_mm2", "cell_centroid_error_mm")}}
        require(row == expected, "compact rebuilt patch summary differs")
    require(summary["changed_host_inherited_floor_observations"] == [r for r in saved["floor_observations"]
             if r["host"] in proof["changed_host_inherited_floor_regions"]], "compact floor summary differs")
    for key, kind in (("flange_domains_canonical_sha256_before_and_after", "flange_domains"),
                      ("flange_patches_canonical_sha256_before_and_after", "flange_shared_face_patches")):
        require(summary[key] == canonical(current[kind]) == canonical(saved[kind]), "compact flange hash differs")
    require(summary["flange_rows_canonical_sha256_before_and_after"] == canonical([r for r in current["direct_contacts"] if r["kind"] == "flange_contact"])
            == canonical([r for r in saved["direct_contacts"] if r["kind"] == "flange_contact"]), "compact flange row hash differs")
    maximum = max(p["second_moment_relative_frobenius_error"] for key in
                  ("timber_and_panel_shared_face_patches", "flange_shared_face_patches") for p in saved[key])
    require(summary["sampling_limit"]["maximum_sampled_second_moment_relative_frobenius_error"] == maximum
            and summary["sampling_limit"]["pressure_rocking_or_physical_acceptance"] is False,
            "compact quadrature limit differs")
    return maximum


def main():
    pins = {path_name(D/name): expected for name, expected in TARGETS.items()}
    for name, expected in TARGETS.items():
        require(digest((D/name).read_bytes()) == expected, "frozen review target changed: "+name)
    spec = importlib.util.spec_from_file_location("z180_independent_correctness_frozen_v4", D/"review-fix-v4/descriptor.py")
    v4 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v4)
    v3 = v4.corrected_v3()
    v2 = v3.verified_v2()
    frozen = v3.corrected_frozen_module(v2)
    with v2.source_context(frozen):
        bundle = frozen.load_inputs(D/"review-fix-v4/inputs.json", TARGETS["review-fix-v4/inputs.json"])
        require(len(bundle["source_sha256"]) == 1116, "exact inherited closure census differs")
        replay = frozen.build_descriptor(bundle)
        frozen.verify(bundle["source_sha256"], ROOT)
    descriptor_raw = (D/"runs-v1/attempt03/descriptor.json").read_bytes()
    saved = json.loads(descriptor_raw)
    replay["source_pins_before_after_unchanged"] = True
    require((json.dumps(replay, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n").encode() == descriptor_raw,
            "complete JSON-serialized in-memory replay differs from exact saved bytes")
    records, inp = bundle["records"], bundle["input"]
    current = records["current"]
    proof = saved["geometry_delta_proof"]
    old_axes = index(records["current_geometry"]["axes"])
    new_axes = {**old_axes, **index(records["layout"]["proposed_axes"])}
    profiles = records["receiver_inventory"]["affected_members"]
    observations, parent_observations = index(saved["finished_body_observations"]), index(current["finished_body_observations"])
    com_delta = {}
    for host, profile in profiles.items():
        near(independent_com(profile, old_axes, host, parent_observations[host]["volume_mm3"]), parent_observations[host]["center_xyz_mm"])
        near(independent_com(profile, new_axes, host, observations[host]["volume_mm3"]), observations[host]["center_xyz_mm"])
        near(observations[host]["volume_mm3"], parent_observations[host]["volume_mm3"], absolute=.001)
        com_delta[host] = observations[host]["center_xyz_mm"][2]-parent_observations[host]["center_xyz_mm"][2]
        require(observations[host]["source_only_analytic_centroid"] is True
                and observations[host]["provenance"]["new_native_COM_query_performed"] is False, "new COM must remain analytical")
    changed_owners = set(profiles)
    old_shafts, new_shafts = index(current["shafts"], "axis_id"), index(saved["shafts"], "axis_id")
    moved = set(frozen.AXES)
    for axis_id, shaft in new_shafts.items():
        prior = old_shafts[axis_id]
        if axis_id not in moved:
            require(shaft == prior, "one of 96 protected shafts changed")
            continue
        changed_owners.add(shaft["body"])
        near(shaft["point"], [prior["point"][0], prior["point"][1], prior["point"][2]-20.])
        require(shaft["source_axis"] == new_axes[axis_id] and len(shaft["metal_roles"]) == 5, "moved source-axis/role join differs")
        for old, new in zip(prior["metal_roles"], shaft["metal_roles"], strict=True):
            near(new["center_of_mass_xyz_mm"], [*old["center_of_mass_xyz_mm"][:2], old["center_of_mass_xyz_mm"][2]-20.])
            require(all(new[k] == old[k] for k in ("id", "kind", "mass_kg", "volume_mm3")), "same nominal hardware mass changed")
        require(all(shaft[k] == prior[k] for k in set(shaft)-{"point", "metal_roles", "source_axis"}), "translated shaft local properties changed")
    old_owners, owners = index(current["physical_owner_gravity_rows"]), index(saved["physical_owner_gravity_rows"])
    require(set(owners) == set(old_owners) and len(owners) == 150, "physical owner identity census differs")
    for name, row in owners.items():
        if name not in changed_owners:
            require(row == old_owners[name], "protected physical owner changed")
        near(row["mass_kg"], old_owners[name]["mass_kg"], absolute=1e-12)
        require(row["mass_kg"] > 0 and all(math.isfinite(v) for v in row["center_xyz_mm"]), "positive finite owner required")
        if name in profiles:
            near(row["center_xyz_mm"], observations[name]["center_xyz_mm"])
            near(row["mass_kg"], observations[name]["volume_mm3"]*saved["parameters"]["wood_density_kg_m3"]*1e-9)
        elif name in changed_owners:
            shaft = next(s for s in new_shafts.values() if s["body"] == name)
            mass = sum(r["mass_kg"] for r in shaft["metal_roles"])
            near(row["mass_kg"], mass)
            near(row["center_xyz_mm"], [sum(r["mass_kg"]*r["center_of_mass_xyz_mm"][j] for r in shaft["metal_roles"])/mass for j in range(3)])
    patches, old_patches = index(saved["timber_and_panel_shared_face_patches"]), index(current["timber_and_panel_shared_face_patches"])
    area_errors = [independent_patch(patches[r["id"]], new_axes, patches[r["id"]]["first"], profiles) for r in proof["rebuilt_patches"]]
    for row in proof["changed_host_inherited_regions"]:
        patch = patches[row["id"]]
        for host in row["changed_hosts"]:
            near([p["gap_mm"] for p in separation(patch["trimmed_region_geometry"]["bounds_xyz_mm"], host, profiles, old_axes, new_axes)],
                 [p["gap_mm"] for p in row["proofs"][host]])
        require(canonical(patch["source_region_identity"]) == patch["analytic_source_region_sha256"], "own analytical source identity differs")
    for floor in saved["floor_observations"]:
        if floor["host"] not in profiles:
            continue
        points = floor["observed_normal_reference_points_xyz_mm"]
        bounds = [v for i in range(3) for v in (min(p[i] for p in points), max(p[i] for p in points))]
        require(separation(bounds, floor["host"], profiles, old_axes, new_axes)
                == floor["inherited_floor_observation"]["whole_footprint_sweep_separation"], "floor whole-sweep proof differs")
    new_native = next(s for s in records["native"]["scenarios"] if s["scenario"] == "proposed_Z180_modeled")
    walls = {(w["axis_id"], w["receiver"]): w for w in saved["finished_receiver_wall_queries"]}
    for wall in new_native["wall_queries"]:
        actual = walls[wall["axis_id"], wall["receiver"]]
        require(all(actual[key] == value for key, value in wall.items()), "native own-wall evidence binding differs")
        require(actual["observation_provenance"]["finished_source"] == {k: observations[wall["receiver"]]["source"][k] for k in ("path", "sha256")},
                "native wall bound to foreign finished source")
    affected_patches = {r["id"] for key in ("rebuilt_patches", "changed_host_inherited_regions") for r in proof[key]}
    contacts = index(saved["direct_contacts"])
    for old in current["direct_contacts"]:
        actual = contacts[old["id"]]
        if old["kind"] == "flange_contact" or old["source_patch_id"] not in affected_patches:
            require(actual == old, "unaffected contact row changed")
        else:
            patch = patches[old["source_patch_id"]]
            cell = next(c for c in patch["cells"] if c["id"] == old["id"])
            require(actual["point_xyz_mm"] == cell["point_xyz_mm"] and actual["reference_area_mm2"] == cell["area_mm2"]
                    and actual["stiffness"] == old["bedding_n_mm3"]*cell["area_mm2"]
                    and actual["source_only_region_provenance"] == patch["source_region_identity"], "changed contact own-cell join differs")
    for key in proof["byte_identical_descriptor_fields"]:
        require(saved[key] == current[key], "protected descriptor field changed: "+key)
    # Independent offset disk known answer, including arbitrary clipped strips.
    for y, z, radius, lo, hi in ((7., 11., 3., 4., 10.), (-2., 4., 2., -2.7, -1.1), (.3, -4., 1.7, -.6, 1.4)):
        near(frozen.disk_strip_moments(y, z, radius, lo, hi), disk_numeric(y, z, radius, lo, hi), absolute=1e-8)
    summary = json.loads((D/"result.json").read_bytes())
    maximum_error = check_summary(summary, saved, current, inp, descriptor_raw)
    source_audit = json.loads((ROOT/inp["sources"]["late_source_contract_audit"]["path"]).read_bytes())
    require(v4.source_contract_audit(current) == source_audit["audit"], "saved late schema audit differs")
    for ref in (summary["method"], summary["tests"], *summary["preserved_failures"]):
        require(digest((ROOT/ref["path"]).read_bytes()) == ref["sha256"], "compact evidence reference differs")
        pins[ref["path"]] = ref["sha256"]
    test_command = [sys.executable, "-B", "-m", "pytest", "--import-mode=importlib", "-q", "-p", "no:cacheprovider",
                    *(str(D/name) for name in TARGETS if name.endswith("test_descriptor.py"))]
    tests = subprocess.run(test_command, cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
    require(tests.returncode == 0 and "58 passed" in tests.stdout, tests.stdout+tests.stderr)
    frozen.join(pins, bundle["source_sha256"])
    pins[path_name(OWN)] = digest(OWN.read_bytes())
    with v2.source_context(frozen):
        frozen.verify(pins, ROOT)
    require(not any(n in sys.modules for n in ("cadquery", "OCP", "numpy")), "review must remain stdlib and saved-data only")
    receipt = {"schema": "eoere_z180_geometry_descriptors_independent_review/v1",
        "success": "independent_z180_descriptor_source_checks_pass", "independent_z180_descriptor_source_checks_pass": True,
        "status": "CLEAN_SAVED_DESCRIPTOR_SOURCE_AND_ANALYTIC_GEOMETRY_SCOPE", "findings": [],
        "descriptor": summary["descriptor"], "compact_result": {"path": path_name(D/"result.json"), "sha256": TARGETS["result.json"]},
        "geometry": saved["geometry"], "parent_descriptors": saved["parent_descriptors"],
        "checks": {"exact_full_descriptor_bytes_replayed_in_memory": True, "descriptor_input_source_pins": 1116,
            "source_pins_before_after_unchanged": True, "all58_frozen_source_tests_passed": True,
            "independent_profile_minus_four_bores_COM_for_old_and_new_receivers": True,
            "independent_full_rectangle_minus_disk_area_centroid_and_second_moments": True,
            "independent_angular_Simpson_actual12_cell_area_centroids": True,
            "maximum_independent_cell_area_difference_mm2": max(area_errors), "COM_Z_deltas_mm": com_delta,
            "four_shafts_twenty_roles_and_eight_gravity_owners_correctly_relocated": True,
            "sixteen_native_wall_rebindings_to_exact_new_finished_sources": True,
            "twelve_regions_and_two_floors_independently_sweep_separated": True,
            "all1606_own_contact_rows_join_and1442_unaffected_rows_identical": True,
            "compact_result_exact_refs_numerical_claims_and_limit_reconciled": True,
            "maximum_recorded_sampled_second_moment_relative_error": maximum_error,
            "protected_panels_66screws_96bolts_material_support_and_flange_primitives_identical": True},
        "counts": proof["counts"], "source_sha256": dict(sorted(pins.items())),
        "test_command": test_command, "test_result": tests.stdout.strip(), "python": sys.version,
        "execution": {"saved_JSON_source_bytes_and_stdlib_arithmetic_only": True, "descriptor_CLI_trial": False,
            "CAD_BREP_import_query_or_rebuild": False, "operator_preparation_K_q_native_or_frame_solve": False,
            "old_force_or_response_consumed": False},
        "limits": ["Only the exact unadopted Z180 source geometry descriptors and compact result were reviewed; no geometry adoption, force admission, physical contact or complete-joint capacity follows.",
            "Four saved native receiver volumes/walls are reused as their exact original observations. New four COMs and two six-cell patches are analytical derivations, not fresh native queries.",
            "Finite swept-cylinder separation proves recorded unchanged regions. Exact area moments and centroid quadrature remain distinct; the recorded maximum second-moment relative error remains diagnostic.",
            "Fresh Z180 input, cases, RHS, operators, mechanics execution and independent force admission remain separate work."],
        "release": copy.deepcopy(frozen.RELEASE)}
    output = OWN.with_name("receipt.json")
    with output.open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"receipt": path_name(output), "sha256": digest(output.read_bytes()),
                      "review_helper_sha256": digest(OWN.read_bytes()), "status": receipt["status"],
                      "source_pins": len(pins), "tests_passed": 58}, sort_keys=True))


if __name__ == "__main__":
    main()
