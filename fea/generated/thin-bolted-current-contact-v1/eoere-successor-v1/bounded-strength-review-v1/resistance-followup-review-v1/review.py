"""Independent source-only resistance-followup review of its once-only replay.

No original calculation replay, test suite, geometry construction or solver is
invoked here. Frozen inputs are read and exact dimensional/force accounting is
checked independently. The issued packet and earlier review remain unchanged.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = next(
    p
    for p in Path(__file__).resolve().parents
    if (p / "current-candidate.json").is_file()
)
OWN = Path(__file__).resolve().parent
BASE = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1"
)
PACKET = BASE / "resistance-followup-v1"
EARLIER_REVIEW = OWN.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def require(ok, message):
    if not ok:
        raise ValueError(message)


def snapshot():
    files = [
        p / n
        for p in (BASE, PACKET)
        for n in (
            "README.md",
            "analyze.py",
            "inputs.json",
            "result.json",
            "verification.json",
        )
    ]
    files += [
        EARLIER_REVIEW / n
        for n in (
            "review.py",
            "review-result.json",
            "replay/result.json",
            "replay/details.json",
        )
    ]
    return {str(p.relative_to(ROOT)): sha(p) for p in files}


def horizontal_edges(polygon, z):
    hits = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if min(a[1], b[1]) <= z <= max(a[1], b[1]) and a[1] != b[1]:
            hits.append(a[0] + (b[0] - a[0]) * (z - a[1]) / (b[1] - a[1]))
    require(len(hits) >= 2, "two silhouette intersections required")
    return min(hits), max(hits)


def independent_cut(field, member, saved):
    """Independent raw point-force/couple sum plus Gaussian affine selfweight.

    All cleat grain directions are global +Z. Numerical quadrature integrates
    the recorded member gravity mass and centroid exactly to roundoff, without
    importing or reusing the producer's closed-form cut-wrench function.
    """
    name = member["name"]
    require(member["axis"] == [0.0, 0.0, 1.0], "review's +Z cleat contract")
    cut = np.asarray(saved["cut_point_xyz_mm"])
    station, low, high = cut[2], member["start"][2], member["end"][2]
    force, moment, census = np.zeros(3), np.zeros(3), {}
    for table in (
        "common_shaft_bearing_actions",
        "shaft_end_capture_actions",
        "panel_screw_actions",
        "contact_actions",
        "floor_actions",
        "attachment_actions",
        "retained_bolt_actions",
    ):
        selected = [
            r for r in field[table] if name in (r.get("first"), r.get("second"))
        ]
        census[table] = len(selected)
        for row in selected:
            if row["first"] == name:
                p = np.asarray(row["point_xyz_mm"])
                f = np.asarray(row["force_on_first_xyz_n"])
                m = np.asarray(
                    row.get(
                        "moment_on_first_at_point_xyz_nmm",
                        row.get("moment_at_point_model_xyz_nmm", [0.0, 0.0, 0.0]),
                    )
                )
            else:
                p = np.asarray(
                    row.get("host_support_point_xyz_mm", row["point_xyz_mm"])
                )
                f = np.asarray(
                    row.get(
                        "force_on_second_xyz_n",
                        -np.asarray(row["force_on_first_xyz_n"]),
                    )
                )
                first_moment = np.asarray(
                    row.get(
                        "moment_on_first_at_point_xyz_nmm",
                        row.get("moment_at_point_model_xyz_nmm", [0.0, 0.0, 0.0]),
                    )
                )
                m = np.asarray(
                    row.get("moment_on_second_at_point_xyz_nmm", -first_moment)
                )
            if p[2] < station:
                force += f
                moment += m + np.cross(p - cut, f)
    loads = [r for r in field["body_applied_loads"] if r["body"] == name]
    require(
        len(loads) == 1 and loads[0]["id"] == "self-weight/" + name,
        "cleat requires own affine selfweight only",
    )
    load = loads[0]
    center, weight = np.asarray(load["point_xyz_mm"]), np.asarray(load["force_xyz_n"])
    q, w = np.polynomial.legendre.leggauss(16)
    z = low + (q + 1) * (station - low) / 2
    mid = (low + high) / 2
    beta = 12 * (center[2] - mid) / (high - low) ** 2
    fractions = w * (station - low) / 2 / (high - low) * (1 + beta * (z - mid))
    for zi, fraction in zip(z, fractions, strict=True):
        p = np.array([center[0], center[1], zi])
        f = weight * fraction
        force += f
        moment += np.cross(p - cut, f)
    return (
        float(np.max(abs(-force - saved["force_on_lower_portion_xyz_n"]))),
        float(
            np.max(abs(-moment - saved["moment_on_lower_portion_about_cut_xyz_nmm"]))
        ),
        census,
    )


def main():
    before = snapshot()
    require(
        sha(PACKET / "result.json")
        == "f6ae2d1bbf5528f0027c74bfd2de13fa444b8bc567afaa079d66a295ab04b36b",
        "frozen result differs",
    )
    require(
        sha(PACKET / "verification.json")
        == "9e4b44ee39bc191908b43f36a1d698031a93a2f81b8f4632d86453c90bed8628",
        "frozen verification differs",
    )
    require(
        sha(EARLIER_REVIEW / "review-result.json")
        == "46bc5fa29f34f804bd4c79cc8e7ee793de85230ccefaecf18254b0c2f0e8badd",
        "original review differs",
    )
    inputs, result, details, verification = (
        read(p)
        for p in (
            PACKET / "inputs.json",
            PACKET / "result.json",
            OWN / "replay/details.json",
            PACKET / "verification.json",
        )
    )
    require(
        sha(OWN / "replay/result.json") == sha(PACKET / "result.json"),
        "result replay differs",
    )
    require(
        sha(OWN / "replay/details.json")
        == verification["artifacts"]["details.json"]["sha256"],
        "detail replay differs",
    )
    pins = details["complete_source_sha256"]
    require(len(pins) == 1071, "source census differs")
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "source changed: " + path)
    canonical = hashlib.sha256(
        json.dumps(
            pins, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()
    require(
        canonical
        == result["source_binding"]["canonical_sha256"]
        == verification["source_binding"]["canonical_sha256"],
        "source union differs",
    )
    original = read(ROOT / inputs["original_inputs"]["path"])
    geometry, old, trim = (
        read(ROOT / original[k]["path"])
        for k in ("current_geometry", "old_geometry", "trim_geometry")
    )
    require(
        geometry["revision"] == "eoere-grid-aligned-wire-cutouts-v1"
        and not geometry["mechanics_ready"],
        "wrong local revision",
    )
    require(
        geometry["axes"] == old["axes"] and geometry["screw_axes"] == old["screw_axes"],
        "axis revision mismatch",
    )
    fields, washers, timbers = {}, {}, {}
    for spec in original["cases"]:
        manifest = read(ROOT / spec["manifest"]["path"])
        field = read(ROOT / manifest["field"]["path"])
        require(
            field["source_inputs"]["geometry"]["report"] == original["old_geometry"],
            "force geometry identity differs",
        )
        require(field["case_id"] == spec["case_id"], "field case differs")
        fields[spec["case_id"]] = field
        for kind, destination in (("timber", timbers), ("washers", washers)):
            report = read(ROOT / spec["reports"][kind]["path"])
            require(
                report["source_sha256"].get(manifest["field"]["path"])
                == manifest["field"]["sha256"],
                "report lacks own field pin",
            )
            destination[spec["case_id"]] = report
    max_force, max_moment, max_group, ref_error, census = 0.0, 0.0, 0.0, 0.0, None
    fv = result["material_reference"]["Fv_mpa"]
    for row in details["cleats"]["reduced_depth_shear"]:
        field = fields[row["case_id"]]
        member = next(
            r
            for r in field["source_inputs"]["timber_rows"]
            if r["name"] == row["member"]
        )
        z = row["group_grain_station_mm"]
        raw = [
            r
            for r in field["common_shaft_bearing_actions"]
            if r["second"] == row["member"] and abs(r["point_xyz_mm"][2] - z) < 1e-8
        ]
        raw_group = sum(r["force_on_second_xyz_n"][1] for r in raw)
        require(len(raw) == 4, "two physical bores/four bearing points per cleat group")
        max_group = max(
            max_group, abs(raw_group - row["group_crossgrain_Y_resultant_n"])
        )
        wood = [
            r
            for r in timbers[row["case_id"]]["wood_surfaces"]
            if r["receiver"] == row["member"]
            and abs(r["own_aggregate_point_xyz_mm"][2] - z) < 1e-8
        ]
        ys = [r["own_aggregate_point_xyz_mm"][1] for r in wood]
        rear, front = horizontal_edges(trim["retained_YZ_polygon_mm"], z)
        de = front - min(ys) if raw_group >= 0 else max(ys) - rear
        expected = {
            "untrimmed_rectangular_NDS_reference": (139.7, 95.25),
            "current_local_depth_parameter_sensitivity": (front - rear, de),
            "stock_depth_with_trimmed_engagement_parameter_sensitivity": (139.7, de),
        }
        for key, (d, engaged) in expected.items():
            ref = row[key]
            require(
                ref["equation"] == "3.4-6" and ref["nearest_grain_end_mm"] < 5 * d,
                "near-end branch differs",
            )
            value = 2 / 3 * fv * member["width_mm"] * engaged**3 / d**2
            ref_error = max(ref_error, abs(value - ref["reference_n"]))
            require(
                abs(ref["d_mm"] - d) < 1e-9 and abs(ref["de_mm"] - engaged) < 1e-9,
                "loaded/unloaded edge depth differs",
            )
        for saved in row["adjacent_complete_own_cut_wrenches"]:
            f, m, census = independent_cut(field, member, saved)
            max_force, max_moment = max(max_force, f), max(max_moment, m)
        require(
            row["current_trimmed_cleat_complete_splitting_resistance_n"] is None,
            "component transferred to cleat resistance",
        )
    require(
        max_force < 1e-8
        and max_moment < 1e-6
        and max_group < 1e-10
        and ref_error < 1e-7,
        "independent component accounting differs",
    )
    seats = details["washers"]["seat_geometry"]
    require(
        len(seats) == 112 and len({r["capture_id"] for r in seats}) == 112,
        "wood-seat census differs",
    )
    proofs = Counter(r["proof"] for r in seats)
    queried = [s for s in seats if "solid_source" in s]
    require(
        len(queried) == 44 and len({s["host"] for s in queried}) == 8,
        "current probe census differs",
    )
    require(
        sum(s["host"].startswith("eoere_cleat") for s in seats) == 8,
        "cleat reuse census differs",
    )
    require(
        sum("byte-identical" in s["proof"] for s in seats) == 60,
        "unchanged-seat reuse census differs",
    )
    new_solids = {
        r["id"]: r
        for k in ("changed_finished_solids", "unchanged_finished_solids")
        for r in geometry[k]
    }
    old_solids = {r["id"]: r for r in old["finished_solids"]}
    seat_lookup = {s["capture_id"]: s for s in seats}
    for seat in seats:
        require(seat["full_modeled_support"], "unsupported seat reported full")
        if "solid_source" in seat:
            require(
                seat["solid_source"]["sha256"] == new_solids[seat["host"]]["sha256"],
                "probe solid is not current local geometry",
            )
            require(
                abs(
                    seat["intersected_current_wood_volume_mm3"]
                    - seat["expected_probe_volume_mm3"]
                )
                <= 1e-4,
                "probe tolerance fails",
            )
        elif "byte-identical" in seat["proof"]:
            require(
                new_solids[seat["host"]]["sha256"]
                == old_solids[seat["host"]]["sha256"],
                "reused wood changed",
            )
    max_ring_error, max_peak_error = 0.0, 0.0
    for case, report in washers.items():
        captures = {r["id"]: r for r in fields[case]["shaft_end_capture_actions"]}
        wood_rows = [
            r
            for r in report["all200_own_end_diagnostics"]
            if r["receiver_kind"] == "wood"
        ]
        require(
            {r["capture_id"] for r in wood_rows} == set(seat_lookup),
            "cross-case own seat census differs",
        )
        for original_row in wood_rows:
            seat = seat_lookup[original_row["capture_id"]]
            require(
                original_row["N_n"]
                == captures[original_row["capture_id"]]["compression_n"],
                "own-end axial force substituted",
            )
            for p in [
                original_row["nominal_own_hardware_geometry"],
                *original_row["USS_catalog_corners_min_thickness"],
            ]:
                require(
                    p["OD_mm"] <= seat["bounding_OD_mm"]
                    and max(p["ID_mm"], p["source_support_opening_diameter_mm"])
                    >= seat["bounding_inner_diameter_mm"],
                    "catalog ring leaves proven probe",
                )
    for row in details["washers"]["own_case_component_rows"]:
        area = math.pi / 4 * (row["OD_mm"] ** 2 - row["support_inner_diameter_mm"] ** 2)
        reference = area * result["material_reference"]["Fc_perp_mpa"]
        max_ring_error = max(
            max_ring_error, abs(reference - row["Fc_perp625psi_full_ring_reference_n"])
        )
        a, b = row["support_inner_diameter_mm"] / 2, row["OD_mm"] / 2
        inertia = math.pi / 4 * (b**4 - a**4)
        peak = (
            row["axial_N_n"] / area
            + row["axial_N_n"] * row["two_face_affine_eccentricity_mm"] * b / inertia
        )
        max_peak_error = max(
            max_peak_error,
            abs(
                peak / result["material_reference"]["Fc_perp_mpa"]
                - row["peak_reference_ratio_at_two_face_affine_contact_limit"]
            ),
        )
        require(
            not row["physical_couple_and_washer_combined_resistance_qualified"],
            "contact limit counted as strength",
        )
    require(
        max_ring_error < 1e-8 and max_peak_error < 1e-12,
        "washer component arithmetic differs",
    )
    require(all(v is False for v in result["release"].values()), "release flag enabled")
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "source changed during review: " + path)
    require(before == snapshot(), "frozen packet or original review changed")
    receipt = {
        "schema": "eoere_resistance_followup_independent_review/v1",
        "status": "PASS_BOUNDED_COMPONENT_AND_GEOMETRY_REVIEW_NO_CONFIRMED_BLOCKER",
        "confirmed_blockers": [],
        "scope": "Six fixed old untrimmed raised-rail fields with preserved aligned-wire local geometry; excludes adjusted-base/2026 geometry and any new response or complete joint acceptance.",
        "review_source_sha256": sha(__file__),
        "preserved_original_packet_review_and_followup_sha256_before_after": before,
        "source_binding": {
            "pin_count": len(pins),
            "canonical_sha256": canonical,
            "verified_before_after": True,
        },
        "once_only_original_replay": {
            "result_sha256": sha(OWN / "replay/result.json"),
            "details_sha256": sha(OWN / "replay/details.json"),
            "exact_bytes": True,
        },
        "primary_method_review": {
            "NDS2024_chapter3_local_pinned_sha_verified": True,
            "NDS2024_printed_page21_Figure3E_visually_checked": True,
            "March2026_AWC_errata_local_sha_verified_and_primary_online_browsed": "https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf",
            "MTCv4_printed_page123_existing_source_visually_checked": {
                "url": "https://mtcsolutions.com/wp-content/uploads/2024/02/BHDGvU4.0_Web.pdf",
                "existing_pdf_sha256": "85092c13dffa464f59fdc24b5354404168e136f578dc112b3e4eef3a57acdd20",
                "use": "Application precedent only; no product resistance transferred.",
            },
            "3_4_6_and_exact_5d_3_4_7_formula_and_fastener_center_de_match": True,
            "trimmed_nonrectangular_values_remain_parameter_sensitivities": True,
        },
        "independent_cleat_check": {
            "group_rows": 24,
            "complete_signed_cut_wrenches": 48,
            "max_raw_group_force_error_n": max_group,
            "max_cut_force_error_n": max_force,
            "max_cut_moment_error_nmm": max_moment,
            "max_reduced_depth_reference_error_n": ref_error,
            "external_cleat_table_census": census,
            "separate_Y_normal_opening_not_used_as_shear": True,
        },
        "washer_geometry_and_components": {
            "wood_seats": 112,
            "steel_seats": 88,
            "current_cached_annular_queries": 44,
            "queried_hosts": 8,
            "reused_unchanged_seats": 60,
            "reused_trimmed_cleat_seats": 8,
            "proof_census": dict(proofs),
            "own_case_profile_rows": 3360,
            "max_ring_reference_error_n": max_ring_error,
            "max_affine_peak_ratio_error": max_peak_error,
            "geometric_eligibility_only": True,
        },
        "known_answers_reused_in_original_replay": result["known_answers"],
        "duplicate_library_tests_run": False,
        "actual_release": {
            "new_response": False,
            "geometry_change": False,
            "resistance_acceptance": False,
            "actual_hardware_or_bracing_pass": False,
            "fabrication": False,
            "climbing": False,
        },
        "writes": "Only this ignored review source/result and the once-only replay. No edits to frozen/shared files, native/global execution, frame CAD rebuild, staging, commit, archive or prune.",
    }
    target = OWN / "review-result.json"
    require(not target.exists(), "preserve issued review receipt")
    target.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "path": str(target.relative_to(ROOT)),
                "sha256": sha(target),
                "max_cut_force_error_n": max_force,
                "max_cut_moment_error_nmm": max_moment,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
