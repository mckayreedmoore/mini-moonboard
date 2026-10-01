#!/usr/bin/env python3
"""Independent read-only audit of taper bore preflight attempt02."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
PACKET = BASE / "current-taper-bore-clearance-preflight-attempt02"
MANIFEST = BASE / "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
BUNDLE = BASE / "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json"
TAPER = BASE / "current-taper-geometry-preflight-attempt01/current-taper-geometry-preflight.json"
LEGS = ("lumber_leg_left", "lumber_leg_right")
GEOM_TOL = 1e-5
AXIS_TOL = 1e-10


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    length = norm(a)
    if not math.isfinite(length) or length <= 0:
        raise AssertionError("nonfinite/zero vector")
    return tuple(x / length for x in a)


def read(path):
    return json.loads(path.read_text())


def verify(path_hashes):
    errors = []
    for relative, expected in path_hashes.items():
        path = ROOT / relative
        if path.is_symlink() or not path.is_file() or sha(path) != expected:
            errors.append(relative)
    return errors


def main():
    report = read(ROOT / PACKET / "current-taper-bore-clearance-preflight.json")
    pins = read(ROOT / PACKET / "source-pins.json")["files_sha256"]
    pin_failures = verify(pins)
    upstream_pins_path = BASE / "current-taper-geometry-preflight-attempt01/source-pins.json"
    upstream_pins = read(ROOT / upstream_pins_path)["files_sha256"]
    upstream_pin_failures = verify(upstream_pins)

    bundle = read(ROOT / BUNDLE)
    manifest = read(ROOT / MANIFEST)
    taper = read(ROOT / TAPER)
    bundle_ids = [r["member_id"] for r in bundle["members"]]
    physical_ids = [r["member_id"] for r in manifest["physical_members"]]
    assert len(bundle_ids) == len(set(bundle_ids)) == 50
    assert len(physical_ids) == len(set(physical_ids)) == 50
    assert set(bundle_ids) == set(physical_ids)

    candidate_axes = manifest["candidate_bolt_axes"]
    assert len(candidate_axes) == len({r["axis_id"] for r in candidate_axes}) == 92
    physical_set = set(physical_ids)
    candidate_receiver_rows = []
    for axis in candidate_axes:
        receivers = axis["receiver_member_ids"]
        interval_ids = [r["receiver_id"] for r in axis["geometry"]["wood_receiver_intervals"]]
        assert len(receivers) > 0 and len(receivers) == len(set(receivers))
        assert set(receivers) <= physical_set
        assert set(receivers) == set(interval_ids)
        candidate_receiver_rows.append({"axis_id": axis["axis_id"], "receiver_member_ids": receivers})
    candidate_leg_rows = [
        row for row in candidate_receiver_rows if set(row["receiver_member_ids"]) & set(LEGS)
    ]

    # The 66 panel/kicker screws are a distinct Hillman policy inventory, not
    # part of the 92 candidate structural bolt axis table.
    panel_axes = manifest["panel_kicker_screw_axes"]
    assert len(panel_axes) == 66
    panel_leg_rows = [
        {"axis_id": row["axis_id"], "receiver_member": row["receiver_member"]}
        for row in panel_axes if row.get("receiver_member") in LEGS
    ]

    retained = manifest["retained_frame_bolt_axes"]
    assert len(retained) == len({r["axis_id"] for r in retained}) == 12
    taper_by_leg = {r["member_id"]: r for r in taper["members"]}
    measured = {}
    for leg in LEGS:
        retained_leg = [r for r in retained if leg in r["members_as_recorded"]]
        assert len(retained_leg) == 4
        step = ROOT / BASE / "current-full-frame-member-solids-attempt01/bundle/members" / f"{leg}.step"
        shape = cq.importers.importStep(str(step)).val()
        assert shape.isValid() and len(shape.Solids()) == 1
        cyl_faces = []
        for face in shape.Faces():
            if face.geomType() != "CYLINDER":
                continue
            adaptor = BRepAdaptor_Surface(face.wrapped, True)
            cyl = adaptor.Cylinder()
            loc = cyl.Axis().Location()
            direction = cyl.Axis().Direction()
            cyl_faces.append({
                "location": (loc.X(), loc.Y(), loc.Z()),
                "direction": unit((direction.X(), direction.Y(), direction.Z())),
                "radius": cyl.Radius(),
                "v0": adaptor.FirstVParameter(),
                "v1": adaptor.LastVParameter(),
                "area": face.Area(),
            })
        assert len(cyl_faces) == 4
        bore_rows = []
        matched_axis_ids = []
        grain = unit(tuple(taper_by_leg[leg]["grain_axis_xyz"]))
        taper_start = taper_by_leg[leg]["taper_start_grain_station_mm"]
        taper_end = taper_by_leg[leg]["taper_end_grain_station_mm"]
        for cyl in cyl_faces:
            matches = []
            for bolt in retained_leg:
                bolt_origin = tuple(bolt["origin_global_xyz_mm"])
                bolt_direction = unit(tuple(bolt["axis_global_xyz"]))
                direction_error = norm(cross(cyl["direction"], bolt_direction))
                line_distance = norm(cross(sub(bolt_origin, cyl["location"]), cyl["direction"]))
                if direction_error <= AXIS_TOL and line_distance <= GEOM_TOL:
                    matches.append((bolt, direction_error, line_distance))
            assert len(matches) == 1
            bolt, direction_error, line_distance = matches[0]
            member_pair_ok = any(
                set(a.get("source_member_pair_as_recorded", a.get("member_pair", []))) == set(bolt["members_as_recorded"])
                for a in bolt["geometric_member_pair_associations"]
            )
            assert member_pair_ok
            matched_axis_ids.append(bolt["axis_id"])
            station_rate = dot(cyl["direction"], grain)
            assert abs(station_rate) <= AXIS_TOL
            radial_projection = cyl["radius"] * math.sqrt(max(0.0, 1.0 - station_rate * station_rate))
            end_stations = (
                dot(cyl["location"], grain) + cyl["v0"] * station_rate,
                dot(cyl["location"], grain) + cyl["v1"] * station_rate,
            )
            lo = min(end_stations) - radial_projection
            hi = max(end_stations) + radial_projection
            gap = max(taper_start - hi, lo - taper_end, 0.0)
            overlaps = not (hi < taper_start - GEOM_TOL or lo > taper_end + GEOM_TOL)
            bore_rows.append({
                "axis_id": bolt["axis_id"],
                "member_pair": bolt["members_as_recorded"],
                "direction_error_sine": direction_error,
                "line_distance_mm": line_distance,
                "radius_mm": cyl["radius"],
                "v_bounds_mm": [cyl["v0"], cyl["v1"]],
                "projected_interval_mm": [lo, hi],
                "taper_interval_mm": [taper_start, taper_end],
                "gap_mm": gap,
                "overlaps_tolerance_expanded_taper": overlaps,
            })
        assert len(matched_axis_ids) == len(set(matched_axis_ids)) == 4
        assert set(matched_axis_ids) == {row["axis_id"] for row in retained_leg}
        measured[leg] = {
            "cylinder_faces": len(cyl_faces),
            "mapped_axis_ids": sorted(matched_axis_ids),
            "minimum_gap_mm": min(row["gap_mm"] for row in bore_rows),
            "overlap_count": sum(row["overlaps_tolerance_expanded_taper"] for row in bore_rows),
            "bores": sorted(bore_rows, key=lambda row: row["axis_id"]),
        }

    report_bores = {
        leg: {r["axis_id"]: r for r in report["leg_bore_envelopes"][leg]["bores"]}
        for leg in LEGS
    }
    comparison = []
    for leg in LEGS:
        for row in measured[leg]["bores"]:
            frozen = report_bores[leg][row["axis_id"]]
            comparison.append({
                "axis_id": row["axis_id"],
                "independent_gap_mm": row["gap_mm"],
                "producer_gap_mm": frozen["clear_gap_mm"],
                "gap_delta_mm": row["gap_mm"] - frozen["clear_gap_mm"],
                "independent_interval_mm": row["projected_interval_mm"],
                "producer_interval_mm": frozen["bore_envelope_grain_station_interval_mm"],
            })
            assert math.isclose(row["gap_mm"], frozen["clear_gap_mm"], rel_tol=0.0, abs_tol=1e-9)
            assert all(math.isclose(a, b, rel_tol=0.0, abs_tol=1e-9) for a, b in zip(row["projected_interval_mm"], frozen["bore_envelope_grain_station_interval_mm"], strict=True))

    result = {
        "audit_schema": "independent_taper_bore_review/v1",
        "attempt02_report_sha256": sha(ROOT / PACKET / "current-taper-bore-clearance-preflight.json"),
        "attempt02_source_pin_failures": pin_failures,
        "upstream_216_source_pin_count": len(upstream_pins),
        "upstream_source_pin_failures": upstream_pin_failures,
        "bundle_and_manifest_member_ids_match": True,
        "bundle_member_count": len(bundle_ids),
        "manifest_physical_member_count": len(physical_ids),
        "candidate_structural_bolt_axis_count": len(candidate_axes),
        "candidate_structural_bolt_leg_receiver_count": len(candidate_leg_rows),
        "retained_frame_bolt_axis_count": len(retained),
        "panel_kicker_hillman_axis_count": len(panel_axes),
        "panel_kicker_hillman_leg_receiver_count": len(panel_leg_rows),
        "panel_kicker_policy": "66 separate Hillman panel/kicker screw axes; their receiver_member inventory was checked separately and no row names either leg. Their physical hole geometry is not created or structurally qualified by this audit.",
        "independent_cylinder_projection": measured,
        "producer_vs_independent_comparison": comparison,
        "criterion_status": report["criterion_disposition"]["status"],
        "criterion_id": report["criterion_disposition"]["criterion_id"],
        "release": report["release"],
        "cad_envelope_screen": report["cad_envelope_screen"],
        "toolchain_versions": {
            "cadquery": __import__("importlib.metadata", fromlist=["version"]).version("cadquery"),
            "cadquery_ocp": __import__("importlib.metadata", fromlist=["version"]).version("cadquery-ocp"),
        },
    }
    assert not pin_failures and not upstream_pin_failures
    assert report["criterion_disposition"]["status"] == "pending"
    assert not any(report["release"].values())
    assert result["candidate_structural_bolt_leg_receiver_count"] == 0
    assert result["panel_kicker_hillman_leg_receiver_count"] == 0
    out = ROOT / Path(__file__).parent / "independent-audit.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "source_pin_failures": len(pin_failures),
        "upstream_pin_count": len(upstream_pins),
        "upstream_pin_failures": len(upstream_pin_failures),
        "mapped_bores": sum(row["cylinder_faces"] for row in measured.values()),
        "min_gap_mm": min(row["minimum_gap_mm"] for row in measured.values()),
        "candidate_leg_receivers": len(candidate_leg_rows),
        "panel_screw_leg_receivers": len(panel_leg_rows),
        "criterion_status": result["criterion_status"],
        "release": result["release"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
