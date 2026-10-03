"""Join saved six-case joint forces; parent owns the serialized arithmetic run.

No mechanical producer, constitutive calculation, native solver or CAD runs.
The earlier index remains immutable. Only saved-force joins, vector sums,
wrench shifts and comparisons are performed here.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/working-joint-register"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
KNEE_AXES = {f"knee_outer_{side}_side_{number}" for side in ("left", "right") for number in (1, 2)}
FROZEN = {
    "comparison": ("frame-250-attempt02/comparison.json", "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca"),
    "response": ("frame-250-attempt02/response.npz", "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7"),
    "model": ("operators-attempt02/model.json", "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626"),
    "rows": ("operators-attempt02/row-identities.json", "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27"),
    "index": ("rawlocal/joint-register/attempt01/register.json", "79db8c6830dee42e47dcdcd75c331ce22a67cd3d27e38f9a8b616e820c37d3ca"),
    "index_producer": ("joint_register.py", "c939fd65d340d6c332739525af381b5570290087621fef64e74a8302368c3a6a"),
    "index_snapshot": ("rawlocal/joint-register/attempt01/producer.py.snapshot", "c939fd65d340d6c332739525af381b5570290087621fef64e74a8302368c3a6a"),
    "wrench_helper": ("cleat-traction.py", "2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764"),
    "top": ("rawlocal/corner-first-order/attempt01/checks.json", "b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe"),
    "top_components": ("rawlocal/corner-first-order-components/attempt01/checks.json", "f220673994b6a6c5b6bc0afd104becd61b5bb68f5e22bc700ed07b901b94525c"),
    "top_right": ("rawlocal/upper-right-block/attempt01/checks.json", "0b0b392b9e5e411173395671878c09e0be303abd4885f48d1e7e7b61d8f6a89b"),
    "top_left": ("rawlocal/upper-left-block/attempt01/checks.json", "5e8c52e529f58f9276c4c67f554fa0b74a990dd501e347e59434aa244e628ed0"),
    "bottom": ("rawlocal/bottom-corner-transfer/first-order-attempt01/checks.json", "4d255ba5ebd8f1f93fb41ef90511eb3da49906f4729f33f5f63766e0a0bd78ed"),
    "bottom_components": ("rawlocal/bottom-corner-components/attempt01/checks.json", "39e698d7ffec6646e2295f5ce96be0764ea8fbe6654ed3b0e881040b410bcc95"),
    "bottom_boundary": ("rawlocal/bottom-corner-transfer/preparation-attempt02/readiness.json", "e8ca5bbcb38747bb2641928da5927ab9698cf079574ced37dc391903a4b8ec25"),
    "knee": ("rawlocal/knee-contact-entry/suite-attempt01/suite.json", "b707952e5ad740ad2ebc0306bce17a37e4718e88c1164cba568d9a39a6e8b79a"),
    "knee_receipt": ("rawlocal/knee-contact-entry/suite-attempt01/receipt.json", "63224d7d4e25bd8705123f75dc60663f6b4fcb8ab998d149ed2507ec79ee5e43"),
    "knee_boundary": ("rawlocal/knee-compatible/prepare-attempt02/input-contract.json", "f2876952e6b71d59acdbf20dacaef233444402e50bfcc6d3b9ec1967f2cad01f"),
    "knee_historical_suite": ("rawlocal/knee-compatible-suite/suite-attempt01/suite.json", "0d7dff18b38d82130be212b1fc53fbb18a97c0e6f0c3a8c4a13e58fa3375910f"),
    "knee_historical_receipt": ("rawlocal/knee-compatible-suite/suite-attempt01/receipt.json", "3180d95e9b7f146da7bc2dce40ec3d88c10b6152e3da9f06b70e11a9226187f1"),
    "knee_selected_receipt": ("rawlocal/knee-compatible/witness-attempt01/receipt.json", "7088673c7e3b1afa78e2a53438bff9e9f475444f1014a7fc018329156df2eb27"),
    "header": ("rawlocal/header-traction-map/attempt01/result.json", "39d63b41dc495659b02cb4ff4fb638a19a491bc09e6ea3fd76a70314db08a837"),
    "header_receipt": ("rawlocal/header-traction-map/attempt01/receipt.json", "1d454a949640a9b43d6ae3e3cf56ca20705e12ff6ae06f9bb51c1749623d96fd"),
    "header_boundary": ("rawlocal/header-local-transfer/attempt01/inputs.json", "cccd8969132c30e996fe5d3509069dbe851720786cec92a46a064cc0f7c0758b"),
    "nominal_header": ("rawlocal/header-net-section/attempt01/checks.json", "f582f87a45b80e9f95b5344bad289ce9837d4088135b21fc26c15dfc3e1d462d"),
    "nominal_header_receipt": ("rawlocal/header-net-section/attempt01/receipt.json", "dbb35782f1e028459ec6b13877f98d242e7cbb5e80d2de6df0a2c57e4e96c988"),
    "central": ("rawlocal/central-seat-transfer/coupon-attempt01/coupon.json", "bdc35b60ca03039f6e5acad8c5c81784086368a3472183ae7515f66335fe41bb"),
    "central_boundary": ("rawlocal/central-seat-transfer/preparation-attempt01/contract.json", "e430c138f0e1fb4eacda278fa535d3e14400fcff3514f4a81d3a5f7fc3ac6646"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def label(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def close(actual: Any, expected: Any, message: str, tolerance: float = 1e-7) -> None:
    first, second = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    require(first.shape == second.shape and np.isfinite(first).all() and np.isfinite(second).all()
            and np.max(np.abs(first - second), initial=0) <= tolerance, message)


def module(path: Path, name: str) -> Any:
    # Import only the authenticated, side-effect-free definitions; never main/build.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"missing saved helper: {path}")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def build_register(*, producer_sha256: str) -> tuple[dict[str, Any], dict[Path, str]]:
    """Return the joined register and direct pins without writing or solving.

    This function performs the parent-owned saved-action arithmetic. Call it
    once after freezing this producer; do not call earlier mechanical producers.
    """
    pins: dict[Path, str] = {}

    def pin(path: Path, expected: str) -> None:
        path = path.resolve()
        require(path.is_relative_to(ROOT), f"direct source leaves repository: {path}")
        require(path not in pins or pins[path] == expected, f"conflicting source pin: {path}")
        require(digest(path) == expected, f"changed consumed source: {path}")
        pins[path] = expected

    pin(Path(__file__), producer_sha256)
    for relative, expected in FROZEN.values():
        pin(HERE / relative, expected)
    data = {name: json.loads((HERE / relative).read_text())
            for name, (relative, _) in FROZEN.items() if relative.endswith(".json")}
    helper = module(HERE / FROZEN["wrench_helper"][0], "working_register_saved_wrenches")
    index, model, rows = data["index"], data["model"], data["rows"]
    comparison = data["comparison"]

    def ref(name: str, pointer: str) -> dict[str, Any]:
        relative, expected = FROZEN[name]
        return {"source": label(HERE / relative), "sha256": expected, "record_pointer": pointer}

    def ordered(records: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[tuple[Any, ...], tuple[int, dict[str, Any]]]:
        mapped = {}
        for number, record in enumerate(records):
            key = tuple(record[field] for field in keys)
            require(key not in mapped, f"duplicate join identity: {key}")
            require(record["case_id"] in CASES, f"unexpected case: {key}")
            mapped[key] = (number, record)
        return mapped

    def old_reference(reference: dict[str, Any]) -> dict[str, Any]:
        path = (HERE.parent / reference["source"]).resolve()
        source = label(path)
        expected = index["source_sha256"].get(source)
        require(expected is not None, f"old method has no consumed-source pin: {source}")
        pin(path, expected)
        return {**copy.deepcopy(reference), "source": source, "sha256": expected,
                "force_allocation_scope": "original_integrated_frame"}

    require(index["case_ids"] == CASES, "six-case index identity differs")
    for field in ("candidate", "source_revision", "development_revision"):
        require(index[field] == model[field], f"model/index authority differs: {field}")
    require(comparison["response_sha256"] == FROZEN["response"][1], "frame response receipt differs")
    require([state["case_id"] for state in comparison["states"] if state["gap_scale"] == 1.0] == CASES,
            "original nominal cases differ")
    require(index["same_state_force_source"]["comparison_sha256"] == FROZEN["comparison"][1]
            and index["same_state_force_source"]["response_sha256"] == FROZEN["response"][1], "old index uses another frame")
    for name, source in data.items():
        if isinstance(source, dict):
            require(not source.get("complete_joint_acceptance", False) and not source.get("physical_release", False),
                    f"source claims acceptance/release: {name}")
    require(len(rows) == 1888 and sorted(row["row"] for row in rows) == list(range(1888)), "row census differs")
    row_map = {row["row"]: row for row in rows}
    axes = {axis["axis_id"]: copy.deepcopy(axis) for axis in index["axes"]}
    screws = copy.deepcopy(index["panel_kicker_screws"])
    require(len(axes) == 104 and len(screws) == 66 and len(index["blocks"]) == 24, "physical inventory differs")
    require(sum(axis["kind"] == "candidate_bolt" for axis in axes.values()) == 92
            and sum(axis["kind"] == "retained_bolt" for axis in axes.values()) == 12, "bolt policies differ")
    require(set(index["accounting"]["shared_physical_axes"]) == KNEE_AXES, "continuous shaft inventory differs")
    baseline = {}
    with np.load(HERE / FROZEN["response"][0], allow_pickle=False) as response:
        for axis in [*axes.values(), *screws]:
            axis_id = axis["axis_id"]
            axis["member_evidence"] = [old_reference(reference) for reference in axis["member_evidence"]]
            axis["member_evidence_scope"] = "Original integrated-frame member checks only; no stress field is transferred to a redistributed local bolt/contact allocation."
            require([state["case_id"] for state in axis["per_state"]] == CASES, f"case coverage differs: {axis_id}")
            tie = axis["outer_tie"]
            saved_tie = row_map[tie["row"]]
            require(saved_tie["row_id"] == tie["row_id"] and saved_tie["ownership"] == {
                key: value for key, value in tie.items() if key not in ("row", "row_id")}, f"tie receiver identity differs: {axis_id}")
            for interface in axis["interfaces"]:
                for row_number, direction in zip(interface["component_rows"], interface["component_directions_xyz"], strict=True):
                    row = row_map[row_number]
                    ownership = row["ownership"]
                    require(row["row_id"] == interface["plane_id"] and
                            [ownership["first_body"], ownership["second_body"]] == interface["receivers"], f"plane identity differs: {axis_id}")
                    require(ownership["point_mm"] == interface["point_xyz_mm"] and
                            ownership["direction_global_xyz"] == direction, f"plane station/direction differs: {axis_id}")
            for state in axis["per_state"]:
                case = state["case_id"]
                force = response[case + "_gap_raw_force_n"]
                require(force.shape == (1888,) and np.isfinite(force).all(), f"invalid saved frame force: {case}")
                close(state["outer_tie_signed_n"], force[tie["row"]], f"old tie allocation differs: {case}/{axis_id}")
                require([plane["plane_id"] for plane in state["interfaces"]] ==
                        [plane["plane_id"] for plane in axis["interfaces"]], f"state plane coverage differs: {case}/{axis_id}")
                for plane in state["interfaces"]:
                    close(plane["components_n"], force[plane["component_rows"]], f"old lateral allocation differs: {case}/{axis_id}")
                state["component_references"] = [old_reference(reference) for reference in state["component_references"]]
                baseline[case, axis_id] = copy.deepcopy(state)
                axis["current_force_authority"] = "original_integrated_frame"
                state["force_authority"] = "original_integrated_frame"
                if axis["kind"] == "panel_kicker_screw":
                    state["signed_parametric_withdrawal_n"] = state["outer_tie_signed_n"]
                    state["withdrawal_scope"] = "Saved parametric action only; no qualified Hillman withdrawal or stiffness."
                else:
                    state["single_axial_tie_n"] = state.pop("outer_tie_signed_n")
                state["same_state_stress"] = None
                state["stress_scope"] = "Saved component references only; no new same-position shaft stress field is inferred."
                state["boundary_receipt_ids"] = []

    balances: list[dict[str, Any]] = []

    def balance(lane: str, case: str, receiver: str, datum: Any, original: Any, returned: Any,
                source_reference: dict[str, Any], local_reference: dict[str, Any],
                tolerances: tuple[float, float] = (0.001, 0.2), weight: Any = None) -> str:
        original, returned = np.asarray(original, dtype=float), np.asarray(returned, dtype=float)
        delta = returned - original
        require(original.shape == returned.shape == (6,) and np.isfinite(delta).all(), "invalid group wrench")
        require(np.max(abs(delta[:3])) <= tolerances[0] and np.max(abs(delta[3:])) <= tolerances[1],
                f"corrected interface equilibrium differs: {lane}/{case}/{receiver}")
        record = {"receipt_id": f"{lane}/{case}/{receiver}", "case_id": case, "lane": lane, "receiver": receiver,
                  "datum_xyz_mm": list(datum), "original_integrated_boundary_wrench_n_nmm": original.tolist(),
                  "independently_summed_local_wrench_n_nmm": returned.tolist(), "local_minus_original_n_nmm": delta.tolist(),
                  "force_tolerance_n": tolerances[0], "moment_tolerance_nmm": tolerances[1],
                  "original_source": source_reference, "local_action_source": local_reference,
                  "weight_count": 0, "interface_equilibrium_preserved": True,
                  "displacement_feedback_asserted": False, "global_compatibility_asserted": False}
        if weight is not None:
            weight = np.asarray(weight, dtype=float)
            original_closure, local_closure = original + weight, returned + weight
            for name, residual in (("original", original_closure), ("local", local_closure)):
                require(np.max(abs(residual[:3])) <= tolerances[0] and np.max(abs(residual[3:])) <= tolerances[1],
                        f"{name} whole-cleat weight-once balance differs: {lane}/{case}/{receiver}")
            record.update(weight_count=1, own_weight_once_wrench_n_nmm=weight.tolist(),
                          original_plus_weight_once_n_nmm=original_closure.tolist(), local_plus_weight_once_n_nmm=local_closure.tolist())
        balances.append(record)
        return record["receipt_id"]

    def set_local(case: str, axis_id: str, authority: str, force: dict[str, Any]) -> dict[str, Any]:
        require(axis_id in axes and axes[axis_id]["kind"] == "candidate_bolt", f"unknown corrected physical axis: {axis_id}")
        axis = axes[axis_id]
        state = next(state for state in axis["per_state"] if state["case_id"] == case)
        require(state["force_authority"] == "original_integrated_frame", f"duplicate local allocation: {case}/{axis_id}")
        state.clear()
        state.update(case_id=case, gap_scale=1.0, force_authority=authority,
                     integrated_frame_allocation=baseline[case, axis_id], **force)
        axis["current_force_authority"] = authority
        return state

    corrected: dict[str, set[str]] = {"top": set(), "bottom": set(), "knee": set()}
    for lane in ("top", "bottom"):
        source, components = data[lane], data[lane + "_components"]
        require(source["status"] == "COMPLETE_FIRST_ORDER_LOCAL_FORCES" and source["failure"] is None
                and source["frame_response_changed"] is False and source["balancing_free_couples_added"] == 0
                and source["geometric_shortening_and_preload_stiffness"] is False, f"incomplete first-order source: {lane}")
        state_map = ordered(source["states"], ("case_id", "side"))
        component_map = ordered(components["states"], ("case_id", "axis_id"))
        require(set(state_map) == {(case, side) for case in CASES for side in ("left", "right")}, f"missing local block/case: {lane}")
        require(len(component_map) == 48, f"component coverage differs: {lane}")
        for (case, side), (number, group) in state_map.items():
            common = group["common_datum_xyz_mm"]
            cleat = group.get("cleat", f"top_outer_{side}_cleat")
            require(len(group["hosts"]) == 2, "corner must have two host interfaces")
            if lane == "top":
                original_name = "top_" + side
                original = data[original_name]
                original_number, original_state = ordered(original["states"], ("case_id",))[(case,)]
                if side == "right":
                    close(common, original["common_datum_xyz_mm"], "right cleat datum differs")
                    original_cleat = original_state["source_connector_wrench_n_nmm"]
                    original_weight = original_state["applied_weight_wrench_n_nmm"]
                    original_hosts = {entry["host"]: entry for entry in original_state["hosts"]}
                else:
                    close(common, original["model"]["common_cleat_datum_xyz_mm"], "left cleat datum differs")
                    original_cleat = original_state["whole_cleat"]["source_full_cleat_interface_wrench_on_cleat_n_nmm"]
                    original_weight = original_state["whole_cleat"]["current_W_cleat_applied_wrench_at_common_datum_n_nmm"]
                    original_hosts = original_state["whole_cleat"]["host_interfaces"]
                original_reference = ref(original_name, f"/states/{original_number}")
            else:
                prepared = data["bottom_boundary"]
                block = prepared["blocks"][side]
                require(block["cleat"] == cleat, "bottom cleat identity differs")
                close(common, block["common_datum_xyz_mm"], "bottom cleat datum differs")
                original_weight = block["weight_by_case"][case]["wrench_n_nmm"]
                close(helper.wrench(block["weight_by_case"][case]["actions"], common), original_weight,
                      "original bottom weight actions differ", 1e-5)
                close(helper.wrench(group["own_weight_actions_once"], common), original_weight,
                      "current bottom weight actions differ", 1e-5)
                original_cleat = np.zeros(6)
                original_hosts = {}
                for entry in prepared["groups"]:
                    if entry["side"] != side:
                        continue
                    _, boundary = ordered(entry["sources"], ("case_id",))[(case,)]
                    value = helper.shifted(boundary["source_connector_wrench_on_host_n_nmm"], entry["datum_xyz_mm"], common)
                    original_hosts[entry["host"]] = {"source_wrench_n_nmm": value, "datum_xyz_mm": entry["datum_xyz_mm"]}
                    original_cleat -= value
                original_reference = ref("bottom_boundary", f"/blocks/{side}")
            close(group["current_weight_once_n_nmm"], original_weight, "local/source weight differs", 1e-5)
            cleat_receipt = balance(lane + "_whole_cleat", case, cleat, common, original_cleat,
                                    helper.wrench(group["physical_cleat_actions"], common), original_reference,
                                    ref(lane, f"/states/{number}/physical_cleat_actions"), (0.002, 0.4), original_weight)
            require(set(group["hosts"]) == set(original_hosts), "original/local host identities differ")
            for host, host_group in group["hosts"].items():
                local = host_group["state"]
                require(local["case_id"] == case and len(local["bolts"]) == 2, "host/case/bolt join differs")
                prior = original_hosts[host]
                if lane == "top":
                    original_host = (-np.asarray(prior["source_reaction_on_rigid_cleat_n_nmm"]) if side == "right"
                                     else prior["source_wrench_on_host_at_common_cleat_datum_n_nmm"])
                    datum = host_group["host_interface_datum_xyz_mm"]
                else:
                    original_host, datum = prior["source_wrench_n_nmm"], prior["datum_xyz_mm"]
                close(helper.shifted(local["source_connector_wrench_on_host_n_nmm"], datum, common), original_host,
                      "local boundary differs from original integrated group", 1e-5)
                host_receipt = balance(lane + "_host", case, host + ":" + cleat, common, original_host,
                                       helper.wrench(host_group["physical_host_actions"], common), original_reference,
                                       ref(lane, f"/states/{number}/hosts/{host}/physical_host_actions"))
                for bolt_number, bolt in enumerate(local["bolts"]):
                    axis_id = bolt["axis_id"]
                    require(axis_id in axes and axes[axis_id]["receivers"] == sorted([host, cleat])
                            and axes[axis_id]["block_ids"] == [cleat] and len(axes[axis_id]["interfaces"]) == 1,
                            f"local physical receiver identity differs: {axis_id}")
                    corrected[lane].add(axis_id)
                    component_number, component = component_map[case, axis_id]
                    require(component["host"] == host and component.get("cleat", component.get("block")) == cleat,
                            "component receiver identity differs")
                    old = baseline[case, axis_id]
                    close(bolt["source_original_T_n"], old["outer_tie_signed_n"], "original local tie binding differs")
                    close(bolt["source_original_V_n"], old["interfaces"][0]["V_resultant_n"], "original local plane binding differs")
                    close(bolt["source_original_signed_plane_components_n"], old["interfaces"][0]["components_n"],
                          "original local signed plane binding differs")
                    tension = bolt["compatible_T_n"]
                    shear = component["V_n" if lane == "top" else "shear_n"]
                    force_cleat = component["force_on_cleat_lateral_xyz_n" if lane == "top" else "shear_xyz_on_cleat_n"]
                    close(tension, component["T_n" if lane == "top" else "tension_n"], "same-state component tie differs")
                    close(shear, bolt["bore_V_resultant_n"], "same-state component plane differs")
                    close(force_cleat, -np.asarray(bolt["bore_force_on_host_xyz_n"]), "signed local bore resultant differs")
                    close(bolt["peak_stress_witness"]["nominal_smooth_von_mises_proxy_mpa"],
                          component["smooth_bolt_VM_mpa"] if lane == "top" else
                          component["smooth_bolt_stress_witness"]["nominal_smooth_von_mises_proxy_mpa"],
                          "saved stress/component state differs")
                    interface = axes[axis_id]["interfaces"][0]
                    first = np.asarray(force_cleat) * (1 if interface["receivers"][0] == cleat else -1)
                    seats = []
                    for seat_number, seat in enumerate(host_group["wood_seat_recovery"]):
                        if seat["axis_id"] != axis_id:
                            continue
                        member = seat.get("member", host if seat["end"].startswith("host_") else cleat)
                        require(member in (host, cleat), "local end receiver differs")
                        close(seat["T_n"], tension, "end record duplicates a differing tie")
                        seats.append({"member": member, "end": seat["end"], "single_tie_n": tension,
                                      "point_xyz_mm": seat["nominal_outer_wood_seat_xyz_mm"],
                                      "pressure_wrench_about_own_seat_n_nmm": seat["recovered_force_and_own_pressure_moment_at_seat_n_nmm"],
                                      "saved_pressure_reference": ref(lane, f"/states/{number}/hosts/{host}/wood_seat_recovery/{seat_number}")})
                    require(len(seats) == 2 and {seat["member"] for seat in seats} == {host, cleat}, "two outer ends must share one tie")
                    local_pointer = f"/states/{number}/hosts/{host}/state/bolts/{bolt_number}"
                    set_local(case, axis_id, lane + "_first_order", {
                        "single_axial_tie_n": tension, "outer_tie_row_identity_only": axes[axis_id]["outer_tie"],
                        "interfaces": [{"plane_id": interface["plane_id"], "receivers": interface["receivers"],
                                        "force_on_first_xyz_n": first.tolist(), "force_on_second_xyz_n": (-first).tolist(),
                                        "V_resultant_n": shear, "force_kind": "recovered_receiver_bore_resultant",
                                        "point_xyz_mm": interface["point_xyz_mm"],
                                        "scope": "Integrated bore force for this two-receiver interface; end pressure moments are recorded separately."}],
                        "outer_seats": seats, "same_state_stress": bolt["peak_stress_witness"],
                        "stress_scope": "Saved same-state, same-position smooth-section diagnostic; no thread-root or actual hardware acceptance.",
                        "component_references": [{**ref(lane + "_components", f"/states/{component_number}"), "values": component}],
                        "local_force_reference": ref(lane, local_pointer), "boundary_receipt_ids": [host_receipt, cleat_receipt]})
        require(len(corrected[lane]) == 8 and set(component_map) == {(case, axis) for case in CASES for axis in corrected[lane]},
                f"eight-axis/all-case join incomplete: {lane}")

    contract = data["knee_boundary"]
    boundary_map = ordered(contract["boundaries"], ("case_id", "axis_id"))
    knee_map = ordered(data["knee"]["states"], ("case_id", "axis_id"))
    require(set(knee_map) == set(boundary_map) == {(case, axis) for case in CASES for axis in KNEE_AXES}, "knee all-24 join differs")
    require(data["knee"]["status"] == "conditional_first_order_equilibrium_all24", "knee suite incomplete")
    suite, receipt = data["knee"], data["knee_receipt"]
    historical, historical_receipt = data["knee_historical_suite"], data["knee_historical_receipt"]
    selected_receipt = data["knee_selected_receipt"]
    historical_map = ordered(historical["states"], ("case_id", "axis_id"))
    require(set(historical_map) == set(boundary_map), "historical knee case/axis coverage differs")
    require(suite["schema"] == "knee_contact_entry_finite_suite/v1" and
            historical["schema"] == "knee_compatible_finite_suite/v1" and
            contract["schema"] == "knee_three_receiver_first_order_contract/v1", "knee provenance schemas differ")
    require(suite["original_model"] == historical["original_model"] == contract["model"], "knee suite input model differs")
    require(receipt["mode"] == historical_receipt["mode"] == selected_receipt["mode"] == "run"
            and receipt["status"] == suite["status"] and historical_receipt["status"] == historical["status"],
            "knee execution receipt status differs")
    require(receipt["output_sha256"]["suite.json"] == FROZEN["knee"][1] and
            historical_receipt["output_sha256"]["suite.json"] == FROZEN["knee_historical_suite"][1],
            "knee suite output binding differs")
    require(receipt["source_receipts"] == historical_receipt["source_receipts"] == historical["source_receipts"],
            "current/historical knee source receipts differ")
    sources = receipt["source_receipts"]
    require(sources["input_contract"]["path"] == label(HERE / FROZEN["knee_boundary"][0]) and
            sources["input_contract"]["sha256"] == FROZEN["knee_boundary"][1], "knee receipt input contract differs")
    for source in sources.values():
        pin(ROOT / source["path"], source["sha256"])
    for source_path, source_sha in receipt["source_sha256"].items():
        pin(ROOT / source_path, source_sha)
    for name in ("knee_historical_suite", "knee_historical_receipt"):
        require(receipt["source_sha256"][label(HERE / FROZEN[name][0])] == FROZEN[name][1],
                f"contact-entry historical source binding differs: {name}")
    require(sources["selected_receipt"]["path"] == label(HERE / FROZEN["knee_selected_receipt"][0]) and
            sources["selected_receipt"]["sha256"] == FROZEN["knee_selected_receipt"][1], "original selected receipt binding differs")
    require(selected_receipt["source_receipts"] == contract["source_receipts"], "selected witness source inputs differ")
    for name, source in contract["source_receipts"].items():
        require(sources["upstream/" + name] == source, f"knee source input differs: {name}")
    for name in ("comparison", "response", "model", "rows"):
        source = contract["source_receipts"][name]
        require(source["path"] == label(HERE / FROZEN[name][0]) and source["sha256"] == FROZEN[name][1],
                f"knee input is outside the original frame: {name}")
    original_producer = contract["producer_sha256"]
    contact_producer = suite["producer_sha256"]
    adapter_producer = historical["adapter_sha256"]
    require(sources["original_producer"]["sha256"] == historical_receipt["original_producer_sha256"] ==
            selected_receipt["producer_sha256"] == original_producer, "knee original producer binding differs")
    require(selected_receipt["input_contract_sha256"] == FROZEN["knee_boundary"][1], "selected witness input contract differs")
    require(receipt["producer_sha256"] == receipt["output_sha256"]["producer.py.snapshot"] == contact_producer,
            "contact-entry producer binding differs")
    require(historical_receipt["adapter_sha256"] == historical_receipt["output_sha256"]["executed-adapter.py"] == adapter_producer
            and receipt["source_sha256"][label(HERE / "knee-compatible-suite.py")] == adapter_producer,
            "historical adapter producer binding differs")
    require(selected_receipt["output_sha256"]["executed-producer.py"] == original_producer,
            "selected original producer snapshot differs")
    pin(HERE / Path(FROZEN["knee"][0]).parent / "producer.py.snapshot", contact_producer)
    pin(HERE / Path(FROZEN["knee_historical_suite"][0]).parent / "executed-adapter.py", adapter_producer)
    pin(HERE / Path(FROZEN["knee_selected_receipt"][0]).parent / "executed-producer.py", original_producer)
    coupon_path = ROOT / receipt["argv"][receipt["argv"].index("--coupon") + 1]
    pin(coupon_path, suite["coupon_sha256"])
    coupon = json.loads(coupon_path.read_text())
    require(coupon["status"] == "matched" and coupon["producer_sha256"] == contact_producer,
            "contact-entry coupon producer binding differs")
    provenance_counts = {"contact_entry_receipt": 0, "historical_adapter_result": 0, "original_selected_result": 0}
    pair_wrenches: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for (case, axis_id), (number, entry) in knee_map.items():
        require(entry["independent_reference_equilibrium_closed"] and entry["newton_converged"], "knee physical recovery incomplete")
        path = (ROOT / entry["result_path"]).resolve()
        pin(path, entry["result_sha256"])
        result = json.loads(path.read_text())
        require((result["case_id"], result["axis_id"]) == (case, axis_id), "knee result case/axis differs")
        boundary_number, boundary = boundary_map[case, axis_id]
        historical_number, prior = historical_map[case, axis_id]
        require(number == entry["index"] == boundary_number == historical_number == prior["index"],
                "knee exact suite/input boundary index differs")
        require(result["schema"] == "knee_three_receiver_first_order_witness/v1" and
                result["scope"] == contract["model"] and result["status"] == entry["status"] == "conditional_first_order_equilibrium"
                and result["newton_converged"] and result["independent_reference_equilibrium_closed"] and
                result["defect"] is None and not result["complete_joint_acceptance"] and not result["physical_release"]
                and not result["actual_hardware_or_wood_acceptance"], "knee completed result fields differ")
        require(entry["receivers"] == result["receivers"] and
                entry["physical_recovery_max_residual"] == result["physical_recovery_max_residual"] and
                entry["full_mixed_gradient_max_n"] == result["full_mixed_gradient_max_n"], "knee result/suite recovery fields differ")
        if entry["reused_accepted_witness"]:
            require(prior["independent_reference_equilibrium_closed"] and
                    (entry["result_path"], entry["result_sha256"]) == (prior["result_path"], prior["result_sha256"]),
                    "reused knee result is not the exact accepted historical output")
            require(result["input_contract_sha256"] == FROZEN["knee_boundary"][1] and
                    result["producer_sha256"] == original_producer and result["coupon_sha256"] == sources["coupon"]["sha256"],
                    "historical knee result producer/input/coupon differs")
            if prior["reused_accepted_witness"]:
                variant = "original_selected_result"
                require(path == (ROOT / sources["selected_witness"]["path"]).resolve() and
                        entry["result_sha256"] == sources["selected_witness"]["sha256"] == selected_receipt["output_sha256"][path.name] and
                        selected_receipt["status"] == result["status"],
                        "selected knee result receipt output differs")
                result_receipt = ref("knee_selected_receipt", "/output_sha256/witness.json")
                result_producer = original_producer
                serialization_producer = original_producer
            else:
                variant = "historical_adapter_result"
                require(path == (HERE / Path(FROZEN["knee_historical_suite"][0]).parent / f"state-{number:02d}.json").resolve()
                        and historical_receipt["output_sha256"][path.name] == entry["result_sha256"] and
                        result["suite_adapter_sha256"] == adapter_producer and
                        result["source_boundary_pointer"] == f"input_contract#/boundaries/{boundary_number}",
                        "historical knee adapter result binding differs")
                result_receipt = ref("knee_historical_receipt", f"/output_sha256/{path.name}")
                result_producer = original_producer
                serialization_producer = adapter_producer
        else:
            # These 14 frozen files put hashes in the execution receipt, not
            # in each witness. Authenticate that exact output/input chain.
            variant = "contact_entry_receipt"
            require(not prior["independent_reference_equilibrium_closed"] and
                    path == (HERE / Path(FROZEN["knee"][0]).parent / f"state-{number:02d}.json").resolve() and
                    receipt["output_sha256"][path.name] == entry["result_sha256"] and result["physics_changed"] is False,
                    "contact-entry result is not the exact completed receipt output")
            require("input_contract_sha256" not in result and "producer_sha256" not in result,
                    "contact-entry witness provenance variant differs")
            result_receipt = ref("knee_receipt", f"/output_sha256/{path.name}")
            result_producer = contact_producer
            serialization_producer = contact_producer
        provenance_counts[variant] += 1
        geometry = contract["geometry"][axis_id]
        receiver_order, datum = geometry["receiver_order"], geometry["datum_mm"]
        require(set(receiver_order) == set(axes[axis_id]["receivers"]) and len(receiver_order) == 3
                and [receiver["receiver"] for receiver in result["receivers"]] == receiver_order, "knee physical receivers differ")
        tension = entry["single_physical_tie_n"]
        close(tension, boundary["physical_axial_tie_n"], "knee prescribed tie differs")
        close(tension, baseline[case, axis_id]["outer_tie_signed_n"], "knee/frame tie binding differs")
        close(tension, result["normal_transfer"]["single_physical_tie_n"], "knee result tie differs")
        for plane in boundary["planes"]:
            original_plane = next(item for item in baseline[case, axis_id]["interfaces"] if item["plane_id"] == plane["plane_id"])
            require(original_plane["component_rows"] == plane["raw_rows"], "knee original plane rows differ")
            close(original_plane["components_n"], plane["signed_components_n"], "knee original signed plane allocation differs")
        local_ref = {"source": label(path), "sha256": entry["result_sha256"],
                     "authentication": {"variant": variant, "result_producer_sha256": result_producer,
                                        "serialization_producer_sha256": serialization_producer,
                                        "recorded_result_sha256_fields": {name: result[name] for name in
                                            ("producer_sha256", "input_contract_sha256", "coupon_sha256", "suite_adapter_sha256") if name in result},
                                        "mechanical_core_producer_sha256": original_producer, "output_receipt": result_receipt,
                                        "input_contract": ref("knee_boundary", f"/boundaries/{boundary_number}"),
                                        "suite_entry": ref("knee", f"/states/{number}"),
                                        "input_source_receipts": ref("knee_receipt", "/source_receipts")}}
        bore_resultants, receiver_receipts, seats = {}, [], []
        for receiver in receiver_order:
            fields = [field for field in result["bore_fields"] if field["receiver"] == receiver]
            require(fields, "missing knee receiver bore fields")
            actions = [{"point_xyz_mm": field["reference_point_mm"], "force_xyz_n": field["force_on_wood_xyz_n"]} for field in fields]
            bore_resultants[receiver] = np.sum([action["force_xyz_n"] for action in actions], axis=0)
            for end_number, end in enumerate(result["outer_seat_fields"]):
                if end["receiver"] != receiver:
                    continue
                pressure = end["point_tractions"]["wood_contact"]
                seat_actions = [{"point_xyz_mm": point, "force_xyz_n": force} for point, force in
                                zip(pressure["reference_points_mm"], pressure["point_forces_xyz_n"], strict=True)]
                actions.extend(seat_actions)
                point = geometry[end["end"] + "_seat_point_mm"]
                seats.append({"member": receiver, "end": end["end"], "single_tie_n": tension, "point_xyz_mm": point,
                              "pressure_wrench_about_own_seat_n_nmm": helper.wrench(seat_actions, point).tolist(),
                              "saved_pressure_reference": {**local_ref, "record_pointer": f"/outer_seat_fields/{end_number}"}})
            original = boundary["operator_connector_wrenches_on_receivers"][receiver]
            original_vector = original["force_xyz_n"] + original["moment_xyz_nmm"]
            returned = helper.wrench(actions, datum)
            tolerances = contract["model"]["numerical_tolerances"]
            receipt_id = balance("knee_receiver", case, axis_id + ":" + receiver, datum, original_vector, returned,
                                 ref("knee_boundary", f"/boundaries/{boundary_number}/operator_connector_wrenches_on_receivers/{receiver}"),
                                 local_ref, (tolerances["force_n"], tolerances["moment_nmm"]))
            receiver_receipts.append(receipt_id)
            side = "left" if axis_id.startswith("knee_outer_left_") else "right"
            pair_wrenches.setdefault((case, side, receiver), []).append({"datum": datum, "original": original_vector,
                                                                         "returned": returned, "receipt_id": receipt_id})
        require(len(seats) == 2 and {seat["member"] for seat in seats} == {receiver_order[0], receiver_order[-1]}, "knee middle receiver acquired an outer tie")
        cumulative, planes = np.zeros(3), []
        require(len(axes[axis_id]["interfaces"]) == 2 and len(boundary["planes"]) == 2, "continuous shaft plane census differs")
        for index_number, receiver in enumerate(receiver_order[:-1]):
            cumulative += bore_resultants[receiver]
            plane_source = boundary["planes"][index_number]
            interface = next(plane for plane in axes[axis_id]["interfaces"] if plane["plane_id"] == plane_source["plane_id"])
            require(interface["receivers"] == [plane_source["first_body"], plane_source["second_body"]]
                    and set(interface["receivers"]) == set(receiver_order[index_number:index_number + 2])
                    and interface["component_rows"] == plane_source["raw_rows"], "knee plane identity differs")
            first = cumulative * (1 if interface["receivers"][0] == receiver else -1)
            planes.append({"plane_id": interface["plane_id"], "receivers": interface["receivers"],
                           "point_xyz_mm": interface["point_xyz_mm"], "force_on_first_xyz_n": first.tolist(),
                           "force_on_second_xyz_n": (-first).tolist(), "V_resultant_n": float(np.linalg.norm(first)),
                           "force_kind": "cumulative_saved_bore_force_at_physical_plane",
                           "scope": "Two plane forces on one continuous shaft; middle receiver net bore force is their signed difference."})
        diagnostic = entry["diagnostics"]
        require((diagnostic["case_id"], diagnostic["axis_id"]) == (case, axis_id), "knee stress identity differs")
        close(diagnostic["peak_same_state_same_position_smooth_proxy"]["signed_single_tie_n"], tension, "knee stress/tie state differs")
        set_local(case, axis_id, "knee_contact_entry", {
            "single_axial_tie_n": tension, "outer_tie_row_identity_only": axes[axis_id]["outer_tie"],
            "interfaces": planes, "outer_seats": seats, "receiver_bore_resultants_xyz_n": {member: value.tolist() for member, value in bore_resultants.items()},
            "same_state_stress": diagnostic["peak_same_state_same_position_smooth_proxy"], "stress_scope": diagnostic["stress_scope"],
            "component_references": [{**ref("knee", f"/states/{number}/diagnostics"), "values": diagnostic}],
            "local_force_reference": local_ref, "boundary_receipt_ids": receiver_receipts,
            "shared_knee_body_pose_compatibility_asserted": False})
        corrected["knee"].add(axis_id)
    require(provenance_counts == {"contact_entry_receipt": 14, "historical_adapter_result": 9, "original_selected_result": 1},
            "all-24 knee provenance variant census differs")
    for (case, side, receiver), contributions in pair_wrenches.items():
        require(len(contributions) == 2, "two-shaft receiver group missing")
        datum = contributions[0]["datum"]
        original = sum((helper.shifted(item["original"], item["datum"], datum) for item in contributions), np.zeros(6))
        returned = sum((helper.shifted(item["returned"], item["datum"], datum) for item in contributions), np.zeros(6))
        balance("knee_two_shaft_boundary", case, side + ":" + receiver, datum, original, returned,
                ref("knee_boundary", "/boundaries"), ref("knee", "/states"),
                (2 * contract["model"]["numerical_tolerances"]["force_n"], 2 * contract["model"]["numerical_tolerances"]["moment_nmm"]))
        balances[-1]["summed_receiver_receipt_ids"] = [item["receipt_id"] for item in contributions]
        balances[-1]["scope"] = "The two shaft duties only. Face-contact and body-weight duties stay in the frozen frame; this is not a complete knee-body pose calculation."

    header_map = ordered(data["header"]["cases"], ("case_id",))
    header_boundary_map = ordered(data["header_boundary"]["cases"], ("case_id",))
    require(set(header_map) == set(header_boundary_map) == {(case,) for case in CASES}, "header case join differs")
    header_axes = set(data["header"]["header_seats"])
    require(len(header_axes) == 12 and header_axes <= axes.keys(), "header physical-axis join differs")
    for (case,), (number, entry) in header_map.items():
        boundary_number, boundary = header_boundary_map[case,]
        def header_actions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
            for action in records:
                close(action["free_moment_nmm"], [0, 0, 0], "header action has an unrepresented free couple", 1e-6)
            return [{"point_xyz_mm": action["point_mm"], "force_xyz_n": action["force_n"]} for action in records]
        original = helper.wrench(header_actions(boundary["complete_header_actions"]), entry["datum_xyz_mm"])
        returned = helper.wrench(header_actions(entry["mapped_point_actions"]), entry["datum_xyz_mm"])
        balance("header_supported_boundary", case, "base_header", entry["datum_xyz_mm"], original, returned,
                ref("header_boundary", f"/cases/{boundary_number}/complete_header_actions"),
                ref("header", f"/cases/{number}/mapped_point_actions"), (1e-6, 1e-5))
        balances[-1]["weight_scope"] = "Full saved action inventories include body loads once; no additional weight is applied."
        require(len(entry["header_washer_records"]) == 12 and
                {washer["axis_id"] for washer in entry["header_washer_records"]} == header_axes,
                "header six-case seat coverage differs")
        for washer_number, washer in enumerate(entry["header_washer_records"]):
            axis_id = washer["axis_id"]
            require(axis_id in header_axes and "base_header" in axes[axis_id]["receivers"], "header washer receiver differs")
            state = next(state for state in axes[axis_id]["per_state"] if state["case_id"] == case)
            close(washer["tension_n"], state["single_axial_tie_n"], "header same-state tie differs")
            require(washer["source_row"] == axes[axis_id]["outer_tie"]["row"], "header source tie row differs")
            state["component_references"].append({**ref("header", f"/cases/{number}/header_washer_records/{washer_number}"), "values": washer})
            state["boundary_receipt_ids"].append(balances[-1]["receipt_id"])
    cut_coverage = set()
    require(len(data["nominal_header"]["cuts"]) == 72, "nominal header signed-cut census differs")
    for number, cut in enumerate(data["nominal_header"]["cuts"]):
        require(cut["case_id"] in CASES and set(cut["axis_ids"]) <= header_axes, "nominal header section identity differs")
        for axis_id in cut["axis_ids"]:
            state = next(state for state in axes[axis_id]["per_state"] if state["case_id"] == cut["case_id"])
            state["component_references"].append({**ref("nominal_header", f"/cuts/{number}"),
                                                  "section_plane_id": cut["plane_id"], "trace": cut["trace"],
                                                  "scope": data["nominal_header"]["scope"]})
            cut_coverage.add((cut["case_id"], axis_id))
    require(cut_coverage == {(case, axis) for case in CASES for axis in header_axes}, "nominal header six-case axis coverage differs")
    central, central_boundary = data["central"], data["central_boundary"]
    require(central["status"] == "MATCHED_SIGNED_INTEGRALS" and central["contract_sha256"] == FROZEN["central_boundary"][1], "central coupon binding differs")
    central_map = ordered(central_boundary["states"], ("case_id",))
    coupon_map = ordered(central["states"], ("case_id",))
    require(set(central_map) == set(coupon_map) == {(case,) for case in CASES}, "central six-case join differs")
    axis_id = central_boundary["axis_id"]
    require(axis_id == "center_principal_right_2" and central_boundary["body"] in axes[axis_id]["receivers"], "central receiver identity differs")
    require(axes[axis_id]["outer_tie"]["row"] == 1535, "central physical tie row differs")
    for (case,), (number, entry) in coupon_map.items():
        boundary_number, boundary = central_map[case,]
        state = next(state for state in axes[axis_id]["per_state"] if state["case_id"] == case)
        close(boundary["signed_tie_n"], state["single_axial_tie_n"], "central same-state tie differs")
        receipt_id = balance("central_static_ring", case, central_boundary["body"], central_boundary["seat_point_global_xyz_mm"],
                             boundary["source_tie_wrench_at_seat_Fxyz_N_Mxyz_Nmm"], entry["returned_wrench_n_nmm"],
                             ref("central_boundary", f"/states/{boundary_number}"), ref("central", f"/states/{number}"), (1e-9, 1e-9))
        state["component_references"].extend([{**ref("central_boundary", f"/states/{boundary_number}"), "values": boundary},
                                             {**ref("central", f"/states/{number}"), "values": entry, "scope": central["stress_scope"]}])
        state["boundary_receipt_ids"].append(receipt_id)

    local_axes = set.union(*corrected.values())
    require(len(local_axes) == 20 and sum(map(len, corrected.values())) == 20, "corrected physical shafts overlap")
    require(len(set(axes) - local_axes) == 84, "uncorrected physical axis census differs")
    for axis in axes.values():
        require([state["case_id"] for state in axis["per_state"]] == CASES, "final six-case axis coverage differs")
        axis["method_ids"] = sorted({reference["source"] for state in axis["per_state"] for reference in state["component_references"]})
    blocks = [{key: copy.deepcopy(block[key]) for key in ("block_id", "candidate_axis_ids", "physical_axis_count", "shared_axis_ids", "receiver_interfaces", "unavailable_criteria", "full_joint_status")}
              for block in index["blocks"]]
    for block in blocks:
        block["current_force_authorities"] = sorted({axes[axis]["current_force_authority"] for axis in block["candidate_axis_ids"]})
    register = {
        "schema": "working_six_case_joint_force_register/v1", "status": "COMPLETE_SAVED_FORCE_INTEGRATION",
        "candidate": index["candidate"], "source_revision": index["source_revision"], "development_revision": index["development_revision"],
        "reviewed_geometry_changed": index["reviewed_geometry_changed"],
        "owner_authorized_screw_movements": index["owner_authorized_screw_movements"],
        "case_ids": CASES, "accounting": {**index["accounting"], "corrected_top_axes": 8, "corrected_bottom_axes": 8,
                                           "corrected_continuous_knee_shafts": 4, "current_frame_method_axes": 84},
        "frame_authority": {key: ref(key, "") for key in ("comparison", "response", "model", "rows")},
        "preserved_machine_index": ref("index", ""), "preserved_index_producer": ref("index_producer", ""),
        "axes": list(axes.values()), "blocks": blocks, "panel_kicker_screws": screws,
        "retained_frame_bolt_arrangements": [{key: copy.deepcopy(item[key]) for key in
                                             ("arrangement_id", "physical_axis_ids", "receivers", "unavailable_criteria", "full_joint_status")}
                                            for item in index["retained_frame_bolt_arrangements"]],
        "interface_equilibrium_receipts": balances,
        "knee_provenance_variant_counts": provenance_counts,
        "interface_equilibrium_preserved": True, "displacement_feedback_asserted": False,
        "global_compatibility_asserted": False, "complete_joint_acceptance": False, "physical_release": False,
        "mechanics_recalculated": False, "native_or_CAD_run": False, "tests_or_review_run": False,
        "conventions": {
            "allocation": "The 20 local axes use saved corrected forces. Their integrated_frame_allocation is comparison evidence, never the current local force table. The other 84 axes and 66 separate screw axes retain authenticated original-frame forces/methods.",
            "single_tie": "One axial tie per shaft. End pressure forces and moments are separate distributions carrying that tie; they are not extra ties. Continuous knee shafts have two lateral planes and three receivers.",
            "moments": "Saved pressure actions already carry end rocking moments. No additional free couple is added. Wrenches are summed in reference geometry at their named datums.",
            "stress": "Reuse each saved same-state/same-position smooth stress witness. No maxima from different cases, sections or positions are combined; thread roots and delivered hardware remain unqualified.",
            "equilibrium": "Independent saved-action sums preserve original integrated group/interface boundary wrenches. Cleat weight is counted once. Knee pair checks cover shaft duties only; shared body poses and global displacement compatibility are not established.",
            "provenance": "Direct consumed bytes are rehashed. Earlier producer/source closures, including foreign temporary files and geometry, remain inherited provenance and are not rerun or mutated.",
        },
        "source_records": {name: {**ref(name, ""), "schema": source.get("schema"), "status": source.get("status"),
                                  "limits": source.get("limits", source.get("scope")),
                                  "inherited_source_sha256_provenance_only": source.get("source_sha256", {})}
                           for name, source in data.items() if name not in ("index", "model", "rows", "comparison")},
        "source_sha256": {label(path): expected for path, expected in sorted(pins.items())},
        "producer_sha256": producer_sha256, "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
    }
    for path, expected in pins.items():
        require(digest(path) == expected, f"source changed during integration: {path}")
    return register, pins


def allocation_rows(register: dict[str, Any]) -> list[dict[str, Any]]:
    """Make exact per-plane, per-case old/current allocation rows for the parent."""
    records = []
    for axis in register["axes"]:
        for state in axis["per_state"]:
            old = state.get("integrated_frame_allocation")
            original_planes = {plane["plane_id"]: plane for plane in old["interfaces"]} if old else {}
            for plane in state["interfaces"]:
                prior = original_planes.get(plane["plane_id"], plane)
                prior_tie = old["outer_tie_signed_n"] if old else state["single_axial_tie_n"]
                definition = next(item for item in axis["interfaces"] if item["plane_id"] == plane["plane_id"])
                records.append({"case_id": state["case_id"], "axis_id": axis["axis_id"], "plane_id": plane["plane_id"],
                                "receivers": definition["receivers"], "current_force_authority": state["force_authority"],
                                "original_frame_V_n": prior["V_resultant_n"], "current_plane_V_n": plane["V_resultant_n"],
                                "current_minus_original_V_n": plane["V_resultant_n"] - prior["V_resultant_n"],
                                "original_frame_single_T_n": prior_tie, "current_single_T_n": state["single_axial_tie_n"],
                                "current_minus_original_T_n": state["single_axial_tie_n"] - prior_tie,
                                "original_force_on_first_xyz_n": prior["force_on_first_xyz_n"],
                                "current_force_on_first_xyz_n": plane["force_on_first_xyz_n"],
                                "current_minus_original_force_on_first_xyz_n":
                                    (np.asarray(plane["force_on_first_xyz_n"]) - prior["force_on_first_xyz_n"]).tolist(),
                                "single_tie_identity": axis["outer_tie"]["row_id"],
                                "tie_repeated_per_plane_for_join_only": True,
                                "same_state_stress_witness": state["same_state_stress"],
                                "local_force_reference": state.get("local_force_reference"), "boundary_receipt_ids": state["boundary_receipt_ids"]})
    require(len(records) == 648, "final plane-state census differs")
    return records


def worksheet(register: dict[str, Any], allocations: list[dict[str, Any]]) -> str:
    lines = ["# Working six-case joint force register", "",
             ("Saved local corrections preserve interface equilibrium against the original integrated source boundaries. "
             "This register does not assert displacement feedback or global compatibility. Complete joint acceptance and physical release remain false."), "",
             ("104 physical bolt axes: eight top, eight bottom and four continuous knee shafts use saved local allocations; "
             "84 use current original-frame methods. The 24 blocks and 66 separate Hillman axes remain identified. "
             "Each shaft has one tie; plane forces and end pressure wrenches remain distinct."), "",
             ("The table selects each corrected axis's greatest current plane force and reports its simultaneous original/current tie. "
             "All six exact case allocations, including vector differences, are in allocations.csv. Values are N."), "",
             "| Physical axis | Case / plane | Original V → current V | Same-state original T → current T |",
             "| --- | --- | ---: | ---: |"]
    for axis in register["axes"]:
        if axis["current_force_authority"] == "original_integrated_frame":
            continue
        peak = max((item for item in allocations if item["axis_id"] == axis["axis_id"]), key=lambda item: item["current_plane_V_n"])
        lines.append(f"| `{axis['axis_id']}` | {peak['case_id']} / `{peak['plane_id'].rsplit('/', 1)[-1]}` | "
                     f"{peak['original_frame_V_n']:.6g} → {peak['current_plane_V_n']:.6g} | "
                     f"{peak['original_frame_single_T_n']:.6g} → {peak['current_single_T_n']:.6g} |")
    lines.extend(["", ("Independent accounting uses saved physical bore/seat/face actions, original source group wrenches, "
                  "and explicit datums. End pressure moments are carried by those actions once. "
                  "Top/bottom whole cleat checks add their own saved weight once; knee checks cover the two shaft duties "
                  "and leave other frame/body duties untouched. Header full inventories already contain body loads. "
                  "The central result is the existing static ring coupon."), "",
                  "| Case | Maximum local/source force residual, N | Maximum moment residual, Nmm |",
                  "| --- | ---: | ---: |"])
    for case in CASES:
        receipts = [item for item in register["interface_equilibrium_receipts"] if item["case_id"] == case]
        force = max(abs(value) for item in receipts for value in item["local_minus_original_n_nmm"][:3])
        moment = max(abs(value) for item in receipts for value in item["local_minus_original_n_nmm"][3:])
        lines.append(f"| {case} | {force:.6g} | {moment:.6g} |")
    lines.extend(["", ("Saved same-state stress/component references retain their own local assumptions. "
                  "The nominal header cuts, supported header boundary map and central compression route do not establish "
                  "shared displacements, actual washer/hardware capacity or complete joint resistance."), "",
                  f"Producer SHA-256: `{register['producer_sha256']}`. Exact direct input/output bindings: receipt.json.", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Fresh child of rawlocal/working-joint-register.")
    parser.add_argument("--producer-sha256", required=True, help="Parent-frozen hash of this producer.")
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(RAW) and output != RAW and not output.exists(), "use a fresh owned ignored output child")
    register, pins = build_register(producer_sha256=args.producer_sha256)
    allocations = allocation_rows(register)
    rendered = worksheet(register, allocations)
    # Reuse the existing register's CSV formatting, without calling its producer.
    writer = module(HERE / FROZEN["index_producer"][0], "working_register_saved_csv").write_csv
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    writer(output / "allocations.csv", allocations)
    (output / "worksheet.md").write_text(rendered)
    (output / "register.json").write_text(json.dumps(register, indent=2, sort_keys=True, allow_nan=False) + "\n")
    for path, expected in pins.items():
        require(digest(path) == expected, f"source changed before publication: {path}")
    receipt = {"schema": "working_six_case_joint_force_register_receipt/v1", "status": register["status"],
               "source_sha256": register["source_sha256"], "output_sha256": {path.name: digest(path) for path in sorted(output.iterdir())},
               "source_unchanged_before_and_after_write": True, "producer_sha256": args.producer_sha256,
               "interface_equilibrium_preserved": True, "displacement_feedback_asserted": False,
               "global_compatibility_asserted": False, "complete_joint_acceptance": False, "physical_release": False,
               "mechanics_recalculated": False, "native_or_CAD_run": False, "tests_or_review_run": False}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": register["status"], "register_sha256": digest(output / "register.json"),
                      "receipt_sha256": digest(output / "receipt.json"), "physical_axes": 104, "cases": 6,
                      "plane_states": len(allocations), "output": label(output)}, sort_keys=True))


if __name__ == "__main__":
    main()
