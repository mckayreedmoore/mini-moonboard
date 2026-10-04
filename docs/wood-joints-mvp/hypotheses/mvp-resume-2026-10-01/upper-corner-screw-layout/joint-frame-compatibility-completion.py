"""Couple four continuous knee shafts to the existing elastic frame ports.

The reviewed 104-axis geometry and its original gravity are retained. The
four knee shafts replace their twenty lumped spring rows. Their bending,
axial extension, circular bore gaps, and two series end contacts participate
in the same equilibrium as all other frame interfaces. This remains a
conditional elastic, first-order calculation; no reference failure is repaired.

Importing this module neither reads evidence nor executes a calculation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy import linalg, sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = HERE.parent
RAW = HERE / "rawlocal/joint-frame-compatibility-completion"
OPERATORS = HERE / "operators-attempt02"
CONTRACT = HERE / "rawlocal/knee-compatible/prepare-attempt02/input-contract.json"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PERMANENT = "dead-only"
ALL_CASES = (*CASES, PERMANENT)
PERMANENT_BASE = HERE/"rawlocal/dead-load-check/parent-attempt06"
PERMANENT_PINS = {
    PERMANENT_BASE/"comparison.json": "20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75",
    PERMANENT_BASE/"response.npz": "9ff6f4ca177029b2c03acfb5425be9f943ad34679c8ab59013eb36764dd92f14",
    PERMANENT_BASE/"producer.py.snapshot": "ffdb2ee797000c055cd67c6e46ac80e549b4865a79346e728074625767bf213d",
}
AXES = tuple(f"knee_outer_{side}_side_{number}" for side in ("left", "right") for number in (1, 2))
PINS = {
    CONTRACT: "f2876952e6b71d59acdbf20dacaef233444402e50bfcc6d3b9ec1967f2cad01f",
    OPERATORS / "operators.npz": "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    OPERATORS / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    OPERATORS / "model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    OPERATORS / "model-inputs.json": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    OPERATORS / "B.npz": "d109f7db25cb05619e26560e501e7e82f3608fdbb3580f76e64f9beae916128a",
    HERE / "knee-compatible.py": "8bfd4aab145e468f477a04a23073feebab9d9c3a0b4bb4cc1bc2407399fb3413",
    HERE / "upper-right-combined-transfer.py": "fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0",
}
ROTATION_SCALE = 1000.0
SOLVER_SETTINGS = {
    "verbose": False, "max_iter": 150, "time_limit": 60.0,
    "tol_gap_abs": 1e-8, "tol_gap_rel": 1e-10, "tol_feas": 1e-10,
    "max_threads": 1, "direct_solve_method": "auto",
}
REFINEMENT_SETTINGS = {**SOLVER_SETTINGS, "tol_gap_abs": 1e-9, "tol_gap_rel": 1e-13,
    "tol_feas": 1e-10, "iterative_refinement_abstol": 1e-14,
    "iterative_refinement_reltol": 1e-14, "iterative_refinement_max_iter": 20}
PANEL_SCREW_ROLES = ("panel_screw_lateral_plane", "non_qualifying_parametric_screw_withdrawal")
STATE_TAGS = {case+("_zero" if gap == 0 else "_gap"): (case, gap) for case in ALL_CASES for gap in (0., 1.)}
PRIMARY_DOCS = (
    "https://clarabel.org/stable/python/getting_started_py/",
    "https://raw.githubusercontent.com/oxfordcontrol/Clarabel.rs/v0.11.1/src/solver/implementations/default/settings.rs",
)
DIAGNOSTICS = HERE / "knee-compatible-suite.py"
DIAGNOSTICS_SHA256 = "9798402070802a1804f4c9797fea336cda66951179340c1255e7122315990304"
FLOOR_MASK_METHOD = HERE/"floor_seed.py"
FLOOR_MASK_SHA256 = "42fdf8942e0994f1627bdfc407d2bae53d261077dcc1e7bcbc5240e9882a7f5f"
FLOOR_FAILURE_PREFIX = "STOP: no audited coupled floor branch among 256 masks: "
PARTIAL_STATUS = "PARTIAL_CONDITIONAL_COUPLED_FRAME_STATES_WITH_DECLARED_STOPS"


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


class UnacceptedTrial(ValueError):
    """Finite solver fields retained solely for diagnosis, never acceptance."""
    def __init__(self, message, force, motion, rigid, solver, audit=None):
        super().__init__(message)
        self.trial = {"force": force, "motion": motion, "rigid": rigid, "solver": solver, "audit": audit}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed: " + str(path))


def annulus_points(inner, outer, radial_order=4, angular_order=16):
    """Fixed physical annulus quadrature; both transverse tilt axes are retained."""
    nodes, weights = np.polynomial.legendre.leggauss(radial_order)
    radius = inner + (nodes + 1) * (outer - inner) / 2
    angle = (np.arange(angular_order) + 0.5) * 2 * math.pi / angular_order
    area = np.repeat(radius * weights * (outer - inner) / 2 * 2 * math.pi / angular_order,
                     angular_order)
    points = np.column_stack(((radius[:, None] * np.cos(angle)).ravel(),
                              (radius[:, None] * np.sin(angle)).ravel()))
    expected_area = math.pi * (outer**2 - inner**2)
    expected_second = math.pi * (outer**4 - inner**4) / 4
    require(abs(area.sum() - expected_area) < 1e-10
            and np.max(abs(area @ points)) < 1e-10
            and np.max(abs(points.T @ (area[:, None] * points) - expected_second * np.eye(2))) < 1e-9,
            "annulus area/centroid/second moments differ from exact integrals")
    return points, area


def beam_quotient(model):
    """Free beam bending plus exact two-end uniform axial compliance."""
    scalar_size = model["scalar_size"]
    transverse_size = 2 * scalar_size
    size, length = transverse_size + 2, model["length"]
    stiffness = np.zeros((size, size))
    stiffness[:transverse_size, :transverse_size] = model["K"][:transverse_size, :transverse_size]
    axial = 200000.0 * math.pi * model["diameter"]**2 / (4 * length)
    stiffness[-2:, -2:] = axial * np.array([[1.0, -1.0], [-1.0, 1.0]])
    rigid = np.zeros((size, 5))
    for component in range(2):
        offset = component * scalar_size
        rigid[offset:offset+scalar_size:2, 2*component] = 1
        rigid[offset:offset+scalar_size:2, 2*component+1] = (model["nodes"] - length/2) / ROTATION_SCALE
        rigid[offset+1:offset+scalar_size:2, 2*component+1] = length / ROTATION_SCALE
    rigid[-2:, -1] = 1
    orthogonal, _ = linalg.qr(rigid, mode="full")
    elastic = orthogonal[:, 5:]
    reduced = elastic.T @ stiffness @ elastic
    factor = linalg.cho_factor((reduced + reduced.T)/2, lower=True)
    compliance = elastic @ linalg.cho_solve(factor, elastic.T)
    force_error = float(np.max(abs(stiffness @ compliance - elastic @ elastic.T)))
    rigid_error = float(np.max(abs(stiffness @ rigid)) / max(1, np.max(abs(stiffness))))
    require(force_error <= 1e-5 and rigid_error <= 1e-12,
            "free shaft elastic quotient failed unchanged stiffness identity")
    tension = np.zeros(size)
    tension[-2:] = [-100.0, 100.0]
    displacement = compliance @ tension
    expected = 100.0 / axial
    require(abs(displacement[-1] - displacement[-2] - expected) < 1e-8,
            "uniform shaft axial extension differs from EA/L")
    return stiffness, rigid, compliance, {
        "elastic_force_projector_max_error": force_error,
        "rigid_stiffness_relative_max_error": rigid_error,
        "100_n_axial_extension_mm": float(displacement[-1] - displacement[-2]),
        "analytic_axial_extension_mm": expected,
        "shaft_degrees_of_freedom": size,
        "free_rigid_modes": 5,
    }


def joint_ports(contract, core, radial_order, angular_order):
    """Build physical force/displacement maps, without imposed receiver drives."""
    labels, wood_terms, bore_pairs, profiles = [], [], [], []
    bolt_maps, washer_maps, stiffnesses, unilateral = [], [], [], []
    beam_blocks, rigid_blocks, compliance_blocks, certificates = [], [], [], []
    shaft_size = 102

    def append(label, wood, bolt, washer, stiffness, one_sided):
        index = len(labels)
        labels.append(label)
        wood_terms.append(wood)
        bolt_maps.append(bolt)
        washer_maps.append(washer)
        stiffnesses.append(float(stiffness))
        unilateral.append(bool(one_sided))
        return index

    for shaft_index, axis in enumerate(AXES):
        geometry = contract["geometry"][axis]
        helper = core.pure_helper(geometry["modeled_wood_grip_mm"])
        model = core.assemble(geometry, helper)
        matrix, rigid, compliance, certificate = beam_quotient(model)
        require(matrix.shape == (shaft_size, shaft_size), "retained 25-node shaft layout changed")
        beam_blocks.append(matrix)
        rigid_blocks.append(rigid)
        compliance_blocks.append(compliance)
        certificates.append({"axis_id": axis, **certificate})
        normal = np.asarray(geometry["bolt_axis_xyz"])
        # The two columns span physical global transverse directions. A fixed
        # basis, rather than a solved tilt direction, also covers zero force.
        seed = np.eye(3)[np.argmin(abs(normal))]
        first = np.cross(normal, seed)
        first /= np.linalg.norm(first)
        basis = np.column_stack((first, np.cross(normal, first)))
        start, end = [np.asarray(geometry[key]) for key in ("head_seat_point_mm", "nut_seat_point_mm")]
        require(np.linalg.norm(start + model["length"] * normal - end) < 1e-8,
                "shaft length and outer seat points differ")
        begin = len(labels)
        for sample_index, sample in enumerate(model["samples"]):
            point = start + sample["x_mm"] * normal
            member = geometry["receivers"][sample["receiver_index"]]["member"]
            pair = []
            for component in range(2):
                bolt = np.zeros(4 * shaft_size)
                bolt[shaft_index*shaft_size:shaft_index*shaft_size+100] = sample["map"][component, :100]
                direction = -basis[:, component]
                pair.append(append({"axis_id": axis, "role": "distributed_bore", "sample": sample_index,
                                    "component": component, "point_mm": point.tolist(), "member_id": member},
                                   [{"member_id": member, "point_mm": point.tolist(),
                                     "direction_global_xyz": direction.tolist()}], bolt, np.zeros(24),
                                   20 * model["diameter"] * sample["weight_mm"], False))
            bore_pairs.append({"rows": pair, "radial_gap_mm": sample["gap_mm"]})

        profile = contract["model"]["end_profile"]
        inner = profile["washer_ID_max_mm"] / 2
        for end_index, (point, member, sign) in enumerate(((start, geometry["receiver_order"][0], 1),
                                                        (end, geometry["receiver_order"][-1], -1))):
            washer_index = 2 * shaft_index + end_index
            for surface, outer, coefficient in (("head", profile["hypothetical_concentric_head_and_nut_flat_radius_mm"], 10000.0),
                                                 ("wood", profile["washer_OD_min_mm"]/2, 20.0)):
                points, areas = annulus_points(inner, outer, radial_order, angular_order)
                profiles.append({"axis_id": axis, "end_index": end_index, "surface": surface,
                                 "area_mm2": float(areas.sum()), "quadrature_points": len(areas)})
                for quadrature_index, (offset, area) in enumerate(zip(points, areas, strict=True)):
                    location = point + basis @ offset
                    washer = np.zeros(24)
                    washer[3*washer_index:3*washer_index+3] = np.r_[1, offset/ROTATION_SCALE]
                    bolt = np.zeros(4 * shaft_size)
                    terms = []
                    if surface == "head":
                        node = 0 if end_index == 0 else len(model["nodes"])-1
                        bolt[shaft_index*shaft_size+100+end_index] = sign
                        for component in range(2):
                            # Euler-Bernoulli end plane: axial displacement at
                            # offset r equals u_axial - r dot transverse slope.
                            bolt[shaft_index*shaft_size+component*model["scalar_size"]+2*node+1] = -sign*offset[component]/model["length"]
                        washer *= -sign
                    else:
                        washer *= sign
                        terms = [{"member_id": member, "point_mm": location.tolist(),
                                  "direction_global_xyz": (-sign*normal).tolist()}]
                    append({"axis_id": axis, "role": surface+"_seat", "end_index": end_index,
                            "sample": quadrature_index, "point_mm": location.tolist(), "member_id": member,
                            "area_mm2": float(area)}, terms, bolt, washer, coefficient*area, True)
        certificates[-1]["new_rows"] = [begin, len(labels)]
    return {
        "labels": labels, "wood_terms": wood_terms, "bore_pairs": bore_pairs, "profiles": profiles,
        "Bbolt": np.asarray(bolt_maps), "Dwasher": np.asarray(washer_maps),
        "k": np.asarray(stiffnesses), "unilateral": np.asarray(unilateral),
        "Kbolt": linalg.block_diag(*beam_blocks), "Rbolt": linalg.block_diag(*rigid_blocks),
        "Cbolt": linalg.block_diag(*compliance_blocks), "beam_quotient_certificates": certificates,
    }


def prepare(output, radial_order=4, angular_order=16):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned output child required")
    pins = {**PINS, Path(__file__).resolve(): sha(__file__)}
    for path in (PACKET / "simple_frame.py", PACKET / "both_corner_frame.py"):
        pins[path] = sha(path)
    reducer = module(HERE / "joint-frame-port-reduction.py", "joint_frame_port_source_paths")
    for path in reducer.source_pin_paths().values():
        require(path not in pins or pins[path] == sha(path), "conflicting native method input")
        pins[path] = sha(path)
    authenticate(pins)
    contract = read(CONTRACT)
    core = module(HERE / "knee-compatible.py", "joint_frame_knee_core")
    frame = module(PACKET / "simple_frame.py", "joint_frame_floor")
    rows = read(OPERATORS / "row-identities.json")
    with np.load(OPERATORS / "operators.npz", allow_pickle=False) as source:
        _, _, _, _, old_k, old_uni, normals, tangents, _, _ = frame.lump_floor(
            *[source[name] for name in ("H", "D", "e", "W")], rows)
    retained = [row for row in rows if row["ownership"]["second_body"] != "floor"]
    removed = [i for i, row in enumerate(retained) if row["row_id"].rsplit("/", 1)[0] in AXES]
    require(len(removed) == 20, "four continuous shafts require twenty replaced lumped rows")
    kept = np.setdiff1d(np.arange(len(old_k)), removed)
    joint = joint_ports(contract, core, radial_order, angular_order)
    old_map = {int(original): i for i, original in enumerate(kept)}
    connections = {connection["axis_id"]: connection for connection in read(OPERATORS / "model-inputs.json")["connections"]}
    lateral = [old_map[i] for i, row in enumerate(retained)
               if i in old_map and row["ownership"]["role"] == "candidate_bolt_lateral_plane"
               and len(connections[row["row_id"].rsplit("/", 1)[0]]["receiver_member_ids"]) == 2]
    require(len(lateral) == 176, "unchanged two-receiver clearance inventory differs")
    pairs = np.asarray(lateral).reshape(-1, 2).tolist()
    gaps = [1.0625 if "/side_" in retained[int(kept[pair[0]])]["row_id"] else 1.15 for pair in pairs]
    for record in joint["bore_pairs"]:
        pairs.append([len(kept)+i for i in record["rows"]])
        gaps.append(record["radial_gap_mm"])
    request = {
        "schema": "joint_frame_port_request/v1", "source_operator_directory": OPERATORS.relative_to(ROOT).as_posix(),
        "old_kept_lumped_rows": kept.tolist(), "new_wood_port_terms": joint["wood_terms"],
        "new_port_count": len(joint["labels"]), "case_ids": list(CASES),
        # The maintained implementation may later grow a response stage. Bind
        # the executed preparation bytes at their immutable snapshot path.
        "source_sha256": {p.relative_to(ROOT).as_posix(): digest for p, digest in pins.items()
                          if p != Path(__file__).resolve()},
        "reviewed_bolt_axes": 104, "proposed_internal_ties_included": False,
    }
    output.mkdir(parents=True)
    snapshot = output / "producer.py.snapshot"
    snapshot.write_bytes(Path(__file__).read_bytes())
    request["source_sha256"][snapshot.relative_to(ROOT).as_posix()] = sha(snapshot)
    write(output / "wood-port-request.json", request)
    write(output / "port-labels.json", {"new_ports": joint["labels"], "profiles": joint["profiles"],
                                        "beam_quotient_certificates": joint["beam_quotient_certificates"]})
    np.savez_compressed(output / "joint-operators.npz", Bbolt=joint["Bbolt"], Dwasher=joint["Dwasher"],
                        Cbolt=joint["Cbolt"], Rbolt=joint["Rbolt"], Kbolt=joint["Kbolt"],
                        k=np.r_[old_k[kept], joint["k"]], unilateral=np.r_[old_uni[kept], joint["unilateral"]],
                        floor_normals=np.asarray([old_map[int(i)] for i in normals]),
                        floor_tangents=np.asarray([[old_map[int(i)] for i in pair] for pair in tangents]),
                        clearance_pairs=np.asarray(pairs), clearance_gaps=np.asarray(gaps),
                        old_kept_lumped_rows=kept)
    authenticate(pins)
    outputs = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    write(output / "receipt.json", {
        "schema": "joint_frame_compatibility_preparation/v1", "status": "PREPARED_COUPLED_PORTS_NOT_FRAME_RESPONSE",
        "source_sha256": request["source_sha256"], "output_sha256": outputs,
        "old_rows": len(old_k), "removed_rows": len(removed), "retained_rows": len(kept),
        "new_rows": len(joint["labels"]), "wood_bodies": 50, "shaft_free_modes": 20, "washer_free_modes": 24,
        "radial_order": radial_order, "angular_order": angular_order,
        "physical_release": False, "numerical_goal_complete": False,
    })
    print(json.dumps({"status": "PREPARED_COUPLED_PORTS_NOT_FRAME_RESPONSE", "new_rows": len(joint["labels"]),
                      "request_path": str(output / "wood-port-request.json"),
                      "request_sha256": sha(output / "wood-port-request.json")}), flush=True)


def conic_branch(H, D, e, W, k, unilateral, held, pairs, gaps, solver_settings=None):
    """One convex complementary-energy equilibrium at a selected floor branch."""
    import clarabel

    require(clarabel.__version__ == "0.11.1", "recorded Clarabel 0.11.1 runtime required")
    require(np.asarray(pairs).shape == (len(gaps), 2) and np.all(gaps >= 0),
            "invalid circular contact inventory")
    # A zero coefficient removes the norm from the exact energy. Keeping its
    # unconstrained epigraph adds a flat coordinate and an unnecessary cone.
    nonzero = gaps > 0
    pairs, gaps = np.asarray(pairs)[nonzero], np.asarray(gaps)[nonzero]
    positions = np.sort(np.r_[np.flatnonzero(k > 0), held])
    inverse = np.divide(1.0, k[positions], out=np.zeros(len(positions)), where=k[positions] > 0)
    quadratic = H[np.ix_(positions, positions)] + np.diag(inverse)
    quadratic = (quadratic + quadratic.T)/2
    require(np.all(np.diag(quadratic) > 0), "nonpositive active complementary-energy diagonal")
    force_scale = 1/np.sqrt(np.diag(quadratic))
    quadratic = force_scale[:, None]*quadratic*force_scale[None, :]
    n, count = len(positions), len(pairs)
    p = sparse.block_diag((sparse.csc_matrix(quadratic), sparse.csc_matrix((count, count))), format="csc")
    equality = sparse.hstack((sparse.csc_matrix(D[positions].T*force_scale),
                              sparse.csc_matrix((D.shape[1], count))), format="csc")
    bounded = np.flatnonzero(unilateral[positions])
    signs = sparse.csc_matrix((-np.ones(len(bounded)), (np.arange(len(bounded)), bounded)), shape=(len(bounded), n+count))
    cone = sparse.lil_matrix((3*count, n+count))
    local_pairs = np.searchsorted(positions, pairs)
    require(np.array_equal(positions[local_pairs], pairs), "clearance pair missing from active force coordinates")
    epigraph_scale = np.max(force_scale[local_pairs], axis=1)
    for i, pair in enumerate(local_pairs):
        cone[3*i, n+i] = -epigraph_scale[i]
        cone[3*i+1, pair[0]] = -force_scale[pair[0]]
        cone[3*i+2, pair[1]] = -force_scale[pair[1]]
    matrix = sparse.vstack((equality, signs, cone.tocsc()), format="csc")
    rhs = np.r_[W, np.zeros(len(bounded)+3*count)]
    cones = [clarabel.ZeroConeT(D.shape[1]), clarabel.NonnegativeConeT(len(bounded)),
             *[clarabel.SecondOrderConeT(3) for _ in pairs]]
    settings = clarabel.DefaultSettings()
    configuration = SOLVER_SETTINGS if solver_settings is None else solver_settings
    for key, value in configuration.items():
        setattr(settings, key, value)
    solver = clarabel.DefaultSolver(sparse.triu(p, format="csc"),
        np.r_[-e[positions]*force_scale, gaps*epigraph_scale], matrix, rhs, cones, settings)
    result = solver.solve()
    info = {"status": str(result.status), "iterations": result.iterations,
            "solve_time_seconds": result.solve_time, "objective": result.obj_val,
            "dual_objective": result.obj_val_dual, "primal_residual": result.r_prim,
            "dual_residual": result.r_dual, "force_variables": n, "circular_epigraphs": count,
            "force_diagonal_scale_range": [float(force_scale.min()), float(force_scale.max())],
            "linear_solver": solver.get_info().linsolver.name, "settings": configuration}
    force = np.zeros(len(k))
    force[positions] = force_scale*result.x[:n]
    rigid = -np.asarray(result.z[:D.shape[1]])
    motion = D @ rigid + e - H @ force
    if str(result.status) != "Solved":
        message = "STOP: coupled contact QP " + json.dumps(info)
        if all(np.all(np.isfinite(values)) for values in (force,motion,rigid)):
            raise UnacceptedTrial(message, force, motion, rigid, info)
        raise ValueError(message)
    return force, motion, rigid, info


def known_answer():
    """Analytic circular contact and axial series coupons for new dual signs."""
    force, motion, _, info = conic_branch(np.zeros((2, 2)), np.eye(2), np.zeros(2), np.array([3., 4.]),
                                         np.array([1000., 1000.]), np.zeros(2, dtype=bool),
                                         np.array([], dtype=int), np.array([[0, 1]]), np.array([0.575]))
    expected = np.array([3., 4.]) * (0.001+0.575/5)
    require(np.max(abs(force-[3., 4.])) < 1e-8 and np.max(abs(motion-expected)) < 1e-7,
            "coupled contact dual sign differs from analytic circular spring")
    compliance = np.array([[0.003, 0.0], [0.0, 0.007]])
    series_force, series_motion, _, series = conic_branch(compliance, np.eye(2), np.zeros(2), np.array([10., 10.]),
        np.array([1000., 2000.]), np.ones(2, dtype=bool), np.array([], dtype=int),
        np.empty((0, 2), dtype=int), np.array([]))
    require(np.max(abs(series_force-10)) < 1e-8 and np.max(abs(series_motion-[0.01, 0.005])) < 1e-7,
            "series elastic/contact partition differs from exact scalar answer")
    zero_force, zero_motion, _, zero = conic_branch(np.zeros((2, 2)), np.eye(2), np.zeros(2),
        np.array([3., 4.]), np.array([1000., 1000.]), np.zeros(2, dtype=bool),
        np.array([], dtype=int), np.array([[0, 1]]), np.array([0.]))
    require(np.max(abs(zero_force-[3., 4.])) < 1e-8
            and np.max(abs(zero_motion-[.003, .004])) < 1e-7 and zero["circular_epigraphs"] == 0,
            "zero-gap cone elimination differs from exact spring answer")
    open_force, open_motion, _, opened = conic_branch(np.zeros((1, 1)), np.zeros((1, 0)),
        np.array([-1.]), np.zeros(0), np.array([1000.]), np.ones(1, dtype=bool),
        np.array([], dtype=int), np.empty((0, 2), dtype=int), np.array([]))
    require(abs(open_force[0]) < 1e-7 and open_motion[0] == -1.,
            "open compression-only contact differs from exact answer")
    floor_D = np.zeros((24,344))
    floor_D[:8,2] = 1
    floor_D[8::2,0], floor_D[9::2,1] = 1, 1
    floor_W = np.zeros(344)
    floor_W[2] = 80
    floor_joint = {"k": np.r_[np.full(8,1000.), np.zeros(16)],
        "unilateral": np.r_[np.ones(8,dtype=bool), np.zeros(16,dtype=bool)],
        "floor_normals": np.arange(8), "floor_tangents": np.arange(8,24).reshape(8,2),
        "clearance_pairs": np.empty((0,2),dtype=int), "clearance_gaps": np.array([])}
    floor_force, floor_motion, _, floor_bearing, floor_audit, floor_history = solve_coupled(
        .001*np.eye(24), floor_D, np.zeros(24), floor_W, floor_joint,
        np.r_[np.ones(4,dtype=bool),np.zeros(4,dtype=bool)], 0.)
    require(floor_bearing.all() and np.max(abs(floor_force[:8]-10)) < 1e-7
            and np.max(abs(floor_motion[:8]-.01)) < 1e-7 and floor_audit["all_passed"],
            "fixed-floor-mask inactive-normal entry differs from exact equal-footprint answer")
    separated_e = np.zeros(24)
    separated_e[7] = -1
    separated_W = floor_W.copy()
    separated_W[2] = 70
    separated_f, separated_q, _, separated_bearing, separated_audit, separated_history = solve_coupled(
        .001*np.eye(24), floor_D, separated_e, separated_W, floor_joint, np.ones(8,dtype=bool), 0.)
    require(separated_bearing.tolist() == [True]*7+[False]
            and np.max(abs(separated_f[:7]-10)) < 1e-7 and separated_f[7] == 0
            and abs(separated_q[7]+.98) < 1e-7 and separated_audit["all_passed"],
            "separated footprint accepted unavailable force or violated original inactive normal law")
    return {"circular_force_n": force.tolist(), "circular_motion_mm": motion.tolist(),
            "analytic_circular_motion_mm": expected.tolist(), "circular_solver": info,
            "series_force_n": series_force.tolist(), "series_spring_motion_mm": series_motion.tolist(),
            "series_solver": series, "zero_gap_force_n": zero_force.tolist(),
            "zero_gap_motion_mm": zero_motion.tolist(), "zero_gap_solver": zero,
            "open_unilateral_force_n": open_force.tolist(), "open_unilateral_motion_mm": open_motion.tolist(),
            "open_unilateral_solver": opened, "clarabel_version": "0.11.1",
            "fixed_floor_mask_oracle": {"normal_forces_n": floor_force[:8].tolist(),
                "normal_motion_mm": floor_motion[:8].tolist(), "attempted_masks": len(floor_history),
                "original_physical_law_audit": floor_audit},
            "separated_floor_oracle": {"normal_forces_n": separated_f[:8].tolist(),
                "normal_motion_mm": separated_q[:8].tolist(), "bearing_mask": separated_bearing.tolist(),
                "attempted_masks": len(separated_history), "original_physical_law_audit": separated_audit},
            "primary_docs": list(PRIMARY_DOCS)}


def bind_packet(directory, pins, preserved_producer=False):
    """Authenticate actual consumed artifacts and their frozen input closure."""
    directory = Path(directory).resolve()
    receipt_path = directory / "receipt.json"
    receipt = read(receipt_path)
    require(isinstance(receipt.get("output_sha256"), dict) and receipt["output_sha256"],
            "completed packet output hashes required: " + str(directory))
    pins[receipt_path] = sha(receipt_path)
    for name, digest in receipt["output_sha256"].items():
        path = (directory / name).resolve()
        require(path.is_relative_to(directory), "output escapes its packet")
        require(path not in pins or pins[path] == digest, "conflicting consumed artifact")
        pins[path] = digest
    for name, digest in receipt["source_sha256"].items():
        path = (ROOT / name).resolve()
        if preserved_producer and path == Path(__file__).resolve():
            snapshot = directory/"producer.py.snapshot"
            require(receipt["output_sha256"].get(snapshot.name) == digest and sha(snapshot) == digest,
                    "historical live producer lacks exact receipt-bound snapshot")
            path = snapshot
        require(path.is_relative_to(ROOT) and (path not in pins or pins[path] == digest),
                "conflicting consumed input")
        pins[path] = digest
    authenticate(pins)
    return receipt


def refinement_known_answer():
    """Circular contact and near-open unilateral oracle at stricter tolerances."""
    f, q, _, circular = conic_branch(np.zeros((2,2)), np.eye(2), np.zeros(2), np.array([3.,4.]),
        np.full(2,1000.), np.zeros(2,dtype=bool), np.array([],dtype=int),
        np.array([[0,1]]), np.array([.575]), REFINEMENT_SETTINGS)
    expected = np.array([3.,4.])*(.001+.575/5)
    require(np.max(abs(f-[3.,4.])) < 1e-8 and np.max(abs(q-expected)) < 1e-8,
            "refinement circular oracle differs")
    hf = np.eye(2)*.001
    uf, uq, _, unilateral = conic_branch(hf, np.ones((2,1)), np.array([0.,-.0101228]),
        np.array([10.]), np.full(2,100000.), np.ones(2,dtype=bool), np.array([],dtype=int),
        np.empty((0,2),dtype=int), np.array([]), REFINEMENT_SETTINGS)
    law_residual = float(np.max(abs(uf-100000*np.maximum(uq,0))))
    require(law_residual < 1e-4 and abs(uf[0]-10) < 1e-4 and abs(uf[1]) < 1e-4
            and abs(uq[1]+.0000228) < 1e-8, "near-open unilateral refinement oracle differs")
    return {"circular_force_n": f.tolist(), "circular_motion_mm": q.tolist(), "circular_solver": circular,
        "near_open_unilateral_force_n": uf.tolist(), "near_open_unilateral_motion_mm": uq.tolist(),
        "near_open_unilateral_law_residual_n": law_residual, "unilateral_solver": unilateral,
        "solver_settings": REFINEMENT_SETTINGS, "primary_docs": list(PRIMARY_DOCS)}


def panel_screw_ports(rows, joint):
    """Map all 66 original screw axes' three laws to the retained force basis."""
    nonfloor = [row for row in rows if row["ownership"]["second_body"] != "floor"]
    kept = {int(old): index for index, old in enumerate(joint["old_kept_lumped_rows"])}
    selected = [kept[index] for index, row in enumerate(nonfloor) if row["ownership"]["role"] in PANEL_SCREW_ROLES]
    require(len(selected) == 198 and np.count_nonzero(joint["unilateral"][selected]) == 66,
            "panel screw three-component census differs")
    return np.asarray(selected,dtype=int)


