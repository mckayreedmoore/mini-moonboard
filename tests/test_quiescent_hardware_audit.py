"""Portable native-format replay; synthetic completion is not a solver result."""
import copy
import json
import re
import tarfile
from pathlib import Path

import pytest

from fea import quiescent_hardware_audit as audit


@pytest.fixture(scope="module")
def original():
    path = Path(__file__).resolve().parents[1] / "fea/results/moving_hardware_control/third-catalog-quiescent.tar.gz"
    with tarfile.open(path) as bundle:
        return {n: bundle.extractfile("solve/" + str(audit.retained.input_path(n))).read() for n in audit.INPUTS}


def reseal(files):
    context = json.loads(files["context.json"])
    context["deck_sha256"]["quiescent"] = audit.retained.sha(files["control.inp"])
    files["context.json"] = json.dumps(context).encode()
    freeze = json.loads(files["freeze.json"])
    for name in ("context.json", "control.inp"):
        freeze["inputs_sha256"][name] = audit.retained.sha(files[name])
    files["freeze.json"] = json.dumps(freeze).encode()
    launch = json.loads(files["launch.json"])
    launch["freeze_sha256"] = audit.retained.sha(files["freeze.json"])
    files["launch.json"] = json.dumps(launch).encode()
    outcome = json.loads(files["exit.json"])
    for name in ("control.inp", "control.dat", "control.sta", "container-probe.json", "cleanup.json"):
        outcome["output_sha256"][name] = audit.retained.sha(files[name])
    files["exit.json"] = json.dumps(outcome).encode()
    return files


@pytest.fixture(scope="module")
def complete(original):
    # Synthetic one-state completion built from native first-state formatting.
    files = dict(original)
    files["control.dat"] = re.split(rb"\n\s*INCREMENT\s+2\s*\n", files["control.dat"], maxsplit=1)[0]
    files["control.sta"] = b"\n".join(files["control.sta"].splitlines()[:3]) + b"\n"
    context = json.loads(files["context.json"])
    context["cases"]["quiescent"]["total_time_s"] = 1e-8
    files["context.json"] = json.dumps(context).encode()
    text = files["control.inp"].decode()
    match = re.search(r"^\*DYNAMIC[^\n]*\n([^\n]+)", text, re.MULTILINE)
    fields = match[1].split(",")
    fields[1] = "1e-8"
    files["control.inp"] = (text[:match.start(1)] + ",".join(fields) + text[match.end(1):]).encode()
    outcome = json.loads(files["exit.json"])
    outcome.update(returncode=0, status="SOLVER COMPLETED; AUDIT PENDING")
    files["exit.json"] = json.dumps(outcome).encode()
    probe = json.loads(files["container-probe.json"])
    containers = json.loads(probe["stdout"])
    containers[0]["State"]["ExitCode"] = 0
    probe["stdout"] = json.dumps(containers)
    files["container-probe.json"] = json.dumps(probe).encode()
    return reseal(files)


def test_retained_third_attempt_is_not_complete(original):
    with pytest.raises(ValueError, match="Incomplete solver"):
        audit.audit(original)
    with pytest.raises(ValueError, match="Incomplete requested STA duration"):
        audit.history(original["control.sta"].decode(), 2e-6)


