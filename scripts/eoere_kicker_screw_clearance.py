"""Raise the two outer kicker screws 20 mm; preserve every bolt station.

Compose on the separately authenticated uniform-channel successor. Only two
panel holes and their screw solids change. Run with a fresh ignored --out.
"""

from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

DOC = Path(
    "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1"
)
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
PARENT = DOC / "occupied-uniform-channels-v1.json"
PARENT_SHA = "5726cad4203df4533b599c869e6a0e2e0599e27e874e6252cc34f34d5b36e6d4"
PLACEMENT = DOC / "occupied-extended-cleats-v1.json"
PLACEMENT_SHA = "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d"
REPORT = DOC / "occupied-kicker-clearance-v1.json"
REVISION = "eoere-raised-kicker-screws-v1"
TARGETS = {f"round_kicker_{side}_rim_2" for side in ("left", "right")}
THICKNESS, OLD_Z, NEW_Z = 18.25625, 192.0, 212.0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def build(out):
    assert not out.exists(), "preserve earlier outputs; choose a fresh --out"
    assert out.resolve().is_relative_to(
        (Path.cwd() / BASE / "kicker-clearance-v1").resolve()
    )
    assert sha(PLACEMENT) == PLACEMENT_SHA, "placement source changed"
    parent, original = read(PARENT), read(PLACEMENT)
    assert (
        parent["axes"] == original["axes"]
        and parent["screw_axes"] == original["screw_axes"]
    )
    pins = dict(parent["source_sha256"])

    def pin(path, expected=None):
        path = str(path)
        digest = sha(path)
        assert expected is None or digest == expected, "changed source: " + path
        assert path not in pins or pins[path] == digest, "conflicting source: " + path
        pins[path] = digest
        return digest

    def verify():
        for path, digest in pins.items():
            assert sha(path) == digest, "source drift: " + path

    pin(PARENT, PARENT_SHA)
    pin(PLACEMENT, PLACEMENT_SHA)
    pin(Path(__file__).resolve().relative_to(Path.cwd()))
    method_path = BASE / "cleat-corners-v1/lower_bolt_z_v2.py"
    bounds_path = BASE / "cleat-top-extension-v1/revision.py"
    pin(method_path)
    pin(bounds_path)
    method = module(method_path, "preserved_kicker_capsules")
    bounds_method = module(bounds_path, "preserved_kicker_bounds")
    assert method.known_answers() == 4
    screws = copy.deepcopy(original["screw_axes"])
    moves = []
    for old, new in zip(original["screw_axes"], screws, strict=True):
        if old["axis_id"] in TARGETS:
            assert old["origin_xyz_mm"][2] == OLD_Z
            new["origin_xyz_mm"][2] = NEW_Z
            moves.append(
                {
                    "axis_id": old["axis_id"],
                    "old_origin_xyz_mm": old["origin_xyz_mm"],
                    "new_origin_xyz_mm": new["origin_xyz_mm"],
                    "translation_xyz_mm": [0.0, 0.0, 20.0],
                }
            )
        else:
            assert old == new
    assert len(moves) == 2 and len(screws) == 66 and len(original["axes"]) == 100
    targets = [r for r in screws if r["axis_id"] in TARGETS]
    lower = [a for a in original["axes"] if a["id"].startswith("cleat_post_bolt_")]
    assert len(lower) == 4 and all(a["point_xyz_mm"][2] == 200 for a in lower)
    capsule = min(
        (
            method.pair(
                a,
                method.primitive(
                    s["axis_id"],
                    role,
                    s["origin_xyz_mm"],
                    s["direction_xyz"],
                    near,
                    far,
                    radius,
                ),
            )
            for bolt in lower
            for a in method.hardware({**bolt, "bore_diameter_mm": 11.1125}, bore=True)
            for s in targets
            for role, near, far, radius in (
                ("screw_body", 3.0, 63.5, 2.5),
                ("screw_head", 0.0, 3.0, 4.5),
            )
        ),
        key=lambda row: row["capsule_separation_lower_bound_mm"],
    )
    assert abs(capsule["capsule_separation_lower_bound_mm"] - 3.94375) < 1e-9
    verify()
    import cadquery as cq

    from scripts import thin_bolted_occupied as hardware
    from scripts.export_wood_joint_wj24_scene import (
        _deduplicate_triangle_topologies,
        _shape_mesh,
    )

    for name, loaded in tuple(sys.modules.items()):
        if name.startswith(("scripts.", "mini_moonboard.")) and getattr(
            loaded, "__file__", None
        ):
            pin(Path(loaded.__file__).resolve().relative_to(Path.cwd()))
    native = read(DOC.parent / "native-geometry-v4.json")
    aligned = read(DOC / "occupied-aligned-wire-v1.json")
    adjusted = read(DOC / "occupied-adjusted-base-v3.json")
    records = {r["id"]: r for r in native["parts"]}
    records.update(
        {
            r["id"]: r
            for r in aligned["changed_finished_solids"]
            + aligned["unchanged_finished_solids"]
        }
    )
    records.update({r["id"]: r for r in adjusted["changed_finished_solids"]})
    outlines = {r["member"]: r for r in native["panel_outline_parts"]}

    def load(row):
        pin(row["path"], row["sha256"])
        body = cq.Shape.importBrep(row["path"])
        assert body.isValid() and len(body.Solids()) == 1
        return body

    out.mkdir(parents=True)
    saved, replacements, support = [], [], []
    before = {r["axis_id"]: r for r in original["screw_axes"]}
    for row in targets:
        old = before[row["axis_id"]]
        panel = load(records[row["panel"]])
        outline = load(outlines[row["panel"]])
        post = load(records[row["receiver"]])
        p, d = cq.Vector(*old["origin_xyz_mm"]), cq.Vector(*old["direction_xyz"])
        cutter = (
            cq.Solid.makeCylinder(2.5, THICKNESS + 2, p - d, d)
            .fuse(hardware.screw_shapes(old)[0][1])
            .clean()
        )
        plug = outline.intersect(cutter)
        revised = panel.fuse(plug).clean().cut(cutter.translate((0, 0, 20))).clean()
        assert abs(revised.Volume() - panel.Volume()) < 0.01
        assert revised.intersect(cutter).Volume() > plug.Volume() - 0.01
        assert revised.intersect(cutter.translate((0, 0, 20))).Volume() < 1e-7
        point = cq.Vector(*row["origin_xyz_mm"])
        probe = cq.Solid.makeCylinder(2.5, 63.5 - THICKNESS, point + d * THICKNESS, d)
        fraction = probe.intersect(post).Volume() / probe.Volume()
        assert fraction > 0.999999
        pb, wb = outline.BoundingBox(), post.BoundingBox()
        support.append(
            {
                "axis_id": row["axis_id"],
                "panel": row["panel"],
                "receiver": row["receiver"],
                "modeled_body_backing_fraction": fraction,
                "modeled_wood_penetration_mm": 63.5 - THICKNESS,
                "panel_top_axis_distance_mm": pb.zmax - NEW_Z,
                "post_top_axis_distance_mm": wb.zmax - NEW_Z,
                "post_top_body_edge_distance_mm": wb.zmax - NEW_Z - 2.5,
                "panel_and_post_side_axis_distance_mm": min(
                    point.x - wb.xmin, wb.xmax - point.x
                ),
                "edge_distance_strength_qualification": False,
                "actual": None,
            }
        )
        head, body = hardware.screw_shapes(row)
        for name, kind, shape in (
            (row["panel"], "panel", revised),
            ("fastener_" + row["axis_id"], "screw", head[1].fuse(body[1]).clean()),
        ):
            assert shape.isValid() and len(shape.Solids()) == 1
            path = out / (name + ".brep")
            assert shape.exportBrep(str(path))
            restored = cq.Shape.importBrep(str(path))
            assert restored.isValid() and abs(restored.Volume() - shape.Volume()) < 1e-7
            mesh = _shape_mesh(restored)
            saved.append(
                {
                    "id": name,
                    "kind": kind,
                    "path": str(path),
                    "sha256": sha(path),
                    "bytes": path.stat().st_size,
                    "volume_mm3": restored.Volume(),
                    "bounds_xyz_mm": mesh["bounds_xyz_mm"],
                }
            )
            replacements.append(
                {
                    "id": name,
                    "name": name,
                    "mesh": mesh,
                    "fabrication": {
                        "kind": kind,
                        "kicker_clearance_revision": REVISION,
                        "description": "Upper outer kicker screw and panel hole raised 20 mm to Z212",
                    },
                }
            )

    scene_paths = [
        "site/eoere-bottom-rail-scene.json.gz",
        "site/eoere-cleat-trim-scene.json",
        "site/eoere-aligned-wire-scene.json.gz",
        "site/eoere-adjusted-base-v3-scene.json.gz",
        "site/eoere-cleat-extension-scene.json.gz",
    ]
    scenes = []
    for path in scene_paths:
        pin(path)
        scenes.append(bounds_method.asset(path))
    extra_path, parent_scene = (
        "site/eoere-2026-adjustments-v3-scene.json.gz",
        "site/eoere-uniform-channels-scene.json.gz",
    )
    pin(extra_path)
    pin(parent_scene)
    channel_patch = bounds_method.asset(parent_scene)
    assert channel_patch["layout_report"]["sha256"] == sha(PARENT)
    screens = []
    for variant, count in (("base", 1021), ("extra", 1380)):
        layers = (
            scenes
            if variant == "base"
            else scenes[:-1] + [bounds_method.asset(extra_path), scenes[-1]]
        )
        layers = [
            *layers,
            {
                "replacements": channel_patch["common_replacements"]
                + channel_patch[f"{variant}_replacements"]
            },
        ]
        bank = bounds_method.compose_bounds(native, layers)
        assert len(bank) == count
        bank.update(
            {r["id"]: {"kind": r["kind"], "bounds": r["bounds_xyz_mm"]} for r in saved}
        )
        nearest = None
        comparisons = 0
        for screw in targets:
            name = "fastener_" + screw["axis_id"]
            bounds = bank[name]["bounds"]
            for other, record in bank.items():
                if other in (name, screw["panel"], screw["receiver"]):
                    continue
                gap = max(
                    max(
                        record["bounds"][i] - bounds[i + 1],
                        bounds[i] - record["bounds"][i + 1],
                    )
                    for i in (0, 2, 4)
                )
                assert gap > 0, (variant, name, other, gap)
                comparisons += 1
                if nearest is None or gap < nearest["separating_axis_gap_mm"]:
                    nearest = {
                        "screw": name,
                        "other": other,
                        "separating_axis_gap_mm": gap,
                    }
        screens.append(
            {
                "variant": variant,
                "part_count": count,
                "positive_AABB_comparisons": comparisons,
                "minimum": nearest,
                "method": "Authenticated CAD bounding boxes; positive separating-axis gaps prove modeled-body separation. Intended panel and post excluded.",
            }
        )

    csv_source = (
        DOC / "shop-assembly-v1/extended-cleat-followup-v1/panel-screw-datums.csv"
    )
    pin(csv_source)
    with csv_source.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields, datums = reader.fieldnames, list(reader)
    # The datum table is a complete 66-row successor; observations stay blank.
    for row in datums:
        if row["axis_id"] in TARGETS:
            for key in (
                "front_axis_origin_z_mm",
                "origin_in_panel_u_mm",
                "origin_in_receiver_l_mm",
            ):
                assert float(row[key]) == OLD_Z
                row[key] = str(NEW_Z)
            row["source"] = "kicker-clearance#/screw_axes/" + str(
                next(i for i, s in enumerate(screws) if s["axis_id"] == row["axis_id"])
            )
    with (out / "panel-screw-datums.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(datums)
    verify()
    report = {
        "schema": "eoere_kicker_screw_clearance_geometry/v1",
        "candidate": original["candidate"],
        "revision": REVISION,
        "status": "REVISE_UNEVALUATED_GEOMETRY",
        "source_sha256": pins,
        "parent_geometry": {"path": str(PARENT), "sha256": sha(PARENT)},
        "placement_source": {"path": str(PLACEMENT), "sha256": PLACEMENT_SHA},
        "axes": original["axes"],
        "screw_axes": screws,
        "moved_screw_axes": moves,
        "unchanged_100_bolt_axes_canonical_sha256": canonical(original["axes"]),
        "unchanged_screw_count": 64,
        "counts": original["counts"],
        "changed_finished_solids": saved,
        "screw_support": support,
        "maximum_bore_clearance": capsule,
        "known_answer_fixtures": 4,
        "unrelated_body_screens": screens,
        "panel_screw_datums": {
            "path": str(out / "panel-screw-datums.csv"),
            "sha256": sha(out / "panel-screw-datums.csv"),
        },
        "cadquery_version": cq.__version__,
        "execution": {"command": sys.argv, "native_solver": False},
        "mechanics_ready": False,
        "analysis_pass_transferred": False,
        "release": original["release"],
        "limits": [
            "Owner-directed geometric clearance change only; no joint, withdrawal, splitting or panel-strength acceptance.",
            "Full modeled screw-body backing is geometric occupancy, not Hillman resistance or installation qualification.",
            "All actual observations remain blank. Accumulated placement/size errors must remain below the 3.94375-mm geometric gap.",
            "The old Z192 holes are removed in the new CAD panels; this is not a physical hole-plugging instruction.",
            "Preserved Z200/Z180 numerical and shop packets retain their original sources; no result transfers to the changed screw layout.",
        ],
    }
    report_path = out / "geometry.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    raw_parent = Path(parent_scene).read_bytes()
    patch = {
        "schema": "eoere_kicker_screw_clearance_patch/v1",
        "candidate": original["candidate"],
        "revision": REVISION,
        "status": report["status"],
        "layout_report": {"path": str(REPORT), "sha256": sha(report_path)},
        "parent_scene": {
            "url": Path(parent_scene).name,
            "sha256": sha(parent_scene),
            "decoded_sha256": hashlib.sha256(gzip.decompress(raw_parent)).hexdigest(),
            "layout_sha256": sha(PARENT),
        },
        "counts": report["counts"],
        "replacements": replacements,
        "triangle_topologies": _deduplicate_triangle_topologies(replacements),
        "moved_screw_axes": moves,
        "mechanics_ready": False,
        "analysis_pass_transferred": False,
        "release": original["release"],
    }
    encoded = (
        json.dumps(patch, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()
    (out / "scene.json.gz").write_bytes(gzip.compress(encoded, mtime=0))
    verify()
    print(
        json.dumps(
            {
                "report": str(report_path),
                "report_sha256": sha(report_path),
                "compressed_sha256": sha(out / "scene.json.gz"),
                "decoded_sha256": hashlib.sha256(encoded).hexdigest(),
                "moves": moves,
                "screens": screens,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    build(parser.parse_args().out)