def spring_expected(motion, k, unilateral, pairs, gaps):
    """Original contact laws, shared by acceptance and diagnostic witnesses."""
    expected = k * np.where(unilateral, np.maximum(motion, 0), motion)
    radii = np.linalg.norm(motion[pairs], axis=1)
    paired_k = k[pairs]
    require(np.max(abs(paired_k[:, 0]-paired_k[:, 1]), initial=0) < 1e-10, "paired bore coefficients differ")
    norm_scale = np.divide(np.maximum(radii-gaps, 0), radii,
                           out=np.zeros(len(radii)), where=radii > 0)
    expected[pairs] = paired_k * norm_scale[:, None] * motion[pairs]
    return expected


def force_law_audit(force, motion, rigid, H, D, e, W, k, unilateral, normals, tangents,
                    bearing, pairs, gaps, screw_ports=None):
    expected = spring_expected(motion, k, unilateral, pairs, gaps)
    finite = k > 0
    balance = D.T @ force - W
    body = balance[:300].reshape(50, 6)
    shaft = balance[300:320].reshape(4, 5)
    washer = balance[320:].reshape(8, 3)
    metrics = {
        "body_force_residual_n": float(np.max(abs(body[:, :3]))),
        "body_moment_residual_nmm": float(1000*np.max(abs(body[:, 3:]))),
        "shaft_force_residual_n": float(np.max(abs(shaft[:, [0, 2, 4]]))),
        "shaft_moment_residual_nmm": float(1000*np.max(abs(shaft[:, [1, 3]]))),
        "washer_force_residual_n": float(np.max(abs(washer[:, 0]))),
        "washer_moment_residual_nmm": float(1000*np.max(abs(washer[:, 1:]))),
        "spring_law_residual_n": float(np.max(abs(force[finite]-expected[finite]))),
        "minimum_unilateral_force_n": float(np.min(force[unilateral])),
        "held_floor_motion_mm": float(np.max(abs(motion[tangents[bearing]]), initial=0)),
        "released_floor_force_n": float(np.max(abs(force[tangents[~bearing]]), initial=0)),
        "port_compatibility_residual_mm": float(np.max(abs(motion-D@rigid-e+H@force))),
        "maximum_positive_unilateral_motion_mm": float(np.max(motion[unilateral])),
        "minimum_bearing_normal_force_n": float(np.min(force[normals[bearing]], initial=math.inf)),
        "released_floor_normal_force_n": float(np.max(abs(force[normals[~bearing]]), initial=0)),
        "released_floor_positive_motion_mm": float(np.max(motion[normals[~bearing]], initial=0)),
    }
    checks = {key: metrics[key] <= tolerance for key, tolerance in (
        ("body_force_residual_n", .1), ("body_moment_residual_nmm", 2),
        ("shaft_force_residual_n", .1), ("shaft_moment_residual_nmm", 2),
        ("washer_force_residual_n", .1), ("washer_moment_residual_nmm", 2),
        ("spring_law_residual_n", .1), ("held_floor_motion_mm", 1e-5),
        ("released_floor_force_n", 0), ("port_compatibility_residual_mm", 1e-8),
        ("released_floor_normal_force_n", .01), ("released_floor_positive_motion_mm", 1e-8),
        ("maximum_positive_unilateral_motion_mm", 10))}
    checks["nonnegative_contact"] = metrics["minimum_unilateral_force_n"] >= -.1
    checks["bearing_floor_branch"] = metrics["minimum_bearing_normal_force_n"] > .01
    if screw_ports is not None:
        metrics["panel_screw_law_residual_n"] = float(np.max(abs(force[screw_ports]-expected[screw_ports])))
        metrics["minimum_panel_screw_axial_force_n"] = float(np.min(force[screw_ports[unilateral[screw_ports]]]))
        checks["panel_screw_law_residual_n"] = metrics["panel_screw_law_residual_n"] < 1e-4
        checks["minimum_panel_screw_axial_force_n"] = metrics["minimum_panel_screw_axial_force_n"] >= -1e-4
    return {"checks": checks, "metrics": metrics, "all_passed": all(checks.values())}


