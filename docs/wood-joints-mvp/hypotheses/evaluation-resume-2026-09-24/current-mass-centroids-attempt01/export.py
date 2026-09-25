"""Read modeled mass centers from the parent's existing reviewed CAD objects."""

import hashlib
import json
import math
from pathlib import Path


def export_mass_centroids(geometry, source_parts, reviewed_report, destination):
    root = Path.cwd()
    sources = {
        "weight": root / "docs/wood-joints-mvp/board-weight-2026-09-24.json",
        "scene": root / "site/owner-wood-joints-wj24-scene.json",
        "review": root / "site/owner-wood-joints-review-report.json",
    }
    expected = {
        "weight": "7425c8100c9bbf0586d8e1732138eb5ec1e6147f8418b5cf3ea95dc6108e035e",
        "scene": "74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf",
        "review": "148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695",
    }
    data = {}
    for name, path in sources.items():
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected[name]:
            raise ValueError(f"reviewed source changed: {name}")
        data[name] = json.loads(raw)
    if reviewed_report != data["review"]:
        raise ValueError("in-memory review report differs from frozen reviewed report")
    weight, scene = data["weight"], data["scene"]
    if geometry.layout_id != weight["revision_id"] or geometry.layout_id != scene["revision_id"]:
        raise ValueError("in-memory geometry revision differs")
    translations = scene["baseline_display_translations_mm"]
    moved_axes = {r["axis_id"]: r for r in scene["model_inventory"]["moved_panel_axes"]}
    if len(translations) != 8:
        raise ValueError("expected eight moved screw axes")
    rows = []
    used_translations = set()
    for source_row in weight["rows"]:
        name, group = source_row["name"], source_row["group"]
        translation = (0.0, 0.0, 0.0)
        if group in {"frame timber", "plywood panels"}:
            if name in geometry.finished_hosts:
                shape, origin = geometry.finished_hosts[name], "finished_hosts"
            elif name in geometry.panel_replacements:
                shape, origin = geometry.panel_replacements[name], "panel_replacements"
            else:
                shape, origin = source_parts[name], "preserved_source_parts"
        elif group == "corner blocks":
            shape, origin = geometry.finished_candidate_parts[name], "finished_candidate_parts"
        elif group == "block bolts nuts washers":
            axis, role = name.rsplit("/", 1)
            shape = geometry.candidate_installed_hardware[axis][role]
            origin = "candidate_installed_hardware"
        elif group == "frame bolts nuts washers":
            shape = geometry.protected["retained_12_frame_bolt_components"][name]
            origin = "protected_retained_frame_components"
        elif group == "panel kicker screws":
            visual = "fastener_" + name
            if visual in source_parts:
                shape, origin = source_parts[visual], "source_screw_display_body"
                if visual in translations:
                    translation = tuple(translations[visual])
            else:
                shape, origin = geometry.fixed_axes[name], "current_screw_axis_envelope"
                if name in moved_axes:
                    moved = moved_axes[name]
                    expected_center = tuple(s + 31.75 * d for s, d in zip(
                        moved["new_start_global_xyz_mm"], moved["axis_global_xyz_unchanged"], strict=True
                    ))
                    if math.dist(shape.Center().toTuple(), expected_center) > 1e-6:
                        raise ValueError(f"moved 63.5 mm screw envelope center differs: {name}")
            if visual in translations:
                used_translations.add(visual)
        elif group == "hold T-nuts":
            shape, origin = geometry.protected["tnuts"][name], "protected_tnuts"
        else:
            raise ValueError(f"unmapped physical inventory group: {group}")
        volume = shape.Volume()
        if not math.isclose(volume, source_row["volume_mm3"], rel_tol=1e-10, abs_tol=1e-6):
            raise ValueError(f"current volume differs from frozen weight inventory: {name}")
        center = tuple(a + b for a, b in zip(shape.Center().toTuple(), translation, strict=True))
        if not all(math.isfinite(x) for x in center) or volume <= 0:
            raise ValueError(f"invalid physical mass geometry: {name}")
        mass = volume * source_row["density_kg_m3"] / 1e9
        if not math.isclose(mass, source_row["mass_kg"], rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError(f"mass differs from frozen inventory: {name}")
        force_z = -mass * 9.80665
        rows.append({
            **source_row,
            "current_volume_mm3": volume,
            "mass_center_global_xyz_mm": center,
            "source_shape_map": origin,
            "display_translation_applied_mm": translation,
            "gravity_force_global_xyz_n": [0.0, 0.0, force_z],
            "gravity_moment_about_global_origin_nmm": [center[1] * force_z, -center[0] * force_z, 0.0],
        })
    if len(rows) != 778 or len({r["name"] for r in rows}) != len(rows):
        raise ValueError("physical inventory count or uniqueness changed")
    if used_translations != set(translations):
        raise ValueError("not all eight moved screw axes were accounted for exactly once")
    total_mass = math.fsum(r["mass_kg"] for r in rows)
    center = [math.fsum(r["mass_kg"] * r["mass_center_global_xyz_mm"][i] for r in rows) / total_mass for i in range(3)]
    result = {
        "status": "MODELED_SOLID_MASS_CENTERS_NOT_A_FRAME_RESPONSE",
        "revision_id": geometry.layout_id,
        "source_sha256": {str(sources[k].relative_to(root)): v for k, v in expected.items()},
        "physical_inventory_rows": len(rows),
        "moved_screw_axes_accounted_for": len(used_translations),
        "screw_axis_envelope_count": sum(r["source_shape_map"] == "current_screw_axis_envelope" for r in rows),
        "modeled_mass_kg": total_mass,
        "modeled_mass_center_global_xyz_mm": center,
        "gravity_force_global_xyz_n": [math.fsum(r["gravity_force_global_xyz_n"][i] for r in rows) for i in range(3)],
        "gravity_moment_about_global_origin_nmm": [math.fsum(r["gravity_moment_about_global_origin_nmm"][i] for r in rows) for i in range(3)],
        "equipment_allowance_kg_excluded_from_centroid": 25.0,
        "rows": rows,
        "mechanical_acceptance": False,
        "cad_rebuilt_or_modified": False,
        "native_solve_run": False,
        "limits": [
            "Masses are the frozen modeled-volume/density estimate, not measured part masses.",
            "Screw rows retain the original weight producer's axis-envelope fallback where no display body exists; these are not detailed purchased screw solids.",
            "The unitemized 25 kg equipment allowance has no assigned center in this export.",
            "Gravity moments are about the global origin, not individual support reactions.",
            "This supplies body-level mass centers; reduced-model load-transfer ownership still needs explicit mapping.",
        ],
    }
    destination = Path(destination)
    with destination.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    return {k: v for k, v in result.items() if k != "rows"}
