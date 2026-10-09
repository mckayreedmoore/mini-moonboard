"""Add the owner's horizontal midpoint grid to cached existing-frame geometry.

The adjusted base moves the right principal and its connections coherently.
The unofficial midpoint grid and its additional cuts are a separate layer.
Run: PYTHONPATH=. .venv/bin/python -B scripts/eoere_2026_adjustments.py --out fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/2026-adjustments-v1
"""

import argparse
import copy
import gzip
import hashlib
import json
import math
import sys
from itertools import pairwise
from pathlib import Path

import cadquery as cq

from mini_moonboard import hold_tnut_reinforcement as tnuts
from mini_moonboard import no_shoes_frame, panel_grid_v2
from scripts import eoere_bolted_candidate as fitting
from scripts import hl35_nominal_service_candidate as services
from scripts import thin_bolted_layout_revision as routing
from scripts import thin_bolted_occupied as hardware
from scripts import wood_joint_midpoint_clearance as midpoint
from scripts.export_wood_joint_wj24_scene import (
    _deduplicate_triangle_topologies,
    _shape_mesh,
)
from scripts.hl35_candidate import overlaps

DOC = Path(
    "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1"
)
PARENT_REPORT = DOC / "occupied-aligned-wire-v1.json"
PARENT_SCENE = Path("site/eoere-aligned-wire-scene.json.gz")
PARENT_SHA = "dbb6c2cdf65b4473b71a38faa233dd7c6f43bb02bb07ad6a702943c343947ee4"
PARENT_DECODED_SHA = "367ddf67b376597e9ca906bb1faa904cbbfa16c98ddc86c879548a6eff637573"
PARENT_LAYOUT_SHA = "2b31d82a41cd6eb1c80e3ed84b2d0cae428fdc575b1c8c6fa27d7c3e6f0276c5"
REVISION = "eoere-2026-horizontal-midpoint-grid-v3"
KEY = "eoere-new-2026-adjustments"
THICKNESS = 18.25625
N = no_shoes_frame.b.normal().normalized()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def panel_at(x, s):
    return f"main_{'lower' if s < panel_grid_v2.PANEL_HEIGHT_MM else 'upper'}_{'left' if x < no_shoes_frame.b.HALF else 'right'}"


def grid():
    holds, lights = panel_grid_v2.main_tnut_datums(), panel_grid_v2.main_led_datums()
    rows = []
    for column in "ABCDEFGHIJ":
        neighbor = chr(ord(column) + 1)
        for row in range(1, 13):
            first, second = f"{column}{row}", f"{neighbor}{row}"
            x, s = [(a + b) / 2 for a, b in zip(holds[first], holds[second])]
            lx, ls = [(a + b) / 2 for a, b in zip(lights[first], lights[second])]
            rows.append(
                {
                    "id": f"{column}{neighbor}{row}",
                    "column": column,
                    "row": row,
                    "endpoints": [first, second],
                    "tnut_x_s_mm": [x, s],
                    "LED_x_s_mm": [lx, ls],
                    "tnut_panel": panel_at(x, s),
                    "LED_panel": panel_at(lx, ls),
                }
            )
    assert len(rows) == 120 and len({r["id"] for r in rows}) == 120
    return rows


def matrix(plane):
    transform = plane.location.wrapped.Transformation()
    return [
        transform.Value(r + 1, c + 1) if r < 3 else float(c == 3)
        for c in range(4)
        for r in range(4)
    ]


def pair_hits(first, second):
    # Cache bounding boxes once; these hundreds of detailed bodies otherwise
    # repeat expensive OCCT bounds queries for every unrelated pair.
    a = [(name, role, shape, midpoint._bbox(shape)) for name, role, shape in first]
    b = [(name, role, shape, midpoint._bbox(shape)) for name, role, shape in second]
    return [
        {
            "first": name,
            "first_role": role,
            "second": other,
            "second_role": other_role,
            "intersection_mm3": round(volume, 6),
        }
        for name, role, shape, bounds in a
        for other, other_role, body, other_bounds in b
        if midpoint._overlap(bounds, other_bounds)
        and (volume := max(0.0, shape.intersect(body).Volume())) > 0.01
    ]


