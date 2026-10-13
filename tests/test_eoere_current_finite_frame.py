"""Known numerical identities and current ownership; no production frame solve."""

import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import coo_matrix, eye
from scipy.spatial.transform import Rotation
from test_eoere_current_timber_bedding import (
    current_force_fixture,
    potential_fixture,
    preserved_force_fixture,
)

from scripts import eoere_current_finite_frame as frame


@pytest.fixture(scope="module")
def methods():
    return (frame.timber.inverse.runtime_methods(),
        frame.component.load(frame.precision.METHOD, "current_frame_test_fittings"),
        frame.component.load(frame.preflight.PARTITION, "current_frame_test_router"))


def recipe():
    chart = {"final_ndof": 9448, "rotation_scale": 1000., "timber": {}, "shafts": {}}
    rows, cols, values = [], [], []
    def add(index, block):
        i, j = np.nonzero(block)
        rows.extend(index[i]); cols.extend(index[j]); values.extend(block[i, j])
    for j, body in enumerate(["slave", "master"]):
        index = np.arange(18).reshape(3, 6)+18*j
        stations = np.array([0., 40., 100.])
        source = {"name": body, "start": [0., 0., 0.], "end": [100., 0., 0.],
            "axis": [1., 0., 0.], "section_u": [0., 1., 0.], "section_v": [0., 0., 1.], "width_mm": 10., "depth_mm": 12.}
        chart["timber"][body] = {"index": index.tolist(), "stations": stations.tolist(), "source": source,
            "start": source["start"], "axis": source["axis"]}
        scale = np.tile([1., 1., 1., .001, .001, .001], 2)
        for i, length in enumerate(np.diff(stations)):
            k = frame.finite.frame.beam_stiffness(length, 120., 1440., 1000.,
                frame.finite.frame.rectangular_torsion(10., 12.), 10000., 640.)
            add(index[i:i+2].ravel(), k*scale[:, None]*scale[None, :])
    sources = []
    for j, body in enumerate(["shaft/z-source", "shaft/a-source"]):
        row = {"body": body, "axis_id": body[6:], "point": [200.+200.*j, 0., 0.],
            "basis": np.eye(3).tolist(), "diameter_mm": 8.+2.*j, "ends": [], "surfaces": []}
        k, local, _elements = frame.common.reduced_shaft_matrix([0., 100.], row["diameter_mm"], 200000., 200000./2.6)
        index = np.where(local >= 0, local+36+11*j, -1)
        chart["shafts"][body] = {**row, "index": index.tolist(), "stations": [0., 100.]}
        add(index[index >= 0], k.toarray())
        sources.append(row)
    chart["shafts"] = dict(sorted(chart["shafts"].items()))
    matrix = coo_matrix((values, (rows, cols)), shape=(9448, 9448)).tocsr()
    scenario = {"timber_e_mpa": 10000., "timber_shear_ratio": .064,
        "common_shaft_parameters": {"steel_E_mpa": 200000., "steel_nu": .3}}
    return chart, scenario, sources, matrix


def small_frame(methods, *, floor=False):
    kernels, fitting_method, router_method = methods
    chart, scenario, sources, reference = recipe()
    assembly, base, replacement, errors = frame.restore_mechanics(chart, scenario, sources, reference, source_sha256={})
    pose = {"id": "own-fitting", "origin_xyz_mm": [200., 300., 400.],
        "u_xyz": [1., 0., 0.], "v_xyz": [0., 1., 0.], "w_xyz": [0., 0., 1.]}
    model, _ = fitting_method.model_from_reference_pose(pose["origin_xyz_mm"], pose["u_xyz"], pose["v_xyz"], pose["w_xyz"])
    element = fitting_method.GuardedFourPortAssemblyElement(model, pose["id"], np.arange(100, 124), 9450)
    fitting = frame.precision.prepare_current_fitting(fitting_method, pose, element.descriptor(), full_ndof=9450)
    router = frame.four_port_router(base, {fitting.body: fitting}, router_method, fitting_method, {})
    initial, q = potential_fixture(kernels), np.zeros(9450)
    original = initial[0]
    charts = {b: r for b, r in frame.finite.kinematic_map(router, {})["mechanical_bodies"].items() if b in base.members}
    local_boxes = {b: frame.timber.neighbors.local_reference_box(b, charts[b], original.extents[b], g, kernels[3])
                   for b, g in original.geometries.items()}
    bedding = frame.timber.TimberBedding(charts, original.extents, original.geometries, original.samples,
        methods=kernels, local_boxes=local_boxes, source_sha256={}, ndof=9450)
    q[[1, 7, 13]] = -.2
    q[base.shafts["shaft/z-source"]["index"][-1, 1]] = .02
    fitting_load = {"id": "own-fitting-gravity", "body": fitting.body,
        "point_xyz_mm": (np.asarray(model.origin)+[1., 2., 3.]).tolist(), "force_xyz_n": [0., 0., -5.]}
    dead = [{"id": "own-timber-load", "body": "slave", "point_xyz_mm": [50., 0., 0.], "force_xyz_n": [0., 0., -11.]},
        {"id": "own-shaft-load", "body": "shaft/z-source", "point_xyz_mm": [250., 0., 0.], "force_xyz_n": [0., 0., -3.]}]
    field = {"response": {"q": np.zeros(9350).tolist()}, "body_applied_loads": [fitting_load, *dead],
        "four_port_fitting_actions": [{"body": fitting.body, "loaded_heel_q_mm_rad": np.zeros(6).tolist()}]}
    loaded = frame.LoadedFittings({fitting.body: fitting}, field, {})
    interactions = []
    if floor:
        normals, tangents = [], []
        for body in (["slave", "master"] if floor == "both" else ["slave"]):
            normals.append({"id": body+"/own-normal", "kind": "floor_normal", "first": body, "second": "floor",
                "point_xyz_mm": [31., 0., -6.], "direction_xyz": [0., 0., 1.], "stiffness": 25.})
            tangents.extend({"id": body+"/own-tangent-"+str(i), "kind": "floor_tangent", "first": body,
                "point_xyz_mm": [31., 0., -6.], "direction_xyz": np.eye(3)[i].tolist(), "stiffness": 17.} for i in [0, 1])
            q[base.members[body]["index"][:, 2]] = -.1
        interactions = frame.finite.describe_interactions([], normals, tangents)
    generic = frame.finite.FiniteFramePotential(router, {}, {}, interactions, dead,
        case={"case_id": "coupon", "state_id": "own-state", "accessory_placement": "coupon"}, shaft_replacement=replacement)
    binding = {"case_id": "coupon", "state_id": "own-state", "field": {"path": "synthetic"}}
    binding.update(gradient_inf_n=1e-9, current_equilibrium_and_recovery_pass=True)
    cached = bedding.response(q, tangent=False)
    cached.pop("hessian_csr"); cached["gradient_n"] = cached["gradient_n"].tolist()
    potential = frame.CurrentFrame(generic, bedding, loaded, binding, q, source_sha256={}, cached_timber=cached)
    return potential, errors, assembly


def test_restore_keeps_owned_gross_matrices_and_actual_source_order_for_new_spins(methods):
    potential, errors, assembly = small_frame(methods)
    base = potential.generic.mechanics.base
    assert assembly.ndof == 9448 and base.ndof == 9450
    assert [r["body"] for r in errors] == ["slave", "master", "shaft/z-source", "shaft/a-source"]
    assert max(r["relative_reference_block_error"] for r in errors) < 1e-14
    assert base.shafts["shaft/z-source"]["index"][0, 3] == 9448
    assert base.shafts["shaft/a-source"]["index"][0, 3] == 9449
    q = np.zeros(9450); q[12] = .1
    result = potential.generic.shaft_replacement.replacement_response(q, False)
    assert result["energy_nmm"] == pytest.approx(.5*(10000.*120./60.)*.1**2, abs=1e-10)
    assert result["gradient_n"][12] == pytest.approx(2000., abs=1e-9)


@pytest.mark.parametrize("problem", ["matrix", "owner", "station", "duplicate_index", "shaft_source", "shaft_gauge", "material"])
def test_restore_rejects_incompatible_owned_properties_and_reference_blocks(problem):
    chart, scenario, sources, reference = recipe()
    if problem == "matrix": reference[0, 0] += 1.
    if problem == "owner": chart["timber"]["slave"]["source"]["name"] = "foreign"
    if problem == "station": chart["timber"]["slave"]["stations"][1] = 0.
    if problem == "duplicate_index": chart["timber"]["slave"]["index"][1][0] = 0
    if problem == "shaft_source": sources[0]["diameter_mm"] += 1.
    if problem == "shaft_gauge": chart["shafts"][sources[0]["body"]]["index"][0][3] = 9000
    if problem == "material": scenario["timber_e_mpa"] = np.nan
    with pytest.raises(ValueError): frame.restore_mechanics(chart, scenario, sources, reference, source_sha256={})


