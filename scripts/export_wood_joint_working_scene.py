"""Export the frozen, unadopted wood-joint proposal for the main viewer.

Only six saved STEP solids are imported and tessellated. The remaining WJ24
meshes and topology records are retained. Hardware meshes are display envelopes
from the bound planning records; this exporter performs no CAD reconstruction,
collision query, force calculation, or fabrication-authority change.
"""

from __future__ import annotations

import argparse
import base64
import copy
import csv
import hashlib
import json
import math
import struct
import sys
from array import array
from pathlib import Path
from types import SimpleNamespace

from scripts.export_wood_joint_design_review_scene import _mesh_with_topology_reference
from scripts.export_wood_joint_wj24_scene import _shape_mesh

ROOT = Path(__file__).resolve().parents[1]
PACKET = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01"
UPPER = f"{PACKET}/upper-corner-screw-layout"
SCHEMA = "wood_joint_working_proposal_scene/v1"
OUTPUT = "site/owner-wood-joints-working-scene.json"
PARENT = "site/owner-wood-joints-wj24-scene.json"
MANIFEST = f"{UPPER}/rawlocal/knee-bridge-working-package/attempt02/manifest.json"
TOP = f"{PACKET}/top-corner-correction/proposal.json"
HARDWARE = f"{PACKET}/top-corner-hardware/hardware-inputs.json"
MODEL = f"{UPPER}/operators-attempt02/model-inputs.json"
TOP_FIT = f"{PACKET}/assembly-package/rawlocal/top-washer-fit/prepare-attempt02/setup.json"
BRIDGE_FIT = f"{PACKET}/assembly-package/rawlocal/knee-bridge-fit/prepare-attempt02/setup.json"
SHOP_RECEIPT = f"{UPPER}/rawlocal/shop-axes/receipt.json"
SHOP_AXES = f"{UPPER}/rawlocal/shop-axes/axes.csv"
PINS = {
    PARENT: "74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf",
    MANIFEST: "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0",
    TOP: "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
    HARDWARE: "a2110d7580621dee92017403345f21c458729612547ac1f7b2eb8068d0c723c7",
    MODEL: "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    TOP_FIT: "d5b885bf3e023ca4efdcecd219453a288294d264692beb4d4bce100702928128",
    BRIDGE_FIT: "794f1aa45fa9f47955f16a083a3637b2821615ede47640817305a60ddab4ddfb",
    SHOP_RECEIPT: "535bcdaeb85ed683e66040c8042dd6c3bdea7d835ca7a9d7c510de99d6cf773d",
    SHOP_AXES: "46406c559d1f427ad4422edf033759831a83d0ddcef4bbb871579da132853eca",
}
TIMBERS = (
    "base_side_left", "base_side_right", "top_outer_left_cleat",
    "top_outer_right_cleat", "knee_outer_left_spine", "knee_outer_right_spine",
)
STACK_ROLES = ["head", "head_washer", "shaft", "nut_washer", "nut"]
CENSUS = {
    "bodies": 50, "blocks": 24, "bolts": 108, "nuts": 108,
    "washers": 216, "panel_kicker_screws": 66,
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _bound_bytes(path: str, digest: str, sources: dict) -> bytes:
    raw = (ROOT / path).read_bytes()
    if _sha(raw) != digest:
        raise ValueError(f"frozen display source changed: {path}")
    sources[path] = digest
    return raw


def _bound_json(path: str, digest: str, sources: dict) -> dict:
    return json.loads(_bound_bytes(path, digest, sources))


def _add(a, b, scale=1.0):
    return [float(x) + scale * float(y) for x, y in zip(a, b, strict=True)]


def _dot(a, b):
    return sum(float(x) * float(y) for x, y in zip(a, b, strict=True))


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _unit(a):
    length = math.sqrt(_dot(a, a))
    if not math.isfinite(length) or length <= 0:
        raise ValueError("display cylinder needs a finite nonzero direction")
    return [float(x) / length for x in a]


class _EnvelopeMesh:
    """Small analytic display mesh accepted by the existing typed-array quantizer."""

    def __init__(self, cylinder: dict, inside_diameter=0.0):
        start = cylinder["start_xyz_mm"]
        direction = _unit(cylinder["direction_xyz"])
        radius, length = float(cylinder["radius_mm"]), float(cylinder["length_mm"])
        inside = float(inside_diameter) / 2
        if not 0 <= inside < radius or length <= 0:
            raise ValueError("invalid display cylinder or annulus")
        seed = [0.0, 0.0, 1.0] if abs(direction[2]) < .9 else [1.0, 0.0, 0.0]
        first = _unit(_cross(seed, direction))
        second = _cross(direction, first)
        count = 48
        points = []
        for r in ([radius, inside] if inside else [radius]):
            for station in (0.0, length):
                for i in range(count):
                    angle = 2 * math.pi * i / count
                    radial = _add([v * r * math.cos(angle) for v in first], second,
                                  r * math.sin(angle))
                    points.append(_add(_add(start, direction, station), radial))
        triangles = []
        for i in range(count):
            following = (i + 1) % count
            triangles.extend(((i, following, count + following),
                              (i, count + following, count + i)))
            if inside:
                ib, it = 2 * count, 3 * count
                triangles.extend(((ib + i, it + following, ib + following),
                                  (ib + i, it + i, it + following),
                                  (i, ib + following, following),
                                  (i, ib + i, ib + following),
                                  (count + i, count + following, it + following),
                                  (count + i, it + following, it + i)))
        if not inside:
            points.extend((list(start), _add(start, direction, length)))
            for i in range(count):
                following = (i + 1) % count
                triangles.extend(((2 * count, following, i),
                                  (2 * count + 1, count + i, count + following)))
        self.points, self.triangles = points, triangles

    def copy(self):
        return self

    def tessellate(self, _tolerance):
        return [SimpleNamespace(toTuple=lambda p=p: tuple(p)) for p in self.points], self.triangles

    def BoundingBox(self):
        return SimpleNamespace(**{
            f"{axis}{extreme}": reducer(p[i] for p in self.points)
            for i, axis in enumerate("xyz") for extreme, reducer in (("min", min), ("max", max))
        })


def _mesh_vertices(mesh: dict):
    values = array("h" if mesh["vertex_component_type"] == "int16" else "i")
    values.frombytes(base64.b64decode(mesh["vertices_base64"], validate=True))
    if sys.byteorder != "little":
        values.byteswap()
    scale = mesh["vertex_quantization_mm"]
    return [(values[i] * scale, values[i + 1] * scale, values[i + 2] * scale)
            for i in range(0, len(values), 3)]


def _mesh_bounds(mesh: dict):
    vertices = _mesh_vertices(mesh)
    return [[min(p[i] for p in vertices) for i in range(3)],
            [max(p[i] for p in vertices) for i in range(3)]]


def _display_bounds(scene: dict, baseline: dict) -> list:
    """Union rendered quantized vertices and visible, translated baseline STL vertices."""
    low, high = [math.inf] * 3, [-math.inf] * 3

    def include(point, translation=(0.0, 0.0, 0.0)):
        for i in range(3):
            value = float(point[i]) + translation[i]
            low[i], high[i] = min(low[i], value), max(high[i], value)

    for row in scene["solids"]:
        for point in _mesh_vertices(row["mesh"]):
            include(point)
    aliases = json.loads((ROOT / "site/mesh-aliases.json").read_bytes())["aliases"]
    hidden = set(scene["hidden_baseline_visual_names"])
    for row in baseline["parts"]:
        if row["name"] in hidden:
            continue
        path = row["path"]
        resolved, seen = path, set()
        while not (ROOT / "site" / resolved).is_file():
            if resolved in seen or resolved not in aliases:
                raise ValueError(f"missing baseline display mesh: {path}")
            seen.add(resolved)
            resolved = aliases[resolved]
        raw = (ROOT / "site" / resolved).read_bytes()
        if _sha(raw) != scene["baseline_asset_sha256"][path]:
            raise ValueError(f"baseline display asset changed: {path}")
        translation = scene["baseline_display_translations_mm"].get(row["name"], (0, 0, 0))
        if len(raw) >= 84 and len(raw) == 84 + 50 * struct.unpack_from("<I", raw, 80)[0]:
            for triangle in struct.iter_unpack("<12fH", raw[84:]):
                for index in (3, 6, 9):
                    include(triangle[index:index + 3], translation)
        else:
            vertex_count = 0
            for line in raw.decode("ascii").splitlines():
                words = line.split()
                if words and words[0] == "vertex" and len(words) == 4:
                    include([float(value) for value in words[1:]], translation)
                    vertex_count += 1
            if not vertex_count:
                raise ValueError(f"baseline STL has no readable vertices: {path}")
    return [low, high]


def _fabrication(row: dict, model_members: dict, axis_rows: dict) -> dict:
    bounds = _mesh_bounds(row["mesh"])
    dimensions = [bounds[1][i] - bounds[0][i] for i in range(3)]
    if row["display_class"] == "candidate_hardware":
        axis_id, role = row["axis_id"], row["id"].rsplit("/", 1)[1]
        source = axis_rows[axis_id]
        direction, origin = _unit(source["axis_xyz"]), source["axis_point_xyz_mm"]
        vertices = _mesh_vertices(row["mesh"])
        stations = [_dot(_add(point, origin, -1), direction) for point in vertices]
        radii = [math.sqrt(max(0.0, _dot(_add(point, origin, -1),
                                       _add(point, origin, -1)) - station * station))
                 for point, station in zip(vertices, stations, strict=True)]
        diameter = 2 * max(radii)
        return {"kind": "bolt", "category": "bolts", "dimensions_mm": [diameter, diameter, max(stations) - min(stations)],
                "inside_diameter_mm": 2 * min(radii) if role in ("head_washer", "nut_washer") else None,
                "connection_name": axis_id, "hardware_role": role, "stack_roles": STACK_ROLES,
                "description": "Preserved source occupancy mesh; dimensions are projected quantized display extents, not planned stock or delivered hardware.",
                "clearance_status": "Unadopted proposal display; exact collision geometry is not established"}
    kind = "panel" if row["display_class"] == "panel_replacement" else "timber"
    if row["display_class"] == "electrical_replacement":
        kind = "light" if row["id"].startswith("light_") else "wire"
    member = model_members.get(row["id"])
    if member:
        kind = "panel" if member["member_kind"] in ("panel", "plywood") else "timber"
        descriptor = member.get("reduced_geometry_descriptor", {})
        dimensions = [descriptor.get(key, dimensions[i]) for i, key in enumerate(("length_mm", "width_mm", "depth_mm"))]
    return {"kind": kind, "category": {"panel": "panels", "timber": "timber", "light": "lights", "wire": "wiring"}[kind],
            "dimensions_mm": dimensions, "description": "Source-bound proposal display; no physical cutting or assembly release",
            "clearance_status": "Unadopted proposal display; exact collision geometry is not established"}


def build_scene() -> dict:
    sources = {}
    documents = {path: _bound_json(path, digest, sources) for path, digest in PINS.items() if path != SHOP_AXES}
    _bound_bytes(SHOP_AXES, PINS[SHOP_AXES], sources)
    base, manifest, top, catalog, model = [documents[path] for path in (PARENT, MANIFEST, TOP, HARDWARE, MODEL)]
    top_fit, bridge_fit, shop = [documents[path] for path in (TOP_FIT, BRIDGE_FIT, SHOP_RECEIPT)]
    if len(base["solids"]) != 508 or base["schema"] != "owner_wood_joints_design_review_scene/v1":
        raise ValueError("preserved WJ24 parent must contain its original 508 meshes")
    if manifest["proposal_adopted"] is not False or manifest["physical_release"] is not False:
        raise ValueError("working manifest must retain its unadopted, unreleased status")
    if {key: manifest["census"][key] for key in CENSUS if key != "panel_kicker_screws"} != {key: value for key, value in CENSUS.items() if key != "panel_kicker_screws"} or manifest["census"]["Hillman_screws"] != 66:
        raise ValueError("frozen proposal census differs")
    members = {row["body"]: row for row in manifest["geometry"]["effective_members"]}
    if len(members) != 50:
        raise ValueError("effective STEP source inventory must contain 50 distinct bodies")
    bindings = {}
    for name, member in sorted(members.items()):
        binding = member["effective_proposal_step"]
        _bound_bytes(binding["path"], binding["sha256"], sources)
        bindings[name] = copy.deepcopy(binding)
    order_ref = manifest["planning_order"]["source"]
    order = _bound_json(order_ref["source"], order_ref["sha256"], sources)
    if order["proposed_counts"] != {"Hillman_screws": 66, "bolts": 108, "nuts": 108, "washers": 216}:
        raise ValueError("planning-order census differs from the frozen proposal")
    baseline = _bound_json(base["baseline_manifest_path"], base["baseline_manifest_sha256"], sources)
    scene = copy.deepcopy(base)
    solids = {row["id"]: row for row in scene["solids"]}
    topologies = scene["triangle_topologies"]
    axis_rows = {row["axis_id"]: row for row in manifest["existing_bolt_axes"]}
    model_members = {row["member_id"]: row for row in model["members"]}
    for row in solids.values():
        row["fabrication"] = _fabrication(row, model_members, axis_rows)
        row["display_mesh_origin"] = "preserved_parent_quantized_mesh"
        row["exact_collision_geometry"] = False
        if row["id"] in bindings:
            row["effective_step_source_binding"] = bindings[row["id"]]
    # The sole CAD operation is display tessellation of these six already saved solids.
    import cadquery as cq

    for name in TIMBERS:
        shape = cq.importers.importStep(str(ROOT / bindings[name]["path"])).val().copy()
        solids[name]["mesh"] = _mesh_with_topology_reference(_shape_mesh(shape), topologies)
        solids[name]["display_mesh_origin"] = "frozen_effective_STEP_display_tessellation"
        solids[name]["visual_status"] = "Frozen proposal STEP display; quantized surface approximation only"
    for proposal in top["proposals"]:
        solids[proposal["block"]]["fabrication"]["dimensions_mm"] = [proposal["grain_length_mm"], *proposal["proposed_section_X_T_mm"]]

    changed_top, added_bridge = [], []

    def hardware(axis_id, component, cylinder, inside=0.0, *, family, references, nominal_af=None):
        name = f"{axis_id}/{component}"
        mesh = _mesh_with_topology_reference(_shape_mesh(_EnvelopeMesh(cylinder, inside)), topologies)
        dimensions = [2 * cylinder["radius_mm"], 2 * cylinder["radius_mm"], cylinder["length_mm"]]
        row = solids.get(name, {"id": name, "name": name, "axis_id": axis_id,
                              "display_class": "candidate_hardware", "role": f"candidate_hardware_occupancy/{component}",
                              "family": family, "station_id": axis_id.split("/")[1]})
        row.update(mesh=mesh, collision_envelope=False, exact_collision_geometry=False,
                   display_mesh_origin="bound_planning_envelope_display_mesh",
                   visual_status="Planning display envelope; not an observed or delivered hardware profile",
                   display_geometry={"cylinder": cylinder, "inside_diameter_mm": inside,
                                     "source_references": references},
                   fabrication={"kind": "bolt", "category": "bolts", "dimensions_mm": dimensions,
                                "connection_name": axis_id, "hardware_role": component, "stack_roles": STACK_ROLES,
                                "nominal_across_flats_mm": nominal_af, "inside_diameter_mm": inside or None,
                                "description": "Planning display: nominal shaft and annular washers; circumscribed cylindrical head/nut. Threads, chamfers, runout and delivered profiles are not shown.",
                                "clearance_status": "Planning envelope only; no exact collision or delivered-fit claim"})
        solids[name] = row
        return name

    # Rail placements include the saved 0.468 mm headward washer change.
    rail_axes = {row["axis_id"] for row in catalog["axis_families"]["rail"]["axes"]}
    for axis_id in sorted(rail_axes):
        replacement = next(row for row in top_fit["replacements"] if row["axis_id"] == axis_id)
        queries = {row["component"]: row for row in top_fit["queries"]
                   if row["axis_id"] == axis_id and row["id"].endswith("/installed")}
        direction = _unit(axis_rows[axis_id]["axis_xyz"])
        shaft = {"start_xyz_mm": replacement["underhead_xyz_mm"], "direction_xyz": direction,
                 "length_mm": top_fit["conditional_engagement_mm"]["nominal_length"], "radius_mm": 3.175}
        queries["shaft"] = {"cylinder": shaft}
        refs = [{"path": TOP_FIT, "sha256": PINS[TOP_FIT]}, order_ref]
        for role in STACK_ROLES:
            query = queries[role]
            changed_top.append(hardware(axis_id, role, query["cylinder"], query.get("inside_diameter_mm", 0),
                                        family="top_outer", references=refs,
                                        nominal_af=11.1125 if role in ("head", "nut") else None))
    side_axes = {row["axis_id"] for row in catalog["axis_families"]["side"]["axes"]}
    side_washer = catalog["catalog_parts"]["side_washer_uss"]
    for axis_id in sorted(side_axes):
        rows = {row["component"]: row for row in top_fit["obstacles"]
                if row.get("axis_id") == axis_id and row["category"] == "corrected_top_component"}
        for role in STACK_ROLES:
            query = rows[role]
            cylinder = copy.deepcopy(query["cylinder"])
            inside = 0.0
            if role in ("head_washer", "nut_washer"):
                cylinder["radius_mm"] = side_washer["outside_diameter"]["mm"]["nominal"] / 2
                inside = side_washer["inside_diameter"]["mm"]["nominal"]
                if cylinder["length_mm"] != side_washer["thickness"]["mm"]["maximum"]:
                    raise ValueError("side washer display thickness differs from declared catalog maximum")
            changed_top.append(hardware(axis_id, role, cylinder, inside, family="top_outer",
                                        references=[{"path": TOP_FIT, "sha256": PINS[TOP_FIT]},
                                                    {"path": HARDWARE, "sha256": PINS[HARDWARE]}],
                                        nominal_af=12.7 if role in ("head", "nut") else None))
    for axis in manifest["proposed_internal_bolt_axes"]:
        axis_id, fit_id = axis["canonical_axis_id"], axis["fit_axis_id"]
        rows = {row["component"]: row for row in bridge_fit["queries"]
                if row["axis_id"] == fit_id and (row["id"].endswith("/installed") or row["id"].endswith("/shaft/nominal"))}
        for role in STACK_ROLES:
            query = rows[role]
            inside = bridge_fit["proposal"]["stock_and_component_envelopes"]["washer"]["OD_ID_thickness_mm"][1] if role in ("head_washer", "nut_washer") else 0.0
            name = hardware(axis_id, role, query["cylinder"], inside, family="proposed_knee_bridge",
                            references=[{"path": BRIDGE_FIT, "sha256": PINS[BRIDGE_FIT]}, order_ref],
                            nominal_af=11.1125 if role in ("head", "nut") else None)
            solids[name]["order_axis_id"] = axis["order_axis_id"]
            solids[name]["fit_axis_id"] = fit_id
            added_bridge.append(name)
        scene["model_inventory"]["candidate_axes"][axis_id] = {
            "family": "proposed_knee_bridge", "receiver_ids": axis["receivers"],
            "installed_component_roles": STACK_ROLES, "installed_role_ids": STACK_ROLES,
            "installed_cad_role_ids": [], "proposal_only": True, "order_axis_id": axis["order_axis_id"],
            "fit_axis_id": fit_id, "global_operator_row": None,
        }

    movements = model["owner_authorized_upper_screw_movements"]
    csv_rows = {row["axis_id"]: row for row in csv.DictReader((ROOT / SHOP_AXES).read_text().splitlines())}
    if len(movements) != 4 or len(csv_rows) != 66 or shop["csv"]["sha256"] != PINS[SHOP_AXES]:
        raise ValueError("four moved axes and 66-row shop schedule are required")
    changed_screws = []
    for movement in movements:
        before, after = movement["before"], movement["after"]
        axis_id, visual = movement["axis_id"], f"fastener_{movement['axis_id']}"
        saved = csv_rows[axis_id]
        if any(abs(float(saved[f"front_datum_{axis}_global_mm"]) - after["origin_global_xyz_mm"][i]) > 1e-8
               or abs(float(saved[f"direction_{axis}_global"]) - after["axis_global_xyz"][i]) > 1e-8
               for i, axis in enumerate("xyz")) or saved["receiver_member"] != after["receiver_member"]:
            raise ValueError(f"shop schedule and operator screw coordinates differ: {axis_id}")
        translation = _add(after["origin_global_xyz_mm"], before["origin_global_xyz_mm"], -1)
        scene["baseline_display_translations_mm"][visual] = translation
        changed_screws.append(axis_id)
        scene["model_inventory"]["moved_panel_axes"].append({
            "axis_id": axis_id, "visual_name": visual, "panel_member": after["panel_member"],
            "receiver_member": after["receiver_member"], "old_start_global_xyz_mm": before["origin_global_xyz_mm"],
            "new_start_global_xyz_mm": after["origin_global_xyz_mm"], "translation_global_xyz_mm": translation,
            "axis_global_xyz_unchanged": after["axis_global_xyz"], "purchased_product_policy": after["purchased_policy"],
        })
    changed_screws.sort()
    fixed = sorted(set(scene["model_inventory"]["fixed_panel_axes"]) - set(changed_screws))
    scene["model_inventory"]["fixed_panel_axes"] = fixed
    moved = sorted(row["axis_id"] for row in scene["model_inventory"]["moved_panel_axes"])
    scene["baseline_scene_policy"].update(retained_fixed_axis_ids=fixed, moved_panel_axis_ids=moved)
    changes = sorted([*TIMBERS, *changed_top, *added_bridge])
    if len(changes) != 66 or len(solids) != 528 or len(set(moved)) != 12 or len(fixed) != 54:
        raise ValueError("display delta or panel axis census differs")
    scene["solids"] = [solids[name] for name in sorted(solids)]
    referenced = {row["mesh"]["triangle_topology_sha256"] for row in scene["solids"]}
    scene["triangle_topologies"] = {key: topologies[key] for key in sorted(referenced)}
    scene["display_mesh_encoding"].update(unique_triangle_topology_count=len(referenced),
                                          imported_saved_STEP_solid_count=6,
                                          analytic_hardware_display_mesh_count=60,
                                          exact_collision_geometry=False)
    scene["counts"].update(candidate_bores=96, candidate_installed_hardware_axes=96,
                           candidate_installed_hardware_components=480, rendered_overlay_solids=528,
                           fixed_panel_axes=54, moved_panel_axes=12)
    scene["model_inventory"]["changed_display_solid_ids"] = changes
    scene["model_inventory"]["effective_member_source_bindings"] = bindings
    scene.setdefault("historical_reference", {}).update(
        preserved_WJ24_scene_path=PARENT, preserved_WJ24_scene_sha256=PINS[PARENT],
        historical_reports_are_not_current_revision_claims=True)
    design = copy.deepcopy(baseline["design"])
    design.update(key="wood-joints-working-proposal", viewer_key="wood-joints-working-proposal",
                  candidate="compact-floor-flush-wood-joints-development",
                  status="Current unadopted wood-joint proposal", qualified_for_design=False,
                  description="Frozen unadopted wood-joint proposal display; baseline panel datums retained",
                  total_bolt_count=108, panel_kicker_screw_count=66,
                  documents=[
                      {"label": "Proposal working packet", "path": f"{UPPER}/knee-bridge-working-package.md"},
                      {"label": "Upper screw shop overlay", "path": f"{UPPER}/shop-addendum.md"},
                      {"label": "Current joint addendum", "path": f"{PACKET}/assembly-package/current-joint-addendum.md"},
                  ])
    scene.update(schema=SCHEMA, revision_id="knee-bridge-working-package-attempt02",
                 layout_id="knee-bridge-working-package-attempt02", trial_id="knee-bridge-working-package-attempt02",
                 layout_status="UNADOPTED_WORKING_PROPOSAL", status="UNADOPTED WORKING PROPOSAL",
                 scope="Display-only frozen proposal: six saved STEP solids, corrected top stacks, four proposed bridge stacks and four upper screw visual translations. No source geometry, analysis, force display or physical authority is changed.",
                 design=design, census=CENSUS, planning_mass_kg=manifest["modeled_mass_kg"],
                 changed_screw_axis_ids=changed_screws, changed_overlay_solid_ids=changes,
                 changed_display_solid_ids=sorted(changes + [f"fastener_{name}" for name in changed_screws]),
                 proposal_binding={"manifest_path": MANIFEST, "manifest_sha256": PINS[MANIFEST],
                                   "planning_order_path": order_ref["source"], "planning_order_sha256": order_ref["sha256"],
                                   "effective_step_source_bindings": bindings, "proposal_adopted": False},
                 display_only=True, exact_collision_geometry=False, applied_forces_shown=False,
                 physical_release=False, proposal_adopted=False, drilling_released=False,
                 geometry_accepted=False, source_cutting_released=False)
    scene["revision_report"] = {"changed_overlay_solid_ids": changes, "changed_screw_axis_ids": changed_screws,
                                "display_only": True, "proposal_adopted": False}
    scene["revision_report_path"], scene["revision_report_sha256"] = MANIFEST, PINS[MANIFEST]
    scene["revision_checks"] = {"source_geometry_changed": False, "forces_shown": False, "exact_collision_geometry": False,
                                "complete_joint_acceptance": False, "fabrication_released": False}
    scene["display_hardware_limits"] = {
        "top_rail": "Latest Hillman 885522 planning envelope: washers OD/ID/t 25.4/8.3058/2.5 mm; nominal shaft 6.35 x 203.2 mm. Saved top-washer seats and underhead datum used.",
        "top_side": "Deterministic catalog display: washers nominal OD/ID 22.225/9.525 mm, maximum thickness 2.6416 mm; nominal shaft 7.9375 x 203.2 mm. Saved corrected side placements retained.",
        "new_bridge": "Four canonical proposed_v_bridge axes, with saved bridge_g100/bridge_g250 aliases. Nominal shaft 6.35 x 165.1 mm and washers 25.4/8.3058/2.5 mm; saved fit-recipe placements used. The 203.2 mm conservative bound is not displayed as stock.",
        "head_and_nut": "Circumscribed cylindrical display envelopes use bound maximum catalog widths and heights; these are not actual regular-hex, chamfer or delivered bearing profiles. Nuts are displayed as the saved solid-cylinder enclosures.",
        "preserved_other_hardware": "All other original WJ24 occupancy meshes and twelve retained baseline stacks remain their source geometry. Planned longer stock for twelve other axes is not substituted into those meshes. Their source envelopes are not the latest order geometry.",
        "panel_kicker_screws": "All 66 source Hillman-policy screw visuals retained; twelve total baseline visual translations include the original eight and four upper-row moves. Screw head/thread/pilot/resistance remain unqualified.",
        "mesh": "Hardware circles use 48 sectors and 0.1 mm vertex quantization; six saved STEP surfaces use 0.5 mm tessellation and the same quantization. Display meshes are not exact collision geometry.",
    }
    scene["limits"] = ["Unadopted proposal display; no candidate, fabrication, structural or climbing release.",
                       "No source cut geometry or source authority changes; old WJ24 scene remains preserved.",
                       "Hardware is planning or preserved source occupancy geometry, not delivered component geometry.",
                       "Display meshes establish no exact collision, fit, force, contact or complete-joint result.",
                       "Planning frame mass is 225.19791414318078 kg under saved density/envelope conventions; it is not measured mass. The separate 25 kg equipment allowance is not included."]
    scene["findings"] = [{"title": "Current proposal display", "detail": scene["scope"]},
                         {"title": "Hardware display scope", "detail": scene["display_hardware_limits"]["preserved_other_hardware"]}]
    for flag in scene["release"]:
        scene["release"][flag] = False
    scene["source_binding"].update(proposal_manifest_path=MANIFEST, proposal_manifest_sha256=PINS[MANIFEST],
                                    display_source_sha256=dict(sorted(sources.items())),
                                    exporter_path="scripts/export_wood_joint_working_scene.py",
                                    exporter_sha256=_sha(Path(__file__).read_bytes()))
    scene["bounds_mm"] = _display_bounds(scene, baseline)
    scene["bounds_scope"] = "Exact union of rendered quantized overlay vertices and visible translated baseline STL vertices; not a CAD collision or physical envelope claim."
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if output != ROOT / OUTPUT:
        raise ValueError("exporter owns only its separate working-proposal scene output")
    scene = build_scene()
    raw = json.dumps(scene, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                     allow_nan=False).encode("utf-8") + b"\n"
    output.write_bytes(raw)
    print(json.dumps({"path": OUTPUT, "sha256": _sha(raw), "bytes": len(raw),
                      "schema": SCHEMA, "overlay_solids": len(scene["solids"]),
                      "changed_overlay_solids": len(scene["changed_overlay_solid_ids"]),
                      "changed_screw_axis_ids": scene["changed_screw_axis_ids"], "census": scene["census"]}))


if __name__ == "__main__":
    main()
