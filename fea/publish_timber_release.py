"""Immutable compact evidence for the conditional K12 panel-edge release."""
import gzip
import hashlib
import json
import math
from pathlib import Path

from fea import timber_release as run

OUTPUT = Path("fea/results/timber-release")
NAMES = ("input.json", "K12.inp", "K12.dat", "K12.log", "K12.sta", "K12.launch.json", "K12.json")


def validate_replay(replay, record):
    """Only eigensolver roundoff may differ between recorded NumPy versions.

    Matrix entries, displacements, reactions, gap values and all other replay
    fields remain exact. The two 3-value spectra are recomputed from those
    identical matrices, not accepted from the archived solver unchecked.
    """
    current = json.loads(json.dumps(replay, allow_nan=False))
    expected = {key: record[key] for key in current}
    for name in ("bonded_compliance", "released_compliance"):
        actual = current["comparison"][name]["symmetric_eigenvalues_mm_per_n"]
        saved = expected["comparison"][name]["symmetric_eigenvalues_mm_per_n"]
        if len(actual) != 3 or len(saved) != 3 or any(
                not math.isfinite(b) or b <= 0 or not math.isclose(a, b, rel_tol=1e-13, abs_tol=1e-18)
                for a, b in zip(actual, saved, strict=True)):
            raise ValueError("Release compliance spectrum replay differs")
        current["comparison"][name]["symmetric_eigenvalues_mm_per_n"] = saved
    if current != expected:
        raise ValueError("Release result replay differs")


def publish():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite release publication")
    payloads = {name: (run.DIRECTORY/name).read_bytes() for name in NAMES}
    sha = lambda data: hashlib.sha256(data).hexdigest()
    info, record, launch = (json.loads(payloads[name]) for name in ("input.json", "K12.json", "K12.launch.json"))
    if (info.get("candidate") != "timber-base-development" or record.get("candidate") != info["candidate"]
            or info.get("limits") != run.LIMITS or record.get("limits") != run.LIMITS):
        raise ValueError("Unexpected release candidate or scope")
    run.basis_run.unchanged(info["source_sha256"])
    if (record["input_sha256"] != sha(payloads["input.json"])
            or launch["input_sha256"] != record["input_sha256"]
            or info["deck_sha256"] != sha(payloads["K12.inp"])
            or launch["deck_sha256"] != info["deck_sha256"]
            or launch["source_sha256"] != info["source_sha256"]):
        raise ValueError("Release input/deck/launch identity differs")
    required = {name for name in NAMES if name not in ("input.json", "K12.json")}
    if not required <= record["artifacts"].keys() or any(Path(name).name != name for name in record["artifacts"]):
        raise ValueError("Missing or invalid solver artifact inventory")
    run.basis_run.unchanged({str(run.DIRECTORY/name): digest for name, digest in record["artifacts"].items()})
    if any(sha(payloads[name]) != record["artifacts"][name] for name in required):
        raise ValueError("Captured solver artifact changed")
    if "*ERROR" in payloads["K12.log"].decode().upper():
        raise ValueError("Solver log contains an error")
    replay = run.audit(payloads["K12.inp"].decode(), payloads["K12.dat"].decode(), info)
    validate_replay(replay, record)
    sources = {**info["source_sha256"], "fea/publish_timber_release.py": run.basis_run.digest(__file__)}
    archives = {name+".gz": gzip.compress(data, mtime=0) for name, data in payloads.items()}
    report = {"candidate": info["candidate"], "limits": run.LIMITS, "source_sha256": sources,
        "input": info, **replay,
        "omitted_diagnostic_artifacts_sha256": {name: value for name, value in record["artifacts"].items() if name not in required},
        "replay_archives": {name+".gz": {"gzip_sha256": sha(archives[name+".gz"]),
            "uncompressed_sha256": sha(data)} for name, data in payloads.items()}}
    run.basis_run.unchanged(sources)
    run.basis_run.unchanged({str(run.DIRECTORY/name): sha(data) for name, data in payloads.items()})
    OUTPUT.mkdir(parents=True, exist_ok=False)
    for name, data in archives.items():
        with (OUTPUT/name).open("xb") as stream:
            stream.write(data)
    run.basis_run.save(OUTPUT/"summary.json", report)


if __name__ == "__main__":
    publish()
