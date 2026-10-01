#!/usr/bin/env python3
"""Independent input oracle and native-output checker for the SPR489 coupon.

The default native API is:
  python check.py --native-dir PATH_TO_FROZEN_NATIVE_PACKET

No solver is invoked. `--input-audit` writes the reproducible analytical
readiness record from the prepared input deck only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
import tarfile
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
METHOD = Path(__file__).resolve().parent
PACKET = SERIES / "current-k12-rear-spr489-cascade-trace-attempt01"
COUPON = PACKET / "direct-scalar-coupon"
ATTEMPT03 = SERIES / "current-springa-selected-floor-k12-rear-attempt03"
RELATIVE_FIXTURE = SERIES / "current-springa-relative-coordinate-fixture-attempt01"
STABLE_AUDIT = SERIES / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
STABLE_AUDIT_SHA256 = "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"
ARCHIVE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt02/build/context/source.tar.bz2"
MANIFEST = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/calculix-2.23-upgrade-attempt01/build_manifest.json"
MANUAL = ROOT / "fea/generated/ccx_2.23.pdf"
PROFILE = ROOT / "fea/calculix_223/solver-profile.json"
STEPS_MEMBER = "./CalculiX/ccx_2.23/src/steps.f"
STEPS_SHA256 = "4fe0e421f62640ba92e83f1e7e2cc0ceb7ed778f752639c2347538bf716bfcd4"
MANUAL_SHA256 = "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"
EXPECTED_COUPON_DECK_SHA256 = "95057c23311105f953a9e99a35ae1e73e76d8c6f3137f464af957ef32e5a489c"
EXPECTED_COUPON_MODEL_SHA256 = "6fcc8a55afd156c3516146bb6e98aabe4f3d4366647d6e57ea0924703e4e68ff"
EXPECTED_PARENT_INPUT_AUDIT_SHA256 = ""  # Parent may regenerate this audit before freeze.
EXPECTED_END_TIMES = {1: 1.0, 2: 2.0, 3: 3.0}
FLOAT_GUARD = 32.0 * sys.float_info.epsilon


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def fail(message: str) -> None:
    raise RuntimeError(message)


def token_helper():
    if sha(STABLE_AUDIT) != STABLE_AUDIT_SHA256:
        fail("Pinned CCX DAT precision helper changed")
    spec = importlib.util.spec_from_file_location("pinned_springa_stable_response", STABLE_AUDIT)
    if spec is None or spec.loader is None:
        fail("Cannot import pinned CCX DAT precision helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fnum(value: str) -> float:
    return float(value.strip().replace("D", "E").replace("d", "e"))


def parse_deck(deck: str) -> dict[str, Any]:
    """Parse the small coupon's nodes, springs, equation, boundaries and CLOADs."""
    out: dict[str, Any] = {
        "nodes": {}, "elements": [], "equation": None, "boundaries": [],
        "cloads": [], "linear_springs": {}, "nonlinear_springs": {},
        "step_cards": [], "step_static": [],
    }
    lines = deck.splitlines()
    i = 0
    card = ""
    current_elset = ""
    current_element_type = ""
    current_load: dict[tuple[int, int], float] | None = None
    current_step = 0
    while i < len(lines):
        raw = lines[i].strip()
        if not raw or raw.startswith("**"):
            i += 1
            continue
        if raw.startswith("*"):
            upper = raw.upper()
            card = upper
            if upper.startswith("*STEP"):
                current_step += 1
                out["step_cards"].append(upper)
                current_load = None
            elif upper.startswith("*STATIC"):
                out["step_static"].append(current_step)
            elif upper.startswith("*ELEMENT"):
                current_elset = param(upper, "ELSET")
                current_element_type = param(upper, "TYPE")
            elif upper.startswith("*CLOAD"):
                current_load = {}
                out["cloads"].append(current_load)
            elif upper.startswith("*EQUATION"):
                if out["equation"] is not None:
                    fail("Coupon deck has multiple equations; expected the single direct scalar row")
                i += 1
                if i >= len(lines):
                    fail("Truncated *EQUATION term count")
                count = int(lines[i].strip())
                terms: list[tuple[int, int, float]] = []
                i += 1
                while i < len(lines) and len(terms) < count:
                    fields = [x.strip() for x in lines[i].split(",") if x.strip()]
                    if len(fields) % 3:
                        fail(f"Malformed *EQUATION data line {i + 1}")
                    for j in range(0, len(fields), 3):
                        terms.append((int(fields[j]), int(fields[j + 1]), fnum(fields[j + 2])))
                    i += 1
                if len(terms) != count:
                    fail("*EQUATION term count differs from serialized terms")
                out["equation"] = terms
                continue
            elif upper.startswith("*SPRING"):
                elset = param(upper, "ELSET")
                i += 1
                if "NONLINEAR" in upper:
                    rows = []
                    while i < len(lines) and not lines[i].strip().startswith("*"):
                        line = lines[i].strip()
                        if line:
                            fs = [x.strip() for x in line.split(",") if x.strip()]
                            if len(fs) != 2:
                                fail(f"Malformed nonlinear spring table row at line {i + 1}")
                            rows.append([fnum(fs[0]), fnum(fs[1])])
                        i += 1
                    out["nonlinear_springs"][elset] = rows
                    continue
                if i + 1 >= len(lines):
                    fail("Truncated linear *SPRING definition")
                dofs = [int(x.strip()) for x in lines[i].split(",") if x.strip()]
                stiffness = fnum(lines[i + 1].strip())
                out["linear_springs"][elset] = {"dofs": dofs, "stiffness": stiffness}
                i += 2
                continue
            i += 1
            continue

        fields = [x.strip() for x in raw.split(",") if x.strip()]
        if card == "*NODE" or card.startswith("*NODE,"):
            if len(fields) != 4:
                fail(f"Bad node row at line {i + 1}")
            out["nodes"][int(fields[0])] = [fnum(x) for x in fields[1:]]
        elif card.startswith("*ELEMENT"):
            out["elements"].append({
                "id": int(fields[0]), "nodes": [int(x) for x in fields[1:]],
                "type": current_element_type, "elset": current_elset,
            })
        elif card.startswith("*BOUNDARY"):
            if len(fields) not in (2, 4):
                fail(f"Bad boundary row at line {i + 1}")
            if len(fields) == 2:
                out["boundaries"].append((int(fields[0]), int(fields[1]), int(fields[1]), 0.0))
            else:
                out["boundaries"].append((int(fields[0]), int(fields[1]), int(fields[2]), fnum(fields[3])))
        elif card.startswith("*CLOAD"):
            if current_load is None:
                fail("CLOAD row outside a CLOAD block")
            key = (int(fields[0]), int(fields[1]))
            if key in current_load:
                fail(f"Duplicate CLOAD {key}")
            current_load[key] = fnum(fields[2])
        i += 1

    if current_step != 3 or len(out["cloads"]) != 3:
        fail(f"Expected three static load steps/CLOAD blocks, got {current_step}/{len(out['cloads'])}")
    return out


