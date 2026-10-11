"""Portable current-component bindings and ground-plane statics; no raw bank."""

import contextlib
import copy
import json
import math
from types import SimpleNamespace

import pytest

from scripts import eoere_current_components as component
from scripts import eoere_current_sections as section
from scripts import summarize_eoere_current_components as summary


def test_selected_catalog_uses_new_length_and_smooth_body_without_mutating_source():
    facts = {"diameters": [{"diameter_in": .375, "washer": {"sku": 1}, "nut": {"sku": 2}}],
             "bolts": [{"diameter_in": .375, "nominal_length_in": 4., "Lb_min_in": 2.69}],
             "material_source": {"minimum_yield_psi": 92000}}
    row = {"selected_diameter_mm": 9.525, "selected_underhead_length_mm": 120.65,
           "minimum_body_mm": 87.376, "selected_product": "new", "selected_product_url": "source",
           "selected_washer_SKU": "1", "selected_nut_SKU": "2"}
    before = copy.deepcopy(facts)
    result = component.selected_catalog(facts, {"axis": row})
    assert result["bolts"] == [{"diameter_in": .375, "nominal_length_in": 4.75,
                                "Lb_min_in": pytest.approx(3.44), "sku": "new", "url": "source"}]
    assert result["material_source"] == facts["material_source"]
    assert facts == before
    with pytest.raises(ValueError, match="nut/washer family"):
        component.selected_catalog(facts, {"axis": row | {"selected_washer_SKU": "foreign"}})
    with pytest.raises(ValueError, match="conflicting selected"):
        component.selected_catalog(facts, {"a": row, "b": row | {"minimum_body_mm": 80.}})


def floor_fixture(x=0., couple_y=0.):
    points = [[-100., -100., 0.], [-100., 100., 0.], [100., -100., 0.], [100., 100., 0.]] * 8
    rows = [{"kind": "floor_normal", "compression_n": 10., "point_xyz_mm": p} for p in points]
    rows += [{"kind": "floor_tangent", "interaction_enabled": True, "id": str(i),
              "point_xyz_mm": [0., 0., 0.]} for i in range(4)]
    return {"floor_actions": rows, "body_applied_loads": [
        {"force_xyz_n": [32., 0., -320.], "point_xyz_mm": [x, 0., 100.],
         "moment_xyz_nmm": [0., couple_y, 0.]}]}


def test_ground_plane_screen_keeps_height_and_free_couple_and_never_qualifies_floor():
    result = component.support_screen(floor_fixture(20., 6400.))
    assert result["required_ground_normal_resultant_xy_mm"] == pytest.approx([50., 0.])
    assert result["minimum_signed_hull_edge_margin_mm"] == pytest.approx(50.)
    assert result["global_required_friction_coefficient_lower_bound"] == pytest.approx(.1)
    assert result["necessary_no_tension_ground_plane_screen_pass"] is True
    assert result["actual_no_slip_or_overturning_qualified"] is False
    assert result["floor_friction_or_contact_pressure_capacity"] is None


def test_outside_hull_is_recorded_as_necessary_screen_failure():
    result = component.support_screen(floor_fixture(100.))
    assert result["required_ground_normal_resultant_xy_mm"] == pytest.approx([110., 0.])
    assert result["minimum_signed_hull_edge_margin_mm"] == pytest.approx(-10.)
    assert result["necessary_no_tension_ground_plane_screen_pass"] is False


@pytest.mark.parametrize("couple_x,expected_y,margin,passes", [(0., 70., 30., True), (3200., 60., 40., True),
                                                            (-12800., 110., -10., False)])
