"""Continuous affine-bearing trial on the eight current mixed bolt stacks.

This is a statics/material-reference calculation, not an adjusted NDS capacity.
It joins each member's signed force and couple, includes the bolt's own metal
gravity, and searches the continuous bending field across the body/root window.
It does not solve bearing compatibility or change the admitted frame response.
"""

from __future__ import annotations

import argparse
import json
import math
from itertools import pairwise
from pathlib import Path

import numpy as np
from numpy.polynomial import polynomial as poly

from scripts import eoere_current_response as current
from scripts.summarize_eoere_current_response import SEQUENCE, canonical_sha

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
PACKET = current.ROOT / (
    "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/"
    "eoere-successor-v1/selected-hardware-v1/current-response-v1")
MIXED_IDS = [f"eoere_bolt_{n:03d}" for n in [65, 66, 67, 70, 71, 74, 79, 80]]
PSI_MPA = 0.006894757293168361
MATERIAL_SCENARIO = {
    "body_and_purchase_root": "own selected catalog minimum body; own declared purchase root floor; neither is delivered observation",
    "bolt_Fyb_psi": 92000.0,
    "steel_Fu_mpa": 370.0,
    "wood_G": 0.5,
}


def vector(value):
    out = np.asarray(value, dtype=float)
    current.require(out.shape == (3,) and np.isfinite(out).all(), "finite spatial vector required")
    return out


def peak_norm(coefficients):
    """All extrema of a vector polynomial on the closed unit interval."""
    c = np.asarray(coefficients, dtype=float)
    current.require(c.ndim == 2 and c.shape[1] == 3 and np.isfinite(c).all(), "finite vector polynomial required")
    squared = np.zeros(1)
    for i in range(3):
        squared = poly.polyadd(squared, poly.polymul(c[:, i], c[:, i]))
    derivative = poly.polyder(squared)
    roots = poly.polyroots(poly.polytrim(derivative)) if np.any(derivative) else []
    stations = [0., 1., *[float(z.real) for z in roots if abs(z.imag) < 1e-8 and 0 < z.real < 1]]
    values = [(float(np.linalg.norm(poly.polyval(t, c))), t) for t in stations]
    maximum, t = max(values)
    return {"fraction": t, "magnitude": maximum, "vector": poly.polyval(t, c).tolist(),
            "stationary_points_checked": len(stations)-2}


def affine_surface(trial, axis):
    """Authenticate endpoint densities against the complete own lateral wrench."""
    axis = vector(axis)
    low, high = trial["interval_from_axis_point_mm"]
    length = high-low
    current.require(math.isfinite(length) and length > 0, "positive bearing interval required")
    q0, q1 = map(vector, trial["affine_endpoint_line_density_vectors_n_mm"])
    force, moment = vector(trial["lateral_force_on_host_xyz_n"]), vector(trial["moment_on_host_about_interval_center_xyz_nmm"])
    current.require(max(abs(axis @ q0), abs(axis @ q1), abs(axis @ moment)) < 1e-6,
                    "lateral trial only; axial and torsional actions remain separate")
    force_error = float(np.linalg.norm((q0+q1)*length/2-force))
    moment_error = float(np.linalg.norm(np.cross(axis, (q1-q0)*length**2/12)-moment))
    current.require(force_error < 1e-7 and moment_error < 1e-5, "affine trial differs from its own signed wrench")
    return {"low": low, "high": high, "q0": -q0, "slope": -(q1-q0)/length,
            "host": trial["host"], "kind": trial["kind"], "surface_index": trial["surface_index"],
            "force_replay_error_n": force_error, "moment_replay_error_nmm": moment_error}