def test_nodal_world_rigid_modes_match_independent_scipy_pose_differences():
    basis = Rotation.from_rotvec([.21, -.13, .17]).as_matrix()
    centers = np.array([[13., -17., 23.], [71., 19., -31.]])
    q = np.array([.3, -.7, .2, 170., -110., 90., -.2, .5, .8, -70., 190., 130.])
    index, modes = frame.nodal_rigid_modes(centers, np.arange(12).reshape(2, 6), basis, q)
    assert index.tolist() == list(range(12))
    for column in range(6):
        values = []
        for sign in [-1., 1.]:
            h = sign*1e-7
            world_rotation = np.eye(3) if column < 3 else Rotation.from_rotvec(h*np.eye(3)[column-3]).as_matrix()
            translation = h*np.eye(3)[column] if column < 3 else np.zeros(3)
            altered = q.reshape(2, 6).copy()
            for i, row in enumerate(altered):
                row[:3] = basis.T @ (world_rotation @ (centers[i]+basis @ q.reshape(2, 6)[i, :3])+translation-centers[i])
                row[3:] = 1000.*Rotation.from_matrix(basis.T @ world_rotation @ basis @ Rotation.from_rotvec(q.reshape(2, 6)[i, 3:]/1000.).as_matrix()).as_rotvec()
            values.append(altered.ravel())
        np.testing.assert_allclose((values[1]-values[0])/2e-7, modes[:, column], atol=4e-6, rtol=0.)


def test_complete_composition_recovers_all_owner_work_and_only_own_gravity_once(methods):
    potential, _errors, _assembly = small_frame(methods)
    result = potential.diagnostic_response()
    assert result["owner_virtual_work_residual_inf_n_nmm"] < 1e-7
    assert len(result["owner_physical_action_wrenches_about_origin"]) == 5
    assert len(result["loaded_four_port_fittings"]) == 1
    assert len(result["finite_body_applied_loads"]) == 2
    np.testing.assert_allclose(result["sum_owner_external_and_generalized_wrenches_about_origin"][:3], [0., 0., -19.], atol=1e-11, rtol=0.)
    assert result["timber_branch_counts"] == {"closed": 1}
    assert result["same_pose_cached_complete_timber_response_used"] is True
    assert result["finite_equilibrium_established"] is False
    assert result["physical_stiffness_demand_strength_or_acceptance_qualified"] is False
    assert result["saved_first_order_source"] == potential.binding
    assert not {"gradient_inf_n", "current_equilibrium_and_recovery_pass"} & result.keys()


def test_local_heel_accuracy_closes_world_work_at_an_unchanged_current_fitting(methods):
    """An accepted local heel residual can still fail the world-moment gate."""
    _, method, _ = methods
    pose = {"id": "eoere_clip_split_top_center_left", "origin_xyz_mm": [-89.05, 1457.586095203, 2172.205368329],
        "u_xyz": [-1., 0., 0.], "v_xyz": [0., -.6427876099290708, -.7660444429154699],
        "w_xyz": [0., -.7660444429154699, .6427876099290708]}
    model, _ = method.model_from_reference_pose(pose["origin_xyz_mm"], pose["u_xyz"], pose["v_xyz"], pose["w_xyz"])
    element = method.GuardedFourPortAssemblyElement(model, pose["id"], np.arange(100, 124), 9450)
    fitting = frame.precision.prepare_current_fitting(method, pose, element.descriptor(), full_ndof=9450)
    q24 = np.array([4.226306697755668, .571190110183136, -17.42647634056868, -11.475016511757818,
        11.143773100584772, 15.430529812290438, 3.2541166613152197, .12148994522442016, -17.96437456388976,
        -11.619789989959745, 9.00533352306871, 17.20842058457043, 4.427596881352791, 1.0346462150497264,
        -17.644604018319846, -11.360265549821065, 9.66039600647937, 16.462087911020486, 3.54355439894272,
        .6669683188681794, -18.083136291057677, -11.360947789017297, 8.386111572329057, 17.61422129930019])
    seed = np.array([3.7383371951635564, 1.4162594806714495, -18.341016316779243,
        -11.373904302053132, 9.605353927764893, 16.696441839726567])
    load = {"id": "self-weight/eoere_clip_split_top_center_left", "body": fitting.body,
        "point_xyz_mm": [-113.65971554575181, 1441.767274966312, 2153.3532324934463],
        "force_xyz_n": [0., 0., -6.494403558280331]}

    def world_wrench(result):
        value = np.zeros(6)
        for port in result["port_actions"]:
            force = np.asarray(port["external_force_required_at_port_xyz_n"])
            value += np.r_[force, np.asarray(port["external_couple_required_at_port_xyz_nmm"])
                + np.cross(port["point_xyz_mm"], force)]
        gravity = result["current_load_actions"][0]
        force = np.asarray(gravity["force_xyz_n"])
        return value+np.r_[force, np.cross(gravity["point_xyz_mm"], force)]

    original = fitting.condensed_response(q24, heel_seed=seed, loads=[load], tangent=False,
        recover_actions=True, heel_tolerance_n=1e-8, max_local_evaluations=100)
    assert original["heel_residual_inf_n"] < 1e-8
    assert np.max(abs(world_wrench(original))) > 1e-5
    q = np.zeros(9450); q[element.indices] = q24
    initial = seed.copy(); initial[3:] /= 1000.
    field = {"response": {"q": q[:9350].tolist()}, "body_applied_loads": [load],
        "four_port_fitting_actions": [{"body": fitting.body, "loaded_heel_q_mm_rad": initial.tolist()}]}
    loaded = frame.LoadedFittings({fitting.body: fitting}, field, {})
    response = loaded.response(q, tangent=False)
    result = response["fittings"][0]
    assert np.max(abs(world_wrench(result))) < 1e-5
    assert result["heel_residual_inf_n"] < result["local_numerical_accuracy_target_n"] < result["heel_acceptance_gate_n"] == 1e-8
    assert original["local_function_evaluations"] < result["local_function_evaluations"] <= 100
    assert result["heel_hessian_min_symmetric_eigenvalue_n_mm"] > 1e-8
    np.testing.assert_allclose(result["internal_heel_q_mm_1000rad"], original["internal_heel_q_mm_1000rad"], atol=1e-9, rtol=0.)
    assert len(result["current_load_actions"]) == 1


@pytest.mark.parametrize("response_path", ["cached", "fresh"])
def test_complete_owner_work_gate_rejects_a_recovered_action_mismatch(monkeypatch, methods, response_path):
    potential, _, _ = small_frame(methods)
    original = potential.generic.response

    def mismatched_action(q, tangent=True, **kwargs):
        result = original(q, tangent, **kwargs)
        result["finite_body_applied_loads"][0]["free_spatial_moment_xyz_nmm"][1] += 2e-4
        return result

    monkeypatch.setattr(potential.generic, "response", mismatched_action)
    with pytest.raises(ValueError, match="same-state complete owner force/moment virtual-work closure failed"):
        if response_path == "cached": potential.diagnostic_response()
        else: potential.response(potential.q, tangent=False)