def test_offset_asymmetric_floor_keeps_y_height_and_free_x_couple(couple_x, expected_y, margin, passes):
    field = floor_fixture()
    corners = [[0., 0., 0.], [0., 100., 0.], [120., 0., 0.], [120., 100., 0.]]
    weights = [320/24, 320/24, 320/48, 320/48]
    for i, row in enumerate(field["floor_actions"][:32]):
        row["point_xyz_mm"], row["compression_n"] = corners[i % 4], weights[i % 4]
    field["body_applied_loads"] = [{"force_xyz_n": [0., 32., -320.], "point_xyz_mm": [50., 60., 100.],
                                   "moment_xyz_nmm": [couple_x, 0., 0.]}]
    result = component.support_screen(field)
    assert result["required_ground_normal_resultant_xy_mm"] == pytest.approx([50., expected_y])
    assert result["minimum_signed_hull_edge_margin_mm"] == pytest.approx(margin)
    assert result["saved_compression_center_xy_mm"] == pytest.approx([40., 50.])
    assert result["required_vs_saved_center_error_mm"] == pytest.approx(math.hypot(10., expected_y-50.))
    assert result["net_normal_balance_error_n"] == pytest.approx(0.)
    assert result["global_required_friction_coefficient_lower_bound"] == pytest.approx(.1)
    assert result["necessary_no_tension_ground_plane_screen_pass"] is passes
    assert result["actual_no_slip_or_overturning_qualified"] is False
    assert result["floor_friction_or_contact_pressure_capacity"] is None


@pytest.mark.parametrize("mutation", ["elevated", "tension", "zero_normal", "upward"])
def test_incompatible_floor_screen_inputs_fail_closed(mutation):
    field = floor_fixture()
    if mutation == "elevated":
        field["floor_actions"][-1]["point_xyz_mm"][2] = 1.
    elif mutation == "tension":
        field["floor_actions"][0]["compression_n"] = -1.
    elif mutation == "zero_normal":
        for row in field["floor_actions"][:32]:
            row["compression_n"] = 0.
    else:
        field["body_applied_loads"][0]["force_xyz_n"][2] = 320.
    with pytest.raises(ValueError):
        component.support_screen(field)


def test_raw_washer_land_cannot_become_finished_wood_support_proof():
    raw = {"source_nominal_outer_landing_full": True, "finished_local_service_cuts_proven_clear": True,
           "own_receiver_service_cut_count": 0, "source_convex_stock_disk_contained": True}
    result = component.conditional_finished_land(lambda: copy.deepcopy(raw))()
    assert result["source_convex_stock_disk_contained"] is True
    assert result["source_nominal_outer_landing_full"] is False
    assert result["finished_local_service_cuts_proven_clear"] is False
    assert result["own_receiver_service_cut_count"] is None
    assert raw["source_nominal_outer_landing_full"] is True


def spacer_fixture():
    shafts, rows = [], []
    scenario = {"ID_mm": 11., "OD_mm": 25., "t_mm": 2., "sampled_axial_only_Fy_required_mpa": 1.,
                "Fy_33ksi_reference_ratio_unadopted": 0.1,
                "raw_ring_Fc_perp625psi_mean_ratio_conditional": .1,
                "nominal_supported_ring_Fc_perp625psi_mean_reference_index": None,
                "uniform_supported_ring_mean_mpa_geometric_diagnostic": .4}
    for index in range(9):
        aid = str(index)
        nominal = scenario | {"ID_mm": 11.+index/10., "OD_mm": 25.+index}
        corners = [scenario | {"ID_mm": nominal["ID_mm"]+inner, "OD_mm": nominal["OD_mm"]+outer, "t_mm": 1.5}
                   for inner, outer in [(0., 0.), (.5, 0.), (0., 3.), (.5, 3.)]]
        shafts.append({"axis_id": aid, "source_axis": {"nut_side_spacer_mm": 12.7 if index < 8 else 0.},
                       "metal_roles": [{"kind": "spacer"}] if index < 8 else [],
                       "surfaces": [{"host": aid, "interval_mm": [0., 80.], "bore_diameter_mm": 10.+index/100.}],
                       "ends": [{"end": "nut", "support_s_mm": 80.}]})
        rows.append({"capture_id": aid + "/nut-capture", "axis_id": aid, "end": "nut", "host": aid,
                     "receiver_kind": "wood", "diameter_mm": 9.525, "N_n": 100.+17*index,
                     "nominal_own_hardware_geometry": nominal,
                     "USS_catalog_corners_min_thickness": corners,
                     "own_max_catalog_axial_Fy_corner": copy.deepcopy(scenario),
                     "own_max_catalog_geometric_mean_corner": copy.deepcopy(scenario),
                     "outer_landing_for_max_nominal_or_catalog_OD": {"fixture_land": index}, "grain_axis_abs_cos_to_pressure_normal": index/10.})
    return ({"all200_own_end_diagnostics": rows, "limits": []}, {"source_inputs": {"shafts": shafts}},
            {"diameters": [{"diameter_in": .375, "washer": {"sku": 1}}]}, scenario)


