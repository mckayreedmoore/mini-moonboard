import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from fea import native_dynamic_control as control
from fea.dynamic_momentum import momentum


def output(velocity=None):
    text = ""
    for label in ("displacements", "velocities"):
        text += f"\n {label} (vx,vy,vz) for set BODY and time 1.0000000E-03\n\n"
        text += "\n".join(f"{n} " + " ".join(map(str, velocity(n) if velocity and label == "velocities"
                                                   else (.1, .2, .3))) for n in range(1, 11)) + "\n"
    for name, value in (("kinetic energy", ".01"), ("mass", ".1666667"), ("internal energy", "0")):
        text += f"\n total {name} for set BODY and time 1.0000000E-03\n\n {value}\n"
    # Native EMAS also writes inertia and center of gravity; ignore those.
    text += "\n total mass moment of inertia (xx,yy,zz,xy,xz,yz) for set BODY and time 1.0000000E-03\n\n1 2 3 4 5 6\n"
    return text


def test_four_decks_are_bounded_unforced_single_tets():
    for case in control.CASES:
        deck = control.deck(case)
        assert "*DYNAMIC,ALPHA=0\n1.e-3,1.e-3,1.e-8,1.e-3" in deck
        assert "EXPLICIT" not in deck
        assert "*ELEMENT,TYPE=C3D10,ELSET=BODY\n1,1,2,3,4,5,6,7,8,9,10" in deck
        assert "*ELASTIC\n1.,0.3\n*DENSITY\n1." in deck
        assert "FREQUENCY=1\nU,V" in deck
        assert "TOTALS=ONLY\nELKE,EMAS,ELSE" in deck
        assert (",NLGEOM" in deck) == case.endswith("nlgeom")
        assert not any(keyword in deck for keyword in ("*BOUNDARY", "*CONTACT", "*CLOAD", "*DLOAD"))
        velocities = deck.split("*INITIAL CONDITIONS,TYPE=VELOCITY\n")[1].split("*STEP")[0].splitlines()
        assert len(velocities) == 30
        assert velocities[0] == "1,1,1."
        assert all(v.endswith(",0.") for v in velocities[1:])
    assert control.nodes() != control.nodes(True)


def test_native_source_explicit_is_a_presence_switch_and_alpha_reads_value():
    source = control.SOURCE / "dynamics.f"
    if not source.exists():
        pytest.skip("Archived CalculiX 2.21 source required")
    manifest = json.loads(control.BUILD.read_text())
    assert control.sha(source) == manifest["upstream_files_sha256"]["./CalculiX/ccx_2.21/src/dynamics.f"]
    text = source.read_text()
    assert "elseif(textpart(i)(1:8).eq.'EXPLICIT') then\n          iexpl=2" in text
    assert "if(textpart(i)(1:6).eq.'ALPHA=') then" in text
    assert "read(textpart(i)(7:26),'(f20.0)',iostat=istat) alpha(1)" in text
    for case in control.CASES:
        dynamic = next(line for line in control.deck(case).splitlines() if line.startswith("*DYNAMIC"))
        assert not any(parameter.startswith("EXPLICIT") for parameter in dynamic.split(",")[1:])


def test_parser_requires_complete_matched_actual_fields():
    states = control.parse_dat(output())
    assert states[.001]["V"][1] == (.1, .2, .3)
    assert states[.001]["EMAS"] == .1666667
    for bad in (output().replace("total kinetic energy", "other energy"),
                output().replace("10 0.1 0.2 0.3", ""),
                output().replace("0.1 0.2 0.3", "nan 0.2 0.3"), output() + output()):
        with pytest.raises(ValueError):
            control.parse_dat(bad)
    for time in ("0", "-1", "NaN", "Inf"):
        with pytest.raises(ValueError, match="times"):
            control.parse_dat(output().replace("1.0000000E-03", time))


def test_exact_image_limits_and_frozen_mount(tmp_path):
    cmd = control.command(tmp_path, "straight-linear")
    assert cmd[cmd.index("--name") + 1] == f"native-{tmp_path.name}-straight-linear"
    assert control.IMAGE in cmd
    assert "--network=none" in cmd and "--memory=2g" in cmd
    assert f"{tmp_path / 'frozen'}:/frozen:ro" in cmd
    assert cmd[cmd.index("timeout"):] == ["timeout", "--signal=TERM", "--kill-after=2", "20",
                                          "python3", "/frozen/native_dynamic_control.py", "--execute-case", "straight-linear"]


