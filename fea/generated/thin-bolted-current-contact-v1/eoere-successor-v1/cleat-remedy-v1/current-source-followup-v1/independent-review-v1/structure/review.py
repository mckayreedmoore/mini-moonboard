"""Bounded architecture/source/retention review of the current Z180 proposal.

Saved source joins, AST contracts, four tiny preserved fixtures and inert output
preflights only. No CAD, stiffness/frame/native/browser work or field consumption.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
DOC = OWN.parents[1]
EXPECTED = {
    "inputs.json": "989a518a33f05c72c38613e9b8c53fc85458fc1aabc94948803ff5f9fe2bbb7f",
    "prepare.py": "9d12bcaa8d375153f4e93e4bfbc36c283ee3167bd614049e698d92ed067395c4",
    "placement.json": "5e131e9f58014b4a9426aa6a976338b930f471221e19b8e0e122ceff105f9b39",
    "result.json": "26d27f9c8f5e3c1d91e48143341a8e808d0ece99f316eaf789e2fcbe22e4252a",
    "verify.py": "267ff85c8fa87930a56f960f9c12c5a01329c546e117f012d1f16eae34b3d0d4",
    "verification.json": "ba4ed094c618cc71385754f6c4d06a05787f3706273a4faa4c6987f650c48acb",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def record(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": digest(raw)}


def load(path):
    return json.loads(path.read_bytes())


def relative(path):
    return str(path.relative_to(ROOT))


def main():
    require(OWN.parts[-2:] == ("independent-review-v1", "structure") and DOC.name == "current-source-followup-v1", "exclusive review boundary differs")
    target = {name: record(DOC / name) for name in EXPECTED}
    require({name: ref["sha256"] for name, ref in target.items()} == EXPECTED, "frozen six-file packet differs")
    require(sum(r["bytes"] for r in target.values()) == 66497, "compact permanent volume differs")
    context = {p: record(ROOT / p) for p in ["AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md"]}
    config, placement, result, verification = [load(DOC / name) for name in ["inputs.json", "placement.json", "result.json", "verification.json"]]
    direct = result["source_sha256"]
    require(direct == {**config["sources"], relative(DOC / "inputs.json"): EXPECTED["inputs.json"], relative(DOC / "prepare.py"): EXPECTED["prepare.py"]} and len(direct) == 13, "direct source ownership differs")
    require(all(record(ROOT / p)["sha256"] == sha for p, sha in direct.items()), "direct source differs")
    verifier_pins = verification["source_sha256"]
    require(verifier_pins == {**direct, **{relative(DOC / n): EXPECTED[n] for n in ["placement.json", "result.json", "verify.py"]}}, "verifier source ownership differs")
    require(all(record(ROOT / p)["sha256"] == sha for p, sha in verifier_pins.items()), "verifier source differs")
    current, cache, prior = [load(ROOT / config[key]) for key in ["current_geometry", "current_cached_descriptors", "prior_review"]]
    require(current["revision"] == config["current_revision"] == placement["base_revision"] == result["current_revision"] == "eoere-base-side-edge-cleats-v1", "current revision differs")
    require(config["optional_2026_extra"] is placement["optional_2026_extra"] is False, "optional grid included")
    axes = {a["id"]: a for a in current["axes"]}
    screws = {s["axis_id"]: s for s in current["screw_axes"]}
    require(len(axes) == len(current["axes"]) == len(cache["shafts"]) == 100 and axes == {a["axis_id"]: a["source_axis"] for a in cache["shafts"]}, "current 100-axis identity join differs")
    require(len(screws) == len(current["screw_axes"]) == len(cache["hillman_rows"]) == 66 and screws == {s["id"]: s["source_screw_descriptor"] for s in cache["hillman_rows"]}, "current 66-screw identity join differs")
    ids = {f"cleat_post_bolt_{side}_{n}" for side in ["left", "right"] for n in [1, 2]}
    require(set(config["target_axis_ids"]) == ids and len(config["target_axis_ids"]) == 4, "four target identities differ")
    proposed = {a["id"]: a for a in placement["proposed_axes"]}
    require(set(proposed) == ids and len(placement["proposed_axes"]) == 4, "four proposal rows differ")
    for ident, candidate in proposed.items():
        original = axes[ident]
        require(original["point_xyz_mm"][2] == 200 and candidate == {**original, "point_xyz_mm": [*original["point_xyz_mm"][:2], 180.0]}, "a proposal changes more than its Z coordinate")
    require(proposed == {a["id"]: a for a in prior["proposed_geometry_inputs"]["axis_rows"]}, "prior four-axis proposal join differs")
    fixed = [a for a in current["axes"] if a["id"] not in ids]
    all_proposed = [proposed.get(a["id"], a) for a in current["axes"]]
    require(len(fixed) == 96 and sum(a != b for a, b in zip(current["axes"], all_proposed, strict=True)) == 4, "four-only move census differs")
    for key, rows in [("current_fixed_96_canonical_sha256", fixed), ("current_66_screws_canonical_sha256", current["screw_axes"]), ("current_100_axes_canonical_sha256", current["axes"]), ("proposed_100_axes_canonical_sha256", all_proposed)]:
        require(canonical(rows) == placement[key], "placement identity binding differs: " + key)
    require(placement["current_geometry_source"] == {"path": config["current_geometry"], "sha256": config["sources"][config["current_geometry"]]}, "placement/current source binding differs")
    require(result["placement"] == {"file": "placement.json", "sha256": EXPECTED["placement.json"]}, "result/placement binding differs")
    require(placement["status"] == "UNADOPTED_CURRENT_SOURCE_PROPOSAL" and result["status"] == "UNADOPTED_PROPOSAL_CURRENT_HOLD4_RETAINED", "proposal relabeled as adopted")
    require(placement["geometry_adopted"] is False and all(v is False for v in result["release"].values()), "acceptance/release claimed")
    require(set(result["current_drilling_holds"]) == ids and len(result["current_drilling_holds"]) == 4 and result["new_bore_wall_seat_tool_or_response_qualification"] is False, "four current holds or qualification boundary changed")

    producer_source = (DOC / "prepare.py").read_text()
    producer_tree = ast.parse(producer_source)
    verifier_source = (DOC / "verify.py").read_text()
    verifier_tree = ast.parse(verifier_source)
    method_path = ROOT / config["capsule_method"]
    method_tree = ast.parse(method_path.read_bytes())
    independent_path = ROOT / verification["reused_independent_method"]["path"]
    independent_tree = ast.parse(independent_path.read_bytes())
    require('exec(compile(raw_sources[method_path], method_path, "exec"), method.__dict__)' in producer_source, "captured pinned method bytes not used")
    method_calls = Counter(n.func.attr for n in ast.walk(producer_tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == "method")
    require(set(method_calls) == {"known_answers", "primitive", "hardware", "pair"}, "pure method call boundary differs")
    review_calls = {n.func.attr for n in ast.walk(verifier_tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == "review"}
    require(review_calls == {"canonical", "primitive", "hardware", "summary_check", "matrix"}, "independent helper call boundary differs")
    require(not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {"main", "evaluate", "run"} and isinstance(n.func.value, ast.Name) and n.func.value.id in {"method", "review"} for tree in [producer_tree, verifier_tree] for n in ast.walk(tree)), "historical whole-study entrypoint called")
    for tree in [producer_tree, verifier_tree, method_tree, independent_tree]:
        imported = {name.split(".")[0] for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for name in ([n.module or ""] if isinstance(n, ast.ImportFrom) else [a.name for a in n.names])}
        require(not imported & {"cadquery", "OCP", "dolfin", "petsc4py"}, "unexpected CAD/frame import")
    build = next(n for n in producer_tree.body if isinstance(n, ast.FunctionDef) and n.name == "build")
    verifier_run = next(n for n in verifier_tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")
    require(ast.unparse(build.body[0]) == ast.unparse(verifier_run.body[0]) == 'output.mkdir(parents=True, exist_ok=False)', "fresh output ownership differs")
    require('with path.open("xb") as handle:' in producer_source and producer_source.count('unchanged()') == 3, "exclusive artifact/source stability contract differs")

    # Tiny genuine helper fixtures only; do not import or execute either old main.
    tiny_names = {"require", "unit", "primitive", "axis_distance", "pair", "hardware", "known_answers"}
    tiny = [n for n in method_tree.body if isinstance(n, ast.FunctionDef) and n.name in tiny_names]
    namespace = {"math": math}
    exec(compile(ast.fix_missing_locations(ast.Module(body=tiny, type_ignores=[])), str(method_path), "exec"), namespace)
    require(namespace["known_answers"]() == 4, "four preserved tiny fixtures failed")
    # The genuine producer's first statement must reject existing outputs before
    # any source calculation; use existing owned/shared paths, creating nothing.
    preflight_namespace = {"Path": Path, "json": json, "sha": digest, "require": require, "INPUT_SHA": EXPECTED["inputs.json"]}
    definitions = [n for n in producer_tree.body if isinstance(n, ast.FunctionDef)]
    preflight_namespace["hashlib"] = hashlib
    exec(compile(ast.fix_missing_locations(ast.Module(body=definitions, type_ignores=[])), str(DOC / "prepare.py"), "exec"), preflight_namespace)
    preflights = []
    for label, output in [("occupied_packet_directory", DOC), ("source_output_alias", DOC / "inputs.json")]:
        before = record(DOC / "inputs.json")
        try:
            preflight_namespace["build"](DOC / "inputs.json", output)
        except FileExistsError:
            require(record(DOC / "inputs.json") == before, "preflight changed source")
            preflights.append(label)
        else:
            raise ValueError("occupied output accepted")

    class InertOutput:
        def mkdir(self, **options):
            require(options == {"parents": True, "exist_ok": False}, "inert output contract differs")

    try:
        preflight_namespace["build"](Path(__file__), InertOutput())
    except ValueError as error:
        require("changed source:" in str(error), "wrong input preflight rejection")
        preflights.append("wrong_input_hash_before_method_or_output")
    else:
        raise ValueError("wrong input hash accepted")

    require(result["method"]["known_answer_count"] == 4 and result["method"]["sha256"] == direct[relative(method_path)], "producer fixture/method binding differs")
    require(verification["reused_independent_method"]["sha256"] == direct[relative(independent_path)], "independent method binding differs")
    comparisons = sum(v["count"] for row in result["screens"] for v in row.values() if isinstance(v, dict))
    require(comparisons == verification["general_segment_comparisons"] == 40752, "saved comparison census differs")
    gaps = [s["maximum_bore_vs_66_current_screws"]["minimum"]["capsule_separation_lower_bound_mm"] for s in result["screens"]]
    require(all(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(gaps, [-0.05625, 3.94375], strict=True)), "saved capsule gap claim differs")
    require(verification["passed"] is verification["sources_unchanged_after"] is verification["exact_four_Z_moves"] is True and len(verification["controls"]) == 7, "saved control claims differ")
    retain_names = ["attempt01/placement.json", "attempt01/result.json", "controls01/verifier-at-run.py", "controls01/receipt.json", "controls02/receipt.json", "controls02/frozen-packet.json"]
    require((DOC / "attempt01/placement.json").read_bytes() == (DOC / "placement.json").read_bytes() and (DOC / "attempt01/result.json").read_bytes() == (DOC / "result.json").read_bytes(), "original issued attempt differs")
    require((DOC / "controls02/receipt.json").read_bytes() == (DOC / "verification.json").read_bytes(), "current raw/issued verification differs")
    old_verification = load(DOC / "controls01/receipt.json")
    require(old_verification["source_sha256"][relative(DOC / "verify.py")] == record(DOC / "controls01/verifier-at-run.py")["sha256"], "preserved older verifier/source join differs")
    frozen = load(DOC / "controls02/frozen-packet.json")
    require(frozen["file_count"] == 6 and frozen["bytes"] == 66497 and {Path(r["path"]).name: {"bytes": r["bytes"], "sha256": r["sha256"]} for r in frozen["files"]} == target, "frozen retention map differs")
    for folder in ["controls01", "controls02"]:
        for control in verification["controls"]:
            require(control["passed"] is True, "saved control failed")
            name = folder + "/" + control["name"] + ".json"
            retain_names.append(name)
            saved = load(DOC / name)
            successful = control["name"] == "fresh_byte_replay" or control["name"].startswith("source_or_late_output_")
            require((saved["returncode"] == 0) == successful, "saved control exit differs")
        for name in ["placement.json", "result.json"]:
            require((DOC / folder / "replayed" / name).read_bytes() == (DOC / name).read_bytes(), "retained replay differs")
        require((DOC / folder / "race/placement.json").read_bytes() == b"other-writer\n", "raced output overwritten")
        require(not (DOC / folder / "race/result.json").exists(), "raced failure published success")
        for phase in ["before", "during", "rejected"]:
            require(not any((DOC / folder / phase).iterdir()), "source failure published partial artifacts")
    retained = {name: record(DOC / name) for name in retain_names}
    require({name: record(DOC / name) for name in EXPECTED} == target, "target changed during review")
    require(all(record(ROOT / p)["sha256"] == sha for p, sha in verifier_pins.items()), "direct source changed during review")
    require(all(record(ROOT / p) == ref for p, ref in context.items()), "context changed during review")
    require(all(record(DOC / p) == ref for p, ref in retained.items()), "retained attempt changed during review")

    receipt = {
        "schema": "eoere_current_Z180_architecture_source_retention_review/v1",
        "status": "NO_SUBSTANTIAL_CONFIRMED_ARCHITECTURE_SOURCE_OR_RETENTION_FINDINGS",
        "findings": [],
        "review_helper": record(Path(__file__)),
        "target": {"path": relative(DOC), "files": target, "bytes": 66497},
        "current_context": context,
        "direct_source_bindings_authenticated_before_after": direct,
        "recursive_closure_boundary": {"current_geometry_declared": len(current["source_sha256"]), "cache_declared": len(cache["source_sha256"]), "prior_review_declared": prior["source_binding"]["verified_union_count"], "independently_rehashed_here": False, "full_source_or_mechanics_admission_claimed": False},
        "checks": {"current_geometry_cache_identity_join": "100 bolts / 66 screws", "exact_proposed_Z_moves": 4, "fixed_current_bolts": 96, "unchanged_current_screws": 66, "all_four_current_holds_retained": True, "all_four_canonical_identity_bindings": "PASS", "pure_preserved_tiny_fixtures": 4, "inert_source_output_preflights": preflights, "saved_general_segment_comparisons_bound": comparisons, "saved_capsule_gap_pair_mm": gaps, "seven_current_and_seven_preserved_control_records": "BOUND", "source_method_call_names": sorted(method_calls), "independent_method_call_names": sorted(review_calls)},
        "retained_attempt_and_control_hashes": retained,
        "architecture_assessment": [
            {"evidence": "prepare.py:84-168,240-283; placement.json", "assessment": "The new wrapper owns current-source identity and four-Z-only proposal composition. Both complete current 100/66 lists join their cached descriptors, preserving the v3 moves. The four target rows match the preserved proposal while all 96 other current rows and all 66 screws retain canonical bindings. Current Z200 sources are not changed."},
            {"evidence": "prepare.py:164-230; verify.py:111-190; lower_bolt_z_v2.py:39-110; cleat-remedy-review-v1/review.py:56-120", "assessment": "Pure capsule and independent general-segment primitives are reused from pinned existing helpers. The producer executes captured authenticated method bytes; neither wrapper calls old main/evaluate entrypoints. New inputs and compact proposal/results reference old evidence and dependencies without duplicating CAD assets, forces, or installations."},
            {"evidence": "prepare.py:67-88,307-328; verify.py:71-84,193-257; controls02/frozen-packet.json", "assessment": "Thirteen direct pins bind eleven existing sources plus config and producer; verifier adds its own result/placement/source pins. This is separate from nested source admission. Both entrypoints require new directories; exclusive file creation and created-file cleanup preserve existing/raced outputs. Command/stdout/stderr evidence, original attempt and earlier verification remain recoverable."},
            {"evidence": "prepare.py:281-305; result.json:current_drilling_holds,required_before_adoption,limits,release", "assessment": "All four current drilling holds remain. The maximum-bore capsule gap change is a nominal containing-envelope screen, with negative bounds inconclusive and no new solid/bore/seat/edge/tool or strength acceptance. Adoption requires the affected current receiver reconstruction and own subsequent checks; there is no geometry change, old-field transfer or blanket physical/signoff prerequisite."}
        ],
        "limits": [
            "Source/ownership/retention review only: no CAD/BREP, stiffness/frame/native/browser execution, geometry changes or force/field consumption.",
            "Only four tiny stdlib known-answer fixtures and early source/output rejection branches executed. The 40,752 current segment comparisons and byte replay are bound to existing producer records, not independently rerun here.",
            "Nested 581/1077/343 source closure admission, actual tools/hardware, new finished bores/seats, compatible actions and complete resistance remain separate. Parent owns final validation/publication and adoption."
        ],
        "source_and_target_unchanged": True,
        "shared_edits_staging_commits": False,
        "reproduce_review": "python3 -B " + relative(Path(__file__))
    }
    raw = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    (OWN / "receipt.json").write_bytes(raw)
    print(json.dumps({"status": receipt["status"], "receipt_sha256": digest(raw), "receipt_bytes": len(raw), "review_helper_sha256": receipt["review_helper"]["sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
