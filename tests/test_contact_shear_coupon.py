import hashlib
import json
import tarfile
from copy import deepcopy
from pathlib import Path

import pytest

from fea.contact_shear_coupon import SOURCE, audit, deck


def fixture():
    context = {"nodes": {1: (0., 0., 100.), 2: (0., 0., 0.), 10: (0., 0., 0.), 11: (2., 0., 0.)},
               "wood": [1, 2], "top": [1], "foot": [2], "ground": [10, 11], "support": [10, 11]}
    rows = {}
    for t in (1., 2.):
        rows[("displacements", "WOOD", t)] = {1: (t-1, 0., 0.), 2: (0., 0., 0.)}
        rows[("forces", "TOP", t)] = {1: (0., 0., -120.)}
        rows[("forces", "FOOT", t)] = {2: (0., 0., 0.)}
        rows[("forces", "GROUND", t)] = {10: (0., 0., 120. if t == 1. else 60.), 11: (0., 0., 0. if t == 1. else 60.)}
        rows[("displacements", "GROUND", t)] = {10: (0., 0., 0.), 11: (0., 0., 0.)}
    return context, rows


def output(rows):
    return "\n".join(f"{kind} for set {name} and time {t}\n"+
                     "\n".join(f"{n} "+" ".join(map(str, xyz)) for n, xyz in values.items())+"\n"
                     for (kind, name, t), values in rows.items())


@pytest.mark.parametrize("increment", [.25, .125])
def test_same_cube_material_load_and_boundaries_across_formulations(increment):
    source = SOURCE.read_text()
    penalty, p = deck(source, "penalty", increment)
    mortar, m = deck(source, "mortar", increment)
    contact = "*CONTACT PRINT\nCDIS,CSTR\n*CONTACT PRINT,SLAVE=SLAVE,MASTER=MASTER\nCF,CFN,CFS\n"
    assert penalty.replace(contact, "").replace("TYPE=SURFACE TO SURFACE", "TYPE=MORTAR") == mortar
    assert p == m and len(p["wood"]) == 27
    assert "GRAV" not in penalty and "*DLOAD" not in penalty
    model, preload, shear = penalty.split("*STEP,NLGEOM,INC=100\n")
    assert "TOP,1,2,0" in model and "SUPPORT,1,3,0" in model
    assert "*BOUNDARY" not in preload
    assert "*BOUNDARY\nTOP,1,1,1.0\n" in shear
    assert "*CONTACT PRINT" not in mortar
    assert penalty.count(f"{increment!r},1,1e-6,{increment!r}") == 2


def test_bottom_support_changes_only_support_set():
    original, full = deck(SOURCE.read_text(), "mortar", .25)
    bottom, reduced = deck(SOURCE.read_text(), "mortar", .25, True)
    assert full["support"] == full["ground"]
    assert len(reduced["support"]) == 4
    assert all(reduced["nodes"][n][2] == -100. for n in reduced["support"])
    assert bottom.replace(",".join(map(str, reduced["support"]))+"\n*BOUNDARY", ",".join(map(str, full["support"]))+"\n*BOUNDARY") == original


@pytest.mark.parametrize("formulation,increment", [("other", .25), ("mortar", float("nan")), ("penalty", .001)])
def test_unsupported_comparisons_fail(formulation, increment):
    with pytest.raises(ValueError):
        deck("", formulation, increment)


def test_deformed_load_lever_arm_and_single_counted_top_cload():
    context, rows = fixture()
    result = audit(output(rows), context)
    assert all(s["force_pass"] and s["moment_pass"] for s in result)
    assert result[1]["moment_residual_nmm"] == [0., 0., 0.]
    rows[("forces", "GROUND", 2.)] = {10: (0., 0., 120.), 11: (0., 0., 0.)}
    rejected = audit(output(rows), context)[1]
    assert rejected["force_pass"] and not rejected["moment_pass"]
    assert rejected["moment_residual_nmm"][1] == 120.


