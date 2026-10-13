"""Independent spatial statics and continuous-extremum known answers."""

import copy
import math

import numpy as np
import pytest

from scripts import eoere_mixed_stack_yield as trial


def surface(low, high, q0, slope=(0., 0., 0.)):
    return {"low": low, "high": high, "q0": np.array(q0, dtype=float), "slope": np.array(slope, dtype=float)}


def test_uniform_simply_supported_beam_has_interior_vector_moment_maximum():
    segments, force, moment = trial.bending_field(
        [1., 0., 0.], [0., 10.], [surface(0., 10., [0., 1., 0.])],
        [{"s": 0., "force": [0., -5., 0.]}, {"s": 10., "force": [0., -5., 0.]}], [])
    witness = segments[0]["maximum_bending"]
    assert witness["station_mm"] == pytest.approx(5.)
    assert witness["vector"] == pytest.approx([0., 0., -12.5])
    assert witness["magnitude"] == pytest.approx(12.5)
    assert force == pytest.approx([0., 0., 0.])
    assert moment == pytest.approx([0., 0., 0.])


def test_affine_load_cubic_search_finds_both_stationary_points():
    segments, force, moment = trial.bending_field(
        [1., 0., 0.], [0., 10.], [surface(0., 10., [0., -10., 0.], [0., 2., 0.])],
        [{"s": 0., "force": [0., 50./3., 0.]}, {"s": 10., "force": [0., -50./3., 0.]}], [])
    witness = segments[0]["maximum_bending"]
    station = 5.-5./math.sqrt(3.)
    value = 50./3.*station-5.*station**2+station**3/3.
    assert witness["magnitude"] == pytest.approx(value)
    # Stationary squared norms include zero-moment points as well as maxima.
    assert witness["stationary_points_checked"] >= 2
    assert min(abs(witness["station_mm"]-s) for s in [station, 10.-station]) < 1e-7
    assert force == pytest.approx([0., 0., 0.])
    assert moment == pytest.approx([0., 0., 0.], abs=1e-12)


def test_gap_point_couple_and_diameter_event_are_retained():
    segments, force, moment = trial.bending_field(
        [1., 0., 0.], [0., 10.],
        [surface(0., 4., [0., 1., 0.]), surface(6., 10., [0., -1., 0.])],
        [{"s": 10., "force": [0., 0., 0.], "couple": [0., 0., 24.]}], [5.])
    assert [s["interval_mm"] for s in segments] == [[0., 4.], [4., 5.], [5., 6.], [6., 10.]]
    assert force == pytest.approx([0., 0., 0.])
    assert moment == pytest.approx([0., 0., 0.], abs=1e-12)
    assert segments[-1]["maximum_bending"]["magnitude"] == pytest.approx(24.)


def test_outside_head_load_is_transported_to_underhead_section():
    segments, force, moment = trial.bending_field(
        [1., 0., 0.], [0., 10.], [], [{"s": -2., "force": [0., 3., 4.]}], [])
    assert segments[0]["moment_coefficients_unit_interval_nmm"][0] == pytest.approx([0., -8., 6.])
    assert force == pytest.approx([0., 3., 4.])
    assert moment == pytest.approx([0., -48., 36.])


def test_oblique_three_dimensional_vector_polynomial_interior_peak():
    direction = np.array([1., 2., -3.])/math.sqrt(14.)
    result = trial.peak_norm(np.array([0.*direction, direction, 0.*direction, -direction]))
    assert result["fraction"] == pytest.approx(1./math.sqrt(3.))
    assert result["magnitude"] == pytest.approx(2./(3.*math.sqrt(3.)))
    assert result["vector"] == pytest.approx(direction*2./(3.*math.sqrt(3.)))
    assert trial.peak_norm([direction])["magnitude"] == pytest.approx(1.)
    assert trial.peak_norm([[0., 0., 0.]])["magnitude"] == 0.


