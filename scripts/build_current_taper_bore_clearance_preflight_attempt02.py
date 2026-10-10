#!/usr/bin/env python3
"""Source-pinned CAD-only bore envelope screen for the reviewed wood-joint model."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
ATTEMPT01 = BASE + "current-taper-bore-clearance-preflight-attempt01"
PACKET = BASE + "current-taper-bore-clearance-preflight-attempt02"
BUNDLE = BASE + "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json"
INPUT_MANIFEST = BASE + "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
TAPER_PACKET = BASE + "current-taper-geometry-preflight-attempt01"
TAPER_REPORT = TAPER_PACKET + "/current-taper-geometry-preflight.json"
TAPER_PINS = TAPER_PACKET + "/source-pins.json"
CRITERIA = "docs/floor-runner-mvp-criteria.md"
METHOD_MAP = "docs/wood-joints-mvp/criteria-method-map.md"
TAPER_CHECKS = "scripts/floor_taper_checks.py"
PRODUCER = "scripts/build_current_taper_bore_clearance_preflight_attempt02.py"
TESTS = "tests/test_current_taper_bore_clearance_preflight_attempt02.py"
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
LEGS = ("lumber_leg_left", "lumber_leg_right")
CRITERION = "taper_taper_region_unbored_torsion_applicable"
GEOMETRY_TOLERANCE_MM = 1e-5
AXIS_TOLERANCE = 1e-10

# These pins were checked against the upstream taper preflight and the reviewed
# attempt04 manifest before this producer was written. Bundle STEP hashes are
# independently repeated in the bundle manifest and the upstream 216-file pin.
INPUT_PINS = {
    "current-candidate.json": "f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4",
    "wood-joints-candidate.json": "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
    BUNDLE: "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420",
    BASE + "current-full-frame-member-solids-attempt01/bundle/members/lumber_leg_left.step": "1416e3aec21eea2993542f8266649ebe0aec50b3ec6444f445f18f88cbffa065",
    BASE + "current-full-frame-member-solids-attempt01/bundle/members/lumber_leg_right.step": "e346646efb8bdf9c03d45dfa024900622abcd65fe0d58bf11c6dcd3735bedff4",
    INPUT_MANIFEST: "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    TAPER_REPORT: "d1c0b701d1b8d2ec265b1ebe44399a3172002c8cd2afd2e5f7ec61bd2028a401",
    TAPER_PINS: "c4e3a89efd6cf60b0368dc8d62887f76d1b1baa40c0241188301b474b9263d7c",
    CRITERIA: "f6b5591bbbb2aaf87553095e04fbe5abd66d38a926a3efb66711420492f0f090",
    METHOD_MAP: "bd356fc8751e17c860fd6df8150c3076b9cfbd742fff9b0de518b970868f324a",
    TAPER_CHECKS: "bf15d8983b42d95dda0d0329bc2d8c2664f9c146813f21e1a0cc8f0f6a3bf1c3",
    ATTEMPT01 + "/README.md": "2439a5743941adb07d0da9d85eca6d0a77308a4459857baecb87a61c9a17bf86",
    ATTEMPT01 + "/current-taper-bore-clearance-preflight.json": "883c7e34b1ae10c72d73d3cd284b5cb233032fe6be972d64dc469407271da969",
    ATTEMPT01 + "/source-pins.json": "c03c3e2a3009bcf4123766e6a86a9f09e6122cc4f2ed3442dcab0968ef565734",
    ATTEMPT01 + "/verification.json": "2ff5366622c4a48c6ec218fa3f65684f3a4a11fcd656dd550ff3d2a7e53f3a6d",
    ATTEMPT01 + "/SHA256SUMS": "98861e75d4b41f887632cf3cc221c446dc5c981d9bbd8d2593e637d4e8d242a3",
    "scripts/build_current_taper_bore_clearance_preflight_attempt01.py": "fe793b75f86e1fde8a64c4ee9251de515548dd381879e05f462dc04df47f28e2",
    "tests/test_current_taper_bore_clearance_preflight_attempt01.py": "0dda9e02f0cb8caad1d17606a53a6ea62f836eb1d2a657168f8eba9a1f62cd17",
}


class NoGoError(ValueError):
    """The source geometry cannot support a clear applicability screen."""


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON number: {value}")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(), object_pairs_hook=_object, parse_constant=_constant)
    if not isinstance(value, dict):
        raise TypeError(f"JSON object required: {path}")
    return value


def finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise NoGoError(f"nonfinite or nonnumeric {label}")
    return float(value)


def vector(value: Any, label: str) -> tuple[float, float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise NoGoError(f"three coordinates required for {label}")
    return tuple(finite(item, label) for item in value)


def dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def subtract(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(x - y for x, y in zip(a, b, strict=True))


def norm(value: tuple[float, ...]) -> float:
    return math.sqrt(dot(value, value))


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(value: tuple[float, float, float], label: str) -> tuple[float, float, float]:
    magnitude = norm(value)
    if not math.isfinite(magnitude) or magnitude <= 0:
        raise NoGoError(f"invalid {label}")
    return tuple(item / magnitude for item in value)


def verify_pins(root: Path, pins: dict[str, str]) -> None:
    for relative, expected in pins.items():
        path = root / relative
        if path.is_symlink() or not path.is_file() or sha256(path) != expected:
            raise ValueError(f"source hash mismatch: {relative}")


def verify_upstream_pins(root: Path, pins: dict[str, str]) -> None:
    upstream = read_json(root / TAPER_PINS)
    rows = upstream.get("files_sha256")
    if not isinstance(rows, dict) or len(rows) != 216:
        raise ValueError("upstream taper source pin inventory must contain 216 files")
    verify_pins(root, rows)
    for path, digest in INPUT_PINS.items():
        if path in rows and rows[path] != digest:
            raise ValueError(f"upstream/current pin disagreement: {path}")


def unique_rows(rows: Any, key: str, count: int, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise NoGoError(f"{label} rows are missing")
    ids = [row.get(key) if isinstance(row, dict) else None for row in rows]
    if len(ids) != count or any(not isinstance(item, str) or not item for item in ids) or len(set(ids)) != count:
        raise NoGoError(f"expected exactly {count} unique {label} {key} rows")
    return dict(zip(ids, rows, strict=True))


def validate_sources(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    verify_pins(root, INPUT_PINS)
    verify_upstream_pins(root, INPUT_PINS)
    bundle = read_json(root / BUNDLE)
    manifest = read_json(root / INPUT_MANIFEST)
    taper = read_json(root / TAPER_REPORT)
    if bundle.get("candidate") != CANDIDATE or bundle.get("geometry_revision_id") != REVISION:
        raise NoGoError("member bundle candidate/revision mismatch")
    if manifest.get("candidate") != CANDIDATE or manifest.get("geometry_revision_id") != REVISION:
        raise NoGoError("attempt04 manifest candidate/revision mismatch")
    if manifest.get("manifest_id") != "current-full-frame-input-manifest-attempt04":
        raise NoGoError("unexpected full-frame manifest identity")
    if taper.get("candidate") != CANDIDATE or taper.get("geometry_revision_id") != REVISION:
        raise NoGoError("taper report candidate/revision mismatch")
    unique_rows(bundle.get("members"), "member_id", 50, "bundle member")
    if (manifest.get("inventory_counts", {}).get("full_physical_member_nodes") != 50
            or manifest.get("inventory_counts", {}).get("candidate_bolt_axes") != 92
            or manifest.get("inventory_counts", {}).get("retained_starting_frame_bolt_axes") != 12):
        raise NoGoError("attempt04 reviewed geometry inventory counts changed")
    return bundle, manifest, taper


def candidate_receiver_audit(manifest: dict[str, Any]) -> dict[str, Any]:
    axes = unique_rows(manifest.get("candidate_bolt_axes"), "axis_id", 92, "candidate axis")
    physical_ids = {row["member_id"] for row in manifest.get("physical_members", []) if isinstance(row, dict)}
    membership_rows = []
    leg_receivers = []
    for axis_id, axis in axes.items():
        receivers = axis.get("receiver_member_ids")
        if not isinstance(receivers, list) or not receivers or any(not isinstance(x, str) or not x for x in receivers):
            raise NoGoError(f"missing receiver membership for {axis_id}")
        if len(set(receivers)) != len(receivers):
            raise NoGoError(f"duplicate receiver membership for {axis_id}")
        if not set(receivers) <= physical_ids:
            raise NoGoError(f"receiver membership references an unknown current member: {axis_id}")
        interval_rows = axis.get("geometry", {}).get("wood_receiver_intervals")
        if not isinstance(interval_rows, list):
            raise NoGoError(f"receiver interval inventory missing for {axis_id}")
        interval_ids = [row.get("receiver_id") if isinstance(row, dict) else None for row in interval_rows]
        if len(interval_ids) != len(set(interval_ids)) or set(interval_ids) != set(receivers):
            raise NoGoError(f"receiver list/interval inventory mismatch for {axis_id}")
        found = sorted(set(receivers) & set(LEGS))
        if found:
            leg_receivers.append({"axis_id": axis_id, "leg_receivers": found})
        membership_rows.append({"axis_id": axis_id, "receiver_member_ids": receivers})
    return {
        "candidate_axis_count": len(axes),
        "receiver_membership_rows_checked": len(membership_rows),
        "receiver_membership_total": sum(len(row["receiver_member_ids"]) for row in membership_rows),
        "leg_receiver_axis_count": len(leg_receivers),
        "leg_receiver_axes": leg_receivers,
        "all_candidate_receiver_memberships_exclude_both_legs": not leg_receivers,
        "membership_rows": membership_rows,
    }


def retained_axes_by_leg(manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    unique_rows(manifest.get("retained_frame_bolt_axes"), "axis_id", 12, "retained frame axis")
    result: dict[str, list[dict[str, Any]]] = {}
    for leg in LEGS:
        rows = []
        for axis in manifest["retained_frame_bolt_axes"]:
            pair = axis.get("members_as_recorded")
            if isinstance(pair, list) and leg in pair:
                if len(pair) != 2 or len(set(pair)) != 2:
                    raise NoGoError(f"invalid retained member pair: {axis.get('axis_id')}")
                pairs = axis.get("geometric_member_pair_associations")
                if not isinstance(pairs, list) or not any(
                    set(item.get("source_member_pair_as_recorded", item.get("member_pair", []))) == set(pair)
                    for item in pairs if isinstance(item, dict)
                ):
                    raise NoGoError(f"retained pair association is not source-bound: {axis.get('axis_id')}")
                rows.append(axis)
        if len(rows) != 4:
            raise NoGoError(f"expected four retained frame axes in {leg}")
        result[leg] = rows
    return result


def read_cylinder_faces(step_path: Path, member_id: str) -> list[dict[str, Any]]:
    try:
        import cadquery as cq
        from OCP.BRepAdaptor import BRepAdaptor_Surface
    except ImportError as exc:
        raise NoGoError(f"CadQuery/OCP unavailable: {exc}") from exc
    shape = cq.importers.importStep(str(step_path)).val()
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise NoGoError(f"expected one valid solid in {step_path}")
    cylinders = []
    for face in shape.Faces():
        if face.geomType() != "CYLINDER":
            continue
        adaptor = BRepAdaptor_Surface(face.wrapped, True)
        cylinder = adaptor.Cylinder()
        location = cylinder.Axis().Location()
        direction = cylinder.Axis().Direction()
        values = {
            "member_id": member_id,
            "axis_location_xyz_mm": [location.X(), location.Y(), location.Z()],
            "axis_direction_xyz": [direction.X(), direction.Y(), direction.Z()],
            "radius_mm": cylinder.Radius(),
            "v_first_mm": adaptor.FirstVParameter(),
            "v_last_mm": adaptor.LastVParameter(),
            "face_area_mm2": face.Area(),
        }
        # Validate every scalar before it can enter an output JSON document.
        for field in ("axis_location_xyz_mm", "axis_direction_xyz"):
            vector(values[field], field)
        for field in ("radius_mm", "v_first_mm", "v_last_mm", "face_area_mm2"):
            finite(values[field], field)
        if values["radius_mm"] <= 0 or values["v_last_mm"] <= values["v_first_mm"] or values["face_area_mm2"] <= 0:
            raise NoGoError(f"invalid bounded cylindrical face in {member_id}")
        cylinders.append(values)
    return cylinders


def cylinder_axis_match(cylinder: dict[str, Any], bolt: dict[str, Any]) -> tuple[bool, float, float]:
    surf_origin = vector(cylinder["axis_location_xyz_mm"], "cylinder axis location")
    surf_dir = unit(vector(cylinder["axis_direction_xyz"], "cylinder axis direction"), "cylinder direction")
    bolt_origin = vector(bolt.get("origin_global_xyz_mm"), "retained axis origin")
    bolt_dir = unit(vector(bolt.get("axis_global_xyz"), "retained axis direction"), "retained axis direction")
    direction_error = norm(cross(surf_dir, bolt_dir))
    line_distance = norm(cross(subtract(bolt_origin, surf_origin), surf_dir))
    return direction_error <= AXIS_TOLERANCE and line_distance <= GEOMETRY_TOLERANCE_MM, direction_error, line_distance


def map_leg_cylinders(manifest: dict[str, Any], root: Path) -> dict[str, list[dict[str, Any]]]:
    per_leg_axes = retained_axes_by_leg(manifest)
    mapped: dict[str, list[dict[str, Any]]] = {}
    for leg in LEGS:
        step_path = root / BASE / "current-full-frame-member-solids-attempt01/bundle/members" / f"{leg}.step"
        cylinders = read_cylinder_faces(step_path, leg)
        if len(cylinders) != 4:
            raise NoGoError(f"expected every one of the four {leg} bore cylinders, found {len(cylinders)}")
        matches = []
        for cylinder in cylinders:
            eligible = []
            for bolt in per_leg_axes[leg]:
                ok, direction_error, line_distance = cylinder_axis_match(cylinder, bolt)
                if ok:
                    eligible.append((bolt, direction_error, line_distance))
            if len(eligible) != 1:
                raise NoGoError(f"cylinder does not map uniquely to one retained axis in {leg}")
            bolt, direction_error, line_distance = eligible[0]
            matches.append({
                "axis_id": bolt["axis_id"],
                "member_pair": bolt["members_as_recorded"],
                "axis_location_xyz_mm": cylinder["axis_location_xyz_mm"],
                "axis_direction_xyz": cylinder["axis_direction_xyz"],
                "radius_mm": cylinder["radius_mm"],
                "v_parameter_bounds_mm": [cylinder["v_first_mm"], cylinder["v_last_mm"]],
                "face_area_mm2": cylinder["face_area_mm2"],
                "axis_direction_error_sine": direction_error,
                "centerline_perpendicular_distance_mm": line_distance,
            })
        axis_ids = [row["axis_id"] for row in matches]
        expected_ids = {row["axis_id"] for row in per_leg_axes[leg]}
        if len(axis_ids) != len(set(axis_ids)) or set(axis_ids) != expected_ids:
            raise NoGoError(f"missing or duplicated cylindrical mapping in {leg}")
        mapped[leg] = sorted(matches, key=lambda row: row["axis_id"])
    return mapped


def projected_envelope(cylinder: dict[str, Any], grain: tuple[float, float, float]) -> tuple[float, float, float, float]:
    location = vector(cylinder["axis_location_xyz_mm"], "cylinder axis location")
    direction = unit(vector(cylinder["axis_direction_xyz"], "cylinder axis direction"), "cylinder axis direction")
    radius = finite(cylinder["radius_mm"], "cylinder radius")
    v0, v1 = (finite(v, "cylinder V bound") for v in cylinder["v_parameter_bounds_mm"])
    if v1 <= v0 or radius <= 0:
        raise NoGoError("invalid cylinder projection bounds")
    direction_station = dot(direction, grain)
    radius_projection = radius * math.sqrt(max(0.0, 1.0 - direction_station * direction_station))
    centerline_stations = (dot(location, grain) + v0 * direction_station, dot(location, grain) + v1 * direction_station)
    return min(centerline_stations) - radius_projection, max(centerline_stations) + radius_projection, radius_projection, direction_station


def compare_to_taper(mapped: dict[str, list[dict[str, Any]]], taper: dict[str, Any]) -> dict[str, Any]:
    taper_members = unique_rows(taper.get("members"), "member_id", 2, "taper member")
    output = {}
    for leg in LEGS:
        record = taper_members[leg]
        grain = unit(vector(record.get("grain_axis_xyz"), "pinned leg grain axis"), "leg grain axis")
        start = finite(record.get("taper_start_grain_station_mm"), "taper start station")
        end = finite(record.get("taper_end_grain_station_mm"), "taper end station")
        if end <= start or record.get("current_1_to_12_geometry_matches") is not True:
            raise NoGoError(f"invalid measured taper interval for {leg}")
        rows = []
        for bore in mapped[leg]:
            lo, hi, radial, direction_station = projected_envelope(bore, grain)
            if abs(direction_station) > AXIS_TOLERANCE:
                raise NoGoError(f"bore axis is not perpendicular to the pinned grain direction: {bore['axis_id']}")
            if hi < start:
                gap = start - hi
            elif lo > end:
                gap = lo - end
            else:
                gap = 0.0
            touches_with_tolerance = not (hi < start - GEOMETRY_TOLERANCE_MM or lo > end + GEOMETRY_TOLERANCE_MM)
            rows.append({
                **bore,
                "bore_envelope_grain_station_interval_mm": [lo, hi],
                "radial_projection_mm": radial,
                "taper_interval_grain_station_mm": [start, end],
                "clear_gap_mm": gap,
                "envelope_intersects_or_touches_with_source_tolerance": touches_with_tolerance,
            })
        output[leg] = {
            "grain_axis_xyz": list(grain),
            "taper_interval_grain_station_mm": [start, end],
            "bore_count": len(rows),
            "bores": rows,
            "minimum_bore_envelope_gap_mm": min(row["clear_gap_mm"] for row in rows),
            "all_bore_envelopes_clear_by_more_than_tolerance": all(
                not row["envelope_intersects_or_touches_with_source_tolerance"] for row in rows
            ),
        }
    return output


def build_report(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, str]]:
    bundle, manifest, taper = validate_sources(root)
    pins = dict(INPUT_PINS)
    pins[PRODUCER] = sha256(root / PRODUCER)
    pins[TESTS] = sha256(root / TESTS)
    try:
        candidate = candidate_receiver_audit(manifest)
        mapped = map_leg_cylinders(manifest, root)
        measured = compare_to_taper(mapped, taper)
        clear = candidate["all_candidate_receiver_memberships_exclude_both_legs"] and all(
            row["all_bore_envelopes_clear_by_more_than_tolerance"] for row in measured.values()
        )
        no_go_reasons: list[str] = []
        if not candidate["all_candidate_receiver_memberships_exclude_both_legs"]:
            no_go_reasons.append("one or more candidate bolt receiver memberships include a leg")
        for leg, row in measured.items():
            if not row["all_bore_envelopes_clear_by_more_than_tolerance"]:
                no_go_reasons.append(f"one or more {leg} bore envelopes meet or enter the taper interval")
    except (NoGoError, KeyError, TypeError, ValueError) as exc:
        candidate = None
        measured = None
        clear = False
        no_go_reasons = [str(exc)]
    try:
        cq_version = importlib.metadata.version("cadquery")
        ocp_version = importlib.metadata.version("cadquery-ocp")
    except (ImportError, importlib.metadata.PackageNotFoundError) as exc:
        cq_version = None
        ocp_version = None
        clear = False
        no_go_reasons.append(f"CAD kernel runtime version unavailable: {exc}")
    report = {
        "schema": "wood_joint_taper_bore_clearance_preflight/v2",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "predecessor_attempt01": {
            "packet_path": ATTEMPT01,
            "report_sha256": INPUT_PINS[ATTEMPT01 + "/current-taper-bore-clearance-preflight.json"],
            "producer_sha256": INPUT_PINS["scripts/build_current_taper_bore_clearance_preflight_attempt01.py"],
            "test_sha256": INPUT_PINS["tests/test_current_taper_bore_clearance_preflight_attempt01.py"],
            "attempt01_bytes_mutated": False,
        },
        "inputs": {
            "member_bundle_path": BUNDLE,
            "reviewed_manifest_path": INPUT_MANIFEST,
            "taper_geometry_report_path": TAPER_REPORT,
            "bundle_member_count": len(bundle["members"]),
            "candidate_bolt_axis_count": 92,
            "retained_frame_bolt_axis_count": 12,
            "leg_step_hashes": {leg: INPUT_PINS[BASE + f"current-full-frame-member-solids-attempt01/bundle/members/{leg}.step"] for leg in LEGS},
        },
        "toolchain": {"cadquery": cq_version, "cadquery_ocp": ocp_version},
        "projection_method": {
            "surface_source": "all analytic CYLINDER faces from each exact pinned leg STEP BRep, read through OCP BRepAdaptor_Surface axis, location, radius and finite V bounds",
            "mapping": "unique parallel centerline match plus the exact retained manifest member pair; no face ordinal",
            "envelope": "full circular-cylinder radial projection over the bounded face V interval; conservative if a face is angularly trimmed",
            "geometry_tolerance_mm": GEOMETRY_TOLERANCE_MM,
            "geometry_tolerance_source": "upstream current taper geometry preflight consistency tolerance",
            "axis_tolerance": AXIS_TOLERANCE,
            "axis_tolerance_source": "upstream current taper geometry preflight unit-axis tolerance",
            "units": "mm; grain station is the pinned global dot product used by the current taper geometry preflight",
        },
        "candidate_receiver_audit": candidate,
        "leg_bore_envelopes": measured,
        "cad_envelope_screen": "CLEAR_WITHIN_PINNED_CAD_ENVELOPES" if clear else "NO_GO_OR_UNRESOLVED",
        "no_go_reasons": no_go_reasons,
        "criterion_disposition": {
            "criterion_id": CRITERION,
            "status": "pending",
            "reason": "The adopted criteria table requires a fresh current case. This geometry-only envelope screen is supporting input and cannot disposition the criterion.",
        },
        "claim_limits": [
            "Geometry-only CAD evidence from source-pinned STEP BReps; no actual hole or cut inspection.",
            "No physical hardware sizing, bore fit, delivered-part or installation claim.",
            "No native/CAD identity or mesh equivalence claim; no fresh case, torsion strength result, or criterion acceptance.",
            "Clear envelope separation only tests geometric overlap with the measured taper station interval; it does not validate the torsion method or qualify failure modes.",
        ],
        "release": {"candidate_accepted": False, "fabrication_released": False, "climbing_released": False},
    }
    if clear and measured is not None:
        report["claim_limits"].append("No candidate receiver membership references either leg; no candidate bolt bore is included in these leg solids.")
    return report, pins


def artifact_files(root: Path = ROOT) -> dict[str, bytes]:
    report, pins = build_report(root)
    pin_doc = {
        "schema": "wood_joint_taper_bore_clearance_source_pins/v2",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "files_sha256": pins,
    }
    readme = f"""# Current taper bore clearance preflight — attempt02

