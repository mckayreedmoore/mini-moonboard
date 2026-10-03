"""Prepare gap P's exact masks and a conditional static compression certificate.

This source reads completed evidence and performs only finite algebra after the
parent freezes its invocation. It does not import CAD, open response arrays,
solve contact, generate meshes, run coupons, or launch a native solver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = HERE.parent
HYPOTHESES = PACKET.parent
RAW = HERE / "rawlocal/central-seat-transfer"
AXIS, BODY = "center_principal_right_2", "base_principal_center_right"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
STEP = HYPOTHESES / "evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_principal_center_right.step"
RING = HERE / "bolted-replay-results/central-seat-attempt01/result.json"
GEOMETRY = PACKET / "member-screen-attempt02/four-screw-layout01/geometry.json"
PROFILE = HYPOTHESES / "mvp-integration-2026-10-01/conditional-nut-profile.json"
PASSAGES = ROOT / "docs/floor-flush-construction-kerf-right/timber-passages.json"
ROWS = HERE / "operators-attempt02/row-identities.json"
COMPARISON = HERE / "frame-250-attempt02/comparison.json"
RESPONSE = HERE / "frame-250-attempt02/response.npz"
PINS = {
    RING: "a058f494bc4a733e90c0ee954f38634abadceac4c24273b92dab4434cac42b33",
    PACKET / "partial-seat-footprint-attempt02/result.json": "ffba33b640e3ae00e61049664a603cdb6fe27cf7561f0068a735878ed8e3bf1b",
    STEP: "9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58",
    GEOMETRY: "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    PROFILE: "d30a5e94e7adbd4b617ea85af8790955738025dbae26af544efc96b29fecab34",
    PASSAGES: "5c86941458a6a92432941fdf7e13b2b21ef2f933332e0e1ec602d4d57796f15f",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    COMPARISON: "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    RESPONSE: "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    PACKET / "assembly-package/rawlocal/hardware-engagement/hardware-engagement.json": "93c24fe5fb421152b0294cc35106bfb6d595b558f45e0be826406405084c111a",
    HERE / "washer-product-basis.md": "af76a17eea64c63ad740694ebfde66cbf6d634dc70ad8bfb8b92648b0c0a4b53",
    HYPOTHESES / "remaining-candidate-washer-seats-2026-10-01/cut-diagnosis-review.md": "5f7e0d60678a0a7c14ba6d6929d165b67773e05422ab046e7586af86d0aa57c4",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


def authenticate(pins: dict[Path, str]) -> None:
    for path, expected in pins.items():
        require(sha(path) == expected, f"Frozen source changed: {path}")


def cross(a, b) -> list[float]:
    return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]]


def prepare(output: Path, washer_yield_mpa: float | None) -> None:
    output = output.resolve()
    require(RAW.resolve() == RAW, "Owned raw directory must not be a symlink")
    require(output.is_relative_to(RAW) and output != RAW and not output.exists(),
            "Use a fresh child of rawlocal/central-seat-transfer")
    require(washer_yield_mpa is None or (math.isfinite(washer_yield_mpa) and washer_yield_mpa > 0),
            "A declared washer yield must be finite and positive")
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__).resolve())}
    authenticate(pins)
    ring, geometry, profile, comparison = read(RING), read(GEOMETRY), read(PROFILE), read(COMPARISON)
    require(ring["axis_id"] == AXIS and ring["body"] == BODY, "Central seat identity changed")
    require(ring["declared_outer_inner_diameters_mm"] == [10.0, 8.3058], "Current ring changed")
    require([s["case_id"] for s in ring["states"]] == CASES, "Current six cases changed")
    require([p["depth_mm"] for p in ring["geometry_probes"]] == [0.01, 0.05, 0.1]
            and all(abs(p["supported_fraction"] - 1) < 1e-6 for p in ring["geometry_probes"]),
            "Saved central support changed")
    require(ring["source_sha256"][str(COMPARISON.relative_to(ROOT))] == PINS[COMPARISON]
            and ring["source_sha256"][str(RESPONSE.relative_to(ROOT))] == PINS[RESPONSE]
            and comparison["response_sha256"] == PINS[RESPONSE], "Force source binding changed")
    nominal = [s for s in comparison["states"] if s["gap_scale"] == 1.0]
    require([s["case_id"] for s in nominal] == CASES
            and all(s["status"] == "PASS_CONDITIONAL_LAWS_WITH_BOUNDED_SEATING" for s in nominal),
            "Nominal bounded force scope changed")
    member = geometry["members"][BODY]
    require(member["current_finished_step_sha256"] == PINS[STEP], "Finished member changed")
    row = read(ROWS)[1535]
    require(row["row"] == 1535 and row["row_id"] == AXIS + "/outer-seat-axial-tie"
            and row["ownership"]["second_body"] == BODY, "Signed tie ownership changed")
    passage = next(p for p in read(PASSAGES) if p["name"] == "bore_base_principal_center_right_072")
    require(passage["member"] == BODY and passage["direction"] == [1.0, 0.0, 0.0]
            and passage["diameter_mm"] == 38.1, "F1/G1 passage changed")

    seat = ring["seat_point_mm"]
    require(all(abs(a-b) < 1e-9 for a, b in zip(seat, [50.95, -90.30983137880766, 367.0102220661388])),
            "Seat datum changed")
    center = [passage["start_mm"][i] - seat[i] for i in (1, 2)]
    distance = math.hypot(*center)
    inner, outer, passage_radius = 8.3058/2, 5.0, passage["diameter_mm"]/2
    require(distance - passage_radius > outer, "Supported ring intersects passage")
    area = math.pi*(outer**2 - inner**2)
    second_moment = math.pi*(outer**4 - inner**4)/4
    require(math.isclose(area, ring["central_area_mm2"], abs_tol=1e-10), "Ring area changed")
    natural = [p for p in member["profile_planes"] if p["id"].endswith(("facet014", "facet018"))]
    edge_distances = [p["offset"] - sum(a*b for a, b in zip(p["normal"], seat)) for p in natural]
    require(len(natural) == 2 and min(edge_distances) > 19.0246/2, "Natural washer boundary changed")
    station = sum((a-b)*d for a, b, d in zip(seat, member["geometry"]["start"], member["geometry"]["axis"]))
    nearby = [p for p in member["bore_or_passage_intervals"]
              if p["lo"] <= station + 19.0246/2 and p["hi"] >= station - 19.0246/2]
    require({p["id"] for p in nearby} == {BODY + "/facet007", BODY + "/facet013"},
            "Additional opening intersects the source washer span")
    require(profile["initial_contact_land"]["H2_annulus_inner_outer_radii"] == [3.556, 5.00635]
            and not profile["actual_product_profile_established"], "Conditional nut profile changed")
    nut_inner, nut_outer = profile["initial_contact_land"]["H2_annulus_inner_outer_radii"]
    require(nut_inner <= inner and nut_outer >= outer, "Declared nut land does not contain the ring")

    states = []
    lever = [a-b for a, b in zip(row["ownership"]["point_mm"], seat)]
    for source in ring["states"]:
        force = [-source["signed_tie_n"]*d for d in row["ownership"]["direction_global_xyz"]]
        moment = cross(lever, force)
        require(max(abs(force[1]), abs(force[2]), abs(moment[0])) <= 1e-9,
                "Normal compression certificate cannot carry transverse force or axial torque")
        # The exact authored axis is X. Preserve numerical wrench components and
        # report the transverse roundoff discarded by this axial idealization.
        q0, qy, qz = force[0]/area, -moment[2]/second_moment, moment[1]/second_moment
        excursion = outer*math.hypot(qy, qz)
        qmin, qmax = q0 - excursion, q0 + excursion
        require(qmin >= 0, "This affine compression ansatz is insufficient; not a joint failure")
        require(math.isclose(q0, source["declared_central_mean_pressure_mpa"], abs_tol=1e-12),
                "Saved ring pressure changed")
        states.append({
            "case_id": source["case_id"], "signed_tie_n": source["signed_tie_n"],
            "source_tie_wrench_at_seat_Fxyz_N_Mxyz_Nmm": force + moment,
            "discarded_transverse_roundoff_Fy_Fz_N_Mx_Nmm": [force[1], force[2], moment[0]],
            "trial_pressure_q0_MPa_qy_qz_MPa_per_mm": [q0, qy, qz],
            "trial_pressure_min_max_mpa": [qmin, qmax],
            "mean_over_conditional_Fc_perp": source["central_mean_pressure_over_base_Fc_perp"],
            "required_hypothetical_washer_yield_mpa": qmax,
            "declared_yield_covers_trial_field": None if washer_yield_mpa is None else qmax <= washer_yield_mpa,
        })

    contract = {
        "schema": "central_seat_static_transfer_preparation/v1", "gap_id": "P", "axis_id": AXIS,
        "body": BODY, "status": "CONDITIONAL_STATIC_ROUTE_COUPON_PENDING",
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "seat_point_global_xyz_mm": seat, "inward_global_xyz": [1, 0, 0],
        "chart": "y=global_Y-seat_Y; z=global_Z-seat_Z; x=global_X-seat_X",
        "wood_support_mask": {
            "local_passage_center_yz_mm": center, "passage_radius_mm": passage_radius,
            "own_bore_radius_mm": 3.65, "nearest_passage_edge_radius_mm": distance - passage_radius,
            "within_centered_maximum_washer": "(y-cy)^2+(z-cz)^2 >= 19.05^2 and y^2+z^2 >= 3.65^2",
            "natural_edge_planes": natural, "natural_edge_distances_mm": edge_distances,
            "seat_grain_station_mm": station, "intersecting_opening_intervals": nearby,
            "scope": "Fixed source plane and concentric catalog washer; saved BREP/cut diagnosis, no new CAD query.",
        },
        "conditional_washer_metal_mask": {
            "inner_outer_diameters_mm": [8.3058, 18.4658], "thickness_mm": 1.2954,
            "centering_offset_yz_mm": [0, 0],
            "mask": "(8.3058/2)^2 <= y^2+z^2 <= (18.4658/2)^2; -1.2954 <= x <= 0",
            "flat_faces_and_full_thickness_columns": "Explicit delivered-profile hypothesis, not established product geometry.",
        },
        "conditional_initial_nut_face_mask": {
            "source": str(PROFILE.relative_to(ROOT)), "H1_radii_mm": [3.556, 5.5626],
            "H2_radii_mm": [3.556, 5.00635], "centering_offset_yz_mm": [0, 0],
            "flat_mask": "3.556^2 <= y^2+z^2 <= R_land^2; no contact over the washer opening",
            "relief_surfaces": profile["bearing_side_outer_relief"],
            "limit": "Initial hypothetical lands only; any later relief contact is outside this certificate.",
        },
        "credited_transfer_patch": {
            "mask": "(8.3058/2)^2 <= y^2+z^2 <= 5^2",
            "area_mm2": area, "second_moment_yy_zz_mm4": second_moment,
            "supported_probe_depths_mm": [0.01, 0.05, 0.1],
            "outside_patch_pressure_and_trial_stress": 0,
            "unsupported_crescent_credited": False, "full_washer_annulus_credited": False,
        },
        "static_bound": {
            "stress": "sigma_xx=-q(y,z) through the washer thickness; every other component zero; zero outside patch",
            "q": "N/A - Mz*y/I + My*z/I", "von_mises_mpa": "abs(q)",
            "hypothetical_washer_yield_mpa": washer_yield_mpa,
            "wood_comparison_only_Fc_perp_mpa": ring["conditional_base_Fc_perpendicular_mpa"],
            "assumptions": [
                "Concentric, parallel, seated flat faces cover the patch at both interfaces; no preload or prescribed pressure outside it.",
                "Full-thickness washer metal exists on every credited column; catalog limits describe the declared dimensional hypothesis.",
                "The nut is a rigid load spreader with a centered axial resultant, not a modeled thread or a nut material resistance.",
                "Washer is ductile elastic-perfectly plastic/rigid-plastic von Mises material with the separately declared yield floor.",
                "Fixed geometry and small deformation plastic limit analysis; geometry instability is outside this local certificate.",
                "The wood face can supply the declared nonnegative pressure field; its mean Fc-perp comparison remains conditional.",
            ],
            "proof_scope": "Static plastic collapse bound for washer transfer with admissible boundary tractions; not actual elastic stress, first yield, seating motion, wood ligament resistance, or cyclic shakedown.",
            "method_source": "https://solidmechanics.org/Text/Chapter6_3/Chapter6_3.php (sections 6.3.5 and 6.3.6)",
        },
        "states": states,
        "missing_exact_product_inputs": [
            "Nut flat-land inner/outer radii and flatness at the actual bearing plane; nut-axis offset and tilt relative to washer/wood.",
            "Washer bore/profile through its thickness, flat face coverage, installed centering, and a product-bound ductile yield minimum.",
            "Any preload and additional local nut end wrench or imposed rocking not represented by the centered frame tie.",
            "Applicability of the static plastic transfer interpretation and wood reaction field to the parent's existing joint criterion.",
        ],
        "minimal_next_method_if_ansatz_inapplicable": "Retain these masks and simultaneous complete local nut wrenches; prepare only a bounded static contact/transfer certificate for the missing component. No 3D/native method is presumed necessary.",
        "geometry_changed": False, "hardware_changed": False, "engineering_coupon_executed": False,
        "algebraic_trial_evaluated": True, "mechanics_solver_executed": False,
        "native_readiness": False, "actual_profile_established": False,
        "complete_joint_acceptance": False, "physical_release": False,
    }
    coupon = {
        "schema": "central_seat_static_known_answer_readiness/v1", "status": "SPECIFICATION_ONLY_NOT_EXECUTED",
        "question": "Do signed affine pressures reproduce all normal force/moment components without empty-hole or crescent credit?",
        "annulus_inner_outer_radii_mm": [1, 2], "prescribed_q_MPa": "3 + 0.5*y - 0.25*z",
        "known_answer": {"area_mm2": "3*pi", "Iyy_Izz_mm4": "15*pi/4",
                         "Fxyz_N_Mxyz_Nmm": ["9*pi", 0, 0, 0, "-15*pi/16", "-15*pi/8"],
                         "q_min_max_mpa": ["3-sqrt(1.25)", "3+sqrt(1.25)"]},
        "negative_cases": ["A passage circle intersecting the credited ring must refuse this ring certificate.",
                           "A nut land not containing the credited ring must refuse this ring certificate.",
                           "An affine pressure becoming tensile must report insufficient ansatz, not a physical joint failure."],
        "parent_completion": "Freeze a bounded algebraic coupon evaluation and inspect signed integrals before using the certificate; no native coupon required.",
    }
    authenticate(pins)
    files = {"contract.json": contract, "coupon-readiness.json": coupon}
    encoded = {name: (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
               for name, value in files.items()}
    output.mkdir(parents=True)
    for name, content in encoded.items():
        (output / name).write_bytes(content)
    receipt = {"source_sha256": contract["source_sha256"],
               "output_sha256": {name: hashlib.sha256(content).hexdigest() for name, content in encoded.items()},
               "parent_freeze_created": False, "native_execution_authorized": False}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"Prepared conditional ring certificate and coupon specifications: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--washer-yield-mpa", type=float,
                        help="Explicit hypothetical ductile washer yield; never an exact-product strength claim")
    args = parser.parse_args()
    prepare(args.output, args.washer_yield_mpa)