def test_noncollinear_vector_peak_is_not_a_component_extremum():
    result = trial.peak_norm([[0., 1., 0.], [0., 0., 2.], [0., -1., -1.]])
    assert result["fraction"] == pytest.approx(.5)
    assert result["magnitude"] == pytest.approx(math.sqrt(1.125))
    assert result["vector"] == pytest.approx([0., .75, .75])


def test_independent_orthogonal_force_and_couple_find_vector_beam_peak():
    segments, force, moment = trial.bending_field(
        [1., 0., 0.], [0., 1.], [surface(0., 1., [0., -2., 2.])],
        [{"s": 0., "force": [0., 2., 0.], "couple": [0., -1., 0.]},
         {"s": 1., "force": [0., 0., -2.], "couple": [0., 0., 1.]}], [])
    witness = segments[0]["maximum_bending"]
    assert witness["station_mm"] == pytest.approx(.5)
    assert witness["vector"] == pytest.approx([0., .75, .75])
    assert witness["magnitude"] == pytest.approx(math.sqrt(1.125))
    assert force == pytest.approx([0., 0., 0.])
    assert moment == pytest.approx([0., 0., 0.])


def fixture():
    shaft = {"axis_id": "mixed", "point": [0., 0., 0.], "basis": [[1., 0., 0.]],
             "ends": [{"end": "head", "pressure_face_s_mm": 0.}], "shaft_interval_mm": [0., 10.],
             "surfaces": [{"host": "wood-a", "kind": "wood", "interval_mm": [0., 4.]},
                          {"host": "steel", "kind": "steel", "interval_mm": [4., 6.]},
                          {"host": "wood-b", "kind": "wood", "interval_mm": [6., 10.]}]}
    component = {"thread_window": {"catalog_min_body_in": .369, "purchase_design_root_floor_in": .2881,
                                    "catalog_Lb_min_mm": 5.}}
    rows = []
    for i, (s, density) in enumerate(zip(shaft["surfaces"], [-1., 4., -1.], strict=True)):
        low, high = s["interval_mm"]
        rows.append({"axis_id": "mixed", "surface_index": i, "host": s["host"], "kind": s["kind"],
                     "interval_from_axis_point_mm": [low, high], "lateral_force_on_host_xyz_n": [0., density*(high-low), 0.],
                     "moment_on_host_about_interval_center_xyz_nmm": [0., 0., 0.],
                     "affine_endpoint_line_density_vectors_n_mm": [[0., density, 0.], [0., density, 0.]],
                     "affine_trial_peak_line_density_n_mm": abs(density)})
    return shaft, component, rows


def test_piecewise_minimum_body_root_and_raw_bearing_are_separate_from_capacity():
    shaft, component, rows = fixture()
    result = trial.check_stack(shaft, component, rows, [])
    assert result["catalog_body_to_purchase_root_transition_s_mm"] == 5.
    assert [s["interval_mm"] for s in result["continuous_bending_segments"]] == [[0., 4.], [4., 5.], [5., 6.], [6., 10.]]
    assert [s["reference_diameter_mm"] for s in result["continuous_bending_segments"]] == pytest.approx([9.3726, 9.3726, 7.31774, 7.31774])
    assert result["worst_raw_bending_trial"]["maximum_bending"]["station_mm"] == 5.
    assert result["worst_raw_bending_trial"]["maximum_bending"]["magnitude"] == 10.
    bearing = result["raw_bearing_trials"]
    assert [r["bearing_reference_mpa"] for r in bearing] == pytest.approx([25.5106020, 555., 28.6132428], rel=1e-7)
    assert [r["raw_bearing_reference_n_mm"] for r in bearing] == pytest.approx([239.10066816, 4061.3457, 209.38427112], rel=1e-9)
    assert [s["raw_plastic_moment_reference_nmm"] for s in result["continuous_bending_segments"]] == pytest.approx(
        [87043.39229299, 87043.39229299, 41427.28619035, 41427.28619035], rel=1e-9)
    assert result["maximum_raw_material_trial_index"] == pytest.approx(1./209.38427112, rel=1e-9)
    assert result["compatible_bearing_or_adjusted_ASD_capacity"] is None
    assert result["complete_joint_resistance"] is None


