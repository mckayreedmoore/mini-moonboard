"""Source-only map for current component consumers; no field consumer is exposed.

Read saved JSON and exact source bytes only. Historical receipts supply the
explicitly selected geometry proofs; their old loads and execution dependency
maps are not current runtime inputs. Equations remain in the frozen reducers.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[6]
BASE = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1"
MECH = BASE + "/adjusted-base-mechanics-v1"
DOC = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
ARCHIVE_MANIFEST = {
    "path": "/home/mckay-linux/repos/mini-moonboard-cleanup-backups-2026-10-08/eoere-aligned-wire-cutouts-v1.tar.gz.manifest.json",
    "sha256": "688acf55c2884086ff14352d6d5ac6377b8f6bcebeb29c0e8275e4ffcdf3a15c",
}


def ref(path, sha256):
    return {"path": path, "sha256": sha256}


ARTIFACTS = {
    "geometry": ref(DOC + "/occupied-extended-cleats-v1.json", "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d"),
    "parent_geometry": ref(DOC + "/occupied-adjusted-base-v3.json", "5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7"),
    "manifest": ref(MECH + "/parent-authority-v1/extended-cleat-manifest.json", "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6"),
    "parent_manifest": ref(MECH + "/parent-authority-v1/adjusted-base-manifest.json", "27220ec69ebe96e0c637d02d74aea1a7732f68d111b9918c973fa8ee954b48c2"),
    "descriptors": ref(MECH + "/current-source-observations-v1/attempt01.json", "0f7e95f0dabfb5f0b5d63f8ef7d78e3c52c07672b4f482a89a89496eec703de7"),
    "descriptor_review": ref(MECH + "/current-source-observations-v1/independent-review-v1/correctness/receipt.json", "14db73198c6705d866e42f43f41184e2235cfe66450418f6ba892aabbd98ee34"),
    "preserved_metadata": ref(BASE + "/raised-rail-mechanics-v1/inputs.json", "81e9ad126f806a412a8bcb73ae3d0057ef3568ed0fa45986503f97fb5fb62d9f"),
    "seat_audit": ref(DOC + "/bounded-strength-v1/revised-base-audit-v1/result.json", "1205472ce4f96626318b42f2ad7578396485d167932f22fc0af387b156c4f875"),
    "seat_details": ref(BASE + "/bounded-strength-v1/revised-base-audit-v1/attempt06/details.json", "837474fad3300ade9c3dc1e15c68827c7faeb2c76b0a17fae83c32d4511abf71"),
    "extension_review": ref(BASE + "/cleat-top-extension-review-v1/actual-output-review.json", "c5d97796a59a8fa085abeacdc4a7672c81f9aa57ea9db0bd7872f9e7e5e1f109"),
    "gate": ref(MECH + "/current-force-bridge-v1/review-fix-v2/bridge.py", "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643"),
}

# File SHA and existing callable names; these files are parsed, never imported.
METHODS = {
    "fixed-floor-components-v1/assessment.py": ("3283b7a1c048e26894193d0e31d939d772af44b36bac90922bcd821d46d0e315", ("consume",)),
    "raised-rail-components-v1/assessment.py": ("c435067dd3504dd566c65e097ab8d5e36ce3ecc31b1e7e9cf275b66cd6b6242d", ("component_context", "prepared_datums", "consume")),
    "component-method-v1/assessment.py": ("f5ae45cb3b630a57895b2119958c24f1cc559d9cbf34d5b2373b5a1975c300b0", ("reduce_field", "panel_reductions")),
    "component-method-v1/gross_members.py": ("01aaf22c8b2cf93430e7bbce4768260efea39bed3d527b8f5486ba4e38e32258", ("member_witnesses",)),
    "raised-rail-components-v1/comparisons.py": ("fe70dbd0bb41c3d1328a2a2406b0b566240522d09384960bf8e68ab06b17d580", ("fitting_strip_comparisons",)),
    "steel-shaft-comparison-v1/comparison.py": ("9d670f264d5b074abf4cbd48baaebde486b1c15e3ddb612302bd1f41a577a360", ("shaft_circle_comparisons",)),
    "joint-mvp-v1/washer-reuse-v1/admitted_intake.py": ("b57fce9e682be9cf7740ba6857f768e387ac198f75a328682ddca15a14cd5eb0", ("load_admitted",)),
    "joint-mvp-v1/washer-reuse-v1/calculate.py": ("96bb2ede4b65202bd9c74631cb39568aad3055294d931e1d352b9d3a8b4741e5", ("calculate", "scenario_metrics")),
    "joint-mvp-v1/timber-reuse-v1/calculate_v2.py": ("41385d35d8faf785ae14f88f8bb54ed69dbed56e271ff7524f1dc6b071f6310d", ("produce", "raw_ray", "placement")),
    "joint-mvp-v1/steel-reuse-v1/calculate.py": ("6acf9421d8fcbcafd1334edfa3a5a9e3bbb80ccea8594d9094d47cba4c4d7b18", ("own_loads", "reduce_angle")),
    "joint-mvp-v1/steel-reuse-v1/core.py": ("477ca831860a163e4baefcab3a93fd82002528f4735fe66ec98aec0d382797f1", ("band_comparison", "heel_component", "bore_reference", "whole_flange_reference")),
    "joint-mvp-v1/first_joint.py": ("9a3decbff84ba24ab5ecb9d34489a3427d83144a0813e9dcf6a5b500904a279e", ("bolt_components",)),
    "joint-mvp-v1/current_joint_disposition.py": ("8c6afe877d8a98a10acbcba373cf3d808a1000c96e4e3fc003cf3f1c673198c9", ("produce",)),
    "joint-mvp-v1/finished_sections.py": ("7721ecccf31cbb2b8c798ec056ae148ce09d64d1c47c1557495cc0a0292628f9", ("section_method", "run")),
    "joint-mvp-v1/coherent_case_coverage.py": ("bf2263ee020fbde16f76cc98e2c2a29f17341ae91e8df8f40d11f119cb327832", ("analysis_contract", "same_contract", "produce")),
    "joint-mvp-v1/joint_reference_envelope.py": ("defd616bf106e6b8e26f222b5ba29ca598d98ff21133b8da51e6a39fd3b5c068", ("produce",)),
}
CHANGED = {
    "base_header", "base_post_center_right", "base_principal_center_right",
    "base_rail_bottom_left", "base_rail_bottom_right", "base_rail_service_lower_left",
    "base_rail_service_lower_right", "base_rail_service_upper_left", "base_rail_service_upper_right",
    "base_rail_top", "eoere_cleat_left", "eoere_cleat_right", "kicker_right",
    "main_lower_right", "main_upper_right",
}
CLEATS = {"eoere_cleat_left", "eoere_cleat_right"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def checked_bytes(source):
    path = ROOT / source["path"]
    require(path.resolve().is_relative_to(ROOT) or source == ARCHIVE_MANIFEST, "repository source or exact declared recovery manifest required")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == source["sha256"], "exact source bytes required: " + source["path"])
    return raw


def merge(pins, extra):
    for path, sha in extra.items():
        require(path not in pins or pins[path] == sha, "source closure conflict: " + path)
        pins[path] = sha


def indexed(rows, key):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), "unique metadata rows required: " + key)
    return result


def source_ref(row):
    return ref(row["path"], row["sha256"])


def verify_current_metadata(data, geometry, parent, review, preserved):
    """Pure metadata checks, not a second admission or a BRep query."""
    require(data["schema"] == "eoere_extended_cleat_cached_source_export/v1", "current descriptor schema required")
    require(data["geometry"] == ARTIFACTS["geometry"] and data["manifest"] == ARTIFACTS["manifest"]
            and data["parent_base_geometry"] == ARTIFACTS["parent_geometry"]
            and data["parent_base_manifest"] == ARTIFACTS["parent_manifest"], "exact current geometry/manifest refs required")
    require(not any(data["release"].values()) and data["fresh_contact_domains_not_copied_from_old_field"] is True,
            "current unreleased fresh descriptors required")
    require(geometry["parent_geometry"]["base"] == ARTIFACTS["parent_geometry"]
            and geometry["axes"] == parent["axes"] and geometry["screw_axes"] == parent["screw_axes"]
            and geometry["only_two_cleat_bodies_changed"] is True, "exact OFF two-cleat extension required")
    axes = indexed(geometry["axes"], "id")
    shafts = indexed(data["shafts"], "axis_id")
    prior_shafts = indexed(preserved["shafts"], "axis_id")
    require(len(axes) == len(shafts) == 100 and set(axes) == set(shafts) == set(prior_shafts), "current 100 shafts required")
    for key, shaft in shafts.items():
        require(shaft["source_axis"] == axes[key] and shaft["point"] == axes[key]["point_xyz_mm"], "current own shaft source required")
        require(shaft["ends"] == prior_shafts[key]["ends"], "unchanged geometric end offsets/hosts required")
        direction = axes[key]["direction_xyz"]
        length = math.sqrt(sum(v*v for v in direction))
        require(max(abs(a-b/length) for a, b in zip(shaft["basis"][0], direction, strict=True)) < 1e-12,
                "current normalized shaft direction required")
    require([r["source_screw_descriptor"] for r in data["hillman_rows"]] == geometry["screw_axes"]
            and len(indexed(data["hillman_rows"], "id")) == 66, "all 66 current ordered screw descriptors required")
    observations = indexed(data["finished_body_observations"], "id")
    previous = indexed(preserved["finished_body_observations"], "id")
    timber = indexed(data["raw_gross_timber_rows"], "name")
    require(len(observations) == 28 and set(observations) == set(previous) and len(timber) == 22
            and len(set(observations)-set(timber)) == 6, "current 22 timber / six panel sources required")
    changed = {key for key in observations if source_ref(observations[key]["source"]) != source_ref(previous[key]["source"])}
    require(changed == CHANGED, "exact 15 changed finished sources required")
    require(review["status"] == "PASS_NO_SUBSTANTIAL_FINDINGS"
            and review["sources"][ARTIFACTS["descriptors"]["path"]] == ARTIFACTS["descriptors"]["sha256"]
            and set(review["current_vs_preserved"]["changed_finished_source_ids"]) == CHANGED
            and review["review_performed_only_saved_metadata_reads_and_source_hashes"] is True,
            "own saved-data correctness review required")
    require({r["id"] for r in geometry["changed_finished_solids"]} == CLEATS, "only two current cleat replacements required")
    for row in [*parent["changed_finished_solids"], *geometry["changed_finished_solids"]]:
        if row["id"] in observations:
            require(source_ref(observations[row["id"]]["source"]) == source_ref(row), "finished source composition differs")
    for key in CLEATS:
        raw = timber[key]["raw_profile_source"]
        require(raw["current_geometry_source"] == ARTIFACTS["geometry"]
                and raw["basis_grain_u_v_xyz"][0] == [0.0, 0.0, 1.0]
                and raw["finished_YZ_polygon_mm"] == geometry["new_cleat_YZ_polygon_mm"]
                and raw["raw_stock_scenario_dimensions_mm"] == [38.1, 139.7, geometry["maximum_blank_length_mm"]]
                and timber[key]["finished_cut_stiffness_or_resistance_qualified"] is False,
                "separate current gross cleat blank and finished profile required")
    expected = {"physical_owner_gravity_rows": 150, "fitting_poses": 22, "fitting_ports": 88,
                "finished_receiver_wall_queries": 120, "floor_observations": 8,
                "flange_domains": 88, "direct_contacts": 1606}
    require(all(len(data[key]) == n for key, n in expected.items()), "complete current owner/wall/port/contact census required")
    require(sum(len(r["holes"]) for r in data["all_factory_holes"]) == 176
            and sum(len(r["ends"]) for r in shafts.values()) == 200
            and len(data["current_panel_machining_descriptors"]["features"]) == 340, "current hole/end/machining census required")
    contacts = Counter()
    for patch in data["flange_shared_face_patches"]:
        contacts[patch["first"]] += len(patch["cells"])
    require(contacts == Counter({row["id"]: 16 for row in data["fitting_poses"]}), "all 22 current fittings need their own 16 backing cells")
    return {"census": {**expected, "shafts": 100, "ends": 200, "wood_seats": 112, "panel_screws": 66,
                       "raw_timbers": 22, "panels": 6, "factory_holes": 176, "panel_features": 340,
                       "flange_backing_cells": sum(contacts.values())},
            "finished_sources": [{"id": key, "current": source_ref(observations[key]["source"]),
                                  "changed_since_preserved": key in changed} for key in sorted(observations)]}


def nominal_seat_carry(data, geometry, audit, details, extension):
    """Select only recorded nominal geometry; never old actions or strength."""
    require(audit["current_base"] == ARTIFACTS["parent_geometry"]
            and audit["washer_support"]["total_wood_seats"] == 112
            and audit["washer_support"]["fresh_changed_host_probes"] == 36
            and audit["washer_support"]["unchanged_seat_proofs_reused"] == 76
            and audit["washer_support"]["failed_seat_ids"] == [], "exact v3 nominal seat audit required")
    require(extension["status"] == "PASS_NOMINAL_SAVED_GEOMETRY_ONLY"
            and extension["sole_two_cleat_replacements"] is True
            and extension["both_parent_variant_bindings_verified"] is True
            and extension["analysis_pass_transferred"] is False, "current extension subset proof required")
    bodies = indexed(extension["body_checks"], "id")
    require(set(bodies) == CLEATS and all(row["valid_single_solid"] is True and row["lost_old_volume_mm3"] == 0.0
                                        for row in bodies.values()), "full old cleat volume must be retained")
    for row in geometry["changed_finished_solids"]:
        require(extension["source_sha256"].get(row["path"]) == row["sha256"], "current cleat body must join extension proof")
        prior_path = BASE + "/cleat-rear-trim-v1/cad-v2/" + row["id"] + ".brep"
        require(details["complete_source_sha256"].get(prior_path) == geometry["source_sha256"][prior_path]
                == extension["source_sha256"].get(prior_path), "same prior cleat body must join both proofs")
    wood = {row["name"] for row in data["raw_gross_timber_rows"]}
    sources = {r["id"]: r["source"] for r in data["finished_body_observations"]}
    seats = {}
    for shaft in data["shafts"]:
        for end in shaft["ends"]:
            if end["host"] in wood:
                seats[shaft["axis_id"] + "/" + end["end"] + "-capture"] = (shaft, end)
    rows = indexed(details["washer_seat_rows"], "capture_id")
    require(len(seats) == len(rows) == 112 and set(seats) == set(rows), "exact current 112 wood seat IDs required")
    fresh = 0
    for key, row in rows.items():
        shaft, end = seats[key]
        require(row["axis_id"] == shaft["axis_id"] and row["host"] == end["host"]
                and row["full_modeled_support"] is True, "own nominal supported seat identity required")
        hardware = shaft["source_axis"]["hardware_scenario"]
        require(row["bounding_OD_mm"] >= hardware["washer_od_mm"]
                and row["bounding_inner_diameter_mm"] <= hardware["washer_id_mm"], "audited annulus must bound current nominal washer")
        if "solid_source" in row:
            require(source_ref(row["solid_source"]) == source_ref(sources[end["host"]]), "audited seat host source required")
        if "current_host_support_point_xyz_mm" in row:
            fresh += 1
            point = [p+a*end["support_s_mm"] for p, a in zip(shaft["point"], shaft["basis"][0], strict=True)]
            require(math.dist(point, row["current_host_support_point_xyz_mm"]) < 1e-7
                    and row["old_force_used_as_new_response"] is False, "fresh v3 seat source/point join required")
        elif end["host"] not in CLEATS and "solid_source" not in row:
            source = sources[end["host"]]
            require(details["complete_source_sha256"].get(source["path"]) == source["sha256"], "unchanged seat host source required")
    cleat_rows = {row["axis_id"] for row in rows.values() if row["host"] in CLEATS}
    lands = indexed(extension["bore_and_land_checks"], "axis_id")
    require(fresh == 36 and len(cleat_rows) == 8 and set(lands) == cleat_rows
            and all(len(row["annular_skin_fraction_at_both_X_faces"]) == 2 for row in lands.values()),
            "36 fresh / 76 reused seats and eight cleat bore/land identities required")
    return {"nominal_wood_seats": 112, "fresh_v3_probes": 36, "unchanged_v3_proofs": 76,
            "current_cleat_seats_carried_by_full_parent_volume": 8,
            "basis": [ARTIFACTS["seat_audit"], ARTIFACTS["seat_details"], ARTIFACTS["extension_review"]],
            "scope": "nominal geometry only; current pressure, stiffness, contact and complete resistance unresolved",
            "old_actions_or_strength_transferred": False}


def reuse_map():
    """Bounded followup interfaces; no callable adapters or numerical work."""
    return {
        "coarse": {"reuse": "assessment.reduce_field + gross_members.member_witnesses; existing samples 41/51",
            "needs": "one own-admitted current field; scoped current FIELD_SCHEMA/ADMISSION_SCHEMA/SUCCESS and gate; current axis/source_contract map, centroidal steel callback and current panel prepared_datums callback",
            "wrapper_limit": "fixed-floor and raised-rail consume wrappers bind historical gates/geometry/features; reuse their context pattern only after explicit current source rebinding",
            "limit": "same-state references and gross rectangular-stock witnesses; finished net sections/bracing and complete joint resistance remain null"},
        "rich_steel": {"reuse": "calculate.own_loads/reduce_angle + core band/heel/bore/flange equations and existing scenario",
            "needs": "own current 22 operator descriptors; each 8 fine bearing + 4 capture + 16 backing actions, own gravity, pose and free couples; exact current manifest via admitted_intake",
            "tolerances_unchanged": {"port_aggregate_error": 1e-7, "force_equilibrium_n": 1e-4, "moment_equilibrium_nmm": 0.1},
            "limit": "conditional 6-mm/r6-mm Fy235/Fu370 references; actual thickness, bend radius, material and complete angle/group behavior unqualified"},
        "shaft": {"reuse": "comparison.shaft_circle_comparisons and first_joint.bolt_components",
            "needs": "own same-state 100 current shaft cut tables/axes and exact catalog/material reference sources",
            "limit": "smooth-circle/body/root scenarios only; delivered body/runout/thread window and complete joint resistance unresolved"},
        "panel_screws": {"reuse": "assessment.panel_reductions + existing screw_references",
            "needs": "own current six panel coefficient slices/chart, 340 machining descriptors and 66 simultaneous screw actions; current panel-bank source dependencies",
            "limit": "generic references only; actual Hillman product resistance and finished edge/head/punching/support behavior unresolved; remedies held"},
        "timber": {"reuse": "calculate_v2 equations, raw_ray/placement and own-bearing/capture replay",
            "needs": "own 120 current wood bearing rows, current full walls/grain and gross raw profiles, own capture actions, exact material/yield-method refs and a current manifest",
            "tolerances_unchanged": {"force_replay_n": 1e-8, "moment_replay_nmm": 1e-6},
            "limit": "individual compatible two-member references only; mixed/multiple shear planes, finished ligaments, Cg/Cdelta, splitting and group resistance remain null"},
        "washer": {"reuse": "calculate.scenario_metrics and same-state capture diagnostics; nominal support evidence selected separately",
            "needs": "own 200 signed current capture actions, own nominal hardware, current grain and support geometry; explicitly composed v3 service_cuts and current fitting scenario for full calculate API",
            "limit": "current extension report alone lacks service_cuts/scenario; do not invent scene alias; nominal annulus support does not establish contact pressure or stiffness"},
        "finished_sections": {"reuse": "existing bounded section method only if a later claim needs it",
            "needs": "current finished source ID, section plane/axes, own same-case cuts and a justified ligament/end/edge/restraint/failure model for affected members",
            "limit": "old finished_sections.run is fixed to old A12/geometry and imports CAD; no call or old result transfer; keep current capacities null without additional CAD"},
        "disposition": {"reuse": "existing four-report identity joins, coherent_case_coverage and joint_reference_envelope selection arithmetic",
            "needs": "fresh current steel/timber/washer/shaft reports with one exact raw field/state/case/accessory identity, all 24 duties and 12 retained starting axes; six own-admitted primary cases, separate gravity diagnostic",
            "limit": "rebind old geometry/schema wrappers before use; preserve exceedances/null resistance and same-case witnesses; no cross-case force combination"},
    }


def component_plan():
    """Verify current saved inputs/method sources and return a deferred plan."""
    pins = {str(OWN.relative_to(ROOT)): LOADED_SHA}
    values = {}
    for key, source in ARTIFACTS.items():
        raw = checked_bytes(source)
        merge(pins, {source["path"]: source["sha256"]})
        if key != "gate":
            values[key] = json.loads(raw)
        else:
            names = {n.name for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef)}
            require("require_admitted_payload" in names, "current gate API required")
    data = values["descriptors"]
    merge(pins, data["source_sha256"])
    metadata = verify_current_metadata(data, values["geometry"], values["parent_geometry"],
                                       values["descriptor_review"], values["preserved_metadata"])
    seats = nominal_seat_carry(data, values["geometry"], values["seat_audit"], values["seat_details"], values["extension_review"])
    historical = {}
    for key, field in (("seat_details", "complete_source_sha256"), ("extension_review", "source_sha256")):
        overlap = {path: sha for path, sha in values[key][field].items() if path in pins and not path.startswith("site/")}
        require(all(pins[path] == sha for path, sha in overlap.items()), "historical computational overlap conflicts")
        historical[key] = {"current_computational_overlap_pins": len(overlap), "old_dependency_map_used_as_current_runtime": False}
    methods = []
    for relative, (sha, functions) in METHODS.items():
        source = ref(BASE + "/" + relative, sha)
        raw = checked_bytes(source)
        names = {n.name for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef)}
        require(set(functions) <= names, "existing frozen method API required: " + relative)
        merge(pins, {source["path"]: sha})
        methods.append({**source, "existing_functions": list(functions), "imported_or_executed": False})
    for path, sha in pins.items():
        checked_bytes(ref(path, sha))
    return {"schema": "eoere_extended_cleat_component_source_plan/v1", "status": "SOURCE_PLAN_ONLY_CONSUMER_DEFERRED",
            "current_geometry": ARTIFACTS["geometry"], "current_manifest": ARTIFACTS["manifest"],
            "current_saved_descriptors": ARTIFACTS["descriptors"], "current_descriptor_review": ARTIFACTS["descriptor_review"],
            "future_admission": {"gate": ARTIFACTS["gate"], "api": "require_admitted_payload(field_bytes, receipt, *, admission_sha256=gate SOURCE SHA)",
                "field_schema": "eoere_extended_cleat_fixed_floor_candidate/v1",
                "receipt_schema": "eoere_extended_cleat_fixed_floor_independent_field_admission/v1",
                "success_key": "current_extended_cleat_equilibrium_and_recovery_pass",
                "manifest_api": "admitted_intake.load_admitted(manifest_path) -> (field, pins)",
                "geometry_mapping": ["report", "source_manifest", "cached_source_export"], "scene_alias_allowed": False},
            **metadata, "nominal_seat_geometry": seats, "reuse": reuse_map(), "methods": methods,
            "historical_evidence": historical, "source_sha256": dict(sorted(pins.items())),
            "execution": {"saved_JSON_and_source_byte_reads_only": True, "method_imports_or_execution": False,
                          "CAD_import_or_query": False, "K_q_forces_or_native_solve": False,
                          "field_or_force_consumer": False, "viewer_or_browser": False},
            "complete_joint_resistance": None, "release": {"physical": False, "fabrication": False, "structural": False, "climbing": False}}
