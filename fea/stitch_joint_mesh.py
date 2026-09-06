"""Prepare disjoint quadratic meshes of actual stitch geometry; no solver."""
import argparse
import hashlib
import json
import math
import tempfile
from pathlib import Path

from fea.floor_contact import FACES

LIMITS = "Mesh preparation only: no materials, contact laws, ties, restraints, preload or solver."
VOLUME_RELATIVE_TOLERANCE = .001
GMSH_TO_CCX = (0, 1, 2, 3, 4, 5, 6, 7, 9, 8)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def external_faces(elements):
    """Index exterior C3D10 faces and reject incompatible quadratic interiors."""
    indexed = {}
    for element, nodes in elements.items():
        if len(nodes) != 10 or len(set(nodes)) != 10:
            raise ValueError("Expected ten distinct C3D10 nodes")
        for face, indices in enumerate(FACES, 1):
            ids = tuple(nodes[i] for i in indices)
            indexed.setdefault(tuple(sorted(ids[:3])), []).append((element, face, ids))
    result = {}
    for key, members in indexed.items():
        if len(members) == 1:
            result[key] = members[0]
        elif len(members) != 2 or edge_nodes(members[0][2]) != edge_nodes(members[1][2]):
            raise ValueError("Nonmanifold or incompatible quadratic interior face")
    return result


def edge_nodes(triangle):
    if len(triangle) != 6 or len(set(triangle)) != 6:
        raise ValueError("Expected six distinct TRI6 nodes")
    return {tuple(sorted((triangle[a], triangle[b]))): triangle[m]
            for a, b, m in ((0, 1, 3), (1, 2, 4), (2, 0, 5))}


def surface_faces(triangles, exterior):
    faces, nodes = [], set()
    for triangle in triangles:
        edges = edge_nodes(triangle)
        match = exterior.get(tuple(sorted(triangle[:3])))
        if match is None or edge_nodes(match[2]) != edges:
            raise ValueError("Surface triangle does not match an exterior quadratic face")
        faces.append([match[0], match[1]])
        nodes.update(triangle)
    if not faces or len({tuple(f) for f in faces}) != len(faces):
        raise ValueError("Empty or duplicate surface faces")
    return {"faces": faces, "nodes": sorted(nodes)}


def append_body(all_nodes, all_elements, nodes, elements):
    """Renumber each independent model; never merge coincident coordinates."""
    if not nodes or not elements or any(len(p) != 3 or not all(map(math.isfinite, p)) for p in nodes.values()):
        raise ValueError("Missing mesh or nonfinite coordinates")
    if {n for row in elements.values() for n in row} != set(nodes):
        raise ValueError("Incomplete body node ownership")
    external_faces(elements)
    node_offset, element_offset = max(all_nodes, default=0), max(all_elements, default=0)
    node_map = {n: node_offset + i + 1 for i, n in enumerate(sorted(nodes))}
    element_map = {e: element_offset + i + 1 for i, e in enumerate(sorted(elements))}
    all_nodes.update({node_map[n]: xyz for n, xyz in nodes.items()})
    all_elements.update({element_map[e]: tuple(node_map[n] for n in row) for e, row in elements.items()})
    return node_map, element_map


def validate_ownership(nodes, elements, bodies):
    seen_nodes, seen_elements = set(), set()
    for body in bodies.values():
        ns, es = set(body["nodes"]), set(body["elements"])
        if (not ns or not es or seen_nodes & ns or seen_elements & es
                or not es <= elements.keys() or {n for e in es for n in elements[e]} != ns):
            raise ValueError("Body ownership overlaps or is incomplete")
        seen_nodes.update(ns)
        seen_elements.update(es)
    if seen_nodes != set(nodes) or seen_elements != set(elements):
        raise ValueError("Body ownership does not cover the mesh")