def retained_services(source, native, load, pins):
    """Load every retained body; canonical changed wire dependencies are mandatory."""
    native_services = {
        r["id"]: r for r in native["parts"] if r["kind"] in ("tnut", "light", "wire")
    }
    existing = [(name, row["kind"], load(row)) for name, row in native_services.items()]
    manifest_path = (
        Path.cwd().parent
        / "mini-moonboard-cleanup-backups-2026-10-08/eoere-aligned-wire-cutouts-v1.tar.gz.manifest.json"
    )
    expected_manifest = (
        "688acf55c2884086ff14352d6d5ac6377b8f6bcebeb29c0e8275e4ffcdf3a15c"
    )
    assert sha(manifest_path) == expected_manifest, (
        "authenticated aligned-wire archive manifest required"
    )
    pins[str(manifest_path)] = expected_manifest
    archived = {row["path"]: row for row in read(manifest_path)["files"]}
    aligned_dir = Path(
        "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/aligned-wire-cutouts-v1/cad-v1"
    )
    required_paths = {
        path
        for path in archived
        if path.startswith(str(aligned_dir) + "/wire_") and path.endswith(".brep")
    }
    assert len(required_paths) == 30
    required = {Path(path).stem for path in required_paths}
    assert required.issubset({r["name"] for r in source["wire_proposals"]})
    for index, (name, kind, shape) in enumerate(existing):
        if kind != "wire" or name not in required:
            continue
        path = aligned_dir / (name + ".brep")
        record = archived[str(path)]
        assert sha(path) == record["sha256"], (
            "aligned-wire dependency missing or changed: " + str(path)
        )
        pins[str(path)] = record["sha256"]
        existing[index] = (name, kind, cq.Shape.importBrep(str(path)))
    assert len(existing) == 405
    return existing


def canonical_interval_shift(direction, translation):
    """Attachment intervals project onto a unit direction with first nonzero positive."""
    norm = math.sqrt(sum(v * v for v in direction))
    assert norm > 0 and math.isfinite(norm)
    sign = 1 if next(v for v in direction if abs(v) > 1e-8) > 0 else -1
    return sign * sum(a * b for a, b in zip(direction, translation)) / norm