def fixed_floor_branch(H, D, e, W, joint, bearing, gap_scale, solver_settings=None):
    """One fixed mask; only unavailable floor normal force variables are omitted."""
    k, uni, normals, tangents, pairs, gaps = [joint[name] for name in (
        "k", "unilateral", "floor_normals", "floor_tangents", "clearance_pairs", "clearance_gaps")]
    branch_k = k.copy()
    branch_k[normals[~bearing]] = 0
    try:
        force, motion, rigid, solver = conic_branch(H, D, e, W, branch_k, uni,
            tangents[bearing].ravel(), pairs, gap_scale*gaps, solver_settings)
    except UnacceptedTrial as error:
        trial = error.trial
        trial["audit"] = force_law_audit(trial["force"], trial["motion"], trial["rigid"], H,D,e,W,k,uni,
            normals,tangents,bearing,pairs,gap_scale*gaps,joint.get("panel_screw_ports"))
        raise
    audit = force_law_audit(force, motion, rigid, H, D, e, W, k, uni,
                            normals, tangents, bearing, pairs, gap_scale*gaps, joint.get("panel_screw_ports"))
    return force, motion, rigid, solver, audit


def solve_coupled(H, D, e, W, joint, initial_bearing, gap_scale):
    """Finite fixed-floor-mask search, audited against unchanged physical laws.

    The existing floor seed omits inactive normal variables. Its all-body QP
    adapter cannot take shaft/washer coordinates, so reuse only its inert mask
    iterator and evaluate each mask with this coupled conic formulation.
    """
    normals = joint["floor_normals"]
    require(len(normals) == 8, "finite floor search requires the existing eight footprints")
    require(sha(FLOOR_MASK_METHOD) == FLOOR_MASK_SHA256, "existing floor mask method changed")
    preferred = module(FLOOR_MASK_METHOD, "joint_frame_existing_floor_mask_iterator")
    initial = np.asarray(initial_bearing, dtype=bool)
    pending = [initial.copy(), *preferred._masks(normals)]
    remaining = sorted(itertools.product((False,True), repeat=8),
                       key=lambda mask: (np.count_nonzero(np.asarray(mask) != initial), -sum(mask), mask))
    pending.extend(np.asarray(mask) for mask in remaining)
    seen, history = set(), []
    while pending:
        bearing = np.asarray(pending.pop(0), dtype=bool)
        key = tuple(bearing)
        if key in seen:
            continue
        seen.add(key)
        entry = {"step": len(history), "bearing_footprints": np.flatnonzero(bearing).tolist(),
                 "inactive_floor_normals_omitted_from_force_coordinates": True}
        try:
            force, motion, rigid, solver, audit = fixed_floor_branch(H, D, e, W, joint, bearing, gap_scale)
        except ValueError as error:
            entry["numerical_branch_stop"] = str(error)
            history.append(entry)
            continue
        entry.update(normal_forces_n=force[normals].tolist(), normal_motion_mm=motion[normals].tolist(),
                     solver=solver, original_physical_law_audit=audit)
        history.append(entry)
        if audit["all_passed"]:
            return force, motion, rigid, bearing, audit, history
        violations = (bearing & (force[normals] <= .01)) | (~bearing & (motion[normals] > 1e-8))
        # First try the observed full update, then one-contact pivots. Every
        # unseen mask remains available in the finite deterministic fallback.
        updated = bearing ^ violations
        pivots = []
        for footprint in np.flatnonzero(violations):
            pivot = bearing.copy()
            pivot[footprint] = ~pivot[footprint]
            pivots.append(pivot)
        pending[:0] = [updated, *pivots]
    raise ValueError(FLOOR_FAILURE_PREFIX + json.dumps(history))


