"""Portable own-member reductions; no CAD rebuild or candidate solve."""

import copy
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import eoere_local_timber_closure as local
from scripts.thin_bolted_timber_demand_checks import member_cut_wrench


def cleat_fixture():
    shafts, surfaces = [], []
    for name, forces in [("eoere_cleat_left", [-10., -20., 7., 23.]),
                         ("eoere_cleat_right", [-100., -200., 80., 220.])]:
        for i, (y, force) in enumerate(zip([-130., -80., -130., -80.], forces, strict=True)):
            aid = name+str(i)
            shafts.append({"axis_id": aid, "basis": [[1., 0., 0.]], "bore_diameter_mm": 10.})
            surfaces.append({"receiver": name, "axis_id": aid,
                             "own_aggregate_point_xyz_mm": [7., y, 200.+100*i],
                             "own_force_xyz_n": [13., force, 17.]})
    field = {"source_inputs": {"shafts": shafts}, "contact_actions": [],
             "shaft_end_capture_actions": [], "panel_screw_actions": [], "body_applied_loads": []}
    return field, {"findings": {"timber": {"wood_surfaces": surfaces}}}


def opening_method():
    return local.component.load(local.OPENING, "test_actual_cleat_opening").opening_force


def test_two_cleats_keep_whole_own_bores_and_signed_opening():
    field, data = cleat_fixture()
    before = copy.deepcopy((field, data))
    rows = local.cleat_opening(field, data, opening_method())
    assert [r["necessary_integrated_Y_tension_under_fixed_actions_n"] for r in rows] == [3., 20.]
    assert rows[0]["whole_bore_supports_y_min_max_force_n"] == [
        [-135., -125., -10.], [-85., -75., -20.], [-135., -125., 7.], [-85., -75., 23.]]
    for row in rows:
        assert row["actual_cross_grain_fracture_resistance_n"] is None
        assert row["retained_X_axis_bolts_cross_this_Y_normal_plane"] is False
        assert row["force_only_lower_bound_disposes_couples_or_all_crack_planes"] is False
    assert (field, data) == before
    for row in data["findings"]["timber"]["wood_surfaces"]:
        row["own_force_xyz_n"][1] *= -1.
    assert [r["necessary_integrated_Y_tension_under_fixed_actions_n"]
            for r in local.cleat_opening(field, data, opening_method())] == [0., 0.]


@pytest.mark.parametrize("mutation", ["axis", "bore_crossing", "missing_bore", "equilibrium",
                                      "contact", "capture", "screw", "applied"])
def test_cleat_query_rejects_unaccounted_force_or_intersected_support(mutation):
    field, data = cleat_fixture()
    if mutation == "axis":
        field["source_inputs"]["shafts"][0]["basis"][0] = [0., 1., 0.]
    elif mutation == "bore_crossing":
        data["findings"]["timber"]["wood_surfaces"][0]["own_aggregate_point_xyz_mm"][1] = -105.85
    elif mutation == "missing_bore":
        data["findings"]["timber"]["wood_surfaces"].pop(0)
    elif mutation == "equilibrium":
        data["findings"]["timber"]["wood_surfaces"][0]["own_force_xyz_n"][1] += 1.
    elif mutation == "applied":
        field["body_applied_loads"] = [{"body": "eoere_cleat_right", "force_xyz_n": [0., 1., 0.]}]
    else:
        key = {"contact": "contact_actions", "capture": "shaft_end_capture_actions", "screw": "panel_screw_actions"}[mutation]
        field[key] = [{"first": "other", "second": "eoere_cleat_left", "force_on_first_xyz_n": [0., 1., 0.]}]
    with pytest.raises(ValueError):
        local.cleat_opening(field, data, opening_method())


