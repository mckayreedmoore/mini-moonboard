"""Fresh, conditional panel transfer for the reviewed thin bolted geometry.

Cubic tensor B-spline Ritz bending/membrane energy, finite Hillman scenario
springs and compression-only finished-wood footprints. This small matrix
method is not a native solve and does not inherit a historical response.
Fixed receivers, zero prestress/friction, assumed seat and fastener properties
remain explicit limits; no scenario establishes physical stiffness bounds.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.interpolate import BSpline
from scipy.linalg import solve

from fea import current_response_materials as material

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
LAYOUT = PACKET / "mixed-offset-rows-shallow-wires-v4.json"
INTEGRATED = PACKET / "integrated-model-v4.json"
LAYOUT_SHA = "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c"
INTEGRATED_SHA = "28bbd2d2fb6f1a93acb441af124c453f04f81e03be551906c633d5acad1d407e"
CAT = 23 / 32 * 25.4
N_PER_LBF = 4.4482216152605
G = 9.80665
PANELS = ("main_lower_left", "main_lower_right", "main_upper_left",
          "main_upper_right", "kicker_left", "kicker_right")
LEGACY_METHOD = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-method-correction.py"
APA_PDF = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/panel-local-net-completion/source-cache/apa-D510C-2012.pdf"
APA_SHA = "6141e0fe02ad0db8ddec20becf2ec25c85accd21c9796e51411d19448e5762ca"
NDS_PDF = ROOT / "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf"
NDS_SHA = "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def scalar_head_reference(thickness: float, seat_depth: float = 3.) -> float:
    """Reuse the authenticated generic equation, not a Hillman capacity."""
    require(sha(NDS_PDF) == NDS_SHA and sha(APA_PDF) == APA_SHA,
            "retained panel reference source differs")
    spec = importlib.util.spec_from_file_location("retained_panel_scalar", LEGACY_METHOD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._nds_head_reference(.50, 9., thickness - seat_depth / 3.)


@dataclass
class SheetBasis:
    width: float
    height: float
    intervals: int = 8

    def __post_init__(self):
        require(min(self.width, self.height) > 0 and self.intervals >= 1,
                "positive sheet dimensions and interval count required")
        self.knots = np.r_[np.zeros(4), np.linspace(0, 1, self.intervals + 1)[1:-1], np.ones(4)]
        self.order = len(self.knots) - 4
        self.size = self.order**2
        self.spline = BSpline(self.knots, np.eye(self.order), 3, extrapolate=False)

    def values(self, points: np.ndarray, dx: int = 0, dy: int = 0) -> np.ndarray:
        xy = np.asarray(points, dtype=float).reshape(-1, 2)
        require(np.all(xy >= -1e-7) and np.all(xy <= [self.width + 1e-7, self.height + 1e-7]),
                "basis query outside sheet")
        a = self.spline(np.clip(xy[:, 0] / self.width, 0, 1), nu=dx) / self.width**dx
        b = self.spline(np.clip(xy[:, 1] / self.height, 0, 1), nu=dy) / self.height**dy
        return np.einsum("qi,qj->qij", a, b).reshape(len(xy), self.size)

    def quadrature(self, order: int = 4) -> tuple[np.ndarray, np.ndarray]:
        z, w = leggauss(order)
        ab = np.linspace(0, 1, self.intervals + 1)
        p = ((ab[:-1, None] + ab[1:, None]) / 2 + np.diff(ab)[:, None] * z / 2).ravel()
        v = (np.diff(ab)[:, None] * w / 2).ravel()
        x, y = np.meshgrid(p * self.width, p * self.height, indexing="ij")
        wx, wy = np.meshgrid(v * self.width, v * self.height, indexing="ij")
        return np.c_[x.ravel(), y.ravel()], (wx * wy).ravel()


def disk_quadrature(center: np.ndarray, radius: float, radial: int = 4,
                    angular: int = 24, inner: float = 0.) -> tuple[np.ndarray, np.ndarray]:
    """Polar Gauss quadrature, exact disk area and first/second moments."""
    z, w = leggauss(radial)
    r = inner + (radius - inner) * (z + 1) / 2
    theta = (np.arange(angular) + .5) * 2 * math.pi / angular
    rr, tt = np.meshgrid(r, theta, indexing="ij")
    xy = center + np.c_[rr.ravel() * np.cos(tt.ravel()), rr.ravel() * np.sin(tt.ravel())]
    weights = np.repeat(w * (radius - inner) / 2 * r, angular) * (2 * math.pi / angular)
    return xy, weights


def plate_matrix(basis: SheetBasis, points: np.ndarray, weights: np.ndarray,
                 thickness: float = CAT, twist_scale: float = 1.) -> np.ndarray:
    """[u,v,w] energy; X is the owner-reported horizontal strength axis.

    Reuse 23/32 family targets even for the 19.05 mm geometry sensitivity.
    Poisson and extension/bending coupling are zero proxies. Twist is the
    homogeneous shear target GA*t²/12, scaled as a declared scenario.
    """
    ex, ey = material.APA_EA[::-1]
    bx, by = material.APA_EI[::-1]
    ga = material.APA_GA
    bt = ga * thickness**2 / 12 * twist_scale
    dx, dy = basis.values(points, 1), basis.values(points, 0, 1)
    dxx, dyy, dxy = basis.values(points, 2), basis.values(points, 0, 2), basis.values(points, 1, 1)
    weighted = lambda a, b: a.T @ (weights[:, None] * b)
    size = basis.size
    k = np.zeros((3 * size, 3 * size))
    k[:size, :size] = ex * weighted(dx, dx) + ga * weighted(dy, dy)
    k[size:2 * size, size:2 * size] = ey * weighted(dy, dy) + ga * weighted(dx, dx)
    k[:size, size:2 * size] = ga * weighted(dy, dx)
    k[size:2 * size, :size] = k[:size, size:2 * size].T
    k[2 * size:, 2 * size:] = bx * weighted(dxx, dxx) + by * weighted(dyy, dyy) + 4 * bt * weighted(dxy, dxy)
    return k


def aperture_matrix(basis: SheetBasis, holes: list[dict], thickness: float,
                    twist_scale: float = 1.) -> tuple[np.ndarray, float]:
    """Subtract full bores and the explicit 3 mm conical-seat scenario.

    Local remaining-thickness EA/D factors use a homogeneous section analogy;
    no actual veneer or countersink pressure distribution is established.
    """
    removed = np.zeros((3 * basis.size, 3 * basis.size))
    area = 0.
    for row in holes:
        center, radius = np.asarray(row["xy_mm"]), row["diameter_mm"] / 2
        xy, weights = disk_quadrature(center, radius)
        require(np.all(xy >= 0) and np.all(xy <= [basis.width, basis.height]),
                "opening crosses rectangular sheet boundary")
        removed += plate_matrix(basis, xy, weights, thickness, twist_scale)
        area += float(weights.sum())
        if row["kind"] == "conditional_screw_clearance":
            xy, weights = disk_quadrature(center, 4.5, inner=radius)
            depth = 3 * (4.5 - np.linalg.norm(xy - center, axis=1)) / (4.5 - radius)
            membrane = plate_matrix(basis, xy, weights * depth / thickness, thickness, twist_scale)
            bending = plate_matrix(basis, xy, weights * (1 - (1 - depth / thickness)**3), thickness, twist_scale)
            n = 2 * basis.size
            removed[:n, :n] += membrane[:n, :n]
            removed[n:, n:] += bending[n:, n:]
    return removed, area


def port_rows(basis: SheetBasis, points: np.ndarray, z: float = 0.) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Port displacement rows: u-z*wx, v-z*wy and outward w."""
    b = basis.values(points)
    zero = np.zeros_like(b)
    return (np.c_[b, zero, -z * basis.values(points, 1)],
            np.c_[zero, b, -z * basis.values(points, 0, 1)], np.c_[zero, zero, b])


