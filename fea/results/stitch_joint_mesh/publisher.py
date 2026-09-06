"""Publish/replay frozen stitch geometry and mesh evidence, without CAD or solver."""
import argparse
import hashlib
import io
import json
import math
import re
import tarfile
from pathlib import Path, PurePosixPath

BODY_NAMES = {"leg_right_inner", "leg_right_outer"} | {
    f"leg_stitch_right_{i}_{role}" for i in (1, 2, 3)
    for role in ("bolt", "nut", "washer_inner", "washer_outer")}
FACE_NODES = ((0, 1, 2, 4, 5, 6), (0, 3, 1, 7, 8, 4),
              (1, 3, 2, 8, 9, 5), (2, 3, 0, 9, 7, 6))
LIMITS = ("Geometry and mesh evidence only. No materials, interface laws, ties, "
          "supports, preload, friction, response, strength or capacity verified. "
          "Portable replay checks topology, recorded quality/volume gates and provenance; "
          "it does not recalculate CAD geometry or quadratic Jacobians.")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mesh(text):
    """Independent strict parser: only the actual mesh's heading/node/element cards."""
    nodes, elements, sets = {}, {}, {}
    mode, owner = None, None
    for line in text.splitlines():
        if not line.strip() or line.startswith("**"):
            continue
        if line.startswith("*"):
            if line == "*HEADING":
                mode = "heading"
            elif line == "*NODE":
                mode = "node"
            elif re.fullmatch(r"\*ELEMENT,TYPE=C3D10,ELSET=[A-Z0-9_]+", line):
                owner = line.split("ELSET=")[1].lower()
                if owner in sets:
                    raise ValueError("Duplicate element ownership card")
                sets[owner] = []
                mode = "element"
            else:
                raise ValueError("Unexpected mesh directive; no solver cards permitted")
            continue
        cells = line.split(",")
        if mode == "node":
            if len(cells) != 4:
                raise ValueError("Malformed node")
            tag, xyz = int(cells[0]), tuple(map(float, cells[1:]))
            if tag <= 0 or tag in nodes or not all(map(math.isfinite, xyz)):
                raise ValueError("Duplicate or invalid node")
            nodes[tag] = xyz
        elif mode == "element":
            if len(cells) != 11:
                raise ValueError("Malformed C3D10")
            tag, ns = int(cells[0]), tuple(map(int, cells[1:]))
            if tag <= 0 or tag in elements or len(set(ns)) != 10:
                raise ValueError("Duplicate or invalid element")
            elements[tag] = ns
            sets[owner].append(tag)
        elif mode != "heading":
            raise ValueError("Mesh data outside a supported card")
    if not nodes or not elements or {n for ns in elements.values() for n in ns} != set(nodes):
        raise ValueError("Mesh node references are incomplete")
    return nodes, elements, sets


def edge_map(ns):
    return {tuple(sorted((ns[a], ns[b]))): ns[c]
            for a, b, c in ((0, 1, 3), (1, 2, 4), (2, 0, 5))}


