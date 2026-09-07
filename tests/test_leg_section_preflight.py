"""Read archived meshes/loads only; no solver, Gmsh, stress or contact replay."""
import copy
import json
import tarfile

import pytest

from fea import leg_section_preflight as preflight
from fea.floor_contact import mesh
from fea.floor_contact_results import cross


@pytest.fixture(scope="module")
def report():
    return preflight.preflight()


def test_actual_curved_cuts_and_independent_external_resultants(report):
    assert report["qualified"] is False and "not a planar section" in report["limits"]
    assert report["archive_sha256"] == preflight.ARCHIVE_SHA
    for size, count, faces, deviation in (("40", 1496, 22, .35272021249060753),
                                         ("25", 3665, 26, .19846186846062233)):
        row = report["meshes"][size]
        assert len(row["selected_elements"]) == count
        assert len(row["cut"]) == row["cut_face_count"] == faces
        assert row["boundary_face_count"] > faces
        assert row["maximum_cut_midside_deviation_mm"] == pytest.approx(deviation, abs=1e-10)
        assert len({tuple(c["lower"]) for c in row["cut"]}) == faces
        assert len({tuple(c["upper"]) for c in row["cut"]}) == faces
        assert all(c["lower"][0] in row["selected_elements"] and c["upper"][0] not in row["selected_elements"] for c in row["cut"])
        assert [(c["sharing"], c["axis"]) for c in row["loads"]] == [
            (sharing, axis) for sharing in ("symmetric", "inner_only", "outer_only") for axis in range(3)]
        # Independently known floor centroid and declared reference; no use of
        # the extractor's force integration to form the expected six-vector.
        lever = [0., 1403.9983879518763-900., -1400.]
        for case in row["loads"]:
            amplitude = {"symmetric": .5, "inner_only": 1., "outer_only": 0.}[case["sharing"]]
            force = [amplitude if a == case["axis"] else 0. for a in range(3)]
            expected = force+list(cross(lever, force))
            assert case["external_force_moment"] == pytest.approx(expected, abs=1e-8)
            assert case["expected_upper_on_lower_force_moment"] == pytest.approx([-v for v in expected], abs=1e-8)


@pytest.fixture(scope="module")
def coarse():
    with tarfile.open(preflight.ARCHIVE) as archive:
        nodes, elements = mesh(archive.extractfile("independent40.inp").read().decode())
        metadata = json.load(archive.extractfile("mesh40.json"))
    return nodes, elements, metadata["part_elements"]["inner"], [n for hole in metadata["bore_nodes"]["inner"] for n in hole], list(map(int, metadata["floor"]["inner"]["weights_mm2"]))


@pytest.mark.parametrize("fault", ["midnode", "fixture", "floor", "flat_cut", "fixture_island"])
def test_rejects_nonconforming_or_wrong_subbody(coarse, fault):
    nodes, elements, owned, fixed, floor = copy.deepcopy(coarse)
    selected = None
    if fault == "midnode":
        e = owned[0]
        ids = list(elements[e])
        ids[4], ids[5] = ids[5], ids[4]
        elements[e] = ids
    elif fault == "fixture":
        fixed.append(floor[0])
    elif fault == "floor":
        floor.append(fixed[0])
    elif fault == "flat_cut":
        selected = {e for e in owned if sum(nodes[n][2] for n in elements[e][:4])/4 < 1300}
    else:
        selected = {e for e in owned if sum(nodes[n][2] for n in elements[e][:4])/4 < 1400}
        selected.add(max(owned, key=lambda e: min(nodes[n][2] for n in elements[e])))
    with pytest.raises(ValueError):
        preflight.cut_topology(nodes, elements, owned, fixed, floor, selected)


def test_disconnected_topology_is_rejected():
    preflight.connected({1, 2, 3}, [(1, 2), (2, 3)])
    with pytest.raises(ValueError, match="Disconnected"):
        preflight.connected({1, 2, 3}, [(1, 2)])


def test_wrong_archive_rejected_before_geometry(tmp_path):
    archive = tmp_path/"wrong.tar.gz"
    archive.write_bytes(b"not actual-leg evidence")
    with pytest.raises(ValueError, match="archive differs"):
        preflight.preflight(archive)


def test_actual_load_parser_rejects_replacement_or_token_damage():
    text = "*STEP\n*CLOAD,OP=NEW\n1,1,.5\n1,3,-1.25\n*END STEP\n*STEP\n*CLOAD,OP=NEW\n2,2,1\n*END STEP\n"
    assert preflight.serialized_loads(text) == [{1: (.5, 0., -1.25)}, {2: (0., 1., 0.)}]
    for changed in (text.replace(",OP=NEW", "", 1), text.replace(".5", "-4.44089209850063e-16"),
                    text.replace(".5", "nan"), text.replace("1,1,.5", "1,1,.5\n1,1,.5"),
                    text.replace("1,1,.5", "1,4,.5"), text+"*STEP\n*END STEP\n"):
        with pytest.raises(ValueError):
            preflight.serialized_loads(changed)