def test_compression_census_uses_oblique_member_actions_gravity_and_event_sides():
    grain, start = np.array([.6, 0., .8]), np.array([6., 2., 8.])
    member = {"name": "oblique", "axis": grain.tolist(), "start": start.tolist(), "end": (start+grain*100.).tolist()}
    actions = {"oblique": [((start+grain*20.).tolist(), (grain*30.).tolist(), [1., 2., 3.]),
                            ((start+grain*70.).tolist(), (-grain*30.).tolist(), [-1., -2., -3.])]}
    gravity = {"oblique": ((start+grain*50.+[0., 3., 0.]).tolist(), [0., -20., 0.])}
    field = {"source_inputs": {"timber_rows": [member]}}
    gross = SimpleNamespace(own=SimpleNamespace(member_point_inputs=lambda f: (actions, gravity),
                            previous=SimpleNamespace(member_cut_wrench=member_cut_wrench)))
    before = copy.deepcopy((field, actions, gravity))
    row = local.compression_events(field, gross)[0]
    witness = row["most_compressive_action_event_witness"]
    assert row["action_event_side_candidate_count"] == 6
    assert witness["station_global_grain_projection_mm"] == pytest.approx(30.00001)
    assert witness["axial_tension_positive_n"] == pytest.approx(-30.)
    cut = witness["signed_same_cut_wrench"]
    assert cut["cut_point_xyz_mm"] == pytest.approx(start+grain*20.00001)
    assert cut["force_on_lower_portion_xyz_n"] == pytest.approx([-18., 4.000002, -24.])
    assert grain @ cut["moment_on_lower_portion_about_cut_xyz_nmm"] == pytest.approx(-3.)
    assert row["continuous_finished_stability_or_qualified_restraint"] is None
    assert (field, actions, gravity) == before


@pytest.mark.parametrize("drift", [None, "before", "after", "opening_before",
                                  "five_cases", "duplicate_case", "reversed_cases", "duplicate_state"])
