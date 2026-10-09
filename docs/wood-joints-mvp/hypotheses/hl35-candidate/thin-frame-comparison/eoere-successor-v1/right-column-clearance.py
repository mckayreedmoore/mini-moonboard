"""Screen the owner's hypothetical X2300 column against cached current solids.

Run from the repository root with a fresh ignored output directory:
PYTHONPATH=. .venv/bin/python -B docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/right-column-clearance.py --out fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/right-column-clearance-v1

No source solids, axes, meshes or mechanics are changed. New cable routes and
actual hold footprints/bolt lengths are not supplied by this screen.
"""

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import cadquery as cq

from mini_moonboard import hold_tnut_reinforcement, no_shoes_frame, panel_grid_v2
from scripts import eoere_2026_adjustments as shared
from scripts import thin_bolted_occupied as hardware
from scripts import wood_joint_midpoint_clearance as method

DOC = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(out):
    assert not out.exists(), "Use a fresh output directory."
    pins, loaded = {}, {}

    def pin(path, expected=None):
        path = str(Path(path).resolve().relative_to(Path.cwd()))
        value = sha(path)
        assert expected is None or value == expected, path
        assert path not in pins or pins[path] == value, path
        pins[path] = value
        return path

    def read(path):
        return json.loads(Path(pin(path)).read_bytes())

    def load(row):
        path = pin(row["path"], row["sha256"])
        if path not in loaded:
            loaded[path] = cq.Shape.importBrep(path)
            assert loaded[path].isValid(), path
        return loaded[path]

    pin(__file__)
    pin("uv.lock")
    for name, module in tuple(sys.modules.items()):
        if name.startswith(("mini_moonboard.", "scripts.")) and getattr(
            module, "__file__", None
        ):
            pin(module.__file__)
    aligned = read(DOC / "occupied-aligned-wire-v1.json")
    base = read(DOC / "occupied-adjusted-base-v3.json")
    extra = read(DOC / "occupied-2026-adjustments-v3.json")
    cleats = read(DOC / "occupied-extended-cleats-v1.json")
    channels = read(DOC / "occupied-uniform-channels-v1.json")
    current = read(DOC / "occupied-kicker-clearance-v1.json")
    native = read(DOC.parent / "native-geometry-v4.json")
    assert current["revision"] == "eoere-raised-kicker-screws-v1"
    assert current["parent_geometry"]["sha256"] == sha(
        DOC / "occupied-uniform-channels-v1.json"
    )
    assert channels["parent_geometry"]["sha256"] == sha(
        DOC / "occupied-extended-cleats-v1.json"
    )

    rows = {
        r["id"]: r
        for r in aligned["changed_finished_solids"]
        + aligned["unchanged_finished_solids"]
    }
    rows.update(
        {r["id"]: r for r in base["changed_finished_solids"] if r["kind"] == "timber"}
    )
    rows.update({r["id"]: r for r in cleats["changed_finished_solids"]})
    wood = {name: load(row) for name, row in rows.items()}
    wood.update(
        {
            r["id"]: load(r)
            for r in channels["changed_finished_solids"]
            if r["kind"] == "timber" and r["variant"] == "base"
        }
    )
    extra_wood = dict(wood)
    extra_wood.update(
        {
            r["id"]: load(r)
            for r in channels["changed_finished_solids"]
            if r["kind"] == "timber" and r["variant"] == "extra"
        }
    )
    assert len(wood) == len(extra_wood) == 22

    print(
        "Loaded both 22-timber variants; reconstructing recorded hardware and services",
        flush=True,
    )
    axes = [
        {
            **a,
            "point": cq.Vector(*a["point_xyz_mm"]),
            "direction": cq.Vector(*a["direction_xyz"]),
        }
        for a in current["axes"]
    ]
    metal = {
        (axis + "/" + role): (role, shape)
        for axis, role, shape in hardware.hardware(axes)
    }
    scene = json.loads(
        gzip.decompress(Path(pin("site/eoere-bottom-rail-scene.json.gz")).read_bytes())
    )
    template = shared.fitting.template(shared.fitting.Scenario())
    moved = {
        r["id"]: r for r in base["changed_finished_solids"] if r["kind"] == "bracket"
    }
    for row in scene["solids"]:
        if row["fabrication"]["kind"] == "bracket":
            t = row["transform"]
            shape = (
                load(moved[row["name"]])
                if row["name"] in moved
                else template.moved(
                    cq.Plane(origin=t[12:15], xDir=t[:3], normal=t[8:11]).location
                )
            )
            metal[row["name"]] = ("bracket", shape)
    screws = {r["id"]: r for r in native["parts"] if r["kind"] == "screw"}
    screws.update(
        {r["id"]: r for r in base["changed_finished_solids"] if r["kind"] == "screw"}
    )
    screws.update(
        {r["id"]: r for r in current["changed_finished_solids"] if r["kind"] == "screw"}
    )
    assert len(screws) == 66
    metal.update({name: ("screw", load(row)) for name, row in screws.items()})
    assert len(metal) == 588

    services = {
        name: (kind, shape)
        for name, kind, shape in shared.retained_services(aligned, native, load, pins)
    }
    for row in channels["changed_finished_solids"]:
        if row["kind"] == "wire" and row["variant"] == "common":
            services[row["id"]] = ("wire", load(row))
    extra_services = dict(services)
    for row in channels["changed_finished_solids"]:
        if row["kind"] == "wire" and row["variant"] == "extra":
            extra_services[row["id"]] = ("wire", load(row))
    frame, normal = no_shoes_frame.b, no_shoes_frame.b.normal().normalized()
    for row in extra["grid"]:
        x, s = row["tnut_x_s_mm"]
        plane = cq.Plane(
            origin=frame.point(x - frame.HALF, s, 0), xDir=(1, 0, 0), normal=-normal
        )
        extra_services["hold_tnut_2026_" + row["id"]] = (
            "tnut",
            hold_tnut_reinforcement.local_shape().moved(plane.location),
        )
        x, s = row["LED_x_s_mm"]
        extra_services["light_2026_" + row["id"]] = (
            "light",
            cq.Solid.makeCylinder(
                6.35,
                shared.THICKNESS + 12,
                frame.point(x - frame.HALF, s, -shared.THICKNESS),
                normal,
            ),
        )
    assert Counter(k for k, _ in services.values()) == {
        "tnut": 142,
        "light": 132,
        "wire": 131,
    }
    assert Counter(k for k, _ in extra_services.values()) == {
        "tnut": 262,
        "light": 252,
        "wire": 250,
    }

    # A known overlap and a separated pair exercise the exact screening method.
    box = cq.Solid.makeBox(10, 10, 10)
    assert abs(box.intersect(box.translate((5, 0, 0))).Volume() - 500) < 1e-6
    assert not method._overlap(
        method._bbox(box), method._bbox(box.translate((11, 0, 0)))
    )
    datums, lights = panel_grid_v2.main_tnut_datums(), panel_grid_v2.main_led_datums()
    x = datums["K1"][0] + 100
    assert x == 2300 and frame.HALF * 2 - x > method.FLANGE_DIAMETER_MM / 2
    probes = []
    for row in range(1, 13):
        label = f"K{row}"
        s = datums[label][1]
        rear = frame.point(x - frame.HALF, s, 0)
        probes.extend(
            [
                (
                    row,
                    "T-nut flange",
                    cq.Solid.makeCylinder(
                        method.FLANGE_DIAMETER_MM / 2,
                        method.FLANGE_THICKNESS_MM,
                        rear,
                        normal,
                    ),
                ),
                (
                    row,
                    "rear bolt envelope",
                    cq.Solid.makeCylinder(
                        method.PROJECTION_DIAMETER_MM / 2,
                        method.PROJECTION_LENGTH_MM,
                        rear,
                        normal,
                    ),
                ),
                (
                    row,
                    "LED and bore envelope",
                    cq.Solid.makeCylinder(
                        6.5,
                        shared.THICKNESS + 12,
                        frame.point(
                            x - frame.HALF, lights[label][1], -shared.THICKNESS
                        ),
                        normal,
                    ),
                ),
            ]
        )
    assert len(probes) == 36
    states = {}
    for name, timber, service in [
        ("base", wood, services),
        ("extra", extra_wood, extra_services),
    ]:
        pool = {**{k: ("timber", s) for k, s in timber.items()}, **metal, **service}
        bounds = {k: method._bbox(s) for k, (_, s) in pool.items()}
        hits = []
        candidates = 0
        for row, kind, probe in probes:
            for other, (role, shape) in pool.items():
                if method._overlap(method._bbox(probe), bounds[other]):
                    candidates += 1
                    volume = probe.intersect(shape).Volume()
                    if volume > method.VOLUME_TOLERANCE_MM3:
                        hits.append(
                            {
                                "row": row,
                                "probe": kind,
                                "other": other,
                                "role": role,
                                "volume_mm3": volume,
                            }
                        )
        rim = timber["base_side_right"]
        gaps = {
            kind: min(probe.distance(rim) for _, k, probe in probes if k == kind)
            for kind in {k for _, k, _ in probes}
        }
        states[name] = {
            "obstacle_counts": dict(Counter(role for role, _ in pool.values())),
            "bbox_candidates": candidates,
            "hits": hits,
            "right_4x6_minimum_distance_mm": gaps,
            "right_4x6_bounds_xyz_mm": method._bbox(rim),
        }
        print(name, len(hits), "intersections", gaps, flush=True)

    for path, value in pins.items():
        assert sha(path) == value, "Source changed during check: " + path
    result = {
        "schema": "hypothetical-right-column-clearance-v1",
        "current_revision": current["revision"],
        "status": "geometry screen only; column unadopted",
        "main_face_x_mm": x,
        "right_panel_edge_to_center_mm": frame.HALF * 2 - x,
        "added_T_nuts": 12,
        "added_LEDs": 12,
        "expanded_main_face_positions": 264,
        "double_2025_bundle_main_holds": 256,
        "spare_main_face_positions": 8,
        "envelopes_mm": {
            "T_nut_flange_diameter": method.FLANGE_DIAMETER_MM,
            "flange_thickness": method.FLANGE_THICKNESS_MM,
            "rear_bolt_diameter": method.PROJECTION_DIAMETER_MM,
            "rear_bolt_length": method.PROJECTION_LENGTH_MM,
            "LED_bore_diameter": 13,
            "LED_rear_projection": 12,
        },
        "variants": states,
        "source_bytes_unchanged": True,
        "python_version": sys.version,
        "cadquery_version": cq.__version__,
        "source_sha256": {p: v for p, v in pins.items() if not p.endswith(".brep")},
        "consumed_source_count": len(pins),
        "consumed_source_pins_sha256": hashlib.sha256(
            json.dumps(pins, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "raw_output": str(out),
        "limits": [
            "No frame, axes, panel holes, viewer meshes or candidate selection changed.",
            "Actual hold footprints, retention screws, actual hold bolts, tolerances, drilling access and resistance are not qualified.",
            "Existing cable bodies are screened; routes for the twelve proposed LEDs are not designed or screened.",
            "50.8 mm rear bolt reach is a generic screening envelope, not a purchased or delivered bolt-length instruction.",
            "Two complete 2025 bundles also contain twenty kicker footholds; the existing kicker has ten positions.",
        ],
        "command": "PYTHONPATH=. .venv/bin/python -B "
        + str(Path(__file__).resolve().relative_to(Path.cwd()))
        + " --out "
        + str(out),
    }
    out.mkdir(parents=True)
    (out / "source-pins.json").write_text(json.dumps(pins, indent=2) + "\n")
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(out / "result.json", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    main(parser.parse_args().out)
