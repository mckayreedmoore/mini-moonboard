"""Pure preparation of all source-proved timber compression interfaces.

No geometry query, stiffness assembly, solve or admission is performed.  The
existing first-order point ports/law are reused on all 30 patches.  The small
geometry-only coordinate chart below is a method coupon, never a field state.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import platform
import sys
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import scipy
from scipy.sparse import diags, vstack

from scripts import thin_bolted_linear_timber_faces as linear

faces, frame = linear.faces, linear.frame
OWN = str(Path(__file__).resolve().relative_to(ROOT))
TEST = str(Path(__file__).with_name("test_adapter.py").relative_to(ROOT))
LOADED_SHA256 = frame.sha(Path(__file__))
LOADED_TEST_SHA256 = frame.sha(ROOT / TEST)
BASIS = "source-bound-linear-complete-atlas-wood-compression-v1"
SCENARIO = "complete-atlas-wood-bedding-declared-v1"
SCHEMA = "thin_bolted_complete_timber_contact_preparation/v1"
PACKET = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/"
ATLAS = "fea/generated/thin-bolted-local-joint-ports/all-timber-pair-contact-atlas.json"
DIRECT = "fea/generated/thin-bolted-local-joint-ports/direct-timber-contact.json"
OLD = PACKET + "timber-face-contact-geometry-v4.json"
FRAME_GEOMETRY = PACKET + "compatible-frame-a12-rear-finished-floor-v4.json"
INPUT_SHA256 = {
    ATLAS: "5331d559f5454afc8e35dd86bd5435bf8a7239283e29c5c1f3c193eb6671a420",
    DIRECT: "ead9fee6a06d1233ac4cfd006fb2c681241d6ea2e81ddc410b1e47d9550e7dfa",
    OLD: "be88aeb6754bc03e8afd523f5127f74b93b90bd00e8c3ceaa910e70aab3f125a",
    FRAME_GEOMETRY: "8d90941f9d1cb20d938ddc65992b2db7b0fe0c38420bf6bfc10fc0684281256d",
}
METHOD_SHA256 = {
    "scripts/thin_bolted_linear_timber_faces.py": "6283d85ec2bfacd6d72f0713c662e273201935e09445a6455b86a841de587208",
    "scripts/thin_bolted_frame_mechanics.py": linear.FRAME_SHA,
    "scripts/thin_bolted_timber_face_contact.py": linear.FACE_SHA,
}
LIMITS = [
    "All 30 positive-area reference interfaces at the atlas tolerances are represented; future overlap after slip, near gaps, line/point contacts and interpenetration are not resolved.",
    "Fixed reference normals/points and first-order rigid arms are a declared linear response approximation, not a finite-motion contact operator.",
    "Uniform 1 N/mm^3 bedding is an unmeasured scenario; host grain angles are nominal geometry classifications, not Fc(theta), bearing resistance or joint capacity.",
    "Area and first moments are conserved; centroid cell quadrature does not exactly reproduce the source second moments or bound rocking response.",
    "Compression only, zero reference gap/preload, no tangential friction, axial tie, free point couple or external rotational clamp.",
    "L/u/v are proper geometric grain frames; actual radial/tangential growth-ring orientation is unknown and no orthotropic R/T assignment is adopted.",
    "The geometry-only 240-coordinate coupon reads saved endpoints/frames only: no saved q, loads, forces or acceptance is transferred.",
    "A future complete field requires a new physical signature/state and independent admission; no previous six-interface field pass is inherited.",
]


def require(condition, message):
    faces.require(condition, message)


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def verify_pins(pins):
    for path, expected in pins.items():
        require(frame.sha(ROOT / path) == expected, "complete contact source changed: " + path)


def read_inputs():
    verify_pins(INPUT_SHA256)
    data = {path: json.loads((ROOT / path).read_bytes()) for path in INPUT_SHA256}
    pins = faces.merge_pins(INPUT_SHA256, METHOD_SHA256,
                           {OWN: LOADED_SHA256, TEST: LOADED_TEST_SHA256},
                           *(row["source_sha256"] for row in data.values()))
    pins = linear.source_pins(pins)
    verify_pins(pins)
    atlas = data[ATLAS]
    require(atlas["schema"] == "thin_bolted_all_timber_reference_contact_atlas/v1"
            and atlas["candidate"] == "compact-floor-flush-thin-bolted-development"
            and atlas["reference_positive_area_contact_geometry_enumerated"] is True
            and atlas["complete_contact_response_operator"] is False,
            "exact complete reference atlas required")
    require(data[OLD]["schema"] == faces.PROOF_SCHEMA
            and data[DIRECT]["schema"] == "thin_bolted_local_direct_timber_contact_geometry/v1",
            "distinct old/direct source proof schemas required")
    saved = data[FRAME_GEOMETRY]
    require(saved["candidate"] == atlas["candidate"]
            and saved["layout_report_sha256"] == frame.LAYOUT_SHA
            and saved["geometry_cache_sha256"] == frame.GEOMETRY_CACHE_SHA,
            "saved geometry-only frame source differs")
    require(all(not any(row["release"].values()) for row in data.values()),
            "unreleased source geometry required")
    return data, pins


def grain_geometry(saved, atlas):
    """Consume ONLY member ID, geometric endpoints and L/u/v frame keys."""
    grouped = {}
    for row in saved["member_element_actions"]:
        grouped.setdefault(row["member"], []).append({
            key: copy.deepcopy(row[key]) for key in
            ("element", "start_xyz_mm", "end_xyz_mm", "basis_grain_u_v_xyz")})
    cached = {row["member"]: row for row in atlas["cached_timbers"]}
    require(len(cached) == len(grouped) == 20 and set(cached) == set(grouped),
            "all20 cached/source geometric grain frames required")
    result = {}
    for name in sorted(grouped):
        rows = sorted(grouped[name], key=lambda row: row["element"])
        require([r["element"] for r in rows] == list(range(len(rows))), "geometry element sequence differs")
        basis = np.asarray(rows[0]["basis_grain_u_v_xyz"], dtype=float)
        cached_grain = faces.vector(cached[name]["grain_axis_xyz"])
        require(abs(np.linalg.norm(cached_grain) - 1.) <= 1e-8, "cached nominal grain vector is not unit")
        cached_grain = cached_grain / np.linalg.norm(cached_grain)
        require(basis.shape == (3, 3) and np.isfinite(basis).all()
                and np.max(abs(basis @ basis.T - np.eye(3))) <= 1e-12
                and abs(np.linalg.det(basis) - 1.) <= 1e-12,
                "proper geometric L/u/v grain frame required: " + name)
        require(all(np.array_equal(r["basis_grain_u_v_xyz"], basis) for r in rows)
                and np.linalg.norm(np.cross(basis[0], cached_grain)) <= 1e-8,
                "cached and saved nominal grain axes differ: " + name)
        start, end = faces.vector(rows[0]["start_xyz_mm"]), faces.vector(rows[-1]["end_xyz_mm"])
        length = float((end - start) @ basis[0])
        require(length > 0. and np.linalg.norm(end - start - length * basis[0]) < 1e-6
                and all(np.allclose(a["end_xyz_mm"], b["start_xyz_mm"], rtol=0., atol=1e-6)
                        for a, b in pairwise(rows)),
                "cached geometry-only endpoint chain differs: " + name)
        result[name] = {"basis_grain_u_v_xyz": basis.tolist(), "start_xyz_mm": start.tolist(),
                        "end_xyz_mm": end.tolist(), "length_mm": length,
                        "cached_nominal_grain_axis_xyz": cached[name]["grain_axis_xyz"],
                        "cached_grain_to_geometric_L_sign": float(np.sign(basis[0] @ faces.vector(cached[name]["grain_axis_xyz"]))),
                        "cached_finished_part_path": cached[name]["path"],
                        "cached_finished_part_sha256": cached[name]["sha256"]}
    return result


def complete_patches(data):
    """Keep original patch order/normal ownership, including reused reverse pairs."""
    atlas = data[ATLAS]
    names = {row["member"] for row in atlas["cached_timbers"]}
    candidate_pairs = {tuple(sorted((r["first"], r["second"]))) for r in atlas["pairs"]}
    require(len(names) == 20 and len(atlas["pairs"]) == len(candidate_pairs) == 190
            and candidate_pairs == {(a, b) for a in names for b in names if a < b},
            "complete190 unordered source pair census required")
    patches = [(OLD, p) for p in data[OLD]["patches"]]
    patches += [(DIRECT, p) for p in data[DIRECT]["patches"]]
    patches += [(ATLAS, p) for p in atlas["new_positive_patches"]]
    require([len(data[OLD]["patches"]), len(data[DIRECT]["patches"]),
             len(atlas["new_positive_patches"])] == [6, 3, 21]
            and len({p["id"] for _, p in patches}) == 30
            and sum(len(p["cells"]) for _, p in patches) == 584,
            "complete30-patch/584-cell union required")
    by_pair = {tuple(sorted((p["first"], p["second"]))): (path, p) for path, p in patches}
    positive = [r for r in atlas["pairs"] if r["patch_count"] > 0]
    require(len(by_pair) == len(positive) == 30
            and {tuple(sorted((r["first"], r["second"]))) for r in positive} == set(by_pair),
            "source positive pair census differs from complete patch union")
    for row in atlas["pairs"]:
        pair = tuple(sorted((row["first"], row["second"])))
        require(row["patch_count"] in (0, 1), "unexpected source pair patch count")
        if pair not in by_pair:
            require(row["patch_count"] == 0, "positive source pair omitted")
            continue
        path, patch = by_pair[pair]
        if path == ATLAS:
            require(row["status"] == "positive-planar-area-queried"
                    and row["patch_ids"] == [patch["id"]], "new source patch identity differs")
        else:
            reused = row["reused_geometry"]
            require(row["status"] == "positive-planar-area-reused"
                    and reused["path"] == path and reused["sha256"] == INPUT_SHA256[path]
                    and reused["patch_ids"] == [patch["id"]]
                    and reused["cell_count"] == len(patch["cells"]), "own reused proof identity differs")
        require(abs(float(row["positive_area_mm2"]) - float(patch["area_mm2"])) <= 1e-6,
                "atlas/proof positive area differs")
    return patches


def host_grain_metadata(name, normal, grain):
    basis = np.asarray(grain[name]["basis_grain_u_v_xyz"])
    cosine = float(np.clip(abs(basis[0] @ normal), 0., 1.))
    return {"host": name, "absolute_normal_dot_nominal_grain": cosine,
            "normal_to_nominal_grain_angle_deg": float(np.rad2deg(np.arccos(cosine))),
            "normal_components_in_geometric_L_u_v": (basis @ normal).tolist(),
            "material_capacity_or_growth_ring_orientation_established": False}


def describe_complete_contacts(data, grain, *, bedding_n_mm3=1., scenario_id=SCENARIO):
    require(np.isfinite(bedding_n_mm3) and float(bedding_n_mm3) == 1.
            and scenario_id == SCENARIO, "existing declared1 N/mm^3 complete-atlas scenario required")
    result, seen = [], set()
    for path, patch in complete_patches(data):
        normal = faces.vector(patch["normal_from_second_to_first_xyz"])
        center, area = faces.vector(patch["centroid_xyz_mm"]), float(patch["area_mm2"])
        require(abs(np.linalg.norm(normal) - 1.) < 1e-8 and np.isfinite(area) and area > 0.
                and patch["first"] in grain and patch["second"] in grain
                and patch["first"] != patch["second"], "valid own positive source patch required")
        require(np.allclose(faces.vector(patch["first_outward_normal_xyz"]), -normal, rtol=0., atol=1e-8)
                and abs(float(patch["opposed_normal_dot"]) + 1.) < 1e-8
                and abs(float(patch["coplanar_offset_mm"])) <= 1e-5,
                "opposed coplanar own source normals required")
        host_angles = {role: host_grain_metadata(patch[role], normal, grain) for role in ("first", "second")}
        first_moment, cell_area = np.zeros(3), 0.
        for cell in patch["cells"]:
            point, weight = faces.vector(cell["point_xyz_mm"]), float(cell["area_mm2"])
            require(isinstance(cell["id"], str) and cell["id"] and cell["id"] not in seen,
                    "all distinct own source cells required")
            seen.add(cell["id"])
            require(np.isfinite(weight) and weight > 0. and abs((point - center) @ normal) <= 1e-5
                    and cell["reference_centroid_on_trimmed_patch"] is True
                    and cell["both_inward_material_probes_occupied"] is True
                    and float(cell["reference_centroid_patch_distance_mm"]) <= 1e-5,
                    "positive occupied source-plane cell required")
            first_moment += weight * point
            cell_area += weight
            metadata = {"geometry_proof_path": path, "geometry_proof_sha256": INPUT_SHA256[path],
                "patch_id": patch["id"], "cell_id": cell["id"], "patch_area_mm2": area,
                "cell_area_mm2": weight, "patch_centroid_xyz_mm": center.tolist(),
                "normal_from_second_to_first_xyz": normal.tolist(), "bedding_n_mm3": float(bedding_n_mm3),
                "scenario_id": scenario_id, "trimmed_region_signature_sha256": patch["trimmed_region_signature_sha256"],
                "source_first_face": {k: v for k, v in patch["source_first_face"].items() if k != "signature"},
                "source_second_face": {k: v for k, v in patch["source_second_face"].items() if k != "signature"},
                "host_nominal_grain": host_angles, "effective_cell_size_mm": patch["effective_cell_size_mm"],
                "second_moment_relative_frobenius_error": patch["second_moment_relative_frobenius_error"],
                **{key: cell[key] for key in ("reference_centroid_on_trimmed_patch",
                   "both_inward_material_probes_occupied", "reference_centroid_patch_distance_mm")}}
            result.append({"id": cell["id"], "kind": "timber_face_contact",
                "first": patch["first"], "second": patch["second"],
                "reference_first_point_xyz_mm": point.tolist(), "reference_second_point_xyz_mm": point.tolist(),
                "first_port_kind": "point", "director_owner": patch["second"],
                "reference_director_xyz": normal.tolist(), "axial_stiffness_n_mm": float(bedding_n_mm3) * weight,
                "lateral_stiffness_n_mm": 0., "radial_gap_mm": 0., "axial_sign": -1.,
                "reference_axial_projection_mm": 0., "axial_tension_only": True, "source_descriptor": metadata})
        require(abs(cell_area - area) <= max(1e-5, area * 1e-8)
                and np.allclose(first_moment / cell_area, center, rtol=0., atol=1e-6),
                "complete source area/first moments not conserved")
    require(len(result) == 584, "every584 complete source cell required")
    return result


def prepare_complete_timber_faces(assembly, *, bedding_n_mm3=1., scenario_id=SCENARIO):
    """Prepare rows on the caller's existing assembly without touching its K."""
    data, pins = read_inputs()
    grain = grain_geometry(data[FRAME_GEOMETRY], data[ATLAS])
    require(type(assembly) is frame.ElasticAssembly and set(assembly.members) == set(grain),
            "existing20-timber authenticated point-port assembly required")
    before = canonical_sha(linear.timber_coordinate_map(assembly))
    old_K = getattr(assembly, "K", None)
    for name, member in assembly.members.items():
        require(np.allclose(member["axis"], grain[name]["basis_grain_u_v_xyz"][0], rtol=0., atol=1e-12),
                "existing member nominal grain axis differs: " + name)
    descriptors = describe_complete_contacts(data, grain, bedding_n_mm3=bedding_n_mm3, scenario_id=scenario_id)
    contacts = linear.linear_contact_rows(assembly, descriptors)
    mapping = linear.timber_coordinate_map(assembly)
    descriptor_sha = canonical_sha(descriptors)
    signature_inputs = {"basis": BASIS, "scenario_id": scenario_id, "bedding_n_mm3": float(bedding_n_mm3),
                        "descriptor_sha256": descriptor_sha, "grain_geometry_sha256": canonical_sha(grain),
                        "layout_sha256": frame.LAYOUT_SHA, "geometry_cache_sha256": frame.GEOMETRY_CACHE_SHA,
                        "geometry_proof_sha256": {p: INPUT_SHA256[p] for p in (ATLAS, DIRECT, OLD)},
                        "adapter_sha256": LOADED_SHA256}
    signature = canonical_sha(signature_inputs)
    parameters = {"linear_timber_face_contact_basis": BASIS,
                  "linear_timber_face_contact_geometry_sha256": INPUT_SHA256[ATLAS],
                  "linear_timber_face_contact_bedding_n_mm3": float(bedding_n_mm3),
                  "linear_timber_face_contact_scenario_id": scenario_id,
                  "linear_timber_face_contact_cell_mm": 25.,
                  "linear_timber_face_contact_producer_sha256": LOADED_SHA256,
                  "complete_timber_face_contact_descriptor_sha256": descriptor_sha,
                  "complete_timber_face_contact_physical_signature_sha256": signature}
    metadata = {"method": BASIS, "contact_pair_count": 30, "contact_cell_count": 584,
                "parameters": parameters, "signature_inputs": signature_inputs, "limits": LIMITS,
                "contact_operator_sha256": contact_operator_sha(contacts),
                "coordinate_map_sha256": canonical_sha(mapping),
                "candidate_flags": copy.deepcopy(frame.RELEASE),
                "future_new_state_and_admission_required": True}
    require(getattr(assembly, "K", None) is old_K and canonical_sha(mapping) == before,
            "existing assembly coordinates or K changed during pure preparation")
    verify_pins(pins)
    return {"contacts": contacts, "descriptors": descriptors, "coordinate_map": mapping,
            "metadata": metadata, "source_sha256": pins, "grain_geometry": grain}