def test_timeout_cleans_exact_container_and_prevents_rerun(tmp_path, monkeypatch):
    freeze(tmp_path)
    calls = []
    def run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[1] == "run":
            assert kwargs["timeout"] == 35
            raise subprocess.TimeoutExpired(cmd, 35)
        return subprocess.CompletedProcess(cmd, 0, b"retained", b"")
    monkeypatch.setattr(control.subprocess, "run", run)
    with pytest.raises(subprocess.TimeoutExpired):
        control.launch(tmp_path)
    expected = f"native-{tmp_path.name}-straight-linear"
    assert calls[-1] == ["docker", "rm", "-f", expected]
    assert (tmp_path / "straight-linear/console.log").exists()
    exit_report = json.loads((tmp_path / "straight-linear/exit.json").read_text())
    assert exit_report["exceptions"][0]["type"] == "TimeoutExpired"
    assert "console.log" in exit_report["output_sha256"]
    with pytest.raises(FileExistsError):
        control.launch(tmp_path)


def test_changed_frozen_inputs_rejected_before_container(tmp_path, monkeypatch):
    (tmp_path / "input.inp").write_text("changed")
    (tmp_path / "freeze.json").write_text(json.dumps({"image": control.IMAGE, "inputs_sha256": {"input.inp": "wrong"}}))
    monkeypatch.setattr(control.subprocess, "run", lambda *a, **k: pytest.fail("must not launch"))
    with pytest.raises(ValueError, match="Frozen"):
        control.launch(tmp_path)


def test_analysis_uses_printed_velocity_and_retains_gauss8(tmp_path, monkeypatch):
    native_mode_files(tmp_path, "straight-linear")
    def blocks(scale):
        return {1: (tuple(range(1, 11)), tuple(tuple(scale if i == j else 0 for j in range(10)) for i in range(10)))}
    monkeypatch.setitem(sys.modules, "dynamic_momentum", SimpleNamespace(
        calculix_221_mass=lambda *a: blocks(1), consistent_mass=lambda *a: blocks(2), momentum=momentum))
    actual = output(lambda n: (2, 0, 0) if n == 1 else (0, 0, 0))
    (tmp_path / "control.dat").write_text(actual.replace(" .01\n", " 2\n").replace(" .1666667\n", " 10\n"))
    (tmp_path / "control.sta").write_text("1 1 1 2 .001 .001 .001\n")
    control.analyze("straight-linear", tmp_path)
    report = json.loads((tmp_path / "comparison.json").read_text())
    assert report["qualified"]
    assert report["states"][0]["four_point"]["kinetic_energy"] == pytest.approx(2)
    assert report["states"][0]["Gauss8"]["kinetic_energy"] == pytest.approx(4)
    (tmp_path / "control.sta").write_text("1 1 1 2 .0005 .0005 .0005\n1 2 1 2 .001 .001 .0005\n")
    with pytest.raises(ValueError, match="every accepted"):
        control.analyze("straight-linear", tmp_path)


@pytest.mark.parametrize("case", ["straight-linear", "curved-nlgeom"])
@pytest.mark.parametrize("mode", ["zero", "rigid", "rotation"])
def test_zero_or_rigid_actual_velocity_cannot_qualify(tmp_path, monkeypatch, mode, case):
    native_mode_files(tmp_path, case)
    xyz = control.nodes(case.startswith("curved"))
    velocities = {n: ((0, 0, 0) if mode == "zero" else (1, 2, 3) if mode == "rigid" else (-p[1], p[0], 0))
                  for n, p in xyz.items()}
    def blocks(scale):
        return {1: (tuple(xyz), tuple(tuple(scale if i == j else 0 for j in range(10)) for i in range(10)))}
    # Deliberately distinct operators ensure the affine gate independently rejects rigid fields.
    monkeypatch.setitem(sys.modules, "dynamic_momentum", SimpleNamespace(
        calculix_221_mass=lambda *a: blocks(1), consistent_mass=lambda *a: blocks(2), momentum=momentum))
    energy = .5*sum(v*v for row in velocities.values() for v in row)
    (tmp_path / "control.dat").write_text(output(velocities.__getitem__).replace(" .01\n", f" {energy}\n")
                                         .replace(" .1666667\n", " 10\n"))
    (tmp_path / "control.sta").write_text("1 1 1 2 .001 .001 .001\n")
    with pytest.raises(ValueError, match="qualification failed"):
        control.analyze(case, tmp_path)
    report = json.loads((tmp_path / "comparison.json").read_text())
    gates = report["final_accepted_state_discriminator_gates"]
    assert not gates["relative_affine_velocity_residual"]["passed"]
    assert gates["positive_kinetic_energy"]["passed"] == (mode != "zero")
    assert gates["relative_Gauss8_energy_contrast"]["passed"] == (mode != "zero")
    assert not report["qualified"]


@pytest.mark.parametrize("amplitude,physical_scale,failed_gate", [
    (1e-5, 2, "positive_kinetic_energy"), (2, 1, "relative_Gauss8_energy_contrast")])
