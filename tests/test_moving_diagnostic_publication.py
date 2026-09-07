"""Portable retained-observable checks; no DAT/mass-matrix replay or solver."""
import json
import math
from pathlib import Path

import pytest

from fea.publish_moving_fixture import checked_members
from fea.results.stitch_joint_mesh.publisher import sha

HERE = Path(__file__).resolve().parents[1] / "fea/results/coarse_moving_control"
SHA = "3155d9c023e550698cc62fa684c30b38a15015bf54a40f4bfbe59c57cbeb0e43"


@pytest.fixture(scope="module")
def evidence():
    files = checked_members(HERE / "fail-only-diagnostic.tar.gz", SHA)
    refs = json.loads(files["references.json"])
    linked = {name: checked_members(HERE / name, digest) for name, digest in refs["archive_sha256"].items()}
    return files, refs, linked, json.loads(files[refs["report"]])


def test_complete_runtime_provenance_caps_owned_cleanup_and_source_closure(evidence):
    files, refs, linked, report = evidence
    runtime, outcome, command, cleanup = [json.loads(files["diagnostic/"+n]) for n in
                                         ("runtime.json", "exit.json", "command.json", "cleanup.json")]
    assert len(files) == 17
    assert set(files) == {"diagnostic/"+n for n in outcome["files_sha256"]} | {
        "diagnostic/exit.json", "references.json", "members.json", "selection.json"}
    assert all(sha(files["diagnostic/"+n]) == h for n, h in outcome["files_sha256"].items())
    assert refs["selected_runtime"] == "fea/generated/moving-hardware-diagnostic-runs/fail-only-diagnostic-yr39fect"
    assert outcome["status"] == "DIAGNOSTIC PROCESS COMPLETED"
    assert outcome["returncode"] == outcome["cleanup_returncode"] == 0 and outcome["exceptions"] == []
    assert outcome["container_stopped_successfully_before_cleanup"] is True
    assert 0 < outcome["elapsed_seconds"] < 900
    assert (runtime["inner_timeout_seconds"], runtime["outer_timeout_seconds"]) == (900, 920)
    assert runtime["memory_bytes"] == runtime["memory_plus_swap_bytes"] == 8*1024**3 and runtime["cpus"] == 2
    assert command[command.index("timeout"):] == ["timeout", "--signal=TERM", "--kill-after=5", "900",
        "python3", "-m", "fea.moving_hardware_diagnostic", "--output", "/output"]
    assert command[command.index("--user")+1] == "1000:1000"
    assert all(flag in command for flag in ("--network=none", "--read-only", "--memory=8g", "--memory-swap=8g", "--cpus=2"))
    assert runtime["image"] == "sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646"
    assert runtime["image"] in command
    cid = outcome["owned_container_id"]
    assert cid == "19cf58929b002e88153794bfb61e562b3325fd452df73303d2b47f825ad49631"
    assert files["diagnostic/container.id"].decode().strip() == cid
    probe = json.loads(files["diagnostic/container-probe.json"])
    assert probe["returncode"] == 0 and probe["command"] == ["docker", "inspect", cid]
    container, = json.loads(probe["stdout"])
    assert container["Id"] == cid and container["Name"] == "/"+command[3]
    assert container["Config"]["Image"] == runtime["image"]
    assert container["State"]["Running"] is False and container["State"]["OOMKilled"] is False
    assert container["State"]["ExitCode"] == 0
    assert cleanup["command"] == ["docker", "rm", "-f", cid]
    assert cleanup["returncode"] == 0 and cleanup["container_id"] == cleanup["stdout"].strip() == cid
    assert json.loads(files["selection.json"])["selected_solve"] == runtime["selected_solve"]
    assert sha(files["diagnostic/supervisor.py.snapshot"]) == runtime["supervisor_sha256"]
    assert sha(files["diagnostic/command.json"]) == runtime["command_sha256"]
    assert sha(files["diagnostic/solver-exit.json.snapshot"]) == runtime["solver_exit_sha256"]
    assert files["diagnostic/solver-exit.json.snapshot"] == linked["native-other.tar.gz"]["solve/result/exit.json"]
    assert all(sha(files["diagnostic/"+n+".snapshot"]) == h for n, h in runtime["frozen_source_sha256"].items())
    assert report["diagnostic_source_sha256"] == runtime["frozen_source_sha256"]["moving_hardware_diagnostic.py"]
    assert files[refs["report"].replace("report.json", "moving_hardware_diagnostic.py.snapshot")] == files["diagnostic/moving_hardware_diagnostic.py.snapshot"]
    prepared = linked["preparation.tar.gz"]
    assert all(sha(prepared["prepared/frozen/"+n]) == h for n, h in report["evaluator_sha256"].items())
    for key, name in (("context_sha256", "prepared/context.json"), ("deck_sha256", "prepared/moving.inp"),
                      ("mass_blocks_sha256", "mass/blocks.json.gz")):
        assert report[key] == sha(prepared[name])
    assert report["archive_sha256"] == refs["archive_sha256"]
    assert report["DAT_sha256"] == refs["DAT_sha256"] == json.loads(files["diagnostic/solver-exit.json.snapshot"])["output_sha256"]["control.dat"]
    assert linked["first-audit.tar.gz"]["audit/audit.log"].decode().rstrip().endswith("ValueError: Contact pressure/penetration differs")
    assert report["original_failure"] == "ValueError: Contact pressure/penetration differs; original full balance was not evaluated"
    assert report["status"] == outcome["numerical_status"] == "FAIL-ONLY OBSERVATIONS; ORIGINAL AUDIT REMAINS FAILED"
    assert report["qualified"] is False and report["contact_energy_qualified"] is False


