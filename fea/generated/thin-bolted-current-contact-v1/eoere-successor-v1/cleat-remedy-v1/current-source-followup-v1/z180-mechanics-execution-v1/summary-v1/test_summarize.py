"""Only inert JSON/source copies; no candidate artifacts or producer calls."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("z180_saved_summary", HERE/"summarize.py")
a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)
REAL_ROOT = a.ROOT
SELECTOR_RAW = (REAL_ROOT/a.SELECTORS["path"]).read_bytes()
GUARD_RAW = (REAL_ROOT/a.CLOSURE_GUARD["path"]).read_bytes()
OWN_RAW = a.OWN.read_bytes()


def findings():
    members = []
    for i in range(22):
        witnesses = {name: {"gross_CD1_comparison": {metric: i/10}, "station_global_grain_projection_mm": i,
            "local_N_Vu_Vv_T_Mu_Mv_n_nmm": [i]*6} for name, metric in (
                ("fully_braced_normal", "fully_braced_component_normal_interaction"),
                ("sufficient_shear_torsion", "equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio"))}
        members.append({"member": "member"+str(i), "witnesses": witnesses})
    coarse = {"fresh_gross_member_diagnostics": members,
        "angle_duties": [{"complete_group_heel_hole_prying_or_corner_resistance": None} for _ in range(22)],
        "exterior_cleat_corners": [{"complete_corner_splitting_group_or_bearing_resistance": None} for _ in range(2)],
        "six_panel_reductions": {"sample_count_per_axis": 41, "panel_diagnostics": [{"panel": "panel"+str(i),
            "resolved_section_diagnostics": {"components": {"bending": {"sampled_ratio_CD1": i/2}}},
            "deformation_diagnostics": {"maximum_sampled_abs_outward_w_mm": i, "linear_plate_applicability_established": False}} for i in range(6)]},
        "simultaneous_Hillman_actions_and_generic_references": [{"axis_id": "screw"+str(i), "generic_head_ratio_CD1": i/20,
            "generic_withdrawal_required_effective_thread_mm_CD1": i, "same_axis_simultaneous_lateral_n": 2*i} for i in range(66)],
        "own_shaft_circle_comparisons": [None]*100, "own_washer_capture_diagnostics": [None]*200,
        "own_wood_bearing_resultants_from_admitted_field": [None]*120}
    steel = [{"comparison": {"id": name}, "summary": {"used_hole_bearing": {"comparison_count": 1, "exceedance_count": 1,
        "worst": {"body": "own-angle", "comparison": {"bearing_reference_ratio": 1.5, "force_N_V1_V2_n": [1, 2, 3]}},
        "exceedances": [{"body": "own-angle", "comparison": {"bearing_reference_ratio": 1.5}}]}}} for name in ("t6_r6", "t6p35_r6p35")]
    rich = {"rich_steel": steel, "timber": {
        "shaft_components": [{"axis_id": "mixed"+str(i), "component": None, "missing_method": "mixed-plane resistance unknown", "disposition": "unknown"} for i in range(8)]
            + [{"axis_id": "two-member", "component": {"exceeds_unadjusted_component_reference": True, "Cdelta0p5_Cg1_CD1_sensitivity_ratio": 2.}}],
        "duties": [{"complete_joint_resistance_n": None} for _ in range(24)],
        "summary": {"worst_components": [{"axis_id": "two-member", "value": 2.}]}, "unsupported_mechanisms": ["finished ligaments unknown"]},
        "shaft": {"all100": [{"axis_id": "shaft"+str(i), "governing": {"specified_material_first_yield_index": i/50}} for i in range(100)],
            "complete_bolt_resistance": None, "first_yield_reference_exceedances": ["shaft99"]},
        "washers": {"census": {"physical_end_captures": 200}, "reviewed_nominal_seat_geometry": {"nominal_wood_seats": 112},
            "worsts": {"by_diameter": {"9.525": None}, "overall": None}, "exceeded_reference_diagnostics": [],
            "limits": ["pressure unknown"], "geometry_composition": {"own": True}},
        "missing_current_inputs": {"finished_sections": "own finished-section witnesses absent"}}
    return {"coarse": coarse, "rich": rich}


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    root = tmp_path
    def save(path, data):
        path = root/path
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = data if isinstance(data, bytes) else (json.dumps(data, sort_keys=True, allow_nan=False)+"\n").encode()
        path.write_bytes(raw)
        return {"path": str(path.relative_to(root)), "sha256": a.sha(raw)}
    save(a.SELECTORS["path"], SELECTOR_RAW)
    save(a.CLOSURE_GUARD["path"], GUARD_RAW)
    helper = save("summary-v1/summarize.py", OWN_RAW)
    gate, consumer = save("gate.py", b"# inert source only\n"), save("consumer.py", b"# inert consumer source only\n")
    geometry = {key: save(key+".json", {"inert": key}) for key in ("report", "source_manifest", "cached_source_export")}
    monkeypatch.setattr(a, "ROOT", root)
    monkeypatch.setattr(a, "OWN", root/helper["path"])
    monkeypatch.setattr(a, "GATE", gate)
    monkeypatch.setattr(a, "CONSUMER", consumer)
    monkeypatch.setattr(a, "GEOMETRY", geometry)
    base = {r["path"]: r["sha256"] for r in (helper, gate, consumer, *geometry.values())}
    cases = []
    for i, case in enumerate(a.CASES):
        prefix = "case"+str(i)+"/"
        identity = {"state_id": "eoere-z180-fixed-floor-inert-"+str(i), "case_id": case, "accessory_placement": "inert-position"}
        field = {"schema": "eoere_z180_fixed_floor_candidate/v1", **identity, "release": a.RELEASE,
            "source_inputs": {"geometry": geometry, "source_sha256": base}, "source_sha256": base,
            "current_execution": {"geometry": geometry["report"], "loaded_driver_path": gate["path"], "loaded_driver_sha256": gate["sha256"]},
            "response": {"q_canonical_sha256": "0"*64, "gradient_canonical_sha256": "1"*64},
            "source_case_selection": {"case_id": case}, "original_operator_fingerprint_sha256": "2"*64, "limits": ["own inert field limit"]}
        field_ref = save(prefix+"field.json", field)
        admission = {"schema": "eoere_z180_fixed_floor_independent_field_admission/v1", **identity, "release": a.RELEASE,
            "unadopted_z180_equilibrium_and_recovery_pass": True, "input_raw_sha256": field_ref["sha256"],
            "input_canonical_sha256": a.canonical(field), "admission_source_sha256": gate["sha256"], "source_path": gate["path"],
            **field["response"], "source_case_selection": field["source_case_selection"], "original_operator_fingerprint_sha256": "2"*64,
            "source_sha256": base, "declared_law_checks": {"gradient_inf_n": 1e-6}, "loaded_recovery_checks": {"own": True},
            "motion_diagnostics": {"first_order_applicability_established": False}, "normal_force_n_by_host": {"leg": 1.},
            "horizontal_force_xyz_n_by_host": {"leg": [0., 0., 0.]}, "reaction_ratio_required_not_measured_friction": {"leg": 0.}, "support_contract": {"assumption": True}}
        admission_ref = save(prefix+"admission.json", admission)
        sources = {"gate": gate, "geometry": geometry["report"], "manifest": geometry["source_manifest"], "descriptor": geometry["cached_source_export"]}
        config = {"schema": "eoere_z180_component_consumer_inputs/v1", "state_id": identity["state_id"], "case_id": case,
            "field": field_ref, "admission": admission_ref, "sources": sources, "ready_for_saved_field_consumption": True, "release": a.RELEASE}
        config_ref = save(prefix+"config.json", config)
        seat = {"nominal_wood_seats": 112, "new_own_nominal_seats": [{"capture_id": "own"+str(j)} for j in range(16)],
            "unaffected_proof_count": 96, "unaffected_capture_ids": ["unchanged"+str(j) for j in range(96)], "old_actions_or_strength_transferred": False}
        result = {"schema": "eoere_unadopted_z180_same_state_component_references/v1", **identity,
            "field": field_ref, "admission": admission_ref, "sources": sources, "source_sha256": base, "mode": "both",
            "source_inputs_canonical_sha256": a.canonical(field["source_inputs"]), "findings": findings(), "nominal_seat_geometry": seat,
            "complete_joint_resistance": None, "unadopted_proposal": True, "release": a.RELEASE}
        result_ref = save(prefix+"result.json", result)
        observed_before = dict(base)
        missing = []
        if i == 0:
            missing = [consumer["path"]]
            del observed_before[consumer["path"]]
        snapshot_before = save(prefix+"before.json", {"schema": "eoere_z180_component_source_snapshot_before/v1", "current_expected_pins": base,
            "observed_before": observed_before, "drift": {}, "inventory_only_historical_receipts": ["inventory-only"], "reviews": []})
        snapshot_after = save(prefix+"after.json", {"schema": "eoere_z180_component_source_snapshot_after/v1", "observed_after": base,
            "before_after_drift": {}, "result_source_drift": {}, "result_source_pin_count": len(base), "result_pins_missing_before_snapshot": missing})
        stdout, stderr = save(prefix+"stdout.log", b"inert producer status\n"), save(prefix+"stderr.log", b"")
        process = {"schema": "eoere_z180_component_process_receipt/v1", "exit_code": 0, "cwd": str(root), "env": {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"},
            "command": ["python", "-u", str(root/consumer["path"]), "--config", str(root/config_ref["path"]), "--config-sha256", config_ref["sha256"], "--mode", "both", "--samples", "41", "--out", str(root/result_ref["path"])],
            "field": field_ref, "admission": admission_ref, "config": config_ref, "consumer": consumer, "result": result_ref,
            "stdout": stdout, "stderr": stderr, "source_drift_before": {}, "source_drift_after": {}, "result_source_drift": {},
            "source_pins_before": snapshot_before, "source_pins_after": snapshot_after, "missing_before": missing, "result_pin_count": len(base), "union_pin_count": len(base), "elapsed_seconds": 1.}
        for key in ("config", "consumer", "result", "stdout", "stderr", "source_pins_before", "source_pins_after"):
            process[key] = {**process[key], "bytes": (root/process[key]["path"]).stat().st_size}
        process_ref = save(prefix+"process.json", process)
        cases.append({"case_id": case, "field": field_ref, "admission": admission_ref,
            "component": {"config": config_ref, "result": result_ref, "process": process_ref, "stdout": stdout, "stderr": stderr}})
    manifest = {"schema": a.INPUT_SCHEMA, "geometry": geometry, "source_sha256": base, "cases": cases, "release": a.RELEASE}
    manifest_ref = save("manifest.json", manifest)
    return SimpleFixture(root, save, manifest, manifest_ref)


class SimpleFixture:
    def __init__(self, root, save, manifest, ref):
        self.root, self.save, self.manifest, self.ref = root, save, manifest, ref


def test_six_case_inert_summary_uses_exact_selectors_and_preserves_caveat(fixture):
    result = a.build(fixture.manifest, fixture.ref)
    assert [row["case_id"] for row in result["cases"]] == list(a.CASES)
    first = result["cases"][0]
    metric = "fully_braced_component_normal_interaction"
    assert first["coarse"]["gross_raw_members"][metric]["worst"]["member"] == "member21"
    assert first["coarse"]["generic_screw_references"]["generic_head_ratio_CD1"]["axis_id"] == "screw65"
    assert first["rich"]["shaft"]["worst"]["axis_id"] == "shaft99"
    assert first["coarse"]["source_limits"] == ["own inert field limit"]
    assert first["coarse_selector_limits_provenance"]["source"] == fixture.manifest["cases"][0]["field"]
    assert first["outer_snapshot_caveats"]["complete_outer_pre_snapshot_claimed"] is False
    assert result["cases"][1]["outer_snapshot_caveats"]["complete_outer_pre_snapshot_claimed"] is True
    assert len(first["nominal_seat_geometry"]["new_own_nominal_seats"]) == 16
    assert first["nominal_seat_geometry"]["unaffected_proof_count"] == 96
    assert result["complete_joint_resistance"] is None and not any(result["release"].values())
    assert result["execution"]["gate_consumer_reducer_CAD_operator_K_q_native_or_solve_called"] is False


@pytest.mark.parametrize("text", ['{"x":NaN}', '{"x":Infinity}', '{"x":1e999}', '{"x":1,"x":2}'])
def test_strict_json_negative_controls(text):
    with pytest.raises(ValueError):
        a.decode(text)


def test_exact_selector_hash_checked_before_ast(fixture, monkeypatch):
    wrong = {**a.SELECTORS, "sha256": "0"*64}
    monkeypatch.setattr(a.ast, "parse", lambda *_: pytest.fail("AST reached before source hash"))
    with pytest.raises(ValueError, match="exact source bytes differ"):
        a.definitions(wrong, a.SELECTED, {})


@pytest.mark.parametrize("mutation,match", [("order", "six exact ordered"), ("duplicate_state", "six unique"),
    ("old_schema", "Z180 schemas"), ("raw_pair", "raw field/admission"), ("samples", "command binding"),
    ("drift", "process source drift"), ("spacer_source", "component source"), ("non_null", "null resistance"),
    ("seat", "own16/unchanged96"), ("sample_grid", "41 samples"), ("producer", "corrected consumer"),
    ("log_ref", "recorded reference differs"), ("snapshot_missing", "coverage caveat")])
def test_saved_pair_process_and_source_negative_controls(fixture, mutation, match):
    manifest = copy.deepcopy(fixture.manifest)
    binding = manifest["cases"][0]
    def update(key, mutate):
        group = binding if key in ("field", "admission") else binding["component"]
        value = json.loads((fixture.root/group[key]["path"]).read_bytes())
        mutate(value)
        group[key] = fixture.save(group[key]["path"], value)
    if mutation == "order":
        manifest["cases"].reverse()
    elif mutation == "duplicate_state":
        # Bypass only record authentication to isolate the roster guard.
        original = a.case_records
        def duplicate(row, pins):
            record = original(row, pins)
            record[0]["state_id"] = "same inert state"
            return record
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(a, "case_records", duplicate)
            ref = fixture.save("manifest.json", manifest)
            with pytest.raises(ValueError, match=match):
                a.build(manifest, ref)
        return
    elif mutation == "old_schema":
        update("result", lambda r: r.update(schema="eoere_current_same_state_followup_component_references/v1"))
    elif mutation == "raw_pair":
        update("admission", lambda r: r.update(input_raw_sha256="0"*64))
    elif mutation == "samples":
        update("process", lambda r: r["command"].__setitem__(r["command"].index("--samples")+1, "51"))
    elif mutation == "drift":
        update("process", lambda r: r.update(source_drift_after={"inert": "changed"}))
    elif mutation == "spacer_source":
        update("config", lambda r: r["sources"].__setitem__("descriptor", r["sources"]["geometry"]))
        # Make report/config agree so the fixed current4in descriptor guard fires.
        update("result", lambda r: r["sources"].__setitem__("descriptor", r["sources"]["geometry"]))
    elif mutation == "non_null":
        update("result", lambda r: r.update(complete_joint_resistance=1.))
    elif mutation == "seat":
        update("result", lambda r: r["nominal_seat_geometry"].update(unaffected_proof_count=95))
    elif mutation == "sample_grid":
        update("result", lambda r: r["findings"]["coarse"]["six_panel_reductions"].update(sample_count_per_axis=51))
    elif mutation == "producer":
        update("process", lambda r: r["command"].__setitem__(2, "foreign.py"))
    elif mutation == "log_ref":
        update("process", lambda r: r["stdout"].update(sha256="0"*64))
    else:
        update("process", lambda r: r.update(source_pins_after=r["source_pins_before"]))
        match = "exact component source snapshot"
    # When result bytes change, update only process result provenance as well.
    if mutation in ("old_schema", "non_null", "seat", "sample_grid", "spacer_source"):
        def join_result(r):
            r["result"] = {**binding["component"]["result"], "bytes": (fixture.root/binding["component"]["result"]["path"]).stat().st_size}
        update("process", join_result)
    ref = fixture.save("manifest.json", manifest)
    with pytest.raises(ValueError, match=match):
        a.build(manifest, ref)


@pytest.mark.parametrize("kind", ["existing", "dangling", "traversal"])
def test_fresh_output_guards_before_any_source_callback(fixture, monkeypatch, kind):
    out = a.OWN.parent/"runs-v1/attempt/out.json"
    out.parent.mkdir(parents=True)
    if kind == "existing":
        out.write_text("preserve")
    elif kind == "dangling":
        out.symlink_to(out.parent/"absent")
    else:
        out = out.parent/".."/"out.json"
    monkeypatch.setattr(a, "checked", lambda *_: pytest.fail("source callback before fresh reservation"))
    with pytest.raises((ValueError, FileExistsError)):
        a.write_to_file(fixture.ref, out)


def test_failure_receipt_retained_and_retry_rejected(fixture):
    out = a.OWN.parent/"runs-v1/failed/out.json"
    wrong = {**fixture.ref, "sha256": "0"*64}
    with pytest.raises(ValueError, match="source bytes differ"):
        a.write_to_file(wrong, out)
    failed = out.read_bytes()
    assert json.loads(failed)["status"] == "FAILED"
    with pytest.raises(FileExistsError):
        a.write_to_file(fixture.ref, out)
    assert out.read_bytes() == failed


def test_parent_alias_retarget_cannot_redirect_reserved_output(fixture, monkeypatch):
    runs = a.OWN.parent/"runs-v1"
    original, foreign = runs/"original", fixture.root/"foreign"
    original.mkdir(parents=True)
    foreign.mkdir()
    alias = runs/"alias"
    alias.symlink_to(original, target_is_directory=True)
    original_open = Path.open
    def retarget(path, *args, **kwargs):
        if path == original/"out.json" and args and args[0] == "x+":
            alias.unlink()
            alias.symlink_to(foreign, target_is_directory=True)
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", retarget)
    with pytest.raises(ValueError, match="source bytes differ"):
        a.write_to_file({**fixture.ref, "sha256": "0"*64}, alias/"out.json")
    assert json.loads((original/"out.json").read_bytes())["status"] == "FAILED"
    assert not (foreign/"out.json").exists()


def test_source_drift_after_selection_fails_closed(fixture, monkeypatch):
    original = a.verify
    count = 0
    def drift(pins):
        nonlocal count
        count += 1
        if count == 2:
            (fixture.root/a.CONSUMER["path"]).write_text("changed after selection")
        return original(pins)
    monkeypatch.setattr(a, "verify", drift)
    with pytest.raises(ValueError, match="exact source bytes differ"):
        a.build(fixture.manifest, fixture.ref)


def test_own_runs_symlink_cannot_escape_packet(fixture, monkeypatch):
    foreign = fixture.root/"foreign"
    foreign.mkdir()
    (a.OWN.parent/"runs-v1").symlink_to(foreign, target_is_directory=True)
    monkeypatch.setattr(a, "checked", lambda *_: pytest.fail("source callback on foreign output"))
    with pytest.raises(ValueError, match="own runs-v1"):
        a.write_to_file(fixture.ref, a.OWN.parent/"runs-v1/out.json")
    assert not (foreign/"out.json").exists()