def test_eight_spacer_nuts_use_overlap_ring_and_keep_unspaced_row():
    report, field, facts, scenario = spacer_fixture()
    calls = []
    before = copy.deepcopy(report["all200_own_end_diagnostics"])
    expected_calls = [(row["N_n"], s["ID_mm"], s["OD_mm"], s["t_mm"], 19.05/2,
                       field["source_inputs"]["shafts"][i]["surfaces"][0]["bore_diameter_mm"], row["receiver_kind"],
                       row["outer_landing_for_max_nominal_or_catalog_OD"], row["grain_axis_abs_cos_to_pressure_normal"])
                      for i, row in enumerate(before[:8])
                      for s in [row["nominal_own_hardware_geometry"], *row["USS_catalog_corners_min_thickness"]]]
    def metrics(force, inner, outer, thickness, ring, bore, receiver, land, grain):
        calls.append((force, inner, outer, thickness, ring, bore, receiver, copy.deepcopy(land), grain))
        # A load- and dimension-dependent sentinel checks adapter arguments;
        # the frozen annular plate equations are a separate reviewed method.
        fy = force*(inner+outer)/thickness**2
        mean = force/(outer**2-inner**2)
        return scenario | {"ID_mm": inner, "OD_mm": outer, "t_mm": thickness,
                           "uniform_load_ring_outer_radius_mm": ring,
                           "sampled_axial_only_Fy_required_mpa": fy, "Fy_33ksi_reference_ratio_unadopted": fy/200.,
                           "raw_ring_Fc_perp625psi_mean_ratio_conditional": mean/4.,
                           "uniform_supported_ring_mean_mpa_geometric_diagnostic": mean}
    untouched = copy.deepcopy(report["all200_own_end_diagnostics"][-1])
    result = component.spacer_washer_references(report, field, facts, metrics)
    assert calls == expected_calls
    assert len(result["spacer_nut_load_rings_refreshed"]) == 8
    assert result["all200_own_end_diagnostics"][-1] == untouched
    for row, original in zip(result["all200_own_end_diagnostics"][:8], before[:8], strict=True):
        actual = [row["nominal_own_hardware_geometry"], *row["USS_catalog_corners_min_thickness"]]
        saved = [original["nominal_own_hardware_geometry"], *original["USS_catalog_corners_min_thickness"]]
        for value, source in zip(actual, saved, strict=True):
            assert [value[k] for k in ("ID_mm", "OD_mm", "t_mm")] == [source[k] for k in ("ID_mm", "OD_mm", "t_mm")]
            assert value["sampled_axial_only_Fy_required_mpa"] == pytest.approx(original["N_n"]*(source["ID_mm"]+source["OD_mm"])/source["t_mm"]**2)
            assert value["uniform_supported_ring_mean_mpa_geometric_diagnostic"] == pytest.approx(original["N_n"]/(source["OD_mm"]**2-source["ID_mm"]**2))
        assert row["own_max_catalog_axial_Fy_corner"] == row["USS_catalog_corners_min_thickness"][3]
        assert row["own_max_catalog_geometric_mean_corner"] == row["USS_catalog_corners_min_thickness"][1]
        assert row["spacer_nominal_axial_mean_stress_mpa"] == pytest.approx(original["N_n"]/(math.pi*(19.05**2-10.31875**2)/4))
        assert row["spacer_strength_nut_contact_or_compatible_pressure_bound"] is None
    assert result["worsts"]["all_catalog_axial_Fy_required"]["capture_id"] == "7/nut-capture"


