"""Join the frozen, unadopted knee bridge when the parent calls build(output).

Import is inert. The only new mechanics arithmetic is the exact rigid wrench
sum of each prescribed axial end pair; no other producer or helper is run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ASSEMBLY = HERE.parent / "assembly-package"
RAW = HERE / "rawlocal/knee-bridge-integration"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
BODIES = ("knee_outer_left_spine", "knee_outer_right_spine")
CURRENT_COUNTS = {"bolts": 104, "nuts": 104, "washers": 208, "Hillman_screws": 66}
PROPOSED_COUNTS = {"bolts": 108, "nuts": 108, "washers": 216, "Hillman_screws": 66}
FROZEN = {
    "normal": (HERE / "rawlocal/knee-spine-reinforcement/attempt01/checks.json",
               "c9360e7ca4ab167a5cbc505373b2bd1342aa6a830f72a26113da9f7c4a8ad778"),
    "normal_receipt": (HERE / "rawlocal/knee-spine-reinforcement/attempt01/receipt.json",
                       "991f6742f6aae386552338b1fea79f02766bd0def09bfa8fabea27560ba13819"),
    "geometry": (HERE / "rawlocal/knee-bridge-geometry/attempt01/manifest.json",
                 "254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147"),
    "geometry_receipt": (HERE / "rawlocal/knee-bridge-geometry/attempt01/receipt.json",
                         "92ccabb307b6d9cbcd8f768b8275a7ecf4ef6ae6a55a7be2cd83742d76be9973"),
    "fit_setup": (ASSEMBLY / "rawlocal/knee-bridge-fit/prepare-attempt02/setup.json",
                  "794f1aa45fa9f47955f16a083a3637b2821615ede47640817305a60ddab4ddfb"),
    "fit_result": (ASSEMBLY / "rawlocal/knee-bridge-fit/run-attempt01/result.json",
                   "5a2a2e3c886353d4a24262748d0169ba33826cdcca76e8fa01c0a1e0d2bfde8b"),
    "order": (ASSEMBLY / "rawlocal/knee-bridge-order/attempt01/proposal-order.json",
              "028542c6127320ce51410ed9f0910896a1ee1b13c5737fcdc68895b500e2ffe1"),
    "order_receipt": (ASSEMBLY / "rawlocal/knee-bridge-order/attempt01/receipt.json",
                      "9dfd84b938fe7be0f7917c1bfef57f451cb26a53da94295c2accae91ac9b4774"),
    "register": (HERE / "rawlocal/working-joint-register/attempt03/register.json",
                 "c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c"),
    "model": (HERE / "operators-attempt02/model.json",
              "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626"),
}
FLAGS = {
    "proposal_adopted": False,
    "current_geometry_changed": False,
    "current_axes_changed": False,
    "authority_changed": False,
    "original_force_envelope_reused": True,
    "changed_geometry_global_force_acceptance_transferred": False,
    "changed_geometry_elastic_operator_acceptance_transferred": False,
    "gravity_delta_in_global_model": False,
    "loads_or_stiffness_changed": False,
    "compatibility_unsolved": True,
    "global_compatibility_asserted": False,
    "wood_stiffness_or_compatibility_solved": False,
    "displacement_feedback_asserted": False,
    "new_receiver_interface_added": False,
    "floor_restraint_added": False,
    "new_lateral_capacity_established": False,
    "installation_preload_credited": False,
    "hardware_capacity_qualified": False,
    "complete_joint_acceptance": False,
    "fabrication_authorized": False,
    "physical_release": False,
    "mechanics_recalculated": False,
    "native_or_CAD_run": False,
    "frame_or_method_run": False,
    "tests_or_review_run": False,
}


def require(condition, message):
    if not condition:
        raise ValueError(f"STOP: {message}")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def key(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def dump(path, record):
    Path(path).write_text(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n")


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def close(a, b, description, tolerance=1e-6):
    require(len(a) == len(b) and all(math.isfinite(float(x)) and math.isfinite(float(y))
                                   and abs(x - y) <= tolerance for x, y in zip(a, b)), description)


def build(output):
    """Write one fresh immediate child of rawlocal/knee-bridge-integration.

    The parent owns execution. Return paths and hashes, never an adoption or
    compatibility verdict. Existing geometry is referenced, not copied.
    """
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "output must be a fresh immediate child")
    pins = {}

    def pin(path, expected):
        path = Path(path).resolve()
        require(path.is_relative_to(ROOT), f"source leaves repository: {path}")
        require(path not in pins or pins[path] == expected, f"conflicting pin: {path}")
        require(sha(path) == expected, f"source hash differs: {path}")
        pins[path] = expected

    def read_pinned(path, expected):
        pin(path, expected)
        record = json.loads(Path(path).read_text())
        require(sha(path) == expected, f"source changed during read: {path}")
        return record

    def ref(path, pointer=""):
        return {"source": key(path), "sha256": pins[Path(path).resolve()], "record_pointer": pointer}

    def source_ref(name, pointer=""):
        return ref(FROZEN[name][0], pointer)

    def unique(records, field, description):
        result = {record[field]: (i, record) for i, record in enumerate(records)}
        require(len(result) == len(records), f"duplicate {description}")
        return result

    def authenticate():
        for path, expected in pins.items():
            require(sha(path) == expected, f"source changed during integration: {path}")

    pin(Path(__file__), sha(__file__))
    data = {name: read_pinned(path, expected) for name, (path, expected) in FROZEN.items()}
    normal, geometry, setup, fit, order, register, model = (
        data[name] for name in ("normal", "geometry", "fit_setup", "fit_result", "order", "register", "model"))
    schemas = {
        "normal": "knee-spine-v-bridge-static-proposal/v1",
        "geometry": "knee-bridge-proposal-geometry/v1",
        "fit_setup": "knee_bridge_saved_scene_fit_setup/v1",
        "fit_result": "knee_bridge_saved_scene_fit_result/v1",
        "register": "working_six_case_joint_force_register/v1",
        "model": "simple_corrected_frame_model/v1",
    }
    for name, schema in schemas.items():
        require(data[name]["schema"] == schema, f"unsupported {name} schema")
    for name in ("normal", "geometry", "fit_setup", "fit_result", "order"):
        require(data[name]["proposal_adopted"] is False and data[name]["physical_release"] is False,
                f"{name} is not an unreleased proposal")
    for name, receipt in (("normal", "normal_receipt"), ("geometry", "geometry_receipt"), ("order", "order_receipt")):
        require(data[receipt]["output_sha256"][FROZEN[name][0].name] == FROZEN[name][1],
                f"{name} receipt does not bind output")
        require(data[receipt]["source_sha256"] == data[name]["source_sha256"], f"{name} receipt source map differs")
    require(fit["setup_sha256"] == FROZEN["fit_setup"][1], "fit result does not bind setup")
    require(fit["status"] == "BOUNDED_NOMINAL_SCENE_FIT_CLEAR" and not fit["overlap_pairs"]
            and not fit["undecided_pairs"], "saved fit has unresolved pairs")
    require(register["case_ids"] == list(CASES), "six-case register differs")
    require(model["candidate"] == register["candidate"] and model["source_revision"] == register["source_revision"]
            and model["development_revision"] == register["development_revision"], "frame/register identity differs")

    # These are byte references only. No operator, response or helper is loaded.
    for binding in register["frame_authority"].values():
        pin(ROOT / binding["source"], binding["sha256"])
    operators = HERE / "operators-attempt02/operators.npz"
    pin(operators, register["source_sha256"][key(operators)])
    model_inputs_path = HERE / "operators-attempt02/model-inputs.json"
    model_inputs = read_pinned(model_inputs_path, setup["source_sha256"][key(model_inputs_path)])

    # Freeze authority at invocation, because the parent owns concurrent publication.
    authority_paths = [ROOT / name for name in (
        "current-candidate.json", "barrel-nut-candidate.json", "wood-joints-candidate.json",
        "docs/wood-joints-mvp/criteria.json", "docs/wood-joints-mvp/authority-integrity.json")]
    authorities = {key(path): read_pinned(path, sha(path)) for path in authority_paths}
    candidate = authorities["wood-joints-candidate.json"]
    criteria = authorities["docs/wood-joints-mvp/criteria.json"]
    criteria_records = criteria["legacy_criteria"] + criteria["additional_candidate_obligations"]
    require(len(criteria_records) == 47 and all(row["status"] == "pending" for row in criteria_records),
            "expected 47 pending criteria")
    require(len(candidate["release_flags"]) == 8 and all(value is False for value in candidate["release_flags"].values())
            and candidate["release"] is False, "expected eight false release flags")
    require(candidate["candidate"] == register["candidate"], "development authority differs")

    for counts in (normal["current_authority_counts"], geometry["current_authority_counts"], order["current_counts"]):
        require(counts == CURRENT_COUNTS, "current hardware census differs")
    for counts in (normal["hypothetical_counts_if_later_adopted"],
                   geometry["hypothetical_counts_if_later_adopted"], order["proposed_counts"]):
        require(counts == PROPOSED_COUNTS, "proposed hardware census differs")
    require(normal["source_load_identity"] == {
        "source_climber_weight_lb": 250, "source_dynamic_factor": 2,
        "source_horizontal_force_magnitude_n": 300, "source_hold_lever_mm": 100}, "load identity differs")
    require(normal["source_gravity_multiplier"] == model["dead_load_factor"], "gravity multiplier differs")
    require(set(normal["geometry_proposals"]) == set(geometry["bodies"]) == set(BODIES), "spine coverage differs")

    # The saved scene includes the current four top STEP corrections. The older
    # model-input member STEP bindings must not overwrite that baseline.
    members = unique(model_inputs["members"], "member_id", "member")
    wood = unique([row for row in setup["obstacles"] if row["category"] == "wood"], "id", "wood obstacle")
    require(len(members) == len(wood) == len(model["body_names"]) == 50, "body census differs")
    require(set(members) == set(model["body_names"]), "geometry/model body membership differs")
    effective_members, overrides = [], []
    for body in model["body_names"]:
        require(f"wood/{body}" in wood, f"missing current geometry: {body}")
        _, obstacle = wood[f"wood/{body}"]
        step = ROOT / obstacle["step_path"]
        pin(step, setup["source_sha256"][key(step)])
        source_binding = {"path": key(step), "sha256": pins[step.resolve()]}
        effective_binding = source_binding
        if body in BODIES:
            record = geometry["bodies"][body]
            require(record["source_step_binding"]["path"] == key(step)
                    and record["source_step_binding"]["file_sha256"] == pins[step.resolve()],
                    f"proposal replaces a different source spine: {body}")
            exports = [(name, row) for name, row in record["exports"].items() if Path(name).suffix == ".step"]
            require(len(exports) == 1, f"expected one proposal STEP: {body}")
            filename, binding = exports[0]
            require(Path(filename).name == filename, "proposal STEP filename leaves packet")
            proposal_step = FROZEN["geometry"][0].parent / filename
            require(data["geometry_receipt"]["output_sha256"][filename] == binding["sha256"], "STEP receipt differs")
            pin(proposal_step, binding["sha256"])
            require(proposal_step.stat().st_size == binding["size_bytes"], "proposal STEP size differs")
            effective_binding = {"path": key(proposal_step), "sha256": binding["sha256"], "size_bytes": binding["size_bytes"]}
            overrides.append({"body": body, "current_step": source_binding, "proposal_step": effective_binding,
                              "geometry_reference": source_ref("geometry", f"/bodies/{body}"), "proposal_adopted": False})
        effective_members.append({"body": body, "current_step": source_binding, "effective_proposal_step": effective_binding,
                                  "source_bounds_xyz_mm": obstacle["bounds_xyz_mm"],
                                  "member_reference": ref(model_inputs_path, f"/members/{members[body][0]}"),
                                  "geometry_role": "proposal_override" if body in BODIES else "unchanged_current_geometry"})

    connections = unique(model_inputs["connections"], "axis_id", "connection")
    old_axes = unique(register["axes"], "axis_id", "existing bolt axis")
    screws = unique(register["panel_kicker_screws"], "axis_id", "Hillman axis")
    require(len(old_axes) == 104 and len(screws) == 66 and len(register["blocks"]) == 24, "register census differs")
    require(set(old_axes).isdisjoint(screws) and set(connections) == set(old_axes) | set(screws), "connection axis census differs")
    require(model["owner_authorized_screw_movements"] == register["owner_authorized_screw_movements"], "screw movements differ")
    existing_axes, receiver_forces = [], []
    for axis_id, (i, axis) in old_axes.items():
        ci, connection = connections[axis_id]
        require(connection["kind"] in ("candidate_bolt", "retained_bolt"), "bolt/screw kind differs")
        require(set(connection["receiver_member_ids"]) == set(axis["receivers"]), f"receiver membership differs: {axis_id}")
        require(set(axis["receivers"]) <= set(members), "unknown existing receiver")
        states = unique(axis["per_state"], "case_id", f"case for {axis_id}")
        require(set(states) == set(CASES), f"missing case for {axis_id}")
        existing_axes.append({"axis_id": axis_id, "kind": axis["kind"], "receivers": axis["receivers"],
                              "axis_point_xyz_mm": connection["source_point_xyz_mm"], "axis_xyz": connection["axis_xyz"],
                              "interfaces": axis["interfaces"], "outer_tie": axis["outer_tie"],
                              "current_force_authority": axis["current_force_authority"],
                              "geometry_reference": ref(model_inputs_path, f"/connections/{ci}"),
                              "register_reference": source_ref("register", f"/axes/{i}"),
                              "force_record_indices": list(range(len(receiver_forces), len(receiver_forces) + 6)),
                              "changed_geometry_force_acceptance_transferred": False})
        for case in CASES:
            si, state = states[case]
            receiver_forces.append({"axis_id": axis_id, "case_id": case, "receivers": axis["receivers"],
                                    "allocation_kind": "existing_receiver_force_record",
                                    "saved_register_allocation": state,
                                    "original_integrated_frame_allocation": state.get("integrated_frame_allocation", state),
                                    "register_reference": source_ref("register", f"/axes/{i}/per_state/{si}"),
                                    "original_force_envelope_reused": True,
                                    "changed_geometry_force_acceptance_transferred": False})

    # Resolve aliases by the explicit body and local station, then validate all
    # global geometry. No alias is inferred by replacing or parsing an ID string.
    axes = geometry["added_stock_bolt_axes"]
    require(len(axes) == len({axis["axis_id"] for axis in axes}) == 4, "new canonical axis census differs")
    stacks = setup["stacks"]
    require(len(stacks) == 4, "fit stack census differs")
    aliases, internal_axes, matched_stacks = [], [], set()
    for ai, axis in enumerate(axes):
        body = axis["body"]
        require(body in BODIES and axis["proposal_only"] is True, "invalid proposal axis")
        grain, u, v = axis["center_local_guv_mm"]
        require(v == 0 and u == 0 and grain in (100, 250), "new station differs")
        matches = [(i, stack) for i, stack in enumerate(stacks)
                   if stack["proposed_bore"]["block"] == body and stack["local_center_grain_u_mm"] == [grain, u]]
        require(len(matches) == 1, f"ambiguous or missing body/station alias: {axis['axis_id']}")
        si, stack = matches[0]
        require(si not in matched_stacks, "fit stack used twice")
        matched_stacks.add(si)
        seats = unique(axis["end_seats"], "end_v_sign", "end seat")
        require(set(seats) == {-1, 1}, "expected opposite v end seats")
        negative, positive = seats[-1][1], seats[1][1]
        proposal = normal["geometry_proposals"][body]
        geom = proposal["hypothetical_geometry"]
        basis = geom["grain_frame_rows_xyz"]
        world_center = [geom["start_xyz_mm"][j] + sum(axis["center_local_guv_mm"][k] * basis[k][j] for k in range(3))
                        for j in range(3)]
        close(axis["center_global_xyz_mm"], world_center, "canonical local/global center differs")
        close(axis["axis_unit_global_xyz"], basis[2], "canonical axis/grain frame differs")
        close(axis["axis_unit_global_xyz"], stack["nut_direction_global_xyz"], "fit axis direction differs")
        close(axis["axis_unit_global_xyz"], stack["proposed_bore"]["axis_direction_to_nut_xyz"], "fit bore direction differs")
        close(axis["center_global_xyz_mm"], stack["proposed_bore"]["center_xyz_mm"], "fit global center differs")
        close(axis["center_local_guv_mm"], stack["proposed_bore"]["center_local_guv_mm"], "fit local center differs")
        close(axis["axis_origin_global_xyz_mm"], negative["center_xyz_mm"], "canonical origin/end seat differs")
        close(negative["center_xyz_mm"], stack["head_wood_face_xyz_mm"], "head seat differs")
        close(positive["center_xyz_mm"], stack["nut_wood_face_xyz_mm"], "nut seat differs")
        close(negative["center_xyz_mm"], stack["proposed_bore"]["axis_start_xyz_mm"], "bore start differs")
        close(positive["center_xyz_mm"], stack["proposed_bore"]["axis_end_xyz_mm"], "bore end differs")
        close([axis["bore_envelope_diameter_mm"]], [stack["proposed_bore"]["proposed_bore_diameter_mm"]], "bore diameter differs")
        for sign, (_, seat) in seats.items():
            close(seat["center_local_guv_mm"], [grain, u, sign * geom["width_depth_mm"][1] / 2], "local seat differs")
            world_seat = [geom["start_xyz_mm"][j] + sum(seat["center_local_guv_mm"][k] * basis[k][j] for k in range(3))
                          for j in range(3)]
            close(seat["center_xyz_mm"], world_seat, "local/global seat differs")
            close(seat["outward_unit_xyz"], [sign * x for x in axis["axis_unit_global_xyz"]], "seat outward direction differs")
        normal_axes = [(i, row) for i, row in enumerate(proposal["new_axes"])
                       if [row["station_mm"], row["transverse_center_mm"]] == [grain, u]]
        require(len(normal_axes) == 1 and normal_axes[0][1]["axis_id"] == axis["axis_id"], "mechanical canonical ID differs")
        normal_index, normal_axis = normal_axes[0]
        require(normal_axis["removed_interval_axis"] == 1, "normal bridge direction differs")
        close([2 * normal_axis["radius_mm"]], [axis["bore_envelope_diameter_mm"]], "normal bore differs")
        for sign, (_, seat) in seats.items():
            lands = [land for land in proposal["washer_lands"]
                     if land["axis_id"] == normal_axis["axis_id"] and land["end_v_sign"] == sign]
            require(len(lands) == 1, "normal end land missing")
            close(lands[0]["seat_center_xyz_mm"], seat["center_xyz_mm"], "normal end seat differs")
        alias = {"canonical_axis_id": axis["axis_id"], "fit_axis_id": stack["axis_id"], "order_axis_id": stack["axis_id"],
                 "body": body, "local_center_grain_u_mm": [grain, u],
                 "center_global_xyz_mm": axis["center_global_xyz_mm"], "axis_unit_global_xyz": axis["axis_unit_global_xyz"],
                 "end_seats": axis["end_seats"], "normal_bolt_index_one_based": normal_index + 1,
                 "geometry_reference": source_ref("geometry", f"/added_stock_bolt_axes/{ai}"),
                 "fit_reference": source_ref("fit_setup", f"/stacks/{si}")}
        aliases.append(alias)
        internal_axes.append({**axis, "canonical_axis_id": axis["axis_id"], "fit_axis_id": stack["axis_id"],
                              "order_axis_id": stack["axis_id"], "kind": "proposed_internal_axial_bolt",
                              "receivers": [body], "receiver_interfaces": [], "same_body_end_pair": True,
                              "global_operator_row": None, "normal_bolt_index_one_based": normal_index + 1})
    require(len({(row["body"], tuple(row["local_center_grain_u_mm"])) for row in aliases}) == 4,
            "duplicate canonical body/station")
    require(len({row["fit_axis_id"] for row in aliases}) == 4 and len(set(order["new_bolt_axis_ids"])) == 4
            and set(order["new_bolt_axis_ids"]) == {row["fit_axis_id"] for row in aliases}, "order alias coverage differs")
    require(set(old_axes).isdisjoint(axis["axis_id"] for axis in internal_axes), "old/new axis collision")

    state_map = {(row["block"], row["case_id"]): (i, row) for i, row in enumerate(normal["states"])}
    require(len(state_map) == len(normal["states"]) == 12
            and set(state_map) == {(body, case) for body in BODIES for case in CASES}, "normal state census differs")
    allocations = []
    for axis in internal_axes:
        for case in CASES:
            ni, state = state_map[axis["body"], case]
            candidates = [(i, row) for i, row in enumerate(state["candidates"]) if row["uniform_case_force_margin"] == 1.25]
            require(len(candidates) == 1, "declared 1.25 allocation missing or ambiguous")
            ci, allocation = candidates[0]
            bi = axis["normal_bolt_index_one_based"] - 1
            require(len(allocation["constant_axial_ties_n"]) == 2, "normal tie census differs")
            tension = allocation["constant_axial_ties_n"][bi]
            require(math.isfinite(tension) and tension >= 0, "invalid declared axial tension")
            comparisons = [row for row in allocation["axial_stack_reference_comparisons"] if row["proposed_bolt_index"] == bi + 1]
            require(len(comparisons) == 1 and comparisons[0]["axial_tension_n"] == tension, "declared T binding differs")
            direction = [Fraction(str(x)) for x in axis["axis_unit_global_xyz"]]
            require(sum(x * x for x in direction) == 1, "canonical axis is not exactly unit length")
            points = [[Fraction(str(x)) for x in seat["center_xyz_mm"]] for seat in axis["end_seats"]]
            delta = [points[1][j] - points[0][j] for j in range(3)]
            require(cross(delta, direction) == [0, 0, 0], "canonical end seats are not exactly coaxial")
            ends, total = [], [Fraction(0) for _ in range(6)]
            for seat, point in zip(axis["end_seats"], points):
                force = [-seat["end_v_sign"] * Fraction(str(tension)) * x for x in direction]
                wrench = force + cross(point, force)
                total = [a + b for a, b in zip(total, wrench)]
                ends.append({"body": axis["body"], "end_v_sign": seat["end_v_sign"],
                             "center_xyz_mm": seat["center_xyz_mm"], "force_on_body_xyz_n": [float(x) for x in force],
                             "wrench_about_global_origin_n_nmm": [float(x) for x in wrench],
                             "exact_wrench_rational_n_nmm": [str(x) for x in wrench]})
            require(total == [0] * 6, "internal axial end pair does not exactly cancel")
            allocations.append({"axis_id": axis["axis_id"], "canonical_axis_id": axis["axis_id"],
                                "fit_axis_id": axis["fit_axis_id"], "order_axis_id": axis["order_axis_id"],
                                "body": axis["body"], "case_id": case, "allocation_kind": "proposed_internal_axial_allocation",
                                "declared_T_n": tension, "uniform_case_force_margin": 1.25, "ends": ends,
                                "whole_body_wrench_n_nmm": [0] * 6, "exact_whole_body_wrench_cancellation": True,
                                "normal_source": source_ref("normal", f"/states/{ni}/candidates/{ci}/constant_axial_ties_n/{bi}"),
                                "exact_arithmetic": "Fractions of the canonical JSON decimal coordinates, direction and declared T",
                                "scope": "Rigid whole-body axial pair only; no receiver reaction, lateral capacity or displacement solution."})

    planning_counts = {kind: sum(row["quantity_required"] for row in order[field]) for kind, field in (
        ("bolts", "bolt_order_lines"), ("nuts", "nut_order_lines"), ("washers", "washer_order_lines"))}
    require(planning_counts == {name: PROPOSED_COUNTS[name] for name in planning_counts}, "planning order totals differ")
    require(order["new_stock_family_count"] == 1 and order["global_gravity_adopted"] is False, "planning order scope differs")
    close([order["mass_planning_convention"]["net_mass_delta_kg"]], [0.24795882906138145], "planning gravity delta differs", 1e-12)
    require(order["mass_planning_convention"]["frozen_modeled_frame_mass_kg"] == model["modeled_mass_kg"], "frozen mass differs")
    require(len(receiver_forces) == 624 and len(allocations) == 24 and sum(len(row["ends"]) for row in allocations) == 48,
            "force/end census differs")
    census = {"current": CURRENT_COUNTS, "proposal": PROPOSED_COUNTS,
              "existing_receiver_bolt_axes": 104, "new_internal_bolt_axes": 4,
              "total_unique_proposal_bolt_axes": len(existing_axes) + len(internal_axes),
              "existing_receiver_force_records": len(receiver_forces), "proposed_internal_T_records": len(allocations),
              "proposed_internal_end_records": 48, "ordinary_receiver_interfaces_added": 0,
              "geometry_body_count": len(effective_members), "modified_STEP_overrides": len(overrides),
              "connector_block_bodies_unchanged": 24, "retained_frame_bolt_axes_unchanged": 12,
              "Hillman_axes_unchanged": len(screws), "planning_order_totals": planning_counts}
    require(census["total_unique_proposal_bolt_axes"] == 108 and len(overrides) == 2, "integrated census differs")
    authenticate()
    source_hashes = {key(path): expected for path, expected in sorted(pins.items())}
    inputs = {"schema": "knee-bridge-integration-inputs/v1", "source_sha256": source_hashes,
              "frozen_sources": {name: source_ref(name) for name in FROZEN},
              "inherited_source_sha256_provenance_only": {name: data[name].get("source_sha256", {}) for name in schemas},
              "inherited_source_closures_rehashed": False, "source_authentication_before_after": True,
              "geometry_coordinate_comparison_tolerance_mm": 1e-6, "rigid_cancellation_tolerance": "exact zero", **FLAGS}
    manifest = {"schema": "knee-bridge-unadopted-integration/v1", "status": "UNADOPTED_INTEGRATION_PREPARED",
                "candidate": register["candidate"], "source_revision": register["source_revision"],
                "development_revision": register["development_revision"], "case_ids": list(CASES), **FLAGS,
                "source_sha256": source_hashes, "producer_sha256": pins[Path(__file__).resolve()], "census": census,
                "frame_authority_unchanged": register["frame_authority"],
                "operators_unchanged": ref(operators), "model_inputs_unchanged": ref(model_inputs_path),
                "source_load_identity": normal["source_load_identity"], "source_frame_assumptions": normal["source_frame_assumptions"],
                "source_gravity_multiplier": normal["source_gravity_multiplier"],
                "original_H_D_e_W_and_force_bytes_unchanged": True,
                "authority": {"criteria_reference": ref(ROOT / "docs/wood-joints-mvp/criteria.json"),
                              "pending_criteria_count": 47, "release_flags_unchanged": candidate["release_flags"],
                              "files_unchanged": [ref(path) for path in authority_paths]},
                "geometry": {"current_scene_reference": source_ref("fit_setup", "/obstacles"),
                             "effective_members": effective_members, "STEP_overrides": overrides,
                             "geometry_used_for_new_global_operator": False},
                "existing_bolt_axes": existing_axes, "proposed_internal_bolt_axes": internal_axes, "axis_aliases": aliases,
                "existing_receiver_forces": {"file": "existing-receiver-forces.jsonl", "record_count": 624,
                                             "scope": "Unchanged saved register allocations and original integrated comparisons; no changed-geometry acceptance."},
                "proposed_internal_allocations": {"file": "proposed-internal-allocations.jsonl", "record_count": 24, "end_count": 48},
                "Hillman_panel_kicker_screws": {"source": source_ref("register", "/panel_kicker_screws"),
                                              "axis_ids": list(screws), "purchased_policy_unchanged": True,
                                              "owner_authorized_screw_movements": register["owner_authorized_screw_movements"]},
                "planning_order": {"source": source_ref("order"), "counts": order["proposed_counts"],
                                   "new_bolt_axis_ids_canonical": [row["canonical_axis_id"] for row in aliases],
                                   "new_bolt_axis_ids_as_saved": order["new_bolt_axis_ids"], "new_stock_family_count": 1},
                "mass_planning_convention": order["mass_planning_convention"],
                "net_mass_delta_kg_not_fed_to_global": order["mass_planning_convention"]["net_mass_delta_kg"],
                "rigid_wrench_proof": {"exact_zero_pairs": 24, "force_and_moment_about_global_origin": [0] * 6,
                                       "scope": "Each canonical end pair separately cancels on its single whole body at declared case T. This identity does not update elastic operators, gravity, compatibility or acceptance."}}
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "inputs.json", inputs)
    for filename, records in (("existing-receiver-forces.jsonl", receiver_forces), ("proposed-internal-allocations.jsonl", allocations)):
        with (output / filename).open("w") as stream:
            for record in records:
                stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
    manifest["existing_receiver_forces"]["sha256"] = sha(output / "existing-receiver-forces.jsonl")
    manifest["proposed_internal_allocations"]["sha256"] = sha(output / "proposed-internal-allocations.jsonl")
    dump(output / "manifest.json", manifest)
    authenticate()
    require(sha(output / "producer.py.snapshot") == pins[Path(__file__).resolve()], "producer snapshot differs")
    files = (".gitignore", "producer.py.snapshot", "inputs.json", "manifest.json",
             "existing-receiver-forces.jsonl", "proposed-internal-allocations.jsonl")
    output_hashes = {name: sha(output / name) for name in files}
    dump(output / "receipt.json", {"schema": "knee-bridge-integration-receipt/v1", "status": manifest["status"],
                                   "source_sha256": source_hashes, "output_sha256": output_hashes,
                                   "sources_authenticated_before_and_after": True, "authority_files_unchanged": True,
                                   "census": census, "exact_whole_body_cancellation_pairs": 24, **FLAGS})
    authenticate()
    for name, expected in output_hashes.items():
        require(sha(output / name) == expected, f"receipt-bound output changed: {name}")
    return {"status": manifest["status"], "output": str(output), "manifest_sha256": output_hashes["manifest.json"],
            "receipt_sha256": sha(output / "receipt.json"), "census": census, **FLAGS}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), sort_keys=True, allow_nan=False))
