"""Publish one terminal raw run, streaming large fields; no numerical audit."""
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / "fea/generated/moving-hardware-solves/moving-9gsvcbgg"
PREPARATION_SHA = "053d6c06995cb76c666ec8eae85178be299747db96cadd220cabc8355bb5c9d1"
LIMIT = 95 * 1024**2
CHUNK = 1024**2


def stream_digest(stream):
    digest, size = hashlib.sha256(), 0
    while data := stream.read(CHUNK):
        digest.update(data)
        size += len(data)
    return digest.hexdigest(), size


def identity(path):
    with path.open("rb") as stream:
        digest, size = stream_digest(stream)
    return {"sha256": digest, "bytes": size}


def encoded(value):
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()


def publish():
    if identity(HERE / "preparation.tar.gz")["sha256"] != PREPARATION_SHA:
        raise ValueError("Selected preparation archive differs")
    freeze_bytes = (RUN / "freeze.json").read_bytes()
    launch_bytes = (RUN / "launch.json").read_bytes()
    exit_bytes = (RUN / "result/exit.json").read_bytes()
    outcome = json.loads(exit_bytes)
    if (outcome["status"] != "SOLVER COMPLETED; AUDIT PENDING" or outcome["returncode"] != 0
            or outcome["cleanup_returncode"] != 0 or outcome["exceptions"]
            or outcome["container_stopped_successfully_before_cleanup"] is not True):
        raise ValueError("Terminal solver and cleanup evidence required")
    inventory = outcome["output_sha256"]
    actual = {p.relative_to(RUN / "result").as_posix() for p in (RUN / "result").rglob("*") if p.is_file()}
    if actual != set(inventory) | {"exit.json"}:
        raise ValueError("Native output inventory differs")
    large = {}
    for name in ("control.dat", "control.frd"):
        target = HERE / (name + ".gz")
        digest, size = hashlib.sha256(), 0
        with ((RUN / "result" / name).open("rb") as source, target.open("xb") as destination,
              gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0, compresslevel=9) as zipped):
            while data := source.read(CHUNK):
                digest.update(data)
                size += len(data)
                zipped.write(data)
        if digest.hexdigest() != inventory[name]:
            raise ValueError("Native field changed: " + name)
        compressed = identity(target)
        print(json.dumps({"file": target.name, **compressed}), flush=True)
        if compressed["bytes"] > LIMIT:
            raise ValueError("Compressed file exceeds 95 MiB; retained, no automatic partition: " + str(target))
        large[name] = {"file": target.name, "plain_sha256": digest.hexdigest(), "plain_bytes": size,
                       "compressed_sha256": compressed["sha256"], "compressed_bytes": compressed["bytes"]}
    others = {"solve/launch.json": launch_bytes, "solve/result/exit.json": exit_bytes}
    for name, expected in inventory.items():
        if name in large:
            continue
        data = (RUN / "result" / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("Native ancillary output changed: " + name)
        others["solve/result/" + name] = data
    others["members.json"] = encoded({name: hashlib.sha256(data).hexdigest() for name, data in others.items()})
    target = HERE / "native-other.tar.gz"
    with (target.open("xb") as destination, gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as zipped,
          tarfile.open(fileobj=zipped, mode="w|") as archive):
        for name, data in sorted(others.items()):
            member = tarfile.TarInfo(name)
            member.size = len(data)
            member.mode = 0o644
            archive.addfile(member, io.BytesIO(data))
    other = {"file": target.name, **identity(target)}
    if other["bytes"] > LIMIT:
        raise ValueError("Ancillary archive exceeds 95 MiB; no automatic partition")
    if (freeze_bytes != (RUN / "freeze.json").read_bytes() or launch_bytes != (RUN / "launch.json").read_bytes()
            or exit_bytes != (RUN / "result/exit.json").read_bytes()
            or any(identity(RUN / "result" / name)["sha256"] != expected for name, expected in inventory.items())):
        raise ValueError("Native evidence changed during publication")
    report = {"status": "RAW SOLVER COMPLETION EVIDENCE ONLY", "numerical_audit_included": False,
              "limits": "No moving numerical pass, refinement qualification, contact qualification or structural capacity claimed.",
              "source_run": str(RUN.relative_to(ROOT)), "preparation_archive": "preparation.tar.gz",
              "preparation_sha256": PREPARATION_SHA, "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
              "large_fields": large, "other_archive": other}
    with (HERE / "native-output.json").open("xb") as destination:
        destination.write(encoded(report))
    print(json.dumps(other), flush=True)


if __name__ == "__main__":
    publish()