This append-only packet screens the reviewed `{REVISION}` CAD geometry for bore-cylinder envelope overlap with the measured leg taper interval. It reads the exact full-frame member bundle, exact left/right leg STEP files, reviewed attempt04 manifest, upstream taper report and source pins. The upstream taper packet rechecked all 216 of its pinned sources before this result was produced.

This revision preserves attempt01 and pins its complete packet, producer and test bytes. It fixes the focused test's over-specific error-message match; no CAD inputs or geometry method changed.

The producer extracts every cylindrical face from each exact leg STEP with CadQuery {report['toolchain']['cadquery']} / OCP {report['toolchain']['cadquery_ocp']}. It maps each face to one of four retained frame-bolt axes in that leg using the source member pair and analytic centerline; face ordinals are not used. It checks all 92 candidate `receiver_member_ids` against their corresponding per-receiver interval rows and finds {report['candidate_receiver_audit']['leg_receiver_axis_count'] if report['candidate_receiver_audit'] else 'unresolved'} candidate receiver memberships in the legs. The full-circumference cylinder envelope is projected onto the pinned global grain station and compared with the taper interval from the upstream CAD preflight.

Result: **{report['cad_envelope_screen']}**. The measured minimum envelope-to-taper gap is {min((row['minimum_bore_envelope_gap_mm'] for row in report['leg_bore_envelopes'].values()), default=float('nan')):.9f} mm when all mappings resolve. The full adopted criterion `{CRITERION}` remains **pending** because its authoritative table requires a fresh current case.

