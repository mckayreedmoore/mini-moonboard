"""Independent scalar reaction recovery from archived output and physical contacts."""
import gzip
import hashlib
import json
import math
from pathlib import Path

import pytest

from fea import timber_base_demand as recovery
from fea.floor_contact import mesh
from fea.floor_contact_results import blocks


def wrench(nodes, forces, selected, reference):
    force = [math.fsum(forces[n][i] for n in selected) for i in range(3)]
    moments = [[], [], []]
    for n in selected:
        x, y, z = [nodes[n][i]-reference[i] for i in range(3)]
        fx, fy, fz = forces[n]
        for values, value in zip(moments, (y*fz-z*fy, z*fx-x*fz, x*fy-y*fx), strict=True):
            values.append(value)
    return force+[math.fsum(values) for values in moments]


def assert_actions(saved, expected, axes):
    assert saved["base_on_board_world_n_nmm"] == pytest.approx(expected, abs=1e-7)
    assert saved["board_on_base_world_n_nmm"] == pytest.approx([-v for v in expected], abs=1e-7)
    local = [sum(expected[offset+i]*axis[i] for i in range(3)) for offset in (0, 3) for axis in axes]
    assert saved["base_on_board_local_xsn_n_nmm"] == pytest.approx(local, abs=1e-7)


def assert_global_equilibrium(nodes, reactions, applied):
    total = wrench(nodes, reactions, set(reactions), (0., 0., 0.))
    load = wrench(nodes, applied, set(applied), (0., 0., 0.))
    residual = [a+b for a, b in zip(total, load, strict=True)]
    assert max(map(abs, residual[:3])) <= .1
    assert max(map(abs, residual[3:])) <= 1.


@pytest.fixture(scope="module")
def evidence():
    report = json.loads(recovery.OUTPUT.read_text())
    accepted, deck, dat, sources = recovery.authenticated_inputs()
    joint = json.loads(recovery.JOINTS.read_text())
    asymmetric = json.loads((recovery.ASYMMETRIC/"summary.json").read_text())
    expected = set(sources) | set(joint["source_sha256"]) | set(asymmetric["source_sha256"]) | {
        str(recovery.JOINTS), "fea/timber_base_demand.py", "fea/timber_asymmetric.py",
        str(recovery.ASYMMETRIC/"summary.json"),
        *(str(recovery.ASYMMETRIC/n) for n in asymmetric["replay_archives"])}
    assert set(report["source_sha256"]) == expected
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha for p, sha in report["source_sha256"].items())
    assert all(report["source_sha256"][p] == sha for p, sha in sources.items())
    assert report["candidate"] == accepted["candidate"] == asymmetric["candidate"] == "timber-base-development"
    assert report["limits"] == recovery.LIMITS
    assert report["local_axes_world"] == joint["local_axes_world"]
    return report, accepted, mesh(deck)[0], blocks(dat), joint, asymmetric


def test_six_original_case_resultants_and_exhaustive_reaction_partition(evidence):
    report, accepted, nodes, parsed, joint, _ = evidence
    base = set(report["floor_nodes"])
    legs = [set(joint["legs"][s]["floor_nodes"]) for s in ("left", "right")]
    assert not base & (legs[0] | legs[1]) and not legs[0] & legs[1]
    assert len(report["cases"]) == len(accepted["frozen_geometry"]["audited_cases"]) == 6
    for step, (saved, case) in enumerate(zip(report["cases"], accepted["frozen_geometry"]["audited_cases"], strict=True), 1):
        forces = parsed["forces", "FEET", float(step)]
        assert base | legs[0] | legs[1] == set(forces)
        assert saved["case"] == case["name"]
        expected = wrench(nodes, forces, base, report["reference_world_mm"])
        assert_actions(saved, expected, report["local_axes_world"])
        partition = [wrench(nodes, forces, ids, report["reference_world_mm"]) for ids in [base, *legs]]
        whole = wrench(nodes, forces, set(forces), report["reference_world_mm"])
        assert [math.fsum(w[i] for w in partition) for i in range(6)] == pytest.approx(whole, abs=1e-7)
        applied = {n: [f/len(accepted["load_nodes"]) for f in case["force_n"]]
                   for n in accepted["load_nodes"]}
        assert_global_equilibrium(nodes, forces, applied)


