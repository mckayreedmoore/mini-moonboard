"""Portable current section selection and component references."""

import copy
import json
import math
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from scripts import eoere_current_sections as section


def fixture():
    members = [{"name": str(i), "axis": [0., 0., 1.], "start": [float(i), 0., 0.],
                "end": [float(i), 0., 100.]} for i in range(22)]
    fields, cases = {}, {}
    for case_index, case_id in enumerate(section.SEQUENCE):
        rows = [{"member": m["name"], "witnesses": {"fully_braced_normal": {
            "station_global_grain_projection_mm": 50.,
            "gross_CD1_comparison": {"fully_braced_component_normal_interaction": 1.+case_index}}}} for m in members]
        cases[case_id] = {"component_reductions": {"fresh_gross_member_diagnostics": rows}}
        ports = [{"host": m["name"], "surface_interval_mm": [0., 10.], "axis_id": "axis-"+m["name"],
                  "force_on_host_xyz_n": [float(i+1), 0., 0.], "moment_on_host_at_point_xyz_nmm": [0., 0., 0.],
                  "point_xyz_mm": [float(i), 0., 20.]} for i, m in enumerate(members)]
        fields[case_id] = {"source_inputs": {"timber_rows": copy.deepcopy(members)}, "common_shaft_wood_bearing_actions": ports}
    return cases, fields


def test_bounded_stations_keep_whole_case_witnesses_and_deduplicate_bores():
    cases, fields = fixture()
    before = copy.deepcopy((cases, fields))
    rows = section.select_requests(cases, fields)
    assert len(rows) == 38
    assert {r["member"] for r in rows[:22]} == {str(i) for i in range(22)}
    assert all(r["selection"]["case_id"] == "a1-rear" for r in rows[:22])
    assert all(r["selection"]["gross_normal_reference_index"] == 6. for r in rows[:22])
    assert all(r["station_global_grain_projection_mm"] == 20. for r in rows[22:])
    assert {r["member"] for r in rows[22:]} == {str(i) for i in range(6, 22)}
    assert (cases, fields) == before


def test_terminal_witness_gets_recorded_interior_plane_and_foreign_geometry_rejects():
    cases, fields = fixture()
    cases['a1-rear']["component_reductions"]["fresh_gross_member_diagnostics"][0]["witnesses"]["fully_braced_normal"]["station_global_grain_projection_mm"] = 100.
    row = section.select_requests(cases, fields)[0]
    assert row["station_global_grain_projection_mm"] == pytest.approx(99.9)
    assert row["selection"]["original_gross_station_mm"] == 100.
    fields['a1-rear']["source_inputs"]["timber_rows"][0]["end"][2] = 101.
    with pytest.raises(ValueError, match="same current"):
        section.select_requests(cases, fields)


def test_each_member_retains_its_own_case_station_and_action_witness():
    cases, fields = fixture()
    expected = {}
    for case_index, case_id in enumerate(section.SEQUENCE):
        for i, row in enumerate(cases[case_id]["component_reductions"]["fresh_gross_member_diagnostics"]):
            witness = row["witnesses"]["fully_braced_normal"]
            witness["station_global_grain_projection_mm"] = 20.+i+2*case_index
            value = 100.+i if case_index == (5*i+1) % 6 else .1+case_index/100.
            witness["gross_CD1_comparison"]["fully_braced_component_normal_interaction"] = value
            if value >= 100.:
                expected[row["member"]] = (case_id, witness["station_global_grain_projection_mm"], value)
    before = copy.deepcopy((cases, fields))
    rows = section.select_requests(cases, fields)
    actual = {r["member"]: (r["selection"]["case_id"], r["station_global_grain_projection_mm"],
                             r["selection"]["gross_normal_reference_index"]) for r in rows[:22]}
    assert actual == expected
    assert (cases, fields) == before


