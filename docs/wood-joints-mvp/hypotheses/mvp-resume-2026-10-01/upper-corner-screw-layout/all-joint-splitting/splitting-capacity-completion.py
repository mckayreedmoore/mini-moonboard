"""Three-dimensional crack-compliance comparisons on the reviewed 104-axis wood.

prepare/summarize are lightweight postprocessors. coupon/solve perform sparse
solid-mechanics calculations and are reserved for the parent's serialized slot.
No six-bore proposal spine is imported. Existing results are never overwritten.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import platform
import sys
import time
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPPER = HERE.parent
RESUME = UPPER.parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
RAW = HERE / "rawlocal/splitting-capacity-completion"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PRIORITY = (
    "knee_outer_left_spine", "knee_outer_right_spine",
    "center_post_cleat_left", "center_post_cleat_right",
    "center_principal_cleat_left", "center_principal_cleat_right",
    "knee_outer_left_inner_frame_block", "knee_outer_right_inner_frame_block",
)
BASELINE = RESUME / "member-screen-attempt02/four-screw-layout01"
FRESH = RESUME / "member-screen-attempt02/knee-bridge-gravity01"
PERMANENT = UPPER / "rawlocal/dead-load-check/parent-attempt06"
CORRECTION = RESUME / "top-corner-correction/proposal.json"
SURFACES = RESUME.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
REGISTER = UPPER / "rawlocal/working-joint-register/attempt03/register.json"
COMMON = UPPER / "rawlocal/knee-common-shafts/attempt01"
OPENING = HERE / "rawlocal/common-spine-opening/attempt02"
HEADER = HERE / "rawlocal/header-fresh-force-adapter/attempt02"
ALL_DUTIES = HERE / "rawlocal/attempt01/checks.json"
BRICK = RESUME / "corner_frame.py"
PINS = {
    PERMANENT / "comparison.json": "20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75",
    PERMANENT / "response.npz": "9ff6f4ca177029b2c03acfb5425be9f943ad34679c8ab59013eb36764dd92f14",
    PERMANENT / "member-actions.npz": "cfe750ab9082ed854a5d641b781cd420fa79bbdaba3fa5978570ae7f20f6fa09",
    PERMANENT / "body-balances.json": "8d67f12d5f67b24c678c037cfe30826633a6e1ed6be25aa4054a60ec4d587baf",
    CORRECTION: "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
    BASELINE / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    BASELINE / "action-section-arrays.npz": "ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf",
    BASELINE / "member-results.json": "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    FRESH / "action-section-arrays.npz": "3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596",
    FRESH / "member-results.json": "5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0",
    REGISTER: "c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c",
    UPPER / "frame-250-attempt02/response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    SURFACES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    ALL_DUTIES: "91124cdd68bd440d5221047f77d81b47f13cbcf06e68093f3ebc6c5091a74fb9",
    OPENING / "checks.json": "949770568a16880c0477109a244cc76a9b634be28fc74e6216ff8eea3a9d7a39",
    OPENING / "receipt.json": "5f0c6a62f928f4007baabafba541e04679bb7c9f360abced5216a8e36f8d20aa",
    HEADER / "fresh-header-actions.jsonl.gz": "09293d656b0a3b49c2fe770a1b5962371c01f5ca793552edda4beed7d4d1c59b",
    HEADER / "checks.json": "94e8f4c698772530ac25df0bc5f91715db64078bba1c27fc26b42545d86680b6",
    HEADER / "receipt.json": "5294be28ae9854dc5b90641c8223a64d7fca817d1494d90965f2c6d3173be738",
    BRICK: "726f058d488e2dc9e7f83abc5537246afd994102ccddaee17416a7126a610f5d",
    ROOT / "fea/horizontal_panel_frame.py": "9ac5ceb2bd76ffddb6c048f92e54082a4672d72aab635ba2230e4352253378d9",
    ROOT / "fea/floor_recess_mesh.py": "518e3ee913537fb0e42a6dd843166974a011299921e116759bf2d330f221d184",
    ROOT / "fea/wood_joint_reduced_members.py": "825bd3a8463eef3fbd7df9bd4892b20b660d980f5c94088537ce7a0a5d058335",
    ROOT / "fea/wood_joint_patch_materials.py": "ecbbd11a8a0e99ece69aeb5cb4159e7cf17e0aa18c509c78b5c8f5a2e573ae78",
}
REFERENCES = [
    {"id": "jensen2016", "url": "https://onlinelibrary.wiley.com/doi/10.1155/2016/9402650",
     "use": "Section 3, compliance energy law; Section 3.3, initiation strength and finite flaws; Sections 4/5, three-dimensional and short-beam limitations. No bottom-rail scalar capacity is transferred."},
    {"id": "romanowicz2024", "url": "https://link.springer.com/article/10.1007/s10704-024-00798-z",
     "use": "Appendix equations 7, 9, 10: orthotropic DCB known-answer compliance, root correction and energy release. Pine test properties are not transferred."},
    {"id": "fpl2021", "url": "https://research.fs.usda.gov/fpl/wood-handbook",
     "use": "Chapter 5, orthotropic elasticity. Reuse the repository's explicitly unmeasured Douglas-fir elastic scenario, including both R/T bindings."},
]
ASSUMPTIONS = {
    "Gc_all_modes_n_per_mm": 0.100,
    "Ft90_mpa": 0.500,
    "property_status": "Explicit conditional lower-bound hypotheses for the modeled wood and crack orientations; not NDS DF-L No.2 design values, measurements, or characteristic-to-design conversions.",
    "flaw": "Full-front straight end slit on each named transverse plane, initially 5 mm long and extended to 10 mm from each grain end. Crack faces are traction free. No reinforcement, preload or friction is credited.",
    "law": "G = (f.T u_extended - f.T u_initial)/(2 * added_sound_crack_area). Fixed simultaneous loads; compare total mixed-mode G with the assumed common lower fracture threshold. Retain every signed force and free couple.",
    "initiation": "Intact three-dimensional integration-point transverse tensile stress compared with the independent conditional Ft90. It is a finite mesh stress result, not a certified continuous maximum.",
    "boundary": "Statically equivalent minimum-norm force/moment distribution over nearby retained mesh nodes, reusing distribute_wrench. Source points, original free couples, all body loads and their whole-body wrench are retained. This placement is an explicit conditional local model, not recovered contact pressure.",
    "mixed_mode": "Gc >= 0.100 N/mm is assumed in every mode and mixture. A Mode-I measurement alone cannot establish that hypothesis. No separate measured Mode-II/III resistance is invented.",
    "duration": "No NDS CD is applied to fracture toughness or Ft90. The permanent and six live states require their own force maps; a live result is not a permanent result.",
    "contact_upper_bound": "For each fixed load vector and unchanged sound elastic solid, intact kinematics are admissible in the contact-constrained initial crack, whose strain energy is no smaller than intact energy; contact-constrained final energy is no greater than traction-free final energy. Therefore (U_final_free - U_intact)/added_area bounds the initial-to-final contact energy increment above. This deliberately includes release of the initial flaw and is separate from free-face finite-difference G. It is an upper reference comparison, not an observed fracture demand.",
    "graded_mesh": "Cross-section pitch is the requested mesh size. Grain pitch is at most four times that size away from frozen bore/path breakpoints. The same full breakpoint set is used intact/initial/final; both transverse and grain pitches halve together. Removed cylindrical cells and clipped profiles are center-classified voxel approximations, with separate retained-volume and response-convergence guards.",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def key(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "Changed frozen input: " + str(path))


def new_output(output):
    output = Path(output).resolve()
    require(output.is_relative_to(RAW.resolve()) and output != RAW.resolve(), "Output must be a new owned rawlocal child")
    output.mkdir(parents=True, exist_ok=False)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return output


def jsonl(path):
    with gzip.open(path, "rt") if str(path).endswith(".gz") else Path(path).open() as stream:
        for line in stream:
            yield json.loads(line)


def receipt(output, pins, started, files):
    authenticate(pins)
    write(output / "receipt.json", {
        "producer_sha256": sha(output / "producer.py.snapshot"),
        "source_sha256": {key(p): h for p, h in pins.items()},
        "output_sha256": {name: sha(output / name) for name in ["producer.py.snapshot", *files]},
        "elapsed_seconds": time.monotonic() - started,
        "python": platform.python_version(), "geometry_changed": False,
        "tests_or_review_run": False, "complete_joint_acceptance": False,
    })


def libraries():
    """Import existing implementations without invoking their build functions."""
    sys.dont_write_bytecode = True
    for path in (ROOT, RESUME):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    import numpy as np
    from scipy import sparse
    from scipy.sparse.linalg import splu
    from fea.floor_recess_mesh import CORNERS, EDGES
    from fea.horizontal_panel_frame import distribute_wrench
    from fea.wood_joint_patch_materials import material_scenario
    spec = importlib.util.spec_from_file_location("splitting_existing_brick", BRICK)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return np, sparse, splu, np.vstack((CORNERS, EDGES)), distribute_wrench, material_scenario, helper


def actions_from_archive(archive, body, case, record):
    points = archive[body + "__point_xyz_mm"]
    values = archive[case + "__" + body + "__point_force_free_couple_xyz"]
    return [dict(source_id=i, role=r, point_mm=p.tolist(), force_n=q[:3].tolist(), free_moment_nmm=q[3:].tolist())
            for i, r, p, q in zip(record["point_action_ids"], record["point_action_roles"], points, values, strict=True)]


def full_wrench(actions, datum):
    import numpy as np
    answer = np.zeros(6)
    for a in actions:
        f = np.array(a["force_n"])
        answer[:3] += f
        answer[3:] += np.cross(np.array(a["point_mm"]) - datum, f) + a["free_moment_nmm"]
    return answer


def geometry_record(body, member, surface, correction, register, pins):
    import numpy as np
    g = member["geometry"]
    frame = np.array([g[n] for n in ("axis", "section_u", "section_v")])
    start = np.array(g["start"])
    length = float(frame[0] @ (np.array(g["end"]) - start))
    bores = []
    removed = set(member["replaced_original_bore_features"])
    for feature in surface["features"]:
        if feature["surface_kind"] != "CYLINDER" or feature["feature_id"] in removed:
            continue
        c = feature["cylinder"]
        require(c["material_side_geometry"] == "bore_like", "Unbound cylinder material side")
        bores.append({"id": feature["feature_id"], "origin": (frame @ (np.array(c["axis_origin_global_xyz_mm"]) - start)).tolist(),
                      "axis": (frame @ np.array(c["axis_unit_global_xyz"])).tolist(),
                      "radius_mm": c["radius_mm"], "interval_mm": c["axis_parameter_interval_mm"]})
    actual_intervals = [b for b in member["bore_or_passage_intervals"]
                        if not b["id"].endswith("/owner_authorized_station_exclusion")]
    source_supported = (len(bores) == len(actual_intervals)
                        and surface["step_binding"]["file_sha256"] == member["current_finished_step_sha256"])
    prop = next((p for p in correction["proposals"] if p["block"] == body), None)
    side_prop = next((p for p in correction["proposals"] if "base_side_" + p["block"].split("_")[-2] == body), None)
    actual_volume = g.get("geometry_diagnostics", {}).get("actual_step_volume_mm3")
    caps = {f["feature_id"] for f in surface["features"] if f["surface_kind"] == "PLANE"
            and len(f["trim"]["wires"]) == 1 and f["trim"]["wires"][0]["edge_count"] == 1
            and f["trim"]["wires"][0]["edges"][0]["curve_kind"] == "CIRCLE"}
    planes = [{"normal": (frame @ np.array(p["normal"])).tolist(), "offset": float(p["offset"] - np.array(p["normal"]) @ start)}
              for p in member["profile_planes"] if p["id"] not in caps]
    if prop or side_prop:
        require(correction["proposal_step_sha256"][member["current_finished_step"]] == member["current_finished_step_sha256"], "Corrected STEP binding differs")
        if prop:
            bores = []  # Whole corrected cleat replaces its earlier four walls.
        axes = {a["axis_id"]: a for a in register["axes"]}
        for axis in (prop or side_prop)["axes"]:
            if side_prop and "/rail_" in axis["axis_id"]:
                continue
            point = frame @ (np.array(axis["proposed_axis_point_mm"]) - start)
            direction = frame @ np.array(axes[axis["axis_id"]]["outer_tie"]["direction_global_xyz"])
            shaft = int(np.argmax(abs(direction)))
            require(shaft in (1, 2) and abs(abs(direction[shaft]) - 1) < 1e-7, "Corrected bore must remain transverse")
            limits = [-math.inf, math.inf]
            for p in planes:
                n = np.array(p["normal"])
                den = float(n @ direction)
                if abs(den) > 1e-8:
                    t = float((p["offset"] - n @ point) / den)
                    limits[1 if den > 0 else 0] = min(limits[1], t) if den > 0 else max(limits[0], t)
            require(all(math.isfinite(x) for x in limits) and limits[1] > limits[0], "Corrected bore has no finite profile interval")
            bores.append({"id": axis["axis_id"] + "/corrected_bore", "origin": point.tolist(), "axis": direction.tolist(),
                          "radius_mm": axis["proposed_CAD_bore_envelope_mm"] / 2, "interval_mm": limits,
                          "source_recipe": key(CORRECTION)})
        actual_volume = prop["finished_proposal_volume_mm3"] if prop else next(p["finished_host_volume_mm3"] for p in correction["side_host_bore_replacements"] if p["host"] == body)
        source_supported = len(bores) == len(actual_intervals)
    pins[ROOT / member["current_finished_step"]] = member["current_finished_step_sha256"]
    if body.endswith("_spine"):
        require(len(bores) == 4, "Reviewed spine must have exactly four bores")
    if member["recess_source"] is not None:
        actual_volume = member["recess_source"]["step_drilled_volume_mm3"]
    return {"body": body, "frame": frame.tolist(), "start": start.tolist(), "length_mm": length,
            "width_mm": g["width_mm"], "depth_mm": g["depth_mm"], "bores": bores, "planes": planes,
            "recess_source": member["recess_source"], "actual_volume_mm3": actual_volume if source_supported else None,
            "step_source": member["current_finished_step"], "step_sha256": member["current_finished_step_sha256"],
            "finished_catalog_matches_current_STEP": source_supported,
            "catalog_limit": None if source_supported else "Join the existing corrected top-corner/top-host bore geometry recipe; the earlier surface catalog is not the current finished timber.",
            "screw_station_exclusions_are_not_physical_holes": [b for b in member["bore_or_passage_intervals"] if b not in actual_intervals]}


def prepare(output):
    """Bind all baseline duty actions and the distinct priority fresh comparisons."""
    import numpy as np
    started = time.monotonic()
    pins = dict(PINS)
    authenticate(pins)
    register = read(REGISTER)
    require(len(register["axes"]) == 104 and len(register["panel_kicker_screws"]) == 66, "Reviewed axis/screw census differs")
    require(register["source_sha256"][key(UPPER / "frame-250-attempt02/response.npz")] == PINS[UPPER / "frame-250-attempt02/response.npz"], "Baseline force authority differs")
    members = read(BASELINE / "geometry.json")["members"]
    surfaces = {r["member_id"]: r for r in read(SURFACES)["records"]}
    duties = read(ALL_DUTIES)["joint_duties"]
    require(len(duties) == 30 and len(members) == 44, "All-duty coverage differs")
    correction = read(CORRECTION)
    geometries = {b: geometry_record(b, m, surfaces[b], correction, register, pins) for b, m in members.items()}
    records = []
    with np.load(BASELINE / "action-section-arrays.npz", allow_pickle=False) as arrays:
        for body, member in members.items():
            for case in CASES:
                actions = actions_from_archive(arrays, body, case, member)
                records.append({"basis": "reviewed104_baseline_gravity", "body": body, "case_id": case, "actions": actions,
                                "source": key(BASELINE / "action-section-arrays.npz"), "opening_demand_n": None})
    permanent = read(PERMANENT / "comparison.json")
    require(permanent["load_case"] == "dead-only" and permanent["live_gravity_scale"] == permanent["live_horizontal_scale"] == permanent["live_moment_scale"] == 0., "Permanent source includes live actions")
    require(permanent["source_sha256"][key(UPPER / "frame-250-attempt02/response.npz")] == PINS[UPPER / "frame-250-attempt02/response.npz"], "Permanent reviewed response differs")
    for source, digest in permanent["source_sha256"].items():
        path = ROOT / source
        if path.name == "bottom_corner_checks.py" and sha(path) != digest:
            snapshot = RESUME / "bottom-corner-component-attempt06/producer.py.snapshot"
            require(sha(snapshot) == digest and snapshot.read_text().replace('"reviewed_geometry_changed": False,', '"reviewed_geometry_changed": member_report.get("reviewed_geometry_changed", False),') == path.read_text(), "Permanent historical reporting-only adapter differs")
            pins[snapshot] = digest
            pins[path] = sha(path)
            continue
        require(path not in pins or pins[path] == digest, "Permanent source pin conflict")
        pins[path] = digest
    with np.load(PERMANENT / "member-actions.npz", allow_pickle=False) as dead, np.load(BASELINE / "action-section-arrays.npz", allow_pickle=False) as baseline:
        for body, member in members.items():
            for case in ("dead-only_zero", "dead-only_gap"):
                points = baseline[body + "__point_xyz_mm"]
                values = dead[case + "__" + body + "__point_force_free_couple_xyz"]
                actions = [dict(source_id=i, role=r, point_mm=p.tolist(), force_n=q[:3].tolist(), free_moment_nmm=q[3:].tolist())
                           for i, r, p, q in zip(member["point_action_ids"], member["point_action_roles"], points, values, strict=True)]
                records.append({"basis": "reviewed104_permanent", "body": body, "case_id": case, "actions": actions,
                                "source": key(PERMANENT / "member-actions.npz"), "opening_demand_n": None})
    opening = read(OPENING / "checks.json")
    source_pins = read(OPENING / "receipt.json")["source_sha256"]
    with np.load(FRESH / "action-section-arrays.npz", allow_pickle=False) as arrays:
        for index, state in enumerate(opening["states"]):
            path = COMMON / state["common_state_path"]
            pins[path] = source_pins[key(path)]
            require(sha(path) == pins[path], "Common state differs")
            common = read(path)
            body, case = state["body"], state["case_id"]
            replaced = {a["axis_id"] for a in state["common_axis_records"]}
            actions = [a for a in actions_from_archive(arrays, body, case, members[body])
                       if a["source_id"].rsplit("/", 1)[0] not in replaced]
            for shaft in common["shafts"]:
                require(shaft["axis_id"] in replaced, "Unexpected common shaft")
                for field in shaft["bore_fields"]:
                    if field["receiver"] == body:
                        actions.append(dict(source_id=shaft["axis_id"] + "/saved_bore_field", role="common_bore_traction",
                                            point_mm=field["reference_point_mm"], force_n=field["force_on_wood_xyz_n"], free_moment_nmm=[0., 0., 0.]))
                for seat in shaft["outer_seat_fields"]:
                    if seat["receiver"] == body:
                        t = seat["point_tractions"]["wood_contact"]
                        for point, force in zip(t["reference_points_mm"], t["point_forces_xyz_n"], strict=True):
                            actions.append(dict(source_id=shaft["axis_id"] + "/saved_wood_seat", role="common_seat_traction",
                                                point_mm=point, force_n=force, free_moment_nmm=[0., 0., 0.]))
            records.append({"basis": "reviewed104_common_spine_proposal_gravity", "body": body, "case_id": case, "actions": actions,
                            "source": key(path), "opening_record_pointer": f"/states/{index}",
                            "opening_demand_n": state["minimum_required_timber_tension_n"], "transverse_plane_v_mm": state["cut_local_v_mm"]})
        for body in PRIORITY[2:]:
            for case in CASES:
                records.append({"basis": "reviewed104_fresh_global_proposal_gravity", "body": body, "case_id": case,
                                "actions": actions_from_archive(arrays, body, case, members[body]),
                                "source": key(FRESH / "action-section-arrays.npz"), "opening_demand_n": None})
    for r in records:
        body = r["body"]
        datum = np.array(geometries[body]["start"])
        wrench = full_wrench(r["actions"], datum)
        r["body_wrench_xyz_n_nmm"] = wrench.tolist()
        require(max(abs(wrench[:3])) < 1e-5 and max(abs(wrench[3:])) < .002, "Prescribed body actions do not balance: " + str((r["basis"], body, r["case_id"], wrench)))
    output = new_output(output)
    with gzip.open(output / "actions.jsonl.gz", "wt") as stream:
        for r in records:
            stream.write(json.dumps(r, separators=(",", ":"), allow_nan=False) + "\n")
    write(output / "geometry.json", geometries)
    write(output / "plan.json", {"schema": "splitting_crack_compliance_plan/v1", "source_sha256": {key(p): h for p, h in pins.items()},
                                "sources": REFERENCES, "assumptions": ASSUMPTIONS, "duties": duties, "priority_bodies": PRIORITY,
                                "baseline_body_states": 264, "baseline_permanent_body_states": 88, "distinct_priority_body_states": 48,
                                "baseline_frame_axis_count": 104, "Hillman_axis_count": 66,
                                "native_CAD_or_frame_run": False, "splitting_qualification_complete": False,
                                "permanent_force_map_supplied": True})
    receipt(output, pins, started, ["actions.jsonl.gz", "geometry.json", "plan.json"])
    return {"prepared_states": len(records), "owned_output": key(output)}


def plane_properties(geometry, axis, station):
    """Exact plane moments for disjoint full circles and rectangular bore strips.

    This is a normal-traction component model, not a crack compliance or a
    stress-concentration factor. Refuse partial circles, oblique bores and
    overlapping voids rather than using the gross rectangle.
    """
    import numpy as np
    other = 3 - axis
    bounds3 = [[0., geometry["length_mm"]], [-geometry["width_mm"] / 2, geometry["width_mm"] / 2],
               [-geometry["depth_mm"] / 2, geometry["depth_mm"] / 2]]
    bounds = np.array([bounds3[0], bounds3[other]])
    require(bounds3[axis][0] + 1e-6 < station < bounds3[axis][1] - 1e-6, "Terminal transverse plane")
    require(geometry["finished_catalog_matches_current_STEP"] and geometry["recess_source"] is None,
            "Matching finished transverse-plane geometry is required")
    for p in geometry["planes"]:
        # Priority eight bodies are full rectangular stock; do not extend
        # this simple section implementation to clipped profiles silently.
        n = np.array(p["normal"])
        require(np.count_nonzero(abs(n) > 1e-7) == 1, "Clipped transverse profile requires its existing exact section recipe")
    def rect_integrals(box):
        center = box.mean(axis=1)
        lengths = box[:, 1] - box[:, 0]
        area = float(np.prod(lengths))
        return area, area * center, area * (np.outer(center, center) + np.diag(lengths ** 2 / 12))
    area, first, second = rect_integrals(bounds)
    voids = []
    for b in geometry.get("bores", []):
        direction = np.array(b["axis"])
        d = int(np.argmax(abs(direction)))
        require(abs(abs(direction[d]) - 1) < 1e-7 and np.max(abs(np.delete(direction, d))) < 1e-7,
                "Oblique cylinder-plane intersection requires its exact ellipse/trim integration")
        center = np.array(b["origin"])
        ends = sorted(center[d] + direction[d] * np.array(b["interval_mm"]))
        if d == axis:
            if not ends[0] - 1e-7 <= station <= ends[1] + 1e-7:
                continue
            c, r = center[[0, other]], b["radius_mm"]
            require(np.all(c - r > bounds[:, 0] + 1e-7) and np.all(c + r < bounds[:, 1] - 1e-7),
                    "Clipped circle requires exact disk/rectangle intersection")
            a = math.pi * r * r
            s = a * c
            ss = a * np.outer(c, c) + np.eye(2) * math.pi * r ** 4 / 4
            void = {"id": b["id"], "kind": "circle", "center": c.tolist(), "radius_mm": r,
                    "bounds": np.column_stack((c - r, c + r)).tolist(), "area_mm2": a}
        else:
            distance = abs(station - center[axis])
            if distance >= b["radius_mm"]:
                continue
            half = math.sqrt(b["radius_mm"] ** 2 - distance ** 2)
            c = 3 - axis - d
            box = bounds.copy()
            inplane_d = (0, other).index(d)
            inplane_c = (0, other).index(c)
            box[inplane_d] = [max(ends[0], bounds[inplane_d, 0]), min(ends[1], bounds[inplane_d, 1])]
            box[inplane_c] = [max(center[c] - half, bounds[inplane_c, 0]), min(center[c] + half, bounds[inplane_c, 1])]
            if np.any(box[:, 1] <= box[:, 0]):
                continue
            a, s, ss = rect_integrals(box)
            void = {"id": b["id"], "kind": "rectangle", "bounds": box.tolist(), "area_mm2": a}
        for earlier in voids:
            old = np.array(earlier["bounds"])
            new = np.array(void["bounds"])
            overlap = np.minimum(old[:, 1], new[:, 1]) - np.maximum(old[:, 0], new[:, 0])
            if np.all(overlap > 1e-7):
                if earlier["kind"] == void["kind"] == "circle":
                    require(np.linalg.norm(np.array(earlier["center"]) - void["center"]) >= earlier["radius_mm"] + void["radius_mm"] - 1e-7,
                            "Overlapping circular voids require union integration")
                else:
                    raise ValueError("Potential bore-void overlap requires exact union integration")
        voids.append(void)
        area, first, second = area - a, first - s, second - ss
    matrix = np.array([[area, *first], [first[0], *second[0]], [first[1], *second[1]]])
    require(area > 0 and np.linalg.det(matrix) > 0., "Singular retained transverse section")
    corners = np.array(list(product(*bounds)))
    for corner in corners:
        for v in voids:
            if v["kind"] == "circle":
                require(np.linalg.norm(corner - v["center"]) > v["radius_mm"] - 1e-7, "A nominal outer corner lies in a bore")
            else:
                box = np.array(v["bounds"])
                require(not np.all((corner >= box[:, 0] - 1e-7) & (corner <= box[:, 1] + 1e-7)), "A nominal outer corner lies in a bore strip")
    return {"bounds_g_other_mm": bounds.tolist(), "net_area_mm2": float(area), "net_raw_moment_matrix": matrix.tolist(),
            "voids": voids, "retained_outer_corners_g_other_mm": corners.tolist()}


def nominal(output, prepared):
    """Lightweight exact-section Ft90 components; never count them as fracture."""
    import numpy as np
    started = time.monotonic()
    prepared = Path(prepared).resolve()
    source = read(prepared / "receipt.json")
    pins = {prepared / name: digest for name, digest in source["output_sha256"].items()}
    pins[prepared / "receipt.json"] = sha(prepared / "receipt.json")
    authenticate(pins)
    geometries = read(prepared / "geometry.json")
    rows, limits = [], []
    for state in jsonl(prepared / "actions.jsonl.gz"):
        body, basis = state["body"], state["basis"]
        if body not in PRIORITY or basis == "reviewed104_baseline_gravity":
            continue
        g = geometries[body]
        frame, start = np.array(g["frame"]), np.array(g["start"])
        for axis in (1, 2):
            plane = state.get("transverse_plane_v_mm", 0.) if axis == 2 else 0.
            try:
                section = plane_properties(g, axis, plane)
            except ValueError as exc:
                limits.append({"body": body, "basis": basis, "case_id": state["case_id"], "axis": axis,
                               "exact_section_requirement": str(exc)})
                continue
            high = [a for a in state["actions"] if (frame @ (np.array(a["point_mm"]) - start))[axis] > plane + 1e-7]
            global_q = full_wrench(high, start + plane * frame[axis])
            q = np.r_[frame @ global_q[:3], frame @ global_q[3:]]
            target = [q[axis], q[5] if axis == 1 else -q[4], -q[3] if axis == 1 else q[3]]
            matrix = np.array(section["net_raw_moment_matrix"])
            coefficients = np.linalg.solve(matrix, target)
            stress = np.array([[1., *c] for c in section["retained_outer_corners_g_other_mm"]]) @ coefficients
            peak = max(float(max(stress)), 0.)
            index = peak / ASSUMPTIONS["Ft90_mpa"]
            scale = ASSUMPTIONS["Ft90_mpa"] / peak if peak > 1e-15 else None
            rows.append({"body": body, "basis": basis, "case_id": state["case_id"], "axis": axis, "plane_mm": plane,
                         "source_full_signed_wrench_g_u_v_n_nmm": q.tolist(), "section": section,
                         "linear_sigma90_coefficients_1_g_other": coefficients.tolist(),
                         "nominal_tension_peak_mpa": peak, "conditional_Ft90_mpa": ASSUMPTIONS["Ft90_mpa"],
                         "nominal_tension_reference_index": index, "same_pattern_normal_component_load_scale": scale,
                         "opening_demand_n": state["opening_demand_n"],
                         "same_pattern_opening_reference_n": state["opening_demand_n"] * scale if state["opening_demand_n"] is not None and scale is not None else None,
                         "normal_force_moment_recovery_residual": (matrix @ coefficients - target).tolist(),
                         "method": "Common linear normal traction on the actual retained transverse plane; complete N and both normal-force moments, with separate shear/torque retained in source wrench.",
                         "fracture_or_complete_joint_qualification": False})
    require(len(rows) + len(limits) == 96, "Priority state/orientation coverage differs")
    output = new_output(output)
    result = {"schema": "reviewed104_exact_transverse_Ft90_component/v1", "records": rows, "geometry_limits": limits,
              "normal_component_comparison_count": len(rows), "fracture_comparison_count": 0,
              "max_nominal_tension_reference_index": max(r["nominal_tension_reference_index"] for r in rows),
              "reference_exceedance_count": sum(r["nominal_tension_reference_index"] > 1. for r in rows),
              "complete_splitting_qualification": False,
              "applicability": "Exact net section integrals and nominal N/M traction under an explicit common plane hypothesis. No bore stress-concentration or crack resistance is inferred. The signed simultaneous V/V/T components remain separate obligations.",
              "source_law": "Elementary section equilibrium and the independently declared conditional Ft90; Jensen2016 section3.3 treats perpendicular tensile strength separately from fracture energy.",
              "duties": [{"joint_id": d["joint_id"], "supported_component_timbers": [b for b in d["timber_sides"] if any(r["body"] == b for r in rows)],
                          "complete_duty_splitting_qualification": False} for d in read(prepared / "plan.json")["duties"]]}
    write(output / "nominal.json", result)
    receipt(output, pins, started, ["nominal.json"])
    return {k: v for k, v in result.items() if k not in ("records", "duties")}


def grid(low, high, size, extra=()):
    import numpy as np
    points = list(np.linspace(low, high, max(1, math.ceil((high - low) / size)) + 1))
    points.extend(x for x in extra if low + 1e-7 < x < high - 1e-7)
    answer = []
    for p in sorted(points):
        if not answer or p - answer[-1] > 1e-6:
            answer.append(float(p))
    return np.array(answer)


def crack_paths(geometry, axes, center_v=0.):
    """Finite end paths and full-front bore-seeded intervals, without new holes."""
    L = geometry["length_mm"]
    paths = []
    for axis in axes:
        plane = center_v if axis == 2 else 0.
        for end in ("low", "high"):
            intervals = [[0., 5.], [0., 10.]] if end == "low" else [[L - 5., L], [L - 10., L]]
            paths.append(dict(id=f"end/{axis}/{end}", kind="grain_end", axis=axis, plane_mm=plane, tip=end,
                              initial_interval_mm=intervals[0], final_interval_mm=intervals[1]))
    for b in geometry.get("bores", []):
        shaft = max(range(3), key=lambda k: abs(b["axis"][k]))
        if shaft == 0 or abs(abs(b["axis"][shaft]) - 1.) > 1e-7:
            continue
        # The longitudinal split plane contains the bore shaft and grain.
        axis = 3 - shaft
        if axis not in axes:
            continue
        s, r = b["origin"][0], b["radius_mm"]
        initial = [max(0., s - r - 5.), min(L, s + r + 5.)]
        for tip in ("low", "high"):
            final = [max(0., s - r - 10.), initial[1]] if tip == "low" else [initial[0], min(L, s + r + 10.)]
            if final == initial:
                continue
            paths.append(dict(id=b["id"] + "/" + tip, kind="cross_grain_bore_seeded_full_front", axis=axis,
                              plane_mm=b["origin"][axis], tip=tip, bore_id=b["id"],
                              initial_interval_mm=initial, final_interval_mm=final))
    return paths


def mesh(geometry, size, axis, plane, crack_end=None, crack_length=0., coupon=False, crack_interval=None, grain_factor=4.):
    np, _, _, natural, *_ = libraries()
    require(geometry.get("finished_catalog_matches_current_STEP", True), geometry.get("catalog_limit", "Finished geometry is not bound"))
    L, w, h = [geometry[k] for k in ("length_mm", "width_mm", "depth_mm")]
    frozen_breaks = [x for p in crack_paths(geometry, (1, 2)) for k in ("initial_interval_mm", "final_interval_mm") for x in p[k]]
    frozen_breaks.extend(b["origin"][0] for b in geometry.get("bores", []))
    gs = grid(0., L, size if coupon else size * grain_factor, [100., 104.] if coupon else frozen_breaks)
    us = grid(-w / 2, w / 2, size, [plane] if axis == 1 else [])
    vs = grid(-h / 2, h / 2, size, [plane] if axis == 2 else [])
    planes = [(np.array(p["normal"]), p["offset"]) for p in geometry.get("planes", [])]
    bores = geometry.get("bores", [])
    recess = geometry.get("recess_source")
    if recess:
        # Reuse the existing validated source profile; keep its two X strips
        # and horizontal shoulder as a nonconvex retained-material predicate.
        from fea.floor_recess_mesh import profile
        _, normal, qs, tops, _, retained_x, shoulder = profile({"axis": geometry["frame"][0], "floor_recess_geometry": recess})
        start, frame = np.array(geometry["start"]), np.array(geometry["frame"])
    if crack_interval is None:
        crack_interval = [0., crack_length] if crack_end == "low" else [L - crack_length, L] if crack_end == "high" else None
    nodes, elements, node_map, volume, removed = [], [], {}, 0., 0.
    for i, j, k in product(range(len(gs) - 1), range(len(us) - 1), range(len(vs) - 1)):
        lo = np.array([gs[i], us[j], vs[k]])
        hi = np.array([gs[i + 1], us[j + 1], vs[k + 1]])
        center = (lo + hi) / 2
        dv = float(np.prod(hi - lo))
        if recess:
            global_center = start + frame.T @ center
            q = float(normal @ global_center)
            ztop = float(np.interp(q, qs, tops))
            retained = (qs[0] - 1e-7 <= q <= qs[-1] + 1e-7 and 0. <= global_center[2] <= ztop
                        and (global_center[2] >= shoulder or retained_x[0] <= global_center[0] <= retained_x[1]))
        else:
            retained = all(n @ center <= off + 1e-7 for n, off in planes)
        for b in bores:
            delta = center - b["origin"]
            a = np.array(b["axis"])
            t = float(delta @ a)
            if b["interval_mm"][0] - 1e-7 <= t <= b["interval_mm"][1] + 1e-7 and np.linalg.norm(delta - t * a) < b["radius_mm"]:
                retained = False
        if not retained:
            removed += dv
            continue
        indices = []
        for q in natural:
            p = center + q * (hi - lo) / 2
            side = 0
            inside_crack = crack_interval is not None and crack_interval[0] + 1e-7 < p[0] < crack_interval[1] - 1e-7
            if crack_interval is not None and crack_interval[0] == 0. and p[0] < crack_interval[1] - 1e-7:
                inside_crack = True
            if crack_interval is not None and crack_interval[1] == L and p[0] > crack_interval[0] + 1e-7:
                inside_crack = True
            if inside_crack and abs(p[axis] - plane) < 1e-7 and center[axis] > plane:
                side = 1
            identifier = (*np.round(p, 8), side)
            if identifier not in node_map:
                node_map[identifier] = len(nodes)
                nodes.append(p)
            indices.append(node_map[identifier])
        elements.append(indices)
        volume += dv
    require(elements, "Empty retained wood mesh")
    nodes, elements = np.array(nodes), np.array(elements, dtype=int)
    expected = geometry["actual_volume_mm3"]
    require(abs(volume / expected - 1) < .05, "Retained voxel volume differs from reviewed STEP by >=5%; refine or supply exact cut-cell geometry")
    # Count actual common retained faces in the added crack band; removed bore
    # cells cannot become fictitious fracture area.
    faces = {}
    area = 0.
    for e in elements:
        p = nodes[e[:8]]
        lo, hi = p.min(axis=0), p.max(axis=0)
        if abs(hi[axis] - plane) > 1e-7:
            continue
        other = 3 - axis
        signature = tuple(np.round([lo[0], hi[0], lo[other], hi[other]], 8))
        faces[signature] = (hi[0] - lo[0]) * (hi[other] - lo[other])
    for e in elements:
        p = nodes[e[:8]]
        lo, hi = p.min(axis=0), p.max(axis=0)
        if abs(lo[axis] - plane) > 1e-7:
            continue
        other = 3 - axis
        signature = tuple(np.round([lo[0], hi[0], lo[other], hi[other]], 8))
        if signature in faces:
            if crack_interval is not None:
                overlap = max(0., min(hi[0], crack_interval[1]) - max(lo[0], crack_interval[0]))
            else:
                overlap = 0.
            area += overlap * (hi[other] - lo[other])
    return nodes, elements, {"elements": len(elements), "nodes": len(nodes), "retained_volume_mm3": volume,
                             "relative_volume_error": volume / expected - 1, "crack_area_mm2": float(area), "mesh_size_mm": size,
                             "maximum_grain_pitch_mm": size if coupon else size * grain_factor}


def rigid_columns(nodes):
    import numpy as np
    center = nodes.mean(axis=0)
    R = np.zeros((3 * len(nodes), 6))
    for i, p in enumerate(nodes):
        R[3 * i:3 * i + 3, :3] = np.eye(3)
        for j, unit in enumerate(np.eye(3)):
            R[3 * i:3 * i + 3, j + 3] = np.cross(unit, p - center) / 100.
    Q, _ = np.linalg.qr(R, mode="reduced")
    return Q


def stiffness(nodes, elements, constants, swap):
    np, sparse, _, _, _, _, brick = libraries()
    axes = {"L": [1., 0., 0.], "R": [0., 0., 1.] if swap else [0., 1., 0.], "T": [0., -1., 0.] if swap else [0., 0., 1.]}
    # Reuse the existing C3D20/3x3x3 Gauss implementation and material validator.
    matrices = {}
    rows, cols, values = [], [], []
    for e in elements:
        p = nodes[e]
        positions = p - p.mean(axis=0)
        signature = tuple(np.round(positions.ravel(), 8))
        if signature not in matrices:
            matrices[signature] = brick.brick_stiffness(positions, constants, axes)[0]
        dofs = (3 * e[:, None] + np.arange(3)).ravel()
        rows.append(np.repeat(dofs, 60))
        cols.append(np.tile(dofs, 60))
        values.append(matrices[signature].ravel())
    K = sparse.coo_matrix((np.concatenate(values), (np.concatenate(rows), np.concatenate(cols))), shape=(3 * len(nodes),) * 2).tocsr()
    require(np.max(abs((K - K.T).data), initial=0.) < 1e-7, "Asymmetric wood stiffness")
    return K


def load_vector(nodes, geometry, records, axis, plane):
    np, _, _, _, distribute, *_ = libraries()
    frame, start = np.array(geometry["frame"]), np.array(geometry["start"])
    F = np.zeros((3 * len(nodes), len(records)))
    max_distance, residual = 0., np.zeros(6)
    for col, record in enumerate(records):
        for action in record["actions"]:
            force = frame @ action["force_n"]
            moment = frame @ action["free_moment_nmm"]
            if max(abs(force)) < 1e-14 and max(abs(moment)) < 1e-12:
                continue
            point = frame @ (np.array(action["point_mm"]) - start)
            distance = np.linalg.norm(nodes - point, axis=1)
            # Keep a point on its original side of the crack. A force cloud
            # cannot silently act as an artificial stitch across the split.
            # Exclude seam nodes in every crack configuration. Otherwise the
            # duplicated seam changes the prescribed force vector and an
            # energy difference would include a load-placement change.
            eligible = np.flatnonzero(nodes[:, axis] > plane + 1e-7 if point[axis] >= plane else nodes[:, axis] < plane - 1e-7)
            order = eligible[np.argsort(distance[eligible], kind="stable")]
            require(len(order) > 0, "No retained nodes on the source side of the crack")
            radius = 15.
            chosen = order[distance[order] < distance[order[0]] + radius]
            require(len(chosen) >= 4, "Insufficient retained load nodes")
            weights = (1 - (distance[chosen] - distance[order[0]]) / radius) ** 2
            values = distribute(nodes[chosen], force, moment, point, weights)
            F[(3 * chosen[:, None] + np.arange(3)).ravel(), col] += values.ravel()
            got = np.r_[values.sum(axis=0), np.cross(nodes[chosen] - point, values).sum(axis=0)]
            residual = np.maximum(residual, abs(got - np.r_[force, moment]))
            max_distance = max(max_distance, float(distance[chosen].max()))
    require(max(residual[:3]) < 1e-7 and max(residual[3:]) < 1e-5, "Nodal force/couple map does not recover source")
    return F, {"maximum_individual_wrench_residual_n_nmm": residual.tolist(), "maximum_patch_node_distance_from_source_mm": max_distance,
               "placement_scope": ASSUMPTIONS["boundary"]}


def elastic_response(K, nodes, F):
    np, sparse, splu, *_ = libraries()
    Q = rigid_columns(nodes)
    balance = Q.T @ F
    require(np.max(abs(balance)) < 2e-5, "Local body action wrench cannot be equilibrated without artificial support")
    system = sparse.bmat([[K, sparse.csr_matrix(Q)], [sparse.csr_matrix(Q.T), None]], format="csc")
    rhs = np.vstack((F, np.zeros((6, F.shape[1]))))
    solution = splu(system).solve(rhs)
    U = solution[:len(F)]
    delta = K @ U - F + Q @ solution[len(F):]
    require(np.max(abs(delta)) < 1e-5, "Elastic force residual exceeds tolerance")
    return U, {"maximum_equilibrium_residual_n": float(np.max(abs(delta))), "maximum_gauge_reaction_n": float(np.max(abs(solution[len(F):]))),
               "strain_energy_nmm": (.5 * np.sum(F * U, axis=0)).tolist(), "maximum_source_rigid_load_projection_n": float(np.max(abs(balance)))}


def transverse_stress(nodes, elements, U, constants, swap):
    np, _, _, _, _, _, brick = libraries()
    from fea.wood_joint_reduced_members import shape20_derivatives
    axes = {"L": [1., 0., 0.], "R": [0., 0., 1.] if swap else [0., 1., 0.], "T": [0., -1., 0.] if swap else [0., 0., 1.]}
    C = brick.engineering_stiffness(constants, axes)
    maximum = np.zeros(U.shape[1])
    witness = [None] * U.shape[1]
    gauss = np.polynomial.legendre.leggauss(3)[0]
    natural_points = list(product(gauss, repeat=3))
    operators = {}
    for ei, e in enumerate(elements):
        p = nodes[e]
        ue = U[(3 * e[:, None] + np.arange(3)).ravel()]
        signature = tuple(np.round((p - p.mean(axis=0)).ravel(), 8))
        if signature not in operators:
            matrices = []
            for natural in natural_points:
                dn = shape20_derivatives(natural)
                grad = dn @ np.linalg.inv(p.T @ dn)
                B = np.zeros((6, 60))
                for i in range(3):
                    B[i, i::3] = grad[:, i]
                for k, (i, j) in enumerate(brick.PAIR[3:], 3):
                    B[k, i::3], B[k, j::3] = grad[:, j], grad[:, i]
                matrices.append(C @ B)
            operators[signature] = np.array(matrices)
        stress = operators[signature] @ ue
        s90 = .5 * (stress[:, 1] + stress[:, 2]) + np.sqrt(.25 * (stress[:, 1] - stress[:, 2]) ** 2 + stress[:, 5] ** 2)
        peaks = s90.max(axis=0)
        for col in np.flatnonzero(peaks > maximum):
            gi = int(s90[:, col].argmax())
            maximum[col] = peaks[col]
            witness[col] = {"element": int(ei), "gauss_natural": list(natural_points[gi]), "stress_g_u_v_gu_gv_uv_mpa": stress[gi, :, col].tolist()}
    return maximum, witness


def contact_bound_oracle():
    """Exact two-arm fixture for both opening and closing unilateral states."""
    import numpy as np
    results = []
    ground = np.diag([2., 3.])
    mode = np.array([-1., 1.])
    for force in (np.array([-1., 1.]), np.array([1., -1.]), np.array([3., 1.])):
        intact_energy = .5 * float(force.sum() ** 2 / ground.diagonal().sum())
        free_energies, contact_energies = [], []
        for ligament in (4., 1.):
            u = np.linalg.solve(ground + ligament * np.outer(mode, mode), force)
            free = .5 * float(force @ u)
            contact = free if float(mode @ u) >= 0 else intact_energy
            free_energies.append(free)
            contact_energies.append(contact)
        upper = free_energies[1] - intact_energy
        actual = contact_energies[1] - contact_energies[0]
        require(-1e-14 <= actual <= upper + 1e-14, "Contact compliance bound failed exact two-arm oracle")
        results.append({"load": force.tolist(), "intact_energy": intact_energy, "initial_final_free_energies": free_energies,
                        "initial_final_unilateral_energies": contact_energies, "contact_increment": actual, "upper_increment": upper})
    return {"status": "SUPPORTED_EXACT_CONTACT_ENERGY_BOUND", "fixture": "Two grounded elastic arms, remaining ligament stiffness 4 then 1, no-penetration gap u2-u1 >= 0; exact active-set solution.",
            "states": results, "applicability": "Validates the energy ordering and bound algebra on opening/closing states. Project geometry/load placement and Gc hypotheses remain separate."}


def coupon(output, sizes=(8., 4.)):
    """Parent-run DCB validation, not a project strength result or software test."""
    np, sparse, splu, _, _, scenario, _ = libraries()
    started = time.monotonic()
    pins = {p: h for p, h in PINS.items() if p == BRICK or p.is_relative_to(ROOT / "fea")}
    authenticate(pins)
    output = new_output(output)
    constants = scenario()["calculix_engineering_constants"]
    E, Er, _, _, _, _, G, *_ = constants
    b, h, P, a, da = 20., 10., 100., 100., 4.
    geometry = {"length_mm": 240., "width_mm": b, "depth_mm": 2 * h, "actual_volume_mm3": 240 * b * 2 * h,
                "frame": np.eye(3).tolist(), "start": [0., 0., 0.], "recess_source": None}
    gamma = 1.18 * math.sqrt(E * Er) / G
    correction = h * math.sqrt(E / (11 * G) * (3 - 2 * (gamma / (1 + gamma)) ** 2))
    expected = 6 * P * P / (b * b * h) * (2 * (a + da / 2 + correction) ** 2 / (E * h * h) + 1 / (5 * G))
    results = []
    for size in sizes:
        energies = []
        for crack in (a, a + da):
            nodes, elements, census = mesh(geometry, size, 2, 0., "low", crack, coupon=True)
            K = stiffness(nodes, elements, constants, True)
            F = np.zeros(3 * len(nodes))
            for sign in (-1, 1):
                ids = np.flatnonzero((abs(nodes[:, 0]) < 1e-7) & (sign * nodes[:, 2] > 1e-7))
                F[3 * ids + 2] = sign * P / len(ids)
            fixed = (3 * np.flatnonzero(abs(nodes[:, 0] - 240.) < 1e-7)[:, None] + np.arange(3)).ravel()
            free = np.setdiff1d(np.arange(len(F)), fixed)
            displacement = np.zeros(len(F))
            displacement[free] = splu(K[free][:, free].tocsc()).solve(F[free])
            require(np.max(abs((K @ displacement - F)[free])) < 1e-6, "DCB numerical equilibrium failed")
            energies.append(float(.5 * F @ displacement))
        got = (energies[1] - energies[0]) / (b * da)
        results.append({"mesh_size_mm": size, "energies_nmm": energies, "G_n_per_mm": got,
                        "relative_difference_from_corrected_DCB": got / expected - 1, "final_mesh": census})
    require(len(results) >= 2, "At least two DCB mesh resolutions are required")
    convergence = abs(results[-1]["G_n_per_mm"] / results[-2]["G_n_per_mm"] - 1)
    supported = abs(results[-1]["relative_difference_from_corrected_DCB"]) < .15 and convergence < .15
    result = {"schema": "splitting_DCB_numerical_validation/v1", "status": "SUPPORTED_DCB_ENERGY_METHOD" if supported else "METHOD_NOT_VALIDATED",
              "known_answer_primary_equations": "Romanowicz2024 appendix equations 7,9,10",
              "expected_midpoint_G_n_per_mm": expected, "root_correction_mm": correction, "results": results,
              "relative_mesh_change": convergence, "maximum_allowed_relative_difference": .15,
              "contact_energy_upper_bound_oracle": contact_bound_oracle(),
              "applicability": "Validates 3D linear orthotropic brick energy differentiation on this DCB. It does not validate project mesh, local load maps, crack paths or material resistance.",
              "complete_joint_acceptance": False}
    write(output / "validation.json", result)
    receipt(output, pins, started, ["validation.json"])
    return result


def solve(output, prepared, validation, body, basis, sizes=(10., 5.), axes=(1, 2)):
    """Parent-owned sparse solid run for one body and one named load basis."""
    np, _, _, _, _, scenario, _ = libraries()
    started = time.monotonic()
    prepared, validation = Path(prepared).resolve(), Path(validation).resolve()
    pins = dict(PINS)
    for directory in (prepared, validation):
        record = read(directory / "receipt.json")
        for name, digest in record["output_sha256"].items():
            pins[directory / name] = digest
        pins[directory / "receipt.json"] = sha(directory / "receipt.json")
    authenticate(pins)
    require(read(validation / "validation.json")["status"] == "SUPPORTED_DCB_ENERGY_METHOD", "Known-answer energy method has not been validated")
    geometry = read(prepared / "geometry.json")[body]
    records = [r for r in jsonl(prepared / "actions.jsonl.gz") if r["body"] == body and r["basis"] == basis]
    require([r["case_id"] for r in records] == list(CASES), "Missing/duplicate simultaneous cases for requested basis")
    constants = scenario()["calculix_engineering_constants"]
    output = new_output(output)
    results, mesh_limits = [], []
    for axis in axes:
        plane = records[0].get("transverse_plane_v_mm", 0.) if axis == 2 else 0.
        for swap in (False, True):
            for size in sizes:
                nodes, elements, census = mesh(geometry, size, axis, plane)
                K = stiffness(nodes, elements, constants, swap)
                F, map_record = load_vector(nodes, geometry, records, axis, plane)
                U, intact = elastic_response(K, nodes, F)
                stress, stress_witness = transverse_stress(nodes, elements, U, constants, swap)
                for end in ("low", "high"):
                    energy, areas = [], []
                    for crack in (5., 10.):
                        n, e, details = mesh(geometry, size, axis, plane, end, crack)
                        f, mapped = load_vector(n, geometry, records, axis, plane)
                        k = stiffness(n, e, constants, swap)
                        _, response = elastic_response(k, n, f)
                        energy.append(np.array(response["strain_energy_nmm"]))
                        areas.append(details["crack_area_mm2"])
                    da = areas[1] - areas[0]
                    require(da > 0., "No sound crack area is released")
                    G = (energy[1] - energy[0]) / da
                    require(np.min(G) > -1e-8, "Crack release reduced compliance; inconsistent force/crack mapping")
                    for col, record in enumerate(records):
                        demand = max(float(G[col]), 0.)
                        scale = math.sqrt(ASSUMPTIONS["Gc_all_modes_n_per_mm"] / demand) if demand > 1e-15 else None
                        results.append({"body": body, "basis": basis, "case_id": record["case_id"], "axis": axis, "plane_mm": plane,
                                        "RT_binding": "R=v,T=-u" if swap else "R=u,T=v", "crack_end": end, "mesh_size_mm": size,
                                        "initial_extended_crack_areas_mm2": areas, "initial_extended_energies_nmm": [float(e[col]) for e in energy],
                                        "G_n_per_mm": demand, "Gc_n_per_mm": ASSUMPTIONS["Gc_all_modes_n_per_mm"],
                                        "fracture_index": demand / ASSUMPTIONS["Gc_all_modes_n_per_mm"],
                                        "intact_sampled_sigma90_mpa": float(stress[col]), "Ft90_mpa": ASSUMPTIONS["Ft90_mpa"],
                                        "initiation_index": float(stress[col]) / ASSUMPTIONS["Ft90_mpa"], "intact_stress_witness": stress_witness[col],
                                        "simultaneous_full_load_fracture_scale": scale,
                                        "opening_demand_n": record["opening_demand_n"],
                                        "same_pattern_opening_at_fracture_reference_n": record["opening_demand_n"] * scale if record["opening_demand_n"] is not None and scale is not None else None,
                                        "mesh": census, "intact_elastic_accounting": intact, "load_map": map_record,
                                        "qualification_scope": "Conditional finite-mesh numerical component comparison; complete joint acceptance remains separate"})
                print(body, basis, axis, swap, size, "completed", flush=True)
    # Mesh comparison is by exact state/path/RT identity; witnesses are never
    # swapped between cases. A small energy does not excuse unresolved stress.
    group = {}
    for r in results:
        identifier = tuple(r[k] for k in ("case_id", "axis", "plane_mm", "RT_binding", "crack_end"))
        group.setdefault(identifier, []).append(r)
    for identifier, rows in group.items():
        rows.sort(key=lambda r: -r["mesh_size_mm"])
        require(len(rows) >= 2, "Project comparison requires two mesh resolutions")
        coarse, fine = rows[-2:]
        for metric in ("G_n_per_mm", "intact_sampled_sigma90_mpa"):
            delta = abs(fine[metric] - coarse[metric]) / max(abs(fine[metric]), abs(coarse[metric]), 1e-8)
            fine[metric + "_relative_mesh_change"] = delta
            if delta > .20:
                mesh_limits.append({"path": list(identifier), "metric": metric, "relative_mesh_change": delta,
                                    "finite_next_action": "Repeat this same body/path at mesh_size_mm=2.5; keep load footprint fixed in physical millimetres before claiming convergence."})
    result = {"schema": "reviewed104_3D_splitting_comparison/v1", "body": body, "basis": basis,
              "status": "COMPARED_WITH_MESH_LIMITS" if mesh_limits else "CONDITIONAL_NUMERICAL_COMPARISONS_COMPLETE",
              "records": results, "mesh_limits": mesh_limits, "assumptions": ASSUMPTIONS, "source_references": REFERENCES,
              "numerical_scope": "Named 5-to-10 mm end cracks on u/v planes, both R/T bindings, sampled intact tensile initiation; no all-crack or washer-plug capacity claim.",
              "complete_joint_acceptance": False, "reviewed_geometry_changed": False, "existing_reference_exceedances_replaced": False}
    write(output / "result.json", result)
    receipt(output, pins, started, ["result.json"])
    return {k: v for k, v in result.items() if k != "records"}


def summarize(output, prepared, results):
    started = time.monotonic()
    prepared = Path(prepared).resolve()
    pins = {prepared / "plan.json": sha(prepared / "plan.json")}
    plan = read(prepared / "plan.json")
    available = {}
    summaries = []
    for directory in results:
        directory = Path(directory).resolve()
        r = read(directory / "receipt.json")
        for name, digest in r["output_sha256"].items():
            pins[directory / name] = digest
        pins[directory / "receipt.json"] = sha(directory / "receipt.json")
        result = read(directory / "result.json")
        identifier = (result["body"], result["basis"])
        require(identifier not in available, "Duplicate body/basis result")
        available[identifier] = {"source": key(directory / "result.json"), "sha256": pins[directory / "result.json"],
                                 "status": result["status"], "mesh_limit_count": len(result["mesh_limits"]),
                                 "max_fracture_index": max(x["fracture_index"] for x in result["records"]),
                                 "max_initiation_index": max(x["initiation_index"] for x in result["records"])}
        summaries.append(dict(body=identifier[0], basis=identifier[1], **available[identifier]))
    duties = []
    for duty in plan["duties"]:
        sides = []
        for body in duty["timber_sides"]:
            baseline = available.get((body, "reviewed104_baseline_gravity"))
            distinct = [v for (b, source), v in available.items() if b == body and source != "reviewed104_baseline_gravity"]
            sides.append({"body": body, "baseline": baseline, "distinct_proposal_gravity_comparisons": distinct,
                          "required_next_calculation": None if baseline else "Run the prepared reviewed104_baseline_gravity three-dimensional crack/strength comparison for this timber side. Curved/recess cells must satisfy the retained-volume and project-mesh guards."})
        duties.append({"joint_id": duty["joint_id"], "sides": sides, "full_splitting_qualification": False,
                       "remaining_scope": "Finite u/v planes and 5-to-10mm grain-end flaws do not cover bore-initiated internal cracks, radial washer-plug cracks, crack-face contact or permanent load states. Those resistances remain unassigned."})
    output = new_output(output)
    value = {"schema": "splitting_resistance_30_duty_map/v1", "duty_count": 30, "duties": duties, "results": summaries,
             "new_numerical_result_count": len(summaries), "required_splitting_qualification_complete": False,
             "exact_missing_inputs": ["Conditional Gc lower bound for every mode/mixture and Ft90 are supplied hypotheses, not measured grade-specific values.",
                                      "Internal bore-initiated crack extent/path and washer-anchorage crack geometry require separate release surfaces; no scalar capacity is assigned.",
                                      "A reviewed104 permanent signed body-action map is required; six-bore proposal permanent spine geometry cannot be substituted."],
             "finite_next_implementation": "Extend the existing duplicate-interface-node crack mesh to a bounded g interval starting at each reviewed cross-grain bore, preserve both crack tips, and evaluate the same energy difference/added sound area with the fixed source loads. Add radial washer release surfaces and crack-face contact where compression closes the slit. Reuse existing physical bore/seat fields; parent supplies and pins permanent reviewed104 body actions.",
             "no_new_limit_counted_as_qualification": True, "existing_eight_NDS_exceedances_unchanged": True}
    write(output / "coverage.json", value)
    receipt(output, pins, started, ["coverage.json"])
    return {"duty_count": 30, "new_numerical_result_count": len(summaries), "required_splitting_qualification_complete": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "nominal", "coupon", "solve", "summarize"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--validation", type=Path)
    parser.add_argument("--body")
    parser.add_argument("--basis", default="reviewed104_baseline_gravity")
    parser.add_argument("--mesh-sizes", nargs="+", type=float)
    parser.add_argument("--axes", nargs="+", type=int, choices=(1, 2), default=[1, 2])
    parser.add_argument("--results", nargs="*", type=Path, default=[])
    args = parser.parse_args()
    if args.stage == "prepare":
        result = prepare(args.output)
    elif args.stage == "nominal":
        require(args.prepared is not None, "nominal needs --prepared")
        result = nominal(args.output, args.prepared)
    elif args.stage == "coupon":
        result = coupon(args.output, tuple(args.mesh_sizes or (8., 4.)))
    elif args.stage == "solve":
        require(args.prepared is not None and args.validation is not None and args.body is not None, "solve needs --prepared, --validation and --body")
        result = solve(args.output, args.prepared, args.validation, args.body, args.basis, tuple(args.mesh_sizes or (10., 5.)), tuple(args.axes))
    else:
        require(args.prepared is not None, "summarize needs --prepared")
        result = summarize(args.output, args.prepared, args.results)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
