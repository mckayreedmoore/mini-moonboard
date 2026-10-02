"""Recover a finite affine bearing field for the saved continuous knee bolts.

The field matches each receiver's signed lateral wrench. It is a static
construction, not a displacement/contact solution or adjusted NDS capacity.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from numpy.polynomial import Polynomial as Poly

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = HERE / "three-member-screen-attempt01/all-two-receiver"
SOURCE_SHA = "306aa4a8e4c6113d4a0258d09564292d07095131ef2b4621370d7284e75e0377"
PSI_MPA = 0.006894757293168
D_MM = 6.35
AREA_MM2 = math.pi * D_MM**2 / 4
THREAD_AREA_MM2 = 0.0318 * 25.4**2
ELASTIC_MODULUS_MM3 = math.pi * D_MM**3 / 32
PLASTIC_MODULUS_MM3 = D_MM**3 / 6
MIN_FE_MPA = 4450 * PSI_MPA
FY_MPA = 92000 * PSI_MPA


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def extrema(polynomials, length):
    """Evaluate vector-norm extrema at endpoints and stationary polynomial roots."""
    squared = sum((p * p for p in polynomials), Poly([0.0]))
    positions = [0.0, length]
    for root in squared.deriv().roots():
        if abs(root.imag) < 1e-7 and 0 < root.real < length:
            positions.append(float(root.real))
    values = [(float(np.linalg.norm([p(x) for p in polynomials])), x) for x in positions]
    value, position = max(values)
    return {"norm": value, "local_position_mm": position,
            "vector_xyz": [float(p(position)) for p in polynomials]}


def field(geometry, plane_forces, endpoint_fe=None):
    """Match interface forces and first moments with one affine field per member."""
    order = geometry["receiver_order"]
    lengths = geometry["bearing_lengths_mm"]
    f0, f2 = np.array(plane_forces[0]), -np.array(plane_forces[1])
    forces = [f0, -f0 - f2, f2]
    first_moments = [lengths[0] * f0, -lengths[1] * f2, np.zeros(3)]
    initial_q, initial_b = np.zeros(3), np.zeros(3)
    records = []
    axis = np.array(geometry["bolt_axis_xyz"])
    for i, (body, length, force, first) in enumerate(zip(order, lengths, forces, first_moments, strict=True)):
        slope = 12 * (first - length * force / 2) / length**3
        constant = force / length - slope * length / 2
        qwood = [Poly([a, b]) for a, b in zip(constant, slope, strict=True)]
        shear = [Poly([a, -b, -c / 2]) for a, b, c in zip(initial_q, constant, slope, strict=True)]
        arm = [Poly([a, b, -c / 2, -d / 6]) for a, b, c, d in zip(initial_b, initial_q, constant, slope, strict=True)]
        q_peak, v_peak, m_peak = (extrema(p, length) for p in (qwood, shear, arm))
        integral = constant * length + slope * length**2 / 2
        first_integral = constant * length**2 / 2 + slope * length**3 / 3
        require(np.linalg.norm(integral - force) < 1e-7, "receiver force mismatch")
        require(np.linalg.norm(first_integral - first) < 1e-5, "receiver first moment mismatch")
        # The circular lower bearing-strength reference avoids adopting an
        # oblique or varying-direction interaction surface in the middle member.
        fe = MIN_FE_MPA if endpoint_fe is None else min(MIN_FE_MPA, endpoint_fe[i])
        records.append({
            "receiver": body, "length_mm": length,
            "force_on_wood_xyz_n": force.tolist(),
            "first_moment_about_receiver_start_xyz_nmm": first.tolist(),
            "bearing_on_wood_constant_xyz_n_per_mm": constant.tolist(),
            "bearing_on_wood_slope_xyz_n_per_mm2": slope.tolist(),
            "bearing_peak": q_peak, "internal_shear_peak": v_peak,
            "internal_bending_peak": {**m_peak,
                "physical_moment_xyz_nmm": np.cross(axis, m_peak["vector_xyz"]).tolist()},
            "maximum_bearing_pressure_mpa": q_peak["norm"] / D_MM,
            "bearing_over_minimum_nominal_fe": q_peak["norm"] / (D_MM * fe),
            "force_residual_n": float(np.linalg.norm(integral - force)),
            "first_moment_residual_nmm": float(np.linalg.norm(first_integral - first)),
            "shear_at_start_xyz_n": initial_q.tolist(),
            "bending_arm_at_start_xyz_nmm": initial_b.tolist(),
        })
        initial_q = np.array([p(length) for p in shear])
        initial_b = np.array([p(length) for p in arm])
        records[-1]["shear_at_end_xyz_n"] = initial_q.tolist()
        records[-1]["bending_arm_at_end_xyz_nmm"] = initial_b.tolist()
    require(np.linalg.norm(initial_q) < 1e-7 and np.linalg.norm(initial_b) < 1e-5,
            "continuous bolt does not have free-end lateral equilibrium")
    return records


def main(output, *, source_dir=SOURCE):
    output = output.resolve()
    require(output.parent == HERE and output.name.startswith("knee-bearing-attempt")
            and not output.exists(), "use a fresh knee-bearing-attempt directory")
    source_dir = Path(source_dir).resolve()
    if source_dir.name == "screen.json":
        source_dir = source_dir.parent
    require(source_dir.is_relative_to(HERE) and source_dir.relative_to(HERE).parts
            and source_dir.relative_to(HERE).parts[0].startswith("three-member-screen-attempt"),
            "source must be inside a three-member-screen-attempt directory")
    source_path = source_dir / "screen.json"
    source_sha = sha(source_path)
    if source_dir == SOURCE.resolve():
        require(source_sha == SOURCE_SHA, "saved three-member force source changed")
    source = json.loads(source_path.read_text())
    require(source["schema"] == "saved_knee_three_member_conditional_screen/v1"
            and source["bolt_case_count"] == 24 and source["symmetric_action_case_count"] == 0
            and source["complete_joint_acceptance"] is False and source["physical_release"] is False,
            "unexpected knee-bolt source")
    axes = {f"knee_outer_{side}_side_{i}" for side in ("left", "right") for i in (1, 2)}
    cases = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
    require(source["case_ids"] == list(cases) and set(source["geometry"]) == axes
            and len(source["bolt_cases"]) == 24
            and {(s["case_id"], s["axis_id"]) for s in source["bolt_cases"]}
            == {(case, axis) for case in cases for axis in axes}
            and source["gap_scale"] == 1.0
            and source["scenario_fyb_psi"] == {"45ksi": 45000.0, "92ksi": 92000.0},
            "incomplete or changed knee force-state/scenario census")
    pins_path = source_dir / "source-pins.json"
    pins = json.loads(pins_path.read_text())
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "changed upstream source: " + path)
    pins[str(source_path.relative_to(ROOT))] = source_sha
    for path in (pins_path, Path(__file__)):
        pins[str(path.relative_to(ROOT))] = sha(path)
    for name, digest in source["output_sha256"].items():
        path = source_dir / name
        require(sha(path) == digest, "saved knee output changed: " + name)
        pins[str(path.relative_to(ROOT))] = digest
    snapshot = "three_member_screen.py.snapshot"
    require(source["output_sha256"].get(snapshot) == source["producer_sha256"],
            "three-member producer snapshot differs")
    states, endpoints = [], []
    for state in source["bolt_cases"]:
        g = source["geometry"][state["axis_id"]]
        require(len(g["receiver_order"]) == 3 and len(state["planes"]) == 2,
                "unexpected receiver/plane count")
        plane_forces = [p["force_on_first_xyz_n"] for p in state["planes"]]
        members = field(g, plane_forces)
        vmax = max(r["internal_shear_peak"]["norm"] for r in members)
        mmax = max(r["internal_bending_peak"]["norm"] for r in members)
        axial = state["outer_tie_signed_n"] / THREAD_AREA_MM2
        shear_stress = 4 * vmax / (3 * AREA_MM2)
        bending_stress = mmax / ELASTIC_MODULUS_MM3
        # Maxima belong to this one bolt/load state. Their spatial envelopes
        # conservatively bound every section; they need not share a position.
        bound = math.sqrt((axial + bending_stress)**2 + 3 * shear_stress**2)
        states.append({
            "case_id": state["case_id"], "axis_id": state["axis_id"],
            "members": members, "outer_tie_signed_n": state["outer_tie_signed_n"],
            "maximum_shear_n": vmax, "maximum_bending_nmm": mmax,
            "nominal_thread_axial_stress_mpa": axial,
            "elastic_bending_stress_mpa": bending_stress,
            "assumed_maximum_round_shank_shear_mpa": shear_stress,
            "spatial_stress_envelope_mpa": bound,
            "spatial_stress_envelope_over_declared_92ksi_fy": bound / FY_MPA,
            "maximum_bearing_over_minimum_nominal_fe": max(r["bearing_over_minimum_nominal_fe"] for r in members),
        })
        for pi, plane in enumerate(state["planes"]):
            for label, fyb_psi in source["scenario_fyb_psi"].items():
                force = np.array(plane["force_on_first_xyz_n"])
                z = plane["single_shear_endpoint_references"][label]["reference_n"]
                force *= z / np.linalg.norm(force)
                only = [np.zeros(3), np.zeros(3)]
                only[pi] = force
                witness = field(g, only)
                maximum = max(r["internal_bending_peak"]["norm"] for r in witness)
                bearing_ratio = max(r["bearing_over_minimum_nominal_fe"] for r in witness)
                moment_ratio = maximum / (fyb_psi * PSI_MPA * PLASTIC_MODULUS_MM3)
                endpoints.append({
                    "case_id": state["case_id"], "axis_id": state["axis_id"],
                    "plane_index": pi, "scenario": label, "endpoint_z_n": z,
                    "members": witness, "nominal_bearing_ratio": bearing_ratio,
                    "nominal_plastic_bending_ratio": moment_ratio,
                    "static_bearing_bending_field_within_nominal_bounds": max(bearing_ratio, moment_ratio) <= 1,
                    "contact_displacement_compatibility_established": False,
                })
    require(len(states) == 24 and len(endpoints) == 96, "incomplete coverage")
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "input changed during calculation: " + path)
    output.mkdir()
    (output / ".gitignore").write_text("*\n")
    (output / "knee_bearing_checks.py.snapshot").write_bytes(Path(__file__).read_bytes())
    result = {
        "schema": "continuous_knee_affine_static_bearing_field/v1",
        "status": "STATIC_FIELD_CONSTRUCTED_CONTACT_AND_DESIGN_GAPS_OPEN",
        "source_directory": str(source_dir.relative_to(ROOT)), "source_screen_sha256": source_sha,
        "candidate": source["candidate"], "geometry_revision_id": source["geometry_revision_id"],
        "case_ids": source["case_ids"], "gap_scale": source["gap_scale"],
        "frame_operator_directory": source.get("frame_operator_directory", str((HERE / "corner-frame-attempt01").relative_to(ROOT))),
        "metadata_seed_directory": source.get("metadata_seed_directory", str((HERE / "corner-frame-attempt01").relative_to(ROOT))),
        "metadata_seed_scope": "Case order and inherited seed provenance only; no old force vectors or acceptance transferred.",
        "clearance_source": source["clearance_source"],
        "source_comparison_sha256": pins[source["clearance_source"] + "/comparison.json"],
        "source_response_sha256": pins[source["clearance_source"] + "/response.npz"],
        "source_force_key": "case_id + '_gap_raw_force_n'",
        "source_sha256": pins, "source_force_state_scope": source["source_force_state_scope"],
        "diameter_mm": D_MM, "nominal_minimum_fe_mpa": MIN_FE_MPA,
        "declared_smooth_shank_yield_mpa": FY_MPA, "states": states, "endpoint_fields": endpoints,
        "peak_steel_state": max(states, key=lambda s: s["spatial_stress_envelope_over_declared_92ksi_fy"]),
        "peak_wood_state": max(states, key=lambda s: s["maximum_bearing_over_minimum_nominal_fe"]),
        "limits": [
            "Affine bearing matches each saved receiver force and first moment; no hidden end moment or head/nut lateral reaction is added.",
            "Signed bearing reversals require opposite bore-wall contacts; no actual displacement, contact pattern or common-bolt clearance is established.",
            "Fe and Fyb describe nominal bearing/bending bounds, not adjusted NDS Z-prime or complete wood resistance.",
            "Endpoint fields are static witnesses only. A complete physical convex admissible set and kinematic embedding are not established.",
            "Steel assumes a smooth 6.35-mm bending section throughout the wood and declared J429 Grade5 92ksi yield. Actual thread/runout/root, head/nut and washer transfer remain open.",
            "Brittle wood splitting, group action, local finished cuts, functional motion, floor verification and Hillman qualification are outside this calculation.",
        ],
        "normative_asymmetric_capacity_n": None, "contact_displacement_compatibility_established": False,
        "complete_joint_acceptance": False,
        "reviewed_geometry_changed": source["reviewed_geometry_changed"],
        "owner_authorized_screw_movements": source.get("owner_authorized_screw_movements", []),
        "bolt_geometry_changed": False, "physical_release": False,
        "native_solve_run": False, "frame_solve_run": False, "CAD_rebuilt": False,
        "tests_run": False, "review_run": False,
        "producer_sha256": sha(Path(__file__)),
        "output_sha256": {"knee_bearing_checks.py.snapshot": sha(output / "knee_bearing_checks.py.snapshot")},
    }
    path = output / "checks.json"
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(path), "sha256": sha(path), "states": len(states),
        "endpoint_fields": len(endpoints), "source_pins": len(pins),
        "peak_steel_ratio": result["peak_steel_state"]["spatial_stress_envelope_over_declared_92ksi_fy"],
        "peak_wood_ratio": result["peak_wood_state"]["maximum_bearing_over_minimum_nominal_fe"],
        "all_endpoint_nominal_bounds_met": all(r["static_bearing_bending_field_within_nominal_bounds"] for r in endpoints)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE,
                        help="Saved three-member directory or its screen.json; defaults to the pinned historical source.")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    main(arguments.output, source_dir=arguments.source)