def test_spacer_annulus_rejects_incompatible_washer_overlap():
    report, field, facts, scenario = spacer_fixture()
    report["all200_own_end_diagnostics"][0]["nominal_own_hardware_geometry"]["ID_mm"] = 10.
    with pytest.raises(ValueError, match="spacer/washer overlap"):
        component.spacer_washer_references(report, field, facts, lambda *_: scenario)


def test_current_axes_reject_preceding_length_or_foreign_axis(monkeypatch):
    axes = [{"id": str(i), "length": 120.65} for i in range(100)]
    monkeypatch.setattr(component.current, "current_metadata", lambda: (None, None, axes, None, {}))
    field = {"source_inputs": {"shafts": [{"axis_id": a["id"], "source_axis": copy.deepcopy(a)} for a in axes]}}
    assert len(component.current_axes(field)[0]) == 100
    field["source_inputs"]["shafts"][0]["source_axis"]["length"] = 101.6
    with pytest.raises(ValueError, match="exact current selected"):
        component.current_axes(field)


def test_mixed_stack_adapter_joins_all_own_surfaces_and_selects_whole_witnesses():
    axes = ["mixed-"+str(i) for i in range(8)]
    shafts = [{"axis_id": aid, "surfaces": [{"host": aid+"/host-"+str(j)} for j in range(3)]} for aid in axes]
    wood, steel = [], []
    for i, shaft in enumerate(shafts):
        for j, surface in enumerate(shaft["surfaces"]):
            port = {"axis_id": shaft["axis_id"], "surface_index": j, "host": surface["host"],
                    "force_on_host_xyz_n": [i+1., j+2., i-j], "moment_on_host_at_point_xyz_nmm": [13.*i, -17.*j, 19.],
                    "point_xyz_mm": [i+101., j-211., 37.]}
            (steel if j == 1 else wood).append(port)
    bearings = [{"id": aid+"/bearing", "point_xyz_mm": [i, 23., 31.]} for i, aid in enumerate(axes)]
    captures = [{"id": aid+"/capture", "point_xyz_mm": [-i, 29., 41.], "force_n": 43.+i} for i, aid in enumerate(axes)]
    field = {"source_inputs": {"shafts": list(reversed(shafts)) + [{"axis_id": "supported", "surfaces": []}]},
             "common_shaft_wood_bearing_actions": list(reversed(wood)), "common_shaft_steel_port_actions": list(reversed(steel)),
             "common_shaft_bearing_actions": list(reversed(bearings)), "shaft_end_capture_actions": list(reversed(captures))}
    order = [axes[i] for i in [6, 0, 7, 3, 1, 5, 2, 4]]
    detailed = {"timber": {"shaft_components": [{"axis_id": aid, "component": None} for aid in order]
                          + [{"axis_id": "supported", "component": {"reference": .2}}]}}
    before = copy.deepcopy((field, detailed))
    expected_ports = {(p['axis_id'], p['surface_index']): p for p in wood+steel}
    expected_bearings = {p['id']: p for p in bearings}
    expected_captures = {p['id']: p for p in captures}
    calls, witnesses = [], []
    def trial(shaft, index, port, bearing_map, capture_map):
        aid = shaft['axis_id']
        assert shaft == shafts[axes.index(aid)]
        assert port == expected_ports[aid, index]
        assert bearing_map == expected_bearings and capture_map == expected_captures
        calls.append((aid, index))
        i = axes.index(aid)
        value = {'necessary_directional_peak_line_density_bound_n_mm': 100.*i+index,
                 'affine_trial_peak_line_density_n_mm': 100.*(7-i)+(2-index),
                 'surface_index': index, 'whole_own_port': copy.deepcopy(port),
                 'own_capture': copy.deepcopy(capture_map[aid+'/capture'])}
        witnesses.append({'axis_id': aid, **value})
        return value
    source = component.FROZEN['connected']
    def pure(path, names, namespace):
        assert path == source['path'] and names == ['line_bound', 'bearing_trial', 'known_answers']
        assert namespace['math'] is math and namespace['np'].__name__ == 'numpy'
        assert namespace['parent'].require is component.current.require
        return {'bearing_trial': trial, 'known_answers': lambda: {'fixture_known_answer': True}}
    result = component.connected_references(field, detailed, SimpleNamespace(pure=pure), {source['path']: source['sha256']})
    assert calls == [(aid, j) for aid in order for j in range(3)]
    assert result['mixed_axis_ids'] == order and result['own_surface_trials'] == witnesses
    assert result['known_answers'] == {'fixture_known_answer': True}
    assert result['worst_necessary_line_density'] == next(w for w in witnesses if w['axis_id'] == axes[7] and w['surface_index'] == 2)
    assert result['worst_affine_trial_line_density'] == next(w for w in witnesses if w['axis_id'] == axes[0] and w['surface_index'] == 0)
    assert result['compatible_threaded_contact_or_yield_capacity'] is None
    assert (field, detailed) == before
    with pytest.raises(ValueError, match='eight current mixed stacks'):
        component.connected_references(field, detailed, SimpleNamespace(pure=pure), {source['path']: 'foreign'})
    with pytest.raises(ValueError, match='eight current mixed stacks'):
        component.connected_references(field, {'timber': {'shaft_components': detailed['timber']['shaft_components'][1:]}},
                                       SimpleNamespace(pure=pure), {source['path']: source['sha256']})


