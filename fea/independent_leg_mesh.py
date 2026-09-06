"""Bounded matched mesh of the actual drilled foot100 right leg; no solver."""
import argparse
import hashlib
import json
import math
import os
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

from fea.floor_contact import FACES, integrated_weights, mesh

ROOT = Path("fea/generated/independent-leg-profile")
IMAGE = "mini-moonboard-fea:box-v1"
LIMITS = "Geometry/mesh preparation only. Full cylindrical bore surfaces are available for ideal fixed fixtures, and full floor faces for distributed reversed loading. These are not loose-bolt engagement or unilateral floor contact. No material properties, capacity, interface ties, or load-sharing assumptions assigned."


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def prepare():
    global ROOT
    import cadquery as cq

    from mini_moonboard import footprint_frame as frame

    leg = next(p.shape for p in frame.parts(100, drilled=True) if p.name == "leg_right")
    bounds = leg.BoundingBox()
    split = (bounds.xmin + bounds.xmax) / 2
    if abs(bounds.xlen - 38.1) > 1e-5 or abs(split - 1276.35) > 1e-5:
        raise ValueError("Unexpected actual right-leg thickness/location")
    ROOT = Path(tempfile.mkdtemp(prefix="independent-leg-profile-", dir="fea/generated")).relative_to(Path.cwd())
    parts = {}
    for name, x0 in (("inner", bounds.xmin), ("outer", split)):
        clip = cq.Solid.makeBox(19.05, bounds.ylen + 2, bounds.zlen + 2,
                                cq.Vector(x0, bounds.ymin - 1, bounds.zmin - 1))
        ply = leg.intersect(clip)
        if not ply.isValid() or len(ply.Solids()) != 1 or abs(ply.Volume() / leg.Volume() - .5) > 1e-8:
            raise ValueError("Invalid half-leg solid")
        floors = [f for f in ply.Faces() if abs(f.BoundingBox().zmin) < 1e-5 and abs(f.BoundingBox().zmax) < 1e-5]
        if len(floors) != 1:
            raise ValueError("Expected one complete CAD floor face per ply")
        cq.exporters.export(ply, str(ROOT / f"{name}.step"))
        parts[name] = {"volume_mm3": ply.Volume(), "floor_area_mm2": floors[0].Area(),
                       "floor_centroid_mm": floors[0].Center().toTuple(), "x_interval_mm": [x0, x0 + 19.05]}
    bolts = [c for c in frame.connections() if "leg_right" in c.members]
    if len(bolts) != 4:
        raise ValueError("Expected four actual bolt locations")
    info = {"candidate": "foot100-independent-plies-right", "limits": LIMITS, "parts": parts,
            "split_x_mm": split, "cad_volume_mm3": leg.Volume(), "bore_radius_mm": 5,
            "bores_yz_mm": [[c.start.y, c.start.z] for c in bolts],
            "geometry_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "cadquery_version": cq.__version__,
            "source_sha256": {str(p): digest(p) for p in sorted(Path("mini_moonboard").glob("*.py"))},
            "step_sha256": {f"{n}.step": digest(ROOT / f"{n}.step") for n in parts},
            "acceptance": {"relative_volume_error_max": .001, "floor_area_relative_error_max": 1e-6,
                           "floor_centroid_error_mm_max": 1e-5, "sampled_jacobian_min_exclusive": 0}}
    save(ROOT / "input.json", info)
    print(ROOT, flush=True)


def floor_selection(nodes, elements, owners, info):
    """Complete quadratic floor patches, with exact planar consistent weights."""
    result = {}
    for name, tags in owners.items():
        faces, weights = [], {}
        for e in tags:
            for face, indices in enumerate(FACES, 1):
                ids = [elements[e][i] for i in indices]
                if not all(abs(nodes[n][2]) < 1e-5 for n in ids):
                    continue
                faces.append([e, face])
                a, b, c = [nodes[n] for n in ids[:3]]
                for middle, p, q in zip(ids[3:], (a, b, c), (b, c, a), strict=True):
                    if math.dist(nodes[middle], tuple((u + v) / 2 for u, v in zip(p, q))) > 1e-5:
                        raise ValueError("Floor triangle is not affine; quadratic quadrature required")
                area = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) / 2
                for n in ids:
                    weights.setdefault(n, 0.)
                for n in ids[3:]:
                    weights[n] += area / 3
        expected_nodes = {n for e in tags for n in elements[e] if abs(nodes[n][2]) < 1e-5}
        if not faces or set(weights) != expected_nodes:
            raise ValueError("Incomplete floor patch")
        area = sum(weights.values())
        centroid = [sum(nodes[n][i] * w for n, w in weights.items()) / area for i in range(3)]
        cad = info["parts"][name]
        if abs(area / cad["floor_area_mm2"] - 1) > 1e-6 or math.dist(centroid, cad["floor_centroid_mm"]) > 1e-5:
            raise ValueError("Floor area/centroid differs from actual CAD")
        result[name] = {"faces": faces, "nodes": sorted(weights), "weights_mm2": weights,
                        "area_mm2": area, "centroid_mm": centroid}
    return result