def contact_operator_sha(rows):
    matrix = vstack([row["B"] for row in rows], format="csr")
    return canonical_sha({"CSR_shape": matrix.shape, "CSR_indptr": matrix.indptr.tolist(),
        "CSR_indices": matrix.indices.tolist(), "CSR_data": matrix.data.tolist(),
        "rows": [{key: row[key] for key in ("id", "kind", "first", "second", "point_xyz_mm",
                  "direction_xyz", "stiffness", "source_descriptor")} for row in rows]})


def verify_component(prepared):
    verify_pins(prepared["source_sha256"])
    metadata = prepared["metadata"]
    require(metadata["method"] == BASIS and metadata["contact_pair_count"] == 30
            and metadata["contact_cell_count"] == len(prepared["contacts"]) == 584
            and canonical_sha(prepared["descriptors"]) == metadata["parameters"][
                "complete_timber_face_contact_descriptor_sha256"]
            and contact_operator_sha(prepared["contacts"]) == metadata["contact_operator_sha256"]
            and canonical_sha(prepared["coordinate_map"]) == metadata["coordinate_map_sha256"]
            and canonical_sha(metadata["signature_inputs"]) == metadata["parameters"][
                "complete_timber_face_contact_physical_signature_sha256"]
            and not any(metadata["candidate_flags"].values()), "unchanged complete contact component required")


