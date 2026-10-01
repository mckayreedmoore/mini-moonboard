#!/usr/bin/env python3
"""Read-only replay for exact zero-SPC DAT displacement precision."""
from __future__ import annotations

import hashlib
import json
import math
import re
import tarfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
CASE = BASE / "current-springa-frame-k12-rear-all-bearing-attempt01"
CASE_SOURCE = CASE / "sources/docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-response-audit-attempt01/response_audit.py"
SOURCE_ARCHIVE = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "implicit-bounded-contact-capture-attempt02/build/context/source.tar.bz2"
)
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
MANIFEST = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "calculix-2.23-upgrade-attempt01/build_manifest.json"
)
SOURCE_FILE_SHA256 = {
    "bounadd.f": "c94911a6ada3cba7fdd35b4d43f2926ec60f6b42a2610e42341f4332adc82659",
    "mastruct.c": "bb695de956e5157e91d4d4ff884426eac02351c9b56c8e295a3635254cd50e52",
    "printoutnode.f": "ed77454fbf771c38ebbb32f0785013dae3585eca50e5cc7b28c646dec0ce4b94",
}
MANUAL = Path("fea/generated/ccx_2.23.pdf")
MANUAL_SHA256 = "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"
PROFILE = Path("fea/calculix_223/solver-profile.json")
PROFILE_SHA256 = "f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c"

FILE_PINS = {
    CASE / "model.inp": "0cdcee16de7be40e8a7a511c26f6cbf67f116d2475f76eab294fa661ee6fac68",
    CASE / "model.json": "72cc39411bb92d3ee739a9b9aa9b025fe466f2b818f29feaa76a26c284366424",
    CASE / "model.dat": "8c3c7590e11df6c8bce52e814ece2aba2f05ff24eb261517e95e74db41528807",
    CASE / "freeze.json": "161e9b8bfecb7ef4d5060db4d6fb25aeeb38df5fa4332a3ba47fbd92df70ac92",
    CASE / "execution.json": "4e10033ba2a12952122ac790ae6c4dcf4a9585b936d239e86d73465be6db6ccc",
    CASE_SOURCE: "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
    MANUAL: MANUAL_SHA256,
    PROFILE: PROFILE_SHA256,
    MANIFEST: "496efd407abd71c8ced12e3631ea2d223dee1fe6ec1b1b757a2e5e28dfb19e66",
}