@pytest.mark.parametrize("scale,within", [(209.38427112*.999, True), (209.38427112*1.001, False)])
def test_proportional_trial_crosses_raw_material_reference(scale, within):
    shaft, component, rows = fixture()
    for row in rows:
        row["affine_endpoint_line_density_vectors_n_mm"] = [(np.array(q)*scale).tolist() for q in row["affine_endpoint_line_density_vectors_n_mm"]]
        row["lateral_force_on_host_xyz_n"] = (np.array(row["lateral_force_on_host_xyz_n"])*scale).tolist()
        row["affine_trial_peak_line_density_n_mm"] *= scale
    result = trial.check_stack(shaft, component, rows, [])
    assert result["affine_trial_within_declared_raw_material_references"] is within
    assert result["maximum_raw_material_trial_index"] == pytest.approx(scale/209.38427112, rel=1e-9)


@pytest.mark.parametrize("factor,within", [(.999, True), (1.001, False)])
def test_bending_governed_stack_uses_every_segment_moment_reference(factor, within):
    shaft, component, rows = fixture()
    # Lengthening the independent three-block beam makes bolt bending govern.
    # For q=[1,-4,1], M=[s^2/2, ...] reaches 100000 Nmm at s=500 mm.
    shaft["shaft_interval_mm"] = [0., 1000.]
    component["thread_window"]["catalog_Lb_min_mm"] = 500.
    load_scale = 41427.28619035/100000.*factor
    for member, row in zip(shaft["surfaces"], rows, strict=True):
        member["interval_mm"] = [s*100. for s in member["interval_mm"]]
        row["interval_from_axis_point_mm"] = member["interval_mm"].copy()
        row["affine_endpoint_line_density_vectors_n_mm"] = [
            [x*load_scale for x in q] for q in row["affine_endpoint_line_density_vectors_n_mm"]]
        row["lateral_force_on_host_xyz_n"] = [x*100.*load_scale for x in row["lateral_force_on_host_xyz_n"]]
        row["affine_trial_peak_line_density_n_mm"] *= load_scale
    result = trial.check_stack(shaft, component, rows, [])
    for segment, moment, reference in zip(result["continuous_bending_segments"],
            [80000., 100000., 100000., 80000.],
            [87043.39229299, 87043.39229299, 41427.28619035, 41427.28619035], strict=True):
        assert segment["maximum_bending"]["magnitude"] == pytest.approx(moment*load_scale)
        assert segment["raw_trial_utilization"] == pytest.approx(moment*load_scale/reference, rel=1e-9)
    assert result["worst_raw_bending_trial"]["maximum_bending"]["station_mm"] == pytest.approx(500.)
    assert result["maximum_raw_material_trial_index"] == pytest.approx(factor, rel=1e-9)
    assert result["affine_trial_within_declared_raw_material_references"] is within


@pytest.mark.parametrize("mutation", ["identity", "force", "couple", "axial", "peak", "unbalanced"])
def test_reject_inconsistent_surface_or_equilibrium(mutation):
    shaft, component, rows = fixture()
    loads = []
    if mutation == "identity":
        rows[1]["host"] = "other"
    elif mutation == "force":
        rows[1]["lateral_force_on_host_xyz_n"][1] += 1.
    elif mutation == "couple":
        rows[1]["moment_on_host_about_interval_center_xyz_nmm"][2] = 1.
    elif mutation == "axial":
        rows[1]["affine_endpoint_line_density_vectors_n_mm"][0][0] = 1.
    elif mutation == "peak":
        rows[1]["affine_trial_peak_line_density_n_mm"] = 1.
    else:
        loads = [{"point_xyz_mm": [1., 0., 0.], "force_xyz_n": [0., 1., 0.]}]
    with pytest.raises(ValueError):
        trial.check_stack(shaft, component, rows, loads)


