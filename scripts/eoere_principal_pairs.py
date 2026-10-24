"""Restore the center principal/header upper pairs beside the flat cleats.

The cleat perimeter and height remain those of the reference. Extending the
cleat toward bolt 039 is a conditional remedy after a failed calculation.
"""

from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import inspect
import io
import json
from pathlib import Path

import cadquery as cq
import numpy as np

from scripts import eoere_leg_header_clearance as clearance
from scripts import eoere_paired_shop as shop
from scripts.eoere_leg_header_revision import verify_attachment_axes
from scripts.eoere_paired_frame_basis import RAW, ROOT, read, ref, sha
from scripts.eoere_reference_cleats import encode
from scripts.export_wood_joint_wj24_scene import (
    _deduplicate_triangle_topologies,
    _shape_mesh,
)

REVISION = "eoere-flat-cleats-principal-upper-pairs-v6"
BASE = RAW / "frame-completion-v1/owner-principal-pairs-v6"
PREVIOUS = Path("docs/bolted-frame-development/owner-frame-v5")
PACKET = Path("docs/bolted-frame-development/owner-frame-v6")
INDEX = Path("docs/bolted-frame-development/development-revisions.json")
SCENE = Path("site/eoere-owner-frame-v6-scene.json.gz")
PAIRS = (("left", "eoere_bolt_068", "eoere_bolt_072"),
         ("right", "eoere_bolt_069", "eoere_bolt_073"))
COUNTS = {"sawn_members": 20, "plywood_cleats": 4, "panels": 6, "angles": 24,
          "bolt_stacks": 96, "nuts": 96, "washers": 192, "spacer_pieces": 32,
          "Hillman_axes": 66, "receiver_occurrences": 120, "occupied_parts": 1037}


