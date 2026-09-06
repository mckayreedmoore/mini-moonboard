"""Pure numerical balance gates for already-reconstructed moving hardware states.

assess(states, scales, reference): states include explicit t=0, then increasing
time_s. Each state has bodies BOLT_NUT/WASHER, each containing native (the
dynamic_momentum.momentum result: mass, linear_momentum, angular_momentum about
origin, kinetic_energy), and native EMAS/ELKE/ELSE scalars. Pairs WASHER_HEAD/
WASHER_BORE contain force_N and origin_moment_N_mm acting on the washer.
CELS_N_mm is the assembly contact energy. At t=0 the caller supplies known
initial-condition energy/mass values, not invented printed observations.

scales supplies P_star_tonne_mm_s, H_star_tonne_mm2_s, E_star_N_mm. reference is
fixed XYZ in mm. Extra body fields (e.g. physical_Gauss8) are not formal gates.
This function does not establish provenance, initial-velocity correctness,
complete requested output grids, contact completeness or refinement agreement.
"""
import math

from fea.floor_contact_results import cross

GATES = {"native_mass_rtol": 5e-6, "native_ke_rtol": 5e-6,
         "native_ke_floor_over_E_star": 1e-8, "body_linear_residual_over_P_star": 1e-3,
         "body_angular_residual_over_H_star": 1e-3, "assembly_linear_drift_over_P_star": 1e-4,
         "assembly_angular_drift_over_H_star": 1e-4, "total_energy_residual_over_E_star": .01,
         "min_endpoint_pair_impulse_over_P_star": 1e-3, "min_endpoint_core_ke_over_E_star": 1e-4}
LIMITS = ("Numerical gates on supplied states only; no file/provenance, initial-velocity, complete-window, "
          "contact-output or timestep-refinement qualification. No physical Gauss8 balance, moving-contact "
          "or structural acceptance inferred.")


def scalar(value, *, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError("Expected finite nonnegative scalar (positive for mass/scales)")
    return value


def vector(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) for v in value):
        raise ValueError("Expected finite XYZ vector")
    return tuple(value)


def difference(a, b):
    return vector(tuple(x-y for x, y in zip(a, b, strict=True)))


def vector_sum(values):
    values = list(values)
    return vector(tuple(math.fsum(v[k] for v in values) for k in range(3)))


