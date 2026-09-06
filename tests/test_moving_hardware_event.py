"""Prepare from actual passed quiet evidence without Gmsh, Docker or a solver."""
import copy
import json
from pathlib import Path

import pytest

from fea import hardware_mass_cache as mass
from fea import moving_hardware_balance as balance
from fea import moving_hardware_event as event


@pytest.fixture(scope="module")
def evidence():
    return event.archived_files(event.ARCHIVE.read_bytes())


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    return event.prepare(tmp_path_factory.mktemp("moving-event"))


def test_actual_event_preserves_pose_physics_and_reference(prepared, evidence):
    context = json.loads((prepared / "context.json").read_bytes())
    original = json.loads(evidence["prepared/context.json"])
    for key in ("nodes", "elements", "bodies", "surfaces", "material", "contact_pairs", "quiescent_diagnostic_gates",
                "diagnostic_reference_scales", "angular_reference_mm_local", "initial_interface_gap_bounds_mm"):
        assert context[key] == original[key], key
    assert set(context["cases"]) == {"moving"}
    assert context["cases"]["moving"] == {**event.control.DIRECT_MOVING_SETTINGS,
        "initial_velocity_mm_s": {"BOLT_NUT": [0, 0, 0], "WASHER": [-100, 100, 0]}}
    assert context["passed_quiet_evidence"]["archive_sha256"] == event.ARCHIVE_SHA
    output = (prepared / "moving.inp").read_text()
    assert output == event.control.deck(context, "moving")
    assert "*STEP,NLGEOM,INC=200\n*DYNAMIC,DIRECT,ALPHA=0\n1e-07,2e-05\n" in output
    assert not any(card in output for card in ("*CLOAD", "*DLOAD", "*BOUNDARY", "*TIE", "EXPLICIT", "*DAMPING"))
    rows = output.split("*INITIAL CONDITIONS,TYPE=VELOCITY\n")[1].split("*STEP")[0].splitlines()
    velocities = {(int(n), int(d)): float(v) for n, d, v in (row.split(",") for row in rows)}
    assert len(velocities) == 3 * len(context["nodes"])
    for body, values in (("BOLT_NUT", (0, 0, 0)), ("WASHER", (-100, 100, 0))):
        assert all(velocities[n, d] == value for n in context["bodies"][body]["nodes"] for d, value in enumerate(values, 1))
    mass.deck_mesh(output, context)
    assert not (prepared / "quiescent.inp").exists() and not (prepared / "launch.json").exists()
    with pytest.raises(ValueError, match="explicitly prepared"):
        event.control.deck(context, "quiescent")


def test_all_inputs_sources_and_full_protocol_are_frozen(prepared):
    context = json.loads((prepared / "context.json").read_bytes())
    inventory = json.loads((prepared / "freeze.json").read_bytes())["files_sha256"]
    assert set(inventory) == {p.relative_to(prepared).as_posix() for p in prepared.rglob("*") if p.is_file() and p != prepared / "freeze.json"}
    assert all(event.control.digest((prepared / n).read_bytes()) == h for n, h in inventory.items())
    for group in ("input_sha256", "source_sha256"):
        assert all(inventory["frozen/" + n] == h for n, h in context[group].items())
    assert set(context["audit_source_sha256"]) == {Path(n).name for n in event.EVALUATOR_FILES}
    assert all(context["source_sha256"][n] == h for n, h in context["audit_source_sha256"].items())
    assert context["deck_sha256"] == {"moving": inventory["moving.inp"]}
    protocol = context["moving_protocol"]
    assert {k: protocol[k] for k in event.PROTOCOL} == event.PROTOCOL
    expected = event.SECTION + event.DOCUMENT.read_text().split(event.SECTION, 1)[1]
    assert protocol["document_section"] == expected
    assert protocol["document_section_sha256"] == event.control.digest(expected.encode())
    assert protocol["solver_timeout_seconds"] == 1800 and protocol["outer_timeout_seconds"] == 1820
    assert protocol["native_ke_rtol"] == 5e-6 and protocol["native_ke_floor_over_E_star"] == 1e-8
    assert {key: protocol[key] for key in balance.GATES} == balance.GATES
    assert "Not prepared" in protocol["refinement"]["authorization"]


@pytest.mark.parametrize("fault", ["velocity", "step", "duration", "count", "pose", "flag", "extra"])
def test_moving_direct_deck_cannot_silently_change_contract(prepared, fault):
    context = json.loads((prepared / "context.json").read_bytes())
    settings = context["cases"]["moving"]
    if fault == "velocity":
        settings["initial_velocity_mm_s"]["BOLT_NUT"][0] = 1
    elif fault == "pose":
        context["pose_variant"] = "unknown"
    elif fault == "flag":
        settings["direct_moving"] = "true"
    else:
        key = {"step": "initial_dt_s", "duration": "total_time_s", "count": "maximum_increment_count", "extra": "direct_quiescent"}[fault]
        settings[key] = 1
    with pytest.raises(ValueError):
        event.control.deck(context, "moving")


def test_existing_quiet_deck_is_byte_identical(evidence):
    context = json.loads(evidence["prepared/context.json"])
    assert event.control.deck(context, "quiescent").encode() == evidence["prepared/quiescent.inp"]


def test_wrong_archive_rejected_before_output(tmp_path):
    path = tmp_path / "wrong.tar.gz"
    path.write_bytes(b"not passed quiet evidence")
    with pytest.raises(ValueError, match="archive identity"):
        event.prepare(tmp_path / "output", archive=path)
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("fault", ["audit", "pose", "mass"])
def test_failed_or_inconsistent_evidence_cannot_prepare(evidence, fault):
    files = dict(evidence)
    if fault == "audit":
        key = "audit/report.json"
        value = json.loads(files[key])
        value["status"] = "QUIESCENT OUTPUT GATES FAILED"
    elif fault == "pose":
        key = "prepared/frozen/pose/report.json"
        value = json.loads(files[key])
        value["quadratic_mesh"]["radial_gap_lower_mm"] = -1
    else:
        key = "mass/report.json"
        value = json.loads(files[key])
        value["blocks_sha256"] = "0" * 64
    files[key] = json.dumps(value).encode()
    with pytest.raises(ValueError, match="quiet audit|pose proof|mass identity"):
        event.build_context(files, event.SECTION)


def test_changed_loaded_protocol_is_rejected_before_reads(tmp_path, monkeypatch):
    altered = copy.deepcopy(event.PROTOCOL)
    altered["native_ke_rtol"] = 1
    monkeypatch.setattr(event, "PROTOCOL", altered)
    with pytest.raises(ValueError, match="source/configuration"):
        event.prepare(tmp_path / "output", archive=tmp_path / "missing")


@pytest.mark.parametrize("source", ["document", "event", "evaluator"])
def test_mid_replay_drift_cannot_publish(tmp_path, monkeypatch, source):
    read, loads, changed = Path.read_bytes, json.loads, []
    target = {"event": Path(event.__file__).resolve(), "document": event.DOCUMENT.resolve(),
              "evaluator": event.ROOT / "fea/moving_hardware_balance.py"}[source]
    def load(*args, **kwargs):
        changed.append(True)
        return loads(*args, **kwargs)
    monkeypatch.setattr(json, "loads", load)
    monkeypatch.setattr(Path, "read_bytes", lambda p: read(p) + b"\n" if changed and p.resolve() == target else read(p))
    with pytest.raises(ValueError, match="source/configuration|input/source drift"):
        event.prepare(tmp_path / "output")
    assert not (tmp_path / "output").exists()
