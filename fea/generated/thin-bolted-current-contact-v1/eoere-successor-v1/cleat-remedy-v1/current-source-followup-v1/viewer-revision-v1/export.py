"""Display the Z180 proposal using four already queried finished receivers.

Only saved BREP import and display tessellation are native operations. No cut,
Boolean, full-frame reconstruction, mechanics solve or response transfer occurs.
The current Z200 viewer, geometry descriptor and numerical results stay intact.
"""

from __future__ import annotations

import gzip
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
from pathlib import Path

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
REVISION = "eoere-lower-cleat-z180-proposal-v1"
FLAGS = {key: False for key in (
    "geometry_adopted", "candidate_accepted", "drilling_released",
    "fabrication_released", "structural_accepted", "climbing_released",
)}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(path):
    return json.loads(Path(path).read_bytes(), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))


def verify(pins):
    for name, digest in pins.items():
        path = ROOT / name
        require(not Path(name).is_absolute() and ".." not in Path(name).parts
                and path.resolve() == path.absolute(), "canonical repository source required")
        require(sha(path) == digest, "source changed: " + name)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare():
    """Source-only intake; native imports occur only after parent readiness."""
    inp = read(HERE / "inputs.json")
    permit = read(HERE / "parent-readiness.json")
    pins = dict(inp["source_sha256"])
    pins[str(HERE.relative_to(ROOT) / "inputs.json")] = permit["inputs_sha256"]
    pins[str(OWN.relative_to(ROOT))] = permit["exporter_sha256"]
    verify(pins)
    require(permit["only_four_saved_BREP_display_tessellations"] is True
            and permit["native_mechanics_or_full_frame_CAD_authorized"] is False
            and permit["geometry_adoption_authorized_by_this_file"] is False,
            "bounded parent readiness required")
    runtime = {"python": platform.python_version(),
               "cadquery": importlib.metadata.version("cadquery"),
               "cadquery-ocp": importlib.metadata.version("cadquery-ocp")}
    require(runtime == inp["runtime"], "pinned native display runtime required")
    layout = read(ROOT / inp["current_geometry"])
    proposal = read(ROOT / inp["placement"])
    native = read(ROOT / inp["native_result"])
    audit = load(ROOT / inp["saved_result_verifier"], "z180_saved_result_verifier").evaluate(native)
    require(audit["pass"] is True, "independent saved receiver audit required")
    require(proposal["geometry_adopted"] is False and proposal["optional_2026_extra"] is False,
            "unadopted base-only proposal required")
    changes = proposal["changes"]
    axes = {axis["id"]: axis for axis in layout["axes"]}
    proposed = {axis["id"]: axis for axis in proposal["proposed_axes"]}
    require(len(axes) == 100 and len(proposed) == len(changes) == 4
            and len(layout["screw_axes"]) == 66, "100/66/4 source census required")
    for row in changes:
        name = row["axis_id"]
        before, after = axes[name], proposed[name]
        require(before["point_xyz_mm"] == row["current_point_xyz_mm"]
                and after["point_xyz_mm"] == row["proposed_point_xyz_mm"]
                and row["translation_xyz_mm"] == [0.0, 0.0, -20.0]
                and before["point_xyz_mm"][2] == 200 and after["point_xyz_mm"][2] == 180,
                "exact four Z200 to Z180 moves required")
        expected = dict(before, point_xyz_mm=after["point_xyz_mm"])
        require(expected == after, "no other axis properties may change")
    full_axes = [proposed.get(axis["id"], axis) for axis in layout["axes"]]
    require(hashlib.sha256(canonical(full_axes)).hexdigest()
            == proposal["proposed_100_axes_canonical_sha256"], "proposed descriptor closure required")
    scenario = next(row for row in native["scenarios"] if row["scenario"] == "proposed_Z180_modeled")
    bodies = scenario["finished_bodies"]
    require(set(bodies) == {"eoere_cleat_left", "eoere_cleat_right",
                            "base_post_outer_left", "base_post_outer_right"}, "four receivers required")
    for row in bodies.values():
        require(pins[row["path"]] == row["sha256"]
                and (ROOT / row["path"]).stat().st_size == row["bytes"], "saved receiver binding differs")
    datums = []
    for name, axis in proposed.items():
        for member in axis["receivers"]:
            bounds = bodies[member]["bounds_xyz_mm"]
            datums.append({"axis_id": name, "receiver": member,
                           "world_axis_point_xyz_mm": axis["point_xyz_mm"],
                           "world_direction_xyz": axis["direction_xyz"],
                           "from_Ymin_mm": round(axis["point_xyz_mm"][1] - bounds[1][0], 8),
                           "from_Zmin_mm": round(180 - bounds[2][0], 8),
                           "from_Zmax_mm": round(bounds[2][1] - 180, 8),
                           "modeled_wood_bore_mm": axis["bore_diameter_mm"],
                           "bit_instruction": None, "actual": None})
    pins[str(HERE.relative_to(ROOT) / "parent-readiness.json")] = sha(HERE / "parent-readiness.json")
    descriptor = {
        "schema": "eoere_lower_cleat_z180_geometry_patch/v1", "revision": REVISION,
        "candidate": layout["candidate"], "status": "UNADOPTED_GEOMETRY_PREVIEW",
        "parent_geometry": {"path": inp["current_geometry"], "sha256": pins[inp["current_geometry"]]},
        "placement": {"path": inp["placement"], "sha256": pins[inp["placement"]]},
        "current_100_axes_canonical_sha256": proposal["current_100_axes_canonical_sha256"],
        "proposed_100_axes_canonical_sha256": proposal["proposed_100_axes_canonical_sha256"],
        "unchanged_66_screws_canonical_sha256": proposal["current_66_screws_canonical_sha256"],
        "axis_changes": changes, "proposed_axes": proposal["proposed_axes"], "receiver_datums": datums,
        "finished_receivers": {name: {key: row[key] for key in
            ("path", "sha256", "bytes", "volume_mm3", "bounds_xyz_mm")} for name, row in bodies.items()},
        "counts": layout["counts"]["base"], "optional_2026_extra": False,
        "saved_response_transferred": False, "complete_joint_resistance": None, "release": FLAGS,
        "limits": ["Display geometry only; current six-case actions remain bound to Z200.",
                   "Datums describe an unadopted proposal, not drilling instructions.",
                   "Tool access, tolerances and delivered hardware remain unverified."],
    }
    return inp, pins, runtime, descriptor, bodies, audit