def test_spatial_rotation_preserves_complete_trial_with_nonzero_couple():
    shaft, component, rows = fixture()
    # Unequal endpoint bearing adds a real couple in each outside member;
    # reversing it on the other outside member preserves complete equilibrium.
    for row, sign in [(rows[0], 1.), (rows[2], -1.)]:
        row["affine_endpoint_line_density_vectors_n_mm"] = [[0., -1.-sign*.2, 0.], [0., -1.+sign*.2, 0.]]
        row["moment_on_host_about_interval_center_xyz_nmm"] = [0., 0., sign*.4*16./12.]
        row["affine_trial_peak_line_density_n_mm"] = 1.2
    first = trial.check_stack(shaft, component, rows, [])
    rotated_shaft, rotated_rows = copy.deepcopy(shaft), copy.deepcopy(rows)
    rotation = np.array([[1., 2., 2.], [2., 1., -2.], [-2., 2., -1.]])/3.
    assert np.linalg.det(rotation) == pytest.approx(1.)
    rotated_shaft["basis"][0] = (rotation @ shaft["basis"][0]).tolist()
    for row in rotated_rows:
        for key in ["lateral_force_on_host_xyz_n", "moment_on_host_about_interval_center_xyz_nmm"]:
            row[key] = (rotation @ row[key]).tolist()
        row["affine_endpoint_line_density_vectors_n_mm"] = [(rotation @ q).tolist() for q in row["affine_endpoint_line_density_vectors_n_mm"]]
    second = trial.check_stack(rotated_shaft, component, rotated_rows, [])
    assert second["maximum_raw_material_trial_index"] == pytest.approx(first["maximum_raw_material_trial_index"])
    assert second["worst_raw_bending_trial"]["maximum_bending"]["magnitude"] == pytest.approx(
        first["worst_raw_bending_trial"]["maximum_bending"]["magnitude"])