def positive_spring_solve(k: np.ndarray, f: np.ndarray, rows: np.ndarray,
                          stiffness: np.ndarray) -> dict:
    """Convex tension-only spring/contact energy with damped Newton steps.

    A compression row is the negative outward displacement row. Returned
    spring magnitudes are nonnegative. Initialization is bilateral; energy,
    gradient and active-set laws are checked at the converged state.
    """
    require(np.all(stiffness > 0), "positive port stiffness required")
    bilateral = k + rows.T @ (stiffness[:, None] * rows)
    q = solve(bilateral, f, assume_a="pos")

    def fields(q):
        d = rows @ q
        p = stiffness * np.maximum(d, 0)
        grad = k @ q + rows.T @ p - f
        energy = .5 * q @ k @ q + .5 * np.dot(stiffness, np.maximum(d, 0)**2) - f @ q
        return d, p, grad, float(energy)

    for iteration in range(100):
        d, p, grad, energy = fields(q)
        if np.max(np.abs(grad)) <= 1e-7 * max(1., np.max(np.abs(f))):
            break
        active = d > 0
        tangent = k + rows[active].T @ (stiffness[active, None] * rows[active])
        step = solve(tangent, -grad, assume_a="pos")
        alpha = 1.
        slope = float(grad @ step)
        while alpha >= 2**-30:
            candidate = q + alpha * step
            if fields(candidate)[3] <= energy + 1e-4 * alpha * slope + 1e-10:
                q = candidate
                break
            alpha /= 2
        else:
            raise ValueError("contact Newton line search failed")
    else:
        raise ValueError("contact active set failed to converge")
    d, p, grad, energy = fields(q)
    return {"q": q, "port_displacement_mm": d, "port_force_n": p,
            "iterations": iteration + 1, "gradient_inf_n": float(np.max(np.abs(grad))),
            "energy_nmm": energy, "active_ports": int(np.count_nonzero(d > 0))}


def planar_footprint(shape, inward: np.ndarray, backplane: float) -> list[np.ndarray]:
    """Exact CAD planar receiver faces; tessellation only integrates their area."""
    triangles = []
    for face in shape.Faces():
        if face.geomType() != "PLANE":
            continue
        normal = np.asarray(face.normalAt().toTuple())
        center = np.asarray(face.Center().toTuple())
        if abs(normal @ inward) < .999999 or abs(center @ inward - backplane) > 1e-5:
            continue
        vertices, topology = face.tessellate(.1, .1)
        points = np.asarray([v.toTuple() for v in vertices])
        triangles.extend(points[list(t)] for t in topology)
    return triangles


def clip_polygon(polygon: np.ndarray, width: float, height: float) -> np.ndarray:
    """Clip a projected receiver triangle to the retained rectangular sheet."""
    out = list(polygon)
    for axis, value, sign in ((0, 0., 1), (0, width, -1), (1, 0., 1), (1, height, -1)):
        previous = out
        out = []
        if not previous:
            break
        for a, b in zip(previous, previous[1:] + previous[:1], strict=True):
            ia, ib = sign * (a[axis] - value) >= -1e-9, sign * (b[axis] - value) >= -1e-9
            if ia:
                out.append(a)
            if ia != ib:
                out.append(a + (b - a) * (value - a[axis]) / (b[axis] - a[axis]))
    return np.asarray(out)


def footprint_quadrature(triangles: list[np.ndarray], origin: np.ndarray,
                         axes: np.ndarray, width: float, height: float,
                         maximum_edge: float = 70.) -> tuple[np.ndarray, np.ndarray]:
    """Area-preserving subdivision and degree-two triangle integration."""
    points, weights = [], []
    barycentric = np.array([[2 / 3, 1 / 6, 1 / 6], [1 / 6, 2 / 3, 1 / 6], [1 / 6, 1 / 6, 2 / 3]])

    def add(tri):
        lengths = np.linalg.norm(np.roll(tri, -1, axis=0) - tri, axis=1)
        if lengths.max() > maximum_edge:
            edge = int(lengths.argmax())
            a, b, c = tri[edge], tri[(edge + 1) % 3], tri[(edge + 2) % 3]
            midpoint = (a + b) / 2
            add(np.array([a, midpoint, c]))
            add(np.array([midpoint, b, c]))
            return
        area = abs(float(np.linalg.det(np.c_[tri[1] - tri[0], tri[2] - tri[0]]))) / 2
        if area > 1e-8:
            points.extend(barycentric @ tri)
            weights.extend([area / 3] * 3)

    for triangle in triangles:
        xy = (triangle - origin) @ axes[:, :2]
        polygon = clip_polygon(xy, width, height)
        for i in range(1, len(polygon) - 1):
            add(np.array([polygon[0], polygon[i], polygon[i + 1]]))
    return np.asarray(points).reshape(-1, 2), np.asarray(weights)


