"""Prepare N02 joins; let the parent evaluate frozen six-case row sensitivities.

Import is inert and prepare(output) uses only the standard library. build(output)
is a parent-only scalar worksheet, using existing pinned group-factor functions.
No solver, historical producer, CAD, coupon, test or review entry point is called.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = HERE.parent
RAW = HERE / "rawlocal/bolt-group-completion"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
FRAME = HERE / "rawlocal/knee-bridge-frame/attempt02/response"
EXPORT = HERE / "rawlocal/knee-bridge-response/attempt02"
OTHER = HERE / "rawlocal/knee-bridge-other-bolts/attempt01"
CORNER = HERE / "rawlocal/knee-bridge-corner-references/attempt01"
REPLAY = HERE / "rawlocal/knee-bridge-corner-replay/attempt01"
BRIDGE = HERE / "rawlocal/knee-bridge-joint-replay/attempt01"
WORKING = HERE / "rawlocal/knee-bridge-working-package/attempt02"
REGISTER = HERE / "rawlocal/working-joint-register/attempt03/register.json"
RETAINED = Path("/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json")
MATERIAL = PACKET.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
FASTENERS = MATERIAL.with_name("fastener-inputs.json")
ROW_METHOD = PACKET / "retained_group_checks.py"
ADOPTED_METHOD = ROOT / "fea/compact_thick_checks.py"
POSITIVE_METHOD = ROOT / "fea/thick_leg_checks.py"
STRICT_METHOD = ROOT / "mini_moonboard/nds_2024_group_action.py"
CHAPTER = PACKET.parent / "upper-block-strength-2026-10-01/source-cache/chapter11-2024-awc-20260911.pdf"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    GRAVITY / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    GRAVITY / "model-inputs.json": "b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99",
    FRAME / "comparison.json": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    FRAME / "response.npz": "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    EXPORT / "summary.json": "da8fcfde95eda2fb6967194c1060e5b55647eeb1ea98efa25e8a9e8260294c70",
    EXPORT / "receipt.json": "57163aa9f4e1ed7af338d29c4893f5614c21bd422e841532cf67feb67ac20933",
    EXPORT / "global-demands.jsonl": "f0d9bb8a8a25775a2571692183860b209708111b089f16538f7eab5d9adbe4c3",
    OTHER / "records.jsonl": "1050735cfa418fc13b27b48de0ba116adabe32683e1d1cf3524c07cca087dd95",
    OTHER / "summary.json": "317fd50ce080862f42bdd57c36994a71bfe499f7d069688571524a803c54e630",
    OTHER / "receipt.json": "ee67b7e042a8fcf88d1c37eaaaaac8aebcb815e2cf73b8f1a22a61f44283da83",
    CORNER / "worksheet.json": "c7c2bbde84cf48bd5042e06cbe218b741da684fa7477eed56da2add4f132c051",
    CORNER / "receipt.json": "fcd986b018bb121df464292449cedcb23f1c069bd5ec611dd49b654c6d840288",
    REPLAY / "checks.json": "e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976",
    REPLAY / "receipt.json": "50898edc4d0d977c7522c3c30866504235f847ee6d3777345114afb4d86cd52d",
    BRIDGE / "checks.json": "71980f983dd3466d02eb6c5f838186de4b77dc2ebe04653f66cf3f3598fbe891",
    BRIDGE / "receipt.json": "10503afef20c8fc69c0f5b4877f8deb2794646c258b05ca63616611443c6c22b",
    WORKING / "manifest.json": "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0",
    WORKING / "receipt.json": "5fa8cc849e4a2fa042a1cffa6d2957d4163597c7999dbcef1f57563dfdd83e7b",
    REGISTER: "c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c",
    RETAINED: "c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    FASTENERS: "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2",
    ROW_METHOD: "391b459d20a7cc6bb2f53ec4622259948b74f228a6553f4dee749a2011ff559f",
    ADOPTED_METHOD: "036da136ba732d97b20a026ae98f5c78dfe3c9571b2b49b3be188909ba3c3dc4",
    POSITIVE_METHOD: "0609afebe3664d70b60de9499ffeedaa3fc1cd31991bb95f7ca76d18117cf041",
    STRICT_METHOD: "121ec9d5399aa3e856b4038232e6d61c628aac42ce2addf8d1ff7e3a0e4c3df9",
    CHAPTER: "45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33",
    ROOT / "scripts/compact_splice_results.py": "10fd2ffd2afc563edb8f0c9017adec37423ae60d8026fa1fe4e72a85cf38dbdc",
    ROOT / "docs/floor-runner-mvp-criteria.md": "f6b5591bbbb2aaf87553095e04fbe5abd66d38a926a3efb66711420492f0f090",
    ROOT / "docs/wood-joints-mvp/criteria.json": "fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784",
    ROOT / "wood-joints-candidate.json": "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
}
FLAGS = {
    "proposal_adopted": False, "historical_acceptance_transferred": False,
    "formal_criteria_updated": False, "formal_criterion_acceptance": False,
    "actual_oblique_crossed_group_resistance_established": False,
    "actual_changed_hole_stiffness_qualified": False,
    "group_spacing_or_directional_edges_qualified": False,
    "complete_joint_acceptance": False, "physical_release": False,
    "native_CAD_frame_or_coupon_execution": False, "tests_or_review_run": False,
}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def location(path):
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path not in pins or pins[path] == digest, "conflicting pin: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + str(path))


def receipt_closure(pins, directory, *, provenance_only=()):
    """Expand an already pinned receipt before consuming any of its outputs."""
    receipt = read(directory / "receipt.json")
    for name, digest in receipt["source_sha256"].items():
        if name not in provenance_only:
            bind(pins, ROOT / name, digest)
    for name, digest in receipt["output_sha256"].items():
        path = (directory / name).resolve()
        require(path.parent == directory, "receipt artifact leaves its packet")
        bind(pins, path, digest)
    authenticate(pins)
    return receipt


def fresh_output(output):
    output = Path(output).absolute()
    require(output == output.resolve() and output.parent == RAW.resolve()
            and not output.exists(), "fresh immediate owned RAW child required")
    return output


def publish(output, document, pins, name):
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    document["source_sha256"] = {location(path): digest for path, digest in sorted(pins.items())}
    (output / name).write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")
    authenticate(pins)
    receipt = {
        "schema": "bolt_group_completion_receipt/v1", "status": document["status"],
        "source_sha256": document["source_sha256"], "producer_sha256": sha(Path(__file__)),
        "output_sha256": {artifact: sha(output / artifact)
                          for artifact in (".gitignore", "producer.py.snapshot", name)},
        "census": document["census"], "sources_authenticated_before_and_after": True,
        **FLAGS,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    authenticate(pins)
    return receipt


def join_end_grain(pins, receipt_path, receipt_sha256):
    """Join N01 only when the parent supplies both a fixed receipt and its hash."""
    require((receipt_path is None) == (receipt_sha256 is None), "N01 receipt and SHA must be paired")
    if receipt_path is None:
        return {}
    path = Path(receipt_path).resolve()
    require(path.name == "receipt.json" and path.parent.parent == HERE / "rawlocal/bolt-reference-completion",
            "N01 receipt must belong to its owned completion packet")
    bind(pins, path, receipt_sha256)
    authenticate(pins)
    receipt = receipt_closure(pins, path.parent)
    require(receipt["schema"] in ("bolt_reference_completion_receipt/v1", "bolt_reference_completion_receipt/v2")
            and receipt["sources_authenticated_before_and_after"] is True,
            "N01 completion receipt contract differs")
    artifacts = receipt["output_sha256"]
    require({"end-grain.jsonl", "summary.json", "producer.py.snapshot"}.issubset(artifacts)
            and artifacts["producer.py.snapshot"] == receipt["producer_sha256"],
            "N01 worksheet or producer snapshot is not bound by the receipt")
    if receipt["schema"] == "bolt_reference_completion_receipt/v2":
        mode, counts = receipt["mode"], receipt["counts"]
        require(mode in ("n01", "full") and receipt["N01_comparisons_complete"] is True
                and counts["N01_states"] == 72, "v2 receipt does not complete N01")
        summary = read(path.parent / "summary.json")
        require(summary["schema"] == "bolt_reference_completion/v2"
                and summary["mode"] == mode and summary["status"] == receipt["status"]
                and summary["counts"] == counts and summary["case_ids"] == list(CASES),
                "N01 summary/receipt mode, status or census differs")
        if mode == "n01":
            require(receipt["status"] == "COMPLETE_N01_N10_PENDING"
                    and receipt["shaft_helper_calls"] == counts["shaft_helper_calls"] == 0
                    and counts["N10_states"] == counts["completed_shaft_states"] == counts["shaft_field_samples"] == 0
                    and receipt["N10_pending"] is True and receipt["N10_comparisons_complete"] is False
                    and not {"steel.jsonl", "shaft-fields.jsonl"}.intersection(artifacts),
                    "N01-only receipt must leave N10 pending with zero steel/shaft calls and outputs")
        else:
            require(receipt["status"] in ("COMPLETE_CONDITIONAL_COMPARISONS", "PARTIAL_NULL_SHAFT_STATES"),
                    "full-mode receipt does not identify a completed N01 worksheet")
    for source in (GRAVITY / "operator-assessment.json", FRAME / "comparison.json", FRAME / "response.npz"):
        require(receipt["source_sha256"][location(source)] == PINS[source], "N01 uses another force authority")
    records = lines(path.parent / "end-grain.jsonl")
    joined = {(row["case_id"], row["axis_id"]): row for row in records}
    require(len(joined) == len(records) == 72 and all(row["obligation"] == "N01" for row in records),
            "72-state N01 census differs")
    return joined


def preparation(receipt_path=None, receipt_sha256=None):
    """Authenticate saved bytes and assemble records; no group equation executes."""
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    authenticate(pins)
    for directory in (EXPORT, OTHER, CORNER, REPLAY, BRIDGE):
        receipt_closure(pins, directory)
    # The working inventory also pinned a shop prose file that has since changed.
    # Its old binding remains provenance; this worksheet does not consume that
    # prose for geometry, resistance, hardware or a release decision.
    shop_prose = location(PACKET / "assembly-package/hardware-engagement.md")
    working_receipt = receipt_closure(pins, WORKING, provenance_only=(shop_prose,))
    comparison, assessment, inputs, register, working, corner, replay, bridge, retained = map(read, (
        FRAME / "comparison.json", GRAVITY / "operator-assessment.json", GRAVITY / "model-inputs.json",
        REGISTER, WORKING / "manifest.json", CORNER / "worksheet.json", REPLAY / "checks.json",
        BRIDGE / "checks.json", RETAINED))
    require(comparison["response_sha256"] == PINS[FRAME / "response.npz"]
            and comparison["source_sha256"][location(GRAVITY / "operator-assessment.json")]
            == PINS[GRAVITY / "operator-assessment.json"], "gravity/response identity differs")
    require(assessment["operator_ready"] is True and assessment["case_ids"] == list(CASES)
            and {(row["case_id"], row["gap_scale"]) for row in comparison["states"]}
            == {(case, gap) for case in CASES for gap in (0.0, 1.0)}, "fresh case/gap census differs")
    require(comparison["comparison_climber_weight_lb"] == 250.0
            and comparison["modeled_mass_kg"] == assessment["modeled_mass_kg"] == working["modeled_mass_kg"]
            == corner["modeled_mass_kg"] == bridge["modeled_mass_kg"]
            and comparison["dead_load_factor"] == assessment["dead_load_factor"] == working["dead_load_factor"]
            == corner["dead_load_factor"] == bridge["dead_load_factor"], "fresh mass/load scope differs")
    require(all(record["case_ids"] == list(CASES) for record in (register, working, corner, replay, bridge)),
            "six-case order differs")
    criteria = read(ROOT / "docs/wood-joints-mvp/criteria.json")
    obligations = criteria["legacy_criteria"] + criteria["additional_candidate_obligations"]
    candidate = read(ROOT / "wood-joints-candidate.json")
    require(len(obligations) == 47 and all(row["status"] == "pending" for row in obligations)
            and len(candidate["release_flags"]) == 8 and not any(candidate["release_flags"].values())
            and candidate["release"] is False, "47 pending obligations / eight false release flags differ")
    material = read(MATERIAL)["conditional_DF_L_No2_base_row"]["base_properties"]
    require(material["E"] == 1600000.0, "existing row sensitivity E differs")
    members = {row["member_id"]: row["reduced_geometry_descriptor"] for row in inputs["members"]
               if row["member_kind"] != "panel"}
    axes = {row["axis_id"]: row for row in register["axes"]}
    bolts = {row["axis_id"]: row for row in inputs["connections"] if row["kind"] in ("candidate_bolt", "retained_bolt")}
    require(len(axes) == len(register["axes"]) == len(bolts) == 104 and set(axes) == set(bolts),
            "reviewed 104-axis identity differs")
    exported = [row for row in lines(EXPORT / "global-demands.jsonl") if row["kind"] == "structural_bolt"]
    globals_by_state = {(row["case_id"], row["axis_id"]): row for row in exported}
    others = lines(OTHER / "records.jsonl")
    others_by_state = {(row["case_id"], row["axis_id"]): row for row in others}
    corners = {(row["case_id"], row["axis_id"]): row for row in corner["states"]}
    require(len(exported) == len(globals_by_state) == 624
            and set(globals_by_state) == {(case, axis) for case in CASES for axis in axes}
            and len(others) == len(others_by_state) == 504 and len(corner["states"]) == len(corners) == 96
            and set(others_by_state).isdisjoint(corners), "fresh force partition differs")
    local_bolts = {}
    for block in replay["states"]:
        for host in block["hosts"].values():
            for bolt in host["state"]["bolts"]:
                identity = block["case_id"], bolt["axis_id"]
                require(identity not in local_bolts, "duplicate corner local state")
                local_bolts[identity] = bolt
    require(set(local_bolts) == set(corners), "corner local/reference state join differs")
    end_grain = join_end_grain(pins, receipt_path, receipt_sha256)
    groups = defaultdict(list)
    for axis in axes.values():
        for plane in axis["interfaces"]:
            groups[tuple(sorted(plane["receivers"]))].append((axis, plane))
    require(len(groups) == 54 and all(len(pair) == 2 for pair in groups.values()), "54 two-bolt interface census differs")
    records, geometries = [], []
    for receivers, pair in sorted(groups.items()):
        pair.sort(key=lambda item: item[0]["axis_id"])
        group_id = " / ".join(receivers)
        geometry = {"group_id": group_id, "receivers": list(receivers), "axis_ids": [a["axis_id"] for a, _ in pair],
                    "stock_descriptors": {member: members[member] for member in receivers}, "bolts": []}
        for axis, plane in pair:
            axis_id, bolt = axis["axis_id"], bolts[axis["axis_id"]]
            require(set(bolt["receiver_member_ids"]) == set(axis["receivers"]), "receiver identity differs")
            if bolt["kind"] == "retained_bolt":
                basis = retained["axis_register"][axis_id]
                lengths = {r["member"]: r["interval_from_axis_datum_mm"][1] - r["interval_from_axis_datum_mm"][0]
                           for r in basis["finished_receivers"]}
                frames = {r["member"]: r["stock_frame"] for r in basis["finished_receivers"]}
                diameter = basis["hardware_policy"]["nominal_diameter_in"] * 25.4
                for receiver in basis["finished_receivers"]:
                    bind(pins, ROOT / receiver["finished_step"]["path"], receiver["finished_step"]["file_sha256"])
            else:
                basis = bolt["source_record"]["geometry"]
                intervals = {r["receiver_id"]: r["current_shaft_intersection_solid_intervals_from_underhead_mm"]
                             for r in basis["wood_receiver_intervals"]}
                require(all(len(intervals[member]) == 1 for member in receivers), "multispan grip lacks row basis")
                lengths = {member: intervals[member][0][1] - intervals[member][0][0] for member in receivers}
                diameter, frames = basis["modeled_shaft_diameter_mm"], None
            geometric_bolt = {"axis_id": axis_id, "plane_id": plane["plane_id"], "point_xyz_mm": plane["point_xyz_mm"],
                              "diameter_mm": diameter, "bearing_lengths_mm": lengths, "retained_stock_frames": frames,
                              "physical_receiver_count": len(axis["receivers"])}
            if (CASES[0], axis_id) in corners:
                row = corners[CASES[0], axis_id]
                geometric_bolt.update(point_xyz_mm=local_bolts[CASES[0], axis_id]["interface_point_xyz_mm"],
                                      diameter_mm=row["diameter_mm"], bearing_lengths_mm=dict(zip(
                                          row["ordered_receivers_host_cleat"], row["ordered_wood_lengths_mm"], strict=True)))
            geometry["bolts"].append(geometric_bolt)
            for case in CASES:
                identity = case, axis_id
                demand = globals_by_state[identity]
                exported_plane = next(row for row in demand["interfaces"] if row["plane_id"] == plane["plane_id"])
                require(exported_plane["component_rows"] == plane["component_rows"]
                        and exported_plane["component_directions_xyz"] == plane["component_directions_xyz"],
                        "global plane row/direction join differs")
                record = {"group_id": group_id, "case_id": case, "axis_id": axis_id, "plane_id": plane["plane_id"],
                          "receivers": list(receivers), "force_source_receivers": plane["receivers"],
                          "force_components_n": exported_plane["components_n"],
                          "force_component_directions_xyz": exported_plane["component_directions_xyz"],
                          "signed_axial_n": demand["signed_axial_n"], "source_scope": "fresh_global_allocation",
                          "tie": axis["outer_tie"], "reference_n": None, "Cdelta": 1.0,
                          "saved_component_Cg": None, "reference_null_reason": None}
                if identity in corners:
                    row, local = corners[identity], local_bolts[identity]
                    require(row["signed_T_n"] == local["compatible_T_n"]
                            and local["interface_point_xyz_mm"] == geometric_bolt["point_xyz_mm"],
                            "corner simultaneous state/point differs")
                    factor = row["component_factors"]
                    cg, cd = (factor["Cg_Cdelta"] if "Cg_Cdelta" in factor
                              else (factor.get("Cg_component_scenario", 1.0), factor.get("Cdelta_end_scenario", 1.0)))
                    record.update(force_xyz_n=row["signed_lateral_force_on_cleat_xyz_n"], force_on_member=row["cleat"],
                                  signed_axial_n=row["signed_T_n"], reference_n=row["reference_92ksi_n"],
                                  Cdelta=cd, saved_component_Cg=cg, source_scope="fresh_first_order_corner_allocation",
                                  bolt_only_host_wrench_n_nmm=local["wrench_on_host_at_face_datum_n_nmm"],
                                  host_wrench_datum_xyz_mm=next(g["host_interface_datum_xyz_mm"] for g in replay["preparation"]
                                      if axis_id in g["axis_ids"]), host=row["host"])
                elif identity in others_by_state:
                    row = others_by_state[identity]
                    require(row["plane_id"] == plane["plane_id"] and row["signed_axial_n"] == demand["signed_axial_n"]
                            and row["components_n"] == exported_plane["components_n"], "other fresh-state join differs")
                    record.update(force_xyz_n=row["force_on_first_body_xyz_n"], force_on_member=row["receivers"][0],
                                  reference_n=row["reference_92ksi_n"])
                    if record["reference_n"] is None:
                        record["reference_null_reason"] = "N01_END_GRAIN_RECEIPT_NOT_SUPPLIED"
                        if identity in end_grain:
                            n01 = end_grain[identity]
                            require(n01["same_plane_lateral_n"] == row["same_plane_lateral_n"]
                                    and n01["signed_axial_n"] == row["signed_axial_n"]
                                    and {n01["main_member"], n01["side_member"]} == set(receivers),
                                    "N01 same-state force/receiver join differs")
                            record.update(reference_n=n01["Ceg_reference_n"], reference_null_reason=None,
                                          reference_adjustment="N01_Ceg_applied_once")
                else:
                    record["reference_null_reason"] = "CONTINUOUS_THREE_RECEIVER_SHAFT_HAS_NO_FRESH_GROUP_YIELD_BASIS"
                records.append(record)
        geometries.append(geometry)
    require(len(records) == 648 and len({(r["case_id"], r["axis_id"], r["plane_id"]) for r in records}) == 648,
            "648 simultaneous lateral-interface states differ")
    require(not end_grain or set(end_grain) == {(r["case_id"], r["axis_id"]) for r in records
                if r.get("reference_adjustment") == "N01_Ceg_applied_once"}, "unused or missing N01 state")
    new_axes = {axis["canonical_axis_id"]: axis for axis in working["proposed_internal_bolt_axes"]}
    require(len(new_axes) == 4 and all(axis["same_body_end_pair"] and not axis["receiver_interfaces"]
                                    for axis in new_axes.values()), "four internal same-body ties differ")
    internal = []
    for state in bridge["states"]:
        own = state["axial_stack_reference_comparisons"]
        require(len(own) == 2 and [r["axial_tension_n"] for r in own] == state["constant_axial_ties_n"]
                and all(new_axes[r["canonical_axis_id"]]["body"] == state["block"] for r in own),
                "internal pair same-state allocation differs")
        internal.append({"body": state["block"], "case_id": state["case_id"], "comparisons": own,
                         "axes": [new_axes[r["canonical_axis_id"]] for r in own],
                         "Cg_applicability": "NOT_LATERAL_DOWEL_TRANSFER; SAME_BODY_AXIAL_TIES",
                         "complete_anchorage_or_shared_deformation_established": False})
    require(len(internal) == 12 and {(row["body"], row["case_id"]) for row in internal}
            == {(body, case) for body in ("knee_outer_left_spine", "knee_outer_right_spine") for case in CASES},
            "two internal pair / twelve pair-state census differs")
    duties = [{"duty_id": block["block_id"], "axis_ids": block["candidate_axis_ids"],
               "interface_group_ids": [g["group_id"] for g in geometries if block["block_id"] in g["receivers"]]}
              for block in register["blocks"]]
    duties.extend({"duty_id": row["arrangement_id"], "axis_ids": row["physical_axis_ids"],
                   "interface_group_ids": [" / ".join(sorted(row["receivers"]))]}
                  for row in register["retained_frame_bolt_arrangements"])
    require(len(duties) == 30 and Counter(len(d["interface_group_ids"]) for d in duties) == {2: 24, 1: 6},
            "24 block duties / six retained arrangements differ")
    authenticate(pins)
    document = {
        "schema": "bolt_group_completion_preparation/v1", "status": "AUTHENTICATED_CENSUS_ONLY",
        "case_ids": list(CASES), "gap_scale": 1.0, "candidate": inputs["candidate"], "revision_id": inputs["revision_id"],
        "census": {"reviewed_physical_axes": 104, "unadopted_proposal_axes": 108, "proposed_internal_axial_axes": 4,
                   "duties": 30, "lateral_interface_pairs": 54, "lateral_pair_states": 324,
                   "lateral_axis_interface_states": 648, "retained_pairs": 6, "internal_pairs": 2,
                   "internal_pair_states": 12, "internal_axis_states": 24, "Hillman_axes": 66,
                   "joined_N01_end_grain_states": len(end_grain)},
        "fresh_load_sources": {location(p): PINS[p] for p in
                               (GRAVITY / "operator-assessment.json", FRAME / "comparison.json", FRAME / "response.npz")},
        "modeled_mass_kg": comparison["modeled_mass_kg"], "dead_load_factor": comparison["dead_load_factor"],
        "groups": geometries, "lateral_states": records, "internal_pair_states": internal, "duties": duties,
        "E_psi": material["E"], "mechanical_arithmetic_executed": False, **FLAGS,
        "unconsumed_receipt_sources_preserved_as_provenance": {
            shop_prose: working_receipt["source_sha256"][shop_prose]},
    }
    return document, pins


def prepare(output, *, end_grain_receipt=None, end_grain_receipt_sha256=None):
    """Publish authenticated census/API joins only; the worker may call this."""
    output = fresh_output(output)
    document, pins = preparation(end_grain_receipt, end_grain_receipt_sha256)
    return publish(output, document, pins, "preparation.json")


def pure_functions(path, names, namespace):
    tree = ast.parse(path.read_text(), filename=str(path))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    require(len(selected) == len(names) and all(not node.decorator_list for node in selected), "retained functions differ")
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    return {name: namespace[name] for name in names}


def dot(first, second):
    return sum(a * b for a, b in zip(first, second, strict=True))


def norm(vector):
    require(len(vector) == 3 and all(math.isfinite(value) for value in vector), "nonfinite three-vector")
    return math.sqrt(dot(vector, vector))


def subtract(first, second):
    return [a - b for a, b in zip(first, second, strict=True)]


def cross(first, second):
    return [first[1] * second[2] - first[2] * second[1], first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0]]


def force_on_first(record):
    if "force_xyz_n" in record:
        force = record["force_xyz_n"]
        first = record["force_on_member"]
    else:
        force = [sum(scalar * direction[i] for scalar, direction in zip(
            record["force_components_n"], record["force_component_directions_xyz"], strict=True)) for i in range(3)]
        first = record["force_source_receivers"][0]
    return [value if first == record["receivers"][0] else -value for value in force]


def strict_row(method, geometry, state, forces, row_axis, areas, pitch, pins, document):
    """Only a common aligned force row reaches the existing source-bound method."""
    resultant = [sum(force[i] for force in forces) for i in range(3)]
    if norm(resultant) < 1e-9:
        return {"cg": None, "reason_codes": ["zero_or_cancelled_resultant_does_not_define_loaded_row"]}
    direction = [value / norm(resultant) for value in resultant]
    if any(norm(cross(force, direction)) > 1e-8 * max(1.0, norm(force)) or dot(force, direction) < -1e-9
           for force in forces):
        return {"cg": None, "reason_codes": ["simultaneous_bolt_forces_not_common_same_sign_row_load"]}
    if norm(cross(direction, row_axis)) > 1e-8:
        return {"cg": None, "reason_codes": ["load_direction_not_aligned_with_fastener_row"]}
    if any(bolt["physical_receiver_count"] != 2 for bolt in geometry["bolts"]):
        return {"cg": None, "reason_codes": ["continuous_three_receiver_shaft_requires_complete_group_yield_basis"]}
    members = []
    for row in areas:
        cosine = abs(dot(row["grain_xyz"], direction))
        if norm(cross(row["grain_xyz"], direction)) > 1e-8 and cosine > 1e-8:
            return {"cg": None, "reason_codes": ["oblique_member_grain_loading_outside_method_scope"]}
        area = row["gross_area_in2"] if cosine >= 1 - 1e-8 else row["minimum_bearing_length_mm"] * pitch / 25.4**2
        members.append({"member_id": row["member"], "material": "wood", "grain_axis_xyz": row["grain_xyz"],
                        "elastic_modulus_psi": document["E_psi"], "group_factor_area_in2": area,
                        "gross_section_area_in2": row["gross_area_in2"], "thickness_in": row["minimum_bearing_length_mm"] / 25.4,
                        "overall_fastener_group_width_in": pitch / 25.4})
    corner = any(row["source_scope"] == "fresh_first_order_corner_allocation" for row in state["rows"])
    hardware = RETAINED if geometry["bolts"][0]["retained_stock_frames"] is not None else FASTENERS
    bindings = {role: {"source_id": location(path), "sha256": pins[path]} for role, path in (
        ("geometry", REPLAY / "checks.json" if corner else REGISTER),
        ("member_sections", RETAINED if hardware == RETAINED else GRAVITY / "model-inputs.json"),
        ("fastener_product", hardware), ("load_cases", CORNER / "worksheet.json" if corner else FRAME / "comparison.json"))}
    bindings["member_sections"].update(main_member_id=members[0]["member_id"],
                                       side_member_ids=[members[1]["member_id"]], shear_planes=1)
    payload = {"schema": method.SCHEMA_VERSION, "candidate_id": document["candidate"], "revision_id": document["revision_id"],
               "group_id": geometry["group_id"], "scenario_id": "actual_common_aligned_row_only",
               "source_bindings": bindings, "group_geometry": {"row_axis_xyz": row_axis, "fasteners": [
                   {"fastener_id": bolt["axis_id"], "center_in": [x / 25.4 for x in bolt["point_xyz_mm"]],
                    "nominal_diameter_in": bolt["diameter_mm"] / 25.4, "type": "dowel"} for bolt in geometry["bolts"]]},
               "members": {"main": members[0], "side_members": [members[1]], "shear_planes": 1},
               "load_case": {"case_id": state["case_id"], "lateral_resultant_xyz_lbf": [v / 4.4482216152605 for v in resultant]}}
    # The helper requires a coordinator's independent complete input manifest.
    # Source authentication is not that manifest; never self-certify its digest.
    result = method.evaluate_group_action_factor(payload, expected_bindings=None,
                                                 expected_payload_sha256=None)
    return {"cg": result["cg"], "reason_codes": result["reason_codes"], "method_result": result,
            "required_independent_input_record": payload,
            "input_identity_digest": method.canonical_group_record_sha256(payload),
            "independent_coordinator_input_manifest_supplied": False,
            "scope": "Method readiness only; missing independent record cannot establish a Cg or resistance."}


def evaluate_pair(geometry, state, rows, group_factor, adopted_factor, strict_method, pins, document):
    points = [bolt["point_xyz_mm"] for bolt in geometry["bolts"]]
    delta = subtract(points[1], points[0])
    pitch = norm(delta)
    require(pitch > 0, "coincident row axes")
    row_axis, diameter = [x / pitch for x in delta], geometry["bolts"][0]["diameter_mm"]
    require(math.isclose(diameter, geometry["bolts"][1]["diameter_mm"], abs_tol=1e-7), "mixed-diameter pair")
    areas = []
    for member in geometry["receivers"]:
        descriptor = geometry["stock_descriptors"][member]
        frame = geometry["bolts"][0]["retained_stock_frames"]
        if frame is not None:
            require(frame == geometry["bolts"][1]["retained_stock_frames"], "retained pair frames differ")
            grain = frame[member]["basis_columns_global_xyz"][0]
            gross = math.prod(frame[member]["original_dimensions_gqr_mm"][1:])
        else:
            grain = descriptor["axis"]
            gross = descriptor["width_mm"] * descriptor["depth_mm"]
        grain = [x / norm(grain) for x in grain]
        thickness = min(bolt["bearing_lengths_mm"][member] for bolt in geometry["bolts"])
        projection = abs(dot(delta, grain))
        areas.append({"member": member, "grain_xyz": grain, "gross_area_in2": gross / 25.4**2,
                      "minimum_bearing_length_mm": thickness, "pair_projection_on_grain_mm": projection,
                      "declared_perpendicular_area_in2": thickness * projection / 25.4**2})
    scenarios = [{"scenario_id": "original_adopted_equal_EA_total_count_row_sensitivity", "Cg": adopted_factor(
        2, diameter, pitch, min(row["gross_area_in2"] for row in areas) * 25.4**2,
        document["E_psi"] * 0.006894757293168361)}]
    choices = [{"gross": row["gross_area_in2"], **({"declared_perpendicular_width": row["declared_perpendicular_area_in2"]}
               if row["declared_perpendicular_area_in2"] > 1e-12 else {})} for row in areas]
    for first, second in itertools.product(*choices):
        scenarios.append({"scenario_id": "existing_gross_equivalent_area_sensitivity", "main_area_basis": first,
                          "side_area_basis": second, "Cg": group_factor(pitch, diameter / 25.4,
                            choices[0][first], choices[1][second])})
    if "base_header" in geometry["receivers"]:
        scenarios.append({"scenario_id": "existing_header_4D_width_sensitivity", "equivalent_width_mm": 4 * diameter,
                          "Cg": group_factor(pitch, diameter / 25.4,
                            areas[0]["minimum_bearing_length_mm"] * 4 * diameter / 25.4**2,
                            areas[1]["minimum_bearing_length_mm"] * 4 * diameter / 25.4**2)})
    saved = {row["saved_component_Cg"] for row in rows if row["saved_component_Cg"] is not None}
    if saved:
        require(len(saved) == 1, "corner pair uses different saved component group factors")
        scenarios.append({"scenario_id": "existing_finished_corner_component_Cg", "Cg": saved.pop()})
    require(all(math.isfinite(row["Cg"]) and 0 < row["Cg"] <= 1 + 1e-9 for row in scenarios), "invalid scenario factor")
    forces = [force_on_first(row) for row in rows]
    magnitudes = [norm(force) for force in forces]
    factor = min(row["Cg"] for row in scenarios)
    require(all(row["reference_n"] is None or math.isfinite(row["reference_n"]) and row["reference_n"] > 0 for row in rows),
            "invalid saved single-bolt reference")
    references = [None if row["reference_n"] is None else row["reference_n"] * row["Cdelta"] for row in rows]
    indices = [None if reference is None else value / reference / factor
               for value, reference in zip(magnitudes, references, strict=True)]
    for scenario in scenarios:
        scenario["same_state_axis_ratios"] = [None if reference is None else value / reference / scenario["Cg"]
                                              for value, reference in zip(magnitudes, references, strict=True)]
        scenario["same_state_maximum"] = None if any(v is None for v in scenario["same_state_axis_ratios"]) else max(scenario["same_state_axis_ratios"])
    datum = [sum(p[i] for p in points) / 2 for i in range(3)]
    resultant = [sum(force[i] for force in forces) for i in range(3)]
    moments = [cross(subtract(point, datum), force) for point, force in zip(points, forces, strict=True)]
    witnesses = []
    for row, force, index in zip(rows, forces, indices, strict=True):
        along = None if norm(force) < 1e-9 else abs(dot(delta, force)) / norm(force)
        across = None if along is None else math.sqrt(max(0.0, pitch**2 - along**2))
        witnesses.append({"axis_id": row["axis_id"], "force_on_first_receiver_xyz_n": force,
                          "simultaneous_signed_axial_n": row["signed_axial_n"], "reference_n": row["reference_n"],
                          "Cdelta_applied_once": row["Cdelta"], "maximum_row_sensitivity_index": index,
                          "source_scope": row["source_scope"], "null_reason": row["reference_null_reason"],
                          "spacing_parallel_to_own_force_mm": along, "spacing_transverse_to_own_force_mm": across,
                          "quarter_spacing_proximity_diagnostic": None if along is None else across < along / 4})
    strict = strict_row(strict_method, geometry, {**state, "rows": rows}, forces, row_axis, areas, pitch, pins, document)
    finite = all(index is not None for index in indices)
    scalar_index = sum(magnitudes) / (factor * sum(references)) if finite else None
    return {"group_id": geometry["group_id"], "case_id": state["case_id"], "receivers": geometry["receivers"],
            "axis_ids": geometry["axis_ids"], "pitch_mm": pitch, "row_axis_xyz": row_axis, "diameter_mm": diameter,
            "member_area_scenarios": areas, "scenarios": scenarios, "minimum_declared_Cg": factor,
            "same_state_axis_witnesses": witnesses, "maximum_row_sensitivity_index": max(indices) if finite else None,
            "same_state_scalar_sum_over_sum_reference_diagnostic": scalar_index,
            "scalar_sum_scope": "Sum of simultaneous magnitudes/references only; not resultant or couple resistance.",
            "lateral_bore_wrench_datum_xyz_mm": datum,
            "lateral_bore_wrench_on_first_receiver_n_nmm": resultant + [sum(m[i] for m in moments) for i in range(3)],
            "wrench_scope": "Bore resultant forces only. Axial ties, seats, contacts and beam end moments remain separate.",
            "strict_NDS_row_method": strict, "actual_complete_group_resistance_n": None,
            "comparison_status": "METHOD_GAP" if not finite else "SCENARIO_EXCEEDANCE" if max(indices) > 1 else "FINITE_SCENARIOS_BELOW_ONE",
            "specific_uncovered_mechanisms": [
                "Actual oblique or crossed-group load/slip and resistance are not bounded by area scenarios.",
                *sorted({row["reference_null_reason"] for row in rows if row["reference_null_reason"] is not None})],
            **FLAGS}


def build(output, *, end_grain_receipt=None, end_grain_receipt_sha256=None):
    """Parent only: execute the fixed finite worksheet, then authenticate again."""
    output = fresh_output(output)
    document, pins = preparation(end_grain_receipt, end_grain_receipt_sha256)
    row_math = pure_functions(ROW_METHOD, ("group_factor",), {"math": math, "E_PSI": document["E_psi"]})
    positive = pure_functions(POSITIVE_METHOD, ("positive",), {"math": math})["positive"]
    adopted_math = pure_functions(ADOPTED_METHOD, ("conservative_group_factor",), {"math": math, "positive": positive})
    spec = importlib.util.spec_from_file_location("bolt_group_completion_strict_nds", STRICT_METHOD)
    strict = importlib.util.module_from_spec(spec)
    exec(compile(STRICT_METHOD.read_text(), str(STRICT_METHOD), "exec"), strict.__dict__)  # noqa: S102
    by_group_case = defaultdict(list)
    for row in document["lateral_states"]:
        by_group_case[row["group_id"], row["case_id"]].append(row)
    results = []
    for geometry in document["groups"]:
        for case in CASES:
            rows = sorted(by_group_case[geometry["group_id"], case], key=lambda r: r["axis_id"])
            require(len(rows) == 2 and [r["axis_id"] for r in rows] == geometry["axis_ids"], "pair state/order differs")
            results.append(evaluate_pair(geometry, {"case_id": case}, rows, row_math["group_factor"],
                                         adopted_math["conservative_group_factor"], strict, pins, document))
    for pair in document["internal_pair_states"]:
        pair["same_state_total_axial_demand_n"] = sum(row["axial_tension_n"] for row in pair["comparisons"])
        pair["maximum_saved_axial_bolt_reference_index"] = max(
            row["bolt_axial_over_conditional_yield_reference"] for row in pair["comparisons"])
        pair["maximum_saved_axial_nut_reference_index"] = max(
            row["nut_axial_over_conditional_proof_reference"] for row in pair["comparisons"])
        pair["lateral_group_reduction_applied"] = False
        pair["scope"] = "Saved simultaneous axial material proxies only; complete anchorage/deformation remain unqualified."
    eligible = [row for row in results if row["maximum_row_sensitivity_index"] is not None]
    require(eligible, "no finite fresh comparison; inventory cannot complete N02")
    lookup = {(row["group_id"], row["case_id"]): row for row in results}
    duties = []
    for duty in document["duties"]:
        for case in CASES:
            rows = [lookup[group, case] for group in duty["interface_group_ids"]]
            indices = [row["maximum_row_sensitivity_index"] for row in rows]
            internal = [row for row in document["internal_pair_states"] if row["body"] == duty["duty_id"] and row["case_id"] == case]
            duties.append({**duty, "case_id": case, "same_state_lateral_interfaces": [
                {"group_id": row["group_id"], "case_id": case,
                 "maximum_row_sensitivity_index": row["maximum_row_sensitivity_index"],
                 "comparison_status": row["comparison_status"]} for row in rows],
                           "maximum_complete_interface_scenario_index": None if any(v is None for v in indices) else max(indices),
                           "internal_axial_pair_source_join": internal,
                           "actual_complete_duty_resistance_n": None, "complete_joint_acceptance": False})
    result = {"schema": "bolt_group_completion/v1", "status": "FRESH_FINITE_SENSITIVITIES_WITH_EXPLICIT_METHOD_GAPS",
              "census": {**document["census"], "finite_lateral_pair_states": len(eligible),
                         "method_gap_lateral_pair_states": len(results) - len(eligible), "duty_states": len(duties)},
              "case_ids": list(CASES), "gap_scale": 1.0, "fresh_load_sources": document["fresh_load_sources"],
              "modeled_mass_kg": document["modeled_mass_kg"], "dead_load_factor": document["dead_load_factor"],
              "E_psi": document["E_psi"], "groups": results, "duties": duties,
              "unconsumed_receipt_sources_preserved_as_provenance": document["unconsumed_receipt_sources_preserved_as_provenance"],
              "internal_pair_states": document["internal_pair_states"],
              "peak_same_state_scenario": max(eligible, key=lambda r: r["maximum_row_sensitivity_index"]),
              "scenario_exceedances": [row for row in eligible if row["maximum_row_sensitivity_index"] > 1],
              "method_gaps": [row for row in results if row["maximum_row_sensitivity_index"] is None],
              "strict_row_reason_counts": dict(Counter(reason for row in results
                    for reason in row["strict_NDS_row_method"]["reason_codes"])),
              "adopted_obligation": "additional_group_reduction_sensitivity", "comparison_threshold": 1.0,
              "criterion_disposition": "pending", "historical_0_962538_used": False,
              "mechanical_arithmetic_executed": True,
              "limits": ["Finite scenario arithmetic is complete for its eligible rows; no universal oblique group resistance is asserted.",
                         "Each pair and duty retains a single case. No sum of maxima across cases or equal sharing is used.",
                         "Existing Cg is replaced by the scenario Cg, not multiplied a second time; Cdelta/Ceg are applied once.",
                         "The row modulus gamma is a resistance-equation input, not a changed frame spring or delivered stiffness.",
                         "Internal ties retain their saved simultaneous axial proxy comparisons. Lateral Cg does not apply to same-body axial ties.",
                         "N01, N03, splitting, washer, contact and shared-deformation acceptance remain separate."], **FLAGS}
    return publish(output, result, pins, "checks.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("prepare", "build"), default="prepare")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--end-grain-receipt", type=Path)
    parser.add_argument("--end-grain-receipt-sha256")
    args = parser.parse_args()
    api = prepare if args.mode == "prepare" else build
    receipt = api(args.output, end_grain_receipt=args.end_grain_receipt,
                  end_grain_receipt_sha256=args.end_grain_receipt_sha256)
    print(json.dumps({"output": str(args.output), "status": receipt["status"], "census": receipt["census"],
                      "output_sha256": receipt["output_sha256"]}, indent=2))
