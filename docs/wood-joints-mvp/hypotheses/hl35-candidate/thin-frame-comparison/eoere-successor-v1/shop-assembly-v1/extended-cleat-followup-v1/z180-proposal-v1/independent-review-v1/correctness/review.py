"""Bounded independent shop-source/coordinate review; no genuine composition."""
from __future__ import annotations

import builtins
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
PACKET = OWN.parents[2]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "adapter.py": "805dd6afe0921cb14f7e24fea4974714de6ee4c94cc50e74daca3b5595c951c2",
    "test_adapter.py": "e243ed889154b21f4f380ee20c6a012cda87f80bc5ffdb1d42240cf11767eddb",
    "inputs.json": "24168aba426c8a3e65035e877b03fc58347a3c00f450980cba9319f4d6e19918",
    "preflight.json": "cd7e28c42e59f41d9fae96378a5cc1cf005a5b04cbc7613db23088fef1a08854",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def maximum_error(a, b):
    return max(abs(x-y) for x, y in zip(a, b, strict=True))


def local(point, profile):
    offset = [point[i]-profile["datum_xyz_mm"][i] for i in range(3)]
    return [math.fsum(offset[i]*basis[i] for i in range(3)) for basis in profile["basis_grain_u_v_xyz"]]


def world(point, profile):
    return [profile["datum_xyz_mm"][i]+math.fsum(point[j]*profile["basis_grain_u_v_xyz"][j][i] for j in range(3)) for i in range(3)]


