"""Build and publish the shorter A574 bolts and single factory cleat spacers.

All v8 timber, holes, fittings, panel screws and inward bolt directions remain.
The small viewer patch applies the checked affine transforms to existing meshes.
"""

from __future__ import annotations

import argparse
import copy
import inspect
import json
from pathlib import Path

import cadquery as cq

from scripts import eoere_leg_header_clearance as clearance
from scripts.eoere_inward_bolts import encode
from scripts.eoere_leg_header_revision import verify_attachment_axes
from scripts.eoere_paired_frame_basis import RAW, ROOT, read, ref, sha
from scripts.eoere_single_spacer_basis import AXES, FACTS, PACKET, PARAMETERS, REVISION

BASE = RAW / "frame-completion-v1/owner-single-spacer-stacks-v9"
INDEX = Path("docs/bolted-frame-development/development-revisions.json")
SCENE = Path("site/eoere-single-spacer-scene.json")
OWN = Path(__file__).resolve()


def build(out):
    assert not out.exists(), "fresh ignored output required"
    pins = {ref(OWN)["path"]: sha(OWN)}
    parameters = read(PARAMETERS, pins)
    facts = read(FACTS, pins, parameters["facts"]["sha256"])
    assert parameters["producer"] == ref(parameters["producer"]["path"])
    pins[parameters["producer"]["path"]] = parameters["producer"]["sha256"]
    g = read(parameters["parent_checked_geometry"]["path"], pins, parameters["parent_checked_geometry"]["sha256"])
    assert g["revision"] == "eoere-inward-bolts-and-angles-v8"
    prior = read(parameters["parent_clearance"]["path"], pins, parameters["parent_clearance"]["sha256"])
    assert prior["nominal_geometry_clear"] and prior["occupied_part_count"] == 1037
    parent = copy.deepcopy(g)
    registry = {r["id"]: r for r in g["changed_finished_solids"]}
    selections = {r["axis_id"]: r for r in g["selected_stack_overrides"]}
    axes = {a["id"]: a for a in g["axes"]}
    out.mkdir(parents=True)
    (out / "producer-snapshot.py").write_bytes(OWN.read_bytes())
    replacements, observed = set(), []

    def load(row):
        assert sha(row["path"]) == row["sha256"], row["path"]
        pins[row["path"]] = row["sha256"]
        return cq.Shape.importBrep(str(ROOT / row["path"]))

    for update in parameters["axis_updates"]:
        identity = update["axis_id"]
        assert axes[identity] == update["before_axis"] and selections[identity] == update["before_selection"]
        axes[identity], selections[identity] = update["after_axis"], update["after_selection"]
    for change in parameters["part_transforms"]:
        name, role = change["name"], change["role"]
        assert registry[name] == change["before"]
        before = load(registry[name])
        axis = axes[change["axis_id"]]
        point, direction = cq.Vector(*axis["point_xyz_mm"]), cq.Vector(*axis["direction_xyz"])
        if role == "shaft":
            start = point - direction.multiply(axis["hardware_scenario"]["washer_thickness_mm"])
            body = cq.Solid.makeCylinder(axis["diameter_mm"] / 2, axis["nominal_under_head_length_mm"], start, direction)
            assert abs(before.intersect(body).Volume() - body.Volume()) < 1e-5, "shorter shaft must be contained in the old envelope"
        elif role == "spacer":
            second = load(registry[change["axis_id"]+"_spacer_2"])
            body = before.fuse(second).clean()  # CAD envelope for one factory one-inch spacer, not physical joining.
            expected = 3.141592653589793 / 4 * (facts["spacer"]["outside_diameter_mm"]**2-facts["spacer"]["inside_diameter_mm"]**2) * 25.4
            assert abs(body.Volume()-expected) < 1e-5
        else:
            assert role == "nut"
            body = before.translate(cq.Vector(*change["translation_xyz_mm"]))
        assert body.isValid() and len(body.Solids()) == 1
        path = out / (name+".brep")
        assert body.exportBrep(str(path))
        box = body.BoundingBox()
        row = {"id": name, "kind": "bolt", **ref(path), "bytes": path.stat().st_size,
               "volume_mm3": body.Volume(), "center_of_mass_xyz_mm": list(body.Center().toTuple()),
               "bounds_xyz_mm": [getattr(box, a+end) for a in "xyz" for end in ("min", "max")]}
        expected = change["predicted_after"]
        assert abs(row["volume_mm3"]-expected["volume_mm3"]) < 1e-5
        for key in ("center_of_mass_xyz_mm", "bounds_xyz_mm"):
            assert max(abs(a-b) for a, b in zip(row[key], expected[key], strict=True)) < 1e-5
        observed.append({"name": name, "before": change["before"], "after": row})
        registry[name] = row
        replacements.add(name)
    removed = [r["id"] for r in parameters["removed_parts"]]
    for row in parameters["removed_parts"]:
        assert registry.pop(row["id"]) == row
    g.update(revision=REVISION, axes=[axes[a["id"]] for a in g["axes"]],
             selected_stack_overrides=[selections[r["axis_id"]] for r in g["selected_stack_overrides"]],
             changed_finished_solids=list(registry.values()), new_response_computed=False,
             complete_joint_qualified=False, geometry_adopted=False, release=False,
             scope="Eight 7.5-inch A574 cleat bolts with one one-inch factory spacer each; cumulative inward bolts and inset angles retained.",
             single_spacer_revision={"parameters": ref(PARAMETERS), "facts": ref(FACTS),
                                     "parent_geometry": parameters["parent_checked_geometry"],
                                     "replacement_part_ids": sorted(replacements), "removed_part_ids": removed,
                                     "observed_part_changes": observed,
                                     "holes_profiles_fittings_and_66_screws_unchanged": True,
                                     "forty_inward_directions_preserved": True,
                                     "current_mechanics_or_strength_transferred": False},
             source_sha256={**g["source_sha256"], **pins})
    assert len(g["axes"]) == 96 and len(replacements) == 24 and len(removed) == 16
    assert g["profiles"] == parent["profiles"] and g["fitting_poses"] == parent["fitting_poses"]
    assert g["screw_axes"] == parent["screw_axes"] and len(g["screw_axes"]) == 66
    for a, b in zip(g["axes"], parent["axes"], strict=True):
        for key in ("point_xyz_mm", "direction_xyz", "receivers", "attachments", "grip_mm", "before_plate_mm", "after_plate_mm"):
            assert a[key] == b[key]
        if a["id"] not in AXES:
            assert a == b
    verify_attachment_axes(g["axes"], expected_ports=96)
    path = out / "geometry.json"
    path.write_bytes(encode(g))
    code = inspect.getsource(clearance.check)
    assert code.count("    for first in sorted(changed):") == 1
    code = code.replace("    for first in sorted(changed):", "    for first in sorted(REPLACEMENT_IDS):")
    code = code.replace("'occupied_part_count': len(bank),",
                        "'newly_checked_part_ids': sorted(REPLACEMENT_IDS), 'explicitly_removed_part_ids': REMOVED_IDS, 'reused_unchanged_pair_clearance': PRIOR_CLEARANCE, 'occupied_part_count': len(bank),")
    scope = {**vars(clearance), "REPLACEMENT_IDS": replacements, "REMOVED_IDS": removed,
             "PRIOR_CLEARANCE": parameters["parent_clearance"]}
    exec(compile(code, str(OWN), "exec"), scope)  # noqa: S102 -- pinned full-registry intersection method with explicit changed/removed sets
    scope["check"](path, out / "clearance.json")
    c = json.loads((out / "clearance.json").read_bytes())
    assert c["occupied_part_count"] == 1021 and c["nominal_geometry_clear"]
    assert all(sha(p) == digest for p, digest in pins.items())
    print(json.dumps({"geometry": ref(path), "clearance": ref(out / "clearance.json"), "changed_parts": 24, "removed_parts": 16}), flush=True)