def worker(directory, size):
    import gmsh

    directory = Path(directory)
    info = json.loads((ROOT / "input.json").read_text())
    if any(digest(ROOT / p) != h for p, h in info["step_sha256"].items()):
        raise ValueError("Frozen STEP changed")
    gmsh.initialize()
    gmsh.option.setNumber("General.Verbosity", 2)
    gmsh.model.add("actual_drilled_right_leg")
    names = ["inner", "outer"]
    volumes = []
    for name in names:
        imported = gmsh.model.occ.importShapes(str(ROOT / f"{name}.step"))
        if len(imported) != 1 or imported[0][0] != 3:
            raise ValueError("Expected one STEP solid per ply")
        if abs(gmsh.model.occ.getMass(*imported[0]) / info["parts"][name]["volume_mm3"] - 1) > 1e-7:
            raise ValueError("STEP volume mismatch")
        volumes.extend(imported)
    _, mapped = gmsh.model.occ.fragment(volumes[:1], volumes[1:])
    gmsh.model.occ.synchronize()
    if any(len(v) != 1 or v[0][0] != 3 for v in mapped) or len(gmsh.model.getEntities(3)) != 2:
        raise ValueError("Fragmentation changed ply volume inventory")
    gmsh.model.addPhysicalGroup(3, [tag for _, tag in gmsh.model.getEntities(3)], 1)
    gmsh.model.setPhysicalName(3, 1, "TIMBER")
    for option, value in {"Mesh.MeshSizeMax": size, "Mesh.MeshSizeMin": 2,
                          "Mesh.MeshSizeFromCurvature": 16, "Mesh.ElementOrder": 2}.items():
        gmsh.option.setNumber(option, value)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize("HighOrder")
    types, tags, _ = gmsh.model.mesh.getElements(3)
    if set(types) != {11}:
        raise ValueError("Expected only quadratic tetrahedra")
    qualities = [float(q) for ids in tags for q in gmsh.model.mesh.getElementQualities(ids, "minDetJac")]
    if not qualities or not all(math.isfinite(q) and q > 0 for q in qualities):
        raise ValueError("Nonpositive sampled quadratic Jacobian")
    owners, bores = {}, {}
    for name, entities in zip(names, mapped, strict=True):
        owners[name] = [int(e) for _, tag in entities for ids in gmsh.model.mesh.getElements(3, tag)[1] for e in ids]
        bores[name] = []
        surfaces = gmsh.model.getBoundary(entities, oriented=False)
        for y, z in info["bores_yz_mm"]:
            selected, area = set(), 0.
            for dim, tag in surfaces:
                if gmsh.model.getType(dim, tag) != "Cylinder":
                    continue
                box = gmsh.model.getBoundingBox(dim, tag)
                if abs((box[1] + box[4]) / 2 - y) > 1e-4 or abs((box[2] + box[5]) / 2 - z) > 1e-4:
                    continue
                ids, _, _ = gmsh.model.mesh.getNodes(dim, tag, includeBoundary=True)
                selected.update(map(int, ids))
                area += gmsh.model.occ.getMass(dim, tag)
            if len(selected) < 6 or abs(area / (2 * math.pi * 5 * 19.05) - 1) > 1e-6:
                raise ValueError("Incomplete actual cylindrical bore fixture")
            bores[name].append(sorted(selected))
    gmsh.write(str(directory / "mesh.inp"))
    version = gmsh.__version__
    gmsh.finalize()
    nodes, elements = mesh((directory / "mesh.inp").read_text())
    if set(owners["inner"]) & set(owners["outer"]) or {e for ids in owners.values() for e in ids} != set(elements):
        raise ValueError("Element ownership overlapping/incomplete")
    part_nodes = {name: sorted({n for e in ids for n in elements[e]}) for name, ids in owners.items()}
    shared = sorted(set(part_nodes["inner"]) & set(part_nodes["outer"]))
    if len(shared) < 6 or set(shared) != {n for n in nodes if abs(nodes[n][0] - info["split_x_mm"]) < 1e-5}:
        raise ValueError("Invalid conformal shared interface")
    floors = floor_selection(nodes, elements, owners, info)
    mesh_volumes = {}
    for name, ids in owners.items():
        subset = {e: elements[e] for e in ids}
        selected = {n: nodes[n] for n in part_nodes[name]}
        mesh_volumes[name] = sum(integrated_weights(subset, selected).values())
        if abs(mesh_volumes[name] / info["parts"][name]["volume_mm3"] - 1) > .001:
            raise ValueError("Integrated quadratic ply volume differs from CAD")
        for ids in bores[name]:
            if not set(ids) <= set(part_nodes[name]) or set(ids) & set(floors[name]["nodes"]):
                raise ValueError("Invalid bore ownership or floor overlap")
    save(directory / "mesh.json", {"status": "VERIFIED MESH ONLY; NO SOLVER", "limits": LIMITS,
         "mesh_size_mm": size, "gmsh_version": version, "node_count": len(nodes), "element_count": len(elements),
         "min_sampled_jacobian": min(qualities), "part_elements": owners, "part_nodes": part_nodes,
         "shared_interface_nodes": shared, "floor": floors, "bore_nodes": bores,
         "mesh_volumes_mm3": mesh_volumes, "mesh_sha256": digest(directory / "mesh.inp")})


