"""Actual finite serializer, physical-space replay, and admission mutations."""

import importlib.util
import json
from copy import deepcopy
from functools import lru_cache
from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import thin_bolted_finite_state_audit as audit


def actual_export():
    spec = importlib.util.spec_from_file_location("finite_composition_fixture", Path(__file__).with_name("test_thin_bolted_finite_frame.py"))
    fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
    potential, _, _ = fixture.small_potential()
    for i in range(32):
        point = [float(i), 0., 0.]
        normal = fixture.descriptor("coupon/floor-" + str(i), "floor_normal", "timber", "floor", point,
            [0., 0., 1.], "floor", axial=25000., sign=-1.)
        tangent = fixture.descriptor(normal["id"] + "/finite-no-slip-xy", "floor_tangent_xy", "timber", "floor", point,
            [0., 0., 1.], "floor", lateral=25000.)
        tangent.update(floor_support_id=normal["id"], normal_contact_id=normal["id"])
        potential.interactions.extend((normal, tangent))
    q = np.zeros(potential.ndof)
    # Nonzero rigid rotation and translation on only one body exercises the
    # actual material-director couples instead of the trivial reference state.
    index = potential.map["mechanical_bodies"]["timber"]["node_dof_indices"]
    for node in index:
        q[np.asarray(node)[3:]] = [20., -30., 40.]
        q[np.asarray(node)[:3]] = [.03, -.02, -.1]
    normal_ids = [r["id"] for r in potential.interactions if r["kind"] == "floor_normal"]
    first = potential.response(q, False, recover_actions=True)
    disabled = [key for key, value in first["floor_normal_reactions_n"].items() if value <= 1e-7]
    result = potential.response(q, False, recover_actions=True, disabled_floor_support_ids=disabled)
    field = {**potential.case, "response": {"disabled_floor_support_ids": disabled},
        "finite_kinematic_map": result["finite_kinematic_map"], "reference_interaction_descriptors": result["reference_interaction_descriptors"],
        "finite_interaction_actions": result["finite_interaction_actions"]}
    assert len(normal_ids) == 32
    expected = {r["id"]: deepcopy(r) for r in potential.interactions}
    return field, q, expected


def test_actual_frozen_serializer_current_actions_and_couples_replay():
    field, q, expected = actual_export()
    receipt = audit.verify_current_actions(field, q, expected)
    assert receipt["counts"]["floor_normal"] == receipt["counts"]["floor_tangent_xy"] == 32
    assert receipt["maximum_current_pair_moment_residual_nmm"] < 1e-8
    assert receipt["own_corner_activation_authenticated"]


@pytest.mark.parametrize("mutation", ["point", "force", "dual", "director", "couple", "law", "source", "identity", "missing", "activation"])
def test_actual_export_mutations_are_rejected(mutation):
    field, q, expected = actual_export()
    row = field["finite_interaction_actions"][0]
    if mutation == "point":
        row["point_on_first_xyz_mm"][0] += .01
    elif mutation == "force":
        row["force_on_first_xyz_n"][0] += 1.
    elif mutation == "dual":
        row["force_on_second_xyz_n"][0] += 1.
    elif mutation == "director":
        row["current_director_xyz"][0] += .01
    elif mutation == "couple":
        row["moment_on_second_at_current_point_xyz_nmm"][0] += 1.
    elif mutation == "law":
        row["lateral_stiffness_n_mm"] *= 2.
    elif mutation == "source":
        expected[row["id"]]["source_descriptor"] = {"axis_id": "correct-axis"}
        row["source_descriptor"] = {"axis_id": "different-axis"}
    elif mutation == "identity":
        row["case_id"] = "different-case"
    elif mutation == "missing":
        field["finite_interaction_actions"].pop()
    else:
        field["response"]["disabled_floor_support_ids"] = [] if field["response"]["disabled_floor_support_ids"] else ["coupon/floor-0"]
    with pytest.raises(ValueError):
        audit.verify_current_actions(field, q, expected)