def build(out):
    assert not out.exists(), "fresh output required"
    pins = {ref(Path(__file__))["path"]: sha(Path(__file__))}
    receipt = read(PREVIOUS / "geometry.json", pins)
    g = read(receipt["checked_geometry"]["path"], pins, receipt["checked_geometry"]["sha256"])
    parent = copy.deepcopy(g)
    assert g["revision"] == "eoere-reference-cleat-upper-pair-v5"
    read(receipt["checked_clearance"]["path"], pins, receipt["checked_clearance"]["sha256"])
    registry = {r["id"]: r for r in g["changed_finished_solids"]}
    axes = {a["id"]: a for a in g["axes"]}
    out.mkdir(parents=True)
    (out / "producer-snapshot.py").write_bytes(Path(__file__).read_bytes())
    changed, additions, proofs = set(), [], []

    def load(row):
        assert sha(row["path"]) == row["sha256"]
        pins[row["path"]] = row["sha256"]
        return cq.Shape.importBrep(str(ROOT / row["path"]))

    def save(name, body, kind):
        assert body.isValid() and len(body.Solids()) == 1
        p = out / (name + ".brep")
        assert body.exportBrep(str(p))
        box = body.BoundingBox()
        row = {"id": name, "kind": kind, **ref(p), "bytes": p.stat().st_size,
               "volume_mm3": body.Volume(), "center_of_mass_xyz_mm": list(body.Center().toTuple()),
               "bounds_xyz_mm": [getattr(box, a + b) for a in "xyz" for b in ("min", "max")]}
        registry[name] = row
        changed.add(name)
        if name in g["profiles"]:
            g["profiles"][name]["finished"] = row

    flat = []
    for name, p in g["profiles"].items():
        if not name.startswith("eoere_cleat_"):
            continue
        body = load(p["finished"])
        faces = [f for f in body.Faces() if f.geomType() == "PLANE" and abs(f.normalAt().x) > .99999]
        assert len(faces) == 2
        for f in faces:
            assert len(f.outerWire().Edges()) == 4 and all(e.geomType() == "LINE" for e in f.outerWire().Edges())
            assert len(f.innerWires()) == 4
        flat.append({"member": name, "outline_edges_per_face": 4, "straight_edges_only": True,
                     "bolt_holes_per_leaf": 4, "finished": p["finished"]})
    assert len(flat) == 4

    for side, identity, original_id in PAIRS:
        a = copy.deepcopy(axes[original_id])
        a["id"] = identity
        a["point_xyz_mm"][1] -= 50.8
        for port in a["attachments"]:
            port["point"][1] -= 50.8
            port["transverse"] *= -1
            port["transverse_mm"] *= -1
            port["installed_bolt_axis_id"] = identity
        axes[identity] = a
        roles = sorted(n[len(original_id) + 1:] for n in registry if n.startswith(original_id + "_"))
        assert set(roles) == {"shaft", "head", "head_washer", "nut_washer", "nut"}
        for role in roles:
            save(identity + "_" + role,
                 load(registry[original_id + "_" + role]).translate((0, -50.8, 0)), "bolt")
        name = "base_principal_center_" + side
        before = load(g["profiles"][name]["finished"])
        point, direction = cq.Vector(*a["point_xyz_mm"]), cq.Vector(*a["direction_xyz"])
        cutter = cq.Solid.makeCylinder(a["bore_diameter_mm"] / 2, 100, point - direction, direction)
        removed = before.intersect(cutter).Volume()
        assert abs(removed - np.pi * (a["bore_diameter_mm"] / 2) ** 2 * 38.1) < .001
        save(name, before.cut(cutter).clean(), "timber")
        selected = copy.deepcopy(next(r for r in g["selected_stack_overrides"] if r["axis_id"] == original_id))
        selected.update(axis_id=identity, Actual="", Disposition="",
                        reason="Restored center principal upper pair; copy the retained nominal stack; no revised strength or eligibility pass.")
        g["selected_stack_overrides"].append(selected)
        additions.append({"axis_id": identity, "copied_stack_axis": original_id,
                          "translation_xyz_mm": [0, -50.8, 0], "roles": roles})
        proofs.append({"axis_id": identity, "receiver": name, "full_bore_wall_mm": 38.1,
                       "removed_volume_mm3": removed})

    verify_attachment_axes(list(axes.values()), expected_ports=96)
    assert all(axes[a["id"]] == a for a in parent["axes"])
    assert len(axes) == 96 and g["screw_axes"] == parent["screw_axes"] and len(changed) == 12
    g.update(revision=REVISION, current_bolt_count=96, axes=list(axes.values()),
             changed_finished_solids=list(registry.values()),
             removed_axes=[i for i in g["removed_axes"] if i not in {"eoere_bolt_068", "eoere_bolt_069"}],
             unbolted_factory_contact_receivers=[], new_response_computed=False,
             complete_joint_qualified=False, geometry_adopted=False,
             principal_pair_revision={"parent": receipt["checked_geometry"], "added_stacks": additions,
                                      "replacement_part_ids": sorted(changed), "full_wall_proofs": proofs,
                                      "flat_cleat_proofs": flat, "cleat_height_changed": False,
                                      "extend_toward_bolt_039_only_after_failed_calculation": True,
                                      "complete_upper_pair_eligibility_established": False},
             source_sha256={**g["source_sha256"], **pins})
    path = out / "geometry.json"
    path.write_bytes(encode(g))
    code = inspect.getsource(clearance.check)
    assert code.count("    for first in sorted(changed):") == 1
    code = code.replace("    for first in sorted(changed):", "    for first in sorted(REPLACEMENT_IDS):")
    code = code.replace("'occupied_part_count': len(bank),",
                        "'newly_checked_part_ids': sorted(REPLACEMENT_IDS), 'reused_unchanged_pair_clearance': PRIOR_CLEARANCE, 'occupied_part_count': len(bank),")
    scope = {**vars(clearance), "REPLACEMENT_IDS": changed, "PRIOR_CLEARANCE": receipt["checked_clearance"]}
    exec(compile(code, str(Path(__file__)), "exec"), scope)  # noqa: S102 -- reuse the pinned complete-registry method with an explicit incremental part set
    scope["check"](path, out / "clearance.json")
    result = json.loads((out / "clearance.json").read_text())
    assert result["nominal_geometry_clear"] and result["occupied_part_count"] == 1037
    assert all(sha(p) == h for p, h in pins.items())
    print(json.dumps({"geometry": ref(path), "counts": COUNTS, "flat_cleats": len(flat)}), flush=True)