def param(card: str, key: str) -> str:
    prefix = key.upper() + "="
    for part in card.split(",")[1:]:
        part = part.strip()
        if part.startswith(prefix):
            return part[len(prefix):]
    return ""


def parse_steps_source() -> str:
    if sha(ARCHIVE) != "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7":
        fail("Pinned CCX 2.23 source archive changed")
    manifest = read_json(MANIFEST)
    if manifest["upstream_files_sha256"].get(STEPS_MEMBER) != STEPS_SHA256:
        fail("Pinned steps.f source manifest hash changed")
    with tarfile.open(ARCHIVE, "r:bz2") as tf:
        member = tf.extractfile(STEPS_MEMBER)
        if member is None:
            fail("Pinned source archive has no steps.f")
        data = member.read()
    if hashlib.sha256(data).hexdigest() != STEPS_SHA256:
        fail("Extracted steps.f differs from pinned CCX 2.23 member hash")
    return data.decode("latin1")


def source_step_semantics(deck: str, previous: dict[str, Any]) -> dict[str, Any]:
    cards = previous["step_cards"]
    expected = "*STEP,NLGEOM,NLGEOM=NO,INC=40"
    if cards != [expected] * 3:
        fail(f"Expected three byte-equivalent known-step cards, got {cards}")
    source = parse_steps_source().splitlines()
    relevant = {line_number: source[line_number - 1].strip()
                for line_number in (156, 157, 161, 165, 166, 176, 179, 180, 181, 183)}
    # steps.f uppercases textpart before this branch. Each comma-separated
    # keyword fragment is handled in order: bare NLGEOM selects iteration and
    # geometry; the later NLGEOM=NO clears geometry only, leaving iperturb(1)
    # intact. Existing frozen coupon proves the same authored card executed.
    return {
        "deck_step_cards": cards,
        "pinned_steps_f_member_sha256": STEPS_SHA256,
        "pinned_steps_f_source_lines": relevant,
        "interpretation": "For the emitted order, bare NLGEOM first sets iperturb(1)=2 (Newton iteration active) and iperturb(2)=1; NLGEOM=NO then sets iperturb(2)=0 without resetting iperturb(1). The pair intentionally requests iterative nonlinear solution with geometric effects off in CCX 2.23. It is not treated as two conflicting duplicate booleans.",
        "same_card_in_prior_successful_fixture": True,
        "prior_fixture_deck_sha256": sha(RELATIVE_FIXTURE / "model.inp"),
        "prior_fixture_assessment_sha256": sha(RELATIVE_FIXTURE / "assessment.json"),
        "prior_fixture_native_pass": read_json(RELATIVE_FIXTURE / "assessment.json")["newton_active_and_geometric_effects_off_verified"] is True,
        "pinned_manual_url": "https://www.dhondt.de/ccx_2.23.pdf",
        "pinned_manual_path": rel(MANUAL),
        "pinned_manual_sha256": sha(MANUAL),
        "manual_section": "7.118 *STEP (CCX 2.23 manual); lists NLGEOM as optional and defines NLGEOM=NO as geometric effects off.",
    }


def load_metadata() -> dict[str, Any]:
    path = COUPON / "model.json"
    if sha(path) != EXPECTED_COUPON_MODEL_SHA256:
        fail(f"Pinned coupon model changed: {sha(path)}")
    return read_json(path)


def verify_source_packet() -> dict[str, Any]:
    pins = read_json(PACKET / "source-pins.json")
    for name, expected in pins["source_files"].items():
        path = ROOT / name
        if not path.is_file() or sha(path) != expected:
            fail(f"Pinned input source changed: {name}")
    for name, expected in pins["output_files"].items():
        path = PACKET / name
        if not path.is_file() or sha(path) != expected:
            fail(f"Pinned prepared artifact changed: {name}")
    if sha(COUPON / "model.inp") != EXPECTED_COUPON_DECK_SHA256:
        fail("Coupon deck hash changed")
    return pins


def vector_add(a: list[float], b: list[float]) -> list[float]:
    return [a[i] + b[i] for i in range(3)]


def vector_scale(a: list[float], scale: float) -> list[float]:
    return [scale * a[i] for i in range(3)]


def cross(a: list[float], b: list[float]) -> list[float]:
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def norm(v: list[float]) -> float:
    return math.sqrt(math.fsum(x * x for x in v))


def token_bounds(token: str, radius_func: Any) -> tuple[float, float, float]:
    value = fnum(token)
    radius = float(radius_func(token))
    return value, value - radius, value + radius