def topology(nodes, elements, sets, record, geometry):
    if set(sets) != BODY_NAMES or set(record["bodies"]) != BODY_NAMES:
        raise ValueError("Incorrect fourteen-body inventory")
    seen, maximum_volume_error, minimum_quality, surface_count = set(), 0., math.inf, 0
    for name in sorted(BODY_NAMES):
        body, cad = record["bodies"][name], geometry["parts"][name]
        ids, actual_nodes = sets[name], {n for e in sets[name] for n in elements[e]}
        if (not ids or len(body["elements"]) != len(set(body["elements"]))
                or set(body["elements"]) != set(ids) or len(body["nodes"]) != len(set(body["nodes"]))
                or set(body["nodes"]) != actual_nodes or seen & actual_nodes):
            raise ValueError("Body ownership differs from disjoint actual mesh")
        seen.update(actual_nodes)
        exterior = {}
        for e in ids:
            for face, indices in enumerate(FACE_NODES, 1):
                ns = tuple(elements[e][i] for i in indices)
                exterior.setdefault(tuple(sorted(ns[:3])), []).append((e, face, ns))
        boundary = {}
        for members in exterior.values():
            if len(members) == 1:
                e, face, ns = members[0]
                boundary[e, face] = ns
            elif len(members) != 2 or edge_map(members[0][2]) != edge_map(members[1][2]):
                raise ValueError("Nonmanifold or inconsistent quadratic interior")
        covered = set()
        if not body["surfaces"]:
            raise ValueError("Missing exterior surface groups")
        for surface in body["surfaces"].values():
            pairs = [tuple(pair) for pair in surface["faces"]]
            keys = set(pairs)
            if (not pairs or len(pairs) != len(keys) or covered & keys
                    or not keys <= boundary.keys()):
                raise ValueError("Surface faces are duplicate, interior or unknown")
            selected = {n for pair in pairs for n in boundary[pair]}
            if len(surface["nodes"]) != len(set(surface["nodes"])) or set(surface["nodes"]) != selected:
                raise ValueError("Quadratic surface node selection differs from actual mesh")
            bounds, area = surface["cad_bounds_mm"], surface["cad_area_mm2"]
            if (surface["cad_type"] not in ("Plane", "Cylinder") or len(bounds) != 6
                    or not all(map(math.isfinite, bounds)) or any(bounds[i] > bounds[i+3] for i in range(3))
                    or not math.isfinite(area) or area <= 0):
                raise ValueError("Invalid recorded CAD surface metadata")
            # OCC bounds include their own small tolerance; all TRI6 nodes belong to the face.
            if any(not bounds[i] - 1e-5 <= nodes[n][i] <= bounds[i+3] + 1e-5 for n in selected for i in range(3)):
                raise ValueError("Surface nodes exceed recorded CAD bounds")
            covered.update(keys)
            surface_count += 1
        if covered != set(boundary):
            raise ValueError("Surface groups do not cover the complete quadratic exterior")
        if body["cad_volume_mm3"] != cad["volume_mm3"] or cad["volume_mm3"] <= 0:
            raise ValueError("Body CAD volume differs from geometry record")
        relative = abs(body["mesh_volume_mm3"] / cad["volume_mm3"] - 1)
        values = (relative, body["min_sampled_jacobian"], body["min_integration_jacobian"], body["target_mesh_size_mm"])
        if not all(map(math.isfinite, values)) or relative > .001 or min(values[1:]) <= 0:
            raise ValueError("Recorded quadratic volume/Jacobian gate failed")
        expected_size = record["configuration"]["size_mm" if name.startswith("leg_right_") else "hardware_size_mm"]
        if body["target_mesh_size_mm"] != expected_size:
            raise ValueError("Body mesh size differs from frozen configuration")
        maximum_volume_error = max(maximum_volume_error, relative)
        minimum_quality = min(minimum_quality, body["min_sampled_jacobian"])
    if seen != set(nodes) or (record["node_count"], record["element_count"], record["body_count"]) != (len(nodes), len(elements), 14):
        raise ValueError("Recorded mesh counts differ from actual INP")
    return {"body_count": 14, "node_count": len(nodes), "element_count": len(elements),
            "cad_surface_count": surface_count, "shared_body_nodes": 0,
            "maximum_relative_volume_error": maximum_volume_error,
            "minimum_recorded_sampled_jacobian": minimum_quality}


def runtime(text):
    required = ("--network=none", "--memory=6g", "--memory-swap=6g", "--cpus=2", "--read-only",
                "timeout --signal=TERM --kill-after=10 120", "python3 -m fea.stitch_joint_mesh /evidence --size 40 --hardware-size 3")
    image = re.search(r"sha256:[0-9a-f]{64}", text)
    elapsed = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): ([\d:.]+)", text)
    exit_status = re.search(r"Exit status: (\d+)", text)
    if not image or not elapsed or not exit_status or exit_status[1] != "0" or any(s not in text for s in required):
        raise ValueError("Missing successful bounded immutable-image runtime evidence")
    seconds = 0.
    for component in elapsed[1].split(":"):
        seconds = seconds * 60 + float(component)
    if not 0 < seconds < 120:
        raise ValueError("Mesh run exceeded wall-time cap")
    return {"elapsed_seconds": seconds, "exit_code": 0, "docker_image_id": image[0],
            "max_seconds": 120, "memory_limit_gib": 6, "network": "none",
            "runtime_scope": "GNU time measures Docker client; its RSS is not container peak memory."}


