"""Synthetic admission/reducer controls only; no real force field is consumed."""
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

OWN = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("current_component_consumer_test_subject", OWN / "consume.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + "\n")
    return m.digest(path.read_bytes())


@pytest.fixture
def tiny(tmp_path, monkeypatch):
    plan = m._load_plan()
    field = {"schema": m.FIELD_SCHEMA, "state_id": "synthetic-state", "case_id": "synthetic-case",
             "accessory_placement": "synthetic-placement", "release": m.RELEASE,
             "source_inputs": {"geometry": {"report": plan.ARTIFACTS["geometry"], "source_manifest": plan.ARTIFACTS["manifest"],
                                            "cached_source_export": plan.ARTIFACTS["descriptors"]}},
             "current_execution": {"geometry": plan.ARTIFACTS["geometry"]}}
    receipt = {"schema": m.ADMISSION_SCHEMA, m.SUCCESS: True}
    fp, rp = tmp_path / "synthetic-field.json", tmp_path / "synthetic-admission.json"
    fsha, rsha = write(fp, field), write(rp, receipt)
    events = []

    def admitted(raw, rec, *, admission_sha256):
        events.append("gate")
        assert raw == fp.read_bytes() and rec == receipt and admission_sha256 == m.GATE_SHA
        return json.loads(raw), {}

    def contract(actual, source_plan):
        events.append("contract")
        assert actual == field and source_plan.ARTIFACTS == plan.ARTIFACTS
        return {"source_sha256": {}, "nominal_seat_geometry": {}, "reuse": {"tiny": {"limit": "synthetic control"}}}, {}

    def reduce(actual, axes, source_plan, pins, samples):
        events.append("reducer")
        assert actual == field and axes == {} and samples == 41
        return {"synthetic_only": True}

    monkeypatch.setattr(m, "_load_gate", lambda source_plan: SimpleNamespace(require_admitted_payload=admitted))
    monkeypatch.setattr(m, "_current_contract", contract)
    monkeypatch.setattr(m, "_reduce", reduce)
    return SimpleNamespace(field=field, receipt=receipt, fp=fp, rp=rp, fsha=fsha, rsha=rsha, events=events)


def call(t, **kwargs):
    return m.consume(t.fp, t.rp, expected_field_sha256=kwargs.pop("fsha", t.fsha),
                     expected_receipt_sha256=kwargs.pop("rsha", t.rsha), **kwargs)


def test_gate_then_contract_then_reducer_with_unchanged_payload(tiny):
    result = call(tiny)
    assert tiny.events == ["gate", "contract", "reducer"]
    assert result["state_id"] == tiny.field["state_id"] and result["raw_field_sha256"] == tiny.fsha
    assert result["field_admission_receipt_sha256"] == tiny.rsha
    assert result["complete_joint_resistance"] is None and result["release"] == m.RELEASE
    assert json.loads(tiny.fp.read_bytes()) == tiny.field


@pytest.mark.parametrize("kwargs", [{"fsha": "0" * 64}, {"rsha": "0" * 64}, {"admission_sha256": "0" * 64}])
def test_wrong_exact_bytes_or_gate_never_reach_admission_or_reducer(tiny, kwargs):
    with pytest.raises(ValueError):
        call(tiny, **kwargs)
    assert tiny.events == []


@pytest.mark.parametrize("mutation", [
    lambda f: f.update(schema="eoere_raised_rail_fixed_rear_leg_floor_candidate/v1"),
    lambda f: f["source_inputs"]["geometry"].update(report={"path": "old/geometry.json", "sha256": "0" * 64}),
    lambda f: f["source_inputs"]["geometry"].update(scene={"path": "old/scene.json", "sha256": "0" * 64}),
    lambda f: f.update(release={**m.RELEASE, "structural_released": True}),
])
def test_old_or_projected_field_identity_never_reaches_reducer(tiny, mutation):
    mutation(tiny.field)
    with pytest.raises(ValueError):
        call(tiny, fsha=write(tiny.fp, tiny.field))
    assert tiny.events == []


def test_unissued_receipt_never_reaches_reducer(tiny):
    tiny.receipt[m.SUCCESS] = False
    with pytest.raises(ValueError, match="own current admission"):
        call(tiny, rsha=write(tiny.rp, tiny.receipt))
    assert tiny.events == []


@pytest.mark.parametrize("mode", ["reject", "mutate_payload", "change_raw_file"])
def test_gate_failure_or_payload_change_never_reaches_reducer(tiny, monkeypatch, mode):
    def gate(raw, receipt, **kwargs):
        tiny.events.append("gate")
        if mode == "reject":
            raise ValueError("synthetic admission rejection")
        field = json.loads(raw)
        if mode == "mutate_payload":
            field["state_id"] = "foreign-state"
        else:
            tiny.fp.write_text("changed during admission\n")
        return field, {}
    monkeypatch.setattr(m, "_load_gate", lambda plan: SimpleNamespace(require_admitted_payload=gate))
    with pytest.raises(ValueError):
        call(tiny)
    assert tiny.events == ["gate"]


def test_reducer_mutation_is_rejected(tiny, monkeypatch):
    def reduce(field, *args):
        tiny.events.append("reducer")
        field["case_id"] = "foreign-case"
        return {}
    monkeypatch.setattr(m, "_reduce", reduce)
    with pytest.raises(ValueError, match="changed the admitted field"):
        call(tiny)
    assert tiny.events == ["gate", "contract", "reducer"]


@pytest.mark.parametrize("key", ["shafts", "hillman_rows", "current_panel_machining_descriptors"])
def test_actual_saved_descriptor_contract_rejects_metadata_changes(key):
    plan = m._load_plan()
    data = json.loads(plan.checked_bytes(plan.ARTIFACTS["descriptors"]))
    source = {key: copy.deepcopy(data[value]) for key, value in m.DESCRIPTOR_KEYS.items()}
    source["parameters"] = data["parameters"]
    source["panel_ids"] = [r["id"] for r in data["finished_body_observations"]
                           if r["id"] not in {t["name"] for t in data["raw_gross_timber_rows"]}]
    field = {"source_inputs": source}  # Metadata only; no force/actions/q payload.
    if key == "current_panel_machining_descriptors":
        source[key]["features"].pop()
    else:
        source[key].pop()
    with pytest.raises(ValueError, match="descriptor join differs"):
        m._current_contract(field, plan)


@pytest.mark.parametrize("fails", [False, True])
def test_scoped_reducer_callbacks_restore_on_success_and_exception(monkeypatch, fails):
    plan = m._load_plan()
    features = [{"current": "aperture metadata fixture"}]
    calls = []

    def original_datums(state, assessment, datums, integrated):
        calls.append("spatial_datums")
        assert integrated == {"panel_machining": {"features": features}}
        return {"tiny-panel": {"support_bounds": ["historical support"]}}

    original_pins = lambda: {"unused": "historical-contract"}
    panel = SimpleNamespace(prepared_datums=original_datums)
    base = SimpleNamespace(FIELD_SCHEMA="original-schema", panel=panel, PINS={})
    old = SimpleNamespace(FROZEN={}, INPUT=plan.ARTIFACTS["geometry"]["path"], GUARDED=plan.ARTIFACTS["manifest"]["path"],
                          DIRECT={r["path"]: r["sha256"] for r in plan.ARTIFACTS.values()})
    steel_path = m.ROOT / plan.BASE / "raised-rail-components-v1/comparisons.py"
    original_path = m.ROOT / plan.BASE / "steel-shaft-comparison-v1/comparison.py"
    steel = SimpleNamespace(old=old, centroidal=SimpleNamespace(source_pins=dict), ORIGINAL=original_path,
                            ORIGINAL_SHA=plan.METHODS["steel-shaft-comparison-v1/comparison.py"][0],
                            __file__=str(steel_path), LOADED_SHA=plan.METHODS["raised-rail-components-v1/comparisons.py"][0],
                            source_pins=original_pins)
    gross = SimpleNamespace(source_pins=dict)

    def reducer(field, comparison, members, axes, *, samples):
        calls.append("reducer")
        assert base.FIELD_SCHEMA == m.FIELD_SCHEMA and comparison is steel and members is gross
        row = panel.prepared_datums({}, {}, {}, {"ignored old features": True})["tiny-panel"]
        assert row["support_bounds"] == [] and row["current_support_footprints_qualified"] is False
        assert plan.ARTIFACTS["geometry"]["path"] in comparison.source_pins()
        if fails:
            raise ValueError("synthetic reducer failure")
        return {"synthetic": True}, {}

    base.reduce_field = reducer
    modules = {"eoere_current_coarse_assessment": base, "eoere_current_coarse_gross": gross,
               "eoere_current_coarse_centroidal_comparison": steel}
    monkeypatch.setattr(m, "load", lambda path, sha, label: modules[label])
    field = {"source_inputs": {"current_panel_machining_descriptors": {"features": features}}}
    if fails:
        with pytest.raises(ValueError, match="synthetic reducer failure"):
            m._reduce(field, {}, plan, {}, 41)
    else:
        assert m._reduce(field, {}, plan, {}, 41) == {"synthetic": True}
    assert base.FIELD_SCHEMA == "original-schema" and panel.prepared_datums is original_datums
    assert steel.source_pins is original_pins and calls == ["reducer", "spatial_datums"]


BOOTSTRAP = """
import importlib.util, json, os, pathlib, sys, time
p, log, mode = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
s = importlib.util.spec_from_file_location('synthetic_cli_control', p)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
def fake(*args, **kwargs):
    with log.open('a') as stream: stream.write('callback\\n')
    if mode == 'fail': raise ValueError('synthetic callback failure')
    if mode == 'exit': os._exit(17)
    time.sleep(.15)
    return {'schema':'synthetic_reservation_control/v1','release':m.RELEASE}
m.consume = fake
m.main(sys.argv[4:])
"""


def cli(out):
    return ["--field", "unused-field.json", "--receipt", "unused-receipt.json",
            "--expected-field-sha256", "0" * 64, "--expected-receipt-sha256", "0" * 64, "--out", str(out)]


def control(log, mode, out):
    return [sys.executable, "-B", "-c", BOOTSTRAP, str(OWN / "consume.py"), str(log), mode, *cli(out)]


def test_actual_cli_dangling_output_link_rejects_before_callback(tmp_path):
    out, log = tmp_path / "out.json", tmp_path / "calls.txt"
    out.symlink_to(tmp_path / "missing.json")
    result = subprocess.run(control(log, "success", out), capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "FileExistsError" in result.stderr
    assert not log.exists() and out.is_symlink() and not out.exists()


def test_actual_cli_two_competitors_only_one_callback(tmp_path):
    out, log = tmp_path / "out.json", tmp_path / "calls.txt"
    processes = [subprocess.Popen(control(log, "success", out), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    results = [p.communicate(timeout=20) for p in processes]
    assert sorted(p.returncode for p in processes) == [0, 1]
    assert log.read_text().splitlines() == ["callback"]
    assert json.loads(out.read_bytes())["schema"] == "synthetic_reservation_control/v1"
    assert sum("FileExistsError" in err for _, err in results) == 1


@pytest.mark.parametrize("mode, status, code", [("fail", "FAILED", 1), ("exit", "STARTED", 17)])
def test_actual_cli_failed_or_abrupt_attempt_is_retained_and_cannot_be_reused(tmp_path, mode, status, code):
    out, log = tmp_path / "out.json", tmp_path / "calls.txt"
    first = subprocess.run(control(log, mode, out), capture_output=True, text=True, check=False)
    assert first.returncode == code and json.loads(out.read_bytes())["status"] == status
    before = out.read_bytes()
    second = subprocess.run(control(log, "success", out), capture_output=True, text=True, check=False)
    assert second.returncode == 1 and "FileExistsError" in second.stderr
    assert out.read_bytes() == before and log.read_text().splitlines() == ["callback"]


def test_actual_unpatched_cli_missing_input_records_failure_without_reducer(tmp_path):
    out = tmp_path / "out.json"
    result = subprocess.run([sys.executable, "-B", str(OWN / "consume.py"), *cli(out)],
                            cwd=tmp_path, capture_output=True, text=True, check=False)
    assert result.returncode == 1
    record = json.loads(out.read_bytes())
    assert record["status"] == "FAILED" and record["exception"]["type"] == "FileNotFoundError"
    assert record["release"] == m.RELEASE
