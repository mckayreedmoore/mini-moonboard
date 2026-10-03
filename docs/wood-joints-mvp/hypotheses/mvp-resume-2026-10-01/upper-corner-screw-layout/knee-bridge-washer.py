"""Parent-run one zero-moment washer envelope for proposed knee bridge bolts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
EDGE = HERE / "upper-right-washer-edge.py"
RETAIL = HERE / "retail-washer.py"
PROPOSAL = HERE / "rawlocal/knee-spine-reinforcement/attempt01/checks.json"
PROPOSAL_RECEIPT = PROPOSAL.with_name("receipt.json")
PROPOSAL_CUTS = PROPOSAL.with_name("cuts.jsonl.gz")
PROPOSAL_SNAPSHOT = PROPOSAL.with_name("producer.py.snapshot")
BASELINE = HERE / "rawlocal/retail-washer-suite/attempt01-fine/checks.json"
BASELINE_PINS = BASELINE.with_name("source-pins.json")
OUTPUT_ROOT = HERE / "rawlocal/knee-bridge-washer"

PROPOSAL_SHA256 = "c9360e7ca4ab167a5cbc505373b2bd1342aa6a830f72a26113da9f7c4a8ad778"
PROPOSAL_RECEIPT_SHA256 = "991f6742f6aae386552338b1fea79f02766bd0def09bfa8fabea27560ba13819"
PROPOSAL_CUTS_SHA256 = "9d416c5b77d12781471b4864275d3024c4a5a7bc3fd5c30059c2d554870c674a"
PROPOSAL_SNAPSHOT_SHA256 = "2ecd3e799dc9929b2524b3fd17efd853ea2a0c0e57dcd3da5d7506267d7c0741"
PROPOSAL_IGNORE_SHA256 = "cdbcae15105d6b781e620813c79c7e868740d4e9cc53ce6f5fcbbc12387adf4b"
BASELINE_SHA256 = "3e2dee327dbd81d8584955de3c4918c9acc695b0386fa46abd568ba767c64f74"
BASELINE_PINS_SHA256 = "8eaeee303516584b7d031365cb83446c287735e9fa801120c0ec58dca1e67f79"
EXPECTED_PEAK_T_N = 1060.6566047532085
MARGIN = 1.25
STATE_ID = "knee-bridge-washer/peak-proposed-tension/concentric-M0"
GATES = {
    "formal_acceptance": False,
    "proposal_adopted": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
    "actual_washer_stress_mpa": None,
    "actual_washer_capacity_n": None,
}
FAILURE_TYPES = (ValueError, RuntimeError, OSError, ImportError, KeyError, TypeError,
                 ArithmeticError, np.linalg.LinAlgError)

PINNED_INPUTS = {
    PROPOSAL: PROPOSAL_SHA256,
    PROPOSAL_RECEIPT: PROPOSAL_RECEIPT_SHA256,
    PROPOSAL_CUTS: PROPOSAL_CUTS_SHA256,
    PROPOSAL_SNAPSHOT: PROPOSAL_SNAPSHOT_SHA256,
    PROPOSAL.with_name(".gitignore"): PROPOSAL_IGNORE_SHA256,
    BASELINE: BASELINE_SHA256,
    BASELINE_PINS: BASELINE_PINS_SHA256,
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def imported(path, name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"helper unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_pin(pins, path, digest):
    path = Path(path).resolve()
    require(path not in pins or pins[path] == digest, f"conflicting source pin: {path}")
    pins[path] = digest


def proposal_loads(proposal):
    require(proposal["schema"] == "knee-spine-v-bridge-static-proposal/v1"
            and proposal["status"] == "FINITE_PROPOSAL_STATIC_ARITHMETIC_COMPLETE",
            "frozen knee-spine proposal is incomplete")
    require(proposal["body_case_count"] == 12 and proposal["original_v_cut_count"] == 984,
            "frozen body-case or v-cut census differs")
    require(not proposal["proposal_adopted"] and not proposal["complete_joint_acceptance"]
            and not proposal["physical_release"], "proposal claim boundary differs")

    loads = []
    for state in proposal["states"]:
        candidates = [candidate for candidate in state["candidates"]
                      if candidate["uniform_case_force_margin"] == MARGIN]
        require(len(candidates) == 1, "1.25-margin candidate is not unique for a body case")
        candidate = candidates[0]
        ties = candidate["constant_axial_ties_n"]
        require(len(ties) == 2 and all(math.isfinite(value) and value >= 0 for value in ties),
                "proposed bridge tie-force pair differs")
        for index, tension in enumerate(ties, start=1):
            loads.append({
                "body_case_id": state["case_id"],
                "block": state["block"],
                "bridge_bolt_index": index,
                "axis_id": f"{state['block']}/proposed_v_bridge_{index}",
                "T_n": tension,
                "M_nmm": 0.0,
                "proposal_margin_already_included": MARGIN,
                "case_constant_axial_ties_n": ties,
            })

    require(len(loads) == 24, "proposed bolt-load census differs")
    peak = max(loads, key=lambda record: record["T_n"])
    require(math.isclose(peak["T_n"], EXPECTED_PEAK_T_N, rel_tol=0, abs_tol=1e-9),
            "frozen proposal peak tension differs")
    require((peak["body_case_id"], peak["block"], peak["bridge_bolt_index"])
            == ("k12-right", "knee_outer_right_spine", 2),
            "frozen proposal peak witness location differs")
    witness_state = next(state for state in proposal["states"] if state["case_id"] == peak["body_case_id"]
                         and state["block"] == peak["block"])
    candidate = next(candidate for candidate in witness_state["candidates"]
                     if candidate["uniform_case_force_margin"] == MARGIN)
    witness = candidate["maximum_finite_pressure_witness"]
    require(witness["case_id"] == peak["body_case_id"] and witness["block"] == peak["block"]
            and witness["axis"] == peak["bridge_bolt_index"]
            and math.isclose(witness["case_constant_axial_ties_n"][peak["bridge_bolt_index"] - 1],
                             peak["T_n"], rel_tol=0, abs_tol=1e-9),
            "peak proposal witness does not identify selected bridge tie")
    peak["proposal_peak_witness"] = witness
    end_loads = [
        {**load, "washer_end_v_sign": sign,
         "support_id": f"{load['axis_id']}/v{sign:+d}"}
        for load in loads for sign in (-1, 1)
    ]
    return loads, end_loads, peak


def support_inventory(proposal, module):
    hardware = proposal["hardware_hypothesis"]
    od, washer_id, thickness = hardware["washer_OD_ID_thickness_mm"]
    require([od, washer_id, thickness] == [25.4, 8.3058, 2.5], "frozen washer dimensions differ")
    family = module.FAMILIES["rail"]
    require(family == {"inner_radius_mm": washer_id / 2, "outer_radius_mm": od / 2,
                      "head_radius_mm": 5.0, "thickness_mm": thickness},
            "retail washer annulus differs from proposal")
    analytic_area = math.pi * (family["outer_radius_mm"]**2 - family["inner_radius_mm"]**2)
    rows = []
    for block, geometry in proposal["geometry_proposals"].items():
        lands = geometry["washer_lands"]
        require(len(lands) == 4, f"washer-land count differs for {block}")
        separations = geometry["perpendicular_bore_separations"]
        require(len(separations) == 8 and all(row["cylinder_surface_gap_mm"] > 0 for row in separations),
                f"neighboring proposed bore clearances differ for {block}")
        bores = {bore["axis_id"]: bore for bore in geometry["hypothetical_geometry"]["bores"]}
        for land in lands:
            axis_id = land["axis_id"]
            bore = bores.get(axis_id)
            require(bore is not None and bore["radius_mm"] == 3.75
                    and bore["removed_interval_axis"] == 1, f"7.5 mm proposed bore differs: {axis_id}")
            require(land["end_v_sign"] in (-1, 1)
                    and land["original_bore_gap_from_seat_plane_mm"] > 0
                    and land["other_new_bore_gap_from_outer_disk_mm"] > 0
                    and land["washer_outer_edge_margin_mm"] >= 0,
                    f"washer land lacks frozen bore/edge clearance: {axis_id}")
            require(math.isclose(land["supported_annulus_area_mm2"], analytic_area,
                                 rel_tol=0, abs_tol=1e-9), f"supported annulus area differs: {axis_id}")
            support_id = f"{axis_id}/v{land['end_v_sign']:+d}"
            neighbor_clearances = [row for row in separations if row["new_axis"] == axis_id]
            require(len(neighbor_clearances) == 4,
                    f"neighboring bore census differs for {axis_id}")
            rows.append({"block": block, **land, "support_id": support_id, "washer_OD_mm": od,
                         "washer_ID_mm": washer_id, "washer_thickness_mm": thickness,
                         "proposed_bore_diameter_mm": 2 * bore["radius_mm"],
                         "neighboring_bore_cylinder_clearances": neighbor_clearances,
                         "support_basis": "receipt-bound proposed annular land; not inspected hardware or timber"})
    require(len(rows) == 8 and len({row["support_id"] for row in rows}) == 8,
            "eight proposed washer-end lands are not unique")
    return rows


def prepare(pins):
    for path, digest in PINNED_INPUTS.items():
        add_pin(pins, path, digest)
        require(sha(path) == digest, f"frozen input differs: {path}")

    proposal = json.loads(PROPOSAL.read_text())
    receipt = json.loads(PROPOSAL_RECEIPT.read_text())
    require(receipt["schema"] == "knee-spine-reinforcement-parent-receipt/v1"
            and receipt["output_sha256"]["checks.json"] == PROPOSAL_SHA256
            and receipt["source_sha256"] == proposal["source_sha256"]
            and receipt["sources_authenticated_before_and_after"],
            "proposal receipt does not bind frozen checks and sources")
    for name, digest in receipt["output_sha256"].items():
        path = PROPOSAL.parent / name
        require(sha(path) == digest, f"receipt-bound proposal output differs: {path}")
        add_pin(pins, path, digest)
    for relative, digest in proposal["source_sha256"].items():
        path = Path(relative)
        add_pin(pins, path if path.is_absolute() else ROOT / path, digest)

    baseline = json.loads(BASELINE.read_text())
    baseline_pins = json.loads(BASELINE_PINS.read_text())
    require(baseline["status"] == "FINITE_RETAIL_WASHER_SUITE_HYPOTHESIS"
            and baseline["counts"]["completed_end_states"] == 48
            and baseline["counts"]["completed_coupons"] == 1
            and baseline_pins["output_sha256"]["checks.json"] == BASELINE_SHA256,
            "frozen fine retail-washer baseline is incomplete or unbound")

    edge = imported(EDGE, "knee_bridge_washer_edge")
    retail = imported(RETAIL, "knee_bridge_washer_retail")
    module, _old_source, inherited_pins = retail.load(edge)
    for path, digest in inherited_pins.items():
        add_pin(pins, path, digest)
    add_pin(pins, EDGE, edge.sha(EDGE))
    add_pin(pins, RETAIL, edge.sha(RETAIL))
    add_pin(pins, BASELINE, BASELINE_SHA256)
    add_pin(pins, BASELINE_PINS, BASELINE_PINS_SHA256)
    add_pin(pins, Path(__file__).resolve(), sha(Path(__file__).resolve()))

    model_record = baseline["model"]
    require(edge.RESOLUTIONS["fine"] == model_record["resolution"]
            and module.FAMILIES["rail"] == model_record["family"],
            "fine model geometry or resolution differs from frozen suite")
    for key, value in (("E_mpa_hypothesis", module.ESTEEL), ("nu_hypothesis", module.NU),
                       ("Fy_mpa_hypothesis", module.FY_HYPOTHESIS),
                       ("Kwood_mpa_per_mm_hypothesis", module.KWOOD),
                       ("Khead_mpa_per_mm_hypothesis", module.KHEAD)):
        require(model_record[key] == value, f"fine model parameter differs: {key}")

    lands = support_inventory(proposal, module)
    loads, end_loads, peak = proposal_loads(proposal)
    require({row["support_id"] for row in lands}
            == {row["support_id"] for row in end_loads},
            "washer-end support map differs from proposal loads")
    module.authenticate(pins)
    return {"edge": edge, "module": module, "proposal": proposal, "baseline": baseline,
            "support_lands": lands, "proposal_bolt_loads": loads, "proposal_end_loads": end_loads,
            "peak": peak, "pins": pins}


def source_for_envelope(prepared):
    module, peak = prepared["module"], prepared["peak"]
    family = module.FAMILIES["rail"]
    wood_area = math.pi * (family["outer_radius_mm"]**2 - family["inner_radius_mm"]**2)
    head_area = math.pi * (family["head_radius_mm"]**2 - family["inner_radius_mm"]**2)
    wood_closure = peak["T_n"] / (module.KWOOD * wood_area)
    head_closure = peak["T_n"] / (module.KHEAD * head_area)
    contact = {
        "wood_contact": {"active_area_mm2": wood_area, "closure_mm": wood_closure,
                         "tilt_rad": 0.0, "pressure_peak_mpa": peak["T_n"] / wood_area,
                         "mean_pressure_full_annulus_mpa": peak["T_n"] / wood_area},
        "head_contact": {"active_area_mm2": head_area, "closure_mm": head_closure,
                         "tilt_rad": 0.0, "pressure_peak_mpa": peak["T_n"] / head_area,
                         "mean_pressure_full_annulus_mpa": peak["T_n"] / head_area},
        "total_closure_mm": wood_closure + head_closure,
        "relative_tilt_rad": 0.0,
        "moment_nmm": 0.0,
        "initial_guess_only": True,
        "construction": "analytical concentric, fully backed annuli; area=pi*(ro^2-ri^2) and pi*(rhead^2-ri^2); closure=T/(K*area)",
    }
    return {
        "state_id": STATE_ID,
        "case_id": peak["body_case_id"],
        "side": "right",
        "axis_id": peak["axis_id"],
        "bridge_bolt_index": peak["bridge_bolt_index"],
        "end_role": "both washer ends; one positive-homogeneous envelope",
        "family": "rail",
        "source_proposal_checks_sha256": PROPOSAL_SHA256,
        "source_proposal_margin": MARGIN,
        "source_T_n": peak["T_n"],
        "T_n": peak["T_n"],
        "M_magnitude_nmm": 0.0,
        "source_signed_M_vector_in_pair_basis_nmm": [0.0, 0.0],
        "source_signed_slope_vector_in_pair_basis_rad": [0.0, 0.0],
        "source_moment_on_beam_xyz_nmm": [0.0, 0.0, 0.0],
        "proposal_peak_witness": peak["proposal_peak_witness"],
        "saved_rigid_contact": contact,
    }


def json_write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def source_names(pins):
    rows = {}
    for path, digest in sorted(pins.items(), key=lambda item: str(item[0])):
        try:
            name = path.relative_to(ROOT).as_posix()
        except ValueError:
            name = str(path)
        rows[name] = digest
    return rows


def snapshot_inputs(output, pins):
    folder = output / "input-snapshots"
    folder.mkdir()
    manifest = {}
    direct = {PROPOSAL, PROPOSAL_RECEIPT, PROPOSAL_CUTS, PROPOSAL_SNAPSHOT,
              PROPOSAL.with_name(".gitignore"), BASELINE, BASELINE_PINS}
    own_source = Path(__file__).resolve()
    selected = [path for path in pins if path != own_source and (path.suffix == ".py" or path in direct)]
    for index, path in enumerate(sorted(selected)):
        saved = folder / f"{index:03d}-{path.name}"
        saved.write_bytes(path.read_bytes())
        digest = sha(saved)
        require(digest == pins[path], f"input snapshot differs: {path}")
        manifest[saved.relative_to(output).as_posix()] = {"source": str(path), "sha256": digest}
    json_write(output / "snapshot-manifest.json", manifest)
    return manifest


def run(output):
    output = Path(output).resolve()
    require(output.parent == OUTPUT_ROOT.resolve() and not output.exists(),
            f"output must be a fresh immediate child of {OUTPUT_ROOT}: {output}")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())

    pins = dict(PINNED_INPUTS)
    prepared = model = modes = coupon = state = fields = source = None
    failure, debug = None, {"stage": "source-authentication"}
    try:
        prepared = prepare(pins)
        module, edge = prepared["module"], prepared["edge"]
        source = source_for_envelope(prepared)
        debug = {"stage": "input-snapshots", "source": source}
        snapshot_inputs(output, pins)
        json_write(output / "inputs-before.json", {
            "source_sha256": source_names(pins),
            "proposal_peak": prepared["peak"],
            "proposal_bolt_loads": prepared["proposal_bolt_loads"],
            "proposal_end_loads": prepared["proposal_end_loads"],
            "support_lands": prepared["support_lands"],
        })
        debug = {"stage": "fine-model-setup", "source": source}
        model = edge.make_model(module, "fine")
        require(model["family"]["inner_radius_mm"] >= 3.75,
                "washer foundation includes unsupported timber bore")
        modes = edge.rigid_modes(model, debug)
        coupon = edge.coupon(model, modes, debug)
        debug = {"stage": "governing-concentric-M0-envelope", "source": source}
        edge.STATE_ID = STATE_ID
        state, fields = edge.solve_state(model, source, debug)
        state["elastic_proxy_over_assumed_Fy"] = (
            state["sampled_stress_peak_witness"]["sampled_through_thickness_maximum_proxy_mpa"]
            / module.FY_HYPOTHESIS
        )
        module.authenticate(pins)
    except FAILURE_TYPES as error:
        failure = {"error_type": type(error).__name__, "error": str(error),
                   "last_accepted_state": debug, "physical_incompatibility_proved": False}
        if (state is None and model is not None and prepared is not None
                and debug.get("stage") == "governing-state" and "scaled_variables_mm" in debug):
            try:
                fields, partial = prepared["edge"].recover_fields(
                    model, np.array(debug["scaled_variables_mm"]))
                failure["partial_sampled_fields"] = partial
            except FAILURE_TYPES as recovery_error:
                failure["partial_field_recovery_error"] = str(recovery_error)

    if prepared is not None:
        module = prepared["module"]
        if fields:
            with (output / "fields.csv").open("w", newline="") as stream:
                module.csv_rows(stream, fields)
        if state is not None:
            state.update(GATES)

    model_record = None
    if prepared:
        module, edge = prepared["module"], prepared["edge"]
        family = module.FAMILIES["rail"]
        model_record = {
            "family": family, "resolution": edge.RESOLUTIONS["fine"],
            "E_mpa_hypothesis": module.ESTEEL, "nu_hypothesis": module.NU,
            "Fy_mpa_hypothesis": module.FY_HYPOTHESIS,
            "Kwood_mpa_per_mm_hypothesis": module.KWOOD,
            "Khead_mpa_per_mm_hypothesis": module.KHEAD,
            "inherited_suite_checks_sha256": BASELINE_SHA256,
            "wood_annulus_area_mm2": math.pi * (family["outer_radius_mm"]**2 - family["inner_radius_mm"]**2),
            "head_bearing_annulus_area_mm2": math.pi * (family["head_radius_mm"]**2 - family["inner_radius_mm"]**2),
            "source_saved_rigid_contact_role": "analytical concentric initial guess only",
            "positive_homogeneity_scope": {
                "load": "positive scaling of concentric T with M=0, through the listed peak",
                "fixed_contact_stiffness": {"Kwood_mpa_per_mm": module.KWOOD,
                                            "Khead_mpa_per_mm": module.KHEAD},
                "fixed_conditions": ["geometry", "linear elastic plate", "zero initial gap", "no preload"],
                "actual_capacity_established": False,
            },
        }

    status = "STOP" if failure else "FINITE_KNEE_BRIDGE_WASHER_HYPOTHESIS"
    result = {
        "schema": "knee_bridge_washer_peak_concentric_M0/v1",
        "status": status,
        "counts": {"proposal_body_cases": 12, "receipt_bound_source_v_cuts": 984,
                   "proposed_bridge_bolt_loads": len(prepared["proposal_bolt_loads"]) if prepared else 0,
                   "proposed_washer_end_loads": len(prepared["proposal_end_loads"]) if prepared else 0,
                   "verified_proposed_washer_lands": len(prepared["support_lands"]) if prepared else 0,
                   "completed_coupons": int(coupon is not None),
                   "completed_peak_envelopes": int(state is not None)},
        "source": source,
        "proposal_bolt_loads": prepared["proposal_bolt_loads"] if prepared else None,
        "proposal_end_loads": prepared["proposal_end_loads"] if prepared else None,
        "support_lands": prepared["support_lands"] if prepared else None,
        "state": state,
        "fields_csv": "fields.csv" if fields else None,
        "failure": failure,
        "engineering_coupon": coupon,
        "rigid_mode_diagnostics": modes,
        "model": model_record,
        "runtime": {"python": sys.version.split()[0],
                    "numpy": np.__version__,
                    "scipy": prepared["edge"].scipy.__version__ if prepared else None},
        "source_sha256": source_names(pins),
        "limits": [
            "The single peak T already includes the frozen proposal's 1.25 uniform force margin; no further factor is applied.",
            "One concentric M=0 solve envelopes all 48 proposed washer-end loads only by positive homogeneity of this fixed linear-elastic plate/contact model at fixed Kwood/Khead, geometry, zero gap and no preload.",
            "The analytical concentric full-annulus contact state seeds Newton only; plate equilibrium and recovered fields come from the existing fine polar helper.",
            "The eight lands and neighboring-bore clearances are receipt-bound proposal geometry, not inspected hardware, cut timber or installed contacts.",
            "No end moment, tilt, friction, preload, gap, plasticity, three-dimensional contact-edge stress, actual washer resistance or complete-joint capacity is evaluated.",
            "Proposal remains unadopted; the 47-criterion authority remains pending and physical release false. Modified-grain comparisons are recorded in the separate parent packet, not this washer screen.",
            "Conditional bolt stock-length correction to 6.5 in is separate; preliminary 8 in fit wording supplies no result in this washer envelope.",
        ],
        "cad_run": False, "frame_or_native_run": False,
        "proposal_adopted": False, "complete_joint_acceptance": False,
        "physical_release": False, **GATES,
    }
    json_write(output / "checks.json", result)
    output_hashes = {path.relative_to(output).as_posix(): sha(path)
                     for path in sorted(output.rglob("*")) if path.is_file()}
    pin_record = {"source_sha256": source_names(pins), "output_sha256": output_hashes,
                  "proposal_adopted": False, "complete_joint_acceptance": False,
                  "physical_release": False}
    json_write(output / "source-pins.json", pin_record)
    output_hashes["source-pins.json"] = sha(output / "source-pins.json")
    json_write(output / "receipt.json", {
        "schema": "knee-bridge-washer-parent-receipt/v1",
        "source_sha256": source_names(pins), "output_sha256": output_hashes,
        "stop_details": failure, "proposal_adopted": False,
        "complete_joint_acceptance": False, "physical_release": False,
    })
    print(json.dumps({"status": status, "checks_sha256": sha(output / "checks.json")}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="fresh immediate child of rawlocal/knee-bridge-washer")
    args = parser.parse_args()
    if run(args.output)["status"] == "STOP":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