def test_run_authenticates_sources_and_keeps_six_own_cut_inputs(monkeypatch, tmp_path, drift):
    current = local.current
    monkeypatch.setattr(current, "ROOT", tmp_path)

    def put(name, value):
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())
        return {"path": name, "sha256": current.sha(path)}

    producer = put("producer.py", b"local producer")
    monkeypatch.setattr(local, "OWN", tmp_path/producer["path"])
    monkeypatch.setattr(local, "LOADED_SHA", producer["sha256"])
    wrapper = put("targeted.py", b"targeted sections wrapper")
    monkeypatch.setattr(local.targeted, "__file__", str(tmp_path/wrapper["path"]))
    methods = {k: put(k+".py", k.encode()) for k in ["sections", "plane", "cuts"]}
    monkeypatch.setattr(local.targeted, "METHODS", methods)
    opening = put("opening.py", b"opening")
    monkeypatch.setattr(local, "OPENING", opening)
    dependency = put("dependency.py", b"dependency")
    monkeypatch.setattr(local.targeted, "IMPORT_CLOSURE", {dependency["path"]: dependency["sha256"]})
    brep = put("rail.brep", b"cached solid")
    member = {"name": "base_rail_top", "axis": [1., 0., 0.], "start": [0., 2., 3.], "end": [10., 2., 3.]}
    observation = {"id": member["name"], "source": brep, "volume_mm3": 10.}
    bindings, raw_refs, own_inputs = [], [], {}
    for i, case in enumerate(local.SEQUENCE):
        shafts = [{"axis_id": aid, "point": [station, 2., 3.], "basis": [[0., 1., 0.]],
                   "bore_diameter_mm": diameter, "surfaces": [{"host": member["name"]}]}
                  for aid, station, diameter in [("eoere_bolt_017", 5., 2.), ("eoere_bolt_018", 7., 1.)]]
        field = {"case_id": case, "state_id": "own-"+case,
                 "source_inputs": {"timber_rows": [member], "finished_body_observations": [observation], "shafts": shafts}}
        fref = put(case+"/field.json", field)
        aref = put(case+"/admission.json", {"own_case": case})
        bindings.append({"case_id": case, "state_id": field["state_id"], "field": fref, "admission": aref})
        data = {"case_id": case, "state_id": field["state_id"], "field": fref, "admission": aref,
                "raw_field_canonical_sha256": local.canonical_sha(field), "component_reductions": {
                    "fresh_gross_member_diagnostics": [{"member": member["name"], "witnesses": {"sufficient_shear_torsion": {
                        "gross_CD1_comparison": {"equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio": .1+i},
                        "station_global_grain_projection_mm": 4.5}}}]}}
        raw_refs.append(put(case+"/components.json", data))
        own_inputs[case] = ({member["name"]: {"axial": (-1.)**i*(20.+i), "shear": 30.+2*i, "couple": 40.+3*i}},
                            {member["name"]: ([2.+i, 3.+i, 4.+i], [0., -5.-i, 0.])})
    unions = [{"force-dependency": "a"*64}, {"component-dependency": "b"*64}]
    union_refs = [put("union"+str(i)+".json", value) for i, value in enumerate(unions)]
    common = {"case_sequence": local.SEQUENCE, "geometry_revision": "eoere-raised-kicker-screws-v1",
              "hardware_revision": "eoere-selected-purchase-hardware-v1", "extra_grid": False, "release": {"fabrication": False}}
    if drift == "five_cases":
        bindings.pop()
        raw_refs.pop()
    elif drift == "duplicate_case":
        bindings[-1], raw_refs[-1] = bindings[0], raw_refs[0]
    elif drift == "reversed_cases":
        bindings.reverse()
        raw_refs.reverse()
    elif drift == "duplicate_state":
        bindings[1]["state_id"] = bindings[0]["state_id"]
    force = {**common, "cases": bindings, "all_six_saved_field_admissions_pass": True,
             "source_union": {"record": union_refs[0], "count": 1, "canonical_sha256": local.canonical_sha(unions[0])}}
    fref = put("forces.json", force)
    cref = put("components.json", {**common, "current_response": fref,
                "source_union": {"record": union_refs[1], "count": 1, "canonical_sha256": local.canonical_sha(unions[1])}})
    parent = put("inputs-v2.json", {"current_response": fref, "current_components": cref, "case_components": raw_refs})
    monkeypatch.setattr(local, "PACKET", tmp_path)
    verify_calls = []
    required = current.join(*unions, local.targeted.IMPORT_CLOSURE,
                {r["path"]: r["sha256"] for r in [parent, fref, cref, *raw_refs, producer,
                 current.ref(local.targeted.__file__), opening, *methods.values(), *union_refs]})

    def verify(pins):
        verify_calls.append(copy.deepcopy(pins))
        assert all(pins.get(k) == v for k, v in required.items())
        current.require(current.sha(tmp_path/dependency["path"]) == dependency["sha256"], "fixture dependency drift")
        current.require(current.sha(tmp_path/opening["path"]) == opening["sha256"], "fixture opening helper drift")

    monkeypatch.setattr(current, "verify", verify)
    monkeypatch.setattr(local, "cleat_opening", lambda field, data, method: [
        {"field_case": field["case_id"], "component_case": data["case_id"]}])
    monkeypatch.setattr(local, "compression_events", lambda field, gross: [{"case": field["case_id"]}])
    cuts = []

    def cut(grain, low, high, origin, center, weight, actions):
        cuts.append((origin.copy(), center.copy(), weight.copy(), actions.copy()))
        return {"force_on_lower_portion_xyz_n": [actions["axial"], actions["shear"]+weight[1]*center[1], 0.],
                "couple": actions["couple"]+center[2]*weight[1]}

    face, transform, local_face = object(), object(), object()

    class Shape:
        def isValid(self): return True
        def Solids(self): return [self]
        def Volume(self): return 10.
        def intersect(self, other):
            assert other is face
            return SimpleNamespace(transformShape=lambda matrix: local_face if matrix is transform else None)

    imports = []

    def import_brep(path):
        imports.append(path)
        if drift == "after":
            (tmp_path/dependency["path"]).write_bytes(b"changed")
        return Shape()

    monkeypatch.setitem(sys.modules, "cadquery", SimpleNamespace(Shape=SimpleNamespace(importBrep=import_brep), Vector=lambda *v: list(v)))

    def stress(shape, properties, wrench):
        assert shape is local_face
        return {"mean_axial_normal_stress_n_mm2": wrench["force_on_lower_portion_xyz_n"][0]/properties["finished_area_mm2"],
                "bending_normal_stress_extrema_n_mm2": [-wrench["couple"]/100., wrench["couple"]/200.]}

    helpers = {"sections": SimpleNamespace(measure_section=lambda shape, origin, grain: {
                    "finished_area_mm2": 10.+origin[0], "basis_u_v_grain_xyz": [[0., 1., 0.], [0., 0., 1.], grain]},
                    rigid_matrix=lambda rows: transform, linear_normal_stress=stress),
               "plane": SimpleNamespace(_basis_matrix=lambda *args: SimpleNamespace(wrapped=SimpleNamespace(Value=lambda i,j: 1.)),
                    _plane_face=lambda *args: face),
               "cuts": SimpleNamespace(source_pins=dict,
                    rectangle=SimpleNamespace(nds=SimpleNamespace(adjusted_reference=lambda width: {
                        "Ft_mpa": 4., "Fc_star_mpa": 8., "Fb_star_mpa": 2., "Fv_mpa": 1.})),
                    own=SimpleNamespace(member_point_inputs=lambda field: own_inputs[field["case_id"]],
                    previous=SimpleNamespace(member_cut_wrench=cut))), "opening": SimpleNamespace(opening_force=None)}
    monkeypatch.setattr(local.component, "load", lambda ref, name: helpers[ref["path"].removesuffix(".py")])
    if drift == "before":
        (tmp_path/dependency["path"]).write_bytes(b"changed")
    if drift == "opening_before":
        (tmp_path/opening["path"]).write_bytes(b"changed")
    if drift:
        message = "fixture (dependency|opening helper) drift" if drift in ["before", "after", "opening_before"] else "exact ordered case bindings"
        with pytest.raises(ValueError, match=message):
            local.run()
        assert bool(imports) is (drift == "after")
        return
    result = local.run()
    assert result["top_rail_governing_gross_witness"]["case_id"] == "a1-rear"
    assert len(result["cases"]) == 6
    for row, binding, raw_ref in zip(result["cases"], bindings, raw_refs, strict=True):
        case = binding["case_id"]
        assert (row["case_id"], row["state_id"], row["field"], row["components"]) == (
            case, "own-"+case, binding["field"], raw_ref)
        assert row["cleat_opening"] == [{"field_case": case, "component_case": case}]
        assert row["compression_action_events"] == [{"case": case}]
    assert result["source_sha256"] == {**required, brep["path"]: brep["sha256"]}
    assert verify_calls == [required, result["source_sha256"], result["source_sha256"]]
    assert result["top_rail_bore_neighborhood"] == [
        {"axis_id": "eoere_bolt_017", "center_grain_station_mm": 5., "nominal_bore_radius_mm": 1.},
        {"axis_id": "eoere_bolt_018", "center_grain_station_mm": 7., "nominal_bore_radius_mm": .5}]
    assert [row["station_global_grain_projection_mm"] for row in result["top_rail_finished_sections"]] == pytest.approx(
        [3.99, 4.01, 4.5, 5., 5.99, 6.01, 6.49, 6.51, 7., 7.49, 7.51])
    assert len(cuts) == 66
    for section in result["top_rail_finished_sections"]:
        station, area = section["station_global_grain_projection_mm"], section["properties"]["finished_area_mm2"]
        for i, row in enumerate(section["case_comparisons"]):
            case = local.SEQUENCE[i]
            actions, (center, weight) = own_inputs[case][0][member["name"]], own_inputs[case][1][member["name"]]
            assert row["case_id"] == case and row["state_id"] == "own-"+case
            assert row["necessary_mean_shear_mpa"] == pytest.approx(abs(actions["shear"]+weight[1]*center[1])/area)
            assert row["linear_normal_stress"]["mean_axial_normal_stress_n_mm2"] == pytest.approx(actions["axial"]/area)
            assert row["linear_normal_stress"]["bending_normal_stress_extrema_n_mm2"] == pytest.approx(
                [-(actions["couple"]+center[2]*weight[1])/100., (actions["couple"]+center[2]*weight[1])/200.])
            mean = actions["axial"]/area
            bending = abs(actions["couple"]+center[2]*weight[1])/100.
            expected = (mean/4. if mean >= 0 else (mean/8.)**2)+bending/2.
            normal = row["fully_braced_normal_reference"]
            assert normal["mean_axial_normal_stress_mpa"] == pytest.approx(mean)
            assert normal["largest_abs_bending_normal_stress_mpa"] == pytest.approx(bending)
            assert normal["fully_braced_linear_normal_CD1_reference_index"] == pytest.approx(expected)
            assert normal["exceeds_conditional_normal_reference"] is (expected > 1.)
            assert normal["local_hole_notch_fracture_restraint_or_complete_resistance"] is None
        assert all(c[0] == [station, 2., 3.] for c in cuts if c[0][0] == station)
    assert result["finished_member_capacity"] is None
    assert result["structural_acceptance"] is False
    assert result["native_solve_CAD_rebuild_or_remedy_performed"] is False
