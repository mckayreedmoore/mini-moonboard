"""Targeted finished-timber section properties from the shared BREP cache.

This method performs selected plane intersections, never rebuilds the model
or repeats the 1050-section inventory. A simultaneous signed cut wrench can
be evaluated using the actual centroid, cross moment and material boundary.
Linear normal stress is a component diagnostic; shear/local fracture and
member stability are separate methods.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
from pathlib import Path

from scripts import thin_bolted_timber_resistance as unit

ROOT = unit.ROOT
PACKET = unit.PACKET
NATIVE = PACKET / "native-geometry-v4.json"
NATIVE_SHA = "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9"
UNIT = PACKET / "timber-bolt-resistance-v4.json"
UNIT_SHA = "5e78ac49a2db2050caf7ee7d2002d0ebf4f9a92496e857a0e2d652629bd0d848"
AREA_TOLERANCE_MM2 = 1e-3


def section_basis(grain) -> tuple[list, list, list]:
    """Match the frozen inventory's right-handed U,V,grain convention."""
    g = unit.unit(unit.vector(grain, "section grain"))
    seed = [1., 0., 0.] if abs(g[0]) < .9 else [0., 1., 0.]
    u = unit.unit([x - unit.dot(seed, g) * y for x, y in zip(seed, g, strict=True)])
    v = unit.unit(unit.cross(g, u))
    return u, v, g


def exact_bounds(shape) -> list[list[float]]:
    """Analytic-geometry extremal bounds, independent of viewer tessellation."""
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib

    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape.wrapped, box, False, False)
    low_x, low_y, low_z, high_x, high_y, high_z = box.Get()
    return [[low_x, high_x], [low_y, high_y], [low_z, high_z]]


def rigid_matrix(rows):
    """Mark an orthonormal transform as gp_Trsf, preserving analytic curves."""
    import cadquery as cq
    from OCP.gp import gp_Trsf

    transform = gp_Trsf()
    transform.SetValues(*(float(value) for row in rows[:3] for value in row))
    return cq.Matrix(transform)


def linear_normal_stress(local_section, properties: dict, wrench: dict) -> dict:
    """Recover sigma=N/A+bU*U+bV*V from one complete signed cut wrench.

    The cut force/couple act on the lower-grain member portion. In the
    right-handed U,V,grain basis, Mu=int(sigma*V)dA and
    Mv=-int(sigma*U)dA. The full wrench is transported to the actual centroid
    before solving the two-by-two area-moment matrix.
    """
    force = unit.vector(wrench["force_on_lower_portion_xyz_n"], "same-cut force")
    moment = unit.vector(wrench["moment_on_lower_portion_about_cut_xyz_nmm"], "same-cut couple")
    cut = unit.vector(wrench["cut_point_xyz_mm"], "same-cut point")
    center = properties["centroid_xyz_mm"]
    u, v, g = properties["basis_u_v_grain_xyz"]
    unit.require(abs(unit.dot(g, cut) - properties["station_global_grain_projection_mm"]) < 1e-5,
                 "complete wrench does not belong to this section station")
    offset = [a - b for a, b in zip(center, cut, strict=True)]
    centroid_moment = [a - b for a, b in zip(moment, unit.cross(offset, force), strict=True)]
    hu, hv = -unit.dot(centroid_moment, v), unit.dot(centroid_moment, u)
    second = properties["centroidal_area_moment_matrix_uv_mm4"]
    uu, uv, vv = second[0][0], second[0][1], second[1][1]
    determinant = uu * vv - uv * uv
    unit.require(determinant > 1e-12 * uu * vv, "degenerate section inertia matrix")
    beta = [(vv * hu - uv * hv) / determinant, (uu * hv - uv * hu) / determinant]
    mean = unit.dot(force, g) / properties["finished_area_mm2"]
    magnitude = math.hypot(*beta)
    if magnitude > 1e-20:
        cu, cv = properties["centroid_uv_mm"]
        direction = [b / magnitude for b in beta]
        matrix = rigid_matrix([[direction[0], direction[1], 0., -direction[0] * cu - direction[1] * cv],
                            [-direction[1], direction[0], 0., direction[1] * cu - direction[0] * cv],
                            [0., 0., 1., 0.], [0., 0., 0., 1.]])
        bounds = exact_bounds(local_section.transformShape(matrix))[0]
        bending = [magnitude * bounds[0], magnitude * bounds[1]]
    else:
        bending = [0., 0.]
    limits = [mean + value for value in bending]
    return {"signed_same_cut_wrench": wrench,
            "force_xyz_n": force, "moment_about_actual_centroid_xyz_nmm": centroid_moment,
            "axial_tension_positive_n": unit.dot(force, g), "mean_axial_normal_stress_n_mm2": mean,
            "normal_stress_gradient_uv_n_mm3": beta,
            "bending_normal_stress_extrema_n_mm2": bending,
            "combined_linear_normal_stress_extrema_n_mm2": limits,
            "maximum_tensile_normal_stress_n_mm2": max(0., limits[1]),
            "maximum_compressive_normal_stress_n_mm2": max(0., -limits[0]),
            "extrema_method": "analytic geometry directional support bounds of actual trimmed material",
            "provided_wrench_independently_recovered_from_compatible_field_by_this_geometry_method": False,
            "rectangle_corner_envelope_substituted": False,
            "shear_stress_or_effective_shear_area": None, "torsion_stress": None,
            "local_stress_concentration_fracture_or_stability": None,
            "complete_adjusted_NDS_resistance_or_acceptance": None}


