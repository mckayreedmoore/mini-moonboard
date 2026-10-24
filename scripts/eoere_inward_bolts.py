"""Reverse exterior bolt stacks, retaining their holes and purchased hardware.

The viewer uses the same rigid transforms as the checked CAD bodies. Its small
patch reuses the preceding meshes instead of publishing duplicate mesh bytes.
"""

from __future__ import annotations

import argparse
import copy
import inspect
import json
from pathlib import Path

import cadquery as cq
import numpy as np

from scripts import eoere_leg_header_clearance as clearance
from scripts.eoere_leg_header_revision import verify_attachment_axes
from scripts.eoere_paired_frame_basis import RAW, ROOT, read, ref, sha

REVISION = "eoere-inward-exterior-bolts-v7"
PARENT_REVISION = "eoere-flat-cleats-principal-upper-pairs-v6"
BASE = RAW / "frame-completion-v1/owner-inward-bolts-v7"
PACKET = Path("docs/bolted-frame-development/owner-frame-v7")
INDEX = Path("docs/bolted-frame-development/development-revisions.json")
SCENE = Path("site/eoere-inward-bolts-scene.json")
OWN = Path(__file__).resolve()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def build(out):
    assert not out.exists(), "fresh output required"
    pins = {ref(OWN)["path"]: sha(OWN)}
    index = read(INDEX, pins)
    assert index["geometry"]["revision"] == PARENT_REVISION
    receipt = read(index["geometry"]["receipt"]["path"], pins, index["geometry"]["receipt"]["sha256"])
    g = read(receipt["checked_geometry"]["path"], pins, receipt["checked_geometry"]["sha256"])
    assert read(receipt["checked_clearance"]["path"], pins,
                receipt["checked_clearance"]["sha256"])["nominal_geometry_clear"]
    parent = copy.deepcopy(g)
    registry = {r["id"]: r for r in g["changed_finished_solids"]}
    out.mkdir(parents=True)
    (out / "parent-index.json").write_bytes((ROOT / INDEX).read_bytes())
    # The live index will advance at publication; bind its frozen copy instead.
    del pins[str(INDEX)]
    pins[ref(out / "parent-index.json")["path"]] = sha(out / "parent-index.json")
    (out / "producer-snapshot.py").write_bytes(OWN.read_bytes())
    changed, moves, axis_updates, summaries = set(), [], [], []

    def load(row):
        assert sha(row["path"]) == row["sha256"], row["path"]
        pins[row["path"]] = row["sha256"]
        return cq.Shape.importBrep(str(ROOT / row["path"]))

    for axis in g["axes"]:
        point, direction = np.asarray(axis["point_xyz_mm"]), np.asarray(axis["direction_xyz"])
        side = abs(point[0]) > 1000 and point[0] * direction[0] > .99
        top = axis["receivers"] == ["base_rail_top"] and direction[2] > .7
        if not (side or top):
            continue
        identity = axis["id"]
        turn_axis = np.array([0., 0., 1.]) if side else np.array([1., 0., 0.])
        rotation = 2 * np.outer(turn_axis, turn_axis) - np.eye(3)
        center = point + direction * (axis["grip_mm"] + axis["after_plate_mm"] - axis["before_plate_mm"]) / 2
        translation = center - rotation @ center
        roles = sorted(n[len(identity) + 1:] for n in registry if n.startswith(identity + "_"))
        assert set(roles) == {"shaft", "head", "head_washer", "nut_washer", "nut"} | (
            {"spacer", "spacer_2", "spacer_3"} if axis.get("nut_side_spacer_mm", 0) else set())
        before_centers, after_centers = {}, {}
        for role in roles:
            name = identity + "_" + role
            before = registry[name]
            body = load(before).rotate(tuple(center), tuple(center + turn_axis), 180)
            assert body.isValid() and len(body.Solids()) == 1
            assert abs(body.Volume() - before["volume_mm3"]) < 1e-5
            path = out / (name + ".brep")
            assert body.exportBrep(str(path))
            box = body.BoundingBox()
            row = {"id": name, "kind": "bolt", **ref(path), "bytes": path.stat().st_size,
                   "volume_mm3": body.Volume(), "center_of_mass_xyz_mm": list(body.Center().toTuple()),
                   "bounds_xyz_mm": [getattr(box, a + end) for a in "xyz" for end in ("min", "max")]}
            expected = rotation @ np.asarray(before["center_of_mass_xyz_mm"]) + translation
            assert np.max(np.abs(expected - row["center_of_mass_xyz_mm"])) < 1e-6
            registry[name] = row
            changed.add(name)
            before_centers[role] = before["center_of_mass_xyz_mm"]
            after_centers[role] = row["center_of_mass_xyz_mm"]
        nut_to_head = np.asarray(after_centers["nut"]) - after_centers["head"]
        assert np.dot(nut_to_head, direction) < 0
        if side:
            assert abs(after_centers["nut"][0]) < abs(after_centers["head"][0])
        old_axis = copy.deepcopy(axis)
        axis.update(point_xyz_mm=(point + direction * axis["grip_mm"]).tolist(),
                    direction_xyz=(-direction).tolist(), before_plate_mm=old_axis["after_plate_mm"],
                    after_plate_mm=old_axis["before_plate_mm"], nut_faces="interior", head_faces="exterior",
                    installation_orientation_revision=REVISION,
                    nominal_thread_window_qualified=False, delivered_part_or_thread_window_verified=False)
        axis_updates.append({"before": old_axis, "after": copy.deepcopy(axis)})
        moves.append({"axis_id": identity, "exterior_face": "left" if side and point[0] < 0 else "right" if side else "top",
                      "roles": roles, "rotation_axis_xyz": turn_axis.tolist(), "rotation_center_xyz_mm": center.tolist(),
                      "rotation_matrix_row_major": rotation.tolist(), "translation_xyz_mm": translation.tolist(),
                      "before_centers_xyz_mm": before_centers, "after_centers_xyz_mm": after_centers})
        summaries.append({"axis_id": identity, "head_faces": "exterior", "nut_faces": "interior",
                          "selected_underhead_length_mm": axis["nominal_under_head_length_mm"],
                          "spacer_piece_count": len(roles) - 5, "nut_side_spacer_mm": axis.get("nut_side_spacer_mm", 0),
                          "Actual": "", "Disposition": ""})
        selection = next(r for r in g["selected_stack_overrides"] if r["axis_id"] == identity)
        selection["head_side_fitting_ids"], selection["nut_side_fitting_ids"] = (
            selection.get("nut_side_fitting_ids", ""), selection.get("head_side_fitting_ids", ""))
        selection.update(installation_orientation_revision=REVISION, head_faces="exterior", nut_faces="interior",
                         thread_window_recheck_required=True, old_thread_window_margins_apply=False,
                         Actual="", Disposition="")

    assert len(moves) == 40 and sum(r["exterior_face"] == "top" for r in moves) == 8 and len(changed) == 224
    verify_attachment_axes(g["axes"], expected_ports=96)
    assert g["profiles"] == parent["profiles"] and g["screw_axes"] == parent["screw_axes"]
    assert g["fitting_poses"] == parent["fitting_poses"] and len(g["axes"]) == 96
    identities = {r["axis_id"] for r in moves}
    assert all(a == b for a, b in zip(g["axes"], parent["axes"], strict=True) if a["id"] not in identities)
    g.update(revision=REVISION, changed_finished_solids=list(registry.values()),
             inward_bolt_revision={"parent": receipt["checked_geometry"], "transforms": moves,
                                   "replacement_part_ids": sorted(changed), "axis_updates": axis_updates,
                                   "hardware_summary": summaries, "holes_members_panels_and_screws_unchanged": True,
                                   "bolt_lengths_grades_and_spacer_counts_unchanged": True,
                                   "thread_windows_washer_seats_and_tool_access_requalified": False},
             new_response_computed=False, complete_joint_qualified=False, geometry_adopted=False,
             scope="Reverse 32 side and eight top-edge stacks; heads exterior, nuts and spacers interior. No hole, frame or purchase-length changes.",
             engineering_question="Do the exterior stack reversals fit the unchanged occupied frame?",
             source_sha256={**g["source_sha256"], **pins})
    path = out / "geometry.json"
    path.write_bytes(encode(g))
    code = inspect.getsource(clearance.check)
    assert code.count("    for first in sorted(changed):") == 1
    code = code.replace("    for first in sorted(changed):", "    for first in sorted(REPLACEMENT_IDS):")
    code = code.replace("'occupied_part_count': len(bank),",
                        "'newly_checked_part_ids': sorted(REPLACEMENT_IDS), 'reused_unchanged_pair_clearance': PRIOR_CLEARANCE, 'occupied_part_count': len(bank),")
    scope = {**vars(clearance), "REPLACEMENT_IDS": changed, "PRIOR_CLEARANCE": receipt["checked_clearance"]}
    exec(compile(code, str(OWN), "exec"), scope)  # noqa: S102 -- existing exact intersection method; explicit incremental part set
    scope["check"](path, out / "clearance.json")
    result = json.loads((out / "clearance.json").read_bytes())
    assert result["occupied_part_count"] == 1037
    assert all(sha(p) == digest for p, digest in pins.items())
    print(json.dumps({"reversed_stacks": len(moves), "changed_parts": len(changed),
                      "nominal_geometry_clear": result["nominal_geometry_clear"],
                      "collisions": result["collisions"]}), flush=True)