def replay_files(files):
    """Validate hashes plus semantics; never execute archived source."""
    try:
        manifest = json.loads(files["manifest.json"])
        if set(manifest) != set(files) - {"manifest.json"} or any(sha(files[n]) != h for n, h in manifest.items()):
            raise ValueError("Archive inventory/digest mismatch")
        geometry, record = json.loads(files["geometry/geometry.json"]), json.loads(files["mesh/mesh.json"])
        expected = {"manifest.json", "publisher.py", "geometry/geometry.json", "mesh/mesh.inp", "mesh/mesh.json",
                    "runtime/mesh-worker.log", "runtime/mesh-runtime.txt", "runtime/mesh-postcheck.json"}
        expected |= {"geometry/" + n for n in geometry["step_sha256"]}
        expected |= {"geometry/launch_sources/" + n for n in geometry["source_sha256"]}
        expected |= {"mesh/" + n + ".snapshot" for n in record["source_sha256"]}
        if set(files) != expected:
            raise ValueError("Missing or extra publication files")
        if set(geometry["parts"]) != BODY_NAMES or set(geometry["step_sha256"]) != {n + ".step" for n in BODY_NAMES}:
            raise ValueError("Geometry body/STEP inventory differs")
        if (geometry["status"] != "VERIFIED GEOMETRY ONLY; NO MESH OR SOLVER"
                or geometry["source_binding"] != "before geometry through export"
                or record["status"] != "VERIFIED MESH ONLY; NO SOLVER"):
            raise ValueError("Geometry or mesh lacks successful frozen preparation")
        if (record["geometry_sha256"] != sha(files["geometry/geometry.json"])
                or record["step_sha256"] != geometry["step_sha256"]
                or record["mesh_sha256"] != sha(files["mesh/mesh.inp"])):
            raise ValueError("Mesh is not bound to archived geometry/STEP/input")
        for name, expected_hash in geometry["step_sha256"].items():
            if sha(files["geometry/" + name]) != expected_hash:
                raise ValueError("Frozen STEP hash mismatch")
        for name, expected_hash in geometry["source_sha256"].items():
            if sha(files["geometry/launch_sources/" + name]) != expected_hash:
                raise ValueError("Frozen geometry source hash mismatch")
        if set(record["source_sha256"]) != {"stitch_joint_mesh.py", "floor_contact.py"}:
            raise ValueError("Missing mesh preparation source provenance")
        for name, expected_hash in record["source_sha256"].items():
            if sha(files["mesh/" + name + ".snapshot"]) != expected_hash:
                raise ValueError("Frozen mesh source hash mismatch")
        if record["acceptance"] != {"relative_volume_error_max": .001, "minimum_jacobian_exclusive": 0, "shared_body_nodes": 0}:
            raise ValueError("Changed predeclared mesh gates")
        if record["configuration"] != {"size_mm": 40., "hardware_size_mm": 3.}:
            raise ValueError("Changed bounded mesh configuration")
        run = runtime(files["runtime/mesh-runtime.txt"].decode())
        postcheck = json.loads(files["runtime/mesh-postcheck.json"])
        container = postcheck["container_name"]
        if (postcheck["classification"] != "Post-hoc read-only inspection; not a prelaunch monitor record"
                or postcheck["mesh_session_exit_code"] != 0 or postcheck["named_container_absent"] is not True
                or postcheck["container_probe_command"] != ["docker", "inspect", "--format", "{{.State.Running}}", container]
                or postcheck["container_probe_exit_code"] != 1 or postcheck["container_probe_stdout"].strip()
                or postcheck["container_probe_stderr"].strip() != "error: no such object: " + container
                or postcheck["image_probe_command"] != ["docker", "image", "inspect", run["docker_image_id"], "--format", "{{.Id}}"]
                or postcheck["image_probe_exit_code"] != 0 or postcheck["image_probe_stdout"].strip() != run["docker_image_id"]
                or "--name " + container + " " not in files["runtime/mesh-runtime.txt"].decode()):
            raise ValueError("Post-hoc container/image evidence differs from bounded run")
        run["postcheck_classification"] = postcheck["classification"]
        run["named_container_absent"] = True
        log = files["runtime/mesh-worker.log"].decode()
        if not re.fullmatch(r"(/evidence/mesh-[a-z0-9_]+\n)\1", log):
            raise ValueError("Unexpected worker log")
        nodes, elements, sets = mesh(files["mesh/mesh.inp"].decode())
        return {**topology(nodes, elements, sets, record, geometry), "runtime": run}
    except (KeyError, TypeError, IndexError, OverflowError) as error:
        raise ValueError("Missing or malformed required publication metadata") from error


