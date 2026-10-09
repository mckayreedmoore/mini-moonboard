"""Bind a static architecture/scope review of two frozen bounded followups."""

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path.cwd()
OWN = Path(__file__).resolve().relative_to(ROOT)
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
PACKETS = DOC / "bounded-strength-v1"
DRAFT = BASE / "bounded-strength-v1/revised-base-audit-v1/integration-draft-v1/proposed.patch"
NAMES = ("revised-base-audit-v1", "connected-stack-followup-v1")
FILES = ("README.md", "analyze.py", "inputs.json", "result.json", "verification.json")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def main():
    out = OWN.parent / "receipt.json"
    assert not out.exists(), "preserve the review receipt; use a fresh supplement for changed inputs"
    paths = [OWN, Path("AGENTS.md"), Path("docs/wood-joints-mvp/README.md"),
             Path("docs/wood-joints-mvp/completion-ledger.md"), DRAFT,
             PACKETS / "analyze.py", PACKETS / "resistance-followup-v1/analyze.py",
             DOC / "occupied-adjusted-base-v3.json", DOC / "occupied-extended-cleats-v1.json"]
    paths += [PACKETS / name / file for name in NAMES for file in FILES]
    frozen = {name: json.loads((PACKETS / name / "verification.json").read_bytes()) for name in NAMES}
    paths += [Path(frozen[name]["raw_details"]["path"]) for name in NAMES]
    source = {str(path): path.read_bytes() for path in paths}
    pins = {path: sha(data) for path, data in source.items()}
    results = {name: json.loads(source[str(PACKETS / name / "result.json")]) for name in NAMES}
    assert pins[str(PACKETS / NAMES[0] / "result.json")] == "1205472ce4f96626318b42f2ad7578396485d167932f22fc0af387b156c4f875"
    assert pins[str(PACKETS / NAMES[1] / "result.json")] == "d81540a6c69b98f1182a6d2649d9a0d39126756ea94f0b3cd691026de7cb94d1"
    checks = {}
    for name in NAMES:
        verification, result = frozen[name], results[name]
        artifact_ok = all(len(source[path]) == binding["bytes"] and pins[path] == binding["sha256"]
                          for path, binding in verification["owned_artifacts"].items())
        detail_ref = verification["raw_details"]
        assert pins[detail_ref["path"]] == detail_ref["sha256"]
        details = json.loads(source[detail_ref["path"]])
        closure = details["complete_source_sha256"]
        checks[name] = {
            "four_owned_artifact_bindings_match": artifact_ok,
            "raw_details_binding_matches": True,
            "source_map_count": len(closure),
            "source_map_canonical_digest_matches": canonical(closure) == result["complete_source_canonical_sha256"],
            "complete_packet_bytes": sum(len(source[str(PACKETS / name / file)]) for file in FILES),
            "execution_and_physical_release_false": not any(result["execution"].values()) and result["fabrication_or_climbing_release"] is False,
        }
        assert artifact_ok and checks[name]["source_map_canonical_digest_matches"]
        assert len(closure) == result["source_pin_count"]
        assert checks[name]["execution_and_physical_release_false"]
    audit, connected = (results[name] for name in NAMES)
    assert audit["current_geometry_revision"] == "eoere-midpoint-ready-frame-v3"
    assert audit["six_field_geometry_revision"] == connected["source_geometry_revision"] == "eoere-bottom-rail-tnut-clearance-v1"
    assert connected["target_geometry_revision_not_evaluated"] == audit["current_geometry_revision"]
    assert connected["stack_case_count"] == 48 and connected["member_case_count"] == 144
    assert len(connected["stacks"]) == 8 and all(row["adjusted_complete_joint_resistance_n"] is None for row in connected["stacks"])
    receipt = {
        "schema": "eoere_current_geometry_followups_architecture_review/v1",
        "status": "ONE_SUBSTANTIAL_RETENTION_FINDING",
        "source_sha256": pins, "binding_checks": checks,
        "findings": [{
            "id": "ARCH-RETENTION-01", "severity": "P2",
            "title": "Reject existing output destinations before replaying frozen followups",
            "locations": [
                {"path": str(PACKETS / "revised-base-audit-v1/analyze.py"), "line": 661},
                {"path": str(PACKETS / "connected-stack-followup-v1/analyze.py"), "line": 474},
            ],
            "evidence": "Both CLIs create --out with exist_ok=True and use write_text on result.json/details.json. The connected --compare is optional, and the audit has no compare-only mode. The preceding bounded CLI rejects existing outputs; the resistance helper uses exist_ok=False and a non-writing compare mode.",
            "impact": "A replay directed at issued attempt06/attempt02, or at a compact packet directory, silently replaces hash-bound result/detail artifacts. Changed runtime metadata or a future producer revision can then destroy the frozen bytes needed by downstream source bindings. This is an output-retention regression, not a mechanics finding.",
            "concrete_fix": "Preserve both issued five-file packets. Route subsequent replays through a small external guard that refuses any existing --out destination before invoking the frozen producer, and document that guarded command in the maintained integration record. A later unfrozen producer should create its fresh output directory with exist_ok=False before expensive work and compare all serialized payloads before any write.",
        }],
        "architecture_assessment": [
            {"source": str(PACKETS / "revised-base-audit-v1/analyze.py") + ":22", "assessment":
             "The audit reuses the frozen component annulus/known-answer methods and the canonical interval shift helper; it separates nominal saved-geometry checks from old-action component diagnostics."},
            {"source": str(PACKETS / "connected-stack-followup-v1/analyze.py") + ":244", "assessment":
             "The connected followup reuses admitted-field intake, thread windows and timber bearing parameters through explicit source bindings; it creates a bounded alternate statics distribution without a new frame operator or geometry."},
            {"source": str(PACKETS / "connected-stack-followup-v1/README.md") + ":104", "assessment":
             "The trial is explicitly separated from elastic compatibility, yield/ASD resistance and the old same-cut shaft markers. All eight adjusted complete capacities remain null."},
            {"source": "docs/wood-joints-mvp/README.md:63", "assessment":
             "The maintained current model is the later extended-cleat revision. Both frozen followups name their older base-v3 or raised-rail scope and cannot qualify the latest geometry by inheritance."},
            {"source": str(PACKETS / "connected-stack-followup-v1/README.md") + ":155", "assessment":
             "The two compact five-file packets retain existing raw detail/pin maps and shared manuals/helpers instead of duplicating them; prototypes and failed attempts remain recoverable, with parent-owned integration and publication."},
        ],
        "proposed_draft_assessment": {
            "path": str(DRAFT), "status": "UNADOPTED_PROPOSED_PROSE_ONLY",
            "truthfulness": "Its base-v3 extra-OFF, old-field, nominal support, paused-remedy and cleat-extension applicability claims match the audit's frozen scope. It does not assert force transfer, an adopted resistance or physical acceptance.",
            "integration_update": "The proposed next-action wording at lines 23-24 and 70-71 predates the completed connected-stack followup. When integrating both packets, describe the completed 48-stack/144-wrench statics step and retain compatibility/yield/complete resistance as unresolved; keep the old draft frozen rather than presenting it as the latest task queue.",
        },
        "retention": "All original packets, shared maintained docs and the unadopted draft remain read-only. This review wrote only its exclusive helper and compact receipt; no archive, pruning or copied dependencies.",
        "limits": [
            "Static architecture, scope and artifact-binding review only. No producer imports, CAD/BRep queries, native/global mechanics, browser work, installs or full suite.",
            "Source-map count and canonical digest were verified from retained raw JSON; the 1,120/1,126 underlying source files were not individually rehashed here.",
            "No new demands, hardware, geometry, independent resistance, sign-off prerequisite or physical release. Parent owns final validation, remedy disposition and publication."
        ],
        "reproduction_command": [sys.executable, str(OWN)],
    }
    for path, data in source.items():
        assert Path(path).read_bytes() == data, "review source changed: " + path
    out.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"receipt": str(out), "sha256": sha(out.read_bytes()), "source_count": len(pins), "findings": 1}))


if __name__ == "__main__":
    main()
