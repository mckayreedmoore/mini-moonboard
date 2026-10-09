"""Bounded source/ownership/retention review of the frozen extended-cleat shop packet.

Uses saved JSON/CSV/SVG and the stdlib exporter only. No CAD, browser or mechanics.
Writes only this review's receipt; fresh reproduction is temporary and owned here.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1"
VERIFICATION_SHA = "38aaa554039e3dd5c5bbcf7545c3dc6b6339b7dd9dc93af6ac9cecc327e9f721"
RESULT_SHA = "0f00a7ba22a08975adac6bf660db370866510c40b5d56e5829bfab9b2ad3f92e"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def record(path):
    raw = path.read_bytes()
    return {"sha256": digest(raw), "bytes": len(raw)}


def rows(name):
    reader = csv.DictReader(io.StringIO((DOC / name).read_text()))
    require(len(reader.fieldnames) == len(set(reader.fieldnames)), f"duplicate CSV headers: {name}")
    data = list(reader)
    require(all(None not in row and None not in row.values() for row in data), f"ragged CSV: {name}")
    return data


def run_export(*args):
    command = [sys.executable, "-B", str(DOC / "export.py"), *map(str, args)]
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)


def main():
    require(OWN.parts[-2:] == ("independent-review-v1", "structure"), "exclusive output boundary differs")
    verification = json.loads((DOC / "verification.json").read_bytes())
    result = json.loads((DOC / "result.json").read_bytes())
    require(record(DOC / "verification.json")["sha256"] == VERIFICATION_SHA, "frozen verification differs")
    require(record(DOC / "result.json")["sha256"] == RESULT_SHA, "frozen result differs")
    packet = {p.name: record(p) for p in DOC.iterdir() if p.is_file()}
    require(len(packet) == 26 and sum(r["bytes"] for r in packet.values()) == 615144, "packet census/volume differs")
    require({k: v for k, v in packet.items() if k != "verification.json"} == verification["owned_artifacts"], "26-file frozen artifact map differs")
    require(sum(r["bytes"] for r in verification["owned_artifacts"].values()) == verification["owned_artifact_bytes"], "permanent-volume accounting differs")
    context = {p: record(ROOT / p) for p in ["AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md"]}
    original = verification["preserved_original_14_shop_artifact_sha256"]
    require(len(original) == 14 and all(record(ROOT / p)["sha256"] == sha for p, sha in original.items()), "original shop bytes differ")

    inputs = json.loads((DOC / "inputs.json").read_bytes())
    source_data = {}
    pins = {}
    for key, ref in inputs["sources"].items():
        raw = (ROOT / ref["path"]).read_bytes()
        require(record(ROOT / ref["path"]) == {"sha256": ref["sha256"], "bytes": ref["bytes"]}, f"direct source differs: {key}")
        pins[ref["path"]] = ref["sha256"]
        if ref["path"].endswith(".json"):
            source_data[key] = json.loads(raw)
    for key in ["aligned", "base", "extension"]:
        for path, sha in source_data[key]["source_sha256"].items():
            require(path not in pins or pins[path] == sha, "inherited source conflict")
            pins[path] = sha
    for ref in source_data["old_result"]["sources"].values():
        require(ref["path"] not in pins or pins[ref["path"]] == ref["sha256"], "old datum source conflict")
        pins[ref["path"]] = ref["sha256"]
    profiles = json.loads((DOC / "current_profiles.json").read_bytes())
    for profile in profiles.values():
        ref = profile["finished"]
        require(ref["path"] not in pins or pins[ref["path"]] == ref["sha256"], "current profile source conflict")
        pins[ref["path"]] = ref["sha256"]
    require(len(pins) == 864 == result["source_pin_count"], "source closure census differs")
    require(canonical(pins) == result["source_map_canonical_sha256"], "source closure binding differs")
    require(all(record(ROOT / path)["sha256"] == sha for path, sha in pins.items()), "inherited source differs")
    require(source_data["extension"]["axes"] == source_data["base"]["axes"], "base/extension axes differ")
    require(source_data["extension"]["screw_axes"] == source_data["base"]["screw_axes"], "base/extension screws differ")
    require(inputs["optional_extra_grid"] is False and verification["optional_extra_grid"] is False, "optional-grid boundary differs")

    tables = {name: rows(name) for name in ["members.csv", "member-end-datums.csv", "receiver-holes.csv", "panel-screw-datums.csv", "panel-machining.csv", "bolt-stacks.csv", "access-sides.csv"]}
    expected_rows = {"members.csv": 28, "member-end-datums.csv": 260, "receiver-holes.csv": 120, "panel-screw-datums.csv": 66, "panel-machining.csv": 340, "bolt-stacks.csv": 100, "access-sides.csv": 200}
    require({name: len(data) for name, data in tables.items()} == expected_rows, "table census differs")
    observation_cells = 0
    for name, data in tables.items():
        for row in data:
            observed = [v for k, v in row.items() if k.startswith("Actual") or k == "Disposition"]
            require(all(v == "" for v in observed), f"filled observation cell: {name}")
            observation_cells += len(observed)
    access = tables["access-sides.csv"]
    require(all(r["current_tool_access_disposition"] == r["current_axial_removal_disposition"] == "UNVERIFIED" for r in access), "access acceptance transferred")
    require(all(r["prior_140_side_access_pass_transferred"] == "False" for r in access), "historical access acceptance transferred")
    require(len({(r["axis_id"], r["side"]) for r in access}) == 200 and Counter(r["side"] for r in access) == {"head": 100, "nut": 100}, "head/nut ownership differs")
    stacks = tables["bolt-stacks.csv"]
    require(len({r["axis_id"] for r in stacks}) == 100, "duplicate physical stack")
    require(Counter(r["catalog_box_disposition"] for r in stacks) == {"NONNEGATIVE_COMPARISON": 76, "SHORT_STACK_COMPARISON": 24}, "catalog flag census differs")
    require(all(r["part_receiving_disposition"] == "UNVERIFIED" for r in stacks), "delivered hardware acceptance transferred")
    require(Counter(r["kind"] for r in tables["panel-machining.csv"]) == {"tnut": 142, "light": 132, "conditional_screw_clearance": 66}, "base grid feature census differs")
    require(len(profiles) == 28 and Counter(p["kind"] for p in profiles.values()) == {"timber": 22, "panel": 6}, "profile ownership differs")

    stock = json.loads((DOC / "stock-nesting.json").read_bytes())
    placed = [member for stick in stock["sticks"] for member in stick["members"]]
    require(len(stock["sticks"]) == 13 and len(placed) == len(set(placed)) == 22, "stock coverage differs")
    require(set(placed) == {name for name, p in profiles.items() if p["kind"] == "timber"}, "stock/member ownership join differs")
    for stick in stock["sticks"]:
        lengths = [profiles[name]["blank_mm"][0] for name in stick["members"]]
        require(lengths == stick["blank_lengths_mm"], "stock/profile lengths differ")
        consumed = sum(lengths) + len(lengths) * stock["kerf_mm_per_output_piece"] + 2 * stock["end_trim_allowance_mm_each"]
        require(math.isclose(consumed, stick["consumed_with_kerf_and_trim_mm"], abs_tol=1e-8), "stock allowance arithmetic differs")
        require(math.isclose(stick["length_ft"] * 304.8 - consumed, stick["remaining_mm"], abs_tol=1e-8), "stock remainder differs")
    require(math.isclose(min(s["remaining_mm"] for s in stock["sticks"]), 46.05, abs_tol=1e-8), "minimum spare differs")
    mass = sum(p["finished"]["volume_mm3"] for p in profiles.values()) * 500e-9 + result["nominal_mass"]["preserved_nominal_nonwood_and_25kg_allowance_kg"]
    require(math.isclose(mass, result["nominal_mass"]["conditional_total_kg"], abs_tol=1e-9), "saved-volume mass arithmetic differs")
    require(result["nominal_mass"]["actual_total_kg"] is None and not any(result["release"].values()), "physical/release claim differs")

    svgs = sorted(DOC.glob("*.svg"))
    require(len(svgs) == 9, "SVG census differs")
    svg_text_counts = {}
    for path in svgs:
        root = ET.fromstring(path.read_bytes())
        require(root.tag == "{http://www.w3.org/2000/svg}svg", "invalid SVG root")
        require(not any(e.tag.rsplit("}", 1)[-1] in {"script", "image", "foreignObject"} for e in root.iter()), "unexpected copied/executable SVG asset")
        require(not any(k.rsplit("}", 1)[-1] == "href" and not v.startswith("#") for e in root.iter() for k, v in e.attrib.items()), "external SVG dependency")
        svg_text_counts[path.name] = sum(e.tag == "{http://www.w3.org/2000/svg}text" for e in root.iter())
    links = re.findall(r"\]\(([^)]+)\)", (DOC / "README.md").read_text())
    local = [urlsplit(link) for link in links if not urlsplit(link).scheme]
    require(len(local) == 25 and all((DOC / unquote(link.path)).is_file() for link in local), "local leaf navigation differs")

    producer_records = {}
    for kind, checker in [("controls", "check_packet.py"), ("drawings", "check-drawings.cjs")]:
        ref = verification[kind]
        raw = (ROOT / ref["path"]).read_bytes()
        require(digest(raw) == ref["sha256"], f"producer evidence changed: {kind}")
        data = json.loads(raw)
        require(data["passed"] and data["checker_sha256"] == packet[checker]["sha256"], f"producer evidence/checker mismatch: {kind}")
        require(data["geometry_or_mechanics_acceptance"] is False, "producer evidence overclaim")
        if kind == "controls":
            require(len(data["checks"]) == 5 and all(c["passed"] for c in data["checks"]), "five controls claim differs")
            require(data["packet_sha256"] == {name: ref["sha256"] for name, ref in packet.items() if name != "verification.json"}, "control packet binding differs")
        else:
            require(len(data["captures"]) == 9 and data["errors"] == data["overflow"] == [], "drawing browser record differs")
            require(data["browser_page_code_evaluation"] is False, "browser evaluation boundary differs")
            for capture in data["captures"]:
                require(capture["sha256"] == packet[capture["file"]]["sha256"], "capture source differs")
                require(capture["text_count"] == svg_text_counts[capture["file"]], "capture/XML text count differs")
                require(record(ROOT / capture["screenshot"]["path"])["sha256"] == capture["screenshot"]["sha256"], "retained capture differs")
        producer_records[kind] = {"path": ref["path"], "sha256": ref["sha256"]}

    replay = run_export("--check")
    require(replay.returncode == 0, f"byte replay failed: {replay.stderr}")
    with tempfile.TemporaryDirectory(prefix="source-replay-", dir=OWN) as temporary:
        out = Path(temporary) / "fresh"
        fresh = run_export("--out", out)
        require(fresh.returncode == 0, f"fresh stdlib replay failed: {fresh.stderr}")
        require({p.name: record(p) for p in out.iterdir()} == {name: packet[name] for name in [*result["files"], "result.json"]}, "fresh output bytes differ")
        before = {p.name: record(p) for p in out.iterdir()}
        rejected = run_export("--out", out)
        require(rejected.returncode != 0 and "output directory must be fresh/empty" in rejected.stderr, "occupied-output gate failed")
        require({p.name: record(p) for p in out.iterdir()} == before, "failed output changed issued bytes")
    require({p.name: record(p) for p in DOC.iterdir() if p.is_file()} == packet, "packet changed during review")
    require(all(record(ROOT / p) == ref for p, ref in context.items()), "current context changed during review")
    require(all(record(ROOT / p)["sha256"] == sha for p, sha in pins.items()), "source changed during review")
    require(all(record(ROOT / p)["sha256"] == sha for p, sha in original.items()), "original shop changed during review")

    receipt = {
        "schema": "eoere_extended_cleat_shop_architecture_review/v1",
        "status": "NO_SUBSTANTIAL_CONFIRMED_ARCHITECTURE_SOURCE_OR_RETENTION_FINDINGS",
        "findings": [],
        "review_helper": record(Path(__file__)),
        "target": {"path": str(DOC.relative_to(ROOT)), "files": 26, "bytes": 615144, "verification_sha256": VERIFICATION_SHA, "result_sha256": RESULT_SHA, "all_26_records_canonical_sha256": canonical(packet)},
        "current_context": context,
        "source_closure": {"files": len(pins), "canonical_sha256": canonical(pins), "authenticated_before_after": True, "current_geometry_sha256": inputs["sources"]["extension"]["sha256"], "base_geometry_sha256": inputs["sources"]["base"]["sha256"], "original_14_hash_map_canonical_sha256": canonical(original), "original_14_unchanged": True, "shared_helper_hashes": {key: inputs["sources"][key] for key in ["datum_helper", "drawing_helper"]}},
        "checks": {"stdlib_issued_byte_replay": "PASS", "fresh_owned_output_byte_replay": "PASS", "occupied_failed_output_immutable": "PASS", "source_table_profile_and_stock_ownership": "PASS", "table_rows": expected_rows, "blank_observation_cells": observation_cells, "XML_SVGs": 9, "local_link_occurrences": len(local), "all_current_access_sides_unverified": 200, "catalog_short_stack_flags_retained": 24, "minimum_nominal_stock_spare_mm": stock["minimum_nominal_remaining_mm"], "conditional_mass_kg": mass, "producer_evidence_hashes": producer_records},
        "architecture_assessment": [
            {"evidence": "export.py:53-99,335-372; inputs.json", "assessment": "Saved-data composition has one owner, merges inherited hash contracts, imports two pinned stdlib helpers, and authenticates sources again before returning. The new revision overrides current profiles and translates preserved recipes; no duplicate CAD model or dependency installation."},
            {"evidence": "export.py:183-275; README.md:3-57,213-234", "assessment": "Physical shaft and receiver-occurrence ownership remain distinct. Latest OFF geometry supplies 100/66 axes, base panel datums and current coordinates; optional grid and unadopted Z180/screw remedies are excluded. Old scalar intervals are reused under explicit unchanged-recipe gates, with no fresh bearing/tool claim."},
            {"evidence": "export.py:523-538; check_packet.py:31-80; README.md:342-368", "assessment": "Issued artifacts remain read-only during replay. Separate output requires a fresh/empty directory before generation; occupied failures preserve output. Original fourteen records and producer attempts/captures remain recoverable. Permanent volume contains current tables/SVGs, with shared helpers and external bulky captures referenced."},
            {"evidence": "README.md:35-49,108-234,238-340; access-sides.csv; bolt-stacks.csv", "assessment": "Leaf navigation, local datum conventions, raw-versus-finished outlines and assembly/removal dependencies are explicit. Tools, fixture travel/retention, tolerances, hardware seating and all 200 tool/removal sides remain missing practical inputs. Four incompatible stations are held, observations stay blank, and the packet adds no physical test or blanket signoff requirement."}
        ],
        "limits": [
            "Source/ownership/retention review of these frozen 26 files only; no CAD/BREP queries, geometry changes, native/whole-frame mechanics, browser rerun or dependency installation.",
            "SVG XML and source/evidence bindings checked independently; producer browser/visual records reused, without independent visual or physical fit qualification.",
            "Current force response, elastic/yield/complete joint resistance, fabrication and climbing remain unqualified; historical results do not transfer. Parent owns final publication/validation."
        ],
        "commands": ["python3 -B <packet>/export.py --check", "python3 -B <packet>/export.py --out <owned-temporary-fresh-directory>", "python3 -B <packet>/export.py --out <same-occupied-directory> (expected rejection)", "python3 -B <exclusive-structure>/review.py"],
        "source_and_target_unchanged": True,
        "temporary_fresh_outputs_removed": True,
        "shared_edits_staging_commits": False
    }
    encoded = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    (OWN / "receipt.json").write_bytes(encoded)
    print(json.dumps({"status": receipt["status"], "receipt_sha256": digest(encoded), "review_helper_sha256": receipt["review_helper"]["sha256"], "receipt_bytes": len(encoded)}, sort_keys=True))


if __name__ == "__main__":
    main()
