"""Apply the selected purchase lengths and eight spacers on retained axes.

Only metal occupancy changes. Six shared templates replace 32 shafts, translate
eight existing nuts and add eight annular spacers. No timber, panel or screw is
rebuilt, and no mechanics is executed. Preserve all previous receipts and scenes.
"""

from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import io
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/selected-hardware-v1")
REPORT = DOC / "occupied-selected-hardware-v1.json"
REVISION = "eoere-selected-purchase-hardware-v1"
KEYS = {"base": "eoere-selected-hardware-frame-development",
        "extra": "eoere-selected-hardware-grid-development"}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def selected_rows(raw, axes):
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    require(len(rows) == len(axes) == 100 and {r["axis_id"] for r in rows} == set(axes),
            "100 exact selected axes required")
    fields = ("selected_underhead_length_mm", "selected_diameter_mm", "nut_side_spacer_mm",
              "minimum_length_mm", "maximum_grip_gaging_mm", "minimum_body_mm",
              "minimum_two_pitch_margin_mm", "minimum_nut_seating_margin_mm",
              "minimum_body_to_nominated_target_margin_mm", "selected_tip_delta_mm")
    result = {}
    for original in rows:
        row = {**{k: float(original[k]) for k in fields},
               **{k: original[k] for k in ("axis_id", "selected_product", "selected_product_url",
                   "selected_bolt_grade", "selected_nut_SKU", "selected_washer_SKU",
                   "selected_spacer_SKU", "selected_recipe")}}
        axis = axes[row["axis_id"]]
        require(all(math.isfinite(row[k]) for k in fields), "finite catalog dimensions required")
        require(abs(row["selected_diameter_mm"] - axis["diameter_mm"]) < 1e-9,
                "selected diameter changes an axis")
        require(abs(row["selected_underhead_length_mm"] - axis["nominal_under_head_length_mm"]
                    - row["selected_tip_delta_mm"]) < 1e-8, "length delta differs")
        require(row["selected_tip_delta_mm"] >= 0, "shorter shafts are outside this selection")
        require(all(row[k] > 0 for k in ("minimum_two_pitch_margin_mm",
                    "minimum_nut_seating_margin_mm", "minimum_body_to_nominated_target_margin_mm")),
                "selected catalog comparison failed")
        require(row["nut_side_spacer_mm"] in (0., 12.7), "single half-inch spacer required")
        require(row["axis_id"] not in result, "duplicate selected axis")
        result[row["axis_id"]] = row
    require(sum(r["selected_tip_delta_mm"] > 0 for r in result.values()) == 32,
            "32 longer shafts required")
    require(sum(r["nut_side_spacer_mm"] > 0 for r in result.values()) == 8,
            "eight spacer stacks required")
    return result