def test_bore_ranking_uses_own_free_couple_and_surface_length():
    cases, fields = fixture()
    for field in fields.values():
        field["common_shaft_wood_bearing_actions"] = []
    # The larger force loses to the smaller force plus its own couple/length.
    fields['a12-rear']["common_shaft_wood_bearing_actions"] = [
        {"host": "0", "surface_interval_mm": [2., 12.], "axis_id": "large-force",
         "force_on_host_xyz_n": [100., 0., 0.], "moment_on_host_at_point_xyz_nmm": [0., 0., 0.],
         "point_xyz_mm": [0., 0., 21.]},
        {"host": "1", "surface_interval_mm": [-2., 2.], "axis_id": "short-couple",
         "force_on_host_xyz_n": [3., 4., 0.], "moment_on_host_at_point_xyz_nmm": [0., 0., 440.],
         "point_xyz_mm": [1., 0., 22.]},
        {"host": "2", "surface_interval_mm": [0., 40.], "axis_id": "long-couple",
         "force_on_host_xyz_n": [0., 0., 5.], "moment_on_host_at_point_xyz_nmm": [0., 0., 440.],
         "point_xyz_mm": [2., 0., 23.]}]
    before = copy.deepcopy((cases, fields))
    row = section.select_requests(cases, fields, extra_bore_planes=1)[-1]
    assert row == {"member": "1", "station_global_grain_projection_mm": 22.,
                   "selection": {"basis": "largest remaining own wood port force plus couple/interval selection score",
                                 "case_id": "a12-rear", "axis_id": "short-couple", "selection_score_n": 115.}}
    assert (cases, fields) == before