def main():
    inp, pins, runtime, descriptor, bodies, audit = prepare()
    out = HERE / "runs-v1/export01"
    require(out.parent.resolve() == out.parent.absolute(), "canonical output parent required")
    out.mkdir()  # Exclusive fixed destination, including rejection of dangling links.
    import cadquery as cq

    exporter = load(ROOT / inp["display_exporter"], "z180_reused_display_exporter")
    replacements = []
    for name, row in sorted(bodies.items()):
        imported = cq.importers.importBrep(str(ROOT / row["path"]))
        solids = imported.solids().vals()
        require(len(solids) == 1 and solids[0].isValid(), "one valid saved receiver required")
        shape = solids[0]
        require(abs(shape.Volume() - row["volume_mm3"]) < 1e-5, "saved receiver volume differs")
        box = shape.BoundingBox()
        actual = [[box.xmin, box.xmax], [box.ymin, box.ymax], [box.zmin, box.zmax]]
        require(all(abs(a-b) < 1e-6 for pair, expected in zip(actual, row["bounds_xyz_mm"], strict=True)
                    for a, b in zip(pair, expected, strict=True)), "saved receiver bounds differ")
        replacements.append({"name": name, "id": name, "source_brep_sha256": row["sha256"],
                             "mesh": exporter._shape_mesh(shape),
                             "fabrication": {"kind": "timber", "lower_cleat_revision": REVISION}})
    topologies = exporter._deduplicate_triangle_topologies(replacements)
    layout_bytes = json.dumps(descriptor, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    patch = {
        "schema": "eoere_lower_cleat_z180_display_patch/v1", "revision": REVISION,
        "candidate": descriptor["candidate"], "status": descriptor["status"],
        "layout_report": {"path": str((out / "layout.json").relative_to(ROOT)),
                          "sha256": hashlib.sha256(layout_bytes).hexdigest()},
        "parent_scene": inp["parent_scene"], "counts": descriptor["counts"],
        "replacements": replacements, "triangle_topologies": topologies,
        "bolt_translations": [{"axis_id": row["axis_id"], "translation_xyz_mm": row["translation_xyz_mm"]}
                              for row in descriptor["axis_changes"]],
        "optional_2026_extra": False, "saved_response_transferred": False,
        "complete_joint_resistance": None, "release": FLAGS,
    }
    decoded = canonical(patch)
    encoded = gzip.compress(decoded, mtime=0)
    verify(pins)
    outputs = {"layout.json": layout_bytes, "scene.json.gz": encoded}
    for name, value in outputs.items():
        with (out / name).open("xb") as stream:
            stream.write(value)
    result = {
        "schema": "eoere_lower_cleat_z180_display_export/v1", "status": "DISPLAY_EXPORT_COMPLETE",
        "revision": REVISION, "runtime": runtime, "source_sha256": pins,
        "sources_unchanged_before_after": True, "saved_receiver_audit": audit,
        "saved_BREP_tessellations": 4, "hardware_components_to_translate": 20,
        "output": {name: {"path": str((out / name).relative_to(ROOT)),
                           "sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}
                   for name, value in outputs.items()},
        "scene_decoded_sha256": hashlib.sha256(decoded).hexdigest(),
        "native_cuts_Boolean_or_mechanics": False, "saved_response_transferred": False,
        "release": FLAGS,
    }
    with (out / "export-result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "output": result["output"],
                      "scene_decoded_sha256": result["scene_decoded_sha256"]}))


if __name__ == "__main__":
    main()