def test_reference_plane_subtraction_and_same_point_force_couple_known_answer():
    law = {"axial_sign": -1., "reference_axial_projection_mm": -4., "axial_stiffness_n_mm": 100.,
           "lateral_stiffness_n_mm": 0., "radial_gap_mm": 0., "axial_tension_only": True}
    F, M, extension, _, tension, energy = audit.replay_constitutive(law, [3., 0., 0.], [0., 0., 0.], [1., 0., 0.])
    np.testing.assert_allclose(F, [100., 0., 0.]); np.testing.assert_allclose(M, 0.)
    assert extension == 1. and tension == 100. and energy == 50.
    F, M, *_ = audit.replay_constitutive(law, [4., 0., 0.], [0., 0., 0.], [1., 0., 0.])
    np.testing.assert_array_equal(F, 0.); np.testing.assert_array_equal(M, 0.)


def test_current_wrench_balance_includes_separate_generalized_panel_correction():
    point = [31., -23., 17.]
    force = [3., -7., 11.]
    load = {"body": "panel", "current_point_xyz_mm": point, "force_xyz_n": force, "free_spatial_moment_xyz_nmm": [0., 0., 0.]}
    W = audit.arithmetic.wrench(force, point, audit.REFERENCE)
    correction = {"panel": "panel", "wrench_reference_xyz_mm": audit.REFERENCE.tolist(), "current_equivalent_rigid_wrench_n_nmm": (-W).tolist()}
    residuals, applied, global_value = audit.current_balances(["panel"], [load], [], [correction])
    np.testing.assert_allclose(residuals["panel"], 0.); np.testing.assert_allclose(applied, 0.); np.testing.assert_allclose(global_value, 0.)


def test_discrete_timber_gravity_preserves_source_mass_and_first_moment():
    field = {"finite_kinematic_map": {"mechanical_bodies": {"member": {"kind": "timber",
        "reference_axis_xyz": [1., 0., 0.], "reference_start_xyz_mm": [10., 20., 30.], "reference_stations_mm": [0., 40., 100.]}}}}
    loads = [{"id": "self-weight/member", "body": "member", "point_xyz_mm": [65., 22., 33.], "force_xyz_n": [0., 0., -100.]}]
    rows = audit.expected_finite_loads(field, loads)
    assert len(rows) == 4
    exact = audit.arithmetic.wrench(loads[0]["force_xyz_n"], loads[0]["point_xyz_mm"], [0., 0., 0.])
    actual = sum((audit.arithmetic.wrench(r["force_xyz_n"], r["point_xyz_mm"], [0., 0., 0.]) for r in rows), np.zeros(6))
    np.testing.assert_allclose(actual, exact, atol=1e-10)


@pytest.mark.parametrize("source", ["compatible-common-shaft-a12-rear-v4.json", "compatible-common-shaft-a12-rear-incremental-v4.json",
                                   "compatible-frame-a12-rear-finished-floor-v4.json"])
def test_preserved_reference_or_failed_experiments_cannot_enter_finite_gate(source):
    with pytest.raises(ValueError, match="finite-current outer schema"):
        audit.audit_finite_state(audit.PACKET / source)