def test_actual_published_direct_window_has_twenty_complete_zero_states():
    path = Path(__file__).resolve().parents[1] / "fea/results/moving_hardware_control/fourth-direct-quiescent.tar.gz"
    assert audit.retained.sha(path.read_bytes()) == "978f55507db7a92bf6d985b841dae38ecdb6748063802119c811a13cff808631"
    with tarfile.open(path) as bundle:
        files = {n: bundle.extractfile("solve/" + str(audit.retained.input_path(n))).read() for n in audit.INPUTS}
    report = audit.audit(files)
    published = path.parent / "diagnostics/quiet-audit-dcp8zhtm"
    recorded = json.loads((published / "report.json").read_text())
    sources = recorded.pop("source_sha256")
    assert all(audit.retained.sha((published / (name + ".snapshot")).read_bytes()) == digest
               for name, digest in sources.items())
    assert recorded == json.loads(json.dumps(report))
    assert report["status"] == "COMPLETE QUIESCENT OUTPUT GATES PASSED"
    assert len(report["states"]) == 20 and report["states"][-1]["time_s"] == 2e-6
    assert report["failures"] == [] and report["core_reference_mass_qualified"] is False
    assert all(v == 0 for v in report["pair_sampled_force_norm_integral_N_s"].values())
    for state in report["states"]:
        assert state["total_CELS_N_mm"] == state["max_penetration_mm"] == 0
        assert state["CNUM"] == 24801
        for body in state["bodies"].values():
            assert all(body[key] == 0 for key in ("max_displacement_mm", "max_velocity_mm_s", "ELKE_N_mm", "ELSE_N_mm"))
        assert state["bodies"]["WASHER"]["observed_mass_tonne"] == 6.463770e-6
        assert state["pairs"]["WASHER_BORE"]["area_mm2"] == 0
        for pair in state["pairs"].values():
            assert pair["force_N"] == pair["origin_moment_N_mm"] == (0, 0, 0)


def test_synthetic_complete_native_format_passes_quiet_only(complete):
    report = audit.audit(complete)
    assert report["status"] == "COMPLETE QUIESCENT OUTPUT GATES PASSED"
    assert report["core_reference_mass_qualified"] is False
    assert report["states"][0]["CNUM"] == 24801
    assert report["states"][0]["pairs"]["WASHER_BORE"]["area_mm2"] == 0
    assert report["pair_sampled_force_norm_integral_N_s"] == {"WASHER_HEAD": 0, "WASHER_BORE": 0}


def test_nodal_vectors_preserve_all_signed_components_and_integer_ownership():
    assert audit.nodal_vectors(["12 -1.25 2.5 -3e-2", "4 7 -8 9"], [4, 12]) == {
        12: (-1.25, 2.5, -.03), 4: (7., -8., 9.)}


@pytest.mark.parametrize("rows", [[], ["4 1 2 3"], ["4 1 2 3", "4 4 5 6"],
    ["4 1 2 3", "13 4 5 6"], ["4 1 2 3", "12.5 4 5 6"],
    ["4 1 2 3", "12 NaN 5 6"], ["4 1 2 3", "12 4 inf 6"],
    ["4 1 2 3", "12 4 5"], ["4 1 2 3", "12 4 5 6", "13 7 8 9"]])
def test_nodal_vectors_reject_incomplete_duplicate_foreign_or_nonfinite_rows(rows):
    with pytest.raises(ValueError):
        audit.nodal_vectors(rows, [4, 12])


@pytest.mark.parametrize("ids", [[], [4, 4], [4, 12.], [4, True], [4, -12]])
def test_nodal_vectors_reject_invalid_expected_ownership(ids):
    with pytest.raises(ValueError, match="Invalid body node ownership"):
        audit.nodal_vectors(["4 1 2 3", "12 4 5 6"], ids)


@pytest.mark.parametrize("missing", [None, "relative contact displacement", "contact stress",
                                    "contact spring energy (", "total number of contact elements",
                                    "total contact spring energy", "statistics for slave set WASHER_HEAD",
                                    "statistics for slave set WASHER_BORE"])
