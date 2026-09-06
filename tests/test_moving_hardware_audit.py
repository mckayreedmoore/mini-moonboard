"""Synthetic raw-run pipeline checks; no native moving result or integration claim."""
import copy
import gzip
import json
import math
from pathlib import Path

import pytest
from test_moving_hardware_replay import (
    inputs as replay_inputs,  # noqa: F401 -- pytest fixture registration
)

from fea import moving_hardware_audit as audit


def encoded(value):
    return json.dumps(value, allow_nan=False).encode()


def seal(files):
    """Rehash synthetic recorded bytes; never recompute the approval itself."""
    freeze = json.loads(files["freeze.json"])
    freeze["inputs_sha256"] = {n[7:]: audit.event.control.digest(b) for n, b in files.items() if n.startswith("frozen/")}
    files["freeze.json"] = encoded(freeze)
    launch = json.loads(files["launch.json"])
    launch["freeze_sha256"] = audit.event.control.digest(files["freeze.json"])
    files["launch.json"] = encoded(launch)
    outcome = json.loads(files["result/exit.json"])
    outcome["output_sha256"] = {n[7:]: audit.event.control.digest(b) for n, b in files.items()
                                if n.startswith("result/") and n != "result/exit.json"}
    files["result/exit.json"] = encoded(outcome)
    return files


@pytest.fixture(scope="module")
def run_files(replay_inputs):  # noqa: F811 -- pytest fixture injection
    data, deck, cache, dat, sta = copy.deepcopy(replay_inputs)
    context = json.loads(data)
    loaded = audit.sources()
    context["moving_protocol"] = copy.deepcopy(audit.event.PROTOCOL)
    context["passed_quiet_evidence"] = {"archive_sha256": audit.event.ARCHIVE_SHA,
        "audit_status": "COMPLETE QUIESCENT OUTPUT GATES PASSED"}
    context["angular_reference_mm_local"] = [1.001, .7356, 0.]
    context["source_sha256"] = {n: audit.event.control.digest(b) for n, b in loaded.items()}
    context["audit_source_sha256"] = {Path(n).name: context["source_sha256"][Path(n).name] for n in audit.event.EVALUATOR_FILES}
    context["diagnostic_reference_scales"] = {"reference_mass_tonne": 2., "P_star_tonne_mm_s": 2*math.sqrt(20000),
        "E_star_N_mm": 20000., "H_star_tonne_mm2_s": 57.15*2*math.sqrt(20000)}
    data = encoded(context)
    cache.update(context_sha256=audit.event.control.digest(data), gmsh_version="synthetic-test-only")
    blocks = gzip.compress(encoded(cache), mtime=0)
    prepared = encoded({"files_sha256": {"context.json": audit.event.control.digest(data),
        "moving.inp": audit.event.control.digest(deck), **{"frozen/"+n: audit.event.control.digest(b) for n, b in loaded.items()}}})
    mass_sources = audit.event.mass.sources()
    mass_report = {"case": "moving", "context_sha256": audit.event.control.digest(data),
        "deck_sha256": audit.event.control.digest(deck), "prepared_freeze_sha256": audit.event.control.digest(prepared),
        "blocks_sha256": audit.event.control.digest(blocks), "source_sha256": {n: audit.event.control.digest(b) for n, b in mass_sources.items()},
        "body_mass_tonne": audit.event.mass.validate_cache(cache, data), "gmsh_version": cache["gmsh_version"]}
    cid, image = "a"*64, "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
    files = {"frozen/context.json": data, "frozen/control.inp": deck, "frozen/prepared-freeze.json": prepared,
        "frozen/moving_hardware_solve.py": loaded["moving_hardware_solve.py"],
        "frozen/build_manifest.json": (audit.event.ROOT / "fea/mortar_build/baseline-njusw3dz/build_manifest.json").read_bytes(),
        "frozen/mass/context.json": data, "frozen/mass/moving.inp": deck, "frozen/mass/prepared-freeze.json": prepared,
        "frozen/mass/report.json": encoded(mass_report), "frozen/mass/blocks.json.gz": blocks,
        "result/control.inp": deck, "result/control.dat": dat.encode(), "result/control.sta": sta.encode(),
        "result/container.id": cid.encode(), "result/control.frd": b"not parsed; inventory must still bind this file",
        "result/container-probe.json": encoded({"returncode": 0, "stdout": json.dumps([{
            "Id": cid, "Name": "/moving-synthetic", "Config": {"Image": image},
            "State": {"Running": False, "OOMKilled": False, "ExitCode": 0}}])}),
        "result/cleanup.json": encoded({"returncode": 0, "container_id": cid, "stdout": cid}),
        "result/exit.json": encoded({"returncode": 0, "cleanup_returncode": 0, "owned_container_id": cid,
            "status": "SOLVER COMPLETED; AUDIT PENDING", "exceptions": [], "container_stopped_successfully_before_cleanup": True}),
        "freeze.json": encoded({"case": "moving", "image": image, "solver_timeout_seconds": 1800}),
        "launch.json": encoded({"outer_timeout_seconds": 1820,
            "command": audit.launcher.command(Path("/synthetic"), solver_timeout_seconds=1800, case="moving")})}
    files.update({"frozen/evaluators/"+n+".snapshot": b for n, b in loaded.items()})
    files.update({"frozen/mass/"+n+".snapshot": b for n, b in mass_sources.items()})
    approval = {"case": "moving", "context_sha256": audit.event.control.digest(data),
        "deck_sha256": audit.event.control.digest(deck), "prepared_freeze_sha256": audit.event.control.digest(prepared),
        "passed_quiet_archive_sha256": audit.event.ARCHIVE_SHA,
        "mass_report_sha256": audit.event.control.digest(files["frozen/mass/report.json"]),
        "mass_blocks_sha256": audit.event.control.digest(blocks),
        "evaluator_sha256": {"evaluators/"+n+".snapshot": audit.event.control.digest(b) for n, b in loaded.items()},
        "inputs_sha256": {n[7:]: audit.event.control.digest(b) for n, b in files.items() if n.startswith("frozen/")}}
    files["frozen/moving-preflight.json"] = encoded(approval)
    return seal(files)