def run(size):
    directory = ROOT / f"mesh{size:g}"
    directory.mkdir()
    source = Path(__file__)
    (directory / "independent_leg_mesh.launch.py").write_bytes(source.read_bytes())
    dependencies = (source, Path("fea/floor_contact.py"), ROOT / "input.json")
    sources = {str(p): digest(p) for p in dependencies}
    (directory / "floor_contact.launch.py").write_bytes(Path("fea/floor_contact.py").read_bytes())
    image = subprocess.check_output(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], text=True).strip()
    started = time.monotonic()
    with (directory / "worker.log").open("w") as log:
        result = subprocess.run(["docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}", "-e", "OMP_NUM_THREADS=2", "-v", f"{Path.cwd()}:/work",
                                 IMAGE, "timeout", "120", "python3", "-m", "fea.independent_leg_mesh", "--worker", str(directory),
                                 "--directory", str(ROOT), "--size", str(size)], stdout=log, stderr=subprocess.STDOUT, check=False)
    save(directory / "run.json", {"exit_code": result.returncode, "elapsed_seconds": time.monotonic() - started,
         "max_seconds": 120, "docker_image": IMAGE, "docker_image_id": image,
         "source_sha256": sources, "sources_unchanged": all(digest(p) == h for p, h in sources.items()),
         "worker_log_sha256": digest(directory / "worker.log")})
    if result.returncode:
        raise RuntimeError(f"Bounded mesh failed; inspect {directory}/worker.log")
    if any(digest(p) != h for p, h in sources.items()):
        raise RuntimeError("Launched source changed during mesh preparation")


