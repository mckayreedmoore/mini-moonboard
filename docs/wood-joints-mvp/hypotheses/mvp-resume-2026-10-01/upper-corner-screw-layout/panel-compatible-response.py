"""Compare saved compatible original104 panel actions with frozen references.

Import is inert. Preparation authenticates files and joins static identities.
Build reads the accepted states in one receipt-bound action export, preserves
the full fourteen-state disposition inventory, reuses the original
physical nodal footprints and pure resistance helpers, and solves no system.
"""

from __future__ import annotations

import argparse
import ast
import bisect
import gzip
import hashlib
import json
import math
import platform
import re
import time
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/panel-compatible-response"
ORIGINAL = HERE / "operators-attempt02"
LOCAL = HERE / "rawlocal/panel-local-net-completion"
N14 = HERE / "panel-reference-completion.py"
LOCAL_HELPER = LOCAL / "original104-permanent-attempt01/producer.py.snapshot"
GEOMETRY = LOCAL / "attempt05/geometry.json"
LOCAL_SUMMARY = LOCAL / "attempt05/summary.json"
CATALOG = HERE / "rawlocal/panel-reference-completion/attempt01/summary.json"
MATERIAL = ROOT / "fea/current_response_materials.py"
PANEL = ROOT / "fea/reinforced_panel_checks.py"
WRENCH = HERE.parent / "top_corner_actions.py"
LATERAL = HERE.parent / "panel-attachment/lateral_reference.py"
BASE = HERE.parent.parent / "mvp-acceleration-2026-09-28"
DOF = BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof"
PARSER = BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PERMANENT = "dead-only"
REQUIRED_STATES = {(case, gap) for case in (*CASES, PERMANENT) for gap in (0., 1.)}
PINS = {
    N14: "1943198db40ed6729f6c93c3a1196e1642d3a3843fb2bbf5e826aa6b35a116b1",
    LOCAL_HELPER: "8034adfee0f052aebf3f51aecfaf07a82e9cdcee5264e3de0c5f79b84b6f93cd",
    GEOMETRY: "758b5156f0d5ce9d0c46a0fd7f29b47d59fe408a122c6eec7e4d7de34fc0dd4c",
    LOCAL_SUMMARY: "61223ff7ffae4a4cc7bca567c0d3a2aac1fc69674795a7cfe0f1f06c303bf4b3",
    LOCAL / "attempt05/method-validation.json": "7575cf1af8ee9342d8992cfc26e8f39c3eb6da90173bf1620d03bf1c9f51e49c",
    CATALOG: "dfa8a93d686e82b5ee8099ad55fce66f436d1720ab5fb51b4cdf6c1b2761c6f5",
    ORIGINAL / "model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    ORIGINAL / "model-inputs.json": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    ORIGINAL / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    ORIGINAL / "operators.npz": "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    ORIGINAL / "B.npz": "d109f7db25cb05619e26560e501e7e82f3608fdbb3580f76e64f9beae916128a",
    MATERIAL: "72af0456272d91282928014d8fde557d347e36df6b7bdf23bcc41ef923d0d135",
    PANEL: "1cf47584c36ab5c513ee74072f66782b0aa3907cca6b0ee940218d84693d634d",
    WRENCH: "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
    LATERAL: "8bcf31f3e69338de5f16824411ae14567187ce6b92cd05a61f7de3be0de7fbb2",
    DOF: "532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d",
    PARSER: "7abfeb3b02843588651b440dba4a86ae3f85106557383225a50c09b5cb080632",
}
FLAGS = dict.fromkeys(("N14_accepted", "complete_panel_acceptance", "complete_joint_acceptance",
    "physical_release", "fabrication_release", "proposal_adopted", "geometry_hardware_or_load_changed",
    "source_pipeline_native_CAD_or_frame_run", "tests_or_review_loop_run"), False)


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def authenticate(pins):
    for path, digest in pins.items():
        require(path.is_file() and sha(path) == digest, "changed frozen source: " + str(path))


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(len(digest) == 64 and (path not in pins or pins[path] == digest), "conflicting source binding")
    pins[path] = digest