@pytest.mark.parametrize("dependency_drift", [None, 'before', 'after'], ids=['stable', 'before_import', 'after_import'])
def test_successful_recovery_keeps_six_own_actions_gravity_and_actual_oblique_cut(monkeypatch, tmp_path, dependency_drift):
    """Exercise run's case wiring with portable solid/helper stand-ins."""
    current, component = section.current, section.component
    monkeypatch.setattr(current, "ROOT", tmp_path)

    def put(name, value):
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())
        return {"path": name, "sha256": current.sha(path)}

    force_producer = put('force.py', b'force producer')
    monkeypatch.setattr(current, "OWN", tmp_path/'force.py')
    monkeypatch.setattr(current, "LOADED_SHA", force_producer["sha256"])
    component_producer, section_producer = put('component.py', b'component'), put('section.py', b'section')
    monkeypatch.setattr(component, "own_ref", lambda: component_producer)
    monkeypatch.setattr(section, "own_ref", lambda: section_producer)
    dependency = put('canonical.py', b'canonical')
    monkeypatch.setattr(component, "canonical_dependency", lambda: dependency)
    methods = {k: put(k+'.py', k.encode()) for k in ('sections', 'plane', 'cuts')}
    monkeypatch.setattr(section, "METHODS", methods)
    dependency_ref = put('import.py', b'import dependency')
    monkeypatch.setattr(section, "IMPORT_CLOSURE", {dependency_ref["path"]: dependency_ref["sha256"]})
    monkeypatch.setattr(component, "RAW", tmp_path/'raw')
    monkeypatch.setattr(component, "INPUTS", tmp_path/'inputs.json')
    manifest = {"references": {"geometry": {"revision": "current"}, "hardware": {"revision": "selected"}},
                "release": {"fabrication_released": False}}
    monkeypatch.setattr(current, "manifest", lambda: manifest)
    grain = [math.sqrt(.5), 0., math.sqrt(.5)]
    start = [10., -4., 20.]
    member = {"name": "timber", "axis": grain, "start": start,
              "end": [start[i]+80*grain[i] for i in range(3)], "width_mm": 10., "depth_mm": 20.}
    source = {"timber_rows": [member], "finished_body_observations": [
        {"id": "timber", "source": put('solid.brep', b'cached solid'), "volume_mm3": 10.}]}
    geometry, hardware = manifest["references"].values()
    bindings, own_inputs = [], {}
    for i, case_id in enumerate(section.SEQUENCE):
        own_inputs[case_id] = ({"timber": {"axial": (-1)**i*(i+1)*7., "shear": (7-i)*9., "couple": (i+1)**2*11.}},
                              {"timber": ([i-2., 2.-i/2, (-1)**i*(i+1)], i+3.)})
        field = {"case_id": case_id, "state_id": 'own-'+case_id, "source_inputs": copy.deepcopy(source)}
        binding = {"case_id": case_id, "state_id": field["state_id"], "field": put(case_id+'/field.json', field),
                   "admission": put(case_id+'/admission.json', {"own": case_id})}
        bindings.append(binding)
        put('raw/cases-v1/'+case_id+'/'+component.CASE_ATTEMPT+'/components.json', {
            "schema": "eoere_selected_hardware_current_component_case/v1", "producer": component_producer,
            "field": binding["field"], "admission": binding["admission"], "state_id": field["state_id"],
            "geometry": geometry, "hardware_model": hardware, "release": manifest["release"],
            "raw_field_canonical_sha256": section.canonical_sha(field), "source_sha256": {}})
    summary = put('forces.json', {"case_sequence": section.SEQUENCE, "extra_grid": False,
        "all_six_saved_field_admissions_pass": True, "force_producer": force_producer,
        "geometry": geometry, "hardware_model": hardware, "release": manifest["release"], "cases": bindings})
    put('inputs.json', {"current_response": summary, "release": manifest["release"]})
    admitted = []

    def admit(raw, receipt, **kwargs):
        field = json.loads(raw)
        assert receipt == {"own": field["case_id"]}
        admitted.append(field["case_id"])
        return field, {}

    gate = SimpleNamespace(require_admitted_payload=admit)
    monkeypatch.setattr(current, "response_context", lambda: nullcontext((gate, None)))
    low = sum(a*b for a, b in zip(grain, start))
    monkeypatch.setattr(section, "select_requests", lambda cases, fields: [
        {"member": "timber", "station_global_grain_projection_mm": low+25., "selection": {}}])

    expected_origin = [start[j]+25*grain[j] for j in range(3)]
    face, transform, local = object(), object(), object()
    geometry_calls = []

    class Cut:
        def transformShape(self, matrix):
            assert matrix is transform
            geometry_calls.append('transform')
            return local

    class Solid:
        def isValid(self): return True
        def Solids(self): return [self]
        def Volume(self): return 10.
        def intersect(self, other):
            assert other is face
            geometry_calls.append('intersect')
            return Cut()

    monkeypatch.setitem(sys.modules, 'cadquery', SimpleNamespace(
        Shape=SimpleNamespace(importBrep=lambda name: Solid()), Vector=lambda *xyz: list(xyz)))
    properties = {"finished_area_mm2": 10., "basis_u_v_grain_xyz": [[0., 1., 0.], [-grain[2], 0., grain[0]], grain]}
    calls = []

    def measure(shape, *, origin, grain):
        assert isinstance(shape, Solid)
        assert origin == pytest.approx(expected_origin)
        assert grain == member["axis"]
        geometry_calls.append('measure')
        return properties

    def basis(point, *axes):
        assert point == pytest.approx(expected_origin)
        assert list(axes) == properties["basis_u_v_grain_xyz"]
        geometry_calls.append('basis')
        return SimpleNamespace(wrapped=SimpleNamespace(Value=lambda i, j: float(4*(i-1)+j)))

    def plane_face(point, normal):
        assert point == pytest.approx(expected_origin)
        assert normal == grain
        geometry_calls.append('face')
        return face

    def rigid(rows):
        assert rows == [[1., 2., 3., 4.], [5., 6., 7., 8.], [9., 10., 11., 12.]]
        geometry_calls.append('rigid')
        return transform

    def cut(g, lo, hi, origin, center, weight, actions):
        calls.append((g, lo, hi, origin, center, weight, copy.deepcopy(actions)))
        axial, shear, couple = [actions[k]+weight*center[i] for i, k in enumerate(('axial', 'shear', 'couple'))]
        return {"force_on_lower_portion_xyz_n": [g[0]*axial, shear, g[2]*axial], "couple": couple}

    def stress(local_section, prop, wrench):
        assert local_section is local and prop is properties
        force = wrench["force_on_lower_portion_xyz_n"]
        return {"mean_axial_normal_stress_n_mm2": sum(a*b for a, b in zip(force, grain))/10,
                "bending_normal_stress_extrema_n_mm2": [-wrench["couple"]/50, wrench["couple"]/100]}

    reference = {"Ft_mpa": 4., "Fc_star_mpa": 8., "Fb_star_mpa": 8., "Fv_mpa": 2.}
    helpers = {"sections": SimpleNamespace(measure_section=measure, rigid_matrix=rigid, linear_normal_stress=stress),
               "plane": SimpleNamespace(_basis_matrix=basis, _plane_face=plane_face),
               "cuts": SimpleNamespace(source_pins=dict, rectangle=SimpleNamespace(nds=SimpleNamespace(adjusted_reference=lambda width: reference)),
                    own=SimpleNamespace(member_point_inputs=lambda field: own_inputs[field["case_id"]], previous=SimpleNamespace(member_cut_wrench=cut)))}

    def load(pointer, name):
        assert admitted == section.SEQUENCE
        if dependency_drift == 'after':
            (tmp_path/dependency_ref["path"]).write_bytes(b'changed import')
        return helpers[pointer["path"].removesuffix('.py')]

    monkeypatch.setattr(component, "load", load)
    monkeypatch.setattr(section.importlib.metadata, "version", lambda name: 'fixture')
    if dependency_drift == 'before':
        (tmp_path/dependency_ref["path"]).write_bytes(b'changed import')
    if dependency_drift:
        with pytest.raises(ValueError, match='source drift: import.py'):
            section.run()
        assert bool(geometry_calls) is (dependency_drift == 'after')
        return
    result = section.run()
    rows = result["finished_sections"][0]["case_comparisons"]
    assert result["same_plane_case_comparisons"] == 6
    assert result["native_solve_or_CAD_rebuild"] is False
    assert len(calls) == len(rows) == 6
    assert geometry_calls == ['measure', 'basis', 'face', 'intersect', 'rigid', 'transform']
    for i, case_id in enumerate(section.SEQUENCE):
        actions, gravity = own_inputs[case_id]
        center, weight = gravity["timber"]
        assert calls[i][0] == grain
        assert calls[i][1:3] == pytest.approx((low, low+80))
        assert calls[i][3] == pytest.approx([start[j]+25*grain[j] for j in range(3)])
        assert calls[i][4:] == (center, weight, actions["timber"])
        axial, shear, couple = [actions["timber"][k]+weight*center[j] for j, k in enumerate(('axial', 'shear', 'couple'))]
        mean = axial/10
        normal = (mean/4 if mean >= 0 else (mean/8)**2)+abs(couple)/400
        assert (rows[i]["case_id"], rows[i]["state_id"]) == (case_id, 'own-'+case_id)
        assert rows[i]["linear_normal_stress"]["mean_axial_normal_stress_n_mm2"] == pytest.approx(mean)
        assert rows[i]["normal_reference"]["fully_braced_linear_normal_CD1_reference_index"] == pytest.approx(normal)
        assert rows[i]["necessary_mean_shear_mpa"] == pytest.approx(abs(shear)/10)
        assert rows[i]["necessary_mean_shear_over_CD1_Fv"] == pytest.approx(abs(shear)/20)
        assert rows[i]["finished_shear_torsion_fracture_or_stability_resistance"] is None


