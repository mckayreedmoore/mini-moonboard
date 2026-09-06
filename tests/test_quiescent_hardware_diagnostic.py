"""Replay retained native partial output without CAD, Gmsh, Docker or solver."""
import json
import tarfile
from pathlib import Path

import pytest

from fea import quiescent_hardware_diagnostic as diagnostic
from fea.quiescent_hardware_diagnostic import INPUTS, diagnose, sections, sha


@pytest.fixture(scope="module")
def files():
    archive = Path(__file__).resolve().parents[1] / "fea/results/moving_hardware_control/second-quiescent-timeout.tar.gz"
    with tarfile.open(archive) as bundle:
        return {name: bundle.extractfile("solve/" + str(diagnostic.input_path(name))).read()
                for name in INPUTS}


def changed_dat(files, text):
    changed = dict(files)
    changed["control.dat"] = text.encode()
    exit_record = json.loads(changed["exit.json"])
    exit_record["output_sha256"]["control.dat"] = sha(changed["control.dat"])
    changed["exit.json"] = json.dumps(exit_record).encode()
    return changed


def test_actual_retained_first_state_proves_failure_without_acceptance(files):
    result = diagnose(files)
    assert result["status"] == "PARTIAL QUIESCENT GATES FAILED"
    assert result["accepted_time_s"] == 1e-8
    assert result["aligned_contact_point_rows"] == 32376
    assert result["body_results"]["WASHER"]["max_speed_mm_s"] == pytest.approx(9.36767476997)
    assert result["body_results"]["BOLT_NUT"]["max_speed_mm_s"] == pytest.approx(6.38201236759)
    assert result["pair_results"]["WASHER_BORE"]["max_penetration_mm"] == 1.768548e-5
    assert result["pair_results"]["WASHER_HEAD"]["point_rows"] == 14544
    assert result["pair_results"]["WASHER_BORE"]["point_rows"] == 17832
    assert len(result["failures"]) == 4
    assert result["native_total_contact_energy_qualified"] is False
    assert result["CF_impulse_qualified"] is False
    assert result["pair_results"]["WASHER_BORE"]["sum_recorded_CELS_N_mm"] > 6.83658698012575e-6


def test_raw_identity_and_missing_input_rejected(files):
    changed = dict(files)
    changed["control.dat"] += b"changed"
    with pytest.raises(ValueError, match="hash"):
        diagnose(changed)
    del changed["context.json"]
    with pytest.raises(ValueError, match="inputs"):
        diagnose(changed)


def test_published_diagnostic_replays_exactly(files):
    directory = Path(__file__).resolve().parents[1] / "fea/results/moving_hardware_control/diagnostics/partial-quiescent-gb9rn5dl"
    report = json.loads((directory / "report.json").read_text())
    source_hash = report.pop("diagnostic_source_sha256")
    assert source_hash == sha((directory / "quiescent_hardware_diagnostic.py.snapshot").read_bytes())
    assert diagnose(files) == report


def test_duplicate_integration_points_are_retained_in_sequence():
    blocks = sections("contact values\n1 2 3\n1 2 4\nnext header\n")
    assert blocks[0][1] == [["1", "2", "3"], ["1", "2", "4"]]


@pytest.mark.parametrize("fault", ["time", "count", "nonfinite", "unterminated"])
def test_partial_contact_rows_cannot_be_silently_misaligned(files, fault):
    text = files["control.dat"].decode()
    prefix = "contact stress (slave element+face,press,tang1,tang2)"
    before, section = text.split(prefix, 1)
    if fault == "time":
        section = section.replace("0.1000000E-07", "0.2000000E-07", 1)
    elif fault in ("count", "nonfinite"):
        rows = section.splitlines()
        index = next(i for i, line in enumerate(rows) if line.strip() and line.strip()[0].isdigit() and len(line.split()) == 5)
        if fault == "count":
            del rows[index]
        else:
            values = rows[index].split()
            values[2] = "NaN"
            rows[index] = " ".join(values)
        section = "\n".join(rows)
    else:
        text = text.split("total contact spring energy for time", 1)[0]
    changed = changed_dat(files, text if fault == "unterminated" else before + prefix + section)
    with pytest.raises(ValueError, match="time|align|Nonfinite|Unterminated"):
        diagnose(changed)


