"""Independent source/synthetic testing review. Genuine consumption stays held."""
from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
MECH = OWN.parents[2]
TARGET = MECH / "current-component-bridge-v1/followups-v1"
PINS = {
    TARGET / "followups.py": "a27bacf7260905f69c2a69bae60c0f2cf4ed1f4efd229100e3c8fb846b892798",
    TARGET / "test_followups.py": "eec79c2a9f33305f9cccfbec14520806f69a4a46a34efb995e4dc7ab31df912f",
    TARGET / "verification.json": "1390a83569c7885e0006645e1a8fb11814c1751900ebad6f0118daeea454173f",
    MECH / "current-component-bridge-v1/consumer-v1/consume.py": "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9",
    MECH / "current-force-bridge-v1/review-fix-v2/bridge.py": "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    for path, expected in PINS.items():
        assert sha(path) == expected, str(path)


def load(path, label):
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rejection(callback, expected):
    try:
        callback()
    except expected as error:
        return {"type": type(error).__name__, "message": str(error)}
    raise AssertionError("expected rejection: " + str(expected))


def boundary_checks(fixture, directory):
    import pytest

    m = fixture.m
    observed = {}
    for mode in ("metadata_failure", "gate_payload_substitution", "gate_pin_conflict", "receipt_schema", "receipt_integer_success"):
        mp = pytest.MonkeyPatch()
        try:
            folder = directory / mode
            folder.mkdir()
            tiny = fixture.tiny.__wrapped__(folder, mp)
            if mode == "metadata_failure":
                def metadata(*args, tiny=tiny):
                    tiny.events.append("metadata")
                    raise ValueError("synthetic metadata join failure")
                mp.setattr(tiny.c, "_current_contract", metadata)
            elif mode.startswith("gate_"):
                def gate(raw, receipt, tiny=tiny, mode=mode, **kwargs):
                    tiny.events.append("gate")
                    field = json.loads(raw)
                    pins = {}
                    if mode == "gate_payload_substitution":
                        field["case_id"] = "foreign-case"
                    else:
                        pins[m.name(tiny.fp)] = "f" * 64
                    return field, pins
                mp.setattr(tiny.c, "_load_gate", lambda plan, gate=gate: SimpleNamespace(require_admitted_payload=gate))
            else:
                tiny.receipt["schema" if mode == "receipt_schema" else tiny.c.SUCCESS] = "wrong" if mode == "receipt_schema" else 1
                tiny.rsha = fixture.write(tiny.rp, tiny.receipt)
            error = rejection(lambda tiny=tiny: fixture.call(tiny), ValueError)
            assert "rich_reducer" not in tiny.events
            expected = ["gate", "metadata"] if mode == "metadata_failure" else ["gate"] if mode.startswith("gate_") else []
            assert tiny.events == expected, (mode, tiny.events)
            observed[mode] = {"events": tiny.events.copy(), "rejection": error}
        finally:
            mp.undo()
    return observed


def source_and_restore_checks(fixture, directory):
    m = fixture.m
    c = m._consumer()
    plan = c._load_plan()
    pins = dict(plan.component_plan()["source_sha256"])
    m._materials(c, plan, pins)
    methods = m._methods(c, plan, pins)
    c.verify(pins)
    source_record = {"count": len(pins), "canonical_sha256": m.canonical(pins)}
    declared = json.loads((TARGET / "verification.json").read_bytes())["reused_source_closure"]
    assert source_record == {"count": declared["current_plus_followup_source_count"],
                             "canonical_sha256": declared["current_plus_followup_sources_canonical_sha256"]}
    original_ast = methods.group.ast
    ast_checks = {}
    for label, raw, error_type in (("missing_function", b"def available():\n    return 7\n", ValueError),
                                   ("invalid_syntax", b"def broken(:\n", SyntaxError)):
        source = directory / (label + ".py")
        source.write_bytes(raw)
        pins[str(source)] = m.digest(raw)
        ast_checks[label] = rejection(lambda source=source: methods.pure(str(source), ["wanted"]), error_type)
        assert methods.group.ast is original_ast
        pins.pop(str(source))
    c.verify(pins)
    return source_record, ast_checks


def synthetic_adapter_checks(fixture, directory):
    m = fixture.m
    base_field, _, _, _ = fixture.metadata.__wrapped__()
    observed = {}
    for mode in ("success", "steel_census", "timber_interrupt", "mixed_count", "duplicate_shaft", "washer_failure"):
        field = copy.deepcopy(base_field)
        field.update(schema="synthetic-only", state_id="synthetic", case_id="tiny", accessory_placement="tiny")
        before = m.canonical(field)
        fp = directory / (mode + "-synthetic.json")
        pins = {m.name(fp): fixture.write(fp, field)}
        c = m._consumer()
        plan = c._load_plan()
        events = []

        def old_intake(*args):
            raise AssertionError("historical intake forbidden")

        timber = SimpleNamespace(intake=old_intake)

        def angle(actual, descriptor, net, scenario, *, field=field, events=events, mode=mode):
            assert actual is field and scenario in m.STEEL_SCENARIOS
            events.append("steel:" + scenario["id"])
            return {"bands": [None] * (3 if mode == "steel_census" else 4), "integrity": {"point_loads_retained": 28}}

        def produce(_, *, timber=timber, field=field, pins=pins, events=events, mode=mode):
            intake = timber.intake(None)
            assert intake[1] is field and intake[4] is None and intake[5] is pins
            events.append("timber")
            if mode == "timber_interrupt":
                raise KeyboardInterrupt("synthetic timber interruption")
            unknown = 7 if mode == "mixed_count" else 8
            return {"shaft_components": [{"axis_id": s["axis_id"], "component": None if i < unknown else {}}
                                         for i, s in enumerate(field["source_inputs"]["shafts"])]}

        def bolt(shafts, actual, *args, field=field, events=events, mode=mode):
            assert actual is field
            events.append("shaft")
            rows = [{"axis_id": key, "governing": {"specified_material_first_yield_index": 1. if i == 0 else 2. if i == 1 else .5}}
                    for i, key in enumerate(shafts)]
            if mode == "duplicate_shaft":
                rows[0]["axis_id"] = rows[1]["axis_id"]
            return rows

        def washer(actual, composition, facts, actual_pins, authenticated, *, field=field, pins=pins, events=events, mode=mode):
            assert actual is field and actual_pins is pins
            events.append("washer")
            if mode == "washer_failure":
                raise ValueError("synthetic washer failure")
            return {"preserved_first_tmp_sha256": {}, "first_tmp_bytes_currently_match": {},
                    "limits": ["old context"], "known_answer_checks": {"synthetic": True}}

        timber.produce = produce
        fake = SimpleNamespace(steel={"reduce_angle": angle, "summary": lambda angles: {"synthetic": len(angles)}},
            net=None, timber=timber, group=None, ws=None, ww=None, resolved=None, circles=None,
            bolt=bolt, washer={"calculate": washer}, steel_known=lambda net: {"synthetic": True})
        with patch.object(m, "_methods", return_value=fake):
            call = lambda field=field, fp=fp, c=c, plan=plan, pins=pins: m._reduce(field, fp, c, plan, pins, {"nominal_seat_geometry": {"synthetic": True}})
            if mode == "success":
                result = call()
                expected = field["source_inputs"]["shafts"][1]["axis_id"]
                assert result["shaft"]["first_yield_reference_exceedances"] == [expected]
                assert result["shaft"]["complete_bolt_resistance"] is None
                assert len(result["missing_current_inputs"]["mixed_stacks"]) == 8
                assert result["washers"]["reviewed_nominal_seat_geometry"] == {"synthetic": True}
            else:
                rejection(call, KeyboardInterrupt if mode == "timber_interrupt" else ValueError)
        assert timber.intake is old_intake and m.canonical(field) == before
        if mode == "steel_census":
            assert "timber" not in events
        elif mode in {"timber_interrupt", "mixed_count"}:
            assert "shaft" not in events
        elif mode == "duplicate_shaft":
            assert "washer" not in events
        observed[mode] = {"steel_calls": sum(e.startswith("steel:") for e in events),
                          "downstream_events": [e for e in events if not e.startswith("steel:")],
                          "current_intake_restored": True, "synthetic_payload_unchanged": True}
    return observed


def output_checks(fixture, directory):
    m = fixture.m
    kwargs = {"expected_field_sha256": "0" * 64, "expected_receipt_sha256": "0" * 64}
    observed = {}
    for mode, error_type in (("serialization", ValueError), ("interrupt", KeyboardInterrupt), ("exit", SystemExit)):
        output = directory / (mode + "-output.json")

        def consume(*args, mode=mode, **kwargs):
            if mode == "interrupt":
                raise KeyboardInterrupt("synthetic interruption")
            if mode == "exit":
                raise SystemExit("synthetic exit")
            return {"execution": {}, "value": float("nan")}

        with patch.object(m, "consume", side_effect=consume) as callback:
            rejection(lambda output=output: m.consume_to_file("unused", "unused", output, **kwargs), error_type)
            record = json.loads(output.read_bytes())
            assert record["status"] == "FAILED" and record["release"] == m.RELEASE
            assert record["exception"]["type"] == error_type.__name__
            before = output.read_bytes()
            rejection(lambda output=output: m.consume_to_file("unused", "unused", output, **kwargs), FileExistsError)
            assert output.read_bytes() == before and callback.call_count == 1
        observed[mode] = {"failed_JSON_retained": True, "retry_rejected_before_callback": True}
    target = directory / "existing-target.json"
    target.write_text("preserved")
    link = directory / "existing-target-link.json"
    link.symlink_to(target)
    with patch.object(m, "consume", side_effect=AssertionError("must not consume")) as callback:
        rejection(lambda: m.consume_to_file("unused", "unused", link, **kwargs), FileExistsError)
        assert callback.call_count == 0 and target.read_text() == "preserved" and link.is_symlink()
    observed["existing_target_symlink"] = {"target_preserved": True, "callback_calls": 0}
    return observed


def main():
    verify()
    commands = [[sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(TARGET / "test_followups.py")],
                [sys.executable, "-m", "ruff", "check", str(TARGET)]]
    runs = []
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        runs.append({"command": command, "exit_code": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    fixture = load(TARGET / "test_followups.py", "independent_followup_fixtures")
    with tempfile.TemporaryDirectory(prefix="followup-testing-review-") as scratch:
        directory = Path(scratch)
        boundaries = boundary_checks(fixture, directory)
        closure, ast_restore = source_and_restore_checks(fixture, directory)
        adapter = synthetic_adapter_checks(fixture, directory)
        output = output_checks(fixture, directory)
    verify()
    report = {
        "schema": "eoere_current_followup_independent_testing_review/v1",
        "status": "SOURCE_AND_SYNTHETIC_TESTING_PASSED_GENUINE_CONSUMPTION_REMAINS_HELD",
        "confirmed_substantial_findings": [],
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
        "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)},
        "exact_targets_unchanged_before_after": True, "supplied_checks": runs,
        "source_closure_matches_frozen_verification": closure,
        "additional_authentication_order_controls": boundaries,
        "additional_private_AST_failure_restore_controls": ast_restore,
        "additional_synthetic_adapter_controls": adapter,
        "additional_reserved_output_controls": output,
        "testing_assessment": [
            "Thirty supplied tests and Ruff pass independently; known-answer functions use tiny algebra and declared scalar scenarios.",
            "The supplied tests reject wrong raw hashes/gate, old aliases and release claims, verify 100/22/27 metadata composition, and test physical point/couple ownership, same-cut bolt roots and AST second-read authentication.",
            "Supplied fake callback tests verify 44 steel calls over separate scenarios, current timber intake and restoration, 100 shaft references, unknown mixed stacks and retained exceedances.",
            "Additional controls reject nonidentical gate payloads, contradictory gate pins, malformed receipt schema/success and metadata failure before any rich reducer callback.",
            "Additional synthetic adapter controls stop downstream stages after steel/mixed/shaft census failures and restore timber intake through KeyboardInterrupt and subsequent washer failure.",
            "The supplied real subprocess checks cover CLI races, dangling links, failed/abrupt attempts and import laziness. Additional serialization/interruption/exit failures keep valid FAILED records and reject retries; existing-target symlinks preserve their targets.",
            "No complete real reduction is tested or claimed. Frozen numerical helper correctness is bounded by existing tiny known answers; current steel, timber, shaft and all200 washer outputs need genuine admitted-field execution after all required reviews.",
            "The 112 nominal seat geometry proof remains separate from raw-stock washer diagnostics; group/splitting/net/restraint/actual pressure/product/complete-joint resistance remain unresolved.",
        ],
        "execution": {"genuine_force_field_consumed": False, "genuine_reducer_callback": False,
                      "actual_BREP_or_CAD": False, "panel_or_frame_K_q_native_or_browser": False,
                      "source_metadata_and_tiny_synthetic_callbacks_only": True},
        "release": fixture.m.RELEASE,
        "tool_versions": {"python": sys.version.split()[0], **{n: importlib.metadata.version(n) for n in ("numpy", "scipy", "pytest", "ruff")}},
        "retention": "Keep this compact review pair active with the source followups. Private temporary synthetic/CLI files were removed; no archived evidence, shared source, staging or commits were changed.",
    }
    path = OWN.with_name("receipt.json")
    path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "bytes": path.stat().st_size,
                      "confirmed_substantial_findings": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
