import copy
import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq

from scripts.wood_joint_current_contact_graph import (
    CURRENT_REVISION_ID,
    EXPECTED_CANDIDATE_BOLT_COUNT,
    EXPECTED_FRAME_BOLT_COUNT,
    EXPECTED_PANEL_SCREW_COUNT,
    collect_current_contact_graph,
)
from scripts.wood_joint_current_receiver_screen import EXPECTED_KICKER_CENTER_RECEIVERS

ROOT = Path(__file__).resolve().parents[1]


class _SourcePart:
    def __init__(self, name, shape):
        self.name = name
        self.shape = shape


class _Source:
    def __init__(self, members):
        self._members = members

    def uncut_wood_parts(self):
        return self._members

    def parts(self):
        return self._members


def _box(x, y=0.0, z=0.0, *, dx=1.0, dy=1.0, dz=1.0):
    return cq.Workplane("XY").box(dx, dy, dz).val().translate((x, y, z))


def _edge(result, first, second):
    pair = sorted((first, second))
    return next(row for row in result["edges"] if row["member_ids"] == pair)


def _fixture():
    inventory = json.loads(
        (ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text()
    )
    report = json.loads(
        (ROOT / "site/owner-wood-joints-review-report.json").read_text()
    )
    part_rows = inventory["parts"]
    source_ids = [row["part_id"] for row in part_rows]
    screw_receiver_ids = {
        row.get(
            "candidate_finished_receiver_member", row["source_finished_receiver_member"]
        )
        for row in inventory["fixed_panel_kicker_screws"]
    }
    all_frame_ids = {
        member for row in inventory["starting_frame_bolts"] for member in row["members"]
    }
    source_ids = sorted(set(source_ids) | all_frame_ids)

    shapes = {
        member_id: _box(index * 30.0) for index, member_id in enumerate(source_ids)
    }
    # Finite opposing contact.
    panel_shapes = {
        row["part_id"]: _box(1000.0 + index * 30.0)
        for index, row in enumerate(part_rows)
        if row["kind"] == "plywood_panel"
    }
    panel_shapes["main_lower_left"] = _box(0.0)
    panel_shapes["main_lower_right"] = _box(1.0)

    # Positive-volume overlap.
    shapes["base_post_outer_left"] = _box(200.0)
    shapes["base_post_outer_right"] = _box(200.5)

    # Overlapping AABBs, but separated exact cylinders.
    shapes["base_side_left"] = cq.Solid.makeCylinder(
        1.0, 2.0, cq.Vector(400.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)
    )
    shapes["base_side_right"] = cq.Solid.makeCylinder(
        1.0, 2.0, cq.Vector(401.9, 1.9, 0.0), cq.Vector(0.0, 0.0, 1.0)
    )

    host_ids = sorted(screw_receiver_ids)
    for index, member_id in enumerate(host_ids):
        if member_id not in shapes:
            shapes[member_id] = _box(2000.0 + index * 30.0)
    candidate_ids = (
        "candidate_block_left",
        "candidate_block_right",
        "candidate_block_center",
    )
    candidate_shapes = {
        member_id: _box(4000.0 + index * 30.0)
        for index, member_id in enumerate(candidate_ids)
    }
    all_node_ids = set(shapes) | set(host_ids) | set(candidate_ids) | set(panel_shapes)
    receiver_pool = sorted(set(host_ids) | set(candidate_ids))
    candidate_bores = {}
    for index in range(EXPECTED_CANDIDATE_BOLT_COUNT):
        if index == 0:
            receivers = (candidate_ids[0], candidate_ids[1], host_ids[0])
        else:
            first = receiver_pool[index % len(receiver_pool)]
            second = receiver_pool[(index + 1) % len(receiver_pool)]
            if first == second:
                second = receiver_pool[(index + 2) % len(receiver_pool)]
            receivers = (first, second)
        candidate_bores[f"candidate-axis-{index:03d}"] = SimpleNamespace(
            receiver_ids=receivers
        )

    source_members = [
        _SourcePart(member_id, shapes[member_id]) for member_id in source_ids
    ]
    current = SimpleNamespace(
        layout_id=CURRENT_REVISION_ID,
        trial_id=CURRENT_REVISION_ID,
        source=_Source(source_members),
        source_inventory=inventory,
        source_inventory_sha256=hashlib.sha256(
            (ROOT / "docs/wood-joints-mvp/source-inventory.json").read_bytes()
        ).hexdigest(),
        source_inputs_sha256={"test/current-geometry-producer.py": "a" * 64},
        raw_hosts={member_id: shapes[member_id] for member_id in host_ids},
        finished_hosts={member_id: shapes[member_id] for member_id in host_ids},
        raw_candidate_parts=candidate_shapes,
        finished_candidate_parts=candidate_shapes,
        candidate_bores=candidate_bores,
        candidate_installed_hardware={axis_id: {} for axis_id in candidate_bores},
        additional_finished_source_parts={},
        panel_replacements=panel_shapes,
        fixed_axes={
            row["axis_id"]: object() for row in inventory["fixed_panel_kicker_screws"]
        },
        frame_bolt_records=tuple(copy.deepcopy(inventory["starting_frame_bolts"])),
    )
    assert len(all_node_ids) >= 2
    return current, report


class CurrentContactGraphTests(unittest.TestCase):
    def test_collects_complete_member_pairs_and_distinguishes_geometry_states(self):
        geometry, report = _fixture()
        result = collect_current_contact_graph(geometry, report)

        nodes = result["inventories"]["physical_members"]
        node_ids = {row["member_id"] for row in nodes}
        self.assertEqual(len(result["edges"]), len(node_ids) * (len(node_ids) - 1) // 2)
        self.assertEqual(result["counts"]["unique_member_pairs"], len(result["edges"]))
        self.assertEqual(
            _edge(result, "main_lower_left", "main_lower_right")["geometry_state"],
            "finite_opposed_planar_touch",
        )
        self.assertEqual(
            _edge(result, "base_post_outer_left", "base_post_outer_right")[
                "geometry_state"
            ],
            "solid_overlap",
        )

        exact_gap = _edge(result, "base_side_left", "base_side_right")
        self.assertTrue(exact_gap["broadphase_candidate"])
        self.assertEqual(exact_gap["geometry_state"], "separated")
        self.assertGreater(exact_gap["minimum_separation_mm"], 0.0)

        broadphase_gap = next(
            edge for edge in result["edges"] if not edge["broadphase_candidate"]
        )
        self.assertEqual(
            broadphase_gap["interface_geometry_state"], "not_evaluated_aabb_separated"
        )
        self.assertIsNone(broadphase_gap["minimum_separation_mm"])

        panels = {
            row["member_id"]: row for row in nodes if row["member_kind"] == "panel"
        }
        self.assertIsNotNone(panels["main_lower_left"]["raw"])
        self.assertIsNotNone(panels["main_lower_left"]["finished"])
        self.assertFalse(result["assumptions_and_limits"][5].find("capacity") < 0)

    def test_joins_all_three_fastener_inventories_without_ordering_stacks(self):
        geometry, report = _fixture()
        result = collect_current_contact_graph(geometry, report)

        self.assertEqual(
            result["counts"]["candidate_bolt_axes"], EXPECTED_CANDIDATE_BOLT_COUNT
        )
        self.assertEqual(
            result["counts"]["retained_frame_bolt_axes"], EXPECTED_FRAME_BOLT_COUNT
        )
        self.assertEqual(
            result["counts"]["current_panel_screw_axes"], EXPECTED_PANEL_SCREW_COUNT
        )

        first_bolt = result["inventories"]["candidate_bolt_axes"][0]
        self.assertEqual(len(first_bolt["receiver_member_ids_as_recorded"]), 3)
        self.assertEqual(len(first_bolt["member_pair_associations"]), 3)
        self.assertTrue(
            all(
                row["physical_head_to_nut_order_established"] is False
                for row in first_bolt["member_pair_associations"]
            )
        )

        axis_ids = {
            row["axis_id"] for row in result["inventories"]["candidate_bolt_axes"]
        }
        self.assertEqual(
            sum(
                association["axis_id"] in axis_ids
                for edge in result["edges"]
                for association in edge["candidate_bolt_associations"]
            ),
            sum(
                len(row["member_pair_associations"])
                for row in result["inventories"]["candidate_bolt_axes"]
            ),
        )
        frame_rows = result["inventories"]["retained_frame_bolts"]
        self.assertTrue(
            all(
                row["physical_head_to_nut_order_established"] is False
                for frame in frame_rows
                for row in frame["member_pair_associations"]
            )
        )
        screw_ids = {
            row["axis_id"] for row in result["inventories"]["current_panel_screw_axes"]
        }
        self.assertEqual(len(screw_ids), EXPECTED_PANEL_SCREW_COUNT)
        screws_by_id = {
            row["axis_id"]: row
            for row in result["inventories"]["current_panel_screw_axes"]
        }
        self.assertEqual(
            {
                axis_id: screws_by_id[axis_id]["receiver_member"]
                for axis_id in EXPECTED_KICKER_CENTER_RECEIVERS
            },
            EXPECTED_KICKER_CENTER_RECEIVERS,
        )

    def test_unchanged_source_plywood_panel_keeps_panel_kind(self):
        geometry, report = _fixture()
        geometry.panel_replacements = dict(geometry.panel_replacements)
        geometry.panel_replacements.pop("main_upper_left")

        result = collect_current_contact_graph(geometry, report)
        panel = next(
            row
            for row in result["inventories"]["physical_members"]
            if row["member_id"] == "main_upper_left"
        )

        self.assertEqual(panel["member_kind"], "panel")
        self.assertIn("source_inventory_member", panel["composition_roles"])
        self.assertNotIn("current_panel_replacement", panel["composition_roles"])
        self.assertIsNotNone(panel["raw"])
        self.assertIsNotNone(panel["finished"])

    def test_rejects_a_report_for_another_geometry_revision(self):
        geometry, report = _fixture()
        stale_report = dict(report, revision_id="historical-revision")
        with self.assertRaisesRegex(ValueError, "does not match"):
            collect_current_contact_graph(geometry, stale_report)


if __name__ == "__main__":
    unittest.main()