def adjusted_base(source, raised, native, wood, panels, load, out, pins):
    """Rebuild only affected stock, connections and right-panel screw bores."""
    shift = cq.Vector(-39.2, 0, 0)
    target = "base_principal_center_right"
    duties = {
        a["duty_id"]
        for row in source["axes"]
        if target in row["receivers"]
        for a in row["attachments"]
    }
    # Shared shafts require every attached factory angle to move coherently.
    while True:
        closure = duties | {
            a["duty_id"]
            for row in source["axes"]
            if any(a["duty_id"] in duties for a in row["attachments"])
            for a in row["attachments"]
        }
        if closure == duties:
            break
        duties = closure
    shifted_members = {target, "base_post_center_right"}
    updated = copy.deepcopy(source)
    moved_axes = []
    for axis in updated["axes"]:
        if any(a["duty_id"] in duties for a in axis["attachments"]):
            moved_axes.append(axis["id"])
            axis["point_xyz_mm"][0] -= 39.2
            for attachment in axis["attachments"]:
                attachment["point"][0] -= 39.2
                delta = canonical_interval_shift(
                    attachment["direction"], shift.toTuple()
                )
                attachment["interval_mm"] = [
                    v + delta for v in attachment["interval_mm"]
                ]
    moved_screws = []
    for row in updated["screw_axes"]:
        if row["receiver"] in shifted_members:
            moved_screws.append(row["axis_id"])
            row["origin_xyz_mm"][0] -= 39.2
    assert len(duties) == 6 and len(moved_axes) == 22 and len(moved_screws) == 10
    raw_records = {r["member"]: r for r in native["raw_parts"]}
    raw = {
        name: load(raw_records[name])
        for name in (target, "base_post_center_right", "base_header", "base_rail_top")
    }
    for name in shifted_members:
        raw[name] = raw[name].translate(shift)
    plan_path = Path(source["plan"]["path"])
    assert sha(plan_path) == source["plan"]["sha256"]
    pins[str(plan_path)] = sha(plan_path)
    extended = []
    for row in read(plan_path)["rails"]:
        if row["id"].endswith("_right"):
            name = row["id"]
            body = load(row["raw"]).translate(tuple(row["raw_translation_xyz_mm"]))
            raw[name] = body.fuse(body.translate(shift)).clean()
            extended.append(name)
    assert len(raw) == 7 and len(extended) == 3
    routes = {r["name"]: r for r in source["wire_proposals"]}
    service_cutters = []
    # Relocation can intersect services that never needed cuts in the parent.
    # Discover cuts from every authenticated retained route, not prior cut membership.
    for name, record in sorted(routes.items()):
        service_cutters.append(
            (
                name,
                "wire",
                routing.front_open_cutter(
                    record["route_local_mm"], record["placement_xyz_mm"], 6.35
                ),
            )
        )
    serviced, cuts = services.cut_services(raw, set(raw), service_cutters)
    axes = [
        {
            **a,
            "point": cq.Vector(*a["point_xyz_mm"]),
            "direction": cq.Vector(*a["direction_xyz"]),
            "receivers": [name for name in a["receivers"] if name in raw],
        }
        for a in updated["axes"]
        if any(name in raw for name in a["receivers"])
    ]
    finished = hardware.bore_wood(serviced, axes)
    contacts = []
    for name in extended + ["base_header", "base_rail_top"]:
        distance = finished[target].distance(finished[name])
        volume = overlaps(finished[target], finished[name])
        assert distance < 1e-5 and volume < 0.01, (name, distance, volume)
        contacts.append(
            {"member": name, "distance_mm": distance, "intersection_mm3": volume}
        )
    distance = finished["base_post_center_right"].distance(finished["base_header"])
    assert distance < 1e-5
    contacts.append(
        {
            "member": "base_post_center_right",
            "receiver": "base_header",
            "distance_mm": distance,
            "intersection_mm3": overlaps(
                finished["base_post_center_right"], finished["base_header"]
            ),
        }
    )
    updated_panels = dict(panels)
    changed_panels = {
        r["panel"] for r in updated["screw_axes"] if r["axis_id"] in moved_screws
    }
    for name in sorted(changed_panels):
        outline = next(r for r in native["panel_outline_parts"] if r["member"] == name)
        finished_panel = panels[name]
        for old in source["screw_axes"]:
            if old["panel"] != name or old["axis_id"] not in moved_screws:
                continue
            point, direction = (
                cq.Vector(*old["origin_xyz_mm"]),
                cq.Vector(*old["direction_xyz"]),
            )
            cutter = (
                cq.Solid.makeCylinder(2.5, THICKNESS + 2, point - direction, direction)
                .fuse(hardware.screw_shapes(old)[0][1])
                .clean()
            )
            plug = load(outline).intersect(cutter)
            finished_panel = (
                finished_panel.fuse(plug).clean().cut(cutter.translate(shift)).clean()
            )
        updated_panels[name] = finished_panel
        assert finished_panel.isValid() and len(finished_panel.Solids()) == 1
        assert abs(finished_panel.Volume() - panels[name].Volume()) < 0.01
    adjusted_wood = {**wood, **finished}
    screw_support = []
    for row in updated["screw_axes"]:
        if row["receiver"] not in finished:
            continue
        p, d = cq.Vector(*row["origin_xyz_mm"]), cq.Vector(*row["direction_xyz"])
        body = cq.Solid.makeCylinder(2.5, 63.5 - THICKNESS, p + d * THICKNESS, d)
        fraction = overlaps(body, adjusted_wood[row["receiver"]]) / body.Volume()
        assert fraction > 0.999999, row["axis_id"]
        screw_support.append(
            {
                "id": row["axis_id"],
                "receiver": row["receiver"],
                "full_body_fraction": fraction,
            }
        )
    bracket_path = Path("site/eoere-bottom-rail-scene.json.gz")
    pins[str(bracket_path)] = sha(bracket_path)
    bracket_scene = json.loads(gzip.decompress(bracket_path.read_bytes()))
    bracket_ids = {"eoere_" + duty for duty in duties}
    angle = fitting.template(fitting.Scenario())
    metals = hardware.hardware(
        [
            {
                **a,
                "point": cq.Vector(*a["point_xyz_mm"]),
                "direction": cq.Vector(*a["direction_xyz"]),
            }
            for a in updated["axes"]
        ]
    )
    moved_shapes = {
        f"{axis}_{role}": shape for axis, role, shape in metals if axis in moved_axes
    }
    for row in bracket_scene["solids"]:
        if row["fabrication"]["kind"] != "bracket":
            continue
        m = row["transform"]
        shape = angle.moved(
            cq.Plane(origin=m[12:15], xDir=m[:3], normal=m[8:11]).location
        )
        if row["name"] in bracket_ids:
            shape = shape.translate(shift)
            moved_shapes[row["name"]] = shape
        metals.append((row["name"], "bracket", shape))
    for row in updated["screw_axes"]:
        if row["axis_id"] in moved_screws:
            shapes = hardware.screw_shapes(row)
            moved_shapes["fastener_" + row["axis_id"]] = (
                shapes[0][1].fuse(shapes[1][1]).clean()
            )
    checks = {
        "moved_brackets_vs_timber": pair_hits(
            [(name, "bracket", moved_shapes[name]) for name in sorted(bracket_ids)],
            [(name, "timber", shape) for name, shape in adjusted_wood.items()],
        ),
        "moved_hardware_vs_wood": pair_hits(
            [
                (name, "hardware", shape)
                for name, shape in moved_shapes.items()
                if name not in bracket_ids and not name.startswith("fastener_")
            ],
            [(name, "timber", shape) for name, shape in adjusted_wood.items()],
        ),
    }
    checks["all_hardware_vs_all_brackets"] = pair_hits(
        [(axis, role, shape) for axis, role, shape in metals if role != "bracket"],
        [(axis, role, shape) for axis, role, shape in metals if role == "bracket"],
    )
    assert not checks["all_hardware_vs_all_brackets"], checks[
        "all_hardware_vs_all_brackets"
    ]
    original_services = retained_services(source, native, load, pins)
    checks["retained_services_vs_changed_timber"] = pair_hits(
        original_services, [(name, "timber", body) for name, body in finished.items()]
    )
    assert not checks["retained_services_vs_changed_timber"], checks[
        "retained_services_vs_changed_timber"
    ]
    canonical_checks = []
    for axis in updated["axes"]:
        if axis["id"] not in moved_axes:
            continue
        for attachment in axis["attachments"]:
            if abs(attachment["direction"][0] + 1) > 1e-8:
                continue
            bounds = finished[attachment["receiver"]].BoundingBox()
            assert (
                max(
                    abs(a - b)
                    for a, b in zip(
                        attachment["interval_mm"], [bounds.xmin, bounds.xmax]
                    )
                )
                < 1e-6
            )
            canonical_checks.append(
                {
                    "axis_id": axis["id"],
                    "duty_id": attachment["duty_id"],
                    "canonical_interval_mm": attachment["interval_mm"],
                    "saved_receiver_x_bounds_mm": [bounds.xmin, bounds.xmax],
                }
            )
    assert len(canonical_checks) == 12
    # Installed washers bear on wood tangentially; shaft/wood volume should be
    # zero after boring. Findings are retained rather than converted to capacity.
    base_dir = out / "base"
    base_dir.mkdir()
    saved, replacements = [], []
    shape_rows = {
        **finished,
        **{n: updated_panels[n] for n in changed_panels},
        **moved_shapes,
    }
    original_meta = {r["name"]: r["fabrication"] for r in bracket_scene["solids"]}
    for name, shape in shape_rows.items():
        kind = (
            "timber"
            if name in finished
            else "panel"
            if name in panels
            else "bracket"
            if name in bracket_ids
            else "screw"
            if name.startswith("fastener_")
            else "bolt"
        )
        assert shape.isValid() and len(shape.Solids()) == 1, name
        path = base_dir / (name + ".brep")
        assert shape.exportBrep(str(path))
        saved.append(
            {
                "id": name,
                "kind": kind,
                "path": str(path),
                "sha256": sha(path),
                "volume_mm3": shape.Volume(),
            }
        )
        metadata = {
            **original_meta.get(name, {}),
            "kind": kind,
            "adjustment_revision": "eoere-midpoint-ready-frame-v3",
            "description": "Adjusted base frame; coordinated 39.2-mm principal and connection relocation",
        }
        if kind == "bolt":
            metadata["connection_name"] = next(
                a for a in moved_axes if name.startswith(a + "_")
            )
        replacements.append(
            {
                "id": name,
                "name": name,
                "mesh": _shape_mesh(shape),
                "fabrication": metadata,
            }
        )
    assert len(replacements) == 136
    report = {
        "schema": "eoere_adjusted_base_geometry/v1",
        "revision": "eoere-midpoint-ready-frame-v3",
        "candidate": source["candidate"],
        "viewer_key": "eoere-adjusted-frame-development",
        "status": "REVISE_UNEVALUATED_GEOMETRY",
        "source_sha256": copy.deepcopy(pins),
        "parent_geometry": {"path": str(PARENT_REPORT), "sha256": PARENT_LAYOUT_SHA},
        "principal_shift_xyz_mm": list(shift.toTuple()),
        "extended_rails": extended,
        "moved_bolt_axes": moved_axes,
        "moved_panel_screw_axes": moved_screws,
        "affected_duties": sorted(duties),
        "canonical_interval_checks": canonical_checks,
        "retained_service_bodies_audited": len(original_services),
        "axes": updated["axes"],
        "screw_axes": updated["screw_axes"],
        "changed_finished_solids": saved,
        "service_cuts": cuts,
        "restored_contacts": contacts,
        "screw_support": screw_support,
        "collisions": checks,
        "counts": source["counts"],
        "mechanics_ready": False,
        "release": source["release"],
        "cadquery_version": cq.__version__,
        "unofficial_2026_grid_included": False,
        "limits": [
            "Existing hold/light grid and panel outlines retained; Eight main-panel and two kicker screw axes move with the right principal and kicker post.",
            "Three longer individual rail blanks restore end contact; all six bracket arrangements and twenty-two stacks move coherently.",
            "Nominal CAD geometry only; changed joint forces, capacity, tooling and tolerances are unevaluated.",
        ],
    }
    report_path = base_dir / "geometry.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    scene = {
        "schema": "eoere_adjusted_base_patch/v1",
        "candidate": source["candidate"],
        "revision": report["revision"],
        "status": report["status"],
        "parent_scene": {
            "url": PARENT_SCENE.name,
            "sha256": PARENT_SHA,
            "decoded_sha256": PARENT_DECODED_SHA,
            "layout_sha256": PARENT_LAYOUT_SHA,
        },
        "layout_report": {
            "path": str(DOC / "occupied-adjusted-base-v3.json"),
            "sha256": sha(report_path),
        },
        "counts": source["counts"],
        "replacements": replacements,
        "additions": [],
        "templates": [],
        "triangle_topologies": _deduplicate_triangle_topologies(replacements),
        "design": {
            "key": report["viewer_key"],
            "status": report["status"],
            "qualified_for_design": False,
        },
        "mechanics_ready": False,
        "release": source["release"],
        "principal_move_adopted": True,
    }
    encoded = (json.dumps(scene, separators=(",", ":")) + "\n").encode()
    (base_dir / "scene.json").write_bytes(encoded)
    (base_dir / "scene.json.gz").write_bytes(gzip.compress(encoded, mtime=0))
    parent = {
        "url": "eoere-adjusted-base-v3-scene.json.gz",
        "sha256": sha(base_dir / "scene.json.gz"),
        "decoded_sha256": hashlib.sha256(encoded).hexdigest(),
        "layout_sha256": sha(report_path),
    }
    print(
        "Adjusted base saved; contacts restored and ten screw receivers supported",
        flush=True,
    )
    return updated, adjusted_wood, updated_panels, parent, bracket_ids


