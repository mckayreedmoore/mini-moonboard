"""Stream-verify raw terminal evidence; do not parse full DAT or run an audit."""
import gzip
import json
import re
from pathlib import Path

import pytest

from fea import moving_hardware_solve as launcher
from fea import quiescent_hardware_audit as quiet
from fea.publish_moving_fixture import checked_members
from fea.results.coarse_moving_control import publish_native as publication
from fea.results.stitch_joint_mesh.publisher import sha

HERE = publication.HERE
OTHER_SHA = "f90c6b421a4c91620823617a790252009795c782672c77087d4ece0d60c866c1"
EXPECTED = {
    "control.dat": (514571422, "1d106908563f4a8014c892d58cf31f7a95fac1d205679cfcd1016540b3def65a"),
    "control.frd": (736654536, "f7972f8fafb11e6d048209a47fc64e9d7cbca4b27cc40ef2eb74574389cd834b"),
}


@pytest.fixture(scope="module")
def manifest():
    return json.loads((HERE / "native-output.json").read_bytes())


@pytest.fixture(scope="module")
def other(manifest):
    selected = manifest["other_archive"]
    assert selected["file"] == "native-other.tar.gz" and selected["sha256"] == OTHER_SHA
    assert publication.identity(HERE / selected["file"]) == {k: selected[k] for k in ("sha256", "bytes")}
    assert selected["bytes"] <= publication.LIMIT
    return checked_members(HERE / selected["file"], selected["sha256"])


@pytest.mark.parametrize("name", EXPECTED)
def test_full_large_field_hashes_are_streamed(manifest, other, name):
    record = manifest["large_fields"][name]
    assert record["file"] == name + ".gz"
    identity = publication.identity(HERE / record["file"])
    assert identity == {"sha256": record["compressed_sha256"], "bytes": record["compressed_bytes"]}
    assert 0 < identity["bytes"] <= publication.LIMIT
    with gzip.open(HERE / record["file"], "rb") as stream:
        digest, size = publication.stream_digest(stream)
    assert (size, digest) == EXPECTED[name]
    assert (record["plain_bytes"], record["plain_sha256"]) == EXPECTED[name]
    assert json.loads(other["solve/result/exit.json"])["output_sha256"][name] == digest


def test_exact_native_inventory_is_complete_without_numerical_claim(manifest, other):
    assert manifest["status"] == "RAW SOLVER COMPLETION EVIDENCE ONLY"
    assert manifest["numerical_audit_included"] is False
    assert manifest["source_run"] == "fea/generated/moving-hardware-solves/moving-9gsvcbgg"
    assert set(manifest["large_fields"]) == set(EXPECTED)
    outcome = json.loads(other["solve/result/exit.json"])
    native = {n.removeprefix("solve/result/") for n in other if n.startswith("solve/result/")}
    assert native == (set(outcome["output_sha256"]) - set(EXPECTED)) | {"exit.json"}
    assert set(other) == {"solve/result/" + n for n in native} | {"solve/launch.json", "members.json"}
    assert all(sha(other["solve/result/" + n]) == h for n, h in outcome["output_sha256"].items() if n not in EXPECTED)


def test_terminal_ownership_caps_and_complete_200_state_grid(manifest, other):
    assert manifest["preparation_archive"] == "preparation.tar.gz"
    assert manifest["preparation_sha256"] == publication.PREPARATION_SHA
    prepared = checked_members(HERE / "preparation.tar.gz", publication.PREPARATION_SHA)
    freeze = json.loads(prepared["solve/freeze.json"])
    launch = json.loads(other["solve/launch.json"])
    outcome = json.loads(other["solve/result/exit.json"])
    assert sha(prepared["solve/freeze.json"]) == launch["freeze_sha256"] == manifest["freeze_sha256"]
    assert freeze["case"] == "moving" and freeze["solver_timeout_seconds"] == 1800
    assert launch["outer_timeout_seconds"] == 1820
    command = launch["command"]
    assert command == launcher.command(Path(command[5]).parent.parent, case="moving", solver_timeout_seconds=1800)
    assert freeze["image"] == launcher.IMAGE
    assert outcome["status"] == "SOLVER COMPLETED; AUDIT PENDING"
    assert outcome["returncode"] == outcome["cleanup_returncode"] == 0
    assert outcome["exceptions"] == [] and outcome["container_stopped_successfully_before_cleanup"] is True
    cid = outcome["owned_container_id"]
    assert re.fullmatch(r"[0-9a-f]{64}", cid)
    assert other["solve/result/container.id"].decode().strip() == cid
    probe = json.loads(other["solve/result/container-probe.json"])
    inspected = json.loads(probe["stdout"])
    assert probe["returncode"] == 0 and len(inspected) == 1
    container = inspected[0]
    assert container["Id"] == cid and container["Name"] == "/" + command[3]
    assert container["Config"]["Image"] == launcher.IMAGE
    assert container["State"]["Running"] is False and container["State"]["OOMKilled"] is False
    assert container["State"]["ExitCode"] == 0
    cleanup = json.loads(other["solve/result/cleanup.json"])
    assert cleanup["returncode"] == 0 and cleanup["container_id"] == cleanup["stdout"].strip() == cid
    assert other["solve/result/control.inp"] == prepared["solve/frozen/control.inp"] == prepared["prepared/moving.inp"]
    times = quiet.history(other["solve/result/control.sta"].decode(), 2e-5)
    assert len(times) == 200 and all(quiet.close(t, (i+1)*1e-7) for i, t in enumerate(times))
    log = other["solve/result/solver.log"].decode()
    assert re.search(r"Total CalculiX Time:\s+1110\.379499", log)