def archive_files(path):
    with tarfile.open(path, "r:gz") as archive:
        files = {}
        for member in archive.getmembers():
            name = PurePosixPath(member.name)
            if (not member.isfile() or member.name in files or name.is_absolute()
                    or ".." in name.parts or name.as_posix() != member.name):
                raise ValueError("Unsafe or duplicate archive entry")
            files[member.name] = archive.extractfile(member).read()
    return files


def replay_archive(path):
    return replay_files(archive_files(path))


def publish(geometry_directory, mesh_directory, destination):
    geometry_directory, mesh_directory, destination = map(Path, (geometry_directory, mesh_directory, destination))
    names = ["geometry.json", *sorted(p.name for p in geometry_directory.glob("*.step"))]
    files = {"geometry/" + n: (geometry_directory / n).read_bytes() for n in names}
    for path in sorted((geometry_directory / "launch_sources").rglob("*.py")):
        files["geometry/" + path.relative_to(geometry_directory).as_posix()] = path.read_bytes()
    for name in ("mesh.inp", "mesh.json", "stitch_joint_mesh.py.snapshot", "floor_contact.py.snapshot"):
        files["mesh/" + name] = (mesh_directory / name).read_bytes()
    for name in ("mesh-worker.log", "mesh-runtime.txt", "mesh-postcheck.json"):
        files["runtime/" + name] = (geometry_directory / name).read_bytes()
    files["publisher.py"] = Path(__file__).read_bytes()
    manifest = {name: sha(data) for name, data in sorted(files.items())}
    files["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    summary = replay_files(files)
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / "evidence.tar.gz"
    with tarfile.open(archive_path, "x:gz") as archive:
        for name, data in sorted(files.items()):
            member = tarfile.TarInfo(name)
            member.size = len(data)
            member.mode = 0o644
            archive.addfile(member, io.BytesIO(data))
    replayed = replay_archive(archive_path)
    if replayed != summary:
        raise ValueError("Written archive replay differs")
    with (destination / "manifest.json").open("xb") as output:
        output.write(files["manifest.json"])
    report = {"status": "VERIFIED ACTUAL STITCH GEOMETRY AND DISJOINT MESH; NO SOLVER",
              "limits": LIMITS, "archive_sha256": sha(archive_path.read_bytes()),
              "publisher_sha256": sha(files["publisher.py"]), "summary": summary,
              "prepared_geometry_directory": str(geometry_directory), "prepared_mesh_directory": str(mesh_directory)}
    with (destination / "report.json").open("x") as output:
        output.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geometry_directory", type=Path)
    parser.add_argument("mesh_directory", type=Path)
    parser.add_argument("--destination", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    print(json.dumps(publish(args.geometry_directory, args.mesh_directory, args.destination), indent=2))
