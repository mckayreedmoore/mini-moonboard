"""Source-only architecture review of the frozen replay source gate v2.

Run from repository root with Python 3.12 and -B. Never runs CAD or a browser.
The receipt is created exclusively; preserve it and choose a new output filename
for a later review of changed inputs.
"""

import argparse
import ast
import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
GATE = Path("scripts/check_eoere_2026_replay_inputs.py")
ISSUED = BASE / "2026-adjustments-v10"
PRIOR = BASE / "2026-adjustments-v3-review-v1"
FROZEN = {
    str(GATE): "d714ccb706443b6ebf4420d8ba5937d4e49612e4290b20538fd4cacaea929c76",
    "scripts/eoere_2026_adjustments.py": "136d7e63f1e337ef8a65421d22d4614b336697cb1b8556ff099995fe26a92821",
    "mini_moonboard/__init__.py": "ddca6b543ee77144e10ec73f6dcd3ca6ae5693cfa7ca5a881697ded0c6782f12",
    "docs/wood-joints-mvp/README.md": "e8527f55997b74d49950d653a55e4ccb1e9a46a49692e1d81907979b406e2b7c",
    "docs/wood-joints-mvp/completion-ledger.md": "b8929e16013caa80536780a238adbcc7fe0a402e62cd588f41b22b8abbf03c57",
    "site/index.html": "1a1a8bbae255886214d6111769674bfafb8e80c72f3ebfa1acea319b2fa8b883",
    "site/eoere-2026-adjustments-overlay.mjs": "b57759996903d1a5696f9cf5dca85af7e392a3cac38eaf6c5e15f49e54a5110d",
    "site/eoere-adjusted-base-v3-scene.json.gz": "d77b9923b7d0df6b3416b2938b2d249a5406a9174fe98fba5118c341bc3df947",
    "site/eoere-2026-adjustments-v3-scene.json.gz": "8682bf9a81c0bf8e7ffb23c3f6725adc6d3c9bd4728b00e50edb696ca3305d1d",
    str(ISSUED / "replay-gate-v2/result.json"): "a8e9efcf59fe0e4435e012c5d64a032d62e8c8a6ba4bb74f124efbaeec133266",
    str(ISSUED / "driver.py.snapshot"): "136d7e63f1e337ef8a65421d22d4614b336697cb1b8556ff099995fe26a92821",
    str(PRIOR / "correctness/review.json"): "2997304b9b6b431b01d3539d0c675da05bf60b218b8aa329e21032cc3fcc374d",
    str(PRIOR / "structure/receipt.json"): "2b4837adc7b6e2a8b4dfd0ba98ea3c7b218bfa14cd4bd909d38f6a1bb255b34a",
    str(PRIOR / "verification/verification-result-v1.json"): "bee7b40d7f2171f78b65bcd41e0296c92e79cb27883144702179eb459fd512fc",
    str(PRIOR / "verification/independent-actual-mesh-check-v1.json"): "3d280e0003e970b909b79ee916444fde2088ed72b11b0c89195762084ad55816",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def check_pins(pins):
    for name, expected in pins.items():
        assert digest(Path(name).read_bytes()) == expected, name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("receipt.json"))
    args = parser.parse_args()
    assert args.out.resolve().parent == Path(__file__).resolve().parent
    assert not args.out.exists(), "preserve frozen review receipts"
    check_pins(FROZEN)
    spec = importlib.util.spec_from_file_location("frozen_replay_source_gate", GATE)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    frozen, complete = gate.verify()
    assert len(frozen) == 570 and len(complete) == 572
    check_pins(complete)
    rejected = gate.controls()
    assert len(rejected) == 26
    issued_gate = read(ISSUED / "replay-gate-v2/result.json")
    assert issued_gate["rejected_controls"] == rejected
    assert issued_gate["mode"] == "VERIFY_EXISTING_FROZEN_V3_INPUTS_ONLY"
    assert issued_gate["original_v3_execution_used_this_gate"] is False
    assert issued_gate["geometry_or_assets_reissued"] is False
    assert issued_gate["cad_execution_this_check"] is False
    assert issued_gate["native_solver"] is False
    check_pins(issued_gate["source_sha256"])

    # Independent record joins verify the original 570-source contract exactly.
    independently_joined = {}
    for report in (DOC / "occupied-adjusted-base-v3.json", DOC / "occupied-2026-adjustments-v3.json"):
        data = read(report)
        assert data["mechanics_ready"] is False
        assert all(value is False for value in data["release"].values())
        for name, expected in data["source_sha256"].items():
            canonical = str(Path(name).resolve())
            assert independently_joined.get(canonical, expected) == expected
            independently_joined[canonical] = expected
    assert independently_joined == frozen

    # Reuse prior independent nominal geometry, mesh and browser evidence.
    reused = []
    for path in (PRIOR / "correctness/review.json", PRIOR / "structure/receipt.json",
                 PRIOR / "verification/verification-result-v1.json",
                 PRIOR / "verification/independent-actual-mesh-check-v1.json"):
        data = read(path)
        check_pins(data.get("source_sha256", data.get("frozen_inputs", {})))
        check_pins(data.get("receipt_bindings", {}))
        reused.append({"path": str(path), "sha256": FROZEN[str(path)]})
    verification = read(PRIOR / "verification/verification-result-v1.json")
    assert verification["passed"] is True and verification["substantial_findings"] == []
    assert verification["browser_evidence_reused"] is True
    assert verification["mechanics_or_physical_release"] is False
    for pair in verification["raw_published_pairs"]:
        assert Path(pair["report"]).read_bytes() == Path(pair["raw_report"]).read_bytes()
        assert Path(pair["scene"]).read_bytes() == Path(pair["raw_scene"]).read_bytes()
    for row in verification["screenshots"]:
        assert digest(Path(row["path"]).read_bytes()) == row["sha256"]
    assert Path("scripts/eoere_2026_adjustments.py").read_bytes() == (ISSUED / "driver.py.snapshot").read_bytes()

    # Inspect ancestry metadata only; do not decode triangle arrays or build meshes.
    ancestry = []
    for scene in ("eoere-adjusted-base-v3-scene.json.gz", "eoere-2026-adjustments-v3-scene.json.gz"):
        data = json.loads(gzip.decompress((Path("site") / scene).read_bytes()))
        parent = data["parent_scene"]
        encoded_parent = (Path("site") / parent["url"]).read_bytes()
        assert digest(encoded_parent) == parent["sha256"]
        assert digest(gzip.decompress(encoded_parent)) == parent["decoded_sha256"]
        assert digest(Path(data["layout_report"]["path"]).read_bytes()) == data["layout_report"]["sha256"]
        assert all(value is False for value in data["release"].values())
        ancestry.append({"scene": scene, "parent": parent["url"], "layout_sha256": data["layout_report"]["sha256"]})

    initializer = Path("mini_moonboard/__init__.py")
    assert str(initializer.resolve()) not in complete
    ast_tree = ast.parse(Path("scripts/eoere_2026_adjustments.py").read_text())
    import_lines = [node.lineno for node in ast_tree.body if isinstance(node, ast.ImportFrom)
                    and node.module == "mini_moonboard"]
    assert import_lines
    supplied = []

    def changed_initializer_reader(path):
        if path.resolve() == initializer.resolve():
            supplied.append(str(path))
            return path.read_bytes() + b"\nraise RuntimeError('changed package bootstrap')\n"
        return path.read_bytes()

    assert gate.verify(changed_initializer_reader) == (frozen, complete)
    assert supplied == []
    assert not Path("scripts/__init__.py").exists()
    ledger = Path("docs/wood-joints-mvp/completion-ledger.md").read_text()
    for text in ("optional CAD replay has not run", "original v3 production predates this gate",
                 "No native mechanics, actual measurements, structural acceptance or build release",
                 "Prior input/route failures remain recoverable", "source snapshots and dispositions"):
        assert text in ledger, text
    check_pins(FROZEN)
    check_pins(complete)
    result = {
        "schema": "eoere_v3_replay_structure_independent_review/v1",
        "reviewer": "/root/adjusted_replay_structure",
        "status": "ONE_CONFIRMED_SUBSTANTIVE_FINDING",
        "source_sha256": FROZEN,
        "helper_sha256": digest(Path(__file__).read_bytes()),
        "python_version": sys.version.split()[0],
        "original_cadquery_version": read(DOC / "occupied-2026-adjustments-v3.json")["cadquery_version"],
        "recorded_contract": {"canonical_frozen_sources": len(frozen), "total_canonical_gate_pins": len(complete),
                              "canonical_map_sha256": digest(json.dumps(frozen, sort_keys=True).encode()),
                              "all_current_source_hashes_match": True, "negative_controls_rejected": len(rejected),
                              "positive_generated_output_control_reused": True,
                              "relative_absolute_conflict_rejected": True},
        "reused_reviews": reused,
        "scene_ancestry": ancestry,
        "source_preservation": {"issued_producer_matches_snapshot": True, "raw_and_published_v3_bytes_identical": True,
                                "original_v3_execution_used_new_gate": False, "optional_CAD_replay_performed": False},
        "initializer_control": {"path": str(initializer), "import_lines": import_lines,
                                "present_in_frozen_gate_pins": False, "changed_reader_preflight_passed": True,
                                "target_read_count": len(supplied), "control_scope": "source verification only; initializer not executed"},
        "findings": [{"priority": "P2", "title": "Authenticate the package bootstrap before replaying the frozen producer",
                      "criterion": "Source authority and caller boundary",
                      "sources": ["scripts/check_eoere_2026_replay_inputs.py:56", "scripts/check_eoere_2026_replay_inputs.py:176",
                                  "scripts/eoere_2026_adjustments.py:22", "scripts/eoere_2026_adjustments.py:552",
                                  "mini_moonboard/__init__.py:1"],
                      "observed": "The canonical 570-source contract and all 572 gate pins omit mini_moonboard/__init__.py. The producer imports mini_moonboard, executing that initializer, while its module enumeration excludes the package root. A reader supplying changed initializer bytes is never queried and preflight still passes. scripts currently has no initializer; its namespace-package state is also outside the contract.",
                      "impact": "A changed bootstrap can alter pinned module functions or abort before source-map collection while the added gate accepts the original 570 hashes. The optional replay therefore has an executable repository-source dependency outside its authentication boundary. This does not establish a defect in today's preserved v3 geometry, and the optional replay remains unperformed.",
                      "recommendation": "Keep the issued producer and 570 recorded bindings immutable. Supplement the separate gate with fixed expected package-initializer hashes and recorded namespace-package absence checks before producer launch, and add changed/missing initializer controls. Attribute the supplemental pins only to the new gate."}],
        "retention": {"issued_v3_sources_and_assets_preserved": True,
                      "prior_failed_outputs_and_snapshots_preserved": True,
                      "archive_recovery_record_present": True,
                      "portability_limit": "Two original source witnesses use absolute locations; this remains an environment-bound record requiring the documented retained inputs and archive recovery, not a standalone portable bundle."},
        "limits": ["No producer run, CAD/BREP query, native/global solve, actual mesh construction, browser run, numerical replay, materialization, full tests, shared-source edit or Git mutation.",
                   "BREP dependencies were read only for source-hash authentication, not geometric queries.",
                   "Previous source-bound v3 geometry, mesh and browser reviews were reused within their nominal-geometry limits.",
                   "Neither gate acceptance nor this source review qualifies revised strength, tooling, tolerances, delivered parts or physical work."],
        "mechanics_or_physical_release": False,
        "reproduction_command": "python3 -B " + str(Path(__file__).relative_to(Path.cwd())) + " --out FRESH_OWNED_STRUCTURE_RECEIPT.json",
    }
    with args.out.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"receipt": str(args.out), "findings": len(result["findings"]), "source_pins_match": True}))


if __name__ == "__main__":
    main()