@pytest.mark.parametrize("kind,name", [("displacements", "WOOD"), ("forces", "TOP"), ("forces", "GROUND"), ("forces", "FOOT")])
def test_each_endpoint_requires_complete_outputs(kind, name):
    context, rows = fixture()
    del rows[(kind, name, 2.)]
    with pytest.raises(ValueError, match="Incomplete"):
        audit(output(rows), context)


def test_nonfinite_context_and_output_fail_closed():
    context, rows = fixture()
    bad = deepcopy(context)
    bad["nodes"][1] = (float("nan"), 0., 100.)
    with pytest.raises(ValueError):
        audit(output(rows), bad)
    rows[("forces", "TOP", 2.)][1] = (float("inf"), 0., -120.)
    with pytest.raises(ValueError):
        audit(output(rows), context)


def test_actuator_position_must_reach_prescribed_endpoint():
    context, rows = fixture()
    rows[("displacements", "WOOD", 2.)][1] = (0., 0., 0.)
    with pytest.raises(ValueError, match="Actuator"):
        audit(output(rows), context)


def test_free_top_force_and_fixed_support_semantics_are_checked():
    context, rows = fixture()
    bad = deepcopy(rows)
    bad[("forces", "TOP", 2.)][1] = (0., 0., -240.)
    with pytest.raises(ValueError, match="Free top Z"):
        audit(output(bad), context)
    rows[("displacements", "GROUND", 2.)][10] = (1., 0., 0.)
    with pytest.raises(ValueError, match="Fixed ground"):
        audit(output(rows), context)


def test_free_ground_contact_rf_is_not_an_external_support():
    context, rows = fixture()
    context["nodes"][12] = (1., 0., 0.)
    context["ground"].append(12)
    for t in (1., 2.):
        rows[("forces", "GROUND", t)][12] = (1000., 1000., 1000.)
        rows[("displacements", "GROUND", t)][12] = (0.1, 0., 0.)
    result = audit(output(rows), context)
    assert all(s["force_pass"] and s["moment_pass"] for s in result)


def test_published_matrix_replays_exact_decks_outputs_and_rejections():
    directory = Path("fea/results/contact_shear_coupon")
    report = json.loads((directory/"report.json").read_text())
    path = directory/report["archive"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == report["archive_sha256"]
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        assert all(m.isfile() and len(Path(m.name).parts) == 2 and ".." not in Path(m.name).parts for m in members)
        assert len(members) == len({m.name for m in members})
        raw = {m.name: archive.extractfile(m).read() for m in members}
    assert {n: hashlib.sha256(b).hexdigest() for n, b in raw.items()} == report["archive_contents"]
    for variant, jobs in report["comparisons"].items():
        for name, summary in jobs.items():
            record = json.loads(raw[f"{variant}/{name}.json"])
            text, context = deck(SOURCE.read_text(), record["formulation"], record["increment"], record["bottom_supported"])
            assert text.encode() == raw[f"{variant}/{name}.inp"]
            assert hashlib.sha256(text.encode()).hexdigest() == record["deck_sha256"]
            assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == record["source_sha256"][str(SOURCE)]
            launch = raw[f"{variant}/contact_shear_coupon.launch.py"]
            assert hashlib.sha256(launch).hexdigest() == record["source_sha256"]["/work/fea/contact_shear_coupon.py"]
            for filename, digest in record["output_sha256"].items():
                assert hashlib.sha256(raw[f"{variant}/{filename}"]).hexdigest() == digest
            endpoints = audit(raw[f"{variant}/{name}.dat"].decode(), context)
            assert endpoints == record["endpoints"] == summary["endpoints"]
            assert summary["status"] == record["status"]
            assert record["exit_code"] == summary["exit_code"] == 0
            if record["formulation"] == "penalty":
                assert endpoints[0]["moment_pass"] and not endpoints[1]["moment_pass"]
            elif record["bottom_supported"]:
                assert all(s[k] for s in endpoints for k in ("force_pass", "moment_pass", "aggregate_friction_pass"))
                assert "LOCAL CONTACT NOT VALIDATED" in summary["status"]
            else:
                assert "SEMANTICS UNVERIFIED" in summary["status"]
