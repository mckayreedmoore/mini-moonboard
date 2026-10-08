"""Pure checks for the complete source-bound timber compression extension.

Saved operators supply a same-q original-gradient replay without a material
matrix assembly or a solve. Complete field admission additionally checks the
actual invocation, immutable sources and all 132 body/global balances. The
receipt establishes export/law/equilibrium consistency, never joint strength.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

from scripts import thin_bolted_linear_timber_admission as linear
from scripts import thin_bolted_numerical_step as numerical
from scripts import thin_bolted_support_search_admission as floor_reuse

ROOT = linear.ROOT
PACKET = Path(__file__).resolve().parent
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_PRODUCER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
SCHEMA = "thin_bolted_independent_complete_timber_admission/v1"
SUCCESS = "independent_complete_timber_face_source_map_original_gradient_and_equilibrium_checks_pass"
DRIVER = "fea/generated/thin-bolted-direct-contact-a12-v1/runner.py"
ADAPTER = "fea/generated/thin-bolted-complete-timber-contact-v1/adapter.py"
ADAPTER_SHA256 = "531d8e3393e309de172442b6a936c76b0d8db73f97a2bf63f831fa2a87d3b67f"
PREPARATION = "fea/generated/thin-bolted-complete-timber-contact-v1/preparation.json"
PREPARATION_SHA256 = "59f6691d6c772938e5cb7a078294a65b99660645c8f2604b3a4a33dc1b302fe1"
BASIS = "source-bound-linear-complete-atlas-wood-compression-v1"
SCENARIO = "complete-atlas-wood-bedding-declared-v1"
LINEAR_GATE = "scripts/thin_bolted_linear_timber_admission.py"
LINEAR_GATE_SHA256 = "e6dcb38947bea00ca583cd9a9e8d37a0cf0720d1f3ca97f7013ba9f2def0c676"
NUMERICAL = "scripts/thin_bolted_numerical_step.py"
NUMERICAL_SHA256 = "82b7d5a8d9d9dc871ee6410fb4c5854093a998cfd9b331fdd986917b63ebbc28"
FLOOR_REUSE = "scripts/thin_bolted_support_search_admission.py"
FLOOR_REUSE_SHA256 = "c7a70cebfe3640b82a151e358d32d0826d2c14b4d881059ed6c48a1c1a1cba84"
OLD = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/timber-face-contact-geometry-v4.json"
DIRECT = "fea/generated/thin-bolted-local-joint-ports/direct-timber-contact.json"
ATLAS = "fea/generated/thin-bolted-local-joint-ports/all-timber-pair-contact-atlas.json"
CACHE = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/native-geometry-v4.json"
GEOMETRY_PINS = {
    OLD: "be88aeb6754bc03e8afd523f5127f74b93b90bd00e8c3ceaa910e70aab3f125a",
    DIRECT: "ead9fee6a06d1233ac4cfd006fb2c681241d6ea2e81ddc410b1e47d9550e7dfa",
    ATLAS: "5331d559f5454afc8e35dd86bd5435bf8a7239283e29c5c1f3c193eb6671a420",
    CACHE: "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9",
}
require = linear.require
canonical_sha = linear.canonical_sha
original = linear.proof_method.original


def source_pins(additional=None):
    pins = linear.merge_pins(linear.source_pins(), GEOMETRY_PINS,
                            {OWN: LOADED_PRODUCER_SHA256, LINEAR_GATE: LINEAR_GATE_SHA256,
                             NUMERICAL: NUMERICAL_SHA256, FLOOR_REUSE: FLOOR_REUSE_SHA256},
                            additional or {})
    linear.verify_pins(pins)
    return pins


def _read(path):
    payload = (ROOT / path).read_bytes()
    require(hashlib.sha256(payload).hexdigest() == GEOMETRY_PINS[path],
            "complete contact geometry bytes changed: " + path)
    return json.loads(payload)


def _pair(row):
    return tuple(sorted((row["first"], row["second"])))


def _verify_patch(patch, members):
    require(patch["first"] != patch["second"] and {patch["first"], patch["second"]} <= set(members),
            "contact patch requires two distinct source timber hosts")
    normal = original.array(patch["normal_from_second_to_first_xyz"], (3,))
    centroid = original.array(patch["centroid_xyz_mm"], (3,))
    area = linear.support.finite_scalar(patch["area_mm2"])
    require(area > 0. and abs(np.linalg.norm(normal) - 1.) <= 1e-8,
            "positive patch and unit source normal required")
    original.close(patch["first_outward_normal_xyz"], -normal, 1e-8, "opposed source face normal differs")
    require(abs(patch["coplanar_offset_mm"]) <= 1e-5 and abs(patch["opposed_normal_dot"] + 1.) <= 1e-8,
            "source faces must be opposed and coplanar")
    for host, key, outward in ((patch["first"], "source_first_face", -normal),
                               (patch["second"], "source_second_face", normal)):
        face = patch[key]
        signature = face["signature"]
        ordinal = face["face_ordinal_1_based"]
        require(type(ordinal) is int and ordinal > 0 and signature["surface_type"] == "PLANE"
                and canonical_sha(signature) == face["signature_sha256"]
                and face["face_id"] == f"{host}/step-face-{ordinal:04d}-{face['signature_sha256'][:16]}",
                "source face identity or signature differs")
        original.close(signature["oriented_normal_xyz"], outward, 1e-8, "source face director differs")
        require(signature["area_mm2"] >= area - 1e-5, "patch exceeds its source face")
    region = patch["trimmed_region_geometry"]
    require(canonical_sha(region) == patch["trimmed_region_signature_sha256"]
            and region["surface_type"] == "PLANE" and abs(region["area_mm2"] - area) <= 1e-5,
            "trimmed patch geometry signature differs")
    original.close(region["center_xyz_mm"], centroid, 1e-5, "trimmed patch center differs")
    cells = original.unique(patch["cells"])
    require(cells, "positive source patch needs occupied cells")
    total, first = 0., np.zeros(3)
    for identity, cell in cells.items():
        point = original.array(cell["point_xyz_mm"], (3,))
        weight = linear.support.finite_scalar(cell["area_mm2"])
        require(identity.startswith(patch["id"] + "/cell-") and weight > 0.
                and cell["reference_centroid_on_trimmed_patch"] is True
                and cell["both_inward_material_probes_occupied"] is True
                and 0. <= cell["reference_centroid_patch_distance_mm"] <= 1e-7
                and abs(normal @ (point - centroid)) <= 1e-5,
                "source cell identity, occupancy, plane or positive area differs")
        total += weight
        first += weight * point
    require(abs(total - area) <= max(1e-5, area * 1e-8), "source cells lose patch area")
    original.close(first / total, centroid, 1e-6, "source cells lose patch first moment")
    sampled = sum((c["area_mm2"] * np.outer(np.asarray(c["point_xyz_mm"]) - centroid,
                                              np.asarray(c["point_xyz_mm"]) - centroid)
                   for c in cells.values()), np.zeros((3, 3)))
    original.close(sampled, patch["sampled_centroidal_second_moment_matrix_xyz_mm4"], 1e-5,
                   "source cell second moments differ")
    exact = original.array(patch["exact_centroidal_second_moment_matrix_xyz_mm4"], (3, 3))
    original.close(exact, exact.T, 1e-5, "source patch second moments are not symmetric")
    require(np.linalg.norm(exact) > 0., "nonzero source patch second moment required")
    error = float(np.linalg.norm(sampled - exact) / np.linalg.norm(exact))
    require(abs(error - patch["second_moment_relative_frobenius_error"]) <= 1e-10,
            "declared contact quadrature error differs")


def read_complete_geometry():
    """Authenticate the immutable union, without CAD or an operator build."""
    old, direct, atlas, cache = [_read(path) for path in (OLD, DIRECT, ATLAS, CACHE)]
    members = {row["id"]: row for row in cache["parts"] if row["kind"] == "timber"}
    require(len(members) == 20, "all twenty cached timber bodies required")
    for name, row in members.items():
        grain = original.array(row["grain_axis_xyz"], (3,))
        require(abs(np.linalg.norm(grain) - 1.) <= 1e-8, "unit cached grain axis required: " + name)
    require(atlas["reference_positive_area_contact_geometry_enumerated"] is True
            and atlas["complete_contact_response_operator"] is False,
            "complete reference geometry enumeration required; no response adoption inherited")
    pairs = {_pair(row): row for row in atlas["pairs"]}
    require(len(atlas["pairs"]) == len(pairs) == 190
            and set(pairs) == set(itertools.combinations(sorted(members), 2)),
            "all 190 unique unordered source timber pair dispositions required")
    cached = {row["member"]: row for row in atlas["cached_timbers"]}
    require(len(cached) == len(atlas["cached_timbers"]) == 20 and set(cached) == set(members),
            "complete atlas timber source census required")
    for name, row in cached.items():
        require(all(row[key] == members[name][key] for key in
                    ("path", "sha256", "bounds_xyz_mm", "grain_axis_xyz")),
                "atlas cached timber source/grain differs")
    owned = [(path, digest, patch) for path, report in ((OLD, old), (DIRECT, direct), (ATLAS, atlas))
             for digest in (GEOMETRY_PINS[path],)
             for patch in report.get("patches", report.get("new_positive_patches"))]
    patches = {patch["id"]: patch for _, _, patch in owned}
    require(len(patches) == len(owned) == 30 and len({_pair(p) for p in patches.values()}) == 30,
            "exact thirty distinct positive-area source interfaces required")
    require([len(old["patches"]), len(direct["patches"]), len(atlas["new_positive_patches"])] == [6, 3, 21],
            "six plus three plus twenty-one immutable geometry union required")
    cell_ids = [c["id"] for p in patches.values() for c in p["cells"]]
    require(len(cell_ids) == len(set(cell_ids)) == 584, "all 584 distinct occupied contact cells required")
    for path, digest, patch in owned:
        _verify_patch(patch, members)
        record = pairs[_pair(patch)]
        require(record["patch_count"] == 1 and abs(record["positive_area_mm2"] - patch["area_mm2"]) <= 1e-5,
                "atlas positive pair patch/area census differs")
        if path == ATLAS:
            require(record["status"] == "positive-planar-area-queried" and record["patch_ids"] == [patch["id"]],
                    "new atlas patch provenance differs")
        else:
            reused = record["reused_geometry"]
            require(record["status"] == "positive-planar-area-reused" and reused["path"] == path
                    and reused["sha256"] == digest and reused["patch_ids"] == [patch["id"]]
                    and reused["cell_count"] == len(patch["cells"]), "reused geometry provenance differs")
    positive_pairs = {_pair(p) for p in patches.values()}
    for pair, row in pairs.items():
        if pair not in positive_pairs:
            require(row["patch_count"] == 0 and row["positive_area_mm2"] == 0.
                    and row["status"] in {"disjoint-source-bounds", "empty-trimmed-planar-intersection"},
                    "unresolved or omitted positive-area source pair")
        require(all(c["status"] == "no-positive-trimmed-surface-area"
                    for c in row["curved_surface_candidate_queries"]), "unresolved curved contact geometry")
    pins = source_pins(linear.merge_pins(*(r["source_sha256"] for r in (old, direct, atlas))))
    spans = linear.spans.read_member_span_geometry()
    grain_geometry = {}
    for name in sorted(members):
        span = spans[name]
        basis = original.array(span["basis_grain_u_v_xyz"], (3, 3))
        original.close(basis @ basis.T, np.eye(3), 1e-12, "proper source grain frame required")
        cached_grain = original.array(members[name]["grain_axis_xyz"], (3,))
        require(np.linalg.norm(np.cross(basis[0], cached_grain / np.linalg.norm(cached_grain))) <= 1e-8,
                "source nominal grain axis differs")
        require(abs(np.linalg.det(basis) - 1.) <= 1e-12, "right-handed geometric grain frame required")
        start, end = np.asarray(span["start_xyz_mm"]), np.asarray(span["end_xyz_mm"])
        grain_geometry[name] = {**span, "length_mm": float((end - start) @ basis[0]),
            "cached_nominal_grain_axis_xyz": members[name]["grain_axis_xyz"],
            "cached_grain_to_geometric_L_sign": float(np.sign(basis[0] @ cached_grain)),
            "cached_finished_part_path": members[name]["path"],
            "cached_finished_part_sha256": members[name]["sha256"]}
    return {"patch_sources": owned, "members": members, "grain_geometry": grain_geometry, "source_sha256": pins,
            "pair_count": 30, "cell_count": 584, "source_unordered_pair_count": 190,
            "capacity_or_current_overlap_established": False}


def source_grain_classification(patch, members):
    normal = original.array(patch["normal_from_second_to_first_xyz"], (3,))
    result = {}
    for host in (patch["first"], patch["second"]):
        grain = original.array(members[host]["grain_axis_xyz"], (3,))
        cosine = min(1., abs(float(normal @ grain)))
        result[host] = {"grain_axis_xyz": grain.tolist(), "normal_grain_abs_cosine": cosine,
                        "normal_grain_angle_degrees": math.degrees(math.acos(cosine))}
    return result


def expected_complete_descriptors(geometry):
    """Independently map each pinned occupied cell to its zero-preload law."""
    result = []
    for path, digest, patch in geometry["patch_sources"]:
        normal = original.array(patch["normal_from_second_to_first_xyz"], (3,))
        grain = {}
        for role in ("first", "second"):
            name = patch[role]
            basis = np.asarray(geometry["grain_geometry"][name]["basis_grain_u_v_xyz"])
            cosine = float(np.clip(abs(basis[0] @ normal), 0., 1.))
            grain[role] = {"host": name, "absolute_normal_dot_nominal_grain": cosine,
                "normal_to_nominal_grain_angle_deg": float(np.rad2deg(np.arccos(cosine))),
                "normal_components_in_geometric_L_u_v": (basis @ normal).tolist(),
                "material_capacity_or_growth_ring_orientation_established": False}
        for cell in patch["cells"]:
            metadata = {"geometry_proof_path": path, "geometry_proof_sha256": digest,
                "patch_id": patch["id"], "cell_id": cell["id"], "patch_area_mm2": patch["area_mm2"],
                "cell_area_mm2": cell["area_mm2"], "patch_centroid_xyz_mm": patch["centroid_xyz_mm"],
                "normal_from_second_to_first_xyz": normal.tolist(), "bedding_n_mm3": 1., "scenario_id": SCENARIO,
                "trimmed_region_signature_sha256": patch["trimmed_region_signature_sha256"],
                "source_first_face": {k: v for k, v in patch["source_first_face"].items() if k != "signature"},
                "source_second_face": {k: v for k, v in patch["source_second_face"].items() if k != "signature"},
                "host_nominal_grain": grain, "effective_cell_size_mm": patch["effective_cell_size_mm"],
                "second_moment_relative_frobenius_error": patch["second_moment_relative_frobenius_error"],
                **{key: cell[key] for key in ("reference_centroid_on_trimmed_patch",
                    "both_inward_material_probes_occupied", "reference_centroid_patch_distance_mm")}}
            result.append({"id": cell["id"], "kind": "timber_face_contact",
                "first": patch["first"], "second": patch["second"],
                "reference_first_point_xyz_mm": cell["point_xyz_mm"],
                "reference_second_point_xyz_mm": cell["point_xyz_mm"], "first_port_kind": "point",
                "director_owner": patch["second"], "reference_director_xyz": normal.tolist(),
                "axial_stiffness_n_mm": cell["area_mm2"], "lateral_stiffness_n_mm": 0., "radial_gap_mm": 0.,
                "axial_sign": -1., "reference_axial_projection_mm": 0., "axial_tension_only": True,
                "source_descriptor": metadata})
    require(len(result) == len({r["id"] for r in result}) == 584, "complete expected descriptor census differs")
    return result


def verify_complete_face_actions(field, geometry, mapping, q, *, adapter_sha256):
    """Replay every new face action from immutable geometry and final q."""
    params = field["parameters"]
    descriptors = expected_complete_descriptors(geometry)
    expected_parameters = {"linear_timber_face_contact_basis": BASIS,
        "linear_timber_face_contact_geometry_sha256": GEOMETRY_PINS[ATLAS],
        "linear_timber_face_contact_bedding_n_mm3": 1., "linear_timber_face_contact_scenario_id": SCENARIO,
        "linear_timber_face_contact_cell_mm": 25., "linear_timber_face_contact_producer_sha256": adapter_sha256,
        "complete_timber_face_contact_descriptor_sha256": canonical_sha(descriptors)}
    signature_inputs = {"basis": BASIS, "scenario_id": SCENARIO, "bedding_n_mm3": 1.,
        "descriptor_sha256": canonical_sha(descriptors), "grain_geometry_sha256": canonical_sha(geometry["grain_geometry"]),
        "layout_sha256": linear.proof_method.original.arithmetic.PINS["mixed-offset-rows-shallow-wires-v4.json"],
        "geometry_cache_sha256": GEOMETRY_PINS[CACHE],
        "geometry_proof_sha256": {p: GEOMETRY_PINS[p] for p in (ATLAS, DIRECT, OLD)},
        "adapter_sha256": adapter_sha256}
    signature = canonical_sha(signature_inputs)
    expected_parameters["complete_timber_face_contact_physical_signature_sha256"] = signature
    require(field["linear_timber_face_method"] == BASIS
            and all(params.get(k) == v for k, v in expected_parameters.items()),
            "distinct complete source-bound face parameters/signature required")
    require(field.get("complete_timber_face_contact_physical_signature_sha256") == signature,
            "complete physical signature alias differs")
    metadata = field["complete_timber_face_contact_metadata"]
    require(metadata["method"] == BASIS and metadata["contact_pair_count"] == 30
            and metadata["contact_cell_count"] == 584
            and canonical_sha(metadata["parameters"]) == canonical_sha(expected_parameters)
            and canonical_sha(metadata["signature_inputs"]) == canonical_sha(signature_inputs),
            "complete face metadata/source signature differs")
    require(metadata["future_new_state_and_admission_required"] is True
            and set(metadata["candidate_flags"]) == set(field["release"])
            and all(v is False for v in metadata["candidate_flags"].values()), "unreleased complete face metadata required")
    rows = [r for r in field["contact_actions"] if r["kind"] == "timber_face_contact"]
    indexed = original.unique(rows)
    alias = original.unique(field["timber_face_contact_actions"])
    require(set(indexed) == {r["id"] for r in descriptors} and len(indexed) == 584
            and canonical_sha(indexed) == canonical_sha(alias), "all 584 face rows and exact aliases required")
    original.identities(field, rows)
    q = original.array(q, (mapping["ndof"],))
    total_energy = 0.
    for descriptor in descriptors:
        row = indexed[descriptor["id"]]
        point = descriptor["reference_first_point_xyz_mm"]
        normal = np.asarray(descriptor["reference_director_xyz"])
        require((row["first"], row["second"]) == (descriptor["first"], descriptor["second"])
                and canonical_sha(row["source_descriptor"]) == canonical_sha(descriptor["source_descriptor"])
                and row["action_wrench_uses_reference_point_first_order"] is True
                and row["physical_pressure_or_current_overlap_resolved"] is False,
                "complete face owner/source descriptor or first-order law differs")
        closure = -float(normal @ (linear.point_displacement(mapping, row["first"], point, q)
                                  - linear.point_displacement(mapping, row["second"], point, q)))
        stiffness = descriptor["axial_stiffness_n_mm"]
        compression = stiffness * max(closure, 0.)
        total_energy += .5 * stiffness * max(closure, 0.)**2
        require(abs(linear.support.finite_scalar(row["relative_closure_mm"]) - closure) <= 1e-8
                and abs(linear.support.finite_scalar(row["compression_n"]) - compression) <= 1e-6
                and row["penalty_stiffness_n_mm"] == stiffness and row["cell_area_mm2"] == stiffness,
                "complete face closure/stiffness/area/compression differs from saved q")
        for key, value in (("point_xyz_mm", point), ("direction_xyz", normal),
                           ("force_on_first_xyz_n", compression * normal),
                           ("force_on_second_xyz_n", -compression * normal)):
            original.close(row[key], value, 1e-6 if "force" in key else 1e-8,
                           "complete face point/director/force dual differs: " + key)
        for key in ("moment_at_point_model_xyz_nmm", "moment_on_first_at_point_xyz_nmm", "moment_on_second_at_point_xyz_nmm"):
            original.close(row[key], [0., 0., 0.], 1e-8, "complete point law cannot add a free couple")
        if "host_support_point_xyz_mm" in row:
            original.close(row["host_support_point_xyz_mm"], point, 1e-8, "complete paired reference datum differs")
    return {"face_cell_count": 584, "retained_pair_count": 30, "all_source_cells_and_zero_rows_retained": True,
            "original_linear_q_contact_laws_replayed": True, "face_potential_energy_nmm": total_energy,
            "physical_signature_sha256": signature, "material_capacity_or_current_overlap_established": False}


def read_csr(arrays, descriptor):
    """Read one source-bound numeric CSR record; never build material K."""
    prefix = descriptor["prefix"]
    shape = np.asarray(arrays[prefix + "_shape"])
    indices = np.asarray(arrays[prefix + "_indices"])
    indptr = np.asarray(arrays[prefix + "_indptr"])
    data = np.asarray(arrays[prefix + "_data"], dtype=float)
    require(shape.shape == (2,) and np.issubdtype(shape.dtype, np.integer)
            and np.all(shape >= 0) and shape.tolist() == descriptor["shape"]
            and indices.ndim == indptr.ndim == data.ndim == 1
            and np.issubdtype(indices.dtype, np.integer) and np.issubdtype(indptr.dtype, np.integer)
            and np.isfinite(data).all() and len(indices) == len(data)
            and len(indptr) == int(shape[0]) + 1 and indptr[0] == 0 and indptr[-1] == len(data)
            and np.all(np.diff(indptr) >= 0) and np.all((indices >= 0) & (indices < shape[1])),
            "finite complete CSR operator record required: " + prefix)
    matrix = csr_matrix((data.copy(), indices.copy(), indptr.copy()), shape=tuple(shape))
    return matrix


def _host_set(value, hosts, label):
    require(isinstance(value, list) and value == sorted(set(value)) and set(value) <= set(hosts), label)
    return set(value)


def replay_original_gradient(field, operator_inputs, arrays, *, observed_enabled_hosts=None,
                             observed_linear_K=None):
    """Fresh original-law algebra at current q, including honest failed q.

    A failed vector is diagnostic only. Both the actual observed branch and
    the demanded original floor branch are evaluated at that same vector.
    Neither evaluation solves, transfers old q or supplies current actions.
    """
    require(operator_inputs["schema"] == "thin_bolted_complete_timber_original_operator_inputs/v1",
            "complete original operator-input schema required")
    response = field["response"]
    q_kind = "q" if "q" in response else "diagnostic_last_q"
    require(q_kind in response, "fresh current or diagnostic vector required for original-law replay")
    ndof = operator_inputs["ndof"]
    require(type(ndof) is int and ndof > 0, "positive original coordinate dimension required")
    q = original.array(response[q_kind], (ndof,))
    material = read_csr(arrays, operator_inputs["material_K"])
    require(material.shape == (ndof, ndof), "original material operator dimension differs")
    applied = original.array(arrays[operator_inputs["applied"]["key"]], (ndof,))
    groups = []
    for row in operator_inputs["groups"]:
        B = read_csr(arrays, row["B"])
        require(B.shape == (3, ndof) and type(row["tension_only"]) is bool
                and all(linear.support.finite_scalar(row[k]) >= 0. for k in ("ka", "kl", "clearance")),
                "original three-component constitutive group required")
        groups.append({**row, "B": B})
    contacts = operator_inputs["contacts"]
    require(len(original.unique(contacts)) == len(contacts), "unique original normal contact identities required")
    C = read_csr(arrays, operator_inputs["C"])
    ck = original.array(arrays[operator_inputs["ck"]["key"]], (len(contacts),))
    require(C.shape == (len(contacts), ndof) and np.all(ck > 0.)
            and np.array_equal(ck, [r["stiffness"] for r in contacts]),
            "complete original contact matrix and positive stiffness order required")
    tangents = [{**row, "B": read_csr(arrays, row["B"])} for row in operator_inputs["tangents"]]
    hosts = sorted({r["first"] for r in contacts if r["kind"] == "floor_normal"})
    require(hosts and {r["first"] for r in tangents} == set(hosts)
            and len({r["id"] for r in tangents}) == len(tangents)
            and all(r["B"].shape == (1, ndof) and r["stiffness"] == 100000. for r in tangents),
            "unchanged centroid floor tangent inputs required")
    if observed_enabled_hosts is None:
        require(q_kind == "q" and "nonbearing_no_slip_removed" in response,
                "failed replay requires explicit actual observed branch provenance")
        disabled = _host_set(response["nonbearing_no_slip_removed"], hosts, "original disabled floor host set differs")
        observed_enabled_hosts = sorted(set(hosts) - disabled)
    observed = _host_set(observed_enabled_hosts, hosts, "actual observed floor host set differs")

    def linear_for(enabled):
        matrix = material.copy()
        for tangent in tangents:
            if tangent["first"] in enabled:
                matrix += tangent["stiffness"] * (tangent["B"].T @ tangent["B"])
        return matrix

    observed_matrix = linear_for(observed)
    if observed_linear_K is not None:
        require(observed_linear_K.shape == observed_matrix.shape
                and np.isfinite(observed_linear_K.data).all(), "finite captured original closed-branch operator required")
        difference = observed_linear_K - observed_matrix
        require(not difference.nnz or abs(difference.data).max() <= 1e-8,
                "captured observed branch differs from original material and selected floor operators")
    else:
        require(q_kind == "q", "failed replay requires captured actual last closed-branch operator")
    observed_fields = numerical.physical_fields(observed_matrix, applied, groups, C, ck, q, tangent=False)
    gradient, energy, _, _, normal, _ = observed_fields
    require(np.isfinite(gradient).all() and math.isfinite(energy) and np.isfinite(normal).all(),
            "finite original physical fields required")
    normal_by_host = dict.fromkeys(hosts, 0.)
    for row, force in zip(contacts, normal, strict=True):
        if row["kind"] == "floor_normal":
            normal_by_host[row["first"]] += float(force)
    demanded = {host for host in hosts if normal_by_host[host] > 1e-7}
    demanded_fields = numerical.physical_fields(linear_for(demanded), applied, groups, C, ck, q, tangent=False)

    def record(result):
        g, E = result[:2]
        require(np.isfinite(g).all() and math.isfinite(E), "finite original same-q branch fields required")
        return {"signed_gradient_n": g.tolist(), "gradient_canonical_sha256": canonical_sha(g.tolist()),
                "gradient_inf_n": float(abs(g).max()), "potential_energy_nmm": float(E)}

    source_pins()
    return {"schema": "thin_bolted_complete_timber_original_gradient_replay/v1",
        "q_kind": q_kind, "diagnostic_only": q_kind != "q", "final_q_canonical_sha256": canonical_sha(q.tolist()),
        "observed_enabled_centroid_xy_hosts": sorted(observed),
        "demanded_enabled_centroid_xy_hosts": sorted(demanded), "floor_normal_force_n_by_host": normal_by_host,
        "same_state_support_mask_consistent": observed == demanded, "floor_activation_threshold_n": 1e-7,
        "observed_branch": record(observed_fields), "demanded_floor_law_branch": record(demanded_fields),
        "native_CAD_material_K_assembly_or_response_solve": False, "physical_laws_modified": False,
        "current_action_admission_or_capacity_established": False}


def verify_complete_action_census(field, panels):
    """Check full new census directly, retaining zero rows and all old paths."""
    contacts = original.unique(field["contact_actions"])
    require(len(contacts) == 1402 and Counter(r["kind"] for r in contacts.values())
            == {"flange_contact": 288, "panel_contact": 530, "timber_face_contact": 584},
            "all 1402 complete contact rows required")
    require(field["parameters"]["panel_intervals"] == 8
            and field["parameters"]["foundation_port_cell_mm"] == 70., "unchanged panel contact discretization required")
    panel_rows = {i: r for i, r in contacts.items() if r["kind"] == "panel_contact"}
    require(set(panel_rows) == set(panels), "all 530 original panel contact identities required")
    for identity, expected in panels.items():
        row = panel_rows[identity]
        require((row["first"], row["second"]) == (expected["first"], expected["second"]),
                "original panel contact ownership differs")
        original.close(row["point_xyz_mm"], expected["point_xyz_mm"], 1e-7, "original panel point differs")
        compression = linear.support.finite_scalar(row["compression_n"])
        require(compression >= 0., "panel compression cannot be tensile")
        original.close(row["force_on_first_xyz_n"], compression * np.asarray(expected["direction_xyz"]),
                       1e-6, "original panel force/director differs")
        for key in ("moment_at_point_model_xyz_nmm", "moment_on_first_at_point_xyz_nmm", "moment_on_second_at_point_xyz_nmm"):
            if key in row:
                original.close(row[key], [0., 0., 0.], 1e-8, "panel point law cannot add free couple")
    expected_counts = {"normal_contacts": 1574, "paired_timber_interfaces": 30,
        "paired_timber_compression_cells": 584, "timber_members": 20, "finite_fittings": 36,
        "flexible_panels": 6, "physical_bolt_axes": 70, "physical_shaft_bodies": 70,
        "structural_bodies": 132, "panel_screw_axes": 66, "finished_wood_bearing_spans": 82,
        "steel_bore_spans": 72, "radial_bearing_quadrature_ports": 308, "own_axial_end_captures": 140,
        "independent_lumped_frame_bolt_ports": 0}
    require(all(field["counts"].get(key) == value for key, value in expected_counts.items()),
            "complete contact/unchanged physical body producer counts differ")
    tables = (("panel_screw_actions", 66, "axis_id"), ("common_shaft_bearing_actions", 308, "id"),
              ("shaft_end_capture_actions", 140, "id"), ("common_shaft_section_cut_actions", 70, "axis_id"))
    for key, count, identity in tables:
        require(len(original.unique(field[key], identity)) == count, "unchanged action census differs: " + key)
    for key, count, identity in (("common_shaft_wood_bearing_actions", 82, ("axis_id", "surface_index")),
                                 ("common_shaft_steel_port_actions", 72, ("axis_id", "angle_id", "flange"))):
        require(len(field[key]) == len({tuple(r[i] for i in identity) for r in field[key]}) == count,
                "unchanged aggregate census differs: " + key)
    floor = original.unique(field["floor_actions"])
    require(sum(r["kind"] == "floor_normal" for r in floor.values()) == 32,
            "all original thirty-two floor normal ports required")
    require(len(field["body_identities"]) == len(set(field["body_identities"])) == 132
            and sum(i.startswith("shaft/") for i in field["body_identities"]) == 70,
            "all original 132 physical body identities required")
    original.identities(field, [r for rows in (field["contact_actions"], field["floor_actions"],
                        *[field[key] for key, _, _ in tables], field["common_shaft_wood_bearing_actions"],
                        field["common_shaft_steel_port_actions"]) for row in rows for r in (row, *row.get("cuts", []))])
    return {"contact_action_count": 1402, "normal_contact_count": 1574, "timber_contact_cell_count": 584,
            "panel_contact_q_law_independently_replayed": False}


def _scalar_point_row(mapping, host, point, direction):
    row = next(r for r in mapping["members"] if r["member"] == host)
    start, axis, point, direction = map(np.asarray, (row["reference_start_xyz_mm"], row["reference_axis_xyz"], point, direction))
    stations = np.asarray(row["reference_stations_mm"])
    station = float((point - start) @ axis)
    segment = int(np.clip(np.searchsorted(stations, station) - 1, 0, len(stations) - 2))
    low, high = stations[segment:segment + 2]
    t = float(np.clip((station - low) / (high - low), 0., 1.))
    arm = point - (start + axis * (low + t * (high - low)))
    local = np.r_[direction, np.cross(arm, direction) / 1000.]
    index = np.asarray(row["node_dof_indices"])
    data = np.r_[(1. - t) * local, t * local]
    columns = np.r_[index[segment], index[segment + 1]]
    return csr_matrix((data, (np.zeros(len(data), dtype=int), columns)), shape=(1, mapping["ndof"]))


def verify_complete_operator_maps(field, inputs, arrays, geometry, mapping):
    """Check new face/floor B rows from the independent production chart."""
    require(inputs["ndof"] == mapping["ndof"] == 8018 and len(inputs["groups"]) == 374,
            "complete source-bound production chart and spring groups required")
    contacts = inputs["contacts"]
    require(len(original.unique(contacts)) == len(contacts) == 1574
            and Counter(r["kind"] for r in contacts) == {"flange_contact": 288, "panel_contact": 530,
                "timber_face_contact": 584, "shaft_end_capture": 140, "floor_normal": 32},
            "all original and complete added normal operator paths required")
    C = read_csr(arrays, inputs["C"])
    require(C.shape == (1574, 8018), "complete normal operator dimensions differ")
    descriptors = {r["id"]: r for r in expected_complete_descriptors(geometry)}
    timber_indices, timber_metadata = [], []
    floors = original.unique([r for r in field["floor_actions"] if r["kind"] == "floor_normal"])
    for index, row in enumerate(contacts):
        if row["kind"] == "timber_face_contact":
            require(row["id"] in descriptors, "foreign complete timber operator")
            source = descriptors[row["id"]]
            require((row["first"], row["second"]) == (source["first"], source["second"])
                    and row["stiffness"] == source["axial_stiffness_n_mm"]
                    and canonical_sha(row["source_descriptor"]) == canonical_sha(source["source_descriptor"]),
                    "complete operator source/ownership/stiffness differs")
            point, normal = source["reference_first_point_xyz_mm"], source["reference_director_xyz"]
            original.close(row["point_xyz_mm"], point, 1e-8, "complete operator point differs")
            original.close(row["direction_xyz"], normal, 1e-8, "complete operator director differs")
            B = -_scalar_point_row(mapping, row["first"], point, normal) + _scalar_point_row(mapping, row["second"], point, normal)
            difference = C[index] - B
            require(not difference.nnz or abs(difference.data).max() <= 1e-10,
                    "complete face closing operator differs from first-order point chart")
            timber_indices.append(index)
            timber_metadata.append({k: row[k] for k in ("id", "kind", "first", "second", "point_xyz_mm",
                                                        "direction_xyz", "stiffness", "source_descriptor")})
        elif row["kind"] == "floor_normal":
            require(row["id"] in floors and row["first"] == floors[row["id"]]["first"] and row["stiffness"] == 25000.,
                    "original floor normal source differs")
            point = floors[row["id"]]["point_xyz_mm"]
            original.close(row["point_xyz_mm"], point, 1e-8, "original floor operator datum differs")
            difference = C[index] + _scalar_point_row(mapping, row["first"], point, [0., 0., 1.])
            require(not difference.nnz or abs(difference.data).max() <= 1e-10, "original floor normal q operator differs")
    require(len(timber_indices) == 584 and {contacts[i]["id"] for i in timber_indices} == set(descriptors),
            "complete independent timber normal operator census differs")
    matrix = C[timber_indices]
    operator_sha = canonical_sha({"CSR_shape": matrix.shape, "CSR_indptr": matrix.indptr.tolist(),
        "CSR_indices": matrix.indices.tolist(), "CSR_data": matrix.data.tolist(), "rows": timber_metadata})
    metadata = field["complete_timber_face_contact_metadata"]
    require(metadata["coordinate_map_sha256"] == canonical_sha(field["linear_timber_coordinate_map"])
            and metadata["contact_operator_sha256"] == operator_sha,
            "runtime complete chart/contact operator digest differs; coupon digest cannot transfer")
    footprints = {r["member"]: r for r in field["finished_floor_footprints"]}
    tangents = inputs["tangents"]
    require(len(tangents) == len(original.unique(tangents)) == 16 and len(footprints) == 8
            and {r["id"] for r in tangents} == {h + "/no-slip-" + str(i) for h in footprints for i in (0, 1)},
            "all sixteen original centroid floor input ports required")
    for row in tangents:
        host = row["first"]
        point = np.asarray(footprints[host]["polygons_xyz_mm"][0]).mean(axis=0)
        component = int(row["id"][-1])
        require(row["kind"] == "floor_tangent" and row["stiffness"] == 100000., "original floor tangent law differs")
        original.close(row["point_xyz_mm"], point, 1e-8, "original centroid operator datum differs")
        difference = read_csr(arrays, row["B"]) - _scalar_point_row(mapping, host, point, np.eye(3)[component])
        require(not difference.nnz or abs(difference.data).max() <= 1e-10, "original centroid q operator differs")
    return {"complete_face_and_original_floor_B_rows_independently_replayed": True,
            "runtime_coordinate_map_sha256": canonical_sha(mapping), "runtime_contact_operator_sha256": operator_sha,
            "original_material_K_reassembled": False}


def _read_record(record, field=None):
    require(isinstance(record, dict) and isinstance(record.get("path"), str)
            and isinstance(record.get("sha256"), str) and len(record["sha256"]) == 64,
            "one immutable source record required")
    path = (ROOT / record["path"]).resolve()
    require(path.parent == PACKET and str(path.relative_to(ROOT)) == record["path"],
            "exclusive current execution packet record required")
    payload = path.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == record["sha256"], "current immutable record changed: " + record["path"])
    if field is not None:
        require(field["source_sha256"].get(record["path"]) == record["sha256"], "field omits current immutable record")
    return payload


def verify_execution(field, *, driver_sha256, method_receipt_path, method_receipt_sha256):
    execution = field["complete_timber_a12_execution"]
    command = execution["command"]
    require(isinstance(command, list) and len(command) >= 2 and all(isinstance(v, str) and v for v in command)
            and (ROOT / command[1]).resolve() == ROOT / DRIVER, "actual new complete-timber runner command required")
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False, exit_on_error=False)
    parser.add_argument("--method-input", type=Path, required=True)
    parser.add_argument("--method-input-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cases", nargs="+", default=["a12-rear"])
    for flag, value in (("wall-seconds", 600.), ("wood-bedding", 1.), ("contact-edge", 70.)):
        parser.add_argument("--" + flag, type=float, default=value)
    for flag, value in (("newton-limit", 300), ("intervals", 8)):
        parser.add_argument("--" + flag, type=int, default=value)
    try:
        args, remaining = parser.parse_known_args(command[2:])
    except (argparse.ArgumentError, SystemExit) as exc:
        raise ValueError("invalid complete-timber execution arguments") from exc
    receipt_path = Path(method_receipt_path).resolve()
    require(not remaining and receipt_path.parent == PACKET and args.method_input.resolve() == receipt_path
            and args.method_input_sha256 == method_receipt_sha256 and args.out.resolve().parent == PACKET
            and args.cases == ["a12-rear"] and args.wall_seconds == 600. and args.newton_limit == 300
            and args.wood_bedding == 1. and args.intervals == 8 and args.contact_edge == 70.,
            "actual command must retain frozen one-case cold options")
    method_record = {"path": str(receipt_path.relative_to(ROOT)), "sha256": method_receipt_sha256}
    receipt = json.loads(_read_record(method_record, field))
    require(receipt["schema"] == "thin_bolted_complete_timber_a12_method_inputs/v1"
            and receipt["driver"] == {"path": DRIVER, "sha256": driver_sha256}
            and receipt.get("method_checks_pass") is True and receipt["complete_face_basis"] == BASIS
            and receipt["complete_face_scenario"] == SCENARIO
            and receipt["historical_q_force_or_acceptance_transferred"] is False
            and receipt["floor_datum_or_constitutive_law_changed"] is False
            and receipt["execution_authorization_supplied_by_receipt"] is False
            and receipt["original_physical_fields_source_sha256"] == NUMERICAL_SHA256
            and receipt["fixed_options"] == {"cases": ["a12-rear"], "wood_bedding": 1., "intervals": 8,
                "contact_edge": 70., "newton_limit": 300, "wall_seconds": 600.}
            and receipt["expected_census"] == {"timber": 20, "fittings": 36, "panels": 6, "shafts": 70,
                "bodies": 132, "dofs": 8018, "timber_pairs": 30, "timber_cells": 584,
                "compression_contacts": 1402, "normal_contacts": 1574}
            and receipt["release"] == field["release"] and all(v is False for v in receipt["release"].values()),
            "reviewed distinct method input receipt required")
    require(execution["loaded_driver_sha256"] == driver_sha256
            and execution["loaded_admission_sha256"] == LOADED_PRODUCER_SHA256
            and execution["loaded_adapter_sha256"] == ADAPTER_SHA256
            and execution["nested_lean_execution_is_a_reused_internal_call"] is True
            and execution["method_input"] == method_record and execution["one_case_only"] is True
            and execution["automatic_retries"] == 0 and execution["wall_time_limit_seconds"] == 600.
            and execution["controller"] == "frozen-lean-common-shaft-incremental-original-cold"
            and execution["environment"]["OPENBLAS_NUM_THREADS"] == "1"
            and execution["warm_initialization"] is None and execution["all_30_patches_used_once"] is True
            and execution["original_floor_datum_and_law_preserved"] is True
            and execution["new_constitutive_law"] is False and execution["native_or_CAD_execution"] is False
            and execution["old_q_force_or_acceptance_transfer"] is False,
            "fresh loaded code and truthful original-controller reuse required")
    inner = [command[0], "-m", "scripts.run_thin_bolted_linear_timber_frame", "--cases", "a12-rear",
        "--out", str(args.out), "--wall-seconds", "600", "--newton-limit", "300", "--wood-bedding", "1",
        "--intervals", "8", "--contact-edge", "70"]
    require(field["lean_joint_execution"]["command"] == inner
            and field["common_shaft_execution"]["command"] == command,
            "actual outer and truthful reused inner invocation differ")
    params = field["parameters"]
    fixed = {"complete_timber_a12_driver_sha256": driver_sha256,
        "complete_timber_a12_method_input_sha256": method_receipt_sha256,
        "beam_size_mm": 150., "shaft_max_segment_mm": 25., "panel_intervals": 8,
        "foundation_port_cell_mm": 70., "floor_corner_contact_n_mm": 25000.,
        "floor_no_slip_xy_penalty_n_mm": 100000., "shaft_steel_E_mpa": 200000., "shaft_steel_nu": .3,
        "shaft_diameter_scale": 1., "end_capture_stiffness_n_mm": 1000.,
        "Hillman_axial_lateral_stiffness_n_mm": 1000., "fitting_section": "gross",
        "lean_case_wall_time_limit_seconds": 600., "numerical_newton_iteration_limit_per_floor_pattern": 300}
    require(all(params.get(k) == v for k, v in fixed.items()), "complete reviewed physical/numerical parameters differ")
    require(abs(params["wood_radial_foundation_n_mm2"] - 1000. / 38.1) <= 1e-8
            and abs(params["plate_radial_foundation_n_mm2"] - 10000. / 5.55625) <= 1e-8,
            "original declared bore foundation scenario required")
    pins = source_pins(linear.merge_pins(receipt["source_sha256"], field["source_sha256"],
        {DRIVER: driver_sha256, ADAPTER: ADAPTER_SHA256, PREPARATION: PREPARATION_SHA256,
         method_record["path"]: method_receipt_sha256}))
    require(all(field["source_sha256"].get(k) == v for k, v in receipt["source_sha256"].items())
            and all(field["source_sha256"].get(k) == receipt["source_sha256"].get(k) == v
                    for k, v in {OWN: LOADED_PRODUCER_SHA256, DRIVER: driver_sha256,
                                  ADAPTER: ADAPTER_SHA256, PREPARATION: PREPARATION_SHA256}.items()),
            "current field omits loaded method source pins")
    return execution, receipt, pins


def _gradient_record_summary(field):
    replay = field["response"]["original_gradient_replay_v1"]
    capture = field["response"]["original_closed_branch_capture_v1"]
    return {"operator_inputs": replay["operator_inputs"], "operator_array_bundle": replay["operator_array_bundle"],
        "original_closed_branch_capture": replay["original_closed_branch_capture"],
        "final_branch_array_bundle": capture["array_bundle"],
        "final_q_canonical_sha256": replay["final_q_canonical_sha256"],
        "observed_gradient_canonical_sha256": replay["observed_branch"]["gradient_canonical_sha256"],
        "gradient_inf_n": replay["observed_branch"]["gradient_inf_n"],
        "same_state_support_mask_consistent": replay["same_state_support_mask_consistent"]}


def audit_complete_timber_state(path_or_bytes, *, driver_sha256, method_receipt_path, method_receipt_sha256):
    """Admit identical complete bytes after source/map/law/gradient/body checks."""
    require(isinstance(path_or_bytes, (bytes, str, Path)), "immutable complete field bytes or one path required")
    path = None if isinstance(path_or_bytes, bytes) else Path(path_or_bytes)
    payload = path.read_bytes() if path is not None else path_or_bytes
    field = json.loads(payload)
    before = canonical_sha(field)
    require(field["schema"] == "thin_bolted_common_shaft_frame/v1"
            and field["candidate"] == "compact-floor-flush-thin-bolted-development"
            and field["layout_report_sha256"] == original.arithmetic.PINS["mixed-offset-rows-shallow-wires-v4.json"]
            and field["geometry_cache_sha256"] == GEOMETRY_PINS[CACHE]
            and field["case_id"] == "a12-rear" and field["accessory_placement"] == "retained-original-top-hold",
            "one complete source-bound A12 rear original accessory field required")
    floor_reuse.require_unreleased(field.get("release"))
    require(field["complete_contact_admission_pending"] is True
            and all(field[k] is False for k in ("complete_joint_acceptance", "complete_joint_capacity_established",
                                               "compatible_numerical_mvp_complete")), "unreleased conditional field required")
    response = field["response"]
    require(response["converged"] is True and "q" in response and field["usable_conditional_actions"] is True
            and response["physical_residual_uses_unmodified_laws"] is True
            and 0. < linear.support.finite_scalar(response["generalized_residual_tolerance_n"]) <= 1e-5
            and 0. <= linear.support.finite_scalar(response["gradient_inf_n"]) <= response["generalized_residual_tolerance_n"],
            "failed or unaccepted numerical field cannot supply admitted actions")
    identity = {k: field[k] for k in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    require(field["state_id"] == "thin-v4-" + canonical_sha(identity)[:24], "complete current state identity differs")
    execution, _, pins = verify_execution(field, driver_sha256=driver_sha256,
        method_receipt_path=method_receipt_path, method_receipt_sha256=method_receipt_sha256)
    geometry = read_complete_geometry()
    require(all(field["source_sha256"].get(k) == v for k, v in geometry["source_sha256"].items()),
            "complete field omits authenticated face/map dependencies")
    _, cache, _, _, _, _, base_pins = linear.common.read_sources()
    mapping, q = linear.verify_timber_map(field, cache, linear.spans.read_member_span_geometry())
    faces = verify_complete_face_actions(field, geometry, mapping, q, adapter_sha256=ADAPTER_SHA256)
    census = verify_complete_action_census(field, linear.panel_contact_sources())
    floor = floor_reuse.verify_floor_q_laws(field, mapping, q)
    operator_record = field["complete_timber_original_operator_inputs"]
    input_ref = {k: operator_record[k] for k in ("path", "sha256")}
    inputs = json.loads(_read_record(input_ref, field))
    bundle = inputs["array_bundle"]
    require(operator_record["array_bundle"] == bundle and execution["operator_inputs"] == operator_record
            and inputs["command"] == execution["command"] and inputs["method_input"] == execution["method_input"]
            and inputs["controller"] == execution["controller"] and inputs["historical_q_initialization"] is False
            and inputs["warm_initialization"] is None and inputs["material_K_includes_floor_tangents_or_damping"] is False
            and inputs["retained_source_CSR_order"] is True
            and inputs["no_operator_numeric_or_sparsity_normalization"] is True
            and field["parameters"]["complete_timber_original_operator_input_sha256"] == input_ref["sha256"]
            and field["parameters"]["complete_timber_original_operator_bundle_sha256"] == bundle["sha256"],
            "immutable pre-response original operator capture differs")
    _read_record(bundle, field)
    capture_ref = execution["final_original_closed_branch_capture"]
    capture = json.loads(_read_record(capture_ref, field))
    final_bundle = capture["array_bundle"]
    _read_record(final_bundle, field)
    require(capture["schema"] == "thin_bolted_complete_timber_original_closed_branch_capture/v1"
            and capture["q_kind"] == "q" and capture["diagnostic_only"] is False
            and capture["original_physical_fields_path"] == NUMERICAL
            and capture["original_physical_fields_source_sha256"] == NUMERICAL_SHA256
            and capture["fresh_known_original_function_called"] is True and capture["physical_laws_changed"] is False
            and capture["pre_response_operator_inputs"] == input_ref and capture["pre_response_array_bundle"] == bundle,
            "fresh current original closed-branch observation required")
    with np.load(ROOT / bundle["path"], allow_pickle=False) as arrays, np.load(ROOT / final_bundle["path"], allow_pickle=False) as final:
        operator_maps = verify_complete_operator_maps(field, inputs, arrays, geometry, mapping)
        original.close(final["q"], q, 0., "captured final q differs from immutable current field")
        observed_K = read_csr(final, capture["observed_linear_K"])
        replay = replay_original_gradient(field, inputs, arrays,
            observed_enabled_hosts=capture["observed_enabled_centroid_xy_hosts"], observed_linear_K=observed_K)
        original.close(final["gradient"], replay["observed_branch"]["signed_gradient_n"], 0., "captured signed original gradient differs")
    require(capture["full_signed_gradient_n"] == replay["observed_branch"]["signed_gradient_n"]
            and capture["gradient_canonical_sha256"] == replay["observed_branch"]["gradient_canonical_sha256"]
            and capture["final_q_canonical_sha256"] == replay["final_q_canonical_sha256"]
            and capture["gradient_inf_n"] == replay["observed_branch"]["gradient_inf_n"]
            and capture["potential_energy_nmm"] == replay["observed_branch"]["potential_energy_nmm"]
            and response["gradient_inf_n"] == capture["gradient_inf_n"]
            and replay["same_state_support_mask_consistent"] is True
            and replay["observed_branch"]["gradient_inf_n"] <= 1e-5,
            "fresh signed original residual, mask and accepted current q must agree")
    saved_replay = response["original_gradient_replay_v1"]
    require(all(saved_replay.get(k) == v for k, v in replay.items())
            and saved_replay["original_closed_branch_capture"] == capture_ref
            and saved_replay["operator_inputs"] == input_ref and saved_replay["operator_array_bundle"] == bundle
            and saved_replay["replay_helper_sha256"] == LOADED_PRODUCER_SHA256,
            "current gradient replay aliases/source records differ")
    source_capture = response["original_closed_branch_capture_v1"]
    require(source_capture == {**capture_ref, "array_bundle": final_bundle,
                "final_q_canonical_sha256": capture["final_q_canonical_sha256"],
                "gradient_canonical_sha256": capture["gradient_canonical_sha256"]},
            "current original capture alias differs")
    pins = source_pins(linear.merge_pins(pins, base_pins, geometry["source_sha256"], inputs["source_sha256"],
                                      capture["source_sha256"]))
    unchanged = linear.common_export.audit_common_shaft_state(field)
    require(unchanged[linear.common_export.ACCEPTANCE_KEY] is True, "complete same-field 132-body/global/support/load audit failed")
    pins = source_pins(linear.merge_pins(pins, unchanged["source_sha256"]))
    require(canonical_sha(field) == before and (path is None or hashlib.sha256(path.read_bytes()).hexdigest()
                                               == hashlib.sha256(payload).hexdigest()), "immutable complete field changed during admission")
    return {"schema": SCHEMA, SUCCESS: True, **{k: field[k] for k in linear.IDENTITIES},
        "field_sha256": hashlib.sha256(payload).hexdigest(), "field_canonical_sha256": before, "source_sha256": pins,
        "actual_complete_timber_execution": execution, "linear_timber_map_checks_pass": True,
        "linear_timber_face_checks": faces, "complete_action_census": census, "floor_q_law_checks": floor,
        "complete_operator_map_checks": operator_maps, "original_gradient_checks": _gradient_record_summary(field),
        "support_search_checks": {"final_q_canonical_sha256": replay["final_q_canonical_sha256"],
                                 "controller": execution["controller"], "support_search_execution_performed": False},
        "independent_common_shaft_audit": unchanged, "native_CAD_material_K_assembly_or_response_solve": False,
        "small_motion_complete_capacity_or_release_established": False, "release": {k: False for k in field["release"]}}


def require_admitted_payload(field_bytes, receipt, *, admission_sha256):
    """Authenticate an existing exact receipt cheaply, without operator replay."""
    require(isinstance(field_bytes, bytes) and admission_sha256 == LOADED_PRODUCER_SHA256,
            "immutable admitted bytes and mandatory actual gate source SHA required")
    field = json.loads(field_bytes)
    require(receipt["schema"] == SCHEMA and receipt.get(SUCCESS) is True
            and receipt["field_sha256"] == hashlib.sha256(field_bytes).hexdigest()
            and receipt["field_canonical_sha256"] == canonical_sha(field)
            and all(receipt[k] == field[k] for k in linear.IDENTITIES)
            and receipt["source_sha256"].get(OWN) == admission_sha256,
            "actual complete-field admission/raw/canonical/state receipt required")
    floor_reuse.require_unreleased(field.get("release"))
    identity = {k: field[k] for k in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    require(field["schema"] == "thin_bolted_common_shaft_frame/v1"
            and field["candidate"] == "compact-floor-flush-thin-bolted-development"
            and field["linear_timber_face_method"] == BASIS
            and field["layout_report_sha256"] == original.arithmetic.PINS["mixed-offset-rows-shallow-wires-v4.json"]
            and field["geometry_cache_sha256"] == GEOMETRY_PINS[CACHE]
            and field["state_id"] == "thin-v4-" + canonical_sha(identity)[:24]
            and field["response"]["converged"] is True and field["usable_conditional_actions"] is True
            and field["release"] and all(v is False for v in field["release"].values())
            and receipt["release"] == field["release"], "fresh unreleased admitted current vector required")
    q = original.array(field["response"]["q"], (field["counts"]["dofs"],))
    checks = _gradient_record_summary(field)
    replay = field["response"]["original_gradient_replay_v1"]
    gradient = original.array(replay["observed_branch"]["signed_gradient_n"], q.shape)
    require(receipt["original_gradient_checks"] == checks and checks["same_state_support_mask_consistent"] is True
            and checks["final_q_canonical_sha256"] == canonical_sha(q.tolist())
            and receipt["support_search_checks"]["final_q_canonical_sha256"] == checks["final_q_canonical_sha256"]
            and 0. <= linear.support.finite_scalar(checks["gradient_inf_n"]) <= 1e-5
            and replay["q_kind"] == "q" and replay["diagnostic_only"] is False
            and checks["observed_gradient_canonical_sha256"] == canonical_sha(gradient.tolist())
            and checks["gradient_inf_n"] == float(abs(gradient).max())
            and field["response"]["gradient_inf_n"] == checks["gradient_inf_n"],
            "actual same-q original gradient/support receipt required")
    for key in ("operator_inputs", "operator_array_bundle", "original_closed_branch_capture", "final_branch_array_bundle"):
        _read_record(checks[key], field)
        require(receipt["source_sha256"].get(checks[key]["path"]) == checks[key]["sha256"],
                "admission omits current original operator/capture pin")
    pins = source_pins(linear.merge_pins(receipt["source_sha256"], field["source_sha256"]))
    return field, pins
