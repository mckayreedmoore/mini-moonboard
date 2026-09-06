"""Fail-closed complete-window quiet-output audit; no solver or strength acceptance."""
import argparse
import hashlib
import json
import math
import re
import sys
import tempfile
import types
from pathlib import Path

from fea import quiescent_hardware_diagnostic as retained

INPUTS = retained.INPUTS + ("cleanup.json",)
LIMITS = "Quiet numerical output gates only; no moving contact, impulse/momentum balance, core reference-mass or structural qualification."
PRINT_RTOL = 5e-6  # STA prints fewer digits than DAT; comparison is print-resolution only.
_SOURCE_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_CONFIG = (INPUTS, LIMITS, PRINT_RTOL)


def sources():
    data = Path(__file__).read_bytes()
    if hashlib.sha256(data).hexdigest() != _SOURCE_HASH or (INPUTS, LIMITS, PRINT_RTOL) != _CONFIG:
        raise ValueError("Audit source/configuration changed after import")
    for code in compile(data, str(Path(__file__).resolve()), "exec").co_consts:
        if isinstance(code, types.CodeType) and code.co_name.isidentifier():
            loaded = getattr(sys.modules[__name__], code.co_name, None)
            if not isinstance(loaded, types.FunctionType) or loaded.__code__ != code:
                raise ValueError("Loaded audit function differs from source")
    return {"quiescent_hardware_audit.py": data,
            "quiescent_hardware_diagnostic.py": retained.source_snapshot()}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(a, b):
    return math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=PRINT_RTOL, abs_tol=0.)


