"""Archive two terminal geometry attempts; no integration or solver execution."""
import hashlib
import io
import json
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNS = {"failed-import": "leg-section-geometry-rMNuN4", "completed": "leg-section-geometry-2N0ZGp"}
REFERENCE = "fea/results/independent_leg_response/evidence.tar.gz"
REFERENCE_SHA = "476283677930a59e8c0ed202f3455fa72b67880dbfcba3a8062dcb35522dfc5a"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def capture():
    files = {}
    for label, name in RUNS.items():
        directory = ROOT / "fea/generated" / name
        for path in sorted(directory.rglob("*")):
            if path.is_symlink():
                raise ValueError("Runtime symlink rejected")
            if path.is_file():
                files[label+"/"+path.relative_to(directory).as_posix()] = path.read_bytes()
    return files


def publish():
    with (ROOT/REFERENCE).open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != REFERENCE_SHA:
            raise ValueError("Reference archive differs")
    files = capture()
    for label, code in (("failed-import", 1), ("completed", 0)):
        outcome = json.loads(files[label+"/exit.json"])
        if outcome["state"]["Running"] or outcome["state"]["ExitCode"] != code or outcome["cleanup"]["exit_code"] != 0:
            raise ValueError("Expected terminal and cleaned run")
    refs = {"source_runs": RUNS, "reference_archive": REFERENCE, "reference_sha256": REFERENCE_SHA,
            "limits": "Portable replay checks recorded integrals and provenance, not independent surface/volume integration. "
                      "NumPy was supplied through a read-only host mount, not the pinned image; package bytes are not archived or hashed. "
                      "The successful run has terminal records and output JSON but no captured process.log. "
                      "Publication hashes describe retained files, not a retroactive prelaunch manifest."}
    files["references.json"] = json.dumps(refs, indent=2).encode()
    files["publisher.py.snapshot"] = Path(__file__).read_bytes()
    files["members.json"] = json.dumps({n: sha(b) for n, b in files.items()}, sort_keys=True).encode()
    target = HERE/"evidence.tar.gz"
    with tarfile.open(target, "x:gz") as archive:
        for name, data in sorted(files.items()):
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(data), 0o644
            archive.addfile(member, io.BytesIO(data))
    if capture() != {n: b for n, b in files.items() if n.startswith(tuple(label+"/" for label in RUNS))}:
        raise ValueError("Runtime changed during publication")
    with (HERE/"manifest.json").open("x") as stream:
        json.dump({"archive": target.name, "archive_sha256": sha(target.read_bytes()), "archive_bytes": target.stat().st_size,
                   "member_count": len(files), **refs}, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    publish()