@lru_cache(maxsize=1)
def complete_reference_geometry():
    """Pure JSON/basis preparation; selects no old q/actions/K or response."""
    contact, cache, unit, layout, takeoff, integrated, _ = audit.common.read_sources()
    shafts = audit.common_method.shaft_inputs(layout, unit, cache)
    spans = audit.member_geometry.read_member_span_geometry()
    mechanical, panels = {}, {}
    offset = 0
    for name, span in spans.items():
        start, end = np.asarray(span["start_xyz_mm"]), np.asarray(span["end_xyz_mm"])
        length = np.linalg.norm(end-start)
        stations = np.linspace(0., length, int(np.ceil(length/150.))+1)
        index = np.arange(offset, offset+6*len(stations)).reshape(-1, 6); offset += index.size
        axis = np.asarray(span["basis_grain_u_v_xyz"][0])
        mechanical[name] = {"kind": "timber", "node_reference_centers_xyz_mm": (start+stations[:, None]*axis).tolist(),
            "node_dof_indices": index.tolist(), "storage_basis_columns_xyz": np.eye(3).tolist(),
            "reference_start_xyz_mm": start.tolist(), "reference_axis_xyz": axis.tolist(), "reference_stations_mm": stations.tolist()}
    for fitting in layout["raw_fittings"]:
        points = {r["flange"]: r["entry_xyz_mm"] for r in fitting["holes"]}
        index = np.arange(offset, offset+12).reshape(2, 6); offset += 12
        mechanical[fitting["angle_id"]] = {"kind": "fitting", "node_reference_centers_xyz_mm": [points["beam"], points["post"]],
            "node_dof_indices": index.tolist(), "storage_basis_columns_xyz": np.eye(3).tolist(),
            "flange_node_map": {"beam": 0, "post": 1}, "gravity_port": "mean of two exact flange rigid-arm ports"}
    geometry = {r["panel"]: r for r in json.loads(audit.panel_datums.ASSESSMENT.read_text())["panel_geometry"]}
    datums = json.loads(audit.panel_datums.DATUMS.read_text())
    for name in audit.panel_method.PANELS:
        source, datum = geometry[name], datums[name]
        basis = audit.panel_method.SheetBasis(source["width_mm"], source["height_mm"], 8)
        geo = {"name": name, "origin": np.asarray(datum["origin_xyz_mm"]), "axes": np.asarray(datum["local_axes_columns_xyz"]),
               "front_height": source["front_height_mm"]}
        holes = [{**r, "xy_mm": audit.panel_method.local_xy(r["start_xyz_mm"], geo).tolist()}
            for r in integrated["panel_machining"]["features"] if r["panel"] == name]
        p = {"basis": basis, "geometry": geo, "holes": holes, "thickness": audit.panel_method.CAT, "twist_scale": 1.}
        audit.panel_loads.mass_only_quadrature(p)
        index = np.arange(offset, offset+3*basis.size); offset += len(index)
        panels[name] = {"kind": "panel", "global_dof_indices": index.tolist(), "origin_xyz_mm": geo["origin"].tolist(),
            "axes_columns_xyz": geo["axes"].tolist(), "thickness_mm": audit.panel_method.CAT, "twist_scale": 1.,
            "basis_width_mm": basis.width, "basis_height_mm": basis.height, "basis_order": basis.order,
            "basis_knots_normalized": basis.knots.tolist(), "mass_reference_xy_mm": (p["mass_weights"] @ p["mass_xy"]).tolist(),
            "mass_coefficient_row": p["mass_row"].tolist()}
    for shaft in shafts:
        events = set(shaft["shaft_interval_mm"])
        for surface in shaft["surfaces"]:
            a, b = surface["interval_mm"]; events.update((a, .5*(a+b), b))
        for end in shaft["ends"]:
            events.update((end["support_s_mm"], end["pressure_face_s_mm"]))
        coarse = []
        for value in sorted(events):
            if not coarse or value-coarse[-1] > 1e-6:
                coarse.append(value)
        stations = []
        for a, b in pairwise(coarse):
            stations.extend(np.linspace(a, b, max(1, int(np.ceil((b-a)/25.)))+1)[:-1])
        stations.append(coarse[-1]); stations = np.asarray(stations)
        index = np.arange(6*len(stations)).reshape(-1, 6); index[0, 3] = -1
        keep = index >= 0; index[keep] = np.arange(offset, offset+keep.sum()); offset += int(keep.sum())
        mechanical[shaft["body"]] = {"kind": "shaft", "node_reference_centers_xyz_mm": (shaft["point"]+stations[:, None]*shaft["basis"][0]).tolist(),
            "node_dof_indices": index.tolist(), "storage_basis_columns_xyz": shaft["basis"].T.tolist(),
            "reference_start_xyz_mm": shaft["point"].tolist(), "reference_axis_xyz": shaft["basis"][0].tolist(), "reference_stations_mm": stations.tolist()}
    for shaft in shafts:
        mechanical[shaft["body"]]["node_dof_indices"][0][3] = offset; offset += 1
    params = {"panel_intervals": 8, "foundation_port_cell_mm": 70., "beam_size_mm": 150., "shaft_max_segment_mm": 25.,
        "wood_radial_foundation_n_mm2": 1000/38.1, "plate_radial_foundation_n_mm2": 10000/5.55625,
        "end_capture_stiffness_n_mm": 1000., "Hillman_axial_lateral_stiffness_n_mm": 1000.,
        "flange_corner_contact_n_mm": 10000., "panel_foundation_n_mm3": 2., "floor_corner_contact_n_mm": 25000.,
        "floor_no_slip_xy_penalty_n_mm_per_foot": 100000., "floor_xy_penalty_n_mm_per_corner": 25000.}
    field = {"case_id": "a12-rear", "accessory_placement": "retained-original-top-hold", "parameters": params,
        "finite_kinematic_map": {"ndof": offset, "mechanical_bodies": mechanical, "panels": panels}}
    return field, np.zeros(offset), contact, cache, unit, layout, takeoff, integrated, shafts


