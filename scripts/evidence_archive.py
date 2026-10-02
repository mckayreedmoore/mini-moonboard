"""Archive explicit evidence trees, prove restoration, then optionally prune.

Only ignored files are eligible by default. Archive and manifest must live
outside the source repository. No native analysis is run by this tool.
"""

import argparse
import gzip
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

CHUNK = 1024 * 1024
FORMAT = "mini-moonboard-evidence-archive-v1"


def now():
    return datetime.now(UTC).isoformat()


def digest(stream):
    result = hashlib.sha256()
    while chunk := stream.read(CHUNK):
        result.update(chunk)
    return result.hexdigest()


def file_digest(path):
    with path.open("rb") as stream:
        return digest(stream)


def relative_path(value):
    path = PurePosixPath(value)
    if (path.is_absolute() or not path.parts or ".." in path.parts
            or ".git" in path.parts or str(path) != value):
        raise ValueError(f"Unsafe relative path: {value!r}")
    return path


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def repository_root(root):
    root = Path(root).resolve(strict=True)
    actual = Path(os.fsdecode(git(root, "rev-parse", "--show-toplevel")).strip()).resolve()
    if root != actual:
        raise ValueError("--root must name the repository root")
    return root


def outside(path, root):
    path = Path(path).absolute()
    if path.resolve().is_relative_to(root):
        raise ValueError("Archive and restoration destinations must be outside the repository")
    return path


def inventory(root, selected, hashes=True):
    """Use lstat throughout: links and special files are never followed."""
    directories, files = [], []

    def visit(path):
        info = path.lstat()
        name = path.relative_to(root).as_posix()
        relative_path(name)
        entry = {"path": name, "mode": stat.S_IMODE(info.st_mode)}
        if stat.S_ISDIR(info.st_mode):
            directories.append(entry)
            for child in sorted(path.iterdir()):
                visit(child)
        elif stat.S_ISREG(info.st_mode):
            entry["size"] = info.st_size
            if hashes:
                entry["sha256"] = file_digest(path)
                after = path.lstat()
                if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
                    info.st_ctime_ns, info.st_mode) != (
                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
                    after.st_ctime_ns, after.st_mode
                ):
                    raise ValueError(f"Source changed while hashing: {name}")
            files.append(entry)
        else:
            raise ValueError(f"Symlink or special file refused: {name}")

    for name in selected:
        relative_path(name)
        path = root / name
        # A symlink in an ancestor is also unsafe, even if this leaf is regular.
        if path.resolve() != path.absolute():
            raise ValueError(f"Symlink in source path: {name}")
        if not stat.S_ISDIR(path.lstat().st_mode):
            raise ValueError(f"Select a directory: {name}")
        visit(path)
    return {"directories": directories, "files": files}


def eligible(root, snapshot, allow_tracked):
    directories = {entry["path"] for entry in snapshot["directories"]}
    selected = {name for name in directories if str(PurePosixPath(name).parent) not in directories}
    tracked = {os.fsdecode(name) for name in git(root, "ls-files", "-z").split(b"\0") if name}
    dirty = {os.fsdecode(name) for name in git(root, "diff", "HEAD", "--name-only", "-z").split(b"\0") if name}
    untracked = {os.fsdecode(name) for name in git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if name}
    protected = dirty | untracked | (set() if allow_tracked else tracked)
    rejected = {name for name in protected if any(name == item or name.startswith(item + "/") for item in selected)}
    if rejected:
        raise ValueError(f"Tracked, dirty, or nonignored source refused: {min(rejected)}")


def load_manifest(path):
    path = Path(path).resolve(strict=True)
    manifest = json.loads(path.read_text())
    if manifest.get("format") != FORMAT:
        raise ValueError("Unrecognized archive manifest")
    selected = manifest["selected_directories"]
    if not selected or selected != sorted(set(selected)):
        raise ValueError("Invalid selected directories")
    for name in selected:
        relative_path(name)
        if any(name != other and name.startswith(other + "/") for other in selected):
            raise ValueError("Selected directories overlap")
    entries = manifest["directories"] + manifest["files"]
    names = set()
    for entry in entries:
        name = entry["path"]
        relative_path(name)
        if name in names or not any(name == item or name.startswith(item + "/") for item in selected):
            raise ValueError(f"Duplicate or out-of-scope manifest path: {name}")
        names.add(name)
        if not isinstance(entry["mode"], int) or not 0 <= entry["mode"] <= 0o7777:
            raise ValueError(f"Invalid mode: {name}")
    directory_names = {entry["path"] for entry in manifest["directories"]}
    if not set(selected) <= directory_names:
        raise ValueError("Missing selected directory entries")
    for name in names:
        parent = str(PurePosixPath(name).parent)
        if name not in selected and parent not in directory_names:
            raise ValueError(f"Missing parent directory: {name}")
    for entry in manifest["files"]:
        if (not isinstance(entry["size"], int) or entry["size"] < 0
                or len(entry["sha256"]) != 64
                or any(ch not in "0123456789abcdef" for ch in entry["sha256"])):
            raise ValueError(f"Invalid file metadata: {entry['path']}")
    archive = path.parent / manifest["archive_file"]
    if archive.name != manifest["archive_file"]:
        raise ValueError("Archive filename must be a basename")
    outside(archive, Path(manifest["source_root"]))
    return manifest, archive