def build(inputs_path, expected, out):
    require(Path.cwd() == ROOT, "run from the repository root")
    require(sha(inputs_path) == expected, "frozen input digest differs")
    inputs = json.loads(inputs_path.read_bytes())
    require(inputs["schema"] == "eoere_selected_hardware_inputs/v1"
            and inputs["revision"] == REVISION, "selected hardware input scope differs")
    require(out.resolve().is_relative_to(ROOT / BASE), "ignored selected-hardware output required")
    require(not out.exists(), "preserve existing attempts; choose a fresh output directory")
    pins = {str(inputs_path.resolve().relative_to(ROOT)): expected,
            str(Path(__file__).resolve().relative_to(ROOT)): sha(__file__)}

    def pin(path, digest=None):
        path = str(path)
        observed = sha(ROOT / path)
        require(digest is None or observed == digest, "changed source: " + path)
        require(path not in pins or pins[path] == observed, "conflicting source: " + path)
        pins[path] = observed
        return ROOT / path

    def read(ref):
        return json.loads(pin(ref["path"], ref["sha256"]).read_bytes())

    def verify():
        for name, digest in pins.items():
            require(sha(ROOT / name) == digest, "source drift: " + name)

    base, extra = (read(inputs["parents"][v]) for v in ("base", "extra"))
    require(base["axes"] == extra["axes"] and base["screw_axes"] == extra["screw_axes"],
            "parent axis sets differ")
    require(len(base["screw_axes"]) == 66, "66 Hillman axes required")
    for parent in (base, extra):
        for path, digest in parent["source_sha256"].items():
            pin(path, digest)
    shop = read(inputs["shop_result"])
    require(shop["revision"] == base["revision"] and shop["counts"]["bolts"] == 100,
            "shop parent geometry differs")
    audit = read(inputs["shop_source_union"])
    require(audit["union_pin_count"] == 1230 and audit["all_saved_output_bytes_equal"],
            "preceding shop replay audit required")
    for path, digest in audit["source_sha256"].items():
        pin(path, digest)
    raw = pin(inputs["hardware_selection"]["path"], inputs["hardware_selection"]["sha256"]).read_bytes()
    require(inputs["hardware_selection"]["sha256"] == shop["files"]["hardware-selection.csv"]["sha256"],
            "hardware table differs from issued shop result")
    axes = {row["id"]: row for row in base["axes"]}
    selections = selected_rows(raw, axes)
    for variant, ref in inputs["parent_scenes"].items():
        decoded = gzip.decompress(pin(ref["path"], ref["sha256"]).read_bytes())
        require(hashlib.sha256(decoded).hexdigest() == ref["decoded_sha256"],
                "decoded parent scene differs")
        require(json.loads(decoded)["layout_report"] == inputs["parents"][variant],
                "parent scene geometry binding differs")
    for ref in inputs["method_sources"]:
        pin(ref["path"], ref["sha256"])
    verify()
    out.mkdir(parents=True)
    (out / "producer-snapshot.py").write_bytes(Path(__file__).read_bytes())
    (out / "inputs-snapshot.json").write_bytes(inputs_path.read_bytes())
    print("Authenticated selected stacks and both retained parent frames", flush=True)

    import cadquery as cq

    from scripts import eoere_2026_adjustments as shared
    from scripts import thin_bolted_occupied as hardware
    from scripts.export_wood_joint_wj24_scene import (
        _deduplicate_triangle_topologies,
        _shape_mesh,
    )

    for name, loaded in tuple(sys.modules.items()):
        if name.startswith(("scripts.", "mini_moonboard.")) and getattr(loaded, "__file__", None):
            pin(Path(loaded.__file__).resolve().relative_to(ROOT))

    def bounds(shape):
        b = shape.BoundingBox()
        return [getattr(b, axis + end) for axis in "xyz" for end in ("min", "max")]

    coupon = cq.Solid.makeCylinder(2., 3.)
    require(abs(coupon.Volume() - 12 * math.pi) < 1e-9, "cylinder known answer differs")
    annulus = cq.Solid.makeCylinder(2., 3.).cut(cq.Solid.makeCylinder(1., 3.))
    require(abs(annulus.Volume() - 9 * math.pi) < 1e-9, "annulus known answer differs")
    templates, template_shapes, template_sources = [], {}, []

    def template(identity, shape, expected_volume):
        require(shape.isValid() and len(shape.Solids()) == 1, "single valid template required")
        require(abs(shape.Volume() - expected_volume) < 1e-6, "template volume differs")
        path = out / (identity + ".brep")
        require(shape.exportBrep(str(path)), "template export failed")
        restored = cq.Shape.importBrep(str(path))
        require(restored.isValid() and abs(restored.Volume() - expected_volume) < 1e-6,
                "template round trip differs")
        row = {"id": identity, "path": str(path.relative_to(ROOT)), "sha256": sha(path),
               "bytes": path.stat().st_size, "volume_mm3": restored.Volume(),
               "bounds_xyz_mm": bounds(restored)}
        template_sources.append(row)
        templates.append({"id": identity, "mesh": _shape_mesh(restored),
                          "source_brep_sha256": row["sha256"]})
        template_shapes[identity] = restored

    kinds = sorted({(r["selected_diameter_mm"], r["selected_underhead_length_mm"])
                    for r in selections.values() if r["selected_tip_delta_mm"] > 0})
    kind_ids = {}
    for index, (diameter, length) in enumerate(kinds):
        identity = f"selected_shaft_{index + 1}"
        kind_ids[diameter, length] = identity
        template(identity, cq.Solid.makeCylinder(diameter / 2, length),
                 math.pi * diameter**2 * length / 4)
    template("selected_spacer", cq.Solid.makeCylinder(19.05 / 2, 12.7).cut(
        cq.Solid.makeCylinder(10.31875 / 2, 12.7)),
        math.pi * (19.05**2 - 10.31875**2) * 12.7 / 4)
    require(len(templates) == 6, "five shaft templates and one spacer required")

    saved, replacements, translations, additions = [], [], [], []

    def save(name, role, shape, axis_id):
        require(shape.isValid() and len(shape.Solids()) == 1, "valid occupied metal required")
        path = out / (name + ".brep")
        require(shape.exportBrep(str(path)), "occupied export failed")
        restored = cq.Shape.importBrep(str(path))
        require(restored.isValid() and abs(restored.Volume() - shape.Volume()) < 1e-6,
                "occupied round trip differs")
        row = {"id": name, "kind": "bolt", "role": role, "axis_id": axis_id,
               "path": str(path.relative_to(ROOT)), "sha256": sha(path),
               "bytes": path.stat().st_size, "volume_mm3": restored.Volume(),
               "bounds_xyz_mm": bounds(restored)}
        saved.append(row)
        return row

    for name, row in selections.items():
        axis = axes[name]
        point, direction = cq.Vector(*axis["point_xyz_mm"]), cq.Vector(*axis["direction_xyz"])
        direction = direction.normalized()
        washer = axis["hardware_scenario"]["washer_thickness_mm"]
        length = row["selected_underhead_length_mm"]
        origin = point - direction * (axis["before_plate_mm"] + washer)
        metadata = {"kind": "bolt", "connection_name": name,
                    "selected_hardware_revision": REVISION}
        if row["selected_tip_delta_mm"] > 0:
            identity = kind_ids[row["selected_diameter_mm"], length]
            plane = cq.Plane(origin=origin, normal=direction)
            shape = template_shapes[identity].moved(plane.location)
            rec = save(name + "_shaft", "shaft", shape, name)
            # Check the full new shaft and added volume independently in world space.
            old = cq.Solid.makeCylinder(axis["diameter_mm"] / 2,
                                       axis["nominal_under_head_length_mm"], origin, direction)
            require(old.cut(shape).Volume() < 1e-6, "new shaft removes old occupied volume")
            require(abs(shape.Volume() - old.Volume() - math.pi * axis["diameter_mm"]**2
                        * row["selected_tip_delta_mm"] / 4) < 1e-6, "shaft increment differs")
            replacements.append({"id": rec["id"], "name": rec["id"], "template_id": identity,
                                 "transform": shared.matrix(plane), "source_brep_sha256": rec["sha256"],
                                 "fabrication": {**metadata, "hardware_role": "shaft"}})
        spacer = row["nut_side_spacer_mm"]
        if spacer:
            offset = axis["grip_mm"] + axis["after_plate_mm"] + washer
            plane = cq.Plane(origin=point + direction * offset, normal=direction)
            shape = template_shapes["selected_spacer"].moved(plane.location)
            rec = save(name + "_spacer", "spacer", shape, name)
            additions.append({"id": rec["id"], "name": rec["id"], "template_id": "selected_spacer",
                              "transform": shared.matrix(plane), "source_brep_sha256": rec["sha256"],
                              "fabrication": {**metadata, "hardware_role": "spacer"}})
            original_axis = copy.deepcopy(axis)
            nut = dict(hardware.local_hardware(original_axis))["nut"]
            require(abs(original_axis["nominal_under_head_length_mm"]
                        - axis["nominal_under_head_length_mm"]) < 1e-8, "old hardware recipe differs")
            delta = direction * spacer
            nut = nut.moved(cq.Plane(origin=point, normal=direction).location).translate(delta)
            rec = save(name + "_nut", "nut", nut, name)
            translations.append({"name": rec["id"], "translation_xyz_mm": list(delta.toTuple()),
                                 "source_brep_sha256": rec["sha256"],
                                 "fabrication": {**metadata, "hardware_role": "nut"}})

    require((len(replacements), len(translations), len(additions), len(saved)) == (32, 8, 8, 48),
            "selected hardware change census differs")
    topology = _deduplicate_triangle_topologies(templates)
    verify()
    source_map = encoded(pins)
    (out / "source-pins.json").write_bytes(source_map)
    direct_paths = {str(inputs_path.relative_to(ROOT)), str(Path(__file__).resolve().relative_to(ROOT))}
    for group in ("parents", "parent_scenes"):
        direct_paths.update(ref["path"] for ref in inputs[group].values())
    direct_paths.update(inputs[k]["path"] for k in ("shop_result", "hardware_selection", "shop_source_union"))
    direct_paths.update(ref["path"] for ref in inputs["method_sources"])
    release = {"fabrication": False, "climbing": False, "observed_parts": False,
               "complete_joint_acceptance": False, "response_pass_transferred": False,
               "native_analysis": False}
    report = {"schema": "eoere_selected_hardware_geometry/v1", "candidate": base["candidate"],
              "revision": REVISION, "status": "REVISE_UNEVALUATED_HARDWARE_GEOMETRY",
              "parents": inputs["parents"], "wood_screw_revision": base["revision"],
              "retained_axis_geometry": inputs["parents"]["base"],
              "axes_canonical_sha256": canonical(base["axes"]),
              "screw_axes_canonical_sha256": canonical(base["screw_axes"]),
              "axis_records_preserved_as_parent_geometry": True,
              "selected_hardware_overrides_parent_lengths": True,
              "hardware_selection": inputs["hardware_selection"],
              "shop_result": inputs["shop_result"], "selected_stacks": list(selections.values()),
              "template_solids": template_sources, "changed_finished_solids": saved,
              "counts": {"base": 1029, "extra": 1424, "physical_bolt_axes": 100,
                         "longer_shafts": 32, "translated_nuts": 8, "added_spacers": 8,
                         "timbers": 22, "panels": 6, "angles": 22, "Hillman_screws": 66},
              "known_answer_fixtures": 2, "release": release,
              "mechanics_ready": False, "analysis_pass_transferred": False,
              "source_pin_count": len(pins), "source_map_canonical_sha256": canonical(pins),
              "source_map": {"path": str((out / "source-pins.json").relative_to(ROOT)),
                             "sha256": hashlib.sha256(source_map).hexdigest(), "bytes": len(source_map)},
              "direct_source_sha256": {p: pins[p] for p in sorted(direct_paths)},
              "inputs_sha256": expected,
              "execution": {"command": f"PYTHONPATH=. .venv/bin/python -B scripts/eoere_selected_hardware.py --inputs {inputs_path.relative_to(ROOT)} --inputs-sha256 {expected} --out {out.relative_to(ROOT)}",
                            "python": sys.version, "cadquery": cq.__version__},
              "limits": ["Full nominal-diameter cylinders are occupied envelopes, not delivered thread/runout shapes.",
                         "No timber, panel, screw, axis or optional-grid geometry changes.",
                         "Unchanged parts reuse preceding meshes and source geometry.",
                         "Catalog windows and delivered fit, contact and resistance remain separate.",
                         "Physical observations, new frame response and complete-joint acceptance remain absent."]}
    report_bytes = encoded(report)
    report_sha = hashlib.sha256(report_bytes).hexdigest()
    scene = {"schema": "eoere_selected_hardware_patch/v1", "candidate": base["candidate"],
             "revision": REVISION, "status": report["status"],
             "layout_report": {"path": str(REPORT), "sha256": report_sha},
             "parents": {v: {**ref, "url": Path(ref["path"]).name}
                         for v, ref in inputs["parent_scenes"].items()},
             "keys": KEYS, "counts": report["counts"], "release": release,
             "mechanics_ready": False, "analysis_pass_transferred": False,
             "selected_stacks": list(selections.values()), "templates": templates,
             "replacements": replacements, "translations": translations, "additions": additions,
             "triangle_topologies": topology}
    scene_bytes = encoded(scene)
    compressed = gzip.compress(scene_bytes, compresslevel=9, mtime=0)
    (out / "result.json").write_bytes(report_bytes)
    (out / "scene.json.gz").write_bytes(compressed)
    production = {"report_sha256": report_sha, "scene_sha256": hashlib.sha256(compressed).hexdigest(),
                  "decoded_sha256": hashlib.sha256(scene_bytes).hexdigest(),
                  "source_pin_count": len(pins), "source_bytes_unchanged": True,
                  "changed_parts": len(saved), "compressed_scene_bytes": len(compressed)}
    (out / "production.json").write_bytes(encoded(production))
    print(json.dumps(production, sort_keys=True), flush=True)
    return report, scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    build(args.inputs.resolve(), args.inputs_sha256, args.out.resolve())


if __name__ == "__main__":
    main()