def measure_section(shape, *, origin, grain, expected_prior_area_mm2: float | None = None,
                    wrench: dict | None = None) -> dict:
    """Measure one unfilled actual plane, including every hole/recess/void."""
    import cadquery as cq
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps

    from scripts.wood_joint_wj12_sections import (
        _basis_matrix,
        _plane_face,
        _section_measure,
    )

    u, v, g = section_basis(grain)
    point = cq.Vector(*unit.vector(origin, "section origin"))
    axes = [cq.Vector(*a) for a in (u, v, g)]
    section = shape.intersect(_plane_face(point, axes[2]))
    unit.require(section.isValid(), "invalid section topology")
    matrix = _basis_matrix(point, *axes)
    local = section.transformShape(rigid_matrix(
        [[matrix.wrapped.Value(i, j) for j in (1, 2, 3, 4)] for i in (1, 2, 3)]))
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(local.wrapped, props, False, False)
    area = float(props.Mass())
    unit.require(math.isfinite(area) and area > 1e-6, "no positive material on targeted plane")
    # Independently match the established area-query method at this same
    # targeted station. This does not rerun the saved inventory.
    prior_method = _section_measure(shape, origin=point, normal=axes[2], u_axis=axes[0], v_axis=axes[1])
    unit.require(abs(area - prior_method["area_mm2"]) <= AREA_TOLERANCE_MM2,
                 "new surface properties differ from established section area method")
    if expected_prior_area_mm2 is not None:
        unit.require(abs(area - expected_prior_area_mm2) <= AREA_TOLERANCE_MM2,
                     "targeted section area differs from frozen same-station inventory")
    center = props.CentreOfMass()
    cu, cv, cg = center.X(), center.Y(), center.Z()
    unit.require(abs(cg) < 1e-5, "section centroid is off its plane")
    inertia = props.MatrixOfInertia()
    covariance = [[inertia.Value(2, 2), -inertia.Value(1, 2)],
                  [-inertia.Value(1, 2), inertia.Value(1, 1)]]
    unit.require(all(math.isfinite(x) for row in covariance for x in row)
                 and covariance[0][0] > 0. and covariance[1][1] > 0., "invalid centroidal moments")
    world_center = point + axes[0].multiply(cu) + axes[1].multiply(cv)
    bounds = exact_bounds(local)
    result = {"finished_area_mm2": area, "established_section_measure_area_mm2": prior_method["area_mm2"],
              "expected_frozen_same_station_area_mm2": expected_prior_area_mm2,
              "same_station_area_tolerance_mm2": AREA_TOLERANCE_MM2,
              "station_global_grain_projection_mm": point.dot(axes[2]),
              "section_origin_xyz_mm": list(point.toTuple()), "basis_u_v_grain_xyz": [u, v, g],
              "centroid_uv_mm": [cu, cv], "centroid_xyz_mm": list(world_center.toTuple()),
              "centroidal_area_moment_matrix_uv_mm4": covariance,
              "I_about_u_mm4": covariance[1][1], "I_about_v_mm4": covariance[0][0],
              "product_integral_uv_mm4": covariance[0][1],
              "polar_area_moment_mm4": sum(covariance[i][i] for i in (0, 1)),
              "bounds_uv_mm": {"u": bounds[0], "v": bounds[1]},
              "trimmed_face_count": len(section.Faces()),
              "bores_or_other_voids_restored": False,
              "linear_normal_stress": None, "shear_area_method_qualified": False,
              "continuous_extrema_or_complete_member_resistance_proved": False}
    if wrench is not None:
        result["linear_normal_stress"] = linear_normal_stress(local, result, wrench)
    return result