def calculate_oracle(deck: str, model: dict[str, Any], parsed: dict[str, Any], precision: Any) -> dict[str, Any]:
    terms = parsed["equation"]
    if not terms or terms[0] != (90001, 1, 1.0):
        fail("Direct equation dependent term must be Q,1,+1")
    b = {(n, d): -coef for n, d, coef in terms[1:]}
    if len(b) != 80 or set((n, d) for n, d in b) != {
            (int(n), d) for side in ("first_master_nodes_and_weights", "second_master_nodes_and_weights")
            for n, _w in model["source_interpolation"][side] for d in (2, 3)}:
        fail("Direct MPC does not contain exactly the 80 source projection master DOFs")
    owner_meta = model["source_physical_binding"]
    point = [float(x) for x in owner_meta["physical_owner_point_global_mm"]]
    axis = [float(x) for x in owner_meta["preserved_scalar_normal_global"]]
    first = owner_meta["first_owner"]
    second = owner_meta["second_owner"]
    first_nodes = [int(n) for n, _w in model["source_interpolation"]["first_master_nodes_and_weights"]]
    second_nodes = [int(n) for n, _w in model["source_interpolation"]["second_master_nodes_and_weights"]]
    first_set, second_set = set(first_nodes), set(second_nodes)
    coords = parsed["nodes"]
    if not first_set.isdisjoint(second_set):
        fail("Physical owner master node sets overlap")
    if any(n not in coords for n in first_set | second_set):
        fail("A physical source master is absent from the emitted deck")

    # Parse exact source stiffness and unilateral SPRINGA table from deck.
    if parsed["linear_springs"].get("SUPPORT_Y") != {"dofs": [2, 2], "stiffness": 100.0}:
        fail("Fixture SUPPORT_Y law differs from the serialized 100 N/mm oracle")
    if parsed["linear_springs"].get("SUPPORT_Z") != {"dofs": [3, 3], "stiffness": 100.0}:
        fail("Fixture SUPPORT_Z law differs from the serialized 100 N/mm oracle")
    support_k = 100.0
    table = parsed["nonlinear_springs"].get("JOINT")
    expected_table = [[0.0, -10.0], [0.0, 0.0], [2630833.0386325, 10.0]]
    if table != expected_table:
        fail(f"Unrecognized SPRINGA table: {table}")
    force_k = table[2][0] / table[2][1]
    source_stiffness = float(owner_meta["stiffness_N_per_mm"])
    if abs(force_k - source_stiffness) > 1.0e-8:
        fail("Emitted unilateral table slope differs from source SPR489 stiffness")

    joint_elements = [e for e in parsed["elements"]
                      if e["elset"] == "JOINT" and e["type"] == "SPRINGA"]
    if len(joint_elements) != 1 or len(joint_elements[0]["nodes"]) != 2:
        fail(f"Expected exactly one two-node JOINT SPRINGA, got {joint_elements}")
    q_node, q_ground = joint_elements[0]["nodes"]
    if q_node not in coords or q_ground not in coords:
        fail("SPRINGA Q/GQ endpoint is absent from serialized node inventory")

    # Explicit source owner/geometry lineage check against pinned attempt03.
    source_model = read_json(ATTEMPT03 / "model.json")
    source_binding = next(x for x in source_model["unilateral_springa_bindings"]
                          if x["source_row_id"] == "SPR489")
    if (source_binding["physical_owner"]["first"] != first
            or source_binding["physical_owner"]["second"] != second
            or source_binding["physical_owner"]["point"] != point
            or source_binding["physical_owner"]["scalar_normal"] != axis
            or source_binding["stiffness_n_per_mm"] != source_stiffness):
        fail("Coupon changed source SPR489 physical owner, point, axis, or stiffness")
    for n in first_set | second_set:
        # The input writer serializes nodal coordinates with 14 significant
        # digits; compare against that exact emitted representation.
        serialized_source = [float(format(float(v), ".14g"))
                             for v in source_model["nodes"][str(n)]]
        if coords[n] != serialized_source:
            fail(f"Source geometry changed for interpolation master node {n}")
    for owner, nodes in ((first, first_set), (second, second_set)):
        if not nodes.issubset(set(map(int, source_model["physical_body_nodes"][owner]))):
            fail(f"Source interpolation nodes do not retain owner {owner}")

    # Check direct equation coefficient map against actual source interpolation
    # rows and preserved normal, using emitted deck reals, not the old qghost.
    for side, nodes, sign in (("A", first_nodes, 1.0), ("B", second_nodes, -1.0)):
        raw_weights = dict((int(n), float(w)) for n, w in model["source_interpolation"][
            "first_master_nodes_and_weights" if side == "A" else "second_master_nodes_and_weights"])
        for node in nodes:
            expected_by_dof = {2: sign * axis[1] * raw_weights[node],
                               3: sign * axis[2] * raw_weights[node]}
            for dof in (2, 3):
                actual_eq = -b[(node, dof)]
                emitted = float(format(expected_by_dof[dof], ".14g"))
                if actual_eq != emitted:
                    fail(f"Direct scalar coefficient changed at {(node, dof)}")

    # Identify support ground endpoints from the serialized SPRING2 elements.
    support_ground: dict[tuple[int, int], int] = {}
    for elset, dof in (("SUPPORT_Y", 2), ("SUPPORT_Z", 3)):
        rows = [e for e in parsed["elements"] if e["elset"] == elset and e["type"] == "SPRING2"]
        if len(rows) != 40:
            fail(f"Expected 40 {elset} endpoint springs, got {len(rows)}")
        for e in rows:
            if len(e["nodes"]) != 2:
                fail(f"Bad SPRING2 endpoints on element {e['id']}")
            key = (e["nodes"][0], dof)
            if key in support_ground:
                fail(f"Duplicate support ground for source dof {key}")
            support_ground[key] = e["nodes"][1]
    if set(support_ground) != set(b):
        fail("Support endpoint map and direct equation DOFs differ")

    if len(parsed["cloads"]) != 3 or any(set(load) != set(b) for load in parsed["cloads"]):
        fail("Each of three CLOAD blocks must contain exactly the 80 source interpolation DOFs")
    # The rank-one system has diagonal source support stiffness s and one
    # SPRINGA coordinate q=b^T u. With closed-side force f=kq, solve
    # q=(b^T L/s)/(1+k b^T b/s). If that candidate is nonpositive, use the
    # open branch f=0 and q=b^T L/s. This is independent of parent metadata.
    bnorm2 = math.fsum(value * value for value in b.values())
    states = []
    for step, loads in enumerate(parsed["cloads"], start=1):
        rhs = math.fsum(b[key] * loads[key] for key in b) / support_k
        closed_candidate = rhs / (1.0 + force_k * bnorm2 / support_k)
        q = closed_candidate if closed_candidate > 0.0 else rhs
        f = table_force(q, table)
        u = {key: (loads[key] - f * b[key]) / support_k for key in b}
        q_check = math.fsum(b[key] * u[key] for key in b)
        guard = FLOAT_GUARD * max(1.0, abs(q), abs(q_check))
        if abs(q_check - q) > guard:
            fail(f"Rank-one oracle internal equation residual at step {step}: {q_check-q}")
        # Analytic action is -f*b, equivalent to +f*n on source first owner
        # and -f*n on second owner for q=pB-pA.
        nodal_action = {str(n): [0.0, -f * b[(n, 2)], -f * b[(n, 3)]]
                        for n in first_nodes + second_nodes}
        action_a = [math.fsum(nodal_action[str(n)][j] for n in first_nodes) for j in range(3)]
        action_b = [math.fsum(nodal_action[str(n)][j] for n in second_nodes) for j in range(3)]
        moment_a = [0.0, 0.0, 0.0]
        moment_b = [0.0, 0.0, 0.0]
        for n in first_nodes:
            moment_a = vector_add(moment_a, cross(coords[n], nodal_action[str(n)]))
        for n in second_nodes:
            moment_b = vector_add(moment_b, cross(coords[n], nodal_action[str(n)]))
        ideal_a = vector_scale(axis, f)
        ideal_b = vector_scale(ideal_a, -1.0)
        ideal_ma, ideal_mb = cross(point, ideal_a), cross(point, ideal_b)
        displacement_by_node = {str(n): [0.0, u[(n, 2)], u[(n, 3)]] for n in first_nodes + second_nodes}
        spring_endpoint_force = {str(n): [0.0, support_k * u[(n, 2)], support_k * u[(n, 3)]]
                                 for n in first_nodes + second_nodes}
        states.append({
            "step": step,
            "serialized_CLOAD_N": {f"{n}:{d}": float(loads[(n, d)]) for n, d in sorted(b)},
            "analytic_q_mm": q,
            "analytic_q_from_direct_MPC_mm": q_check,
            "analytic_joint_force_N": f,
            "analytic_master_displacements_mm": {f"{n}:{d}": u[(n, d)] for n, d in sorted(b)},
            "analytic_source_displacement_by_node_mm": displacement_by_node,
            "support_spring_endpoint_force_by_node_N": spring_endpoint_force,
            "expected_joint_action_by_source_master_N": nodal_action,
            "expected_owner_force_first_N": action_a,
            "expected_owner_force_second_N": action_b,
            "ideal_owner_force_first_N": ideal_a,
            "ideal_owner_force_second_N": ideal_b,
            "owner_force_first_residual_N": [action_a[j] - ideal_a[j] for j in range(3)],
            "owner_force_second_residual_N": [action_b[j] - ideal_b[j] for j in range(3)],
            "owner_moment_first_global_origin_Nmm": moment_a,
            "owner_moment_second_global_origin_Nmm": moment_b,
            "ideal_owner_moment_first_global_origin_Nmm": ideal_ma,
            "ideal_owner_moment_second_global_origin_Nmm": ideal_mb,
            "owner_moment_first_residual_Nmm": [moment_a[j] - ideal_ma[j] for j in range(3)],
            "owner_moment_second_residual_Nmm": [moment_b[j] - ideal_mb[j] for j in range(3)],
            "springa_force_table_domain_mm": [-10.0, 10.0],
            "springa_ground_is_numerical_only": True,
        })
    return {
        "nodes": parsed["nodes"], "elements": parsed["elements"],
        "equation": terms, "b": b, "support_ground": support_ground,
        "support_stiffness": support_k, "springa_table": table,
        "springa_slope": force_k, "axis": axis, "owner_point": point,
        "first_owner": first, "second_owner": second,
        "first_nodes": first_nodes, "second_nodes": second_nodes,
        "states": states,
        "springa_q_node": q_node,
        "springa_ground_node": q_ground,
        "source_weights": model["source_interpolation"],
        "step_semantics": source_step_semantics(deck, parsed),
    }