def floor_failure_summary(exception):
    """Summarize a complete preserved mask search without inventing a field."""
    require(exception.startswith(FLOOR_FAILURE_PREFIX), "only exhaustive fixed-mask stops may be reused")
    history = json.loads(exception[len(FLOOR_FAILURE_PREFIX):])
    require(len(history) == 256 and len({tuple(entry["bearing_footprints"]) for entry in history}) == 256
            and not any(entry.get("original_physical_law_audit", {}).get("all_passed") for entry in history),
            "stopped disposition lacks all 256 distinct unsuccessful masks")
    statuses, failures = {}, {}
    for entry in history:
        if "solver" in entry:
            status = entry["solver"]["status"]
            for gate, passed in entry["original_physical_law_audit"]["checks"].items():
                if not passed:
                    failures[gate] = failures.get(gate, 0)+1
        else:
            message = entry["numerical_branch_stop"]
            status = next((word for word in ("PrimalInfeasible", "InsufficientProgress", "AlmostSolved",
                          "NumericalError", "MaxIterations", "MaxTime") if word in message), "OtherNumericalStop")
        statuses[status] = statuses.get(status, 0)+1
    return {"attempted_unique_masks": len(history), "solver_status_counts": statuses,
            "failed_audit_gate_counts": failures, "accepted_force_field_exists": False,
            "scope": "No branch passed the unchanged physical audit; numerical stops are not physical infeasibility proofs."}


def source_lumped_force(raw, rows):
    """Invert saved raw = T.T f by summing each existing floor footprint.

    Retained rows are identity maps. Every footprint's normal and tangent
    weights sum to one, so the saved distributed forces sum to its resultant.
    T @ raw would average the weights a second time and change floor forces.
    """
    retained = [row for row in rows if row["ownership"]["second_body"] != "floor"]
    floor = [row for row in rows if row["ownership"]["second_body"] == "floor"]
    by_id = {row["row_id"]: row["row"] for row in rows}
    result = [float(raw[row["row"]]) for row in retained]
    for member in sorted({row["ownership"]["first_body"] for row in floor}):
        cells = [row for row in floor if row["ownership"]["first_body"] == member
                 and row["ownership"]["role"] == "floor_normal"]
        require(cells, "source footprint has no normal cells")
        result.append(float(sum(raw[row["row"]] for row in cells)))
        for component in (2, 3):
            result.append(float(sum(raw[by_id[row["row_id"]+"_friction/local-dof-"+str(component)]]
                                    for row in cells)))
    return np.asarray(result)