def run_fixture(monkeypatch):
    objects = {}

    def add(path, value):
        objects[path] = value
        return {"path": path, "sha256": trial.canonical_sha(value)}

    union_a = {"source-a": "a"*64}
    union_b = {"source-b": "b"*64}
    maps = [add("union-a", union_a), add("union-b", union_b)]
    force_cases, component_refs = [], []
    for i, case_id in enumerate(trial.SEQUENCE):
        shafts, components, trials, loads = [], [], [], []
        for j, aid in enumerate(trial.MIXED_IDS):
            shaft, component, rows = fixture()
            shaft.update({"axis_id": aid, "body": "shaft/"+aid, "metal_roles": [{"id": aid+"/mass"}]})
            component["axis_id"] = aid
            component["thread_window"]["catalog_Lb_min_mm"] = 2.+j
            gravity = .1*(i+1)+.001*j
            rows[1]["affine_endpoint_line_density_vectors_n_mm"] = [[0., 4.+gravity/2., 0.]]*2
            rows[1]["lateral_force_on_host_xyz_n"] = [0., 8.+gravity, 0.]
            rows[1]["affine_trial_peak_line_density_n_mm"] = 4.+gravity/2.
            for row in rows:
                row["axis_id"] = aid
            shafts.append(shaft)
            components.append(component)
            trials.extend(rows)
            loads.append({"id": case_id+"/"+aid, "body": shaft["body"],
                          "point_xyz_mm": [5., 0., 0.], "force_xyz_n": [0., gravity, 0.]})
        shafts.extend({"axis_id": "unused-"+str(n)} for n in range(92))
        components.extend({"axis_id": "unused-"+str(n)} for n in range(92))
        # An unrelated owner's load must never reach a mixed shaft.
        loads.append({"id": "foreign", "body": "other-owner", "point_xyz_mm": [0., 0., 0.], "force_xyz_n": [0., 2000., 0.]})
        field = {"case_id": case_id, "state_id": case_id+"-state", "body_applied_loads": loads,
                 "source_inputs": {"shafts": shafts}}
        field_ref = add(case_id+"/field", field)
        admission_ref = add(case_id+"/admission", {"admitted": True})
        force_cases.append({"case_id": case_id, "state_id": field["state_id"], "field": field_ref, "admission": admission_ref})
        data = {"case_id": case_id, "state_id": field["state_id"], "field": field_ref, "admission": admission_ref,
                "raw_field_canonical_sha256": trial.canonical_sha(field), "findings": {"timber": {"shaft_components": components}},
                "connected_mixed_stack_statics": {"mixed_axis_ids": trial.MIXED_IDS, "own_surface_trials": trials}}
        component_refs.append(add(case_id+"/components", data))
    release = {"fabrication": False}
    force_report = {"case_sequence": trial.SEQUENCE, "extra_grid": False,
                    "geometry_revision": "eoere-raised-kicker-screws-v1", "hardware_revision": "eoere-selected-purchase-hardware-v1",
                    "all_six_saved_field_admissions_pass": True, "geometry": {"path": "geometry", "sha256": "c"*64},
                    "hardware_model": {"path": "hardware", "sha256": "d"*64}, "release": release, "cases": force_cases,
                    "source_union": {"record": maps[0], "count": 1, "canonical_sha256": trial.canonical_sha(union_a)}}
    force_ref = add("force-report", force_report)
    component_report = {"case_sequence": trial.SEQUENCE, "extra_grid": False, "current_response": force_ref,
                        "geometry": force_report["geometry"], "hardware_model": force_report["hardware_model"], "release": release,
                        "source_union": {"record": maps[1], "count": 1, "canonical_sha256": trial.canonical_sha(union_b)}}
    component_ref = add("component-report", component_report)
    producer = {"path": str(trial.OWN.relative_to(trial.current.ROOT)), "sha256": trial.LOADED_SHA}
    inputs = {"producer": producer, "current_response": force_ref, "current_components": component_ref,
              "methods": [{"path": "method", "sha256": "e"*64}], "case_components": component_refs, "limits": ["raw references only"],
              "material_scenarios": {"body_and_purchase_root": "own selected catalog minimum body; own declared purchase root floor; neither is delivered observation",
                                     "bolt_Fyb_psi": 92000., "steel_Fu_mpa": 370., "wood_G": .5}}
    input_ref = add("closure-inputs", inputs)
    monkeypatch.setattr(trial.current, "ref", lambda _: input_ref)
    monkeypatch.setattr(trial.current, "read", lambda ref: objects[ref["path"]])
    monkeypatch.setattr(trial.current, "manifest", lambda: {"release": release})
    verified = []
    monkeypatch.setattr(trial.current, "verify", lambda pins: verified.append(copy.deepcopy(pins)))
    expected = {**union_a, **union_b, **{r["path"]: r["sha256"] for r in
                [input_ref, producer, force_ref, component_ref, *inputs["methods"], *component_refs, *maps]}}
    return objects, inputs, verified, expected


