"""Source-only Z180 cylinder/moment delta; no CAD or mechanics imports.

Saved observations remain observations of their exact original source. New
centroids, cells and material proofs are analytic descriptors, never new native
queries. No response, operator, support-law change or adoption is supplied.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
SCHEMA = "eoere_z180_geometry_delta_descriptors/v1"
INPUT_SCHEMA = "eoere_z180_geometry_delta_frozen_inputs/v1"
HOSTS = ("base_post_outer_left", "base_post_outer_right", "eoere_cleat_left", "eoere_cleat_right")
AXES = tuple("cleat_post_bolt_" + side + "_" + str(i) for side in ("left", "right") for i in (1, 2))
RELEASE = {key: False for key in ("candidate_admitted", "climbing", "complete_joint_resistance", "fabrication", "physical_contact", "structural")}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def indexed(rows, key):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), "duplicate " + key)
    return result


def exact_ref(ref, root=ROOT):
    require(set(ref) == {"path", "sha256"} and not Path(ref["path"]).is_absolute(), "exact relative source reference required")
    path = (root / ref["path"]).resolve()
    require(path.is_relative_to(root.resolve()) and sha(path) == ref["sha256"], "source bytes differ: " + ref["path"])
    return path


def verify(pins, root=ROOT):
    for path, digest in pins.items():
        exact_ref({"path": path, "sha256": digest}, root)


def join(pins, additions):
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, "source pin conflict: " + path)
        pins[path] = digest


def load_inputs(path, digest, *, root=ROOT):
    path = Path(path).resolve()
    require(path.is_relative_to(root.resolve()) and sha(path) == digest, "frozen input bytes differ")
    inp = json.loads(path.read_bytes())
    require(inp["schema"] == INPUT_SCHEMA and inp["release"] == RELEASE, "distinct unreleased Z180 input pins required")
    exact_ref(inp["helper"], root)
    require((root / inp["helper"]["path"]).resolve() == OWN and sha(OWN) == inp["helper"]["sha256"], "exact helper required")
    refs, records = inp["sources"], {}
    pins = {str(path.relative_to(root)): digest, inp["helper"]["path"]: inp["helper"]["sha256"]}
    for key, ref in refs.items():
        source = exact_ref(ref, root)
        join(pins, {ref["path"]: ref["sha256"]})
        if source.suffix == ".json":
            records[key] = json.loads(source.read_bytes())
    # These upstream byte closures are provenance checks, not imported code,
    # cached operators, coefficient fields or transferred acceptance.
    for key in ("current", "native", "receiver_inventory"):
        join(pins, records[key]["source_sha256"])
    current = records["current"]
    for row in current["finished_body_observations"]:
        source = row["source"]
        join(pins, {source["path"]: source["sha256"]})
    for scenario in records["native"]["scenarios"]:
        if scenario["scenario"] in {"current_Z200_modeled", "proposed_Z180_modeled"}:
            for source in scenario["finished_bodies"].values():
                join(pins, {source["path"]: source["sha256"]})
    verify(pins, root)
    return {"input": inp, "records": records, "source_sha256": pins, "root": root}


def close(actual, expected, tolerance, message):
    require(math.isfinite(actual) and math.isfinite(expected) and abs(actual - expected) <= tolerance, message)


def vector_close(actual, expected, tolerance, message):
    require(len(actual) == len(expected), message)
    for a, b in zip(actual, expected, strict=True):
        close(a, b, tolerance, message)


def cylinder_moments(point, direction, interval, diameter):
    require(len(point) == len(direction) == 3 and abs(direction[0]) == 1.
            and direction[1:] == [0., 0.] and interval[1] > interval[0] and diameter > 0., "full X cylinder required")
    volume = math.pi * (diameter / 2.)**2 * (interval[1] - interval[0])
    center = [p + g * sum(interval) / 2. for p, g in zip(point, direction, strict=True)]
    return volume, [volume * x for x in center]


def replace_centroid(old_volume, old_center, new_volume, removed, added):
    """Restore old voids, remove new voids. Caller proves full/disjoint bores."""
    require(min(old_volume, new_volume) > 0., "positive finished volume required")
    moment = [old_volume * x for x in old_center]
    for sign, cylinders in ((1., removed), (-1., added)):
        for _, first in cylinders:
            moment = [x + sign * y for x, y in zip(moment, first, strict=True)]
    return [x / new_volume for x in moment]


def rectangle_moments(y0, y1, z0, z1):
    require(y1 > y0 and z1 > z0, "positive rectangle required")
    area = (y1 - y0) * (z1 - z0)
    return [area, area * (y0 + y1) / 2., area * (z0 + z1) / 2.,
            area * (y0*y0 + y0*y1 + y1*y1) / 3., area * (y0 + y1) * (z0 + z1) / 4.,
            area * (z0*z0 + z0*z1 + z1*z1) / 3.]


def disk_strip_moments(y, z, radius, y0, y1):
    """Exact disk moments clipped in Y; full disk Z extent must fit its row.

    Coordinates are in a patch-local YZ chart. Integrate 2*sqrt(r²-t²),
    2*t*sqrt(r²-t²), 2*t²*sqrt(r²-t²), and 2/3*(r²-t²)**1.5.
    """
    require(radius > 0. and y1 > y0, "positive disk/strip required")
    lo, hi = max(-radius, y0 - y), min(radius, y1 - y)
    if hi <= lo:
        return [0.] * 6
    def primitive(t):
        s = math.sqrt(max(0., radius*radius - t*t))
        angle = math.asin(max(-1., min(1., t / radius)))
        return [t*s + radius*radius*angle, -2.*s**3 / 3.,
                (radius**4*angle + t*s*(2.*t*t-radius*radius)) / 4.,
                (t*s*(5.*radius*radius-2.*t*t) + 3.*radius**4*angle) / 12.]
    before, after = primitive(lo), primitive(hi)
    area, first, yy, zz = [a-b for a, b in zip(after, before, strict=True)]
    return [area, y*area+first, z*area, y*y*area+2.*y*first+yy,
            z*(y*area+first), z*z*area+zz]


def cell_moments(bounds, disks):
    y0, y1, z0, z1 = bounds
    result = rectangle_moments(*bounds)
    for y, z, radius in disks:
        if z + radius <= z0 or z - radius >= z1 or y + radius <= y0 or y - radius >= y1:
            continue
        require(z - radius >= z0 and z + radius <= z1, "disk crosses Z grid boundary; unsupported clipping")
        result = [a-b for a, b in zip(result, disk_strip_moments(y, z, radius, y0, y1), strict=True)]
    require(result[0] > 0., "positive remaining cell area required")
    return result


def yz_central(m):
    a, fy, fz, yy, yz, zz = m
    return [[0., 0., 0.], [0., yy-fy*fy/a, yz-fy*fz/a], [0., yz-fy*fz/a, zz-fz*fz/a]]


def matrix_norm(matrix):
    return math.sqrt(sum(x*x for row in matrix for x in row))


def polygon_clearance(point, polygon):
    distances = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1], strict=True):
        dy, dz = b[0] - a[0], b[1] - a[1]
        distances.append((dy*(point[1]-a[1]) - dz*(point[0]-a[0])) / math.hypot(dy, dz))
    return max(min(distances), min(-x for x in distances))


def material_at_reference(point, normal, profiles, axes, probe_depth=.05):
    """Analytic own-profile and all-bore exclusion at both inward probes."""
    proof = []
    for sign, profile in zip((1., -1.), profiles, strict=True):
        probe = [p + sign*probe_depth*n for p, n in zip(point, normal, strict=True)]
        xgap = min(probe[0]-profile["X_interval_mm"][0], profile["X_interval_mm"][1]-probe[0])
        pgap = polygon_clearance(probe[1:], profile["YZ_polygon_mm"])
        bore_gap = min(math.hypot(probe[1]-a["point_xyz_mm"][1], probe[2]-a["point_xyz_mm"][2])-a["bore_diameter_mm"]/2.
                       for a in axes if profile["host"] in a["receivers"])
        require(min(xgap, pgap, bore_gap) > 0., "analytic reference or inward probe lies outside material")
        proof.append({"host": profile["host"], "point_xyz_mm": probe,
                      "minimum_X_profile_clearance_mm": xgap, "minimum_YZ_profile_clearance_mm": pgap,
                      "minimum_bore_clearance_mm": bore_gap})
    return {"method": "analytic convex source profile and every own cylinder exclusion", "probe_depth_mm": probe_depth,
            "native_probe_performed": False, "both_own_material_probes_proved": True, "probes": proof}


def swept_separation(bounds, host, profiles, old_axes, new_axes, tolerance):
    """A disjoint coordinate interval proves a region avoids the whole sweep."""
    require(len(bounds) == 6, "six region bounds required")
    box = [[bounds[2*i], bounds[2*i+1]] for i in range(3)]
    proofs = []
    for axis_id in AXES:
        a, b = old_axes[axis_id], new_axes[axis_id]
        if host not in a["receivers"]:
            continue
        radius = a["bore_diameter_mm"] / 2.
        swept = [profiles[host]["X_interval_mm"], [a["point_xyz_mm"][1]-radius, a["point_xyz_mm"][1]+radius],
                 [min(a["point_xyz_mm"][2], b["point_xyz_mm"][2])-radius,
                  max(a["point_xyz_mm"][2], b["point_xyz_mm"][2])+radius]]
        gaps = [max(x[0]-s[1], s[0]-x[1]) for x, s in zip(box, swept, strict=True)]
        require(max(gaps) > tolerance, "unchanged region intersects old/new bore sweep: " + host)
        proofs.append({"axis_id": axis_id, "separating_coordinate": "XYZ"[gaps.index(max(gaps))], "gap_mm": max(gaps)})
    require(len(proofs) == 2, "two own moved cylinders required")
    return proofs


def patch_cells(patch, disks, *, profiles, all_axes):
    bounds = patch["trimmed_region_geometry"]["bounds_xyz_mm"]
    xlo, xhi, ymin, ymax, zmin, zmax = bounds
    require(abs(xhi-xlo) <= 1e-6 and patch["effective_cell_size_mm"] == 50.
            and patch["occupancy_refinement_levels"] == 0 and len(patch["cells"]) == 6,
            "frozen planar six-cell unrefined patch required")
    ny, nz = max(2, math.ceil((ymax-ymin)/50.)), max(2, math.ceil((zmax-zmin)/50.))
    require((ny, nz) == (3, 2), "frozen3x2 source partition required")
    local_disks = [(y-ymin, z-zmin, r) for y, z, r in disks]
    old_ids = {}
    for old in patch["cells"]:
        iy = min(ny-1, int((old["point_xyz_mm"][1]-ymin)*ny/(ymax-ymin)))
        iz = min(nz-1, int((old["point_xyz_mm"][2]-zmin)*nz/(zmax-zmin)))
        require((iy, iz) not in old_ids and min(iy, iz) >= 0, "unique source grid-cell join required")
        old_ids[iy, iz] = old["id"]
    cells, total = [], [0.]*6
    for iy in range(ny):
        for iz in range(nz):
            limits = [iy*(ymax-ymin)/ny, (iy+1)*(ymax-ymin)/ny, iz*(zmax-zmin)/nz, (iz+1)*(zmax-zmin)/nz]
            moments = cell_moments(limits, local_disks)
            point = [xlo, ymin+moments[1]/moments[0], zmin+moments[2]/moments[0]]
            cell = {"id": old_ids[iy, iz], "area_mm2": moments[0], "point_xyz_mm": point,
                    "analytic_cell_bounds_local_YZ_mm": limits, "analytic_material_at_reference":
                        material_at_reference(point, patch["normal_from_second_to_first_xyz"], profiles, all_axes)}
            cells.append(cell)
            total = [a+b for a, b in zip(total, moments, strict=True)]
    center = [xlo, ymin+total[1]/total[0], zmin+total[2]/total[0]]
    exact = yz_central(total)
    sampled = [[sum(c["area_mm2"]*(c["point_xyz_mm"][i]-center[i])*(c["point_xyz_mm"][j]-center[j]) for c in cells)
                for j in range(3)] for i in range(3)]
    error = matrix_norm([[sampled[i][j]-exact[i][j] for j in range(3)] for i in range(3)]) / matrix_norm(exact)
    return cells, total[0], center, exact, sampled, error


def prove_cylinders(old, new, native_old, native_new, profiles, coordinate_tol, volume_tol):
    """Join all16 local bores, including eight retained bores on changed hosts."""
    require(set(profiles) == set(HOSTS), "exact four receiver profiles required")
    proofs = {}
    for host in HOSTS:
        profile = profiles[host]
        own_old = [a for a in old.values() if host in a["receivers"]]
        own_new = [new[a["id"]] for a in own_old]
        require(len(own_old) == 4, "four own cylinders per changed host required")
        for rows, scenario in ((own_old, native_old), (own_new, native_new)):
            for axis in rows:
                wall = scenario[(axis["id"], host)]
                vector_close(wall["query_point_xyz_mm"], axis["point_xyz_mm"], coordinate_tol, "native wall point differs")
                vector_close(wall["query_direction_xyz"], axis["direction_xyz"], coordinate_tol, "native wall direction differs")
                close(wall["bore_diameter_mm"], axis["bore_diameter_mm"], 0., "native wall diameter differs")
                require(not wall["partial_wall_present"] and len(wall["full_wall_intervals_mm"]) == 1
                        and bool(wall["matching_cylindrical_faces"])
                        and all(f["full_circumference_wall"] for f in wall["matching_cylindrical_faces"]), "full native cylinder wall required")
                expected = sorted(axis["direction_xyz"][0]*(v-axis["point_xyz_mm"][0]) for v in profile["X_interval_mm"])
                vector_close(wall["full_wall_intervals_mm"][0], expected, coordinate_tol, "full cylinder end interval differs")
                close(wall["full_wall_length_mm"], profile["thickness_mm"], coordinate_tol, "full cylinder length differs")
                require(polygon_clearance(axis["point_xyz_mm"][1:], profile["YZ_polygon_mm"]) > axis["bore_diameter_mm"]/2., "cylinder truncated at profile edge")
            for i, a in enumerate(rows):
                for b in rows[i+1:]:
                    require(math.dist(a["point_xyz_mm"][1:], b["point_xyz_mm"][1:]) > (a["bore_diameter_mm"]+b["bore_diameter_mm"])/2., "own cylinders overlap")
        for axis in own_old:
            if axis["id"] in AXES:
                other = new[axis["id"]]
                require(math.dist(axis["point_xyz_mm"][1:], other["point_xyz_mm"][1:]) > axis["bore_diameter_mm"], "old and new voids overlap")
        proofs[host] = {"four_old_and_four_new_full_nonoverlapping_cylinders": True,
                        "source_thickness_mm": profile["thickness_mm"], "coordinate_tolerance_mm": coordinate_tol,
                        "recorded_volume_tolerance_mm3": volume_tol}
    return proofs


DATA_KEYS = ("parameters", "material_scenario", "support", "case_provider", "panel_refresh",
    "raw_gross_timber_rows", "physical_owner_gravity_rows", "auxiliary_metal_gravity_descriptors",
    "fitting_poses", "fitting_ports", "all_factory_holes", "shafts", "finished_receiver_wall_queries",
    "finished_body_observations", "hillman_rows", "current_panel_machining_descriptors",
    "timber_and_panel_shared_face_patches", "shared_pair_query_census", "flange_domains",
    "flange_shared_face_patches", "direct_contacts", "floor_observations")


def source_binding(row):
    return {key: copy.deepcopy(row[key]) for key in ("path", "sha256")}


def region_identity(patch, sources, current_ref, derivation):
    return {"schema": "eoere_z180_analytic_region_identity/v1", "first": patch["first"], "second": patch["second"],
        "current_finished_sources": {host: source_binding(sources[host]) for host in (patch["first"], patch["second"]) if host in sources},
        "region_geometry_canonical_sha256": canonical(patch["trimmed_region_geometry"]),
        "parent_export": current_ref, "parent_patch_id": patch["id"], "derivation": derivation}


def retire_native_patch_claims(patch, current_ref, old_patch):
    """Retain evidence by exact reference, not as a new-source face observation."""
    patch["inherited_native_observation"] = {"source_export": current_ref, "patch_id": old_patch["id"],
        "patch_canonical_sha256": canonical(old_patch), "observed_geometry_is_parent_Z200": True}
    for key in ("source_first_face", "source_second_face", "trimmed_region_signature_sha256",
                "coplanar_offset_mm", "opposed_normal_dot", "occupancy_refinement_levels"):
        patch.pop(key, None)
    for cell in patch["cells"]:
        for key in ("both_inward_material_probes_occupied", "reference_centroid_on_trimmed_patch", "reference_centroid_patch_distance_mm"):
            cell.pop(key, None)


def build_descriptor(bundle):
    """Pure metadata/arithmetic join. Caller authenticates files before/after."""
    records, inp = bundle["records"], bundle["input"]
    current, layout, native = (records[k] for k in ("current", "layout", "native"))
    current_ref, native_ref = inp["sources"]["current"], inp["sources"]["native"]
    require(current["schema"] == "eoere_extended_cleat_cached_source_export/v1" and current["release"] == RELEASE,
            "authentic current descriptor schema required")
    require(layout["schema"] == "eoere_lower_cleat_z180_geometry_patch/v1" and layout["revision"] == "eoere-lower-cleat-z180-proposal-v1"
            and layout["parent_geometry"] == current["geometry"] == inp["sources"]["current_geometry"]
            and layout["optional_2026_extra"] is False and layout["release"] == RELEASE
            and layout["saved_response_transferred"] is False, "exact unadopted OFF proposal required")
    require(records["viewer_verification"]["passed"] is True and records["viewer_verification"]["parent_review_consumed_native_digest_joined"] is True
            and records["viewer_verification"]["original_outputs"]["layout.json"]["sha256"] == inp["sources"]["layout"]["sha256"],
            "reviewed saved proposal descriptor required")
    require(records["native_review"]["schema"] == "eoere_four_finished_receiver_candidate01_independent_correctness_saved_result_review/v1"
            and records["native_review"]["status"] == "NO_SUBSTANTIAL_FINDINGS_WITHIN_SAVED_RESULT_SCOPE"
            and records["native_review"]["findings"] == [], "clean saved receiver review required")
    manifest = records["manifest"]
    require(manifest["schema"] == "eoere_z180_analytical_mechanics_frozen_sources/v1"
            and manifest["geometry"] == inp["sources"]["layout"] and manifest["parent_geometry"] == current["geometry"]
            and manifest["parent_descriptors"] == current_ref
            and manifest["readiness"] == {"candidate_operator_assembly_or_solve": False, "independent_field_admission": False,
                "source_only_analytic_descriptor_preparation": True} and not any(manifest["release"].values()),
            "parent source-only Z180 authority required")
    old_axes = indexed(records["current_geometry"]["axes"], "id")
    require(len(old_axes) == len(current["shafts"]) == 100 and len(current["hillman_rows"]) == 66
            and len(current["physical_owner_gravity_rows"]) == 150 and len(current["finished_body_observations"]) == 28,
            "protected100/66/150/28 census differs")
    require({s["axis_id"]: s["source_axis"] for s in current["shafts"]} == old_axes, "current physical shaft/source-axis join differs")
    require(canonical(list(old_axes.values())) == layout["current_100_axes_canonical_sha256"]
            and canonical([s["source_screw_descriptor"] for s in current["hillman_rows"]]) == layout["unchanged_66_screws_canonical_sha256"],
            "protected source-axis or screw canonical binding differs")
    proposed = indexed(layout["proposed_axes"], "id")
    require(set(proposed) == set(AXES) and {r["axis_id"] for r in layout["axis_changes"]} == set(AXES), "exact four moved axes required")
    new_axes = copy.deepcopy(old_axes)
    for axis_id, row in proposed.items():
        expected = copy.deepcopy(old_axes[axis_id])
        expected["point_xyz_mm"][2] -= 20.
        require(row == expected and row["nominal_under_head_length_mm"] == 101.6
                and row["bore_diameter_mm"] == 10.31875 and row["attachments"] == [], "only Z200-to-Z180 move with original4in hardware permitted")
        change = next(r for r in layout["axis_changes"] if r["axis_id"] == axis_id)
        require(change["current_point_xyz_mm"] == old_axes[axis_id]["point_xyz_mm"]
                and change["proposed_point_xyz_mm"] == row["point_xyz_mm"] and change["translation_xyz_mm"] == [0., 0., -20.], "axis patch point join differs")
        new_axes[axis_id] = copy.deepcopy(row)
    require(canonical(list(new_axes.values())) == layout["proposed_100_axes_canonical_sha256"], "full proposed100-axis closure differs")
    scenarios = indexed(native["scenarios"], "scenario")
    old_native, new_native = scenarios["current_Z200_modeled"], scenarios["proposed_Z180_modeled"]
    profiles = copy.deepcopy(records["receiver_inventory"]["affected_members"])
    for host, profile in profiles.items():
        profile["host"] = host
    tol = records["native_inputs"]["tolerances"]
    coordinate, volume = tol["coordinate_mm"], tol["volume_mm3"]
    require(tol == {"annular_fraction": 1e-8, "boolean_volume_mm3": .001, "coordinate_mm": 1e-6, "volume_mm3": .001}, "recorded native tolerance box differs")
    old_walls = {(r["axis_id"], r["receiver"]): r for r in old_native["wall_queries"]}
    new_walls = {(r["axis_id"], r["receiver"]): r for r in new_native["wall_queries"]}
    require(len(old_walls) == len(new_walls) == len(old_native["wall_queries"]) == len(new_native["wall_queries"]) == 16
            and set(old_walls) == set(new_walls), "complete16 own old/new wall joins required")
    cylinder_proof = prove_cylinders(old_axes, new_axes, old_walls, new_walls, profiles, coordinate, volume)
    observations = indexed(current["finished_body_observations"], "id")
    sources = {host: row["source"] for host, row in observations.items()}
    new_sources = dict(sources)
    data = {key: copy.deepcopy(current[key]) for key in DATA_KEYS}
    com_proof, comparisons = {}, indexed(old_native["current_finished_baseline_comparisons"], "receiver")
    for host in HOSTS:
        old_body, new_body, original = old_native["finished_bodies"][host], new_native["finished_bodies"][host], observations[host]
        require(source_binding(comparisons[host]["original"]) == source_binding(original["source"]), "native baseline source differs from COM source")
        require(max(comparisons[host]["reconstructed_missing_volume_mm3"], comparisons[host]["reconstructed_added_volume_mm3"]) <= tol["boolean_volume_mm3"], "native baseline volume equivalence failed")
        for label, body, axes, walls in (("old", old_body, old_axes, old_walls), ("new", new_body, new_axes, new_walls)):
            bores = [cylinder_moments(a["point_xyz_mm"], a["direction_xyz"], walls[(a["id"], host)]["full_wall_intervals_mm"][0], a["bore_diameter_mm"])
                     for a in axes.values() if host in a["receivers"]]
            close(body["volume_mm3"], profiles[host]["raw_volume_mm3"] - sum(v for v, _ in bores), volume, "raw-minus-four-cylinder " + label + " volume differs")
            close(body["raw_minus_four_bores_volume_error_mm3"], 0., volume, "native raw-minus-four-bores check failed")
        close(original["volume_mm3"], old_body["volume_mm3"], volume, "current COM volume differs from saved native old volume")
        require(layout["finished_receivers"][host] == {k: new_body[k] for k in layout["finished_receivers"][host]}, "displayed receiver source differs from native proposal")
        removed, added = [], []
        for axis_id in AXES:
            if host in old_axes[axis_id]["receivers"]:
                for rows, walls, out in ((old_axes, old_walls, removed), (new_axes, new_walls, added)):
                    a = rows[axis_id]
                    out.append(cylinder_moments(a["point_xyz_mm"], a["direction_xyz"], walls[(axis_id, host)]["full_wall_intervals_mm"][0], a["bore_diameter_mm"]))
        center = replace_centroid(original["volume_mm3"], original["center_xyz_mm"], new_body["volume_mm3"], removed, added)
        vector_close(center[:2], original["center_xyz_mm"][:2], coordinate, "equal-volume Z translation changed transverse COM")
        source = {"id": host, **copy.deepcopy(layout["finished_receivers"][host])}
        new_sources[host] = source
        com_proof[host] = {**cylinder_proof[host], "old_volume_mm3": original["volume_mm3"], "old_center_xyz_mm": original["center_xyz_mm"],
            "new_volume_mm3": new_body["volume_mm3"], "new_center_xyz_mm": center,
            "restored_old_cylinders_volume_first_moment": removed, "removed_new_cylinders_volume_first_moment": added,
            "method": "Vnew*Cnew=Vold*Cold+old_void_first_moments-new_void_first_moments", "new_native_COM_query_performed": False,
            "old_COM_observation_source": {"export": current_ref, "finished_source": source_binding(original["source"])},
            "saved_native_receiver_evidence": {"result": native_ref, "scenario": "proposed_Z180_modeled", "finished_source": source_binding(source)}}
        replacement = {"id": host, "source": source, "volume_mm3": new_body["volume_mm3"], "center_xyz_mm": center,
            "bounds_xyz_mm": new_body["bounds_xyz_mm"], "source_only_analytic_centroid": True, "provenance": com_proof[host]}
        data["finished_body_observations"] = [replacement if r["id"] == host else r for r in data["finished_body_observations"]]
        for owner in data["physical_owner_gravity_rows"]:
            if owner["id"] == host:
                owner.update(center_xyz_mm=center, mass_kg=new_body["volume_mm3"]*data["parameters"]["wood_density_kg_m3"]*1e-9,
                    mass_basis="saved native Z180 volume; analytic full-cylinder delta COM", geometry_source=source_binding(source))
    shaft_changes = []
    for shaft in data["shafts"]:
        if shaft["axis_id"] not in AXES:
            continue
        axis_id = shaft["axis_id"]
        require(shaft["point"] == old_axes[axis_id]["point_xyz_mm"] and len(shaft["metal_roles"]) == 5, "own four-shaft geometry/role join differs")
        shaft["point"][2] -= 20.
        shaft["source_axis"] = copy.deepcopy(new_axes[axis_id])
        for role in shaft["metal_roles"]:
            role["center_of_mass_xyz_mm"][2] -= 20.
            role["basis"] += "; rigid Z180 translation of the same nominal4in hardware, no spacer"
        for surface in shaft["surfaces"]:
            own = new_walls[(axis_id, surface["host"])]
            vector_close(surface["interval_mm"], own["full_wall_intervals_mm"][0], coordinate, "translated shaft own interval lacks new full wall")
        mass = sum(r["mass_kg"] for r in shaft["metal_roles"])
        center = [sum(r["mass_kg"]*r["center_of_mass_xyz_mm"][i] for r in shaft["metal_roles"])/mass for i in range(3)]
        owner = next(r for r in data["physical_owner_gravity_rows"] if r["id"] == shaft["body"])
        require(owner["mass_kg"] == mass, "same nominal shaft-role mass differs")
        owner["center_xyz_mm"] = center
        shaft_changes.append({"axis_id": axis_id, "body": shaft["body"], "translation_xyz_mm": [0., 0., -20.],
            "retained_shaft_basis_intervals_diameter_ends_and_mass": True, "own_roles_translated": [r["id"] for r in shaft["metal_roles"]]})
    wall_changes = []
    for i, wall in enumerate(data["finished_receiver_wall_queries"]):
        key = wall["axis_id"], wall["receiver"]
        if wall["receiver"] not in HOSTS:
            continue
        observed = copy.deepcopy(new_walls[key])
        observed["grain_axis_xyz"] = wall["grain_axis_xyz"]
        observed["finished_full_wall_intervals_from_axis_point_mm"] = copy.deepcopy(wall["finished_full_wall_intervals_from_axis_point_mm"])
        vector_close(observed["finished_full_wall_intervals_from_axis_point_mm"][0], observed["full_wall_intervals_mm"][0], coordinate, "saved new wall fails inherited mechanical interval")
        observed["observation_provenance"] = {"saved_native_result": native_ref, "scenario": "proposed_Z180_modeled",
            "finished_source": source_binding(new_sources[wall["receiver"]]), "query_performed_now": False}
        data["finished_receiver_wall_queries"][i] = observed
        wall_changes.append({"axis_id": key[0], "receiver": key[1], "axis_moved": key[0] in AXES})
    require(not any({p["first"], p["second"]} & set(HOSTS) for p in data["flange_shared_face_patches"]),
            "changed-host flange regions require an explicit own-source proof")
    patch_changes, region_reuse = [], []
    patch_index = {}
    for patch in data["timber_and_panel_shared_face_patches"]:
        old_patch = copy.deepcopy(patch)
        changed_hosts = [h for h in (patch["first"], patch["second"]) if h in HOSTS]
        is_changed = {patch["first"], patch["second"]} in [{"base_post_outer_"+side, "eoere_cleat_"+side} for side in ("left", "right")]
        if is_changed:
            own_profiles = [profiles[patch[k]] for k in ("first", "second")]
            axes = [old_axes, new_axes]
            evaluated = []
            for rows in axes:
                disks = [(*a["point_xyz_mm"][1:], a["bore_diameter_mm"]/2.) for a in rows.values()
                    if a["id"] in AXES and patch["first"] in a["receivers"]]
                evaluated.append(patch_cells(old_patch, disks, profiles=own_profiles, all_axes=list(rows.values())))
            old_cells, old_area, old_center, old_second, _, _ = evaluated[0]
            close(old_area, old_patch["area_mm2"], max(1e-5, old_area*1e-8), "analytic old patch area does not reconcile native source")
            vector_close(old_center, old_patch["centroid_xyz_mm"], 1e-6, "analytic old patch centroid differs from native source")
            by_id = indexed(old_patch["cells"], "id")
            for cell in old_cells:
                close(cell["area_mm2"], by_id[cell["id"]]["area_mm2"], max(1e-5, cell["area_mm2"]*1e-8), "old clipped cell area differs")
                vector_close(cell["point_xyz_mm"], by_id[cell["id"]]["point_xyz_mm"], 1e-6, "old clipped cell centroid differs")
            cells, area, center, exact, sampled, error = evaluated[1]
            patch.update(cells=cells, area_mm2=area, centroid_xyz_mm=center,
                exact_centroidal_second_moment_matrix_xyz_mm4=exact, sampled_centroidal_second_moment_matrix_xyz_mm4=sampled,
                second_moment_relative_frobenius_error=error, cell_area_error_mm2=sum(c["area_mm2"] for c in cells)-area,
                cell_centroid_error_mm=math.dist([sum(c["area_mm2"]*c["point_xyz_mm"][i] for c in cells)/area for i in range(3)], center),
                cell_semantics="analytic clipped-area resultants; source-profile/bore-exclusion material proof; no native queries")
            patch["trimmed_region_geometry"] = {"surface_type": "PLANE", "bounds_xyz_mm": old_patch["trimmed_region_geometry"]["bounds_xyz_mm"],
                "area_mm2": area, "center_xyz_mm": center, "analytic_description": "source overlap rectangle minus two full Z180 disks",
                "disk_axes": [new_axes[a] for a in AXES if patch["first"] in new_axes[a]["receivers"]]}
            old_error = matrix_norm([[old_second[i][j]-old_patch["exact_centroidal_second_moment_matrix_xyz_mm4"][i][j] for j in range(3)] for i in range(3)]) / matrix_norm(old_second)
            patch_changes.append({"id": patch["id"], "cells": len(cells), "old_native_exact_vs_analytic_second_moment_relative_error": old_error,
                "old_sampled_second_moment_relative_error": old_patch["second_moment_relative_frobenius_error"],
                "new_sampled_second_moment_relative_error": error, "second_moment_error_is_diagnostic_not_acceptance": True,
                "cell_deltas": [{"id": c["id"], "area_delta_mm2": c["area_mm2"]-by_id[c["id"]]["area_mm2"],
                    "centroid_delta_xyz_mm": [v-w for v, w in zip(c["point_xyz_mm"], by_id[c["id"]]["point_xyz_mm"], strict=True)]} for c in cells]})
            derivation = "analytic full-disk replacement in unchanged source rectangle/grid"
        elif changed_hosts:
            proofs = {host: swept_separation(patch["trimmed_region_geometry"]["bounds_xyz_mm"], host, profiles, old_axes, new_axes, coordinate) for host in changed_hosts}
            for cell in patch["cells"]:
                require(cell["both_inward_material_probes_occupied"] is True and cell["reference_centroid_on_trimmed_patch"] is True,
                        "inherited source material observation absent")
                cell["analytic_material_at_reference"] = {"method": "inherited occupied reference; whole region avoids moved bore sweep",
                    "native_probe_performed": False, "old_observation_source": {"export": current_ref, "cell_id": cell["id"]}, "region_sweep_proofs": proofs}
            patch["unchanged_region_sweep_proofs"] = proofs
            region_reuse.append({"id": patch["id"], "changed_hosts": changed_hosts, "proofs": proofs})
            derivation = "inherited region after finite swept-cylinder separation"
        else:
            continue
        retire_native_patch_claims(patch, current_ref, old_patch)
        patch["source_region_identity"] = region_identity(patch, new_sources, current_ref, derivation)
        patch["analytic_source_region_sha256"] = canonical(patch["source_region_identity"])
        patch_index[patch["id"]] = patch
    require(len(patch_changes) == 2 and len(region_reuse) == 12, "two rebuilt/twelve changed-host inherited regions required")
    for contact in data["direct_contacts"]:
        patch = patch_index.get(contact["source_patch_id"])
        if patch is None:
            continue
        cell = next(c for c in patch["cells"] if c["id"] == contact["id"])
        contact.update(point_xyz_mm=cell["point_xyz_mm"], reference_area_mm2=cell["area_mm2"],
            stiffness=contact["bedding_n_mm3"]*cell["area_mm2"], source_region_identity_sha256=patch["analytic_source_region_sha256"],
            source_only_region_provenance=patch["source_region_identity"])
        for key in ("source_first_face_signature_sha256", "source_second_face_signature_sha256", "source_trimmed_region_signature_sha256"):
            contact.pop(key, None)
    floor_reuse = []
    for floor in data["floor_observations"]:
        if floor["host"] not in HOSTS:
            continue
        points, host = floor["observed_normal_reference_points_xyz_mm"], floor["host"]
        bounds = [v for i in range(3) for v in (min(p[i] for p in points), max(p[i] for p in points))]
        proof = swept_separation(bounds, host, profiles, old_axes, new_axes, coordinate)
        floor["inherited_floor_observation"] = {"export": current_ref, "finished_source": source_binding(sources[host]),
            "current_finished_source": source_binding(new_sources[host]), "whole_footprint_sweep_separation": proof}
        floor.pop("own_floor_face_confirmed_from_current_cached_solid", None)
        floor.pop("own_floor_face_confirmation_required", None)
        floor["source_only_unchanged_floor_region_proved"] = True
        floor_reuse.append(host)
    untouched = [k for k in DATA_KEYS if data[k] == current[k]]
    proof = {"COM": com_proof, "shafts": shaft_changes, "wall_source_rebindings": wall_changes, "rebuilt_patches": patch_changes,
        "changed_host_inherited_regions": region_reuse, "changed_host_inherited_floor_regions": floor_reuse,
        "byte_identical_descriptor_fields": untouched,
        "counts": {"finished_owners_changed": 4, "finished_owners_reused": 24, "shaft_axes_changed": 4, "shaft_axes_reused": 96,
            "hardware_role_locations_changed": 20, "wall_occurrences_moved": 8, "wall_occurrences_rebound_same_axis": 8,
            "wall_occurrences_reused": 104, "contact_patches_rebuilt": 2, "contact_cells_rebuilt": 12,
            "changed_host_other_regions_rebound": len(region_reuse), "floor_regions_rebound": len(floor_reuse),
            "physical_owners": len(data["physical_owner_gravity_rows"]), "shafts": len(data["shafts"]), "Hillman_screws": len(data["hillman_rows"]),
            "contact_cells_total": len(data["direct_contacts"]), "timber_panel_patches_total": len(data["timber_and_panel_shared_face_patches"]),
            "flange_patches_total": len(data["flange_shared_face_patches"])}}
    return {"schema": SCHEMA, "status": "SOURCE_ONLY_UNADOPTED_Z180_DESCRIPTORS_PENDING_INDEPENDENT_REVIEW",
        "geometry": inp["sources"]["layout"], "parent_geometry": current["geometry"], "parent_descriptors": current_ref,
        "manifest": inp["sources"]["manifest"], "inherited_current_manifest": current["manifest"],
        "source_sha256": copy.deepcopy(bundle["source_sha256"]), **data, "geometry_delta_proof": proof,
        "inherited_observation_source": current_ref, "inherited_native_receiver_evidence": native_ref,
        "native_CAD_BREP_import_K_panel_preparation_response_or_solve_performed": False,
        "current_4in_hardware_retained_spacer_proposal_excluded": True,
        "historical_q_forces_operators_or_acceptance_transferred": False,
        "force_execution_readiness_claimed": False, "complete_joint_resistance": None,
        "unresolved_joins": ["Distinct Z180 mechanics input/review/method/producer/admission and parent serial slot are not supplied by this geometry descriptor.",
            "Parent must validate unchanged panel/material primitive reuse and construct fresh own-case maps, RHS, operators and response.",
            "Exact analytic area second moments and centroid-quadrature error are distinct; pressure, rocking accuracy and physical applicability remain unqualified."],
        "release": copy.deepcopy(RELEASE)}


def write_descriptor(inputs_path, inputs_sha256, out):
    """Reserve a fresh ignored output before source intake; retain failures."""
    out = Path(os.path.abspath(out))
    require(out.parent.resolve().is_relative_to((OWN.parent / "runs-v1").resolve()), "full descriptor belongs under this packet runs-v1")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x+") as handle:
        reserved = os.fstat(handle.fileno())
        def write(value):
            current_inode = out.lstat()
            require((current_inode.st_dev, current_inode.st_ino) == (reserved.st_dev, reserved.st_ino), "reserved output identity changed")
            handle.seek(0)
            json.dump(value, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
            handle.write("\n")
            handle.truncate()
            handle.flush()
        write({"schema": SCHEMA, "status": "STARTED", "release": RELEASE})
        try:
            loaded = load_inputs(inputs_path, inputs_sha256, root=ROOT)
            result = build_descriptor(loaded)
            verify(loaded["source_sha256"], loaded["root"])
            result["source_pins_before_after_unchanged"] = True
            write(result)
        except BaseException as error:
            write({"schema": SCHEMA, "status": "FAILED", "error_type": type(error).__name__, "error": str(error),
                "accepted_response": None, "accepted_actions": None, "release": RELEASE})
            raise
    return {"path": str(out.relative_to(ROOT)), "sha256": sha(out), "bytes": out.stat().st_size,
            "counts": result["geometry_delta_proof"]["counts"], "force_execution_readiness_claimed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(write_descriptor(args.inputs, args.inputs_sha256, args.out), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
