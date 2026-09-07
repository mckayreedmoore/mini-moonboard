"""Stream selected moving output for fail-only momentum/KE observations."""
import argparse
import gzip
import hashlib
import json
import math
import re
import tempfile
from pathlib import Path

from fea import dynamic_momentum as dynamic
from fea import hardware_mass_cache as mass
from fea import moving_hardware_audit as audit
from fea import moving_hardware_balance as balance
from fea import moving_hardware_control as control
from fea import quiescent_hardware_audit as quiet
from fea.floor_contact_results import cross
from fea.publish_moving_fixture import checked_members

HERE = Path(__file__).resolve().parent / "results/coarse_moving_control"
ARCHIVES = {"preparation.tar.gz": "053d6c06995cb76c666ec8eae85178be299747db96cadd220cabc8355bb5c9d1",
            "native-other.tar.gz": "f90c6b421a4c91620823617a790252009795c782672c77087d4ece0d60c866c1",
            "first-audit.tar.gz": "3c1ca9a3a281a928cf2194e0e15d9102ba657b8f1af693e4f62e745f2b8b4e66"}
LIMITS = ("Fail-only momentum/kinetic-energy observations. Original pressure audit remains failed. "
          "CF resultants are parsed but contact completeness, traction consistency and unilateral contact are not qualified. "
          "CELS and total-energy balance are not evaluated. No Gauss8, refinement, moving-contact or structural qualification.")
_SOURCE_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_CONFIG = (dict(ARCHIVES), LIMITS)


def state_blocks(lines, times):
    """Buffer one chronological DAT state; reuse the existing block parser."""
    header = re.compile(r"^\s*([^\n]+?(?:and time|for time))\s+(\S+)\s*$")
    index, pending = 0, []
    for line in lines:
        match = header.match(line)
        if match:
            time = float(match[2])
            quiet.require(index < len(times), "Extra DAT state")
            if not quiet.close(time, times[index]):
                quiet.require(pending and index + 1 < len(times) and quiet.close(time, times[index+1]),
                              "Missing or out-of-order DAT state")
                yield quiet.blocks("".join(pending), [times[index]])[0]
                pending = []
                index += 1
        pending.append(line)
    quiet.require(pending and index == len(times)-1, "Incomplete DAT grid")
    yield quiet.blocks("".join(pending), [times[index]])[0]


def reconstruct(context, cache, fields, time):
    nodes = {int(n): p for n, p in context["nodes"].items()}
    if fields is not None:
        required = {f"{label} (vx,vy,vz) for set {name} and time" for name in context["bodies"]
                    for label in ("displacements", "velocities")}
        required |= {f"total {label} for set {name} and time" for name in context["bodies"] for label in ("mass", "kinetic energy")}
        required |= {f"statistics for slave set {p['slave']}, master set {p['master']} and time" for p in context["contact_pairs"]}
        ignored = {f"total internal energy for set {name} and time" for name in context["bodies"]}
        ignored |= {label+" for all contact elements and time" for label in
                    ("relative contact displacement (slave element+face,normal,tang1,tang2)",
                     "contact stress (slave element+face,press,tang1,tang2)", "contact spring energy (slave element+face,energy)")}
        ignored |= {"total number of contact elements for time", "total contact spring energy for time"}
        quiet.require(required <= fields.keys(), "Missing primary diagnostic block")
        quiet.require(all(n in required | ignored or n.startswith(("total mass moment of inertia", "center of gravity for set "))
                          for n in fields), "Unexpected diagnostic block")
    bodies = {}
    for name, body in context["bodies"].items():
        if fields is None:
            u = {n: (0., 0., 0.) for n in body["nodes"]}
            v = {n: context["cases"]["moving"]["initial_velocity_mm_s"][name] for n in body["nodes"]}
        else:
            u, v = [quiet.nodal_vectors(fields[f"{label} (vx,vy,vz) for set {name} and time"], body["nodes"])
                    for label in ("displacements", "velocities")]
        native = dynamic.momentum(nodes, cache["operators"]["native_four_point"][name], u, v)
        printed = {}
        if fields is not None:
            for label, key in (("mass", "EMAS"), ("kinetic energy", "ELKE")):
                rows = quiet.numeric(fields[f"total {label} for set {name} and time"], 1)
                quiet.require(len(rows) == 1 and rows[0][0] >= 0 and (key != "EMAS" or rows[0][0] > 0),
                              "Invalid native mass/KE scalar")
                printed[key] = rows[0][0]
        bodies[name] = {"native": native, **printed}
    pairs = {p["slave"]: (quiet.contact_force(fields[f"statistics for slave set {p['slave']}, master set {p['master']} and time"])
                           if fields is not None else {"force_N": (0., 0., 0.), "origin_moment_N_mm": (0., 0., 0.)})
             for p in context["contact_pairs"]}
    return {"time_s": time, "source": "PRINTED U/V AND CF" if fields is not None else "RECONSTRUCTED INITIAL CONDITIONS; NO PRINTED t0",
            "bodies": bodies, "pairs": pairs}