def test_native_success_does_not_pass_bad_numerical_history(run_files):
    report = audit.audit(run_files)
    assert report["status"] == "COARSE MOVING AUDIT FAILED"
    assert report["accepted_states"] == 200 and not report["refinement_qualified"]
    assert len(report["physical_Gauss8"]) == 201
    assert "NOT PRINTED" in report["initial_state_source"]


def analytic_fields(files, *, transfer):
    """Arithmetic native-format fixture, not a contact trajectory or native result.

    Fixed supplied positions isolate the P/H/energy gate algebra. They do not
    assert the independently solved kinematics or traction directions are real.
    """
    files = dict(files)
    context = json.loads(files["frozen/context.json"])
    cache = json.loads(gzip.decompress(files["frozen/mass/blocks.json.gz"]))
    centres = {}
    for name, blocks in cache["operators"]["native_four_point"].items():
        centres[name] = [sum(sum(row)*context["nodes"][str(n)][a]
            for ids, matrix in blocks.values() for n, row in zip(ids, matrix, strict=True))/2 for a in range(3)]
    direction = audit.balance.difference(centres["WASHER"], centres["BOLT_NUT"])
    direction = tuple(v/math.hypot(*direction) for v in direction)
    times = [i*1e-7 for i in range(1, 201)]
    tables = audit.quiet.blocks(files["result/control.dat"].decode(), times)
    output = []
    for t, state in zip(times, tables, strict=True):
        core = tuple(3*(t/2e-5)**2*v if transfer else 0. for v in direction)
        velocities = {"BOLT_NUT": core, "WASHER": audit.balance.difference((-100., 100., 0.), core)}
        energies = {n: sum(v*v for v in values) for n, values in velocities.items()}
        for name, body in context["bodies"].items():
            for label, values in (("displacements", (0., 0., 0.)), ("velocities", velocities[name])):
                state[f"{label} (vx,vy,vz) for set {name} and time"] = [
                    str(n)+" "+" ".join(format(v, ".17g") for v in values) for n in body["nodes"]]
            state[f"total kinetic energy for set {name} and time"] = [format(energies[name], ".17g")]
            state[f"total internal energy for set {name} and time"] = [
                format(20000-sum(energies.values()) if name == "WASHER" else 0., ".17g")]
        if transfer:
            force = tuple(-6*t/(2e-5)**2*v for v in direction)
            moment = audit.balance.cross(centres["WASHER"], force)
            # The synthetic two-tonne operators require correspondingly scaled
            # effective contact areas. These are arithmetic, not CAD-area data.
            area, penalty = 1e6, 100000.
            magnitude = math.hypot(*force)
            pressure = magnitude/area
            spring = .5*pressure**2/penalty*area
            state["total internal energy for set WASHER and time"] = [format(20000-sum(energies.values())-2*spring, ".17g")]
            state["total contact spring energy for time"] = [format(2*spring, ".17g")]
            state["total number of contact elements for time"] = ["2"]
            for pair in context["contact_pairs"]:
                element, face = context["surfaces"][pair["slave"]]["faces"][0]
                owner = f"{element} {face} "
                state["relative contact displacement (slave element+face,normal,tang1,tang2) for all contact elements and time"].append(owner+f"{-pressure/penalty:.17g} 0 0")
                state["contact stress (slave element+face,press,tang1,tang2) for all contact elements and time"].append(owner+f"{pressure:.17g} 0 0")
                state["contact spring energy (slave element+face,energy) for all contact elements and time"].append(owner+f"{spring:.17g}")
                rows = state[f"statistics for slave set {pair['slave']}, master set {pair['master']} and time"]
                rows[1] = " ".join(format(v, ".17g") for v in (*force, *moment))
                rows[3] = " ".join(format(v, ".17g") for v in (*centres["WASHER"], *(-v/magnitude for v in force)))
                rows[5], rows[7] = "0 0 0", f"{area:.17g} {-magnitude:.17g} 0"
        output.extend(name+f" {t:.17g}\n"+"\n".join(rows) for name, rows in state.items())
    files["result/control.dat"] = "\n".join(output).encode()
    return seal(files)