def static_sources():
    pins = {**PINS, Path(__file__).resolve(): sha(__file__)}
    authenticate(pins)
    node = next(n for n in ast.parse(N14.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == "definitions")
    namespace = {"ast": ast, "SimpleNamespace": SimpleNamespace, "require": require}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(N14), "exec"), namespace)  # noqa: S102 -- pinned pure definition loader
    definitions = namespace["definitions"]
    local = definitions(LOCAL_HELPER,
        ("dot", "cross", "radius_at", "union_length", "width_at", "section", "elastic_field", "circular_kt",
         "local_screw", "directional_ligaments", "net_rows"),
        {"math": math, "bisect": bisect, "defaultdict": defaultdict, "require": require},
        ("N", "T", "HEAD_R", "SCREW_R", "HEAD_ANGLE_DEG", "PLANAR", "MEMBRANE", "FACE_BEARING"))
    material = definitions(MATERIAL, ("equivalent_layers",), {"math": math, "validate_constants": tuple,
        "WOOD_E": 1600000*local.N/25.4**2, "APA_EA": (3150000*local.N/304.8, 5100000*local.N/304.8),
        "APA_EI": (90500*local.N*25.4**2/304.8, 320000*local.N*25.4**2/304.8), "APA_GA": 50500*local.N/25.4})
    model, inputs, rows, geometry = map(read, (ORIGINAL / "model.json", ORIGINAL / "model-inputs.json",
                                              ORIGINAL / "row-identities.json", GEOMETRY))
    targets = model["material_binding"]["panel_targets"]
    layers = material.equivalent_layers(local.T, targets["ea_n_per_mm"], targets["ei_nmm"], targets["ga_n_per_mm"])
    require(json.dumps(layers, sort_keys=True) == json.dumps(read(LOCAL_SUMMARY)["material"]["equivalent_layers"], sort_keys=True),
            "equivalent-layer material changed")
    require(model["modeled_mass_kg"] == 224.9499553141194
            and model["dead_load_factor"] == 1.1111358300342407
            and model["material_binding"]["panel_group_factor"] == 1
            and geometry["counts"] == {"screw": 66, "hold": 142, "LED": 132}, "original geometry/material/mass scope differs")
    members = {m["member_id"]: m for m in inputs["members"]}
    for panel, data in geometry["panels"].items():
        binding = data["STEP_binding"]
        bind(pins, ROOT / binding["path"], binding["file_sha256"])
        require(binding == members[panel]["current_finished_step_binding"], "panel source STEP binding changed")
    axial, lateral = {}, defaultdict(list)
    for row in rows:
        axis = row["row_id"].split("/")[0]
        if row["ownership"]["role"] == "non_qualifying_parametric_screw_withdrawal":
            require(axis not in axial, "repeated screw axial row")
            axial[axis] = row
        elif row["ownership"]["role"] == "panel_screw_lateral_plane":
            lateral[axis].append(row)
    axes = []
    for connection in inputs["connections"]:
        if connection["kind"] != "panel_screw":
            continue
        axis, source = connection["axis_id"], connection["source_record"]
        panel, receiver = source["panel_member"], source["receiver_member"]
        components = [*lateral[axis], axial[axis]]
        require(len(components) == 3 and all(r["ownership"]["point_mm"] == axial[axis]["ownership"]["point_mm"]
            and {r["ownership"]["first_body"], r["ownership"]["second_body"]} == {panel, receiver} for r in components),
            "screw row/host/datum join differs")
        point = axial[axis]["ownership"]["point_mm"]
        hole = next(h for h in geometry["panels"][panel]["openings"] if h.get("axis_id") == axis)
        require(math.dist(hole["xy_mm"], [local.dot(point, b) for b in geometry["panels"][panel]["basis"][:2]]) < 1e-8,
                "force station differs from frozen current cavity")
        axes.append({"axis_id": axis, "panel": panel, "receiver": receiver, "point_mm": point,
            "rows": [r["row"] for r in components], "axis": connection["axis_xyz"], "source_axis_record": source,
            "receiver_geometry": members[receiver]["reduced_geometry_descriptor"]})
    require(len(axes) == len(axial) == len(lateral) == 66 and len(rows) == 1888
            and [r["row"] for r in rows] == list(range(1888)), "66-screw/canonical row census differs")
    authenticate(pins)
    return SimpleNamespace(pins=pins, definitions=definitions, local=local, model=model, inputs=inputs,
                           rows=rows, axes=axes, geometry=geometry, layers=layers)


