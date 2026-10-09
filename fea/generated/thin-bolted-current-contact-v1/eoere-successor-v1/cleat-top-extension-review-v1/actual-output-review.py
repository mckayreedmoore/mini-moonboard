"""Bounded independent saved-solid review; exclusively create its own receipt."""
from __future__ import annotations

import base64
from collections import Counter, defaultdict
import gzip
import hashlib
import itertools
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
REVIEW = OWN.parent
LEAF = REVIEW.parent
CAD = LEAF / "cleat-top-extension-v1/cad-v1"
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1"
EXPECTED = {
    CAD / "geometry.json": "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d",
    CAD / "scene.json.gz": "ae6315463f0482597075a769ad3ee55630b4c8b430c2ae93137c5232cc6dbb54",
    REVIEW / "profile-review.json": "7c5fe6457b96be5af62ebb6d64b5610dbb24471bff24e9f467c06e0a1dfff6ae",
    REVIEW / "profile-review.py": "221630bec2a047193fcfa22b83ed639259f94ffc28e5cb120ef4a609b3083f83",
    LEAF / "cleat-top-extension-v1/revision.py": "3d26790b93aa3754c50ed5b427e7b4b1db05e517e7e759ef6d009d427216ec08",
}
AXES_SHA = "009a8799bb28dfe989e7c75651a3d111c6bb9e003c8f9ab0adda99e3471b7926"
SCREWS_SHA = "addb41a1836eacea53e7411407ae8006f97cb56ed314ae29cded2c4ff1e2a88b"
CLEATS = ("eoere_cleat_left", "eoere_cleat_right")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    data = Path(path).read_bytes()
    return json.loads(gzip.decompress(data) if str(path).endswith(".gz") else data)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + str(path))


def bounds(shape):
    box = shape.BoundingBox()
    return [[getattr(box, a + "min"), getattr(box, a + "max")] for a in "xyz"]


def world_box(row, templates):
    mesh = row.get("mesh") or templates[row["template_id"]]["mesh"]
    box = mesh["bounds_xyz_mm"]
    if not row.get("transform"):
        return box
    matrix = row["transform"]
    points = [[matrix[12+i] + sum(matrix[4*k+i]*p[k] for k in range(3)) for i in range(3)]
              for p in itertools.product(*[box[k:k+2] for k in (0, 2, 4)])]
    return [v for i in range(3) for v in (min(p[i] for p in points), max(p[i] for p in points))]


def bank(native, scenes):
    result = {r["id"]: {"kind": r["kind"], "bounds": [v for pair in r["bounds_xyz_mm"] for v in pair]}
              for r in native["parts"] if r["kind"] in ("panel", "screw", "light", "tnut", "wire")}
    require(len(result) == 477, "native retained bounds census")
    for scene in scenes:
        templates = scene.get("mesh_templates") or {r["id"]: r for r in scene.get("templates", [])}
        for row in scene.get("solids", []) + scene.get("replacements", []) + scene.get("additions", []):
            result[row["name"]] = {"kind": row["fabrication"]["kind"], "bounds": world_box(row, templates)}
    return result


def signed_mesh_volume(vertices, triangles):
    value = 0.
    for ia, ib, ic in triangles:
        a, b, c = vertices[ia], vertices[ib], vertices[ic]
        value += a[0]*(b[1]*c[2]-b[2]*c[1]) + a[1]*(b[2]*c[0]-b[0]*c[2]) + a[2]*(b[0]*c[1]-b[1]*c[0])
    return value / 6