def stamp_complete_recovered_actions(recovered, prepared, q):
    """Reuse force-dual checks then replace the six-only helper's final label."""
    verify_component(prepared)
    result = linear.stamp_recovered_actions(recovered, prepared, q)
    result["linear_timber_face_method"] = BASIS
    result["complete_timber_face_contact_metadata"] = copy.deepcopy(prepared["metadata"])
    result["complete_timber_face_contact_physical_signature_sha256"] = prepared["metadata"]["parameters"][
        "complete_timber_face_contact_physical_signature_sha256"]
    result["source_sha256"] = faces.merge_pins(recovered.get("source_sha256", {}), prepared["source_sha256"])
    verify_pins(result["source_sha256"])
    return result


def _response(rows, q, ndof, tangent=True):
    """Contact-only potential matching the frozen first-order solver law."""
    q = np.asarray(q, dtype=float)
    require(q.shape == (ndof,) and np.isfinite(q).all(), "full finite contact-only coupon vector required")
    B = vstack([row["B"] for row in rows], format="csr")
    k = np.asarray([row["stiffness"] for row in rows])
    closure = np.asarray(B @ q).ravel()
    force = k * np.maximum(closure, 0.)
    active = closure > 0.
    actions = [{"id": row["id"], "kind": "timber_face_contact", "first": row["first"],
        "second": row["second"], "point_xyz_mm": row["point_xyz_mm"], "compression_n": float(f),
        "force_on_first_xyz_n": (f * np.asarray(row["direction_xyz"])).tolist(),
        "force_on_second_xyz_n": (-f * np.asarray(row["direction_xyz"])).tolist(),
        "moment_on_first_at_point_xyz_nmm": [0., 0., 0.],
        "moment_on_second_at_point_xyz_nmm": [0., 0., 0.]}
        for row, f in zip(rows, force, strict=True)]
    return {"energy_nmm": float(.5 * closure @ force), "gradient_n": np.asarray(B.T @ force).ravel(),
            "hessian_csr": B[active].T @ diags(k[active]) @ B[active] if tangent else None,
            "closure_mm": closure, "compression_n": force, "contact_actions": actions}