@pytest.mark.parametrize("transfer,expected", [(False, "COARSE MOVING AUDIT INCONCLUSIVE"),
    (True, "COMPLETE COARSE MOVING GATES PASSED; REFINEMENT REQUIRED")])
def test_raw_arithmetic_pipeline_distinguishes_transfer_and_refinement(run_files, transfer, expected):
    report = audit.audit(analytic_fields(run_files, transfer=transfer))
    assert report["status"] == expected
    assert not report["refinement_qualified"]
    assert report["balance"]["failures"] == []


@pytest.mark.parametrize("removed", ["both", "WASHER_HEAD", "WASHER_BORE"])
def test_resealed_cf_without_its_contact_rows_fails(run_files, removed):
    files = analytic_fields(run_files, transfer=True)
    context = json.loads(files["frozen/context.json"])
    times = [i*1e-7 for i in range(1, 201)]
    states = audit.quiet.blocks(files["result/control.dat"].decode(), times)
    remove_faces = {tuple(context["surfaces"][name]["faces"][0]) for name in
                   (("WASHER_HEAD", "WASHER_BORE") if removed == "both" else (removed,))}
    state = states[99]  # An intermediate contradiction must not hide at the endpoint.
    for label in ("relative contact displacement", "contact stress", "contact spring energy ("):
        key = next(n for n in state if n.startswith(label))
        state[key] = [row for row in state[key] if tuple(map(int, row.split()[:2])) not in remove_faces]
    rows = state["contact spring energy (slave element+face,energy) for all contact elements and time"]
    state["total number of contact elements for time"] = [str(len(rows))]
    state["total contact spring energy for time"] = [format(sum(float(row.split()[2]) for row in rows), ".17g")]
    files["result/control.dat"] = "\n".join(name+f" {t:.17g}\n"+"\n".join(rows)
        for t, state in zip(times, states, strict=True) for name, rows in state.items()).encode()
    with pytest.raises(ValueError, match="no contact rows"):
        audit.audit(seal(files))


