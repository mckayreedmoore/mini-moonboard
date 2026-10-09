"""Extend only two cached cleats; inherit both frozen v3 viewer layers."""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path.cwd()
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
OWN = Path(__file__).resolve().relative_to(ROOT)
PROPOSAL = BASE / "cleat-top-extension-review-v1/profile-review.json"
PROPOSAL_SHA = "7c5fe6457b96be5af62ebb6d64b5610dbb24471bff24e9f467c06e0a1dfff6ae"
REVISION = "eoere-base-side-edge-cleats-v1"
CLEATS = ("eoere_cleat_left", "eoere_cleat_right")
ASSETS = {
    "site/eoere-bottom-rail-scene.json.gz": "28269c01354dd901ad87604fe80475fcbb19cf71ad6cebec29194e7fe94cf536",
    "site/eoere-cleat-trim-scene.json": "e49ed92875c8de3dfafbab10755fb49175662c0c4a3eaf5affe247da04535c57",
    "site/eoere-aligned-wire-scene.json.gz": "dbb6c2cdf65b4473b71a38faa233dd7c6f43bb02bb07ad6a702943c343947ee4",
    "site/eoere-adjusted-base-v3-scene.json.gz": "d77b9923b7d0df6b3416b2938b2d249a5406a9174fe98fba5118c341bc3df947",
    "site/eoere-2026-adjustments-v3-scene.json.gz": "8682bf9a81c0bf8e7ffb23c3f6725adc6d3c9bd4728b00e50edb696ca3305d1d",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify(pins):
    for path, digest in pins.items():
        assert sha(path) == digest, "frozen dependency changed: " + path


def merge(pins, bank):
    for path, digest in bank.items():
        assert path not in pins or pins[path] == digest, "conflicting source binding: " + path
        pins[path] = digest


def asset(path):
    data = Path(path).read_bytes()
    return json.loads(gzip.decompress(data) if path.endswith(".gz") else data)


def world_bounds(row, templates):
    mesh = row.get("mesh") or templates[row["template_id"]]["mesh"]
    bounds = mesh["bounds_xyz_mm"]
    assert len(bounds) == 6 and all(math.isfinite(v) for v in bounds)
    if not row.get("transform"):
        return bounds
    matrix = row["transform"]
    assert len(matrix) == 16 and all(math.isfinite(v) for v in matrix)
    corners = [tuple(sum(matrix[j * 4 + i] * p[j] for j in range(3)) + matrix[12 + i] for i in range(3))
               for p in itertools.product(*[(bounds[i], bounds[i + 1]) for i in (0, 2, 4)])]
    return [value for i in range(3) for value in (min(p[i] for p in corners), max(p[i] for p in corners))]


def compose_bounds(native, scenes):
    # The exporter stores CAD BoundingBox values, not extrema of quantized vertices.
    bank = {
        row["id"]: {"kind": row["kind"], "bounds": [v for pair in row["bounds_xyz_mm"] for v in pair]}
        for row in native["parts"] if row["kind"] in {"panel", "screw", "light", "tnut", "wire"}
    }
    assert len(bank) == 477
    for scene in scenes:
        templates = scene.get("mesh_templates", {}) or {r["id"]: r for r in scene.get("templates", [])}
        rows = scene.get("solids", scene.get("replacements", [])) + scene.get("additions", [])
        for row in rows:
            bank[row["name"]] = {"kind": row["fabrication"]["kind"], "bounds": world_bounds(row, templates)}
    return bank


def build(out):
    assert not out.exists(), "preserve all previous outputs; choose a fresh directory"
    assert out.resolve().is_relative_to((ROOT / OWN.parent).resolve())
    assert sha(PROPOSAL) == PROPOSAL_SHA
    proposal = read(PROPOSAL)
    base = read(DOC / "occupied-adjusted-base-v3.json")
    extra = read(DOC / "occupied-2026-adjustments-v3.json")
    native_path = DOC.parent / "native-geometry-v4.json"
    pins = {str(PROPOSAL): PROPOSAL_SHA, str(OWN): sha(OWN), **ASSETS}
    merge(pins, proposal["source_sha256"])
    merge(pins, base["source_sha256"])
    merge(pins, extra["source_sha256"])
    pins[str(native_path)] = sha(native_path)
    verify(pins)
    scenes = {path: asset(path) for path in ASSETS}
    base_path, extra_path = "site/eoere-adjusted-base-v3-scene.json.gz", "site/eoere-2026-adjustments-v3-scene.json.gz"
    assert scenes[base_path]["layout_report"]["sha256"] == sha(DOC / "occupied-adjusted-base-v3.json")
    assert scenes[extra_path]["layout_report"]["sha256"] == sha(DOC / "occupied-2026-adjustments-v3.json")
    common = [scenes[p] for p in ASSETS if p != extra_path]
    native = read(native_path)
    base_bank = compose_bounds(native, common)
    extra_bank = compose_bounds(native, [*common, scenes[extra_path]])
    assert len(base_bank) == 1021 and len(extra_bank) == 1380
    banks = {"base": base_bank, "extra": extra_bank}
    out.mkdir(parents=True)
    print("Frozen v3 inputs verified; importing only two cleats and two side members", flush=True)
    import cadquery as cq

    from scripts.export_wood_joint_wj24_scene import (
        _deduplicate_triangle_topologies,
        _shape_mesh,
    )
    from scripts.hl35_candidate import overlaps
    from scripts.hl35_full_fit_candidate import line_span

    for name, module in tuple(sys.modules.items()):
        if name.startswith(("scripts.", "mini_moonboard.")) and getattr(module, "__file__", None):
            path = Path(module.__file__).resolve().relative_to(ROOT)
            merge(pins, {str(path): sha(path)})
    verify(pins)
    records = {r["id"]: r for r in proposal["retained_side_and_cleat_body_bindings"]}
    originals = {r["id"]: r for r in proposal["new_finished_cleat_expectations"]}
    raw_polygon = proposal["new_cleat_YZ_polygon_mm"]
    old_top = records[CLEATS[0]]["bounds_xyz_mm"][2][1]
    y0, y1 = raw_polygon[0][0], raw_polygon[1][0]
    z0, z1 = raw_polygon[0][1], raw_polygon[2][1]
    rear_y, rear_z = proposal["base_side_rear_edge_YZ_mm"][0]
    old_corner_y = rear_y + (old_top - rear_z) / proposal["top_slope_dZ_dY"]
    added_polygon = [(old_corner_y, old_top), (y1, old_top), (y1, z1)]
    body_rows, mesh_rows, seats, contact_rows, screens = [], [], [], [], []
    old_metadata = {r["name"]: r["fabrication"] for r in scenes["site/eoere-cleat-trim-scene.json"]["solids"]}
    for name in CLEATS:
        old = cq.Shape.importBrep(records[name]["path"])
        side_name = "base_side_" + name.rsplit("_", 1)[1]
        side = cq.Shape.importBrep(records[side_name]["path"])
        x0, x1 = records[name]["bounds_xyz_mm"][0]
        thickness = x1 - x0
        assert abs(thickness - 38.1) < 1e-6
        raw = cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(raw_polygon).close().extrude(thickness).val()
        added = cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(added_polygon).close().extrude(thickness).val()
        new = old.fuse(added).clean()
        assert all(shape.isValid() and len(shape.Solids()) == 1 for shape in (old, side, raw, added, new))
        assert abs(added.Volume() - proposal["added_volume_mm3_each"]) < .001
        assert abs(new.Volume() - originals[name]["expected_finished_volume_mm3"]) < .001
        assert abs(overlaps(old, new) - old.Volume()) < .001
        assert abs(overlaps(raw, new) - new.Volume()) < .001
        b = new.BoundingBox()
        bounds = [[getattr(b, a + "min"), getattr(b, a + "max")] for a in "xyz"]
        expected_bounds = [[x0, x1], [y0, y1], [z0, z1]]
        assert max(abs(a - b) for pair, expected in zip(bounds, expected_bounds) for a, b in zip(pair, expected)) < 1e-6
        for axis in base["axes"]:
            if name not in axis["receivers"]:
                continue
            point, direction = cq.Vector(*axis["point_xyz_mm"]), cq.Vector(*axis["direction_xyz"])
            near, far = line_span(raw, point, direction)
            assert abs(far - near - thickness) < 1e-6
            bore = cq.Solid.makeCylinder(axis["bore_diameter_mm"] / 2, far - near, point + direction * near, direction)
            assert abs(overlaps(bore, raw) / bore.Volume() - 1) < 1e-8
            assert overlaps(bore, new) < .001
            outer_x = x0 if name.endswith("left") else x1
            inward = cq.Vector(1 if name.endswith("left") else -1, 0, 0)
            h = axis["hardware_scenario"]
            center = cq.Vector(outer_x, point.y, point.z)
            land = cq.Solid.makeCylinder(h["washer_od_mm"] / 2, 1, center, inward).cut(
                cq.Solid.makeCylinder(h["washer_id_mm"] / 2, 1, center, inward))
            fraction = overlaps(land, new) / land.Volume()
            assert abs(fraction - 1) < 1e-8
            seats.append({"axis_id": axis["id"], "receiver": name,
                          "full_bore_wall_mm": far - near, "nominal_annular_land_fraction": fraction})
        footprint = cq.Solid.makeBox(thickness, y1 - y0, 1, cq.Vector(x0, y0, z0))
        assert abs(overlaps(footprint, new) / footprint.Volume() - 1) < 1e-8
        inward = cq.Vector(1 if name.endswith("left") else -1, 0, 0)
        old_contact = overlaps(old.translate(inward), side)
        new_contact = overlaps(new.translate(inward), side)
        assert abs(new_contact - old_contact - proposal["added_cross_section_area_mm2_each"]) < .001
        assert overlaps(new, side) < .001 and overlaps(added, side) < .001
        contact_rows.append({"cleat": name, "side_member": side_name,
                             "one_mm_inward_slice_method": True,
                             "old_nominal_side_face_area_mm2": old_contact,
                             "new_nominal_side_face_area_mm2": new_contact,
                             "added_nominal_side_face_area_mm2": new_contact - old_contact,
                             "unshifted_intersection_mm3": overlaps(new, side),
                             "limit": "Prismatic shared X-face geometry only; no preload, contact pressure or strength."})
        ab = added.BoundingBox()
        added_bounds = [v for a in "xyz" for v in (getattr(ab, a + "min"), getattr(ab, a + "max"))]
        for layer, bank in banks.items():
            neighbors = [n for n, row in bank.items() if n != name and
                         all(added_bounds[i] <= row["bounds"][i + 1] + .001 and
                             row["bounds"][i] <= added_bounds[i + 1] + .001 for i in (0, 2, 4))]
            assert neighbors == [side_name], (name, layer, neighbors)
            minimum = min((max(max(row["bounds"][i] - added_bounds[i + 1], added_bounds[i] - row["bounds"][i + 1], 0)
                                for i in (0, 2, 4)), n)
                          for n, row in bank.items() if n not in (name, side_name))
            screens.append({"layer": layer, "cleat": name, "body_census": len(bank),
                            "body_bank_canonical_sha256": canonical(bank),
                            "bounds_proximity_padding_mm": .001,
                            "added_prism_bounds_xyz_mm": added_bounds,
                            "bounds_candidates": neighbors,
                            "minimum_other_body_separating_axis_gap_mm": minimum[0],
                            "nearest_other_body": minimum[1],
                            "unintended_candidates": [],
                            "method": "Authenticated exporter CAD bounds; affine template bounding-box corners are conservative. Added prism checked; unchanged old volume inherits only prior geometry evidence."})
        path = out / (name + ".brep")
        assert new.exportBrep(str(path))
        saved = cq.Shape.importBrep(str(path))
        assert saved.isValid() and len(saved.Solids()) == 1 and abs(saved.Volume() - new.Volume()) < 1e-6
        body_rows.append({"id": name, "path": str(path), "sha256": sha(path),
                          "bytes": path.stat().st_size, "volume_mm3": new.Volume(),
                          "parent_volume_mm3": old.Volume(), "added_volume_mm3": added.Volume(),
                          "raw_polygon_volume_mm3": raw.Volume(), "preserved_void_volume_mm3": raw.Volume() - new.Volume(),
                          "bounds_xyz_mm": bounds, "center_of_mass_xyz_mm": list(new.Center().toTuple()),
                          "runner_seat_area_mm2": thickness * (y1 - y0), "valid_single_solid": True})
        metadata = copy.deepcopy(old_metadata[name])
        metadata.update({"cleat_extension_revision": REVISION,
                         "description": "Full-thickness exterior cleat extended upward to the base_side rear edge; existing bolt positions retained.",
                         "kind": "timber"})
        mesh_rows.append({"id": name, "name": name, "mesh": _shape_mesh(new), "fabrication": metadata})
    assert len(seats) == 8 and len(contact_rows) == 2 and len(screens) == 4
    verify(pins)
    report = {
        "schema": "eoere_cleat_top_extension_geometry/v1", "candidate": base["candidate"],
        "revision": REVISION, "status": "REVISE_UNEVALUATED_GEOMETRY",
        "source_sha256": pins, "source_pin_count": len(pins),
        "proposal": {"path": str(PROPOSAL), "sha256": PROPOSAL_SHA},
        "parent_geometry": {"base": {"path": str(DOC / "occupied-adjusted-base-v3.json"), "sha256": sha(DOC / "occupied-adjusted-base-v3.json")},
                            "extra": {"path": str(DOC / "occupied-2026-adjustments-v3.json"), "sha256": sha(DOC / "occupied-2026-adjustments-v3.json")}},
        "changed_finished_solids": body_rows, "new_cleat_YZ_polygon_mm": raw_polygon,
        "base_side_rear_edge_YZ_mm": proposal["base_side_rear_edge_YZ_mm"],
        "front_height_addition_mm": proposal["front_height_addition_mm"],
        "maximum_blank_length_mm": proposal["maximum_blank_length_mm"],
        "nominal_bore_and_washer_support": seats, "nominal_side_face_contacts": contact_rows,
        "added_timber_collision_screen": screens,
        "axes": base["axes"], "screw_axes": base["screw_axes"],
        "base_100_axis_records_canonical_sha256": canonical(base["axes"]),
        "base_66_screw_records_canonical_sha256": canonical(base["screw_axes"]),
        "counts": {"base": base["counts"], "extra": extra["counts"]},
        "only_two_cleat_bodies_changed": True, "base_and_extra_harness_retained": True,
        "nominal_two_cleat_mass_delta_kg_at_500kg_m3": proposal["nominal_two_cleat_mass_delta_kg_at_500kg_m3"],
        "cadquery_version": cq.__version__, "execution": {"command": sys.argv, "native_solver": False},
        "mechanics_ready": False, "release": copy.deepcopy(base["release"]),
        "limits": ["Only four cached CAD bodies imported; two cleats grow and all other source bodies retain their bindings.",
                   "Saved CAD bounding-box screening concerns the added volume. Side-face contact is geometric, not a resistance or pressure result.",
                   "Complete joint resistance, revised actions, tooling, delivered parts and construction tolerances remain unevaluated.",
                   "The longer blank invalidates previous 289.7-mm cleat cut templates/offcut nesting; old packets remain frozen.",
                   "Optional 2026 grid remains unofficial and unconfirmed. No historical mechanical pass or physical release transfers."],
    }
    report_path = out / "geometry.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    parents = {}
    for layer, path in (("base", base_path), ("extra", extra_path)):
        encoded = Path(path).read_bytes()
        parents[layer] = {"url": Path(path).name, "sha256": ASSETS[path],
                          "decoded_sha256": hashlib.sha256(gzip.decompress(encoded)).hexdigest(),
                          "layout_sha256": scenes[path]["layout_report"]["sha256"]}
    patch = {"schema": "eoere_cleat_top_extension_patch/v1", "candidate": base["candidate"],
             "revision": REVISION, "status": report["status"], "parent_scenes": parents,
             "layout_report": {"path": str(DOC / "occupied-extended-cleats-v1.json"), "sha256": sha(report_path)},
             "counts": report["counts"], "replacements": mesh_rows,
             "triangle_topologies": _deduplicate_triangle_topologies(mesh_rows),
             "mechanics_ready": False, "release": copy.deepcopy(base["release"]),
             "only_two_cleat_bodies_changed": True, "base_and_extra_harness_retained": True,
             "analysis_pass_transferred": False}
    encoded = (json.dumps(patch, separators=(",", ":"), allow_nan=False) + "\n").encode()
    (out / "scene.json").write_bytes(encoded)
    (out / "scene.json.gz").write_bytes(gzip.compress(encoded, mtime=0))
    verify(pins)
    print(json.dumps({"report": str(report_path), "report_sha256": sha(report_path),
                      "scene_gzip_sha256": sha(out / "scene.json.gz"),
                      "scene_decoded_sha256": hashlib.sha256(encoded).hexdigest(),
                      "changed_cleats": len(body_rows), "source_pins": len(pins),
                      "finished_volume_mm3_each": [r["volume_mm3"] for r in body_rows],
                      "collision_screens": screens}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    build(parser.parse_args().out)