def publish(out):
    previous = json.loads((out / "parent-index.json").read_bytes())
    assert (ROOT / INDEX).read_bytes() == (out / "parent-index.json").read_bytes(), "live index changed"
    assert not (ROOT / PACKET).exists() and not (ROOT / SCENE).exists()
    g = json.loads((out / "geometry.json").read_bytes())
    c = json.loads((out / "clearance.json").read_bytes())
    assert g["revision"] == REVISION and c["geometry"] == ref(out / "geometry.json")
    assert c["nominal_geometry_clear"], "resolve occupied collisions before publishing"
    (ROOT / PACKET).mkdir()
    orientation = g["inward_bolt_revision"]
    updates = ROOT / PACKET / "orientation.json"
    updates.write_bytes(encode(orientation))
    path = ROOT / PACKET / "geometry.json"
    report = {"schema": "eoere_inward_bolts_revision/v1", "revision": REVISION,
              "candidate": previous["evidence_candidate"], "parent_geometry": previous["geometry"],
              "checked_geometry": ref(out / "geometry.json"), "checked_clearance": ref(out / "clearance.json"),
              "counts": json.loads((ROOT / previous["geometry"]["receipt"]["path"]).read_bytes())["counts"],
              "files": {"orientation.json": ref(updates)}, "producer": ref(OWN),
              "reversed_stacks": 40, "side_stacks": 32, "top_stacks": 8, "changed_hardware_parts": 224,
              "nominal_geometry_clear": True, "holes_members_panels_and_screws_unchanged": True,
              "bolt_lengths_grades_and_spacer_counts_unchanged": True,
              "thread_windows_washer_seats_and_tool_access_requalified": False,
              "current_response_computed": False, "historical_capacity_transferred": False,
              "complete_conditional_frame_evaluation": False, "panel_Hillman_resolution_deferred": True,
              "fabrication_released": False, "climbing_released": False, "actual_observations": None}
    path.write_bytes(encode(report))
    scene = {"schema": "eoere_inward_bolts_patch/v1", "revision": REVISION,
             "key": previous["geometry"]["viewer"], "parent_scene": previous["geometry"]["scene"],
             "parent_layout": previous["geometry"]["receipt"], "layout_report": ref(path),
             "part_count": 1037, "counts": report["counts"],
             "transforms": [{k: row[k] for k in ("axis_id", "exterior_face", "roles", "rotation_axis_xyz",
                             "rotation_center_xyz_mm", "rotation_matrix_row_major", "translation_xyz_mm")}
                            for row in orientation["transforms"]],
             "bounds_mm": [[min(r["bounds_xyz_mm"][2 * i] for r in g["changed_finished_solids"]) for i in range(3)],
                           [max(r["bounds_xyz_mm"][2 * i + 1] for r in g["changed_finished_solids"]) for i in range(3)]],
             "historical_capacity_transferred": False, "current_response_computed": False,
             "complete_conditional_frame_evaluation": False,
             "thread_windows_washer_seats_and_tool_access_requalified": False,
             "panel_Hillman_resolution_deferred": True, "fabrication_released": False, "climbing_released": False}
    (ROOT / SCENE).write_bytes(encode(scene))
    index = copy.deepcopy(previous)
    for key in ("engineering_review", "testing_review", "bolt_geometry_review"):
        index.pop(key, None)
    index.update(schema="bolted_frame_development_revisions/v12", preceding_revision=previous,
                 geometry={"revision": REVISION, "viewer": scene["key"], "receipt": ref(path), "scene": ref(SCENE)},
                 hardware_model={**index["hardware_model"], "revision": REVISION, "receipt": ref(path)},
                 shop={**index["shop"], "revision": REVISION, "geometry": ref(path), "result": ref(path)},
                 preserved_owner_v6_viewer="eoere-owner-frame-v6-development")
    (ROOT / INDEX).write_bytes(encode(index))
    print(json.dumps({"geometry": ref(path), "scene": ref(SCENE), "counts": report["counts"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "publish"))
    parser.add_argument("--out", type=Path, default=ROOT / BASE / "geometry")
    args = parser.parse_args()
    (build if args.action == "build" else publish)(args.out.resolve())
