"""C3D20 volume quadrature for one exact, axis-aligned cylindrical bore.

The existing local C3D20 pilot uses affine Cartesian bricks and 3x3x3 Gauss
integration.  This helper supplies a drop-in integration rule for cells cut by
one finite cylindrical void.  It changes the material integration domain, so
both element stiffness and stress recovery must consume the returned rule.
It never edits a frozen producer or runs a solve.

Use ``rule['natural_points']`` and ``rule['weights_mm3']`` in
``K_e += B.T @ C @ B * weight``.  The returned points are inside the exact
retained timber domain.  A caller must split background cells at bore end
planes, omit cells whose exact retained volume is zero, and reject cells cut
by more than one bore until a union-domain rule is supplied.

``positive_volume_c3d20_mesh`` rebuilds the intact cell connectivity from the
same caller-supplied refined grids, including positive-volume cells whose old
center predicate discarded them. ``c3d20_element_stiffness`` and
``c3d20_stress_at_rule`` use the same integration rule, so stress is recovered
only at true-wood material points.
"""

from __future__ import annotations

import math
from itertools import pairwise, product
from typing import Any

import numpy as np

_FULL_NATURAL_NODES = None


def _natural_nodes() -> np.ndarray:
    global _FULL_NATURAL_NODES
    if _FULL_NATURAL_NODES is None:
        from fea.floor_recess_mesh import CORNERS, EDGES

        _FULL_NATURAL_NODES = np.vstack((CORNERS, EDGES)).astype(float)
    return _FULL_NATURAL_NODES


