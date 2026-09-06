import hashlib
import json
import tarfile
from pathlib import Path

import pytest

from fea import leg_shear_coupon
from fea.contact_shear_coupon import audit
from fea.floor_contact import FACES, mesh
from fea.leg_shear_coupon import deck


def source():
    # Reuse archived actual geometry without requiring ignored full-frame inputs.
    with tarfile.open("fea/results/foot_contact_diagnosis/actual_leg/solver_evidence.tar.gz") as archive:
        return archive.extractfile("actual_leg/actual_leg.inp").read().decode().replace("ELSET=TIMBER", "ELSET=Volume8")


@pytest.fixture(autouse=True)
def extracted_archive(monkeypatch):
    # Frozen full-frame extract() already has its own tests. Adapt its return
    # contract here from the archived single-volume coupon (no RIGHT/KICKER).
    def extract(text):
        all_nodes, elements = mesh(text)
        used = {n for ids in elements.values() for n in ids}
        nodes = {n: p for n, p in all_nodes.items() if n in used}
        faces = [(e, f) for e, ids in elements.items() for f, idx in enumerate(FACES, 1)
                 if all(abs(nodes[ids[i]][2]) < 1e-5 for i in idx)]
        return nodes, elements, {"LEFT": faces}, "VOLUME8"
    monkeypatch.setattr(leg_shear_coupon, "extract", extract)


@pytest.mark.parametrize("increment", [.25, .125])
def test_actual_leg_pair_preserves_geometry_and_matches_loading(increment):
    original = source()
    penalty, p = deck(original, "penalty", increment)
    mortar, m = deck(original, "mortar", increment)
    assert p == m
    _, original_elements = mesh(original)
    _, actual_elements = mesh(penalty)
    assert actual_elements == original_elements and len(actual_elements) == 968
    assert len(p["top"]) == 46 and len(p["support"]) == 4
    assert all(p["nodes"][n][2] == -100. for n in p["support"])
    assert not (set(p["top"]) & set(p["foot"]))
    contact = "*CONTACT PRINT\nCDIS,CSTR\n*CONTACT PRINT,SLAVE=SLAVE_LEFT,MASTER=MASTER_LEFT\nCF,CFN,CFS\n"
    assert penalty.replace(contact, "").replace("TYPE=SURFACE TO SURFACE", "TYPE=MORTAR") == mortar
    assert "*DLOAD" not in penalty and "GRAV" not in penalty
    assert "TOP,1,2,0" in penalty and "TOP,1,1,1.0" in penalty
    assert "SUPPORT,1,3,0" in penalty and "GROUND_LEFT,1,3,0" not in penalty
    for step in penalty.split("*STEP,")[1:]:
        load = step.split("*CLOAD,OP=NEW\n")[1].split("*", 1)[0]
        rows = [line.split(",") for line in load.splitlines()]
        assert {int(row[0]) for row in rows} == set(p["top"])
        assert sum(float(row[2]) for row in rows) == pytest.approx(-1200.)


def test_undefined_formulation_is_rejected():
    with pytest.raises(ValueError, match="comparisons"):
        deck(source(), "other", .25)


def test_actual_leg_archive_replays_raw_global_results(monkeypatch):
    directory = Path("fea/results/leg_shear_coupon")
    report = json.loads((directory/"report.json").read_text())
    path = directory/report["archive"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == report["archive_sha256"]
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        assert all(m.isfile() and Path(m.name).name == m.name for m in members)
        assert len(members) == len({m.name for m in members})
        raw = {m.name: archive.extractfile(m).read() for m in members}
    assert {n: hashlib.sha256(b).hexdigest() for n, b in raw.items()} == report["archive_contents"]
    original_nodes, original_elements = mesh(source())
    for name, summary in report["jobs"].items():
        record = json.loads(raw[name+".json"])
        text = raw[name+".inp"].decode()
        assert hashlib.sha256(text.encode()).hexdigest() == record["deck_sha256"]
        for filename, expected in record["output_sha256"].items():
            assert hashlib.sha256(raw[filename]).hexdigest() == expected
        for stem, key in (("leg_shear_coupon", "/work/fea/leg_shear_coupon.py"), ("contact_shear_coupon", "fea/contact_shear_coupon.py")):
            assert hashlib.sha256(raw[stem+".launch.py"]).hexdigest() == record["source_sha256"][key]
        nodes = {int(n): xyz for n, xyz in record["nodes"].items() if int(n) in record["wood"]}
        _, elements = mesh(text)
        assert elements == original_elements
        assert nodes.keys() == {n for ids in original_elements.values() for n in ids}
        for node, xyz in nodes.items():
            # The old coupon deck rounded coordinates; connectivity alone
            # would not detect a changed leg shape under the same node IDs.
            assert xyz == pytest.approx(original_nodes[node], abs=1e-7, rel=0)
        faces = [(e, f) for e, ids in elements.items() for f, idx in enumerate(FACES, 1)
                 if all(abs(nodes[ids[i]][2]) < 1e-5 for i in idx)]
        extracted = (nodes, elements, {"LEFT": faces}, record["original_volume"])
        monkeypatch.setattr(leg_shear_coupon, "extract", lambda _, value=extracted: value)
        regenerated, context = deck("", record["formulation"], record["increment"])
        assert regenerated == text
        actual = audit(raw[name+".dat"].decode(), context, preload_n=1200.)
        assert actual == record["endpoints"] == summary["endpoints"]
        assert summary["status"] == record["status"] and record["exit_code"] == summary["exit_code"] == 0
        if name == "penalty_0p25":
            assert not actual[0]["moment_pass"]
        else:
            assert all(s[k] for s in actual for k in ("force_pass", "moment_pass", "aggregate_friction_pass"))
