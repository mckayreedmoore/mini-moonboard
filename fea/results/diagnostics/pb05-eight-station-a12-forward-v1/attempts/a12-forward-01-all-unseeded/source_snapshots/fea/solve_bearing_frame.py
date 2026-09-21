"""Straight-sided quadratic bearing-frame bulk diagnostic, never joint approval."""
import argparse
import json
import math
import subprocess
import uuid
from pathlib import Path

from fea.floor_contact import mesh
from fea.solve_easy_frame import audit, digest, make_deck, target_mapping

DIRECTORY = Path("fea/generated/bearing-frame")
KEY = "bearing-lean-frame"
LIMITS = (
    "Optimistic isotropic bulk stiffness diagnostic only. Undrilled timber and "
    "all touching interfaces, including independent plywood leg plies, are ideally bonded. "
    "All floor nodes fixed XYZ; no gravity, separation, slip, actual bolt/screw/connector "
    "compliance, strengths, buckling or approval. Straight-sided C3D10 elements facet "
    "curved boundaries; gross volume agreement does not qualify local geometry/stress. "
    "Five equally loaded row-12 nodes: reported displacement is their maximum, not "
    "the whole-frame maximum or a single-hold result. Point-load and target-mapping "
    "mesh sensitivity precludes treating two mesh levels as general convergence proof."
)


def straight_mesh_volume(nodes, elements):
    """Independently integrate corner tetrahedra and verify every midside is linear."""
    if not nodes or not elements or any(len(p) != 3 or not all(map(math.isfinite, p)) for p in nodes.values()):
        raise ValueError("Finite nonempty three-dimensional mesh required")
    volumes = []
    maximum_midpoint_error = 0.
    edges = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
    for tag, ids in elements.items():
        if len(ids) != 10 or len(set(ids)) != 10 or not set(ids) <= nodes.keys():
            raise ValueError(f"Invalid C3D10 connectivity: {tag}")
        points = [nodes[n] for n in ids]
        a, z, c = [tuple(points[i][j]-points[0][j] for j in range(3)) for i in (1, 2, 3)]
        cross = (z[1]*c[2]-z[2]*c[1], z[2]*c[0]-z[0]*c[2], z[0]*c[1]-z[1]*c[0])
        determinant = sum(a[i]*cross[i] for i in range(3))
        if not math.isfinite(determinant) or determinant <= 0:
            raise ValueError(f"Nonpositive independent corner Jacobian: {tag}")
        volumes.append(determinant/6)
        for index, (i, j) in enumerate(edges, 4):
            midpoint = tuple((points[i][k]+points[j][k])/2 for k in range(3))
            error = math.dist(points[index], midpoint)
            maximum_midpoint_error = max(maximum_midpoint_error, error)
            if error > 1e-6:
                raise ValueError(f"Quadratic element is not straight-sided: {tag}")
    return math.fsum(volumes), maximum_midpoint_error


