import copy
import importlib.util
import math
from itertools import combinations
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "center_backing_test", Path(__file__).with_name("backing.py")
)
B = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)


def rectangle(x0=0.0, x1=10.0, z0=0.0, z1=10.0, holes=()):
    corners = [[x0, -36.0, z0], [x1, -36.0, z0], [x1, -36.0, z1], [x0, -36.0, z1]]
    edges = []
    for a, b in zip(corners, corners[1:] + corners[:1]):
        edges.append(
            {
                "curve_type": "LINE",
                "vertex_xyz_mm": [a, b],
                "length_mm": math.dist(a, b),
                "center_xyz_mm": [(x + y) / 2 for x, y in zip(a, b)],
                "bounds_xyz_mm": [
                    v for k in range(3) for v in (min(a[k], b[k]), max(a[k], b[k]))
                ],
            }
        )
    for x, z, radius in holes:
        edges.append(
            {
                "curve_type": "CIRCLE",
                "vertex_xyz_mm": [[x + radius, -36.0, z]],
                "length_mm": 2 * math.pi * radius,
                "center_xyz_mm": [x, -36.0, z],
                "bounds_xyz_mm": [
                    x - radius,
                    x + radius,
                    -36.0,
                    -36.0,
                    z - radius,
                    z + radius,
                ],
            }
        )
    return {
        "surface_type": "PLANE",
        "bounds_xyz_mm": [x0, x1, -36.0, -36.0, z0, z1],
        "area_mm2": (x1 - x0) * (z1 - z0) - sum(math.pi * r * r for _, _, r in holes),
        "center_xyz_mm": [(x0 + x1) / 2, -36.0, (z0 + z1) / 2],
        "oriented_normal_xyz": [0.0, 1.0, 0.0],
        "edge_signatures": edges,
        "wire_count": 1 + len(holes),
    }


def test_closed_hole_removes_line_and_narrow_strip_support():
    region = B.rectangle_holes(rectangle(holes=[(5.0, 5.0, 2.0)]))
    line = B.project_strip(region, 5.0, 1, 0.0)
    assert line["covered_z_intervals_mm"] == [[0.0, 3.0], [7.0, 10.0]]
    strip = B.project_strip(region, 4.0, 1, 2.0)
    root = math.sqrt(3.0)
    assert strip["covered_z_intervals_mm"] == [[0.0, 5.0 - root], [5.0 + root, 10.0]]
    assert B.project_strip(region, 2.0, 1, 6.0)["covered_z_intervals_mm"] == [
        [0.0, 10.0]
    ]


def test_strip_must_reach_past_rectangle_and_retains_tangent_event():
    region = B.rectangle_holes(rectangle(holes=[(5.0, 5.0, 2.0)]))
    assert B.project_strip(region, -2.0, 1, 2.0)["covered_z_intervals_mm"] == []
    assert B.project_strip(region, -2.0, 1, 2.5)["covered_z_intervals_mm"] == [
        [0.0, 10.0]
    ]
    assert B.project_strip(region, 3.0, 1, 0.0)["isolated_hole_tangencies_z_mm"] == [
        5.0
    ]
    with pytest.raises(B.ProjectionRefusal):
        B.project_strip(region, 0.0, 1, -1.0)


@pytest.mark.parametrize(
    "mutation", ["curve", "open_circle", "area", "outline", "overlap", "nonfinite"]
)
def test_unproved_trim_is_refused(mutation):
    shape = rectangle(holes=[(5.0, 5.0, 2.0)])
    if mutation == "curve":
        shape["edge_signatures"][-1]["curve_type"] = "ELLIPSE"
    elif mutation == "open_circle":
        shape["edge_signatures"][-1]["length_mm"] /= 2
    elif mutation == "area":
        shape["area_mm2"] += 1
    elif mutation == "outline":
        shape["edge_signatures"][0]["vertex_xyz_mm"][1][0] -= 1
    elif mutation == "overlap":
        shape = rectangle(holes=[(5.0, 5.0, 2.0), (6.0, 5.0, 2.0)])
    else:
        shape["bounds_xyz_mm"][0] = float("nan")
    with pytest.raises(B.ProjectionRefusal):
        B.rectangle_holes(shape)


