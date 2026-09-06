"""Portable raw-output replay; integration witness is not a fresh Gmsh solve."""
import hashlib
import json
import math
import tarfile
from pathlib import Path

import pytest

from fea.full_frame_mortar import GRAVITY_PER_MM3_N, blocks, cross, verify_deck

ROOT = Path("fea/results/full_frame_mortar")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def replay(files):
    record = json.loads(files["frame.json"])
    nodes, _, _, ground, supports = verify_deck(files["frame.inp"].decode(), record)
    parsed = blocks(files["frame.dat"].decode())
    rows = []
    for line in files["frame.sta"].decode().splitlines():
        fields = line.split()
        if len(fields) == 7 and all(v.isdigit() for v in fields[:4]):
            rows.append(dict(zip(("step", "increment", "attempt", "iterations", "time", "step_time", "increment_time"),
                                 [*map(int, fields[:4]), *map(float, fields[4:])], strict=True)))
    endpoints = []
    for row in rows:
        time = row["time"]
        u = parsed.get(("displacements", "WOODN", time), {})
        assert u.keys() == nodes.keys()
        positions = {n: tuple(a+b for a, b in zip(p, u[n], strict=True)) for n, p in nodes.items()}
        forces, patches = [], {}
        for name, xyz in ground.items():
            gu = parsed[("displacements", "GROUND_"+name, time)]
            rf = parsed[("forces", "GROUND_"+name, time)]
            assert gu.keys() == rf.keys() == xyz.keys()
            assert all(abs(v) <= 1e-9 for n in supports[name] for v in gu[n])
            forces.extend((tuple(a+b for a, b in zip(xyz[n], gu[n], strict=True)), rf[n]) for n in supports[name])
            patches[name] = {"bottom_reaction_n": [sum(rf[n][i] for n in supports[name]) for i in range(3)],
                             "maximum_ground_displacement_mm": max(math.hypot(*v) for v in gu.values()),
                             "master_displacement_mm": {str(n): list(gu[n]) for n in xyz if n not in supports[name]}}
        load = max(0., time-1.)*1200
        forces.extend((positions[int(n)], (0., 0., -v*GRAVITY_PER_MM3_N*min(time, 1.)))
                      for n, v in record["nodal_volume_mm3"].items())
        forces.extend((positions[n], (0., 0., -load/5)) for n in record["load_nodes"])
        force = [sum(f[i] for _, f in forces) for i in range(3)]
        moment = [sum(cross(p, f)[i] for p, f in forces) for i in range(3)]
        assert all(math.isfinite(v) for p, f in forces for v in (*p, *f))
        endpoints.append({"time": time, "climber_load_n": load, "gravity_fraction": min(time, 1.),
                          "force_residual_n": force, "moment_residual_nmm": moment,
                          "global_gate_pass": max(map(abs, force)) <= .1 and max(map(abs, moment)) <= 1.,
                          "maximum_wood_displacement_mm": max(math.hypot(*v) for v in u.values()),
                          "maximum_loaded_node_displacement_mm": max(math.hypot(*u[n]) for n in record["load_nodes"]),
                          "patches": patches})
    return rows, endpoints


@pytest.mark.parametrize("formulation", ["penalty", "mortar"])
def test_published_raw_evidence(formulation):
    report = json.loads((ROOT/"report.json").read_text())
    item = report["formulations"][formulation]
    archive = ROOT/item["archive"]
    assert archive.stat().st_size < 100_000_000
    assert digest(archive.read_bytes()) == item["archive_sha256"]
    with tarfile.open(archive) as tar:
        files = {m.name: tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
    assert {p: digest(v) for p, v in files.items()} == item["archive_contents_sha256"]
    record = json.loads(files["frame.json"])
    for name, sha in record["output_sha256"].items():
        assert digest(files[name]) == sha
    for name, sha in record["prelaunch_sha256"].items():
        key = "launch_sources/"+Path(name).name
        if key in files:
            assert digest(files[key]) == sha
    rows, endpoints = replay(files)
    assert rows == item["accepted_increments"]
    assert endpoints == item["diagnostic_endpoints"]
    validation = json.loads((ROOT/"weight_validation.json").read_text())
    assert digest((ROOT/"weight_validation.json").read_bytes()) == report["weight_validation_sha256"]
    witness = validation["formulations"][formulation]
    assert digest(files["frame.json"]) == witness["terminal_context_sha256"]
    assert digest(files["frame.dat"]) == witness["dat_sha256"]
    assert witness["deck_sha256"] == record["deck_sha256"]
    weights = {int(n): v for n, v in record["nodal_volume_mm3"].items()}
    assert digest(json.dumps(weights, sort_keys=True).encode()) == witness["integrated_weights_sha256"]
    assert witness["weight_count"] == len(weights) == 62020
    assert witness["negative_weight_count"] == sum(v < 0 for v in weights.values()) == 10140
    assert witness["maximum_absolute_difference_mm3"] == 0
    assert witness["weight_validation_pass"] is True
    for name, sha in validation["validator_source_sha256"].items():
        assert digest((ROOT/"postrun_audit_sources"/Path(name).name).read_bytes()) == sha
    if formulation == "mortar":
        assert record["exit_code"] == 0 and endpoints[-1]["time"] == 2
        assert endpoints[3]["global_gate_pass"] and not endpoints[-1]["global_gate_pass"]
        assert "Deformed equilibrium failed at 2.0" in witness["production_audit_error"]
    else:
        assert record["exit_code"] == -999 and endpoints[-1]["time"] < 1
        assert "Incomplete timber endpoint 1.0" == witness["production_audit_error"]