def test_explicit_zero_contact_output_is_distinct_from_missing_output(complete, missing):
    # Synthetic parser contract, not a recorded no-contact solver result.
    # CCX 2.21 printout/printoutcontact retain headers, totals and CF at CNUM=0.
    state = audit.blocks(complete["control.dat"].decode(), [1e-8])[0]
    inactive = state["statistics for slave set WASHER_BORE, master set CORE_SHANK and time"]
    for name in state:
        if name.startswith(("relative contact displacement", "contact stress", "contact spring energy (")):
            state[name] = []
        elif name.startswith(("total number of contact elements", "total contact spring energy")):
            state[name] = ["0"]
        elif name.startswith("statistics for slave set"):
            state[name] = list(inactive)
    text = "\n".join(name + " 1e-8\n" + "\n".join(rows) for name, rows in state.items()
                     if missing is None or not name.startswith(missing))
    files = dict(complete, **{"control.dat": text.encode()})
    if missing is not None:
        with pytest.raises(ValueError, match="Missing DAT block"):
            audit.audit(reseal(files))
    else:
        report = audit.audit(reseal(files))
        assert report["status"] == "COMPLETE QUIESCENT OUTPUT GATES PASSED"
        assert report["states"][0]["CNUM"] == 0
        assert all(pair["area_mm2"] == 0 for pair in report["states"][0]["pairs"].values())


@pytest.mark.parametrize("fault", ["missing_bore", "duplicate_time", "missing_node", "nonfinite_velocity", "cnum", "cels", "unknown_face", "truncated_cf"])
def test_incomplete_or_changed_native_output_rejected(complete, fault):
    files = dict(complete)
    text = files["control.dat"].decode()
    if fault == "missing_bore":
        text = text.split("statistics for slave set WASHER_BORE", 1)[0]
    elif fault == "duplicate_time":
        text += text
    elif fault in ("missing_node", "nonfinite_velocity"):
        before, after = text.split("velocities (vx,vy,vz) for set WASHER and time", 1)
        lines = after.splitlines()
        index = next(i for i, line in enumerate(lines) if len(line.split()) == 4)
        if fault == "missing_node":
            del lines[index]
        else:
            lines[index] = lines[index].replace("0.000000E+00", "NaN", 1)
        text = before + "velocities (vx,vy,vz) for set WASHER and time" + "\n".join(lines)
    elif fault == "cnum":
        text = text.replace("24801", "24802")
    elif fault == "cels":
        prefix, suffix = text.split("total contact spring energy for time", 1)
        text = prefix + "total contact spring energy for time" + suffix.replace("0.000000E+00", "1.000000E+00", 1)
    elif fault == "unknown_face":
        text = text.replace("39163          2", "999999999      2")
    else:
        text = text.rsplit("area,  normal force", 1)[0]
    files["control.dat"] = text.encode()
    with pytest.raises(ValueError):
        audit.audit(reseal(files))


def test_inactive_ancillary_allowance_is_narrow(complete):
    states = audit.blocks(complete["control.dat"].decode(), [1e-8])
    lines = states[0]["statistics for slave set WASHER_BORE, master set CORE_SHANK and time"]
    assert audit.contact_force(lines)["area_mm2"] == 0
    for index, value in ((1, "NaN 0 0 0 0 0"), (1, "1 0 0 0 0 0"), (7, "1 NaN NaN"), (3, "inf NaN NaN NaN NaN NaN")):
        changed = list(lines)
        changed[index] = value
        with pytest.raises(ValueError):
            audit.contact_force(changed)


def test_frozen_context_threshold_change_rejected(complete):
    files = dict(complete)
    context = json.loads(files["context.json"])
    context["quiescent_diagnostic_gates"]["max_velocity_mm_s"] = 1e10
    files["context.json"] = json.dumps(context).encode()
    with pytest.raises(ValueError, match="Frozen input hash"):
        audit.audit(files)