def action_sources(data, actions, receipt_sha256):
    actions = Path(actions).resolve()
    require(len(receipt_sha256) == 64 and sha(actions / "receipt.json") == receipt_sha256,
            "parent-frozen action receipt identity differs")
    bind(data.pins, actions / "receipt.json", receipt_sha256)
    receipt = read(actions / "receipt.json")
    require(receipt["status"] == "COMPLETE_SAVED_COUPLED_ACTION_RECONCILIATION_NOT_RESISTANCE_QUALIFICATION",
            "completed reconciled action export required")
    aliases = {}
    for name, digest in receipt["source_sha256"].items():
        path = ROOT / name
        if path.is_file() and sha(path) == digest:
            bind(data.pins, path, digest)
        else:
            snapshot = actions / "producer.py.snapshot"
            require(path.suffix == ".py" and receipt["output_sha256"].get(snapshot.name) == digest
                    and sha(snapshot) == digest, "changed source has no authenticated executed producer snapshot: " + name)
            bind(data.pins, snapshot, digest)
            aliases[name] = str(snapshot.relative_to(ROOT))
    for name in ("summary.json", "inputs.json", "source-row-response.npz", "source-row-map.json",
                 "body-actions.jsonl.gz", "producer.py.snapshot"):
        require(name in receipt["output_sha256"], "required action artifact absent: " + name)
        bind(data.pins, actions / name, receipt["output_sha256"][name])
    report, inputs = read(actions / "summary.json"), read(actions / "inputs.json")
    inventory, accepted = state_inventory(data.pins, report)
    require(receipt["required_state_inventory"] == inventory
            and report["completed_states"] == len(accepted)
            and report["action_exports_complete_for_accepted_states"] is True
            and report["all14_required_states"] is (accepted == REQUIRED_STATES)
            and report["action_state_scope"] == ("all14_accepted_states" if accepted == REQUIRED_STATES else "accepted_state_subset")
            and report["counts"]["required_states"] == 14
            and report["counts"]["accepted_states"] == len(accepted)
            and report["counts"]["rejected_force_fields_exported"] == 0,
            "receipt/summary accepted-state inventory or completion differs")
    require(report["source_force_basis"] == inputs["source_force_basis"] == "reviewed104_coupled_knee_sensitivity"
            and inputs["dead_load_factor"] == data.model["dead_load_factor"], "compatible action force/mass scope differs")
    # This source field identifies the actual prepared wood-port request.
    request_path = ROOT / inputs["preparation"] / "wood-port-request.json"
    require(request_path in data.pins, "prepared point-action request missing from consumed closure")
    request = read(request_path)
    panels = set(data.geometry["panels"])
    require(not any(t["member_id"] in panels for terms in request["new_wood_port_terms"] for t in terms),
            "new wood ports act directly on panels; original B footprints are insufficient")
    require(request["reviewed_bolt_axes"] == 104 and request["proposed_internal_ties_included"] is False,
            "reviewed original104 and proposed internal ties conflated")
    authenticate(data.pins)
    return actions, report, aliases


def source_record(pins, record, identity):
    path = (ROOT / record["path"]).resolve()
    require(path in pins and pins[path] == record["sha256"], "state provenance is outside authenticated closure")
    value = read(path)
    pointer = record["pointer"]
    require(isinstance(pointer, str) and pointer.startswith("/"), "state provenance pointer missing")
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    require((value["case_id"], float(value["gap_scale"])) == identity, "source state provenance identifies another state")
    return value


def state_inventory(pins, report):
    inventory = report["required_state_inventory"]
    identities = [(r["case_id"], float(r["gap_scale"])) for r in inventory]
    require(len(inventory) == len(set(identities)) == 14 and set(identities) == REQUIRED_STATES,
            "complete unique fourteen-state disposition inventory required")
    accepted = set()
    for row, identity in zip(inventory, identities, strict=True):
        require(isinstance(row["accepted_force_field_exists"], bool)
                and row["state_tag"] == identity[0] + ("_zero" if identity[1] == 0 else "_gap")
                and isinstance(row["status"], str) and row["status"], "invalid required-state disposition")
        if row.get("source_disposition_record") is not None:
            original = source_record(pins, row["source_disposition_record"], identity)
            require(original["status"] == row["status"]
                    and original["accepted_force_field_exists"] is row["accepted_force_field_exists"],
                    "source disposition was relabeled")
        if row["accepted_force_field_exists"]:
            require(row["status"] == "PASS_CONDITIONAL_COMPATIBLE_EQUILIBRIUM", "unqualified force state marked accepted")
            original = source_record(pins, row["source_state_record"], identity)
            require(original["audit"]["all_passed"] is True, "source force audit was not accepted")
            accepted.add(identity)
    states = report["states"]
    exported = [(s["case_id"], float(s["gap_scale"])) for s in states]
    require(accepted and len(exported) == len(set(exported)) == len(accepted)
            and set(exported) == accepted, "exported force states differ from explicitly accepted inventory")
    by_identity = dict(zip(identities, inventory, strict=True))
    for state, identity in zip(states, exported, strict=True):
        require(state["state_tag"] == by_identity[identity]["state_tag"]
                and state["source_state_record"] == by_identity[identity]["source_state_record"],
                "exported accepted-state provenance differs")
    return inventory, accepted