def walk_archive(archive, manifest, destination=None):
    """Check every member; optionally write regular files without tar.extractall."""
    if file_digest(archive) != manifest["archive_sha256"]:
        raise ValueError("Archive SHA-256 differs from manifest")
    directories = {entry["path"]: entry for entry in manifest["directories"]}
    files = {entry["path"]: entry for entry in manifest["files"]}
    seen = set()
    with tarfile.open(archive, "r|gz") as bundle:
        for member in bundle:
            name = member.name
            relative_path(name)
            if name in seen:
                raise ValueError(f"Duplicate archive member: {name}")
            seen.add(name)
            if name in directories and member.isdir():
                entry = directories[name]
                if destination is not None:
                    (destination / name).mkdir(parents=True, exist_ok=True)
            elif name in files and member.isfile():
                entry = files[name]
                if member.size != entry["size"]:
                    raise ValueError(f"Archive file size mismatch: {name}")
                stream = bundle.extractfile(member)
                result = hashlib.sha256()
                output = None
                try:
                    if destination is not None:
                        target = destination / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        output = target.open("xb")
                    while chunk := stream.read(CHUNK):
                        result.update(chunk)
                        if output is not None:
                            output.write(chunk)
                finally:
                    stream.close()
                    if output is not None:
                        output.close()
                if result.hexdigest() != entry["sha256"]:
                    raise ValueError(f"Archive file hash mismatch: {name}")
                if destination is not None:
                    (destination / name).chmod(entry["mode"])
            else:
                raise ValueError(f"Unexpected or unsafe archive member: {name}")
            if member.mode != entry["mode"]:
                raise ValueError(f"Archive mode mismatch: {name}")
    if seen != set(directories) | set(files):
        raise ValueError("Archive member set differs from manifest")
    if destination is not None:
        for entry in sorted(directories.values(), key=lambda item: item["path"].count("/"), reverse=True):
            (destination / entry["path"]).chmod(entry["mode"])
        if inventory(destination, manifest["selected_directories"]) != {
            "directories": manifest["directories"], "files": manifest["files"]
        }:
            raise ValueError("Restored tree differs from manifest")


def restore(manifest_path, destination):
    manifest, archive = load_manifest(manifest_path)
    destination = outside(destination, Path(manifest["source_root"]))
    destination.mkdir()  # Existing targets are refused, including empty ones.
    walk_archive(archive, manifest, destination)
    return destination


def write_tar(stream, root, snapshot):
    with tarfile.open(fileobj=stream, mode="w|", format=tarfile.PAX_FORMAT) as bundle:
        for entry in snapshot["directories"] + snapshot["files"]:
            info = tarfile.TarInfo(entry["path"])
            info.mode = entry["mode"]
            if "size" not in entry:
                info.type = tarfile.DIRTYPE
                bundle.addfile(info)
            else:
                info.size = entry["size"]
                with (root / entry["path"]).open("rb") as source:
                    bundle.addfile(info, source)