def worker(geometry_directory, size, hardware_size):
    import gmsh

    geometry_directory = Path(geometry_directory)
    geometry_path = geometry_directory / "geometry.json"
    geometry_hash = digest(geometry_path)
    info = json.loads(geometry_path.read_text())
    names = sorted(info["parts"])
    if len(names) != 14 or set(info["step_sha256"]) != {name + ".step" for name in names}:
        raise ValueError("Expected exactly fourteen frozen STEP bodies")
    if any(Path(name).name != name for name in names):
        raise ValueError("Invalid body name")
    if any(not math.isfinite(v) or v <= 0 for v in (size, hardware_size)):
        raise ValueError("Mesh sizes must be finite and positive")
    if any(digest(geometry_directory / name) != value for name, value in info["step_sha256"].items()):
        raise ValueError("Frozen STEP changed before meshing")
    sources = {str(Path(__file__).name): Path(__file__).read_bytes(),
               "floor_contact.py": Path(__file__).with_name("floor_contact.py").read_bytes()}
    output = Path(tempfile.mkdtemp(prefix="mesh-", dir=geometry_directory))
    all_nodes, all_elements, bodies = {}, {}, {}
    record = {"status": "PREPARING; NO SOLVER", "limits": LIMITS,
              "geometry_sha256": geometry_hash, "step_sha256": info["step_sha256"],
              "configuration": {"size_mm": size, "hardware_size_mm": hardware_size},
              "source_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in sources.items()},
              "acceptance": {"relative_volume_error_max": VOLUME_RELATIVE_TOLERANCE,
                             "minimum_jacobian_exclusive": 0, "shared_body_nodes": 0}}
    for name, contents in sources.items():
        (output / (name + ".snapshot")).write_bytes(contents)
    (output / "mesh.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print(output, flush=True)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Verbosity", 2)
        for name in names:
            gmsh.model.add(name)
            imported = gmsh.model.occ.importShapes(str(geometry_directory / (name + ".step")))
            gmsh.model.occ.synchronize()
            if len(imported) != 1 or imported[0][0] != 3 or len(gmsh.model.getEntities(3)) != 1:
                raise ValueError("Expected one solid per independent Gmsh model")
            cad_volume = info["parts"][name]["volume_mm3"]
            if not math.isfinite(cad_volume) or cad_volume <= 0 or abs(gmsh.model.occ.getMass(*imported[0]) / cad_volume - 1) > 1e-7:
                raise ValueError("Imported STEP volume differs from frozen CAD")
            target = size if name.startswith("leg_right_") else hardware_size
            for option, value in {"Mesh.MeshSizeMax": target, "Mesh.MeshSizeMin": min(1., target / 4),
                                  "Mesh.MeshSizeFromCurvature": 32, "Mesh.MeshSizeExtendFromBoundary": 0,
                                  "Mesh.ElementOrder": 2}.items():
                gmsh.option.setNumber(option, value)
            gmsh.model.mesh.generate(3)
            gmsh.model.mesh.optimize("HighOrder")
            types, tags_by_type, connectivity = gmsh.model.mesh.getElements(3)
            if list(types) != [11]:
                raise ValueError("Expected quadratic tetrahedra only")
            tags = tags_by_type[0]
            nodes_tags, coordinates, _ = gmsh.model.mesh.getNodes()
            nodes = {int(n): tuple(float(v) for v in coordinates[3*i:3*i+3]) for i, n in enumerate(nodes_tags)}
            elements = {int(e): tuple(int(connectivity[0][10*i+j]) for j in GMSH_TO_CCX) for i, e in enumerate(tags)}
            exterior = external_faces(elements)
            minimum = min(float(v) for v in gmsh.model.mesh.getElementQualities(tags, "minDetJac"))
            points, weights = gmsh.model.mesh.getIntegrationPoints(11, "Gauss5")
            _, determinants, _ = gmsh.model.mesh.getJacobians(11, points, imported[0][1])
            if len(determinants) != len(tags) * len(weights) or not all(math.isfinite(float(d)) and d > 0 for d in determinants):
                raise ValueError("Invalid quadratic integration Jacobians")
            if not math.isfinite(minimum) or minimum <= 0:
                raise ValueError("Nonpositive sampled quadratic Jacobian")
            mesh_volume = math.fsum(float(d) * float(weights[i % len(weights)]) for i, d in enumerate(determinants))
            if abs(mesh_volume / cad_volume - 1) > VOLUME_RELATIVE_TOLERANCE:
                raise ValueError("Integrated quadratic mesh volume differs from CAD")
            node_map, element_map = append_body(all_nodes, all_elements, nodes, elements)
            surfaces, covered = {}, set()
            for dim, tag in gmsh.model.getBoundary(imported, oriented=False):
                kinds, _, flat_nodes = gmsh.model.mesh.getElements(dim, tag)
                if list(kinds) != [9]:
                    raise ValueError("Expected quadratic surface triangles only")
                flat = flat_nodes[0]
                selected = surface_faces([tuple(map(int, flat[i:i+6])) for i in range(0, len(flat), 6)], exterior)
                keys = {tuple(pair) for pair in selected["faces"]}
                if covered & keys:
                    raise ValueError("Exterior face appears on multiple CAD surfaces")
                covered.update(keys)
                surfaces[str(tag)] = {"cad_type": gmsh.model.getType(dim, tag),
                    "cad_bounds_mm": list(gmsh.model.getBoundingBox(dim, tag)),
                    "cad_area_mm2": gmsh.model.occ.getMass(dim, tag),
                    "faces": [[element_map[e], face] for e, face in selected["faces"]],
                    "nodes": [node_map[n] for n in selected["nodes"]]}
            if covered != {(e, face) for e, face, _ in exterior.values()}:
                raise ValueError("CAD surface groups do not cover complete exterior")
            bodies[name] = {"nodes": sorted(node_map.values()), "elements": sorted(element_map.values()),
                           "surfaces": surfaces, "target_mesh_size_mm": target,
                           "min_sampled_jacobian": minimum, "min_integration_jacobian": float(min(determinants)),
                           "cad_volume_mm3": cad_volume, "mesh_volume_mm3": mesh_volume}
            gmsh.model.remove()
        version = gmsh.__version__
    except Exception as error:
        failure = {**record, "status": "FAILED MESH PREPARATION; NO SOLVER",
                   "error": f"{type(error).__name__}: {error}", "completed_bodies": bodies,
                   "completed_node_count": len(all_nodes), "completed_element_count": len(all_elements)}
        (output / "mesh.json").write_text(json.dumps(failure, indent=2, allow_nan=False) + "\n")
        raise
    finally:
        gmsh.finalize()
    validate_ownership(all_nodes, all_elements, bodies)
    if digest(geometry_path) != geometry_hash or any(digest(geometry_directory / name) != value for name, value in info["step_sha256"].items()):
        raise ValueError("Frozen geometry changed during meshing")
    if any(Path(__file__).with_name(name).read_bytes() != contents for name, contents in sources.items()):
        raise ValueError("Mesh source changed during preparation")
    lines = ["*HEADING", LIMITS, "*NODE"]
    lines += [f"{n}," + ",".join(map(repr, xyz)) for n, xyz in all_nodes.items()]
    for name, body in bodies.items():
        lines += [f"*ELEMENT,TYPE=C3D10,ELSET={name.upper()}"]
        lines += [f"{e}," + ",".join(map(str, all_elements[e])) for e in body["elements"]]
    (output / "mesh.inp").write_text("\n".join(lines) + "\n")
    record = {**record, "status": "VERIFIED MESH ONLY; NO SOLVER",
              "gmsh_version": version, "body_count": len(bodies), "node_count": len(all_nodes),
              "element_count": len(all_elements), "bodies": bodies,
              "mesh_sha256": digest(output / "mesh.inp")}
    (output / "mesh.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geometry_directory", type=Path)
    parser.add_argument("--size", type=float, default=40.)
    parser.add_argument("--hardware-size", type=float, default=3.)
    args = parser.parse_args()
    print(worker(args.geometry_directory, args.size, args.hardware_size), flush=True)


if __name__ == "__main__":
    main()