def test_complete_source_geometry_and_initial_contact70_census_without_CAD_or_K():
    field, q, contact, _, _, layout, _, integrated, shafts = deepcopy(complete_reference_geometry())
    panels, datums = audit.verify_maps(field, q, layout, shafts, integrated)
    expected = audit.descriptor_expected(field, contact, layout, shafts, panels, datums)
    counts = audit.Counter(r["kind"] for r in expected.values())
    assert counts == {"common_shaft_bearing": 308, "shaft_end_capture": 140, "flange_contact": 288,
                      "panel_screw": 66, "panel_contact": 530, "floor_normal": 32, "floor_tangent_xy": 32}
    assert len(q) == 8088


@pytest.mark.parametrize("mutation", ["floor-recess", "shaft-basis", "missing-twist", "panel-origin", "panel-mass", "shaft-span", "fitting-gravity-port"])
def test_complete_map_geometry_mutations_reject(mutation):
    field, q, _, _, _, layout, _, integrated, shafts = deepcopy(complete_reference_geometry())
    mechanical, panels = field["finite_kinematic_map"]["mechanical_bodies"], field["finite_kinematic_map"]["panels"]
    shaft = next(r for r in mechanical.values() if r["kind"] == "shaft")
    panel = next(iter(panels.values()))
    if mutation == "floor-recess":
        mechanical["base_post_outer_left"]["reference_start_xyz_mm"][0] += .1
    elif mutation == "shaft-basis":
        shaft["storage_basis_columns_xyz"][0][0] += .01
    elif mutation == "missing-twist":
        shaft["node_dof_indices"][0][3] = shaft["node_dof_indices"][0][4]
    elif mutation == "panel-origin":
        panel["origin_xyz_mm"][0] += .01
    elif mutation == "panel-mass":
        panel["mass_coefficient_row"][0] += .01
    elif mutation == "shaft-span":
        shaft["reference_stations_mm"][-1] += .01
    else:
        next(r for r in mechanical.values() if r["kind"] == "fitting")["gravity_port"] = "unsupported own flange sharing"
    with pytest.raises(ValueError):
        audit.verify_maps(field, q, layout, shafts, integrated)


@lru_cache(maxsize=1)
def actual_source_load_export():
    """Actual frozen load serializer at reference q, without any response solve."""
    field, q, _, cache, _, layout, takeoff, integrated, shafts = deepcopy(complete_reference_geometry())
    field["state_id"] = "unconverged-source-load-coupon"
    panels, _ = audit.verify_maps(field, q, layout, shafts, integrated)
    bodies, source, _ = audit.common.expected_common_loads(field, cache, takeoff, integrated)
    expanded = audit.expected_finite_loads(field, source)
    mechanical = []
    for row in expanded:
        if row["body"] in panels:
            continue
        current = audit.finite.current_pose_from_map(field["finite_kinematic_map"], row["body"], row["point_xyz_mm"], q)["position_xyz_mm"]
        mechanical.append({**row, "reference_point_xyz_mm": row["point_xyz_mm"], "current_point_xyz_mm": current.tolist(),
            "free_spatial_moment_xyz_nmm": [0., 0., 0.]})
    adapters, loads = {}, {}
    case = next(r for r in audit.panel_method.load_cases(integrated) if r["id"] == field["case_id"])
    for name, panel in panels.items():
        adapters[name] = audit.light_panel_adapter(panel, field["finite_kinematic_map"]["panels"][name], len(q))
        owned = [r for r in source if r["body"] == name]
        loads[name] = audit.panel_finite.FinitePanelLoads(adapters[name], case, integrated, "original_top", owned)
    holder = SimpleNamespace(panels=adapters, panel_loads=loads)
    panel_rows, corrections = [], []
    for name in panels:
        external = loads[name].external(q, False, audit.REFERENCE)
        rows, delta = audit.finite.FiniteFramePotential.panel_load_actions(holder, name, q, external)
        panel_rows.extend(rows); corrections.extend(delta)
    field["finite_body_applied_loads"] = mechanical+panel_rows
    field["panel_generalized_load_corrections"] = corrections
    for row in [*field["finite_body_applied_loads"], *corrections]:
        row.update({key: field[key] for key in ("state_id", "case_id", "accessory_placement")})
    # Actual JSON serialization breaks in-memory source/export list aliases.
    return json.loads(json.dumps(field)), q, source, panels, integrated, bodies


