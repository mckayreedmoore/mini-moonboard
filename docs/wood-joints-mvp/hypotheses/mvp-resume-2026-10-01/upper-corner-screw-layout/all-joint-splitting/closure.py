"""Bind all joint sides and locate unresolved transverse opening paths.

Parent owns execution. Existing cleat arithmetic is reused without a rerun.
Receiver cuts retain the archived point forces, free couples and mapped gravity.
The gross stock hull supplies a necessary normal-transfer lower bound only;
it is not a pressure witness, timber resistance or hardware allocation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from itertools import pairwise
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPPER = HERE.parent
PACKET = UPPER.parent
ROOT = next(
    path for path in HERE.parents if (path / "current-candidate.json").is_file()
)
MEMBER_DIR = PACKET / "member-screen-attempt02/four-screw-layout01"
REGISTER = UPPER / "rawlocal/working-joint-register/attempt03/register.json"
GEOMETRY = MEMBER_DIR / "geometry.json"
ARRAYS = MEMBER_DIR / "action-section-arrays.npz"
MEMBERS = MEMBER_DIR / "member-results.json"
TWENTY = UPPER / "rawlocal/remaining-block-transverse/attempt01/checks.json"
BOTTOM = UPPER / "rawlocal/corner-physical-gravity/grain-attempt02/checks.json"
CORNER = UPPER / "rawlocal/corner-split-closure/normal-census-attempt01/checks.json"
PRESSURE = UPPER / "rawlocal/corner-split-closure/finite-pressure-attempt01/checks.json"
PROPOSAL = UPPER / "rawlocal/knee-bridge-working-package/attempt02/manifest.json"
BRIDGE = UPPER / "rawlocal/knee-bridge-joint-replay/attempt01/checks.json"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    REGISTER: "c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c",
    GEOMETRY: "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    ARRAYS: "ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf",
    MEMBERS: "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    TWENTY: "f3118804d3a03df66d274d783ca93248757ac3d629de4a874d23e85da9a61f19",
    BOTTOM: "e11c2c469c6ef8a8582f5117231d72cfa148c0780de2e5e0ef9fb8365c2492db",
    CORNER: "49f7c143d5a7cda5ff0f3ac8e9ef8d1d8fdf8d8090db4a31f6090c346cf7e75f",
    PRESSURE: "5676849306531c7b506990a5f82e82558f371afadcf7c2dc90bbe24d15c1655c",
    PROPOSAL: "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0",
    BRIDGE: "71980f983dd3466d02eb6c5f838186de4b77dc2ebe04653f66cf3f3598fbe891",
    REGISTER.with_name(
        "receipt.json"
    ): "026fe56a606e453a16faa94aecb4a9302c30ed970260e587ac36061e0104279b",
    TWENTY.with_name(
        "receipt.json"
    ): "dce3437a105cdd269aec9ff98ac831c00d6e64e34a807c42254030ca4fffb519",
    BOTTOM.with_name(
        "receipt.json"
    ): "9f89a14231101cf4c09dd7ae6adc431b43b6f8f39fd90ad049e1ad3aaeba3b68",
    CORNER.with_name(
        "receipt.json"
    ): "aec19f2255d7be94f29d7f4b0d77efae1345063bf39357cb1ddc19b1477b830d",
    PRESSURE.with_name(
        "receipt.json"
    ): "a8188869edbf53fb683b7d733ceb57ab5bf1f02dbbc23e8a0e8e98ff12815aec",
    PROPOSAL.with_name(
        "receipt.json"
    ): "5fa8cc849e4a2fa042a1cffa6d2957d4163597c7999dbcef1f57563dfdd83e7b",
    BRIDGE.with_name(
        "receipt.json"
    ): "10503afef20c8fc69c0f5b4877f8deb2794646c258b05ca63616611443c6c22b",
}
FLAGS = {
    "splitting_resistance_established": False,
    "existing_host_redistribution_solved": False,
    "hardware_reserve_credited": False,
    "installation_preload_credited": False,
    "interface_friction_credited": False,
    "elastic_compatibility_solved": False,
    "complete_joint_acceptance": False,
    "formal_criterion_acceptance": False,
    "physical_release": False,
    "fabrication_release": False,
    "geometry_changed": False,
    "proposal_adopted": False,
    "native_CAD_or_frame_run": False,
    "tests_or_review_loop_run": False,
}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def key(path):
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(len(digest) == 64, "invalid source digest: " + str(path))
    require(
        path not in pins or pins[path] == digest, "conflicting digest: " + str(path)
    )
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed frozen source: " + str(path))


def receipt_sources(pins, path):
    receipt = read(path)
    for relative, digest in receipt["source_sha256"].items():
        bind(pins, ROOT / relative, digest)
    for relative, digest in receipt["output_sha256"].items():
        output = (path.parent / relative).resolve()
        require(output.is_relative_to(path.parent), "receipt output leaves packet")
        bind(pins, output, digest)


def crossing_axes(body, axis, geometry, axes):
    """List geometry candidates; no existing force is credited again."""
    import numpy as np

    normal = np.asarray(
        geometry[body]["geometry"][("axis", "section_u", "section_v")[axis]]
    )
    result = []
    for index, item in enumerate(axes):
        tie = item["outer_tie"]
        receivers = (tie["first_body"], tie["second_body"])
        if body not in receivers:
            continue
        direction = np.asarray(tie["direction_global_xyz"])
        direction /= np.linalg.norm(direction)
        cosine = abs(float(normal @ direction))
        if cosine < 1 - 1e-8:
            continue
        result.append(
            {
                "axis_id": item["axis_id"],
                "other_receiver": receivers[1]
                if receivers[0] == body
                else receivers[0],
                "normal_alignment_abs_cosine": cosine,
                "outer_tie": tie,
                "existing_simultaneous_ties": [
                    {
                        "case_id": state["case_id"],
                        "signed_tie_n": state["single_axial_tie_n"],
                        "force_authority": state["force_authority"],
                    }
                    for state in item["per_state"]
                ],
                "full_simultaneous_state_reference": {
                    "source": key(REGISTER),
                    "sha256": PINS[REGISTER],
                    "record_pointer": f"/axes/{index}/per_state",
                },
                "route_status": "EXISTING_BOLT_HOST_CONTACT_ROUTE_NOT_ESTABLISHED",
                "two_ends_on_this_body": False,
                "spare_tension_or_capacity_credited_n": None,
            }
        )
    return result


def cleat_states():
    twenty, bottom, corner, pressure = (
        read(path) for path in (TWENTY, BOTTOM, CORNER, PRESSURE)
    )
    require(
        not twenty["affected_scope_stops"] and twenty["evaluated_body_count"] == 20,
        "remaining twenty packet incomplete",
    )
    result = []
    for state in twenty["states"]:
        if state["axis"] == 0:
            continue
        result.append(
            {
                "body": state["block"],
                "case_id": state["case_id"],
                "axis": state["axis"],
                "cut_count": state["cut_count"],
                "positive_normal_lower_bound_count": state[
                    "positive_normal_tensile_bound_count"
                ],
                "normal_peak": state["normal_peak"],
                "finite_pressure_count": state["finite_pressure_count"],
                "finite_pressure_above_reference_count": state[
                    "finite_pressure_above_reference_count"
                ],
                "finite_pressure_missing_count": state[
                    "no_finite_pressure_construction_count"
                ],
                "pressure_peak": state["pressure_peak"],
                "source": key(TWENTY),
                "source_placement": "ORIGINAL_FRAME_MECHANICAL_POINTS_PHYSICAL_TIMBER_GRAVITY",
            }
        )
    pressure_map = {
        (s["block"], s["case_id"], s["axis"]): s for s in pressure["states"]
    }
    for packet, source in ((corner, CORNER), (bottom, BOTTOM)):
        for state in packet["states"]:
            if state["axis"] not in (1, 2):
                continue
            body = state["block"]
            if source == CORNER and not body.startswith("top_outer_"):
                continue
            witness = state["maximum_normal_tensile_bound_witness"]
            if source == CORNER:
                finite = pressure_map[(body, state["case_id"], state["axis"])]
                count = state["cut_limit_count"]
                positive = state["positive_normal_tensile_bound_count"]
                finite_count = finite["count_by_status"].get(
                    "FINITE_COMPRESSION_BAND_WITNESS", 0
                )
                missing = finite["count_by_status"].get(
                    "NO_FINITE_SUPPORTED_BAND_WITNESS", 0
                )
                pressure_peak = finite["maximum_pressure_witness"]
                above = finite["finite_pressure_above_reference_count"]
            else:
                count = state["cut_count"]
                positive = state["positive_normal_tensile_bound_count"]
                finite_count = state["finite_pressure_count"]
                missing = count - positive - finite_count
                # This packet records pressure envelopes globally, not by state.
                # Never attach a different state's pressure peak to this state.
                pressure_peak = None
                require(
                    bottom["maximum_finite_pressure_witness"]["finite_band_pressure"][
                        "pressure_peak_mpa"
                    ]
                    <= pressure["conditional_Fc_perpendicular_reference_mpa"],
                    "bottom pressure envelope exceeds its recorded reference",
                )
                above = 0
            result.append(
                {
                    "body": body,
                    "case_id": state["case_id"],
                    "axis": state["axis"],
                    "cut_count": count,
                    "positive_normal_lower_bound_count": positive,
                    "normal_peak": witness,
                    "finite_pressure_count": finite_count,
                    "finite_pressure_missing_count": missing,
                    "pressure_peak": pressure_peak,
                    "finite_pressure_above_reference_count": above,
                    "source": key(source),
                    "source_placement": "FIRST_ORDER_CORNER_TRANSFER_"
                    + (
                        "MAPPED_TOP_GRAVITY"
                        if source == CORNER
                        else "PHYSICAL_BOTTOM_GRAVITY"
                    ),
                }
            )
    require(len(result) == 24 * 6 * 2, "24 cleat transverse state census differs")
    require(len({s["body"] for s in result}) == 24, "24 cleat body census differs")
    require(
        len({(s["body"], s["case_id"], s["axis"]) for s in result}) == len(result),
        "duplicate cleat state",
    )
    return result


def normal_lower_bound(q, bounds):
    """Exact normal-resultant hull bound on a SUPERSET of retained wood."""
    n, _, _, _, mp, mq = q
    (plo, phi), (qlo, qhi) = bounds
    cp, cq = (plo + phi) / 2, (qlo + qhi) / 2
    hp, hq = (phi - plo) / 2, (qhi - qlo) / 2
    require(hp > 0 and hq > 0, "degenerate gross support hull")
    normalized = [n, (-mq - cp * n) / hp, (mp - cq * n) / hq]
    tensile = max(0.0, (max(map(abs, normalized)) + n) / 2)
    return {
        "minimum_tensile_normal_resultant_n": tensile,
        "normal_resultant_and_centered_moment_over_halfwidth_n": normalized,
        "gross_hull_bounds_pq_mm": bounds,
        "retained_material_pressure_witness": None,
        "splitting_resistance_n": None,
        "zero_is_only_gross_hull_feasibility": True,
    }


def receiver_states(np, records, frame_ids, archive, stream):
    """Finite original-point cuts for ALL receiver bodies, without a solve."""
    result = []
    for body in sorted(frame_ids):
        record = records[body]
        geometry = record["geometry"]
        basis = np.asarray([geometry[k] for k in ("axis", "section_u", "section_v")])
        require(
            np.max(abs(basis @ basis.T - np.eye(3))) < 1e-8
            and abs(float(np.linalg.det(basis)) - 1) < 1e-8,
            "invalid timber frame: " + body,
        )
        start = np.asarray(geometry["start"])
        length = float(basis[0] @ (np.asarray(geometry["end"]) - start))
        bounds = [
            [0.0, length],
            [-geometry["width_mm"] / 2, geometry["width_mm"] / 2],
            [-geometry["depth_mm"] / 2, geometry["depth_mm"] / 2],
        ]
        points = (archive[body + "__point_xyz_mm"] - start) @ basis.T
        require(
            points.shape == (len(record["point_action_ids"]), 3),
            "point inventory differs: " + body,
        )
        for case in CASES:
            values = archive[case + "__" + body + "__point_force_free_couple_xyz"]
            require(
                values.shape == (len(points), 6) and np.isfinite(values).all(),
                "invalid source actions",
            )
            forces = values[:, :3] @ basis.T
            moments = np.cross(points, forces) + values[:, 3:] @ basis.T
            whole = np.r_[forces.sum(axis=0), moments.sum(axis=0)]
            require(
                np.max(abs(whole[:3])) < 1e-5 and np.max(abs(whole[3:])) < 0.01,
                "original whole-body source imbalance: " + body + "/" + case,
            )
            for axis in (1, 2):
                lo, hi = bounds[axis]
                positions = sorted(
                    {
                        lo + 1e-4,
                        hi - 1e-4,
                        0.0,
                        *[
                            float(s)
                            for s in points[:, axis]
                            if lo + 1e-5 < s < hi - 1e-5
                        ],
                    }
                )
                stations = sorted(
                    set(positions + [(a + b) / 2 for a, b in pairwise(positions)])
                )
                perm = [axis, (axis + 1) % 3, (axis + 2) % 3]
                state = {
                    "body": body,
                    "case_id": case,
                    "axis": axis,
                    "cut_count": 0,
                    "positive_normal_lower_bound_count": 0,
                    "normal_peak": None,
                    "whole_original_point_wrench_local_guv_n_nmm": whole.tolist(),
                    "source": key(ARRAYS),
                    "retained_pressure_witness_available": False,
                    "source_placement": "ORIGINAL_FRAME_POINTS_FREE_COUPLES_AND_MAPPED_GRAVITY",
                }
                for station in stations:
                    for limit in ("before", "after"):
                        select = (
                            points[:, axis] < station - 1e-9
                            if limit == "before"
                            else points[:, axis] <= station + 1e-9
                        )
                        f = -forces[select].sum(axis=0)
                        origin_moment = -moments[select].sum(axis=0)
                        datum = np.eye(3)[axis] * station
                        m = origin_moment - np.cross(datum, f)
                        q = np.r_[f[perm], m[perm]].tolist()
                        normal = normal_lower_bound(q, [bounds[i] for i in perm[1:]])
                        witness = {
                            "body": body,
                            "case_id": case,
                            "axis": axis,
                            "station_mm": station,
                            "limit": limit,
                            "signed_internal_n_nmm": q,
                            "normal_hull": normal,
                        }
                        stream.write(json.dumps(witness, allow_nan=False) + "\n")
                        state["cut_count"] += 1
                        tensile = normal["minimum_tensile_normal_resultant_n"]
                        state["positive_normal_lower_bound_count"] += tensile > 1e-9
                        if state["normal_peak"] is None or tensile > peak_tension(
                            state["normal_peak"]
                        ):
                            state["normal_peak"] = witness
                result.append(state)
    require(len(result) == 20 * 6 * 2, "20 receiver transverse state census differs")
    return result


def peak_tension(witness):
    return witness.get("normal_hull", witness)["minimum_tensile_normal_resultant_n"]


def build(output):
    """Return finite all-joint demand/path disposition; parent executes once."""
    import numpy as np

    output = Path(output).resolve()
    require(
        output.is_relative_to(HERE / "rawlocal") and not output.exists(),
        "fresh owned rawlocal child required",
    )
    pins = dict(PINS)
    for path in list(pins):
        if path.name == "receipt.json":
            receipt_sources(pins, path)
    for path in (MEMBERS, PROPOSAL, BRIDGE):
        for relative, digest in read(path)["source_sha256"].items():
            bind(pins, ROOT / relative, digest)
    authenticate(pins)
    register, geometry, members = (read(path) for path in (REGISTER, GEOMETRY, MEMBERS))
    records = geometry["members"]
    blocks = {b["block_id"] for b in register["blocks"]}
    frame_ids = set(records) - blocks
    require(
        len(blocks) == 24 and len(frame_ids) == 20 and len(records) == 44,
        "44 timber partition differs",
    )
    require(
        tuple(register["case_ids"]) == CASES
        and tuple(c["case_id"] for c in members["cases"]) == CASES,
        "six case identity differs",
    )
    require(
        register["accounting"]["total_unique_frame_bolt_axes"] == 104
        and len(register["axes"]) == 104
        and len(register["retained_frame_bolt_arrangements"]) == 6,
        "104-axis / six-retained-pair authority differs",
    )
    for body, record in records.items():
        bind(
            pins,
            ROOT / record["current_finished_step"],
            record["current_finished_step_sha256"],
        )
        require(body == record["geometry"]["name"], "body/geometry identity differs")
    states = cleat_states()
    require(
        all(
            state["finite_pressure_missing_count"] == 0
            and state["finite_pressure_above_reference_count"] == 0
            for state in states
        ),
        "a retained cleat pressure construction is missing or exceeds its reference",
    )
    authenticate(pins)
    digest = sha(Path(__file__))
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n!.gitignore\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    require(
        {s["body"] for s in states} == blocks,
        "saved cleat census differs from register",
    )
    with (
        np.load(ARRAYS, allow_pickle=False) as archive,
        (output / "receiver-cuts.jsonl").open("w") as stream,
    ):
        states.extend(receiver_states(np, records, frame_ids, archive, stream))
    require(len(states) == 44 * 6 * 2, "all timber/case/orientation coverage differs")
    body_records = {}
    for body in sorted(records):
        by_axis = []
        for axis in (1, 2):
            own = [s for s in states if s["body"] == body and s["axis"] == axis]
            require({s["case_id"] for s in own} == set(CASES), "body lacks six cases")
            peak = max((s["normal_peak"] for s in own), key=peak_tension)
            crossing = crossing_axes(body, axis, records, register["axes"])
            positive = peak_tension(peak) > 1e-9
            by_axis.append(
                {
                    "axis": axis,
                    "axis_name": ("g", "u", "v")[axis],
                    "normal_peak": peak,
                    "cut_count": sum(s["cut_count"] for s in own),
                    "positive_normal_lower_bound_count": sum(
                        s["positive_normal_lower_bound_count"] for s in own
                    ),
                    "existing_crossing_bolt_candidates": crossing,
                    "opening_path_disposition": (
                        "POSITIVE_OPENING_NO_PARALLEL_EXISTING_BOLT"
                        if not crossing
                        else "POSITIVE_OPENING_EXISTING_HOST_ROUTE_UNPROVEN"
                    )
                    if positive
                    else (
                        "FINITE_NORMAL_COMPRESSION_WITNESSES_REUSED"
                        if body in blocks
                        else "NO_POSITIVE_GROSS_HULL_BOUND_NOT_A_PRESSURE_PASS"
                    ),
                    "splitting_resistance_n": None,
                    "remaining_basis": [
                        "Any changed bolt/contact allocation must balance each host and cleat's full simultaneous wrench.",
                        "Normal compression witnesses do not establish tangential shear, torque or local fracture resistance.",
                        "Bolt tension and washer mean bearing are separate from short-block anchorage/pull-through resistance.",
                    ],
                }
            )
        body_records[body] = {
            "kind": "cleat" if body in blocks else "frame_receiver",
            "transverse": by_axis,
        }
    joints = []
    for block in register["blocks"]:
        receivers = sorted(
            {
                r
                for interface in block["receiver_interfaces"]
                for r in interface["receivers"]
            }
        )
        require(
            block["block_id"] in receivers and set(receivers).issubset(records),
            "block receiver census differs",
        )
        joints.append(
            {
                "joint_id": block["block_id"],
                "kind": "block_duty",
                "timber_sides": receivers,
                "physical_axis_ids": block["candidate_axis_ids"],
                "case_ids": list(CASES),
                "splitting_resistance_n": None,
                "complete_joint_acceptance": False,
            }
        )
    for pair in register["retained_frame_bolt_arrangements"]:
        require(
            set(pair["receivers"]).issubset(frame_ids), "retained pair receivers differ"
        )
        joints.append(
            {
                "joint_id": pair["arrangement_id"],
                "kind": "retained_pair",
                "timber_sides": pair["receivers"],
                "physical_axis_ids": pair["physical_axis_ids"],
                "case_ids": list(CASES),
                "splitting_resistance_n": None,
                "complete_joint_acceptance": False,
            }
        )
    require(
        len(joints) == 30 and len({j["joint_id"] for j in joints}) == 30,
        "30 joint-duty census differs",
    )
    require(
        set(records).issubset({b for j in joints for b in j["timber_sides"]}),
        "timber side missing from duties",
    )
    bridge, proposal = read(BRIDGE), read(PROPOSAL)
    require(
        not bridge["proposal_adopted"]
        and not proposal["proposal_adopted"]
        and not bridge["complete_joint_acceptance"],
        "proposal authority/disposition changed",
    )
    result = {
        "schema": "all-joint-splitting-path-disposition/v1",
        "status": "ALL_JOINT_SIDES_ASSESSED_SPLITTING_RESISTANCE_UNRESOLVED",
        "reviewed_authority": {
            "bolt_axes": 104,
            "panel_kicker_screws": 66,
            "cases": list(CASES),
            "frame_source": key(UPPER / "frame-250-attempt02"),
            "register": key(REGISTER),
        },
        "coverage": {
            "block_duties": 24,
            "retained_pair_duties": 6,
            "joint_duties": 30,
            "timber_bodies": 44,
            "frame_receivers": 20,
            "body_case_orientation_states": len(states),
            "cleat_cut_count_reused": sum(
                s["cut_count"] for s in states if s["body"] in blocks
            ),
            "receiver_original_point_cut_count": sum(
                s["cut_count"] for s in states if s["body"] in frame_ids
            ),
        },
        "opening_path_counts": dict(
            Counter(
                a["opening_path_disposition"]
                for b in body_records.values()
                for a in b["transverse"]
            )
        ),
        "bodies": body_records,
        "joint_duties": joints,
        "states": states,
        "unadopted_108_axis_proposal": {
            "manifest": key(PROPOSAL),
            "manifest_sha256": PINS[PROPOSAL],
            "normal_transfer_source": key(BRIDGE),
            "normal_cut_count": bridge["normal_cut_count"],
            "grain_cut_count": bridge["grain_cut_count"],
            "finite_reference_screens_satisfied": bridge[
                "all_named_reference_screens_satisfied"
            ],
            "scope": "TWO_OUTER_VERTICAL_KNEE_CLEATS_NOT_REAR_LEG_RUNNER_JOINTS",
            "proposal_adopted": False,
            "complete_joint_acceptance": False,
        },
        "limits": [
            "The 104-axis and 108-axis forces, geometry and inventories are distinct.",
            "Receiver demands retain original mapped gravity, mechanical points and free couples.",
            "Receiver stock hull is a superset of sound wood; a zero lower bound does not establish a retained-material pressure field.",
            "No continuous-station maximum, local stress field or crack-strength comparison is supplied.",
            "Existing tie actions are already in cuts and cannot be subtracted or reused as spare reinforcement.",
            "Candidate axis alignment supplies no two-ended stitch tie within a timber or supported host reaction route.",
            "Panel timber receiver actions are included; plywood screw-head pull-through remains a different mode.",
            "NDS perpendicular-opening and local-mechanics provisions supply no universal crossed-joint scalar capacity.",
        ],
        **FLAGS,
        "producer_sha256": digest,
        "source_sha256": {key(path): value for path, value in sorted(pins.items())},
    }
    authenticate(pins)
    require(sha(Path(__file__)) == digest, "producer changed during execution")
    write(output / "checks.json", result)
    write(
        output / "receipt.json",
        {
            "source_sha256": result["source_sha256"],
            "output_sha256": {
                p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()
            },
        },
    )
    return {
        "status": result["status"],
        "coverage": result["coverage"],
        "opening_path_counts": result["opening_path_counts"],
        "checks_sha256": sha(output / "checks.json"),
        "receipt_sha256": sha(output / "receipt.json"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2, allow_nan=False))