@pytest.mark.parametrize("mutation", ["raw_hash", "unadmitted", "foreign_case"])
def test_reducer_import_is_unreachable_before_exact_current_admission(tmp_path, monkeypatch, mutation):
    current = component.current
    monkeypatch.setattr(current, "ROOT", tmp_path)
    producer = tmp_path / "producer.py"
    producer.write_text("force producer")
    monkeypatch.setattr(current, "OWN", producer)
    monkeypatch.setattr(current, "LOADED_SHA", current.sha(producer))
    field_path = tmp_path / "field.json"
    field_path.write_text('{}')
    geom, hardware, release = {"path": "geom", "sha256": "g"}, {"path": "hardware", "sha256": "h"}, {"structural_released": False}
    binding = {"case_id": "a12-forward", "state_id": "current", "field": current.ref(field_path),
               "admission": {"path": "admission", "sha256": "a"}}
    summary = {"geometry": geom, "hardware_model": hardware, "force_producer": current.ref(producer),
               "extra_grid": False, "case_sequence": component.SEQUENCE, "all_six_saved_field_admissions_pass": True,
               "structural_acceptance": False, "release": release, "cases": [binding]}
    config = {"schema": "eoere_current_component_inputs/v1", "release": release,
              "current_response": {"path": "summary", "sha256": "s"}, "methods": component.FROZEN}
    inputs = tmp_path / "inputs.json"
    inputs.write_text('{}')
    monkeypatch.setattr(component, "INPUTS", inputs)
    monkeypatch.setattr(component, "own_ref", lambda: current.ref(producer))
    monkeypatch.setattr(component, "canonical_dependency", lambda: dict(component.CANONICAL_HELPER))
    monkeypatch.setattr(current, "manifest", lambda: {"release": release, "references": {"geometry": geom, "hardware": hardware}})
    monkeypatch.setattr(current, "read", lambda ref: {"inputs.json": config, "summary": summary, "admission": {}}[ref["path"]])
    monkeypatch.setattr(current, "verify", lambda pins: pins)
    called = []
    def intake(*args, **kwargs):
        called.append("gate")
        if mutation == "unadmitted":
            raise ValueError("not admitted")
        return {"case_id": "foreign", "state_id": "current"}, {}
    @contextlib.contextmanager
    def context():
        yield SimpleNamespace(require_admitted_payload=intake), None
    monkeypatch.setattr(current, "response_context", context)
    def forbidden(*args):
        pytest.fail("component callback reached before valid admission")
    monkeypatch.setattr(component, "load", forbidden)
    monkeypatch.setattr(component, "current_axes", forbidden)
    if mutation == "raw_hash":
        binding["field"]["sha256"] = "foreign"
    with pytest.raises(ValueError):
        component.consume_case("a12-forward")
    assert called == ([] if mutation == "raw_hash" else ["gate"])


