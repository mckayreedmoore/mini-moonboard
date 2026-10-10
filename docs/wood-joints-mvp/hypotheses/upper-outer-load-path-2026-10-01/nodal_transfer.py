#!/usr/bin/env python3
"""Audit source-MPC load transfer without solving or inferring cut tractions.

The source point actions and distributed FE nodal actions have the same
whole-body wrench. Their cut-selected sums can differ. Neither sum supplies
the missing traction field in the bored, finished section.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
UPPER = "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/upper-joints.json"
UPPER_HASH = "0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6"
GEOMETRY = "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/geometry.json"
GEOMETRY_HASH = "2ba66f4242b59e73a7dfc14a0b21d20d1f2710b9f835d60fce569eb73353fe91"
BLOCKS = ("top_outer_left_cleat", "top_outer_right_cleat")
CASES = ("a1-rear", "a12-rear", "k12-rear")
OUTPUT = HERE / "nodal-transfer.json"
PLANE_TOL = 1e-6


class TransferError(ValueError):
    """An input or transfer identity is not usable."""


def require(condition, message):
    if not condition:
        raise TransferError(message)


def finite(value):
    require(isinstance(value, (int, float)) and not isinstance(value, bool), "not a numeric value")
    require(math.isfinite(value), "nonfinite value")
    return float(value)


def vector(values):
    require(isinstance(values, (list, tuple)) and len(values) == 3, "not a three-vector")
    return [finite(v) for v in values]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_pinned(relative, expected, root=ROOT):
    path = root / relative
    require(sha(path) == expected, f"changed source: {relative}")
    return json.loads(path.read_bytes())


def canonical(data):
    return (json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def add(a, b):
    return [math.fsum((x, y)) for x, y in zip(a, b, strict=True)]


def sub(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def scale(a, s):
    return [s * x for x in a]


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def sums(vectors):
    return [math.fsum(v[i] for v in vectors) for i in range(3)]


def moment_radius(arm, radius):
    return [abs(arm[1])*radius[2]+abs(arm[2])*radius[1],
            abs(arm[2])*radius[0]+abs(arm[0])*radius[2],
            abs(arm[0])*radius[1]+abs(arm[1])*radius[0]]


def wrench(actions, datum):
    forces, moments, radii, mradii = [], [], [], []
    for a in actions:
        arm = sub(a["point_mm"], datum)
        forces.append(a["force_n"])
        moments.append(cross(arm, a["force_n"]))
        radii.append(a["radius_n"])
        mradii.append(moment_radius(arm, a["radius_n"]))
    return {"force_n": sums(forces), "moment_nmm": sums(moments),
            "force_radius_n": sums(radii), "moment_radius_nmm": sums(mradii)}


def near(a, b, tolerance, label):
    require(max(abs(x-y) for x, y in zip(a, b, strict=True)) <= tolerance, label)


def node_id(value):
    require(type(value) is int or (isinstance(value, str) and value.isascii() and value.isdigit()),
            "node ID must be a discrete integer")
    result = int(value)
    require(result > 0, "node ID must be positive")
    return result


def dof_key(node, dof):
    node = node_id(node)
    dof = node_id(dof)
    require(dof in (1, 2, 3), "DOF must be translational (1–3)")
    return node, dof


class MPCExpansion:
    """Transpose of the recorded displacement equations, without pruning."""

    def __init__(self, equations, physical_owner, fixed_nodes=()):
        self.owner = {node_id(n): body for n, body in physical_owner.items()}
        require(len(self.owner) == len(physical_owner), "duplicate physical node ID")
        self.fixed = {(node_id(n), d) for n in fixed_nodes for d in (1, 2, 3)}
        self.equations = {}
        self.cache = {}
        self.visiting = set()
        for terms in equations:
            require(bool(terms), "empty MPC")
            require(all(isinstance(term, (list, tuple)) and len(term) == 3 for term in terms), "invalid MPC term")
            terms = [(*dof_key(node, dof), finite(coefficient)) for node, dof, coefficient in terms]
            pivot = terms[0][:2]
            require(pivot not in self.equations, "duplicate MPC pivot")
            require(finite(terms[0][2]) != 0, "zero MPC pivot")
            self.equations[pivot] = terms

    def expand(self, key):
        require(isinstance(key, (list, tuple)) and len(key) == 2, "invalid DOF key")
        key = dof_key(*key)
        if key in self.cache:
            return self.cache[key]
        require(key not in self.visiting, "MPC cycle")
        self.visiting.add(key)
        try:
            if key in self.fixed:
                result = {}
            elif key in self.equations:
                terms = self.equations[key]
                pivot = finite(terms[0][2])
                collected = defaultdict(list)
                for node, dof, coefficient in terms[1:]:
                    multiplier = -finite(coefficient) / pivot
                    for target, weight in self.expand((node, dof)).items():
                        collected[target].append(multiplier * weight)
                result = {k: math.fsum(v) for k, v in collected.items()}
                result = {k: v for k, v in result.items() if v != 0}
            else:
                require(key[0] in self.owner and key[1] in (1, 2, 3), f"unresolved physical DOF: {key}")
                result = {key: 1.0}
            self.cache[key] = result
            return result
        finally:
            self.visiting.remove(key)

    def receiver(self, key, body):
        result = self.expand(key)
        require(bool(result), "receiver expands to an empty/fixed support")
        require(all(self.owner[n] == body for n, _ in result), "receiver crosses physical ownership")
        return result


def owner_map(model):
    result = {}
    for body, nodes in model["physical_body_nodes"].items():
        for node in nodes:
            node = node_id(node)
            require(node not in result, "physical node has multiple owners")
            result[node] = body
    return result


def unique(rows, key):
    result = {}
    for row in rows:
        value = row[key]
        require(value not in result, f"duplicate {key}: {value}")
        result[value] = row
    return result


def validate_case_identity(model, response, case, candidate, revision, model_hash):
    for label, source in (("model", model), ("response", response)):
        require(source["case_id"] == case, f"wrong {label} case")
        require(source["candidate"] == candidate, f"wrong {label} candidate")
        require(source["geometry_revision_id"] == revision, f"wrong {label} geometry revision")
    require(response["source_input_model_json_sha256"] == model_hash, "response/model binding mismatch")


def nodal_action(model, expansion, row, body, scalars):
    terms = defaultdict(list)
    radius_terms = defaultdict(list)
    for key, scalar, radius in scalars:
        scalar, radius = finite(scalar), finite(radius)
        require(radius >= 0, "negative force radius")
        for target, weight in expansion.receiver(key, body).items():
            terms[target].append(weight * scalar)
            radius_terms[target].append(abs(weight) * radius)
    nodes = sorted({n for n, _ in terms})
    result = []
    for n in nodes:
        result.append({"node": n, "point_mm": vector(model["nodes"][str(n)]),
                       "force_n": [math.fsum(terms[n, d]) for d in (1, 2, 3)],
                       "radius_n": [math.fsum(radius_terms[n, d]) for d in (1, 2, 3)]})
    side = "first" if row["first"] == body else "second"
    point = vector(row.get(side + "_point", row["point"]))
    reference = {"point_mm": point, "force_n": vector(row["force_on_"+side+"_xyz_n"]),
                 "radius_n": vector(row["force_rounding_radius_xyz_n"])}
    observed, expected = wrench(result, point), wrench([reference], point)
    near(observed["force_n"], expected["force_n"], 1e-7, "expanded receiver force mismatch")
    near(observed["moment_nmm"], expected["moment_nmm"], 1e-5, "expanded receiver point-moment mismatch")
    return result, reference, observed


def selected_wrench(actions, section, trace, side="positive"):
    require(trace in ("minus", "plus") and side in ("positive", "negative"), "unknown cut trace")
    origin = section["plane_origin_xyz_mm"]
    normal = section["section_plane_normal_global_xyz"]
    require(abs(dot(normal, normal)-1) <= 1e-8, "nonunit section normal")
    chosen = []
    for a in actions:
        distance = dot(sub(a["point_mm"], origin), normal)
        positive = distance > PLANE_TOL or (abs(distance) <= PLANE_TOL and trace == "minus")
        if positive == (side == "positive"):
            chosen.append(a)
    return {"selected_action_count": len(chosen), "external_wrench": wrench(chosen, origin)}


def audit_block(model, increment, upper_balance, sections):
    body = upper_balance["block"]
    owners = owner_map(model)
    expansion = MPCExpansion(model["equations"], owners, model["fixed_nodes"])
    spring_rows = unique(model["springs"], "source_row_id")
    springa_rows = unique(model["unilateral_springa_bindings"], "source_row_id")
    local = unique(increment["retained_bilateral_spring2_components"], "source_row_id")
    axial = unique(increment["springa_components"], "source_row_id")
    incident = {n:r for n,r in increment["physical_connection_forces"].items() if body in (r["first"],r["second"])}
    require(len(incident) == 16, "missing or extra outer-block connections")
    point_actions, nodal_actions, comparisons = [], [], []
    datum = vector(upper_balance["datum_xyz_mm"])
    receiver_forces = defaultdict(list)
    for name, row in sorted(incident.items()):
        first_side = row["first"] == body
        sign = 1.0 if first_side else -1.0
        position = 0 if first_side else 1
        scalars = []
        for source_id in row["source_row_ids"]:
            if source_id in spring_rows:
                spring, component = spring_rows[source_id], local[source_id]
                require(spring["name"] == name, "spring/connection name mismatch")
                require(component["rf_action_reaction_passed"] is True and component["rf_kdu_intervals_intersect"] is True, "failed bilateral source gate")
                key = dof_key(spring["nodes"][position], spring["dof"])
                scalars.append((key, sign*component["force_on_first_local_N"], component["force_rounding_radius_local_N"]))
            elif source_id in springa_rows:
                binding, component = springa_rows[source_id], axial[source_id]
                require(binding["name"] == name, "springa/connection name mismatch")
                require(component["native_endpoint_action_reaction_passed"] is True and component["table_force_interval_intersects_native_rf"] is True, "failed unilateral source gate")
                key = dof_key(binding["source_projection_nodes"][position], binding["source_projection_dof"])
                scalars.append((key, sign*component["native_endpoint_internal_force_N"], component["native_endpoint_internal_radius_N"]))
            else:
                raise TransferError("unmapped scalar source row")
        cloud, point, observed = nodal_action(model, expansion, row, body, scalars)
        receiver = row["second"] if first_side else row["first"]
        for a in cloud:
            a.update(source_name=name, receiver=receiver)
        point.update(source_name=name, receiver=receiver)
        nodal_actions.extend(cloud)
        point_actions.append(point)
        receiver_forces[receiver].extend(cloud)
        comparisons.append({"source_name":name, "scalar_source_ids":row["source_row_ids"],
                            "nodal_force_entry_count":len(cloud), "force_n":observed["force_n"],
                            "moment_about_attachment_point_nmm":observed["moment_nmm"]})
    for receiver, cloud in receiver_forces.items():
        observed = wrench(cloud, datum)
        expected = upper_balance["receiver_actions_on_block"][receiver]
        near(observed["force_n"], expected["force_n"], 1e-7, "receiver-group force mismatch")
        near(observed["moment_nmm"], expected["moment_at_block_datum_nmm"], 1e-5, "receiver-group moment mismatch")
    for node, load in model["physical_body_loads"][body].items():
        node = node_id(node)
        require(owners[node] == body, "body load has wrong owner")
        a = {"node":node, "point_mm":vector(model["nodes"][str(node)]),
             "force_n":scale(vector(load), finite(increment["load_factor"])), "radius_n":[0.0]*3,
             "source_name":f"{body}/gravity/{node}", "receiver":None}
        nodal_actions.append(a)
        point_actions.append(a)
    full = wrench(nodal_actions, datum)
    near(full["force_n"], upper_balance["force_residual_n"], 1e-7, "whole-body force mismatch")
    near(full["moment_nmm"], upper_balance["moment_residual_nmm"], 1e-5, "whole-body moment mismatch")
    require(max(abs(v) for v in full["force_n"]) <= 0.1 and max(abs(v) for v in full["moment_nmm"]) <= 2, "source body equilibrium limit exceeded")
    for key, tolerance in (("force", 1e-7), ("moment", 1e-5)):
        units = "n" if key == "force" else "nmm"
        require(all(abs(v) <= r + tolerance for v, r in zip(full[f"{key}_{units}"], full[f"{key}_radius_{units}"], strict=True)), "nodal RF intervals do not cover whole-body residual")
    cuts = []
    for section in sections:
        for trace in ("minus", "plus"):
            point = selected_wrench(point_actions, section, trace)
            node = selected_wrench(nodal_actions, section, trace)
            opposite = selected_wrench(nodal_actions, section, trace, "negative")
            complete = wrench(nodal_actions, section["plane_origin_xyz_mm"])
            for key in ("force_n", "moment_nmm"):
                near(add(node["external_wrench"][key], opposite["external_wrench"][key]), complete[key], 1e-7, "cut partition loses an action")
            cuts.append({"sample_id":section["sample_id"], "sample_kind":section["sample_kind"],
                         "trace":trace, "source_point_positive_side":point,
                         "source_nodal_positive_side":node, "source_nodal_negative_side":opposite,
                         "point_minus_nodal_force_n":sub(point["external_wrench"]["force_n"],node["external_wrench"]["force_n"]),
                         "point_minus_nodal_moment_nmm":sub(point["external_wrench"]["moment_nmm"],node["external_wrench"]["moment_nmm"]),
                         "physical_cut_traction_established":False})
    return {"block":body, "case":model["case_id"], "increment_index":upper_balance["increment_index"],
            "load_factor":increment["load_factor"], "datum_mm":datum,
            "native_block_element_count":model["body_geometry"][body]["element_count"],
            "native_block_physical_node_count":len(model["physical_body_nodes"][body]),
            "native_finished_bores_modeled":model["body_geometry"][body]["geometry_record"]["geometry_diagnostics"]["gross_cut_and_bore_stiffness_modeled"],
            "whole_body_wrench":full, "connection_transfer_checks":comparisons,
            "distributed_connection_and_gravity_actions":nodal_actions, "cut_attribution_comparisons":cuts}


def produce():
    upper = read_pinned(UPPER, UPPER_HASH)
    geometry = read_pinned(GEOMETRY, GEOMETRY_HASH)
    require(upper["geometry_revision_id"] == geometry["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1", "wrong geometry revision")
    require(upper["candidate"] == geometry["candidate"] == "compact-floor-flush-wood-joints-development", "wrong candidate")
    for source in (upper, geometry):
        for flag in ("complete_joint_resistance_established", "six_case_envelope_established", "drilling_released", "fabrication_released", "structural_released", "reviewed_geometry_changed", "native_solve_executed_by_this_packet"):
            require(source[flag] is False, f"unexpected source claim: {flag}")
    sections = {s["block"]:s["sampled_sections"] for s in geometry["block_exact_sections"] if s["block"] in BLOCKS}
    require(set(sections) == set(BLOCKS) and all(len(s)==5 for s in sections.values()), "missing source sections")
    balances = {}
    for b in upper["block_balances"]:
        if b["block"] in BLOCKS:
            key = (b["case"], b["block"], b["increment_index"])
            require(key not in balances, "duplicate source body state")
            balances[key] = b
    require(len(balances) == 42, "missing source body states")
    pins = {UPPER:UPPER_HASH, GEOMETRY:GEOMETRY_HASH}
    records = []
    for case in CASES:
        files = upper["source_cases"][case]
        for name in ("model", "response", "all_body_audit"):
            spec = files[name]
            pins[spec["path"]] = spec["sha256"]
        model = read_pinned(files["model"]["path"], files["model"]["sha256"])
        response = read_pinned(files["response"]["path"], files["response"]["sha256"])
        audit = read_pinned(files["all_body_audit"]["path"], files["all_body_audit"]["sha256"])
        require(audit["status"] == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS", "failed parent source audit")
        validate_case_identity(model, response, case, upper["candidate"], upper["geometry_revision_id"], files["model"]["sha256"])
        require(len(response["increments"]) == 7, "wrong source increment count")
        for i, increment in enumerate(response["increments"]):
            for flag in ("mpc_interval_checks_passed", "retained_bilateral_checks_passed", "springa_law_checks_passed", "selected_floor_complementarity_passed", "inactive_floor_tangent_no_restraint_or_reaction_passed", "raw_balance_passed", "rounding_interval_balance_passed"):
                require(increment[flag] is True, f"failed increment gate: {flag}")
            for body in BLOCKS:
                balance = balances[case,body,i]
                require(balance["load_factor"] == increment["load_factor"], "misjoined load factor")
                records.append(audit_block(model, increment, balance, sections[body]))
    peak_f = max(abs(v) for r in records for c in r["cut_attribution_comparisons"] for v in c["point_minus_nodal_force_n"])
    peak_m = max(abs(v) for r in records for c in r["cut_attribution_comparisons"] for v in c["point_minus_nodal_moment_nmm"])
    return {"schema":"upper_outer_source_nodal_transfer/v1", "status":"CONDITIONAL_SOURCE_MPC_TRANSFER_AND_CUT_ATTRIBUTION_ONLY",
            "candidate":upper["candidate"], "geometry_revision_id":upper["geometry_revision_id"],
            "producer_sha256":sha(Path(__file__)), "source_pins":pins,
            "counts":{"blocks":2, "cases":3, "body_states":len(records), "connection_transfer_checks":len(records)*16, "cut_trace_comparisons":len(records)*10},
            "max_point_minus_nodal_cut_component_force_n":peak_f, "max_point_minus_nodal_cut_component_moment_nmm":peak_m,
            "source_nodal_force_distribution_established":True,
            "physical_finished_cut_traction_established":False,
            "complete_joint_resistance_established":False, "six_case_envelope_established":False,
            "native_solve_executed_by_this_packet":False, "reviewed_geometry_changed":False,
            "drilling_released":False, "fabrication_released":False, "structural_released":False,
            "limits":["Nodal actions are equivalent generalized loads of the gross C3D20 source, not a physical bearing/contact-pressure field.",
                      "Selecting nodes by cut location does not integrate the FE stress field on a cut through an element.",
                      "Point action cut resultants and cut-selected nodal load sums preserve whole-body wrench but can differ locally.",
                      "Finished bored-section regions require an applicable traction/load-transfer model; no regional share is assigned."],
            "records":records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        result = produce()
        payload = canonical(result)
        if args.verify:
            require(OUTPUT.read_bytes() == payload, "output differs from exact replay")
        else:
            OUTPUT.write_bytes(payload)
        print(json.dumps({"status":"PASS_NODAL_TRANSFER_REPLAY" if args.verify else "WROTE_NODAL_TRANSFER", "counts":result["counts"],
                          "max_cut_force_difference_n":result["max_point_minus_nodal_cut_component_force_n"],
                          "max_cut_moment_difference_nmm":result["max_point_minus_nodal_cut_component_moment_nmm"]}))
        return 0
    except (TransferError, OSError, KeyError, TypeError, ValueError) as error:
        print(f"FAIL_NODAL_TRANSFER: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