COUPONS = [
    {
        "name": "current-exact-floor-mpc-fixture-attempt02",
        "model": BASE / "current-exact-floor-mpc-fixture-attempt02/model.json",
        "deck": BASE / "current-exact-floor-mpc-fixture-attempt02/model.inp",
        "dat": BASE / "current-exact-floor-mpc-fixture-attempt02/native/model.dat",
        "parent_check": BASE / "current-exact-floor-mpc-fixture-attempt02/parent-all-increment-check.json",
        "targets": [8],
        "pins": {
            "model.json": "94368165d50627350f1e92b0396e35e07ad794c60161d22016d1444faf54af5f",
            "model.inp": "09689c00090008eccc955f5cf6fa020c73836b4460a38c0f10ae56493f1ce5b7",
            "model.dat": "6b7fce5cfbb6230bca951931917f146a299da75d71f2a5a9fce756d4e6cf3bdc",
            "parent_check": "e06c476ac0ef83e248f725e7adcb8bbffe3f310497ccc5ab018a211de4fac64f",
        },
    },
    {
        "name": "nonlinear-springa-known-answer-attempt01",
        "model": BASE / "nonlinear-springa-known-answer-attempt01/native/model.json",
        "deck": BASE / "nonlinear-springa-known-answer-attempt01/native/model.inp",
        "dat": BASE / "nonlinear-springa-known-answer-attempt01/native/model.dat",
        "parent_check": BASE / "nonlinear-springa-known-answer-attempt01/parent-all-increment-check.json",
        "targets": [3, 5],
        "pins": {
            "model.json": "e8d20960545fb2371212533e90358b67d220f5cec2eb9f6378868a3b66d6843c",
            "model.inp": "29648efb81b2cc6ad44788a107f7138bab3fdc5148171d68c46cca1b7d6bdbfe",
            "model.dat": "0767d6d2687fda99a949cb2e1cdac3b672f01a0eac1e92b0290932131c5ddaa8",
            "parent_check": "3a051a1b36768b383c6be68b3884cc58ab264a488e139467c6879c797e5c470c",
        },
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text())


def half_last_place(token: str) -> float:
    """The pinned response auditor's DAT token radius rule."""
    normalized = token.upper().replace("D", "E")
    if "E" in normalized:
        mantissa, exponent = normalized.split("E", 1)
        exponent_value = int(exponent)
    else:
        mantissa, exponent_value = normalized, 0
    decimal_places = len(mantissa.split(".", 1)[1]) if "." in mantissa else 0
    return 0.5 * 10.0 ** (exponent_value - decimal_places)


def parse_native_blocks(text: str) -> dict[tuple[str, float], dict[int, list[str]]]:
    pattern = re.compile(
        r"^\s*(displacements|forces)\s*\([^\n]*\btime\s+([0-9.EeDd+-]+)\s*\n",
        re.MULTILINE | re.IGNORECASE,
    )
    result: dict[tuple[str, float], dict[int, list[str]]] = {}
    for match in pattern.finditer(text):
        kind = "u" if match.group(1).lower() == "displacements" else "rf"
        time = float(match.group(2).replace("D", "E").replace("d", "e"))
        key = (kind, time)
        require(key not in result, f"duplicate DAT block {key}")
        rows: dict[int, list[str]] = {}
        started = False
        for line in text[match.end():].splitlines():
            if not line.strip():
                if started:
                    break
                continue
            fields = line.split()
            if len(fields) == 4 and fields[0].isdigit():
                node = int(fields[0])
                require(node not in rows, f"duplicate node {node} in DAT block {key}")
                rows[node] = fields[1:]
                started = True
            elif started:
                break
        require(bool(rows), f"empty DAT block {key}")
        result[key] = rows
    return result


def zero_boundary_rows(deck: str, node: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    in_boundary = False
    before_first_step = True
    boundary_has_amplitude = False
    for line in deck.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("**"):
            continue
        if stripped.startswith("*"):
            in_boundary = stripped.upper().startswith("*BOUNDARY")
            if stripped.upper().startswith("*STEP"):
                before_first_step = False
            if in_boundary:
                boundary_has_amplitude = "AMPLITUDE=" in stripped.upper()
            continue
        if not in_boundary:
            continue
        fields = [field.strip() for field in stripped.split(",")]
        if not fields or not fields[0].isdigit() or int(fields[0]) != node:
            continue
        try:
            if len(fields) == 4:
                first, last = int(fields[1]), int(fields[2])
                value = float(fields[3].replace("D", "E").replace("d", "e"))
            elif len(fields) == 3:
                first, last, value = int(fields[1]), int(fields[2]), 0.0
            else:
                continue
        except ValueError:
            continue
        if first <= last:
            rows.append({
                "node": node,
                "first_dof": first,
                "last_dof": last,
                "value": value,
                "before_first_step": before_first_step,
                "amplitude_parameter": boundary_has_amplitude,
            })
    return rows


def dependent_dofs(model: dict[str, Any]) -> set[tuple[int, int]]:
    equations = model.get("equations", [])
    return {(int(eq[0][0]), int(eq[0][1])) for eq in equations if eq and eq[0]}


def evidence_pins() -> dict[str, Any]:
    for path, expected in FILE_PINS.items():
        require(sha256(path) == expected, f"pinned evidence hash mismatch: {path}")
    archive_hash = sha256(SOURCE_ARCHIVE)
    require(archive_hash == SOURCE_ARCHIVE_SHA256, "upstream source archive hash mismatch")
    manifest = load_json(MANIFEST)
    require(manifest["upstream_source_archive_sha256"] == SOURCE_ARCHIVE_SHA256,
            "build manifest source archive hash mismatch")
    archived_sources: dict[str, str] = {}
    with tarfile.open(ROOT / SOURCE_ARCHIVE, "r:bz2") as archive:
        for name, expected in SOURCE_FILE_SHA256.items():
            member_name = f"./CalculiX/ccx_2.23/src/{name}"
            member = archive.extractfile(member_name)
            require(member is not None, f"pinned upstream source member missing: {member_name}")
            actual = hashlib.sha256(member.read()).hexdigest()
            require(actual == expected, f"upstream source file hash mismatch: {name}")
            require(manifest["upstream_files_sha256"].get(member_name) == expected,
                    f"build manifest file hash mismatch: {name}")
            archived_sources[name] = actual
    return {
        "case_files_sha256": {str(path): sha256(path) for path in FILE_PINS},
        "upstream_source_archive": {"path": str(SOURCE_ARCHIVE), "sha256": archive_hash},
        "upstream_source_files_sha256": archived_sources,
        "manual_sha256": sha256(MANUAL),
        "solver_profile_sha256": sha256(PROFILE),
    }


def check_coupon(coupon: dict[str, Any]) -> dict[str, Any]:
    for role, expected in coupon["pins"].items():
        path = {
            "model.json": coupon["model"],
            "model.inp": coupon["deck"],
            "model.dat": coupon["dat"],
            "parent_check": coupon["parent_check"],
        }[role]
        require(sha256(path) == expected, f"coupon pin mismatch: {coupon['name']} {role}")
    model = load_json(coupon["model"])
    deck = (ROOT / coupon["deck"]).read_text()
    dat = (ROOT / coupon["dat"]).read_text()
    check = load_json(coupon["parent_check"])
    require(check.get("status") == "PASS_PARENT_ALL_PRINTED_INCREMENT_CHECK",
            f"coupon independent increment check did not pass: {coupon['name']}")
    dependent = dependent_dofs(model)
    blocks = parse_native_blocks(dat)
    times = sorted({time for (kind, time) in blocks if kind == "u"})
    require(len(times) == int(check.get("printed_increment_count", check.get("increment_count", -1))),
            f"coupon DAT increment count differs from parent check: {coupon['name']}")
    for node in coupon["targets"]:
        require(node in set(model.get("fixed_nodes", [])),
                f"coupon target is not recorded fixed: {coupon['name']} node {node}")
        for dof in (1, 2, 3):
            require((node, dof) not in dependent,
                    f"coupon target is MPC dependent: {coupon['name']} node {node} dof {dof}")
            rows = zero_boundary_rows(deck, node)
            require(any(row["first_dof"] <= dof <= row["last_dof"] and row["value"] == 0.0
                        for row in rows),
                    f"coupon target lacks zero boundary row: {coupon['name']} node {node} dof {dof}")
            require(all(float(blocks[("u", time)][node][dof - 1].replace("D", "E")) == 0.0
                        for time in times),
                    f"coupon fixed target has nonzero native U: {coupon['name']} node {node} dof {dof}")
    return {
        "name": coupon["name"],
        "parent_check_status": check["status"],
        "observed_increment_count": len(times),
        "fixed_ground_nodes_with_zero_U_all_printed_increments": coupon["targets"],
        "all_target_dofs_zero_spc_and_not_mpc_dependent": True,
        "physical_or_design_acceptance": False,
    }


def replay() -> dict[str, Any]:
    pins = evidence_pins()
    execution = load_json(CASE / "execution.json")
    freeze = load_json(CASE / "freeze.json")
    model = load_json(CASE / "model.json")
    deck = (ROOT / (CASE / "model.inp")).read_text()
    dat = (ROOT / (CASE / "model.dat")).read_text()
    blocks = parse_native_blocks(dat)
    time = 0.1
    require(("u", time) in blocks and ("rf", time) in blocks,
            "k12-rear first increment U/RF block missing")
    require(execution.get("native_solve_executed") is True
            and execution.get("returncode") == 0
            and execution.get("container_confirmed_terminal") is True,
            "existing k12 native evidence is not successful/terminal")
    require(execution["outputs_sha256"].get("model.dat") == sha256(CASE / "model.dat"),
            "k12 DAT does not match the recorded execution output hash")
    require(execution["outputs_sha256"].get("model.inp") == sha256(CASE / "model.inp")
            and execution["outputs_sha256"].get("model.json") == sha256(CASE / "model.json"),
            "k12 model/deck do not match the recorded execution input hashes")
    require(freeze["solver_profile"]["version"] == "2.23"
            and freeze["solver_profile"]["image_id"] == "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
            and freeze["solver_profile"]["binary_sha256"] == "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863",
            "k12 native freeze does not match the pinned CCX 2.23 build")

    binding = next(row for row in model["unilateral_springa_bindings"] if row["group"] == "SPR1110")
    node_q, node_ground = map(int, binding["springa_nodes"])
    row_by_node = blocks[("u", time)]
    radii = {node: [half_last_place(token) for token in tokens] for node, tokens in row_by_node.items()}
    dep = dependent_dofs(model)
    bc_rows = zero_boundary_rows(deck, node_ground)
    require(node_ground in set(model["fixed_nodes"]), "SPR1110 ground node is not recorded fixed")
    for dof in (1, 2, 3):
        require((node_ground, dof) not in dep, f"SPR1110 ground DOF {dof} is MPC dependent")
        exact_rows = [row for row in bc_rows if row["first_dof"] <= dof <= row["last_dof"]]
        require(len(exact_rows) == 1 and exact_rows[0]["value"] == 0.0
                and exact_rows[0]["before_first_step"]
                and not exact_rows[0]["amplitude_parameter"],
                f"SPR1110 ground DOF {dof} lacks a single step-invariant zero SPC")
        require(float(row_by_node[node_ground][dof - 1].replace("D", "E")) == 0.0,
                f"SPR1110 ground DOF {dof} native U token is not zero")

    axis = [float(x) for x in binding["numerical_axis_global_xyz"]]
    coords = model["nodes"]
    initial = [float(coords[str(node_q)][i]) - float(coords[str(node_ground)][i]) for i in range(3)]
    require(all(abs(initial[i] - float(binding["initial_span_mm"]) * axis[i]) < 1e-10
                for i in range(3)), "SPR1110 initial vector differs from its recorded axis/span")
    uq = [float(x.replace("D", "E")) for x in row_by_node[node_q]]
    ug = [float(x.replace("D", "E")) for x in row_by_node[node_ground]]
    rq = radii[node_q][:]
    rg_old = radii[node_ground][:]
    rg_new = [0.0, 0.0, 0.0]
    qvec = [uq[i] - ug[i] for i in range(3)]
    cur = [initial[i] + qvec[i] for i in range(3)]
    initial_length = math.sqrt(sum(x * x for x in initial))
    current_length = math.sqrt(sum(x * x for x in cur))
    current_axis = [x / current_length for x in cur]
    geometric_q = current_length - initial_length
    arithmetic_guard = 16.0 * float.fromhex("0x1.0000000000000p-52") * max(
        1.0, initial_length, current_length
    )
    old_radius = sum(abs(current_axis[i]) * (rq[i] + rg_old[i]) for i in range(3)) + arithmetic_guard
    new_radius = sum(abs(current_axis[i]) * (rq[i] + rg_new[i]) for i in range(3)) + arithmetic_guard

    projection_nodes = list(map(int, binding["source_projection_nodes"]))
    projection_dof = int(binding["source_projection_dof"]) - 1
    source_q = (float(row_by_node[projection_nodes[1]][projection_dof].replace("D", "E"))
                - float(row_by_node[projection_nodes[0]][projection_dof].replace("D", "E")))
    source_q_radius = (radii[projection_nodes[1]][projection_dof]
                       + radii[projection_nodes[0]][projection_dof])
    q_from_ghost = sum(qvec[i] * axis[i] for i in range(3))
    ground_force_tokens = blocks[("rf", time)][node_q]
    ground_force = [float(x.replace("D", "E")) for x in ground_force_tokens]
    internal_force = sum(ground_force[i] * axis[i] for i in range(3))
    stiffness = float(binding["stiffness_n_per_mm"])
    old_interval = [geometric_q - old_radius, geometric_q + old_radius]
    new_interval = [geometric_q - new_radius, geometric_q + new_radius]
    require(old_interval[0] < 0.0 < old_interval[1], "old printed-zero interval does not straddle zero")
    require(new_interval[1] < 0.0, "exact-SPC replay did not place q interval strictly below zero")
    require(abs(q_from_ghost - source_q) <= old_radius + source_q_radius + 1e-12,
            "native q and source projection are inconsistent even with original intervals")

    coupons = [check_coupon(coupon) for coupon in COUPONS]
    return {
        "schema": "zero_spc_displacement_interval_proof/v1",
        "status": "SUPPORTED_NARROW_EXACT_ZERO_SPC_INTERVAL_RULE",
        "rule": {
            "eligible_only_when": [
                "The exact native input serializes a zero *BOUNDARY value for the displacement DOF, active before the increment and without an amplitude.",
                "The DOF is an SPC, not the dependent term of any serialized *EQUATION/MPC.",
                "The matching native U token is printed as numeric zero.",
            ],
            "effect": "For DAT rounding-interval propagation only, replace that qualifying component's printed-token half-last-place radius by exactly zero.",
            "unchanged": "All free, nonzero-constraint, and MPC-dependent output components retain the existing half-last-place radii; all geometric arithmetic guards and force/equilibrium limits stay unchanged.",
        },
        "source_pins": pins,
        "native_input_and_execution": {
            "case_id": model["case_id"],
            "execution_returncode": execution["returncode"],
            "execution_terminal": execution["container_confirmed_terminal"],
            "solver_version": freeze["solver_profile"]["version"],
            "solver_image_id": freeze["solver_profile"]["image_id"],
            "solver_binary_sha256": freeze["solver_profile"]["binary_sha256"],
            "selected_time": time,
        },
        "springa_ground": {
            "source_group": binding["group"],
            "springa_nodes_first_ground": [node_q, node_ground],
            "ground_role": next(row["role"] for row in model["numerical_spring_ground_nodes"]
                                if int(row["node"]) == node_ground),
            "ground_xyz_mm": coords[str(node_ground)],
            "ground_u_tokens_xyz_mm": row_by_node[node_ground],
            "ground_u_token_radii_xyz_mm_before": radii[node_ground],
            "ground_u_token_radii_xyz_mm_after": rg_new,
            "explicit_zero_spc_rows": bc_rows,
            "all_ground_dofs_fixed_and_not_mpc_dependent": True,
            "spring_axis_global": axis,
            "source_projection_nodes_dof_one_based": [*projection_nodes, projection_dof + 1],
            "source_projection_q_mm": source_q,
            "source_projection_q_radius_mm_unchanged": source_q_radius,
            "q_from_native_springa_endpoint_displacements_mm": q_from_ghost,
            "native_geometric_elongation_mm": geometric_q,
            "native_internal_force_on_first_endpoint_n": internal_force,
            "native_first_endpoint_rf_tokens_xyz_n": ground_force_tokens,
            "table_force_from_negative_elongation_n": stiffness * max(geometric_q, 0.0),
            "geometric_arithmetic_guard_mm_unchanged": arithmetic_guard,
            "original_geometry_radius_mm": old_radius,
            "proposed_geometry_radius_mm": new_radius,
            "original_elongation_interval_mm": old_interval,
            "proposed_elongation_interval_mm": new_interval,
            "old_interval_classification": "overlaps zero; first increment is unresolved by printed-rounding interval",
            "proposed_interval_classification": "strictly negative; consistent with the native zero-force inactive SPRINGA branch",
            "only_changed_interval_inputs": [f"U({node_ground},DOF {dof}) printed radii, each changed from {radii[node_ground][dof-1]} to 0.0 mm" for dof in (1, 2, 3)],
        },
        "existing_2_23_native_coupon_observations": coupons,
        "limitations": [
            "This is a DAT representation-rounding correction, not a bound on nonlinear solver residual, iterative convergence error, discretization, or physical uncertainty.",
            "A zero-looking free DOF or an MPC-dependent zero token stays at its full printed half-last-place interval.",
            "The rule is demonstrated only for explicit homogeneous zero SPC translational DOFs in the pinned CCX 2.23 output path; do not extend it to nonzero prescribed values, other solver builds, or alternate coordinate transformations without separate evidence.",
            "Known-answer coupons establish method/output behavior only; they do not qualify frame stability, contact, joint resistance, a floor, or design acceptance.",
            "No auditor, native deck/data, freeze, run ledger, or geometry was modified or executed by this replay.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(replay(), indent=2, sort_keys=True))