def bending_field(axis, domain, surfaces, point_loads, transitions):
    """Exact piecewise-cubic moment; all vector-norm stationary points searched.

    q is force on the bolt. V(s)=integral q and M(s)=integral (s-u)*axis×q(u).
    Point couples use the same convolution sign, so M jumps by -external couple.
    Events split bearing endpoints, point loads, and diameter transitions.
    """
    axis = vector(axis)
    current.require(abs(np.linalg.norm(axis)-1) < 1e-10, "unit bolt direction required")
    low, high = map(float, domain)
    current.require(math.isfinite(low) and math.isfinite(high) and high > low, "positive finite shaft domain required")
    current.require(all(low <= t <= high for t in transitions), "transition outside shaft domain")
    current.require(all(low <= s["low"] < s["high"] <= high for s in surfaces), "bearing interval outside shaft")
    points = [{"s": float(p["s"]), "force": vector(p["force"]), "couple": vector(p.get("couple", [0., 0., 0.]))}
              for p in point_loads]
    current.require(all(math.isfinite(p["s"]) for p in points), "finite point station required")
    events = sorted({low, high, *transitions,
                     *[v for s in surfaces for v in (s["low"], s["high"])],
                     *[p["s"] for p in points if low < p["s"] < high]})
    shear = sum((p["force"] for p in points if p["s"] < low), start=np.zeros(3))
    moment = sum((np.cross(axis, p["force"])*(low-p["s"])-p["couple"]
                  for p in points if p["s"] < low), start=np.zeros(3))
    segments = []
    for a, b in pairwise(events):
        for p in points:
            if p["s"] == a:
                shear += p["force"]
                moment -= p["couple"]
        active = [s for s in surfaces if s["low"] <= a and b <= s["high"]]
        q0 = sum((s["q0"]+s["slope"]*(a-s["low"]) for s in active), start=np.zeros(3))
        slope = sum((s["slope"] for s in active), start=np.zeros(3))
        length = b-a
        coefficients = np.array([moment, np.cross(axis, shear)*length,
                                 np.cross(axis, q0)*length**2/2,
                                 np.cross(axis, slope)*length**3/6])
        maximum = peak_norm(coefficients)
        segments.append({"interval_mm": [a, b], "moment_coefficients_unit_interval_nmm": coefficients.tolist(),
                         "maximum_bending": {"station_mm": a+maximum["fraction"]*length, **maximum}})
        moment = poly.polyval(1., coefficients)
        shear += q0*length+slope*length**2/2
    for p in points:
        if p["s"] == high:
            shear += p["force"]
            moment -= p["couple"]
    return segments, shear, moment


