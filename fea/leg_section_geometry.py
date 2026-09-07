"""Curved boundary geometry arithmetic only; no stress or native FEA solve."""
import argparse
import hashlib
import json
import math
import tarfile
from collections import defaultdict
from pathlib import Path

import numpy as np

from fea import leg_section_preflight as selection
from fea.floor_contact import FACES, integrated_weights, mesh

GATES = {"closed_area_relative": 1e-10, "volume_relative": 1e-8,
         "centroid_over_length": 1e-8, "area_quadrature_relative": 1e-8}
LIMITS = ("Curved mesh geometry integration only. Sampled surface Jacobians/orientation, not an "
          "everywhere-positive or injective mapping proof. No native SECTION PRINT, stress, contact, "
          "material, connection demand, resistance or construction qualification.")


def outward_face(nodes, ids, indices):
    ns = tuple(ids[i] for i in indices)
    xyz = np.array([nodes[n] for n in ns])
    opposite = next(n for n in ids[:4] if n not in ns[:3])
    if np.dot(np.cross(xyz[1]-xyz[0], xyz[2]-xyz[0]), np.array(nodes[opposite])-xyz[0]) > 0:
        ns = tuple(ns[i] for i in (0, 2, 1, 5, 4, 3))
    return ns


def boundary(nodes, elements, selected):
    """Recover complete outward quadratic faces of already audited sub-body."""
    faces = defaultdict(list)
    for e in selected:
        ids = elements[e]
        for indices in FACES:
            ns = tuple(ids[i] for i in indices)
            faces[tuple(sorted(ns))].append((e, ns))
    result = []
    for entries in faces.values():
        if len(entries) == 2:
            continue
        if len(entries) != 1:
            raise ValueError("Nonmanifold sub-body")
        e, ns = entries[0]
        result.append(outward_face(nodes, elements[e], [elements[e].index(n) for n in ns]))
    return result


def surface_integrals(points, basis, gradients, weights):
    """Integrate x, cross(dx/dr,dx/ds) on oriented TRI6 faces."""
    points, basis, gradients, weights = map(np.asarray, (points, basis, gradients, weights))
    if (points.ndim != 3 or points.shape[1:] != (6, 3) or basis.shape != (len(weights), 6)
            or gradients.shape != (len(weights), 6, 3) or not len(points)
            or not all(np.isfinite(v).all() for v in (points, basis, gradients, weights))):
        raise ValueError("Finite matching TRI6 quadrature arrays required")
    position = np.einsum("qn,fnk->fqk", basis, points)
    derivatives = np.einsum("qna,fnk->fqak", gradients, points)
    area_vector = np.cross(derivatives[:, :, 0], derivatives[:, :, 1])
    jacobian = np.linalg.norm(area_vector, axis=2)
    corner = np.cross(points[:, 1]-points[:, 0], points[:, 2]-points[:, 0])
    orientation = np.einsum("fqk,fk->fq", area_vector, corner)
    if np.any(jacobian <= 0) or np.any(orientation <= 0):
        raise ValueError("Nonpositive sampled surface Jacobian/orientation")
    flux = np.einsum("fqk,fqk->fq", position, area_vector)
    return {"area_vector": np.einsum("q,fqk->k", weights, area_vector).tolist(),
            "area": float(np.einsum("q,fq->", weights, jacobian)),
            "volume": float(np.einsum("q,fq->", weights, flux)/3),
            "first_moment": (np.einsum("q,fq,fqk->k", weights, flux, position)/4).tolist(),
            "minimum_sampled_surface_jacobian": float(jacobian.min()),
            "minimum_sampled_orientation_cosine": float((orientation/(jacobian*np.linalg.norm(corner, axis=1)[:, None])).min())}


def assess(low, high, volume, first_moment, length, opposed):
    """Frozen geometric arithmetic gates; report failure without tuning."""
    if not math.isfinite(opposed) or opposed < 0:
        raise ValueError("Finite nonnegative opposed-cut residual required")
    if min(volume, low["area"], high["area"], length) <= 0 or low["volume"] <= 0:
        raise ValueError("Positive geometry scales required")
    values = {"closed_area_relative": math.hypot(*low["area_vector"])/low["area"],
              "volume_relative": abs(low["volume"]/volume-1),
              "centroid_over_length": math.dist(np.array(low["first_moment"])/low["volume"], np.array(first_moment)/volume)/length,
              "area_quadrature_relative": abs(low["area"]/high["area"]-1)}
    if not all(math.isfinite(v) for v in values.values()):
        raise ValueError("Nonfinite geometry comparisons")
    failures = {name: value for name, value in values.items() if value > GATES[name]}
    if opposed > GATES["closed_area_relative"]:
        failures["opposed_cut_area_relative"] = opposed
    return {"geometric_comparisons_within_gates": not failures, "comparisons": values,
            "opposed_cut_area_relative": opposed, "failures": failures}


