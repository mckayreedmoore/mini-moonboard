"""Record a bounded architecture review without loading CAD or a browser."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()
BASE_COMMIT = "29404b051393506dff3ad4f8a1aba03a80e55468"
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
RAW = BASE / "cleat-top-extension-v1"
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
OWN = Path(__file__).resolve().relative_to(ROOT)
INPUTS = [
    OWN, Path("AGENTS.md"), Path("CONTRIBUTING.md"),
    Path("site/index.html"), Path("site/eoere-cleat-extension-overlay.mjs"),
    Path("site/eoere-cleat-extension-scene.json.gz"),
    Path("site/wood-joints-overlay.mjs"), Path("site/eoere-2026-adjustments-overlay.mjs"),
    Path("site/eoere-aligned-wire-gzip-overlay.mjs"), Path("site/eoere-cleat-trim-overlay.mjs"),
    Path("site/eoere-bottom-rail-overlay.mjs"), Path("site/eoere-bolted-overlay.mjs"),
    Path("scripts/check_eoere_cleat_extension_browser.cjs"), Path("scripts/eoere_2026_adjustments.py"),
    Path("docs/wood-joints-mvp/README.md"), Path("docs/wood-joints-mvp/completion-ledger.md"),
    DOC / "occupied-extended-cleats-v1.json", DOC / "occupied-adjusted-base-v3.json",
    DOC / "occupied-2026-adjustments-v3.json", RAW / "revision.py", RAW / "check-viewer.mjs",
    RAW / "eoere-cleat-extension-overlay.mjs", RAW / "actual-mesh-check-v1.json",
    RAW / "cad-v1/geometry.json", RAW / "cad-v1/scene.json.gz",
    BASE / "cleat-top-extension-review-v1/profile-review.json",
    BASE / "cleat-top-extension-review-v1/actual-output-review.json",
    Path("site/eoere-adjusted-base-v3-scene.json.gz"),
    Path("site/eoere-2026-adjustments-v3-scene.json.gz"),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    output = OWN.parent / "receipt.json"
    assert not output.exists(), "preserve the review receipt; select a fresh review folder for changed inputs"
    sources = {str(path): path.read_bytes() for path in INPUTS}
    pins = {path: digest(data) for path, data in sources.items()}
    index = sources["site/index.html"].decode()
    old_index = subprocess.check_output(["git", "show", f"{BASE_COMMIT}:site/index.html"] ).decode()
    branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    assert branch == "master"
    patch = json.loads(gzip.decompress(sources["site/eoere-cleat-extension-scene.json.gz"]))
    report = json.loads(sources[str(DOC / "occupied-extended-cleats-v1.json")])
    checks = {}
    pairs = [
        ("site/eoere-cleat-extension-overlay.mjs", str(RAW / "eoere-cleat-extension-overlay.mjs")),
        ("site/eoere-cleat-extension-scene.json.gz", str(RAW / "cad-v1/scene.json.gz")),
        (str(DOC / "occupied-extended-cleats-v1.json"), str(RAW / "cad-v1/geometry.json")),
    ]
    checks["publication_copies_match_reviewed_outputs"] = all(sources[a] == sources[b] for a, b in pairs)
    frozen = [
        "site/eoere-adjusted-base-v3-scene.json.gz", "site/eoere-2026-adjustments-v3-scene.json.gz",
        str(DOC / "occupied-adjusted-base-v3.json"), str(DOC / "occupied-2026-adjustments-v3.json"),
        "site/eoere-2026-adjustments-overlay.mjs", "scripts/eoere_2026_adjustments.py",
    ]
    checks["frozen_v3_scenes_reports_loader_producer_match_base_commit"] = all(
        sources[path] == subprocess.check_output(["git", "show", f"{BASE_COMMIT}:{path}"])
        for path in frozen
    )
    for variant, binding in patch["parent_scenes"].items():
        path = "site/" + binding["url"]
        assert pins[path] == binding["sha256"]
        assert digest(gzip.decompress(sources[path])) == binding["decoded_sha256"]
        geometry = report["parent_geometry"][variant]
        assert pins[geometry["path"]] == geometry["sha256"] == binding["layout_sha256"]
    checks["both_frozen_parent_scene_and_geometry_bindings_match"] = True
    checks["new_geometry_binding_matches_publication_receipt"] = (
        pins[patch["layout_report"]["path"]] == patch["layout_report"]["sha256"]
    )
    names = {"eoere_cleat_left", "eoere_cleat_right"}
    checks["patch_contains_two_replacements_without_whole_models"] = (
        len(patch["replacements"]) == 2
        and {row["name"] for row in patch["replacements"]} == names
        and not {"solids", "parts", "additions", "templates"}.intersection(patch)
        and {row["id"] for row in report["changed_finished_solids"]} == names
    )
    old_block = old_index.split("const woodJointModels = [", 1)[1].split("];", 1)[0]
    new_block = index.split("const woodJointModels = [", 1)[1].split("];", 1)[0]
    old_keys = set(re.findall(r"\['([^']+)'", old_block))
    new_keys = set(re.findall(r"\['([^']+)'", new_block))
    checks["historical_wood_joint_viewer_choices_preserved"] = old_keys <= new_keys
    checks["exactly_two_new_wood_joint_model_keys"] = new_keys - old_keys == {
        "eoere-extended-cleat-frame-development", "eoere-extended-cleat-2026-development"
    }
    checks["geometry_and_patch_keep_release_flags_false"] = all(
        obj["mechanics_ready"] is False
        and len(obj["release"]) >= 6 and all(value is False for value in obj["release"].values())
        for obj in (patch, report)
    ) and patch["analysis_pass_transferred"] is False
    assert all(checks.values()), checks
    for path, data in sources.items():
        assert Path(path).read_bytes() == data, "source changed during review binding: " + path
    receipt = {
        "schema": "eoere_extended_cleats_architecture_review/v1",
        "status": "NO_SUBSTANTIAL_ARCHITECTURE_FINDINGS",
        "base_commit": BASE_COMMIT, "branch": branch,
        "source_sha256": pins, "checks": checks, "findings": [],
        "architecture": [
            {"source": "site/eoere-cleat-extension-overlay.mjs:2", "assessment":
             "Shared mesh decoding and authenticated parent loaders own the unchanged geometry; the extension owns only the two named cleat replacements."},
            {"source": "site/eoere-cleat-extension-overlay.mjs:71", "assessment":
             "One compact patch binds both frozen parents; each load obtains its own parent objects, replaces two bodies and disposes superseded geometry."},
            {"source": "site/index.html:320", "assessment":
             "The new checkbox pair stays within the extended-cleat model family; the preceding v3 pair remains independently addressable."},
            {"source": "site/eoere-cleat-extension-overlay.mjs:95", "assessment":
             "A distinct model key and revision preserve history; design qualification, mechanics transfer, joint acceptance, physical release and planning mass do not inherit favorable analytical claims."},
            {"source": "docs/wood-joints-mvp/README.md:63", "assessment":
             "The current reading path identifies geometry-only evidence and invalidated old cleat templates; old numerical and shop records keep their revision boundaries."},
            {"source": "docs/wood-joints-mvp/completion-ledger.md:3027", "assessment":
             "Existing raw producers and saved-output reviews remain active; permanent publication inputs are named without overwriting or pruning frozen evidence."},
        ],
        "permanent_asset_bytes": {
            path: len(sources[path]) for path in [
                "site/eoere-cleat-extension-overlay.mjs", "site/eoere-cleat-extension-scene.json.gz",
                str(DOC / "occupied-extended-cleats-v1.json"), "scripts/check_eoere_cleat_extension_browser.cjs"
            ]
        },
        "limits": [
            "Bounded architecture and retention review; no CAD/BRep query, native mechanics, browser recapture, dependency installation or full suite was run.",
            "Existing saved-output and Three.js proof receipts were read and hash-bound; their geometry results were not independently recalculated here.",
            "Parent owns final validation, any revised source binding, staging, publication and claims; this review grants no fabrication or climbing release."
        ],
        "reproduction_command": [sys.executable, str(OWN)],
        "python_version": sys.version,
    }
    output.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"receipt": str(output), "sha256": digest(output.read_bytes()),
                      "source_count": len(pins), "checks": len(checks), "findings": 0}))


if __name__ == "__main__":
    main()