def test_actual_source_load_serializer_mass_centroids_and_both_corrections():
    field, q, source, panels, integrated, _ = deepcopy(actual_source_load_export())
    receipt = audit.verify_current_loads(field, q, source, panels, integrated)
    assert receipt["source_load_count_before_timber_quadrature"] == 689
    assert receipt["exported_discrete_load_count"] == 1079
    assert receipt["own_shaft_metal_roles"] == 350 and receipt["generalized_panel_corrections"] == 12


@pytest.mark.parametrize("mutation", ["gravity-owner", "gravity-force", "source-load-id", "hold-lever", "current-point", "correction-vector", "correction-wrench"])
def test_actual_current_source_load_mutations_reject(mutation):
    field, q, source, panels, integrated, _ = deepcopy(actual_source_load_export())
    metal = next(r for r in field["finite_body_applied_loads"] if r["id"].startswith("physical-bolt-metal/"))
    if mutation == "gravity-owner":
        metal["body"] = "base_floor_left"
    elif mutation == "gravity-force":
        metal["force_xyz_n"][2] -= 1.
    elif mutation == "source-load-id":
        metal["source_load_id"] = "wrong-source-metal-role"
    elif mutation == "hold-lever":
        next(r for r in field["finite_body_applied_loads"] if r["id"].startswith("climber/"))["point_xyz_mm"][2] += 100.
    elif mutation == "current-point":
        metal["current_point_xyz_mm"][0] += .01
    elif mutation == "correction-vector":
        field["panel_generalized_load_corrections"][0]["local_generalized_force_n"][0] += .01
    else:
        field["panel_generalized_load_corrections"][0]["current_equivalent_rigid_wrench_n_nmm"][0] += 1.
    with pytest.raises(ValueError):
        audit.verify_current_loads(field, q, source, panels, integrated)


def test_reference_source_load_export_cannot_claim_equilibrium_without_reactions():
    field, _, _, _, _, bodies = deepcopy(actual_source_load_export())
    field["finite_interaction_actions"] = []
    with pytest.raises(ValueError, match="current wrench closure fails"):
        audit.verify_equilibrium(field, bodies)


def test_raw_byte_and_canonical_dict_receipt_hashes_are_explicitly_distinct():
    field = {"a": 1, "b": [2, 3]}
    payload = json.dumps(field, indent=2).encode()
    raw = audit.field_hashes(field, payload)
    parsed = audit.field_hashes(field)
    assert raw["field_sha256"] != raw["field_canonical_sha256"]
    assert parsed["field_sha256"] is None
    assert raw["field_canonical_sha256"] == parsed["field_canonical_sha256"]


def test_all_actual_method_source_pins_authenticate_before_candidate_response():
    _, _, _, _, _, _, pins = audit.common.read_sources()
    pins.update(audit.SOURCE_PINS); pins.update(audit.PHYSICAL_EXPORT_PINS); pins.update(audit.finite.source_pins())
    receipt = audit.source_receipt({"source_sha256": pins})
    assert receipt[-1]["scripts/thin_bolted_finite_frame.py"] == audit.FINITE_SHA


@pytest.mark.parametrize("mutation", ["ghost-leg-vertex", "foreign-BREP", "area", "missing-foot"])
def test_finished_floor_proof_mutations_reject_without_BREP_queries(mutation):
    field, _, contact, cache, *_ = deepcopy(complete_reference_geometry())
    source = json.loads(audit.member_geometry.SPAN_SOURCE.read_text())
    field["finished_floor_footprints"] = source["finished_floor_footprints"]
    field["parameters"].update(floor_contact_geometry_sha256=audit.support.CONTACT_SHA,
        floor_support_basis="finished-corner-local-rough-elastic-stick-v1", floor_normal_activation_threshold_n=1e-7)
    audit.verify_floor_proofs(field, contact, cache)
    if mutation == "ghost-leg-vertex":
        proof = next(p for p in field["finished_floor_footprints"] if p["member"] == "lumber_leg_left")
        proof["polygons_xyz_mm"][0][0][0] = -1219.2
    elif mutation == "foreign-BREP":
        field["finished_floor_footprints"][0]["source_brep_sha256"] = "0"*64
    elif mutation == "area":
        field["finished_floor_footprints"][0]["bearing_area_mm2"] += 1.
    else:
        field["finished_floor_footprints"].pop()
    with pytest.raises(ValueError):
        audit.verify_floor_proofs(field, contact, cache)