def active_rigid_rank(D, motion, joint, bearing, gap_scale):
    """Activity-sensitive rigid-map rank; no prestress or stability inference."""
    k, uni, pairs, gaps = [joint[name] for name in ("k", "unilateral", "clearance_pairs", "clearance_gaps")]
    rows = []
    for tolerance in (0., 1e-8, 1e-6):
        active = (k > 0) & (~uni | (motion > tolerance))
        active[pairs] = (np.linalg.norm(motion[pairs], axis=1) > gap_scale*gaps+tolerance)[:, None]
        active[joint["floor_tangents"][bearing]] = True
        singular = linalg.svdvals(D[active], check_finite=False)
        rank = int(np.count_nonzero(singular > 1e-10*singular[0]))
        rows.append({"activity_motion_tolerance_mm": tolerance, "active_port_rows": int(active.sum()),
                     "rank": rank, "rigid_coordinate_count": D.shape[1],
                     "smallest_singular_value": float(singular[-1]),
                     "largest_singular_value": float(singular[0])})
    return {"activity_sensitivities": rows, "relative_rank_threshold": 1e-10,
            "full_rank_at_all_recorded_activity_thresholds": all(row["rank"] == D.shape[1] for row in rows),
            "second_order_or_dynamic_stability_established": False,
            "scope": "Rank of currently active rigid force/displacement maps only; filled-body compliance, sampled activity and first-order geometry remain conditional."}


def floor_diagnostic(force, motion, D, joint, bearing, gap_scale, rows, labels):
    """Save rejected branch witnesses; this never promotes a branch to acceptance."""
    k, uni, normals, tangents, pairs, gaps = [joint[name] for name in (
        "k", "unilateral", "floor_normals", "floor_tangents", "clearance_pairs", "clearance_gaps")]
    retained = [row for row in rows if row["ownership"]["second_body"] != "floor"]
    floor_rows = [row for row in rows if row["ownership"]["second_body"] == "floor"]
    members = sorted({row["ownership"]["first_body"] for row in floor_rows})
    source_labels = [{"source_raw_row": row["row"], "row_id": row["row_id"],
                      "ownership": row["ownership"]} for row in retained]
    for footprint, member in enumerate(members):
        source_labels.extend({"footprint": footprint, "member_id": member, "component": component}
                             for component in ("normal", "tangent_2", "tangent_3"))
    kept = joint["old_kept_lumped_rows"]
    all_labels = [{"port_family": "retained_original", **source_labels[int(index)]} for index in kept]
    all_labels.extend({"port_family": "new_continuous_knee", **label} for label in labels)
    require(len(all_labels) == len(force) and len(members) == len(normals), "diagnostic row ownership differs")
    expected = spring_expected(motion, k, uni, pairs, gap_scale*gaps)
    residual = np.where(k > 0, force-expected, 0)
    worst = [{"coupled_port": int(index), "force_n": float(force[index]),
              "expected_original_law_force_n": float(expected[index]), "law_residual_n": float(residual[index]),
              "motion_mm": float(motion[index]), "coefficient_n_per_mm": float(k[index]),
              "label": all_labels[int(index)]}
             for index in np.argsort(abs(residual))[-20:][::-1]]
    nonfloor = (k > 0)
    nonfloor[normals] = False
    floors = [{"footprint": index, "member_id": member, "held": bool(bearing[index]),
               "normal_port": int(normals[index]), "tangent_ports": tangents[index].tolist(),
               "normal_force_n": float(force[normals[index]]), "normal_motion_mm": float(motion[normals[index]]),
               "normal_coefficient_n_per_mm": float(k[normals[index]]),
               "tangent_forces_n": force[tangents[index]].tolist(),
               "tangent_force_norm_n": float(np.linalg.norm(force[tangents[index]])),
               "tangent_motion_mm": motion[tangents[index]].tolist()}
              for index, member in enumerate(members)]
    candidate = bearing & (force[normals] > .01)
    active = (k > 0) & (~uni | (motion > 1e-8))
    active[pairs] = (np.linalg.norm(motion[pairs], axis=1) > gap_scale*gaps+1e-8)[:, None]
    active[normals[bearing & ~candidate]] = False
    active[tangents[candidate]] = True
    _, singular, vh = linalg.svd(D[active], full_matrices=False, check_finite=False)
    rank = int(np.count_nonzero(singular > 1e-10*singular[0]))
    nullspace = vh[rank:].T
    removed = np.flatnonzero(bearing & ~candidate)
    release_force = float(np.max(abs(force[tangents[removed]]), initial=0))
    return {"floor_fields": floors, "worst_original_spring_law_ports": worst,
            "nonfloor_spring_law_residual_n": float(np.max(abs(residual[nonfloor]), initial=0)),
            "held_floor_active_rigid_map": active_rigid_rank(D, motion, joint, bearing, gap_scale),
            "candidate_release_near_zero_normal_footprints": removed.tolist(),
            "candidate_release_fixed_force_max_tangent_n": release_force,
            "candidate_force_fixed_release_blocked_by_nonzero_tangent": release_force > .01,
            "candidate_force_fixed_pose_feasibility_solved": False,
            "candidate_release_active_map": {"rank": rank, "rigid_coordinate_count": D.shape[1],
                "nullity": int(nullspace.shape[1]), "activity_motion_tolerance_mm": 1e-8,
                "relative_rank_threshold": 1e-10,
                "floor_normal_nullspace_projection_norms": np.linalg.norm(D[normals]@nullspace, axis=1).tolist(),
                "scope": "First-order activity diagnostic after removing near-zero-normal footprint rows; not an admissible-pose certificate or stability proof."},
            "physical_branch_accepted": False, "physical_frame_failure_claim": False, "physical_release": False}, {
                "original_law_expected_force_n": expected, "original_law_residual_n": residual,
                "candidate_release_active_rows": active, "candidate_release_nullspace": nullspace}


def shaft_diagnostics(case, force, motion, pose, nold, labels, contract, models, adapter, references):
    """Recover current fields and reuse the frozen same-position stress helper."""
    rows = []
    for shaft, axis in enumerate(AXES):
        geometry, model = contract["geometry"][axis], models[axis]
        shaft_pose = pose[102*shaft:102*(shaft+1)]
        area = math.pi*model["diameter"]**2/4
        tension = 200000*area/model["length"]*(shaft_pose[-1]-shaft_pose[-2])
        beam = []
        for element, location, indices, moment_row, shear_row in model["fields"]:
            beam.append({"element": element, "x_mm": location,
                "EI_curvature_components_nmm": [float(moment_row @ shaft_pose[index]) for index in indices],
                "EI_third_derivative_components_n": [float(shear_row @ shaft_pose[index]) for index in indices]})
        bore_rows = [i for i, label in enumerate(labels) if label["axis_id"] == axis and label["role"] == "distributed_bore"]
        require(len(bore_rows) == 2*len(model["samples"]), "current bore row census differs")
        bore = []
        for sample, pair in zip(model["samples"], np.asarray(bore_rows).reshape(-1,2), strict=True):
            bore.append({"receiver": geometry["receiver_order"][sample["receiver_index"]],
                "x_mm": sample["x_mm"],
                "pressure_mpa": float(np.linalg.norm(force[nold+pair])/(model["diameter"]*sample["weight_mm"]))})
        current = {"case_id": case, "axis_id": axis, "beam_fields": beam, "bore_fields": bore,
                   "outer_seat_fields": [], "normal_transfer": {"single_physical_tie_n": float(tension)}}
        derived = adapter.diagnostics(current, geometry, references)
        seats = []
        for end in (0,1):
            indices = np.asarray([i for i, label in enumerate(labels) if label["axis_id"] == axis
                and label["role"] == "wood_seat" and label["end_index"] == end])
            areas = np.asarray([labels[i]["area_mm2"] for i in indices])
            pressures = force[nold+indices]/areas
            witness = int(np.argmax(pressures))
            mean = float(np.sum(force[nold+indices])/np.sum(areas))
            reference = references["wood_seat_Fc_perpendicular_mean_reference_mpa"]
            seats.append({"end": "head" if end == 0 else "nut", "receiver": labels[int(indices[0])]["member_id"],
                "sample_count": len(indices), "area_mm2": float(areas.sum()), "normal_resultant_n": float(np.sum(force[nold+indices])),
                "peak_pressure_mpa": float(pressures[witness]), "peak_point_mm": labels[int(indices[witness])]["point_mm"],
                "full_annulus_mean_pressure_mpa": mean, "Fc_perpendicular_mean_reference_mpa": reference,
                "peak_over_Fc_perpendicular_diagnostic": float(pressures[witness]/reference),
                "mean_over_Fc_perpendicular_diagnostic": mean/reference,
                "relative_spring_motion_range_mm": [float(motion[nold+indices].min()), float(motion[nold+indices].max())]})
        rows.append({"axis_id": axis, "physical_axial_force_n": float(tension),
            **{key: derived[key] for key in ("peak_same_state_same_position_smooth_proxy", "declared_sensitivity_exceeded",
                "bore_pressure_diagnostics", "stress_scope", "pressure_ratios_are_joint_utilization", "actual_hardware_or_wood_acceptance")},
            "wood_seat_pressure_diagnostics": seats, "physical_acceptance": False})
    return rows


