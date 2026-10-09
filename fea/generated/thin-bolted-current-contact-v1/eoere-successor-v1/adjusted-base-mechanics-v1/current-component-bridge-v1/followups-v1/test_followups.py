"""Tiny pure known answers and source/CLI boundaries; no genuine field run."""
import importlib.util
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

OWN = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("current_followup_test_subject", OWN / "followups.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + "\n")
    return m.digest(path.read_bytes())


@pytest.fixture
def tiny(tmp_path, monkeypatch):
    c = m._consumer()
    plan = c._load_plan()
    field = {"schema": c.FIELD_SCHEMA, "state_id": "synthetic-state", "case_id": "synthetic-case",
             "accessory_placement": "synthetic-placement", "release": c.RELEASE,
             "source_inputs": {"geometry": {"report": plan.ARTIFACTS["geometry"], "source_manifest": plan.ARTIFACTS["manifest"],
                                             "cached_source_export": plan.ARTIFACTS["descriptors"]}},
             "current_execution": {"geometry": plan.ARTIFACTS["geometry"]}}
    receipt = {"schema": c.ADMISSION_SCHEMA, c.SUCCESS: True}
    fp, rp = tmp_path / "tiny.json", tmp_path / "admission.json"
    fsha, rsha = write(fp, field), write(rp, receipt)
    events = []

    def gate(raw, receipt, **kwargs):
        events.append("gate")
        return json.loads(raw), {}

    def contract(actual, source_plan):
        events.append("metadata")
        assert actual == field
        return {"source_sha256": {}}, {}

    def reduce(actual, field_path, consumer, source_plan, pins, current_contract):
        events.append("rich_reducer")
        assert consumer is c and actual == field and field_path == fp
        return {"synthetic_only": True}

    monkeypatch.setattr(c, "_load_gate", lambda plan: SimpleNamespace(require_admitted_payload=gate))
    monkeypatch.setattr(c, "_current_contract", contract)
    monkeypatch.setattr(m, "_consumer", lambda: c)
    monkeypatch.setattr(m, "_reduce", reduce)
    return SimpleNamespace(c=c, field=field, receipt=receipt, fp=fp, rp=rp, fsha=fsha, rsha=rsha, events=events)


def call(t, **kwargs):
    return m.consume(t.fp, t.rp, expected_field_sha256=kwargs.pop("fsha", t.fsha),
                     expected_receipt_sha256=kwargs.pop("rsha", t.rsha), **kwargs)


def test_current_gate_then_metadata_then_rich_reducer(tiny):
    result = call(tiny)
    assert tiny.events == ["gate", "metadata", "rich_reducer"]
    assert result["raw_field_sha256"] == tiny.fsha and result["field_admission_receipt_sha256"] == tiny.rsha
    assert result["field_schema"] == tiny.c.FIELD_SCHEMA and result["state_id"] == tiny.field["state_id"]
    assert result["complete_joint_resistance"] is None and result["release"] == m.RELEASE
    assert result["current_source_manifest"] == tiny.c._load_plan().ARTIFACTS["manifest"]


@pytest.mark.parametrize("kwargs", [{"fsha": "0"*64}, {"rsha": "0"*64}, {"admission_sha256": "0"*64}])
def test_wrong_bytes_or_gate_cannot_reach_reducer(tiny, kwargs):
    with pytest.raises(ValueError):
        call(tiny, **kwargs)
    assert tiny.events == []


@pytest.mark.parametrize("mutation", [
    lambda f: f.update(schema="old_schema"),
    lambda f: f["source_inputs"]["geometry"].update(scene={"path": "old-scene", "sha256": "0"*64}),
    lambda f: f["source_inputs"]["geometry"].update(report={"path": "old-report", "sha256": "0"*64}),
    lambda f: f.update(release={**m.RELEASE, "structural_released": True}),
])
def test_old_geometry_alias_or_release_rejects_before_reducer(tiny, mutation):
    mutation(tiny.field)
    with pytest.raises(ValueError):
        call(tiny, fsha=write(tiny.fp, tiny.field))
    assert tiny.events == []


def test_admission_and_metadata_failure_prevent_reducer(tiny, monkeypatch):
    def reject(*args, **kwargs):
        tiny.events.append("gate")
        raise ValueError("synthetic own admission failure")
    monkeypatch.setattr(tiny.c, "_load_gate", lambda plan: SimpleNamespace(require_admitted_payload=reject))
    with pytest.raises(ValueError, match="own admission"):
        call(tiny)
    assert tiny.events == ["gate"]


def test_reducer_may_not_mutate_admitted_payload(tiny, monkeypatch):
    def mutate(field, *args):
        field["case_id"] = "foreign-case"
        return {}
    monkeypatch.setattr(m, "_reduce", mutate)
    with pytest.raises(ValueError, match="changed the admitted field"):
        call(tiny)


@pytest.fixture
def metadata():
    c = m._consumer()
    plan = c._load_plan()
    exported = json.loads(plan.checked_bytes(plan.ARTIFACTS["descriptors"]))
    geometry = json.loads(plan.checked_bytes(plan.ARTIFACTS["geometry"]))
    parent = json.loads(plan.checked_bytes(plan.ARTIFACTS["parent_geometry"]))
    # Metadata-only dimensional fixture, not a manufactured/admitted force field.
    field = {"source_inputs": {"shafts": exported["shafts"], "fitting_poses": exported["fitting_poses"]},
             "fitting_operator_descriptors": [{"body": p["id"], "own_fitting_scenario": {
                 "arm_length_mm": 88.9, "width_mm": 88.9, "thickness_mm": 6.35, "factory_hole_diameter_mm": 10.}}
                 for p in exported["fitting_poses"]]}
    return field, geometry, parent, plan.ARTIFACTS


def test_current_washer_composition_has_three_truthful_sources(metadata):
    field, geometry, parent, refs = metadata
    result = m.washer_geometry(*metadata)
    assert result["axes"] == geometry["axes"] and result["service_cuts"] == parent["service_cuts"]
    assert len(result["service_cuts"]) == 27 and result["scenario"]["thickness_mm"] == 6.35
    assert result["source_composition"]["service_cuts"] == refs["parent_geometry"]
    assert result["extension_report_contains_service_cuts_or_fitting_scenario"] is False
    assert result["source_composition"]["fitting_dimensions"]["own_operator_descriptors_canonical_sha256"] == m.canonical(field["fitting_operator_descriptors"])
    assert "service_cuts" not in geometry and "scenario" not in geometry
    counts = Counter((sum(s["kind"] == "wood" for s in shaft["surfaces"]),
                      sum(s["kind"] == "steel" for s in shaft["surfaces"])) for shaft in field["source_inputs"]["shafts"])
    assert counts == {(1, 1): 76, (2, 0): 16, (1, 2): 4, (2, 1): 4}


@pytest.mark.parametrize("mutate, match", [
    (lambda f,g,p,r: p["service_cuts"].pop(), "27 v3 service"),
    (lambda f,g,p,r: g["parent_geometry"].update(base=r["geometry"]), "exact v3 parent"),
    (lambda f,g,p,r: f["source_inputs"]["shafts"][0]["source_axis"].update(grip_mm=0), "current axes differ"),
    (lambda f,g,p,r: f["fitting_operator_descriptors"][0]["own_fitting_scenario"].update(thickness_mm=6.), "dimensional scenario"),
    (lambda f,g,p,r: f["fitting_operator_descriptors"].pop(), "all22"),
])
def test_current_washer_composition_rejects_incomplete_or_aliased_inputs(metadata, mutate, match):
    mutate(*metadata)
    with pytest.raises(ValueError, match=match):
        m.washer_geometry(*metadata)


@pytest.fixture(scope="module")
def methods():
    c = m._consumer()
    plan = c._load_plan()
    pins = {}
    m._materials(c, plan, pins)
    return m._methods(c, plan, pins), c, plan, pins


def test_exact_frozen_steel_and_washer_known_answers(methods):
    functions, _, _, _ = methods
    assert functions.steel_known(functions.net)["same_point_force_and_free_couple_transport"] is True
    assert functions.washer["known_checks"]()["inverse_thickness_squared_plate_stress"] is True
    land = {"source_nominal_outer_landing_full": True}
    ring = functions.washer["scenario_metrics"](100, 10, 20, 2, 7, 10, "wood", land, 0.)
    assert ring["uniform_supported_ring_mean_mpa_geometric_diagnostic"] == pytest.approx(100/(math.pi*75))
    assert ring["combined_washer_strength_index"] is None and ring["physical_contact_pressure_bound_mpa"] is None


def test_tiny_timber_modes_and_signed_grain_known_answers(methods):
    functions, _, _, _ = methods
    reference = functions.ws["wood_steel_single_shear_reference"](
        bolt_full_body_diameter_in=.375, bolt_thread_root_diameter_in=.3,
        wood_thread_bearing_length_in=0, steel_thread_bearing_length_in=0,
        bolt_bending_yield_psi=92000, steel_bearing_psi=87000,
        wood_bearing_length_in=1.5, steel_thickness_in=.25, grain_load_angle_degrees=0.)
    assert reference["wood_bearing_psi"] == 5600.
    assert set(reference["reference_values_lbf"]) == {"Im", "Is", "II", "IIIm", "IIIs", "IV"}
    assert reference["reference_values_lbf"]["Im"] == pytest.approx(1.5*.375*5600/4)
    assert reference["reference_lateral_lbf"] == min(reference["reference_values_lbf"].values())
    signed = functions.resolved([30,-40,0], [1,0,0], [0,0,1])
    assert signed["parallel_grain_signed_n"] == 30 and signed["lateral_n"] == 50
    assert abs(signed["cross_grain_signed_n"]) == 40
    assert functions.ww["dowel_bending_yield_moment_lb_in"](bending_yield_strength_psi=92000, effective_diameter_in=.3) == pytest.approx(414.)
    wood = functions.ww["wood_wood_single_shear_reference"](
        main_bearing_length_in=1.5, side_bearing_length_in=1.5,
        main_load_to_grain_degrees=0., side_load_to_grain_degrees=0.,
        main_bolt_axis_parallel_to_grain=False, side_bolt_axis_parallel_to_grain=False,
        bolt_full_body_diameter_in=.375, bolt_thread_root_diameter_in=.3,
        main_thread_bearing_length_in=0., side_thread_bearing_length_in=0.,
        bolt_bending_yield_moment_lb_in=92000*.375**3/6, gap_in=0.,
        reduction_terms=dict(zip(functions.timber.MODES, (4.,4.,3.6,3.2,3.2,3.2))))
    assert wood["reference_values_lbf"]["Im"] == pytest.approx(1.5*.375*5600/4)
    assert wood["reference_values_lbf"]["Im"] == wood["reference_values_lbf"]["Is"]
    with pytest.raises(ValueError, match="root cannot exceed"):
        functions.ws["wood_steel_single_shear_reference"](
            bolt_full_body_diameter_in=.375, bolt_thread_root_diameter_in=.4,
            wood_thread_bearing_length_in=0, steel_thread_bearing_length_in=0,
            bolt_bending_yield_psi=92000, steel_bearing_psi=87000,
            wood_bearing_length_in=1.5, steel_thickness_in=.25, grain_load_angle_degrees=0.)


def test_tiny_same_cut_bolt_body_and_root_selection(methods):
    functions, _, _, _ = methods
    shaft = {"body": "tiny-shaft", "diameter_mm": 10., "shaft_interval_mm": [0,60],
             "source_axis": {"nominal_under_head_length_mm": 80.}, "point": [0,0,0],
             "basis": [[1,0,0],[0,1,0],[0,0,1]]}
    values = [100,0,0,0,0,0]
    field = {"common_shaft_section_cut_actions": [{"axis_id": "tiny", "body": "tiny-shaft", "elastic_section_diameter_mm": 10.,
              "cuts": [{"station_from_axis_point_mm": s, "point_xyz_mm": [s,0,0],
                        "local_N_V1_V2_T_M1_M2_n_nmm": values} for s in (10.,40.)]}]}
    facts = {"material_source": {"minimum_yield_psi": 92000.},
             "diameters": [{"diameter_in": 10/25.4, "full_body_min_in": 10/25.4, "underhead_fillet_max_length_in": 2/25.4}],
             "bolts": [{"diameter_in": 10/25.4, "nominal_length_in": 80/25.4, "Lb_min_in": 20/25.4}]}
    root = {"profile_scenarios": [{"nominal_diameter_in": 10/25.4, "downward_4dp_design_floor_mm": 8.}]}
    row = functions.bolt({"tiny": shaft}, field, facts, root, functions.circles)[0]
    assert row["governing"]["region"] == "conditional_root_or_runout_floor"
    assert row["governing"]["same_cut_vm_envelope_mpa"] == pytest.approx(100/(math.pi*8**2/4))
    assert row["ordinary_UNC_guarantees_this_root_floor"] is False
    field["common_shaft_section_cut_actions"][0]["cuts"][0]["point_xyz_mm"] = [11,0,0]
    with pytest.raises(ValueError, match="same-cut datum"):
        functions.bolt({"tiny": shaft}, field, facts, root, functions.circles)


def test_private_function_second_read_guard_and_restore(methods, tmp_path, monkeypatch):
    functions, c, _, pins = methods
    source = tmp_path / "tiny.py"
    raw = b"def tiny():\n    return 7\n"
    source.write_bytes(raw)
    relative = str(source)
    pins[relative] = m.digest(raw)
    assert functions.pure(relative, ["tiny"])["tiny"]() == 7
    original_ast = functions.group.ast
    original_read = Path.read_bytes
    reads = []
    def racing_read(path):
        if path == source:
            reads.append(1)
            if len(reads) == 2:
                return b"def tiny():\n    return 99\n"
        return original_read(path)
    monkeypatch.setattr(Path, "read_bytes", racing_read)
    with pytest.raises(ValueError, match="immediately before AST parse"):
        functions.pure(relative, ["tiny"])
    assert functions.group.ast is original_ast
    pins.pop(relative)
    c.verify(pins)


def test_one_tiny_steel_owner_retains_own_points_couples_and_closure(methods):
    functions, _, _, _ = methods
    identity = {"state_id": "tiny", "case_id": "tiny-case", "accessory_placement": "tiny-placement"}
    body = "tiny-angle"
    field = {**identity, "common_shaft_bearing_actions": [], "shaft_end_capture_actions": [],
             "contact_actions": [], "common_shaft_steel_port_actions": [],
             "four_port_fitting_actions": [{"body": body, "load_projection": {"physical_load_rows": []}}]}
    descriptor = {"body": body, "own_fitting_scenario": {
        "fitting_basis_columns_xyz": [[1,0,0],[0,1,0],[0,0,1]], "heel_reference_xyz_mm": [0,0,0]}}
    for port in ("beam/minus", "beam/plus", "post/minus", "post/plus"):
        ids = []
        for sign in (-1,1):
            row = {**identity, "id": port+"/bearing/"+str(sign), "host": body, "flange": port,
                   "point_xyz_mm": [0,0,0], "force_on_second_xyz_n": [10*sign,0,0],
                   "moment_on_second_at_point_xyz_nmm": [0,2*sign,0]}
            field["common_shaft_bearing_actions"].append(row)
            ids.append(row["id"])
        cap = {**identity, "id": port+"/capture", "second": body, "end": {"flange": port},
               "point_xyz_mm": [0,0,0], "force_on_second_xyz_n": [0,0,0],
               "moment_on_second_at_point_xyz_nmm": [0,0,0]}
        field["shaft_end_capture_actions"].append(cap)
        for index in range(4):
            field["contact_actions"].append({**identity, "id": port+"/contact/"+str(index), "first": body,
                "kind": "flange_contact", "flange": port, "point_xyz_mm": [0,0,0], "force_on_first_xyz_n": [0,0,0],
                "moment_at_point_model_xyz_nmm": [0,0,0], "compression_n": 0})
        field["common_shaft_steel_port_actions"].append({"angle_id": body, "own_bearing_points": ids,
            "own_end_captures": [cap["id"]], "point_xyz_mm": [0,0,0], "force_on_steel_xyz_n": [0,0,0],
            "moment_on_steel_at_point_xyz_nmm": [0,0,0]})
    result = functions.steel["own_loads"](field, descriptor)
    assert len(result[3]) == 28 and sum(abs(r["moment"][1]) for r in result[3]) == 16
    assert result[-1]["own_aggregate_max_error_n_nmm"] == 0
    field["common_shaft_bearing_actions"][0]["case_id"] = "foreign-case"
    with pytest.raises(ValueError, match="mixed state/case/placement"):
        functions.steel["own_loads"](field, descriptor)


@pytest.mark.parametrize("fails", [False, True])
def test_all_followup_callbacks_use_current_field_and_intake_restores(metadata, tmp_path, monkeypatch, fails):
    field, _, _, refs = metadata
    field.update(schema="synthetic-only", state_id="synthetic", case_id="tiny", accessory_placement="tiny")
    c = m._consumer()
    plan = c._load_plan()
    fp = tmp_path / "tiny-field.json"
    pins = {m.name(fp): write(fp, field)}
    calls = []
    old_intake = lambda _: pytest.fail("old intake called")
    timber = SimpleNamespace(intake=old_intake)

    def angle(actual, descriptor, net, scenario):
        assert actual is field and scenario in m.STEEL_SCENARIOS
        calls.append(scenario["id"])
        return {"bands": [None]*4, "integrity": {"point_loads_retained": 28}}

    def produce(_):
        manifest, actual, _facts, _roots, assessment, actual_pins, _group, _ws, _ww, _resolved = timber.intake(None)
        assert actual is field and assessment is None and actual_pins is pins
        assert manifest["files"] == {"field": m.name(fp)} and "current admitted" in manifest["calculation_scope"]
        calls.append("current_timber")
        if fails:
            raise ValueError("tiny timber failure")
        return {"shaft_components": [{"axis_id": str(i), "component": None if i < 8 else {}} for i in range(100)]}

    def washer(actual, composition, facts, actual_pins, authenticated):
        assert actual is field and actual_pins is pins and authenticated["raw_field_sha256"] == pins[m.name(fp)]
        assert composition["source_composition"]["service_cuts"] == refs["parent_geometry"]
        calls.append("current_washers")
        return {"preserved_first_tmp_sha256": {}, "first_tmp_bytes_currently_match": {}, "limits": ["old context"],
                "known_answer_checks": {"synthetic": True}}

    timber.produce = produce
    fake = SimpleNamespace(steel={"reduce_angle": angle, "summary": lambda angles: {"synthetic": len(angles)}},
        net=None, timber=timber, group=None, ws=None, ww=None, resolved=None, circles=None,
        bolt=lambda shafts, actual, facts, roots, circles: [{"axis_id": k, "governing": {"specified_material_first_yield_index": 2.}}
                                                         for k in shafts],
        washer={"calculate": washer}, steel_known=lambda net: {"synthetic": True})
    monkeypatch.setattr(m, "_methods", lambda *args: fake)
    if fails:
        with pytest.raises(ValueError, match="tiny timber failure"):
            m._reduce(field, fp, c, plan, pins, {"nominal_seat_geometry": {"synthetic": True}})
    else:
        result = m._reduce(field, fp, c, plan, pins, {"nominal_seat_geometry": {"synthetic": True}})
        assert len(result["shaft"]["first_yield_reference_exceedances"]) == 100
        assert len(result["missing_current_inputs"]["mixed_stacks"]) == 8
        assert result["washers"]["reviewed_nominal_seat_geometry"] == {"synthetic": True}
        assert result["washers"]["limits"][-1].startswith("Every diagnostic belongs")
        assert calls[-1] == "current_washers"
    assert calls.count("t6_r6") == calls.count("t6p35_r6p35") == 22 and timber.intake is old_intake


def test_material_source_closure_and_old_maps_remain_historical():
    c = m._consumer()
    plan = c._load_plan()
    pins = dict(plan.component_plan()["source_sha256"])
    preserved_evidence_pins = dict(pins)
    _, _, _, evidence = m._materials(c, plan, pins)
    assert len(evidence["root_evidence_maps"]) == 3
    assert all(r["historical_field_or_viewer_map_imported_as_current"] is False for r in evidence["root_evidence_maps"])
    assert evidence["delivered_hardware_inspected"] is False
    assert not any(path.endswith("a12-first-order-v2/field.json") for path in pins.keys() - preserved_evidence_pins.keys())


BOOT = """
import importlib.util, json, os, pathlib, sys, time
p, log, mode = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
s = importlib.util.spec_from_file_location('cli_fixture', p)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
def fake(*args, **kwargs):
    with log.open('a') as stream: stream.write('called\\n')
    if mode == 'fail': raise ValueError('tiny failure')
    if mode == 'exit': os._exit(17)
    time.sleep(.15)
    return {'state_id':'synthetic','case_id':'tiny','execution':{},'release':m.RELEASE}
m.consume = fake
m.main(sys.argv[4:])
"""


def cli(out):
    return ["--field", "unused.json", "--field-sha256", "0"*64, "--receipt", "unused-admission.json",
            "--receipt-sha256", "0"*64, "--out", str(out)]


def command(log, mode, out):
    return [sys.executable, "-B", "-c", BOOT, str(OWN / "followups.py"), str(log), mode, *cli(out)]


def test_actual_cli_dangling_link_reserves_before_callback(tmp_path):
    out, log = tmp_path / "out.json", tmp_path / "calls.txt"
    out.symlink_to(tmp_path / "absent.json")
    result = subprocess.run(command(log, "ok", out), text=True, capture_output=True, check=False)
    assert result.returncode == 1 and "FileExistsError" in result.stderr and not log.exists()


def test_actual_cli_same_output_competitors_call_once(tmp_path):
    out, log = tmp_path / "out.json", tmp_path / "calls.txt"
    attempts = [subprocess.Popen(command(log, "ok", out), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    for p in attempts:
        p.communicate(timeout=20)
    assert sorted(p.returncode for p in attempts) == [0,1] and log.read_text().splitlines() == ["called"]
    assert json.loads(out.read_bytes())["output_reservation"]["method"] == "exclusive-create-before-intake"


@pytest.mark.parametrize("mode, status, code", [("fail", "FAILED", 1), ("exit", "STARTED", 17)])
def test_actual_cli_failure_retains_reserved_record(tmp_path, mode, status, code):
    out, log = tmp_path / "out.json", tmp_path / "calls.txt"
    first = subprocess.run(command(log, mode, out), text=True, capture_output=True, check=False)
    assert first.returncode == code and json.loads(out.read_bytes())["status"] == status
    before = out.read_bytes()
    second = subprocess.run(command(log, "ok", out), text=True, capture_output=True, check=False)
    assert second.returncode == 1 and out.read_bytes() == before and log.read_text().splitlines() == ["called"]


def test_actual_unpatched_cli_missing_input_is_fail_retained(tmp_path):
    out = tmp_path / "out.json"
    result = subprocess.run([sys.executable, "-B", str(OWN / "followups.py"), *cli(out)], cwd=tmp_path,
                            text=True, capture_output=True, check=False)
    record = json.loads(out.read_bytes())
    assert result.returncode == 1 and record["status"] == "FAILED" and record["release"] == m.RELEASE
    assert record["exception"]["type"] == "FileNotFoundError"


def test_module_import_has_no_numerical_or_CAD_import(tmp_path):
    code = """
import builtins,importlib.util,sys
original=builtins.__import__
def guarded(name,*a,**kw):
    if name.split('.')[0] in {'numpy','scipy','cadquery','OCP','mini_moonboard'}: raise AssertionError(name)
    return original(name,*a,**kw)
builtins.__import__=guarded
s=importlib.util.spec_from_file_location('source_only_import',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
assert m.GATE_SHA=='4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643'
"""
    subprocess.run([sys.executable, "-B", "-c", code, str(OWN / "followups.py")], cwd=tmp_path, check=True, capture_output=True)

