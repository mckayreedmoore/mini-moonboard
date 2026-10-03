"""Evaluate only A1 nominal clearance after an area-preserving contact refinement.

The frozen frame equations and gates are reused. Saved complete strong-X
responses supply numerical force guesses, remapped by row identity; guesses
carry no acceptance. This finite comparison is not a six-case replacement.
"""

from __future__ import annotations

import argparse
import fcntl
import inspect
import json
from pathlib import Path

import conic_frame as initialization
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = initialization.ROOT
SOURCE = initialization.frame_run
require, sha, read = initialization.require, initialization.sha, initialization.read
SOURCE_SHA = "27a8a8d2f5d34f1230c86f34385e68a8a895f675683f0dc39199e82c93096bc0"
INITIALIZATION_SHA = "445574a04559e8faa28a3b69bfdbf1a439f6fc25940e0f02837b0927c48f0025"
BASELINE_SHA = "34eb66332a655244a4018e1b77344985e4c145fc946cb2028405a437003d0c41"
PACKETS = {
    12: ("panel-width-operators-attempt01", "panel-width-frame-250-attempt05-conic",
         "5a49b2076e0e32e5fbae90b1da41be6b77973da9057aee860acebaee9cef05f0",
         "ff54c8f662bce93e03b46e47b088408c82471c5956b824e3320afb32b79919ef"),
    20: ("count20-width-grain-operators-attempt02", "count20-width-grain-frame-attempt01",
         "0a8bcf1ac6679d970d72e11e652d31e3406607699230bcf9915bb009e34e9b88",
         "8271a9e6c3ff15440703f78b704e6f601a545b538611c09009afdeb77393eb7c"),
}


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def run(operators, output):
    require(not output.exists(), "Preserve completed and stopped comparisons")
    seed_directory = output.parent / (output.name + "-seed")
    require(not seed_directory.exists(), "Preserve the previous numerical seed")
    assessment = read(operators / "operator-assessment.json")
    count = assessment["screws_per_main_panel"]
    require(count in PACKETS, "Only the declared twelve/twenty-screw scenarios apply")
    source_name, frame_name, comparison_sha, response_sha = PACKETS[count]
    source_operators, source_frame = HERE / source_name, HERE / frame_name
    require(assessment["source_operator_directory"] == str(source_operators.relative_to(ROOT)),
            "Refinement source operator differs")
    baseline_path = SOURCE.FRAME / "frame-results.json"
    pins = {Path(__file__): sha(Path(__file__)), Path(SOURCE.__file__): SOURCE_SHA,
            Path(initialization.__file__): INITIALIZATION_SHA, baseline_path: BASELINE_SHA,
            source_frame / "comparison.json": comparison_sha,
            source_frame / "response.npz": response_sha,
            operators / "operator-assessment.json": sha(operators / "operator-assessment.json"),
            source_operators / "row-identities.json": sha(source_operators / "row-identities.json")}
    pins.update({ROOT / name: digest for name, digest in assessment["source_sha256"].items()})
    pins.update({operators / name: digest for name, digest in assessment["output_sha256"].items()})
    source_assessment = read(source_operators / "operator-assessment.json")
    require(pins[source_operators / "row-identities.json"]
            == source_assessment["output_sha256"]["row-identities.json"], "Source row identity changed")
    for path, digest in pins.items():
        require(sha(path) == digest, "Changed frozen input: " + str(path))
    rows = read(operators / "row-identities.json")
    old_rows = read(source_operators / "row-identities.json")
    old_index = {row["row_id"]: row["row"] for row in old_rows}
    new_index = {row["row_id"]: row["row"] for row in rows}
    removed = set(old_index) - set(new_index)
    added = set(new_index) - set(old_index)
    require(len(removed) == 22 and len(added) == 44
            and removed == set(assessment["removed_contact_row_ids"])
            and added == set(assessment["appended_contact_row_ids"]), "Unexpected changed row set")
    require(len(old_rows) == assessment["source_scalar_row_count"]
            and len(rows) == len(old_rows) + 22, "Unexpected refined scalar inventory")
    screw_total = 66 if count == 12 else 98
    require(sum(row["ownership"]["role"] == "non_qualifying_parametric_screw_withdrawal"
                for row in rows) == screw_total, "Screw inventory changed")
    require(all(row["ownership"]["role"] == "timber_or_panel_contact"
                for row in rows if row["row_id"] in added), "Non-contact row appended")
    baseline = read(baseline_path)
    require(abs(assessment["modeled_mass_kg"] - baseline["modeled_mass_kg"]) < 1e-9,
            "Comparison mass changed")
    floor_members = sorted({row["ownership"]["first_body"] for row in rows
                            if row["ownership"]["second_body"] == "floor"})
    guesses = {}
    with np.load(source_frame / "response.npz", allow_pickle=False) as saved:
        for case in baseline["cases"]:
            case_id = case["case_id"]
            force = saved[case_id + "_gap_raw_force_n"]
            require(force.shape == (len(old_rows),), "Source force inventory differs")
            mapped = np.zeros(len(rows))
            for name in set(old_index) & set(new_index):
                mapped[new_index[name]] = force[old_index[name]]
            guesses[case_id + "_force_n"] = mapped
            guesses[case_id + "_bearing_mask"] = np.array([
                sum(mapped[row["row"]] for row in rows
                    if row["ownership"]["role"] == "floor_normal"
                    and row["ownership"]["first_body"] == member) > 1e-7
                for member in floor_members
            ])
    seed_directory.mkdir(parents=True)
    np.savez_compressed(seed_directory / "frame-response.npz", **guesses)
    baseline["response_sha256"] = sha(seed_directory / "frame-response.npz")
    baseline["numerical_seed_only"] = True
    baseline["source_comparison_sha256"] = comparison_sha
    baseline["source_response_sha256"] = response_sha
    baseline["seed_row_mapping"] = "Common row identities copied; forty-four new contacts start at zero force"
    write(seed_directory / "frame-results.json", baseline)
    pins[seed_directory / "frame-response.npz"] = baseline["response_sha256"]
    pins[seed_directory / "frame-results.json"] = sha(seed_directory / "frame-results.json")
    text = inspect.getsource(SOURCE.run)
    substitutions = {
        "len(screw_lateral) == 132 and len(screw_axial) == 66":
            f"len(screw_lateral) == {2 * screw_total} and len(screw_axial) == {screw_total}",
        "for gap_scale in (0.0, 1.0):": "for gap_scale in (1.0,):",
        'for index, source in enumerate(baseline["cases"]):':
            'for index, source in enumerate(baseline["cases"]):\n'
            '                if source["case_id"] != "a1-rear":\n'
            '                    continue',
    }
    require(all(text.count(site) == 1 for site in substitutions), "Frozen adaptation site changed")
    for old, new in substitutions.items():
        text = text.replace(old, new)
    namespace = SOURCE.__dict__.copy()
    exec(compile(text, "<patch59-a1-nominal-frame>", "exec"), namespace)  # noqa: S102 -- pinned source and exact checked substitutions
    preserved_run = SOURCE.run

    def configured_run(*args, **kwargs):
        kwargs.update(seed_directory=seed_directory, qp_seed=False)
        return namespace["run"](*args, **kwargs)

    SOURCE.run = configured_run
    try:
        initialization.run(output, operators)
    finally:
        SOURCE.run = preserved_run
        if output.exists():
            target = output / ("comparison.json" if (output / "comparison.json").exists() else "stop.json")
            if target.exists():
                for path, digest in pins.items():
                    require(sha(path) == digest, "Input changed during comparison")
                report = read(target)
                report["source_sha256"].update({str(path.relative_to(ROOT)): digest
                                                for path, digest in pins.items()})
                report.update(finite_case_scope=[{"case_id": "a1-rear", "gap_scale": 1.0}],
                              screws_per_main_panel=count, hypothetical_panel_screw_total=screw_total,
                              physical_inventory_change_selected=False, full_six_case_frame=False,
                              source_force_guess_acceptance_transferred=False,
                              mechanical_equations_and_gates_changed=False,
                              patch59_contact_refinement_only=True)
                (output / "patch-frame-producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
                (output / "adapted-run.py.snapshot").write_text(text)
                report["patch_adapted_run_sha256"] = sha(output / "adapted-run.py.snapshot")
                write(target, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operators", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle", "Shared mechanics slot occupied")
        run(args.operators.resolve(), args.output.resolve())
