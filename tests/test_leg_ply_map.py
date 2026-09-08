import json

import pytest

from fea.leg_ply_map import OUTPUT, build


def test_individual_plies_and_stitch_mapping_replay():
    result = build()
    assert result == json.loads(OUTPUT.read_text())
    for side, counts, shared in (("left", [1982, 1972], 1197), ("right", [1980, 1973], 1189)):
        leg = result["legs"][side]
        assert len(leg["shared_nodes"]) == shared
        assert len(leg["stitch_points"]) == 3
        assert [len(m["element_ids"]) for m in leg["members"].values()] == counts
        assert set(leg["members"][f"leg_{side}_inner"]["element_ids"]).isdisjoint(
            leg["members"][f"leg_{side}_outer"]["element_ids"])
        for member in leg["members"].values():
            assert member["floor_nodes"]
            assert member["mesh_volume_mm3"] == pytest.approx(member["cad_volume_mm3"], rel=.001)
        for point in leg["stitch_points"].values():
            assert sum(point["weights"]) == pytest.approx(1.)
            assert point["point_mm"][0] == pytest.approx(leg["plane_x_mm"])