def test_refinement_target_is_distinct_from_the_original_heel_acceptance_gate(methods):
    _, method, _ = methods
    origin, u, v = [-1130.3, -105.85, 277.], [1., 0., 0.], [0., 0., 1.]
    model, _ = method.model_from_reference_pose(origin, u, v, [0., -1., 0.])
    element = method.GuardedFourPortAssemblyElement(model, "accuracy-floor", np.arange(100, 124), 9450)
    fitting = frame.precision.stable_adapter(method, element, refine_heel=True)
    q24 = np.array([12.15861388368663, -30.19765942760619, 5.712634763271397, 20.803621076891947,
        11.948424967747972, 30.016354958438423, 10.636806567020393, -30.198231080804074, 6.769590217366234,
        20.562770869266522, 11.680615640511057, 30.01884726496352, 12.614400630082484, -33.4930961051154,
        6.436191489154649, 20.622248925733924, 5.39793170554166, 29.614290783524787, 11.297372423383473,
        -33.48986310402552, 7.491132524025922, 20.613374318147578, 8.67892448369535, 28.822352285576013])
    seed = np.array([11.403268494806943, -32.151801319581416, 6.973053206771393,
        20.581491676111646, 10.051160253320921, 29.970745354852372])
    loads = [{"id": "own-gravity", "body": fitting.body, "force_xyz_n": [0., 0., -6.494403558280331],
        "point_xyz_mm": [-1105.690284454248, -105.85, 301.6097155457518]}]
    original_refiner = frame.precision.residual_refined_root
    with pytest.raises(ValueError, match="finite internal heel failed local stationarity"):
        fitting.condensed_response(q24, heel_seed=seed, loads=loads, tangent=False,
            recover_actions=True, heel_tolerance_n=1e-9, max_local_evaluations=100)
    result = frame.condensed_fitting_response(fitting, q24, seed=seed, loads=loads, tangent=False)
    assert 1e-9 < result["heel_residual_inf_n"] < 1e-8
    assert result["local_function_evaluations"] <= 100
    assert frame.precision.residual_refined_root is original_refiner
    work = frame.precision.fitting_work_check(fitting, q24, result, loads)
    closure = np.asarray(work["independent_body_wrench_residual_n_nmm"])
    heel = np.asarray(origin)+np.asarray(result["internal_heel_q_mm_1000rad"][:3])
    closure[3:] += np.cross(heel, closure[:3])
    assert np.max(abs(closure)) < 1e-5
    q = np.zeros(9450); q[element.indices] = q24
    field_seed = seed.copy(); field_seed[3:] /= 1000.
    field = {"response": {"q": q[:9350].tolist()}, "body_applied_loads": loads,
        "four_port_fitting_actions": [{"body": fitting.body, "loaded_heel_q_mm_rad": field_seed.tolist()}]}
    loaded = frame.LoadedFittings({fitting.body: fitting}, field, {},
        numerical_translation_origins={fitting.body: np.zeros(3)})
    public_result = loaded.response(q, tangent=False)["fittings"][0]
    assert public_result["heel_acceptance_gate_n"] == 1e-8
    assert public_result["local_numerical_accuracy_target_n"] == 1e-9
    assert public_result["local_numerical_target_met"] is False
    assert public_result["heel_residual_inf_n"] == pytest.approx(result["heel_residual_inf_n"], abs=1e-15, rel=0.)
    assert frame.precision.residual_refined_root is original_refiner
    with pytest.raises(ValueError, match="finite complete four-port value required"):
        frame.condensed_fitting_response(fitting, np.zeros(23), seed=seed, loads=loads, tangent=False)
    assert frame.precision.residual_refined_root is original_refiner


def test_fixed_translation_restores_current_world_actions_energy_and_tangent(methods):
    _, method, _ = methods
    model, _ = method.model_from_reference_pose([1127.125, 1457.586095203, 2172.205368329],
        [-1., 0., 0.], [0., -.6427876099290708, -.7660444429154699],
        [0., -.7660444429154699, .6427876099290708])
    element = method.GuardedFourPortAssemblyElement(model, "translation-precision", np.arange(100, 124), 9450)
    fitting = frame.precision.stable_adapter(method, element, refine_heel=True)
    q24 = np.array([44.01700879984672, -.8469416715644079, -16.131516834973727, -57.9448631054819,
        -15.405128632014378, -22.671887474188548, 45.42076203452944, -2.5643437376377722,
        -18.181712602343197, -58.70444149533984, -10.250029757764114, -26.994838424670377,
        43.92905879263485, -5.261895535079296, -12.666182671604343, -58.981212024411654,
        -17.408755555343667, -20.5940954826088, 45.02011645691028, -7.192363230053194,
        -14.974130647491203, -58.97534009069692, -12.712826142463635, -22.767231193963443])
    seed = np.array([44.71434680854519, -3.2935841226702136, -16.291272534280136,
        -58.921053848529624, -13.871781471200421, -23.878815980100818])
    loads = [{"id": "own-gravity", "body": fitting.body, "force_xyz_n": [0., 0., -6.494403558280331],
        "point_xyz_mm": [1102.515284454248, 1441.767274966312, 2153.3532324934463]}]
    before = frame.condensed_fitting_response(fitting, q24, seed=seed, loads=loads, tangent=True)
    q = np.zeros(9450); q[element.indices] = q24
    field_seed = seed.copy(); field_seed[3:] /= 1000.
    field = {"response": {"q": q[:9350].tolist()}, "body_applied_loads": loads,
        "four_port_fitting_actions": [{"body": fitting.body, "loaded_heel_q_mm_rad": field_seed.tolist()}]}
    loaded = frame.LoadedFittings({fitting.body: fitting}, field, {})
    response = loaded.response(q, tangent=True)
    after = response["fittings"][0]

    def world_wrench(row):
        terms = []
        for port in row["port_actions"]:
            force = np.asarray(port["external_force_required_at_port_xyz_n"])
            terms.append(np.r_[force, np.asarray(port["external_couple_required_at_port_xyz_nmm"])
                +np.cross(port["point_xyz_mm"], force)])
        for load in row["current_load_actions"]:
            force = np.asarray(load["force_xyz_n"])
            terms.append(np.r_[force, np.asarray(load["free_couple_xyz_nmm"])+np.cross(load["point_xyz_mm"], force)])
        return np.sum(terms, axis=0)

    assert np.max(abs(world_wrench(before))) > 1e-5
    assert np.max(abs(world_wrench(after))) < 1e-5
    assert after["heel_residual_inf_n"] < 1e-9 < after["heel_acceptance_gate_n"] == 1e-8
    assert after["local_numerical_target_met"] is True
    assert after["local_function_evaluations"] <= 100
    np.testing.assert_array_equal(after["numerical_translation_origin_xyz_mm"], q24[:3])
    assert after["energy_nmm"] == pytest.approx(before["energy_nmm"], abs=1e-8)
    assert after["dead_load_work_from_reference_nmm"] == pytest.approx(before["dead_load_work_from_reference_nmm"], abs=1e-9)
    np.testing.assert_allclose(after["gradient_n"], before["gradient_n"], atol=1e-8, rtol=0.)
    for key in ["port_actions", "strip_root_actions", "current_load_actions"]:
        for first, second in zip(before[key], after[key], strict=True):
            np.testing.assert_allclose(first["point_xyz_mm"], second["point_xyz_mm"], atol=1e-10, rtol=0.)
    direction = np.zeros(9450); direction[element.indices[[0, 8, 15, 21]]] = [.1, -.2, .05, -.03]
    h = 1e-3
    plus, minus = loaded.response(q+h*direction, tangent=False), loaded.response(q-h*direction, tangent=False)
    assert direction@response["gradient_n"] == pytest.approx((plus["energy_nmm"]-minus["energy_nmm"])/(2*h), abs=3e-6)
    np.testing.assert_allclose(response["hessian_csr"]@direction,
        (plus["gradient_n"]-minus["gradient_n"])/(2*h), atol=2e-4, rtol=1e-7)
    np.testing.assert_array_equal(plus["fittings"][0]["numerical_translation_origin_xyz_mm"], q24[:3])


@pytest.mark.parametrize("director_owner", ["slave", "master"])
def test_off_axis_connector_free_couple_reaches_its_own_owner(director_owner, methods):
    potential, _, _ = small_frame(methods)
    router = potential.generic.mechanics
    group = {"kind": "panel_screw", "axis_id": "off-axis-coupon", "first": "slave", "second": "master",
        "point_xyz_mm": [31., 0., 0.], "basis": np.eye(3).tolist(), "ka": 1000., "kl": 0.}
    interactions = frame.finite.describe_interactions([group], [], [])
    interactions[0]["director_owner"] = director_owner
    generic = frame.finite.FiniteFramePotential(router, {}, {}, interactions, [],
        case=potential.generic.case, shaft_replacement=potential.generic.shaft_replacement)
    q = np.zeros(9450)
    q[router.members["slave"]["index"][:, :3]] = [.2, .6, 1.]
    result = generic.response(q, False, recover_actions=True)
    action = result["finite_interaction_actions"][0]
    expected_couple = np.array([0., 200., -120.])
    for side in ["first", "second"]:
        np.testing.assert_allclose(action["moment_on_"+side+"_at_current_point_xyz_nmm"],
            expected_couple if action[side] == director_owner else np.zeros(3), atol=1e-9, rtol=0.)
    work = frame.owner_work_wrenches(router, {}, q, result["gradient_n"])
    physical, corrections = frame.physical_owner_wrenches(work, result,
        {"owner_wrenches_at_world_origin": {}}, {"fittings": []})
    expected = {"slave": np.r_[[-200., 0., 0.], -expected_couple], "master": np.r_[[200., 0., 0.], np.zeros(3)]}
    expected[director_owner][3:] += expected_couple
    for body in work:
        np.testing.assert_allclose(physical[body], expected.get(body, np.zeros(6)), atol=1e-8, rtol=0.)
        np.testing.assert_allclose(work[body], physical[body]+corrections[body], atol=1e-8, rtol=0.)
    np.testing.assert_allclose(sum(physical.values()), np.zeros(6), atol=1e-8, rtol=0.)