@pytest.mark.parametrize("slave", ["WASHER_HEAD", "WASHER_BORE"])
def test_resealed_zero_pair_tractions_cannot_have_nonzero_cf(run_files, slave):
    files = analytic_fields(run_files, transfer=True)
    context = json.loads(files["frozen/context.json"])
    times = [i*1e-7 for i in range(1, 201)]
    states = audit.quiet.blocks(files["result/control.dat"].decode(), times)
    state = states[99]
    face = tuple(context["surfaces"][slave]["faces"][0])
    old_energy = float(state["total contact spring energy for time"][0])
    for prefix, width in (("relative contact displacement", 3), ("contact stress", 3), ("contact spring energy (", 1)):
        key = next(n for n in state if n.startswith(prefix))
        state[key] = [" ".join(row.split()[:2])+" 0"*width if tuple(map(int, row.split()[:2])) == face else row
                      for row in state[key]]
    energy_rows = state["contact spring energy (slave element+face,energy) for all contact elements and time"]
    new_energy = sum(float(row.split()[2]) for row in energy_rows)
    state["total contact spring energy for time"] = [format(new_energy, ".17g")]
    key = "total internal energy for set WASHER and time"
    state[key] = [format(float(state[key][0])+old_energy-new_energy, ".17g")]
    # Keep totals, row ownership/counts, and the entire balance history consistent.
    files["result/control.dat"] = "\n".join(name+f" {t:.17g}\n"+"\n".join(rows)
        for t, state in zip(times, states, strict=True) for name, rows in state.items()).encode()
    with pytest.raises(ValueError, match="Nonzero CF contradicts zero point traction"):
        audit.audit(seal(files))


def test_present_zero_tractions_allow_positive_area_with_zero_cf(run_files):
    files = analytic_fields(run_files, transfer=False)
    context = json.loads(files["frozen/context.json"])
    times = [i*1e-7 for i in range(1, 201)]
    states = audit.quiet.blocks(files["result/control.dat"].decode(), times)
    state = states[99]
    for pair in context["contact_pairs"]:
        element, face = context["surfaces"][pair["slave"]]["faces"][0]
        for prefix, width in (("relative contact displacement", 3), ("contact stress", 3), ("contact spring energy (", 1)):
            key = next(n for n in state if n.startswith(prefix))
            state[key].append(f"{element} {face}"+" 0"*width)
        cf = state[f"statistics for slave set {pair['slave']}, master set {pair['master']} and time"]
        cf[3], cf[5], cf[7] = "0 0 0 1 0 0", "0 0 0", "1 0 0"
    state["total number of contact elements for time"] = ["2"]
    files["result/control.dat"] = "\n".join(name+f" {t:.17g}\n"+"\n".join(rows)
        for t, state in zip(times, states, strict=True) for name, rows in state.items()).encode()
    report = audit.audit(seal(files))
    assert report["status"] == "COARSE MOVING AUDIT INCONCLUSIVE"
    assert report["balance"]["failures"] == []


@pytest.mark.parametrize("fault", ["constant", "source", "loaded_function"])
def test_current_loaded_source_identity_is_enforced(run_files, monkeypatch, fault):
    if fault == "constant":
        monkeypatch.setitem(audit.balance.GATES, "native_mass_rtol", 1.)
    elif fault == "loaded_function":
        monkeypatch.setattr(audit.balance, "assess", lambda *args: {})
    else:
        original = Path.read_bytes
        def changed(path):
            data = original(path)
            return data+b"\n# concurrent checkout\n" if path.name == "moving_hardware_audit.py" else data
        monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(ValueError, match="configuration|source changed|differs from source"):
        audit.audit(run_files)