def stationary_deck(text, context):
    """Exact allowed card sequence excludes loads, SPCs, ties and hidden initial fields."""
    cards = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("**"):
            continue
        if line.startswith("*"):
            cards.append((line, []))
        else:
            require(cards, "Deck data before heading")
            cards[-1][1].append(line)
    case = context["cases"]["quiescent"]
    direct = case.get("direct_quiescent", False)
    require(type(direct) is bool, "Invalid integration intent")
    expected = ["*HEADING", "*NODE"]
    for body in ("BOLT_NUT", "WASHER"):
        expected += [f"*ELEMENT,TYPE=C3D10,ELSET={body}", f"*NSET,NSET={body}", f"*SOLID SECTION,ELSET={body},MATERIAL=STEEL"]
    expected += ["*MATERIAL,NAME=STEEL", "*ELASTIC", "*DENSITY", "*SURFACE INTERACTION,NAME=FRICTIONLESS",
                 "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR"]
    expected += ["*SURFACE,NAME=" + n for n in ("WASHER_HEAD", "CORE_HEAD", "WASHER_BORE", "CORE_SHANK")]
    expected += ["*CONTACT PAIR,INTERACTION=FRICTIONLESS,TYPE=SURFACE TO SURFACE"] * 2
    dynamic_card = "*DYNAMIC,DIRECT,ALPHA=0" if direct else "*DYNAMIC,ALPHA=0"
    expected += ["*INITIAL CONDITIONS,TYPE=VELOCITY", f"*STEP,NLGEOM,INC={case['maximum_increment_count']}", dynamic_card]
    for body in ("BOLT_NUT", "WASHER"):
        expected += [f"*NODE PRINT,NSET={body},FREQUENCY=1", f"*EL PRINT,ELSET={body},FREQUENCY=1,TOTALS=ONLY"]
    expected += ["*NODE FILE,FREQUENCY=1", "*CONTACT FILE,FREQUENCY=1", "*CONTACT PRINT,FREQUENCY=1,TOTALS=YES",
                 "*CONTACT PRINT,SLAVE=WASHER_HEAD,MASTER=CORE_HEAD,FREQUENCY=1",
                 "*CONTACT PRINT,SLAVE=WASHER_BORE,MASTER=CORE_SHANK,FREQUENCY=1", "*END STEP"]
    require([name for name, _ in cards] == expected, "Unsupported stationary deck cards or ordering")
    data = dict(cards)
    velocities = [tuple(map(float, row.split(","))) for row in data["*INITIAL CONDITIONS,TYPE=VELOCITY"]]
    require(all(len(row) == 3 and row[2] == 0 for row in velocities)
            and len(velocities) == 3 * len(context["nodes"])
            and {(r[0], r[1]) for r in velocities} == {(int(n), d) for n in context["nodes"] for d in (1, 2, 3)},
            "Nonzero or incomplete actual initial velocity")
    for body in ("BOLT_NUT", "WASHER"):
        ids = [int(n) for row in data[f"*NSET,NSET={body}"] for n in row.split(",") if n]
        require(len(ids) == len(set(ids)) and set(ids) == set(context["bodies"][body]["nodes"]), "Deck output node ownership differs")
        require(data[f"*NODE PRINT,NSET={body},FREQUENCY=1"] == ["U,V"]
                and data[f"*EL PRINT,ELSET={body},FREQUENCY=1,TOTALS=ONLY"] == ["ELKE,EMAS,ELSE"], "Required body output differs")
    require(len(data[dynamic_card]) == 1, "Malformed dynamic settings")
    times = tuple(map(float, data[dynamic_card][0].split(",")))
    keys = ("initial_dt_s", "total_time_s") if direct else ("initial_dt_s", "total_time_s", "min_dt_s", "max_dt_s")
    require(len(times) == len(keys) and all(close(v, case[k]) for v, k in zip(times, keys, strict=True)), "Deck/context dynamic values differ")
    require([rows for name, rows in cards if name.startswith("*CONTACT PAIR,")] == [["WASHER_HEAD,CORE_HEAD"], ["WASHER_BORE,CORE_SHANK"]], "Actual contact pairs differ")
    require(data["*CONTACT PRINT,FREQUENCY=1,TOTALS=YES"] == ["CDIS,CSTR,CELS,CNUM"]
            and all(data[n] == ["CF"] for n in expected if n.startswith("*CONTACT PRINT,SLAVE=")), "Required contact output differs")
    require(data["*ELASTIC"] == ["210000.,0.3"] and data["*DENSITY"] == ["7.85e-9"]
            and data["*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR"] == ["100000."]
            and all(p["normal_penalty_n_mm3"] == 100000 and p["friction"] == 0 for p in context["contact_pairs"]),
            "Actual provisional material/contact settings differ")


def identities(files):
    require(set(files) == set(INPUTS), "Audit input inventory differs")
    context, freeze, launch, outcome, probe, cleanup = [json.loads(files[n]) for n in
        ("context.json", "freeze.json", "launch.json", "exit.json", "container-probe.json", "cleanup.json")]
    require(retained.sha(files["freeze.json"]) == launch["freeze_sha256"] and freeze["case"] == "quiescent", "Launch freeze differs")
    for n in ("context.json", "control.inp"):
        require(retained.sha(files[n]) == freeze["inputs_sha256"][n], "Frozen input hash differs")
    require(retained.sha(files["control.inp"]) == context["deck_sha256"]["quiescent"], "Deck hash differs")
    for n in ("control.inp", "control.dat", "control.sta", "container-probe.json", "cleanup.json"):
        require(retained.sha(files[n]) == outcome["output_sha256"][n], "Output hash differs")
    inspected = json.loads(probe["stdout"])
    require(len(inspected) == 1 and probe["returncode"] == 0, "Missing terminal container")
    container = inspected[0]
    cid = outcome["owned_container_id"]
    require(re.fullmatch(r"[0-9a-f]{64}", cid) and container["Id"] == cid
            and container["Config"]["Image"] == freeze["image"]
            and container["State"]["Running"] is False and container["State"]["OOMKilled"] is False
            and container["State"]["ExitCode"] == outcome["returncode"], "Terminal ownership/state differs")
    require(outcome["returncode"] == 0 and outcome["cleanup_returncode"] == 0
            and outcome["status"] == "SOLVER COMPLETED; AUDIT PENDING" and outcome["exceptions"] == []
            and cleanup["returncode"] == 0 and cleanup["container_id"] == cid
            and cleanup["stdout"].strip() == cid, "Incomplete solver or owned cleanup")
    case = context["cases"]["quiescent"]
    dynamic = re.findall(r"^\*DYNAMIC[^\n]*\n([^\n]+)", files["control.inp"].decode(), re.MULTILINE)
    require(len(dynamic) == 1 and close(float(dynamic[0].split(",")[1]), case["total_time_s"]), "Deck/context duration differs")
    require(set(case["initial_velocity_mm_s"]) == {"BOLT_NUT", "WASHER"}
            and all(v == [0., 0., 0.] for v in case["initial_velocity_mm_s"].values()), "Not a stationary case")
    retained.actual_mesh(files["control.inp"].decode(), context)
    stationary_deck(files["control.inp"].decode(), context)
    return context