def replay_archive(path):
    """Verify saved topology/selections/provenance without CAD, Gmsh, or solver."""
    with tarfile.open(path, "r:gz") as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
    manifest = json.loads(files["manifest.json"])
    if set(manifest) != set(files) - {"manifest.json"} or any(
            hashlib.sha256(files[name]).hexdigest() != expected for name, expected in manifest.items()):
        raise ValueError("Archive inventory/digest mismatch")
    info = json.loads(files["input.json"])
    for name, expected in {**info["step_sha256"], **info["source_sha256"]}.items():
        if hashlib.sha256(files[name]).hexdigest() != expected:
            raise ValueError("CAD/STEP source digest mismatch")
    if abs(info["cad_volume_mm3"] - 13122254.26617948) > .01 or abs(info["split_x_mm"] - 1276.35) > 1e-5:
        raise ValueError("Wrong actual drilled right-leg geometry")
    result = {}
    for size in (40, 25):
        prefix = f"mesh{size}/"
        record = json.loads(files[prefix + "run.json"])
        data = json.loads(files[prefix + "mesh.json"])
        if record["exit_code"] != 0 or not record["sources_unchanged"] or record["elapsed_seconds"] >= 120:
            raise ValueError("Mesh worker did not finish successfully within cap")
        for original, expected in record["source_sha256"].items():
            name = Path(original).name
            archived = "input.json" if name == "input.json" else prefix + name.replace(".py", ".launch.py")
            if hashlib.sha256(files[archived]).hexdigest() != expected:
                raise ValueError("Launch source snapshot differs from recorded hash")
        if (hashlib.sha256(files[prefix + "mesh.inp"]).hexdigest() != data["mesh_sha256"]
                or hashlib.sha256(files[prefix + "worker.log"]).hexdigest() != record["worker_log_sha256"]):
            raise ValueError("Raw mesh/log differs from recorded hash")
        nodes, elements = mesh(files[prefix + "mesh.inp"].decode())
        owners = data["part_elements"]
        if set(owners) != {"inner", "outer"} or not all(owners.values()):
            raise ValueError("Missing ply ownership")
        flattened = [e for ids in owners.values() for e in ids]
        if len(flattened) != len(set(flattened)) or set(flattened) != set(elements):
            raise ValueError("Element ownership overlapping/incomplete")
        part_nodes = {name: sorted({n for e in ids for n in elements[e]}) for name, ids in owners.items()}
        if part_nodes != data["part_nodes"] or set(nodes) != set(part_nodes["inner"]) | set(part_nodes["outer"]):
            raise ValueError("Recorded ply nodes differ from elements")
        shared = set(part_nodes["inner"]) & set(part_nodes["outer"])
        if (len(shared) < 6 or shared != set(data["shared_interface_nodes"])
                or shared != {n for n in nodes if abs(nodes[n][0] - info["split_x_mm"]) < 1e-5}):
            raise ValueError("Incomplete conformal interface")
        floors = floor_selection(nodes, elements, owners, info)
        if json.loads(json.dumps(floors)) != data["floor"]:
            raise ValueError("Archived floor selections differ from mesh")
        for name, ids in part_nodes.items():
            cad = info["parts"][name]
            if abs(cad["floor_area_mm2"] - 3670.2881245686) > 1e-5 or abs(cad["volume_mm3"] - 6561127.13308975) > .01:
                raise ValueError("Wrong half-leg CAD floor/volume")
            if abs(data["mesh_volumes_mm3"][name] / cad["volume_mm3"] - 1) > .001:
                raise ValueError("Recorded integrated mesh volume differs from CAD")
            if len(data["bore_nodes"][name]) != 4:
                raise ValueError("Missing bore fixture")
            for (y, z), selected in zip(info["bores_yz_mm"], data["bore_nodes"][name], strict=True):
                expected = {n for n in ids if abs(math.hypot(nodes[n][1] - y, nodes[n][2] - z) - 5) < 1e-5}
                if len(expected) < 6 or set(selected) != expected or expected & set(floors[name]["nodes"]):
                    raise ValueError("Bore fixture differs from actual radial surface nodes")
                if any(not any(abs(nodes[n][0] - x) < 1e-5 for n in selected) for x in cad["x_interval_mm"]):
                    raise ValueError("Bore fixture does not reach both ply ends")
        if (data["node_count"] != len(nodes) or data["element_count"] != len(elements)
                or not math.isfinite(data["min_sampled_jacobian"]) or data["min_sampled_jacobian"] <= 0):
            raise ValueError("Invalid recorded mesh counts/quality")
        result[size] = data
    return result


def publish():
    destination = Path("fea/results/independent_leg_mesh")
    destination.mkdir()  # Existing publication is never overwritten.
    info = json.loads((ROOT / "input.json").read_text())
    entries = {name: ROOT / name for name in ("input.json", "inner.step", "outer.step")}
    for name, expected in info["source_sha256"].items():
        if digest(name) != expected:
            raise ValueError("CAD source changed since preparation; cannot archive current bytes")
        entries[name] = Path(name)
    for size in (40, 25):
        for name in ("mesh.inp", "mesh.json", "run.json", "worker.log",
                     "independent_leg_mesh.launch.py", "floor_contact.launch.py"):
            entries[f"mesh{size}/{name}"] = ROOT / f"mesh{size}" / name
    manifest = {name: digest(path) for name, path in entries.items()}
    save(destination / "manifest.json", manifest)
    archive_path = destination / "evidence.tar.gz"
    with tarfile.open(archive_path, "x:gz") as archive:
        for name, path in entries.items():
            archive.add(path, arcname=name)
        archive.add(destination / "manifest.json", arcname="manifest.json")
    replay_archive(archive_path)
    save(destination / "report.json", {"status": "TWO VERIFIED MATCHED MESHES; NO SOLVER OR CAPACITY",
         "archive_sha256": digest(archive_path), "prepared_directory": str(ROOT),
         "limits": LIMITS, "publisher_source_sha256": digest(__file__),
         "chronology": "Each worker launch source snapshot predates publication/replay additions. CAD source bytes copied at publication only after matching preparation hashes. Portable replay verifies recorded positive quality and volume, without recalculating Gmsh Jacobians or CAD geometry."})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--worker")
    parser.add_argument("--directory", type=Path, default=ROOT)
    parser.add_argument("--size", type=float, choices=(40., 25.), default=40.)
    args = parser.parse_args()
    ROOT = args.directory
    if args.prepare:
        prepare()
    elif args.publish:
        publish()
    elif args.worker:
        worker(args.worker, args.size)
    else:
        run(args.size)
