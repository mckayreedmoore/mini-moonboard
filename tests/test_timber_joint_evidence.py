"""Replay published aggregate actions and actual leg/interface ownership."""
import json
import math

import pytest

from fea import timber_joint_demand as demand
from fea.floor_contact import mesh
from fea.floor_contact_results import blocks


@pytest.fixture(scope="module")
def evidence():
    source, deck, dat, hashes = demand.authenticated_inputs()
    report = json.loads(demand.OUTPUT.read_text())
    nodes, elements = mesh(deck)
    return report, source, hashes, nodes, elements, blocks(dat)


def test_published_actions_replay_exact_source_bound_twelve_cases(evidence):
    report, source, hashes, nodes, _, parsed = evidence
    assert report["source_sha256"] == hashes
    assert report["candidate"] == source["candidate"] == "timber-base-development"
    assert report["limits"] == demand.LIMITS
    assert "not an isolated rim/bolt demand" in report["limits"]
    assert set(report["legs"]) == {"left", "right"}
    cases = source["frozen_geometry"]["audited_cases"]
    assert len(cases) == 6
    total = 0
    for leg in report["legs"].values():
        assert len(leg["cases"]) == 6
        feet = leg["floor_nodes"]
        assert feet and len(feet) == len(set(feet))
        assert all(n in nodes and abs(nodes[n][2]) < 1e-6 for n in feet)
        origin = leg["reference_world_mm"]
        for step, (case, saved) in enumerate(zip(cases, leg["cases"], strict=True), 1):
            reactions = parsed[("forces", "FEET", float(step))]
            assert set(feet) <= reactions.keys()
            assert saved["case"] == case["name"]
            force = [math.fsum(reactions[n][i] for n in feet) for i in range(3)]
            moments = []
            for n in feet:
                x, y, z = [nodes[n][i]-origin[i] for i in range(3)]
                fx, fy, fz = reactions[n]
                moments.append((y*fz-z*fy, z*fx-x*fz, x*fy-y*fx))
            world = force+[math.fsum(m[i] for m in moments) for i in range(3)]
            assert saved["leg_on_board_world_n_nmm"] == pytest.approx(world, abs=1e-7)
            assert saved["board_on_leg_world_n_nmm"] == pytest.approx([-v for v in world], abs=1e-7)
            local = [sum(world[offset+i]*axis[i] for i in range(3))
                     for offset in (0, 3) for axis in report["local_axes_world"]]
            assert saved["leg_on_board_local_xsn_n_nmm"] == pytest.approx(local, abs=1e-7)
            total += 1
    assert total == 12
    assert not set(report["legs"]["left"]["floor_nodes"]) & set(report["legs"]["right"]["floor_nodes"])


def test_saved_leg_floor_and_interface_inventory_matches_actual_cad(evidence):
    import cadquery as cq

    from mini_moonboard import box_frame as b
    from mini_moonboard import timber_frame as frame
    from mini_moonboard.box_exports import exact_bounds

    report, source, _, nodes, elements, parsed = evidence
    raw = {p.name: p.shape for p in frame.wood_parts(False)}
    axes = [(1., 0., 0.), (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized().toTuple(), b.normal().toTuple()]
    for saved, actual in zip(report["local_axes_world"], axes, strict=True):
        assert saved == pytest.approx(actual)
    feet = set(parsed[("forces", "FEET", 1.)])
    for side, sign in (("left", -1), ("right", 1)):
        saved = report["legs"][side]
        plies = [raw[f"leg_{side}_{layer}"] for layer in ("inner", "outer")]
        bounds = exact_bounds(cq.Compound.makeCompound(plies))
        limits = [getattr(bounds, axis+end) for end in ("min", "max") for axis in "xyz"]
        cache = {}

        def contains(p, plies=plies, cache=cache):
            key = tuple(p)
            if key not in cache:
                cache[key] = any(shape.isInside(cq.Vector(*p), demand.TOL) for shape in plies)
            return cache[key]

        selected = demand.select_leg(nodes, elements, limits, contains)
        board = {name: raw[name] for name in (f"base_side_{side}", f"main_upper_{side}")}
        ids, shared, supports = demand.ownership(nodes, elements, selected, feet, source["load_nodes"],
            lambda p, board=board, sign=sign: abs(p[0]-sign*b.HALF) < demand.TOL
            and any(shape.isInside(cq.Vector(*p), demand.TOL) for shape in board.values()), contains)
        assert saved["floor_nodes"] == sorted(supports)
        assert saved["element_count"] == len(selected)
        assert saved["node_count"] == len(ids)
        assert saved["shared_interface_node_count"] == len(shared)
        groups = {name: sorted(n for n in shared if shape.isInside(cq.Vector(*nodes[n]), demand.TOL))
                  for name, shape in board.items()}
        assert all(groups.values())
        assert saved["shared_nodes_by_board_member"] == groups
        volume, midpoint = demand.straight_mesh_volume({n: nodes[n] for n in ids}, selected)
        actual_volume = sum(p.Volume() for p in plies)
        assert saved["mesh_volume_mm3"] == pytest.approx(volume)
        assert saved["cad_volume_mm3"] == pytest.approx(actual_volume)
        assert abs(volume/actual_volume-1) <= .001
        assert saved["maximum_midpoint_error_mm"] == pytest.approx(midpoint)
        bolts = [c for c in frame.connections() if c.name.startswith(f"analysis_leg_wall_bolt_{side}_")]
        assert len(bolts) == 4
        assert saved["reference_world_mm"] == pytest.approx(
            [sign*b.HALF, *[sum(c.start.toTuple()[i] for c in bolts)/4 for i in (1, 2)]])