@pytest.mark.parametrize("case_id", ["a12-forward", "k12-rear"])
def test_consumed_case_routes_selected_catalog_and_corrected_washers(tmp_path, monkeypatch, case_id):
    """Exercise adapter orchestration with portable reducer/gate stand-ins."""
    current = component.current
    monkeypatch.setattr(current, "ROOT", tmp_path)
    def saved(name, data):
        path = tmp_path / name
        path.write_text(json.dumps(data))
        return current.ref(path)
    producer = saved("producer.py", "force producer")
    monkeypatch.setattr(current, "OWN", tmp_path / producer["path"])
    monkeypatch.setattr(current, "LOADED_SHA", producer["sha256"])
    adapter = saved("adapter.py", "component adapter")
    monkeypatch.setattr(component, "own_ref", lambda: adapter)
    canonical = saved("canonical.py", "canonical helper")
    monkeypatch.setattr(component, "canonical_dependency", lambda: canonical)
    frozen = {name: saved(name+".py", name) for name in component.FROZEN}
    monkeypatch.setattr(component, "FROZEN", frozen)
    release = {"structural_released": False}
    geom, hardware, descriptor = (saved(name, {}) for name in ["geometry", "hardware", "descriptor"])
    monkeypatch.setattr(current, "manifest", lambda: {
        "release": release, "references": {"geometry": geom, "hardware": hardware}})
    report, field, facts, scenario = spacer_fixture()
    facts["diameters"][0]["nut"] = {"sku": 2}
    facts["bolts"] = [{"diameter_in": .375, "nominal_length_in": 4., "Lb_min_in": 2.69}]
    original_facts = copy.deepcopy(facts)
    field.update(floor_fixture())
    field.update(case_id=case_id, state_id="own-"+case_id, accessory_placement={"extra_grid": False})
    field["source_inputs"]["geometry"] = {"cached_source_export": descriptor}
    # Keep the real 100-axis adapter check; only the bulky solver/reducers are replaced.
    for i in range(9, 100):
        field["source_inputs"]["shafts"].append({"axis_id": str(i), "source_axis": {}, "metal_roles": []})
    axes = []
    for shaft in field["source_inputs"]["shafts"]:
        shaft["source_axis"].update(id=shaft["axis_id"], length=120.65)
        axes.append(copy.deepcopy(shaft["source_axis"]))
    selection = {"selected_diameter_mm": 9.525, "selected_underhead_length_mm": 120.65,
                 "minimum_body_mm": 87.376, "selected_product": "selected", "selected_product_url": "source",
                 "selected_washer_SKU": "1", "selected_nut_SKU": "2"}
    selection_ref = saved("selections", selection)
    selection_pins = {selection_ref["path"]: selection_ref["sha256"]}
    monkeypatch.setattr(current, "current_metadata", lambda: (None, None, axes, {"axis": selection}, selection_pins))
    binding = {"case_id": case_id, "state_id": field["state_id"], "field": saved("field.json", field),
               "admission": saved("admission.json", {"admitted": True})}
    response_ref = saved("response.json", {"geometry": geom, "hardware_model": hardware, "force_producer": producer,
        "extra_grid": False, "case_sequence": component.SEQUENCE, "all_six_saved_field_admissions_pass": True,
        "release": release, "structural_acceptance": False, "cases": [binding], "source_manifest": descriptor})
    saved("inputs.json", {"schema": "eoere_current_component_inputs/v1", "release": release,
                          "current_response": response_ref, "methods": frozen})
    monkeypatch.setattr(component, "INPUTS", tmp_path / "inputs.json")
    checked_ast = object()
    events = []
    def intake(raw, receipt, *, admission_sha256):
        assert receipt == {"admitted": True} and admission_sha256 == producer["sha256"]
        events.append("admitted")
        return json.loads(raw), {}
    @contextlib.contextmanager
    def context():
        yield SimpleNamespace(require_admitted_payload=intake), SimpleNamespace(checked_ast=checked_ast)
    monkeypatch.setattr(current, "response_context", context)
    prior_plan = SimpleNamespace(BASE="fixture", METHODS={}, ARTIFACTS={}, merge=current.join,
                                 checked_bytes=object(), indexed=object())
    def coarse(admitted, observed_axes, plan, pins, version):
        assert events == ["admitted"] and admitted == field and observed_axes == {a["id"]: a for a in axes}
        assert plan.ARTIFACTS["geometry"] == geom and plan.ARTIFACTS["descriptors"] == descriptor and version == 41
        events.append("coarse")
        return {"own_case": admitted["case_id"]}
    original_gate = object()
    consumer = SimpleNamespace(FIELD_SCHEMA="old-schema", _reduce=coarse, _load_gate=original_gate)
    raw_land = {"source_nominal_outer_landing_full": True, "finished_local_service_cuts_proven_clear": True,
                "own_receiver_service_cut_count": 0}
    def raw_land_function():
        return copy.deepcopy(raw_land)
    private_globals = {"wood_land": raw_land_function, "copy": copy, "report": report}
    # A literal function gets the same private globals as checked frozen methods.
    exec("def calculate(*args):\n    data = copy.deepcopy(report)\n    data['fixture_landing'] = wood_land()\n    return data\n", private_globals)  # noqa: S102
    raw_calculate = private_globals["calculate"]
    def metrics(force, inner, outer, thickness, ring, bore, receiver, land, grain):
        fy = force*(inner+outer)/thickness**2
        return scenario | {"ID_mm": inner, "OD_mm": outer, "t_mm": thickness,
            "uniform_load_ring_outer_radius_mm": ring, "sampled_axial_only_Fy_required_mpa": fy,
            "Fy_33ksi_reference_ratio_unadopted": fy/200.,
            "uniform_supported_ring_mean_mpa_geometric_diagnostic": force/(outer**2-inner**2)}
    method_result = SimpleNamespace(washer={"wood_land": raw_land_function, "calculate": raw_calculate,
                                           "scenario_metrics": metrics})
    def methods():
        return method_result
    def materials():
        return "template", facts, "roots", "material"
    rich = SimpleNamespace(GATE_SHA="old-gate", _methods=methods, _materials=materials, washer_geometry=object())
    def detailed(admitted, path, c, plan, pins, contract):
        assert events == ["admitted", "coarse"] and path == tmp_path / binding["field"]["path"]
        assert c._load_gate(None).checked_ast is checked_ast and rich.GATE_SHA == producer["sha256"]
        assert contract["nominal_seat_geometry"]["all_current_finished_wood_lands_qualified"] is False
        composition = rich.washer_geometry()
        assert composition["axes"] == axes and composition["current_finished_cut_inventory_used_for_landing_proof"] is False
        template, catalog, roots, material = rich._materials()
        assert (template, roots, material) == ("template", "roots", "material")
        result = rich._methods().washer["calculate"](admitted, composition, catalog, pins, True)
        events.append("detailed")
        return {"washers": result, "fixture_catalog": catalog, "missing_current_inputs": {}}
    rich._reduce = detailed
    def load(ref, name):
        assert events == ["admitted"] and ref == frozen[name]
        return {"consumer": consumer, "followups": rich, "plan": prior_plan}[name]
    monkeypatch.setattr(component, "load", load)
    def connected(admitted, details, loaded_methods, pins):
        assert events == ["admitted", "coarse", "detailed"] and loaded_methods is method_result
        assert len(details["washers"]["spacer_nut_load_rings_refreshed"]) == 8
        return {"fixture_case": admitted["case_id"], "compatible_threaded_contact_or_yield_capacity": None}
    monkeypatch.setattr(component, "connected_references", connected)
    result = component.consume_case(case_id)
    catalog = result["findings"]["fixture_catalog"]
    assert catalog["bolts"] == [{"diameter_in": .375, "nominal_length_in": 4.75,
        "Lb_min_in": pytest.approx(3.44), "sku": "selected", "url": "source"}]
    assert catalog["current_selected_length_and_minimum_body_basis"] is True
    washers = result["findings"]["washers"]
    assert washers["fixture_landing"]["source_nominal_outer_landing_full"] is False
    assert washers["fixture_landing"]["finished_local_service_cuts_proven_clear"] is False
    for index, row in enumerate(washers["all200_own_end_diagnostics"][:8]):
        own = row["nominal_own_hardware_geometry"]
        assert own["uniform_load_ring_outer_radius_mm"] == 19.05/2
        assert own["sampled_axial_only_Fy_required_mpa"] == pytest.approx((100.+17*index)*(36.+1.1*index)/4)
        assert row["spacer_nominal_axial_mean_stress_mpa"] == pytest.approx((100.+17*index)/(math.pi*(19.05**2-10.31875**2)/4))
        assert row["spacer_strength_nut_contact_or_compatible_pressure_bound"] is None
    assert result["case_id"] == case_id and result["state_id"] == "own-"+case_id
    assert result["component_reductions"] == {"own_case": case_id}
    assert result["connected_mixed_stack_statics"]["fixture_case"] == case_id
    assert result["support_screen"]["required_ground_normal_resultant_xy_mm"] == pytest.approx([10., 0.])
    assert result["complete_joint_resistance"] is None and result["native_or_global_solve_performed"] is False
    assert consumer._load_gate is original_gate and consumer.FIELD_SCHEMA == "old-schema"
    assert rich._methods is methods and rich._materials is materials and rich.GATE_SHA == "old-gate"
    assert private_globals["wood_land"] is raw_land_function and facts == original_facts
    assert current.read(binding["field"]) == field


@pytest.mark.parametrize("entrypoint", ["component", "section", "summary"])
@pytest.mark.parametrize("drift", ["disk_changed", "unreviewed_loaded_version"])
def test_canonical_dependency_drift_rejects_before_saved_input_or_method_use(monkeypatch, entrypoint, drift):
    helper = component.saved_force_summary
    original_sha = component.current.sha
    monkeypatch.setattr(component.current, "sha", lambda path: "0"*64 if path == helper.OWN else original_sha(path))
    if drift == "unreviewed_loaded_version":
        monkeypatch.setattr(helper, "LOADED_SHA", "0"*64)
    def forbidden(*args):
        pytest.fail("saved inputs reached before canonical helper authentication")
    monkeypatch.setattr(component.current, "read", forbidden)
    with pytest.raises(ValueError, match="summary producer changed|exact frozen canonical helper"):
        if entrypoint == "component":
            component.consume_case("a12-forward")
        elif entrypoint == "section":
            section.run()
        else:
            summary.summarize({"path": "unused.json", "sha256": "unused"})
