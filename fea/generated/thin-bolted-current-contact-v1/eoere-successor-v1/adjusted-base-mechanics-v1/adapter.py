"""Source-only adjusted-base descriptor preflight. No CAD, K, q or solve route.

A parent-approved exact manifest is required for production intake. The output
is deliberately not the factory input schema: missing own geometry measures,
panel refresh and independent admission cannot be bypassed with this receipt.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
BASE = OWN.parent.parent.relative_to(ROOT).as_posix()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
OLD_INPUT = BASE + "/raised-rail-mechanics-v1/inputs.json"
OLD_INPUT_SHA = "81e9ad126f806a412a8bcb73ae3d0057ef3568ed0fa45986503f97fb5fb62d9f"
EXTRACT = BASE + "/mechanics-inputs-v1/extract.py"
EXTRACT_SHA = "b02cb1318518dda0949ac6175b72a130d5379a8ca45d4776ee22e540bd6769a4"
RAISED_PLAN = BASE + "/raised-rail-mechanics-v1/plan.json"
RAISED_PLAN_SHA = "a1f50ac69fe91f5234d86590cab09e8f1b1a8b49d74c1b7b2d878ed355948470"
INTERVAL_METHOD = "scripts/eoere_bolted_model.py"
INTERVAL_METHOD_SHA = "9bbdaae74981710891fbd1a01a97088e29cd99fda47bff854e51473f66e1adaa"
SHIFT = [-39.2, 0., 0.]
MOVED_RAW = {"base_principal_center_right", "base_post_center_right"}
EXTENDED = {"base_rail_bottom_right", "base_rail_service_lower_right", "base_rail_service_upper_right"}
DUTIES = {"clip_horizontal_bottom_right_1", "clip_horizontal_lower_right_1",
          "clip_horizontal_upper_right_1", "clip_split_base_center_right",
          "clip_split_top_center_right", "clip_split_header_center_right"}
EXPECTED_PANELS = {"main_lower_right", "main_upper_right", "kicker_right"}
RESTRAINED = ["lumber_leg_left", "lumber_leg_right"]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def join(pins, additions):
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, "contradictory source pin: " + path)
        pins[path] = digest


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "source bytes changed: " + path)


def read_ref(ref, pins):
    require(set(ref) == {"path", "sha256"}, "exact source path/hash reference required")
    join(pins, {ref["path"]: ref["sha256"]})
    verify({ref["path"]: ref["sha256"]})
    return json.loads((ROOT / ref["path"]).read_bytes())


def generic():
    verify({EXTRACT: EXTRACT_SHA})
    spec = importlib.util.spec_from_file_location("adjusted_base_unchanged_generic_metadata", ROOT / EXTRACT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, module.pure_methods()


def indexed(rows, key):
    result = {r[key]: r for r in rows}
    require(len(rows) == len(result), "duplicate source identity: " + key)
    return result


def close_ports(old, current):
    """Every shared physical shaft attachment must agree with one rigid pose."""
    verify({INTERVAL_METHOD: INTERVAL_METHOD_SHA})
    before = indexed([s["source_axis"] for s in old["shafts"]], "id")
    after = indexed(current["axes"], "id")
    require(len(before) == len(after) == 100 and before.keys() == after.keys(), "exact100 shaft identity required")
    deltas, moves, bindings, interval_errors = {}, [], [], []
    for identity, axis in after.items():
        prior = before[identity]
        delta = [b-a for a, b in zip(prior["point_xyz_mm"], axis["point_xyz_mm"], strict=True)]
        require(math.dist(delta, SHIFT) < 1e-6 or math.dist(delta, [0., 0., 0.]) < 1e-6,
                "only reviewed uniform shaft translation supported: " + identity)
        changed = math.dist(delta, [0., 0., 0.]) > 1e-6
        if changed:
            moves.append(identity)
        require({k: v for k, v in prior.items() if k not in {"point_xyz_mm", "attachments"}}
                == {k: v for k, v in axis.items() if k not in {"point_xyz_mm", "attachments"}},
                "shaft recipe/receiver changed: " + identity)
        key = lambda a: (a["angle_id"], a["flange"], a["transverse"])
        arows, brows = {key(a): a for a in prior["attachments"]}, {key(a): a for a in axis["attachments"]}
        require(len(arows) == len(prior["attachments"]) and len(brows) == len(axis["attachments"])
                and arows.keys() == brows.keys(), "shared shaft attachments missing: " + identity)
        for port, row in brows.items():
            a = arows[port]
            require({k: v for k, v in a.items() if k not in {"point", "interval_mm"}}
                    == {k: v for k, v in row.items() if k not in {"point", "interval_mm"}},
                    "attachment recipe changed: " + identity)
            pd = [b-a for a, b in zip(a["point"], row["point"], strict=True)]
            require(math.dist(pd, delta) < 1e-6, "attachment is off its own moved shaft: " + identity)
            # eoere_bolted_model.py97-104 stores absolute endpoints on the
            # normalized line with its first nonzero component positive.
            norm = math.sqrt(sum(x*x for x in row["direction"]))
            require(math.isfinite(norm) and norm > 1e-12, "finite attachment direction required")
            require(len(row["interval_mm"]) == 2 and all(math.isfinite(x) for x in row["interval_mm"])
                    and row["interval_mm"][1] > row["interval_mm"][0], "finite ordered attachment interval required")
            line = [x/norm for x in row["direction"]]
            if next(x for x in line if abs(x) > 1e-8) < 0:
                line = [-x for x in line]
            along = sum(x*y for x, y in zip(delta, line, strict=True))
            if math.dist(row["interval_mm"], [v+along for v in a["interval_mm"]]) >= 1e-6:
                interval_errors.append(identity+"/"+row["angle_id"]+"/"+row["flange"]+"/"+str(row["transverse"]))
            deltas.setdefault(row["angle_id"], []).append(pd)
            bindings.append({**row, "physical_axis_id": identity})
    poses = []
    for pose in old["fitting_poses"]:
        rows = deltas.get(pose["id"], [])
        require(len(rows) == 4, "four actual ports required: " + pose["id"])
        require(all(math.dist(rows[0], r) < 1e-6 for r in rows),
                "incoherent shared-axis attachment pose: " + pose["id"])
        p = copy.deepcopy(pose)
        p["origin_xyz_mm"] = [a+b for a, b in zip(p["origin_xyz_mm"], rows[0], strict=True)]
        p["source_translation_xyz_mm"] = rows[0]
        poses.append(p)
    require(not interval_errors, "attachment canonical-positive interval differs: " + ", ".join(interval_errors))
    moved_duties = {p["duty_id"] for p in poses if math.dist(p["source_translation_xyz_mm"], [0., 0., 0.]) > 1e-6}
    require(moved_duties == DUTIES == set(current["affected_duties"]), "corrected six-duty closure required")
    require(len(moves) == 22 and set(moves) == set(current["moved_bolt_axes"]), "corrected22 moved shafts required")
    require(len(bindings) == 88, "all88 fitted ports required")
    return poses, bindings, sorted(moves)


def screw_delta(old, current):
    before = indexed([r["source_screw_descriptor"] for r in old["hillman_rows"]], "axis_id")
    after = indexed(current["screw_axes"], "axis_id")
    require(len(before) == len(after) == 66 and before.keys() == after.keys(), "exact66 Hillman identities required")
    moved = []
    for identity, b in after.items():
        a = before[identity]
        require(all(a[k] == b[k] for k in ("panel", "receiver", "direction_xyz")), "screw owner/direction changed")
        delta = [y-x for x, y in zip(a["origin_xyz_mm"], b["origin_xyz_mm"], strict=True)]
        if math.dist(delta, [0., 0., 0.]) > 1e-6:
            require(b["receiver"] in MOVED_RAW and math.dist(delta, SHIFT) < 1e-6, "unsupported screw move")
            moved.append(identity)
    require(len(moved) == 10 and set(moved) == set(current["moved_panel_screw_axes"])
            and {after[n]["panel"] for n in moved} == EXPECTED_PANELS, "corrected ten screws/three panels required")
    return after, sorted(moved)


def compose_sources(current, old, pins):
    """Follow frozen geometry ancestry; carry source rows, never old measures."""
    sources = {r["id"]: copy.deepcopy(r["source"]) for r in old["finished_body_observations"]}
    chain, record, seen = [], current, set()
    while "parent_geometry" in record:
        ref = record["parent_geometry"]
        require(ref["path"] not in seen, "cyclic geometry ancestry")
        seen.add(ref["path"])
        parent = read_ref(ref, pins)
        chain.append(parent)
        record = parent
    for record in [*reversed(chain), current]:
        join(pins, record.get("source_sha256", {}))
        for group in ("finished_solids", "finished_panel_solids", "changed_finished_solids"):
            for row in record.get(group, []):
                if row["id"] in sources:
                    sources[row["id"]] = copy.deepcopy(row)
        for row in record.get("unchanged_finished_solids", []):
            if row["id"] in sources:
                require(row["sha256"] == sources[row["id"]]["sha256"], "ancestor unchanged-source contradiction")
    for row in [*sources.values(), *current["changed_finished_solids"]]:
        join(pins, {row["path"]: row["sha256"]})
    return sources


def auxiliary_gravity(ex, screws, moved_screws):
    """Nominal source metal shares, never inferred from old field/load forces."""
    access_path, access_sha = ex.DATA["access"]
    verify({access_path: access_sha, RAISED_PLAN: RAISED_PLAN_SHA})
    access = json.loads((ROOT / access_path).read_bytes())
    plan = json.loads((ROOT / RAISED_PLAN).read_bytes())
    raised = {(r["id"], r["owner"]): r for r in plan["changed_data"]["moved_screw_gravity_shares"]}
    rows, moved = [], []
    for source in access["takeoff"]["conditional_metal_gravity_rows"]:
        if source["role"] not in {"screw", "tnut"}:
            continue
        prior = raised.get((source["id"], source["owner"]))
        center = prior["current_center_xyz_mm"] if prior else source["centroid_xyz_mm"]
        if prior:
            require(source["mass_kg"] == prior["mass_kg"], "raised source-share mass differs")
        identity = source["id"].removeprefix("fastener_")
        if source["role"] == "screw" and identity in moved_screws:
            require(source["owner"] in {screws[identity]["panel"], screws[identity]["receiver"]}, "moved source-share owner differs")
            center = [x+y for x, y in zip(center, SHIFT, strict=True)]
            moved.append(identity)
        rows.append({"id": source["id"]+f"/source-metal-share-{len(rows)}", "owner": source["owner"],
                     "mass_kg": source["mass_kg"], "center_xyz_mm": center,
                     "basis": "source nominal raw-envelope share; baseline rail correction retained; moved screw share translated with unchanged local overlap"})
    require(len(rows) == 274 and len(moved) == 20 and all(moved.count(n) == 2 for n in moved_screws), "274 source metal shares/20 moved shares required")
    return rows


def descriptors(old, current, sources):
    ex, m = generic()
    poses, bindings, moved_shafts = close_ports(old, current)
    screws, moved_screws = screw_delta(old, current)
    require(set(current["extended_rails"]) == EXTENDED and current["principal_shift_xyz_mm"] == SHIFT,
            "reviewed raw-stock transformation differs")
    changed_parts = current["changed_finished_solids"]
    require(len(changed_parts) == len(indexed(changed_parts, "id")) == 136
            and {kind: sum(r["kind"] == kind for r in changed_parts)
                 for kind in ("timber", "panel", "bracket", "bolt", "screw")}
            == {"timber": 7, "panel": 3, "bracket": 6, "bolt": 110, "screw": 10},
            "corrected136 changed physical parts required")
    require({r["id"] for r in changed_parts if r["kind"] == "timber"}
            == MOVED_RAW | EXTENDED | {"base_header", "base_rail_top"}
            and {r["id"] for r in changed_parts if r["kind"] == "panel"} == EXPECTED_PANELS
            and {r["id"] for r in changed_parts if r["kind"] == "bracket"} == {"eoere_"+d for d in DUTIES},
            "changed physical source identities differ")
    gross = []
    for prior in old["timber_rows"]:
        p = copy.deepcopy(prior["raw_profile_source"])
        name = p["member"]
        if name in MOVED_RAW:
            p["datum_xyz_mm"] = m.add(p["datum_xyz_mm"], SHIFT)
        elif name in EXTENDED:
            require(math.dist(prior["axis"], [1., 0., 0.]) < 1e-8, "rail union requires unchanged +X grain")
            vertices = p["raw_profile_vertices_luv_mm"]
            lo, hi = min(v[0] for v in vertices), max(v[0] for v in vertices)
            require(all(abs(v[0]-lo) < 1e-6 or abs(v[0]-hi) < 1e-6 for v in vertices), "only prismatic rail extension supported")
            for v in vertices:
                if abs(v[0]-lo) < 1e-6:
                    v[0] += SHIFT[0]
        p["current_analysis_transform"] = "translate -39.2mm X" if name in MOVED_RAW else "union with -39.2mm X translation" if name in EXTENDED else "unchanged gross raw profile"
        gross.append(ex.gross_row(p, m))
    changed = {n for n, s in sources.items() if s["sha256"] != next(r["source"]["sha256"] for r in old["finished_body_observations"] if r["id"] == n)}
    owners = []
    prior_owners = indexed(old["physical_owner_gravity_rows"], "id")
    for name, source in sources.items():
        prior = prior_owners[name]
        require(math.isfinite(source["volume_mm3"]) and source["volume_mm3"] > 0., "positive current source volume required")
        center = source.get("center_of_mass_xyz_mm")
        if name not in changed:
            center = prior["center_xyz_mm"]
        require(center is None or len(center) == 3 and all(math.isfinite(x) for x in center), "finite own source COM required")
        owners.append({"id": name, "kind": prior["kind"], "source": source,
                       "mass_kg": source["volume_mm3"] * old["parameters"]["wood_density_kg_m3"] * 1e-9,
                       "center_xyz_mm": center, "own_COM_query_required": center is None})
    for pose in poses:
        prior = prior_owners[pose["id"]]
        owners.append({"id": pose["id"], "kind": "fitting", "mass_kg": prior["mass_kg"],
                       "center_xyz_mm": m.add(prior["center_xyz_mm"], pose["source_translation_xyz_mm"]),
                       "basis": "unchanged nominal angle mass/centroid; verified uniform four-port translation"})
    shafts, pending_walls = [], []
    for axis in current["axes"]:
        prior = next(r for r in old["shafts"] if r["axis_id"] == axis["id"])
        roles = ex.role_rows(axis, m, {r["kind"]: r["volume_mm3"] for r in prior["metal_roles"]})
        mass = sum(r["mass_kg"] for r in roles)
        center = [sum(r["mass_kg"]*r["center_of_mass_xyz_mm"][j] for r in roles)/mass for j in range(3)]
        owners.append({"id": prior["body"], "kind": "shaft", "mass_kg": mass, "center_xyz_mm": center,
                       "gravity_route": "five own role loads required; no duplicate selfweight"})
        walls = []
        for receiver in axis["receivers"]:
            query = receiver in changed or axis["id"] in moved_shafts
            pending_walls += [{"axis_id": axis["id"], "receiver": receiver}] if query else []
            walls.append({"receiver": receiver, "current_full_wall_query_required": query,
                          "intervals_mm": None if query else [s["interval_mm"] for s in prior["surfaces"] if s["kind"] == "wood" and s["host"] == receiver]})
        shafts.append({"axis_id": axis["id"], "source_axis": axis, "metal_roles": roles,
                       "wood_walls": walls, "current_external_seat_join_required": any(r["current_full_wall_query_required"] for r in walls)})
    require(len(owners) == len(indexed(owners, "id")) == 150 and len(gross) == 22, "all150 owners/all22 raw spans required")
    ports = [{"angle_id": r["angle_id"], "axis_id": r["physical_axis_id"], "entry_xyz_mm": r["point"],
              "model_port_id": ex.port_id(r["flange"], r["transverse"])} for r in bindings]
    holes = copy.deepcopy(old["all_factory_holes"])
    pose_map = indexed(poses, "id")
    for fitting in holes:
        for hole in fitting["holes"]:
            hole["point_xyz_mm"] = m.add(hole["point_xyz_mm"], pose_map[fitting["angle_id"]]["source_translation_xyz_mm"])
    hillman = []
    for row in old["hillman_rows"]:
        s = screws[row["id"]]
        h = {**copy.deepcopy(row), "source_screw_descriptor": copy.deepcopy(s),
             "point_xyz_mm": m.add(s["origin_xyz_mm"], m.scale(m.unit(s["direction_xyz"]), 18.25625/2))}
        hillman.append(h)
    baseline_ref = old["geometry"]["report"]
    verify({baseline_ref["path"]: baseline_ref["sha256"]})
    machining = copy.deepcopy(json.loads((ROOT / baseline_ref["path"]).read_bytes())["panel_machining"])
    features = indexed(machining["features"], "identity")
    for identity in moved_screws:
        feature = features[identity]
        require(feature["kind"] == "conditional_screw_clearance" and feature["diameter_mm"] == 5.
                and feature["panel"] == screws[identity]["panel"], "own preserved screw aperture descriptor required")
        feature["start_xyz_mm"] = copy.deepcopy(screws[identity]["origin_xyz_mm"])
    floors = []
    for host, points in old["floor_footprints"].items():
        delta = SHIFT if host == "base_post_center_right" else [0., 0., 0.]
        require(host not in changed or host == "base_post_center_right", "unexpected changed floor host")
        floors.append({"host": host, "normal_reference_points_xyz_mm": [m.add(p, delta) for p in points],
                       "own_floor_face_confirmation_required": host in changed,
                       "centroid_XY_enabled": host in RESTRAINED})
    require(len(floors) == 8 and sum(len(r["normal_reference_points_xyz_mm"]) for r in floors) == 32, "eight feet/32 normals required")
    return {"gross_raw_timber_rows": gross, "fitting_poses": poses, "fitting_ports": ports,
            "all_factory_holes": holes,
            "shaft_descriptors": shafts, "hillman_rows": hillman, "physical_owner_gravity_descriptors": owners,
            "auxiliary_metal_gravity_descriptors": auxiliary_gravity(ex, screws, moved_screws),
            "current_panel_machining_descriptors": machining,
            "floor_descriptors": floors, "changed_finished_owner_ids": sorted(changed),
            "moved_shaft_ids": moved_shafts, "moved_screw_ids": moved_screws,
            "required_own_wall_queries": pending_walls,
            "pending_COM_owner_ids": sorted(r["id"] for r in owners if r.get("own_COM_query_required")),
            "panel_refresh": {"fresh_aperture_K_mass_and_screw_port_panels": sorted(EXPECTED_PANELS),
                              "unchanged_panel_K_candidates": sorted(set(old["panel_ids"])-EXPECTED_PANELS),
                              "fresh_geometry_source_contract_required": True,
                              "reuse_functions": ["aperture_delta", "refresh_screw_ports", "direct_reference_matrix"],
                              "affected_old_coefficient_blocks_reusable_as_unchanged": False,
                              "all_panel_contact_domains_require_current_own_sources": True}}


def preflight(manifest_path, expected_sha):
    pins = {EXTRACT: EXTRACT_SHA, OLD_INPUT: OLD_INPUT_SHA,
            RAISED_PLAN: RAISED_PLAN_SHA, INTERVAL_METHOD: INTERVAL_METHOD_SHA,
            str(OWN.relative_to(ROOT)): LOADED_SHA}
    manifest_path = Path(manifest_path).resolve()
    require(sha(manifest_path) == expected_sha, "frozen parent manifest raw SHA differs")
    manifest = json.loads(manifest_path.read_bytes())
    require(manifest.get("schema") == "eoere_adjusted_base_mechanics_frozen_sources/v1"
            and manifest.get("parent_model_review_approved") is True
            and manifest.get("optional_2026_extra") is False, "approved frozen adjusted base with optional extra OFF required")
    join(pins, {str(manifest_path.relative_to(ROOT)): expected_sha})
    current = read_ref(manifest["geometry"], pins)
    require(current.get("schema") == "eoere_adjusted_base_geometry/v1"
            and current.get("unofficial_2026_grid_included") is False
            and current.get("revision") == manifest["revision"]
            and current.get("candidate") == "compact-floor-flush-eoere-bolted-development"
            and not any(current["release"].values()), "current adjusted-base identity/release differs")
    require(all(not v for v in current["collisions"].values()), "current geometric collision blocker")
    old = read_ref({"path": OLD_INPUT, "sha256": OLD_INPUT_SHA}, pins)
    join(pins, old["source_sha256"])
    close_ports(old, current)  # Reject incoherent geometry before ancestry/adapters.
    sources = compose_sources(current, old, pins)
    verify(pins)
    result = descriptors(old, current, sources)
    verify(pins)
    return {"schema": "eoere_adjusted_base_mechanics_source_preflight/v1",
            "status": "SOURCE_DESCRIPTORS_PREPARED_CURRENT_MEASURES_AND_PARENT_ADMISSION_REQUIRED",
            "source_sha256": pins, "source_pins_before_after_unchanged": True,
            "geometry": manifest["geometry"], "optional_2026_extra": False, **result,
            "material_scenario": copy.deepcopy(old["scenario"]), "parameters": copy.deepcopy(old["parameters"]),
            "support": {"method": "fixed-rear-leg-centroid-XY-all-feet-compression-only",
                        "enabled_centroid_xy_hosts": RESTRAINED, "normal_count": 32,
                        "normal_and_joint_laws_changed": False, "no_slip_assumed_not_verified": True},
            "case_provider": {"path": BASE+"/raised-rail-cases-v1/cases.py", "API": "derive_fresh_cases(evidence,geometry,expected_owner_ids,source_sha256)",
                              "required_current_inputs": "current original hold features; all50 base masses/COM; own500 shaft role loads; current screw/Tnut ownership shares; exact150 IDs",
                              "climber_lb": 250, "dynamic_multiplier": 2, "horizontal_n": 300, "arm_mm": 100,
                              "accessory_kg": 25, "fresh_cases_ready": False},
            "unresolved": ["Changed body COM/bounds/topology and source-bound bore walls/external seats",
                           "Current complete opposed-face contact inventory, including newly possible/removed pairs and all88 flange domains",
                           "Moved center-post own floor-face confirmation; seven unchanged hosts source identity",
                           "Current three-panel aperture K/mass/screw ports and all66 metal ownership shares, without old q",
                           "Parent-owned factory input schema, method-input/readiness bridge and new raw-field independent admission"],
            "candidate_CAD_K_factorization_q_force_or_native_run_performed": False,
            "historical_q_forces_or_passes_transferred": False,
            "release": copy.deepcopy(old["release"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = preflight(args.manifest, args.manifest_sha256)
    result["command"] = list(sys.orig_argv)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.out), "owners": len(result["physical_owner_gravity_descriptors"]),
                      "pending_COM": len(result["pending_COM_owner_ids"]), "pending_walls": len(result["required_own_wall_queries"])}))


if __name__ == "__main__":
    main()