def source_fixture():
    names = ["kicker_left", "kicker_right", "base_header"]
    for stem in (
        "base_post_center",
        "base_post_outer",
        "base_floor",
        "base_principal_center",
        "base_side",
        "center_principal_cleat",
        "main_lower",
    ):
        names.extend(stem + "_" + side for side in ("left", "right"))
    names.extend(f"unused_{i}" for i in range(50 - len(names)))
    bodies, graph_bodies, bindings, faces = {}, {}, [], {}

    def face(member, label, signature, normal):
        signature["oriented_normal_xyz"] = normal
        fid = member + "/" + label
        row = {
            "face_id": fid,
            "signature": signature,
            "signature_sha256": B.signature_sha(signature),
        }
        bodies[member]["planar_faces"].append(row)
        faces[fid] = row
        return fid

    for member in names:
        bodies[member] = {
            "member_id": member,
            "step_path": member + ".step",
            "step_sha256": member,
            "planar_faces": [],
        }
        graph_bodies[member] = {
            "member_id": member,
            "member_kind": "panel"
            if member.startswith(("kicker", "main_lower"))
            else "timber",
        }
        bindings.append(
            {"member_id": member, "path": member + ".step", "file_sha256": member}
        )
    for panel, lo, hi in (("kicker_left", -10.0, 0.0), ("kicker_right", 0.0, 10.0)):
        face(panel, "rear", rectangle(lo, hi, 0.0, 20.0), [0.0, -1.0, 0.0])
        face(panel, "side", rectangle(lo, hi, 0.0, 20.0), [1.0, 0.0, 0.0])
        graph_bodies[panel]["finished"] = {
            "bounds_xyz_mm": [lo, hi, -36.0, -34.0, 0.0, 20.0]
        }
    face("base_header", "front", rectangle(-10.0, 10.0, 15.0, 20.0), [0.0, 1.0, 0.0])
    for side, a, b in (("left", -4.0, -2.0), ("right", 2.0, 4.0)):
        face(
            "base_post_center_" + side,
            "front",
            rectangle(a, b, 0.0, 15.0),
            [0.0, 1.0, 0.0],
        )
        face(
            "base_post_outer_" + side,
            "front",
            rectangle(
                -10.0 if side == "left" else 8.0,
                -8.0 if side == "left" else 10.0,
                0.0,
                15.0,
            ),
            [0.0, 1.0, 0.0],
        )
        for stem in ("base_floor", "main_lower"):
            face(stem + "_" + side, "context", rectangle(), [-1.0, 0.0, 0.0])
    finite = {tuple(sorted(("kicker_left", "kicker_right")))}
    unresolved, exact_separated = set(), set()
    for side in ("left", "right"):
        panel = "kicker_" + side
        for other in (
            "base_header",
            *(
                stem + "_" + side
                for stem in (
                    "base_post_center",
                    "base_post_outer",
                    "base_floor",
                    "main_lower",
                )
            ),
        ):
            finite.add(tuple(sorted((panel, other))))
        unresolved.add(tuple(sorted((panel, "center_principal_cleat_" + side))))
        unresolved.add(
            tuple(
                sorted((panel, "main_lower_" + ("right" if side == "left" else "left")))
            )
        )
        for stem in ("base_principal_center", "base_side"):
            exact_separated.add(tuple(sorted((panel, stem + "_" + side))))
    edges, interfaces = [], []
    for pair in combinations(sorted(names), 2):
        if not any(p in pair for p in B.PANELS):
            continue
        state = (
            "finite_opposed_planar_touch"
            if pair in finite
            else "zero_area_touch_or_unresolved"
            if pair in unresolved
            else "separated"
        )
        edge = {
            "member_ids": list(pair),
            "geometry_state": state,
            "broadphase_candidate": pair in finite | unresolved | exact_separated,
        }
        if pair in finite:
            panel = next(p for p in pair if p in B.PANELS)
            other = next(m for m in pair if m != panel)
            direct = other in (
                "base_header",
                "base_post_center_left",
                "base_post_center_right",
                "base_post_outer_left",
                "base_post_outer_right",
            )
            ids = {
                panel: panel + ("/rear" if direct else "/side"),
                other: other
                + (
                    "/front"
                    if direct
                    else "/side"
                    if other.startswith("kicker")
                    else "/context"
                ),
            }
            region = copy.deepcopy(faces[ids[other]]["signature"])
            if other == "base_header":
                region = rectangle(
                    -10.0 if panel == "kicker_left" else 0.0,
                    0.0 if panel == "kicker_left" else 10.0,
                    15.0,
                    20.0,
                )
            area = region["area_mm2"]
            fp = {
                "face_a_id": ids[pair[0]],
                "face_b_id": ids[pair[1]],
                "normal_dot": -1.0,
                "face_a_signature_sha256": faces[ids[pair[0]]]["signature_sha256"],
                "face_b_signature_sha256": faces[ids[pair[1]]]["signature_sha256"],
                "face_a_oriented_normal_xyz": faces[ids[pair[0]]]["signature"][
                    "oriented_normal_xyz"
                ],
                "face_b_oriented_normal_xyz": faces[ids[pair[1]]]["signature"][
                    "oriented_normal_xyz"
                ],
                "overlap_regions": [region],
            }
            interfaces.append(
                {
                    "member_ids": list(pair),
                    "reconstructed_opposed_area_mm2": area,
                    "face_pairs": [fp],
                }
            )
            edge["opposed_planar_face_contact_area_mm2"] = area
        edges.append(edge)
    return (
        {
            "candidate": B.CANDIDATE,
            "revision_id": B.REVISION,
            "body_inventory": list(bodies.values()),
            "finite_opposed_interfaces": interfaces,
        },
        {
            "revision_id": B.REVISION,
            "inventories": {"physical_members": list(graph_bodies.values())},
            "edges": edges,
        },
        {
            "candidate": B.CANDIDATE,
            "geometry_revision_id": B.REVISION,
            "finished_member_step_bindings": bindings,
        },
    )


