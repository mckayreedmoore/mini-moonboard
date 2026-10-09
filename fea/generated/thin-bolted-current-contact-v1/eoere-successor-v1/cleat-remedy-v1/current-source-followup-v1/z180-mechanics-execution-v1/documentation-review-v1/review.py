"""Read saved Z180 JSON and documentation only; execute no producer or selector."""

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
BASE = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/"
PROP = BASE + "cleat-remedy-v1/current-source-followup-v1/"
E = PROP + "z180-mechanics-execution-v1/"
DOC = "docs/wood-joints-mvp/"
SHOP = DOC + "hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/z180-proposal-v1/"
CASES = ("a12-forward", "a12-rear", "a12-left", "k12-right", "k12-rear", "a1-rear")
HEEL = "radius_conditioned_heel_component_with_gravity"
RATIO = "conditional_combined_yield_reference_ratio"
PINS = {
    DOC + "README.md": "c32f79ff38a92f759b3eb40d8493b2c75013fe022dcf2a7cfb19d7ee1c044b40",
    DOC + "completion-ledger.md": "7b39962b443fb96878de0e799bd2abfb02472c3f8c5b1bff5eb89d7b114ddf58",
    SHOP + "README.md": "97c6a9fe4abac45ae5878df6f3a3755e9e21e1498da50663a6d5654a819fd99e",
    E + "cases-v1/result-v1.json": "b37923501498fe35f500105df8b1ee601d7f4d4a553d80a109692565bac3400a",
    E + "cases-v1/independent-output-review-v1/runs-v1/attempt01/receipt.json": "ba6bcdb50cb721ec83709cc393bae9256fd865bd9a235c08f8ebae2f651d52a7",
    E + "component-results-v1/result-roster-v1.json": "b88953ec73f50756a22519b54a6809c5c55c312783133574fc36066c0866ada7",
    E + "inputs-v1/attempt01/inputs.json": "80b5c013b5c69e895c4286d8673f91143f57ac0b0b5243c7370450ec87a2565a",
    E + "inputs-review-v1/runs-v1/attempt01/receipt.json": "3b8b6e2dff8cc8d047cf53b7865137aea11d5085d86359041f6541c78e9dcedf",
    E + "summary-v1/runs-v1/attempt01/summary.json": "d0e36a1d5a253e88e319edfaf5ef8803f96822da215d452dcacb968de44d5a6a",
    E + "summary-v1/runs-v1/attempt01/process.json": "3e20fe1cd3d57593eb076d24f7827e9aceb5b653d3ee72b1141c9342325cb98f",
    E + "summary-v1/runs-v1/attempt02/summary.json": "8241e099fd31a588fb4b504929f8ca487dff7b19dafbaaeea505f7aad9ed9600",
    E + "summary-v1/runs-v1/attempt02/process.json": "0fc7aad991990f56bd16324d90e264babbe17ce87145d60a8c6fe5dfc5c187f4",
    E + "summary-v1/runs-v1/attempt02/parent-verification.json": "8fd7a0d64c9a9a2e86f3d7c62bdca953a78a890bebf17b4459cae0e32824cb51",
    E + "summary-v1/summary-inputs-v2.json": "618622d3257ec2e3a008d5731dddb18a600e66043376da16ac9c2ad00203b02d",
    E + "summary-v1/independent-review-v4/correctness/receipt.json": "d4b782b37ab4142c28a377bba24fd9c8f06fd8bf8c562e6a1747ee1574de1419",
    E + "summary-v1/independent-review-v4/testing/receipt.json": "f47ca0517e8d4c0859522b053f81064c7b9d433dcad1c02e62e2be4c270e9180",
    E + "summary-v1/independent-review-v4/structure/receipt.json": "cbffc5bdb693c052f5e800796baa6eb084e7b6a8824bf5a7975e2ee90226f5d7",
    SHOP + "runs-v1/output01/result.json": "a8cacd9cfaf04d92b98ecb32b74908a43d39c3351e9d90cad4e6194188790208",
    SHOP + "saved-output-review-v1/receipt.json": "7b22bcf9af293220fe776c57176bf576b2692cfd9336367bb06377fced3bd94f",
    BASE + "adjusted-base-mechanics-v1/current-inputs-v1/global-statics-v1/result.json": "f05f81d17a80b1fc1e2a0df106a60ac34f6253a1bb0b664a7241e63cc3702c24",
    PROP + "receiver-seats-v1/fixture-design-v1/catalog-adapter-v1/result-v3.json": "1060bc7a57fb90b6dc8b3dd1aeb18bb863eb3e0fbe7dd2043c524a15c5d48fbf",
    BASE + "adjusted-base-mechanics-v1/current-component-results-v1/summarize.py": "0547b984f150bb9bbd4dbe25b50825a12c047de70bcb1d86a267abd58a935735",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def raw(path, sources, expected=None):
    value = (ROOT / path).read_bytes()
    actual = digest(value)
    require(expected is None or actual == expected, "source changed: " + path)
    require(path not in sources or sources[path] == actual, "source drift: " + path)
    sources[path] = actual
    return value


def load(path, sources, expected=None):
    return json.loads(raw(path, sources, expected))


def ref(value, sources):
    return load(value["path"], sources, value["sha256"])


def unreleased(value):
    require(value["release"] and all(v is False for v in value["release"].values()), "release claim changed")


def section(text, heading, level):
    require(heading in text, "missing documentation section: " + heading)
    return text.split(heading, 1)[1].split("\n" + "#" * level + " ", 1)[0]


def metric(value, pointer, **identity):
    return {"value": value, "pointer": pointer, "identity": identity}


def component_metrics(result):
    coarse, rich = (result["findings"][key] for key in ("coarse", "rich"))
    metrics = {}
    screws = coarse["simultaneous_Hillman_actions_and_generic_references"]
    require(len(screws) == 66, "66 own simultaneous screws required")
    index, row = max(enumerate(screws), key=lambda pair: pair[1]["generic_head_ratio_CD1"])
    metrics["head"] = metric(row["generic_head_ratio_CD1"], f"/findings/coarse/simultaneous_Hillman_actions_and_generic_references/{index}", axis_id=row["axis_id"])
    panels = coarse["six_panel_reductions"]
    require(panels["sample_count_per_axis"] == 41 and len(panels["panel_diagnostics"]) == 6, "six panels and original grid required")
    sections = [(i, p["panel"], key, v) for i, p in enumerate(panels["panel_diagnostics"])
                for key, v in p["resolved_section_diagnostics"]["components"].items()]
    for name in ("bending", "rolling"):
        index, panel, key, row = max((s for s in sections if s[2].startswith(name)), key=lambda s: s[3]["sampled_ratio_CD1"])
        metrics[name] = metric(row["sampled_ratio_CD1"], f"/findings/coarse/six_panel_reductions/panel_diagnostics/{index}/resolved_section_diagnostics/components/{key}", panel=panel, component=key)
    members = coarse["fresh_gross_member_diagnostics"]
    require(len(members) == 22 and len(coarse["angle_duties"]) == 22 and len(coarse["exterior_cleat_corners"]) == 2, "22 members/angles and two corners required")
    require(all(r["complete_group_heel_hole_prying_or_corner_resistance"] is None for r in coarse["angle_duties"])
            and all(r["complete_corner_splitting_group_or_bearing_resistance"] is None for r in coarse["exterior_cleat_corners"]), "complete joints must remain null")
    for name, witness, key in (("gross_normal", "fully_braced_normal", "fully_braced_component_normal_interaction"),
                               ("gross_shear", "sufficient_shear_torsion", "equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio")):
        index, row = max(enumerate(members), key=lambda pair: pair[1]["witnesses"][witness]["gross_CD1_comparison"][key])
        metrics[name] = metric(row["witnesses"][witness]["gross_CD1_comparison"][key], f"/findings/coarse/fresh_gross_member_diagnostics/{index}/witnesses/{witness}", member=row["member"])
    require([s["comparison"]["id"] for s in rich["rich_steel"]] == ["t6_r6", "t6p35_r6p35"], "distinct steel scenarios required")
    for i, scenario in enumerate(rich["rich_steel"]):
        saved = scenario["summary"][HEEL]
        require(saved["comparison_count"] == 88, "88 heel rows per own case required")
        row = saved["worst"]
        name = scenario["comparison"]["id"]
        metrics[name] = metric(row["comparison"][RATIO], f"/findings/rich/rich_steel/{i}/summary/{HEEL}/worst", body=row["body"], port_id=row["port_id"])
        metrics[name]["exceedance_count"] = saved["exceedance_count"]
    timber = rich["timber"]
    compatible = [(i, s) for i, s in enumerate(timber["shaft_components"]) if s["component"] is not None]
    require(len(compatible) == 92 and len(timber["shaft_components"]) == 100, "92 compatible/eight mixed shafts required")
    require(len(timber["duties"]) == 24 and all(s["complete_joint_resistance_n"] is None for s in timber["duties"]), "24 null timber duties required")
    index, row = max(compatible, key=lambda pair: pair[1]["component"]["V_over_unadjusted_component_Z"])
    metrics["timber"] = metric(row["component"]["V_over_unadjusted_component_Z"], f"/findings/rich/timber/shaft_components/{index}", axis_id=row["axis_id"])
    metrics["timber"]["sensitivity_exceedance_count"] = sum(s["component"]["Cdelta0p5_Cg1_CD1_sensitivity_ratio"] > 1 for _, s in compatible)
    shafts = rich["shaft"]["all100"]
    require(len(shafts) == 100 and rich["shaft"]["complete_bolt_resistance"] is None, "100 reference shafts and null complete resistance required")
    index, row = max(enumerate(shafts), key=lambda pair: pair[1]["governing"]["specified_material_first_yield_index"])
    metrics["shaft"] = metric(row["governing"]["specified_material_first_yield_index"], f"/findings/rich/shaft/all100/{index}", axis_id=row["axis_id"])
    washer = rich["washers"]
    require(washer["census"]["physical_end_captures"] == 200, "200 own end diagnostics required")
    row = washer["worsts"]["all_catalog_axial_Fy_required"]
    require(row["scenario"]["actual_product_Fy_mpa"] is None and row["scenario"]["combined_washer_strength_index"] is None, "actual washer strength stays unknown")
    metrics["washer"] = metric(row["value"], "/findings/rich/washers/worsts/all_catalog_axial_Fy_required", axis_id=row["axis_id"], host=row["host"], capture_id=row["capture_id"])
    seats = result["nominal_seat_geometry"]
    require(seats["nominal_wood_seats"] == 112 and len(seats["new_own_nominal_seats"]) == 16
            and len(set(seats["unaffected_capture_ids"])) == seats["unaffected_proof_count"] == 96
            and seats["old_actions_or_strength_transferred"] is False, "distinct own16/unchanged96 nominal seats required")
    return metrics


def summary_metrics(row):
    coarse, rich = row["coarse"], row["rich"]
    panels = [v for p in coarse["panels"]["per_panel"] for key, v in p["section_components"].items()]
    values = {"head": coarse["generic_screw_references"]["generic_head_ratio_CD1"]["generic_head_ratio_CD1"],
              "timber": rich["timber"]["summary"]["worst_component"]["V_over_unadjusted_component_Z"],
              "shaft": rich["shaft"]["worst"]["governing"]["specified_material_first_yield_index"],
              "washer": rich["washers"]["worsts"]["all_catalog_axial_Fy_required"]["value"]}
    require(panels, "summary panel witnesses missing")
    for name in ("bending", "rolling"):
        values[name] = max(v["sampled_ratio_CD1"] for p in coarse["panels"]["per_panel"]
                           for key, v in p["section_components"].items() if key.startswith(name))
    for name, key in (("gross_normal", "fully_braced_component_normal_interaction"),
                      ("gross_shear", "equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio")):
        values[name] = coarse["gross_raw_members"][key]["worst"]["value"]
    for scenario in rich["steel_scenarios"]:
        values[scenario["comparison"]["id"]] = scenario["summary"][HEEL]["worst"][RATIO]
    return values


def review(allow_pending_summary=False):
    sources = {}
    frozen = {p: load(p, sources, sha) for p, sha in PINS.items() if p.endswith(".json")}
    for path, sha in PINS.items():
        if not path.endswith(".json"):
            raw(path, sources, sha)  # Read the frozen selector source; never compile or call it.
    cases = frozen[E + "cases-v1/result-v1.json"]
    roster = frozen[E + "component-results-v1/result-roster-v1.json"]
    failed_summary = frozen[E + "summary-v1/runs-v1/attempt01/summary.json"]
    require(failed_summary["status"] == "FAILED" and failed_summary["exception"]["message"] == "exact component source snapshot required", "original failed summary must remain distinct")
    unreleased(failed_summary)
    require(tuple(r["case_id"] for r in cases["cases"]) == tuple(r["case_id"] for r in roster["cases"]) == CASES, "six exact own case order required")
    require(cases["no_retries_or_alternative_masks"] and cases["original_recorded_applied_loads_retained"], "original force run claims differ")
    require(cases["total_field_bytes"] == 154326660 and cases["total_operator_bytes"] == 57202333
            and sum(r["files"]["result.json"]["bytes"] for r in roster["cases"]) == 37596835, "active ignored bank byte totals differ")
    require(roster["source_union_count"] == 1253 and not roster["source_union_drift"]
            and [r["source_pin_count"] for r in roster["cases"]] == [1228] * 6
            and [r["outer_before_uncovered_count"] for r in roster["cases"]] == [42, 0, 0, 0, 0, 0], "source inventory/caveat differs")
    require(cases["complete_joint_resistance"] is None and roster["complete_joint_resistance"] is None, "resistance must remain null")
    unreleased(cases)
    unreleased(roster)
    selected, gradients, legs = [], [], []
    for field_entry, entry in zip(cases["cases"], roster["cases"], strict=True):
        refs = field_entry["references"]
        field = ref(refs["field.json"], sources)
        admission = ref(refs["admission.json"], sources)
        result = ref(entry["files"]["result.json"], sources)
        config = ref(entry["files"]["config.json"], sources)
        for value in (field, admission, result, config):
            unreleased(value)
            require(value["case_id"] == entry["case_id"] and value["state_id"] == entry["state_id"], "own case/state identity differs")
        require(admission["input_raw_sha256"] == refs["field.json"]["sha256"]
                and result["field"] == entry["field"] == config["field"]
                and result["admission"] == entry["admission"] == config["admission"]
                and entry["field"] == {key: refs["field.json"][key] for key in ("path", "sha256")}
                and entry["admission"] == {key: refs["admission.json"][key] for key in ("path", "sha256")}, "own raw pair/component binding differs")
        require(admission["unadopted_z180_equilibrium_and_recovery_pass"] is True
                and result["complete_joint_resistance"] is None and result["unadopted_proposal"] is True, "own conditional result required")
        support = admission["support_contract"]
        require(support["enabled_centroid_xy_hosts"] == ["lumber_leg_left", "lumber_leg_right"]
                and support["all_other_floor_hosts_normal_only"] and support["no_slip_assumed_not_verified"]
                and not support["physical_floor_capacity_established"], "fixed analytical floor contract differs")
        gradients.append(admission["declared_law_checks"]["gradient_inf_n"])
        legs.extend(admission["normal_force_n_by_host"][host] for host in ("lumber_leg_left", "lumber_leg_right"))
        selected.append({"case_id": entry["case_id"], "state_id": entry["state_id"], "result": entry["files"]["result.json"], "metrics": component_metrics(result)})
    require(max(gradients) == cases["maxima"]["admitted_gradient_inf_n"] and min(legs) == cases["minimum_credited_leg_normal_n"], "roster gradient/leg summaries differ")
    inputs = frozen[E + "inputs-v1/attempt01/inputs.json"]
    parent = ref(inputs["applied_source_wrench_reuse"]["source"], sources)
    require(inputs["floor_footprints"] == parent["floor_footprints"], "statics footprint reuse differs")
    previous = {r["case_id"]: r for r in parent["cases"]}
    for row in inputs["cases"]:
        require(all(row[key] == previous[row["case_id"]][key] for key in ("applied_force_xyz_n", "applied_moment_about_global_origin_xyz_nmm", "primary_load_basis", "hold", "accessory_placement")), "original applied source loads differ")
    require(len(inputs["cases"]) == 7 and sum(map(len, inputs["floor_footprints"].values())) == 32, "seven source cases/32 floor points required")
    statics = frozen[BASE + "adjusted-base-mechanics-v1/current-inputs-v1/global-statics-v1/result.json"]
    require(statics["summary"]["minimum_edge_margin_mm"] == 330.28499147990897, "statics margin differs")
    shop = frozen[SHOP + "runs-v1/output01/result.json"]
    require(len(shop["files"]) == 10 and sum(r["bytes"] for r in shop["files"].values()) == 348024, "shop file/byte census differs")
    blank = 0
    for name, info in shop["files"].items():
        data = raw(SHOP + "runs-v1/output01/" + name, sources, info["sha256"])
        require(len(data) == info["bytes"], "shop byte size differs")
        if name.endswith(".csv"):
            rows = list(csv.DictReader(io.StringIO(data.decode())))
            cols = [key for key in rows[0] if key.startswith("Actual") or key == "Disposition"]
            require(all(not row[key] for row in rows for key in cols), "actual shop observation supplied")
            blank += len(rows) * len(cols)
    require(blank == 3296, "candidate blank observation census differs")
    roles = load(SHOP + "runs-v1/output01/hardware-role-locations.json", sources)["roles"]
    require(len(roles) == 20 and all(not row[key] for row in roles for key in ("Actual", "Disposition")), "forty blank role observations required")
    require(all("nominal4in" in row["basis"] and "no spacer" in row["basis"] for row in roles), "original four-inch/no-spacer roles required")
    for item in shop["inherited_files_via_links"].values():
        raw(item["path"], sources, item["sha256"])
    fixture = frozen[PROP + "receiver-seats-v1/fixture-design-v1/catalog-adapter-v1/result-v3.json"]
    require(fixture["derived_relative_bound_under_declared_unobserved_conditions_mm"] == 1.522541290125167
            and fixture["retained_error_conditions"]["relative_bore_screw_target_mm"] == 1.5, "retained fixture exceedance differs")
    require(frozen[E + "inputs-review-v1/runs-v1/attempt01/receipt.json"]["mass_reconciliation_kg"]["total"] == 219.11593970030577, "nominal mass differs")
    maxima = {name: max(({"case_id": row["case_id"], "result": row["result"], **row["metrics"][name]} for row in selected), key=lambda row: row["value"]) for name in selected[0]["metrics"]}
    docs = {DOC + "README.md": "## Proposed Z180 evaluation", DOC + "completion-ledger.md": "### Lowered cleat-bolt proposal: conditional numerical completion", SHOP + "README.md": None}
    links, pending, summary_paths, self_links = [], [], set(), []
    for path, heading in docs.items():
        text = raw(path, sources).decode()
        selected_text = section(text, heading, heading.count("#")) if heading else text
        if path == DOC + "README.md":
            require(all(f"{maxima[name]['value']:.6f}" in selected_text for name in maxima), "README component maximum differs")
            require(f"{min(legs):.6f}" in selected_text and "330.28499148" in selected_text, "README leg/statics value differs")
        if path == DOC + "completion-ledger.md":
            require(all(f"{maxima[name]['value']:.6f}" in selected_text for name in ("head", "bending", "rolling")), "ledger panel/screw maximum differs")
            require(all(token in selected_text for token in ("112 = sixteen own new + 96 unchanged", "1.522541", "1.50", "219.115940", "$109.93", "excluding pads", "348,024", "3,296", "forty")), "ledger retained scope/quantity differs")
        if path == SHOP + "README.md":
            require(all(token in selected_text for token in ("original four-inch", "no\nspacer", "348,024", "219.115940", "excluding pads", "$109.93", "unpriced", "unverified")), "shop retained scope/quantity differs")
        for target in re.findall(r"\]\(([^)]+)\)", selected_text):
            if target.startswith(("https:", "http:", "mailto:")):
                continue
            leaf, _, anchor = target.partition("#")
            destination = (ROOT / path).parent / leaf if leaf else ROOT / path
            is_summary = "summary-v1/runs-v1/" in target and target.endswith("/summary.json")
            if is_summary:
                summary_paths.add(str(destination.resolve().relative_to(ROOT)))
            if not destination.exists() and is_summary and allow_pending_summary:
                pending.append(target)
                continue
            if destination.resolve() == OWN.parent / "receipt.json":
                self_links.append({"document": path, "target": target, "created_after_successful_checks": True})
                continue
            require(destination.exists(), "documentation link missing: " + target)
            if anchor and destination.suffix == ".md":
                headings = re.findall(r"^#+\s+(.+)$", destination.read_text(), re.MULTILINE)
                anchors = [re.sub(r"[^\w -]", "", value.strip().lower()).replace(" ", "-") for value in headings]
                require(anchor in anchors, "documentation anchor missing: " + target)
            links.append({"document": path, "target": target})
    require(len(summary_paths) == 1, "one linked final summary path required")
    summary_path = next(iter(summary_paths))
    if (ROOT / summary_path).exists():
        summary = load(summary_path, sources)
        if summary.get("status") == "FAILED" and allow_pending_summary:
            pending.append(summary_path + " [preserved failed attempt; not summary evidence]")
        else:
            require(summary.get("schema") == "eoere_exact_unadopted_z180_six_case_summary/v1", "successful own summary schema required")
            require(summary_path == E + "summary-v1/runs-v1/attempt02/summary.json", "linked summary must be the final frozen successful attempt")
            unreleased(summary)
            require(tuple(r["case_id"] for r in summary["cases"]) == CASES and summary["complete_joint_resistance"] is None, "summary scope differs")
            for saved, row in zip(selected, summary["cases"], strict=True):
                require(saved["state_id"] == row["state_id"] and saved["result"]["sha256"] == row["component_bindings"]["result"]["sha256"], "summary own result identity differs")
                require(summary_metrics(row) == {key: value["value"] for key, value in saved["metrics"].items()}, "summary selected witness metrics differ")
            require(summary["unadopted_proposal"] is True and summary["spacer_or_4p5in_adopted"] is False, "summary proposal/hardware scope differs")
            process = frozen[E + "summary-v1/runs-v1/attempt02/process.json"]
            validation = frozen[E + "summary-v1/runs-v1/attempt02/parent-verification.json"]
            for value in (process, validation):
                unreleased(value)
                require(value["status"] == "PASS" and value["complete_joint_resistance"] is None, "successful conditional reporting evidence required")
            require(process["exit_code"] == 0 and process["case_count"] == 6 and process["elapsed_seconds"] == 5.1472283719995175
                    and process["pre_source_count"] == process["post_source_count"] == len(summary["source_sha256"]) == 1314
                    and process["source_union_canonical_sha256_before"] == process["source_union_canonical_sha256_after"] == summary["verified_source_union"]["canonical_sha256"], "final process/source-union report differs")
            require(process["output"]["sha256"] == PINS[summary_path] and process["manifest"]["sha256"] == PINS[E + "summary-v1/summary-inputs-v2.json"]
                    and validation["summary"] == process["output"] and validation["manifest"] == process["manifest"], "final process/parent/manifest identity differs")
            raw(process["writer"]["path"], sources, process["writer"]["sha256"])
            for log in ("stdout", "stderr"):
                raw(process[log]["path"], sources, process[log]["sha256"])
            for entry, row in zip(roster["cases"], summary["cases"], strict=True):
                snapshots = [ref(entry["files"][key], sources) for key in ("source-pins-before.json", "source-pins-after.json")]
                require(all(s["schema"] == "eoere_z180_component_process_source_snapshot/v1" for s in snapshots), "actual snapshot schema changed")
                caveats = row["outer_snapshot_caveats"]
                require(caveats["inventory_only_historical_receipts"] == snapshots[0].get("inventory_only_historical_receipts", [])
                        and caveats["result_pins_missing_before_snapshot"] == snapshots[1]["result_pins_missing_before_snapshot"], "summary original snapshot caveats differ")
            for kind, key in (("correctness", "findings"), ("testing", "confirmed_substantial_findings"), ("structure", "findings")):
                require(frozen[E + f"summary-v1/independent-review-v4/{kind}/receipt.json"][key] == [], "final narrow review finding differs")
    else:
        require(allow_pending_summary, "final summary is pending")
    require(sum(r["metrics"]["t6_r6"]["exceedance_count"] for r in selected) == 7
            and sum(r["metrics"]["t6p35_r6p35"]["exceedance_count"] for r in selected) == 0, "heel exceedance totals differ")
    require(sum(r["metrics"]["timber"]["sensitivity_exceedance_count"] for r in selected) == 10
            and sum(bool(r["metrics"]["timber"]["sensitivity_exceedance_count"]) for r in selected) == 5, "timber sensitivity totals differ")
    publication, active_ignored = [], []
    for owner in (PROP + "z180-mechanics-inputs-v1", E.rstrip("/"), SHOP.rstrip("/")):
        for path in sorted((ROOT / owner).rglob("*")):
            if not path.is_file() or path.is_symlink() or any(part in {"__pycache__", ".pytest_cache", ".ruff_cache"} for part in path.parts) or path.is_relative_to(OWN.parent):
                continue
            relative, size = str(path.relative_to(ROOT)), path.stat().st_size
            snapshot = "component-results-v1" in path.parts and path.name in {"source-pins-before.json", "source-pins-after.json"}
            compact_summary = "summary-v1" in path.parts and path.name == "summary.json"
            if (size > 1000000 and not compact_summary) or snapshot or "_probes" in path.parts:
                active_ignored.append({"path": relative, "bytes": size})
            else:
                publication.append({"path": relative, "bytes": size, "sha256": digest(raw(relative, sources))})
    require(len(publication) == 252 and sum(r["bytes"] for r in publication) == 5850512, "stable compact publication inventory differs")
    require(len(active_ignored) == 67 and sum(r["bytes"] for r in active_ignored) == 284811250, "active regular raw/fixture inventory differs")
    for path, sha in sources.items():
        require(digest((ROOT / path).read_bytes()) == sha, "source changed during review: " + path)
    return {"schema": "eoere_z180_documentation_saved_claim_review/v1", "status": "PASS_BOUNDED_SAVED_DOCUMENTATION_AND_DATA_CLAIMS" if not pending else "WORKING_DOCS_CHECKS_PASS_FINAL_SUMMARY_PENDING",
            "findings": [], "helper": {"path": str(OWN.relative_to(ROOT)), "sha256": digest(OWN.read_bytes())}, "source_sha256": dict(sorted(sources.items())),
            "reproduce_read_only": [".venv/bin/python", "-B", str(OWN.relative_to(ROOT))], "helper_validation": "Ruff check passes; working saved-data execution passes before final frozen execution.",
            "release": cases["release"], "complete_joint_resistance": None, "unadopted_proposal": True, "all_bound_sources_unchanged_before_after": True,
            "per_case_saved_metrics": selected, "global_selected_saved_witnesses": maxima, "verified_local_links": links, "pending_links": pending, "self_receipt_links": self_links,
            "retention_inventory": {"publication_count": len(publication), "publication_bytes": sum(r["bytes"] for r in publication),
                                    "publication_inventory_canonical_sha256": digest(json.dumps(publication, sort_keys=True, separators=(",", ":")).encode()),
                                    "publication_file_hashes_are_in_source_sha256": True,
                                    "active_regular_raw_fixture_count": len(active_ignored), "active_regular_raw_fixture_bytes": sum(r["bytes"] for r in active_ignored),
                                    "raw_paths_and_sizes_checked": active_ignored, "exclusions": ["Two maintained documents", "Entire documentation-review-v1", "Caches and symlinks"]},
            "manual_claim_review": {"working_text_numbers_match_saved_witnesses": True, "unadopted_Z180_and_main_Z200_four_HOLD_authority_distinct": True,
                                    "unknowns_exceedances_panel_remedy_stop_and_all_false_releases_preserved": True, "original4in_no_spacer_actual_blank_pads_exclusion_partial_dated_price_and_tool_exceedance_preserved": True,
                                    "old_source_arithmetic_and_nominal_geometry_reuse_distinct_from_old_forces": True, "no_new_capacity_physical_test_or_external_signoff_gate_added": True},
            "execution": {"saved_JSON_CSV_SVG_source_and_documentation_bytes_only": True, "producer_gate_reducer_selector_summary_CAD_BREP_K_q_native_global_or_browser_executed": False},
            "limits": ["Documentation/data-claim review only; genuine field admissions and component reducers supply the original numerical arithmetic.", "Saved metric selection retains one complete own-case witness; no cross-case force combination or new component calculation.", "Raw/fixture inventory checks regular paths and sizes; full source/operator arithmetic and the 1,314-path before/after production check rely on their saved process/admission audits.", "CI diagnostic-set comparison and Pages status remain the separate parent-recorded read-only audit of the linked GitHub runs; this review does not fetch those logs or rerun CI.", "Prior saved-output audits retain their recorded limits; no inference of actual hardware, tool, floor, capacity, fabrication or climbing acceptance."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--allow-pending-summary", action="store_true")
    args = parser.parse_args()
    require(not args.receipt or not args.allow_pending_summary, "final receipt requires final summary")
    result = review(args.allow_pending_summary)
    if args.receipt:
        require(args.receipt.resolve().parent == OWN.parent, "review owns only its receipt directory")
        with args.receipt.open("x") as stream:
            json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps({"status": result["status"], "findings": result["findings"], "sources": len(result["source_sha256"]), "cases": len(result["per_case_saved_metrics"]), "local_links": len(result["verified_local_links"]), "pending_links": result["pending_links"]}, sort_keys=True))


if __name__ == "__main__":
    main()