def check_stack(shaft, component, trials, loads):
    """Current own-wrench affine trial against declared raw material scenarios."""
    axis, origin = vector(shaft["basis"][0]), vector(shaft["point"])
    current.require(len(trials) == len(shaft["surfaces"]) == 3, "three actual mixed-stack members required")
    surfaces = []
    for i, (surface, trial) in enumerate(zip(shaft["surfaces"], trials, strict=True)):
        current.require(trial["axis_id"] == shaft["axis_id"] and trial["surface_index"] == i
                        and trial["host"] == surface["host"] and trial["kind"] == surface["kind"]
                        and trial["interval_from_axis_point_mm"] == surface["interval_mm"], "own ordered surface join required")
        surfaces.append(affine_surface(trial, axis))
    window = component["thread_window"]
    body_d = window["catalog_min_body_in"]*25.4
    root_d = window["purchase_design_root_floor_in"]*25.4
    current.require(0 < root_d <= body_d and window["catalog_Lb_min_mm"] > 0, "positive conditional body/root dimensions required")
    head = next(e for e in shaft["ends"] if e["end"] == "head")["pressure_face_s_mm"]
    transition = head+window["catalog_Lb_min_mm"]
    domain = shaft["shaft_interval_mm"]
    points = []
    for load in loads:
        offset, full_force = vector(load["point_xyz_mm"])-origin, vector(load["force_xyz_n"])
        station = float(offset @ axis)
        force = full_force-axis*float(full_force @ axis)
        couple = np.cross(offset-axis*station, full_force)+vector(load.get("moment_xyz_nmm", [0., 0., 0.]))
        couple -= axis*float(couple @ axis)
        points.append({"s": station, "force": force, "couple": couple})
    segments, end_force, end_moment = bending_field(axis, domain, surfaces, points,
                                                   [transition] if domain[0] < transition < domain[1] else [])
    force_error, moment_error = float(np.linalg.norm(end_force)), float(np.linalg.norm(end_moment))
    current.require(force_error < 1e-5 and moment_error < 1e-3, "complete own lateral wrench does not equilibrate")
    # Reuse the pure source-backed Fe expression, not its historical candidate API.
    from mini_moonboard.nds_2024_multi_member_bolt_yield import _fe_theta_psi

    bearing = []
    for surface, trial in zip(surfaces, trials, strict=True):
        d = body_d if surface["high"] <= transition else root_d
        if surface["kind"] == "wood":
            # Minimum radial Fe for G=.50 solid-sawn wood: conservative for every
            # transverse direction of this affine field, including reversals.
            fe = _fe_theta_psi(specific_gravity=.50, diameter_in=d/25.4, angle_degrees=90.)*PSI_MPA
            basis = "NDS2024 Table12.3.3 perpendicular Fe, G0.50, minimum diameter over this interval"
        else:
            fe = 1.5*370.
            basis = "TR12 Appendix A effective Fe=1.5Fu; conditional Q235B Fu370MPa; not product bearing qualification"
        peak = max(float(np.linalg.norm(vector(q))) for q in trial["affine_endpoint_line_density_vectors_n_mm"])
        current.require(abs(peak-trial["affine_trial_peak_line_density_n_mm"]) < 1e-8, "retained peak differs from own densities")
        bearing.append({"surface_index": surface["surface_index"], "host": surface["host"], "kind": surface["kind"],
                        "minimum_reference_diameter_mm": d, "bearing_reference_mpa": fe, "basis": basis,
                        "peak_affine_line_density_n_mm": peak, "raw_bearing_reference_n_mm": fe*d,
                        "raw_trial_utilization": peak/(fe*d)})
    for segment in segments:
        d = body_d if segment["interval_mm"][1] <= transition else root_d
        cap = 92000.*PSI_MPA*d**3/6.
        segment.update({"reference_diameter_mm": d, "raw_plastic_moment_reference_nmm": cap,
                        "raw_trial_utilization": segment["maximum_bending"]["magnitude"]/cap})
    worst_bending = max(segments, key=lambda s: s["raw_trial_utilization"])
    worst_bearing = max(bearing, key=lambda s: s["raw_trial_utilization"])
    index = max(worst_bearing["raw_trial_utilization"], worst_bending["raw_trial_utilization"])
    return {"axis_id": shaft["axis_id"], "catalog_body_to_purchase_root_transition_s_mm": transition,
            "raw_bearing_trials": bearing, "continuous_bending_segments": segments,
            "worst_raw_bearing_trial": worst_bearing, "worst_raw_bending_trial": worst_bending,
            "maximum_raw_material_trial_index": index,
            "affine_trial_within_declared_raw_material_references": index <= 1.,
            "lateral_force_closure_error_n": force_error, "lateral_moment_closure_error_nmm": moment_error,
            "compatible_bearing_or_adjusted_ASD_capacity": None, "complete_joint_resistance": None}


