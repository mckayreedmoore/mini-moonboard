"""Compose the current finite source model without transferring acceptance.

Reuse owned saved operators and the reviewed objective component laws. Cached
timber responses may be composed only at their exact source-bound diagnostic
poses; future responses recompute timber admission and contact. No native FEA,
geometry change or physical stiffness/strength qualification is supplied.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from collections import Counter
from dataclasses import fields, is_dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from scipy.linalg import block_diag
from scipy.sparse import csr_matrix, issparse
from scipy.spatial.transform import Rotation

from scripts import eoere_current_finite_preflight as preflight
from scripts import eoere_current_timber_bedding as timber
from scripts import eoere_finite_fitting_precision as precision
from scripts import thin_bolted_common_shaft as common
from scripts import thin_bolted_finite_frame as finite

current, component = timber.current, timber.inverse.component
mechanical, isotropic, panel_method = finite.mechanical, finite.isotropic, finite.panels_method
canonical_sha = timber.canonical_sha
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
TIMBER_PRODUCER = {"path": "scripts/eoere_current_timber_bedding.py",
    "sha256": "658a8c6e1e0845b3fb0683d9a35b1a6f2ff480d238bcb4a0b56083949896f41c"}
PRECISION_PRODUCER = {"path": "scripts/eoere_finite_fitting_precision.py",
    "sha256": "f534bbcf72786fecf52b38e8896def8992d5202cc5b9c5abc5e6e30b840cf772"}
PREFLIGHT_PRODUCER = {"path": "scripts/eoere_current_finite_preflight.py",
    "sha256": "dbf28ba07c4c953f0976a795968406a961b58cb2a1c7320e98b8100eeebaab62"}
FINITE_PRODUCER = {"path": "scripts/thin_bolted_finite_frame.py",
    "sha256": "68f711549da9e6b52c60db4e4df78235ba8105084ded0d81c9a3430cf5973588"}
COMMON_PRODUCER = {"path": "scripts/thin_bolted_common_shaft.py",
    "sha256": "0ff8c52a36f168cba0bd3fed2d592daa9e5d9de5facbc650b151f64c2f23f4eb"}
# Numerical headroom for heel-force residuals transported to world moments.
# The original 1e-8-N heel and 1e-5-N/Nmm owner-work gates remain enforced.
HEEL_NUMERICAL_TARGET_N = 1e-9
INTERACTION_COUNTS = {"common_shaft_bearing": 416, "panel_screw": 66,
    "flange_contact": 352, "panel_contact": 922, "shaft_end_capture": 200,
    "floor_normal": 32, "floor_tangent_xy": 2}
TIMBER_EVIDENCE = {"path": timber.scope.RAW+"current-timber-bedding-v2.json",
    "sha256": "684b510d9b4ba110aee187a7e1fd6f83f14277b58dea36b17cf8cf3c4bd3174e"}


def own_ref():
    current.require(current.sha(OWN) == LOADED_SHA, "loaded current finite-frame producer changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def indices(value, shape, ndof, *, omitted=False):
    raw = np.asarray(value)
    result = np.asarray(value, dtype=int)
    current.require(raw.shape == result.shape == shape and np.array_equal(raw, result)
        and np.all(result >= (-1 if omitted else 0)) and np.all(result < ndof)
        and len(set(result[result >= 0].tolist())) == np.count_nonzero(result >= 0),
        "unique exact owned coordinate indices required")
    return result


def assembled_block(index, blocks):
    lookup = {int(v): i for i, v in enumerate(index)}
    result = np.zeros((len(index), len(index)))
    for dofs, block in blocks:
        local = [lookup[int(v)] for v in dofs]
        result[np.ix_(local, local)] += block
    return result


def check_reference_block(reference, index, expected, body):
    observed = reference[index][:, index].toarray()
    error = float(np.linalg.norm(observed-expected)/max(1., np.linalg.norm(expected)))
    current.require(np.isfinite(error) and error <= 1e-11,
                    "owned elastic block differs from saved reference operator: "+body)
    return {"body": body, "relative_reference_block_error": error}


def restore_mechanics(chart, scenario, shaft_sources, reference_K, *, source_sha256):
    """Restore existing beam matrices from their own recorded member properties.

    This does not rebuild geometry or a first-order frame. Each reconstructed
    timber/shaft block must equal its own saved elastic operator block before
    being passed to the frozen objective adapters.
    """
    ndof = chart["final_ndof"]
    reference_K = csr_matrix(reference_K)
    current.require(reference_K.shape == (ndof, ndof) and np.isfinite(reference_K.data).all()
        and chart["rotation_scale"] == 1000., "finite own reference matrix and rotation scale required")
    assembly = SimpleNamespace(ndof=ndof, members={}, fittings={})
    errors, owned = [], set()
    e, ratio = scenario["timber_e_mpa"], scenario["timber_shear_ratio"]
    current.require(np.isfinite([e, ratio]).all() and min(e, ratio) > 0., "positive finite recorded timber properties required")
    for body, saved in chart["timber"].items():
        source = copy.deepcopy(saved["source"])
        stations = np.asarray(saved["stations"], dtype=float)
        start, axis = mechanical.vector(saved["start"], 3), mechanical.vector(saved["axis"], 3)
        basis = mechanical.check_rotation(np.asarray([source[k] for k in ["axis", "section_u", "section_v"]]).T)
        current.require(stations.ndim == 1 and len(stations) >= 2 and np.isfinite(stations).all()
            and stations[0] == 0. and np.all(np.diff(stations) > 0.) and source["name"] == body
            and np.array_equal(start, source["start"]) and np.array_equal(axis, source["axis"])
            and np.linalg.norm(start+stations[-1]*axis-source["end"]) < 1e-7,
            "own timber chart and strictly ordered reference stations required")
        index = indices(saved["index"], (len(stations), 6), ndof)
        current.require(not (owned & set(index.ravel())), "beam coordinate owners overlap")
        owned.update(index.ravel())
        width, depth = source["width_mm"], source["depth_mm"]
        current.require(np.isfinite([width, depth]).all() and min(width, depth) > 0., "positive finite source timber section required")
        transform = block_diag(basis.T, basis.T/1000., basis.T, basis.T/1000.)
        elements, blocks = [], []
        for i, length in enumerate(np.diff(stations)):
            local = finite.frame.beam_stiffness(length, width*depth, width*depth**3/12., depth*width**3/12.,
                finite.frame.rectangular_torsion(width, depth), e, e*ratio)
            dofs = index[i:i+2].ravel()
            block = transform.T @ local @ transform
            elements.append({"dofs": dofs, "local_K": local, "K": block, "T": transform,
                "start": start+stations[i]*axis, "end": start+stations[i+1]*axis})
            blocks.append((dofs, block))
        errors.append(check_reference_block(reference_K, index.ravel(), assembled_block(index.ravel(), blocks), body))
        assembly.members[body] = {"index": index, "stations": stations, "start": start,
            "axis": axis, "source": source, "elements": elements}
    parameters = scenario["common_shaft_parameters"]
    steel, nu = parameters["steel_E_mpa"], parameters["steel_nu"]
    current.require(np.isfinite([steel, nu]).all() and steel > 0. and -.9 < nu < .5,
                    "positive finite recorded shaft material required")
    shafts = {}
    current.require(len(shaft_sources) == len(chart["shafts"])
        and {s["body"] for s in shaft_sources} == set(chart["shafts"]), "complete source-ordered shaft ownership required")
    for source in shaft_sources:
        body = source["body"]
        saved = chart["shafts"][body]
        current.require(all(saved[k] == source[k] for k in ["axis_id", "basis", "point", "diameter_mm", "surfaces", "ends"]),
                        "own shaft source and chart differ")
        stations = np.asarray(saved["stations"], dtype=float)
        local_K, _local_index, elements = common.reduced_shaft_matrix(stations, saved["diameter_mm"], steel, steel/(2.*(1.+nu)))
        index = indices(saved["index"], (len(stations), 6), ndof, omitted=True)
        current.require(np.count_nonzero(index < 0) == 1 and index[0, 3] == -1
            and not (owned & set(index[index >= 0])), "one first-spin gauge and disjoint shaft coordinates required")
        owned.update(index[index >= 0])
        errors.append(check_reference_block(reference_K, index[index >= 0], local_K.toarray(), body))
        shafts[body] = {**copy.deepcopy(saved), "index": index, "stations": stations,
            "basis": np.asarray(saved["basis"], dtype=float), "point": mechanical.vector(saved["point"], 3), "elements": elements}
    system = SimpleNamespace(shafts=shafts, parameters={"shaft_steel_E_mpa": steel, "shaft_steel_nu": nu,
        "shaft_diameter_scale": 1., "circular_shear_factor_scenario": .9})
    base = mechanical.FiniteMechanicsAdapter(assembly, system, source_sha256=source_sha256)
    replacement = isotropic.IsotropicShaftAdapter(base, system, source_sha256=source_sha256)
    return assembly, base, replacement, errors


def four_port_router(base, fittings, method, fitting_method, source_sha256):
    """Extend only the frozen router's constructor to reviewed stable subclasses."""
    class StableRouter(method.FourPortPointRouter):
        def __init__(self):
            current.require(type(base) is mechanical.FiniteMechanicsAdapter and base.fittings == {},
                            "genuine mechanics with no legacy fitting law required")
            current.require(fittings and all(isinstance(f, fitting_method.objective.ObjectiveFourPort)
                and f.body == body and type(f).__module__ == precision.__name__ for body, f in fittings.items()),
                "genuine owned precision four-port adapters required")
            current.require(not (set(fittings) & (set(base.members) | set(base.shafts)))
                and all(max(f.element.indices) < base.ndof for f in fittings.values()), "disjoint full-chart fitting owners required")
            for fitting in fittings.values(): fitting._check()
            self.base, self.four_port_fittings, self.ndof = base, dict(fittings), base.ndof
            self.members, self.shafts, self.fittings, self.beams = base.members, base.shafts, {}, base.beams
            self.source_sha256 = current.join(source_sha256, base.source_sha256, method.source_pins(), fitting_method.source_pins(),
                *(f.precision_pins for f in fittings.values()))
            current.verify(self.source_sha256)
    return StableRouter()