def native_rule(gmsh, order):
    points, weights = gmsh.model.mesh.getIntegrationPoints(9, f"Gauss{order}")
    _, basis, _ = gmsh.model.mesh.getBasisFunctions(9, points, "Lagrange")
    _, gradient, _ = gmsh.model.mesh.getBasisFunctions(9, points, "GradLagrange")
    return np.array(basis).reshape(-1, 6), np.array(gradient).reshape(-1, 6, 3), np.array(weights)


def run(output=None):
    import gmsh

    preflight = selection.preflight()
    results = {}
    with tarfile.open(selection.ARCHIVE) as archive:
        for size, selected in preflight["meshes"].items():
            nodes, elements = mesh(archive.extractfile(f"independent{size}.inp").read().decode())
            subset = {e: elements[e] for e in selected["selected_elements"]}
            used = {n for ids in subset.values() for n in ids}
            origin = np.mean([nodes[n] for n in used], axis=0)
            local = {n: tuple(np.array(nodes[n])-origin) for n in used}
            length = float(np.linalg.norm(np.ptp(list(local.values()), axis=0)))
            weights = integrated_weights(subset, local)
            volume = math.fsum(weights.values())
            moment = [math.fsum(w*local[n][axis] for n, w in weights.items()) for axis in range(3)]
            faces = boundary(nodes, elements, subset)
            if len(faces) != selected["boundary_face_count"]:
                raise ValueError("Boundary differs from preflight")
            patches = np.array([[np.array(nodes[n])-origin for n in ns] for ns in faces])
            cuts = np.array([[np.array(nodes[n])-origin for n in c["outward_nodes"]] for c in selected["cut"]])
            upper = [outward_face(nodes, elements[c["upper"][0]], FACES[c["upper"][1]-1]) for c in selected["cut"]]
            upper_patches = np.array([[np.array(nodes[n])-origin for n in ns] for ns in upper])
            gmsh.initialize()
            try:
                gmsh.option.setNumber("General.NumThreads", 2)
                rules = {order: native_rule(gmsh, order) for order in (8, 12)}
                surface = {str(order): surface_integrals(patches, *rule) for order, rule in rules.items()}
                cut = surface_integrals(cuts, *rules[8])
                reverse = surface_integrals(upper_patches, *rules[8])
                opposed = math.hypot(*(np.array(cut["area_vector"])+reverse["area_vector"]))/cut["area"]
                version = gmsh.__version__
            finally:
                gmsh.finalize()
            results[size] = {**assess(surface["8"], surface["12"], volume, moment, length, opposed),
                "surface": surface, "cut_surface": cut, "reverse_cut_surface": reverse,
                "volume_integral_mm3": volume, "volume_first_moment_local_mm4": moment,
                "origin_mm": origin.tolist(), "characteristic_length_mm": length,
                "selected_elements": len(subset), "boundary_faces": len(faces), "cut_faces": len(cuts)}
            if output is not None:
                with (output/f"mesh{size}.json").open("x") as stream:
                    json.dump(results[size], stream, indent=2, allow_nan=False)
    with selection.ARCHIVE.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != selection.ARCHIVE_SHA:
            raise ValueError("Archive changed during integration")
    return {"limits": LIMITS, "qualified_for_design": False, "gates": GATES, "gmsh_version": version,
            "archive_sha256": selection.ARCHIVE_SHA, "meshes": results,
            "status": "GEOMETRIC COMPARISONS WITHIN GATES" if all(r["geometric_comparisons_within_gates"] for r in results.values()) else "GEOMETRIC COMPARISON FAILED"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        report = run(args.output)
    except Exception as error:
        report = {"status": "GEOMETRY INTEGRATION FAILED", "limits": LIMITS, "qualified_for_design": False,
                  "exception": {"type": type(error).__name__, "message": str(error)}}
        with (args.output/"report.json").open("x") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
        raise
    with (args.output/"report.json").open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