def test_complete_gradient_and_tangent_match_centered_energy_and_residual_differences(methods):
    potential, _errors, _assembly = small_frame(methods)
    q = potential.q.copy()
    result = potential.response(q, tangent=True)
    direction = np.zeros(9450); direction[[1, 7, 19, 25, 101, 113]] = [.2, -.1, .3, -.2, .0001, -.0002]
    h = 1e-3
    plus, minus = potential.response(q+h*direction, tangent=False), potential.response(q-h*direction, tangent=False)
    assert direction @ result["gradient_n"] == pytest.approx((plus["energy_nmm"]-minus["energy_nmm"])/(2.*h), abs=2e-7)
    np.testing.assert_allclose(result["hessian_csr"] @ direction, (plus["gradient_n"]-minus["gradient_n"])/(2.*h), atol=2e-5, rtol=0.)


def test_future_response_recomputes_contact_and_diagnostic_cache_is_exact_pose_only(monkeypatch, methods):
    potential, _errors, _assembly = small_frame(methods)
    genuine, calls = potential.bedding.response, []
    def counted(q, *, tangent):
        calls.append(q.copy())
        return genuine(q, tangent=tangent)
    monkeypatch.setattr(potential.bedding, "response", counted)
    potential.diagnostic_response()
    assert calls == []
    q = potential.q.copy(); q[[1, 7, 13]] = -.3
    result = potential.response(q, tangent=False)
    assert len(calls) == 1 and np.array_equal(calls[0], q)
    assert result["same_pose_cached_complete_timber_response_used"] is False
    assert result["final_q_canonical_sha256"] != potential.cached_timber["final_q_canonical_sha256"]
    potential.cached_timber["final_q_canonical_sha256"] = result["final_q_canonical_sha256"]
    with pytest.raises(ValueError, match="unchanged authenticated"): potential.diagnostic_response()


def test_floor_xy_requires_current_compression_and_cannot_act_as_a_tensile_anchor(methods):
    potential, _errors, _assembly = small_frame(methods, floor=True)
    result = potential.diagnostic_response()
    assert result["floor_normal_sum_by_host_n"] == {"slave": pytest.approx(2.5)}
    assert result["floor_centroid_XY_hosts"] == ["slave"]
    q = potential.q.copy(); q[[2, 8, 14]] = .1
    with pytest.raises(ValueError, match="lost compression"): potential.response(q, tangent=False)


def test_each_of_two_xy_hosts_needs_its_own_current_compression(methods):
    potential, _, _ = small_frame(methods, floor="both")
    result = potential.diagnostic_response()
    assert result["floor_normal_sum_by_host_n"] == {"slave": pytest.approx(2.5), "master": pytest.approx(2.5)}
    assert result["floor_centroid_XY_hosts"] == ["master", "slave"]
    for body in ["slave", "master"]:
        q = potential.q.copy()
        index = potential.generic.mechanics.members[body]["index"]
        q[index[:, 2]] = .1
        q[index[:, 0]] += .2
        q[index[:, 1]] += .1
        with pytest.raises(ValueError, match="lost compression"): potential.response(q, tangent=False)


@pytest.mark.parametrize("response_path", ["cached", "fresh"])
@pytest.mark.parametrize("changed", ["timber_measure", "timber_stiffness", "shaft_stiffness", "fitting_registry",
    "legacy_fitting", "replacement_base", "router_members"])
def test_live_prepared_operator_changes_fail_before_response(methods, changed, response_path):
    potential, _, _ = small_frame(methods)
    if changed == "timber_measure": potential.bedding.samples[0]["reference_area_mm2"] *= 2.
    if changed == "timber_stiffness": potential.generic.shaft_replacement.timber_elements[1].beam.local_stiffness[:] *= 2.
    if changed == "shaft_stiffness": potential.generic.shaft_replacement.elements[0]["beam"].reference_positions[1, 0] += 1.
    if changed == "fitting_registry": potential.fittings.fittings.clear()
    if changed == "legacy_fitting":
        stiffness = np.zeros((12, 12))
        stiffness[np.ix_([0, 6], [0, 6])] = 12000.*np.array([[1., -1.], [-1., 1.]])
        model = frame.mechanical.ObjectiveCondensedFitting(np.array([[0., 0., 0.], [100., 0., 0.]]), stiffness)
        potential.generic.mechanics.base.fittings["historical"] = {
            "index": np.array([[0, 1, 2, 3, 4, 5], [12, 13, 14, 15, 16, 17]]), "model": model}
        local_q = np.zeros(12); local_q[6] = .1
        assert model.response(local_q, False)["energy_nmm"] == pytest.approx(60.)
    if changed == "replacement_base": potential.generic.shaft_replacement.mechanics = copy.copy(potential.generic.mechanics.base)
    if changed == "router_members": potential.generic.mechanics.members = copy.deepcopy(potential.generic.mechanics.members)
    with pytest.raises(ValueError, match="fixed current frame sources changed"):
        potential.diagnostic_response() if response_path == "cached" else potential.response(potential.q, tangent=False)


def panel_recipe(monkeypatch, tmp_path):
    """Six small genuine plate/load adapters with a distinct current projection."""
    method = frame.panel_method.method
    panels, stock = {}, []
    for i, body in enumerate(method.PANELS):
        basis = method.SheetBasis(100., 100., 2)
        geometry = {"name": body, "origin": np.array([-50., 0., 0.]), "axes": np.eye(3),
            "inward": np.array([0., 0., -1.]), "front_height": 100.}
        panel = {"basis": basis, "geometry": geometry, "thickness": method.CAT,
                 "twist_scale": 1., "holes": [], "screws": []}
        panels[body] = frame.panel_method.FinitePanelAdapter(panel, 500+75*i+np.arange(75), 9450)
        stock.append({"name": body, "volume_mm3": 10000.*method.CAT+i*1000., "center_of_mass_xyz_mm": [0., 50., 0.]})
    features = [{"identity": "hold_tnut_main_"+hold, "panel": body, "start_xyz_mm": [x, y, method.CAT/2.]}
        for hold, body, x, y in [("A12", "main_upper_left", -17., 71.),
            ("K12", "main_upper_right", 23., 61.), ("A1", "main_lower_left", -11., 19.)]]
    integrated = {"finished_stock": stock, "panel_machining": {"features": features}, "screw_axes": [],
                  "panel_operator_source_inputs": {"coupon": "current own panel data"}}
    case_loads = {}
    cases = {case["id"]: case for case in method.load_cases(integrated) if case["id"] in frame.component.SEQUENCE}
    for case_id, case in cases.items():
        rows = []
        for i, source in enumerate(stock):
            body = source["name"]
            rows.append({"id": "self-weight/"+body, "body": body, "point_xyz_mm": [0., 50., 0.],
                "force_xyz_n": [0., 0., -source["volume_mm3"]*500e-9*method.G]})
            rows.append({"id": "bolt-weight/"+body, "body": body, "point_xyz_mm": [13., 37., 4.],
                         "force_xyz_n": [0., 0., -.2-.01*i]})
            if body.startswith("main_upper_"):
                rows.append({"id": "accessory/"+body, "body": body,
                    "point_xyz_mm": [0., 71., -method.CAT/2.], "force_xyz_n": [0., 0., -12.5*method.G]})
            if case["hold"]["panel"] == body:
                x, y = case["hold"]["start_xyz_mm"][:2]
                rows.append({"id": "climber/"+body, "body": body,
                    "point_xyz_mm": [x, y, 100.+method.CAT/2.], "force_xyz_n": case["force_n"]})
        case_loads[case_id] = rows
    marker = tmp_path/"current-panel-source.json"
    marker.write_text("authenticated test current inputs\n")
    proof = {"current_own_projection_canonical_sha256": frame.canonical_sha(integrated),
             "source_sha256": {str(marker): frame.current.sha(marker)}}
    data = {"coupon_source": "owned"}
    calls = []
    def verified(supplied, supplied_proof):
        assert supplied == data and supplied_proof == proof
        calls.append(True)
    monkeypatch.setattr(frame.current, "verify_panel_source_inputs", verified)
    pins = frame.current.join(*[a.source_sha256 for a in panels.values()],
        {"scripts/thin_bolted_finite_panel_adapter.py": frame.current.sha(frame.current.ROOT/"scripts/thin_bolted_finite_panel_adapter.py")})
    load_class = frame.current_panel_load_class(data, integrated, proof, panels, case_loads, pins)
    assert calls == [True]
    return panels, integrated, cases, case_loads, proof, load_class, marker