def test_complete_pair_census_and_known_support_intervals():
    report = B.build_backing(*source_fixture())
    assert report["counts"]["kicker_other_body_pairs"] == 97
    assert report["counts"]["broadphase_candidates"] == 19
    for panel in report["panels"]:
        assert panel["direct_rear_timber_edge_covered_z_intervals_mm"] == [[15.0, 20.0]]
        assert panel["direct_rear_timber_edge_gap_z_intervals_mm"] == [[0.0, 15.0]]
        assert panel["panel_thickness_strip_covered_z_intervals_mm"] == [[15.0, 20.0]]
        assert (
            panel["nearest_rear_timber_stand_off_by_z"][0][
                "minimum_geometric_inward_offset_mm"
            ]
            == 2.0
        )
        assert not panel["gap_establishes_mechanical_failure"]


def test_pair_census_preserves_exact_and_aabb_separation_identities():
    atlas, graph, manifest = source_fixture()
    report = B.build_backing(atlas, graph, manifest)
    expected = [
        {k: edge[k] for k in ("member_ids", "geometry_state", "broadphase_candidate")}
        for edge in sorted(graph["edges"], key=lambda e: e["member_ids"])
    ]
    assert report["pair_census"] == expected
    exact = [
        r
        for r in graph["edges"]
        if r["geometry_state"] == "separated" and r["broadphase_candidate"]
    ]
    aabb = [
        r
        for r in graph["edges"]
        if r["geometry_state"] == "separated" and not r["broadphase_candidate"]
    ]
    assert len(exact) == 4 and len(aabb) == 78
    exact[0]["broadphase_candidate"] = False
    aabb[0]["broadphase_candidate"] = True
    changed = B.build_backing(atlas, graph, manifest)
    assert changed["counts"] == report["counts"]
    assert changed["pair_census"] != report["pair_census"]
    by_pair = {tuple(r["member_ids"]): r for r in changed["pair_census"]}
    assert not by_pair[tuple(exact[0]["member_ids"])]["broadphase_candidate"]
    assert by_pair[tuple(aabb[0]["member_ids"])]["broadphase_candidate"]


@pytest.mark.parametrize(
    "mutation", ["face_hash", "missing_pair", "step_binding", "wrong_pair_face"]
)
def test_source_joins_fail_closed(mutation):
    atlas, graph, manifest = source_fixture()
    if mutation == "face_hash":
        atlas["body_inventory"][0]["planar_faces"][0]["signature"]["area_mm2"] += 1
    elif mutation == "missing_pair":
        graph["edges"].pop()
    elif mutation == "step_binding":
        manifest["finished_member_step_bindings"][0]["file_sha256"] = "different"
    else:
        atlas["finite_opposed_interfaces"][0]["face_pairs"][0]["face_a_id"] = (
            "kicker_left/side"
        )
    with pytest.raises((B.ProjectionRefusal, KeyError)):
        B.build_backing(atlas, graph, manifest)