@pytest.mark.parametrize("name", ["result/control.dat", "result/control.frd", "frozen/context.json",
    "frozen/mass/blocks.json.gz", "frozen/evaluators/moving_hardware_balance.py.snapshot"])
def test_unsealed_missing_or_changed_input_fails(run_files, name):
    for remove in (False, True):
        files = dict(run_files)
        if remove:
            del files[name]
        else:
            files[name] += b"changed"
        with pytest.raises((KeyError, ValueError)):
            audit.audit(files)


@pytest.mark.parametrize("fault", ["preflight", "source", "mass_source", "terminal", "cleanup", "short", "missing_field", "gate"])
def test_rehashed_faults_still_fail(run_files, fault):
    files = dict(run_files)
    if fault == "short":
        files["result/control.sta"] = b"\n".join(files["result/control.sta"].splitlines()[:-1])
    elif fault == "missing_field":
        files["result/control.dat"] = files["result/control.dat"].replace(b"velocities (", b"unknown (", 1)
    else:
        name, key, value = {
            "preflight": ("frozen/moving-preflight.json", "mass_blocks_sha256", "0"*64),
            "source": ("frozen/context.json", "source_sha256", {}),
            "mass_source": ("frozen/mass/report.json", "source_sha256", {}),
            "terminal": ("result/exit.json", "returncode", 124),
            "cleanup": ("result/cleanup.json", "returncode", 1),
            "gate": ("frozen/context.json", "moving_protocol", {})}[fault]
        record = json.loads(files[name])
        record[key] = value
        files[name] = encoded(record)
    with pytest.raises((ValueError, KeyError)):
        audit.audit(seal(files))


def test_cli_streams_unused_payload_and_publishes_unique_report(run_files, tmp_path, monkeypatch):
    root = tmp_path / "run"
    for name, data in run_files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    original = Path.read_bytes
    def guarded(path):
        assert path.suffix != ".frd", "FRD must only be stream hashed"
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", guarded)
    output = audit.write_audit(root, tmp_path / "reports")
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "COARSE MOVING AUDIT FAILED"
    assert report["input_sha256"]["result/control.frd"] == audit.event.control.digest(run_files["result/control.frd"])


def test_oversize_dat_rejected_before_payload_read(tmp_path, monkeypatch):
    target = tmp_path / "result/control.dat"
    target.parent.mkdir()
    with target.open("wb") as stream:
        stream.truncate(audit.MAX_DAT_BYTES + 1)
    def forbidden(path):
        raise AssertionError("oversized payload was read")
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    with pytest.raises(ValueError, match="size cap"):
        audit.FileInputs(tmp_path)


@pytest.mark.parametrize("fault", ["source", "unparsed_output"])
def test_mid_audit_drift_cannot_publish_report(run_files, tmp_path, monkeypatch, fault):
    root = tmp_path / "run"
    for name, data in run_files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    original = Path.read_bytes
    saw_dat = False
    def changed(path):
        nonlocal saw_dat
        data = original(path)
        if path == root / "result/control.dat":
            saw_dat = True
            if fault == "unparsed_output":
                (root / "result/control.frd").write_bytes(b"drift during evaluation")
        if fault == "source" and saw_dat and path.name == "moving_hardware_audit.py":
            return data+b"\n# changed while reconstructing\n"
        return data
    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(ValueError, match="source changed|input changed|source/input drift"):
        audit.write_audit(root, tmp_path / "reports")
    assert not (tmp_path / "reports").exists()


def test_direct_lazy_mapping_rescans_unparsed_output_before_pass(run_files, tmp_path, monkeypatch):
    files = analytic_fields(run_files, transfer=True)
    for name, data in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    selected = audit.FileInputs(tmp_path)
    original = Path.read_bytes
    def mutate_frd(path):
        data = original(path)
        if path == tmp_path / "result/control.dat":
            (tmp_path / "result/control.frd").write_bytes(b"changed after the initial scan")
        return data
    monkeypatch.setattr(Path, "read_bytes", mutate_frd)
    with pytest.raises(ValueError, match="input changed"):
        audit.audit(selected)
