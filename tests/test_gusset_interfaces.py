import json

import pytest

from fea import gusset_interfaces as model


def test_current_face_ownership_replay():
    report = model.build()
    assert report == json.loads(model.OUTPUT.read_text())
    for side, count in (("left", 814), ("right", 808)):
        row = report["gussets"][side]
        assert len(row["element_ids"]) == count
        assert row["mesh_volume_mm3"] == pytest.approx(row["cad_volume_mm3"], rel=1e-8)
        assert row["shared_nodes_without_shared_face"] == []
        assert set(row["interfaces"]) == {"base_side_"+side, "base_post_outer_"+side, "base_header"}
        nodes, faces = set(), set()
        for member, entries in row["interfaces"].items():
            area = sum(f["corner_triangle_area_mm2"] for f in entries)
            assert area == pytest.approx(10887.075 if member == "base_header" else
                47691.675 if "post" in member else 35402.226759298836)
            for f in entries:
                assert f["element"] in row["element_ids"]
                assert f["neighbor_element"] not in row["element_ids"]
                assert (f["element"], f["face"]) not in faces
                faces.add((f["element"], f["face"]))
                assert len(set(f["nodes"])) == 6
                assert f["corner_triangle_area_mm2"] > 0
                nodes.update(f["nodes"])
        assert nodes == set(row["shared_nodes"])