def compress_quadrature(points: np.ndarray, area: np.ndarray, cell: float) -> tuple[np.ndarray, np.ndarray]:
    """Preserve footprint area/centroid while limiting shared matrix size.

    Per-cell centroid integration is a controllable quadrature approximation,
    not an exact pressure solution. Halve cell size for convergence checks.
    """
    if not len(area):
        return points, area
    cells = np.floor(points / cell).astype(int)
    _, inverse = np.unique(cells, axis=0, return_inverse=True)
    weights = np.bincount(inverse, weights=area)
    xy = np.c_[np.bincount(inverse, weights=area * points[:, 0]),
               np.bincount(inverse, weights=area * points[:, 1])] / weights[:, None]
    return xy, weights


def read_sources() -> tuple[dict, dict, dict]:
    require(sha(LAYOUT) == LAYOUT_SHA and sha(INTEGRATED) == INTEGRATED_SHA,
            "reviewed geometry reports differ")
    layout, integrated = json.loads(LAYOUT.read_text()), json.loads(INTEGRATED.read_text())
    for path, expected in integrated["source_sha256"].items():
        require(sha(ROOT / path) == expected, f"integrated producer/source differs: {path}")
    require(len(layout["screw_axes"]) == 66 and all(s["full_receiver_bodies"] == 66 for s in integrated["panel_screw_receiver_support"]),
            "retained 66 full receiver bodies required")
    contract = json.loads((ROOT / "thin-bolted-candidate.json").read_text())
    require(contract["load_basis"] == {"climber_weight_lb": 250, "downward_multiplier": 2,
                                      "horizontal_force_N": 300, "hold_lever_mm": 100,
                                      "floor_no_slip_assumed": True, "floor_no_slip_verified": False},
            "load contract differs")
    return layout, integrated, contract


def load_cases(integrated: dict) -> list[dict]:
    features = {r["identity"]: r for r in integrated["panel_machining"]["features"]}
    cases = [{"id": "permanent", "hold": None, "force_n": [0., 0., 0.]}]
    for case_id, hold, horizontal in (("a12-rear", "A12", [0., 300., 0.]),
                                     ("a12-forward", "A12", [0., -300., 0.]),
                                     ("a12-left", "A12", [-300., 0., 0.]),
                                     ("k12-right", "K12", [300., 0., 0.]),
                                     ("k12-rear", "K12", [0., 300., 0.]),
                                     ("a1-rear", "A1", [0., 300., 0.])):
        row = features["hold_tnut_main_" + hold]
        force = np.asarray(horizontal) + [0., 0., -250 * 2 * N_PER_LBF]
        cases.append({"id": case_id,
                      "hold": row, "force_n": force.tolist()})
    return cases


def load_geometry(path: Path) -> tuple[dict, dict, dict]:
    import cadquery as cq

    record = json.loads(path.read_text())
    wood, outlines = {}, {}
    for rows, target in ((record["parts"], wood), (record["panel_outline_parts"], outlines)):
        for row in rows:
            name = row["id"].removeprefix("outline_")
            if name not in PANELS and row["kind"] != "timber":
                continue
            source = ROOT / row["path"]
            require(sha(source) == row["sha256"], f"exact geometry cache differs: {row['id']}")
            target[name] = cq.Shape.importBrep(str(source))
    require(len(wood) == 26 and len(outlines) == 6, "complete finished wood/outline cache required")
    return record, wood, outlines


def rectangle_geometry(name: str, outline, screw: dict) -> dict:
    inward = np.asarray(screw["direction_xyz"], dtype=float)
    inward /= np.linalg.norm(inward)
    x = np.array([1., 0., 0.])
    y = np.array([0., math.sin(math.radians(40)), math.cos(math.radians(40))]) if name.startswith("main_") else np.array([0., 0., 1.])
    axes = np.column_stack((x, y, -inward))
    vertices = np.asarray([v.Center().toTuple() for v in outline.Vertices()])
    projections = vertices @ np.column_stack((x, y, inward))
    low, high = projections.min(axis=0), projections.max(axis=0)
    origin = low[0] * x + low[1] * y + (low[2] + CAT / 2) * inward
    front = np.abs(projections[:, 2] - low[2]) < 1e-5
    return {"name": name, "origin": origin, "axes": axes, "inward": inward,
            "width": high[0] - low[0], "height": high[1] - low[1],
            "backplane": high[2], "frontplane": low[2],
            "front_height": projections[front, 1].max() - low[1],
            "thickness": high[2] - low[2]}


def local_xy(point, geometry):
    return (np.asarray(point) - geometry["origin"]) @ geometry["axes"][:, :2]


