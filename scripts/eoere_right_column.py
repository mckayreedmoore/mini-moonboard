"""Add an optional X2300 column to the current expanded-grid CAD/viewer.

Use a fresh ignored --out directory. Cached current solids are authenticated;
Two right panels, three service-channel rails and twelve links are exported.
No mechanics runs.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import cadquery as cq

from mini_moonboard import hold_tnut_reinforcement, no_shoes_frame, panel_grid_v2
from scripts import eoere_2026_adjustments as shared
from scripts import eoere_uniform_service_channels as channels_method
from scripts import hl35_nominal_service_candidate as service
from scripts import thin_bolted_layout_revision as routing
from scripts import thin_bolted_occupied as hardware
from scripts import wood_joint_midpoint_clearance as method
from scripts.export_wood_joint_wj24_scene import (
    _deduplicate_triangle_topologies,
    _shape_mesh,
)

DOC = shared.DOC
REVISION = "eoere-expanded-right-column-v1"
KEY = "eoere-expanded-right-column-development"
REPORT = DOC / "occupied-right-column-v1.json"
PARENT = DOC / "occupied-kicker-clearance-v1.json"
PARENT_SHA = "7ebee98cb777de63ecdbc32007c97967c445500d93053eb942ab775568a5fb5f"
SCENE = Path("site/eoere-kicker-clearance-scene.json.gz")
SCENE_SHA = "0c0acfde3d6dbcaada4ffc9789898775348d4765b87525a83c20e724f8e8aa52"
COUNTS = {
    "timber": 22,
    "panel": 6,
    "bracket": 22,
    "bolt": 500,
    "screw": 66,
    "physical_bolt_axes": 100,
    "tnuts": 274,
    "lights": 264,
    "wire": 262,
    "total_visible_parts": 1416,
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def build(out):
    assert not out.exists(), "Choose a fresh output directory."
    pins, loaded = {}, {}

    def pin(path, expected=None):
        path = str(path)
        digest = sha(path)
        assert expected is None or digest == expected, path
        assert path not in pins or pins[path] == digest, path
        pins[path] = digest
        return path

    def read(path, expected=None):
        return json.loads(Path(pin(path, expected)).read_bytes())

    def load(row):
        path = pin(row["path"], row["sha256"])
        if path not in loaded:
            loaded[path] = cq.Shape.importBrep(path)
            assert loaded[path].isValid() and len(loaded[path].Solids()) == 1, path
        return loaded[path]

    def verify():
        for path, digest in pins.items():
            assert sha(path) == digest, "Changed input: " + path

    pin(Path(__file__).resolve().relative_to(Path.cwd()))
    pin("uv.lock")
    for name, module in tuple(sys.modules.items()):
        if name.startswith(("mini_moonboard.", "scripts.")) and getattr(
            module, "__file__", None
        ):
            pin(Path(module.__file__).resolve().relative_to(Path.cwd()))
    aligned = read(DOC / "occupied-aligned-wire-v1.json")
    base = read(DOC / "occupied-adjusted-base-v3.json")
    extra = read(DOC / "occupied-2026-adjustments-v3.json")
    cleats = read(DOC / "occupied-extended-cleats-v1.json")
    channels = read(DOC / "occupied-uniform-channels-v1.json")
    current = read(PARENT, PARENT_SHA)
    native = read(DOC.parent / "native-geometry-v4.json")
    pin(SCENE, SCENE_SHA)
    assert current["parent_geometry"]["sha256"] == sha(
        DOC / "occupied-uniform-channels-v1.json"
    )
    assert channels["parent_geometry"]["sha256"] == sha(
        DOC / "occupied-extended-cleats-v1.json"
    )
    out.mkdir(parents=True)
    (out / "producer.py").write_bytes(Path(__file__).read_bytes())
    print("Authenticated current frame; importing cached occupied solids", flush=True)

    rows = {
        r["id"]: r
        for r in aligned["changed_finished_solids"]
        + aligned["unchanged_finished_solids"]
    }
    rows.update(
        {r["id"]: r for r in base["changed_finished_solids"] if r["kind"] == "timber"}
    )
    rows.update({r["id"]: r for r in cleats["changed_finished_solids"]})
    for variant in ["base", "extra"]:
        rows.update(
            {
                r["id"]: r
                for r in channels["changed_finished_solids"]
                if r["kind"] == "timber" and r["variant"] == variant
            }
        )
    wood = [(name, "timber", load(row)) for name, row in rows.items()]
    assert len(wood) == 22
    axes = [
        {
            **a,
            "point": cq.Vector(*a["point_xyz_mm"]),
            "direction": cq.Vector(*a["direction_xyz"]),
        }
        for a in current["axes"]
    ]
    metal = [
        (axis + "/" + role, role, shape)
        for axis, role, shape in hardware.hardware(axes)
    ]
    bracket_scene = json.loads(
        gzip.decompress(Path(pin("site/eoere-bottom-rail-scene.json.gz")).read_bytes())
    )
    bracket_template = shared.fitting.template(shared.fitting.Scenario())
    moved = {
        r["id"]: r for r in base["changed_finished_solids"] if r["kind"] == "bracket"
    }
    for row in bracket_scene["solids"]:
        if row["fabrication"]["kind"] == "bracket":
            t = row["transform"]
            body = (
                load(moved[row["name"]])
                if row["name"] in moved
                else bracket_template.moved(
                    cq.Plane(origin=t[12:15], xDir=t[:3], normal=t[8:11]).location
                )
            )
            metal.append((row["name"], "bracket", body))
    screws = {r["id"]: r for r in native["parts"] if r["kind"] == "screw"}
    for source in [base, current]:
        screws.update(
            {
                r["id"]: r
                for r in source["changed_finished_solids"]
                if r["kind"] == "screw"
            }
        )
    metal.extend((name, "screw", load(row)) for name, row in screws.items())
    assert len(screws) == 66 and len(metal) == 588
    retained = {
        name: (kind, body)
        for name, kind, body in shared.retained_services(aligned, native, load, pins)
    }
    for variant in ["common", "extra"]:
        retained.update(
            {
                r["id"]: ("wire", load(r))
                for r in channels["changed_finished_solids"]
                if r["kind"] == "wire" and r["variant"] == variant
            }
        )
    frame, normal = no_shoes_frame.b, no_shoes_frame.b.normal().normalized()

    def tnut_plane(x, s):
        return cq.Plane(
            origin=frame.point(x - frame.HALF, s, 0), xDir=(1, 0, 0), normal=-normal
        )

    def light_plane(x, s):
        return cq.Plane(
            origin=frame.point(x - frame.HALF, s, -shared.THICKNESS),
            xDir=(1, 0, 0),
            normal=normal,
        )

    light_template = cq.Solid.makeCylinder(6.35, shared.THICKNESS + 12)
    for row in extra["grid"]:
        retained["hold_tnut_2026_" + row["id"]] = (
            "tnut",
            hold_tnut_reinforcement.local_shape().moved(
                tnut_plane(*row["tnut_x_s_mm"]).location
            ),
        )
        retained["light_2026_" + row["id"]] = (
            "light",
            light_template.moved(light_plane(*row["LED_x_s_mm"]).location),
        )
    assert Counter(k for k, _ in retained.values()) == {
        "tnut": 262,
        "light": 252,
        "wire": 250,
    }
    old_services = [(name, kind, body) for name, (kind, body) in retained.items()]

    holds, lights = panel_grid_v2.main_tnut_datums(), panel_grid_v2.main_led_datums()
    grid, added, holes, probes, instances = [], [], [], [], []
    for row in range(1, 13):
        label = f"Kplus{row}"
        x, s = holds[f"K{row}"]
        x += 100
        ls = lights[f"K{row}"][1]
        assert x == 2300
        item = {
            "id": label,
            "row": row,
            "column": "Kplus",
            "tnut_x_s_mm": [x, s],
            "LED_x_s_mm": [x, ls],
            "tnut_panel": shared.panel_at(x, s),
            "LED_panel": shared.panel_at(x, ls),
        }
        grid.append(item)
        for kind, point, template, plane, diameter in [
            (
                "tnut",
                (x, s),
                hold_tnut_reinforcement.local_shape(),
                tnut_plane(x, s),
                11.1125,
            ),
            ("light", (x, ls), light_template, light_plane(x, ls), 13),
        ]:
            name = ("hold_tnut_right_" if kind == "tnut" else "light_right_") + label
            body = template.moved(plane.location)
            assert body.isValid() and len(body.Solids()) == 1
            added.append((name, kind, body))
            instances.append(
                {
                    "id": name,
                    "name": name,
                    "template_id": "right_" + kind,
                    "transform": shared.matrix(plane),
                    "fabrication": {
                        "kind": kind,
                        "right_column_revision": REVISION,
                        "grid_position": label,
                        "unofficial_position": True,
                    },
                }
            )
            px, ps = point
            cutter = cq.Solid.makeCylinder(
                diameter / 2,
                shared.THICKNESS + 2,
                frame.point(px - frame.HALF, ps, 1),
                -normal,
            )
            holes.append((name + "_bore", kind + "_bore", cutter))
        rear = frame.point(x - frame.HALF, s, 0)
        probes.append(
            (
                label + "_rear_bolt",
                "rear_bolt_envelope",
                cq.Solid.makeCylinder(
                    method.PROJECTION_DIAMETER_MM / 2,
                    method.PROJECTION_LENGTH_MM,
                    rear,
                    normal,
                ),
            )
        )

    routes, cables = [], []
    endpoints = {
        "JK1": [extra["grid"][-12]["LED_x_s_mm"][0] - frame.HALF, lights["K1"][1], 8]
    }
    for row in grid:
        endpoints[row["id"]] = [
            row["LED_x_s_mm"][0] - frame.HALF,
            row["LED_x_s_mm"][1],
            8,
        ]
    assert endpoints["JK1"][0] == 880.8

    def link(first, last, route, source=None):
        name = f"wire_right_{first}_{last}"
        assert route[0] == endpoints[first] and route[-1] == endpoints[last]
        body, length = service.sweep(route, 2, list(no_shoes_frame.SHIFT.toTuple()))
        assert body.isValid() and len(body.Solids()) == 1 and length <= 304.8
        cables.append((name, "wire", body))
        routes.append(
            {
                "id": name,
                "LED_endpoints": [first, last],
                "route_local_mm": route,
                "source_route": source,
                "rounded_length_mm": length,
                "approximate_budget_mm": 304.8,
                "cable_diameter_mm": 4,
                "actual_slack_bend_radius_or_feed_verified": False,
            }
        )

    link(
        "JK1",
        "Kplus1",
        channels_method.flexible_route(
            endpoints["JK1"], endpoints["Kplus1"], "extra_horizontal"
        ),
    )
    aligned_routes = {r["name"]: r for r in aligned["wire_proposals"]}
    for row in range(1, 12):
        source = f"wire_{120 + row:03d}_K{row}_K{row + 1}"
        route = [
            [x + 100, s, n] for x, s, n in aligned_routes[source]["route_local_mm"]
        ]
        link(f"Kplus{row}", f"Kplus{row + 1}", route, source)
    assert len(cables) == 12
    # Three translated links cross rails. Use the existing planar front-open
    # channel profile; their hold-bolt doglegs lie outside those rail sections.
    channel_cutters = []
    for row in routes:
        if row["source_route"] in {
            "wire_121_K1_K2",
            "wire_126_K6_K7",
            "wire_127_K7_K8",
        }:
            planar = [row["route_local_mm"][0], row["route_local_mm"][-1]]
            row["machining_route_local_mm"] = planar
            channel_cutters.append(
                (
                    row["id"],
                    "wire",
                    routing.front_open_cutter(
                        planar,
                        list(no_shoes_frame.SHIFT.toTuple()),
                        channels_method.RADIUS,
                    ),
                )
            )
    original_wood = {name: body for name, _, body in wood}
    finished, channel_cuts = service.cut_services(
        original_wood, set(original_wood), channel_cutters
    )
    changed_wood = {r["receiver"] for r in channel_cuts}
    assert changed_wood == {
        "base_rail_bottom_right",
        "base_rail_service_lower_right",
        "base_rail_service_upper_right",
    }
    assert len(channel_cuts) == 3
    for name in changed_wood:
        assert finished[name].isValid() and len(finished[name].Solids()) == 1
        assert all(
            abs(a - b) < 1e-6
            for a, b in zip(
                method._bbox(original_wood[name]), method._bbox(finished[name])
            )
        )
    wood = [(name, "timber", body) for name, body in finished.items()]
    verify()
    print(
        "Checking new services, bolt envelopes and panel bores against current solids",
        flush=True,
    )
    box = cq.Solid.makeBox(10, 10, 10)
    assert abs(box.intersect(box.translate((5, 0, 0))).Volume() - 500) < 1e-6
    assert not method._overlap(
        method._bbox(box), method._bbox(box.translate((11, 0, 0)))
    )
    candidates, collisions, contacts = defaultdict(int), [], []

    def screen(label, first, second, allow=None):
        a = [(name, kind, body, method._bbox(body)) for name, kind, body in first]
        b = [(name, kind, body, method._bbox(body)) for name, kind, body in second]
        for name, kind, body, bounds in a:
            for other, role, shape, other_bounds in b:
                if not method._overlap(bounds, other_bounds):
                    continue
                candidates[label] += 1
                volume = body.intersect(shape).Volume()
                if volume <= method.VOLUME_TOLERANCE_MM3:
                    continue
                result = {
                    "check": label,
                    "first": name,
                    "first_role": kind,
                    "second": other,
                    "second_role": role,
                    "intersection_mm3": volume,
                }
                (
                    contacts
                    if allow and allow(name, other, body, shape)
                    else collisions
                ).append(result)

    # Only cable/LED contacts confined to the modeled endpoint bulb are expected.
    route_by_name = {r["id"]: r for r in routes}
    LED_shapes = {
        **{n: b for n, k, b in old_services if k == "light"},
        **{n: b for n, k, b in added if k == "light"},
    }

    def endpoint_contact(name, other, cable, obstacle):
        for endpoint in route_by_name[name]["LED_endpoints"]:
            led_name = (
                "light_2026_JK1" if endpoint == "JK1" else "light_right_" + endpoint
            )
            if other == led_name:
                return True
            if (
                other in route_by_name
                and endpoint in route_by_name[other]["LED_endpoints"]
            ):
                overlap = cable.intersect(obstacle)
                return (
                    overlap.cut(LED_shapes[led_name]).Volume()
                    <= method.VOLUME_TOLERANCE_MM3
                )
            if endpoint == "JK1" and other == "wire_2026_119_JK2_JK1":
                overlap = cable.intersect(obstacle)
                return (
                    overlap.cut(LED_shapes[led_name]).Volume()
                    <= method.VOLUME_TOLERANCE_MM3
                )
        return False

    screen("new_services_vs_frame", added + cables + holes + probes, wood + metal)
    screen("new_channel_cutters_vs_hardware", channel_cutters, metal)
    screen("new_positions_vs_existing_services", added + holes + probes, old_services)
    screen("new_cables_vs_existing_services", cables, old_services, endpoint_contact)
    screen(
        "new_cables_vs_new_positions_and_bolts",
        cables,
        added + probes,
        endpoint_contact,
    )
    for index, cable in enumerate(cables):
        screen("new_cable_pairs", [cable], cables[index + 1 :], endpoint_contact)
    check = {
        "passed": not collisions,
        "exact_candidates": dict(candidates),
        "collisions": collisions,
        "intentional_LED_endpoint_contacts": contacts,
        "intersection_tolerance_mm3": method.VOLUME_TOLERANCE_MM3,
        "known_answer_fixtures": 2,
    }
    write_json(out / "clearance.json", check)
    assert not collisions, "New-column collision(s); see clearance.json"

    # Every new bore is fully contained in its assigned panel and removes its
    # full circular prism, independently verifying axes, depth and hole count.
    panel_sources = {
        r["id"]: r for r in extra["changed_finished_solids"] if r["kind"] == "panel"
    }
    panels, panel_checks = {}, []
    for name in ["main_lower_right", "main_upper_right"]:
        previous = load(panel_sources[name])
        relevant, counts = [], Counter()
        for row in grid:
            for kind, coords, diameter in [
                ("tnut", row["tnut_x_s_mm"], 11.1125),
                ("LED", row["LED_x_s_mm"], 13),
            ]:
                if row["tnut_panel" if kind == "tnut" else "LED_panel"] == name:
                    x, s = coords
                    relevant.append(
                        cq.Solid.makeCylinder(
                            diameter / 2,
                            shared.THICKNESS + 2,
                            frame.point(x - frame.HALF, s, 1),
                            -normal,
                        )
                    )
                    counts[kind] += 1
        body = previous.cut(*relevant).clean()
        expected = (
            math.pi
            * shared.THICKNESS
            * (counts["tnut"] * (11.1125 / 2) ** 2 + counts["LED"] * 6.5**2)
        )
        removed = previous.Volume() - body.Volume()
        assert body.isValid() and len(body.Solids()) == 1
        assert abs(removed - expected) < 0.01, (name, removed, expected)
        assert all(
            abs(a - b) < 1e-6
            for a, b in zip(method._bbox(previous), method._bbox(body))
        )
        panels[name] = body
        panel_checks.append(
            {
                "id": name,
                "holes": dict(counts),
                "removed_volume_mm3": removed,
                "expected_removed_volume_mm3": expected,
                "bounds_unchanged": True,
                "parent_path": panel_sources[name]["path"],
                "parent_sha256": panel_sources[name]["sha256"],
            }
        )
    assert sum(sum(r["holes"].values()) for r in panel_checks) == 24
    rim = {n: b for n, _, b in wood}["base_side_right"]
    flange_gap = min(b.distance(rim) for _, kind, b in added if kind == "tnut")
    bolt_gap = min(b.distance(rim) for _, _, b in probes)
    cable_gap = min(b.distance(rim) for _, _, b in cables)
    assert abs(flange_gap - 33.625) < 1e-5
    print(
        "Nominal clearance passed; exporting two panels, three channel rails and twelve links",
        flush=True,
    )
    saved_rows, replacements, wire_meshes = [], [], []
    saves = (
        [(n, "panel", b) for n, b in panels.items()]
        + [(n, "timber", finished[n]) for n in sorted(changed_wood)]
        + cables
    )
    for name, kind, body in saves:
        path = out / (name + ".brep")
        assert body.exportBrep(str(path))
        saved = cq.Shape.importBrep(str(path))
        assert (
            saved.isValid()
            and len(saved.Solids()) == 1
            and abs(saved.Volume() - body.Volume()) < 0.001
        )
        saved_rows.append(
            {
                "id": name,
                "kind": kind,
                "path": str(path),
                "sha256": sha(path),
                "bytes": path.stat().st_size,
                "volume_mm3": saved.Volume(),
                "bounds_xyz_mm": method._bbox(saved),
            }
        )
        mesh_row = {
            "id": name,
            "name": name,
            "mesh": _shape_mesh(saved),
            "source_brep_sha256": sha(path),
            "fabrication": {"kind": kind, "right_column_revision": REVISION},
        }
        (wire_meshes if kind == "wire" else replacements).append(mesh_row)
    templates = [
        {
            "id": "right_tnut",
            "mesh": _shape_mesh(hold_tnut_reinforcement.local_shape()),
        },
        {"id": "right_light", "mesh": _shape_mesh(light_template)},
    ]
    verify()
    report = {
        "schema": "eoere_right_column_geometry/v1",
        "revision": REVISION,
        "candidate": current["candidate"],
        "status": "REVISE_UNEVALUATED_GEOMETRY",
        "parent_geometry": {"path": str(PARENT), "sha256": PARENT_SHA},
        "source_sha256": pins,
        "grid": grid,
        "counts": COUNTS,
        "main_face_positions": 264,
        "kicker_positions": 10,
        "added_tnuts": 12,
        "added_lights": 12,
        "added_links": 12,
        "column_x_mm": 2300,
        "offset_right_of_K_mm": 100,
        "changed_finished_solids": saved_rows,
        "panel_bores": panel_checks,
        "service_cuts": channel_cuts,
        "service_channel_profile": {
            "front_width_mm": 2 * math.hypot(8, 6.35),
            "rear_depth_mm": 14.35,
            "center_N_mm": 8,
            "clearance_radius_mm": 6.35,
        },
        "routes": routes,
        "clearance": check,
        "right_4x6_gaps_mm": {
            "tnut_flange": flange_gap,
            "rear_bolt_envelope": bolt_gap,
            "cable": cable_gap,
        },
        "unchanged_timber_count": 19,
        "axes": current["axes"],
        "screw_axes": current["screw_axes"],
        "axes_canonical_sha256": channels_method.canonical(current["axes"]),
        "screw_axes_canonical_sha256": channels_method.canonical(current["screw_axes"]),
        "optional_grid_unofficial": True,
        "base_geometry_unchanged": True,
        "analysis_pass_transferred": False,
        "mechanics_ready": False,
        "release": current["release"],
        "cadquery_version": cq.__version__,
        "execution": {"command": sys.argv, "native_solver": False},
        "limits": [
            "Provisional owner-requested column; future official grid/hold selection is unknown.",
            "Generic 11.1125-mm diameter, 50.8-mm rear bolt envelope; actual hold footprints/bolts unqualified.",
            "Nominal 4-mm cables and 304.8-mm approximate link budget; actual slack, bends, connectors and feed unverified.",
            "Three optional rail service channels added; frame axes, screws, kicker and base option preserved. No mechanics or physical release.",
        ],
    }
    write_json(out / "geometry.json", report)
    patch = {
        "schema": "eoere_right_column_patch/v1",
        "revision": REVISION,
        "candidate": current["candidate"],
        "status": report["status"],
        "parent_scene": {
            "url": SCENE.name,
            "sha256": SCENE_SHA,
            "decoded_sha256": hashlib.sha256(
                gzip.decompress(SCENE.read_bytes())
            ).hexdigest(),
            "layout_sha256": PARENT_SHA,
        },
        "layout_report": {"path": str(REPORT), "sha256": sha(out / "geometry.json")},
        "grid": grid,
        "counts": COUNTS,
        "replacements": replacements,
        "additions": instances + wire_meshes,
        "templates": templates,
        "triangle_topologies": _deduplicate_triangle_topologies(
            replacements + wire_meshes + templates
        ),
        "optional_grid_unofficial": True,
        "base_geometry_unchanged": True,
        "analysis_pass_transferred": False,
        "mechanics_ready": False,
        "release": current["release"],
    }
    decoded = (
        json.dumps(patch, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()
    with (
        (out / "scene.json.gz").open("xb") as stream,
        gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as zipped,
    ):
        zipped.write(decoded)
    verify()
    print(
        json.dumps(
            {
                "passed": True,
                "out": str(out),
                "scene_bytes": (out / "scene.json.gz").stat().st_size,
                "scene_sha256": sha(out / "scene.json.gz"),
                "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
                "layout_sha256": sha(out / "geometry.json"),
                "gaps_mm": report["right_4x6_gaps_mm"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    build(parser.parse_args().out)