def test_current_panel_gate_retains_genuine_six_case_loads_and_generalized_work(monkeypatch, tmp_path):
    panels, integrated, cases, case_loads, _proof, load_class, _marker = panel_recipe(monkeypatch, tmp_path)
    assert integrated != json.loads(frame.panel_method.method.INTEGRATED.read_text())
    for case_id in frame.component.SEQUENCE:
        loads = {body: load_class(a, cases[case_id], integrated, "original_top", case_loads[case_id]) for body, a in panels.items()}
        for body, load in loads.items():
            a = panels[body]
            q = np.zeros(9450); q[a.indices] = np.linspace(-.13, .21, a.local_size)
            result = load.external(q, True, reference=np.zeros(3))
            zero = load.external(np.zeros(9450), False)
            np.testing.assert_allclose(-zero["local_gradient_n"], load.corrected_reference_force_n, atol=1e-11, rtol=0.)
            assert abs(result["wrench_residual_n_nmm"]).max() < 1e-8
            rigid = a.current_rigid_modes(q, np.zeros(3))
            np.testing.assert_allclose(rigid.T @ -result["local_gradient_n"],
                result["physical_applied_wrench_n_nmm"]+result["generalized_correction_wrench_n_nmm"], atol=1e-8, rtol=0.)
            direction = np.zeros(9450); direction[a.indices] = np.sin(np.arange(a.local_size))
            direction /= np.linalg.norm(direction)
            h = 1e-3
            plus, minus = load.external(q+h*direction, False), load.external(q-h*direction, False)
            assert (plus["energy_nmm"]-minus["energy_nmm"])/(2.*h) == pytest.approx(result["gradient_n"] @ direction, abs=1e-7)
            np.testing.assert_allclose((plus["gradient_n"]-minus["gradient_n"])/(2.*h), result["hessian_csr"] @ direction, atol=1e-7, rtol=0.)
        assert sum(sum(r["force_xyz_n"][2] for r in load.loads) for load in loads.values()) == pytest.approx(
            -sum(r["volume_mm3"] for r in integrated["finished_stock"])*500e-9*frame.panel_method.method.G
            -25.*frame.panel_method.method.G-250.*2.*frame.panel_method.method.N_PER_LBF-sum(.2+.01*i for i in range(6)))


@pytest.mark.parametrize("failure", ["projection", "case", "accessory", "loads", "foreign_adapter", "source"])
def test_current_panel_gate_rejects_foreign_projection_loads_or_source(monkeypatch, tmp_path, failure):
    panels, integrated, cases, case_loads, _proof, load_class, marker = panel_recipe(monkeypatch, tmp_path)
    body = "main_upper_left"
    a, case, supplied, accessory, loads = panels[body], copy.deepcopy(cases["a12-forward"]), copy.deepcopy(integrated), "original_top", copy.deepcopy(case_loads["a12-forward"])
    if failure == "projection": supplied["finished_stock"][0]["volume_mm3"] += 1.
    if failure == "case": case["force_n"][0] += 1.
    if failure == "accessory": accessory = "proportional"
    if failure == "loads": loads[-1]["force_xyz_n"][2] += 1.
    if failure == "foreign_adapter": a = frame.panel_method.FinitePanelAdapter(a.panel, a.indices, a.ndof)
    if failure == "source": marker.write_text("changed current panel source\n")
    with pytest.raises(ValueError): load_class(a, case, supplied, accessory, loads)


def test_all_six_panels_join_mechanics_contact_and_heel_loads_with_separate_corrections(monkeypatch, tmp_path, methods):
    potential, _, _ = small_frame(methods)
    panels, integrated, cases, case_loads, _proof, load_class, _marker = panel_recipe(monkeypatch, tmp_path)
    case_id = "a12-forward"
    loads = {body: load_class(a, cases[case_id], integrated, "original_top", case_loads[case_id]) for body, a in panels.items()}
    screw = {"axis_id": "own-ring-screw", "panel": "main_upper_left", "receiver": "slave", "origin_xyz_mm": [13., 37., 0.]}
    panels[screw["panel"]].panel["screws"].append(screw)
    group = {"kind": "panel_screw", "axis_id": screw["axis_id"], "first": screw["panel"], "second": "slave",
        "point_xyz_mm": screw["origin_xyz_mm"], "basis": [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]], "ka": 1000., "kl": 500.}
    old = potential.generic
    generic = frame.finite.FiniteFramePotential(old.mechanics, panels, loads,
        old.interactions+frame.finite.describe_interactions([group], [], []), old.nonpanel_loads,
        case={"case_id": case_id, "state_id": "own-state", "accessory_placement": "original_top"},
        shaft_replacement=old.shaft_replacement)
    q = potential.q.copy()
    for a in panels.values(): q[a.indices] = np.linspace(-.013, .021, a.local_size)
    cached = potential.bedding.response(q, tangent=False)
    cached.pop("hessian_csr"); cached["gradient_n"] = cached["gradient_n"].tolist()
    complete = frame.CurrentFrame(generic, potential.bedding, potential.fittings,
        {**potential.binding, "case_id": case_id}, q, source_sha256=generic.source_sha256, cached_timber=cached)
    result = complete.diagnostic_response()
    assert result["owner_virtual_work_residual_inf_n_nmm"] < 1e-7
    assert len(result["owner_physical_action_wrenches_about_origin"]) == 11
    assert len(result["panel_generalized_load_corrections"]) == 12
    assert all(r["physical_point_forces_or_pressure_representation"] is False for r in result["panel_generalized_load_corrections"])
    expected = sum((np.asarray(r["force_xyz_n"]) for r in case_loads[case_id]), np.array([0., 0., -19.]))
    np.testing.assert_allclose(result["sum_owner_external_and_generalized_wrenches_about_origin"][:3], expected, atol=1e-8, rtol=0.)
    assert result["finite_equilibrium_established"] is False
    load = next(iter(complete.generic.panel_loads.values()))
    load.point_loads[0]["force_xyz_n"][2] -= 123.
    with pytest.raises(ValueError, match="fixed current frame sources changed"): complete.diagnostic_response()
    load.point_loads[0]["force_xyz_n"][2] += 123.
    generic.screw_by_id[screw["axis_id"]] = copy.deepcopy(screw)
    generic.screw_by_id[screw["axis_id"]]["origin_xyz_mm"][0] += 10.
    with pytest.raises(ValueError, match="own projected-ring screw routing differs"): complete.diagnostic_response()
    with pytest.raises(ValueError, match="own projected-ring screw routing differs"): complete.response(q, tangent=False)
    generic.screw_by_id[screw["axis_id"]] = screw
    load.adapter = copy.copy(load.adapter)
    with pytest.raises(ValueError, match="prepared adapter ownership differ"): complete.diagnostic_response()
    with pytest.raises(ValueError, match="prepared adapter ownership differ"): complete.response(q, tangent=False)


def test_heel_seed_uses_own_reference_and_transforms_objectively_without_warm_state(methods):
    potential, _, _ = small_frame(methods)
    fitting = next(iter(potential.fittings.fittings.values()))
    before = np.linspace(-.05, .09, 24).reshape(4, 6)
    before[:, 3:] *= 1000.
    heel = np.array([.1, -.2, .3, 110., -70., 90.])
    rotation, translation = Rotation.from_rotvec([.11, -.07, .09]).as_matrix(), np.array([7., -3., 13.])
    changed = before.copy()
    for i, row in enumerate(fitting.model.port_manifest):
        point = np.asarray(row["point_reference_xyz_mm"])
        changed[i, :3] = rotation @ (point+before[i, :3])+translation-point
        changed[i, 3:] = 1000.*Rotation.from_matrix(rotation @ Rotation.from_rotvec(before[i, 3:]/1000.).as_matrix()).as_rotvec()
    answer = frame.transported_seed(fitting, changed.ravel(), before.ravel(), heel)
    np.testing.assert_allclose(answer[:3]+fitting.model.origin,
        rotation @ (np.asarray(fitting.model.origin)+heel[:3])+translation, atol=1e-12, rtol=0.)
    np.testing.assert_allclose(Rotation.from_rotvec(answer[3:]/1000.).as_matrix(),
        rotation @ Rotation.from_rotvec(heel[3:]/1000.).as_matrix(), atol=1e-13, rtol=0.)
    np.testing.assert_array_equal(frame.transported_seed(fitting, before.ravel(), before.ravel(), heel), heel)
    different = before.copy(); different[1:, :3] += [.01, -.02, .03]
    np.testing.assert_array_equal(frame.transported_seed(fitting, different.ravel(), before.ravel(), heel), heel)


