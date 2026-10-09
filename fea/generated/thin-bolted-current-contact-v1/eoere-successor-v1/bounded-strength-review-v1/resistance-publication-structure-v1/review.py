"""Source-only publication/provenance review; never imports the calculation.

Hash and contract checks read existing evidence. No numerical replay, CAD,
native solve, test suite, shared edits, staging, archive or pruning occurs.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "current-candidate.json").is_file())
OWN = Path(__file__).resolve().parent
BASE = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1"
PACKET = BASE + "/resistance-followup-v1"
REVIEW = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-review-v1/resistance-followup-review-v1"
EXPECTED = {
    BASE + "/README.md": "5940ec7ca4bcbbe260527d311cec29766c7170bbda637c1404cd3fcf33061491",
    BASE + "/analyze.py": "8bffd53e9e730e63db2f041a10626edb002cba7034af118d6dc9bdf3fed69ae3",
    BASE + "/inputs.json": "ae2c65447ed9a0b628dd25b52573f4c04eca58bc6f2b2657ee0a6f88a69a6bd7",
    BASE + "/result.json": "ba5ada3a7d76dc113a0a82705c0e1b3889b16e8b0b98d86669b17438e4624cda",
    BASE + "/verification.json": "8abeea98cab6801ec3135f4633783b7b1d63a38f807384756dcf8cbcf7ea5ecc",
    PACKET + "/README.md": "327cecaf787ad8bef3280c3f1f87e4c21c723b7af04949f86bcfc483917ca5af",
    PACKET + "/analyze.py": "5cddc0db7a3976d232e84b9789eccff0e7b0b99ca11bcf24bb0ef3dc28bfa5a7",
    PACKET + "/inputs.json": "c5e2e58ca5e81ceb8e10c73a9e8287094020db5aebc1841ebece6c6e27a5e099",
    PACKET + "/result.json": "f6ae2d1bbf5528f0027c74bfd2de13fa444b8bc567afaa079d66a295ab04b36b",
    PACKET + "/verification.json": "9e4b44ee39bc191908b43f36a1d698031a93a2f81b8f4632d86453c90bed8628",
    REVIEW + "/review.py": "d8fb5afcc5bfb72eb88174f7916219e2cf54cd5467554a472e69dc009229c8c8",
    REVIEW + "/review-result.json": "3f48ef86677961289b1dce6d8f0f1a8c6369961d2ed1074ff7c3db7f2abcf02b",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_bytes())


def verify(pins):
    for path, digest in pins.items():
        source = ROOT / path
        require(not Path(path).is_absolute() and source.resolve().is_relative_to(ROOT),
                "source is not repository-relative: " + path)
        require(sha(source) == digest, "source changed: " + path)


def audit():
    verify(EXPECTED)
    result = read(PACKET + "/result.json")
    verification = read(PACKET + "/verification.json")
    inputs = read(PACKET + "/inputs.json")
    original = read(BASE + "/inputs.json")
    independent = read(REVIEW + "/review-result.json")
    artifacts = verification["artifacts"]
    for row in artifacts.values():
        require(sha(ROOT / row["path"]) == row["sha256"]
                and (ROOT / row["path"]).stat().st_size == row["bytes"],
                "issued artifact differs")
    for path, row in verification["owned_artifacts"].items():
        require(EXPECTED[path] == row["sha256"]
                and (ROOT / path).stat().st_size == row["bytes"],
                "owned artifact receipt differs")
    require((ROOT / (PACKET + "/result.json")).read_bytes()
            == (ROOT / artifacts["result.json"]["path"]).read_bytes(),
            "compact and issued result differ")
    details = read(artifacts["details.json"]["path"])
    pins = details["complete_source_sha256"]
    canonical = hashlib.sha256(json.dumps(
        pins, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()).hexdigest()
    require(len(pins) == 1071 and canonical == result["source_binding"]["canonical_sha256"],
            "source closure identity differs")
    require(result["source_binding"] == verification["source_binding"]
            == independent["source_binding"], "source binding receipts differ")
    verify(pins)
    dependencies = [BASE + "/analyze.py", "mini_moonboard/bolted_timber_checks.py",
                    "fea/reinforced_timber_resistance.py",
                    "scripts/thin_bolted_timber_common_shaft_checks.py",
                    "scripts/thin_bolted_steel_resistance.py",
                    "tests/test_washer_seating.py", "uv.lock", "pyproject.toml",
                    original["helpers"]["admission"]]
    require(all(path in pins for path in dependencies), "dependency missing from source closure")
    for ref in [inputs[k] for k in ("original_inputs", "original_result", "original_details")] + inputs["pinned_method_sources"]:
        require(pins[ref["path"]] == ref["sha256"], "direct input/source pin differs")
    require(result["case_ids"] == [r["case_id"] for r in original["cases"]]
            == ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"],
            "six-case authority differs")
    require(result["response_geometry"] == original["old_geometry"]
            and result["current_geometry"] == "eoere-grid-aligned-wire-cutouts-v1"
            and result["load_contract"]["field_case_geometry"] == "eoere-bottom-rail-tnut-clearance-v1"
            and result["load_contract"]["new_response_evaluated"] is False,
            "old response/local geometry boundary differs")
    require(not any(result["release"].values())
            and not any(independent["actual_release"].values()), "release flag is enabled")
    require(result["cleat_member_components"]["actual_all_mode_current_cleat_resistance_n"] is None
            and result["bolt_yield_components"]["adjusted_oblique_group_or_shared_stack_reference_n"] is None,
            "unresolved resistance boundary differs")
    require(independent["confirmed_blockers"] == []
            and independent["review_source_sha256"] == EXPECTED[REVIEW + "/review.py"],
            "existing correctness review is not authenticated")
    for name in ("result.json", "details.json"):
        require(independent["once_only_original_replay"][name.split(".")[0] + "_sha256"]
                == artifacts[name]["sha256"], "independent replay artifact differs")
    text = (ROOT / (PACKET + "/README.md")).read_text()
    links = re.findall(r"\]\(([^)]+)\)", text)
    local_links = [u for u in links if not u.startswith(("http:", "https:", "#"))]
    require(all((ROOT / PACKET / u.split("#")[0]).exists() for u in local_links),
            "README source/evidence link is missing")
    # Parse only. Importing the producer would execute shared Python modules.
    ast.parse((ROOT / (PACKET + "/analyze.py")).read_text())
    observations = [
        {
            "criterion": "method reuse and cohesion",
            "evidence": [PACKET + "/analyze.py:24", PACKET + "/analyze.py:562"],
            "assessment": "The followup consumes the original bounded packet and admitted intake, imports existing NDS/reference/own-wrench/annulus-pressure helpers, and reuses saved exact section areas and 552 issued bolt comparisons. New code adds the reduced-depth component formula and parameterizes the existing thin-annulus probe method. It does not copy a solver, library installation, or second section exporter.",
        },
        {
            "criterion": "source authority",
            "evidence": [PACKET + "/inputs.json", REVIEW + "/review-result.json"],
            "assessment": "Chapter 3 and March 2026 AWC errata are explicit pinned method inputs. Existing NDS Appendix/material documents and repository helpers remain in the inherited source closure. MTC is identified only as application precedent; no MTC product rating, XC basis, perpendicular-tension value or generic joint factor is transferred. Formula interpretation and primary-source visual checks are the existing independent review's evidence, not repeated here.",
        },
        {
            "criterion": "dataflow and revision boundary",
            "evidence": [PACKET + "/analyze.py:589", PACKET + "/README.md:13", PACKET + "/result.json"],
            "assessment": "Six authenticated untrimmed raised-rail fields remain the sole response authority. The fixed aligned-wire revision and unchanged axis records are asserted; local trim/cut dimensions are sensitivities. The result does not consume adjusted-base or optional 2026-grid geometry sources or claim their response or geometry acceptance.",
        },
        {
            "criterion": "claim boundaries",
            "evidence": [PACKET + "/README.md:97", PACKET + "/analyze.py:299", PACKET + "/analyze.py:549"],
            "assessment": "The 44 new annular probes, 60 unchanged-source proofs and eight trimmed-cleat proofs establish nominal eligibility for 112 wood washer seats. Thin geometric containment remains distinct from deeper stress, actual seating, preload, moment, washer metal resistance or rotational restraint. Rectangular shear, trimmed-depth and sloping-end screens retain their component/sensitivity status; complete cleat and adjusted group/shared-stack resistance remain null.",
        },
        {
            "criterion": "units and load contracts",
            "evidence": [PACKET + "/analyze.py:35", PACKET + "/analyze.py:264", PACKET + "/README.md:29"],
            "assessment": "The existing lbf helper interface is converted at explicit inch/mm and N/lbf boundaries. The reduced-depth formula uses MPa and millimeters to produce N; result keys carry N, N/mm-squared and N-mm conventions. README states 1 kN equals 1000 N, inherited dry DF-L No.2 CD=1 and CF=1.3 tension scenario, and does not convert a component reference into climber rating. The old load contract and unverified no-slip/multiplier assumptions remain recorded.",
        },
        {
            "criterion": "reproduction and retention",
            "evidence": [PACKET + "/README.md:135", PACKET + "/verification.json"],
            "assessment": "The five-file packet is compact; exact issued attempt02 result/details paths, sizes and hashes authenticate. The CLI supplies output and compare modes; the README identifies the ignored output root and issued attempt. Existing uv.lock/pyproject pins plus recorded Python/NumPy/CadQuery versions retain the environment basis. The active source closure, admitted fields, details and shared primary sources stay active. Superseded attempt01 exact input/script snapshots remain recoverable, with archive/prune subject to the existing workflow; this followup performs neither.",
        },
    ]
    verify(pins)
    verify(EXPECTED)
    return {
        "schema": "eoere_resistance_publication_structure_review/v1",
        "status": "PASS_SOURCE_AUTHORITY_DATAFLOW_AND_CLAIM_BOUNDARIES_NO_SUBSTANTIVE_FINDING",
        "scope": "Five-file resistance followup and existing independent correctness receipt; fixed six old raised-rail fields plus preserved aligned-wire local geometry. Adjusted-base/optional 2026-grid geometry sources, fresh response and actual joint acceptance excluded.",
        "findings": [],
        "observations": observations,
        "source_sha256_before_after": EXPECTED,
        "source_binding": {"details_path": artifacts["details.json"]["path"],
                           "details_sha256": artifacts["details.json"]["sha256"],
                           "pin_count": len(pins), "canonical_sha256": canonical,
                           "verified_before_after": True},
        "checked_artifacts": artifacts,
        "direct_dependency_pins": {p: pins[p] for p in dependencies},
        "five_file_packet_bytes": sum((ROOT / PACKET / n).stat().st_size for n in
                                      ("README.md", "analyze.py", "inputs.json", "result.json", "verification.json")),
        "runtime_as_recorded_by_producer": result["runtime"],
        "local_readme_links_verified": len(local_links),
        "review_helper_sha256": sha(__file__),
        "review_check_command": "python3 " + str(Path(__file__).relative_to(ROOT)) + " --check",
        "execution": {"target_imports": False, "numerical_replay": False,
                      "CAD_queries_or_rebuild": False, "native_or_global_solve": False,
                      "test_suites": False, "target_or_shared_edits": False,
                      "git_mutations_or_staging": False, "archive_or_prune": False},
        "retention": "Only this ignored helper and compact receipt are added. Existing evidence sources, frozen packets and result paths remain unchanged; nothing is archived or pruned.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    receipt = audit()
    payload = json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    destination = OWN / "review-result.json"
    if args.check:
        require(destination.read_bytes() == payload, "saved review receipt differs")
    else:
        with destination.open("xb") as stream:
            stream.write(payload)
    print(json.dumps({"checked": args.check, "receipt": str(destination.relative_to(ROOT)),
                      "sha256": sha(destination), "bytes": len(payload),
                      "findings": len(receipt["findings"])}))