def mesh_check(shape, row, topologies):
    mesh = row["mesh"]
    raw_vertices = base64.b64decode(mesh["vertices_base64"], validate=True)
    topology = topologies[mesh["triangle_topology_sha256"]]
    raw_indices = base64.b64decode(topology["triangle_indices_base64"], validate=True)
    require(hashlib.sha256(raw_indices).hexdigest() == mesh["triangle_topology_sha256"], "mesh topology digest")
    vc = "h" if mesh["vertex_component_type"] == "int16" else "i"
    tc = "H" if mesh["triangle_component_type"] == "uint16" else "I"
    quantized = list(struct.iter_unpack("<" + 3*vc, raw_vertices))
    triangles = list(struct.iter_unpack("<" + 3*tc, raw_indices))
    require(len(quantized) == mesh["vertex_count"] and len(triangles) == mesh["triangle_count"], "mesh census")
    require(all(0 <= i < len(quantized) for triangle in triangles for i in triangle), "mesh index range")
    q = mesh["vertex_quantization_mm"]
    vertices = [[v*q for v in point] for point in quantized]
    expected_vertices, expected_triangles = shape.copy().tessellate(.5)
    expected_quantized = [tuple(round(v/q) for v in p.toTuple()) for p in expected_vertices]
    require(Counter(quantized) == Counter(expected_quantized), "viewer vertices differ from saved CAD tessellation")
    require(len(triangles) == len(expected_triangles), "viewer triangle count differs from saved CAD tessellation")
    edges = defaultdict(lambda: [0,0])
    graph = defaultdict(set)
    for triangle in triangles:
        points = [quantized[i] for i in triangle]
        require(len(set(points)) == 3, "quantized triangle collapsed")
        for first,last in zip(points,points[1:]+points[:1]):
            edge = tuple(sorted((first,last)))
            edges[edge][0] += 1
            edges[edge][1] += 1 if first == edge[0] else -1
            graph[first].add(last)
            graph[last].add(first)
    require(all(count == 2 and direction == 0 for count,direction in edges.values()), "mesh is not an oriented closed manifold")
    visited, pending = set(), [next(iter(graph))]
    while pending:
        point = pending.pop()
        if point in visited:
            continue
        visited.add(point)
        pending.extend(graph[point]-visited)
    require(len(visited) == len(graph), "mesh surface disconnected")
    require(len(graph)-len(edges)+len(triangles) == -6, "mesh does not retain four through bores")
    cad_bounds = [v for pair in bounds(shape) for v in pair]
    require(max(abs(a-b) for a,b in zip(cad_bounds, mesh["bounds_xyz_mm"])) < 1e-6, "mesh CAD bounds differ")
    display_volume = signed_mesh_volume(vertices, triangles)
    independently_meshed_volume = signed_mesh_volume([[v*q for v in p] for p in expected_quantized],expected_triangles)
    require(display_volume > 0, "mesh orientation/volume")
    require(abs(display_volume-independently_meshed_volume) < 1e-5, "mesh volume differs from independently tessellated saved CAD")
    return {"id": row["id"], "vertex_count": len(vertices), "triangle_count": len(triangles),
            "saved_CAD_tessellation_quantized_vertex_multiset_identical": True,
            "oriented_connected_closed_manifold": True, "Euler_characteristic": -6,
            "independent_tessellation_signed_volume_difference_mm3": display_volume-independently_meshed_volume,
            "triangulation_note": "BREP roundtrip changes triangle diagonals/order while retaining identical quantized vertices and surface volume.",
            "display_quantization_mm": q,
            "display_mesh_signed_volume_mm3": display_volume,
            "display_mesh_volume_minus_exact_CAD_mm3": display_volume-shape.Volume(),
            "exact_CAD_volume_mm3": shape.Volume()}


