import json
import math

import pytest

from fea.dynamic_momentum import calculix_221_quadrature, mass_block
from fea.publish_native_dynamic_control import DIRECTORY, members, verify


def test_complete_archives_and_actual_velocity_replay_without_solver():
    errors = verify()
    assert errors["ELKE_relative_error"] == pytest.approx(3.5127798777658994e-7, rel=1e-10)
    assert errors["EMAS_relative_error"] < 2.1e-7
    manifest = json.loads((DIRECTORY / "manifest.json").read_text())
    assert len(manifest["runs"]["control-ajgbgzoh"]["executed_cases"]) == 4
    assert manifest["runs"]["control-axqh8cyi"]["executed_cases"] == ["straight-linear"]
    for record in manifest["runs"].values():
        files = members(DIRECTORY / record["archive"])
        assert len([n for n in files if n.startswith("frozen/native-source/")]) > 1000
        for case in record["executed_cases"]:
            for name in ("control.dat", "control.sta", "control.frd", "console.log", "container-inspect.json", "cleanup.log", "command.json", "exit.json"):
                assert f"{case}/{name}" in files


def test_cached_four_point_blocks_from_reference_shape_functions():
    cache = json.loads((DIRECTORY / "mass-blocks.json").read_text())
    gradients = ((-1, -1, -1), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    edges = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
    points, weights = calculix_221_quadrature()
    for geometry in cache["geometries"].values():
        xyz = {int(n): p for n, p in geometry["nodes"].items()}
        ids, cached = geometry["four_point"]["1"]
        basis, determinants = [], []
        for x, y, z in points:
            bary = (1-x-y-z, x, y, z)
            shape = [v*(2*v-1) for v in bary] + [4*bary[i]*bary[j] for i, j in edges]
            derivative = [[(4*bary[i]-1)*g for g in gradients[i]] for i in range(4)]
            derivative += [[4*(gradients[i][a]*bary[j] + bary[i]*gradients[j][a]) for a in range(3)] for i, j in edges]
            jac = [[math.fsum(xyz[n+1][a]*derivative[n][b] for n in range(10)) for b in range(3)] for a in range(3)]
            a, b, c = jac
            determinants.append(a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))
            basis.append([shape[n-1] for n in ids])
        rebuilt = mass_block(basis, weights, determinants, 1)
        for actual, expected in zip(rebuilt, cached, strict=True):
            assert actual == pytest.approx(expected, rel=1e-12, abs=1e-15)