This is geometry-only CAD evidence. It does not establish actual holes or cuts, physical hardware size or fit, native/CAD identity, mesh equivalence, fresh case results, torsion strength, or criterion acceptance. Release flags remain false.

From the repository root, reproduce with:

```sh
.venv/bin/python -B scripts/{Path(PRODUCER).name} --check
```

The producer verifies fixed source hashes, the upstream taper packet's 216 source pins, exact member/axis inventories, unique cylinder-to-axis mappings, finite numeric data and byte-identical packet outputs. `--write` is exclusive and refuses an existing packet.
"""
    verification = {
        "schema": "wood_joint_taper_bore_clearance_verification/v2",
        "cad_envelope_screen": report["cad_envelope_screen"],
        "candidate_axis_count": 92,
        "retained_frame_axis_count": 12,
        "mapped_bores": 8 if report["leg_bore_envelopes"] is not None else 0,
        "candidate_leg_receiver_axis_count": report["candidate_receiver_audit"]["leg_receiver_axis_count"] if report["candidate_receiver_audit"] else None,
        "criterion_status": "pending",
        "native_run_performed": False,
        "release": False,
    }
    files = {
        "README.md": readme.encode(),
        "current-taper-bore-clearance-preflight.json": json_bytes(report),
        "source-pins.json": json_bytes(pin_doc),
        "verification.json": json_bytes(verification),
    }
    sums = "".join(f"{hashlib.sha256(content).hexdigest()}  {name}\n" for name, content in sorted(files.items()))
    files["SHA256SUMS"] = sums.encode()
    return files


def write_packet(root: Path = ROOT) -> None:
    target = root / PACKET
    if target.exists():
        raise FileExistsError(f"append-only packet already exists: {target}")
    files = artifact_files(root)
    target.mkdir(parents=True, exist_ok=False)
    for name, content in files.items():
        path = target / name
        with path.open("xb") as stream:
            stream.write(content)


def check_packet(root: Path = ROOT) -> dict[str, Any]:
    target = root / PACKET
    expected = artifact_files(root)
    if not target.is_dir() or target.is_symlink():
        raise FileNotFoundError(f"packet directory missing or unsafe: {target}")
    actual_names = {path.name for path in target.iterdir()}
    if actual_names != set(expected):
        raise ValueError("packet file inventory mismatch")
    for name, content in expected.items():
        path = target / name
        if path.is_symlink() or not path.is_file() or path.read_bytes() != content:
            raise ValueError(f"packet output mismatch: {name}")
    report = read_json(target / "current-taper-bore-clearance-preflight.json")
    return {
        "schema": "wood_joint_taper_bore_clearance_verification/v2",
        "cad_envelope_screen": report["cad_envelope_screen"],
        "mapped_bores": sum(row["bore_count"] for row in report["leg_bore_envelopes"].values()) if report["leg_bore_envelopes"] else 0,
        "candidate_leg_receiver_axis_count": report["candidate_receiver_audit"]["leg_receiver_axis_count"] if report["candidate_receiver_audit"] else None,
        "criterion_status": "pending",
        "native_run_performed": False,
        "release": False,
        "report_sha256": sha256(target / "current-taper-bore-clearance-preflight.json"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        write_packet()
        print(json.dumps(check_packet(), sort_keys=True))
    else:
        print(json.dumps(check_packet(), sort_keys=True))


if __name__ == "__main__":
    main()
