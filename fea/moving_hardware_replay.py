"""Reconstruct moving state integrals; launch provenance is a separate required gate."""
import json

from fea import dynamic_momentum
from fea import hardware_mass_cache as mass
from fea import moving_hardware_control as control
from fea import quiescent_hardware_audit as quiet


def reconstruct(context_bytes, deck_bytes, cache, dat_text, sta_text):
    """Return t0 plus complete coarse-grid states, never a qualification verdict.

    Caller must establish frozen launch/cache provenance and passed initial-pose
    evidence. t0 derives from initial conditions, not printed native output.
    """
    context = json.loads(context_bytes)
    case = context["cases"].get("moving", {})
    quiet.require(set(context["cases"]) == {"moving"}
                  and case.get("direct_moving") is True
                  and case.get("initial_dt_s") == 1e-7
                  and case.get("total_time_s") == 2e-5
                  and case.get("maximum_increment_count") == 200
                  and case.get("alpha") == 0
                  and case.get("initial_velocity_mm_s") == {"BOLT_NUT": [0., 0., 0.], "WASHER": [-100., 100., 0.]},
                  "Unsupported moving reconstruction case")
    quiet.require(control.deck(context, "moving").encode() == deck_bytes
                  and mass.sha(deck_bytes) == context["deck_sha256"]["moving"],
                  "Actual moving deck differs")
    mass.deck_mesh(deck_bytes.decode(), context)
    mass.validate_cache(cache, context_bytes)
    nodes = {int(n): tuple(p) for n, p in context["nodes"].items()}
    times = quiet.history(sta_text, case["total_time_s"])
    quiet.require(len(times) == 200 and all(quiet.close(t, (i + 1)*1e-7) for i, t in enumerate(times)),
                  "Incomplete fixed moving grid")
    # Reuse complete contact/body validation; maxima alone are not momentum data.
    summaries = quiet.outputs(dat_text, times, context)
    raw = quiet.blocks(dat_text, times)

    def integrals(body, displacement, velocity):
        return {key: dynamic_momentum.momentum(nodes, cache["operators"][operator][body], displacement, velocity)
                for key, operator in (("native", "native_four_point"), ("physical_Gauss8", "physical_Gauss8"))}

    initial = {"time_s": 0., "source": "RECONSTRUCTED INITIAL CONDITIONS; NOT PRINTED NATIVE OUTPUT",
               "bodies": {}, "pairs": {p["slave"]: {"force_N": (0., 0., 0.), "origin_moment_N_mm": (0., 0., 0.)}
                                         for p in context["contact_pairs"]}, "CELS_N_mm": 0.}
    for name, body in context["bodies"].items():
        u = {n: (0., 0., 0.) for n in body["nodes"]}
        v = {n: tuple(case["initial_velocity_mm_s"][name]) for n in body["nodes"]}
        result = integrals(name, u, v)
        initial["bodies"][name] = {**result, "EMAS": result["native"]["mass"],
                                    "ELKE": result["native"]["kinetic_energy"], "ELSE": 0.}
    states = [initial]
    for t, summary, fields in zip(times, summaries, raw, strict=True):
        state = {"time_s": t, "source": "NATIVE OUTPUT WITH INDEPENDENT MASS RECONSTRUCTION",
                 "bodies": {}, "pairs": summary["pairs"], "CELS_N_mm": summary["total_CELS_N_mm"]}
        for name, body in context["bodies"].items():
            u, v = [quiet.nodal_vectors(fields[f"{label} (vx,vy,vz) for set {name} and time"], body["nodes"])
                    for label in ("displacements", "velocities")]
            result = integrals(name, u, v)
            native = summary["bodies"][name]
            state["bodies"][name] = {**result, "EMAS": native["observed_mass_tonne"],
                                      "ELKE": native["ELKE_N_mm"], "ELSE": native["ELSE_N_mm"]}
        states.append(state)
    return states