def test_all_asymmetric_cases_recover_from_nine_archived_reaction_bases(evidence):
    report, _, nodes, _, joint, accepted = evidence
    decoded = {}
    for name, hashes in accepted["replay_archives"].items():
        payload = (recovery.ASYMMETRIC/name).read_bytes()
        raw = gzip.decompress(payload)
        assert hashlib.sha256(payload).hexdigest() == hashes["gzip_sha256"]
        assert hashlib.sha256(raw).hexdigest() == hashes["uncompressed_sha256"]
        decoded[name.removesuffix(".gz")] = raw.decode()
    base = set(report["floor_nodes"])
    legs = [set(joint["legs"][s]["floor_nodes"]) for s in ("left", "right")]
    basis = {}
    for hold in recovery.asymmetric.HOLDS:
        assert mesh(decoded[hold+".inp"])[0] == nodes
        parsed = blocks(decoded[hold+".dat"])
        basis[hold] = []
        for step in (1, 2, 3):
            forces = parsed["forces", "FEET", float(step)]
            assert set(forces) == base | legs[0] | legs[1]
            basis[hold].append(wrench(nodes, forces, base, report["reference_world_mm"]))
            partial = [wrench(nodes, forces, ids, report["reference_world_mm"]) for ids in [base, *legs]]
            whole = wrench(nodes, forces, set(forces), report["reference_world_mm"])
            assert [math.fsum(w[i] for w in partial) for i in range(6)] == pytest.approx(whole, abs=1e-7)
            node = accepted["input"]["mapping"][hold]["node"]
            force = ((1000., 0., 0.), (0., 1000., 0.), (0., 0., -1000.))[step-1]
            assert_global_equilibrium(nodes, forces, {node: force})
    assert len(report["asymmetric_cases"]) == len(accepted["cases"]) == 216
    for saved, original in zip(report["asymmetric_cases"], accepted["cases"], strict=True):
        assert saved["hold"] == original["hold"]
        for key, value in original.items():
            if key != "legs":
                assert saved[key] == value
        expected = [math.fsum(c*w[i] for c, w in zip(saved["basis_coefficients"], basis[saved["hold"]], strict=True))
                    for i in range(6)]
        assert_actions(saved, expected, report["local_axes_world"])


def test_actual_cad_base_contact_inventory_and_zero_applied_base_load(evidence):
    import cadquery as cq

    from mini_moonboard import timber_frame as frame

    report, accepted, nodes, parsed, _, asymmetric = evidence
    raw = {p.name: p.shape for p in frame.wood_parts(False)}
    expected_members = {"base_header", "kicker_left", "kicker_right", "timber_base_gusset_left",
        "timber_base_gusset_right", "base_post_outer_left", "base_post_outer_right",
        "base_post_center_left", "base_post_center_right"}
    assert set(report["members"]) == expected_members
    assert report["reference_world_mm"] == pytest.approx(raw["base_header"].Center().toTuple())
    floor = parsed["forces", "FEET", 1.]
    contacts = {name: sorted(n for n in floor if raw[name].isInside(cq.Vector(*nodes[n]), 1e-5))
                for name in expected_members if name.startswith(("kicker_", "base_post_"))}
    assert contacts == report["floor_nodes_by_member"]
    assert set().union(*map(set, contacts.values())) == set(report["floor_nodes"])
    assert any(n not in set().union(*(set(ids) for name, ids in contacts.items() if name.startswith("base_post_")))
               for name, ids in contacts.items() if name.startswith("kicker_") for n in ids)
    loads = set(accepted["load_nodes"]) | {r["node"] for r in asymmetric["input"]["mapping"].values()}
    for n in loads:
        assert not any(raw[name].isInside(cq.Vector(*nodes[n]), 1e-5) for name in expected_members)