def current_panel_load_class(data, integrated, proof, panels, case_loads, source_sha256):
    """Reuse the frozen load constructor with an authenticated current input gate.

    Only its historical integrated-JSON identity check is replaced. The current
    own projection, cases, loads and prepared adapters must match exactly; all
    load, reference-port and generalized-correction calculations remain intact.
    No shared module globals or historical source files are changed.
    """
    current.verify_panel_source_inputs(data, proof)
    current.require(canonical_sha(integrated) == proof["current_own_projection_canonical_sha256"]
        and set(panels) == set(panel_method.method.PANELS) and set(case_loads) == set(component.SEQUENCE),
        "complete own current panel projection, adapters and six load cases required")
    integrated, case_loads = copy.deepcopy(integrated), copy.deepcopy(case_loads)
    expected_cases = {row["id"]: row for row in panel_method.method.load_cases(integrated)
                      if row["id"] in case_loads}
    current.require(set(expected_cases) == set(case_loads), "each current panel case needs its own load projection")
    pins = current.join(source_sha256, proof["source_sha256"], {own_ref()["path"]: own_ref()["sha256"]})
    descriptor = canonical_sha([integrated, case_loads, proof])
    source = Path(panel_method.__file__).resolve()
    relative = str(source.relative_to(current.ROOT))
    current.require(pins.get(relative) == current.sha(source), "exact pinned frozen panel constructor required")
    tree = ast.parse(source.read_text())
    original_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "FinitePanelLoads")
    constructor = copy.deepcopy(next(n for n in original_class.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"))
    old_gate = ast.parse('method.require(integrated == json.loads(method.INTEGRATED.read_text()), "integrated panel load source differs")').body[0]
    matches = [i for i, node in enumerate(constructor.body)
               if ast.dump(node, include_attributes=False) == ast.dump(old_gate, include_attributes=False)]
    current.require(len(matches) == 1, "exact single historical panel input gate required")
    constructor.body[matches[0]] = ast.parse("_verify_current_load_projection(adapter, case, integrated, accessory, body_loads)").body[0]

    def verify_projection(adapter, case, supplied, accessory, body_loads):
        current.verify(pins)
        current.require(canonical_sha([integrated, case_loads, proof]) == descriptor
            and type(adapter) is panel_method.FinitePanelAdapter
            and panels.get(adapter.geometry["name"]) is adapter
            and supplied == integrated and case == expected_cases.get(case["id"])
            and accessory == "original_top" and body_loads == case_loads.get(case["id"]),
            "exact own current projection, case, original-top loads and panel adapter required")

    namespace = {**vars(panel_method), "_verify_current_load_projection": verify_projection}
    module = ast.fix_missing_locations(ast.Module(body=[constructor], type_ignores=[]))
    # Only the authenticated local constructor AST is compiled; no supplied code.
    exec(compile(module, str(source)+":current-input-gate", "exec"), namespace)  # noqa: S102
    return type("CurrentFinitePanelLoads", (panel_method.FinitePanelLoads,),
                {"__module__": __name__, "__init__": namespace["__init__"]})


def transported_seed(fitting, q24, reference_q24, reference_heel):
    """Transport an explicit own seed by the first port's relative rigid motion.

    Other port deformation is left for fresh local stationarity. The seed is
    deterministic for each trial, never treated as an accepted heel response.
    """
    q = mechanical.vector(q24, 24).reshape(4, 6)
    before = mechanical.vector(reference_q24, 24).reshape(4, 6)
    heel = mechanical.vector(reference_heel, 6)
    if np.array_equal(q[0], before[0]):
        return heel.copy()
    point = np.asarray(fitting.model.port_manifest[0]["point_reference_xyz_mm"])
    relative = Rotation.from_rotvec(q[0, 3:]/1000.).as_matrix() @ Rotation.from_rotvec(before[0, 3:]/1000.).as_matrix().T
    position = point+q[0, :3]+relative @ (np.asarray(fitting.model.origin)+heel[:3]-point-before[0, :3])
    rotation = relative @ Rotation.from_rotvec(heel[3:]/1000.).as_matrix()
    return np.r_[position-fitting.model.origin, 1000.*Rotation.from_matrix(rotation).as_rotvec()]


def prepare_panel_embedding(panel):
    """Derive an orthogonal finite normal from the unchanged source midsurface.

    The recorded normal is independently rounded. Keep source geometry and
    its initial RHS intact; only the finite embedding uses the oriented cross
    product of the two already orthonormal source plane axes. Either handedness
    is valid. This changes neither local XY, quadrature nor the elastic block.
    """
    current.require(type(panel) is panel_method.FinitePanelAdapter
        and not hasattr(panel, "finite_embedding_precision"), "one genuine fresh panel embedding required")
    raw = np.asarray(panel.geometry["axes"], dtype=float)
    current.require(np.array_equal(panel.axes, raw) and raw.shape == (3, 3)
        and np.isfinite(raw).all() and np.max(abs(raw.T@raw-np.eye(3))) < 1e-8,
        "own recorded panel embedding required")
    plane = raw[:, :2]
    current.require(np.max(abs(plane.T@plane-np.eye(2))) < 1e-13,
        "source midsurface axes require a separate geometry treatment")
    normal = np.cross(plane[:, 0], plane[:, 1])
    normal /= np.linalg.norm(normal)
    if normal@raw[:, 2] < 0.: normal = -normal
    runtime = np.column_stack([plane, normal])
    current.require(np.max(abs(runtime.T@runtime-np.eye(3))) < 1e-13,
                    "derived finite panel embedding must be orthogonal")
    delta = float(np.linalg.norm(normal-raw[:, 2]))
    offset = .5*panel.panel["thickness"]*delta
    current.require(offset < 1e-7, "derived normal exceeds the recorded reference-face datum precision")
    record = {"recorded_axes_columns_xyz": raw.tolist(), "runtime_axes_columns_xyz": runtime.tolist(),
        "source_midsurface_and_local_xy_unchanged": True, "source_geometry_and_initial_RHS_retained": True,
        "handedness": int(np.sign(np.linalg.det(runtime))), "normal_difference_norm": delta,
        "reference_half_thickness_offset_change_bound_mm": offset,
        "finite_transverse_coefficient_embedding_change": "normal_difference_norm times the local transverse field; source q remains diagnostic"}
    panel.axes = runtime
    panel.finite_embedding_precision = copy.deepcopy(record)
    return record


def condensed_fitting_response(fitting, q24, *, seed, loads, tangent, translation_origin_mm=(0., 0., 0.)):
    """Seek smaller heel residuals without changing the original force gate.

    The reviewed refiner retains its three improving corrections and shared
    hard callback budget. Failure to reach this numerical target is recorded;
    original local stationarity, positive heel and complete owner work still
    decide whether the response is usable. No failed original gate is caught.
    """
    origin = mechanical.vector(translation_origin_mm, 3).copy()
    local_q, local_seed = q24, seed
    if np.any(origin):
        local_q = mechanical.vector(q24, 24).copy()
        local_q.reshape(4, 6)[:, :3] -= origin
        local_seed = mechanical.vector(seed, 6).copy()
        local_seed[:3] -= origin
    original = precision.residual_refined_root

    def refined(root, fun, start, *, options, tolerance_n, step_mm):
        current.require(tolerance_n == 1e-8, "original local heel acceptance gate required")
        return original(root, fun, start, options=options,
            tolerance_n=HEEL_NUMERICAL_TARGET_N, step_mm=step_mm)

    # Parent-owned serialized root execution; restore this seam on all exits.
    with patch.object(precision, "residual_refined_root", refined):
        result = fitting.condensed_response(local_q, heel_seed=local_seed, loads=loads, tangent=tangent,
            recover_actions=True, heel_tolerance_n=1e-8, max_local_evaluations=100)
    current.require(precision.residual_refined_root is original, "restored local refiner required")
    # A fixed common translation has identity coordinate Jacobian and leaves
    # internal energy, rotations, forces, couples and tangent unchanged.
    # Restore physical points and the exact dead-force work offset explicitly.
    result["numerical_translation_origin_xyz_mm"] = origin.tolist()
    result["numerical_internal_heel_q_mm_1000rad"] = copy.deepcopy(result["internal_heel_q_mm_1000rad"])
    result["residual_refinement"]["heel_translation_coordinates_relative_to_xyz_mm"] = origin.tolist()
    if np.any(origin):
        result["internal_heel_q_mm_1000rad"] = (np.asarray(result["internal_heel_q_mm_1000rad"])+np.r_[origin, np.zeros(3)]).tolist()
        result["current_heel_point_xyz_mm"] = (np.asarray(result["current_heel_point_xyz_mm"])+origin).tolist()
        for rows in [result["port_actions"], result["strip_root_actions"], result["current_load_actions"]]:
            for row in rows: row["point_xyz_mm"] = (np.asarray(row["point_xyz_mm"])+origin).tolist()
        offset = sum(mechanical.vector(load["force_xyz_n"], 3)@origin for load in loads)
        result["dead_load_work_from_reference_nmm"] += offset
        result["energy_nmm"] -= offset
    return result


class LoadedFittings:
    """Own four-strip energy and own heel gravity, each exactly once."""
    def __init__(self, fittings, field, source_sha256, *, numerical_translation_origins=None):
        self.fittings, self.ndof, self.source_sha256 = dict(fittings), 9450, dict(source_sha256)
        current.require(numerical_translation_origins is None or set(numerical_translation_origins) == set(fittings),
                        "one fixed numerical translation origin per fitting required")
        actions = {a["body"]: a for a in field["four_port_fitting_actions"]}
        self.references = {}
        for body, fitting in fittings.items():
            loads = [copy.deepcopy(r) for r in field["body_applied_loads"] if r["body"] == body]
            current.require(len(loads) == 1 and actions[body]["body"] == body, "one own fitting gravity source and heel seed required")
            seed = mechanical.vector(actions[body]["loaded_heel_q_mm_rad"], 6).copy()
            seed[3:] *= 1000.
            q24 = np.asarray(field["response"]["q"])[fitting.element.indices]
            origin = q24[:3] if numerical_translation_origins is None else numerical_translation_origins[body]
            self.references[body] = {"q24": q24.tolist(), "heel": seed.tolist(), "loads": loads,
                "numerical_translation_origin_xyz_mm": mechanical.vector(origin, 3).tolist()}
        self.reference_sha = canonical_sha([self.references, self.registry_descriptor()])

    def registry_descriptor(self):
        return {body: {"type": [type(f).__module__, type(f).__qualname__],
            "element": f.element.descriptor(), "relative_operator": f._relative_fingerprint(),
            "source_sha256": f.precision_pins} for body, f in self.fittings.items()}

    def response(self, q, *, tangent):
        current.verify(self.source_sha256)
        current.require(canonical_sha([self.references, self.registry_descriptor()]) == self.reference_sha,
                        "fixed own fitting references or adapter registry changed")
        q = mechanical.vector(q, self.ndof)
        energy, gradient = 0., np.zeros(self.ndof)
        hessian = csr_matrix((self.ndof, self.ndof)) if tangent else None
        rows = []
        for body, fitting in self.fittings.items():
            reference, index = self.references[body], fitting.element.indices
            seed = transported_seed(fitting, q[index], reference["q24"], reference["heel"])
            result = condensed_fitting_response(fitting, q[index], seed=seed, loads=reference["loads"], tangent=tangent,
                translation_origin_mm=reference["numerical_translation_origin_xyz_mm"])
            current.require(np.isfinite([result["heel_residual_inf_n"], result["heel_hessian_min_symmetric_eigenvalue_n_mm"]]).all()
                and 0. <= result["heel_residual_inf_n"] <= 1e-8 and result["heel_hessian_min_symmetric_eigenvalue_n_mm"] > 1e-8,
                "same current fitting stationarity and positive-heel gates required")
            work = precision.fitting_work_check(fitting, q[index], result, reference["loads"])
            energy += result["energy_nmm"]
            np.add.at(gradient, index, result["gradient_n"])
            if tangent: hessian += mechanical.sparse_local(result["hessian_n_per_mm"], index, self.ndof)
            rows.append({"body": body, "seed_mm_1000rad": seed.tolist(),
                "local_numerical_accuracy_target_n": HEEL_NUMERICAL_TARGET_N,
                "local_numerical_target_met": bool(result["heel_residual_inf_n"] <= HEEL_NUMERICAL_TARGET_N),
                "heel_acceptance_gate_n": 1e-8, **work, **result})
        current.require(np.isfinite(energy) and np.isfinite(gradient).all()
            and (not tangent or np.isfinite(hessian.data).all()), "complete finite fitting response required")
        current.verify(self.source_sha256)
        return {"energy_nmm": energy, "gradient_n": gradient, "hessian_csr": hessian, "fittings": rows}


def nodal_rigid_modes(centers, index, basis, q):
    """Exact stored-coordinate variations under a world rigid motion about zero."""
    centers, basis, index = np.asarray(centers), mechanical.check_rotation(basis), np.asarray(index)
    modes = np.zeros((index.size, 6))
    for i, (center, dofs) in enumerate(zip(centers, index, strict=True)):
        state = q[dofs]
        position = center+basis @ state[:3]
        theta = state[3:]/1000.
        modes[6*i:6*i+3, :3] = basis.T
        modes[6*i:6*i+3, 3:] = -basis.T @ mechanical.skew(position)
        modes[6*i+3:6*i+6, 3:] = 1000.*mechanical.so3_left_jacobian_inverse(theta) @ basis.T
    return index.ravel(), modes


def owner_work_wrenches(router, panels, q, gradient):
    """Project the signed residual independently onto every current owner."""
    result = {}
    for body, row in router.members.items():
        centers = row["start"]+row["stations"][:, None]*row["axis"]
        index, modes = nodal_rigid_modes(centers, row["index"], np.eye(3), q)
        result[body] = -modes.T @ gradient[index]
    for body, row in router.shafts.items():
        centers = row["point"]+row["stations"][:, None]*row["basis"][0]
        index, modes = nodal_rigid_modes(centers, row["index"], row["storage_basis"], q)
        result[body] = -modes.T @ gradient[index]
    for body, fitting in router.four_port_fittings.items():
        centers = [r["point_reference_xyz_mm"] for r in fitting.model.port_manifest]
        index, modes = nodal_rigid_modes(centers, fitting.element.indices.reshape(4, 6), np.eye(3), q)
        result[body] = -modes.T @ gradient[index]
    for body, panel in panels.items():
        result[body] = -panel.current_rigid_modes(q, np.zeros(3)).T @ gradient[panel.indices]
    return result


def physical_owner_wrenches(owners, generic, bedding, fittings):
    """Sum current physical actions and explicitly separate panel corrections."""
    result = {body: np.zeros(6) for body in owners}

    def add(body, point, force, couple):
        if body == "floor": return
        current.require(body in result, "physical action has an unowned body: "+body)
        force, point, couple = (mechanical.vector(v, 3) for v in [force, point, couple])
        result[body] += np.r_[force, couple+np.cross(point, force)]

    for action in generic["finite_interaction_actions"]:
        for side in ["first", "second"]:
            add(action[side], action["point_on_"+side+"_xyz_mm"], action["force_on_"+side+"_xyz_n"],
                action["moment_on_"+side+"_at_current_point_xyz_nmm"])
    for load in generic["finite_body_applied_loads"]:
        add(load["body"], load["current_point_xyz_mm"], load["force_xyz_n"], load["free_spatial_moment_xyz_nmm"])
    for fitting in fittings["fittings"]:
        for load in fitting["current_load_actions"]:
            add(load["body"], load["point_xyz_mm"], load["force_xyz_n"], load["free_couple_xyz_nmm"])
    for body, wrench in bedding["owner_wrenches_at_world_origin"].items():
        current.require(body in result, "timber wrench has an unowned body")
        result[body] += mechanical.vector(wrench, 6)
    corrections = {body: np.zeros(6) for body in owners}
    for row in generic["panel_generalized_load_corrections"]:
        current.require(row["physical_point_forces_or_pressure_representation"] is False,
                        "panel RHS corrections must remain explicitly generalized")
        wrench = mechanical.vector(row["current_equivalent_rigid_wrench_n_nmm"], 6).copy()
        wrench[3:] += np.cross(row["wrench_reference_xyz_mm"], wrench[:3])
        corrections[row["panel"]] += wrench
    return result, corrections


def compose_responses(generic, bedding, fittings, *, tangent):
    """Sum three disjoint potentials; there is no retained first-order RHS."""
    energy = sum(r["energy_nmm"] for r in [generic, bedding, fittings])
    gradients = [np.asarray(r["gradient_n"]) for r in [generic, bedding, fittings]]
    current.require(gradients[0].ndim == 1 and all(g.shape == gradients[0].shape for g in gradients),
                    "all composed gradients must use the same whole chart")
    gradient = sum(gradients)
    if tangent:
        current.require(all(r["hessian_csr"] is not None and r["hessian_csr"].shape == (len(gradient), len(gradient))
            for r in [generic, bedding, fittings]), "all composed tangents must use the same whole chart")
    hessian = sum(r["hessian_csr"] for r in [generic, bedding, fittings]) if tangent else None
    current.require(np.isfinite(energy) and np.isfinite(gradient).all()
        and (not tangent or np.isfinite(hessian.data).all()), "complete finite composed response required")
    components = {**generic["component_potential_energies_nmm"],
        "reference_material_timber_bedding": bedding["energy_nmm"], "loaded_four_port_fittings": fittings["energy_nmm"]}
    current.require(abs(sum(components.values())-energy) <= 1e-10*max(1., abs(energy)), "component potential sum differs")
    return energy, gradient, hessian, components


def numerical_descriptor(value):
    """Fingerprint mutable numerical inputs without copying large array values."""
    if isinstance(value, np.ndarray):
        return {"array_shape": list(value.shape), "dtype": value.dtype.str,
                "bytes_sha256": hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()}
    if isinstance(value, np.generic): return value.item()
    if issparse(value):
        matrix = value.tocsr()
        return {"csr_shape": list(matrix.shape), **{key: numerical_descriptor(getattr(matrix, key))
                for key in ["data", "indices", "indptr"]}}
    if isinstance(value, panel_method.method.SheetBasis):
        return {"sheet_basis": numerical_descriptor({key: item for key, item in vars(value).items() if key != "spline"}),
                "spline": numerical_descriptor({key: getattr(value.spline, key) for key in ["t", "c", "k", "axis", "extrapolate"]})}
    if is_dataclass(value):
        return {"dataclass": [type(value).__module__, type(value).__qualname__],
                "fields": {field.name: numerical_descriptor(getattr(value, field.name)) for field in fields(value)}}
    if isinstance(value, dict): return {key: numerical_descriptor(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)): return [numerical_descriptor(item) for item in value]
    current.require(value is None or isinstance(value, (str, bool, int, float)), "undeclared prepared numerical input type")
    return value


def prepared_operator_descriptor(generic):
    """Seal the actual operands consumed by frozen finite adapters and loads."""
    router, replacement = generic.mechanics, generic.shaft_replacement
    base = router.base
    screws = [(body, row) for body, panel in generic.panels.items() for row in panel.panel.get("screws", [])]
    current.require(len(screws) == len(generic.screw_by_id)
        and {row["axis_id"] for _, row in screws} == generic.screw_by_id.keys()
        and all(row["panel"] == body and generic.screw_by_id[row["axis_id"]] is row for body, row in screws),
        "fixed current frame sources changed: own projected-ring screw routing differs")
    current.require(replacement.mechanics is base and not base.fittings and not router.fittings
        and all(getattr(router, key) is getattr(base, key) for key in ["members", "shafts", "beams"])
        and all(load.adapter is generic.panels[body] for body, load in generic.panel_loads.items()),
        "fixed current frame sources changed: legacy laws or prepared adapter ownership differ")
    return numerical_descriptor({"generic": {key: getattr(generic, key) for key in
        ["ndof", "case", "map", "source_sha256", "screw_by_id"]},
        "base": {key: getattr(base, key) for key in
        ["old_ndof", "ndof", "step", "members", "shafts", "beams", "fittings", "source_sha256"]},
        "replacement": {key: getattr(replacement, key) for key in
            ["ndof", "parameters", "elements", "timber_elements", "source_sha256"]},
        "panels": {body: vars(panel) for body, panel in generic.panels.items()},
        "panel_loads": {body: {key: value for key, value in vars(load).items() if key != "adapter"}
                        for body, load in generic.panel_loads.items()}})


class CurrentFrame:
    """Current complete numerical source model; acceptance stays separate."""
    def __init__(self, generic, bedding, fittings, binding, q, *, source_sha256, cached_timber=None):
        self.generic, self.bedding, self.fittings = generic, bedding, fittings
        self.ndof, self.binding = generic.ndof, copy.deepcopy(binding)
        self.q = mechanical.vector(q, self.ndof).copy()
        self.q.setflags(write=False)
        self.source_sha256 = dict(source_sha256)
        current.require(self.ndof == bedding.ndof == fittings.ndof
            and set(generic.mechanics.members) == set(bedding.maps)
            and generic.mechanics.four_port_fittings.keys() == fittings.fittings.keys()
            and all(fittings.fittings[body] is fitting for body, fitting in generic.mechanics.four_port_fittings.items()),
            "complete shared timber, own fitting registry and whole-frame chart required")
        self.map = copy.deepcopy(generic.map)
        self.map["four_port_fittings"] = generic.mechanics.explicit_four_port_map()
        self.map["schema"] = "eoere_current_complete_finite_kinematic_map/v1"
        self.cached_timber = copy.deepcopy(cached_timber)
        self.cached_sha = canonical_sha(self.cached_timber) if cached_timber is not None else None
        self.descriptor_sha = self._descriptor_sha()

    def _descriptor_sha(self):
        return canonical_sha([self.binding, self.q.tolist(), self.generic.interactions,
            self.generic.nonpanel_loads, self.generic.case, self.fittings.references,
            self.fittings.registry_descriptor(), self.generic.mechanics.explicit_four_port_map(),
            self.bedding._descriptor_sha(), prepared_operator_descriptor(self.generic), self.map, self.source_sha256])

    def _check(self):
        current.verify(self.source_sha256)
        current.require(self._descriptor_sha() == self.descriptor_sha, "fixed current frame sources changed")

    def diagnostic_response(self):
        self._check()
        current.require(self.cached_timber is not None and canonical_sha(self.cached_timber) == self.cached_sha,
                        "unchanged authenticated complete diagnostic timber response required")
        value = copy.deepcopy(self.cached_timber)
        current.require(value["final_q_canonical_sha256"] == canonical_sha(self.q.tolist())
            and value["fixed_sample_descriptor_sha256"] == self.bedding.descriptor_sha,
            "cached timber force belongs to a different own pose or fixed measure")
        value["gradient_n"] = np.asarray(value["gradient_n"])
        value["hessian_csr"] = None
        return self._response(self.q, value, tangent=False, cached=True)

    def response(self, q, *, tangent=True):
        self._check()
        q = mechanical.vector(q, self.ndof).copy()
        return self._response(q, self.bedding.response(q, tangent=tangent), tangent=tangent, cached=False)

    def _response(self, q, bedding, *, tangent, cached):
        self._check()
        generic = self.generic.response(q, tangent, recover_actions=True)
        fittings = self.fittings.response(q, tangent=tangent)
        energy, gradient, hessian, components = compose_responses(generic, bedding, fittings, tangent=tangent)
        work = owner_work_wrenches(self.generic.mechanics, self.generic.panels, q, gradient)
        physical, corrections = physical_owner_wrenches(work, generic, bedding, fittings)
        residuals = {body: work[body]-physical[body]-corrections[body] for body in work}
        error = max(float(np.max(abs(value))) for value in residuals.values())
        current.require(error < 1e-5, "same-state complete owner force/moment virtual-work closure failed")
        floor_rows = [r for r in generic["finite_interaction_actions"] if r["kind"] == "floor_normal"]
        normal_by_host = {}
        for row in floor_rows: normal_by_host[row["first"]] = normal_by_host.get(row["first"], 0.)+row["axial_scalar_force_n"]
        xy_hosts = {r["first"] for r in self.generic.interactions if r["kind"] == "floor_tangent_xy"}
        current.require(all(normal_by_host.get(body, 0.) > finite.floor_method.NORMAL_ACTIVATION_THRESHOLD_N for body in xy_hosts),
                        "a current centroid XY restraint has lost compression; no tensile floor anchor supplied")
        current.verify(self.source_sha256)
        return {**timber.case_source(self.binding), "energy_nmm": energy, "gradient_n": gradient, "hessian_csr": hessian,
            "component_potential_energies_nmm": components, "final_q_canonical_sha256": canonical_sha(q.tolist()),
            "same_pose_cached_complete_timber_response_used": cached,
            "signed_gradient_inf_n": float(np.max(abs(gradient))),
            "owner_virtual_work_residual_inf_n_nmm": error,
            "owner_physical_action_wrenches_about_origin": {b: v.tolist() for b, v in physical.items()},
            "owner_explicit_panel_generalized_correction_wrenches_about_origin": {b: v.tolist() for b, v in corrections.items()},
            "owner_negative_gradient_rigid_projection_wrenches_about_origin": {b: v.tolist() for b, v in work.items()},
            "owner_virtual_work_residuals": {b: v.tolist() for b, v in residuals.items()},
            "sum_owner_external_and_generalized_wrenches_about_origin": sum(physical[b]+corrections[b] for b in work).tolist(),
            "floor_normal_sum_by_host_n": normal_by_host, "floor_centroid_XY_hosts": sorted(xy_hosts),
            "floor_support_basis": "32 original normal points and the two original enabled rear-leg centroid XY groups",
            "full_finite_kinematic_map": self.map, "finite_interaction_actions": generic["finite_interaction_actions"],
            "finite_body_applied_loads": generic["finite_body_applied_loads"],
            "panel_generalized_load_corrections": generic["panel_generalized_load_corrections"],
            "loaded_four_port_fittings": fittings["fittings"],
            "timber_branch_counts": bedding["branch_counts"], "timber_trial_scope": bedding["trial_scope"],
            "finite_equilibrium_established": False, "physical_stiffness_demand_strength_or_acceptance_qualified": False}


def cached_timber_evidence(potential, poses):
    """Authenticate the full force result, never substitute the probe receipts."""
    evidence = current.read(TIMBER_EVIDENCE)
    closure = dict(potential.source_sha256)
    if "preserved_force_evaluation" in evidence:
        preserved = evidence["preserved_force_evaluation"]
        current.require(preserved["result"] == timber.PRESERVED_FORCE
            and preserved["producer_snapshot"] == timber.PRESERVED_PRODUCER
            and preserved["numerical_evaluation_repeated"] is False and preserved["constitutive_ast_unchanged"] is True,
            "exact preserved force evaluation and producer provenance required")
        closure = current.join(closure, {r["path"]: r["sha256"] for r in [timber.PRESERVED_FORCE, timber.PRESERVED_PRODUCER]})
    verified_sources = current.join(evidence["source_sha256"], {TIMBER_EVIDENCE["path"]: TIMBER_EVIDENCE["sha256"]})
    current.verify(verified_sources)
    current.require(evidence["schema"] == "eoere_current_reference_material_timber_bedding/v2"
        and evidence["producer"] == TIMBER_PRODUCER and evidence["source_sha256"] == closure
        and evidence["force_law_source_sha256"] == potential.source_sha256
        and evidence["case_sequence"] == component.SEQUENCE and evidence["all_sources_unchanged"] is True
        and evidence["geometry_revision"] == "eoere-raised-kicker-screws-v1"
        and evidence["hardware_revision"] == "eoere-selected-purchase-hardware-v1" and evidence["extra_grid"] is False
        and evidence["force_and_gradient_evaluated"] is True and evidence["full_current_tangent_evaluated"] is False
        and evidence["finite_frame_equilibrium_or_native_FEA_performed"] is False
        and evidence["physical_stiffness_or_demand_or_strength_qualified"] is False and evidence["structural_acceptance"] is False
        and evidence["fixed_samples"] == potential.samples and evidence["sample_row_columns"] == timber.ROW_COLUMNS,
        "exact complete current diagnostic timber force evidence required")
    for row, (binding, q, _case, _domain) in zip(evidence["cases"], poses, strict=True):
        current.require(all(row[k] == value for k, value in timber.case_source(binding).items())
            and not (set(binding)-{"case_id", "state_id", "field"}) & row.keys()
            and row["final_q_canonical_sha256"] == canonical_sha(q.tolist())
            and row["fixed_sample_descriptor_sha256"] == potential.descriptor_sha
            and len(row["sample_rows"]) == len(potential.samples)
            and [r[0] for r in row["sample_rows"]] == list(range(len(potential.samples)))
            and all(len(r) == len(timber.ROW_COLUMNS) for r in row["sample_rows"])
            and dict(Counter(r[1] for r in row["sample_rows"])) == row["branch_counts"]
            and np.asarray(row["gradient_n"]).shape == q.shape and np.isfinite(row["gradient_n"]).all()
            and np.isfinite(row["energy_nmm"]) and set(row["owner_wrenches_at_world_origin"]) == set(potential.maps)
            and row["trial_scope"]["remaining_possible_new_neighbor_count"] == 0,
            "complete own saved force state and fixed cell bindings required")
    current.verify(verified_sources)
    return evidence


def reference_matrix(bundle, pins):
    source, record = bundle["arrays"], bundle["K"]
    current.require(pins.get(source["path"]) == source["sha256"] == current.sha(current.ROOT/source["path"])
        and record["storage"] == "csr", "authenticated own reference elastic array bank required")
    with np.load(current.ROOT/source["path"], allow_pickle=False) as arrays:
        result = csr_matrix((arrays[record["data"]].copy(), arrays[record["indices"]].copy(),
                             arrays[record["indptr"]].copy()), shape=record["shape"])
    return result


def current_interactions(bundle, field):
    selection = preflight.current_contacts(bundle, field)
    enabled = set(selection["enabled_floor_tangent_ids"])
    groups = [r["descriptor"] for r in bundle["partitions"]["groups"]]
    contacts = [r["descriptor"] for r in bundle["partitions"]["contacts"] if r["descriptor"]["kind"] != "timber_face_contact"]
    tangents = [r["descriptor"] for r in bundle["partitions"]["tangents"] if r["descriptor"]["id"] in enabled]
    interactions = finite.describe_interactions(groups, contacts, tangents)
    current.require(dict(Counter(r["kind"] for r in interactions)) == INTERACTION_COUNTS,
                    "current finite interaction census differs; no historical support transfer")
    return interactions, selection


def execution_pins():
    own_ref()
    current.require(timber.own_ref() == TIMBER_PRODUCER and precision.own_ref() == PRECISION_PRODUCER
        and preflight.own_ref() == PREFLIGHT_PRODUCER and finite.LOADED_PRODUCER_SHA256 == FINITE_PRODUCER["sha256"]
        and common.LOADED_PRODUCER_SHA256 == COMMON_PRODUCER["sha256"], "exact loaded current composition helpers required")
    refs = [own_ref(), TIMBER_PRODUCER, PRECISION_PRODUCER, PREFLIGHT_PRODUCER, FINITE_PRODUCER, COMMON_PRODUCER,
        preflight.PARTITION, precision.METHOD, TIMBER_EVIDENCE]
    return current.join(finite.source_pins(), common.source_pins(), precision.execution_pins(),
                        {r["path"]: r["sha256"] for r in refs})


def prepare_current():
    """Prepare current owned adapters once, then bind all six independent loads."""
    pins = execution_pins()
    current.verify(pins)
    bedding, poses, _neighbors = timber.prepare_current()
    evidence = cached_timber_evidence(bedding, poses)
    pins = current.join(pins, bedding.source_sha256, evidence["source_sha256"])
    current.verify(pins)
    router_method = component.load(preflight.PARTITION, "current_finite_full_router")
    fitting_method = component.load(precision.METHOD, "current_finite_full_fittings")
    fields = [current.read(binding["field"]) for binding, _q, _case, _domain in poses]
    bundles = [current.read(field["operator_bundle"]["manifest"]) for field in fields]
    first, chart = fields[0], bundles[0]["coordinate_map"]
    current.require(chart["final_ndof"] == 9350 and not chart["unused_legacy_two_port_fitting_indices"],
                    "complete current chart without unused legacy fitting coordinates required")
    for field, bundle in zip(fields, bundles, strict=True):
        current.require(bundle["coordinate_map"] == chart and field["source_inputs"]["scenario"] == first["source_inputs"]["scenario"]
            and field["source_inputs"]["shafts"] == first["source_inputs"]["shafts"]
            and field["source_inputs"]["fitting_poses"] == first["source_inputs"]["fitting_poses"]
            and bundle["case"]["loads"] == field["body_applied_loads"]
            and bundle["original_operator_fingerprint_sha256"] == field["original_operator_fingerprint_sha256"],
            "same current geometry/operators and each own source load case required")
        preflight.current_partition(router_method, chart, field["body_applied_loads"], field["source_inputs"]["shafts"])
    reference = reference_matrix(bundles[0], pins)
    assembly, base, replacement, errors = restore_mechanics(chart, first["source_inputs"]["scenario"],
        first["source_inputs"]["shafts"], reference, source_sha256=pins)
    current.require(base.ndof == 9450 and len(base.members) == 22 and len(base.shafts) == 100,
                    "current whole finite mechanics and source-ordered 100 spins required")
    fitting_poses = {p["id"]: p for p in first["source_inputs"]["fitting_poses"]}
    fittings = {body: precision.prepare_current_fitting(fitting_method, fitting_poses[body], descriptor, full_ndof=9450)
                for body, descriptor in chart["four_port_fittings"].items()}
    for body, fitting in fittings.items():
        index, block = fitting.element.elastic_block()
        errors.append(check_reference_block(reference, np.asarray(index), np.asarray(block), body))
    router = four_port_router(base, fittings, router_method, fitting_method, pins)
    raw_panels, integrated, panel_pins, proof = current.load_panel_dependencies(first["source_inputs"])
    current.verify_panel_source_inputs(first["source_inputs"], proof)
    pins = current.join(pins, router.source_sha256, panel_pins)
    panels = panel_method.prepare_adapters(raw_panels, {body: np.asarray(row["indices"]) for body, row in chart["panels"].items()}, 9450, pins)
    mapping = finite.kinematic_map(router, panels)
    current.require({body: mapping["mechanical_bodies"][body] for body in base.members} == bedding.charts,
                    "full-frame mechanics and contact material charts differ")
    embeddings = {}
    for body, panel in panels.items():
        row = chart["panels"][body]
        current.require(canonical_sha(json_value(panel.geometry)) == canonical_sha(row["geometry"]) and panel.basis.width == row["width_mm"]
            and panel.basis.height == row["height_mm"] and panel.basis.order == row["basis_order_per_direction"]
            and np.array_equal(panel.basis.knots, row["knots_normalized"]) and panel.panel["thickness"] == row["thickness_mm"],
            "own current finite panel source and basis differ")
        errors.append(check_reference_block(reference, panel.indices, csr_matrix(panel.panel["K"]).toarray(), body))
        embeddings[body] = prepare_panel_embedding(panel)
    prepared, selections = [], []
    panel_cases = {r["id"]: r for r in panel_method.method.load_cases(integrated)}
    panel_load_class = current_panel_load_class(first["source_inputs"], integrated, proof, panels,
        {binding["case_id"]: field["body_applied_loads"] for (binding, *_), field in zip(poses, fields, strict=True)}, pins)
    for (binding, q, _case, _domain), field, bundle, cached in zip(poses, fields, bundles, evidence["cases"], strict=True):
        current.verify_panel_source_inputs(field["source_inputs"], proof)
        interactions, selection = current_interactions(bundle, field)
        current.require(bundle["case"]["primary_load_basis"] is True, "current retained-original-top accessory scenario required")
        loads = {body: panel_load_class(panel, panel_cases[binding["case_id"]], integrated, "original_top", field["body_applied_loads"])
                 for body, panel in panels.items()}
        nonpanel = [r for r in finite.mechanical_load_ports(assembly, bundle["case"], panels) if r["body"] not in fittings]
        current.require(not any(np.linalg.norm(r.get("moment_xyz_nmm", [0., 0., 0.])) > 0. for r in nonpanel),
                        "nonzero point couple lacks a declared finite dead-load potential")
        owned_ids = {r["source_load_id"] for r in nonpanel}
        owned_ids.update(r["id"] for load in loads.values() for r in load.loads)
        owned_ids.update(r["id"] for r in field["body_applied_loads"] if r["body"] in fittings)
        current.require(owned_ids == {r["id"] for r in field["body_applied_loads"]} and len(owned_ids) == 835,
                        "all 835 own source loads must enter once through their own family")
        identity = {**bundle["case"], "state_id": binding["state_id"]}
        generic = finite.FiniteFramePotential(router, panels, loads, interactions, nonpanel, case=identity,
            source_sha256=pins, shaft_replacement=replacement)
        loaded = LoadedFittings(fittings, field, pins)
        prepared.append(CurrentFrame(generic, bedding, loaded, binding, q, source_sha256=pins, cached_timber=cached))
        selections.append({**timber.case_source(binding), **selection})
    current.verify(pins)
    return prepared, {"source_sha256": pins, "reference_block_checks": errors, "floor_source_selections": selections,
        "panel_runtime_embeddings": embeddings,
        "same_source_full_timber_response": TIMBER_EVIDENCE, "current_panel_preparation": proof,
        "body_counts": preflight.FAMILIES, "original_load_counts": preflight.LOAD_COUNTS,
        "finite_interaction_counts": INTERACTION_COUNTS, "full_ndof": 9450}


def json_value(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, dict): return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [json_value(v) for v in value]
    return value


def run(*, progress=None):
    prepared, proof = prepare_current()
    results = []
    for potential in prepared:
        result = potential.diagnostic_response()
        result.pop("hessian_csr")
        results.append(json_value(result))
        if progress: progress({"case_id": result["case_id"], "signed_gradient_inf_n": result["signed_gradient_inf_n"],
            "owner_virtual_work_residual_inf_n_nmm": result["owner_virtual_work_residual_inf_n_nmm"]})
    current.verify(proof["source_sha256"])
    return {"schema": "eoere_current_complete_finite_frame_diagnostic/v1", "producer": own_ref(), **proof,
        "all_sources_unchanged": True, "cases": results, "case_sequence": component.SEQUENCE,
        "geometry_revision": "eoere-raised-kicker-screws-v1", "hardware_revision": "eoere-selected-purchase-hardware-v1", "extra_grid": False,
        "complete_current_source_model_composed": True, "saved_first_order_states_are_diagnostic_only": True,
        "equilibrium_solve_native_FEA_geometry_change_or_strength_acceptance": False,
        "release": current.manifest()["release"],
        "limits": ["Complete finite potentials and same-state work closure are method results, not physical stiffness or load bounds.",
            "Only the exact reviewed timber force states are cached; future trials recompute complete timber admission/contact and local fitting stationarity.",
            "Current floor restraint remains the unverified no-slip two-centroid analytical branch, with compression required; no floor anchor is introduced.",
            "The two panel RHS correction terms remain explicit generalized loads rather than invented physical tractions.",
            "No finite equilibrium, complete joint/hardware resistance, finished-timber strength/restraint or movement acceptance is inferred."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run(progress=lambda value: print(json.dumps(value), flush=True)))
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__": main()