def test_retained_201_state_impulses_residuals_and_thresholds_recompute(evidence):
    _, _, linked, report = evidence
    context = json.loads(linked["preparation.tar.gz"]["prepared/context.json"])
    scales, gates = context["diagnostic_reference_scales"], report["thresholds"]
    assert all(context["moving_protocol"][n] == v for n, v in gates.items())
    states = report["states"]
    assert len(states) == 201
    assert [s["time_s"] for s in states] == pytest.approx([i*1e-7 for i in range(201)], rel=5e-6, abs=0)
    assert states[0]["source"] == "RECONSTRUCTED INITIAL CONDITIONS; NO PRINTED t0"
    impulses = {p: [0., 0., 0.] for p in ("WASHER_HEAD", "WASHER_BORE")}
    moments = {p: [0., 0., 0.] for p in impulses}
    failures = []
    def check(quantity, value, limit):
        if value > limit:
            failures.append(quantity)
    for i, state in enumerate(states):
        assert set(state) == {"time_s", "source", "bodies", "pairs", "assembly_linear_drift", "assembly_angular_drift"}
        assert set(state["pairs"]) == set(impulses) and set(state["bodies"]) == {"BOLT_NUT", "WASHER"}
        for name, pair in state["pairs"].items():
            assert set(pair) == {"F", "Mc", "J", "K"}
            if i:
                dt = state["time_s"]-states[i-1]["time_s"]
                for axis in range(3):
                    impulses[name][axis] += dt*(states[i-1]["pairs"][name]["F"][axis]+pair["F"][axis])/2
                    moments[name][axis] += dt*(states[i-1]["pairs"][name]["Mc"][axis]+pair["Mc"][axis])/2
            else:
                assert pair["F"] == pair["Mc"] == [0., 0., 0.]
            assert pair["J"] == pytest.approx(impulses[name], rel=1e-12, abs=1e-20)
            assert pair["K"] == pytest.approx(moments[name], rel=1e-12, abs=1e-20)
        changes = {"P": [], "Hc": []}
        for name, body in state["bodies"].items():
            base_fields = {"P", "Hc", "mass", "KE_reconstructed", "delta_P", "delta_Hc", "linear_residual", "angular_residual"}
            assert set(body) == base_fields | ({"EMAS", "ELKE", "native_mass_relative_error", "native_KE_absolute_error", "native_KE_comparison_scale"} if i else set())
            for key, integral, residual_key, gate, scale in (("P", impulses, "linear_residual", "body_linear_residual_over_P_star", "P_star_tonne_mm_s"),
                    ("Hc", moments, "angular_residual", "body_angular_residual_over_H_star", "H_star_tonne_mm2_s")):
                delta = [body[key][a]-states[0]["bodies"][name][key][a] for a in range(3)]
                residual = [delta[a]-(1 if name == "WASHER" else -1)*math.fsum(v[a] for v in integral.values()) for a in range(3)]
                assert body["delta_"+key] == pytest.approx(delta, rel=1e-12, abs=1e-20)
                assert body[residual_key] == pytest.approx(residual, rel=1e-12, abs=1e-20)
                changes[key].append(delta)
                check(name+residual_key, math.hypot(*residual), gates[gate]*scales[scale])
            if i:
                mass_error = abs(body["EMAS"]/body["mass"]-1)
                ke_error = abs(body["ELKE"]-body["KE_reconstructed"])
                ke_scale = max(body["ELKE"], abs(body["KE_reconstructed"]), gates["native_ke_floor_over_E_star"]*scales["E_star_N_mm"])
                assert body["native_mass_relative_error"] == mass_error
                assert body["native_KE_absolute_error"] == ke_error and body["native_KE_comparison_scale"] == ke_scale
                check(name+"mass", mass_error, gates["native_mass_rtol"])
                check(name+"KE", ke_error, gates["native_ke_rtol"]*ke_scale)
        for key, field, gate, scale in (("P", "assembly_linear_drift", "assembly_linear_drift_over_P_star", "P_star_tonne_mm_s"),
                ("Hc", "assembly_angular_drift", "assembly_angular_drift_over_H_star", "H_star_tonne_mm2_s")):
            drift = [math.fsum(v[a] for v in changes[key]) for a in range(3)]
            assert state[field] == pytest.approx(drift, rel=1e-12, abs=1e-20)
            check(field, math.hypot(*drift), gates[gate]*scales[scale])
    assert failures == report["additional_failures"] == []