def build(output, preparation, wood_reduction, selected_cases=ALL_CASES, gap_scales=(0., 1.), reuse_response=None,
          diagnostic_floor_mask=None, diagnostic_source=None, continue_after_stop=False, reuse_disposition=None,
          refine_states=()):
    """Parent-serialized actual frame solve from the two completed port packets."""
    import platform

    import clarabel
    import scipy

    output, preparation, wood_reduction = [Path(p).resolve() for p in (output, preparation, wood_reduction)]
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned output child required")
    require(selected_cases and set(selected_cases).issubset(ALL_CASES), "unknown source case")
    require(gap_scales and all(g in (0., 1.) for g in gap_scales), "only declared zero/nominal gaps")
    require(diagnostic_floor_mask is None or (len(selected_cases) == len(gap_scales) == 1
            and not reuse_response and not continue_after_stop and not reuse_disposition and diagnostic_source is not None),
            "fixed-mask diagnostic requires exactly one case/gap, frozen failed source and no replay cache")
    require(not reuse_disposition or continue_after_stop, "reused STOP dispositions require explicit independent-state continuation")
    refine_keys = {STATE_TAGS[tag] for tag in refine_states}
    require(not refine_keys or (reuse_response and diagnostic_floor_mask is None
            and all(case in selected_cases and gap in gap_scales for case,gap in refine_keys)),
            "refinement requires actually accepted source states in the requested inventory")
    pins = {Path(__file__).resolve(): sha(__file__), DIAGNOSTICS: DIAGNOSTICS_SHA256,
            FLOOR_MASK_METHOD: FLOOR_MASK_SHA256}
    prepared = bind_packet(preparation, pins)
    wood_receipt = bind_packet(wood_reduction, pins)
    require(prepared["status"] == "PREPARED_COUPLED_PORTS_NOT_FRAME_RESPONSE", "completed preparation required")
    require(wood_receipt["schema"] == "joint_frame_port_receipt/v1"
            and wood_receipt["status"] == "PASS_JOINT_FRAME_PORT_REDUCTION", "completed wood reduction required")
    request = read(preparation / "wood-port-request.json")
    require(wood_receipt.get("request_sha256") == sha(preparation / "wood-port-request.json"),
            "wood reduction uses a different joint port request")
    require(request["reviewed_bolt_axes"] == 104 and request["proposed_internal_ties_included"] is False,
            "reviewed/proposed connector geometry conflated")
    with np.load(preparation / "joint-operators.npz", allow_pickle=False) as source:
        joint = {name: source[name].copy() for name in source.files}
    with np.load(wood_reduction / "wood-operators.npz", allow_pickle=False) as source:
        H, Dwood, ewood, Wwood = [source[name].copy() for name in ("Hwood", "Dwood", "ewood", "Wwood")]
    nold = len(joint["old_kept_lumped_rows"])
    nnew = len(joint["Bbolt"])
    require(H.shape == (nold+nnew, nold+nnew) and Dwood.shape == (nold+nnew, 300)
            and ewood.shape == (nold+nnew, 12) and Wwood.shape == (300, 12), "wood reduction dimensions differ")
    Bbolt = np.vstack((np.zeros((nold, joint["Bbolt"].shape[1])), joint["Bbolt"]))
    Dwasher = np.vstack((np.zeros((nold, 24)), joint["Dwasher"]))
    H[nold:, nold:] += joint["Bbolt"] @ joint["Cbolt"] @ joint["Bbolt"].T
    D = np.column_stack((Dwood, Bbolt @ joint["Rbolt"], Dwasher))
    require(D.shape[1] == 344, "body/shaft/washer rigid coordinate census changed")
    e, W = ewood, np.vstack((Wwood, np.zeros((44, 12))))
    mass_model = read(OPERATORS / "model.json")
    dead_factor = mass_model["dead_load_factor"]
    require(abs(dead_factor-(1+25/mass_model["modeled_mass_kg"])) < 1e-12,
            "reviewed gravity/accessory factor changed")
    source_response = HERE / "frame-250-attempt02/response.npz"
    pins[source_response] = "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7"
    pins[OPERATORS / "model.json"] = PINS[OPERATORS / "model.json"]
    if PERMANENT in selected_cases:
        pins.update(PERMANENT_PINS)
    authenticate(pins)
    if PERMANENT in selected_cases:
        permanent_source = read(PERMANENT_BASE/"comparison.json")
        require(permanent_source["status"] == "COMPLETED_CONDITIONAL_DEAD_ONLY_COMPARISON"
                and permanent_source["load_columns"] == {"gravity": 0, "live": None}
                and permanent_source["modeled_mass_kg"] == mass_model["modeled_mass_kg"]
                and permanent_source["dead_load_factor"] == dead_factor
                and permanent_source["output_sha256"]["response.npz"] == PERMANENT_PINS[PERMANENT_BASE/"response.npz"],
                "permanent starting floor/force comparison uses different loads or outputs")
        for name in ("operators.npz", "model.json", "row-identities.json"):
            require(permanent_source["source_sha256"][(OPERATORS/name).relative_to(ROOT).as_posix()] == PINS[OPERATORS/name],
                    "permanent starting source uses different frame basis")
    adapter = module(DIAGNOSTICS, "joint_frame_current_field_diagnostics")
    contract, _, reference_receipts, references = adapter.frozen_inputs()
    for record in reference_receipts.values():
        path = ROOT/record["path"]
        require(path not in pins or pins[path] == record["sha256"], "conflicting field reference source")
        pins[path] = record["sha256"]
    core = module(HERE/"knee-compatible.py", "joint_frame_field_core")
    models = {axis: core.assemble(contract["geometry"][axis],
                core.pure_helper(contract["geometry"][axis]["modeled_wood_grip_mm"])) for axis in AXES}
    labels = read(preparation/"port-labels.json")["new_ports"]
    source_rows = read(OPERATORS/"row-identities.json")
    joint["panel_screw_ports"] = panel_screw_ports(source_rows, joint)
    source_branch = None
    if diagnostic_floor_mask is not None:
        diagnostic_source = Path(diagnostic_source).resolve()
        diagnostic_receipt = bind_packet(diagnostic_source, pins, preserved_producer=True)
        require(diagnostic_receipt["status"] == "STOP_COUPLED_FRAME_NUMERICAL_QUALIFICATION_OPEN",
                "fixed-mask diagnostic requires a frozen failed coupled search")
        source_inputs = read(diagnostic_source/"inputs.json")
        require(source_inputs["preparation"] == preparation.relative_to(ROOT).as_posix()
                and source_inputs["wood_reduction"] == wood_reduction.relative_to(ROOT).as_posix()
                and source_inputs["cases"] == list(selected_cases) and source_inputs["gap_scales"] == list(gap_scales),
                "diagnostic does not reproduce the source case/gap/physics")
        source_stop = read(diagnostic_source/"stop.json")
        require(source_stop["exception"].startswith(FLOOR_FAILURE_PREFIX), "diagnostic requires exact finite-search trace")
        source_history = json.loads(source_stop["exception"][len(FLOOR_FAILURE_PREFIX):])
        matches = [entry for entry in source_history if entry["bearing_footprints"] == sorted(diagnostic_floor_mask)]
        require(len(matches) == 1 and "original_physical_law_audit" in matches[0],
                "selected diagnostic mask lacks a solved frozen source branch")
        source_branch = matches[0]
    reused_vectors, reused_states, reused_locations, refinement_sources = {}, {}, {}, {}
    reuse_paths = [] if reuse_response is None else [reuse_response] if isinstance(reuse_response,(str,Path)) else list(reuse_response)
    for reuse_path in reuse_paths:
        reuse_path = Path(reuse_path).resolve()
        reused_receipt = bind_packet(reuse_path, pins, preserved_producer=True)
        require(reused_receipt["schema"] == "joint_frame_compatibility_completion_receipt/v1"
                and reused_receipt["status"] in ("COMPLETE_CONDITIONAL_COUPLED_FRAME_STATES", PARTIAL_STATUS,
                    "STOP_COUPLED_FRAME_NUMERICAL_QUALIFICATION_OPEN"),
                "reuse requires receipt-bound actually completed coupled states")
        partial = reused_receipt["status"] == "STOP_COUPLED_FRAME_NUMERICAL_QUALIFICATION_OPEN"
        reused_inputs = read(reuse_path/"inputs.json")
        reused_comparison = read(reuse_path/("stop.json" if partial else "comparison.json"))
        completed = reused_comparison["completed_states" if partial else "states"]
        require(completed, "stopped packet contains no completed states to reuse")
        require(reused_inputs["preparation"] == preparation.relative_to(ROOT).as_posix()
                and reused_inputs["wood_reduction"] == wood_reduction.relative_to(ROOT).as_posix()
                and reused_inputs["modeled_mass_kg"] == mass_model["modeled_mass_kg"]
                and reused_inputs["dead_load_factor"] == dead_factor
                and reused_inputs["proposal_ties_included"] is False,
                "cached coupled physics/load inputs differ")
        for state in completed:
            key = (state["case_id"], state["gap_scale"])
            require(key not in reused_states and key not in refinement_sources and state["audit"]["all_passed"], "invalid cached state inventory")
            if key in refine_keys:
                refinement_sources[key] = state
            else:
                reused_states[key] = state
            reused_locations[key] = reuse_path
        with np.load(reuse_path/("partial-response.npz" if partial else "response.npz"), allow_pickle=False) as source:
            reused_vectors.update({name: source[name].copy() for name in source.files})
    require(set(refinement_sources) == refine_keys, "a requested refinement lacks an accepted source field")
    stopped_states, disposition_paths = {}, [] if reuse_disposition is None else list(reuse_disposition)
    for disposition_path in disposition_paths:
        disposition_path = Path(disposition_path).resolve()
        stopped_receipt = bind_packet(disposition_path, pins, preserved_producer=True)
        require(stopped_receipt["status"] in ("STOP_COUPLED_FRAME_NUMERICAL_QUALIFICATION_OPEN", PARTIAL_STATUS),
                "reused case disposition requires a frozen exhaustive floor stop")
        isolated = stopped_receipt["status"] == "STOP_COUPLED_FRAME_NUMERICAL_QUALIFICATION_OPEN"
        stopped_inputs = read(disposition_path/"inputs.json")
        stopped_result = read(disposition_path/("stop.json" if isolated else "comparison.json"))
        require(stopped_inputs["preparation"] == preparation.relative_to(ROOT).as_posix()
                and stopped_inputs["wood_reduction"] == wood_reduction.relative_to(ROOT).as_posix()
                and stopped_inputs["modeled_mass_kg"] == mass_model["modeled_mass_kg"]
                and stopped_inputs["dead_load_factor"] == dead_factor
                and stopped_inputs["solver_settings"] == SOLVER_SETTINGS
                and stopped_inputs["elastic_duration_factor"] == 1.0
                and stopped_inputs["proposal_ties_included"] is False, "stopped state physics/inventory differ")
        if isolated:
            require(len(stopped_inputs["cases"]) == len(stopped_inputs["gap_scales"]) == 1
                    and not stopped_result["completed_states"], "isolated stop inventory differs")
            records = [{"case_id": stopped_inputs["cases"][0], "gap_scale": stopped_inputs["gap_scales"][0],
                "stop_evidence": {"packet": disposition_path.relative_to(ROOT).as_posix(),
                    "receipt_sha256": sha(disposition_path/"receipt.json"),
                    "trace_path": (disposition_path/"stop.json").relative_to(ROOT).as_posix(),
                    "trace_sha256": sha(disposition_path/"stop.json"), "pointer": "exception"},
                "floor_search_summary": floor_failure_summary(stopped_result["exception"])}]
        else:
            records = [record for record in stopped_result["case_dispositions"] if not record["accepted_force_field_exists"]]
        for record in records:
            key = (record["case_id"], record["gap_scale"])
            require(key not in stopped_states and key not in reused_states and key not in refine_keys,
                    "conflicting accepted/stopped state inventories")
            evidence = dict(record["stop_evidence"])
            if evidence["receipt_sha256"] is None:
                evidence["receipt_sha256"] = sha(ROOT/evidence["packet"]/"receipt.json")
            trace = ROOT/evidence["trace_path"]
            require(pins.get(trace) == evidence["trace_sha256"]
                    and floor_failure_summary(read(trace)["exception"]) == record["floor_search_summary"],
                    "reused disposition lacks its exact exhaustive trace")
            stopped_states[key] = {"case_id": key[0], "gap_scale": key[1],
                "status": "STOP_NO_AUDITED_POSITIVE_BEARING_FLOOR_BRANCH", "accepted_force_field_exists": False,
                "reused_stopped_packet": disposition_path.relative_to(ROOT).as_posix(),
                "stop_evidence": evidence, "floor_search_summary": record["floor_search_summary"],
                "new_coupled_mechanics_calls": 0, "physical_frame_failure_claim": False, "physical_release": False}
    if refine_keys:
        require({(case,gap) for case in selected_cases for gap in gap_scales}
                <= set(reused_states)|refine_keys|set(stopped_states),
                "bounded refinement cannot trigger any undeclared new state solve")
    authenticate(pins)
    coupon = known_answer()
    output.mkdir(parents=True)
    snapshot = output / "producer.py.snapshot"
    snapshot.write_bytes(Path(__file__).read_bytes())
    write(output / "known-answer.json", coupon)
    if refine_keys:
        write(output/"refinement-known-answer.json", refinement_known_answer())
    output_pins = {p: digest for p, digest in pins.items() if p != Path(__file__).resolve()}
    output_pins[snapshot] = sha(snapshot)
    write(output / "inputs.json", {"source_sha256": {p.relative_to(ROOT).as_posix(): digest for p, digest in output_pins.items()},
        "preparation": preparation.relative_to(ROOT).as_posix(), "wood_reduction": wood_reduction.relative_to(ROOT).as_posix(),
        "cases": list(selected_cases), "gap_scales": list(gap_scales), "modeled_mass_kg": mass_model["modeled_mass_kg"],
        "reused_packet_paths": [Path(p).resolve().relative_to(ROOT).as_posix() for p in reuse_paths],
        "continue_independent_states_after_stop": continue_after_stop,
        "reused_stopped_packet_paths": [Path(p).resolve().relative_to(ROOT).as_posix() for p in disposition_paths],
        "refined_state_tags": list(refine_states), "refinement_solver_settings": REFINEMENT_SETTINGS if refine_keys else None,
        "panel_screw_component_count": 198, "panel_screw_law_residual_gate_n": 1e-4,
        "diagnostic_fixed_floor_mask": diagnostic_floor_mask,
        "diagnostic_source": diagnostic_source.relative_to(ROOT).as_posix() if diagnostic_source is not None else None,
        "permanent_only_load_columns": {"gravity": 0, "live": None}, "elastic_duration_factor": 1.0,
        "dead_load_factor": dead_factor, "unchanged_other_bolt_axes": 100,
        "replaced_continuous_knee_axes": list(AXES), "proposal_ties_included": False,
        "hypotheses": ["source orthotropic filled-body compliance", "first-order geometry", "no-slip bearing footprints",
                       "Kwood=20 MPa/mm", "Khead=10000 MPa/mm", "concentric rigid washer planes",
                       "steel E=200000 MPa", "other 100 bolt axes retain original scalar connector laws",
                       "66 Hillman axes retain original conditional stiffness"],
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                    "clarabel": clarabel.__version__}, "solver_settings": SOLVER_SETTINGS,
        "primary_docs": list(PRIMARY_DOCS)})
    vectors, states, dispositions = {}, [], []
    try:
        rows = read(OPERATORS / "row-identities.json")
        permanent_response = {}
        if PERMANENT in selected_cases:
            with np.load(PERMANENT_BASE/"response.npz", allow_pickle=False) as saved:
                permanent_response = {name: saved[name].copy() for name in saved.files}
        with np.load(source_response, allow_pickle=False) as response:
            for case in selected_cases:
                column = 0 if case == PERMANENT else 2*CASES.index(case)
                load_motion, load_wrench = dead_factor*e[:, column], dead_factor*W[:, column]
                if case != PERMANENT:
                    load_motion, load_wrench = load_motion+e[:, column+1], load_wrench+W[:, column+1]
                for gap_scale in gap_scales:
                    old_tag = case+("_zero" if gap_scale == 0 else "_gap")
                    if (case, gap_scale) in stopped_states:
                        dispositions.append(stopped_states[(case, gap_scale)])
                        print(old_tag, "reused receipt-bound STOP disposition; no accepted field or mechanics replay", flush=True)
                        continue
                    original = permanent_response if case == PERMANENT else response
                    old_force = source_lumped_force(original[old_tag+"_raw_force_n"], rows)[joint["old_kept_lumped_rows"]]
                    initial = old_force[joint["floor_normals"]] > .01
                    started = time.monotonic()
                    reused = (case, gap_scale) in reused_states
                    refined = (case, gap_scale) in refine_keys
                    if diagnostic_floor_mask is not None:
                        bearing = np.isin(np.arange(8), diagnostic_floor_mask)
                        print(old_tag, "starting one frozen fixed-mask diagnostic", diagnostic_floor_mask, flush=True)
                        force, motion, rigid, solver, audit = fixed_floor_branch(
                            H, D, load_motion, load_wrench, joint, bearing, gap_scale)
                        report, fields = floor_diagnostic(force, motion, D, joint, bearing, gap_scale, rows, labels)
                        pose = joint["Rbolt"]@rigid[300:320]-joint["Cbolt"]@Bbolt.T@force
                        fields.update(force_n=force, relative_motion_mm=motion, rigid_scaled_mm=rigid,
                                      shaft_pose_mm=pose, bearing=bearing, rigid_port_map=D,
                                      load_motion_mm=load_motion, load_wrench_scaled=load_wrench)
                        report.update(status="DIAGNOSTIC_REJECTED_FIXED_FLOOR_BRANCH_NOT_ACCEPTED",
                            case_id=case, gap_scale=gap_scale, original_physical_law_audit=audit,
                            solver=solver, elapsed_seconds=time.monotonic()-started,
                            frozen_source_branch=source_branch,
                            recovered_beam_nodal_balance_n=float(np.max(abs(joint["Kbolt"]@pose+Bbolt.T@force))))
                        authenticate(pins)
                        authenticate(output_pins)
                        np.savez_compressed(output/"diagnostic-response.npz", **fields)
                        write(output/"diagnostic.json", report)
                        write(output/"receipt.json", {"schema": "joint_frame_floor_diagnostic_receipt/v1",
                            "status": report["status"],
                            "source_sha256": {p.relative_to(ROOT).as_posix(): digest for p, digest in output_pins.items()},
                            "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
                            "new_coupled_mechanics_calls": 1, "completed_states": 0, "physical_release": False})
                        print(old_tag, "fixed-mask diagnostic saved; zero accepted states", flush=True)
                        return
                    elif reused:
                        force, saved_motion, rigid, bearing = [reused_vectors[old_tag+suffix].copy() for suffix in (
                            "_force_n", "_relative_motion_mm", "_rigid_scaled_mm", "_bearing")]
                        motion = D@rigid+load_motion-H@force
                        require(np.max(abs(saved_motion-motion)) <= 1e-8
                                and np.array_equal(bearing, force[joint["floor_normals"]] > .01),
                                "cached coupled motions or bearing branch differ")
                        audit = force_law_audit(force, motion, rigid, H, D, load_motion, load_wrench,
                            joint["k"], joint["unilateral"], joint["floor_normals"], joint["floor_tangents"],
                            bearing, joint["clearance_pairs"], gap_scale*joint["clearance_gaps"], joint["panel_screw_ports"])
                        require(audit["all_passed"], "cached coupled physical law/equilibrium audit failed")
                        history = reused_states[(case,gap_scale)]["floor_branch_history"]
                        print(old_tag, "reused receipt-bound accepted field without mechanics replay", flush=True)
                    else:
                        print(old_tag, "starting one fixed-mask source refinement" if refined else "starting coupled contact equilibrium", flush=True)
                        try:
                            if refined:
                                bearing = reused_vectors[old_tag+"_bearing"].copy()
                                require(np.array_equal(bearing, reused_vectors[old_tag+"_force_n"][joint["floor_normals"]] > .01),
                                        "refinement source floor mask differs")
                                force, motion, rigid, solver, audit = fixed_floor_branch(
                                    H, D, load_motion, load_wrench, joint, bearing, gap_scale, REFINEMENT_SETTINGS)
                                if not audit["all_passed"]:
                                    raise UnacceptedTrial("STOP: source refinement physical/screw law audit failed: "+json.dumps(audit),
                                                          force,motion,rigid,solver,audit)
                                history = [{"step": 0, "bearing_footprints": np.flatnonzero(bearing).tolist(),
                                    "inactive_floor_normals_omitted_from_force_coordinates": True,
                                    "receipt_bound_source_floor_mask_retained": True, "solver": solver,
                                    "original_physical_law_audit": audit,
                                    "normal_forces_n": force[joint["floor_normals"]].tolist(),
                                    "normal_motion_mm": motion[joint["floor_normals"]].tolist()}]
                            else:
                                force, motion, rigid, bearing, audit, history = solve_coupled(
                                    H, D, load_motion, load_wrench, joint, initial, gap_scale)
                        except ValueError as error:
                            if not continue_after_stop:
                                raise
                            exception = str(error)
                            trace = output/(old_tag+"-stop.json")
                            trial_record = None
                            if refined and isinstance(error,UnacceptedTrial):
                                trial = error.trial
                                trial_path = output/(old_tag+"-unaccepted-trial.npz")
                                np.savez_compressed(trial_path, trial_force_n=trial["force"],
                                    trial_relative_motion_mm=trial["motion"], trial_rigid_scaled_mm=trial["rigid"],
                                    source_bearing=bearing)
                                trial_record = {"path": trial_path.name, "sha256": sha(trial_path),
                                    "solver": trial["solver"], "original_physical_and_screw_law_audit": trial["audit"],
                                    "accepted_force_field_exists": False, "export_to_response_or_actions": False,
                                    "physical_release": False}
                            write(trace, {"case_id": case, "gap_scale": gap_scale, "exception": exception,
                                          "unaccepted_trial": trial_record,
                                          "accepted_force_field_exists": False, "physical_release": False})
                            exhaustive = exception.startswith(FLOOR_FAILURE_PREFIX)
                            dispositions.append({"case_id": case, "gap_scale": gap_scale,
                                "status": "STOP_NO_AUDITED_POSITIVE_BEARING_FLOOR_BRANCH" if exhaustive else "STOP_NUMERICAL_QUALIFICATION_OPEN",
                                "accepted_force_field_exists": False,
                                "stop_evidence": {"packet": output.relative_to(ROOT).as_posix(), "receipt_sha256": None,
                                    "trace_path": trace.relative_to(ROOT).as_posix(), "trace_sha256": sha(trace), "pointer": "exception"},
                                "floor_search_summary": floor_failure_summary(exception) if exhaustive else None,
                                "elapsed_seconds": time.monotonic()-started,
                                "physical_frame_failure_claim": False, "physical_release": False})
                            print(old_tag, "STOP preserved; continuing independent states without a force field", flush=True)
                            continue
                    bolt_pose = joint["Rbolt"] @ rigid[300:320] - joint["Cbolt"] @ Bbolt.T @ force
                    if reused:
                        require(np.max(abs(bolt_pose-reused_vectors[old_tag+"_shaft_pose_mm"])) <= 1e-8,
                                "cached coupled shaft recovery differs")
                    bolt_force = joint["Kbolt"] @ bolt_pose + Bbolt.T @ force
                    require(np.max(abs(bolt_force)) <= .1, "recovered continuous beam nodal equilibrium failed")
                    free_washer_balance = Dwasher.T @ force
                    require(np.max(abs(free_washer_balance.reshape(8,3)[:,0])) <= .1
                            and np.max(abs(free_washer_balance.reshape(8,3)[:,1:]))*1000 <= 2,
                            "recovered washer plane equilibrium failed")
                    tag = case+("_zero" if gap_scale == 0 else "_gap")
                    vectors.update({tag+"_force_n": force, tag+"_relative_motion_mm": motion,
                                    tag+"_rigid_scaled_mm": rigid, tag+"_shaft_pose_mm": bolt_pose,
                                    tag+"_bearing": bearing})
                    states.append({"case_id": case, "gap_scale": gap_scale, "audit": audit,
                                   "load_scope": "gravity_plus_proportional_accessory_only" if case == PERMANENT else "source_live_plus_gravity_and_accessory",
                                   "reused_coupled_response": reused_locations[(case,gap_scale)].relative_to(ROOT).as_posix() if reused else None,
                                   "refined_coupled_response": reused_locations[(case,gap_scale)].relative_to(ROOT).as_posix() if refined else None,
                                   "refinement_force_change_peak_n": float(np.max(abs(force-reused_vectors[tag+"_force_n"]))) if refined else None,
                                   "new_coupled_mechanics_calls": 0 if reused else len(history),
                                   "elapsed_seconds": time.monotonic()-started,
                                   "floor_branch_history": history, "recovered_beam_nodal_balance_n": float(np.max(abs(bolt_force))),
                                   "current_body_translation_peak_mm": float(np.max(np.linalg.norm(rigid[:300].reshape(50,6)[:,:3],axis=1))),
                                   "current_body_rotation_peak_rad": float(np.max(np.linalg.norm(rigid[:300].reshape(50,6)[:,3:],axis=1))/1000),
                                   "original_other_port_force_change_peak_n": float(np.max(abs(force[:nold]-old_force))),
                                   "active_rigid_map": active_rigid_rank(D, motion, joint, bearing, gap_scale),
                                   "compatible_shaft_diagnostics": shaft_diagnostics(case, force, motion, bolt_pose, nold,
                                        labels, contract, models, adapter, references),
                                   "full_frame_joint_feedback_solved_within_declared_hypotheses": True,
                                   "physical_acceptance": False})
                    dispositions.append({"case_id": case, "gap_scale": gap_scale,
                        "status": "PASS_CONDITIONAL_COMPATIBLE_EQUILIBRIUM", "accepted_force_field_exists": True,
                        "response_tag": tag, "physical_release": False})
                    print(tag,"coupled balance/laws complete",json.dumps(audit["metrics"]),flush=True)
    except Exception as error:
        np.savez_compressed(output / "partial-response.npz", **vectors)
        write(output / "stop.json", {"status": "STOP_COUPLED_FRAME_NUMERICAL_QUALIFICATION_OPEN", "exception": str(error),
                                      "completed_states": states, "required_cases": list(selected_cases),
                                      "case_dispositions": dispositions,
                                      "physical_frame_failure_claim": False, "physical_release": False})
        write(output / "receipt.json", {"schema": "joint_frame_compatibility_completion_receipt/v1",
            "status": "STOP_COUPLED_FRAME_NUMERICAL_QUALIFICATION_OPEN",
            "source_sha256": {p.relative_to(ROOT).as_posix(): digest for p, digest in output_pins.items()},
            "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
            "completed_states": len(states), "physical_release": False})
        raise
    authenticate(pins)
    authenticate(output_pins)
    np.savez_compressed(output / "response.npz", **vectors)
    status = PARTIAL_STATUS if any(not item["accepted_force_field_exists"] for item in dispositions) else "COMPLETE_CONDITIONAL_COUPLED_FRAME_STATES"
    write(output / "comparison.json", {"schema": "joint_frame_compatibility_completion/v1",
        "status": status, "states": states, "case_dispositions": dispositions,
        "complete_requested_state_inventory": {(s["case_id"],s["gap_scale"]) for s in dispositions}
            == {(case,gap) for case in selected_cases for gap in gap_scales},
        "complete_six_case_zero_and_nominal_scope": {(s["case_id"],s["gap_scale"]) for s in states if s["case_id"] in CASES}
            == {(case,gap) for case in CASES for gap in (0.,1.)},
        "complete_permanent_zero_and_nominal_scope": {(s["case_id"],s["gap_scale"]) for s in states if s["case_id"] == PERMANENT}
            == {(PERMANENT,gap) for gap in (0.,1.)},
        "diagnostic_references": references,
        "reused_states": sum(state["reused_coupled_response"] is not None for state in states),
        "new_states": sum(state["reused_coupled_response"] is None for state in states),
        "reviewed_geometry_changed": False, "replaced_knee_axes": list(AXES), "physical_release": False,
        "numerical_goal_complete": False})
    write(output / "receipt.json", {"schema": "joint_frame_compatibility_completion_receipt/v1",
        "status": status,
        "source_sha256": {p.relative_to(ROOT).as_posix(): digest for p, digest in output_pins.items()},
        "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
        "completed_states": len(states), "physical_release": False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "coupon", "solve", "diagnose"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--radial-order", type=int, default=4)
    parser.add_argument("--angular-order", type=int, default=16)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--wood-reduction", type=Path)
    parser.add_argument("--reuse-response", type=Path, action="append", help="Receipt-bound completed coupled states; repeat for disjoint caches")
    parser.add_argument("--case", action="append", choices=ALL_CASES)
    parser.add_argument("--gap-scale", action="append", type=float, choices=(0., 1.))
    parser.add_argument("--floor-mask", nargs="+", type=int, choices=range(8),
                        help="One rejected held-footprint mask for diagnose only")
    parser.add_argument("--diagnostic-source", type=Path, help="Receipt-bound failed finite floor search")
    parser.add_argument("--continue-after-stop", action="store_true", help="Preserve per-state STOP and evaluate independent states")
    parser.add_argument("--reuse-disposition", type=Path, action="append", help="Receipt-bound isolated exhaustive STOP; no force field")
    parser.add_argument("--refine-state", action="append", choices=tuple(STATE_TAGS),
                        help="Re-solve exactly this accepted source state once at its saved floor mask and tighter tolerances")
    parser.add_argument("--refinement-coupon", action="store_true", help="Also run stricter circular and near-open unilateral oracles")
    args = parser.parse_args()
    if args.stage == "coupon":
        report = known_answer()
        if args.refinement_coupon:
            report["refinement"] = refinement_known_answer()
        print(json.dumps(report, indent=2), flush=True)
    elif args.stage == "prepare":
        require(args.output is not None, "preparation output required")
        prepare(args.output, args.radial_order, args.angular_order)
    else:
        require(args.output is not None and args.preparation is not None and args.wood_reduction is not None,
                "response output, preparation and wood reduction required")
        require(args.stage == "diagnose" or (args.floor_mask is None and args.diagnostic_source is None),
                "diagnostic options cannot change a production solve")
        require(args.stage != "diagnose" or (args.floor_mask and len(set(args.floor_mask)) == len(args.floor_mask)),
                "diagnose requires a unique explicit held-footprint mask")
        build(args.output, args.preparation, args.wood_reduction, args.case or ALL_CASES,
              args.gap_scale or (0., 1.), args.reuse_response,
              args.floor_mask if args.stage == "diagnose" else None, args.diagnostic_source,
              args.continue_after_stop, args.reuse_disposition, args.refine_state or ())


if __name__ == "__main__":
    main()