def main():
    output = REVIEW / "actual-output-review.json"
    require(not output.exists(), "review receipts are immutable; choose a separate follow-up file")
    verify(EXPECTED)
    report, scene, proposal = read(CAD / "geometry.json"), read(CAD / "scene.json.gz"), read(REVIEW / "profile-review.json")
    pins = dict(EXPECTED)
    pins.update({ROOT / p: h for p,h in report["source_sha256"].items()})
    pins[OWN] = sha(OWN)
    for row in report["changed_finished_solids"]:
        pins[ROOT / row["path"]] = row["sha256"]
    pins[CAD / "scene.json"] = "6c39b4a240f8033491bbd43c437d60dc888c524e90b350e53351eaf28ddc5db6"
    verify(pins)
    require(gzip.decompress((CAD / "scene.json.gz").read_bytes()) == (CAD / "scene.json").read_bytes(), "scene encoding differs")
    base, extra = read(DOC / "occupied-adjusted-base-v3.json"), read(DOC / "occupied-2026-adjustments-v3.json")
    require(report["axes"] == base["axes"] and report["screw_axes"] == base["screw_axes"], "current v3 axes changed")
    require(canonical(report["axes"]) == AXES_SHA and canonical(report["screw_axes"]) == SCREWS_SHA, "current v3 axis digests")
    require(extra["bolt_axes_unchanged_sha256"] == hashlib.sha256(json.dumps(base["axes"], sort_keys=True).encode()).hexdigest(), "optional bolt join")
    require(extra["screw_axes_unchanged_sha256"] == hashlib.sha256(json.dumps(base["screw_axes"], sort_keys=True).encode()).hexdigest(), "optional screw join")
    require(set(r["id"] for r in report["changed_finished_solids"]) == set(CLEATS), "sole two changed bodies")
    require(set(r["name"] for r in scene["replacements"]) == set(CLEATS) and len(scene["replacements"]) == 2, "sole two mesh replacements")
    require(not scene.get("additions") and not scene.get("solids"), "unexpected scene additions")
    require(scene["layout_report"]["sha256"] == sha(CAD / "geometry.json"), "scene layout binding")
    require(report["counts"] == {"base": base["counts"], "extra": extra["counts"]}, "variant census changes")
    require(not report["mechanics_ready"] and not scene["mechanics_ready"] and scene["analysis_pass_transferred"] is False, "qualification boundary")
    require(all(v is False for v in report["release"].values()) and scene["release"] == report["release"], "release flags")
    parent_paths = {layer: ROOT / "site" / row["url"] for layer,row in scene["parent_scenes"].items()}
    require(set(parent_paths) == {"base", "extra"}, "both parent variants required")
    for layer, path in parent_paths.items():
        row = scene["parent_scenes"][layer]
        require(sha(path) == row["sha256"] and hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest() == row["decoded_sha256"], "variant scene binding")
        expected_layout = DOC / ("occupied-adjusted-base-v3.json" if layer == "base" else "occupied-2026-adjustments-v3.json")
        require(row["layout_sha256"] == sha(expected_layout), "variant geometry binding")
    native = read(DOC.parent / "native-geometry-v4.json")
    common = [read(ROOT / "site" / p) for p in ("eoere-bottom-rail-scene.json.gz", "eoere-cleat-trim-scene.json", "eoere-aligned-wire-scene.json.gz")]
    base_scenes = common + [read(parent_paths["base"])]
    banks = {"base": bank(native, base_scenes), "extra": bank(native, base_scenes + [read(parent_paths["extra"])])}
    require(len(banks["base"]) == 1021 and len(banks["extra"]) == 1380, "complete bounds bank census")
    for screen in report["added_timber_collision_screen"]:
        require(canonical(banks[screen["layer"]]) == screen["body_bank_canonical_sha256"], "CAD-bounds bank identity")

    # Only these six saved source/output solids are imported; no repository model module is imported.
    import cadquery as cq
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    def overlap(a, b):
        return max(0., a.intersect(b).Volume())

    sources = {r["id"]: r for r in proposal["retained_side_and_cleat_body_bindings"]}
    outputs = {r["id"]: r for r in report["changed_finished_solids"]}
    polygon = proposal["new_cleat_YZ_polygon_mm"]
    expected_rows = {r["id"]: r for r in proposal["new_finished_cleat_expectations"]}
    body_checks, bore_checks, contacts, collision_screens, meshes = [], [], [], [], []
    for name in CLEATS:
        old = cq.Shape.importBrep(str(ROOT / sources[name]["path"]))
        side_name = "base_side_" + name.rsplit("_", 1)[1]
        side = cq.Shape.importBrep(str(ROOT / sources[side_name]["path"]))
        new = cq.Shape.importBrep(str(ROOT / outputs[name]["path"]))
        require(all(s.isValid() and len(s.Solids()) == 1 for s in (old, side, new)), "saved solid validity")
        x0,x1 = sources[name]["bounds_xyz_mm"][0]
        thickness = x1-x0
        raw = cq.Workplane("YZ", origin=(x0,0,0)).polyline(polygon).close().extrude(thickness).val()
        expected = raw
        cleat_axes = [a for a in base["axes"] if name in a["receivers"]]
        require(len(cleat_axes) == 4, "four bores per cleat")
        for axis in cleat_axes:
            _,y,z = axis["point_xyz_mm"]
            bore_radius = axis["bore_diameter_mm"]/2
            bore = cq.Solid.makeCylinder(bore_radius, thickness+2, cq.Vector(x0-1,y,z), cq.Vector(1,0,0))
            expected = expected.cut(bore)
            require(overlap(new,bore) < .001, "preserved bore filled")
            wall = cq.Solid.makeCylinder(bore_radius+.5, thickness, cq.Vector(x0,y,z), cq.Vector(1,0,0)).cut(
                cq.Solid.makeCylinder(bore_radius, thickness, cq.Vector(x0,y,z), cq.Vector(1,0,0)))
            wall_fraction = overlap(new,wall)/wall.Volume()
            require(abs(wall_fraction-1) < 1e-8, "full bore wall missing")
            h = axis["hardware_scenario"]
            land_fractions = []
            for x,d in ((x0,1),(x1,-1)):
                direction = cq.Vector(d,0,0)
                land = cq.Solid.makeCylinder(h["washer_od_mm"]/2,1,cq.Vector(x,y,z),direction).cut(
                    cq.Solid.makeCylinder(h["washer_id_mm"]/2,1,cq.Vector(x,y,z),direction))
                land_fractions.append(overlap(new,land)/land.Volume())
            require(all(abs(v-1) < 1e-8 for v in land_fractions), "annular section support missing")
            bore_checks.append({"axis_id": axis["id"], "cleat": name, "full_wall_length_mm": thickness,
                                "bearing_wall_skin_0p5mm_fraction": wall_fraction,
                                "annular_skin_fraction_at_both_X_faces": land_fractions})
        symmetric_difference = new.cut(expected).Volume()+expected.cut(new).Volume()
        require(symmetric_difference < .001, "saved solid differs from prescribed polygon minus four bores")
        old_lost = old.cut(new).Volume()
        require(old_lost < .001, "old cleat not subset")
        added = new.cut(old)
        require(abs(added.Volume()-proposal["added_volume_mm3_each"]) < .001, "added volume differs")
        require(abs(new.Volume()-expected_rows[name]["expected_finished_volume_mm3"]) < .001, "finished volume differs")
        expected_bounds = [[x0,x1],[-175.7,-36.0],[139.7,polygon[2][1]]]
        require(max(abs(a-b) for p,q in zip(bounds(new),expected_bounds) for a,b in zip(p,q)) < 1e-6, "exact saved bounds differ")
        face_profiles = []
        top_faces = []
        for face in new.Faces():
            if face.geomType() != "PLANE":
                continue
            normal = face.normalAt().toTuple()
            if abs(abs(normal[0])-1) < 1e-8:
                yz = sorted((v.Center().y,v.Center().z) for v in face.outerWire().Vertices())
                require(len(yz) == 4 and max(math.dist(a,b) for a,b in zip(yz,sorted(map(tuple,polygon)))) < 1e-6, "four-point actual side outline")
                face_profiles.append(yz)
            if abs(normal[0]) < 1e-8 and normal[2] > .6 and normal[1] < -.7:
                top_faces.append(face)
        require(len(face_profiles) == 2 and len(top_faces) == 1, "expected planar face census")
        top_length = math.dist(polygon[2],polygon[3])
        require(abs(top_faces[0].Area()-thickness*top_length) < 1e-6, "whole-width sloping top area")
        cylindrical_faces = [f for f in new.Faces() if f.geomType() == "CYLINDER"]
        require(len(cylindrical_faces) == 4 and all(abs(BRepAdaptor_Surface(f.wrapped).Cylinder().Radius()-5.159375) < 1e-8 for f in cylindrical_faces), "actual four bore radii")
        bottom = cq.Solid.makeBox(thickness,139.7,1,cq.Vector(x0,-175.7,139.7))
        require(abs(overlap(new,bottom)-bottom.Volume()) < 1e-6 and abs(overlap(old,bottom)-bottom.Volume()) < 1e-6, "runner footprint changed")
        direction = cq.Vector(1 if name.endswith("left") else -1,0,0)
        old_contact = overlap(old.translate(direction),side)
        new_contact = overlap(new.translate(direction),side)
        require(abs(new_contact-old_contact-proposal["added_cross_section_area_mm2_each"]) < .001, "side contact addition")
        require(overlap(new,side) < .001 and overlap(added,side) < .001, "unshifted side overlap")
        contacts.append({"cleat":name,"side":side_name,"old_face_area_mm2":old_contact,
                         "new_face_area_mm2":new_contact,"added_face_area_mm2":new_contact-old_contact,
                         "method":"One-mm inward slice of prismatic shared X faces; geometric area only.",
                         "unshifted_overlap_mm3":overlap(new,side)})
        ab = [v for pair in bounds(added) for v in pair]
        for layer, rows in banks.items():
            candidates = sorted(n for n,r in rows.items() if n != name and all(
                max(ab[k],r["bounds"][k]) <= min(ab[k+1],r["bounds"][k+1])+.001 for k in (0,2,4)))
            require(candidates == [side_name], "new collision bounds candidate")
            nearest = min((max(max(ab[k]-r["bounds"][k+1],r["bounds"][k]-ab[k+1],0) for k in (0,2,4)),n)
                          for n,r in rows.items() if n not in (name,side_name))
            collision_screens.append({"cleat":name,"layer":layer,"CAD_bounds_body_count":len(rows),
                                      "candidates":candidates,"nearest_other_body":nearest[1],
                                      "minimum_other_body_separating_axis_gap_mm":nearest[0]})
        body_checks.append({"id":name,"valid_single_solid":True,"bounds_xyz_mm":bounds(new),
                            "volume_mm3":new.Volume(),"added_volume_mm3":added.Volume(),
                            "prescribed_solid_symmetric_difference_mm3":symmetric_difference,
                            "lost_old_volume_mm3":old_lost,"actual_side_outline_point_count":4,
                            "whole_width_top_edge_length_mm":top_length,"actual_sloped_top_face_area_mm2":top_faces[0].Area(),
                            "runner_seat_area_mm2":thickness*139.7})
        meshes.append(mesh_check(new,next(r for r in scene["replacements"] if r["id"]==name),scene["triangle_topologies"]))
    verify(pins)
    receipt = {"schema":"independent_saved_cleat_top_extension_review/v1","status":"PASS_NOMINAL_SAVED_GEOMETRY_ONLY",
               "source_sha256":{str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):h
                                for p,h in sorted(pins.items(),key=lambda x:str(x[0]))},
               "producer_source_pin_count_verified":report["source_pin_count"],"saved_solids_imported":6,
               "cadquery_version":cq.__version__,"body_checks":body_checks,"bore_and_land_checks":bore_checks,
               "side_contact_checks":contacts,"added_volume_CAD_bounds_screens":collision_screens,"viewer_mesh_checks":meshes,
               "current_v3_axes_canonical_sha256":AXES_SHA,"current_v3_screw_axes_canonical_sha256":SCREWS_SHA,
               "sole_two_cleat_replacements":True,"both_parent_variant_bindings_verified":True,
               "mechanics_or_global_rebuild_run":False,"analysis_pass_transferred":False,"physical_release":False,
               "limits":["Review concerns frozen nominal saved shapes and added volume, not delivered parts, machining or physical fit.",
                         "Bounds exclusion covers the authenticated 1021/1380 modeled bodies; omitted holds/hold bolts and real harness hardware remain outside it.",
                         "Contact slice areas do not establish pressure, preload, stiffness, resistance or structural acceptance.",
                         "Display mesh volume is approximate after tessellation and 0.1-mm quantization; exact saved CAD volume controls."],
               "reproduction_command":".venv/bin/python "+str(OWN.relative_to(ROOT))}
    with output.open("x") as stream:
        stream.write(json.dumps(receipt,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"status":receipt["status"],"receipt":str(output.relative_to(ROOT)),"sha256":sha(output),
                      "producer":sha(LEAF/"cleat-top-extension-v1/revision.py"),"body_checks":body_checks,"meshes":meshes},indent=2))


if __name__ == "__main__":
    main()