def table_force(q: float, table: list[list[float]]) -> float:
    """Piecewise-linear force for table pairs stored as [force, elongation]."""
    points = [(float(row[1]), float(row[0])) for row in table]
    if q < points[0][0] or q > points[-1][0]:
        fail(f"SPRINGA elongation {q} mm is outside the serialized table domain")
    for (x0, f0), (x1, f1) in zip(points, points[1:]):
        if x0 <= q <= x1:
            if x1 == x0:
                return f0
            return f0 + (q - x0) * (f1 - f0) / (x1 - x0)
    return points[-1][1]


def input_audit() -> dict[str, Any]:
    pins = verify_source_packet()
    deck_path = COUPON / "model.inp"
    deck = deck_path.read_text()
    model = load_metadata()
    parsed = parse_deck(deck)
    precision = token_helper()
    oracle = calculate_oracle(deck, model, parsed, precision)
    # The same geometry and action labels must remain the previously reviewed
    # source; no new owners are inferred from this coupon.
    binding = model["source_physical_binding"]
    if binding["source_row_id"] != "SPR489" or binding["source_owner_fields_exactly_match_pinned_attempt03_binding"] is not True:
        fail("Input coupon is not bound to the original SPR489 physical ownership")
    # Cross-check the prepared known-answer points without using them to derive
    # the independent rank-one solution.
    metadata_states = model["known_answer_states"]
    if len(metadata_states) != 3:
        fail("Coupon must provide exactly three analytic answer states")
    for derived, declared in zip(oracle["states"], metadata_states):
        if abs(derived["analytic_q_mm"] - float(declared["serialized_equation_q_mm"])) > 1.0e-12:
            fail(f"Independent rank-one q differs from prepared state {derived['step']}")
        if abs(derived["analytic_joint_force_N"] - float(declared["native_force_expected_N"])) > 1.0e-8:
            fail(f"Independent force oracle differs from prepared state {derived['step']}")
    return {
        "schema": "current_spr489_direct_scalar_coupon_input_readiness/v1",
        "status": "PASS_INPUT_ONLY_INDEPENDENT_RANK_ONE_ORACLE",
        "native_solve_executed": False,
        "mechanical_acceptance": False,
        "qualified_for_design": False,
        "source_deck_sha256": sha(deck_path),
        "source_model_sha256": sha(COUPON / "model.json"),
        "source_packet_pins_sha256": sha(PACKET / "source-pins.json"),
        "checker_sha256": sha(Path(__file__).resolve()),
        "solver_profile_sha256": sha(PROFILE),
        "manual_sha256": sha(MANUAL),
        "steps_source_sha256": STEPS_SHA256,
        "input_native_method_semantics": oracle["step_semantics"],
        "source_owner": {
            "source_row_id": binding["source_row_id"],
            "first_owner": binding["first_owner"],
            "second_owner": binding["second_owner"],
            "point_global_mm": binding["physical_owner_point_global_mm"],
            "normal_global": binding["preserved_scalar_normal_global"],
            "stiffness_N_per_mm": binding["stiffness_N_per_mm"],
            "owner_binding_matches_original_source": True,
        },
        "rank_one_serialized_oracle": oracle["states"],
        "serialized_CLOAD_spring_and_MPC_cards_parsed_and_rebuilt_independently": True,
        "limits": [
            "Input readiness is method-coupon evidence only; it authorizes no native run itself.",
            "SPRING2 supports are numerical fixtures, not physical floor/support properties.",
            "The three endpoint oracles use each step's complete serialized CLOAD set. No assumption is made about intermediate load transitions after successive OP=NEW sets.",
            "The isolated coupon does not qualify a frame, joint, bearing branch, or connection capacity.",
            "Native output checker must pass after parent-owned freeze/run before interpreting this method candidate.",
        ],
        "source_hashes": {
            **{name: hash_value for name, hash_value in pins["source_files"].items()},
            **{rel(PACKET / name): hash_value for name, hash_value in pins["output_files"].items()},
            rel(MANUAL): sha(MANUAL),
            rel(PROFILE): sha(PROFILE),
            rel(ARCHIVE): sha(ARCHIVE),
            rel(MANIFEST): sha(MANIFEST),
            rel(STABLE_AUDIT): sha(STABLE_AUDIT),
            rel(RELATIVE_FIXTURE / "model.inp"): sha(RELATIVE_FIXTURE / "model.inp"),
            rel(RELATIVE_FIXTURE / "assessment.json"): sha(RELATIVE_FIXTURE / "assessment.json"),
            rel(Path(__file__).resolve()): sha(Path(__file__).resolve()),
        },
    }