def observe(states, context):
    """Existing thresholds can expose failures, never confer acceptance."""
    reference = context["angular_reference_mm_local"]
    scales = context["diagnostic_reference_scales"]
    ps, hs, es = [balance.scalar(scales[k], positive=True) for k in
                  ("P_star_tonne_mm_s", "H_star_tonne_mm2_s", "E_star_N_mm")]
    add, sub = balance.vector_sum, balance.difference
    results, failures = [], []
    impulses = {p["slave"]: (0., 0., 0.) for p in context["contact_pairs"]}
    moments = dict(impulses)
    def failure(time, quantity, observed, limit):
        quiet.require(math.isfinite(observed), "Nonfinite diagnostic observable")
        if observed > limit:
            failures.append({"time_s": time, "quantity": quantity, "observed": observed, "limit": limit})
    for index, state in enumerate(states):
        time = state["time_s"]
        quiet.require(time == 0 if index == 0 else time > results[-1]["time_s"], "Initial/increasing diagnostic times required")
        pair_result = {}
        for name, pair in state["pairs"].items():
            force = balance.vector(pair["force_N"])
            moment = sub(pair["origin_moment_N_mm"], cross(reference, force))
            if index:
                previous = results[-1]["pairs"][name]
                dt = time-results[-1]["time_s"]
                impulses[name] = add((impulses[name], tuple(.5*dt*(a+b) for a, b in zip(previous["F"], force))))
                moments[name] = add((moments[name], tuple(.5*dt*(a+b) for a, b in zip(previous["Mc"], moment))))
            else:
                quiet.require(all(v == 0 for v in (*force, *moment)), "Expected separated zero-force initial state")
            pair_result[name] = {"F": force, "Mc": moment, "J": impulses[name], "K": moments[name]}
        bodies = {}
        for name, body in state["bodies"].items():
            native = body["native"]
            p = native["linear_momentum"]
            h = sub(native["angular_momentum"], cross(reference, p))
            initial = results[0]["bodies"][name] if index else {"P": p, "Hc": h}
            dp, dh = sub(p, initial["P"]), sub(h, initial["Hc"])
            sign = 1 if name == "WASHER" else -1
            rp = sub(dp, tuple(sign*v for v in add(impulses.values())))
            rh = sub(dh, tuple(sign*v for v in add(moments.values())))
            values = {"P": p, "Hc": h, "mass": native["mass"], "KE_reconstructed": native["kinetic_energy"],
                      "delta_P": dp, "delta_Hc": dh, "linear_residual": rp, "angular_residual": rh}
            failure(time, name+" linear residual", math.hypot(*rp), balance.GATES["body_linear_residual_over_P_star"]*ps)
            failure(time, name+" angular residual", math.hypot(*rh), balance.GATES["body_angular_residual_over_H_star"]*hs)
            if index:
                mass_error = abs(body["EMAS"]/native["mass"]-1)
                ke_error = abs(body["ELKE"]-native["kinetic_energy"])
                ke_scale = max(body["ELKE"], abs(native["kinetic_energy"]), balance.GATES["native_ke_floor_over_E_star"]*es)
                values.update(EMAS=body["EMAS"], ELKE=body["ELKE"], native_mass_relative_error=mass_error,
                              native_KE_absolute_error=ke_error, native_KE_comparison_scale=ke_scale)
                failure(time, name+" native mass error", mass_error, balance.GATES["native_mass_rtol"])
                failure(time, name+" native KE error", ke_error, balance.GATES["native_ke_rtol"]*ke_scale)
            bodies[name] = values
        dp, dh = [add(b[k] for b in bodies.values()) for k in ("delta_P", "delta_Hc")]
        failure(time, "assembly linear drift", math.hypot(*dp), balance.GATES["assembly_linear_drift_over_P_star"]*ps)
        failure(time, "assembly angular drift", math.hypot(*dh), balance.GATES["assembly_angular_drift_over_H_star"]*hs)
        results.append({"time_s": time, "source": state["source"], "bodies": bodies, "pairs": pair_result,
                        "assembly_linear_drift": dp, "assembly_angular_drift": dh})
    quiet.require(len(results) > 1, "Subsequent diagnostic states required")
    return {"status": "FAIL-ONLY OBSERVATIONS; ORIGINAL AUDIT REMAINS FAILED", "limits": LIMITS,
            "qualified": False, "contact_energy_qualified": False, "states": results, "additional_failures": failures,
            "thresholds": dict(balance.GATES), "norm_convention": "Euclidean norms; signed trapezoidal CF impulses/moments"}


