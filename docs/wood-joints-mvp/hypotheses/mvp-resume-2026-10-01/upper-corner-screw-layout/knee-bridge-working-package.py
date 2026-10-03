"""Bind the fresh frame, local actions and conditional proposal shop recipe.

This performs inventory and provenance arithmetic only. It runs no mechanics,
CAD, native solver, software test or historical producer pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-working-package"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    HERE / "rawlocal/knee-bridge-integration/attempt02/manifest.json":
        "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c",
    HERE / "rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json":
        "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json":
        "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    HERE / "rawlocal/knee-bridge-response/attempt02/receipt.json":
        "57163aa9f4e1ed7af338d29c4893f5614c21bd422e841532cf67feb67ac20933",
    HERE / "rawlocal/knee-bridge-corner-replay/attempt01/receipt.json":
        "50898edc4d0d977c7522c3c30866504235f847ee6d3777345114afb4d86cd52d",
    HERE / "rawlocal/knee-bridge-washer/attempt02/checks.json":
        "d3ad497f8990bca5f18d691d77cd90646b3d40a09d02331c6adf36aa900a2a9d",
    HERE / "rawlocal/knee-bridge-washer/attempt02/receipt.json":
        "041067657335395f4b1723a237e11574a0ed0b3efcba4e95f32e25db77d3630f",
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
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def build(output, knee_receipt, knee_sha256, worksheets):
    """Parent supplies the exact completed knee and component receipt hashes."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh owned child required")
    pins = {**PINS, Path(__file__).resolve(): sha(__file__)}

    def pin(path, digest):
        path = Path(path).resolve()
        require(path not in pins or pins[path] == digest, "conflicting pin: " + key(path))
        require(sha(path) == digest, "source changed: " + key(path))
        pins[path] = digest

    def receipt(path, digest):
        path = Path(path).resolve()
        pin(path, digest)
        document = read(path)
        for field in ("source_sha256", "classifier_source_sha256"):
            for relative, expected in document.get(field, {}).items():
                pin(ROOT / relative, expected)
        for relative, expected in document["output_sha256"].items():
            artifact = (path.parent / relative).resolve()
            require(artifact.is_relative_to(path.parent), "receipt artifact leaves packet")
            pin(artifact, expected)
        return document

    for path, digest in list(pins.items()):
        pin(path, digest)
    recipe = read(HERE / "rawlocal/knee-bridge-integration/attempt02/manifest.json")
    gravity = read(HERE / "rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json")
    frame = read(HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json")
    require(gravity["operator_ready"] is True and gravity["case_ids"] == list(CASES),
            "fresh gravity incomplete")
    require(frame["source_sha256"][key(HERE / "rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json")]
            == PINS[HERE / "rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json"],
            "frame consumed another gravity packet")
    require(frame["dead_load_factor"] == gravity["dead_load_factor"]
            and frame["modeled_mass_kg"] == gravity["modeled_mass_kg"], "gravity metadata differs")
    require(len(frame["states"]) == 12 and [s["case_id"] for s in frame["states"] if s["gap_scale"] == 1]
            == list(CASES), "six zero/nominal states incomplete")
    require(all(s["status"] in {"PASS_CONDITIONAL_COUPLED_FRAME_LAWS",
                                "PASS_CONDITIONAL_LAWS_WITH_BOUNDED_SEATING"}
                for s in frame["states"]), "frame law comparison incomplete")
    require(frame["climber_load_scale"] == frame["horizontal_load_scale"] == 1,
            "live load scales differ")
    for relative, digest in gravity["output_sha256"].items():
        pin(HERE / "rawlocal/knee-bridge-gravity/attempt01" / relative, digest)
    for document in (recipe, gravity, frame):
        for relative, digest in document["source_sha256"].items():
            pin(ROOT / relative, digest)
    export_path = HERE / "rawlocal/knee-bridge-response/attempt02/receipt.json"
    receipt(export_path, PINS[export_path])
    corner_path = HERE / "rawlocal/knee-bridge-corner-replay/attempt01/receipt.json"
    receipt(corner_path, PINS[corner_path])
    corner = read(corner_path.with_name("checks.json"))
    require(corner["status"] == "COMPLETE_FRESH_FIRST_ORDER_LOCAL_FORCES"
            and corner["failure"] is None, "corner transfers incomplete")
    knee_receipt = Path(knee_receipt).resolve()
    require(knee_receipt.is_relative_to(HERE / "rawlocal/knee-bridge-joint-replay"),
            "knee receipt outside fresh replay")
    receipt(knee_receipt, knee_sha256)
    knee = read(knee_receipt.with_name("checks.json"))
    require(knee["status"] == "FINITE_FRESH_KNEE_STATIC_REPLAY_COMPLETE"
            and knee["all_named_reference_screens_satisfied"] is True, "knee static comparison incomplete")
    require(len(knee["states"]) == 12 and knee["internal_allocation_count"] == 24,
            "knee state census differs")
    worksheet_bindings = []
    expected_worksheets = {"knee-bridge-other-bolts", "knee-bridge-members", "knee-bridge-top-rail",
                           "knee-bridge-corner-references", "knee-bridge-remaining-sections",
                           "knee-bridge-continuous-shafts"}
    require(len(worksheets) == 6 and {Path(p).parent.parent.name for p, _ in worksheets}
            == expected_worksheets, "six completed finite worksheet receipts required")
    shaft_suite = None
    for path, digest in worksheets:
        path = Path(path).resolve()
        require(path.is_relative_to(HERE / "rawlocal") and path.name == "receipt.json",
                "worksheet must be a result receipt in this packet")
        record = receipt(path, digest)
        require(not record.get("physical_release", False), "worksheet claims physical release")
        require(not record.get("status", "").startswith("STOP"), "worksheet stopped")
        require(record["source_sha256"].get(key(HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json"))
                == PINS[HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json"],
                "worksheet did not consume the fresh frame")
        worksheet_bindings.append({"receipt": key(path), "sha256": digest})
        if path.parent.parent.name == "knee-bridge-continuous-shafts":
            shaft_suite = read(path.with_name("suite.json"))
    require(shaft_suite is not None and shaft_suite["status"]
            == "COMPLETE_FRESH_24_SHAFT_STATES_AND_96_PLACEMENTS"
            and shaft_suite["all24_nominal_completed"] is True, "continuous shaft replay incomplete")
    global_records = [json.loads(line) for line in export_path.with_name("global-demands.jsonl").read_text().splitlines()]
    bolts = {(row["case_id"], row["axis_id"]): row for row in global_records if row["kind"] == "structural_bolt"}
    panels = [row for row in global_records if row["kind"] != "structural_bolt"]
    local = {(row["case_id"], row["axis_id"]): row for row in corner["same_state_bolt_actions"]}
    shafts = {(row["case_id"], row["axis_id"]): row for row in shaft_suite["states"]}
    require(len(bolts) == 624 and len(local) == 96 and len(panels) == 396,
            "fresh existing-force census differs")
    require(len(shafts) == 24 and set(local).isdisjoint(shafts)
            and (set(local) | set(shafts)).issubset(bolts), "local allocation ownership differs")
    records = []
    for identity, global_record in bolts.items():
        allocation = ("fresh_corner_local" if identity in local else
                      "fresh_continuous_shaft" if identity in shafts else "fresh_global")
        if identity in shafts:
            require(shafts[identity]["independent_reference_equilibrium_closed"] is True
                    and abs(shafts[identity]["physical_axial_tie_n"] - global_record["signed_axial_n"]) <= 1e-9,
                    "continuous shaft same-state tie or closure differs")
            pin(ROOT / shafts[identity]["result_path"], shafts[identity]["result_sha256"])
        records.append({"case_id": identity[0], "axis_id": identity[1],
                        "allocation_kind": allocation,
                        "global_boundary_allocation": global_record,
                        "local_action_allocation": local.get(identity, shafts.get(identity)),
                        "complete_joint_acceptance": False})
    axes = {row["canonical_axis_id"]: row for row in recipe["proposed_internal_bolt_axes"]}
    require(len(axes) == 4, "internal axis census differs")
    for state in knee["states"]:
        for comparison in state["axial_stack_reference_comparisons"]:
            axis_id = comparison["canonical_axis_id"]
            axis = axes[axis_id]
            tension = comparison["axial_tension_n"]
            require(axis["body"] == state["block"] and math.isfinite(tension) and tension >= 0,
                    "internal allocation body or T differs")
            records.append({"case_id": state["case_id"], "axis_id": axis_id,
                            "allocation_kind": "fresh_static_internal_axial_pair", "body": axis["body"],
                            "signed_axial_n": tension, "end_seats": axis["end_seats"],
                            "global_receiver_interface": False, "global_operator_row": None,
                            "local_elastic_compatibility_solved": False, "complete_joint_acceptance": False})
    washer_path = HERE / "rawlocal/knee-bridge-washer/attempt02/receipt.json"
    receipt(washer_path, PINS[washer_path])
    washer = read(washer_path.with_name("checks.json"))
    require(washer["status"] == "FINITE_KNEE_BRIDGE_WASHER_HYPOTHESIS"
            and washer["failure"] is None and washer["state"]["M_magnitude_nmm"] == 0,
            "saved concentric washer envelope incomplete")
    maximum_tension = max(r["signed_axial_n"] for r in records
                          if r["allocation_kind"] == "fresh_static_internal_axial_pair")
    require(maximum_tension <= washer["state"]["T_n"], "fresh tie exceeds the saved washer envelope")
    require({r["axis_id"] for r in washer["proposal_bolt_loads"]} == set(axes),
            "washer envelope refers to other bridge axes")
    require(washer["model"]["positive_homogeneity_scope"]["fixed_conditions"]
            == ["geometry", "linear elastic plate", "zero initial gap", "no preload"],
            "washer homogeneity conditions differ")
    require(len(records) == len({(r["case_id"], r["axis_id"]) for r in records}) == 648,
            "108 physical bolt axes by six cases must be unique")
    existing_axes = []
    for source_axis in recipe["existing_bolt_axes"]:
        axis_id = source_axis["axis_id"]
        axis = {field: source_axis[field] for field in
                ("axis_id", "kind", "receivers", "axis_point_xyz_mm", "axis_xyz", "interfaces",
                 "outer_tie", "geometry_reference")}
        indices = [index for index, record in enumerate(records) if record["axis_id"] == axis_id]
        require(len(indices) == 6 and {records[index]["case_id"] for index in indices} == set(CASES),
                "existing axis fresh case indices incomplete")
        axis.update(force_case_record_indices=indices,
                    current_force_authority=records[indices[0]]["allocation_kind"])
        existing_axes.append(axis)
    members = recipe["geometry"]["effective_members"]
    require(len(members) == len({r["body"] for r in members}) == 50, "effective body census differs")
    for member in members:
        binding = member["effective_proposal_step"]
        pin(ROOT / binding["path"], binding["sha256"])
    for binding in recipe["authority"]["files_unchanged"]:
        pin(ROOT / binding["source"], binding["sha256"])
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    for name, rows in (("bolt-actions.jsonl", records), ("panel-actions.jsonl", panels)):
        with (output / name).open("w") as stream:
            for row in rows:
                stream.write(json.dumps(row, allow_nan=False) + "\n")
    manifest = {
        "schema": "knee-bridge-conditional-working-package/v1", "status": "CONDITIONAL_WORKING_PACKET_BOUND",
        "case_ids": list(CASES), "modeled_mass_kg": gravity["modeled_mass_kg"],
        "dead_load_factor": gravity["dead_load_factor"], "source_load_identity": recipe["source_load_identity"],
        "geometry": {**recipe["geometry"], "global_stiffness_basis": "FILLED-BORE_GROSS_APPROXIMATION",
                     "gravity_matches_modified_solid_and_added_hardware_recipe": True},
        "existing_bolt_axes": existing_axes,
        "proposed_internal_bolt_axes": recipe["proposed_internal_bolt_axes"], "axis_aliases": recipe["axis_aliases"],
        "planning_order": recipe["planning_order"], "worksheet_receipts": worksheet_bindings,
        "concentric_washer_envelope_reuse": {
            "source": key(washer_path.with_name("checks.json")), "sha256": PINS[washer_path.with_name("checks.json")],
            "fresh_maximum_T_n": maximum_tension, "saved_envelope_T_n": washer["state"]["T_n"],
            "maximum_positive_load_scale": maximum_tension / washer["state"]["T_n"],
            "conservative_saved_stress_ratio": washer["state"]["elastic_proxy_over_assumed_Fy"],
            "M_nmm": 0, "new_washer_solve": False, "actual_washer_capacity_qualified": False},
        "census": {"bodies": 50, "timber_blanks": 44, "blocks": 24, "bolts": 108, "nuts": 108,
                   "washers": 216, "Hillman_screws": 66, "bolt_case_records": 648, "screw_case_records": 396,
                   "local_corner_case_records": 96, "local_continuous_shaft_case_records": 24,
                   "global_existing_case_records": 504,
                   "static_internal_case_records": 24},
        "frame_response": {"comparison": key(HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json"),
                           "sha256": PINS[HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json"]},
        "limits": ["Filled-bore gross stiffness and the existing finite contact laws remain the simple frame approximation.",
                   "Sixteen corner axes and four continuous shafts use fresh local allocations; 84 other existing axes retain fresh global actions.",
                   "Two same-body bridge pairs use finite static allocations, without an elastic local compatibility solution or frame feedback.",
                   "The Hillman head-reference exception and actual screw, hardware, floor and installation uncertainties remain explicit.",
                   "Historical qualification results retain their original load scope; no old local acceptance transfers.",
                   "The proposal remains unadopted; the 47 pending criteria and eight false authority flags remain unchanged."],
        "proposal_adopted": False, "complete_joint_acceptance": False, "physical_release": False,
        "fabrication_release": False, "tests_run": False, "native_or_CAD_or_frame_run": False,
        "source_sha256": {key(path): digest for path, digest in sorted(pins.items())},
    }
    write(output / "manifest.json", manifest)
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during binding: " + key(path))
    write(output / "receipt.json", {"source_sha256": manifest["source_sha256"],
          "output_sha256": {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file()},
          "census": manifest["census"], "status": manifest["status"], "physical_release": False})
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--knee-receipt", required=True, type=Path)
    parser.add_argument("--knee-sha256", required=True)
    parser.add_argument("--worksheet", nargs=2, action="append", default=[], metavar=("RECEIPT", "SHA256"))
    args = parser.parse_args()
    result = build(args.output, args.knee_receipt, args.knee_sha256, args.worksheet)
    print(json.dumps({"status": result["status"], "census": result["census"]}))
