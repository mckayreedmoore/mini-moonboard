"""Authenticate finished floor ports and reuse the frozen JSON equilibrium audit.

No CAD query or solve is performed. Passing authenticates this conditional
model's exported support geometry and arithmetic, not an actual floor,
physical stiffness, component resistance or structural acceptance.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from scripts import thin_bolted_equilibrium_audit as arithmetic

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
CONTACT_PATH = PACKET / "frame-contact-geometry-v4.json"
CONTACT_SHA = "e6c7ac4548b943bef4580b7c58efd67c11e29ed3335ae4036998a70c346986fc"
CACHE_PATH = PACKET / "native-geometry-v4.json"
CACHE_SHA = "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9"
ARITHMETIC_SHA = "748f637b918bf9b7faca673cb2e723c8dbb8f98bc4a2d3fd5b12987c20980b84"
FLOOR_BASIS = "authenticated-finished-timber-horizontal-faces"
FLOOR_HOSTS = {
    "base_floor_left", "base_floor_right", "base_post_center_left",
    "base_post_center_right", "base_post_outer_left", "base_post_outer_right",
    "lumber_leg_left", "lumber_leg_right",
}
POINT_TOLERANCE_MM = 1e-5


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_scalar(value) -> float:
    value = float(value)
    if not np.isfinite(value):
        raise ValueError("finite scalar required")
    return value


def rectangle_polygon(points, *, ordered: bool = True) -> np.ndarray:
    """Require the four real vertices of one horizontal axis-aligned rectangle."""
    array = np.asarray(points, dtype=float)
    if array.shape != (4, 3) or not np.isfinite(array).all() or np.max(abs(array[:, 2])) > POINT_TOLERANCE_MM:
        raise ValueError("four finite horizontal floor vertices at z=0 required")
    low, high = array[:, :2].min(axis=0), array[:, :2].max(axis=0)
    if np.any(high - low <= POINT_TOLERANCE_MM):
        raise ValueError("positive rectangular floor bearing area required")
    corners = np.array([(x, y) for x in (low[0], high[0]) for y in (low[1], high[1])])
    matches = np.linalg.norm(array[:, None, :2] - corners[None, :, :], axis=2) <= POINT_TOLERANCE_MM
    if not np.all(matches.sum(axis=0) == 1) or not np.all(matches.sum(axis=1) == 1):
        raise ValueError("floor vertices do not describe one rectangle")
    if ordered:
        # Each perimeter edge changes exactly one XY coordinate. A diagonal
        # exposes crossed or unordered corner lists, even if their hull agrees.
        delta = np.roll(array, -1, axis=0)[:, :2] - array[:, :2]
        if not np.all((abs(delta) > POINT_TOLERANCE_MM).sum(axis=1) == 1):
            raise ValueError("floor polygon must follow its perimeter")
    return array


def inside_rectangle(point, polygon) -> bool:
    point = arithmetic.vector(point)
    polygon = rectangle_polygon(polygon)
    return bool(abs(point[2]) <= POINT_TOLERANCE_MM
                and np.all(point[:2] >= polygon[:, :2].min(axis=0) - POINT_TOLERANCE_MM)
                and np.all(point[:2] <= polygon[:, :2].max(axis=0) + POINT_TOLERANCE_MM))


def read_authenticated_sources() -> tuple[dict, dict, dict]:
    pins = {str(CONTACT_PATH.relative_to(ROOT)): CONTACT_SHA,
            str(CACHE_PATH.relative_to(ROOT)): CACHE_SHA,
            str(Path(arithmetic.__file__).relative_to(ROOT)): ARITHMETIC_SHA}
    for name, expected in pins.items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"preserve frozen support/audit input: {name}")
    contact, cache = json.loads(CONTACT_PATH.read_text()), json.loads(CACHE_PATH.read_text())
    if (contact["geometry_cache_sha256"] != CACHE_SHA
            or contact["layout_report_sha256"] != arithmetic.PINS["mixed-offset-rows-shallow-wires-v4.json"]
            or contact["candidate"] != cache["candidate"] or contact["unsupported_flange_contacts"]):
        raise ValueError("finished-contact audit leaves frozen candidate scope")
    for name, expected in contact["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"finished-contact source differs: {name}")
        pins[name] = expected
    return contact, cache, pins


def verify_finished_support(demand: dict, contact: dict, cache: dict) -> dict:
    """Validate an authenticated record's eight proofs and every exported port."""
    parameters = demand.get("parameters", {})
    if (parameters.get("floor_support_basis") != FLOOR_BASIS
            or parameters.get("floor_contact_geometry_sha256") != CONTACT_SHA):
        raise ValueError("finished floor basis and authenticated geometry pin required; raw state rejected")
    if (demand.get("candidate") != contact["candidate"]
            or demand.get("geometry_cache_sha256") != CACHE_SHA
            or demand.get("layout_report_sha256") != contact["layout_report_sha256"]):
        raise ValueError("finished-support state leaves frozen candidate inputs")
    identity = {"case_id": demand["case_id"], "accessory_placement": demand["accessory_placement"],
                "parameters": parameters, "geometry_cache_sha256": demand["geometry_cache_sha256"]}
    state_id = "thin-v4-" + hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]
    if demand.get("state_id") != state_id:
        raise ValueError("state identity does not bind finished support parameters")
    reference = contact["finished_floor_footprints"]
    if set(reference) != FLOOR_HOSTS:
        raise ValueError("authenticated record requires all eight finished floor hosts")
    timber = {row["id"]: row for row in cache["parts"] if row["kind"] == "timber"}
    proofs = demand.get("finished_floor_footprints", [])
    by_host = {row["member"]: row for row in proofs}
    if len(proofs) != 8 or len(by_host) != 8 or set(by_host) != FLOOR_HOSTS:
        raise ValueError("all eight unique finished floor proofs required")
    polygons = {}
    for host, proof in by_host.items():
        source = timber[host]
        if (proof["source_brep_path"] != source["path"] or proof["source_brep_sha256"] != source["sha256"]
                or contact["source_sha256"].get(source["path"]) != source["sha256"]):
            raise ValueError("finished floor BREP provenance differs")
        if len(proof["polygons_xyz_mm"]) != 1:
            raise ValueError("current authenticated host requires its single bearing polygon")
        polygon = rectangle_polygon(proof["polygons_xyz_mm"][0])
        expected = rectangle_polygon(reference[host], ordered=False)
        matches = np.linalg.norm(polygon[:, None, :] - expected[None, :, :], axis=2) <= POINT_TOLERANCE_MM
        if not np.all(matches.sum(axis=0) == 1) or not np.all(matches.sum(axis=1) == 1):
            raise ValueError("finished polygon differs from exact finished timber face")
        area = float(np.prod(polygon[:, :2].max(axis=0) - polygon[:, :2].min(axis=0)))
        if abs(finite_scalar(proof["bearing_area_mm2"]) - area) > 1e-5:
            raise ValueError("finished bearing area differs from authenticated polygon")
        polygons[host] = polygon
    rows = demand.get("floor_actions", [])
    indexed = {row["id"]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError("floor action identities must be unique")
    expected_normals = {host + f"/floor-{i}": (host, point)
                        for host, points in reference.items() for i, point in enumerate(points)}
    normal_rows = {key: row for key, row in indexed.items() if row["kind"] == "floor_normal"}
    if set(normal_rows) != set(expected_normals):
        raise ValueError("all 32 authenticated normal ports, including zero reactions, required")
    resultants = dict.fromkeys(FLOOR_HOSTS, 0.)
    for row in rows:
        host = row["first"]
        if host not in FLOOR_HOSTS or row["second"] != "floor":
            raise ValueError("floor action host differs")
        if (row.get("state_id"), row.get("case_id"), row.get("accessory_placement")) != (
                state_id, demand["case_id"], demand["accessory_placement"]):
            raise ValueError("floor action mixes states or loads")
        if not inside_rectangle(row["point_xyz_mm"], polygons[host]):
            raise ValueError("floor action lies outside its actual finished bearing polygon")
        if np.linalg.norm(arithmetic.vector(row.get("moment_at_point_model_xyz_nmm", [0., 0., 0.]))) > 1e-7:
            raise ValueError("current point-support model does not supply a free floor couple")
        force = arithmetic.vector(row["force_on_first_xyz_n"])
        if row["kind"] == "floor_normal":
            expected_host, point = expected_normals[row["id"]]
            compression = finite_scalar(row["compression_n"])
            if host != expected_host or np.linalg.norm(arithmetic.vector(row["point_xyz_mm"]) - point) > POINT_TOLERANCE_MM:
                raise ValueError("normal floor port differs from its authenticated finished vertex")
            if compression < 0. or np.linalg.norm(force - [0., 0., compression]) > 1e-7:
                raise ValueError("floor normal reaction must be nonnegative and vertical")
            resultants[host] += compression
        elif row["kind"] == "floor_tangent":
            if row["id"] not in {host + "/no-slip-0", host + "/no-slip-1"}:
                raise ValueError("foreign floor tangent identity")
            component = int(row["id"][-1])
            if np.linalg.norm(arithmetic.vector(row["point_xyz_mm"]) - polygons[host].mean(axis=0)) > POINT_TOLERANCE_MM:
                raise ValueError("floor tangent is not at its actual finished face centroid")
            if np.linalg.norm(np.delete(force, component)) > 1e-7:
                raise ValueError("floor tangent force differs from its component axis")
            stiffness = finite_scalar(row["penalty_stiffness_n_mm"])
            displacement = finite_scalar(row["tangent_displacement_mm"])
            if (stiffness <= 0. or stiffness != finite_scalar(parameters["floor_no_slip_xy_penalty_n_mm"])
                    or abs(force[component] + stiffness * displacement) > 1e-7):
                raise ValueError("floor tangent differs from declared conditional penalty law")
        else:
            raise ValueError("foreign floor action kind")
    bearing = {host for host, normal in resultants.items() if normal > 1e-7}
    expected_tangents = {host + f"/no-slip-{i}" for host in bearing for i in (0, 1)}
    actual_tangents = {key for key, row in indexed.items() if row["kind"] == "floor_tangent"}
    if actual_tangents != expected_tangents:
        raise ValueError("centroid no-slip ports require positive host normal bearing")
    if set(demand["response"]["nonbearing_no_slip_removed"]) != FLOOR_HOSTS - bearing:
        raise ValueError("removed no-slip hosts differ from reconstructed normal bearing")
    return {"finished_support_geometry_checks_pass": True, "finished_host_count": 8,
            "normal_port_count": len(normal_rows), "tangent_port_count": len(actual_tangents),
            "bearing_hosts": sorted(bearing), "point_tolerance_mm": POINT_TOLERANCE_MM,
            "floor_support_basis": FLOOR_BASIS, "floor_contact_geometry_sha256": CONTACT_SHA}


def audit_finished_state(demand: dict) -> dict:
    """Raise on support/provenance mismatch; return combined conditional gate."""
    contact, cache, pins = read_authenticated_sources()
    recorded_pins = demand.get("source_sha256", {})
    # The arithmetic helper is independently imported by this gate; its hash is
    # bound in the result. The state binds every geometry-audit dependency.
    for name, expected in pins.items():
        if name != str(Path(arithmetic.__file__).relative_to(ROOT)) and recorded_pins.get(name) != expected:
            raise ValueError(f"state omits authenticated finished-support dependency: {name}")
    support = verify_finished_support(demand, contact, cache)
    response = demand["response"]
    tolerance = finite_scalar(response["generalized_residual_tolerance_n"])
    residual = finite_scalar(response["gradient_inf_n"])
    if (demand.get("usable_conditional_actions") is not True or response.get("converged") is not True
            or not 0. < tolerance <= 1e-5 or not 0. <= residual <= tolerance):
        raise ValueError("conditional actions require the declared bounded unmodified-law convergence gate")
    closure = arithmetic.audit_state(demand)
    if digest(Path(arithmetic.__file__)) != ARITHMETIC_SHA:
        raise ValueError("frozen arithmetic helper changed during support audit")
    return {"independent_finished_support_and_equilibrium_checks_pass":
            bool(support["finished_support_geometry_checks_pass"] and closure["independent_equilibrium_and_contact_checks_pass"]),
            "support": support, "equilibrium": closure, "source_sha256": pins,
            "native_or_CAD_execution": False, "actual_floor_or_physical_stiffness_verified": False,
            "strength_or_structural_acceptance": False}
