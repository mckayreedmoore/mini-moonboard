"""Replay preserved posed quiet evidence without CAD, Gmsh or a solver."""
import gzip
import json
from pathlib import Path

import pytest

from fea import hardware_mass_cache as mass
from fea import moving_hardware_pose as pose
from fea import quiescent_hardware_audit as audit
from fea.publish_moving_fixture import checked_members
from fea.results.stitch_joint_mesh.publisher import sha

RESULTS = Path(__file__).resolve().parents[1] / "fea/results"
ARCHIVE_SHA = "0149053d26aa67e1c5f2d22de7e9b1e058d24f7188ef02324fe3cc6508bb86ea"
REFERENCE_SHA = "978f55507db7a92bf6d985b841dae38ecdb6748063802119c811a13cff808631"


@pytest.fixture(scope="module")
def evidence():
    files = checked_members(RESULTS / "posed_hardware_control/posed-quiet.tar.gz", ARCHIVE_SHA)
    reference = checked_members(RESULTS / "moving_hardware_control/fourth-direct-quiescent.tar.gz", REFERENCE_SHA)
    return files, reference


def hashes(files, prefix, inventory):
    assert all(sha(files[prefix + name]) == digest for name, digest in inventory.items())


def test_prepared_pose_and_launch_have_closed_original_provenance(evidence):
    files, reference = evidence
    refs = json.loads(files["references.json"])
    assert refs["archive"] == "../moving_hardware_control/fourth-direct-quiescent.tar.gz"
    assert refs["archive_sha256"] == REFERENCE_SHA
    assert set(refs["members_sha256"]) == {"geometry/geometry.json", "geometry/leg_stitch_right_1_bolt_nut.step",
                                           "geometry/leg_stitch_right_1_washer_inner.step"}
    hashes(reference, "", refs["members_sha256"])
    prepared = json.loads(files["prepared/freeze.json"])["files_sha256"]
    assert set(prepared) == {n.removeprefix("prepared/") for n in files if n.startswith("prepared/")} - {"freeze.json"}
    hashes(files, "prepared/", prepared)
    context = json.loads(files["prepared/context.json"])
    for group in ("input_sha256", "source_sha256"):
        hashes(files, "prepared/frozen/", context[group])
    centred_prefix = "prepared/frozen/centred/"
    centred = json.loads(files[centred_prefix + "context.json"])
    centred_inventory = json.loads(files[centred_prefix + "freeze.json"])["files_sha256"]
    hashes(files, centred_prefix, centred_inventory)
    for name in ("context.json", "freeze.json", "quiescent.inp", *centred_inventory):
        assert files[centred_prefix + name] == reference["prepared/" + name]
    pose_prefix = "prepared/frozen/pose/"
    proof = json.loads(files[pose_prefix + "report.json"])
    assert proof["context_sha256"] == sha(files[centred_prefix + "context.json"])
    assert proof["prepared_freeze_sha256"] == sha(files[centred_prefix + "freeze.json"])
    assert files[pose_prefix + "original-context.json"] == files[centred_prefix + "context.json"]
    assert proof["posed_nodes_sha256"] == sha(files[pose_prefix + "posed-nodes.json"])
    hashes(files, pose_prefix, {n + ".snapshot": h for n, h in proof["source_sha256"].items()})
    assert proof["translation_local_mm"] == list(pose.TRANSLATION_MM)
    assert proof["CAD"]["geometry_sha256"] == refs["members_sha256"]["geometry/geometry.json"]
    assert {"geometry/" + n: h for n, h in proof["CAD"]["step_sha256"].items()} == {
        n: h for n, h in refs["members_sha256"].items() if n.endswith(".step")}
    nodes, quantization = pose.posed_nodes(centred)
    normalized = json.loads(json.dumps({"nodes": nodes, "quantization": quantization}))
    assert json.loads(files[pose_prefix + "posed-nodes.json"]) == normalized
    assert context["nodes"] == normalized["nodes"]
    assert proof["quadratic_mesh"] == json.loads(json.dumps(pose.mesh_clearance(centred)))
    assert proof["quadratic_mesh"]["strictly_separated_selected_surfaces"] is True
    for key in ("elements", "material", "contact_pairs", "quiescent_diagnostic_gates", "cases", "integration_intent"):
        assert context[key] == centred[key]
    assert set(context["cases"]) == {"quiescent"}
    assert context["angular_reference_mm_local"] == [1.001, .7356, 0]
    for node in context["bodies"]["BOLT_NUT"]["nodes"]:
        assert context["nodes"][str(node)] == centred["nodes"][str(node)]
    freeze = json.loads(files["solve/freeze.json"])
    hashes(files, "solve/frozen/", freeze["inputs_sha256"])
    assert files["solve/frozen/prepared-freeze.json"] == files["prepared/freeze.json"]
    assert files["solve/frozen/context.json"] == files["prepared/context.json"]
    assert files["solve/frozen/control.inp"] == files["prepared/quiescent.inp"] == files["solve/result/control.inp"]
    assert sha(files["prepared/quiescent.inp"]) == context["deck_sha256"]["quiescent"]
    outcome = json.loads(files["solve/result/exit.json"])
    hashes(files, "solve/result/", outcome["output_sha256"])
    assert files["solve/result/container.id"].decode().strip() == outcome["owned_container_id"]
    launch = json.loads(files["solve/launch.json"])
    assert launch["freeze_sha256"] == sha(files["solve/freeze.json"])
    assert freeze["solver_timeout_seconds"] == 180 and launch["outer_timeout_seconds"] == 200
    command = launch["command"]
    assert command[command.index("timeout"):] == ["timeout", "--signal=TERM", "--kill-after=5", "180",
                                                 "python3", "/frozen/moving_hardware_solve.py", "--execute"]
    assert all(option in command for option in ("--network=none", "--read-only", "--memory=4g", "--memory-swap=4g",
                                                 "--cpus=2", "--pids-limit=256"))
    probe = json.loads(json.loads(files["solve/result/container-probe.json"])["stdout"])[0]
    assert probe["Name"] == "/" + command[3]


