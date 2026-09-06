"""Replay preparation evidence without CAD, Gmsh, Docker or a solver."""
import gzip
import json
import math

import pytest

from fea import dynamic_momentum
from fea import publish_moving_fixture as publication


@pytest.fixture(scope="module")
def cached():
    manifest = json.loads((publication.HERE / "manifest.json").read_text())
    item = manifest["mass"]
    files = publication.checked_members(publication.HERE / item["archive"], item["sha256"])
    return json.loads(files["context.json"]), json.loads(gzip.decompress(files["blocks.json.gz"]))


def test_archived_preflight_and_native_mass_replay():
    report = publication.verify()
    assert report == json.loads((publication.HERE / "comparison.json").read_text())
    assert report["native_mass_states"] == 20
    assert max(report["native_mass_max_relative_error"].values()) < 6e-8
    assert report["radial_gap_lower_mm"] > .00077


def test_selected_actual_native_blocks_from_analytic_shape_functions(cached):
    context, cache = cached
    gradients = ((-1, -1, -1), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    edges = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
    a, b = .138196601125011, .585410196624968
    points = ((a, a, a), (b, a, a), (a, b, a), (a, a, b))
    density = context["material"]["density_tonne_mm3"]
    for blocks in cache["operators"]["native_four_point"].values():
        keys = sorted(blocks, key=int)
        for key in (keys[0], keys[len(keys)//2], keys[-1]):
            ids, actual = blocks[key]
            canonical = context["elements"][key]
            coordinates = [context["nodes"][str(n)] for n in canonical]
            basis, determinants = [], []
            for x, y, z in points:
                bary = (1-x-y-z, x, y, z)
                shape = [v*(2*v-1) for v in bary] + [4*bary[i]*bary[j] for i, j in edges]
                derivative = [[(4*bary[i]-1)*v for v in gradients[i]] for i in range(4)]
                derivative += [[4*(gradients[i][k]*bary[j] + bary[i]*gradients[j][k]) for k in range(3)] for i, j in edges]
                jac = [[math.fsum(coordinates[n][i]*derivative[n][j] for n in range(10)) for j in range(3)] for i in range(3)]
                u, v, w = jac
                determinants.append(u[0]*(v[1]*w[2]-v[2]*w[1])-u[1]*(v[0]*w[2]-v[2]*w[0])+u[2]*(v[0]*w[1]-v[1]*w[0]))
                basis.append([shape[canonical.index(n)] for n in ids])
            assert min(determinants) > 0
            expected = [[math.fsum(density*.041666666666667*d*row[i]*row[j]
                                  for d, row in zip(determinants, basis, strict=True)) for j in range(10)] for i in range(10)]
            for row, wanted in zip(actual, expected, strict=True):
                assert row == pytest.approx(wanted, rel=1e-9, abs=1e-19)


def test_all_cached_blocks_preserve_rigid_translation(cached):
    context, cache = cached
    xyz = {int(n): tuple(p) for n, p in context["nodes"].items()}
    zero = {n: (0., 0., 0.) for n in xyz}
    velocity = (2., -3., 4.)
    velocities = {n: velocity for n in xyz}
    for bodies in cache["operators"].values():
        for blocks in bodies.values():
            result = dynamic_momentum.momentum(xyz, blocks, zero, velocities)
            total = math.fsum(v for _, matrix in blocks.values() for row in matrix for v in row)
            weighted = [math.fsum(math.fsum(matrix[i])*xyz[n][k] for ids, matrix in blocks.values()
                                  for i, n in enumerate(ids)) for k in range(3)]
            angular = tuple(weighted[(k+1)%3]*velocity[(k+2)%3] - weighted[(k+2)%3]*velocity[(k+1)%3] for k in range(3))
            assert result["linear_momentum"] == pytest.approx(tuple(total*v for v in velocity), rel=1e-12, abs=1e-18)
            assert result["kinetic_energy"] == pytest.approx(total*29/2, rel=1e-12)
            assert result["angular_momentum"] == pytest.approx(angular, rel=1e-12, abs=1e-18)


def test_archive_bytes_cannot_be_changed(tmp_path):
    path = tmp_path / "changed.tar.gz"
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Archive hash"):
        publication.checked_members(path, "0"*64)