def rounded_panel():
    method = frame.panel_method.method
    axes = np.array([[1., 0., 0.], [0., .6427876096865393, .76604444291547],
        [0., .766044443118978, -.6427876099290709]])
    geometry = {"name": "main_upper_left", "origin": np.array([500., 600., 1700.]),
        "axes": axes, "inward": axes[:, 2], "front_height": 100.}
    panel = {"basis": method.SheetBasis(100., 100., 2), "geometry": geometry,
        "thickness": method.CAT, "twist_scale": 1., "holes": [], "screws": []}
    return frame.panel_method.FinitePanelAdapter(panel, 500+np.arange(75), 9450)


def test_derived_normal_keeps_source_plane_and_elasticity_but_restores_world_rigid_ports():
    panel = rounded_panel()
    original_geometry = copy.deepcopy(panel.geometry)
    original_axes = panel.axes.copy()
    q = np.zeros(9450); q[panel.indices] = np.linspace(-.13, .21, panel.local_size)
    point = panel.origin+original_axes[:, :2]@np.array([31., 43.])
    def port_error():
        port = panel.point_port(q, point, tangent=False)
        modes = panel.current_rigid_modes(q, np.zeros(3))
        projected = port["J_csr"][:, panel.indices]@modes
        expected = np.c_[np.eye(3), -frame.mechanical.skew(port["position_xyz_mm"])]
        return float(np.max(abs(projected-expected)))
    before_error = port_error()
    before = panel.response(q, True)
    record = frame.prepare_panel_embedding(panel)
    after = panel.response(q, True)
    assert before_error > 1e-7 and port_error() < 1e-9
    assert record["handedness"] == -1
    assert record["normal_difference_norm"] == pytest.approx(3.1660245e-10, rel=1e-7)
    assert record["reference_half_thickness_offset_change_bound_mm"] < 4e-9
    np.testing.assert_array_equal(panel.axes[:, :2], original_axes[:, :2])
    for key in original_geometry: np.testing.assert_array_equal(panel.geometry[key], original_geometry[key])
    assert before["energy_nmm"] == after["energy_nmm"]
    np.testing.assert_array_equal(before["gradient_n"], after["gradient_n"])
    assert (before["hessian_csr"] != after["hessian_csr"]).nnz == 0
    modes = panel.current_rigid_modes(q, np.zeros(3))
    np.testing.assert_allclose(modes.T@after["gradient_n"][panel.indices], np.zeros(6), atol=1e-8, rtol=0.)
    port = panel.point_port(q, point, tangent=False)
    np.testing.assert_allclose(port["normal_J_csr"][:, panel.indices]@modes,
        np.c_[np.zeros((3, 3)), -frame.mechanical.skew(port["normal_xyz"])], atol=1e-10, rtol=0.)
    with pytest.raises(ValueError, match="fresh panel"): frame.prepare_panel_embedding(panel)


@pytest.mark.parametrize("changed", ["plane", "runtime", "normal"])
def test_derived_normal_rejects_a_changed_plane_or_unbound_embedding(changed):
    panel = rounded_panel()
    if changed == "plane":
        angle = 1e-9
        panel.axes[:, 0] = [np.cos(angle), np.sin(angle), 0.]
    if changed == "runtime": panel.axes = panel.axes.copy(); panel.axes[0, 2] += 1e-10
    if changed == "normal": panel.axes[:, 2] *= 1.+1e-6
    with pytest.raises(ValueError): frame.prepare_panel_embedding(panel)


def complete_contact_recipe():
    partitions = {kind: [] for kind in ["groups", "contacts", "tangents"]}
    for kind, count in frame.preflight.CONTACT_COUNTS.items():
        for i in range(count):
            row = {"id": f"{kind}/{i}", "kind": kind, "first": "own-first", "second": "own-second",
                "point_xyz_mm": [17., 31., 43.], "direction_xyz": [0., 0., 1.], "stiffness": 7.}
            family = "contacts"
            if kind in ["common_shaft_bearing", "panel_screw"]:
                family = "groups"
                row.update(basis=np.eye(3).tolist(), kl=11., ka=13., clearance=.5, surface={})
            if kind == "flange_contact": row["flange"] = "arm-x/far-plus"
            if kind == "shaft_end_capture": row["end"] = {}
            if kind == "floor_tangent":
                family = "tangents"
                row["first"] = "lumber_leg_left" if i < 2 else ("lumber_leg_right" if i < 4 else "disabled-own-"+str(i))
                row["direction_xyz"] = np.eye(3)[i % 2].tolist()
            partitions[family].append({"descriptor": row})
    descriptors = [r["descriptor"] for family in ["groups", "contacts", "tangents"] for r in partitions[family]]
    floors = [{**r["descriptor"], "interaction_enabled": i < 4} for i, r in enumerate(partitions["tangents"])]
    return {"partitions": partitions}, {"reference_interaction_descriptors": copy.deepcopy(descriptors), "floor_actions": floors}


def test_current_source_census_keeps_32_normals_two_centroids_and_all_nonwood_contacts_once():
    bundle, field = complete_contact_recipe()
    rows, selection = frame.current_interactions(bundle, field)
    assert dict(frame.Counter(row["kind"] for row in rows)) == frame.INTERACTION_COUNTS
    assert not any(row["kind"] == "timber_face_contact" for row in rows)
    xy = [row for row in rows if row["kind"] == "floor_tangent_xy"]
    assert {r["first"] for r in xy} == {"lumber_leg_left", "lumber_leg_right"}
    assert {key for row in xy for key in row["source_component_ids"]} == {"floor_tangent/"+str(i) for i in range(4)}
    assert selection["enabled_centroid_XY_groups"] == 2
    normals = [row for row in rows if row["kind"] == "floor_normal"]
    assert [row["id"] for row in normals] == ["floor_normal/"+str(i) for i in range(32)]
    assert all(row["source_descriptor"] == next(r["descriptor"] for r in bundle["partitions"]["contacts"] if r["descriptor"]["id"] == row["id"]) for row in normals)


@pytest.mark.parametrize("failure", ["all_tangents", "missing_bearing", "wrong_source", "noncolocated_xy"])
def test_current_source_census_rejects_historical_or_changed_supports(failure):
    bundle, field = complete_contact_recipe()
    if failure == "all_tangents":
        for row in field["floor_actions"]: row["interaction_enabled"] = True
    if failure == "missing_bearing": bundle["partitions"]["groups"].pop(0)
    if failure == "wrong_source": field["reference_interaction_descriptors"][0]["kl"] += 1.
    if failure == "noncolocated_xy":
        bundle["partitions"]["tangents"][1]["descriptor"]["point_xyz_mm"][0] += 1.
        field["reference_interaction_descriptors"] = [copy.deepcopy(r["descriptor"]) for family in ["groups", "contacts", "tangents"] for r in bundle["partitions"][family]]
    with pytest.raises(ValueError): frame.current_interactions(bundle, field)


@pytest.mark.parametrize("preserved", [False, True])
def test_cached_complete_force_admission_keeps_all_six_sources_and_rejects_changed_semantics(monkeypatch, tmp_path, methods, preserved):
    if preserved:
        preserved_force_fixture(monkeypatch, tmp_path, methods[0])
        result = frame.timber.reexport_preserved()
    else:
        current_force_fixture(monkeypatch, tmp_path, methods[0])
        result = frame.timber.run()
    raw = tmp_path/"complete-force.json"
    potential, poses, _ = frame.timber.prepare_current()
    monkeypatch.setattr(frame, "TIMBER_PRODUCER", frame.timber.own_ref())
    def write(value):
        raw.write_text(json.dumps(value))
        monkeypatch.setattr(frame, "TIMBER_EVIDENCE", frame.current.ref(raw))
    write(result)
    assert frame.cached_timber_evidence(potential, poses) == result
    for failure in ["producer", "schema", "source_closure", "law_closure", "case", "source_status", "unscoped_status",
                    "q", "samples", "descriptor", "rows", "branches", "gradient", "owners", "accepted", "neighbor"]:
        bad = copy.deepcopy(result)
        row = bad["cases"][4]
        if failure == "producer": bad["producer"]["sha256"] = "foreign"
        if failure == "schema": bad["schema"] = "eoere_current_reference_material_timber_bedding/v1"
        if failure == "source_closure": bad["source_sha256"].pop(next(iter(bad["source_sha256"])))
        if failure == "law_closure": bad["force_law_source_sha256"] = {}
        if failure == "case": row["state_id"] = "foreign"
        if failure == "source_status": row["saved_first_order_source"]["gradient_inf_n"] += 1.
        if failure == "unscoped_status": row["current_equilibrium_and_recovery_pass"] = True
        if failure == "q": row["final_q_canonical_sha256"] = "foreign"
        if failure == "samples": bad["fixed_samples"][-1]["reference_area_mm2"] += 1.
        if failure == "descriptor": row["fixed_sample_descriptor_sha256"] = "foreign"
        if failure == "rows": row["sample_rows"][-1][0] = 0
        if failure == "branches": row["branch_counts"]["closed"] += 1
        if failure == "gradient": row["gradient_n"][1] = float("nan")
        if failure == "owners": row["owner_wrenches_at_world_origin"].pop(next(iter(potential.maps)))
        if failure == "accepted": bad["structural_acceptance"] = True
        if failure == "neighbor": row["trial_scope"]["remaining_possible_new_neighbor_count"] = 1
        write(bad)
        with pytest.raises(ValueError): frame.cached_timber_evidence(potential, poses)
    write(result)
    genuine, count = frame.canonical_sha, [0]
    def late(value):
        if value == poses[-1][1].tolist():
            count[0] += 1
            raw.write_bytes(raw.read_bytes()+b" ")
        return genuine(value)
    monkeypatch.setattr(frame, "canonical_sha", late)
    with pytest.raises(ValueError): frame.cached_timber_evidence(potential, poses)
    assert count == [1]


