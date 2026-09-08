"""Immutable two-penalty/two-increment coupon audit, not frame qualification."""
import gzip
import hashlib
import json
from pathlib import Path

from fea import panel_contact_coupon as coupon
from fea.panel_contact_audit import audit, audit_history

DIRECTORY = Path("fea/generated/panel-contact-series")
OUTPUT = Path("fea/results/panel-contact-coupon")
CASES = {f"k{k}_i{i.replace('.', 'p')}": (float(k), float(i))
         for k in (10000, 100000) for i in ("0.25", "0.125")}
FILES = ("input.json", "coupon.inp", "launch.json", "coupon.log", "coupon.dat",
         "coupon.sta", "execution.json")
SOURCES = (coupon.SOURCE, Path("fea/panel_contact_coupon.py"),
           Path("fea/floor_contact.py"), Path("fea/solve_bearing_frame.py"))
AUDIT_SOURCES = (Path("fea/publish_panel_contact_coupon.py"), Path("fea/panel_contact_audit.py"),
                 Path("fea/floor_contact_results.py"))
LIMITS = ("Eccentric prescribed-motion two-cube C3D10 control only. Four nonlinear "
          "runs audit contact wrench and penalty/increment sensitivity; no frame "
          "contact result, measured wood contact stiffness, joint capacity or approval.")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalized(value):
    return json.loads(json.dumps(value))


def validate(payload, parameters):
    """Replay exact prepared inputs and every output endpoint from archived bytes."""
    if set(payload) != set(FILES):
        raise ValueError("Incomplete coupon replay payload")
    info = json.loads(payload["input.json"])
    penalty, increment = parameters
    text, context = coupon.deck(coupon.SOURCE.read_text(), penalty, increment)
    sources = {str(p): coupon.digest(p) for p in SOURCES}
    expected = {**context, "source_sha256": sources, "deck_sha256": sha(text.encode())}
    if info != normalized(expected) or payload["coupon.inp"] != text.encode():
        raise ValueError("Coupon context or deck differs")
    launch = json.loads(payload["launch.json"])
    if launch != {"input_sha256": sha(payload["input.json"]),
                  "deck_sha256": info["deck_sha256"], "source_sha256": sources,
                  "timeout_seconds": 60}:
        raise ValueError("Coupon launch differs")
    execution = json.loads(payload["execution.json"])
    if (execution["status"] != "solver exited successfully; contact audit pending"
            or execution["limits"] != coupon.LIMITS
            or any(execution["artifacts"].get(n) != sha(payload[n]) for n in FILES
                   if n != "execution.json")):
        raise ValueError("Coupon execution identity differs")
    if "*ERROR" in payload["coupon.log"].decode().upper():
        raise ValueError("Coupon solver error")
    rows = audit(payload["coupon.dat"].decode(), info)
    audit_history(payload["coupon.sta"].decode(), rows, increment)
    return {"penalty_n_per_mm3": penalty, "maximum_increment": increment,
            "input": info, "endpoints": rows,
            "omitted_solver_artifacts_sha256": {n: h for n, h in execution["artifacts"].items()
                                                if n not in FILES}}


def comparisons(cases):
    def delta(first, second):
        a, b = cases[first]["endpoints"][-1], cases[second]["endpoints"][-1]
        return {"first": first, "second": second,
                "contact_wrench_second_minus_first_n_nmm":
                    [y-x for x, y in zip(a["contact_on_upper_wrench_n_nmm"],
                                        b["contact_on_upper_wrench_n_nmm"], strict=True)],
                "penetration_second_minus_first_mm": b["maximum_penetration_mm"]-a["maximum_penetration_mm"],
                "pressure_second_minus_first_mpa": b["maximum_pressure_mpa"]-a["maximum_pressure_mpa"]}
    return {"increment": [delta(f"k{k}_i0p25", f"k{k}_i0p125") for k in (10000, 100000)],
            "penalty": [delta(f"k10000_i{i}", f"k100000_i{i}") for i in ("0p25", "0p125")]}


def main():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite coupon publication")
    if {p.name for p in DIRECTORY.iterdir()} != set(CASES):
        raise ValueError("Require exactly the two-by-two coupon series")
    sources = {str(p): coupon.digest(p) for p in (*SOURCES, *AUDIT_SOURCES)}
    cases, archives, compressed = {}, {}, {}
    for name, parameters in CASES.items():
        directory = DIRECTORY/name
        payload = {n: (directory/n).read_bytes() for n in FILES}
        row = validate(payload, parameters)
        execution = json.loads(payload["execution.json"])
        if set(execution["artifacts"]) != {p.name for p in directory.iterdir()}-{"execution.json"}:
            raise ValueError("Coupon solver artifact inventory differs")
        if any(coupon.digest(directory/n) != h for n, h in execution["artifacts"].items()):
            raise ValueError("Coupon solver artifact differs")
        for filename, raw in payload.items():
            target = f"{name}/{filename}.gz"
            zipped = gzip.compress(raw, mtime=0)
            compressed[target] = zipped
            archives[target] = {"gzip_sha256": sha(zipped), "uncompressed_sha256": sha(raw)}
        cases[name] = row
    if any(coupon.digest(p) != h for p, h in sources.items()):
        raise ValueError("Coupon publication sources changed")
    summary = {"limits": LIMITS, "case_count": 4, "source_sha256": sources,
               "cases": cases, "comparisons": comparisons(cases), "replay_archives": archives,
               "archive_note": "FRD and auxiliary solver files are omitted; their execution hashes are retained."}
    OUTPUT.mkdir(parents=True, exist_ok=False)
    for name, raw in compressed.items():
        path = OUTPUT/name
        path.parent.mkdir(exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
    with (OUTPUT/"summary.json").open("x") as stream:
        stream.write(json.dumps(summary, indent=2, allow_nan=False)+"\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
