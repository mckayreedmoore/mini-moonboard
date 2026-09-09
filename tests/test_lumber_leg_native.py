"""Native replay and deliberate rejection tests; no physical load rating."""
import hashlib
import json
import re
import tarfile
from pathlib import Path

import pytest

from fea import lumber_leg_response as response

ARCHIVES = sorted(Path("fea/results/lumber-leg-response").glob("*.tar.gz"))
assert Path("fea/results/lumber-leg-response/2x8-e0-m40-E7000.tar.gz") in ARCHIVES


def load_native(path):
    with tarfile.open(path) as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
    report = json.loads(files["report.json"])
    response.unchanged(report["source_sha256"])
    assert set(report["artifact_sha256"]) == set(files)-{"report.json"}
    assert all(hashlib.sha256(files[name]).hexdigest() == sha for name, sha in report["artifact_sha256"].items())
    value = json.loads(files["input.json"])
    value["nodes"] = {int(n): p for n, p in value["nodes"].items()}
    value["elements"] = {int(e): ids for e, ids in value["elements"].items()}
    assert report["qualified_for_design"] is False
    assert path.name == (f'{report["stock"]}-e{report["extension_mm"]:g}'
        f'-m{report["mesh_size_mm"]:g}-E{report["leg_modulus_mpa"]:g}.tar.gz')
    return files, report, value


@pytest.fixture(scope="module", params=ARCHIVES, ids=lambda p: p.stem)
def native(request):
    return load_native(request.param)


def test_all_native_bases_and_scenarios_replay(native):
    files, report, value = native
    previous = None
    for stiffness in response.base.STIFFNESSES:
        name = f"k{int(stiffness)}"
        text, context = response.deck(value["nodes"], value["elements"], value["points"], value["cases"],
                                      stiffness, value["legs"], report["leg_modulus_mpa"])
        assert text == files[name+".inp"].decode()
        log = files[name+".log"].decode()
        assert "Job finished" in log and "*ERROR" not in log.upper()
        rows = response.audit(files[name+".dat"].decode(), context, value["cases"], stiffness, value["legs"])
        assert rows == report["runs"][name]["basis"]
        assert len(rows) == 9 and all(r["passed"] for r in rows)
        # Same geometry/material, only spring stiffness changes: valid ordering.
        if previous is not None:
            assert all(r["load_work_nmm"] <= old["load_work_nmm"]+.01 for r, old in zip(rows, previous, strict=True))
        previous = rows
        combined = response.combine(rows, value["cases"], value["nodes"])
        assert combined == report["runs"][name]["scenarios"] and len(combined) == 216
        assert all(len(row["leg_connector_force_on_leg_n"]) == 8 for row in combined)
    assert report["passed"]


def first_run(native):
    files, report, value = native
    _, context = response.deck(value["nodes"], value["elements"], value["points"], value["cases"],
                              100., value["legs"], report["leg_modulus_mpa"])
    return files["k100.dat"].decode(), context, value


def test_native_energy_gate_rejects_changed_energy(native):
    data, context, value = first_run(native)
    pattern = r"(total internal energy for set TIMBER and time\s+\S+\s+)([\d.Ee+\-]+)"
    changed, count = re.subn(pattern, lambda m: m[1]+str(float(m[2])*2), data, count=1)
    assert count == 1
    rows = response.audit(changed, context, value["cases"], 100., value["legs"])
    assert not rows[0]["passed"]
    assert rows[0]["relative_energy_work_error"] > response.GATES["relative_energy_work"]


@pytest.mark.parametrize("failure", ("floor_balance", "interpolation"))
def test_leg_specific_gates_reject_inconsistent_native_fields(native, monkeypatch, failure):
    data, context, value = first_run(native)
    parsed = response.blocks(data)
    if failure == "floor_balance":
        node = value["legs"]["left"]["floor_nodes"][0]
        vector = list(parsed["forces", "FEET", 1.][node])
        vector[2] += 1.
        parsed["forces", "FEET", 1.][node] = vector
    else:
        point = next(p for n, p in context["connections"].items() if n.startswith("lumber_leg_bolt_"))
        node = max(zip(point["gusset_nodes"], point["other_weights"], strict=True),
                   key=lambda item: abs(item[1]))[0]
        vector = list(parsed["displacements", "AUDIT", 1.][node])
        vector[0] += .01
        parsed["displacements", "AUDIT", 1.][node] = vector
    # Isolate the new leg checks: the inherited global/gusset parser still
    # receives the original data, so it cannot mask a missing leg-specific gate.
    monkeypatch.setattr(response, "blocks", lambda _: parsed)
    rows = response.audit(data, context, value["cases"], 100., value["legs"])
    assert not rows[0]["passed"]
    if failure == "floor_balance":
        assert abs(rows[0]["leg_residual_n_nmm"]["left"][2]) > response.GATES["leg_force_n"]
    else:
        assert rows[0]["maximum_leg_constraint_error_mm"] > response.GATES["constraint_mm"]
        assert rows[0]["relative_energy_work_error"] <= response.GATES["relative_energy_work"]
        assert all(max(map(abs, r[:3])) <= response.GATES["leg_force_n"]
                   and max(map(abs, r[3:])) <= response.GATES["leg_moment_nmm"]
                   for r in rows[0]["leg_residual_n_nmm"].values())
        monkeypatch.setitem(response.GATES, "constraint_mm", 1e99)
        assert response.audit(data, context, value["cases"], 100., value["legs"])[0]["passed"]