def publish(out):
    assert not (ROOT / SCENE).exists() and not (ROOT / PACKET / "geometry.json").exists()
    index_bytes = (ROOT / INDEX).read_bytes()
    previous = json.loads(index_bytes)
    parameters = json.loads((ROOT / PARAMETERS).read_bytes())
    assert previous["geometry"] == parameters["parent_geometry"], "current geometry advanced during hardware work"
    g = json.loads((out / "geometry.json").read_bytes())
    c = json.loads((out / "clearance.json").read_bytes())
    assert c["geometry"] == ref(out / "geometry.json") and c["nominal_geometry_clear"]
    assert g["revision"] == REVISION and g["single_spacer_revision"]["parameters"] == ref(PARAMETERS)
    (out / "publication-parent-index.json").write_bytes(index_bytes)
    parent_report = json.loads((ROOT / previous["geometry"]["receipt"]["path"]).read_bytes())
    counts = {**parent_report["counts"], "spacer_pieces": 16, "occupied_parts": 1021}
    files = {"hardware-facts.json": ref(FACTS), "candidate-parameters.json": ref(PARAMETERS)}

    def put(name, value):
        path = ROOT / PACKET / name
        path.write_bytes(value if isinstance(value, bytes) else encode(value))
        files[name] = ref(path)

    from scripts.eoere_paired_shop import csv_bytes
    put("hardware-selection.csv", csv_bytes([u["after_selection"] for u in parameters["axis_updates"]]))
    put("stack-checks.json", {"facts": ref(FACTS), "checks": parameters["stack_checks"],
                              "actual_or_complete_joint_qualified": False})
    put("mechanics-input-delta.json", {"parent_geometry": previous["geometry"], "new_checked_geometry": ref(out / "geometry.json"),
                                      "axis_updates": parameters["axis_updates"],
                                      "changed_parts": g["single_spacer_revision"]["observed_part_changes"],
                                      "removed_parts": parameters["removed_parts"],
                                      "frame_geometry_and_joint_contact_locations_unchanged": True,
                                      "hardware_gravity_and_capture_offsets_require_comparison": True,
                                      "existing_mechanical_results_transferred": False})
    put("layout.md", ("# Single factory spacers and shorter cleat bolts\n\n"
        "Current development revision `"+REVISION+"` uses eight 3/8-16 × 7½-inch ASTM A574 socket-cap bolts "
        "(Bolt Depot 8095), each with one 1-inch steel factory spacer (13733), the retained Grade 8 nut and two specified washers. "
        "This replaces each preceding 8-inch bolt and three half-inch spacers. Total spacers fall from 32 to 16; "
        "all 96 bolt axes, inward orientations, inset angles, timber, panels and 66 Hillman screws remain.\n\n"
        "[Eight hardware selections](hardware-selection.csv) · [catalog facts](hardware-facts.json) · "
        "[dimensional checks](stack-checks.json) · [mechanics input delta](mechanics-input-delta.json). "
        "The shorter 7-inch product is rejected because its catalog minimum body does not cover all current steel bearing. "
        "The eight header stacks already use one half-inch spacer each and retain their own hardware.\n\n"
        "The nominal and minimum-thickness USS washer checks pass the recorded smooth-body, free-nut-seating and two-pitch projection references. "
        "Actual clamped wood/steel thickness, spacer dimensions, body/runout and full engagement remain unobserved. "
        "A gaged clamped wood/plate thickness of at least 130.0988 mm is needed with the stated minimum washers and nominal spacer; "
        "the corresponding conservative upper reference is 145.034 mm for two-pitch projection. These are conditional review limits, not measured fit. "
        "Earlier force/strength passes do not transfer; changed metal mass, nut offsets and joint behavior require their own applicable comparison. "
        "No cutting, drilling, fabrication or climbing release. Actual/Disposition cells remain blank.\n").encode())
    report = {"schema": "eoere_single_spacer_revision/v1", "revision": REVISION,
              "candidate": previous["evidence_candidate"], "parent_geometry": previous["geometry"],
              "checked_geometry": ref(out / "geometry.json"), "checked_clearance": ref(out / "clearance.json"),
              "files": files, "producer": ref(OWN), "counts": counts, "changed_stacks": 8,
              "changed_parts": 24, "removed_spacer_parts": 16, "nominal_geometry_clear": True,
              "nominal_catalog_windows_checked": True, "actual_parts_verified": False,
              "timber_holes_fittings_and_66_screws_unchanged": True, "forty_inward_stacks_preserved": True,
              "current_response_computed": False, "historical_capacity_transferred": False,
              "complete_conditional_frame_evaluation": False, "panel_Hillman_resolution_deferred": True,
              "geometry_adopted": False, "fabrication_released": False, "climbing_released": False,
              "actual_observations": None}
    path = ROOT / PACKET / "geometry.json"
    path.write_bytes(encode(report))
    scene = {"schema": "eoere_single_spacer_patch/v1", "revision": REVISION,
             "key": previous["geometry"]["viewer"], "parent_scene": previous["geometry"]["scene"],
             "parent_layout": previous["geometry"]["receipt"], "layout_report": ref(path),
             "part_count": 1021, "counts": counts,
             "part_transforms": [{k: r[k] for k in ("name", "axis_id", "role", "scale_xyz", "translation_xyz_mm")}
                                 for r in parameters["part_transforms"]],
             "removals": [r["id"] for r in parameters["removed_parts"]],
             "stack_updates": [u["after_selection"] for u in parameters["axis_updates"]],
             "current_response_computed": False, "historical_capacity_transferred": False,
             "complete_conditional_frame_evaluation": False, "panel_Hillman_resolution_deferred": True,
             "fabrication_released": False, "climbing_released": False}
    (ROOT / SCENE).write_bytes(encode(scene))
    index = copy.deepcopy(previous)
    for key in ("engineering_review", "testing_review", "bolt_geometry_review", "panel_bracing_review"):
        index.pop(key, None)
    index.update(schema="bolted_frame_development_revisions/v14", preceding_revision=previous,
                 geometry={"revision": REVISION, "viewer": scene["key"], "receipt": ref(path), "scene": ref(SCENE)},
                 hardware_model={**index["hardware_model"], "revision": REVISION, "receipt": ref(path)},
                 shop={**index["shop"], "revision": REVISION, "geometry": ref(path), "result": ref(path)},
                 preserved_owner_v8_viewer="eoere-owner-frame-v8-development")
    assert (ROOT / INDEX).read_bytes() == index_bytes, "current index changed during publication"
    (ROOT / INDEX).write_bytes(encode(index))
    print(json.dumps({"geometry": ref(path), "scene": ref(SCENE), "counts": counts}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "publish"))
    parser.add_argument("--out", type=Path, default=ROOT / BASE / "geometry")
    args = parser.parse_args()
    (build if args.action == "build" else publish)(args.out.resolve())