def bevel_quadrature(basis: SheetBasis, start: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Exact top bevel geometry represented as a variable-thickness plate."""
    if basis.height - start < 1e-7:
        return np.empty((0, 2)), np.empty(0), np.empty(0)
    z, w = leggauss(6)
    xs = np.linspace(0, basis.width, basis.intervals + 1)
    ys = np.r_[start, np.linspace(0, basis.height, basis.intervals + 1)]
    ys = np.unique(ys[ys >= start])
    points, weights = [], []
    for a, b in pairwise(xs):
        for c, d in pairwise(ys):
            xx, yy = np.meshgrid((a + b) / 2 + (b - a) / 2 * z,
                                  (c + d) / 2 + (d - c) / 2 * z, indexing="ij")
            ww = np.outer(w, w) * (b - a) * (d - c) / 4
            points.extend(np.c_[xx.ravel(), yy.ravel()])
            weights.extend(ww.ravel())
    xy, weights = np.asarray(points), np.asarray(weights)
    remaining = (basis.height - xy[:, 1]) / (basis.height - start)
    return xy, weights, remaining


def assemble_panel(name: str, wood: dict, outline, layout: dict, integrated: dict,
                   intervals: int, thickness: float, twist_scale: float,
                   contact_edge: float) -> dict:
    screws = [row for row in layout["screw_axes"] if row["panel"] == name]
    geometry = rectangle_geometry(name, outline, screws[0])
    require(abs(geometry["thickness"] - CAT) < 1e-5, "geometry cache panel category differs")
    basis = SheetBasis(geometry["width"], geometry["height"], intervals)
    holes = [{**row, "xy_mm": local_xy(row["start_xyz_mm"], geometry).tolist()}
             for row in integrated["panel_machining"]["features"] if row["panel"] == name]
    points, weights = basis.quadrature()
    k = plate_matrix(basis, points, weights, thickness, twist_scale)
    remove, hole_area = aperture_matrix(basis, holes, thickness, twist_scale)
    k -= remove
    bevel_xy, bevel_weights, remaining = bevel_quadrature(basis, geometry["front_height"])
    if len(bevel_weights):
        membrane = plate_matrix(basis, bevel_xy, bevel_weights * (1 - remaining), thickness, twist_scale)
        bending = plate_matrix(basis, bevel_xy, bevel_weights * (1 - remaining**3), thickness, twist_scale)
        n = 2 * basis.size
        k[:n, :n] -= membrane[:n, :n]
        k[n:, n:] -= bending[n:, n:]
    k = (k + k.T) / 2
    contacts, areas, owners = [], [], []
    support_bounds = []
    for receiver in sorted(name for name in wood if name not in PANELS):
        triangles = planar_footprint(wood[receiver], geometry["inward"], geometry["backplane"])
        xy, area = footprint_quadrature(triangles, geometry["origin"], geometry["axes"],
                                       basis.width, basis.height, contact_edge)
        if not len(area):
            continue
        keep = np.ones(len(area), dtype=bool)
        for hole in holes:
            keep &= np.linalg.norm(xy - hole["xy_mm"], axis=1) >= hole["diameter_mm"] / 2
        xy, area = xy[keep], area[keep]
        if len(area):
            projected_vertices = np.concatenate(triangles) - geometry["origin"]
            projected_xy = projected_vertices @ geometry["axes"][:, :2]
            projected_xy = np.clip(projected_xy, [0., 0.], [basis.width, basis.height])
            support_bounds.append({"receiver": receiver, "area_mm2": float(area.sum()),
                                   "quadrature_bounds_xy_mm": [*xy.min(axis=0).tolist(), *xy.max(axis=0).tolist()],
                                   "face_bounds_xy_mm": [*projected_xy.min(axis=0).tolist(), *projected_xy.max(axis=0).tolist()]})
        xy, area = compress_quadrature(xy, area, contact_edge)
        contacts.extend(xy)
        areas.extend(area)
        owners.extend([receiver] * len(area))
    contact_xy, contact_area = np.asarray(contacts), np.asarray(areas)
    require(len(contact_area) > 0, f"missing compression footprint: {name}")
    screw_xy = np.asarray([local_xy(r["origin_xyz_mm"], geometry) for r in screws])
    screw_u, screw_v, screw_w = port_rows(basis, screw_xy)
    # Axial screw head force averages the declared projected annulus; no
    # fictitious point restraint is added in the open screw bore.
    for i, xy in enumerate(screw_xy):
        annulus, annular_area = disk_quadrature(xy, 4.5, inner=2.5)
        screw_w[i, 2 * basis.size:] = annular_area @ basis.values(annulus) / annular_area.sum()
    contact_w = port_rows(basis, contact_xy)[2]
    mass_points, mass_weights = [points], [weights]
    mass_row = weights @ basis.values(points)
    for hole in holes:
        xy, area = disk_quadrature(np.asarray(hole["xy_mm"]), hole["diameter_mm"] / 2)
        mass_row -= area @ basis.values(xy)
        mass_points.append(xy)
        mass_weights.append(-area)
    if len(bevel_weights):
        mass_row -= (bevel_weights * (1 - remaining)) @ basis.values(bevel_xy)
        mass_points.append(bevel_xy)
        mass_weights.append(-bevel_weights * (1 - remaining))
    mass_row /= mass_row.sum()
    return {"geometry": geometry, "basis": basis, "K": k,
            "screws": screws, "holes": holes, "screw_xy": screw_xy,
            "screw_u": screw_u, "screw_v": screw_v, "screw_w": screw_w,
            "contact_w": contact_w, "contact_xy": contact_xy,
            "contact_area": contact_area, "contact_owner": owners,
            "support_bounds": support_bounds, "mass_row": mass_row,
            "mass_xy": np.concatenate(mass_points), "mass_weights": np.concatenate(mass_weights) / sum(a.sum() for a in mass_weights),
            "hole_area_mm2": hole_area, "thickness": thickness,
            "twist_scale": twist_scale}


def point_load(panel: dict, point, force, outward_offset: float) -> tuple[np.ndarray, dict]:
    geometry, basis = panel["geometry"], panel["basis"]
    xy = local_xy(point, geometry)
    require(np.all(xy >= -2.) and np.all(xy <= [basis.width + 2, basis.height + 2]),
            "load is outside its panel")
    # Original accessory X=0 lies within the 3.175 mm center gap. Apply its
    # exact rigid-motion wrench at the nearest retained edge with a dipole.
    clipped = np.clip(xy, [0., 0.], [basis.width, basis.height])
    delta = xy - clipped
    values = basis.values(clipped[None])[0]
    dx, dy = basis.values(clipped[None], 1)[0], basis.values(clipped[None], 0, 1)[0]
    fu, fv, fw = geometry["axes"].T @ np.asarray(force)
    load = np.r_[fu * values, fv * values,
                 fw * values - outward_offset * (fu * dx + fv * dy)]
    load[:basis.size] += fu * (delta[0] * dx + delta[1] * dy)
    load[basis.size:2 * basis.size] += fv * (delta[0] * dx + delta[1] * dy)
    load[2 * basis.size:] += fw * (delta[0] * dx + delta[1] * dy)
    world = geometry["origin"] + geometry["axes"][:, :2] @ xy + outward_offset * geometry["axes"][:, 2]
    return load, {"point_xyz_mm": world.tolist(), "force_n": list(force),
                  "xy_mm": xy.tolist(), "outward_offset_mm": outward_offset,
                  "edge_wrench_translation_mm": delta.tolist()}


def panel_case_load(panel: dict, case: dict, integrated: dict, accessory: str) -> tuple[np.ndarray, list[dict]]:
    name, geometry = panel["geometry"]["name"], panel["geometry"]
    source = next(r for r in integrated["finished_stock"] if r["name"] == name)
    mass = source["volume_mm3"] * 500e-9
    panel_masses = {r["name"]: r["volume_mm3"] * 500e-9 for r in integrated["finished_stock"] if r["name"] in PANELS}
    uniform_mass = mass + (25 * mass / sum(panel_masses.values()) if accessory == "proportional" else 0)
    force = np.array([0., 0., -uniform_mass * G])
    fu, fv, fw = geometry["axes"].T @ force
    f = np.r_[fu * panel["mass_row"], fv * panel["mass_row"], fw * panel["mass_row"]]
    # For full-body rigid-motion balance the integrated source centroid is
    # retained, while the plate mass distribution above handles flexibility.
    loads = [{"point_xyz_mm": source["center_of_mass_xyz_mm"], "force_n": force.tolist(),
              "distribution": "uniform net plate mass and proportional accessories"}]
    if accessory == "original_top" and name.startswith("main_upper_"):
        feature = next(r for r in integrated["panel_machining"]["features"] if r["identity"] == "hold_tnut_main_A12")
        point = np.asarray(feature["start_xyz_mm"])
        point[0] = 0.
        original_rear = point + geometry["inward"] * CAT
        added, description = point_load(panel, original_rear, [0., 0., -12.5 * G], -panel["thickness"] / 2)
        f += added
        loads.append(description)
    if case["hold"] and case["hold"]["panel"] == name:
        added, description = point_load(panel, case["hold"]["start_xyz_mm"], case["force_n"],
                                         100 + panel["thickness"] / 2)
        f += added
        loads.append(description)
    return f, loads


def solve_panel(panel: dict, load: np.ndarray, ka: float, kl: float, foundation: float) -> dict:
    lateral = kl * (panel["screw_u"].T @ panel["screw_u"] + panel["screw_v"].T @ panel["screw_v"])
    rows = np.r_[panel["screw_w"], -panel["contact_w"]]
    stiffness = np.r_[np.full(len(panel["screws"]), ka), foundation * panel["contact_area"]]
    response = positive_spring_solve(panel["K"] + lateral, load, rows, stiffness)
    q, count = response["q"], len(panel["screws"])
    response["screw_axial_n"] = response["port_force_n"][:count]
    response["screw_lateral_uv_n"] = kl * np.c_[panel["screw_u"] @ q, panel["screw_v"] @ q]
    response["compression_n"] = response["port_force_n"][count:]
    return response


def point_matrix(panel: dict, xyz_mm) -> np.ndarray:
    """World displacement matrix for coupled frame assembly at an exact port.

    [u,v,w] coefficients use the panel midplane. Through-thickness points
    retain the Kirchhoff rigid-section arm u-z*wx and v-z*wy; this is not a
    prescribed receiver motion or an added rotational joint stiffness.
    """
    geometry = panel["geometry"]
    delta = np.asarray(xyz_mm) - geometry["origin"]
    xy = delta @ geometry["axes"][:, :2]
    z = float(delta @ geometry["axes"][:, 2])
    local = np.vstack([row[0] for row in port_rows(panel["basis"], xy[None], z)])
    return geometry["axes"] @ local


def prepare_panel_models(geometry_path: Path = PACKET / "native-geometry-v4.json",
                         intervals: int = 8, thickness: float = CAT,
                         twist_scale: float = 1., contact_edge: float = 70.) -> tuple[dict, dict, dict]:
    """Source-authenticated six-panel matrices and physical port identities."""
    layout, integrated, _ = read_sources()
    cache, wood, outlines = load_geometry(geometry_path)
    panels = {name: assemble_panel(name, wood, outlines[name], layout, integrated, intervals,
                                   thickness, twist_scale, contact_edge) for name in PANELS}
    return panels, integrated, cache


def receiver_actions(panel: dict, response: dict, case_id: str) -> tuple[list[dict], list[dict]]:
    geometry = panel["geometry"]
    rows, contacts = [], []
    for row, axial, uv in zip(panel["screws"], response["screw_axial_n"], response["screw_lateral_uv_n"], strict=True):
        force = geometry["axes"] @ np.r_[uv, axial]
        point = np.asarray(row["origin_xyz_mm"]) + geometry["inward"] * CAT / 2
        rows.append({"case_id": case_id, "axis_id": row["axis_id"], "panel": row["panel"],
                     "receiver": row["receiver"], "point_xyz_mm": point.tolist(),
                     "force_on_receiver_n": force.tolist(), "tension_n": float(axial),
                     "lateral_n": float(np.linalg.norm(uv))})
    for xy, force, owner in zip(panel["contact_xy"], response["compression_n"], panel["contact_owner"], strict=True):
        if force <= 1e-8:
            continue
        point = geometry["origin"] + geometry["axes"][:, :2] @ xy - CAT / 2 * geometry["axes"][:, 2]
        contacts.append({"case_id": case_id, "panel": geometry["name"], "receiver": owner,
                         "point_xyz_mm": point.tolist(),
                         "force_on_receiver_n": (-force * geometry["axes"][:, 2]).tolist()})
    return rows, contacts


def balance(panel: dict, screws: list[dict], contacts: list[dict], loads: list[dict]) -> dict:
    origin = panel["geometry"]["origin"]
    force, moment = np.zeros(3), np.zeros(3)
    for rows, sign, key in ((loads, 1, "force_n"), (screws, -1, "force_on_receiver_n"), (contacts, -1, "force_on_receiver_n")):
        for row in rows:
            p, f = np.asarray(row["point_xyz_mm"]), sign * np.asarray(row[key])
            force += f
            moment += np.cross(p - origin, f)
    return {"force_residual_xyz_n": force.tolist(), "moment_residual_xyz_nmm": moment.tolist(),
            "force_residual_norm_n": float(np.linalg.norm(force)),
            "moment_residual_norm_nmm": float(np.linalg.norm(moment)),
            "limit": "mass centroid residual can reflect the variable-thickness plate approximation"}


def summarize_response(panel: dict, response: dict, case_id: str, reference: float) -> dict:
    peak = int(np.argmax(response["screw_axial_n"]))
    axial = float(response["screw_axial_n"][peak])
    lateral = float(np.linalg.norm(response["screw_lateral_uv_n"], axis=1).max())
    required_thread = axial / (2850 * .50**2 * .190 * N_PER_LBF / 25.4)
    return {"case_id": case_id, "panel": panel["geometry"]["name"],
            "peak_tension_n": axial, "witness_axis": panel["screws"][peak]["axis_id"],
            "peak_lateral_n": lateral, "head_ratio_CD1": axial / reference,
            "simultaneous_lateral_at_head_witness_n": float(np.linalg.norm(response["screw_lateral_uv_n"][peak])),
            "head_ratio_conditional_CD1p6": axial / (1.6 * reference),
            "projected_head_annulus_pressure_mpa": axial / (math.pi * (9**2 - 5**2) / 4),
            "generic_wood_screw_required_effective_thread_mm_CD1": required_thread,
            "generic_wood_screw_withdrawal_applicable_to_Hillman": False,
            "gradient_inf_n": response["gradient_inf_n"], "iterations": response["iterations"],
            "active_compression_ports": int(np.count_nonzero(response["compression_n"] > 1e-8))}


def resolved_section_references(panel: dict, q: np.ndarray, sample_count: int = 41) -> dict:
    """Plate moment/shear diagnostics, without local hole/seat acceptance.

    These are sampled continuum strip resultants. The global spline space
    does not resolve each small hole's free boundary or concentrated hold
    contact field; point-load local peaks require footprint/convergence data.
    """
    basis, geometry = panel["basis"], panel["geometry"]
    xx, yy = np.meshgrid(np.linspace(0, basis.width, sample_count),
                          np.linspace(0, basis.height, sample_count), indexing="ij")
    xy = np.c_[xx.ravel(), yy.ravel()]
    keep = np.ones(len(xy), dtype=bool)
    for hole in panel["holes"]:
        keep &= np.linalg.norm(xy - hole["xy_mm"], axis=1) > hole["diameter_mm"] / 2
    keep &= xy[:, 1] <= geometry["front_height"] + 1e-8
    xy = xy[keep]
    w = q[2 * basis.size:]
    bx, by = material.APA_EI[::-1]
    twist = material.APA_GA * panel["thickness"]**2 / 12 * panel["twist_scale"]
    mx = -bx * (basis.values(xy, 2) @ w)
    my = -by * (basis.values(xy, 0, 2) @ w)
    qx = -bx * (basis.values(xy, 3) @ w) - 2 * twist * (basis.values(xy, 1, 2) @ w)
    qy = -by * (basis.values(xy, 0, 3) @ w) - 2 * twist * (basis.values(xy, 2, 1) @ w)
    convert = N_PER_LBF / 304.8
    references = {"bending_x": 775 * 25.4 * convert, "bending_y": 455 * 25.4 * convert,
                  "rolling_x": 350 * convert, "rolling_y": 350 * convert}
    data = {}
    for key, values in (("bending_x", mx), ("bending_y", my), ("rolling_x", qx), ("rolling_y", qy)):
        peak = int(np.argmax(np.abs(values)))
        data[key] = {"peak_abs_resultant": float(abs(values[peak])), "xy_mm": xy[peak].tolist(),
                     "reference_per_mm_width_CD1": references[key],
                     "sampled_ratio_CD1": float(abs(values[peak]) / references[key]),
                     "sampled_ratio_conditional_CD1p6": float(abs(values[peak]) / (1.6 * references[key]))}
    return {"panel": geometry["name"], "sample_count_per_axis": sample_count,
            "status": "SPATIAL_RESOLUTION_DIAGNOSTIC_NOT_LOCAL_CAPACITY_ACCEPTANCE", "components": data,
            "limits": "Third derivatives jump between spline spans; opening-boundary, hold-footprint and head-seat fields are not resolved. No pointwise rolling-shear or punching acceptance follows."}


def edge_transfer_diagnostics(panel: dict, q: np.ndarray, sample_count: int = 41) -> dict:
    """Retained edge regions with no continuous wood strip behind them."""
    name, basis = panel["geometry"]["name"], panel["basis"]
    regions = []
    if name.startswith("main_lower_"):
        row = next(r for r in panel["support_bounds"] if r["receiver"].startswith("base_rail_bottom_"))
        x0, y0, x1, _ = row["face_bounds_xy_mm"]
        regions.append(("free_bottom_between_rim_and_principal", [x0, 0., x1, y0]))
    if name.startswith("kicker_"):
        row = next(r for r in panel["support_bounds"] if r["receiver"].startswith("base_post_center_"))
        x0, _, x1, y1 = row["face_bounds_xy_mm"]
        regions.append(("free_inner_edge_below_header", [x1, 0., basis.width, y1] if name.endswith("left") else [0., 0., x0, y1]))
    results = []
    w = q[2 * basis.size:]
    bx, by = material.APA_EI[::-1]
    for region, bounds in regions:
        x0, y0, x1, y1 = bounds
        xx, yy = np.meshgrid(np.linspace(x0, x1, sample_count), np.linspace(y0, y1, sample_count), indexing="ij")
        xy = np.c_[xx.ravel(), yy.ravel()]
        keep = np.ones(len(xy), dtype=bool)
        for hole in panel["holes"]:
            keep &= np.linalg.norm(xy - hole["xy_mm"], axis=1) > hole["diameter_mm"] / 2
        xy = xy[keep]
        mx, my = -bx * (basis.values(xy, 2) @ w), -by * (basis.values(xy, 0, 2) @ w)
        displacement = basis.values(xy) @ w
        results.append({"region": region, "bounds_xy_mm": bounds, "region_height_mm": y1 - y0,
                        "region_width_mm": x1 - x0, "maximum_outward_displacement_mm": float(displacement.max()),
                        "minimum_outward_displacement_mm": float(displacement.min()),
                        "sampled_bending_x_ratio_CD1": float(np.abs(mx).max() / (775 * 25.4 * N_PER_LBF / 304.8)),
                        "sampled_bending_y_ratio_CD1": float(np.abs(my).max() / (455 * 25.4 * N_PER_LBF / 304.8))})
    return {"panel": name, "regions": results,
            "status": "CONDITIONAL_GLOBAL_PLATE_EDGE_TRANSFER_NOT_LOCAL_EDGE_RUPTURE_ACCEPTANCE"}


def net_intervals(panel: dict, direction: int, cut: float) -> list[tuple[float, float]]:
    """Actual current full-bore chords at a cut, preserving separate voids."""
    width = panel["basis"].height if direction == 0 else panel["basis"].width
    intervals = [(0., width)]
    for hole in panel["holes"]:
        center = hole["xy_mm"]
        offset = cut - center[direction]
        radius = hole["diameter_mm"] / 2
        if abs(offset) >= radius:
            continue
        chord = math.sqrt(radius**2 - offset**2)
        a, b = center[1 - direction] - chord, center[1 - direction] + chord
        result = []
        for low, high in intervals:
            if b <= low or a >= high:
                result.append((low, high))
            else:
                if low < a:
                    result.append((low, a))
                if b < high:
                    result.append((b, high))
        intervals = result
    return intervals


def equilibrium_cut_references(panel: dict, screws: list[dict], contacts: list[dict],
                                external: list[dict], count: int = 41) -> dict:
    """Necessary aggregate net-section demand indices from fresh actions.

    A mean resultant below the reference is not a local stress pass. These
    cuts cannot assign a screw edge-out/punching capacity or hide moment
    concentration. Full-bores reduce width; the conical seat remains local.
    """
    geometry = panel["geometry"]
    positions, forces = [], []
    for row in external:
        if "distribution" in row:
            world = geometry["origin"] + panel["mass_xy"] @ geometry["axes"][:, :2].T
            positions.extend(world)
            forces.extend(panel["mass_weights"][:, None] * np.asarray(row["force_n"]))
        else:
            positions.append(row["point_xyz_mm"])
            forces.append(row["force_n"])
    for row in screws + contacts:
        positions.append(row["point_xyz_mm"])
        forces.append(-np.asarray(row["force_on_receiver_n"]))
    positions, forces = np.asarray(positions), np.asarray(forces)
    xy = (positions - geometry["origin"]) @ geometry["axes"][:, :2]
    results = []
    convert = N_PER_LBF / 304.8
    for direction in (0, 1):
        length = panel["basis"].width if direction == 0 else panel["basis"].height
        cuts = np.r_[np.linspace(.001, length - .001, count),
                     [r["xy_mm"][direction] for r in panel["holes"]]]
        for cut in np.unique(cuts):
            intervals = net_intervals(panel, direction, cut)
            net_width = sum(b - a for a, b in intervals)
            centroid = sum((b**2 - a**2) / 2 for a, b in intervals) / net_width
            local = np.zeros(2)
            local[direction], local[1 - direction] = cut, centroid
            center = geometry["origin"] + geometry["axes"][:, :2] @ local
            selected = xy[:, direction] < cut
            resultant = forces[selected].sum(axis=0)
            moment = np.cross(positions[selected] - center, forces[selected]).sum(axis=0)
            bending = abs(float(moment @ geometry["axes"][:, 1 - direction]))
            rolling = abs(float(resultant @ geometry["axes"][:, 2]))
            axial = -float(resultant @ geometry["axes"][:, direction])
            fb = (775 if direction == 0 else 455) * 25.4 * convert
            fs = 350 * convert
            ft = (5100 if direction == 0 else 3400) * convert
            fc = (4800 if direction == 0 else 2900) * convert
            results.append({"cut_axis": "x" if direction == 0 else "upslope", "cut_coordinate_mm": float(cut),
                            "net_full_bore_width_mm": net_width, "normal_bending_resultant_nmm": bending,
                            "outward_shear_resultant_n": rolling, "signed_in_plane_axial_n": axial,
                            "mean_net_bending_ratio_CD1": bending / (fb * net_width),
                            "mean_net_rolling_shear_ratio_CD1": rolling / (fs * net_width),
                            "mean_net_axial_ratio_CD1": abs(axial) / ((ft if axial >= 0 else fc) * net_width)})
    maxima = {key: max(results, key=lambda r: r[key]) for key in
              ("mean_net_bending_ratio_CD1", "mean_net_rolling_shear_ratio_CD1", "mean_net_axial_ratio_CD1")}
    return {"panel": geometry["name"], "cut_count": len(results), "necessary_mean_resultant_maxima": maxima,
            "status": "NECESSARY_AGGREGATE_REFERENCE_ONLY", "local_panel_resistance_accepted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, default=PACKET / "native-geometry-v4.json")
    parser.add_argument("--intervals", type=int, default=8)
    parser.add_argument("--stiffnesses", type=float, nargs="+", default=[100., 1000., 10000.])
    parser.add_argument("--foundation", type=float, default=2.)
    parser.add_argument("--thickness", type=float, choices=[CAT, 19.05], default=CAT)
    parser.add_argument("--twist-scale", type=float, default=1.)
    parser.add_argument("--contact-edge", type=float, default=70.)
    parser.add_argument("--accessory", choices=["original_top", "proportional"], default="original_top")
    parser.add_argument("--export-operators", type=Path)
    parser.add_argument("--output", type=Path, default=PACKET / "panel-mechanics-v4.json")
    args = parser.parse_args()
    layout, integrated, contract = read_sources()
    _cache, wood, outlines = load_geometry(args.geometry)
    reference = scalar_head_reference(args.thickness)
    cases = load_cases(integrated)
    panels = {name: assemble_panel(name, wood, outlines[name], layout, integrated, args.intervals,
                                   args.thickness, args.twist_scale, args.contact_edge) for name in PANELS}
    if args.export_operators:
        arrays, identities = {}, {}
        for name, panel in panels.items():
            for key in ("K", "screw_u", "screw_v", "screw_w", "contact_w", "contact_xy", "contact_area"):
                arrays[f"{name}/{key}"] = panel[key]
            arrays[f"{name}/contact_points_xyz_mm"] = panel["geometry"]["origin"] + panel["contact_xy"] @ panel["geometry"]["axes"][:, :2].T - CAT / 2 * panel["geometry"]["axes"][:, 2]
            for case in cases:
                arrays[f"{name}/load/{case['id']}"] = panel_case_load(panel, case, integrated, args.accessory)[0]
            identities[name] = {"screw_axes": [r["axis_id"] for r in panel["screws"]],
                                "screw_receivers": [r["receiver"] for r in panel["screws"]],
                                "contact_receivers": panel["contact_owner"],
                                "origin_xyz_mm": panel["geometry"]["origin"].tolist(),
                                "local_axes_columns_xyz": panel["geometry"]["axes"].tolist(),
                                "basis_order": "u,v,outward_w; tensor x-major/y-minor", "basis_size": panel["basis"].size}
        args.export_operators.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(args.export_operators, **arrays)
        args.export_operators.with_suffix(".json").write_text(json.dumps(identities, indent=2) + "\n")
    summaries, receiver_rows, contact_summaries = [], [], []
    for stiffness in args.stiffnesses:
        for case in cases:
            for panel in panels.values():
                load, external = panel_case_load(panel, case, integrated, args.accessory)
                response = solve_panel(panel, load, stiffness, stiffness, args.foundation)
                screws, contacts = receiver_actions(panel, response, case["id"])
                summary = summarize_response(panel, response, case["id"], reference)
                summary.update({"axial_stiffness_n_per_mm": stiffness, "lateral_stiffness_n_per_mm": stiffness,
                                "balance": balance(panel, screws, contacts, external),
                                "resolved_section_diagnostics": resolved_section_references(panel, response["q"]),
                                "edge_transfer_diagnostics": edge_transfer_diagnostics(panel, response["q"]),
                                "net_section_equilibrium": equilibrium_cut_references(panel, screws, contacts, external)})
                summaries.append(summary)
                if stiffness == 1000.:
                    receiver_rows.extend(screws)
                    for owner in sorted({r["receiver"] for r in contacts}):
                        owned = [r for r in contacts if r["receiver"] == owner]
                        force = sum((np.asarray(r["force_on_receiver_n"]) for r in owned), np.zeros(3))
                        moment = sum((np.cross(r["point_xyz_mm"], r["force_on_receiver_n"]) for r in owned), np.zeros(3))
                        contact_summaries.append({"case_id": case["id"], "panel": panel["geometry"]["name"], "receiver": owner,
                                                  "force_on_receiver_n": force.tolist(), "moment_on_receiver_about_world_origin_nmm": moment.tolist()})
        print(json.dumps({"stiffness_n_per_mm": stiffness, "completed_panel_states": len(cases) * len(panels)}), flush=True)
    report = {"schema": "thin_bolted_panel_mechanics/v1", "candidate": contract["candidate"],
              "revision": contract["revision"], "status": "CONDITIONAL_FIXED_RECEIVER_METHOD_COMPARISON",
              "inputs": {"panel_thickness_mm": args.thickness, "retained_category_reference_mm": CAT,
                         "head_diameter_mm_owner_report": 9., "head_height_mm_unmeasured_scenario": 3.,
                         "screw_body_diameter_mm_unmeasured_scenario": 5., "Hillman_product": "42605 #10 x 2.5 in",
                         "strength_axis_global_xyz": [1., 0., 0.], "screw_stiffness_scenarios_n_per_mm": args.stiffnesses,
                         "foundation_n_per_mm3_scenario": args.foundation, "twist_scale_scenario": args.twist_scale,
                         "accessory_distribution": args.accessory, "accessory_mass_kg": 25., "panel_density_kg_per_m3_scenario": 500.,
                         "intervals": args.intervals, "contact_maximum_triangle_edge_mm": args.contact_edge,
                         "head_reference_CD1_n": reference, "load_basis": contract["load_basis"]},
              "head_reference_thickness_scenarios": {"CAT_23_32_18p25625mm_unmeasured_3mm_seat_CD1_N": scalar_head_reference(CAT),
                                                    "owner_nominal_19p05mm_unmeasured_3mm_seat_CD1_N": scalar_head_reference(19.05),
                                                    "scope": "Separate reference sensitivities; each uses net thickness t-3/3. Forces cannot be assumed unchanged by actual thickness variation."},
              "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in (LAYOUT, INTEGRATED, args.geometry, Path(__file__),
                                                                              LEGACY_METHOD, APA_PDF, NDS_PDF, Path(material.__file__),
                                                                              ROOT / "scripts/clear_space_batch.py")},
              "geometry_cache_sha256": sha(args.geometry), "native_execution": False,
              "panel_geometry": [{"panel": name, "width_mm": panel["basis"].width, "height_mm": panel["basis"].height,
                                  "front_height_mm": panel["geometry"]["front_height"], "screw_count": len(panel["screws"]),
                                  "compression_quadrature_count": len(panel["contact_area"]), "support_footprints": panel["support_bounds"],
                                  "opening_area_mm2": panel["hole_area_mm2"]} for name, panel in panels.items()],
              "responses": summaries, "fixed_receiver_screw_actions_1000N_per_mm": receiver_rows,
              "fixed_receiver_compression_wrenches_1000N_per_mm": contact_summaries,
              "references": {"APA_current_catalog": "https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/",
                             "APA_authored_2020_PDF": "https://wood.tcaup.umich.edu/lectures/2021/D510.pdf",
                             "AWC_NDS2024": "https://awc.org/resources/2024-nds/",
                             "AWC_head_model": "https://web-media.awc.org/wp-content/uploads/2021/12/17210650/2018-nds-head-pull-through-paper.pdf"},
              "limits": ["Fixed receivers; surrounding frame/bolt/fitting compatibility not included. These actions cannot be used as complete coupled frame demands.",
                         "Stiffness scenarios are unmeasured examples, not physical bounds; zero initial gap/preload and zero support friction.",
                         "23/32 Group1 A-C dry family membrane/bending references, zero Poisson coupling, GA*t²/12 twist proxy; actual layup/constants unknown.",
                         "Variable-thickness kicker bevel uses a plate section analogy; extension/bending coupling from the eccentric beveled section is omitted.",
                         "Uniform annular head displacement and midpoint lateral bearing are explicit contact proxies; no Hillman product capacity, screw root/yield strength or withdrawal installation qualification.",
                         "Generic pull-through is distinct from conical-seat radial thrust/indentation; projected pressure is descriptive and APA360psi is a deformation reference.",
                         "No independent screw-head punching, loaded-edge rupture or two-ray edge-out capacity is assigned.",
                         "Point hold loading preserves the 100mm lever, but actual hold contact footprint and bolt/T-nut local transfer remain missing for local peak stress resistance.",
                         "All physical observations and release flags remain false; no geometry changes or new screws."],
              "release": {key: False for key in ("candidate_accepted", "complete_joint_acceptance", "capacity_established", "fabrication_released", "structural_released", "climbing_released")}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output), "maximum_head_ratio_CD1": max(r["head_ratio_CD1"] for r in summaries),
                      "maximum_fixed_receiver_tension_n": max(r["peak_tension_n"] for r in summaries)}))


if __name__ == "__main__":
    main()
