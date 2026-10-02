"""Generic NDS No. 10 lateral and same-state combined reference arithmetic.

Read frozen panel screw CSVs; never regenerate their force allocations. These
contacting-member, standard rolled-thread references are declared hypotheses,
not measured Hillman properties or adjusted connection capacities.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OUTPUT = HERE / "results/lateral-attempt01"
CACHE = ROOT / "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache"
sys.path.insert(0, str(ROOT))
from fea.dowel_yield import single_shear

N_PER_LBF = 4.4482216152605
D_IN = 0.190
DR_IN = 0.152
FYB_PSI = 80000.0
PLYWOOD_MM = 18.25625
LENGTH_MM = 63.5
TIP_MM = 2 * D_IN * 25.4
NOMINAL_P_MM = LENGTH_MM - PLYWOOD_MM
THREAD_P_MM = (30.0, 38.1, LENGTH_MM * 2 / 3, NOMINAL_P_MM)
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
CASES = {"a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"}
DEFAULTS = {
    "attempt05-baseline": {
        "comparison.json": "da36efb1d343f5462fdda87055c38b635767e517a3ead5ac8e69922dbe4cc112",
        "screw-states.csv": "7035199a52ae0fdcdbc3b65ed53fe9f6f0e87f8c7b829a9ccc5ad3247fe1c892",
    },
    "attempt06-k1000": {
        "comparison.json": "ac1a6f0788661c9404e838d268ecabd66b45b6a69f8e26ec10bd3ae2abd1f3c3",
        "screw-states.csv": "99b6b0b0d081464a40375716ac94d873468c6313dcae3fbdafb8b87d8775bd84",
    },
    "attempt07-k100": {
        "comparison.json": "45be72a715652f9770a0235c3468528cc8e15a85b35c49ed55d445c495c5ded8",
        "screw-states.csv": "d8c2048d299d083e2e954e95e240169ee1432199803daf3baab408871ed4c27e",
    },
}
PDF_PINS = {
    "chapter12-2024-awc-20260911.pdf": "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
    "appendix-2024-awc-20260911.pdf": "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31",
    "chapter11-2024-awc-20260911.pdf": "45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33",
}
RECEIVER = ROOT / "docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01/receiver-transfer.json"
MODEL_INPUTS = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
HELPER = ROOT / "fea/dowel_yield.py"
DATA_PINS = {
    RECEIVER: "0ac0e30d582322f8919277aabec3af134c7bf5ecb2b0523d649622bcd4a47534",
    MODEL_INPUTS: "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    HELPER: "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def generic_lateral_reference(plywood_fe_psi):
    """Six contacting-member modes: root D, actual plywood thickness, tip rule.

    F_em=4650 psi is the rounded Table 12.3.3 value for DF-L G=.50,
    D<1/4 inch. Small-diameter bearing is independent of load/grain angle.
    R_d=K_D=2.2; the K_theta footnote applies to nominal D>=1/4 inch,
    and does not apply to this nominal .190-inch wood screw.
    """
    require(plywood_fe_psi in (3350.0, 4650.0), "undeclared plywood reference")
    require(NOMINAL_P_MM >= 6 * D_IN * 25.4, "minimum wood screw penetration not met")
    main_mm = NOMINAL_P_MM - TIP_MM / 2
    moment = FYB_PSI * DR_IN**3 / 6
    result = single_shear(
        main_length_in=main_mm / 25.4, side_length_in=PLYWOOD_MM / 25.4,
        main_bearing_lb_in=4650 * DR_IN, side_bearing_lb_in=plywood_fe_psi * DR_IN,
        main_yield_moment_lb_in=moment, side_yield_moment_lb_in=moment,
        gap_in=0, reduction_terms=dict.fromkeys(MODES, 2.2),
    )
    return {
        "plywood_fe_psi": plywood_fe_psi, "timber_fe_psi": 4650.0,
        "nominal_diameter_in": D_IN, "effective_root_diameter_in": DR_IN,
        "Fyb_psi_hypothesis": FYB_PSI, "Rd_all_modes": 2.2,
        "plywood_bearing_length_mm": PLYWOOD_MM, "timber_bearing_length_mm": main_mm,
        "nominal_tip_penetration_mm": NOMINAL_P_MM, "tapered_tip_mm_hypothesis": TIP_MM,
        "six_mode_references_n": {mode: result["reference_values_lbf"][mode] * N_PER_LBF for mode in MODES},
        "governing_mode": result["governing_mode"],
        "unadjusted_generic_lateral_reference_n": result["reference_lateral_lbf"] * N_PER_LBF,
        "contacting_faces_hypothesis": True, "product_applicability_established": False,
    }


def combined_reference(V, T, Z, A):
    """NDS 12.4-1 at unit adjustment hypotheses, using this same V/T tuple."""
    R = math.hypot(V, T)
    lateral = V * V / (R * Z) if R else 0.0
    withdrawal = T * T / (R * A) if R else 0.0
    if not R:
        required, status = 0.0, "FINITE"
    elif withdrawal < 1:
        required, status = V * V / (R * (1 - withdrawal)), "FINITE"
    else:
        required, status = None, "NO_FINITE_LATERAL_REFERENCE"
    return {"resultant_n": R, "lateral_term": lateral, "withdrawal_term": withdrawal,
            "combined_index": lateral + withdrawal,
            "required_lateral_reference_n": required, "required_lateral_status": status}


def load_packet(path, pins):
    """Bind the saved producer snapshot, not the concurrently maintained source."""
    receipt = read(path / "receipt.json")
    for name, digest in receipt["artifact_sha256"].items():
        if name in ("comparison.json", "screw-states.csv", "producer.py.snapshot"):
            require(sha(path / name) == digest, "saved packet artifact changed: " + str(path / name))
            pins[path / name] = digest
    pins[path / "receipt.json"] = sha(path / "receipt.json")
    if path.name in DEFAULTS:
        for name, digest in DEFAULTS[path.name].items():
            require(pins[path / name] == digest, "different frozen allocation: " + path.name)
    comparison = read(path / "comparison.json")
    require(comparison["producer_sha256"] == pins[path / "producer.py.snapshot"], "saved comparison/snapshot mismatch")
    rows = list(csv.DictReader((path / "screw-states.csv").open()))
    keys = {(r["case_id"], float(r["gap_scale"]), r["axis_id"]) for r in rows}
    require(len(rows) == len(keys) == 792 and len({r["axis_id"] for r in rows}) == 66, "saved state census mismatch")
    require({r["case_id"] for r in rows} == CASES and {float(r["gap_scale"]) for r in rows} == {0, 1}, "case or gap census mismatch")
    frame_paths = [ROOT / name for name in comparison["source_sha256"] if name.endswith("comparison.json")]
    require(len(frame_paths) == 1, "ambiguous saved frame metadata")
    frame_path = frame_paths[0]
    pins[frame_path] = comparison["source_sha256"][str(frame_path.relative_to(ROOT))]
    require(sha(frame_path) == pins[frame_path], "saved frame metadata changed")
    frame = read(frame_path)
    if "panel_screw_stiffness_n_per_mm" in frame:
        lateral_k = frame["panel_screw_stiffness_n_per_mm"]["lateral_components"]
    else:
        # The older baseline predates explicit override metadata. Its frozen
        # scalar law inventory provides the unchanged lateral values directly.
        law_path = HERE.parent / "corner-frame-attempt01/row-identities.json"
        pins[law_path] = comparison["source_sha256"][str(law_path.relative_to(ROOT))]
        require(sha(law_path) == pins[law_path], "baseline scalar law inventory changed")
        lateral_k = [r["law"]["stiffness_N_per_mm"] for r in read(law_path)
                     if r["ownership"]["role"] == "panel_screw_lateral_plane"]
    require(len(lateral_k) == 132 and all(abs(x - 2689.679) < 0.0005 for x in lateral_k), "lateral stiffness changed")
    return rows, comparison


def run(sources, output=OUTPUT):
    output = Path(output)
    require(not output.is_symlink(), "output must be a fresh directory, not a symlink")
    output = output.resolve()
    require(output.parent == (HERE / "results").resolve()
            and re.fullmatch(r"lateral-attempt[0-9]+", output.name),
            "output must be results/lateral-attempt followed by digits")
    require(not output.exists(), "preserve existing lateral output directory")
    sources = [Path(source).resolve() for source in sources]
    require(all(source.is_relative_to(ROOT) for source in sources), "source packets must be inside the shared repository")
    require(1 <= len(sources) <= 3 and len(set(sources)) == len(sources), "consume one to three distinct completed packets")
    producer_path = Path(__file__).resolve()
    producer_bytes = producer_path.read_bytes()
    producer_hash = hashlib.sha256(producer_bytes).hexdigest()
    pins = {CACHE / name: digest for name, digest in PDF_PINS.items()} | DATA_PINS
    pins[producer_path] = producer_hash
    for path, digest in pins.items():
        require(sha(path) == digest, "consumed source changed: " + str(path))
    receiver = {r["axis_id"]: r for r in read(RECEIVER)["inventory"]["axes"]}
    members = {r["member_id"]: r["reduced_geometry_descriptor"] for r in read(MODEL_INPUTS)["members"]}
    max_grain_dot = max(abs(sum(x * y for x, y in zip(r["axis_global_xyz"], members[r["receiver_member"]]["grain_global_xyz"], strict=True))) for r in receiver.values())
    require(max_grain_dot < 1e-8, "saved receiver is not a side-grain insertion")
    require(all(abs(r["nominal_embedment_envelope"]["raw_receiver_full_section_equivalent_length_mm"] - NOMINAL_P_MM) < 1e-6 for r in receiver.values()), "different nominal receiver overlap")

    lateral = {"plywood_other_G042": generic_lateral_reference(3350.0),
               "plywood_structural1_marine_G050": generic_lateral_reference(4650.0)}
    scenarios = {}
    for label, reference in lateral.items():
        for j, p in enumerate(THREAD_P_MM):
            scenarios[f"{label}_thread_p{j}"] = {
                "effective_thread_penetration_mm_hypothesis": p,
                "unadjusted_withdrawal_reference_n": 2850 * .5**2 * D_IN * p / 25.4 * N_PER_LBF,
                "unadjusted_lateral_reference_n": reference["unadjusted_generic_lateral_reference_n"],
                "lateral_reference_label": label,
            }
    records, allocations = [], []
    for source in sources:
        rows, comparison = load_packet(source, pins)
        current = []
        head = max(r["unadjusted_generic_head_reference_n"] for r in comparison["generic_head_reference_sensitivities"])
        for raw in rows:
            axis = receiver[raw["axis_id"]]
            require(raw["panel"] == axis["panel_member"] and raw["receiver"] == axis["receiver_member"], "current receiver join differs")
            V, T = float(raw["lateral_resultant_n"]), float(raw["withdrawal_n"])
            require(V >= 0 and T >= -1e-6 and all(math.isfinite(x) for x in (V, T)), "invalid saved demand")
            require(math.isclose(V, math.hypot(float(raw["lateral_1_signed_n"]), float(raw["lateral_2_signed_n"])), abs_tol=1e-8), "saved lateral resultant differs")
            record = {"allocation": source.name, **{name: raw[name] for name in (
                "case_id", "gap_scale", "axis_id", "panel", "receiver", "withdrawal_n",
                "lateral_1_signed_n", "lateral_2_signed_n", "lateral_resultant_n",
                "withdrawal_stiffness_hypothesis_n_per_mm", "screw_relative_opening_mm")}}
            record["root_mean_tensile_stress_mpa_demand_only"] = T / (math.pi * (DR_IN * 25.4)**2 / 4)
            record["separate_head_most_favorable_unadjusted_reference_n"] = head
            record["separate_head_reference_ratio"] = T / head
            for label, s in scenarios.items():
                combined = combined_reference(V, T, s["unadjusted_lateral_reference_n"], s["unadjusted_withdrawal_reference_n"])
                record[label + "/combined_index"] = combined["combined_index"]
            favorable = combined_reference(V, T, lateral["plywood_structural1_marine_G050"]["unadjusted_generic_lateral_reference_n"], scenarios["plywood_structural1_marine_G050_thread_p3"]["unadjusted_withdrawal_reference_n"])
            record.update({"full_thread/lateral_term": favorable["lateral_term"],
                           "full_thread/withdrawal_term": favorable["withdrawal_term"],
                           "full_thread/required_lateral_reference_n": favorable["required_lateral_reference_n"],
                           "full_thread/required_lateral_status": favorable["required_lateral_status"]})
            saved_required = raw["NDS12_4_required_lateral_reference_n_G050_45mm"]
            require((saved_required == "" and favorable["required_lateral_reference_n"] is None) or (saved_required != "" and math.isclose(float(saved_required), favorable["required_lateral_reference_n"], rel_tol=1e-12, abs_tol=1e-8)), "same-state required-reference threshold differs")
            current.append(record)
        summaries = []
        for gap in (0, 1):
            selected = [r for r in current if float(r["gap_scale"]) == gap]
            finite = [r for r in selected if r["full_thread/required_lateral_status"] == "FINITE"]
            summaries.append({
                "gap_scale": gap, "screw_states": len(selected),
                "same_state_peak_lateral": max(selected, key=lambda r: float(r["lateral_resultant_n"])),
                "same_state_peak_withdrawal": max(selected, key=lambda r: float(r["withdrawal_n"])),
                "full_thread_no_finite_lateral_reference_state_count": len(selected) - len(finite),
                "full_thread_peak_finite_required_lateral_reference": max(finite, key=lambda r: r["full_thread/required_lateral_reference_n"]) if finite else None,
                "scenario_envelopes": {label: {
                    "maximum_same_state_combined_index": max(r[label + "/combined_index"] for r in selected),
                    "states_exceeding_unadjusted_combined_reference": sum(r[label + "/combined_index"] > 1 for r in selected),
                    "governing_same_state": max(selected, key=lambda r: r[label + "/combined_index"]),
                } for label in scenarios},
                "separate_peak_head_ratio": max(r["separate_head_reference_ratio"] for r in selected),
            })
        allocations.append({"source_packet": str(source.relative_to(ROOT)), "withdrawal_stiffness_hypothesis_n_per_mm": comparison["withdrawal_stiffness_hypotheses_n_per_mm"], "lateral_stiffness_unchanged": True, "head_reference_bounds_n": [min(r["unadjusted_generic_head_reference_n"] for r in comparison["generic_head_reference_sensitivities"]), head], "summaries": summaries})
        records.extend(current)
    replay_argv = ["uv", "run", "python", str(producer_path.relative_to(ROOT))]
    for source in sources:
        replay_argv.extend(["--source", str(source)])
    replay_argv.extend(["--output", str(output)])
    report = {
        "schema": "generic_panel_screw_lateral_same_state_reference/v1",
        "classification": "DECLARED_GENERIC_LATERAL_AND_COMBINED_REFERENCE_DEFICITS",
        "screw_states_consumed": len(records), "force_allocations_regenerated": False,
        "lateral_references": lateral, "combined_scenarios": scenarios,
        "allocations": allocations, "maximum_axis_grain_dot": max_grain_dot,
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "producer_sha256": producer_hash,
        "producer_version": "fresh-output-v2",
        "adjustments": {"all_applied_multipliers": 1.0, "adjusted_capacity_adopted": False,
                        "Cg_small_diameter_rule": 1.0, "C_delta_small_diameter_rule": 1.0,
                        "duration_service_temperature_treatment_applicability_established": False},
        "measured_product_laws_established": False, "hillman_resistance_established": False,
        "actual_thread_root_and_Fyb_established": False, "steel_root_tension_capacity_established": False,
        "head_capacity_adopted": False, "complete_joint_acceptance": False,
        "formal_acceptance": False, "native_acceptance": False, "physical_release": False,
        "command": "PYTHONDONTWRITEBYTECODE=1 " + shlex.join(replay_argv),
        "limits": [
            "No Hillman, SPAX or SDS resistance/stiffness transfer. Standard No.10 nominal/root geometry and Fyb are hypotheses.",
            "NDS yield equations assume contacting faces; saved screw opening and contact allocation do not establish that condition at each axis.",
            "Full nominal timber projection does not establish effective installed thread penetration. The full-thread withdrawal case is explicitly favorable.",
            "Root bending reference does not establish tensile strength. NDS 12.2.2.5 root tension and independent head transfer remain unresolved or failed reference screens.",
            "Small-diameter Cg and C_delta of one do not qualify splitting, edge/end spacing, receiver support or plywood tear-out.",
            "All comparisons use each saved simultaneous V/T state. No independent demand maxima are combined.",
        ],
    }
    for path, digest in pins.items():
        require(sha(path) == digest, "input changed during arithmetic: " + str(path))
    output.mkdir(parents=True)
    with (output / "same-state-references.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (output / "producer.py.snapshot").write_bytes(producer_bytes)
    report["same_state_csv_sha256"] = sha(output / "same-state-references.csv")
    (output / "comparison.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (output / "receipt.json").write_text(json.dumps({"artifact_sha256": {name: sha(output / name) for name in ("comparison.json", "same-state-references.csv", "producer.py.snapshot")}, "producer_sha256": producer_hash, "producer_version": report["producer_version"], "source_sha256": report["source_sha256"], "physical_release": False}, indent=2) + "\n")
    print(json.dumps({"screw_states": len(records), "generic_lateral_references_n": [s["unadjusted_generic_lateral_reference_n"] for s in lateral.values()], "allocations": [{"packet": a["source_packet"], "modeled_gap_favorable_combined_envelope": a["summaries"][1]["scenario_envelopes"]["plywood_structural1_marine_G050_thread_p3"]["maximum_same_state_combined_index"]} for a in allocations]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, action="append", help="One to three completed 792-state packets; defaults are the frozen allocations 05/06/07.")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="Fresh results/lateral-attemptNN directory; default remains lateral-attempt01. Existing directories are never overwritten.")
    args = parser.parse_args()
    run(args.source or [HERE / "results" / name for name in DEFAULTS], args.output)