def history(text, duration):
    times = []
    for line in text.splitlines():
        row = line.split()
        if not row or not row[0].isdigit():
            continue
        require(len(row) == 7, "Malformed STA")
        if row[2].endswith("U"):
            continue
        require(row[:2] == ["1", str(len(times) + 1)], "STA sequence differs")
        total, step, dt = map(float, row[4:])
        previous = times[-1] if times else 0.
        require(close(total, step) and math.isfinite(dt) and dt > 0 and total > previous
                and abs(total - previous - dt) <= PRINT_RTOL * total, "Invalid STA times")
        times.append(total)
    require(times and close(times[-1], duration), "Incomplete requested STA duration")
    return times


def blocks(text, times):
    pattern = re.compile(r"^\s*([^\n]+?(?:and time|for time))\s+(\S+)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    result = [{} for _ in times]
    for index, match in enumerate(matches):
        t = float(match[2])
        choices = [i for i, expected in enumerate(times) if close(t, expected)]
        require(len(choices) == 1, "Unmatched or ambiguous DAT time")
        name = match[1].strip()
        state = result[choices[0]]
        require(name not in state, "Duplicate DAT state/block")
        body = text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        state[name] = [line.strip() for line in body.splitlines() if line.strip()
                       and not re.fullmatch(r"INCREMENT\s+\d+", line.strip())]
    return result


def numeric(lines, width, *, empty=False, finite=True):
    require((lines or empty) and all(len(line.split()) == width for line in lines), "Missing or malformed numeric rows")
    rows = [tuple(map(float, line.split())) for line in lines]
    require(not finite or all(math.isfinite(v) for row in rows for v in row), "Nonfinite primary output")
    return rows


def contact_force(lines):
    labels = ("total surface force (fx,fy,fz) and moment about the origin (mx,my,mz)",
              "center of gravity and mean normal", "moment about the center of gravity(mx,my,mz)",
              "area,  normal force (+ = tension) and shear force (size)")
    require(len(lines) == 8 and tuple(lines[::2]) == labels, "Incomplete CF statistics")
    primary = numeric([lines[1]], 6)[0]
    ancillary = numeric([lines[3]], 6, finite=False)[0] + numeric([lines[5]], 3, finite=False)[0]
    area, normal, shear = numeric([lines[7]], 3, finite=False)[0]
    require(math.isfinite(area) and area >= 0, "Invalid CF area")
    rest = ancillary + (normal, shear)
    require(all(math.isfinite(v) for v in rest)
            or (area == 0 and all(v == 0 for v in primary)
                and all(math.isfinite(v) or math.isnan(v) for v in rest)), "Invalid active CF ancillary values")
    require(area != 0 or all(v == 0 for v in primary), "Inactive CF has nonzero primary force/moment")
    return {"force_N": primary[:3], "origin_moment_N_mm": primary[3:], "area_mm2": area}


def outputs(text, times, context):
    states = blocks(text, times)
    pairs = {p["slave"]: p for p in context["contact_pairs"]}
    require({k: p["master"] for k, p in pairs.items()} == {"WASHER_HEAD": "CORE_HEAD", "WASHER_BORE": "CORE_SHANK"}, "Contact pair inventory differs")
    face_owner = {}
    for name in pairs:
        for pair in context["surfaces"][name]["faces"]:
            require(tuple(pair) not in face_owner, "Ambiguous slave face")
            face_owner[tuple(pair)] = name
    results = []
    for t, state in zip(times, states, strict=True):
        def take(name, state=state):
            require(name in state, "Missing DAT block: " + name)
            return state.pop(name)
        def scalar(name):
            rows = numeric(take(name), 1)
            require(len(rows) == 1 and rows[0][0] >= 0, "Invalid native total")
            return rows[0][0]
        bodies = {}
        for name in ("BOLT_NUT", "WASHER"):
            body = {}
            for label, key in (("displacements", "max_displacement_mm"), ("velocities", "max_velocity_mm_s")):
                rows = numeric(take(f"{label} (vx,vy,vz) for set {name} and time"), 4)
                ids = [r[0] for r in rows]
                require(len(ids) == len(set(ids)) and set(ids) == set(context["bodies"][name]["nodes"]), "Incomplete body U/V ownership")
                body[key] = max(math.hypot(*r[1:]) for r in rows)
            for label, key in (("mass", "observed_mass_tonne"), ("kinetic energy", "ELKE_N_mm"), ("internal energy", "ELSE_N_mm")):
                body[key] = scalar(f"total {label} for set {name} and time")
            require(body["observed_mass_tonne"] > 0, "Nonpositive mass")
            bodies[name] = body
        dis = numeric(take("relative contact displacement (slave element+face,normal,tang1,tang2) for all contact elements and time"), 5, empty=True)
        stress = numeric(take("contact stress (slave element+face,press,tang1,tang2) for all contact elements and time"), 5, empty=True)
        energy = numeric(take("contact spring energy (slave element+face,energy) for all contact elements and time"), 3, empty=True)
        require([r[:2] for r in dis] == [r[:2] for r in stress] == [r[:2] for r in energy], "Contact row alignment differs")
        count = scalar("total number of contact elements for time")
        total = scalar("total contact spring energy for time")
        require(count == len(dis) and close(total, math.fsum(r[2] for r in energy)), "CNUM or total CELS differs")
        penetration = 0.
        active = {name: False for name in pairs}
        for d, s, e in zip(dis, stress, energy, strict=True):
            require(d[:2] in face_owner and all(v == int(v) for v in d[:2]), "Unknown quadratic slave face")
            penalty = pairs[face_owner[d[:2]]]["normal_penalty_n_mm3"]
            require(s[2] >= 0 and e[2] >= 0 and math.isclose(s[2], max(0., -penalty*d[2]), rel_tol=PRINT_RTOL, abs_tol=1e-10), "Contact pressure/penetration differs")
            penetration = max(penetration, -d[2])
            active[face_owner[d[:2]]] |= any(v != 0 for v in s[2:]) or e[2] != 0
        forces = {name: contact_force(take(f"statistics for slave set {name}, master set {p['master']} and time")) for name, p in pairs.items()}
        require(all(not active[name] or pair["area_mm2"] > 0 for name, pair in forces.items()), "Inactive CF contradicts point pressure/energy")
        # Native EMAS also emits inertia/centroid summaries; they are not mass-reference qualification.
        for name in state:
            require(any(name.startswith(prefix) for prefix in ("total mass moment of inertia", "center of gravity for set")), "Unexpected DAT output block")
        results.append({"time_s": t, "bodies": bodies, "pairs": forces, "CNUM": int(count),
                        "total_CELS_N_mm": total, "max_penetration_mm": penetration})
    return results


def assess(states, context):
    gates, reference = context["quiescent_diagnostic_gates"], context["diagnostic_reference_scales"]
    require(all(math.isfinite(reference[k]) and reference[k] > 0 for k in
                ("reference_mass_tonne", "E_star_N_mm", "P_star_tonne_mm_s")), "Invalid reference scales")
    failures, impulse, previous = [], {name: 0. for name in states[0]["pairs"]}, None
    for state in states:
        time = state["time_s"]
        def gate(quantity, value, limit, time=time):
            require(math.isfinite(value) and value >= 0 and math.isfinite(limit) and limit > 0, "Invalid frozen gate/reference")
            if value > limit:
                failures.append({"time_s": time, "quantity": quantity, "observed": value, "limit": limit})
        for name, body in state["bodies"].items():
            for key in ("max_displacement_mm", "max_velocity_mm_s"):
                gate(name + " " + key, body[key], gates[key])
        mass_error = abs(state["bodies"]["WASHER"]["observed_mass_tonne"] / reference["reference_mass_tonne"] - 1)
        gate("washer native/reference relative mass error", mass_error, PRINT_RTOL)
        gate("penetration_mm", state["max_penetration_mm"], gates["max_normal_penetration_mm"])
        total = state["total_CELS_N_mm"] + math.fsum(b["ELKE_N_mm"] + b["ELSE_N_mm"] for b in state["bodies"].values())
        gate("ELSE+ELKE+CELS_N_mm", total, gates["max_total_ELSE_ELKE_CELS_over_E_star"] * reference["E_star_N_mm"])
        dt = time - (previous["time_s"] if previous else 0.)
        for name, pair in state["pairs"].items():
            force = math.hypot(*pair["force_N"])
            old = math.hypot(*previous["pairs"][name]["force_N"]) if previous else force
            impulse[name] += dt * max(force, old)
            gate(name + " sampled force-norm integral_N_s", impulse[name], gates["max_each_pair_cumulative_impulse_over_P_star"] * reference["P_star_tonne_mm_s"])
        previous = state
    return {"status": "QUIESCENT OUTPUT GATES FAILED" if failures else "COMPLETE QUIESCENT OUTPUT GATES PASSED",
            "limits": LIMITS, "failures": failures, "states": states,
            "pair_sampled_force_norm_integral_N_s": impulse,
            "impulse_rule": "Sum dt*max(norm(F_previous),norm(F_current)); first interval uses first observed force. Sampled endpoint envelope, not a bound on unobserved forces or momentum qualification.",
            "core_reference_mass_qualified": False}


def audit(files):
    before = sources()
    context = identities(files)
    times = history(files["control.sta"].decode(), context["cases"]["quiescent"]["total_time_s"])
    case = context["cases"]["quiescent"]
    if case.get("direct_quiescent"):
        expected_count = context["integration_intent"]["expected_fixed_increment_count"]
        require(context["integration_intent"]["direct_quiescent"] is True and len(times) == expected_count
                and all(close(t, (i + 1) * case["initial_dt_s"]) for i, t in enumerate(times)), "DIRECT accepted history differs")
    report = assess(outputs(files["control.dat"].decode(), times, context), context)
    require(sources() == before, "Audit source changed during calculation")
    report["input_sha256"] = {n: retained.sha(b) for n, b in files.items()}
    return report


def write_audit(directory, parent):
    before = sources()
    files = {n: (Path(directory) / retained.input_path(n)).read_bytes() for n in INPUTS}
    report = audit(files)
    require(sources() == before, "Audit source changed before publication")
    Path(parent).mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix="quiet-audit-", dir=parent))
    for name, data in before.items():
        (destination / (name + ".snapshot")).write_bytes(data)
    report["source_sha256"] = {n: retained.sha(b) for n, b in before.items()}
    (destination / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path("fea/generated/quiescent-audits"))
    args = parser.parse_args()
    print(write_audit(args.directory, args.output))
