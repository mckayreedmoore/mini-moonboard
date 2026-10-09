"""Anchor the whole summary output ancestry before mkdir or callbacks.

The source-owned summary directory identity is captured on module import.
Each call authenticates and holds that directory, then walks every relative
parent with dir_fd mkdir/open and O_DIRECTORY|O_NOFOLLOW. Replaced namespaces
fail closed; FAILED writes use only the original verified held leaf inode.
The verified v2 loader supplies the unchanged99 summary build and selectors.
"""
import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from types import ModuleType

OWN = Path(__file__).resolve()
SUMMARY_ROOT = OWN.parent.parent
_root_stat = SUMMARY_ROOT.lstat()
if not stat.S_ISDIR(_root_stat.st_mode):
    raise ValueError("source-owned summary root is not a directory")
ROOT_ID = (_root_stat.st_dev, _root_stat.st_ino)  # Pre-callback import identity.
V2 = SUMMARY_ROOT/"review-fix-v2/summarize.py"
V2_SHA = "15dd2c60a1b6db3eeae6e98b0267268a4460c9a6efc86cb711aa8376fb82046f"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
RELEASE = dict.fromkeys(("candidate_accepted", "complete_joint_acceptance", "capacity_established",
                         "fabrication_released", "structural_released", "climbing_released"), False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def identity(value):
    return value.st_dev, value.st_ino


def original():
    raw = V2.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == V2_SHA
            and hashlib.sha256(OWN.read_bytes()).hexdigest() == LOADED_SHA, "frozen output loader/v3 bytes changed")
    loader = ModuleType("exact_z180_summary_v2_loader_15dd2c60")
    loader.__file__ = str(V2)
    exec(compile(raw, str(V2), "exec"), loader.__dict__)  # noqa: S102 -- verified source; writer never called
    return loader.original()


def bind_output(out):
    out = Path(out)
    require(".." not in out.parts, "output parent traversal rejected")
    parent = Path(os.path.abspath(out)).parent.resolve()
    # Do not resolve an attacker-replaced runs-v1 into another ownership root.
    require(parent.is_relative_to(SUMMARY_ROOT/"runs-v1"), "summary belongs under own runs-v1")
    return parent/out.name


def write_to_file(manifest_ref, out):
    held, edges = [], []
    try:
        root_fd = os.open(SUMMARY_ROOT, DIRECTORY_FLAGS)
        held.append(root_fd)
        require(identity(os.fstat(root_fd)) == ROOT_ID, "source-owned summary root identity changed")
        def held_identity():
            require(identity(os.fstat(root_fd)) == ROOT_ID, "held summary root changed")
            for _, _, child_fd, expected in edges:
                require(identity(os.fstat(child_fd)) == expected, "held ancestor changed")
        def namespace():
            held_identity()
            root = SUMMARY_ROOT.lstat()
            require(stat.S_ISDIR(root.st_mode) and identity(root) == ROOT_ID, "source-owned summary root namespace changed")
            for parent_fd, name, _, expected in edges:
                current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                require(stat.S_ISDIR(current.st_mode) and identity(current) == expected, "owned ancestor namespace changed: "+name)
        namespace()
        bound = bind_output(out)
        namespace()
        parent_fd = root_fd
        for name in bound.parent.relative_to(SUMMARY_ROOT).parts:
            namespace()
            try:
                prior = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                # Creation is relative to the held owned parent, never a path.
                os.mkdir(name, dir_fd=parent_fd)
                prior = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            require(stat.S_ISDIR(prior.st_mode), "output ancestor is not a directory: "+name)
            child_fd = os.open(name, DIRECTORY_FLAGS, dir_fd=parent_fd)
            held.append(child_fd)
            expected = identity(prior)
            require(identity(os.fstat(child_fd)) == expected, "opened ancestor identity changed: "+name)
            edges.append((parent_fd, name, child_fd, expected))
            parent_fd = child_fd
            namespace()
        namespace()
        leaf_fd = os.open(bound.name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o666, dir_fd=parent_fd)
        with os.fdopen(leaf_fd, "w+", encoding="utf-8") as stream:
            leaf_id = identity(os.fstat(stream.fileno()))
            attempt = {"schema": "eoere_z180_summary_attempt/v3", "status": "STARTED", "release": RELEASE,
                       "output_adapter_sha256": LOADED_SHA, "whole_ancestry_directory_fd_anchored": True}
            def write(record, *, failed=False):
                held_identity()
                if not failed:
                    namespace()
                leaf = os.stat(bound.name, dir_fd=parent_fd, follow_symlinks=False)
                require(stat.S_ISREG(leaf.st_mode) and identity(leaf) == leaf_id
                        == identity(os.fstat(stream.fileno())), "reserved summary inode changed")
                stream.seek(0)
                json.dump(record, stream, sort_keys=True, indent=2, allow_nan=False)
                stream.write("\n")
                stream.truncate()
                stream.flush()
                os.fsync(stream.fileno())
            try:
                write(attempt)
                a = original()
                manifest = a.decode(a.checked(manifest_ref, {}))
                for path, expected in ((OWN, LOADED_SHA), (V2, V2_SHA)):
                    require(manifest["source_sha256"].get(str(path.relative_to(a.ROOT))) == expected,
                            "exact v3/output-loader source pin required")
                result = a.build(manifest, manifest_ref)  # Unchanged99 implementation.
                write(result)
                return result
            except BaseException as error:
                attempt.update(status="FAILED", exception={"type": type(error).__name__, "message": str(error)})
                # A replaced namespace cannot redirect these original held FDs.
                write(attempt, failed=True)
                raise
    finally:
        for fd in reversed(held):
            os.close(fd)


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
