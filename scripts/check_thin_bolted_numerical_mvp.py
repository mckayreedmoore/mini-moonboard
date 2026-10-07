"""Independent frozen-geometry and local-method audit, not strength acceptance.

This checker reproduces signed rigid-body kinematics independently and records
the coverage required before a numerical thin-frame strength claim. It performs
no native FE execution, creates no stiffness law and changes no candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.thin_bolted_joint_kinematics import evaluate, hinge_matrix

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
LAYOUT = PACKET / "mixed-offset-rows-shallow-wires-v4.json"
MODEL = PACKET / "integrated-model-v4.json"
LAYOUT_SHA = "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c"
MODEL_SHA = "28bbd2d2fb6f1a93acb441af124c453f04f81e03be551906c633d5acad1d407e"
AUTHORITIES = {
    "current-candidate.json": "f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4",
    "wood-joints-candidate.json": "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    for path, digest in [(LAYOUT, LAYOUT_SHA), (MODEL, MODEL_SHA),
                         *[(ROOT / p, h) for p, h in AUTHORITIES.items()]]:
        if sha(path) != digest:
            raise ValueError(f"frozen source differs: {path.relative_to(ROOT)}")
    layout = json.loads(LAYOUT.read_text())
    model = json.loads(MODEL.read_text())
    contract = json.loads((ROOT / "thin-bolted-candidate.json").read_text())
    expected = {"climber_weight_lb": 250, "downward_multiplier": 2,
                "horizontal_force_N": 300, "hold_lever_mm": 100,
                "floor_no_slip_assumed": True, "floor_no_slip_verified": False}
    if contract["load_basis"] != expected:
        raise ValueError("load or floor boundary differs")
    if contract["candidate"] != layout["candidate"] or model["candidate"] != layout["candidate"]:
        raise ValueError("candidate identities differ")
    if any(contract["release"].values()) or any(layout["release"].values()):
        raise ValueError("an audit cannot authorize a release")
    physical = layout["installed_axes"]
    ids = [a["id"] for a in physical]
    if len(ids) != len(set(ids)) or len(ids) != 70:
        raise ValueError("physical shafts are not seventy unique identities")
    attachments = [a for axis in physical for a in axis["attachments"]]
    if len(attachments) != 72:
        raise ValueError("flange attachment count differs")
    duties = {a["duty_id"] for a in attachments}
    if len(duties) != 24 or len(layout["screw_axes"]) != 66:
        raise ValueError("duty/screw coverage differs")
    if len(layout["raw_fittings"]) != 36 or len(layout["washer_seats"]) != 140:
        raise ValueError("fitting/washer-end coverage differs")
    panel_ids = {"kicker_left", "kicker_right", "main_lower_left", "main_lower_right",
                 "main_upper_left", "main_upper_right"}
    stock_ids = {part["name"] for part in model["finished_stock"]}
    if not panel_ids <= stock_ids or len(stock_ids - panel_ids) != 20 or len(stock_ids) != 26:
        raise ValueError("timber/panel coverage differs")
    new = sum(a["source"] == "new_factory_fitting_axis" for a in physical)
    retained = sum(a["source"] == "original_starting_frame_axis" for a in physical)
    if (new, retained) != (58, 12):
        raise ValueError("new and retained physical axes differ")

    local = evaluate()
    free = {str(n): sum(d["isolated_joint_free_motions"] == n for d in local["duties"])
            for n in sorted({d["isolated_joint_free_motions"] for d in local["duties"]})}
    if free != {"1": 12, "2": 12}:
        raise ValueError("local mechanism census differs")

    # Direct point velocities, rather than the producer's skew-matrix algebra.
    rng = np.random.default_rng(42605)
    velocity_error = work_error = shaft_torque = 0.0
    samples = 100
    for _ in range(samples):
        point = rng.uniform(-500, 500, 3)
        reference = rng.uniform(-500, 500, 3)
        axis = rng.normal(size=3)
        axis /= np.linalg.norm(axis)
        scale = float(10 ** rng.uniform(1, 3))
        q, multiplier = rng.normal(size=12), rng.normal(size=5)
        a = hinge_matrix(["beam", "angle"], [{"first": "beam", "second": "angle",
                         "point_mm": point, "axis": axis}], "ground", reference, scale)
        first = q[:3] + np.cross(q[3:6] / scale, point - reference)
        second = q[6:9] + np.cross(q[9:12] / scale, point - reference)
        velocity_error = max(velocity_error, float(np.linalg.norm((a @ q)[:3] - (first - second))))
        work_error = max(work_error, float(abs((a @ q) @ multiplier - q @ (a.T @ multiplier))))
        # Remove r cross F to recover only the hinge's own rotational couple.
        own_moment = (a.T @ multiplier)[3:6] * scale - np.cross(point - reference, multiplier[:3])
        shaft_torque = max(shaft_torque, float(abs(axis @ own_moment)))
    if velocity_error > 1e-10 or work_error > 1e-10 or shaft_torque > 1e-9:
        raise ValueError("independent point-velocity/work/shaft-torque audit failed")

    gates = [
        ("applied_loads", "Freeze the six original signed hold cases at current datums; reconstruct F and M=(p_hold-reference) cross F, including the 100 mm outward-normal lever exactly once."),
        ("gravity", "Include all current timber, panels, fittings, bolt stacks and remaining hardware once; preserve per-body mass and first moments. Name the retained 25 kg placement and any alternative scenario separately; the 2x factor applies only to climber force."),
        ("assembled_load_path", "Account for all 24 angle duties, 70 physical bolt shafts, 66 panel/kicker screws, member contacts and compression-only no-slip floor support; recover force and moment equilibrium for every body."),
        ("compatible_or_bounded_demands", "Obtain a compatible physical response with validated properties, or justified conservative bounds. A min-max LP feasible allocation is only a static witness; it is not an actual demand or upper bound."),
        ("contact_and_kinematics", "Establish the assembled mechanisms and loaded contact branches under the actual model's constraints. Three translation pin rows and five revolute rows are distinct. Do not credit unspecified clamp friction or shaft torque."),
        ("shared_shafts", "Retain per-attachment signed actions and ordered occupied stations on each shared shaft. Check internal shear/bending on relevant spans; total vector sums can conceal opposite internal actions."),
        ("frame_members", "Check all twenty original-size finished members, including oblique ends, bolt/service holes, rear recesses and 8 mm shallow channels, using actual weakest sections and same-state combined actions."),
        ("timber_connections", "Check both sides of every shaft with applicable signed loaded-end/edge/spacing, bearing/yield, group/net-section and splitting rules. Midshaft grain rays and full CAD bore support alone are not NDS classifications."),
        ("steel_angles", "Use exact SKU-specific geometry and material assumptions, actual eccentricities and same-state flange/heel actions; check plate bending, shear, net section, bearing and tear-out. Eaton strut assembly ratings are not wood-joint resistance."),
        ("bolt_strength_and_stack", "Check combined shaft axial/shear/bending and threads where present for all 58 new and 12 retained shafts. Keep nominal length, minimum nut engagement and delivered unthreaded shank distinct."),
        ("washers", "Check all 140 ends including 14 SAE replacements: use minimum published thickness for resistance, maximum dimensions for occupied fit, actual metal/wood seats and hole bridging. OD support is not capacity."),
        ("panels_and_screws", "Use all six current perforated panels and all 66 Hillman axes. Check compatible or bounded normal/lateral transfer, bending/shear/net/hold load introduction, screw withdrawal/lateral/head pull-through and complete backing routes."),
        ("lower_edges_and_kickers", "Recheck the two bottom rails shifted 50.8 mm, four moved bottom screws, panel seam/free-edge response and kerf-right kicker support with actual current receivers."),
        ("materials_and_adjustments", "Keep matching NDS/APA edition, DF-L No. 2, actual grain/ply orientation, Group 1 A-C, moisture/duration/temperature factors and product scenarios explicit. Unmeasured Hillman/hardware properties remain conditional inputs."),
        ("method_validation", "Require known-answer mechanics/units/sign checks, residuals, appropriate discretization and contact/parameter sensitivity. Arbitrary spring-ratio sweeps do not establish physical bounds."),
        ("numerical_disposition", "For each duty/member/fastener, retain same-state signed witnesses and an applicable pass/failure or exact unavailable input/method. Keep conditional reference exceedances separate from adopted failures and numerical sensitivity."),
        ("access_transport", "Verify installation, counterhold, tightening, bolt stroke and reverse disassembly for the integrated layout and front-open channels; retain individual-member transport and full tool paths."),
        ("installed_takeoff", "Reconcile complete installed timber, machining, 36 fittings, 70 bolts/nuts, 140 washers, 66 purchased Hillman screws, panels, services and freight; give scenario mass/cost limits rather than an observed or configured quote."),
    ]
    pins = {str(p.relative_to(ROOT)): sha(p) for p in [LAYOUT, MODEL, Path(__file__),
            ROOT / "scripts/thin_bolted_joint_kinematics.py",
            ROOT / "mini_moonboard/bolted_joint_mechanics.py", ROOT / "uv.lock",
            ROOT / "thin-bolted-candidate.json", *[ROOT / p for p in AUTHORITIES]]}
    return {
        "schema": "thin_bolted_independent_method_audit/v1", "candidate": layout["candidate"],
        "revision": layout["revision"], "question": "Are the frozen source identities and local hinge arithmetic sound, and what coverage is required for numerical MVP acceptance?",
        "command": ".venv/bin/python -m scripts.check_thin_bolted_numerical_mvp",
        "source_sha256": pins, "numpy_version": np.__version__,
        "frozen_inventory_verified": {"duties": 24, "fittings": 36, "flange_attachments": 72,
            "physical_shafts": 70, "new_shafts": 58, "retained_shafts": 12, "hillman_axes": 66},
        "independent_local_method_verification": {"samples": samples, "seed": 42605,
            "max_direct_point_velocity_error": velocity_error, "max_virtual_work_error": work_error,
            "max_intrinsic_shaft_torque_n_mm": shaft_torque,
            "isolated_free_motion_census": free, "result": "VERIFIED_LOCAL_ARITHMETIC_ONLY",
            "rotation_scale_range_mm": [10, 1000], "contact_and_floor_included": False,
            "inference": "All 24 isolated duties retain local motions; this does not establish assembled frame instability."},
        "coverage_gates": [{"id": name, "required_evidence": requirement,
                            "completion_assessed_here": False} for name, requirement in gates],
        "numeric_strength_acceptance_established": False, "native_execution": False,
        "release": contract["release"],
        "limits": ["This is a frozen-input and local-method audit; no demand allocation or resistance is computed.",
                   "Conditional desktop review completion, numerical method validity and structural acceptance are separate claims.",
                   "A failed applicable criterion or absent load path remains open; arbitrary stiffness and plausible equilibrium cannot close it.",
                   "Actual cuts, wood, holes, hardware, floor, wires and assembly have not been inspected."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET / "independent-method-audit-v4.json")
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve the prior immutable audit")
    report = audit()
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"inventory": report["frozen_inventory_verified"],
                      "method": report["independent_local_method_verification"],
                      "coverage_gates": len(report["coverage_gates"])}))


if __name__ == "__main__":
    main()