def run(size, modulus=7000.):
    if size not in (60., 40.) or not math.isfinite(modulus) or modulus <= 0:
        raise ValueError("Require mesh size 60/40 mm and positive finite modulus")
    import gmsh

    info_path = DIRECTORY/"box_frame_bulk.json"
    info = json.loads(info_path.read_text())
    step = DIRECTORY/"box_frame_bulk.step"
    if info["candidate"] != KEY or digest(step) != info["step_sha256"]:
        raise ValueError("Frozen candidate/STEP identity differs")
    sources = dict(info["geometry_source_sha256"])
    if not sources:
        raise ValueError("Missing frozen geometry source closure")
    for name in ("fea/solve_bearing_frame.py", "fea/solve_easy_frame.py", "fea/box_results.py",
                 "fea/floor_contact.py", "fea/floor_contact_results.py", "fea/hybrid_results.py"):
        sources.setdefault(name, digest(name))
    if any(digest(name) != sha for name, sha in sources.items()):
        raise ValueError("Frozen source differs")
    prefix = DIRECTORY/f"bearing_audited_{size:g}_{modulus:g}_{uuid.uuid4().hex}".replace(".", "p")
    context = prefix.with_suffix(".context.json")
    settings = {"Mesh.MeshSizeMax": size, "Mesh.MeshSizeMin": size/5,
                "Mesh.MeshSizeFromCurvature": 0, "Mesh.ElementOrder": 2,
                "Mesh.SecondOrderLinear": 1}
    launch = {"input_sha256": digest(info_path), "source_sha256": sources,
              "limits": LIMITS, "candidate": KEY, "size_mm": size,
              "modulus_mpa": modulus, "mesh_settings": settings,
              "high_order_optimizer_used": False}
    with context.open("x") as stream:
        json.dump(launch, stream, indent=2, allow_nan=False)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Verbosity", 2)
        gmsh.model.add(KEY)
        shapes = gmsh.model.occ.importShapes(str(step))
        if len(shapes) < 2 or any(dim != 3 for dim, _ in shapes):
            raise ValueError("Expected multi-solid timber STEP")
        gmsh.model.occ.fragment(shapes[:1], shapes[1:])
        gmsh.model.occ.synchronize()
        volumes = [tag for _, tag in gmsh.model.getEntities(3)]
        cad_volumes = [gmsh.model.occ.getMass(3, tag) for tag in volumes]
        if not cad_volumes or any(not math.isfinite(v) or v <= 0 for v in cad_volumes):
            raise ValueError("Invalid fragmented CAD volume")
        cad_volume = math.fsum(cad_volumes)
        if not math.isclose(cad_volume, info["cad_unfragmented_volume_mm3"], rel_tol=1e-6):
            raise ValueError("Fragmented CAD volume differs from frozen source solids")
        gmsh.model.addPhysicalGroup(3, volumes, 1)
        gmsh.model.setPhysicalName(3, 1, "TIMBER")
        for name, value in settings.items():
            gmsh.option.setNumber(name, value)
        gmsh.model.mesh.generate(3)
        qualities = [float(q) for tags in gmsh.model.mesh.getElements(3)[1]
                     for q in gmsh.model.mesh.getElementQualities(tags, "minDetJac")]
        if not qualities or not all(map(math.isfinite, qualities)) or min(qualities) <= 0:
            raise ValueError("Invalid quadratic Jacobian")
        gmsh.write(str(prefix.with_suffix(".inp")))
        version = gmsh.__version__
    finally:
        gmsh.finalize()
    mesh_text = prefix.with_suffix(".inp").read_text()
    nodes, elements = mesh(mesh_text)
    mesh_volume, midpoint_error = straight_mesh_volume(nodes, elements)
    volume_relative_error = abs(mesh_volume-cad_volume)/cad_volume
    if volume_relative_error > .005:
        raise ValueError(f"Straight mesh differs from CAD volume by more than 0.5%: {volume_relative_error}")
    if len(qualities) != len(elements):
        raise ValueError("Quality coverage differs from parsed C3D10 inventory")
    parent = {n: n for n in nodes}

    def root(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    for ids in elements.values():
        for n in ids[1:]:
            parent[root(n)] = root(ids[0])
    if len({root(n) for n in nodes}) != 1:
        raise ValueError("Ideal-bonded timber mesh is disconnected")
    feet = sorted(n for n, p in nodes.items() if abs(p[2]) < 1e-5)
    targets = info["audited_load_targets_mm"]
    mapping = target_mapping(nodes, targets, size)
    top = sorted(row["node"] for row in mapping)
    if len(targets) != 5 or len(top) != 5 or not feet or set(top) & set(feet):
        raise ValueError("Invalid load/support selection")
    text = "** "+LIMITS+"\n"+make_deck(mesh_text, feet, top, info["audited_cases"], modulus)
    prefix.with_suffix(".inp").write_text(text)
    deck_sha = digest(prefix.with_suffix(".inp"))
    launch.update(deck_sha256=deck_sha, load_nodes=top, floor_node_count=len(feet),
                  gmsh_version=version, min_jacobian=min(qualities),
                  nodes=len(nodes), elements=len(elements), cad_volume_mm3=cad_volume,
                  mesh_volume_mm3=mesh_volume, volume_relative_error=volume_relative_error,
                  maximum_midpoint_error_mm=midpoint_error)
    context.write_text(json.dumps(launch, indent=2, allow_nan=False)+"\n")
    with prefix.with_suffix(".log").open("x") as stream:
        result = subprocess.run(["ccx", "-i", prefix.name], cwd=DIRECTORY,
                                stdout=stream, stderr=subprocess.STDOUT, check=False)
    if result.returncode or "*ERROR" in prefix.with_suffix(".log").read_text().upper():
        raise ValueError("CalculiX failed; outputs retained")
    if (digest(prefix.with_suffix(".inp")) != deck_sha or digest(step) != info["step_sha256"]
            or digest(info_path) != launch["input_sha256"]):
        raise ValueError("Frozen solver input changed")
    if any(digest(name) != sha for name, sha in sources.items()):
        raise ValueError("Source changed during run")
    summary = {**launch, "mesh_size_mm": size, "geometry_commit": info["geometry_commit"],
               "frozen_geometry": info, "load_target_mapping": mapping,
               "load_target_distances_mm": [row["distance_mm"] for row in mapping],
               **audit(text, prefix.with_suffix(".dat").read_text(), info)}
    summary["evidence_sha256"] = {p.name: digest(p) for p in DIRECTORY.glob(prefix.name+".*")}
    with prefix.with_suffix(".json").open("x") as stream:
        stream.write(json.dumps(summary, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"result": str(prefix.with_suffix(".json")), "candidate": KEY,
                      "nodes": len(nodes), "max_top_displacement_mm": summary["max_top_displacement_mm"]}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=float, choices=(60., 40.), required=True)
    parser.add_argument("--modulus", type=float, default=7000.)
    args = parser.parse_args()
    if not math.isfinite(args.modulus) or args.modulus <= 0:
        parser.error("Modulus must be positive finite")
    run(args.size, args.modulus)


if __name__ == "__main__":
    main()
