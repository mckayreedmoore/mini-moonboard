"""Inert source/ordering coupons; no actual field, admission or reducer runs."""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from types import SimpleNamespace

import pytest

SOURCE = Path(__file__).with_name("consume.py")
spec = importlib.util.spec_from_file_location("z180_component_inert_subject", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
REPO_ROOT = m.ROOT


def write(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return {"path": name, "sha256": m.digest(raw)}


@pytest.fixture
def tiny(tmp_path, monkeypatch):
    # Import only the frozen consumer's stdlib definitions and descriptor table.
    c = m.load(m.FROZEN["coarse"], {}, "z180_inert_descriptor_table")
    own = tmp_path / "consume.py"
    own.write_bytes(SOURCE.read_bytes())
    gate_path = tmp_path / "gate.py"
    gate_path.write_text("# Inert definition-loader stand-in, never an admission.\n")
    monkeypatch.setattr(m, "ROOT", tmp_path)
    monkeypatch.setattr(m, "OWN", own)
    monkeypatch.setattr(m, "GATE_PATH", gate_path)
    rows = {value: [] for value in c.DESCRIPTOR_KEYS.values()}
    rows["shafts"] = [{"axis_id": str(i), "source_axis": {"id": str(i), "point_xyz_mm": [0., 0., 200.]}}
                      for i in range(100)]
    rows["current_panel_machining_descriptors"] = {"features": []}
    parent = {**copy.deepcopy(rows), "source_sha256": {}}
    exported = copy.deepcopy(parent)
    exported["schema"] = "eoere_z180_geometry_delta_descriptors/v1"
    for row in exported["shafts"][:4]:
        row["source_axis"]["point_xyz_mm"][2] = 180.
    geometry = {"proposed_axes": [copy.deepcopy(s["source_axis"]) for s in exported["shafts"][:4]]}
    field = {"schema": m.FIELD_SCHEMA, "state_id": "inert-state", "case_id": "inert-case",
             "accessory_placement": "inert-placement", "release": dict(m.RELEASE)}
    t = SimpleNamespace(root=tmp_path, c=c, parent=parent, exported=exported, geometry=geometry,
                        finished={"scenarios": []}, field=field, receipt_extra={}, events=[])
    proof = tmp_path / "proof.bin"
    proof.write_bytes(b"inert exact source\n")
    parent["source_sha256"]["proof.bin"] = m.digest(proof.read_bytes())

    def freeze(*, source=True):
        refs = {"gate": {"path": "gate.py", "sha256": m.digest(gate_path.read_bytes())},
                "geometry": write(tmp_path, "layout.json", t.geometry),
                "parent_descriptors": write(tmp_path, "parent.json", t.parent),
                "finished_receivers": write(tmp_path, "finished.json", t.finished)}
        refs["manifest"] = write(tmp_path, "manifest.json", {"saved_finished_receiver_evidence": refs["finished_receivers"]})
        t.exported.update(geometry=refs["geometry"], manifest=refs["manifest"], parent_descriptors=refs["parent_descriptors"],
            source_sha256={**t.parent["source_sha256"], **{refs[k]["path"]: refs[k]["sha256"] for k in
                ("geometry", "manifest", "parent_descriptors", "finished_receivers")}})
        refs["descriptor"] = write(tmp_path, "descriptor.json", t.exported)
        refs["descriptor_review"] = write(tmp_path, "review.json", {
            "schema": "eoere_z180_geometry_descriptors_independent_review/v1",
            "success": "independent_z180_descriptor_source_checks_pass", "independent_z180_descriptor_source_checks_pass": True,
            "descriptor": refs["descriptor"], "release": dict(m.RELEASE)})
        if source:
            t.field["source_inputs"] = {key: copy.deepcopy(t.exported[value]) for key, value in c.DESCRIPTOR_KEYS.items()}
            t.field["source_inputs"].update(geometry={"report": refs["geometry"], "source_manifest": refs["manifest"],
                "cached_source_export": refs["descriptor"]}, source_sha256=dict(t.exported["source_sha256"]))
            t.field["current_execution"] = {"geometry": refs["geometry"]}
        fref = write(tmp_path, "field.json", t.field)
        receipt = {"schema": m.ADMISSION_SCHEMA, m.SUCCESS: True, "field_sha256": fref["sha256"],
                   "state_id": t.field["state_id"], **t.receipt_extra}
        aref = write(tmp_path, "admission.json", receipt)
        t.config = {"schema": "eoere_z180_component_consumer_inputs/v1", "sources": refs, "field": fref,
            "admission": aref, "state_id": "inert-state", "case_id": "inert-case",
            "ready_for_saved_field_consumption": True, "release": dict(m.RELEASE)}
        t.config_ref = write(tmp_path, "config.json", t.config)
        t.records = {"descriptor": t.exported, "parent_descriptors": t.parent, "geometry": t.geometry}
        return t.config_ref
    t.freeze = freeze
    freeze()

    @contextmanager
    def corrected(adapter):
        t.events.append("corrected_source_scope")
        try:
            yield adapter
        finally:
            t.events.append("source_scope_restored")

    def source_join(data):
        t.events.append("source_join")
        assert data is not None
        return {"cached_source_export": json.loads((tmp_path / "descriptor.json").read_bytes())}

    def original():
        return SimpleNamespace(GEOMETRY=t.config["sources"]["geometry"], SOURCE_MANIFEST=t.config["sources"]["manifest"],
                               PARENT_DESCRIPTOR=t.config["sources"]["parent_descriptors"], require_sources=source_join)

    def admitted(raw, receipt, *, admission_sha256):
        t.events.append("inert_gate_callback")
        assert admission_sha256 == t.config["sources"]["gate"]["sha256"]
        m.require(receipt["field_sha256"] == m.digest(raw) and receipt["state_id"] == t.field["state_id"], "wrong pair")
        if getattr(t, "during_gate", None):
            t.during_gate()
        actual = json.loads(raw)
        if getattr(t, "mutate_gate", False):
            actual["case_id"] = "foreign"
        return actual, {}

    gate = SimpleNamespace(require_admitted_payload=admitted, original=original, corrected_context=corrected)
    t.gate = gate
    def load(ref, pins, label):
        assert ref == t.config["sources"]["gate"]
        m.checked(ref, pins)
        t.events.append("gate_definitions")
        return gate
    monkeypatch.setattr(m, "load", load)

    def reduce(config, records, field, pins, gate, **kwargs):
        t.events.append("metadata")
        axes = m.source_contract(config, records, field, pins, gate, c)
        assert len(axes) == 100 and "axes" not in records["geometry"]
        t.events.append("inert_reducer_callback")
        assert field == t.field
        return {"inert_only": True}, {"nominal_seat_geometry": {"nominal_wood_seats": None}}
    monkeypatch.setattr(m, "reduce_admitted", reduce)
    return t


def call(t):
    return m.consume(t.root / "config.json", t.config_ref["sha256"])


def test_real_boundary_orders_exact_pair_then_corrected_source_join_then_callback(tiny):
    result = call(tiny)
    assert tiny.events == ["gate_definitions", "inert_gate_callback", "metadata", "corrected_source_scope",
                           "source_join", "source_scope_restored", "inert_reducer_callback"]
    assert result["field_schema"] == m.FIELD_SCHEMA and result["case_id"] == "inert-case"
    assert result["complete_joint_resistance"] is None and result["release"] == m.RELEASE
    assert result["unadopted_proposal"] and json.loads((tiny.root / "field.json").read_bytes()) == tiny.field


@pytest.mark.parametrize("mutation", ["old_field", "old_receipt", "wrong_pair", "scene", "wrong_case", "not_ready"])
def test_wrong_pairs_schemas_scene_and_readiness_stop_before_reducer(tiny, mutation):
    if mutation == "old_field":
        tiny.field["schema"] = "eoere_extended_cleat_fixed_floor_candidate/v1"
    elif mutation == "old_receipt":
        tiny.receipt_extra["schema"] = "eoere_extended_cleat_fixed_floor_independent_field_admission/v1"
    elif mutation == "wrong_pair":
        tiny.receipt_extra["field_sha256"] = "0"*64
    elif mutation == "wrong_case":
        tiny.field["case_id"] = "foreign"
    tiny.freeze()
    if mutation == "scene":
        tiny.field["source_inputs"]["geometry"]["scene"] = {"path": "old", "sha256": "0"*64}
        tiny.freeze(source=False)
    if mutation == "not_ready":
        tiny.config["ready_for_saved_field_consumption"] = False
        tiny.config_ref = write(tiny.root, "config.json", tiny.config)
    with pytest.raises(ValueError):
        call(tiny)
    assert "inert_reducer_callback" not in tiny.events


@pytest.mark.parametrize("mutation", ["duplicate_axis", "duplicate_parent_axis", "layout_only", "descriptor_join", "foreign_proposal"])
def test_full_descriptor_unique_axis_and_partial_layout_joins(tiny, mutation):
    if mutation == "duplicate_axis":
        tiny.exported["shafts"][-1] = copy.deepcopy(tiny.exported["shafts"][0])
    elif mutation == "duplicate_parent_axis":
        tiny.parent["shafts"].append(copy.deepcopy(tiny.parent["shafts"][0]))
    elif mutation == "layout_only":
        tiny.exported["schema"] = "eoere_lower_cleat_z180_geometry_patch/v1"
    elif mutation == "foreign_proposal":
        tiny.geometry["proposed_axes"][0]["point_xyz_mm"][2] = 170.
    tiny.freeze()
    if mutation == "descriptor_join":
        tiny.field["source_inputs"]["shafts"][0]["source_axis"]["point_xyz_mm"][2] = 200.
        tiny.freeze(source=False)
    with pytest.raises(ValueError):
        call(tiny)
    assert "inert_reducer_callback" not in tiny.events


@pytest.mark.parametrize("when", ["before", "during", "changed_payload"])
def test_source_drift_and_gate_payload_change_fail_closed(tiny, when):
    if when == "before":
        (tiny.root / "proof.bin").write_bytes(b"changed")
    elif when == "during":
        tiny.during_gate = lambda: (tiny.root / "proof.bin").write_bytes(b"changed")
    else:
        tiny.mutate_gate = True
    with pytest.raises(ValueError):
        call(tiny)
    assert "inert_reducer_callback" not in tiny.events


def test_duplicate_config_json_keys_rejected_without_gate(tiny):
    raw = (tiny.root / "config.json").read_bytes().replace(b'"ready_for_saved_field_consumption": true',
        b'"ready_for_saved_field_consumption": false, "ready_for_saved_field_consumption": true')
    (tiny.root / "config.json").write_bytes(raw)
    with pytest.raises(ValueError, match="duplicate JSON"):
        m.consume(tiny.root / "config.json", m.digest(raw))
    assert tiny.events == []


def seat_coupon():
    hosts = sorted(m.HOSTS) + ["unchanged"]
    shafts, old_shafts, observations, prior_observations, old_rows, annuli = [], [], [], [], [], []
    bodies = {}
    for host in hosts:
        body = {"path": host + ".brep", "sha256": "a"*64}
        old_body = {"path": "old-" + host + ".brep", "sha256": "b"*64} if host in m.HOSTS else body
        observations.append({"id": host, "source": body})
        prior_observations.append({"id": host, "source": old_body})
        if host in m.HOSTS:
            bodies[host] = copy.deepcopy(body)
        for i in range(4 if host in m.HOSTS else 96):
            aid = host + "/" + str(i)
            end = {"host": host, "end": "head", "support_s_mm": 0., "direction_on_shaft_xyz": [-1., 0., 0.]}
            shaft = {"axis_id": aid, "point": [0., 0., 180.], "basis": [[1., 0., 0.]], "ends": [end],
                     "source_axis": {"hardware_scenario": {"washer_od_mm": 26., "washer_id_mm": 11.}}}
            old = copy.deepcopy(shaft)
            if host in m.HOSTS:
                old["point"][2] = 200.
            shafts.append(shaft)
            old_shafts.append(old)
            old_rows.append({"capture_id": aid + "/head-capture", "full_modeled_support": True})
            if host in m.HOSTS:
                annuli.append({"axis_id": aid, "receiver": host, "end": "head", "support_point_xyz_mm": [0., 0., 180.],
                    "inward_xyz": [1., 0., 0.], "nominal_washer_OD_mm": 26., "nominal_washer_ID_mm": 11.,
                    "observed_backing_fraction": 1., "single_own_host_targets": 1, "inward_skin_mm": .05,
                    "physical_contact_or_strength_qualified": False})
    exported = {"shafts": shafts, "raw_gross_timber_rows": [{"name": h} for h in hosts],
                "finished_body_observations": observations}
    parent = {"shafts": old_shafts, "finished_body_observations": prior_observations}
    finished = {"scenarios": [{"scenario": "proposed_Z180_modeled", "finished_bodies": bodies, "annular_queries": annuli}]}
    return exported, parent, finished, {"nominal_wood_seats": 112}, {"washer_seat_rows": old_rows}, {"finished_receivers": {"path": "inert.json", "sha256": "c"*64}}


def test_nominal_seat_selection_is16_own_observations_plus96_unchanged():
    result = m.nominal_seats(*seat_coupon())
    assert result["nominal_wood_seats"] == 112 and len(result["new_own_nominal_seats"]) == 16
    assert len(result["unaffected_capture_ids"]) == 96 and result["old_actions_or_strength_transferred"] is False


@pytest.mark.parametrize("mutation", ["source", "point", "normal", "washer", "physical", "duplicate", "unaffected"])
def test_seat_wrong_source_datum_hardware_or_unsupported_claim_rejects(mutation):
    args = seat_coupon()
    row = args[2]["scenarios"][0]["annular_queries"][0]
    if mutation == "source":
        args[2]["scenarios"][0]["finished_bodies"][row["receiver"]]["sha256"] = "0"*64
    elif mutation == "point":
        row["support_point_xyz_mm"][2] = 200.
    elif mutation == "normal":
        row["inward_xyz"][0] = -1.
    elif mutation == "washer":
        row["nominal_washer_OD_mm"] = 30.
    elif mutation == "physical":
        row["physical_contact_or_strength_qualified"] = True
    elif mutation == "duplicate":
        args[2]["scenarios"][0]["annular_queries"][-1] = copy.deepcopy(row)
    else:
        args[0]["shafts"][-1]["point"][2] += 1.
    with pytest.raises(ValueError):
        m.nominal_seats(*args)


def test_missing16_nominal_observations_stays_null():
    args = seat_coupon()
    args[2]["scenarios"][0]["annular_queries"].pop()
    result = m.nominal_seats(*args)
    assert result["nominal_wood_seats"] is None and result["physical_pressure_or_strength"] is None


def fitting_coupon():
    scenario = {"arm_length_mm": 88.9, "width_mm": 88.9, "thickness_mm": 6.35, "factory_hole_diameter_mm": 10.}
    field = {"source_inputs": {"fitting_poses": [{"id": str(i)} for i in range(22)]},
             "fitting_operator_descriptors": [{"body": str(i), "own_fitting_scenario": scenario.copy()} for i in range(22)]}
    cuts = [{"service": str(i), "kind": "inert", "receiver": "inert"} for i in range(27)]
    return field, {str(i): {"id": str(i)} for i in range(100)}, {"service_cuts": cuts}, {
        key: {"path": key + ".json", "sha256": "a"*64} for key in ("descriptor", "geometry", "parent_descriptors", "parent_geometry")}


def test_washer_composition_names_full_descriptor_partial_layout_and_original_cuts():
    args = fitting_coupon()
    result = m.washer_composition(*args)
    assert len(result["axes"]) == 100 and len(result["service_cuts"]) == 27
    assert result["source_composition"]["axes"]["partial_layout"] == args[3]["geometry"]
    assert result["source_composition"]["service_cuts"] == args[3]["parent_geometry"]
    assert result["partial_layout_contains_full_axes_or_service_cuts"] is False


@pytest.mark.parametrize("missing", ["cuts", "scenario"])
def test_unsupported_full_washer_composition_stays_null(missing):
    args = fitting_coupon()
    if missing == "cuts":
        args[2]["service_cuts"].pop()
    else:
        args[0]["fitting_operator_descriptors"][0]["own_fitting_scenario"]["thickness_mm"] = 5.
    assert m.washer_composition(*args) is None


def test_genuine491653_compiler_definition_checks_exact_second_read_bytes():
    pins = {}
    w = m.load(m.FROZEN["compiler"], pins, "z180_inert_exact_compiler_definition")
    raw = b"def coupon():\n    return 7\n"
    guarded = w.checked_ast(m.digest(raw))
    assert isinstance(guarded.parse(raw), ast.Module)
    with pytest.raises(ValueError, match="exact compiler bytes changed"):
        guarded.parse(raw + b"\n")
    m.verify(pins)


@pytest.mark.parametrize("fails", [False, True])
@pytest.mark.parametrize("composition_available", [False, True])
def test_scoped_frozen_reducer_boundaries_restore_without_real_reducers(tmp_path, monkeypatch, fails, composition_available):
    original_reduce = m.reduce_admitted
    args = fitting_coupon()
    field = args[0]
    field.update(schema=m.FIELD_SCHEMA)
    plan_path = tmp_path / "plan.py"
    plan_path.write_text("# Inert method-registry stand-in\n")
    plan = SimpleNamespace()
    c = SimpleNamespace(DESCRIPTOR_KEYS={}, _load_plan=lambda: plan, PLAN=plan_path,
        PLAN_SHA=m.digest(plan_path.read_bytes()), BOUNDARY_LOCK=RLock(), FIELD_SCHEMA="old",
        _load_gate=lambda _p: "old-provider")
    old_gate = c._load_gate
    composition = {"inert": True} if composition_available else None
    calls = []
    c._reduce = lambda actual, *_args: calls.append("inert_coarse") or {"inert": True}
    original_method = lambda *_args: SimpleNamespace(washer={"calculate": lambda *_args: pytest.fail("real washer called")})
    old_washer = lambda *_args: "old-composition"
    f = SimpleNamespace(_methods=original_method, washer_geometry=old_washer, GATE_SHA="old-gate")
    def rich(actual, _path, consumer, _plan, _pins, _contract):
        assert actual is field and c.FIELD_SCHEMA == m.FIELD_SCHEMA
        assert consumer._load_gate(None).checked_ast is compiler.checked_ast
        assert f.GATE_SHA == "a"*64 and f.washer_geometry(None) is composition
        methods = f._methods(None)
        if composition is None:
            assert methods.washer["calculate"]()["diagnostics"] is None
        calls.append("inert_rich")
        if fails:
            raise ValueError("inert rich stop")
        return {"missing_current_inputs": {}}
    f._reduce = rich
    compiler = SimpleNamespace(checked_ast=lambda _sha: "exact-provider")
    def load(ref, _pins, _label):
        return {"coarse": c, "rich": f, "compiler": compiler}[next(k for k, v in m.FROZEN.items() if v == ref)]
    monkeypatch.setattr(m, "load", load)
    monkeypatch.setattr(m, "ROOT", tmp_path)
    monkeypatch.setattr(m, "source_contract", lambda *_args: args[1])
    facade = SimpleNamespace(ARTIFACTS={"parent_geometry": args[3]["parent_geometry"]})
    monkeypatch.setattr(m, "prepare_contract", lambda *_args: (facade, {}, args[2]))
    monkeypatch.setattr(m, "washer_composition", lambda *_args: composition)
    config = {"sources": {"gate": {"sha256": "a"*64}}, "field": {"path": "inert-field.json"}}
    if fails:
        with pytest.raises(ValueError, match="inert rich stop"):
            original_reduce(config, {}, field, {}, None, mode="both", samples=41)
    else:
        findings, _ = original_reduce(config, {}, field, {}, None, mode="both", samples=41)
        if composition is None:
            assert "washer_composition" in findings["rich"]["missing_current_inputs"]
    assert calls == ["inert_coarse", "inert_rich"]
    assert c.FIELD_SCHEMA == "old" and c._load_gate is old_gate
    assert f._methods is original_method and f.washer_geometry is old_washer and f.GATE_SHA == "old-gate"


def test_frozen_gross_selectors_bind_distinct_metrics_without_import_or_reduction():
    path = REPO_ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/component-method-v1/gross_members.py"
    raw = path.read_bytes()
    assert m.digest(raw) == "01aaf22c8b2cf93430e7bbce4768260efea39bed3d527b8f5486ba4e38e32258"
    function = next(n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == "member_witnesses")
    loop = next(n for n in function.body if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == "row")
    assignments = {n.targets[0].id: n.value for n in loop.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
    selected = ast.literal_eval(assignments["selectors"])
    expression = assignments["witnesses"]
    coupons = [{"id": "normal", "gross_CD1_comparison": dict(zip(selected.values(), (5., 1.)))},
               {"id": "shear", "gross_CD1_comparison": dict(zip(selected.values(), (1., 6.)))}]
    result = eval(compile(ast.Expression(expression), str(path), "eval"), {"cuts": coupons, "selectors": selected})
    assert result["fully_braced_normal"]["id"] == "normal" and result["sufficient_shear_torsion"]["id"] == "shear"


def test_actual_cli_missing_config_retains_failure_and_cannot_retry(tmp_path):
    out = tmp_path / "attempt.json"
    command = [sys.executable, "-B", str(SOURCE), "--config", str(tmp_path / "absent.json"),
               "--config-sha256", "0"*64, "--out", str(out)]
    first = subprocess.run(command, capture_output=True, text=True, check=False)
    assert first.returncode != 0 and json.loads(out.read_bytes())["status"] == "FAILED"
    before = out.read_bytes()
    second = subprocess.run(command, capture_output=True, text=True, check=False)
    assert second.returncode != 0 and "FileExistsError" in second.stderr and out.read_bytes() == before


def test_actual_cli_dangling_link_rejects_before_config_intake(tmp_path):
    out = tmp_path / "attempt.json"
    out.symlink_to(tmp_path / "missing-target.json")
    command = [sys.executable, "-B", str(SOURCE), "--config", "absent-config.json", "--config-sha256", "0"*64, "--out", str(out)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "FileExistsError" in result.stderr and "absent-config" not in result.stderr
    assert out.is_symlink() and not out.exists()


def test_actual_cli_competing_processes_retain_one_intake_failure(tmp_path):
    out = tmp_path / "attempt.json"
    command = [sys.executable, "-B", str(SOURCE), "--config", str(tmp_path / "absent.json"),
               "--config-sha256", "0"*64, "--out", str(out)]
    def run():
        return subprocess.run(command, capture_output=True, text=True, check=False)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run(), range(2)))
    assert all(result.returncode != 0 for result in results)
    assert sum("FileExistsError" in result.stderr for result in results) == 1
    assert json.loads(out.read_bytes())["status"] == "FAILED"


def test_same_output_competitors_only_one_inert_callback(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(m, "consume", lambda *_args, **_kwargs: calls.append("inert") or {"execution": {}})
    out = tmp_path / "attempt.json"
    def run():
        try:
            m.consume_to_file("unused", "0"*64, out)
            return "owned"
        except FileExistsError:
            return "rejected"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run(), range(2)))
    assert sorted(results) == ["owned", "rejected"] and calls == ["inert"]


def test_import_is_definition_only_with_no_numerical_or_geometry_modules(tmp_path):
    script = "import runpy,sys; runpy.run_path(sys.argv[1],run_name='inert_import'); assert not any(k in sys.modules for k in ('cadquery','OCP','numpy','scipy'))"
    result = subprocess.run([sys.executable, "-B", "-c", script, str(SOURCE)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
