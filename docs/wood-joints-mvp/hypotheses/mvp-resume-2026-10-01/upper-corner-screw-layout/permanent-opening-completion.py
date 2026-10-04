"""Parent-only permanent opening arithmetic from frozen resolver02 wrenches.

Import and prepare(output) use only the standard library. build(output) reuses
three existing pure N08 methods; it never executes a source producer pipeline.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import platform
import sys
from collections import Counter
from functools import cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/permanent-opening-completion"
RESOLVER = HERE / "rawlocal/knee-bridge-permanent-resolve/attempt02"
MEMBERS = HERE.parent / "member-screen-attempt02/knee-bridge-gravity01"
STATES = ("permanent-only_zero", "permanent-only_gap")
SPINES = {"knee_outer_left_spine", "knee_outer_right_spine"}
OUTER_CLEATS = {f"{level}_outer_{side}_cleat" for level in ("top", "bottom") for side in ("left", "right")}
PARTITION_TOL = 1e-6
COMMON_METRICS = ("normal_reference_sum", "total_tension_over_Ft", "total_compression_over_Fc",
                  "absolute_bending_over_Fb", "same_state_shear_bound_over_Fv",
                  "transverse_shear_over_Fv", "torsional_shear_over_Fv")
FACE_METRICS = ("compatible_face_peak_over_Fv", "scalar_shear_bound_over_Fv",
                "sufficient_rectangle_bound_over_Fv")
CATEGORIES = {
    "blind_or_partial_shaft": (1368, "Saved shaft ends do not span the actual finished profile; the whole transverse-slot method is inapplicable."),
    "bore_clipped_end_overlap": (80, "Opening intersects a clipped terminal profile; saved point loads do not establish terminal traction distribution."),
    "other_terminal_profile": (392, "Incomplete or clipped terminal profile has no supported traction field in the existing point-load rectangle method."),
    "unmachined_station_envelope": (88, "Owner-authorized moved-screw station envelope is not a finished hole; no finished-cut resistance is assigned."),
    "outer_cleat_pressure_accounting": (336, "Actual section geometry is available. N08 uses physical half-cosine bore pressure; resolver02 uses global point actions. Matching permanent local pressure accounting is unperformed."),
    "six_bore_spine_accounting": (288, "Actual six-bore geometry is available. N08 uses physical distributed wood/hardware gravity; resolver02 retains mapped nodal loads. Permanent physical accounting and separate internal transverse allocation remain unperformed."),
}
FLAGS = dict.fromkeys((
    "proposal_adopted", "reviewed_104_pass_transferred", "live_utilization_or_pass_transferred",
    "source_acceptance_transferred", "complete_member_acceptance", "complete_joint_acceptance",
    "formal_criterion_acceptance", "full_frame_acceptance", "strict_frame_stability",
    "formal_torsion_qualification", "physical_release", "fabrication_release",
    "native_CAD_or_frame_execution", "tests_run", "review_run", "geometry_changed",
    "hardware_changed", "material_laws_changed", "new_resistance_established",
    "local_pressure_or_gravity_reallocation", "internal_bridge_allocation_solved",
    "local_compatibility_solved", "actual_changed_hole_stiffness_qualified",
), False)
GEOMETRY_SHA = "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af"
PINS = {
    RESOLVER / "comparison.json": "3179d7d40d60a3e21f101610c83acfb588f7e9612941cd253123c9881bbd708a",
    RESOLVER / "geometry.json": "f844524aab764b35d7880f93f280f3ee5484674c6542182c2a7af743b6b65596",
    RESOLVER / "section-coverage.json": "5696f838bec214ea0d54f5fdfeeb3be358bf2b1e5093397bb5b5ef4ad9c43ad2",
    RESOLVER / "member-actions.npz": "e1f3c22a02b7072bf1941ce02be9d3437d7a709dc00cbf802b8327697cb956e8",
    MEMBERS / "geometry.json": GEOMETRY_SHA,
    MEMBERS / "action-section-arrays.npz": "3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596",
    HERE / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    HERE / "remaining-net-sections.py": "acd60cee627331fdfeb06eb02321221f09a666bcea7e3997a9e51e616c98c129",
    HERE / "top-host-net-sections.py": "bfa6a1716908efdb83b3ebf07b0def1bd9114d448dbdf294057b832749d8b3e8",
    HERE.parent / "member_stability.py": "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    HERE.parent / "member_screen.py": "5ecbfcebc8ea45bba83961305735f919d5e6caa3862625befec875655dd0b5d9",
    HERE / "dead-load-check.py": "ffdb2ee797000c055cd67c6e46ac80e549b4865a79346e728074625767bf213d",
}
# Authenticated packet roots bind only the stored recipes actually consumed.
PACKETS = {
    "refresh": ("member-opening-refresh/attempt02", "40beca5a3a5863612a0fadcee4b259f1edacf55f9c58035bc058918c1d64f7e8", "1b31e5582c67c5374bbabcfbbd179957aea976701fbb991f41a0268084d3d694", ("cuts.jsonl.gz",)),
    "remainder": ("member-opening-remainder/attempt02", "b328e9c19bd001bf542e79399f5b15f7b67c595e37d18ff035a9e13d177ae163", "db5a48bc43ab7d953da9fa57df99ddac507dfe0b389f0d1907c5c946a93e6931", ("section-recipes.json",)),
    "side": ("side-host-opening-completion/attempt01", "c6d7074e0a4c5824d41dcbf06849537c2960ba4a7fce6e67b6e19f4185a72a02", "14df990be586554ab89257311c406f49c77190ee94fdaa8f206f426cfcb85320", ("section-recipes.json",)),
    "profile": ("profile-method-completion/attempt02", "d619b34c02402963540b1b34696be0a09ba2fb339790b3aa7335f9e16d5a6d12", "15236a2a44955ba63aba7075c491debee651a48dd083e4affb72cba07fedd36b", ()),
    "earlier": ("knee-bridge-remaining-sections/attempt01", "f519ecc04af7622ec5637162b7a86d6a88e6478e2b15332bf566e6d0e5a3d4c3", "e1796242c3ede025927db911af73b69d226ddd7b7e03aa621f77a548a4f322d0", ("header_cleats-cuts.jsonl.gz", "remaining_12_blocks-cuts.jsonl.gz", "header_paired_bores-cuts.jsonl.gz")),
    "rail": ("knee-bridge-top-rail/attempt02", "9af1574d785466cdb8de36d3f0cd13dd92cd554ca6e374999f59d20adee5a744", "80ed0f8af4dee1e9cf4d006728a33fdb049c97b3bc0d4ccb904610e7b6b679a1", ("point-diagnostic.json",)),
}
EXPECTED_RECIPES = {"refresh": 26, "remainder": 582, "side": 108,
                    "remaining_12_blocks": 192, "header_paired_bores": 6,
                    "rail_point_diagnostic": 12, "header_cleats_subset": 164}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def source_map(pins):
    return {str(p.relative_to(ROOT)): digest for p, digest in sorted(pins.items())}


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, "source changed: " + str(path))


def bind(pins, path, digest):
    require(path not in pins or pins[path] == digest, "conflicting source pin: " + str(path))
    pins[path] = digest


def json_lines(path):
    with gzip.open(path, "rt") as stream:
        for line in stream:
            yield json.loads(line)


def sources():
    """Authenticate and classify saved inputs; no numerical helper is imported."""
    pins = {**PINS, Path(__file__).resolve(): sha(__file__)}
    paths = {}
    for label, (relative, checks_sha, receipt_sha, names) in PACKETS.items():
        directory = HERE / "rawlocal" / relative
        paths[label] = directory
        bind(pins, directory / "checks.json", checks_sha)
        bind(pins, directory / "receipt.json", receipt_sha)
    authenticate(pins)
    for label, (_, _, _, names) in PACKETS.items():
        directory = paths[label]
        checks, receipt = read(directory / "checks.json"), read(directory / "receipt.json")
        require(checks["source_sha256"] == receipt["source_sha256"], "N08 source/receipt differs: " + label)
        require(checks["source_sha256"][str((MEMBERS / "geometry.json").relative_to(ROOT))] == GEOMETRY_SHA,
                "N08 finished-geometry binding differs: " + label)
        require(receipt["output_sha256"]["checks.json"] == pins[directory / "checks.json"], "N08 output binding differs")
        for name in names:
            bind(pins, directory / name, receipt["output_sha256"][name])
    resolver, geometry, original, coverage = [read(p) for p in (
        RESOLVER / "comparison.json", RESOLVER / "geometry.json", MEMBERS / "geometry.json",
        RESOLVER / "section-coverage.json")]
    for name in ("geometry.json", "section-coverage.json", "member-actions.npz"):
        require(resolver["output_sha256"][name] == pins[RESOLVER / name], "resolver output binding differs")
    members = geometry["members"]
    require(len(members) == 44 and set(members) == set(original["members"]), "44-member census differs")
    require({b for b in members if members[b] != original["members"][b]} == SPINES,
            "exact 42-identical/two-changed-spine geometry guard differs")
    spine_sha = {"knee_outer_left_spine": "534ec2db81bbedfddba6cdf92c8703112231e970eff9b10e6a11fd11ce134645",
                 "knee_outer_right_spine": "847e644efdb36156a74dee1641e52a18cf17d301f03f59d2fa0bb68cd7d2b273"}
    for body, member in members.items():
        bind(pins, ROOT / member["current_finished_step"], member["current_finished_step_sha256"])
        if body in SPINES:
            ids = {b["id"] for b in member["bore_or_passage_intervals"]}
            require(member["current_finished_step_sha256"] == spine_sha[body]
                    and ids == {body + "/" + x for x in ("facet006", "facet007", "facet008", "facet009", "proposed_v_bridge_1", "proposed_v_bridge_2")}
                    and len(member["permanent_proposal_geometry"]["bores"]) == 6,
                    "six-bore proposal identity differs: " + body)
    require(resolver["wood_strength_CD"] == .9 and resolver["equipment_multiplier_applied_once"]
            and resolver["additional_dead_load_multiplier"] == 1
            and all(resolver[k] == 0 for k in ("live_gravity_scale", "live_horizontal_scale", "live_moment_scale")),
            "permanent-only load/duration basis differs")
    require(tuple(s["state"] for s in resolver["states"]) == STATES
            and [s["gap_scale"] for s in resolver["states"]] == [0, 1], "two permanent states differ")
    require(resolver["census"]["global_bolts"] == 104 and resolver["census"]["proposal_bolts"] == 108
            and resolver["census"]["internal_static_bolts"] == 4 and not resolver["proposal_adopted"]
            and not resolver["full_frame_acceptance"] and not resolver["physical_release"], "authority boundary differs")
    references = {m["member"]: m["references_cd0_9"] for m in resolver["members"]}
    require(set(references) == set(members), "stored permanent reference census differs")
    for m in resolver["members"]:
        for name in ("Fb_star_mpa", "Ft_mpa", "Fc_star_mpa", "Fv_mpa"):
            require(math.isfinite(m["references_cd0_9"][name]) and m["references_cd0_9"][name] > 0
                    and abs(m["references_cd0_9"][name] - .9 * m["references_cd1"][name]) < 1e-12,
                    "stored CD=.9 reference binding differs")
        for name in ("Fc_perp_mpa", "Emin_mpa"):
            require(m["references_cd0_9"][name] == m["references_cd1"][name], "duration changed non-duration reference")
    authenticate(pins)
    recipes, unsupported = {}, {}

    def add(body, si, section, family, source, metrics, tier="ordinary"):
        require(body not in SPINES and body in members and isinstance(si, int), "recipe body/index differs")
        require(abs(section["station_mm"] - members[body]["stations_mm"][si]) <= PARTITION_TOL,
                "recipe station/index differs")
        require(section["net_area_mm2"] > 0 and section["regions"]
                and section["material_region_count"] == len(section["regions"]), "empty section recipe")
        key = body, si
        entry = {"body": body, "station_index": si, "family": family, "tier": tier,
                 "source": str(source.relative_to(ROOT)), "source_sha256": pins[source],
                 "section": section, "metrics": list(metrics)}
        require(key not in recipes or recipes[key] == entry, "duplicate/conflicting section recipe")
        recipes[key] = entry

    for label in ("remainder", "side"):
        source = paths[label] / "section-recipes.json"
        for recipe in read(source)["recipes"]:
            identity = recipe["opening_identity"]
            body, si = identity["body"], identity["station_index"]
            require(identity["saved_trace_indices"] == [2 * si, 2 * si + 1]
                    and identity["limits"] == ["before", "after"]
                    and identity["station_mm"] == members[body]["stations_mm"][si]
                    and set(identity["feature_ids"]) == set(members[body]["rectangle_at_station"][si]["feature_ids"]),
                    "opening recipe feature/trace identity differs")
            if recipe["status"] == "SUPPORTED_EXACT_TRANSVERSE_SLOT_RECIPE":
                add(body, si, recipe["section"], label, source, COMMON_METRICS + FACE_METRICS)
            else:
                require(recipe["status"] == "INAPPLICABLE_EXISTING_RECTANGULAR_LIGAMENT_RESISTANCE_MODEL",
                        "unknown unsupported recipe status")
                unsupported[body, si] = {"source": str(source.relative_to(ROOT)),
                                         "reason": recipe["reason"], "detail": recipe["detail"]}
    source = paths["refresh"] / "cuts.jsonl.gz"
    for cut in json_lines(source):
        if cut["body"] in ("base_side_left", "base_side_right"):
            require(cut["method"] == "original_signed_point_placement", "refresh side method differs")
            si = cut["saved_trace_index"] // 2
            require(cut["saved_trace_index"] == 2 * si + int(cut["limit"] == "after")
                    and cut["station_mm"] == members[cut["body"]]["stations_mm"][si], "refresh trace differs")
            add(cut["body"], si, cut["section"], "refresh", source, COMMON_METRICS + FACE_METRICS)
    for family in ("header_cleats", "remaining_12_blocks", "header_paired_bores"):
        source = paths["earlier"] / (family + "-cuts.jsonl.gz")
        for cut in json_lines(source):
            summary, section = cut["summary"], cut["section"]
            si = section["saved_station_index"]
            require(summary["saved_trace_index"] == 2 * si + int(summary["limit"] == "after"), "earlier trace differs")
            subset = family == "header_cleats"
            if subset:
                require(section["region_scope"].startswith("Artificial retained rectangles"), "subset hypothesis differs")
            add(summary["block"], si, section, "header_cleats_subset" if subset else family,
                source, COMMON_METRICS, "artificial_retained_subset" if subset else "ordinary")
    source = paths["rail"] / "point-diagnostic.json"
    rail = read(source)
    require(rail["host"] == "base_rail_top"
            and rail["schema"] == "knee-bridge-top-rail-fresh-point-diagnostic/v1", "rail point-method identity differs")
    for section in rail["opening_sections"][rail["host"]]:
        add(rail["host"], section["saved_station_index"], section, "rail_point_diagnostic", source,
            ("normal_reference_sum",) + FACE_METRICS)
    require(dict(Counter(r["family"] for r in recipes.values())) == EXPECTED_RECIPES, "926 ordinary/164 subset recipe census differs")
    selected, residual, identities = [], [], set()
    for cut in coverage:
        body, state, station, limit = (cut[k] for k in ("member", "state", "station_mm", "trace"))
        require(state in STATES and limit in ("before", "after"), "coverage state/limit differs")
        si = members[body]["stations_mm"].index(station)
        identity = state, body, si, limit
        require(identity not in identities, "duplicate saved permanent cut")
        identities.add(identity)
        require(cut["section"] == members[body]["rectangle_at_station"][si]
                and cut["modified_six_bore_spine"] == (body in SPINES)
                and len(cut["signed_cut_grain_u_v_n_nmm"]) == 6
                and all(math.isfinite(v) for v in cut["signed_cut_grain_u_v_n_nmm"]), "saved cut geometry/full wrench differs")
        if cut["normal_shear_torsion_reference_applicable"]:
            require((body, si) not in recipes, "opening recipe unexpectedly joins applicable intact cut")
            continue
        require(cut["opening_resistance_ratio"] is None, "source permanent opening ratio is not null")
        record = {**cut, "station_index": si, "saved_trace_index": 2 * si + int(limit == "after")}
        if (body, si) in recipes:
            selected.append(record)
            continue
        prior = unsupported.get((body, si))
        if body in SPINES:
            category = "six_bore_spine_accounting"
        elif body in OUTER_CLEATS:
            category = "outer_cleat_pressure_accounting"
        elif prior is not None:
            category = {"BLIND_OR_PARTIAL_SHAFT_NOT_A_COMPLETE_TRANSVERSE_SLOT": "blind_or_partial_shaft",
                        "OUTER_PROFILE_OR_TERMINAL_POINT_LOAD_MODEL_INAPPLICABLE": "bore_clipped_end_overlap"}[prior["reason"]]
        elif any(f.endswith("/owner_authorized_station_exclusion") for f in cut["section"].get("feature_ids", [])):
            category = "unmachined_station_envelope"
        else:
            require(cut["section"]["status"] in ("NON_APPLICABLE_END_TRIM_POINT_LOAD_DISTRIBUTION",
                                                "NON_APPLICABLE_INCOMPLETE_OR_TERMINAL_PROFILE"), "uncatalogued residual cut")
            category = "other_terminal_profile"
        residual.append({**record, "category": category, "reason": CATEGORIES[category][1],
                         "recorded_inapplicable_recipe": prior,
                         "actual_section_geometry_recipe_available": category in ("outer_cleat_pressure_accounting", "six_bore_spine_accounting"),
                         "matching_source_action_accounting_available": category not in ("outer_cleat_pressure_accounting", "six_bore_spine_accounting"),
                         "outcome": "UNCALCULATED_SPECIFIC_GEOMETRY_OR_ACCOUNTING_LIMIT"})
    require(len(coverage) == 18488 and len(selected) == 4360 and len(residual) == 2552, "18488/4360/2552 cut partition differs")
    for state in STATES:
        own = [c for c in selected if c["state"] == state]
        require(Counter(recipes[c["member"], c["station_index"]]["tier"] for c in own)
                == {"ordinary": 1852, "artificial_retained_subset": 328}, "per-state selected tier census differs")
        require(Counter(c["category"] for c in residual if c["state"] == state)
                == {k: n // 2 for k, (n, _) in CATEGORIES.items()}, "per-state six-category residual differs")
    require({(c["member"], c["station_index"], c["trace"]) for c in selected if c["state"] == STATES[0]}
            == {(c["member"], c["station_index"], c["trace"]) for c in selected if c["state"] == STATES[1]},
            "zero/nominal selected identities differ")
    authenticate(pins)
    plan = {"schema": "permanent_opening_preparation/v1", "status": "PREPARED_NOT_EXECUTED",
            "producer_sha256": pins[Path(__file__).resolve()], "source_count": len(pins), "source_sha256": source_map(pins),
            "states": list(STATES), "CD": .9, "ordinary_signed_cuts": 3704, "artificial_retained_subset_signed_cuts": 656,
            "remaining_signed_cuts": 2552, "residual_counts": {k: n for k, (n, _) in CATEGORIES.items()},
            "recipe_family_station_counts": EXPECTED_RECIPES, "identical_geometry_records": 42,
            "changed_geometry_records": sorted(SPINES), "partition_tolerance_mm": PARTITION_TOL,
            "source_action_basis": "Saved resolver02 nodal/point actions, all six wrench components; no physical pressure or gravity reallocation.",
            "arithmetic_executed": False, **FLAGS}
    return pins, plan, members, references, recipes, selected, residual


def start(output, pins, plan, recipes, residual):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned output child required")
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "sources-before.json", source_map(pins))
    write(output / "preparation.json", plan)
    write(output / "section-recipes.json", {"recipes": list(recipes.values())})
    write(output / "residual-cuts.json", residual)
    return output


def finish(output, pins, summary):
    authenticate(pins)
    write(output / "sources-after.json", source_map(pins))
    write(output / "summary.json", summary)
    outputs = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    authenticate(pins)
    receipt = {"schema": "permanent_opening_receipt/v1", "status": summary["status"],
               "producer_sha256": pins[Path(__file__).resolve()], "source_count": len(pins),
               "source_sha256": source_map(pins), "output_sha256": outputs,
               "sources_unchanged_before_and_after": True,
               "arithmetic_executed": summary["arithmetic_executed"], **FLAGS}
    write(output / "receipt.json", receipt)
    return {"status": summary["status"], "arithmetic_executed": summary["arithmetic_executed"],
            "ordinary_signed_cuts": summary["ordinary_signed_cuts"],
            "artificial_retained_subset_signed_cuts": summary["artificial_retained_subset_signed_cuts"],
            "remaining_signed_cuts": 2552, "source_count": len(pins), "output_count": len(outputs),
            "summary_sha256": outputs["summary.json"], "receipt_sha256": sha(output / "receipt.json")}


def prepare(output):
    """Optional stdlib-only source census; no mechanics or stress arithmetic."""
    pins, plan, _, _, recipes, _, residual = sources()
    output = start(output, pins, plan, recipes, residual)
    return finish(output, pins, plan)


def helper(name, pins):
    path = HERE / name
    require(sha(path) == pins[path], "helper changed")
    spec = importlib.util.spec_from_file_location("permanent_opening_" + path.stem.replace("-", "_"), path)
    require(spec is not None and spec.loader is not None, "helper import unavailable")
    result = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(result)
    finally:
        sys.dont_write_bytecode = previous
    return result


def comparisons(rows):
    """Summarize only the metrics already assigned to each source recipe family."""
    result = {}
    for metric in sorted({k for row in rows for k in row["comparison_outcomes"]}):
        own = [row for row in rows if metric in row["comparison_outcomes"]]
        result[metric] = {"compared_cut_count": len(own),
                          "exceeded_cut_count": int(sum(row[metric] > 1 for row in own)),
                          "maximum_witness": max(own, key=lambda row: row[metric])}
    return result


def build(output):
    """Parent executes 3,704 ordinary and 656 subset comparisons, without solves."""
    pins, plan, members, stored_refs, recipes, selected, residual = sources()
    output = start(output, pins, plan, recipes, residual)
    try:
        import numpy as np

        require(np.__version__ == "2.5.2", "pinned N08 NumPy runtime differs")
        net, remaining, previous = [helper(name, pins) for name in (
            "corner-net-section.py", "remaining-net-sections.py", "top-host-net-sections.py")]
        require(previous.PARTITION_TOL == PARTITION_TOL, "source partition tolerance differs")
        net.rectangle_torsion = cache(net.rectangle_torsion)
        summaries, audits = [], []
        with (np.load(MEMBERS / "action-section-arrays.npz", allow_pickle=False) as points,
              np.load(RESOLVER / "member-actions.npz", allow_pickle=False) as permanent,
              gzip.open(output / "cuts.jsonl.gz", "wt") as stream):
            for cut in selected:
                body, state, si = cut["member"], cut["state"], cut["station_index"]
                recipe, g = recipes[body, si], members[body]["geometry"]
                section = recipe["section"]
                frame = np.array([g[k] for k in ("axis", "section_u", "section_v")])
                require(np.max(abs(frame @ frame.T - np.eye(3))) < 1e-8 and abs(np.linalg.det(frame) - 1) < 1e-8,
                        "grain basis differs")
                source = np.array(cut["signed_cut_grain_u_v_n_nmm"])
                prefix = state + "__" + body
                index = cut["saved_trace_index"]
                require(np.max(abs(source - permanent[prefix + "__internal_negative_grain_u_v"][index])) == 0,
                        "saved permanent coverage/array wrench differs")
                restored, source_datum = previous.global_cut(
                    permanent[prefix + "__point_force_free_couple_xyz"], points[body + "__point_xyz_mm"],
                    points[body + "__point_stations_mm"], g, cut["station_mm"], cut["trace"] == "before")
                local_restored = np.r_[frame @ restored[:3], frame @ restored[3:]]
                delta = local_restored - source
                require(np.max(abs(delta[:3])) <= 1e-7 and np.max(abs(delta[3:])) <= 1e-5,
                        "full permanent point-action cut restoration differs")
                datum = np.array(section.get("datum_xyz_mm", source_datum))
                local = source.copy()
                local[3:] -= np.cross(frame @ (datum - source_datum), local[:3])
                stored = stored_refs[body]
                refs = {"Fb": stored["Fb_star_mpa"], "Ft_parallel": stored["Ft_mpa"],
                        "Fc_parallel": stored["Fc_star_mpa"], "Fv_parallel": stored["Fv_mpa"]}
                nominal = net.nominal_section(local, section["regions"], refs)
                nominal["references"] = refs
                recovery = np.array(nominal["reconstructed_signed_cut_n_nmm"]) - local
                require(np.max(abs(recovery[:3])) <= 1e-7 and np.max(abs(recovery[3:])) <= 1e-6,
                        "regional complete signed-wrench recovery differs")
                require(abs(nominal["net_section_integrals"]["area_mm2"] - section["net_area_mm2"]) < 1e-7,
                        "stored section area differs")
                summary = remaining.cut_summary(state, body, index, section, nominal)
                summary.update(state=state, station_index=si, station_mm=cut["station_mm"],
                               tier=recipe["tier"], family=recipe["family"], CD=.9)
                faces = []
                if any(m in FACE_METRICS for m in recipe["metrics"]):
                    faces = [previous.region_faces(r, refs, {"cut_datum_global_xyz_mm": datum.tolist()}, frame)
                             for r in nominal["regions"]]
                    deciding = max(faces, key=lambda r: r["face_peak"]["combined_shear_over_Fv"])
                    summary.update(compatible_face_peak_over_Fv=deciding["face_peak"]["combined_shear_over_Fv"],
                                   scalar_shear_bound_over_Fv=max(r["same_state_shear_bound_over_Fv"] for r in nominal["regions"]),
                                   sufficient_rectangle_bound_over_Fv=max(r["sufficient_all_section_bound_over_Fv"] for r in faces),
                                   deciding_region_id=deciding["region_id"], deciding_face=deciding["face_peak"])
                require(all(math.isfinite(summary[m]) and summary[m] >= 0 for m in recipe["metrics"]),
                        "uncalculated/nonfinite assigned metric")
                summary["comparison_outcomes"] = {m: {"value": summary[m], "outcome": (
                    "NOMINAL_REFERENCE_EXCEEDED" if summary[m] > 1 else "NOMINAL_REFERENCE_AT_OR_BELOW_ONE")}
                    for m in recipe["metrics"]}
                summaries.append(summary)
                audit = {"state": state, "member": body, "saved_trace_index": index,
                         "point_action_cut_delta_n_nmm": delta.tolist(), "regional_recovery_delta_n_nmm": recovery.tolist()}
                audits.append(audit)
                record = {"state": state, "member": body, "station_index": si, "station_mm": cut["station_mm"],
                          "trace": cut["trace"], "saved_trace_index": index, "tier": recipe["tier"],
                          "recipe_source": recipe["source"], "recipe_family": recipe["family"],
                          "source_signed_cut_grain_u_v_n_nmm": source.tolist(), "source_cut_datum_xyz_mm": source_datum.tolist(),
                          "section_cut_datum_xyz_mm": datum.tolist(), "signed_cut_at_section_datum_n_nmm": local.tolist(),
                          "references_cd0_9_mpa": refs, "nominal_section": nominal,
                          "regional_faces": faces, "summary": summary, "accounting_audit": audit}
                stream.write(json.dumps(record, separators=(",", ":"), allow_nan=False) + "\n")
        require(len(summaries) == 4360 and Counter(r["tier"] for r in summaries)
                == {"ordinary": 3704, "artificial_retained_subset": 656}, "actual finite arithmetic census differs")
        write(output / "action-audits.json", audits)
        summary = {**plan, "schema": "permanent_opening_completion/v1",
                   "status": "COMPLETE_FINITE_PERMANENT_NOMINAL_REFERENCES_WITH_EXPLICIT_RESIDUAL_LIMITS",
                   "arithmetic_executed": True, "all_assigned_comparisons_finite": True,
                   "runtime": {"python": platform.python_version(), "numpy": np.__version__},
                   "comparisons_by_state_and_tier": [{"state": state, "tier": tier,
                       "signed_cut_count": len(own), "metrics": comparisons(own)}
                       for state in STATES for tier in ("ordinary", "artificial_retained_subset")
                       for own in [[r for r in summaries if r["state"] == state and r["tier"] == tier]]],
                   "body_state_coverage": [{"state": state, "member": body,
                       "ordinary_signed_cuts": sum(r["tier"] == "ordinary" for r in own),
                       "subset_signed_cuts": sum(r["tier"] == "artificial_retained_subset" for r in own)}
                       for state in STATES for body in sorted({r["block"] for r in summaries})
                       for own in [[r for r in summaries if r["state"] == state and r["block"] == body]]],
                   "limits": ["Existing common-strain, area-sharing, common rectangular twist and grain-end continuity hypotheses remain; no physical concentration/splitting/local-capacity bound.",
                              "Artificial retained rectangles omit sound wood and are not complete actual curved sections or a physical stress bound.",
                              "Saved permanent point/nodal demand interpretation only; unchanged no-slip support and filled-bore elasticity. No new pressure, gravity or bridge allocation.",
                              "Remaining 2,552 cuts retain six exact geometry/accounting categories; outer-cleat and spine geometry is available."]}
        return finish(output, pins, summary)
    except Exception as error:
        changed = [str(p.relative_to(ROOT)) for p, digest in pins.items() if not p.exists() or sha(p) != digest]
        write(output / "stop.json", {"status": "STOP_INCOMPLETE_NOT_ACCEPTANCE", "error": str(error),
                                     "changed_sources": changed, "successful_receipt_written": False, **FLAGS})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true", help="Stdlib source census only; no numerical build.")
    args = parser.parse_args()
    try:
        result = prepare(args.output) if args.prepare else build(args.output)
    except Exception as error:  # noqa: BLE001 - Report any parent build failure with exit 2.
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
