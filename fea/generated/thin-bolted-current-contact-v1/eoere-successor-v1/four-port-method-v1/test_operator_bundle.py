"""Tiny raw-operator replay and mutation fixtures; no candidate or solve."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix

PATH = Path(__file__).with_name("operator_bundle.py")
SPEC = importlib.util.spec_from_file_location("eoere_bundle_fixtures", PATH)
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)
TOY_SPEC = importlib.util.spec_from_file_location("eoere_bundle_genuine_toy", PATH.with_name("test_first_order_factory.py"))
toy = importlib.util.module_from_spec(TOY_SPEC)
TOY_SPEC.loader.exec_module(toy)


def genuine_toy():
    data, panels, integrated = toy.toy()
    return method.core.factory.prepare_synthetic(data, panels, integrated)


def capture(prepared, tmp_path):
    return method.snapshot(prepared, arrays_path=tmp_path/"operators.npz", manifest_path=tmp_path/"operators.json",
                           pins=method.source_pins(), command=["pure-snapshot-fixture"])


def test_genuine_source_order_and_all_sparse_bytes_roundtrip_with_full_rigid_work(tmp_path):
    p = genuine_toy()
    before = method.core.operator_fingerprint(p)
    pointer = capture(p, tmp_path)
    restored = method.read_snapshot(pointer)
    assert method.core.operator_fingerprint(restored) == before == method.core.operator_fingerprint(p)
    for old, new in [(p.assembly.K, restored.assembly.K), *[(a["B"], b["B"]) for name in
                     ("groups", "contacts", "tangents") for a, b in zip(getattr(p, name), getattr(restored, name), strict=True)]]:
        for key in ("data", "indices", "indptr"):
            assert getattr(old, key).dtype == getattr(new, key).dtype
            assert getattr(old, key).tobytes() == getattr(new, key).tobytes()
    assert restored.applied.tobytes() == p.applied.tobytes()
    assert np.array_equal(restored.rigid_modes, p.assembly.rigid_modes())
    wrench = sum((method.frame.wrench(row["force_xyz_n"], row["point_xyz_mm"], method.frame.REFERENCE)
                  for row in p.case["loads"]), np.zeros(6))
    assert np.max(abs(restored.rigid_modes.T @ restored.applied-wrench)) < 1e-8
    assert restored.coordinate_map["final_ndof"] == p.assembly.ndof
    assert set(restored.coordinate_map["timber"]) == {"wood-a", "wood-b"}
    assert len(restored.coordinate_map["four_port_fittings"]["toy-fitting"]["dof_indices"]) == 24
    assert restored.coordinate_map["unused_legacy_two_port_fitting_indices"] == {}
    assert restored.coordinate_map["fitting_embedding_ndof_by_owner"]["toy-fitting"] < p.assembly.ndof
    for name in ("groups", "contacts", "tangents"):
        assert [row["id"] for row in getattr(restored, name)] == [row["id"] for row in getattr(p, name)]


def test_two_coordinate_original_gradient_known_answer_after_immutable_read(tmp_path):
    # Algebraic u/w block only: not a physical body or equilibrium field.
    n = 2
    k = csr_matrix([[2., .5], [.5, 3.]])
    groups = [{"id": "spring", "kind": "toy-spring", "first": "toy", "second": "toy",
               "B": csr_matrix([[1., -1.], [.5, 0.], [0., 1.]]), "ka": 4., "kl": 5., "clearance": 0., "tension_only": False}]
    contacts = [{"id": "normal", "kind": "floor_normal", "first": "toy", "second": "floor",
                 "B": csr_matrix([[0., -1.]]), "stiffness": 7.}]
    tangents = [{"id": "xy-x", "kind": "floor_tangent", "first": "toy", "B": csr_matrix([[1., 0.]]), "stiffness": 11.},
                {"id": "xy-y", "kind": "floor_tangent", "first": "toy", "B": csr_matrix([[0., 0.]]), "stiffness": 11.}]
    p = SimpleNamespace(assembly=SimpleNamespace(K=k, ndof=n, geo={"bodies": []}, members={}, panels={},
        fittings={}, rigid_modes=lambda: np.zeros((n, 6))), applied=np.array([.2, -.4]),
        case={"loads": []}, fittings={}, system=SimpleNamespace(shafts={}), groups=groups, contacts=contacts, tangents=tangents)
    restored = method.read_snapshot(capture(p, tmp_path))
    q = np.array([.3, -.2])
    # Kq-f + Bspring.T*[2,.75,-1] + Bnormal.T*1.4 + [3.3,0].
    expected = np.array([5.975, -4.45])
    result = method.core.search._fresh_fields(restored.assembly.K, restored.applied, restored.groups,
        restored.contacts, restored.tangents, ["toy"], q)
    assert np.max(abs(result[0]-expected)) < 1e-14
    assert result[4].tolist() == pytest.approx([1.4])
    # Whole-foot-off branch changes only its original tangent contribution.
    off = method.core.search._fresh_fields(restored.assembly.K, restored.applied, restored.groups,
        restored.contacts, restored.tangents, [], q)
    assert np.max(abs(off[0]-(expected-np.array([3.3, 0.])))) < 1e-14


@pytest.mark.parametrize("mutation", ["raw-bytes", "dtype", "shape", "fingerprint", "row-order"])
def test_bundle_mutations_reject_without_reassembly(tmp_path, mutation, monkeypatch):
    p = genuine_toy()
    pointer = capture(p, tmp_path)
    monkeypatch.setattr(method.core.factory.frame, "ElasticAssembly", lambda *a, **k: pytest.fail("replay built assembly"))
    if mutation == "raw-bytes":
        path = Path(pointer["arrays"]["path"])
        path.write_bytes(path.read_bytes()+b"changed")
    else:
        path = Path(pointer["manifest"]["path"])
        manifest = json.loads(path.read_bytes())
        if mutation == "dtype":
            manifest["array_metadata"]["K/data"]["dtype"] = "<f4"
        elif mutation == "shape":
            manifest["K"]["shape"][1] -= 1
        elif mutation == "fingerprint":
            manifest["original_operator_fingerprint_sha256"] = "0"*64
        else:
            manifest["partitions"]["groups"].reverse()
        path.write_text(json.dumps(manifest))
        pointer = copy.deepcopy(pointer)
        pointer["manifest"]["sha256"] = method.frame.sha(path)
    with pytest.raises(ValueError):
        method.read_snapshot(pointer)


def test_snapshot_preserves_existing_artifacts_and_source_operator_mutation_rejects(tmp_path, monkeypatch):
    p = genuine_toy()
    pointer = capture(p, tmp_path)
    before = {name: Path(record["path"]).read_bytes() for name, record in pointer.items()}
    with pytest.raises(ValueError, match="preserve existing"):
        capture(p, tmp_path)
    assert all(Path(pointer[name]["path"]).read_bytes() == value for name, value in before.items())
    again = capture(p, tmp_path/"same-operators")
    assert again["arrays"]["sha256"] == pointer["arrays"]["sha256"]
    old = p.assembly.rigid_modes

    def changed():
        p.applied[0] += 1.
        return old()

    monkeypatch.setattr(p.assembly, "rigid_modes", changed)
    with pytest.raises(ValueError, match="source/operator changed"):
        capture(p, tmp_path/"changed")
