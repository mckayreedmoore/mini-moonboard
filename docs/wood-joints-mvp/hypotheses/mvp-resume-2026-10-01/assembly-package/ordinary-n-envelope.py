#!/usr/bin/env python3
"""Project the frozen 108-stack installed planning inventory onto canonical N.

This standard-library calculation names source-frame diagnostics. It does not
adopt a station datum, an exception, hardware, geometry or criterion acceptance.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUT = HERE / "rawlocal" / "ordinary-n-envelope"
H = "docs/wood-joints-mvp/hypotheses"
R = f"{H}/mvp-resume-2026-10-01"
U = f"{R}/upper-corner-screw-layout"
A = f"{R}/assembly-package"
FILES = {
    "manifest": f"{U}/rawlocal/knee-bridge-working-package/attempt02/manifest.json",
    "setup": f"{A}/rawlocal/knee-bridge-fit/prepare-attempt02/setup.json",
    "order": f"{A}/rawlocal/working-order/attempt03/working-order.json",
    "axes": f"{A}/rawlocal/working-order/attempt03/working-order-axes.csv",
    "grip": f"{H}/evaluation-resume-2026-09-24/grip-screen-attempt02.json",
    "snapshot": f"{H}/evaluation-resume-2026-09-24/geometry-snapshot.json",
    "model": f"{U}/operators-attempt02/model-inputs.json",
    "engagement": f"{A}/hardware_engagement.py",
    "top": f"{R}/top-corner-hardware/hardware-inputs.json",
    "criteria": "docs/wood-joints-mvp/criteria.json",
    "inventory": "docs/wood-joints-mvp/source-inventory.json",
    "historical_block": f"{H}/evaluation-resume-2026-09-24/current-block-n-envelope-attempt01/README.md",
    "historical_outer": "docs/wood-joints-mvp/outer-node-result.md",
}
PINS = {
    "manifest": "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0",
    "setup": "794f1aa45fa9f47955f16a083a3637b2821615ede47640817305a60ddab4ddfb",
    "order": "6becf19a9b06f625b4292cc8cd60f908fd3bff8d865430e60abcec155af4e9be",
    "axes": "b5eb648c0e684f110efd6ec39700e1ba954bbea6642cff88dac6b8022b5cde5f",
    "grip": "9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a",
    "snapshot": "0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187",
    "model": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    "engagement": "d8e2a08e46fd9507a89d8e7ecb238ddf229490f4909345cbb641374ee8133295",
    "top": "a2110d7580621dee92017403345f21c458729612547ac1f7b2eb8068d0c723c7",
    "criteria": "fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784",
    "inventory": "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78",
    "historical_block": "f96806a1a97ce8bd7dc6ef4ba315932a32d0217794393dea01ca4b95cd77eedf",
    "historical_outer": "be2ffd9483bd96034d5417212db9f863de02a4e922904eeac1a214e88a47c7e3",
}
N = (0.0, -math.sin(math.radians(50.0)), math.cos(math.radians(50.0)))
REFERENCE_MM = 139.7
ROLES = ("shaft", "head", "head_washer", "nut_washer", "nut")
FALSE_CLAIMS = {
    "criterion_acceptance": False,
    "criterion_closed": False,
    "station_datum_adopted": False,
    "dimensioned_exception_adopted": False,
    "candidate_adopted": False,
    "delivered_hardware_verified": False,
    "physical_release": False,
    "fabrication_release": False,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_pins() -> dict[str, str]:
    actual = {}
    for name, expected in PINS.items():
        path = ROOT / FILES[name]
        if not path.is_file():
            raise ValueError(f"Missing pinned input: {FILES[name]}")
        got = sha256(path)
        if got != expected:
            raise ValueError(f"Input pin mismatch: {FILES[name]}: {got} != {expected}")
        actual[FILES[name]] = got
    return actual


def ref(name: str, pointer: str = "") -> dict:
    return {"path": FILES[name], "sha256": PINS[name], "record_pointer": pointer}


def read_json(name: str) -> dict:
    return json.loads((ROOT / FILES[name]).read_text(encoding="utf-8"))


def vector(values) -> list[float]:
    result = [float(v) for v in values]
    if len(result) != 3 or not all(math.isfinite(v) for v in result):
        raise ValueError(f"Invalid XYZ vector: {values!r}")
    return result


def unit(values) -> list[float]:
    result = vector(values)
    length = math.sqrt(sum(v * v for v in result))
    if abs(length - 1.0) > 1e-8:
        raise ValueError(f"Recorded axis is not a unit vector: {values!r}")
    return [v / length for v in result]


def dot(a, b) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def advance(point, direction, distance) -> list[float]:
    return [p + distance * d for p, d in zip(point, direction, strict=True)]


def bounds(values) -> list[float]:
    result = [float(v) for v in values]
    if len(result) != 6 or not all(math.isfinite(v) for v in result):
        raise ValueError(f"Invalid world bounding box: {values!r}")
    if any(result[2 * i] > result[2 * i + 1] for i in range(3)):
        raise ValueError(f"Inverted world bounding box: {values!r}")
    return result


def component(axis_id: str, role: str, geometry: dict, source: dict, limit: str) -> dict:
    kind = geometry["kind"]
    if kind == "cylinder":
        start = vector(geometry["start_xyz_mm"])
        direction = unit(geometry["direction_xyz"])
        length = float(geometry["length_mm"])
        radius = float(geometry["radius_mm"])
        if not math.isfinite(length + radius) or length <= 0 or radius <= 0:
            raise ValueError(f"Invalid cylinder dimensions: {axis_id}/{role}")
        geometry = {**geometry, "start_xyz_mm": start, "direction_xyz": direction}
        axial = [dot(N, start), dot(N, advance(start, direction, length))]
        radial = radius * math.sqrt(max(0.0, 1.0 - dot(N, direction) ** 2))
        low, high = min(axial) - radial, max(axial) + radial
    elif kind == "saved_world_aabb":
        box = bounds(geometry["bounds_xyz_mm"])
        geometry = {**geometry, "bounds_xyz_mm": box}
        low = sum(min(N[i] * box[2 * i], N[i] * box[2 * i + 1]) for i in range(3))
        high = sum(max(N[i] * box[2 * i], N[i] * box[2 * i + 1]) for i in range(3))
    else:
        raise ValueError(f"Unsupported projection geometry: {kind}")
    return {
        "component_id": f"{axis_id}/{role}", "axis_id": axis_id, "role": role,
        "geometry": geometry, "source": source, "geometry_limit": limit,
        "global_n_extrema_mm": [low, high],
        "exact_physical_part_projection": False,
    }


def cylinder(axis_id, role, start, direction, length, radius, source, limit) -> dict:
    return component(axis_id, role, {
        "kind": "cylinder", "start_xyz_mm": start, "direction_xyz": direction,
        "length_mm": length, "radius_mm": radius,
    }, source, limit)


def literal_stacks() -> dict:
    tree = ast.parse((ROOT / FILES["engagement"]).read_text(encoding="utf-8"))
    assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "STACKS"
                           for target in node.targets)]
    if len(assignments) != 1:
        raise ValueError("Expected one literal STACKS assignment; no module is imported")
    return ast.literal_eval(assignments[0].value)


def catalog_key(diameter: float) -> str:
    keys = {6.35: "qtr_kl", 7.9375: "five16", 9.525: "three8", 12.7: "half"}
    for nominal, key in keys.items():
        if abs(diameter - nominal) < 1e-6:
            return key
    raise ValueError(f"No frozen catalog stack for diameter {diameter}")


def build(output: str | Path) -> dict:
    """Write one fresh, source-pinned conditional report; return its receipt."""
    output = Path(output).resolve()
    if output.parent != OUT.resolve() or output.exists():
        raise ValueError("Output must be a fresh immediate child of rawlocal/ordinary-n-envelope")
    before = check_pins()
    producer = Path(__file__).resolve()
    producer_bytes = producer.read_bytes()
    producer_sha = hashlib.sha256(producer_bytes).hexdigest()
    manifest, setup, order = (read_json(name) for name in ("manifest", "setup", "order"))
    model, inventory = (read_json(name) for name in ("model", "inventory"))
    grip, snapshot, top = (read_json(name) for name in ("grip", "snapshot", "top"))
    criteria = read_json("criteria")
    criterion = next(row for row in criteria["additional_candidate_obligations"]
                     if row["id"] == "ordinary_n_envelope")
    if "139.7" not in criterion["requirement"] or "named datum" not in criterion["requirement"]:
        raise ValueError("Frozen ordinary-N requirement does not match the recorded definition")
    with (ROOT / FILES["axes"]).open(newline="", encoding="utf-8-sig") as handle:
        order_rows = list(csv.DictReader(handle))
    working = {row["axis_id"]: row for row in order_rows}
    existing = {row["axis_id"]: row for row in manifest["existing_bolt_axes"]}
    new = {row["axis_id"]: row for row in manifest["proposed_internal_bolt_axes"]}
    grips = {row["axis_id"]: (i, row) for i, row in enumerate(grip["axes"])}
    retained = {row["axis_id"]: (i, row) for i, row in enumerate(inventory["starting_frame_bolts"])}
    if len(order_rows) != 104 or len(working) != 104 or set(working) != set(existing):
        raise ValueError("Working order and current manifest must bind the same 104 axes")
    if len(grips) != 92 or set(grips) != set(snapshot["axes"]) or len(retained) != 12 or len(new) != 4:
        raise ValueError("Expected 92 candidate, 12 retained and four new internal axes")
    families = {row["family_id"]: row for row in order["families"]}
    family_counts = Counter(row["family_id"] for row in order_rows)
    for family_id, count in family_counts.items():
        if count != families[family_id]["axis_count"]:
            raise ValueError(f"Working family count differs: {family_id}")
    stacks = literal_stacks()
    head = top["catalog_parts"]["rail_bolt_grade5_lawson"]["head"]
    head_height = float(head["height"]["mm"]["maximum"])
    head_radius = float(head["across_flats"]["mm"]["maximum"]) / math.sqrt(3.0)
    parts = {row["part_id"]: (i, row) for i, row in enumerate(inventory["parts"])}
    members = {row["member_id"]: (i, row) for i, row in enumerate(model["members"])}
    body_rows = manifest["geometry"]["effective_members"]
    effective = {row["body"]: row for row in body_rows}
    blocks = {body for body, (_, row) in members.items()
              if "current_candidate_timber" in row["composition_roles"]}
    if len(body_rows) != 50 or len(effective) != 50 or set(effective) != set(members) or len(blocks) != 24:
        raise ValueError("Expected 50 effective body references and 24 connector bodies")

    datums = {}
    for body, (member_index, row) in members.items():
        if body in parts and parts[body][1].get("local_to_global_transform"):
            part_index, part = parts[body]
            transform = part["local_to_global_transform"]
            origin = vector([transform[i][3] for i in range(3)])
            basis = "source_inventory_host_frame_origin"
            name = part.get("local_datum", "source frame origin; local datum unlisted")
            source = ref("inventory", f"/parts/{part_index}/local_to_global_transform")
        else:
            start = row.get("reduced_geometry_descriptor", {}).get("start")
            origin = vector(start) if start is not None else None
            basis = "source_reduced_member_centerline_start_diagnostic"
            name = "reduced_geometry_descriptor.start; source centerline start"
            source = ref("model", f"/members/{member_index}/reduced_geometry_descriptor/start")
        datums[body] = {
            "datum_id": f"{body}/{basis}", "host_body": body, "name": name,
            "origin_xyz_mm": origin, "basis": basis, "source": source,
            "adopted_station_datum": False,
            "limit": "Named source datum candidate only; no current station-to-host datum mapping is adopted.",
        }

    components, axes, comparisons = [], [], []
    missing_datums = []

    def compare(kind, object_id, role, projection, receivers, geometry_basis):
        rows = []
        for receiver in dict.fromkeys(receivers):
            if receiver not in datums or datums[receiver]["origin_xyz_mm"] is None:
                missing_datums.append({"object_id": object_id, "receiver": receiver})
                continue
            datum = datums[receiver]
            shift = dot(N, datum["origin_xyz_mm"])
            low, high = projection[0] - shift, projection[1] - shift
            row = {
                "kind": kind, "object_id": object_id, "role": role,
                "receiver": receiver, "datum_id": datum["datum_id"],
                "datum_name": datum["name"], "datum_basis": datum["basis"],
                "datum_x_mm": datum["origin_xyz_mm"][0],
                "datum_y_mm": datum["origin_xyz_mm"][1],
                "datum_z_mm": datum["origin_xyz_mm"][2],
                "n_min_mm": low, "n_max_mm": high,
                "reference_upper_n_mm": REFERENCE_MM,
                "conditional_rearward_excess_mm": max(0.0, high - REFERENCE_MM),
                "geometry_basis": geometry_basis,
                "datum_adopted": False, "exception_adopted": False,
                "criterion_acceptance": False, "physical_exceedance_proved": False,
            }
            rows.append(row)
            comparisons.append(row)
        return rows

    def add_stack(axis_id, rows, receivers, info):
        if len(rows) != 5 or {row["role"] for row in rows} != set(ROLES):
            raise ValueError(f"Expected five unique installed roles: {axis_id}")
        rows.sort(key=lambda row: ROLES.index(row["role"]))
        components.extend(rows)
        low = min(row["global_n_extrema_mm"][0] for row in rows)
        high = max(row["global_n_extrema_mm"][1] for row in rows)
        for row in rows:
            compare("stack_component", row["component_id"], row["role"],
                    row["global_n_extrema_mm"], receivers, row["geometry"]["kind"])
        axis_comparisons = compare("axis_envelope", axis_id, "five_installed_roles",
                                   [low, high], receivers, "union_of_planning_components")
        axes.append({
            "axis_id": axis_id, "receivers": receivers,
            "component_ids": [row["component_id"] for row in rows],
            "global_n_extrema_mm": [low, high],
            "controlling_min_component_ids": [row["component_id"] for row in rows
                                               if abs(row["global_n_extrema_mm"][0] - low) < 1e-9],
            "controlling_max_component_ids": [row["component_id"] for row in rows
                                               if abs(row["global_n_extrema_mm"][1] - high) < 1e-9],
            "receiver_comparisons": axis_comparisons, "reconstruction": info,
            **FALSE_CLAIMS,
        })

    top_components = {}
    retained_boxes = {}
    for i, row in enumerate(setup["obstacles"]):
        if row["category"] == "corrected_top_component":
            top_components.setdefault(row["axis_id"], []).append((i, row))
        elif row["category"] == "retained_frame_bolt_roles":
            prefix = "retained_frame_bolt_roles/"
            axis_id, role = row["id"][len(prefix):].rsplit("/", 1)
            if role in retained_boxes.setdefault(axis_id, {}):
                raise ValueError(f"Duplicate retained obstacle role: {row['id']}")
            retained_boxes[axis_id][role] = (i, row)
    if len(top_components) != 8 or not set(top_components) <= set(grips) or set(retained_boxes) != set(retained):
        raise ValueError("Saved top-eight or retained-twelve obstacle census differs")

    for axis_id in sorted(existing):
        row = working[axis_id]
        receivers = existing[axis_id]["receivers"]
        diameter = float(row["diameter_mm"])
        length = float(row["working_profile_nominal_length_mm"])
        wood_grip = float(row["wood_grip_mm"])
        family = families[row["family_id"]]
        if abs(length - float(family["working_profile"]["nominal_length_mm"])) > 1e-6:
            raise ValueError(f"CSV/JSON working nominal length differs: {axis_id}")
        info = {
            "working_order": ref("axes"), "family_id": row["family_id"],
            "working_item": row["working_order_item"], "nominal_length_mm": length,
            "wood_grip_mm": wood_grip, "diameter_mm": diameter,
            "part_profile_or_thread_acceptance": False,
        }
        if axis_id in top_components:
            rows = [component(axis_id, saved["component"], {"kind": "cylinder", **saved["cylinder"]},
                              ref("setup", f"/obstacles/{i}"), saved["geometry_limit"])
                    for i, saved in top_components[axis_id]]
            shaft = next(c for c in rows if c["role"] == "shaft")
            if abs(shaft["geometry"]["length_mm"] - length) > 1e-6:
                raise ValueError(f"Top saved cylinder / nominal order length differs: {axis_id}")
            info["basis"] = "eight saved corrected-top installed catalog planning cylinders"
            info["rail_washers"] = "Existing four rail stacks retain two retail 25.4 mm OD by 2.5 mm washers each."
            add_stack(axis_id, rows, receivers, info)
            continue

        key = catalog_key(diameter)
        catalog = stacks[key]
        washer_t = max(catalog["washer"]["thickness_mm"])
        washer_r = max(catalog["washer"]["outside_diameter_mm"]) / 2.0
        nut_h = max(catalog["nut"]["height_mm"])
        nut_r = max(catalog["nut"]["across_flats_mm"]) / math.sqrt(3.0)
        info["catalog_stack"] = {"literal": ref("engagement", f"STACKS[{key!r}]"), **catalog}
        if axis_id in retained:
            inventory_index, saved_axis = retained[axis_id]
            direction = unit(saved_axis["axis_global_xyz"])
            if abs(abs(direction[0]) - 1.0) > 1e-12 or abs(direction[1]) + abs(direction[2]) > 1e-12:
                raise ValueError(f"Retained source axis is not pure +/-X: {axis_id}")
            saved = retained_boxes[axis_id]
            if set(saved) != set(ROLES):
                raise ValueError(f"Retained box roles differ: {axis_id}")
            shaft_box = bounds(saved["shaft"][1]["bounds_xyz_mm"])
            washer_box = bounds(saved["head_washer"][1]["bounds_xyz_mm"])
            near_x, far_x = ((shaft_box[0], shaft_box[1]) if direction[0] > 0
                             else (shaft_box[1], shaft_box[0]))
            source_underhead = [near_x, (shaft_box[2] + shaft_box[3]) / 2.0,
                                (shaft_box[4] + shaft_box[5]) / 2.0]
            source_tip = [far_x, source_underhead[1], source_underhead[2]]
            wood_face = [washer_box[1] if direction[0] > 0 else washer_box[0],
                         source_underhead[1], source_underhead[2]]
            underhead = advance(wood_face, direction, -washer_t)
            head_index, head_row = saved["head"]
            shift = [a - b for a, b in zip(underhead, source_underhead, strict=True)]
            head_box = bounds(head_row["bounds_xyz_mm"])
            head_box = [value + shift[i // 2] for i, value in enumerate(head_box)]
            head_component = component(axis_id, "head", {
                "kind": "saved_world_aabb", "bounds_xyz_mm": head_box,
                "translation_xyz_mm": shift,
            }, ref("setup", f"/obstacles/{head_index}"),
                "Saved modeled head AABB translated with the head-washer change; catalog AF/height unsupported, not a product bound.")
            info.update({
                "basis": "pure-X saved padded shaft/washer bounds and rebuilt catalog nut/washer maxima",
                "source_axis": ref("inventory", f"/starting_frame_bolts/{inventory_index}"),
                "source_padded_shaft_endpoints_xyz_mm": [source_underhead, source_tip],
                "source_padded_shaft_length_mm": abs(far_x - near_x),
                "source_recorded_occupied_length_mm": saved_axis["source_occupied_length_mm"],
                "source_head_washer_bounds_xyz_mm": washer_box,
                "source_head_wood_face_xyz_mm": wood_face,
                "source_bound_padding_limit": "Saved exported AABBs include approximately 0.001 mm inflation per boundary. Endpoints and wood-face point retain that padding; they are not exact bearing surfaces.",
                "catalog_head_dimensions_supported": False,
            })
        else:
            grip_index, saved_axis = grips[axis_id]
            direction = unit(saved_axis["axis_head_to_nut_global_unit"])
            center = vector(saved_axis["frozen_shaft_center_xyz_mm"])
            source_length = float(saved_axis["modeled_underhead_to_tip_mm"])
            snapshot_axis = snapshot["axes"][axis_id]
            if any(abs(a - b) > 1e-7 for a, b in zip(center, snapshot_axis["shaft_center_xyz_mm"], strict=True)):
                raise ValueError(f"Saved candidate shaft center differs: {axis_id}")
            if any(abs(a - b) > 1e-7 for a, b in zip(direction, snapshot_axis["axis_head_to_nut_global"], strict=True)):
                raise ValueError(f"Saved candidate axis direction differs: {axis_id}")
            source_underhead = advance(center, direction, -source_length / 2.0)
            interval = saved_axis["hardware_roles"]["head_washer"]["projection_envelope_from_underhead_mm"]
            source_t = float(interval[1]) - float(interval[0])
            if abs(float(interval[0])) > 1e-6:
                raise ValueError(f"Source head washer does not start at underhead: {axis_id}")
            wood_face = advance(source_underhead, direction, source_t)
            underhead = advance(source_underhead, direction, -(washer_t - source_t))
            head_component = cylinder(axis_id, "head", underhead, [-d for d in direction],
                                      head_height, head_radius, ref("top", "/catalog_parts/rail_bolt_grade5_lawson/head"),
                                      "Conditional 1/4-in B18.2.1 maximum-height/circumscribed regular-hex profile; not delivered item-specific head conformity.")
            info.update({
                "basis": "frozen shaft center and source modeled length; catalog thickness shift keeps source wood face fixed",
                "source_grip_axis": ref("grip", f"/axes/{grip_index}"),
                "source_geometry_axis": ref("snapshot", f"/axes/{axis_id}"),
                "source_underhead_xyz_mm": source_underhead,
                "source_modeled_underhead_to_tip_mm": source_length,
                "source_head_washer_thickness_mm": source_t,
                "catalog_minus_source_head_washer_thickness_mm": washer_t - source_t,
                "source_head_wood_face_xyz_mm": wood_face,
            })
        info["planning_underhead_xyz_mm"] = underhead
        nut_wood_face = advance(wood_face, direction, wood_grip)
        catalog_source = ref("engagement", f"STACKS[{key!r}]")
        rows = [
            cylinder(axis_id, "shaft", underhead, direction, length, diameter / 2.0,
                     ref("axes"), "Nominal working under-head length and diameter only; no delivered shank/thread/profile conformity."),
            head_component,
            cylinder(axis_id, "head_washer", underhead, direction, washer_t, washer_r,
                     catalog_source, "Catalog maximum outer-disk/thickness planning enclosure; hole and actual bearing excluded."),
            cylinder(axis_id, "nut_washer", nut_wood_face, direction, washer_t, washer_r,
                     catalog_source, "Catalog maximum outer-disk/thickness at nominal working wood grip; no partial-seat or bearing acceptance."),
            cylinder(axis_id, "nut", advance(nut_wood_face, direction, washer_t), direction, nut_h, nut_r,
                     catalog_source, "Catalog maximum-height/circumscribed regular-hex planning cylinder; no thread engagement or delivered profile acceptance."),
        ]
        add_stack(axis_id, rows, receivers, info)

    aliases = {row["fit_axis_id"]: row["canonical_axis_id"] for row in manifest["axis_aliases"]}
    new_components = {}
    for i, row in enumerate(setup["queries"]):
        installed = ((row["component"] == "shaft" and row["operation"] == "installed_165.1_mm_stock")
                     or (row["component"] in ROLES[1:] and row["operation"] == "installed"))
        if installed:
            axis_id = aliases[row["axis_id"]]
            new_components.setdefault(axis_id, []).append(component(
                axis_id, row["component"], {"kind": "cylinder", **row["cylinder"]},
                ref("setup", f"/queries/{i}"), row["geometry_limit"]))
    if set(new_components) != set(new):
        raise ValueError("Four canonical internal axes do not match installed query aliases")
    for axis_id in sorted(new):
        rows = new_components[axis_id]
        if abs(next(c for c in rows if c["role"] == "shaft")["geometry"]["length_mm"] - 165.1) > 1e-6:
            raise ValueError(f"New installed stock is not 165.1 mm: {axis_id}")
        add_stack(axis_id, rows, new[axis_id]["receivers"], {
            "basis": "saved four new installed 165.1 mm stock component cylinders",
            "fit_axis_id": new[axis_id]["fit_axis_id"], "nominal_length_mm": 165.1,
            "excluded": "203.2 mm sensitivity, duplicate tip/bound cylinders and all removal/tool sweeps",
            "datum_policy": "Own receiver source centerline-start diagnostic; no station datum adopted.",
        })

    screws = []
    for i, row in enumerate(model["connections"]):
        if row["kind"] != "panel_screw":
            continue
        record = row["source_record"]
        length = float(record["purchased_nominal_length_mm"])
        if abs(length - 63.5) > 1e-6:
            raise ValueError(f"Purchased-policy screw length differs: {row['axis_id']}")
        screw = cylinder(row["axis_id"], "screw_occupancy", record["origin_global_xyz_mm"],
                         record["axis_global_xyz"], length, 4.1402 / 2.0,
                         ref("model", f"/connections/{i}/source_record"),
                         "Hillman 42605 purchased nominal 63.5 mm by recorded 4.1402 mm occupied diameter; complete purchased head/profile unavailable and not inherited from modeled source head.")
        screw["receivers"] = row["receiver_member_ids"]
        screw["current_location_status"] = record["current_location_status"]
        screw["receiver_comparisons"] = compare("screw_component", screw["component_id"], screw["role"],
                                                screw["global_n_extrema_mm"], screw["receivers"], "cylinder")
        screws.append(screw)

    hosts = {body: set() for body in blocks}
    for row in existing.values():
        for body in set(row["receivers"]) & blocks:
            hosts[body].update(set(row["receivers"]) - blocks)
    connector_rows, effective_rows = [], []
    for i, row in enumerate(body_rows):
        body = row["body"]
        box = bounds(row["source_bounds_xyz_mm"])
        limit = "Frozen manifest source world enclosure; referenced effective STEP is not loaded or independently bounded here. Projection is conservative and is not exact physical exceedance."
        if body in {"top_outer_left_cleat", "top_outer_right_cleat"}:
            limit += " Corrected top STEP reference supersedes the older reduced descriptor; source descriptor/start and saved enclosure do not authenticate corrected finished extents."
        if row["effective_proposal_step"] != row["current_step"]:
            limit += " Effective proposal STEP differs from the source STEP; saved source bounds remain an enclosure reference, not a freshly measured effective BRep bound."
        effective_rows.append({**row, "source_bounds_xyz_mm": box, "bounds_limit": limit,
                               "manifest_reference": ref("manifest", f"/geometry/effective_members/{i}"),
                               "effective_step_loaded": False})
        if body not in blocks:
            continue
        connector = component(body, "connector_body_enclosure", {
            "kind": "saved_world_aabb", "bounds_xyz_mm": box,
        }, ref("manifest", f"/geometry/effective_members/{i}"), limit)
        receiver_ids = sorted(hosts[body]) or [body]
        connector["host_datum_policy"] = ("linked nonblock hosts from current existing bolt receivers"
                                            if hosts[body] else "own source centerline-start fallback; no linked nonblock host")
        connector["receivers"] = receiver_ids
        connector["effective_member_reference"] = row
        connector["receiver_comparisons"] = compare("connector_body", body, "connector_body_enclosure",
                                                    connector["global_n_extrema_mm"], receiver_ids,
                                                    "saved_world_aabb")
        connector_rows.append(connector)

    role_counts = Counter(row["role"] for row in components)
    if len(axes) != 108 or len({row["axis_id"] for row in axes}) != 108 or len(components) != 540:
        raise ValueError("Installed bolt-stack count does not reconcile to 108 by five roles")
    if role_counts != Counter({role: 108 for role in ROLES}) or len(screws) != 66 or len(connector_rows) != 24:
        raise ValueError("Installed role, screw or connector census differs")
    if len({row["axis_id"] for row in screws}) != 66:
        raise ValueError("Duplicate screw axes")
    summary_rows = [row for row in comparisons if row["kind"] != "stack_component"]
    conditional_excesses = [row for row in summary_rows if row["conditional_rearward_excess_mm"] > 0.0]

    def extrema(rows):
        if not rows:
            return {"n_min_mm": None, "n_max_mm": None, "controlling_min": [], "controlling_max": []}
        low = min(row["n_min_mm"] for row in rows)
        high = max(row["n_max_mm"] for row in rows)
        return {"n_min_mm": low, "n_max_mm": high,
                "controlling_min": [row for row in rows if abs(row["n_min_mm"] - low) < 1e-9],
                "controlling_max": [row for row in rows if abs(row["n_max_mm"] - high) < 1e-9]}

    unsupported = [
        {"fact": "No adopted current station-to-host datum mapping for the 108-stack proposal.",
         "affects": "Every comparison; conditional excess cannot close N17 or adopt an exception."},
        {"fact": "Retained 3/8-in Bolt Depot 367/368 head maximum AF and height are not machine-readable supported catalog facts in these frozen inputs.",
         "affects": sorted(a for a in retained if working[a]["family_id"].startswith("retained_rail_")),
         "route": "Saved modeled head AABB proxy, translated with catalog washer thickness; not a purchased-product enclosure."},
        {"fact": "Retained 1/2-in Bolt Depot 407 head maximum AF and height are not machine-readable supported catalog facts in these frozen inputs.",
         "affects": sorted(a for a in retained if working[a]["family_id"] == "retained_lumber_leg_4"),
         "route": "Saved modeled head AABB proxy, translated with catalog washer thickness; not a purchased-product enclosure."},
        {"fact": "Hillman 42605 complete purchased screw-head, countersunk seat and body/thread profile envelope is unavailable.",
         "affects": "All 66 screw projections; only the nominal purchased-length occupancy cylinder is represented."},
        {"fact": "Nominal working bolt lengths and conditional regular-hex/nut/washer dimensions are not delivered shank, thread, tolerances, profile or bearing observations.",
         "affects": "All 108 stacks, including central partial nut seat; no nut/thread/tool sequence acceptance."},
        {"fact": "Manifest body bounds are saved source enclosures, not newly authenticated exact effective STEP projections.",
         "affects": "All 24 connector projections, with corrected-top descriptor and effective knee-STEP limitations stated on their rows."},
    ]
    report = {
        "schema": "ordinary_n_installed_planning_envelope/v1",
        "status": "conditional_source_datum_diagnostics_only",
        "definition": {
            "canonical_n_global_xyz": list(N), "reference_upper_n_mm": REFERENCE_MM,
            "criterion": criterion, "criterion_source": ref("criteria"),
            "definition_provenance": [ref("historical_block"), ref("historical_outer")],
            "missing_definition": unsupported[0]["fact"],
            "frontward_limit_adopted": False,
            "coordinate_rule": "n = N dot (global point - each named receiver source datum); compare upper coordinate to 139.7 mm, not part length or span.",
            "cylinder_rule": "endpoint extrema +/- radius * sqrt(1 - (N dot unit axis)^2)",
            "aabb_rule": "conservative extrema of the saved world-axis enclosure; no BRep or collision proof",
        },
        "counts": {
            "existing_axes": 104, "proposed_internal_axes": 4, "bolt_axes": 108,
            "bolt_shafts": role_counts["shaft"], "bolt_heads": role_counts["head"],
            "nuts": role_counts["nut"], "washers": role_counts["head_washer"] + role_counts["nut_washer"],
            "stack_components": len(components), "purchased_policy_screws": len(screws),
            "effective_bodies": len(effective_rows), "connector_enclosures": len(connector_rows),
            "comparison_rows": len(comparisons),
        },
        "working_families": [{"family_id": key, "axis_count": count, "source": families[key]}
                             for key, count in sorted(family_counts.items())],
        "datum_candidates": list(datums.values()), "missing_source_datum_candidates": missing_datums,
        "components": components, "axes": axes, "screws": screws,
        "effective_bodies": effective_rows, "connectors": connector_rows,
        "comparisons": comparisons,
        "receiver_relative_extrema": {kind: extrema([row for row in summary_rows if row["kind"] == kind])
                                     for kind in ("axis_envelope", "screw_component", "connector_body")},
        "conditional_exception_candidates": conditional_excesses,
        "conditional_exception_candidate_count": len(conditional_excesses),
        "unsupported_facts": unsupported,
        "excluded_scope": ["203.2 mm new-knee sensitivity", "withdrawal, counterhold and tool sweeps",
                           "exact physical head/thread fit", "complete nut/tool/thread sequence acceptance",
                           "collision proof", "viewer mesh", "mechanics or frame acceptance"],
        "source_sha256": before, "producer_sha256": producer_sha,
        "tests_run": False, "native_or_CAD_or_frame_run": False,
        **FALSE_CLAIMS,
    }
    after = check_pins()
    if before != after or sha256(producer) != producer_sha:
        raise ValueError("Producer or frozen input bytes changed during calculation")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n", encoding="utf-8")
    (output / "producer.py.snapshot").write_bytes(producer_bytes)
    (output / "envelope.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    with (output / "comparisons.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparisons[0]))
        writer.writeheader()
        writer.writerows(comparisons)
    final = check_pins()
    if final != before or sha256(producer) != producer_sha:
        raise ValueError("Producer or frozen input bytes changed while writing output")
    receipt = {
        "schema": "ordinary_n_installed_planning_envelope_receipt/v1",
        "output": output.relative_to(ROOT).as_posix(), "counts": report["counts"],
        "producer": {"path": producer.relative_to(ROOT).as_posix(), "sha256": producer_sha},
        "source_sha256_before": before, "source_sha256_after": final,
        "source_pins_unchanged": before == final,
        "output_sha256": {name: sha256(output / name) for name in
                          ("envelope.json", "comparisons.csv", "producer.py.snapshot", ".gitignore")},
        "missing_source_datum_candidates": missing_datums,
        "conditional_exception_candidate_count": len(conditional_excesses),
        "tests_run": False, "native_or_CAD_or_frame_run": False,
        **FALSE_CLAIMS,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path,
                        help="Fresh immediate child of assembly-package/rawlocal/ordinary-n-envelope")
    args = parser.parse_args()
    receipt = build(args.output)
    print(json.dumps({"output": receipt["output"], "counts": receipt["counts"],
                      "output_sha256": receipt["output_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
