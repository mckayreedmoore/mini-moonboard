"""Source-bound arithmetic for the two upward cleat extensions; no CAD imports."""

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path.cwd()
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
OWN = Path(__file__).resolve().relative_to(ROOT)
OUT = OWN.parent / "profile-review.json"
PINS = {
    str(DOC / "occupied-adjusted-base-v3.json"): "5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7",
    str(DOC / "occupied-2026-adjustments-v3.json"): "5dfa03b785715c92717725400e73bf41b00a58160595ddf6b61b61c3b31f6134",
    str(DOC / "occupied-aligned-wire-v1.json"): "2b31d82a41cd6eb1c80e3ed84b2d0cae428fdc575b1c8c6fa27d7c3e6f0276c5",
    str(DOC / "occupied-cleat-trim-v1.json"): "4223b78f85418b37832861d8eedc936381188e4e091750bbc8c112646d7f1056",
    str(BASE / "flush-cleat-review-v1/review.json"): "7607bb2cd55d681707c3bdfec8dff48d645948360b2a9d31123e2ecd94e22023",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def main():
    assert not OUT.exists(), "issued arithmetic receipt is immutable"
    assert all(sha(path) == digest for path, digest in PINS.items())
    base = read(DOC / "occupied-adjusted-base-v3.json")
    extra = read(DOC / "occupied-2026-adjustments-v3.json")
    aligned = read(DOC / "occupied-aligned-wire-v1.json")
    trimmed = read(DOC / "occupied-cleat-trim-v1.json")
    old = read(BASE / "flush-cleat-review-v1/review.json")
    csv_path = DOC / "shop-assembly-v1/member-end-datums.csv"
    PINS[str(csv_path)] = old["source_sha256"][str(csv_path)]
    assert sha(csv_path) == PINS[str(csv_path)]
    with csv_path.open() as handle:
        ends = list(csv.DictReader(handle))
    profiles = {
        name: [(float(r["point_y_mm"]), float(r["point_z_mm"])) for r in ends
               if r["member"] == name and r["record_kind"] == "raw_profile_vertex"]
        for name in ("base_side_left", "base_side_right", "eoere_cleat_left", "eoere_cleat_right")
    }
    assert set(profiles["base_side_left"]) == set(profiles["base_side_right"])
    assert set(profiles["eoere_cleat_left"]) == set(profiles["eoere_cleat_right"])
    side_points = set(profiles["base_side_left"])
    (rear_y, rear_z), (end_y, end_z) = old["rear_profile_edge_YZ_mm"]
    assert (rear_y, rear_z) in side_points and (end_y, end_z) in side_points
    slope = (end_z - rear_z) / (end_y - rear_y)
    raw = profiles["eoere_cleat_left"]
    y0, y1 = min(p[0] for p in raw), max(p[0] for p in raw)
    z0, old_top = min(p[1] for p in raw), max(p[1] for p in raw)
    new_top = rear_z + slope * (y1 - rear_y)
    old_corner_y = rear_y + (old_top - rear_z) / slope
    polygon = [[y0, z0], [y1, z0], [y1, new_top], [y0, rear_z]]
    added_area = (y1 - old_corner_y) * (new_top - old_top) / 2
    added_volume = added_area * 38.1
    assert y0 == rear_y and new_top > old_top and len(base["axes"]) == 100
    assert len(base["screw_axes"]) == 66
    records = {r["id"]: r for r in aligned["unchanged_finished_solids"]}
    trim_records = {r["id"]: r for r in trimmed["changed_finished_solids"]}
    unchanged = []
    for name in profiles:
        record = records[name]
        PINS[record["path"]] = record["sha256"]
        assert sha(record["path"]) == record["sha256"]
        assert base["source_sha256"][record["path"]] == record["sha256"]
        assert extra["source_sha256"][record["path"]] == record["sha256"]
        assert name not in {r["id"] for r in base["changed_finished_solids"]}
        assert name in extra["unchanged_timber_ids"]
        unchanged.append(record)
    bore_rows = []
    for axis in base["axes"]:
        for receiver in axis["receivers"]:
            if not receiver.startswith("eoere_cleat_"):
                continue
            center = axis["point_xyz_mm"][1:]
            distances = [((b[0] - a[0]) * (center[1] - a[1]) - (b[1] - a[1]) * (center[0] - a[0])) / math.dist(a, b)
                         for a, b in zip(polygon, polygon[1:] + polygon[:1])]
            bore_r = axis["bore_diameter_mm"] / 2
            washer_r = axis["hardware_scenario"]["washer_od_mm"] / 2
            assert min(distances) > max(bore_r, washer_r)
            bore_rows.append({"axis_id": axis["id"], "receiver": receiver,
                              "center_yz_mm": center,
                              "minimum_bore_ligament_to_polygon_mm": min(distances) - bore_r,
                              "minimum_washer_outer_edge_margin_mm": min(distances) - washer_r})
    assert len(bore_rows) == 8
    cleats = [{"id": name, "parent_binding": trim_records[name],
               "expected_X_bounds_mm": trim_records[name]["bounds_xyz_mm"][0],
               "expected_finished_volume_mm3": trim_records[name]["volume_mm3"] + added_volume}
              for name in ("eoere_cleat_left", "eoere_cleat_right")]
    PINS[str(OWN)] = sha(OWN)
    assert all(sha(path) == digest for path, digest in PINS.items())
    result = {
        "schema": "eoere_cleat_top_extension_arithmetic/v1",
        "status": "PROPOSED_NOMINAL_PROFILE_NO_CAD_OR_MECHANICS_RUN",
        "source_sha256": PINS, "source_pin_count": len(PINS),
        "base_revision": base["revision"], "extra_revision": extra["revision"],
        "new_cleat_YZ_polygon_mm": polygon,
        "base_side_rear_edge_YZ_mm": old["rear_profile_edge_YZ_mm"],
        "top_slope_dZ_dY": slope,
        "front_height_addition_mm": new_top - old_top,
        "full_thickness_mm": 38.1, "width_mm": y1 - y0,
        "maximum_blank_length_mm": new_top - z0,
        "added_cross_section_area_mm2_each": added_area,
        "added_volume_mm3_each": added_volume,
        "nominal_two_cleat_mass_delta_kg_at_500kg_m3": added_volume * 2 * 500e-9,
        "retained_side_and_cleat_body_bindings": unchanged,
        "new_finished_cleat_expectations": cleats,
        "nominal_bore_and_washer_circle_containment": bore_rows,
        "base_100_axis_records_canonical_sha256": canonical(base["axes"]),
        "base_66_screw_records_canonical_sha256": canonical(base["screw_axes"]),
        "mechanics_ready": False, "physical_release": False,
        "required_geometry_checks": [
            "Both saved successor cleats valid single solids; original trimmed bodies are subsets.",
            "Entire top follows base_side rear edge at both X faces; no timber projects beyond that plane.",
            "Full38.1-mm thickness, full runner seat, original eight bores and washer lands retained.",
            "Only two cleat bodies change versus each frozen base/extra parent; axes, panels, harness and moved-principal layout retained.",
            "Check added timber against nominal neighboring timbers, all hardware and services in both viewer layers.",
            "Check finished CAD/mesh volumes, bounds and browser appearance; no historical mechanics pass transfers."
        ],
        "limits": [
            "This standard-library receipt supplies arithmetic and source bindings, not an executed CAD or collision check.",
            "Nominal blank extent changes from289.7 to361.1860828294mm; old offcut nesting and shop templates must not be inherited.",
            "Physical tolerance, tooling, installation, strength, revised load response and release are not evaluated."
        ],
        "reproduction_command": ".venv/bin/python " + str(OWN), "python_version": sys.version,
    }
    OUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"receipt": str(OUT), "sha256": sha(OUT),
                      "source_pins": len(PINS), "polygon_YZ_mm": polygon,
                      "added_volume_mm3_each": added_volume,
                      "maximum_blank_length_mm": new_top - z0}, indent=2))


if __name__ == "__main__":
    main()
