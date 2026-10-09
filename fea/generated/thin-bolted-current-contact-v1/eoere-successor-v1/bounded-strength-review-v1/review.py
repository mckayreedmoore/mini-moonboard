"""Independent fixed-input review; no solve, CAD rebuild, or packet edits.

Run after the once-only original analyze.py replay in this directory's replay/
child. Reuses original pure method helpers and checks raw force accounting,
source identities, and signed analytical fixtures without changing frozen data.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = next(
    p
    for p in Path(__file__).resolve().parents
    if (p / "current-candidate.json").is_file()
)
sys.path.insert(0, str(ROOT))
OWN = Path(__file__).resolve().parent
PACKET = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1"
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def check(ok, reason):
    if not ok:
        raise ValueError(reason)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def rejection(action, expected):
    try:
        action()
    except (ValueError, AssertionError) as error:
        check(
            expected in str(error),
            "unexpected negative-fixture rejection: " + str(error),
        )
        return str(error)
    raise ValueError("negative fixture was accepted")


def raw_cleat(field, report, name, cut):
    """Independent regional sum of actual external point forces, not aliases.

    Each physical bore and its end capture lie entirely on one side. Other
    tables are explicitly inventoried; their zero Y component cannot affect
    this force-only bound even at a cut-plane datum. Free couples affect the
    unresolved moment problem, never the integrated normal-force sum.
    """
    wood = [r for r in report["wood_surfaces"] if r["receiver"] == name]
    shafts = {r["axis_id"]: r for r in field["source_inputs"]["shafts"]}
    bearings = [r for r in field["common_shaft_bearing_actions"] if r["second"] == name]
    captures = [r for r in field["shaft_end_capture_actions"] if r["second"] == name]
    check(
        len(wood) == 4 and len(bearings) == 8 and len(captures) == 4,
        "cleat physical census differs",
    )
    check(len({r["axis_id"] for r in bearings}) == 4, "cleat bore axis census differs")
    high, low, alias_error, clearance = 0.0, 0.0, 0.0, math.inf
    for row in wood:
        axis = shafts[row["axis_id"]]
        direction = np.asarray(axis["basis"][0])
        check(abs(direction[1]) < 1e-12, "bolt crosses the Y-normal cut")
        y = row["own_aggregate_point_xyz_mm"][1]
        radius = axis["bore_diameter_mm"] / 2
        check(y + radius < cut or y - radius > cut, "cut crosses complete bore support")
        clearance = min(clearance, abs(y - cut) - radius)
        own = [q for q in bearings + captures if q["axis_id"] == row["axis_id"]]
        check(
            len(own) == 3, "each cleat bore requires two bearings and one own capture"
        )
        check(
            all(
                abs(q.get("host_support_point_xyz_mm", q["point_xyz_mm"])[1] - y)
                < 1e-10
                for q in own
            ),
            "own bore points leave their Y region",
        )
        force = sum(q["force_on_second_xyz_n"][1] for q in own)
        alias_error = max(alias_error, abs(force - row["own_force_xyz_n"][1]))
        check(alias_error < 1e-10, "report misses or reverses an own external force")
        if y > cut:
            high += force
        else:
            low += force
    other_census = {}
    other_force_y = []
    for table in (
        "contact_actions",
        "panel_screw_actions",
        "floor_actions",
        "attachment_actions",
        "retained_bolt_actions",
    ):
        rows = [r for r in field[table] if name in (r.get("first"), r.get("second"))]
        other_census[table] = len(rows)
        for row in rows:
            vector = row["force_on_first_xyz_n"]
            other_force_y.append(vector[1] if row["first"] == name else -vector[1])
    loads = [r for r in field["body_applied_loads"] if r["body"] == name]
    other_census["body_applied_loads"] = len(loads)
    other_force_y.extend(r["force_xyz_n"][1] for r in loads)
    check(
        all(abs(f) < 1e-10 for f in other_force_y), "additional external cleat Y force"
    )
    check(abs(high + low) < 1e-5, "independent whole-cleat Y equilibrium")
    check(
        all(abs(r["force_on_second_xyz_n"][1]) < 1e-12 for r in captures),
        "X clamps silently supply Y force",
    )
    return {
        "member": name,
        "case_id": field["case_id"],
        "high_Y_external_force_n": high,
        "low_Y_external_force_n": low,
        "whole_Y_residual_n": high + low,
        "necessary_tension_n": max(high, 0.0),
        "raw_report_force_max_error_n": alias_error,
        "minimum_bore_edge_to_plane_mm": clearance,
        "other_external_table_census": other_census,
        "direct_crossplane_X_clamp_tie_n": 0.0,
    }


def main():
    names = (
        "README.md",
        "analyze.py",
        "inputs.json",
        "result.json",
        "verification.json",
    )
    before = {str((PACKET / n).relative_to(ROOT)): sha(PACKET / n) for n in names}
    check(
        before[str((PACKET / "result.json").relative_to(ROOT))]
        == "ba5ada3a7d76dc113a0a82705c0e1b3889b16e8b0b98d86669b17438e4624cda",
        "reviewed result identity differs",
    )
    check(
        before[str((PACKET / "verification.json").relative_to(ROOT))]
        == "8abeea98cab6801ec3135f4633783b7b1d63a38f807384756dcf8cbcf7ea5ecc",
        "reviewed verification identity differs",
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
    check(
        sha(OWN / "replay/result.json") == sha(PACKET / "result.json"),
        "replay result bytes differ",
    )
    check(
        sha(OWN / "replay/details.json")
        == verification["artifacts"]["details"]["sha256"],
        "replay detailed bytes differ",
    )
    pins = details["complete_source_sha256"]
    check(len(pins) == 1065, "source union census differs")
    for path, digest in pins.items():
        check(sha(ROOT / path) == digest, "review source changed: " + path)
    canonical = hashlib.sha256(
        json.dumps(
            pins, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()
    check(
        canonical
        == verification["source_union_canonical_sha256"]
        == result["source_binding"]["canonical_sha256"],
        "source union identity differs",
    )
    bounded = load("independent_bounded_review_original", PACKET / "analyze.py")
    from scripts.thin_bolted_steel_resistance import annulus_pressure

    current, old, trim = (
        read(ROOT / inputs[k]["path"])
        for k in ("current_geometry", "old_geometry", "trim_geometry")
    )
    check(
        current["axes"] == old["axes"] and len(current["axes"]) == 100,
        "bolt revision identity or census differs",
    )
    check(
        current["screw_axes"] == old["screw_axes"] and len(current["screw_axes"]) == 66,
        "screw revision identity or census differs",
    )
    fields, report_links, cuts, thicknesses = [], [], [], []
    issued_cuts = {
        (r["case_id"], r["member"]): r
        for r in result["timber_bolts_and_splitting"]["cleat_force_only_opening_bounds"]
    }
    for spec in inputs["cases"]:
        manifest = read(ROOT / spec["manifest"]["path"])
        field = read(ROOT / manifest["field"]["path"])
        reports = {
            kind: read(ROOT / ref["path"]) for kind, ref in spec["reports"].items()
        }
        check(
            field["source_inputs"]["geometry"]["report"] == inputs["old_geometry"],
            "current revision falsely used as force geometry",
        )
        for kind, report in reports.items():
            check(
                report["case_id"] == field["case_id"] == spec["case_id"],
                "cross-case report",
            )
            check(
                report["source_sha256"].get(manifest["field"]["path"])
                == manifest["field"]["sha256"],
                "report lacks its own field source pin",
            )
            report_links.append(
                {"case_id": spec["case_id"], "report_kind": kind, "own_field_pin": True}
            )
        for name in ("eoere_cleat_left", "eoere_cleat_right"):
            row = raw_cleat(field, reports["timber"], name, -105.85)
            check(
                abs(
                    row["necessary_tension_n"]
                    - issued_cuts[spec["case_id"], name][
                        "necessary_integrated_Y_tension_under_fixed_actions_n"
                    ]
                )
                < 1e-10,
                "split lower bound differs",
            )
            cuts.append(row)
        thicknesses.append(
            dict(
                sorted(
                    Counter(
                        r["nominal_own_hardware_geometry"]["t_mm"]
                        for r in reports["washers"]["all200_own_end_diagnostics"]
                    ).items()
                )
            )
        )
        fields.append((spec["case_id"], field, reports))

    negative = {}
    negative["intersected_bore"] = rejection(
        lambda: bounded.opening_force([(-12.0, -8.0, -100.0), (8.0, 12.0, 100.0)], 9.0),
        "cut crosses bore support",
    )
    negative["opening_sign_reversal"] = bounded.opening_force(
        [(-12.0, -8.0, 100.0), (8.0, 12.0, -100.0)], 0.0
    )
    check(
        negative["opening_sign_reversal"][
            "necessary_integrated_Y_tension_under_fixed_actions_n"
        ]
        == 0.0,
        "compression was counted as opening",
    )
    changed = copy.deepcopy(fields[0][1])
    selected = next(
        r for r in changed["contact_actions"] if r["second"] == "eoere_cleat_left"
    )
    selected["force_on_first_xyz_n"][1] = 1.0
    timber = bounded.module("review_timber_original", inputs["helpers"]["timber"])
    negative["added_contact_Y_force"] = rejection(
        lambda: bounded.timber_study(
            [(fields[0][0], changed, fields[0][2])], current, trim, timber
        ),
        "unaccounted cleat Y action",
    )
    changed_report = copy.deepcopy(fields[0][2]["timber"])
    next(
        r
        for r in changed_report["wood_surfaces"]
        if r["receiver"] == "eoere_cleat_left"
    )["own_force_xyz_n"][1] += 1.0
    negative["missing_or_reversed_raw_force"] = rejection(
        lambda: raw_cleat(fields[0][1], changed_report, "eoere_cleat_left", -105.85),
        "report misses or reverses",
    )
    manifest = read(ROOT / inputs["cases"][0]["manifest"]["path"])
    gate = bounded.module("review_original_gate", manifest["gate"]["path"])
    receipt = read(ROOT / manifest["admission"]["path"])
    changed_payload = json.dumps(changed, sort_keys=True).encode()
    try:
        gate.require_admitted_payload(
            changed_payload, receipt, admission_sha256=manifest["gate"]["sha256"]
        )
    except (ValueError, AssertionError) as error:
        negative["tampered_field_rejected_by_original_admission"] = str(error)
    else:
        raise ValueError("tampered field payload admitted")

    # Signed equilibrium fixture: integrate p=N/A+(Mx*y-My*x)/I directly.
    # The full ring is circular, so extrema depend on norm(M), not its sign.
    a, b, n = 5.0, 10.0, 100.0
    area, inertia = math.pi * (b * b - a * a), math.pi / 4 * (b**4 - a**4)
    q, weights = np.polynomial.legendre.leggauss(24)
    radii = a + (q + 1) * (b - a) / 2
    angles = np.arange(256) * 2 * math.pi / 256
    rr, tt = np.meshgrid(radii, angles, indexing="ij")
    xx, yy = rr * np.cos(tt), rr * np.sin(tt)
    da = weights[:, None] * (b - a) / 2 * rr * 2 * math.pi / 256
    signed = []
    for moment in ([120.0, -160.0], [-120.0, 160.0], [312.5, 0.0], [313.0, 0.0]):
        p = n / area + (moment[0] * yy - moment[1] * xx) / inertia
        recovered = [
            float(np.sum(p * da)),
            float(np.sum(p * yy * da)),
            float(-np.sum(p * xx * da)),
        ]
        check(
            np.max(abs(np.asarray(recovered) - np.asarray([n, *moment]))) < 1e-10,
            "signed annulus force or moment equilibrium fails",
        )
        response = annulus_pressure(
            axial_n=n, moment_xy_nmm=moment, inner_radius_mm=a, outer_radius_mm=b
        )
        check(
            abs(
                response["pressure_min_mpa"]
                - (n / area - math.hypot(*moment) * b / inertia)
            )
            < 1e-14,
            "ring pressure sign/extrema differs",
        )
        check(
            response["full_contact_admissible"] == (math.hypot(*moment) <= 312.5),
            "tensile pressure wrongly admitted",
        )
        signed.append(
            {
                "signed_moment_xy_Nmm": moment,
                "integrated_N_Mx_My": recovered,
                "full_contact_admissible": response["full_contact_admissible"],
            }
        )

    members = details["members"]
    check(
        len(members) == 23844
        and len({(r["case_id"], r["member"]) for r in members}) == 132,
        "member census differs",
    )
    failing_domain = sorted(
        {
            r["member"]
            for r in members
            if not r["full_length_K1"]["within_slenderness_limits"]
        }
    )
    check(
        failing_domain
        == [
            "base_header",
            "base_principal_center_left",
            "base_principal_center_right",
            "base_rail_top",
        ],
        "four weak-column domain identities differ",
    )
    check(
        all(
            r["weak_column_50b_scenario"]["within_slenderness_limits"] for r in members
        ),
        "50b scenario does not enter every sampled domain",
    )
    sections = details["sections"]
    check(
        len(sections) == 99 and len({r["member"] for r in sections}) == 8,
        "changed-member section census differs",
    )
    check(
        all(len(r["fixed_old_action_average_bounds"]) == 6 for r in sections),
        "section same-plane case census differs",
    )
    axial = max(
        q["necessary_axial_average_reference"]
        for r in sections
        for q in r["fixed_old_action_average_bounds"]
    )
    shear = max(
        q["necessary_shear_average_reference"]
        for r in sections
        for q in r["fixed_old_action_average_bounds"]
    )
    heel = result["bracket_heel"]
    check(
        heel["actual_3D_heel_capacity"] is None
        and all(
            not r["additive_to_half_band_bending"]
            for r in heel["same_case_whole_flange_references_not_added_to_half_band"]
        ),
        "heel references transfer or add incompatible models",
    )
    check(
        heel["comparison_count"] == 528 and heel["exact_nominal_replay"],
        "heel census or replay differs",
    )
    heel_inputs = read(ROOT / inputs["heel_input"]["path"])
    core = bounded.module(
        "review_heel_core_original", heel_inputs["files"]["kernel"]["path"]
    )
    heel_report = read(ROOT / heel_inputs["cases"][heel["worst"]["case_id"]]["path"])
    angle = next(a for a in heel_report["angles"] if a["body"] == heel["worst"]["body"])
    band = next(b for b in angle["bands"] if b["port_id"] == heel["worst"]["port_id"])
    c = core.heel_component(
        band["root"],
        width=44.45,
        thickness=heel["thickness_at_scalar_reference_boundary_mm"],
        inside_radius=6.35,
        fy=235.0,
        factor=1.67,
        weight_n=angle["own_physical_source_weight_n"],
        bound_radius_mm=angle["gravity_bounding_radius_mm"],
    )
    check(
        abs(c["conditional_combined_yield_reference_ratio"] - 1.0) < 1e-9,
        "heel scalar boundary fails original method",
    )
    for path, digest in pins.items():
        check(sha(ROOT / path) == digest, "source changed during review: " + path)
    after = {str((PACKET / n).relative_to(ROOT)): sha(PACKET / n) for n in names}
    check(before == after, "reviewed packet changed")
    review = {
        "schema": "eoere_bounded_strength_independent_review/v1",
        "status": "PASS_BOUNDED_METHOD_AND_REPORTING_REVIEW_NO_CONFIRMED_BLOCKER",
        "confirmed_blockers": [],
        "review_scope": "Fixed old authenticated actions/current local geometry sensitivity; no current response, resistance acceptance, actual hardware or bracing pass.",
        "frozen_packet_sha256_before_after": before,
        "review_source_sha256": sha(__file__),
        "original_replay": {
            "result_sha256": sha(OWN / "replay/result.json"),
            "details_sha256": sha(OWN / "replay/details.json"),
            "byte_identical": True,
            "runs": 1,
        },
        "source_union": {
            "verified_before_after": True,
            "pins": len(pins),
            "canonical_sha256": canonical,
        },
        "own_report_field_links": report_links,
        "physical_census": {
            "bolts": 100,
            "screws": 66,
            "timbers": 22,
            "angles": 22,
            "current_changed_members": 8,
            "cases": 6,
        },
        "cleat_raw_freebody": cuts,
        "negative_fixtures": negative,
        "signed_annulus_equilibrium_fixtures": signed,
        "nominal_washer_thickness_census_per_case": thicknesses,
        "member_census": {
            "case_members": 132,
            "same_cut_samples": len(members),
            "weak_column_domain_members": failing_domain,
            "50b_scenario_domains_all_entered": True,
            "actual_bracing_qualified": False,
        },
        "net_section_census": {
            "changed_members": 8,
            "planes": len(sections),
            "fixed_old_case_bounds": len(sections) * 6,
            "max_necessary_axial_average_reference": axial,
            "max_necessary_shear_average_reference": shear,
            "bending_torsion_continuous_minimum_or_fracture_disposed": False,
        },
        "heel_scalar_boundary_original_method_ratio": c[
            "conditional_combined_yield_reference_ratio"
        ],
        "checks_already_observed": {
            "command": "uv run pytest -q tests/test_washer_plate_response.py tests/test_reinforced_timber_resistance.py tests/test_thin_bolted_timber_common_shaft_checks.py",
            "passed": 38,
            "failed": 0,
        },
        "original_heel_known_answers": {
            "command": ".venv/bin/python -B fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/joint-mvp-v1/steel-reuse-v1/test_core.py",
            "status": "PASS_CHEAP_ANALYTICAL_KNOWN_ANSWERS",
            "curved_pure_bending_force_moment_recovery": True,
            "same_point_wrench_and_net_centroid_torque_transport": True,
        },
        "frozen_or_shared_paths_written_staged_committed_or_pruned": False,
        "native_global_response_or_actual_geometry_rebuild": False,
        "active_retention": "Review source and compact result plus once-only replay remain in this ignored review path; existing frozen packet and all shared sources remain active; no archive/prune operation.",
    }
    target = OWN / "review-result.json"
    check(not target.exists(), "preserve issued review result")
    target.write_text(
        json.dumps(review, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "status": review["status"],
                "path": str(target.relative_to(ROOT)),
                "sha256": sha(target),
                "cleat_range_n": [
                    min(r["necessary_tension_n"] for r in cuts),
                    max(r["necessary_tension_n"] for r in cuts),
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