def test_frame_source_drift_is_rejected_before_any_contact_query(monkeypatch, tmp_path, methods):
    old, _, _ = small_frame(methods)
    source = tmp_path/"owned-frame-input.json"
    source.write_text("owned frame data\n")
    potential = frame.CurrentFrame(old.generic, old.bedding, old.fittings, old.binding, old.q,
        source_sha256={str(source): frame.current.sha(source)}, cached_timber=old.cached_timber)
    source.write_text("changed before any query\n")
    def forbidden(*_args, **_kwargs): raise AssertionError("changed source reached a contact query")
    monkeypatch.setattr(potential.bedding, "response", forbidden)
    with pytest.raises(ValueError): potential.response(potential.q, tangent=False)


def orchestration_recipe(monkeypatch, tmp_path, *, late=False):
    """Control source handoffs; component numerical kernels have separate coupons."""
    monkeypatch.setattr(frame.current, "ROOT", tmp_path)
    monkeypatch.setattr(frame.current, "manifest", lambda: {"release": {"accepted": False}})
    producer = tmp_path/"current-frame.py"
    producer.write_text("orchestration producer\n")
    monkeypatch.setattr(frame, "OWN", producer)
    monkeypatch.setattr(frame, "LOADED_SHA", frame.current.sha(producer))
    dependencies = {}
    for name in ["execution", "timber", "force", "router", "panel"]:
        path = tmp_path/(name+"-only.json")
        path.write_text(name+" source\n")
        dependencies[name] = frame.current.ref(path)
    def pin(name):
        ref = dependencies[name]
        return {ref["path"]: ref["sha256"]}
    timber_names = [f"timber/{i:02d}" for i in range(22)]
    shafts = [{"body": f"shaft/{99-i:03d}"} for i in range(100)]
    fitting_names = [f"fitting/{i:02d}" for i in range(22)]
    fitting_poses = [{"id": body} for body in fitting_names]
    source_panels = {}
    panel_charts = {}
    for i, body in enumerate(frame.panel_method.method.PANELS):
        geometry = {"name": body, "fixture_origin": [i, 0., 0.]}
        source_panels[body] = {"geometry": geometry, "K": np.ones((1, 1)), "thickness": 18.}
        panel_charts[body] = {"indices": [528+i], "geometry": geometry, "width_mm": 100., "height_mm": 200.,
            "basis_order_per_direction": 4, "knots_normalized": [0., 1.], "thickness_mm": 18.}
    chart = {"final_ndof": 9350, "unused_legacy_two_port_fitting_indices": {},
        "four_port_fittings": {body: {"indices": list(range(24*i, 24*i+24))} for i, body in enumerate(fitting_names)},
        "panels": panel_charts}
    reference = eye(9350, format="csr")
    bank = tmp_path/"source-operators.npz"
    np.savez(bank, kdata=reference.data, kindices=reference.indices, kindptr=reference.indptr)
    array_ref = frame.current.ref(bank)
    fields, bundles, poses, expected, cached = [], [], [], [], []
    for i, case_id in enumerate(frame.component.SEQUENCE):
        loads = []
        for body in timber_names:
            loads.append({"id": "self-weight/"+body, "body": body, "point_xyz_mm": [50., 0., 0.], "force_xyz_n": [0., 0., -3.]})
            loads.extend({"id": "metal-weight/"+body+"/"+str(j), "body": body,
                "point_xyz_mm": [31., 2., 3.], "force_xyz_n": [0., 0., -.1]} for j in range(3))
        for body in fitting_names:
            loads.append({"id": "self-weight/"+body, "body": body, "point_xyz_mm": [10., 20., 30.], "force_xyz_n": [0., 0., -.3]})
        for j, source in enumerate(shafts):
            loads.extend({"id": "metal-weight/"+source["body"]+"/"+str(k), "body": source["body"],
                "point_xyz_mm": [j, 0., 0.], "force_xyz_n": [0., 0., -.02]} for k in range(5+(j < 8)))
        for j, body in enumerate(source_panels):
            loads.extend({"id": "panel-load/"+body+"/"+str(k), "body": body, "point_xyz_mm": [0., 0., 0.],
                "force_xyz_n": [0., 0., -100.*(i+1) if j == k == 0 else -.01]} for k in range(36+(j == 0)))
        assert len(loads) == len({r["id"] for r in loads}) == 835
        q = np.zeros(9450); q[0] = i+1
        source_inputs = {"scenario": {"numerical_case": "fixed"}, "shafts": shafts, "fitting_poses": fitting_poses}
        field = {"source_inputs": source_inputs, "body_applied_loads": loads, "original_operator_fingerprint_sha256": "source-operator"}
        bundle = {"coordinate_map": chart, "original_operator_fingerprint_sha256": "source-operator",
            "case": {"case_id": case_id, "loads": loads, "primary_load_basis": True, "accessory_placement": "original_top"},
            "arrays": array_ref, "K": {"storage": "csr", "data": "kdata", "indices": "kindices", "indptr": "kindptr", "shape": [9350, 9350]}}
        bundle_path, field_path = tmp_path/f"bundle-{i}.json", tmp_path/f"field-{i}.json"
        bundle_path.write_text(json.dumps(bundle))
        field["operator_bundle"] = {"manifest": frame.current.ref(bundle_path)}
        field_path.write_text(json.dumps(field))
        binding = {"case_id": case_id, "state_id": f"own-state-{i}", "field": frame.current.ref(field_path),
            "gradient_inf_n": 1e-9, "current_equilibrium_and_recovery_pass": True}
        poses.append((binding, q, {}, {})); fields.append(field); bundles.append(bundle)
        expected.append(-sum(r["force_xyz_n"][2] for r in loads))
        cached.append({"case_id": case_id, "final_q_canonical_sha256": frame.canonical_sha(q.tolist())})
    execution = {p.name: frame.current.sha(p) for p in tmp_path.iterdir() if p.is_file()
                 and p.name not in [dependencies[name]["path"] for name in ["timber", "force", "router", "panel"]]}
    monkeypatch.setattr(frame, "execution_pins", lambda: execution)
    charts = {body: {"owner": body, "fixture": "own kinematics"} for body in timber_names}
    bedding = SimpleNamespace(source_sha256=pin("timber"), charts=charts)
    monkeypatch.setattr(frame.timber, "prepare_current", lambda: (bedding, poses, {}))
    def cached_evidence(potential, received):
        assert potential is bedding and received is poses
        return {"source_sha256": pin("force"), "cases": cached}
    monkeypatch.setattr(frame, "cached_timber_evidence", cached_evidence)
    method_a, method_b = object(), object()
    def load_method(ref, name):
        if ref == frame.preflight.PARTITION: return method_a
        assert ref == frame.precision.METHOD
        return method_b
    monkeypatch.setattr(frame.component, "load", load_method)
    calls = {"partition": [], "panel_loads": [], "generic": [], "fitting_gravity": [], "prepared": [], "evaluated": []}
    def partition(method, received_chart, loads, received_shafts):
        assert method is method_a and received_chart == chart and received_shafts == shafts
        family = frame.Counter("timber" if r["body"] in timber_names else "fitting" if r["body"] in fitting_names
            else "panel" if r["body"] in source_panels else "shaft" for r in loads)
        assert family == {"timber": 88, "fitting": 22, "shaft": 508, "panel": 217}
        calls["partition"].append(loads)
    monkeypatch.setattr(frame.preflight, "current_partition", partition)
    assembly = SimpleNamespace(members={body: {"stations": np.array([0., 100.]), "start": np.zeros(3), "axis": np.array([1., 0., 0.])} for body in timber_names})
    base = SimpleNamespace(ndof=9450, members=assembly.members, shafts={s["body"]: s for s in shafts})
    replacement = object()
    def restore(received, scenario, received_shafts, matrix, *, source_sha256):
        assert received == chart and scenario == {"numerical_case": "fixed"} and received_shafts == shafts
        assert (matrix != reference).nnz == 0 and source_sha256 == frame.current.join(execution, pin("timber"), pin("force"))
        return assembly, base, replacement, [{"body": f"checked/{i}", "relative_reference_block_error": 0.} for i in range(122)]
    monkeypatch.setattr(frame, "restore_mechanics", restore)
    def prepare_fitting(method, pose, descriptor, *, full_ndof):
        assert method is method_b and full_ndof == 9450 and descriptor == chart["four_port_fittings"][pose["id"]]
        index = np.asarray(descriptor["indices"])
        return SimpleNamespace(body=pose["id"], element=SimpleNamespace(elastic_block=lambda: (index, np.eye(24))))
    monkeypatch.setattr(frame.precision, "prepare_current_fitting", prepare_fitting)
    router = SimpleNamespace(source_sha256=pin("router"), members=base.members)
    def router_factory(received_base, fittings, ma, mb, pins):
        assert received_base is base and set(fittings) == set(fitting_names) and ma is method_a and mb is method_b
        return router
    monkeypatch.setattr(frame, "four_port_router", router_factory)
    integrated = {"panel_machining": {"features": [{"identity": "hold_tnut_main_"+hold, "panel": "main_upper_left"} for hold in ["A12", "K12", "A1"]]}}
    proof = {"source_sha256": pin("panel")}
    def panel_dependencies(data):
        assert data == fields[0]["source_inputs"]
        return source_panels, integrated, pin("panel"), proof
    monkeypatch.setattr(frame.current, "load_panel_dependencies", panel_dependencies)
    def verify_panel(data, received):
        assert data == fields[0]["source_inputs"] and received is proof
    monkeypatch.setattr(frame.current, "verify_panel_source_inputs", verify_panel)
    panels = {body: SimpleNamespace(geometry=row["geometry"], basis=SimpleNamespace(width=100., height=200., order=4, knots=np.array([0., 1.])),
        indices=np.asarray(panel_charts[body]["indices"]), panel=row) for body, row in source_panels.items()}
    def panel_adapters(raw, offsets, ndof, pins):
        assert raw is source_panels and ndof == 9450
        assert all(np.array_equal(offsets[b], panels[b].indices) for b in panels)
        return panels
    monkeypatch.setattr(frame.panel_method, "prepare_adapters", panel_adapters)
    def embedding(panel):
        assert panel is panels[panel.geometry["name"]]
        return {"own_panel": panel.geometry["name"], "source_midsurface_and_local_xy_unchanged": True}
    monkeypatch.setattr(frame, "prepare_panel_embedding", embedding)
    def mapping(received, received_panels):
        assert received is router and received_panels is panels
        return {"mechanical_bodies": charts}
    monkeypatch.setattr(frame.finite, "kinematic_map", mapping)
    def load_class(data, projection, received, received_panels, case_loads, pins):
        assert data == fields[0]["source_inputs"] and projection is integrated and received is proof and received_panels is panels
        assert case_loads == {case: field["body_applied_loads"] for case, field in zip(frame.component.SEQUENCE, fields, strict=True)}
        class Loads:
            def __init__(self, panel, case, supplied, accessory, body_loads):
                assert supplied is integrated and accessory == "original_top" and body_loads == case_loads[case["id"]]
                self.loads = [row for row in body_loads if row["body"] == panel.geometry["name"]]
                calls["panel_loads"].append((case["id"], panel.geometry["name"]))
        return Loads
    monkeypatch.setattr(frame, "current_panel_load_class", load_class)
    def interactions(bundle, field):
        assert bundle["case"]["loads"] == field["body_applied_loads"]
        return [{"own_case": bundle["case"]["case_id"]}], {"enabled_centroid_XY_groups": 2}
    monkeypatch.setattr(frame, "current_interactions", interactions)
    def generic(received, received_panels, panel_loads, interaction_rows, nonpanel, *, case, source_sha256, shaft_replacement):
        case_id = case["case_id"]; i = frame.component.SEQUENCE.index(case_id)
        assert received is router and received_panels is panels and shaft_replacement is replacement
        assert case["state_id"] == poses[i][0]["state_id"] and interaction_rows == [{"own_case": case_id}]
        assert len(nonpanel) == 618 and not any(r["body"] in fitting_names or r["body"] in panels for r in nonpanel)
        for body in timber_names:
            own = [r for r in nonpanel if r["source_load_id"] == "self-weight/"+body]
            assert len(own) == 2
            np.testing.assert_allclose(sum(np.asarray(r["force_xyz_n"]) for r in own), [0., 0., -3.], atol=1e-14)
            np.testing.assert_allclose(sum(np.cross(r["point_xyz_mm"], r["force_xyz_n"]) for r in own), [0., 150., 0.], atol=1e-12)
        calls["generic"].append(case_id)
        return SimpleNamespace(case=case, source_sha256=source_sha256)
    monkeypatch.setattr(frame.finite, "FiniteFramePotential", generic)
    def loaded(fittings, field, pins):
        assert set(fittings) == set(fitting_names)
        rows = [r for r in field["body_applied_loads"] if r["body"] in fittings]
        assert len(rows) == len({r["body"] for r in rows}) == 22
        calls["fitting_gravity"].append(rows)
        return SimpleNamespace(loads=rows)
    monkeypatch.setattr(frame, "LoadedFittings", loaded)
    class RecordedFrame:
        def __init__(self, generic, received_bedding, fitting_loads, binding, q, *, source_sha256, cached_timber):
            i = frame.component.SEQUENCE.index(binding["case_id"])
            assert received_bedding is bedding and np.array_equal(q, poses[i][1]) and cached_timber == cached[i]
            assert generic.case["state_id"] == binding["state_id"] and len(fitting_loads.loads) == 22
            assert source_sha256 == frame.current.join(execution, *[pin(name) for name in ["timber", "force", "router", "panel"]])
            self.binding, self.i = binding, i
            calls["prepared"].append(binding["case_id"])
        def diagnostic_response(self):
            calls["evaluated"].append(self.binding["case_id"])
            if late and len(calls["evaluated"]) == 6:
                path = tmp_path/dependencies["force"]["path"]
                path.write_text("changed after final response\n")
            gradient = np.zeros(9450); gradient[0] = expected[self.i]
            return {**frame.timber.case_source(self.binding), "energy_nmm": expected[self.i], "gradient_n": gradient,
                "hessian_csr": None, "signed_gradient_inf_n": expected[self.i], "owner_virtual_work_residual_inf_n_nmm": 0.}
    monkeypatch.setattr(frame, "CurrentFrame", RecordedFrame)
    return calls, expected, frame.current.join(execution, *[pin(name) for name in ["timber", "force", "router", "panel"]])