def parse_dat_by_step(data: str, parser: Any) -> list[dict[str, Any]]:
    """Parse paired U/RF output states and retain each DAT token/radius."""
    step_matches = list(re.finditer(r"^\s*S\s*T\s*E\s*P\s+(\d+)\s*$", data, re.MULTILINE | re.IGNORECASE))
    if len(step_matches) != 3:
        fail(f"Expected 3 STEP markers in DAT, found {len(step_matches)}")
    block_pattern = re.compile(
        r"^\s*(displacements|forces)\s*\([^\n]*\btime\s+([0-9.EeDd+-]+)\s*\n",
        re.MULTILINE | re.IGNORECASE,
    )
    staged: dict[tuple[int, float], dict[str, Any]] = defaultdict(dict)
    for match in block_pattern.finditer(data):
        step_match = next((candidate for candidate in reversed(step_matches) if candidate.start() < match.start()), None)
        if step_match is None:
            fail("DAT output block precedes any STEP marker")
        step = int(step_match.group(1))
        total_time = fnum(match.group(2))
        key = (step, total_time)
        kind = "u" if match.group(1).lower() == "displacements" else "rf"
        if kind in staged[key]:
            fail(f"Duplicate {kind.upper()} block at step/time {key}")
        values: dict[int, list[float]] = {}
        radii: dict[int, list[float]] = {}
        raw_tokens: dict[int, list[str]] = {}
        for line in data[match.end():].splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[0].isdigit():
                node = int(fields[0])
                if node in values:
                    fail(f"Duplicate node {node} in {kind.upper()} state {key}")
                raw_tokens[node] = fields[1:]
                values[node] = [fnum(x) for x in fields[1:]]
                radii[node] = [parser._u_token_radius(x) if kind == "u" else parser._half_last_place(x)
                               for x in fields[1:]]
            elif values:
                break
        if not values:
            fail(f"Empty {kind.upper()} output state {key}")
        staged[key][kind] = values
        staged[key][kind + "_radius"] = radii
        staged[key][kind + "_tokens"] = raw_tokens
    results = []
    for (step, total_time), values in sorted(staged.items()):
        if "u" not in values or "rf" not in values:
            fail(f"Unpaired U/RF output state at step {step}, time {total_time}")
        if set(values["u"]) != set(values["rf"]):
            fail(f"U/RF node inventories differ at step {step}, time {total_time}")
        results.append({"step": step, "total_time": total_time,
                        "step_time": total_time - (step - 1), **values})
    if not results:
        fail("DAT contains no U/RF states")
    return results


def guard(*values: float) -> float:
    return FLOAT_GUARD * max(1.0, *(abs(float(x)) for x in values))


def interval_distance(actual: float, expected: float, radius: float, *guard_values: float) -> float:
    return max(0.0, abs(actual - expected) - radius - guard(actual, expected, *guard_values))