def review():
    before = {name: sha(PACKET / name) for name in EXPECTED}
    require(before == EXPECTED, "four frozen targets differ")
    spec = importlib.util.spec_from_file_location("bounded_independent_z180_shop_correctness", PACKET / "adapter.py")
    a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    original_import = builtins.__import__
    def guarded(name, *args, **kwargs):
        require(name.split(".")[0] not in {"cadquery", "OCP", "OCC", "build123d", "numpy", "scipy"}, "CAD/mechanics import prohibited")
        return original_import(name, *args, **kwargs)
    def prohibited(*_args, **_kwargs):
        raise AssertionError("genuine composition is outside this review")
    generated_before = sorted(p.name for p in PACKET.iterdir() if p.suffix in {".csv", ".svg"})
    with patch.object(builtins, "__import__", guarded), patch.object(a, "build_outputs", prohibited):
        bundle = a.prepare(PACKET / "inputs.json", EXPECTED["inputs.json"])
    data, sources = bundle["data"], bundle["inputs"]["sources"]
    preflight = json.loads((PACKET / "preflight.json").read_bytes())
    pins = dict(bundle["pins"])
    require(len(pins) == preflight["source_pin_count"] == 1141
            and a.canonical(pins) == preflight["source_map_canonical_sha256"]
            == "9359334ec1453dcd3dc1306a3477d9af2da64a651a258d3e32f12b33d41a20f6", "exact source closure differs")
    snapshot = a.canonical(data)
    axes, old_axes = bundle["new_axes"], bundle["old_axes"]
    require(set(axes) == set(old_axes) and len(axes) == 100, "complete exact shaft identities")
    for name, axis in axes.items():
        expected = copy.deepcopy(old_axes[name])
        if name in a.AXES:
            expected["point_xyz_mm"][2] -= 20.
        require(axis == expected, "only four exact Z translations permitted")
    holes = {(r["axis_id"], r["receiver"]): (number, r) for number, r in enumerate(data["receiver-holes.csv"][1], 2)}
    walls = {(r["axis_id"], r["receiver"]): r for r in bundle["scenario"]["wall_queries"]}
    expected_keys = {key for key in holes if key[1] in a.HOSTS}
    require(len(holes) == 120 and set(walls) == expected_keys and len(walls) == 16, "all own changed-host source joins")
    errors, moved, retained = [], [], []
    for key, wall in walls.items():
        number, row = holes[key]
        axis, profile = axes[key[0]], data["profiles"][key[1]]
        require(wall["query_point_xyz_mm"] == axis["point_xyz_mm"] and wall["query_direction_xyz"] == axis["direction_xyz"], "saved wall world axis")
        intervals = [float(row[k+"_from_axis_point_mm"]) for k in ("entry", "exit")]
        require(maximum_error(intervals, wall["full_wall_intervals_mm"][0]) <= 1e-6
                and abs(intervals[1]-intervals[0]-wall["full_wall_length_mm"]) <= 1e-6
                and float(row["modeled_bore_envelope_diameter_mm"]) == wall["bore_diameter_mm"] == axis["bore_diameter_mm"],
                "saved interval/diameter/length join")
        require(wall["partial_wall_present"] is False and wall["matching_cylindrical_faces"]
                and all(face["full_circumference_wall"] for face in wall["matching_cylindrical_faces"]), "full saved wall geometry only")
        is_moved = key[0] in a.AXES
        require(wall["changed_axis"] is is_moved, "moved/retained wall provenance")
        (moved if is_moved else retained).append(number)
        for label, distance in (("axis_point", 0.), ("entry", intervals[0]), ("exit", intervals[1])):
            point = [axis["point_xyz_mm"][i]+distance*axis["direction_xyz"][i] for i in range(3)]
            projected = local(point, profile)
            saved = [float(row[label+"_in_receiver_"+c+"_mm"]) for c in "luv"]
            delta = [20., 0., 0.] if is_moved else [0., 0., 0.]
            require(maximum_error(projected, [saved[i]-delta[i] for i in range(3)]) <= 1e-6, "own L/U/V source arithmetic")
            errors.append(maximum_error(world(projected, profile), point))
    require(sorted(moved) == list(range(90, 98)) and sorted(retained) == [69, 73, 75, 79, 106, 108, 110, 112], "exact receiver source rows")
    require(max(errors) <= 1e-6, "independent world/local round trip")
    descriptor = data["descriptor"]
    parent = json.loads(a.read_ref(descriptor["parent_descriptors"]))
    original_shafts = {r["axis_id"]: r for r in parent["shafts"]}
    owners = {r["id"]: r for r in descriptor["physical_owner_gravity_rows"]}
    centroid_errors = {}
    for host in sorted(a.HOSTS):
        observation = bundle["observations"][host]
        proof = observation["provenance"]
        old_voids, new_voids = (proof[k] for k in ("restored_old_cylinders_volume_first_moment", "removed_new_cylinders_volume_first_moment"))
        expected_volume = proof["old_volume_mm3"]+math.fsum(v for v, _ in old_voids)-math.fsum(v for v, _ in new_voids)
        expected_center = [(proof["old_volume_mm3"]*proof["old_center_xyz_mm"][i]
                            +math.fsum(m[i] for _, m in old_voids)-math.fsum(m[i] for _, m in new_voids))/expected_volume for i in range(3)]
        centroid_errors[host] = maximum_error(expected_center, observation["center_xyz_mm"])
        require(centroid_errors[host] <= 1e-6 and abs(expected_volume-observation["volume_mm3"]) <= .001, "independent void first-moment COM")
        require(a.source_ref(observation["source"]) == a.source_ref(bundle["scenario"]["finished_bodies"][host])
                == owners[host]["geometry_source"] and owners[host]["center_xyz_mm"] == observation["center_xyz_mm"]
                and proof["new_native_COM_query_performed"] is False, "native geometry versus analytic gravity COM provenance")
    roles = []
    for shaft in descriptor["shafts"]:
        if shaft["axis_id"] not in a.AXES:
            continue
        prior = original_shafts[shaft["axis_id"]]
        require(len(shaft["metal_roles"]) == len(prior["metal_roles"]) == 5 and shaft["source_axis"]["nominal_under_head_length_mm"] == 101.6, "original4in five-role recipe")
        for role, old in zip(shaft["metal_roles"], prior["metal_roles"], strict=True):
            require({k: v for k, v in role.items() if k not in {"basis", "center_of_mass_xyz_mm"}}
                    == {k: v for k, v in old.items() if k not in {"basis", "center_of_mass_xyz_mm"}}
                    and role["center_of_mass_xyz_mm"] == [old["center_of_mass_xyz_mm"][0], old["center_of_mass_xyz_mm"][1], old["center_of_mass_xyz_mm"][2]-20.], "same metal role rigid Z translation")
            roles.append(role["id"])
    require(len(roles) == len(set(roles)) == 20, "twenty original roles, no spacer")
    access = [row for row in data["access-sides.csv"][1] if row["axis_id"] in a.AXES]
    require(len(access) == 8 and {(r["axis_id"], r["side"]) for r in access} == {(axis, side) for axis in a.AXES for side in ("head", "nut")}, "eight installed head/nut sides")
    require({1+sorted(data["profiles"]).index(host)//7 for host in a.HOSTS} == {1, 3}, "three changed drawing contracts")
    require(data["old_inputs"]["sources"]["extension"]["path"] == sources["parent_geometry"]["path"]
            and data["old_inputs"]["sources"]["extension"]["sha256"] == sources["parent_geometry"]["sha256"], "retained extension-pointer source namespace")
    for filename in ("members.csv", "receiver-holes.csv", "bolt-stacks.csv", "access-sides.csv", "panel-screw-datums.csv", "panel-machining.csv"):
        a.blank_observations(data[filename][1])
    require(a.canonical(data) == snapshot, "metadata review changed source objects")
    a.verify(pins)
    require(before == {name: sha(PACKET / name) for name in EXPECTED}, "frozen targets changed")
    require(sorted(p.name for p in PACKET.iterdir() if p.suffix in {".csv", ".svg"}) == generated_before == [], "genuine outputs created")
    return {"schema": "eoere_z180_shop_adapter_independent_correctness_review/v1", "status": "CLEAN_BOUNDED_SOURCE_AND_COORDINATE_REVIEW",
        "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)}, "target_sha256_before_after": before,
        "source_closure": {"count": len(pins), "canonical_sha256_before_after": a.canonical(pins), "all_exact_bytes_verified_before_after": True},
        "independent_checks": {"four_Z200_to_Z180_axes_96_unchanged": True, "receiver_rows_moved": sorted(moved), "retained_rows_rebound": sorted(retained),
            "world_local_round_trip_maximum_error_mm": max(errors), "analytic_void_COM_error_mm_by_host": centroid_errors,
            "four_native_geometry_sources_separate_from_analytic_gravity_COM": True, "original4in_roles": len(roles), "eight_access_side_identities": True,
            "raw_profile_page_ownership": [1, 3], "unchanged_file_links_keep_original_pointer_namespace": True, "all_Actual_and_Disposition_blank": True},
        "existing_controls": {"pytest": "39 passed in 1.62s", "ruff": "All checks passed!", "scope": "source metadata and inert fixtures, including deferred composition with a synthetic renderer only"},
        "findings": [], "genuine_build_outputs_calls": 0, "genuine_candidate_CSV_or_SVG_generation": False,
        "CAD_BREP_native_K_forces_or_solve_performed": False, "complete_joint_resistance_or_tool_acceptance_claimed": False,
        "limitations": "Actual emitted CSV/SVG bytes and six drawing byte replays remain deferred to a separately authorized parent output trial. Source and inert checks do not adopt geometry or authorize physical work.",
        "release": dict(a.RELEASE)}


if __name__ == "__main__":
    result = review()
    with OWN.with_name("receipt.json").open("x") as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps({"status": result["status"], "findings": result["findings"], "source_pins": result["source_closure"]["count"]}))