def expected_counts(accepted):
    permanent = sum(case == PERMANENT for case, _gap in accepted)
    live = len(accepted)-permanent
    return {"screw_tuples": 66*len(accepted), "panel_balances": 6*len(accepted),
            "gross_cut_traces": 376*len(accepted), "local_duration_rows": 132*live+66*permanent,
            "net_duration_rows": 980*live+490*permanent}


def new_output(output):
    output = Path(output)
    require(not output.is_symlink() and not RAW.is_symlink(), "output symlink refused")
    output = output.resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned output child required")
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return output


def write(path, value, *, lines=False):
    with path.open("x") as stream:
        for row in value if lines else [value]:
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False)+"\n")


def finish(output, data, report, started):
    authenticate(data.pins)
    report.update(source_sha256={str(p.relative_to(ROOT)): d for p, d in sorted(data.pins.items())}, **FLAGS)
    write(output / "summary.json", report)
    outputs = {p.name: sha(p) for p in sorted(output.iterdir())}
    write(output / "receipt.json", {"schema": "panel_compatible_response_receipt/v1", "status": report["status"],
        "source_sha256": report["source_sha256"], "output_sha256": outputs,
        "sources_authenticated_before_and_after": True, "elapsed_seconds": time.monotonic()-started,
        "producer_sha256": sha(__file__), **FLAGS})
    authenticate(data.pins)
    return report


def prepare(output, actions=None, receipt_sha256=None):
    started = time.monotonic()
    data = static_sources()
    inventory, accepted = None, None
    if actions is not None:
        _actions, report, _aliases = action_sources(data, actions, receipt_sha256 or "")
        inventory, accepted = state_inventory(data.pins, report)
    output = new_output(output)
    plan = {"schema": "panel_compatible_response_preparation/v1",
        "status": "PREPARED_STATIC_CONSUMER_NOT_NUMERICAL_COMPARISON",
        "required_states": sorted(REQUIRED_STATES), "actions_supplied": actions is not None,
        "required_frozen_action_input": "receipt-bound accepted-state action export with complete14-state disposition inventory",
        "required_state_inventory": inventory, "accepted_states": sorted(accepted) if accepted is not None else None,
        "expected_counts": expected_counts(accepted) if accepted is not None else None,
        "all14_accepted_state_counts": expected_counts(REQUIRED_STATES),
        "original_mass_kg": 224.9499553141194, "original_dead_factor": 1.1111358300342407,
        "local_resistance_CD_live": [1., 1.25], "generic_screw_CD_live": [1., 1.6], "permanent_CD": .9,
        "arrays_read": False, "numerical_comparison_complete": False,
        "accepted_state_numerical_comparisons_complete": False}
    return finish(output, data, plan, started)


def scope(case, gap):
    return ("permanent" if case == PERMANENT else "live") + ("/zero" if gap == 0 else "/nominal")


def envelopes(records, metrics):
    result = {}
    groups = defaultdict(list)
    for record in records:
        groups[(record["scope"], record["CD"])].append(record)
    for (branch, cd), selected in sorted(groups.items()):
        for metric in metrics:
            require(all(math.isfinite(r[metric]) and r[metric] >= 0 for r in selected), "nonfinite panel comparison")
            witness = max(selected, key=lambda r: r[metric])
            result[f"{branch}/CD{cd}/{metric}"] = {"finite": len(selected),
                "exceeded": sum(r[metric] > 1 for r in selected), "maximum_ratio": witness[metric], "witness": witness}
    return result