def test_successful_run_routes_six_own_states_gravity_and_exact_source_union(monkeypatch):
    _, _, verified, expected = run_fixture(monkeypatch)
    result = trial.run()
    assert verified == [expected, expected]
    assert [c["case_id"] for c in result["cases"]] == trial.SEQUENCE
    assert [c["state_id"] for c in result["cases"]] == [c+"-state" for c in trial.SEQUENCE]
    assert all([r["axis_id"] for r in c["mixed_stacks"]] == trial.MIXED_IDS for c in result["cases"])
    assert sum(len(c["mixed_stacks"]) for c in result["cases"]) == 48
    assert len({c["mixed_stacks"][0]["worst_raw_bending_trial"]["maximum_bending"]["magnitude"] for c in result["cases"]}) == 6
    assert all(r["lateral_force_closure_error_n"] < 1e-10 for c in result["cases"] for r in c["mixed_stacks"])
    for case in result["cases"]:
        for j, row in enumerate(case["mixed_stacks"]):
            transition, root = 2.+j, 7.31774
            assert row["catalog_body_to_purchase_root_transition_s_mm"] == transition
            for segment in row["continuous_bending_segments"]:
                diameter = 9.3726 if segment["interval_mm"][1] <= transition else root
                assert segment["reference_diameter_mm"] == pytest.approx(diameter)
                assert segment["raw_trial_utilization"] == pytest.approx(
                    segment["maximum_bending"]["magnitude"]/(634.3176709714892*diameter**3/6.))
            # The declared 0.2881-inch roots give Fe_perp=4150 psi.
            assert row["maximum_raw_material_trial_index"] == pytest.approx(1./(28.613242766647204*root))
    assert result["complete_joint_resistance"] is None
    assert result["structural_acceptance"] is False


@pytest.mark.parametrize("mutation", ["pre_drift", "post_drift", "state", "swapped_case", "admission", "missing_gravity",
                                      "five_cases", "duplicate_case", "reversed_cases", "duplicate_state",
                                      "missing_material", "changed_fyb", "changed_fu", "changed_G"])
def test_run_rejects_bad_intake_and_post_calculation_drift(monkeypatch, mutation):
    objects, inputs, _, _ = run_fixture(monkeypatch)
    calculations, verifications = [], []
    original = trial.check_stack

    def calculate(*args):
        calculations.append(args[0]["axis_id"])
        return original(*args)

    def verify(_):
        verifications.append(True)
        if mutation == "pre_drift" or (mutation == "post_drift" and len(verifications) == 2):
            raise ValueError("changed frozen source")

    monkeypatch.setattr(trial, "check_stack", calculate)
    monkeypatch.setattr(trial.current, "verify", verify)
    first = trial.SEQUENCE[0]
    if mutation == "state":
        objects[first+"/components"]["state_id"] = "foreign"
    elif mutation == "swapped_case":
        inputs["case_components"] = inputs["case_components"][::-1]
    elif mutation == "admission":
        objects["force-report"]["all_six_saved_field_admissions_pass"] = False
    elif mutation == "missing_gravity":
        objects[first+"/field"]["body_applied_loads"].pop(0)
        objects[first+"/components"]["raw_field_canonical_sha256"] = trial.canonical_sha(objects[first+"/field"])
    elif mutation == "five_cases":
        objects["force-report"]["cases"].pop()
        inputs["case_components"].pop()
    elif mutation == "duplicate_case":
        objects["force-report"]["cases"][-1] = objects["force-report"]["cases"][0]
        inputs["case_components"][-1] = inputs["case_components"][0]
    elif mutation == "reversed_cases":
        objects["force-report"]["cases"].reverse()
        inputs["case_components"].reverse()
    elif mutation == "duplicate_state":
        second = trial.SEQUENCE[1]
        state = objects[first+"/field"]["state_id"]
        objects["force-report"]["cases"][1]["state_id"] = state
        objects[second+"/field"]["state_id"] = objects[second+"/components"]["state_id"] = state
        objects[second+"/components"]["raw_field_canonical_sha256"] = trial.canonical_sha(objects[second+"/field"])
    elif mutation == "missing_material":
        inputs.pop("material_scenarios")
    elif mutation.startswith("changed_"):
        key, value = {"changed_fyb": ("bolt_Fyb_psi", 1000.), "changed_fu": ("steel_Fu_mpa", 1.), "changed_G": ("wood_G", .1)}[mutation]
        inputs["material_scenarios"][key] = value
    with pytest.raises(ValueError):
        trial.run()
    assert len(calculations) == (48 if mutation == "post_drift" else 0)