def create(root, selected, destination, allow_tracked=False, pigz=False):
    root = repository_root(root)
    selected = sorted(selected)
    if not selected or len(set(selected)) != len(selected) or any(
        name != other and name.startswith(other + "/") for name in selected for other in selected
    ):
        raise ValueError("Select unique, nonoverlapping directories")
    archive = outside(destination, root)
    manifest_path = Path(str(archive) + ".manifest.json")
    if archive.exists() or archive.is_symlink() or manifest_path.exists() or manifest_path.is_symlink():
        raise ValueError("Archive or companion manifest already exists")
    compressor = shutil.which("pigz") if pigz else None
    if pigz and not compressor:
        raise ValueError("--pigz requested but pigz is not installed")
    snapshot = inventory(root, selected)
    eligible(root, snapshot, allow_tracked)
    manifest = {
        "format": FORMAT, "created_utc": now(), "source_root": str(root),
        "source_head": os.fsdecode(git(root, "rev-parse", "HEAD")).strip(),
        "selected_directories": selected, "allow_tracked": allow_tracked,
        "archive_file": archive.name,
        "compression": "pigz level 1, two threads" if pigz else "gzip level 1", **snapshot,
    }
    with archive.open("xb") as raw:
        if compressor:
            process = subprocess.Popen([compressor, "-1", "-p", "2", "-c"], stdin=subprocess.PIPE, stdout=raw)
            try:
                with process.stdin:
                    write_tar(process.stdin, root, snapshot)
                if process.wait() != 0:
                    raise ValueError("pigz compression failed")
            except BaseException:
                process.kill()
                process.wait()
                raise
        else:
            with gzip.GzipFile(filename="", mode="wb", compresslevel=1, fileobj=raw) as compressed:
                write_tar(compressed, root, snapshot)
    manifest["archive_sha256"] = file_digest(archive)
    walk_archive(archive, manifest)
    manifest["archive_contents_verified_utc"] = now()
    with tempfile.TemporaryDirectory(prefix="moonboard-evidence-restore-", dir=archive.parent) as temp:
        walk_archive(archive, manifest, Path(temp))
    manifest["restored_tree_verified_utc"] = now()
    if inventory(root, selected) != snapshot:
        raise ValueError("Source tree changed during archival; pruning is forbidden")
    with manifest_path.open("x") as output:
        json.dump(manifest, output, indent=2)
        output.write("\n")
    return manifest_path


def prune(root, manifest_path):
    root = repository_root(root)
    manifest, archive = load_manifest(manifest_path)
    if str(root) != manifest["source_root"]:
        raise ValueError("Repository root differs from manifest")
    if not manifest.get("restored_tree_verified_utc") or not manifest.get("archive_contents_verified_utc"):
        raise ValueError("Archive has no completed restoration verification")
    walk_archive(archive, manifest)
    expected = {"directories": manifest["directories"], "files": manifest["files"]}
    current = inventory(root, manifest["selected_directories"])
    if current != expected:
        raise ValueError("Source tree changed; no files pruned")
    eligible(root, current, manifest["allow_tracked"])
    for entry in manifest["files"]:
        path = root / entry["path"]
        info = path.lstat()
        if (path.resolve() != path.absolute() or not stat.S_ISREG(info.st_mode) or info.st_size != entry["size"]
                or stat.S_IMODE(info.st_mode) != entry["mode"] or file_digest(path) != entry["sha256"]):
            raise ValueError(f"Source changed during pruning: {entry['path']}")
        after = path.lstat()
        if (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns) != (
            after.st_dev, after.st_ino, after.st_mtime_ns, after.st_ctime_ns
        ):
            raise ValueError(f"Source changed during pruning: {entry['path']}")
        path.unlink()
    # New files are preserved: rmdir refuses to remove any nonempty directory.
    for entry in sorted(manifest["directories"], key=lambda item: item["path"].count("/"), reverse=True):
        (root / entry["path"]).rmdir()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("create", help="Create, verify and test-restore an external archive")
    make.add_argument("--root", required=True, type=Path)
    make.add_argument("--destination", required=True, type=Path)
    make.add_argument("--allow-tracked", action="store_true", help="Also archive clean tracked files; dirty/nonignored files remain refused")
    make.add_argument("--pigz", action="store_true", help="Use installed pigz at level 1 with two compression threads")
    make.add_argument("directories", nargs="+")
    check = commands.add_parser("verify", help="Verify archive member set, modes and all hashes")
    check.add_argument("--manifest", required=True, type=Path)
    unpack = commands.add_parser("restore", help="Restore into a fresh external directory and verify bytes")
    unpack.add_argument("--manifest", required=True, type=Path)
    unpack.add_argument("--destination", required=True, type=Path)
    remove = commands.add_parser("prune", help="Verify archive and unchanged source before pruning selected trees")
    remove.add_argument("--root", required=True, type=Path)
    remove.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "create":
            print(create(args.root, args.directories, args.destination, args.allow_tracked, args.pigz))
        elif args.command == "verify":
            manifest, archive = load_manifest(args.manifest)
            walk_archive(archive, manifest)
            print(f"Verified {len(manifest['files'])} files: {archive}")
        elif args.command == "restore":
            print(restore(args.manifest, args.destination))
        else:
            prune(args.root, args.manifest)
            print(f"Pruned unchanged archived trees from {args.root}")
    except (OSError, ValueError, tarfile.TarError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Archive operation refused: {error}\n")


if __name__ == "__main__":
    main()