def run():
    input_ref = current.ref(PACKET / "joint-closure-v1/inputs-v2.json")
    inputs = current.read(input_ref)
    current.require(current.sha(OWN) == LOADED_SHA == inputs["producer"]["sha256"], "loaded producer differs")
    current.require(inputs.get("material_scenarios") == MATERIAL_SCENARIO, "fixed raw material scenario differs")
    forces = current.read(inputs["current_response"])
    components = current.read(inputs["current_components"])
    maps = []
    for report in [forces, components]:
        pins = current.read(report["source_union"]["record"])
        current.require(len(pins) == report["source_union"]["count"]
                        and canonical_sha(pins) == report["source_union"]["canonical_sha256"], "authenticated parent union required")
        maps.append(pins)
    refs = [input_ref, inputs["producer"], inputs["current_response"], inputs["current_components"],
            *inputs["methods"], *inputs["case_components"],
            *[r["source_union"]["record"] for r in [forces, components]]]
    pins = current.join(*maps, {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    current.require(forces["case_sequence"] == components["case_sequence"] == SEQUENCE
                    and forces["extra_grid"] is False and components["extra_grid"] is False
                    and forces["geometry_revision"] == "eoere-raised-kicker-screws-v1"
                    and forces["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
                    and forces["all_six_saved_field_admissions_pass"] is True
                    and components["current_response"] == inputs["current_response"]
                    and components["geometry"] == forces["geometry"]
                    and components["hardware_model"] == forces["hardware_model"]
                    and components["release"] == forces["release"] == current.manifest()["release"],
                    "exact current six-case OFF revisions required")
    current.require([r.get("case_id") for r in forces["cases"]] == SEQUENCE
                    and len({r.get("state_id") for r in forces["cases"]}) == len(SEQUENCE)
                    and all(isinstance(r.get("state_id"), str) and r["state_id"] for r in forces["cases"]),
                    "exact ordered case bindings and unique states required")
    cases = []
    for binding, raw_ref in zip(forces["cases"], inputs["case_components"], strict=True):
        field, data = current.read(binding["field"]), current.read(raw_ref)
        current.require(field["case_id"] == data["case_id"] == binding["case_id"]
                        and field["state_id"] == data["state_id"] == binding["state_id"]
                        and data["field"] == binding["field"] and data["admission"] == binding["admission"]
                        and data["raw_field_canonical_sha256"] == canonical_sha(field)
                        and data["connected_mixed_stack_statics"]["mixed_axis_ids"] == MIXED_IDS
                        and len(field["source_inputs"]["shafts"]) == 100
                        and len(data["findings"]["timber"]["shaft_components"]) == 100,
                        "own frozen case/field/component join required")
        shafts = {s["axis_id"]: s for s in field["source_inputs"]["shafts"]}
        wood = {s["axis_id"]: s for s in data["findings"]["timber"]["shaft_components"]}
        rows = []
        for aid in MIXED_IDS:
            trials = [t for t in data["connected_mixed_stack_statics"]["own_surface_trials"] if t["axis_id"] == aid]
            loads = [r for r in field["body_applied_loads"] if r["body"] == shafts[aid]["body"]]
            current.require(len(loads) == len(shafts[aid]["metal_roles"]), "all own selected metal gravity roles required")
            rows.append(check_stack(shafts[aid], wood[aid], trials, loads))
        cases.append({"case_id": binding["case_id"], "state_id": binding["state_id"],
                      "field": binding["field"], "admission": binding["admission"], "components": raw_ref,
                      "mixed_stacks": rows})
    current.verify(pins)
    current.require(current.sha(OWN) == LOADED_SHA, "producer changed during calculation")
    return {"schema": "eoere_current_mixed_stack_affine_raw_yield/v1", "producer": inputs["producer"],
            "inputs": input_ref, "current_response": inputs["current_response"],
            "current_components": inputs["current_components"], "case_sequence": SEQUENCE, "cases": cases,
            "geometry_revision": forces["geometry_revision"], "hardware_revision": forces["hardware_revision"],
            "extra_grid": False, "all_input_sources_unchanged": True,
            "maximum_raw_material_trial_index": max(r["maximum_raw_material_trial_index"] for c in cases for r in c["mixed_stacks"]),
            "compatible_bearing_or_adjusted_ASD_capacity": None, "complete_joint_resistance": None,
            "physical_demand_bounds_established": False, "structural_acceptance": False,
            "native_solve_CAD_rebuild_or_remedy_performed": False, "release": forces["release"],
            "limits": inputs["limits"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