def build(out):
    assert not out.exists(), "preserve prior attempts; choose a fresh output directory"
    assert sha(PARENT_SCENE) == PARENT_SHA and sha(PARENT_REPORT) == PARENT_LAYOUT_SHA
    assert (
        hashlib.sha256(gzip.decompress(PARENT_SCENE.read_bytes())).hexdigest()
        == PARENT_DECODED_SHA
    )
    source = read(PARENT_REPORT)
    raised_path = DOC / "occupied-bottom-rail-v1.json"
    raised = read(raised_path)
    native_path = DOC.parent / "native-geometry-v4.json"
    native = read(native_path)
    pins = {
        str(p): sha(p)
        for p in (PARENT_REPORT, PARENT_SCENE, raised_path, native_path, Path(__file__))
    }
    for name, module in tuple(sys.modules.items()):
        if name.startswith(("mini_moonboard.", "scripts.")) and getattr(
            module, "__file__", None
        ):
            path = Path(module.__file__).resolve()
            pins[str(path.relative_to(Path.cwd()))] = sha(path)
    loaded = {}

    def load(row):
        assert sha(row["path"]) == row["sha256"], row["path"]
        pins[row["path"]] = row["sha256"]
        if row["path"] not in loaded:
            loaded[row["path"]] = cq.Shape.importBrep(row["path"])
            assert (
                loaded[row["path"]].isValid() and len(loaded[row["path"]].Solids()) == 1
            )
        return loaded[row["path"]]

    wood_rows = source["changed_finished_solids"] + source["unchanged_finished_solids"]
    wood = {r["id"]: load(r) for r in wood_rows}
    panels = {r["id"]: load(r) for r in raised["finished_panel_solids"]}
    assert len(wood) == 22 and len(panels) == 6
    out.mkdir(parents=True)
    source, wood, panels, adjusted_parent, moved_brackets = adjusted_base(
        source, raised, native, wood, panels, load, out, pins
    )
    panels = {name: panel for name, panel in panels.items() if name.startswith("main_")}
    rows = grid()
    print(
        "Authenticated cached frame; building 120 new T-nuts, 120 lights and 119 links",
        flush=True,
    )
    additions, bodies, cutters, bores = [], [], [], {name: [] for name in panels}
    template_rows = [
        {"id": "midpoint_tnut", "mesh": _shape_mesh(tnuts.local_shape())},
        {
            "id": "midpoint_light",
            "mesh": _shape_mesh(
                cq.Solid.makeCylinder(6.35, THICKNESS + 12, cq.Vector(0, 0, -THICKNESS))
            ),
        },
    ]
    for row in rows:
        for kind, key, xy, owner, axis, template in (
            (
                "tnut",
                "hold_tnut_2026_",
                row["tnut_x_s_mm"],
                row["tnut_panel"],
                -N,
                "midpoint_tnut",
            ),
            (
                "light",
                "light_2026_",
                row["LED_x_s_mm"],
                row["LED_panel"],
                N,
                "midpoint_light",
            ),
        ):
            x, s = xy
            point = no_shoes_frame.b.point(x - no_shoes_frame.b.HALF, s, 0)
            plane = cq.Plane(origin=point, xDir=(1, 0, 0), normal=axis)
            shape = (
                tnuts.local_shape()
                if kind == "tnut"
                else cq.Solid.makeCylinder(
                    6.35, THICKNESS + 12, cq.Vector(0, 0, -THICKNESS)
                )
            ).moved(plane.location)
            name = key + row["id"]
            bodies.append((name, kind, shape))
            additions.append(
                {
                    "id": name,
                    "name": name,
                    "template_id": template,
                    "transform": matrix(plane),
                    "fabrication": {
                        "kind": kind,
                        "panel": owner,
                        "grid_station": row["id"],
                        "description": "Unofficial, unconfirmed 2026 position; exact midpoint assumed for this preview",
                        "adjustment_revision": REVISION,
                    },
                }
            )
            diameter = 11.1125 if kind == "tnut" else 13.0
            bores[owner].append(
                cq.Solid.makeCylinder(diameter / 2, THICKNESS + 2, point + N, -N)
            )
            if kind == "light":
                cutters.append(
                    (name, "light", cq.Solid.makeCylinder(9.35, 15, point, N))
                )

    sequence = [
        r
        for c in "ABCDEFGHIJ"
        for r in sorted(
            [r for r in rows if r["column"] == c],
            key=lambda r: r["row"],
            reverse=(ord(c) - ord("A")) % 2 == 1,
        )
    ]
    routes = []
    for index, (first, last) in enumerate(pairwise(sequence), 1):
        a, b = [
            [r["LED_x_s_mm"][0] - no_shoes_frame.b.HALF, r["LED_x_s_mm"][1], 14.0]
            for r in (first, last)
        ]
        controls = (
            [a, b]
            if a[0] == b[0]
            else [
                a,
                [a[0], a[1] + (30 if first["row"] == 12 else -30), 14.0],
                [b[0], b[1] + (30 if first["row"] == 12 else -30), 14.0],
                b,
            ]
        )
        route = routing.simplify_route(controls)
        shape, length = services.sweep(route, 2.0, list(no_shoes_frame.SHIFT.toTuple()))
        for endpoint in (a, b):
            point = no_shoes_frame.b.point(endpoint[0], endpoint[1], 8.0)
            shape = shape.fuse(cq.Solid.makeCylinder(2.0, 6.0, point, N)).clean()
        assert shape.isValid() and len(shape.Solids()) == 1 and length <= 304.8
        name = f"wire_2026_{index:03}_{first['id']}_{last['id']}"
        bodies.append((name, "wire", shape))
        additions.append(
            {
                "id": name,
                "name": name,
                "mesh": _shape_mesh(shape),
                "fabrication": {
                    "kind": "wire",
                    "description": "Separate midpoint lighting route; provisional cable and connection order",
                    "adjustment_revision": REVISION,
                },
            }
        )
        cutters.append(
            (
                name,
                "wire",
                routing.front_open_cutter(
                    route, list(no_shoes_frame.SHIFT.toTuple()), 6.35
                ),
            )
        )
        routes.append(
            {
                "id": name,
                "endpoints": [first["id"], last["id"]],
                "route_local_mm": route,
                "rounded_length_mm": length,
                "approximate_budget_mm": 304.8,
                "bulb_base_N_mm": 8.0,
                "cable_plane_N_mm": 14.0,
                "modeled_endpoint_lead_mm": 6.0,
                "controller_connectors_slack_and_feeding_qualified": False,
            }
        )
    assert len(routes) == 119
    rerouted = {}
    rerouted_records = []
    for record in source["wire_proposals"]:
        first, last = record["route_local_mm"][0], record["route_local_mm"][-1]
        if abs(first[0] - last[0]) < 100 or abs(first[1] - last[1]) > 1e-6:
            continue
        offset = 20.0 if first[1] > 2000 else -20.0
        route = [
            first,
            [first[0], first[1] + offset, 8.0],
            [last[0], last[1] + offset, 8.0],
            last,
        ]
        shape, length = services.sweep(route, 2.0, record["placement_xyz_mm"])
        assert shape.isValid() and len(shape.Solids()) == 1 and length <= 304.8
        rerouted[record["name"]] = shape
        cutters.append(
            (
                record["name"],
                "wire",
                routing.front_open_cutter(route, record["placement_xyz_mm"], 6.35),
            )
        )
        rerouted_records.append(
            {
                "id": record["name"],
                "route_local_mm": route,
                "rounded_length_mm": length,
                "original_LED_endpoints_retained": True,
            }
        )
    assert len(rerouted) == 10
    finished_panels, drilling = {}, []
    for name, panel in panels.items():
        finished = panel.cut(cq.Compound.makeCompound(bores[name])).clean()
        assert finished.isValid() and len(finished.Solids()) == 1
        h = sum(r["tnut_panel"] == name for r in rows)
        l = sum(r["LED_panel"] == name for r in rows)
        expected = math.pi * THICKNESS * (h * (11.1125 / 2) ** 2 + l * 6.5**2)
        actual = panel.Volume() - finished.Volume()
        assert abs(actual - expected) < 0.01, (name, actual, expected)
        finished_panels[name] = finished
        drilling.append(
            {
                "panel": name,
                "added_hold_bores": h,
                "added_LED_bores": l,
                "hold_bore_diameter_mm": 11.1125,
                "LED_bore_diameter_mm": 13,
                "removed_volume_mm3": actual,
                "expected_volume_mm3": expected,
            }
        )
        print(name, h, "hold /", l, "LED bores", flush=True)
    print(
        "Cutting additional nominal body and cable passages in existing-position timbers",
        flush=True,
    )
    finished_wood, cut_records = services.cut_services(wood, set(wood), cutters)
    changed = {
        name
        for name in wood
        if wood[name].Volume() - finished_wood[name].Volume() > 0.01
    }
    for name in changed:
        assert (
            finished_wood[name].isValid() and len(finished_wood[name].Solids()) == 1
        ), name
    print("Changed timber:", sorted(changed), flush=True)
    collisions = {
        "new_services_vs_timber": pair_hits(
            bodies, [(n, "timber", s) for n, s in finished_wood.items()]
        )
    }
    # Keep nominal hardware clashes and lost screw backing visible; this option
    # deliberately precedes the separately proposed principal relocation.
    axes = [
        {
            **copy.deepcopy(a),
            "point": cq.Vector(*a["point_xyz_mm"]),
            "direction": cq.Vector(*a["direction_xyz"]),
        }
        for a in source["axes"]
    ]
    metals = hardware.hardware(axes)
    bracket_source = Path("site/eoere-bottom-rail-scene.json.gz")
    pins[str(bracket_source)] = sha(bracket_source)
    bracket_scene = json.loads(gzip.decompress(bracket_source.read_bytes()))
    angle_body = fitting.template(fitting.Scenario())
    for row in bracket_scene["solids"]:
        if row["fabrication"]["kind"] == "bracket":
            m = row["transform"]
            placed = angle_body.moved(
                cq.Plane(origin=m[12:15], xDir=m[:3], normal=m[8:11]).location
            )
            if row["name"] in moved_brackets:
                placed = placed.translate((-39.2, 0, 0))
            metals.append(
                (
                    row["name"],
                    "bracket",
                    placed,
                )
            )
    screws = [
        (r["axis_id"], role, shape)
        for r in source["screw_axes"]
        for role, shape in hardware.screw_shapes(r)
    ]
    collisions["new_services_vs_metal"] = pair_hits(bodies, metals + screws)
    removed = [
        (name, "new_cut_void", wood[name].cut(finished_wood[name]))
        for name in sorted(changed)
    ]
    collisions["new_cuts_vs_metal"] = pair_hits(removed, metals + screws)
    existing = retained_services(source, native, load, pins)
    existing = [
        (name, kind, rerouted.get(name, shape)) for name, kind, shape in existing
    ]
    base_changed = {
        row["id"]
        for row in read(out / "base/geometry.json")["changed_finished_solids"]
        if row["kind"] == "timber"
    }
    checked_timber = changed | base_changed
    collisions["retained_services_vs_changed_timber"] = pair_hits(
        existing,
        [(name, "timber", finished_wood[name]) for name in sorted(checked_timber)],
    )
    assert not collisions["retained_services_vs_changed_timber"], collisions[
        "retained_services_vs_changed_timber"
    ]
    rerouted_bodies = [(name, "wire", shape) for name, shape in rerouted.items()]
    collisions["rerouted_original_wires_vs_timber"] = pair_hits(
        rerouted_bodies, [(n, "timber", shape) for n, shape in finished_wood.items()]
    )
    collisions["rerouted_original_wires_vs_metal"] = pair_hits(
        rerouted_bodies, metals + screws
    )
    unrelated = []
    for name, kind, shape in rerouted_bodies:
        endpoints = set(name.split("_")[2:])
        obstacles = [
            (other, role, body)
            for other, role, body in existing
            if other != name
            and not (role == "light" and other.removeprefix("light_") in endpoints)
            and not (role == "wire" and endpoints.intersection(other.split("_")[2:]))
        ]
        unrelated.extend(pair_hits([(name, kind, shape)], obstacles))
    collisions["rerouted_original_wires_vs_unrelated_services"] = unrelated
    collisions["new_services_vs_retained_services"] = pair_hits(bodies, existing)
    screw_checks = []
    for row in source["screw_axes"]:
        name = row["receiver"]
        if name not in changed:
            continue
        p, d = cq.Vector(*row["origin_xyz_mm"]), cq.Vector(*row["direction_xyz"])
        for thickness in (THICKNESS, 19.05):
            body = cq.Solid.makeCylinder(2.5, 63.5 - thickness, p + d * thickness, d)
            screw_checks.append(
                {
                    "id": row["axis_id"],
                    "receiver": name,
                    "panel_thickness_mm": thickness,
                    "before_fraction": overlaps(body, wood[name]) / body.Volume(),
                    "after_fraction": overlaps(body, finished_wood[name])
                    / body.Volume(),
                }
            )
    failed_names = {
        r["first"]
        for group in collisions.values()
        for r in group
        if r["first"].startswith(("hold_tnut_2026_", "light_2026_", "wire_2026_"))
    }
    for row in additions:
        if row["name"] in failed_names:
            row["fabrication"]["clearance_status"] = "FAIL_NOMINAL_INTERSECTION"
    saved, replacements = [], []
    for name, shape in {
        **{n: finished_wood[n] for n in sorted(changed)},
        **finished_panels,
    }.items():
        path = out / (name + ".brep")
        assert shape.exportBrep(str(path))
        restored = cq.Shape.importBrep(str(path))
        assert (
            restored.isValid()
            and len(restored.Solids()) == 1
            and abs(restored.Volume() - shape.Volume()) < 0.001
        )
        kind = "panel" if name in finished_panels else "timber"
        saved.append(
            {
                "id": name,
                "kind": kind,
                "path": str(path),
                "sha256": sha(path),
                "bytes": path.stat().st_size,
                "volume_mm3": shape.Volume(),
                "parent_volume_mm3": (panels if kind == "panel" else wood)[
                    name
                ].Volume(),
            }
        )
        replacements.append(
            {
                "id": name,
                "name": name,
                "mesh": _shape_mesh(shape),
                "fabrication": {
                    "kind": kind,
                    "description": "Additional midpoint panel bores"
                    if kind == "panel"
                    else "Additional midpoint lighting cutouts; existing member position",
                    "adjustment_revision": REVISION,
                },
            }
        )
    for name, shape in rerouted.items():
        path = out / (name + ".brep")
        assert shape.exportBrep(str(path))
        saved.append(
            {
                "id": name,
                "kind": "wire",
                "path": str(path),
                "sha256": sha(path),
                "volume_mm3": shape.Volume(),
            }
        )
        replacements.append(
            {
                "id": name,
                "name": name,
                "mesh": _shape_mesh(shape),
                "fabrication": {
                    "kind": "wire",
                    "description": "Original endpoints; link detoured around an unofficial midpoint light",
                    "adjustment_revision": REVISION,
                },
            }
        )
    topologies = _deduplicate_triangle_topologies(
        replacements + [row for row in additions if "mesh" in row] + template_rows
    )
    for path, expected in pins.items():
        assert sha(path) == expected, path
    counts = {
        **source["counts"],
        "lights": 252,
        "tnuts": 262,
        "wire": 250,
        "total_visible_parts": 1380,
    }
    report = {
        "schema": "eoere_2026_adjustments_geometry/v1",
        "candidate": source["candidate"],
        "revision": REVISION,
        "viewer_key": KEY,
        "status": "REVISE_UNEVALUATED_GEOMETRY",
        "source_sha256": pins,
        "parent_geometry": {
            "path": str(DOC / "occupied-adjusted-base-v3.json"),
            "sha256": adjusted_parent["layout_sha256"],
        },
        "grid": rows,
        "panel_drilling": drilling,
        "new_wire_routes": routes,
        "rerouted_original_wire_links": rerouted_records,
        "second_cable_plane_N_mm": 14.0,
        "original_cable_plane_N_mm": 8.0,
        "modeled_new_cable_endpoint_lead_mm": 6.0,
        "service_cuts": cut_records,
        "changed_finished_solids": saved,
        "unchanged_timber_ids": sorted(set(wood) - changed),
        "changed_timber_ids": sorted(changed),
        "screw_backing": screw_checks,
        "collisions": collisions,
        "counts": counts,
        "original_grid_retained": True,
        "retained_service_bodies_audited": len(existing),
        "retained_services_checked_timber_ids": sorted(checked_timber),
        "principal_move_adopted": True,
        "unofficial_2026_positions": True,
        "all_midpoints_are_assumed_not_confirmed": True,
        "bolt_axes_unchanged_sha256": hashlib.sha256(
            json.dumps(source["axes"], sort_keys=True).encode()
        ).hexdigest(),
        "screw_axes_unchanged_sha256": hashlib.sha256(
            json.dumps(source["screw_axes"], sort_keys=True).encode()
        ).hexdigest(),
        "source_bytes_unchanged": True,
        "cadquery_version": cq.__version__,
        "mechanics_ready": False,
        "release": source["release"],
        "execution": {"command": sys.argv, "native_solver": False},
        "limits": [
            "Owner-added main-panel horizontal midpoint grid, not a confirmed official 2026 layout; kicker unchanged.",
            "Positions are unofficial and not fully greenlit; actual future holds may not occupy exact midpoints at every station.",
            "Adjusted base retains the principal relocation when the extra 2026 layer is switched off.",
            "New holes and timber passages are model proposals, not physical drilling or machining instructions.",
            "Hardware display repeats the existing provisional T-nut/light dimensions; no holds, hold bolts or retention screws.",
            "Second lighting route is a provisional 120-site/119-link chain at N14, with modeled 6-mm leads to the assumed N8 light bases; not a sourced controller/strand/connector design.",
            "Reported nominal intersections and lost backing remain revision findings; no old force or resistance pass transfers.",
            "Machining method, tolerances, residual wood sections, installation/removal and complete joint resistance remain unqualified.",
        ],
    }
    report_path = out / "geometry.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    scene = {
        "schema": "eoere_2026_adjustments_patch/v1",
        "candidate": source["candidate"],
        "revision": REVISION,
        "status": report["status"],
        "parent_scene": adjusted_parent,
        "layout_report": {
            "path": str(DOC / "occupied-2026-adjustments-v3.json"),
            "sha256": sha(report_path),
        },
        "counts": counts,
        "replacements": replacements,
        "additions": additions,
        "templates": template_rows,
        "triangle_topologies": topologies,
        "design": {
            "key": KEY,
            "status": report["status"],
            "qualified_for_design": False,
        },
        "mechanics_ready": False,
        "release": source["release"],
        "principal_move_adopted": True,
        "unofficial_2026_positions": True,
    }
    encoded = (json.dumps(scene, separators=(",", ":")) + "\n").encode()
    (out / "scene.json").write_bytes(encoded)
    (out / "scene.json.gz").write_bytes(gzip.compress(encoded, mtime=0))
    print(
        json.dumps(
            {
                "report_sha256": sha(report_path),
                "scene_sha256": sha(out / "scene.json.gz"),
                "decoded_sha256": hashlib.sha256(encoded).hexdigest(),
                "changed_timber": sorted(changed),
                "collisions": {key: len(value) for key, value in collisions.items()},
                "failed_new_parts": len(failed_names),
                "scene_bytes": (out / "scene.json.gz").stat().st_size,
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    build(parser.parse_args().out)