def assess(states, scales, reference):
    reference = vector(reference)
    linear_scale, angular_scale, energy_scale = [scalar(scales[k], positive=True) for k in
        ("P_star_tonne_mm_s", "H_star_tonne_mm2_s", "E_star_N_mm")]
    if not isinstance(states, (list, tuple)) or len(states) < 2:
        raise ValueError("Explicit initial state and subsequent states required")
    if states[0]["time_s"] != 0:
        raise ValueError("Initial t=0 state required")
    names, pairs = ("BOLT_NUT", "WASHER"), ("WASHER_HEAD", "WASHER_BORE")
    results, failures = [], []
    impulses = {p: (0., 0., 0.) for p in pairs}
    moment_impulses = dict(impulses)
    force_norm_integrals = {p: 0. for p in pairs}
    for index, state in enumerate(states):
        time = scalar(state["time_s"])
        if index and time <= states[index-1]["time_s"]:
            raise ValueError("State times must increase strictly")
        if set(state["bodies"]) != set(names) or set(state["pairs"]) != set(pairs):
            raise ValueError("Exact two-body/two-pair inventory required")
        body_results, pair_results = {}, {}
        def gate(quantity, observed, limit, time=time):
            scalar(observed)
            scalar(limit, positive=True)
            if observed > limit:
                failures.append({"time_s": time, "quantity": quantity, "observed": observed, "limit": limit})
        for name in names:
            body = state["bodies"][name]
            native = body["native"]
            mass = scalar(native["mass"], positive=True)
            p, h0 = vector(native["linear_momentum"]), vector(native["angular_momentum"])
            h = difference(h0, cross(reference, p))
            ke, printed_ke = scalar(native["kinetic_energy"]), scalar(body["ELKE"])
            printed_mass = scalar(body["EMAS"], positive=True)
            internal = scalar(body["ELSE"])
            mass_error = abs(printed_mass / mass - 1)
            floor = GATES["native_ke_floor_over_E_star"] * energy_scale
            denominator = max(printed_ke, ke, floor)
            ke_error = abs(printed_ke-ke)
            gate(name + " native mass relative error", mass_error, GATES["native_mass_rtol"])
            gate(name + " native kinetic-energy error", ke_error, GATES["native_ke_rtol"] * denominator)
            body_results[name] = {"mass": mass, "P": p, "Hc": h, "KE_reconstructed": ke,
                                  "EMAS": printed_mass, "ELKE": printed_ke, "ELSE": internal,
                                  "native_mass_relative_error": mass_error, "native_KE_absolute_error": ke_error,
                                  "native_KE_comparison_scale": denominator,
                                  "native_KE_floor_controls": floor >= max(printed_ke, ke)}
        for name in pairs:
            force = vector(state["pairs"][name]["force_N"])
            moment0 = vector(state["pairs"][name]["origin_moment_N_mm"])
            moment = difference(moment0, cross(reference, force))
            if not index and any(v != 0 for v in (*force, *moment0)):
                raise ValueError("Explicit justified zero initial pair force/moment required")
            if index:
                dt = time-results[-1]["time_s"]
                previous = results[-1]["pairs"][name]
                impulses[name] = vector_sum((impulses[name], tuple(.5 * dt * (a+b) for a, b in zip(previous["F"], force, strict=True))))
                moment_impulses[name] = vector_sum((moment_impulses[name], tuple(.5 * dt * (a+b) for a, b in zip(previous["Mc"], moment, strict=True))))
                force_norm_integrals[name] += .5 * dt * (math.hypot(*previous["F"]) + math.hypot(*force))
                scalar(force_norm_integrals[name])
            pair_results[name] = {"F": force, "Mc": moment, "J": impulses[name], "K": moment_impulses[name],
                                  "cumulative_force_norm_integral": force_norm_integrals[name]}
        total_energy = math.fsum([body_results[n]["ELKE"] + body_results[n]["ELSE"] for n in names] + [scalar(state["CELS_N_mm"])])
        initial_bodies = results[0]["bodies"] if index else body_results
        for name in names:
            dp = difference(body_results[name]["P"], initial_bodies[name]["P"])
            dh = difference(body_results[name]["Hc"], initial_bodies[name]["Hc"])
            sign = 1 if name == "WASHER" else -1
            rp = difference(dp, tuple(sign*v for v in vector_sum(impulses.values())))
            rh = difference(dh, tuple(sign*v for v in vector_sum(moment_impulses.values())))
            body_results[name].update(delta_P=dp, delta_Hc=dh, linear_residual=rp, angular_residual=rh)
            gate(name + " linear balance norm", math.hypot(*rp), GATES["body_linear_residual_over_P_star"] * linear_scale)
            gate(name + " angular balance norm", math.hypot(*rh), GATES["body_angular_residual_over_H_star"] * angular_scale)
        drift_p = vector_sum(body_results[n]["delta_P"] for n in names)
        drift_h = vector_sum(body_results[n]["delta_Hc"] for n in names)
        energy_residual = total_energy - (results[0]["total_native_energy"] if index else total_energy)
        gate("assembly linear drift norm", math.hypot(*drift_p), GATES["assembly_linear_drift_over_P_star"] * linear_scale)
        gate("assembly angular drift norm", math.hypot(*drift_h), GATES["assembly_angular_drift_over_H_star"] * angular_scale)
        gate("total native energy residual", abs(energy_residual), GATES["total_energy_residual_over_E_star"] * energy_scale)
        results.append({"time_s": time, "bodies": body_results, "pairs": pair_results,
                        "assembly_linear_drift": drift_p, "assembly_angular_drift": drift_h,
                        "CELS": state["CELS_N_mm"], "total_native_energy": total_energy,
                        "native_energy_residual": energy_residual})
    insufficient = []
    for name in pairs:
        value = math.hypot(*impulses[name])
        limit = GATES["min_endpoint_pair_impulse_over_P_star"] * linear_scale
        if value < limit:
            insufficient.append({"quantity": name + " endpoint net impulse norm", "observed": value, "minimum": limit})
    core_energy = results[-1]["bodies"]["BOLT_NUT"]["ELKE"]
    limit = GATES["min_endpoint_core_ke_over_E_star"] * energy_scale
    if core_energy < limit:
        insufficient.append({"quantity": "endpoint core ELKE", "observed": core_energy, "minimum": limit})
    status = "NUMERICAL BALANCE GATES FAILED" if failures else "NUMERICAL BALANCE INCONCLUSIVE" if insufficient else "NUMERICAL BALANCE GATES PASSED"
    return {"status": status, "limits": LIMITS, "reference_mm": reference, "gates": dict(GATES),
            "states": results, "failures": failures, "insufficient_endpoint_transfer": insufficient,
            "peak_core_ELKE": max(s["bodies"]["BOLT_NUT"]["ELKE"] for s in results),
            "norm_convention": "Euclidean vector norms; signed trapezoidal J/K; trapezoidal integral of force norms",
            "full_window_qualified": False, "refinement_qualified": False}