def publish(out):
    assert not (ROOT / PACKET).exists() and not (ROOT / SCENE).exists()
    previous = json.loads((ROOT / INDEX).read_bytes())
    assert previous["schema"] == "bolted_frame_development_revisions/v10"
    g = json.loads((out / "geometry.json").read_bytes())
    c = json.loads((out / "clearance.json").read_bytes())
    assert c["geometry"] == ref(out / "geometry.json") and c["nominal_geometry_clear"]
    (ROOT / PACKET).mkdir()
    files = {}

    def put(name, value):
        p = ROOT / PACKET / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(value if isinstance(value, bytes) else encode(value))
        files[name] = ref(p)

    identities = {i for _, i, _ in PAIRS}
    new_axes = [a for a in g["axes"] if a["id"] in identities]
    put("axes-additions.json", {"parent_axes": ref(PREVIOUS / "axes.json"), "axes": new_axes,
                                "screw_axes_changed": False, "fitting_poses_changed": False})
    updated = {"base_principal_center_" + side: g["profiles"]["base_principal_center_" + side] for side, _, _ in PAIRS}
    put("member-updates.json", updated)
    holes = [r for r in csv.DictReader(io.StringIO((ROOT / PREVIOUS / "receiver-holes.csv").read_text()))
             if r["receiver"] in updated]
    for a in new_axes:
        name = a["receivers"][0]
        p = updated[name]
        row = {"axis_id": a["id"], "receiver": name, "nominal_shaft_diameter_mm": 9.525,
               "modeled_bore_envelope_diameter_mm": 10.31875, "saved_full_wall_length_mm": 38.1,
               "Actual": "", "Disposition": ""}
        point, direction = np.asarray(a["point_xyz_mm"]), np.asarray(a["direction_xyz"])
        for prefix, distance in (("entry", 0.), ("exit", 38.1)):
            local = np.asarray(p["basis_grain_u_v_xyz"]) @ (point + direction * distance - p["datum_xyz_mm"])
            for letter, value in zip("luv", local, strict=True):
                row[prefix + "_in_receiver_" + letter + "_mm"] = float(value)
        holes.append(row)

    def table(rows):
        keys = list(dict.fromkeys(k for r in rows for k in r))
        return shop.csv_bytes([{k: r.get(k, "") for k in keys} for r in rows])

    put("receiver-updates.csv", table(holes))
    put("hardware-additions.csv", table([r for r in g["selected_stack_overrides"] if r["axis_id"] in identities]))
    for name, p in updated.items():
        drawing = shop.drawing(name, p, [r for r in holes if r["receiver"] == name])
        drawing = drawing.replace(b"millimetre datum and drill sheet", b"millimetre geometry review")
        drawing = drawing.replace(b"Exact drilling coordinates appear below.", b"Review coordinates appear below; no cutting or drilling release.")
        put("drawings/" + name + ".svg", drawing)
    put("layout.md", ("# Paired center principal/header geometry review\n\n"
        "Applies to `" + REVISION + "`. Two upper bolts are now present at each exterior cleat and at each center principal/header angle. All cleat sides remain straight, without tabs or steps.\n\n"
        "The [two added axes](axes-additions.json) compose with the preceding [94 axes](../owner-frame-v5/axes.json). [Updated principal receivers](receiver-updates.csv) and [member profiles](member-updates.json) replace those members' previous records. The other 118 receiver rows retain their scope apart from these updated member rows. Actual/Disposition cells stay blank.\n\n"
        "[Left principal](drawings/base_principal_center_left.svg) · [Right principal](drawings/base_principal_center_right.svg) · [Unchanged flat cleat drawings](../owner-frame-v5/layout.md).\n\n"
        "These are nominal review coordinates. Restored upper-pair edge/end/row eligibility and revised forces and strength remain open. No cutting or drilling release follows. Extending the cleat toward bolt 039 remains conditional on a failed calculation and is not modeled here.\n").encode())
    report = {"schema": "eoere_principal_pair_revision/v1", "revision": REVISION,
              "candidate": previous["evidence_candidate"], "parent_geometry": previous["geometry"],
              "checked_geometry": ref(out / "geometry.json"), "checked_clearance": ref(out / "clearance.json"),
              "counts": COUNTS, "files": files, "principal_pair_revision": g["principal_pair_revision"],
              "nominal_geometry_clear": True, "current_response_computed": False,
              "old_force_pass_transferred": False, "upper_pair_eligible": False,
              "complete_conditional_frame_evaluation": False, "panel_Hillman_resolution_deferred": True,
              "fabrication_released": False, "climbing_released": False,
              "actual_observations": None, "producer": ref(Path(__file__))}
    path = ROOT / PACKET / "geometry.json"
    path.write_bytes(encode(report))
    registry = {r["id"]: r for r in g["changed_finished_solids"]}
    patches = []
    for name in g["principal_pair_revision"]["replacement_part_ids"]:
        row = registry[name]
        fabrication = {"kind": row["kind"], "owner_frame_revision": REVISION,
                       "description": "Paired center principal/header bolts; nominal geometry review only"}
        other = {}
        if row["kind"] == "bolt":
            _, identity, retained = next(v for v in PAIRS if name.startswith(v[1] + "_"))
            role = name[len(identity) + 1:]
            fabrication.update(connection_name=identity, hardware_role=role,
                               stack_roles=["shaft", "head", "head_washer", "nut_washer", "nut"],
                               diameter_mm=9.525, delivered_part_verified=False)
            other["copy_metadata_from"] = retained + "_" + role
        assert sha(row["path"]) == row["sha256"]
        patches.append({"id": name, "name": name, "fabrication": fabrication,
                        "mesh": _shape_mesh(cq.Shape.importBrep(str(ROOT / row["path"]))), **other})
    scene = {"schema": "eoere_principal_pair_patch/v1", "revision": REVISION,
             "key": "eoere-current-frame-development", "parent_scene": previous["geometry"]["scene"],
             "parent_layout": previous["geometry"]["receipt"], "layout_report": ref(path),
             "part_count": 1037, "counts": COUNTS, "replacements": patches, "removals": [],
             "flat_cleat_outline_yz_mm": g["reference_cleat_revision"]["outline_yz_mm"],
             "historical_capacity_transferred": False, "current_response_computed": False,
             "complete_conditional_frame_evaluation": False, "upper_pair_eligible": False,
             "panel_Hillman_resolution_deferred": True, "fabrication_released": False, "climbing_released": False}
    scene["triangle_topologies"] = _deduplicate_triangle_topologies(patches)
    decoded = (json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n").encode()
    (ROOT / SCENE).write_bytes(gzip.compress(decoded, compresslevel=9, mtime=0))
    scene_ref = {**ref(SCENE), "decoded_sha256": hashlib.sha256(decoded).hexdigest()}
    index = {**copy.deepcopy(previous), "schema": "bolted_frame_development_revisions/v11",
             "geometry": {"revision": REVISION, "viewer": scene["key"], "receipt": ref(path), "scene": scene_ref},
             "hardware_model": {**copy.deepcopy(previous["hardware_model"]), "revision": REVISION, "receipt": ref(path)},
             "shop": {**copy.deepcopy(previous["shop"]), "revision": REVISION, "geometry": ref(path), "result": ref(path)},
             "preserved_owner_v5_viewer": "eoere-owner-frame-v5-development", "preceding_revision": previous}
    (ROOT / INDEX).write_bytes(encode(index))
    print(json.dumps({"geometry": ref(path), "scene": scene_ref, "counts": COUNTS}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "publish"))
    parser.add_argument("--out", type=Path, default=ROOT / BASE / "geometry")
    args = parser.parse_args()
    (build if args.action == "build" else publish)(args.out.resolve())