def test_positive_energy_and_contrast_thresholds_are_independent(tmp_path, monkeypatch, amplitude, physical_scale, failed_gate):
    native_mode_files(tmp_path, "straight-linear")
    def blocks(scale):
        return {1: (tuple(range(1, 11)), tuple(tuple(scale if i == j else 0 for j in range(10)) for i in range(10)))}
    monkeypatch.setitem(sys.modules, "dynamic_momentum", SimpleNamespace(
        calculix_221_mass=lambda *a: blocks(1), consistent_mass=lambda *a: blocks(physical_scale), momentum=momentum))
    actual = output(lambda n: (amplitude, 0, 0) if n == 1 else (0, 0, 0))
    (tmp_path / "control.dat").write_text(actual.replace(" .01\n", f" {amplitude**2/2}\n")
                                         .replace(" .1666667\n", " 10\n"))
    (tmp_path / "control.sta").write_text("1 1 1 2 .001 .001 .001\n")
    with pytest.raises(ValueError, match="qualification failed"):
        control.analyze("straight-linear", tmp_path)
    gates = json.loads((tmp_path / "comparison.json").read_text())["final_accepted_state_discriminator_gates"]
    assert [name for name, gate in gates.items() if not gate["passed"]] == [failed_gate]


def native_mode_files(directory, case):
    (directory / "control.inp").write_text(control.deck(case))
    (directory / "solver.log").write_text("Dynamic analysis was selected\n")


def test_explicit_banner_rejected_even_with_implicit_deck(tmp_path):
    native_mode_files(tmp_path, "straight-linear")
    (tmp_path / "solver.log").write_text("Dynamic analysis was selected\nExplicit time integration: Volumetric COURANT\n")
    with pytest.raises(ValueError, match="Explicit time integration"):
        control.analyze("straight-linear", tmp_path)


def test_solver_success_and_analysis_failure_are_separate(tmp_path, monkeypatch):
    monkeypatch.setattr(control.subprocess, "run", lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0))
    def failed_analysis(*args):
        raise ValueError("Explicit time integration")
    monkeypatch.setattr(control, "analyze", failed_analysis)
    with pytest.raises(ValueError, match="Explicit"):
        control.run_case("straight-linear", tmp_path)
    assert json.loads((tmp_path / "solver-exit.json").read_text())["returncode"] == 0
    analysis = json.loads((tmp_path / "analysis-exit.json").read_text())
    assert not analysis["passed"]
    assert analysis["exception"]["type"] == "ValueError"
    assert (tmp_path / "solver.log").exists()


def freeze(directory):
    frozen = directory / "frozen"
    frozen.mkdir()
    source = frozen / "native_dynamic_control.py"
    source.write_bytes(Path(control.__file__).read_bytes())
    (directory / "freeze.json").write_text(json.dumps({"image": control.IMAGE,
        "inputs_sha256": {"frozen/native_dynamic_control.py": control.sha(source)}}))


@pytest.mark.parametrize("running,mutation", [(True, False), (False, True), (False, False)])
def test_running_container_and_changed_snapshot_rejected(tmp_path, monkeypatch, running, mutation):
    freeze(tmp_path)
    calls = []
    def run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[1] == "run" and mutation:
            (tmp_path / "frozen/native_dynamic_control.py").write_text("changed")
        data = json.dumps([{"State": {"Running": running, "ExitCode": 0, "OOMKilled": False}}]).encode()
        return subprocess.CompletedProcess(cmd, 0, data if cmd[1] == "inspect" else b"", b"")
    monkeypatch.setattr(control.subprocess, "run", run)
    if running or mutation:
        with pytest.raises((RuntimeError, ValueError)):
            control.launch(tmp_path)
        assert len([c for c in calls if c[1] == "run"]) == 1
    else:
        control.launch(tmp_path)
        assert len([c for c in calls if c[1] == "run"]) == 4
    report = json.loads((tmp_path / "straight-linear/exit.json").read_text())
    assert report["container_stopped_successfully_before_cleanup"] == (not running)
    assert "container-inspect.json" in report["output_sha256"]


def test_host_launcher_must_match_frozen_source(tmp_path, monkeypatch):
    freeze(tmp_path)
    source = tmp_path / "frozen/native_dynamic_control.py"
    source.write_text("different launcher")
    (tmp_path / "freeze.json").write_text(json.dumps({"image": control.IMAGE,
        "inputs_sha256": {"frozen/native_dynamic_control.py": control.sha(source)}}))
    monkeypatch.setattr(control.subprocess, "run", lambda *a, **k: pytest.fail("must not launch"))
    with pytest.raises(ValueError, match="Executing launcher"):
        control.launch(tmp_path)