def contact_response(prepared, q, tangent=True):
    """584-row contact component only, never a complete frame response/solve."""
    verify_component(prepared)
    return _response(prepared["contacts"], q, prepared["coordinate_map"]["ndof"], tangent)


def geometry_only_coupon_assembly(grain):
    """Two endpoints per source host; 240 coordinates, no K or body physics."""
    assembly = frame.ElasticAssembly.__new__(frame.ElasticAssembly)
    assembly.members, assembly.fittings, assembly.panels, assembly.panel_offsets = {}, {}, {}, {}
    assembly.ndof = 20 * 12
    for i, (name, row) in enumerate(grain.items()):
        assembly.members[name] = {"start": np.asarray(row["start_xyz_mm"]),
            "axis": np.asarray(row["basis_grain_u_v_xyz"][0]),
            "stations": np.asarray([0., row["length_mm"]]), "index": np.arange(12 * i, 12 * i + 12).reshape(2, 6)}
    return assembly


def known_answers(assembly, prepared):
    """New union/operator checks; old finite-rotation method fixtures stay frozen."""
    rows, ndof = prepared["contacts"], assembly.ndof
    B = vstack([r["B"] for r in rows], format="csr")
    rigid = assembly.rigid_modes()
    rigid_error = float(np.max(abs(B @ rigid)))
    require(rigid_error < 1e-9, "complete rows violate common rigid work")
    zero = contact_response(prepared, np.zeros(ndof))
    require(zero["energy_nmm"] == 0. and not np.any(zero["gradient_n"])
            and zero["hessian_csr"].nnz == 0 and not np.any(zero["compression_n"]),
            "zero-gap touch must have zero preload/inactive one-sided tangent")
    max_force_error = max_energy_error = max_slip_force = 0.
    for patch_id in sorted({r["source_descriptor"]["patch_id"] for r in rows}):
        patch_rows = [r for r in rows if r["source_descriptor"]["patch_id"] == patch_id]
        normal = np.asarray(patch_rows[0]["direction_xyz"])
        first = patch_rows[0]["first"]
        q = np.zeros(ndof)
        for idx in assembly.members[first]["index"]:
            q[idx[:3]] = -.02 * normal
        closed = _response(patch_rows, q, ndof)
        area = sum(r["source_descriptor"]["cell_area_mm2"] for r in patch_rows)
        max_force_error = max(max_force_error, abs(sum(closed["compression_n"]) - .02 * area))
        max_energy_error = max(max_energy_error, abs(closed["energy_nmm"] - .5 * .02**2 * area))
        opened = _response(patch_rows, -q, ndof)
        require(opened["energy_nmm"] == 0. and not np.any(opened["compression_n"]), "source patch opening force")
        tangent = np.cross(normal, np.eye(3)[int(np.argmin(abs(normal)))])
        for idx in assembly.members[first]["index"]:
            q[idx[:3]] = 3. * tangent
        slip = _response(patch_rows, q, ndof)
        max_slip_force = max(max_slip_force, float(np.max(slip["compression_n"])))
    require(max_force_error < 1e-9 and max_energy_error < 1e-10 and max_slip_force < 1e-9,
            "30 hand uniform compression/opening/friction-free slip answers differ")
    rng = np.random.default_rng(30584)
    q = np.zeros(ndof)
    for member in assembly.members.values():
        shift = rng.normal(size=3) * .03
        for idx in member["index"]:
            q[idx[:3]] = shift
    response = contact_response(prepared, q)
    direction = rng.normal(size=ndof)
    direction /= np.linalg.norm(direction)
    step = 1e-5
    plus, minus = contact_response(prepared, q + step * direction, False), contact_response(prepared, q - step * direction, False)
    require(np.array_equal(plus["closure_mm"] > 0., response["closure_mm"] > 0.)
            and np.array_equal(minus["closure_mm"] > 0., response["closure_mm"] > 0.), "FD branch crossed")
    gradient_error = abs(float(direction @ response["gradient_n"])
                         - (plus["energy_nmm"] - minus["energy_nmm"]) / (2 * step))
    hessian_error = float(np.max(abs(response["hessian_csr"] @ direction
        - (plus["gradient_n"] - minus["gradient_n"]) / (2 * step))))
    H = response["hessian_csr"]
    symmetry_error = float(np.max(abs((H - H.T).data), initial=0.))
    require(gradient_error < 1e-7 and hessian_error < 1e-6 and symmetry_error < 1e-10,
            "complete contact component gradient/Hessian differs")
    adjoint_error = pair_force_error = pair_moment_error = 0.
    body_wrenches = {name: np.zeros(6) for name in assembly.members}
    for action in response["contact_actions"]:
        F, G = np.asarray(action["force_on_first_xyz_n"]), np.asarray(action["force_on_second_xyz_n"])
        point = np.asarray(action["point_xyz_mm"])
        pair_force_error = max(pair_force_error, float(np.linalg.norm(F + G)))
        pair_moment_error = max(pair_moment_error, float(np.linalg.norm(np.cross(point, F) + np.cross(point, G))))
        for host, force in ((action["first"], F), (action["second"], G)):
            datum = assembly.members[host]["start"]
            body_wrenches[host] += np.r_[force, np.cross(point - datum, force)]
    for name, member in assembly.members.items():
        own_modes = np.zeros((ndof, 6))
        for idx, station in zip(member["index"], member["stations"], strict=True):
            own_modes[idx[:3], :3] = np.eye(3)
            own_modes[idx[:3], 3:] = -frame.cross_matrix(station * member["axis"])
            own_modes[idx[3:], 3:] = frame.ROTATION_SCALE * np.eye(3)
        adjoint_error = max(adjoint_error, float(np.max(abs(own_modes.T @ response["gradient_n"] + body_wrenches[name]))))
    require(max(adjoint_error, pair_force_error, pair_moment_error) < 1e-7,
            "all20 own-body generalized-work/point-wrench closure differs")
    stamped = stamp_complete_recovered_actions({"contact_actions": response["contact_actions"]}, prepared, q)
    require(stamped["linear_timber_face_method"] == BASIS
            and len(stamped["timber_face_contact_actions"]) == 584
            and all(r["source_descriptor"]["scenario_id"] == SCENARIO for r in stamped["timber_face_contact_actions"]),
            "fresh complete writer identity/all zero rows lost")
    return {"coupon_ndof": ndof, "source_host_count": 20, "represented_patch_count": 30,
        "represented_cell_count": 584, "common_rigid_work_max_closure_mm": rigid_error,
        "zero_preload_energy_nmm": zero["energy_nmm"], "touch_inactive_tangent_nnz": zero["hessian_csr"].nnz,
        "all30_uniform_compression_force_error_n": max_force_error,
        "all30_uniform_compression_energy_error_nmm": max_energy_error,
        "all30_opening_zero_force": True, "all30_friction_free_slip_max_force_n": max_slip_force,
        "mixed_branch_active_cells": int(np.count_nonzero(response["closure_mm"] > 0.)),
        "mixed_branch_minimum_absolute_closure_mm": float(np.min(abs(response["closure_mm"]))),
        "gradient_energy_directional_derivative_error_nmm": gradient_error,
        "hessian_gradient_directional_derivative_max_error_n_mm": hessian_error,
        "hessian_symmetry_max_error_n_mm": symmetry_error,
        "all20_own_body_rigid_work_wrench_max_error_n_or_nmm": adjoint_error,
        "all584_pair_force_residual_n": pair_force_error, "all584_pair_origin_moment_residual_nmm": pair_moment_error,
        "all584_actions_including_zeros_and_fresh_basis_stamped": True,
        "reference_normals_material_motion_or_candidate_field_tested": False,
        "K_prepared_or_global_field_solved": False}