def screw_envelopes(screws):
    result = {}
    for branch in sorted({s["scope"] for s in screws}):
        selected = [s for s in screws if s["scope"] == branch]
        groups = {}
        for kind in ("head", "withdrawal", "contacting_lateral", "combined_withdrawal_lateral"):
            groups[kind] = {}
            for scenario in selected[0]["references"][kind]:
                finite = [s for s in selected if s["references"][kind][scenario]["ratio"] is not None]
                peak = max(finite, key=lambda s: s["references"][kind][scenario]["ratio"]) if finite else None
                groups[kind][scenario] = {"finite": len(finite), "unsupported": len(selected)-len(finite),
                    "exceeded": sum(s["references"][kind][scenario]["ratio"] > 1 for s in finite),
                    "maximum_ratio": peak["references"][kind][scenario]["ratio"] if peak else None,
                    "witness": {k: peak[k] for k in ("case_id", "state_id", "axis_id", "panel", "receiver",
                        "tension_n", "lateral_n", "positive_opening_mm")} if peak else None}
        result[branch] = groups
    return result


def build(output, actions, receipt_sha256):
    import numpy as np

    started = time.monotonic()
    data = static_sources()
    actions, action_report, aliases = action_sources(data, actions, receipt_sha256)
    inventory, accepted = state_inventory(data.pins, action_report)
    planned = expected_counts(accepted)
    defs = data.definitions
    panel = defs(PANEL, ("size_factor", "panel_reference"),
        {"math": math, "LBF_N": data.local.N, "PSI_MPA": data.local.N/25.4**2}, ("BASE",))
    helper = defs(N14, ("comparison_row", "nominal_receiver", "screw_references", "panel_sections"),
        {"np": np, "math": math, "N_PER_LBF": data.local.N, "require": require})
    wrench = defs(WRENCH, ("wrench",), {"np": np}).wrench
    parser = defs(PARSER, ("parse_dof_lines", "parse_dof_file"), {"Path": Path, "re": re, "AssessmentError": ValueError})
    labels = parser.parse_dof_file(DOF)
    label_rows = {label: i for i, label in enumerate(labels)}
    combined = defs(LATERAL, ("combined_reference",), {"math": math}).combined_reference
    catalog = read(CATALOG)["reference_catalog"]
    refs = SimpleNamespace(heads=catalog["heads"], withdrawal=catalog["withdrawal"], lateral=catalog["lateral"], combined=combined)
    names = data.model["body_names"]
    centers = {b: np.mean([data.model["physical_node_coordinates_mm"][str(n)]
                          for n in sorted(set(data.model["body_nodes"][b]))], axis=0) for b in names}
    receivers = {a["axis_id"]: helper.nominal_receiver(np, a) for a in data.axes}
    action_panels = {}
    with gzip.open(actions / "body-actions.jsonl.gz", "rt") as stream:
        for line in stream:
            row = json.loads(line)
            if row["body"] in data.geometry["panels"]:
                identity = (row["case_id"], float(row["gap_scale"]), row["body"])
                require(identity not in action_panels, "repeated source panel action catalog")
                require(row["state_tag"] == row["case_id"] + ("_zero" if identity[1] == 0 else "_gap")
                        and all(a["source_force_available"] and not a["replaced_source_row_placeholder"]
                                for a in row["actions"]), "panel action has another state or an unavailable source row")
                action_panels[identity] = row
    require(len(action_panels) == planned["panel_balances"] and {key[:2] for key in action_panels} == accepted,
            "panel action catalog differs from explicitly accepted state subset")
    output = new_output(output)
    write(output / "inputs.json", {"action_export": str(actions.relative_to(ROOT)), "action_receipt_sha256": receipt_sha256,
        "source_aliases_to_executed_snapshots": aliases, "force_basis": "reviewed104_coupled_knee_sensitivity",
        "geometry_source": str(GEOMETRY.relative_to(ROOT)), "replaced_panel_connector_rows": 0,
        "required_state_inventory": inventory, "accepted_states": sorted(accepted),
        "action_state_scope": action_report["action_state_scope"],
        "source_response_status": action_report["source_response_status"]})
    write(output / "source-case-dispositions.json", inventory)
    try:
        screws, cuts, balances, audits = [], [], [], []
        with np.load(ORIGINAL / "operators.npz", allow_pickle=False) as operator, \
                np.load(ORIGINAL / "B.npz", allow_pickle=False) as projection, \
                np.load(actions / "source-row-response.npz", allow_pickle=False) as response:
            D, F, W = (operator[k] for k in ("D", "F", "W"))
            require(D.shape == (1888, 300) and F.shape == (37647, 12) and W.shape == (300, 12)
                    and len(labels) == 37647 and all(np.isfinite(a).all() for a in (D, F, W)), "D/F/W/DOF source dimensions differ")
            require(projection["shape"].tolist() == [1888, 37647] and projection["format"].item() == b"csr",
                    "original physical projection differs")
            indices, indptr, coefficients = (projection[k] for k in ("indices", "indptr", "data"))
            available = response["canonical_raw_row_available"]
            motions_map = response["canonical_raw_row_to_kept_lumped_position"]
            kept = response["old_kept_lumped_rows"]
            row_map = read(actions / "source-row-map.json")
            require(available.shape == motions_map.shape == (1888,) and available.dtype.kind == "b"
                    and motions_map.dtype.kind in "iu" and kept.shape == (1592,)
                    and kept.tolist() == row_map["old_kept_lumped_rows"]
                    and np.flatnonzero(~available).tolist() == row_map["unavailable_replaced_canonical_rows"]
                    and np.count_nonzero(~available) == 20 and (motions_map[~available] == -1).all()
                    and (motions_map[available] >= 0).all() and (motions_map[available] < len(kept)).all(),
                    "canonical availability/motion map differs from declared 20-row replacement")
            accepted_tags = {case + ("_zero" if gap == 0 else "_gap") for case, gap in accepted}
            for suffix in ("_raw_force_n", "_kept_lumped_relative_motion_mm", "_coupled_force_n"):
                require({key[:-len(suffix)] for key in response.files if key.endswith(suffix)} == accepted_tags,
                        "saved force/motion fields differ from accepted-state subset")
            for case, gap in sorted(accepted):
                tag = case + ("_zero" if gap == 0 else "_gap")
                raw, q = response[tag+"_raw_force_n"], response[tag+"_kept_lumped_relative_motion_mm"]
                require(raw.shape == (1888,) and q.shape == (1592,) and np.isfinite(raw).all()
                        and np.isfinite(q).all() and (raw[~available] == 0.).all(), "invalid canonical response or placeholder")
                column = 0 if case == PERMANENT else 2*CASES.index(case)
                load, nodal = data.model["dead_load_factor"]*W[:, column], data.model["dead_load_factor"]*F[:, column]
                if case != PERMANENT:
                    load, nodal = load+W[:, column+1], nodal+F[:, column+1]
                connector = np.bincount(indices, weights=-coefficients*np.repeat(raw, np.diff(indptr)), minlength=37647)
                max_law_error, max_moment_error = 0., 0.
                refs.duration_factors = [.9] if case == PERMANENT else [1., 1.6]
                for axis in data.axes:
                    ids, panel_name, receiver = axis["rows"], axis["panel"], axis["receiver"]
                    require(available[ids].all() and (motions_map[ids] >= 0).all() and (motions_map[ids] < len(q)).all(),
                            "screw row is an unavailable placeholder")
                    pb, rb = 6*names.index(panel_name), 6*names.index(receiver)
                    basis = D[ids, pb:pb+3]
                    require(np.max(abs(basis@basis.T-np.eye(3))) < 1e-10
                            and np.max(abs(basis+D[ids, rb:rb+3])) < 1e-10, "screw component signs/basis differ")
                    motion = q[motions_map[ids]]
                    expected = [data.rows[i]["law"]["stiffness_N_per_mm"]*(max(0., m) if j == 2 else m)
                                for j, (i, m) in enumerate(zip(ids, motion, strict=True))]
                    law_error = float(np.max(abs(raw[ids]-expected)))
                    require(law_error < 1e-4 and raw[ids[2]] >= -1e-4, "inherited screw law audit failed")
                    max_law_error = max(max_law_error, law_error)
                    signed = -basis.T @ raw[ids]
                    moment_error = float(np.max(abs(np.cross(np.array(axis["point_mm"])-centers[panel_name], signed)
                        + 1000*D[ids, pb+3:pb+6].T @ raw[ids])))
                    require(moment_error < .01, "screw signed point moment differs")
                    max_moment_error = max(max_moment_error, moment_error)
                    tension, shear = max(0., float(raw[ids[2]])), float(np.linalg.norm(raw[ids[:2]]))
                    screws.append({"case_id": case, "state_id": tag, "gap_scale": gap, "scope": scope(case, gap),
                        "axis_id": axis["axis_id"], "panel": panel_name, "receiver": receiver, "source_rows": ids,
                        "point_mm": axis["point_mm"], "panel_datum_mm": centers[panel_name].tolist(),
                        "tension_n": tension, "lateral_n": shear, "signed_force_on_panel_n": signed.tolist(),
                        "signed_axial_relative_mm": float(motion[2]), "positive_opening_mm": max(0., float(motion[2])),
                        "references": helper.screw_references(tension, shear, receivers[axis["axis_id"]], refs),
                        "loaded_opening_present": bool(motion[2] > 1e-8), "lateral_contacting_faces_demonstrated": False,
                        "actual_Hillman_steel_capacity_assigned": False, "complete_screw_acceptance": False})
                for name in sorted(data.geometry["panels"]):
                    block = 6*names.index(name)
                    incident = [r["row"] for r in data.rows if name in (r["ownership"]["first_body"], r["ownership"]["second_body"])]
                    require(available[incident].all(), "panel incident row unavailable after coupled replacement")
                    source = action_panels[(case, gap, name)]
                    require(np.max(abs(np.array(source["center_mm"])-centers[name])) < 1e-8, "panel action datum differs")
                    total, external, connector_actions = [], [], []
                    for node in sorted(set(data.model["body_nodes"][name])):
                        ids = [label_rows[(node, dof)] for dof in (1, 2, 3)]
                        action = {"row": -1, "point_mm": data.model["physical_node_coordinates_mm"][str(node)],
                                  "free_moment_nmm": [0., 0., 0.]}
                        external.append({**action, "force_n": nodal[ids].tolist()})
                        connector_actions.append({**action, "force_n": connector[ids].tolist()})
                        total.append({**action, "force_n": (nodal[ids]+connector[ids]).tolist()})
                    expected = load[block:block+6]*[1, 1, 1, 1000, 1000, 1000]
                    require(np.max(abs(wrench(external, centers[name])-expected)) < 1e-5, "panel nodal F/W load mismatch")
                    source_connector = [a for a in source["actions"] if a["role"] != "discrete_body_load"]
                    require(np.max(abs(wrench(connector_actions, centers[name])-wrench(source_connector, centers[name]))) < 1e-5,
                            "panel nodal B/source action wrench mismatch")
                    balance = wrench(total, centers[name])
                    require(np.max(abs(balance[:3])) < 1e-5 and np.max(abs(balance[3:])) < .01,
                            "inherited panel equilibrium/cut gates failed")
                    recovered = helper.panel_sections(np, panel, wrench, SimpleNamespace(model=data.model), tag, name, total, centers[name])
                    cuts.extend({**c, "state_id": tag, "source_case_id": case, "gap_scale": gap, "scope": scope(case, gap)} for c in recovered)
                    balances.append({"case_id": case, "state_id": tag, "gap_scale": gap, "panel": name,
                        "balance_residual_n_nmm": balance.tolist(), "nodal_count": len(total), "scope": scope(case, gap)})
                audits.append({"case_id": case, "gap_scale": gap, "state_id": tag,
                               "screw_law_error_n": max_law_error, "screw_point_moment_error_nmm": max_moment_error})
        local = []
        for screw in screws:
            for cd in ([.9] if screw["case_id"] == PERMANENT else [1., 1.25]):
                local.append({**data.local.local_screw(screw, data.geometry["panels"][screw["panel"]], cd),
                    "state_id": screw["state_id"], "gap_scale": screw["gap_scale"], "scope": screw["scope"]})
        net, quadrature = [], {}
        for permanent in (False, True):
            selected = [c for c in cuts if (c["source_case_id"] == PERMANENT) == permanent]
            values, observation = data.local.net_rows(selected, data.geometry, data.model, data.layers, panel,
                                                       (.9,) if permanent else (1., 1.25))
            quadrature["permanent" if permanent else "live"] = observation
            for value in values:
                tag = value["case_id"]
                case, gap_word = tag.rsplit("_", 1)
                gap = 0. if gap_word == "zero" else 1.
                net.append({**value, "case_id": case, "state_id": tag, "gap_scale": gap, "scope": scope(case, gap)})
        counts = {"screw_tuples": len(screws), "panel_balances": len(balances), "gross_cut_traces": len(cuts),
                  "local_duration_rows": len(local), "net_duration_rows": len(net)}
        require(counts == planned, "accepted-state panel comparison census differs")
        for name, records in (("screw-states.jsonl", screws), ("panel-cut-actions.jsonl", cuts),
                              ("panel-balances.jsonl", balances), ("screw-local.jsonl", local), ("net-sections.jsonl", net)):
            write(output / name, records, lines=True)
        report = {"schema": "panel_compatible_response/v1",
            "status": ("COMPLETED_COMPATIBLE_ORIGINAL104_PANEL_REFERENCE_COMPARISON" if accepted == REQUIRED_STATES
                       else "COMPLETED_ACCEPTED_COMPATIBLE_ORIGINAL104_PANEL_REFERENCE_COMPARISONS_WITH_EXCLUDED_STATES"),
            "numerical_comparison_complete": accepted == REQUIRED_STATES,
            "accepted_state_numerical_comparisons_complete": True,
            "required_state_inventory": inventory, "accepted_states_compared": sorted(accepted),
            "excluded_required_states": [r for r in inventory if not r["accepted_force_field_exists"]],
            "all14_required_states_compared": accepted == REQUIRED_STATES,
            "source_action_receipt_sha256": receipt_sha256,
            "source_action_export_status": action_report["status"],
            "source_response_status": action_report["source_response_status"],
            "source_action_state_scope": action_report["action_state_scope"],
            "source_force_basis": "reviewed104_coupled_knee_sensitivity",
            "required_states": sorted(REQUIRED_STATES), "original_mass_kg": 224.9499553141194,
            "original_dead_factor": 1.1111358300342407, "proposal_ties_or_mass_included": False,
            "counts": {**counts, "accepted_states": len(accepted), "required_states": 14,
                       "excluded_required_states": 14-len(accepted), "Hillman_steel_resistance_rows": 0},
            "local_envelopes": envelopes(local, ("head_face_bearing_ratio", "local_punching_ratio",
                "directional_two_ligament_shear_ratio", "simultaneous_linear_shear_budget_hypothesis")),
            "net_envelopes": envelopes(net, ("net_axial_ratio", "net_bending_ratio", "linear_axial_bending_budget_hypothesis",
                "net_planar_shear_ratio", "net_membrane_shear_ratio", "isolated_hole_membrane_reference_sensitivity")),
            "generic_screw_envelopes": screw_envelopes(screws), "audits": audits, "quadrature": quadrature,
            "source_action_states": [{k: s[k] for k in ("case_id", "gap_scale", "state_tag", "source_state_record")}
                                     for s in action_report["states"]],
            "runtime": {"python": platform.python_version(), "numpy": np.__version__, "numerical_solver": None},
            "limits": [
                "Compatible source is a separate original104 first-order knee-shaft/contact sensitivity, not a replacement authority or a physical release.",
                "All66 screw states are recomputed from the compatible canonical forces and motions; old demand maxima are not reused.",
                "Only explicitly accepted saved force states are compared. Failed, quarantined and unassessed required states retain source dispositions and have no zero-filled demands or comparisons.",
                "Panel cuts preserve original F/B physical nodal footprints and every nodal action station; new knee ports apply no direct panel load.",
                "Local net stiffness/resistance does not feed back into the frame. Frozen body compliance and declared source material axes remain conditional.",
                "Uniform cone pressure, circular punching strip, two-ligament shear and additive budgets remain declared hypotheses, not tested Hillman capacities or codified plate acceptance.",
                "Existing head/withdrawal/contacting-lateral references are unadjusted catalog hypotheses; CD is applied once, and positive opening does not qualify contacting faces.",
                "Hillman steel/profile/thread conformity and delivered plywood/hold contact/loaded-hole fracture remain unbound; steel records are demands only.",
                "Live zero-gap, live nominal-gap and both permanent branches remain separate. No force envelope over alternative seating solutions is supplied."]}
        return finish(output, data, report, started)
    except Exception as error:
        write(output / "stop.json", {"status": "STOP_COMPATIBLE_PANEL_COMPARISON_INCOMPLETE", "error": str(error),
            "numerical_comparison_complete": False, "accepted_state_numerical_comparisons_complete": False,
            "required_state_inventory": inventory, "physical_failure_claimed": False, **FLAGS})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "build"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--actions", type=Path)
    parser.add_argument("--receipt-sha256")
    args = parser.parse_args()
    if args.stage == "build" and (args.actions is None or args.receipt_sha256 is None):
        parser.error("build requires --actions and parent-frozen --receipt-sha256")
    result = (prepare(args.output, args.actions, args.receipt_sha256) if args.stage == "prepare"
              else build(args.output, args.actions, args.receipt_sha256))
    print(json.dumps({"status": result["status"], "output": str(args.output)}, sort_keys=True))
