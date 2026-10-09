"""Use the smaller cable channel and flexible cable lifts in the extra-grid preview.

The principal's unnecessary F-column arc cuts are restored in both modes. The
optional layer is recut from base timbers, without old deeper and sideways voids.
Run with a fresh ignored --out directory. No native mechanics is performed.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path

DOC = Path(
    "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1"
)
REVISION = "eoere-uniform-small-service-channels-v1"
REPORT = DOC / "occupied-uniform-channels-v1.json"
PARENT = DOC / "occupied-extended-cleats-v1.json"
PARENT_SHA = "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d"
RADIUS, CHANNEL_N, LIFT_N, LEAD = 6.35, 8.0, 12.2, 20.0


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


def flexible_route(first, last, family):
    """Separate flexible cable paths from the common straight machining profile."""
    first, last = list(first), list(last)
    first[2] = last[2] = CHANNEL_N
    if abs(first[0] - last[0]) < 1e-6:
        return [first, last]
    assert abs(first[1] - last[1]) < 1e-6
    sign = 1 if last[0] > first[0] else -1
    assert abs(last[0] - first[0]) > 2 * LEAD
    middle = (first[0] + last[0]) / 2
    offset = 12 if first[1] > 2000 else -12
    depth = CHANNEL_N if family == "original_horizontal" else LIFT_N
    bypass = 30 if family == "original_horizontal" else 20
    controls = [
        [middle - sign * bypass, first[1], depth],
        [middle, first[1] + offset, depth],
        [middle + sign * bypass, first[1], depth],
    ]
    if family == "original_horizontal":
        return [first, *controls, last]
    return [
        first,
        [first[0] + sign * LEAD, first[1], depth],
        *controls,
        [last[0] - sign * LEAD, last[1], depth],
        last,
    ]


def build(out):
    assert not out.exists(), (
        "choose a fresh output directory; preserve earlier evidence"
    )
    assert sha(PARENT) == PARENT_SHA, "extended-cleat parent changed"
    parent = read(PARENT)
    pins = dict(parent["source_sha256"])
    pins[str(PARENT)] = PARENT_SHA
    pins[str(Path(__file__).resolve().relative_to(Path.cwd()))] = sha(__file__)

    def pin(path, expected=None):
        path = str(path)
        digest = sha(path)
        assert expected is None or digest == expected, "changed source: " + path
        assert path not in pins or pins[path] == digest, "conflicting source: " + path
        pins[path] = digest
        return digest

    def verify():
        for path, digest in pins.items():
            assert sha(path) == digest, "changed source: " + path

    pin("site/eoere-cleat-extension-scene.json.gz")
    verify()
    out.mkdir(parents=True)
    (out / "producer.py").write_bytes(Path(__file__).read_bytes())
    (out / "inputs.json").write_text(json.dumps(pins, indent=2) + "\n")
    import cadquery as cq

    from mini_moonboard import (
        hold_tnut_reinforcement,
        no_shoes_frame,
        round_structural_wiring,
    )
    from scripts import eoere_2026_adjustments as shared
    from scripts import hl35_nominal_service_candidate as service
    from scripts import thin_bolted_layout_revision as routing
    from scripts import thin_bolted_occupied as hardware
    from scripts.export_wood_joint_wj24_scene import (
        _deduplicate_triangle_topologies,
        _shape_mesh,
    )
    from scripts.hl35_candidate import overlaps

    for name, module in tuple(sys.modules.items()):
        if name.startswith(("mini_moonboard.", "scripts.")) and getattr(
            module, "__file__", None
        ):
            pin(Path(module.__file__).resolve().relative_to(Path.cwd()))
    verify()
    base = read(DOC / "occupied-adjusted-base-v3.json")
    extra = read(DOC / "occupied-2026-adjustments-v3.json")
    aligned = read(DOC / "occupied-aligned-wire-v1.json")
    native = read(DOC.parent / "native-geometry-v4.json")
    for path in [
        DOC / "occupied-adjusted-base-v3.json",
        DOC / "occupied-2026-adjustments-v3.json",
        DOC / "occupied-aligned-wire-v1.json",
        DOC.parent / "native-geometry-v4.json",
    ]:
        pin(path)
    loaded = {}

    def load(row):
        path = row["path"]
        pin(path, row["sha256"])
        if path not in loaded:
            loaded[path] = cq.Shape.importBrep(path)
            assert loaded[path].isValid() and len(loaded[path].Solids()) == 1, path
        return loaded[path]

    print(
        "Authenticated extended-cleat base; importing current service and timber bodies",
        flush=True,
    )
    rows = {
        r["id"]: r
        for r in aligned["changed_finished_solids"]
        + aligned["unchanged_finished_solids"]
    }
    rows.update(
        {r["id"]: r for r in base["changed_finished_solids"] if r["kind"] == "timber"}
    )
    rows.update({r["id"]: r for r in parent["changed_finished_solids"]})
    wood = {name: load(row) for name, row in rows.items()}
    assert len(wood) == 22
    retained = shared.retained_services(aligned, native, load, pins)
    old_extra = {
        r["id"]: r for r in extra["changed_finished_solids"] if r["id"] in wood
    }
    assert len(old_extra) == 9
    # The two exposed cleats are already part of the base and receive no changes.
    assert not any(name.startswith("eoere_cleat") for name in old_extra)
    route_records, cables, cutters, endpoints = [], [], [], {}
    ramp_limits = []
    placement = list(no_shoes_frame.SHIFT.toTuple())

    def make_link(name, first, last, family):
        route = flexible_route(first, last, family)
        body, length = service.sweep(route, 2.0, placement)
        lifted = any(p[2] > CHANNEL_N for p in route)
        # Retain the original connector-bearing D1/E1 link. Its flexible lead
        # lets the provisional connector sit clear of the midpoint bulb.
        connector = None
        if name in {"wire_048_D1_E1", "wire_066_F7_F6"}:
            center = [(3 * a + b) / 4 for a, b in zip(first, last)]
            center[2] = LIFT_N if lifted else CHANNEL_N
            direction = (
                round_structural_wiring.b.point(*last)
                - round_structural_wiring.b.point(*first)
            ).normalized()
            start = (
                round_structural_wiring.b.point(*center)
                + cq.Vector(*placement)
                - direction * 15
            )
            envelope = cq.Solid.makeCylinder(
                round_structural_wiring.MEASURED_MAXIMUM_DIAMETER_MM / 2,
                30,
                start,
                direction,
            )
            body = body.fuse(envelope).clean()
            connector = {
                "center_local_mm": center,
                "length_mm": 30,
                "diameter_mm": round_structural_wiring.MEASURED_MAXIMUM_DIAMETER_MM,
                "actual_connector_position_or_feed_verified": False,
            }
        assert body.isValid() and len(body.Solids()) == 1 and length <= 304.8, name
        planar = [[first[0], first[1], CHANNEL_N], [last[0], last[1], CHANNEL_N]]
        cutter = routing.front_open_cutter(planar, placement, RADIUS)
        cables.append((name, "wire", body))
        cutters.append((name, "wire", cutter))
        record = {
            "id": name,
            "family": family,
            "route_local_mm": route,
            "machining_route_local_mm": planar,
            "source_LED_endpoints_local_mm": [first, last],
            "endpoints_retained": route[0] == first and route[-1] == last,
            "rounded_length_mm": length,
            "approximate_budget_mm": 304.8,
            "cable_diameter_mm": 4.0,
            "depth_lift": lifted,
            "connector_envelope": connector,
            "actual_slack_bend_radius_or_feed_verified": False,
        }
        assert record["endpoints_retained"]
        route_records.append(record)
        if lifted:
            ramp_limits.append(
                {
                    "id": name,
                    "rise_mm": LIFT_N - CHANNEL_N,
                    "nominal_crossing_gap_mm": LIFT_N - CHANNEL_N - 4,
                    "nominal_rear_channel_gap_mm": CHANNEL_N + RADIUS - LIFT_N - 2,
                }
            )

    f_names = set()
    for source in aligned["wire_proposals"]:
        first, last = source["route_local_mm"][0], source["route_local_mm"][-1]
        labels = source["name"].split("_")[2:]
        if all(label.startswith("F") for label in labels):
            make_link(source["name"], first, last, "original_F_column")
            endpoints[source["name"]] = set(labels)
            f_names.add(source["name"])
    assert len(f_names) == 11
    common_cables = list(cables)
    for source in aligned["wire_proposals"]:
        first, last = source["route_local_mm"][0], source["route_local_mm"][-1]
        if abs(first[0] - last[0]) > 100 and abs(first[1] - last[1]) < 1e-6:
            make_link(source["name"], first, last, "original_horizontal")
            endpoints[source["name"]] = set(source["name"].split("_")[2:])
    assert len(cables) == 21
    for source in extra["new_wire_routes"]:
        first, last = (
            copy.deepcopy(source["route_local_mm"][0]),
            copy.deepcopy(source["route_local_mm"][-1]),
        )
        first[2] = last[2] = CHANNEL_N
        make_link(source["id"], first, last, "unofficial_extra")
        endpoints[source["id"]] = set(source["endpoints"])
    assert len(cables) == 140
    target = "base_principal_center_right"
    raw_record = next(r for r in native["raw_parts"] if r["member"] == target)
    raw_principal = load(raw_record).translate((-39.2, 0, 0))
    old_cutters = [
        (
            r["name"],
            "wire",
            routing.front_open_cutter(
                r["route_local_mm"], r["placement_xyz_mm"], RADIUS
            ),
        )
        for r in aligned["wire_proposals"]
    ]
    old_rebuild, _ = service.cut_services(
        {target: raw_principal}, {target}, old_cutters
    )
    new_rebuild, base_cuts = service.cut_services(
        {target: raw_principal},
        {target},
        [r for r in old_cutters if r[0] not in f_names],
    )
    target_axes = [
        {
            **a,
            "point": cq.Vector(*a["point_xyz_mm"]),
            "direction": cq.Vector(*a["direction_xyz"]),
            "receivers": [target],
        }
        for a in base["axes"]
        if target in a["receivers"]
    ]
    old_principal = hardware.bore_wood(old_rebuild, target_axes)[target]
    new_principal = hardware.bore_wood(new_rebuild, target_axes)[target]
    assert abs(old_principal.Volume() - wood[target].Volume()) < 0.01
    assert overlaps(old_principal, wood[target]) >= wood[target].Volume() - 0.01
    restored_arc_volume = new_principal.Volume() - wood[target].Volume()
    assert restored_arc_volume > 0
    assert not any(r["service"] in f_names for r in base_cuts)
    prior_base_wood = wood.copy()
    wood[target] = new_principal
    print(
        "Built 140 flexible cable links; restoring principal arc cuts and using one smaller profile",
        flush=True,
    )
    finished, cuts = service.cut_services(wood, set(old_extra), cutters)
    # Unlike the earlier sideways loops, none of these routes needs a header cut.
    assert not any(r["receiver"] == "base_header" for r in cuts)
    assert all(r["kind"] == "wire" for r in cuts)
    retained_active = [r for r in retained if r[0] not in endpoints]
    assert len(retained_active) == 384
    grid = shared.grid()
    new_services = []
    for row in grid:
        x, s = row["tnut_x_s_mm"]
        plane = cq.Plane(
            origin=no_shoes_frame.b.point(x - no_shoes_frame.b.HALF, s, 0),
            xDir=(1, 0, 0),
            normal=-no_shoes_frame.b.normal(),
        )
        new_services.append(
            (
                "hold_tnut_2026_" + row["id"],
                "tnut",
                hold_tnut_reinforcement.local_shape().moved(plane.location),
            )
        )
        x, s = row["LED_x_s_mm"]
        new_services.append(
            (
                "light_2026_" + row["id"],
                "light",
                cq.Solid.makeCylinder(
                    6.35,
                    shared.THICKNESS + 12,
                    no_shoes_frame.b.point(
                        x - no_shoes_frame.b.HALF, s, -shared.THICKNESS
                    ),
                    no_shoes_frame.b.normal(),
                ),
            )
        )
    axes = [
        {
            **a,
            "point": cq.Vector(*a["point_xyz_mm"]),
            "direction": cq.Vector(*a["direction_xyz"]),
        }
        for a in base["axes"]
    ]
    metals = hardware.hardware(axes)
    bracket_scene = json.loads(
        gzip.decompress(Path("site/eoere-bottom-rail-scene.json.gz").read_bytes())
    )
    bracket_rows = {
        r["name"]: r
        for r in bracket_scene["solids"]
        if r["fabrication"]["kind"] == "bracket"
    }
    base_scene = json.loads(
        gzip.decompress(Path("site/eoere-adjusted-base-v3-scene.json.gz").read_bytes())
    )
    moved_brackets = {
        r["id"]: r for r in base["changed_finished_solids"] if r["kind"] == "bracket"
    }
    template = shared.fitting.template(shared.fitting.Scenario())
    for name, row in bracket_rows.items():
        if name in moved_brackets:
            body = load(moved_brackets[name])
        else:
            transform = row["transform"]
            plane = cq.Plane(
                origin=transform[12:15], xDir=transform[:3], normal=transform[8:11]
            )
            body = template.moved(plane.location)
        metals.append((name, "bracket", body))
    assert len(metals) == 522
    print(
        "Checking current hardware, cable crossings, bulbs and all changed timber",
        flush=True,
    )
    changed_wood = [(name, "timber", finished[name]) for name in old_extra]
    active_services = retained_active + new_services + cables
    collisions = {
        "base_services_vs_restored_principal": shared.pair_hits(
            [r for r in retained if r[0] not in f_names] + common_cables,
            [(target, "timber", wood[target])],
        ),
        "all_services_vs_revised_wood": shared.pair_hits(active_services, changed_wood),
        "new_cables_vs_all_metal": shared.pair_hits(cables, metals),
        "all_metal_vs_revised_wood": shared.pair_hits(metals, changed_wood),
    }
    contacts = shared.pair_hits(cables, retained_active + new_services)
    allowed_contacts, unintended = [], []
    for hit in contacts:
        node = hit["second"].removeprefix("light_2026_").removeprefix("light_")
        neighbor = (
            set(hit["second"].split("_")[2:]) if hit["second_role"] == "wire" else set()
        )
        (
            allowed_contacts
            if (hit["second_role"] == "light" and node in endpoints[hit["first"]])
            or endpoints[hit["first"]].intersection(neighbor)
            else unintended
        ).append(hit)
    collisions["new_cables_vs_unrelated_services"] = unintended
    new_pairs = shared.pair_hits(cables, cables)
    collisions["new_cables_vs_unrelated_cables"] = [
        r
        for r in new_pairs
        if r["first"] < r["second"]
        and not endpoints[r["first"]].intersection(endpoints[r["second"]])
    ]
    (out / "collision-register.json").write_text(
        json.dumps(collisions, indent=2) + "\n"
    )
    assert not any(collisions.values()), (
        "nominal collision: see collision-register.json"
    )
    body_rows = []
    replacements = {"common": [], "base": [], "extra": []}
    old_mesh_rows = {r["name"]: r for r in base_scene["replacements"]}
    extra_scene = json.loads(
        gzip.decompress(
            Path("site/eoere-2026-adjustments-v3-scene.json.gz").read_bytes()
        )
    )
    old_mesh_rows.update(
        {r["name"]: r for r in extra_scene["replacements"] + extra_scene["additions"]}
    )
    saves = [(name, kind, body, "common") for name, kind, body in common_cables]
    saves.append((target, "timber", wood[target], "base"))
    saves.extend(
        (name, "timber", finished[name], "extra") for name in sorted(old_extra)
    )
    saves.extend(
        (name, kind, body, "extra")
        for name, kind, body in cables
        if name not in f_names
    )
    for name, kind, body, variant in saves:
        (out / variant).mkdir(exist_ok=True)
        path = out / variant / (name + ".brep")
        assert body.exportBrep(str(path))
        saved = cq.Shape.importBrep(str(path))
        assert (
            saved.isValid()
            and len(saved.Solids()) == 1
            and abs(saved.Volume() - body.Volume()) < 0.001
        )
        bounds = shared.midpoint._bbox(saved)
        row = {
            "id": name,
            "kind": kind,
            "variant": variant,
            "path": str(path),
            "sha256": sha(path),
            "bytes": path.stat().st_size,
            "volume_mm3": saved.Volume(),
            "bounds_xyz_mm": bounds,
        }
        if kind == "timber":
            old = prior_base_wood[name] if variant == "base" else load(old_extra[name])
            row["previous_volume_mm3"] = old.Volume()
            row["restored_net_volume_mm3"] = saved.Volume() - old.Volume()
            assert row["restored_net_volume_mm3"] > -0.01
            assert overlaps(saved, wood[name]) >= saved.Volume() - 0.01
            row["base_volume_mm3"] = wood[name].Volume()
        body_rows.append(row)
        metadata = copy.deepcopy(
            old_mesh_rows.get(name, {}).get("fabrication", {"kind": kind})
        )
        metadata.update(
            {
                "uniform_channel_revision": REVISION,
                "description": "Smaller common cable channel; flexible links stand within the channel",
            }
        )
        replacements[variant].append(
            {
                "id": name,
                "name": name,
                "mesh": _shape_mesh(saved),
                "source_brep_sha256": row["sha256"],
                "fabrication": metadata,
            }
        )
    # Rebuilt header is byte-independent but geometrically identical to its base.
    assert abs(finished["base_header"].Volume() - wood["base_header"].Volume()) < 0.001
    verify()
    release = {key: False for key in parent["release"]}
    report = {
        "schema": "eoere_uniform_service_channels_geometry/v1",
        "revision": REVISION,
        "candidate": parent["candidate"],
        "status": "REVISE_UNEVALUATED_GEOMETRY",
        "parent_geometry": {"path": str(PARENT), "sha256": PARENT_SHA},
        "source_sha256": pins,
        "smaller_profile": {
            "wire_clearance_radius_mm": RADIUS,
            "channel_center_N_mm": CHANNEL_N,
            "front_width_mm": 2 * math.hypot(CHANNEL_N, RADIUS),
            "rear_depth_mm": CHANNEL_N + RADIUS,
            "revised_vertical_cable_N_mm": CHANNEL_N,
            "original_horizontal_cable_N_mm": CHANNEL_N,
            "extra_horizontal_cable_N_mm": LIFT_N,
            "modeled_cable_diameter_mm": 4,
            "machining_tolerance_or_bit_selected": False,
        },
        "base_geometry_unchanged": False,
        "optional_grid_unofficial": True,
        "axes": base["axes"],
        "screw_axes": base["screw_axes"],
        "axes_canonical_sha256": canonical(base["axes"]),
        "screw_axes_canonical_sha256": canonical(base["screw_axes"]),
        "changed_finished_solids": body_rows,
        "flexible_routes": route_records,
        "service_cuts": cuts,
        "depth_lifts": ramp_limits,
        "collisions": collisions,
        "intentional_LED_endpoint_contacts": allowed_contacts,
        "principal_arc_cuts": {
            "member": "base_principal_center_right",
            "removed_F_column_arc_cut_links": sorted(f_names),
            "base_restored_volume_mm3": restored_arc_volume,
            "existing_base_channel_retained": True,
            "no_new_header_channel": True,
        },
        "counts": parent["counts"],
        "base_changed_visible_parts": len(replacements["common"])
        + len(replacements["base"]),
        "base_unchanged_visible_parts": 1021
        - len(replacements["common"])
        - len(replacements["base"]),
        "extra_changed_visible_parts": len(replacements["common"])
        + len(replacements["extra"]),
        "extra_unchanged_visible_parts": 1380
        - len(replacements["common"])
        - len(replacements["extra"]),
        "cadquery_version": cq.__version__,
        "execution": {"command": sys.argv, "native_solver": False},
        "mechanics_ready": False,
        "analysis_pass_transferred": False,
        "release": release,
        "limits": [
            "Smaller existing cutter envelope, not a selected bit or tolerance.",
            "Flexible cable lifts and connector placement are nominal geometry; delivered routing, slack, bend radius and installation remain unverified.",
            "All bolt/screw axes unchanged; previous numerical evidence retains its geometry boundary.",
        ],
    }
    report_bytes = (json.dumps(report, indent=2, allow_nan=False) + "\n").encode()
    (out / "geometry.json").write_bytes(report_bytes)
    parent_scene_path = Path("site/eoere-cleat-extension-scene.json.gz")
    parent_bytes = parent_scene_path.read_bytes()
    pin(parent_scene_path)
    patch = {
        "schema": "eoere_uniform_service_channels_patch/v1",
        "revision": REVISION,
        "candidate": parent["candidate"],
        "status": report["status"],
        "parent_scene": {
            "url": parent_scene_path.name,
            "sha256": sha(parent_scene_path),
            "decoded_sha256": hashlib.sha256(gzip.decompress(parent_bytes)).hexdigest(),
            "layout_sha256": PARENT_SHA,
        },
        "layout_report": {
            "path": str(REPORT),
            "sha256": hashlib.sha256(report_bytes).hexdigest(),
        },
        "counts": parent["counts"],
        "base_geometry_unchanged": False,
        "optional_grid_unofficial": True,
        "smaller_profile": report["smaller_profile"],
        "common_replacements": replacements["common"],
        "base_replacements": replacements["base"],
        "extra_replacements": replacements["extra"],
        "triangle_topologies": _deduplicate_triangle_topologies(
            [r for v in replacements.values() for r in v]
        ),
        "mechanics_ready": False,
        "analysis_pass_transferred": False,
        "release": release,
    }
    encoded = (
        json.dumps(patch, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()
    with (
        (out / "scene.json.gz").open("xb") as stream,
        gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as zipped,
    ):
        zipped.write(encoded)
    verify()
    print(
        json.dumps(
            {
                "passed": True,
                "out": str(out),
                "base_replacements": report["base_changed_visible_parts"],
                "extra_replacements": report["extra_changed_visible_parts"],
                "scene_bytes": (out / "scene.json.gz").stat().st_size,
                "scene_sha256": sha(out / "scene.json.gz"),
                "decoded_sha256": hashlib.sha256(encoded).hexdigest(),
                "layout_sha256": hashlib.sha256(report_bytes).hexdigest(),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    build(parser.parse_args().out)