def test_actual_posed_quiet_output_replays_retained_audit(evidence):
    files, _ = evidence
    inputs = {n: files["solve/" + audit.retained.input_path(n).as_posix()] for n in audit.INPUTS}
    replayed = audit.audit(inputs)
    recorded = json.loads(files["audit/report.json"])
    sources = recorded.pop("source_sha256")
    hashes(files, "audit/", {n + ".snapshot": h for n, h in sources.items()})
    assert recorded == json.loads(json.dumps(replayed))
    assert replayed["status"] == "COMPLETE QUIESCENT OUTPUT GATES PASSED"
    assert replayed["failures"] == []
    assert len(replayed["states"]) == 20 and replayed["states"][-1]["time_s"] == 2e-6
    assert replayed["core_reference_mass_qualified"] is False
    for state in replayed["states"]:
        assert state["CNUM"] == state["total_CELS_N_mm"] == state["max_penetration_mm"] == 0
        for body in state["bodies"].values():
            assert all(body[k] == 0 for k in ("max_displacement_mm", "max_velocity_mm_s", "ELKE_N_mm", "ELSE_N_mm"))
        for pair in state["pairs"].values():
            assert pair["area_mm2"] == 0
            assert pair["force_N"] == pair["origin_moment_N_mm"] == (0, 0, 0)


def test_posed_mass_operators_match_every_native_body_mass(evidence):
    files, _ = evidence
    data = files["prepared/context.json"]
    context = json.loads(data)
    assert files["mass/context.json"] == data
    assert files["mass/quiescent.inp"] == files["prepared/quiescent.inp"]
    assert files["mass/prepared-freeze.json"] == files["prepared/freeze.json"]
    report = json.loads(files["mass/report.json"])
    assert report["context_sha256"] == sha(data)
    assert report["prepared_freeze_sha256"] == sha(files["prepared/freeze.json"])
    assert report["deck_sha256"] == sha(files["prepared/quiescent.inp"])
    hashes(files, "mass/", {n + ".snapshot": h for n, h in report["source_sha256"].items()})
    assert sha(files["mass/blocks.json.gz"]) == report["blocks_sha256"]
    cache = json.loads(gzip.decompress(files["mass/blocks.json.gz"]))
    mass.deck_mesh(files["mass/quiescent.inp"].decode(), context)
    totals = mass.validate_cache(cache, data)
    assert totals == report["body_mass_tonne"] and cache["gmsh_version"] == report["gmsh_version"]
    assert context["diagnostic_reference_scales"]["reference_mass_tonne"] == pytest.approx(
        totals["native_four_point"]["WASHER"], rel=1e-12, abs=0)
    times = audit.history(files["solve/result/control.sta"].decode(), 2e-6)
    states = audit.blocks(files["solve/result/control.dat"].decode(), times)
    assert len(states) == 20
    for body in ("BOLT_NUT", "WASHER"):
        for state in states:
            rows = audit.numeric(state[f"total mass for set {body} and time"], 1)
            assert len(rows) == 1 and rows[0][0] > 0
            assert abs(rows[0][0] / totals["native_four_point"][body] - 1) <= 5e-6