def assess_native(native_dir: Path) -> dict[str, Any]:
    native_dir = native_dir.resolve()
    if not native_dir.is_dir():
        fail(f"Native directory does not exist: {native_dir}")
    freeze = read_json(native_dir / "freeze.json")
    execution = read_json(native_dir / "execution.json")
    for name, expected in freeze["files_sha256"].items():
        if sha(native_dir / name) != expected:
            fail(f"Frozen input hash mismatch: {name}")
    output_hashes = execution.get("outputs_sha256", {})
    for required in ("model.dat", "native.stdout", "native.stderr"):
        if required not in output_hashes or not (native_dir / required).is_file():
            fail(f"Native execution does not pin required output {required}")
    for name, expected in output_hashes.items():
        if not (native_dir / name).is_file() or sha(native_dir / name) != expected:
            fail(f"Native output hash mismatch or missing output: {name}")
    if execution.get("native_solve_executed") is not True or execution.get("returncode") != 0:
        fail("Native execution is absent or did not terminate with return code 0")
    if execution.get("container_confirmed_terminal") is not True:
        fail("Native runner did not confirm a terminal solver state")
    if freeze.get("mechanical_acceptance") is not False:
        fail("Frozen coupon must remain non-acceptance evidence")
    frozen_sources = freeze.get("source_sha256", {})
    for path in (Path(__file__).resolve(), STABLE_AUDIT,
                 COUPON / "model.inp", COUPON / "model.json"):
        relative = rel(path)
        if frozen_sources.get(relative) != sha(path):
            fail(f"Freeze does not pin this exact checker/input dependency: {relative}")
    model_path, deck_path = native_dir / "model.json", native_dir / "model.inp"
    if sha(deck_path) != EXPECTED_COUPON_DECK_SHA256:
        fail("Frozen native deck does not match the prepared coupon input")
    model = read_json(model_path)
    deck = deck_path.read_text()
    parsed = parse_deck(deck)
    precision = token_helper()
    oracle = calculate_oracle(deck, model, parsed, precision)
    source_stdout = (native_dir / "native.stdout").read_text(errors="replace")
    source_stderr = (native_dir / "native.stderr").read_text(errors="replace")
    if "*ERROR" in (source_stdout + source_stderr).upper():
        fail("Native output contains a CalculiX error")
    stdout_normalized = " ".join(source_stdout.lower().split())
    if stdout_normalized.count("newton-raphson iterative procedure is active") < 3:
        fail("Native stdout does not show active Newton iterations for all three steps")
    if stdout_normalized.count("effects are turned off") < 3:
        fail("Native stdout does not show geometrical effects off in all three steps")
    if "nonlinear geometric effects are taken into account" in stdout_normalized:
        fail("Native stdout reports geometric nonlinear effects active")
    native_blocks = parse_dat_by_step((native_dir / "model.dat").read_text(errors="replace"), precision)
    node_ids = set(parsed["nodes"])
    for block in native_blocks:
        if set(block["u"]) != node_ids or set(block["rf"]) != node_ids:
            fail(f"Incomplete printed node inventory at step={block['step']} time={block['total_time']}")
    endpoint_by_step: dict[int, dict[str, Any]] = {}
    for step, target in EXPECTED_END_TIMES.items():
        candidates = [b for b in native_blocks if b["step"] == step]
        if not candidates:
            fail(f"No DAT output states for step {step}")
        final = max(candidates, key=lambda b: b["step_time"])
        if abs(final["total_time"] - target) > 1.0e-8 or abs(final["step_time"] - 1.0) > 1.0e-8:
            fail(f"Step {step} did not print its full endpoint: {final['total_time']}/{final['step_time']}")
        endpoint_by_step[step] = final

    # Native endpoint step q mapping: each source node appears on one scalar
    # SPRING2 per transverse component; the ground RF carries the support
    # action on the source body, while Q/GQ remain numerical SPRINGA endpoints.
    all_checks = []
    worst: dict[str, float] = defaultdict(float)
    first_nodes = oracle["first_nodes"]
    second_nodes = oracle["second_nodes"]
    point, axis = oracle["owner_point"], oracle["axis"]
    qnode, qground = oracle["springa_q_node"], oracle["springa_ground_node"]
    bmap = oracle["b"]
    support_ground = oracle["support_ground"]
    source_interpolation = model["source_interpolation"]
    wA = {int(n): float(w) for n, w in source_interpolation["first_master_nodes_and_weights"]}
    wB = {int(n): float(w) for n, w in source_interpolation["second_master_nodes_and_weights"]}
    for block in native_blocks:
        step = block["step"]
        lam = block["step_time"]
        if not -1.0e-9 <= lam <= 1.0 + 1.0e-8:
            fail(f"Out-of-step output time {lam} in step {step}")
        lam = min(1.0, max(0.0, lam))
        # CCX may ramp a replacement *CLOAD set from the prior step's ending
        # values. Until that transition is established for this exact pinned
        # input, only full-step endpoints use the current step's serialized
        # CLOAD vector as the analytical rank-one RHS. Intermediate checks
        # below are load-independent (MPC, SPRINGA law, support law).
        is_endpoint = abs(lam - 1.0) <= 1.0e-8
        base_loads = parsed["cloads"][step - 1]
        endpoint_loads = base_loads if is_endpoint else None
        q_expected = None
        force_expected = None
        if endpoint_loads is not None:
            rhs = math.fsum(bmap[key] * endpoint_loads[key] for key in bmap) / oracle["support_stiffness"]
            closed_candidate = rhs / (1.0 + oracle["springa_slope"]
                                       * math.fsum(x * x for x in bmap.values())
                                       / oracle["support_stiffness"])
            q_expected = closed_candidate if closed_candidate > 0.0 else rhs
            force_expected = table_force(q_expected, oracle["springa_table"])

        # Source interpolation projection computed independently on each 20-
        # node owner face; intervals account for every parsed DAT U token.
        pA = 0.0
        rA = 0.0
        pB = 0.0
        rB = 0.0
        for node, weight in wA.items():
            for dof, component in ((2, 1), (3, 2)):
                value = block["u"][node][component]
                radius = block["u_radius"][node][component]
                coefficient = axis[component] * weight
                pA += coefficient * value
                rA += abs(coefficient) * radius
        for node, weight in wB.items():
            for dof, component in ((2, 1), (3, 2)):
                value = block["u"][node][component]
                radius = block["u_radius"][node][component]
                coefficient = axis[component] * weight
                pB += coefficient * value
                rB += abs(coefficient) * radius
        q_from_source_points = pB - pA
        q_source_radius = rA + rB
        q_from_mpc = -math.fsum(
            coefficient * block["u"][node][dof - 1]
            for node, dof, coefficient in parsed["equation"][1:])
        q_mpc_radius = math.fsum(
            abs(coefficient) * block["u_radius"][node][dof - 1]
            for node, dof, coefficient in parsed["equation"][1:])
        q_node = block["u"][qnode][0]
        q_node_radius = block["u_radius"][qnode][0]
        q_interval_radius = q_node_radius + q_mpc_radius
        q_residual = q_node - q_from_mpc
        q_distance = interval_distance(q_node, q_from_mpc, q_interval_radius, q_node, q_from_mpc)
        q_source_distance = interval_distance(q_node, q_from_source_points,
                                              q_node_radius + q_source_radius, q_node,
                                              q_from_source_points)
        q_oracle_distance = None
        if q_expected is not None:
            q_oracle_distance = interval_distance(q_node, q_expected, q_node_radius, q_node, q_expected)
        for label, distance in (("direct_mpc_q_interval", q_distance),
                                ("source_projection_q_interval", q_source_distance)):
            worst[label] = max(worst[label], distance)
            if distance > 0.0:
                fail(f"q check failed ({label}) at step {step}, time {block['total_time']}: {distance} mm")
        if q_oracle_distance is not None:
            worst["analytical_q_output_interval_at_full_step_endpoints"] = max(
                worst["analytical_q_output_interval_at_full_step_endpoints"], q_oracle_distance)
            if q_oracle_distance > 0.0:
                fail(f"q endpoint rank-one oracle mismatch at step {step}: {q_oracle_distance} mm")

        # Native SPRINGA force and equal/opposite numerical ground force.
        rq = block["rf"][qnode][0]
        rg = block["rf"][qground][0]
        rqrad = block["rf_radius"][qnode][0]
        rgrad = block["rf_radius"][qground][0]
        q_lo, q_hi = q_node - q_node_radius, q_node + q_node_radius
        force_lo = table_force(q_lo, oracle["springa_table"])
        force_hi = table_force(q_hi, oracle["springa_table"])
        if force_lo > force_hi:
            force_lo, force_hi = force_hi, force_lo
        spring_rf_force_interval_distance = max(
            0.0,
            force_lo - (rq + rqrad) - guard(rq, force_lo),
            (rq - rqrad) - force_hi - guard(rq, force_hi),
        )
        worst["SPRINGA_Q_RF_vs_table_force_interval"] = max(
            worst["SPRINGA_Q_RF_vs_table_force_interval"], spring_rf_force_interval_distance)
        if spring_rf_force_interval_distance > 0.0:
            fail(f"SPRINGA Q endpoint RF does not match table force at step {step}, time {block['total_time']}")
        if abs(rq + rg) > rqrad + rgrad + guard(rq, rg):
            fail(f"SPRINGA Q/GQ endpoint action-reaction failed at step {step}, time {block['total_time']}")
        if abs(rg + rq) > rqrad + rgrad + guard(rg, rq):
            fail(f"Numerical SPRINGA ground force closure failed at step {step}")

        # Check the separate linear numerical supports at all source masters.
        source_joint_actions: dict[int, list[float]] = {n: [0.0, 0.0, 0.0]
                                                        for n in first_nodes + second_nodes}
        source_joint_radii: dict[int, list[float]] = {n: [0.0, 0.0, 0.0]
                                                      for n in first_nodes + second_nodes}
        support_records = []
        support_record_by_key = {}
        for node in first_nodes + second_nodes:
            for dof, component in ((2, 1), (3, 2)):
                ground_node = support_ground[(node, dof)]
                ground_rf = block["rf"][ground_node][component]
                ground_rf_radius = block["rf_radius"][ground_node][component]
                expected_ground_rf = -oracle["support_stiffness"] * block["u"][node][component]
                input_u_radius = block["u_radius"][node][component]
                support_radius = ground_rf_radius + oracle["support_stiffness"] * input_u_radius
                support_distance = interval_distance(ground_rf, expected_ground_rf, support_radius,
                                                     ground_rf, expected_ground_rf)
                worst["numerical_support_ground_RF"] = max(worst["numerical_support_ground_RF"], support_distance)
                if support_distance > 0.0:
                    fail(f"Numerical support endpoint RF mismatch at node {node}, dof {dof}, step {step}")
                support_record = {
                    "source_node": node, "dof": dof, "support_ground_node": ground_node,
                    "ground_RF_N": ground_rf, "ground_RF_radius_N": ground_rf_radius,
                    "source_U_mm": block["u"][node][component],
                    "support_ground_RF_expected_N": expected_ground_rf,
                }
                support_records.append(support_record)
                support_record_by_key[(node, dof)] = support_record

        # Recover physical owner forces/moments only at the three full-step
        # endpoints, where the serialized CLOAD set is the endpoint RHS.
        # Numerical support and SPRINGA grounds stay outside owner wrenches.
        owner_results = {}
        if endpoint_loads is not None:
            for node in first_nodes + second_nodes:
                for dof, component in ((2, 1), (3, 2)):
                    ground_node = support_ground[(node, dof)]
                    ground_rf = block["rf"][ground_node][component]
                    ground_rf_radius = block["rf_radius"][ground_node][component]
                    applied = endpoint_loads[(node, dof)]
                    recovered = -applied - ground_rf
                    recovered_radius = ground_rf_radius + guard(applied, ground_rf)
                    predicted = -force_expected * bmap[(node, dof)]
                    force_distance = interval_distance(recovered, predicted, recovered_radius,
                                                       recovered, predicted)
                    worst["owner_nodal_joint_action_at_full_step_endpoints"] = max(
                        worst["owner_nodal_joint_action_at_full_step_endpoints"], force_distance)
                    if force_distance > 0.0:
                        fail(f"Owner nodal action mismatch at node {node}, dof {dof}, step {step}")
                    source_joint_actions[node][component] = recovered
                    source_joint_radii[node][component] = recovered_radius
                    support_record_by_key[(node, dof)]["source_CLOAD_N"] = applied
                    support_record_by_key[(node, dof)].update({
                        "recovered_joint_action_N": recovered,
                        "recovered_joint_action_radius_N": recovered_radius,
                        "analytical_joint_action_N": predicted,
                    })
            for owner, nodes in ((oracle["first_owner"], first_nodes),
                                 (oracle["second_owner"], second_nodes)):
                force = [math.fsum(source_joint_actions[n][j] for n in nodes) for j in range(3)]
                moment = [math.fsum(cross(parsed["nodes"][n], source_joint_actions[n])[j]
                                    for n in nodes) for j in range(3)]
                force_radius = [math.fsum(source_joint_radii[n][j] for n in nodes) for j in range(3)]
                moment_radius = [
                    math.fsum(abs(parsed["nodes"][n][1]) * source_joint_radii[n][2]
                              + abs(parsed["nodes"][n][2]) * source_joint_radii[n][1] for n in nodes),
                    math.fsum(abs(parsed["nodes"][n][2]) * source_joint_radii[n][0]
                              + abs(parsed["nodes"][n][0]) * source_joint_radii[n][2] for n in nodes),
                    math.fsum(abs(parsed["nodes"][n][0]) * source_joint_radii[n][1]
                              + abs(parsed["nodes"][n][1]) * source_joint_radii[n][0] for n in nodes),
                ]
                ideal_force = vector_scale(axis, force_expected if owner == oracle["first_owner"] else -force_expected)
                ideal_moment = cross(point, ideal_force)
                f_errors = [interval_distance(force[j], ideal_force[j], force_radius[j], force[j], ideal_force[j])
                            for j in range(3)]
                m_errors = [interval_distance(moment[j], ideal_moment[j], moment_radius[j], moment[j], ideal_moment[j])
                            for j in range(3)]
                worst["owner_wrench_force_at_full_step_endpoints"] = max(
                    worst["owner_wrench_force_at_full_step_endpoints"], *f_errors)
                worst["owner_wrench_moment_at_full_step_endpoints"] = max(
                    worst["owner_wrench_moment_at_full_step_endpoints"], *m_errors)
                if any(error > 0.0 for error in f_errors + m_errors):
                    fail(f"Recovered {owner} owner-point wrench falls outside RF intervals at step {step}")
                owner_results[owner] = {
                    "recovered_force_N": force,
                    "recovered_force_component_interval_radii_N": force_radius,
                    "expected_owner_force_N": ideal_force,
                    "recovered_moment_global_origin_Nmm": moment,
                    "recovered_moment_component_interval_radii_Nmm": moment_radius,
                    "expected_owner_moment_global_origin_Nmm": ideal_moment,
                    "force_interval_distance_N": f_errors,
                    "moment_interval_distance_Nmm": m_errors,
                    "numerical_ground_forces_excluded": True,
                }

        u_errors = []
        if endpoint_loads is not None:
            u_oracle = {key: (endpoint_loads[key] - force_expected * bmap[key])
                        / oracle["support_stiffness"] for key in bmap}
            for key, expected_u in u_oracle.items():
                node, dof = key
                actual_u = block["u"][node][dof - 1]
                radius = block["u_radius"][node][dof - 1]
                distance = interval_distance(actual_u, expected_u, radius, actual_u, expected_u)
                u_errors.append(distance)
                worst["master_displacement_oracle_at_full_step_endpoints"] = max(
                    worst["master_displacement_oracle_at_full_step_endpoints"], distance)
                if distance > 0.0:
                    fail(f"Rank-one U endpoint oracle mismatch at step {step}, DOF {key}")
        q_expected_distance = (interval_distance(q_node, q_expected, q_node_radius, q_node, q_expected)
                              if q_expected is not None else None)
        state_record = {
            "step": step,
            "total_time": block["total_time"],
            "step_load_factor": lam,
            "is_full_step_endpoint": abs(lam - 1.0) <= 1.0e-8,
            "q_from_native_Q_U_mm": q_node,
            "q_Q_U_token_radius_mm": q_node_radius,
            "q_from_source_interpolation_pB_minus_pA_mm": q_from_source_points,
            "q_source_interpolation_radius_mm": q_source_radius,
            "q_from_serialized_direct_MPC_mm": q_from_mpc,
            "q_direct_MPC_residual_mm": q_residual,
            "q_direct_MPC_interval_distance_mm": q_distance,
            "q_source_projection_interval_distance_mm": q_source_distance,
            "q_rank_one_oracle_mm": q_expected,
            "q_rank_one_oracle_interval_distance_mm": q_expected_distance,
            "pA_source_projection_mm": pA,
            "pB_source_projection_mm": pB,
            "SPRINGA_Q_RF_N": rq,
            "SPRINGA_Q_RF_radius_N": rqrad,
            "SPRINGA_Q_RF_table_force_interval_N": [force_lo, force_hi],
            "SPRINGA_Q_RF_table_interval_distance_N": spring_rf_force_interval_distance,
            "SPRINGA_ground_RF_N_excluded_from_physical_owner_balance": rg,
            "SPRINGA_hand_table_force_N": (force_expected if force_expected is not None else None),
            "SPRINGA_law_closed_or_open": ("closed" if q_node > 0.0 else "open"),
            "source_support_and_joint_recovery": support_records,
            "owner_wrenches": owner_results,
            "maximum_master_U_interval_distance_mm": max(u_errors, default=0.0),
            "analytical_load_oracle_applicable": endpoint_loads is not None,
            "intermediate_owner_wrench_check": (
                "not_checked_load_ramp_not_independently_pinned" if endpoint_loads is None else "checked"
            ),
        }
        all_checks.append(state_record)

    endpoint_rows = []
    for step, block in sorted(endpoint_by_step.items()):
        check_row = next(row for row in all_checks
                         if row["step"] == step and abs(row["total_time"] - block["total_time"]) < 1.0e-12)
        endpoint_rows.append({"step": step, "total_time": block["total_time"],
                              "full_step_endpoint_checked": check_row["is_full_step_endpoint"],
                              "q_mm": check_row["q_from_native_Q_U_mm"],
                              "force_N": check_row["SPRINGA_Q_RF_N"]})
    if len(endpoint_rows) != 3 or not all(row["full_step_endpoint_checked"] for row in endpoint_rows):
        fail("Did not check all three full-step endpoints")

    return {
        "schema": "current_spr489_direct_scalar_native_output_audit/v1",
        "status": "PASS_NATIVE_SPR489_DIRECT_SCALAR_METHOD_COUPON",
        "native_solve_executed": True,
        "mechanical_acceptance": False,
        "qualified_for_design": False,
        "frame_or_joint_qualification": False,
        "input_freeze_sha256": sha(native_dir / "freeze.json"),
        "execution_sha256": sha(native_dir / "execution.json"),
        "native_dat_sha256": sha(native_dir / "model.dat"),
        "source_input_deck_sha256": sha(native_dir / "model.inp"),
        "source_model_json_sha256": sha(native_dir / "model.json"),
        "case_id": "k12-rear",
        "source_row_id": "SPR489",
        "source_owner_order": [oracle["first_owner"], oracle["second_owner"]],
        "output_state_count": len(all_checks),
        "full_step_endpoints": endpoint_rows,
        "all_recorded_states": all_checks,
        "worst_interval_excesses": dict(worst),
        "solver_method": oracle["step_semantics"],
        "limits": [
            "This pass validates only the direct-scalar known-answer method coupon.",
            "The 100 N/mm SPRING2 supports and 100 mm SPRINGA ground endpoint are numerical fixtures, not frame or floor properties.",
            "The physical owner force/moment recovery uses only source master DOFs; numerical supports and q ground RF are excluded from owner wrench.",
            "No K12-rear frame response, joint capacity, floor branch, design criterion, or acceptance conclusion is established.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-audit", action="store_true",
                       help="write the independent source-deck/rank-one readiness audit only")
    group.add_argument("--native-dir", type=Path,
                       help="check a parent-frozen/parent-run packet; never invokes CalculiX")
    parser.add_argument("--output", type=Path,
                        help="optional audit JSON path (default: native-dir/direct-scalar-response-audit.json)")
    args = parser.parse_args()
    if args.input_audit:
        result = input_audit()
        out = args.output or (METHOD / "input-readiness-audit.json")
    else:
        result = assess_native(args.native_dir)
        out = args.output or (args.native_dir / "direct-scalar-response-audit.json")
    out = out.resolve()
    if out.exists():
        fail(f"Refusing to overwrite audit output: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(result["status"])
    print(out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
