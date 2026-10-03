"""First-order local corner mechanics with independently recovered timber forces.

Preserve frozen frame wrenches and contact laws. Omit geometric shortening
and preload stiffness consistently; add no compensating moment to the wood.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/corner-first-order"
PINS = {
    HERE
    / "upper-right-rail-pair.py": "4243b53bbb7377753f0b1fdd73fa1aa6c80e1a96c99d428def88e82a899e6f96",
    HERE
    / "upper-right-side-pair.py": "ce07e9489d96fb251ee780ecb96cdbb38539b5d204922a74c39066095d9ac0cc",
    HERE
    / "upper-left-block.py": "7b07b3f575b7c7cac6dc69dfef83b02ec06c8bac5990ebf1a58f74e807498f6f",
    HERE
    / "rawlocal/upper-right-rail-pair/attempt01/checks.json": "e0cccb56abb94ed16c322da888cd64a9904c4e49d1e34f573a6903c8b8b98d3d",
    HERE
    / "rawlocal/upper-right-side-pair/attempt01/checks.json": "b507a5a501737c89814a471eee6a12749a3c54224f5444b2c5d583020e875ba7",
    HERE
    / "rawlocal/upper-right-block/attempt01/checks.json": "0b0b392b9e5e411173395671878c09e0be303abd4885f48d1e7e7b61d8f6a89b",
    HERE
    / "rawlocal/upper-left-block/attempt01/checks.json": "5e8c52e529f58f9276c4c67f554fa0b74a990dd501e347e59434aa244e628ed0",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "missing frozen helper")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed consumed input: " + str(path))


def merge(pins, additions):
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, "conflicting source binding")
        pins[path] = digest


def prepare(pins):
    groups = []
    rail = module(HERE / "upper-right-rail-pair.py", "first_order_right_rail")
    helper, bolts, face, n, basis, sources, _datum, _centroid, sources_pins = (
        rail.load_sources()
    )
    merge(pins, sources_pins)
    blocks, cells = rail.model_matrices(helper, bolts, face, n, basis)
    groups.append(
        ("right", rail, helper, blocks, cells, n, basis, sources, dict(rail.FAMILY))
    )
    side = module(HERE / "upper-right-side-pair.py", "first_order_right_side")
    (
        mechanics,
        helper,
        bolts,
        face,
        n,
        basis,
        sources,
        _datum,
        _centroid,
        sources_pins,
    ) = side.load_sources()
    merge(pins, sources_pins)
    blocks, cells = mechanics.model_matrices(helper, bolts, face, n, basis)
    groups.append(
        (
            "right",
            mechanics,
            helper,
            blocks,
            cells,
            n,
            basis,
            sources,
            dict(mechanics.FAMILY),
        )
    )
    left = module(HERE / "upper-left-block.py", "first_order_left_source")
    merge(pins, left.source_pins())
    inputs = [
        read(path) for path in (left.MODEL, left.ROWS, left.COMPARISON, left.COMPONENT)
    ]
    for definition in left.HOSTS:
        template = module(left.RAIL_PAIR, "first_order_left_" + definition["key"])
        data = left.configure_group(definition, *inputs)
        mechanics, helper, blocks, cells = left.configure_mechanics(template, data)
        groups.append(
            (
                "left",
                mechanics,
                helper,
                blocks,
                cells,
                data["n"],
                data["basis"],
                data["sources"],
                dict(data["family"]),
            )
        )
    # The only mechanical change: the same zero matrix is used by axial
    # elimination, shortening, energy, gradient and Hessian in every group.
    for group in groups:
        for block in group[3]:
            block["geometric"] = np.zeros_like(block["geometric"])
    return groups


def cantilever_coupon(helper, family):
    elastic, _geometric, _samples, _curvatures, inertia = helper.beam_model(family, 0.0)
    stiffness = elastic[:34, :34]
    load = np.zeros(34)
    load[-2] = 10.0
    pose = np.zeros(34)
    pose[2:] = np.linalg.solve(stiffness[2:, 2:], load[2:])
    length = family["host_length_mm"] + family["cleat_length_mm"]
    rigidity = helper.E_BOLT * inertia
    expected = np.array(
        [10 * length**3 / (3 * rigidity), 10 * length**2 / (2 * rigidity)]
    )
    actual = np.array([pose[-2], pose[-1] / length])
    relative_error = float(np.max(abs(actual / expected - 1)))
    reaction = stiffness @ pose - load
    require(relative_error < 1e-8, "cantilever displacement/rotation coupon failed")
    require(
        abs(reaction[0] + 10) < 1e-7 and abs(length * reaction[1] + 10 * length) < 1e-5,
        "cantilever reaction coupon failed",
    )
    return {
        "force_n": 10,
        "length_mm": length,
        "expected_tip_mm_rad": expected.tolist(),
        "returned_tip_mm_rad": actual.tolist(),
        "relative_error": relative_error,
        "root_force_n_moment_nmm": [float(reaction[0]), float(length * reaction[1])],
    }


def physical_actions(traction, helper, mechanics, geometry, n, basis, state):
    cleat, host = [], []
    seat_records = []
    for bolt in state["bolts"]:
        require(
            bolt["projected_shortening_mm"] == 0.0,
            "preload shortening leaked into first-order response",
        )
        point = np.array(bolt["interface_point_xyz_mm"])
        for field in bolt["bore_fields"]:
            where = point + (field["x_mm"] - geometry["host_length_mm"]) * n
            item = traction.action(
                "bore_station_resultant",
                bolt["axis_id"],
                where,
                -np.array(field["force_on_beam_xyz_n"]),
                receiver=field["receiver"],
            )
            (host if field["receiver"] == "host" else cleat).append(item)
        for end, target in ((0, host), (1, cleat)):
            actions, record = traction.wood_seat(
                helper, bolt, end, geometry, n, basis, mechanics.KWOOD
            )
            target.extend(actions)
            seat_records.append(record)
    for field in state["face_cells"]:
        force = field["compression_n"] * n
        cleat.append(
            traction.action("face_cell", field["row_id"], field["point_xyz_mm"], force)
        )
        host.append(
            traction.action("face_cell", field["row_id"], field["point_xyz_mm"], -force)
        )
    returned = traction.wrench(host, mechanics.DATUM)
    source = np.array(state["source_connector_wrench_on_host_n_nmm"])
    residual = returned - source
    require(
        np.max(abs(residual[:3])) <= mechanics.FORCE_TOLERANCE
        and np.max(abs(residual[3:])) <= mechanics.MOMENT_TOLERANCE,
        "independent physical host wrench does not balance source",
    )
    return cleat, host, seat_records, residual


def run(args):
    require(
        args.output.resolve().is_relative_to(RAW) and not args.output.exists(),
        "use a fresh owned output child",
    )
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    pins[HERE / "cleat-traction.py"] = args.traction_producer_sha256
    authenticate(pins)
    traction = module(HERE / "cleat-traction.py", "first_order_traction_recovery")
    groups = prepare(pins)
    authenticate(pins)
    coupons = [cantilever_coupon(group[2], group[-1]) for group in groups]
    args.output.mkdir(parents=True)
    (args.output / ".gitignore").write_text("*\n")
    (args.output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    originals = {
        side: read(HERE / f"rawlocal/upper-{side}-block/attempt01/checks.json")
        for side in ("right", "left")
    }
    cases = groups[0][1].CASES
    states, failure = [], None
    try:
        for case_index, case_id in enumerate(cases):
            for side in ("right", "left"):
                previous = originals[side]
                datum = np.array(
                    previous["common_datum_xyz_mm"]
                    if side == "right"
                    else previous["model"]["common_cleat_datum_xyz_mm"]
                )
                applied = previous["states"][case_index]
                weight = np.array(
                    applied["applied_weight_wrench_n_nmm"]
                    if side == "right"
                    else applied["whole_cleat"][
                        "current_W_cleat_applied_wrench_at_common_datum_n_nmm"
                    ]
                )
                hosts, actions = {}, []
                for group in (g for g in groups if g[0] == side):
                    _, mechanics, helper, blocks, cells, n, basis, sources, geometry = (
                        group
                    )
                    source = next(s for s in sources if s["case_id"] == case_id)
                    debug = {}
                    state, _beam_fields = mechanics.solve_case(
                        helper, blocks, cells, n, basis, source, debug
                    )
                    cleat, host, seats, residual = physical_actions(
                        traction, helper, mechanics, geometry, n, basis, state
                    )
                    hosts[mechanics.HOST] = {
                        "state": state,
                        "geometry": geometry,
                        "host_interface_datum_xyz_mm": mechanics.DATUM.tolist(),
                        "physical_host_residual_n_nmm": residual.tolist(),
                        "wood_seat_recovery": seats,
                        "physical_host_actions": host,
                    }
                    actions.extend(cleat)
                closure = traction.wrench(actions, datum) + weight
                require(
                    np.max(abs(closure[:3])) < 0.002 and np.max(abs(closure[3:])) < 0.4,
                    "independent whole-cleat forces and moments do not balance",
                )
                states.append(
                    {
                        "case_id": case_id,
                        "side": side,
                        "common_datum_xyz_mm": datum.tolist(),
                        "current_weight_once_n_nmm": weight.tolist(),
                        "hosts": hosts,
                        "physical_cleat_actions": actions,
                        "physical_whole_cleat_residual_n_nmm": closure.tolist(),
                    }
                )
    except (ValueError, RuntimeError, np.linalg.LinAlgError) as error:
        failure = {
            "case_id": case_id,
            "side": side,
            "host": mechanics.HOST,
            "error": str(error),
            "last_accepted_iteration": debug,
            "physical_failure_claimed": False,
        }
    authenticate(pins)
    result = {
        "schema": "first_order_corner_independent_traction/v1",
        "status": "COMPLETE_FIRST_ORDER_LOCAL_FORCES" if failure is None else "STOP",
        "failure": failure,
        "cantilever_coupons": coupons,
        "states": states,
        "geometric_shortening_and_preload_stiffness": False,
        "frame_response_changed": False,
        "material_or_contact_laws_changed": False,
        "balancing_free_couples_added": 0,
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "limits": [
            "First-order reference-geometry equilibrium; finite rotation, prestress stiffening and second-order force geometry are omitted together.",
            "The source six-case frame remains frozen; local redistribution does not feed back into the integrated frame.",
            "Rigid cleat/host, hypothetical K20 bore/seat contacts, rigid concentric washers and smooth elastic bolts remain explicit assumptions.",
            "Nonunique returned poses are representatives, not motion bounds or tangent stability acceptance.",
            "This is local force compatibility and independent traction recovery, not timber group/splitting, washer metal, delivered hardware resistance or physical release.",
        ],
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    (args.output / "checks.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "completed_block_states": len(states),
                "checks_sha256": sha(args.output / "checks.json"),
                "failure": None if failure is None else failure["error"],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--traction-producer-sha256", required=True)
    run(parser.parse_args())