def _cell_bounds(nodes_mm: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    nodes = np.asarray(nodes_mm, dtype=float)
    if nodes.shape != (20, 3) or not np.isfinite(nodes).all():
        raise ValueError("C3D20 cell nodes must be a finite 20 by 3 array")
    low, high = nodes.min(axis=0), nodes.max(axis=0)
    half = (high - low) / 2.0
    if np.any(half <= 0.0):
        raise ValueError("C3D20 cell must have positive extent on each axis")
    expected = (low + high) / 2.0 + _natural_nodes() * half
    error = float(np.max(np.abs(nodes - expected)))
    if error > 1e-8:
        raise ValueError(
            "Cut-cell rule requires the existing affine axis-aligned C3D20 cell; "
            f"maximum node-map error is {error:.6g} mm"
        )
    return low, high, half


def _disk_rectangle_area(
    y0: float,
    y1: float,
    z0: float,
    z1: float,
    cy: float,
    cz: float,
    radius: float,
) -> float:
    """Analytic area of a disk clipped to an axis-aligned rectangle."""
    breaks = [y0, y1]
    for y in (cy - radius, cy + radius):
        if y0 < y < y1:
            breaks.append(y)
    for z in (z0, z1):
        dz = z - cz
        if abs(dz) < radius:
            span = math.sqrt(max(0.0, radius * radius - dz * dz))
            for y in (cy - span, cy + span):
                if y0 < y < y1:
                    breaks.append(y)
    breaks = sorted(set(breaks))

    def root_primitive(delta: float) -> float:
        d = min(radius, max(-radius, delta))
        root = math.sqrt(max(0.0, radius * radius - d * d))
        return 0.5 * (d * root + radius * radius * math.asin(d / radius))

    area = 0.0
    for left, right in pairwise(breaks):
        if right <= left:
            continue
        mid = 0.5 * (left + right)
        delta = mid - cy
        if abs(delta) >= radius:
            continue
        span = math.sqrt(radius * radius - delta * delta)
        circle_low, circle_high = cz - span, cz + span
        clipped_low, clipped_high = max(z0, circle_low), min(z1, circle_high)
        if clipped_high <= clipped_low:
            continue
        lower_is_circle = circle_low > z0
        upper_is_circle = circle_high < z1
        constant = (
            (cz if upper_is_circle else z1)
            - (cz if lower_is_circle else z0)
        )
        root_coefficient = int(upper_is_circle) + int(lower_is_circle)
        # The lower circle contributes -sqrt; subtracting it adds +sqrt.
        area += constant * (right - left)
        area += root_coefficient * (
            root_primitive(right - cy) - root_primitive(left - cy)
        )
    return max(0.0, float(area))


def _bore_frame(bore: dict[str, Any]) -> tuple[np.ndarray, int, list[int], float, float, float]:
    origin = np.asarray(bore["origin"], dtype=float)
    direction = np.asarray(bore["axis"], dtype=float)
    interval = np.asarray(bore["interval_mm"], dtype=float)
    radius = float(bore["radius_mm"])
    if origin.shape != (3,) or direction.shape != (3,) or interval.shape != (2,):
        raise ValueError("Bore requires origin[3], axis[3] and interval_mm[2]")
    if not np.isfinite(origin).all() or not np.isfinite(direction).all():
        raise ValueError("Bore coordinates must be finite")
    if not np.isfinite(interval).all() or interval[1] <= interval[0]:
        raise ValueError("Finite bore interval must be increasing")
    if not math.isfinite(radius) or radius <= 0.0:
        raise ValueError("Bore radius must be positive and finite")
    if abs(np.linalg.norm(direction) - 1.0) > 1e-10:
        raise ValueError("Bore axis must be a unit vector")
    shaft = int(np.argmax(np.abs(direction)))
    if abs(abs(direction[shaft]) - 1.0) > 1e-10 or np.max(
        np.abs(np.delete(direction, shaft))
    ) > 1e-10:
        raise ValueError("Bore axis must align with one C3D20 Cartesian axis")
    axial_ends = origin[shaft] + direction[shaft] * interval
    radial = [axis for axis in range(3) if axis != shaft]
    return (
        origin,
        shaft,
        radial,
        min(float(axial_ends[0]), float(axial_ends[1])),
        max(float(axial_ends[0]), float(axial_ends[1])),
        radius,
    )


def exact_cylinder_void_volume_mm3(
    low_mm: Any, high_mm: Any, bore: dict[str, Any]
) -> float:
    """Return exact box/cylinder intersection volume for cell classification."""
    low, high = np.asarray(low_mm, dtype=float), np.asarray(high_mm, dtype=float)
    if low.shape != (3,) or high.shape != (3,) or not np.isfinite([low, high]).all():
        raise ValueError("Cell bounds must be finite 3-vectors")
    if np.any(high <= low):
        raise ValueError("Cell bounds must have positive extent")
    origin, shaft, radial, axial_low, axial_high, radius = _bore_frame(bore)
    radial_corner_square=max(
        (a-origin[radial[0]])**2+(b-origin[radial[1]])**2
        for a,b in product((low[radial[0]],high[radial[0]]),
                           (low[radial[1]],high[radial[1]])))
    plane_roundoff=8.*np.spacing(max(1.,abs(axial_low),abs(axial_high),abs(low[shaft]),abs(high[shaft])))
    if (low[shaft]>=axial_low-plane_roundoff and high[shaft]<=axial_high+plane_roundoff
            and radial_corner_square<=radius**2):
        # A convex cylinder contains this entire convex box. Return the same
        # product as the cell-volume calculation, avoiding fictitious 1e-15
        # material slivers from subtracting two rounded analytic volumes.
        return float(np.prod(high-low))
    axial_overlap = max(0.0, min(high[shaft], axial_high) - max(low[shaft], axial_low))
    disk_area = _disk_rectangle_area(
        low[radial[0]], high[radial[0]],
        low[radial[1]], high[radial[1]],
        origin[radial[0]], origin[radial[1]], radius,
    )
    return float(axial_overlap * disk_area)


def exact_cylinder_retained_volume_mm3(
    low_mm: Any, high_mm: Any, bore: dict[str, Any]
) -> float:
    """Return exact remaining material volume for one finite cylinder."""
    low, high = np.asarray(low_mm, dtype=float), np.asarray(high_mm, dtype=float)
    cell_volume = float(np.prod(high - low))
    void_volume = exact_cylinder_void_volume_mm3(low, high, bore)
    if void_volume > cell_volume + 1e-9:
        raise ValueError("Cylinder intersection volume exceeds cell volume")
    return max(0.0, cell_volume - void_volume)


def intersecting_bore_indices(
    low_mm: Any, high_mm: Any, bores: list[dict[str, Any]], *, tolerance_mm3: float = 0.0
) -> list[int]:
    """List bores cutting a cell; multiple hits need an exact union rule."""
    hits = [
        index
        for index, bore in enumerate(bores)
        if exact_cylinder_void_volume_mm3(low_mm, high_mm, bore) > tolerance_mm3
    ]
    if len(hits) > 1:
        raise ValueError(
            "Cell intersects multiple exact bores; split the cell or supply a union-domain rule"
        )
    return hits


def positive_volume_c3d20_mesh(
    grain_grid: Any,
    u_grid: Any,
    v_grid: Any,
    geometry: dict[str, Any],
    *,
    volume_tolerance: float = 0.05,
) -> dict[str, Any]:
    """Build intact C3D20 connectivity over exact positive-volume bore cuts.

    Supply the same refined coordinate grids returned by the frozen local
    kernel's ``mesh_grids``. The target center-post cleats have box planes;
    cells crossing a non-box exterior face are rejected to prevent the old
    center-sampling approximation from entering this bore-only correction.
    """
    grids = [np.asarray(values, dtype=float) for values in (grain_grid, u_grid, v_grid)]
    if any(values.ndim != 1 or len(values) < 2 for values in grids):
        raise ValueError("Each refined mesh grid must contain at least two coordinates")
    if any(not np.isfinite(values).all() or np.any(np.diff(values) <= 0.0) for values in grids):
        raise ValueError("Refined mesh grids must be finite and strictly increasing")
    planes = geometry.get("planes", [])
    bores = geometry.get("bores", [])
    natural_nodes = _natural_nodes()
    corner_natural_nodes = natural_nodes[:8]
    nodes: list[np.ndarray] = []
    elements: list[list[int]] = []
    cell_bounds: list[np.ndarray] = []
    element_bores: list[int | None] = []
    element_material_fractions: list[float] = []
    node_map: dict[tuple[float, float, float], int] = {}
    retained_volume = 0.0
    cut_cell_count = 0
    omitted_empty_cell_count = 0

    for i, j, k in product(
        range(len(grids[0]) - 1),
        range(len(grids[1]) - 1),
        range(len(grids[2]) - 1),
    ):
        low = np.array([grids[0][i], grids[1][j], grids[2][k]], dtype=float)
        high = np.array(
            [grids[0][i + 1], grids[1][j + 1], grids[2][k + 1]], dtype=float
        )
        corners = (low + high) / 2.0 + corner_natural_nodes * ((high - low) / 2.0)
        entirely_outside = False
        for face in planes:
            normal = np.asarray(face["normal"], dtype=float)
            projections = corners @ normal
            if np.all(projections > float(face["offset"]) + 1e-8):
                entirely_outside = True
                break
            if np.any(projections > float(face["offset"]) + 1e-8):
                raise ValueError("Bore-cut mesh does not support a cell cut by an exterior plane")
        if entirely_outside:
            continue

        hits = intersecting_bore_indices(low, high, bores)
        cell_volume = float(np.prod(high - low))
        bore_index = hits[0] if hits else None
        exact_cell_volume = (
            cell_volume
            if bore_index is None
            else exact_cylinder_retained_volume_mm3(
                low, high, bores[bore_index]
            )
        )
        if exact_cell_volume <= 0.0:
            omitted_empty_cell_count += 1
            continue

        center, half = (low + high) / 2.0, (high - low) / 2.0
        local_nodes = center + natural_nodes * half
        element: list[int] = []
        for point in local_nodes:
            key = tuple(np.round(point, 8))
            if key not in node_map:
                node_map[key] = len(nodes)
                nodes.append(point)
            element.append(node_map[key])
        elements.append(element)
        cell_bounds.append(np.stack((low, high)))
        element_bores.append(bore_index)
        element_material_fractions.append(exact_cell_volume / cell_volume)
        retained_volume += exact_cell_volume
        cut_cell_count += int(bore_index is not None)

    if not elements:
        raise ValueError("Exact bore clipping removed the entire candidate timber body")
    expected_volume = float(geometry["actual_volume_mm3"])
    relative_volume_error = retained_volume / expected_volume - 1.0
    if abs(relative_volume_error) > volume_tolerance:
        raise ValueError(
            "Exact cut-cell volume differs from the pinned solid volume by "
            f"{relative_volume_error:.6g}"
        )
    return {
        "nodes_mm": np.asarray(nodes, dtype=float),
        "elements": np.asarray(elements, dtype=np.int64),
        "element_bounds_mm": np.asarray(cell_bounds, dtype=float),
        "element_bore_indices": element_bores,
        "element_material_volume_fractions": np.asarray(
            element_material_fractions, dtype=float
        ),
        "retained_volume_mm3": float(retained_volume),
        "expected_step_volume_mm3": expected_volume,
        "relative_volume_error": float(relative_volume_error),
        "positive_volume_cut_cell_count": cut_cell_count,
        "minimum_cut_cell_material_volume_fraction": float(
            min(
                (
                    fraction
                    for fraction, bore_index in zip(
                        element_material_fractions, element_bores, strict=True
                    )
                    if bore_index is not None
                ),
                default=1.0,
            )
        ),
        "omitted_zero_volume_cell_count": omitted_empty_cell_count,
        "restores_cut_cells_without_center_in_wood": True,
        "scope": "Intact box-bound center-post cleats; one bore per cut cell; same caller-supplied grid and physical port coordinates.",
    }


def _c3d20_B_matrices(nodes_mm: Any, natural_points: Any) -> tuple[np.ndarray, np.ndarray]:
    from fea.wood_joint_reduced_members import shape20_derivatives

    nodes = np.asarray(nodes_mm, dtype=float)
    points = np.asarray(natural_points, dtype=float)
    if nodes.shape != (20, 3) or points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("Require C3D20 nodes[20,3] and natural integration points[n,3]")
    derivatives = np.asarray([shape20_derivatives(point) for point in points])
    jacobians = np.einsum("ia,qik->qak", nodes, derivatives)
    determinants = np.linalg.det(jacobians)
    if np.any(determinants <= 0.0):
        raise ValueError("C3D20 cut-cell mapping has a nonpositive Jacobian")
    inverse = np.linalg.inv(jacobians)
    gradients = np.einsum("qik,qka->qia", derivatives, inverse)
    B = np.zeros((len(points), 6, 60), dtype=float)
    for axis in range(3):
        B[:, axis, axis::3] = gradients[:, :, axis]
    pairs = ((0, 1), (0, 2), (1, 2))
    for row, (i, j) in enumerate(pairs, start=3):
        B[:, row, i::3] = gradients[:, :, j]
        B[:, row, j::3] = gradients[:, :, i]
    return B, determinants


def c3d20_element_stiffness(
    nodes_mm: Any, constitutive_mpa: Any, rule: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray]:
    """Assemble one current C3D20 stiffness and shape-volume vector.

    ``constitutive_mpa`` uses the local assembler's engineering order
    ``[g,u,v,gu,gv,uv]``. The caller should use this for cut cells and the
    existing pinned ``brick_stiffness`` for uncut cells until the coupon
    comparison establishes the identical full-cell result.
    """
    constitutive = np.asarray(constitutive_mpa, dtype=float)
    points = rule["natural_points"]
    weights = np.asarray(rule["weights_mm3"], dtype=float)
    if constitutive.shape != (6, 6) or not np.isfinite(constitutive).all():
        raise ValueError("Engineering constitutive matrix must be finite 6 by 6")
    if not np.allclose(constitutive, constitutive.T, atol=1e-8, rtol=0.0):
        raise ValueError("Engineering constitutive matrix must be symmetric")
    if len(points) == 0:
        return np.zeros((60, 60)), np.zeros(20)
    from fea.floor_recess_mesh import shape20

    B, _ = _c3d20_B_matrices(nodes_mm, points)
    CB = np.einsum("ab,qbi->qai", constitutive, B)
    stiffness = np.einsum("qai,qaj,q->ij", B, CB, weights)
    shape = np.asarray([shape20(point) for point in points])
    volume_vector = np.einsum("qi,q->i", shape, weights)
    return (stiffness + stiffness.T) / 2.0, volume_vector


def c3d20_stress_at_rule(
    nodes_mm: Any,
    displacement_mm: Any,
    constitutive_mpa: Any,
    rule: dict[str, Any],
) -> np.ndarray:
    """Recover six engineering stresses only at the rule's true-wood points."""
    displacement = np.asarray(displacement_mm, dtype=float)
    constitutive = np.asarray(constitutive_mpa, dtype=float)
    if displacement.shape == (20, 3):
        displacement = displacement.reshape(60)
    if displacement.shape != (60,) or constitutive.shape != (6, 6):
        raise ValueError("Require 60 C3D20 displacement DOFs and a 6 by 6 material")
    B, _ = _c3d20_B_matrices(nodes_mm, rule["natural_points"])
    strain = np.einsum("qai,i->qa", B, displacement)
    return np.einsum("ab,qb->qa", constitutive, strain)


def _raw_rule(
    nodes_mm: Any, bore: dict[str, Any] | None, order: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    low, high, half = _cell_bounds(nodes_mm)
    center = (low + high) / 2.0
    points_1d, weights_1d = np.polynomial.legendre.leggauss(3)
    physical: list[list[float]] = []
    weights: list[float] = []
    bore_active = False
    exact_void_volume = 0.0
    exact_retained_volume = float(np.prod(high - low))
    shaft = 0
    origin = np.zeros(3)
    direction = np.array([1.0, 0.0, 0.0])
    radial = [1, 2]
    radius = 0.0
    axial_low, axial_high = -math.inf, math.inf
    axial_plane_snap_mm=0.0
    if bore is not None:
        origin, shaft, radial, axial_low, axial_high, radius = _bore_frame(bore)
        exact_void_volume = exact_cylinder_void_volume_mm3(low, high, bore)
        exact_retained_volume -= exact_void_volume
        if exact_retained_volume < -1e-9:
            raise ValueError("Analytic cut volume exceeds the C3D20 cell volume")
        exact_retained_volume = max(0.0, exact_retained_volume)
        bore_active = exact_void_volume > 0.0
        direction = np.asarray(bore["axis"], dtype=float)
        # CAD coordinate addition and cell-node reconstruction can differ by
        # a few ulps at the same axial plane. Such a one-ulp outside slice has
        # no representable interior Gauss point. Align only coincident planes
        # at floating precision; retain every finite physical material cut.
        limits=[axial_low,axial_high]
        for index,endpoint in enumerate(limits):
            for face in (low[shaft],high[shaft]):
                roundoff=8.*np.spacing(max(1.,abs(endpoint),abs(face)))
                if abs(endpoint-face)<=roundoff:
                    axial_plane_snap_mm=max(axial_plane_snap_mm,abs(endpoint-face))
                    limits[index]=float(face)
                    break
        axial_low,axial_high=limits

    if not bore_active:
        for ix, iy, iz in product(range(3), repeat=3):
            natural = np.array(
                [points_1d[ix], points_1d[iy], points_1d[iz]], dtype=float
            )
            physical.append(center + natural * half)
            weights.append(
                float(np.prod(half) * weights_1d[ix] * weights_1d[iy] * weights_1d[iz])
            )
        method = "full_c3d20_3x3x3_gauss"
    elif exact_retained_volume <= 0.0:
        method = "empty_exact_bore_cell"
    else:
        # Break the shaft interval at finite cylinder end planes. The regular
        # C3D20 three-point rule stays exact for the element's degree-four
        # stiffness products in this coordinate.
        x_breaks = [float(low[shaft]), float(high[shaft])]
        for endpoint in (axial_low, axial_high):
            if low[shaft] < endpoint < high[shaft]:
                x_breaks.append(float(endpoint))
        x_breaks = sorted(set(x_breaks))
        r0, r1 = radial
        cy, cz = float(origin[r0]), float(origin[r1])
        y0, y1 = float(low[r0]), float(high[r0])
        z0, z1 = float(low[r1]), float(high[r1])
        # Segment boundaries make the square-root cross-section smooth within
        # each y interval, including intersections with the cell's z faces.
        y_breaks = [y0, y1]
        for y in (cy - radius, cy + radius):
            if y0 < y < y1:
                y_breaks.append(y)
        for z in (z0, z1):
            dz = z - cz
            if abs(dz) < radius:
                span = math.sqrt(max(0.0, radius * radius - dz * dz))
                for y in (cy - span, cy + span):
                    if y0 < y < y1:
                        y_breaks.append(y)
        y_breaks = sorted(set(y_breaks))
        cross_points, cross_weights = np.polynomial.legendre.leggauss(order)

        for x0, x1 in pairwise(x_breaks):
            if x1 <= x0:
                continue
            xm = 0.5 * (x0 + x1)
            is_bored = axial_low < xm < axial_high
            for ix, (qx, wx) in enumerate(zip(points_1d, weights_1d, strict=True)):
                x = xm + qx * (x1 - x0) / 2.0
                wx_phys = wx * (x1 - x0) / 2.0
                for ylo, yhi in pairwise(y_breaks):
                    if yhi <= ylo:
                        continue
                    if ylo >= cy - radius - 1e-12 and yhi <= cy + radius + 1e-12:
                        # y=cy+r*sin(theta) removes the square-root endpoint
                        # singularity in the circular slice height.
                        theta0 = math.asin(min(1.0, max(-1.0, (ylo - cy) / radius)))
                        theta1 = math.asin(min(1.0, max(-1.0, (yhi - cy) / radius)))
                        theta = 0.5 * (theta0 + theta1) + cross_points * (
                            (theta1 - theta0) / 2.0
                        )
                        y_values = cy + radius * np.sin(theta)
                        y_weights = (
                            cross_weights
                            * (theta1 - theta0)
                            / 2.0
                            * radius
                            * np.cos(theta)
                        )
                    else:
                        y_values = 0.5 * (ylo + yhi) + cross_points * (
                            (yhi - ylo) / 2.0
                        )
                        y_weights = cross_weights * (yhi - ylo) / 2.0
                    for y, wy_phys in zip(y_values, y_weights, strict=True):
                        z_intervals = [(z0, z1)]
                        if is_bored:
                            dy = y - cy
                            if abs(dy) < radius:
                                span = math.sqrt(max(0.0, radius * radius - dy * dy))
                                hole_low, hole_high = cz - span, cz + span
                                z_intervals = []
                                if min(z1, hole_low) > z0:
                                    z_intervals.append((z0, min(z1, hole_low)))
                                if z1 > max(z0, hole_high):
                                    z_intervals.append((max(z0, hole_high), z1))
                        for zlo, zhi in z_intervals:
                            if zhi <= zlo:
                                continue
                            for qz, wz in zip(cross_points, cross_weights, strict=True):
                                z = 0.5 * (zlo + zhi) + qz * (zhi - zlo) / 2.0
                                wz_phys = wz * (zhi - zlo) / 2.0
                                point = np.empty(3, dtype=float)
                                point[shaft], point[r0], point[r1] = x, y, z
                                physical.append(point.tolist())
                                weights.append(float(wx_phys * wy_phys * wz_phys))
        method = "finite_cylinder_cut_cell_nested_gauss"

    physical_array = np.asarray(physical, dtype=float).reshape((-1, 3))
    weights_array = np.asarray(weights, dtype=float)
    natural_array = (physical_array - center) / half if len(physical_array) else np.empty((0, 3))
    if len(physical_array) and np.any(np.abs(natural_array) > 1.0 + 1e-10):
        raise AssertionError("Generated quadrature point escaped its C3D20 cell")
    metadata = {
        "method": method,
        "order": int(order),
        "exact_void_volume_mm3": float(exact_void_volume),
        "exact_retained_volume_mm3": float(exact_retained_volume),
        "integrated_volume_mm3": float(weights_array.sum()),
        "cell_material_volume_fraction": float(
            exact_retained_volume / np.prod(high - low)
        ),
        "bore_active": bool(bore_active),
        "maximum_axial_plane_roundoff_alignment_mm":float(axial_plane_snap_mm),
    }
    if bore is not None and len(physical_array):
        axial = (physical_array - origin) @ direction
        delta = physical_array - origin
        radial_distance = np.linalg.norm(delta - axial[:, None] * direction, axis=1)
        in_bore_length = (axial >= float(bore["interval_mm"][0])) & (
            axial <= float(bore["interval_mm"][1])
        )
        if np.any(in_bore_length & (radial_distance < radius)):
            raise AssertionError("Material quadrature point lies inside the exact bore")
        candidates = radial_distance[in_bore_length]
        metadata["minimum_bore_clearance_mm"] = (
            float(np.min(candidates - radius)) if len(candidates) else None
        )
    return natural_array, physical_array, weights_array, metadata


def _polynomial_moments(natural: np.ndarray, weights: np.ndarray) -> np.ndarray:
    exponents = np.asarray(list(product(range(5), repeat=3)), dtype=int)
    if not len(natural):
        return np.zeros(len(exponents), dtype=float)
    values = np.prod(
        natural[:, None, :] ** exponents[None, :, :], axis=2
    )
    return np.einsum("i,ij->j", weights, values)


def c3d20_cylinder_cut_rule(
    nodes_mm: Any, bore: dict[str, Any] | None, *, order: int = 12
) -> dict[str, Any]:
    """Return a C3D20 quadrature rule integrated over wood outside one bore.

    ``order`` is the Gauss order in the two bore-radial coordinates.  The
    shaft coordinate keeps three-point Gauss integration. The report compares
    all natural-coordinate monomials with per-axis degree 0 through 4 against
    a 2x radial-order rule; these contain the products needed by the current
    C3D20 stiffness integrand. Callers should retain at least two such levels
    in stress convergence reports.
    """
    if not isinstance(order, int) or order < 3 or order > 64:
        raise ValueError("Radial quadrature order must be an integer in [3, 64]")
    natural, physical, weights, metadata = _raw_rule(nodes_mm, bore, order)
    fine_natural, _, fine_weights, fine_metadata = _raw_rule(
        nodes_mm, bore, min(2 * order, 128)
    )
    exact_volume = metadata["exact_retained_volume_mm3"]
    volume_error = (
        abs(metadata["integrated_volume_mm3"] - exact_volume) / exact_volume
        if exact_volume > 1e-14
        else abs(metadata["integrated_volume_mm3"])
    )
    moment_coarse = _polynomial_moments(natural, weights)
    moment_fine = _polynomial_moments(fine_natural, fine_weights)
    moment_scale = max(exact_volume, 1e-14)
    return {
        "natural_points": natural,
        "physical_points_mm": physical,
        "weights_mm3": weights,
        "report": {
            **metadata,
            "relative_volume_error": float(volume_error),
            "moment_error_vs_2x_order": float(
                np.max(np.abs(moment_coarse - moment_fine), initial=0.0)
                / moment_scale
            ),
            "comparison_order": fine_metadata["order"],
            "integration_point_count": len(weights),
            "exact_integration_point_bore_exclusion": True,
            "stiffness_and_stress_must_share_rule": True,
            "scope": "One finite axis-aligned cylinder in an affine Cartesian C3D20 cell; no joint strength or peak convergence claim.",
        },
    }