def diagnose(directory=HERE):
    directory = Path(directory)
    before = audit.sources()
    own = Path(__file__).read_bytes()
    quiet.require(control.digest(own) == _SOURCE_SHA and (ARCHIVES, LIMITS) == _CONFIG, "Loaded diagnostic source/configuration differs")
    prepared, other, first = [checked_members(directory / n, h) for n, h in ARCHIVES.items()]
    refs = json.loads(first["references.json"])
    quiet.require(refs["preparation_sha256"] == ARCHIVES["preparation.tar.gz"], "Original failure preparation differs")
    log = first["audit/audit.log"].decode()
    quiet.require(log.rstrip().endswith("ValueError: Contact pressure/penetration differs"), "Original pressure failure missing")
    files = {n.removeprefix("solve/"): b for n, b in prepared.items() if n.startswith("solve/")}
    context_bytes, deck = files["frozen/context.json"], files["frozen/control.inp"]
    context = json.loads(context_bytes)
    quiet.require(all(context["source_sha256"][n] == control.digest(b) for n, b in before.items()), "Loaded frozen evaluator differs")
    quiet.require(control.deck(context, "moving").encode() == deck and control.digest(deck) == context["deck_sha256"]["moving"], "Selected deck differs")
    mass.deck_mesh(deck.decode(), context)
    cache = audit.mass_cache(files, context)
    times = quiet.history(other["solve/result/control.sta"].decode(), 2e-5)
    quiet.require(len(times) == 200 and all(quiet.close(t, (i+1)*1e-7) for i, t in enumerate(times)), "Incomplete coarse grid")
    outcome = json.loads(other["solve/result/exit.json"])
    expected_dat = outcome["output_sha256"]["control.dat"]
    quiet.require(expected_dat == refs["DAT_sha256"], "First failure/native DAT identity differs")
    digest = hashlib.sha256()
    def lines(stream):
        for line in stream:
            digest.update(line)
            yield line.decode()
    def states(stream):
        yield reconstruct(context, cache, None, 0.)
        for time, fields in zip(times, state_blocks(lines(stream), times), strict=True):
            yield reconstruct(context, cache, fields, time)
    with gzip.open(directory / "control.dat.gz", "rb") as stream:
        report = observe(states(stream), context)
    quiet.require(digest.hexdigest() == expected_dat, "Streamed DAT differs from retained native output")
    quiet.require(audit.sources() == before and Path(__file__).read_bytes() == own, "Diagnostic source drift")
    report.update(original_failure="ValueError: Contact pressure/penetration differs; original full balance was not evaluated",
                  archive_sha256=dict(ARCHIVES), DAT_sha256=expected_dat, context_sha256=control.digest(context_bytes),
                  deck_sha256=control.digest(deck), mass_blocks_sha256=control.digest(files["frozen/mass/blocks.json.gz"]),
                  diagnostic_source_sha256=control.digest(own), evaluator_sha256={n: control.digest(b) for n, b in before.items()})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=HERE)
    parser.add_argument("--output", type=Path, default=Path("fea/generated/moving-hardware-diagnostics"))
    args = parser.parse_args()
    result = diagnose(args.directory)
    args.output.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix="fail-only-", dir=args.output))
    (destination / "moving_hardware_diagnostic.py.snapshot").write_bytes(Path(__file__).read_bytes())
    (destination / "report.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(destination)