def test_quiet_gates_and_pair_impulse_cannot_cancel(complete):
    context = json.loads(complete["context.json"])
    base = audit.outputs(complete["control.dat"].decode(), [1e-8], context)[0]
    first, second = copy.deepcopy(base), copy.deepcopy(base)
    second["time_s"] = 2e-8
    first["pairs"]["WASHER_HEAD"]["force_N"] = [100, 0, 0]
    second["pairs"]["WASHER_HEAD"]["force_N"] = [-100, 0, 0]
    second["bodies"]["WASHER"]["max_velocity_mm_s"] = 1
    second["bodies"]["BOLT_NUT"]["max_displacement_mm"] = 1
    second["max_penetration_mm"] = 1
    second["total_CELS_N_mm"] = 1
    second["bodies"]["WASHER"]["observed_mass_tonne"] *= 2
    report = audit.assess([first, second], context)
    assert report["status"] == "QUIESCENT OUTPUT GATES FAILED"
    assert len(report["failures"]) == 7
    assert report["pair_sampled_force_norm_integral_N_s"]["WASHER_HEAD"] == pytest.approx(2e-6)


def test_source_drift_rejected_before_publication(tmp_path, monkeypatch):
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: read(p) + b"\n# changed" if p.resolve() == Path(audit.__file__).resolve() else read(p))
    with pytest.raises(ValueError, match="source/configuration changed"):
        audit.write_audit(tmp_path, tmp_path / "reports")
    assert not (tmp_path / "reports").exists()


def test_source_drift_during_calculation_cannot_publish(complete, tmp_path, monkeypatch):
    for name, data in complete.items():
        target = tmp_path / audit.retained.input_path(name)
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
    read, loads, changed = Path.read_bytes, json.loads, []
    def load(*args, **kwargs):
        changed.append(True)
        return loads(*args, **kwargs)
    monkeypatch.setattr(json, "loads", load)
    monkeypatch.setattr(Path, "read_bytes", lambda p: read(p) + b"\n# changed" if changed and p.resolve() == Path(audit.__file__).resolve() else read(p))
    with pytest.raises(ValueError, match="source/configuration changed"):
        audit.write_audit(tmp_path, tmp_path / "reports")
    assert changed and not (tmp_path / "reports").exists()


def test_missing_middle_dat_state_is_rejected(complete):
    context = json.loads(complete["context.json"])
    with pytest.raises(ValueError, match="Missing DAT block"):
        audit.outputs(complete["control.dat"].decode(), [1e-8, 2e-8], context)


@pytest.mark.parametrize("change", ["spc", "load", "tie", "initial_velocity", "direct"])
def test_hash_consistent_nonstationary_deck_is_rejected(complete, change):
    files = dict(complete)
    text = files["control.inp"].decode()
    if change in ("spc", "load", "tie"):
        card = {"spc": "*BOUNDARY\nWASHER,1,3\n", "load": "*DLOAD\nWASHER,GRAV,9810,0,0,-1\n", "tie": "*TIE\nWASHER_HEAD,CORE_HEAD\n"}[change]
        text = text.replace("*END STEP", card + "*END STEP")
    elif change == "direct":
        text = text.replace("*DYNAMIC,ALPHA=0", "*DYNAMIC,DIRECT,ALPHA=0")
    else:
        before, after = text.split("*INITIAL CONDITIONS,TYPE=VELOCITY\n")
        after = after.replace(",1,0.0", ",1,1.0", 1)
        text = before + "*INITIAL CONDITIONS,TYPE=VELOCITY\n" + after
    files["control.inp"] = text.encode()
    with pytest.raises(ValueError, match="stationary deck|actual initial velocity"):
        audit.audit(reseal(files))


def test_inactive_pair_cannot_contradict_point_energy(complete):
    text = complete["control.dat"].decode()
    before, after = text.split("contact spring energy (slave element+face,energy)", 1)
    after = after.replace("0.000000E+00", "1.000000E+00", 1)
    text = before + "contact spring energy (slave element+face,energy)" + after
    before, after = text.split("total contact spring energy for time", 1)
    after = after.replace("0.000000E+00", "1.000000E+00", 1)
    text = (before + "total contact spring energy for time" + after).replace("1.590512E+02", "0.000000E+00")
    with pytest.raises(ValueError, match="Inactive CF contradicts"):
        audit.outputs(text, [1e-8], json.loads(complete["context.json"]))