def query_requests(request_path: Path, expected_sha256: str) -> dict:
    """Source-bound, deliberately bounded selected-station production API."""
    import cadquery as cq

    unit.require(unit.sha(request_path) == expected_sha256, "immutable targeted request differs")
    request = json.loads(request_path.read_text())
    unit.require(request["candidate"] == unit.CANDIDATE and request["unit_packet_sha256"] == UNIT_SHA
                 and request["geometry_cache_sha256"] == NATIVE_SHA, "targeted request candidate/source differs")
    unit.require(unit.sha(UNIT) == UNIT_SHA and unit.sha(NATIVE) == NATIVE_SHA, "preserve existing unit/cache bytes")
    packet, cache = json.loads(UNIT.read_text()), json.loads(NATIVE.read_text())
    for relative, expected in packet["source_sha256"].items():
        unit.require(unit.sha(ROOT / relative) == expected, "frozen timber geometry dependency differs")
    detail = packet["reproducible_detail_artifact"]
    unit.require(unit.sha(ROOT / detail["path"]) == detail["sha256"], "existing section inventory differs")
    full = json.loads((ROOT / detail["path"]).read_text())["finished_geometry_queries"]
    prior = {row["member"]: row for row in full["finished_member_sections"]}
    parts = {row["id"]: row for row in cache["parts"] if row["kind"] == "timber"}
    rows = request["requests"]
    unit.require(1 <= len(rows) <= 40, "targeted batch must select1-40 cuts, not repeat the inventory")
    pins = {str(path.resolve().relative_to(ROOT)): unit.sha(path) for path in
            (request_path, UNIT, NATIVE, ROOT / detail["path"], Path(__file__),
             ROOT / "scripts/wood_joint_wj12_sections.py")}
    for relative, expected in request.get("source_sha256", {}).items():
        unit.require(unit.sha(ROOT / relative) == expected, "targeted demand source differs")
        pins[relative] = expected
    shapes, results, seen = {}, [], set()
    for row in rows:
        name, station = row["member"], row["station_global_grain_projection_mm"]
        key = (name, station)
        unit.require(key not in seen and name in prior and name in parts, "duplicate/foreign targeted timber cut")
        seen.add(key)
        samples = [sample for sample in prior[name]["sampled_sections"]
                   if abs(sample["station_global_grain_projection_mm"] - station) < 1e-8]
        unit.require(len(samples) == 1, "targeted plane is not an existing immutable sampled station")
        part = parts[name]
        grain = unit.unit(part["grain_axis_xyz"])
        unit.require(math.dist(grain, prior[name]["grain_axis_xyz"]) < 1e-8, "targeted timber grain differs")
        path = ROOT / part["path"]
        unit.require(unit.sha(path) == part["sha256"], "targeted finished BREP bytes differ")
        pins[part["path"]] = part["sha256"]
        if name not in shapes:
            shape = cq.Shape.importBrep(str(path))
            unit.require(shape.isValid() and abs(shape.Volume() - part["volume_mm3"]) < .01,
                         "targeted imported solid differs from native cache")
            shapes[name] = shape
        wrench = row.get("signed_same_cut_wrench")
        if wrench is not None:
            unit.require(request.get("state_id") and row.get("state_id") == request["state_id"]
                         and request.get("source_sha256"), "targeted wrench needs an immutable same-state demand source")
        result = measure_section(shapes[name], origin=[g * station for g in grain], grain=grain,
                                 expected_prior_area_mm2=samples[0]["finished_area_mm2"], wrench=wrench)
        results.append({"member": name, "state_id": request.get("state_id"), **result})
    return {"schema": "thin_bolted_targeted_finished_section_properties/v1", "candidate": unit.CANDIDATE,
            "state_id": request.get("state_id"), "source_sha256": pins,
            "selected_cut_count": len(results), "finished_sections": results,
            "tool_versions": {name: importlib.metadata.version(name) for name in ("cadquery", "cadquery-ocp", "numpy")},
            "full_1050_inventory_repeated": False, "model_rebuilt": False, "native_solve_executed": False,
            "limits": ["OpenCascade exact surface integration uses actual trimmed plane faces and includes cross inertia.",
                       "Linear normal stresses are simultaneous centroid-transported section components; local hole/notch concentrations, shear/torsion/fracture and stability are separate.",
                       "Actual stock and strength adjustments remain unadopted; no geometry or structural release is supplied."],
            "release": unit.RELEASE}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--requests-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    unit.require(not args.out.exists(), "preserve distinct targeted evidence bytes")
    result = query_requests(args.requests, args.requests_sha256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "selected_cut_count": result["selected_cut_count"],
                      "release": result["release"]}, indent=2))


if __name__ == "__main__":
    main()