@pytest.mark.parametrize("mean,bending,expected", [(2., [-1., .5], 1.), (-4., [-1., .5], .75),
    (0., [-1., .5], .5), (2.4, [-1., .5], 1.1), (-8., [0., 0.], 1.), (-8.8, [0., 0.], 1.21),
    (4., [0., 0.], 1.), (4.4, [0., 0.], 1.1), (-4., [.2, -1.5], 1.)])
def test_normal_comparison_keeps_same_cut_signed_axial_and_actual_bending_extrema(mean, bending, expected):
    stress = {"mean_axial_normal_stress_n_mm2": mean, "bending_normal_stress_extrema_n_mm2": bending}
    reference = {"Ft_mpa": 4., "Fc_star_mpa": 8., "Fb_star_mpa": 2.}
    result = section.normal_reference(stress, reference)
    assert result["mean_axial_normal_stress_mpa"] == mean
    assert result["largest_abs_bending_normal_stress_mpa"] == max(abs(bending[0]), abs(bending[1]))
    assert result["fully_braced_linear_normal_CD1_reference_index"] == pytest.approx(expected)
    assert result["exceeds_conditional_normal_reference"] is (expected > 1.)
    assert result["local_hole_notch_fracture_restraint_or_complete_resistance"] is None


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize("component", ["axial", "bending_first", "bending_last"])
def test_normal_comparison_rejects_nonfinite_components(bad, component):
    stress = {"mean_axial_normal_stress_n_mm2": 0., "bending_normal_stress_extrema_n_mm2": [0., 1.]}
    if component == "axial":
        stress["mean_axial_normal_stress_n_mm2"] = bad
    else:
        stress["bending_normal_stress_extrema_n_mm2"][0 if component == "bending_first" else 1] = bad
    with pytest.raises(ValueError, match="finite normal"):
        section.normal_reference(stress, {"Ft_mpa": 4., "Fc_star_mpa": 4., "Fb_star_mpa": 4.})
