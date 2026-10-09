"""Directory-fd output reservation around the unchanged frozen summary build.

The parent inode is recorded before opening its O_NOFOLLOW directory handle.
Leaf creation is exclusive and relative to that handle. Every payload write
uses the retained leaf inode; a replaced canonical parent fails closed and its
FAILED receipt stays in the original owned directory. No producer is loaded.
"""
import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from types import ModuleType

OWN = Path(__file__).resolve()
FROZEN = OWN.parent.parent/"summarize.py"
FROZEN_SHA = "99ead1194671c82e0e28f905e84c4208cf2a82dc1ed4532aaf1aeb13c0c7124d"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
RELEASE = dict.fromkeys(("candidate_accepted", "complete_joint_acceptance", "capacity_established",
                         "fabrication_released", "structural_released", "climbing_released"), False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def identity(value):
    return value.st_dev, value.st_ino


def original():
    raw = FROZEN.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == FROZEN_SHA
            and hashlib.sha256(OWN.read_bytes()).hexdigest() == LOADED_SHA, "frozen summary/output adapter bytes changed")
    module = ModuleType("exact_frozen_z180_summary_99ead119")
    module.__file__ = str(FROZEN)
    exec(compile(raw, str(FROZEN), "exec"), module.__dict__)  # noqa: S102 -- exact frozen definitions; no candidate work on import
    return module


def bind_output(out):
    out = Path(out)
    require(".." not in out.parts, "output parent traversal rejected")
    canonical_parent = Path(os.path.abspath(out)).parent.resolve()
    owned_runs = FROZEN.parent/"runs-v1"
    require(not owned_runs.is_symlink() and owned_runs.resolve().is_relative_to(FROZEN.parent)
            and canonical_parent.is_relative_to(owned_runs.resolve()), "summary belongs under own runs-v1")
    return canonical_parent/out.name


def write_to_file(manifest_ref, out):
    bound = bind_output(out)
    bound.parent.mkdir(parents=True, exist_ok=True)
    prior_parent = bound.parent.lstat()  # Recorded BEFORE any leaf creation.
    require(stat.S_ISDIR(prior_parent.st_mode), "canonical parent must be a directory")
    parent_fd = os.open(bound.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        require(identity(os.fstat(parent_fd)) == identity(prior_parent), "opened parent identity changed")
        def live_parent():
            current = bound.parent.lstat()
            require(stat.S_ISDIR(current.st_mode) and identity(current) == identity(prior_parent), "canonical parent identity changed")
        live_parent()
        leaf_fd = os.open(bound.name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o666, dir_fd=parent_fd)
        with os.fdopen(leaf_fd, "w+", encoding="utf-8") as stream:
            opened_leaf = os.fstat(stream.fileno())
            attempt = {"schema": "eoere_z180_summary_attempt/v2", "status": "STARTED", "release": RELEASE,
                       "output_adapter_sha256": LOADED_SHA, "directory_fd_anchored": True}
            def write(record):
                # Both checks stay anchored even if the canonical path changes.
                require(identity(os.fstat(parent_fd)) == identity(prior_parent), "reserved directory handle changed")
                leaf = os.stat(bound.name, dir_fd=parent_fd, follow_symlinks=False)
                require(stat.S_ISREG(leaf.st_mode) and identity(leaf) == identity(opened_leaf)
                        == identity(os.fstat(stream.fileno())), "reserved summary inode changed")
                stream.seek(0)
                json.dump(record, stream, sort_keys=True, indent=2, allow_nan=False)
                stream.write("\n")
                stream.truncate()
                stream.flush()
                os.fsync(stream.fileno())
            try:
                live_parent()  # Compare opened parent identity before any write.
                write(attempt)
                a = original()
                manifest = a.decode(a.checked(manifest_ref, {}))
                require(manifest["source_sha256"].get(str(OWN.relative_to(a.ROOT))) == LOADED_SHA,
                        "exact corrected output adapter source pin required")
                result = a.build(manifest, manifest_ref)  # Unchanged source joins/selectors.
                live_parent()
                write(result)
                return result
            except BaseException as error:
                attempt.update(status="FAILED", exception={"type": type(error).__name__, "message": str(error)})
                write(attempt)  # Original anchored directory, never replacement.
                raise
    finally:
        os.close(parent_fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = write_to_file({"path": args.manifest, "sha256": args.manifest_sha256}, args.out)
    print(json.dumps({"schema": result["schema"], "cases": len(result["cases"]), "output": str(args.out)}))


if __name__ == "__main__":
    main()