def test_unknown_quadratic_slave_face_is_rejected_even_with_aligned_rows(files):
    text = files["control.dat"].decode()
    for label in ("relative contact displacement", "contact stress", "contact spring energy"):
        before, section = text.split(label + " (slave element+face", 1)
        rows = section.splitlines()
        index = next(i for i, line in enumerate(rows) if line.strip() and line.strip()[0].isdigit() and len(line.split()) in (3, 5))
        values = rows[index].split()
        values[0] = "999999999"
        rows[index] = " ".join(values)
        text = before + label + " (slave element+face" + "\n".join(rows)
    with pytest.raises(ValueError, match="slave face"):
        diagnose(changed_dat(files, text))


def test_writer_rejects_source_edit_before_call_and_constant_only_edit(tmp_path, monkeypatch):
    source = Path(diagnostic.__file__).resolve()
    read = Path.read_bytes
    original = read(source)
    for changed in (original + b"\n# concurrent editor\n", original.replace(b"Partial accepted-state", b"Changed accepted-state")):
        with monkeypatch.context() as patch:
            patch.setattr(Path, "read_bytes", lambda path, data=changed: data if path.resolve() == source else read(path))
            with pytest.raises(ValueError, match="source changed after import"):
                diagnostic.write_diagnostic(tmp_path / "missing", tmp_path / "outputs")
        assert not (tmp_path / "outputs").exists()


def test_writer_rejects_mutated_constants_and_loaded_functions(tmp_path, monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(diagnostic, "LIMITS", "changed")
        with pytest.raises(ValueError, match="configuration changed"):
            diagnostic.write_diagnostic(tmp_path, tmp_path / "outputs")
    with monkeypatch.context() as patch:
        patch.setattr(diagnostic, "diagnose", lambda files: {})
        with pytest.raises(ValueError, match="Loaded diagnostic function"):
            diagnostic.write_diagnostic(tmp_path, tmp_path / "outputs")
    assert not (tmp_path / "outputs").exists()


def test_mid_calculation_source_edit_leaves_no_success_report(files, tmp_path, monkeypatch):
    for name, data in files.items():
        target = tmp_path / diagnostic.input_path(name)
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
    source = Path(diagnostic.__file__).resolve()
    read, loads = Path.read_bytes, json.loads
    original, changed = read(source), []
    def during_calculation(*args, **kwargs):
        changed.append(True)
        return loads(*args, **kwargs)
    monkeypatch.setattr(json, "loads", during_calculation)
    monkeypatch.setattr(Path, "read_bytes", lambda path: original + b"\n# edited\n"
                        if path.resolve() == source and changed else read(path))
    with pytest.raises(ValueError, match="source changed after import"):
        diagnostic.write_diagnostic(tmp_path, tmp_path / "outputs")
    assert changed and not (tmp_path / "outputs").exists()


@pytest.mark.parametrize("field", ["quiescent_diagnostic_gates", "diagnostic_reference_scales"])
def test_context_only_gate_or_reference_edit_cannot_change_frozen_assessment(files, field):
    changed = dict(files)
    context = json.loads(files["context.json"])
    context[field] = {key: 1e30 for key in context[field]}
    changed["context.json"] = json.dumps(context).encode()
    with pytest.raises(ValueError, match="Frozen diagnostic input hash"):
        diagnose(changed)


def test_changed_freeze_cannot_rebind_context_without_original_launch(files):
    changed = dict(files)
    freeze = json.loads(files["freeze.json"])
    freeze["inputs_sha256"]["context.json"] = "0" * 64
    changed["freeze.json"] = json.dumps(freeze).encode()
    with pytest.raises(ValueError, match="Launch/freeze identity"):
        diagnose(changed)
