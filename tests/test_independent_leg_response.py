"""Small analytic mesh fixture; archived actual profile replay added separately."""
import hashlib
import json
import tarfile
from pathlib import Path

import numpy as np
import pytest

from fea.floor_contact import FACES, mesh
from fea.independent_leg_response import audit, deck, replay_archive, validate_prepared
from fea.independent_ply_control import deck as control_deck
from fea.independent_ply_control import resultant
from fea.section_force_tet_coupon import triangle_loads


def fixture():
    source, _ = control_deck(2, False)
    nodes, elements = mesh(source)
    owners = {name: [e for e, ids in elements.items() if (sum(nodes[n][0] for n in ids[:4]) < 0) == (name == "inner")]
              for name in ("inner", "outer")}
    part_nodes = {name: sorted({n for e in ids for n in elements[e]}) for name, ids in owners.items()}
    metadata = {"mesh_sha256": hashlib.sha256(source.encode()).hexdigest(), "part_elements": owners,
                "part_nodes": part_nodes, "shared_interface_nodes": sorted(set(part_nodes["inner"]) & set(part_nodes["outer"])),
                "floor": {}, "bore_nodes": {}}
    for name, ids in owners.items():
        fixed = [n for n in part_nodes[name] if nodes[n][2] == 0]
        metadata["bore_nodes"][name] = [fixed[i::4] for i in range(4)]
        weights = {}
        for e in ids:
            for indices in FACES:
                face = [elements[e][i] for i in indices]
                if all(nodes[n][2] == 400 for n in face):
                    for n, w in zip(face, triangle_loads([nodes[n] for n in face[:3]], [1., 1., 1.]), strict=True):
                        weights[n] = weights.get(n, 0.)+w
        metadata["floor"][name] = {"weights_mm2": weights}
    return source, metadata


@pytest.mark.parametrize("independent", [False, True])
def test_matched_mesh_split_and_unit_resultants(independent):
    source, metadata = fixture()
    text, context = deck(source, metadata, independent)
    a, b = [set(p["nodes"]) for p in context["plies"].values()]
    assert bool(a & b) is not independent
    assert not any(token in text for token in ("*TIE", "*EQUATION", "*COUPLING", "*CONTACT"))
    for case in context["cases"]:
        force = [0., 0., 0.]
        force[case["axis"]] = 1.
        assert case["applied_force_moment"][:3] == pytest.approx(force, abs=1e-10)
    if independent:
        for axis in range(3):
            before, after = context["cases"][axis], context["cases"][axis+3]
            delta = [b-a for a, b in zip(before["applied_force_moment"][3:], after["applied_force_moment"][3:], strict=True)]
            assert delta == pytest.approx(((0, 0, 0), (0, 0, -9.525), (0, 9.525, 0))[axis], abs=1e-9)
        assert all(n in a for case in context["cases"][3:6] for n in case["loads"])
        assert all(n in b for case in context["cases"][6:] for n in case["loads"])
        for axis in range(3):
            before, after = context["cases"][axis], context["cases"][axis+6]
            delta = [b-a for a, b in zip(before["applied_force_moment"][3:], after["applied_force_moment"][3:], strict=True)]
            assert delta == pytest.approx(((0, 0, 0), (0, 0, 9.525), (0, -9.525, 0))[axis], abs=1e-9)
    with pytest.raises(ValueError, match="digest"):
        deck(source+"\n", metadata, independent)
    with pytest.raises(ValueError, match="endpoints"):
        audit("", context)


def synthetic_output(context, *, bad_energy=False, move_fixed=False, move_unloaded=False):
    # Statics/printing fixture, deliberately not a solved displacement field.
    lines = []
    for time, case in enumerate(context["cases"], 1):
        u = {n: [0., 0., 0.] for n in context["nodes"]}
        rf, energies = {}, {}
        for name, ply in context["plies"].items():
            ids = set(ply["nodes"])
            loads = {n: f for n, f in case["loads"].items() if n in ids}
            columns = [resultant(context["nodes"], {n: tuple(float(i == axis) for i in range(3))})
                       for n in ply["fixed"] for axis in range(3)]
            solution = np.linalg.lstsq(np.array(columns).T, -np.array(resultant(context["nodes"], loads)), rcond=None)[0]
            rf.update({n: solution[3*i:3*i+3] for i, n in enumerate(ply["fixed"])})
            for n in loads:
                u[n][case["axis"]] = 2. if name == "inner" else 4.
            energies[name] = sum(sum(f*v for f, v in zip(force, u[n], strict=True)) for n, force in loads.items())/2
            if not loads and move_unloaded:
                u[next(n for n in ply["nodes"] if n not in ply["fixed"])][0] = .1
        if move_fixed:
            u[context["fixed"][0]][0] = .1
        for title, name, values in (("displacements", "ALLN", u), ("forces", "FIXED", rf)):
            lines.append(f"{title} for set {name} and time {time}\n")
            lines += [f"{n} "+" ".join(map(str, values[n])) for n in values]
            lines.append("")
        for name, value in energies.items():
            lines.append(f"total internal energy for set {name.upper()} and time {time}\n\n{value*(2 if bad_energy else 1)}\n")
    return "\n".join(lines)


def test_complete_audit_per_ply_energy_and_failure_gates():
    source, metadata = fixture()
    _, context = deck(source, metadata, True)
    results = audit(synthetic_output(context), context)
    assert all(r["pass"] for r in results)
    for r in results:
        assert sum(p["native_internal_energy_nmm"] for p in r["plies"].values()) == pytest.approx(r["energy_from_half_external_work_nmm"])
        for p in r["plies"].values():
            assert p["native_internal_energy_nmm"] == pytest.approx(p["energy_from_half_external_work_nmm"])
    assert not any(r["pass"] for r in audit(synthetic_output(context, bad_energy=True), context))
    assert not any(r["pass"] for r in audit(synthetic_output(context, move_unloaded=True), context)[3:])
    with pytest.raises(ValueError, match="fixed bore"):
        audit(synthetic_output(context, move_fixed=True), context)


def test_prepared_fixture_metadata_is_bound_to_verified_archive(tmp_path):
    archive = Path("fea/results/independent_leg_mesh/evidence.tar.gz")
    with tarfile.open(archive) as bundle:
        for name in ("input.json", "mesh40/mesh.inp", "mesh40/mesh.json", "mesh25/mesh.inp", "mesh25/mesh.json"):
            path = tmp_path/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bundle.extractfile(name).read())
    validate_prepared(tmp_path)
    target = tmp_path/"mesh40/mesh.json"
    target.write_bytes(target.read_bytes()+b"\n")
    with pytest.raises(ValueError, match="fixture/mesh"):
        validate_prepared(tmp_path)


def test_archived_actual_profile_response():
    root = Path("fea/results/independent_leg_response")
    report = json.loads((root/"report.json").read_text())
    assert hashlib.sha256((root/"evidence.tar.gz").read_bytes()).hexdigest() == report["archive_sha256"]
    assert hashlib.sha256((root/"publisher.py").read_bytes()).hexdigest() == report["publisher_source_sha256"]
    actual = replay_archive(root/"evidence.tar.gz")
    assert actual["pass"]
    assert all(report[key] == value for key, value in actual.items())
