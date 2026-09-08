"""Source-reconstructed nonlinear contact evidence; no frame/joint approval."""
import gzip
import hashlib
import json
import tempfile
from pathlib import Path

from fea import timber_panel_contact as run
from fea.timber_panel_contact_audit import LIMITS, audit_with_history

OUTPUT = Path("fea/results/timber-panel-contact")
FILES = ("input.json", "contact.inp", "contact.dat", "contact.log", "contact.sta",
         "launch.json", "execution.json")
AUDIT_SOURCES = ("fea/publish_timber_panel_contact.py", "fea/timber_panel_contact_audit.py",
                 "fea/panel_contact_audit.py", "fea/floor_contact_results.py", "fea/timber_release.py")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate(payload):
    """Rebuild preparation from authenticated historical inputs, then audit output."""
    if set(payload) != set(FILES):
        raise ValueError("Incomplete contact replay payload")
    info = json.loads(payload["input.json"])
    if info.get("candidate") != "timber-base-development" or info.get("limits") != run.LIMITS:
        raise ValueError("Unexpected contact candidate or scope")
    run.common.unchanged(info["source_sha256"])
    with tempfile.TemporaryDirectory(prefix="timber-contact-replay-") as temporary:
        fresh = Path(temporary)/"prepared"
        run.prepare(info["penalty"], info["increment"], fresh)
        if (json.loads((fresh/"input.json").read_bytes()) != info
                or (fresh/"contact.inp").read_bytes() != payload["contact.inp"]):
            raise ValueError("Contact input or deck differs from independent reconstruction")
    if sha(payload["contact.inp"]) != info["deck_sha256"]:
        raise ValueError("Contact deck hash differs")
    launch = json.loads(payload["launch.json"])
    if launch != {"input_sha256": sha(payload["input.json"]), "deck_sha256": info["deck_sha256"],
                  "source_sha256": info["source_sha256"], "timeout_seconds": run.TIMEOUT}:
        raise ValueError("Contact launch identity differs")
    execution = json.loads(payload["execution.json"])
    if (execution["status"] != "solver completed; contact audit pending" or execution["limits"] != run.LIMITS
            or any(execution["artifacts"].get(n) != sha(payload[n]) for n in FILES if n != "execution.json")):
        raise ValueError("Contact execution identity differs")
    if "*ERROR" in payload["contact.log"].decode().upper():
        raise ValueError("Contact solver error")
    rows = audit_with_history(payload["contact.dat"].decode(), info, payload["contact.sta"].decode())
    return {"candidate": info["candidate"], "model_limits": run.LIMITS, "audit_limits": LIMITS,
            "input": info, "endpoints": rows,
            "omitted_solver_artifacts_sha256": {n: h for n, h in execution["artifacts"].items() if n not in FILES}}


def main():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite contact publication")
    payload = {n: (run.DIRECTORY/n).read_bytes() for n in FILES}
    sources = dict(json.loads(payload["input.json"])["source_sha256"])
    for name in AUDIT_SOURCES:
        current = run.common.digest(name)
        if name in sources and sources[name] != current:
            raise ValueError("Conflicting audit source identity")
        sources[name] = current
    run.common.unchanged(sources)
    result = validate(payload)
    execution = json.loads(payload["execution.json"])
    if set(execution["artifacts"]) != {p.name for p in run.DIRECTORY.iterdir()}-{"execution.json"}:
        raise ValueError("Contact solver artifact inventory differs")
    if any(run.common.digest(run.DIRECTORY/n) != h for n, h in execution["artifacts"].items()):
        raise ValueError("Contact solver artifacts changed")
    zipped = {n+".gz": gzip.compress(raw, mtime=0) for n, raw in payload.items()}
    result.update(source_sha256=sources, replay_archives={n+".gz": {
        "gzip_sha256": sha(zipped[n+".gz"]), "uncompressed_sha256": sha(raw)} for n, raw in payload.items()},
        archive_note="FRD and auxiliary files omitted; execution hashes retained. No capacity qualification.")
    run.common.unchanged(sources)
    OUTPUT.mkdir(parents=True, exist_ok=False)
    for name, raw in zipped.items():
        with (OUTPUT/name).open("xb") as stream:
            stream.write(raw)
    with (OUTPUT/"summary.json").open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
