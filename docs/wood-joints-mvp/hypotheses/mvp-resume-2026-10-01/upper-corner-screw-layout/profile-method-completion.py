"""Parent-run N07/N19 profile arithmetic on the unadopted 108-axis proposal.

Import is inert. prepare(output) only authenticates and joins saved identities
using the standard library. build(output) reuses existing signed-cut and
rectangle resistance functions; it launches no solve, CAD, coupon or test.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import math
import platform
import sys
from collections import Counter
from functools import cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/profile-method-completion"
ACCEL = BASE.parent / "mvp-acceleration-2026-09-28"
ADAPTER = ACCEL / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
NATIVE = ACCEL / "current-frame-pure-solid-matrix-export-native-attempt01/model.json"
PROJECTION_CONTRACT = ACCEL / "current-frame-physical-connector-projection-contract-attempt01/projection-contract.json"
PROJECTION_INPUTS = ACCEL / "current-frame-connector-compliance-attempt04/inputs.json"
PACKAGE = HERE / "rawlocal/knee-bridge-working-package/attempt02/manifest.json"
BRIDGE = HERE / "rawlocal/knee-bridge-geometry/attempt01/manifest.json"
CORRECTION = BASE / "top-corner-correction/proposal.json"
SURFACES = BASE.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
PIN_HELPER = HERE / "knee-bridge-members.py"
LEGS = ("lumber_leg_left", "lumber_leg_right")
DURATIONS = {"original_CD1": 1.0, "conditional_peak_CD1_25": 1.25}
TOL = 1e-5
METRICS = ("normal_reference_sum", "compatible_face_peak_over_Fv",
           "scalar_shear_bound_over_Fv", "sufficient_rectangle_bound_over_Fv")
PINS = {
    PIN_HELPER: "bc0704d2c4f7cb6dc472a139b382e514ab69f0a8de02f05a19a3266de6addb0b",
    PACKAGE: "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0",
    PACKAGE.with_name("receipt.json"): "5fa8cc849e4a2fa042a1cffa6d2957d4163597c7999dbcef1f57563dfdd83e7b",
    BRIDGE: "254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147",
    BRIDGE.with_name("receipt.json"): "92ccabb307b6d9cbcd8f768b8275a7ecf4ef6ae6a55a7be2cd83742d76be9973",
    CORRECTION: "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
    ADAPTER: "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    NATIVE: "89354d05f089c6eb8de3b90891ccadd547d18c89ba4faaa30b86c7366af217dc",
    NATIVE.with_name("freeze.json"): "614c9b466fd05c0b5ee6917aa26e108fd8151b36459b8b84999cd474f13d9ed3",
    PROJECTION_CONTRACT: "4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3",
    PROJECTION_INPUTS: "3d17f953df265035e95fdb3543e19eb0f7505d81778067f28783e4bb9b0b3208",
    HERE / "knee-bridge-remaining-sections.py": "e2a08ca075fdb397696889d22d8cbbfb30d83a3d4bb5e3af1726574c38ca2e15",
    HERE / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    HERE / "header-net-section.py": "d413a2ae912df6bf56086ad6ddda59526db32cc6325f1b4bf2b71f984d86a328",
    HERE / "top-host-net-sections.py": "bfa6a1716908efdb83b3ebf07b0def1bd9114d448dbdf294057b832749d8b3e8",
    HERE / "knee-bridge-top-rail.py": "d8f4a84ab8c6fefcdce4ba65a6812de6a7e6199ea69f67c3fb4fde1252681fec",
    ROOT / "mini_moonboard/base_frame.py": "e6f988738e172a7403a8b1a9e86d3d9fe6cfbb239fb29a16058acb0778957f16",
    ROOT / "mini_moonboard/compact_thick_frame.py": "2cc0693053645a2d6c3bccab7c69a66f06a8347ba0440c6b95dc04866d4bb362",
    ROOT / "mini_moonboard/compact_floor_taper_frame.py": "07ed7ffa094a62855880cfea2af63cae8193bda4a35402dbe90fa3417d82cfb1",
    ROOT / "mini_moonboard/compact_floor_flush_frame.py": "8764bec57564efa79f2636e589aa0e35b229c48975c791eec5c47b20183bf17a",
    ROOT / "mini_moonboard/compact_floor_recess_frame.py": "1c01f3a200bd824e18af172e7320820351caa6818b4ad3d4f35fb46835ccead0",
    ROOT / "scripts/compact_thick_results.py": "3f4f0ec5bfd1535c602c0c00c8017665fd336ca32f9cd6b38ccf9d5813853c1a",
    RAW / "sources/nds2024-chapter3.pdf": "205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644",
    RAW / "sources/nds2024-chapter4.pdf": "52feedd07d3b672f0dd2666903cf8b481687d3da975cd3fccac545f66dfeb9ec",
}
SOURCES = {
    "NDS2024_chapter3": "https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf",
    "NDS2024_chapter4": "https://web-media.awc.org/wp-content/uploads/2021/12/17210008/AWC_NDS2024_20241011_AWCWebsite_Chapter4.pdf",
}
LIMITS = [
    "Only finite bore-free rear-recess rectangles receive nominal stress arithmetic. Opening stations belong to member-opening-remainder; no opening resistance is duplicated here.",
    "A common longitudinal strain plane, isotropic rectangular torsion and signed face comparisons are existing nominal hypotheses, not notch concentration or fracture resistance.",
    "NDS 2024 3.4.3.1 equations require permitted end cuts. The deep side recess exceeds 4.4.3.1 d/4 when mapped to weak-plane depth and the oblique floor end is not the Figure 3D bearing geometry.",
    "Terminal point actions do not define a distributed traction field through clipped sections tending to zero area. The exact named terminal exclusions remain method-inapplicable.",
    "Saved native outer-profile and filled-bore volume agreement does not establish exact drilled STEP geometry or exact finished-hole compliance H. Six effective body bindings differ from inherited native descriptors.",
    "Native mesh node/plane comparisons are finite observations at the existing 1e-5 mm geometry tolerance, not continuous surface or stiffness qualification.",
    "No full member stability, all-joint splitting/anchorage, hardware qualification, physical observation, criterion adoption or release is supplied.",
]
FLAGS = {"proposal_adopted": False, "reviewed_104_source_pass_transferred": False,
         "geometry_hardware_material_or_loads_changed": False, "native_or_frame_or_CAD_run": False,
         "coupon_or_test_or_review_run": False, "exact_finished_H_claimed": False,
         "opening_strength_comparisons_duplicated": False, "splitting_or_anchorage_assessed": False,
         "complete_joint_acceptance": False, "formal_criterion_acceptance": False,
         "physical_release": False, "fabrication_release": False}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def output_guard(output):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and output.name != "sources" and not output.exists(),
            "output must be a fresh owned immediate child other than sources")
    return output


def module(path, expected):
    require(sha(path) == expected, "helper changed: " + str(path))
    spec = importlib.util.spec_from_file_location("profile_" + Path(path).stem.replace("-", "_"), path)
    require(spec is not None and spec.loader is not None, "helper unavailable")
    result = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(result)
    finally:
        sys.dont_write_bytecode = previous
    return result


def floor_direction_metadata(api, pins):
    """Join saved constraint orientation without inferring a sign from D."""
    inputs = read(PROJECTION_INPUTS)
    require(inputs["source_sha256"][str(PROJECTION_CONTRACT.relative_to(ROOT))]
            == pins[PROJECTION_CONTRACT], "compliance/projection contract binding differs")
    contract = read(PROJECTION_CONTRACT)
    saved_floor = [r for r in contract["rows"] if r["family"] == "conditional_floor_tangent_constraint"]

    def identity(row):
        return row["row_id"], row["source_group"], row["source_element"]

    saved = {identity(r): r for r in saved_floor}
    rows = read(api.GRAVITY / "row-identities.json")
    current = [r for r in rows if r["family"] == "conditional_floor_tangent_constraint"]
    require(len(saved_floor) == len(saved) == len(current) == 200 and len(rows) == 1888
            and all(r["row"] == i for i, r in enumerate(rows))
            and {identity(r) for r in current} == set(saved), "source/current floor row join differs")
    mappings = []
    for raw in current:
        original, own = saved[identity(raw)], raw["ownership"]
        require(raw["law"] == original["law"] and own == original["ownership"]
                and own["role"] == "assumed_no_slip_floor" and own["second_body"] == "floor"
                and raw["law"]["intended_law"] == "floor_tangent_all_bearing_hypothesis"
                and original["owner_point_rigid_row_sign"] == -1
                and math.isfinite(original["owner_point_rigid_row_max_abs_residual"])
                and 0 <= original["owner_point_rigid_row_max_abs_residual"] < 1e-8,
                "floor source orientation/schema differs: " + raw["row_id"])
        sign = original["owner_point_rigid_row_sign"]
        mappings.append({"row": raw["row"], "row_id": raw["row_id"],
            "source_group": raw["source_group"], "source_element": raw["source_element"],
            "first_body": own["first_body"], "second_body": own["second_body"],
            "role": own["role"], "point_mm": own["point_mm"],
            "source_constraint_axis_global_xyz": own["direction_global_xyz"],
            "source_owner_point_rigid_row_sign": sign,
            "helper_force_axis_on_first_per_unit_scalar_xyz": [sign * x for x in own["direction_global_xyz"]]})
    leg_rows = {body: [m["row"] for m in mappings if m["first_body"] == body] for body in LEGS}
    require(all(len(indices) == 8 for indices in leg_rows.values()), "profile leg floor row count differs")
    return {"schema": "floor_constraint_direction_adapter/v1", "row_count": len(mappings),
            "profile_leg_floor_row_indices": leg_rows,
            "projection_contract_sha256": pins[PROJECTION_CONTRACT],
            "compliance_inputs_sha256": pins[PROJECTION_INPUTS],
            "current_compact_row_identities_sha256": pins[api.GRAVITY / "row-identities.json"],
            "mappings": mappings, "full_D_join_executed": False,
            "original_actions_for_guard_retained": True,
            "scope": "Private physical-force direction metadata for unchanged -D.T scalar reactions. The saved source axis, point, law, role, D, W and response forces remain unchanged."}


def private_action_rows(rows, model, D, direction_map, np):
    """Parent-only full D binding before the original ownership guard runs."""
    require(len(rows) == 1888 and D.shape == (1888, 6 * len(model["body_names"])),
            "current D/body ordering shape differs")
    private = copy.deepcopy(rows)
    for mapping in direction_map["mappings"]:
        i, body = mapping["row"], mapping["first_body"]
        raw, own = rows[i], rows[i]["ownership"]
        require(raw["row"] == i and raw["row_id"] == mapping["row_id"]
                and raw["source_group"] == mapping["source_group"]
                and raw["source_element"] == mapping["source_element"]
                and own["first_body"] == body and own["second_body"] == mapping["second_body"]
                and own["role"] == mapping["role"] and own["point_mm"] == mapping["point_mm"]
                and own["direction_global_xyz"] == mapping["source_constraint_axis_global_xyz"],
                "private floor row identity differs")
        center = np.mean([model["physical_node_coordinates_mm"][str(n)]
                          for n in model["body_nodes"][body]], axis=0)
        point, axis = np.array(mapping["point_mm"]), np.array(mapping["source_constraint_axis_global_xyz"])
        sign = mapping["source_owner_point_rigid_row_sign"]
        # Saved owner_rigid_row is (-axis on first, +axis on second).
        # Constraint orientation comes from the authenticated contract.
        expected = sign * np.r_[-axis, -np.cross(point - center, axis) / 1000]
        first = 6 * model["body_names"].index(body)
        require(np.isfinite(D[i]).all() and np.max(abs(D[i, first:first + 6] - expected)) < 1e-8,
                "saved floor orientation/full D force-moment binding differs: " + raw["row_id"])
        require(np.max(abs(np.r_[D[i, :first], D[i, first + 6:]])) < 1e-12,
                "floor D row contains another body's action")
        private[i]["ownership"]["direction_global_xyz"] = mapping["helper_force_axis_on_first_per_unit_scalar_xyz"].copy()
        private[i]["source_constraint_direction_binding"] = copy.deepcopy(mapping)
    require(rows != private and len(private) == len(rows), "private floor context was not constructed")
    return private


def sources():
    """Authenticate fixed inputs and join identities without numerical helpers."""
    api = module(PIN_HELPER, PINS[PIN_HELPER])  # This existing module is stdlib-only.
    pins = {**api.PINS, **api.CLASSIFIER_PINS, **PINS}
    api.bind(pins, Path(__file__).resolve(), sha(__file__))
    api.authenticate(pins)
    fresh, inputs, assessment, comparison, geometry, package, bridge, adapter, native = [read(p) for p in (
        api.REPORT, api.INPUTS, api.ASSESSMENT, api.COMPARISON, api.GEOMETRY,
        PACKAGE, BRIDGE, ADAPTER, NATIVE)]
    require(fresh["source_sha256"] == inputs["source_sha256"], "fresh extraction closure differs")
    for record in (fresh, assessment, comparison):
        for relative, digest in record["source_sha256"].items():
            api.bind(pins, ROOT / relative, digest)
    for folder, record in ((api.MEMBERS, fresh), (api.GRAVITY, assessment)):
        for relative, digest in record["output_sha256"].items():
            artifact = (folder / relative).resolve()
            require(artifact.is_relative_to(folder), "source output leaves its packet")
            api.bind(pins, artifact, digest)
    for source in (PACKAGE, BRIDGE):
        require(read(source.with_name("receipt.json"))["output_sha256"][source.name] == pins[source],
                "geometry/package receipt differs")
    require(read(NATIVE.with_name("freeze.json"))["files_sha256"]["model.json"] == pins[NATIVE]
            and native["source_model_sha256"] == pins[ADAPTER], "native source mesh binding differs")
    require(comparison["response_sha256"] == pins[api.RESPONSE]
            and assessment["actual_new_hole_stiffness_qualified"] is False
            and assessment["H_D_B_connector_rows_and_k_unchanged"] is True, "fresh frame scope differs")
    require(package["proposal_adopted"] is False and package["census"] == {
        "bodies": 50, "timber_blanks": 44, "blocks": 24, "bolts": 108, "nuts": 108,
        "washers": 216, "Hillman_screws": 66, "bolt_case_records": 648,
        "screw_case_records": 396, "local_corner_case_records": 96,
        "local_continuous_shaft_case_records": 24, "global_existing_case_records": 504,
        "static_internal_case_records": 24}, "unadopted proposal census differs")
    require(package["source_load_identity"] == {"source_climber_weight_lb": 250,
        "source_dynamic_factor": 2, "source_hold_lever_mm": 100,
        "source_horizontal_force_magnitude_n": 300}, "fixed force/lever scope differs")
    require(tuple(package["case_ids"]) == tuple(c["case_id"] for c in fresh["cases"]) == api.CASES
            and package["dead_load_factor"] == assessment["dead_load_factor"]
            == comparison["dead_load_factor"] == fresh["same_state_dead_load_factor"], "fresh cases/gravity differ")
    effective = {r["body"]: r for r in package["geometry"]["effective_members"]}
    members = geometry["members"]
    load_inputs = read(api.GRAVITY / "model-inputs.json")
    model = read(api.GRAVITY / "model.json")
    descriptors = {r["member_id"]: r for r in load_inputs["members"]}
    require(len(effective) == len(descriptors) == 50 and len(members) == 44
            and set(effective) == set(model["body_names"]) == set(adapter["body_geometry"]),
            "50/44 current body identity differs")
    require(model["physical_elements"] == native["elements"], "inherited native connectivity differs")
    for body, row in effective.items():
        for key in ("current_step", "effective_proposal_step"):
            api.bind(pins, ROOT / row[key]["path"], row[key]["sha256"])
        if body in members and body not in api.EXCLUDED:
            require(row["effective_proposal_step"]["sha256"] == members[body]["current_finished_step_sha256"],
                    "current finished profile binding differs: " + body)
    require(SURFACES in pins, "finished surface register absent from frozen closure")
    surface_records = {r["member_id"]: r for r in read(SURFACES)["records"]}
    targets = []
    for body in LEGS:
        record = members[body]
        require(record["recess_source"] == record["geometry"]["floor_recess_geometry"]
                == adapter["body_geometry"][body]["geometry_record"]["floor_recess_geometry"],
                "saved exact recess recipe differs: " + body)
        endpoints = record["geometry"]["additional_recovery_stations_mm"]
        require(len(endpoints) == 2 and surface_records[body]["step_binding"]["file_sha256"]
                == record["current_finished_step_sha256"], "recess endpoints/STEP differ")
        for i, (station, section) in enumerate(zip(record["stations_mm"], record["rectangle_at_station"], strict=True)):
            if station <= endpoints[1] + TOL:
                targets.append({"body": body, "station_index": i, "station_mm": station,
                                "saved_trace_indices": [2 * i, 2 * i + 1],
                                "source_section_status": section["status"],
                                "feature_ids": section.get("feature_ids", [])})
    partitions = Counter(t["source_section_status"] for t in targets)
    require(targets and partitions["BORE_FREE_PROFILE_RECTANGLE"] > 0, "empty supported recess family")
    direction_map = floor_direction_metadata(api, pins)
    api.authenticate(pins)
    plan = {"schema": "profile_method_preparation/v1", "status": "PREPARED_NOT_EXECUTED",
            "source_sha256": api.source_map(pins), "source_count": len(pins),
            "producer_sha256": pins[Path(__file__).resolve()], "runtime": {"python": platform.python_version()},
            "force_basis": "unadopted108_ce69_c3a8_62bd", "case_ids": list(api.CASES),
            "proposal_census": package["census"], "source_load_identity": package["source_load_identity"],
            "dead_load_factor": package["dead_load_factor"], "modeled_mass_kg": package["modeled_mass_kg"],
            "targets": targets, "target_station_count": len(targets), "target_signed_limit_count": 12 * len(targets),
            "source_status_station_counts": dict(partitions), "duration_scenarios": DURATIONS,
            "N07_notch_resistance": "INAPPLICABLE_NDS_PERMITTED_END_TAPER_ROUTE",
            "notch_route_missing_basis": "Resistance for the actual deep side recess with oblique end bearing and complete signed N/V/M/T; NDS 3.4.3.1 requires permitted end cuts, not every tapered profile.",
            "leaf_scope": {"opening_stations": "member-opening-remainder.py owner Gibbs",
                           "splitting_fracture_anchorage": "all-joint-splitting peer",
                           "terminal_point_load_profiles": "explicit traction-distribution method gap"},
            "original_all42_terminal_signed_limits": 1176,
            "original_all42_unmachined_exclusion_signed_limits": 264,
            "floor_direction_adapter": direction_map,
            "arithmetic_executed": False, "limits": LIMITS, "primary_sources": SOURCES, **FLAGS}
    return api, pins, plan, members, effective, descriptors, bridge, read(CORRECTION), adapter, native, model, surface_records


def start(output, pins):
    output_guard(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    with (output / "producer.py.snapshot").open("xb") as stream:
        stream.write(Path(__file__).read_bytes())
    require(sha(output / "producer.py.snapshot") == pins[Path(__file__).resolve()], "producer snapshot differs")


def finish(output, api, pins, status, arithmetic):
    api.authenticate(pins)
    hashes = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    dump(output / "receipt.json", {"schema": "profile_method_receipt/v1", "status": status,
         "source_sha256": api.source_map(pins), "output_sha256": hashes,
         "producer_sha256": pins[Path(__file__).resolve()], "arithmetic_executed": arithmetic, **FLAGS})
    api.authenticate(pins)
    require(all(sha(output / name) == digest for name, digest in hashes.items()), "published output changed")


def prepare(output):
    output = output_guard(output)
    api, pins, plan, *_ = sources()
    start(output, pins)
    dump(output / "preparation.json", plan)
    finish(output, api, pins, plan["status"], False)
    return plan


def outcome(value):
    require(math.isfinite(value) and value >= 0, "invalid finite comparison")
    return "FINITE_REFERENCE_EXCEEDANCE" if value > 1 else "FINITE_REFERENCE_NOT_EXCEEDED"


def profile_inventory(members, surfaces, effective, np):
    """Classify saved outward profiles; circular caps are interior bore boundaries."""
    result = []
    for body, record in sorted(members.items()):
        g = record["geometry"]
        frame = np.array([g[k] for k in ("axis", "section_u", "section_v")])
        length = float(np.linalg.norm(np.array(g["end"]) - g["start"]))
        caps = {f["feature_id"] for f in surfaces[body]["features"] if f["surface_kind"] == "PLANE"
                and any(w["edge_count"] == 1 and w["edges"][0]["curve_kind"] == "CIRCLE"
                        for w in f["trim"]["wires"])}
        shoulders, ramps = [], []
        for plane in record["profile_planes"]:
            if plane["id"] in caps:
                continue
            n = frame @ plane["normal"]
            if abs(abs(n[0]) - 1) < 1e-7 and plane["lo"] > TOL and plane["hi"] < length - TOL:
                shoulders.append(plane)
            elif abs(n[0]) > 1e-7 and max(abs(n[1:])) > 1e-7:
                ramps.append({**plane, "normal_grain_u_v": n.tolist(),
                              "role": "interior_taper_runout" if plane["lo"] > TOL and plane["hi"] < length - TOL
                              else "convex_terminal_end_trim"})
        result.append({"body": body, "saved_profile_source": record["current_finished_step"],
                       "saved_profile_sha256": record["current_finished_step_sha256"],
                       "effective_proposal_STEP": effective[body]["effective_proposal_step"],
                       "two_spine_hole_overlays_supersede_bores_only": body.startswith("knee_outer_") and body.endswith("_spine"),
                       "square_shoulder_candidates": shoulders, "ramps_and_end_trims": ramps,
                       "excluded_blind_cylinder_cap_ids": sorted(caps),
                       "recess_source": record["recess_source"],
                       "source_profile_status_counts": dict(Counter(s["status"] for s in record["rectangle_at_station"]))})
    require(not any(r["square_shoulder_candidates"] for r in result), "unresolved current square shoulder found")
    return result


def mesh_audit(effective, descriptors, bridge, correction, adapter, native, model, members, np):
    """Join saved native volumes; do not integrate, remesh or replace stiffness."""
    weights = {r["body"]: r for r in adapter["gravity_load_audits"]["member_self_weight_rows"]}
    require(set(weights) == set(effective), "50 saved source-mesh volumes required")
    corrected = {r["block"]: r["finished_proposal_volume_mm3"] for r in correction["proposals"]}
    corrected.update({r["host"]: r["finished_host_volume_mm3"] for r in correction["side_host_bore_replacements"]})
    rows = []
    for body, current in sorted(effective.items()):
        descriptor = descriptors[body]["reduced_geometry_descriptor"]
        source_record = adapter["body_geometry"][body]["geometry_record"]
        diagnostic = source_record.get("geometry_diagnostics", {})
        old_volume = descriptor.get("actual_volume_mm3", descriptor.get("exact_volume_mm3"))
        volume = corrected.get(body, old_volume)
        basis = "unchanged_finished_descriptor"
        if body in corrected:
            basis = "frozen_top_corner_finished_correction"
        if body in bridge["bodies"]:
            volume = bridge["bodies"][body]["proposal"]["observed"]["volume_mm3"]
            basis = "unadopted108_two_added_spine_holes"
        require(volume is not None and math.isfinite(volume) and volume > 0, "missing finished volume: " + body)
        ids = {str(n) for eid in native["physical_body_elements"][body] for n in native["elements"][str(eid)][1]}
        delta = max(float(np.max(abs(np.array(model["physical_node_coordinates_mm"][n]) - native["nodes"][n]))) for n in ids)
        mesh_volume = weights[body]["mesh_volume_mm3"]
        require(math.isfinite(mesh_volume) and mesh_volume > 0, "invalid saved source-mesh volume")
        row = {"body": body, "current_effective_STEP": current["effective_proposal_step"],
               "finished_volume_basis": basis, "effective_finished_volume_mm3": volume,
               "inherited_descriptor_STEP": {"path": descriptor["step_path"], "sha256": descriptor["step_sha256"]},
               "inherited_descriptor_finished_volume_mm3": old_volume,
               "effective_minus_inherited_finished_volume_mm3": volume - old_volume,
               "saved_native_mesh_volume_mm3": mesh_volume,
               "saved_native_mesh_minus_effective_finished_volume_mm3": mesh_volume - volume,
               "saved_mesh_record_pointer": "/gravity_load_audits/member_self_weight_rows/" + str(
                   adapter["gravity_load_audits"]["member_self_weight_rows"].index(weights[body])),
               "saved_mesh_source": str(ADAPTER.relative_to(ROOT)),
               "native_element_source": str(NATIVE.relative_to(ROOT)),
               "native_mesh_kind": diagnostic.get("native_member_mesh", "GROSS_PANEL_LAYER_SOLIDS"),
               "source_mesh_node_count": len(ids), "maximum_fresh_vs_native_coordinate_delta_mm": delta,
               "coordinates_within_existing_geometry_tolerance": delta <= TOL,
               "current_binding_matches_inherited_descriptor": current["effective_proposal_step"]["sha256"] == descriptor["step_sha256"],
               "exact_finished_compliance": False, "exact_finished_mesh": False}
        if body in LEGS:
            recess = members[body]["recess_source"]
            observed = mesh_volume - recess["expected_retained_volume_mm3"]
            points = np.array([native["nodes"][n] for n in ids])
            g = members[body]["geometry"]
            stations = (points - g["start"]) @ g["axis"]
            plane_rows = []
            for plane in members[body]["profile_planes"]:
                selected = points[(stations >= plane["lo"] - TOL) & (stations <= plane["hi"] + TOL)]
                require(len(selected) > 0, "source mesh has no node in profile face interval")
                residual = selected @ plane["normal"] - plane["offset"]
                plane_rows.append({"face_id": plane["id"], "sampled_native_node_count": len(selected),
                                   "maximum_outward_distance_mm": max(0.0, float(max(residual))),
                                   "minimum_absolute_plane_distance_mm": float(min(abs(residual)))})
            endpoints = g["additional_recovery_stations_mm"]
            intersecting_bores = [opening for opening in members[body]["bore_or_passage_intervals"]
                                 if opening["lo"] <= endpoints[1] + TOL and opening["hi"] >= endpoints[0] - TOL]
            row["recess"] = {"recipe": recess, "saved_native_geometry_recipe_matches_finished_descriptor":
                source_record["floor_recess_geometry"] == recess,
                "saved_mesh_minus_filled_profile_volume_mm3": observed,
                "filled_profile_volume_match_within_existing_0_05_mm3": abs(observed) <= 0.05,
                "filled_bore_omission_volume_mm3": recess["filled_bore_omission_volume_mm3"],
                "mesh_minus_drilled_STEP_minus_omitted_bores_mm3": mesh_volume - volume - recess["filled_bore_omission_volume_mm3"],
                "native_profile_plane_samples": plane_rows,
                "all_sampled_planes_within_existing_geometry_tolerance": all(
                    r["maximum_outward_distance_mm"] <= TOL and r["minimum_absolute_plane_distance_mm"] <= TOL for r in plane_rows),
                "local_grain_taper_bounds_mm": endpoints,
                "opening_intervals_intersecting_taper_or_runout": intersecting_bores,
                "taper_and_runout_unbored_geometry": not intersecting_bores,
                "foot_bores_below_taper": [opening for opening in members[body]["bore_or_passage_intervals"]
                                          if opening["hi"] < endpoints[0] - TOL],
                "upper_bores_above_taper": [opening for opening in members[body]["bore_or_passage_intervals"]
                                           if opening["lo"] > endpoints[1] + TOL],
                "continuous_finished_surface_match_claimed": False}
        rows.append(row)
    return rows


def notch_basis(body, record):
    """Evaluate the actual geometric eligibility before any shear capacity."""
    recess, g = record["recess_source"], record["geometry"]
    d, b = g["width_mm"], g["depth_mm"]  # The cut removes section_u, not section_v.
    removed, run = recess["max_recess_depth_mm"], recess["taper_run_mm"]
    return {"body": body, "profile": "open_lower_side_recess_with_continuous_1_to_12_runout",
            "weak_plane_depth_d_mm": d, "breadth_b_mm": b, "remaining_depth_dn_mm": d - removed,
            "removed_depth_mm": removed, "removed_fraction_of_weak_depth": removed / d,
            "taper_run_mm": run, "run_over_removed_depth": run / removed,
            "one_in_ten_geometric_margin_mm": run - 10 * removed,
            "intended_4x6_stock_depth_and_runout_geometry_matches": all((
                abs(d - 88.9) <= TOL, abs(b - 139.7) <= TOL,
                abs(removed - 38.1) <= TOL, abs(run - 457.2) <= TOL)),
            "NDS_4_4_3_1_end_cut_limit_mm": d / 4,
            "NDS_4_4_3_1_margin_mm": d / 4 - removed,
            "NDS_4_4_3_1_geometry_outcome": "EXCEEDS_PERMITTED_END_TAPER_DEPTH" if removed > d / 4 + TOL else "WITHIN_END_TAPER_DEPTH_ONLY",
            "NDS_3_2_3_2_small_notch_stiffness_depth_limit_mm": d / 6,
            "NDS_3_2_3_2_small_notch_stiffness_length_limit_mm": d / 3,
            "NDS_3_2_3_2_small_notch_stiffness_exception_applicable": False,
            "NDS_3_4_3_1_c_tension_taper_route": "Requires permitted end cut and Figure 3D support; otherwise no resistance assigned.",
            "NDS_3_4_3_1_a_equation_3_4_3": "Vr = (2/3) * Fv_prime * b * dn * (dn/d)**2",
            "NDS_equation_applied_to_current_recess": False,
            "notch_shear_resistance_n": None, "notch_shear_ratio": None,
            "notch_shear_outcome": "INAPPLICABLE_PERMITTED_END_CUT_AND_SUPPORT_ROUTE",
            "support_mapping_gap": "Current bearing acts on the oblique grain foot at global Z=0; Figure 3D end bearing lies along a grain-parallel beam face. No equivalence is supplied.",
            "missing_basis": "A resistance relation for the recorded deep side recess and actual oblique end/contact loading, including simultaneous signed bending, two transverse shears, torque and bores; splitting/anchorage stays with its peer."}


def summaries(rows):
    result = {}
    for scenario in DURATIONS:
        own = [r for r in rows if r["duration_scenario"] == scenario]
        result[scenario] = {"finite_duration_records": len(own),
            "metrics": {metric: {"finite_count": len(own),
                "exceedance_count": int(sum(r[metric] > 1 for r in own)),
                "maximum_witness": max(own, key=lambda r: r[metric]) if own else None,
                "outcome": ("EMPTY_NOT_A_PASS" if not own else
                    "FINITE_REFERENCE_EXCEEDANCE" if any(r[metric] > 1 for r in own) else "FINITE_REFERENCE_NOT_EXCEEDED")}
                for metric in METRICS}}
    return result


def build(output):
    """Parent serializes actual signed-cut arithmetic; no producer pipeline runs."""
    output = output_guard(output)
    api, pins, plan, members, effective, descriptors, bridge, correction, adapter, native, model, surfaces = sources()
    import numpy as np

    replay, net, header, previous, rail = [module(HERE / name, pins[HERE / name]) for name in (
        "knee-bridge-remaining-sections.py", "corner-net-section.py", "header-net-section.py",
        "top-host-net-sections.py", "knee-bridge-top-rail.py")]
    fresh, joined_model, rows, _ = replay.source_context(pins)
    require(joined_model == model and api.source_map(pins) == plan["source_sha256"], "numerical context expanded closure")
    require(rail.DURATIONS == DURATIONS, "duration assumptions differ")
    net.rectangle_torsion = cache(net.rectangle_torsion)
    outer_at = previous.outer_rectangle_function()
    profiles = profile_inventory(members, surfaces, effective, np)
    mesh = mesh_audit(effective, descriptors, bridge, correction, adapter, native, model, members, np)
    notch = [notch_basis(body, members[body]) for body in LEGS]
    require(all(r["NDS_4_4_3_1_geometry_outcome"] == "EXCEEDS_PERMITTED_END_TAPER_DEPTH" for r in notch), "unexpected end-taper eligibility")
    api.authenticate(pins)
    start(output, pins)
    dump(output / "preparation.json", plan)
    dump(output / "geometry-method-audit.json", {"profiles": profiles, "mesh_and_finished_volumes": mesh,
         "notch_applicability": notch, "historical_square_notch_recipe": {
             "current_square_notch_found": False, "notch_shear_ratio": None,
             "outcome": "SUPERSEDED_RECIPE_NOT_A_CURRENT_PASS",
             "current_base_end_profiles": "Convex level/plumb trims; their terminal traction gap remains explicit."}})
    material = read(api.MATERIALS)
    audited, results, exclusions, count = [], [], [], 0
    with (np.load(api.ARRAYS, allow_pickle=False) as arrays,
          np.load(api.RESPONSE, allow_pickle=False) as response,
          np.load(api.GRAVITY / "operators.npz", allow_pickle=False) as operators,
          gzip.open(output / "cuts.jsonl.gz", "wt") as stream):
        action_rows = private_action_rows(rows, model, operators["D"], plan["floor_direction_adapter"], np)
        direction_audit = {**plan["floor_direction_adapter"], "full_D_join_executed": True,
                           "original_source_metadata_mutated": False}
        dump(output / "ownership-direction-map.json", direction_audit)
        for body in LEGS:
            record, g = members[body], members[body]["geometry"]
            frame = np.array([g[k] for k in ("axis", "section_u", "section_v")])
            targets = [t for t in plan["targets"] if t["body"] == body]
            for case in fresh["cases"]:
                source, _, negative, audit = replay.actions_for(case, body, record, arrays, response,
                    operators["D"], operators["W"], model, action_rows, header)
                binding, _ = replay.material_for(source, material, net)
                audit["private_floor_direction_adapter_used"] = True
                audited.append(audit)
                prefix = source["array_prefix"]
                for target in targets:
                    station, si = target["station_mm"], target["station_index"]
                    outer = outer_at(station, g, record["profile_planes"], record["bore_or_passage_intervals"])
                    require(outer["status"] == target["source_section_status"], "saved profile applicability differs")
                    supported = outer["status"].startswith("BORE_FREE_")
                    for before in (True, False):
                        index = 2 * si + int(not before)
                        cut, datum = previous.global_cut(arrays[prefix + "__point_force_free_couple_xyz"],
                            arrays[body + "__point_xyz_mm"], arrays[body + "__point_stations_mm"], g, station, before)
                        local = np.r_[frame @ cut[:3], frame @ cut[3:]]
                        replay.difference(local, negative[index], "fresh complete signed cut")
                        row = {**target, "case": case["case_id"], "limit": "before" if before else "after",
                               "saved_trace_index": index, "signed_cut_grain_u_v_n_nmm": local.tolist(),
                               "cut_datum_xyz_mm": datum.tolist(), "notch_shear_ratio": None}
                        if supported:
                            lo, hi = outer["bounds_uv_mm"]
                            section = {"station_mm": station, "saved_station_index": si,
                                       "regions": [{"bounds_uv_mm": [[lo[0], hi[0]], [lo[1], hi[1]]]}]}
                            duration = rail.duration_results(local, section, datum, frame, case["case_id"], before, net, previous, binding)
                            for item in duration.values():
                                replay.difference(item["nominal_section"]["reconstructed_signed_cut_n_nmm"], local,
                                                  "profile centroid signed-wrench recovery")
                                summary = item["summary"]
                                summary["body"] = body
                                summary["outcomes"] = {m: outcome(summary[m]) for m in METRICS}
                                results.append(summary)
                            row.update(status="FINITE_NOMINAL_PROFILE_ARITHMETIC", outer_rectangle=outer, duration_results=duration)
                        else:
                            ids = target["feature_ids"]
                            kind = ("UNMACHINED_STATION_EXCLUSION" if ids and all(x.endswith("/owner_authorized_station_exclusion") for x in ids)
                                    else "OPENING_RESISTANCE_OWNED_BY_GIBBS" if outer["status"] == "NON_APPLICABLE_BORE_OR_PASSAGE"
                                    else "TERMINAL_TRACTION_DISTRIBUTION_METHOD_INAPPLICABLE")
                            row.update(status=kind, duration_results=None, comparison_outcome="NOT_A_PASS")
                            exclusions.append({**target, "case": case["case_id"], "limit": row["limit"],
                                               "saved_trace_index": index, "reason": kind})
                        stream.write(json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n")
                        count += 1
    require(count == plan["target_signed_limit_count"] and len(audited) == 12
            and len(results) == 2 * (count - len(exclusions)) and results, "profile arithmetic coverage differs")
    endpoint_rows = []
    for body in LEGS:
        record = members[body]
        for endpoint in record["geometry"]["additional_recovery_stations_mm"]:
            matches = [i for i, station in enumerate(record["stations_mm"]) if abs(station - endpoint) <= TOL]
            endpoint_rows.append({"body": body, "local_grain_station_mm": endpoint,
                                  "saved_station_indices_within_existing_tolerance": matches,
                                  "finite_signed_comparison_count": int(sum(r["body"] == body and abs(r["station_mm"] - endpoint) <= TOL for r in results))})
    result = {"schema": "profile_method_completion/v1", "status": "COMPLETE_FINITE_PROFILE_COMPARISONS_WITH_EXPLICIT_METHOD_LIMITS",
              "source_sha256": api.source_map(pins), "source_count": len(pins),
              "producer_sha256": pins[Path(__file__).resolve()], "runtime": {"python": platform.python_version(), "numpy": np.__version__},
              "case_ids": list(api.CASES), "dead_load_factor": plan["dead_load_factor"],
              "force_basis": plan["force_basis"], "target_signed_limit_count": count,
              "floor_direction_adapter": {k: v for k, v in direction_audit.items() if k != "mappings"},
              "finite_profile_signed_limit_count": count - len(exclusions),
              "unsupported_or_peer_owned_signed_limit_count": len(exclusions),
              "exclusion_counts": dict(Counter(r["reason"] for r in exclusions)),
              "excluded_cut_identities": exclusions, "comparison_summary": summaries(results),
              "recess_endpoint_coverage": endpoint_rows, "geometry_audit_body_count": len(mesh),
              "changed_binding_bodies": [r["body"] for r in mesh if not r["current_binding_matches_inherited_descriptor"]],
              "N07": {"finite_bore_free_profile_arithmetic_complete": True,
                       "notch_resistance_outcome": "INAPPLICABLE_PERMITTED_END_CUT_AND_SUPPORT_ROUTE",
                       "all_recess_strength_comparisons_complete": False},
              "N19": {"effective_50_STEP_bindings_authenticated": True,
                       "saved_native_filled_profile_evidence_joined": True,
                       "exact_finished_geometry_and_H": False,
                       "all_machining_represented_in_native": False,
                       "remaining_basis": "Named hole/profile omissions and sampled/terminal method limits in geometry-method-audit.json; no generic native rerun prerequisite."},
              "arithmetic_executed": True, "limits": LIMITS, **FLAGS}
    api.authenticate(pins)
    dump(output / "action-audits.json", {"audits": audited})
    dump(output / "checks.json", result)
    finish(output, api, pins, result["status"], True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true", help="standard-library source authentication and joins only")
    args = parser.parse_args()
    packet = prepare(args.output) if args.prepare else build(args.output)
    print(json.dumps({"status": packet["status"], "source_count": packet["source_count"]}))