@pytest.mark.parametrize("late", [False, True])
def test_complete_preparation_and_export_route_every_current_case_and_verify_final_sources(monkeypatch, tmp_path, late):
    calls, expected, pins = orchestration_recipe(monkeypatch, tmp_path, late=late)
    progress = []
    if late:
        with pytest.raises(ValueError): frame.run(progress=progress.append)
    else:
        result = frame.run(progress=progress.append)
        assert [row["case_id"] for row in result["cases"]] == frame.component.SEQUENCE
        assert [row["energy_nmm"] for row in result["cases"]] == expected
        assert [row["state_id"] for row in result["cases"]] == [f"own-state-{i}" for i in range(6)]
        assert all(not {"gradient_inf_n", "current_equilibrium_and_recovery_pass"} & row.keys() for row in result["cases"])
        assert result["source_sha256"] == pins and len(result["reference_block_checks"]) == 150
        assert result["full_ndof"] == 9450 and result["complete_current_source_model_composed"] is True
        assert result["panel_runtime_embeddings"] == {body: {"own_panel": body,
            "source_midsurface_and_local_xy_unchanged": True} for body in frame.panel_method.method.PANELS}
        assert result["equilibrium_solve_native_FEA_geometry_change_or_strength_acceptance"] is False
    assert calls["generic"] == calls["prepared"] == calls["evaluated"] == frame.component.SEQUENCE
    assert len(calls["partition"]) == len(calls["fitting_gravity"]) == len(progress) == 6
    assert len(calls["panel_loads"]) == 36 and len(set(calls["panel_loads"])) == 36