def preparation_report():
    data, pins = read_inputs()
    grain = grain_geometry(data[FRAME_GEOMETRY], data[ATLAS])
    assembly = geometry_only_coupon_assembly(grain)
    prepared = prepare_complete_timber_faces(assembly)
    observations = known_answers(assembly, prepared)
    patches = []
    for path, patch in complete_patches(data):
        normal = faces.vector(patch["normal_from_second_to_first_xyz"])
        patches.append({"patch_id": patch["id"], "first": patch["first"], "second": patch["second"],
            "geometry_proof_path": path, "geometry_proof_sha256": INPUT_SHA256[path],
            "area_mm2": patch["area_mm2"], "cell_count": len(patch["cells"]),
            "centroid_xyz_mm": patch["centroid_xyz_mm"], "normal_from_second_to_first_xyz": normal.tolist(),
            "host_nominal_grain": {role: host_grain_metadata(patch[role], normal, grain) for role in ("first", "second")},
            "source_face_signature_sha256": {role: patch["source_" + role + "_face"]["signature_sha256"] for role in ("first", "second")},
            "trimmed_region_signature_sha256": patch["trimmed_region_signature_sha256"],
            "second_moment_relative_frobenius_error": patch["second_moment_relative_frobenius_error"]})
    result = {"schema": SCHEMA, "candidate": data[ATLAS]["candidate"],
        "mathematical_preparation_only": True, "metadata": prepared["metadata"], "source_sha256": pins,
        "source_verification_before_and_after": True,
        "raw_input_sha256": INPUT_SHA256, "canonical_input_sha256": {p: canonical_sha(d) for p, d in data.items()},
        "geometry_only_saved_source_keys": ["member", "element", "start_xyz_mm", "end_xyz_mm", "basis_grain_u_v_xyz"],
        "grain_geometry": grain, "patches": patches, "counts": {"timber_hosts": 20, "source_unordered_pairs": 190,
            "positive_interfaces": 30, "old_interfaces": 6, "direct_interfaces": 3, "atlas_new_interfaces": 21,
            "represented_cells": 584, "old_cells": 272, "new_cells": 312},
        "known_answers": observations,
        "floor_support_preservation": {"adapter_supplies_floor_rows": False, "floor_datums_or_operators_modified": False,
            "existing_basis": faces.finite.floor_method.SUPPORT_BASIS,
            "original_normal_activation_threshold_n": faces.finite.floor_method.NORMAL_ACTIVATION_THRESHOLD_N},
        "old_finite_contact_method_reused_within_scope": {"source": "scripts/thin_bolted_timber_face_contact.py",
            "finite_rotation_method_coupons_repeated": False, "finite_motion_law_adopted_by_this_linear_adapter": False},
        "tool_versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "reproduction_command": "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python " + OWN,
        "tests_command": "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q " + TEST,
        "limits": LIMITS, "release": copy.deepcopy(frame.RELEASE)}
    verify_pins(pins)
    require(pins == read_inputs()[1], "source graph changed after pure preparation")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("preparation.json"))
    args = parser.parse_args()
    require(not args.out.exists(), "preserve issued complete-contact preparation bytes")
    report = preparation_report()
    report["invocation_argv"] = sys.argv
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "sha256": frame.sha(args.out), "counts": report["counts"],
                      "known_answers": report["known_answers"], "candidate_flags": report["release"]}))


if __name__ == "__main__":
    main()
